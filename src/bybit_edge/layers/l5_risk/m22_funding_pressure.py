"""
M22 — Funding-Rate-Clamp Pressure-Release [L5] [Quick Win — TOP PRIORITÄT]

Formeln (PRD):
    F_t = P_t + clamp(I_t - P_t, -0.05%, +0.05%)
    Pressure_t = (I_t - P_t) - clamp(I_t - P_t, ±0.05%)
    Signal: |Pressure_t| > 2σ(Pressure_24h) AND T_settlement - t < 30 min

Negative Pressure → Long (Shorts haben "zu wenig" gezahlt → Reversion).
Positive Pressure → Short (Longs haben "zu wenig" gezahlt → Reversion).
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import (
    FUNDING_CLAMP_LOWER,
    FUNDING_CLAMP_UPPER,
    FUNDING_INTEREST_RATE,
    PRESSURE_ENTRY_WINDOW_MINUTES,
    PRESSURE_EXIT_MINUTES_POST_SETTLEMENT,
    PRESSURE_ZSCORE_THRESHOLD,
)
from bybit_edge.layers.base import BaseModule

# Memory-Cap: 24h bei 100ms = 864_000 Samples — wir capen bei 50_000
_PRESSURE_HISTORY_MAXLEN: int = 50_000

# Mindest-Samples bevor wir sigma sinnvoll schätzen
_MIN_SAMPLES_FOR_SIGMA: int = 100


class M22FundingPressure(BaseModule):
    """Funding-Rate-Clamp Pressure-Release Module.

    Berechnet den gestauten Pressure jenseits der Bybit Funding-Clamp-Grenzen
    und erzeugt ein Mean-Reversion-Signal im Settlement-Window.
    """

    def __init__(self) -> None:
        self._pressure_history: deque[float] = deque(maxlen=_PRESSURE_HISTORY_MAXLEN)
        self._24h_sigma: float = 0.0

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(
        self, ticker_data: dict[str, Any], seconds_to_settlement: float
    ) -> dict[str, Any]:
        """Berechne Funding-Pressure-Signal.

        Parameters
        ----------
        ticker_data : dict
            Muss enthalten: ``premium_index``, ``funding_rate``.
            Optional: ``mark_price``, ``index_price``, ``last_price``.
        seconds_to_settlement : float
            Sekunden bis zum nächsten Settlement (>0).

        Returns
        -------
        dict mit signal, pressure, pressure_zscore, funding_rate,
        seconds_to_settlement, in_window, method_id, confidence, ts.
        """
        P_t: float = float(ticker_data.get("premium_index", 0.0))
        I_t: float = FUNDING_INTEREST_RATE

        diff = I_t - P_t
        clamped = float(np.clip(diff, FUNDING_CLAMP_LOWER, FUNDING_CLAMP_UPPER))
        F_t: float = P_t + clamped
        pressure: float = diff - clamped

        # History-Update
        self._pressure_history.append(pressure)

        # Sigma-Update (nur bei genug Samples)
        if len(self._pressure_history) >= _MIN_SAMPLES_FOR_SIGMA:
            self._24h_sigma = float(np.std(list(self._pressure_history)))

        # Window-Check
        in_window: bool = (
            0 < seconds_to_settlement
            < PRESSURE_ENTRY_WINDOW_MINUTES * 60
        )

        # Z-Score (Division-by-Zero sicher)
        if self._24h_sigma > 0:
            pressure_zscore: float = pressure / self._24h_sigma
        else:
            pressure_zscore = 0.0

        # Signal-Bestimmung
        pressure_extreme: bool = (
            self._24h_sigma > 0
            and abs(pressure) > PRESSURE_ZSCORE_THRESHOLD * self._24h_sigma
        )

        signal: int = 0
        if in_window and pressure_extreme:
            # Negative Pressure → Long (Short-Reversion)
            # Positive Pressure → Short (Long-Reversion)
            signal = 1 if pressure < 0 else -1

        # Confidence: skaliert mit abs(zscore), gedeckelt bei 1.0
        confidence: float = min(abs(pressure_zscore) / 4.0, 1.0) if signal != 0 else 0.0

        return {
            "signal": signal,
            "pressure": pressure,
            "pressure_zscore": pressure_zscore,
            "funding_rate": F_t,
            "seconds_to_settlement": seconds_to_settlement,
            "in_window": in_window,
            "method_id": "M22",
            "confidence": confidence,
            "ts": time.time(),
        }

    def validate(self) -> bool:
        """Prüft ob Clamp-Parameter sinnvoll konfiguriert sind."""
        return (
            FUNDING_CLAMP_UPPER > 0
            and FUNDING_CLAMP_LOWER < 0
            and PRESSURE_ZSCORE_THRESHOLD > 0
        )

    def reset(self) -> None:
        """Leert die Pressure-History und setzt sigma zurück."""
        self._pressure_history.clear()
        self._24h_sigma = 0.0
