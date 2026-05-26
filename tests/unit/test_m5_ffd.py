"""
Tests fuer M5 -- Fraktionale Differenzierung FFD.

Testet:
- Weight-Berechnung (d=0, d=1, Decay)
- FFD-Transform (Vergleich mit np.diff, Laengenerhaltung)
- Stationaritaet des Outputs
- Optimales d fuer Random Walk
- Reset
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.layers.l2_denoising.m5_ffd import M5FFD, _HAS_STATSMODELS


class TestFFDWeights:
    """Tests fuer die _compute_weights Methode."""

    def test_weights_d_zero(self) -> None:
        """d=0 -> weights = [1] (keine Differenzierung)."""
        mod = M5FFD()
        weights = mod._compute_weights(d=0.0, threshold=1e-4)
        assert len(weights) == 1
        assert weights[0] == pytest.approx(1.0)

    def test_weights_d_one(self) -> None:
        """d=1 -> weights = [1, -1] (einfache Differenzierung)."""
        mod = M5FFD()
        weights = mod._compute_weights(d=1.0, threshold=1e-4)
        assert len(weights) == 2
        assert weights[0] == pytest.approx(1.0)
        assert weights[1] == pytest.approx(-1.0)

    def test_weights_decay(self) -> None:
        """Weights werden mit steigendem k kleiner (Betrag)."""
        mod = M5FFD()
        weights = mod._compute_weights(d=0.5, threshold=1e-8)
        abs_weights = np.abs(weights)
        # Erstes Weight ist 1.0, danach monoton fallend
        assert abs_weights[0] == pytest.approx(1.0)
        for i in range(1, len(abs_weights) - 1):
            assert abs_weights[i] >= abs_weights[i + 1]

    def test_weights_d_half(self) -> None:
        """d=0.5: w_0=1, w_1=-0.5, w_2=-0.125, ..."""
        mod = M5FFD()
        weights = mod._compute_weights(d=0.5, threshold=1e-8)
        assert weights[0] == pytest.approx(1.0)
        assert weights[1] == pytest.approx(-0.5)
        # w_2 = w_1 * -(0.5 - 2 + 1) / 2 = -0.5 * -(-.5)/2 = -0.5 * 0.25 = -0.125
        assert weights[2] == pytest.approx(-0.125, abs=1e-10)


class TestFFDTransform:
    """Tests fuer die _ffd_transform Methode."""

    def test_ffd_integer_d_equals_diff(self) -> None:
        """d=1.0 -> FFD ist gleich wie np.diff (bis auf NaN-Padding)."""
        mod = M5FFD()
        series = np.array([100.0, 102.0, 101.0, 105.0, 103.0])
        transformed = mod._ffd_transform(series, d=1.0)
        expected_diff = np.diff(series)

        # Erstes Element ist NaN (nicht genug History)
        assert np.isnan(transformed[0])
        # Ab Index 1 sollte es np.diff entsprechen
        np.testing.assert_allclose(
            transformed[1:], expected_diff, atol=1e-10
        )

    def test_ffd_preserves_length(self) -> None:
        """Output hat gleiche Laenge wie Input."""
        mod = M5FFD()
        series = np.arange(100, dtype=np.float64)
        transformed = mod._ffd_transform(series, d=0.5)
        assert len(transformed) == len(series)

    def test_ffd_d_zero_identity(self) -> None:
        """d=0 -> Output = Input (keine Differenzierung)."""
        mod = M5FFD()
        series = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        transformed = mod._ffd_transform(series, d=0.0)
        np.testing.assert_allclose(transformed, series, atol=1e-10)

    @pytest.mark.skipif(not _HAS_STATSMODELS, reason="statsmodels not available")
    def test_ffd_stationary_output(self) -> None:
        """FFD-Output ist stationaerer als Input (Random Walk)."""
        from statsmodels.tsa.stattools import adfuller

        rng = np.random.default_rng(123)
        # Langer Random Walk fuer zuverlaessiges ADF-Ergebnis
        random_walk = np.cumsum(rng.standard_normal(2000))

        mod = M5FFD()
        # d=1.0 garantiert Stationaritaet (einfache Differenzierung)
        transformed = mod._ffd_transform(random_walk, d=1.0)
        valid = transformed[~np.isnan(transformed)]

        # ADF auf transformiert (sollte stationaer sein, p < 0.05)
        adf_transformed = adfuller(valid)
        p_transformed = adf_transformed[1]

        assert p_transformed < 0.05


class TestM5Module:
    """Tests fuer das M5FFD Modul."""

    @pytest.mark.skipif(not _HAS_STATSMODELS, reason="statsmodels not available")
    def test_optimal_d_random_walk(self) -> None:
        """Random Walk -> optimales d sollte zwischen 0.1 und 1.0 liegen."""
        rng = np.random.default_rng(42)
        random_walk = np.cumsum(rng.standard_normal(1000))

        mod = M5FFD()
        d = mod._find_optimal_d(random_walk)

        assert 0.1 <= d <= 1.0

    def test_compute_with_explicit_d(self) -> None:
        """compute() mit explizitem d funktioniert korrekt."""
        mod = M5FFD()
        series = np.arange(100, dtype=np.float64)
        result = mod.compute(series, d=0.5)

        assert result["method_id"] == "M5"
        assert result["signal"] == 0
        assert result["d"] == 0.5
        assert result["n_weights"] > 1
        assert len(result["transformed"]) == len(series)

    def test_reset(self) -> None:
        """Reset setzt internen State zurueck."""
        mod = M5FFD(default_d=0.4)
        mod._last_d = 0.7
        mod._last_adf_pvalue = 0.01

        mod.reset()

        assert mod._last_d == 0.4
        assert mod._last_adf_pvalue is None

    def test_validate(self) -> None:
        """validate() gibt True bei korrekter Konfiguration."""
        mod = M5FFD()
        assert mod.validate() is True

    def test_output_keys(self) -> None:
        """Prueft ob alle erwarteten Keys im Output vorhanden sind."""
        mod = M5FFD()
        result = mod.compute(np.arange(100, dtype=np.float64), d=0.5)
        expected_keys = {
            "transformed", "d", "adf_pvalue", "n_weights",
            "method_id", "signal", "confidence", "ts",
        }
        assert set(result.keys()) == expected_keys
