"""Orchestration + gate-neutral payload for the H-14 PANEL-LAG gate.

Runs the registered two-window measurement (registry H-14, Welle 5):

  * per window: the FULL training plan (1 full + 12 retrain ablations +
    ~100 all-surrogate null retrainings — ``ablation.run_window_plan``,
    checkpointed/resumable),
  * per directed edge j->i (j != i): T(j->i) = OOS delta log-loss
    ``L_ablate_j(i) - L_full(i)`` (retrain ablation, NOT attention-weight
    reading),
  * per target i: null-delta distribution from ALL ordered pairs of the
    ~100 null-retrain losses (``stats.paired_null_deltas`` — construction
    documented there and in README_H14.md), registered 95th-percentile
    threshold + add-one empirical p-value per edge,
  * ONE F-PANELLAG BH-FDR family over ALL non-BTC-source edges of BOTH
    windows together (``stats.benjamini_hochberg``, alpha = 0.10),
  * positive control: BTC-source -> ETH-target edges are EXCLUDED from the
    pass criterion; if in a window NO such edge clears its null 95th
    percentile, the run is METHODICALLY INVALID (own ``validity_status``,
    no verdict — registry: "methodisch invalide statt informativ"),
  * COMPUTE GATING (analog of H-11/H-13 data gating, but for compute): the
    payload always carries ``compute_gating`` with ``gpu_required: true``;
    ``gate_valid`` is False unless the trainings actually ran on CUDA, and
    ``weiter_indication`` is ``null`` (non-verdict-bearing) in that case.

Edge-family size: 12 nodes give 132 directed edges; excluding the 3
BTC-source nodes leaves EXACTLY 9 x 11 = 99 non-BTC-source edges per window
(the registry's "~110" is its own pre-registered approximation of this
combinatorial count; nothing was re-tuned) -> F-PANELLAG family size
99 x 2 = 198 tests.

GATE-NEUTRAL payload (H-04b/H-12 convention): every criterion is reported
individually; the driver renders NO overall verdict — the gate-auditor
adjudicates against the H-14 registry entry.

KAPITALFREI: pure structure/existence measurement, ``capital_free: true``;
no friction, bps, PnL, Sharpe field anywhere.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .ablation import (
    DEFAULT_N_NULL,
    RESULT_LOSS_KEY,
    TrainFn,
    build_task_plan,
    make_torch_train_fn,
    run_window_plan,
)
from .encoder import check_gpu
from .panel import PanelWindow
from .stats import (
    FDR_ALPHA,
    NULL_PERCENTILE,
    benjamini_hochberg,
    empirical_p_ge,
    null_q95,
    paired_null_deltas,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-14"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-PANELLAG"

#: Pre-registered calendar windows (registry H-14, identical H-09/H-12
#: convention; Cutoff = 2026-07-04 = the base-stock cutoff used by H-12).
DEFAULT_WINDOW_A = ("2026-03-27", "2026-05-15")
DEFAULT_WINDOW_B = ("2026-05-16", "2026-07-04")

#: The gate is defined over BOTH pre-registered windows.
MIN_WINDOWS = 2

#: Base asset whose source edges are excluded from the pass criterion.
BTC_BASE = "BTC"
#: Positive-control target base (registry: BTC->ETH, established by H-04).
POSITIVE_CONTROL_TARGET_BASE = "ETH"

COMPUTE_GATE_NOTE = (
    "GPU-Pflicht (Registry H-14, Rechenaufwand): ohne echtes CUDA-Training "
    "ist der Lauf NICHT verdikt-tragend — gate_valid=false, "
    "weiter_indication=null. Der numpy-/CPU-Pfad ersetzt die registrierte "
    "~226-Retrain-Null NICHT."
)
VALIDITY_NOTE = (
    "Positivkontrolle (Registry H-14): mindestens eine BTC->ETH-Kante muss "
    "je Fenster das 95. Perzentil ihrer Null ueberschreiten (durch H-04 "
    "etabliert, vom Pass-Kriterium AUSGESCHLOSSEN). Scheitert sie, ist der "
    "Lauf METHODISCH INVALIDE (kein Verdikt, NICHT DROP)."
)


# ---------------------------------------------------------------------------
# Statistics assembly (pure — sandbox-testable without torch)
# ---------------------------------------------------------------------------

def _extract_losses(
    results: dict[str, dict[str, Any]], n_nodes: int, n_null: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(full (N,), ablations (N_src, N), nulls (n_null, N)) loss arrays."""
    full = np.asarray(results["full"][RESULT_LOSS_KEY], dtype=np.float64)
    if full.shape != (n_nodes,):
        raise ValueError(f"full loss shape {full.shape} != ({n_nodes},)")
    abl = np.full((n_nodes, n_nodes), np.nan, dtype=np.float64)
    for j in range(n_nodes):
        abl[j, :] = np.asarray(
            results[f"ablate/{j:02d}"][RESULT_LOSS_KEY], dtype=np.float64
        )
    nulls = np.full((n_null, n_nodes), np.nan, dtype=np.float64)
    for k in range(n_null):
        nulls[k, :] = np.asarray(
            results[f"null/{k:03d}"][RESULT_LOSS_KEY], dtype=np.float64
        )
    return full, abl, nulls


