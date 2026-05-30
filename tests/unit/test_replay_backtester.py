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


def test_replay_uses_persisted_orderbook(persist: PersistenceLayer) -> None:
    """When L2 snapshots are persisted, ``_build_ticker_data`` must surface
    those depth arrays (not the 1-element bid1/ask1 fallback) and M6 must
    score the resulting profile to the value expected for the snapshot.

    Construction:
        * Uniform top-5 size profile on each side → Shannon entropy ≈ log2(5).
        * The replay loop sees the OB snapshot first (ts=T0), then a later
          ticker at ts=T1 with no fresh OB → the cached snapshot is reused.
    """
    from bybit_edge.layers.l3_regime.m6_entropy import M6ShannonEntropy

    n_levels = 5
    base_bid_price = 29_999.0
    base_ask_price = 30_001.0
    uniform_size = 1.0

    bid_prices = np.array(
        [base_bid_price - i for i in range(n_levels)], dtype=np.float64
    )
    bid_sizes = np.full(n_levels, uniform_size, dtype=np.float64)
    ask_prices = np.array(
        [base_ask_price + i for i in range(n_levels)], dtype=np.float64
    )
    ask_sizes = np.full(n_levels, uniform_size, dtype=np.float64)

    # Persist a single ticker @ts=BASE+5000 and an OB snapshot @ts=BASE+3000
    # (strictly before the ticker; OB is consumed first because it has higher
    # kind_order rank on equal ts and earlier-than-ticker on lesser ts).
    persist.write_tickers_batch([_ticker(5, last_price=30_000.0)])
    persist.write_orderbook_snapshots_batch([{
        "ts": _BASE_TS + 3000,
        "symbol": _SYMBOL,
        "bid_prices": bid_prices,
        "bid_sizes": bid_sizes,
        "ask_prices": ask_prices,
        "ask_sizes": ask_sizes,
        "recv_ts": (_BASE_TS + 3000) / 1000.0,
        "depth": 20,
    }])

    bt = _new_bt(persist)
    n = bt.load_events()
    assert n == 2  # 1 ticker + 1 ob snapshot

    # Intercept the ticker_data that is handed to the strategies.
    captured: dict[str, Any] = {}

    def fake_eval(strategy_id: str, strategy: Any, ticker_data: dict,
                  ts_seconds: float) -> dict:
        captured.setdefault("ticker_data", ticker_data)
        return {"action": "wait", "direction": 0, "strategy": strategy_id}

    bt._eval_strategy = fake_eval  # type: ignore[assignment]
    bt.run(pipeline_interval_seconds=1.0)

    td = captured["ticker_data"]
    # 1. Data origin: arrays come from the persisted OB snapshot, not the
    #    1-element bid1/ask1 fallback.
    assert td["bid_sizes"].size == n_levels
    assert td["ask_sizes"].size == n_levels
    np.testing.assert_array_almost_equal(td["bid_sizes"], bid_sizes)
    np.testing.assert_array_almost_equal(td["ask_sizes"], ask_sizes)
    # best_bid/best_ask also come from the OB top level.
    assert td["best_bid"][0] == pytest.approx(base_bid_price)
    assert td["best_ask"][0] == pytest.approx(base_ask_price)

    # 2. M6 Shannon entropy on a uniform 5-level distribution = log2(5).
    m6 = M6ShannonEntropy()
    res = m6.compute(td["bid_sizes"], td["ask_sizes"])
    expected_h = float(np.log2(n_levels))
    assert res["h_bid"] == pytest.approx(expected_h, abs=1e-9)
    assert res["h_ask"] == pytest.approx(expected_h, abs=1e-9)


def test_has_orderbook_and_runtime_data_limited(
    persist: PersistenceLayer,
) -> None:
    """``has_orderbook`` flips True once L2 snapshots are loaded and S2 is
    no longer reported as data-limited via ``is_data_limited_runtime``."""
    # Before any load → flags default to False / S2 still limited.
    bt = _new_bt(persist)
    assert bt.has_orderbook is False
    assert bt.is_data_limited_runtime("S2") is True

    bid_prices = np.array([29_999.0, 29_998.0], dtype=np.float64)
    bid_sizes = np.array([1.0, 2.0], dtype=np.float64)
    ask_prices = np.array([30_001.0, 30_002.0], dtype=np.float64)
    ask_sizes = np.array([1.0, 2.0], dtype=np.float64)
    persist.write_tickers_batch([_ticker(0)])
    persist.write_orderbook_snapshots_batch([{
        "ts": _BASE_TS,
        "symbol": _SYMBOL,
        "bid_prices": bid_prices,
        "bid_sizes": bid_sizes,
        "ask_prices": ask_prices,
        "ask_sizes": ask_sizes,
        "recv_ts": _BASE_TS / 1000.0,
        "depth": 20,
    }])
    bt.load_events()
    assert bt.has_orderbook is True
    # Per-instance flag flips; static class flag is unchanged (conservative).
    assert bt.is_data_limited_runtime("S2") is False
    assert ReplayBacktester.is_data_limited("S2") is True
    # S4/S5 stay limited even with L2 data.
    assert bt.is_data_limited_runtime("S4") is True
    assert bt.is_data_limited_runtime("S5") is True


def test_load_events_is_idempotent_for_ob_flag(
    persist: PersistenceLayer,
) -> None:
    """Re-loading after the OB rows have been deleted resets the flag."""
    persist.write_tickers_batch([_ticker(0)])
    persist.write_orderbook_snapshots_batch([{
        "ts": _BASE_TS,
        "symbol": _SYMBOL,
        "bid_prices": np.array([100.0], dtype=np.float64),
        "bid_sizes": np.array([1.0], dtype=np.float64),
        "ask_prices": np.array([101.0], dtype=np.float64),
        "ask_sizes": np.array([1.0], dtype=np.float64),
        "recv_ts": _BASE_TS / 1000.0,
        "depth": 20,
    }])
    bt = _new_bt(persist)
    bt.load_events()
    assert bt.has_orderbook is True

    # Wipe OB rows and reload — flag must reset.
    persist.conn.execute("DELETE FROM orderbook_snapshots")
    bt.load_events()
    assert bt.has_orderbook is False
    assert bt.is_data_limited_runtime("S2") is True


def test_replay_falls_back_to_l1_without_orderbook(
    persist: PersistenceLayer,
) -> None:
    """Without any persisted L2 snapshots, the depth arrays in
    ``_build_ticker_data`` are the 1-element bid1/ask1 fallback (legacy
    behaviour unchanged)."""
    persist.write_tickers_batch([_ticker(0, last_price=30_000.0)])

    bt = _new_bt(persist)
    bt.load_events()

    captured: dict[str, Any] = {}

    def fake_eval(strategy_id: str, strategy: Any, ticker_data: dict,
                  ts_seconds: float) -> dict:
        captured.setdefault("ticker_data", ticker_data)
        return {"action": "wait", "direction": 0, "strategy": strategy_id}

    bt._eval_strategy = fake_eval  # type: ignore[assignment]
    bt.run(pipeline_interval_seconds=1.0)

    td = captured["ticker_data"]
    assert td["bid_sizes"].size == 1
    assert td["ask_sizes"].size == 1
    # bid1_size from the _ticker fixture is 5.0.
    assert td["bid_sizes"][0] == pytest.approx(5.0)
    assert td["ask_sizes"][0] == pytest.approx(5.0)
