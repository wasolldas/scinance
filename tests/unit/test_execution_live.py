"""
Tests für BybitExecutor (Signing, Rounding, Safety) und LiveRunner
(Handler-Parsing, Pipeline-Eingabe, Decision-Handling).

Keine echten Netzwerk-Calls — alles gemockt.
"""
from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import duckdb
import numpy as np
import pytest

from bybit_edge._legacy_v1.collector.ws_collector import BybitWSCollector, WSMessage
from bybit_edge._legacy_v1.execution.bybit_executor import BybitExecutor
from bybit_edge._legacy_v1.live_runner import LiveRunner


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
        monkeypatch.setattr("bybit_edge._legacy_v1.execution.bybit_executor.BYBIT_DEMO", False)
        monkeypatch.setattr("bybit_edge._legacy_v1.execution.bybit_executor.BYBIT_TESTNET", False)
        ex = BybitExecutor("BTCUSDT", api_key="k", api_secret="s", allow_live=False)
        assert ex.is_live is True
        with pytest.raises(RuntimeError):
            ex._safety_check()

    def test_demo_mode_allows(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.execution.bybit_executor.BYBIT_DEMO", True)
        monkeypatch.setattr("bybit_edge._legacy_v1.execution.bybit_executor.BYBIT_TESTNET", False)
        ex = BybitExecutor("BTCUSDT", api_key="k", api_secret="s")
        assert ex.is_live is False
        ex._safety_check()  # darf nicht werfen

    def test_missing_keys_blocks(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.execution.bybit_executor.BYBIT_DEMO", True)
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

    def test_on_ticker_uses_envelope_ts(self):
        """The envelope exchange ts from the WSMessage lands on the snapshot."""
        r = LiveRunner("BTCUSDT")
        msg = WSMessage(
            stream="tickers", symbol="BTCUSDT",
            data={"symbol": "BTCUSDT", "lastPrice": "50000"},
            recv_ts=1.0, envelope_ts=1700000000123,
        )
        r._on_ticker(msg)
        assert r.ticker is not None
        assert r.ticker.ts == 1700000000123

    def test_on_ticker_default_envelope_ts_zero(self):
        """Helper WSMessages without envelope_ts default to ts=0 (back-compat)."""
        r = LiveRunner("BTCUSDT")
        r._on_ticker(_ticker_msg())
        assert r.ticker is not None
        assert r.ticker.ts == 0

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
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.PERSIST_ORDERBOOK", False)
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

        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.PERSIST_ORDERBOOK", True)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.PERSIST_ORDERBOOK_DEPTH", 20)
        monkeypatch.setattr(
            "bybit_edge._legacy_v1.live_runner.PERSIST_ORDERBOOK_SNAPSHOT_SECONDS", 1.0
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
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ORDER_USD", 100.0)
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
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
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
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ORDER_USD", 100.0)
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
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
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

    @pytest.mark.asyncio
    async def test_risk_block_skips_order(self, monkeypatch, tmp_path):
        """Wenn das Risiko-Budget ``check_entry_allowed`` → False meldet,
        wird keine Order gesendet und ein risk_block-Journaleintrag geschrieben."""
        from bybit_edge._legacy_v1.risk import RiskBudget
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ORDER_USD", 100.0)
        r = LiveRunner("BTCUSDT")
        r._journal_path = tmp_path / "journal.csv"
        r._on_ticker(_ticker_msg())
        ex = AsyncMock()
        ex.round_qty = lambda q: 0.002
        ex.place_market_order = AsyncMock(return_value={"retCode": 0})
        ex.close_position = AsyncMock(return_value={"retCode": 0})
        r.executor = ex

        # Risiko-Budget mit erzwungenem Daily-Loss-Block.
        rb = RiskBudget(
            daily_loss_pct=-0.03,
            max_dd_pct=-0.15,
            vol_scaling_enabled=False,
            vol_target_bps=50.0,
            state_path=tmp_path / "risk_state.json",
        )
        rb.load(current_equity=1000.0)
        rb.on_equity_update(equity=900.0)  # 10% Verlust → daily_loss
        assert rb.state.blocked_reason == "daily_loss"
        r.risk_budget = rb

        await r._act_on_decision(
            {"action": "long", "direction": 1, "strategy_id": "S3",
             "position_size_pct": 0.1, "confidence": 0.6}
        )
        ex.place_market_order.assert_not_awaited()
        assert r._position_side == ""
        # Journaleintrag mit action=risk_block, ret_code=-1
        content = r._journal_path.read_text(encoding="utf-8")
        assert "risk_block" in content
        assert "-1" in content

    @pytest.mark.asyncio
    async def test_force_close_triggers_close_position(self, monkeypatch, tmp_path):
        """should_force_close() → True ⇒ offene Position wird geschlossen,
        kein neuer Entry."""
        from bybit_edge._legacy_v1.risk import RiskBudget
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ORDER_USD", 100.0)
        r = LiveRunner("BTCUSDT")
        r._journal_path = tmp_path / "journal.csv"
        r._on_ticker(_ticker_msg())
        # Position auf Gegenseite, damit der "halte"-Early-Return nicht greift.
        r._position_side = "Sell"
        ex = AsyncMock()
        ex.round_qty = lambda q: 0.002
        ex.place_market_order = AsyncMock(return_value={"retCode": 0})
        ex.close_position = AsyncMock(return_value={"retCode": 0})
        r.executor = ex

        rb = RiskBudget(
            daily_loss_pct=-0.50,
            max_dd_pct=-0.15,
            vol_scaling_enabled=False,
            vol_target_bps=50.0,
            state_path=tmp_path / "risk_state.json",
        )
        rb.load(current_equity=1000.0)
        rb.on_equity_update(equity=2000.0)  # peak
        rb.on_equity_update(equity=1600.0)  # -20% vom peak → max_drawdown
        assert rb.should_force_close() is True
        r.risk_budget = rb

        await r._act_on_decision(
            {"action": "long", "direction": 1, "strategy_id": "S3",
             "position_size_pct": 0.1, "confidence": 0.6}
        )
        ex.close_position.assert_awaited_once()
        ex.place_market_order.assert_not_awaited()
        assert r._position_side == ""

    @pytest.mark.asyncio
    async def test_vol_scaling_changes_qty(self, monkeypatch, tmp_path):
        """``adjust_qty`` wird VOR ``round_qty`` aufgerufen und beeinflusst die
        finale Order-Größe."""
        from bybit_edge._legacy_v1.risk import RiskBudget
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ORDER_USD", 100.0)
        r = LiveRunner("BTCUSDT")
        r._journal_path = tmp_path / "journal.csv"
        r._on_ticker(_ticker_msg())

        # Erfasse, welche raw_qty bei round_qty ankommt.
        received: list[float] = []

        def fake_round(q):
            received.append(q)
            return 0.002

        ex = AsyncMock()
        ex.round_qty = fake_round
        ex.place_market_order = AsyncMock(return_value={"retCode": 0})
        ex.close_position = AsyncMock(return_value={"retCode": 0})
        r.executor = ex

        # Vol-Scaling aktiv mit klarem Scaling-Faktor (high target → 2x cap).
        rb = RiskBudget(
            daily_loss_pct=-0.50,
            max_dd_pct=-0.50,
            vol_scaling_enabled=True,
            vol_target_bps=10_000.0,  # absurd hoch → scale -> _VOL_SCALE_MAX
            state_path=tmp_path / "risk_state.json",
        )
        rb.load(current_equity=1000.0)
        r.risk_budget = rb
        # Sehr ruhige Preise (kleine returns) → realisierte Vol gering →
        # scale geht gegen MAX (2.0).
        for px in np.linspace(50000.0, 50001.0, 50):
            r.price_history.append(float(px))

        await r._act_on_decision(
            {"action": "long", "direction": 1, "strategy_id": "S3",
             "position_size_pct": 0.1, "confidence": 0.6}
        )
        # raw_qty (ohne scaling) wäre 100 / 50000 = 0.002.
        # Scaling Cap 2.0 → erwartete raw_qty ≈ 0.004.
        assert received, "round_qty wurde nicht aufgerufen"
        assert received[0] == pytest.approx(0.004, rel=1e-6)
        ex.place_market_order.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_act_exit_close_failure_keeps_position_side(self, monkeypatch):
        """Ein fehlgeschlagenes Close (retCode != 0) darf ``_position_side``
        NICHT auf 'flat' zurücksetzen — sonst desynchronisiert der interne
        Status lautlos von der echten Exchange-Position."""
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
        r = LiveRunner("BTCUSDT")
        r._on_ticker(_ticker_msg())
        r._position_side = "Buy"
        ex = AsyncMock()
        ex.close_position = AsyncMock(
            return_value={"retCode": 110007, "retMsg": "insufficient margin"}
        )
        r.executor = ex
        await r._act_on_decision(
            {"action": "exit", "direction": 0, "strategy_id": "S3",
             "position_size_pct": 0.0, "confidence": 0.5}
        )
        ex.close_position.assert_awaited_once()
        assert r._position_side == "Buy"

    @pytest.mark.asyncio
    async def test_force_close_failure_keeps_position_side(self, monkeypatch, tmp_path):
        """Risk-Force-Close: schlägt close_position() fehl, bleibt
        ``_position_side`` unverändert (kein lautloses "flat")."""
        from bybit_edge._legacy_v1.risk import RiskBudget
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ORDER_USD", 100.0)
        r = LiveRunner("BTCUSDT")
        r._journal_path = tmp_path / "journal.csv"
        r._on_ticker(_ticker_msg())
        r._position_side = "Sell"
        ex = AsyncMock()
        ex.round_qty = lambda q: 0.002
        ex.place_market_order = AsyncMock(return_value={"retCode": 0})
        ex.close_position = AsyncMock(
            return_value={"retCode": 10006, "retMsg": "rate limit"}
        )
        r.executor = ex

        rb = RiskBudget(
            daily_loss_pct=-0.50,
            max_dd_pct=-0.15,
            vol_scaling_enabled=False,
            vol_target_bps=50.0,
            state_path=tmp_path / "risk_state.json",
        )
        rb.load(current_equity=1000.0)
        rb.on_equity_update(equity=2000.0)  # peak
        rb.on_equity_update(equity=1600.0)  # -20% vom peak → max_drawdown
        assert rb.should_force_close() is True
        r.risk_budget = rb

        await r._act_on_decision(
            {"action": "long", "direction": 1, "strategy_id": "S3",
             "position_size_pct": 0.1, "confidence": 0.6}
        )
        ex.close_position.assert_awaited_once()
        ex.place_market_order.assert_not_awaited()
        assert r._position_side == "Sell"

    @pytest.mark.asyncio
    async def test_opposite_close_failure_blocks_entry_and_keeps_side(self, monkeypatch):
        """Schlägt das Schließen der Gegenposition fehl, wird KEIN neuer
        Entry gesendet und ``_position_side`` bleibt auf der alten Seite."""
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ORDER_USD", 100.0)
        r = LiveRunner("BTCUSDT")
        r._on_ticker(_ticker_msg())
        r._position_side = "Sell"
        ex = AsyncMock()
        ex.round_qty = lambda q: 0.002
        ex.place_market_order = AsyncMock(return_value={"retCode": 0})
        ex.close_position = AsyncMock(
            return_value={"retCode": 110043, "retMsg": "reduce-only rejected"}
        )
        r.executor = ex
        await r._act_on_decision(
            {"action": "long", "direction": 1, "strategy_id": "S3",
             "position_size_pct": 0.1, "confidence": 0.6}
        )
        ex.close_position.assert_awaited_once()
        ex.place_market_order.assert_not_awaited()
        assert r._position_side == "Sell"


# ──────────────────────────────────────────────────────────────────
# Risk-Loop Robustness — transient timeouts, backoff escalation
# ──────────────────────────────────────────────────────────────────

class TestRiskLoopRobustness:
    """Verifies that transient errors in get_equity() don't spam the logs
    with stacktraces and that the consecutive-error counter escalates
    severity exactly after N failures."""

    def _make_runner_with_mocked_executor(
        self, side_effect=None, return_value=None
    ) -> LiveRunner:
        from bybit_edge._legacy_v1.risk import RiskBudget
        import pathlib
        import tempfile

        r = LiveRunner("BTCUSDT")
        # Risk-Budget muss truthy sein, damit der Tick aktiv arbeitet.
        tmp = pathlib.Path(tempfile.mkdtemp()) / "risk_state.json"
        r.risk_budget = RiskBudget(
            daily_loss_pct=-0.03,
            max_dd_pct=-0.15,
            vol_scaling_enabled=False,
            vol_target_bps=50.0,
            state_path=tmp,
        )
        r.risk_budget.load(current_equity=1000.0)

        ex = AsyncMock()
        if side_effect is not None:
            ex.get_equity = AsyncMock(side_effect=side_effect)
        else:
            ex.get_equity = AsyncMock(return_value=return_value)
        r.executor = ex
        return r

    @pytest.mark.asyncio
    async def test_risk_loop_logs_warning_on_first_timeout(self, caplog):
        r = self._make_runner_with_mocked_executor(
            side_effect=asyncio.TimeoutError()
        )
        caplog.set_level(logging.WARNING, logger="bybit_edge._legacy_v1.live_runner")

        ok = await r._risk_loop_tick()
        # Counter wird vom Loop hochgezählt; der Tick selbst gibt nur False zurück.
        assert ok is False

        warnings = [rec for rec in caplog.records if rec.levelno == logging.WARNING]
        errors = [rec for rec in caplog.records if rec.levelno == logging.ERROR]
        assert len(warnings) == 1
        assert errors == []
        assert "TimeoutError" in warnings[0].getMessage()
        # Kein Stacktrace mitgeloggt.
        assert warnings[0].exc_info is None

    @pytest.mark.asyncio
    async def test_risk_loop_logs_error_after_consecutive_failures(self, caplog):
        r = self._make_runner_with_mocked_executor(
            side_effect=asyncio.TimeoutError()
        )
        caplog.set_level(logging.WARNING, logger="bybit_edge._legacy_v1.live_runner")

        # Simuliere 4 vorausgegangene Fehler — der nächste (5.) Tick muss als
        # ERROR geloggt werden (Eskalations-Schwelle = 5).
        r._risk_consec_errors = 4
        caplog.clear()
        ok = await r._risk_loop_tick()
        assert ok is False

        errors = [rec for rec in caplog.records if rec.levelno == logging.ERROR]
        warnings = [rec for rec in caplog.records if rec.levelno == logging.WARNING]
        assert len(errors) == 1
        assert warnings == []
        assert "aufeinanderfolgenden Fehlern" in errors[0].getMessage()

    @pytest.mark.asyncio
    async def test_risk_loop_resets_counter_on_success(self, caplog):
        """Drei Failures, dann ein Erfolg → Counter ist 0; der nächste
        Fehler wird wieder als WARNING (nicht ERROR) geloggt."""
        call_results = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            1234.5,  # success
            asyncio.TimeoutError(),  # neuer Fehler nach Reset
        ]

        async def fake_get_equity():
            v = call_results.pop(0)
            if isinstance(v, BaseException):
                raise v
            return v

        r = self._make_runner_with_mocked_executor(return_value=0.0)
        r.executor.get_equity = fake_get_equity
        caplog.set_level(logging.WARNING, logger="bybit_edge._legacy_v1.live_runner")

        # Drei Failures: Counter manuell hochzählen wie der Loop es täte.
        for _ in range(3):
            ok = await r._risk_loop_tick()
            assert ok is False
            r._risk_consec_errors += 1
        assert r._risk_consec_errors == 3

        # Erfolg → Loop würde Counter auf 0 setzen.
        ok = await r._risk_loop_tick()
        assert ok is True
        r._risk_consec_errors = 0

        caplog.clear()
        ok = await r._risk_loop_tick()
        assert ok is False
        warnings = [rec for rec in caplog.records if rec.levelno == logging.WARNING]
        errors = [rec for rec in caplog.records if rec.levelno == logging.ERROR]
        # Nach Reset MUSS der erste neue Fehler wieder ein WARNING sein.
        assert len(warnings) == 1
        assert errors == []

    @pytest.mark.asyncio
    async def test_risk_loop_unknown_exception_logs_stacktrace(self, caplog):
        """Echte Bugs (nicht-transiente Exceptions) müssen weiterhin mit
        vollem Stacktrace geloggt werden, nicht als WARNING verschluckt."""
        r = self._make_runner_with_mocked_executor(
            side_effect=ValueError("totally unexpected")
        )
        caplog.set_level(logging.WARNING, logger="bybit_edge._legacy_v1.live_runner")

        ok = await r._risk_loop_tick()
        # Unbekannte Exception → Tick returnt True (kein Backoff-Spin).
        assert ok is True
        errors = [rec for rec in caplog.records if rec.levelno == logging.ERROR]
        assert len(errors) == 1
        assert errors[0].exc_info is not None
        assert "Fehler im Risk-Loop" in errors[0].getMessage()


# ──────────────────────────────────────────────────────────────────
# Snapshot Export Retry — Windows file-lock contention
# ──────────────────────────────────────────────────────────────────

class TestSnapshotExportRetry:
    """Verifies the retry helper for DuckDB COPY-to-Parquet exports.

    Background: Windows refuses to rename a Parquet file while a Dashboard
    reader holds it open. The helper retries a few times with a tiny
    sleep — the reader almost always closes within 50-150 ms.
    """

    def test_export_retries_on_permission_denied(self, caplog):
        r = LiveRunner("BTCUSDT")
        caplog.set_level(logging.WARNING, logger="bybit_edge._legacy_v1.live_runner")

        conn = MagicMock()
        # 1. Aufruf wirft (lock), 2. klappt.
        conn.execute = MagicMock(side_effect=[
            duckdb.IOException("IO Error: Could not move file: Zugriff verweigert"),
            None,
        ])
        ok = r._safe_parquet_export(conn, "row_counts.parquet", "COPY ...")
        assert ok is True
        assert conn.execute.call_count == 2
        # Kein WARNING — Retry war erfolgreich.
        warnings = [rec for rec in caplog.records if rec.levelno == logging.WARNING]
        assert warnings == []

    def test_export_gives_up_after_3_retries(self, caplog):
        r = LiveRunner("BTCUSDT")
        caplog.set_level(logging.WARNING, logger="bybit_edge._legacy_v1.live_runner")

        conn = MagicMock()
        conn.execute = MagicMock(side_effect=duckdb.IOException(
            "IO Error: Could not move file: Zugriff verweigert"
        ))
        ok = r._safe_parquet_export(conn, "row_counts.parquet", "COPY ...")
        assert ok is False
        assert conn.execute.call_count == 3
        warnings = [rec for rec in caplog.records if rec.levelno == logging.WARNING]
        errors = [rec for rec in caplog.records if rec.levelno == logging.ERROR]
        assert len(warnings) == 1
        # Genau 1 WARNING, KEIN Stacktrace, KEIN ERROR.
        assert warnings[0].exc_info is None
        assert "skipped this cycle" in warnings[0].getMessage()
        assert errors == []

    def test_export_does_not_retry_on_other_io_error(self, caplog):
        """Andere IOException-Varianten (z.B. 'disk full') sind echte
        Probleme und werden sofort mit Stacktrace als ERROR geloggt –
        keine Retries."""
        r = LiveRunner("BTCUSDT")
        caplog.set_level(logging.WARNING, logger="bybit_edge._legacy_v1.live_runner")

        conn = MagicMock()
        conn.execute = MagicMock(side_effect=duckdb.IOException(
            "IO Error: disk full"
        ))
        ok = r._safe_parquet_export(conn, "row_counts.parquet", "COPY ...")
        assert ok is False
        # Genau 1 Aufruf — keine Retries für nicht-Lock-Fehler.
        assert conn.execute.call_count == 1
        errors = [rec for rec in caplog.records if rec.levelno == logging.ERROR]
        assert len(errors) == 1
        # ERROR mit Stacktrace (logger.exception).
        assert errors[0].exc_info is not None
        assert "konnte nicht geschrieben werden" in errors[0].getMessage()

    def test_export_permission_denied_english_marker(self, caplog):
        """Auch die englische Fehlervariante 'Permission denied' triggert Retries."""
        r = LiveRunner("BTCUSDT")
        caplog.set_level(logging.WARNING, logger="bybit_edge._legacy_v1.live_runner")

        conn = MagicMock()
        conn.execute = MagicMock(side_effect=[
            duckdb.IOException("IO Error: Permission denied"),
            None,
        ])
        ok = r._safe_parquet_export(conn, "coverage.parquet", "COPY ...")
        assert ok is True
        assert conn.execute.call_count == 2


# ──────────────────────────────────────────────────────────────────
# Collector dispatch — envelope ts propagation
# ──────────────────────────────────────────────────────────────────

class TestCollectorEnvelopeTs:
    def test_dispatch_propagates_envelope_ts(self):
        """_dispatch must copy the Bybit envelope ``ts`` onto the WSMessage."""
        collector = BybitWSCollector(symbol="BTCUSDT")
        captured: list[WSMessage] = []
        collector.add_handler("tickers", lambda m: captured.append(m))

        payload = {
            "topic": "tickers.BTCUSDT",
            "type": "snapshot",
            "ts": 1700000000123,
            "data": {"symbol": "BTCUSDT", "lastPrice": "50000"},
        }
        asyncio.run(collector._dispatch(payload, recv_ts=1.0))

        assert len(captured) == 1
        assert captured[0].envelope_ts == 1700000000123
        # And it survives into the queued message too.
        queued = collector.queues["tickers"].get_nowait()
        assert queued.envelope_ts == 1700000000123

    def test_dispatch_missing_ts_defaults_zero(self):
        """A payload without ``ts`` yields envelope_ts=0 (back-compat)."""
        collector = BybitWSCollector(symbol="BTCUSDT")
        captured: list[WSMessage] = []
        collector.add_handler("tickers", lambda m: captured.append(m))

        payload = {
            "topic": "tickers.BTCUSDT",
            "type": "delta",
            "data": {"symbol": "BTCUSDT", "fundingRate": "0.0001"},
        }
        asyncio.run(collector._dispatch(payload, recv_ts=1.0))

        assert len(captured) == 1
        assert captured[0].envelope_ts == 0
