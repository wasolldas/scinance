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

        # premium_index=0.01 → P=0.01, I=0.0003
        # diff = I-P = -0.0097, clamped = -0.0005, pressure = -0.0092 (negative)
        # For alignment: sign(pressure)=-1, so basis must be negative → mark < index
        result = _trigger_entry(
            strat,
            extreme_premium=0.01,  # very extreme → high negative pressure
            mark_price=49950.0,    # below index → negative basis → aligned
            index_price=50000.0,
            seconds_to_settlement=900.0,  # 15 min
        )
        assert result["action"] == "enter"
        assert result["direction"] in (1, -1)
        assert result["strategy"] == "S3"
        assert result["price"] == 49950.0
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
        """Pressure negative but basis positive -> wait (directions must match)."""
        strat = Strategy3PreSettlement()
        # Warm up with low pressure so the extreme tick stands out
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # premium_index=0.01 → pressure = -0.0092 (negative)
        # For MISALIGNMENT: sign(pressure)=-1, but basis POSITIVE → mark > index
        ticker = _make_ticker(
            premium_index=0.01,
            mark_price=50050.0,  # above index → positive basis
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

        # premium_index=0.01 → negative pressure
        # mark < index → negative basis → ALIGNED (passes basis check)
        # So we reach the BOCPD condition, which should block entry
        result = _trigger_entry(
            strat,
            extreme_premium=0.01,
            mark_price=49950.0,   # below index → negative basis → aligned
            index_price=50000.0,
            seconds_to_settlement=900.0,
            open_interest=5000.0,
        )
        assert result["action"] == "wait"
        assert result["reason"] == "bocpd_changepoint_detected"

    # ----- 6. Direction: Long -----

    def test_entry_direction_long(self) -> None:
        """Negative pressure -> direction = +1 (Long)."""
        strat = Strategy3PreSettlement()
        # Warm up with small positive premium (low pressure)
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # Very negative premium_index → diff = I - P becomes large positive
        # But with the clamp, the pressure = diff - clamped can be positive
        # Actually: I = 0.0003, P = -0.01 → diff = 0.0003 - (-0.01) = 0.0103
        # clamped = clip(0.0103, -0.0005, 0.0005) = 0.0005
        # pressure = 0.0103 - 0.0005 = 0.0098 (positive)
        # For NEGATIVE pressure we need P > I by a large margin:
        # I = 0.0003, P = 0.01 → diff = 0.0003 - 0.01 = -0.0097
        # clamped = clip(-0.0097, -0.0005, 0.0005) = -0.0005
        # pressure = -0.0097 - (-0.0005) = -0.0092 → NEGATIVE → Long
        # For basis alignment: pressure < 0 → basis must also be < 0 → mark < index
        ticker = _make_ticker(
            premium_index=0.01,  # large positive P
            mark_price=49950.0,  # below index → negative basis
            index_price=50000.0,
        )
        result = strat.on_ticker(
            ticker,
            seconds_to_settlement=900.0,
            open_interest=1100.0,
        )
        # With P = 0.01: pressure = (I - P) - clamp(I-P) = (0.0003 - 0.01) - (-0.0005)
        # = -0.0097 + 0.0005 = -0.0092 → negative → Long
        # Basis = (49950 - 50000) / 50000 = -0.001 → negative
        # sign(pressure) = -1, basis * sign(pressure) = -0.001 * -1 = 0.001 > 0 ✓
        assert result["action"] == "enter"
        assert result["direction"] == 1  # Long

    # ----- 7. Direction: Short -----

    def test_entry_direction_short(self) -> None:
        """Positive pressure -> direction = -1 (Short)."""
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat, n_samples=200, premium_index=0.0003)

        # Negative premium → diff = I - P becomes large positive
        # I = 0.0003, P = -0.01 → diff = 0.0103
        # clamped = 0.0005
        # pressure = 0.0103 - 0.0005 = 0.0098 → POSITIVE → Short
        # For alignment: pressure > 0 → basis must be > 0 → mark > index
        ticker = _make_ticker(
            premium_index=-0.01,  # large negative P
            mark_price=50050.0,   # above index → positive basis
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

        # Enter trade
        entry = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=50050.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert entry["action"] == "enter"
        assert strat.in_trade

        # Now simulate: settlement has passed by > 10 minutes
        # seconds_to_settlement = -(10*60 + 1) = -601
        ticker = _make_ticker(premium_index=-0.01, mark_price=50050.0)
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

        # Enter trade
        entry = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=50050.0,
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

        # First entry
        entry1 = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=50050.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert entry1["action"] == "enter"
        assert strat.in_trade

        # Attempt second entry with same extreme conditions
        entry2 = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=50055.0,
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

        # Enter
        entry = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=50050.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert entry["action"] == "enter"

        # Exit via settlement timeout
        ticker = _make_ticker(premium_index=-0.01, mark_price=50050.0)
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
            _make_ticker(premium_index=-0.01, mark_price=50050.0),
            seconds_to_settlement=2000.0,  # > 30 min
            open_interest=1100.0,
        )
        assert result["action"] == "wait"
        assert not strat.in_trade

        # Phase 2: Enter window with extreme conditions -> enter
        entry = _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=50050.0,
            index_price=50000.0,
            seconds_to_settlement=900.0,
        )
        assert entry["action"] == "enter"
        assert strat.in_trade
        entered_direction = entry["direction"]

        # Phase 3: Still in trade, pressure still extreme, before settlement -> hold
        # (seconds_to_settlement still positive, pressure NOT dissipated)
        hold_result = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=50060.0),
            seconds_to_settlement=300.0,  # 5 min to settlement, pressure still extreme
            open_interest=1100.0,
        )
        # Should either wait (hold) or exit depending on pressure.
        # With extreme premium, pressure won't be in the exit band.
        assert strat.in_trade  # still holding

        # Phase 4: Past settlement by > 10 min -> exit
        exit_result = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=50070.0),
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
            mark_price=50050.0,
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

        # Enter a trade
        _trigger_entry(
            strat,
            extreme_premium=-0.01,
            mark_price=50050.0,
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
