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


class TestLiveRunnerPersistence:
    def test_buffers_fill_when_persist_active(self):
        r = LiveRunner("BTCUSDT")
        # Persist simulieren (kein echtes DuckDB nötig fürs Puffern)
        r.persist = object()  # truthy Platzhalter
        r._on_ticker(_ticker_msg())
        r._on_trade(WSMessage("trades", "BTCUSDT",
                              {"T": 1, "p": "50000", "v": "0.5", "S": "Buy"}, 1.0))
        r._on_liquidation(WSMessage("liquidation", "BTCUSDT",
                                    {"T": 1, "s": "BTCUSDT", "S": "Sell",
                                     "v": "1.0", "p": "49000"}, 1.0))
        assert len(r._buf_tickers) == 1
        assert len(r._buf_trades) == 1
        assert len(r._buf_liqs) == 1

    def test_no_buffering_without_persist(self):
        r = LiveRunner("BTCUSDT")
        assert r.persist is None
        r._on_ticker(_ticker_msg())
        r._on_trade(WSMessage("trades", "BTCUSDT",
                              {"T": 1, "p": "50000", "v": "0.5", "S": "Buy"}, 1.0))
        assert len(r._buf_tickers) == 0
        assert len(r._buf_trades) == 0

    def test_flush_writes_to_duckdb(self):
        from bybit_edge.persistence.db import PersistenceLayer
        r = LiveRunner("BTCUSDT")
        r.persist = PersistenceLayer(db_path=__import__("pathlib").Path(":memory:"))
        r._on_ticker(_ticker_msg())
        r._on_trade(WSMessage("trades", "BTCUSDT",
                              {"T": 1, "p": "50000", "v": "0.5", "S": "Buy"}, 1.0))
        r._on_liquidation(WSMessage("liquidation", "BTCUSDT",
                                    {"T": 1, "s": "BTCUSDT", "S": "Sell",
                                     "v": "1.0", "p": "49000"}, 1.0))
        r._flush_persist()
        counts = r.persist.row_counts()
        assert counts["tickers"] == 1
        assert counts["trades"] == 1
        assert counts["liquidations"] == 1
        # Puffer nach Flush geleert
        assert r._buf_tickers == []
        assert r._persisted == 3
        r.persist.close()

    def test_orderbook_persistence_optin_off_no_buffer(self, monkeypatch):
        """PERSIST_ORDERBOOK=false → kein OB-Puffer trotz aktiver Persistenz."""
        monkeypatch.setattr("bybit_edge.live_runner.PERSIST_ORDERBOOK", False)
        r = LiveRunner("BTCUSDT")
        # Persistenz aktiv simulieren (Buffer-Pfad sonst nicht erreichbar).
        r.persist = object()  # truthy
        snap = WSMessage(
            "orderbook50", "BTCUSDT",
            {"b": [["49999", "2.0"], ["49998", "1.5"]],
             "a": [["50001", "1.5"], ["50002", "0.8"]],
             "u": 1},
            1.0, msg_type="snapshot",
        )
        r._on_orderbook(snap)
        for i in range(5):
            delta = WSMessage(
                "orderbook50", "BTCUSDT",
                {"b": [["49999", str(2.0 + i * 0.1)]], "a": [], "u": 2 + i},
                1.0 + (i + 1) * 0.5, msg_type="delta",
            )
            r._on_orderbook(delta)
        assert r._buf_orderbook_snaps == []
        assert r._last_ob_snap_ts == 0.0

    def test_orderbook_persistence_optin_on_buffers_and_flushes(
        self, monkeypatch
    ):
        """PERSIST_ORDERBOOK=true: respektiert Throttle + Flush → DuckDB."""
        from bybit_edge.persistence.db import PersistenceLayer
        import pathlib

        monkeypatch.setattr("bybit_edge.live_runner.PERSIST_ORDERBOOK", True)
        monkeypatch.setattr("bybit_edge.live_runner.PERSIST_ORDERBOOK_DEPTH", 20)
        monkeypatch.setattr(
            "bybit_edge.live_runner.PERSIST_ORDERBOOK_SNAPSHOT_SECONDS", 1.0
        )

        r = LiveRunner("BTCUSDT")
        r.persist = PersistenceLayer(db_path=pathlib.Path(":memory:"))

        # t=1.0: snapshot creates the book → first OB snapshot persisted.
        snap = WSMessage(
            "orderbook50", "BTCUSDT",
            {"b": [["49999", "2.0"], ["49998", "1.5"], ["49997", "1.0"]],
             "a": [["50001", "1.5"], ["50002", "0.8"], ["50003", "0.6"]],
             "u": 1},
            1.0, msg_type="snapshot",
        )
        r._on_orderbook(snap)

        # t=1.05: delta well inside the 1-s throttle window — must be skipped.
        delta_throttled = WSMessage(
            "orderbook50", "BTCUSDT",
            {"b": [["49999", "2.5"]], "a": [], "u": 2},
            1.05, msg_type="delta",
        )
        r._on_orderbook(delta_throttled)

        # t=2.20: > 1 s past the last snapshot → must be captured.
        delta_ok = WSMessage(
            "orderbook50", "BTCUSDT",
            {"b": [["49999", "2.6"]], "a": [], "u": 3},
            2.20, msg_type="delta",
        )
        r._on_orderbook(delta_ok)

        assert len(r._buf_orderbook_snaps) == 2

        # Flush → DuckDB.
        r._flush_persist()
        assert r._buf_orderbook_snaps == []
        assert r._ob_snaps_persisted == 2

        counts = r.persist.row_counts()
        # 3 bids + 3 asks per snapshot × 2 snapshots = 12 rows.
        assert counts["orderbook_snapshots"] == 12

        # Verify the chronological ordering of stored snapshots.
        recs = r.persist.query_orderbook_snapshots(
            "BTCUSDT", 0, 10_000_000_000_000, depth=20
        )
        assert len(recs) == 2
        assert recs[0]["ts"] == 1000  # int(1.0 * 1000)
        assert recs[1]["ts"] == 2200  # int(2.20 * 1000)
        # Bids are sorted descending in the book → first level is the best bid.
        np.testing.assert_array_almost_equal(
            recs[0]["bid_prices"][:3],
            np.array([49999.0, 49998.0, 49997.0]),
        )
        # Size update at t=2.20 must be reflected.
        assert recs[1]["bid_sizes"][0] == pytest.approx(2.6)

        r.persist.close()


    @pytest.mark.asyncio
    async def test_shared_persist_not_closed_in_stop(self):
        """LiveRunner mit shared_persist darf die geteilte DuckDB-Instanz nicht schließen."""
        from bybit_edge.persistence.db import PersistenceLayer
        import pathlib

        shared = PersistenceLayer(db_path=pathlib.Path(":memory:"))
        r = LiveRunner("BTCUSDT", shared_persist=shared)
        # Simuliere, dass run() die Schicht gemountet hat.
        r.persist = shared
        assert r._owns_persist is False

        await r.stop()
        # Die geteilte Schicht muss weiter benutzbar sein — und der Runner
        # darf sie nicht geschlossen haben.
        counts = shared.row_counts()
        assert isinstance(counts, dict)
        assert r.persist is None
        shared.close()


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
    async def test_long_writes_journal(self, monkeypatch, tmp_path):
        monkeypatch.setattr("bybit_edge.live_runner.EXECUTION_ENABLED", True)
        monkeypatch.setattr("bybit_edge.live_runner.EXECUTION_ORDER_USD", 100.0)
        r = LiveRunner("BTCUSDT")
        r._journal_path = tmp_path / "journal.csv"
        r._on_ticker(_ticker_msg())
        ex = AsyncMock()
        ex.round_qty = lambda q: 0.002
        ex.place_market_order = AsyncMock(
            return_value={"retCode": 0, "result": {"orderId": "abc123"}}
        )
        ex.close_position = AsyncMock(return_value={"retCode": 0})
        r.executor = ex
        await r._act_on_decision(
            {"action": "long", "direction": 1, "strategy_id": "S3",
             "position_size_pct": 0.1, "confidence": 0.6}
        )
        assert r._journal_path.exists()
        content = r._journal_path.read_text(encoding="utf-8")
        assert "S3" in content
        assert "abc123" in content
        assert "Buy" in content

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
