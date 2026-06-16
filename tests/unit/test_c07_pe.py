"""WP-3-VERIFY (T0, SANDBOX) — tests for the C-07 Permutation-Entropy module.

Covers ``src/bybit_edge/research/c07_pe/`` (H-06, KAPITALFREI; registry:
``scinance2-impl/state/hypothesis_registry.md``; design DEC-12). H-06 is a
two-stage KAPITALFREI mess-gate on the existing ``kline_1min`` close stream:

* PE = Bandt-Pompe permutation entropy of the log-returns, embedding m = 4 /
  tau = 1 PRE-FIXED (read-only constants ``PE_M`` / ``PE_TAU`` — NOT CLI flags;
  any deviation is a NEW H-06 line, verdict.md §1f). PE-drop = -diff(PE), rolling.
* PRE-Gate (hard pre-condition): Spearman rho between the PE-drop at t and the
  forward 15-min vol-cluster ``(t, t+15min]`` must clear 0.30 on >= 2 disjoint
  windows; rho < 0.30 in ONE window => DROP, no expensive main gate.
* Main-Gate: MI(PE_t ; target_{t+delta}) via 4 equal-frequency bins against a
  block-shift surrogate null (N >= 200 in the binding run), BH-FDR alpha = 0.10
  over F-ENTROPY, plus a conditional AUC-lift >= +0.03 in G1 (= top vol quartile
  of the surrogate null). delta in {1,5,15,60} min. WINDOW_MAX_BARS = 43200.

Tests (matching DEC-12's three Sandbox smokes + the registered mechanics):
 1. PE correctness: monotone -> PE ~ 0; i.i.d. -> PE ~ 1 (all m! = 24 patterns);
    m = 4 / tau = 1.
 2. m/tau fixation: PE_M == 4, PE_TAU == 1; NO --m / --tau CLI flag.
 3. Null control (i.i.d., several seeds): PRE-Gate rho < 0.3 AND 0 FDR-sig.
 4. Positive detection (coil-then-release): rho >= 0.3, surrogate_p < 0.05,
    AUC-lift >= +0.03.
 5. PRE-Gate blocker (THE structural test): PE structure but vol DECOUPLED ->
    rho < 0.3; the driver must NOT report the main gate as passed when rho < 0.3.
 6. Causality / No-Lookahead: forward vol window is strictly forward; PE-drop_t
    uses only the past; mutating a future bar leaves earlier PE untouched.
 7. Surrogate-p exactness ((#{>=obs} + 1)/(N + 1)) and BH-FDR (hand computed).
 8. G1 definition: G1 = top vol quartile of the surrogate null; AUC-lift =
    AUC(G1) - 0.5 exact on constructed labels.
 9. Window disjointness (HALF-OPEN edges, no WP-1 bug) + WINDOW_MAX_BARS cap
    (newest bars) + determinism (same seed -> identical JSON).
10. Driver E2E: mini kline-CSV -> JSON + MD, H-06 reference, capital_free: true,
    m/tau documented, every criterion per window/delta, NO bps/edge/PnL.

Runtime budget: surrogate N is kept small (50 for the statistical tests, 40 for
the driver E2E); seeds are fixed; everything is T0/SANDBOX. The binding H-06 run
on real klines (N = 200) is T3 (handoff_local), not this file.
"""
from __future__ import annotations

import argparse
import csv
import importlib
import json
import re
from pathlib import Path

import numpy as np
import pytest

import scripts.c07_pe as c07_cli
from bybit_edge.research.c07_pe import (
    AUC_LIFT_FLOOR,
    DEFAULT_LAGS_MIN,
    PE_M,
    PE_TAU,
    RHO_FLOOR,
    SURROGATE_P_MAX,
    VOL_CLUSTER_BARS,
    WINDOW_MAX_BARS,
    DataError,
    KlineArrays,
    benjamini_hochberg,
    forward_realized_vol,
    g1_auc_lift,
    info_test,
    log_returns,
    pe_drop,
    permutation_entropy,
    pre_gate,
    rolling_permutation_entropy,
    run,
    split_windows,
)
from bybit_edge.research.c07_pe.perm_entropy import _ordinal_pattern_codes

