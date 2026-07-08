#!/usr/bin/env python3
"""F-XDOM1 two-stage BH-FDR aggregation for the Welle-4 cohort handoff.

Stage 1 is done INSIDE each driver: BH-FDR alpha=0.10 within each family
(F-BUNCH for H-09, F-POINTER for H-10, F-FRAG for H-12). This aggregator
performs Stage 2 - the Welle-4 ueber-family (F-XDOM1) BH-FDR alpha=0.10 over
the p-values of the cells/days that survived Stage 1 in any family. A
hypothesis counts as PASSED only if a cell survives BOTH stages, per the
F-XDOM1 pre-registration (`scinance2-impl/state/hypothesis_registry.md`,
section "F-XDOM1 - Welle-4-Ueber-Familie"; DEC-22).

Inputs are the three driver output directories (one per H-09/H-10/H-12).
Output is a deterministic Markdown report - same input -> bit-identical output
(audit trail) - plus an optional JSON sidecar.

Registered field mapping (verbatim from the driver run() payloads):
  H-09 c09_bunch_results.json  -> cells[]:          p = bootstrap_p,
                                                    flag = fdr_significant
  H-10 c10_pointer_results.json -> cells[]:         p = p_for_fdr,
                                                    flag = fdr_significant
  H-12 c12_frag_results.json   -> windows[].days[]: p = p_lambda2_one_factor
                                  (analyzed only),  flag = fdr_significant

Schema robustness: if a driver dir is missing or its JSON is malformed the
aggregator records the gap, never raises, and continues. Stage-2 still runs on
whatever survivors are available. Non-p-value gate parts (H-09 anti-gaming /
placebo dominance, H-10 N_pointer floor, H-12 validity precondition and
criteria (b)/(c)) are reported in SEPARATE sections because they do NOT enter
F-XDOM1 (the gate-auditor combines the signals).

KEIN Gesamturteil - gate-auditor entscheidet WEITER/DROP gegen H-09/H-10/H-12.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- BH-FDR (copy-by-design; see registry sec. 8.2 convention) ---------------
# The three research packages each ship their own BH implementation (cohesion
# over reuse for a calibration primitive). Stage 2 needs a single, audit-stable
# implementation - re-implementing here keeps the aggregator independent of any
# driver package import path (identical contract to aggregate_wave2_fdr.py).

FDR_ALPHA = 0.10


def benjamini_hochberg(
    p_values: List[float], alpha: float = FDR_ALPHA
) -> Tuple[List[bool], float]:
    """BH-FDR over a family of p-values. Returns (rejected_mask, p_crit).

    Input order is preserved in the output mask. ``p_crit`` is the largest
    p-value that passes (0.0 if none). Identical contract to the per-family
    implementations in the three research packages.
    """
    m = len(p_values)
    if m == 0:
        return [], 0.0
    order = sorted(range(m), key=lambda i: p_values[i])
    p_crit = 0.0
    k_max = -1
    for rank, idx in enumerate(order, start=1):
        if p_values[idx] <= (rank / m) * alpha:
            k_max = rank
            p_crit = p_values[idx]
    rejected = [False] * m
    if k_max >= 0:
        for rank, idx in enumerate(order, start=1):
            if rank <= k_max:
                rejected[idx] = True
    return rejected, p_crit


# --- JSON loaders (one per family) --------------------------------------------

def _load_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _find_first(dir_path: Path, names: Tuple[str, ...]) -> Optional[Path]:
    """Find the first matching driver output file under dir_path."""
    if not dir_path or not dir_path.is_dir():
        return None
    for name in names:
        cand = dir_path / name
        if cand.is_file():
            return cand
    # Fall back to recursive search (driver may have written into a subfolder).
    for name in names:
        for match in sorted(dir_path.rglob(name)):
            return match
    return None


def _extract_h09(payload: dict) -> List[Dict[str, Any]]:
    """Flatten H-09 (F-BUNCH) cells. p = bootstrap_p, flag = fdr_significant.

    Sentinel cells (missing data, p=1.0) stay in the family exactly as the
    driver registered them; they can never be Stage-1 survivors in practice
    but are counted in the family total.
    """
    out: List[Dict[str, Any]] = []
    for c in payload.get("cells") or []:
        p = c.get("bootstrap_p")
        if p is None:
            continue
        wi = c.get("window_index")
        out.append({
            "family": "F-BUNCH",
            "hypothesis": "H-09",
            "symbol": c.get("symbol"),
            "window": int(wi) if wi is not None else -1,
            "window_label": c.get("window_label"),
            "label": f"{c.get('symbol')}/w{wi}",
            "b_minus": c.get("b_minus"),
            "b_asymmetry": c.get("b_asymmetry"),
            "b_placebo_max": c.get("b_placebo_max"),
            "cell_valid": bool(c.get("cell_valid", False)),
            "sentinel_missing_data": bool(c.get("sentinel_missing_data", False)),
            "kink_is_placeholder": bool(c.get("kink_is_placeholder", False)),
            "cell_passed_registered_gate": bool(c.get("passed", False)),
            "p_value": float(p),
            "family_fdr_significant": bool(c.get("fdr_significant", False)),
        })
    return out


def _extract_h10(payload: dict) -> List[Dict[str, Any]]:
    """Flatten H-10 (F-POINTER) cells. p = p_for_fdr, flag = fdr_significant.

    ``p_for_fdr`` is the driver's own BH input (stage 1 = surrogate_p,
    stage 2 = permutation_p_two_sided, undefined -> 1.0). If an older payload
    lacks it, fall back to the stage-specific field; undefined -> 1.0
    (the driver's registered worst-case convention).
    """
    out: List[Dict[str, Any]] = []
    for c in payload.get("cells") or []:
        stage = c.get("stage")
        p = c.get("p_for_fdr")
        if p is None:
            p = c.get("surrogate_p") if stage == 1 else c.get("permutation_p_two_sided")
        if p is None:
            p = 1.0  # driver convention: undefined p counts as worst case
        n_ptr = c.get("n_pointer") if stage == 1 else c.get("n_pointer_in_window")
        out.append({
            "family": "F-POINTER",
            "hypothesis": "H-10",
            "stage": stage,
            "window_label": c.get("window_label"),
            "label": f"S{stage}/{c.get('window_label')}",
            "n_pointer": n_ptr,
            "n_pointer_floor_met": bool(c.get("n_pointer_floor_met", False)),
            "cell_pass_registered_gate": bool(c.get("cell_pass", False)),
            "p_value": float(p),
            "family_fdr_significant": bool(c.get("fdr_significant", False)),
        })
    return out


def _extract_h12(payload: dict) -> List[Dict[str, Any]]:
    """Flatten H-12 (F-FRAG) day tests. p = p_lambda2_one_factor (analyzed
    days only), flag = fdr_significant. The validity precondition and the
    criteria (b)/(c) are NOT p-tests - gathered by ``_extract_h12_windows``
    and reported separately (NOT part of F-XDOM1)."""
    out: List[Dict[str, Any]] = []
    for w in payload.get("windows") or []:
        wl = w.get("window_label")
        for d in w.get("days") or []:
            if not d.get("analyzed"):
                continue
            p = d.get("p_lambda2_one_factor")
            if p is None:
                continue
            out.append({
                "family": "F-FRAG",
                "hypothesis": "H-12",
                "window_label": wl,
                "date": d.get("date"),
                "label": f"{wl}/{d.get('date')}",
                "lambda2": d.get("lambda2"),
                "ipr_v2": d.get("ipr_v2"),
                "dominant_exchange_v2": d.get("dominant_exchange_v2"),
                "p_value": float(p),
                "family_fdr_significant": bool(d.get("fdr_significant", False)),
            })
    return out


def _extract_h12_windows(payload: dict) -> List[Dict[str, Any]]:
    """Per-window H-12 validity precondition + criteria (a)/(b)/(c) readings.
    Separate from F-XDOM1 (only (a)'s day p-values are p-tests, and those are
    handled per-day in ``_extract_h12``)."""
    out: List[Dict[str, Any]] = []
    for w in payload.get("windows") or []:
        v = w.get("validity") or {}
        c = w.get("criteria") or {}
        out.append({
            "window_label": w.get("window_label"),
            "n_days_valid": w.get("n_days_valid"),
            "n_days_fdr_significant": w.get("n_days_fdr_significant"),
            "window_valid": bool(v.get("window_valid", False)),
            "ipr_v1_ok_share": v.get("ipr_v1_ok_share"),
            "a_sig_day_share": c.get("a_sig_day_share"),
            "a_met": bool(c.get("a_met", False)),
            "b_median_ipr_v2_sig": c.get("b_median_ipr_v2_sig"),
            "b_met": bool(c.get("b_met", False)),
            "c_dominant_exchange": c.get("c_dominant_exchange"),
            "c_dominant_exchange_share": c.get("c_dominant_exchange_share"),
            "c_met": bool(c.get("c_met", False)),
            "all_criteria_met": bool(w.get("all_criteria_met", False)),
        })
    return out


# --- Two-stage aggregation core ------------------------------------------------

def aggregate(
    h09_payload: Optional[dict],
    h10_payload: Optional[dict],
    h12_payload: Optional[dict],
) -> Dict[str, Any]:
    """Run Stage 1 read-out + Stage 2 BH-FDR. Pure function (deterministic)."""
    variants_h09 = _extract_h09(h09_payload) if h09_payload else []
    variants_h10 = _extract_h10(h10_payload) if h10_payload else []
    variants_h12 = _extract_h12(h12_payload) if h12_payload else []

    # Stage 1 survivors per family (already computed by the driver - we just
    # collect them here; we do NOT recompute Stage 1 to avoid double counting).
    stage1_survivors = (
        [v for v in variants_h09 if v["family_fdr_significant"]]
        + [v for v in variants_h10 if v["family_fdr_significant"]]
        + [v for v in variants_h12 if v["family_fdr_significant"]]
    )

    # Stable, deterministic ordering for Stage-2 input (audit-trail).
    stage1_survivors.sort(key=lambda e: (e["hypothesis"], str(e.get("label") or "")))

    p_values = [float(v["p_value"]) for v in stage1_survivors]
    rejected, p_crit_stage2 = benjamini_hochberg(p_values, FDR_ALPHA)
    for v, rej in zip(stage1_survivors, rejected):
        v["f_xdom1_significant"] = bool(rej)

    # Per-hypothesis tallies.
    def _tally(variants: List[dict], hyp: str) -> Dict[str, int]:
        survivors_s1 = [v for v in variants if v["family_fdr_significant"]]
        survivors_s2 = [v for v in stage1_survivors
                        if v["hypothesis"] == hyp and v["f_xdom1_significant"]]
        # Stage-1 survivors that LOST in Stage 2 (the audit-flagging case).
        lost_s2 = [v for v in stage1_survivors
                   if v["hypothesis"] == hyp
                   and v["family_fdr_significant"]
                   and not v["f_xdom1_significant"]]
        return {
            "n_variants_total": len(variants),
            "n_stage1_survivors": len(survivors_s1),
            "n_stage2_survivors": len(survivors_s2),
            "n_lost_in_stage2": len(lost_s2),
        }

    # H-12: per-window Stage-2 survivor counts (the gate criterion (a) counts
    # FDR-sig day shares; the Beide-Stufen-Regel makes the Stage-2 set the
    # cohort-judgment-relevant one - report both so the gate-auditor sees the
    # full picture without recomputation).
    h12_windows = _extract_h12_windows(h12_payload) if h12_payload else []
    s2_dates_by_window: Dict[str, int] = {}
    for v in stage1_survivors:
        if v["hypothesis"] == "H-12" and v["f_xdom1_significant"]:
            wl = str(v.get("window_label"))
            s2_dates_by_window[wl] = s2_dates_by_window.get(wl, 0) + 1
    for w in h12_windows:
        w["n_days_stage2_survivors"] = s2_dates_by_window.get(
            str(w.get("window_label")), 0
        )

    # H-09: anti-gaming / validity flags (NOT p-tests, NOT in F-XDOM1).
    h09_flags: Optional[Dict[str, Any]] = None
    if h09_payload:
        h09_flags = {
            "gate_valid_assumptions": bool(
                h09_payload.get("gate_valid_assumptions", False)),
            "family_size_deviation": bool(
                h09_payload.get("family_size_deviation", False)),
            "n_sentinel_cells": h09_payload.get("n_sentinel_cells"),
            "any_window_truncated": bool(
                h09_payload.get("any_window_truncated", False)),
            "kink_placeholder_symbols": h09_payload.get(
                "kink_placeholder_symbols"),
            "placeholder_driven_pass_only": bool(
                h09_payload.get("placeholder_driven_pass_only", False)),
            "fdr_p_crit_stage1": h09_payload.get("fdr_p_crit"),
        }

    # H-10: family-level observation flags (NOT in F-XDOM1).
    h10_flags: Optional[Dict[str, Any]] = None
    if h10_payload:
        h10_flags = {
            "all_four_cells_pass": bool(
                h10_payload.get("all_four_cells_pass", False)),
            "fdr_p_crit_stage1": h10_payload.get("fdr_p_crit"),
        }

    # H-12: run-level validity status (NOT in F-XDOM1).
    h12_flags: Optional[Dict[str, Any]] = None
    if h12_payload:
        h12_flags = {
            "validity_status": h12_payload.get("validity_status"),
            "all_windows_valid": bool(
                h12_payload.get("all_windows_valid", False)),
            "all_criteria_met_all_windows": bool(
                h12_payload.get("all_criteria_met_all_windows", False)),
            "fdr_p_crit_stage1": h12_payload.get("fdr_p_crit"),
            "fdr_family_size": h12_payload.get("fdr_family_size"),
        }

    return {
        "fdr_alpha": FDR_ALPHA,
        "stage1_per_family": {
            "F-BUNCH (H-09)": _tally(variants_h09, "H-09"),
            "F-POINTER (H-10)": _tally(variants_h10, "H-10"),
            "F-FRAG (H-12)": _tally(variants_h12, "H-12"),
        },
        "stage2_p_crit": float(p_crit_stage2),
        "stage2_input_n": len(stage1_survivors),
        "stage2_survivors": [v for v in stage1_survivors if v["f_xdom1_significant"]],
        "stage1_survivors_all": stage1_survivors,
        "all_variants": {
            "H-09": variants_h09, "H-10": variants_h10, "H-12": variants_h12,
        },
        "h09_flags": h09_flags,
        "h10_flags": h10_flags,
        "h12_flags": h12_flags,
        "h12_windows": h12_windows,
        "drivers_present": {
            "H-09": h09_payload is not None,
            "H-10": h10_payload is not None,
            "H-12": h12_payload is not None,
        },
    }


# --- Markdown rendering (deterministic, no timestamp inside the body) ---------

def _fmt_p(p: Optional[float]) -> str:
    if p is None:
        return "n/a"
    try:
        return f"{float(p):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def _fmt_v(v: Any) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    if isinstance(v, float):
        return f"{v:+.4f}" if abs(v) < 1 else f"{v:.4f}"
    return str(v)


def render_markdown(agg: Dict[str, Any], *, run_label: str = "") -> str:
    L: List[str] = []
    L.append("# F-XDOM1 zweistufige BH-FDR - WAVE4_SUMMARY")
    L.append("")
    L.append("- Hypothesen-Registry: `scinance2-impl/state/hypothesis_registry.md` (F-XDOM1-Eintrag, DEC-22)")
    L.append("- Welle-4-Ueber-Familie F-XDOM1 = F-BUNCH (H-09) U F-POINTER (H-10) U F-FRAG (H-12)")
    L.append(f"- Stage 1: BH-FDR alpha={agg['fdr_alpha']} INNERHALB jeder Familie (Driver-intern).")
    L.append(f"- Stage 2: BH-FDR alpha={agg['fdr_alpha']} ueber alle Stage-1-Survivor GEMEINSAM.")
    L.append("- Eine Hypothese gilt im Kohorten-Lauf nur als bestanden, wenn sie BEIDE Stufen ueberlebt.")
    L.append("- H-11/H-13 sind data-gated und NICHT Teil von F-XDOM1 (Entsperr-Check ist kein Test).")
    L.append("- KEIN Gesamturteil hier - gate-auditor entscheidet WEITER/DROP gegen H-09/H-10/H-12.")
    if run_label:
        L.append(f"- Run-Label: `{run_label}`")
    L.append("")

    present = agg["drivers_present"]
    L.append("## Driver-Praesenz")
    L.append("")
    L.append("| Hypothese | Driver-Output gefunden |")
    L.append("|---|---|")
    L.append(f"| H-09 (F-BUNCH) | {_fmt_v(present['H-09'])} |")
    L.append(f"| H-10 (F-POINTER) | {_fmt_v(present['H-10'])} |")
    L.append(f"| H-12 (F-FRAG) | {_fmt_v(present['H-12'])} |")
    L.append("")

    # ---- Stage-1 / Stage-2 tallies per hypothesis -----------------------
    L.append("## Stage-1 / Stage-2 Bilanz je Hypothese")
    L.append("")
    L.append("| Hypothese (Familie) | Zellen gesamt | Stage-1 Survivor | Stage-2 Survivor | in Stage-2 verloren |")
    L.append("|---|---|---|---|---|")
    for fam, t in agg["stage1_per_family"].items():
        lost = t["n_lost_in_stage2"]
        lost_str = f"**{lost}**" if lost > 0 else str(lost)
        L.append(
            f"| {fam} | {t['n_variants_total']} | {t['n_stage1_survivors']} "
            f"| {t['n_stage2_survivors']} | {lost_str} |"
        )
    L.append("")
    L.append(
        f"Stage-2-Input: {agg['stage2_input_n']} Stage-1-Survivor-p-Werte * "
        f"Stage-2 p_crit (BH alpha={agg['fdr_alpha']}): "
        f"{_fmt_p(agg['stage2_p_crit'])}"
    )
    L.append("")
    any_lost = any(t["n_lost_in_stage2"] > 0
                   for t in agg["stage1_per_family"].values())
    if any_lost:
        L.append(
            "> **Achtung:** mindestens ein Pilot verliert in Stage 2 was er in "
            "Stage 1 hatte. Die F-XDOM1-Ueber-Familie greift - das ist der "
            "vorregistrierte Multiple-Testing-Schutz ueber die Welle-4-Kohorte."
        )
        L.append("")

    # ---- Stage-1 survivor listing with Stage-2 outcome ------------------
    L.append("## Stage-1 Survivor mit Stage-2-Ergebnis")
    L.append("")
    if not agg["stage1_survivors_all"]:
        L.append("(keine Stage-1-Survivor - Stage 2 entfaellt.)")
    else:
        L.append("| Hypothese | Familie | Zelle | p-Wert | Stage-1 | Stage-2 (F-XDOM1) |")
        L.append("|---|---|---|---|---|---|")
        for v in agg["stage1_survivors_all"]:
            L.append(
                f"| {v['hypothesis']} | {v['family']} | `{v.get('label', '?')}` "
                f"| {_fmt_p(v['p_value'])} | {_fmt_v(v['family_fdr_significant'])} "
                f"| {_fmt_v(v.get('f_xdom1_significant', False))} |"
            )
    L.append("")

    # Deterministic re-link of Stage-2 outcome by stable (hypothesis, label).
    s2_keys = {(x["hypothesis"], str(x.get("label") or ""))
               for x in agg["stage1_survivors_all"]
               if x.get("f_xdom1_significant")}

    # ---- Per-cell criteria per hypothesis (gate-relevant) ---------------
    L.append("## Gate-Kriterien je Zelle (gate-auditor-Input)")
    L.append("")

    # H-09
    h09 = agg["all_variants"]["H-09"]
    L.append("### H-09 * F-BUNCH (Risk-Limit-Tier-Bunching)")
    L.append("")
    if not h09:
        L.append("(keine H-09-Zellen - Driver-Output fehlt oder leer)")
    else:
        L.append("| Symbol | Fenster | b- | Asym (b- - b+) | Placebo-Max | p | Zelle gueltig | Sentinel | Stage-1 FDR | Gate-Zelle bestanden | Stage-2 FDR |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for v in h09:
            s2 = (v["hypothesis"], str(v.get("label") or "")) in s2_keys
            L.append(
                f"| {v.get('symbol')} | {v.get('window')} | {_fmt_v(v.get('b_minus'))} "
                f"| {_fmt_v(v.get('b_asymmetry'))} | {_fmt_v(v.get('b_placebo_max'))} "
                f"| {_fmt_p(v['p_value'])} | {_fmt_v(v['cell_valid'])} "
                f"| {_fmt_v(v['sentinel_missing_data'])} "
                f"| {_fmt_v(v['family_fdr_significant'])} "
                f"| {_fmt_v(v['cell_passed_registered_gate'])} | {_fmt_v(s2)} |"
            )
    f09 = agg.get("h09_flags")
    if f09:
        L.append("")
        L.append(
            f"Anti-Gaming/Validitaet (NICHT in F-XDOM1): gate_valid_assumptions="
            f"{_fmt_v(f09['gate_valid_assumptions'])} * family_size_deviation="
            f"{_fmt_v(f09['family_size_deviation'])} * n_sentinel_cells="
            f"{_fmt_v(f09['n_sentinel_cells'])} * any_window_truncated="
            f"{_fmt_v(f09['any_window_truncated'])} * K_s-Platzhalter="
            f"{_fmt_v(f09['kink_placeholder_symbols'])} * "
            f"placeholder_driven_pass_only={_fmt_v(f09['placeholder_driven_pass_only'])} * "
            f"Stage-1 p_crit={_fmt_p(f09['fdr_p_crit_stage1'])}"
        )
    L.append("")

    # H-10
    h10 = agg["all_variants"]["H-10"]
    L.append("### H-10 * F-POINTER (Cross-Stream-Pointer-Days + Pre-Event-Drift)")
    L.append("")
    if not h10:
        L.append("(keine H-10-Zellen - Driver-Output fehlt oder leer)")
    else:
        L.append("| Stufe | Fenster | N_pointer | N-Floor (>=3) | p (p_for_fdr) | Stage-1 FDR | Gate-Zelle bestanden | Stage-2 FDR |")
        L.append("|---|---|---|---|---|---|---|---|")
        for v in h10:
            s2 = (v["hypothesis"], str(v.get("label") or "")) in s2_keys
            L.append(
                f"| {v.get('stage')} | {v.get('window_label')} | {_fmt_v(v.get('n_pointer'))} "
                f"| {_fmt_v(v['n_pointer_floor_met'])} | {_fmt_p(v['p_value'])} "
                f"| {_fmt_v(v['family_fdr_significant'])} "
                f"| {_fmt_v(v['cell_pass_registered_gate'])} | {_fmt_v(s2)} |"
            )
    f10 = agg.get("h10_flags")
    if f10:
        L.append("")
        L.append(
            f"Familien-Beobachtung (gate-neutral): all_four_cells_pass="
            f"{_fmt_v(f10['all_four_cells_pass'])} * "
            f"Stage-1 p_crit={_fmt_p(f10['fdr_p_crit_stage1'])} * "
            f"Hinweis: der N_pointer-Floor ist KEIN p-Test und NICHT in F-XDOM1."
        )
    L.append("")

    # H-12 (per-window aggregate view; the day-level detail lives in the
    # survivor table above and in the driver's own report).
    L.append("### H-12 * F-FRAG (Cross-Exchange-Fragmentierungsmatrix) - je Fenster")
    L.append("")
    h12w = agg.get("h12_windows") or []
    if not h12w:
        L.append("(keine H-12-Fenster - Driver-Output fehlt oder leer)")
    else:
        L.append("| Fenster | gueltige Tage | Stage-1 FDR-sig Tage | Stage-2 FDR-sig Tage | (a) Anteil | (a) | (b) Median-IPR(v2) | (b) | (c) dominante Boerse (Anteil) | (c) | Fenster gueltig |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for w in h12w:
            dom = w.get("c_dominant_exchange") or "n/a"
            L.append(
                f"| {w.get('window_label')} | {_fmt_v(w.get('n_days_valid'))} "
                f"| {_fmt_v(w.get('n_days_fdr_significant'))} "
                f"| {_fmt_v(w.get('n_days_stage2_survivors'))} "
                f"| {_fmt_v(w.get('a_sig_day_share'))} | {_fmt_v(w['a_met'])} "
                f"| {_fmt_v(w.get('b_median_ipr_v2_sig'))} | {_fmt_v(w['b_met'])} "
                f"| {dom} ({_fmt_v(w.get('c_dominant_exchange_share'))}) "
                f"| {_fmt_v(w['c_met'])} | {_fmt_v(w['window_valid'])} |"
            )
    f12 = agg.get("h12_flags")
    if f12:
        L.append("")
        L.append(
            f"Validitaets-Status (NICHT in F-XDOM1, Vorbedingung vor dem Gate): "
            f"**{str(f12['validity_status']).upper()}** * all_windows_valid="
            f"{_fmt_v(f12['all_windows_valid'])} * all_criteria_met_all_windows="
            f"{_fmt_v(f12['all_criteria_met_all_windows'])} * "
            f"Stage-1 Familie: {_fmt_v(f12['fdr_family_size'])} Tages-Tests, "
            f"p_crit={_fmt_p(f12['fdr_p_crit_stage1'])}"
        )
    L.append("")

    # ---- Non-p-value gate parts (NOT part of F-XDOM1) --------------------
    L.append("## Nicht-p-Wert-Gate-Bestandteile - separat, NICHT in F-XDOM1")
    L.append("")
    L.append(
        "F-XDOM1 korrigiert ausschliesslich die p-Wert-Tests der drei Familien. "
        "Die uebrigen registrierten Gate-/Validitaets-Bestandteile bleiben "
        "unveraendert in Kraft und werden vom gate-auditor separat geprueft: "
        "H-09 b->=1,0 / Asymmetrie>=0,5 / Placebo-Dominanz / N-Floor / "
        "Anti-Gaming (gate_valid_assumptions); H-10 N_pointer>=3 je Fenster "
        "(Floor NICHT absenkbar); H-12 Validitaets-Vorbedingung (IPR(v1), "
        "35-Tage-Floor - verfehlt -> Lauf UNGUELTIG, KEIN Verdikt) und "
        "Kriterien (b)/(c). Hartes Ein-Fenster-DROP-Kriterium je Hypothese "
        "wie registriert; kein GRAUBEREICH."
    )
    L.append("")
    return "\n".join(L) + "\n"


# --- CLI -----------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="F-XDOM1 two-stage BH-FDR aggregator (Welle-4 Kohorten-Handoff)."
    )
    ap.add_argument("--h09", type=Path, required=True,
                    help="Driver-Output-Verzeichnis des H-09-Laufs (enthaelt c09_bunch_results.json)")
    ap.add_argument("--h10", type=Path, required=True,
                    help="Driver-Output-Verzeichnis des H-10-Laufs (enthaelt c10_pointer_results.json)")
    ap.add_argument("--h12", type=Path, required=True,
                    help="Driver-Output-Verzeichnis des H-12-Laufs (enthaelt c12_frag_results.json)")
    ap.add_argument("--out", type=Path, required=True,
                    help="Ausgabe-Markdown (z.B. WAVE4_SUMMARY.md)")
    ap.add_argument("--json", type=Path, default=None,
                    help="Optionaler JSON-Sidecar mit den Aggregat-Daten")
    ap.add_argument("--label", default="",
                    help="Optionales Run-Label fuer den Bericht (nicht determinismus-relevant)")
    args = ap.parse_args(argv)

    h09_path = _find_first(args.h09, ("c09_bunch_results.json",))
    h10_path = _find_first(args.h10, ("c10_pointer_results.json",))
    h12_path = _find_first(args.h12, ("c12_frag_results.json",))

    h09_payload = _load_json(h09_path) if h09_path else None
    h10_payload = _load_json(h10_path) if h10_path else None
    h12_payload = _load_json(h12_path) if h12_path else None

    agg = aggregate(h09_payload, h10_payload, h12_payload)
    md = render_markdown(agg, run_label=args.label)

    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
    except Exception as exc:
        print(f"AGGREGATE_WAVE4 ERROR (markdown write): {exc}", file=sys.stderr)
        return 1

    if args.json is not None:
        try:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(agg, sort_keys=True, indent=2),
                                 encoding="utf-8")
        except Exception as exc:
            print(f"AGGREGATE_WAVE4 ERROR (json write): {exc}", file=sys.stderr)
            # md was written; do not fail the run only on the sidecar.

    n_s1 = sum(t["n_stage1_survivors"] for t in agg["stage1_per_family"].values())
    n_s2 = sum(t["n_stage2_survivors"] for t in agg["stage1_per_family"].values())
    n_lost = sum(t["n_lost_in_stage2"] for t in agg["stage1_per_family"].values())
    print(
        f"F-XDOM1 | stage1_survivors={n_s1} stage2_survivors={n_s2} "
        f"lost_in_stage2={n_lost} stage2_p_crit={_fmt_p(agg['stage2_p_crit'])} "
        f"-> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
