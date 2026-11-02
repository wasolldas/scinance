"""Part B-4: placebo SE, SE(contrast) and MDE80 per design with the measured nuisance (R-9, R-10).
Every power / MDE / regime number comes from bybit_edge.research.power_p1.  No return data is read
here; inputs are the guarded JSON outputs of a2v_sigma30.py (dispersion only) and a2v_oi.py (counts).

DESIGNS (fixed in R-9 / A-2 before this script; event and placebo sets are calendar classes):
  PRD_a  reference: events FRI (all Fridays), placebo P2 = all non-Friday slots [07:30, 08:00) (NONFRI)
  PRD_b  reference: events FRI_MQ (monthly incl. quarterly), placebo P1 -> FRI_W (weekly-only Fridays)
  D_i    events FRI; placebos P2' = MODO [07:30,08:00), P3fix = ALL [15:30,16:00), P3all = ALL per-day
         average of the 44 half-hours outside [07:00, 09:00)
  D_i_s  D_i plus the paired same-day placebo P3'-Fri = FRI [15:30,16:00) (difference per day)
  D_i_W  events FRI_W (weekly-only Fridays); placebos as D_i
  D_ii   events FRI_MQ; placebos P1' = FRI_W, P2' = MODO, P3fix, P3all
  D_iii  OI-sorted top vs bottom quintile (ex post, report only; SD of ALL, N 73 / 73)
"""
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

Z_P1 = power_p1.z_krit(0.05)                       # 1.6449
Z_A3 = power_p1.Z_PER_WINDOW_A3_PRACTICE           # 2.4865
PRIORS = (5.0, 8.0, 12.0, 16.5, 25.0)
WINDOWS = {"W1": "W1_2024-07-01..2025-06-30", "W2": "W2_DEC99_2025-07-01..2026-06-28"}
WINDOW_W2_FULL = "W2_2025-07-01..2026-06-30"
YEARS = ("2021", "2022", "2023", "2024")
# REZENZ geometry (DEC-99 (1)/(8)): youngest window ends 2026-06-28; equal windows back to back
LAST_JUDGED = 2026 + (31 + 28 + 31 + 30 + 31 + 28) / 365.0          # 2026-06-28 as decimal year
NUIS_END = 2024 + (31 + 29 + 31 + 30 + 31) / 366.0                    # 2024-05-31
DATA_START_ETH = 2021 + (31 + 28 + 14) / 365.0                        # 2021-03-15 (DEC-98 N4 (d))


def load():
    s = json.loads((c.WORK / "a2v_sigma30.json").read_text())
    o = json.loads((c.WORK / "a2v_oi.json").read_text())
    return s, o


def years_for_power(prior: float, se12: float, z: float) -> float:
    """Window length L (years) with window power 0.80, SE(L) = se12 / sqrt(L); bisection on
    power_p1.window_power."""
    lo, hi = 1e-3, 1e4
    f = lambda L: power_p1.window_power(prior, se12 / math.sqrt(L), z) - power_p1.POWER_TARGET
    if f(hi) < 0:
        return float("inf")
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if f(mid) >= 0:
            hi = mid
        else:
            lo = mid
    return hi