# The package __init__ re-exports ``info_test`` as a FUNCTION, which shadows the
# submodule of the same name. Pull the submodule explicitly so we can monkeypatch
# its module-level ``mutual_information`` for the surrogate-p exactness test.
info_test_mod = importlib.import_module("bybit_edge.research.c07_pe.info_test")

T0_MS = 1_700_000_000_000  # fixed epoch-ms anchor for synthetic kline timelines
PE_WINDOW = 24  # rolling-PE window used by the synthetic tests (small for speed)


# ---------------------------------------------------------------------------
# Synthetic return / close-price constructions
# ---------------------------------------------------------------------------

def _close_from_returns(rets: np.ndarray) -> np.ndarray:
    """Strictly-positive close path from a log-return series (P0 = 100)."""
    return 100.0 * np.exp(np.cumsum(np.asarray(rets, dtype=np.float64)))


def _iid_close(seed: int, n: int = 8000) -> np.ndarray:
    """Pure i.i.d. Gaussian log-returns -> no PE/vol coupling (the null)."""
    rng = np.random.default_rng(seed)
    return _close_from_returns(rng.normal(0.0, 1e-3, n))


def _coil_release_close(seed: int, n: int = 16000) -> np.ndarray:
    """Coil-then-release: an ordered low-complexity 'coil' (a PE / complexity
    collapse) immediately precedes a graded volatility burst, so the PE-drop at
    coil-entry leads the vol-cluster in its forward 15-min window. Cycle lengths
    are randomised so a block-shift surrogate breaks the coupling (=> a
    significant surrogate p), and burst size scales with a per-cycle energy so
    deeper coils predict bigger bursts (=> a strong rank correlation).

    Calibrated (test-engineer grid, seeds 0-2): rho >= 0.36, surrogate_p = 0.0196
    (N = 50), AUC-lift >= 0.057 — clearing the registered floors with margin.
    """
    rng = np.random.default_rng(seed)
    rets: list[float] = []
    while len(rets) < n:
        energy = rng.uniform(0.4, 1.0)
        bg = int(rng.integers(35 - 10, 35 + 10))      # noisy background: high PE
        coil = int(rng.integers(14 - 2, 14 + 2))      # ordered coil: PE collapse
        burst = int(rng.integers(8 - 2, 8 + 2))       # release: high vol
        rets.extend(rng.normal(0.0, 2e-4, bg))
        rets.extend(np.linspace(0.0, energy * 3e-5, coil))
        rets.extend(rng.normal(0.0, energy * 1.2e-2, burst))
    return _close_from_returns(np.array(rets[:n]))


def _pe_signal_no_volcoupling_close(seed: int, n: int = 16000) -> np.ndarray:
    """PE structure WITHOUT vol coupling (the PRE-Gate blocker): the series has
    real ordered coils (so PE genuinely drops), but the volatility bursts sit at
    INDEPENDENT random positions, decoupled from the coils. The PE-drop therefore
    carries no information about the forward vol-cluster -> rho < 0.3, and the
    cheap PRE-Gate must block before the expensive main gate runs.
    """
    rng = np.random.default_rng(seed)
    rets = np.zeros(n, dtype=np.float64)
    # 1) PE structure: ordered coils scattered through a mild-noise background,
    #    with only tiny vol (NO burst follows a coil).
    i = 0
    while i < n:
        bg = int(rng.integers(25, 45))
        coil = int(rng.integers(12, 16))
        end = min(i + bg, n)
        rets[i:end] = rng.normal(0.0, 3e-4, end - i)
        i = end
        if i >= n:
            break
        end = min(i + coil, n)
        rets[i:end] = np.linspace(0.0, 3e-5, end - i)
        i = end
    # 2) Vol bursts at INDEPENDENT random positions (decoupled from the coils).
    for _ in range(120):
        p = int(rng.integers(0, n - 12))
        length = int(rng.integers(8, 12))
        rets[p:p + length] += rng.normal(0.0, 1.2e-2, length)
    return _close_from_returns(rets)


