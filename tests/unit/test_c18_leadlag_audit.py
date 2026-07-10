"""WP-1-VERIFY (T0, SANDBOX) — tests for the H-18 GL-006/H-04 lead-lag
high-N-surrogate RESOLUTION AUDIT (Welle 5).

Covers ``src/bybit_edge/research/c18_leadlag_audit/`` (registry:
``scinance2-impl/state/hypothesis_registry.md`` H-18; base gate
``scinance2-impl/state/gate_log.md`` GL-006). H-18 is NOT a new hypothesis —
it is a re-execution of the byte-identical, already-adjudicated F-LEADLAG
pipeline (``c17_c41_lead_lag``) with exactly one change: ``n_surrogates`` 200
-> 100_000, evaluated via GPU-capable tensor batches. The GL-006 verdict is
NEVER touched by this module or these tests.

Sandbox constraint (no torch, no GPU): the tests below verify METHODOLOGY
CORRECTNESS at small N via the ``numpy`` backend, with the single most
important test being the EQUIVALENCE PROOF against the original
``c17_c41_lead_lag`` module — same synthetic input, same methodology,
N=200 -> the two pipelines must agree.

1. **Methodology equivalence (most important):** ``run_equivalence_selftest``
   against the ORIGINAL c17_c41_lead_lag pipeline. Because the circular-shift
   offsets are drawn with the EXACT same sequential RNG consumption
   (``generate_shift_offsets`` replicates ``_circular_shift`` call-by-call),
   the surrogate ensembles — and therefore the p-values — must be EXACTLY
   equal on the numpy backend, not just "statistically similar". TE/WCOH
   point estimates must match to float64 precision (same formulas,
   vectorised).
2. Phase-shuffle surrogates preserve the amplitude spectrum exactly (the
   registry-named ``torch.fft.rfft/irfft`` primitive, IAAFT-style check).
3. Permutation surrogates preserve the marginal (multiset of values).
4. T1/T2 payload fields computed correctly on a constructed example.
5. ``--check-gpu-only`` honestly reports absence of CUDA in the sandbox
   (rc=3) and never fabricates a positive GPU claim.
6. Every N=200 (or any non-verdict-carrying) run is explicitly marked
   "equivalence test / not a resolution audit", never as a T1/T2 result.
7. Module import works WITHOUT torch (honest degradation, registry
   requirement).
8. Batched TE / WCOH numerically match the original point estimators
   directly (not only through the surrogate wrapper).
9. Driver E2E on a synthetic pair -> JSON + MD, correct schema, KAPITALFREI.
10. capital_free token scan (static + payload keys), reused BH-FDR identity
    (no drift from the original F-LEADLAG family), backend resolution logic,
    GL-006 baseline integrity (12 Stage-1 survivors).

Runtime budget: everything here uses small N (80-500 surrogates) and short
synthetic series — T0/SANDBOX. The binding H-18 100k-surrogate run is T3
(handoff_local, real GPU).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

import scripts.c18_leadlag_audit as c18_cli
from bybit_edge.research.c17_c41_lead_lag.surrogate import (
    benjamini_hochberg as orig_benjamini_hochberg,
)
from bybit_edge.research.c17_c41_lead_lag.surrogate import (
    surrogate_test_te as orig_surrogate_test_te,
)
from bybit_edge.research.c17_c41_lead_lag.surrogate import (
    surrogate_test_wcoh as orig_surrogate_test_wcoh,
)
from bybit_edge.research.c17_c41_lead_lag.transfer_entropy import (
    transfer_entropy as orig_transfer_entropy,
)
from bybit_edge.research.c17_c41_lead_lag.transfer_entropy import (
    wavelet_coherence_lead as orig_wavelet_coherence_lead,
)

from bybit_edge.research.c18_leadlag_audit import stats as c18_stats
from bybit_edge.research.c18_leadlag_audit.driver import (
    FULL_RESOLUTION_N_SURROGATES,
    generate_synthetic_lead_lag_pair,
    gpu_status,
    render_markdown,
    run,
    run_equivalence_selftest,
    write_outputs,
)
from bybit_edge.research.c18_leadlag_audit.surrogate_gpu import (
    generate_shift_offsets,
    permutation_surrogates,
    phase_shuffle_surrogates,
    resolve_backend,
    torch_cuda_available,
)
from bybit_edge.research.c18_leadlag_audit.te_batched import transfer_entropy_batch
from bybit_edge.research.c18_leadlag_audit.wcoh_batched import (
    wavelet_coherence_lead_batch,
)

T0_MS = 1_700_000_000_000.0
GRID_MS = 1000.0


def _ticks_from_log_returns(log_ret: np.ndarray, p0: float, grid_ms: float = GRID_MS):
    px = p0 * np.exp(np.concatenate([[0.0], np.cumsum(log_ret)]))
    n = px.size
    ts = T0_MS + (np.arange(n) + 0.5) * grid_ms
    return ts, px


# ===========================================================================
# 1. Methodology equivalence against the ORIGINAL c17_c41_lead_lag pipeline
#    (the most important test in this file)
# ===========================================================================

def test_equivalence_selftest_holds_against_original_pipeline():
    """``run_equivalence_selftest`` at N=200 must report ``equivalence_holds``.

    Same synthetic lead-lag input through BOTH pipelines: TE/WCOH point
    estimates within 1e-6, and — because the circular-shift offsets are
    drawn with the SAME sequential RNG consumption as the original serial
    loop — the surrogate p-values must be EXACTLY equal (not merely close).
    """
    result = run_equivalence_selftest(
        seed=7, n_bars=900, lag=3, lags=(2, 3), n_surrogates=200,
        surrogate_seed=42, backend="numpy",
    )
    assert result["mode"] == "equivalence_selftest"
    assert result["not_a_resolution_audit"] is True
    assert "kein Aufloesungs-Audit" in result["note"] or "Aequivalenz" in result["note"]

    assert result["all_point_estimates_match"] is True, result["variants"]
    assert result["all_p_values_exact_match"] is True, [
        (v["label"], v["p_original"], v["p_batched"]) for v in result["variants"]
    ]
    assert result["equivalence_holds"] is True

    for v in result["variants"]:
        assert v["point_estimate_abs_diff"] < 1e-6, v
        assert v["p_original"] == pytest.approx(v["p_batched"], abs=0.0), v
        # The surrogate ENSEMBLE itself (not just the p-value) is bit-identical
        # on the numpy backend, because both pipelines consume the RNG
        # identically for the shift offsets.
        assert v["surrogate_stats_bit_identical"] or v["point_estimate_abs_diff"] < 1e-9, v


def test_equivalence_selftest_detects_a_broken_pipeline():
    """Sanity-negative: if the batched TE disagreed with the original, the
    self-test would catch it. We simulate this by comparing a batched TE run
    with a DIFFERENT n_bins against the original — the point estimates must
    then legitimately differ (proves the comparison is not vacuously True)."""
    source, target = generate_synthetic_lead_lag_pair(seed=7, n_bars=900, lag=3)
    te_orig = orig_transfer_entropy(source, target, 3, n_bins=3)
    te_batch_wrong_bins = float(
        transfer_entropy_batch(source[None, :], target, 3, n_bins=5, backend="numpy")[0]
    )
    assert te_orig != pytest.approx(te_batch_wrong_bins, abs=1e-9), (
        "comparison is vacuous: different n_bins must yield different TE"
    )


def test_batched_te_matches_original_point_estimate_directly():
    """``transfer_entropy_batch`` vs the original ``transfer_entropy``, over
    several lags/seeds — direct point-estimator equivalence (no surrogate
    machinery involved)."""
    for seed in (1, 7, 23):
        source, target = generate_synthetic_lead_lag_pair(seed=seed, n_bars=700, lag=2)
        for lag in (1, 2, 3, 5):
            orig = orig_transfer_entropy(source, target, lag, n_bins=3)
            batch = float(
                transfer_entropy_batch(source[None, :], target, lag, n_bins=3, backend="numpy")[0]
            )
            assert batch == pytest.approx(orig, abs=1e-9), (seed, lag, orig, batch)


def test_batched_te_matches_original_over_a_batch_of_rows():
    """A REAL batch (B > 1 rows) must match the original applied row-by-row —
    this is the actual GPU-necessity code path (many surrogates at once)."""
    rng = np.random.default_rng(11)
    n = 500
    target = rng.normal(0.0, 1e-3, size=n)
    batch = np.stack([rng.normal(0.0, 1e-3, size=n) for _ in range(6)])

    batched_out = transfer_entropy_batch(batch, target, 3, n_bins=3, backend="numpy")
    for i in range(batch.shape[0]):
        row_orig = orig_transfer_entropy(batch[i], target, 3, n_bins=3)
        assert batched_out[i] == pytest.approx(row_orig, abs=1e-9), i


def test_batched_wcoh_matches_original_point_estimate():
    """``wavelet_coherence_lead_batch`` vs the original
    ``wavelet_coherence_lead`` — same scales/formulas, must agree closely."""
    source, target = generate_synthetic_lead_lag_pair(seed=7, n_bars=900, lag=3)
    lead_orig, coh_orig = orig_wavelet_coherence_lead(source, target, GRID_MS)
    leads, cohs = wavelet_coherence_lead_batch(source[None, :], target, GRID_MS, backend="numpy")
    assert float(cohs[0]) == pytest.approx(coh_orig, abs=1e-6)
    assert float(leads[0]) == pytest.approx(lead_orig, abs=1e-3)


def test_shift_offsets_replicate_original_rng_consumption_exactly():
    """``generate_shift_offsets`` must draw bit-identical offsets to the
    original ``_circular_shift`` loop's sequential RNG consumption."""
    from bybit_edge.research.c17_c41_lead_lag.surrogate import (
        MIN_SHIFT_FRACTION,
    )

    n, n_surrogates, seed = 500, 50, 123
    lo = max(1, int(MIN_SHIFT_FRACTION * n))
    hi = n - lo
    rng = np.random.default_rng(seed)
    expected = np.array([int(rng.integers(lo, hi)) for _ in range(n_surrogates)])

    got = generate_shift_offsets(n, n_surrogates, seed)
    assert np.array_equal(got, expected)


