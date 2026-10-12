"""Unit tests for WP-13a (F-XSEC1 Vorlauf, PRD 5.3, DEC-73/74).

Covers (per the task brief):
  - ``characteristics.py`` basics (momentum/reversal-gap/vol/beta/turnover).
  - ``ic.py`` DEC-39 trio (positive, null, adversarial market-beta).
  - Alignment fixture (IC = +1.000 / -1.000) and the -1..+2 lag profile
    (only lag +1 shows the effect).
  - Delisting fixture: both conventions on a signal-free panel, the
    difference between them is inside a week-cluster bootstrap CI
    around 0.
  - Near-threshold fixture: injected IC = the registered threshold ->
    hit rate ~= 0.5 over 200 seeds (+/- 0.1).
  - Persistence-null determinism (same seed -> identical quantiles/c_rho).
  - THE SEAL, both halves: ``ic.weekly_ic_series`` is monkeypatched for a
    full ``--prelaunch`` run and never once receives the REAL union
    panel's returns array; the prelaunch report JSON carries no
    ``real*ic``/``ic*real``-shaped key and no genuine per-window real
    mean IC.
  - An end-to-end ``--prelaunch`` CLI run on a synthetic union tree,
    reusing the WP-12b fixture builders (``_write_full_history``,
    ``_closes``, ``_load_script``) rather than reimplementing them.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import math
import re
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.wp7_universe import panel_load, pit_universe
from bybit_edge.research.wp12_delisting import delisted_panel
from bybit_edge.research.wp13_xsec import characteristics, ic, nulls, prelaunch

from tests.unit.test_wp12b_delisted_panel import _closes, _load_script, _write_full_history

WP13 = _load_script("wp13_xsec.py")


# ============================================================================
# characteristics.py -- basics
# ============================================================================

def test_momentum_characteristic_trailing_sum():
    returns = np.array([[0.10], [0.20], [-0.10], [0.05]])
    m1 = characteristics.momentum_characteristic(returns, trail_win=1)
    assert np.allclose(m1[:, 0], returns[:, 0])
    m2 = characteristics.momentum_characteristic(returns, trail_win=2)
    assert m2[0, 0] == pytest.approx(0.10)          # only week 0 available
    assert m2[1, 0] == pytest.approx(0.30)           # 0.10 + 0.20
    assert m2[3, 0] == pytest.approx(-0.05)          # -0.10 + 0.05


def test_reversal_gap_characteristic_shifts_by_one_week():
    returns = np.array([[0.10], [0.20], [-0.10]])
    r = characteristics.reversal_gap_characteristic(returns)
    assert math.isnan(r[0, 0])
    assert r[1, 0] == pytest.approx(0.10)
    assert r[2, 0] == pytest.approx(0.20)


def test_realized_vol_and_max_return_from_known_daily_data():
    dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]  # Mon..Fri
    closes = np.array([[100.0], [101.0], [99.0], [103.0], [102.0]])
    panel = {"dates": dates, "close": closes}
    weeks = [pit_universe.iso_week_start(date(2024, 1, 1)).isoformat()]

    vol = characteristics.realized_vol_characteristic(panel, weeks)
    mx = characteristics.max_return_characteristic(panel, weeks)

    daily_log_rets = np.diff(np.log(closes[:, 0]))
    assert vol[0, 0] == pytest.approx(float(daily_log_rets.std(ddof=1)))
    assert mx[0, 0] == pytest.approx(float(daily_log_rets.max()))


def test_beta_characteristic_recovers_known_beta():
    w = 30
    rng = np.random.default_rng(0)
    btc = rng.normal(0.0, 0.05, size=w)
    idio = rng.normal(0.0, 0.001, size=w)
    sym = 2.0 * btc + idio
    returns = np.column_stack([btc, sym])
    beta = characteristics.beta_characteristic(returns, ["BTCUSDT", "SYMUSDT"],
                                                trail_win=8, min_weeks=4)
    assert beta[-1, 0] == pytest.approx(1.0, abs=0.05)   # BTC regressed on itself
    assert beta[-1, 1] == pytest.approx(2.0, abs=0.20)
    assert math.isnan(beta[0, 1])                        # not enough trailing weeks yet


def _beta_characteristic_reference(returns: np.ndarray, symbols: list[str], *,
                                    market_symbol: str = "BTCUSDT",
                                    trail_win: int = characteristics.VOL_BETA_TRAIL_WEEKS,
                                    min_weeks: int = 4) -> np.ndarray:
    """DEC-81: the former per-symbol-loop ``characteristics.beta_characteristic``, copied
    verbatim as the bit-exact reference for the vectorised implementation."""
    n_weeks, n_symbols = returns.shape
    out = np.full((n_weeks, n_symbols), np.nan, dtype=np.float64)
    if market_symbol not in symbols:
        return out
    m = symbols.index(market_symbol)
    mkt = returns[:, m]
    for t in range(n_weeks):
        lo = max(0, t - trail_win + 1)
        mkt_win = mkt[lo:t + 1]
        valid_m = ~np.isnan(mkt_win)
        if int(valid_m.sum()) < min_weeks:
            continue
        mkt_v = mkt_win[valid_m]
        var_m = float(np.var(mkt_v, ddof=1)) if mkt_v.size > 1 else 0.0
        if var_m <= 0.0:
            continue
        mkt_c = mkt_v - mkt_v.mean()
        for j in range(n_symbols):
            sym_win = returns[lo:t + 1, j][valid_m]
            if np.isnan(sym_win).any():
                continue
            n_win = sym_win.size
            cov = float(np.sum((sym_win - sym_win.mean()) * mkt_c) / (n_win - 1))
            out[t, j] = cov / var_m
    return out


@pytest.mark.parametrize("trail_win,min_weeks", [(26, 26), (13, 4), (8, 8)])
def test_beta_characteristic_bit_identical_to_reference_loop(trail_win, min_weeks):
    """DEC-81: the vectorised ``beta_characteristic`` reproduces the former symbol loop
    BIT FOR BIT (``np.array_equal``, not ``allclose``) on random panels with NaN holes in
    the symbol columns AND in the market column, for the three window/min_weeks pairs the
    package uses (calibration 26/26, method grid 13/4, A3-V characteristic 8/8)."""
    for seed in range(4):
        rng = np.random.default_rng(100 + seed)
        w, k = 100, 45
        returns = rng.normal(0.0, 0.06, size=(w, k))
        returns[rng.random((w, k)) < 0.03] = np.nan            # holes in the symbol columns
        returns[[2, 5, 30, 31, 47], -1] = np.nan               # holes in the market column
        returns[:, 3] = np.nan                                 # one symbol with no data at all
        symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
        new = characteristics.beta_characteristic(returns, symbols, trail_win=trail_win, min_weeks=min_weeks)
        ref = _beta_characteristic_reference(returns, symbols, trail_win=trail_win, min_weeks=min_weeks)
        assert np.array_equal(new, ref, equal_nan=True), (seed, trail_win, min_weeks)
        assert np.isfinite(new).sum() > 100                    # the comparison is not vacuous
        assert np.isnan(new[:, 3]).all()

    # degenerate branches: no market symbol, constant (zero-variance) market column
    returns = np.random.default_rng(7).normal(0.0, 0.05, size=(30, 6))
    syms = [f"s{i}" for i in range(5)] + ["BTCUSDT"]
    assert np.array_equal(
        characteristics.beta_characteristic(returns, syms[:-1] + ["XUSDT"], trail_win=trail_win,
                                             min_weeks=min_weeks),
        _beta_characteristic_reference(returns, syms[:-1] + ["XUSDT"], trail_win=trail_win,
                                        min_weeks=min_weeks), equal_nan=True)
    returns[:, -1] = 0.5                                       # exactly representable -> variance exactly 0
    const_new = characteristics.beta_characteristic(returns, syms, trail_win=trail_win, min_weeks=min_weeks)
    assert np.isnan(const_new).all()
    assert np.array_equal(const_new, _beta_characteristic_reference(
        returns, syms, trail_win=trail_win, min_weeks=min_weeks), equal_nan=True)


def test_weekly_turnover_trailing_median_and_decile_bucket():
    dates = ["2024-01-01", "2024-01-02", "2024-01-08", "2024-01-09"]
    turnover = np.array([[10.0, 1.0], [10.0, 1.0], [20.0, 2.0], [20.0, 2.0]])
    panel = {"dates": dates, "turnover": turnover}
    weeks = sorted({pit_universe.iso_week_start(date.fromisoformat(d)).isoformat() for d in dates})

    wt = characteristics.weekly_turnover(panel, weeks)
    assert wt[0].tolist() == [20.0, 2.0]
    assert wt[1].tolist() == [40.0, 4.0]

    trail = characteristics.trailing_median_turnover(wt, trail_win=8)
    assert trail[1, 0] == pytest.approx(float(np.median([20.0, 40.0])))

    buckets = characteristics.decile_bucket(np.array([5.0, 1.0]), np.array([True, True]))
    assert buckets[1] < buckets[0]   # the smaller value gets the lower decile


# ============================================================================
# ic.py -- DEC-39 trio
# ============================================================================

def test_dec39_positive_injected_ic_recovered():
    seed, k, w = 0, 150, 52
    rng = np.random.default_rng(seed)
    characteristic = rng.normal(0, 1, size=(w, k))
    target_rho = 0.06
    a = target_rho / math.sqrt(max(1 - target_rho ** 2, 1e-9))
    returns = rng.normal(0, 1, size=(w, k))
    returns[1:] += a * characteristic[:-1]
    alive = np.ones((w, k), dtype=bool)

    res = ic.weekly_ic_series(characteristic, returns, alive, min_universe=10)
    assert res["n_weeks_used"] == w - 1
    se = float(np.std([r["ic"] for r in res["weekly"]], ddof=1) / math.sqrt(w - 1))
    assert res["mean_ic"] - 3 * se <= target_rho <= res["mean_ic"] + 3 * se
    assert res["mean_ic"] > 0.02


def test_dec39_null_permuted_characteristic_mean_near_zero():
    seed, k, w = 1, 120, 60
    rng = np.random.default_rng(seed)
    returns = rng.normal(0, 0.03, size=(w, k))
    characteristic = np.empty((w, k))
    for t in range(w):
        characteristic[t] = rng.permutation(k)
    alive = np.ones((w, k), dtype=bool)

    res = ic.weekly_ic_series(characteristic, returns, alive, min_universe=10)
    se = 1.0 / math.sqrt(k - 1) / math.sqrt(res["n_weeks_used"])
    assert abs(res["mean_ic"]) < 4 * se


def test_dec39_adversarial_market_beta_correlated_characteristic():
    """ADVERSARIAL (PRD 5.3): a characteristic mechanically equal to each
    symbol's TRUE beta, on a panel with a DOMINANT, zero-mean market
    factor (sigma_market >> sigma_idio, so a single week's cross-section
    is almost entirely ranked by beta -- |weekly IC| close to 1 on most
    weeks) -- the WINDOW MEAN IC must still be close to 0, because the
    market factor's sign flips roughly symmetrically across many weeks.
    Also documents (and asserts) that ``demean_outcome`` provably makes
    NO difference to a Spearman rank correlation (subtracting a
    per-week constant from every value in that week's cross-section never
    changes ranks) -- both settings must give IDENTICAL results."""
    seed, k, w = 7, 150, 250
    rng = np.random.default_rng(seed)
    beta = rng.uniform(0.5, 2.5, size=k)
    market = rng.normal(0.0, 0.05, size=w)     # dominant, ZERO-MEAN factor
    idio = rng.normal(0.0, 0.002, size=w * k).reshape(w, k)
    returns = beta[None, :] * market[:, None] + idio
    characteristic = np.tile(beta, (w, 1))     # mechanically == true beta, every week
    alive = np.ones((w, k), dtype=bool)

    res_demean = ic.weekly_ic_series(characteristic, returns, alive, demean_outcome=True, min_universe=10)
    res_raw = ic.weekly_ic_series(characteristic, returns, alive, demean_outcome=False, min_universe=10)

    per_week_abs = [abs(r["ic"]) for r in res_demean["weekly"] if not math.isnan(r["ic"])]
    assert np.median(per_week_abs) > 0.8, "the single-week factor must genuinely dominate"

    assert res_demean["mean_ic"] == pytest.approx(res_raw["mean_ic"], abs=1e-12)
    se = 1.0 / math.sqrt(res_demean["n_weeks_used"])
    assert abs(res_demean["mean_ic"]) < 3 * se


# ============================================================================
# alignment fixture + lag profile
# ============================================================================

def _rank_matrix(returns: np.ndarray) -> np.ndarray:
    return np.array([np.argsort(np.argsort(returns[t])) for t in range(returns.shape[0])], dtype=np.float64)


def test_alignment_fixture_perfect_and_mirrored_ic():
    w, k = 25, 30
    rng = np.random.default_rng(42)
    returns = rng.normal(0, 1, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    ranks = _rank_matrix(returns)

    char_perfect = np.full((w, k), np.nan)
    char_perfect[:-1] = ranks[1:]                          # char[t] == exact rank of returns[t+1]
    res = ic.weekly_ic_series(char_perfect, returns, alive, min_universe=5)
    assert res["mean_ic"] == pytest.approx(1.0, abs=1e-9)

    char_mirror = np.full((w, k), np.nan)
    char_mirror[:-1] = (k - 1) - ranks[1:]                  # exactly reversed rank
    res_m = ic.weekly_ic_series(char_mirror, returns, alive, min_universe=5)
    assert res_m["mean_ic"] == pytest.approx(-1.0, abs=1e-9)


def test_lag_profile_only_lag_plus1_shows_the_effect():
    w, k = 30, 40
    rng = np.random.default_rng(11)
    returns = rng.normal(0, 1, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    ranks = _rank_matrix(returns)

    mean_ic_by_lag: dict[int, float] = {}
    for lag in (-1, 0, 1, 2):
        char = np.full((w, k), np.nan)
        for t in range(w):
            target = t + lag
            if 0 <= target < w:
                char[t] = ranks[target]
        res = ic.weekly_ic_series(char, returns, alive, min_universe=5)
        mean_ic_by_lag[lag] = res["mean_ic"]

    assert mean_ic_by_lag[1] == pytest.approx(1.0, abs=1e-9)
    for lag in (-1, 0, 2):
        assert abs(mean_ic_by_lag[lag]) < 0.25, (lag, mean_ic_by_lag)


# ============================================================================
# delisting fixture -- both conventions on a signal-free panel
# ============================================================================

def test_delisting_fixture_conventions_agree_on_signal_free_panel():
    seed, k, w = 3, 80, 40
    rng = np.random.default_rng(seed)
    returns = rng.normal(0, 0.03, size=(w, k))
    characteristic = rng.normal(0, 1, size=(w, k))      # signal-free, independent of returns
    first_bar = np.zeros(k, dtype=np.int64)
    last_bar = np.full(k, w - 1, dtype=np.int64)
    doomed = rng.choice(k, size=k // 4, replace=False)
    for s in doomed:
        last_bar[s] = int(rng.integers(10, w - 2))
    alive = pit_universe.pit_alive_mask(first_bar, last_bar, w, min_weeks_history=8)

    res_drop = ic.weekly_ic_series(characteristic, returns, alive, convention="drop", min_universe=5)
    res_close = ic.weekly_ic_series(characteristic, returns, alive, convention="close_at_last", min_universe=5)
    assert res_close["n_affected_series"] and sum(res_close["n_affected_series"]) > 0

    ic_drop = np.array([r["ic"] for r in res_drop["weekly"]])
    ic_close = np.array([r["ic"] for r in res_close["weekly"]])

    rng2 = np.random.default_rng(seed + 1)
    n_weeks = len(ic_drop)
    boots = []
    for _ in range(500):
        idx = rng2.integers(0, n_weeks, size=n_weeks)
        d = np.nanmean(ic_close[idx]) - np.nanmean(ic_drop[idx])
        if not math.isnan(d):
            boots.append(d)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    assert lo <= 0.0 <= hi, (lo, hi)


# ============================================================================
# near-threshold fixture -- hit rate ~= 0.5
# ============================================================================

def test_near_threshold_hit_rate_about_half():
    k, w = 120, 40
    alive = np.ones((w, k), dtype=bool)
    floor = nulls.analytic_permutation_floor(alive, [str(i) for i in range(w)])["e_floor"]
    threshold = nulls.Z_PER_WINDOW * floor / math.sqrt(w)

    n_seeds, hits = 200, 0
    for seed in range(n_seeds):
        rng = np.random.default_rng(10_000 + seed)
        characteristic = rng.normal(0, 1, size=(w, k))
        a = threshold / math.sqrt(max(1 - threshold ** 2, 1e-9))
        returns = rng.normal(0, 1, size=(w, k))
        returns[1:] += a * characteristic[:-1]
        res = ic.weekly_ic_series(characteristic, returns, alive, min_universe=10)
        if res["mean_ic"] > threshold:
            hits += 1
    hit_rate = hits / n_seeds
    assert 0.4 <= hit_rate <= 0.6, hit_rate


# ============================================================================
# persistence-null determinism
# ============================================================================

def test_persistence_null_determinism_same_seed():
    k, w = 40, 20
    rng = np.random.default_rng(5)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    weeks = [f"w{i}" for i in range(w)]

    r1 = nulls.persistence_null(returns, alive, weeks, variants=("mom1", "rev_gap"), n_sims=20, seed=53)
    r2 = nulls.persistence_null(returns, alive, weeks, variants=("mom1", "rev_gap"), n_sims=20, seed=53)
    assert r1["variants"] == r2["variants"]
    assert np.array_equal(r1["ar1"]["phi"], r2["ar1"]["phi"])
    assert np.array_equal(r1["ar1"]["sigma"], r2["ar1"]["sigma"])

    r3 = nulls.persistence_null(returns, alive, weeks, variants=("mom1", "rev_gap"), n_sims=20, seed=999)
    assert r3["variants"] != r1["variants"]


# ============================================================================
# fixture tree (reuses WP-12b's builders, never reimplements them)
# ============================================================================

def _build_prelaunch_fixture_tree(tmp_path: Path):
    """11 survivors + BTCUSDT + 1 delisted symbol spanning
    2021-01-01..2026-06-30 (covers L, W1 and W2) -- small enough to run
    the full ``assemble_prelaunch_report`` pipeline (small ``n_sims``) in
    a unit test, reusing ``test_wp12b_delisted_panel``'s fixture-tree
    writers instead of a parallel implementation. >= 10 SURVIVOR symbols
    (DEC-78: the Gegenprobe/factor-share machinery needs >= min_universe
    =10 alive symbols per week to produce a FINITE calibration -- same
    reason ``test_wp13_run.py``'s ``_build_run_fixture_tree_large``
    exists; the old 3-survivor fixture left every calibration NaN)."""
    surv_base = tmp_path / "panel_1d"
    surv_manifest = surv_base / "panel_manifest.sqlite"
    del_base = tmp_path / "panel_1d_delisted"
    del_manifest = del_base / "panel_manifest.sqlite"

    full_start, full_end = date(2021, 1, 1), date(2026, 6, 30)
    survivors = ["BTCUSDT"] + [f"SYM{i:02d}USDT" for i in range(11)]
    for i, sym in enumerate(survivors):
        _write_full_history(surv_base, surv_manifest, sym,
                             _closes(full_start, full_end, seed=i + 1), as_of_date=full_end)

    delist_date = date(2025, 2, 10)   # inside W1 (2024-07-01..2025-06-30)
    _write_full_history(del_base, del_manifest, "MMMUSDT",
                         _closes(full_start, delist_date, seed=9), as_of_date=delist_date)
    dd = delisted_panel.write_delisting_dates_json(del_base, {
        "MMMUSDT": {"delist_date": delist_date.isoformat(),
                    "announcement_id": "ann-mmmusdt", "source": "delisting_ms"}})

    as_of = date(2027, 1, 1)
    panel = panel_load.load_panel_union(
        surv_base, surv_manifest, del_base, del_manifest,
        year_start=2021, year_end=2026, as_of=as_of, delisting_dates_path=Path(dd["path"]))
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    return panel, weekly, surv_base, surv_manifest, del_base, del_manifest, Path(dd["path"])


# ============================================================================
# THE SEAL -- both halves
# ============================================================================

def test_seal_prelaunch_never_calls_ic_with_real_returns(tmp_path, monkeypatch):
    panel, weekly, _sb, _sm, _db, del_manifest, dd_path = _build_prelaunch_fixture_tree(tmp_path)
    real_returns = weekly["returns"]
    real_hash = hashlib.sha256(np.ascontiguousarray(real_returns).tobytes()).hexdigest()

    calls: list[np.ndarray] = []
    orig = ic.weekly_ic_series

    def spy(characteristic, returns, alive, **kwargs):
        calls.append(returns)
        return orig(characteristic, returns, alive, **kwargs)

    monkeypatch.setattr(ic, "weekly_ic_series", spy)

    # DEC-78 Nachtrag: gegenprobe_rel_tol widened -- this fixture's tiny (12-symbol) panel is
    # too statistically underpowered for the Gegenprobe's own sampling noise (see the CLI e2e
    # test's comment); this test's OWN purpose (THE SEAL) is unaffected either way.
    # DEC-81: the z-test and the search precision are switched off the same way
    # (gegenprobe_z_max, calibration_search_rel_tol), the probes kept small.
    report = prelaunch.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=del_manifest, delisting_dates_path=dd_path,
        n_sims=5, n_reps_factor_null=5, n_reps_beta_control_study=5, n_reps_beta_control_winner=5, seed=53,
        gegenprobe_n_reps=10, gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9, gegenprobe_market_check=False,
        calibration_search_n_reps=5, calibration_search_rel_tol=10.0, calibration_search_max_iter=8)
    assert report["windows"]["W1"]["available"]

    assert calls, "expected ic.weekly_ic_series to be called by the persistence null"
    for returns_arg in calls:
        assert returns_arg is not real_returns
        arg_hash = hashlib.sha256(np.ascontiguousarray(returns_arg).tobytes()).hexdigest()
        assert arg_hash != real_hash


def _walk_keys(obj, path: str = ""):
    if isinstance(obj, dict):
        for key, val in obj.items():
            new_path = f"{path}/{key}"
            yield new_path
            yield from _walk_keys(val, new_path)
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            yield from _walk_keys(val, f"{path}[{i}]")


def test_seal_prelaunch_report_json_no_real_ic_key(tmp_path):
    panel, weekly, _sb, _sm, _db, del_manifest, dd_path = _build_prelaunch_fixture_tree(tmp_path)
    report = prelaunch.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=del_manifest, delisting_dates_path=dd_path,
        n_sims=5, n_reps_factor_null=5, n_reps_beta_control_study=5, n_reps_beta_control_winner=5, seed=53,
        gegenprobe_n_reps=10, gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9, gegenprobe_market_check=False,
        calibration_search_n_reps=5, calibration_search_rel_tol=10.0, calibration_search_max_iter=8)
    artifacts = prelaunch.write_prelaunch_artifacts(tmp_path / "out", report)
    payload = __import__("json").loads(
        Path(artifacts["artifacts"]["wp13a_prelaunch_json"]["path"]).read_text(encoding="utf-8"))

    pattern = re.compile(r"real.*ic|ic.*real", re.IGNORECASE)
    bad_keys = [k for k in _walk_keys(payload) if pattern.search(k.rsplit("/", 1)[-1])]
    assert not bad_keys, bad_keys

    # no leaf key literally named "mean_ic" anywhere -- the only IC-window
    # aggregates in the report are the persistence-null's SIMULATED-draw
    # statistics (mean_ic_draws_mean etc.), never a real-data mean IC.
    mean_ic_keys = [k for k in _walk_keys(payload) if k.rsplit("/", 1)[-1] == "mean_ic"]
    assert not mean_ic_keys, mean_ic_keys

    # DEC-78 Entscheidung 1, seal extension: the new beta_sd_true/Gegenprobe fields are
    # wired through this SAME seal-tested --prelaunch path (never real-outcome-derived --
    # the regex/mean_ic checks above already cover them, this just confirms they are
    # actually present, not silently skipped).
    assert any(k.endswith("/beta_sd_true") for k in _walk_keys(payload))
    assert any(k.endswith("/gegenprobe") or k.endswith("/gegenprobe_error") for k in _walk_keys(payload))

    # DEC-85 (ii): the Gegenprobe's market-column bands are in the JSON and in the
    # calibration table of the Markdown report (two new columns).
    assert any(k.endswith("/gegenprobe/market_sd_band") for k in _walk_keys(payload))
    assert any(k.endswith("/gegenprobe/market_rho_band") for k in _walk_keys(payload))
    md = Path(artifacts["artifacts"]["wp13a_prelaunch_md"]["path"]).read_text(encoding="utf-8")
    header = next(line for line in md.splitlines() if line.startswith("| Kalibrierung |"))
    assert "Marktspalte SD-Band | rho-Band" in header
    rows = [line for line in md.splitlines() if re.match(r"\| (measured|stress|zero) \|", line)]
    assert rows and all(line.count("|") == header.count("|") for line in rows)


# ============================================================================
# end-to-end --prelaunch CLI on a synthetic union tree
# ============================================================================

def _ns_prelaunch(**overrides) -> argparse.Namespace:
    base = dict(
        panel_base="", delisted_base="", delisted_manifest="", delisting_dates="",
        start_year=2021, end_year=2026, as_of="2027-01-01", out="",
        seed=53, n_sims=5, n_reps_factor_null=5,
        n_reps_beta_control_study=5, n_reps_beta_control_winner=5,
        # DEC-78 Nachtrag: strict/literal defaults (match nulls.py's own) unless a test
        # overrides them -- e.g. for a small synthetic panel too statistically underpowered
        # for the Gegenprobe's own sampling noise, never for a real run.
        # DEC-81: the defaults are the nulls constants (400 replicates, z <= 3 on a standard-error basis).
        gegenprobe_n_reps=nulls.GEGENPROBE_N_REPS_DEFAULT, gegenprobe_rel_tol=nulls.GEGENPROBE_REL_TOL,
        gegenprobe_z_max=nulls.GEGENPROBE_Z_MAX, no_gegenprobe_market_check=False,
        calibration_search_n_reps=nulls.CALIBRATION_SEARCH_N_REPS_DEFAULT,
        calibration_search_rel_tol=nulls.CALIBRATION_SEARCH_REL_TOL_DEFAULT,
        calibration_search_max_iter=nulls.CALIBRATION_SEARCH_MAX_ITER_DEFAULT,
        convention="close_at_last", allow_partial=False,
        stress_rel="scinance3-impl/state/wp10_stress_canon/stress_rel.json",
        stress_abs="scinance3-impl/state/wp10_stress_canon/stress_abs.json",
    )
    base.update(overrides)
    return argparse.Namespace(**base)


# ============================================================================
# DEC-75 Vorlauf v2 -- task brief items 1-9
# ============================================================================

# ---- item 1: W_judged -------------------------------------------------------

def test_w_judged_is_n_weeks_minus_one_and_floor_drops_final_week():
    n_weeks, k = 10, 20
    alive = np.ones((n_weeks, k), dtype=bool)
    weeks = [str(i) for i in range(n_weeks)]
    floor = nulls.analytic_permutation_floor(alive, weeks)
    assert floor["w_judged"] == n_weeks - 1 == 9
    assert len(floor["floor_per_week"]) == 9
    assert len(floor["k_series"]) == 9
    assert nulls.w_judged_of(n_weeks) == 9
    assert nulls.w_judged_of(1) == 0
    assert nulls.w_judged_of(0) == 0


# ---- item 2: c_rho bias correction + ic_min_capped/raw ---------------------

def test_c_rho_bias_correction_additive_plus_one_over_w():
    rho_raw = {1: 0.10, 2: -0.05, 3: 0.0, 4: 0.02}
    w_judged = 52
    corrected = nulls.bias_correct_rho_by_lag(rho_raw, w_judged=w_judged)
    for k, v in rho_raw.items():
        assert corrected[k] == pytest.approx(v + 1.0 / w_judged)
    c_rho_raw = nulls.c_rho_from_lag_autocorr(rho_raw, w=w_judged)
    c_rho_corrected = nulls.c_rho_from_lag_autocorr(corrected, w=w_judged)
    assert c_rho_corrected > c_rho_raw   # a positive additive shift never lowers c_rho


def test_ic_threshold_cap_c_rho_default_true_and_raw_next_to_capped():
    e_floor, w = 0.05, 52
    below_one = nulls.ic_threshold(e_floor, 0.6, w)              # cap_c_rho defaults True
    assert below_one == pytest.approx(nulls.Z_PER_WINDOW * e_floor * 1.0 / math.sqrt(w))
    raw = nulls.ic_threshold(e_floor, 0.6, w, cap_c_rho=False)
    assert raw == pytest.approx(nulls.Z_PER_WINDOW * e_floor * 0.6 / math.sqrt(w))
    assert raw < below_one                                        # capped >= raw whenever c_rho < 1
    above_one = nulls.ic_threshold(e_floor, 1.3, w, cap_c_rho=True)
    assert above_one == pytest.approx(nulls.ic_threshold(e_floor, 1.3, w, cap_c_rho=False))


def test_persistence_null_reports_c_rho_raw_and_corrected():
    k, w = 40, 30
    rng = np.random.default_rng(5)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    weeks = [f"w{i}" for i in range(w)]
    res = nulls.persistence_null(returns, alive, weeks, variants=("mom1",), n_sims=30, seed=53)
    v = res["variants"]["mom1"]
    assert "c_rho_raw" in v and "c_rho_corrected" in v and v["c_rho"] == v["c_rho_corrected"]
    w_judged = nulls.w_judged_of(w)
    assert res["w_judged"] == w_judged
    expected_corrected = nulls.c_rho_from_lag_autocorr(
        nulls.bias_correct_rho_by_lag({int(kk): vv for kk, vv in v["rho_by_lag"].items()}, w_judged=w_judged),
        w=w_judged)
    assert v["c_rho_corrected"] == pytest.approx(expected_corrected)


def test_window_noise_floor_and_threshold_reports_capped_and_raw_ic_min():
    k, w = 60, 30
    rng = np.random.default_rng(9)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    window = {"returns": returns, "alive": alive, "weeks": [str(i) for i in range(w)]}
    nf = prelaunch.window_noise_floor_and_threshold(window, variants=("mom1", "rev_gap"), n_sims=15, seed=53)
    assert nf["w_judged"] == nulls.w_judged_of(w)
    for v in ("mom1", "rev_gap"):
        capped = nf["ic_min_capped_per_variant"][v]
        raw = nf["ic_min_raw_per_variant"][v]
        c_rho = nf["persistence_null"]["variants"][v]["c_rho_corrected"]
        assert capped == pytest.approx(nulls.ic_threshold(
            nf["floor"]["e_floor"], c_rho, nf["w_judged"], cap_c_rho=True))
        assert raw == pytest.approx(nulls.ic_threshold(
            nf["floor"]["e_floor"], c_rho, nf["w_judged"], cap_c_rho=False))
        if c_rho < 1.0:
            assert raw < capped
        else:
            assert raw == pytest.approx(capped)


# ---- item 3: factor-preserving null + block-permutation p-value ------------

def test_factor_preserving_null_elevates_sd_above_plain_permutation_floor():
    """Regression test for Review B-1: on a panel with heterogeneous beta
    to a common factor, SD(IC_t) under the factor-preserving null must
    exceed the plain exchangeability floor E_t[1/sqrt(K_t-1)] -- the
    exact failure mode DEC-75 exists to correct."""
    n_weeks, k = 60, 80
    rng = np.random.default_rng(0)
    returns = rng.normal(0, 0.03, size=(n_weeks, k))
    alive = np.ones((n_weeks, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k)]
    floor = nulls.analytic_permutation_floor(alive, [str(i) for i in range(n_weeks)])

    fp = nulls.factor_preserving_null(returns, alive, symbols, variants=("mom1", "rev_gap"),
                                       n_reps=60, seed=53)
    for v in ("mom1", "rev_gap"):
        assert fp["variants"][v]["factor_sd"] > floor["e_floor"]
        assert math.isfinite(fp["variants"][v]["quantile_one_sided"])
    assert math.isfinite(fp["selection_ceiling_mean_of_max"])
    assert fp["n_reps"] == 60


def test_factor_preserving_null_determinism_same_seed():
    n_weeks, k = 30, 25
    rng = np.random.default_rng(1)
    returns = rng.normal(0, 0.03, size=(n_weeks, k))
    alive = np.ones((n_weeks, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k)]
    r1 = nulls.factor_preserving_null(returns, alive, symbols, variants=("mom1",), n_reps=20, seed=53)
    r2 = nulls.factor_preserving_null(returns, alive, symbols, variants=("mom1",), n_reps=20, seed=53)
    assert r1["variants"] == r2["variants"]
    r3 = nulls.factor_preserving_null(returns, alive, symbols, variants=("mom1",), n_reps=20, seed=999)
    assert r3["variants"] != r1["variants"]


def test_block_permute_week_index_is_a_permutation_and_preserves_blocks():
    n_weeks, block = 17, 4
    rng = np.random.default_rng(3)
    perm = nulls.block_permute_week_index(n_weeks, block, rng)
    assert sorted(perm.tolist()) == list(range(n_weeks))
    # every block's internal order is preserved (only block ORDER shuffles)
    n_blocks = math.ceil(n_weeks / block)
    blocks = [list(range(b * block, min((b + 1) * block, n_weeks))) for b in range(n_blocks)]
    # reconstruct: walk perm in chunks matching the ORIGINAL blocks (order of blocks may differ,
    # sizes are 4,4,4,...,shorter-last) -- verify every contiguous chunk of perm equals SOME block, in order
    remaining = list(perm)
    covered = set()
    idx = 0
    for _ in range(n_blocks):
        # find which block size comes next by matching the block starting at remaining[idx]
        found = False
        for bi, b in enumerate(blocks):
            if bi in covered:
                continue
            if remaining[idx:idx + len(b)] == b:
                covered.add(bi)
                idx += len(b)
                found = True
                break
        assert found, (idx, remaining)
    assert idx == n_weeks


def test_block_permutation_pvalue_null_large_signal_small():
    seed, k, w = 1, 60, 60
    rng = np.random.default_rng(seed)
    returns = rng.normal(0, 0.03, size=(w, k))
    characteristic = rng.normal(0, 1, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    res = ic.weekly_ic_series(characteristic, returns, alive)
    pv_null = nulls.block_permutation_pvalue(res["mean_ic"], characteristic, returns, alive,
                                              direction="positive", n_reps=150, seed=53)
    assert pv_null["p_value"] > 0.05

    ranks = _rank_matrix(returns)
    char_perfect = np.full((w, k), np.nan)
    char_perfect[:-1] = ranks[1:]
    res2 = ic.weekly_ic_series(char_perfect, returns, alive, min_universe=5)
    pv_signal = nulls.block_permutation_pvalue(res2["mean_ic"], char_perfect, returns, alive,
                                                direction="positive", n_reps=150, seed=53)
    assert pv_signal["p_value"] < 0.02
    assert pv_signal["p_value"] < pv_null["p_value"]


# ---- item 4: H-30 vol-weighted-outcome v2 -----------------------------------

def test_vol_weighted_outcome_with_drag_requires_literal_pit():
    returns = np.ones((3, 2))
    vol = np.full((3, 2), 0.05)
    with pytest.raises(ValueError):
        ic.vol_weighted_outcome_with_drag(returns, vol, weight_source="not_pit")


def test_vol_weighted_outcome_with_drag_uses_formation_week_vol_for_next_week_outcome():
    """DEC-87 (G) changed the SIGN of the drag term (the pre-DEC-87 version of this test pinned
    ``(returns[1] - 0.5*vol**2) * w``, which subtracted the drag from a LOG outcome and so doubled it): the
    adjusted outcome is ``returns[t+1] + sigma_w[t]^2/2``. Without ``day_count`` the caller declares ``vol`` to be
    weekly already (sigma_w = vol); the formation-week/next-week alignment (B-6) is unchanged."""
    n_weeks, k = 4, 2
    returns = np.array([[0.0, 0.0], [0.10, 0.20], [-0.05, 0.03], [0.02, -0.01]])
    weekly_vol = np.array([[0.04, 0.06], [0.05, 0.03], [0.02, 0.08], [0.01, 0.01]])
    out = ic.vol_weighted_outcome_with_drag(returns, weekly_vol, weight_source="pit")
    target_vol = out["target_vol"]
    assert target_vol == pytest.approx(float(np.median(weekly_vol)))
    # row t=0: formation week 0's vol (weekly_vol[0]) weights returns[1] (NOT returns[0]); the drag is ADDED
    expected_w0 = (returns[1] + 0.5 * weekly_vol[0] ** 2) * (target_vol / weekly_vol[0])
    assert np.allclose(out["weighted_outcome"][0], expected_w0)
    # last row has no t+1 -> NaN
    assert np.isnan(out["weighted_outcome"][-1]).all()
    assert out["weight_source"] == "pit"


def test_h30_feasibility_v2_reports_both_ratios_with_bound():
    dates, k = [], 40
    d0 = date(2022, 1, 3)
    n_days = 400
    dates = [(d0 + __import__("datetime").timedelta(days=i)).isoformat() for i in range(n_days)]
    rng = np.random.default_rng(11)
    close = 100.0 * np.cumprod(1.0 + rng.normal(0, 0.01, size=(n_days, k)), axis=0)
    panel = {"dates": dates, "close": close}
    weeks = sorted({pit_universe.iso_week_start(date.fromisoformat(d)).isoformat() for d in dates})
    returns = rng.normal(0, 0.03, size=(len(weeks), k))
    alive = np.ones((len(weeks), k), dtype=bool)
    vol_rv = characteristics.realized_vol_characteristic(panel, weeks)
    day_count = characteristics.weekly_valid_day_count(panel, weeks)
    window_l = {"returns": returns, "alive": alive, "weeks": weeks, "vol_rv": vol_rv, "day_count": day_count}

    h = prelaunch.h30_feasibility(window_l)
    assert "spread_d10_minus_d1_over_kante" in h and "se_drag_over_kante" in h
    assert h["feasible"] == (h["spread_d10_minus_d1_over_kante"] <= 0.5 and h["se_drag_over_kante"] <= 0.5)
    assert h["n_days_median"] > 0
    assert math.isfinite(h["se_drag_bps"])


# ---- item 5: survivorship drawdown fixture (prelaunch report line) ---------

def test_survivorship_drawdown_fixture_is_deterministic_and_reports_ic_min_units():
    n_weeks, k = 60, 100
    alive = np.ones((n_weeks, k), dtype=bool)
    window = {"returns": np.zeros((n_weeks, k)), "alive": alive, "weeks": [str(i) for i in range(n_weeks)]}
    r1 = prelaunch.survivorship_drawdown_fixture(window, ic_min_mom1=0.02, ic_min_rev_gap=0.02, seed=53)
    r2 = prelaunch.survivorship_drawdown_fixture(window, ic_min_mom1=0.02, ic_min_rev_gap=0.02, seed=53)
    assert r1 == r2                                    # T2 determinism
    assert r1["n_deleted"] > 0
    assert r1["mom1_diff_in_ic_min_units"] == pytest.approx(r1["mom1_diff"] / 0.02)
    assert r1["rev_gap_diff_in_ic_min_units"] == pytest.approx(r1["rev_gap_diff"] / 0.02)
    for key in ("mom1_uncontrolled", "mom1_controlled", "rev_gap_uncontrolled", "rev_gap_controlled"):
        assert math.isfinite(r1[key])


# ---- item 6: beta residualization -------------------------------------------

def test_residualize_outcome_pure_beta_panel_gives_near_zero_ic():
    """A PURE-beta panel (returns = beta_i * r_btc, zero idio noise):
    residualizing against the SAME beta/r_btc must drive the residual to
    (near) exactly zero, so the beta characteristic's IC against it is
    ~0 -- the calibration property task brief item 6 asks for."""
    w, k = 60, 40
    rng = np.random.default_rng(4)
    beta_true = rng.uniform(0.5, 2.0, size=k)
    r_btc = rng.normal(0.0, 0.04, size=w)
    returns = beta_true[None, :] * r_btc[:, None]
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    returns_full = np.concatenate([returns, r_btc[:, None]], axis=1)
    alive = np.ones((w, k + 1), dtype=bool)

    beta_8w = characteristics.beta_characteristic(returns_full, symbols, market_symbol="BTCUSDT",
                                                    trail_win=8, min_weeks=4)
    r_btc_col = returns_full[:, symbols.index("BTCUSDT")]
    resid = ic.residualize_outcome(returns_full, beta_8w, r_btc_col)
    finite = resid[~np.isnan(resid)]
    assert np.max(np.abs(finite)) < 1e-6            # exact beta -> residual ~ 0 exactly

    res = ic.weekly_ic_series(beta_8w, resid, alive, convention="close_at_last", min_universe=5)
    assert abs(res["mean_ic"]) < 0.05


# ---- item 7: adversarial fixture v2 (AR(1) market factor, heterogeneous beta) ---

def test_adversarial_v2_residualized_ic_near_zero_and_bounded_by_factor_null():
    """DEC-75 Entscheidung 1 (3)/task brief item 7: market factor with
    drift and AR(1) rho=0.2, betas 0.5..2.0, NO true cross-sectional
    predictability -- raw mom1 IC may be non-zero (a market-timing
    artifact, Review B-9), but (a) the RESIDUALIZED IC is close to zero,
    and (b) the raw IC stays within the factor-preserving null's
    registered one-sided quantile (with a documented tolerance for a
    finite-replicate Monte Carlo estimate -- exact equality is not
    expected)."""
    seed = 7
    rng = np.random.default_rng(seed)
    w, k = 104, 150
    rho_f, drift_f, sigma_f = 0.2, 0.002, 0.05
    beta_true = rng.uniform(0.5, 2.0, size=k)
    f = np.empty(w)
    f[0] = drift_f / (1.0 - rho_f) + sigma_f * rng.standard_normal()
    for t in range(1, w):
        f[t] = drift_f + rho_f * f[t - 1] + sigma_f * rng.standard_normal()
    idio = rng.normal(0.0, sigma_f, size=(w, k))       # idio vol matched to sigma_f -- realistic ratio
    returns = beta_true[None, :] * f[:, None] + idio
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    returns_full = np.concatenate([returns, f[:, None]], axis=1)   # BTCUSDT == f_t exactly
    alive = np.ones((w, k + 1), dtype=bool)

    mom1 = characteristics.momentum_characteristic(returns_full, trail_win=1)
    res_raw = ic.weekly_ic_series(mom1, returns_full, alive, convention="close_at_last")

    beta_8w = characteristics.beta_characteristic(returns_full, symbols, market_symbol="BTCUSDT",
                                                    trail_win=8, min_weeks=4)
    r_btc = returns_full[:, symbols.index("BTCUSDT")]
    resid = ic.residualize_outcome(returns_full, beta_8w, r_btc)
    res_resid = ic.weekly_ic_series(mom1, resid, alive, convention="close_at_last")

    assert abs(res_resid["mean_ic"]) < 0.03
    assert abs(res_raw["mean_ic"]) > 2.0 * abs(res_resid["mean_ic"])   # raw artifact clearly bigger

    fp = nulls.factor_preserving_null(returns_full, alive, symbols, variants=("mom1",),
                                       n_reps=200, seed=53)
    q = fp["variants"]["mom1"]["quantile_one_sided"]
    assert abs(res_raw["mean_ic"]) <= abs(q) * 1.75 + 0.02   # bounded, with a documented MC tolerance


# ============================================================================
# DEC-76 Vorlauf v3 -- Task A item 1: idiosyncratic sigma_e, drift_f
# configurations, residualized factor-preserving-null fields
# ============================================================================

def test_idiosyncratic_vol_excludes_market_and_is_smaller_than_naive_total():
    """A pure-beta panel (returns = beta_i * r_btc + idio_i, idio SD much
    smaller than the market's own SD): the idiosyncratic sigma_e must be
    close to the TRUE idio SD, clearly smaller than the naive per-symbol
    TOTAL SD (which is inflated by each symbol's own beta*market
    component) -- the DEC-76 "Anlass" double-counting bug this function
    fixes."""
    w, k = 200, 30
    rng = np.random.default_rng(21)
    beta_true = rng.uniform(0.5, 2.0, size=k)
    r_btc = rng.normal(0.0, 0.05, size=w)
    idio_sd_true = 0.01
    idio = rng.normal(0.0, idio_sd_true, size=(w, k))
    returns = beta_true[None, :] * r_btc[:, None] + idio
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    returns_full = np.concatenate([returns, r_btc[:, None]], axis=1)

    res = nulls.idiosyncratic_vol_from_beta_regression(returns_full, symbols, market_symbol="BTCUSDT")
    assert res["market_symbol"] == "BTCUSDT"
    assert "BTCUSDT" not in res["per_symbol_residual_sd"]        # market excluded from its own median
    assert res["n_symbols_used"] == k
    assert res["sigma_e_idiosyncratic"] == pytest.approx(idio_sd_true, rel=0.25)

    naive_total_sd = float(np.median(np.std(returns_full[:, :k], axis=0, ddof=1)))
    assert res["sigma_e_idiosyncratic"] < naive_total_sd          # strictly smaller: no double-counting


def test_idiosyncratic_vol_nan_when_market_symbol_absent():
    returns = np.random.default_rng(0).normal(0, 0.03, size=(20, 5))
    symbols = [f"s{i}" for i in range(5)]
    res = nulls.idiosyncratic_vol_from_beta_regression(returns, symbols, market_symbol="BTCUSDT")
    assert math.isnan(res["sigma_e_idiosyncratic"])
    assert res["n_symbols_used"] == 0


def test_factor_preserving_null_drift_f_configurations_report_raw_and_residualized():
    """DEC-76 Entscheidung 2 (Vorlauf v3): one call = one (rho_f, drift_f)
    configuration; drift_f=0 ("driftfree") vs. drift_f=0.002 ("drifting")
    are two SEPARATE calls, each reporting RAW (unchanged DEC-75 fields)
    AND residualized (DEC-76, additive) statistics side by side."""
    n_weeks, k = 60, 60
    rng = np.random.default_rng(3)
    returns = rng.normal(0, 0.03, size=(n_weeks, k))
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    alive = np.ones((n_weeks, k), dtype=bool)

    drifting = nulls.factor_preserving_null(returns, alive, symbols, variants=("mom1", "rev_gap"),
                                             n_reps=40, seed=53, drift_f=nulls.DRIFT_F_DRIFTING)
    driftfree = nulls.factor_preserving_null(returns, alive, symbols, variants=("mom1", "rev_gap"),
                                              n_reps=40, seed=53, drift_f=nulls.DRIFT_F_DRIFTFREE)

    assert drifting["drift_f"] == pytest.approx(0.002)
    assert driftfree["drift_f"] == 0.0
    assert drifting["rho_f"] == driftfree["rho_f"] == pytest.approx(0.2)

    for fp in (drifting, driftfree):
        assert math.isfinite(fp["sigma_e_median_symbol_weekly"])                     # old (total), unchanged
        assert math.isfinite(fp["sigma_e_median_symbol_weekly_idiosyncratic"])       # new (DEC-76 (e))
        assert fp["sigma_e_used_in_simulation"] == pytest.approx(
            fp["sigma_e_median_symbol_weekly_idiosyncratic"])                        # (e): idio value USED
        assert math.isfinite(fp["selection_ceiling_mean_of_max"])                    # unchanged (raw)
        assert math.isfinite(fp["selection_ceiling_mean_of_max_residualized"])       # DEC-76 (c), additive
        for v in ("mom1", "rev_gap"):
            vv = fp["variants"][v]
            assert math.isfinite(vv["factor_sd"]) and math.isfinite(vv["quantile_one_sided"])
            assert math.isfinite(vv["factor_sd_residualized"])
            assert math.isfinite(vv["quantile_one_sided_residualized"])
            assert vv["quantile_level_residualized"] == vv["quantile_level"]


def test_factor_preserving_null_no_market_symbol_residualized_fields_are_none():
    n_weeks, k = 40, 30
    rng = np.random.default_rng(5)
    returns = rng.normal(0, 0.03, size=(n_weeks, k))
    symbols = [f"s{i}" for i in range(k)]     # no BTCUSDT
    alive = np.ones((n_weeks, k), dtype=bool)
    fp = nulls.factor_preserving_null(returns, alive, symbols, variants=("mom1",), n_reps=10, seed=53)
    assert fp["selection_ceiling_mean_of_max_residualized"] is None
    v = fp["variants"]["mom1"]
    assert v["factor_sd_residualized"] is None and v["quantile_one_sided_residualized"] is None


def test_factor_preserving_null_residualization_shrinks_drifting_mean_toward_zero():
    """DEC-76 "Anlass": under the DRIFTING null, the RESIDUALIZED mean IC
    must sit much closer to 0 than the RAW mean IC (the raw null's
    positive mean IS beta-driven market-timing, exactly what
    residualisation removes) -- the empirical property the whole DEC-76
    fix rests on."""
    n_weeks, k = 104, 150
    rng = np.random.default_rng(9)
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    alive = np.ones((n_weeks, k), dtype=bool)
    returns = rng.normal(0, 0.03, size=(n_weeks, k))       # sigma_f/sigma_e derived from this, real construction

    fp = nulls.factor_preserving_null(returns, alive, symbols, variants=("mom1",), n_reps=150, seed=53,
                                       drift_f=nulls.DRIFT_F_DRIFTING)
    v = fp["variants"]["mom1"]
    assert abs(v["mean_ic_draws_mean_residualized"]) < abs(v["mean_ic_draws_mean"]) + 1e-9


# ============================================================================
# DEC-76 -- prelaunch.factor_preserving_report (Task A item 1/2 wrapper)
# ============================================================================

def test_factor_preserving_report_wraps_both_configurations():
    n_weeks, k = 60, 60
    rng = np.random.default_rng(4)
    returns = rng.normal(0, 0.03, size=(n_weeks, k))
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    alive = np.ones((n_weeks, k), dtype=bool)
    window = {"returns": returns, "alive": alive}
    rep = prelaunch.factor_preserving_report(window, symbols, variants=("mom1",), n_reps=15, seed=53)
    assert set(rep.keys()) >= {"drifting", "driftfree", "binding", "report_only", "label"}
    assert rep["drifting"]["drift_f"] == pytest.approx(nulls.DRIFT_F_DRIFTING)
    assert rep["driftfree"]["drift_f"] == nulls.DRIFT_F_DRIFTFREE
    assert math.isfinite(rep["driftfree"]["selection_ceiling_mean_of_max_residualized"])


# ============================================================================
# end-to-end --prelaunch CLI (existing suite continues below)
# ============================================================================

def test_cli_prelaunch_end_to_end_synthetic_union_tree(tmp_path):
    _panel, _weekly, surv_base, surv_manifest, del_base, del_manifest, _dd = \
        _build_prelaunch_fixture_tree(tmp_path)
    out_dir = tmp_path / "out"
    # DEC-78 Nachtrag: this fixture's tiny (12-symbol) panel is far too statistically
    # underpowered for the Gegenprobe's own sampling noise (verified: the search does not
    # reliably converge at this K) -- this test exercises the CLI/pipeline WIRING, not the
    # calibration search's statistical quality (that is exercised, at a realistic K, by the
    # dedicated nulls.py tests), so it widens the tolerance/keeps the search cheap. A REAL run
    # (scripts/wp13_xsec.py's own CLI defaults) never does this.
    # DEC-81: z-test and search precision switched off the same way (gegenprobe_z_max,
    # calibration_search_rel_tol), probes kept small.
    ns = _ns_prelaunch(panel_base=str(surv_base), delisted_base=str(del_base), out=str(out_dir),
                        gegenprobe_n_reps=10, gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9,
                        no_gegenprobe_market_check=True,
                        calibration_search_n_reps=5, calibration_search_rel_tol=10.0,
                        calibration_search_max_iter=8)

    rc = WP13.cmd_prelaunch(ns)
    assert rc == 0
    assert (out_dir / "wp13a_prelaunch.json").is_file()
    assert (out_dir / "wp13a_prelaunch.md").is_file()
    assert (out_dir / "wp13a_prelaunch_L_window_sealed.json").is_file()

    payload = __import__("json").loads((out_dir / "wp13a_prelaunch.json").read_text(encoding="utf-8"))
    assert payload["windows"]["W1"]["available"] is True
    assert payload["windows"]["W2"]["available"] is True
    assert payload["windows"]["L"]["note"]   # sealed elsewhere, not inlined
    assert payload["windows"]["W1"]["delisting"]["n_symbol_weeks_delisting"] >= 1
    assert payload["reversal_gap_design_deviation"]
    assert payload["selection_ceiling_scale_factor_interpretation"]
    # DEC-77 Entscheidung 1, revised by DEC-78 Entscheidung 1/Nachtrag -- Vorlauf v5: the
    # calibration block/decision table/full method-study grid is present for both judged
    # windows (never for L) -- the Gegenprobe is EXPECTED to pass (by construction, since
    # beta_sd is bisection-calibrated) and is never caught any more, so this either completes
    # with the full shape or the test itself fails loud (a real bug, per the Nachtrag).
    for wn in ("W1", "W2"):
        w1 = payload["windows"][wn]
        assert "factor_calibration" in w1 and "beta_control_method_study" in w1
        assert "beta_control_decision" in w1
        assert "beta_sd_true" in w1["factor_calibration"]
        study = w1["beta_control_method_study"]
        assert set(study["calibrations"].keys()) == set(nulls.FACTOR_NULL_CALIBRATIONS)
        assert set(study["methods"]) == set(nulls.BETA_CONTROL_METHODS_GRID)
        assert len(w1["beta_control_decision"]["rows"]) == len(nulls.BETA_CONTROL_METHODS_GRID)
        for cal in nulls.FACTOR_NULL_CALIBRATIONS:
            c = study["calibrations"][cal]
            assert "gegenprobe" in c and c["gegenprobe"]["ok"] is True
            assert "calibration_search" in c
            # DEC-81: the search/Gegenprobe run on the real measurement's cross-section (the
            # fixture's ~12 alive symbols per week), the standard-error fields are in the artifact.
            assert 10 <= c["calibration_mask_k_median"] <= 13
            assert c["calibration_search"]["crn"] is True
            assert c["calibration_search"]["mask_k_median"] == c["calibration_mask_k_median"]
            for key in ("se_gegenprobe", "search_se", "se_diff", "z", "z_max", "power_ok", "seed"):
                assert key in c["gegenprobe"]
            assert c["gegenprobe"]["seed"] == 53 + nulls.GEGENPROBE_SEED_OFFSET
    assert "beta_control_recommendation" in payload


# ============================================================================
# DEC-77 Entscheidung 1 -- Vorlauf v4: beta-control METHODS (ic.py, pure)
# ============================================================================

def test_beta_control_trail_weeks_known_methods_and_unknown_loud_fail():
    assert ic.beta_control_trail_weeks("none") is None
    assert ic.beta_control_trail_weeks("ts_resid_8w") == 8
    assert ic.beta_control_trail_weeks("fm_neutral_13w") == 13
    assert ic.beta_control_trail_weeks("double_sort_26w") == 26
    with pytest.raises(ValueError):
        ic.beta_control_trail_weeks("nonexistent_method")


def test_trailing_beta_coverage_counts_alive_and_finite():
    alive = np.array([[True, True, False], [True, True, True]])
    beta = np.array([[1.0, np.nan, 0.5], [np.nan, 2.0, 1.5]])
    cov = ic.trailing_beta_coverage(beta, alive)
    assert cov["n_alive_symbol_weeks"] == 5           # 5 of the 6 symbol-weeks are alive
    # alive AND finite-beta: (0,0)=1.0, (1,1)=2.0, (1,2)=1.5 -> 3 (the (0,1)/(1,0) alive
    # positions have NaN beta and do not count).
    expected = int((alive & ~np.isnan(beta)).sum())
    assert expected == 3
    assert cov["n_covered_symbol_weeks"] == 3
    assert cov["n_covered_symbol_weeks"] == expected
    assert cov["coverage_fraction"] == pytest.approx(expected / 5)


def test_apply_beta_control_none_is_passthrough():
    w, k = 10, 5
    rng = np.random.default_rng(1)
    char = rng.normal(size=(w, k))
    returns = rng.normal(size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    out = ic.apply_beta_control("none", char, returns, alive)
    assert out["characteristic"] is char
    assert out["returns"] is returns
    assert out["coverage"] is None


def test_apply_beta_control_unknown_method_loud_fail():
    w, k = 10, 5
    char = np.zeros((w, k))
    returns = np.zeros((w, k))
    alive = np.ones((w, k), dtype=bool)
    with pytest.raises(ValueError):
        ic.apply_beta_control("bogus_method", char, returns, alive)


def test_apply_beta_control_missing_beta_pit_loud_fail():
    w, k = 10, 5
    char = np.zeros((w, k))
    returns = np.zeros((w, k))
    alive = np.ones((w, k), dtype=bool)
    with pytest.raises(ValueError, match="beta_pit"):
        ic.apply_beta_control("ts_resid_8w", char, returns, alive, symbols=[f"s{i}" for i in range(k)])


def test_ts_resid_via_apply_beta_control_true_beta_removes_factor_exactly():
    """DEC-77 item 6: ts_resid with the TRUE beta removes the factor
    exactly (same property as ic.residualize_outcome's own unit test,
    exercised here through the apply_beta_control dispatcher, the code
    path the simulation/run actually use)."""
    w, k = 80, 40
    rng = np.random.default_rng(4)
    beta_true = rng.uniform(0.5, 2.0, size=k)
    r_btc = rng.normal(0.0, 0.04, size=w)
    returns = beta_true[None, :] * r_btc[:, None]          # zero idio noise
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    returns_full = np.concatenate([returns, r_btc[:, None]], axis=1)
    alive = np.ones((w, k + 1), dtype=bool)
    beta_8w = characteristics.beta_characteristic(returns_full, symbols, market_symbol="BTCUSDT",
                                                    trail_win=8, min_weeks=8)
    char = np.zeros((w, k + 1))     # characteristic is irrelevant to this property
    out = ic.apply_beta_control("ts_resid_8w", char, returns_full, alive, beta_pit=beta_8w, symbols=symbols)
    finite = out["returns"][~np.isnan(out["returns"])]
    assert np.max(np.abs(finite)) < 1e-6


def test_fm_neutralize_outcome_residuals_orthogonal_to_beta():
    """DEC-77 item 6: FM residuals have (near) zero cross-sectional
    correlation with beta -- structural OLS property, checked per outcome
    week directly (not just in aggregate)."""
    w, k = 40, 60
    rng = np.random.default_rng(6)
    beta_pit = np.tile(rng.uniform(0.5, 2.0, size=k), (w, 1))
    returns = rng.normal(0, 0.03, size=(w, k)) + beta_pit * rng.normal(0, 0.05, size=(w, 1))
    alive = np.ones((w, k), dtype=bool)
    resid = ic.fm_neutralize_outcome(returns, beta_pit, alive, min_universe=5)
    for t in range(w - 1):
        row = resid[t + 1]
        valid = ~np.isnan(row)
        if int(valid.sum()) < 5:
            continue
        x = beta_pit[t, valid] - beta_pit[t, valid].mean()
        y = row[valid]
        corr_num = float(np.dot(x, y))
        assert abs(corr_num) < 1e-6 * max(1.0, float(np.abs(y).max()))


def test_double_sort_characteristic_within_quintile_permutation():
    """DEC-77 item 6: for every week, each beta-quintile's output values
    are an EXACT permutation of 1..bucket_size."""
    w, k = 12, 47   # deliberately not a multiple of 5
    rng = np.random.default_rng(8)
    beta_pit = rng.uniform(0.5, 2.0, size=(w, k))
    characteristic = rng.normal(size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    out = ic.double_sort_characteristic(characteristic, beta_pit, alive, n_quintiles=5)

    for t in range(w):
        order = np.argsort(beta_pit[t], kind="mergesort")
        n = k
        for q in range(5):
            lo, hi = (n * q) // 5, (n * (q + 1)) // 5
            members = order[lo:hi]
            vals = sorted(out[t, members].tolist())
            assert vals == list(range(1, len(members) + 1)), (t, q, vals)


def test_double_sort_characteristic_skips_thin_weeks():
    w, k = 3, 3        # fewer than n_quintiles=5 alive symbols every week
    beta_pit = np.random.default_rng(0).uniform(0.5, 2.0, size=(w, k))
    characteristic = np.random.default_rng(1).normal(size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    out = ic.double_sort_characteristic(characteristic, beta_pit, alive, n_quintiles=5)
    assert np.isnan(out).all()


# ============================================================================
# DEC-77 Entscheidung 1 (a) -- Vorlauf v4: factor-null calibration (nulls.py)
# ============================================================================

def test_trailing_pit_beta_excluding_current_week_shifts_by_one_and_excludes_week_t():
    w, k = 60, 20
    rng = np.random.default_rng(2)
    r_btc = rng.normal(0.0, 0.04, size=w)
    beta_true = rng.uniform(0.5, 2.0, size=k)
    returns = beta_true[None, :] * r_btc[:, None]
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    returns_full = np.concatenate([returns, r_btc[:, None]], axis=1)

    beta_all = characteristics.beta_characteristic(returns_full, symbols, market_symbol="BTCUSDT",
                                                     trail_win=26, min_weeks=26)
    beta_prev = nulls.trailing_pit_beta_excluding_current_week(returns_full, symbols, market_symbol="BTCUSDT",
                                                                trail_win=26)
    assert np.isnan(beta_prev[0]).all()
    assert np.allclose(beta_prev[1:], beta_all[:-1], equal_nan=True)


def test_measure_market_factor_recovers_known_rho_f_and_sigma_f():
    w = 400
    rho_f, sigma_f = 0.35, 0.04
    rng = np.random.default_rng(3)
    f = np.empty(w)
    f[0] = sigma_f * rng.standard_normal()
    for t in range(1, w):
        f[t] = rho_f * f[t - 1] + sigma_f * rng.standard_normal()
    symbols = ["AAAUSDT", "BTCUSDT"]
    returns = np.column_stack([rng.normal(0, 0.03, size=w), f])
    res = nulls.measure_market_factor(returns, symbols, market_symbol="BTCUSDT")
    assert res["rho_f_measured"] == pytest.approx(rho_f, abs=0.12)
    assert res["sigma_f"] == pytest.approx(sigma_f, rel=0.15)
    assert res["n_weeks_used"] == w


def test_measure_market_factor_nan_when_market_absent():
    returns = np.zeros((10, 3))
    res = nulls.measure_market_factor(returns, ["a", "b", "c"], market_symbol="BTCUSDT")
    assert math.isnan(res["rho_f_measured"]) and math.isnan(res["sigma_f"])


def test_factor_share_from_trailing_beta_high_for_pure_beta_panel():
    """A near-pure-beta panel (small idio noise): the median cross-
    sectional R^2 of return on the (previous-week) trailing beta must be
    close to 1 -- beta alone almost fully explains the cross-section."""
    w, k = 120, 60
    rng = np.random.default_rng(5)
    beta_true = rng.uniform(0.5, 2.0, size=k)
    r_btc = rng.normal(0.0, 0.05, size=w)
    idio = rng.normal(0.0, 0.001, size=(w, k))
    returns = beta_true[None, :] * r_btc[:, None] + idio
    symbols = [f"s{i}" for i in range(k)] + ["BTCUSDT"]
    returns_full = np.concatenate([returns, r_btc[:, None]], axis=1)
    alive = np.ones((w, k + 1), dtype=bool)
    beta_prev = nulls.trailing_pit_beta_excluding_current_week(returns_full, symbols, market_symbol="BTCUSDT",
                                                                 trail_win=26)
    share = nulls.factor_share_from_trailing_beta(returns_full, alive, beta_prev, min_universe=10)
    assert share["factor_share_median"] > 0.9
    assert share["n_weeks_used"] > 0


def test_beta_dispersion_from_trailing_beta_matches_pooled_stats():
    beta_prev = np.array([[1.0, 2.0, np.nan], [3.0, np.nan, 4.0]])
    alive = np.array([[True, True, True], [True, True, True]])
    disp = nulls.beta_dispersion_from_trailing_beta(beta_prev, alive)
    pooled = nulls.pooled_finite_beta(beta_prev, alive)
    assert sorted(pooled.tolist()) == [1.0, 2.0, 3.0, 4.0]
    assert disp["n_pooled"] == 4
    assert disp["mean"] == pytest.approx(pooled.mean())
    assert disp["quantiles"]["0.5"] == pytest.approx(float(np.quantile(pooled, 0.5)))


def test_factor_calibration_report_assembles_all_three_plus_analytic_line():
    w, k = 60, 30
    rng = np.random.default_rng(9)
    returns = rng.normal(0, 0.03, size=(w, k))
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    alive = np.ones((w, k), dtype=bool)
    beta_prev = nulls.trailing_pit_beta_excluding_current_week(returns, symbols, market_symbol="BTCUSDT",
                                                                 trail_win=26)
    report = nulls.factor_calibration_report(returns, alive, symbols, beta_prev, market_symbol="BTCUSDT")
    assert set(report.keys()) >= {"market_factor", "factor_share", "beta_dispersion",
                                    "analytic_mechanical_momentum", "beta_trail_weeks",
                                    "sigma_e_used", "beta_sd_true"}
    assert report["beta_trail_weeks"] == 26
    assert "KEIN Verdikt" in report["analytic_mechanical_momentum"]["label"]
    assert "DEC-78" in report["beta_sd_true"]["label"]


# ============================================================================
# DEC-78 Entscheidung 1 -- Vorlauf v5: true_beta_sd_from_factor_share +
# the Gegenprobe (nulls.py, pure)
# ============================================================================

def test_true_beta_sd_from_factor_share_formula_and_guards():
    # sqrt(0.0162/0.9838) * 0.057/0.0669 -- DEC-78 "Anlass", W1 numbers, verbatim.
    beta_sd = nulls.true_beta_sd_from_factor_share(0.0162, 0.057, 0.0669)
    assert beta_sd == pytest.approx(0.109, abs=0.002)
    assert nulls.true_beta_sd_from_factor_share(0.0, 0.05, 0.05) == pytest.approx(0.0)
    # guards: NaN/non-finite/degenerate inputs never fabricate a value.
    assert math.isnan(nulls.true_beta_sd_from_factor_share(float("nan"), 0.05, 0.05))
    assert math.isnan(nulls.true_beta_sd_from_factor_share(0.1, float("nan"), 0.05))
    assert math.isnan(nulls.true_beta_sd_from_factor_share(0.1, 0.05, 0.0))
    assert math.isnan(nulls.true_beta_sd_from_factor_share(0.1, 0.05, -0.01))
    # share >= 1 is clipped (0.999), never a ZeroDivisionError/negative-sqrt domain error.
    assert math.isfinite(nulls.true_beta_sd_from_factor_share(1.5, 0.05, 0.05))


def test_true_beta_sd_from_factor_share_identity_reproduced_in_large_panel():
    """DEC-78 task brief item 6: the share is reproduced within +/-10% in
    a LARGE simulated panel -- this validates the FORMULA's own algebra
    (the population relationship it inverts: factor_share =
    (beta_sd*sigma_f)^2 / ((beta_sd*sigma_f)^2 + sigma_e^2)), checked via
    the MEAN cross-sectional R^2 of return on the panel's TRUE (population)
    beta over many weeks/replicates -- the quantity the formula's
    algebraic derivation is exact for. (The SEPARATE, much noisier
    "median of weekly R^2 on a RE-ESTIMATED trailing PIT beta" pipeline --
    :func:`nulls.factor_share_gegenprobe`, the SAME one the real
    ``factor_share_measured`` uses -- carries its OWN, well-documented
    estimation-noise/median-vs-mean gap, see that function's docstring;
    this test isolates the closed-form formula's own correctness from
    that separate, acknowledged effect.)"""
    sigma_f, sigma_e = 0.0669, 0.057      # DEC-78 W1 measured magnitudes
    target_share = 0.0324                 # 2 * W1's measured factor_share (the "stress" target)
    beta_sd = nulls.true_beta_sd_from_factor_share(target_share, sigma_e, sigma_f)
    n_symbols, n_weeks = 400, 80
    rng = np.random.default_rng(21)
    pooled_r2: list[float] = []
    for _ in range(20):
        sim = nulls.simulate_factor_panel(n_weeks, n_symbols, sigma_f=sigma_f, sigma_e=sigma_e,
                                           rho_f=0.05, drift_f=0.0, rng=rng, beta_sd=beta_sd)
        beta_true = sim["beta"]
        for t in range(n_weeks):
            y = sim["returns"][t]
            if beta_true.std() == 0.0 or y.std() == 0.0:
                continue
            r = float(np.corrcoef(beta_true, y)[0, 1])
            pooled_r2.append(r * r)
    mean_r2 = float(np.mean(pooled_r2))
    assert mean_r2 == pytest.approx(target_share, rel=0.10)


def test_factor_share_gegenprobe_wrong_sigma_e_raises_loud():
    """DEC-78 task brief item 6: a wrong sigma_e (a large multiple of the
    correct one, deliberately breaking the calibration's own internal
    consistency) must raise :class:`nulls.FactorShareCalibrationError`,
    naming both the simulated and target share (C.14 loud fail, never a
    silent report)."""
    sigma_f, sigma_e_correct = 0.05, 0.001
    target_share = 0.8
    beta_sd = nulls.true_beta_sd_from_factor_share(target_share, sigma_e_correct, sigma_f)
    n_symbols, n_weeks = 60, 60
    symbols = [f"s{i}" for i in range(n_symbols - 1)] + ["BTCUSDT"]

    # A WRONG sigma_e (100x too large): the panel is simulated with far more idiosyncratic
    # noise than the calibration's own beta_sd/target_share assume -- the resulting simulated
    # share collapses well outside +/-25% of the (now-inconsistent) target.
    with pytest.raises(nulls.FactorShareCalibrationError, match="Gegenprobe fehlgeschlagen"):
        nulls.factor_share_gegenprobe(
            n_weeks, n_symbols, symbols, sigma_f=sigma_f, sigma_e=sigma_e_correct * 100.0,
            rho_f=0.05, beta_sd=beta_sd, target_share=target_share, n_reps=15, seed=53)


def test_factor_share_gegenprobe_reports_both_numbers_on_failure():
    sigma_f, sigma_e_correct = 0.05, 0.001
    target_share = 0.8
    beta_sd = nulls.true_beta_sd_from_factor_share(target_share, sigma_e_correct, sigma_f)
    n_symbols, n_weeks = 60, 60
    symbols = [f"s{i}" for i in range(n_symbols - 1)] + ["BTCUSDT"]
    try:
        nulls.factor_share_gegenprobe(
            n_weeks, n_symbols, symbols, sigma_f=sigma_f, sigma_e=sigma_e_correct * 100.0,
            rho_f=0.05, beta_sd=beta_sd, target_share=target_share, n_reps=15, seed=53)
        assert False, "expected FactorShareCalibrationError"
    except nulls.FactorShareCalibrationError as exc:
        msg = str(exc)
        assert str(target_share) in msg or "0.8" in msg
        assert "rel_diff" in msg
        # DEC-81: the message also names z and se_diff and which condition is violated.
        assert "z=" in msg and "se_diff=" in msg
        assert "Abweichung > z_max Standardfehler" in msg


def _calibrated_closed_form_case():
    """DEC-81 helper: the 'consistent inputs' fixture of the Gegenprobe tests (large target
    share, negligible idiosyncratic noise), calibrated by the search so the independent
    Gegenprobe can be run under the new standard-error contract."""
    sigma_f, sigma_e, rho_f, target_share = 0.05, 0.001, 0.05, 0.8
    n_symbols, n_weeks = 60, 60
    symbols = [f"s{i}" for i in range(n_symbols - 1)] + ["BTCUSDT"]
    search = nulls.calibrate_beta_sd_to_observed_share(
        target_share, rho_f=rho_f, sigma_f=sigma_f, sigma_e=sigma_e, n_weeks=n_weeks,
        n_symbols=n_symbols, symbols=symbols, seed=53, n_reps=20, rel_tol=0.02, max_iter=25)
    assert search["converged"] is True
    kwargs = dict(sigma_f=sigma_f, sigma_e=sigma_e, rho_f=rho_f, beta_sd=search["beta_sd_calibrated"],
                  target_share=target_share, n_reps=20, search_se=search["achieved_share_se"])
    return n_weeks, n_symbols, symbols, search, kwargs


def test_factor_share_gegenprobe_passes_within_tolerance_for_consistent_inputs():
    """A calibration where the Gegenprobe's OWN methodology (median of
    weekly R^2 on a re-estimated trailing PIT beta) can reproduce its
    target -- large target share, negligible idiosyncratic noise
    (near-zero beta-estimation error) -- confirms the Gegenprobe does NOT
    always raise, only when the calibration is genuinely inconsistent
    (the companion 'wrong sigma_e' test above).

    DEC-81: the contract changed from 'closed-form beta_sd within +/-25 %'
    to a standard-error criterion on an independent seed, so the beta_sd
    is first calibrated by the search (which carries ``achieved_share_se``
    into the Gegenprobe as ``search_se``) -- the closed-form value is only
    an approximation and would fail a z-test it was never calibrated for."""
    n_weeks, n_symbols, symbols, _search, kwargs = _calibrated_closed_form_case()
    result = nulls.factor_share_gegenprobe(
        n_weeks, n_symbols, symbols, seed=53 + nulls.GEGENPROBE_SEED_OFFSET, **kwargs)
    assert result["ok"] is True
    assert result["power_ok"] is True
    assert result["z"] <= nulls.GEGENPROBE_Z_MAX
    assert result["rel_diff"] <= nulls.GEGENPROBE_REL_TOL


def test_factor_share_gegenprobe_determinism_same_seed():
    """DEC-81: the contract changed (see the 'consistent inputs' test), so the determinism
    check runs on the calibrated beta_sd; the new result fields are deterministic too."""
    n_weeks, n_symbols, symbols, _search, kwargs = _calibrated_closed_form_case()
    seed = 53 + nulls.GEGENPROBE_SEED_OFFSET
    r1 = nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, seed=seed, **kwargs)
    r2 = nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, seed=seed, **kwargs)
    assert r1 == r2
    assert r1["seed"] == seed
    r3 = nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, seed=seed + 1, **kwargs)
    assert r3["simulated_factor_share"] != r1["simulated_factor_share"]
    assert r3["se_gegenprobe"] != r1["se_gegenprobe"]


# ============================================================================
# DEC-78 Nachtrag (orchestrator decision) -- calibrate_beta_sd_to_observed_share:
# OBSERVABLE-MATCHING calibration replaces the closed-form beta_sd, bisection on
# log(beta_sd), the Gegenprobe stays literal and is expected to PASS BY CONSTRUCTION.
# ============================================================================

def test_calibrate_beta_sd_to_observed_share_converges_on_synthetic_panel():
    """A fast, moderate-K synthetic panel: the bisection search converges
    (``rel_diff <= rel_tol``) within ``max_iter`` iterations, and a
    SUBSEQUENT, INDEPENDENT :func:`nulls.factor_share_gegenprobe` call
    with the searched ``beta_sd`` passes -- the round-trip property the
    DEC-78 Nachtrag exists for.

    DEC-81: the Gegenprobe criterion is now ``z <= z_max`` on a standard-
    error basis (search SE passed in as ``search_se``) plus a power
    condition, not a fixed +/-25 % band -- so the probes use enough
    replicates (60 search / 150 Gegenprobe) to be resolvable at all."""
    sigma_f, sigma_e, rho_f, target_share = 0.05, 0.01, 0.05, 0.10
    n_symbols, n_weeks = 250, 52
    symbols = [f"s{i}" for i in range(n_symbols - 1)] + ["BTCUSDT"]

    res = nulls.calibrate_beta_sd_to_observed_share(
        target_share, rho_f=rho_f, sigma_f=sigma_f, sigma_e=sigma_e,
        n_weeks=n_weeks, n_symbols=n_symbols, symbols=symbols, seed=7,
        n_reps=60, rel_tol=0.05, max_iter=15)
    assert res["converged"] is True
    assert res["n_iter"] <= 15
    assert math.isfinite(res["beta_sd_calibrated"])
    assert math.isfinite(res["true_share"])
    assert math.isfinite(res["achieved_share_se"]) and res["achieved_share_se"] > 0.0
    assert len(res["trace"]) == res["n_iter"]
    for row in res["trace"]:
        assert set(row.keys()) == {"iter", "beta_sd", "achieved_share", "true_share", "rel_diff"}

    gp = nulls.factor_share_gegenprobe(
        n_weeks, n_symbols, symbols, sigma_f=sigma_f, sigma_e=sigma_e, rho_f=rho_f,
        beta_sd=res["beta_sd_calibrated"], target_share=target_share,
        seed=7 + nulls.GEGENPROBE_SEED_OFFSET, n_reps=150, search_se=res["achieved_share_se"])
    assert gp["ok"] is True


def test_calibrate_beta_sd_to_observed_share_degenerate_target_is_nan_not_a_crash():
    res = nulls.calibrate_beta_sd_to_observed_share(
        0.0, rho_f=0.05, sigma_f=0.05, sigma_e=0.01, n_weeks=20, n_symbols=20, seed=1)
    assert math.isnan(res["beta_sd_calibrated"])
    assert res["converged"] is False
    assert res["n_iter"] == 0
    res_nan = nulls.calibrate_beta_sd_to_observed_share(
        float("nan"), rho_f=0.05, sigma_f=0.05, sigma_e=0.01, n_weeks=20, n_symbols=20, seed=1)
    assert math.isnan(res_nan["beta_sd_calibrated"])


def test_calibrate_beta_sd_to_observed_share_determinism_same_seed():
    kwargs = dict(rho_f=0.05, sigma_f=0.05, sigma_e=0.01, n_weeks=30, n_symbols=60,
                  n_reps=8, rel_tol=0.10, max_iter=8)
    r1 = nulls.calibrate_beta_sd_to_observed_share(0.10, seed=53, **kwargs)
    r2 = nulls.calibrate_beta_sd_to_observed_share(0.10, seed=53, **kwargs)
    assert r1 == r2
    r3 = nulls.calibrate_beta_sd_to_observed_share(0.10, seed=999, **kwargs)
    assert r3["trace"] != r1["trace"]


def test_calibrate_beta_sd_to_observed_share_and_gegenprobe_pass_on_real_w1_numbers():
    """DEC-78 Nachtrag: on the REAL W1 measured magnitudes (rho_f=0.046,
    factor_share=0.0162, sigma_f=0.0669, sigma_e=0.057 -- state/
    decisions.md DEC-78) the bisection search converges and a SEPARATE
    Gegenprobe passes -- a REDUCED K (300, not the production ~1138)
    keeps this fast enough for the unit suite.

    DEC-81: the Gegenprobe is judged on the standard-error criterion (with
    the search's own SE) and needs enough replicates to resolve a 25 %
    deviation of a 1.6 % share (the old 40/30 cannot); to keep the suite
    fast this reuses the cached K=300 search of the regression test below
    (same magnitudes to within rounding: 0.06685/0.05695/0.016245) and
    runs a second, differently seeded Gegenprobe on it."""
    res, symbols, n_weeks, n_symbols = _w1_size_search(0.046)
    assert res["converged"] is True, res["trace"]
    gp = nulls.factor_share_gegenprobe(
        n_weeks, n_symbols, symbols, sigma_f=0.06685, sigma_e=0.05695, rho_f=0.046,
        beta_sd=res["beta_sd_calibrated"], target_share=0.016245,
        seed=53 + nulls.GEGENPROBE_SEED_OFFSET + 1, n_reps=250, search_se=res["achieved_share_se"])
    assert gp["ok"] is True, gp


# ============================================================================
# DEC-81 -- Kalibrierungs-Gegenprobe auf Standardfehler-Basis (Vorlauf v5c):
# bootstrap SE of the pooled-median share, cross-section mask, common random
# numbers, z-test + power condition, loud non-convergence, real-size regression.
# ============================================================================

def _dec81_small_case(n_weeks: int = 40, n_symbols: int = 30):
    symbols = [f"s{i}" for i in range(n_symbols - 1)] + ["BTCUSDT"]
    kw = dict(sigma_f=0.05, sigma_e=0.03, rho_f=0.05, beta_sd=0.4)
    return n_weeks, n_symbols, symbols, kw


def _spy_factor_share(monkeypatch):
    """Record (window_alive, result) of every ``factor_share_from_trailing_beta`` call."""
    calls: list[tuple[np.ndarray, dict]] = []
    orig = nulls.factor_share_from_trailing_beta

    def spy(window_returns, window_alive, beta_prev, **kwargs):
        res = orig(window_returns, window_alive, beta_prev, **kwargs)
        calls.append((window_alive, res))
        return res

    monkeypatch.setattr(nulls, "factor_share_from_trailing_beta", spy)
    return calls


def test_dec81_measure_simulated_share_reports_deterministic_bootstrap_se(monkeypatch):
    """DEC-81: ``se_bootstrap`` is finite and > 0 for n_reps >= 2, deterministic per seed,
    NaN below 2 replicates with R^2 values; ``simulated_share`` is still the plain pooled
    median of every replicate's weekly R^2, and the SE equals an independent slow
    recomputation of the documented recipe (bootstrap over REPLICATES, B draws, ddof=1)."""
    n_weeks, n_symbols, symbols, kw = _dec81_small_case()
    calls = _spy_factor_share(monkeypatch)
    m1 = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=12, seed=53, **kw)
    assert math.isfinite(m1["se_bootstrap"]) and m1["se_bootstrap"] > 0.0
    assert m1["n_reps_with_r2"] == 12
    m2 = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=12, seed=53, **kw)
    assert m1 == m2
    m3 = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=12, seed=54, **kw)
    assert m3["se_bootstrap"] != m1["se_bootstrap"]

    # the first 12 spied calls belong to m1: pooled median unchanged, SE recomputed independently
    per_rep = [np.array([w["r2"] for w in res["per_week"] if w["r2"] is not None]) for _a, res in calls[:12]]
    assert m1["simulated_share"] == float(np.median(np.concatenate(per_rep)))
    rng = np.random.default_rng(53 + nulls.SHARE_SE_BOOTSTRAP_SEED_OFFSET)
    idx = rng.integers(0, len(per_rep), size=(nulls.SHARE_SE_BOOTSTRAP_B, len(per_rep)))
    meds = [float(np.median(np.concatenate([per_rep[i] for i in row]))) for row in idx]
    assert m1["se_bootstrap"] == pytest.approx(float(np.std(meds, ddof=1)), rel=1e-12)

    one = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=1, seed=53, **kw)
    assert math.isnan(one["se_bootstrap"]) and one["n_reps_with_r2"] == 1
    assert math.isfinite(one["simulated_share"])


def test_dec81_bootstrap_se_matches_empirical_sampling_sd_of_the_share():
    """DEC-81: the bootstrap SE is a meaningful standard error -- its mean over 40 seeds
    is within [0.6, 1.6] of the empirical SD of the share over those same 40 independent
    seeds (each a 16-replicate estimate)."""
    n_weeks, n_symbols, symbols, kw = _dec81_small_case(n_weeks=40, n_symbols=60)
    shares, ses = [], []
    for seed in range(40):
        m = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=16, seed=1000 + seed, **kw)
        shares.append(m["simulated_share"])
        ses.append(m["se_bootstrap"])
    ratio = float(np.mean(ses)) / float(np.std(shares, ddof=1))
    assert 0.6 <= ratio <= 1.6, ratio


def test_dec81_measure_simulated_share_mask_limits_the_cross_section(monkeypatch):
    """DEC-81: ``mask`` replaces the all-alive mask -- each simulated week's cross-section
    has exactly the masked size (per_week k), an all-True mask equals the default, a wrong
    shape is a loud ValueError."""
    n_weeks, n_symbols, symbols, kw = _dec81_small_case()
    rng = np.random.default_rng(3)
    mask = np.zeros((n_weeks, n_symbols), dtype=bool)
    for t in range(n_weeks):
        mask[t, rng.permutation(n_symbols)[:12 + (t % 7)]] = True

    calls = _spy_factor_share(monkeypatch)
    nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=2, seed=5, mask=mask, **kw)
    assert len(calls) == 2
    for alive_arg, res in calls:
        assert alive_arg is mask or np.array_equal(alive_arg, mask)
        for row in res["per_week"]:
            t = row["t"]
            # the simulated trailing beta is finite from week 26 on (26 weeks of history)
            assert row["k"] == (int(mask[t].sum()) if t >= 26 else 0)

    calls.clear()
    nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=1, seed=5, **kw)
    assert all(row["k"] == (n_symbols if row["t"] >= 26 else 0) for row in calls[0][1]["per_week"])

    full = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=4, seed=5, **kw)
    all_true = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=4, seed=5,
                                              mask=np.ones((n_weeks, n_symbols), dtype=bool), **kw)
    assert full == all_true
    masked = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=4, seed=5, mask=mask, **kw)
    assert masked["simulated_share"] != full["simulated_share"]

    with pytest.raises(ValueError, match="mask shape"):
        nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=1, seed=5,
                                       mask=np.ones((n_weeks, n_symbols - 1), dtype=bool), **kw)


def test_dec81_calibration_uses_common_random_numbers_and_reproduces_achieved_share():
    """DEC-81: every bisection iteration uses the SAME seed, so re-measuring any trace
    entry's beta_sd with that seed/n_reps reproduces its achieved share EXACTLY (and the
    final one reproduces ``achieved_share``/``achieved_share_se``/``true_share``); the
    sample function beta_sd -> share is deterministic and increasing on a coarse grid."""
    n_weeks, n_symbols, symbols, kw = _dec81_small_case(n_weeks=40, n_symbols=60)
    kw.pop("beta_sd")
    res = nulls.calibrate_beta_sd_to_observed_share(
        0.10, n_weeks=n_weeks, n_symbols=n_symbols, symbols=symbols, seed=11, n_reps=10,
        rel_tol=0.03, max_iter=14, **kw)
    assert res["crn"] is True and len(res["trace"]) >= 3
    assert res["mask_k_median"] == n_symbols
    for row in res["trace"]:
        m = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, beta_sd=row["beta_sd"],
                                           seed=11, n_reps=10, **kw)
        assert m["simulated_share"] == row["achieved_share"]
        assert m["true_share"] == row["true_share"]
    m = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, beta_sd=res["beta_sd_calibrated"],
                                       seed=11, n_reps=10, **kw)
    assert m["simulated_share"] == res["achieved_share"]
    assert m["se_bootstrap"] == res["achieved_share_se"]
    assert m["true_share"] == res["true_share"]

    grid = [nulls._measure_simulated_share(n_weeks, n_symbols, symbols, beta_sd=b, seed=11, n_reps=10,
                                           **kw)["simulated_share"] for b in (0.05, 0.1, 0.2, 0.4, 0.8)]
    assert all(b > a for a, b in zip(grid, grid[1:])), grid


def test_dec81_calibration_forwards_mask_and_reports_its_median_size():
    """DEC-81: ``mask`` reaches the measurement (the share differs from the unmasked one),
    ``mask_k_median`` is the median per-week cross-section size."""
    n_weeks, n_symbols, symbols, kw = _dec81_small_case(n_weeks=40, n_symbols=60)
    kw.pop("beta_sd")
    rng = np.random.default_rng(8)
    mask = rng.random((n_weeks, n_symbols)) < 0.4
    common = dict(n_weeks=n_weeks, n_symbols=n_symbols, symbols=symbols, seed=11, n_reps=6,
                  rel_tol=0.5, max_iter=3, **kw)
    masked = nulls.calibrate_beta_sd_to_observed_share(0.10, mask=mask, **common)
    plain = nulls.calibrate_beta_sd_to_observed_share(0.10, **common)
    assert masked["mask_k_median"] == float(np.median(mask.sum(axis=1)))
    assert plain["mask_k_median"] == n_symbols
    assert masked["trace"][0]["achieved_share"] != plain["trace"][0]["achieved_share"]
    degenerate = nulls.calibrate_beta_sd_to_observed_share(0.0, mask=mask, **common)
    assert degenerate["mask_k_median"] == masked["mask_k_median"] and degenerate["crn"] is True


@functools.lru_cache(maxsize=None)
def _w1_size_search(rho_f: float):
    """DEC-81: the CRN calibration search on the REAL W1 magnitudes (sigma_f 0.06685, sigma_e
    0.05695, target 0.016245) at a reduced K = 300, W = 53 -- cached, the two tests below
    share it (~20 s each otherwise)."""
    n_symbols, n_weeks = 300, 53
    symbols = [f"S{i:03d}" for i in range(n_symbols - 1)] + ["BTCUSDT"]
    res = nulls.calibrate_beta_sd_to_observed_share(
        0.016245, rho_f=rho_f, sigma_f=0.06685, sigma_e=0.05695, n_weeks=n_weeks, n_symbols=n_symbols,
        symbols=symbols, seed=53, n_reps=200)
    return res, symbols, n_weeks, n_symbols


@pytest.mark.parametrize("rho_f", [0.0, 0.046])
def test_dec81_regression_real_w1_sizes_search_converges_gegenprobe_passes_and_has_teeth(rho_f):
    """DEC-81 regression of the wp13a failure (``zero`` calibration: simulated 0.0212 against
    target 0.0162, both runs): the REAL W1 magnitudes (sigma_f 0.06685, sigma_e 0.05695,
    target 0.016245) at a reduced K = 300 (W = 53). The CRN search converges, the INDEPENDENT
    Gegenprobe (other seed, SE criterion incl. the search SE) passes for both rho_f -- and a
    beta_sd 15 % too large is rejected (the Gegenprobe has teeth)."""
    target = 0.016245
    res, symbols, n_weeks, n_symbols = _w1_size_search(rho_f)
    assert res["converged"] is True, res["trace"]
    assert abs(res["achieved_share"] - target) / target <= nulls.CALIBRATION_SEARCH_REL_TOL_DEFAULT

    common = dict(sigma_f=0.06685, sigma_e=0.05695, rho_f=rho_f, target_share=target,
                  seed=53 + nulls.GEGENPROBE_SEED_OFFSET, search_se=res["achieved_share_se"])
    gp = nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, beta_sd=res["beta_sd_calibrated"],
                                       n_reps=250, **common)
    assert gp["ok"] is True and gp["power_ok"] is True
    assert gp["z"] <= nulls.GEGENPROBE_Z_MAX

    with pytest.raises(nulls.FactorShareCalibrationError, match="Gegenprobe fehlgeschlagen"):
        nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols,
                                      beta_sd=1.15 * res["beta_sd_calibrated"], n_reps=100, **common)


def _fake_measure(monkeypatch, simulated_share: float, se: float):
    def fake(*_a, **_k):
        return {"simulated_share": simulated_share, "true_share": simulated_share, "n_r2_pooled": 1000,
                "n_true_r2_pooled": 1000, "se_bootstrap": se, "n_reps_with_r2": 100}
    monkeypatch.setattr(nulls, "_measure_simulated_share", fake)


def _gegenprobe_stub(target: float, **kwargs):
    symbols = [f"s{i}" for i in range(19)] + ["BTCUSDT"]
    return nulls.factor_share_gegenprobe(
        10, 20, symbols, sigma_f=0.05, sigma_e=0.03, rho_f=0.0, beta_sd=0.2, target_share=target, **kwargs)


def test_dec81_gegenprobe_z_formula_with_search_se(monkeypatch):
    """DEC-81: z = |sim - target| / sqrt(se_gegenprobe^2 + search_se^2), computed by hand:
    sim 0.0170, target 0.0162, se 0.0003, search_se 0.0004 -> se_diff 0.0005, z 1.6."""
    _fake_measure(monkeypatch, 0.0170, 0.0003)
    res = _gegenprobe_stub(0.0162, search_se=0.0004)
    assert res["se_gegenprobe"] == pytest.approx(0.0003)
    assert res["search_se"] == pytest.approx(0.0004)
    assert res["se_diff"] == pytest.approx(0.0005)
    assert res["z"] == pytest.approx(0.0008 / 0.0005)
    assert res["z_max"] == nulls.GEGENPROBE_Z_MAX
    assert res["power_ok"] is True and res["ok"] is True
    assert res["rel_diff"] == pytest.approx(0.0008 / 0.0162)

    res0 = _gegenprobe_stub(0.0162)                         # search_se defaults to 0
    assert res0["se_diff"] == pytest.approx(0.0003) and res0["z"] == pytest.approx(0.0008 / 0.0003)

    # z above z_max: raises naming the violated condition, z, se_diff and both shares
    _fake_measure(monkeypatch, 0.0180, 0.0003)
    with pytest.raises(nulls.FactorShareCalibrationError) as exc:
        _gegenprobe_stub(0.0162, search_se=0.0004)
    msg = str(exc.value)
    assert msg.startswith("Gegenprobe fehlgeschlagen")
    assert "Abweichung > z_max Standardfehler" in msg and "unterpowert" not in msg
    assert float(re.search(r"z=([0-9.]+)", msg).group(1)) == pytest.approx(3.6)
    assert float(re.search(r"se_diff=([0-9.e-]+)", msg).group(1)) == pytest.approx(0.0005)
    assert "0.018" in msg and "0.0162" in msg
    # ... and the very same numbers pass with a larger z_max
    assert _gegenprobe_stub(0.0162, search_se=0.0004, z_max=4.0)["ok"] is True


def test_dec81_gegenprobe_power_condition_and_nan(monkeypatch):
    """DEC-81: z = 0 but 3 * se_diff > rel_tol * target -> 'unterpowert: n_reps erhoehen';
    NaN share or NaN SE is never ok."""
    _fake_measure(monkeypatch, 0.0162, 0.003)                 # exact hit, but a hopelessly noisy probe
    with pytest.raises(nulls.FactorShareCalibrationError) as exc:
        _gegenprobe_stub(0.0162)
    msg = str(exc.value)
    assert "unterpowert: n_reps erhoehen" in msg and "Abweichung > z_max" not in msg
    # the same probe is fine when the resolvable deviation is widened (rel_tol * target >= 3 * se_diff)
    res = _gegenprobe_stub(0.0162, rel_tol=1.0)
    assert res["ok"] is True and res["z"] == 0.0 and res["power_ok"] is True

    _fake_measure(monkeypatch, float("nan"), 0.0003)
    with pytest.raises(nulls.FactorShareCalibrationError, match="Gegenprobe fehlgeschlagen"):
        _gegenprobe_stub(0.0162)
    _fake_measure(monkeypatch, 0.0162, float("nan"))
    with pytest.raises(nulls.FactorShareCalibrationError, match="nicht berechenbar"):
        _gegenprobe_stub(0.0162)


@pytest.mark.parametrize("rel_dev", [0.26, 0.5, -0.3])
@pytest.mark.parametrize("se", [1e-7, 1e-4, 1e-3, 3e-3, 1e-2])
def test_dec81_gegenprobe_is_never_looser_than_the_old_band(monkeypatch, rel_dev, se):
    """DEC-81: whatever the standard error, a deviation beyond the old +/-25 % band never
    passes -- a tiny SE trips the z-test, a large SE the power condition."""
    target = 0.0162
    _fake_measure(monkeypatch, target * (1.0 + rel_dev), se)
    with pytest.raises(nulls.FactorShareCalibrationError, match="Gegenprobe fehlgeschlagen"):
        _gegenprobe_stub(target)


def test_dec81_gegenprobe_underpowered_with_tiny_n_reps_raises_unterpowert():
    """DEC-81: a probe with a handful of replicates cannot resolve a 25 % miscalibration. The
    target is set to the probe's own share (z == 0), so ONLY the power condition can fail.

    DEC-85: 4 replicates instead of 3 -- with the market column := factor the seed-5 trio of
    replicates happens to agree closely (bootstrap SE 0.0025, i.e. 3*se < 0.25*share), so the
    3-replicate probe no longer demonstrates the under-power; seed 5 / 4 replicates does."""
    n_weeks, n_symbols, symbols, kw = _dec81_small_case()
    own = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=4, seed=5, **kw)
    with pytest.raises(nulls.FactorShareCalibrationError, match="unterpowert") as exc:
        nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, target_share=own["simulated_share"],
                                      n_reps=4, seed=5, **kw)
    assert "Abweichung > z_max" not in str(exc.value)
    # with a widened resolvable deviation the very same probe passes at z == 0
    res = nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, target_share=own["simulated_share"],
                                        n_reps=4, seed=5, rel_tol=10.0, **kw)
    assert res["ok"] is True and res["z"] == 0.0


def test_dec81_study_raises_loud_when_a_search_does_not_converge():
    """DEC-81: ``converged is False`` aborts the study at once, naming the calibration, the
    target and the last trace entry (formerly the last value was silently taken over)."""
    w, k = 40, 30
    rng = np.random.default_rng(13)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    with pytest.raises(nulls.FactorShareCalibrationError, match="nicht konvergiert") as exc:
        nulls.beta_control_method_study(
            returns, alive, symbols, rho_f_measured=0.3, factor_share_measured=0.02,
            variants=("mom1",), methods=("none",), n_reps=2, seed=53, gegenprobe_n_reps=5,
            calibration_search_n_reps=4, calibration_search_rel_tol=1e-6, calibration_search_max_iter=1)
    msg = str(exc.value)
    assert "'measured'" in msg and "0.02" in msg and "'iter': 0" in msg
    # a degenerate (NaN) target has no trace at all but is just as loud
    with pytest.raises(nulls.FactorShareCalibrationError, match="nicht konvergiert"):
        nulls.beta_control_method_study(
            returns, alive, symbols, rho_f_measured=0.3, factor_share_measured=float("nan"),
            variants=("mom1",), methods=("none",), n_reps=2, seed=53, gegenprobe_n_reps=5)


def test_dec81_study_forwards_calibration_mask_to_searches_and_gegenproben(monkeypatch):
    """DEC-81: ``calibration_mask`` reaches all three searches and all three Gegenproben;
    each calibration reports ``calibration_mask_k_median``; the Gegenprobe draws from
    ``seed + GEGENPROBE_SEED_OFFSET`` with the search's own SE and ``gegenprobe_z_max``."""
    w, k = 40, 30
    rng = np.random.default_rng(13)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    mask = np.zeros((w, k), dtype=bool)
    mask[:, :18] = True
    seen: list[tuple[str, np.ndarray, dict]] = []
    orig_search, orig_gp = nulls.calibrate_beta_sd_to_observed_share, nulls.factor_share_gegenprobe

    def spy_search(*a, **kw):
        seen.append(("search", kw.get("mask"), kw))
        return orig_search(*a, **kw)

    def spy_gp(*a, **kw):
        seen.append(("gegenprobe", kw.get("mask"), kw))
        return orig_gp(*a, **kw)

    monkeypatch.setattr(nulls, "calibrate_beta_sd_to_observed_share", spy_search)
    monkeypatch.setattr(nulls, "factor_share_gegenprobe", spy_gp)
    study = nulls.beta_control_method_study(
        returns, alive, symbols, rho_f_measured=0.3, factor_share_measured=0.02,
        variants=("mom1",), methods=("none",), n_reps=2, seed=53, gegenprobe_n_reps=10,
        gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9, calibration_search_n_reps=5,
        calibration_search_rel_tol=10.0, calibration_search_max_iter=4, calibration_mask=mask)
    assert [kind for kind, _m, _kw in seen].count("search") == 3
    assert [kind for kind, _m, _kw in seen].count("gegenprobe") == 3
    for kind, m, kw in seen:
        assert m is mask
        if kind == "gegenprobe":
            assert kw["seed"] == 53 + nulls.GEGENPROBE_SEED_OFFSET and kw["z_max"] == 1e9
            assert kw["n_reps"] == 10
    for cal in nulls.FACTOR_NULL_CALIBRATIONS:
        assert study["calibrations"][cal]["calibration_mask_k_median"] == 18.0
        assert (study["calibrations"][cal]["gegenprobe"]["search_se"]
                == study["calibrations"][cal]["calibration_search"]["achieved_share_se"])