def _kline_arrays(close: np.ndarray, t0_ms: int = T0_MS) -> KlineArrays:
    ts = (t0_ms + np.arange(close.size) * 60_000).astype(np.float64)
    return KlineArrays(ts=ts, close=np.asarray(close, dtype=np.float64))


def _stages(close: np.ndarray, *, pe_window: int = PE_WINDOW, delta: int = 5,
            n_surrogates: int = 50, seed: int = 11):
    """Run the full PE -> PRE-Gate -> main-gate stack on a close series."""
    rets = log_returns(close)
    pe = rolling_permutation_entropy(rets, window=pe_window, m=PE_M, tau=PE_TAU)
    drop = pe_drop(pe)
    fwd_rv = forward_realized_vol(rets, horizon_bars=VOL_CLUSTER_BARS)
    pg = pre_gate(drop, fwd_rv)
    target = forward_realized_vol(rets, horizon_bars=delta)
    st = info_test(pe, drop, target, fwd_rv, float(delta),
                   n_surrogates=n_surrogates, seed=seed)
    return pg, st


def _write_kline_csv(path: Path, close: np.ndarray, t0_ms: int = T0_MS) -> None:
    ts = (t0_ms + np.arange(close.size) * 60_000).astype(np.int64)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "close"])
        for t, c in zip(ts, close):
            w.writerow([int(t), f"{c:.6f}"])


# ===========================================================================
# 1. PE correctness (Bandt-Pompe)
# ===========================================================================

def test_pe_monotone_series_near_zero() -> None:
    """A strictly monotone series visits exactly ONE ordinal pattern (the
    identity permutation) -> normalised PE = 0 (minimal complexity)."""
    assert permutation_entropy(np.arange(200.0)) == pytest.approx(0.0, abs=1e-9)
    assert permutation_entropy(-np.arange(200.0)) == pytest.approx(0.0, abs=1e-9)


def test_pe_iid_random_near_one() -> None:
    """An i.i.d. random series spreads near-uniformly over all m! patterns ->
    normalised PE ~ 1 (maximal complexity)."""
    rng = np.random.default_rng(0)
    pe = permutation_entropy(rng.normal(size=20_000))
    assert pe > 0.99
    assert pe <= 1.0


def test_pe_m4_tau1_uses_all_24_ordinal_patterns() -> None:
    """m = 4 / tau = 1 has m! = 24 ordinal patterns; an i.i.d. series exercises
    all 24 (codes in [0, 24)). This verifies the embedding dimension concretely."""
    rng = np.random.default_rng(1)
    codes = _ordinal_pattern_codes(rng.normal(size=100_000), PE_M, PE_TAU)
    assert int(codes.max()) == 23  # 24 patterns, indices 0..23
    assert len(np.unique(codes)) == 24


def test_pe_in_unit_interval() -> None:
    """Normalised PE is always in [0, 1] regardless of input."""
    rng = np.random.default_rng(2)
    for x in (rng.normal(size=500), np.zeros(500), np.arange(500.0)):
        pe = permutation_entropy(x)
        assert 0.0 <= pe <= 1.0


def test_pe_drop_is_negative_diff() -> None:
    """PE-drop[t] = PE[t-1] - PE[t] (positive = a fall in complexity)."""
    pe = np.array([np.nan, 0.9, 0.7, 0.8, 0.5])
    drop = pe_drop(pe)
    assert np.isnan(drop[0])
    assert drop[2] == pytest.approx(0.2)   # 0.9 -> 0.7 : drop +0.2
    assert drop[3] == pytest.approx(-0.1)  # 0.7 -> 0.8 : rise -> negative
    assert drop[4] == pytest.approx(0.3)


# ===========================================================================
# 2. m/tau fixation — constants + NO CLI flag
# ===========================================================================

