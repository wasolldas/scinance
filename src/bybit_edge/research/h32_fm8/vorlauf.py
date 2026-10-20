"""Vorlauf v6 (``--prelaunch``): outcome-free, hard panel cut, frozen constants per window and variant (B-1, ERSTFASSUNG
1.2, 1.3, 1.6, 12.1) and the emitter of the registration skeleton ``state/registered/h32_v1.yaml`` (ERSTFASSUNG 11).

**Outcome-free.**  ``ic.weekly_ic_series`` is called here only with SIMULATED returns (``nullsim``) -- never with the real
returns matrix.  The characteristics and the 8-week betas of the real panel are built (formation), the real outcome is
never set against them; the pilot period is calibrated for dispersion / autocorrelation / factor share only (no mean).

Order (all of it on the CUT panel): weekly arrays -> windows P / W1 / W2 (w_judged pins, K minimum) -> K_fm8 series
(from ``returns_valid``) -> calibration per window (W2 anew on the cut window, W1 as determinism control against the
v5e reference, P stress only) -> null with 8 lead weeks (K = 4, driftfree and drift 0.002, ``rules.n_reps``) -> frozen
constants -> survivorship label, stress coverage with date filter -> report.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import yaml

from ..wp13_xsec import nulls
from . import artifacts
from . import calibration as cal
from . import constants as C
from . import nullsim, panel_cut, schema
from . import weekly as wkl
from .errors import H32Abort, PinError

__all__ = ["assemble_prelaunch", "stress_coverage_filtered", "build_template", "render_prelaunch_markdown",
           "write_prelaunch_artifacts", "w1_determinism_control", "template_yaml_text"]


def stress_coverage_filtered(path: Path | str, start: str, end: str, cut_date: str) -> dict[str, Any]:
    """Stress-list coverage (STRESS_REL / STRESS_ABS, DEC-55/56) with the DATE FILTER of DEC-96 E3: entries after
    ``cut_date`` are dropped right after parsing and never counted or printed.  ``{"available": False}`` if the file is
    missing."""
    artifacts.refuse_unsafe_path(path)
    p = Path(path)
    if not p.is_file():
        return {"available": False, "note": f"{p.name} nicht vorhanden"}
    payload = json.loads(p.read_text(encoding="utf-8"))
    days = payload if isinstance(payload, list) else payload.get("days", [])
    if not all(isinstance(d, str) for d in days):
        raise ValueError(f"{p.name}: the day list holds non-string entries")
    kept = [d for d in days if d <= cut_date]                    # DEC-96 E3: nothing after the cut survives this line
    end_eff = min(end, cut_date)
    in_window = sorted(d for d in kept if start <= d <= end_eff)
    return {"available": True, "date_filter": cut_date, "n_days_to_cut": len(kept), "n_days_in_window": len(in_window),
            "days_in_window": in_window}


def w1_determinism_control(report_w1: dict[str, Any], reference: dict[str, Any], *, rel_tol: float = 1e-6) -> dict[str, Any]:
    """W1 is not affected by the cut: recomputed on the cut panel it must hit the v5e reference
    (``windows.W1.null_scales`` / ``calibration`` of the reference YAML).  Returns the comparison; ``ok`` False on any
    deviation beyond ``rel_tol`` (``beta_sd_calibrated``: 1e-3, a bisection result)."""
    w = (reference.get("windows") or {}).get("W1") or {}
    rows: dict[str, Any] = {}
    ok = True

    def cmp(name: str, new: float, old: Any, tol: float) -> None:
        nonlocal ok
        if old is None:
            rows[name] = {"new": new, "reference": None, "ok": False}
            ok = False
            return
        good = abs(new - float(old)) <= tol * max(abs(float(old)), 1e-12)
        rows[name] = {"new": new, "reference": float(old), "ok": bool(good)}
        ok = ok and good

    sc = w.get("null_scales") or {}
    cmp("sigma_f", report_w1["sigma_f"], sc.get("sigma_f"), rel_tol)
    cmp("sigma_e_used", report_w1["sigma_e_used"], sc.get("sigma_e_used"), rel_tol)
    for name, blk in (report_w1.get("calibration") or {}).items():
        ref = (w.get("calibration") or {}).get(name) or {}
        cmp(f"{name}.rho_f", blk["rho_f"], ref.get("rho_f"), rel_tol)
        cmp(f"{name}.target_factor_share", blk["target_factor_share"], ref.get("target_factor_share"), rel_tol)
        cmp(f"{name}.beta_sd_calibrated", blk["beta_sd_calibrated"], ref.get("beta_sd_calibrated"), 1e-3)
    return {"ok": ok, "rows": rows, "rel_tol": rel_tol}


def assemble_prelaunch(
    panel: dict[str, Any], observed_fingerprints: dict[str, Any] | None, *, cut_date: str = C.CUT_TEST,
    n_reps: int = C.N_REPS_MIN, n_boot: int = C.N_BOOT_MIN, seed: int = C.SEED,
    calibration_kwargs: dict[str, Any] | None = None, stress_rel_path: Path | str | None = None,
    stress_abs_path: Path | str | None = None, v5e_reference: dict[str, Any] | None = None,
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Vorlauf v6 on the UNCUT daily union panel (fingerprints were checked on the files by the caller).  The hard cut at
    ``cut_date`` (<= 2026-06-28, a Sunday) happens here, before anything is calculated, followed by the maximum-date guard.
    Returns the report dict (JSON-serialisable)."""
    say = log or (lambda _m: None)
    ck = dict(calibration_kwargs or {})
    panel, cut_report = panel_cut.cut_panel_days(panel, cut_date, limit=C.CUT_TEST)
    panel_cut.assert_panel_max_date(panel, cut_date)
    say(f"panel cut at {cut_date}: {cut_report['n_days_removed']} days removed")
    wk = wkl.build_weekly(panel, cut_date, with_turnover=False)
    say(f"weekly arrays: {len(wk.weeks)} weeks ({wk.weeks[0]}..{wk.weeks[-1]}), {len(wk.symbols)} symbols")
    beta_prev = nulls.trailing_pit_beta_excluding_current_week(wk.returns_est, wk.symbols, market_symbol=C.MARKET_SYMBOL,
                                                               trail_win=nulls.CALIBRATION_BETA_TRAIL_WEEKS)
    windows_out: dict[str, Any] = {}
    thresholds: dict[str, dict[str, float]] = {}
    for wn in ("P", "W1", "W2"):
        win = wkl.make_window(wk, wn)
        if win.w_judged != C.W_JUDGED[wn]:
            raise PinError(f"window {wn}: w_judged {win.w_judged} differs from the frozen {C.W_JUDGED[wn]} (T5)")
        if wn == "P" and (win.weeks[0] != C.PILOT_FIRST_FORMATION or win.weeks[win.w_judged - 1] != C.PILOT_LAST_FORMATION):
            raise PinError(f"pilot window formation weeks {win.weeks[0]}..{win.weeks[win.w_judged - 1]} differ from the registered "
                           f"{C.PILOT_FIRST_FORMATION}..{C.PILOT_LAST_FORMATION}")
        k_summary = wkl.check_k_min(win, C.K_MIN[wn])
        k8 = wkl.k_fm8_series(win)
        floor, v_fm8 = wkl.floor_and_v(k8)
        say(f"window {wn}: {win.n_weeks} weeks, K {k_summary}, floor_fm8 {floor:.6f}")
        beta_prev_w = beta_prev[win.lo:win.hi]
        names = ("stress",) if wn == "P" else cal.CAL_NAMES
        c_rep = cal.calibrate_window(win, beta_prev_w, names=names, seed=seed, **ck)
        if wn == "P":
            cal.assert_no_mean_keys(c_rep)                       # Waechter "kein Mittel" (Review B-8)
        stress = c_rep["calibration"]["stress"]
        say(f"window {wn}: calibration done (stress rho_f {stress['rho_f']:.4f}, beta_sd {stress['beta_sd_calibrated']:.4f})")
        nul = nullsim.window_null_constants(
            win, rho_f=stress["rho_f"], beta_sd=stress["beta_sd_calibrated"], sigma_f=c_rep["null_scales"]["sigma_f"],
            sigma_e=c_rep["null_scales"]["sigma_e_used"], n_reps=n_reps, seed=seed, floor_fm8=None if wn == "P" else floor,
            n_boot=n_boot, mean_block=C.MEAN_BLOCK, boot_seed=seed)
        entry: dict[str, Any] = {
            "geometry": wkl.window_geometry_report(win), "k": k_summary, "k_fm8_series": [int(x) for x in k8],
            "k_fm8_series_sha256": wkl.int_series_sha256(k8), "floor_fm8": floor, "v_fm8": v_fm8,
            "calibration_report": c_rep, "null": nul,
        }
        if wn == "P":
            entry["m_P"] = dict(nul["frozen"]["null_mean"])
            entry["null"] = {"cells": {k: {kk: vv for kk, vv in cell.items()} for k, cell in nul["cells"].items()},
                             "frozen": {"null_mean": nul["frozen"]["null_mean"],
                                        "null_mean_driftfree": nul["frozen"]["null_mean_driftfree"],
                                        "null_mean_drifting": nul["frozen"]["null_mean_drifting"]}}
        else:
            fz = dict(nul["frozen"])
            fz.update({"floor_fm8": floor, "v_fm8": v_fm8, "k_fm8_series_sha256": entry["k_fm8_series_sha256"]})
            entry["frozen_v6"] = fz
            thr = {v: C.Z_KRIT * fz["e_se_rule"][v] + max(0.0, fz["null_mean"][v]) for v in C.VARIANTS}
            thresholds[wn] = thr
            entry["bounce_sigma_true"] = c_rep["bounce_sigma_true"]
            entry["survivorship"] = cal.survivorship_report(win, thr["mom1"], thr["rev_gap"], seed=seed)
            if stress_rel_path is not None:
                entry["stress_rel"] = stress_coverage_filtered(stress_rel_path, win.start, win.end, cut_date)
            if stress_abs_path is not None:
                entry["stress_abs"] = stress_coverage_filtered(stress_abs_path, win.start, win.end, cut_date)
        windows_out[wn] = entry
        say(f"window {wn}: null done")
    control = None
    if v5e_reference is not None:
        control = w1_determinism_control(windows_out["W1"]["calibration_report"], v5e_reference)
        if not control["ok"]:
            raise H32Abort("W1 determinism control failed: the recomputed W1 calibration does not hit the v5e reference "
                           f"({[k for k, r in control['rows'].items() if not r['ok']]}) -- the v6 constants are not registrable")
    core = {
        "schema": C.PRELAUNCH_SCHEMA, "mode": "prelaunch",
        "label": ("Vorlauf v6 (DEC-99, ERSTFASSUNG 12.1): outcome-frei -- kein realer Charakteristik-gegen-Outcome-IC; "
                  "Panel vor jeder Rechnung auf das Stichtagsdatum geschnitten; Pilotperiode nur Streuung/Autokorrelation/"
                  "Faktoranteil (kein Mittel)."),
        "cut": {"cut_date": cut_date, **cut_report, "last_week": wk.weeks[-1], "n_weeks": len(wk.weeks),
                "n_symbols": len(wk.symbols)},
        "data_fingerprints": observed_fingerprints,
        "parameters": {"n_reps": int(n_reps), "n_boot": int(n_boot), "seed": int(seed), "mean_block": C.MEAN_BLOCK,
                       "null_level": C.NULL_LEVEL, "lead_weeks": C.LEAD_WEEKS, "calibration": ck},
        "windows": windows_out, "w1_determinism_control": control,
    }
    core["result_sha256"] = artifacts.canonical_sha256(core)
    return core


