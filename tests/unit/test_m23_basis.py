"""
Tests für M23 — Mark-Index Basis Settlement Convergence.

Testet:
- Korrekte Basis-Berechnung
- Short-Signal bei positiver Basis im Window
- Long-Signal bei negativer Basis im Window
- Kein Signal außerhalb des Settlement-Windows
- Kein Signal bei kleiner Basis (innerhalb Threshold)
"""

from __future__ import annotations

import pytest

from bybit_edge.config import (
    BASIS_ENTRY_WINDOW_MINUTES,
    BASIS_LONG_THRESHOLD,
    BASIS_SHORT_THRESHOLD,
)
from bybit_edge.layers.l5_risk.m23_basis_convergence import M23BasisConvergence


def _make_ticker(mark_price: float, index_price: float) -> dict:
    """Erzeugt minimales ticker_data dict."""
    return {
        "mark_price": mark_price,
        "index_price": index_price,
    }


class TestBasisCalculation:
    """Test korrekte Basis-Berechnung."""

    def test_basis_calculation(self) -> None:
        """Basis = (mark - index) / index."""
        mod = M23BasisConvergence()

        mark = 100_100.0
        index = 100_000.0
        expected_basis = (mark - index) / index  # 0.001

        result = mod.compute(
            _make_ticker(mark, index),
            seconds_to_settlement=1800.0,
        )

        assert result["basis"] == pytest.approx(expected_basis, abs=1e-12)
        assert result["method_id"] == "M23"

    def test_basis_zero_when_equal(self) -> None:
        """Wenn mark == index → Basis == 0."""
        mod = M23BasisConvergence()
        result = mod.compute(
            _make_ticker(100_000.0, 100_000.0),
            seconds_to_settlement=1800.0,
        )
        assert result["basis"] == pytest.approx(0.0, abs=1e-12)

    def test_basis_zero_index_zero(self) -> None:
        """Wenn index_price == 0 → Division-by-Zero sicher, Basis == 0."""
        mod = M23BasisConvergence()
        result = mod.compute(
            _make_ticker(100_000.0, 0.0),
            seconds_to_settlement=1800.0,
        )
        assert result["basis"] == 0.0
        assert result["signal"] == 0


class TestShortSignal:
    """Test Short-Signal bei positiver Basis im Window."""

    def test_short_signal_positive_basis(self) -> None:
        """Basis > 0.0008 in Window → Signal -1 (Short)."""
        mod = M23BasisConvergence()

        # mark = 100_100, index = 100_000 → basis = 0.001 > 0.0008
        result = mod.compute(
            _make_ticker(100_100.0, 100_000.0),
            seconds_to_settlement=1800.0,  # 30 min < 60 min Window
        )

        assert result["signal"] == -1
        assert result["in_window"] is True
        assert result["basis"] > BASIS_SHORT_THRESHOLD

    def test_short_signal_exactly_at_threshold(self) -> None:
        """Basis exakt am Threshold — muss Signal geben wenn > Threshold."""
        mod = M23BasisConvergence()

        # Basis exakt etwas über dem Threshold
        index = 100_000.0
        mark = index * (1 + BASIS_SHORT_THRESHOLD + 1e-9)

        result = mod.compute(
            _make_ticker(mark, index),
            seconds_to_settlement=1800.0,
        )
        assert result["signal"] == -1


class TestLongSignal:
    """Test Long-Signal bei negativer Basis im Window."""

    def test_long_signal_negative_basis(self) -> None:
        """Basis < -0.0008 in Window → Signal 1 (Long)."""
        mod = M23BasisConvergence()

        # mark = 99_900, index = 100_000 → basis = -0.001 < -0.0008
        result = mod.compute(
            _make_ticker(99_900.0, 100_000.0),
            seconds_to_settlement=1800.0,
        )

        assert result["signal"] == 1
        assert result["in_window"] is True
        assert result["basis"] < BASIS_LONG_THRESHOLD


class TestNoSignalOutsideWindow:
    """Test kein Signal außerhalb des Settlement-Windows."""

    def test_no_signal_outside_window(self) -> None:
        """Extremer Basis, aber außerhalb Window → Signal == 0."""
        mod = M23BasisConvergence()

        result = mod.compute(
            _make_ticker(100_100.0, 100_000.0),
            seconds_to_settlement=7200.0,  # 2h >> 1h Window
        )

        assert result["signal"] == 0
        assert result["in_window"] is False

    def test_no_signal_negative_seconds(self) -> None:
        """Negative seconds_to_settlement (nach Settlement) → kein Signal."""
        mod = M23BasisConvergence()

        result = mod.compute(
            _make_ticker(100_100.0, 100_000.0),
            seconds_to_settlement=-100.0,
        )

        assert result["signal"] == 0
        assert result["in_window"] is False


class TestNoSignalSmallBasis:
    """Test kein Signal bei kleiner Basis."""

    def test_no_signal_small_basis(self) -> None:
        """Basis innerhalb [-0.0008, +0.0008] → kein Signal."""
        mod = M23BasisConvergence()

        # mark = 100_010, index = 100_000 → basis = 0.0001 (innerhalb Threshold)
        result = mod.compute(
            _make_ticker(100_010.0, 100_000.0),
            seconds_to_settlement=1800.0,
        )

        assert result["signal"] == 0
        assert abs(result["basis"]) < BASIS_SHORT_THRESHOLD

    def test_no_signal_basis_zero(self) -> None:
        """Basis == 0 → kein Signal."""
        mod = M23BasisConvergence()

        result = mod.compute(
            _make_ticker(100_000.0, 100_000.0),
            seconds_to_settlement=1800.0,
        )

        assert result["signal"] == 0


class TestReturnFormat:
    """Test dass alle Required-Keys vorhanden sind."""

    def test_all_keys_present(self) -> None:
        mod = M23BasisConvergence()
        result = mod.compute(
            _make_ticker(100_000.0, 100_000.0),
            seconds_to_settlement=1800.0,
        )

        required_keys = {"signal", "basis", "in_window", "method_id", "confidence", "ts"}
        assert required_keys.issubset(result.keys())

    def test_signal_in_valid_range(self) -> None:
        mod = M23BasisConvergence()
        result = mod.compute(
            _make_ticker(100_000.0, 100_000.0),
            seconds_to_settlement=1800.0,
        )
        assert result["signal"] in {-1, 0, 1}

    def test_confidence_in_range(self) -> None:
        mod = M23BasisConvergence()
        result = mod.compute(
            _make_ticker(100_100.0, 100_000.0),
            seconds_to_settlement=1800.0,
        )
        assert 0.0 <= result["confidence"] <= 1.0


class TestValidate:
    """Test validate() Methode."""

    def test_validate_returns_true(self) -> None:
        mod = M23BasisConvergence()
        assert mod.validate() is True


class TestReset:
    """Test reset() — M23 hat keinen State."""

    def test_reset_no_crash(self) -> None:
        mod = M23BasisConvergence()
        mod.reset()  # Sollte ohne Fehler durchlaufen
        result = mod.compute(
            _make_ticker(100_000.0, 100_000.0),
            seconds_to_settlement=1800.0,
        )
        assert result["signal"] == 0
