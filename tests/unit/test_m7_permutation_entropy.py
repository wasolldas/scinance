"""
Tests fuer M7 -- Permutation Entropy (Bandt-Pompe).

Testet:
- PE fuer konstante, monotone und zufaellige Serien
- Analytisch bekannte Werte
- Greenlight-Logik
- Insufficient-Data-Verhalten
- Reset
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from bybit_edge.config import PE_DELAY, PE_ORDER, PE_WINDOW_TICKS
from bybit_edge._legacy_v1.layers.l3_regime.m7_permutation_entropy import (
    M7PermutationEntropy,
    _permutation_entropy,
)


class TestPermutationEntropyFunction:
    """Tests fuer die standalone _permutation_entropy Funktion."""

    def test_pe_constant_series(self) -> None:
        """Konstante Serie -> alle Muster gleich -> PE = 0."""
        prices = np.array([42.0] * 50)
        pe = _permutation_entropy(prices, order=3, delay=1)
        assert pe == pytest.approx(0.0, abs=1e-10)

    def test_pe_random_series(self) -> None:
        """Zufaellige Serie -> PE nahe 1.0 (maximal)."""
        rng = np.random.default_rng(42)
        prices = rng.standard_normal(10_000)
        pe = _permutation_entropy(prices, order=3, delay=1)
        # Fuer grosse zufaellige Serien sollte PE nahe 1.0 liegen
        assert pe > 0.95
        assert pe <= 1.0

    def test_pe_monotonic_increasing(self) -> None:
        """Streng monoton steigende Serie -> nur ein Muster -> PE = 0."""
        prices = np.arange(100, dtype=np.float64)
        pe = _permutation_entropy(prices, order=3, delay=1)
        assert pe == pytest.approx(0.0, abs=1e-10)

    def test_pe_monotonic_decreasing(self) -> None:
        """Streng monoton fallende Serie -> nur ein Muster -> PE = 0."""
        prices = np.arange(100, 0, -1, dtype=np.float64)
        pe = _permutation_entropy(prices, order=3, delay=1)
        assert pe == pytest.approx(0.0, abs=1e-10)

    def test_pe_known_value_order2(self) -> None:
        """Analytisch bekannt: alternierend [1,2,1,2,...] mit order=2.

        Muster: (0,1) fuer Aufstieg, (1,0) fuer Abstieg.
        50% jedes Muster -> PE = log(2)/log(2!) = log(2)/log(2) = 1.0
        """
        prices = np.array([1.0, 2.0] * 50)
        pe = _permutation_entropy(prices, order=2, delay=1)
        assert pe == pytest.approx(1.0, abs=0.05)

    def test_pe_known_value_order3_periodic(self) -> None:
        """Periodische Serie [1,2,3,1,2,3,...] mit order=3.

        Embeddings cross period boundaries producing 3 distinct patterns:
        (1,2,3)->(0,1,2), (2,3,1)->(2,0,1), (3,1,2)->(1,2,0).
        Each appears equally often -> PE = log(3)/log(3!) = log(3)/log(6).
        """
        prices = np.tile([1.0, 2.0, 3.0], 50)
        pe = _permutation_entropy(prices, order=3, delay=1)
        expected = math.log(3) / math.log(math.factorial(3))
        assert pe == pytest.approx(expected, abs=0.02)

    def test_pe_insufficient_data(self) -> None:
        """Zu wenig Daten fuer Embedding -> PE = 0.0."""
        prices = np.array([1.0, 2.0])  # Braucht min (3-1)*1+1 = 3 bei order=3
        pe = _permutation_entropy(prices, order=3, delay=1)
        assert pe == 0.0

    def test_pe_with_delay(self) -> None:
        """PE mit delay > 1 funktioniert korrekt."""
        prices = np.arange(200, dtype=np.float64)
        pe = _permutation_entropy(prices, order=3, delay=2)
        # Monoton steigend, auch mit delay -> PE = 0
        assert pe == pytest.approx(0.0, abs=1e-10)


class TestM7Module:
    """Tests fuer das M7PermutationEntropy Modul."""

    def test_greenlight_ordered_market(self) -> None:
        """PE < Median -> Greenlight = True."""
        mod = M7PermutationEntropy()

        # Fuettere erstmal mit zufaelligen Preisen um hohe PE history aufzubauen
        rng = np.random.default_rng(123)
        random_prices = rng.standard_normal(PE_WINDOW_TICKS + 50) * 100 + 50000
        for p in random_prices:
            mod.update(float(p))

        # Jetzt monotone Preise -> PE wird niedrig -> unter dem Median
        for i in range(PE_WINDOW_TICKS):
            result = mod.update(60000.0 + i * 0.01)

        assert result["greenlight"] is True
        assert result["signal"] == 1

    def test_no_greenlight_chaotic(self) -> None:
        """PE >= Median -> Greenlight = False nach geordneter History."""
        mod = M7PermutationEntropy()

        # Monotone Preise als History (niedrige PE)
        for i in range(PE_WINDOW_TICKS + 50):
            mod.update(50000.0 + i * 0.01)

        # Jetzt zufaellige Preise (hohe PE)
        rng = np.random.default_rng(999)
        for _ in range(PE_WINDOW_TICKS):
            result = mod.update(float(rng.standard_normal() * 100 + 50000))

        assert result["greenlight"] is False
        assert result["signal"] == 0

    def test_insufficient_data(self) -> None:
        """Zu wenig Preise -> greenlight=False."""
        mod = M7PermutationEntropy()
        for i in range(PE_WINDOW_TICKS - 1):
            result = mod.update(100.0 + i)
        assert result["greenlight"] is False
        assert math.isnan(result["pe"])

    def test_reset(self) -> None:
        """Reset setzt alle internen Zustaende zurueck."""
        mod = M7PermutationEntropy()
        for i in range(PE_WINDOW_TICKS + 10):
            mod.update(100.0 + i)

        mod.reset()

        assert len(mod._prices) == 0
        assert len(mod._pe_history) == 0
        assert mod._pe_median == float("inf")

    def test_compute_delegates_to_update(self) -> None:
        """compute() ist ein Wrapper um update()."""
        mod = M7PermutationEntropy()
        result = mod.compute(price=42000.0)
        assert result["method_id"] == "M7"
        assert "pe" in result
        assert "greenlight" in result

    def test_validate(self) -> None:
        """validate() gibt True bei korrekter Konfiguration."""
        mod = M7PermutationEntropy()
        assert mod.validate() is True

    def test_pe_value_range(self) -> None:
        """PE-Wert liegt immer in [0, 1] nach genuegend Daten."""
        mod = M7PermutationEntropy()
        rng = np.random.default_rng(42)
        for i in range(PE_WINDOW_TICKS + 10):
            result = mod.update(float(rng.standard_normal() * 100 + 50000))

        pe = result["pe"]
        assert 0.0 <= pe <= 1.0
