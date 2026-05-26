"""
M2 — Order Flow Imbalance (Cont-Kukanov-Stoikov) [L1] [Quick Win]

Formeln (PRD):
    e_n = I(P^b_n >= P^b_{n-1}) * q^b_n
        - I(P^b_n <= P^b_{n-1}) * q^b_{n-1}
        - I(P^a_n <= P^a_{n-1}) * q^a_n
        + I(P^a_n >= P^a_{n-1}) * q^a_{n-1}

    OFI = rolling sum of e_n over window
    Signal: |OFI_rolling_5s| > Q90 -> Trigger

Positive OFI -> starke Kaufseite (signal=1),
Negative OFI -> starke Verkaufsseite (signal=-1).
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import OFI_QUANTILE_THRESHOLD, OFI_WINDOW_SECONDS
from bybit_edge.layers.base import BaseModule

# ~5 min bei ~50 Hz Update-Rate
_OFI_HISTORY_MAXLEN: int = 15_000

# Mindestanzahl Samples bevor Q90 sinnvoll geschaetzt werden kann
_MIN_QUANTILE_SAMPLES: int = 100


class M2OFI(BaseModule):
    """Order Flow Imbalance nach Cont-Kukanov-Stoikov.

    Berechnet den mikrostrukturellen OFI aus best-bid/best-ask Updates
    und erzeugt ein Drucksignal wenn |OFI| ueber dem rollenden Q90 liegt.
    """

    def __init__(self) -> None:
        # Rolling events: (timestamp, e_n)
        self._events: deque[tuple[float, float]] = deque()
        # History of abs(ofi) fuer Quantil-Tracking
        self._ofi_history: deque[float] = deque(maxlen=_OFI_HISTORY_MAXLEN)
        # Previous best bid/ask: (price, size)
        self._prev_bb: tuple[float, float] = (0.0, 0.0)
        self._prev_ba: tuple[float, float] = (0.0, 0.0)
        # Cached Q90 value
        self._q90: float = 0.0
        # Flag: first update has no previous reference
        self._initialized: bool = False

    # ------------------------------------------------------------------
    # Core computation
    # ------------------------------------------------------------------

    def update(
        self,
        best_bid: tuple[float, float],
        best_ask: tuple[float, float],
        ts: float,
    ) -> dict[str, Any]:
        """Verarbeite ein neues Orderbook-BBO-Update.

        Parameters
        ----------
        best_bid : tuple[float, float]
            (price, size) des besten Bids.
        best_ask : tuple[float, float]
            (price, size) des besten Asks.
        ts : float
            Zeitstempel in Sekunden (time.time() oder Exchange-TS).

        Returns
        -------
        dict mit signal, ofi, ofi_q90, e_n, method_id, confidence, ts.
        """
        bid_price, bid_size = best_bid
        ask_price, ask_size = best_ask

        if not self._initialized:
            # Erster Tick: prev speichern, e_n = 0
            self._prev_bb = best_bid
            self._prev_ba = best_ask
            self._initialized = True
            return {
                "signal": 0,
                "ofi": 0.0,
                "ofi_q90": 0.0,
                "e_n": 0.0,
                "method_id": "M2",
                "confidence": 0.0,
                "ts": ts,
            }

        prev_bid_price, prev_bid_size = self._prev_bb
        prev_ask_price, prev_ask_size = self._prev_ba

        # --- e_n nach Cont-Kukanov-Stoikov ---
        e_n: float = 0.0

        # Bid-Seite
        if bid_price >= prev_bid_price:
            e_n += bid_size
        if bid_price <= prev_bid_price:
            e_n -= prev_bid_size

        # Ask-Seite
        if ask_price <= prev_ask_price:
            e_n -= ask_size
        if ask_price >= prev_ask_price:
            e_n += prev_ask_size

        # Update previous
        self._prev_bb = best_bid
        self._prev_ba = best_ask

        # Event in rolling window einfuegen
        self._events.append((ts, e_n))

        # Alte Events ausserhalb des Windows entfernen
        cutoff = ts - OFI_WINDOW_SECONDS
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()

        # Rolling OFI = Summe aller e_n im Fenster
        ofi: float = sum(ev[1] for ev in self._events)

        # Quantile-Update
        self._ofi_history.append(abs(ofi))

        # Q90 berechnen wenn genug History vorhanden
        if len(self._ofi_history) >= _MIN_QUANTILE_SAMPLES:
            self._q90 = float(
                np.quantile(list(self._ofi_history), OFI_QUANTILE_THRESHOLD)
            )

        # Signal-Bestimmung
        signal: int = 0
        if self._q90 > 0 and len(self._ofi_history) >= _MIN_QUANTILE_SAMPLES:
            if ofi > self._q90:
                signal = 1
            elif ofi < -self._q90:
                signal = -1

        # Confidence: skaliert mit Abstand zum Threshold
        confidence: float = 0.0
        if signal != 0 and self._q90 > 0:
            confidence = min(abs(ofi) / (2.0 * self._q90), 1.0)

        return {
            "signal": signal,
            "ofi": ofi,
            "ofi_q90": self._q90,
            "e_n": e_n,
            "method_id": "M2",
            "confidence": confidence,
            "ts": ts,
        }

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Wrapper um update() fuer BaseModule-Kompatibilitaet.

        Erwartet keyword-Argumente best_bid, best_ask, ts
        oder positional in dieser Reihenfolge.
        """
        best_bid: tuple[float, float] = kwargs.get("best_bid", args[0] if len(args) > 0 else (0.0, 0.0))  # type: ignore[assignment]
        best_ask: tuple[float, float] = kwargs.get("best_ask", args[1] if len(args) > 1 else (0.0, 0.0))  # type: ignore[assignment]
        ts: float = kwargs.get("ts", args[2] if len(args) > 2 else time.time())  # type: ignore[assignment]
        return self.update(best_bid, best_ask, ts)

    def validate(self) -> bool:
        """Prueft ob OFI-Parameter sinnvoll konfiguriert sind."""
        return OFI_WINDOW_SECONDS > 0 and 0 < OFI_QUANTILE_THRESHOLD < 1

    def reset(self) -> None:
        """Setzt internen State vollstaendig zurueck."""
        self._events.clear()
        self._ofi_history.clear()
        self._prev_bb = (0.0, 0.0)
        self._prev_ba = (0.0, 0.0)
        self._q90 = 0.0
        self._initialized = False
