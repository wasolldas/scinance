"""
WP-2-VERIFY (T0, SANDBOX) — tests for the F0 Recording-Engine (C-36).

Covers the engine half of ``src/bybit_edge/recorder/``:

* per-stream normalisers (all 5) on canned Bybit frames,
* the full async dispatch -> normalise -> buffer -> flush path with a
  constructor-injected fake WS transport (zero network, DEC-06),
* the reconnect/backoff path after a dropped connection,
* malformed-frame robustness (logged + skipped, engine keeps running).

The fake transport follows the builder's injection contract: ``ws_connect``
is an async callable returning an object with ``async send()`` and
``__aiter__`` over canned raw JSON frames; ``rest_poll`` is an injectable
coroutine for the premium-index kline.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Optional

import pytest

import bybit_edge.recorder.recording_engine as engine_mod
from bybit_edge.recorder.recording_engine import (
    REST_PREMIUM_INDEX_KLINE,
    RecordingEngine,
    _norm_adl_alert,
    _norm_insurance,
    _norm_option_ticker,
    _norm_premium_index_kline,
    _norm_rpi_orderbook,
    default_stream_specs,
)
from bybit_edge.recorder.storage import STREAM_SCHEMAS


# ──────────────────────────────────────────────────────────────────────
# Canned Bybit frames (shapes per Bybit v5 public WS / REST docs)
# ──────────────────────────────────────────────────────────────────────
def _rpi_frame(symbol: str = "BTCUSDT") -> dict[str, Any]:
    return {
        "topic": f"orderbook.rpi.{symbol}",
        "type": "snapshot",
        "ts": 1718000000123,
        "data": {
            "s": symbol,
            "u": 7001,
            "seq": 9001,
            "b": [["50000.5", "1.5"], ["49999.0", "2.0"]],
            "a": [["50001.0", "0.5"], ["50002.5", "3.25"]],
        },
    }


def _insurance_frame() -> dict[str, Any]:
    return {
        "topic": "insurance.USDT",
        "ts": 1718000001000,
        "data": [{"coin": "USDT", "balance": "123456789.12"}],
    }


def _adl_frame() -> dict[str, Any]:
    return {
        "topic": "adlAlert",
        "ts": 1718000002000,
        "data": [
            {
                "symbol": "ETHUSDT",
                "side": "Buy",
                "adlRankIndicator": 4,
                "someUndocumentedKey": "keep-me",
            }
        ],
    }


def _option_ticker_frame() -> dict[str, Any]:
    return {
        "topic": "tickers.BTC-27JUN25-60000-C",
        "ts": 1718000003000,
        "data": {
            "symbol": "BTC-27JUN25-60000-C",
            "markPrice": "1234.5",
            "indexPrice": "60123.4",
            "markIv": "0.5567",
            "underlyingPrice": "60100.1",
            "delta": "0.42",
            "gamma": "0.0001",
            "vega": "12.3",
            "theta": "-45.6",
            "openInterest": "789.0",
        },
    }


def _premium_index_rest_payload() -> dict[str, Any]:
    """REST premium-index-price-kline response shape (result.list of bars)."""
    return {
        "retCode": 0,
        "result": {
            "category": "linear",
            "symbol": "BTCUSDT",
            "list": [
                ["1718000040000", "0.0001", "0.0002", "0.00005", "0.00015"],
                ["1718000100000", "0.00015", "0.0003", "0.0001", "0.0002"],
                ["1718000160000", "0.0002", "0.0002", "0.0001", "0.0001"],
            ],
        },
    }


# ──────────────────────────────────────────────────────────────────────
# Fake WS transport (constructor-injected; no network)
# ──────────────────────────────────────────────────────────────────────
class FakeWS:
    """Fake websocket: ``async send()`` + ``__aiter__`` over canned frames.

    ``after`` controls behaviour once frames are exhausted:
      * "hang"  — block until cancelled (steady-state connection),
      * "raise" — raise ConnectionError (dropped connection),
      * "stop"  — clean StopAsyncIteration (server closed stream).
    """

    def __init__(self, frames: list[str], after: str = "hang") -> None:
        self._frames = list(frames)
        self._after = after
        self.sent: list[str] = []

    async def send(self, msg: str) -> None:
        self.sent.append(msg)

    def __aiter__(self) -> "FakeWS":
        return self

    async def __anext__(self) -> str:
        if self._frames:
            await asyncio.sleep(0)  # yield, like a real socket would
            return self._frames.pop(0)
        if self._after == "raise":
            raise ConnectionError("fake connection dropped")
        if self._after == "stop":
            raise StopAsyncIteration
        await asyncio.Event().wait()  # hang until task cancellation
        raise StopAsyncIteration  # pragma: no cover


class FakeConnectFactory:
    """``ws_connect`` stand-in: first connect per URL gets the canned frames,
    every later connect gets an empty hanging socket (unless ``after`` says
    otherwise). Tracks all connections for reconnect assertions."""

    def __init__(
        self,
        frames_by_url_part: dict[str, list[str]],
        after: str = "hang",
        repeat_frames: bool = False,
    ) -> None:
        self._frames = frames_by_url_part
        self._after = after
        self._repeat = repeat_frames
        self._served: set[str] = set()
        self.connections: list[tuple[str, FakeWS]] = []

    def _key_for(self, url: str) -> Optional[str]:
        for part in self._frames:
            if part in url:
                return part
        return None

    async def __call__(self, url: str) -> FakeWS:
        key = self._key_for(url)
        if key is not None and (self._repeat or key not in self._served):
            self._served.add(key)
            ws = FakeWS(self._frames[key], after=self._after)
        else:
            ws = FakeWS([], after="hang")
        self.connections.append((url, ws))
        return ws


def _make_engine(tmp_path, **kwargs: Any) -> RecordingEngine:
    root = tmp_path / "data" / "parquet" / "recording_f0"
    kwargs.setdefault("linear_symbols", ["BTCUSDT"])
    kwargs.setdefault("option_underlyings", ["BTC"])
    return RecordingEngine(root=root, **kwargs)


def _spec(engine: RecordingEngine, stream: str):
    return next(s for s in engine.specs if s.stream == stream)


async def _wait_for(predicate, timeout: float = 3.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.01)
    return predicate()


@pytest.fixture(autouse=True)
def _fast_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shrink reconnect backoff so the async tests run in milliseconds."""
    monkeypatch.setattr(engine_mod, "WS_RECONNECT_DELAY_SECONDS", 0.01)
    monkeypatch.setattr(engine_mod, "WS_RECONNECT_MAX_DELAY_SECONDS", 0.05)


