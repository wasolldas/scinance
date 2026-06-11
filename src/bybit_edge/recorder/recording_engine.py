"""
F0 Recording-Engine (C-36) — additive WebSocket/REST recorder.

Records the NEW Scinance-2.0 streams (FINAL_PRD §3, Pilot 3) next to — never
inside — the existing ``BybitWSCollector`` (DEC-06). Engine properties:

* **Two transports.** The linear public WS (``orderbook.rpi``, ``insurance``,
  ``adlAlert``) and the OPTION public WS (``tickers.{opt}``) live on different
  URLs and are handled as independent connections. Premium-index kline has no
  WS topic, so it is polled over REST.
* **Reconnect** with exponential backoff (same constants as the 1.0 collector:
  1 s → 2 s → … → 60 s).
* **Heartbeat** ping on each connection (delegated to the websockets library's
  ``ping_interval`` / ``ping_timeout``, mirroring the collector).
* **Graceful shutdown** on SIGINT/SIGTERM — buffers are flushed, writers closed.
* **Per-stream buffer + flush interval** via :class:`ParquetStreamWriter`.

**Testability (Constructor-Injection).** The engine never imports
``websockets`` at module import nor hard-codes ``websockets.connect``. Instead
it takes a ``ws_connect`` callable in its constructor. In production this is a
thin wrapper around ``websockets.connect``; in tests the test-engineer injects
a fake async transport (an object yielding canned raw JSON frames) so the full
dispatch → normalise → buffer → flush path is exercised with zero network.
Likewise ``rest_poll`` is an injectable coroutine for the premium-index kline.
"""
from __future__ import annotations

import asyncio
import json
import logging
import signal
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from bybit_edge.config import (
    WS_PING_INTERVAL_SECONDS,
    WS_PING_TIMEOUT_SECONDS,
    WS_RECONNECT_BACKOFF_FACTOR,
    WS_RECONNECT_DELAY_SECONDS,
    WS_RECONNECT_MAX_DELAY_SECONDS,
    ws_public_url,
)
from bybit_edge.recorder.storage import (
    DEFAULT_CAP_GB,
    DEFAULT_FLUSH_ROWS,
    DEFAULT_FLUSH_SECONDS,
    RECORDING_ROOT,
    STREAM_SCHEMAS,
    ParquetStreamWriter,
    StorageCap,
)

logger = logging.getLogger(__name__)

# Option public WS URL — a different endpoint than the linear public stream
# (repo_survey §2.P3). Kept here, not in the 1.0 config, to avoid touching it.
OPTION_WS_URL: str = "wss://stream.bybit.com/v5/public/option"

# REST endpoint for premium-index-price klines (no WS topic exists).
REST_PREMIUM_INDEX_KLINE: str = "/v5/market/premium-index-price-kline"

# How often the storage cap is enforced and telemetry is logged (seconds).
CAP_ENFORCE_INTERVAL_SECONDS: float = 30.0


# Production WS-connect callable. Imported lazily so the module (and the tests
# that inject a fake) never require ``websockets`` to be installed.
async def _default_ws_connect(url: str) -> Any:  # pragma: no cover - thin shim
    import websockets

    return await websockets.connect(
        url,
        ping_interval=WS_PING_INTERVAL_SECONDS,
        ping_timeout=WS_PING_TIMEOUT_SECONDS,
    )


@dataclass
class RecordedMessage:
    """One normalised record on its way from a transport to a writer."""

    stream: str               # key into STREAM_SCHEMAS
    rows: list[dict[str, Any]]  # one or more flat rows for that stream
    recv_ts: float


@dataclass
class StreamSpec:
    """Declarative description of one recorded stream.

    ``topics`` are the WS subscription topics (empty for the REST-polled
    premium-index kline). ``transport`` selects which connection carries it.
    ``normalise`` maps a raw Bybit payload dict to a list of flat rows that
    match ``STREAM_SCHEMAS[stream]``.
    """

    stream: str
    transport: str                              # "linear" | "option" | "rest"
    topics: list[str] = field(default_factory=list)
    normalise: Optional[Callable[[dict, float], list[dict[str, Any]]]] = None


