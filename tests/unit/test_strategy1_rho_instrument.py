"""
Tests for iter-4 Push A T2: S1 rho-distribution instrumentation.

Instrumentation is fully opt-in. When the flag is off, the buffer stays
None and the strategy is byte-for-byte identical to iter-3. When the flag
is on, every rho value seen at _check_entry is captured (including the
rho_below_threshold short-circuit ticks) and can be dumped as a JSON
summary via dump_rho_distribution.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from bybit_edge import config as _cfg
from bybit_edge.strategies.strategy1_cascade import Strategy1CascadeDetector


@pytest.fixture(autouse=True)
def _reset_s1_flags():
    saved = (_cfg.S1_RHO_INSTRUMENT_ENABLED, _cfg.S1_RHO_INSTRUMENT_MAXLEN)
    _cfg.S1_RHO_INSTRUMENT_ENABLED = False
    yield
    (_cfg.S1_RHO_INSTRUMENT_ENABLED,
     _cfg.S1_RHO_INSTRUMENT_MAXLEN) = saved


def _drive_check_entry(
    strat: Strategy1CascadeDetector, n_calls: int, rng: np.random.Generator
) -> list[float]:
    """Call _check_entry n_calls times with synthetic m14/m15/m26 dicts.

    Returns the list of rho values supplied (so tests can verify quantiles).
    """
    rhos: list[float] = []
    for _ in range(n_calls):
        rho = float(rng.uniform(0.0, 1.0))
        rhos.append(rho)
        m14_out = {"branching_ratio": rho}
        m15_out: dict[str, Any] = {
            "b_value": 1.0,
            "omori_active": False,
            "mainshock_ts": None,
            "omori_params": None,
        }
        m26_out = {"r0": 0.0}
        # Fire the check; result doesn't matter — we only care about the
        # instrumentation side-effect.
        strat._check_entry(m14_out, m15_out, m26_out)
    return rhos


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════

def test_instrument_off_no_samples_collected(tmp_path: Path) -> None:
    """Flag off: buffer stays None and dump_rho_distribution returns None."""
    strat = Strategy1CascadeDetector()
    rng = np.random.default_rng(seed=42)
    _drive_check_entry(strat, 200, rng)
    assert strat._rho_samples is None
    out = strat.dump_rho_distribution("BTCUSDT", tmp_path)
    assert out is None
    assert not (tmp_path / "rho_distribution_BTCUSDT.json").exists()


def test_instrument_on_quantiles_correct(tmp_path: Path) -> None:
    """Flag on: dumped JSON has all 9 quantile keys; p50 within ±0.05 of
    the known synthetic median; count == number of _check_entry calls."""
    _cfg.S1_RHO_INSTRUMENT_ENABLED = True
    strat = Strategy1CascadeDetector()
    rng = np.random.default_rng(seed=42)
    n_calls = 500
    rhos = _drive_check_entry(strat, n_calls, rng)

    out_path = strat.dump_rho_distribution("ETHUSDT", tmp_path)
    assert out_path is not None
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["symbol"] == "ETHUSDT"
    assert payload["n_samples"] == n_calls
    assert payload["threshold"] == pytest.approx(0.85)

    quantiles = payload["quantiles"]
    expected_keys = {"min", "p10", "p25", "p50", "p75",
                     "p90", "p95", "p99", "max"}
    assert set(quantiles.keys()) == expected_keys

    true_median = float(np.median(np.asarray(rhos)))
    assert abs(quantiles["p50"] - true_median) < 0.05


def test_instrument_buffer_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flag on, MAXLEN monkeypatched to 50: buffer length caps at 50."""
    _cfg.S1_RHO_INSTRUMENT_ENABLED = True
    monkeypatch.setattr(_cfg, "S1_RHO_INSTRUMENT_MAXLEN", 50)
    strat = Strategy1CascadeDetector()
    rng = np.random.default_rng(seed=7)
    _drive_check_entry(strat, 200, rng)
    assert strat._rho_samples is not None
    assert len(strat._rho_samples) == 50


def test_reset_clears_buffer() -> None:
    """reset() empties any collected samples."""
    _cfg.S1_RHO_INSTRUMENT_ENABLED = True
    strat = Strategy1CascadeDetector()
    rng = np.random.default_rng(seed=99)
    _drive_check_entry(strat, 30, rng)
    assert strat._rho_samples is not None
    assert len(strat._rho_samples) == 30
    strat.reset()
    assert strat._rho_samples is None or len(strat._rho_samples) == 0
