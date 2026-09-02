"""
M21 -- Long/Short-Ratio Smart-Money Divergenz [L4] [Quick Win]

Formeln (PRD):
    Divergenz_t = sign(Return_1h) - sign(buyRatio - 0.5)
    Signal: Divergenz < 0 AND |buyRatio - 0.5| > 0.25

Smart-Money-Logik:
- Retail extrem long (buyRatio > 0.75) + Preis faellt -> Smart Money shortet
  => signal = -1 (Short folgen)
- Retail extrem short (buyRatio < 0.25) + Preis steigt -> Smart Money long
  => signal = +1 (Long folgen)
- Kein extremer Skew oder Retail und Preis aligned -> signal = 0

Datenquelle: Bybit REST /v5/market/account-ratio (Long/Short-Ratio).
"""

from __future__ import annotations

import math
import time
from typing import Any

from bybit_edge.config import (
    LS_RATIO_DIVERGENCE_THRESHOLD,
)
from bybit_edge._legacy_v1.layers.base import BaseModule


def _sign(x: float) -> float:
    """Vorzeichen-Funktion: +1, -1, oder 0."""
    if x > 0.0:
        return 1.0
    if x < 0.0:
        return -1.0
    return 0.0


class M21LSRatio(BaseModule):
    """Long/Short-Ratio Smart-Money Divergenz Detektor.

    Vergleicht die Retail-Konto-Ratio (buyRatio) mit dem 1h-Return.
    Divergenzen bei extremem Retail-Skew deuten auf Smart-Money-
    Gegenpositionierung hin.
    """

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(
        self,
        buy_ratio: float,
        return_1h: float,
        current_ts: float | None = None,
    ) -> dict[str, Any]:
        """Berechne Smart-Money-Divergenz-Signal.

        Parameters
        ----------
        buy_ratio : float
            Anteil Long-Konten (0.0 bis 1.0),
            aus REST /v5/market/account-ratio.
        return_1h : float
            1h-Return des Symbols (z.B. 0.01 = +1%).
        current_ts : float | None
            Zeitstempel. Falls None, wird time.time() verwendet.

        Returns
        -------
        dict mit divergence, buy_ratio, extreme_skew, signal,
        method_id, confidence, ts.
        """
        now = current_ts if current_ts is not None else time.time()

        # Divergenz: sign(Return_1h) - sign(buyRatio - 0.5)
        sign_return = _sign(return_1h)
        sign_ratio = _sign(buy_ratio - 0.5)
        divergence: float = sign_return - sign_ratio

        # Extremer Skew: |buyRatio - 0.5| > threshold (0.25)
        skew_magnitude: float = abs(buy_ratio - 0.5)
        extreme_skew: bool = skew_magnitude > LS_RATIO_DIVERGENCE_THRESHOLD

        # Signal-Logik
        signal: int = 0
        if extreme_skew and divergence != 0.0:
            # Retail extrem long + Preis faellt -> short
            if buy_ratio > 0.5 + LS_RATIO_DIVERGENCE_THRESHOLD and return_1h < 0.0:
                signal = -1
            # Retail extrem short + Preis steigt -> long
            elif buy_ratio < 0.5 - LS_RATIO_DIVERGENCE_THRESHOLD and return_1h > 0.0:
                signal = 1

        # Confidence: basiert auf Skew-Groesse und Return-Groesse
        confidence: float = 0.0
        if signal != 0:
            # Skew-Confidence: wie weit ueber Threshold
            skew_conf = min(skew_magnitude / 0.5, 1.0)
            # Return-Confidence: hoehere Returns -> mehr Vertrauen
            ret_conf = min(abs(return_1h) / 0.05, 1.0)
            confidence = (skew_conf + ret_conf) / 2.0

        return {
            "divergence": divergence,
            "buy_ratio": buy_ratio,
            "extreme_skew": extreme_skew,
            "signal": signal,
            "method_id": "M21",
            "confidence": confidence,
            "ts": now,
        }

    def validate(self) -> bool:
        """Prueft ob Konfiguration sinnvoll ist."""
        return 0.0 < LS_RATIO_DIVERGENCE_THRESHOLD < 0.5

    def reset(self) -> None:
        """M21 ist stateless -- nichts zurueckzusetzen."""