# ══════════════════════════════════════════════════════════════════════
# 1) Normalisers — canned frame -> correct row fields, per stream
# ══════════════════════════════════════════════════════════════════════
class TestNormalisers:
    def test_rpi_orderbook_per_level_rows(self) -> None:
        rows = _norm_rpi_orderbook(_rpi_frame(), recv_ts=1718000000.5)
        # 2 bids + 2 asks exploded into per-level rows.
        assert len(rows) == 4
        bids = [r for r in rows if r["side"] == "bid"]
        asks = [r for r in rows if r["side"] == "ask"]
        assert [b["level"] for b in bids] == [0, 1]
        assert [a["level"] for a in asks] == [0, 1]
        top_bid = bids[0]
        assert top_bid["price"] == pytest.approx(50000.5)
        assert top_bid["size"] == pytest.approx(1.5)
        assert top_bid["symbol"] == "BTCUSDT"
        assert top_bid["update_id"] == 7001
        assert top_bid["seq"] == 9001
        assert top_bid["msg_type"] == "snapshot"
        assert top_bid["ts"] == 1718000000123
        assert top_bid["recv_ts"] == pytest.approx(1718000000.5)
        # Every row matches the declared schema columns exactly.
        schema_cols = set(STREAM_SCHEMAS["rpi_orderbook"].names)
        for row in rows:
            assert set(row) == schema_cols

    def test_rpi_orderbook_skips_corrupt_level(self) -> None:
        frame = _rpi_frame()
        frame["data"]["b"].append(["not-a-price"])  # short/garbage level
        rows = _norm_rpi_orderbook(frame, recv_ts=0.0)
        assert len(rows) == 4  # corrupt level silently dropped, rest kept

    def test_insurance_symbolless_row(self) -> None:
        rows = _norm_insurance(_insurance_frame(), recv_ts=2.0)
        assert len(rows) == 1
        row = rows[0]
        # Symbol-less topic: schema has NO symbol column, coin instead.
        assert set(row) == set(STREAM_SCHEMAS["insurance_pool"].names)
        assert "symbol" not in row
        assert row["coin"] == "USDT"
        assert row["balance"] == pytest.approx(123456789.12)
        assert row["ts"] == 1718000001000

    def test_insurance_accepts_dict_data(self) -> None:
        payload = {"ts": 5, "data": {"coin": "USDT", "balance": "1.0"}}
        rows = _norm_insurance(payload, recv_ts=0.0)
        assert len(rows) == 1 and rows[0]["balance"] == pytest.approx(1.0)

    def test_adl_alert_row_with_raw_json(self) -> None:
        rows = _norm_adl_alert(_adl_frame(), recv_ts=3.0)
        assert len(rows) == 1
        row = rows[0]
        assert set(row) == set(STREAM_SCHEMAS["adl_alerts"].names)
        assert row["symbol"] == "ETHUSDT"
        assert row["side"] == "Buy"
        assert row["adl_rank"] == 4
        # raw_json keeps the FULL entry incl. undocumented keys.
        raw = json.loads(row["raw_json"])
        assert raw["someUndocumentedKey"] == "keep-me"
        assert raw["adlRankIndicator"] == 4

    def test_adl_alert_raw_json_fallback_for_non_dict_entry(self) -> None:
        # Under-documented stream: non-dict entries must not crash; the row
        # falls back to empty typed fields + raw_json of the empty fallback.
        payload = {"ts": 7, "data": ["unexpected-scalar"]}
        rows = _norm_adl_alert(payload, recv_ts=0.0)
        assert len(rows) == 1
        row = rows[0]
        assert row["symbol"] == "" and row["side"] == "" and row["adl_rank"] == 0
        assert json.loads(row["raw_json"]) == {}

    def test_option_ticker_iv_fields(self) -> None:
        rows = _norm_option_ticker(_option_ticker_frame(), recv_ts=4.0)
        assert len(rows) == 1
        row = rows[0]
        assert set(row) == set(STREAM_SCHEMAS["option_tickers"].names)
        assert row["symbol"] == "BTC-27JUN25-60000-C"
        assert row["underlying"] == "BTC"
        assert row["mark_iv"] == pytest.approx(0.5567)
        assert row["underlying_price"] == pytest.approx(60100.1)
        assert row["delta"] == pytest.approx(0.42)
        assert row["gamma"] == pytest.approx(0.0001)
        assert row["vega"] == pytest.approx(12.3)
        assert row["theta"] == pytest.approx(-45.6)
        assert row["open_interest"] == pytest.approx(789.0)

    def test_option_ticker_missing_iv_becomes_nan(self) -> None:
        frame = _option_ticker_frame()
        del frame["data"]["markIv"]
        row = _norm_option_ticker(frame, recv_ts=0.0)[0]
        assert row["mark_iv"] != row["mark_iv"]  # NaN

    def test_premium_index_kline_rest_shape(self) -> None:
        payload = _premium_index_rest_payload()
        payload["_interval"] = "1"
        rows = _norm_premium_index_kline(payload, recv_ts=5.0)
        assert len(rows) == 3
        first = rows[0]
        assert set(first) == set(STREAM_SCHEMAS["premium_index_kline"].names)
        assert first["ts"] == 1718000040000
        assert first["symbol"] == "BTCUSDT"
        assert first["interval"] == "1"
        assert first["open"] == pytest.approx(0.0001)
        assert first["high"] == pytest.approx(0.0002)
        assert first["low"] == pytest.approx(0.00005)
        assert first["close"] == pytest.approx(0.00015)

    def test_premium_index_kline_skips_corrupt_bar(self) -> None:
        payload = _premium_index_rest_payload()
        payload["result"]["list"].append(["1718000220000", "bad-open"])
        payload["_interval"] = "1"
        rows = _norm_premium_index_kline(payload, recv_ts=0.0)
        assert len(rows) == 3  # corrupt bar dropped, no exception

    def test_record_payload_direct_no_transport(self, tmp_path) -> None:
        """record_payload is public and works without any transport."""
        engine = _make_engine(tmp_path)
        n = engine.record_payload(
            _spec(engine, "rpi_orderbook"), _rpi_frame(), recv_ts=1.0
        )
        assert n == 4
        assert engine.messages_recorded == 1
        n2 = engine.record_payload(
            _spec(engine, "insurance_pool"), _insurance_frame(), recv_ts=2.0
        )
        assert n2 == 1 and engine.messages_recorded == 2