def test_dec81_prelaunch_passes_the_real_measurement_cross_section_as_calibration_mask(tmp_path, monkeypatch):
    """DEC-81 (F): per window the study gets exactly ``alive & finite beta_prev_26w & finite
    returns`` -- the cross-section ``factor_share_from_trailing_beta`` measures on real data
    -- and the new ``gegenprobe_z_max`` knob.

    DEC-85 (iii): "returns" and "beta_prev_26w" there are the ESTIMATION returns
    (``returns_est = where(returns_valid, returns, NaN)``). The fixture's weekly dict is
    altered so one alive symbol did not trade for 20 weeks inside each window (zero return,
    ``returns_valid`` False): the mask must drop those cells (and the following 26 weeks of
    that symbol's beta) although the zero-filled ``returns`` and ``alive`` still count them,
    the study must receive ``returns_est`` itself, and the Gegenprobe results carry the new
    DEC-85 (ii) market-column fields."""
    panel, weekly, _sb, _sm, _db, del_manifest, dd_path = _build_prelaunch_fixture_tree(tmp_path)
    weeks, returns, alive = weekly["weeks"], weekly["returns"].copy(), weekly["alive"]
    valid = weekly["returns_valid"].copy()
    j_silent = panel["symbols"].index("SYM03USDT")
    for wname in ("W1", "W2"):
        lo_hi = prelaunch.slice_window(weeks, *prelaunch.WINDOWS[wname], returns)
        gap = slice(lo_hi["lo"] + 8, lo_hi["lo"] + 28)
        assert alive[gap, j_silent].all() and valid[gap, j_silent].all()
        valid[gap, j_silent] = False
        returns[gap, j_silent] = 0.0
    weekly_mod = dict(weekly, returns=returns, returns_valid=valid)

    captured: list[tuple[tuple, dict]] = []
    orig = nulls.beta_control_method_study

    def spy(*a, **kw):
        captured.append((a, dict(kw)))
        return orig(*a, **kw)

    monkeypatch.setattr(nulls, "beta_control_method_study", spy)
    report = prelaunch.assemble_prelaunch_report(
        panel, weekly_mod, delisted_manifest_path=del_manifest, delisting_dates_path=dd_path,
        n_sims=5, n_reps_factor_null=5, n_reps_beta_control_study=5, n_reps_beta_control_winner=5, seed=53,
        gegenprobe_n_reps=10, gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9, gegenprobe_market_check=False,
        calibration_search_n_reps=5, calibration_search_rel_tol=10.0, calibration_search_max_iter=8)
    assert len(captured) == 2                                   # W1 and W2 (never L)
    returns_est = nulls.estimation_returns(weekly_mod)
    assert np.isnan(returns_est[~valid]).all() and np.array_equal(returns_est[valid], returns[valid])
    beta_prev = nulls.trailing_pit_beta_excluding_current_week(returns_est, panel["symbols"])
    beta_prev_zero_filled = nulls.trailing_pit_beta_excluding_current_week(returns, panel["symbols"])
    for (args, kw), wname in zip(captured, ("W1", "W2")):
        lo_hi = prelaunch.slice_window(weeks, *prelaunch.WINDOWS[wname], returns, alive)
        lo, hi = lo_hi["lo"], lo_hi["hi"]
        expected = alive[lo:hi] & ~np.isnan(beta_prev[lo:hi]) & ~np.isnan(returns_est[lo:hi])
        mask = kw["calibration_mask"]
        assert mask.dtype == bool and np.array_equal(mask, expected)
        assert 0 < mask.sum() < mask.size
        assert kw["gegenprobe_z_max"] == 1e9
        # DEC-85 (iii): the silent symbol's cells (and its next 26 weeks of beta) are out ...
        assert not mask[8:28, j_silent].any() and not mask[28:34, j_silent].any()
        # ... whereas the old zero-filled construction would have kept them
        old_mask = alive[lo:hi] & ~np.isnan(beta_prev_zero_filled[lo:hi]) & ~np.isnan(returns[lo:hi])
        assert old_mask[8:28, j_silent].all() and (mask <= old_mask).all() and not np.array_equal(mask, old_mask)
        # the study's window returns are the estimation returns, not the zero-filled outcome array
        assert np.array_equal(args[0], returns_est[lo:hi], equal_nan=True)
        # DEC-85 (ii): the Gegenprobe results carry the market-column bands and targets
        study = report["windows"][wname]["beta_control_method_study"]
        for cal in nulls.FACTOR_NULL_CALIBRATIONS:
            gp = study["calibrations"][cal]["gegenprobe"]
            for key in ("market_sd_band", "market_rho_band", "market_sd_ok", "market_rho_ok",
                        "target_sigma_f", "target_rho_f"):
                assert key in gp
            assert len(gp["market_sd_band"]) == 2 and len(gp["market_rho_band"]) == 2
            assert gp["target_sigma_f"] is None and gp["market_sd_ok"] is None    # check switched off here