def compute_window_edges(
    results: dict[str, dict[str, Any]],
    node_labels: tuple[str, ...],
    node_bases: tuple[str, ...],
    *,
    n_null: int,
) -> dict[str, Any]:
    """Edge statistics for one window from the plan's training results.

    Returns family edges (non-BTC source, verdict-bearing after the
    run-level BH-FDR), BTC-source edges (reported, NOT verdict-bearing) and
    the positive-control record. p-values here are pre-FDR.
    """
    n_nodes = len(node_labels)
    full, abl, nulls = _extract_losses(results, n_nodes, n_null)
    null_deltas = [paired_null_deltas(nulls[:, i]) for i in range(n_nodes)]
    q95 = [null_q95(nd) for nd in null_deltas]

    family: list[dict[str, Any]] = []
    btc_source: list[dict[str, Any]] = []
    for j in range(n_nodes):
        for i in range(n_nodes):
            if i == j:
                continue
            delta = float(abl[j, i] - full[i])
            rec = {
                "source": j,
                "target": i,
                "source_label": node_labels[j],
                "target_label": node_labels[i],
                "delta_log_loss": delta,
                "null_delta_q95": float(q95[i]),
                "over_null_q95": bool(delta > q95[i]),
                "p_value": empirical_p_ge(null_deltas[i], delta),
            }
            if node_bases[j] == BTC_BASE:
                btc_source.append(rec)
            else:
                family.append(rec)

    pc_edges = [
        e for e in btc_source
        if node_bases[e["target"]] == POSITIVE_CONTROL_TARGET_BASE
    ]
    positive_control = {
        "n_btc_to_eth": len(pc_edges),
        "n_over_null_q95": sum(1 for e in pc_edges if e["over_null_q95"]),
        "ok": bool(any(e["over_null_q95"] for e in pc_edges)),
    }
    return {
        "full_per_node_log_loss": [float(v) for v in full],
        "null_loss_mean_per_node": [float(v) for v in np.mean(nulls, axis=0)],
        "family_edges": family,
        "btc_source_edges": btc_source,
        "positive_control": positive_control,
    }