def test_pe_m_tau_are_prefixed_constants() -> None:
    """PE_M == 4, PE_TAU == 1 (claims_register §C-07 / verdict.md §1f, DEC-12)."""
    assert PE_M == 4
    assert PE_TAU == 1


def test_cli_has_no_m_or_tau_flag() -> None:
    """m / tau MUST NOT be CLI-settable — they are read-only constants. Any
    deviation is a NEW H-06 registry line (DEC-12). Inspect the argparse option
    strings AND the parsed namespace: no --m / --tau / --pe-m / --pe-tau."""
    captured: dict[str, list[str]] = {}
    orig = argparse.ArgumentParser.parse_args

    def spy(self, *a, **k):  # type: ignore[no-untyped-def]
        captured["opts"] = [s for act in self._actions for s in act.option_strings]
        return orig(self, *a, **k)

    argparse.ArgumentParser.parse_args = spy  # type: ignore[assignment]
    try:
        ns = c07_cli._parse_args(["--file", "x.csv"])
    finally:
        argparse.ArgumentParser.parse_args = orig  # type: ignore[assignment]

    opts = captured["opts"]
    for forbidden in ("--m", "--tau", "--pe-m", "--pe-tau", "--embedding-m"):
        assert forbidden not in opts, f"m/tau must not be a CLI flag: {forbidden}"
    # The parsed namespace must carry no m/tau knob either.
    assert not ({"m", "tau", "pe_m", "pe_tau"} & set(vars(ns).keys()))


# ===========================================================================
# 3. Null control (i.i.d.): PRE-Gate rho < 0.3 AND 0 FDR-significant
# ===========================================================================

@pytest.mark.parametrize("seed", [100, 101, 202, 303])
def test_null_iid_pre_gate_below_floor(seed: int) -> None:
    """Pure i.i.d. returns have no PE-drop -> vol coupling: PRE-Gate rho < 0.30.
    Parametrised over several fixed seeds so a lucky seed cannot carry it."""
    pg, _ = _stages(_iid_close(seed))
    assert abs(pg.rho) < RHO_FLOOR
    assert pg.rho_floor_met is False


def test_null_iid_no_fdr_significant_variant() -> None:
    """Null end-to-end through the driver: no FDR-significant variant (no false
    positive) and every window fails the PRE-Gate floor."""
    arrays = {sym: _kline_arrays(_iid_close(400 + i))
              for i, sym in enumerate(("AAA", "BBB"))}
    payload = run(arrays, n_windows=2, lags_min=(5, 15), n_surrogates=50, seed=42,
                  max_bars_per_window=4000, source="null-fixture")
    assert payload["n_fdr_significant"] == 0
    assert payload["all_windows_pre_gate_pass"] is False
    assert payload["any_window_pre_gate_fail"] is True


# ===========================================================================
# 4. Positive detection (coil-then-release)
# ===========================================================================

@pytest.mark.parametrize("seed", [0, 1, 2])
def test_positive_coil_release_clears_all_floors(seed: int) -> None:
    """Coil-then-release where the PE-drop leads the vol-burst: PRE-Gate
    rho >= 0.30, main-gate surrogate_p < 0.05, AUC-lift >= +0.03. The three
    registered detection floors, met across several fixed seeds."""
    pg, st = _stages(_coil_release_close(seed), delta=5, n_surrogates=50)
    assert pg.rho >= RHO_FLOOR, f"rho {pg.rho} below floor"
    assert pg.rho_floor_met is True
    assert st.surrogate_p < SURROGATE_P_MAX, f"surrogate_p {st.surrogate_p}"
    assert st.auc_lift >= AUC_LIFT_FLOOR, f"auc_lift {st.auc_lift}"


# ===========================================================================
# 5. PRE-Gate blocker — THE structural test
# ===========================================================================

@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_pre_gate_blocks_pe_signal_without_vol_coupling(seed: int) -> None:
    """A series with REAL PE structure but vol DECOUPLED from the coils: the
    PE-drop carries no information about the forward vol-cluster -> rho < 0.30.
    The cheap PRE-Gate is the hard pre-condition; it must fail here."""
    pg, _ = _stages(_pe_signal_no_volcoupling_close(seed))
    assert pg.rho < RHO_FLOOR, f"PRE-Gate should block (rho {pg.rho})"
    assert pg.rho_floor_met is False


