"""
Tests fuer M3 -- Iceberg Detection.

Testet:
- Kein Iceberg ohne Replenishment
- Iceberg erkannt bei Replenishment mit Score > 0.7 und N > 5
- Zu wenige Hits -> kein Iceberg
- Niedriger Score -> kein Iceberg
- Mehrere Levels
- Leere Levels crashen nicht
- Return-Keys
- Reset
"""

from __future__ import annotations

import pytest

from bybit_edge.layers.l1_ingestion.m3_iceberg import M3IcebergDetector


class TestM3IcebergDetector:
    """Tests fuer das Iceberg-Detection-Modul."""

    def test_no_iceberg_no_replenishment(self) -> None:
        """Level verschwindet nach Trade -> kein Iceberg."""
        mod = M3IcebergDetector()
        price = 50000.0

        # Level initial setzen
        mod.on_orderbook_update(price, 10.0, ts=1.0)
        # Trade trifft das Level
        mod.on_trade(price, ts=2.0)
        # Level NICHT wieder aufgefuellt (Size = 0)
        mod.on_orderbook_update(price, 0.0, ts=3.0)

        result = mod.compute(levels={price: 0.0}, recent_trades=[], ts=4.0)
        assert result["n_icebergs_detected"] == 0
        assert result["signal"] == 0

    def test_iceberg_detected(self) -> None:
        """Level refilled nach Trade, Score > 0.7, N > 5 -> Iceberg."""
        mod = M3IcebergDetector()
        price = 50000.0

        # Simuliere 8 Zyklen von: Level setzen -> Trade -> Replenishment
        for i in range(8):
            t_base = float(i * 3)
            mod.on_orderbook_update(price, 10.0, ts=t_base)
            mod.on_trade(price, ts=t_base + 1.0)
            # Replenishment: Size >= 80% von 10.0 = 8.0
            mod.on_orderbook_update(price, 9.0, ts=t_base + 2.0)

        result = mod.compute(levels={price: 10.0}, recent_trades=[], ts=30.0)
        assert result["n_icebergs_detected"] >= 1
        assert result["signal"] == 1
        assert len(result["iceberg_levels"]) >= 1
        assert result["iceberg_levels"][0]["score"] > 0.7

    def test_insufficient_hits(self) -> None:
        """N_hits < 5 -> kein Iceberg auch bei perfektem Replenishment."""
        mod = M3IcebergDetector()
        price = 50000.0

        # Nur 3 Zyklen (weniger als Minimum 5)
        for i in range(3):
            t_base = float(i * 3)
            mod.on_orderbook_update(price, 10.0, ts=t_base)
            mod.on_trade(price, ts=t_base + 1.0)
            mod.on_orderbook_update(price, 10.0, ts=t_base + 2.0)

        result = mod.compute(levels={price: 10.0}, recent_trades=[], ts=15.0)
        assert result["n_icebergs_detected"] == 0
        assert result["signal"] == 0

    def test_low_score_no_detection(self) -> None:
        """Score < 0.7 -> kein Iceberg (meistens kein Replenishment)."""
        mod = M3IcebergDetector()
        price = 50000.0

        # 8 Hits aber nur 2 Replenishments -> Score = 2/8 = 0.25
        for i in range(8):
            t_base = float(i * 3)
            mod.on_orderbook_update(price, 10.0, ts=t_base)
            mod.on_trade(price, ts=t_base + 1.0)
            if i < 2:
                # Replenishment
                mod.on_orderbook_update(price, 9.0, ts=t_base + 2.0)
            else:
                # Kein Replenishment (zu kleine Size)
                mod.on_orderbook_update(price, 1.0, ts=t_base + 2.0)

        result = mod.compute(levels={price: 1.0}, recent_trades=[], ts=30.0)
        assert result["n_icebergs_detected"] == 0
        assert result["signal"] == 0

    def test_multiple_levels(self) -> None:
        """Mehrere Levels koennen gleichzeitig als Iceberg erkannt werden."""
        mod = M3IcebergDetector()
        prices = [50000.0, 51000.0]

        for price in prices:
            for i in range(8):
                t_base = float(i * 3)
                mod.on_orderbook_update(price, 10.0, ts=t_base)
                mod.on_trade(price, ts=t_base + 1.0)
                mod.on_orderbook_update(price, 9.5, ts=t_base + 2.0)

        levels = {p: 10.0 for p in prices}
        result = mod.compute(levels=levels, recent_trades=[], ts=30.0)
        assert result["n_icebergs_detected"] >= 2

    def test_empty_levels_no_crash(self) -> None:
        """Leere Levels und keine Trades crashen nicht."""
        mod = M3IcebergDetector()
        result = mod.compute(levels={}, recent_trades=[], ts=1.0)
        assert result["n_icebergs_detected"] == 0
        assert result["signal"] == 0
        assert result["iceberg_levels"] == []

    def test_return_keys(self) -> None:
        """Compute gibt alle erwarteten Keys zurueck."""
        mod = M3IcebergDetector()
        result = mod.compute(levels={50000.0: 5.0}, recent_trades=[], ts=1.0)
        expected_keys = {
            "iceberg_levels", "n_icebergs_detected",
            "signal", "method_id", "confidence", "ts",
        }
        assert set(result.keys()) == expected_keys
        assert result["method_id"] == "M3"
        assert result["signal"] in (-1, 0, 1)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_reset(self) -> None:
        """Reset loescht alle Level-Historien."""
        mod = M3IcebergDetector()
        mod.on_orderbook_update(50000.0, 10.0, ts=1.0)
        mod.on_trade(50000.0, ts=2.0)
        assert len(mod._level_history) > 0

        mod.reset()
        assert len(mod._level_history) == 0