def test_batch_circular_shift_matches_np_roll_per_row():
    """``batch_circular_shift`` row ``i`` must equal ``np.roll(x, offsets[i])``
    exactly — this is the identity the equivalence proof depends on."""
    from bybit_edge.research.c18_leadlag_audit.surrogate_gpu import batch_circular_shift

    rng = np.random.default_rng(3)
    x = rng.normal(size=64)
    offsets = np.array([0, 1, 5, 30, 63])
    out = batch_circular_shift(x, offsets, backend="numpy")
    for i, s in enumerate(offsets):
        assert np.array_equal(out[i], np.roll(x, int(s)))


# ===========================================================================
# 2. Phase-shuffle surrogates preserve the amplitude spectrum (IAAFT-style)
# ===========================================================================

def test_phase_shuffle_preserves_amplitude_spectrum():
    """Registry-named ``rfft``/``irfft`` phase-shuffle primitive: every
    surrogate row must have the SAME amplitude spectrum as the input (only
    phases randomised)."""
    rng = np.random.default_rng(5)
    x = rng.normal(size=256) + 0.5 * np.sin(np.linspace(0, 20 * np.pi, 256))
    surr = phase_shuffle_surrogates(x, n_surrogates=20, seed=1, backend="numpy")

    amp_x = np.abs(np.fft.rfft(x))
    for row in surr:
        amp_row = np.abs(np.fft.rfft(row))
        assert amp_row == pytest.approx(amp_x, abs=1e-8), "amplitude spectrum not preserved"
    # Real output (irfft), matching input length.
    assert surr.shape == (20, x.size)
    assert np.all(np.isfinite(surr))