def test_pre_gate_blocker_driver_does_not_report_main_gate_passed() -> None:
    """End-to-end: when the PRE-Gate floor is missed in every window, the driver
    must NOT advertise the main gate as passed. The PRE-Gate (rho >= 0.3) is the
    hard pre-condition — rho < 0.3 in ONE window => DROP (PRD §8.5). The payload
    surfaces the failing rho honestly and renders NO overall 'passed' verdict."""
    arrays = {"BLK": _kline_arrays(_pe_signal_no_volcoupling_close(0))}
    payload = run(arrays, n_windows=2, lags_min=(5,), n_surrogates=50, seed=42,
                  max_bars_per_window=8000, source="blocker-fixture")
    # PRE-Gate floor missed in (at least) one window -> hard DROP signal.
    assert payload["all_windows_pre_gate_pass"] is False
    assert payload["any_window_pre_gate_fail"] is True
    assert all(rho < RHO_FLOOR for rho in payload["pre_gate_rhos"])
    # The driver renders NO overall verdict / pass flag (gate-auditor's call).
    assert "passed" not in payload
    assert "verdict" not in payload
    # No per-variant flag claims a clean main-gate pass while the PRE-Gate failed:
    # the gate-auditor combines main_gate_variant_met WITH the PRE-Gate, and the
    # PRE-Gate here is a hard block. We assert the PRE-Gate failure is visible on
    # every result so the auditor cannot miss it.
    for r in payload["results"]:
        assert r["pre_gate"]["rho_floor_met"] is False


# ===========================================================================
# 6. Causality / No-Lookahead (forensic discipline)
# ===========================================================================

def test_forward_vol_is_strictly_forward() -> None:
    """forward_realized_vol[t] = sum_{k=1..15} r[t+k]^2 — a strictly forward
    window that shares no bar with anything computed up to and including t."""
    rng = np.random.default_rng(0)
    rets = rng.normal(0.0, 1e-3, 500)
    rv = forward_realized_vol(rets, horizon_bars=VOL_CLUSTER_BARS)
    i = 100
    assert rv[i] == pytest.approx(float(np.sum(rets[i + 1:i + 1 + VOL_CLUSTER_BARS] ** 2)))
    # trailing positions whose forward window runs off the end are NaN
    assert np.isnan(rv[-1])


def test_forward_vol_unaffected_by_past_mutation() -> None:
    """rv[t] uses only bars AFTER t: mutating the PAST never changes it."""
    rng = np.random.default_rng(1)
    rets = rng.normal(0.0, 1e-3, 400)
    rv = forward_realized_vol(rets, horizon_bars=VOL_CLUSTER_BARS)
    mutated = rets.copy()
    mutated[:50] = 9.9  # corrupt the past
    rv2 = forward_realized_vol(mutated, horizon_bars=VOL_CLUSTER_BARS)
    assert rv[100] == pytest.approx(rv2[100])


def test_no_lookahead_future_mutation_does_not_change_past_pe() -> None:
    """Rolling PE at bar t uses ONLY returns[t-window+1 : t+1] (causal,
    right-aligned). Mutating a FUTURE return must not change any earlier PE."""
    rng = np.random.default_rng(2)
    rets = rng.normal(0.0, 1e-3, 600)
    pe = rolling_permutation_entropy(rets, window=60, m=PE_M, tau=PE_TAU)
    cut = 400
    mutated = rets.copy()
    mutated[cut:] = rng.normal(0.0, 5e-2, rets.size - cut)  # mutate the future
    pe2 = rolling_permutation_entropy(mutated, window=60, m=PE_M, tau=PE_TAU)
    # PE up to (and including) bar cut-1 only sees returns < cut -> unchanged.
    assert np.allclose(pe[:cut], pe2[:cut], equal_nan=True)


