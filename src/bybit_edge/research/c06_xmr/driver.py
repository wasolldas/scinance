"""Orchestration + gate-neutral payload for the C-06 XMR mess-gate (H-07/H-08).

The ``overextension`` mode parameter (DEC-18) selects axis A: ``"z"`` (default)
is the unchanged H-07 path (|z| >= z_thresh, family F-XMR); ``"rank"`` is the
H-08 path (per-bar rank-1 symbol = argmax |z|, threshold-free, family
F-XMR-RANK). Everything downstream (axis B, baseline, surrogates, CIs, FDR,
N-floor, payload shape) is identical between the modes.

Per (window, horizon h) this computes, on the reversion-signed forward returns:
  * mu_rev_conditioned  — events passing axis A (|z|>=2.5) AND axis B (non-crash),
  * mu_rev_baseline     — ALL (i,t) bars, unconditioned (the E-04 trivial reading,
                          measured ONLY as the non-triviality null anchor),
  * surrogate_p         — permutation p for conditioned mu_rev > 0,
  * block-bootstrap 95% CIs for BOTH conditioned and baseline,
  * n_events            — conditioned event count (N-floor check).

BH-FDR alpha=0.10 is applied over the whole F-XMR family (all h x window, on the
conditioned surrogate p-values). Per horizon h the roll-up flag
``amplified_consistent`` is True iff, in >= 2 windows: conditioned mu_rev > 0 AND
fdr_significant AND n_events >= N_FLOOR AND the conditioned CI does NOT overlap
(lies above) the baseline CI. ``any_amplified_consistent`` folds this over h.

The driver renders NO overall verdict — the gate-auditor adjudicates against
H-07. It reports each cell individually plus the per-h roll-up.

KAPITALFREI: pure measurement. ``capital_free: true`` in the payload; there is NO
friction, bps, edge, PnL, Sharpe field anywhere.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

import numpy as np

from .panel import DEFAULT_SYMBOLS, SyncedPanel
from .stats import (
    CI_LEVEL,
    FDR_ALPHA,
    SURROGATE_P_MAX,
    benjamini_hochberg,
    block_bootstrap_ci,
    ci_non_overlap,
    surrogate_p_mu_positive,
)
from .xsec import (
    DEFAULT_CRASH_DECILE,
    DEFAULT_HORIZONS,
    DEFAULT_LOOKBACK_BARS,
    DEFAULT_Z_THRESH,
    PANEL_RV_BARS,
    build_event_table,
    build_event_table_rank,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-07"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-XMR"

#: RANK over-stretch mode (H-08 / DEC-18): own hypothesis + own FDR family.
HYPOTHESIS_ID_RANK = "H-08"
FDR_FAMILY_RANK = "F-XMR-RANK"

#: Valid axis-A over-stretch modes ("z" = H-07 default path, "rank" = H-08).
OVEREXTENSION_MODES: tuple[str, ...] = ("z", "rank")

#: Minimum conditioned over-stretch events per window (registry H-07: >= 30).
DEFAULT_N_FLOOR = 30

#: >= 2 disjoint windows for amplification consistency (registry H-07).
MIN_WINDOWS = 2


def run(
    panels: list[SyncedPanel],
    *,
    window_labels: tuple[str, ...],
    lookback_bars: int = DEFAULT_LOOKBACK_BARS,
    z_thresh: float = DEFAULT_Z_THRESH,
    crash_decile: float = DEFAULT_CRASH_DECILE,
    panel_rv_bars: int = PANEL_RV_BARS,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    n_surrogates: int = 200,
    n_bootstrap: int = 1000,
    n_floor: int = DEFAULT_N_FLOOR,
    seed: int = 42,
    source: str = "",
    overextension: str = "z",
) -> dict[str, Any]:
    """Run the C-06 XMR mess-gate over >= 2 pre-registered synchronised panels.

    ``panels[w]`` is the synchronised panel for window w (>= 2). Returns the
    gate-neutral payload (per-cell stats + per-h amplification roll-up).

    ``overextension`` selects axis A (DEC-18): ``"z"`` (default) is the H-07
    path — |z| >= z_thresh, bit-identical to the pre-DEC-18 behaviour;
    ``"rank"`` is the H-08 path — per-bar rank-1 symbol (argmax |z|,
    threshold-free), reported under hypothesis H-08 / family F-XMR-RANK.
    Axis B, baseline, surrogates, CIs, FDR and N-floor are identical in both.
    """
    if overextension not in OVEREXTENSION_MODES:
        raise ValueError(
            f"overextension must be one of {OVEREXTENSION_MODES}, got {overextension!r}"
        )
    hypothesis_id = HYPOTHESIS_ID_RANK if overextension == "rank" else HYPOTHESIS_ID
    fdr_family = FDR_FAMILY_RANK if overextension == "rank" else FDR_FAMILY
    n_windows = len(panels)
    if n_windows < MIN_WINDOWS:
        raise ValueError(f"{hypothesis_id} needs >= {MIN_WINDOWS} windows, got {n_windows}")

    # 1) per (window, horizon) cell stats.
    cells: list[dict[str, Any]] = []
    for w, panel in enumerate(panels):
        for h in horizons:
            if overextension == "rank":
                evt = build_event_table_rank(
                    panel,
                    lookback_bars=lookback_bars,
                    crash_decile=crash_decile,
                    panel_rv_bars=panel_rv_bars,
                    horizon=h,
                )
            else:
                evt = build_event_table(
                    panel,
                    lookback_bars=lookback_bars,
                    z_thresh=z_thresh,
                    crash_decile=crash_decile,
                    panel_rv_bars=panel_rv_bars,
                    horizon=h,
                )
            cond = evt.conditioned()
            base = evt.baseline()
            n_cond = int(cond.size)
            p_cond, surr_mean = surrogate_p_mu_positive(
                evt.z, evt.rev_ret, evt.is_conditioned,
                n_surrogates=n_surrogates, seed=seed + w * 100 + h,
            )
            mu_c, cl_c, ch_c = block_bootstrap_ci(
                cond, n_bootstrap=n_bootstrap, seed=seed + w * 100 + h,
            )
            mu_b, cl_b, ch_b = block_bootstrap_ci(
                base, n_bootstrap=n_bootstrap, seed=seed + w * 100 + h + 1,
            )
            delta_mu = (mu_c - mu_b) if (np.isfinite(mu_c) and np.isfinite(mu_b)) else float("nan")
            nonoverlap = ci_non_overlap(cl_c, ch_c, cl_b, ch_b)
            n_floor_met = n_cond >= n_floor
            cells.append({
                "window_index": w,
                "window_label": window_labels[w] if w < len(window_labels) else f"w{w}",
                "horizon": int(h),
                "n_events_conditioned": n_cond,
                "n_events_baseline": int(base.size),
                "n_floor": int(n_floor),
                "n_floor_met": bool(n_floor_met),
                "mu_rev_conditioned": _f(mu_c),
                "ci_low_conditioned": _f(cl_c),
                "ci_high_conditioned": _f(ch_c),
                "surrogate_p": _f(p_cond),
                "surrogate_mean": _f(surr_mean),
                "mu_rev_baseline": _f(mu_b),
                "ci_low_baseline": _f(cl_b),
                "ci_high_baseline": _f(ch_b),
                "delta_mu": _f(delta_mu),
                "ci_nonoverlap_vs_baseline": bool(nonoverlap),
                "mu_positive": bool(np.isfinite(mu_c) and mu_c > 0.0),
            })

    # 2) BH-FDR over the whole F-XMR family (conditioned surrogate p-values).
    p_values = [float(c["surrogate_p"]) for c in cells]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for c, rej in zip(cells, rejected):
        c["fdr_significant"] = bool(rej)

    # 3) per-horizon amplification roll-up (>= 2 windows all criteria met).
    horizon_rollup: list[dict[str, Any]] = []
    for h in horizons:
        h_cells = [c for c in cells if c["horizon"] == h]
        passing_windows = sorted(
            c["window_index"] for c in h_cells
            if c["mu_positive"] and c["fdr_significant"]
            and c["n_floor_met"] and c["ci_nonoverlap_vs_baseline"]
        )
        amplified = len(passing_windows) >= MIN_WINDOWS
        horizon_rollup.append({
            "horizon": int(h),
            "n_windows_measured": len(h_cells),
            "passing_windows": passing_windows,
            "n_passing_windows": len(passing_windows),
            "amplified_consistent": bool(amplified),
        })

    any_amplified = any(r["amplified_consistent"] for r in horizon_rollup)
    n_fdr_sig = sum(1 for c in cells if c["fdr_significant"])

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": hypothesis_id,
        "hypothesis_registry": REGISTRY_PATH,
        "overextension_mode": overextension,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(panels[0].symbols),
        "window_labels": list(window_labels),
        "n_windows": n_windows,
        "n_bars_per_window": [p.n_bars for p in panels],
        "lookback_bars": int(lookback_bars),
        "z_thresh": float(z_thresh),
        "crash_decile": float(crash_decile),
        "panel_rv_bars": int(panel_rv_bars),
        "horizons": list(horizons),
        "n_surrogates": int(n_surrogates),
        "n_bootstrap": int(n_bootstrap),
        "n_floor": int(n_floor),
        "seed": int(seed),
        "ci_level": CI_LEVEL,
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": fdr_family,
        "fdr_p_crit": _f(p_crit),
        "n_fdr_significant": int(n_fdr_sig),
        "gate_thresholds": {
            "surrogate_p_max": SURROGATE_P_MAX,
            "n_floor": int(n_floor),
            "min_windows": MIN_WINDOWS,
            "mu_positive_required": True,
            "ci_nonoverlap_required": True,
        },
        # Gate-neutral family-level observations (gate-auditor adjudicates):
        "any_amplified_consistent": bool(any_amplified),
        "horizon_rollup": horizon_rollup,
        "cells": cells,
    }


def _f(v: Any) -> float:
    """JSON-safe float (NaN/inf -> None handled by json? keep as float, use None)."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return float("nan")
    return x