# ══════════════════════════════════════════════════════════════════════
# 2) Async run with fake WS transports: N frames -> N rows + clean shutdown
# ══════════════════════════════════════════════════════════════════════
class TestAsyncRun:
    async def test_n_frames_yield_n_rows_and_clean_shutdown(self, tmp_path) -> None:
        linear_frames = [
            json.dumps(_rpi_frame()),                       # 4 rows
            json.dumps(_rpi_frame()),                       # 4 rows
            json.dumps(_insurance_frame()),                 # 1 row
            json.dumps(_adl_frame()),                       # 1 row
        ]
        option_frames = [
            json.dumps(_option_ticker_frame()),             # 1 row
            json.dumps(_option_ticker_frame()),             # 1 row
        ]
        factory = FakeConnectFactory(
            {"linear": linear_frames, "option": option_frames}
        )
        rest_calls: list[tuple[str, dict]] = []

        async def fake_rest_poll(path: str, params: dict) -> dict:
            rest_calls.append((path, params))
            return _premium_index_rest_payload()            # 3 rows

        engine = _make_engine(
            tmp_path,
            ws_connect=factory,
            rest_poll=fake_rest_poll,
            premium_index_poll_seconds=60.0,  # exactly one poll in this test
        )
        task = asyncio.create_task(engine.run())
        # 4 rpi/ins/adl frames + 2 option frames + 1 REST poll = 7 messages.
        assert await _wait_for(lambda: engine.messages_recorded >= 7)
        await engine.stop()
        await asyncio.wait_for(task, timeout=2.0)
        assert task.exception() is None

        # Exact row accounting per stream (close() flushed all buffers).
        assert engine.writers["rpi_orderbook"].rows_written == 8
        assert engine.writers["insurance_pool"].rows_written == 1
        assert engine.writers["adl_alerts"].rows_written == 1
        assert engine.writers["option_tickers"].rows_written == 2
        assert engine.writers["premium_index_kline"].rows_written == 3
        assert rest_calls and rest_calls[0][0] == REST_PREMIUM_INDEX_KLINE

        # Clean shutdown = buffers flushed to disk as Parquet segments.
        root = tmp_path / "data" / "parquet" / "recording_f0"
        for stream in STREAM_SCHEMAS:
            segs = list((root / stream).rglob("*.parquet"))
            assert segs, f"no segment flushed for {stream} on shutdown"

        # Subscriptions are sent PER-SPEC (DEC-08 isolation fix): each
        # subscribe request carries exactly one stream's topics so a rejected
        # topic only kills its own stream. ``adlAlert`` is phantom — never on
        # the wire — so the linear connection sends two subscribes only.
        first_linear_ws = next(
            ws for url, ws in factory.connections if "linear" in url
        )
        linear_subs = [
            json.loads(m) for m in first_linear_ws.sent
            if json.loads(m).get("op") == "subscribe"
        ]
        all_linear_topics = {t for s in linear_subs for t in s["args"]}
        assert "orderbook.rpi.BTCUSDT" in all_linear_topics
        assert "insurance.USDT" in all_linear_topics
        assert "adlAlert" not in all_linear_topics  # phantom, skipped
        # Each subscribe carries a SINGLE spec's topics.
        assert all(len(s["args"]) >= 1 for s in linear_subs)
        rpi_sub = next(s for s in linear_subs if any(
            t.startswith("orderbook.rpi.") for t in s["args"]
        ))
        ins_sub = next(s for s in linear_subs if "insurance.USDT" in s["args"])
        assert rpi_sub is not ins_sub  # separate requests

    async def test_symbolless_topics_dispatch(self, tmp_path) -> None:
        """insurance.USDT / adlAlert resolve without a {symbol} suffix."""
        engine = _make_engine(tmp_path)
        assert engine._spec_for_topic("insurance.USDT").stream == "insurance_pool"
        assert engine._spec_for_topic("adlAlert").stream == "adl_alerts"
        assert (
            engine._spec_for_topic("orderbook.rpi.BTCUSDT").stream
            == "rpi_orderbook"
        )
        assert (
            engine._spec_for_topic("tickers.BTC-27JUN25-60000-C").stream
            == "option_tickers"
        )
        assert engine._spec_for_topic("publicTrade.BTCUSDT") is None

    async def test_unknown_enabled_stream_rejected(self, tmp_path) -> None:
        with pytest.raises(ValueError, match="Unknown stream"):
            _make_engine(tmp_path, enabled_streams=["no_such_stream"])


