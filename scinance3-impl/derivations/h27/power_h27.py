"""H-27 power, window length L (DEC-96 E2) and regime assignment (DEC-94 via power_p1).

Reference configuration (FEASIBILITY.md P-9, fixed before any nuisance number): statistic S1
(vol points, mean over the window's IV days of IV - RV_fwd30 minus the null-world J), leg BTC,
SE_W = max(SD * sqrt(c_bind / n_W), SE_null(n_W)), prior pi-2 central (constant relative premium
ln(IV/RV) = 0.1431 from L-1) evaluated at the pre-period RV level sigma_n.
Windows W3/W4 from 2026-07-01, L in {6, 9, 12} months, IV days = all calendar days of the window,
RV target up to 30 days after the window end.  L = the smallest L with regime C10 or DEC52.
Everything else is report.  Reads nuisance.json and nullworld.json; writes power.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1 as pp  # noqa: E402

V_LIT = 0.14
LOG_CENTRAL, LOG_LO, LOG_HI = 0.1431, 0.1077, 0.2012
WINDOWS = {6: (184, 181), 9: (274, 275), 12: (365, 366)}
WIN_DATES = {6: ("2026-07-01..2026-12-31", "2027-01-01..2027-06-30"),
             9: ("2026-07-01..2027-03-31", "2027-04-01..2027-12-31"),
             12: ("2026-07-01..2027-06-30", "2027-07-01..2028-06-30")}


def priors(unit: str, sigma: float) -> dict[str, float]:
    """Prior per convention, net of the structural null, in the unit of the statistic."""
    def from_log(l):
        if unit == "S1":
            return 100 * sigma * (math.exp(l) - 1)
        if unit == "S2":
            return 100 * sigma * sigma * (math.exp(2 * l) - 1)
        return l
    pi1 = {"S1": 100 * (math.sqrt(sigma ** 2 + V_LIT) - sigma), "S2": 100 * V_LIT,
           "S3": 0.5 * math.log((sigma ** 2 + V_LIT) / sigma ** 2)}[unit]
    return {"pi2_central": from_log(LOG_CENTRAL), "pi2_low": from_log(LOG_LO),
            "pi2_high": from_log(LOG_HI), "pi1": pi1}


def se_window(nu: dict, nw: dict, unit: str, n: int, sym_null: str, c_override: float | None = None) -> dict:
    sd, c = nu[unit]["sd"], (nu[unit]["c_bind"] if c_override is None else c_override)
    se_nuis = sd * math.sqrt(c / n)
    # null-world SE expressed at the pre-period level sigma_ref (level-normalised, nullworld.py)
    se_null = nw[sym_null]["windows"][str(n)][unit]["se_null_at_ref"]
    return {"se_nuis": se_nuis, "se_null": se_null, "se": max(se_nuis, se_null),
            "binding_source": "nuisance" if se_nuis >= se_null else "null_world"}


def evaluate(prior: float, ses: list[float]) -> dict:
    p1 = pp.assign_regime([prior, prior], ses, exact_report=True)
    a3 = pp.assign_regime_a3_practice([prior, prior], ses)
    return {"regime_p1": p1["regime"], "reason_p1": p1["reason"],
            "window_power": p1["window_power"], "mde80": p1["mde80"],
            "gate_power_product": p1["gate_power_product"], "gate_power_exact": p1["gate_power_exact"],
            "gate_mde80": p1["gate"]["mde80_gate"] if p1["gate"] else None,
            "regime_a3": a3["regime"], "a3_window_power": a3["window_power"], "a3_mde80": a3["mde80"],
            "a3_gate_power_product": a3["gate_power_product"],
            "zugelassen_nur_durch_dec94": a3["zugelassen_nur_durch_dec94"]}


def main() -> None:
    nuis = json.loads((HERE / "nuisance.json").read_text())
    null = json.loads((HERE / "nullworld.json").read_text())
    sig = {s: nuis[f"rv_level_{s}"]["sigma_n_rms"] for s in ("BTC", "ETH")}
    sig["LEG_MEAN"] = 0.5 * (sig["BTC"] + sig["ETH"])
    out: dict = {"sigma_n_rms": sig, "z_krit": pp.z_krit(0.05), "configs": {}}
    configs = []
    for leg in ("BTC", "ETH", "LEG_MEAN"):
        for unit in ("S1", "S2", "S3"):
            configs.append((leg, unit))
    for leg, unit in configs:
        nu = nuis[leg]
        sym_null = "BTC" if leg in ("BTC", "LEG_MEAN") else "ETH"
        if leg == "LEG_MEAN":   # leg prior = mean of the symbol priors (ETH prior = same relative premium: UNBELEGT)
            pb, pe = priors(unit, sig["BTC"]), priors(unit, sig["ETH"])
            pr = {k: 0.5 * (pb[k] + pe[k]) for k in pb}
        else:
            pr = priors(unit, sig[leg])
        J = null[sym_null]["windows"]["365"][unit]["J"]
        res = {"J_365": J, "priors": pr, "L": {}}
        for L, (n3, n4) in WINDOWS.items():
            s3 = se_window(nu, null, unit, n3, sym_null)
            s4 = se_window(nu, null, unit, n4, sym_null)
            row = {"windows": WIN_DATES[L], "n_days": [n3, n4], "se": [s3, s4]}
            for pname, pval in pr.items():
                row[pname] = evaluate(pval, [s3["se"], s4["se"]])
            # monthly non-overlapping variant (report)
            m = nu[unit]["monthly"]
            se_m = m["sd_m"] * math.sqrt(m["c_bind_m"] / L)
            row["monthly_variant"] = {"se": se_m, "pi2_central": evaluate(pr["pi2_central"], [se_m, se_m])}
            # adjacent-window correlation (report): pooled SE inflation for the DEC-52 gate
            rho = nu[unit]["adjacent_window_corr"][str(n3)]
            se_p_indep = math.sqrt(s3["se"] ** 2 + s4["se"] ** 2) / 2
            se_p_corr = math.sqrt(s3["se"] ** 2 + s4["se"] ** 2 + 2 * rho * s3["se"] * s4["se"]) / 2
            t_p = pp.Z_KRIT_POOLED_DEC52 * se_p_corr
            pooled_corr = pp.condition_power(pr["pi2_central"], t_p, se_p_corr)
            screens = [pp.condition_power(pr["pi2_central"], 0.5 * t_p, s["se"]) for s in (s3, s4)]
            row["dec52_with_adjacent_corr"] = {
                "rho_adjacent": rho, "se_pooled_indep": se_p_indep, "se_pooled_corr": se_p_corr,
                "gate_power_product_corr": pooled_corr * screens[0] * screens[1]}
            # fork report: c from Bartlett 60/90/120 only (batch means excluded) -> testability direction
            c_b = max(1.0, *[nu[unit]["c_bartlett"][b] for b in ("60", "90", "120")])
            sb3 = se_window(nu, null, unit, n3, sym_null, c_b)
            sb4 = se_window(nu, null, unit, n4, sym_null, c_b)
            row["c_bartlett_only"] = {"c": c_b, "se": [sb3["se"], sb4["se"]],
                                      **{pn: evaluate(pv, [sb3["se"], sb4["se"]]) for pn, pv in pr.items()}}
            res["L"][str(L)] = row
        # report: window length (days, both windows equal) needed at the central prior
        sd, c = nu[unit]["sd"], nu[unit]["c_bind"]
        n_c10 = (pp.mde_factor(0.05) * sd * math.sqrt(c) / pr["pi2_central"]) ** 2
        lo, hi = 2.0, 20000.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            se = sd * math.sqrt(c / mid)
            g = pp.dec52_gate_power([pr["pi2_central"]] * 2, [se, se])["power_product"]
            lo, hi = (mid, hi) if g < 0.8 else (lo, mid)
        res["days_needed_pi2_central"] = {"C10": n_c10, "DEC52_gate": hi,
                                          "note": "SE = SD * sqrt(c_bind / n), nuisance source only"}
        out["configs"][f"{leg}/{unit}"] = res
    ref = out["configs"]["BTC/S1"]["L"]
    chosen = None
    for L in (6, 9, 12):
        if ref[str(L)]["pi2_central"]["regime_p1"] in ("C10", "DEC52"):
            chosen = L
            break
    out["reference"] = {"config": "BTC/S1, pi2_central, SE = max(nuisance, null)",
                        "L_chosen": chosen,
                        "regimes": {L: ref[str(L)]["pi2_central"]["regime_p1"] for L in (6, 9, 12)},
                        "regimes_a3": {L: ref[str(L)]["pi2_central"]["regime_a3"] for L in (6, 9, 12)}}
    # L under each prior/leg/unit (report: fork directions)
    summary = {}
    for key, res in out["configs"].items():
        for pname in ("pi2_central", "pi2_low", "pi2_high", "pi1"):
            Ls = [L for L in (6, 9, 12) if res["L"][str(L)][pname]["regime_p1"] in ("C10", "DEC52")]
            Ls_a3 = [L for L in (6, 9, 12) if res["L"][str(L)][pname]["regime_a3"] in ("C10", "DEC52")]
            Lb = [L for L in (6, 9, 12) if res["L"][str(L)]["c_bartlett_only"][pname]["regime_p1"] in ("C10", "DEC52")]
            Lm = [L for L in (6, 9, 12) if res["L"][str(L)]["monthly_variant"]["pi2_central"]["regime_p1"] in ("C10", "DEC52")] if pname == "pi2_central" else None
            summary[f"{key} {pname}"] = {"L_p1": Ls[0] if Ls else None,
                                         "L_a3": Ls_a3[0] if Ls_a3 else None,
                                         "L_p1_c_bartlett_only": Lb[0] if Lb else None,
                                         "L_p1_monthly": (Lm[0] if Lm else None) if Lm is not None else "n/a"}
    out["L_summary"] = summary
    (HERE / "power.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["reference"], indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
