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

        # Subscriptions were sent on each WS connection that carried topics.
        first_linear_ws = next(
            ws for url, ws in factory.connections if "linear" in url
        )
        sub = json.loads(first_linear_ws.sent[0])
        assert sub["op"] == "subscribe"
        assert "orderbook.rpi.BTCUSDT" in sub["args"]
        assert "insurance.USDT" in sub["args"]
        assert "adlAlert" in sub["args"]

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
