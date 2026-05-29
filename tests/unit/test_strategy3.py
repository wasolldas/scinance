"""
Tests for Strategy 3: Pre-Settlement Pressure-Release.

PRD 7.3 Entry conditions:
    T_settlement - t < 30 min
    AND |Funding-Pressure| > Q90 (rolling 30d)
    AND Mark-Index-Basis * sign(Pressure) > 0
    AND BOCPD-Run-Length stable (no concurrent changepoint)

PRD 7.3 Exit conditions:
    Settlement-Tick + 10 min
    OR Funding resets to [-0.01%, +0.01%]

Tests cover: entry gating, direction logic, exit triggers,
position management, and full lifecycle.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from bybit_edge.strategies.strategy3_pre_settlement import (
    Strategy3PreSettlement,
    _ENTRY_WINDOW_SECONDS,
    _EXIT_BAND_HIGH,
    _EXIT_BAND_LOW,
    _EXIT_SECONDS_POST_SETTLEMENT,
    _MIN_SAMPLES_FOR_QUANTILE,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures & Helpers
# ═══════════════════════════════════════════════════════════════════

def _make_ticker(
    last_price: float = 50000.0,
    mark_price: float = 50010.0,
    index_price: float = 50000.0,
    funding_rate: float = 0.0001,
    premium_index: float = 0.001,
) -> dict[str, Any]:
    """Build a minimal ticker_data dict for Strategy3."""
    return {
        "last_price": last_price,
        "mark_price": mark_price,
        "index_price": index_price,
        "funding_rate": funding_rate,
        "premium_index": premium_index,
    }


def _warm_up_strategy(
    strat: Strategy3PreSettlement,
    n_samples: int = 150,
    premium_index: float = 0.001,
    oi_base: float = 1000.0,
) -> None:
    """Feed enough tickers to build up pressure history for Q90 computation.

    Uses a moderate premium_index so most history is 'normal' pressure,
    allowing extreme values to stand out above Q90.
    """
    for i in range(n_samples):
        ticker = _make_ticker(premium_index=premium_index)
        strat.on_ticker(
            ticker,
            seconds_to_settlement=3600.0,  # far from settlement
            open_interest=oi_base + i * 0.1,
        )


def _trigger_entry(
    strat: Strategy3PreSettlement,
    extreme_premium: float = 0.01,
    mark_price: float = 50050.0,
    index_price: float = 50000.0,
    last_price: float | None = None,
    seconds_to_settlement: float = 900.0,
    open_interest: float = 1100.0,
) -> dict[str, Any]:
    """Create conditions that should trigger an entry.

    Uses a very extreme premium_index that generates pressure well
    above Q90 of the warmed-up history, and aligned basis.
    ``last_price`` defaults to ``mark_price`` when not specified.
    """
    if last_price is None:
        last_price = mark_price
    ticker = _make_ticker(
        premium_index=extreme_premium,
        mark_price=mark_price,
        index_price=index_price,
        last_price=last_price,
    )
    return strat.on_ticker(
        ticker,
        seconds_to_settlement=seconds_to_settlement,
        open_interest=open_interest,
    )


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestStrategy3PreSettlement:
    """Test suite for Strategy3PreSettlement."""

    # ----- 1. Entry-Window Gating -----

    def test_no_entry_outside_window(self) -> None:
        """60 minutes before settlement (> 30min window) -> wait."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat)

        result = _trigger_entry(
            strat,
            seconds_to_settlement=3600.0,  # 60 min — outside 30-min window
        )
        assert result["action"] == "wait"
        assert result["strategy"] == "S3"

    # ----- 2. All Conditions Met -----

    def test_entry_all_conditions_met(self) -> None:
        """30-min window + extreme pressure + basis aligned + BOCPD stable -> enter."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # premium_index=0.01 (positive Premium) → P=0.01, I=0.0003
        # diff = I-P = -0.0097, clamped = -0.0005, pressure = -0.0092 (negativ)
        # PRD 7.3/M22: negative pressure (positive Premium) → Short-Reversion.
        # "Gleiche Richtung": ein Short braucht eine POSITIVE Basis (Perp über
        # Index) → mark > index. (basis * direction < 0, direction = -1.)
        result = _trigger_entry(
            strat,
            extreme_premium=0.01,  # positive Premium → negative Pressure → Short
            mark_price=50050.0,    # above index → positive basis → aligned
            index_price=50000.0,
            seconds_to_settlement=900.0,  # 15 min
        )
        assert result["action"] == "enter"
        assert result["direction"] == -1  # Short (positive Premium)
        assert result["strategy"] == "S3"
        assert result["price"] == 50050.0
        assert "M22" in result["modules"]
        assert "M23" in result["modules"]
        assert "M24" in result["modules"]
        assert "M8" in result["modules"]

    # ----- 3. Pressure Too Low -----

    def test_no_entry_pressure_too_low(self) -> None:
        """In window but pressure below Q90 threshold -> wait."""
        strat = Strategy3PreSettlement()
        # Warm up with same pressure as the test tick -> Q90 won't be exceeded
        _warm_up_strategy(strat, n_samples=200, premium_index=0.001)

        # Use the same premium as warmup — not extreme enough
        ticker = _make_ticker(premium_index=0.001, mark_price=50005.0)
        result = strat.on_ticker(
            ticker,
            seconds_to_settlement=900.0,  # inside window
            open_interest=1100.0,
        )
        assert result["action"] == "wait"
        assert "pressure_below_q90" in result["reason"] or result["action"] == "wait"

    # ----- 4. Basis Wrong Direction -----

    def test_no_entry_basis_wrong_direction(self) -> None:
        """Basis confirms the WRONG direction -> wait (PRD 7.3 gleiche Richtung).

        premium_index=0.01 (positive Premium) → pressure<0 → Short (direction
        -1). A Short is only aligned with a POSITIVE basis; here we feed a
        NEGATIVE basis (mark < index) so the gate must reject it. (Previously
        this test asserted the inverted alignment, cementing the bug.)
        """
        strat = Strategy3PreSettlement()
        # Warm up with low pressure so the extreme tick stands out
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # premium_index=0.01 → pressure = -0.0092 (negative) → direction = -1
        # MISALIGNMENT: a Short needs positive basis, but here basis NEGATIVE
        ticker = _make_ticker(
            premium_index=0.01,
            mark_price=49950.0,  # below index → negative basis → misaligned
            index_price=50000.0,
        )
        result = strat.on_ticker(
            ticker,
            seconds_to_settlement=900.0,
            open_interest=1100.0,
        )
        assert result["action"] == "wait"
        assert result["reason"] == "basis_wrong_direction"

    # ----- 5. BOCPD Changepoint Detected -----

    def test_no_entry_bocpd_changepoint(self) -> None:
        """BOCPD detects a changepoint -> wait (too unstable)."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # Mock M8 to always return changepoint=True
        original_compute = strat.m8.compute

        def mock_bocpd_compute(x: float) -> dict[str, Any]:
            result = original_compute(x)
            result["changepoint"] = True
            return result

        strat.m8.compute = mock_bocpd_compute  # type: ignore[assignment]

        # premium_index=0.01 → negative pressure → Short (direction -1)
        # mark > index → positive basis → ALIGNED for a Short (passes gate)
        # So we reach the BOCPD condition, which should block entry
        result = _trigger_entry(
            strat,
            extreme_premium=0.01,
            mark_price=50050.0,   # above index → positive basis → aligned
            index_price=50000.0,
            seconds_to_settlement=900.0,
            open_interest=5000.0,
        )
        assert result["action"] == "wait"
        assert result["reason"] == "bocpd_changepoint_detected"

    # ----- 6. Direction: Long -----

    def test_entry_direction_long(self) -> None:
        """Positive pressure (negative Premium) -> direction = +1 (Long).

        Corrected per PRD 7.3/M22 (S.682): "aufgestaute Negative-Premium-
        Pressure ... Reversion kommt" → Long. Negative Premium ⇒ diff=(I-P)>0
        ⇒ Pressure > 0. A Long is aligned with a NEGATIVE basis (perp below
        index): basis * direction < 0 with direction = +1.
        """
        strat = Strategy3PreSettlement()
        # Warm up with small positive premium (low pressure)
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # I = 0.0003, P = -0.01 → diff = 0.0103, clamped = 0.0005
        # pressure = 0.0098 → POSITIVE → Long
        # Basis negative (mark < index) → aligned for a Long
        ticker = _make_ticker(
            premium_index=-0.01,  # large negative Premium → positive pressure
            mark_price=49950.0,   # below index → negative basis → aligned
            index_price=50000.0,
        )
        result = strat.on_ticker(
            ticker,
            seconds_to_settlement=900.0,
            open_interest=1100.0,
        )
        assert result["action"] == "enter"
        assert result["direction"] == 1  # Long

    # ----- 7. Direction: Short -----

    def test_entry_direction_short(self) -> None:
        """Negative pressure (positive Premium) -> direction = -1 (Short).

        Corrected per PRD 7.3/M22: positive Premium (perp overpriced, Longs
        zu wenig gezahlt) → Short-Reversion. Positive Premium ⇒ diff=(I-P)<0
        ⇒ Pressure < 0. A Short is aligned with a POSITIVE basis: basis *
        direction < 0 with direction = -1.
        """
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # I = 0.0003, P = 0.01 → diff = -0.0097, clamped = -0.0005
        # pressure = -0.0092 → NEGATIVE → Short
        # Basis positive (mark > index) → aligned for a Short
        ticker = _make_ticker(
            premium_index=0.01,   # large positive Premium → negative pressure
            mark_price=50050.0,   # above index → positive basis → aligned
            index_price=50000.0,
        )
        result = strat.on_ticker(
            ticker,
            seconds_to_settlement=900.0,
            open_interest=1100.0,
        )
        assert result["action"] == "enter"
        assert result["direction"] == -1  # Short

    # ----- 8. Exit After Settlement + 10 min -----

    def test_exit_after_settlement(self) -> None:
        """Settlement passed + 10 min -> exit."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # Enter trade — negative Premium → positive pressure → Long;
        # aligned with a negative basis (mark < index). (PRD 7.3)
        entry = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=49950.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert entry["action"] == "enter"
        assert strat.in_trade

        # Now simulate: settlement has passed by > 10 minutes
        # seconds_to_settlement = -(10*60 + 1) = -601
        ticker = _make_ticker(premium_index=-0.01, mark_price=49950.0)
        result = strat.on_ticker(
            ticker,
            seconds_to_settlement=-601.0,  # 10min01s past settlement
            open_interest=1100.0,
        )
        assert result["action"] == "exit"
        assert "settlement" in result["reason"]
        assert not strat.in_trade

    # ----- 9. Exit: Pressure Dissipated -----

    def test_exit_pressure_dissipated(self) -> None:
        """Pressure falls back within [-0.01%, +0.01%] -> exit."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # Enter trade — negative Premium → positive pressure → Long;
        # aligned with negative basis (mark < index). (PRD 7.3)
        entry = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=49950.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert entry["action"] == "enter"

        # Now send ticker where pressure is near zero (premium = I so diff ~ 0)
        # I = 0.0003, P = 0.0003 → diff = 0 → clamped = 0 → pressure = 0
        ticker = _make_ticker(
            premium_index=0.0003,  # equal to I → zero pressure
            mark_price=50000.0,
            index_price=50000.0,
        )
        result = strat.on_ticker(
            ticker,
            seconds_to_settlement=500.0,  # still before settlement
            open_interest=1100.0,
        )
        assert result["action"] == "exit"
        assert result["reason"] == "pressure_dissipated"

    # ----- 10. No Double Entry -----

    def test_no_double_entry(self) -> None:
        """Already in a trade -> no second entry allowed."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # First entry — negative Premium → Long, negative basis (aligned)
        entry1 = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=49950.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert entry1["action"] == "enter"
        assert strat.in_trade

        # Attempt second entry with same extreme conditions
        entry2 = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=49945.0,
            index_price=50000.0,
            seconds_to_settlement=800.0,
        )
        # Should NOT enter again (exit logic will kick in if conditions met,
        # otherwise wait)
        assert entry2["action"] != "enter" or not strat.in_trade

    # ----- 11. Reset After Exit -----

    def test_reset_after_exit(self) -> None:
        """After exit: _in_trade=False, direction=0, entry_price=0."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # Enter — negative Premium → Long, negative basis (aligned, PRD 7.3)
        entry = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=49950.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert entry["action"] == "enter"

        # Exit via settlement timeout
        ticker = _make_ticker(premium_index=-0.01, mark_price=49950.0)
        exit_result = strat.on_ticker(
            ticker,
            seconds_to_settlement=-700.0,
            open_interest=1100.0,
        )
        assert exit_result["action"] == "exit"

        # Verify internal state is fully reset
        assert strat.in_trade is False
        assert strat.entry_direction == 0
        assert strat.entry_price == 0.0

    # ----- 12. Full Lifecycle -----

    def test_full_lifecycle(self) -> None:
        """Entry -> hold -> exit sequence with all intermediate checks."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # Phase 1: Not yet in window -> wait
        result = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=49950.0),
            seconds_to_settlement=2000.0,  # > 30 min
            open_interest=1100.0,
        )
        assert result["action"] == "wait"
        assert not strat.in_trade

        # Phase 2: Enter window with extreme conditions -> enter
        # negative Premium → positive pressure → Long; negative basis aligned.
        entry = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=49950.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert entry["action"] == "enter"
        assert strat.in_trade
        entered_direction = entry["direction"]

        # Phase 3: Still in trade, pressure still extreme, before settlement -> hold
        # (seconds_to_settlement still positive, pressure NOT dissipated)
        hold_result = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=49940.0),
            seconds_to_settlement=300.0,  # 5 min to settlement, pressure still extreme
            open_interest=1100.0,
        )
        # Should either wait (hold) or exit depending on pressure.
        # With extreme premium, pressure won't be in the exit band.
        assert strat.in_trade  # still holding

        # Phase 4: Past settlement by > 10 min -> exit
        exit_result = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=49930.0),
            seconds_to_settlement=-700.0,  # 11.67 min past settlement
            open_interest=1100.0,
        )
        assert exit_result["action"] == "exit"
        assert not strat.in_trade
        assert strat.entry_direction == 0

        # Phase 5: After exit, can enter again in next settlement window
        # Re-warm to add more Q90 history
        for i in range(50):
            strat.on_ticker(
                _make_ticker(premium_index=0.0003),
                seconds_to_settlement=7200.0,
                open_interest=1200.0 + i,
            )

        reentry = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=49950.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
            open_interest=1300.0,
        )
        assert reentry["action"] == "enter"
        assert strat.in_trade

    # ----- 13. Module outputs in result -----

    def test_modules_in_output(self) -> None:
        """Every result contains all four module outputs."""
        strat = Strategy3PreSettlement()
        ticker = _make_ticker()
        result = strat.on_ticker(ticker, seconds_to_settlement=1000.0, open_interest=1000.0)

        assert "modules" in result
        for key in ("M22", "M23", "M24", "M8"):
            assert key in result["modules"]
            assert "signal" in result["modules"][key]
            assert "method_id" in result["modules"][key]

    # ----- 14. Reset method -----

    def test_reset_clears_all_state(self) -> None:
        """reset() brings the strategy back to initial state."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # Enter a trade — negative Premium → Long, negative basis (aligned)
        _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=49950.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert strat.in_trade

        # Reset
        strat.reset()

        assert strat.in_trade is False
        assert strat.entry_direction == 0
        assert strat.entry_price == 0.0
        assert len(strat._pressure_history) == 0

    # ----- 15. Edge case: zero index price -----

    def test_zero_index_price_safe(self) -> None:
        """Zero index price should not crash, basis defaults to 0."""
        strat = Strategy3PreSettlement()
        ticker = _make_ticker(index_price=0.0, mark_price=50000.0)
        result = strat.on_ticker(ticker, seconds_to_settlement=900.0, open_interest=1000.0)
        assert result["action"] == "wait"
        assert result["modules"]["M23"]["basis"] == 0.0


