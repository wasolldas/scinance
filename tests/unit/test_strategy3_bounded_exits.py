"""
Tests for iter-4 Push A T1: S3 time-stop and hard-stop-loss bounded exits.

Both exits are opt-in via config flags and default OFF -> bit-identical to
iter-3 behaviour. The empirical motivation is the worst-3-trades-duration
ratio of 1.7-3.0x on every symbol in the iter-3 replay (worst BNB trade
-195 bps over 1559 s).

Follows the helper pattern in :mod:`tests.unit.test_strategy3`.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from bybit_edge import config as _cfg
from bybit_edge.strategies.strategy3_pre_settlement import (
    Strategy3PreSettlement,
)


def _make_ticker(
    last_price: float = 50000.0,
    mark_price: float = 50050.0,
    index_price: float = 50000.0,
    funding_rate: float = 0.0001,
    premium_index: float = 0.001,
) -> dict[str, Any]:
    return {
        "last_price": last_price,
        "mark_price": mark_price,
        "index_price": index_price,
        "funding_rate": funding_rate,
        "premium_index": premium_index,
    }


def _warm_up_strategy(
    strat: Strategy3PreSettlement,
    n_samples: int = 200,
    premium_index: float = 0.0003,
) -> None:
    for i in range(n_samples):
        strat.on_ticker(
            _make_ticker(premium_index=premium_index),
            seconds_to_settlement=3600.0,
            open_interest=1000.0 + i * 0.1,
        )


def _enter_long(strat: Strategy3PreSettlement, entry_price: float = 49950.0) -> None:
    """Trigger a Long entry. (negative Premium → positive pressure → Long;
    aligned with negative basis: mark < index.)"""
    ticker = _make_ticker(
        last_price=entry_price,
        premium_index=-0.01,
        mark_price=49950.0,
        index_price=50000.0,
    )
    result = strat.on_ticker(
        ticker, seconds_to_settlement=900.0, open_interest=1100.0
    )
    assert result["action"] == "enter"
    assert result["direction"] == 1


@pytest.fixture(autouse=True)
def _reset_s3_flags():
    """Ensure each test starts with all iter-4 flags off; restore after."""
    saved = (
        _cfg.S3_TIME_STOP_ENABLED,
        _cfg.S3_TIME_STOP_MS,
        _cfg.S3_HARD_STOP_ENABLED,
        _cfg.S3_HARD_STOP_BPS,
        _cfg.S3_INVERT_DIRECTION,
        _cfg.S3_FRICTION_BPS_PER_LEG,
    )
    _cfg.S3_TIME_STOP_ENABLED = False
    _cfg.S3_HARD_STOP_ENABLED = False
    _cfg.S3_INVERT_DIRECTION = False
    yield
    (
        _cfg.S3_TIME_STOP_ENABLED,
        _cfg.S3_TIME_STOP_MS,
        _cfg.S3_HARD_STOP_ENABLED,
        _cfg.S3_HARD_STOP_BPS,
        _cfg.S3_INVERT_DIRECTION,
        _cfg.S3_FRICTION_BPS_PER_LEG,
    ) = saved


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════

def test_time_stop_fires_when_enabled() -> None:
    """With S3_TIME_STOP_ENABLED=True, advancing wall-clock by 121 s past
    entry triggers the time_stop_exceeded exit."""
    strat = Strategy3PreSettlement()
    _warm_up_strategy(strat)
    _enter_long(strat)
    assert strat.in_trade
    entry_ts = strat._entry_ts

    _cfg.S3_TIME_STOP_ENABLED = True

    # Drive a follow-up tick with wall-clock advanced 121 s (> 120 s cap).
    # Settlement is still 800 s away, so the existing settlement clauses
    # cannot fire.
    with patch("bybit_edge.strategies.strategy3_pre_settlement.time.time",
               return_value=entry_ts + 121.0):
        result = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=49950.0),
            seconds_to_settlement=800.0,
            open_interest=1100.0,
        )
    assert result["action"] == "exit"
    assert result["reason"] == "time_stop_exceeded"
    assert strat.in_trade is False


def test_time_stop_off_by_default() -> None:
    """Flag off: advancing wall-clock 600 s past entry does NOT trigger
    time_stop_exceeded. Settlement is still in the future so other exits
    also stay quiet — this is the explicit baseline-unchanged guard."""
    strat = Strategy3PreSettlement()
    _warm_up_strategy(strat)
    _enter_long(strat)
    entry_ts = strat._entry_ts

    # Flag stays False (fixture default).
    with patch("bybit_edge.strategies.strategy3_pre_settlement.time.time",
               return_value=entry_ts + 600.0):
        result = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=49950.0),
            seconds_to_settlement=300.0,
            open_interest=1100.0,
        )
    assert result.get("reason") != "time_stop_exceeded"


def test_hard_stop_long_fires_at_threshold() -> None:
    """Long entry at 100.0 with S3_HARD_STOP_ENABLED=True.
    At price 99.65 (-35 bps): exits with hard_stop_loss.
    At price 99.85 (-15 bps): no hard-stop exit (still in trade)."""
    strat = Strategy3PreSettlement()
    # Inject a clean Long entry without driving the gates: bypass on_ticker
    # entry path so price=100.0 is exact (the strategy normally stores the
    # slipped tick price). The MTM logic only reads _entry_price /
    # _entry_direction.
    strat._in_trade = True
    strat._entry_price = 100.0
    strat._entry_direction = 1
    strat._entry_ts = 1_000.0
    strat._settlement_ts = 5_000.0

    _cfg.S3_HARD_STOP_ENABLED = True

    # -15 bps: not enough.
    r1 = strat._check_exit(
        seconds_to_settlement=500.0, pressure=0.0005, now=1_001.0, price=99.85
    )
    assert r1 != "hard_stop_loss"

    # -35 bps: below the -30 bps floor.
    r2 = strat._check_exit(
        seconds_to_settlement=500.0, pressure=0.0005, now=1_001.0, price=99.65
    )
    assert r2 == "hard_stop_loss"


def test_hard_stop_short_fires_at_threshold() -> None:
    """Short entry: MTM uses (entry - price) / entry. A price rise above
    threshold triggers hard_stop_loss. Verifies direction-safe sign."""
    strat = Strategy3PreSettlement()
    strat._in_trade = True
    strat._entry_price = 100.0
    strat._entry_direction = -1   # Short
    strat._entry_ts = 1_000.0
    strat._settlement_ts = 5_000.0

    _cfg.S3_HARD_STOP_ENABLED = True

    # Price rises to 100.35 -> Short loses -35 bps.
    r = strat._check_exit(
        seconds_to_settlement=500.0, pressure=0.0005, now=1_001.0, price=100.35
    )
    assert r == "hard_stop_loss"

    # Price falls -> Short gains, no hard-stop.
    r2 = strat._check_exit(
        seconds_to_settlement=500.0, pressure=0.0005, now=1_001.0, price=99.0
    )
    assert r2 != "hard_stop_loss"


def test_bnb_outlier_would_have_exited() -> None:
    """Regression-of-bug-class: synthetic BNB outlier (1559 s hold) would
    have been time-stopped at 120 s. Wall-clock guard, not market state."""
    strat = Strategy3PreSettlement()
    _warm_up_strategy(strat)
    _enter_long(strat, entry_price=600.0)
    entry_ts = strat._entry_ts

    _cfg.S3_TIME_STOP_ENABLED = True

    # First check at 119 s: still in trade.
    with patch("bybit_edge.strategies.strategy3_pre_settlement.time.time",
               return_value=entry_ts + 119.0):
        r119 = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=49950.0),
            seconds_to_settlement=800.0,
            open_interest=1100.0,
        )
    assert r119["action"] != "exit" or r119.get("reason") != "time_stop_exceeded"

    # At 121 s: time-stop fires. Original outlier ran 1559 s.
    with patch("bybit_edge.strategies.strategy3_pre_settlement.time.time",
               return_value=entry_ts + 121.0):
        r121 = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=49950.0),
            seconds_to_settlement=800.0,
            open_interest=1100.0,
        )
    assert r121["action"] == "exit"
    assert r121["reason"] == "time_stop_exceeded"


def test_trade_record_has_full_friction_accounting() -> None:
    """Time-stop exit routed through ReplayBacktester._apply_signal produces
    a Trade with non-NaN raw_pnl / entry_fee / exit_fee and fee identity
    pnl == raw_pnl - entry_fee - exit_fee to 1e-9."""
    import math
    from pathlib import Path

    from bybit_edge.persistence.db import PersistenceLayer
    from bybit_edge.replay_backtester import ReplayBacktester

    persist = PersistenceLayer(db_path=Path(":memory:"))
    try:
        bt = ReplayBacktester(symbol="BTCUSDT", db_path=Path(":memory:"))
        open_pos: dict[str, Any] = {"S3": None}
        trades_out: dict[str, list[Any]] = {"S3": []}

        # Synthetic enter -> exit cycle.
        bt._apply_signal(
            strategy_id="S3",
            signal={"action": "enter", "direction": 1, "price": 100.0},
            price=100.0,
            ts_ms=1_000_000,
            open_pos=open_pos,
            trades_out=trades_out,
        )
        bt._apply_signal(
            strategy_id="S3",
            signal={
                "action": "exit",
                "direction": 1,
                "price": 99.5,
                "reason": "time_stop_exceeded",
            },
            price=99.5,
            ts_ms=1_120_000,
            open_pos=open_pos,
            trades_out=trades_out,
        )
        bt.close()
    finally:
        persist.close()

    assert len(trades_out["S3"]) == 1
    t = trades_out["S3"][0]
    assert not math.isnan(t.raw_pnl)
    assert not math.isnan(t.entry_fee)
    assert not math.isnan(t.exit_fee)
    assert abs(t.pnl - (t.raw_pnl - t.entry_fee - t.exit_fee)) < 1e-9


def test_flags_off_baseline_unchanged() -> None:
    """Explicit guard: with both T1 flags off, a deterministic 3-tick
    fixture produces an exit list matching a hard-coded snapshot."""
    strat = Strategy3PreSettlement()
    _warm_up_strategy(strat)
    _enter_long(strat)

    # Flags stay OFF (fixture default).
    exits: list[tuple[str, str]] = []
    # Tick 1: still in window, pressure not dissipated -> no exit.
    r1 = strat.on_ticker(
        _make_ticker(premium_index=-0.01, mark_price=49950.0),
        seconds_to_settlement=500.0,
        open_interest=1100.0,
    )
    if r1["action"] == "exit":
        exits.append((r1["action"], r1["reason"]))
    # Tick 2: pressure dissipated -> exit "pressure_dissipated".
    r2 = strat.on_ticker(
        _make_ticker(premium_index=0.0003, mark_price=50000.0, index_price=50000.0),
        seconds_to_settlement=400.0,
        open_interest=1100.0,
    )
    if r2["action"] == "exit":
        exits.append((r2["action"], r2["reason"]))

    expected: list[tuple[str, str]] = [("exit", "pressure_dissipated")]
    assert exits == expected


# ═══════════════════════════════════════════════════════════════════
# iter-5 T1: market-tick time threaded through on_ticker
# ═══════════════════════════════════════════════════════════════════

def test_time_stop_uses_market_time_not_wall_clock() -> None:
    """Regression for the iter-4 fast-replay bug. Pass `ts=` to on_ticker
    and advance market time by 121 s WITHOUT touching wall-clock. The
    time-stop must fire because the elapsed math now uses market time.

    This is the load-bearing test of iter-5 T1: would have caught the
    1-of-213-firings bug in iter-4 Push A.
    """
    strat = Strategy3PreSettlement()
    _warm_up_strategy(strat)

    # Enter Long at market-tick ts = 1_000_000.0
    entry_ticker = _make_ticker(
        last_price=49950.0,
        premium_index=-0.01,
        mark_price=49950.0,
        index_price=50000.0,
    )
    entry_result = strat.on_ticker(
        entry_ticker,
        seconds_to_settlement=900.0,
        open_interest=1100.0,
        ts=1_000_000.0,
    )
    assert entry_result["action"] == "enter"
    assert strat._entry_ts == 1_000_000.0

    _cfg.S3_TIME_STOP_ENABLED = True

    # Drive a follow-up tick 121 s LATER in market time. Wall-clock
    # between the two on_ticker calls is sub-millisecond — the iter-4
    # implementation would NOT have fired the time-stop here.
    result = strat.on_ticker(
        _make_ticker(premium_index=-0.01, mark_price=49950.0),
        seconds_to_settlement=779.0,
        open_interest=1100.0,
        ts=1_000_121.0,
    )
    assert result["action"] == "exit"
    assert result["reason"] == "time_stop_exceeded"


def test_default_ts_falls_back_to_wall_clock() -> None:
    """Bit-identical guard: when `ts` is not passed, on_ticker falls back
    to `time.time()` for both the entry stamp and the time-stop math, so
    iter-4-style `patch("...time.time", ...)` mocks keep working.
    """
    import time as _time

    strat = Strategy3PreSettlement()
    _warm_up_strategy(strat)

    # Enter without passing ts=. Confirm _entry_ts comes from wall-clock.
    wall_before: float = _time.time()
    _enter_long(strat)
    wall_after: float = _time.time()
    assert wall_before <= strat._entry_ts <= wall_after

    entry_ts = strat._entry_ts
    _cfg.S3_TIME_STOP_ENABLED = True

    # Drive another tick without ts= and patch time.time forward.
    with patch("bybit_edge.strategies.strategy3_pre_settlement.time.time",
               return_value=entry_ts + 121.0):
        result = strat.on_ticker(
            _make_ticker(premium_index=-0.01, mark_price=49950.0),
            seconds_to_settlement=800.0,
            open_interest=1100.0,
        )
    assert result["action"] == "exit"
    assert result["reason"] == "time_stop_exceeded"


def test_replay_call_site_passes_ts() -> None:
    """Call-site contract: ReplayBacktester._eval_strategy must thread
    ts_seconds into Strategy3PreSettlement.on_ticker as the `ts` kwarg.

    Uses the real-strategy form: build a Strategy3PreSettlement, warm it
    up to entry-ready, then call _eval_strategy with a known ts_seconds
    and assert the entry stamp matches.
    """
    from pathlib import Path

    from bybit_edge.replay_backtester import ReplayBacktester

    bt = ReplayBacktester(symbol="BTCUSDT", db_path=Path(":memory:"))
    try:
        strat = Strategy3PreSettlement()
        _warm_up_strategy(strat)

        # Build the minimal ticker_data _eval_strategy reads for S3.
        ticker_data: dict[str, Any] = {
            "last_price": 49950.0,
            "mark_price": 49950.0,
            "index_price": 50000.0,
            "funding_rate": 0.0001,
            "premium_index": -0.01,
            "seconds_to_settlement": 900.0,
            "open_interest": 1100.0,
        }
        result = bt._eval_strategy(
            strategy_id="S3",
            strategy=strat,
            ticker_data=ticker_data,
            ts_seconds=12345.0,
        )
        assert result["action"] == "enter"
        assert strat._entry_ts == 12345.0
    finally:
        bt.close()


# ═══════════════════════════════════════════════════════════════════
# iter-5 T2: friction-aware hard-stop
# ═══════════════════════════════════════════════════════════════════

def test_hard_stop_friction_aware_threshold() -> None:
    """Pin the new boundary: with S3_FRICTION_BPS_PER_LEG=5.5 and
    S3_HARD_STOP_BPS=-30.0, the hard-stop fires when
    `mtm_bps - 2 * 5.5 < -30`, i.e. when raw MTM < -19 bps (strict).

    - raw -19 bps -> projected -30 bps: NOT fire (strict `<` boundary).
    - raw -20 bps -> projected -31 bps: FIRES.
    - raw -18 bps -> projected -29 bps: NOT fire.
    """
    strat = Strategy3PreSettlement()
    strat._in_trade = True
    strat._entry_price = 100.0
    strat._entry_direction = 1
    strat._entry_ts = 1_000.0
    strat._settlement_ts = 5_000.0

    _cfg.S3_HARD_STOP_ENABLED = True
    _cfg.S3_FRICTION_BPS_PER_LEG = 5.5
    _cfg.S3_HARD_STOP_BPS = -30.0

    # Exactly at the floor: projected = -30 bps. Strict `<` -> NOT fire.
    r_boundary = strat._check_exit(
        seconds_to_settlement=500.0, pressure=0.0005, now=1_001.0, price=99.81
    )
    assert r_boundary != "hard_stop_loss"

    # Just below: projected = -31 bps -> FIRES.
    r_below = strat._check_exit(
        seconds_to_settlement=500.0, pressure=0.0005, now=1_001.0, price=99.80
    )
    assert r_below == "hard_stop_loss"

    # Just above: projected = -29 bps -> NOT fire.
    r_above = strat._check_exit(
        seconds_to_settlement=500.0, pressure=0.0005, now=1_001.0, price=99.82
    )
    assert r_above != "hard_stop_loss"


def test_hard_stop_friction_config_overridable() -> None:
    """Setting S3_FRICTION_BPS_PER_LEG=0 collapses the projection to raw
    MTM (iter-4 behavior). Confirms the config knob actually controls
    the threshold and the math is wired correctly.
    """
    strat = Strategy3PreSettlement()
    strat._in_trade = True
    strat._entry_price = 100.0
    strat._entry_direction = 1
    strat._entry_ts = 1_000.0
    strat._settlement_ts = 5_000.0

    _cfg.S3_HARD_STOP_ENABLED = True
    _cfg.S3_FRICTION_BPS_PER_LEG = 0.0
    _cfg.S3_HARD_STOP_BPS = -30.0

    # raw -29 bps -> projected -29 bps: NOT fire.
    r_above = strat._check_exit(
        seconds_to_settlement=500.0, pressure=0.0005, now=1_001.0, price=99.71
    )
    assert r_above != "hard_stop_loss"

    # raw -31 bps -> projected -31 bps: FIRES.
    r_below = strat._check_exit(
        seconds_to_settlement=500.0, pressure=0.0005, now=1_001.0, price=99.69
    )
    assert r_below == "hard_stop_loss"