def test_phase_shuffle_randomises_phase_not_a_no_op():
    """A surrogate must actually differ from the input in the TIME domain
    (phases really randomised, not silently identity)."""
    rng = np.random.default_rng(5)
    x = rng.normal(size=256)
    surr = phase_shuffle_surrogates(x, n_surrogates=5, seed=1, backend="numpy")
    for row in surr:
        assert not np.allclose(row, x)


def test_phase_shuffle_deterministic_given_seed():
    rng = np.random.default_rng(9)
    x = rng.normal(size=128)
    a = phase_shuffle_surrogates(x, n_surrogates=10, seed=77, backend="numpy")
    b = phase_shuffle_surrogates(x, n_surrogates=10, seed=77, backend="numpy")
    assert np.array_equal(a, b)


# ===========================================================================
# 3. Permutation surrogates preserve the marginal
# ===========================================================================

def test_permutation_surrogates_preserve_marginal():
    """Registry-named argsort-of-uniform-keys permutation primitive: every
    surrogate row must be a PERMUTATION of the input (same multiset)."""
    rng = np.random.default_rng(4)
    x = rng.normal(size=100)
    surr = permutation_surrogates(x, n_surrogates=15, seed=2, backend="numpy")
    x_sorted = np.sort(x)
    for row in surr:
        assert np.array_equal(np.sort(row), x_sorted)
    # Not the identity permutation for every row (destroys temporal structure).
    assert not all(np.array_equal(row, x) for row in surr)