def test_pe_drop_at_t_uses_only_past_and_current_pe() -> None:
    """PE-drop[t] = PE[t-1] - PE[t]; both PE values are right-aligned to <= t, so
    the PE-drop at t never reads a future bar. Mutating the future leaves the
    early PE-drop series untouched."""
    rng = np.random.default_rng(3)
    rets = rng.normal(0.0, 1e-3, 600)
    pe = rolling_permutation_entropy(rets, window=60, m=PE_M, tau=PE_TAU)
    drop = pe_drop(pe)
    mutated = rets.copy()
    mutated[450:] = 5e-2
    drop2 = pe_drop(rolling_permutation_entropy(mutated, window=60, m=PE_M, tau=PE_TAU))
    assert np.allclose(drop[:450], drop2[:450], equal_nan=True)


# ===========================================================================
# 7. Surrogate-p exactness + BH-FDR (hand computed)
# ===========================================================================

def test_surrogate_p_exact_formula(monkeypatch: pytest.MonkeyPatch) -> None:
    """Block-shift surrogate p = (#{MI_surrogate >= MI_observed} + 1)/(N + 1).
    Patch the module-level MI so 10 of 50 surrogates land >= the observed MI."""
    seq = [0.5] * 10 + [0.1] * 40  # 10 surrogates >= obs(0.3), 40 below
    state = {"i": 0}

    def fake_mi(x, y, n_bins=4):  # type: ignore[no-untyped-def]
        v = seq[state["i"]]
        state["i"] += 1
        return v

    monkeypatch.setattr(info_test_mod, "mutual_information", fake_mi)
    rng = np.random.default_rng(0)
    pe = rng.normal(size=400)
    target = rng.normal(size=400)
    p, _mean = info_test_mod.block_shift_surrogate_p(
        pe, target, observed_mi=0.3, n_surrogates=50, seed=1
    )
    assert p == pytest.approx((10 + 1) / (50 + 1))


def test_surrogate_p_floor_is_one_over_n_plus_one(monkeypatch: pytest.MonkeyPatch) -> None:
    """If NO surrogate reaches the observed MI, p = 1/(N+1) (the minimum)."""
    def zero_mi(x, y, n_bins=4):  # type: ignore[no-untyped-def]
        return 0.0
    monkeypatch.setattr(info_test_mod, "mutual_information", zero_mi)
    pe = np.random.default_rng(0).normal(size=300)
    target = np.random.default_rng(1).normal(size=300)
    p, _ = info_test_mod.block_shift_surrogate_p(
        pe, target, observed_mi=1.0, n_surrogates=50, seed=1
    )
    assert p == pytest.approx(1 / 51)


def test_benjamini_hochberg_hand_computed() -> None:
    """BH-FDR over F-ENTROPY, hand computed. p = [0.001, 0.04, 0.06, 0.2],
    alpha = 0.10, m = 4. Thresholds k/m*alpha = 0.025, 0.05, 0.075, 0.10:
    the three smallest pass (0.06 <= 0.075), 0.2 fails -> reject the 3 smallest,
    p_crit = 0.06."""
    rejected, p_crit = benjamini_hochberg([0.001, 0.04, 0.06, 0.2], 0.10)
    assert rejected == [True, True, True, False]
    assert p_crit == pytest.approx(0.06)


def test_benjamini_hochberg_step_up_and_edges() -> None:
    """Step-up property + edge cases: all-large -> none rejected; empty -> []."""
    rej, pc = benjamini_hochberg([0.5, 0.6, 0.7], 0.10)
    assert rej == [False, False, False]
    assert pc == 0.0
    assert benjamini_hochberg([], 0.10) == ([], 0.0)


# ===========================================================================
# 8. G1 definition + AUC-lift exact
# ===========================================================================

