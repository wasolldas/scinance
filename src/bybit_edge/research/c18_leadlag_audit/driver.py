"""Orchestration for the H-18 GL-006/H-04 lead-lag resolution audit.

Registry contract (verbatim, see ``hypothesis_registry.md`` H-18 + gate log
GL-006): this is a RE-EXECUTION of the byte-identical, already-adjudicated
F-LEADLAG pipeline with EXACTLY ONE pre-declared change (``n_surrogates`` 200
-> 100_000). Everything reused from the original ``c17_c41_lead_lag`` package
(window splitting, grid alignment, BH-FDR, lag/axis/variant set, gate
thresholds) is imported directly — never re-implemented — so the two
pipelines cannot drift apart silently. Only the surrogate-ensemble evaluation
is swapped for the batched/GPU-capable implementation in ``te_batched`` /
``wcoh_batched``.

**Non-Verdikt-Klausel (verbindlich):** this module NEVER writes
``gate_log.md`` and NEVER changes a GL-006 field. It produces a payload/report
from which a NEW, separate GL entry (GL-014ff.) is created MANUALLY by the
gate-auditor. A drifting Stage-1 survivor only marks the standing GL-006
Messungen-WEITER as "aufloesungsbedingt fragil" in that payload — nothing
here is self-adjudicating.

**Compute-Gating-Pflicht:** a full run is only ``verdict_carrying`` when it
used >= 100_000 surrogates AND ran on a real ``torch-cuda`` backend. Every
other invocation (numpy fallback, torch-cpu, or fewer surrogates — e.g. the
sandbox's N=200 equivalence self-test) is honestly marked
``verdict_carrying: false`` with an explicit reason string, and its T1/T2
fields are computed for information only, never as a T1/T2 result.

KAPITALFREI: identical to GL-006 — no tradability logic anywhere.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# Byte-identical reuse of the original H-04 pipeline pieces (window split,
# grid alignment, loaders, DataError, gate thresholds, lag/bin defaults).
from bybit_edge.research.c17_c41_lead_lag.driver import (  # noqa: F401
    DEFAULT_GRID_MS,
    MIN_WINDOWS,
    SURROGATE_P_MAX,
    WINDOW_MAX_TICKS,
    DataError,
    load_pair_duckdb,
    load_trades_duckdb,
    load_trades_file,
    split_pair_windows,
)
from bybit_edge.research.c17_c41_lead_lag.surrogate import FDR_ALPHA, benjamini_hochberg
from bybit_edge.research.c17_c41_lead_lag.surrogate import surrogate_test_te as _orig_surrogate_test_te
from bybit_edge.research.c17_c41_lead_lag.surrogate import surrogate_test_wcoh as _orig_surrogate_test_wcoh
from bybit_edge.research.c17_c41_lead_lag.transfer_entropy import (
    DEFAULT_LAGS,
    DEFAULT_N_BINS,
    align_returns,
    transfer_entropy as _orig_transfer_entropy,
    wavelet_coherence_lead as _orig_wavelet_coherence_lead,
)

from .stats import (
    GL006_BASELINE,
    T1_P_MAX,
    T2_MIN_SE_DISTANCE,
    compare_windows_to_baseline,
    evaluate_t1,
    evaluate_t2,
)
from .surrogate_gpu import resolve_backend, torch_cuda_available
from .te_batched import surrogate_test_te_batched, transfer_entropy_batch
from .wcoh_batched import surrogate_test_wcoh_batched, wavelet_coherence_lead_batch

SCHEMA_VERSION = 1
AUDIT_ID = "H-18"
BASE_GATE = "GL-006"
BASE_HYPOTHESIS = "H-04"
HYPOTHESIS_REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
GATE_LOG_PATH = "scinance2-impl/state/gate_log.md"

#: The registered resolution target (registry H-18): 500x the GL-006 N=200.
FULL_RESOLUTION_N_SURROGATES = 100_000

#: The archived GL-006 window span (informational — for data-binding display).
GL006_SPAN_MS = tuple(
    (w["t0_ms"], w["t1_ms"]) for w in GL006_BASELINE["windows"]
)

NON_VERDICT_CLAUSE = (
    "H-18 ist KEINE neue empirische Hypothese, sondern ein Aufloesungs-Audit "
    "der bereits adjudizierten GL-006/H-04-Pipeline (n_surrogates 200 -> "
    "100.000). Das GL-006-Verdikt (WEITER, Mess-Existenz; Kapital-Status "
    "PARK) bleibt append-only UNVERAENDERT stehen. Ein abdriftender "
    "Stage-1-Survivor faelsifiziert NICHT GL-006 selbst — er markiert das "
    "stehende Messungen-WEITER als aufloesungsbedingt fragil (Audit-Finding). "
    "Dieses Modul schreibt NICHT gate_log.md; ein neuer, eigener GL-Eintrag "
    "(GL-014ff.) wird SPAETER manuell aus diesem Payload erstellt."
)


# ----------------------------------------------------------------------------
# GPU / backend status (compute-gating)
# ----------------------------------------------------------------------------

def gpu_status(requested_backend: str = "auto") -> dict[str, Any]:
    """Honest report of torch/CUDA availability — the ``--check-gpu-only`` body.

    Never raises for ``auto``: if torch is missing this reports
    ``torch_available: false`` and ``resolved_backend: "numpy"`` rather than
    crashing (the module must import and run methodology checks WITHOUT
    torch, per registry H-18 sandbox constraint).
    """
    try:
        import torch  # noqa: PLC0415

        torch_available = True
        torch_version = getattr(torch, "__version__", "unknown")
    except Exception:
        torch_available = False
        torch_version = None

    cuda_available = torch_cuda_available()
    device_name = None
    device_count = 0
    if cuda_available:
        try:
            import torch  # noqa: PLC0415

            device_count = int(torch.cuda.device_count())
            if device_count > 0:
                device_name = torch.cuda.get_device_name(0)
        except Exception:  # pragma: no cover - driver-level breakage
            pass

    try:
        resolved = resolve_backend(requested_backend)
        resolve_error = None
    except RuntimeError as exc:
        resolved = None
        resolve_error = str(exc)

    honest_note = (
        "echtes CUDA-Device gefunden — 100k-Surrogat-Aufloesungs-Audit "
        "verdikt-tragend moeglich"
        if cuda_available
        else (
            "KEIN echtes CUDA-Device — jeder Lauf in dieser Umgebung ist "
            "NICHT verdikt-tragend (Compute-Gating-Pflicht, registry H-18); "
            "nur als Methodik-Aequivalenz-Test bei kleinem N zulaessig"
        )
    )
    return {
        "requested_backend": requested_backend,
        "resolved_backend": resolved,
        "resolve_error": resolve_error,
        "torch_available": torch_available,
        "torch_version": torch_version,
        "cuda_available": cuda_available,
        "cuda_device_count": device_count,
        "cuda_device_name": device_name,
        "full_resolution_n_surrogates": FULL_RESOLUTION_N_SURROGATES,
        "honest_note": honest_note,
    }


def _verdict_carrying(n_surrogates: int, backend: str) -> tuple[bool, str]:
    if backend != "torch-cuda":
        return False, (
            f"backend='{backend}' ist kein echtes CUDA-Device — "
            "Compute-Gating-Pflicht (registry H-18): kein voller "
            "100k-Surrogat-Lauf ohne echtes CUDA-Device ist verdikt-tragend."
        )
    if n_surrogates < FULL_RESOLUTION_N_SURROGATES:
        return False, (
            f"n_surrogates={n_surrogates} < registrierte Aufloesung "
            f"{FULL_RESOLUTION_N_SURROGATES} — Teillauf, nicht das "
            "vorregistrierte Aufloesungs-Audit."
        )
    return True, "voller 100k-Surrogat-Lauf auf echtem CUDA-Device."


# ----------------------------------------------------------------------------
# Per-window pipeline (byte-identical variant/label/order to c17_c41_lead_lag)
# ----------------------------------------------------------------------------

def run_window(
    index: int,
    pair_a: tuple[np.ndarray, np.ndarray],
    pair_b: tuple[np.ndarray, np.ndarray],
    *,
    symbol_a: str,
    symbol_b: str,
    lags: tuple[int, ...],
    n_bins: int,
    grid_ms: float,
    n_surrogates: int,
    seed: int,
    n_windows: int,
    backend: str,
) -> dict[str, Any]:
    """One window of the F-LEADLAG family, batched/GPU-capable evaluation.

    Variant set, label strings, lead-symbol determination and BH-FDR are
    IDENTICAL to ``c17_c41_lead_lag.driver.run_window`` — only the surrogate
    evaluation itself is routed through the batched backend.
    """
    ts_a, px_a = pair_a
    ts_b, px_b = pair_b
    ret_a, ret_b = align_returns(ts_a, px_a, ts_b, px_b, grid_ms)
    n_bars = int(ret_a.size)

    print(
        f"[c18] window {index + 1}/{n_windows}: {n_bars} common bars "
        f"(grid {grid_ms:g}ms), lags={list(lags)}, {n_surrogates} "
        f"surrogates/variant, backend={backend}",
        file=sys.stderr, flush=True,
    )

    per_variant: list[dict[str, Any]] = []
    p_values: list[float] = []
    n_variants = 2 * len(lags) + 1

    vi = 0
    for lag in lags:
        for src_sym, dst_sym, src, dst in (
            (symbol_a, symbol_b, ret_a, ret_b),
            (symbol_b, symbol_a, ret_b, ret_a),
        ):
            vi += 1
            print(
                f"[c18] window {index + 1}/{n_windows} variant {vi}/{n_variants}: "
                f"TE {src_sym}->{dst_sym} lag={lag} — batched surrogate test...",
                file=sys.stderr, flush=True,
            )
            res = surrogate_test_te_batched(
                src, dst, lag, n_bins=n_bins,
                n_surrogates=n_surrogates, seed=seed + vi, backend=backend,
            )
            entry = {
                "axis": "TE",
                "label": f"TE_{src_sym}->{dst_sym}_lag{lag}",
                "lag": lag,
                "lag_ms": lag * grid_ms,
                "source": src_sym,
                "target": dst_sym,
                "surrogate": res.as_dict(),
            }
            per_variant.append(entry)
            p_values.append(res.p_value)
            print(
                f"[c18] window {index + 1}/{n_windows} variant {vi}/{n_variants}: "
                f"{entry['label']} done — TE={res.observed_stat:.5f} p={res.p_value:.6f}",
                file=sys.stderr, flush=True,
            )

    vi += 1
    print(
        f"[c18] window {index + 1}/{n_windows} variant {vi}/{n_variants}: "
        f"WCOH {symbol_a}/{symbol_b} — batched surrogate test...",
        file=sys.stderr, flush=True,
    )
    wres, lead_s = surrogate_test_wcoh_batched(
        ret_a, ret_b, grid_ms, n_surrogates=n_surrogates, seed=seed + vi, backend=backend,
    )
    lead_symbol_wcoh = symbol_a if lead_s > 0 else symbol_b
    wentry = {
        "axis": "WCOH",
        "label": f"WCOH_{symbol_a}/{symbol_b}",
        "lag": 0,
        "lag_ms": abs(lead_s) * 1000.0,
        "source": lead_symbol_wcoh,
        "target": symbol_b if lead_symbol_wcoh == symbol_a else symbol_a,
        "lead_seconds": float(lead_s),
        "surrogate": wres.as_dict(),
    }
    per_variant.append(wentry)
    p_values.append(wres.p_value)
    print(
        f"[c18] window {index + 1}/{n_windows} variant {vi}/{n_variants}: "
        f"{wentry['label']} done — coh={wres.observed_stat:.4f} "
        f"lead={lead_s:.3f}s (leader {lead_symbol_wcoh}) p={wres.p_value:.6f}",
        file=sys.stderr, flush=True,
    )

    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for entry, rej in zip(per_variant, rejected):
        entry["fdr_significant"] = bool(rej)

    survivors = [e for e in per_variant if e["fdr_significant"]]
    pool = survivors if survivors else per_variant
    best = min(
        pool,
        key=lambda e: (e["surrogate"]["p_value"], -e["surrogate"]["observed_stat"]),
    )
    best_p = best["surrogate"]["p_value"]

    te_survivors = [e for e in survivors if e["axis"] == "TE"]
    if te_survivors:
        lead_var = max(te_survivors, key=lambda e: e["surrogate"]["observed_stat"])
    elif survivors:
        lead_var = max(survivors, key=lambda e: e["surrogate"]["observed_stat"])
    else:
        lead_var = best
    lead_source = lead_var["source"]
    lead_lag_ms = lead_var["lag_ms"]

    criteria = {
        "surrogate_p": {
            "value": best_p,
            "threshold": SURROGATE_P_MAX,
            "fdr_significant": best["fdr_significant"],
            "passed": (best_p <= SURROGATE_P_MAX) and best["fdr_significant"],
            "registry_text": "identisch GL-006 (informativ — kein neues Verdikt, s. Nicht-Verdikt-Klausel)",
        },
        "lead_symbol": {
            "value": lead_source,
            "axis": lead_var["axis"],
            "variant": lead_var["label"],
            "lag_ms": lead_lag_ms,
        },
        "fdr_p_crit": p_crit,
        "n_fdr_significant": len(survivors),
    }
    return {
        "index": index,
        "n_bars": n_bars,
        "t0_ms": float(ts_a[0]) if ts_a.size else 0.0,
        "t1_ms": float(ts_a[-1]) if ts_a.size else 0.0,
        "best_variant": best["label"],
        "criteria": criteria,
        "variants": per_variant,
    }


# ----------------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------------

def run(
    pair_a: tuple[np.ndarray, np.ndarray],
    pair_b: tuple[np.ndarray, np.ndarray],
    *,
    symbol_a: str = "BTCUSDT",
    symbol_b: str = "ETHUSDT",
    n_windows: int = 2,
    lags: tuple[int, ...] = DEFAULT_LAGS,
    n_bins: int = DEFAULT_N_BINS,
    grid_ms: float = DEFAULT_GRID_MS,
    n_surrogates: int = FULL_RESOLUTION_N_SURROGATES,
    seed: int = 42,
    max_ticks_per_window: int = WINDOW_MAX_TICKS,
    backend: str = "auto",
    source: str = "",
    check_baseline: bool = True,
) -> dict[str, Any]:
    """Run the H-18 resolution audit over >= 2 windows and assemble the payload.

    Reuses ``split_pair_windows``/``align_returns`` from the original H-04
    module verbatim (byte-identical pipeline clause). Every field the
    gate-auditor needs to write a NEW GL entry is included; nothing here
    writes ``gate_log.md`` and nothing here changes a GL-006 field.
    """
    resolved_backend = resolve_backend(backend)
    verdict_carrying, verdict_reason = _verdict_carrying(n_surrogates, resolved_backend)

    ts_a, px_a = pair_a
    ts_b, px_b = pair_b
    windows_raw = split_pair_windows(
        ts_a, px_a, ts_b, px_b, n_windows,
        max_ticks_per_window=max_ticks_per_window,
    )
    n_total_a, n_total_b = int(ts_a.size), int(ts_b.size)
    print(
        f"[c18] H-18 audit pair {symbol_a}/{symbol_b}: {n_total_a}/{n_total_b} "
        f"ticks, {len(windows_raw)} window(s), lags={list(lags)}, "
        f"grid={grid_ms:g}ms, n_surrogates={n_surrogates}, backend={resolved_backend}, "
        f"verdict_carrying={verdict_carrying}",
        file=sys.stderr, flush=True,
    )

    windows = [
        run_window(
            i, wa, wb,
            symbol_a=symbol_a, symbol_b=symbol_b,
            lags=lags, n_bins=n_bins, grid_ms=grid_ms,
            n_surrogates=n_surrogates, seed=seed,
            n_windows=len(windows_raw), backend=resolved_backend,
        )
        for i, (wa, wb) in enumerate(windows_raw)
    ]

    per_window_existence = [bool(w["criteria"]["surrogate_p"]["passed"]) for w in windows]
    lead_symbols = [w["criteria"]["lead_symbol"]["value"] for w in windows]
    lead_stable = len(set(lead_symbols)) == 1

    is_gl006_pair = (
        {symbol_a, symbol_b} == {"BTCUSDT", "ETHUSDT"}
        and grid_ms == DEFAULT_GRID_MS
        and n_bins == DEFAULT_N_BINS
        and tuple(lags) == DEFAULT_LAGS
    )
    data_binding = (
        compare_windows_to_baseline(windows) if (check_baseline and is_gl006_pair) else {
            "purpose": "uebersprungen (Symbol-Paar/Grid/Lags weichen vom GL-006-Standard ab)",
            "windows": [], "max_observed_stat_deviation": None,
            "all_windows_match_gl006": None,
        }
    )
    t1 = evaluate_t1(windows, n_surrogates) if is_gl006_pair else {
        "claim": "T1 uebersprungen (nicht das registrierte BTCUSDT/ETHUSDT-F-LEADLAG-Setup)",
        "t1_holds": None, "cells": [],
    }
    t2 = evaluate_t2(windows, n_surrogates) if is_gl006_pair else {
        "claim": "T2 uebersprungen (nicht das registrierte BTCUSDT/ETHUSDT-F-LEADLAG-Setup)",
        "t2_holds": None, "cells": [],
    }

    mode = "resolution_audit" if verdict_carrying else "partial_or_equivalence_run"

    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": AUDIT_ID,
        "base_gate": BASE_GATE,
        "base_hypothesis": BASE_HYPOTHESIS,
        "hypothesis_registry": HYPOTHESIS_REGISTRY_PATH,
        "gate_log_not_written_by_this_module": GATE_LOG_PATH,
        "non_verdict_clause": NON_VERDICT_CLAUSE,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "n_windows": len(windows),
        "n_surrogates": n_surrogates,
        "seed": seed,
        "fdr_alpha": FDR_ALPHA,
        "grid_ms": grid_ms,
        "n_bins": n_bins,
        "lags": list(lags),
        "axes": ["TE (C-17)", "WCOH (C-41)"],
        "max_ticks_per_window": int(max_ticks_per_window),
        "n_ticks_total": {"a": n_total_a, "b": n_total_b},
        "backend": {
            "requested": backend,
            "resolved": resolved_backend,
        },
        "mode": mode,
        "verdict_carrying": verdict_carrying,
        "verdict_carrying_reason": verdict_reason,
        "gate_thresholds_reused_from_gl006": {
            "surrogate_p_max": SURROGATE_P_MAX,
            "min_windows": MIN_WINDOWS,
            "lead_symbol_stable_required": True,
        },
        "t1_partial_claim": t1,
        "t2_partial_claim": t2,
        "data_binding_vs_gl006": data_binding,
        "per_window_existence_informational": per_window_existence,
        "lead_symbols_informational": lead_symbols,
        "lead_symbol_stable_informational": lead_stable,
        "windows": windows,
    }


# ----------------------------------------------------------------------------
# Equivalence self-test: byte-for-byte / point-estimate comparison against
# the ORIGINAL c17_c41_lead_lag pipeline at small N (sandbox-verifiable).
# ----------------------------------------------------------------------------

def generate_synthetic_lead_lag_pair(
    *,
    seed: int = 7,
    n_bars: int = 900,
    lag: int = 3,
    alpha: float = 0.85,
    noise: float = 2e-4,
    sigma: float = 1e-3,
) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic ``(source, target)`` LOG-RETURN arrays: ``target[t] =
    alpha * source[t-lag] + noise``. Mirrors the test-fixture construction in
    ``tests/unit/test_c17_c41_lead_lag.py`` but returns raw return arrays
    directly (no tick resampling — the equivalence claim is about the
    TE/WCOH + surrogate machinery, not the grid loader, which is reused
    verbatim from the original module and therefore not re-tested here)."""
    rng = np.random.default_rng(seed)
    source = rng.normal(0.0, sigma, size=n_bars)
    target = np.zeros(n_bars)
    target[lag:] = alpha * source[:-lag] + noise * rng.normal(0.0, 1.0, size=n_bars - lag)
    return source, target