# ===========================================================================
# 4. T1 / T2 payload fields — constructed example
# ===========================================================================

def _make_windows_from_baseline(overrides: dict) -> list[dict]:
    """Build a ``windows`` payload (as ``run()`` would emit it) starting from
    the GL-006 baseline and applying ``overrides[(window_idx, label)] =
    {"p_value": ..., "fdr_significant": ...}`` for specific cells."""
    windows = []
    for bw in c18_stats.GL006_BASELINE["windows"]:
        variants = []
        p_values = []
        for label, v in bw["variants"].items():
            ov = overrides.get((bw["index"], label), {})
            p_value = ov.get("p_value", v["p_value"])
            entry = {
                "axis": "WCOH" if label.startswith("WCOH") else "TE",
                "label": label,
                "surrogate": {
                    "observed_stat": v["observed_stat"],
                    "p_value": p_value,
                    "n_surrogates": ov.get("n_surrogates", 100_000),
                },
                "fdr_significant": ov.get("fdr_significant", v["fdr_significant"]),
            }
            variants.append(entry)
            p_values.append(p_value)
        p_crit = ov_p_crit = overrides.get((bw["index"], "__p_crit__"), bw["p_crit"])
        windows.append({
            "index": bw["index"],
            "n_bars": bw["n_bars"],
            "t0_ms": bw["t0_ms"],
            "t1_ms": bw["t1_ms"],
            "variants": variants,
            "criteria": {"fdr_p_crit": p_crit},
        })
    return windows


def test_t1_holds_when_all_survivors_reproduce_at_high_resolution():
    """T1 constructed-positive: every Stage-1 survivor gets a tiny new p and
    stays FDR-significant -> ``t1_holds`` True, zero drifting survivors."""
    overrides = {}
    for widx, label in c18_stats.STAGE1_SURVIVORS:
        overrides[(widx, label)] = {"p_value": 1e-5, "fdr_significant": True}
    windows = _make_windows_from_baseline(overrides)
    t1 = c18_stats.evaluate_t1(windows, n_surrogates=100_000)

    assert t1["t1_holds"] is True
    assert t1["drifting_survivors"] == []
    assert t1["n_holding"] == t1["n_survivors"] == 12
    for cell in t1["cells"]:
        assert cell["holds"] is True
        assert cell["p_le_threshold"] is True
        assert cell["p_new"] <= c18_stats.T1_P_MAX


def test_t1_flags_a_drifting_survivor_without_touching_gl006():
    """T1 constructed-negative: ONE survivor drifts (p_new above threshold)
    -> that cell does not hold, is listed in ``drifting_survivors``, t1_holds
    False — but nothing here claims GL-006 itself is falsified (the payload
    carries the non-verdict clause text, asserted separately below)."""
    widx, label = c18_stats.STAGE1_SURVIVORS[0]
    overrides = {(widx, label): {"p_value": 0.02, "fdr_significant": False}}
    for w, lab in c18_stats.STAGE1_SURVIVORS[1:]:
        overrides[(w, lab)] = {"p_value": 1e-5, "fdr_significant": True}
    windows = _make_windows_from_baseline(overrides)
    t1 = c18_stats.evaluate_t1(windows, n_surrogates=100_000)

    assert t1["t1_holds"] is False
    assert len(t1["drifting_survivors"]) == 1
    assert f"w{widx}:{label}" in t1["drifting_survivors"]
    assert t1["n_holding"] == 11
    assert "NICHT das GL-006-Verdikt" in t1["non_verdict_clause"]


