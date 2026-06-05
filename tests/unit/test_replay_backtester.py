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


# ══════════════════════════════════════════════════════════════════════
# Regression: Replay must produce S3 trades on a pre-settlement scenario
# the live system would also trigger on.
# ══════════════════════════════════════════════════════════════════════


class TestReplayProducesS3Trades:
    """End-to-end regression for the "live triggers, replay stays at 0
    trades" bug.

    Context: the LiveRunner had logged ``SIGNAL [S3] action=long dir=1
    size=0.1988 conf=1.000`` on a 17h multi-symbol tick stream, yet
    ``python scripts/replay_all.py --auto`` reported ``n_trades=0`` for
    every strategy on every symbol. The replay must be apples-to-apples
    with live on the textbook PRD-7.3 pre-settlement scenario --
    otherwise the per-strategy edge metrics are meaningless.

    The test builds a deterministic two-phase ticker stream that
    satisfies every entry gate of :class:`Strategy3PreSettlement`:

    1. A "background" phase (3000 ticks) with mark==index ->
       basis = 0, pressure = 0. This builds up the Q90 pressure-history
       (>= 100 samples) and the M22 sigma estimate with benign samples,
       exactly mirroring what the LiveRunner would have accumulated
       before the settlement window opened. ``next_funding_time`` is
       set 2h ahead so we are NOT in the entry window during warmup.
    2. A "pressure" phase (200 ticks) where ``index_price`` is bumped
       0.5% above ``mark_price`` so that:

         * basis    = (mark - index) / index = -0.005  (-0.5%)
         * diff     = I_t - P_t = 0.0003 - (-0.005) = +0.0053
         * pressure = diff - clamp(diff, ±0.0005) = +0.0048 (positive)
         * direction = +1 (Long-reversion)
         * basis * direction = -0.005 * 1 < 0  (basis-aligned per PRD 7.3)

       ``next_funding_time`` is set to ``ticker_ts + 600_000 ms`` so that
       ``seconds_to_settlement`` is ~10 minutes -- well inside the 30-min
       :data:`PRESSURE_ENTRY_WINDOW_MINUTES` gate.

    With those inputs, S3's PRD-7.3 entry must fire on (at least) the
    first pressure tick. The replay therefore must return ``n_trades >= 1``
    on S3.

    Regression scope: this test pins down the contract that on a
    perfectly-aligned synthetic scenario the replay reaches an entry.
    A future refactor that breaks the strategy-direct ``action="enter"``
    contract or the ``_apply_signal`` ``"enter"``/``"exit"`` handling --
    e.g. routing the replay through the aggregator and forgetting to
    map ``"long"``/``"short"`` back -- will flip this test red.
    """

    def _persist_pre_settlement_scenario(
        self, persist: PersistenceLayer
    ) -> int:
        """Insert a warmup + pre-settlement ticker stream into DuckDB.

        Returns the timestamp (ms) of the first pre-settlement ticker so
        the test can sanity-check that ``seconds_to_settlement`` is well
        inside the 30-min window.
        """
        warmup_n = 3000  # >= Q90 history minimum (100) with comfortable margin
        pressure_n = 200
        step_ms = 1_000  # 1 ticker / second

        base_ts = _BASE_TS
        tickers: list[TickerSnapshot] = []

        # Phase 1: benign warmup -- mark == index so basis = 0 -> pressure = 0.
        # next_funding_time set far in the future so we are NOT in the
        # entry window yet (Condition 1 rejects).
        for i in range(warmup_n):
            ts = base_ts + i * step_ms
            tickers.append(_ticker(
                0,
                last_price=30_000.0 + (i % 5),  # tiny noise, no drift
                mark_price=30_000.0,
                index_price=30_000.0,
                next_funding_time=ts + 2 * 3600 * 1000,  # 2h ahead
                ts=ts,
            ))

        # Phase 2: pre-settlement pressure.
        # index_price bumped 0.5% above mark_price -> negative premium.
        # next_funding_time = ts + 10 min, so we ARE in the 30-min window.
        pre_settlement_start_ts = base_ts + warmup_n * step_ms
        mark_at_pressure = 30_000.0
        index_at_pressure = mark_at_pressure * (1.0 + 0.005)  # +0.5%
        for j in range(pressure_n):
            ts = pre_settlement_start_ts + j * step_ms
            tickers.append(_ticker(
                0,
                last_price=mark_at_pressure,
                mark_price=mark_at_pressure,
                index_price=index_at_pressure,
                next_funding_time=ts + 600_000,  # 10 min into the future
                ts=ts,
            ))

        persist.write_tickers_batch(tickers)
        return pre_settlement_start_ts

    def test_pre_settlement_scenario_yields_at_least_one_s3_trade(
        self, persist: PersistenceLayer
    ) -> None:
        pre_ts = self._persist_pre_settlement_scenario(persist)

        bt = _new_bt(persist)
        n = bt.load_events()
        assert n > 0, "scenario must populate events"

        # Sanity check: at pre_ts, seconds_to_settlement is in (0, 30 min).
        secs = ReplayBacktester._seconds_to_settlement(pre_ts + 600_000, pre_ts)
        assert 0.0 < secs < 30 * 60.0, (
            f"scenario broken: secs_to_settlement={secs}"
        )

        # Drive the replay through the real strategies (no fake_eval).
        # Use a tight pipeline interval so every ticker fires the strategies
        # -- mirrors the LiveRunner's 1s default but for fine resolution.
        results = bt.run(pipeline_interval_seconds=1.0)

        assert results["S3"].n_trades >= 1, (
            "S3 must trigger at least one round-trip trade on a textbook "
            "PRD-7.3 pre-settlement scenario; live ran this and emitted "
            f"a signal, replay returned n_trades={results['S3'].n_trades}"
        )