# ----------------------------------------------------------------------------
# Report (Deutsch)
# ----------------------------------------------------------------------------

def _fmt(v: Any, nd: int = 6) -> str:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}"


def render_markdown(payload: dict[str, Any]) -> str:
    hyp = payload.get("hypothesis", HYPOTHESIS_ID)
    mode = payload.get("overextension_mode", "z")
    family = payload.get("fdr_family", FDR_FAMILY)
    if mode == "rank":
        axis_a = "rank — Achse A = Rang-1-Symbol je Bar (argmax |z|, schwellen-frei, DEC-18)"
        thresh_txt = "Z_THRESH=entfällt (Rang-Modus)"
    else:
        axis_a = f"z — Achse A = |z| ≥ Z_THRESH ({payload['z_thresh']})"
        thresh_txt = f"Z_THRESH={payload['z_thresh']}"
    L: list[str] = []
    L.append(f"# C-06 Cross-Sectional Ergodic Mean-Reversion — {hyp} Mess-Gate (KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {hyp} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Über-Dehnungs-Modus:** {axis_a}")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Panel: {', '.join(payload['symbols'])})")
    L.append(f"- **Fenster (vorregistriert):** {', '.join(payload['window_labels'])} "
             f"· Bars/Fenster: {payload['n_bars_per_window']}")
    L.append(f"- **L={payload['lookback_bars']} Bars · {thresh_txt} · "
             f"Crash-Dezil={payload['crash_decile']} · Panel-RV={payload['panel_rv_bars']} Bars · "
             f"Horizonte={payload['horizons']} Bars**")
    L.append(f"- **Surrogates={payload['n_surrogates']} · Bootstrap={payload['n_bootstrap']} · "
             f"N-Floor={payload['n_floor']} · Seed={payload['seed']}**")
    L.append(f"- **FDR-Familie:** {family} · **BH-FDR α:** {payload['fdr_alpha']} "
             f"· **p_crit:** {_fmt(payload['fdr_p_crit'], 4)}")
    L.append("- **KAPITALFREI:** ja — reiner Mess-/Verstärkungs-Test, keine bps/Edge/PnL/Sharpe.")
    L.append("")
    L.append(f"> Gate-Urteil fällt der gate-auditor gegen {hyp}. WEITER verlangt (ALLE gemeinsam): "
             f"konditioniert μ_rev>0 UND p≤0.05 (BH-FDR {family}) UND ≥2-Fenster-Konsistenz UND "
             "nicht-überlappende 95%-Bootstrap-CIs (konditioniert > Baseline) für ≥1 Horizont in "
             "≥2 Fenstern UND N≥30/Fenster. Nicht-Trivialitäts-Anker: konditioniert MUSS echt "
             "stärker revertieren als der unkonditionierte Baseline (E-04-/§6-verbotene Trivial-MR "
             "zählt NIE als Erfolg). Hartes Ein-Fenster-DROP, kein GRAUBEREICH.")
    L.append("")
    L.append("## Verstärkungs-Rollup je Horizont (Gate-Kern)")
    L.append("")
    L.append("| Horizont (Bars) | Fenster gemessen | bestehende Fenster | amplified_consistent (≥2) |")
    L.append("|---:|---:|---|---|")
    for r in payload["horizon_rollup"]:
        L.append(f"| {r['horizon']} | {r['n_windows_measured']} | {r['passing_windows']} | "
                 f"{'JA' if r['amplified_consistent'] else 'nein'} |")
    L.append("")
    L.append(f"**any_amplified_consistent:** {'JA' if payload['any_amplified_consistent'] else 'nein'} "
             f"· **FDR-signifikante Zellen:** {payload['n_fdr_significant']}")
    L.append("")
    L.append("## Detail je Fenster × Horizont × {konditioniert | Baseline}")
    L.append("")
    L.append("| Fenster | h | Art | μ_rev | CI_low | CI_high | N | surr_p | FDR-sig | "
             "Δμ | CI-nicht-überlappend | N-Floor |")
    L.append("|---|---:|---|---:|---:|---:|---:|---:|:---:|---:|:---:|:---:|")
    for c in payload["cells"]:
        L.append(
            f"| {c['window_label']} | {c['horizon']} | kond | "
            f"{_fmt(c['mu_rev_conditioned'])} | {_fmt(c['ci_low_conditioned'])} | "
            f"{_fmt(c['ci_high_conditioned'])} | {c['n_events_conditioned']} | "
            f"{_fmt(c['surrogate_p'], 4)} | {'ja' if c['fdr_significant'] else 'nein'} | "
            f"{_fmt(c['delta_mu'])} | {'JA' if c['ci_nonoverlap_vs_baseline'] else 'nein'} | "
            f"{'ja' if c['n_floor_met'] else 'NEIN'} |"
        )
        L.append(
            f"| {c['window_label']} | {c['horizon']} | base | "
            f"{_fmt(c['mu_rev_baseline'])} | {_fmt(c['ci_low_baseline'])} | "
            f"{_fmt(c['ci_high_baseline'])} | {c['n_events_baseline']} | — | — | — | — | — |"
        )
    L.append("")
    L.append(f"*Erzeugt von `c06_xmr/driver.py` (read-only Harvester-Backfill, DEC-15/DEC-17"
             f"{'/DEC-18' if mode == 'rank' else ''}). "
             f"capital_free=true. Endgültiges Gate-Urteil: gate-auditor gegen {hyp}.*")
    return "\n".join(L)


__all__ = [
    "SCHEMA_VERSION",
    "HYPOTHESIS_ID",
    "HYPOTHESIS_ID_RANK",
    "REGISTRY_PATH",
    "FDR_FAMILY",
    "FDR_FAMILY_RANK",
    "OVEREXTENSION_MODES",
    "DEFAULT_N_FLOOR",
    "MIN_WINDOWS",
    "DEFAULT_SYMBOLS",
    "render_markdown",
    "run",
]