# ============================================================================
# DEC-77 Entscheidung 1 (b) -- Vorlauf v4: beta-controlled factor null + the
# full method study grid (nulls.py)
# ============================================================================

def test_beta_controlled_factor_null_unknown_method_loud_fail():
    w, k = 20, 15
    returns = np.zeros((w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k)]
    with pytest.raises(ValueError):
        nulls.beta_controlled_factor_null(returns, alive, symbols, method="not_a_method", n_reps=2, seed=53)


def test_beta_controlled_factor_null_determinism_same_seed():
    w, k = 40, 30
    rng = np.random.default_rng(10)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    r1 = nulls.beta_controlled_factor_null(returns, alive, symbols, method="ts_resid_8w",
                                            variants=("mom1",), n_reps=15, seed=53)
    r2 = nulls.beta_controlled_factor_null(returns, alive, symbols, method="ts_resid_8w",
                                            variants=("mom1",), n_reps=15, seed=53)
    assert r1["variants"] == r2["variants"]
    assert r1["ceiling_mean_of_max"] == r2["ceiling_mean_of_max"]
    r3 = nulls.beta_controlled_factor_null(returns, alive, symbols, method="ts_resid_8w",
                                            variants=("mom1",), n_reps=15, seed=999)
    assert r3["variants"] != r1["variants"]


