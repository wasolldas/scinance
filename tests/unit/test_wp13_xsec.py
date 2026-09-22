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
    """3 survivors + 1 delisted symbol spanning 2021-01-01..2026-06-30
    (covers L, W1 and W2) -- small enough to run the full
    ``assemble_prelaunch_report`` pipeline (small ``n_sims``) in a unit
    test, reusing ``test_wp12b_delisted_panel``'s fixture-tree writers
    instead of a parallel implementation."""
    surv_base = tmp_path / "panel_1d"
    surv_manifest = surv_base / "panel_manifest.sqlite"
    del_base = tmp_path / "panel_1d_delisted"
    del_manifest = del_base / "panel_manifest.sqlite"

    full_start, full_end = date(2021, 1, 1), date(2026, 6, 30)
    for i, sym in enumerate(["AAAUSDT", "BTCUSDT", "ZZZUSDT"]):
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

    report = prelaunch.assemble_prelaunch_report(
        panel, weekly, delisted_manifest_path=del_manifest, delisting_dates_path=dd_path,
        n_sims=5, n_reps_factor_null=5, seed=53)
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
        n_sims=5, n_reps_factor_null=5, seed=53)
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


# ============================================================================
# end-to-end --prelaunch CLI on a synthetic union tree
# ============================================================================

def _ns_prelaunch(**overrides) -> argparse.Namespace:
    base = dict(
        panel_base="", delisted_base="", delisted_manifest="", delisting_dates="",
        start_year=2021, end_year=2026, as_of="2027-01-01", out="",
        seed=53, n_sims=5, n_reps_factor_null=5, convention="close_at_last", allow_partial=False,
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
    n_weeks, k = 4, 2
    returns = np.array([[0.0, 0.0], [0.10, 0.20], [-0.05, 0.03], [0.02, -0.01]])
    weekly_vol = np.array([[0.04, 0.06], [0.05, 0.03], [0.02, 0.08], [0.01, 0.01]])
    out = ic.vol_weighted_outcome_with_drag(returns, weekly_vol, weight_source="pit")
    target_vol = out["target_vol"]
    assert target_vol == pytest.approx(float(np.median(weekly_vol)))
    # row t=0: formation week 0's vol (weekly_vol[0]) weights returns[1] (NOT returns[0])
    expected_w0 = (returns[1] - 0.5 * weekly_vol[0] ** 2) * (target_vol / weekly_vol[0])
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
# end-to-end --prelaunch CLI (existing suite continues below)
# ============================================================================

def test_cli_prelaunch_end_to_end_synthetic_union_tree(tmp_path):
    _panel, _weekly, surv_base, surv_manifest, del_base, del_manifest, _dd = \
        _build_prelaunch_fixture_tree(tmp_path)
    out_dir = tmp_path / "out"
    ns = _ns_prelaunch(panel_base=str(surv_base), delisted_base=str(del_base), out=str(out_dir))

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