def assemble_payload(
    window_stats: list[dict[str, Any]],
    *,
    n_null: int,
    seed: int,
    source: str,
    compute_info: dict[str, Any],
    method_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Gate-neutral payload from per-window edge statistics.

    ``window_stats[w]`` needs keys: ``window_label``, ``start_date``,
    ``end_date``, ``node_labels``, ``node_bases`` plus the
    ``compute_window_edges`` output. ``compute_info`` is the honest compute
    report (see ``build_compute_gating``). One F-PANELLAG BH-FDR family over
    BOTH windows. The gate-auditor adjudicates.
    """
    if len(window_stats) < MIN_WINDOWS:
        raise ValueError(
            f"{HYPOTHESIS_ID} needs >= {MIN_WINDOWS} windows, got {len(window_stats)}"
        )

    # ONE F-PANELLAG BH-FDR family over ALL family edges of BOTH windows.
    family_edges: list[dict[str, Any]] = []
    for w in window_stats:
        family_edges.extend(w["family_edges"])
    p_values = [e["p_value"] for e in family_edges]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for e, rej in zip(family_edges, rejected):
        e["fdr_significant"] = bool(rej)
        e["surviving"] = bool(rej and e["over_null_q95"])

    window_records: list[dict[str, Any]] = []
    for wi, w in enumerate(window_stats):
        fam = w["family_edges"]
        surv = [e for e in fam if e["surviving"]]
        window_records.append({
            "window_index": wi,
            "window_label": w["window_label"],
            "start_date": w["start_date"],
            "end_date": w["end_date"],
            "node_labels": list(w["node_labels"]),
            "node_bases": list(w["node_bases"]),
            "coverage": [float(c) for c in w.get("coverage", [])],
            "n_family_edges": len(fam),
            "n_over_null_q95": sum(1 for e in fam if e["over_null_q95"]),
            "n_fdr_significant": sum(1 for e in fam if e["fdr_significant"]),
            "n_surviving": len(surv),
            "any_family_survivor": bool(surv),
            "surviving_edges": [
                {k: e[k] for k in ("source_label", "target_label",
                                   "delta_log_loss", "null_delta_q95", "p_value")}
                for e in surv
            ],
            "full_per_node_log_loss": w["full_per_node_log_loss"],
            "null_loss_mean_per_node": w["null_loss_mean_per_node"],
            "positive_control": w["positive_control"],
            "family_edges": fam,
            "btc_source_edges": w["btc_source_edges"],
        })

    # positive control (validity precondition — NOT a gate criterion):
    pc_ok_all = all(w["positive_control"]["ok"] for w in window_records)
    validity_status = "gueltig" if pc_ok_all else "ungueltig"

    # compute gating (verdict-bearing only with real CUDA training):
    gate_valid = bool(compute_info.get("gate_valid", False))

    all_windows_survivor = all(
        w["any_family_survivor"] for w in window_records
    )
    # weiter_indication is NON-verdict-bearing (null) without real GPU
    # training OR when the positive control fails (methodically invalid run
    # — a THIRD state, distinct from a genuine DROP). Only with real CUDA
    # training AND a valid positive control does it mirror the registered
    # gate reading.
    weiter_indication: bool | None
    if not gate_valid or not pc_ok_all:
        weiter_indication = None
    else:
        weiter_indication = bool(all_windows_survivor)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "window_labels": [w["window_label"] for w in window_records],
        "n_windows": len(window_records),
        "n_null_retrainings_per_window": int(n_null),
        "seed": int(seed),
        "method": {
            "panel": "12 Nodes = BTC/ETH x {Bybit, Binance, Deribit-PERP} + "
                     "SOL/BNB/XRP x {Bybit, Binance}, publicTrade 1s-Grid",
            "model": "Pro Node ein PatchTST-Style-Encoder (m18-Wiederverwendung) "
                     "+ Cross-Node-Multi-Head-Attention; Target = Vorzeichen "
                     "der naechsten 10s-Rendite je Node",
            "statistic": "T(j->i) = OOS-Delta-Log-Loss (Vollmodell vs. "
                         "Single-Source-j-Retrain-Ablation, zirkulaeres "
                         "Surrogat) — KEINE Attention-Gewicht-Lesart",
            "null": f"~{n_null} Retrainings je Fenster mit komplett "
                    "surrogaten Cross-Node-Inputs (zirkulaerer Shift je Node, "
                    "Targets aus der geshifteten Serie); Null-Deltas = alle "
                    "geordneten Paardifferenzen der Null-OOS-Losses je Target",
            **(method_params or {}),
        },
        "compute_gating": build_compute_gating(compute_info),
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": FDR_FAMILY,
        "fdr_family_size": len(p_values),
        "fdr_p_crit": float(p_crit),
        "n_fdr_significant": sum(1 for e in family_edges if e["fdr_significant"]),
        "family_size_note": (
            "12 Nodes -> 132 gerichtete Kanten; ohne die 3 BTC-Source-Nodes "
            "exakt 9x11=99 Non-BTC-Source-Kanten je Fenster (Registry-"
            "Schaetzung '~110'); Familie = beide Fenster gemeinsam."
        ),
        "gate_thresholds": {
            "null_percentile": NULL_PERCENTILE,
            "fdr_alpha": FDR_ALPHA,
            "min_windows": MIN_WINDOWS,
            "criterion": ">=1 Non-BTC-Source-Kante je Fenster ueber dem 95. "
                         "Perzentil der Null UND BH-FDR-ueberlebend (F-PANELLAG)",
        },
        "positive_control_note": VALIDITY_NOTE,
        "positive_control_ok_all_windows": pc_ok_all,
        "validity_status": validity_status,
        # Gate-neutral observation flags (the gate-auditor adjudicates):
        "all_windows_have_surviving_non_btc_source": all_windows_survivor,
        "weiter_indication": weiter_indication,
        "windows": window_records,
    }


def build_compute_gating(compute_info: dict[str, Any]) -> dict[str, Any]:
    """Normalised compute-gating block (always present in the payload)."""
    return {
        "gpu_required": True,
        "torch_available": bool(compute_info.get("torch_available", False)),
        "cuda_available": bool(compute_info.get("cuda_available", False)),
        "device_name": compute_info.get("device_name"),
        "ran_on_gpu": bool(compute_info.get("ran_on_gpu", False)),
        "cpu_fallback_used": bool(compute_info.get("cpu_fallback_used", False)),
        "synthetic_train_fn_used": bool(
            compute_info.get("synthetic_train_fn_used", False)
        ),
        "gate_valid": bool(compute_info.get("gate_valid", False)),
        "note": COMPUTE_GATE_NOTE,
    }


def make_compute_info(
    *,
    ran_on_gpu: bool,
    cpu_fallback_used: bool = False,
    synthetic_train_fn_used: bool = False,
) -> dict[str, Any]:
    """Honest compute report: gate_valid ONLY for real CUDA training."""
    gpu = check_gpu()
    return {
        **gpu,
        "ran_on_gpu": bool(ran_on_gpu),
        "cpu_fallback_used": bool(cpu_fallback_used),
        "synthetic_train_fn_used": bool(synthetic_train_fn_used),
        "gate_valid": bool(
            ran_on_gpu and not cpu_fallback_used and not synthetic_train_fn_used
        ),
    }


# ---------------------------------------------------------------------------
# Full orchestration (plan -> train/resume -> statistics)
# ---------------------------------------------------------------------------

def run(
    windows: list[PanelWindow],
    ckpt_dir: Path | str,
    *,
    n_null: int = DEFAULT_N_NULL,
    seed: int = 42,
    source: str = "",
    train_fn: TrainFn | None = None,
    compute_info: dict[str, Any] | None = None,
    device: str = "auto",
) -> dict[str, Any]:
    """Run (or resume) the full H-14 measurement over both windows.

    Without an injected ``train_fn`` the real torch path is used
    (compute-gated: raises ``ComputeGateError`` when torch is missing — the
    CLI aborts BEFORE this with a clean message). ``compute_info`` defaults
    to the honest auto-detected report; an injected train_fn marks the run
    as synthetic (never verdict-bearing).
    """
    if len(windows) < MIN_WINDOWS:
        raise ValueError(
            f"{HYPOTHESIS_ID} needs >= {MIN_WINDOWS} windows, got {len(windows)}"
        )
    n_nodes = windows[0].n_nodes
    synthetic = train_fn is not None
    if train_fn is None:
        train_fn = make_torch_train_fn(n_nodes, device=device)
    if compute_info is None:
        gpu = check_gpu()
        compute_info = make_compute_info(
            ran_on_gpu=bool(gpu["gpu_ready"] and not synthetic),
            cpu_fallback_used=bool(not gpu["gpu_ready"] and not synthetic),
            synthetic_train_fn_used=synthetic,
        )

    # Checkpoint-provenance gate (Bug #1 fix): whenever this run claims
    # ran_on_gpu=True (about to report gate_valid=True), EVERY task result —
    # freshly trained now OR resumed from an existing checkpoint — must be
    # real-CUDA. Prevents a checkpoint directory previously populated by a
    # --allow-cpu-fallback/dummy run from being silently resumed into a
    # verdict-bearing gate_valid=True result. Raises ValueError on mismatch.
    require_cuda = bool(compute_info.get("ran_on_gpu", False))

    window_stats: list[dict[str, Any]] = []
    for win in windows:
        tasks = build_task_plan(win.label, win.n_nodes, n_null=n_null, seed=seed)
        print(
            f"[c14_panellag] window {win.label}: plan = {len(tasks)} trainings "
            f"(1 full + {win.n_nodes} ablations + {n_null} nulls)",
            file=sys.stderr, flush=True,
        )
        results = run_window_plan(
            win, tasks, ckpt_dir, train_fn, require_cuda=require_cuda
        )
        stats = compute_window_edges(
            results, win.node_labels, win.node_bases, n_null=n_null
        )
        stats.update({
            "window_label": win.label,
            "start_date": win.start_date,
            "end_date": win.end_date,
            "node_labels": win.node_labels,
            "node_bases": win.node_bases,
            "coverage": win.coverage,
        })
        window_stats.append(stats)

    return assemble_payload(
        window_stats, n_null=n_null, seed=seed, source=source,
        compute_info=compute_info,
    )


# ---------------------------------------------------------------------------
# Report (Deutsch)
# ---------------------------------------------------------------------------

def _fmt(v: Any, nd: int = 4) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}"


def render_markdown(payload: dict[str, Any]) -> str:
    """German Markdown report — compute gating, gate core, edges (H-14)."""
    L: list[str] = []
    L.append("# H-14 · Conditional Cross-Venue-Lead-Lag-Graph "
             "(Node-Ablation-Cross-Attention, F-PANELLAG, KAPITALFREI, GPU)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — "
             f"`{payload['hypothesis_registry']}` (Welle 5)")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}`")
    L.append(f"- **Fenster (vorregistriert):** {', '.join(payload['window_labels'])}")
    m = payload["method"]
    L.append(f"- **Panel:** {m['panel']}")
    L.append(f"- **Modell:** {m['model']}")
    L.append(f"- **Statistik:** {m['statistic']}")
    L.append(f"- **Null:** {m['null']} · Seed: {payload['seed']}")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} (EINE Familie ueber "
             f"BEIDE Fenster, {payload['fdr_family_size']} Kanten-Tests) · "
             f"BH-FDR alpha {payload['fdr_alpha']} · "
             f"p_crit {_fmt(payload['fdr_p_crit'])} · "
             f"FDR-signifikant: {payload['n_fdr_significant']}")
    L.append(f"- **Familien-Groesse:** {payload['family_size_note']}")
    L.append("- **KAPITALFREI:** ja — reine Struktur-/Existenzfrage. "
             "Eine Handelsfolge waere NEUE H-14b, NICHT impliziert.")
    cg = payload["compute_gating"]
    L.append("")
    L.append("## Compute-Gating (GPU-Pflicht)")
    L.append("")
    L.append(f"- torch verfuegbar: {_fmt(cg['torch_available'])} · "
             f"CUDA verfuegbar: {_fmt(cg['cuda_available'])} · "
             f"Device: {cg['device_name'] or 'n/a'}")
    L.append(f"- **auf GPU gelaufen:** {_fmt(cg['ran_on_gpu'])} · "
             f"CPU-Fallback: {_fmt(cg['cpu_fallback_used'])} · "
             f"synthetisches train_fn: {_fmt(cg['synthetic_train_fn_used'])}")
    L.append(f"- **gate_valid:** {_fmt(cg['gate_valid'])} — {cg['note']}")
    L.append("")
    L.append(f"- **Positivkontrolle:** {payload['positive_control_note']}")
    L.append(f"- **Validitaets-Status dieses Laufs:** "
             f"**{payload['validity_status'].upper()}**")
    L.append("")
    L.append("> Gate-Urteil faellt der gate-auditor gegen H-14. WEITER verlangt "
             "in BEIDEN Fenstern mindestens eine gerichtete Non-BTC-Source-"
             "Kante ueber dem 95. Perzentil der ~100-Surrogat-Null UND "
             "BH-FDR alpha=0,10 ueber F-PANELLAG ueberlebend. DROP (hartes "
             "Ein-Fenster-Kriterium): null ueberlebende Non-BTC-Source-Kanten "
             "in einem Fenster. Kein Graubereich, kein Kanten-/Schwellen-"
             "Nachjustieren. BTC->ETH ist Positivkontrolle (vom Pass "
             "ausgeschlossen; Scheitern = methodisch invalide). "
             "A-priori: DROP erwartet.")
    L.append("")
    wi = payload["weiter_indication"]
    L.append(f"**WEITER-Indikation (nur bei gate_valid und gueltigem Lauf):** "
             f"{'n/a (nicht verdikt-tragend)' if wi is None else _fmt(wi)} · "
             f"**alle Fenster mit Survivor:** "
             f"{_fmt(payload['all_windows_have_surviving_non_btc_source'])} · "
             f"**Positivkontrolle alle Fenster:** "
             f"{_fmt(payload['positive_control_ok_all_windows'])}")
    L.append("")
    L.append("## Fenster-Uebersicht (Gate-Kern)")
    L.append("")
    L.append("| Fenster | Familien-Kanten | ueber Null-q95 | FDR-sig | "
             "ueberlebend | >=1 Survivor | Positivkontrolle |")
    L.append("|---|---:|---:|---:|---:|:---:|:---:|")
    for w in payload["windows"]:
        pc = w["positive_control"]
        L.append(
            f"| {w['window_label']} | {w['n_family_edges']} "
            f"| {w['n_over_null_q95']} | {w['n_fdr_significant']} "
            f"| {w['n_surviving']} | {_fmt(w['any_family_survivor'])} "
            f"| {_fmt(pc['ok'])} ({pc['n_over_null_q95']}/{pc['n_btc_to_eth']}) |"
        )
    L.append("")
    for w in payload["windows"]:
        L.append(f"## Kanten {w['window_label']}")
        L.append("")
        if w["surviving_edges"]:
            L.append("**Ueberlebende Non-BTC-Source-Kanten (ueber q95 UND "
                     "FDR-sig):**")
            L.append("")
            L.append("| Quelle -> Ziel | Delta-Log-Loss | Null-q95 | p |")
            L.append("|---|---:|---:|---:|")
            for e in w["surviving_edges"]:
                L.append(
                    f"| {e['source_label']} -> {e['target_label']} "
                    f"| {_fmt(e['delta_log_loss'], 6)} "
                    f"| {_fmt(e['null_delta_q95'], 6)} | {_fmt(e['p_value'])} |"
                )
        else:
            L.append("*Keine ueberlebende Non-BTC-Source-Kante in diesem "
                     "Fenster.*")
        L.append("")
        top = sorted(w["family_edges"], key=lambda e: -e["delta_log_loss"])[:10]
        L.append("**Top-10 Familien-Kanten nach Delta-Log-Loss:**")
        L.append("")
        L.append("| Quelle -> Ziel | Delta-Log-Loss | Null-q95 | ueber q95 | "
                 "p | FDR-sig |")
        L.append("|---|---:|---:|:---:|---:|:---:|")
        for e in top:
            L.append(
                f"| {e['source_label']} -> {e['target_label']} "
                f"| {_fmt(e['delta_log_loss'], 6)} "
                f"| {_fmt(e['null_delta_q95'], 6)} | {_fmt(e['over_null_q95'])} "
                f"| {_fmt(e['p_value'])} | {_fmt(e.get('fdr_significant'))} |"
            )
        L.append("")
        pcs = sorted(
            (e for e in w["btc_source_edges"]
             if e["target_label"] and e["over_null_q95"] is not None),
            key=lambda e: -e["delta_log_loss"],
        )[:6]
        L.append("**BTC-Source-Kanten (NICHT urteilstragend, inkl. "
                 "Positivkontrolle BTC->ETH):**")
        L.append("")
        L.append("| Quelle -> Ziel | Delta-Log-Loss | Null-q95 | ueber q95 |")
        L.append("|---|---:|---:|:---:|")
        for e in pcs:
            L.append(
                f"| {e['source_label']} -> {e['target_label']} "
                f"| {_fmt(e['delta_log_loss'], 6)} "
                f"| {_fmt(e['null_delta_q95'], 6)} | {_fmt(e['over_null_q95'])} |"
            )
        L.append("")
    L.append("*Erzeugt von `scripts/c14_panellag.py` (Welle 5, read-only "
             "Harvester-Backfill, GPU-gated). capital_free=true. "
             "Endgueltiges Gate-Urteil: gate-auditor gegen H-14.*")
    L.append("")
    return "\n".join(L)


__all__ = [
    "BTC_BASE",
    "DEFAULT_WINDOW_A",
    "DEFAULT_WINDOW_B",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "MIN_WINDOWS",
    "POSITIVE_CONTROL_TARGET_BASE",
    "REGISTRY_PATH",
    "SCHEMA_VERSION",
    "assemble_payload",
    "build_compute_gating",
    "compute_window_edges",
    "make_compute_info",
    "render_markdown",
    "run",
]
