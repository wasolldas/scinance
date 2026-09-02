"""
Rolling buffer for ``publicTrade`` events from the Bybit WS stream.

Provides helpers used by: M2 OFI, M14 Hawkes, M25 Kyle's Lambda.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class TradeEvent:
    """Single trade parsed from the ``publicTrade`` stream."""

    timestamp_ms: int       # exchange timestamp (milliseconds)
    price: float
    volume: float
    side: str               # "Buy" or "Sell"
    is_block: bool          # BT flag (block-trade indicator)

    @property
    def signed_volume(self) -> float:
        """Positive for buys, negative for sells."""
        return self.volume if self.side == "Buy" else -self.volume

    @classmethod
    def from_ws(cls, data: dict) -> "TradeEvent":
        """Construct from a Bybit V5 ``publicTrade`` WS payload."""
        return cls(
            timestamp_ms=int(data.get("T", 0)),
            price=float(data.get("p", 0)),
            volume=float(data.get("v", 0)),
            side=str(data.get("S", "")),
            is_block=bool(data.get("BT", False)),
        )


class TradeBuffer:
    """Fixed-capacity rolling buffer of ``TradeEvent`` objects."""

    def __init__(self, maxlen: int = 2000) -> None:
        self._buffer: deque[TradeEvent] = deque(maxlen=maxlen)

    def add(self, event: TradeEvent) -> None:
        """Append a trade (oldest events are evicted when full)."""
        self._buffer.append(event)

    def __len__(self) -> int:
        return len(self._buffer)

    # ------------------------------------------------------------------
    # Vectorised accessors (return most-recent *n* entries)
    # ------------------------------------------------------------------

    def recent_signed_volumes(self, n: int = 100) -> np.ndarray:
        """Signed volumes of the last *n* trades (oldest first)."""
        trades = list(self._buffer)[-n:]
        if not trades:
            return np.array([], dtype=np.float64)
        return np.array([t.signed_volume for t in trades], dtype=np.float64)

    def recent_prices(self, n: int = 100) -> np.ndarray:
        """Prices of the last *n* trades (oldest first)."""
        trades = list(self._buffer)[-n:]
        if not trades:
            return np.array([], dtype=np.float64)
        return np.array([t.price for t in trades], dtype=np.float64)

    def recent_timestamps(self, n: int = 100) -> np.ndarray:
        """Timestamps (ms) of the last *n* trades (oldest first)."""
        trades = list(self._buffer)[-n:]
        if not trades:
            return np.array([], dtype=np.float64)
        return np.array([t.timestamp_ms for t in trades], dtype=np.float64)

    def recent_events(self, n: int = 100) -> list[TradeEvent]:
        """Return the last *n* ``TradeEvent`` objects (oldest first)."""
        return list(self._buffer)[-n:]
