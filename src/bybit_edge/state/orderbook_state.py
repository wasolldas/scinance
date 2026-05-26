"""
Top-50 Orderbook State — sorted arrays, efficient delta-updates.

Uses SortedDict for O(log n) insert/delete and O(1) best-price access.
Consumed by: M2 OFI, M3 Iceberg, M6 Entropie, M14 Hawkes, M25 Kyle.
"""
from __future__ import annotations

import numpy as np
from sortedcontainers import SortedDict


class OrderbookState:
    """Maintains a local copy of a Bybit L2 orderbook (top-N levels).

    Bids are stored in *descending* price order (highest first).
    Asks are stored in *ascending* price order (lowest first).
    """

    def __init__(self, symbol: str, depth: int = 50) -> None:
        self.symbol = symbol
        self.depth = depth
        # SortedDict with negated keys so peekitem(0) returns highest bid
        self.bids: SortedDict = SortedDict(lambda x: -x)
        # SortedDict with natural ordering so peekitem(0) returns lowest ask
        self.asks: SortedDict = SortedDict()
        self.last_update_id: int = 0
        self.last_ts: float = 0.0

    # ------------------------------------------------------------------
    # Snapshot / Delta
    # ------------------------------------------------------------------

    def apply_snapshot(self, data: dict) -> None:
        """Replace entire book from a Bybit ``orderbook`` snapshot.

        Expected *data* shape (Bybit V5 public)::

            {
                "s": "BTCUSDT",
                "b": [["price", "size"], ...],
                "a": [["price", "size"], ...],
                "u": 12345,   # updateId
                "seq": 6789   # optional
            }
        """
        self.bids.clear()
        self.asks.clear()

        for price_str, size_str in data.get("b", []):
            price = float(price_str)
            size = float(size_str)
            if size > 0:
                self.bids[price] = size

        for price_str, size_str in data.get("a", []):
            price = float(price_str)
            size = float(size_str)
            if size > 0:
                self.asks[price] = size

        self._trim()

        if "u" in data:
            self.last_update_id = int(data["u"])
        if "ts" in data:
            self.last_ts = float(data["ts"])

    def apply_delta(self, data: dict) -> None:
        """Incrementally update the book from a Bybit delta message.

        Same schema as snapshot — entries with size == 0 mean deletion.
        """
        for price_str, size_str in data.get("b", []):
            price = float(price_str)
            size = float(size_str)
            if size == 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = size

        for price_str, size_str in data.get("a", []):
            price = float(price_str)
            size = float(size_str)
            if size == 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = size

        self._trim()

        if "u" in data:
            self.last_update_id = int(data["u"])
        if "ts" in data:
            self.last_ts = float(data["ts"])

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def best_bid(self) -> tuple[float, float]:
        """Return ``(price, size)`` of the highest bid.

        Returns ``(0.0, 0.0)`` when the bid side is empty.
        """
        if not self.bids:
            return (0.0, 0.0)
        price = self.bids.keys()[0]
        return (price, self.bids[price])

    @property
    def best_ask(self) -> tuple[float, float]:
        """Return ``(price, size)`` of the lowest ask.

        Returns ``(0.0, 0.0)`` when the ask side is empty.
        """
        if not self.asks:
            return (0.0, 0.0)
        price = self.asks.keys()[0]
        return (price, self.asks[price])

    @property
    def mid_price(self) -> float:
        """Arithmetic mid-point between best bid and best ask.

        Returns 0.0 if either side is empty.
        """
        bid_p, _ = self.best_bid
        ask_p, _ = self.best_ask
        if bid_p == 0.0 or ask_p == 0.0:
            return 0.0
        return (bid_p + ask_p) / 2.0

    @property
    def spread(self) -> float:
        """Absolute spread (best_ask - best_bid).

        Returns 0.0 if either side is empty.
        """
        bid_p, _ = self.best_bid
        ask_p, _ = self.best_ask
        if bid_p == 0.0 or ask_p == 0.0:
            return 0.0
        return ask_p - bid_p

    # ------------------------------------------------------------------
    # Analytics helpers
    # ------------------------------------------------------------------

    def imbalance(self, levels: int = 1) -> float:
        """Normalised bid/ask size imbalance over the top *levels*.

        Returns a value in ``[-1, 1]`` where ``+1`` means all weight
        is on the bid side and ``-1`` means all weight is on the ask side.
        Returns 0.0 when both sides are empty.
        """
        bid_sizes = list(self.bids.values())[:levels]
        ask_sizes = list(self.asks.values())[:levels]

        total_bid = sum(bid_sizes)
        total_ask = sum(ask_sizes)
        total = total_bid + total_ask
        if total == 0:
            return 0.0
        return (total_bid - total_ask) / total

    def top_n_arrays(
        self, n: int = 20
    ) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
        """Return top-*n* bid and ask levels as NumPy arrays.

        Returns::

            ((bid_prices, bid_sizes), (ask_prices, ask_sizes))

        Each array has length ``min(n, available_levels)``.
        """
        bid_prices_list = list(self.bids.keys())[:n]
        bid_sizes_list = [self.bids[p] for p in bid_prices_list]

        ask_prices_list = list(self.asks.keys())[:n]
        ask_sizes_list = [self.asks[p] for p in ask_prices_list]

        return (
            (np.array(bid_prices_list, dtype=np.float64),
             np.array(bid_sizes_list, dtype=np.float64)),
            (np.array(ask_prices_list, dtype=np.float64),
             np.array(ask_sizes_list, dtype=np.float64)),
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _trim(self) -> None:
        """Keep only the top ``self.depth`` levels per side."""
        while len(self.bids) > self.depth:
            # Remove the worst (lowest) bid — last key in descending sort
            self.bids.popitem(-1)
        while len(self.asks) > self.depth:
            # Remove the worst (highest) ask — last key in ascending sort
            self.asks.popitem(-1)