# ══════════════════════════════════════════════════════════════════════
# Regression: Replay must evaluate the strategies on every cadence interval
# across the whole event-time span — not exactly once.
# ══════════════════════════════════════════════════════════════════════


class TestReplayEvaluatesEveryInterval:
    """Regression for the "1 tick over millions of events" bug.

    Symptom (``replay_all.py --diagnose``)::

        S3: 1 ticks | in_window: 0 | pressure>Q90: 0 | ... | all_gates: 0

    i.e. on a multi-million-event production stream the strategies were
    evaluated EXACTLY ONCE instead of once per ``pipeline_interval_seconds``
    of event time, so no entry gate could ever accumulate and every symbol
    reported 0 trades.

    Root cause: Bybit V5 ticker WS payloads carry the message timestamp on the
    *envelope* (``payload["ts"]``), never inside the ticker ``data`` object that
    ``TickerSnapshot.from_ws`` parses. Every persisted ticker therefore lands
    with ``ts == 0``. The replay's event-time throttle compares
    ``ts - last_pipeline_ms < interval_ms``; with a constant ``ts`` this is true
    for every ticker after the first, so the pipeline fires once and never
    again.

    Fix: when the exchange ``ts`` is missing / non-positive the replay drives
    the cadence off the per-row ``recv_ts`` (reception wall-clock, persisted
    with every ticker and strictly increasing in stream order).

    This test reproduces the exact production shape — ``ts == 0`` with a
    ``recv_ts`` spread across ~1000 s of event time (one event every 2 s) — and
    asserts the strategies are evaluated hundreds of times, not once.
    """

    def _persist_ts_zero_stream(
        self, persist: PersistenceLayer, *, n: int, step_s: float
    ) -> None:
        """Insert *n* tickers with ``ts == 0`` and ``recv_ts`` advancing by
        ``step_s`` seconds — mirroring how the LiveRunner actually persisted
        ticker rows (envelope ``ts`` dropped → 0)."""
        base_recv_s = _BASE_TS / 1000.0
        tickers = [
            TickerSnapshot(
                symbol=_SYMBOL,
                last_price=30_000.0 + (i % 5),
                mark_price=30_000.0,
                index_price=30_000.0,
                funding_rate=0.0001,
                next_funding_time=0,
                open_interest=1_000_000.0,
                open_interest_value=3.0e10,
                bid1_price=29_999.0,
                bid1_size=5.0,
                ask1_price=30_001.0,
                ask1_size=5.0,
                ts=0,  # <-- the production reality: envelope ts is dropped
                recv_ts=base_recv_s + i * step_s,
            )
            for i in range(n)
        ]
        persist.write_tickers_batch(tickers)

    def test_strategies_evaluated_many_times_when_ts_is_zero(
        self, persist: PersistenceLayer
    ) -> None:
        # 500 events, one every 2 s -> ~1000 s of event time. At a 1 s cadence
        # the strategies must be evaluated ~hundreds of times, not once.
        self._persist_ts_zero_stream(persist, n=500, step_s=2.0)

        bt = ReplayBacktester(_SYMBOL, db_path=None, collect_diagnostics=True)
        bt.persist = persist
        n = bt.load_events()
        assert n == 500

        bt.run(pipeline_interval_seconds=1.0)

        n_ticks = bt.get_diagnostics()["S3"]["n_ticks_total"]
        # Pre-fix this was exactly 1 (throttle stuck on the constant ts==0).
        # Post-fix it tracks event-time via recv_ts: ~498. Use a generous lower
        # bound so the assertion is robust rather than brittle.
        assert n_ticks >= 50, (
            f"replay evaluated the pipeline only {n_ticks} time(s) over a "
            "~1000 s event-time span — the cadence is not advancing per "
            "interval (the '1 tick over millions of events' bug)"
        )
        # All five strategies share the same cadence -> each saw the same count.
        for sid in ("S1", "S2", "S3", "S4", "S5"):
            rc = bt.get_diagnostics()[sid]["reason_counts"]
            assert sum(rc.values()) >= 50, (
                f"{sid} evaluated only {sum(rc.values())} time(s)"
            )

    def test_distinct_exchange_ts_still_drives_cadence(
        self, persist: PersistenceLayer
    ) -> None:
        """When the exchange ``ts`` IS present and advancing (synthetic streams),
        the cadence keeps using it — behaviour is unchanged."""
        n = 500
        step_ms = 2_000  # one event / 2 s of *exchange* time
        persist.write_tickers_batch([
            _ticker(0, last_price=30_000.0 + (i % 5), ts=_BASE_TS + i * step_ms)
            for i in range(n)
        ])

        bt = ReplayBacktester(_SYMBOL, db_path=None, collect_diagnostics=True)
        bt.persist = persist
        bt.load_events()
        bt.run(pipeline_interval_seconds=1.0)

        n_ticks = bt.get_diagnostics()["S3"]["n_ticks_total"]
        assert n_ticks >= 50, n_ticks


# ══════════════════════════════════════════════════════════════════════
# Regression: Replay must detect the settlement window when persisted
# ticker rows have ``ts == 0`` (envelope-ts bug for legacy collected data).
# ══════════════════════════════════════════════════════════════════════


