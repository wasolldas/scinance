"""
Tests fuer M6 -- Shannon-Entropie L2-Orderbuch.

Testet:
- Entropie-Berechnung (uniform, single, concentrated)
- Greenlight-Logik (niedrig vs. hoch)
- Edge Cases (leere Arrays, asymmetrisch)
- Reset
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from bybit_edge.layers.l3_regime.m6_entropy import (
    M6ShannonEntropy,
    _ENTROPY_HISTORY_MAXLEN,
    _MIN_SAMPLES_FOR_QUANTILE,
)


class TestShannonEntropyFunction:
    """Tests fuer die _shannon_entropy Methode."""

    def test_uniform_distribution_max_entropy(self) -> None:
        """Gleiche Sizes auf allen Levels -> H maximal = log2(N)."""
        mod = M6ShannonEntropy()
        sizes = np.ones(20, dtype=np.float64)
        h = mod._shannon_entropy(sizes)
        expected = math.log2(20)
        assert h == pytest.approx(expected, abs=1e-6)

    def test_single_level_zero_entropy(self) -> None:
        """Nur 1 Level mit Size > 0 -> H = 0 (log2(1) = 0)."""
        mod = M6ShannonEntropy()
        sizes = np.array([100.0])
        h = mod._shannon_entropy(sizes)
        assert h == pytest.approx(0.0, abs=1e-6)

    def test_concentrated_distribution_low_entropy(self) -> None:
        """Ein Level dominiert -> H niedrig (nahe 0)."""
        mod = M6ShannonEntropy()
        sizes = np.array([1000.0] + [0.001] * 19, dtype=np.float64)
        h = mod._shannon_entropy(sizes)
        # Entropie sollte nahe 0 sein (fast alles auf einem Level)
        h_max = math.log2(20)
        assert h < h_max * 0.1

    def test_two_equal_levels(self) -> None:
        """Zwei gleich grosse Levels -> H = log2(2) = 1.0."""
        mod = M6ShannonEntropy()
        sizes = np.array([50.0, 50.0])
        h = mod._shannon_entropy(sizes)
        assert h == pytest.approx(1.0, abs=1e-6)


class TestM6Module:
    """Tests fuer das M6ShannonEntropy Modul."""

    def test_greenlight_low_entropy(self) -> None:
        """H < Q5 -> greenlight=True."""
        mod = M6ShannonEntropy()

        # Erzeuge History mit hoher Entropie (uniform)
        uniform_sizes = np.ones(20, dtype=np.float64)
        for _ in range(_MIN_SAMPLES_FOR_QUANTILE + 10):
            mod.compute(uniform_sizes, uniform_sizes)

        # Jetzt ein stark konzentriertes Orderbuch -> niedrige Entropie
        concentrated = np.array([1000.0] + [0.001] * 19, dtype=np.float64)
        result = mod.compute(concentrated, concentrated)

        assert result["greenlight"] is True
        assert result["signal"] == 1
        assert result["confidence"] > 0.0

    def test_no_greenlight_high_entropy(self) -> None:
        """H > Q5 -> greenlight=False (uniforme Verteilung in History)."""
        mod = M6ShannonEntropy()

        # Erzeuge History mit uniformer Entropie
        uniform_sizes = np.ones(20, dtype=np.float64)
        for _ in range(_MIN_SAMPLES_FOR_QUANTILE + 10):
            result = mod.compute(uniform_sizes, uniform_sizes)

        # Uniform bleibt -> sollte ueber Q5 liegen (da alle gleich, H == Q5 genau)
        # Letztes Ergebnis: H == Median, nicht < Q5
        assert result["greenlight"] is False
        assert result["signal"] == 0

    def test_empty_sizes_no_crash(self) -> None:
        """Leere Arrays -> kein Crash, H = 0."""
        mod = M6ShannonEntropy()
        result = mod.compute(np.array([]), np.array([]))
        assert result["h_bid"] == 0.0
        assert result["h_ask"] == 0.0
        assert result["h_combined"] == 0.0
        assert result["method_id"] == "M6"

    def test_asymmetric_bid_ask(self) -> None:
        """Unterschiedliche Bid/Ask-Verteilungen -> H_combined ist Mittelwert."""
        mod = M6ShannonEntropy()
        # Bid: uniform (hohe H), Ask: konzentriert (niedrige H)
        bid_sizes = np.ones(20, dtype=np.float64)
        ask_sizes = np.array([1000.0] + [0.001] * 19, dtype=np.float64)
        result = mod.compute(bid_sizes, ask_sizes)

        h_bid = result["h_bid"]
        h_ask = result["h_ask"]
        h_combined = result["h_combined"]

        assert h_bid > h_ask
        assert h_combined == pytest.approx((h_bid + h_ask) / 2.0, abs=1e-10)

    def test_reset(self) -> None:
        """Reset setzt alle internen Zustaende zurueck."""
        mod = M6ShannonEntropy()

        # Fuettere mit Daten
        uniform_sizes = np.ones(20, dtype=np.float64)
        for _ in range(50):
            mod.compute(uniform_sizes, uniform_sizes)

        mod.reset()

        assert len(mod._h_history) == 0
        assert mod._h_q5 == float("inf")

    def test_validate(self) -> None:
        """validate() gibt True bei korrekter Konfiguration."""
        mod = M6ShannonEntropy()
        assert mod.validate() is True

    def test_output_keys(self) -> None:
        """Prueft ob alle erwarteten Keys im Output vorhanden sind."""
        mod = M6ShannonEntropy()
        result = mod.compute(np.ones(20), np.ones(20))
        expected_keys = {
            "greenlight", "h_bid", "h_ask", "h_combined", "h_q5",
            "signal", "method_id", "confidence", "ts",
        }
        assert set(result.keys()) == expected_keys

    def test_zero_sizes_no_crash(self) -> None:
        """Alle Sizes = 0 -> kein Crash, H = 0."""
        mod = M6ShannonEntropy()
        result = mod.compute(np.zeros(20), np.zeros(20))
        assert result["h_bid"] == 0.0
        assert result["h_ask"] == 0.0