# ══════════════════════════════════════════════════════════════════════
# Payload normalisers — raw Bybit dict -> flat rows for the explicit schema
# ══════════════════════════════════════════════════════════════════════
def _norm_rpi_orderbook(payload: dict, recv_ts: float) -> list[dict[str, Any]]:
    """orderbook.rpi.{symbol}: explode bids/asks into per-level rows."""
    data = payload.get("data", {}) or {}
    ts = int(payload.get("ts", 0) or 0)
    msg_type = str(payload.get("type", ""))
    symbol = str(data.get("s", ""))
    update_id = int(data.get("u", 0) or 0)
    seq = int(data.get("seq", 0) or 0)
    rows: list[dict[str, Any]] = []
    for side_key, side in (("b", "bid"), ("a", "ask")):
        for level, pair in enumerate(data.get(side_key, []) or []):
            try:
                price = float(pair[0])
                size = float(pair[1])
            except (IndexError, TypeError, ValueError):
                continue
            rows.append({
                "ts": ts,
                "symbol": symbol,
                "update_id": update_id,
                "seq": seq,
                "msg_type": msg_type,
                "side": side,
                "level": level,
                "price": price,
                "size": size,
                "recv_ts": recv_ts,
            })
    return rows


def _norm_insurance(payload: dict, recv_ts: float) -> list[dict[str, Any]]:
    """insurance.USDT: one row per coin entry in the data list."""
    ts = int(payload.get("ts", 0) or 0)
    data = payload.get("data", [])
    entries = data if isinstance(data, list) else [data]
    rows: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            balance = float(entry.get("balance", "nan"))
        except (TypeError, ValueError):
            balance = float("nan")
        rows.append({
            "ts": ts,
            "coin": str(entry.get("coin", "")),
            "balance": balance,
            "recv_ts": recv_ts,
        })
    return rows


def _norm_adl_alert(payload: dict, recv_ts: float) -> list[dict[str, Any]]:
    """adlAlert: schema is under-documented — keep raw_json, lift known keys."""
    ts = int(payload.get("ts", 0) or 0)
    data = payload.get("data", {})
    entries = data if isinstance(data, list) else [data]
    rows: list[dict[str, Any]] = []
    for entry in entries:
        entry = entry if isinstance(entry, dict) else {}
        try:
            adl_rank = int(entry.get("adlRankIndicator", 0) or 0)
        except (TypeError, ValueError):
            adl_rank = 0
        rows.append({
            "ts": ts,
            "symbol": str(entry.get("symbol", "")),
            "side": str(entry.get("side", "")),
            "adl_rank": adl_rank,
            "raw_json": json.dumps(entry, separators=(",", ":")),
            "recv_ts": recv_ts,
        })
    return rows


def _norm_premium_index_kline(payload: dict, recv_ts: float) -> list[dict[str, Any]]:
    """REST premium-index-price-kline result -> one row per kline bar.

    Bybit returns ``result.list`` as ``[startTime, open, high, low, close]``
    string arrays; ``result.symbol`` / the request interval are echoed back.
    """
    result = payload.get("result", {}) or {}
    symbol = str(result.get("symbol", payload.get("_symbol", "")))
    interval = str(payload.get("_interval", ""))
    rows: list[dict[str, Any]] = []
    for bar in result.get("list", []) or []:
        try:
            rows.append({
                "ts": int(bar[0]),
                "symbol": symbol,
                "interval": interval,
                "open": float(bar[1]),
                "high": float(bar[2]),
                "low": float(bar[3]),
                "close": float(bar[4]),
                "recv_ts": recv_ts,
            })
        except (IndexError, TypeError, ValueError):
            continue
    return rows


