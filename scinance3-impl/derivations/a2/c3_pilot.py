"""C-3: pilot hand-over rule for A2 (template, DEC-103 'Pilot-Schaetzfenster-Route', DEC-99 (3), U-4 analogue).
NO PILOT NUMBER (R-C11): only thresholds, powers and error rates from nuisance quantities (work/c1.json).
Fassung 2: orchestrator decisions (a)-(f) of 2026-10-31 - stress line binds (R-C14), test null scaled and
k_pred,W = max(1, SE_T,W / SD_null,W) (R-C13, U-4 literal), Gate-(4) factor 0.9025 provisional (R-C15), rule R0
registered, R1/R2 report, R5 stricter alternative.  Prints only sha256.  Output: work/c3.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_common as cc  # noqa: E402
import c1_nullsim as c1  # noqa: E402  (helpers only: power functions, no data access at import)

P1 = c1.P1
Z, Z80, OI, G4 = c1.Z, c1.Z80, c1.OI, c1.G4
T_MIN = 2.0
PRIORS = c1.PRIORS
_N = c1._N
LINES = ("stress", "zentral")


def window_inputs(c1j: dict, line: str, wn: str) -> dict:
    L = c1j["test_windows"][wn]["lines"][line]
    return {"seb": dict(L["se_bind"]), "nul": {"sd": L["null_sd_transfer"], "d95": L["null_d95_transfer"],
                                               "kappa": L["kappa_efficiency"], "k": L["k_scale_R_C13"],
                                               "sd_shift": L["sd_null_shift_iid_sigma_within"]}}


def mde(w: dict, *, mode: str = "scaled", g4: float = G4, se_scale: float = 1.0, k_mult: float = 1.0,
        with_null: bool = True, bivariate: bool = False, z: float = Z, f_oi: float = 1.0) -> float:
    """Event-scale prior at which the product of the gate conditions of window w reaches 0.80.  se_scale: pilot raises
    SE_T (U-4 first line) -> k_pred,W rises with it (k = SE_T / SD_null); k_mult: extra factor on k (sensitivity)."""
    seb = {j: se_scale * v for j, v in w["seb"].items()}
    nul = dict(w["nul"])
    nul["k"] = max(1.0, seb["P2ss"] / nul["sd"]) * k_mult if mode == "scaled" else 1.0

    def prod(p):
        if bivariate:
            return (c1.p2_bivariate(f_oi * p, seb["P2ss"], z, nul, mode) * P1.window_power(p, seb["P3fix"], z)
                    * P1.window_power(p, seb["P3all"], z) * g4)
        return math.prod(c1.cond_powers(p, f_oi, seb, nul if with_null else None, z, mode, g4).values())
    return c1.bisect(prod, hi=300.0)


def main() -> dict:
    c1j = json.loads((cc.WORK / "c1.json").read_text(encoding="ascii"))
    vp = c1j["pre_windows"]["VP_2021-03-24..2024-05-31"]
    se_pilot = {j: vp["binding"][j]["se_bind"] for j in ("P2ss", "P3fix", "P3all")}
    se_p = se_pilot["P2ss"]
    sd_null_pilot = vp["null_P2ss"]["sd_exact"]

    thr = {}
    for line in LINES:
        W = {wn: window_inputs(c1j, line, wn) for wn in ("W1", "W2")}
        variants = {
            "R0_bindend_vorlaeufig_gate4": {},
            "R0_ohne_gate4_bis_negativpanel": {"g4": 1.0},
            "R0_k_pred_x1.1": {"k_mult": 1.1},
            "R0_pilot_se_plus_10pct": {"se_scale": 1.1},
            "R1_bivariat_P2ss_exakt_bericht": {"bivariate": True},
            "R2_ohne_null_faktor_bericht": {"with_null": False},
            "fassung1_unskaliert_ohne_gate4": {"mode": "unscaled", "g4": 1.0},
            "a3_praxis_gate4": {"z": P1.Z_PER_WINDOW_A3_PRACTICE},
        }
        res = {}
        for name, kw in variants.items():
            comp = {wn: mde(W[wn], **kw) for wn in W}
            res[name] = {"mde80_prod_by_window": comp, "c_A2": max(comp.values()),
                         "binding_window": max(comp, key=comp.get)}
        comp_oi = {wn: mde(W[wn], f_oi=OI) for wn in W}
        res["lesart_OI_0842"] = {"event_scale_by_window": comp_oi, "threshold_on_pilot_contrast": OI * max(comp_oi.values())}
        res["k_pred_by_window_pre_pilot"] = {wn: max(1.0, W[wn]["seb"]["P2ss"] / W[wn]["nul"]["sd"]) for wn in W}
        thr[line] = res

    c_bind = thr["stress"]["R0_bindend_vorlaeufig_gate4"]["c_A2"]
    c_cent = thr["zentral"]["R0_bindend_vorlaeufig_gate4"]["c_A2"]
    c_r5 = c_bind + Z80 * se_p
    c_f1 = thr["zentral"]["fassung1_unskaliert_ohne_gate4"]["c_A2"]

    def pilot_power(mu_c: float, mu_p3: float, c: float) -> float:
        t = max(c, T_MIN * se_p)
        return (_N.cdf((mu_c - t) / se_p) * _N.cdf(mu_p3 / se_pilot["P3fix"]) * _N.cdf(mu_p3 / se_pilot["P3all"]))

    grid = {}
    for pr in PRIORS:
        row = {}
        for lab, f, glab in (("kontrast_skala", 1.0, "unabgeschwaecht"), ("ereignis_skala_oi_0842", OI, "oi_0842")):
            for line in LINES:
                g = [c1j["test_windows"][w]["lines"][line][f"prior_grid_{glab}"][str(pr)] for w in ("W1", "W2")]
                tp = g[0]["product_scaled_gate4"] * g[1]["product_scaled_gate4"]
                c_line = thr[line]["R0_bindend_vorlaeufig_gate4"]["c_A2"]
                pp = pilot_power(f * pr, pr, c_line)
                row[f"{lab}|{line}"] = {"c_A2": c_line, "pilot_handover_power": pp, "test_product_W1xW2": tp,
                                        "two_stage_power_product": pp * tp}
            row[f"{lab}|R5_stress"] = {"c_A2_plus_0_84_SE_P": c_r5, "pilot_handover_power": pilot_power(f * pr, pr, c_r5)}
            row[f"{lab}|fassung1_zentral"] = {"c_A2": c_f1, "pilot_handover_power": pilot_power(f * pr, pr, c_f1)}
        grid[str(pr)] = row

    def upper(t: float) -> float:                     # 1 - Phi(t) without cancellation in the far tail
        return 0.5 * math.erfc(t / math.sqrt(2.0))
    alpha = {"R0_stress": upper(max(c_bind, T_MIN * se_p) / se_p),
             "R0_zentral_bericht": upper(max(c_cent, T_MIN * se_p) / se_p),
             "fassung1_zentral": upper(max(c_f1, T_MIN * se_p) / se_p)}
    bw = thr["stress"]["R0_bindend_vorlaeufig_gate4"]["binding_window"]
    pk = c1j["test_windows"][bw]["lines"]["stress"]["mde80_event_scale_unabgeschwaecht"]["pk_at_target"]
    out = {
        "label": cc.LABEL, "rules": "R-C11, R-C13..R-C16; Regel U-A2 = R0 (Vorlage)",
        "c1_sha256": cc.sha256(cc.WORK / "c1.json"),
        "pilot_period": ["2021-03-24", "2024-05-31"], "pilot_counts": vp["counts"], "pilot_structure": vp["structure"],
        "se_pilot_nuisance": se_pilot, "sd_null_pilot_exact": sd_null_pilot,
        "t_min": T_MIN, "z_krit": Z, "z_power": Z80, "oi_factor": OI, "gate4_factor_provisional": G4,
        "thresholds": thr, "c_A2_R0_stress_bindend": c_bind, "c_A2_R0_zentral_bericht": c_cent,
        "c_A2_R5_stress": c_r5, "c_A2_fassung1": c_f1, "t_P_at_c_A2": c_bind / se_p,
        "pilot_power_grid": grid,
        "error_rates": {"pilot_alpha_upper_bound": alpha, "test_alpha_per_window": 0.05,
                        "test_c10_joint_upper_bound": 0.05 ** 2,
                        "two_stage_false_pass_upper_bound": {k: v * 0.05 ** 2 for k, v in alpha.items()},
                        "note": "Pilot und Test auf getrennten Daten (DEC-99 (6)); Test-Fehlerrate unveraendert"},
        "positive_control": {"binding_window": bw, "line": "stress",
                             "rule": "Ziel = MDE80prod (R0, stress, skaliert, Gate-(4)-Faktor) im bindenden Fenster; "
                                     "Kriterium (b) = erwartete PASS-Quote - 2,3263 x Binomial-SE (200 Seeds)",
                             **pk},
    }
    return out


if __name__ == "__main__":
    res = main()
    h = cc.dump(res, cc.WORK / "c3.json")
    print("c3.json sha256", h)
