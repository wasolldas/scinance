"""
Ticker state management — stores and provides access to the most recent
ticker snapshots per symbol, sourced from the Bybit ``tickers`` WS stream.

Consumed by: M7, M8, M13, M22, M23, M24, M26.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TickerSnapshot:
    """Immutable snapshot of a single ``tickers`` WS update."""

    symbol: str
    last_price: float
    mark_price: float
    index_price: float
    funding_rate: float
    next_funding_time: int          # Unix milliseconds
    open_interest: float
    open_interest_value: float
    bid1_price: float
    bid1_size: float
    ask1_price: float
    ask1_size: float
    ts: int                         # exchange timestamp (ms)
    recv_ts: float = 0.0            # local time.time() at reception

    @property
    def basis(self) -> float:
        """Basis = (mark_price - index_price) / index_price.

        Returns 0.0 when index_price is zero to prevent division errors.
        """
        if self.index_price == 0:
            return 0.0
        return (self.mark_price - self.index_price) / self.index_price

    @property
    def premium_index(self) -> float:
        """Approximate premium index — same formula as ``basis``."""
        return self.basis

    @property
    def seconds_to_funding(self) -> float:
        """Seconds remaining until the next funding settlement.

        Uses ``next_funding_time`` (ms) relative to the *current* wall-clock.
        Can be negative if the settlement just passed and the ticker has not
        yet updated.
        """
        return (self.next_funding_time / 1000.0) - time.time()

    # ------------------------------------------------------------------
    # Factory from raw Bybit WS data
    # ------------------------------------------------------------------

    @classmethod
    def from_ws(cls, data: dict, recv_ts: float | None = None) -> "TickerSnapshot":
        """Build a ``TickerSnapshot`` from a Bybit V5 tickers WS payload.

        Fields that may be absent in delta updates default to 0 / 0.0.
        """
        return cls(
            symbol=str(data.get("symbol", "")),
            last_price=float(data.get("lastPrice", 0)),
            mark_price=float(data.get("markPrice", 0)),
            index_price=float(data.get("indexPrice", 0)),
            funding_rate=float(data.get("fundingRate", 0)),
            next_funding_time=int(data.get("nextFundingTime", 0)),
            open_interest=float(data.get("openInterest", 0)),
            open_interest_value=float(data.get("openInterestValue", 0)),
            bid1_price=float(data.get("bid1Price", 0)),
            bid1_size=float(data.get("bid1Size", 0)),
            ask1_price=float(data.get("ask1Price", 0)),
            ask1_size=float(data.get("ask1Size", 0)),
            ts=int(data.get("ts", 0)),
            recv_ts=recv_ts if recv_ts is not None else time.time(),
        )


class TickerStateManager:
    """Thread-safe manager that holds the latest ``TickerSnapshot`` per symbol."""

    def __init__(self) -> None:
        self._snapshots: dict[str, TickerSnapshot] = {}

    def update(self, snapshot: TickerSnapshot) -> None:
        """Store or overwrite the snapshot for *snapshot.symbol*."""
        self._snapshots[snapshot.symbol] = snapshot

    def get(self, symbol: str) -> Optional[TickerSnapshot]:
        """Return the latest snapshot for *symbol*, or ``None``."""
        return self._snapshots.get(symbol)

    def symbols(self) -> list[str]:
        """Return all symbols for which we have a snapshot."""
        return list(self._snapshots.keys())

    def all_snapshots(self) -> dict[str, TickerSnapshot]:
        """Return a shallow copy of the internal snapshot dict."""
        return dict(self._snapshots)
