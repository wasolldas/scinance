"""
Tests fuer M21 -- Long/Short-Ratio Smart-Money Divergenz.

Testet:
- Retail long + Preis faellt -> short signal
- Retail short + Preis steigt -> long signal
- Kein Signal bei moderater Ratio
- Kein Signal bei aligned Ratio/Preis
- Boundary Ratio
- Zero Return
- Return Keys
- Reset
"""

from __future__ import annotations

import pytest

from bybit_edge.layers.l4_pattern.m21_ls_ratio import M21LSRatio


class TestM21LSRatio:
    """Tests fuer das M21LSRatio Modul."""

    def test_retail_long_price_falls_short_signal(self) -> None:
        """buyRatio > 0.75 und return < 0 -> signal = -1 (Short folgen)."""
        mod = M21LSRatio()
        result = mod.compute(
            buy_ratio=0.80,
            return_1h=-0.02,
            current_ts=1000.0,
        )
        assert result["signal"] == -1
        assert result["extreme_skew"] is True
        assert result["divergence"] < 0
        assert result["confidence"] > 0.0

    def test_retail_short_price_rises_long_signal(self) -> None:
        """buyRatio < 0.25 und return > 0 -> signal = +1 (Long folgen)."""
        mod = M21LSRatio()
        result = mod.compute(
            buy_ratio=0.20,
            return_1h=0.03,
            current_ts=1000.0,
        )
        assert result["signal"] == 1
        assert result["extreme_skew"] is True
        assert result["divergence"] > 0
        assert result["confidence"] > 0.0

    def test_no_signal_moderate_ratio(self) -> None:
        """buyRatio ~ 0.5 -> kein extremer Skew -> signal = 0."""
        mod = M21LSRatio()
        result = mod.compute(
            buy_ratio=0.52,
            return_1h=-0.01,
            current_ts=1000.0,
        )
        assert result["signal"] == 0
        assert result["extreme_skew"] is False

    def test_no_signal_aligned(self) -> None:
        """buyRatio > 0.75 und Preis steigt -> Retail und Preis aligned -> signal = 0."""
        mod = M21LSRatio()
        result = mod.compute(
            buy_ratio=0.80,
            return_1h=0.02,
            current_ts=1000.0,
        )
        # Retail long und Preis steigt -> keine Divergenz -> signal = 0
        assert result["signal"] == 0

    def test_boundary_ratio(self) -> None:
        """buyRatio genau auf Grenzwert (0.75) -> |buyRatio - 0.5| = 0.25 -> nicht extrem."""
        mod = M21LSRatio()
        result = mod.compute(
            buy_ratio=0.75,
            return_1h=-0.01,
            current_ts=1000.0,
        )
        # |0.75 - 0.5| = 0.25 = threshold -> nicht > threshold -> kein Signal
        assert result["signal"] == 0
        assert result["extreme_skew"] is False

    def test_zero_return(self) -> None:
        """return_1h = 0 -> sign(return) = 0 -> kein klares Signal."""
        mod = M21LSRatio()
        result = mod.compute(
            buy_ratio=0.90,
            return_1h=0.0,
            current_ts=1000.0,
        )
        # sign(0) = 0, divergence = 0 - 1 = -1 aber return = 0
        # -> signal bleibt 0, da return_1h weder < 0 noch > 0
        assert result["signal"] == 0

    def test_return_keys(self) -> None:
        """Prueft ob alle erwarteten Keys im Output vorhanden sind."""
        mod = M21LSRatio()
        result = mod.compute(
            buy_ratio=0.50,
            return_1h=0.01,
            current_ts=1000.0,
        )
        expected_keys = {
            "divergence", "buy_ratio", "extreme_skew", "signal",
            "method_id", "confidence", "ts",
        }
        assert set(result.keys()) == expected_keys
        assert result["method_id"] == "M21"

    def test_reset(self) -> None:
        """Reset wirft keinen Fehler (M21 ist stateless)."""
        mod = M21LSRatio()
        mod.compute(buy_ratio=0.80, return_1h=-0.01, current_ts=1000.0)
        mod.reset()
        # Nach Reset funktioniert alles weiterhin
        result = mod.compute(buy_ratio=0.20, return_1h=0.03, current_ts=1000.0)
        assert result["signal"] == 1
