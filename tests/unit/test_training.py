"""
Tests for the training infrastructure (KlineDataset + windowing helpers).

Covers:
- build_windows produces strict-causal X/y windows (no lookahead).
- chronological_split preserves time order (train before val).
- RevIN normalize/denormalize is a roundtrip.
- KlineDataset constructs from a cached numpy series.
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge._legacy_v1.training.dataset import (
    build_windows,
    chronological_split,
    revin_denormalize_sample,
    revin_normalize_sample,
)


class TestKlineDatasetNoLookahead:
    """Each window y must come strictly after its X."""

    def test_kline_dataset_no_lookahead(self) -> None:
        series = np.arange(100, dtype=np.float64)
        lookback, horizon = 10, 4
        X, y = build_windows(series, lookback, horizon, stride=1)
        assert X.shape == (100 - lookback - horizon + 1, lookback)
        assert y.shape == (X.shape[0], horizon)
        # For each window, the last X-value must be < first y-value
        # (since series is strictly increasing).
        for i in range(X.shape[0]):
            assert X[i, -1] < y[i, 0], (
                f"Window {i} has lookahead: X[-1]={X[i, -1]} y[0]={y[i, 0]}"
            )
            # And y[0] must equal X[-1] + 1 (consecutive ints in synthetic data)
            assert y[i, 0] == X[i, -1] + 1


class TestKlineDatasetChronologicalSplit:
    """Train slice must come before val slice in time."""

    def test_kline_dataset_chronological_split(self) -> None:
        series = np.arange(50, dtype=np.float64)
        X, y = build_windows(series, lookback=5, horizon=2, stride=1)
        X_tr, X_va, y_tr, y_va = chronological_split(X, y, val_fraction=0.3)

        assert len(X_tr) + len(X_va) == len(X)
        # Chronology invariant: start-index der ersten Val-Sequenz muss
        # >= start-index der letzten Train-Sequenz sein (Sliding-Window
        # mit stride=1 erlaubt überlappende Fenster, aber der Ordnungs-
        # Index ist streng monoton).
        # Approximiere die Start-Indizes via X[i, 0] (Series ist arange).
        last_train_start = float(X_tr[-1, 0])
        first_val_start = float(X_va[0, 0])
        assert last_train_start < first_val_start, (
            f"Chronology violated: train last start={last_train_start} "
            f">= val first start={first_val_start}"
        )


class TestRevinPerSample:
    """RevIN normalize/denormalize roundtrip approximates the original."""

    def test_revin_per_sample(self) -> None:
        rng = np.random.default_rng(0)
        x = rng.normal(100, 10, 64)
        x_n, mu, sigma = revin_normalize_sample(x)
        # Normalised mean ≈ 0, std ≈ 1
        assert abs(np.mean(x_n)) < 1e-6
        assert abs(np.std(x_n) - 1.0) < 1e-3

        x_back = revin_denormalize_sample(x_n, mu, sigma)
        np.testing.assert_allclose(x_back, x, atol=1e-6)


class TestBuildWindowsEdgeCases:
    """Series shorter than lookback+horizon returns empty windows."""

    def test_build_windows_too_short(self) -> None:
        series = np.arange(5, dtype=np.float64)
        X, y = build_windows(series, lookback=4, horizon=4, stride=1)
        assert X.shape == (0, 4)
        assert y.shape == (0, 4)


torch = pytest.importorskip("torch")


class TestKlineDatasetFromCached:
    """KlineDataset can be constructed from a cached numpy series (no REST)."""

    def test_kline_dataset_from_cached_series(self) -> None:
        from bybit_edge._legacy_v1.training.dataset import KlineDataset

        series = np.linspace(100, 120, 200).astype(np.float64)
        ds = KlineDataset(
            symbol="BTCUSDT",
            interval="5",
            months=1,
            lookback=20,
            horizon=4,
            cached_series=series,
        )
        assert len(ds) == 200 - 20 - 4 + 1
        x, y = ds[0]
        assert x.shape == (20,)
        assert y.shape == (4,)
        # RevIN-normalisiert -> mean ~ 0
        assert abs(float(x.mean())) < 1e-4