class TestReplayWindowDetection:
    """Regression for the "every tick outside settlement window" bug on
    legacy collected ticker rows where ``ts == 0``.

    Symptom (``replay_all.py --diagnose`` on a real 17h, 6-settlement
    stream)::

        S3: 2207 ticks | in_window: 0 | pressure>Q90: 0 | basis_aligned: 0
            | all_gates: 0
            wait_reasons: outside_settlement_window=2207

    Root cause: an earlier fix made the *throttle* in ``_replay_events``
    fall back to ``recv_ts * 1000`` when the persisted exchange ``ts``
    is 0, but :meth:`_build_ticker_data` still computed
    ``seconds_to_settlement`` off the raw ``snap["ts"] == 0``, yielding
    ``(next_funding_time - 0) / 1000 ≈ 1.7e9 s`` — i.e. orders of
    magnitude past the 30-min entry window. Every replay tick therefore
    reported ``outside_settlement_window`` and S3 produced 0 trades on
    legacy data, even on streams that the live runner had traded.

    Fix: when the persisted ``ts <= 0`` AND a ``recv_ts`` is available,
    the settlement countdown uses ``recv_ts * 1000`` as the event-time
    anchor — exactly the same fallback the throttle already uses, so
    the cadence and the window detection stay consistent.
    """

    def _persist_ts_zero_in_window_stream(
        self, persist: PersistenceLayer
    ) -> None:
        """Insert tickers with ``ts == 0`` (legacy collected) spanning ~1 h of
        ``recv_ts``, with ``next_funding_time`` set so the last ~5 min of the
        stream fall inside the 30-min entry window."""
        n = 3600  # 1 ticker per second of recv_ts -> 3600 s = 1 h event time
        base_recv_s = _BASE_TS / 1000.0
        # Final tick lands 5 min before the next funding settlement, so
        # ~the last 30 min of the stream are inside the entry window.
        last_recv_s = base_recv_s + (n - 1) * 1.0
        next_funding_ms = int(last_recv_s * 1000.0) + 5 * 60 * 1000

        tickers = [
            TickerSnapshot(
                symbol=_SYMBOL,
                last_price=30_000.0 + (i % 5),
                mark_price=30_000.0,
                index_price=30_000.0,
                funding_rate=0.0001,
                next_funding_time=next_funding_ms,
                open_interest=1_000_000.0,
                open_interest_value=3.0e10,
                bid1_price=29_999.0,
                bid1_size=5.0,
                ask1_price=30_001.0,
                ask1_size=5.0,
                ts=0,  # <-- the production reality on legacy collected rows
                recv_ts=base_recv_s + i * 1.0,
            )
            for i in range(n)
        ]
        persist.write_tickers_batch(tickers)

    def test_in_window_detected_when_ticker_ts_is_zero(
        self, persist: PersistenceLayer
    ) -> None:
        """At least a few ticks at the end of the stream must register as
        ``in_window`` once the settlement countdown uses the ``recv_ts``
        fallback to anchor itself in event time."""
        self._persist_ts_zero_in_window_stream(persist)

        bt = ReplayBacktester(_SYMBOL, db_path=None, collect_diagnostics=True)
        bt.persist = persist
        n = bt.load_events()
        assert n == 3600

        bt.run(pipeline_interval_seconds=1.0)

        diag = bt.get_diagnostics()["S3"]
        # Sanity: the cadence fix from the previous bug is still effective —
        # we must be evaluating the strategies many times, not exactly once.
        assert diag["n_ticks_total"] >= 100, diag
        # Core regression assertion: at least some ticks fall inside the
        # settlement window. Pre-fix this was 0 across millions of events.
        assert diag["n_in_window"] > 0, (
            "seconds_to_settlement still uses raw ticker.ts=0 — every "
            f"replay tick is gated outside_settlement_window: {diag}"
        )


