"""Unit tests for the H-24 IMPACT-PERSISTENZ gate (c24_impact, KAPITALFREI).

  (a) forward_move: horizon alignment, boundary tolerance, no self-overlap
      (the forward window must start at the NEXT minute close),
  (b) THE THREE REGIMES (DEC-39): reversal gives IC30 clearly NEGATIVE,
      permanent impact gives IC30 ~ 0 (it already sits in the impact
      minute's price), only continuation gives IC30 clearly positive —
      this is what caught the specification error before any run,
  (c) the gate separates them: continuation passes, reversal and permanent
      do not; impact_reading classifies all three,
  (d) the positive control is binding: a fixture where flow does not even
      move its own minute yields verdict_evaluable=false (NOT a drop),
  (e) recency clause: era windows never carry cell_pass flags,
  (f) fingerprint discipline and capital freedom.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.bar_cache import build_range
from bybit_edge.research.c24_impact.driver import (
    CONTROL_IC_MIN,
    day_metrics,
    forward_move,
    run,
    spearman,
)

EPOCH = date(1970, 1, 1)


# ----------------------------------------------------------------------------
# (a) forward_move
# ----------------------------------------------------------------------------

def test_forward_move_alignment_and_no_self_overlap():
    mi = np.arange(0, 100, dtype=np.int64)
    log_px = np.linspace(0.0, 0.99, 100)      # +0.01 per minute
    fwd = forward_move(mi, log_px, 30)
    assert fwd[0] == pytest.approx(0.30), "m -> m+30 spans exactly 30 minutes"
    assert fwd[10] == pytest.approx(0.30)
    assert np.isnan(fwd[-1]), "no bar 30 minutes past the end"
    # a bar exactly at m (horizon 0) would be self-overlap -> excluded
    assert np.all(np.isnan(forward_move(mi, log_px, 0)))


def test_forward_move_boundary_tolerance():
    # gap: minutes 0..10 then 50..60; from minute 10 the +30 target (40) has
    # no bar within 5 minutes -> NaN
    mi = np.r_[np.arange(0, 11), np.arange(50, 61)].astype(np.int64)
    log_px = np.linspace(0.0, 0.21, mi.size)
    fwd = forward_move(mi, log_px, 30)
    assert np.isnan(fwd[10])
    # from minute 25 there is no bar at all; from minute 50 the target 80 is
    # also outside -> NaN, but minute 0 -> target 30 also has no bar
    assert np.isnan(fwd[0])


# ----------------------------------------------------------------------------
# fixture helpers: minute bars with controlled flow/return coupling
# ----------------------------------------------------------------------------

def _day_arrays(n: int, seed: int, *, contemp: float, persist: float,
                lead: float = 0.0
                ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Minute bars with a controllable impact regime.

    ``contemp`` scales the same-minute impact of the net flow; ``persist``
    is the fraction of it that STAYS (0 = fully given back over the next 30
    minutes); ``lead`` adds a forward push of the same size, i.e. genuine
    continuation. The three registered regimes are (persist=0, lead=0)
    reversal, (1, 0) permanent, (1, 1) continuation.
    """
    rng = np.random.default_rng(seed)
    flow = rng.standard_normal(n)
    r = contemp * 1e-4 * flow + 1e-4 * rng.standard_normal(n)
    add = np.zeros(n)
    give_back = (1.0 - persist) * contemp * 1e-4 * flow / 30.0
    push = lead * contemp * 1e-4 * flow / 30.0
    for k in range(1, 31):
        add[k:] += (push - give_back)[:-k]
    px = np.exp(np.log(100.0) + np.cumsum(r + add))
    base = 10.0
    return (np.arange(n, dtype=np.int64), px,
            base + np.maximum(flow, 0.0), base + np.maximum(-flow, 0.0))