def test_beta_controlled_factor_null_beta_sd_mode_determinism_same_seed():
    """DEC-78 Entscheidung 1: the ``beta_sd`` mode (not ``beta_pool``) is
    just as deterministic under a fixed seed."""
    w, k = 40, 30
    rng = np.random.default_rng(10)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    r1 = nulls.beta_controlled_factor_null(returns, alive, symbols, method="fm_neutral_8w",
                                            variants=("mom1",), n_reps=15, seed=53, beta_sd=0.15)
    r2 = nulls.beta_controlled_factor_null(returns, alive, symbols, method="fm_neutral_8w",
                                            variants=("mom1",), n_reps=15, seed=53, beta_sd=0.15)
    assert r1["variants"] == r2["variants"]
    assert r1["beta_sd"] == r2["beta_sd"] == 0.15
    r3 = nulls.beta_controlled_factor_null(returns, alive, symbols, method="fm_neutral_8w",
                                            variants=("mom1",), n_reps=15, seed=53, beta_sd=0.30)
    assert r3["variants"] != r1["variants"]


def test_simulate_factor_panel_beta_sd_precedence_over_beta_pool():
    """DEC-78 Entscheidung 1: ``beta_sd`` (if not ``None``) takes priority
    over ``beta_pool`` (if non-empty), which takes priority over the
    default ``U(0.5, 2.0)`` draw -- see the function's own docstring."""
    n_weeks, n_symbols = 10, 5000
    beta_pool = np.array([100.0, 200.0])   # deliberately wildly different from beta_sd's scale
    rng = np.random.default_rng(1)
    sim_beta_sd = nulls.simulate_factor_panel(n_weeks, n_symbols, sigma_f=0.05, sigma_e=0.03,
                                               rng=rng, beta_pool=beta_pool, beta_sd=0.1)
    # beta_sd wins: beta stays near 1 +/- 0.1, nowhere near the beta_pool's 100/200 scale.
    assert abs(float(sim_beta_sd["beta"].mean()) - 1.0) < 0.05
    assert float(sim_beta_sd["beta"].std()) < 1.0

    rng2 = np.random.default_rng(1)
    sim_pool_only = nulls.simulate_factor_panel(n_weeks, n_symbols, sigma_f=0.05, sigma_e=0.03,
                                                 rng=rng2, beta_pool=beta_pool, beta_sd=None)
    # beta_pool wins over the U(0.5, 2.0) default when beta_sd is None.
    assert set(np.unique(sim_pool_only["beta"]).tolist()) <= {100.0, 200.0}


