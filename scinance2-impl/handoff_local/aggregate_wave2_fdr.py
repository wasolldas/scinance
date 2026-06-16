#!/usr/bin/env python3
"""F-WAVE2 two-stage BH-FDR aggregation for the Welle-2 handoff (WP-4).

Stage 1 is done INSIDE each driver: BH-FDR alpha=0.10 within each family
(F-LEADLAG for H-04, F-OFI for H-05, F-ENTROPY for H-06). This aggregator
performs Stage 2 - the Welle-2 ueber-family (F-WAVE2) BH-FDR alpha=0.10 over
the p-values of the variants that survived Stage 1 in any family. A hypothesis
counts as PASSED only if a variant survives BOTH stages, per the Welle-2
Registry-Disziplin-Nachtrag (`scinance2-impl/state/hypothesis_registry.md`).

Inputs are the three driver output directories (one per H-04/H-05/H-06).
Output is a deterministic Markdown report - same input -> bit-identical output
(audit trail) - plus an optional JSON sidecar.

Schema robustness: if a driver dir is missing or its JSON is malformed the
aggregator records the gap, never raises, and continues. Stage-2 still runs on
whatever survivors are available. PRE-Gate failures in H-06 are reported as a
SEPARATE section because the PRE-Gate is NOT a p-value test and does NOT enter
F-WAVE2 (gate-auditor combines the two signals).

KEIN Gesamturteil - gate-auditor entscheidet WEITER/DROP gegen H-04/H-05/H-06.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- BH-FDR (copy-by-design; see registry sec. 8.2 convention) -------------------
# The three research packages each ship their own BH implementation (cohesion
# over reuse for a calibration primitive). Stage 2 needs a single, audit-stable
# implementation - re-implementing here keeps the aggregator independent of any
# driver package import path.

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


# --- JSON loaders (one per family) -------------------------------------------

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


def _extract_h04(payload: dict) -> List[Dict[str, Any]]:
    """Flatten H-04 (C-17/C-41) variants. Each entry carries family, label,
    p-value, family-FDR flag, lag in ms, lead source."""
    out: List[Dict[str, Any]] = []
    for w in payload.get("windows") or []:
        wi = int(w.get("index", -1))
        for v in w.get("variants") or []:
            surr = v.get("surrogate") or {}
            p = surr.get("p_value")
            if p is None:
                continue
            out.append({
                "family": "F-LEADLAG",
                "hypothesis": "H-04",
                "window": wi,
                "axis": v.get("axis"),
                "label": v.get("label"),
                "source": v.get("source"),
                "target": v.get("target"),
                "lag_ms": v.get("lag_ms"),
                "observed_stat": surr.get("observed_stat"),
                "p_value": float(p),
                "family_fdr_significant": bool(v.get("fdr_significant", False)),
            })
    return out


def _extract_h05(payload: dict) -> List[Dict[str, Any]]:
    """Flatten H-05 (C-01) variants. Each entry carries the sign_direction
    flag so the gate-auditor can spot inverse-significant survivors."""
    out: List[Dict[str, Any]] = []
    for r in payload.get("results") or []:
        sym = r.get("symbol")
        wi = int(r.get("window_index", -1))
        for v in r.get("variants") or []:
            p = v.get("surrogate_p")
            if p is None:
                continue
            out.append({
                "family": "F-OFI",
                "hypothesis": "H-05",
                "symbol": sym,
                "window": wi,
                "delta_s": v.get("delta_s") or v.get("delta") or v.get("delta_seconds"),
                "label": v.get("label"),
                "corr": v.get("corr"),
                "sign_direction": int(v.get("sign_direction", 0)),
                "abs_corr": v.get("abs_corr"),
                "hit_rate": v.get("hit_rate"),
                "p_value": float(p),
                "family_fdr_significant": bool(v.get("fdr_significant", False)),
                "h05_positive_consistent": bool(v.get("h05_positive_consistent", False)),
                "inverse_significant": bool(v.get("inverse_significant", False)),
            })
    return out


def _extract_h06(payload: dict) -> List[Dict[str, Any]]:
    """Flatten H-06 (C-07) variants from the main-gate axis only. The PRE-Gate
    rho is a separate signal - gathered by ``_extract_h06_pre`` - and is NOT
    part of F-WAVE2 (it is not a p-value test)."""
    out: List[Dict[str, Any]] = []
    for r in payload.get("results") or []:
        sym = r.get("symbol")
        wi = int(r.get("window_index", -1))
        for v in r.get("variants") or []:
            p = v.get("surrogate_p")
            if p is None:
                continue
            out.append({
                "family": "F-ENTROPY",
                "hypothesis": "H-06",
                "symbol": sym,
                "window": wi,
                "delta_min": v.get("delta_min") or v.get("delta") or v.get("delta_minutes"),
                "label": v.get("label"),
                "mi": v.get("mi"),
                "auc_lift": v.get("auc_lift"),
                "n_g1": v.get("n_g1"),
                "p_value": float(p),
                "family_fdr_significant": bool(v.get("fdr_significant", False)),
                "auc_lift_floor_met": bool(v.get("auc_lift_floor_met", False)),
                "main_gate_variant_met": bool(v.get("main_gate_variant_met", False)),
            })
    return out


def _extract_h06_pre(payload: dict) -> List[Dict[str, Any]]:
    """Per-(symbol, window) PRE-Gate rho readings. Separate from F-WAVE2."""
    out: List[Dict[str, Any]] = []
    for r in payload.get("results") or []:
        pg = r.get("pre_gate") or {}
        out.append({
            "symbol": r.get("symbol"),
            "window": int(r.get("window_index", -1)),
            "rho": pg.get("rho"),
            "n_pairs": pg.get("n_pairs"),
            "rho_floor_met": bool(pg.get("rho_floor_met", False)),
        })
    return out


# --- Two-stage aggregation core ---------------------------------------------

def aggregate(
    h04_payload: Optional[dict],
    h05_payload: Optional[dict],
    h06_payload: Optional[dict],
) -> Dict[str, Any]:
    """Run Stage 1 read-out + Stage 2 BH-FDR. Pure function (deterministic)."""
    variants_h04 = _extract_h04(h04_payload) if h04_payload else []
    variants_h05 = _extract_h05(h05_payload) if h05_payload else []
    variants_h06 = _extract_h06(h06_payload) if h06_payload else []

    # Stage 1 survivors per family (already computed by the driver - we just
    # collect them here; we do NOT recompute Stage 1 to avoid double counting).
    stage1_survivors = (
        [v for v in variants_h04 if v["family_fdr_significant"]]
        + [v for v in variants_h05 if v["family_fdr_significant"]]
        + [v for v in variants_h06 if v["family_fdr_significant"]]
    )

    # Stable, deterministic ordering for Stage-2 input (audit-trail).
    stage1_survivors.sort(key=lambda e: (
        e["hypothesis"], e.get("symbol") or "", int(e.get("window", -1)),
        str(e.get("label") or "")
    ))

    p_values = [float(v["p_value"]) for v in stage1_survivors]
    rejected, p_crit_stage2 = benjamini_hochberg(p_values, FDR_ALPHA)
    for v, rej in zip(stage1_survivors, rejected):
        v["f_wave2_significant"] = bool(rej)

    # Per-hypothesis tallies.
    def _tally(variants: List[dict], hyp: str) -> Dict[str, int]:
        survivors_s1 = [v for v in variants if v["family_fdr_significant"]]
        # A variant survives Stage 2 only if it survived Stage 1 first.
        survivors_s2 = [v for v in stage1_survivors
                        if v["hypothesis"] == hyp and v["f_wave2_significant"]]
        # Stage-1 survivors that LOST in Stage 2 (the audit-flagging case).
        lost_s2 = [v for v in stage1_survivors
                   if v["hypothesis"] == hyp
                   and v["family_fdr_significant"]
                   and not v["f_wave2_significant"]]
        return {
            "n_variants_total": len(variants),
            "n_stage1_survivors": len(survivors_s1),
            "n_stage2_survivors": len(survivors_s2),
            "n_lost_in_stage2": len(lost_s2),
        }

    h06_pre = _extract_h06_pre(h06_payload) if h06_payload else []
    h05_inverse_flags: List[Dict[str, Any]] = []
    for v in variants_h05:
        if v["inverse_significant"]:
            h05_inverse_flags.append({
                "symbol": v.get("symbol"), "window": v.get("window"),
                "delta_s": v.get("delta_s"), "label": v.get("label"),
                "corr": v.get("corr"), "p_value": v.get("p_value"),
            })

    return {
        "fdr_alpha": FDR_ALPHA,
        "stage1_per_family": {
            "F-LEADLAG (H-04)": _tally(variants_h04, "H-04"),
            "F-OFI (H-05)": _tally(variants_h05, "H-05"),
            "F-ENTROPY (H-06)": _tally(variants_h06, "H-06"),
        },
        "stage2_p_crit": float(p_crit_stage2),
        "stage2_input_n": len(stage1_survivors),
        "stage2_survivors": [v for v in stage1_survivors if v["f_wave2_significant"]],
        "stage1_survivors_all": stage1_survivors,
        "all_variants": {
            "H-04": variants_h04, "H-05": variants_h05, "H-06": variants_h06,
        },
        "h06_pre_gate": h06_pre,
        "h05_inverse_flags": h05_inverse_flags,
        "drivers_present": {
            "H-04": h04_payload is not None,
            "H-05": h05_payload is not None,
            "H-06": h06_payload is not None,
        },
    }


# --- Markdown rendering (deterministic, no timestamp inside the body) -------

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
    L.append("# F-WAVE2 zweistufige BH-FDR - WAVE2_SUMMARY")
    L.append("")
    L.append(f"- Hypothesen-Registry: `scinance2-impl/state/hypothesis_registry.md`")
    L.append(f"- Welle-2-Ueber-Familie F-WAVE2 = F-LEADLAG (H-04) U F-OFI (H-05) U F-ENTROPY (H-06)")
    L.append(f"- Stage 1: BH-FDR alpha={agg['fdr_alpha']} INNERHALB jeder Familie (Driver-intern).")
    L.append(f"- Stage 2: BH-FDR alpha={agg['fdr_alpha']} ueber alle Stage-1-Survivor GEMEINSAM.")
    L.append("- Eine Hypothese gilt nur als bestanden, wenn sie BEIDE Stufen ueberlebt.")
    L.append("- KEIN Gesamturteil hier - gate-auditor entscheidet WEITER/DROP gegen H-04/H-05/H-06.")
    if run_label:
        L.append(f"- Run-Label: `{run_label}`")
    L.append("")

    present = agg["drivers_present"]
    L.append("## Driver-Praesenz")
    L.append("")
    L.append("| Hypothese | Driver-Output gefunden |")
    L.append("|---|---|")
    L.append(f"| H-04 (F-LEADLAG) | {_fmt_v(present['H-04'])} |")
    L.append(f"| H-05 (F-OFI) | {_fmt_v(present['H-05'])} |")
    L.append(f"| H-06 (F-ENTROPY) | {_fmt_v(present['H-06'])} |")
    L.append("")

    # ---- Stage-1 / Stage-2 tallies per hypothesis -----------------------
    L.append("## Stage-1 / Stage-2 Bilanz je Hypothese")
    L.append("")
    L.append("| Hypothese (Familie) | Varianten gesamt | Stage-1 Survivor | Stage-2 Survivor | in Stage-2 verloren |")
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
            "Stage 1 hatte. Die F-WAVE2-Ueber-Familie greift - das ist der "
            "vorregistrierte Multiple-Testing-Schutz ueber die drei Welle-2-Pilots."
        )
        L.append("")

    # ---- Stage-1 survivor listing with Stage-2 outcome ------------------
    L.append("## Stage-1 Survivor mit Stage-2-Ergebnis")
    L.append("")
    if not agg["stage1_survivors_all"]:
        L.append("(keine Stage-1-Survivor - Stage 2 entfaellt.)")
    else:
        L.append("| Hypothese | Familie | Variante | p-Wert | Stage-1 | Stage-2 |")
        L.append("|---|---|---|---|---|---|")
        for v in agg["stage1_survivors_all"]:
            L.append(
                f"| {v['hypothesis']} | {v['family']} | `{v.get('label', '?')}` "
                f"| {_fmt_p(v['p_value'])} | {_fmt_v(v['family_fdr_significant'])} "
                f"| {_fmt_v(v.get('f_wave2_significant', False))} |"
            )
    L.append("")

    # ---- Per-window criteria per hypothesis (gate-relevant) -------------
    L.append("## Gate-Kriterien je Fenster (gate-auditor-Input)")
    L.append("")

    # H-04
    h04 = agg["all_variants"]["H-04"]
    L.append("### H-04 * F-LEADLAG (C-17/C-41 Lead-Lag)")
    L.append("")
    if not h04:
        L.append("(keine H-04-Varianten - Driver-Output fehlt oder leer)")
    else:
        L.append("| Fenster | Achse | Variante | Lag [ms] | Lead | obs.Stat | p | Stage-1 FDR | Stage-2 FDR |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        s2_set = {id(x) for x in agg["stage1_survivors_all"] if x.get("f_wave2_significant")}
        # Re-link by stable label/window because survivors carry copies.
        s2_keys = {(x["hypothesis"], x.get("window"), str(x.get("label") or ""))
                   for x in agg["stage1_survivors_all"]
                   if x.get("f_wave2_significant")}
        for v in h04:
            key = (v["hypothesis"], v.get("window"), str(v.get("label") or ""))
            s2 = key in s2_keys
            L.append(
                f"| {v.get('window')} | {v.get('axis')} | `{v.get('label')}` "
                f"| {_fmt_v(v.get('lag_ms'))} | {v.get('source') or 'n/a'} "
                f"| {_fmt_v(v.get('observed_stat'))} | {_fmt_p(v['p_value'])} "
                f"| {_fmt_v(v['family_fdr_significant'])} | {_fmt_v(s2)} |"
            )
    L.append("")

    # H-05
    h05 = agg["all_variants"]["H-05"]
    L.append("### H-05 * F-OFI (C-01 OFI-Vorzeichen)")
    L.append("")
    if not h05:
        L.append("(keine H-05-Varianten - Driver-Output fehlt oder leer)")
    else:
        L.append("| Symbol | Fenster | delta [s] | sign | |corr| | hit_rate | p | Stage-1 FDR | inverse_sig | Stage-2 FDR |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        s2_keys = {(x["hypothesis"], x.get("symbol"), x.get("window"), str(x.get("label") or ""))
                   for x in agg["stage1_survivors_all"]
                   if x.get("f_wave2_significant")}
        for v in h05:
            key = (v["hypothesis"], v.get("symbol"), v.get("window"),
                   str(v.get("label") or ""))
            s2 = key in s2_keys
            sd = v["sign_direction"]
            sd_s = "+" if sd > 0 else ("-" if sd < 0 else "0")
            L.append(
                f"| {v.get('symbol')} | {v.get('window')} | {_fmt_v(v.get('delta_s'))} "
                f"| {sd_s} | {_fmt_v(v.get('abs_corr'))} | {_fmt_v(v.get('hit_rate'))} "
                f"| {_fmt_p(v['p_value'])} | {_fmt_v(v['family_fdr_significant'])} "
                f"| {_fmt_v(v['inverse_significant'])} | {_fmt_v(s2)} |"
            )
    L.append("")

    # H-06
    h06 = agg["all_variants"]["H-06"]
    L.append("### H-06 * F-ENTROPY (C-07 Permutation Entropy) - Haupt-Gate-Varianten")
    L.append("")
    if not h06:
        L.append("(keine H-06-Varianten - Driver-Output fehlt oder leer; vermutlich PRE-Gate-Failer)")
    else:
        L.append("| Symbol | Fenster | delta [min] | MI | AUC-Lift | n_g1 | p | Stage-1 FDR | Stage-2 FDR |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        s2_keys = {(x["hypothesis"], x.get("symbol"), x.get("window"), str(x.get("label") or ""))
                   for x in agg["stage1_survivors_all"]
                   if x.get("f_wave2_significant")}
        for v in h06:
            key = (v["hypothesis"], v.get("symbol"), v.get("window"),
                   str(v.get("label") or ""))
            s2 = key in s2_keys
            L.append(
                f"| {v.get('symbol')} | {v.get('window')} | {_fmt_v(v.get('delta_min'))} "
                f"| {_fmt_v(v.get('mi'))} | {_fmt_v(v.get('auc_lift'))} "
                f"| {v.get('n_g1')} | {_fmt_p(v['p_value'])} "
                f"| {_fmt_v(v['family_fdr_significant'])} | {_fmt_v(s2)} |"
            )
    L.append("")

    # ---- H-06 PRE-Gate (NOT part of F-WAVE2) ----------------------------
    L.append("## H-06 PRE-Gate (rho >= 0.30) - separat, NICHT in F-WAVE2")
    L.append("")
    L.append(
        "Das PRE-Gate ist ein Korrelations-Floor, KEIN p-Wert-Test. Es zaehlt nicht "
        "in die Welle-2-Ueber-Familie. Ein-Fenster-DROP-Kriterium (PRD sec. 8.5): rho < 0.30 "
        "in EINEM Fenster -> H-06 DROP, unabhaengig von Stage 2."
    )
    L.append("")
    if not agg["h06_pre_gate"]:
        L.append("(kein H-06-Driver-Output - PRE-Gate-Status unbekannt)")
    else:
        L.append("| Symbol | Fenster | rho | n_pairs | rho >= 0.30 |")
        L.append("|---|---|---|---|---|")
        for pg in agg["h06_pre_gate"]:
            L.append(
                f"| {pg.get('symbol')} | {pg.get('window')} | "
                f"{_fmt_v(pg.get('rho'))} | {pg.get('n_pairs')} | "
                f"{_fmt_v(pg.get('rho_floor_met'))} |"
            )
    L.append("")

    # ---- H-05 inverse_significant flags (H-05b trigger) -----------------
    L.append("## H-05 inverse_significant je Symbol/delta (H-05b-Trigger-Erkennung)")
    L.append("")
    L.append(
        "Ein signifikant INVERSES OFI-Vorzeichen ist KEIN H-05-Bestehen, "
        "sondern Ausloeser fuer eine NEUE H-05b-Pre-Registration "
        "(MM-Replenishment-Lesart). Registry-Disziplin sec. 2: kein Verschieben der Torpfosten."
    )
    L.append("")
    if not agg["h05_inverse_flags"]:
        L.append("(keine inverse_significant-Flags - kein H-05b-Trigger)")
    else:
        L.append("| Symbol | Fenster | delta [s] | corr | p |")
        L.append("|---|---|---|---|---|")
        for f in agg["h05_inverse_flags"]:
            L.append(
                f"| {f.get('symbol')} | {f.get('window')} | "
                f"{_fmt_v(f.get('delta_s'))} | {_fmt_v(f.get('corr'))} | "
                f"{_fmt_p(f.get('p_value'))} |"
            )
    L.append("")
    return "\n".join(L) + "\n"


# --- CLI --------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="F-WAVE2 two-stage BH-FDR aggregator (Welle-2 Handoff WP-4)."
    )
    ap.add_argument("--h04", type=Path, required=True,
                    help="Driver-Output-Verzeichnis des H-04-Laufs (enthaelt c17_c41_results.json)")
    ap.add_argument("--h05", type=Path, required=True,
                    help="Driver-Output-Verzeichnis des H-05-Laufs (enthaelt c01_ofi_sign_results.json)")
    ap.add_argument("--h06", type=Path, required=True,
                    help="Driver-Output-Verzeichnis des H-06-Laufs (enthaelt c07_pe_results.json)")
    ap.add_argument("--out", type=Path, required=True,
                    help="Ausgabe-Markdown (z.B. WAVE2_SUMMARY.md)")
    ap.add_argument("--json", type=Path, default=None,
                    help="Optionaler JSON-Sidecar mit den Aggregat-Daten")
    ap.add_argument("--label", default="",
                    help="Optionales Run-Label fuer den Bericht (nicht determinismus-relevant)")
    args = ap.parse_args(argv)

    h04_path = _find_first(args.h04, ("c17_c41_results.json",))
    h05_path = _find_first(args.h05, ("c01_ofi_sign_results.json",))
    h06_path = _find_first(args.h06, ("c07_pe_results.json",))

    h04_payload = _load_json(h04_path) if h04_path else None
    h05_payload = _load_json(h05_path) if h05_path else None
    h06_payload = _load_json(h06_path) if h06_path else None

    agg = aggregate(h04_payload, h05_payload, h06_payload)
    md = render_markdown(agg, run_label=args.label)

    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
    except Exception as exc:
        print(f"AGGREGATE_WAVE2 ERROR (markdown write): {exc}", file=sys.stderr)
        return 1

    if args.json is not None:
        try:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(agg, sort_keys=True, indent=2),
                                 encoding="utf-8")
        except Exception as exc:
            print(f"AGGREGATE_WAVE2 ERROR (json write): {exc}", file=sys.stderr)
            # md was written; do not fail the run only on the sidecar.

    n_s1 = sum(t["n_stage1_survivors"] for t in agg["stage1_per_family"].values())
    n_s2 = sum(t["n_stage2_survivors"] for t in agg["stage1_per_family"].values())
    n_lost = sum(t["n_lost_in_stage2"] for t in agg["stage1_per_family"].values())
    print(
        f"F-WAVE2 | stage1_survivors={n_s1} stage2_survivors={n_s2} "
        f"lost_in_stage2={n_lost} stage2_p_crit={_fmt_p(agg['stage2_p_crit'])} "
        f"-> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
