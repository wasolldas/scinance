"""Tests for the H-12 cross-exchange fragmentation-matrix mess-gate (c12_frag).

Covers:
- Spectrum correctness on a known synthetic case: a PURE one-factor day (one
  true common-market mode, no genuine second mode) -> v1 (market) close to
  the fully delocalized reference IPR=1/N=1/6; v2 (largest of the
  near-degenerate residual eigenvectors) clearly stays BELOW the localised
  regime the registered gate criterion b uses (IPR>=0.40) — it is somewhat
  elevated above the naive 1/N reference by a well-known RMT order-selection
  effect (picking the LARGEST of several near-equal residual eigenvalues
  biases its eigenvector towards more concentration than a "typical" random
  direction), which is exactly why the registry demands a full MC null
  rather than a flat 1/N reference for criterion b.
- nulls.one_factor_null_day calibration plausibility: the simulated null
  distribution of lambda2 sits in a sensible band around the MP-bulk
  reference, always below the calibrating lambda1, with a finite,
  non-degenerate IPR(v2) null distribution.
- End-to-end NULL control via driver.run: synthetic 6-series panels
  generated from a PURE one-factor population correlation matrix (no
  genuine residual mode) -> gate criteria are NOT met (well under the 20%
  FDR-significant-day floor) in both windows.
- End-to-end POSITIVE detection via driver.run: synthetic panels with a
  common market factor (v1, delocalized) PLUS a localised residual factor on
  exactly 2 of the 6 series (one exchange) with elevated correlation -> all
  three registered gate criteria (a/b/c) are met in both windows, the
  validity precondition holds, and weiter_indication is True.
- Validity precondition: too few valid days per window -> validity_status
  "ungueltig" (INVALID), NOT a DROP/criteria verdict.
- capital_free=true and no bps/pnl/sharpe/friction/edge_ token anywhere in
  the JSON payload.
- End-to-end over the full CLI (scripts/c12_frag.py): a synthetic 3-exchange
  x 2-symbol harvester Hive tree (publicTrade backfill payload_json form,
  panel.py's own price-only loader) -> rc=0, valid JSON.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c12_frag.driver import run
from bybit_edge.research.c12_frag.nulls import (
    mp_bulk,
    one_factor_null_day,
)
from bybit_edge.research.c12_frag.panel import DayPanel, WindowDays
from bybit_edge.research.c12_frag.spectrum import analyze_day

REPO_ROOT = Path(__file__).resolve().parents[2]

SERIES_LABELS = (
    "bybit:BTCUSDT", "bybit:ETHUSDT",
    "binance:BTCUSDT", "binance:ETHUSDT",
    "deribit:BTC-PERPETUAL", "deribit:ETH-PERPETUAL",
)
SERIES_EXCHANGES = ("bybit", "bybit", "binance", "binance", "deribit", "deribit")
N_SERIES = 6


# ---------------------------------------------------------------------------
# Synthetic-panel helpers (population-correlation-matrix Cholesky method)
# ---------------------------------------------------------------------------

def _date_range(start: str, n: int) -> list[str]:
    y, m, d = (int(x) for x in start.split("-"))
    d0 = date(y, m, d)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


def _one_factor_chol(lambda1: float) -> np.ndarray:
    """Cholesky factor of a pure one-factor correlation matrix (market only).

    v1 = ones/sqrt(N) (fully delocalized). No second mode.
    """
    v1 = np.ones(N_SERIES) / np.sqrt(N_SERIES)
    c = np.eye(N_SERIES) + (lambda1 - 1.0) * np.outer(v1, v1)
    return np.linalg.cholesky(c)


def _two_factor_chol(lambda1: float, lambda2: float) -> np.ndarray:
    """Cholesky factor of a two-mode correlation matrix: market + one
    exchange-localised residual mode on series 0,1 (both "bybit").

    v1 = (1,-1,1,1,1,1)/sqrt(6): fully delocalized (IPR=1/6), orthogonal to
    v2 by construction. v2 = (1,1,0,0,0,0)/sqrt(2): localised on series 0+1
    (both bybit) -> IPR=0.5, exchange load 100% bybit.
    """
    v1 = np.array([1.0, -1.0, 1.0, 1.0, 1.0, 1.0])
    v1 /= np.linalg.norm(v1)
    v2 = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0])
    v2 /= np.linalg.norm(v2)
    assert abs(float(v1 @ v2)) < 1e-12
    c = (np.eye(N_SERIES)
         + (lambda1 - 1.0) * np.outer(v1, v1)
         + (lambda2 - 1.0) * np.outer(v2, v2))
    return np.linalg.cholesky(c)


def _make_day_prices(rng: np.random.Generator, chol: np.ndarray, t_minutes: int) -> np.ndarray:
    """(t_minutes+1, N) minute last-price panel whose log-return correlation
    structure matches the population matrix behind ``chol`` in expectation."""
    z = rng.standard_normal((t_minutes, N_SERIES))
    ret = z @ chol.T
    logp = np.vstack([np.zeros((1, N_SERIES)), np.cumsum(ret, axis=0)])
    return 100.0 * np.exp(logp)


def _build_window(
    rng: np.random.Generator, chol: np.ndarray, n_days: int, t_minutes: int,
    label: str, start_date: str,
) -> WindowDays:
    dates = _date_range(start_date, n_days)
    days = [
        DayPanel(
            date=d,
            minute_prices=_make_day_prices(rng, chol, t_minutes),
            valid_minutes=np.full(N_SERIES, t_minutes + 1, dtype=np.int64),
            valid=True,
        )
        for d in dates
    ]
    return WindowDays(
        label=label, start_date=dates[0], end_date=dates[-1],
        series_labels=SERIES_LABELS, series_exchanges=SERIES_EXCHANGES, days=days,
    )


# ---------------------------------------------------------------------------
# (a) spectrum correctness — known one-factor synthetic case
# ---------------------------------------------------------------------------

def test_spectrum_pure_one_factor_v2_not_localized() -> None:
    chol = _one_factor_chol(lambda1=3.0)
    rng = np.random.default_rng(11)
    ipr1s: list[float] = []
    ipr2s: list[float] = []
    for _ in range(30):
        px = _make_day_prices(rng, chol, t_minutes=500)
        spec = analyze_day(px, SERIES_EXCHANGES)
        assert spec is not None
        ipr1s.append(spec.ipr_v1)
        ipr2s.append(spec.ipr_v2)
    # v1 = market mode: close to the fully delocalized reference 1/N = 1/6.
    assert abs(float(np.median(ipr1s)) - 1.0 / N_SERIES) < 0.03
    # v2 = residual mode: clearly below the localized-gate threshold (0.40)
    # used by criterion b, and clearly above 0 (a real, non-degenerate
    # measurement) — "not localized" in the sense the registry gate uses,
    # even though selection bias keeps it somewhat above the naive 1/6.
    med_ipr2 = float(np.median(ipr2s))
    assert 0.15 < med_ipr2 < 0.40


# ---------------------------------------------------------------------------
# (b) nulls.one_factor_null_day calibration plausibility
# ---------------------------------------------------------------------------

def test_one_factor_null_day_calibration_plausible() -> None:
    n = N_SERIES
    v1 = np.ones(n) / np.sqrt(n)
    lambda1 = 2.2
    t_obs = 1400
    l2_sims, ipr2_sims = one_factor_null_day(
        lambda1, v1, t_obs, n_reps=500, seed=123
    )
    assert l2_sims.shape == (500,)
    assert ipr2_sims.shape == (500,)
    assert np.all(np.isfinite(l2_sims)) and np.all(np.isfinite(ipr2_sims))
    # lambda2 (residual mode) always strictly below the calibrating lambda1.
    assert np.all(l2_sims > 0.0)
    assert np.all(l2_sims < lambda1)
    # sensible center: the null median sits in a broad, sane band around the
    # MP-bulk reference for the residual (n-1)-dim subspace — not an exact
    # theory match (finite N=6 asymptotics are registered as unreliable,
    # hence MC), just a plausibility/no-nonsense-shape check.
    lo, hi = mp_bulk(t_obs / (n - 1))
    med = float(np.median(l2_sims))
    assert 0.5 * hi < med < 1.5 * hi
    # IPR(v2) null values stay within the valid [1/n, 1] range and are not
    # systematically pinned at the fully localized extreme.
    assert np.all(ipr2_sims >= 1.0 / n - 1e-6)
    assert np.all(ipr2_sims <= 1.0 + 1e-6)
    assert np.median(ipr2_sims) < 0.5


# ---------------------------------------------------------------------------
# (c) End-to-end NULL control via driver.run
# ---------------------------------------------------------------------------

SIG_DAY_SHARE_MIN_TEST = 0.20  # mirrors driver.SIG_DAY_SHARE_MIN (a-criterion)


def test_driver_run_null_control_gate_not_met() -> None:
    chol = _one_factor_chol(lambda1=3.0)
    rng = np.random.default_rng(101)
    win_a = _build_window(rng, chol, n_days=40, t_minutes=300, label="W1",
                           start_date="2030-01-01")
    win_b = _build_window(rng, chol, n_days=40, t_minutes=300, label="W2",
                           start_date="2030-03-01")
    payload = run([win_a, win_b], n_mc=200, seed=42)
    assert payload["validity_status"] == "gueltig"
    assert payload["weiter_indication"] is False
    for w in payload["windows"]:
        assert w["criteria"]["a_sig_day_share"] < SIG_DAY_SHARE_MIN_TEST
        assert w["all_criteria_met"] is False


# ---------------------------------------------------------------------------
# (d) End-to-end POSITIVE detection via driver.run
# ---------------------------------------------------------------------------

def test_driver_run_positive_detection_all_criteria_met() -> None:
    chol = _two_factor_chol(lambda1=3.0, lambda2=2.0)
    rng = np.random.default_rng(3)
    win_a = _build_window(rng, chol, n_days=40, t_minutes=400, label="W1",
                           start_date="2030-01-01")
    win_b = _build_window(rng, chol, n_days=40, t_minutes=400, label="W2",
                           start_date="2030-03-01")
    payload = run([win_a, win_b], n_mc=200, seed=42)
    assert payload["validity_status"] == "gueltig"
    assert payload["all_windows_valid"] is True
    for w in payload["windows"]:
        c = w["criteria"]
        assert c["a_met"] is True
        assert c["b_met"] is True
        assert c["c_met"] is True
        assert c["c_dominant_exchange"] == "bybit"
        assert w["all_criteria_met"] is True
    assert payload["all_criteria_met_all_windows"] is True
    assert payload["weiter_indication"] is True


# ---------------------------------------------------------------------------
# (e) Validity precondition: too few valid days -> "ungueltig", NOT a DROP
# ---------------------------------------------------------------------------

def test_validity_precondition_too_few_days_is_invalid_not_drop() -> None:
    chol = _two_factor_chol(lambda1=3.0, lambda2=2.0)  # would otherwise pass
    rng = np.random.default_rng(5)
    # only 10 valid days per window, well under the 35-day floor.
    win_a = _build_window(rng, chol, n_days=10, t_minutes=300, label="W1",
                           start_date="2030-01-01")
    win_b = _build_window(rng, chol, n_days=10, t_minutes=300, label="W2",
                           start_date="2030-03-01")
    payload = run([win_a, win_b], n_mc=100, seed=42)
    assert payload["validity_status"] == "ungueltig"
    assert payload["all_windows_valid"] is False
    assert payload["weiter_indication"] is False
    for w in payload["windows"]:
        assert w["validity"]["min_days_ok"] is False
        assert w["validity"]["window_valid"] is False
        assert w["n_days_valid"] == 10
    # invalidity is its own status, distinct from (and not overridden by)
    # the gate-criteria fields — those are still reported (gate-neutral
    # payload), the gate-auditor is the one who must NOT read this as DROP.
    assert "validity_status" in payload
    assert payload["validity_status"] != "drop"


# ---------------------------------------------------------------------------
# (f) capital_free + no forbidden capital tokens anywhere in the payload
# ---------------------------------------------------------------------------

def test_capital_free_and_no_forbidden_tokens() -> None:
    chol = _two_factor_chol(lambda1=3.0, lambda2=2.0)
    rng = np.random.default_rng(3)
    win_a = _build_window(rng, chol, n_days=12, t_minutes=200, label="W1",
                           start_date="2030-01-01")
    win_b = _build_window(rng, chol, n_days=12, t_minutes=200, label="W2",
                           start_date="2030-03-01")
    payload = run([win_a, win_b], n_mc=80, seed=1)
    assert payload["capital_free"] is True
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction", "edge_"):
        assert tok not in blob, f"forbidden capital token in payload: {tok!r}"


def test_run_requires_two_windows() -> None:
    chol = _one_factor_chol(lambda1=2.0)
    rng = np.random.default_rng(1)
    win_a = _build_window(rng, chol, n_days=5, t_minutes=100, label="W1",
                           start_date="2030-01-01")
    with pytest.raises(ValueError):
        run([win_a], n_mc=50, seed=1)


# ---------------------------------------------------------------------------
# (g) End-to-end over the full CLI: synthetic harvester Hive tree
# ---------------------------------------------------------------------------

CLI_SYMBOLS = ("BTCUSDT", "ETHUSDT")
CLI_EXCHANGES = ("bybit", "binance", "deribit")


def _storage_symbol(exchange: str, symbol: str) -> str:
    if exchange == "deribit":
        return {"BTCUSDT": "BTC-PERPETUAL", "ETHUSDT": "ETH-PERPETUAL"}[symbol]
    return symbol


def _midnight_ms(date_str: str) -> int:
    from datetime import datetime, timezone
    y, m, d = (int(x) for x in date_str.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def _write_raw_backfill(tmp: Path, exchange: str, storage_symbol: str,
                         date_str: str, rows: list[tuple[int, float]]) -> None:
    """Write a synthetic raw-form parquet: ts_exchange_ms + payload_json.

    Backfill payload form (per panel.py docstring): the price-only loader
    reads COALESCE($.price, $.p) — use the Bybit/Deribit backfill key
    ``price`` here.
    """
    import duckdb

    d = tmp / "raw" / exchange / "publicTrade" / f"symbol={storage_symbol}" / f"date={date_str}"
    d.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        recs = []
        for ts, price in rows:
            payload = json.dumps({"side": "Buy", "price": f"{price:.4f}",
                                  "size": "0.10", "symbol": storage_symbol})
            recs.append((int(ts), payload))
        con.execute("CREATE TABLE t (ts_exchange_ms BIGINT, payload_json VARCHAR)")
        con.executemany("INSERT INTO t VALUES (?, ?)", recs)
        out = d / "data.parquet"
        con.execute(f"COPY t TO '{out.as_posix()}' (FORMAT parquet)")
    finally:
        con.close()


def _write_full_day(tmp: Path, exchange: str, symbol: str, date_str: str, seed: int) -> None:
    """One trade per minute for the whole UTC day (full 1440/1440 validity)."""
    rng = np.random.default_rng(seed)
    storage_symbol = _storage_symbol(exchange, symbol)
    start_ms = _midnight_ms(date_str)
    price = 100.0 + seed
    rows: list[tuple[int, float]] = []
    for minute in range(1440):
        price *= (1.0 + rng.normal(0.0, 0.001))
        ts = start_ms + minute * 60_000 + 1_000
        rows.append((ts, price))
    _write_raw_backfill(tmp, exchange, storage_symbol, date_str, rows)


def test_end_to_end_cli_produces_valid_json(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    win_a_dates = _date_range("2031-01-01", 2)
    win_b_dates = _date_range("2031-02-01", 2)
    for exi, exchange in enumerate(CLI_EXCHANGES):
        for si, symbol in enumerate(CLI_SYMBOLS):
            seed = 100 + exi * 10 + si
            for d in win_a_dates + win_b_dates:
                _write_full_day(base, exchange, symbol, d, seed=seed)

    out_dir = tmp_path / "out"
    script = REPO_ROOT / "scripts" / "c12_frag.py"
    import os
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script),
         "--base-dir", str(base), "--out-dir", str(out_dir),
         "--symbols", ",".join(CLI_SYMBOLS),
         "--exchanges", ",".join(CLI_EXCHANGES),
         "--window-a-start", win_a_dates[0], "--window-a-end", win_a_dates[-1],
         "--window-b-start", win_b_dates[0], "--window-b-end", win_b_dates[-1],
         "--n-mc", "50", "--seed", "1"],
        capture_output=True, text=True, env=env, timeout=300,
    )
    assert proc.returncode == 0, f"CLI failed:\nSTDOUT{proc.stdout}\nSTDERR{proc.stderr}"
    json_path = out_dir / "c12_frag_results.json"
    md_path = out_dir / "c12_frag_results.md"
    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["capital_free"] is True
    assert payload["hypothesis"] == "H-12"
    assert payload["n_windows"] == 2
    # only 2 days/window << the 35-day validity floor -> INVALID, but the
    # CLI must still complete cleanly and emit a well-formed payload.
    assert payload["validity_status"] == "ungueltig"
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction", "edge_"):
        assert tok not in blob
    assert "H-12" in md_path.read_text(encoding="utf-8")