def build_template(report: dict[str, Any], *, bounce_spread: float) -> dict[str, Any]:
    """Skeleton of ``state/registered/h32_v1.yaml`` (ERSTFASSUNG 11) from a Vorlauf v6 report.  The orchestrator reviews
    and registers it; nothing is registered here."""
    wins = report["windows"]
    p = wins["P"]
    fps = report.get("data_fingerprints") or {}
    prm = report["parameters"]

    def window_block(wn: str) -> dict[str, Any]:
        w = wins[wn]
        fz = w["frozen_v6"]
        keep = (*schema.FROZEN_VARIANT_KEYS, "ceiling_k4", "floor_fm8", "v_fm8", "k_fm8_series_sha256")
        cr = w["calibration_report"]
        return {
            "start": C.WINDOWS[wn][0], "end": C.WINDOWS[wn][1], "w_judged": C.W_JUDGED[wn],
            "calibration": {name: {k: blk[k] for k in ("rho_f", "beta_sd_calibrated", "target_factor_share")}
                            for name, blk in cr["calibration"].items()},
            "null_scales": dict(cr["null_scales"]),
            "frozen_v6": {k: fz[k] for k in keep},
            "bounce_sigma_true": w["bounce_sigma_true"],
            "survivorship": {"mom1_diff_in_ic_min_units": w["survivorship"]["mom1_diff_in_ic_min_units"],
                             "rev_gap_diff_in_ic_min_units": w["survivorship"]["rev_gap_diff_in_ic_min_units"],
                             "unit": "Schwelle T_W,v = z_krit * e_se_rule + max(0, null_mean) (frozen_v6)"},
        }

    p_cal = p["calibration_report"]
    tpl: dict[str, Any] = {
        "hypotheses": {C.ENTRY[v]: {"hypothesis": C.HYPOTHESIS, "variant": v, "direction": C.DIRECTION[v]} for v in C.VARIANTS},
        "primary_statistic": C.PRIMARY_STATISTIC,
        "alpha": C.ALPHA,
        "z_krit": round(C.Z_KRIT, C.Z_KRIT_YAML_DIGITS),
        "mde_faktor": C.MDE_FAKTOR,
        "seal": {"panel_cut_test": C.CUT_TEST, "panel_cut_pilot": C.CUT_PILOT, "stress_list_date_filter": True},
        "fdr": {
            "p_statistic": "block_permutation_fm8_window_mean", "sided": "one", "combine": "max_p",
            "block_len": C.PERM_BLOCK, "n_perm": C.N_PERM, "seed": C.SEED,
            "family": {"name": "F-H32", "method": "BH", "alpha": C.BH_ALPHA, "denominator": C.BH_DENOMINATOR, "report_only": True},
            "over_family": {"name": "F-WEEK", "method": "BY", "alpha": C.BY_ALPHA, "binding": True,
                            "m_rule": "DEC-99 (7): nur getestete Eintraege", "double_statement_m": C.FWEEK_DOUBLE_M},
        },
        "selection": {"K": C.K_FAMILY, "ceiling": "ceiling_k4"},
        "fweek_counting": {"rule": "DEC-99 (7): nur Eintraege mit tatsaechlich berechnetem p-Wert zaehlen in m; GL-012 (Pilot) / nicht "
                                   "uebergeben (p = 1) zaehlen nicht", "in_m": "tested_only", "method": "BY", "alpha": C.BY_ALPHA,
                           "double_statement_m": C.FWEEK_DOUBLE_M, "double_statement_rule": "alte Zaehlung: m inkl. p = 1-Eintraege (report-only)"},
        "pilot_window": {
            "start": C.WINDOWS["P"][0], "end": C.CUT_PILOT, "first_formation_week": C.PILOT_FIRST_FORMATION,
            "last_formation_week": C.PILOT_LAST_FORMATION, "last_outcome_day": C.CUT_PILOT, "w_pilot": C.W_PILOT,
            "k_min_rule": C.K_MIN["P"], "role": "pilot_nicht_urteilstragend",
            "single_run": {"required": True, "rerun_requires_dec": True},
            "pilot_result_sha256": None,
            "se_rule": {"floor": True, "sd": True,
                        "stationary_bootstrap": {"mean_block": C.MEAN_BLOCK, "n_rep": prm["n_boot"], "seed": C.SEED}},
            "band": {"level": C.BAND_LEVEL, "form": "normal_zweiseitig", "z": round(C.BAND_Z, 4)},
            "frozen_v6": {
                "m_P": dict(p["m_P"]),
                "calibration": {"stress": {k: p_cal["calibration"]["stress"][k]
                                           for k in ("rho_f", "beta_sd_calibrated", "target_factor_share")},
                                "sigma_f": p_cal["sigma_f"], "sigma_e_used": p_cal["sigma_e_used"],
                                "rho_f_measured": p_cal["rho_f_measured"], "factor_share_median": p_cal["factor_share_median"],
                                "note": "nur Streuung/Autokorrelation/Faktoranteil, kein Mittel (DEC-94 (5) (i))"},
                "k_fm8_series_sha256": p["k_fm8_series_sha256"],
            },
            "report_only": ["bootstrap_percentile_band", "liquidity_buckets_3_10", "ic_without_bucket_1", "mu_sel", "power_at_mu_sel"],
            "not_computed": ["raw_ic", "lag_profile", "beta_calibration_ic"],
        },
        "handover_rule": {
            "version": C.HANDOVER_VERSION,
            "conditions": [{"id": "i", "text": "x_P > 0 in registrierter Richtung"},
                           {"id": "ii", "text": "x_P - m* >= max_W (z_krit * SE_T,W + 0.8416 * SD_T,W)"},
                           {"id": "iii", "text": "t_P >= t_min"}],
            "t_min": C.T_MIN, "prior_reading": "point",
            "se_T": "max(e_se_rule_W (v6), SE_W,Pilot)", "sd_T": "max(se_mean_W (v6), SE_W,Pilot)",
            "pilot_k_adjusted": "SE_W,Pilot = sqrt(max(1, c_real)) * sqrt(v_fm8_W + F2_real) / sqrt(w_judged_W)",
            "null_mean_credit": "m* = max(0, m_P, m_W1, m_W2) in Richtung",
            "regime_function": "power_p1.assign_regime",
            "double_statement": ["power_p1.assign_regime_a3_practice", "mu_sel"],
            "mu_sel": "Loesung von P_mu(X >= x_P | X >= c_v) = 0.5, X ~ N(mu, SE_P^2), c_v = MDE80*_v + m*",
            "on_fail": {"status": "gl012_pilot", "p_value": 1.0, "in_f_week_m": False},
            "result_lock": "--pilot-result + --pilot-result-sha256 im Testlauf; Uebergabe bitgleich nachgerechnet",
        },
        "windows": {"W1": window_block("W1"), "W2": window_block("W2")},
        "beta_control": {"method": C.PRIMARY_STATISTIC, "beta_window_weeks": C.BETA_WINDOW_WEEKS},
        "rules": {"seed": C.SEED, "n_reps": prm["n_reps"], "mean_block": C.MEAN_BLOCK, "n_boot": prm["n_boot"],
                  "null_level": C.NULL_LEVEL, "bounce_spread": float(bounce_spread)},
        "positive_control": {
            "seeds": [min(C.PC_SEEDS_JUDGE), max(C.PC_SEEDS_JUDGE)],
            "calibration_seeds_injection": [min(C.PC_SEEDS_INJECT), max(C.PC_SEEDS_INJECT)],
            "calibration_seeds_world": [min(C.PC_SEEDS_SIGMA_G), max(C.PC_SEEDS_SIGMA_G)],
            "world_sd_target": "sqrt(v_fm8_W + max(F2_null_W, F2_real))",
            "inject_target": "realisiert: z_krit * SE_T,W + 0.8416 * SD_T,W im bindenden Fenster",
            "criteria": {"sd_ratio_max": C.PC_SD_RATIO_MAX, "pass_share_min": C.PC_PASS_SHARE_MIN,
                         "neg_pass_max": C.PC_NEG_PASS_MAX, "injection_tolerance": C.PC_INJECT_JUDGE_TOL},
            "report_only": ["prd_sector_world_0375", "joint_c10_share"],
        },
        "data_fingerprints": {"union_range_fingerprint": fps.get("union_range_fingerprint"),
                              "delisting_dates_sha256": fps.get("delisting_dates_sha256")},
    }
    return tpl