# ═══════════════════════════════════════════════════════════════════
# Regression — REALISTIC coupling (premium_index == basis).
#
# In production (live_runner / replay_backtester) premium_index is
# *derived* from mark/index exactly like M23's basis — they are the
# SAME number (see TickerSnapshot.basis / .premium_index). The helpers
# above decouple them, which masked the bug. These tests feed the
# realistic, coupled ticker.
#
# Bug (PRD 7.3): with premium_index == basis the pressure overflow from
# M22 always has the OPPOSITE sign to the basis (because pressure is the
# clamp residual of (I - P)). Hence the literal gate
# ``basis * sign(pressure) > 0`` is NEVER satisfiable -> S3 never enters
# (empirically 0 trades in the replay backtester). The economically
# correct gate (PRD 7.3 "gleiche Richtung") requires that the basis
# CONFIRMS the intended mean-reversion trade direction:
#   - negative basis (perp underpriced) -> Long-reversion  (PRD 4 M22:
#     "aufgestaute Negative-Premium-Pressure ... Reversion kommt")
#   - positive basis (perp overpriced)  -> Short-reversion
# ═══════════════════════════════════════════════════════════════════

def _coupled_ticker(
    *,
    basis: float,
    index_price: float = 50_000.0,
    last_price: float | None = None,
) -> dict[str, Any]:
    """Build a *realistic* ticker where premium_index == basis.

    Mirrors production: premium_index is derived from mark/index, the
    identical value M23 computes as basis.
    """
    mark_price = index_price * (1.0 + basis)
    if last_price is None:
        last_price = mark_price
    return {
        "last_price": last_price,
        "mark_price": mark_price,
        "index_price": index_price,
        "funding_rate": 0.0001,
        "premium_index": basis,  # == (mark - index) / index
    }


