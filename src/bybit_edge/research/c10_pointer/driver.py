"""Orchestration + gate-neutral payload for the C-10 pointer mess-gate (H-10).

Pipeline (registry H-10, pre-fixed):
  1. Detrend + Cropper-score all 30 detection series on the full daily grid.
  2. Restrict scores to the USABLE range (data start + 21-day burn-in ..
     data end); detect pointer days; split into W1/W2.
  3. Stage 1: circular-surrogate p per window for the pointer-day count.
  4. Stage 2: held-out dvol index D_t, Delta_pre drift, permutation p per
     window (two-sided, null days >= 6 days from every pointer day).
  5. BH-FDR alpha=0.10 over the F-POINTER family (4 cells = 2 stages x 2
     windows) — own copy in ``stats.py``.

The driver renders NO overall verdict — the gate-auditor adjudicates against
H-10. Per-cell booleans (``cell_pass`` etc.) and the family-level
``all_four_cells_pass`` are gate-neutral observations only.

KAPITALFREI: ``capital_free: true`` in the payload; there is NO capital-metric
field of any kind anywhere.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

import numpy as np

from .cropper import (
    C_THRESH,
    CROPPER_HALF_WINDOW,
    DETREND_MIN_PERIODS,
    DETREND_WINDOW,
    N_AVAIL_FLOOR,
    NEUWIRTH_HALF_WINDOW,
    SHARE_FLOOR,
    detect_pointer_days,
    score_matrix,
)
from .stats import (
    FDR_ALPHA,
    FDR_FAMILY,
    MIN_NULL_GAP_DAYS,
    N_POINTER_FLOOR,
    SURROGATE_P_MAX,
    benjamini_hochberg,
    delta_pre,
    dvol_index,
    stage1_surrogate_p,
    stage2_permutation_p,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-10"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"

#: Registry H-10 fixed data binding + windows (UTC daily grid).
DEFAULT_DATA_START = "2026-03-27"
DEFAULT_DATA_END = "2026-07-04"
DEFAULT_BURN_IN_DAYS = 21
DEFAULT_WINDOWS: tuple[tuple[str, str, str], ...] = (
    ("W1", "2026-04-17", "2026-05-25"),
    ("W2", "2026-05-26", "2026-07-04"),
)


def run(
    days: list[str],
    detection_names: list[str],
    detection_panel: np.ndarray,
    dvol_btc: np.ndarray,
    dvol_eth: np.ndarray,
    *,
    windows: tuple[tuple[str, str, str], ...] = DEFAULT_WINDOWS,
    burn_in_days: int = DEFAULT_BURN_IN_DAYS,
    n_surrogates: int = 1000,
    n_permutations: int = 1000,
    seed: int = 42,
    source: str = "",
    dvol_parse_modes: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run the H-10 two-stage pointer gate; return the gate-neutral payload.

    ``days`` is the full daily grid (ISO dates, includes the burn-in);
    ``detection_panel`` is (T x N) daily values aligned to ``days``;
    ``dvol_btc``/``dvol_eth`` are the HELD-OUT target levels on the same grid
    (NEVER part of ``detection_panel`` — enforced only by construction here;
    the caller must not mix them in). ``windows`` are (label, start, end)
    inclusive; both must lie inside the usable range. ``dvol_parse_modes``
    (optional, from ``load_daily_dvol``'s ``info`` out-dict) is surfaced
    verbatim in the payload as ``dvol_parse_mode`` so a fallback field guess
    is auditable post hoc (audit_h10 BUG-4).
    """
    X = np.asarray(detection_panel, dtype=np.float64)
    t_full, n_series = X.shape
    if len(days) != t_full:
        raise ValueError(f"days ({len(days)}) and panel rows ({t_full}) differ")
    if len(detection_names) != n_series:
        raise ValueError("detection_names length != panel columns")
    day_idx = {d: i for i, d in enumerate(days)}
    if burn_in_days >= t_full:
        raise ValueError("burn-in longer than the daily grid")
    u0 = burn_in_days  # usable range starts right after the burn-in
    usable_start = days[u0]

    # global window index arrays + usable-relative masks
    win_global: list[np.ndarray] = []
    win_masks_usable: list[np.ndarray] = []
    t_usable = t_full - u0
    for label, w_start, w_end in windows:
        if w_start not in day_idx or w_end not in day_idx:
            raise ValueError(f"window {label} ({w_start}..{w_end}) outside the daily grid")
        a, b = day_idx[w_start], day_idx[w_end]
        if a < u0:
            raise ValueError(f"window {label} starts inside the {burn_in_days}-day burn-in")
        if b < a:
            raise ValueError(f"window {label} end before start")
        win_global.append(np.arange(a, b + 1, dtype=np.int64))
        m = np.zeros(t_usable, dtype=bool)
        m[a - u0: b - u0 + 1] = True
        win_masks_usable.append(m)

    # 1) detrend + Cropper scores (full grid), then usable slice.
    print(f"[c10_pointer] scoring {n_series} detection series over {t_full} days "
          f"(usable from {usable_start})", file=sys.stderr, flush=True)
    C_full = score_matrix(X)
    C_u = C_full[u0:, :]

    # 2) observed pointer days on the usable range.
    obs = detect_pointer_days(C_u)
    pointer_global = obs.pointer_indices + u0

    # 3) stage 1: circular surrogates (usable range preserves marginals exactly).
    stage1 = stage1_surrogate_p(
        C_u, win_masks_usable, n_surrogates=n_surrogates, seed=seed,
    )

    # 4) stage 2: held-out dvol index + Delta_pre + permutation null per window.
    # z-parameters over the USABLE (non-burn-in) period, applied to the full
    # grid (hardened spec "über den nutzbaren Zeitraum"; DEC-21).
    usable_mask_full = np.arange(t_full) >= u0
    D = dvol_index(dvol_btc, dvol_eth, usable_mask_full)
    dpre = delta_pre(D)
    stage2 = [
        stage2_permutation_p(
            dpre, pointer_global, win_global[w],
            n_draws=n_permutations, seed=seed + 1000 + w,
        )
        for w in range(len(windows))
    ]

    # 4b) Neuwirth window crosscheck — registered as "wird mitberichtet, ist
    # aber nicht-urteilstragend" (hardened_hypotheses.md H-10): same detrend +
    # pointer rule, but a 13-day centred window (Neuwirth et al. 2007) instead
    # of the judgment-bearing 11-day Cropper window. Reported ONLY as a
    # secondary anti-method-shopping diagnostic; enters NO cell, NO p-value,
    # NO FDR (audit_h10 BUG-6).
    C_nw_u = score_matrix(X, half_window=NEUWIRTH_HALF_WINDOW)[u0:, :]
    obs_nw = detect_pointer_days(C_nw_u)
    cropper_ptr_set = set(int(i) for i in obs.pointer_indices)
    neuwirth_windows: list[dict[str, Any]] = []
    for w, (label, w_start, w_end) in enumerate(windows):
        mask = win_masks_usable[w]
        nw_rel = obs_nw.pointer_indices[mask[obs_nw.pointer_indices]]
        nw_dates = [days[u0 + int(i)] for i in nw_rel]
        n_overlap = sum(1 for i in nw_rel if int(i) in cropper_ptr_set)
        neuwirth_windows.append({
            "window_label": label,
            "n_pointer_neuwirth": int(nw_rel.size),
            "pointer_dates_neuwirth": nw_dates,
            "n_overlap_with_cropper": int(n_overlap),
        })

    # 5) 4-cell family + BH-FDR (F-POINTER).
    cells: list[dict[str, Any]] = []
    for w, (label, w_start, w_end) in enumerate(windows):
        mask = win_masks_usable[w]
        ptr_rel = obs.pointer_indices[mask[obs.pointer_indices]]
        ptr_dates = [days[u0 + int(i)] for i in ptr_rel]
        ptr_dirs = [int(obs.direction[int(i)]) for i in ptr_rel]
        n_ptr = len(ptr_dates)
        cells.append({
            "stage": 1,
            "window_label": label,
            "window_start": w_start,
            "window_end": w_end,
            "n_days_in_window": int(mask.sum()),
            "n_pointer": n_ptr,
            "pointer_dates": ptr_dates,
            "pointer_directions": ptr_dirs,
            "n_pointer_floor": N_POINTER_FLOOR,
            "n_pointer_floor_met": bool(n_ptr >= N_POINTER_FLOOR),
            "surrogate_p": float(stage1[w]["surrogate_p"]),
            "surrogate_mean_n_pointer": float(stage1[w]["surrogate_mean"]),
            "surrogate_max_n_pointer": float(stage1[w]["surrogate_max"]),
        })
    for w, (label, w_start, w_end) in enumerate(windows):
        s2 = stage2[w]
        p2 = float(s2["permutation_p_two_sided"])
        cells.append({
            "stage": 2,
            "window_label": label,
            "window_start": w_start,
            "window_end": w_end,
            "n_pointer_in_window": int(s2["n_pointer_in_window"]),
            "n_pointer_used": int(s2["n_pointer_used"]),
            "n_pointer_floor": N_POINTER_FLOOR,
            "n_pointer_floor_met": bool(int(s2["n_pointer_in_window"]) >= N_POINTER_FLOOR),
            "s_mean_delta_pre": _f(s2["s_observed"]),
            "n_eligible_null_days": int(s2["n_eligible_null_days"]),
            "min_null_gap_days": MIN_NULL_GAP_DAYS,
            "permutation_p_two_sided": _f(p2),
            "p_undefined": bool(not np.isfinite(p2)),
        })

    # BH input: undefined p counts as the worst case 1.0 (flagged per cell).
    p_for_bh = []
    for c in cells:
        p = c["surrogate_p"] if c["stage"] == 1 else c["permutation_p_two_sided"]
        p_for_bh.append(float(p) if (p is not None and np.isfinite(p)) else 1.0)
    rejected, p_crit = benjamini_hochberg(p_for_bh, FDR_ALPHA)
    for c, p, rej in zip(cells, p_for_bh, rejected):
        c["p_for_fdr"] = float(p)
        c["fdr_significant"] = bool(rej)
        c["cell_pass"] = bool(rej and p <= SURROGATE_P_MAX and c["n_pointer_floor_met"])

    all_pass = bool(cells) and all(c["cell_pass"] for c in cells)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "data_start": days[0],
        "data_end": days[-1],
        "burn_in_days": int(burn_in_days),
        "usable_start": usable_start,
        "n_days_total": int(t_full),
        "n_days_usable": int(t_usable),
        "windows": [
            {"label": lb, "start": s, "end": e} for lb, s, e in windows
        ],
        "n_detection_series": int(n_series),
        "detection_series": list(detection_names),
        # Per-series coverage so a data-plumbing failure (all-NULL field
        # extraction, missing stream) is auditable post hoc (audit_h10 BUG-3).
        "detection_series_finite_days": {
            name: int(np.isfinite(X[:, j]).sum())
            for j, name in enumerate(detection_names)
        },
        "n_detection_series_nonempty": int(sum(
            1 for j in range(n_series) if np.isfinite(X[:, j]).any()
        )),
        "holdout_target": "deribit dvol BTC+ETH (never in detection)",
        "holdout_finite_days": {
            "dvol_btc": int(np.isfinite(np.asarray(dvol_btc, dtype=np.float64)).sum()),
            "dvol_eth": int(np.isfinite(np.asarray(dvol_eth, dtype=np.float64)).sum()),
            "dvol_btc_usable": int(np.isfinite(
                np.asarray(dvol_btc, dtype=np.float64)[u0:]).sum()),
            "dvol_eth_usable": int(np.isfinite(
                np.asarray(dvol_eth, dtype=np.float64)[u0:]).sum()),
        },
        # Parse mode used by the unknown-generic dvol payload parser
        # (candidate:<field> / fallback:<field> / none) — audit_h10 BUG-4.
        "dvol_parse_mode": dict(dvol_parse_modes) if dvol_parse_modes else None,
        "method": {
            "detrend_window_days": DETREND_WINDOW,
            "detrend_min_periods": DETREND_MIN_PERIODS,
            "cropper_window_days": 2 * CROPPER_HALF_WINDOW + 1,
            "c_thresh": C_THRESH,
            "share_floor": SHARE_FLOOR,
            "n_avail_floor": N_AVAIL_FLOOR,
            "pre_drift_near_days": [5, 1],
            "pre_drift_far_days": [15, 6],
        },
        "n_surrogates": int(n_surrogates),
        "n_permutations": int(n_permutations),
        "seed": int(seed),
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": FDR_FAMILY,
        "fdr_p_crit": _f(p_crit),
        "n_fdr_significant": int(sum(1 for c in cells if c["fdr_significant"])),
        "gate_thresholds": {
            "p_max": SURROGATE_P_MAX,
            "n_pointer_floor": N_POINTER_FLOOR,
            "fdr_alpha": FDR_ALPHA,
            "hard_one_window_drop": True,
            "n_pointer_floor_lowerable": False,
        },
        # Registered NON-judgment-bearing co-report (hardened_hypotheses.md
        # H-10 "Methoden-Fixierung": "der Neuwirth-Fenster-Crosscheck wird
        # mitberichtet, ist aber nicht-urteilstragend"). Enters no cell/FDR.
        "neuwirth_crosscheck": {
            "judgment_bearing": False,
            "window_days": 2 * NEUWIRTH_HALF_WINDOW + 1,
            "note": ("nicht-urteilstragend — schliesst Method-Shopping aus; "
                     "einzige urteilstragende Standardisierung ist der "
                     "11-Tage-Cropper"),
            "windows": neuwirth_windows,
        },
        # Gate-neutral family-level observation (gate-auditor adjudicates):
        "all_four_cells_pass": all_pass,
        "cells": cells,
    }


