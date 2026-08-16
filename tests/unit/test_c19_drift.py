"""Unit tests for the H-19 DRIFT measurement (c19_drift, KAPITALFREI).

Covers the registered H-19 requirements on synthetic bar-cache fixtures:

  (a) descriptor correctness: D1 on a constructed alternating-return day
      (strongly negative AC), D2 on a random-walk day (VR ~ 1) vs. a
      bounce day (VR < 1), D3 on uniform vs. concentrated volume,
  (b) THE KEY CONDITIONING TEST: a descriptor that trends ONLY because the
      vol level trends must show |partial rho| ~ 0 while the RAW rho is
      large — otherwise the "conditioned on vol/activity" clause is empty,
  (c) positive detection: an injected calendar drift in D1 survives the
      conditioning and clears the 0.30 threshold in both windows,
  (d) null behaviour: a stationary panel stays far below the threshold and
      the rotation-null p is non-significant,
  (e) fingerprint discipline: a cache whose fingerprint does not match the
      registered constant yields gate_valid=false,
  (f) capital_free flag and no cost identifiers in the module.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.bar_cache import build_range
from bybit_edge.research.c19_drift.driver import (
    DESCRIPTORS,
    RHO_MIN,
    build_daily_panel,
    day_descriptors,
    partial_spearman,
    rotation_null_p,
    run,
)

EPOCH = date(1970, 1, 1)


# ----------------------------------------------------------------------------
# synthetic cache fixture: write raw partitions, build via the real cache
# ----------------------------------------------------------------------------

def _write_raw_day(base: Path, symbol: str, day_iso: str,
                   prices: np.ndarray, vols: np.ndarray) -> None:
    """One flat trade per minute at minute start (deterministic fixture)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    ms0 = (date.fromisoformat(day_iso) - EPOCH).days * 86_400_000
    n = prices.size
    ts = [ms0 + i * 60_000 for i in range(n)]
    payloads = [json.dumps({"side": "Buy" if i % 2 == 0 else "Sell",
                            "price": f"{prices[i]:.8f}",
                            "size": f"{vols[i]:.8f}"}) for i in range(n)]
    d = base / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}" / f"date={day_iso}"
    d.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({
        "ts_local_ns": pa.array([t * 1_000_000 for t in ts], pa.int64()),
        "ts_exchange_ms": pa.array(ts, pa.int64()),
        "topic": pa.array(["publicTrade"] * n), "stream": pa.array(["publicTrade"] * n),
        "symbol": pa.array([symbol] * n), "payload_json": pa.array(payloads),
    }), d / "part-0.parquet")


def _build_cache(tmp_path: Path, symbol: str, days: list[str],
                 price_fn, vol_fn) -> Path:
    base, cache = tmp_path / "h", tmp_path / "c"
    for i, day in enumerate(days):
        _write_raw_day(base, symbol, day, price_fn(i), vol_fn(i))
    build_range(base, cache, "bybit", "publicTrade", symbol,
                days[0], days[-1], require_manifest_done=False)
    return cache


def _days(start: str, n: int) -> list[str]:
    d0 = date.fromisoformat(start)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


# ----------------------------------------------------------------------------
# (a) descriptor correctness on constructed days
# ----------------------------------------------------------------------------