def test_t2_resolves_when_far_from_p_crit():
    """T2 constructed-positive: both decision cells sit > 5 MC-SE from
    p_crit -> t2_holds True, both cells resolved=True."""
    n_surrogates = 100_000
    # p_crit fixed at 0.02; put the cells' p far below it (many SEs away).
    overrides = {(0, "__p_crit__"): 0.02}
    for widx, label in c18_stats.T2_CELLS:
        overrides[(widx, label)] = {"p_value": 1e-5, "fdr_significant": True}
    windows = _make_windows_from_baseline(overrides)
    t2 = c18_stats.evaluate_t2(windows, n_surrogates=n_surrogates)

    assert t2["t2_holds"] is True
    for cell in t2["cells"]:
        assert cell["resolved"] is True
        assert cell["distance_se"] > c18_stats.T2_MIN_SE_DISTANCE


def test_t2_stays_unresolved_when_close_to_p_crit():
    """T2 constructed-negative: a decision cell sits WITHIN 5 MC-SE of
    p_crit (mirrors today's <1-MC-SE undecidability) -> not resolved,
    t2_holds False."""
    n_surrogates = 100_000
    se = c18_stats.mc_standard_error(0.02, n_surrogates)
    p_crit = 0.02
    close_p = p_crit + 0.5 * se  # well within the 5-SE resolution band
    overrides = {
        (0, "__p_crit__"): p_crit,
        (0, c18_stats.T2_CELLS[0][1]): {"p_value": close_p, "fdr_significant": False},
        (0, c18_stats.T2_CELLS[1][1]): {"p_value": 1e-5, "fdr_significant": True},
    }
    windows = _make_windows_from_baseline(overrides)
    t2 = c18_stats.evaluate_t2(windows, n_surrogates=n_surrogates)

    assert t2["t2_holds"] is False
    cell0 = t2["cells"][0]
    assert cell0["resolved"] is False
    assert cell0["distance_se"] < c18_stats.T2_MIN_SE_DISTANCE


def test_mc_standard_error_formula():
    assert c18_stats.mc_standard_error(0.005, 200) == pytest.approx(
        (0.005 * 0.995 / 200) ** 0.5
    )
    assert c18_stats.mc_standard_error(0.0, 100) == 0.0
    assert c18_stats.mc_standard_error(0.5, 0) == float("inf")


def test_gl006_baseline_has_exactly_12_stage1_survivors():
    """Data-integrity guard: the transcribed baseline must reproduce GL-006's
    documented '12 von 22 Varianten ueberleben' (8 in F0 + 4 in F1)."""
    assert len(c18_stats.STAGE1_SURVIVORS) == 12
    f0 = [x for x in c18_stats.STAGE1_SURVIVORS if x[0] == 0]
    f1 = [x for x in c18_stats.STAGE1_SURVIVORS if x[0] == 1]
    assert len(f0) == 8
    assert len(f1) == 4


def test_compare_windows_to_baseline_detects_match_and_mismatch():
    windows_match = _make_windows_from_baseline({})
    cmp_ok = c18_stats.compare_windows_to_baseline(windows_match)
    assert cmp_ok["all_windows_match_gl006"] is True

    windows_bad = _make_windows_from_baseline({})
    windows_bad[0]["n_bars"] = 999999
    cmp_bad = c18_stats.compare_windows_to_baseline(windows_bad)
    assert cmp_bad["all_windows_match_gl006"] is False


# ===========================================================================
# 5. --check-gpu-only honesty + verdict-carrying gating
# ===========================================================================

def test_gpu_status_never_fabricates_cuda():
    status = gpu_status("auto")
    assert status["cuda_available"] == torch_cuda_available()
    if not status["torch_available"]:
        assert status["cuda_available"] is False
        assert status["resolved_backend"] == "numpy"
    assert status["full_resolution_n_surrogates"] == FULL_RESOLUTION_N_SURROGATES


def test_check_gpu_only_cli_exit_code_matches_cuda_availability():
    rc = c18_cli.main(["--check-gpu-only"])
    expected = 0 if torch_cuda_available() else 3
    assert rc == expected


def test_resolve_backend_auto_never_raises_without_torch():
    # Must not raise even when torch is completely absent (honest degrade).
    backend = resolve_backend("auto")
    assert backend in ("numpy", "torch-cpu", "torch-cuda")


