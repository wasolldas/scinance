"""
Bybit V5 WebSocket Collector.

- Connects to all required public streams (tickers, publicTrade,
  orderbook.50, allLiquidation).
- Auto-reconnect with exponential backoff (1 s -> 2 s -> 4 s -> ... max 60 s).
- Snapshot resync via REST on reconnect.
- Per-stream asyncio.Queue (max_size=10 000) for Pub/Sub fan-out.
- Schema version tag on every ``WSMessage``.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import aiohttp

try:
    import websockets
    from websockets.exceptions import ConnectionClosed
except ImportError:  # allow import without websockets installed (tests)
    websockets = None  # type: ignore[assignment]
    ConnectionClosed = Exception  # type: ignore[assignment,misc]

from bybit_edge.config import (
    PRIMARY_SYMBOL,
    WS_PING_INTERVAL_SECONDS,
    WS_PING_TIMEOUT_SECONDS,
    WS_RECONNECT_BACKOFF_FACTOR,
    WS_RECONNECT_DELAY_SECONDS,
    WS_RECONNECT_MAX_DELAY_SECONDS,
    ws_public_url,
    rest_base_url,
    REST_ORDERBOOK,
    REST_RECENT_TRADE,
)

logger = logging.getLogger(__name__)

# ── Stream topic templates ────────────────────────────────────────────
STREAMS: dict[str, str] = {
    "tickers": "tickers.{symbol}",
    "trades": "publicTrade.{symbol}",
    "orderbook50": "orderbook.50.{symbol}",
    "liquidation": "allLiquidation.{symbol}",
}


@dataclass
class WSMessage:
    """Envelope that wraps every inbound WS message."""

    stream: str
    symbol: str
    data: dict
    recv_ts: float           # time.time() at reception — event-time anchor
    schema_version: int = 1


class BybitWSCollector:
    """Async WebSocket collector for Bybit V5 public linear streams.

    Usage::

        collector = BybitWSCollector(symbol="BTCUSDT")
        collector.add_handler("tickers", my_ticker_handler)
        await collector.connect()       # runs until disconnect()
    """

    def __init__(
        self,
        symbol: str = PRIMARY_SYMBOL,
        max_queue_size: int = 10_000,
    ) -> None:
        self.symbol = symbol
        self._max_queue_size = max_queue_size

        # Per-stream queues
        self.queues: dict[str, asyncio.Queue[WSMessage]] = {
            name: asyncio.Queue(maxsize=max_queue_size)
            for name in STREAMS
        }

        # Pub/Sub handlers: stream_name -> [handler_fn, ...]
        self._handlers: dict[str, list[Callable[[WSMessage], Any]]] = {
            name: [] for name in STREAMS
        }

        self._ws: Any = None
        self._running = False
        self._reconnect_delay = WS_RECONNECT_DELAY_SECONDS
        self._tasks: list[asyncio.Task[None]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_handler(self, stream: str, handler: Callable[[WSMessage], Any]) -> None:
        """Register a callback for *stream* (e.g. ``"tickers"``)."""
        if stream not in self._handlers:
            raise ValueError(f"Unknown stream: {stream!r}. Choose from {list(STREAMS)}")
        self._handlers[stream].append(handler)

    async def connect(self) -> None:
        """Open the WebSocket and start the receive loop.

        Runs until :meth:`disconnect` is called or the task is cancelled.
        Reconnects automatically on connection loss.
        """
        self._running = True
        while self._running:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                logger.info("Collector cancelled — stopping.")
                break
            except Exception as exc:
                if not self._running:
                    break
                logger.warning(
                    "WS connection lost (%s). Reconnecting in %.1f s …",
                    exc,
                    self._reconnect_delay,
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * WS_RECONNECT_BACKOFF_FACTOR,
                    WS_RECONNECT_MAX_DELAY_SECONDS,
                )
                # Resync orderbook snapshot after reconnect
                await self._snapshot_resync()

    async def subscribe(self) -> None:
        """Send subscription messages for all configured streams."""
        if self._ws is None:
            return
        topics = [
            tpl.format(symbol=self.symbol) for tpl in STREAMS.values()
        ]
        msg = json.dumps({"op": "subscribe", "args": topics})
        await self._ws.send(msg)
        logger.info("Subscribed to %d topics for %s", len(topics), self.symbol)

    async def disconnect(self) -> None:
        """Gracefully close the WebSocket."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
        logger.info("Collector disconnected.")

    # ------------------------------------------------------------------
    # Internal: connect + listen
    # ------------------------------------------------------------------

    async def _connect_and_listen(self) -> None:
        """Open a single WS session, subscribe, and consume messages."""
        url = ws_public_url()
        logger.info("Connecting to %s …", url)

        async with websockets.connect(  # type: ignore[union-attr]
            url,
            ping_interval=WS_PING_INTERVAL_SECONDS,
            ping_timeout=WS_PING_TIMEOUT_SECONDS,
        ) as ws:
            self._ws = ws
            self._reconnect_delay = WS_RECONNECT_DELAY_SECONDS  # reset backoff

            await self.subscribe()

            async for raw in ws:
                if not self._running:
                    break
                recv_ts = time.time()
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    logger.debug("Non-JSON message ignored: %s", raw[:120])
                    continue

                # Bybit sends {"success": true} for subscription ack, skip.
                if "topic" not in payload:
                    continue

                await self._dispatch(payload, recv_ts)

    async def _dispatch(self, payload: dict, recv_ts: float) -> None:
        """Route a parsed payload to the correct queue + handlers."""
        topic: str = payload.get("topic", "")
        raw_data = payload.get("data", {})

        # Determine stream name from topic
        stream_name: Optional[str] = None
        for name, tpl in STREAMS.items():
            expected = tpl.format(symbol=self.symbol)
            if topic == expected:
                stream_name = name
                break

        if stream_name is None:
            logger.debug("Unrecognised topic: %s", topic)
            return

        # Handle data — some streams deliver data as a list
        if isinstance(raw_data, list):
            entries = raw_data
        else:
            entries = [raw_data]

        for entry in entries:
            msg = WSMessage(
                stream=stream_name,
                symbol=self.symbol,
                data=entry,
                recv_ts=recv_ts,
            )

            # Enqueue — drop oldest if full (non-blocking)
            queue = self.queues[stream_name]
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(msg)
            except asyncio.QueueFull:
                pass  # safety fallback

            # Fan-out to registered handlers
            for handler in self._handlers[stream_name]:
                try:
                    result = handler(msg)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    logger.exception(
                        "Handler error on stream %s", stream_name
                    )

    # ------------------------------------------------------------------
    # Snapshot resync (REST)
    # ------------------------------------------------------------------

    async def _snapshot_resync(self) -> None:
        """Fetch a fresh orderbook snapshot + recent trades via REST.

        Called after every reconnect so that local state is consistent.
        """
        base = rest_base_url()
        try:
            async with aiohttp.ClientSession() as session:
                # Orderbook snapshot
                ob_url = f"{base}{REST_ORDERBOOK}"
                params = {"category": "linear", "symbol": self.symbol, "limit": "50"}
                async with session.get(ob_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        body = await resp.json()
                        result = body.get("result", {})
                        recv_ts = time.time()
                        msg = WSMessage(
                            stream="orderbook50",
                            symbol=self.symbol,
                            data=result,
                            recv_ts=recv_ts,
                        )
                        for handler in self._handlers.get("orderbook50", []):
                            try:
                                r = handler(msg)
                                if asyncio.iscoroutine(r):
                                    await r
                            except Exception:
                                logger.exception("Handler error during OB resync")
                        logger.info("Orderbook snapshot resynced for %s", self.symbol)
                    else:
                        logger.warning("OB resync HTTP %d", resp.status)

                # Recent trades
                tr_url = f"{base}{REST_RECENT_TRADE}"
                params_tr = {"category": "linear", "symbol": self.symbol, "limit": "50"}
                async with session.get(tr_url, params=params_tr, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        body = await resp.json()
                        trades_list = body.get("result", {}).get("list", [])
                        recv_ts = time.time()
                        for td in trades_list:
                            msg = WSMessage(
                                stream="trades",
                                symbol=self.symbol,
                                data=td,
                                recv_ts=recv_ts,
                            )
                            for handler in self._handlers.get("trades", []):
                                try:
                                    r = handler(msg)
                                    if asyncio.iscoroutine(r):
                                        await r
                                except Exception:
                                    logger.exception("Handler error during trade resync")
                        logger.info("Trade snapshot resynced (%d trades)", len(trades_list))
                    else:
                        logger.warning("Trade resync HTTP %d", resp.status)
        except Exception:
            logger.exception("Snapshot resync failed — will retry on next reconnect")