def test_d1_alternating_returns_give_strong_negative_ac():
    n = 600
    logpx = np.log(100.0) + 0.001 * np.cumsum(np.tile([1.0, -1.0], n // 2))
    d = day_descriptors(np.arange(n, dtype=np.int64), np.exp(logpx),
                        np.ones(n))
    assert d["D1_lag1_ac"] < -0.9


def test_d2_variance_signature_random_walk_vs_bounce():
    rng = np.random.default_rng(3)
    n = 1200
    rw = np.exp(np.log(100.0) + 0.001 * np.cumsum(rng.standard_normal(n)))
    d_rw = day_descriptors(np.arange(n, dtype=np.int64), rw, np.ones(n))
    assert 0.7 < d_rw["D2_variance_signature"] < 1.3, "random walk: VR ~ 1"
    # pure bounce: returns alternate -> 5-min RV collapses vs 1-min RV
    bounce = np.exp(np.log(100.0)
                    + 0.001 * np.cumsum(np.tile([1.0, -1.0], n // 2)))
    d_b = day_descriptors(np.arange(n, dtype=np.int64), bounce, np.ones(n))
    assert d_b["D2_variance_signature"] < 0.2, "bounce day: VR << 1"


def test_d3_herfindahl_uniform_vs_concentrated():
    n = 600
    px = np.full(n, 100.0)
    px[::2] = 100.1  # keep returns defined
    d_u = day_descriptors(np.arange(n, dtype=np.int64), px, np.ones(n))
    assert d_u["D3_herfindahl"] == pytest.approx(0.0, abs=1e-12)
    vols = np.full(n, 1e-9)
    vols[0] = 1000.0
    d_c = day_descriptors(np.arange(n, dtype=np.int64), px, vols)
    assert d_c["D3_herfindahl"] > 0.99


def test_day_floors_yield_nan():
    d = day_descriptors(np.arange(100, dtype=np.int64),
                        np.full(100, 100.0), np.ones(100))
    assert np.isnan(d["D1_lag1_ac"]) and np.isnan(d["D2_variance_signature"])
    d2 = day_descriptors(np.arange(30, dtype=np.int64),
                         np.full(30, 100.0), np.ones(30))
    assert np.isnan(d2["D3_herfindahl"])


# ----------------------------------------------------------------------------
# (b) the conditioning test — the clause that makes H-19 non-trivial
# ----------------------------------------------------------------------------

def test_partial_spearman_removes_vol_driven_pseudo_drift():
    rng = np.random.default_rng(11)
    n = 500
    t = np.arange(n, dtype=np.int64)
    vol_level = 1.0 + 2.0 * t / n + 0.1 * rng.standard_normal(n)  # vol trends
    desc = 0.8 * vol_level + 0.1 * rng.standard_normal(n)  # desc follows vol ONLY
    controls = np.column_stack([vol_level, np.ones(n) + 0.01 * rng.standard_normal(n)])
    raw = partial_spearman(desc, t, np.column_stack(
        [rng.standard_normal(n), rng.standard_normal(n)]))  # useless controls
    part = partial_spearman(desc, t, controls)
    assert abs(raw) > 0.8, "raw correlation must be large (sanity)"
    assert abs(part) < 0.15, (
        f"conditioning on the vol level must remove the pseudo-drift "
        f"(raw={raw:+.3f}, partial={part:+.3f})")


def test_rotation_null_p_calibrated_on_stationary_series():
    rng = np.random.default_rng(5)
    n = 400
    t = np.arange(n, dtype=np.int64)
    desc = rng.standard_normal(n)
    controls = rng.standard_normal((n, 2))
    rho = partial_spearman(desc, t, controls)
    p = rotation_null_p(desc, t, controls, rho, n_rotations=200)
    assert p > 0.05, f"stationary noise must not be significant (p={p:.3f})"


# ----------------------------------------------------------------------------
# (c)/(d) end-to-end on a synthetic cache: injected drift vs. null
# ----------------------------------------------------------------------------

def _price_day(ac: float, sigma: float, seed: int, n: int = 720) -> np.ndarray:
    """Minute prices whose return process has lag-1 AC ~ ``ac``."""
    rng = np.random.default_rng(seed)
    r = np.empty(n - 1)
    r[0] = sigma * rng.standard_normal()
    for i in range(1, n - 1):
        r[i] = ac * r[i - 1] + sigma * np.sqrt(1 - ac * ac) * rng.standard_normal()
    return np.exp(np.log(100.0) + np.cumsum(np.r_[0.0, r]))


@pytest.mark.filterwarnings("ignore")
def test_e2e_injected_d1_drift_is_found_and_null_is_not(tmp_path, monkeypatch):
    from bybit_edge.research.c19_drift import driver as drv
    n_days = 240
    days = _days("2023-01-01", n_days)

    # drifting symbol: AC ramps -0.3 -> +0.3 across the span
    cache = _build_cache(
        tmp_path / "drift", "DRFUSDT", days,
        price_fn=lambda i: _price_day(-0.3 + 0.6 * i / n_days, 0.001, seed=i),
        vol_fn=lambda i: np.ones(720))
    # two short judgment windows inside the fixture span
    monkeypatch.setattr(drv, "WINDOWS", (
        ("OOS1", ("2023-01-01", "2023-04-30")),
        ("OOS2", ("2023-05-01", "2023-08-28"))))
    monkeypatch.setattr(drv, "L_RANGE", ("2023-01-01", "2023-01-01"))
    monkeypatch.setattr(drv, "OOS2_RANGE", ("2023-05-01", "2023-08-28"))
    payload = drv.run(cache, symbols=("DRFUSDT",), skip_fingerprint_check=True,
                      expected_fingerprints={})
    f = {x["descriptor"]: x for x in payload["findings"]}
    assert f["D1_lag1_ac"]["drift_befund"] is True, f
    assert payload["cache_fingerprints"]["DRFUSDT"]["matches"] is False, (
        "fixture fingerprints must not match the registered constants")
    assert payload["gate_valid"] is True, "explicitly skipped for the fixture"

    # stationary symbol: constant AC 0.0
    cache_n = _build_cache(
        tmp_path / "null", "NULUSDT", days,
        price_fn=lambda i: _price_day(0.0, 0.001, seed=10_000 + i),
        vol_fn=lambda i: np.ones(720))
    payload_n = drv.run(cache_n, symbols=("NULUSDT",),
                        skip_fingerprint_check=True, expected_fingerprints={})
    assert all(not x["drift_befund"] for x in payload_n["findings"]), (
        payload_n["findings"])


# ----------------------------------------------------------------------------
# (e) fingerprint discipline / (f) capital freedom
# ----------------------------------------------------------------------------

def test_fingerprint_mismatch_sets_gate_invalid(tmp_path):
    days = _days("2023-01-01", 3)
    cache = _build_cache(tmp_path, "TSTUSDT", days,
                         price_fn=lambda i: _price_day(0.0, 0.001, seed=i),
                         vol_fn=lambda i: np.ones(720))
    payload = run(cache, symbols=("TSTUSDT",),
                  expected_fingerprints={"TSTUSDT": "deadbeef"})
    assert payload["gate_valid"] is False
    assert payload["cache_fingerprints"]["TSTUSDT"]["matches"] is False


def test_module_is_capital_free():
    import ast
    src = (Path(__file__).resolve().parents[2] / "src" / "bybit_edge"
           / "research" / "c19_drift" / "driver.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    code = src
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                code = code.replace(doc, "")
    lowered = "\n".join(l for l in code.splitlines()
                        if not l.lstrip().startswith("#")).lower()
    for term in ("bps", "fee", "slippage", "pnl", "sharpe", "taker", "maker"):
        assert term not in lowered, term