# ══════════════════════════════════════════════════════════════════════
# 3) Reconnect path: dropped connection -> backoff -> reconnect, no leak
# ══════════════════════════════════════════════════════════════════════
class TestReconnect:
    async def test_reconnects_after_two_frames_then_drop(self, tmp_path) -> None:
        # Every connection serves 2 frames, then raises ConnectionError.
        factory = FakeConnectFactory(
            {"linear": [json.dumps(_rpi_frame()), json.dumps(_insurance_frame())]},
            after="raise",
            repeat_frames=True,
        )
        engine = _make_engine(
            tmp_path,
            enabled_streams=["rpi_orderbook", "insurance_pool"],
            ws_connect=factory,
        )
        task = asyncio.create_task(engine.run())
        # At least 3 connections = at least 2 reconnects after drops.
        assert await _wait_for(lambda: len(factory.connections) >= 3)
        assert engine.messages_recorded >= 4  # frames from >= 2 connections
        await engine.stop()
        await asyncio.wait_for(task, timeout=2.0)
        # The drop never escaped the transport loop.
        assert task.exception() is None
        # Each reconnect re-subscribed.
        for _url, ws in factory.connections[:3]:
            assert ws.sent and json.loads(ws.sent[0])["op"] == "subscribe"


# ══════════════════════════════════════════════════════════════════════
# 4) Malformed frames: logged + skipped, engine keeps running
# ══════════════════════════════════════════════════════════════════════
class TestMalformedFrames:
    async def test_malformed_frames_skipped_engine_continues(
        self, tmp_path, caplog: pytest.LogCaptureFixture
    ) -> None:
        bad_data_frame = {
            "topic": "orderbook.rpi.BTCUSDT",
            "ts": 1,
            "data": ["definitely", "not", "a", "dict"],  # breaks normaliser
        }
        frames = [
            "{this is not valid json",            # JSON decode error
            json.dumps({"success": True, "op": "subscribe"}),  # ack, no topic
            json.dumps(bad_data_frame),           # normaliser exception
            json.dumps(_rpi_frame()),             # valid frame AFTER the junk
        ]
        factory = FakeConnectFactory({"linear": frames})
        engine = _make_engine(
            tmp_path, enabled_streams=["rpi_orderbook"], ws_connect=factory
        )
        with caplog.at_level(
            logging.ERROR, logger="bybit_edge.recorder.recording_engine"
        ):
            task = asyncio.create_task(engine.run())
            # The valid frame behind the malformed ones is still recorded.
            assert await _wait_for(lambda: engine.messages_recorded >= 1)
            await engine.stop()
            await asyncio.wait_for(task, timeout=2.0)

        assert task.exception() is None
        assert engine.writers["rpi_orderbook"].rows_written == 4
        # The normaliser failure was logged, not raised.
        assert any(
            "Normaliser failed" in rec.message for rec in caplog.records
        )

    def test_record_payload_normaliser_crash_returns_zero(
        self, tmp_path, caplog: pytest.LogCaptureFixture
    ) -> None:
        engine = _make_engine(tmp_path)
        spec = _spec(engine, "rpi_orderbook")
        with caplog.at_level(
            logging.ERROR, logger="bybit_edge.recorder.recording_engine"
        ):
            n = engine.record_payload(
                spec, {"topic": "orderbook.rpi.BTCUSDT", "data": [1, 2]}, 0.0
            )
        assert n == 0
        assert engine.messages_recorded == 0
        assert any("Normaliser failed" in r.message for r in caplog.records)