def test_three_impact_regimes_are_distinguished(): 
    """DEC-39: the fixture that caught the specification error.

    A PERMANENT impact does NOT produce a positive forward IC — it already
    sits in the impact minute's price. Pinned here so the distinction can
    never be lost again.
    """
    n = 1400
    out = {}
    for name, (persist, lead) in {"reversal": (0.0, 0.0),
                                  "permanent": (1.0, 0.0),
                                  "continuation": (1.0, 1.0)}.items():
        met = day_metrics(*_day_arrays(n, 7, contemp=5.0, persist=persist,
                                       lead=lead), horizons=(30,))
        assert met["ic_contemp"] > 0.3, f"{name}: control must fire"
        out[name] = met["ic_p30"]
    assert out["reversal"] < -0.10, out
    assert abs(out["permanent"]) < 0.05, (
        f"a permanent impact must give a forward IC near ZERO, not positive "
        f"(got {out['permanent']:+.4f}) — this is the DEC-39 finding")
    assert out["continuation"] > 0.05, out
    assert out["reversal"] < out["permanent"] < out["continuation"]


def test_impact_reading_classifies_the_three_regimes():
    from bybit_edge.research.c24_impact.driver import impact_reading
    assert impact_reading(-0.22) == "reversal"
    assert impact_reading(-0.01) == "permanent"
    assert impact_reading(+0.01) == "permanent"
    assert impact_reading(+0.13) == "continuation"
    assert impact_reading(None) is None


def test_day_floor_returns_none():
    mi, px, vb, vs = _day_arrays(100, 2, contemp=5.0, persist=1.0)
    assert day_metrics(mi, px, vb, vs, horizons=(30,)) is None


# ----------------------------------------------------------------------------
# end-to-end on synthetic caches
# ----------------------------------------------------------------------------

def _write_cache(tmp_path: Path, symbol: str, days: list[str], *,
                 contemp: float, persist: float, seed: int,
                 lead: float = 0.0) -> Path:
    import pyarrow as pa
    import pyarrow.parquet as pq

    base, cache = tmp_path / "h", tmp_path / "c"
    for i, day in enumerate(days):
        n = 1400
        mi, px, vb, vs = _day_arrays(n, seed + i, contemp=contemp,
                                     persist=persist, lead=lead)
        ms0 = (date.fromisoformat(day) - EPOCH).days * 86_400_000
        ts, payloads = [], []
        for k in range(n):
            # one buy and one sell trade per minute carrying the split volume
            ts.append(ms0 + k * 60_000)
            payloads.append(json.dumps({"side": "Buy", "price": f"{px[k]:.8f}",
                                        "size": f"{vb[k]:.8f}"}))
            ts.append(ms0 + k * 60_000 + 1)
            payloads.append(json.dumps({"side": "Sell", "price": f"{px[k]:.8f}",
                                        "size": f"{vs[k]:.8f}"}))
        d = (base / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}"
             / f"date={day}")
        d.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.table({
            "ts_local_ns": pa.array([t * 10**6 for t in ts], pa.int64()),
            "ts_exchange_ms": pa.array(ts, pa.int64()),
            "topic": pa.array(["publicTrade"] * len(ts)),
            "stream": pa.array(["publicTrade"] * len(ts)),
            "symbol": pa.array([symbol] * len(ts)),
            "payload_json": pa.array(payloads),
        }), d / "part-0.parquet")
    build_range(base, cache, "bybit", "publicTrade", symbol, days[0], days[-1],
                require_manifest_done=False)
    return cache


def _days(start: str, n: int) -> list[str]:
    d0 = date.fromisoformat(start)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


