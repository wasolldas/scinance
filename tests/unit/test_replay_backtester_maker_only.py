"""
Tests for iter-4 Push A T3: opt-in S2 maker-only fee model.

The flag ``config.S2_MAKER_ONLY`` (default False) zeros both S2 trade
legs' fees inside ``ReplayBacktester._make_trade``. S3 (and every other
strategy) is unaffected. Default off -> bit-identical to iter-3.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from bybit_edge import config as _cfg
from bybit_edge.replay_backtester import ReplayBacktester


@pytest.fixture(autouse=True)
def _reset_maker_only_flag():
    saved = _cfg.S2_MAKER_ONLY
    _cfg.S2_MAKER_ONLY = False
    yield
    _cfg.S2_MAKER_ONLY = saved


@pytest.fixture()
def bt() -> ReplayBacktester:
    return ReplayBacktester(symbol="BTCUSDT", db_path=Path(":memory:"))


def _trade(bt: ReplayBacktester, *, strategy_id: str):
    """Build a synthetic round-trip Long trade @ 100 -> 101."""
    return bt._make_trade(
        side="Long",
        entry_price=100.0,
        entry_ts=1_000,
        exit_price=101.0,
        exit_ts=2_000,
        strategy_id=strategy_id,
    )


def test_s2_maker_only_zero_fees(bt: ReplayBacktester) -> None:
    """S2 with maker-only flag: both fees are 0.0; pnl == raw_pnl."""
    _cfg.S2_MAKER_ONLY = True
    t = _trade(bt, strategy_id="S2")
    assert t.entry_fee == 0.0
    assert t.exit_fee == 0.0
    assert t.pnl == pytest.approx(t.raw_pnl)
    bt.close()


def test_s3_unaffected_by_s2_maker_only(bt: ReplayBacktester) -> None:
    """S3 with maker-only flag: still taker fees; fee identity holds."""
    _cfg.S2_MAKER_ONLY = True
    t = _trade(bt, strategy_id="S3")
    assert t.entry_fee > 0
    assert t.exit_fee > 0
    assert abs(t.pnl - (t.raw_pnl - t.entry_fee - t.exit_fee)) < 1e-9
    bt.close()


def test_maker_only_off_matches_baseline(bt: ReplayBacktester) -> None:
    """Flag off: both S2 and S3 produce taker fees identical to a
    hard-coded baseline snapshot. This is the explicit bit-identity
    guard required by the briefing for T3."""
    # Flag is False (fixture default).
    t_s2 = _trade(bt, strategy_id="S2")
    t_s3 = _trade(bt, strategy_id="S3")

    # Hard-coded snapshot. Engine defaults: slippage 2.0 bps, taker fee
    # 0.00055 (0.055%). Long entry at 100.0:
    #   slip_entry = 100.0 * (1 + 2e-4) = 100.02
    #   entry_fee  = 100.02 * 0.00055   = 0.055011
    # Short exit at 101.0:
    #   slip_exit  = 101.0 * (1 - 2e-4) = 100.9798
    #   exit_fee   = 100.9798 * 0.00055 = 0.05553889
    # Same for S3 because the flag is OFF -> both strategies are taker.
    expected_entry_fee = 100.02 * 0.00055
    expected_exit_fee = (101.0 * (1 - 2e-4)) * 0.00055

    assert t_s2.entry_fee == pytest.approx(expected_entry_fee, abs=1e-9)
    assert t_s2.exit_fee == pytest.approx(expected_exit_fee, abs=1e-9)
    assert t_s3.entry_fee == pytest.approx(expected_entry_fee, abs=1e-9)
    assert t_s3.exit_fee == pytest.approx(expected_exit_fee, abs=1e-9)
    bt.close()


@pytest.mark.parametrize(
    "s2_maker_only,strategy_id",
    [
        (False, "S2"),
        (False, "S3"),
        (True, "S2"),
        (True, "S3"),
    ],
)
def test_fee_identity_holds_across_flag_states(
    bt: ReplayBacktester, s2_maker_only: bool, strategy_id: str
) -> None:
    """pnl == raw_pnl - entry_fee - exit_fee in all four flag-state x
    strategy combinations, to 1e-9."""
    _cfg.S2_MAKER_ONLY = s2_maker_only
    t = _trade(bt, strategy_id=strategy_id)
    assert not math.isnan(t.pnl)
    assert not math.isnan(t.raw_pnl)
    assert abs(t.pnl - (t.raw_pnl - t.entry_fee - t.exit_fee)) < 1e-9
    bt.close()