# ══════════════════════════════════════════════════════════════════════
# 5) Keepalive + control-frame diagnosis (NO_DATA runs 2026-06-11/12)
# ══════════════════════════════════════════════════════════════════════
class TestKeepaliveAndAcks:
    def test_keepalive_kwargs_disable_protocol_ping_for_option_ws(self) -> None:
        """Option WS never answers protocol pings (log evidence: client-side
        '1011 keepalive ping timeout' every ~31 s) -> library keepalive off.
        Linear WS keeps the 1.0-collector protocol-ping behaviour."""
        opt = engine_mod._ws_keepalive_kwargs("wss://stream.bybit.com/v5/public/option")
        assert opt == {"ping_interval": None, "ping_timeout": None}
        lin = engine_mod._ws_keepalive_kwargs("wss://stream.bybit.com/v5/public/linear")
        assert lin["ping_interval"] is not None
        assert lin["ping_timeout"] is not None

    async def test_rejected_subscribe_ack_is_logged_as_error(
        self, tmp_path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A success=false subscribe ack MUST surface in the log — it is the
        only evidence that a topic (e.g. orderbook.rpi.*) does not exist."""
        frames = [
            json.dumps({
                "success": False,
                "op": "subscribe",
                "ret_msg": "error:handler not found",
                "conn_id": "abc123",
            }),
            json.dumps(_rpi_frame()),  # engine must keep running afterwards
        ]
        factory = FakeConnectFactory({"linear": frames})
        engine = _make_engine(
            tmp_path, enabled_streams=["rpi_orderbook"], ws_connect=factory
        )
        with caplog.at_level(
            logging.INFO, logger="bybit_edge.recorder.recording_engine"
        ):
            task = asyncio.create_task(engine.run())
            assert await _wait_for(lambda: engine.messages_recorded >= 1)
            await engine.stop()
            await asyncio.wait_for(task, timeout=2.0)

        assert task.exception() is None
        rejected = [
            r for r in caplog.records
            if r.levelno == logging.ERROR and "REJECTED" in r.message
        ]
        assert rejected, "success=false ack was not logged as ERROR"
        assert "handler not found" in rejected[0].message

    async def test_successful_ack_logged_info_not_error(
        self, tmp_path, caplog: pytest.LogCaptureFixture
    ) -> None:
        frames = [
            json.dumps({"success": True, "op": "subscribe", "conn_id": "ok1"}),
            json.dumps(_rpi_frame()),
        ]
        factory = FakeConnectFactory({"linear": frames})
        engine = _make_engine(
            tmp_path, enabled_streams=["rpi_orderbook"], ws_connect=factory
        )
        with caplog.at_level(
            logging.INFO, logger="bybit_edge.recorder.recording_engine"
        ):
            task = asyncio.create_task(engine.run())
            assert await _wait_for(lambda: engine.messages_recorded >= 1)
            await engine.stop()
            await asyncio.wait_for(task, timeout=2.0)
        acks = [r for r in caplog.records if "ack: op=subscribe" in r.message]
        assert acks and all(r.levelno == logging.INFO for r in acks)

    async def test_app_level_ping_sent_on_ws_connections(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Every WS connection gets the Bybit app-level {"op": "ping"}
        heartbeat (the option endpoint dies without it)."""
        monkeypatch.setattr(engine_mod, "APP_PING_INTERVAL_SECONDS", 0.01)
        factory = FakeConnectFactory({"option": [json.dumps(_option_ticker_frame())]})
        engine = _make_engine(
            tmp_path, enabled_streams=["option_tickers"], ws_connect=factory
        )
        task = asyncio.create_task(engine.run())

        def _ping_seen() -> bool:
            return any(
                json.loads(m).get("op") == "ping"
                for _url, ws in factory.connections
                for m in list(ws.sent)
                if m
            )

        assert await _wait_for(_ping_seen)
        await engine.stop()
        await asyncio.wait_for(task, timeout=2.0)
        assert task.exception() is None
        # First message on the wire stays the subscribe request.
        first_ws = factory.connections[0][1]
        assert json.loads(first_ws.sent[0])["op"] == "subscribe"


# ══════════════════════════════════════════════════════════════════════
# 6) Per-spec subscribe (DEC-08): isolation + phantom-skip
# ══════════════════════════════════════════════════════════════════════
class TestPerSpecSubscribeAndPhantom:
    async def test_per_spec_subscribe_isolates_failures(
        self, tmp_path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A rejected subscribe for ONE spec must not kill its siblings.

        Reproduces the 2026-06-12 T2 failure mode in isolation: the engine
        sends one subscribe request per StreamSpec; the fake server rejects
        the rpi_orderbook subscribe with success=false, then keeps streaming
        the insurance frame. The sibling stream must still record data, the
        ERROR must be logged, and the engine must keep running.
        """
        # Two specs share the linear transport. We watch what the engine
        # sends, then return a REJECT for rpi and a valid insurance frame.
        rejected_subs: list[dict[str, Any]] = []

        class IsolatingFakeWS:
            def __init__(self) -> None:
                self.sent: list[str] = []
                self._inbox: asyncio.Queue[str] = asyncio.Queue()
                self._stopped = False

            async def send(self, msg: str) -> None:
                self.sent.append(msg)
                payload = json.loads(msg)
                if payload.get("op") != "subscribe":
                    return
                args = payload.get("args", [])
                if any(t.startswith("orderbook.rpi.") for t in args):
                    ack = {
                        "success": False,
                        "op": "subscribe",
                        "ret_msg": f"error:handler not found,topic:{args[0]}",
                        "conn_id": "iso-1",
                    }
                    rejected_subs.append(ack)
                    await self._inbox.put(json.dumps(ack))
                else:
                    await self._inbox.put(json.dumps({
                        "success": True, "op": "subscribe", "conn_id": "iso-1",
                    }))
                    # After acking insurance, push one valid insurance frame.
                    await self._inbox.put(json.dumps(_insurance_frame()))

            def __aiter__(self) -> "IsolatingFakeWS":
                return self

            async def __anext__(self) -> str:
                if self._stopped:
                    raise StopAsyncIteration
                try:
                    msg = await asyncio.wait_for(self._inbox.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    await asyncio.Event().wait()  # hang until cancel
                    raise StopAsyncIteration  # pragma: no cover
                return msg

            async def close(self) -> None:
                self._stopped = True

        served: list[IsolatingFakeWS] = []

        async def fake_connect(url: str) -> IsolatingFakeWS:
            ws = IsolatingFakeWS() if not served else IsolatingFakeWS()
            served.append(ws)
            return ws

        engine = _make_engine(
            tmp_path,
            enabled_streams=["rpi_orderbook", "insurance_pool"],
            ws_connect=fake_connect,
        )
        with caplog.at_level(
            logging.INFO, logger="bybit_edge.recorder.recording_engine"
        ):
            task = asyncio.create_task(engine.run())
            # Sibling stream MUST still receive data despite rpi rejection
            # (messages_recorded ticks on append; rows_written ticks on flush).
            assert await _wait_for(
                lambda: engine.messages_recorded >= 1,
                timeout=8.0,
            )
            await engine.stop()
            await asyncio.wait_for(task, timeout=2.0)

        assert task.exception() is None
        # The engine sent TWO subscribe requests on the linear transport
        # (one per spec), not one bundled "all-or-nothing" request.
        first_ws = served[0]
        subs = [
            json.loads(m) for m in first_ws.sent
            if json.loads(m).get("op") == "subscribe"
        ]
        assert len(subs) == 2, f"expected per-spec subscribes, got {subs}"
        rpi_sub = next(s for s in subs if any(
            t.startswith("orderbook.rpi.") for t in s["args"]
        ))
        ins_sub = next(s for s in subs if "insurance.USDT" in s["args"])
        # Each request is single-spec (the isolation property).
        assert "insurance.USDT" not in rpi_sub["args"]
        assert not any(t.startswith("orderbook.rpi.") for t in ins_sub["args"])
        # The rejection landed in the log as ERROR with "handler not found".
        errors = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert any("handler not found" in r.message for r in errors)
        assert rejected_subs, "fake server should have answered with success=false"
        # The sibling stream actually wrote its row.
        assert engine.writers["insurance_pool"].rows_written == 1
        assert engine.writers["rpi_orderbook"].rows_written == 0

    async def test_phantom_spec_skipped(
        self, tmp_path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """phantom=True specs are never subscribed, never receive data,
        and emit a single WARN on start so the skip is auditable."""
        # Inject a synthetic phantom spec by overriding default_stream_specs:
        # the engine path is what we want to verify, not just the default set.
        # The default adl_alerts spec is already phantom — exercise THAT.
        # rpi_orderbook stays as a non-phantom sibling so the connection stays
        # up and we can observe that the phantom spec NEVER appears on wire.
        linear_frames = [
            json.dumps(_rpi_frame()),
        ]
        factory = FakeConnectFactory({"linear": linear_frames})
        engine = _make_engine(
            tmp_path,
            enabled_streams=["rpi_orderbook", "adl_alerts"],
            ws_connect=factory,
        )
        # Sanity: the default-spec set marks adl_alerts phantom.
        assert _spec(engine, "adl_alerts").phantom is True
        assert _spec(engine, "rpi_orderbook").phantom is False

        with caplog.at_level(
            logging.WARNING, logger="bybit_edge.recorder.recording_engine"
        ):
            task = asyncio.create_task(engine.run())
            assert await _wait_for(lambda: engine.messages_recorded >= 1)
            await engine.stop()
            await asyncio.wait_for(task, timeout=2.0)

        assert task.exception() is None
        # Subscribe traffic: only rpi_orderbook, never adlAlert.
        first_ws = next(ws for url, ws in factory.connections if "linear" in url)
        all_subs = [
            json.loads(m) for m in first_ws.sent
            if json.loads(m).get("op") == "subscribe"
        ]
        all_topics = {t for s in all_subs for t in s["args"]}
        assert "orderbook.rpi.BTCUSDT" in all_topics
        assert "adlAlert" not in all_topics, "phantom topic must not be on wire"
        # WARN log emitted exactly once per phantom spec per connect.
        phantom_warns = [
            r for r in caplog.records
            if r.levelno == logging.WARNING
            and "phantom" in r.message
            and "adl_alerts" in r.message
        ]
        assert phantom_warns, "phantom-skip WARN was not logged"
        # No data was recorded for the phantom stream.
        assert engine.writers["adl_alerts"].rows_written == 0


# ══════════════════════════════════════════════════════════════════════
# 7) Housekeeping resilience (CRITICAL_REVIEW_2026-07-09,
#    silent-failure-resource-exhaustion regression tests): a failing
#    _maybe_flush()/cap.enforce() must NOT kill the housekeeping loop.
# ══════════════════════════════════════════════════════════════════════
class TestHousekeepingResilience:
    async def test_housekeeping_survives_flush_and_enforce_errors(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Transient errors in _maybe_flush() and cap.enforce() are logged
        with traceback and the loop keeps running: cap.enforce() MUST be
        called again on later intervals (previously a single exception
        killed the coroutine permanently and stop() swallowed it)."""
        monkeypatch.setattr(engine_mod, "CAP_ENFORCE_INTERVAL_SECONDS", 0.01)
        factory = FakeConnectFactory({"linear": [json.dumps(_rpi_frame())]})
        engine = _make_engine(
            tmp_path, enabled_streams=["rpi_orderbook"], ws_connect=factory
        )

        flush_calls = {"n": 0}
        real_maybe_flush = engine._maybe_flush

        def flaky_flush(stream=None):
            if stream is None:  # only fail the housekeeping-wide flush
                flush_calls["n"] += 1
                if flush_calls["n"] == 1:
                    raise OSError("simulated fs error in flush")
            return real_maybe_flush(stream)

        enforce_calls = {"n": 0}
        real_enforce = engine.cap.enforce

        def flaky_enforce():
            enforce_calls["n"] += 1
            if enforce_calls["n"] == 1:
                raise OSError("simulated fs error in enforce")
            return real_enforce()

        monkeypatch.setattr(engine, "_maybe_flush", flaky_flush)
        monkeypatch.setattr(engine.cap, "enforce", flaky_enforce)

        with caplog.at_level(
            logging.INFO, logger="bybit_edge.recorder.recording_engine"
        ):
            task = asyncio.create_task(engine.run())
            # Iter 1 dies in flush, iter 2 dies in enforce; the loop must
            # STILL reach enforce successfully on later iterations.
            assert await _wait_for(lambda: enforce_calls["n"] >= 3)
            await engine.stop()
            await asyncio.wait_for(task, timeout=2.0)

        assert task.exception() is None
        assert flush_calls["n"] >= 2, "housekeeping stopped calling _maybe_flush"
        failures = [
            r for r in caplog.records
            if r.levelno == logging.ERROR
            and "Housekeeping iteration failed" in r.message
        ]
        assert len(failures) >= 2, "per-iteration errors were not logged"
        # Full traceback attached (logger.exception), not just a message.
        assert any(r.exc_info for r in failures)
        # After recovery, telemetry logging resumed (loop fully alive).
        assert any("Storage telemetry" in r.message for r in caplog.records)

    async def test_housekeeping_alarm_after_consecutive_failures(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Persistent failures raise an escalated ALARM log once the
        consecutive-failure threshold is reached — and the loop still keeps
        running (it must never stop while the engine runs)."""
        monkeypatch.setattr(engine_mod, "CAP_ENFORCE_INTERVAL_SECONDS", 0.01)
        monkeypatch.setattr(engine_mod, "HOUSEKEEPING_ALARM_THRESHOLD", 3)
        factory = FakeConnectFactory({"linear": [json.dumps(_rpi_frame())]})
        engine = _make_engine(
            tmp_path, enabled_streams=["rpi_orderbook"], ws_connect=factory
        )

        fail = {"on": True, "n": 0}
        real_enforce = engine.cap.enforce

        def failing_enforce():
            if fail["on"]:
                fail["n"] += 1
                raise OSError("simulated persistent fs error")
            return real_enforce()

        monkeypatch.setattr(engine.cap, "enforce", failing_enforce)
        with caplog.at_level(
            logging.ERROR, logger="bybit_edge.recorder.recording_engine"
        ):
            task = asyncio.create_task(engine.run())
            # Loop survives well past the alarm threshold.
            assert await _wait_for(lambda: fail["n"] >= 5)
            fail["on"] = False  # let shutdown's enforce succeed
            await engine.stop()
            await asyncio.wait_for(task, timeout=2.0)

        assert task.exception() is None
        alarms = [
            r for r in caplog.records
            if r.levelno == logging.ERROR and "ALARM" in r.message
        ]
        assert alarms, "escalated ALARM missing after consecutive failures"


# ══════════════════════════════════════════════════════════════════════
# Spec wiring sanity: StreamSpec names must match the storage schemas
# ══════════════════════════════════════════════════════════════════════
def test_default_stream_specs_cover_all_schemas() -> None:
    specs = default_stream_specs(["BTCUSDT"], ["BTC", "ETH"])
    assert {s.stream for s in specs} == set(STREAM_SCHEMAS)
    by_name = {s.stream: s for s in specs}
    assert by_name["rpi_orderbook"].transport == "linear"
    assert by_name["rpi_orderbook"].topics == ["orderbook.rpi.BTCUSDT"]
    assert by_name["insurance_pool"].topics == ["insurance.USDT"]
    assert by_name["adl_alerts"].topics == ["adlAlert"]
    assert by_name["option_tickers"].transport == "option"
    assert by_name["option_tickers"].topics == ["tickers.BTC", "tickers.ETH"]
    assert by_name["premium_index_kline"].transport == "rest"
    assert by_name["premium_index_kline"].topics == []
    # DEC-08: adlAlert is rejected by the linear endpoint (Bybit T2 evidence
    # 2026-06-12 ``error:handler not found,topic:adlAlert``). The spec stays
    # as an audit trail but is marked phantom so it is never put on the wire.
    assert by_name["adl_alerts"].phantom is True
    # All others must NOT be phantom (regression guard).
    for name in ("rpi_orderbook", "insurance_pool", "option_tickers", "premium_index_kline"):
        assert by_name[name].phantom is False, f"{name} should not be phantom"
