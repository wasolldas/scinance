"""
Tests fuer M4 -- Wavelet-Symlet-Denoising.

Testet:
- Denoising eines verrauschten Sinussignals
- Konstantes Signal bleibt unveraendert
- Soft-Threshold Verhalten
- VisuShrink Schwellwertberechnung
- Output-Laenge
- SNR-Verbesserung
- Kurze Signale
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from bybit_edge.layers.l2_denoising.m4_wavelet import M4WaveletDenoiser


class TestSoftThreshold:
    """Tests fuer die _soft_threshold Methode."""

    def test_soft_threshold_zeros_small_values(self) -> None:
        """Werte kleiner als Threshold werden zu 0."""
        mod = M4WaveletDenoiser()
        coeffs = np.array([0.1, -0.2, 0.05, -0.15])
        threshold = 0.3
        result = mod._soft_threshold(coeffs, threshold)
        np.testing.assert_array_equal(result, np.zeros(4))

    def test_soft_threshold_preserves_large_values(self) -> None:
        """Werte groesser als Threshold werden geschrumpft, nicht geloescht."""
        mod = M4WaveletDenoiser()
        coeffs = np.array([1.0, -1.0, 0.5, -0.5])
        threshold = 0.3
        result = mod._soft_threshold(coeffs, threshold)
        expected = np.array([0.7, -0.7, 0.2, -0.2])
        np.testing.assert_allclose(result, expected, atol=1e-10)

    def test_soft_threshold_sign_preserved(self) -> None:
        """Vorzeichen wird korrekt erhalten."""
        mod = M4WaveletDenoiser()
        coeffs = np.array([5.0, -5.0])
        result = mod._soft_threshold(coeffs, 2.0)
        assert result[0] > 0
        assert result[1] < 0


class TestVisuShrink:
    """Tests fuer die _visushrink_threshold Methode."""

    def test_visushrink_threshold_calculation(self) -> None:
        """VisuShrink: lambda = sigma * sqrt(2 * log(N))."""
        mod = M4WaveletDenoiser()
        # Bekannte Werte: wenn alle detail_coeffs = 1.0,
        # MAD = median(|1.0|) = 1.0, sigma = 1.0/0.6745
        coeffs = np.ones(100, dtype=np.float64)
        threshold = mod._visushrink_threshold(coeffs)
        sigma = 1.0 / 0.6745
        expected = sigma * math.sqrt(2.0 * math.log(100))
        assert threshold == pytest.approx(expected, rel=1e-6)

    def test_visushrink_empty_coeffs(self) -> None:
        """Leere Koeffizienten -> Threshold = 0."""
        mod = M4WaveletDenoiser()
        threshold = mod._visushrink_threshold(np.array([]))
        assert threshold == 0.0

    def test_visushrink_all_zeros(self) -> None:
        """Alle Koeffizienten = 0 -> sigma = 0 -> Threshold = 0."""
        mod = M4WaveletDenoiser()
        threshold = mod._visushrink_threshold(np.zeros(50))
        assert threshold == 0.0


class TestM4Module:
    """Tests fuer das M4WaveletDenoiser Modul."""

    def test_denoise_noisy_sine(self) -> None:
        """Sinus + Noise -> denoised ist naeher am Original."""
        mod = M4WaveletDenoiser(wavelet="sym6", level=4)
        rng = np.random.default_rng(42)

        t = np.linspace(0, 4 * np.pi, 256)
        clean = np.sin(t)
        noise = rng.standard_normal(256) * 0.5
        noisy = clean + noise

        result = mod.compute(noisy)
        denoised = result["denoised"]

        # Denoised sollte naeher am Original sein als das verrauschte Signal
        error_noisy = np.mean((noisy - clean) ** 2)
        error_denoised = np.mean((denoised - clean) ** 2)
        assert error_denoised < error_noisy

    def test_denoise_constant_signal(self) -> None:
        """Konstantes Signal -> bleibt (fast) unveraendert."""
        mod = M4WaveletDenoiser(wavelet="sym6", level=4)
        signal = np.full(256, 42.0, dtype=np.float64)
        result = mod.compute(signal)
        denoised = result["denoised"]
        np.testing.assert_allclose(denoised, signal, atol=1e-10)

    def test_output_same_length(self) -> None:
        """denoised.shape == input.shape."""
        mod = M4WaveletDenoiser(wavelet="sym6", level=4)
        rng = np.random.default_rng(42)
        signal = rng.standard_normal(256)
        result = mod.compute(signal)
        assert result["denoised"].shape == signal.shape

    def test_snr_improvement_positive(self) -> None:
        """SNR verbessert sich bei verrauschtem Signal."""
        mod = M4WaveletDenoiser(wavelet="sym6", level=4)
        rng = np.random.default_rng(42)

        t = np.linspace(0, 4 * np.pi, 256)
        clean = np.sin(t) * 5.0
        noise = rng.standard_normal(256) * 1.0
        noisy = clean + noise

        result = mod.compute(noisy)
        assert result["snr_improvement_db"] > 0.0

    def test_short_signal_no_crash(self) -> None:
        """Signal kuerzer als 2^level -> graceful Fallback."""
        mod = M4WaveletDenoiser(wavelet="sym6", level=4)
        short_signal = np.array([1.0, 2.0, 3.0])
        result = mod.compute(short_signal)
        assert result["denoised"].shape == short_signal.shape
        assert result["snr_improvement_db"] == 0.0

    def test_output_keys(self) -> None:
        """Prueft ob alle erwarteten Keys im Output vorhanden sind."""
        mod = M4WaveletDenoiser()
        result = mod.compute(np.random.default_rng(42).standard_normal(256))
        expected_keys = {
            "denoised", "snr_improvement_db", "method_id",
            "signal", "confidence", "ts",
        }
        assert set(result.keys()) == expected_keys
        assert result["method_id"] == "M4"
        assert result["signal"] == 0

    def test_validate(self) -> None:
        """validate() gibt True bei korrekter Konfiguration."""
        mod = M4WaveletDenoiser()
        assert mod.validate() is True

    def test_haar_fallback_works(self) -> None:
        """Haar-DWT Fallback produziert korrektes Ergebnis."""
        mod = M4WaveletDenoiser()
        rng = np.random.default_rng(42)
        signal = rng.standard_normal(64)

        # Direkt Haar testen
        approx, details = mod._haar_dwt(signal, level=3)
        reconstructed = mod._haar_idwt(approx, details)
        np.testing.assert_allclose(reconstructed[:len(signal)], signal, atol=1e-10)