class TestReplayDiagnostics:
    """Tests for the opt-in ``collect_diagnostics`` instrumentation.

    The diagnostics are strictly observational: with ``collect_diagnostics``
    off the replay must stay bit-identical, and with it on the trade counts
    must NOT change while the per-strategy wait-reason counters / S3 gate
    counters become populated.
    """

    def _flat_in_window_ticks(self) -> list[TickerSnapshot]:
        """Build a flat (mark==index) ticker stream *inside* the S3 settlement
        window.

        ``next_funding_time`` is 10 min ahead so ``seconds_to_settlement`` is
        well inside the 30-min entry window, but mark==index keeps the funding
        pressure at zero -> the Q90 gate (``pressure_below_q90``) blocks every
        entry. No round-trip trade can form.
        """
        n = 200
        step_ms = 1_000
        base_ts = _BASE_TS
        tickers: list[TickerSnapshot] = []
        for i in range(n):
            ts = base_ts + i * step_ms
            tickers.append(_ticker(
                0,
                last_price=30_000.0 + (i % 3),  # tiny noise, no drift
                mark_price=30_000.0,
                index_price=30_000.0,
                next_funding_time=ts + 600_000,  # 10 min ahead -> in window
                ts=ts,
            ))
        return tickers

    def test_diagnostics_disabled_by_default(
        self, persist: PersistenceLayer
    ) -> None:
        """Without ``collect_diagnostics`` the accumulators stay empty and
        ``get_diagnostics`` returns an empty dict (no per-tick overhead)."""
        persist.write_tickers_batch(self._flat_in_window_ticks())
        bt = _new_bt(persist)
        bt.load_events()
        bt.run(pipeline_interval_seconds=1.0)

        assert bt.get_diagnostics() == {}
        # No counters were ever touched.
        assert bt._reason_counts == {}
        assert bt._s3_counters == {}

    def test_diagnostics_counts_wait_reasons(
        self, persist: PersistenceLayer
    ) -> None:
        """A non-triggering in-window stream must accumulate S3 wait reasons,
        with ``pressure_below_q90`` dominating (window passes, Q90 blocks)."""
        persist.write_tickers_batch(self._flat_in_window_ticks())
        bt = ReplayBacktester(_SYMBOL, db_path=None, collect_diagnostics=True)
        bt.persist = persist
        bt.load_events()
        results = bt.run(pipeline_interval_seconds=1.0)

        diag = bt.get_diagnostics()
        assert set(diag.keys()) == {"S1", "S2", "S3", "S4", "S5"}
        s3_reasons = diag["S3"]["reason_counts"]
        assert s3_reasons.get("pressure_below_q90", 0) > 0, (
            f"expected pressure_below_q90 to dominate, got {s3_reasons}"
        )
        # The flat stream never triggers -> no S3 trades, no enter sentinel.
        assert results["S3"].n_trades == 0
        assert "__enter__" not in s3_reasons

    def test_diagnostics_s3_window_counter(
        self, persist: PersistenceLayer
    ) -> None:
        """Ticks placed inside the settlement window must increment
        ``n_in_window`` (read from M22's per-tick ``in_window`` sub-result)."""
        persist.write_tickers_batch(self._flat_in_window_ticks())
        bt = ReplayBacktester(_SYMBOL, db_path=None, collect_diagnostics=True)
        bt.persist = persist
        bt.load_events()
        bt.run(pipeline_interval_seconds=1.0)

        s3 = bt.get_diagnostics()["S3"]
        assert s3["n_ticks_total"] > 0
        assert s3["n_in_window"] > 0, (
            f"all ticks are inside the 30-min window, got {s3}"
        )
        # Pressure never exceeds Q90 on a flat stream -> no extreme / gates.
        assert s3["n_pressure_extreme"] == 0
        assert s3["n_all_gates_passed"] == 0

    def test_diagnostics_does_not_change_trades(
        self, persist: PersistenceLayer
    ) -> None:
        """The same replay with and without ``collect_diagnostics`` must yield
        IDENTICAL per-strategy trade counts — observation never alters the
        trade path. Uses the PRD-7.3 pre-settlement scenario so S3 actually
        trades (a non-trivial path to keep identical)."""
        scenario = TestReplayProducesS3Trades()
        scenario._persist_pre_settlement_scenario(persist)

        bt_off = _new_bt(persist)
        bt_off.load_events()
        res_off = bt_off.run(pipeline_interval_seconds=1.0)

        bt_on = ReplayBacktester(_SYMBOL, db_path=None, collect_diagnostics=True)
        bt_on.persist = persist
        bt_on.load_events()
        res_on = bt_on.run(pipeline_interval_seconds=1.0)

        for sid in ("S1", "S2", "S3", "S4", "S5"):
            assert res_off[sid].n_trades == res_on[sid].n_trades, (
                f"{sid}: diagnostics changed trade count "
                f"({res_off[sid].n_trades} -> {res_on[sid].n_trades})"
            )
        # And S3 did actually trade (so the equality is meaningful, not 0==0).
        assert res_on["S3"].n_trades >= 1
        # Sanity: the enter was observed in the diagnostics.
        assert bt_on.get_diagnostics()["S3"]["n_all_gates_passed"] >= 1


# ══════════════════════════════════════════════════════════════════════
# Regression: load_events must interleave ts=0 legacy tickers with real-ts
# trades by EFFECTIVE time (recv_ts fallback), not clump them at ts=0.
# ══════════════════════════════════════════════════════════════════════