def template_yaml_text(template: dict[str, Any], report: dict[str, Any], *, source_sha256: str | None = None) -> str:
    header = [
        "# H-32 (A3-fm8): automatisch aus einem Vorlauf-v6-Artefakt (--prelaunch) erzeugtes Skelett von state/registered/h32_v1.yaml.",
        "# NICHT registriert: der Orchestrator prueft (Zuordnung nach Regel U ist mechanisch im Pilot, nicht hier), setzt die",
        "# Registrierung und zitiert den sha256 dieser Datei als --registered-sha256.",
        f"# Stichtag des Panels im Vorlauf: {report['cut']['cut_date']}; result_sha256 des Vorlaufs: {report['result_sha256']}",
    ]
    if source_sha256:
        header.append(f"# Quelle (Vorlauf-JSON) sha256: {source_sha256}")
    ctl = report.get("w1_determinism_control")
    header.append("# W1-Determinismus-Kontrolle gegen v5e: " + ("bestanden" if ctl and ctl["ok"] else "nicht angefordert"))
    fps = template.get("data_fingerprints") or {}
    if not (schema.is_hex64(fps.get("union_range_fingerprint")) and schema.is_hex64(fps.get("delisting_dates_sha256"))):
        header.append("# WARNUNG: Vorlauf ohne Daten-Fingerprints -- data_fingerprints ist unvollstaendig, die Modi lehnen ab.")
    return "\n".join(header) + "\n" + yaml.safe_dump(template, sort_keys=False, allow_unicode=False)


