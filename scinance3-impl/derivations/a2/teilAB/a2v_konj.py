"""Fassung 2, A-1 / A-3 / A-5 (R-15): conjunction power against all placebos of a set (Monte Carlo, shared
event term), product of single powers (lower bound, carries the assignment by orchestrator decision),
the futures-free P2'' variant and the difference-in-differences contrast.  Inputs are the guarded work
JSONs only (dispersion, correlations, counts); every power / MDE / regime number via power_p1."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a2v_common as c  # noqa: E402
from bybit_edge.research import power_p1  # noqa: E402

Z_P1 = power_p1.z_krit(0.05)
Z_A3 = power_p1.Z_PER_WINDOW_A3_PRACTICE
PRIORS = (5.0, 8.0, 12.0, 16.5, 18.25, 25.0)
N_MC = 400_000
SEED_MC = 94
WIN = {"W1": "W1_2024-07-01..2025-06-30", "W2": "W2_DEC99_2025-07-01..2026-06-28"}


def J(name):
    return json.loads((c.WORK / name).read_text())


def main() -> dict:
    sg, oi, pw, cr, fu = J("a2v_sigma30.json"), J("a2v_oi.json"), J("a2v_power.json"), J("a2v_corr2.json"), J("a2v_fut.json")
    disp, pers = sg["dispersion"], sg["persistence"]
    N = {w: oi["event_counts"][lab]["ohne_ausreisser_regel_R4"] for w, lab in WIN.items()}
    futmodo = {w: fu["by_window"][lab]["modo_days_with_future_delivery_any_ccy"] for w, lab in WIN.items()}
    att = pw["oi_attenuation"]
    sc = cr["same_day_corr_cluster"]

    def sdc(slot, cl):
        return disp[slot][cl]["CLUSTER"]["sd"], pers[slot][cl]["CLUSTER"]["c_bind"]

    # placebo catalogue: series, class, N(w), overlap class for correlations
    def n_of(cl, w):
        return N[w][cl]
    PL = {
        "P2_NONFRI": {"sd_c": sdc("pre", "NONFRI"), "N": lambda w: n_of("NONFRI", w), "cls": "NONFRI", "series": "pre"},
        "P2s_MODO": {"sd_c": sdc("pre", "MODO"), "N": lambda w: n_of("MODO", w), "cls": "MODO", "series": "pre"},
        "P2ss_MODO_ohne_Futures": {"sd_c": sdc("pre", "MODO"), "N": lambda w: n_of("MODO", w) - futmodo[w],
                                   "cls": "MODO", "series": "pre"},
        "P1s_FRI_W": {"sd_c": sdc("pre", "FRI_W"), "N": lambda w: n_of("FRI_W", w), "cls": "FRI_W", "series": "pre"},
        "P3fix_ALL_1530": {"sd_c": sdc("fix1530", "ALL"), "N": lambda w: n_of("ALL", w), "cls": "ALL", "series": "fix1530"},
        "P3all_ALL_44slots": {"sd_c": sdc("p3all_44slots", "ALL"), "N": lambda w: n_of("ALL", w), "cls": "ALL",
                              "series": "p3all"},
        "P3_FRI_1530_paired": {"paired": True},
    }

    def rho_pair(a, b):
        """same-day correlation and common-day class of two placebos (R-15)."""
        pa_, pb_ = PL[a], PL[b]
        s = {pa_["series"], pb_["series"]}
        if pa_["series"] == "pre" and pb_["series"] == "pre":
            return 0.0, None                                    # disjoint day classes
        pre_one = pa_ if pa_["series"] == "pre" else pb_ if pb_["series"] == "pre" else None
        if pre_one is not None:
            other = pb_ if pre_one is pa_ else pa_
            key = "pre_vs_fix1530" if other["series"] == "fix1530" else "pre_vs_p3all44"
            return sc[key][pre_one["cls"]]["pearson"], pre_one
        if s == {"fix1530", "p3all"}:
            return sc["fix1530_vs_p3all44"]["ALL"]["pearson"], "ALL"
        raise ValueError((a, b))

    designs = {
        "D_i__S1_P2s": ("FRI", ["P2s_MODO"], {"P2s_MODO": "FRI/MODO"}),
        "D_i__S2_P2s_P3fix": ("FRI", ["P2s_MODO", "P3fix_ALL_1530"], {"P2s_MODO": "FRI/MODO"}),
        "D_i__S3_P2s_P3fix_P3all": ("FRI", ["P2s_MODO", "P3fix_ALL_1530", "P3all_ALL_44slots"], {"P2s_MODO": "FRI/MODO"}),
        "D_i_W": ("FRI_W", ["P2s_MODO", "P3fix_ALL_1530", "P3all_ALL_44slots"], {"P2s_MODO": "FRI_W/MODO"}),
        "PRD_a__P2_P3fix_P3all": ("FRI", ["P2_NONFRI", "P3fix_ALL_1530", "P3all_ALL_44slots"], {"P2_NONFRI": "FRI/NONFRI"}),
        "D_i_s": ("FRI", ["P2s_MODO", "P3fix_ALL_1530", "P3all_ALL_44slots", "P3_FRI_1530_paired"], {"P2s_MODO": "FRI/MODO"}),
        "D_ii": ("FRI_MQ", ["P1s_FRI_W", "P2s_MODO", "P3fix_ALL_1530", "P3all_ALL_44slots"],
                 {"P1s_FRI_W": "FRI_MQ/FRI_W", "P2s_MODO": "FRI_MQ/MODO"}),
        "D_i_futfrei__S1_P2ss": ("FRI", ["P2ss_MODO_ohne_Futures"], {"P2ss_MODO_ohne_Futures": "FRI/MODO"}),
        "D_i_futfrei__S3_P2ss_P3fix_P3all": ("FRI", ["P2ss_MODO_ohne_Futures", "P3fix_ALL_1530", "P3all_ALL_44slots"],
                                             {"P2ss_MODO_ohne_Futures": "FRI/MODO"}),
    }

    def cov_matrix(ev_cl, pls, w):
        sd_e, c_e = sdc("pre", ev_cl)
        n_e = N[w][ev_cl]
        se_e2 = sd_e * sd_e * c_e / n_e
        se = {}
        for p in pls:
            if PL[p].get("paired"):
                continue
            sd, cc = PL[p]["sd_c"]
            se[p] = sd * math.sqrt(cc / PL[p]["N"](w))
        k = len(pls)
        S = np.zeros((k, k))
        for i, a in enumerate(pls):
            for j, b in enumerate(pls):
                if i == j:
                    if PL[a].get("paired"):
                        sdd, cd = sdc("pre_minus_fix1530", ev_cl)
                        S[i, i] = sdd * sdd * cd / n_e
                    else:
                        S[i, i] = se_e2 + se[a] ** 2
                    continue
                pa_, pb_ = (a, b) if not PL[a].get("paired") else (b, a)
                if PL[pb_].get("paired") or PL[pa_].get("paired"):
                    # paired Friday 15:30 component F vs placebo pa_
                    other = pa_
                    sd_f, c_f = sdc("fix1530", ev_cl)
                    se_f = sd_f * math.sqrt(c_f / n_e)
                    if PL[other]["series"] == "pre":
                        cov = 0.0                                      # disjoint days
                    else:
                        rho = 1.0 if PL[other]["series"] == "fix1530" else sc["fix1530_vs_p3all44"]["FRI"]["pearson"]
                        n_o = PL[other]["N"](w)
                        cov = rho * se_f * se[other] * n_e / math.sqrt(n_e * n_o)
                    S[i, j] = se_e2 + cov
                    continue
                rho, common = rho_pair(a, b)
                if common is None:
                    cov = 0.0
                else:
                    n_c = PL[a]["N"](w) if common is PL[a] else PL[b]["N"](w) if common is PL[b] else N[w]["ALL"]
                    n_a, n_b = PL[a]["N"](w), PL[b]["N"](w)
                    cov = rho * se[a] * se[b] * n_c / math.sqrt(n_a * n_b)
                S[i, j] = se_e2 + cov
        return S, math.sqrt(se_e2)

    out_d = {}
    for dname, (ev_cl, pls, attkeys) in designs.items():
        res = {"event": f"pre/{ev_cl}", "placebos": pls, "windows": {}}
        draws = {}
        for w in ("W1", "W2"):
            S, se_e = cov_matrix(ev_cl, pls, w)
            ev = np.linalg.eigvalsh(S)
            assert ev.min() > 0, (dname, w, ev)
            se = np.sqrt(np.diag(S))
            R = S / np.outer(se, se)
            L = np.linalg.cholesky(R)
            rng = np.random.default_rng(SEED_MC)
            draws[w] = (rng.standard_normal((N_MC, len(pls))) @ L.T, se)
            res["windows"][w] = {"n_event": N[w][ev_cl], "se_event": se_e,
                                 "se_contrast": dict(zip(pls, se.tolist())),
                                 "test_corr_matrix": R.round(6).tolist(),
                                 "n_placebo": {p: (N[w][ev_cl] if PL[p].get("paired") else PL[p]["N"](w)) for p in pls}}
        lines = {}
        for line in ("unattenuated", "oi_attenuated_strict"):
            f = np.array([att[attkeys[p]]["factor_strict"] if (line != "unattenuated" and p in attkeys) else 1.0
                          for p in pls])

            def pw_single(mu, w, z):
                se = draws[w][1]
                return [power_p1.window_power(mu * fj, sj, z) for fj, sj in zip(f, se)]

            def pw_joint(mu, w, z):
                Z, se = draws[w]
                return float(np.mean(np.all(Z >= (z - mu * f / se), axis=1)))

            def bisect(fun, target=0.8):
                lo, hi = 0.0, 300.0
                for _ in range(40):
                    mid = 0.5 * (lo + hi)
                    if fun(mid) >= target:
                        hi = mid
                    else:
                        lo = mid
                return hi
            mde = {}
            for w in ("W1", "W2"):
                se = draws[w][1]
                mde[w] = {
                    "mde80_event_single_binding_p1": max(power_p1.mde80(sj, Z_P1) / fj for sj, fj in zip(se, f)),
                    "mde80_event_joint_p1": bisect(lambda mu: pw_joint(mu, w, Z_P1)),
                    "mde80_event_product_p1": bisect(lambda mu: math.prod(pw_single(mu, w, Z_P1))),
                    "mde80_event_single_binding_a3": max(power_p1.mde80(sj, Z_A3) / fj for sj, fj in zip(se, f)),
                    "mde80_event_joint_a3": bisect(lambda mu: pw_joint(mu, w, Z_A3)),
                    "mde80_event_product_a3": bisect(lambda mu: math.prod(pw_single(mu, w, Z_A3))),
                }
            grid = {}
            for mu in PRIORS:
                regs = []
                for j, p in enumerate(pls):
                    ses = [draws["W1"][1][j], draws["W2"][1][j]]
                    pr = mu * f[j]
                    regs.append((power_p1.assign_regime([pr, pr], ses), power_p1.assign_regime_a3_practice([pr, pr], ses)))
                prod_w = [math.prod(r[0]["window_power"][k] for r in regs) for k in (0, 1)]
                prod_gate = math.prod(r[0]["gate_power_product"] for r in regs)
                prod_a3 = [math.prod(r[1]["window_power"][k] for r in regs) for k in (0, 1)]
                if min(prod_w) >= power_p1.POWER_TARGET - 1e-12:
                    reg = power_p1.REGIME_C10
                elif prod_gate >= power_p1.POWER_TARGET - 1e-12:
                    reg = power_p1.REGIME_DEC52
                else:
                    reg = power_p1.REGIME_GL012
                reg_a3 = power_p1.REGIME_C10 if min(prod_a3) >= power_p1.POWER_TARGET - 1e-12 else power_p1.REGIME_GL012
                joint = [pw_joint(mu, w, Z_P1) for w in ("W1", "W2")]
                single = {w: dict(zip(pls, pw_single(mu, w, Z_P1))) for w in ("W1", "W2")}
                grid[f"{mu:g}"] = {
                    "single_power_p1": single,
                    "single_binding_power_p1": [min(single[w].values()) for w in ("W1", "W2")],
                    "joint_power_p1_bericht": joint,
                    "product_power_p1": prod_w, "product_gate_power_dec52": prod_gate,
                    "regime_p1_product": reg, "regime_a3_product": reg_a3,
                    "product_power_a3": prod_a3,
                    "regime_joint_bericht": "C10" if min(joint) >= 0.8 else "unter 0,80",
                    "label_only_dec94": power_p1.LABEL_ONLY_DEC94 if (reg != "GL012" and reg_a3 == "GL012") else None}
            lines[line] = {"factors": dict(zip(pls, f.tolist())), "mde80": mde, "prior_grid": grid}
        res["lines"] = lines
        out_d[dname] = res

    # B6: difference-in-differences (Friday r_pre - r[15:30]) - (Mo-Do r_pre - r[15:30])
    sd_f, c_f = sdc("pre_minus_fix1530", "FRI")
    sd_m, c_m = sdc("pre_minus_fix1530", "MODO")
    rw = cr["did_week_corr_fri_vs_modo_paired_series"]["pearson"]
    did = {"sd_paired_diff_fri": sd_f, "c_paired_diff_fri": c_f, "sd_paired_diff_modo": sd_m,
           "c_paired_diff_modo": c_m, "week_corr_used_only_if_negative": rw, "windows": {}}
    for w in ("W1", "W2"):
        se_f = sd_f * math.sqrt(c_f / N[w]["FRI"])
        se_m = sd_m * math.sqrt(c_m / N[w]["MODO"])
        cov = -2 * rw * se_f * se_m if rw < 0 else 0.0
        se = math.sqrt(se_f ** 2 + se_m ** 2 + cov)
        did["windows"][w] = {"n_fri": N[w]["FRI"], "n_modo": N[w]["MODO"], "se_fri_part": se_f, "se_modo_part": se_m,
                             "se_did": se, "mde80_p1": power_p1.mde80(se, Z_P1), "mde80_a3": power_p1.mde80(se, Z_A3)}
    ses = [did["windows"]["W1"]["se_did"], did["windows"]["W2"]["se_did"]]
    dg = {}
    for line, fac in (("unattenuated", 1.0), ("oi_attenuated_strict", att["FRI/MODO"]["factor_strict"])):
        cell = {}
        for mu in PRIORS:
            r = power_p1.assign_regime([mu * fac] * 2, ses)
            a3 = power_p1.assign_regime_a3_practice([mu * fac] * 2, ses)
            cell[f"{mu:g}"] = {"prior_did": mu * fac, "window_power_p1": r["window_power"], "regime_p1": r["regime"],
                               "regime_a3": a3["regime"]}
        dg[line] = cell
    did["prior_grid"] = dg
    did["mde80_event_scale_attenuated_p1"] = [power_p1.mde80(x, Z_P1) / att["FRI/MODO"]["factor_strict"] for x in ses]

    out = {"label": c.LABEL, "quelle": "S:a2v_konj.py (R-15; power_p1)",
           "festlegung_orchestrator": "Zuordnung (C10/DEC52/GL012) traegt das PRODUKT der Einzel-Powers (Untergrenze, "
                                      "analog DEC-94 (6)); gemeinsame Power = Bericht; Richtung Strenge",
           "mc": {"n_draws": N_MC, "seed": SEED_MC, "z_krit_p1": Z_P1, "z_a3_practice": Z_A3},
           "n_per_window": {w: {k: N[w][k] for k in ("FRI", "FRI_W", "FRI_MQ", "MODO", "NONFRI", "ALL")} for w in WIN},
           "modo_days_with_future_delivery": futmodo,
           "designs": out_d, "did": did}
    c.check_out(out)
    return out


if __name__ == "__main__":
    print("sha256", c.dump(main(), c.WORK / "a2v_konj.json"))