class TestLoadEventsChronologicalWithLegacyTs:
    """Regression for the "ts=0 ticker clump destroys chronology" bug.

    On legacy collected data EVERY ticker row lands with ``ts == 0`` (the
    Bybit V5 envelope-ts was dropped by the collector), while trades carry a
    real exchange ``ts`` (from the "T" field). ``load_events`` merged all
    tables into one stream and sorted strictly by the raw ``ts``. Because
    ``0`` sorts before every real ms timestamp, ALL ts=0 tickers clumped at
    the very front of the stream instead of being interleaved chronologically
    with the trades — and within that clump the recv_ts order was not even
    guaranteed monotone.

    The downstream effect: the causal replay first burned through every
    ticker (driving the cadence off recv_ts) with EMPTY trade/liq buffers,
    then replayed every trade afterwards — so trade-history-dependent gates
    (Kyle's lambda, event-time arrays, S1 cascade) saw a buffer state that
    never matched what the ticker's effective time implied. This made the
    per-symbol results erratic / order-dependent.

    Fix: sort the merged stream by the EFFECTIVE event time
    (``ts`` when ``ts > 0`` else ``recv_ts * 1000``), keeping the kind-order
    tie-break. After the fix a ts=0 ticker with ``recv_ts=1002 s`` lands
    AFTER a trade at ``ts=1001000 ms`` but BEFORE a trade at ``ts=1003000 ms``.
    """

    def test_legacy_ts_zero_tickers_interleave_with_real_ts_trades(
        self, persist: PersistenceLayer
    ) -> None:
        # Build a mixed sequence over ~1 h of event time.
        #   * tickers: ts=0, recv_ts = 1000, 1002, 1004, ... seconds
        #   * trades : real ts in ms, offset 1 s "between" consecutive tickers
        #     so the correct interleaving is strictly trade/ticker/trade/...
        base_recv_s = 1000.0
        n = 50
        step_s = 2.0

        tickers = [
            TickerSnapshot(
                symbol=_SYMBOL,
                last_price=30_000.0 + (i % 5),
                mark_price=30_000.0,
                index_price=30_000.0,
                funding_rate=0.0001,
                next_funding_time=0,
                open_interest=1_000_000.0,
                open_interest_value=3.0e10,
                bid1_price=29_999.0,
                bid1_size=5.0,
                ask1_price=30_001.0,
                ask1_size=5.0,
                ts=0,  # <-- legacy collected reality
                recv_ts=base_recv_s + i * step_s,
            )
            for i in range(n)
        ]
        persist.write_tickers_batch(tickers)

        # Trades with REAL ts (ms) placed 1 s after each ticker's recv time,
        # i.e. ts_ms = (base_recv_s + i*step_s + 1.0) * 1000. The correct
        # chronological order is therefore:
        #   ticker_0 (eff=1000s) , trade_0 (1001s) , ticker_1 (1002s) ,
        #   trade_1 (1003s) , ticker_2 (1004s) , ...
        trades = [
            TradeEvent(
                timestamp_ms=int((base_recv_s + i * step_s + 1.0) * 1000.0),
                price=30_000.0 + i,
                volume=1.0,
                side="Buy",
                is_block=False,
            )
            for i in range(n)
        ]
        persist.write_trades_batch(trades, symbol=_SYMBOL)

        bt = _new_bt(persist)
        loaded = bt.load_events()
        assert loaded == 2 * n

        # Effective time of each event in stream order.
        def _eff(event: tuple) -> int:
            ts_ms, kind, payload = event
            if kind == "ticker":
                ts = int(payload["ts"])
                if ts > 0:
                    return ts
                return int(float(payload.get("recv_ts", 0.0)) * 1000.0)
            # trades / liq / ob carry a real exchange ts.
            return int(ts_ms)

        eff_sequence = [_eff(e) for e in bt._events]

        # Core assertion: the stream is monotone non-decreasing in EFFECTIVE
        # time. Pre-fix the 50 ts=0 tickers all clump at eff=... but with
        # tuple-ts 0 sorted first, so eff_sequence would start with the whole
        # ticker block (1000s..1098s) then jump back to the first trade
        # (1001s) — a hard non-monotone drop.
        assert eff_sequence == sorted(eff_sequence), (
            "merged stream is not chronological by effective time — ts=0 "
            "tickers clump instead of interleaving with real-ts trades"
        )

        # Stronger: assert the exact interleaving around a sample boundary.
        # ticker_1 has eff=1002s; it must sit AFTER trade_0 (eff=1001s) and
        # BEFORE trade_1 (eff=1003s).
        ticker1_eff = int((base_recv_s + 1 * step_s) * 1000.0)  # 1002000
        trade0_eff = int((base_recv_s + 0 * step_s + 1.0) * 1000.0)  # 1001000
        trade1_eff = int((base_recv_s + 1 * step_s + 1.0) * 1000.0)  # 1003000

        idx_ticker1 = next(
            i for i, e in enumerate(bt._events)
            if e[1] == "ticker" and _eff(e) == ticker1_eff
        )
        idx_trade0 = next(
            i for i, e in enumerate(bt._events)
            if e[1] == "trade" and e[0] == trade0_eff
        )
        idx_trade1 = next(
            i for i, e in enumerate(bt._events)
            if e[1] == "trade" and e[0] == trade1_eff
        )
        assert idx_trade0 < idx_ticker1 < idx_trade1, (
            "ticker_1 (eff=1002s) is not interleaved between trade_0 "
            "(1001s) and trade_1 (1003s)"
        )

    def test_real_ts_sort_is_bit_identical(
        self, persist: PersistenceLayer
    ) -> None:
        """With genuine ts>0 data the effective-time sort key must reduce to
        the raw ts — the merged stream is unchanged versus the legacy
        behaviour (eff_ts == ts when ts>0)."""
        persist.write_tickers_batch([_ticker(5), _ticker(1), _ticker(3)])
        persist.write_trades_batch([_trade(4), _trade(0)], symbol=_SYMBOL)
        persist.write_liquidations_batch([_liq(2)])

        bt = _new_bt(persist)
        n = bt.load_events()
        assert n == 6

        ts_sequence = [e[0] for e in bt._events]
        # Tuple-ts equals the raw exchange ts for every event (no recv_ts
        # substitution happened) and is strictly sorted.
        assert ts_sequence == sorted(ts_sequence)
        expected = sorted(
            _BASE_TS + i * 1000 for i in (0, 1, 2, 3, 4, 5)
        )
        assert ts_sequence == expected


# ══════════════════════════════════════════════════════════════════════
# Performance work: behaviour-preservation + Hawkes throttle + progress.
# ══════════════════════════════════════════════════════════════════════