def test_resolve_backend_explicit_cuda_request_raises_when_unavailable():
    if torch_cuda_available():
        pytest.skip("real CUDA device present — explicit request would succeed")
    with pytest.raises(RuntimeError):
        resolve_backend("cuda")


def test_resolve_backend_numpy_always_available():
    assert resolve_backend("numpy") == "numpy"


def test_resolve_backend_unknown_raises():
    with pytest.raises(RuntimeError):
        resolve_backend("quantum")


def test_verdict_carrying_false_without_cuda_regardless_of_n():
    """A full-resolution run() call in THIS sandbox (no CUDA) must be
    honestly marked verdict_carrying=False, and its mode must NOT claim a
    completed resolution audit."""
    pair_x, pair_y = _independent_pair(seed=3, n_bars=400)
    payload = run(
        pair_x, pair_y, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, n_surrogates=FULL_RESOLUTION_N_SURROGATES // 1000,  # small for speed
        lags=(2,), grid_ms=GRID_MS, seed=42, backend="auto",
    )
    assert payload["verdict_carrying"] is False
    assert payload["mode"] == "partial_or_equivalence_run"
    reason = payload["verdict_carrying_reason"].lower()
    assert "verdikt-tragend" in reason and "cuda" in reason


def _independent_pair(seed: int, n_bars: int = 400, sigma: float = 1e-3):
    rng = np.random.default_rng(seed)
    rx = rng.normal(0.0, sigma, size=n_bars)
    ry = rng.normal(0.0, sigma, size=n_bars)
    return (
        _ticks_from_log_returns(rx, 50_000.0),
        _ticks_from_log_returns(ry, 3_000.0),
    )


# ===========================================================================
# 6. Driver E2E — synthetic pair -> JSON + MD (KAPITALFREIHEIT + schema)
# ===========================================================================

def test_driver_e2e_synthetic_pair_non_gl006_skips_t1_t2(tmp_path: Path):
    """A non-BTCUSDT/ETHUSDT pair must SKIP T1/T2 (not the registered
    F-LEADLAG setup) rather than silently computing bogus claims."""
    rng = np.random.default_rng(7)
    n = 700
    rx = rng.normal(0.0, 1e-3, size=n)
    ry = np.zeros(n)
    lag = 3
    ry[lag:] = 0.85 * rx[:-lag] + 2e-4 * rng.normal(size=n - lag)
    pair_x = _ticks_from_log_returns(rx, 50_000.0)
    pair_y = _ticks_from_log_returns(ry, 3_000.0)

    payload = run(
        pair_x, pair_y, symbol_a="XSYM", symbol_b="YSYM",
        n_windows=2, n_surrogates=100, lags=(2, 3), grid_ms=GRID_MS, seed=42,
        backend="numpy", source="synthetic-fixture",
    )
    assert payload["audit_id"] == "H-18"
    assert payload["base_gate"] == "GL-006"
    assert payload["base_hypothesis"] == "H-04"
    assert payload["capital_free"] is True
    assert payload["t1_partial_claim"]["t1_holds"] is None
    assert payload["t2_partial_claim"]["t2_holds"] is None
    assert payload["data_binding_vs_gl006"]["all_windows_match_gl006"] is None
    assert payload["mode"] == "partial_or_equivalence_run"

    json_path, md_path = write_outputs(payload, tmp_path / "out")
    assert json_path.exists() and md_path.exists()
    reloaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert reloaded["audit_id"] == "H-18"

    md = md_path.read_text(encoding="utf-8")
    assert "H-18" in md
    assert "AUFLOESUNGS-AUDIT" in md
    assert "GL-006" in md