def run_equivalence_selftest(
    *,
    seed: int = 7,
    n_bars: int = 900,
    lag: int = 3,
    lags: tuple[int, ...] = (2, 3),
    n_bins: int = DEFAULT_N_BINS,
    grid_ms: float = DEFAULT_GRID_MS,
    n_surrogates: int = 200,
    surrogate_seed: int = 42,
    backend: str = "auto",
    point_estimate_atol: float = 1e-8,
) -> dict[str, Any]:
    """Compare the c18 batched pipeline against the ORIGINAL c17_c41_lead_lag
    module on the SAME synthetic input, at the SAME small N (default 200 —
    the archived GL-006 resolution). This is the sandbox correctness anchor
    (registry H-18): TE/WCOH point estimates must match near-exactly (same
    formulas, vectorised), and — because ``generate_shift_offsets`` replays
    the ORIGINAL RNG consumption call-by-call — the surrogate ensembles (and
    therefore the p-values) must match EXACTLY on the numpy backend.

    Always returns ``mode = "equivalence_selftest"`` — this function is a
    methodology equivalence proof, NEVER a resolution-audit result, even if
    called with a larger N.
    """
    resolved_backend = resolve_backend(backend)
    source, target = generate_synthetic_lead_lag_pair(seed=seed, n_bars=n_bars, lag=lag)

    variants: list[dict[str, Any]] = []
    for test_lag in lags:
        for direction, (src, dst) in (
            ("fwd", (source, target)),
            ("rev", (target, source)),
        ):
            te_orig = _orig_transfer_entropy(src, dst, test_lag, n_bins=n_bins)
            te_batch = float(
                transfer_entropy_batch(
                    src[None, :], dst, test_lag, n_bins=n_bins, backend=resolved_backend
                )[0]
            )
            orig_res = _orig_surrogate_test_te(
                src, dst, test_lag, n_bins=n_bins,
                n_surrogates=n_surrogates, seed=surrogate_seed,
            )
            batch_res = surrogate_test_te_batched(
                src, dst, test_lag, n_bins=n_bins,
                n_surrogates=n_surrogates, seed=surrogate_seed, backend=resolved_backend,
            )
            variants.append({
                "label": f"TE_{direction}_lag{test_lag}",
                "point_estimate_original": te_orig,
                "point_estimate_batched": te_batch,
                "point_estimate_abs_diff": abs(te_orig - te_batch),
                "point_estimate_match": abs(te_orig - te_batch) <= point_estimate_atol,
                "p_original": orig_res.p_value,
                "p_batched": batch_res.p_value,
                "p_exact_match": orig_res.p_value == batch_res.p_value,
                "surrogate_stats_bit_identical": bool(
                    np.array_equal(orig_res.surrogate_stats, batch_res.surrogate_stats)
                ),
            })

    wcoh_lead_orig, wcoh_coh_orig = _orig_wavelet_coherence_lead(source, target, grid_ms)
    leads_b, cohs_b = wavelet_coherence_lead_batch(
        source[None, :], target, grid_ms, backend=resolved_backend
    )
    wcoh_orig_res, wcoh_lead_obs = _orig_surrogate_test_wcoh(
        source, target, grid_ms, n_surrogates=n_surrogates, seed=surrogate_seed,
    )
    wcoh_batch_res, wcoh_lead_obs_b = surrogate_test_wcoh_batched(
        source, target, grid_ms, n_surrogates=n_surrogates, seed=surrogate_seed,
        backend=resolved_backend,
    )
    wcoh_variant = {
        "label": "WCOH",
        "point_estimate_original": wcoh_coh_orig,
        "point_estimate_batched": float(cohs_b[0]),
        "point_estimate_abs_diff": abs(wcoh_coh_orig - float(cohs_b[0])),
        "point_estimate_match": abs(wcoh_coh_orig - float(cohs_b[0])) <= 1e-6,
        "lead_seconds_original": wcoh_lead_orig,
        "lead_seconds_batched": float(leads_b[0]),
        "p_original": wcoh_orig_res.p_value,
        "p_batched": wcoh_batch_res.p_value,
        "p_exact_match": wcoh_orig_res.p_value == wcoh_batch_res.p_value,
        "surrogate_stats_bit_identical": bool(
            np.array_equal(wcoh_orig_res.surrogate_stats, wcoh_batch_res.surrogate_stats)
        ),
    }
    variants.append(wcoh_variant)

    all_point_match = all(v["point_estimate_match"] for v in variants)
    all_p_match = all(v["p_exact_match"] for v in variants)

    return {
        "mode": "equivalence_selftest",
        "not_a_resolution_audit": True,
        "note": (
            f"Aequivalenz-Test (N={n_surrogates}), KEIN Aufloesungs-Audit — "
            "vergleicht die c18-Batch-Pipeline gegen die ORIGINALE "
            "c17_c41_lead_lag-Pipeline auf identischem synthetischem Input."
        ),
        "backend": resolved_backend,
        "n_surrogates": n_surrogates,
        "n_bars": n_bars,
        "injected_lag": lag,
        "variants": variants,
        "all_point_estimates_match": bool(all_point_match),
        "all_p_values_exact_match": bool(all_p_match),
        "equivalence_holds": bool(all_point_match and all_p_match),
    }