def test_beta_controlled_factor_null_none_method_reports_no_coverage():
    w, k = 30, 20
    rng = np.random.default_rng(11)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k)]
    res = nulls.beta_controlled_factor_null(returns, alive, symbols, method="none",
                                             variants=("mom1", "rev_gap"), n_reps=10, seed=53)
    assert res["coverage_mean"] is None
    assert res["beta_window_weeks"] is None
    for v in ("mom1", "rev_gap"):
        assert math.isfinite(res["variants"][v]["factor_sd"])


def test_beta_controlled_factor_null_double_sort_reports_coverage():
    w, k = 60, 40
    rng = np.random.default_rng(12)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    res = nulls.beta_controlled_factor_null(returns, alive, symbols, method="double_sort_13w",
                                             variants=("mom1",), n_reps=10, seed=53)
    assert res["coverage_mean"] is not None
    assert 0.0 <= res["coverage_mean"] <= 1.0
    assert res["beta_window_weeks"] == 13


def test_beta_control_method_study_grid_shape_and_calibration_construction():
    """DEC-78 Entscheidung 1/Nachtrag: the calibration construction
    (rho_f/beta_sd_calibrated per calibration, BISECTION-searched via
    ``nulls.calibrate_beta_sd_to_observed_share`` against
    ``factor_share_measured``, never the old measured-PIT-beta-pool draw
    or the closed-form value directly) and the grid's shape.
    ``gegenprobe_rel_tol`` is set generous here -- this test checks the
    GRID's ASSEMBLY shape, not the Gegenprobe's own statistical tolerance
    (see the dedicated ``factor_share_gegenprobe``/``calibrate_beta_sd_
    to_observed_share`` tests below, which DO exercise real convergence).

    DEC-81: ``gegenprobe_z_max=1e9`` and ``calibration_search_rel_tol=10.0``
    switch the new z-test and the (now loud) convergence requirement off
    on this 30-symbol panel, where the target share is otherwise
    unreachable; the study also records the independent Gegenprobe seed
    and the search SE it hands to the z-test."""
    w, k = 40, 30
    rng = np.random.default_rng(13)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    study = nulls.beta_control_method_study(
        returns, alive, symbols, rho_f_measured=0.3, factor_share_measured=0.02,
        variants=("mom1", "rev_gap"), methods=("none", "ts_resid_8w", "double_sort_13w"),
        n_reps=6, seed=53, gegenprobe_n_reps=10, gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9,
        calibration_search_n_reps=5, calibration_search_rel_tol=10.0, calibration_search_max_iter=6)
    assert set(study["calibrations"].keys()) == {"measured", "stress", "zero"}
    for cal in ("measured", "stress", "zero"):
        assert set(study["calibrations"][cal]["methods"].keys()) == {"none", "ts_resid_8w", "double_sort_13w"}
        for method, m in study["calibrations"][cal]["methods"].items():
            assert set(m["variants"].keys()) == {"mom1", "rev_gap"}
        assert "gegenprobe" in study["calibrations"][cal]
        assert "calibration_search" in study["calibrations"][cal]
        assert math.isfinite(study["calibrations"][cal]["beta_sd_calibrated"])
        assert math.isfinite(study["calibrations"][cal]["beta_sd_analytic_first_guess"])
        # DEC-81: independent Gegenprobe seed, the search's SE handed to the z-test, no mask given.
        gp = study["calibrations"][cal]["gegenprobe"]
        assert gp["seed"] == 53 + nulls.GEGENPROBE_SEED_OFFSET
        assert gp["search_se"] == study["calibrations"][cal]["calibration_search"]["achieved_share_se"]
        assert study["calibrations"][cal]["calibration_search"]["crn"] is True
        assert study["calibrations"][cal]["calibration_mask_k_median"] is None
    assert study["calibrations"]["stress"]["rho_f"] == pytest.approx(0.6)      # 2 * 0.3
    assert study["calibrations"]["measured"]["rho_f"] == pytest.approx(0.3)
    assert study["calibrations"]["zero"]["rho_f"] == 0.0
    assert study["calibrations"]["measured"]["target_factor_share"] == pytest.approx(0.02)
    assert study["calibrations"]["stress"]["target_factor_share"] == pytest.approx(0.04)  # 2 * 0.02
    assert study["calibrations"]["zero"]["target_factor_share"] == pytest.approx(0.02)
    # "zero" has its OWN calibration search at rho_f = 0 (real run 2026-09-25:
    # reusing "measured"'s beta_sd shifted the simulated share by +30 % and
    # failed the Gegenprobe) -- a separate, converged search object.
    assert study["calibrations"]["zero"]["calibration_search"] is not \
        study["calibrations"]["measured"]["calibration_search"]
    assert math.isfinite(study["calibrations"]["zero"]["beta_sd_calibrated"])
    # the analytic first guess is the SAME closed-form value the (now-superseded) DEC-78
    # Entscheidung 1 construction used -- still exact, still report-only.
    expected_analytic = nulls.true_beta_sd_from_factor_share(0.02, study["sigma_e_used"], study["sigma_f"])
    assert study["calibrations"]["measured"]["beta_sd_analytic_first_guess"] == pytest.approx(expected_analytic)


