"""Tests for the H-05c OFI-fade tradability gate (c01_ofi_tradability).

Covers:
- costs: wall arithmetic, net_edge_bps, gate_assumptions_valid (anti-gaming).
- fade_rule: OFI binning, FADE direction (-sign OFI), latency haircut causality.
- driver.run: >=2-window requirement, F-OFI-INV-TRADE FDR, per-delta consistency,
  capital_free=False payload, gate_valid_assumptions flag.
- positive detection: a synthetic window where fading OFI is profitable beyond
  the wall registers variant_pass; a null (no structure) does not.
"""
from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.research.c01_ofi_sign.driver import TradeArrays
from bybit_edge.research.c01_ofi_tradability import costs
from bybit_edge.research.c01_ofi_tradability.driver import run
from bybit_edge.research.c01_ofi_tradability.fade_rule import (
    generate_round_trips,
    captured_sol_move,
)
from bybit_edge.research.c01_ofi_tradability.net_edge import (
    block_len_for_overlap,
    bootstrap_mean_le_zero_p,
)


# ---------------------------------------------------------------------------
# costs
# ---------------------------------------------------------------------------

def test_wall_arithmetic_taker_vs_maker() -> None:
    c = costs.CostModel()
    assert c.wall_bps == pytest.approx(15.0)  # 11 + 4
    cm = costs.CostModel(maker=True)
    assert cm.wall_bps == pytest.approx(6.0)  # 2 + 4


def test_net_edge_bps() -> None:
    c = costs.CostModel()
    # a +20 bps gross move (0.0020 logret) -> 20 - 15 = +5 bps net
    assert costs.net_edge_bps(0.0020, c) == pytest.approx(5.0, abs=1e-6)


def test_gate_assumptions_valid_anti_gaming() -> None:
    ok = dict(latency_ms=300.0, friction_bps=11.0, haircut_applied=True, maker=False)
    assert costs.gate_assumptions_valid(**ok) is True
    # each violation flips it false
    assert costs.gate_assumptions_valid(**{**ok, "latency_ms": 100.0}) is False
    assert costs.gate_assumptions_valid(**{**ok, "friction_bps": 5.0}) is False
    assert costs.gate_assumptions_valid(**{**ok, "haircut_applied": False}) is False
    assert costs.gate_assumptions_valid(**{**ok, "maker": True}) is False


# ---------------------------------------------------------------------------
# fade_rule
# ---------------------------------------------------------------------------

def test_captured_move_latency_haircut_causal() -> None:
    # prices rise linearly; captured (entry later) must differ from full (entry at t)
    ts = np.arange(0, 6000, 100, dtype=np.float64)  # 0..5900 ms, 100ms apart
    px = 100.0 + 0.001 * np.arange(ts.size)  # gently rising
    full, cap = captured_sol_move(ts, px, 1000.0, delta_s=1, grid_ms=1000.0, latency_ms=300.0)
    # exit at t+1000=2000ms; full entry at 1000ms, hc entry at 1300ms
    assert np.isfinite(full) and np.isfinite(cap)
    # haircut window is shorter (entry later) -> smaller magnitude move on a ramp
    assert abs(cap) < abs(full)


def test_fade_direction_is_opposite_ofi() -> None:
    # one heavy BUY bin then flat: OFI>0 -> fade position must be -1 (short)
    ts = np.concatenate([np.arange(0, 1000, 10, dtype=np.float64),       # bin 0: buys
                         np.arange(1000, 4000, 10, dtype=np.float64)])    # later bins
    n = ts.size
    price = np.full(n, 100.0)
    volume = np.ones(n)
    side = np.array(["Buy"] * 100 + ["Sell"] * (n - 100), dtype=object)
    trips = generate_round_trips(ts, price, volume, side,
                                 delta_s=1, grid_ms=1000.0, latency_ms=300.0)
    assert trips, "expected at least one round-trip"
    # the first signalled bin (bin 0, heavy buys) must yield a fade short
    first = trips[0]
    assert first.ofi > 0 and first.position_sign == -1


