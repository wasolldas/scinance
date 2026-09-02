"""
M6 — Shannon-Entropie L2-Orderbuch [L3] [Quick Win]

Formeln (PRD):
    p_i = size_i / sum(size)   (i = 1..N Levels)
    H_bid = -sum p_i * log2(p_i)
    H_ask = -sum p_i * log2(p_i)
    H_combined = (H_bid + H_ask) / 2
    Greenlight: H < Q5(H_24h)

Niedrige Entropie bedeutet konzentriertes Orderbuch (wenige Levels dominieren),
was auf institutionelle Aktivitaet und somit hoehere Signal-Zuverlaessigkeit
hinweist.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import (
    ENTROPY_EPSILON,
    ENTROPY_GREENLIGHT_QUANTILE,
    ENTROPY_LEVELS,
)
from bybit_edge._legacy_v1.layers.base import BaseModule

# Memory-Cap: 24h bei 100ms = 864_000 Samples — wir capen bei 50_000
_ENTROPY_HISTORY_MAXLEN: int = 50_000

# Mindest-Samples bevor Quantil sinnvoll ist
_MIN_SAMPLES_FOR_QUANTILE: int = 20


class M6ShannonEntropy(BaseModule):
    """Shannon-Entropie Regime-Detektor fuer L2-Orderbuch.

    Berechnet die Shannon-Entropie der Orderbuch-Groessenverteilung
    auf Bid- und Ask-Seite. Niedrige Entropie (< Q5 der 24h-Historie)
    signalisiert konzentrierte Liquiditaet und gibt Greenlight.
    """

    def __init__(self) -> None:
        self._h_history: deque[float] = deque(maxlen=_ENTROPY_HISTORY_MAXLEN)
        self._h_q5: float = float("inf")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _shannon_entropy(self, sizes: np.ndarray) -> float:
        """Berechne Shannon-Entropie einer Groessenverteilung.

        Parameters
        ----------
        sizes : np.ndarray
            1D-Array der Orderbuch-Level-Sizes (Top-N).

        Returns
        -------
        float
            Shannon-Entropie in Bits. 0.0 bei leerem/ungueltigem Input.
        """
        if sizes.size == 0:
            return 0.0

        total = np.sum(sizes)
        if total <= 0.0:
            return 0.0

        probs = sizes / total
        # H = -sum p_i * log2(p_i + epsilon)
        h: float = float(-np.sum(probs * np.log2(probs + ENTROPY_EPSILON)))
        return h

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(self, bid_sizes: np.ndarray, ask_sizes: np.ndarray) -> dict[str, Any]:
        """Berechne Shannon-Entropie-Signal.

        Parameters
        ----------
        bid_sizes : np.ndarray
            Top-N Level Sizes der Bid-Seite (aus OrderbookState).
        ask_sizes : np.ndarray
            Top-N Level Sizes der Ask-Seite (aus OrderbookState).

        Returns
        -------
        dict mit greenlight, h_bid, h_ask, h_combined, h_q5,
        signal, method_id, confidence, ts.
        """
        now = time.time()

        # Sicherheits-Konvertierung zu float64
        bid_sizes = np.asarray(bid_sizes, dtype=np.float64)[:ENTROPY_LEVELS]
        ask_sizes = np.asarray(ask_sizes, dtype=np.float64)[:ENTROPY_LEVELS]

        h_bid = self._shannon_entropy(bid_sizes)
        h_ask = self._shannon_entropy(ask_sizes)
        h_combined = (h_bid + h_ask) / 2.0

        # Rolling-History updaten
        self._h_history.append(h_combined)

        # Q5-Quantil aktualisieren
        if len(self._h_history) >= _MIN_SAMPLES_FOR_QUANTILE:
            self._h_q5 = float(
                np.quantile(list(self._h_history), ENTROPY_GREENLIGHT_QUANTILE)
            )

        # Greenlight: H < Q5
        greenlight: bool = (
            len(self._h_history) >= _MIN_SAMPLES_FOR_QUANTILE
            and h_combined < self._h_q5
        )

        signal: int = 1 if greenlight else 0

        # Confidence: wie weit unter Q5 relativ (skaliert 0..1)
        confidence: float = 0.0
        if greenlight and self._h_q5 > 0.0:
            confidence = min((self._h_q5 - h_combined) / self._h_q5, 1.0)

        return {
            "greenlight": greenlight,
            "h_bid": h_bid,
            "h_ask": h_ask,
            "h_combined": h_combined,
            "h_q5": self._h_q5,
            "signal": signal,
            "method_id": "M6",
            "confidence": confidence,
            "ts": now,
        }

    def validate(self) -> bool:
        """Prueft ob Entropie-Parameter sinnvoll konfiguriert sind."""
        return (
            ENTROPY_LEVELS >= 1
            and 0.0 < ENTROPY_GREENLIGHT_QUANTILE < 1.0
            and ENTROPY_EPSILON > 0.0
        )

    def reset(self) -> None:
        """Setzt internen State vollstaendig zurueck."""
        self._h_history.clear()
        self._h_q5 = float("inf")