@pytest.mark.filterwarnings("ignore")
def test_e2e_continuation_passes_reversal_does_not(tmp_path, monkeypatch):
    from bybit_edge.research.c24_impact import driver as drv
    monkeypatch.setattr(drv, "N_DAYS_FLOOR", 6)
    days = _days("2026-02-01", 24)
    wins = (("W-A", days[0], days[11]), ("W-B", days[12], days[-1]))

    cache_p = _write_cache(tmp_path / "p", "PRSUSDT", days, contemp=5.0,
                           persist=1.0, lead=1.0, seed=100)
    pay_p = drv.run(cache_p, symbols=("PRSUSDT",), judgment_windows=wins,
                    era_windows=(), skip_fingerprint_check=True,
                    expected_fingerprints={})
    assert pay_p["control_passed"] is True
    assert pay_p["verdict_evaluable"] is True
    assert pay_p["both_windows_pass"] is True, pay_p["cells"]
    assert all(c["impact_reading"] == "continuation" for c in pay_p["cells"])

    cache_t = _write_cache(tmp_path / "t", "TRNUSDT", days, contemp=5.0,
                           persist=0.0, seed=200)
    pay_t = drv.run(cache_t, symbols=("TRNUSDT",), judgment_windows=wins,
                    era_windows=(), skip_fingerprint_check=True,
                    expected_fingerprints={})
    assert pay_t["control_passed"] is True, (
        "the control must still fire — the impact IS there, it just decays")
    assert pay_t["verdict_evaluable"] is True
    assert pay_t["both_windows_pass"] is False, pay_t["cells"]
    assert all(c["impact_reading"] == "reversal" for c in pay_t["cells"])


@pytest.mark.filterwarnings("ignore")
def test_failed_positive_control_blocks_verdict(tmp_path, monkeypatch):
    from bybit_edge.research.c24_impact import driver as drv
    monkeypatch.setattr(drv, "N_DAYS_FLOOR", 6)
    days = _days("2026-02-01", 14)
    wins = (("W-A", days[0], days[-1]),)
    # contemp=0: flow does not move its own minute at all
    cache = _write_cache(tmp_path, "NULUSDT", days, contemp=0.0, persist=1.0,
                         seed=300)
    pay = drv.run(cache, symbols=("NULUSDT",), judgment_windows=wins,
                  era_windows=(), skip_fingerprint_check=True,
                  expected_fingerprints={})
    assert pay["cells"][0]["mean_ic_contemp"] < CONTROL_IC_MIN
    assert pay["control_passed"] is False
    assert pay["verdict_evaluable"] is False, (
        "a machinery blind to contemporaneous impact carries no verdict")
    assert pay["both_windows_pass"] is False


@pytest.mark.filterwarnings("ignore")
def test_era_windows_are_never_judgment_bearing(tmp_path, monkeypatch):
    from bybit_edge.research.c24_impact import driver as drv
    monkeypatch.setattr(drv, "N_DAYS_FLOOR", 4)
    days = _days("2026-02-01", 20)
    cache = _write_cache(tmp_path, "ERAUSDT", days, contemp=5.0, persist=1.0,
                         lead=1.0, seed=400)
    pay = drv.run(cache, symbols=("ERAUSDT",),
                  judgment_windows=(("W-A", days[10], days[-1]),),
                  era_windows=(("E-OLD", days[0], days[9]),),
                  skip_fingerprint_check=True, expected_fingerprints={})
    era = pay["era_profile"][0]
    assert era["judgment_bearing"] is False
    assert "cell_pass" not in era and "fdr_significant" not in era, (
        "era cells must never carry gate flags")
    assert era["mean_ic_p30"] is not None, "but they must still be reported"


def test_fingerprint_mismatch_sets_gate_invalid(tmp_path):
    days = _days("2026-02-01", 3)
    cache = _write_cache(tmp_path, "FPUSDT", days, contemp=5.0, persist=1.0,
                         seed=500)
    pay = run(cache, symbols=("FPUSDT",),
              judgment_windows=(("W-A", days[0], days[-1]),), era_windows=(),
              expected_fingerprints={"FPUSDT": "deadbeef"})
    assert pay["gate_valid"] is False


def test_spearman_matches_known_value():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert spearman(x, x) == pytest.approx(1.0)
    assert spearman(x, -x) == pytest.approx(-1.0)


def test_module_is_capital_free():
    import ast
    src = (Path(__file__).resolve().parents[2] / "src" / "bybit_edge"
           / "research" / "c24_impact" / "driver.py").read_text(encoding="utf-8")
    code = src
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                code = code.replace(doc, "")
    lowered = "\n".join(l for l in code.splitlines()
                        if not l.lstrip().startswith("#")).lower()
    for term in ("bps", "fee", "slippage", "pnl", "sharpe", "taker", "maker",
                 "friction", "commission"):
        assert term not in lowered, term
