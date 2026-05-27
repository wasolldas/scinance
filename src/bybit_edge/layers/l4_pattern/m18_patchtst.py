"""
M18 — PatchTST Funding-Cycle-Forecast [L4]

Lightweight PatchTST architecture in pure numpy (no PyTorch).

Core idea (Nie et al., 2023):
    1. Slice input series into overlapping patches.
    2. Project patches to d_model via linear layer.
    3. Apply multi-head self-attention (Transformer encoder layers).
    4. Linear head maps encoder output to forecast horizon.

Training: Ridge-regression on patch features -> forecast (gradient-free).
Inference: full forward pass through attention layers.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from bybit_edge.layers.base import BaseModule

_EPS: float = 1e-12


class M18PatchTST(BaseModule):
    """Lightweight PatchTST for funding cycle forecasting (numpy-only)."""

    def __init__(
        self,
        patch_length: int = 16,
        stride: int = 8,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        forecast_horizon: int = 12,
    ) -> None:
        self.patch_length: int = patch_length
        self.stride: int = stride
        self.d_model: int = d_model
        self.n_heads: int = n_heads
        self.n_layers: int = n_layers
        self.forecast_horizon: int = forecast_horizon

        self._weights: dict[str, np.ndarray] = {}
        self._fitted: bool = False
        self._init_weights()

    def _init_weights(self) -> None:
        """Initialise random projection weights (Xavier-scale)."""
        rng = np.random.default_rng(42)
        scale_patch = np.sqrt(2.0 / (self.patch_length + self.d_model))
        self._weights["patch_proj_W"] = rng.normal(
            0, scale_patch, (self.patch_length, self.d_model)
        )
        self._weights["patch_proj_b"] = np.zeros(self.d_model)

        d_k = self.d_model // self.n_heads
        scale_attn = np.sqrt(2.0 / (self.d_model + d_k))
        for layer_i in range(self.n_layers):
            for suffix in ("Q", "K", "V"):
                key = f"L{layer_i}_{suffix}_W"
                self._weights[key] = rng.normal(
                    0, scale_attn, (self.d_model, self.d_model)
                )
                self._weights[f"L{layer_i}_{suffix}_b"] = np.zeros(self.d_model)
            self._weights[f"L{layer_i}_O_W"] = rng.normal(
                0, scale_attn, (self.d_model, self.d_model)
            )
            self._weights[f"L{layer_i}_O_b"] = np.zeros(self.d_model)

        # Ridge head weights (set during fit)
        self._weights["head_W"] = rng.normal(
            0, 0.01, (self.d_model, self.forecast_horizon)
        )
        self._weights["head_b"] = np.zeros(self.forecast_horizon)

    # ------------------------------------------------------------------
    # Building blocks
    # ------------------------------------------------------------------

    def _create_patches(self, series: np.ndarray) -> np.ndarray:
        """Sliding-window patch extraction.

        Parameters
        ----------
        series : np.ndarray, shape (L,)

        Returns
        -------
        np.ndarray, shape (n_patches, patch_length)
        """
        L = len(series)
        starts = list(range(0, L - self.patch_length + 1, self.stride))
        if not starts:
            starts = [0]
        patches = np.array(
            [series[s : s + self.patch_length] for s in starts]
        )
        return patches

    def _linear(self, x: np.ndarray, weight_key: str) -> np.ndarray:
        """x @ W + b using weights from self._weights."""
        W = self._weights[f"{weight_key}_W"]
        b = self._weights[f"{weight_key}_b"]
        return x @ W + b

    @staticmethod
    def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Numerically stable softmax."""
        e = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return e / (np.sum(e, axis=axis, keepdims=True) + _EPS)

    def _simple_attention(
        self, Q: np.ndarray, K: np.ndarray, V: np.ndarray
    ) -> np.ndarray:
        """Scaled dot-product attention (multi-head).

        Parameters
        ----------
        Q, K, V : np.ndarray, shape (n_patches, d_model)

        Returns
        -------
        np.ndarray, shape (n_patches, d_model)
        """
        n, d = Q.shape
        d_k = d // self.n_heads

        out_heads: list[np.ndarray] = []
        for h in range(self.n_heads):
            sl = slice(h * d_k, (h + 1) * d_k)
            q_h = Q[:, sl]  # (n, d_k)
            k_h = K[:, sl]
            v_h = V[:, sl]
            scores = (q_h @ k_h.T) / np.sqrt(d_k + _EPS)  # (n, n)
            attn = self._softmax(scores, axis=-1)
            out_heads.append(attn @ v_h)

        return np.concatenate(out_heads, axis=-1)  # (n, d_model)

    def _forward(self, series: np.ndarray) -> np.ndarray:
        """Full forward pass: patches -> encoder -> mean-pool -> head.

        Returns
        -------
        np.ndarray, shape (forecast_horizon,)
        """
        patches = self._create_patches(series)  # (N, P)
        x = self._linear(patches, "patch_proj")  # (N, d_model)

        for layer_i in range(self.n_layers):
            Q = self._linear(x, f"L{layer_i}_Q")
            K = self._linear(x, f"L{layer_i}_K")
            V = self._linear(x, f"L{layer_i}_V")
            attn_out = self._simple_attention(Q, K, V)
            proj = self._linear(attn_out, f"L{layer_i}_O")
            x = x + proj  # residual connection

        # Mean pooling over patches
        pooled = np.mean(x, axis=0)  # (d_model,)

        forecast = pooled @ self._weights["head_W"] + self._weights["head_b"]
        return forecast

    # ------------------------------------------------------------------
    # Training (gradient-free ridge regression)
    # ------------------------------------------------------------------

    def fit(
        self,
        train_data: np.ndarray,
        targets: np.ndarray,
        epochs: int = 10,
    ) -> dict[str, Any]:
        """Train via ridge regression on random-projection patch features.

        Parameters
        ----------
        train_data : np.ndarray, shape (n_samples, lookback)
            Each row is a lookback window of prices.
        targets : np.ndarray, shape (n_samples, forecast_horizon)
            Forecast targets for each sample.
        epochs : int
            Number of iterative refinement passes.

        Returns
        -------
        dict  {"train_mse": float, "epochs": int}
        """
        n_samples = train_data.shape[0]
        features_list: list[np.ndarray] = []
        for i in range(n_samples):
            patches = self._create_patches(train_data[i])
            proj = patches @ self._weights["patch_proj_W"] + self._weights["patch_proj_b"]
            pooled = np.mean(proj, axis=0)
            features_list.append(pooled)

        X = np.array(features_list)  # (n_samples, d_model)
        Y = targets  # (n_samples, horizon)

        # Ridge regression: W = (X^T X + alpha I)^{-1} X^T Y
        alpha_reg = 1.0
        best_mse = float("inf")
        for _ in range(epochs):
            XtX = X.T @ X + alpha_reg * np.eye(X.shape[1])
            XtY = X.T @ Y
            W = np.linalg.solve(XtX, XtY)
            b = np.mean(Y - X @ W, axis=0)
            preds = X @ W + b
            mse = float(np.mean((preds - Y) ** 2))
            if mse < best_mse:
                best_mse = mse
                self._weights["head_W"] = W
                self._weights["head_b"] = b
            alpha_reg *= 0.8  # anneal regularisation

        self._fitted = True
        return {"train_mse": best_mse, "epochs": epochs}

    # ------------------------------------------------------------------
    # Compute (inference)
    # ------------------------------------------------------------------

    def compute(self, series: np.ndarray) -> dict[str, Any]:
        """Run PatchTST inference on a price series.

        Parameters
        ----------
        series : np.ndarray, shape (L,)
            Recent close prices (e.g. 512 five-minute bars).

        Returns
        -------
        dict
        """
        if not self._fitted:
            return {
                "forecast": np.zeros(self.forecast_horizon),
                "forecast_direction": 0,
                "forecast_magnitude": 0.0,
                "signal": 0,
                "method_id": "M18",
                "confidence": 0.0,
                "ts": time.time(),
            }

        forecast = self._forward(series)
        direction = int(np.sign(forecast[-1] - series[-1]))
        magnitude = float(np.abs(forecast[-1] - series[-1]))
        confidence = float(np.clip(magnitude / (np.std(series) + _EPS), 0.0, 1.0))

        return {
            "forecast": forecast,
            "forecast_direction": direction,
            "forecast_magnitude": magnitude,
            "signal": direction,
            "method_id": "M18",
            "confidence": confidence,
            "ts": time.time(),
        }

    def reset(self) -> None:
        """Reset fitted state and re-initialise weights."""
        self._fitted = False
        self._init_weights()