def _warm_up_coupled(strat: Strategy3PreSettlement, n_samples: int = 200) -> None:
    """Warm Q90 history with small, realistic coupled basis values."""
    for i in range(n_samples):
        strat.on_ticker(
            _coupled_ticker(basis=0.0003),
            seconds_to_settlement=3600.0,
            open_interest=1000.0 + i * 0.1,
        )


class TestStrategy3RealisticCoupling:
    """S3 must be able to enter on realistic (premium_index == basis) ticks."""

    def test_extreme_negative_basis_enters_long(self) -> None:
        """Strongly negative basis (perp underpriced) -> Long reversion.

        PRD 4 M22: negative premium overflows the clamp -> reversion up.
        With the buggy gate this returned ``basis_wrong_direction`` and the
        strategy never entered.
        """
        strat = Strategy3PreSettlement()
        _warm_up_coupled(strat)

        # basis = -0.01 (perp 1% below index) -> P = -0.01
        # diff = I - P = 0.0003 - (-0.01) = 0.0103 ; clamp = +0.0005
        # pressure = 0.0103 - 0.0005 = +0.0098 (positive)
        result = strat.on_ticker(
            _coupled_ticker(basis=-0.01),
            seconds_to_settlement=900.0,
            open_interest=1100.0,
        )
        assert result["action"] == "enter", result["reason"]
        assert result["direction"] == 1  # Long

    def test_extreme_positive_basis_enters_short(self) -> None:
        """Strongly positive basis (perp overpriced) -> Short reversion."""
        strat = Strategy3PreSettlement()
        _warm_up_coupled(strat)

        # basis = +0.01 (perp 1% above index) -> P = +0.01
        # diff = I - P = -0.0097 ; clamp = -0.0005 ; pressure = -0.0092 (neg)
        result = strat.on_ticker(
            _coupled_ticker(basis=0.01),
            seconds_to_settlement=900.0,
            open_interest=1100.0,
        )
        assert result["action"] == "enter", result["reason"]
        assert result["direction"] == -1  # Short

    def test_alignment_gate_is_satisfiable(self) -> None:
        """For BOTH extreme signs of realistic basis the gate must pass.

        This is the direct proof of the bug: under the old gate
        (basis * sign(pressure) > 0) NEITHER extreme could ever align,
        so this assertion failed for the current code.
        """
        for basis in (-0.01, 0.01):
            strat = Strategy3PreSettlement()
            _warm_up_coupled(strat)
            result = strat.on_ticker(
                _coupled_ticker(basis=basis),
                seconds_to_settlement=900.0,
                open_interest=1100.0,
            )
            assert result["reason"] != "basis_wrong_direction", (
                f"alignment gate unsatisfiable for realistic basis={basis}"
            )
            assert result["action"] == "enter"