def test_beta_control_method_study_default_methods_is_restricted_grid():
    """DEC-78 Entscheidung 2: the study's default grid drops TS-
    residualisation (unbrauchbar bei 8-26 Wochen, DEC-77 Vorlauf v4
    finding) -- but ``ic.BETA_CONTROL_METHODS`` (the real-run dispatcher,
    ``ic.apply_beta_control``) keeps all 9, ``ts_resid_*w`` included, so a
    registered real run may still choose it."""
    assert nulls.BETA_CONTROL_METHODS_GRID == (
        "none", "fm_neutral_8w", "fm_neutral_13w", "fm_neutral_26w",
        "double_sort_13w", "double_sort_26w")
    assert not any(m.startswith("ts_resid_") for m in nulls.BETA_CONTROL_METHODS_GRID)
    assert set(nulls.BETA_CONTROL_METHODS_GRID) < set(ic.BETA_CONTROL_METHODS)
    assert any(m.startswith("ts_resid_") for m in ic.BETA_CONTROL_METHODS)
    # ts_resid's dispatch still works (the FUNCTION is kept, only dropped from the grid).
    assert ic.beta_control_trail_weeks("ts_resid_13w") == 13


# ============================================================================
# DEC-77 Entscheidung 1 (b)/(c) -- Vorlauf v4: the decision rule (prelaunch.py)
# ============================================================================

def _fake_method_entry(mean_ic: float, sd: float, ceiling: float, *, variants=("mom1", "rev_gap")) -> dict:
    return {"variants": {v: {"mean_ic_draws_mean": mean_ic, "mean_ic_draws_sd": sd} for v in variants},
            "ceiling_mean_of_max": ceiling}


def _fake_study(methods_config: dict[str, dict[str, tuple]]) -> dict:
    """``methods_config[method] = {"measured": (mean, sd, ceiling), "stress": (...)}``."""
    variants = ("mom1", "rev_gap")
    calibrations = {}
    for cal in ("measured", "stress", "zero"):
        methods_out = {}
        for method, cfg in methods_config.items():
            mean, sd, ceiling = cfg.get(cal, cfg.get("measured"))
            methods_out[method] = _fake_method_entry(mean, sd, ceiling, variants=variants)
        calibrations[cal] = {"methods": methods_out}
    return {"calibrations": calibrations, "methods": list(methods_config.keys()), "variants": list(variants)}


def test_beta_control_pass_table_pass_and_fail_boundaries():
    floor, w_judged, pure_noise_ceiling = 0.05, 52, 0.01
    null_mean_bound = 0.25 * floor / math.sqrt(w_judged)
    ceiling_bound = 1.5 * pure_noise_ceiling
    study = _fake_study({
        "good": {"measured": (null_mean_bound * 0.5, 0.02, ceiling_bound * 0.5),
                 "stress": (null_mean_bound * 0.5, 0.02, ceiling_bound * 0.5)},
        "bad_mean": {"measured": (null_mean_bound * 2.0, 0.02, ceiling_bound * 0.5),
                     "stress": (null_mean_bound * 0.5, 0.02, ceiling_bound * 0.5)},
        "bad_ceiling": {"measured": (null_mean_bound * 0.5, 0.02, ceiling_bound * 2.0),
                        "stress": (null_mean_bound * 0.5, 0.02, ceiling_bound * 0.5)},
    })
    dec = prelaunch.beta_control_pass_table(study, floor=floor, w_judged=w_judged,
                                             pure_noise_ceiling=pure_noise_ceiling,
                                             variants=("mom1", "rev_gap"))
    assert dec["passing_methods"] == ["good"]
    assert dec["note"] is None
    by_method = {r["method"]: r for r in dec["rows"]}
    assert by_method["bad_mean"]["pass"] is False
    assert by_method["bad_mean"]["measured"]["null_mean_ok"] is False
    assert by_method["bad_ceiling"]["pass"] is False
    assert by_method["bad_ceiling"]["measured"]["ceiling_ok"] is False


def test_beta_control_pass_table_no_method_passes_message():
    floor, w_judged, pure_noise_ceiling = 0.05, 52, 0.001
    study = _fake_study({"m1": {"measured": (1.0, 0.02, 1.0), "stress": (1.0, 0.02, 1.0)}})
    dec = prelaunch.beta_control_pass_table(study, floor=floor, w_judged=w_judged,
                                             pure_noise_ceiling=pure_noise_ceiling,
                                             variants=("mom1", "rev_gap"))
    assert dec["passing_methods"] == []
    assert dec["note"] == "KEINE METHODE ERFUELLT DIE KRITERIEN (GL-012-Kandidat)"


def test_beta_control_recommendation_picks_smallest_avg_sd_with_tiebreak():
    windows_out = {}
    for wn in ("W1", "W2"):
        study = _fake_study({
            "ts_resid_26w": {"measured": (0.0, 0.05, 0.0), "stress": (0.0, 0.05, 0.0)},
            "ts_resid_8w": {"measured": (0.0, 0.03, 0.0), "stress": (0.0, 0.03, 0.0)},
        })
        decision = {"passing_methods": ["ts_resid_26w", "ts_resid_8w"], "rows": [], "note": None,
                    "null_mean_bound": 0.0, "ceiling_bound": 0.0}
        windows_out[wn] = {"available": True, "beta_control_method_study": study,
                            "beta_control_decision": decision}
    rec = prelaunch.beta_control_recommendation(windows_out)
    assert rec["recommended_method"] == "ts_resid_8w"     # smaller SD wins
    assert rec["beta_window_weeks"] == 8
    assert set(rec["eligible_methods"]) == {"ts_resid_26w", "ts_resid_8w"}


def test_beta_control_recommendation_tie_prefers_shorter_window():
    windows_out = {}
    for wn in ("W1", "W2"):
        study = _fake_study({
            "ts_resid_26w": {"measured": (0.0, 0.04, 0.0), "stress": (0.0, 0.04, 0.0)},
            "fm_neutral_13w": {"measured": (0.0, 0.04, 0.0), "stress": (0.0, 0.04, 0.0)},
        })
        decision = {"passing_methods": ["ts_resid_26w", "fm_neutral_13w"], "rows": [], "note": None,
                    "null_mean_bound": 0.0, "ceiling_bound": 0.0}
        windows_out[wn] = {"available": True, "beta_control_method_study": study,
                            "beta_control_decision": decision}
    rec = prelaunch.beta_control_recommendation(windows_out)
    assert rec["recommended_method"] == "fm_neutral_13w"   # tie -> shorter beta window (13 < 26)


def test_beta_control_recommendation_none_when_no_method_passes_everywhere():
    windows_out = {
        "W1": {"available": True, "beta_control_method_study": _fake_study({}),
               "beta_control_decision": {"passing_methods": ["ts_resid_8w"], "rows": [], "note": None,
                                          "null_mean_bound": 0.0, "ceiling_bound": 0.0}},
        "W2": {"available": True, "beta_control_method_study": _fake_study({}),
               "beta_control_decision": {"passing_methods": [], "rows": [],
                                          "note": "KEINE METHODE ERFUELLT DIE KRITERIEN (GL-012-Kandidat)",
                                          "null_mean_bound": 0.0, "ceiling_bound": 0.0}},
    }
    rec = prelaunch.beta_control_recommendation(windows_out)
    assert rec["recommended_method"] is None
    assert "GL-012" in rec["note"]


# ============================================================================
# DEC-85 (i) -- the simulated market column IS the factor
# ============================================================================

def test_dec85_simulate_factor_panel_market_column_equals_factor_exactly():
    """DEC-85 (i): ``market_index=k`` -> column k == f exactly, beta[k] == 1; every other
    column, ``f`` and the rng stream are unchanged; the default ``None`` is the old behaviour
    (the market column is an ordinary ``beta*f + e`` column)."""
    kw = dict(sigma_f=0.05, sigma_e=0.03, rho_f=0.1, drift_f=0.0, beta_sd=0.4)
    sim = nulls.simulate_factor_panel(30, 12, rng=np.random.default_rng(5), market_index=7, **kw)
    base = nulls.simulate_factor_panel(30, 12, rng=np.random.default_rng(5), **kw)
    assert np.array_equal(sim["returns"][:, 7], sim["f"])
    assert sim["beta"][7] == 1.0
    assert np.array_equal(np.delete(sim["returns"], 7, axis=1), np.delete(base["returns"], 7, axis=1))
    assert np.array_equal(sim["f"], base["f"])
    assert np.array_equal(np.delete(sim["beta"], 7), np.delete(base["beta"], 7))
    assert not np.array_equal(base["returns"][:, 7], base["f"]) and base["beta"][7] != 1.0
    for bad in (-1, 12):
        with pytest.raises(ValueError, match="market_index"):
            nulls.simulate_factor_panel(30, 12, rng=np.random.default_rng(5), market_index=bad, **kw)


# ============================================================================
# DEC-85 (ii) -- the Gegenprobe checks the market column's SD and lag-1 autocorrelation
# ============================================================================

def _dec85_market_case(n_weeks: int = 53, n_symbols: int = 30):
    symbols = [f"s{i}" for i in range(n_symbols - 1)] + ["BTCUSDT"]
    return n_weeks, n_symbols, symbols


def test_dec85_measure_simulated_share_market_estimators_are_those_of_measure_market_factor():
    """DEC-85 (ii): per replicate the SD (ddof=1) and the lag-1 autocorrelation collected
    from the simulated market column are exactly ``measure_market_factor``'s estimators, the
    bands are the 2.5/97.5 % quantiles of those draws, and there is no market column ->
    no bands."""
    n_weeks, n_symbols, symbols = _dec85_market_case()
    kw = dict(sigma_f=0.05, sigma_e=0.12, rho_f=0.2, beta_sd=0.3)
    got = nulls._measure_simulated_share(n_weeks, n_symbols, symbols, n_reps=40, seed=11, **kw)
    rng = np.random.default_rng(11)
    sds, rhos = [], []
    for _ in range(40):
        sim = nulls.simulate_factor_panel(n_weeks, n_symbols, sigma_f=0.05, sigma_e=0.12, rho_f=0.2,
                                          drift_f=nulls.DRIFT_F_DRIFTFREE, rng=rng, beta_sd=0.3,
                                          market_index=n_symbols - 1)
        m = nulls.measure_market_factor(sim["returns"], symbols)
        sds.append(m["sigma_f"])
        rhos.append(m["rho_f_measured"])
    assert got["market_sd_draws"] == pytest.approx(sds) and got["market_rho_draws"] == pytest.approx(rhos)
    assert got["market_sd_band"] == pytest.approx(np.quantile(sds, [0.025, 0.975]).tolist())
    assert got["market_rho_band"] == pytest.approx(np.quantile(rhos, [0.025, 0.975]).tolist())
    # the simulated market column carries NO idiosyncratic noise: its SD sits near sigma_f
    # (not near sqrt(sigma_f^2 + sigma_e^2) = 0.13)
    assert 0.04 < np.mean(sds) < 0.06

    no_market = nulls._measure_simulated_share(
        n_weeks, n_symbols, [f"s{i}" for i in range(n_symbols)], n_reps=3, seed=11, **kw)
    assert no_market["market_sd_band"] is None and no_market["market_rho_band"] is None
    assert no_market["market_sd_draws"] is None and no_market["market_rho_draws"] is None


def _dec85_gegenprobe_kwargs(n_weeks, n_symbols, symbols, n_reps=80, **overrides):
    kw = dict(sigma_f=0.067, sigma_e=0.12, rho_f=0.05, beta_sd=0.3, n_reps=n_reps, seed=7,
              rel_tol=10.0, market_symbol="BTCUSDT")
    kw.update(overrides)
    own = nulls._measure_simulated_share(
        n_weeks, n_symbols, symbols, sigma_f=kw["sigma_f"], sigma_e=kw["sigma_e"], rho_f=kw["rho_f"],
        beta_sd=kw["beta_sd"], n_reps=n_reps, seed=kw["seed"])
    return kw, own["simulated_share"]


def test_dec85_gegenprobe_market_column_consistent_passes_and_reports_bands():
    """DEC-85 (ii): with the market column := factor, the measured sigma_f / rho_f lie inside
    the replicate bands (despite sigma_e = 0.12 >> sigma_f = 0.067); the result carries the
    bands, the per-target verdicts and the targets."""
    n_weeks, n_symbols, symbols = _dec85_market_case()
    kw, share = _dec85_gegenprobe_kwargs(n_weeks, n_symbols, symbols)
    res = nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, target_share=share,
                                        target_sigma_f=0.067, target_rho_f=0.05, **kw)
    assert res["ok"] is True and res["market_sd_ok"] is True and res["market_rho_ok"] is True
    assert res["target_sigma_f"] == 0.067 and res["target_rho_f"] == 0.05
    sd_lo, sd_hi = res["market_sd_band"]
    rho_lo, rho_hi = res["market_rho_band"]
    assert sd_lo <= 0.067 <= sd_hi and rho_lo <= 0.05 <= rho_hi
    # no targets given -> not checked (None), bands still reported
    res0 = nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, target_share=share, **kw)
    assert res0["market_sd_ok"] is None and res0["market_rho_ok"] is None
    assert res0["target_sigma_f"] is None and res0["market_sd_band"] == res["market_sd_band"]


def test_dec85_gegenprobe_v5c_defect_market_column_with_idiosyncratic_vol_fails_loud(monkeypatch):
    """DEC-85 regression test of the v5c defect: with the OLD construction (market column
    = an ordinary ``beta*f + e`` column, ``market_index=None``) and sigma_e >> sigma_f its SD
    is ~sqrt(sigma_f^2 + sigma_e^2) = 0.137, the measured sigma_f = 0.067 falls out of the
    95 % band -> loud 'Marktspalte inkonsistent' naming target and band. The rho target is
    checked independently (a target of 0.9 is outside its band as well)."""
    n_weeks, n_symbols, symbols = _dec85_market_case()
    kw, share = _dec85_gegenprobe_kwargs(n_weeks, n_symbols, symbols)
    orig = nulls.simulate_factor_panel
    monkeypatch.setattr(nulls, "simulate_factor_panel",
                        lambda *a, **k: orig(*a, **{**k, "market_index": None}))
    with pytest.raises(nulls.FactorShareCalibrationError) as exc:
        nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, target_share=share,
                                      target_sigma_f=0.067, target_rho_f=0.05, **kw)
    msg = str(exc.value)
    assert msg.startswith("Gegenprobe fehlgeschlagen") and "Marktspalte inkonsistent" in msg
    assert "sigma_f-Ziel 0.067" in msg and "Band" in msg
    assert "rho_f-Ziel" not in msg                       # the rho target (0.05) is inside its band
    monkeypatch.setattr(nulls, "simulate_factor_panel", orig)
    # with the DEC-85 construction the very same call passes ...
    assert nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, target_share=share,
                                         target_sigma_f=0.067, target_rho_f=0.05, **kw)["ok"] is True
    # ... and an inconsistent rho target alone fails loud, naming the rho target
    with pytest.raises(nulls.FactorShareCalibrationError, match="Marktspalte inkonsistent") as exc2:
        nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, target_share=share,
                                      target_sigma_f=0.067, target_rho_f=0.9, **kw)
    assert "rho_f-Ziel 0.9" in str(exc2.value) and "sigma_f-Ziel" not in str(exc2.value)


def test_dec85_gegenprobe_market_target_without_market_symbol_and_nan_target_are_loud():
    """DEC-85 (ii): a market target without a market symbol has nothing to check (loud), a NaN
    target is never ok (C.14)."""
    n_weeks, n_symbols, symbols = _dec85_market_case()
    kw, share = _dec85_gegenprobe_kwargs(n_weeks, n_symbols, symbols, n_reps=20)
    with pytest.raises(nulls.FactorShareCalibrationError, match="Gegenprobe fehlgeschlagen"):
        nulls.factor_share_gegenprobe(n_weeks, n_symbols, [f"s{i}" for i in range(n_symbols)],
                                      target_share=share, target_sigma_f=0.067, **kw)
    with pytest.raises(nulls.FactorShareCalibrationError, match="Marktspalte inkonsistent"):
        nulls.factor_share_gegenprobe(n_weeks, n_symbols, symbols, target_share=share,
                                      target_sigma_f=float("nan"), **kw)


def test_dec85_study_hands_each_calibration_its_market_targets(monkeypatch):
    """DEC-85 (ii): ``beta_control_method_study`` calls the Gegenprobe per calibration with
    target_sigma_f = the measured sigma_f (all three) and target_rho_f = measured / 2x / 0;
    the result fields are set; ``gegenprobe_market_check=False`` drops the targets only."""
    w, k = 53, 30
    rng = np.random.default_rng(13)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    seen: list[dict] = []
    orig_gp = nulls.factor_share_gegenprobe

    def spy_gp(*a, **kw):
        seen.append(dict(kw, rho_f_arg=kw["rho_f"]))
        return orig_gp(*a, **kw)

    monkeypatch.setattr(nulls, "factor_share_gegenprobe", spy_gp)
    common = dict(rho_f_measured=0.1, factor_share_measured=0.02, variants=("mom1",), methods=("none",),
                  n_reps=2, seed=53, gegenprobe_n_reps=20, gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9,
                  calibration_search_n_reps=5, calibration_search_rel_tol=10.0, calibration_search_max_iter=4)
    study = nulls.beta_control_method_study(returns, alive, symbols, **common)
    assert len(seen) == 3
    sigma_f = study["sigma_f"]
    assert sigma_f == pytest.approx(float(np.std(returns[:, -1], ddof=1)))
    expected_rho = {"measured": 0.1, "stress": 0.2, "zero": 0.0}
    for kw, cal in zip(seen, nulls.FACTOR_NULL_CALIBRATIONS):
        assert kw["target_sigma_f"] == sigma_f
        assert kw["target_rho_f"] == pytest.approx(expected_rho[cal]) and kw["rho_f_arg"] == kw["target_rho_f"]
        gp = study["calibrations"][cal]["gegenprobe"]
        assert gp["target_sigma_f"] == sigma_f and gp["target_rho_f"] == pytest.approx(expected_rho[cal])
        assert gp["market_sd_ok"] is True and gp["market_rho_ok"] is True
        lo, hi = gp["market_sd_band"]
        assert lo <= sigma_f <= hi

    seen.clear()
    nulls.beta_control_method_study(returns, alive, symbols, gegenprobe_market_check=False, **common)
    assert [(kw["target_sigma_f"], kw["target_rho_f"]) for kw in seen] == [(None, None)] * 3