def main() -> dict:
    s, o = load()
    disp, pers = s["dispersion"], s["persistence"]
    ev = o["event_counts"]
    N = {w: ev[lab]["ohne_ausreisser_regel_R4"] for w, lab in WINDOWS.items()}
    N_full = ev[WINDOW_W2_FULL]["ohne_ausreisser_regel_R4"]

    def comp(slot: str, cl: str, variant: str) -> dict:
        """SD and c of the cluster series of a slot/class under a nuisance variant."""
        d = disp[slot][cl]
        c_bind = pers[slot][cl]["CLUSTER"]["c_bind"] if slot in pers and cl in pers[slot] else None
        sd_full = d["CLUSTER"]["sd"]
        yrs = {y: v["CLUSTER"]["sd"] for y, v in d["by_year"].items() if v["CLUSTER"]["n"] >= 10}
        if variant == "zentral":
            return {"sd": sd_full, "c": c_bind}
        if variant == "c1":
            return {"sd": sd_full, "c": 1.0}
        if variant == "stress_max_year":
            y = max(yrs, key=yrs.get)
            return {"sd": yrs[y], "c": c_bind, "year": y}
        if variant == "min_year":
            y = min(yrs, key=yrs.get)
            return {"sd": yrs[y], "c": c_bind, "year": y}
        raise ValueError(variant)

    def bilanz_formula(cl: str, n: int) -> float:
        """[pb:A2] term sigma30^2 (1 + rho) / (2 N) with measured pooled sigma and rho (c = 1)."""
        sig = disp["pre"][cl]["sigma_pooled"]
        rho = s["rho_btc_eth"]["pre"][cl]["pearson"]
        return sig * sig * (1 + rho) / (2 * n)

    # OI attenuation factors (R-10): strict = smallest q50 ratio over {BTC, ETH} x {W1, W2_DEC99}
    def oi_ratio(key: str) -> dict:
        vals = {}
        for wl in WINDOWS.values():
            for ccy in ("BTC", "ETH"):
                vals[f"{wl}|{ccy}"] = o["size_by_period_and_class"][wl][ccy]["ratio_q50"][key]
        nuis = {ccy: o["size_by_period_and_class"]["nuisance_2021-03-24..2024-05-31"][ccy]["ratio_q50"][key]
                for ccy in ("BTC", "ETH")}
        strict = min(vals.values())
        return {"q50_ratio_by_window_ccy": vals, "q50_ratio_nuisance_period": nuis, "strict_ratio": strict,
                "factor_strict": 1 - 1 / strict, "factor_nuisance_period": 1 - 1 / min(nuis.values())}
    att = {"FRI/MODO": oi_ratio("FRI/MODO"), "FRI/NONFRI": oi_ratio("FRI/NONFRI"), "FRI_W/MODO": oi_ratio("FRI_W/MODO"),
           "FRI_MQ/FRI_W": oi_ratio("FRI_MQ/FRI_W"), "FRI_MQ/MODO": oi_ratio("FRI_MQ/MODO")}

    # contrast definitions: (name, event (slot, class), placebo (slot, class) or 'paired', OI ratio key or None)
    designs = {
        "PRD_a": {"event": ("pre", "FRI"), "placebos": {"P2_NONFRI": (("pre", "NONFRI"), "FRI/NONFRI")}},
        "PRD_b": {"event": ("pre", "FRI_MQ"), "placebos": {"P1_FRI_W": (("pre", "FRI_W"), "FRI_MQ/FRI_W")}},
        "D_i": {"event": ("pre", "FRI"), "placebos": {"P2_MODO": (("pre", "MODO"), "FRI/MODO"),
                                                       "P3fix_ALL_1530": (("fix1530", "ALL"), None),
                                                       "P3all_ALL_44slots": (("p3all_44slots", "ALL"), None)}},
        "D_i_s": {"event": ("pre", "FRI"), "placebos": {"P2_MODO": (("pre", "MODO"), "FRI/MODO"),
                                                         "P3fix_ALL_1530": (("fix1530", "ALL"), None),
                                                         "P3all_ALL_44slots": (("p3all_44slots", "ALL"), None),
                                                         "P3_FRI_1530_paired": ("paired", None)}},
        "D_i_W": {"event": ("pre", "FRI_W"), "placebos": {"P2_MODO": (("pre", "MODO"), "FRI_W/MODO"),
                                                           "P3fix_ALL_1530": (("fix1530", "ALL"), None),
                                                           "P3all_ALL_44slots": (("p3all_44slots", "ALL"), None)}},
        "D_ii": {"event": ("pre", "FRI_MQ"), "placebos": {"P1_FRI_W": (("pre", "FRI_W"), "FRI_MQ/FRI_W"),
                                                           "P2_MODO": (("pre", "MODO"), "FRI_MQ/MODO"),
                                                           "P3fix_ALL_1530": (("fix1530", "ALL"), None),
                                                           "P3all_ALL_44slots": (("p3all_44slots", "ALL"), None)}},
    }
    xcorr = s["cross_corr_event_vs_placebo"]
    xc_map = {("FRI", "MODO"): xcorr["FRI_vs_MODO_same_iso_week"]["pearson"],
              ("FRI_W", "MODO"): xcorr["FRI_W_vs_MODO_same_iso_week"]["pearson"],
              ("FRI_MQ", "FRI_W"): xcorr["FRI_MQ_vs_FRI_W_same_month"]["pearson"],
              ("FRI", "NONFRI"): xcorr["FRI_vs_NONFRI_same_iso_week"]["pearson"]}

    out_designs = {}
    for dname, dd in designs.items():
        e_slot, e_cl = dd["event"]
        dres = {"event": f"{e_slot}/{e_cl}", "contrasts": {}}
        for variant in ("zentral", "c1", "stress_max_year", "min_year"):
            vres = {}
            for pname, (pdef, okey) in dd["placebos"].items():
                win = {}
                for w in ("W1", "W2"):
                    if pdef == "paired":
                        cp = comp("pre_minus_fix1530", e_cl, variant)
                        n_e = N[w][e_cl]
                        se = cp["sd"] * math.sqrt(cp["c"] / n_e)
                        win[w] = {"n_event": n_e, "n_placebo": n_e, "sd_paired_diff": cp["sd"], "c": cp["c"],
                                  "se_contrast": se, "year_sd": cp.get("year")}
                        continue
                    p_slot, p_cl = pdef
                    ce, cpl = comp(e_slot, e_cl, variant), comp(p_slot, p_cl, variant)
                    n_e, n_p = N[w][e_cl], N[w][p_cl]
                    se_e = ce["sd"] * math.sqrt(ce["c"] / n_e)
                    se_p = cpl["sd"] * math.sqrt(cpl["c"] / n_p)
                    rx = xc_map.get((e_cl, p_cl))
                    cov_term = 0.0
                    if rx is not None and rx < 0:        # only if it raises the SE (no credit)
                        cov_term = -2 * rx * se_e * se_p
                    se = math.sqrt(se_e ** 2 + se_p ** 2 + cov_term)
                    win[w] = {"n_event": n_e, "n_placebo": n_p, "sd_event": ce["sd"], "c_event": ce["c"],
                              "sd_placebo": cpl["sd"], "c_placebo": cpl["c"], "se_event": se_e,
                              "se_placebo": se_p, "cross_corr_used": rx, "cov_term_added": cov_term,
                              "se_contrast": se, "year_sd_event": ce.get("year"), "year_sd_placebo": cpl.get("year")}
                    if variant == "zentral" and e_slot == "pre" and p_slot == "pre":
                        bf = math.sqrt(bilanz_formula(e_cl, n_e) + bilanz_formula(p_cl, n_p))
                        win[w]["se_contrast_bilanz_formula_measured_inputs_c1"] = bf
                ses = [win["W1"]["se_contrast"], win["W2"]["se_contrast"]]
                vres[pname] = {"windows": win, "oi_ratio_key": okey,
                               "mde80_p1": [power_p1.mde80(x, Z_P1) for x in ses],
                               "mde80_a3_practice": [power_p1.mde80(x, Z_A3) for x in ses]}
            # binding placebo by largest SE (PRD 5.2), W1 and W2
            bind = max(vres, key=lambda k: max(vres[k]["windows"]["W1"]["se_contrast"],
                                               vres[k]["windows"]["W2"]["se_contrast"]))
            dres["contrasts"][variant] = {"by_placebo": vres, "binding_placebo_largest_se": bind}
        # power over the prior grid (zentral = binding nuisance line; stress and c1 as report)
        grid = {}
        for variant in ("zentral", "stress_max_year", "c1"):
            vres = dres["contrasts"][variant]["by_placebo"]
            gcell = {}
            for prior in PRIORS:
                pcell = {}
                for line in ("unattenuated", "oi_attenuated_strict"):
                    per_pl = {}
                    for pname, pv in vres.items():
                        okey = pv["oi_ratio_key"]
                        if line == "oi_attenuated_strict" and okey is None:
                            pr = prior                     # placebo without option TWAP / reference: full prior
                        elif line == "oi_attenuated_strict":
                            pr = prior * att[okey]["factor_strict"]
                        else:
                            pr = prior
                        ses = [pv["windows"]["W1"]["se_contrast"], pv["windows"]["W2"]["se_contrast"]]
                        reg = power_p1.assign_regime([pr, pr], ses)
                        a3 = power_p1.assign_regime_a3_practice([pr, pr], ses)
                        se12 = max(ses)
                        per_pl[pname] = {
                            "prior_contrast": pr, "window_power_p1": reg["window_power"],
                            "regime_p1": reg["regime"], "gate_power_product_p1": reg["gate_power_product"],
                            "window_power_a3": a3["window_power"], "regime_a3_practice": a3["regime"],
                            "label_only_dec94": a3["label"],
                            "years_per_window_c10_p1": years_for_power(pr, se12, Z_P1),
                            "years_per_window_c10_a3": years_for_power(pr, se12, Z_A3)}
                    # binding contrast = smallest P-1 window power (all placebos must hold)
                    bind = min(per_pl, key=lambda k: min(per_pl[k]["window_power_p1"]))
                    pcell[line] = {"by_placebo": per_pl, "binding_placebo_min_power": bind,
                                   "regime_p1_binding": per_pl[bind]["regime_p1"],
                                   "regime_a3_binding": per_pl[bind]["regime_a3_practice"],
                                   "min_window_power_p1": min(per_pl[bind]["window_power_p1"]),
                                   "years_per_window_c10_p1_binding": per_pl[bind]["years_per_window_c10_p1"],
                                   "years_per_window_c10_a3_binding": per_pl[bind]["years_per_window_c10_a3"]}
                gcell[f"{prior:g}"] = pcell
            grid[variant] = gcell
        dres["prior_grid"] = grid
        out_designs[dname] = dres

    # D_iii (report only)
    sd_all = disp["pre"]["ALL"]["CLUSTER"]["sd"]
    c_all = pers["pre"]["ALL"]["CLUSTER"]["c_bind"]
    n_q = {w: o["design_iii_oi_sorted_report"]["by_period"][lab]["quintil"]["n_top"] for w, lab in
           {"W1": "W1_2024-07-01..2025-06-30", "W2": "W2_DEC99_2025-07-01..2026-06-28"}.items()}
    se3 = {w: sd_all * math.sqrt(2 * c_all / n) for w, n in n_q.items()}
    out_designs["D_iii_report"] = {"rule": "oberes gegen unteres OI-Quintil (ex post), SD und c der Klasse ALL, "
                                           "N je Seite 73; nur Bericht, nicht registrierbar (OI am Verfall ex post)",
                                   "n_per_side": n_q, "se_contrast": se3,
                                   "mde80_p1": {w: power_p1.mde80(v, Z_P1) for w, v in se3.items()}}

    # Bilanz / PRD reproduction (inputs from the Akte, power_p1 for MDE)
    def bil(sig, rho, n, se_p):
        se_e = sig * math.sqrt((1 + rho) / (2 * n))
        se = math.sqrt(se_e ** 2 + se_p ** 2)
        return {"se_event": se_e, "se_placebo": se_p, "se_contrast": se,
                "mde80_p1": power_p1.mde80(se, Z_P1), "mde80_a3_practice": power_p1.mde80(se, Z_A3)}
    repro = {"weekly_bilanz": bil(36.0, 0.815, 52, 36.0 * math.sqrt((1 + 0.8) / (2 * 313))),
             "monthly_bilanz": bil(36.0, 0.815, 12, 36.0 * math.sqrt((1 + 0.8) / (2 * 40))),
             "note": "Akte: sigma30 36 (PRD 5.2), rho 0,815 (DEC-67 E4) fuer das Ereignis, Placebo wie PRD (rho 0,8, "
                     "N 313 bzw. 40); Bilanz 2.4: 4,76/1,93/5,13 bzw. 9,90/5,40/11,28"}

    # c_bind under iid (reference for the P-3 max rule; seeded Monte Carlo, normal)
    rng = np.random.default_rng(c.SEED)
    def cbind(x):
        n = x.size
        cands = [power_p1.variance_factor(x, b).c_hat for b in (4, 8, 13) if n >= b + 2]
        for L in (4, 8, 13):
            if n // L >= 8:
                m = n // L
                bm = x[: m * L].reshape(m, L).sum(axis=1) / L
                cands.append(float(L * np.var(bm, ddof=1) / np.var(x, ddof=1)))
        return max(1.0, *cands)
    iid = {}
    for cl in ("FRI_MQ", "FRI_W", "FRI", "WE", "MODO"):
        n = pers["pre"][cl]["CLUSTER"]["n"]
        sims = np.array([cbind(rng.standard_normal(n)) for _ in range(1000)])
        obs = pers["pre"][cl]["CLUSTER"]["c_bind"]
        iid[cl] = {"n": n, "q50": float(np.quantile(sims, 0.5)), "q90": float(np.quantile(sims, 0.9)),
                   "q95": float(np.quantile(sims, 0.95)), "observed_c_bind": obs,
                   "share_sims_ge_observed": float((sims >= obs).mean())}

    res = {"label": c.LABEL, "quelle": "S:a2v_power.py (R-9, R-10; power_p1)",
           "z_krit_p1": Z_P1, "mde_factor_p1": power_p1.mde_factor(0.05), "z_a3_practice": Z_A3,
           "mde_factor_a3_practice": Z_A3 + power_p1.Z_POWER,
           "windows": {w: lab for w, lab in WINDOWS.items()}, "n_per_window": N,
           "n_W2_full_2025-07-01..2026-06-30": N_full, "priors_bp": list(PRIORS),
           "prior_sources": {"16.5": "sek, Ni/Pearson/Poteshman 2005, Monatsverfaelle US-Aktien (PRD 5.2)",
                             "andere": "Gitter (V-5b UNBELEGT), keine Quelle"},
           "oi_attenuation": att, "designs": out_designs, "bilanz_reproduction": repro,
           "c_bind_iid_reference": iid,
           "rezenz_geometry": {"last_judged_day": "2026-06-28", "nuisance_end": "2024-05-31",
                               "data_start_eth_1min": "2021-03-15",
                               "max_years_per_window_without_nuisance_overlap": (LAST_JUDGED - NUIS_END) / 2,
                               "max_years_per_window_with_all_1min_data": (LAST_JUDGED - DATA_START_ETH) / 2}}
    c.check_out(res)
    return res


if __name__ == "__main__":
    r = main()
    print("sha256", c.dump(r, c.WORK / "a2v_power.json"))