def test_g1_threshold_is_surrogate_top_vol_quartile() -> None:
    """G1 = the bars whose forward RV exceeds the 75th percentile of the
    SURROGATE-NULL distribution (registry H-06). With surr = rv = 0..39 the
    G1 threshold is the 75th pct (~29.25) -> G1 = the 10 bars rv in [30, 39]."""
    n = 40
    rv = np.arange(n, dtype=float)
    pd_ = np.arange(n, dtype=float)  # PE-drop perfectly co-ranks with rv
    surr = np.arange(n, dtype=float)
    _lift, n_g1 = g1_auc_lift(pd_, rv, surr)
    assert n_g1 == 10  # rv >= 29.25 -> 30..39


def test_g1_auc_lift_exact_perfect_and_inverse() -> None:
    """AUC-lift = AUC(G1) - 0.5. On constructed labels: PE-drop that perfectly
    ranks the high-vol G1 bars -> AUC 1.0 -> lift +0.5; the anti-correlated
    ranking -> AUC 0.0 -> lift -0.5."""
    n = 40
    rv = np.arange(n, dtype=float)
    surr = np.arange(n, dtype=float)
    perfect, _ = g1_auc_lift(np.arange(n, dtype=float), rv, surr)
    assert perfect == pytest.approx(0.5)
    inverse, _ = g1_auc_lift(np.arange(n, dtype=float)[::-1].copy(), rv, surr)
    assert inverse == pytest.approx(-0.5)


# ===========================================================================
# 9. Window disjointness (HALF-OPEN) + WINDOW_MAX_BARS cap + determinism
# ===========================================================================

def test_window_max_bars_constant_is_43200() -> None:
    """DEC-12 datierter Nachtrag: WINDOW_MAX_BARS = 43200 (= 30 days 1-min)."""
    assert WINDOW_MAX_BARS == 43_200


def test_split_windows_disjoint_half_open_boundary() -> None:
    """>= 2 disjoint chronological windows; HALF-OPEN [lo, hi) interior edges so
    a bar exactly on a boundary lands in EXACTLY ONE window (no WP-1 double-
    inclusive-edge bug). 200 bars -> partition with no double-counting."""
    ts = np.arange(200, dtype=float) * 60_000.0
    arr = KlineArrays(ts=ts, close=100.0 + np.arange(200, dtype=float))
    windows = split_windows(arr, 2, max_bars_per_window=100)
    assert len(windows) == 2
    for w in windows:
        assert w.size > 0
        assert np.all(np.diff(w.ts) >= 0)
    # disjoint + chronological: last ts of a window precedes first ts of the next
    assert float(windows[0].ts[-1]) < float(windows[1].ts[0])
    # every bar appears exactly once (the half-open partition)
    counts: dict[float, int] = {}
    for w in windows:
        for t in w.ts:
            counts[float(t)] = counts.get(float(t), 0) + 1
    assert all(c == 1 for c in counts.values()), "a boundary bar was double-counted"
    assert sum(w.size for w in windows) == 200


def test_split_windows_caps_to_newest_bars() -> None:
    """A large series is capped to the most recent n_windows x max_bars (DEC-12,
    deterministic-chronological) -> total <= cap and the newest bar is kept."""
    big = KlineArrays(ts=np.arange(500, dtype=float) * 60_000.0,
                      close=np.arange(500, dtype=float))
    windows = split_windows(big, 2, max_bars_per_window=100)
    assert sum(w.size for w in windows) <= 2 * 100
    # most recent bar (ts of index 499) survives the cap
    assert float(windows[-1].ts[-1]) == 499 * 60_000.0


def test_split_windows_rejects_fewer_than_two() -> None:
    """H-06 demands >= 2 disjoint windows; 1 window must raise DataError."""
    arr = KlineArrays(ts=np.arange(300, dtype=float) * 60_000.0,
                      close=100.0 + np.arange(300, dtype=float))
    with pytest.raises(DataError):
        split_windows(arr, 1)