def test_driver_e2e_gl006_pair_populates_t1_t2(tmp_path: Path):
    """The registered BTCUSDT/ETHUSDT/default-grid/default-lags setup DOES
    populate T1/T2 (even if inconclusive at low N/no-CUDA — the fields must
    exist and be well-formed)."""
    rng = np.random.default_rng(3)
    n = 700
    rx = rng.normal(0.0, 1e-3, size=n)
    ry = np.zeros(n)
    lag = 3
    ry[lag:] = 0.8 * rx[:-lag] + 2e-4 * rng.normal(size=n - lag)
    pair_x = _ticks_from_log_returns(rx, 50_000.0)
    pair_y = _ticks_from_log_returns(ry, 3_000.0)

    payload = run(
        pair_x, pair_y, symbol_a="BTCUSDT", symbol_b="ETHUSDT",
        n_windows=2, n_surrogates=50, backend="numpy", seed=42,
    )
    # Default lags/grid/n_bins used -> GL-006 setup recognised.
    assert payload["t1_partial_claim"]["cells"], "T1 should be evaluated for the GL-006 pair"
    assert payload["t2_partial_claim"]["cells"], "T2 should be evaluated for the GL-006 pair"
    assert isinstance(payload["t1_partial_claim"]["t1_holds"], bool)
    assert isinstance(payload["t2_partial_claim"]["t2_holds"], bool)
    assert payload["data_binding_vs_gl006"]["all_windows_match_gl006"] is not None


def test_render_markdown_contains_non_verdict_clause(tmp_path: Path):
    pair_x, pair_y = _independent_pair(seed=1, n_bars=300)
    payload = run(
        pair_x, pair_y, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, n_surrogates=30, lags=(2,), grid_ms=GRID_MS, seed=1,
        backend="numpy",
    )
    md = render_markdown(payload)
    assert "KEINE NEU-ADJUDIKATION" in md
    assert "GL-006" in md
    assert "gate_log.md" in md


# ===========================================================================
# 7. Module import works WITHOUT torch (honest degradation)
# ===========================================================================

def test_module_imports_without_torch():
    """The package must be fully importable in an environment with no torch
    installed (this sandbox) — a hard import-time dependency on torch would
    violate the registry's sandbox constraint."""
    import bybit_edge.research.c18_leadlag_audit as pkg

    assert hasattr(pkg, "run")
    assert hasattr(pkg, "gpu_status")
    assert hasattr(pkg, "run_equivalence_selftest")


# ===========================================================================
# 8. capital_free / F-LEADLAG identity / no drift from the original module
# ===========================================================================

def test_bh_fdr_is_the_identical_imported_function_not_a_copy():
    """The FDR machinery MUST be the literal original function object
    (imported, not re-implemented) so the two pipelines cannot drift apart."""
    from bybit_edge.research.c18_leadlag_audit.stats import benjamini_hochberg

    assert benjamini_hochberg is orig_benjamini_hochberg


def test_module_source_has_no_tradability_logic():
    """KAPITALFREIHEIT, static: c18_leadlag_audit CODE must carry no
    tradability identifiers. Docstring prose that explicitly NEGATES these is
    allowed; a real tradability metric is a bug."""
    pkg_dir = Path(__file__).resolve().parents[2] / "src/bybit_edge/research/c18_leadlag_audit"
    assert pkg_dir.is_dir(), pkg_dir
    leak = re.compile(
        r"\b(bps|edge_bps|friction|pnl|sharpe|net_edge|tradable)\b", re.IGNORECASE
    )
    str_literal = re.compile(r"'''.*?'''|\"\"\".*?\"\"\"|'[^']*'|\"[^\"]*\"", re.DOTALL)
    py_files = sorted(pkg_dir.glob("*.py"))
    assert py_files, "no module sources found"
    for py in py_files:
        src = py.read_text(encoding="utf-8")
        code_only = str_literal.sub(" ", src)
        for lineno, raw in enumerate(code_only.splitlines(), 1):
            code = raw.split("#", 1)[0]
            assert not leak.search(code), f"tradability token in {py.name}:{lineno}: {code!r}"


def test_scripts_source_has_no_tradability_logic():
    script_path = Path(__file__).resolve().parents[2] / "scripts/c18_leadlag_audit.py"
    assert script_path.is_file()
    leak = re.compile(
        r"\b(bps|edge_bps|friction|pnl|sharpe|net_edge|tradable)\b", re.IGNORECASE
    )
    str_literal = re.compile(r"'''.*?'''|\"\"\".*?\"\"\"|'[^']*'|\"[^\"]*\"", re.DOTALL)
    src = script_path.read_text(encoding="utf-8")
    code_only = str_literal.sub(" ", src)
    for lineno, raw in enumerate(code_only.splitlines(), 1):
        code = raw.split("#", 1)[0]
        assert not leak.search(code), f"tradability token in c18_leadlag_audit.py:{lineno}: {code!r}"