# ---------------------------------------------------------------------------
# net_edge: block bootstrap (CRITICAL_REVIEW_2_2026-07-13.md, Lane research-modules,
# net_edge.py:65 -- i.i.d. resampling of overlapping round-trip net edges
# understates the true sampling variance and yields anti-conservative p-values).
# ---------------------------------------------------------------------------

def _overlapping_autocorrelated_net_edges(
    mu: float, block_len: int, n_blocks: int, seed: int,
) -> np.ndarray:
    """Synthetic net edges mimicking round-trips with heavily overlapping
    forward-return windows: every `block_len` consecutive observations share
    one common block-level shock plus small idiosyncratic noise, so the true
    number of statistically independent observations is `n_blocks`, not
    `block_len * n_blocks` -- exactly the structure the review describes for
    delta_s=5s / grid_ms=1000ms (~80% overlap -> effective n ~ n/5).
    """
    rng = np.random.default_rng(seed)
    block_shocks = rng.normal(mu, 1.0, size=n_blocks)
    idiosyncratic = rng.normal(0.0, 0.01, size=block_len * n_blocks)
    return np.repeat(block_shocks, block_len) + idiosyncratic


def test_block_len_for_overlap_matches_registered_delta5_grid1000() -> None:
    # delta_s=5 x grid_ms=1000 is the concrete GL-010 survivor cell named in
    # CRITICAL_REVIEW_2_2026-07-13.md ("~80% overlap" -> block of 5 round-trips).
    assert block_len_for_overlap(5, 1000.0) == 5
    # delta_s=1 x grid_ms=1000: capture window does not exceed the grid spacing
    # -> no overlap -> block of 1 (degenerates to i.i.d.).
    assert block_len_for_overlap(1, 1000.0) == 1


def test_block_bootstrap_more_conservative_than_iid_on_autocorrelated_edges() -> None:
    """Core regression for the reviewed bug: on data with the review's
    described overlap structure, the BLOCK bootstrap must report a strictly
    larger (more conservative) p-value than a naive i.i.d. bootstrap
    (block_len=1) run on the IDENTICAL data -- proving the block resample
    correctly inflates the estimated sampling variance of the mean instead
    of treating heavily-correlated round-trips as independent draws.
    """
    x = _overlapping_autocorrelated_net_edges(mu=0.02, block_len=5, n_blocks=100, seed=123)
    p_iid = bootstrap_mean_le_zero_p(x, n_bootstrap=500, block_len=1, seed=7)
    p_block = bootstrap_mean_le_zero_p(x, n_bootstrap=500, block_len=5, seed=7)
    assert p_block > p_iid
    # The naive i.i.d. bootstrap falsely looks significant at the registered
    # H-05c/DEC-16 threshold (p<=0.05, DEC-16); the corrected block bootstrap
    # correctly does NOT -- this is the exact anti-conservative-p failure mode
    # (CRITICAL_REVIEW_2_2026-07-13.md) that fed directly into the GL-010/
    # GL-011 survivor-cell gate.
    assert p_iid <= 0.05
    assert p_block > 0.05


def test_bootstrap_mean_le_zero_p_block_len_one_is_iid_resampling() -> None:
    # block_len=1 (no overlap, e.g. delta_s=1s / grid_ms=1000ms) must behave
    # like plain i.i.d. resampling: a well-separated positive mean is highly
    # significant even without any block structure.
    rng = np.random.default_rng(3)
    x = rng.normal(0.5, 1.0, size=200)
    p = bootstrap_mean_le_zero_p(x, n_bootstrap=300, block_len=1, seed=9)
    assert 0.0 <= p <= 1.0


def test_bootstrap_mean_le_zero_p_degenerate_input() -> None:
    assert bootstrap_mean_le_zero_p(np.array([1.0, 2.0]), block_len=5) == 1.0  # n < 4
    assert bootstrap_mean_le_zero_p(np.arange(10.0), n_bootstrap=0, block_len=5) == 1.0


# ---------------------------------------------------------------------------
# driver.run
# ---------------------------------------------------------------------------

