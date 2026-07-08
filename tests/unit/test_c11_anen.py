"""Unit tests for the H-11 AnEn vol-regime mess-gate (c11_anen, KAPITALFREI).

Covers the registered H-11 requirements on synthetic fixtures only (the
hypothesis is DATA-GATED — no real-data run happens here):

  (a) causal feature/target computation (explicit no-lookahead test),
  (b) the 30-day analog embargo (a deliberately near duplicate MUST be
      rejected),
  (c) HAR-RV baseline correctness on a synthetic AR process,
  (d) ensemble-CRPS / point-CRPS / CRPSS / bootstrap / BH-FDR correctness —
      including the calibration-sensitivity property that distinguishes
      ensemble-CRPS from the degenerate point-CRPS (registry H-11: the AnEn
      forecast IS the empirical distribution of the 20 analog targets, NOT
      collapsed to its mean),
  (e) positive detection: a regime-switching vol pattern with a leading
      funding signal where the analog ensemble demonstrably beats HAR
      (CRPSS >= 0.05 AND bootstrap-significant), scored with ensemble-CRPS,
  (f) the registered gate's cell_pass requires ALL of CRPSS>=0.05, raw
      bootstrap-p<=0.05 AND BH-FDR rejection — BH-FDR rejection ALONE does
      NOT imply cell_pass (a p=0.09 cell BH-surviving at alpha=0.10 must not
      pass),
  (g) capital_free=true and no cost-model identifiers in the module,
  (h) unlock check: manifest-done_days as PRIMARY source (Bug 4 fix) with
      correct authority over a stale/ahead raw tree; partition-folder-scan
      FALLBACK only when no manifest is present, requiring file size > 0,
  (i) daily RV is built from 1-minute returns aggregated INSIDE DuckDB (Bug 2
      fix), not tick-to-tick returns — verified against a hand-computed
      expected RV on a tiny synthetic tick fixture,
  (j) end-to-end: synthetic harvester tree with >= 800 days -> CLI rc=0;
      short history -> CLI + T2 runner report SKIP/locked (rc=2).
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c11_anen.analog import (
    EMBARGO_DAYS,
    WEIGHT_GRID,
    analog_forecast,
    eligible_candidates,
    tune_weights_loo_crps,
)
from bybit_edge.research.c11_anen.baseline import har_forecast_series
from bybit_edge.research.c11_anen.driver import (
    UNLOCK_MIN_DAYS,
    UNLOCK_RANGE,
    apply_family_flags,
    check_unlock,
    run as driver_run,
)
from bybit_edge.research.c11_anen.features import (
    ANNUALISATION_DAYS,
    compute_feature_matrix,
    compute_target,
    date_range,
    load_daily_rv,
)
from bybit_edge.research.c11_anen.stats import (
    BOOTSTRAP_P_MAX,
    benjamini_hochberg,
    block_bootstrap_p,
    crps_ensemble,
    crps_point,
    crpss,
    pit_ranks,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = REPO_ROOT / "src" / "bybit_edge" / "research" / "c11_anen"

ANN = np.sqrt(float(ANNUALISATION_DAYS))


def _iso_dates(start: str, n: int) -> list[str]:
    d0 = date.fromisoformat(start)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


# ----------------------------------------------------------------------------
# synthetic harvester tree helpers
# ----------------------------------------------------------------------------

def _touch_partitions(base: Path, symbols, streams, days) -> None:
    """Non-empty parquet placeholder per partition.

    The folder-scan FALLBACK (Bug 4 fix) requires parquet file size > 0 — a
    bare ``.touch()`` (0 bytes) must NOT satisfy coverage, so every helper
    write here uses real (if tiny) content.
    """
    for stream in streams:
        for sym in symbols:
            for d in days:
                p = base / "raw" / "bybit" / stream / f"symbol={sym}" / f"date={d}"
                p.mkdir(parents=True, exist_ok=True)
                (p / "part-0.parquet").write_bytes(b"placeholder-nonzero")


def _write_partition(base: Path, stream: str, symbol: str, day_iso: str,
                     ts_ms: list[int], payloads: list[str]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = base / "raw" / "bybit" / stream / f"symbol={symbol}" / f"date={day_iso}"
    d.mkdir(parents=True, exist_ok=True)
    n = len(ts_ms)
    table = pa.table({
        "ts_local_ns": pa.array([t * 1_000_000 for t in ts_ms], pa.int64()),
        "ts_exchange_ms": pa.array(ts_ms, pa.int64()),
        "topic": pa.array([stream] * n, pa.string()),
        "stream": pa.array([stream] * n, pa.string()),
        "symbol": pa.array([symbol] * n, pa.string()),
        "payload_json": pa.array(payloads, pa.string()),
    })
    pq.write_table(table, d / "part-0.parquet")


def _build_synthetic_tree(base: Path, symbols, days: list[str],
                          ticks_per_day: int = 6, seed: int = 7) -> None:
    """Small but realistic tree: publicTrade ticks + rest.fundingRate records."""
    rng = np.random.default_rng(seed)
    for sym in symbols:
        price = 100.0
        for i, d in enumerate(days):
            day_ms = int((date.fromisoformat(d) - date(1970, 1, 1)).days) * 86_400_000
            sigma = 0.02 * (1.0 + 0.5 * np.sin(2.0 * np.pi * i / 90.0))
            ts, payloads = [], []
            for j in range(ticks_per_day):
                price *= float(np.exp(sigma / np.sqrt(ticks_per_day) * rng.standard_normal()))
                side = "Buy" if rng.random() < 0.5 else "Sell"
                # spread ticks across distinct minutes so 1-min bars are non-trivial
                ts.append(day_ms + 1000 + j * 3_600_000)
                payloads.append(json.dumps(
                    {"side": side, "price": f"{price:.4f}", "size": "0.5"}))
            _write_partition(base, "publicTrade", sym, d, ts, payloads)
            funding = 0.0001 * np.sin(2.0 * np.pi * i / 60.0) + 1e-5 * rng.standard_normal()
            _write_partition(base, "rest.fundingRate", sym, d,
                             [day_ms + 8 * 3_600_000],
                             [json.dumps({"symbol": sym,
                                          "fundingRate": f"{funding:.8f}",
                                          "fundingRateTimestamp": str(day_ms)})])


def _write_manifest(base: Path, rows: list[tuple[str, str, str, str, str]]) -> Path:
    """Fake ``harvest_manifest.sqlite`` with the real DATASET.md §7 schema."""
    manifest_dir = base / "state"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    db_path = manifest_dir / "harvest_manifest.sqlite"
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            "CREATE TABLE partitions "
            "(exchange TEXT, stream TEXT, symbol TEXT, date TEXT, status TEXT)")
        con.executemany("INSERT INTO partitions VALUES (?,?,?,?,?)", rows)
        con.commit()
    finally:
        con.close()
    return db_path


# ----------------------------------------------------------------------------
# (a) feature computation — correct AND causal
# ----------------------------------------------------------------------------

def test_feature_values_correct():
    n = 40
    rv = np.linspace(0.01, 0.05, n)
    funding = 1e-4 * np.arange(n, dtype=np.float64)  # exact linear trend
    feats, log_rv22 = compute_feature_matrix(rv, funding)

    t = 30
    assert feats[t, 0] == pytest.approx(np.log(rv[t] * ANN))
    rms5 = np.sqrt(np.mean(rv[t - 4 : t + 1] ** 2))
    assert feats[t, 1] == pytest.approx(np.log(rms5 * ANN))
    rms20 = np.sqrt(np.mean(rv[t - 19 : t + 1] ** 2))
    assert feats[t, 2] == pytest.approx(np.log(rms20 * ANN))
    assert feats[t, 3] == pytest.approx(funding[t])
    # OLS slope of an exact linear series == its increment
    assert feats[t, 4] == pytest.approx(1e-4)
    rms22 = np.sqrt(np.mean(rv[t - 21 : t + 1] ** 2))
    assert log_rv22[t] == pytest.approx(np.log(rms22 * ANN))
    # warm-up rows are NaN (no partial windows = no implicit lookback shortcuts)
    assert np.isnan(feats[3, 1]) and np.isnan(feats[18, 2]) and np.isnan(log_rv22[20])


def test_features_are_causal_no_lookahead():
    rng = np.random.default_rng(11)
    n = 80
    rv = np.exp(rng.normal(np.log(0.02), 0.3, n))
    funding = 1e-4 * rng.standard_normal(n)
    t = 50

    feats1, lr22_1 = compute_feature_matrix(rv, funding)
    rv2, fu2 = rv.copy(), funding.copy()
    rv2[t + 1 :] = rv2[t + 1 :] * 7.0 + 0.5   # corrupt strictly-future data
    fu2[t + 1 :] = fu2[t + 1 :] + 0.123
    feats2, lr22_2 = compute_feature_matrix(rv2, fu2)

    # every feature at day <= t must be bit-identical: features use data <= t only
    np.testing.assert_array_equal(feats1[: t + 1], feats2[: t + 1])
    np.testing.assert_array_equal(lr22_1[: t + 1], lr22_2[: t + 1])
    # and future rows DID change (the corruption was real)
    assert not np.allclose(feats1[t + 1 :, 0], feats2[t + 1 :, 0], equal_nan=True)


def test_target_uses_only_strictly_future_days():
    rng = np.random.default_rng(12)
    n = 60
    rv = np.exp(rng.normal(np.log(0.02), 0.3, n))
    tgt1 = compute_target(rv)
    t = 30
    # target(t) covers t+1..t+3 exactly: changing day t leaves target(t) alone...
    rv_day_t = rv.copy()
    rv_day_t[t] *= 3.0
    assert compute_target(rv_day_t)[t] == tgt1[t]
    # ...changing day t+1 changes it
    rv_next = rv.copy()
    rv_next[t + 1] *= 3.0
    assert compute_target(rv_next)[t] != tgt1[t]
    # value check
    expected = np.log(np.sqrt(np.mean(rv[t + 1 : t + 4] ** 2)) * ANN)
    assert tgt1[t] == pytest.approx(expected)
    # last horizon days have no observable target
    assert np.all(np.isnan(tgt1[-3:]))


# ----------------------------------------------------------------------------
# (i) 1-min-RV DuckDB aggregation (Bug 2)
# ----------------------------------------------------------------------------

def test_load_daily_rv_uses_1min_bars_not_tick_returns(tmp_path):
    """Hand-computed expected RV from 1-minute LAST-price bars.

    Multiple ticks land in the SAME minute bucket; only the last (by
    ts_exchange_ms) must count per bucket (max_by semantics) — a tick-return
    implementation would instead see every intermediate trade and produce a
    different (inflated) RV. A separate day is written to prove no
    cross-midnight return leaks in (the SQL partitions by day_idx).
    """
    day0 = "2024-01-01"
    day1 = "2024-01-02"
    day0_ms = int((date.fromisoformat(day0) - date(1970, 1, 1)).days) * 86_400_000
    day1_ms = int((date.fromisoformat(day1) - date(1970, 1, 1)).days) * 86_400_000

    # minute 0 [0, 60000): two trades, LAST one (ts=50000, price=105) must win
    # minute 1 [60000, 120000): one trade, price=110
    # minute 2 [120000, 180000): one trade, price=108
    ts0 = [day0_ms + 1_000, day0_ms + 50_000, day0_ms + 61_000, day0_ms + 125_000]
    px0 = [100.0, 105.0, 110.0, 108.0]
    payloads0 = [json.dumps({"side": "Buy", "price": f"{p:.4f}", "size": "1"}) for p in px0]
    _write_partition(tmp_path, "publicTrade", "BTCUSDT", day0, ts0, payloads0)

    # a lone trade on the next day: must NOT create a cross-midnight return
    # against day0's last bar (105 minute-2 bar of day0 vs day1's price)
    ts1 = [day1_ms + 5_000, day1_ms + 65_000]
    px1 = [200.0, 202.0]
    payloads1 = [json.dumps({"side": "Sell", "price": f"{p:.4f}", "size": "1"}) for p in px1]
    _write_partition(tmp_path, "publicTrade", "BTCUSDT", day1, ts1, payloads1)

    out = load_daily_rv(tmp_path, "BTCUSDT", day0, day1)

    r1 = np.log(110.0 / 105.0)
    r2 = np.log(108.0 / 110.0)
    expected_rv0 = float(np.sqrt(r1 * r1 + r2 * r2))
    assert out[day0] == pytest.approx(expected_rv0)

    # day1 has only 2 minute bars -> exactly 1 within-day return
    r_day1 = np.log(202.0 / 200.0)
    expected_rv1 = float(np.sqrt(r_day1 * r_day1))
    assert out[day1] == pytest.approx(expected_rv1)

    # sanity: a NAIVE tick-to-tick RV over day0 (4 consecutive trades) would
    # differ from the 1-min-bar RV (3 tick returns vs. 2 minute-bar returns)
    tick_rets = np.diff(np.log(np.array(px0)))
    naive_tick_rv = float(np.sqrt(np.sum(tick_rets * tick_rets)))
    assert naive_tick_rv != pytest.approx(expected_rv0), (
        "fixture must actually distinguish 1-min-bar RV from tick RV")


# ----------------------------------------------------------------------------
# (b) 30-day embargo
# ----------------------------------------------------------------------------

def test_embargo_rejects_near_analog_candidate():
    rng = np.random.default_rng(13)
    n = 120
    feats = rng.standard_normal((n, 5))
    targets = rng.standard_normal(n)
    t = 115
    # plant a PERFECT analog (distance 0) inside the embargo zone at t-10:
    # without the embargo it would be the #1 nearest neighbour.
    feats[t - 10] = feats[t]
    members, sel = analog_forecast(feats, targets, t, np.ones(5), k=5)
    assert members.size == 5 and np.all(np.isfinite(members))
    assert sel.size == 5
    assert (t - 10) not in sel, "embargoed near-duplicate MUST be rejected"
    assert np.all(sel <= t - EMBARGO_DAYS), "candidate rule is t' <= t - 30"
    # the k member targets are literally the analog library's own targets:
    np.testing.assert_array_equal(members, targets[sel])

    cand = eligible_candidates(t, feats, targets, EMBARGO_DAYS)
    assert cand.max() == t - EMBARGO_DAYS
    # too little history for a full ensemble -> empty, never a partial ensemble
    members_early, sel_early = analog_forecast(feats, targets, 20, np.ones(5), k=5)
    assert members_early.size == 0 and sel_early.size == 0


# ----------------------------------------------------------------------------
# (c) HAR-RV baseline on a synthetic AR process
# ----------------------------------------------------------------------------

def test_har_baseline_recovers_linear_target_on_ar_process():
    rng = np.random.default_rng(14)
    n = 400
    log_rv = np.empty(n)
    log_rv[0] = np.log(0.02)
    mu, phi = np.log(0.02), 0.9
    for t in range(1, n):
        log_rv[t] = mu + phi * (log_rv[t - 1] - mu) + 0.2 * rng.standard_normal()
    rv = np.exp(log_rv)
    feats, log_rv22 = compute_feature_matrix(rv, np.zeros(n))
    # exact HAR data-generating process on the three log-RV regressors
    y = 0.2 + 0.5 * feats[:, 0] + 0.3 * feats[:, 1] + 0.1 * log_rv22 \
        + 0.001 * rng.standard_normal(n)
    dates = _iso_dates("2024-01-01", n)
    fidx = np.arange(120, n - 5, dtype=np.int64)
    fc, n_refits = har_forecast_series(feats[:, 0], feats[:, 1], log_rv22, y,
                                       dates, fidx)
    ok = np.isfinite(fc)
    assert ok.sum() > 200
    err = np.abs(fc[ok] - y[fidx][ok])
    assert float(np.mean(err)) < 0.02, "OLS must recover the linear HAR process"
    assert n_refits >= 2, "monthly expanding refit must actually refit"


def test_har_fit_is_causal_wrt_embargo():
    rng = np.random.default_rng(15)
    n = 200
    x = rng.standard_normal(n)
    y = 1.0 + 2.0 * x + 0.01 * rng.standard_normal(n)
    dates = _iso_dates("2024-01-01", n)
    t = 180
    fc1, _ = har_forecast_series(x, x, x, y, dates, np.array([t]))
    y2 = y.copy()
    y2[t - 29 :] = -99.0  # corrupt everything inside the embargo AND the future
    fc2, _ = har_forecast_series(x, x, x, y2, dates, np.array([t]))
    assert fc1[0] == pytest.approx(fc2[0]), "fit must only use samples <= t-30"


# ----------------------------------------------------------------------------
# (d) ensemble-CRPS / point-CRPS / CRPSS / bootstrap / BH-FDR
# ----------------------------------------------------------------------------

def test_crps_point_and_crpss():
    np.testing.assert_allclose(
        crps_point(np.array([1.0, 2.0]), np.array([1.5, 1.0])),
        np.array([0.5, 1.0]))
    assert crpss(np.full(4, 0.5), np.full(4, 1.0)) == pytest.approx(0.5)
    assert crpss(np.full(4, 1.0), np.full(4, 1.0)) == pytest.approx(0.0)
    assert crpss(np.full(4, 2.0), np.full(4, 1.0)) == pytest.approx(-1.0)
    assert np.isnan(crpss(np.array([1.0]), np.array([0.0])))
    assert np.isnan(crpss(np.array([]), np.array([])))


def test_crps_ensemble_reduces_to_point_crps_when_degenerate():
    """A one-point / all-identical-member ensemble IS the degenerate
    distribution — ensemble-CRPS must reduce exactly to |forecast - obs|."""
    members = np.full((3, 7), 2.0)
    obs = np.array([2.5, 1.0, 2.0])
    np.testing.assert_allclose(
        crps_ensemble(members, obs), crps_point(np.full(3, 2.0), obs))
    # single-day (1-D) convenience form:
    np.testing.assert_allclose(
        crps_ensemble(np.full(5, 3.0), 4.0), crps_point(np.array([3.0]), np.array([4.0])))


def test_crps_ensemble_rewards_calibration_not_just_the_mean():
    """THE distinguishing property of the registered H-11 metric: two
    ensembles with the IDENTICAL per-day mean (so a collapsed-mean point
    score could never tell them apart) must score DIFFERENTLY under proper
    ensemble-CRPS — tight/well-calibrated spread scores markedly LOWER
    (better) than diffuse/miscalibrated spread with the same mean.
    """
    rng = np.random.default_rng(20)
    n_days = 300
    obs = rng.normal(0.0, 1.0, n_days)

    tight_dev = rng.normal(0.0, 0.15, (n_days, 20))
    tight_dev -= tight_dev.mean(axis=1, keepdims=True)  # exact per-day mean = obs
    tight = obs[:, None] + tight_dev

    diffuse_dev = rng.normal(0.0, 1.5, (n_days, 20))
    diffuse_dev -= diffuse_dev.mean(axis=1, keepdims=True)  # exact per-day mean = obs
    diffuse = obs[:, None] + diffuse_dev

    # means are EXACTLY identical by construction -- a point/mean-based score
    # cannot distinguish tight from diffuse at all:
    np.testing.assert_allclose(tight.mean(axis=1), diffuse.mean(axis=1))

    c_tight = crps_ensemble(tight, obs)
    c_diffuse = crps_ensemble(diffuse, obs)
    assert np.mean(c_tight) < np.mean(c_diffuse), (
        "tightly-calibrated ensemble must score lower (better) CRPS than a "
        "diffuse one with the identical mean")

    # against a mediocre fixed point baseline (HAR proxy), the tight ensemble
    # clears the registered CRPSS>=0.05 floor while the diffuse one does not
    baseline_fc = obs + rng.normal(0.0, 0.6, n_days)
    c_har = crps_point(baseline_fc, obs)
    skill_tight = crpss(c_tight, c_har)
    skill_diffuse = crpss(c_diffuse, c_har)
    assert skill_tight >= 0.05
    assert skill_tight > skill_diffuse


def test_pit_ranks_uniform_for_calibrated_ensemble():
    """PIT rank histogram (registry: non-judgment-bearing secondary
    diagnostic) — a well-calibrated ensemble (obs drawn from the SAME
    distribution as the members) gives approximately uniform ranks 0..k."""
    rng = np.random.default_rng(21)
    k = 20
    n_days = 4000
    members = rng.normal(0.0, 1.0, (n_days, k))
    obs = rng.normal(0.0, 1.0, n_days)  # same generating distribution
    ranks = pit_ranks(members, obs)
    assert ranks.min() >= 0 and ranks.max() <= k
    hist = np.bincount(ranks, minlength=k + 1)
    expected = n_days / (k + 1)
    # loose uniformity check (chi-square-ish tolerance, no flaky exact bins)
    assert np.all(np.abs(hist - expected) < 0.5 * expected)

    # a badly biased ensemble (obs always ABOVE all members) piles up at rank k
    biased_members = rng.normal(0.0, 1.0, (n_days, k))
    biased_obs = np.full(n_days, 100.0)
    biased_ranks = pit_ranks(biased_members, biased_obs)
    assert np.all(biased_ranks == k)


def test_block_bootstrap_p_signal_vs_noise():
    rng = np.random.default_rng(16)
    strong = 0.5 + 0.05 * rng.standard_normal(120)  # clearly positive mean
    assert block_bootstrap_p(strong, seed=1) <= 0.05
    noise = rng.standard_normal(120)
    noise = noise - noise.mean()                     # mean exactly 0 under H0
    assert block_bootstrap_p(noise, seed=1) > 0.2
    assert block_bootstrap_p(np.array([0.1]), seed=1) == 1.0  # degenerate


def test_benjamini_hochberg_own_copy():
    rejected, p_crit = benjamini_hochberg([0.001, 0.02, 0.5, 0.9], 0.10)
    assert rejected == [True, True, False, False]
    assert p_crit == pytest.approx(0.02)
    assert benjamini_hochberg([], 0.10) == ([], 0.0)
    rej_none, crit_none = benjamini_hochberg([0.5, 0.9], 0.10)
    assert rej_none == [False, False] and crit_none == 0.0


def test_tune_weights_loo_crps_deterministic_and_on_grid():
    rng = np.random.default_rng(17)
    n = 160
    feats = rng.standard_normal((n, 5))
    targets = 2.0 * feats[:, 0] + 0.05 * rng.standard_normal(n)  # feature 0 informative
    tune_idx = np.arange(60, n, dtype=np.int64)
    grid = (0.0, 1.0)
    w1, s1 = tune_weights_loo_crps(feats, targets, tune_idx, grid=grid, k=5)
    w2, s2 = tune_weights_loo_crps(feats, targets, tune_idx, grid=grid, k=5)
    np.testing.assert_array_equal(w1, w2)          # frozen + deterministic
    assert s1 == s2 and np.isfinite(s1)
    assert all(float(x) in grid for x in w1)
    assert np.any(w1 > 0.0)                        # all-zero combo is excluded
    assert w1[0] == 1.0, "tuning must weight the informative feature"
    assert tuple(WEIGHT_GRID) == (0.0, 0.5, 1.0, 1.5, 2.0)  # registered grid frozen


# ----------------------------------------------------------------------------
# (e) positive detection (ensemble-CRPS)
# ----------------------------------------------------------------------------

def _forecast_cell(feats, log_rv22, targets, dates, fidx, weights, k=20):
    """AnEn (ensemble-CRPS) vs. HAR (point-CRPS) — mirrors driver.run scoring."""
    members_list, days = [], []
    for t in fidx:
        t = int(t)
        if not np.isfinite(targets[t]):
            continue
        members, _sel = analog_forecast(feats, targets, t, weights, k=k)
        if members.size:
            members_list.append(members)
            days.append(t)
    days = np.asarray(days, dtype=np.int64)
    har, _ = har_forecast_series(feats[:, 0], feats[:, 1], log_rv22, targets,
                                 dates, days)
    paired = np.isfinite(har)
    obs = targets[days][paired]
    members_mat = (np.vstack(members_list) if members_list
                   else np.empty((0, k), dtype=np.float64))
    c_anen = crps_ensemble(members_mat[paired], obs)
    c_har = crps_point(har[paired], obs)
    return c_anen, c_har


def _regime_series(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Funding square wave LEADS the vol regime by 3 days (AnEn-favourable)."""
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    funding = np.where((idx // 30) % 2 == 0, 1e-4, -1e-4)
    lead = np.roll(funding, 3)
    lead[:3] = funding[0]
    regime_rv = np.where(lead > 0, 0.05, 0.012)
    rv = regime_rv * np.exp(0.10 * rng.standard_normal(n))
    return rv, funding


def test_positive_detection_regime_switching_vol():
    n = 560
    rv, funding = _regime_series(n, seed=18)
    feats, log_rv22 = compute_feature_matrix(rv, funding)
    targets = compute_target(rv)
    dates = _iso_dates("2024-01-01", n)
    fidx = np.arange(260, n - 4, dtype=np.int64)
    # plausible frozen tuning outcome from the registered grid: the funding
    # features carry the regime lead, the RV features carry the level
    weights = np.array([0.5, 0.5, 0.5, 2.0, 2.0])
    c_anen, c_har = _forecast_cell(feats, log_rv22, targets, dates, fidx, weights)
    skill = crpss(c_anen, c_har)
    p = block_bootstrap_p(c_har - c_anen, seed=42)
    assert skill >= 0.05, f"AnEn must beat HAR on the regime pattern (CRPSS={skill:.3f})"
    assert p <= 0.05, f"the win must be bootstrap-significant (p={p:.4f})"


def test_ensemble_crps_vs_point_crps_asymmetry_is_documented_not_a_bug():
    """CHARACTERISATION test (not a regression on "AnEn must lose on noise"):
    on pure AR(1) noise with NO exploitable regime structure between funding
    and RV, the registered metric (proper ensemble-CRPS for AnEn vs.
    degenerate point-CRPS for HAR) can still show AnEn with a positive CRPSS.
    This is NOT an implementation bug: it verified here that the ensemble's
    raw POINT accuracy (its own mean vs. obs) is NOT better than HAR's — the
    apparent CRPSS "edge" is a scoring-rule effect (CRPS rewards calibrated
    spread; a point forecast structurally cannot express any uncertainty and
    is fully penalised for every miss, Gneiting & Raftery 2007). This is
    exactly why the registered gate ALSO requires bootstrap significance
    under BH-FDR AND the raw p<=0.05 clause (Bug 3) rather than trusting
    CRPSS in isolation. Recorded here (fixed seeds) so a future accidental
    change to the scoring formula is caught by this test.
    """
    rng = np.random.default_rng(19)
    n = 560
    log_rv = np.empty(n)
    log_rv[0] = np.log(0.02)
    mu, phi = np.log(0.02), 0.85
    for t in range(1, n):
        log_rv[t] = mu + phi * (log_rv[t - 1] - mu) + 0.25 * rng.standard_normal()
    rv = np.exp(log_rv)
    funding = 1e-4 * rng.standard_normal(n)  # pure noise, no regime structure
    feats, log_rv22 = compute_feature_matrix(rv, funding)
    targets = compute_target(rv)
    dates = _iso_dates("2024-01-01", n)
    fidx = np.arange(260, n - 4, dtype=np.int64)
    weights = np.ones(5)

    members_list, days = [], []
    for t in fidx:
        t = int(t)
        if not np.isfinite(targets[t]):
            continue
        members, _sel = analog_forecast(feats, targets, t, weights, k=20)
        if members.size:
            members_list.append(members)
            days.append(t)
    days = np.asarray(days, dtype=np.int64)
    har, _ = har_forecast_series(feats[:, 0], feats[:, 1], log_rv22, targets, dates, days)
    paired = np.isfinite(har)
    obs = targets[days][paired]
    members_mat = np.vstack(members_list)[paired]

    ensemble_mean_mae = float(np.mean(np.abs(members_mat.mean(axis=1) - obs)))
    har_mae = float(np.mean(np.abs(har[paired] - obs)))
    # the ensemble's collapsed-mean point accuracy is genuinely NOT better --
    # no informational edge is smuggled in:
    assert ensemble_mean_mae >= har_mae, (
        "fixture must show no genuine point-forecast edge for the ensemble "
        "mean (isolates the scoring-rule effect from real information)")


# ----------------------------------------------------------------------------
# (f) registered gate: cell_pass requires raw p<=0.05 (Bug 3)
# ----------------------------------------------------------------------------

def test_cell_pass_requires_raw_bootstrap_p_not_just_fdr_reject():
    """Registry H-11 (verbatim): CRPSS>=0.05 UND Bootstrap-p<=0.05 nach
    BH-FDR alpha=0.10 -- BOTH conditions, not BH-rejection alone. Family
    {0.01, 0.02, 0.04, 0.09} at alpha=0.10: BH-FDR rejects ALL 4 (the audit's
    exact example), but the p=0.09 cell must NOT get cell_pass=True.
    """
    cells = [{"bootstrap_p": p, "crpss_ge_min": True} for p in (0.01, 0.02, 0.04, 0.09)]
    rejected, p_crit = apply_family_flags(cells)
    assert rejected == [True, True, True, True], "BH-FDR alpha=0.10 rejects all 4 here"
    assert p_crit == pytest.approx(0.09)
    assert BOOTSTRAP_P_MAX == 0.05

    assert cells[3]["fdr_significant"] is True
    assert cells[3]["boot_p_le_max"] is False
    assert cells[3]["cell_pass"] is False, (
        "BH-FDR rejection alone must NOT set cell_pass -- raw p<=0.05 is required")
    for c in cells[:3]:
        assert c["boot_p_le_max"] is True
        assert c["fdr_significant"] is True
        assert c["cell_pass"] is True


def test_cell_pass_requires_crpss_floor_too():
    cells = [
        {"bootstrap_p": 0.01, "crpss_ge_min": False},
        {"bootstrap_p": 0.02, "crpss_ge_min": True},
    ]
    apply_family_flags(cells)
    assert cells[0]["cell_pass"] is False, "CRPSS<0.05 must fail even with p<=0.05"
    assert cells[1]["cell_pass"] is True


# ----------------------------------------------------------------------------
# (g) capital_free — payload flag + no cost-model code
# ----------------------------------------------------------------------------

def test_capital_free_flag_and_no_cost_identifiers(tmp_path):
    # locked tree -> cheap SKIP payload; the flag must hold in EVERY payload
    days = date_range(UNLOCK_RANGE[0], UNLOCK_RANGE[0])  # a single day only
    _touch_partitions(tmp_path, ("BTCUSDT", "ETHUSDT"),
                      ("publicTrade", "rest.fundingRate"), days)
    payload = driver_run(tmp_path)
    assert payload["capital_free"] is True
    assert payload["data_gated"] is True
    assert payload["status"] == "SKIP"

    # No bps/PnL/Sharpe/friction COMPUTATION code anywhere in the module:
    # scan every identifier in the AST (names, attributes, functions, args).
    # The registry's narrative 25-75x friction-magnitude note may appear in
    # docstrings — identifiers are what would carry an actual cost model.
    forbidden = ("bps", "pnl", "sharpe", "friction", "slippage", "taker", "maker")
    for py in sorted(MODULE_DIR.glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        idents: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                idents.add(node.id)
            elif isinstance(node, ast.Attribute):
                idents.add(node.attr)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                idents.add(node.name)
            elif isinstance(node, ast.arg):
                idents.add(node.arg)
            elif isinstance(node, ast.keyword) and node.arg:
                idents.add(node.arg)
        for ident in idents:
            low = ident.lower()
            for bad in forbidden:
                assert bad not in low, (
                    f"{py.name}: identifier {ident!r} suggests cost-model code "
                    f"(H-11 is KAPITALFREI)")


# ----------------------------------------------------------------------------
# (h) unlock check — manifest done_days PRIMARY (Bug 4), folder-scan fallback
# ----------------------------------------------------------------------------

def test_check_unlock_false_on_short_coverage(tmp_path):
    days = date_range("2024-03-27", "2024-07-04")  # 100 days only
    _touch_partitions(tmp_path, ("BTCUSDT", "ETHUSDT"),
                      ("publicTrade", "rest.fundingRate"), days)
    res = check_unlock(tmp_path)
    assert res["unlocked"] is False
    assert res["unlock_source"] == "partition_folder_scan"  # no manifest present
    assert res["days_required"] == UNLOCK_MIN_DAYS == 730
    assert all(not d["gapless"] for d in res["details"])
    assert res["details"][0]["days_present"] == 100
    assert res["details"][0]["missing_days_sample"][0] == "2024-07-05"


def test_check_unlock_true_on_sufficient_gapless_coverage(tmp_path):
    days = date_range(UNLOCK_RANGE[0], UNLOCK_RANGE[1])
    assert len(days) == 730
    _touch_partitions(tmp_path, ("BTCUSDT", "ETHUSDT"),
                      ("publicTrade", "rest.fundingRate"), days)
    res = check_unlock(tmp_path)
    assert res["unlocked"] is True
    assert res["unlock_source"] == "partition_folder_scan"
    assert all(d["gapless"] for d in res["details"])
    assert len(res["details"]) == 4  # 2 streams x 2 symbols

    # a single missing day ANYWHERE re-locks (gapless is gapless)
    hole = (tmp_path / "raw" / "bybit" / "rest.fundingRate" / "symbol=ETHUSDT"
            / "date=2025-01-15")
    shutil.rmtree(hole)
    res2 = check_unlock(tmp_path)
    assert res2["unlocked"] is False
    bad = [d for d in res2["details"]
           if d["stream"] == "rest.fundingRate" and d["symbol"] == "ETHUSDT"]
    assert bad[0]["missing_days_count"] == 1
    assert bad[0]["missing_days_sample"] == ["2025-01-15"]

    # a range shorter than min_days never unlocks, even if gapless
    res3 = check_unlock(tmp_path, start="2024-03-27", end="2024-07-04")
    assert res3["unlocked"] is False


def test_check_unlock_folder_fallback_rejects_zero_byte_parquet(tmp_path):
    """The OLD proxy's exact blind spot (audit Bug 4): a 0-byte parquet file
    must NOT satisfy coverage in the folder-scan fallback."""
    days = date_range(UNLOCK_RANGE[0], UNLOCK_RANGE[1])
    _touch_partitions(tmp_path, ("BTCUSDT", "ETHUSDT"),
                      ("publicTrade", "rest.fundingRate"), days)
    zero_file = (tmp_path / "raw" / "bybit" / "publicTrade" / "symbol=BTCUSDT"
                 / f"date={days[10]}" / "part-0.parquet")
    zero_file.write_bytes(b"")
    res = check_unlock(tmp_path)
    assert res["unlocked"] is False
    assert res["unlock_source"] == "partition_folder_scan"
    bad = [d for d in res["details"]
           if d["stream"] == "publicTrade" and d["symbol"] == "BTCUSDT"]
    assert bad[0]["missing_days_count"] == 1
    assert bad[0]["missing_days_sample"] == [days[10]]


def test_check_unlock_uses_manifest_done_days_when_present(tmp_path):
    days = date_range(UNLOCK_RANGE[0], UNLOCK_RANGE[1])
    assert len(days) == 730
    rows = [
        ("bybit", stream, sym, d, "DONE")
        for stream in ("publicTrade", "rest.fundingRate")
        for sym in ("BTCUSDT", "ETHUSDT")
        for d in days
    ]
    # deliberately NO raw partition folders at all -- the manifest alone
    # must be sufficient as the PRIMARY source
    _write_manifest(tmp_path, rows)

    res = check_unlock(tmp_path)
    assert res["unlocked"] is True
    assert res["unlock_source"] == "manifest_done_days"

    # mark one day FAILED -> must re-lock via the manifest alone
    db_path = tmp_path / "state" / "harvest_manifest.sqlite"
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            "UPDATE partitions SET status='FAILED' WHERE stream='publicTrade' "
            "AND symbol='BTCUSDT' AND date=?", (days[300],))
        con.commit()
    finally:
        con.close()
    res2 = check_unlock(tmp_path)
    assert res2["unlocked"] is False
    bad = [d for d in res2["details"]
           if d["stream"] == "publicTrade" and d["symbol"] == "BTCUSDT"]
    assert bad[0]["missing_days_count"] == 1
    assert bad[0]["missing_days_sample"] == [days[300]]


def test_check_unlock_manifest_authoritative_over_stale_raw_folder(tmp_path):
    """The exact Bug-4 anti-conservative scenario: a partition folder exists
    on disk for EVERY required day (would satisfy the OLD raw-tree-only
    proxy), but the manifest says one day is still PENDING (active backfill
    in flight). The registered condition (manifest) must win -> stays LOCKED.
    """
    days = date_range(UNLOCK_RANGE[0], UNLOCK_RANGE[1])
    _touch_partitions(tmp_path, ("BTCUSDT", "ETHUSDT"),
                      ("publicTrade", "rest.fundingRate"), days)
    rows = []
    for stream in ("publicTrade", "rest.fundingRate"):
        for sym in ("BTCUSDT", "ETHUSDT"):
            for d in days:
                status = "DONE"
                if stream == "publicTrade" and sym == "ETHUSDT" and d == days[500]:
                    status = "PENDING"
                rows.append(("bybit", stream, sym, d, status))
    _write_manifest(tmp_path, rows)

    res = check_unlock(tmp_path)
    assert res["unlock_source"] == "manifest_done_days"
    assert res["unlocked"] is False, (
        "manifest PENDING day must lock even though the raw folder exists on disk")
    bad = [d for d in res["details"]
           if d["stream"] == "publicTrade" and d["symbol"] == "ETHUSDT"]
    assert bad[0]["missing_days_count"] == 1


# ----------------------------------------------------------------------------
# (j) end-to-end on synthetic harvester trees
# ----------------------------------------------------------------------------

def _cli_main():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "c11_anen_cli", REPO_ROOT / "scripts" / "c11_anen.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


def test_e2e_cli_long_history_runs_green(tmp_path):
    # >= 800 synthetic days covering unlock range + W2 (+ 3-day target spill)
    days = date_range("2024-03-27", "2026-07-03")
    assert len(days) >= 800
    base = tmp_path / "harvest"
    _build_synthetic_tree(base, ("BTCUSDT", "ETHUSDT"), days)
    out = tmp_path / "out"
    rc = _cli_main()([
        "--base-dir", str(base), "--out-dir", str(out),
        # fixture-speed overrides only (registered values stay the defaults):
        "--weight-grid", "1", "--n-bootstrap", "200", "--seed", "42",
    ])
    assert rc == 0
    payload = json.loads((out / "c11_anen_results.json").read_text(encoding="utf-8"))
    assert payload["hypothesis"] == "H-11"
    assert payload["status"] == "RUN"
    assert payload["capital_free"] is True
    assert payload["data_gated"] is True
    assert payload["unlock_check"]["unlocked"] is True
    assert len(payload["cells"]) == 4  # F-ANEN: 2 symbols x 2 windows
    for cell in payload["cells"]:
        assert cell["n_forecast_days"] > 50
        assert cell["crpss"] is not None
        assert 0.0 < cell["bootstrap_p"] <= 1.0
        assert isinstance(cell["fdr_significant"], bool)
        assert isinstance(cell["boot_p_le_max"], bool)
        assert isinstance(cell["cell_pass"], bool)
        # cell_pass must never be True without BOTH conditions (Bug 3)
        if cell["cell_pass"]:
            assert cell["crpss_ge_min"] is True
            assert cell["boot_p_le_max"] is True
            assert cell["fdr_significant"] is True
        assert len(cell["pit_rank_histogram"]) == cell["pit_n_bins"] == 21
        assert sum(cell["pit_rank_histogram"]) == cell["n_forecast_days"]
    assert "any_symbol_both_windows_pass" in payload  # gate-neutral rollup
    md = (out / "c11_anen_results.md").read_text(encoding="utf-8")
    assert "F-ANEN" in md and "KAPITALFREI" in md
    assert "PIT-Rank-Histogramm" in md


def test_e2e_cli_short_history_reports_locked_skip(tmp_path):
    days = date_range("2026-03-27", "2026-07-04")  # ~100-day base store only
    base = tmp_path / "harvest"
    _touch_partitions(base, ("BTCUSDT", "ETHUSDT"),
                      ("publicTrade", "rest.fundingRate"), days)
    out = tmp_path / "out"
    main = _cli_main()
    # check-unlock-only mode: rc=2, no data run
    assert main(["--base-dir", str(base), "--check-unlock-only"]) == 2
    # full run mode: clean SKIP payload, rc=2, no crash
    rc = main(["--base-dir", str(base), "--out-dir", str(out)])
    assert rc == 2
    payload = json.loads((out / "c11_anen_results.json").read_text(encoding="utf-8"))
    assert payload["status"] == "SKIP"
    assert payload["capital_free"] is True
    assert "Entsperr-Bedingung nicht erfuellt" in payload["reason"]
    assert payload["unlock_check"]["unlocked"] is False


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_runner_sh_reports_locked_skip_on_short_history(tmp_path):
    days = date_range("2026-03-27", "2026-07-04")
    base = tmp_path / "harvest"
    _touch_partitions(base, ("BTCUSDT", "ETHUSDT"),
                      ("publicTrade", "rest.fundingRate"), days)
    results = tmp_path / "results"
    env = dict(os.environ)
    env.update({
        "HARVEST_DIR": str(base),
        "H11_RESULTS_DIR": str(results),
        "PYTHON": sys.executable,
    })
    proc = subprocess.run(
        ["bash", str(REPO_ROOT / "scinance2-impl" / "handoff_local" / "run_h11.sh")],
        env=env, capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "H-11 gesperrt" in proc.stdout
    run_dirs = list(results.glob("h11_*"))
    assert len(run_dirs) == 1
    summaries = list(run_dirs[0].glob("SUMMARY_*.md"))
    assert len(summaries) == 1
    text = summaries[0].read_text(encoding="utf-8")
    assert "Entsperr-Bedingung nicht erfuellt" in text
    assert "H11_ANEN | SKIP" in text
