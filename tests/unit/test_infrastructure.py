"""
Infrastructure tests — must pass 100 % before any module builder starts.

Covers: OrderbookState, TickerState, LiquidationBuffer, TradeBuffer,
        WalkForwardSplitter, BacktestEngine, FundingScheduler,
        PersistenceLayer.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

# ── State imports ─────────────────────────────────────────────────────
from bybit_edge._legacy_v1.state.orderbook_state import OrderbookState
from bybit_edge._legacy_v1.state.ticker_state import TickerSnapshot, TickerStateManager
from bybit_edge._legacy_v1.state.liquidation_buffer import LiquidationEvent, LiquidationBuffer
from bybit_edge._legacy_v1.state.trade_buffer import TradeEvent, TradeBuffer

# ── Backtester imports ────────────────────────────────────────────────
from bybit_edge._legacy_v1.backtester.engine import (
    Trade,
    BacktestResult,
    WalkForwardSplitter,
    BacktestEngine,
)

# ── Scheduler imports ─────────────────────────────────────────────────
from bybit_edge._legacy_v1.scheduler import FundingScheduler

# ── Persistence imports ───────────────────────────────────────────────
from bybit_edge.persistence.db import PersistenceLayer


# =====================================================================
# OrderbookState
# =====================================================================

class TestOrderbookState:

    def _make_snapshot_data(self) -> dict:
        return {
            "s": "BTCUSDT",
            "b": [["50000", "1.5"], ["49999", "2.0"], ["49998", "0.5"]],
            "a": [["50001", "1.0"], ["50002", "3.0"], ["50003", "0.8"]],
            "u": 100,
        }

    def test_orderbook_state_apply_snapshot(self) -> None:
        """Snapshot replaces entire book, levels are ordered correctly."""
        ob = OrderbookState("BTCUSDT")
        ob.apply_snapshot(self._make_snapshot_data())

        assert len(ob.bids) == 3
        assert len(ob.asks) == 3
        assert ob.last_update_id == 100

        # Best bid = highest = 50000
        bp, bs = ob.best_bid
        assert bp == 50000.0
        assert bs == 1.5

        # Best ask = lowest = 50001
        ap, as_ = ob.best_ask
        assert ap == 50001.0
        assert as_ == 1.0

    def test_orderbook_state_apply_delta(self) -> None:
        """Delta updates modify/add/remove levels correctly."""
        ob = OrderbookState("BTCUSDT")
        ob.apply_snapshot(self._make_snapshot_data())

        # Update: change bid 50000 size, remove ask 50001, add ask 50000.5
        delta = {
            "b": [["50000", "2.0"]],  # update size
            "a": [["50001", "0"], ["50000.5", "0.3"]],  # delete + add
            "u": 101,
        }
        ob.apply_delta(delta)

        assert ob.last_update_id == 101
        # Bid 50000 updated
        assert ob.bids[50000.0] == 2.0
        # Ask 50001 removed
        assert 50001.0 not in ob.asks
        # Ask 50000.5 added — now the best ask
        ap, _ = ob.best_ask
        assert ap == 50000.5

    def test_orderbook_state_mid_price(self) -> None:
        """Mid price is (best_bid + best_ask) / 2."""
        ob = OrderbookState("BTCUSDT")
        ob.apply_snapshot(self._make_snapshot_data())

        expected_mid = (50000.0 + 50001.0) / 2.0
        assert abs(ob.mid_price - expected_mid) < 1e-10

    def test_orderbook_state_spread(self) -> None:
        """Spread is best_ask - best_bid."""
        ob = OrderbookState("BTCUSDT")
        ob.apply_snapshot(self._make_snapshot_data())
        assert abs(ob.spread - 1.0) < 1e-10

    def test_orderbook_state_imbalance(self) -> None:
        """Imbalance at level 1: (bid_size - ask_size) / (bid_size + ask_size)."""
        ob = OrderbookState("BTCUSDT")
        ob.apply_snapshot(self._make_snapshot_data())

        # Level 1: bid=1.5, ask=1.0 -> (1.5-1.0)/(1.5+1.0) = 0.5/2.5 = 0.2
        imb = ob.imbalance(levels=1)
        assert abs(imb - 0.2) < 1e-10

        # All 3 levels: bid=1.5+2.0+0.5=4.0, ask=1.0+3.0+0.8=4.8
        # (4.0-4.8)/(4.0+4.8) = -0.8/8.8 = -0.0909...
        imb3 = ob.imbalance(levels=3)
        assert abs(imb3 - (-0.8 / 8.8)) < 1e-10

    def test_orderbook_state_empty_book(self) -> None:
        """Edge case: empty book returns safe defaults."""
        ob = OrderbookState("BTCUSDT")
        assert ob.best_bid == (0.0, 0.0)
        assert ob.best_ask == (0.0, 0.0)
        assert ob.mid_price == 0.0
        assert ob.spread == 0.0
        assert ob.imbalance() == 0.0

    def test_orderbook_state_top_n_arrays(self) -> None:
        """top_n_arrays returns numpy arrays of the right shape."""
        ob = OrderbookState("BTCUSDT")
        ob.apply_snapshot(self._make_snapshot_data())

        (bp, bs), (ap, as_) = ob.top_n_arrays(n=2)
        assert len(bp) == 2
        assert len(bs) == 2
        assert len(ap) == 2
        assert len(as_) == 2
        # Bids descending
        assert bp[0] == 50000.0
        assert bp[1] == 49999.0
        # Asks ascending
        assert ap[0] == 50001.0
        assert ap[1] == 50002.0

    def test_orderbook_state_trim(self) -> None:
        """Book is trimmed to max depth levels."""
        ob = OrderbookState("BTCUSDT", depth=2)
        ob.apply_snapshot({
            "b": [["100", "1"], ["99", "1"], ["98", "1"]],
            "a": [["101", "1"], ["102", "1"], ["103", "1"]],
        })
        assert len(ob.bids) == 2
        assert len(ob.asks) == 2
        # Best bid = 100, best ask = 101
        assert ob.best_bid[0] == 100.0
        assert ob.best_ask[0] == 101.0

    def test_orderbook_state_zero_size_in_snapshot(self) -> None:
        """Snapshot ignores entries with size == 0."""
        ob = OrderbookState("BTCUSDT")
        ob.apply_snapshot({
            "b": [["100", "1"], ["99", "0"]],
            "a": [["101", "1"]],
        })
        assert len(ob.bids) == 1
        assert ob.best_bid[0] == 100.0


# =====================================================================
# TickerState
# =====================================================================

class TestTickerState:

    def _make_snap(self, **overrides: object) -> TickerSnapshot:
        defaults = dict(
            symbol="BTCUSDT",
            last_price=50050.0,
            mark_price=50100.0,
            index_price=50000.0,
            funding_rate=0.0001,
            next_funding_time=int((time.time() + 3600) * 1000),
            open_interest=12000.0,
            open_interest_value=600_000_000.0,
            bid1_price=50045.0,
            bid1_size=1.2,
            ask1_price=50055.0,
            ask1_size=0.9,
            ts=int(time.time() * 1000),
            recv_ts=time.time(),
        )
        defaults.update(overrides)
        return TickerSnapshot(**defaults)  # type: ignore[arg-type]

    def test_ticker_state_basis_calculation(self) -> None:
        """basis = (mark_price - index_price) / index_price."""
        snap = self._make_snap(mark_price=50100.0, index_price=50000.0)
        expected = (50100.0 - 50000.0) / 50000.0  # 0.002
        assert abs(snap.basis - expected) < 1e-10

    def test_ticker_state_basis_negative(self) -> None:
        """Negative basis when mark < index."""
        snap = self._make_snap(mark_price=49900.0, index_price=50000.0)
        expected = (49900.0 - 50000.0) / 50000.0  # -0.002
        assert abs(snap.basis - expected) < 1e-10

    def test_ticker_state_basis_zero_index(self) -> None:
        """basis returns 0 when index_price is zero (no division error)."""
        snap = self._make_snap(index_price=0.0)
        assert snap.basis == 0.0

    def test_ticker_state_premium_index(self) -> None:
        """premium_index is the same as basis."""
        snap = self._make_snap(mark_price=50100.0, index_price=50000.0)
        assert snap.premium_index == snap.basis

    def test_ticker_state_seconds_to_funding(self) -> None:
        """seconds_to_funding returns positive value for future settlement."""
        future_ms = int((time.time() + 7200) * 1000)  # 2h from now
        snap = self._make_snap(next_funding_time=future_ms)
        stf = snap.seconds_to_funding
        # Should be approximately 7200 (within 2s tolerance for test execution)
        assert 7198 < stf < 7202

    def test_ticker_state_manager_update_get(self) -> None:
        """TickerStateManager stores and retrieves snapshots by symbol."""
        mgr = TickerStateManager()
        snap_btc = self._make_snap(symbol="BTCUSDT")
        snap_eth = self._make_snap(symbol="ETHUSDT", last_price=3000.0)

        mgr.update(snap_btc)
        mgr.update(snap_eth)

        assert mgr.get("BTCUSDT") is snap_btc
        assert mgr.get("ETHUSDT") is snap_eth
        assert mgr.get("SOLUSDT") is None
        assert set(mgr.symbols()) == {"BTCUSDT", "ETHUSDT"}

    def test_ticker_from_ws(self) -> None:
        """TickerSnapshot.from_ws parses a Bybit WS payload."""
        data = {
            "symbol": "BTCUSDT",
            "lastPrice": "50050",
            "markPrice": "50100",
            "indexPrice": "50000",
            "fundingRate": "0.0001",
            "nextFundingTime": "1700000000000",
            "openInterest": "12000",
            "openInterestValue": "600000000",
            "bid1Price": "50045",
            "bid1Size": "1.2",
            "ask1Price": "50055",
            "ask1Size": "0.9",
            "ts": "1700000000000",
        }
        snap = TickerSnapshot.from_ws(data, recv_ts=1700000000.0)
        assert snap.symbol == "BTCUSDT"
        assert snap.last_price == 50050.0
        assert snap.recv_ts == 1700000000.0

    def test_ticker_from_ws_uses_exchange_ts(self) -> None:
        """An explicit envelope exchange_ts overrides the (absent) data ts."""
        data = {"symbol": "BTCUSDT", "lastPrice": "50000"}  # no "ts" field
        snap = TickerSnapshot.from_ws(data, exchange_ts=1700000000123)
        assert snap.ts == 1700000000123

    def test_ticker_from_ws_falls_back_to_data_ts(self) -> None:
        """Without exchange_ts the legacy data["ts"] meaning is preserved."""
        snap = TickerSnapshot.from_ws({"symbol": "BTCUSDT", "ts": "999"})
        assert snap.ts == 999

    def test_ticker_from_ws_exchange_ts_zero_falls_back(self) -> None:
        """exchange_ts=0 is treated as absent → fall back to data["ts"]."""
        snap = TickerSnapshot.from_ws({"symbol": "BTCUSDT", "ts": "42"}, exchange_ts=0)
        assert snap.ts == 42


# =====================================================================
# LiquidationBuffer
# =====================================================================

class TestLiquidationBuffer:

    def _make_events(self, n: int, base_ts_ms: int) -> list[LiquidationEvent]:
        events = []
        for i in range(n):
            events.append(LiquidationEvent(
                timestamp_ms=base_ts_ms + i * 1000,  # 1s apart
                symbol="BTCUSDT",
                side="Buy" if i % 2 == 0 else "Sell",
                volume=0.1 * (i + 1),
                price=50000.0,
                usd_value=0.1 * (i + 1) * 50000.0,
            ))
        return events

    def test_liquidation_buffer_recent(self) -> None:
        """recent_by_ts returns only events in the time window."""
        buf = LiquidationBuffer()
        now_ms = 1_700_000_000_000
        events = self._make_events(10, now_ms - 9_000)  # 10 events, 1s apart
        for e in events:
            buf.add(e)

        # Last 5 seconds: cutoff = now - 5000ms = ...995000
        # Events at ...995000, ...996000, ...997000, ...998000, ...999000, ...000000
        # = 6 events (>= cutoff)
        recent = buf.recent_by_ts(5.0, now_ms=now_ms)
        assert len(recent) == 6
        # All timestamps >= cutoff
        cutoff_ms = now_ms - 5000
        for e in recent:
            assert e.timestamp_ms >= cutoff_ms

    def test_liquidation_buffer_magnitudes(self) -> None:
        """magnitudes_usd returns log10(usd_value)."""
        buf = LiquidationBuffer()
        now_ms = 1_700_000_000_000
        buf.add(LiquidationEvent(
            timestamp_ms=now_ms,
            symbol="BTCUSDT",
            side="Buy",
            volume=1.0,
            price=100_000.0,
            usd_value=100_000.0,
        ))
        buf.add(LiquidationEvent(
            timestamp_ms=now_ms - 500,
            symbol="BTCUSDT",
            side="Sell",
            volume=0.01,
            price=100_000.0,
            usd_value=1_000.0,
        ))

        mags = buf.magnitudes_usd(5.0, now_ms=now_ms)
        assert len(mags) == 2
        # Deque order: 100k added first, 1k added second
        # log10(100_000) = 5.0, log10(1_000) = 3.0
        assert abs(mags[0] - 5.0) < 1e-10  # 100k was added first
        assert abs(mags[1] - 3.0) < 1e-10  # 1k was added second

    def test_liquidation_buffer_rate_per_second(self) -> None:
        """rate_per_second = count(events) / window_seconds."""
        buf = LiquidationBuffer()
        now_ms = 1_700_000_000_000
        events = self._make_events(20, now_ms - 19_000)
        for e in events:
            buf.add(e)

        rate = buf.rate_per_second(20.0, now_ms=now_ms)
        assert abs(rate - 1.0) < 1e-10  # 20 events in 20s

    def test_liquidation_buffer_empty(self) -> None:
        """Empty buffer returns safe defaults."""
        buf = LiquidationBuffer()
        assert buf.magnitudes_usd(10.0) is not None
        assert len(buf.magnitudes_usd(10.0)) == 0
        assert buf.rate_per_second(10.0) == 0.0

    def test_liquidation_buffer_maxlen(self) -> None:
        """Buffer evicts oldest events when maxlen is exceeded."""
        buf = LiquidationBuffer(maxlen=5)
        for i in range(10):
            buf.add(LiquidationEvent(
                timestamp_ms=1_000_000 + i * 1000,
                symbol="BTCUSDT",
                side="Buy",
                volume=1.0,
                price=50000.0,
                usd_value=50000.0,
            ))
        assert len(buf) == 5


# =====================================================================
# TradeBuffer
# =====================================================================

class TestTradeBuffer:

    def test_trade_buffer_signed_volumes(self) -> None:
        """signed_volume is positive for Buy, negative for Sell."""
        buf = TradeBuffer()
        buf.add(TradeEvent(timestamp_ms=1000, price=50000, volume=1.0, side="Buy", is_block=False))
        buf.add(TradeEvent(timestamp_ms=2000, price=50001, volume=2.0, side="Sell", is_block=False))
        buf.add(TradeEvent(timestamp_ms=3000, price=50002, volume=0.5, side="Buy", is_block=False))

        sv = buf.recent_signed_volumes(n=3)
        np.testing.assert_array_almost_equal(sv, [1.0, -2.0, 0.5])

    def test_trade_buffer_recent_prices(self) -> None:
        """recent_prices returns the correct price array."""
        buf = TradeBuffer()
        for i in range(5):
            buf.add(TradeEvent(
                timestamp_ms=i * 1000,
                price=100.0 + i,
                volume=1.0,
                side="Buy",
                is_block=False,
            ))
        prices = buf.recent_prices(n=3)
        np.testing.assert_array_almost_equal(prices, [102.0, 103.0, 104.0])

    def test_trade_buffer_recent_timestamps(self) -> None:
        """recent_timestamps returns the correct array."""
        buf = TradeBuffer()
        buf.add(TradeEvent(timestamp_ms=100, price=50000, volume=1, side="Buy", is_block=False))
        buf.add(TradeEvent(timestamp_ms=200, price=50000, volume=1, side="Buy", is_block=False))
        ts = buf.recent_timestamps(n=10)
        np.testing.assert_array_equal(ts, [100, 200])

    def test_trade_buffer_empty(self) -> None:
        """Empty buffer returns empty arrays."""
        buf = TradeBuffer()
        assert len(buf.recent_signed_volumes()) == 0
        assert len(buf.recent_prices()) == 0
        assert len(buf.recent_timestamps()) == 0

    def test_trade_event_from_ws(self) -> None:
        """TradeEvent.from_ws correctly parses Bybit payload."""
        data = {"T": 1700000000000, "p": "50000.5", "v": "0.01", "S": "Buy", "BT": False}
        te = TradeEvent.from_ws(data)
        assert te.timestamp_ms == 1700000000000
        assert te.price == 50000.5
        assert te.volume == 0.01
        assert te.side == "Buy"
        assert te.signed_volume == 0.01


# =====================================================================
# WalkForwardSplitter
# =====================================================================

class TestWalkForwardSplitter:

    def _make_data(self, days: int) -> "object":
        """Create a Polars DataFrame with `days` worth of 1-min bars."""
        import polars as pl
        n = days * 24 * 60  # 1-min bars
        start_ms = 1_700_000_000_000
        ts = [start_ms + i * 60_000 for i in range(n)]
        close = [50000.0 + np.sin(i / 100.0) * 100 for i in range(n)]
        return pl.DataFrame({"ts": ts, "close": close})

    def test_walk_forward_splitter_no_lookahead(self) -> None:
        """test_start is always strictly after train_end + embargo."""
        import polars as pl
        data = self._make_data(90)
        splitter = WalkForwardSplitter(data, train_days=30, test_days=7, embargo_minutes=30)

        embargo_ms = 30 * 60 * 1000
        for train_df, test_df in splitter.splits():
            train_max_ts = int(train_df["ts"].max())  # type: ignore[arg-type]
            test_min_ts = int(test_df["ts"].min())  # type: ignore[arg-type]
            # Strict: test_start >= train_end + embargo
            assert test_min_ts >= train_max_ts + embargo_ms, (
                f"Lookahead! test_min={test_min_ts}, "
                f"train_max+embargo={train_max_ts + embargo_ms}"
            )

    def test_walk_forward_splitter_embargo(self) -> None:
        """The gap between train_end and test_start is at least embargo_minutes."""
        import polars as pl
        data = self._make_data(90)
        splitter = WalkForwardSplitter(data, train_days=30, test_days=7, embargo_minutes=30)

        embargo_ms = 30 * 60 * 1000
        count = 0
        for train_df, test_df in splitter.splits():
            train_max_ts = int(train_df["ts"].max())  # type: ignore[arg-type]
            test_min_ts = int(test_df["ts"].min())  # type: ignore[arg-type]
            gap_ms = test_min_ts - train_max_ts
            assert gap_ms >= embargo_ms
            count += 1

        # Should produce at least 1 split for 90 days of data
        assert count >= 1

    def test_walk_forward_splitter_multiple_folds(self) -> None:
        """With enough data, multiple folds are generated."""
        import polars as pl
        data = self._make_data(120)  # ~120 days
        splitter = WalkForwardSplitter(data, train_days=30, test_days=7, embargo_minutes=30)

        folds = list(splitter.splits())
        # 120 days: should have multiple 7-day test windows
        assert len(folds) >= 3


# =====================================================================
# BacktestEngine
# =====================================================================

class TestBacktestEngine:

    def test_backtest_engine_compute_metrics(self) -> None:
        """compute_metrics produces correct Sharpe, win_rate, drawdown."""
        engine = BacktestEngine()

        trades = [
            Trade("BTC", 1000, 2000, "Long", 50000, 50200, 1.0, "taker", pnl=200.0),
            Trade("BTC", 3000, 4000, "Short", 50200, 50000, 1.0, "taker", pnl=200.0),
            Trade("BTC", 5000, 6000, "Long", 50000, 49800, 1.0, "taker", pnl=-200.0),
            Trade("BTC", 7000, 8000, "Long", 49800, 50100, 1.0, "taker", pnl=300.0),
        ]

        result = engine.compute_metrics(trades)
        assert result.n_trades == 4
        assert result.win_rate == 0.75  # 3 wins out of 4
        assert abs(result.total_return - 500.0) < 1e-10
        assert result.max_drawdown >= 0
        # Equity curve length = n_trades + 1
        assert len(result.equity_curve) == 5

    def test_backtest_engine_empty_trades(self) -> None:
        """Empty trade list produces zeroed metrics."""
        engine = BacktestEngine()
        result = engine.compute_metrics([])
        assert result.n_trades == 0
        assert result.sharpe == 0.0
        assert result.win_rate == 0.0
        assert result.total_return == 0.0

    def test_backtest_engine_fee_model(self) -> None:
        """Fees are applied correctly."""
        engine = BacktestEngine(fee_taker=0.00055, fee_maker=0.0002)
        # Taker fee on 1 BTC at 50000: 50000 * 1 * 0.00055 = 27.5
        fee = engine._apply_fee(50000.0, 1.0, "taker")
        assert abs(fee - 27.5) < 1e-10

        fee_maker = engine._apply_fee(50000.0, 1.0, "maker")
        assert abs(fee_maker - 10.0) < 1e-10

    def test_backtest_engine_slippage_model(self) -> None:
        """Slippage adjusts price adversely."""
        engine = BacktestEngine(slippage_bps=2.0)
        # Long entry: price * (1 + 2/10000) = 50000 * 1.0002 = 50010
        slipped_long = engine._slipped_price(50000.0, "Long")
        assert abs(slipped_long - 50010.0) < 1e-6

        # Short entry: price * (1 - 2/10000) = 50000 * 0.9998 = 49990
        slipped_short = engine._slipped_price(50000.0, "Short")
        assert abs(slipped_short - 49990.0) < 1e-6

    def test_backtest_engine_run_walkforward(self) -> None:
        """Full walk-forward run with a trivial strategy."""
        import polars as pl

        # Create 90 days of data with an uptrend
        n = 90 * 24 * 60
        start_ms = 1_700_000_000_000
        ts = [start_ms + i * 60_000 for i in range(n)]
        close = [50000.0 + i * 0.01 for i in range(n)]
        data = pl.DataFrame({"ts": ts, "close": close})

        def strategy_fn(train_df: pl.DataFrame):
            """Trivial always-long strategy."""
            state = {"position": False}

            def signal_fn(row: dict) -> dict | None:
                if not state["position"]:
                    state["position"] = True
                    return {"side": "Long", "qty": 0.01}
                else:
                    state["position"] = False
                    return {"action": "close"}
            return signal_fn

        engine = BacktestEngine(slippage_bps=0.0, fee_taker=0.0, fee_maker=0.0)
        result = engine.run_walkforward(strategy_fn, data)
        assert result.n_trades > 0
        # With an uptrend and zero costs, total return should be positive
        assert result.total_return > 0


# =====================================================================
# FundingScheduler
# =====================================================================

class TestFundingScheduler:

    def test_funding_scheduler_seconds_to_next(self) -> None:
        """seconds_to_next_settlement is always positive and < 8 h."""
        sched = FundingScheduler(settlement_hours=(0, 8, 16))

        # Test at various times of day
        test_times = [
            datetime(2025, 6, 1, 0, 0, 1, tzinfo=timezone.utc),   # just after 00:00
            datetime(2025, 6, 1, 7, 59, 59, tzinfo=timezone.utc),  # just before 08:00
            datetime(2025, 6, 1, 8, 0, 1, tzinfo=timezone.utc),   # just after 08:00
            datetime(2025, 6, 1, 15, 30, 0, tzinfo=timezone.utc), # mid-afternoon
            datetime(2025, 6, 1, 23, 59, 59, tzinfo=timezone.utc), # end of day
        ]

        for t in test_times:
            secs = sched.seconds_to_next_settlement(now_utc=t)
            assert secs > 0, f"Must be positive at {t}, got {secs}"
            assert secs <= 8 * 3600, f"Must be <= 8h at {t}, got {secs}"

    def test_funding_scheduler_exact_boundary(self) -> None:
        """At exactly a settlement hour, next settlement is the following slot."""
        sched = FundingScheduler(settlement_hours=(0, 8, 16))
        t = datetime(2025, 6, 1, 8, 0, 0, tzinfo=timezone.utc)
        secs = sched.seconds_to_next_settlement(now_utc=t)
        # Next should be 16:00 = 8h away
        assert abs(secs - 8 * 3600) < 1

    def test_funding_scheduler_wrap_midnight(self) -> None:
        """After 16:00, next settlement wraps to 00:00 next day."""
        sched = FundingScheduler(settlement_hours=(0, 8, 16))
        t = datetime(2025, 6, 1, 20, 0, 0, tzinfo=timezone.utc)
        secs = sched.seconds_to_next_settlement(now_utc=t)
        # Expected: 4 hours = 14400 s
        assert abs(secs - 4 * 3600) < 1

    def test_funding_scheduler_register_callback(self) -> None:
        """register_callback adds to the internal list."""
        sched = FundingScheduler()
        assert len(sched._callbacks) == 0
        sched.register_callback(lambda: None)
        assert len(sched._callbacks) == 1
        sched.register_callback(lambda: None)
        assert len(sched._callbacks) == 2


# =====================================================================
# PersistenceLayer (in-memory DuckDB)
# =====================================================================

class TestPersistence:

    def test_persistence_write_read_ticker(self) -> None:
        """Write a TickerSnapshot, read it back."""
        db = PersistenceLayer(db_path=Path(":memory:"))
        try:
            snap = TickerSnapshot(
                symbol="BTCUSDT",
                last_price=50050.0,
                mark_price=50100.0,
                index_price=50000.0,
                funding_rate=0.0001,
                next_funding_time=1_700_000_000_000,
                open_interest=12000.0,
                open_interest_value=600_000_000.0,
                bid1_price=50045.0,
                bid1_size=1.2,
                ask1_price=50055.0,
                ask1_size=0.9,
                ts=1_700_000_000_000,
                recv_ts=1_700_000_000.0,
            )
            db.write_ticker(snap)

            rows = db.query_tickers("BTCUSDT", 0, 2_000_000_000_000)
            assert len(rows) == 1
            row = rows[0]
            assert row[0] == 1_700_000_000_000  # ts
            assert row[1] == "BTCUSDT"          # symbol
            assert row[2] == 50050.0             # last_price
            assert row[3] == 50100.0             # mark_price
        finally:
            db.close()

    def test_persistence_write_read_trade(self) -> None:
        """Write a TradeEvent, read it back."""
        db = PersistenceLayer(db_path=Path(":memory:"))
        try:
            # TradeEvent doesn't have symbol attr by default, we need to handle that
            evt = TradeEvent(
                timestamp_ms=1_700_000_000_000,
                price=50000.0,
                volume=0.5,
                side="Buy",
                is_block=False,
            )
            db.write_trade(evt)

            rows = db.conn.execute(
                "SELECT * FROM trades WHERE ts = ?", [1_700_000_000_000]
            ).fetchall()
            assert len(rows) == 1
            assert rows[0][2] == 50000.0  # price
            assert rows[0][3] == 0.5      # volume
            assert rows[0][4] == "Buy"    # side
        finally:
            db.close()

    def test_persistence_write_read_liquidation(self) -> None:
        """Write a LiquidationEvent, read it back."""
        db = PersistenceLayer(db_path=Path(":memory:"))
        try:
            evt = LiquidationEvent(
                timestamp_ms=1_700_000_000_000,
                symbol="BTCUSDT",
                side="Buy",
                volume=1.0,
                price=50000.0,
                usd_value=50000.0,
            )
            db.write_liquidation(evt)

            rows = db.conn.execute(
                "SELECT * FROM liquidations WHERE symbol = ?", ["BTCUSDT"]
            ).fetchall()
            assert len(rows) == 1
            assert rows[0][4] == 50000.0  # price
            assert rows[0][5] == 50000.0  # usd_value
        finally:
            db.close()

    def test_persistence_write_read_kline(self) -> None:
        """Write a kline, query it back via query_kline."""
        db = PersistenceLayer(db_path=Path(":memory:"))
        try:
            db.write_kline(
                ts=1_700_000_000_000,
                symbol="BTCUSDT",
                open_=50000.0,
                high=50100.0,
                low=49900.0,
                close=50050.0,
                volume=123.4,
                turnover=6_170_000.0,
            )
            df = db.query_kline("BTCUSDT", 0, 2_000_000_000_000)
            assert len(df) == 1
            assert df["close"][0] == 50050.0
        finally:
            db.close()

    def test_persistence_schema_idempotent(self) -> None:
        """Calling _init_schema twice does not raise."""
        db = PersistenceLayer(db_path=Path(":memory:"))
        try:
            db._init_schema()  # should not raise
        finally:
            db.close()

    def test_read_only_connect_skips_schema_init(self, tmp_path: Path) -> None:
        """A pre-populated DB can be opened ``read_only=True`` without crash.

        Replay-backtester scenario: a writer has already created the schema
        and inserted rows. A second connection with ``read_only=True`` must
        attach, see the existing data, and NOT attempt to (re-)create the
        schema (DuckDB rejects DDL on a read-only handle).
        """
        db_file = tmp_path / "ro.duckdb"

        # ── 1) writer creates schema + inserts a ticker ──
        writer = PersistenceLayer(db_path=db_file)
        try:
            snap = TickerSnapshot(
                symbol="BTCUSDT",
                last_price=12345.0,
                mark_price=12346.0,
                index_price=12345.5,
                funding_rate=0.0,
                next_funding_time=0,
                open_interest=0.0,
                open_interest_value=0.0,
                bid1_price=12344.0,
                bid1_size=1.0,
                ask1_price=12346.0,
                ask1_size=1.0,
                ts=1_700_000_000_000,
                recv_ts=0.0,
            )
            writer.write_ticker(snap)
        finally:
            writer.close()

        # ── 2) reader opens the same file read-only ──
        reader = PersistenceLayer(db_path=db_file, read_only=True)
        try:
            rows = reader.query_tickers("BTCUSDT", 0, 2_000_000_000_000)
            assert len(rows) == 1
            assert rows[0][1] == "BTCUSDT"
            assert rows[0][2] == 12345.0
        finally:
            reader.close()

    def test_read_only_cannot_write(self, tmp_path: Path) -> None:
        """A read-only ``PersistenceLayer`` must refuse INSERTs.

        DuckDB itself blocks DDL/DML on a read-only handle — the test only
        asserts that the resulting exception bubbles up so that callers
        cannot silently corrupt the writer's view.
        """
        db_file = tmp_path / "ro_write.duckdb"

        # First open writable to create the schema.
        writer = PersistenceLayer(db_path=db_file)
        try:
            writer._init_schema()
        finally:
            writer.close()

        reader = PersistenceLayer(db_path=db_file, read_only=True)
        try:
            snap = TickerSnapshot(
                symbol="BTCUSDT",
                last_price=1.0,
                mark_price=1.0,
                index_price=1.0,
                funding_rate=0.0,
                next_funding_time=0,
                open_interest=0.0,
                open_interest_value=0.0,
                bid1_price=0.9,
                bid1_size=1.0,
                ask1_price=1.1,
                ask1_size=1.0,
                ts=1_700_000_000_001,
                recv_ts=0.0,
            )
            with pytest.raises(Exception):  # noqa: PT011 — DuckDB-Exception
                reader.write_ticker(snap)
        finally:
            reader.close()


# =====================================================================
# PersistenceLayer — L2 orderbook snapshots
# =====================================================================

class TestPersistenceOrderbook:
    """Round-trip tests for the L2 ``orderbook_snapshots`` table."""

    def test_write_and_read_orderbook_snapshot(self) -> None:
        """Single snapshot round-trip preserves prices and sizes exactly."""
        db = PersistenceLayer(db_path=Path(":memory:"))
        try:
            ts = 1_700_000_000_000
            bid_prices = np.array([50000.0, 49999.5, 49999.0], dtype=np.float64)
            bid_sizes = np.array([1.2, 0.8, 2.5], dtype=np.float64)
            ask_prices = np.array([50001.0, 50001.5, 50002.0], dtype=np.float64)
            ask_sizes = np.array([0.9, 1.7, 3.3], dtype=np.float64)
            n_rows = db.write_orderbook_snapshot(
                ts=ts,
                symbol="BTCUSDT",
                bid_prices=bid_prices,
                bid_sizes=bid_sizes,
                ask_prices=ask_prices,
                ask_sizes=ask_sizes,
                recv_ts=1_700_000_000.123,
                depth=20,
            )
            assert n_rows == 6  # 3 bids + 3 asks

            out = db.query_orderbook_snapshots(
                "BTCUSDT", ts - 1, ts + 1, depth=20
            )
            assert len(out) == 1
            rec = out[0]
            assert rec["ts"] == ts
            np.testing.assert_array_almost_equal(rec["bid_prices"], bid_prices)
            np.testing.assert_array_almost_equal(rec["bid_sizes"], bid_sizes)
            np.testing.assert_array_almost_equal(rec["ask_prices"], ask_prices)
            np.testing.assert_array_almost_equal(rec["ask_sizes"], ask_sizes)
            assert abs(rec["recv_ts"] - 1_700_000_000.123) < 1e-6
        finally:
            db.close()

    def test_orderbook_snapshots_chronological(self) -> None:
        """Three snapshots with different ts are returned sorted ascending."""
        db = PersistenceLayer(db_path=Path(":memory:"))
        try:
            bids_p = np.array([100.0], dtype=np.float64)
            bids_s = np.array([1.0], dtype=np.float64)
            asks_p = np.array([101.0], dtype=np.float64)
            asks_s = np.array([1.0], dtype=np.float64)
            # Insert deliberately out of order.
            for ts in (3000, 1000, 2000):
                db.write_orderbook_snapshot(
                    ts=ts,
                    symbol="BTCUSDT",
                    bid_prices=bids_p,
                    bid_sizes=bids_s,
                    ask_prices=asks_p,
                    ask_sizes=asks_s,
                    recv_ts=ts / 1000.0,
                )

            out = db.query_orderbook_snapshots("BTCUSDT", 0, 10_000, depth=20)
            assert [r["ts"] for r in out] == [1000, 2000, 3000]
        finally:
            db.close()

    def test_orderbook_batch_writer(self) -> None:
        """Batch write of 5 dicts produces 5 recoverable snapshots."""
        db = PersistenceLayer(db_path=Path(":memory:"))
        try:
            snaps = []
            for i in range(5):
                snaps.append({
                    "ts": 1_000 + i,
                    "symbol": "BTCUSDT",
                    "bid_prices": np.array([100.0 - i * 0.1], dtype=np.float64),
                    "bid_sizes": np.array([1.0 + i], dtype=np.float64),
                    "ask_prices": np.array([101.0 + i * 0.1], dtype=np.float64),
                    "ask_sizes": np.array([1.0 + i], dtype=np.float64),
                    "recv_ts": float(i),
                    "depth": 20,
                })
            n_rows = db.write_orderbook_snapshots_batch(snaps)
            assert n_rows == 5 * 2  # 1 bid + 1 ask per snapshot

            out = db.query_orderbook_snapshots("BTCUSDT", 0, 10_000, depth=20)
            assert len(out) == 5
            for i, rec in enumerate(out):
                assert rec["ts"] == 1_000 + i
                assert rec["bid_sizes"][0] == pytest.approx(1.0 + i)
                assert rec["ask_sizes"][0] == pytest.approx(1.0 + i)
        finally:
            db.close()

    def test_row_counts_includes_orderbook(self) -> None:
        """row_counts surfaces the new orderbook_snapshots table."""
        db = PersistenceLayer(db_path=Path(":memory:"))
        try:
            counts0 = db.row_counts()
            assert "orderbook_snapshots" in counts0
            assert counts0["orderbook_snapshots"] == 0

            db.write_orderbook_snapshot(
                ts=1234,
                symbol="BTCUSDT",
                bid_prices=np.array([100.0, 99.0], dtype=np.float64),
                bid_sizes=np.array([1.0, 2.0], dtype=np.float64),
                ask_prices=np.array([101.0, 102.0], dtype=np.float64),
                ask_sizes=np.array([1.0, 2.0], dtype=np.float64),
                recv_ts=1.234,
            )
            counts1 = db.row_counts()
            assert counts1["orderbook_snapshots"] == 4  # 2 bids + 2 asks
        finally:
            db.close()