def test_run_same_seed_identical_json_payload() -> None:
    """Same input + same seed -> identical JSON payload (minus generated_at).
    Registry reproducibility duty."""
    arrays = {"BTC": _kline_arrays(_coil_release_close(5, n=8000))}
    kwargs = dict(n_windows=2, lags_min=(5, 15), n_surrogates=40, seed=42,
                  max_bars_per_window=3000, source="determinism-fixture")
    a = run(arrays, **kwargs)
    b = run(arrays, **kwargs)
    a.pop("generated_at")
    b.pop("generated_at")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ===========================================================================
# 10. Driver E2E (CSV fixture) + KAPITALFREIHEIT
# ===========================================================================

def test_driver_e2e_csv_writes_json_and_md(tmp_path: Path) -> None:
    """CLI on a mini kline-CSV -> JSON + MD with the H-06 reference,
    ``capital_free: true``, m/tau documented, every criterion per window/delta,
    and NO bps/edge/PnL anywhere (KAPITALFREIHEIT)."""
    close = _coil_release_close(1, n=14000)
    csv_path = tmp_path / "kline.csv"
    out_dir = tmp_path / "out"
    _write_kline_csv(csv_path, close)

    rc = c07_cli.main([
        "--file", str(csv_path),
        "--windows", "2",
        "--surrogates", "40",
        "--lags", "5,15",
        "--seed", "42",
        "--max-bars-per-window", "7000",
        "--out", str(out_dir),
    ])
    assert rc == 0

    json_path = out_dir / "c07_pe_results.json"
    md_path = out_dir / "c07_pe_results.md"
    assert json_path.exists() and md_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["hypothesis"] == "H-06"
    assert payload["hypothesis_registry"].endswith("hypothesis_registry.md")
    assert payload["capital_free"] is True
    assert payload["n_windows"] == 2
    # m / tau documented in the payload (read-only constants, not flags)
    assert payload["pe_m"] == 4
    assert payload["pe_tau"] == 1
    assert len(payload["results"]) == 2  # 1 symbol x 2 windows

    pre_fields = {"n_pairs", "rho", "rho_floor", "rho_floor_met"}
    variant_fields = {"delta_min", "surrogate_p", "fdr_significant", "auc_lift", "n_g1"}
    for r in payload["results"]:
        assert r["window_index"] in (0, 1)
        assert pre_fields <= set(r["pre_gate"].keys())
        assert len(r["variants"]) == 2  # 2 deltas
        for v in r["variants"]:
            assert variant_fields <= set(v.keys()), (
                f"missing driver fields: {variant_fields - set(v.keys())}"
            )

    # The driver renders NO overall verdict — gate-auditor's call.
    assert "passed" not in payload
    assert "verdict" not in payload

    md = md_path.read_text(encoding="utf-8")
    assert "H-06" in md
    assert "hypothesis_registry.md" in md

    # KAPITALFREIHEIT (hard): a pure detection/info gate — no tradability field
    # may appear. Scan DATA carriers (JSON keys, MD table rows), NOT the
    # KAPITALFREI disclaimer prose which legitimately NEGATES these words.
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
    rc = c07_cli.main([
        "--file", str(tmp_path / "missing.csv"),
        "--out", str(tmp_path / "out"),
    ])
    assert rc == 1
    assert not (tmp_path / "out" / "c07_pe_results.json").exists()


def test_default_lags_are_registered_deltas() -> None:
    """delta in {1, 5, 15, 60} min (registry H-06 / DEC-12)."""
    assert DEFAULT_LAGS_MIN == (1, 5, 15, 60)


def test_module_source_has_no_tradability_logic() -> None:
    """KAPITALFREIHEIT, static: the module CODE must carry no tradability
    identifiers (bps / edge_bps / friction / pnl / sharpe / net_edge / tradable).
    Disclaimer prose that NEGATES these words is allowed; a real tradability
    metric is a bug. Comments and string literals are stripped before scanning."""
    pkg_dir = Path(__file__).resolve().parents[2] / "src/bybit_edge/research/c07_pe"
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
        no_comment = "\n".join(line.split("#", 1)[0] for line in no_str.splitlines())
        hit = leak.search(no_comment)
        assert hit is None, f"tradability identifier in {py.name}: {hit.group(0)!r}"
