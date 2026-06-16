"""WP-1-VERIFY (T0, SANDBOX) — tests for the C-17/C-41 lead-lag module.

Covers ``src/bybit_edge/research/c17_c41_lead_lag/`` (H-04, registry:
``scinance2-impl/state/hypothesis_registry.md``; design DEC-10). H-04 is a
KAPITALFREI mess-gate: it measures the *existence* of directed information flow
BTC->Alt (Shannon Transfer Entropy = C-17 axis; numpy-FFT Morlet wavelet
coherence phase-lead = C-41 axis) against a circular block-shift surrogate null,
BH-FDR alpha = 0.10 over the F-LEADLAG family, existence in >= 2 disjoint
windows, lead-symbol stability across windows. There is NO friction / edge /
bps / PnL logic — that would be a separate H-04b.

1. False-positive control (most important): two INDEPENDENT random walks
   (several fixed seeds) -> no window passes all criteria. A lucky seed cannot
   carry the suite.
2. Detection power: Y_t = alpha * X_{t-lag} + noise -> the window passes
   (surrogate p <= 0.05 after FDR), lead-symbol = X, detected lag ~ injected
   lag (tolerance = grid step, documented).
3. Direction asymmetry: with X->Y injected, T_{X->Y} is significant and
   T_{Y->X} is NOT (directed information is asymmetric — the core of C-17).
4. Causality sanity: the TE estimator is GLOBAL over the window (no sliding
   t), so we verify (a) the strict-past index window — the last ``lag`` source
   samples never enter the source role — and (b) time-reversing both series
   flips which direction carries the directed information.
5. Surrogate-p exactness ((#>=obs + 1)/(N + 1)) and BH-FDR rejection sets on
   hand-computed families.
6. Window disjointness (>= 2 chronological non-overlapping windows) +
   determinism (same seed -> identical JSON).
7. WINDOW_MAX_TICKS cap: a huge series -> windows <= cap, newest ticks kept.
8. Driver E2E on a mini-pair CSV -> JSON + MD with the H-04 reference,
   ``capital_free: true``, every gate criterion per window, and NO
   bps/edge/friction/PnL column (KAPITALFREIHEIT assertion, grep on output).
9. Grid-sync: two streams with different tick timestamps are resampled onto a
   common grid (length / alignment assertion).

Runtime budget: surrogate N is kept small (30-120) — the detection-power and
driver-E2E tests need N large enough that the true variant's p
(1/(N+1)) clears the BH rank-1 threshold (alpha/m) over the F-LEADLAG family,
so N is sized to m (fewer lags => smaller N). Seeds are fixed; everything is
T0/SANDBOX. The binding H-04 run on real ticks is T3 (handoff_local).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

import scripts.c17_c41_lead_lag as c17_cli
from bybit_edge.research.c17_c41_lead_lag import (
    DEFAULT_GRID_MS,
    WINDOW_MAX_TICKS,
    DataError,
    align_returns,
    benjamini_hochberg,
    resample_log_returns,
    run,
    split_pair_windows,
    surrogate_test_te,
    transfer_entropy,
)
from bybit_edge.research.c17_c41_lead_lag import surrogate as surrogate_mod

T0_MS = 1_700_000_000_000.0  # fixed epoch anchor for all synthetic timelines
GRID_MS = 1000.0

# Detection-power lag tolerance (documented): a fixed integer ``lag`` maps to
# ``lag * grid_ms`` milliseconds, so the lag can be located no better than
# +- one grid step.
LAG_TOL_MS = GRID_MS


# ---------------------------------------------------------------------------
# Synthetic bar-level pairs synthesised into one-tick-per-bar price streams.
#
# The module resamples ticks onto a ``grid_ms`` bar grid (last tick wins). By
# placing exactly one tick at each bar centre we get a deterministic 1:1 map
# from injected bar returns to the module's resampled returns, so the injected
# lead-lag structure survives the resample unchanged.
# ---------------------------------------------------------------------------

def _ticks_from_log_returns(
    log_ret: np.ndarray, p0: float, grid_ms: float = GRID_MS
) -> tuple[np.ndarray, np.ndarray]:
    """One tick per bar centre carrying the cumulative price of ``log_ret``."""
    px = p0 * np.exp(np.concatenate([[0.0], np.cumsum(log_ret)]))
    n = px.size
    ts = T0_MS + (np.arange(n) + 0.5) * grid_ms
    return ts, px


def _independent_pair(
    seed: int, n_bars: int = 900, sigma: float = 1e-3
) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    """Two INDEPENDENT random walks (no cross-coupling) — the H-04 null."""
    rng = np.random.default_rng(seed)
    rx = rng.normal(0.0, sigma, size=n_bars)
    ry = rng.normal(0.0, sigma, size=n_bars)
    return (
        _ticks_from_log_returns(rx, 50_000.0),
        _ticks_from_log_returns(ry, 3_000.0),
    )


def _lead_lag_pair(
    seed: int,
    n_bars: int = 900,
    lag: int = 3,
    alpha: float = 0.85,
    noise: float = 2e-4,
    sigma: float = 1e-3,
) -> tuple[
    tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray], np.ndarray, np.ndarray
]:
    """X leads Y: ``ry[t] = alpha * rx[t-lag] + noise``. Returns the two tick
    streams plus the raw return arrays (for the TE-level direction tests)."""
    rng = np.random.default_rng(seed)
    rx = rng.normal(0.0, sigma, size=n_bars)
    ry = np.zeros(n_bars)
    ry[lag:] = alpha * rx[:-lag] + noise * rng.normal(0.0, 1.0, size=n_bars - lag)
    pair_x = _ticks_from_log_returns(rx, 50_000.0)
    pair_y = _ticks_from_log_returns(ry, 3_000.0)
    return pair_x, pair_y, rx, ry


# ===========================================================================
# 1. False-positive control (most important): independent RWs stay null
# ===========================================================================

@pytest.mark.parametrize("seed", [7, 23, 1337])
def test_false_positive_control_independent_random_walks(seed: int) -> None:
    """Two INDEPENDENT random walks must NOT pass the H-04 gate.

    No window may report existence (FDR-significant surrogate p <= 0.05). This
    is the H-04 falsification anchor (verdict.md §1e: an "abgegraste 30-60s
    HFT-Anomalie" must read as null on structureless noise). Three fixed seeds
    so a single lucky draw cannot carry the suite.
    """
    pair_x, pair_y = _independent_pair(seed)
    payload = run(
        pair_x, pair_y,
        symbol_a="BTC", symbol_b="ETH",
        n_windows=2, n_surrogates=80, seed=42,
        lags=(2, 3), grid_ms=GRID_MS,
    )
    assert payload["all_windows_pass"] is False, (
        f"false positive on independent RWs (seed={seed}): "
        f"per_window={payload['per_window_existence']}"
    )
    assert not any(payload["per_window_existence"]), (
        f"a window claimed existence on independent RWs (seed={seed})"
    )


# ===========================================================================
# 2. Detection power: injected lead is found, lead-symbol + lag correct
# ===========================================================================

def test_detection_power_injected_lead_lag() -> None:
    """Y_t = alpha * X_{t-lag} + noise -> window passes; lead = X; lag ~ injected.

    F-LEADLAG here has m = 2*len(lags)+1 = 5 variants, so the BH rank-1
    threshold is alpha/m = 0.10/5 = 0.02; the true variant's smallest possible
    p is 1/(N+1), so N = 120 gives p_min ~ 0.0083 < 0.02 and the genuine
    BTC->ETH arrow survives FDR. Lag tolerance = LAG_TOL_MS = 1 grid step.
    """
    injected_lag = 3
    pair_x, pair_y, _, _ = _lead_lag_pair(seed=7, lag=injected_lag)
    payload = run(
        pair_x, pair_y,
        symbol_a="BTC", symbol_b="ETH",
        n_windows=2, n_surrogates=120, seed=42,
        lags=(2, 3), grid_ms=GRID_MS,
    )

    assert payload["all_windows_pass"] is True, (
        f"injected lead not detected: per_window={payload['per_window_existence']}"
    )
    assert all(payload["per_window_existence"])
    # Lead symbol is the SOURCE of the directed information = X = BTC, stable.
    assert payload["lead_symbol_stable"] is True
    assert payload["lead_symbols"] == ["BTC", "BTC"]

    for window in payload["windows"]:
        criteria = window["criteria"]
        assert criteria["surrogate_p"]["passed"] is True
        assert criteria["surrogate_p"]["value"] <= 0.05
        assert criteria["lead_symbol"]["value"] == "BTC"
        # Detected lag ~ injected lag * grid_ms (= 3000 ms), within one grid step.
        detected_lag_ms = criteria["lead_symbol"]["lag_ms"]
        assert abs(detected_lag_ms - injected_lag * GRID_MS) <= LAG_TOL_MS, (
            f"detected lag {detected_lag_ms} ms not within {LAG_TOL_MS} ms of "
            f"injected {injected_lag * GRID_MS} ms"
        )


# ===========================================================================
# 3. Direction asymmetry (the core of C-17 transfer entropy)
# ===========================================================================

def test_direction_asymmetry_te_significant_one_way_only() -> None:
    """With X->Y injected, the surrogate gate is significant for T_{X->Y} but
    NOT for T_{Y->X}: directed information is asymmetric.

    Run at the TRUE lag in isolation (m = 1, no FDR tax) so the asymmetry is
    read off the raw surrogate p-values, not the family correction.
    """
    lag = 3
    _, _, rx, ry = _lead_lag_pair(seed=7, lag=lag)

    # Point estimate: TE in the true direction dwarfs the reverse.
    te_fwd = transfer_entropy(rx, ry, lag, n_bins=3)
    te_rev = transfer_entropy(ry, rx, lag, n_bins=3)
    assert te_fwd > 10 * te_rev > 0.0, (
        f"TE not asymmetric: X->Y={te_fwd}, Y->X={te_rev}"
    )

    fwd = surrogate_test_te(rx, ry, lag, n_bins=3, n_surrogates=80, seed=11)
    rev = surrogate_test_te(ry, rx, lag, n_bins=3, n_surrogates=80, seed=11)
    assert fwd.p_value <= 0.05, f"X->Y not significant: p={fwd.p_value}"
    assert rev.p_value > 0.05, (
        f"Y->X spuriously significant (asymmetry broken): p={rev.p_value}"
    )
    assert fwd.observed_stat > rev.observed_stat


# ===========================================================================
# 4. Causality sanity (TE is GLOBAL over the window — no sliding t)
# ===========================================================================

def test_te_uses_only_strict_past_of_source_index_window() -> None:
    """The TE pairing uses ``s_past = source[0:n-lag]``: the last ``lag`` source
    samples never enter the source role (no-lookahead index-window contract).

    Verified WITHOUT disturbing the global equal-frequency quantiser: instead of
    spiking the tail (which would re-rank every sample), we replace the unused
    future-most ``lag`` source values with samples drawn from the SAME interior
    distribution (a permutation of interior values). Their quantile codes stay
    in-range so the binning of the past is untouched, and since those positions
    never enter ``s_past`` the TE estimate is bit-identical — the future tail is
    causally inert.
    """
    rng = np.random.default_rng(3)
    n, lag = 600, 3
    source = rng.normal(0.0, 1.0, size=n)
    target = rng.normal(0.0, 1.0, size=n)

    baseline = transfer_entropy(source, target, lag, n_bins=3)
    assert baseline >= 0.0

    mutated = source.copy()
    # Reorder ONLY the future-most tail among its own values: the multiset of
    # source values is unchanged (quantiser identical) and the tail never enters
    # s_past, so a permutation of it must leave TE bit-identical.
    mutated[n - lag:] = mutated[n - lag:][::-1]
    assert transfer_entropy(mutated, target, lag, n_bins=3) == baseline


def test_te_time_reversal_flips_direction() -> None:
    """Time-reversing BOTH series flips which direction carries the directed
    information — a sanity check that TE tracks genuine temporal order.

    Since the TE estimator is global over the window (no sliding detection
    instant), this swap of past<->future is the registry-prescribed causality
    test: forward T_{X->Y} dominates, reversed T_{Y->X} dominates instead.
    """
    lag = 3
    _, _, rx, ry = _lead_lag_pair(seed=7, lag=lag)

    fwd_xy = transfer_entropy(rx, ry, lag, n_bins=3)
    fwd_yx = transfer_entropy(ry, rx, lag, n_bins=3)
    assert fwd_xy > fwd_yx  # X leads Y forward

    rx_rev, ry_rev = rx[::-1].copy(), ry[::-1].copy()
    rev_xy = transfer_entropy(rx_rev, ry_rev, lag, n_bins=3)
    rev_yx = transfer_entropy(ry_rev, rx_rev, lag, n_bins=3)
    # Under time reversal the arrow flips: Y now "leads" X.
    assert rev_yx > rev_xy, f"time reversal did not flip direction: {rev_xy} vs {rev_yx}"
    # The dominant directed-information magnitude is preserved (same coupling).
    assert rev_yx == pytest.approx(fwd_xy, rel=0.05)


# ===========================================================================
# 5. Surrogate-p exactness + BH-FDR hand computations
# ===========================================================================

def test_surrogate_p_value_exact_formula(monkeypatch: pytest.MonkeyPatch) -> None:
    """p must be exactly (#{surrogate >= observed} + 1) / (N + 1).

    ``transfer_entropy`` is scripted in the surrogate module: first call
    returns the observed TE, the next N calls return a constructed surrogate
    distribution. With observed 5.0 and surrogates [6,4,5,1,7,2,5,0.5,3,8]
    exactly five are >= 5.0 (6,5,7,5,8) -> p = (5 + 1) / (10 + 1) = 6/11.
    """
    scripted = [5.0, 6.0, 4.0, 5.0, 1.0, 7.0, 2.0, 5.0, 0.5, 3.0, 8.0]
    calls: list[float] = []

    def fake_te(*args, **kwargs) -> float:
        calls.append(scripted[len(calls)])
        return calls[-1]

    monkeypatch.setattr(surrogate_mod, "transfer_entropy", fake_te)

    source = np.arange(40, dtype=np.float64)
    target = np.arange(40, dtype=np.float64)
    result = surrogate_test_te(
        source, target, lag=3, n_bins=3, n_surrogates=10, seed=1
    )

    assert len(calls) == 11  # 1 observed + 10 surrogates
    assert result.observed_stat == pytest.approx(5.0)
    assert result.p_value == pytest.approx(6.0 / 11.0)
    assert result.n_surrogates == 10


def test_surrogate_degenerate_input_returns_p_one() -> None:
    """Too few bars for the lag -> no test, p = 1.0, never spuriously sig."""
    source = np.arange(10, dtype=np.float64)
    target = np.arange(10, dtype=np.float64)
    result = surrogate_test_te(source, target, lag=3, n_bins=3, n_surrogates=10)
    assert result.p_value == 1.0
    assert result.n_surrogates == 0


def test_benjamini_hochberg_hand_computed_rejections() -> None:
    """BH at alpha=0.10, m=4: thresholds k/m*alpha = .025/.05/.075/.10.

    p = [0.02, 0.5, 0.03, 0.9] sorted -> .02 <= .025 (k=1 ok), .03 <= .05
    (k=2 ok), .5 > .075, .9 > .10 -> k_max = 2: reject exactly {0.02, 0.03},
    p_crit = 0.03. Input order is preserved in the output mask.
    """
    rejected, p_crit = benjamini_hochberg([0.02, 0.5, 0.03, 0.9], alpha=0.10)
    assert rejected == [True, False, True, False]
    assert p_crit == pytest.approx(0.03)


def test_benjamini_hochberg_step_up_property() -> None:
    """BH is step-UP: a failing low rank is rescued by a passing higher rank.

    alpha=0.10, m=3: thresholds .0333/.0667/.10. p = [0.04, 0.9, 0.045]:
    rank 1 (.04 > .0333) fails, rank 2 (.045 <= .0667) passes -> k_max = 2
    rejects BOTH 0.04 and 0.045.
    """
    rejected, p_crit = benjamini_hochberg([0.04, 0.9, 0.045], alpha=0.10)
    assert rejected == [True, False, True]
    assert p_crit == pytest.approx(0.045)


def test_benjamini_hochberg_edge_cases() -> None:
    """Empty family and an all-null family."""
    assert benjamini_hochberg([], alpha=0.10) == ([], 0.0)
    rejected, p_crit = benjamini_hochberg([0.5, 0.61], alpha=0.10)
    assert rejected == [False, False]
    assert p_crit == 0.0


# ===========================================================================
# 6. Window disjointness + determinism
# ===========================================================================

def test_split_pair_windows_disjoint_and_chronological() -> None:
    """>= 2 windows, chronological, zero timestamp overlap on a SHARED axis."""
    pair_x, pair_y = _independent_pair(seed=11, n_bars=900)
    windows = split_pair_windows(*pair_x, *pair_y, n_windows=3)

    assert len(windows) >= 2
    for (a_ts, a_px), (b_ts, b_px) in windows:
        assert a_ts.size > 0 and b_ts.size > 0
        assert a_ts.size == a_px.size and b_ts.size == b_px.size
        assert np.all(np.diff(a_ts) >= 0)
        assert np.all(np.diff(b_ts) >= 0)
    # Disjoint + chronological across windows (per symbol, on the shared axis).
    # Window tuple = ((a_ts, a_px), (b_ts, b_px)); take the [0] (ts) of each.
    for prev_w, next_w in zip(windows, windows[1:]):
        (prev_a_ts, _), (prev_b_ts, _) = prev_w
        (next_a_ts, _), (next_b_ts, _) = next_w
        assert float(prev_a_ts[-1]) < float(next_a_ts[0]), "symbol A windows overlap"
        assert float(prev_b_ts[-1]) < float(next_b_ts[0]), "symbol B windows overlap"


def test_split_pair_windows_rejects_fewer_than_two() -> None:
    """H-04 demands >= 2 disjoint windows — 1 window must be a DataError."""
    pair_x, pair_y = _independent_pair(seed=11, n_bars=900)
    with pytest.raises(DataError):
        split_pair_windows(*pair_x, *pair_y, n_windows=1)


def test_run_same_seed_identical_json_payload() -> None:
    """Same input + same seed -> bit-identical JSON (minus the timestamp)."""
    pair_x, pair_y = _independent_pair(seed=5, n_bars=900)
    kwargs = dict(
        symbol_a="BTC", symbol_b="ETH",
        n_windows=2, n_surrogates=20, seed=42,
        lags=(2, 3), grid_ms=GRID_MS, source="determinism-fixture",
    )
    a = run(pair_x, pair_y, **kwargs)
    b = run(pair_x, pair_y, **kwargs)
    a.pop("generated_at")
    b.pop("generated_at")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ===========================================================================
# 7. WINDOW_MAX_TICKS cap (DEC-10): keep the newest ticks, stay tractable
# ===========================================================================

def _huge_pair(
    n: int = 400_000, span_days: float = 5.0, seed: int = 17
) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    """A days-deep tick pair (like the real ``trades`` table) + prices.

    The bulk is OLD; only the newest tail forms the dense recent data the cap
    keeps. Mirrors the c31 multiday fixture rationale (DEC-09/DEC-10).
    """
    rng = np.random.default_rng(seed)
    span_ms = span_days * 24 * 3600 * 1000.0

    def one(p0: float, sd: int) -> tuple[np.ndarray, np.ndarray]:
        r = np.random.default_rng(sd)
        budget = 2 * WINDOW_MAX_TICKS
        n_old = n - budget
        recent = np.cumsum(r.exponential(20.0, size=budget))
        recent_span = float(recent[-1])
        old = np.sort(r.uniform(0.0, span_ms - recent_span, size=n_old))
        ts = T0_MS + np.concatenate([old, (span_ms - recent_span) + recent])
        px = p0 * np.exp(np.cumsum(r.normal(0.0, 1e-6, size=n)))
        return ts, px

    return one(50_000.0, seed), one(3_000.0, seed + 1)


def test_split_pair_windows_caps_to_newest_ticks() -> None:
    """A days-deep pair -> 2 windows; the cap keeps only the newest
    ``n_windows * WINDOW_MAX_TICKS`` ticks PER SYMBOL (DEC-10 deterministic tick
    budget), and the kept tail ends at the most recent tick.

    DEC-10 caps the per-symbol TOTAL to ``n_windows * max_ticks`` and then cuts
    the overlapping wall-clock range into equal-TIME slices, so a single window
    may hold slightly more than ``max_ticks`` if ticks cluster in time — the
    binding bound is the per-symbol total budget, not the per-window count.
    """
    pair_x, pair_y = _huge_pair()
    budget = 2 * WINDOW_MAX_TICKS
    windows = split_pair_windows(*pair_x, *pair_y, n_windows=2)

    assert len(windows) == 2
    total_a = sum(a_ts.size for (a_ts, _), _ in windows)
    total_b = sum(b_ts.size for _, (b_ts, _) in windows)
    assert total_a <= budget
    assert total_b <= budget
    # Newest tail kept: the last window ends at the most recent shared tick.
    last_a = windows[-1][0][0]
    assert float(last_a[-1]) == pytest.approx(float(pair_x[0][-1]))
    # The discarded older bulk really was dropped (kept start >> series start).
    first_kept = windows[0][0][0][0]
    assert float(first_kept) > float(pair_x[0][0])


def test_split_pair_windows_custom_cap_respected() -> None:
    """An explicit small cap bounds each symbol's kept TOTAL to
    ``n_windows * max_ticks`` (the DEC-10 per-symbol tick budget)."""
    pair_x, pair_y = _huge_pair()
    windows = split_pair_windows(
        *pair_x, *pair_y, n_windows=2, max_ticks_per_window=2_000
    )
    assert len(windows) == 2
    total_a = sum(a_ts.size for (a_ts, _), _ in windows)
    total_b = sum(b_ts.size for _, (b_ts, _) in windows)
    assert total_a <= 2 * 2_000
    assert total_b <= 2 * 2_000


def test_run_huge_pair_with_small_cap_is_tractable_and_correct() -> None:
    """A days-deep pair with a small explicit cap runs in seconds, records the
    data-scoping fields, and leaves the gate thresholds UNTOUCHED (DEC-10)."""
    import time

    pair_x, pair_y = _huge_pair()
    t0 = time.monotonic()
    payload = run(
        pair_x, pair_y,
        symbol_a="BTC", symbol_b="ETH",
        n_windows=2, n_surrogates=3, seed=42,
        lags=(2, 3), grid_ms=GRID_MS,
        max_ticks_per_window=3_000,
    )
    elapsed = time.monotonic() - t0
    assert elapsed < 120.0, f"capped run too slow ({elapsed:.1f}s)"
    assert payload["n_windows"] == 2
    assert payload["max_ticks_per_window"] == 3_000
    assert payload["n_ticks_total"] == {"a": pair_x[0].size, "b": pair_y[0].size}
    # Gate thresholds are a data-scoping-independent contract.
    assert payload["gate_thresholds"] == {
        "surrogate_p_max": 0.05,
        "min_windows": 2,
        "lead_symbol_stable_required": True,
    }


# ===========================================================================
# 8. Driver E2E on a mini-pair CSV (KAPITALFREIHEIT assertion)
# ===========================================================================

def _write_pair_csv(path: Path, ts: np.ndarray, px: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ts", "price"])
        for t, p in zip(ts, px):
            writer.writerow([f"{t:.3f}", f"{p:.4f}"])


def test_driver_e2e_csv_fixture_writes_json_and_md(tmp_path: Path) -> None:
    """CLI on a mini pair-CSV -> JSON + MD with the H-04 reference,
    ``capital_free: true`` and every gate criterion per window — and NO
    bps/edge/friction/PnL anywhere in the output (KAPITALFREIHEIT)."""
    pair_x, pair_y, _, _ = _lead_lag_pair(seed=7, lag=3)
    file_a = tmp_path / "btc.csv"
    file_b = tmp_path / "eth.csv"
    out_dir = tmp_path / "out"
    _write_pair_csv(file_a, *pair_x)
    _write_pair_csv(file_b, *pair_y)

    rc = c17_cli.main([
        "--file-a", str(file_a),
        "--file-b", str(file_b),
        "--pair", "BTC,ETH",
        "--windows", "2",
        "--surrogates", "120",
        "--lags", "2,3",
        "--seed", "42",
        "--out", str(out_dir),
    ])
    assert rc == 0

    json_path = out_dir / "c17_c41_results.json"
    md_path = out_dir / "c17_c41_results.md"
    assert json_path.exists() and md_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    # H-04 reference + capital-free flag.
    assert payload["hypothesis"] == "H-04"
    assert payload["hypothesis_registry"].endswith("hypothesis_registry.md")
    assert payload["capital_free"] is True
    assert payload["gate_thresholds"] == {
        "surrogate_p_max": 0.05,
        "min_windows": 2,
        "lead_symbol_stable_required": True,
    }
    # Per window: every gate criterion individually (surrogate p, FDR sig,
    # lead symbol, lag).
    assert payload["n_windows"] == 2
    assert len(payload["windows"]) == 2
    for window in payload["windows"]:
        criteria = window["criteria"]
        sp = criteria["surrogate_p"]
        assert "value" in sp and "threshold" in sp
        assert isinstance(sp["passed"], bool)
        assert isinstance(sp["fdr_significant"], bool)
        ls = criteria["lead_symbol"]
        assert ls["value"] in ("BTC", "ETH")
        assert "lag_ms" in ls
    # Injected lead is detected end-to-end through the CLI.
    assert payload["all_windows_pass"] is True
    assert payload["lead_symbols"] == ["BTC", "BTC"]

    md = md_path.read_text(encoding="utf-8")
    assert "H-04" in md
    assert "hypothesis_registry.md" in md
    for window_index in (0, 1):
        assert f"## Fenster {window_index}" in md
    for label in ("Surrogate p", "Lead-Symbol"):
        assert label in md

    # KAPITALFREIHEIT (hard): the gate is existence-only — no tradability
    # field/column may appear. We check DATA carriers (JSON keys, MD table
    # headers), NOT the KAPITALFREI disclaimer prose which legitimately NEGATES
    # these words ("KEINE bps/Edge/PnL/Friction-Metrik").
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

    # MD table headers (lines starting with '|') must carry no tradability column.
    for line in md.splitlines():
        if line.lstrip().startswith("|"):
            low = line.lower()
            for word in forbidden:
                assert word not in low, (
                    f"KAPITALFREIHEIT violated: tradability column in MD: {line!r}"
                )


def test_driver_cli_missing_file_exits_nonzero(tmp_path: Path) -> None:
    """Data defect (missing input) -> exit code 1, no JSON written."""
    rc = c17_cli.main([
        "--file-a", str(tmp_path / "missing_a.csv"),
        "--file-b", str(tmp_path / "missing_b.csv"),
        "--out", str(tmp_path / "out"),
    ])
    assert rc == 1
    assert not (tmp_path / "out" / "c17_c41_results.json").exists()


def test_module_source_has_no_tradability_logic() -> None:
    """KAPITALFREIHEIT, static: the module CODE must carry no tradability
    identifiers (bps / edge_bps / friction / pnl / sharpe / net_edge /
    tradable). Docstring/comment prose that explicitly NEGATES these (e.g. "NO
    friction / edge / bps logic") is allowed; a real tradability metric is a
    bug. We scan code lines only, with comments and string/docstring lines
    stripped out."""
    import re

    pkg_dir = Path(__file__).resolve().parents[2] / (
        "src/bybit_edge/research/c17_c41_lead_lag"
    )
    assert pkg_dir.is_dir(), pkg_dir
    # Specific code tokens that would signal a tradability metric in the gate
    # (deliberately narrow: 'edge_bps'/'net_edge' not bare 'edge', so the word
    # cannot match a comment fragment that survived stripping).
    leak = re.compile(
        r"\b(bps|edge_bps|friction|pnl|sharpe|net_edge|tradable)\b", re.IGNORECASE
    )
    # Strip docstrings, comments and string LITERALS — only bare code
    # identifiers remain. A tradability metric would surface as a real
    # identifier (variable / key / field); the words inside disclaimer strings
    # ("KEINE bps/Edge/PnL/Friction-Metrik") and docstrings are intentional
    # negations and must not trip the check.
    str_literal = re.compile(r"'''.*?'''|\"\"\".*?\"\"\"|'[^']*'|\"[^\"]*\"", re.DOTALL)
    py_files = sorted(pkg_dir.glob("*.py"))
    assert py_files, "no module sources found"
    for py in py_files:
        src = py.read_text(encoding="utf-8")
        # Drop multi-line docstrings / string literals wholesale first.
        code_only = str_literal.sub(" ", src)
        for lineno, raw in enumerate(code_only.splitlines(), 1):
            code = raw.split("#", 1)[0]
            assert not leak.search(code), (
                f"tradability token in {py.name}:{lineno}: {code!r}"
            )


# ===========================================================================
# 9. Grid synchronisation: different tick timestamps -> common grid
# ===========================================================================

def test_align_returns_resamples_to_common_grid() -> None:
    """Two streams with DIFFERENT tick timestamps resample to equal-length,
    aligned return series on a shared grid (the precondition for a meaningful
    fixed integer lag = lag * grid_ms)."""
    rng = np.random.default_rng(2)
    # Symbol A: ~120 ticks; Symbol B: ~80 ticks; both over the same 60 s span
    # but at unrelated timestamps.
    ts_a = T0_MS + np.sort(rng.uniform(0.0, 60_000.0, size=120))
    ts_b = T0_MS + np.sort(rng.uniform(0.0, 60_000.0, size=80))
    px_a = 50_000.0 * np.exp(np.cumsum(rng.normal(0.0, 1e-4, size=120)))
    px_b = 3_000.0 * np.exp(np.cumsum(rng.normal(0.0, 1e-4, size=80)))

    ret_a, ret_b = align_returns(ts_a, px_a, ts_b, px_b, GRID_MS)

    assert ret_a.size == ret_b.size, "aligned series have different lengths"
    assert ret_a.size > 0
    # The grid spans the OVERLAP of both series (~60 s at 1 s bars -> ~58 rets).
    assert ret_a.size >= 50


def test_resample_log_returns_step_sampling_is_backward_looking() -> None:
    """Last tick wins per bar and empty bars forward-fill — strictly backward
    looking (no look-ahead across a bar edge), length == n_bars - 1."""
    # Three ticks placed so bar 0 has two ticks (last wins) and bar 2 is empty.
    ts = T0_MS + np.array([100.0, 900.0, 1_100.0, 3_100.0])
    px = np.array([100.0, 110.0, 121.0, 133.1])
    edges, log_ret = resample_log_returns(ts, px, GRID_MS)
    # Bar 0 last price 110, bar 1 -> 121, bar 2 empty -> ffill 121, bar 3 -> 133.1.
    assert log_ret.size == edges.size - 1
    assert log_ret.size >= 3
    # Empty bar 2 forward-fills -> zero return across it.
    assert log_ret[1] == pytest.approx(0.0, abs=1e-9)
    assert np.all(np.isfinite(log_ret))


def test_align_returns_no_overlap_returns_empty() -> None:
    """Disjoint time ranges -> no common grid -> empty (never a phantom lag)."""
    ts_a = T0_MS + np.array([0.0, 1_000.0, 2_000.0])
    ts_b = T0_MS + np.array([10_000.0, 11_000.0, 12_000.0])
    px = np.array([1.0, 1.1, 1.2])
    ret_a, ret_b = align_returns(ts_a, px, ts_b, px, GRID_MS)
    assert ret_a.size == 0 and ret_b.size == 0
