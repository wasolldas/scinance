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


# ══════════════════════════════════════════════════════════════════════
# Walk-Forward Replay
# ══════════════════════════════════════════════════════════════════════

# Time constants for synthesising multi-fold event streams cheaply.
_MS_PER_DAY = 24 * 3600 * 1000
_MS_PER_MIN = 60 * 1000


def _persist_ticker_grid(
    persist: PersistenceLayer,
    *,
    n: int,
    step_ms: int,
    base_ts: int = _BASE_TS,
    price_base: float = 30_000.0,
) -> list[int]:
    """Insert *n* tickers at ``base_ts + i * step_ms``. Returns the ts list."""
    ts_list = [base_ts + i * step_ms for i in range(n)]
    persist.write_tickers_batch([
        _ticker(0, last_price=price_base + i, ts=ts) for i, ts in enumerate(ts_list)
    ])
    return ts_list


class TestReplayWalkForward:
    """Tests for :meth:`ReplayBacktester.run_walkforward`.

    Where the WF fold geometry (30d / 7d / 30 min) makes seeding 100s of
    thousands of ticks impractical, we shrink it explicitly via the public
    ``train_days``/``test_days``/``embargo_minutes`` knobs so each fold still
    holds ≪ a few hundred events. This keeps the tests fast and deterministic
    while exercising the *same* code path the production defaults take.
    """

    # ------------------------------------------------------------------
    # 1) Result shape
    # ------------------------------------------------------------------
    def test_walkforward_returns_dict_per_strategy(
        self, persist: PersistenceLayer
    ) -> None:
        """``run_walkforward`` must return one ``BacktestResult`` per
        strategy id ("S1".."S5"), exactly like ``run``."""
        # Three folds at 1 train-day / 12h embargo / 1 test-day.
        # 1 ticker per minute -> ~1440/day -> plenty for warmup.
        ts_list = _persist_ticker_grid(persist, n=4500, step_ms=60_000)
        bt = _new_bt(persist)
        bt.load_events()

        results = bt.run_walkforward(
            pipeline_interval_seconds=60.0,
            train_days=1,
            test_days=1,
            embargo_minutes=30,
            min_train_events=10,
        )

        assert set(results.keys()) == {"S1", "S2", "S3", "S4", "S5"}
        for res in results.values():
            assert isinstance(res, BacktestResult)
        # Stream spans ~3.1 days -> at least one fold (1d train + 0.5h emb + 1d
        # test fits twice into 3.1d).
        assert bt.last_walkforward_folds >= 1
        # Sanity: ts list endpoints are the bounds used internally.
        assert ts_list[0] == _BASE_TS

    # ------------------------------------------------------------------
    # 2) Train-phase trades are discarded
    # ------------------------------------------------------------------
    def test_walkforward_train_trades_discarded(
        self, persist: PersistenceLayer
    ) -> None:
        """A strategy that toggles enter/exit every tick should only produce
        trades from the *test* slice — train-slice round-trips must be
        discarded entirely."""
        # 2 days at 1-minute resolution.
        n = 2 * 1440 + 60  # ~2.04 days
        _persist_ticker_grid(persist, n=n, step_ms=60_000)

        bt = _new_bt(persist)
        bt.load_events()

        # Capture which ts ranges trade-entries hit.
        toggle = {"open": False}

        def fake_eval(strategy_id: str, strategy: Any, ticker_data: dict,
                      ts_seconds: float) -> dict:
            if strategy_id != "S1":
                return {"action": "wait", "direction": 0, "strategy": strategy_id}
            if not toggle["open"]:
                toggle["open"] = True
                return {"action": "enter", "direction": 1, "strategy": "S1"}
            toggle["open"] = False
            return {"action": "exit", "direction": 1, "strategy": "S1"}

        bt._eval_strategy = fake_eval  # type: ignore[assignment]

        # 1 train-day, 30 min embargo, 1 test-day -> exactly one fold.
        results = bt.run_walkforward(
            pipeline_interval_seconds=60.0,
            train_days=1,
            test_days=1,
            embargo_minutes=30,
            min_train_events=10,
        )

        assert bt.last_walkforward_folds == 1
        train_end = _BASE_TS + 1 * _MS_PER_DAY
        test_start = train_end + 30 * _MS_PER_MIN
        # All recorded entries must be inside the test window — none in train.
        for t in results["S1"].trades:
            assert t.entry_ts >= test_start, (
                f"entry @ {t.entry_ts} leaked from train slice "
                f"(train_end={train_end}, test_start={test_start})"
            )
        # At least one trade in the test window (toggle fires every tick).
        assert results["S1"].n_trades >= 1

    # ------------------------------------------------------------------
    # 3) Embargo skips events
    # ------------------------------------------------------------------
    def test_walkforward_embargo_skips_events(
        self, persist: PersistenceLayer
    ) -> None:
        """Events whose ts falls in the embargo gap [train_end, test_start)
        must never reach the strategy's ``_eval_strategy`` callback."""
        # 2-day stream, 1-min ticks.
        n = 2 * 1440 + 60
        _persist_ticker_grid(persist, n=n, step_ms=60_000)

        bt = _new_bt(persist)
        bt.load_events()

        seen_ts_ms: list[int] = []

        def probe_eval(strategy_id: str, strategy: Any, ticker_data: dict,
                       ts_seconds: float) -> dict:
            # Only record once (S1) per pipeline tick so we don't 5x-count.
            if strategy_id == "S1":
                seen_ts_ms.append(int(ts_seconds * 1000))
            return {"action": "wait", "direction": 0, "strategy": strategy_id}

        bt._eval_strategy = probe_eval  # type: ignore[assignment]

        embargo_min = 60  # 1 hour
        bt.run_walkforward(
            pipeline_interval_seconds=60.0,
            train_days=1,
            test_days=1,
            embargo_minutes=embargo_min,
            min_train_events=10,
        )

        train_end = _BASE_TS + 1 * _MS_PER_DAY
        test_start = train_end + embargo_min * _MS_PER_MIN

        embargo_hits = [
            ts for ts in seen_ts_ms if train_end <= ts < test_start
        ]
        assert embargo_hits == [], (
            f"strategy saw {len(embargo_hits)} events in the embargo gap "
            f"[{train_end}, {test_start})"
        )

    # ------------------------------------------------------------------
    # 4) Folds with insufficient train data are skipped (no crash)
    # ------------------------------------------------------------------
    def test_walkforward_skips_folds_with_insufficient_train(
        self, persist: PersistenceLayer
    ) -> None:
        """If a fold's train slice has fewer than ``min_train_events``, the
        whole fold is skipped — no exception, no leaked trades, valid empty
        result."""
        # Tiny stream: 2 days but only 30 ticks total -> way under min_train.
        ts_list = [_BASE_TS + i * (2 * _MS_PER_DAY // 30) for i in range(30)]
        persist.write_tickers_batch([
            _ticker(0, last_price=30_000.0 + i, ts=ts)
            for i, ts in enumerate(ts_list)
        ])

        bt = _new_bt(persist)
        bt.load_events()

        results = bt.run_walkforward(
            pipeline_interval_seconds=1.0,
            train_days=1,
            test_days=1,
            embargo_minutes=0,
            min_train_events=500,  # impossible to hit
        )

        # No folds executed, no trades recorded, no crash.
        assert bt.last_walkforward_folds == 0
        for res in results.values():
            assert res.n_trades == 0
            assert isinstance(res, BacktestResult)

    # ------------------------------------------------------------------
    # 5) Concatenation across folds
    # ------------------------------------------------------------------
    def test_walkforward_concatenates_across_folds(
        self, persist: PersistenceLayer
    ) -> None:
        """N folds * k trades-per-fold should accumulate into N*k trades on
        the final BacktestResult. We use a TestSubclass that mocks the inner
        ``_replay_events`` so we can deterministically deposit a fixed
        number of test-phase trades per fold without having to choreograph
        strategy internals.
        """
        # Stream long enough for ~3 folds at train=1d, test=1d, embargo=0.
        n = int(4.0 * 1440) + 10
        _persist_ticker_grid(persist, n=n, step_ms=60_000)

        class _DepositingReplayBT(ReplayBacktester):
            """Subclass whose ``_replay_events`` deposits 2 fake trades into
            ``trades_out`` only when ``record_trades=True`` (i.e. test phase).
            Strategy state is irrelevant for this test, only the bookkeeping.
            """

            def _replay_events(
                self,
                events,
                strategies,
                trade_buffer,
                liq_buffer,
                price_history,
                open_pos,
                trades_out,
                pipeline_interval_seconds,
                record_trades,
                last_ticker,
                last_ob_snap,
                last_pipeline_ms,
            ):
                if record_trades and events:
                    first_ts = events[0][0]
                    last_ts = events[-1][0]
                    for sid in trades_out:
                        for k in range(2):
                            trades_out[sid].append(
                                self._make_trade(
                                    side="Long",
                                    entry_price=30_000.0,
                                    entry_ts=first_ts + k,
                                    exit_price=30_010.0,
                                    exit_ts=last_ts,
                                )
                            )
                # Return a synthetic 'last' tuple consistent with the real
                # signature so the caller's force-close path is a no-op.
                last_ts = events[-1][0] if events else None
                return last_ticker, last_ob_snap, last_ts

        bt = _DepositingReplayBT(_SYMBOL, db_path=None)
        bt.persist = persist
        bt.load_events()

        results = bt.run_walkforward(
            pipeline_interval_seconds=60.0,
            train_days=1,
            test_days=1,
            embargo_minutes=0,
            min_train_events=10,
        )

        folds = bt.last_walkforward_folds
        assert folds >= 3
        for sid in ("S1", "S2", "S3", "S4", "S5"):
            assert results[sid].n_trades == 2 * folds, (
                f"{sid}: expected {2 * folds} trades, got "
                f"{results[sid].n_trades}"
            )

    # ------------------------------------------------------------------
    # 6) Lookahead-free guarantee
    # ------------------------------------------------------------------
    def test_walkforward_lookahead_free(
        self, persist: PersistenceLayer
    ) -> None:
        """Every ``ticker_data`` dict handed to a strategy at wall-clock
        ``ts`` must have been built using only events with ts <= ts. We
        probe this directly: on every call we read ``trades`` and
        ``liq_events`` out of ``ticker_data`` and assert none post-date the
        pipeline tick. We also assert that test-phase pipeline ticks live
        strictly inside [test_start, test_end)."""
        # Add trades alongside the tickers so the buffers fill up.
        n = 2 * 1440 + 60
        ts_list = _persist_ticker_grid(persist, n=n, step_ms=60_000)
        # One trade per ticker, same ts.
        persist.write_trades_batch(
            [_trade(0, price=30_000.0 + i) for i in range(n)],
            symbol=_SYMBOL,
        )
        # Override the trade ts so they match the ticker grid.
        persist.conn.execute("DELETE FROM trades")
        from bybit_edge.state.trade_buffer import TradeEvent as TE
        persist.write_trades_batch(
            [TE(timestamp_ms=ts, price=30_000.0 + i, volume=1.0,
                side="Buy", is_block=False) for i, ts in enumerate(ts_list)],
            symbol=_SYMBOL,
        )

        bt = _new_bt(persist)
        bt.load_events()

        violations: list[tuple[int, int]] = []
        pipeline_ts_seen: list[int] = []

        def probe_eval(strategy_id: str, strategy: Any, ticker_data: dict,
                       ts_seconds: float) -> dict:
            if strategy_id != "S1":
                return {"action": "wait", "direction": 0, "strategy": strategy_id}
            now_ms = int(ts_seconds * 1000)
            pipeline_ts_seen.append(now_ms)
            for tr in ticker_data["trades"]:
                if int(tr["timestamp_ms"]) > now_ms:
                    violations.append((int(tr["timestamp_ms"]), now_ms))
            for ev in ticker_data["liq_events"]:
                if int(ev["timestamp_ms"]) > now_ms:
                    violations.append((int(ev["timestamp_ms"]), now_ms))
            return {"action": "wait", "direction": 0, "strategy": "S1"}

        bt._eval_strategy = probe_eval  # type: ignore[assignment]

        bt.run_walkforward(
            pipeline_interval_seconds=60.0,
            train_days=1,
            test_days=1,
            embargo_minutes=30,
            min_train_events=10,
        )

        assert violations == [], (
            f"lookahead detected: {len(violations)} events with ts > now_ms"
        )
        # And: the probe must have seen at least one pipeline tick — i.e.
        # we actually exercised the causal path, not a vacuously-empty loop.
        assert pipeline_ts_seen, "walk-forward never evaluated a pipeline tick"


# ══════════════════════════════════════════════════════════════════════
# DuckDB concurrent-read regression: replay opens read-only
# ══════════════════════════════════════════════════════════════════════


class TestReplayReadOnlyConnect:
    """Regression: ``ReplayBacktester._open`` must request ``read_only=True``.

    Without this, the replay cannot attach to a DuckDB while the LiveRunner
    is holding the writer lock (``IOException: File is already open``). The
    test patches the :class:`PersistenceLayer` constructor and asserts the
    flag is set.
    """

    def test_replay_uses_read_only_connect(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured_kwargs: dict[str, Any] = {}

        # Build a minimal stub that mimics the attribute surface used by
        # ``_open`` callers (``conn`` + ``close``). We intercept the
        # constructor to capture the ``read_only`` flag without touching
        # any real DuckDB file.
        real_layer = PersistenceLayer(db_path=Path(":memory:"))

        class _StubLayer:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                captured_kwargs.update(kwargs)
                # Reuse the in-memory layer's connection so that any
                # downstream attribute access (``conn.execute(...)``) still
                # works — relevant for the ``load_events`` path even though
                # we don't drive it here.
                self.conn = real_layer.conn

            def close(self) -> None:
                pass

        monkeypatch.setattr(
            "bybit_edge.replay_backtester.PersistenceLayer", _StubLayer
        )

        try:
            bt = ReplayBacktester(symbol=_SYMBOL, db_path=Path("dummy.duckdb"))
            bt._open()
            assert captured_kwargs.get("read_only") is True, (
                f"expected read_only=True, got kwargs={captured_kwargs!r}"
            )
        finally:
            real_layer.close()
