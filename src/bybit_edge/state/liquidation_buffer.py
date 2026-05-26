"""
Rolling buffer for ``allLiquidation`` events from the Bybit WS stream.

Provides helpers used by: M14 Hawkes, M15 Gutenberg-Richter / Omori, M26 SIR.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class LiquidationEvent:
    """Single liquidation tick parsed from the ``allLiquidation`` stream."""

    timestamp_ms: int       # T — exchange timestamp (milliseconds)
    symbol: str             # s
    side: str               # S: "Buy" (short-liq) or "Sell" (long-liq)
    volume: float           # v (contracts / qty)
    price: float            # p (bankruptcy price)
    usd_value: float        # volume * price

    @classmethod
    def from_ws(cls, data: dict) -> "LiquidationEvent":
        """Construct from Bybit V5 ``allLiquidation`` WS payload."""
        price = float(data.get("price", 0))
        volume = float(data.get("size", data.get("qty", 0)))
        return cls(
            timestamp_ms=int(data.get("updatedTime", data.get("T", 0))),
            symbol=str(data.get("symbol", data.get("s", ""))),
            side=str(data.get("side", data.get("S", ""))),
            volume=volume,
            price=price,
            usd_value=volume * price,
        )


class LiquidationBuffer:
    """Fixed-capacity rolling buffer of ``LiquidationEvent`` objects."""

    def __init__(self, maxlen: int = 2000) -> None:
        self._buffer: deque[LiquidationEvent] = deque(maxlen=maxlen)

    def add(self, event: LiquidationEvent) -> None:
        """Append an event (oldest events are evicted when full)."""
        self._buffer.append(event)

    def __len__(self) -> int:
        return len(self._buffer)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def recent(self, seconds: float) -> list[LiquidationEvent]:
        """Return events whose timestamp falls within the last *seconds*.

        Uses ``time.time()`` as the reference clock (wall-clock, not
        exchange time) so that the filter works in live and in tests
        where events carry realistic timestamps.
        """
        cutoff_ms = int((time.time() - seconds) * 1000)
        return [e for e in self._buffer if e.timestamp_ms >= cutoff_ms]

    def recent_by_ts(self, seconds: float, now_ms: int | None = None) -> list[LiquidationEvent]:
        """Return events within the last *seconds* relative to *now_ms*.

        If *now_ms* is ``None``, ``time.time() * 1000`` is used.
        This variant is deterministic and therefore preferred in tests.
        """
        if now_ms is None:
            now_ms = int(time.time() * 1000)
        cutoff_ms = now_ms - int(seconds * 1000)
        return [e for e in self._buffer if e.timestamp_ms >= cutoff_ms]

    def magnitudes_usd(self, seconds: float, now_ms: int | None = None) -> np.ndarray:
        """Return ``log10(usd_value)`` for events in the last *seconds*.

        Used for Gutenberg-Richter *b*-value estimation.
        """
        events = self.recent_by_ts(seconds, now_ms=now_ms)
        if not events:
            return np.array([], dtype=np.float64)
        values = np.array([e.usd_value for e in events], dtype=np.float64)
        # Guard against zero / negative (should not happen, but be safe)
        values = values[values > 0]
        if len(values) == 0:
            return np.array([], dtype=np.float64)
        return np.log10(values)

    def rate_per_second(self, window_seconds: float = 60.0, now_ms: int | None = None) -> float:
        """Average liquidation event rate (events / second) in the window.

        Returns 0.0 when there are no events or the window is zero.
        """
        if window_seconds <= 0:
            return 0.0
        events = self.recent_by_ts(window_seconds, now_ms=now_ms)
        return len(events) / window_seconds
