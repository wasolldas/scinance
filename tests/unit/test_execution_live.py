"""
Tests für BybitExecutor (Signing, Rounding, Safety) und LiveRunner
(Handler-Parsing, Pipeline-Eingabe, Decision-Handling).

Keine echten Netzwerk-Calls — alles gemockt.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import numpy as np
import pytest

from bybit_edge.collector.ws_collector import WSMessage
from bybit_edge.execution.bybit_executor import BybitExecutor
from bybit_edge.live_runner import LiveRunner


# ──────────────────────────────────────────────────────────────────
# Executor
# ──────────────────────────────────────────────────────────────────

class TestExecutorSigning:
    def test_sign_deterministic(self):
        ex = BybitExecutor("BTCUSDT", api_key="key", api_secret="secret")
        sig1 = ex._sign("1700000000000", "payload")
        sig2 = ex._sign("1700000000000", "payload")
        assert sig1 == sig2
        assert len(sig1) == 64  # SHA256 hex

    def test_sign_changes_with_payload(self):
        ex = BybitExecutor("BTCUSDT", api_key="key", api_secret="secret")
        assert ex._sign("1700000000000", "a") != ex._sign("1700000000000", "b")

    def test_headers_contain_required_fields(self):
        ex = BybitExecutor("BTCUSDT", api_key="key", api_secret="secret")
        headers = ex._headers("body")
        for field in ("X-BAPI-API-KEY", "X-BAPI-TIMESTAMP", "X-BAPI-RECV-WINDOW", "X-BAPI-SIGN"):
            assert field in headers


class TestExecutorRounding:
    def test_round_qty_to_step(self):
        ex = BybitExecutor("BTCUSDT", api_key="k", api_secret="s")
        ex._qty_step = 0.001
        ex._min_qty = 0.001
        assert ex.round_qty(0.0017) == 0.001
        assert ex.round_qty(0.0025) == 0.002

    def test_round_qty_below_min_returns_zero(self):
        ex = BybitExecutor("BTCUSDT", api_key="k", api_secret="s")
        ex._qty_step = 0.001
        ex._min_qty = 0.01
        assert ex.round_qty(0.005) == 0.0


class TestExecutorSafety:
    def test_live_mode_blocks_without_allow(self, monkeypatch):
        monkeypatch.setattr("bybit_edge.execution.bybit_executor.BYBIT_DEMO", False)
        monkeypatch.setattr("bybit_edge.execution.bybit_executor.BYBIT_TESTNET", False)
        ex = BybitExecutor("BTCUSDT", api_key="k", api_secret="s", allow_live=False)
        assert ex.is_live is True
        with pytest.raises(RuntimeError):
            ex._safety_check()

    def test_demo_mode_allows(self, monkeypatch):
        monkeypatch.setattr("bybit_edge.execution.bybit_executor.BYBIT_DEMO", True)
        monkeypatch.setattr("bybit_edge.execution.bybit_executor.BYBIT_TESTNET", False)
        ex = BybitExecutor("BTCUSDT", api_key="k", api_secret="s")
        assert ex.is_live is False
        ex._safety_check()  # darf nicht werfen

    def test_missing_keys_blocks(self, monkeypatch):
        monkeypatch.setattr("bybit_edge.execution.bybit_executor.BYBIT_DEMO", True)
        ex = BybitExecutor("BTCUSDT", api_key="", api_secret="")
        with pytest.raises(RuntimeError):
            ex._safety_check()


# ──────────────────────────────────────────────────────────────────
# LiveRunner — Handler / State
# ──────────────────────────────────────────────────────────────────

def _ticker_msg(**fields) -> WSMessage:
    base = {
        "symbol": "BTCUSDT",
        "lastPrice": "50000",
        "markPrice": "50010",
        "indexPrice": "50000",
        "fundingRate": "0.0001",
        "nextFundingTime": "0",
        "openInterest": "1000",
    }
    base.update(fields)
    return WSMessage(stream="tickers", symbol="BTCUSDT", data=base, recv_ts=1.0)


class TestLiveRunnerHandlers:
    def test_ticker_handler_merges_delta(self):
        r = LiveRunner("BTCUSDT")
        r._on_ticker(_ticker_msg())
        assert r.ticker is not None
        assert r.ticker.last_price == 50000.0
        # Delta mit nur fundingRate darf last_price nicht auf 0 setzen
        r._on_ticker(WSMessage("tickers", "BTCUSDT", {"fundingRate": "0.0005"}, 2.0))
        assert r.ticker.last_price == 50000.0
        assert r.ticker.funding_rate == 0.0005

    def test_orderbook_snapshot_then_delta(self):
        r = LiveRunner("BTCUSDT")
        snap = WSMessage(
            "orderbook50", "BTCUSDT",
            {"b": [["49999", "2.0"]], "a": [["50001", "1.5"]], "u": 1},
            1.0, msg_type="snapshot",
        )
        r._on_orderbook(snap)
        assert r.orderbook.best_bid == (49999.0, 2.0)
        delta = WSMessage(
            "orderbook50", "BTCUSDT",
            {"b": [["49999", "0"]], "a": [["50001", "3.0"]], "u": 2},
            2.0, msg_type="delta",
        )
        r._on_orderbook(delta)
        assert r.orderbook.best_bid == (0.0, 0.0)  # gelöscht
        assert r.orderbook.best_ask == (50001.0, 3.0)

    def test_trade_handler_fills_buffer_and_prices(self):
        r = LiveRunner("BTCUSDT")
        msg = WSMessage("trades", "BTCUSDT",
                        {"T": 1000, "p": "50000", "v": "0.5", "S": "Buy"}, 1.0)
        r._on_trade(msg)
        assert len(r.trade_buffer) == 1
        assert list(r.price_history) == [50000.0]

    def test_liquidation_handler(self):
        r = LiveRunner("BTCUSDT")
        msg = WSMessage("liquidation", "BTCUSDT",
                        {"T": 1000, "s": "BTCUSDT", "S": "Sell", "v": "1.0", "p": "49000"},
                        1.0)
        r._on_liquidation(msg)
        assert len(r.liq_buffer) == 1


class TestLiveRunnerPipelineInput:
    def test_build_ticker_data_none_without_ticker(self):
        r = LiveRunner("BTCUSDT")
        assert r._build_ticker_data() is None

    def test_build_ticker_data_complete(self):
        r = LiveRunner("BTCUSDT")
        r._on_ticker(_ticker_msg())
        r._on_orderbook(WSMessage(
            "orderbook50", "BTCUSDT",
            {"b": [["49999", "2.0"]], "a": [["50001", "1.5"]], "u": 1},
            1.0, msg_type="snapshot",
        ))
        data = r._build_ticker_data()
        assert data is not None
        assert data["last_price"] == 50000.0
        assert data["best_bid"] == (49999.0, 2.0)
        assert isinstance(data["bid_sizes"], np.ndarray)
        assert data["seconds_to_settlement"] == 3600.0  # next_funding_time=0 -> Default


class TestLiveRunnerDecision:
    @pytest.mark.asyncio
    async def test_act_read_only_no_executor(self):
        r = LiveRunner("BTCUSDT")
        r._on_ticker(_ticker_msg())
        # EXECUTION_ENABLED ist default False -> kein Executor, kein Crash
        await r._act_on_decision(
            {"action": "long", "direction": 1, "strategy_id": "S3",
             "position_size_pct": 0.1, "confidence": 0.6}
        )
        assert r._position_side == ""

    @pytest.mark.asyncio
    async def test_act_long_places_order_when_enabled(self, monkeypatch):
        monkeypatch.setattr("bybit_edge.live_runner.EXECUTION_ENABLED", True)
        monkeypatch.setattr("bybit_edge.live_runner.EXECUTION_ORDER_USD", 100.0)
        r = LiveRunner("BTCUSDT")
        r._on_ticker(_ticker_msg())
        # Executor mocken
        ex = AsyncMock()
        ex.round_qty = lambda q: 0.002
        ex.place_market_order = AsyncMock(return_value={"retCode": 0})
        ex.close_position = AsyncMock(return_value={"retCode": 0})
        r.executor = ex
        await r._act_on_decision(
            {"action": "long", "direction": 1, "strategy_id": "S3",
             "position_size_pct": 0.1, "confidence": 0.6}
        )
        ex.place_market_order.assert_awaited_once()
        assert r._position_side == "Buy"

    @pytest.mark.asyncio
    async def test_act_exit_closes_position(self, monkeypatch):
        monkeypatch.setattr("bybit_edge.live_runner.EXECUTION_ENABLED", True)
        r = LiveRunner("BTCUSDT")
        r._on_ticker(_ticker_msg())
        r._position_side = "Buy"
        ex = AsyncMock()
        ex.close_position = AsyncMock(return_value={"retCode": 0})
        r.executor = ex
        await r._act_on_decision(
            {"action": "exit", "direction": 0, "strategy_id": "S3",
             "position_size_pct": 0.0, "confidence": 0.5}
        )
        ex.close_position.assert_awaited_once()
        assert r._position_side == ""

    @pytest.mark.asyncio
    async def test_act_hold_same_side(self, monkeypatch):
        monkeypatch.setattr("bybit_edge.live_runner.EXECUTION_ENABLED", True)
        r = LiveRunner("BTCUSDT")
        r._on_ticker(_ticker_msg())
        r._position_side = "Buy"
        ex = AsyncMock()
        ex.place_market_order = AsyncMock()
        r.executor = ex
        await r._act_on_decision(
            {"action": "long", "direction": 1, "strategy_id": "S3",
             "position_size_pct": 0.1, "confidence": 0.6}
        )
        ex.place_market_order.assert_not_awaited()  # bereits Buy -> halten