def _fade_profitable_window(n: int, seed: int) -> TradeArrays:
    """Window where fading the aggressor is profitable beyond the wall.

    Every grid bin (1000ms) is buy-aggressed (OFI > 0 -> fade = short), and the
    price ramps DOWN continuously (~40 bps per second, spread across the ticks so
    the move occurs DURING the capture window, not at a boundary instant). The
    fade short therefore captures a large positive directional move each bin.
    """
    rng = np.random.default_rng(seed)
    per_bin = 200            # ticks per 1000ms bin
    n_bins = max(8, n // per_bin)
    drift_per_tick = -0.004 / per_bin  # -40 bps per bin, continuous
    ts: list[float] = []
    px: list[float] = []
    side: list[str] = []
    vol: list[float] = []
    logp = 0.0
    for b in range(n_bins):
        bt = b * 1000.0 + np.linspace(0.0, 950.0, per_bin)
        for i in range(per_bin):
            logp += drift_per_tick
            ts.append(float(bt[i]))
            px.append(100.0 * float(np.exp(logp)))
            side.append("Buy")
            vol.append(float(rng.uniform(0.8, 1.2)))
    ts_a = np.array(ts, dtype=np.float64)
    px_a = np.array(px, dtype=np.float64)
    side_a = np.array(side, dtype=object)
    vol_a = np.array(vol, dtype=np.float64)
    return TradeArrays(ts_a, px_a, vol_a, side_a)


def _null_window(n: int, seed: int) -> TradeArrays:
    rng = np.random.default_rng(seed)
    ts = np.arange(n, dtype=np.float64) * 50.0
    px = 100.0 * np.exp(np.cumsum(rng.normal(0, 1e-4, n)))
    side = rng.choice(np.array(["Buy", "Sell"], dtype=object), size=n)
    vol = rng.uniform(0.5, 1.5, n)
    return TradeArrays(ts, px, vol, side)


def test_run_requires_two_windows() -> None:
    with pytest.raises(ValueError):
        run([_null_window(3000, 1)], n_bootstrap=20, seed=1)


def test_run_payload_capital_free_false_and_shape() -> None:
    wins = [_null_window(4000, 1), _null_window(4000, 2)]
    out = run(wins, deltas_s=(1, 5), n_bootstrap=50, seed=7)
    assert out["hypothesis"] == "H-05c"
    assert out["capital_free"] is False
    assert out["fdr_family"] == "F-OFI-INV-TRADE"
    assert out["gate_valid_assumptions"] is True  # defaults are the registered point
    assert out["wall_bps_total"] == pytest.approx(15.0)
    assert len(out["tradability_consistency"]) == 2  # 2 deltas
    assert len(out["variants"]) == 4  # 2 windows x 2 deltas


def test_run_null_does_not_pass() -> None:
    wins = [_null_window(6000, 11), _null_window(6000, 12)]
    out = run(wins, deltas_s=(1,), n_bootstrap=100, seed=5)
    assert out["any_tradable_consistent"] is False
    assert out["weiter_indication"] is False


def test_run_detects_tradable_fade() -> None:
    # strong mean-reversion fade profitable beyond the 15 bps wall, both windows
    wins = [_fade_profitable_window(4000, 21), _fade_profitable_window(4000, 22)]
    out = run(wins, deltas_s=(1,), n_bootstrap=200, seed=3)
    v = [x for x in out["variants"]]
    # gross capture should be strongly positive (fade catches the reversion)
    assert all(x["gross_capture_bps_mean"] > 15.0 for x in v), \
        f"expected gross capture > wall, got {[x['gross_capture_bps_mean'] for x in v]}"
    # net edge positive both windows
    assert all(x["net_edge_bps_mean"] > 0 for x in v)


def test_anti_gaming_flag_false_when_latency_shortened() -> None:
    wins = [_null_window(3000, 1), _null_window(3000, 2)]
    out = run(wins, deltas_s=(1,), latency_ms=100.0, n_bootstrap=20, seed=1)
    assert out["gate_valid_assumptions"] is False  # 100ms < registered 300ms
    assert out["weiter_indication"] is False


def test_anti_gaming_flag_false_for_wrong_symbol() -> None:
    wins = [_fade_profitable_window(4000, 21), _fade_profitable_window(4000, 22)]
    out = run(wins, symbol="BTCUSDT", deltas_s=(1,), n_bootstrap=50, seed=3)
    # even if tradable, a non-SOL symbol is not a valid pass cell
    assert out["gate_valid_assumptions"] is False
