"""
M23 — Mark-Index Basis Settlement Convergence [L5] [Quick Win]

Formeln (PRD):
    Basis_t = (markPrice_t - indexPrice_t) / indexPrice_t
    Signal: Basis > 0.0008  AND  T < 1h  →  Short  (-1)
            Basis < -0.0008 AND  T < 1h  →  Long   (+1)

Persistent positive Basis signalisiert einen überbewerteten Perp — der
Funding-Mechanismus zieht die Basis vor Settlement Richtung 0. Bei
negativer Basis ist der Perp unterbewertet → Long-Entry.
"""

from __future__ import annotations

import time
from typing import Any

from bybit_edge.config import (
    BASIS_ENTRY_WINDOW_MINUTES,
    BASIS_LONG_THRESHOLD,
    BASIS_SHORT_THRESHOLD,
)
from bybit_edge._legacy_v1.layers.base import BaseModule


class M23BasisConvergence(BaseModule):
    """Mark-Index Basis Settlement-Convergence Module.

    Erzeugt ein Convergence-Trade-Signal wenn die Basis zwischen
    Mark- und Index-Price im Settlement-Window eine definierte
    Schwelle überschreitet.
    """

    def compute(
        self, ticker_data: dict[str, Any], seconds_to_settlement: float
    ) -> dict[str, Any]:
        """Berechne Basis-Convergence-Signal.

        Parameters
        ----------
        ticker_data : dict
            Muss enthalten: ``mark_price``, ``index_price``.
        seconds_to_settlement : float
            Sekunden bis zum nächsten Settlement (>0).

        Returns
        -------
        dict mit signal, basis, in_window, method_id, confidence, ts.
        """
        mark_price: float = float(ticker_data.get("mark_price", 0.0))
        index_price: float = float(ticker_data.get("index_price", 0.0))

        # Basis berechnen (Division-by-Zero sicher)
        if index_price > 0:
            basis: float = (mark_price - index_price) / index_price
        else:
            basis = 0.0

        # Window-Check: 0 < seconds_to_settlement < Entry-Window
        in_window: bool = (
            0 < seconds_to_settlement
            < BASIS_ENTRY_WINDOW_MINUTES * 60
        )

        # Signal-Bestimmung
        signal: int = 0
        if in_window:
            if basis > BASIS_SHORT_THRESHOLD:
                signal = -1  # Short: Perp überbewertet → Basis konvergiert nach unten
            elif basis < BASIS_LONG_THRESHOLD:
                signal = 1   # Long: Perp unterbewertet → Basis konvergiert nach oben

        # Confidence: proportional zum Abstand über dem Threshold
        if signal == -1:
            confidence: float = min(
                (basis - BASIS_SHORT_THRESHOLD) / BASIS_SHORT_THRESHOLD, 1.0
            )
        elif signal == 1:
            confidence = min(
                (BASIS_LONG_THRESHOLD - basis) / abs(BASIS_LONG_THRESHOLD), 1.0
            )
        else:
            confidence = 0.0

        return {
            "signal": signal,
            "basis": basis,
            "in_window": in_window,
            "method_id": "M23",
            "confidence": confidence,
            "ts": time.time(),
        }

    def validate(self) -> bool:
        """Prüft ob Basis-Thresholds konfiguriert sind."""
        return (
            BASIS_SHORT_THRESHOLD > 0
            and BASIS_LONG_THRESHOLD < 0
            and BASIS_ENTRY_WINDOW_MINUTES > 0
        )

    def reset(self) -> None:
        """M23 hat keinen internen State — reset ist ein No-Op."""
