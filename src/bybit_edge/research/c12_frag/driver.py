"""Orchestration + gate-neutral payload for the H-12 fragmentation mess-gate.

Runs the registered two-window measurement (registry H-12, Welle 4):

  * per window: spectral measurement of every valid day of the 6-series
    cross-exchange minute panel (``spectrum.analyze_day``),
  * per valid day: stage-b one-factor Gaussian null calibrated from the
    observed (lambda1, v1) (``nulls.one_factor_null_day``, t_obs = the day's
    t_eff) -> day p-value P(lambda2_sim >= lambda2_obs),
  * ONE F-FRAG BH-FDR family over ALL day p-values of BOTH windows together
    (``stats.benjamini_hochberg``, alpha = 0.10 — registry: ~70-100 tests),
  * afterwards per window the registered gate criteria:
      (a) share of valid days with FDR-significant lambda2 >= 20%,
      (b) median IPR(v2) over the FDR-significant days >= 0.40,
      (c) on >= 70% of the FDR-significant days the largest v2^2 exchange
          load falls on the SAME exchange,
  * validity PRE-condition (checked BEFORE the gate, NOT a gate criterion):
    IPR(v1) <= 0.25 on >= 90% of the valid days AND >= 35 valid days per
    window — otherwise the run is INVALID: own ``validity_status`` in the
    payload, NO verdict, explicitly NOT a DROP,
  * stage-a MC-Wishart reference ONCE per window (NOT verdict-bearing,
    orientation only — ``nulls.wishart_null_mc``).

GATE-NEUTRAL payload (H-04b/H-05c/H-08 convention): every criterion is
reported individually per window plus a ``weiter_indication`` flag — the
driver renders NO overall verdict; the gate-auditor adjudicates against the
H-12 registry entry.

KAPITALFREI: pure spectral measurement, ``capital_free: true``; no friction,
bps, PnL, Sharpe field anywhere.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

import numpy as np

from .nulls import DEFAULT_N_MC, empirical_p_ge, one_factor_null_day, wishart_null_mc
from .panel import WindowDays
from .spectrum import analyze_day
from .stats import FDR_ALPHA, benjamini_hochberg

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-12"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-FRAG"

#: Pre-registered calendar windows (registry H-12, verbatim; identical H-09).
DEFAULT_WINDOW_A = ("2026-03-27", "2026-05-15")
DEFAULT_WINDOW_B = ("2026-05-16", "2026-07-04")

#: The gate is defined over BOTH pre-registered windows.
MIN_WINDOWS = 2

#: Registered gate thresholds (registry H-12, verbatim):
SIG_DAY_SHARE_MIN = 0.20            # (a) FDR-sig day share >= 20%
IPR_V2_MEDIAN_MIN = 0.40            # (b) median IPR(v2) over FDR-sig days
DOMINANT_EXCHANGE_SHARE_MIN = 0.70  # (c) same dominant exchange on >= 70%

#: Registered validity precondition (NOT part of the gate):
IPR_V1_MAX = 0.25
IPR_V1_SHARE_MIN = 0.90
MIN_VALID_DAYS_PER_WINDOW = 35

VALIDITY_NOTE = (
    "Validitaets-Vorbedingung (VOR dem Gate, KEIN Gate-Bestandteil): "
    "IPR(v1) <= 0,25 an >= 90% der gueltigen Tage UND >= 35 gueltige Tage "
    "je Fenster. Verfehlt -> Lauf UNGUELTIG: eigener Status, KEIN Verdikt, "
    "explizit NICHT DROP (Registry H-12)."
)


def run(
    windows: list[WindowDays],
    *,
    n_mc: int = DEFAULT_N_MC,
    seed: int = 42,
    source: str = "",
) -> dict[str, Any]:
    """Run the H-12 mess-gate over the >= 2 pre-registered window panels.

    ``windows[w]`` is the synchronised day-panel window (``panel.build_window``
    output) for pre-registered window w. Returns the gate-neutral payload:
    per-day measurements, ONE F-FRAG BH-FDR family over both windows, the
    per-window criteria (a)/(b)/(c), the validity precondition status and the
    ``weiter_indication`` flag. The gate-auditor adjudicates.
    """
    if len(windows) < MIN_WINDOWS:
        raise ValueError(
            f"{HYPOTHESIS_ID} needs >= {MIN_WINDOWS} windows, got {len(windows)}"
        )

    # 1) per-day spectra + stage-b one-factor null p-values (both windows).
    window_records: list[dict[str, Any]] = []
    family_days: list[dict[str, Any]] = []  # analyzed days in family order
    for wi, win in enumerate(windows):
        day_records: list[dict[str, Any]] = []
        for di, day in enumerate(win.days):
            rec: dict[str, Any] = {
                "date": day.date,
                "panel_valid": bool(day.valid),
                "analyzed": False,
                "degenerate": False,
            }
            if day.valid:
                spec = analyze_day(day.minute_prices, win.series_exchanges)
                if spec is None:
                    # technical degeneracy guard (zero variance / near-empty
                    # day) — expected 0 on real registered-valid days.
                    rec["degenerate"] = True
                else:
                    lambda2_sims, ipr2_sims = one_factor_null_day(
                        float(spec.lams[0]), spec.v1, spec.t_eff,
                        n_reps=n_mc, seed=(int(seed), wi, di),
                    )
                    p_l2 = empirical_p_ge(lambda2_sims, float(spec.lams[1]))
                    p_ipr2 = empirical_p_ge(ipr2_sims, float(spec.ipr_v2))
                    rec.update({
                        "analyzed": True,
                        "t_eff": int(spec.t_eff),
                        "lambda1": float(spec.lams[0]),
                        "lambda2": float(spec.lams[1]),
                        "ipr_v1": float(spec.ipr_v1),
                        "ipr_v2": float(spec.ipr_v2),
                        "exchange_loads_v2": {
                            k: float(v) for k, v in spec.exchange_loads_v2.items()
                        },
                        "dominant_exchange_v2": str(spec.dominant_exchange_v2),
                        # verdict-bearing day p (registry stage b):
                        "p_lambda2_one_factor": float(p_l2),
                        # reported alongside, NOT verdict-bearing:
                        "p_ipr_v2_one_factor": float(p_ipr2),
                    })
                    family_days.append(rec)
            day_records.append(rec)
        n_analyzed = sum(1 for d in day_records if d["analyzed"])
        print(
            f"[h12] window {win.label}: {n_analyzed}/{len(win.days)} days "
            f"valid+analyzed (n_mc={n_mc})",
            file=sys.stderr, flush=True,
        )
        window_records.append({
            "window_index": wi,
            "window_label": win.label,
            "start_date": win.start_date,
            "end_date": win.end_date,
            "series_labels": list(win.series_labels),
            "series_exchanges": list(win.series_exchanges),
            "n_days_total": len(win.days),
            "n_days_panel_valid": sum(1 for d in day_records if d["panel_valid"]),
            "n_days_degenerate": sum(1 for d in day_records if d["degenerate"]),
            "n_days_valid": n_analyzed,
            "days": day_records,
        })

    # 2) ONE F-FRAG BH-FDR family over ALL day p-values of BOTH windows.
    p_values = [d["p_lambda2_one_factor"] for d in family_days]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for d, rej in zip(family_days, rejected):
        d["fdr_significant"] = bool(rej)

    # 3) per-window: validity precondition + gate criteria (a)/(b)/(c) +
    #    stage-a MC-Wishart reference (NOT verdict-bearing).
    for wi, (win, wrec) in enumerate(zip(windows, window_records)):
        analyzed = [d for d in wrec["days"] if d["analyzed"]]
        n_valid = len(analyzed)
        sig = [d for d in analyzed if d["fdr_significant"]]
        n_sig = len(sig)

        # validity precondition (BEFORE the gate, not a gate criterion):
        n_ipr1_ok = sum(1 for d in analyzed if d["ipr_v1"] <= IPR_V1_MAX)
        ipr_v1_ok_share = (n_ipr1_ok / n_valid) if n_valid else float("nan")
        ipr_v1_share_ok = bool(n_valid > 0 and ipr_v1_ok_share >= IPR_V1_SHARE_MIN)
        min_days_ok = bool(n_valid >= MIN_VALID_DAYS_PER_WINDOW)
        window_valid = bool(ipr_v1_share_ok and min_days_ok)

        # (a) FDR-sig day share:
        sig_day_share = (n_sig / n_valid) if n_valid else float("nan")
        crit_a_met = bool(n_valid > 0 and sig_day_share >= SIG_DAY_SHARE_MIN)
        # (b) median IPR(v2) over the FDR-sig days:
        median_ipr_v2_sig = (
            float(np.median([d["ipr_v2"] for d in sig])) if sig else float("nan")
        )
        crit_b_met = bool(sig and median_ipr_v2_sig >= IPR_V2_MEDIAN_MIN)
        # (c) same dominant exchange on >= 70% of the FDR-sig days
        # (ties in the day count break alphabetically — deterministic):
        if sig:
            counts: dict[str, int] = {}
            for d in sig:
                ex = d["dominant_exchange_v2"]
                counts[ex] = counts.get(ex, 0) + 1
            dominant_exchange, dom_n = sorted(
                counts.items(), key=lambda kv: (-kv[1], kv[0])
            )[0]
            dominant_exchange_share = dom_n / n_sig
        else:
            dominant_exchange = None
            dominant_exchange_share = float("nan")
        crit_c_met = bool(
            sig and dominant_exchange_share >= DOMINANT_EXCHANGE_SHARE_MIN
        )

        # stage-a MC-Wishart reference, ONCE per window (orientation only):
        if analyzed:
            t_med = int(np.median([d["t_eff"] for d in analyzed]))
            wishart_ref = wishart_null_mc(
                len(win.series_labels), t_med, n_draws=n_mc, seed=seed + 1000 + wi
            )
        else:
            wishart_ref = None

        wrec.update({
            "n_days_fdr_significant": n_sig,
            "validity": {
                "ipr_v1_max": IPR_V1_MAX,
                "ipr_v1_ok_share": ipr_v1_ok_share,
                "ipr_v1_share_min": IPR_V1_SHARE_MIN,
                "ipr_v1_share_ok": ipr_v1_share_ok,
                "n_days_valid": n_valid,
                "min_valid_days": MIN_VALID_DAYS_PER_WINDOW,
                "min_days_ok": min_days_ok,
                "window_valid": window_valid,
            },
            "criteria": {
                "a_sig_day_share": sig_day_share,
                "a_threshold": SIG_DAY_SHARE_MIN,
                "a_met": crit_a_met,
                "b_median_ipr_v2_sig": median_ipr_v2_sig,
                "b_threshold": IPR_V2_MEDIAN_MIN,
                "b_met": crit_b_met,
                "c_dominant_exchange": dominant_exchange,
                "c_dominant_exchange_share": dominant_exchange_share,
                "c_threshold": DOMINANT_EXCHANGE_SHARE_MIN,
                "c_met": crit_c_met,
            },
            "all_criteria_met": bool(crit_a_met and crit_b_met and crit_c_met),
            "wishart_reference": wishart_ref,
        })

    # 4) run-level rollup (gate-neutral — the gate-auditor adjudicates).
    all_windows_valid = all(w["validity"]["window_valid"] for w in window_records)
    all_criteria_met_all_windows = all(w["all_criteria_met"] for w in window_records)
    validity_status = "gueltig" if all_windows_valid else "ungueltig"
    weiter_indication = bool(all_windows_valid and all_criteria_met_all_windows)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "window_labels": [w.label for w in windows],
        "n_windows": len(windows),
        "n_mc": int(n_mc),
        "seed": int(seed),
        "method": {
            "panel": "6 Serien = 2 Symbole x 3 Boersen, Minuten-Last-Price, "
                     "Forward-Fill <= 1 min, Tag gueltig >= 1380/1440 min je Serie",
            "spectrum": "Log-Returns je Serie je Tag z-standardisiert, "
                        "Korrelationsmatrix C (6x6), Eigenzerlegung, "
                        "IPR(v) = Summe(v_i^4)",
            "null_stage_a": "MC-Gaussian-Wishart-Referenz (NICHT urteilstragend)",
            "null_stage_b": "Ein-Faktor-Gauss-Null je Tag aus (lambda1, v1), "
                            "Tages-p = P(lambda2_sim >= lambda2_obs), "
                            "Add-one-Konvention",
        },
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": FDR_FAMILY,
        "fdr_family_size": len(p_values),
        "fdr_p_crit": float(p_crit),
        "n_fdr_significant": sum(1 for d in family_days if d["fdr_significant"]),
        "gate_thresholds": {
            "a_sig_day_share_min": SIG_DAY_SHARE_MIN,
            "b_ipr_v2_median_min": IPR_V2_MEDIAN_MIN,
            "c_dominant_exchange_share_min": DOMINANT_EXCHANGE_SHARE_MIN,
            "min_windows": MIN_WINDOWS,
        },
        "validity_precondition": {
            "ipr_v1_max": IPR_V1_MAX,
            "ipr_v1_share_min": IPR_V1_SHARE_MIN,
            "min_valid_days_per_window": MIN_VALID_DAYS_PER_WINDOW,
            "note": VALIDITY_NOTE,
        },
        "validity_status": validity_status,
        "all_windows_valid": all_windows_valid,
        # Gate-neutral observation flags (the gate-auditor adjudicates):
        "all_criteria_met_all_windows": all_criteria_met_all_windows,
        "weiter_indication": weiter_indication,
        "windows": window_records,
    }


# ----------------------------------------------------------------------------
# Report (Deutsch)
# ----------------------------------------------------------------------------

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
    """German Markdown report — criteria per window + day overview (H-12)."""
    L: list[str] = []
    L.append("# H-12 · Cross-Exchange-Fragmentierungsmatrix Mess-Gate "
             "(RMT/MP-IPR, F-FRAG, KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — "
             f"`{payload['hypothesis_registry']}` (Welle 4)")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}`")
    L.append(f"- **Fenster (vorregistriert):** {', '.join(payload['window_labels'])}")
    m = payload["method"]
    L.append(f"- **Panel:** {m['panel']}")
    L.append(f"- **Spektrum:** {m['spectrum']}")
    L.append(f"- **Null (zweistufig):** (a) {m['null_stage_a']} · "
             f"(b) {m['null_stage_b']} · MC-Ziehungen/Reps: {payload['n_mc']} · "
             f"Seed: {payload['seed']}")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} (EINE Familie ueber "
             f"BEIDE Fenster, {payload['fdr_family_size']} Tages-Tests) · "
             f"BH-FDR alpha {payload['fdr_alpha']} · "
             f"p_crit {_fmt(payload['fdr_p_crit'])} · "
             f"FDR-signifikant: {payload['n_fdr_significant']}")
    L.append("- **KAPITALFREI:** ja — reine Mess-/Explorationsfrage. "
             "Cross-Exchange-Arbitragesignal waere NEUE H-12b, NICHT impliziert.")
    L.append(f"- **Validitaets-Vorbedingung:** {payload['validity_precondition']['note']}")
    L.append(f"- **Validitaets-Status dieses Laufs:** "
             f"**{payload['validity_status'].upper()}**")
    L.append("")
    L.append("> Gate-Urteil faellt der gate-auditor gegen H-12. WEITER verlangt "
             "in BEIDEN Fenstern: (a) Anteil gueltiger Tage mit lambda2 nach "
             "BH-FDR alpha=0,10 ueber F-FRAG signifikant ueber der "
             "Ein-Faktor-Null >= 20% UND (b) Median-IPR(v2) ueber den "
             "FDR-signifikanten Tagen >= 0,40 UND (c) an >= 70% der "
             "FDR-signifikanten Tage groesste v2^2-Boersenlast auf derselben "
             "Boerse. DROP: (a), (b) ODER (c) in einem Fenster verfehlt "
             "(hartes Ein-Fenster-Kriterium), kein Graubereich. "
             "Validitaets-Vorbedingung verfehlt -> Lauf UNGUELTIG (kein "
             "Verdikt, NICHT DROP). A-priori: DROP.")
    L.append("")
    L.append(f"**WEITER-Indikation (nur bei gueltigem Lauf):** "
             f"{_fmt(payload['weiter_indication'])} · "
             f"**alle Fenster gueltig:** {_fmt(payload['all_windows_valid'])} · "
             f"**alle Kriterien in allen Fenstern:** "
             f"{_fmt(payload['all_criteria_met_all_windows'])}")
    L.append("")
    L.append("## Kriterien je Fenster (Gate-Kern)")
    L.append("")
    L.append("| Fenster | gueltige Tage | FDR-sig Tage | (a) Anteil >= 0,20 "
             "| (b) Median-IPR(v2) >= 0,40 | (c) dominante Boerse (Anteil >= 0,70) "
             "| a | b | c | alle |")
    L.append("|---|---:|---:|---:|---:|---|:---:|:---:|:---:|:---:|")
    for w in payload["windows"]:
        c = w["criteria"]
        dom = c["c_dominant_exchange"] if c["c_dominant_exchange"] else "n/a"
        L.append(
            f"| {w['window_label']} | {w['n_days_valid']} "
            f"| {w['n_days_fdr_significant']} | {_fmt(c['a_sig_day_share'])} "
            f"| {_fmt(c['b_median_ipr_v2_sig'])} "
            f"| {dom} ({_fmt(c['c_dominant_exchange_share'])}) "
            f"| {_fmt(c['a_met'])} | {_fmt(c['b_met'])} | {_fmt(c['c_met'])} "
            f"| {_fmt(w['all_criteria_met'])} |"
        )
    L.append("")
    L.append("## Validitaets-Vorbedingung je Fenster (kein Gate-Bestandteil)")
    L.append("")
    L.append("| Fenster | gueltige Tage (>= 35) | IPR(v1)<=0,25-Anteil (>= 0,90) "
             "| Fenster gueltig |")
    L.append("|---|---:|---:|:---:|")
    for w in payload["windows"]:
        v = w["validity"]
        L.append(
            f"| {w['window_label']} | {v['n_days_valid']} "
            f"({_fmt(v['min_days_ok'])}) | {_fmt(v['ipr_v1_ok_share'])} "
            f"({_fmt(v['ipr_v1_share_ok'])}) | {_fmt(v['window_valid'])} |"
        )
    L.append("")
    L.append("## MC-Wishart-Referenz je Fenster (Stufe a — NICHT urteilstragend)")
    L.append("")
    L.append("| Fenster | T_eff (Median) | Q | MP lambda+ | lambda1 q95 | "
             "lambda2 q95 | lambda2 q99 |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for w in payload["windows"]:
        r = w["wishart_reference"]
        if r is None:
            L.append(f"| {w['window_label']} | n/a | n/a | n/a | n/a | n/a | n/a |")
        else:
            L.append(
                f"| {w['window_label']} | {r['t_obs']} | {_fmt(r['q_aspect'], 1)} "
                f"| {_fmt(r['mp_lambda_plus'])} "
                f"| {_fmt(r['lambda1_null_quantiles']['q95'])} "
                f"| {_fmt(r['lambda2_null_quantiles']['q95'])} "
                f"| {_fmt(r['lambda2_null_quantiles']['q99'])} |"
            )
    L.append("")
    for w in payload["windows"]:
        L.append(f"## Tagesuebersicht {w['window_label']}")
        L.append("")
        L.append("| Datum | gueltig | T_eff | lambda1 | lambda2 | IPR(v1) | "
                 "IPR(v2) | p(lambda2) | FDR-sig | dominante Boerse (v2^2) |")
        L.append("|---|:---:|---:|---:|---:|---:|---:|---:|:---:|---|")
        for d in w["days"]:
            if not d["analyzed"]:
                why = "degeneriert" if d["degenerate"] else "Panel-Luecke"
                L.append(f"| {d['date']} | nein ({why}) | — | — | — | — | — "
                         f"| — | — | — |")
                continue
            L.append(
                f"| {d['date']} | ja | {d['t_eff']} | {_fmt(d['lambda1'])} "
                f"| {_fmt(d['lambda2'])} | {_fmt(d['ipr_v1'])} "
                f"| {_fmt(d['ipr_v2'])} | {_fmt(d['p_lambda2_one_factor'])} "
                f"| {_fmt(d['fdr_significant'])} | {d['dominant_exchange_v2']} |"
            )
        L.append("")
    L.append("*Erzeugt von `scripts/c12_frag.py` (Welle 4, read-only "
             "Harvester-Backfill). capital_free=true. Endgueltiges Gate-Urteil: "
             "gate-auditor gegen H-12.*")
    L.append("")
    return "\n".join(L)


__all__ = [
    "DEFAULT_WINDOW_A",
    "DEFAULT_WINDOW_B",
    "DOMINANT_EXCHANGE_SHARE_MIN",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "IPR_V1_MAX",
    "IPR_V1_SHARE_MIN",
    "IPR_V2_MEDIAN_MIN",
    "MIN_VALID_DAYS_PER_WINDOW",
    "MIN_WINDOWS",
    "REGISTRY_PATH",
    "SCHEMA_VERSION",
    "SIG_DAY_SHARE_MIN",
    "render_markdown",
    "run",
]
