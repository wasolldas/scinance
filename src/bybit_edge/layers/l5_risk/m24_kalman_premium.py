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

# F/Q are parameterized for this nominal inter-update interval. compute()
# is invoked on irregular ticker updates (not a fixed timer), so _predict()
# rescales F/Q by the actual elapsed wall-clock time relative to this
# reference instead of applying a fixed per-call factor (see
# CRITICAL_REVIEW_2 M24-Finding).
_REFERENCE_DT_SECONDS: float = 1.0

# Floor: guards against a near-zero/degenerate measured dt (e.g. two
# back-to-back calls within the same millisecond) collapsing the process
# noise Q toward zero and effectively freezing the filter. Also a
# reasonable lower bound on realistic exchange ticker cadence.
_MIN_DT_SECONDS: float = 0.01

# Cap: a long reconnect/quiet gap shouldn't blow up decay/process-noise
# scaling beyond "state fully forgotten".
_MAX_DT_SECONDS: float = 3600.0


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
        # Timestamp of the last compute() call (from ticker_data["ts"], NOT
        # wall-clock — see compute()) — used to derive the actual elapsed dt
        # for time-scaled predict().
        self._last_update_ts: float | None = None

    # ------------------------------------------------------------------
    # Kalman-Filter Kern
    # ------------------------------------------------------------------

    def _predict(self, dt: float) -> None:
        """Kalman predict step: propagiert State und Kovarianz über `dt` Sekunden.

        F/Q sind auf `_REFERENCE_DT_SECONDS` parametrisiert. Bei
        unregelmäßigen Aufrufintervallen skalieren wir den Zerfall
        (diagonale F-Einträge) mit `F_ii ** (dt / dt_reference)` und das
        Prozessrauschen Q linear mit `dt / dt_reference`, damit die
        effektive Zerfallsrate von echter verstrichener Zeit abhängt statt
        von der Tick-Dichte. Annahme: F ist diagonal (wie im gesamten
        Modul-Design — Random-Walk-Trend, Mean-Reverting-Sentiment).
        """
        ratio = dt / _REFERENCE_DT_SECONDS
        f_diag = np.maximum(np.diag(self._F), 0.0)
        f_dt_diag = f_diag ** ratio
        F_dt = np.diag(f_dt_diag)

        self._x = F_dt @ self._x
        self._P = F_dt @ self._P @ F_dt.T + self._Q * ratio

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
            Optional: ``ts`` (epoch seconds) — used as the "now" for
            dt-scaling (see ``_predict``); falls back to wall-clock
            ``time.time()`` only if absent.

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

        # "now" MUST come from ticker_data["ts"], not wall-clock time.time():
        # this module also runs inside ReplayBacktester, which feeds ticks at
        # CPU speed while ticker_data["ts"] carries the SIMULATED/event time
        # (see replay_backtester._build_ticker_data). Using real wall-clock
        # time here would make the dt-scaling below measure backtest-loop
        # processing speed instead of actual elapsed market time, silently
        # defeating the fix (same convention as M14 Hawkes's ``current_ts``
        # parameter). live_runner._build_ticker_data sets ts=time.time(), so
        # live behaviour is unchanged.
        now: float = float(ticker_data.get("ts") or time.time())

        # Kalman predict + update. dt is the actual elapsed time (event time
        # in replay, wall-clock in live) since the last call, clamped to a
        # sane range (see _MIN_DT_SECONDS/_MAX_DT_SECONDS) so predict()
        # decays/injects process noise proportional to real elapsed time
        # rather than to the number of compute() calls.
        if self._initialized and self._last_update_ts is not None:
            dt = float(np.clip(now - self._last_update_ts, _MIN_DT_SECONDS, _MAX_DT_SECONDS))
            self._predict(dt)
        self._update(z)
        self._initialized = True
        self._last_update_ts = now

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
            "ts": now,
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
        self._last_update_ts = None