def test_dec85_study_aborts_loud_when_the_market_column_misses_the_measured_sigma_f():
    """DEC-85 (ii): the simulated factor has innovation SD sigma_f, so a strongly persistent
    calibration (stress rho_f = 1.5 * 0.4 = 0.6, marginal SD 1.25 * sigma_f) cannot reproduce the
    measured sigma_f of a 300-week white-noise BTC column inside its 95 % band -> the study
    aborts with the loud market-column message (instead of silently calibrating on it)."""
    w, k = 300, 30
    rng = np.random.default_rng(13)
    returns = rng.normal(0, 0.03, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    kw = dict(rho_f_measured=0.4, factor_share_measured=0.02, stress_multiplier=1.5, variants=("mom1",),
              methods=("none",), n_reps=2, seed=53, gegenprobe_n_reps=60, gegenprobe_rel_tol=10.0,
              gegenprobe_z_max=1e9, calibration_search_n_reps=5, calibration_search_rel_tol=10.0,
              calibration_search_max_iter=4)
    with pytest.raises(nulls.FactorShareCalibrationError, match="Marktspalte inkonsistent") as exc:
        nulls.beta_control_method_study(returns, alive, symbols, **kw)
    assert "sigma_f-Ziel" in str(exc.value)
    # the same study passes with the check switched off (the test knob), bands still reported
    study = nulls.beta_control_method_study(returns, alive, symbols, gegenprobe_market_check=False, **kw)
    assert study["calibrations"]["stress"]["gegenprobe"]["market_sd_ok"] is None


# ============================================================================
# DEC-85 (iii) -- not-trading symbol-weeks are NaN for beta and vol estimation
# ============================================================================

def test_dec85_estimation_returns_helper_and_loud_failures():
    """DEC-85 (iii): ``returns_est = where(returns_valid, returns, NaN)``; a weekly dict
    without ``returns_valid`` (or with a wrong shape) is a loud ValueError, never a silent
    fall back to the zero-filled array."""
    returns = np.array([[0.0, 0.0], [0.1, 0.0], [0.2, -0.3]])
    valid = np.array([[False, False], [True, False], [True, True]])
    est = nulls.estimation_returns({"returns": returns, "returns_valid": valid})
    assert np.array_equal(est, np.array([[np.nan, np.nan], [0.1, np.nan], [0.2, -0.3]]), equal_nan=True)
    assert np.array_equal(returns, np.array([[0.0, 0.0], [0.1, 0.0], [0.2, -0.3]]))     # input untouched
    with pytest.raises(ValueError, match="returns_valid"):
        nulls.estimation_returns({"returns": returns})
    with pytest.raises(ValueError, match="shape"):
        nulls.estimation_returns({"returns": returns, "returns_valid": valid[:2]})


def test_dec85_sigma_f_sigma_e_skip_never_trading_symbols_and_match_the_hand_median():
    """DEC-85 (iii): on ``returns_est`` never-trading columns (all NaN), a 1-week and a 2-week
    symbol do not move the medians; the result equals the by-hand median over the valid
    columns, and equals the result on the matrix with those columns DELETED. The zero-filled
    matrix (the pre-DEC-85 input) gives a smaller median (never-trading symbols enter at SD 0)."""
    rng = np.random.default_rng(3)
    w = 40
    symbols = ["BTCUSDT", "A", "B", "C", "D", "N1", "N2", "N3", "ONE", "TWO"]
    f = rng.normal(0, 0.06, size=w)
    valid_cols = {"A": 1.2, "B": 0.6, "C": 1.8, "D": 0.9}
    est = np.full((w, len(symbols)), np.nan)
    est[:, 0] = f
    for name, beta in valid_cols.items():
        est[:, symbols.index(name)] = beta * f + rng.normal(0, 0.03 + 0.01 * beta, size=w)
    est[5, symbols.index("ONE")] = 0.04                       # a single valid week
    est[[5, 6], symbols.index("TWO")] = [0.04, -0.02]          # two valid weeks (< 3 pairs)
    zero_filled = np.where(np.isnan(est), 0.0, est)

    res = nulls.window_sigma_f_sigma_e(est, symbols)
    assert res["sigma_f"] == pytest.approx(float(np.std(f, ddof=1)))
    # by hand: total vol = median SD over the symbols with >= 2 valid weeks (BTC, A..D, TWO)
    total_sds = [np.std(f, ddof=1)] + [np.std(est[:, symbols.index(n)], ddof=1) for n in valid_cols]
    total_sds.append(np.std([0.04, -0.02], ddof=1))
    assert res["sigma_e_total"] == pytest.approx(float(np.median(total_sds)))
    # by hand: idiosyncratic vol = median residual SD of the OLS on BTC, symbols with >= 3 pairs
    resid_sds = []
    for name in valid_cols:
        y = est[:, symbols.index(name)]
        x_c, y_c = f - f.mean(), y - y.mean()
        resid = y_c - (x_c @ y_c) / (x_c @ x_c) * x_c
        resid_sds.append(resid.std(ddof=1))
    assert res["sigma_e_idiosyncratic"] == pytest.approx(float(np.median(resid_sds)))
    assert res["sigma_e_used"] == res["sigma_e_idiosyncratic"]

    keep = [j for j, s in enumerate(symbols) if s in ("BTCUSDT", "A", "B", "C", "D")]
    ref = nulls.window_sigma_f_sigma_e(est[:, keep], [symbols[j] for j in keep])
    assert res["sigma_e_idiosyncratic"] == pytest.approx(ref["sigma_e_idiosyncratic"])
    assert res["sigma_f"] == pytest.approx(ref["sigma_f"])

    zero = nulls.window_sigma_f_sigma_e(zero_filled, symbols)
    assert zero["sigma_e_idiosyncratic"] < res["sigma_e_idiosyncratic"]
    assert zero["sigma_e_total"] < res["sigma_e_total"]


def test_dec85_pit_beta_with_returns_est_needs_the_full_window_of_valid_returns():
    """DEC-85 (iii): a symbol with only 10 valid weeks gets NaN at trail_win=26 (it had a
    damped, finite beta on the zero-filled returns); a symbol valid from week 20 on gets its
    first finite beta exactly 26 weeks later; a symbol valid throughout is unchanged."""
    rng = np.random.default_rng(8)
    w = 60
    symbols = ["BTCUSDT", "FULL", "YOUNG", "MID"]
    f = rng.normal(0, 0.05, size=w)
    est = np.full((w, 4), np.nan)
    est[:, 0] = f
    est[:, 1] = 1.3 * f + rng.normal(0, 0.03, size=w)
    est[50:, 2] = 0.8 * f[50:] + rng.normal(0, 0.03, size=10)       # 10 valid weeks
    est[20:, 3] = 1.1 * f[20:] + rng.normal(0, 0.03, size=w - 20)   # valid from week 20
    zero_filled = np.where(np.isnan(est), 0.0, est)

    beta_est = nulls.trailing_pit_beta_excluding_current_week(est, symbols, trail_win=26)
    beta_zero = nulls.trailing_pit_beta_excluding_current_week(zero_filled, symbols, trail_win=26)
    assert np.isfinite(beta_zero[-1, 2]) and np.isnan(beta_est[:, 2]).all()      # 10 weeks old
    assert int(np.flatnonzero(np.isfinite(beta_est[:, 3])).min()) == 20 + 26
    assert np.isfinite(beta_zero[30, 3])                                          # damped, pre-DEC-85
    assert np.isnan(beta_est[:26, 1]).all() and np.isfinite(beta_est[26:, 1]).all()
    assert np.allclose(beta_est[26:, 1], beta_zero[26:, 1])                       # full history: identical


def test_dec85_beta_characteristic_gives_nan_to_symbols_with_nan_in_the_window():
    """DEC-85 (iii): ``characteristics.beta_characteristic`` needs no change -- a symbol with a
    NaN anywhere in the trailing window gets NaN, a fully valid one a finite beta."""
    rng = np.random.default_rng(2)
    w = 30
    f = rng.normal(0, 0.05, size=w)
    est = np.column_stack([f, 1.5 * f + rng.normal(0, 0.02, size=w), 0.5 * f + rng.normal(0, 0.02, size=w)])
    est[:12, 2] = np.nan                                    # third symbol starts trading in week 12
    out = characteristics.beta_characteristic(est, ["BTCUSDT", "X", "Y"], trail_win=8, min_weeks=8)
    assert np.isfinite(out[7:, 1]).all()
    assert np.isnan(out[:19, 2]).all() and np.isfinite(out[19:, 2]).all()           # 12 + 8 - 1 = 19


def test_dec85_factor_calibration_report_uses_the_estimation_returns_cross_section():
    """DEC-85 (iii): ``factor_share_from_trailing_beta`` skips symbol-weeks whose
    ``returns_est`` is NaN (they are not in the cross-section), so the per-week K shrinks by
    exactly the not-trading symbols."""
    rng = np.random.default_rng(4)
    w, k = 50, 20
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    est = rng.normal(0, 0.04, size=(w, k))
    est[:, :5] = np.nan                                     # five symbols never trade
    alive = np.ones((w, k), dtype=bool)
    beta_prev = nulls.trailing_pit_beta_excluding_current_week(est, symbols, trail_win=10)
    share = nulls.factor_share_from_trailing_beta(est, alive, beta_prev)
    ks = {row["k"] for row in share["per_week"] if row["r2"] is not None}
    assert ks == {k - 5}
    calib = nulls.factor_calibration_report(est, alive, symbols, beta_prev)
    assert math.isfinite(calib["market_factor"]["sigma_f"]) and math.isfinite(calib["sigma_e_used"])


# ============================================================================
# DEC-87 (Drittfassung H-28..H-30, Vorlauf v5e) -- prelaunch / ic / nulls / characteristics
# ============================================================================

def _weekly_daily_panel(k: int = 40, n_weeks: int = 60, seed: int = 11, daily_sd=None, mu_d: float = 0.0,
                        start: date = date(2022, 1, 3)):
    """A daily-close panel starting on a MONDAY with exactly ``7 * n_weeks`` days (every ISO week has 7 valid
    daily returns except the first week, which has 6), plus its weekly log returns. ``daily_sd`` (per symbol)
    and ``mu_d`` (the daily LOG-return mean shift added to ``-sd^2/2``) shape the data."""
    import datetime as _dt
    n_days = 7 * n_weeks
    dates = [(start + _dt.timedelta(days=i)).isoformat() for i in range(n_days)]
    rng = np.random.default_rng(seed)
    sd = np.full(k, 0.02) if daily_sd is None else np.asarray(daily_sd, dtype=np.float64)
    d = rng.normal(loc=mu_d - 0.5 * sd ** 2, scale=sd, size=(n_days, k))
    close = 100.0 * np.exp(np.cumsum(d, axis=0))
    weeks = sorted({pit_universe.iso_week_start(date.fromisoformat(x)).isoformat() for x in dates})
    wk_close = close[6::7]
    returns = np.zeros((len(weeks), k))
    returns[1:] = np.log(wk_close[1:] / wk_close[:-1])
    return {"dates": dates, "close": close}, weeks, returns


# ---- DEC-87 (G): H-30 drag, weekly units, sign ------------------------------

def test_dec87_vol_weighted_outcome_weekly_sigma_and_added_drag():
    """DEC-87 (G): with ``day_count`` the vol is the DAILY SD and ``sigma_w = sqrt(n_t) * vol_rv``; the adjusted
    outcome is ``r_log[t+1] + sigma_w[t]^2/2`` (removes the log drag), weighted by ``target_vol / sigma_w`` with
    ``target_vol`` the median ``sigma_w`` -- all in weekly units. The pre-DEC-87 formula ``(r - vol_daily^2/2) *
    target_daily/vol_daily`` is NOT what comes out."""
    returns = np.array([[0.0, 0.0, 0.0], [0.10, 0.20, -0.05], [-0.05, 0.03, 0.02], [0.02, -0.01, 0.04]])
    vol_daily = np.array([[0.02, 0.05, 0.03], [0.04, 0.03, 0.02], [0.02, 0.08, 0.01], [0.01, 0.01, 0.02]])
    day_count = np.array([[7, 7, 6], [7, 7, 7], [7, 5, 7], [7, 7, 7]])
    out = ic.vol_weighted_outcome_with_drag(returns, vol_daily, day_count=day_count)
    sigma_w = np.sqrt(day_count) * vol_daily
    assert np.allclose(out["sigma_w"], sigma_w)
    assert np.allclose(characteristics.weekly_vol_from_daily(vol_daily, day_count), sigma_w)
    target = float(np.median(sigma_w))
    assert out["target_vol"] == pytest.approx(target)
    for t in range(3):
        expected = (returns[t + 1] + 0.5 * sigma_w[t] ** 2) * (target / sigma_w[t])
        assert np.allclose(out["weighted_outcome"][t], expected)
        assert np.allclose(out["drag"][t], 0.5 * sigma_w[t] ** 2)
    assert np.isnan(out["weighted_outcome"][-1]).all()
    old = (returns[1] - 0.5 * vol_daily[0] ** 2) * (np.median(vol_daily) / vol_daily[0])
    assert not np.allclose(out["weighted_outcome"][0], old)
    # a NaN vol or a zero day count -> NaN sigma_w -> NaN outcome (never a number from nothing)
    vd = vol_daily.copy()
    vd[0, 0] = np.nan
    dc = day_count.copy()
    dc[0, 1] = 0
    out2 = ic.vol_weighted_outcome_with_drag(returns, vd, day_count=dc)
    assert np.isnan(out2["weighted_outcome"][0, 0]) and np.isnan(out2["weighted_outcome"][0, 1])
    with pytest.raises(ValueError, match="day_count shape"):
        characteristics.weekly_vol_from_daily(vol_daily, day_count[:2])


def test_dec87_h30_feasibility_weekly_units_is_n_times_the_daily_drag():
    """DEC-87 (G): ``h30_feasibility`` works in WEEKLY units -- the drag is ``0.5 * (sqrt(n) * vol_rv)^2`` and so
    ``n`` (= 7) times the daily drag it used until v5d (Spread/Kante 0.395 daily vs ~2.8 weekly on L); a window
    without ``day_count`` is a loud fail (no daily fallback)."""
    k = 40
    panel, weeks, returns = _weekly_daily_panel(k=k, n_weeks=60, daily_sd=np.linspace(0.01, 0.06, k))
    alive = np.ones((len(weeks), k), dtype=bool)
    vol_rv = characteristics.realized_vol_characteristic(panel, weeks)
    day_count = characteristics.weekly_valid_day_count(panel, weeks)
    window_l = {"returns": returns, "alive": alive, "weeks": weeks, "vol_rv": vol_rv, "day_count": day_count}
    h = prelaunch.h30_feasibility(window_l)

    # the old (daily-unit) decile spread on the same data, computed by hand
    by_decile: dict[int, list[float]] = {d: [] for d in range(1, 11)}
    for t in range(len(weeks)):
        buckets = characteristics.decile_bucket(vol_rv[t], alive[t])
        drag = 0.5 * vol_rv[t] ** 2 * 1e4
        for d in range(1, 11):
            by_decile[d].extend(float(x) for x in drag[(buckets == d) & ~np.isnan(drag)])
    daily_spread = float(np.median(by_decile[10]) - np.median(by_decile[1]))
    assert (day_count[1:] == 7).all()                                 # fixture: every week but the first has 7 days
    # all weeks (but the 6-day first one) have n = 7 -> the weekly spread is 7x the daily one (within the
    # tiny effect of the single 6-day week on a decile median)
    assert h["spread_d10_minus_d1_bps"] == pytest.approx(7.0 * daily_spread, rel=0.02)
    assert h["units"].startswith("weekly") and h["n_days_median"] == 7.0
    assert h["spread_d10_minus_d1_over_kante"] == pytest.approx(h["spread_d10_minus_d1_bps"] / h["kante_bps_per_week"])
    assert h["target_vol"] == pytest.approx(float(np.nanmedian(np.sqrt(day_count) * vol_rv)))

    no_dc = {k_: v for k_, v in window_l.items() if k_ != "day_count"}
    with pytest.raises(ValueError, match="day_count"):
        prelaunch.h30_feasibility(no_dc)


def test_dec87_h30_feasibility_sigma_xs_uses_returns_est_and_is_nan_safe():
    """DEC-87 (item 10): ``Kante`` uses the ESTIMATION returns -- a not-trading cell (NaN in ``returns_est``) is a
    missing observation, neither a zero return nor a poisoned week (``stats.sigma_xs_series`` skips NaN)."""
    k = 30
    panel, weeks, returns = _weekly_daily_panel(k=k, n_weeks=40, seed=5)
    alive = np.ones((len(weeks), k), dtype=bool)
    est = returns.copy()
    est[10:20, :4] = np.nan                                  # four symbols silent for ten weeks
    returns_zero = np.where(np.isnan(est), 0.0, est)         # the zero-filled outcome array
    vol_rv = characteristics.realized_vol_characteristic(panel, weeks)
    dc = characteristics.weekly_valid_day_count(panel, weeks)
    base = {"alive": alive, "weeks": weeks, "vol_rv": vol_rv, "day_count": dc}
    h_est = prelaunch.h30_feasibility({**base, "returns": returns_zero, "returns_est": est})
    h_zero = prelaunch.h30_feasibility({**base, "returns": returns_zero})
    expected = np.array([np.std(est[t][~np.isnan(est[t])], ddof=1) for t in range(len(weeks))])
    assert h_est["sigma_xs_l"]["median"] == pytest.approx(float(np.median(expected)))
    assert h_est["sigma_xs_l"]["n_weeks"] == len(weeks)                       # no week lost to a NaN
    assert h_est["sigma_xs_l"]["median"] != h_zero["sigma_xs_l"]["median"]    # zero fill changes the estimate


def test_dec87_sigma_xs_series_skips_nan_cells_and_is_unchanged_without_nan():
    """DEC-87 (item 10): ``stats.sigma_xs_series`` ignores NaN cells (a symbol that did not trade is a missing
    observation); NaN-free input gives the exact pre-DEC-87 numbers, a week with fewer than ``min_universe`` usable
    cells stays NaN."""
    from bybit_edge.research.wp7_universe import stats
    rng = np.random.default_rng(8)
    r = rng.normal(0, 0.05, size=(6, 12))
    alive = np.ones((6, 12), dtype=bool)
    clean = stats.sigma_xs_series(r, alive)
    assert np.array_equal(clean, np.array([np.std(r[t], ddof=1) for t in range(6)]))
    r2 = r.copy()
    r2[1, :3] = np.nan
    r2[2, :11] = np.nan                                  # one usable cell left
    out = stats.sigma_xs_series(r2, alive)
    assert out[1] == pytest.approx(np.std(r[1, 3:], ddof=1)) and np.isnan(out[2])
    assert np.array_equal(out[[0, 3, 4, 5]], clean[[0, 3, 4, 5]])


# ---- DEC-87 (item 10): persistence null / survivorship fixture on returns_est ---

def test_dec87_ar1_fit_skips_nan_cells_and_is_unchanged_without_nan():
    """DEC-87 (item 10): ``fit_ar1_per_symbol`` on ``returns_est`` treats NaN as missing (the symbol's pairs and
    moments use valid weeks only) and is bit-identical to before on NaN-free input."""
    rng = np.random.default_rng(3)
    w, k = 60, 6
    returns = rng.normal(0, 0.05, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    clean = nulls.fit_ar1_per_symbol(returns, alive)
    est = returns.copy()
    est[20:40, 2] = np.nan                                   # symbol 2 silent for 20 weeks
    fitted = nulls.fit_ar1_per_symbol(est, alive)
    assert fitted["n_obs"][2] == w - 20 and fitted["n_obs"][0] == w
    assert np.isfinite(fitted["phi"]).all() and np.isfinite(fitted["sigma"]).all()
    assert fitted["phi"][0] == clean["phi"][0] and fitted["sigma"][0] == clean["sigma"][0]     # untouched columns
    # the zero-filled column would have fitted a different (distorted) sigma
    zero = returns.copy()
    zero[20:40, 2] = 0.0
    assert nulls.fit_ar1_per_symbol(zero, alive)["sigma"][2] != fitted["sigma"][2]
    # a whole persistence null runs on NaN-carrying input without a NaN anywhere in the fit
    res = nulls.persistence_null(est, alive, [f"w{i}" for i in range(w)], variants=("mom1",), n_sims=5, seed=53)
    assert np.isfinite(res["ar1"]["phi"]).all() and np.isfinite(res["ar1"]["sigma"]).all()


def test_dec87_window_noise_floor_uses_returns_est_for_the_ar1_fits(monkeypatch):
    """DEC-87 (item 10): ``window_noise_floor_and_threshold`` hands the persistence null the window's
    ``returns_est`` when it has one (the zero-filled ``returns`` only as a fallback for hand-built windows)."""
    rng = np.random.default_rng(9)
    w, k = 30, 40
    returns = rng.normal(0, 0.03, size=(w, k))
    est = returns.copy()
    est[:10, :5] = np.nan
    alive = np.ones((w, k), dtype=bool)
    weeks = [str(i) for i in range(w)]
    seen = []
    orig = nulls.persistence_null

    def spy(r, *a, **kw):
        seen.append(r)
        return orig(r, *a, **kw)

    monkeypatch.setattr(nulls, "persistence_null", spy)
    prelaunch.window_noise_floor_and_threshold({"returns": returns, "returns_est": est, "alive": alive, "weeks": weeks},
                                               variants=("mom1",), n_sims=3, seed=53)
    prelaunch.window_noise_floor_and_threshold({"returns": returns, "alive": alive, "weeks": weeks},
                                               variants=("mom1",), n_sims=3, seed=53)
    assert seen[0] is est and seen[1] is returns


def test_dec87_survivorship_fixture_is_sized_from_the_estimation_cross_section():
    """DEC-87 (item 10): K of the signal-free fixture is the window's median count of symbols that are alive AND
    carry a computed return (``returns_est``), not the bare alive count."""
    n_weeks, k = 60, 100
    alive = np.ones((n_weeks, k), dtype=bool)
    est = np.zeros((n_weeks, k))
    est[:, 40:] = np.nan                                     # only 40 symbols have a computed return
    window = {"returns": np.zeros((n_weeks, k)), "returns_est": est, "alive": alive,
              "weeks": [str(i) for i in range(n_weeks)]}
    r = prelaunch.survivorship_drawdown_fixture(window, ic_min_mom1=0.02, ic_min_rev_gap=0.02, seed=53)
    assert r["k"] == 40
    without = {k_: v for k_, v in window.items() if k_ != "returns_est"}
    r_old = prelaunch.survivorship_drawdown_fixture(without, ic_min_mom1=0.02, ic_min_rev_gap=0.02, seed=53)
    assert r_old["k"] == 100


# ---- DEC-87 (V5): Gate (5) reachability for all three H-30 variants -------------

def test_dec87_gate5_reachability_by_variant_and_shared_core():
    """DEC-87 (V5): the outcome-free reachability is reported for ``vol_rv``, ``vol_max`` and ``vol_beta``; the
    number is the one ``characteristics.characteristic_turnover_spearman`` gives (the same core ``run_full`` feeds
    ``gates.evaluate`` as Gate (5)). A characteristic identical to the turnover rank has Spearman 1 -> not
    reachable (>= 0.60), an independent one is."""
    rng = np.random.default_rng(6)
    w, k = 30, 80
    alive = np.ones((w, k), dtype=bool)
    weeks = [str(i) for i in range(w)]
    turnover_trail = rng.lognormal(size=(w, k))
    window = {"alive": alive, "weeks": weeks, "turnover_trail": turnover_trail,
              "vol_rv": turnover_trail * 2.0,                          # perfectly rank-correlated
              "vol_max": rng.normal(size=(w, k)),                      # independent
              "vol_beta": np.where(np.arange(k) < 10, np.nan, rng.normal(size=(w, k)))}
    by = prelaunch.gate5_reachability_by_variant(window)
    assert set(by) == {"vol_rv", "vol_max", "vol_beta"}
    assert by["vol_rv"]["median"] == pytest.approx(1.0) and by["vol_rv"]["gate5_reachable"] is False
    assert abs(by["vol_max"]["median"]) < 0.2 and by["vol_max"]["gate5_reachable"] is True
    assert by["vol_beta"]["available"] is True and by["vol_beta"]["gate5_reachable"] is True
    core = characteristics.characteristic_turnover_spearman(window["vol_max"], turnover_trail, alive, weeks)
    assert by["vol_max"]["median"] == core["median"] and by["vol_max"]["n_weeks_used"] == w
    legacy = prelaunch.gate5_reachability(window)                      # pre-DEC-87 call shape: vol_rv
    assert legacy["median"] == by["vol_rv"]["median"] and legacy["threshold"] == 0.60
    missing = prelaunch.gate5_reachability_by_variant({k_: v for k_, v in window.items() if k_ != "vol_max"})
    assert missing["vol_max"] == {"available": False, "note": "vol_max nicht im Fenster geladen"}
    # weeks with fewer than 10 usable symbols are skipped, never silently scored
    few = np.zeros((w, k), dtype=bool)
    few[:, :5] = True
    thin = characteristics.characteristic_turnover_spearman(window["vol_max"], turnover_trail, few, weeks)
    assert thin["median"] is None and thin["n_weeks_used"] == 0


# ---- DEC-87 (A)/(C)/(E): constants, ceilings, binding quantile ------------------

def test_dec87_analytic_selection_ceiling_reports_both_lines():
    """DEC-87 (C): the per-window analytic ceiling is ``z_max * SE_W`` (the 1/sqrt(2) factor, sigma_SR of a
    pooled two-year estimator, is discarded); the v5d line with the factor stays available as ``ceiling_ic``."""
    r = prelaunch.analytic_selection_ceiling(0.04858, 52)
    se = 0.04858 / math.sqrt(52)
    assert r["ceiling_ic_without_factor"] == pytest.approx(prelaunch.analytic_bailey_ldp_ceiling(7) * se)
    assert r["ceiling_ic"] == pytest.approx(r["ceiling_ic_without_factor"] / math.sqrt(2.0))
    assert r["ceiling_ic_without_factor"] == pytest.approx(1.3868 * se, rel=1e-3)


def test_dec87_run_configuration_null_two_drifts_constants_and_binding():
    """DEC-87 (A)/(E): ``nulls.run_configuration_null`` = the registered method under the stress calibration,
    driftfree AND drift 0.002; ``frozen_null_constants`` derives the ceiling (driftfree), both quantile sets and the
    binding (more extreme in the hypothesis direction) from the two cells -- Vorlauf and Lauf use this one code."""
    rng = np.random.default_rng(21)
    w, k = 40, 45
    symbols = [f"s{i}" for i in range(k - 1)] + ["BTCUSDT"]
    est = rng.normal(0, 0.05, size=(w, k))
    alive = np.ones((w, k), dtype=bool)
    cfg = nulls.run_configuration_null(est, alive, symbols, method="fm_neutral_8w", rho_f=0.09, beta_sd=0.6,
                                       n_reps=12, seed=53)
    assert cfg["driftfree"]["drift_f"] == 0.0 and cfg["drifting"]["drift_f"] == pytest.approx(0.002)
    assert cfg["driftfree"]["rho_f"] == cfg["drifting"]["rho_f"] == 0.09 and cfg["driftfree"]["beta_sd"] == 0.6
    c = cfg["constants"]
    assert c["ceiling_method_stress"] == cfg["driftfree"]["ceiling_mean_of_max"]
    assert c["ceiling_method_stress_drifting_report_only"] == cfg["drifting"]["ceiling_mean_of_max"]
    for v in characteristics.VARIANT_NAMES:
        qf = cfg["driftfree"]["variants"][v]["quantile_one_sided"]
        qd = cfg["drifting"]["variants"][v]["quantile_one_sided"]
        assert c["res_quantile_driftfree"][v] == qf and c["res_quantile_drifting"][v] == qd
        direction = nulls.REGISTERED_DIRECTION[v]
        assert c["res_quantile_binding"][v] == (max(qf, qd) if direction == "positive" else min(qf, qd))
    # deterministic: the same configuration twice is bit-identical (T2 at the function level)
    again = nulls.run_configuration_null(est, alive, symbols, method="fm_neutral_8w", rho_f=0.09, beta_sd=0.6,
                                         n_reps=12, seed=53)
    assert again["constants"] == c
    with pytest.raises(ValueError, match="direction"):
        nulls.binding_quantile(0.1, 0.2, "sideways")


# ---- DEC-87 (V1): the winner is confirmed with each window's OWN calibration ---

def _cell(null_mean: float, ceiling: float, n_reps: int = 1000) -> dict:
    return {"variants": {v: {"mean_ic_draws_mean": null_mean, "mean_ic_draws_sd": 0.004,
                             "quantile_one_sided": 0.02, "direction": nulls.REGISTERED_DIRECTION[v]}
                         for v in characteristics.VARIANT_NAMES},
            "ceiling_mean_of_max": ceiling, "n_reps": n_reps}


def _confirmation_fixture():
    """Two judged windows with DIFFERENT calibrations; floor 0.05, W 52 -> null-mean bound 0.001734, pure-noise
    ceiling 0.009 -> ceiling bound 0.0135."""
    def study(rho_m, sd_m, rho_s, sd_s):
        return {"calibrations": {"measured": {"rho_f": rho_m, "beta_sd_calibrated": sd_m},
                                 "stress": {"rho_f": rho_s, "beta_sd_calibrated": sd_s}}}
    w_arr = np.zeros((40, 12))
    a_arr = np.ones((40, 12), dtype=bool)
    windows_out, sliced = {}, {}
    for wn, cal in (("W1", study(0.046, 0.574, 0.092, 0.771)), ("W2", study(0.042, 0.446, 0.083, 0.583))):
        windows_out[wn] = {"available": True, "beta_control_method_study": cal,
                           "noise_floor_and_threshold": {"floor": {"e_floor": 0.05}, "w_judged": 52},
                           "selection_ceiling_measured": {"ceiling_ic_mean": 0.009}}
        sliced[wn] = {"returns_est": w_arr, "alive": a_arr}
    return windows_out, sliced, [f"s{i}" for i in range(11)] + ["BTCUSDT"]


def test_dec87_confirm_winner_hands_each_window_its_own_calibration(monkeypatch):
    """DEC-87 V1 REGRESSION (DEC-86 Nachtrag): the v5d winner loop reused the variable ``study`` of the previous window
    loop, i.e. always W2's, so W1's winner run carried W2's rho_f/beta_sd. The confirmation must call the null for
    W1 with W1's calibration and for W2 with W2's -- for every calibration and every window."""
    windows_out, sliced, symbols = _confirmation_fixture()
    calls: list[tuple] = []

    def fake_null(window_returns, window_alive, syms, *, method, rho_f, beta_sd, drift_f, n_reps, **kw):
        calls.append((method, rho_f, beta_sd, drift_f, n_reps))
        return _cell(0.0005, 0.008, n_reps)

    monkeypatch.setattr(nulls, "beta_controlled_factor_null", fake_null)
    rec = {"recommended_method": "fm_neutral_8w", "ranked_methods": ["fm_neutral_8w"]}
    conf = prelaunch.confirm_beta_control_winner(windows_out, sliced, symbols, rec, n_reps=1000, seed=53)
    assert conf["confirmed_method"] == "fm_neutral_8w" and conf["beta_window_weeks"] == 8
    assert calls == [("fm_neutral_8w", 0.046, 0.574, 0.0, 1000), ("fm_neutral_8w", 0.092, 0.771, 0.0, 1000),     # W1
                     ("fm_neutral_8w", 0.042, 0.446, 0.0, 1000), ("fm_neutral_8w", 0.083, 0.583, 0.0, 1000)]    # W2
    used = conf["attempts"][0]["windows"]
    assert used["W1"]["calibration_used"]["stress"] == {"rho_f": 0.092, "beta_sd_calibrated": 0.771}
    assert used["W2"]["calibration_used"]["stress"] == {"rho_f": 0.083, "beta_sd_calibrated": 0.583}


def test_dec87_confirm_winner_falls_through_to_the_next_ranked_method_and_reports_none(monkeypatch):
    """DEC-87 Bindung: a recommended method that fails the UNCHANGED DEC-77 rule with the 1.000-replicate cells is
    replaced by the next eligible method of the SAME ranking; if no method is confirmed the finding is 'keine
    Methode bestaetigt' (DEC-77 E1 (c) applies)."""
    windows_out, sliced, symbols = _confirmation_fixture()
    bad, good = _cell(0.0030, 0.008), _cell(0.0005, 0.008)                    # 0.0030 > 0.001734 null-mean bound

    def make_null(failing_methods):
        def fake_null(window_returns, window_alive, syms, *, method, rho_f, beta_sd, drift_f, n_reps, **kw):
            return bad if method in failing_methods else good
        return fake_null

    rec = {"recommended_method": "fm_neutral_8w", "ranked_methods": ["fm_neutral_8w", "fm_neutral_13w", "double_sort_13w"]}
    monkeypatch.setattr(nulls, "beta_controlled_factor_null", make_null({"fm_neutral_8w"}))
    conf = prelaunch.confirm_beta_control_winner(windows_out, sliced, symbols, rec, n_reps=1000, seed=53)
    assert conf["confirmed_method"] == "fm_neutral_13w"
    assert [a["method"] for a in conf["attempts"]] == ["fm_neutral_8w", "fm_neutral_13w"]
    assert [a["confirmed"] for a in conf["attempts"]] == [False, True]
    assert conf["attempts"][0]["windows"]["W1"]["pass"] is False
    assert "Vorrang-Methode" in conf["note"]

    monkeypatch.setattr(nulls, "beta_controlled_factor_null", make_null({"fm_neutral_8w", "fm_neutral_13w", "double_sort_13w"}))
    none = prelaunch.confirm_beta_control_winner(windows_out, sliced, symbols, rec, n_reps=1000, seed=53)
    assert none["confirmed_method"] is None and none["beta_window_weeks"] is None
    assert none["note"].startswith("keine Methode bestaetigt") and len(none["attempts"]) == 3
    empty = prelaunch.confirm_beta_control_winner(windows_out, sliced, symbols, {"ranked_methods": []}, n_reps=1000)
    assert empty["confirmed_method"] is None and "keine im Raster zugelassene Methode" in empty["note"]


def test_dec87_recommendation_exposes_the_full_ranking_with_unchanged_rule():
    """The selection rule (smallest residualised SD, tie -> shorter window) is UNCHANGED; DEC-87 only exposes the
    whole order (``ranked_methods``) for the confirmation fall-through."""
    ok = (0.0001, 0.002, 0.01)
    mk = lambda sd: (0.0001, sd, 0.01)                                          # noqa: E731
    study = _fake_study({"fm_neutral_8w": {"measured": mk(0.004), "stress": ok},
                         "fm_neutral_13w": {"measured": mk(0.003), "stress": ok},
                         "double_sort_13w": {"measured": mk(0.0035), "stress": ok},
                         "none": {"measured": (0.05, 0.001, 0.1), "stress": (0.05, 0.001, 0.1)}})
    decision = prelaunch.beta_control_pass_table(study, floor=0.05, w_judged=52, pure_noise_ceiling=0.01,
                                                 variants=("mom1", "rev_gap"))
    windows_out = {wn: {"available": True, "beta_control_decision": decision, "beta_control_method_study": study}
                   for wn in ("W1", "W2")}
    rec = prelaunch.beta_control_recommendation(windows_out)
    assert rec["recommended_method"] == "fm_neutral_13w"
    assert rec["ranked_methods"] == ["fm_neutral_13w", "double_sort_13w", "fm_neutral_8w"]   # ascending residualised SD
    assert "none" not in rec["ranked_methods"]


def _relaxed_pass_table(monkeypatch):
    """The tiny 12-symbol fixture is statistically too weak for the strict DEC-77 bounds; relax the TOLERANCE FACTORS
    only (the rule's arithmetic is the real function) -- same discipline as the Gegenprobe knobs."""
    real = prelaunch.beta_control_pass_table

    def relaxed(study, **kw):
        kw.setdefault("null_mean_tol_factor", 1e6)
        kw.setdefault("ceiling_tol_factor", 1e6)
        return real(study, **kw)

    monkeypatch.setattr(prelaunch, "beta_control_pass_table", relaxed)


_PRELAUNCH_TINY = dict(
    n_sims=5, n_reps_factor_null=5, n_reps_beta_control_study=5, seed=53,
    gegenprobe_n_reps=10, gegenprobe_rel_tol=10.0, gegenprobe_z_max=1e9, gegenprobe_market_check=False,
    calibration_search_n_reps=5, calibration_search_rel_tol=10.0, calibration_search_max_iter=8)


def test_dec87_prelaunch_winner_carries_its_own_windows_calibration_and_run_configuration_constants(tmp_path, monkeypatch):
    """DEC-87 V1 + (A)/(E) end to end on the fixture tree: the confirmed winner's high-rep cells of W1 carry W1's
    rho_f/beta_sd (not W2's), the drifting stress cell exists, and the frozen constants of each window are exactly
    what ``nulls.run_configuration_null`` -- the function ``run_full`` recomputes with -- returns for that window."""
    _relaxed_pass_table(monkeypatch)
    # On this tiny fixture both windows calibrate to the same beta_sd; make the windows DIFFERENT (W2 gets larger
    # rho_f/beta_sd) so that using the wrong window's study -- the v5d defect -- would be visible.
    orig_study = nulls.beta_control_method_study
    n_calls = []

    def distinct_study(*a, **kw):
        out = orig_study(*a, **kw)
        i = len(n_calls)
        n_calls.append(i)
        for cal in out["calibrations"].values():
            cal["rho_f"] = cal["rho_f"] * (1.0 + 0.5 * i)
            cal["beta_sd_calibrated"] = cal["beta_sd_calibrated"] * (1.0 + 0.25 * i)
        return out

    monkeypatch.setattr(nulls, "beta_control_method_study", distinct_study)
    panel, weekly, _sb, _sm, _db, del_manifest, dd_path = _build_prelaunch_fixture_tree(tmp_path)
    report = prelaunch.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=del_manifest, delisting_dates_path=dd_path,
        n_reps_beta_control_winner=6,
        data_fingerprints={"union_range_fingerprint": "aa" * 32, "delisting_dates_sha256": "bb" * 32},
        **_PRELAUNCH_TINY)
    assert len(n_calls) == 2                                           # W1 then W2 (never L)
    conf = report["beta_control_confirmation"]
    method = conf["confirmed_method"]
    assert method and method == report["beta_control_recommendation"]["ranked_methods"][0] == conf["ranked_methods"][0]
    assert report["data_fingerprints"]["union_range_fingerprint"] == "aa" * 32
    w1, w2 = report["windows"]["W1"], report["windows"]["W2"]
    cal1 = w1["beta_control_method_study"]["calibrations"]
    cal2 = w2["beta_control_method_study"]["calibrations"]
    assert cal1["stress"]["beta_sd_calibrated"] != cal2["stress"]["beta_sd_calibrated"]       # windows really differ
    for wn, w, cal in (("W1", w1, cal1), ("W2", w2, cal2)):
        hr = w["beta_control_recommended_high_rep"]
        assert set(hr) == {"measured", "stress", "stress_drifting"}
        for name in ("measured", "stress"):
            assert hr[name]["rho_f"] == cal[name]["rho_f"] and hr[name]["beta_sd"] == cal[name]["beta_sd_calibrated"]
            assert hr[name]["n_reps"] == 6 and hr[name]["method"] == method
        assert hr["stress_drifting"]["drift_f"] == pytest.approx(nulls.DRIFT_F_DRIFTING)
        assert hr["stress_drifting"]["rho_f"] == cal["stress"]["rho_f"]
        fz = w["frozen_null_constants"]
        window = prelaunch.slice_window(weekly["weeks"], *prelaunch.WINDOWS[wn], weekly["returns"], weekly["alive"])
        est = nulls.estimation_returns(weekly)[window["lo"]:window["hi"]]
        cfg = nulls.run_configuration_null(est, window["alive"], panel["symbols"], method=method, convention="close_at_last",
                                           n_reps=6, seed=53, rho_f=cal["stress"]["rho_f"],
                                           beta_sd=cal["stress"]["beta_sd_calibrated"])
        for key in ("ceiling_method_stress", "res_quantile_driftfree", "res_quantile_drifting", "res_quantile_binding"):
            assert fz[key] == cfg["constants"][key]
        assert fz["n_reps"] == 6 and fz["seed"] == 53 and fz["calibration"] == "stress"
        # the confirmation's own stress cell is the same configuration as the run's driftfree cell
        att = [a for a in conf["attempts"] if a["method"] == method][0]["windows"][wn]["cells"]["stress"]
        assert att["ceiling_mean_of_max"] == fz["ceiling_method_stress"]
    # the report carries the new open sections incl. the H-30 weekly-unit summary (L stays in its sealed file)
    assert report["h30_feasibility_weekly_units"]["units"].startswith("weekly")
    assert set(report["windows"]["W1"]["gate5_reachability_by_variant"]) == {"vol_rv", "vol_max", "vol_beta"}
    assert report["historical_ts_ceiling_note"] and "DEC-87 (A)" in report["historical_ts_ceiling_note"]


def test_dec87_prelaunch_without_a_confirmed_method_has_no_frozen_constants(tmp_path):
    """The strict DEC-77 bounds reject everything on the 12-symbol fixture: the report says so ('keine Methode
    bestaetigt', DEC-77 E1 (c)), carries NO ``beta_control_recommended_high_rep``/``frozen_null_constants`` and
    nothing is silently picked."""
    panel, weekly, _sb, _sm, _db, del_manifest, dd_path = _build_prelaunch_fixture_tree(tmp_path)
    report = prelaunch.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=del_manifest, delisting_dates_path=dd_path,
        n_reps_beta_control_winner=5, **_PRELAUNCH_TINY)
    conf = report["beta_control_confirmation"]
    if conf["confirmed_method"] is None:                         # the expected outcome of this fixture
        assert conf["note"].startswith("keine Methode bestaetigt")
        for wn in ("W1", "W2"):
            assert "frozen_null_constants" not in report["windows"][wn]
            assert "beta_control_recommended_high_rep" not in report["windows"][wn]
    assert report["data_fingerprints"] is None


