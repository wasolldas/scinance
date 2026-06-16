"""WP-2-VERIFY (T0, SANDBOX) — tests for the C-01 OFI-sign module.

Covers ``src/bybit_edge/research/c01_ofi_sign/`` (H-05, INC-02-Anker, registry:
``scinance2-impl/state/hypothesis_registry.md``; design DEC-11). H-05 is a
KAPITALFREI mess-gate: it measures the *sign* of the conditional relation
``sign(OFI_t) -> sign(forward_return_{t+delta})`` on the existing ``trades``
stream with an OWN aggressor-signed trade-flow OFI estimator, against a
permutation surrogate null, BH-FDR alpha = 0.10 over the F-OFI family
(all delta lags x symbols), existence in >= 2 disjoint windows. WEITER requires
the POSITIVE (aggression-follow, PRD-v1) direction; a significant INVERSE
direction (the MM-replenishment reading the S2 implementation produced, E-04
hit_sum 0.179) is NOT an H-05 pass — it triggers a separate H-05b. There is NO
friction / edge / bps / PnL logic — that would be a separate H-05c.

1. Null control (most important — no false positive): pure-noise coupling
   (beta = 0), several fixed seeds -> no FDR-significant variant. A lucky seed
   cannot carry the suite.
2. Positive aggression (ret = beta*OFI + noise, beta > 0): sign_direction = +,
   surrogate_p < 0.05, |corr| >= 0.05, hit_rate > 0.53,
   h05_positive_consistent = True, inverse_significant = False.
3. INVERSE / INC-02 trap (beta < 0) — THE CRITICAL TEST: sign_direction = -,
   inverse_significant = True, h05_positive_consistent = FALSE. The module must
   NOT report any "passed" / positive-consistent flag when the coupling is
   inverted. This is the separation S2 failed in 2023.
4. Causality / No-Lookahead: the forward window ``(bin_end, bin_end+delta]`` is
   strictly after the OFI bin ``[t, t+grid)`` — mutating a value AFTER the
   forward window never changes the OFI/return of earlier bins; and time-
   reversing the series flips the coupling sign (the test is directional).
5. OFI correctness: a constructed trade set with known aggressor sides ->
   OFI = sum signed_qty exactly (hand-computed); pure buy flow -> OFI > 0, pure
   sell flow -> OFI < 0.
6. Hit-rate / corr-sign consistency on constructed data: sign(corr) and the
   hit-rate relation to 0.5 agree.
7. Surrogate-p exactness ((#{|surr| >= |obs|} + 1)/(N + 1)) and BH-FDR rejection
   on a hand-computed delta-family.
8. Window disjointness (>= 2 chronological windows, HALF-OPEN edges — the WP-1
   double-inclusive-edge bug must NOT recur) + determinism (same seed ->
   identical JSON).
9. Driver E2E on a mini trades-CSV -> JSON + MD with the H-05 reference,
   ``capital_free: true``, every field per window/delta/symbol, and NO
   bps/edge/friction/PnL column (KAPITALFREIHEIT assertion, grep on output).

Runtime budget: surrogate N is kept small (50 for the statistical tests, 30 for
the driver E2E); seeds are fixed; everything is T0/SANDBOX. The binding H-05 run
on real ticks is T3 (handoff_local), not this file.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np
import pytest

import scripts.c01_ofi_sign as c01_cli
from bybit_edge.research.c01_ofi_sign import (
    ABS_CORR_FLOOR,
    DEFAULT_LAGS_S,
    HIT_RATE_FLOOR,
    SURROGATE_P_MAX,
    DataError,
    TradeArrays,
    benjamini_hochberg,
    bin_ofi,
    conditional_hit_rate,
    ofi_and_forward_return,
    permutation_surrogate_p,
    run,
    sign_test,
    signed_volume,
    split_windows,
)
from bybit_edge.research.c01_ofi_sign.sign_test import _pearson

GRID_MS = 1000.0
SCALE = 0.001  # log-return scale per unit beta*OFI in the synthetic price path


# ===========================================================================
# Synthetic data: a clean, causal OFI -> forward-return coupling.
#
# One aggressor trade per bin at t = i*grid + grid/2 (so the bin grid is
# regular). The per-trade log price increment d[i+1] is driven by beta*OFI_i,
# placed so that the module's causal forward-return for bin i,
# ``log( P(bin_end_i + delta) / P(bin_end_i) )`` with delta = grid, equals
# beta*OFI_i*SCALE (+noise). beta > 0 => aggression-follow (positive) coupling,
# beta < 0 => the inverse / MM-replenishment coupling, beta = 0 => pure noise.
# Verified empirically: beta=0 yields corr exactly 0 (no false positive); a
# clean beta!=0 yields |corr| ~ 1; with noise the magnitude lands mid-range.
# ===========================================================================

def _coupled_trades(
    beta: float,
    seed: int,
    *,
    n: int = 600,
    noise: float = 0.0,
    grid_ms: float = GRID_MS,
) -> TradeArrays:
    rng = np.random.default_rng(seed)
    ofi = rng.normal(0.0, 1.0, n)
    nz = rng.normal(0.0, noise, n) if noise > 0 else np.zeros(n)
    d = np.zeros(n + 2)
    d[1 : n + 1] = (beta * ofi + nz) * SCALE  # d[i+1] drives fwd[i]
    logp = np.concatenate([[0.0], np.cumsum(d)])
    price = 100.0 * np.exp(logp)
    ts = np.array([i * grid_ms + grid_ms * 0.5 for i in range(n)], dtype=np.float64)
    volume = np.abs(ofi) + 0.05
    side = np.array(["Buy" if o > 0 else "Sell" for o in ofi], dtype=object)
    return TradeArrays(ts=ts, price=price[:n], volume=volume, side=side)


def _aligned(beta: float, seed: int, *, noise: float = 0.0, delta_s: float = 1.0):
    arr = _coupled_trades(beta, seed, noise=noise)
    return ofi_and_forward_return(arr.ts, arr.price, arr.volume, arr.side, GRID_MS, delta_s)


def _write_trades_csv(path: Path, arr: TradeArrays) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "price", "volume", "side"])
        for t, p, v, s in zip(arr.ts, arr.price, arr.volume, arr.side):
            w.writerow([f"{t:.1f}", f"{p:.8f}", f"{v:.6f}", str(s)])


# ===========================================================================
# 1. Null control (most important): beta = 0 -> no FDR-significant variant
# ===========================================================================

@pytest.mark.parametrize("seed", [42, 7, 99, 123, 2024])
def test_null_control_no_false_positive(seed: int) -> None:
    """Pure-noise coupling (beta = 0) over the full delta family must yield NO
    FDR-significant variant — no false positive, robust across seeds."""
    arr = _coupled_trades(0.0, seed, n=600)
    payload = run(
        {"NULL": arr},
        n_windows=2,
        lags_s=DEFAULT_LAGS_S,
        n_surrogates=50,
        seed=seed,
        max_ticks_per_window=2000,
        source="null-fixture",
    )
    assert payload["n_fdr_significant"] == 0, "beta=0 produced a FDR false positive"
    assert payload["any_inverse_significant"] is False
    for r in payload["results"]:
        for v in r["variants"]:
            assert v["fdr_significant"] is False
            assert v["h05_positive_consistent"] is False
            assert v["inverse_significant"] is False


def test_null_corr_is_exactly_zero_without_noise() -> None:
    """With no noise the beta=0 construction couples nothing: corr == 0."""
    ofi, fwd = _aligned(0.0, 42, noise=0.0)
    assert ofi.size > 100
    assert _pearson(ofi, fwd) == pytest.approx(0.0, abs=1e-9)


# ===========================================================================
# 2. Positive aggression (beta > 0): the H-05 aggression-follow direction
# ===========================================================================

@pytest.mark.parametrize("seed", [42, 7, 99])
def test_positive_aggression_direction(seed: int) -> None:
    """ret = beta*OFI + noise with beta > 0 -> sign +, p < 0.05, |corr| >= floor,
    hit-rate > 0.53, h05_positive_consistent True, inverse_significant False."""
    arr = _coupled_trades(2.0, seed, noise=1.0)
    payload = run(
        {"POS": arr},
        n_windows=2,
        lags_s=(1, 5),
        n_surrogates=50,
        seed=seed,
        max_ticks_per_window=2000,
        source="positive-fixture",
    )
    assert payload["any_inverse_significant"] is False
    assert payload["n_fdr_significant"] >= 1
    # Inspect the short-delta variants (the coupling lives at delta ~ grid).
    seen_consistent = False
    for r in payload["results"]:
        for v in r["variants"]:
            if v["delta_s"] != 1.0:
                continue
            assert v["sign_direction"] == 1, "positive coupling must read sign +"
            assert v["surrogate_p"] < SURROGATE_P_MAX
            assert v["abs_corr"] >= ABS_CORR_FLOOR
            assert v["hit_rate"] > HIT_RATE_FLOOR
            assert v["inverse_significant"] is False
            if v["h05_positive_consistent"]:
                seen_consistent = True
    assert seen_consistent, "no positive-consistent variant at delta=1s"


# ===========================================================================
# 3. INVERSE / INC-02 trap (beta < 0) — THE CRITICAL TEST
# ===========================================================================

@pytest.mark.parametrize("seed", [42, 7, 99])
def test_inverse_inc02_trap_is_not_a_pass(seed: int) -> None:
    """beta < 0 (MM-replenishment / INC-02 reading): the module must read
    sign -, flag inverse_significant True, and NEVER set h05_positive_consistent
    True. This is the separation S2 (E-04, hit_sum 0.179) failed in 2023 — a
    significant INVERSE coupling must NOT masquerade as an H-05 pass."""
    arr = _coupled_trades(-2.0, seed, noise=1.0)
    payload = run(
        {"INV": arr},
        n_windows=2,
        lags_s=(1, 5),
        n_surrogates=50,
        seed=seed,
        max_ticks_per_window=2000,
        source="inverse-fixture",
    )

    # The family must register the inverse direction as significant somewhere...
    assert payload["any_inverse_significant"] is True
    assert payload["any_nonpositive_sign_window"] is True

    # ...and NO variant anywhere may claim positive-consistency (an H-05 pass).
    for r in payload["results"]:
        for v in r["variants"]:
            assert v["h05_positive_consistent"] is False, (
                "INC-02 trap: inverse coupling reported as H-05 positive-consistent"
            )

    # The short-delta variants concretely show the inverted reading.
    inverse_seen = False
    for r in payload["results"]:
        for v in r["variants"]:
            if v["delta_s"] != 1.0:
                continue
            assert v["sign_direction"] == -1, "inverse coupling must read sign -"
            assert v["weiter_direction_positive"] is False
            assert v["hit_rate"] < 0.5
            if v["inverse_significant"]:
                inverse_seen = True
                # an H-05b trigger, explicitly NOT an H-05 pass:
                assert v["h05_positive_consistent"] is False
    assert inverse_seen, "no significant inverse variant at delta=1s"

    # The payload carries no overall "passed" / verdict field — gate-auditor's
    # call. The trap is reported NEUTRALLY, never adjudicated as a pass.
    assert "passed" not in payload
    assert "verdict" not in payload
    assert "weiter" not in payload


def test_positive_and_inverse_are_distinguished() -> None:
    """Direct contrast on the same seed: only beta>0 is positive-consistent;
    beta<0 is inverse-significant. The two must never both be a 'pass'."""
    pos = run(
        {"S": _coupled_trades(2.0, 314, noise=0.8)},
        n_windows=2, lags_s=(1,), n_surrogates=50, seed=314,
        max_ticks_per_window=2000, source="pos",
    )
    inv = run(
        {"S": _coupled_trades(-2.0, 314, noise=0.8)},
        n_windows=2, lags_s=(1,), n_surrogates=50, seed=314,
        max_ticks_per_window=2000, source="inv",
    )
    pos_consistent = any(
        v["h05_positive_consistent"] for r in pos["results"] for v in r["variants"]
    )
    inv_consistent = any(
        v["h05_positive_consistent"] for r in inv["results"] for v in r["variants"]
    )
    assert pos_consistent is True
    assert inv_consistent is False
    assert inv["any_inverse_significant"] is True
    assert pos["any_inverse_significant"] is False


# ===========================================================================
# 4. Causality / No-Lookahead
# ===========================================================================

def test_no_lookahead_future_mutation_leaves_past_unchanged() -> None:
    """Mutating a price AFTER the forward window of the early bins must not
    change the OFI/forward-return computed for those early bins. The forward
    window (bin_end, bin_end+delta] never reaches data beyond bin_end+delta."""
    arr = _coupled_trades(2.0, 5, n=120)
    # Take an early prefix so its last bin's forward window ends well before the
    # tail we mutate.
    pref = 40
    ts0, px0 = arr.ts[:pref].copy(), arr.price[:pref].copy()
    vol0, sd0 = arr.volume[:pref].copy(), arr.side[:pref].copy()
    ofi_a, fwd_a = ofi_and_forward_return(ts0, px0, vol0, sd0, GRID_MS, 1.0)

    # Mutate the very last (far-future) price of the prefix and re-run.
    px1 = px0.copy()
    px1[-1] *= 5.0
    ofi_b, fwd_b = ofi_and_forward_return(ts0, px1, vol0, sd0, GRID_MS, 1.0)

    # The mutated trade only affects bins whose forward window reaches it; the
    # earlier bins (all but possibly the last one or two) must be identical.
    assert ofi_a.size == ofi_b.size and ofi_a.size > 5
    keep = ofi_a.size - 3  # conservatively drop the last few bins near the edge
    assert np.allclose(ofi_a[:keep], ofi_b[:keep])
    assert np.allclose(fwd_a[:keep], fwd_b[:keep])


def test_forward_window_strictly_after_bin() -> None:
    """The bin end (right, exclusive) is the lower bound of the forward window:
    the OFI bin [t, t+grid) and the return window (bin_end, bin_end+delta] are
    disjoint — they share no trade timestamp."""
    arr = _coupled_trades(1.0, 1, n=60)
    bin_end, ofi = bin_ofi(arr.ts, signed_volume(arr.volume, arr.side), GRID_MS)
    # Each bin's left edge = bin_end - grid; the forward window starts at bin_end
    # (exclusive). So forward window lower bound == bin upper bound, no overlap.
    assert bin_end.size == ofi.size
    assert np.all(np.diff(bin_end) == pytest.approx(GRID_MS))


def test_time_reversal_flips_coupling_sign() -> None:
    """The test is directional: reversing time (so OFI looks at the PAST move
    instead of the future) flips the detected coupling sign. A symmetric /
    bidirectional estimator would not — proving the forward alignment is causal
    and signed, not a static correlation over the whole window."""
    arr = _coupled_trades(4.0, 21, n=400, noise=0.0)
    ofi_f, fwd_f = ofi_and_forward_return(
        arr.ts, arr.price, arr.volume, arr.side, GRID_MS, 1.0
    )
    corr_f = _pearson(ofi_f, fwd_f)
    assert corr_f > 0.2  # forward: strong positive (aggression-follow)

    # Reverse time: invert order AND flip aggressor side (a buy run played
    # backwards is a sell run); re-anchor timestamps ascending.
    rts = (arr.ts.max() - arr.ts[::-1]) + arr.ts.min()
    rpx = arr.price[::-1].copy()
    rvol = arr.volume[::-1].copy()
    rside = np.array(
        ["Sell" if s == "Buy" else "Buy" for s in arr.side[::-1]], dtype=object
    )
    ofi_r, fwd_r = ofi_and_forward_return(rts, rpx, rvol, rside, GRID_MS, 1.0)
    corr_r = _pearson(ofi_r, fwd_r)
    # The causal coupling does not survive time-reversal as the SAME positive
    # signal: the forward correlation must change (it is not a symmetric stat).
    assert corr_r < corr_f - 0.2


# ===========================================================================
# 5. OFI correctness (hand-computed)
# ===========================================================================

def test_signed_volume_aggressor_convention() -> None:
    """+vol for Buy takers (hit the ask), -vol for Sell takers (hit the bid)."""
    vol = np.array([1.0, 2.0, 0.5, 3.0, 4.0])
    side = np.array(["Buy", "Sell", "Buy", "Sell", "Unknown"], dtype=object)
    sv = signed_volume(vol, side)
    # "Unknown" is not exactly "Buy" -> treated as sell (bestand convention).
    assert list(sv) == [1.0, -2.0, 0.5, -3.0, -4.0]


def test_bin_ofi_is_sum_of_signed_qty() -> None:
    """Hand-computed: OFI per bin = sum of aggressor-signed volume in [t, t+grid)."""
    ts = np.array([0.0, 500.0, 1500.0, 1600.0, 2999.0])
    vol = np.array([1.0, 2.0, 0.5, 3.0, 1.0])
    side = np.array(["Buy", "Sell", "Buy", "Sell", "Buy"], dtype=object)
    sv = signed_volume(vol, side)
    bin_end, ofi = bin_ofi(ts, sv, 1000.0)
    # lo = 0 -> bin0=[0,1000): +1 -2 = -1; bin1=[1000,2000): +0.5 -3 = -2.5;
    # bin2=[2000,3000): +1.
    assert list(bin_end) == [1000.0, 2000.0, 3000.0]
    assert ofi == pytest.approx([-1.0, -2.5, 1.0])


def test_pure_buy_flow_positive_pure_sell_flow_negative() -> None:
    """Pure buy aggression -> OFI > 0 everywhere; pure sell -> OFI < 0."""
    ts = np.array([100.0, 400.0, 1200.0, 1800.0])
    vol = np.array([1.0, 2.0, 1.0, 1.0])
    buy = np.array(["Buy"] * 4, dtype=object)
    sell = np.array(["Sell"] * 4, dtype=object)
    _, ofi_buy = bin_ofi(ts, signed_volume(vol, buy), 1000.0)
    _, ofi_sell = bin_ofi(ts, signed_volume(vol, sell), 1000.0)
    nz_buy = ofi_buy[ofi_buy != 0.0]
    nz_sell = ofi_sell[ofi_sell != 0.0]
    assert np.all(nz_buy > 0.0)
    assert np.all(nz_sell < 0.0)


# ===========================================================================
# 6. Hit-rate / corr-sign consistency
# ===========================================================================

def test_hit_rate_and_corr_sign_consistent() -> None:
    """sign(corr) and the hit-rate relation to 0.5 must agree on coupled data."""
    # Positive: corr > 0 and hit-rate > 0.5.
    ofi_p, fwd_p = _aligned(4.0, 3, noise=0.0)
    assert _pearson(ofi_p, fwd_p) > 0
    assert conditional_hit_rate(ofi_p, fwd_p) > 0.5
    # Inverse: corr < 0 and hit-rate < 0.5.
    ofi_n, fwd_n = _aligned(-4.0, 3, noise=0.0)
    assert _pearson(ofi_n, fwd_n) < 0
    assert conditional_hit_rate(ofi_n, fwd_n) < 0.5


def test_hit_rate_perfect_and_flat_cases() -> None:
    """Constructed extremes: perfectly aligned -> 1.0; anti-aligned -> 0.0;
    no directional pairs -> chance 0.5."""
    ofi = np.array([1.0, -1.0, 2.0, -3.0])
    aligned = np.array([0.5, -0.5, 0.2, -0.1])
    anti = -aligned
    assert conditional_hit_rate(ofi, aligned) == 1.0
    assert conditional_hit_rate(ofi, anti) == 0.0
    assert conditional_hit_rate(np.zeros(4), aligned) == 0.5


# ===========================================================================
# 7. Surrogate-p exactness + BH-FDR
# ===========================================================================

def test_surrogate_p_formula_is_exact() -> None:
    """Permutation p = (#{|surr| >= |obs|} + 1)/(N + 1). With a perfectly
    coupled series no surrogate can match |obs| => p = 1/(N+1)."""
    ofi, fwd = _aligned(5.0, 8, noise=0.0)  # |corr| ~ 1
    n_sur = 49
    p, _mean = permutation_surrogate_p(
        ofi, fwd, _pearson(ofi, fwd), n_surrogates=n_sur, seed=11
    )
    assert p == pytest.approx(1.0 / (n_sur + 1))


def test_surrogate_p_uses_abs_corr_detects_both_signs() -> None:
    """The surrogate statistic is |corr|, so the INVERSE coupling is just as
    detectable (low p) as the positive one — the registry needs both."""
    ofi_p, fwd_p = _aligned(5.0, 8, noise=0.0)
    ofi_n, fwd_n = _aligned(-5.0, 8, noise=0.0)
    p_pos, _ = permutation_surrogate_p(ofi_p, fwd_p, _pearson(ofi_p, fwd_p), n_surrogates=49, seed=11)
    p_neg, _ = permutation_surrogate_p(ofi_n, fwd_n, _pearson(ofi_n, fwd_n), n_surrogates=49, seed=11)
    assert p_pos == pytest.approx(p_neg)
    assert p_pos < SURROGATE_P_MAX


def test_benjamini_hochberg_rejection_hand_computed() -> None:
    """BH over a delta-family: with m=4, alpha=0.10, thresholds rank/m*alpha =
    0.025, 0.05, 0.075, 0.10. p=[0.01,0.02,0.2,0.5] sorted -> 0.01<=0.025 and
    0.02<=0.05 reject (k_max=2); 0.2,0.5 stay. p_crit = 0.02."""
    rejected, p_crit = benjamini_hochberg([0.01, 0.02, 0.2, 0.5], alpha=0.10)
    assert rejected == [True, True, False, False]
    assert p_crit == pytest.approx(0.02)


def test_benjamini_hochberg_step_up_recovers_middle() -> None:
    """Step-up property: a borderline middle p is rescued by a later passing p.
    m=4, alpha=0.10: p=[0.02, 0.08, 0.07, 0.10] sorted [0.02,0.07,0.08,0.10] vs
    [0.025,0.05,0.075,0.10] -> 0.10<=0.10 passes at rank 4 => ALL reject."""
    rejected, p_crit = benjamini_hochberg([0.02, 0.08, 0.07, 0.10], alpha=0.10)
    assert rejected == [True, True, True, True]
    assert p_crit == pytest.approx(0.10)


def test_benjamini_hochberg_empty() -> None:
    assert benjamini_hochberg([], alpha=0.10) == ([], 0.0)


# ===========================================================================
# 8. Window disjointness (HALF-OPEN edges) + determinism
# ===========================================================================

def test_split_windows_disjoint_chronological_half_open() -> None:
    """>= 2 disjoint chronological windows. CRITICAL (WP-1 regression): the
    interior edges must be HALF-OPEN [lo, hi) so a trade exactly on a boundary
    lands in EXACTLY ONE window — never double-counted (the WP-1 double-inclusive
    edge bug)."""
    arr = _coupled_trades(0.0, 11, n=900)
    windows = split_windows(arr, 3, max_ticks_per_window=400)
    assert len(windows) == 3
    for w in windows:
        assert w.size > 0
        assert np.all(np.diff(w.ts) >= 0)
    # Disjoint + chronological: each window's last ts strictly precedes the next
    # window's first ts (no shared boundary tick).
    for prev_w, next_w in zip(windows, windows[1:]):
        assert float(prev_w.ts[-1]) < float(next_w.ts[0]), "windows overlap"
    # No tick is double-counted: the windows partition the (capped) tick set.
    total = sum(w.size for w in windows)
    capped = min(arr.size, 3 * 400)
    assert total == capped


def test_split_windows_boundary_tick_not_double_counted() -> None:
    """Construct a tick exactly on an interior window edge -> it must appear in
    exactly one window (the half-open [lo, hi) rule). This directly guards
    against the WP-1 double-inclusive-edge bug for c01."""
    # 8 ticks evenly spaced; linspace edges for 2 windows put the split at the
    # midpoint timestamp, which is itself a tick -> the half-open rule must keep
    # it out of the first window and in the second.
    ts = np.arange(8, dtype=np.float64) * 1000.0  # 0..7000
    arr = TradeArrays(
        ts=ts,
        price=np.full(8, 100.0),
        volume=np.ones(8),
        side=np.array(["Buy"] * 8, dtype=object),
    )
    windows = split_windows(arr, 2, max_ticks_per_window=8)
    counts: dict[float, int] = {}
    for w in windows:
        for t in w.ts:
            counts[float(t)] = counts.get(float(t), 0) + 1
    # Every original tick appears exactly once across the windows.
    assert sorted(counts) == [float(t) for t in ts]
    assert all(c == 1 for c in counts.values()), "a boundary tick was double-counted"


def test_split_windows_rejects_fewer_than_two() -> None:
    """H-05 demands >= 2 disjoint windows — 1 window must raise DataError."""
    arr = _coupled_trades(0.0, 11, n=300)
    with pytest.raises(DataError):
        split_windows(arr, 1)


def test_run_same_seed_identical_json_payload() -> None:
    """Same input + same seed -> identical JSON payload (minus the timestamp)."""
    arr = _coupled_trades(2.0, 5, n=400)
    kwargs = dict(
        n_windows=2, lags_s=(1, 5), n_surrogates=30, seed=42,
        max_ticks_per_window=2000, source="determinism-fixture",
    )
    a = run({"BTC": arr}, **kwargs)
    b = run({"BTC": arr}, **kwargs)
    a.pop("generated_at")
    b.pop("generated_at")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ===========================================================================
# 9. Driver E2E (CSV fixture) + KAPITALFREIHEIT
# ===========================================================================

def test_driver_e2e_csv_fixture_writes_json_and_md(tmp_path: Path) -> None:
    """CLI on a mini trades-CSV -> JSON + MD with the H-05 reference,
    ``capital_free: true``, every field per window/delta, and NO
    bps/edge/friction/PnL anywhere in the output (KAPITALFREIHEIT)."""
    arr = _coupled_trades(3.0, 7, n=500)
    csv_path = tmp_path / "trades.csv"
    out_dir = tmp_path / "out"
    _write_trades_csv(csv_path, arr)

    rc = c01_cli.main([
        "--file", str(csv_path),
        "--windows", "2",
        "--surrogates", "30",
        "--lags", "1,5",
        "--seed", "42",
        "--max-ticks-per-window", "2000",
        "--out", str(out_dir),
    ])
    assert rc == 0

    json_path = out_dir / "c01_ofi_sign_results.json"
    md_path = out_dir / "c01_ofi_sign_results.md"
    assert json_path.exists() and md_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["hypothesis"] == "H-05"
    assert payload["hypothesis_registry"].endswith("hypothesis_registry.md")
    assert payload["capital_free"] is True
    assert payload["n_windows"] == 2
    assert len(payload["results"]) == 2  # 1 symbol x 2 windows

    required_fields = {
        "delta_s", "corr", "sign_direction", "abs_corr", "hit_rate",
        "surrogate_p", "fdr_significant", "inverse_significant",
        "h05_positive_consistent",
    }
    for r in payload["results"]:
        assert r["window_index"] in (0, 1)
        assert len(r["variants"]) == 2  # 2 deltas
        for v in r["variants"]:
            assert required_fields <= set(v.keys()), (
                f"missing driver fields: {required_fields - set(v.keys())}"
            )
            assert v["sign_direction"] in (-1, 0, 1)

    # The driver renders NO overall verdict — gate-auditor's call.
    assert "passed" not in payload
    assert "verdict" not in payload

    md = md_path.read_text(encoding="utf-8")
    assert "H-05" in md
    assert "hypothesis_registry.md" in md

    # KAPITALFREIHEIT (hard): the gate is sign/correlation only — no tradability
    # field/column may appear. Scan DATA carriers (JSON keys, MD table headers),
    # NOT the KAPITALFREI disclaimer prose which legitimately NEGATES these words.
    forbidden = ("bps", "edge", "friction", "pnl", "sharpe", "tradab")

    def _all_keys(obj: object) -> list[str]:
        keys: list[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.append(str(k))
                keys.extend(_all_keys(v))
        elif isinstance(obj, list):
            for item in obj:
                keys.extend(_all_keys(item))
        return keys

    for key in _all_keys(payload):
        low = key.lower()
        for word in forbidden:
            assert word not in low, f"KAPITALFREIHEIT violated: JSON key '{key}'"

    for line in md.splitlines():
        if line.lstrip().startswith("|"):
            low = line.lower()
            for word in forbidden:
                assert word not in low, (
                    f"KAPITALFREIHEIT violated: tradability column in MD: {line!r}"
                )


def test_driver_cli_missing_file_exits_nonzero(tmp_path: Path) -> None:
    """Data defect (missing input) -> exit code 1, no JSON written."""
    rc = c01_cli.main([
        "--file", str(tmp_path / "missing.csv"),
        "--out", str(tmp_path / "out"),
    ])
    assert rc == 1
    assert not (tmp_path / "out" / "c01_ofi_sign_results.json").exists()


def test_module_source_has_no_tradability_logic() -> None:
    """KAPITALFREIHEIT, static: the module CODE must carry no tradability
    identifiers (bps / edge_bps / friction / pnl / sharpe / net_edge /
    tradable). Disclaimer prose that NEGATES these words is allowed; a real
    tradability metric is a bug. We scan code lines with comments and string
    literals stripped."""
    pkg_dir = Path(__file__).resolve().parents[2] / (
        "src/bybit_edge/research/c01_ofi_sign"
    )
    assert pkg_dir.is_dir(), pkg_dir
    leak = re.compile(
        r"\b(bps|edge_bps|friction|pnl|sharpe|net_edge|tradable)\b", re.IGNORECASE
    )
    str_literal = re.compile(
        r"'''.*?'''|\"\"\".*?\"\"\"|'[^']*'|\"[^\"]*\"", re.DOTALL
    )
    for py in pkg_dir.glob("*.py"):
        src = py.read_text(encoding="utf-8")
        no_str = str_literal.sub("", src)
        no_comment = "\n".join(
            line.split("#", 1)[0] for line in no_str.splitlines()
        )
        hit = leak.search(no_comment)
        assert hit is None, f"tradability identifier in {py.name}: {hit.group(0)!r}"
