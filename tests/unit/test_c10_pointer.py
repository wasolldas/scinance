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
  CLI rc=0 and a valid gate-neutral payload.
"""
from __future__ import annotations

import json
import os
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
    daily_grid,
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
# dvol payload parsing (unknown-generic structure)
# ---------------------------------------------------------------------------

def test_parse_dvol_value_candidates_and_fallback(capsys) -> None:
    assert parse_dvol_value(json.dumps({"dvol": "55.5"})) == 55.5
    assert parse_dvol_value(json.dumps({"value": 48.25})) == 48.25
    assert parse_dvol_value(json.dumps({"index_value": "61.0"})) == 61.0
    # fallback: first numeric top-level field, with one-time WARN
    warn_state: dict = {}
    v = parse_dvol_value(json.dumps({"volatility": "44.5", "sym": "BTC"}),
                         warn_state=warn_state, symbol="BTC")
    assert v == 44.5
    assert warn_state.get("warned") is True
    err = capsys.readouterr().err
    assert "WARN dvol BTC" in err
    # nothing numeric -> NaN; malformed -> NaN
    assert np.isnan(parse_dvol_value(json.dumps({"sym": "BTC"})))
    assert np.isnan(parse_dvol_value("not json"))


def test_dvol_index_is_z_standardised_mean() -> None:
    btc = np.array([60.0, 62.0, 64.0, 66.0])
    eth = np.array([50.0, 52.0, 54.0, 56.0])
    D = dvol_index(btc, eth)
    m = (btc + eth) / 2.0
    expected = (m - m.mean()) / m.std(ddof=1)
    assert np.allclose(D, expected)


# ---------------------------------------------------------------------------
# (f) End-to-end: synthetic harvester Hive tree (all 4 stream forms) + CLI
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


def _build_synthetic_tree(base: Path) -> None:
    """All 4 stream forms for the full registry grid (small but complete)."""
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
                # publicTrade (backfill single-trade form): 2 trades per day
                prices[(ex, sym)] *= float(1.0 + rng.normal(0.0, 0.02))
                px = prices[(ex, sym)]
                _write_parquet(
                    base / "raw" / ex / "publicTrade" / f"symbol={sym}" / f"date={d}",
                    [(t0 + 3_600_000,
                      json.dumps({"side": "Buy", "price": f"{px * 0.999:.4f}",
                                  "size": "0.10", "symbol": sym})),
                     (t0 + 43_200_000,
                      json.dumps({"side": "Sell", "price": f"{px:.4f}",
                                  "size": "0.20", "symbol": sym}))],
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