def test_dec87_prelaunch_markdown_has_the_v5e_sections(tmp_path, monkeypatch):
    """DEC-87 item 12: the Markdown report carries Gewinner-Bestaetigung, bindende Decke / Drift-Quantile,
    H-30-Feasibility (Wocheneinheit), Gate-(5)-Erreichbarkeit and Fingerprints sections; the v3 TS ceiling line is
    labelled 'historisch, nicht bindend'."""
    _relaxed_pass_table(monkeypatch)
    panel, weekly, _sb, _sm, _db, del_manifest, dd_path = _build_prelaunch_fixture_tree(tmp_path)
    report = prelaunch.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=del_manifest, delisting_dates_path=dd_path,
        n_reps_beta_control_winner=5,
        data_fingerprints={"union_range_fingerprint": "aa" * 32, "delisting_dates_sha256": "bb" * 32,
                           "union_range_detail": {"n_partitions": 7}}, **_PRELAUNCH_TINY)
    art = prelaunch.write_prelaunch_artifacts(tmp_path / "out", report)
    md = Path(art["artifacts"]["wp13a_prelaunch_md"]["path"]).read_text(encoding="utf-8")
    for heading in ("## Gewinner-Bestaetigung (DEC-87 V1", "## Bindende GL-012-Decke (DEC-87 (A)) und Drift-Quantile",
                    "## H-30-Feasibility in Wocheneinheiten (DEC-87 (G))", "## Gate-(5)-Erreichbarkeit (DEC-87 V5",
                    "## Daten-Fingerprints (DEC-87 V9)"):
        assert heading in md, heading
    assert "HISTORISCH, NICHT BINDEND" in md and "historisch, nicht bindend" in md
    assert "Decke (bindend) =" in md and "| Variante (W1) | Quantil driftfrei | Quantil drifting" in md
    assert "union_range_fingerprint: " + "aa" * 32 in md and "delisting_dates_sha256: " + "bb" * 32 in md
    assert "| W1 | " in md and "vol_max" in md
    payload = __import__("json").loads(Path(art["artifacts"]["wp13a_prelaunch_json"]["path"]).read_text(encoding="utf-8"))
    assert payload["data_fingerprints"]["union_range_fingerprint"] == "aa" * 32
    assert payload["h30_feasibility_weekly_units"]["units"].startswith("weekly")
    assert "feasible" in payload["h30_feasibility_weekly_units"]
    # the seal still holds: no real-IC key anywhere in the open JSON (new keys included)
    bad = [k for k in _walk_keys(payload) if re.search(r"real.*ic|ic.*real", k.rsplit("/", 1)[-1], re.IGNORECASE)]
    assert not bad
    assert not [k for k in _walk_keys(payload) if k.rsplit("/", 1)[-1] == "mean_ic"]