def _persist_cascade_for_s1(persist: PersistenceLayer) -> None:
    """Persist a ticker grid + trade flow + a dense liquidation cascade.

    The cascade drives S1 -> M14 (Hawkes-MLE) + M15 (Omori curve_fit), i.e.
    the exact hot path the optimisation touches, so the behaviour-preservation
    assertion is meaningful (not 0==0 on an inert stream).
    """
    base = _BASE_TS
    tickers = [
        _ticker(0, last_price=30_000.0 + (i % 11), ts=base + i * 1000)
        for i in range(400)
    ]
    persist.write_tickers_batch(tickers)
    persist.write_trades_batch(
        [
            TradeEvent(
                timestamp_ms=base + i * 1000,
                price=30_000.0 - i * 2.0,
                volume=1.0 + (i % 5),
                side="Sell",
                is_block=False,
            )
            for i in range(200)
        ],
        symbol=_SYMBOL,
    )
    liqs = []
    for i in range(120):
        liqs.append(
            LiquidationEvent(
                timestamp_ms=base + (150 + i) * 1000,
                symbol=_SYMBOL,
                side="Sell",
                volume=(1.0e6 + i * 5e4) / 30_000.0,
                price=30_000.0,
                usd_value=1.0e6 + i * 5e4,
            )
        )
    persist.write_liquidations_batch(liqs)


