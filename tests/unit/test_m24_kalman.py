"""
Tests für M24 — Kalman-Funding-Premium-Decomposition.

Testet:
- Kalman predict + update Zyklus konvergiert
- Sentiment-Spike erzeugt Signal
- Kein Signal bei ruhigem Markt
- Reset reinitialisiert den State
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.config import KALMAN_SENTIMENT_ZSCORE
from bybit_edge.layers.l5_risk.m24_kalman_premium import M24KalmanPremium


def _make_ticker(
    funding_rate: float = 0.0001,
    mark_price: float = 100_000.0,
    index_price: float = 100_000.0,
) -> dict:
    """Erzeugt minimales ticker_data dict."""
    return {
        "funding_rate": funding_rate,
        "mark_price": mark_price,
        "index_price": index_price,
    }


class TestKalmanPredictUpdateCycle:
    """Test dass der Kalman-Filter konvergiert."""

    def test_kalman_predict_update_cycle(self) -> None:
        """Nach mehreren Updates mit konstantem Input konvergiert der State."""
        mod = M24KalmanPremium()

        # Konstante Observations: funding=0.0001, basis=0.0
        results = []
        for _ in range(200):
            result = mod.compute(_make_ticker(
                funding_rate=0.0001,
                mark_price=100_000.0,
                index_price=100_000.0,
            ))
            results.append(result)

        # Trend sollte sich stabilisieren nahe dem Beobachtungswert
        last = results[-1]
        assert last["method_id"] == "M24"
        assert last["signal"] in {-1, 0, 1}

        # State-Kovarianz sollte abgenommen haben (Filter konvergiert)
        assert mod._P[0, 0] < 1e-4  # kleiner als Initialisierung
        assert mod._P[1, 1] < 1e-4

    def test_state_tracks_observations(self) -> None:
        """State sollte den Beobachtungen folgen bei konstantem Input."""
        mod = M24KalmanPremium()

        for _ in range(500):
            mod.compute(_make_ticker(
                funding_rate=0.0005,
                mark_price=100_100.0,
                index_price=100_000.0,  # basis = 0.001
            ))

        # trend + sentiment sollten zusammen ungefähr die Observation erklären
        trend = mod._x[0]
        sentiment = mod._x[1]
        # H @ x ≈ z → [trend+sentiment, sentiment] ≈ [0.0005, 0.001]
        # Wir prüfen dass die Werte im sinnvollen Bereich liegen
        assert abs(trend) < 0.01
        assert abs(sentiment) < 0.01


class TestSentimentSpikeSignal:
    """Test dass ein Sentiment-Spike ein Signal auslöst."""

    def test_sentiment_spike_signal(self) -> None:
        """Plötzlicher extremer Input nach ruhiger Phase → Signal."""
        mod = M24KalmanPremium()

        # Phase 1: Ruhiger Markt — Filter konvergiert auf niedrige Varianz
        for _ in range(500):
            mod.compute(_make_ticker(
                funding_rate=0.0001,
                mark_price=100_000.0,
                index_price=100_000.0,
            ))

        # Phase 2: Plötzlicher extremer Spike
        result = mod.compute(_make_ticker(
            funding_rate=0.01,   # 100x normal
            mark_price=101_000.0,
            index_price=100_000.0,  # basis = 0.01
        ))

        # Der Sentiment-Z-Score sollte hoch sein
        assert abs(result["sentiment_zscore"]) > KALMAN_SENTIMENT_ZSCORE
        # Signal sollte Fade-Trade sein (gegen den Spike)
        assert result["signal"] != 0

    def test_positive_sentiment_spike_gives_short(self) -> None:
        """Positiver Sentiment-Spike → Short-Signal (Fade)."""
        mod = M24KalmanPremium()

        for _ in range(500):
            mod.compute(_make_ticker(
                funding_rate=0.0001,
                mark_price=100_000.0,
                index_price=100_000.0,
            ))

        result = mod.compute(_make_ticker(
            funding_rate=0.01,
            mark_price=101_000.0,
            index_price=100_000.0,
        ))

        if result["signal"] != 0 and result["sentiment"] > 0:
            assert result["signal"] == -1  # Short = Fade gegen positive Sentiment


class TestNoSignalCalmMarket:
    """Test kein Signal bei ruhigem Markt."""

    def test_no_signal_calm_market(self) -> None:
        """Konstante, moderate Werte → kein Signal (Sentiment nahe 0)."""
        mod = M24KalmanPremium()

        for _ in range(500):
            result = mod.compute(_make_ticker(
                funding_rate=0.0001,
                mark_price=100_000.0,
                index_price=100_000.0,
            ))

        # Bei konstantem Input: Sentiment → 0, kein Spike
        assert result["signal"] == 0
        assert abs(result["sentiment_zscore"]) < KALMAN_SENTIMENT_ZSCORE


class TestResetReinitializes:
    """Test dass reset() den State komplett reinitialisiert."""

    def test_reset_reinitializes(self) -> None:
        """Nach reset() ist der State zurückgesetzt."""
        mod = M24KalmanPremium()

        # Füttere den Filter
        for _ in range(200):
            mod.compute(_make_ticker(
                funding_rate=0.001,
                mark_price=100_050.0,
                index_price=100_000.0,
            ))

        # State sollte nicht-trivial sein
        assert not np.allclose(mod._x, 0.0)

        mod.reset()

        # State ist zurückgesetzt
        assert np.allclose(mod._x, 0.0)
        assert np.allclose(mod._P, np.eye(2) * 1e-4)
        assert mod._initialized is False

    def test_reset_then_compute_no_crash(self) -> None:
        """Nach reset() funktioniert compute() fehlerfrei."""
        mod = M24KalmanPremium()
        mod.reset()
        result = mod.compute(_make_ticker())
        assert result["method_id"] == "M24"
        assert result["signal"] in {-1, 0, 1}


class TestReturnFormat:
    """Test dass alle Required-Keys vorhanden sind."""

    def test_all_keys_present(self) -> None:
        mod = M24KalmanPremium()
        result = mod.compute(_make_ticker())

        required_keys = {
            "signal", "trend", "sentiment", "sentiment_zscore",
            "method_id", "confidence", "ts",
        }
        assert required_keys.issubset(result.keys())

    def test_signal_in_valid_range(self) -> None:
        mod = M24KalmanPremium()
        result = mod.compute(_make_ticker())
        assert result["signal"] in {-1, 0, 1}

    def test_confidence_in_range(self) -> None:
        mod = M24KalmanPremium()
        result = mod.compute(_make_ticker())
        assert 0.0 <= result["confidence"] <= 1.0


class TestValidate:
    """Test validate() Methode."""

    def test_validate_returns_true(self) -> None:
        mod = M24KalmanPremium()
        assert mod.validate() is True

    def test_validate_custom_matrices(self) -> None:
        """Custom-Matrizen mit korrekter Dimension → validate == True."""
        mod = M24KalmanPremium(
            F=np.eye(2),
            H=np.eye(2),
            Q=np.eye(2) * 0.01,
            R=np.eye(2) * 0.01,
        )
        assert mod.validate() is True


class TestCustomMatrices:
    """Test mit benutzerdefinierten Kalman-Matrizen."""

    def test_identity_kalman(self) -> None:
        """Mit Identity-Matrizen für F, H konvergiert der Filter auch."""
        mod = M24KalmanPremium(
            F=np.eye(2),
            H=np.eye(2),
            Q=np.eye(2) * 1e-6,
            R=np.eye(2) * 1e-4,
        )

        for _ in range(100):
            result = mod.compute(_make_ticker(
                funding_rate=0.0002,
                mark_price=100_050.0,
                index_price=100_000.0,
            ))

        assert result["method_id"] == "M24"