# ----------------------------------------------------------------------------
# Report + output writers
# ----------------------------------------------------------------------------

def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_markdown(payload: dict[str, Any]) -> str:
    """German Markdown report for the H-18 resolution audit."""
    L: list[str] = []
    L.append(f"# H-18 · {payload['base_gate']}/{payload['base_hypothesis']} Lead-Lag High-N-Surrogat-Aufloesungs-Audit")
    L.append("")
    L.append("> **AUFLOESUNGS-AUDIT, KEINE NEU-ADJUDIKATION.** " + payload["non_verdict_clause"])
    L.append("")
    L.append(f"- **Registry:** `{payload['hypothesis_registry']}` (H-18) · Basis-Gate `{payload['base_gate']}` ({payload['base_hypothesis']})")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Paar `{payload['symbol_a']}`/`{payload['symbol_b']}`)")
    L.append(
        f"- **Fenster:** {payload['n_windows']} · **Surrogates:** {payload['n_surrogates']} "
        f"(GL-006: 200) · **Seed:** {payload['seed']} · **BH-FDR alpha:** {payload['fdr_alpha']}"
    )
    L.append(
        f"- **Backend:** angefordert `{payload['backend']['requested']}` -> "
        f"aufgeloest `{payload['backend']['resolved']}`"
    )
    L.append(
        f"- **Modus:** `{payload['mode']}` · **verdict_carrying:** {_fmt(payload['verdict_carrying'])} "
        f"— {payload['verdict_carrying_reason']}"
    )
    L.append(f"- **KAPITALFREI:** {_fmt(payload['capital_free'])} — identisch GL-006.")
    L.append("")
    if not payload["verdict_carrying"]:
        L.append(
            "> **HINWEIS:** dieser Lauf ist NICHT verdikt-tragend "
            "(Compute-Gating-Pflicht, registry H-18). T1/T2 unten sind "
            "INFORMATIV, kein vorregistriertes T1/T2-Ergebnis."
        )
        L.append("")

    t1 = payload["t1_partial_claim"]
    L.append("## T1 — Stage-1-FDR-Survivor-Reproduktion")
    L.append("")
    L.append(f"{t1.get('claim', '')}")
    L.append("")
    if t1.get("cells"):
        L.append(f"**t1_holds:** {_fmt(t1.get('t1_holds'))} · Haltend: {t1.get('n_holding')}/{t1.get('n_survivors')}")
        L.append("")
        L.append("| Fenster | Variante | p (GL-006) | p (neu) | p<=1e-3 | FDR-sig (neu) | haelt |")
        L.append("|---:|---|---:|---:|---|---|---|")
        for c in t1["cells"]:
            L.append(
                f"| {c['window']} | `{c['label']}` | {_fmt(c.get('p_gl006'), 5)} | "
                f"{_fmt(c.get('p_new'), 6)} | {_fmt(c.get('p_le_threshold'))} | "
                f"{_fmt(c.get('fdr_significant_new'))} | {_fmt(c.get('holds'))} |"
            )
        L.append("")

    t2 = payload["t2_partial_claim"]
    L.append("## T2 — Lesart-Entscheidungszellen (ETH->BTC F0 Lag1/Lag2)")
    L.append("")
    L.append(f"{t2.get('claim', '')}")
    L.append("")
    if t2.get("cells"):
        L.append(f"**t2_holds:** {_fmt(t2.get('t2_holds'))}")
        L.append("")
        L.append("| Fenster | Variante | p (neu) | p_crit (neu) | MC-SE | Distanz (SE) | aufgeloest |")
        L.append("|---:|---|---:|---:|---:|---:|---|")
        for c in t2["cells"]:
            L.append(
                f"| {c['window']} | `{c['label']}` | {_fmt(c.get('p_new'), 6)} | "
                f"{_fmt(c.get('p_crit_new'), 6)} | {_fmt(c.get('mc_se'), 6)} | "
                f"{_fmt(c.get('distance_se'), 2)} | {_fmt(c.get('resolved'))} |"
            )
        L.append("")

    db = payload["data_binding_vs_gl006"]
    L.append("## Datenbindung vs. GL-006 (archivierte Fenster F0/F1)")
    L.append("")
    L.append(f"{db.get('purpose', '')}")
    L.append(f"- **all_windows_match_gl006:** {_fmt(db.get('all_windows_match_gl006'))}")
    L.append("")

    for w in payload["windows"]:
        c = w["criteria"]
        L.append(f"## Fenster {w['index']} — {w['n_bars']} gemeinsame Bars")
        L.append(f"- Zeitspanne: {w['t0_ms']:.0f} .. {w['t1_ms']:.0f} ms")
        L.append(f"- Beste Variante: `{w['best_variant']}` · BH-FDR p_crit: {_fmt(c['fdr_p_crit'], 6)} · FDR-sig: {c['n_fdr_significant']}")
        L.append("")
        L.append("| Variante | Achse | Quelle->Ziel | Lag (ms) | Statistik | Surrogate p | FDR sig |")
        L.append("|---|---|---|---:|---:|---:|---|")
        for v in w["variants"]:
            tgt = v.get("target", "")
            L.append(
                f"| `{v['label']}` | {v['axis']} | {v['source']}->{tgt} "
                f"| {_fmt(v['lag_ms'], 1)} | {_fmt(v['surrogate']['observed_stat'])} "
                f"| {_fmt(v['surrogate']['p_value'], 6)} | {_fmt(v['fdr_significant'])} |"
            )
        L.append("")
    L.append("---")
    L.append(
        "*Erzeugt von `scripts/c18_leadlag_audit.py` (Welle-5-WP, read-only "
        f"Driver). KAPITALFREI. {payload['gate_log_not_written_by_this_module']} "
        "wird von diesem Modul NICHT geschrieben — neuer GL-Eintrag ist "
        "Orchestrator-/gate-auditor-Arbeit.*"
    )
    L.append("")
    return "\n".join(L)


