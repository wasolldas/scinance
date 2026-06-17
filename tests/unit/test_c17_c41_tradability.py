"""H-04b-VERIFY (T0, SANDBOX) — tests for the C-17/C-41 tradability module.

Covers ``src/bybit_edge/research/c17_c41_tradability/`` (H-04b, registry:
``scinance2-impl/state/hypothesis_registry.md`` Z.118-139; design DEC-13). H-04b
is the FIRST NON-KAPITALFREI hypothesis (``capital_free=false``): it confronts the
binding 11 bps round-trip Taker friction wall AND a 300 ms latency haircut on the
H-04 (GL-006) directed BTC->ETH lead-lag signal, and asks whether the predicted
ETH move carries a NET edge per round-trip that is > 0 AND statistically > 0
(bootstrap p <= 0.05 after BH-FDR alpha=0.10 over F-LEADLAG-TRADE) on >= 2 disjoint
windows. It remains a historical backtest with a cost model — NO live orders, NO
real capital (CLAUDE.md §4 / Autonomie-Protokoll §3). The PRD-§4 a-priori expects
PARK ("abgegraste 30-60s-HFT-Anomalie"); a WEITER must be hard and honest.

1. Latency haircut correct + causal (MOST IMPORTANT): a constructed coupled
   series — an ETH move injected BEFORE ``t+latenz`` is removed by the haircut
   (captured ~ 0); a move injected AFTER ``t+latenz`` is fully captured. Sub-bar
   precision: a 300 ms latency on a 1000 ms grid cuts at exactly t+300 (last
   trade at-or-before), NOT rounded to a bar edge. No-lookahead: the capture
   reads only trades at-or-before the boundary ts, so mutating a FUTURE trade
   never changes the capture for earlier ``t``.
2. PARK control: lead exists but captured move after haircut < wall -> net edge
   <= 0 -> weiter_indication = False (the PRD-expected outcome).
3. Tradable detection: a move large enough that after 300 ms + 11 bps + 4 bps a
   positive remainder survives -> net > 0, bootstrap p < 0.05, passes in >= 2
   windows. Proves the module CAN detect a WEITER (the gate is not rigged to PARK).
4. Anti-gaming (CRITICAL, registry H-04b Z.132): the same PARK case with
   latency < 300 OR friction < 11 OR the haircut dropped makes net NUMERICALLY
   positive, BUT gate_valid_assumptions = False AND weiter_indication = False are
   FORCED. A WEITER is IMPOSSIBLE under invalid assumptions. Parametrised over the
   three gaming vectors + the marked Maker secondary case.
5. signal-eps is no backdoor: the default pass verdict is anchored at eps = 0.0;
   varying eps away from 0.0 is robustness only — it cannot secretly flip the
   registered verdict in the favourable direction (it can only drop trades).
6. Friction arithmetic exact: net_edge_bps = brutto_capture - 11 - 4 (hand
   computed); the Maker secondary case uses 2 bps friction + sets
   gate_valid_assumptions = false + carries the adverse-selection caveat.
7. Bootstrap-p + BH-FDR: a constructed net-edge distribution -> exact p; BH over
   the F-LEADLAG-TRADE lag family -> hand-computed rejection set.
8. Window disjointness (half-open, imported from c17_c41_lead_lag) + determinism
   (same seed -> identical JSON).
9. Driver E2E: a mini pair-CSV -> JSON + MD with the H-04b reference,
   ``capital_free: false``, every field per window/lag (brutto,
   latenz_haircut_applied, friction_bps, slippage_bps, net_edge_bps, bootstrap_p,
   fdr_sig, gate_valid_assumptions, maker_secondary), and NO overall verdict.

Runtime budget: bootstrap-N is small (50) — the tradable variant's smallest p is
1/(N+1) ~ 0.0196 < the BH rank-1 threshold for the small lag family, so the
genuine WEITER survives FDR while the suite stays fast. Seeds are fixed;
everything is T0/SANDBOX. The binding H-04b run on real ticks is T3 (handoff_local).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

import scripts.c17_c41_tradability as c17b_cli
from bybit_edge.research.c17_c41_tradability import (
    FRICTION_WALL_BPS,
    LATENCY_MS,
    MAKER_WALL_BPS,
    SLIPPAGE_BPS,
    CostModel,
    benjamini_hochberg,
    bootstrap_mean_le_zero_p,
    captured_eth_move,
    gate_assumptions_valid,
    net_edge_bps,
    run,
)
# The half-open deterministic window splitter is REUSED from the kapitalfreie
# H-04 library by H-04b (registry Z.139 / DEC-13 code-bedarf-vermerk). Importing
# it here proves the reuse contract (not a re-implementation in c17_c41_tradability).
from bybit_edge.research.c17_c41_lead_lag import split_pair_windows

T0_MS = 1_700_000_000_000.0  # fixed epoch anchor for all synthetic timelines
GRID_MS = 1000.0
LATENCY = 300.0  # registered default latency haircut (DEC-13c)
WALL_BPS = FRICTION_WALL_BPS + SLIPPAGE_BPS  # 11 + 4 = 15 bps round-trip Taker


# ===========================================================================
# Synthetic fixtures
# ===========================================================================
#
# The trading rule places signal times on a grid raster; for a signal at
# ``t = T0 + (k+1)*grid`` the BTC signal is the BTC log-return over
# ``[t-grid, t]`` and the capture window is ``[t+latency, t+(lag+horizon)*grid]``
# (= ``[t+300, t+2000]`` for lag=horizon=1). To get a deterministic, controllable
# captured move we drive ETH with a STEADY per-bar trend whose direction matches
# a steady BTC trend (so the position sign is stable and every capture window
# realises a known directional move), and we place the move tick either AFTER
# (``move_after_latency=True``) or BEFORE the 300 ms boundary.


def _trend_pair(
    per_bar_bps: float,
    *,
    move_after_latency: bool = True,
    n_bars: int = 420,
) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    """BTC steady-up trend (stable +1 signal) + ETH steady-up trend coupled to it.

    Each bar's ETH move is ``per_bar_bps`` placed at ``t+400`` (after the 300 ms
    haircut) or ``t+100`` (before it). One pre-move anchor tick sits at ``t+250``
    (<= 300 ms boundary) so the haircut ENTRY price is the pre-move price.
    """
    btc_ret = np.full(n_bars, 0.005)  # steady up -> BTC signal is +1 every bar
    btc_px = 50_000.0 * np.exp(np.concatenate([[0.0], np.cumsum(btc_ret)]))
    btc_ts = T0_MS + np.arange(n_bars + 1) * GRID_MS  # ticks at bar edges
    mag = per_bar_bps * 1e-4
    move_at = 400.0 if move_after_latency else 100.0
    eth_ts: list[float] = [T0_MS - 1.0]
    eth_px: list[float] = [3_000.0]
    cur = 3_000.0
    for k in range(n_bars - 2):
        t = T0_MS + (k + 1) * GRID_MS
        eth_ts.append(t + 250.0)  # entry-boundary anchor (<= 300 ms): pre-move px
        eth_px.append(cur)
        cur = cur * np.exp(mag)
        eth_ts.append(t + move_at)  # the directional move tick
        eth_px.append(cur)
    return (btc_ts, btc_px), (np.array(eth_ts), np.array(eth_px))


def _best_variant(payload: dict) -> dict:
    return payload["windows"][0]["variants"][0]


# ===========================================================================
# 1. Latency haircut correct + causal (MOST IMPORTANT) — unit-level on the rule
# ===========================================================================

def test_latency_haircut_removes_move_before_boundary() -> None:
    """An ETH move BEFORE ``t+latency`` is removed by the haircut (captured ~ 0).

    The full (no-haircut) move is reported for diagnostics and is non-zero, but
    the captured move — the ONLY tradable part — is ~ 0 because the entry price at
    ``t+300`` already sits AFTER the jump. This is the crux of the registry Z.128
    haircut: ``[t+latenz, t+lag+horizon]`` not ``[t, ...]``.
    """
    t = T0_MS + 5_000.0
    # ETH jumps 100 -> 110 at t+100 (BEFORE t+300), then flat.
    ts = np.array([t - 1_000, t, t + 100, t + 400, t + 2_000, t + 3_000])
    px = np.array([100.0, 100.0, 110.0, 110.0, 110.0, 110.0])
    full, captured = captured_eth_move(
        ts, px, t, lag=1, horizon=1, grid_ms=GRID_MS, latency_ms=LATENCY
    )
    assert full == pytest.approx(np.log(1.1), rel=1e-9), "full move should see the jump"
    assert captured == pytest.approx(0.0, abs=1e-12), (
        "haircut must REMOVE a move that happens before t+latency"
    )


def test_latency_haircut_keeps_move_after_boundary() -> None:
    """An ETH move AFTER ``t+latency`` is fully captured (captured ~ injected)."""
    t = T0_MS + 5_000.0
    # ETH jumps 100 -> 110 at t+400 (AFTER t+300).
    ts = np.array([t - 1_000, t, t + 100, t + 400, t + 2_000, t + 3_000])
    px = np.array([100.0, 100.0, 100.0, 110.0, 110.0, 110.0])
    full, captured = captured_eth_move(
        ts, px, t, lag=1, horizon=1, grid_ms=GRID_MS, latency_ms=LATENCY
    )
    assert full == pytest.approx(np.log(1.1), rel=1e-9)
    assert captured == pytest.approx(np.log(1.1), rel=1e-9), (
        "a move after t+latency must survive the haircut"
    )


def test_latency_haircut_subbar_precise_not_bar_rounded() -> None:
    """300 ms latency on a 1000 ms grid cuts at exactly t+300, NOT at a bar edge.

    The entry boundary ``t+300`` reads the last trade at-or-before 300 ms (the
    ``t+200`` tick at 100). If the haircut were silently bar-ROUNDED to t+1000 it
    would instead read the ``t+500`` tick (108), giving a much smaller capture —
    which the anti-gaming clause forbids. We assert the sub-bar value.
    """
    t = T0_MS + 5_000.0
    ts = np.array([t - 1_000, t, t + 200, t + 500, t + 2_000])
    px = np.array([100.0, 100.0, 100.0, 108.0, 112.0])
    _, captured = captured_eth_move(
        ts, px, t, lag=1, horizon=1, grid_ms=GRID_MS, latency_ms=LATENCY
    )
    # Sub-bar: entry at t+300 reads the t+200 price (100) -> capture log(112/100).
    assert captured == pytest.approx(np.log(112 / 100), rel=1e-9)
    # Bar-rounded-to-t+1000 would read the t+500 price (108) -> log(112/108).
    assert captured != pytest.approx(np.log(112 / 108), rel=1e-3), (
        "haircut must NOT be bar-rounded (would silently weaken the wall)"
    )


def test_latency_haircut_no_lookahead_future_trade_inert() -> None:
    """No-lookahead: the capture reads only trades at-or-before the boundary ts.

    Mutating a FUTURE trade (strictly after the unwind boundary ``t+2000``) must
    NOT change the captured move for the earlier signal ``t`` — the rule is
    strictly backward-looking (searchsorted side='right' - 1).
    """
    t = T0_MS + 5_000.0
    ts = np.array([t - 1_000, t, t + 400, t + 2_000, t + 3_000, t + 5_000])
    px = np.array([100.0, 100.0, 105.0, 110.0, 110.0, 110.0])
    _, cap0 = captured_eth_move(
        ts, px, t, lag=1, horizon=1, grid_ms=GRID_MS, latency_ms=LATENCY
    )
    px_mut = px.copy()
    px_mut[-1] = 999.0  # tick at t+5000 (>> t+2000)
    px_mut[-2] = 555.0  # tick at t+3000 (> t+2000)
    _, cap1 = captured_eth_move(
        ts, px_mut, t, lag=1, horizon=1, grid_ms=GRID_MS, latency_ms=LATENCY
    )
    assert cap1 == cap0, "a future trade mutation leaked into an earlier capture"


# ===========================================================================
# 2. PARK control — lead exists but captured < wall -> no WEITER (PRD-expected)
# ===========================================================================

def test_park_lead_exists_but_below_wall() -> None:
    """A genuine (correctly signed) lead whose captured move stays UNDER the wall
    -> net edge <= 0 -> weiter_indication = False. This is the PRD-§4 a-priori
    expected outcome (abgegraste HFT-Anomalie)."""
    pair_btc, pair_eth = _trend_pair(3.0, move_after_latency=True)
    payload = run(
        pair_btc, pair_eth, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, lags=(1,), grid_ms=GRID_MS, n_bootstrap=50, seed=42,
    )
    assert payload["gate_valid_assumptions"] is True, "registered point IS valid"
    assert payload["weiter_indication"] is False, "below-wall lead must NOT pass"
    for w in payload["windows"]:
        v = w["variants"][0]
        # The lead is real: a positive directional brutto-capture exists ...
        assert v["gross_capture_bps_mean"] > 0.0
        # ... but it is below the 15 bps wall -> net edge negative -> no pass.
        assert v["net_edge_bps_mean"] <= 0.0
        assert v["passed_global"] is False


# ===========================================================================
# 3. Tradable detection — module CAN report a WEITER (gate is not rigged to PARK)
# ===========================================================================

def test_tradable_detection_positive_net_edge_passes() -> None:
    """A 30 bps move (after 300 ms + 11 + 4 bps a +15 bps remainder survives) ->
    net > 0, bootstrap p < 0.05, passes in >= 2 windows -> weiter_indication True.

    Proves the gate can detect a genuine WEITER (so the PARK in test 2 is an
    honest negative, not a rigged one)."""
    pair_btc, pair_eth = _trend_pair(30.0, move_after_latency=True)
    payload = run(
        pair_btc, pair_eth, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, lags=(1,), grid_ms=GRID_MS, n_bootstrap=50, seed=42,
    )
    assert payload["gate_valid_assumptions"] is True
    assert payload["n_windows"] >= 2
    assert all(payload["per_window_pass"]), "tradable signal must pass in BOTH windows"
    assert payload["weiter_indication"] is True
    for w in payload["windows"]:
        v = w["variants"][0]
        assert v["net_edge_bps_mean"] > 0.0
        assert v["bootstrap_p"] <= 0.05
        assert v["fdr_significant_global"] is True
        assert v["passed_global"] is True


# ===========================================================================
# 4. Anti-gaming (CRITICAL) — a WEITER is IMPOSSIBLE under invalid assumptions
# ===========================================================================

# A PARK fixture whose net edge is NEGATIVE at the registered 300 ms / 11 bps
# point but turns NUMERICALLY POSITIVE the moment a gaming vector is applied
# (12 bps capture: -3 bps net at the wall, but > 0 once the wall/latency is
# weakened). Each gaming vector must FORCE gate_valid_assumptions=false AND
# weiter_indication=false despite the numerically positive, FDR-significant net.
@pytest.mark.parametrize(
    "kwargs, vector",
    [
        ({"latency_ms": 0.0}, "latency<300"),
        ({"latency_ms": 100.0}, "latency<300"),
        ({"friction_bps": 0.0}, "wall<11"),
        ({"friction_bps": 5.0}, "wall<11"),
        ({"maker_secondary": True}, "maker (drops haircut-valid + 2bps wall)"),
    ],
)
def test_anti_gaming_invalid_assumptions_cannot_produce_weiter(
    kwargs: dict, vector: str
) -> None:
    """The same PARK case + a gaming vector -> net flips positive, BUT
    gate_valid_assumptions=False AND weiter_indication=False are forced.

    A WEITER under invalid assumptions is IMPOSSIBLE (registry H-04b Z.132 — a
    different latency/wall is a NEW hypothesis H-04c, not a goalpost shift)."""
    pair_btc, pair_eth = _trend_pair(12.0, move_after_latency=True)
    base = run(
        pair_btc, pair_eth, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, lags=(1,), grid_ms=GRID_MS, n_bootstrap=50, seed=42,
    )
    # Sanity: at the registered point this case is an honest PARK.
    assert base["gate_valid_assumptions"] is True
    assert base["weiter_indication"] is False
    assert _best_variant(base)["net_edge_bps_mean"] <= 0.0

    gamed = run(
        pair_btc, pair_eth, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, lags=(1,), grid_ms=GRID_MS, n_bootstrap=50, seed=42,
        **kwargs,
    )
    v = _best_variant(gamed)
    # The gaming made the per-variant net numerically positive and significant ...
    assert v["net_edge_bps_mean"] > 0.0, (
        f"vector {vector!r} should push net positive (else not a real gaming test)"
    )
    assert v["passed_global"] is True
    # ... yet the gate verdict is hard-blocked: invalid assumptions -> NO WEITER.
    assert gamed["gate_valid_assumptions"] is False, (
        f"gaming vector {vector!r} must set gate_valid_assumptions=false"
    )
    assert gamed["weiter_indication"] is False, (
        f"a WEITER under invalid assumptions ({vector!r}) is FORBIDDEN (Z.132)"
    )


def test_anti_gaming_validity_check_unit() -> None:
    """The validity predicate itself: True ONLY at latency>=300 AND friction>=11
    AND haircut applied AND Taker (the three gaming vectors + maker each break it)."""
    assert gate_assumptions_valid(
        latency_ms=300.0, friction_bps=11.0, haircut_applied=True, maker=False
    ) is True
    # vector (b) latency < 300
    assert gate_assumptions_valid(
        latency_ms=100.0, friction_bps=11.0, haircut_applied=True, maker=False
    ) is False
    # vector (a) friction < 11
    assert gate_assumptions_valid(
        latency_ms=300.0, friction_bps=5.0, haircut_applied=True, maker=False
    ) is False
    # vector (c) haircut dropped (measured over [t, ...] not [t+latenz, ...])
    assert gate_assumptions_valid(
        latency_ms=300.0, friction_bps=11.0, haircut_applied=False, maker=False
    ) is False
    # maker secondary is never a primary pass
    assert gate_assumptions_valid(
        latency_ms=300.0, friction_bps=11.0, haircut_applied=True, maker=True
    ) is False


# ===========================================================================
# 5. signal-eps is no backdoor — registered verdict anchored at eps = 0.0
# ===========================================================================

def test_signal_eps_default_is_zero_and_anchors_verdict() -> None:
    """The default ``signal_eps`` is 0.0 (registry-wörtlich "jedes nicht-flache
    Signal"); the registered pass verdict is read at this point."""
    pair_btc, pair_eth = _trend_pair(30.0, move_after_latency=True)
    payload = run(
        pair_btc, pair_eth, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, lags=(1,), grid_ms=GRID_MS, n_bootstrap=50, seed=42,
    )
    assert payload["signal_eps"] == 0.0
    assert payload["weiter_indication"] is True  # the registered eps=0.0 verdict


def test_signal_eps_variation_does_not_secretly_flip_verdict() -> None:
    """Varying signal-eps away from 0.0 is robustness only — it can only make the
    rule MORE conservative (fewer trades), never secretly manufacture a WEITER.

    A tiny eps below the signal magnitude leaves the verdict unchanged; a huge eps
    drops every trade (0 round-trips -> no pass). In neither direction does the
    eps sweep flip the registered eps=0.0 verdict in the favourable direction."""
    pair_btc, pair_eth = _trend_pair(30.0, move_after_latency=True)
    base = run(
        pair_btc, pair_eth, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, lags=(1,), grid_ms=GRID_MS, n_bootstrap=50, seed=42,
    )
    assert base["weiter_indication"] is True

    # eps below the signal magnitude (0.005): trades unchanged -> same verdict.
    small = run(
        pair_btc, pair_eth, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, lags=(1,), grid_ms=GRID_MS, n_bootstrap=50, seed=42,
        signal_eps=0.001,
    )
    assert small["weiter_indication"] is True
    assert small["signal_eps"] == 0.001

    # huge eps: every trade dropped -> 0 round-trips -> conservative non-pass.
    killed = run(
        pair_btc, pair_eth, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, lags=(1,), grid_ms=GRID_MS, n_bootstrap=50, seed=42,
        signal_eps=1.0,
    )
    assert killed["weiter_indication"] is False
    assert _best_variant(killed)["n_trips"] == 0


# ===========================================================================
# 6. Friction arithmetic exact (hand computed) + Maker secondary case
# ===========================================================================

def test_net_edge_arithmetic_exact_taker() -> None:
    """net_edge_bps = brutto_capture_bps - 11 (friction) - 4 (slippage).

    A captured log-move of 0.0030 = 30 bps -> net = 30 - 11 - 4 = 15 bps."""
    cost = CostModel()  # registered defaults: 11 bps friction, 4 bps slippage
    assert cost.effective_friction_bps == pytest.approx(11.0)
    assert cost.slippage_bps == pytest.approx(4.0)
    assert cost.wall_bps == pytest.approx(WALL_BPS)  # 15
    assert net_edge_bps(0.0030, cost) == pytest.approx(30.0 - 11.0 - 4.0)
    assert net_edge_bps(0.0030, cost) == pytest.approx(15.0)
    # A 10 bps capture is below the 15 bps wall -> net negative.
    assert net_edge_bps(0.0010, cost) == pytest.approx(10.0 - 15.0)


def test_maker_secondary_uses_2bps_wall_and_invalidates_gate() -> None:
    """The Maker secondary case uses a 2 bps friction component (registry Z.127),
    is NEVER gate-valid, and the driver carries the adverse-selection caveat."""
    maker = CostModel(maker=True)
    assert MAKER_WALL_BPS == pytest.approx(2.0)
    assert maker.effective_friction_bps == pytest.approx(2.0)
    # Maker wall = 2 bps friction + 4 bps slippage.
    assert maker.wall_bps == pytest.approx(MAKER_WALL_BPS + SLIPPAGE_BPS)
    assert net_edge_bps(0.0010, maker) == pytest.approx(10.0 - (2.0 + 4.0))
    # Maker is never a primary pass.
    assert gate_assumptions_valid(
        latency_ms=300.0, friction_bps=11.0, haircut_applied=True, maker=True
    ) is False

    # Through the driver: maker run sets gate_valid_assumptions false + caveat.
    pair_btc, pair_eth = _trend_pair(12.0, move_after_latency=True)
    payload = run(
        pair_btc, pair_eth, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, lags=(1,), grid_ms=GRID_MS, n_bootstrap=50, seed=42,
        maker_secondary=True,
    )
    assert payload["maker_secondary"] is True
    assert payload["gate_valid_assumptions"] is False
    assert payload["weiter_indication"] is False
    assert _best_variant(payload)["maker_secondary"] is True
    assert _best_variant(payload)["friction_bps"] == pytest.approx(2.0)
    assert "adverse-selection" in payload["maker_secondary_caveat"].lower()


# ===========================================================================
# 7. Bootstrap-p exactness + BH-FDR over the F-LEADLAG-TRADE family
# ===========================================================================

def test_bootstrap_p_exact_on_constructed_distribution() -> None:
    """One-sided bootstrap p = (#{resample mean <= 0} + 1) / (N + 1).

    All-positive net edges -> no resample mean <= 0 -> p = 1/(N+1). All-negative
    -> every resample mean <= 0 -> p = (N+1)/(N+1) = 1.0. Too few trips -> 1.0."""
    n_boot = 50
    all_pos = np.full(40, 10.0)
    assert bootstrap_mean_le_zero_p(all_pos, n_bootstrap=n_boot, seed=42) == pytest.approx(
        1.0 / (n_boot + 1)
    )
    all_neg = np.full(40, -5.0)
    assert bootstrap_mean_le_zero_p(all_neg, n_bootstrap=n_boot, seed=42) == pytest.approx(1.0)
    assert bootstrap_mean_le_zero_p(np.array([1.0, 2.0]), n_bootstrap=n_boot) == 1.0


def test_benjamini_hochberg_hand_computed_leadlag_family() -> None:
    """BH at alpha=0.10 over the F-LEADLAG-TRADE lag family (hand computed).

    m=3, p = [1/51, 1/51, 0.5] (two significant lags + one null lag). Sorted:
    .0196, .0196, .5; thresholds k/m*alpha = .0333/.0667/.10. Ranks 1,2 pass
    (.0196 <= .0333, .0196 <= .0667), rank 3 fails (.5 > .10) -> k_max=2 rejects
    exactly the two significant lags; p_crit = .0196. Input order preserved."""
    rejected, p_crit = benjamini_hochberg([1.0 / 51, 1.0 / 51, 0.5], alpha=0.10)
    assert rejected == [True, True, False]
    assert p_crit == pytest.approx(1.0 / 51)


def test_benjamini_hochberg_all_null_family_rejects_nothing() -> None:
    """A family of large p-values rejects nothing (no spurious tradability)."""
    rejected, p_crit = benjamini_hochberg([0.4, 0.6, 0.9], alpha=0.10)
    assert rejected == [False, False, False]
    assert p_crit == 0.0


# ===========================================================================
# 8. Window disjointness (half-open, imported splitter) + determinism
# ===========================================================================

def test_window_split_reuses_halfopen_disjoint_splitter() -> None:
    """H-04b reuses the bestand H-04 half-open splitter -> >= 2 disjoint,
    chronological windows with zero timestamp overlap (registry Z.139 reuse)."""
    pair_btc, pair_eth = _trend_pair(10.0, move_after_latency=True)
    windows = split_pair_windows(*pair_btc, *pair_eth, n_windows=2)
    assert len(windows) >= 2
    for (a_ts, _), (b_ts, _) in windows:
        assert a_ts.size > 0 and b_ts.size > 0
        assert np.all(np.diff(a_ts) >= 0)
    for prev_w, next_w in zip(windows, windows[1:]):
        (prev_a_ts, _), _ = prev_w
        (next_a_ts, _), _ = next_w
        # Half-open: previous window ends strictly before the next begins.
        assert float(prev_a_ts[-1]) < float(next_a_ts[0])


def test_run_same_seed_identical_json_payload() -> None:
    """Same input + same seed -> bit-identical JSON (minus the timestamp)."""
    pair_btc, pair_eth = _trend_pair(30.0, move_after_latency=True)
    kwargs = dict(
        symbol_a="BTC", symbol_b="ETH", n_windows=2, lags=(1, 2),
        grid_ms=GRID_MS, n_bootstrap=50, seed=42, source="determinism-fixture",
    )
    a = run(pair_btc, pair_eth, **kwargs)
    b = run(pair_btc, pair_eth, **kwargs)
    a.pop("generated_at")
    b.pop("generated_at")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ===========================================================================
# 9. Driver E2E on a mini pair-CSV — H-04b reference, capital_free:false, no verdict
# ===========================================================================

def _write_pair_csv(path: Path, ts: np.ndarray, px: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ts", "price"])
        for t, p in zip(ts, px):
            writer.writerow([f"{t:.3f}", f"{p:.6f}"])


def test_driver_e2e_csv_fixture_writes_json_and_md(tmp_path: Path) -> None:
    """CLI on a mini pair-CSV -> JSON + MD with the H-04b reference,
    ``capital_free: false``, every field per window/lag, and NO overall verdict."""
    pair_btc, pair_eth = _trend_pair(30.0, move_after_latency=True)
    file_a = tmp_path / "btc.csv"
    file_b = tmp_path / "eth.csv"
    out_dir = tmp_path / "out"
    _write_pair_csv(file_a, *pair_btc)
    _write_pair_csv(file_b, *pair_eth)

    rc = c17b_cli.main([
        "--file-a", str(file_a),
        "--file-b", str(file_b),
        "--pair", "BTC,ETH",
        "--windows", "2",
        "--lags", "1,2,3",
        "--bootstrap", "50",
        "--seed", "42",
        "--out", str(out_dir),
    ])
    assert rc == 0

    json_path = out_dir / "c17_c41_tradability_results.json"
    md_path = out_dir / "c17_c41_tradability_results.md"
    assert json_path.exists() and md_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    # H-04b reference + NON-kapitalfrei flag (the central difference to H-04).
    assert payload["hypothesis"] == "H-04b"
    assert payload["hypothesis_registry"].endswith("hypothesis_registry.md")
    assert payload["capital_free"] is False
    assert payload["fdr_family"] == "F-LEADLAG-TRADE"
    # The registered cost/latency point is surfaced.
    assert payload["registered_friction_wall_bps"] == pytest.approx(FRICTION_WALL_BPS)
    assert payload["registered_latency_ms"] == pytest.approx(LATENCY_MS)
    assert payload["wall_bps_total"] == pytest.approx(WALL_BPS)
    assert payload["latenz_haircut_applied"] is True
    assert payload["gate_valid_assumptions"] is True  # registered point

    # NO overall gate verdict (the gate-auditor's call against H-04b).
    for forbidden_key in ("verdict", "gate_verdict", "urteil", "WEITER", "DROP", "PARK"):
        assert forbidden_key not in payload

    # Every field present per window per lag (registry-mandated columns).
    assert payload["n_windows"] == 2
    assert len(payload["windows"]) == 2
    required = (
        "gross_capture_bps_mean", "latenz_haircut_applied", "friction_bps",
        "slippage_bps", "net_edge_bps_mean", "bootstrap_p",
        "fdr_significant_global", "maker_secondary",
    )
    for window in payload["windows"]:
        assert len(window["variants"]) == 3  # lags 1,2,3
        for v in window["variants"]:
            for field in required:
                assert field in v, f"missing field {field!r} in variant"
            assert isinstance(v["latenz_haircut_applied"], bool)
            assert v["latenz_haircut_applied"] is True
            assert v["friction_bps"] == pytest.approx(FRICTION_WALL_BPS)
            assert v["slippage_bps"] == pytest.approx(SLIPPAGE_BPS)
            assert v["maker_secondary"] is False

    md = md_path.read_text(encoding="utf-8")
    assert "H-04b" in md
    assert "capital_free" in md.lower()
    for window_index in (0, 1):
        assert f"## Fenster {window_index}" in md


def test_driver_cli_missing_file_exits_nonzero(tmp_path: Path) -> None:
    """Data defect (missing input) -> exit code 1, no JSON written."""
    rc = c17b_cli.main([
        "--file-a", str(tmp_path / "missing_a.csv"),
        "--file-b", str(tmp_path / "missing_b.csv"),
        "--out", str(tmp_path / "out"),
    ])
    assert rc == 1
    assert not (tmp_path / "out" / "c17_c41_tradability_results.json").exists()
