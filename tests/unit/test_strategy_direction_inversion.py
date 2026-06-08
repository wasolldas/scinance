"""Tests for the opt-in S2/S3 direction-inversion debug flags.

Validates that ``config.S2_INVERT_DIRECTION`` / ``config.S3_INVERT_DIRECTION``:

* Default to False so existing trade-direction semantics are bit-identical.
* When True, flip the sign of the direction the strategy enters with.
* For S3: the basis-alignment gate (PRD 7.3 ``basis_aligned``) evaluates
  against the UN-INVERTED (economically intended) direction so the gate
  population is invariant under the flag — only the entered direction flips.
  This is the gate-invariant inversion semantics: same trades fire, opposite
  side. Allows clean A/B-comparison of "is the direction wrong?" without
  changing the entry-tick population.
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
    """S3 entry direction flips when config.S3_INVERT_DIRECTION = True.

    Gate-invariant inversion: the basis-alignment gate consumes the
    un-inverted direction so the entered-tick population is identical to
    the default-mode run; only the direction the strategy *enters* with
    flips. This is what enables a clean original-vs-inverted A/B replay.
    """

    def test_s3_default_direction_unchanged(self) -> None:
        """pressure > 0 (negative Premium), default -> direction = +1 (Long).

        The static helper :meth:`_direction_from_pressure` no longer reads
        the inversion flag (the inversion happens at the entry-emission
        call site in :meth:`on_ticker`). The helper must return the base
        direction unconditionally.
        """
        assert _cfg.S3_INVERT_DIRECTION is False
        assert Strategy3PreSettlement._direction_from_pressure(0.001) == 1
        assert Strategy3PreSettlement._direction_from_pressure(-0.001) == -1

    def test_s3_helper_ignores_flag(self) -> None:
        """The flag must NOT affect the helper — only the entry-emission site.

        Regression test for the previous-iteration W1 bug where the flag
        flipped the helper itself, which silently broke the basis-alignment
        gate (gate consumed the inverted direction and rejected every tick).
        """
        original = _cfg.S3_INVERT_DIRECTION
        try:
            _cfg.S3_INVERT_DIRECTION = True
            # Even with the flag on, the helper returns the BASE direction
            # because the flip now happens at the on_ticker call site only.
            assert Strategy3PreSettlement._direction_from_pressure(0.001) == 1
            assert Strategy3PreSettlement._direction_from_pressure(-0.001) == -1
        finally:
            _cfg.S3_INVERT_DIRECTION = original

    def test_s3_inverted_path_preserves_gate(self) -> None:
        """The same fixture that enters in default mode must still enter
        in inverted mode (gate population invariant) — only the entered
        direction flips. Uses a scenario crafted to pass all four entry
        gates with default flags.
        """
        # Default mode: positive pressure (negative premium) + negative
        # basis (mark < index) -> Long is gate-aligned, all gates pass.
        ticker = _make_ticker(
            premium_index=-0.01,       # negative Premium -> positive pressure
            mark_price=49950.0,        # below index -> negative basis
            index_price=50000.0,
        )

        strat_default = Strategy3PreSettlement()
        _s3_warm_up(strat_default, n_samples=200, premium_index=-0.0003)
        result_default = strat_default.on_ticker(
            ticker, seconds_to_settlement=900.0, open_interest=1100.0,
        )
        assert result_default["action"] == "enter"
        assert result_default["direction"] == 1  # Long (un-inverted)

        # Inverted mode: same fixture, same gate decision, opposite direction.
        original = _cfg.S3_INVERT_DIRECTION
        try:
            _cfg.S3_INVERT_DIRECTION = True
            strat_inv = Strategy3PreSettlement()
            _s3_warm_up(strat_inv, n_samples=200, premium_index=-0.0003)
            ticker_inv = _make_ticker(
                premium_index=-0.01,
                mark_price=49950.0,
                index_price=50000.0,
            )
            result_inv = strat_inv.on_ticker(
                ticker_inv,
                seconds_to_settlement=900.0,
                open_interest=1100.0,
            )
            # Same gate-population: the tick still ENTERS (regression test
            # for the W1 bug where inverted runs produced 0 trades).
            assert result_inv["action"] == "enter"
            # Direction flipped (the only observable difference).
            assert result_inv["direction"] == -1
        finally:
            _cfg.S3_INVERT_DIRECTION = original

    def test_s3_inverted_path_zero_pressure_does_not_enter(self) -> None:
        """With pressure exactly 0 and S3_INVERT_DIRECTION=True the strategy
        must NOT enter a trade. Guards against sign-mishandling at the
        boundary (e.g. accidentally treating ``-0 != 0`` and flipping a
        zero direction into a +1 entry).

        Pressure=0 fails the Q90 gate (``abs(0)`` cannot exceed any
        non-negative Q90), so the wait reason is ``pressure_below_q90``;
        the ``pressure_zero`` branch is unreachable for an exact-zero tick
        and exists purely as a defence-in-depth divide-by-zero guard.
        """
        original = _cfg.S3_INVERT_DIRECTION
        try:
            _cfg.S3_INVERT_DIRECTION = True
            strat = Strategy3PreSettlement()
            # Warm up with non-zero pressure so Q90 is positive; live tick
            # has zero pressure so it cannot exceed Q90.
            _s3_warm_up(strat, n_samples=200, premium_index=0.0003)
            ticker_zero = _make_ticker(
                premium_index=0.0,         # -> pressure exactly 0
                mark_price=50000.0,
                index_price=50000.0,
            )
            result = strat.on_ticker(
                ticker_zero, seconds_to_settlement=900.0, open_interest=1100.0,
            )
            assert result["action"] == "wait"
            assert result["direction"] == 0
            # Q90 fires first; pressure_zero is unreachable for exact zero.
            assert result["reason"] == "pressure_below_q90"
        finally:
            _cfg.S3_INVERT_DIRECTION = original
