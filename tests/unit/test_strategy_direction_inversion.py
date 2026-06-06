"""Tests for the opt-in S2/S3 direction-inversion debug flags.

Validates that ``config.S2_INVERT_DIRECTION`` / ``config.S3_INVERT_DIRECTION``:

* Default to False so existing trade-direction semantics are bit-identical.
* When True, flip the sign of the direction the strategy enters with.
* For S3: the basis-alignment gate (PRD 7.3 ``basis_aligned``) uses the
  POST-inversion direction so a tick that fails the gate in default mode
  passes it in inverted mode (and vice versa), keeping the gate semantically
  consistent with the actually-entered direction.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import numpy as np

from bybit_edge import config as _cfg
from bybit_edge.strategies.strategy2_entropy_momentum import (
    Strategy2EntropyMomentum,
)
from bybit_edge.strategies.strategy3_pre_settlement import (
    Strategy3PreSettlement,
)


# ---------------------------------------------------------------------------
# S2 helpers — mirror the warm-up + module-mock pattern from test_strategies.py
# ---------------------------------------------------------------------------

def _s2_warm_up(strat: Strategy2EntropyMomentum, n: int = 150) -> None:
    for i in range(n):
        bid_sizes = np.random.default_rng(i).uniform(1, 10, size=20)
        ask_sizes = np.random.default_rng(i + 1000).uniform(1, 10, size=20)
        strat.on_ticker(
            bid_sizes=bid_sizes,
            ask_sizes=ask_sizes,
            best_bid=(50000.0 - i * 0.01, 1.0),
            best_ask=(50001.0 + i * 0.01, 1.0),
            ticker_data={"premium_index": 0.001, "funding_rate": 0.0001},
            seconds_to_settlement=3600.0,
            price=50000.0 + i * 0.1,
            ts=1_700_000_000.0 + i,
        )


def _run_s2_entry_with_positive_ofi(
    strat: Strategy2EntropyMomentum,
) -> dict[str, Any]:
    """Drive S2 to entry with OFI > 0 (would-be Long in default mode)."""
    with patch.object(strat.m6, "compute", return_value={
        "greenlight": True, "h_bid": 0.5, "h_ask": 0.5,
        "h_combined": 0.1, "h_q5": 1.0, "signal": 1, "method_id": "M6",
        "confidence": 0.8, "ts": time.time(),
    }), patch.object(strat.m2, "update", return_value={
        "signal": 1, "ofi": 100.0, "ofi_q90": 50.0, "e_n": 10.0,
        "method_id": "M2", "confidence": 0.7, "ts": time.time(),
    }), patch.object(strat.m22, "compute", return_value={
        "signal": 1, "pressure": 0.001, "pressure_zscore": 3.0,
        "funding_rate": 0.0001, "seconds_to_settlement": 1000,
        "in_window": True, "method_id": "M22",
        "confidence": 0.6, "ts": time.time(),
    }), patch.object(strat.m7, "update", return_value={
        "greenlight": True, "pe": 0.3, "pe_median": 0.5,
        "signal": 1, "method_id": "M7",
        "confidence": 0.4, "ts": time.time(),
    }):
        strat._entropy_history.clear()
        for _ in range(200):
            strat._entropy_history.append(2.0)
        strat._entropy_history.append(0.1)

        return strat.on_ticker(
            bid_sizes=np.ones(20),
            ask_sizes=np.ones(20),
            best_bid=(50000.0, 1.0),
            best_ask=(50001.0, 1.0),
            ticker_data={"premium_index": 0.001, "funding_rate": 0.0001},
            seconds_to_settlement=1000.0,
            price=50000.0,
        )


# ---------------------------------------------------------------------------
# S3 helpers — mirror test_strategy3.py fixtures
# ---------------------------------------------------------------------------

def _make_ticker(
    last_price: float = 50000.0,
    mark_price: float = 50010.0,
    index_price: float = 50000.0,
    funding_rate: float = 0.0001,
    premium_index: float = 0.001,
) -> dict[str, Any]:
    return {
        "last_price": last_price,
        "mark_price": mark_price,
        "index_price": index_price,
        "funding_rate": funding_rate,
        "premium_index": premium_index,
    }


def _s3_warm_up(
    strat: Strategy3PreSettlement, n_samples: int = 200,
    premium_index: float = 0.0003,
) -> None:
    for i in range(n_samples):
        ticker = _make_ticker(premium_index=premium_index)
        strat.on_ticker(
            ticker,
            seconds_to_settlement=3600.0,
            open_interest=1000.0 + i * 0.1,
        )


# ===========================================================================
# S2 tests
# ===========================================================================

class TestS2DirectionInversion:
    """S2 entry direction flips when config.S2_INVERT_DIRECTION = True."""

    def test_s2_default_direction_unchanged(self) -> None:
        """OFI > 0, default flag (False) -> direction = +1 (Long)."""
        assert _cfg.S2_INVERT_DIRECTION is False
        strat = Strategy2EntropyMomentum()
        _s2_warm_up(strat)
        result = _run_s2_entry_with_positive_ofi(strat)
        assert result["action"] == "enter"
        assert result["direction"] == 1

    def test_s2_invert_flips_direction(self) -> None:
        """OFI > 0 + S2_INVERT_DIRECTION=True -> direction = -1 (Short)."""
        original = _cfg.S2_INVERT_DIRECTION
        try:
            _cfg.S2_INVERT_DIRECTION = True
            strat = Strategy2EntropyMomentum()
            _s2_warm_up(strat)
            result = _run_s2_entry_with_positive_ofi(strat)
            assert result["action"] == "enter"
            assert result["direction"] == -1
        finally:
            _cfg.S2_INVERT_DIRECTION = original


# ===========================================================================
# S3 tests
# ===========================================================================

class TestS3DirectionInversion:
    """S3 entry direction flips when config.S3_INVERT_DIRECTION = True."""

    def test_s3_default_direction_unchanged(self) -> None:
        """pressure > 0 (negative Premium), default -> direction = +1 (Long)."""
        assert _cfg.S3_INVERT_DIRECTION is False
        # Static method: pure unit assertion (no warm-up needed).
        assert Strategy3PreSettlement._direction_from_pressure(0.001) == 1
        assert Strategy3PreSettlement._direction_from_pressure(-0.001) == -1

    def test_s3_invert_flips_direction(self) -> None:
        """pressure > 0 + S3_INVERT_DIRECTION=True -> direction = -1."""
        original = _cfg.S3_INVERT_DIRECTION
        try:
            _cfg.S3_INVERT_DIRECTION = True
            assert Strategy3PreSettlement._direction_from_pressure(0.001) == -1
            assert Strategy3PreSettlement._direction_from_pressure(-0.001) == 1
        finally:
            _cfg.S3_INVERT_DIRECTION = original

    def test_s3_basis_gate_consistent_when_inverted(self) -> None:
        """basis_aligned check follows the POST-inversion direction.

        Setup uses the same scenario from ``test_no_entry_basis_wrong_direction``
        in test_strategy3.py: ``premium_index = 0.01`` -> pressure < 0 ->
        default direction = -1 (Short); a Short needs positive basis but here
        basis is NEGATIVE (mark < index), so the gate must reject in default
        mode. With S3_INVERT_DIRECTION=True the entered direction becomes +1
        (Long); a Long is aligned with a NEGATIVE basis, so the same tick now
        passes the gate.
        """
        # --- Default mode: must reject (basis_wrong_direction) ---
        strat_default = Strategy3PreSettlement()
        _s3_warm_up(strat_default, n_samples=200, premium_index=0.0003)
        ticker = _make_ticker(
            premium_index=0.01,        # positive Premium -> negative pressure
            mark_price=49950.0,        # below index -> negative basis
            index_price=50000.0,
        )
        result_default = strat_default.on_ticker(
            ticker, seconds_to_settlement=900.0, open_interest=1100.0,
        )
        assert result_default["action"] == "wait"
        assert result_default["reason"] == "basis_wrong_direction"

        # --- Inverted mode: same tick now enters as Long ---
        original = _cfg.S3_INVERT_DIRECTION
        try:
            _cfg.S3_INVERT_DIRECTION = True
            strat_inv = Strategy3PreSettlement()
            _s3_warm_up(strat_inv, n_samples=200, premium_index=0.0003)
            ticker_inv = _make_ticker(
                premium_index=0.01,
                mark_price=49950.0,
                index_price=50000.0,
            )
            result_inv = strat_inv.on_ticker(
                ticker_inv,
                seconds_to_settlement=900.0,
                open_interest=1100.0,
            )
            assert result_inv["action"] == "enter"
            assert result_inv["direction"] == 1  # post-inversion Long
        finally:
            _cfg.S3_INVERT_DIRECTION = original
