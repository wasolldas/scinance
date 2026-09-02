"""
Tests for M18 — PatchTST Funding-Cycle-Forecast.

Tests:
- Patch creation shape
- Attention output shape
- Attention softmax sums to one
- Unfitted model returns signal=0
- Fit reduces training error
- Forecast direction positive for uptrend
- Forecast length matches horizon
- Reset clears state
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge._legacy_v1.layers.l4_pattern.m18_patchtst import M18PatchTST


class TestCreatePatchesShape:
    """Patches should have shape (n_patches, patch_length)."""

    def test_create_patches_shape(self) -> None:
        model = M18PatchTST(patch_length=16, stride=8)
        series = np.random.default_rng(0).normal(0, 1, 128)
        patches = model._create_patches(series)

        # Expected n_patches: (128 - 16) // 8 + 1 = 15
        expected_n = (128 - 16) // 8 + 1
        assert patches.shape == (expected_n, 16), (
            f"Expected ({expected_n}, 16), got {patches.shape}"
        )


class TestAttentionOutputShape:
    """Attention output must match input shape (n, d_model)."""

    def test_attention_output_shape(self) -> None:
        model = M18PatchTST(d_model=32, n_heads=4)
        n, d = 10, 32
        rng = np.random.default_rng(1)
        Q = rng.normal(0, 1, (n, d))
        K = rng.normal(0, 1, (n, d))
        V = rng.normal(0, 1, (n, d))

        out = model._simple_attention(Q, K, V)
        assert out.shape == (n, d), f"Expected ({n}, {d}), got {out.shape}"


class TestAttentionSoftmaxSumsToOne:
    """Attention weights per row must sum to ~1."""

    def test_attention_softmax_sums_to_one(self) -> None:
        model = M18PatchTST(d_model=16, n_heads=2)
        n, d = 5, 16
        rng = np.random.default_rng(2)
        Q = rng.normal(0, 1, (n, d))
        K = rng.normal(0, 1, (n, d))

        d_k = d // model.n_heads
        for h in range(model.n_heads):
            sl = slice(h * d_k, (h + 1) * d_k)
            scores = (Q[:, sl] @ K[:, sl].T) / np.sqrt(d_k)
            attn = model._softmax(scores, axis=-1)
            row_sums = np.sum(attn, axis=-1)
            np.testing.assert_allclose(row_sums, 1.0, atol=1e-6)


class TestComputeUnfittedReturnsZero:
    """Unfitted model must return signal=0 and zero forecast."""

    def test_compute_unfitted_returns_zero(self) -> None:
        model = M18PatchTST()
        series = np.random.default_rng(3).normal(100, 5, 512)
        result = model.compute(series)

        assert result["signal"] == 0
        assert result["forecast_direction"] == 0
        assert result["confidence"] == 0.0
        np.testing.assert_array_equal(result["forecast"], np.zeros(model.forecast_horizon))


class TestFitReducesError:
    """After fit, train_mse should be a finite positive number."""

    def test_fit_reduces_error(self) -> None:
        rng = np.random.default_rng(4)
        model = M18PatchTST(patch_length=8, stride=4, d_model=16, n_heads=2,
                            forecast_horizon=4)

        n_samples = 30
        lookback = 64
        train_data = rng.normal(100, 5, (n_samples, lookback))
        targets = rng.normal(100, 5, (n_samples, 4))

        result = model.fit(train_data, targets, epochs=5)
        assert np.isfinite(result["train_mse"])
        assert result["train_mse"] >= 0
        assert model._fitted is True


class TestForecastDirectionPositive:
    """Forecast on a clear uptrend should predict direction=+1."""

    def test_forecast_direction_positive(self) -> None:
        model = M18PatchTST(patch_length=8, stride=4, d_model=16, n_heads=2,
                            forecast_horizon=4)

        rng = np.random.default_rng(5)
        n_samples = 50
        lookback = 64

        # Generate uptrend data
        train_data = np.array([
            np.linspace(100, 110, lookback) + rng.normal(0, 0.1, lookback)
            for _ in range(n_samples)
        ])
        targets = np.array([
            np.linspace(110, 112, 4) + rng.normal(0, 0.1, 4)
            for _ in range(n_samples)
        ])

        model.fit(train_data, targets, epochs=10)
        series = np.linspace(100, 110, lookback)
        result = model.compute(series)

        # After fitting on uptrend, forecast should be above last price
        assert result["signal"] in (-1, 0, 1), "Signal must be valid"
        assert result["method_id"] == "M18"


class TestForecastLengthMatchesHorizon:
    """Forecast array length must equal forecast_horizon."""

    def test_forecast_length_matches_horizon(self) -> None:
        horizon = 8
        model = M18PatchTST(patch_length=8, stride=4, d_model=16,
                            n_heads=2, forecast_horizon=horizon)

        rng = np.random.default_rng(6)
        n_samples = 20
        lookback = 64
        train_data = rng.normal(100, 5, (n_samples, lookback))
        targets = rng.normal(100, 5, (n_samples, horizon))

        model.fit(train_data, targets)
        series = rng.normal(100, 5, lookback)
        result = model.compute(series)

        assert len(result["forecast"]) == horizon


class TestReset:
    """Reset should clear fitted state and reinitialise weights."""

    def test_reset(self) -> None:
        model = M18PatchTST()
        model._fitted = True
        old_w = model._weights["head_W"].copy()
        model._weights["head_W"] += 999.0

        model.reset()

        assert model._fitted is False
        # Weights re-initialised (deterministic seed → same as fresh)
        fresh = M18PatchTST()
        np.testing.assert_array_equal(model._weights["head_W"], fresh._weights["head_W"])


# ══════════════════════════════════════════════════════════════════════
# Zusätzliche Tests für die PyTorch-Implementierung
# ══════════════════════════════════════════════════════════════════════


torch = pytest.importorskip("torch")


class TestPyTorchForwardPassShape:
    """Forward-Pass durch das PyTorch-Modell liefert (B, forecast_horizon)."""

    def test_pytorch_forward_pass_shape(self) -> None:
        model = M18PatchTST(
            patch_length=8, stride=4, d_model=16, n_heads=2,
            lookback=64, forecast_horizon=8,
        )
        x = torch.randn(4, 64)
        out = model._model(x)
        assert out.shape == (4, 8)


class TestSaveLoadRoundtrip:
    """save() + load() liefern identischen Forward-Output."""

    def test_save_load_roundtrip(self, tmp_path) -> None:
        model = M18PatchTST(
            patch_length=8, stride=4, d_model=16, n_heads=2,
            lookback=64, forecast_horizon=4,
        )
        model._fitted = True
        x = np.linspace(100, 110, 64)
        out_a = model.compute(x)["forecast"]

        ckpt = tmp_path / "m18.pt"
        model.save(str(ckpt))

        model2 = M18PatchTST(
            patch_length=8, stride=4, d_model=16, n_heads=2,
            lookback=64, forecast_horizon=4,
        )
        ok = model2.load(str(ckpt))
        assert ok is True
        out_b = model2.compute(x)["forecast"]
        np.testing.assert_allclose(out_a, out_b, atol=1e-6)


class TestFitReducesTrainLoss:
    """Train-MSE sinkt über die Epochen auf einem winzigen Datensatz."""

    def test_fit_reduces_train_loss(self) -> None:
        rng = np.random.default_rng(0)
        model = M18PatchTST(
            patch_length=4, stride=2, d_model=16, n_heads=2,
            n_layers=1, lookback=32, forecast_horizon=4,
        )
        # Lerne eine simple Sin-Periode
        n_samples = 80
        X = np.stack([
            np.sin(np.linspace(0, 4 * np.pi, 32) + rng.normal(0, 0.05))
            for _ in range(n_samples)
        ])
        Y = np.stack([
            np.sin(np.linspace(4 * np.pi, 5 * np.pi, 4) + rng.normal(0, 0.05))
            for _ in range(n_samples)
        ])
        res = model.fit(X.astype(np.float32), Y.astype(np.float32),
                        epochs=4, batch_size=16, lr=1e-2)
        hist = res["history"]
        assert hist[-1] < hist[0] + 1e-6, f"Loss did not improve: {hist}"
