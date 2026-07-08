"""Tests for the C-10 cross-stream pointer-day mess-gate (c10_pointer, H-10).

Covers:
- (a) Cropper-score correctness on a known mini example (lone spike in an
  11-day centred window => C = 10/sqrt(11)) + trailing-median detrend
  min_periods + pointer-day threshold arithmetic (18-floor, 0.60 share).
- (b) NULL control: 30 INDEPENDENT synthetic series => no pointer days,
  stage-1 surrogate p not significant.
- (c) POSITIVE detection: synchronised anomalies on ~3 days per window across
  >= 60% of the 30 series + a correlated dvol pre-drift => stage 1 AND
  stage 2 significant, all four F-POINTER cells pass.
- (d) N-floor path: only 2 pointer days per window => floor not met, no pass
  (hard power-DROP path, floor NOT lowerable).
- (e) capital_free=true + NO capital-metric token anywhere in the JSON.
- (f) End-to-end against a synthetic harvester Hive tree (publicTrade +
  rest.fundingRate + rest.openInterest + dvol, all 4 stream forms) =>
  CLI rc=0 and a valid gate-neutral payload. publicTrade is DENSE (48
  distinct 1-min bars/day) so the registered 1-min RV definition is
  actually exercised (audit_h10 BUG-1 fix regression guard).
- (g) audit_h10 fix regression guards: RV pinned to the registered 1-min
  definition (BUG-1), dvol index is mean-of-per-series-z not z-of-mean
  (BUG-2), silent all-NULL Binance-shaped field extraction WARNs and is
  visible in per-series finite-day counts (BUG-3), the dvol fallback
  refuses timestamp-like/oversized fields (BUG-4), the CLI fails non-zero
  on a zero-usable-dvol tree (BUG-5).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c10_pointer.cropper import (
    cropper_score,
    detect_pointer_days,
    trailing_median_detrend,
)
from bybit_edge.research.c10_pointer.driver import (
    DEFAULT_WINDOWS,
    run,
)
from bybit_edge.research.c10_pointer.loaders import (
    DataError,
    build_detection_panel,
    daily_grid,
    load_daily_rv,
    parse_dvol_value,
)
from bybit_edge.research.c10_pointer.stats import (
    benjamini_hochberg,
    delta_pre,
    dvol_index,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")

#: Registry-fixed daily grid (100 days, burn-in 21, W1 39 + W2 40 days).
DAYS = daily_grid("2026-03-27", "2026-07-04")
DAY_IDX = {d: i for i, d in enumerate(DAYS)}
N_SERIES = 30
NAMES = [f"series_{i:02d}" for i in range(N_SERIES)]


# ---------------------------------------------------------------------------
# (a) Cropper score + detrend + pointer-day arithmetic
# ---------------------------------------------------------------------------

def test_daily_grid_matches_registry_window_arithmetic() -> None:
    assert len(DAYS) == 100
    assert DAYS[21] == "2026-04-17"          # burn-in 21 => usable start
    assert DAY_IDX["2026-05-25"] - DAY_IDX["2026-04-17"] + 1 == 39  # W1
    assert DAY_IDX["2026-07-04"] - DAY_IDX["2026-05-26"] + 1 == 40  # W2


def test_trailing_median_detrend_min_periods() -> None:
    x = np.full(40, 5.0)
    resid = trailing_median_detrend(x, window=63, min_periods=21)
    assert np.isnan(resid[19])               # only 20 obs in trailing window
    assert resid[20] == 0.0                  # 21 obs -> defined, median 5
    assert np.all(resid[20:] == 0.0)


def test_trailing_median_detrend_subtracts_median() -> None:
    x = np.arange(30, dtype=np.float64)
    resid = trailing_median_detrend(x, window=63, min_periods=21)
    # at t=29 the trailing window is 0..29, median 14.5 -> resid 14.5
    assert resid[29] == pytest.approx(29.0 - 14.5)


def test_cropper_score_known_mini_example() -> None:
    # 21 zeros with a lone spike at t=10: the centred 11-day window at t=10
    # holds ten 0s + the spike s -> C = (s - s/11) / (s/sqrt(11)) = 10/sqrt(11),
    # INDEPENDENT of s. A neighbour inside the window gets -1/sqrt(11).
    resid = np.zeros(21)
    resid[10] = 2.2
    c = cropper_score(resid)
    assert c[10] == pytest.approx(10.0 / np.sqrt(11.0))
    assert c[9] == pytest.approx(-1.0 / np.sqrt(11.0))
    # constant window -> zero SD -> NaN
    flat = cropper_score(np.zeros(21))
    assert np.isnan(flat[10])


def test_pointer_day_thresholds_18_floor_and_60_percent_share() -> None:
    # 18 of 30 at +2.0 -> share exactly 0.60 -> pointer (boundary inclusive).
    row = np.zeros((1, 30))
    row[0, :18] = 2.0
    out = detect_pointer_days(row)
    assert bool(out.is_pointer[0]) is True
    assert out.direction[0] == 1
    # 17 of 30 -> share < 0.60 -> no pointer.
    row[0, 17] = 0.0
    assert bool(detect_pointer_days(row).is_pointer[0]) is False
    # 17 finite (all extreme, share 1.0) but n_avail < 18 -> no pointer.
    row2 = np.full((1, 30), np.nan)
    row2[0, :17] = -2.0
    out2 = detect_pointer_days(row2)
    assert int(out2.n_avail[0]) == 17
    assert bool(out2.is_pointer[0]) is False
    # negative direction
    row3 = np.zeros((1, 30))
    row3[0, :20] = -2.0
    out3 = detect_pointer_days(row3)
    assert bool(out3.is_pointer[0]) is True
    assert out3.direction[0] == -1


def test_benjamini_hochberg_own_copy() -> None:
    rejected, p_crit = benjamini_hochberg([0.01, 0.02, 0.9, 0.04], alpha=0.10)
    assert rejected == [True, True, False, True]
    assert p_crit == 0.04
    assert benjamini_hochberg([], 0.10) == ([], 0.0)


def test_delta_pre_windows_are_strictly_pre_event() -> None:
    # D = 0 everywhere, then 1.0 on days t-5..t-1 of t=50 only.
    D = np.zeros(100)
    D[45:50] = 1.0
    dp = delta_pre(D)
    assert dp[50] == pytest.approx(1.0)      # near mean 1, far mean 0
    assert np.isnan(dp[10])                  # t < 15 undefined
    assert dp[30] == pytest.approx(0.0)      # untouched day


# ---------------------------------------------------------------------------
# synthetic driver inputs
# ---------------------------------------------------------------------------

def _synthetic_inputs(
    anomaly_days: list[str],
    *,
    n_anom_series: int = 24,
    spike: float = 10.0,
    dvol_drift: float = 5.0,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """30 independent noise series + synchronised spikes + dvol pre-drift."""
    rng = np.random.default_rng(seed)
    t_full = len(DAYS)
    panel = rng.normal(0.0, 1.0, size=(t_full, N_SERIES))
    dvol_btc = 60.0 + rng.normal(0.0, 0.1, size=t_full)
    dvol_eth = 55.0 + rng.normal(0.0, 0.1, size=t_full)
    for d in anomaly_days:
        t = DAY_IDX[d]
        panel[t, :n_anom_series] += spike
        if dvol_drift:
            dvol_btc[t - 5: t] += dvol_drift
            dvol_eth[t - 5: t] += dvol_drift
    return panel, dvol_btc, dvol_eth


ANOM_W1 = ["2026-04-25", "2026-05-07", "2026-05-19"]
ANOM_W2 = ["2026-06-03", "2026-06-15", "2026-06-27"]


# ---------------------------------------------------------------------------
# (b) NULL control — independent series must NOT produce pointer days
# ---------------------------------------------------------------------------

def test_null_control_independent_series_not_significant() -> None:
    panel, btc, eth = _synthetic_inputs([], seed=11)
    payload = run(DAYS, NAMES, panel, btc, eth,
                  n_surrogates=150, n_permutations=150, seed=3)
    s1 = [c for c in payload["cells"] if c["stage"] == 1]
    assert len(s1) == 2
    for c in s1:
        # under independence P(pointer day) ~ 1e-15 -> zero pointer days
        assert c["n_pointer"] == 0
        assert c["surrogate_p"] > 0.05
        assert c["n_pointer_floor_met"] is False
        assert c["cell_pass"] is False
    assert payload["all_four_cells_pass"] is False


# ---------------------------------------------------------------------------
# (c) POSITIVE detection — synchronised anomalies + dvol pre-drift
# ---------------------------------------------------------------------------

def test_positive_detection_stage1_and_stage2_significant() -> None:
    panel, btc, eth = _synthetic_inputs(ANOM_W1 + ANOM_W2, seed=5)
    payload = run(DAYS, NAMES, panel, btc, eth,
                  n_surrogates=200, n_permutations=300, seed=42)
    s1 = [c for c in payload["cells"] if c["stage"] == 1]
    s2 = [c for c in payload["cells"] if c["stage"] == 2]
    for c, expected in zip(s1, (ANOM_W1, ANOM_W2)):
        assert c["n_pointer"] == len(expected)
        assert c["pointer_dates"] == expected
        assert all(d == 1 for d in c["pointer_directions"])
        assert c["surrogate_p"] <= 0.05
        assert c["n_pointer_floor_met"] is True
    for c in s2:
        assert c["n_pointer_used"] == 3
        assert c["s_mean_delta_pre"] > 0.0     # positive pre-event drift
        assert c["permutation_p_two_sided"] <= 0.05
    # BH-FDR over the 4-cell F-POINTER family keeps all four significant.
    assert payload["n_fdr_significant"] == 4
    assert all(c["cell_pass"] for c in payload["cells"])
    assert payload["all_four_cells_pass"] is True
    assert payload["fdr_family"] == "F-POINTER"
    # Registered non-judgment-bearing co-report is present (audit_h10 BUG-6).
    assert payload["neuwirth_crosscheck"]["judgment_bearing"] is False
    assert len(payload["neuwirth_crosscheck"]["windows"]) == 2


def test_positive_detection_is_seed_reproducible() -> None:
    panel, btc, eth = _synthetic_inputs(ANOM_W1 + ANOM_W2, seed=5)
    p1 = run(DAYS, NAMES, panel, btc, eth,
             n_surrogates=100, n_permutations=100, seed=42)
    p2 = run(DAYS, NAMES, panel, btc, eth,
             n_surrogates=100, n_permutations=100, seed=42)
    for a, b in zip(p1["cells"], p2["cells"]):
        pa = a["surrogate_p"] if a["stage"] == 1 else a["permutation_p_two_sided"]
        pb = b["surrogate_p"] if b["stage"] == 1 else b["permutation_p_two_sided"]
        assert pa == pb


# ---------------------------------------------------------------------------
# (d) N-floor path — 2 pointer days per window => hard power-DROP path
# ---------------------------------------------------------------------------

def test_n_floor_two_pointer_days_never_passes() -> None:
    panel, btc, eth = _synthetic_inputs(ANOM_W1[:2] + ANOM_W2[:2], seed=9)
    payload = run(DAYS, NAMES, panel, btc, eth,
                  n_surrogates=100, n_permutations=100, seed=1)
    s1 = [c for c in payload["cells"] if c["stage"] == 1]
    for c in s1:
        assert c["n_pointer"] == 2
        assert c["n_pointer_floor"] == 3          # floor NOT lowerable
        assert c["n_pointer_floor_met"] is False
        assert c["cell_pass"] is False            # even if p is tiny
    assert payload["gate_thresholds"]["n_pointer_floor"] == 3
    assert payload["gate_thresholds"]["n_pointer_floor_lowerable"] is False
    assert payload["all_four_cells_pass"] is False


# ---------------------------------------------------------------------------
# (e) capital_free + forbidden-token scan
# ---------------------------------------------------------------------------

def test_capital_free_and_no_forbidden_tokens() -> None:
    panel, btc, eth = _synthetic_inputs(ANOM_W1 + ANOM_W2, seed=5)
    payload = run(DAYS, NAMES, panel, btc, eth,
                  n_surrogates=50, n_permutations=50, seed=2,
                  source="data/harvest/raw (synthetic)")
    assert payload["capital_free"] is True
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction", "slippage", "edge"):
        assert tok not in blob, f"forbidden capital token in payload: {tok!r}"
    # dvol hold-out is declared and NOT among the detection series
    assert "dvol" in payload["holdout_target"]
    assert all("dvol" not in n for n in payload["detection_series"])
    assert payload["n_detection_series"] == 30


def test_run_rejects_window_inside_burn_in() -> None:
    panel, btc, eth = _synthetic_inputs([], seed=11)
    with pytest.raises(ValueError):
        run(DAYS, NAMES, panel, btc, eth,
            windows=(("W1", "2026-04-01", "2026-05-25"), DEFAULT_WINDOWS[1]),
            n_surrogates=10, n_permutations=10)


# ---------------------------------------------------------------------------
# dvol payload parsing (unknown-generic structure) — audit_h10 BUG-4
# ---------------------------------------------------------------------------

def test_parse_dvol_value_candidates_and_fallback(capsys) -> None:
    assert parse_dvol_value(json.dumps({"dvol": "55.5"})) == 55.5
    assert parse_dvol_value(json.dumps({"value": 48.25})) == 48.25
    assert parse_dvol_value(json.dumps({"index_value": "61.0"})) == 61.0
    # "volatility"/"mark_iv" were promoted to real candidates (BUG-4 fix) —
    # they must match as candidates, NOT trigger the fallback WARN path.
    warn_state_cand: dict = {}
    v_cand = parse_dvol_value(json.dumps({"volatility": "44.5", "sym": "BTC"}),
                              warn_state=warn_state_cand, symbol="BTC")
    assert v_cand == 44.5
    assert warn_state_cand.get("mode") == "candidate:volatility"
    assert warn_state_cand.get("warned") is None
    assert parse_dvol_value(json.dumps({"mark_iv": "71.2"})) == 71.2

    # genuine fallback: a field name in NONE of the candidates.
    warn_state: dict = {}
    v = parse_dvol_value(json.dumps({"iv_level": "44.5", "sym": "BTC"}),
                         warn_state=warn_state, symbol="BTC")
    assert v == 44.5
    assert warn_state.get("warned") is True
    assert warn_state.get("mode") == "fallback:iv_level"
    err = capsys.readouterr().err
    assert "WARN dvol BTC" in err

    # nothing numeric -> NaN; malformed -> NaN
    assert np.isnan(parse_dvol_value(json.dumps({"sym": "BTC"})))
    assert np.isnan(parse_dvol_value("not json"))


def test_parse_dvol_value_fallback_skips_timestamp_like_keys(capsys) -> None:
    # A leading epoch-ms timestamp field must NEVER be silently mistaken for
    # the dvol value (audit_h10 BUG-4's core scenario): "ts" matches the
    # skip regex, so the parser must continue to the next plausible field.
    warn_state: dict = {}
    v = parse_dvol_value(json.dumps({"ts": 1_750_000_000_000, "level": 42.5}),
                         warn_state=warn_state, symbol="BTC")
    assert v == 42.5
    assert warn_state.get("mode") == "fallback:level"

    # If the ONLY numeric field is timestamp-like, there is nothing safe to
    # fall back to -> NaN, never a fabricated "dvol" reading.
    assert np.isnan(parse_dvol_value(json.dumps({"timestamp": 1_750_000_000_000})))
    assert np.isnan(parse_dvol_value(json.dumps({"seq_id": 42, "date_str": "x"})))


def test_parse_dvol_value_fallback_rejects_oversized_values() -> None:
    # dvol is a percent-scale index; a fallback value > 1e6 (e.g. an epoch-ms
    # timestamp hiding under a non-timestamp-looking key) must be rejected.
    assert np.isnan(parse_dvol_value(json.dumps({"weird_field": 1_750_000_000_000})))
    # a plausible value under the same non-candidate key IS accepted.
    v = parse_dvol_value(json.dumps({"weird_field": 55.5}))
    assert v == 55.5


# ---------------------------------------------------------------------------
# dvol index — audit_h10 BUG-2 (mean-of-z, not z-of-mean; day-close input)
# ---------------------------------------------------------------------------

def test_dvol_index_is_mean_of_per_series_z_scores() -> None:
    # Deliberately different scale AND different day-to-day pattern so
    # mean(z) and z(mean) are NOT trivially equal via a shared affine
    # relationship (a perfectly correlated pair would make them coincide).
    btc = np.array([60.0, 80.0, 60.0, 80.0])
    eth = np.array([500.0, 500.0, 600.0, 600.0])
    D = dvol_index(btc, eth)
    z_btc = (btc - btc.mean()) / btc.std(ddof=1)
    z_eth = (eth - eth.mean()) / eth.std(ddof=1)
    expected = (z_btc + z_eth) / 2.0
    assert np.allclose(D, expected)
    # NOT equivalent to z(mean(levels)) when scales differ (audit_h10 BUG-2b).
    m = (btc + eth) / 2.0
    z_of_mean = (m - m.mean()) / m.std(ddof=1)
    assert not np.allclose(D, z_of_mean)


def test_dvol_index_z_uses_usable_period_parameters_only() -> None:
    # Two burn-in days carry extreme values; the usable_mask must exclude
    # them from the z-fit (hardened spec: "ueber den nutzbaren Zeitraum",
    # DEC-21) while D itself stays DEFINED on those burn-in days too (the
    # driver's Delta_pre look-back can reach into the burn-in).
    btc = np.array([9000.0, 9000.0, 60.0, 62.0, 64.0, 66.0])
    eth = np.array([8000.0, 8000.0, 50.0, 52.0, 54.0, 56.0])
    usable = np.array([False, False, True, True, True, True])
    D = dvol_index(btc, eth, usable)
    assert np.all(np.isfinite(D))
    mu_b, sd_b = btc[2:].mean(), btc[2:].std(ddof=1)
    mu_e, sd_e = eth[2:].mean(), eth[2:].std(ddof=1)
    expected_usable = (((btc[2:] - mu_b) / sd_b) + ((eth[2:] - mu_e) / sd_e)) / 2.0
    assert np.allclose(D[2:], expected_usable)
    # burn-in days use the SAME usable-period mu/sd -> huge out-of-sample z.
    assert D[0] > 100.0


# ---------------------------------------------------------------------------
# harvester-tree helpers (shared by RV-pin, BUG-3 and end-to-end tests)
# ---------------------------------------------------------------------------

def _write_parquet(dirpath: Path, rows: list[tuple[int, str]]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    dirpath.mkdir(parents=True, exist_ok=True)
    table = pa.table({
        "ts_exchange_ms": pa.array([r[0] for r in rows], pa.int64()),
        "payload_json": pa.array([r[1] for r in rows], pa.string()),
    })
    pq.write_table(table, dirpath / "data.parquet")


def _midnight_ms(date_str: str) -> int:
    y, m, d = (int(x) for x in date_str.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


_MINUTE_MS = 60_000


def _minute_trade_rows(t0: int, price0: float, rng: np.random.Generator,
                       *, n_bars: int = 48, spacing_min: int = 30) -> tuple[list[tuple[int, str]], float]:
    """``n_bars`` trades on DISTINCT 1-min buckets across one UTC day.

    Spaced ``spacing_min`` minutes apart (default 48 bars/day, one every 30
    minutes) so ``load_daily_rv``'s ``max_by(price, ts)`` 60-s bucketing sees
    genuinely distinct 1-min bars (audit_h10 BUG-1 regression guard — the
    pre-fix fixture wrote only 2 trades/day, which hid the daily-bar-vs-1-min
    definition bug entirely). Returns ``(rows, last_price)``.
    """
    rows: list[tuple[int, str]] = []
    px = price0
    for k in range(n_bars):
        px *= float(1.0 + rng.normal(0.0, 0.003))
        ts = t0 + k * spacing_min * _MINUTE_MS + 7_000  # +7s: mid-bucket, unambiguous
        rows.append((ts, json.dumps({"price": f"{px:.4f}"})))
    return rows, px


# ---------------------------------------------------------------------------
# (g1) RV pinned to the registered 1-min definition — audit_h10 BUG-1
# ---------------------------------------------------------------------------

def test_load_daily_rv_matches_registered_1_minute_definition(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    day = "2026-01-01"
    t0 = _midnight_ms(day)
    # 6 trades on 6 DISTINCT 1-min buckets with known prices -> hand-computed
    # rv = log(sum((delta log p)^2)) over the 5 within-day returns.
    prices = [100.0, 101.0, 99.0, 102.0, 101.5, 103.0]
    rows = [(t0 + k * _MINUTE_MS, json.dumps({"price": f"{px:.4f}"}))
            for k, px in enumerate(prices)]
    _write_parquet(base / "raw" / "bybit" / "publicTrade" / "symbol=BTCUSDT" / f"date={day}", rows)

    rv = load_daily_rv(base, "bybit", "BTCUSDT", [day], min_bars_per_day=6)
    log_p = np.log(np.array(prices))
    rets = np.diff(log_p)
    expected = np.log(float(np.sum(rets * rets)))
    assert rv[0] == pytest.approx(expected)

    # This is the REGISTERED definition, not the pre-fix daily-bar shortcut:
    # the pre-fix code would have given (log(103.0) - log(100.0))**2 with NO
    # outer log, a completely different number.
    daily_bar_shortcut = (np.log(103.0) - np.log(100.0)) ** 2
    assert rv[0] != pytest.approx(daily_bar_shortcut)

    # Below an explicit min_bars_per_day floor -> NaN, never a crash.
    assert np.isnan(load_daily_rv(base, "bybit", "BTCUSDT", [day], min_bars_per_day=7)[0])
    # The DEFAULT registry-adjacent floor (RV_MIN_BARS_PER_DAY=30) is far
    # above these 6 bars -> NaN with defaults (documents why the old 2-
    # trades/day test fixture could never have caught BUG-1).
    assert np.isnan(load_daily_rv(base, "bybit", "BTCUSDT", [day])[0])


def test_load_daily_rv_dense_day_is_finite_with_default_floor(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    day = "2026-01-01"
    t0 = _midnight_ms(day)
    rng = np.random.default_rng(1)
    rows, _ = _minute_trade_rows(t0, 100.0, rng, n_bars=48, spacing_min=30)
    _write_parquet(base / "raw" / "bybit" / "publicTrade" / "symbol=BTCUSDT" / f"date={day}", rows)
    rv = load_daily_rv(base, "bybit", "BTCUSDT", [day])
    assert np.isfinite(rv[0])


# ---------------------------------------------------------------------------
# (g2) Silent all-NULL Binance-shaped field extraction — audit_h10 BUG-3
# ---------------------------------------------------------------------------

def test_build_detection_panel_warns_on_silent_all_null_binance_fields(
    tmp_path: Path, capsys,
) -> None:
    base = tmp_path / "harvest"
    days = daily_grid("2026-01-01", "2026-01-03")
    rng = np.random.default_rng(2)
    # ETHUSDT: fully valid data (keeps n_loaded > 0 so the panel doesn't
    # raise DataError outright — this test is about the SILENT case).
    for d in days:
        t0 = _midnight_ms(d)
        rows, _ = _minute_trade_rows(t0, 2000.0, rng, n_bars=32, spacing_min=40)
        _write_parquet(base / "raw" / "binance" / "publicTrade" / "symbol=ETHUSDT" / f"date={d}", rows)
        _write_parquet(
            base / "raw" / "binance" / "rest.fundingRate" / "symbol=ETHUSDT" / f"date={d}",
            [(t0, json.dumps({"fundingRate": "0.0001"}))],
        )
        _write_parquet(
            base / "raw" / "binance" / "rest.openInterest" / "symbol=ETHUSDT" / f"date={d}",
            [(t0, json.dumps({"openInterest": "12345.0"}))],
        )
        # BTCUSDT: rest.fundingRate / rest.openInterest PARTITIONS EXIST but
        # use field names matching NONE of the COALESCE candidates (DATASET.md
        # §6 field-name-guess-is-wrong scenario) -> must WARN, not stay silent.
        _write_parquet(
            base / "raw" / "binance" / "rest.fundingRate" / "symbol=BTCUSDT" / f"date={d}",
            [(t0, json.dumps({"symbol": "BTCUSDT", "totallyWrongFundingField": "0.0001"}))],
        )
        _write_parquet(
            base / "raw" / "binance" / "rest.openInterest" / "symbol=BTCUSDT" / f"date={d}",
            [(t0, json.dumps({"symbol": "BTCUSDT", "totallyWrongOiField": "12345.0"}))],
        )

    names, panel = build_detection_panel(
        base, days, symbols=("BTCUSDT", "ETHUSDT"), exchanges=("binance",),
    )
    err = capsys.readouterr().err
    assert "binance:BTCUSDT:funding partitions exist but parse to 0 finite days" in err
    assert "binance:BTCUSDT:dlog_oi partitions exist but parse to 0 finite days" in err

    funding_idx = names.index("binance:BTCUSDT:funding")
    oi_idx = names.index("binance:BTCUSDT:dlog_oi")
    eth_funding_idx = names.index("binance:ETHUSDT:funding")
    assert int(np.isfinite(panel[:, funding_idx]).sum()) == 0
    assert int(np.isfinite(panel[:, oi_idx]).sum()) == 0
    # the sibling symbol with correct field names is NOT affected.
    assert int(np.isfinite(panel[:, eth_funding_idx]).sum()) > 0


def test_build_detection_panel_all_series_missing_raises(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    days = daily_grid("2026-01-01", "2026-01-02")
    with pytest.raises(DataError):
        build_detection_panel(base, days, symbols=("BTCUSDT",), exchanges=("bybit",))


# ---------------------------------------------------------------------------
# (f) End-to-end: synthetic harvester Hive tree (all 4 stream forms) + CLI
# ---------------------------------------------------------------------------

def _build_synthetic_tree(base: Path) -> None:
    """All 4 stream forms for the full registry grid (small but complete).

    publicTrade is DENSE (48 distinct 1-min bars/day per symbol/exchange) so
    the registered 1-min RV definition actually produces finite values
    end-to-end (audit_h10 BUG-1 regression guard — a 2-trades/day fixture
    would leave all 10 RV series structurally NaN under the corrected loader).
    """
    rng = np.random.default_rng(123)
    prices = {(ex, s): 100.0 * (1 + i) for ex in ("bybit", "binance")
              for i, s in enumerate(SYMBOLS)}
    oi = {(ex, s): 5_000.0 * (1 + i) for ex in ("bybit", "binance")
          for i, s in enumerate(SYMBOLS)}
    dvol = {"BTC": 60.0, "ETH": 55.0}
    for d in DAYS:
        t0 = _midnight_ms(d)
        for ex in ("bybit", "binance"):
            for sym in SYMBOLS:
                rows, last_px = _minute_trade_rows(t0, prices[(ex, sym)], rng)
                prices[(ex, sym)] = last_px
                _write_parquet(
                    base / "raw" / ex / "publicTrade" / f"symbol={sym}" / f"date={d}", rows,
                )
                # rest.fundingRate: 3 snapshots per day, field fundingRate
                rates = 0.0001 + rng.normal(0.0, 0.00005, size=3)
                _write_parquet(
                    base / "raw" / ex / "rest.fundingRate" / f"symbol={sym}" / f"date={d}",
                    [(t0 + (k + 1) * 8 * 3_600_000,
                      json.dumps({"symbol": sym, "fundingRate": f"{rates[k]:.8f}"}))
                     for k in range(3)],
                )
                # rest.openInterest: 2 snapshots per day, field openInterest
                oi[(ex, sym)] *= float(1.0 + rng.normal(0.0, 0.01))
                _write_parquet(
                    base / "raw" / ex / "rest.openInterest" / f"symbol={sym}" / f"date={d}",
                    [(t0 + 6 * 3_600_000,
                      json.dumps({"symbol": sym,
                                  "openInterest": f"{oi[(ex, sym)] * 0.99:.4f}"})),
                     (t0 + 18 * 3_600_000,
                      json.dumps({"symbol": sym,
                                  "openInterest": f"{oi[(ex, sym)]:.4f}"}))],
                )
        # deribit dvol hold-out (symbols BTC/ETH, NOT BTCUSDT); exercise two
        # different candidate field names of the unknown-generic payload.
        for cur, field in (("BTC", "dvol"), ("ETH", "value")):
            dvol[cur] *= float(1.0 + rng.normal(0.0, 0.01))
            _write_parquet(
                base / "raw" / "deribit" / "dvol" / f"symbol={cur}" / f"date={d}",
                [(t0 + 12 * 3_600_000,
                  json.dumps({field: f"{dvol[cur]:.4f}", "currency": cur}))],
            )


def test_end_to_end_cli_produces_valid_json(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _build_synthetic_tree(base)

    out_dir = tmp_path / "out"
    script = REPO_ROOT / "scripts" / "c10_pointer.py"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script),
         "--base-dir", str(base), "--out-dir", str(out_dir),
         "--n-surrogates", "100", "--n-permutations", "100", "--seed", "1"],
        capture_output=True, text=True, env=env, timeout=560,
    )
    assert proc.returncode == 0, f"CLI failed:\nSTDOUT{proc.stdout}\nSTDERR{proc.stderr}"
    json_path = out_dir / "c10_pointer_results.json"
    md_path = out_dir / "c10_pointer_results.md"
    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["capital_free"] is True
    assert payload["hypothesis"] == "H-10"
    assert payload["n_detection_series"] == 30
    assert len(payload["cells"]) == 4                 # 2 stages x 2 windows
    assert payload["fdr_family"] == "F-POINTER"
    assert payload["usable_start"] == "2026-04-17"
    assert [w["label"] for w in payload["windows"]] == ["W1", "W2"]
    # gate-neutral: the payload carries flags, never a verdict field
    assert "verdict" not in payload
    # no forbidden capital token end-to-end
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction"):
        assert tok not in blob
    # markdown report is gate-neutral German with the F-POINTER cell table
    md = md_path.read_text(encoding="utf-8")
    assert "F-POINTER" in md
    assert "gate-auditor" in md

    # audit_h10 fix regression guards on the real end-to-end payload:
    # RV series are finite now that publicTrade is dense (BUG-1).
    rv_names = [n for n in payload["detection_series"] if n.endswith(":rv")]
    assert len(rv_names) == 10
    finite_days = payload["detection_series_finite_days"]
    assert all(finite_days[n] > 0 for n in rv_names)
    assert payload["n_detection_series_nonempty"] == 30
    # dvol parse mode + coverage are surfaced (BUG-2/3/4 audit trail).
    assert payload["dvol_parse_mode"]["BTC"] == "candidate:dvol"
    assert payload["dvol_parse_mode"]["ETH"] == "candidate:value"
    assert payload["holdout_finite_days"]["dvol_btc"] == 100
    assert payload["holdout_finite_days"]["dvol_eth"] == 100
    # Neuwirth co-report present and explicitly non-judgment-bearing (BUG-6).
    assert payload["neuwirth_crosscheck"]["judgment_bearing"] is False
    assert "Neuwirth" in md


# ---------------------------------------------------------------------------
# (g3) CLI fails on a zero-usable-dvol tree — audit_h10 BUG-5
# ---------------------------------------------------------------------------

def test_cli_fails_on_zero_usable_dvol(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    _build_synthetic_tree(base)
    # Overwrite EVERY deribit dvol partition with a payload whose only
    # numeric field is timestamp-like -> parse_dvol_value must refuse it
    # (BUG-4), leaving BTC+ETH dvol entirely NaN -> the CLI must FAIL (BUG-5)
    # instead of emitting a complete-looking DROP payload from unparseable
    # data.
    for d in DAYS:
        t0 = _midnight_ms(d)
        for cur in ("BTC", "ETH"):
            path = base / "raw" / "deribit" / "dvol" / f"symbol={cur}" / f"date={d}"
            shutil.rmtree(path, ignore_errors=True)
            _write_parquet(path, [(t0 + 12 * 3_600_000,
                                    json.dumps({"timestamp": t0 + 12 * 3_600_000}))])

    out_dir = tmp_path / "out"
    script = REPO_ROOT / "scripts" / "c10_pointer.py"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script),
         "--base-dir", str(base), "--out-dir", str(out_dir),
         "--n-surrogates", "20", "--n-permutations", "20", "--seed", "1"],
        capture_output=True, text=True, env=env, timeout=560,
    )
    assert proc.returncode != 0, (
        f"CLI must fail on zero-usable dvol, got rc=0:\n"
        f"STDOUT{proc.stdout}\nSTDERR{proc.stderr}"
    )
    assert "FATAL" in proc.stderr
    assert not (out_dir / "c10_pointer_results.json").exists()


def test_cli_fails_on_structurally_empty_detection_panel(tmp_path: Path) -> None:
    # Only 1 of the 30 registered series has any data at all (< n_avail
    # floor 18) -> structurally zero pointer days possible; the CLI must
    # FAIL rather than emit a meaningless complete-looking payload (BUG-5).
    base = tmp_path / "harvest"
    rng = np.random.default_rng(3)
    days3 = daily_grid("2026-01-01", "2026-01-03")
    for d in days3:
        t0 = _midnight_ms(d)
        rows, _ = _minute_trade_rows(t0, 100.0, rng, n_bars=32, spacing_min=40)
        _write_parquet(base / "raw" / "bybit" / "publicTrade" / "symbol=BTCUSDT" / f"date={d}", rows)
        _write_parquet(base / "raw" / "deribit" / "dvol" / "symbol=BTC" / f"date={d}",
                       [(t0, json.dumps({"dvol": "55.0"}))])
        _write_parquet(base / "raw" / "deribit" / "dvol" / "symbol=ETH" / f"date={d}",
                       [(t0, json.dumps({"dvol": "50.0"}))])

    out_dir = tmp_path / "out"
    script = REPO_ROOT / "scripts" / "c10_pointer.py"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script),
         "--base-dir", str(base), "--out-dir", str(out_dir),
         "--data-start", "2026-01-01", "--data-end", "2026-01-03",
         "--burn-in-days", "0",
         "--w1-start", "2026-01-01", "--w1-end", "2026-01-01",
         "--w2-start", "2026-01-02", "--w2-end", "2026-01-03",
         "--n-surrogates", "10", "--n-permutations", "10", "--seed", "1"],
        capture_output=True, text=True, env=env, timeout=120,
    )
    assert proc.returncode != 0, f"CLI must fail on an empty panel:\nSTDOUT{proc.stdout}\nSTDERR{proc.stderr}"
    assert "FATAL" in proc.stderr