def _norm_option_ticker(payload: dict, recv_ts: float) -> list[dict[str, Any]]:
    """tickers.{optionSymbol} on the option WS: IV/greeks snapshot row."""
    data = payload.get("data", {}) or {}
    ts = int(payload.get("ts", 0) or 0)
    symbol = str(data.get("symbol", ""))
    underlying = symbol.split("-", 1)[0] if "-" in symbol else ""

    def _f(key: str) -> float:
        try:
            return float(data.get(key, "nan"))
        except (TypeError, ValueError):
            return float("nan")

    return [{
        "ts": ts,
        "symbol": symbol,
        "underlying": underlying,
        "mark_price": _f("markPrice"),
        "index_price": _f("indexPrice"),
        "mark_iv": _f("markIv"),
        "underlying_price": _f("underlyingPrice"),
        "delta": _f("delta"),
        "gamma": _f("gamma"),
        "vega": _f("vega"),
        "theta": _f("theta"),
        "open_interest": _f("openInterest"),
        "recv_ts": recv_ts,
    }]


def default_stream_specs(
    linear_symbols: list[str],
    option_underlyings: list[str],
) -> list[StreamSpec]:
    """Build the default set of StreamSpecs for the given symbols.

    Option tickers are subscribed at the underlying level (``tickers.BTC`` /
    ``tickers.ETH`` on the option WS delivers all live contracts for that
    underlying — repo_survey §2.P3).
    """
    rpi_topics = [f"orderbook.rpi.{s}" for s in linear_symbols]
    opt_topics = [f"tickers.{u}" for u in option_underlyings]
    return [
        StreamSpec("rpi_orderbook", "linear", rpi_topics, _norm_rpi_orderbook),
        StreamSpec("insurance_pool", "linear", ["insurance.USDT"], _norm_insurance),
        StreamSpec("adl_alerts", "linear", ["adlAlert"], _norm_adl_alert),
        StreamSpec("option_tickers", "option", opt_topics, _norm_option_ticker),
        StreamSpec("premium_index_kline", "rest", [], _norm_premium_index_kline),
    ]


# Topic-prefix -> stream resolution for symbol-bearing topics whose exact
# ``{symbol}`` suffix is not known at dispatch time.
_TOPIC_PREFIX_TO_STREAM: dict[str, str] = {
    "orderbook.rpi.": "rpi_orderbook",
    "tickers.": "option_tickers",
    "insurance": "insurance_pool",
    "adlAlert": "adl_alerts",
}


