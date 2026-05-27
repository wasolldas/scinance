"""
M19 — TimesNet 2D-Periodicity Detector [L4]

Lightweight TimesNet core idea in pure numpy (no PyTorch).

Key insight (Wu et al., 2023):
    1. Detect dominant periods via FFT.
    2. Reshape 1-D series into 2-D tensors [n_periods, period_length].
    3. Extract 2-D features (row/col/diag statistics as inception proxy).
    4. Weighted combination of per-period features -> forecast.

Training: Ridge regression on 2-D features.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from bybit_edge.layers.base import BaseModule

_EPS: float = 1e-12


class M19TimesNet(BaseModule):
    """Lightweight TimesNet for periodicity-based forecasting (numpy-only)."""

    def __init__(
        self,
        top_k: int = 3,
        forecast_horizon: int = 12,
    ) -> None:
        self.top_k: int = top_k
        self.forecast_horizon: int = forecast_horizon

        self._weights: dict[str, np.ndarray] = {}
        self._fitted: bool = False

    # ------------------------------------------------------------------
    # Core building blocks
    # ------------------------------------------------------------------

    @staticmethod
    def _fft_top_k_periods(series: np.ndarray, k: int = 3) -> list[int]:
        """Detect top-k dominant periods via FFT amplitude spectrum.

        Parameters
        ----------
        series : np.ndarray, shape (L,)
        k : int

        Returns
        -------
        list[int]  period lengths (in samples), sorted descending by amplitude.
        """
        N = len(series)
        if N < 4:
            return [max(N, 2)]

        # Remove mean
        x = series - np.mean(series)
        spectrum = np.abs(np.fft.rfft(x))

        # Skip DC (index 0) and Nyquist; consider freqs 1..N//2-1
        usable = min(len(spectrum), N // 2)
        if usable <= 1:
            return [max(N, 2)]

        amps = spectrum[1:usable]
        freqs = np.arange(1, usable)

        # Top-k by amplitude
        k_actual = min(k, len(amps))
        top_indices = np.argsort(amps)[-k_actual:][::-1]
        periods: list[int] = []
        for idx in top_indices:
            freq = freqs[idx]
            period = max(int(round(N / freq)), 2)
            if period not in periods:
                periods.append(period)

        return periods if periods else [max(N, 2)]

    @staticmethod
    def _reshape_2d(series: np.ndarray, period: int) -> np.ndarray:
        """Reshape 1-D series into 2-D [n_periods, period_length].

        Truncates the series to a multiple of *period*.
        """
        period = max(period, 2)
        L = len(series)
        n_full = L // period
        if n_full < 1:
            return series.reshape(1, -1)
        used = n_full * period
        return series[-used:].reshape(n_full, period)

    @staticmethod
    def _inception_block_simple(x_2d: np.ndarray) -> np.ndarray:
        """Extract 2-D statistics as a simplified inception proxy.

        Features per 2-D block:
            - row means, row stds  (temporal patterns within each period)
            - col means, col stds  (cross-period patterns per phase)
            - main-diagonal mean / std
            - global mean, std, min, max

        Returns
        -------
        np.ndarray, 1-D feature vector.
        """
        row_means = np.mean(x_2d, axis=1)
        row_stds = np.std(x_2d, axis=1) + _EPS
        col_means = np.mean(x_2d, axis=0)
        col_stds = np.std(x_2d, axis=0) + _EPS

        diag = np.diag(x_2d) if min(x_2d.shape) > 0 else np.array([0.0])
        diag_mean = np.mean(diag)
        diag_std = np.std(diag) + _EPS

        global_stats = np.array([
            np.mean(x_2d), np.std(x_2d) + _EPS,
            np.min(x_2d), np.max(x_2d),
        ])

        return np.concatenate([
            row_means, row_stds, col_means, col_stds,
            [diag_mean, diag_std], global_stats,
        ])

    def _extract_features(self, series: np.ndarray) -> np.ndarray:
        """Extract features for all top-k periods and concatenate."""
        periods = self._fft_top_k_periods(series, self.top_k)
        all_feats: list[np.ndarray] = []
        for p in periods:
            x_2d = self._reshape_2d(series, p)
            feats = self._inception_block_simple(x_2d)
            all_feats.append(feats)

        # Pad/truncate to fixed size per period for consistent dimensions
        max_len = max(len(f) for f in all_feats)
        padded: list[np.ndarray] = []
        for f in all_feats:
            if len(f) < max_len:
                f = np.concatenate([f, np.zeros(max_len - len(f))])
            padded.append(f)

        return np.concatenate(padded)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(
        self,
        train_data: np.ndarray,
        targets: np.ndarray,
    ) -> dict[str, Any]:
        """Fit ridge regression on 2-D period features.

        Parameters
        ----------
        train_data : np.ndarray, shape (n_samples, lookback)
        targets : np.ndarray, shape (n_samples, forecast_horizon)

        Returns
        -------
        dict  {"train_mse": float}
        """
        n_samples = train_data.shape[0]

        feat_list: list[np.ndarray] = []
        for i in range(n_samples):
            feat_list.append(self._extract_features(train_data[i]))

        # Align feature vectors (may differ in length across samples)
        max_dim = max(len(f) for f in feat_list)
        X = np.zeros((n_samples, max_dim))
        for i, f in enumerate(feat_list):
            X[i, : len(f)] = f

        Y = targets
        alpha_reg = 1.0
        XtX = X.T @ X + alpha_reg * np.eye(X.shape[1])
        XtY = X.T @ Y
        W = np.linalg.solve(XtX, XtY)
        b = np.mean(Y - X @ W, axis=0)

        self._weights["ridge_W"] = W
        self._weights["ridge_b"] = b
        self._weights["feat_dim"] = np.array([max_dim])
        self._fitted = True

        preds = X @ W + b
        mse = float(np.mean((preds - Y) ** 2))
        return {"train_mse": mse}

    # ------------------------------------------------------------------
    # Compute (inference)
    # ------------------------------------------------------------------

    def compute(self, series: np.ndarray) -> dict[str, Any]:
        """Run TimesNet inference.

        Parameters
        ----------
        series : np.ndarray, shape (L,)

        Returns
        -------
        dict
        """
        periods = self._fft_top_k_periods(series, self.top_k)

        if not self._fitted:
            return {
                "forecast": np.zeros(self.forecast_horizon),
                "detected_periods": periods,
                "forecast_direction": 0,
                "signal": 0,
                "method_id": "M19",
                "confidence": 0.0,
                "ts": time.time(),
            }

        feats = self._extract_features(series)
        feat_dim = int(self._weights["feat_dim"][0])
        x = np.zeros(feat_dim)
        x[: min(len(feats), feat_dim)] = feats[: feat_dim]

        forecast = x @ self._weights["ridge_W"] + self._weights["ridge_b"]
        direction = int(np.sign(forecast[-1] - series[-1]))
        confidence = float(
            np.clip(
                np.abs(forecast[-1] - series[-1]) / (np.std(series) + _EPS),
                0.0,
                1.0,
            )
        )

        return {
            "forecast": forecast,
            "detected_periods": periods,
            "forecast_direction": direction,
            "signal": direction,
            "method_id": "M19",
            "confidence": confidence,
            "ts": time.time(),
        }

    def reset(self) -> None:
        """Reset fitted state and weights."""
        self._fitted = False
        self._weights.clear()
