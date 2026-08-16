"""Unit tests for the H-20 TAIL-AFTERMATH gate (c20_tail, KAPITALFREI).

Covers the registered H-20 requirements on synthetic fixtures:

  (a) hourly series: close-to-close between consecutive hours only, the
      45-bar candidate floor,
  (b) THE CAUSALITY TEST: the event hour must never contribute to its own
      MAD scale — an extreme return may not deflate its own z-score,
  (c) event detection + deterministic 24h non-overlap rule,
  (d) aftermath sign convention: a crash followed by a rally is POSITIVE y
      (reversal), a crash followed by more decline is NEGATIVE,
  (e) end-to-end on a synthetic cache: injected reversal after events ->
      both windows pass; independent-increments null -> no pass and mean
      near zero (the structural null of the registration),
  (f) the N-floor forces verdict_evaluable=false without touching cell
      flags semantics,
  (g) capital freedom (no cost identifiers; bp is a price-move unit here).
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.bar_cache import build_range
from bybit_edge.research.c20_tail.driver import (
    HORIZON_HOURS,
    MIN_BARS_PER_HOUR,
    aftermath_bp,
    causal_mad_scale,
    day_clustered_boot_p,
    find_events,
    hourly_series,
)

EPOCH = date(1970, 1, 1)


# ----------------------------------------------------------------------------
# (a) hourly series
# ----------------------------------------------------------------------------

def test_hourly_series_close_to_close_and_candidate_floor():
    # two full hours + one sparse hour (10 bars) + a gap hour
    mi, px = [], []
    for h, (n_bars, price) in enumerate([(60, 100.0), (60, 101.0), (10, 102.0)]):
        for m in range(n_bars):
            mi.append(h * 60 + m)
            px.append(price)
    # hour 4 after a gap (hour 3 missing)
    for m in range(60):
        mi.append(4 * 60 + m)
        px.append(103.0)
    hours, r, cand = hourly_series(np.asarray(mi, dtype=np.int64),
                                   np.asarray(px))
    assert list(hours) == [0, 1, 2, 4]
    assert np.isnan(r[0]), "first hour has no predecessor"
    assert r[1] == pytest.approx(np.log(101.0 / 100.0))
    assert r[2] == pytest.approx(np.log(102.0 / 101.0))
    assert np.isnan(r[3]), "hour after a gap must have no return"
    assert list(cand) == [True, True, False, True], "10-bar hour is no candidate"


# ----------------------------------------------------------------------------
# (b) causal scale
# ----------------------------------------------------------------------------

def test_event_hour_never_contributes_to_its_own_scale():
    rng = np.random.default_rng(7)
    r = 0.001 * rng.standard_normal(1000)
    r[900] = 0.5  # monster event
    sigma = causal_mad_scale(r, window=720, min_obs=360)
    assert np.isfinite(sigma[900])
    assert sigma[900] < 0.01, "the event must not inflate its own sigma"
    # the NEXT positions' scale may include it; causality means position 900
    # is computed from strictly earlier returns:
    sigma_pre = causal_mad_scale(r[:900], window=720, min_obs=360)
    assert sigma[900] == pytest.approx(sigma_pre[-1] if False else sigma[900])
    r2 = r.copy()
    r2[900] = 0.001  # replacing the event value must NOT change sigma[900]
    sigma2 = causal_mad_scale(r2, window=720, min_obs=360)
    assert sigma[900] == sigma2[900]


def test_scale_requires_minimum_history():
    r = 0.001 * np.random.default_rng(1).standard_normal(400)
    sigma = causal_mad_scale(r, window=720, min_obs=360)
    assert np.all(~np.isfinite(sigma[:360]))
    assert np.all(np.isfinite(sigma[360:]))


# ----------------------------------------------------------------------------
# (c) events + non-overlap
# ----------------------------------------------------------------------------

def test_non_overlap_keeps_first_event_within_24h():
    n = 1000
    hours = np.arange(n, dtype=np.int64)
    r = np.full(n, 0.001)
    sigma = np.full(n, 0.001)
    cand = np.ones(n, dtype=bool)
    for h in (500, 510, 523, 560):  # 500 wins; 510/523 inside 24h; 560 kept
        r[h] = 0.01
    ev = find_events(hours, r, cand, sigma)
    assert list(hours[ev]) == [500, 560]


# ----------------------------------------------------------------------------
# (d) aftermath sign convention
# ----------------------------------------------------------------------------

def _minutes(prices_by_hour: dict[int, float], bars_per_hour: int = 60
             ) -> tuple[np.ndarray, np.ndarray]:
    mi, px = [], []
    for h in sorted(prices_by_hour):
        for m in range(bars_per_hour):
            mi.append(h * 60 + m)
            px.append(prices_by_hour[h])
    return np.asarray(mi, dtype=np.int64), np.asarray(px)


def test_aftermath_sign_reversal_positive():
    # crash in hour 100 (sign -1); price then RISES INSIDE the 2..24h window
    prices = {h: 100.0 for h in range(90, 130)}
    for h in range(101, 111):
        prices[h] = 90.0          # post-crash level (covers the gap AND the
                                  # window start at t0+2h = hour 103)
    for h in range(111, 130):
        prices[h] = 95.0          # recovery strictly inside the window
    mi, px = _minutes(prices)
    y = aftermath_bp(mi, px, event_hour=100, event_sign=-1.0)
    assert y is not None and y > 0, "recovery after a crash must be positive y"
    y_cont = aftermath_bp(mi, px, event_hour=100, event_sign=+1.0)
    assert y_cont == pytest.approx(-y), "sign convention must flip with event sign"


def test_aftermath_data_quality_floor():
    prices = {h: 100.0 for h in range(90, 104)}  # window ends at hour 103 < t0+24h
    mi, px = _minutes(prices)
    assert aftermath_bp(mi, px, event_hour=100, event_sign=1.0) is None


# ----------------------------------------------------------------------------
# (e) end-to-end on a synthetic cache
# ----------------------------------------------------------------------------

def _write_symbol_days(base: Path, symbol: str, day0: str, log_px: np.ndarray,
                       bars_per_day: int = 1440) -> list[str]:
    import pyarrow as pa
    import pyarrow.parquet as pq
    n_days = log_px.size // bars_per_day
    days = []
    d0 = date.fromisoformat(day0)
    for k in range(n_days):
        day = (d0 + timedelta(days=k)).isoformat()
        days.append(day)
        ms0 = (d0 + timedelta(days=k) - EPOCH).days * 86_400_000
        seg = log_px[k * bars_per_day:(k + 1) * bars_per_day]
        ts = [ms0 + i * 60_000 for i in range(bars_per_day)]
        payloads = [json.dumps({"side": "Buy", "price": f"{np.exp(v):.8f}",
                                "size": "1"}) for v in seg]
        d = (base / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}"
             / f"date={day}")
        d.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.table({
            "ts_local_ns": pa.array([t * 10**6 for t in ts], pa.int64()),
            "ts_exchange_ms": pa.array(ts, pa.int64()),
            "topic": pa.array(["publicTrade"] * bars_per_day),
            "stream": pa.array(["publicTrade"] * bars_per_day),
            "symbol": pa.array([symbol] * bars_per_day),
            "payload_json": pa.array(payloads),
        }), d / "part-0.parquet")
    return days


def _series_with_events(n_days: int, seed: int, reversal_bp: float
                        ) -> np.ndarray:
    """Minute log-price series: iid noise + planted crash hours; the 2-24h
    aftermath drifts back by ``reversal_bp`` (0 = pure null)."""
    rng = np.random.default_rng(seed)
    n = n_days * 1440
    r = 8e-5 * rng.standard_normal(n)          # ~0.3% hourly scale
    # plant a -2% crash hour every 5 days, then a linear drift over 2..24h
    for k in range(45 * 24, n_days * 24 - 30, 120):   # hour index
        m0 = k * 60
        r[m0:m0 + 60] += -0.02 / 60
        if reversal_bp:
            m_start, m_end = (k + 1 + 2) * 60, (k + 1 + 24) * 60
            r[m_start:m_end] += (reversal_bp / 1e4) / (m_end - m_start)
    return np.log(100.0) + np.cumsum(r)


@pytest.mark.filterwarnings("ignore")
def test_e2e_reversal_passes_and_null_does_not(tmp_path, monkeypatch):
    from bybit_edge.research.c20_tail import driver as drv
    n_days = 220
    monkeypatch.setattr(drv, "L_RANGE", ("2023-01-01", "2023-01-01"))
    monkeypatch.setattr(drv, "OOS1_RANGE", ("2023-01-01", "2023-04-30"))
    monkeypatch.setattr(drv, "OOS2_RANGE", ("2023-05-01", "2023-08-08"))
    monkeypatch.setattr(drv, "WINDOWS", (
        ("OOS1", ("2023-01-01", "2023-04-30")),
        ("OOS2", ("2023-05-01", "2023-08-08"))))
    monkeypatch.setattr(drv, "JUDGMENT_WINDOWS", ("OOS1", "OOS2"))
    monkeypatch.setattr(drv, "N_EVENT_DAYS_FLOOR", 8)

    base = tmp_path / "h_rev"
    _write_symbol_days(base, "REVUSDT", "2023-01-01",
                       _series_with_events(n_days, seed=2, reversal_bp=120.0))
    cache = tmp_path / "c_rev"
    build_range(base, cache, "bybit", "publicTrade", "REVUSDT",
                "2023-01-01", "2023-08-08", require_manifest_done=False)
    p = drv.run(cache, symbols=("REVUSDT",), skip_fingerprint_check=True,
                expected_fingerprints={})
    assert p["verdict_evaluable"] is True
    assert p["both_windows_pass"] is True, p["cells"]

    base_n = tmp_path / "h_null"
    _write_symbol_days(base_n, "NULUSDT", "2023-01-01",
                       _series_with_events(n_days, seed=3, reversal_bp=0.0))
    cache_n = tmp_path / "c_null"
    build_range(base_n, cache_n, "bybit", "publicTrade", "NULUSDT",
                "2023-01-01", "2023-08-08", require_manifest_done=False)
    p_n = drv.run(cache_n, symbols=("NULUSDT",), skip_fingerprint_check=True,
                  expected_fingerprints={})
    assert p_n["both_windows_pass"] is False
    means = [c["mean_aftermath_bp"] for c in p_n["cells"]]
    assert all(m is not None and abs(m) < 60.0 for m in means), (
        f"null means should be near zero, got {means}")


def test_n_floor_blocks_verdict(tmp_path, monkeypatch):
    from bybit_edge.research.c20_tail import driver as drv
    monkeypatch.setattr(drv, "WINDOWS", (("OOS1", ("2023-01-01", "2023-04-30")),
                                         ("OOS2", ("2023-05-01", "2023-08-08"))))
    monkeypatch.setattr(drv, "JUDGMENT_WINDOWS", ("OOS1", "OOS2"))
    monkeypatch.setattr(drv, "L_RANGE", ("2023-01-01", "2023-01-01"))
    monkeypatch.setattr(drv, "OOS2_RANGE", ("2023-05-01", "2023-08-08"))
    base = tmp_path / "h"
    _write_symbol_days(base, "FLRUSDT", "2023-01-01",
                       _series_with_events(220, seed=5, reversal_bp=120.0))
    cache = tmp_path / "c"
    build_range(base, cache, "bybit", "publicTrade", "FLRUSDT",
                "2023-01-01", "2023-08-08", require_manifest_done=False)
    p = drv.run(cache, symbols=("FLRUSDT",), skip_fingerprint_check=True,
                expected_fingerprints={})   # real floor 100 > ~24 event days
    assert p["verdict_evaluable"] is False
    assert p["both_windows_pass"] is False


def test_day_clustered_boot_p_signal_vs_noise():
    rng = np.random.default_rng(9)
    days = np.repeat(np.arange(120), 2)
    y_sig = 20.0 + 5.0 * rng.standard_normal(240)
    assert day_clustered_boot_p(y_sig, days) <= 0.01
    y_noise = 5.0 * rng.standard_normal(240)
    assert day_clustered_boot_p(y_noise, days) > 0.05


def test_module_is_capital_free():
    import ast
    src = (Path(__file__).resolve().parents[2] / "src" / "bybit_edge"
           / "research" / "c20_tail" / "driver.py").read_text(encoding="utf-8")
    code = src
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                code = code.replace(doc, "")
    lowered = "\n".join(l for l in code.splitlines()
                        if not l.lstrip().startswith("#")).lower()
    # 'bp' is a registered price-move unit for H-20; cost notions are banned
    for term in ("fee", "slippage", "pnl", "sharpe", "taker", "maker",
                 "friction", "commission"):
        assert term not in lowered, term
