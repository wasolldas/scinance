"""
Unit tests for :class:`ReplayBacktester`.

All tests are network-free and use an in-memory DuckDB filled with synthetic
ticks via the real ``write_*_batch`` helpers and the real dataclasses
(``TickerSnapshot`` / ``TradeEvent`` / ``LiquidationEvent``).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from bybit_edge.backtester.engine import BacktestResult
from bybit_edge.persistence.db import PersistenceLayer
from bybit_edge.replay_backtester import ReplayBacktester
from bybit_edge.state.liquidation_buffer import LiquidationEvent
from bybit_edge.state.ticker_state import TickerSnapshot
from bybit_edge.state.trade_buffer import TradeEvent

_SYMBOL = "BTCUSDT"
_BASE_TS = 1_700_000_000_000  # arbitrary fixed ms epoch


# ══════════════════════════════════════════════════════════════════════
# Fixtures / helpers
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture()
def persist() -> PersistenceLayer:
    """An in-memory DuckDB persistence layer."""
    layer = PersistenceLayer(db_path=Path(":memory:"))
    yield layer
    layer.close()


def _ticker(
    i: int,
    *,
    last_price: float = 30_000.0,
    mark_price: float | None = None,
    index_price: float = 30_000.0,
    next_funding_time: int = 0,
    funding_rate: float = 0.0001,
    ts: int | None = None,
) -> TickerSnapshot:
    mark = mark_price if mark_price is not None else last_price
    return TickerSnapshot(
        symbol=_SYMBOL,
        last_price=last_price,
        mark_price=mark,
        index_price=index_price,
        funding_rate=funding_rate,
        next_funding_time=next_funding_time,
        open_interest=1_000_000.0,
        open_interest_value=3.0e10,
        bid1_price=last_price - 1.0,
        bid1_size=5.0,
        ask1_price=last_price + 1.0,
        ask1_size=5.0,
        ts=ts if ts is not None else _BASE_TS + i * 1000,
        recv_ts=0.0,
    )


def _trade(i: int, *, price: float = 30_000.0, side: str = "Buy") -> TradeEvent:
    return TradeEvent(
        timestamp_ms=_BASE_TS + i * 1000,
        price=price,
        volume=1.0,
        side=side,
        is_block=False,
    )


def _liq(i: int, *, usd: float = 1.0e6, side: str = "Sell") -> LiquidationEvent:
    price = 30_000.0
    vol = usd / price
    return LiquidationEvent(
        timestamp_ms=_BASE_TS + i * 1000,
        symbol=_SYMBOL,
        side=side,
        volume=vol,
        price=price,
        usd_value=usd,
    )


def _new_bt(persist: PersistenceLayer) -> ReplayBacktester:
    bt = ReplayBacktester(_SYMBOL, db_path=None)
    bt.persist = persist  # reuse the in-memory connection
    return bt


# ══════════════════════════════════════════════════════════════════════
# Tests
# ══════════════════════════════════════════════════════════════════════

def test_load_events_sorts_chronologically(persist: PersistenceLayer) -> None:
    # Insert deliberately out-of-order-ish across tables.
    persist.write_tickers_batch([_ticker(5), _ticker(1), _ticker(3)])
    persist.write_trades_batch([_trade(4), _trade(0)], symbol=_SYMBOL)
    persist.write_liquidations_batch([_liq(2)])

    bt = _new_bt(persist)
    n = bt.load_events()

    assert n == 6
    ts_sequence = [e[0] for e in bt._events]
    assert ts_sequence == sorted(ts_sequence)
    # Strictly non-decreasing -> no lookahead in the merged stream.
    assert all(b >= a for a, b in zip(ts_sequence, ts_sequence[1:]))


def test_load_events_empty_db(persist: PersistenceLayer) -> None:
    bt = _new_bt(persist)
    n = bt.load_events()
    assert n == 0
    # run() on an empty stream must not crash and returns one result per strat.
    results = bt.run()
    assert set(results.keys()) == {"S1", "S2", "S3", "S4", "S5"}
    assert all(r.n_trades == 0 for r in results.values())


def test_no_lookahead(persist: PersistenceLayer) -> None:
    # Trades at i=0..9, a liquidation at i=20.
    trades = [_trade(i, price=30_000.0 + i) for i in range(10)]
    persist.write_trades_batch(trades, symbol=_SYMBOL)
    persist.write_liquidations_batch([_liq(20)])
    persist.write_tickers_batch([_ticker(i) for i in range(0, 30, 5)])

    bt = _new_bt(persist)
    bt.load_events()

    # Reconstruct the causal buffer state at each ticker tick and assert that
    # no event with ts > current ticker ts has been ingested.
    from bybit_edge.state.liquidation_buffer import LiquidationBuffer
    from bybit_edge.state.trade_buffer import TradeBuffer

    tb = TradeBuffer(maxlen=2000)
    lb = LiquidationBuffer(maxlen=2000)
    for ts_ms, kind, payload in bt._events:
        if kind == "trade":
            tb.add(TradeEvent(payload["timestamp_ms"], payload["price"],
                              payload["volume"], payload["side"], payload["is_block"]))
        elif kind == "liq":
            lb.add(LiquidationEvent(payload["timestamp_ms"], payload["symbol"],
                                    payload["side"], payload["volume"],
                                    payload["price"], payload["usd_value"]))
        else:  # ticker — checkpoint
            max_trade_ts = max((t.timestamp_ms for t in tb.recent_events(2000)),
                               default=-1)
            assert max_trade_ts <= ts_ms
            for e in lb.recent_by_ts(1e12, now_ms=ts_ms):
                assert e.timestamp_ms <= ts_ms


def test_seconds_to_settlement_uses_event_time() -> None:
    # next_funding_time is 600 s after the event ts; expect ~600, not a
    # wall-clock-derived value.
    ts = _BASE_TS
    nft = ts + 600_000
    secs = ReplayBacktester._seconds_to_settlement(nft, ts)
    assert secs == pytest.approx(600.0)

    # Invalid/zero -> default.
    assert ReplayBacktester._seconds_to_settlement(0, ts) == pytest.approx(3600.0)
    # Past settlement -> default.
    assert ReplayBacktester._seconds_to_settlement(ts - 1000, ts) == pytest.approx(3600.0)


def test_run_returns_result_per_strategy(persist: PersistenceLayer) -> None:
    persist.write_tickers_batch([_ticker(i) for i in range(50)])
    persist.write_trades_batch([_trade(i) for i in range(50)], symbol=_SYMBOL)

    bt = _new_bt(persist)
    bt.load_events()
    results = bt.run(pipeline_interval_seconds=1.0)

    assert set(results.keys()) == {"S1", "S2", "S3", "S4", "S5"}
    for res in results.values():
        assert isinstance(res, BacktestResult)


def test_run_produces_trades_when_signal(persist: PersistenceLayer) -> None:
    """A strategy that signals enter then exit must yield a round-trip Trade.

    We inject deterministic signals by overriding ``_eval_strategy`` for S1,
    which exercises the full causal run loop + trade bookkeeping honestly
    (real prices from the event stream, real fee/slippage model).
    """
    prices = [30_000.0 + i * 10 for i in range(20)]
    persist.write_tickers_batch(
        [_ticker(i, last_price=prices[i], index_price=prices[i]) for i in range(20)]
    )

    bt = _new_bt(persist)
    bt.load_events()

    state = {"entered": False}

    def fake_eval(strategy_id: str, strategy: Any, ticker_data: dict,
                  ts_seconds: float) -> dict:
        if strategy_id != "S1":
            return {"action": "wait", "direction": 0, "strategy": strategy_id}
        if not state["entered"]:
            state["entered"] = True
            return {"action": "enter", "direction": 1, "strategy": "S1"}
        return {"action": "exit", "direction": 1, "strategy": "S1"}

    bt._eval_strategy = fake_eval  # type: ignore[assignment]
    results = bt.run(pipeline_interval_seconds=1.0)

    assert results["S1"].n_trades >= 1
    trade = results["S1"].trades[0]
    assert trade.side == "Long"
    assert trade.symbol == _SYMBOL
    # Exit happened at a later (higher) ts than entry.
    assert trade.exit_ts > trade.entry_ts


def test_metrics_are_valid(persist: PersistenceLayer) -> None:
    persist.write_tickers_batch(
        [_ticker(i, last_price=30_000.0 + (i % 7) * 25) for i in range(40)]
    )

    bt = _new_bt(persist)
    bt.load_events()

    # Inject an alternating enter/exit pattern for S3 to generate >1 trade.
    toggle = {"open": False}

    def fake_eval(strategy_id: str, strategy: Any, ticker_data: dict,
                  ts_seconds: float) -> dict:
        if strategy_id != "S3":
            return {"action": "wait", "direction": 0, "strategy": strategy_id}
        if not toggle["open"]:
            toggle["open"] = True
            return {"action": "enter", "direction": -1, "strategy": "S3"}
        toggle["open"] = False
        return {"action": "exit", "direction": -1, "strategy": "S3"}

    bt._eval_strategy = fake_eval  # type: ignore[assignment]
    results = bt.run(pipeline_interval_seconds=1.0)

    for res in results.values():
        assert 0.0 <= res.win_rate <= 1.0
        assert isinstance(res.sharpe, float)
        assert isinstance(res.max_drawdown, float)
        assert res.max_drawdown >= 0.0
    assert results["S3"].n_trades >= 1


def test_synthetic_liquidation_cascade(persist: PersistenceLayer) -> None:
    """A dense liquidation cluster must be processed by S1 without errors."""
    # Background ticks + trades, then a burst of liquidations.
    persist.write_tickers_batch([_ticker(i) for i in range(0, 120, 2)])
    persist.write_trades_batch(
        [_trade(i, price=30_000.0 - i * 5, side="Sell") for i in range(60)],
        symbol=_SYMBOL,
    )
    # Cluster of 60 liquidations in a short window (long liquidations: "Sell").
    persist.write_liquidations_batch(
        [_liq(60 + i, usd=2.0e6 + i * 1.0e5, side="Sell") for i in range(60)]
    )

    bt = _new_bt(persist)
    n = bt.load_events()
    assert n > 0

    # Must run end-to-end without raising and return all strategy results.
    results = bt.run(pipeline_interval_seconds=1.0)
    assert set(results.keys()) == {"S1", "S2", "S3", "S4", "S5"}
    # S1 result is a valid (possibly empty) BacktestResult.
    assert isinstance(results["S1"], BacktestResult)
    assert results["S1"].n_trades >= 0


def test_is_data_limited_flags() -> None:
    assert ReplayBacktester.is_data_limited("S2") is True
    assert ReplayBacktester.is_data_limited("S4") is True
    assert ReplayBacktester.is_data_limited("S5") is True
    assert ReplayBacktester.is_data_limited("S1") is False
    assert ReplayBacktester.is_data_limited("S3") is False
