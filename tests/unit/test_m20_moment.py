"""
Tests for M20 — MOMENT Foundation Model Placeholder.

Tests:
- RevIN normalise/denormalise roundtrip
- Fallback forecast length
- Fallback forecast drift direction
- Compute without pretrained (fallback active, is_zero_shot=True)
- Load pretrained missing file returns False
- model_loaded flag
- Return keys complete
- Reset clears state
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest

from bybit_edge.layers.l4_pattern.m20_moment import M20MOMENT


class TestRevinNormalizeDenormalize:
    """Normalise then denormalise should approximate the original."""

    def test_revin_normalize_denormalize(self) -> None:
        rng = np.random.default_rng(0)
        x = rng.normal(100, 10, 256)
        x_norm, mu, sigma = M20MOMENT._revin_normalize(x)
        x_restored = M20MOMENT._revin_denormalize(x_norm, mu, sigma)

        np.testing.assert_allclose(x_restored, x, atol=1e-8)


class TestFallbackForecastLength:
    """Fallback forecast must have exactly *horizon* steps."""

    def test_fallback_forecast_length(self) -> None:
        model = M20MOMENT(forecast_horizon=12)
        series = np.random.default_rng(1).normal(100, 5, 256)
        fc = model._fallback_forecast(series, 12)

        assert len(fc) == 12


class TestFallbackForecastDriftDirection:
    """On a clear uptrend, drift should be positive -> forecast rises."""

    def test_fallback_forecast_drift_direction(self) -> None:
        model = M20MOMENT(forecast_horizon=8, ema_span=10)
        series = np.linspace(100, 120, 100)  # clear uptrend
        fc = model._fallback_forecast(series, 8)

        # Each successive forecast step should be larger
        assert fc[-1] > fc[0], f"Uptrend forecast should rise: {fc}"
        # Forecast should continue above last price
        assert fc[0] > series[-1] - 1.0, "Forecast start should be near/above last price"


class TestComputeWithoutPretrained:
    """Without pretrained weights, fallback is active and is_zero_shot=True."""

    def test_compute_without_pretrained(self) -> None:
        model = M20MOMENT(forecast_horizon=6)
        series = np.random.default_rng(2).normal(100, 5, 256)
        result = model.compute(series)

        assert result["is_zero_shot"] is True
        assert result["model_loaded"] is False
        assert result["method_id"] == "M20"
        assert result["signal"] in (-1, 0, 1)
        assert len(result["forecast"]) == 6


class TestLoadPretrainedMissingFile:
    """load_pretrained with a nonexistent file should return False."""

    def test_load_pretrained_missing_file(self) -> None:
        model = M20MOMENT()
        ok = model.load_pretrained("/nonexistent/path/model.npz")

        assert ok is False
        assert model._model_loaded is False


class TestModelLoadedFlag:
    """After successful load, model_loaded should be True."""

    def test_model_loaded_flag(self) -> None:
        model = M20MOMENT()

        # Create a valid .npz file
        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
            tmp_path = f.name
            np.savez(f, dummy=np.array([1.0]))

        try:
            ok = model.load_pretrained(tmp_path)
            assert ok is True
            assert model._model_loaded is True
            assert model._fitted is True
        finally:
            os.unlink(tmp_path)


class TestReturnKeys:
    """Compute result must contain all required keys."""

    def test_return_keys(self) -> None:
        model = M20MOMENT()
        series = np.random.default_rng(3).normal(100, 5, 256)
        result = model.compute(series)

        required = {
            "forecast", "forecast_direction", "is_zero_shot",
            "model_loaded", "signal", "method_id", "confidence", "ts",
        }
        assert required.issubset(result.keys()), (
            f"Missing keys: {required - result.keys()}"
        )


class TestReset:
    """Reset should clear fitted and model_loaded flags."""

    def test_reset(self) -> None:
        model = M20MOMENT()
        model._fitted = True
        model._model_loaded = True
        model._weights["dummy"] = np.array([1.0])

        model.reset()

        assert model._fitted is False
        assert model._model_loaded is False
        assert len(model._weights) == 0


class TestLoadPretrainedGracefulMissingHF:
    """Bei nicht existierendem HF-Repo (momentfm fehlt) -> False."""

    def test_load_pretrained_graceful_missing_hf(self) -> None:
        model = M20MOMENT()
        ok = model.load_pretrained("AutonLab/MOMENT-1-base", model_size="base")
        # In dieser Sandbox ist momentfm NICHT installiert -> graceful False.
        # Falls doch installiert, wäre True erlaubt.
        assert isinstance(ok, bool)
        if not ok:
            assert model._model_loaded is False