class TestReplayOptimizationPreservesResults:
    """The replay results must be identical before/after the M15 optimisation.

    We assert two complementary properties:

    1. **Determinism** — the exact same loaded stream replayed twice yields
       identical per-strategy ``n_trades`` / ``sharpe`` (no hidden state leak
       from the vectorised buffers).
    2. **Equivalence to the legacy M15 path** — replaying with the live
       (vectorised) ``M15GROmori.compute`` must produce the SAME per-strategy
       results as replaying with the pre-optimisation list-based compute,
       monkey-patched in as an oracle. This is the load-bearing guarantee that
       the optimisation did not move any trade.
    """

    def test_replay_is_deterministic(self, persist: PersistenceLayer) -> None:
        _persist_cascade_for_s1(persist)
        bt1 = _new_bt(persist)
        bt1.load_events()
        r1 = bt1.run(pipeline_interval_seconds=1.0)

        bt2 = _new_bt(persist)
        bt2.load_events()
        r2 = bt2.run(pipeline_interval_seconds=1.0)

        for sid in ("S1", "S2", "S3", "S4", "S5"):
            assert r1[sid].n_trades == r2[sid].n_trades
            assert r1[sid].sharpe == pytest.approx(r2[sid].sharpe, rel=1e-12)
            assert r1[sid].total_return == pytest.approx(
                r2[sid].total_return, rel=1e-12
            )

    def test_results_match_legacy_m15(
        self, persist: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from tests.unit.test_m15_gr_omori import _legacy_compute
        from bybit_edge.layers.l4_pattern.m15_gr_omori import M15GROmori

        _persist_cascade_for_s1(persist)

        # Optimised (live) path.
        bt_opt = _new_bt(persist)
        bt_opt.load_events()
        res_opt = bt_opt.run(pipeline_interval_seconds=1.0)

        # Legacy oracle path — the pre-optimisation list-based compute. The
        # legacy reference returns a subset of keys; the replay only consumes
        # b_value / omori_active / omori_params / mainshock_ts, all present.
        def legacy_compute(self, liq_events, current_ts):  # noqa: ANN001
            return _legacy_compute(self, liq_events, current_ts)

        monkeypatch.setattr(M15GROmori, "compute", legacy_compute)

        bt_legacy = _new_bt(persist)
        bt_legacy.load_events()
        res_legacy = bt_legacy.run(pipeline_interval_seconds=1.0)

        for sid in ("S1", "S2", "S3", "S4", "S5"):
            assert res_opt[sid].n_trades == res_legacy[sid].n_trades, (
                f"{sid}: optimisation changed n_trades "
                f"({res_legacy[sid].n_trades} -> {res_opt[sid].n_trades})"
            )
            assert res_opt[sid].sharpe == pytest.approx(
                res_legacy[sid].sharpe, rel=1e-9, abs=1e-9
            )


class TestHawkesRefitThrottled:
    """M14 must refit the MLE at most once per ``HAWKES_REFIT_SECONDS`` of
    event time — the throttle is time-based so the LiveRunner behaves
    identically. We count ``_fit_mle`` invocations over many compute() calls
    inside a single refit window and assert it ran exactly once."""

    def test_fit_called_once_within_refit_window(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from bybit_edge.config import HAWKES_REFIT_SECONDS
        from bybit_edge.layers.l4_pattern.m14_hawkes import M14HawkesSingleChannel

        m14 = M14HawkesSingleChannel()
        calls = {"n": 0}
        real_fit = m14._fit_mle

        def counting_fit(events):  # noqa: ANN001
            calls["n"] += 1
            return real_fit(events)

        monkeypatch.setattr(m14, "_fit_mle", counting_fit)

        # Enough events for a fit, all inside one refit window.
        base = 1000.0
        event_times = np.array([base + i * 0.5 for i in range(20)], dtype=np.float64)
        # Many compute() calls spaced < HAWKES_REFIT_SECONDS apart in event time.
        n_calls = 0
        t = base + 10.0
        while t < base + HAWKES_REFIT_SECONDS - 1.0:
            m14.compute(event_times, current_ts=t)
            n_calls += 1
            t += 1.0

        assert n_calls > 1, "test must issue multiple compute calls"
        assert calls["n"] == 1, (
            f"M14 refit {calls['n']}x inside one {HAWKES_REFIT_SECONDS}s window "
            "— the throttle is broken (would be the per-tick MLE killer)"
        )

    def test_fit_runs_again_after_refit_window(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from bybit_edge.config import HAWKES_REFIT_SECONDS
        from bybit_edge.layers.l4_pattern.m14_hawkes import M14HawkesSingleChannel

        m14 = M14HawkesSingleChannel()
        calls = {"n": 0}
        real_fit = m14._fit_mle

        def counting_fit(events):  # noqa: ANN001
            calls["n"] += 1
            return real_fit(events)

        monkeypatch.setattr(m14, "_fit_mle", counting_fit)

        base = 1000.0
        event_times = np.array([base + i * 0.5 for i in range(20)], dtype=np.float64)
        m14.compute(event_times, current_ts=base + 10.0)  # fit #1
        # Advance > refit window -> a second fit must fire.
        m14.compute(event_times, current_ts=base + 10.0 + HAWKES_REFIT_SECONDS + 1.0)
        assert calls["n"] == 2


class TestProgressLogging:
    """The opt-in progress reporter must emit lines when enabled and stay
    completely silent (and bit-identical) when disabled."""

    def test_progress_emits_when_enabled(
        self, persist: PersistenceLayer, caplog: pytest.LogCaptureFixture
    ) -> None:
        persist.write_tickers_batch(
            [_ticker(i, last_price=30_000.0 + i, ts=_BASE_TS + i * 1000)
             for i in range(60)]
        )
        bt = _new_bt(persist)
        bt.load_events()

        with caplog.at_level("INFO", logger="bybit_edge.replay_backtester"):
            # Tiny cadence so a progress line fires within the short stream.
            # The wall-clock floor is bypassed by the final finish() line, which
            # always emits, so we assert on that deterministically.
            bt.run(
                pipeline_interval_seconds=1.0,
                progress=True,
                progress_every_events=10,
            )

        msgs = [r.getMessage() for r in caplog.records]
        assert any("fertig in" in m for m in msgs), (
            f"no terminal progress line emitted: {msgs}"
        )
        assert any(m.startswith(f"[{_SYMBOL}]") for m in msgs)

    def test_progress_silent_when_disabled(
        self, persist: PersistenceLayer, caplog: pytest.LogCaptureFixture
    ) -> None:
        persist.write_tickers_batch(
            [_ticker(i, last_price=30_000.0 + i, ts=_BASE_TS + i * 1000)
             for i in range(60)]
        )
        bt = _new_bt(persist)
        bt.load_events()

        with caplog.at_level("INFO", logger="bybit_edge.replay_backtester"):
            bt.run(pipeline_interval_seconds=1.0)  # progress defaults OFF

        progress_lines = [
            r.getMessage() for r in caplog.records
            if "fertig in" in r.getMessage() or r.getMessage().startswith("[")
        ]
        assert progress_lines == [], (
            f"progress lines leaked with progress disabled: {progress_lines}"
        )

    def test_progress_does_not_change_trades(
        self, persist: PersistenceLayer
    ) -> None:
        _persist_cascade_for_s1(persist)

        bt_off = _new_bt(persist)
        bt_off.load_events()
        res_off = bt_off.run(pipeline_interval_seconds=1.0)

        bt_on = _new_bt(persist)
        bt_on.load_events()
        res_on = bt_on.run(
            pipeline_interval_seconds=1.0, progress=True, progress_every_events=5
        )

        for sid in ("S1", "S2", "S3", "S4", "S5"):
            assert res_off[sid].n_trades == res_on[sid].n_trades


# ══════════════════════════════════════════════════════════════════════
# Opt-in M15 Omori refit throttle (--fast-omori path)
# ══════════════════════════════════════════════════════════════════════


class TestReplayM15RefitThrottle:
    """The ``m15_refit_seconds`` constructor kwarg wires the M15 throttle.

    Bit-identical default + measurable speedup when opted-in + tolerance band
    around the un-throttled result on a cascade-heavy stream.
    """

    def test_replay_default_uses_no_throttle(
        self, persist: PersistenceLayer
    ) -> None:
        """Default ReplayBacktester() builds Strategy1 with M15 ``refit_seconds=0``."""
        bt = _new_bt(persist)
        assert bt._m15_refit_seconds == 0.0
        strategies = bt._build_strategies()
        # Default M15 has refit_seconds=0.0 (bit-identical path).
        assert strategies["S1"].m15._refit_seconds == 0.0

    def test_replay_with_m15_refit_overrides_strategy1_m15(
        self, persist: PersistenceLayer
    ) -> None:
        """Passing the kwarg replaces Strategy1's M15 with a throttled copy."""
        bt = ReplayBacktester(_SYMBOL, db_path=None, m15_refit_seconds=30.0)
        bt.persist = persist
        strategies = bt._build_strategies()
        assert strategies["S1"].m15._refit_seconds == 30.0

    @staticmethod
    def _persist_real_cascade(persist: PersistenceLayer) -> None:
        """Persist a stream that actually drives M15 ``_fit_omori`` per tick.

        ``_persist_cascade_for_s1`` builds a monotonically growing liquidation
        list which never crosses Q99 (the largest events ARE the right tail).
        We need: many background events at low USD, ONE clear mainshock spike
        well above Q99, then dense aftershocks AFTER the mainshock — exactly
        the shape M15 was designed for.
        """
        base = _BASE_TS
        # Ticker grid so the pipeline ticks every second.
        tickers = [
            _ticker(0, last_price=30_000.0 + (i % 11), ts=base + i * 1000)
            for i in range(400)
        ]
        persist.write_tickers_batch(tickers)
        persist.write_trades_batch(
            [
                TradeEvent(
                    timestamp_ms=base + i * 1000,
                    price=30_000.0 - (i % 17) * 0.5,
                    volume=1.0 + (i % 5),
                    side="Sell",
                    is_block=False,
                )
                for i in range(200)
            ],
            symbol=_SYMBOL,
        )
        liqs: list[LiquidationEvent] = []
        # 80 small background liquidations spread across the first 80s, so the
        # rolling Q99 is anchored below the mainshock.
        for i in range(80):
            liqs.append(
                LiquidationEvent(
                    timestamp_ms=base + i * 1000,
                    symbol=_SYMBOL,
                    side="Sell",
                    volume=30.0,
                    price=30_000.0,
                    usd_value=1.0e5 + (i % 7) * 1.0e4,
                )
            )
        # The mainshock — a single huge event.
        mainshock_ms = base + 80_000
        liqs.append(
            LiquidationEvent(
                timestamp_ms=mainshock_ms,
                symbol=_SYMBOL,
                side="Sell",
                volume=2_000.0,
                price=30_000.0,
                usd_value=6.0e7,
            )
        )
        # 60 aftershocks within the next ~120s (1 every 2 s), all moderate.
        for j in range(60):
            liqs.append(
                LiquidationEvent(
                    timestamp_ms=mainshock_ms + (j + 1) * 2000,
                    symbol=_SYMBOL,
                    side="Sell",
                    volume=10.0,
                    price=30_000.0,
                    usd_value=2.0e5 + (j % 5) * 3.0e4,
                )
            )
        persist.write_liquidations_batch(liqs)

    def test_replay_with_fast_omori_speedup(
        self, persist: PersistenceLayer
    ) -> None:
        """Throttled replay calls ``_fit_omori`` fewer times than the default.

        We count invocations via :func:`unittest.mock.patch.object` on the
        ``M15GROmori._fit_omori`` method (class-level patch so it covers every
        freshly constructed M15 inside the replay).
        """
        from unittest import mock
        from bybit_edge.layers.l4_pattern.m15_gr_omori import M15GROmori

        self._persist_real_cascade(persist)

        # Default (no throttle).
        bt_off = _new_bt(persist)
        bt_off.load_events()
        original = M15GROmori._fit_omori
        counter_off = {"n": 0}

        def spy_off(self, *args, **kwargs):  # noqa: ANN001
            counter_off["n"] += 1
            return original(self, *args, **kwargs)

        with mock.patch.object(M15GROmori, "_fit_omori", spy_off):
            bt_off.run(pipeline_interval_seconds=1.0)
        n_fits_off = counter_off["n"]

        # Throttled — refit only every 30 s of event time.
        bt_on = ReplayBacktester(
            _SYMBOL, db_path=None, m15_refit_seconds=30.0
        )
        bt_on.persist = persist
        bt_on.load_events()
        counter_on = {"n": 0}

        def spy_on(self, *args, **kwargs):  # noqa: ANN001
            counter_on["n"] += 1
            return original(self, *args, **kwargs)

        with mock.patch.object(M15GROmori, "_fit_omori", spy_on):
            bt_on.run(pipeline_interval_seconds=1.0)
        n_fits_on = counter_on["n"]

        # On a 120 s cascade the throttled path should fit a handful of times
        # while the un-throttled path is per-tick. Strict requirement:
        # throttled MUST be strictly smaller (and both paths must actually
        # exercise ``_fit_omori`` so the assertion isn't vacuous).
        assert n_fits_off > 0, (
            "Synthetic cascade did not trigger any curve_fit calls in the "
            "default path — the test setup is broken."
        )
        assert n_fits_on < n_fits_off, (
            f"Throttle did not reduce curve_fit calls: "
            f"off={n_fits_off}, on={n_fits_on}"
        )

    def test_replay_with_fast_omori_close_to_default(
        self, persist: PersistenceLayer
    ) -> None:
        """Throttled result must be in a tolerance band around the default.

        Documented tolerance: ±20 % on ``n_trades`` per strategy. On synthetic
        data the trade sets are often even identical; the band absorbs the
        documented Aftershock-Decay grey-zone (see M15 docstring).
        """
        self._persist_real_cascade(persist)

        bt_off = _new_bt(persist)
        bt_off.load_events()
        res_off = bt_off.run(pipeline_interval_seconds=1.0)

        bt_on = ReplayBacktester(
            _SYMBOL, db_path=None, m15_refit_seconds=30.0
        )
        bt_on.persist = persist
        bt_on.load_events()
        res_on = bt_on.run(pipeline_interval_seconds=1.0)

        for sid in ("S1", "S2", "S3", "S4", "S5"):
            n_off = res_off[sid].n_trades
            n_on = res_on[sid].n_trades
            if n_off == 0:
                # When the default produced no trades, the band is absolute:
                # at most a handful of extra trades.
                assert n_on <= 2, (
                    f"{sid}: throttle produced {n_on} trades vs default 0"
                )
            else:
                tol = max(1, int(round(0.20 * n_off)))
                assert abs(n_on - n_off) <= tol, (
                    f"{sid}: |n_on={n_on} - n_off={n_off}| > {tol} (±20%)"
                )