def _f(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


# ----------------------------------------------------------------------------
# Report (Deutsch)
# ----------------------------------------------------------------------------

def _fmt(v: Any, nd: int = 4) -> str:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}"


def render_markdown(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# C-10 Cross-Stream-Pointer-Days + Pre-Event-Drift — H-10 Mess-Gate (KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}`")
    L.append(f"- **Tagesraster:** {payload['data_start']}..{payload['data_end']} "
             f"({payload['n_days_total']} Tage, Burn-in {payload['burn_in_days']}, "
             f"nutzbar ab {payload['usable_start']})")
    L.append(f"- **Fenster (vorregistriert):** " + ", ".join(
        f"{w['label']}={w['start']}..{w['end']}" for w in payload["windows"]))
    L.append(f"- **Detektions-Serien:** {payload['n_detection_series']} (vorab fixiert) · "
             f"**Hold-out-Ziel:** {payload['holdout_target']}")
    m = payload["method"]
    L.append(f"- **Methodik:** trailing {m['detrend_window_days']}-Tage-Median "
             f"(min_periods={m['detrend_min_periods']}) · Cropper "
             f"{m['cropper_window_days']}-Tage zentriert · |C|>={m['c_thresh']} · "
             f"Anteil>={m['share_floor']} · n_avail>={m['n_avail_floor']} · "
             f"Pre-Drift [t-5,t-1] vs. [t-15,t-6]")
    L.append(f"- **Surrogate/Permutationen:** {payload['n_surrogates']} / "
             f"{payload['n_permutations']} · **Seed:** {payload['seed']}")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} (4 Zellen) · "
             f"**BH-FDR alpha:** {payload['fdr_alpha']} · "
             f"**p_crit:** {_fmt(payload['fdr_p_crit'])}")
    L.append("- **KAPITALFREI:** ja — reine Mess-/Existenzfrage, keine Kapital-Metriken.")
    L.append("")
    L.append("> Gate-Urteil faellt der gate-auditor gegen H-10. WEITER verlangt nach BH-FDR "
             "alpha=0.10 ueber F-POINTER ALLE 4 Zellen: Stufe-1-p<=0.05 in W1 UND W2, "
             "N_pointer>=3 je Fenster (Floor NICHT absenkbar), Stufe-2-p<=0.05 (zweiseitig) "
             "in W1 UND W2. Hartes Ein-Fenster-DROP, kein GRAUBEREICH.")
    L.append("")
    L.append("## F-POINTER-Zellen (Gate-Kern)")
    L.append("")
    L.append("| Stufe | Fenster | N_pointer | Statistik | p | FDR-sig | N-Floor (>=3) | Zelle besteht |")
    L.append("|---:|---|---:|---:|---:|:---:|:---:|:---:|")
    for c in payload["cells"]:
        if c["stage"] == 1:
            stat = f"N_obs={c['n_pointer']} (Surr-Mittel {_fmt(c['surrogate_mean_n_pointer'], 2)})"
            p = c["surrogate_p"]
            n_ptr = c["n_pointer"]
        else:
            stat = f"S={_fmt(c['s_mean_delta_pre'])} (Null-Pool {c['n_eligible_null_days']})"
            p = c["permutation_p_two_sided"]
            n_ptr = c["n_pointer_in_window"]
        L.append(f"| {c['stage']} | {c['window_label']} | {n_ptr} | {stat} | {_fmt(p)} | "
                 f"{'ja' if c['fdr_significant'] else 'nein'} | "
                 f"{'ja' if c['n_pointer_floor_met'] else 'NEIN'} | "
                 f"{'JA' if c['cell_pass'] else 'nein'} |")
    L.append("")
    L.append(f"**all_four_cells_pass (gate-neutral):** "
             f"{'JA' if payload['all_four_cells_pass'] else 'nein'}")
    L.append("")
    L.append("## Pointer-Tage")
    L.append("")
    for c in payload["cells"]:
        if c["stage"] != 1:
            continue
        if c["pointer_dates"]:
            pts = ", ".join(f"{d} ({'+' if s > 0 else '-'})"
                            for d, s in zip(c["pointer_dates"], c["pointer_directions"]))
        else:
            pts = "keine"
        L.append(f"- **{c['window_label']}** ({c['window_start']}..{c['window_end']}): {pts}")
    L.append("")
    nw = payload.get("neuwirth_crosscheck")
    if nw:
        L.append("## Neuwirth-Fenster-Crosscheck (mitberichtet, NICHT-urteilstragend)")
        L.append("")
        L.append(f"> {nw['window_days']}-Tage-Fenster (Neuwirth et al. 2007), gleiche Detrend-/"
                 "Pointer-Regel. Reines Anti-Method-Shopping-Diagnostikum — geht in KEINE "
                 "Zelle, KEIN p, KEINE FDR ein (Registry H-10).")
        L.append("")
        for w in nw["windows"]:
            dts = ", ".join(w["pointer_dates_neuwirth"]) or "keine"
            L.append(f"- **{w['window_label']}**: N_pointer(Neuwirth)={w['n_pointer_neuwirth']} "
                     f"(Ueberlapp mit Cropper: {w['n_overlap_with_cropper']}): {dts}")
        L.append("")
    hf = payload.get("holdout_finite_days")
    if hf:
        L.append("## Abdeckung (Coverage-Audit)")
        L.append("")
        L.append(f"- **Hold-out dvol:** BTC {hf['dvol_btc']} Tage "
                 f"(nutzbar {hf['dvol_btc_usable']}) · ETH {hf['dvol_eth']} Tage "
                 f"(nutzbar {hf['dvol_eth_usable']}) · Parse-Modus: "
                 f"`{payload.get('dvol_parse_mode')}`")
        L.append(f"- **Detektions-Serien nicht-leer:** "
                 f"{payload.get('n_detection_series_nonempty')} von "
                 f"{payload['n_detection_series']} (finite Tage je Serie im JSON: "
                 f"`detection_series_finite_days`)")
        L.append("")
    L.append("*Erzeugt von `c10_pointer/driver.py` (read-only Harvester-Baum). "
             "capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-10.*")
    return "\n".join(L)


__all__ = [
    "DEFAULT_BURN_IN_DAYS",
    "DEFAULT_DATA_END",
    "DEFAULT_DATA_START",
    "DEFAULT_WINDOWS",
    "HYPOTHESIS_ID",
    "REGISTRY_PATH",
    "SCHEMA_VERSION",
    "render_markdown",
    "run",
]