class RecordingEngine:
    """Async recorder for the F0 streams. Strictly additive (DEC-06)."""

    def __init__(
        self,
        linear_symbols: Optional[list[str]] = None,
        option_underlyings: Optional[list[str]] = None,
        enabled_streams: Optional[list[str]] = None,
        cap_gb: float = DEFAULT_CAP_GB,
        root=RECORDING_ROOT,
        flush_rows: int = DEFAULT_FLUSH_ROWS,
        flush_seconds: float = DEFAULT_FLUSH_SECONDS,
        ws_connect: Callable[[str], Awaitable[Any]] = _default_ws_connect,
        rest_poll: Optional[Callable[[str, dict], Awaitable[dict]]] = None,
        linear_ws_url: Optional[str] = None,
        option_ws_url: str = OPTION_WS_URL,
        premium_index_interval: str = "1",
        premium_index_poll_seconds: float = 60.0,
    ) -> None:
        self.linear_symbols = linear_symbols or ["BTCUSDT"]
        self.option_underlyings = option_underlyings or ["BTC", "ETH"]

        all_specs = default_stream_specs(self.linear_symbols, self.option_underlyings)
        if enabled_streams is not None:
            wanted = set(enabled_streams)
            unknown = wanted - set(STREAM_SCHEMAS)
            if unknown:
                raise ValueError(
                    f"Unknown stream(s) {sorted(unknown)}; "
                    f"choose from {list(STREAM_SCHEMAS)}"
                )
            all_specs = [s for s in all_specs if s.stream in wanted]
        self.specs: list[StreamSpec] = all_specs

        # Constructor-injected transports (fake-able in tests).
        self._ws_connect = ws_connect
        self._rest_poll = rest_poll
        self.linear_ws_url = linear_ws_url or ws_public_url()
        self.option_ws_url = option_ws_url
        self.premium_index_interval = premium_index_interval
        self.premium_index_poll_seconds = premium_index_poll_seconds

        # Per-stream writers + storage cap.
        self.writers: dict[str, ParquetStreamWriter] = {
            spec.stream: ParquetStreamWriter(
                spec.stream,
                root=root,
                flush_rows=flush_rows,
                flush_seconds=flush_seconds,
            )
            for spec in self.specs
        }
        self.cap = StorageCap(cap_gb=cap_gb, root=root)

        self._running = False
        self._stop_event: Optional[asyncio.Event] = None
        self._tasks: list[asyncio.Task[Any]] = []
        self.messages_recorded: int = 0

    # ------------------------------------------------------------------
    # Stream resolution + record path
    # ------------------------------------------------------------------
    def _spec_for_topic(self, topic: str) -> Optional[StreamSpec]:
        """Resolve a raw WS topic string to its StreamSpec (prefix match)."""
        target: Optional[str] = None
        for prefix, stream in _TOPIC_PREFIX_TO_STREAM.items():
            if topic == prefix or topic.startswith(prefix):
                target = stream
                break
        if target is None:
            return None
        for spec in self.specs:
            if spec.stream == target:
                return spec
        return None

    def record_payload(self, spec: StreamSpec, payload: dict, recv_ts: float) -> int:
        """Normalise one payload and append its rows to the stream buffer.

        Returns the number of rows appended. Public so tests can drive the
        record path directly without a transport.
        """
        if spec.normalise is None:
            return 0
        try:
            rows = spec.normalise(payload, recv_ts)
        except Exception:
            logger.exception("Normaliser failed for stream %s", spec.stream)
            return 0
        writer = self.writers.get(spec.stream)
        if writer is None:
            return 0
        for row in rows:
            writer.append(row)
        if rows:
            self.messages_recorded += 1
        return len(rows)

    def _maybe_flush(self, stream: Optional[str] = None) -> None:
        """Flush writers whose row/time threshold is reached."""
        items = (
            [(stream, self.writers[stream])] if stream else list(self.writers.items())
        )
        for _name, writer in items:
            if writer.should_flush():
                writer.flush()

    # ------------------------------------------------------------------
    # WS consumption loop (one per transport connection)
    # ------------------------------------------------------------------
    async def _run_ws_transport(self, transport: str, url: str, topics: list[str]) -> None:
        """Connect, subscribe, consume — with reconnect/backoff. Runs until stop."""
        delay = WS_RECONNECT_DELAY_SECONDS
        while self._running:
            try:
                ws = await self._ws_connect(url)
                logger.info("[%s] connected to %s", transport, url)
                delay = WS_RECONNECT_DELAY_SECONDS  # reset backoff on success
                await self._subscribe(ws, topics)
                await self._consume(ws, transport)
                # ``_consume`` returned without raising = the stream ended
                # cleanly (server closed, or — in tests — the fake transport
                # exhausted its frames). Yield + small pause so we neither busy-
                # loop on reconnect nor starve the event loop / stop signal.
                if self._running:
                    await asyncio.sleep(WS_RECONNECT_DELAY_SECONDS)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if not self._running:
                    break
                logger.warning(
                    "[%s] connection lost (%s) — reconnecting in %.1f s",
                    transport, exc, delay,
                )
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    raise
                delay = min(delay * WS_RECONNECT_BACKOFF_FACTOR, WS_RECONNECT_MAX_DELAY_SECONDS)

    async def _subscribe(self, ws: Any, topics: list[str]) -> None:
        if not topics:
            return
        msg = json.dumps({"op": "subscribe", "args": topics})
        await ws.send(msg)
        logger.info("Subscribed to %d topic(s): %s", len(topics), topics)

    async def _consume(self, ws: Any, transport: str) -> None:
        """Iterate inbound frames and route them to writers until stop."""
        async for raw in ws:
            if not self._running:
                break
            recv_ts = time.time()
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            topic = payload.get("topic")
            if not topic:
                continue  # subscription ack / heartbeat
            spec = self._spec_for_topic(topic)
            if spec is None or spec.transport != transport:
                continue
            self.record_payload(spec, payload, recv_ts)
            self._maybe_flush(spec.stream)

    # ------------------------------------------------------------------
    # REST premium-index kline poll loop
    # ------------------------------------------------------------------
    async def _run_premium_index_poll(self) -> None:
        spec = next((s for s in self.specs if s.stream == "premium_index_kline"), None)
        if spec is None or self._rest_poll is None:
            return
        while self._running:
            for symbol in self.linear_symbols:
                try:
                    params = {
                        "category": "linear",
                        "symbol": symbol,
                        "interval": self.premium_index_interval,
                        "limit": "200",
                    }
                    result = await self._rest_poll(REST_PREMIUM_INDEX_KLINE, params)
                    recv_ts = time.time()
                    result.setdefault("_symbol", symbol)
                    result["_interval"] = self.premium_index_interval
                    self.record_payload(spec, result, recv_ts)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Premium-index poll failed for %s", symbol)
            self._maybe_flush("premium_index_kline")
            try:
                await asyncio.sleep(self.premium_index_poll_seconds)
            except asyncio.CancelledError:
                raise

    # ------------------------------------------------------------------
    # Storage-cap / flush housekeeping loop
    # ------------------------------------------------------------------
    async def _run_housekeeping(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(CAP_ENFORCE_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                raise
            self._maybe_flush()
            self.cap.enforce()
            logger.info("Storage telemetry: %s", self.cap.usage_report())

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def run(self, duration: Optional[float] = None) -> None:
        """Run the engine until ``stop()``, SIGINT/SIGTERM, or ``duration`` s."""
        self._running = True
        self._stop_event = asyncio.Event()
        self._install_signal_handlers()

        # Group WS topics by transport so each transport opens ONE connection.
        by_transport: dict[str, list[str]] = {}
        for spec in self.specs:
            if spec.transport in ("linear", "option"):
                by_transport.setdefault(spec.transport, []).extend(spec.topics)

        self._tasks = []
        for transport, topics in by_transport.items():
            url = self.linear_ws_url if transport == "linear" else self.option_ws_url
            self._tasks.append(
                asyncio.create_task(self._run_ws_transport(transport, url, topics))
            )
        if any(s.stream == "premium_index_kline" for s in self.specs):
            self._tasks.append(asyncio.create_task(self._run_premium_index_poll()))
        self._tasks.append(asyncio.create_task(self._run_housekeeping()))

        try:
            if duration is not None:
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=duration)
                except asyncio.TimeoutError:
                    logger.info("Recording duration %.0f s reached — stopping.", duration)
            else:
                await self._stop_event.wait()
        finally:
            await self.stop()

    def _install_signal_handlers(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._on_signal)
            except (NotImplementedError, RuntimeError):
                # add_signal_handler is unavailable on some platforms / inside
                # non-main threads (e.g. test event loops). Non-fatal.
                pass

    def _on_signal(self) -> None:
        logger.info("Shutdown signal received — flushing and stopping.")
        if self._stop_event is not None:
            self._stop_event.set()

    async def stop(self) -> None:
        """Graceful shutdown: cancel tasks, flush + close every writer."""
        if not self._running:
            return
        self._running = False
        if self._stop_event is not None:
            self._stop_event.set()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self._tasks = []
        for writer in self.writers.values():
            writer.close()
        self.cap.enforce()
        logger.info(
            "Recorder stopped. messages=%d telemetry=%s",
            self.messages_recorded, self.cap.usage_report(),
        )