def write_outputs(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``c18_leadlag_audit_results.json`` + ``.md`` to ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c18_leadlag_audit_results.json"
    md_path = out_dir / "c18_leadlag_audit_results.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path


def render_selftest_markdown(result: dict[str, Any]) -> str:
    """German Markdown for the equivalence self-test (--self-test CLI mode)."""
    L: list[str] = []
    L.append("# H-18 Methodik-Aequivalenz-Test (c18_leadlag_audit vs. c17_c41_lead_lag)")
    L.append("")
    L.append(f"> {result['note']}")
    L.append("")
    L.append(f"- **Backend:** `{result['backend']}` · **N-Surrogates:** {result['n_surrogates']} · **injizierter Lag:** {result['injected_lag']}")
    L.append(f"- **all_point_estimates_match:** {_fmt(result['all_point_estimates_match'])}")
    L.append(f"- **all_p_values_exact_match:** {_fmt(result['all_p_values_exact_match'])}")
    L.append(f"- **equivalence_holds:** {_fmt(result['equivalence_holds'])}")
    L.append("")
    L.append("| Variante | TE/Coh original | TE/Coh batched | |diff| | Punkt match | p original | p batched | p exakt | Surrogate-Ensemble bit-identisch |")
    L.append("|---|---:|---:|---:|---|---:|---:|---|---|")
    for v in result["variants"]:
        L.append(
            f"| `{v['label']}` | {_fmt(v['point_estimate_original'], 6)} | "
            f"{_fmt(v['point_estimate_batched'], 6)} | {_fmt(v['point_estimate_abs_diff'], 8)} | "
            f"{_fmt(v['point_estimate_match'])} | {_fmt(v['p_original'], 6)} | "
            f"{_fmt(v['p_batched'], 6)} | {_fmt(v['p_exact_match'])} | "
            f"{_fmt(v['surrogate_stats_bit_identical'])} |"
        )
    L.append("")
    return "\n".join(L)
