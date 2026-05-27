"""
Tests for M19 — TimesNet 2D-Periodicity Detector.

Tests:
- FFT detects known period (sine wave with period=24)
- Reshape 2D produces correct shape
- Unfitted model returns signal=0
- Fit and forecast produces finite output
- Multiple periods detected
- Short series does not crash
- Return keys are complete
- Reset clears state
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.layers.l4_pattern.m19_timesnet import M19TimesNet


class TestFFTDetectsKnownPeriod:
    """A sine wave with period=24 should be detected by FFT."""

    def test_fft_detects_known_period(self) -> None:
        N = 240
        t = np.arange(N, dtype=np.float64)
        series = np.sin(2 * np.pi * t / 24.0)

        periods = M19TimesNet._fft_top_k_periods(series, k=3)
        assert 24 in periods, f"Period 24 not found in {periods}"


class TestReshape2DShape:
    """1D -> 2D reshape should produce (n_periods, period) shape."""

    def test_reshape_2d_shape(self) -> None:
        series = np.arange(120, dtype=np.float64)
        result = M19TimesNet._reshape_2d(series, period=24)

        assert result.shape == (5, 24), f"Expected (5, 24), got {result.shape}"


class TestComputeUnfittedReturnsZero:
    """Unfitted model must return signal=0."""

    def test_compute_unfitted_returns_zero(self) -> None:
        model = M19TimesNet()
        series = np.random.default_rng(0).normal(100, 5, 256)
        result = model.compute(series)

        assert result["signal"] == 0
        assert result["forecast_direction"] == 0
        np.testing.assert_array_equal(result["forecast"], np.zeros(model.forecast_horizon))


class TestFitAndForecast:
    """After fit, compute should produce a finite forecast."""

    def test_fit_and_forecast(self) -> None:
        rng = np.random.default_rng(1)
        model = M19TimesNet(top_k=2, forecast_horizon=4)

        n_samples = 30
        lookback = 128
        train_data = rng.normal(100, 5, (n_samples, lookback))
        targets = rng.normal(100, 5, (n_samples, 4))

        fit_result = model.fit(train_data, targets)
        assert np.isfinite(fit_result["train_mse"])
        assert model._fitted is True

        series = rng.normal(100, 5, lookback)
        result = model.compute(series)

        assert np.all(np.isfinite(result["forecast"]))
        assert result["signal"] in (-1, 0, 1)


class TestMultiplePeriodsDetected:
    """Composite signal with two frequencies should yield multiple periods."""

    def test_multiple_periods_detected(self) -> None:
        N = 480
        t = np.arange(N, dtype=np.float64)
        series = np.sin(2 * np.pi * t / 24.0) + 0.5 * np.sin(2 * np.pi * t / 48.0)

        periods = M19TimesNet._fft_top_k_periods(series, k=3)
        assert len(periods) >= 2, f"Expected >= 2 periods, got {periods}"


class TestShortSeriesNoCrash:
    """Very short series should not raise exceptions."""

    def test_short_series_no_crash(self) -> None:
        model = M19TimesNet()
        series = np.array([1.0, 2.0, 3.0])
        result = model.compute(series)

        assert result["method_id"] == "M19"
        assert result["signal"] in (-1, 0, 1)


class TestReturnKeys:
    """Compute result must contain all required keys."""

    def test_return_keys(self) -> None:
        model = M19TimesNet()
        series = np.random.default_rng(2).normal(100, 5, 256)
        result = model.compute(series)

        required = {
            "forecast", "detected_periods", "forecast_direction",
            "signal", "method_id", "confidence", "ts",
        }
        assert required.issubset(result.keys()), (
            f"Missing keys: {required - result.keys()}"
        )


class TestReset:
    """Reset should clear fitted state."""

    def test_reset(self) -> None:
        model = M19TimesNet()
        model._fitted = True
        model._weights["dummy"] = np.array([1.0])

        model.reset()

        assert model._fitted is False
        assert len(model._weights) == 0
