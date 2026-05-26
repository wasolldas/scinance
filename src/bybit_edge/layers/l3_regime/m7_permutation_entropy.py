"""
M7 — Permutation Entropy (Bandt-Pompe) [L3] [Quick Win]

Formeln (PRD):
    Fuer Embedding (m, tau):
        Ordinal-Muster pi von (x_t, x_{t+tau}, ..., x_{t+(m-1)*tau})
    PE_m = -sum_pi p(pi) * log(p(pi))
    Normalisiert: PE_norm = PE_m / log(m!) in [0, 1]

PE nahe 0 -> geordneter/deterministischer Markt (Greenlight).
PE nahe 1 -> chaotischer/zufaelliger Markt (kein Greenlight).
"""

from __future__ import annotations

import math
import time
from collections import Counter, deque
from typing import Any

import numpy as np

from bybit_edge.config import PE_DELAY, PE_ORDER, PE_WINDOW_TICKS
from bybit_edge.layers.base import BaseModule

# 24h bei 1 Update/min = 1440 Samples
_PE_HISTORY_MAXLEN: int = 24 * 60


def _permutation_entropy(prices: np.ndarray, order: int, delay: int) -> float:
    """Berechne normalisierte Permutation Entropy (Bandt-Pompe).

    Parameters
    ----------
    prices : np.ndarray
        1D-Array von Preisen/Werten.
    order : int
        Embedding-Dimension m (typisch 3-7).
    delay : int
        Embedding-Delay tau (typisch 1).

    Returns
    -------
    float
        Normalisierte PE in [0, 1]. Gibt 0.0 zurueck wenn nicht genug Daten.
    """
    n = len(prices)
    required = (order - 1) * delay + 1
    if n < required:
        return 0.0

    # Erzeuge alle Ordinal-Muster
    pattern_counts: Counter[tuple[int, ...]] = Counter()
    num_patterns = n - (order - 1) * delay

    for i in range(num_patterns):
        # Extrahiere Embedding-Vektor
        indices = [i + j * delay for j in range(order)]
        window = [prices[idx] for idx in indices]
        # Ordinal-Muster: Rang-Permutation (argsort)
        pattern = tuple(sorted(range(order), key=lambda k: (window[k], k)))
        pattern_counts[pattern] += 1

    # Berechne Haeufigkeiten -> Wahrscheinlichkeiten
    total = sum(pattern_counts.values())
    if total == 0:
        return 0.0

    # Shannon-Entropie
    entropy = 0.0
    for count in pattern_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log(p)

    # Normalisierung durch log(m!)
    max_entropy = math.log(math.factorial(order))
    if max_entropy == 0:
        return 0.0

    return entropy / max_entropy


class M7PermutationEntropy(BaseModule):
    """Permutation Entropy Regime-Detektor nach Bandt-Pompe.

    Berechnet die normalisierte PE ueber ein rollendes Preis-Fenster.
    Gibt Greenlight wenn PE < 24h-Median (geordneter Markt).
    """

    def __init__(self) -> None:
        # Rolling price buffer (2x Window fuer Sicherheit)
        self._prices: deque[float] = deque(maxlen=PE_WINDOW_TICKS * 2)
        # 24h PE history fuer Median-Tracking
        self._pe_history: deque[float] = deque(maxlen=_PE_HISTORY_MAXLEN)
        # Cached Median
        self._pe_median: float = float("inf")

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------

    def update(self, price: float) -> dict[str, Any]:
        """Verarbeite einen neuen Preis-Tick.

        Parameters
        ----------
        price : float
            Aktueller Preis (z.B. Close oder Last).

        Returns
        -------
        dict mit greenlight, pe, pe_median, signal, method_id, confidence, ts.
        """
        now = time.time()
        self._prices.append(price)

        # Nicht genug Daten
        if len(self._prices) < PE_WINDOW_TICKS:
            return {
                "greenlight": False,
                "pe": float("nan"),
                "pe_median": float("nan"),
                "signal": 0,
                "method_id": "M7",
                "confidence": 0.0,
                "ts": now,
            }

        # PE ueber letztes Window berechnen
        window = np.array(list(self._prices)[-PE_WINDOW_TICKS:], dtype=np.float64)
        pe = _permutation_entropy(window, PE_ORDER, PE_DELAY)

        # 24h-History updaten
        self._pe_history.append(pe)

        # Median updaten (braucht mindestens 2 Werte)
        if len(self._pe_history) >= 2:
            self._pe_median = float(np.median(list(self._pe_history)))

        # Greenlight: PE < Median -> geordneter Markt
        greenlight: bool = False
        if len(self._pe_history) >= 2:
            greenlight = pe < self._pe_median

        # Signal: 1 = geordnet (Greenlight), 0 = chaotisch
        signal: int = 1 if greenlight else 0

        # Confidence: wie weit unter dem Median (skaliert)
        confidence: float = 0.0
        if greenlight and self._pe_median > 0:
            confidence = min((self._pe_median - pe) / self._pe_median, 1.0)

        return {
            "greenlight": greenlight,
            "pe": pe,
            "pe_median": self._pe_median,
            "signal": signal,
            "method_id": "M7",
            "confidence": confidence,
            "ts": now,
        }

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Wrapper um update() fuer BaseModule-Kompatibilitaet.

        Erwartet keyword price oder positional arg.
        """
        price: float = kwargs.get("price", args[0] if len(args) > 0 else 0.0)  # type: ignore[assignment]
        return self.update(price)

    def validate(self) -> bool:
        """Prueft ob PE-Parameter sinnvoll konfiguriert sind."""
        return PE_ORDER >= 2 and PE_DELAY >= 1 and PE_WINDOW_TICKS > (PE_ORDER - 1) * PE_DELAY

    def reset(self) -> None:
        """Setzt internen State vollstaendig zurueck."""
        self._prices.clear()
        self._pe_history.clear()
        self._pe_median = float("inf")
