"""
M24 — Kalman-Funding-Premium-Decomposition [L5] [Standard]

Formeln (PRD):
    State equation:       x_t = F * x_{t-1} + w_t,   w_t ~ N(0, Q)
    Observation equation: z_t = H * x_t + v_t,        v_t ~ N(0, R)

    State = [trend_funding, transient_sentiment]
    Observations = [funding_rate, basis]
    Signal: |sentiment_t| > 2 * sqrt(P_22,t) → Fade-Trade

Reine numpy-Implementierung eines 2D-Kalman-Filters — kein pykalman/
filterpy nötig (~40 LOC Kalman-Kern).
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import numpy.typing as npt

from bybit_edge.config import KALMAN_SENTIMENT_ZSCORE
from bybit_edge.layers.base import BaseModule

# Type alias
_Vec2 = npt.NDArray[np.float64]   # shape (2,)
_Mat2 = npt.NDArray[np.float64]   # shape (2, 2)


class M24KalmanPremium(BaseModule):
    """Kalman-Funding-Premium-Decomposition Module.

    Trennt die Funding-Rate in eine persistente Trend-Komponente und
    ein transientes Sentiment-Signal via 2D-Kalman-Filter.
    """

    def __init__(
        self,
        F: _Mat2 | None = None,
        H: _Mat2 | None = None,
        Q: _Mat2 | None = None,
        R: _Mat2 | None = None,
    ) -> None:
        # State-Transition-Matrix (fast Random-Walk für Trend, Mean-Reverting für Sentiment)
        self._F: _Mat2 = (
            F if F is not None
            else np.array([[1.0, 0.0],
                           [0.0, 0.95]], dtype=np.float64)
        )
        # Observation-Matrix: beide Observationen messen beide States
        self._H: _Mat2 = (
            H if H is not None
            else np.array([[1.0, 1.0],
                           [0.0, 1.0]], dtype=np.float64)
        )
        # Process-Noise-Kovarianz
        self._Q: _Mat2 = (
            Q if Q is not None
            else np.array([[1e-8, 0.0],
                           [0.0, 1e-6]], dtype=np.float64)
        )
        # Observation-Noise-Kovarianz
        self._R: _Mat2 = (
            R if R is not None
            else np.array([[1e-6, 0.0],
                           [0.0, 1e-6]], dtype=np.float64)
        )

        # Initial state
        self._x: _Vec2 = np.zeros(2, dtype=np.float64)  # [trend, sentiment]
        self._P: _Mat2 = np.eye(2, dtype=np.float64) * 1e-4  # State-Kovarianz

        self._initialized: bool = False

    # ------------------------------------------------------------------
    # Kalman-Filter Kern
    # ------------------------------------------------------------------

    def _predict(self) -> None:
        """Kalman predict step: propagiert State und Kovarianz."""
        self._x = self._F @ self._x
        self._P = self._F @ self._P @ self._F.T + self._Q

    def _update(self, z: _Vec2) -> None:
        """Kalman update step: korrigiert State mit Beobachtung z."""
        y: _Vec2 = z - self._H @ self._x                # Innovation
        S: _Mat2 = self._H @ self._P @ self._H.T + self._R  # Innovation-Kovarianz
        K: _Mat2 = self._P @ self._H.T @ np.linalg.inv(S)   # Kalman-Gain
        self._x = self._x + K @ y
        I_KH: _Mat2 = np.eye(2, dtype=np.float64) - K @ self._H
        self._P = I_KH @ self._P

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(self, ticker_data: dict[str, Any]) -> dict[str, Any]:
        """Berechne Kalman-decomposed Signal.

        Parameters
        ----------
        ticker_data : dict
            Muss enthalten: ``funding_rate``, ``mark_price``, ``index_price``.

        Returns
        -------
        dict mit signal, trend, sentiment, sentiment_zscore,
        method_id, confidence, ts.
        """
        funding_rate: float = float(ticker_data.get("funding_rate", 0.0))
        mark_price: float = float(ticker_data.get("mark_price", 0.0))
        index_price: float = float(ticker_data.get("index_price", 0.0))

        # Basis berechnen
        if index_price > 0:
            basis: float = (mark_price - index_price) / index_price
        else:
            basis = 0.0

        z: _Vec2 = np.array([funding_rate, basis], dtype=np.float64)

        # Kalman predict + update
        if self._initialized:
            self._predict()
        self._update(z)
        self._initialized = True

        trend: float = float(self._x[0])
        sentiment: float = float(self._x[1])

        # Sentiment-Z-Score aus State-Kovarianz P_22
        p22: float = float(self._P[1, 1])
        if p22 > 0:
            sentiment_sigma: float = float(np.sqrt(p22))
            sentiment_zscore: float = sentiment / sentiment_sigma
        else:
            sentiment_zscore = 0.0

        # Signal: |sentiment| > threshold * sqrt(P_22)
        signal: int = 0
        if abs(sentiment_zscore) > KALMAN_SENTIMENT_ZSCORE:
            # Fade-Trade: gegen den Sentiment-Spike
            signal = -1 if sentiment > 0 else 1

        # Confidence
        confidence: float = (
            min(abs(sentiment_zscore) / (KALMAN_SENTIMENT_ZSCORE * 2), 1.0)
            if signal != 0
            else 0.0
        )

        return {
            "signal": signal,
            "trend": trend,
            "sentiment": sentiment,
            "sentiment_zscore": sentiment_zscore,
            "method_id": "M24",
            "confidence": confidence,
            "ts": time.time(),
        }

    def validate(self) -> bool:
        """Prüft ob Matrizen-Dimensionen korrekt sind."""
        return (
            self._F.shape == (2, 2)
            and self._H.shape == (2, 2)
            and self._Q.shape == (2, 2)
            and self._R.shape == (2, 2)
        )

    def reset(self) -> None:
        """Setzt Kalman-State auf Initialisierungs-Werte zurück."""
        self._x = np.zeros(2, dtype=np.float64)
        self._P = np.eye(2, dtype=np.float64) * 1e-4
        self._initialized = False