def _f(x: Any, nd: int = 6) -> str:
    if x is None:
        return "-"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    return "nan" if v != v else f"{v:.{nd}f}"


def render_prelaunch_markdown(report: dict[str, Any]) -> str:
    """ASCII Markdown of the Vorlauf v6 (numbers only; no real return anywhere)."""
    lines = ["# H-32 Vorlauf v6 (outcome-frei)", "",
             f"- result_sha256: `{report['result_sha256']}`", f"- Stichtag (Panel-Schnitt): {report['cut']['cut_date']}, "
             f"letzte Woche {report['cut']['last_week']}, {report['cut']['n_weeks']} Wochen, {report['cut']['n_symbols']} Symbole",
             f"- Replikate {report['parameters']['n_reps']}, Bootstrap {report['parameters']['n_boot']}, Seed {report['parameters']['seed']}",
             f"- Daten-Fingerprints: `{report.get('data_fingerprints')}`", "", "## Fenster", "",
             "| Fenster | Wochen | w_judged | K min/Median/max | floor_fm8 | v_fm8 | K-Reihe sha256 |", "|---|---|---|---|---|---|---|"]
    for wn, w in report["windows"].items():
        g, k = w["geometry"], w["k"]
        lines.append(f"| {wn} | {g['first_formation_week']}..{g['last_outcome_week']} | {g['w_judged']} | "
                     f"{k['min']}/{k['median']:.0f}/{k['max']} | {_f(w['floor_fm8'])} | {_f(w['v_fm8'])} | `{w['k_fm8_series_sha256'][:12]}...` |")
    lines += ["", "## Kalibrierung je Fenster (nur Streuung / Autokorrelation / Faktoranteil)", "",
              "| Fenster | Kalibrierung | rho_f | beta_sd | Ziel-Faktoranteil | Gegenprobe |", "|---|---|---|---|---|---|"]
    for wn, w in report["windows"].items():
        for name, blk in w["calibration_report"]["calibration"].items():
            lines.append(f"| {wn} | {name} | {_f(blk['rho_f'])} | {_f(blk['beta_sd_calibrated'])} | {_f(blk['target_factor_share'])} | "
                         f"z {_f(blk['gegenprobe'].get('z'), 3)} ok {blk['gegenprobe'].get('ok')} |")
    lines += ["", "## Pilot-Null m_P (stress, Richtung, extremeres aus driftfrei / Drift)", "",
              "| Variante | m_P |", "|---|---|"]
    for v in C.VARIANTS:
        lines.append(f"| {v} | {_f(report['windows']['P']['m_P'][v])} |")
    for wn in ("W1", "W2"):
        fz = report["windows"][wn]["frozen_v6"]
        lines += ["", f"## Eingefrorene Konstanten {wn}", "",
                  "| Variante | se_mean | e_se_rule | sd_week | null_mean | q95 | q95 driftfrei | q95 Drift |", "|---|---|---|---|---|---|---|---|"]
        for v in C.VARIANTS:
            lines.append(f"| {v} | " + " | ".join(_f(fz[k][v]) for k in ("se_mean", "e_se_rule", "sd_week", "null_mean", "q95",
                                                                           "q95_driftfree", "q95_drifting")) + " |")
        lines += ["", f"- ceiling_k4 {wn} (vorzeichenbereinigt, stress, driftfrei): {_f(fz['ceiling_k4'])}",
                  f"- bounce_sigma_true {wn}: {_f(report['windows'][wn]['bounce_sigma_true'])}; Survivorship (Schwellen-Einheiten): "
                  f"mom1 {_f(report['windows'][wn]['survivorship']['mom1_diff_in_ic_min_units'], 3)}, "
                  f"rev_gap {_f(report['windows'][wn]['survivorship']['rev_gap_diff_in_ic_min_units'], 3)}"]
        for key in ("stress_rel", "stress_abs"):
            if key in report["windows"][wn]:
                s = report["windows"][wn][key]
                lines.append(f"- {key}: " + (f"{s['n_days_in_window']} Tage im Fenster (Datumsfilter <= {s['date_filter']})"
                                             if s.get("available") else s.get("note", "nicht vorhanden")))
    ctl = report.get("w1_determinism_control")
    lines += ["", "## W1-Determinismus-Kontrolle gegen v5e", "",
              ("bestanden" if ctl and ctl["ok"] else "nicht angefordert (--v5e-reference)"), "",
              "KEIN VERDIKT -- der Vorlauf berechnet keine reale Signal-Outcome-Verknuepfung.", ""]
    return "\n".join(lines)


def write_prelaunch_artifacts(out_dir: Path | str, report: dict[str, Any]) -> dict[str, Any]:
    """``h32_prelaunch.json`` / ``.md`` and the K series CSV per window (outcome-free DEC-53 material)."""
    out = Path(out_dir)
    artifacts.refuse_unsafe_path(out / "x", writing=True)
    out.mkdir(parents=True, exist_ok=True)
    arts: dict[str, Any] = {}
    for wn, w in report["windows"].items():
        arts[f"k_fm8_{wn}"] = artifacts.write_series_csv(out / f"h32_prelaunch_{wn}_k_fm8.csv", w["k_fm8_series"], value_name="k")
    full = dict(report)
    full["code"] = artifacts.code_fingerprint()
    arts["json"] = artifacts.write_json(out / "h32_prelaunch.json", full)
    md = out / "h32_prelaunch.md"
    md.write_text(render_prelaunch_markdown(report), encoding="utf-8")
    arts["md"] = {"file": md.name, "sha256": artifacts.sha256_file(md)}
    return {"out_dir": str(out), "artifacts": arts}