def test_payload_keys_carry_no_tradability_words(tmp_path: Path):
    pair_x, pair_y = _independent_pair(seed=2, n_bars=300)
    payload = run(
        pair_x, pair_y, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, n_surrogates=30, lags=(2,), grid_ms=GRID_MS, seed=1,
        backend="numpy",
    )
    forbidden = ("bps", "edge", "friction", "pnl", "sharpe", "tradab")

    def _all_keys(obj):
        keys = []
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


def test_capital_free_true_in_payload_and_gl006_reference_present():
    pair_x, pair_y = _independent_pair(seed=6, n_bars=300)
    payload = run(
        pair_x, pair_y, symbol_a="BTC", symbol_b="ETH",
        n_windows=2, n_surrogates=30, lags=(2,), grid_ms=GRID_MS, seed=1,
        backend="numpy",
    )
    assert payload["capital_free"] is True
    assert payload["base_gate"] == "GL-006"
    assert "gate_log.md" in payload["gate_log_not_written_by_this_module"]


def test_module_does_not_write_gate_log(tmp_path: Path):
    """Static guard: no source file in the package may reference writing to
    ``gate_log.md`` (open(...) / write_text against that path) — the
    Nicht-Verdikt-Klausel forbids self-adjudication."""
    pkg_dir = Path(__file__).resolve().parents[2] / "src/bybit_edge/research/c18_leadlag_audit"
    for py in sorted(pkg_dir.glob("*.py")):
        src = py.read_text(encoding="utf-8")
        # gate_log.md may be MENTIONED (as a string constant / doc) but never
        # opened for writing; a simple heuristic: no 'open(' call with
        # 'gate_log' in the same statement, and no '.write' chained near it.
        for lineno, line in enumerate(src.splitlines(), 1):
            if "gate_log" in line and ("open(" in line or ".write(" in line or "write_text(" in line):
                pytest.fail(f"possible gate_log.md write in {py.name}:{lineno}: {line!r}")


# ===========================================================================
# 9. CLI plumbing
# ===========================================================================

def test_cli_self_test_marks_equivalence_not_resolution_audit(tmp_path: Path):
    rc = c18_cli.main([
        "--self-test", "--seed", "7", "--surrogates", "150", "--out", str(tmp_path / "out"),
    ])
    assert rc == 0
    result = json.loads((tmp_path / "out" / "c18_leadlag_audit_selftest.json").read_text())
    assert result["mode"] == "equivalence_selftest"
    assert result["not_a_resolution_audit"] is True
    assert result["equivalence_holds"] is True
    md = (tmp_path / "out" / "c18_leadlag_audit_selftest.md").read_text()
    assert "Aequivalenz" in md


def test_cli_missing_source_exits_nonzero():
    rc = c18_cli.main(["--surrogates", "10"])
    assert rc == 1


def test_cli_missing_file_exits_nonzero(tmp_path: Path):
    rc = c18_cli.main([
        "--file-a", str(tmp_path / "missing_a.csv"),
        "--file-b", str(tmp_path / "missing_b.csv"),
        "--out", str(tmp_path / "out"),
    ])
    assert rc == 1
    assert not (tmp_path / "out" / "c18_leadlag_audit_results.json").exists()


def test_cli_explicit_cuda_backend_without_cuda_is_backend_error(tmp_path: Path):
    if torch_cuda_available():
        pytest.skip("real CUDA device present")
    import csv

    ts, px = _ticks_from_log_returns(np.random.default_rng(1).normal(0, 1e-3, size=100), 100.0)
    file_a = tmp_path / "a.csv"
    file_b = tmp_path / "b.csv"
    for f, (t, p) in ((file_a, (ts, px)), (file_b, (ts, px))):
        with f.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ts", "price"])
            for tt, pp in zip(t, p):
                w.writerow([f"{tt:.3f}", f"{pp:.4f}"])
    rc = c18_cli.main([
        "--file-a", str(file_a), "--file-b", str(file_b),
        "--backend", "cuda", "--surrogates", "10", "--windows", "2",
        "--out", str(tmp_path / "out"),
    ])
    assert rc == 2
