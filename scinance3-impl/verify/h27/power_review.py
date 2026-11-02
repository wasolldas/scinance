"""H-27 review, check points 2 and 3: prior conversion and power / assignment with power_p1.

Recomputes (i) the prior conversion of BVRP 0.14 (variance units) into vol / log units,
(ii) the reference assignment for L = 6/9/12 with the derivation's SE inputs and with the
review's own nuisance / null-world numbers, plus the A3-practice double statement,
(iii) sensitivity rows (direction stated): c consensus, prior at the vol mean instead of the rms,
noise-free RV scenario (check point 4), S3, monthly variant, selection K.
Reads nuisance_review.json, nullworld_review.json, noise_share.json (review) -- no data access.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1 as pp  # noqa: E402

V = 0.14
WIN = {6: (184, 181), 9: (274, 275), 12: (365, 366)}


def conv(iv: float) -> dict:
    rv = math.sqrt(iv * iv - V)
    ell = math.log(iv / rv)
    return {"iv": iv, "rv": rv, "vol_premium_volpts_at_lit": 100 * (iv - rv), "log_premium": ell}


def prior_s1(sigma: float, ell: float) -> float:
    return 100 * sigma * (math.exp(ell) - 1)


def assign(prior: float, se3: float, se4: float, exact: bool = False) -> dict:
    p1 = pp.assign_regime([prior, prior], [se3, se4], exact_report=exact)
    a3 = pp.assign_regime_a3_practice([prior, prior], [se3, se4])
    return {"p1": p1["regime"], "power": [round(x, 3) for x in p1["window_power"]],
            "gate_prod": round(p1["gate_power_product"], 3),
            "gate_exact": None if p1["gate_power_exact"] is None else round(p1["gate_power_exact"], 3),
            "mde80": [round(x, 2) for x in p1["mde80"]], "gate_mde80": round(p1["gate"]["mde80_gate"], 2),
            "a3": a3["regime"], "a3_power": [round(x, 3) for x in a3["window_power"]],
            "a3_gate_prod": round(a3["gate_power_product"], 3), "nur_dec94": a3["zugelassen_nur_durch_dec94"]}


def interp_null(se_null: dict, n: int) -> float:
    """SE_null for n by the 1/sqrt(n) law anchored at the nearest computed n."""
    keys = sorted(int(k) for k in se_null)
    k = min(keys, key=lambda m: abs(m - n))
    return se_null[str(k)] * math.sqrt(k / n)


def table(prior: float, sd: float, c: float, se_null: dict | None, exact: bool = False) -> dict:
    rows = {}
    for L, (n3, n4) in WIN.items():
        s = []
        for n in (n3, n4):
            se = sd * math.sqrt(c / n)
            if se_null:
                se = max(se, interp_null(se_null, n))
            s.append(se)
        rows[str(L)] = {"se": [round(x, 3) for x in s], **assign(prior, s[0], s[1], exact)}
    return rows


def days_needed(prior: float, sd: float, c: float) -> float:
    return (pp.mde_factor(0.05) * sd * math.sqrt(c) / prior) ** 2


def main() -> None:
    nu = json.loads((HERE / "nuisance_review.json").read_text())
    nw = json.loads((HERE / "nullworld_review.json").read_text())
    ns = json.loads((HERE / "noise_share.json").read_text())
    out: dict = {}
    # (i) prior
    out["prior_conversion"] = {str(iv): conv(iv) for iv in (0.65, 0.75, 0.85)}
    sig_rms = nu["BTC/cc"]["rv_rms"]
    ratio = nu["BTC/cc"]["ratio_rvmean_to_rvrms"]
    ell = {k: out["prior_conversion"][k]["log_premium"] for k in ("0.65", "0.75", "0.85")}
    out["prior_S1_at_rms"] = {k: prior_s1(sig_rms, v) for k, v in ell.items()}
    out["prior_S1_pi1_at_rms"] = 100 * (math.sqrt(sig_rms ** 2 + V) - sig_rms)
    out["prior_S1_at_volmean"] = {k: prior_s1(sig_rms * ratio, v) for k, v in ell.items()}
    p_c = out["prior_S1_at_rms"]["0.75"]
    # derivation inputs
    sd_d, c_d = 18.60, 28.17
    null_d = {"184": 5.64, "274": 4.65, "365": 4.17}
    out["ref_derivation_inputs"] = table(p_c, sd_d, c_d, null_d, exact=True)
    # review inputs
    sd_r = nu["BTC/cc"]["S1"]["sd"]
    c_r = nu["BTC/cc"]["S1"]["c_rule_P3_max6"]
    sv = nw["SV"]["phi0.996_eta0.06_nu4.5"]
    null_r = {n: sv[n]["rv_cc/S1"]["se_null_at_ref"] for n in ("184", "274", "365")}
    out["ref_review_inputs"] = table(p_c, sd_r, c_r, null_r, exact=True)
    # sensitivity rows
    c_cons = nu["mc_rule_bias_BTC_S1_cc"]["c_true_longrun"]          # tapered-ACF long-run c
    out["sens"] = {
        "c_consensus_18.6 (Testbarkeit)": table(p_c, sd_r, c_cons, null_r),
        "c_consensus_nullworld_off (Testbarkeit, nur Nuisance)": table(p_c, sd_r, c_cons, None),
        "prior_at_volmean (Strenge)": table(out["prior_S1_at_volmean"]["0.75"], sd_r, c_r, null_r),
        "prior_band_hi_13.72 (Testbarkeit)": table(out["prior_S1_at_rms"]["0.65"], sd_r, c_r, null_r),
        "prior_band_lo_7.00 (Strenge)": table(out["prior_S1_at_rms"]["0.85"], sd_r, c_r, null_r),
        "pi1_10.48 (Testbarkeit)": table(out["prior_S1_pi1_at_rms"], sd_r, c_r, null_r),
    }
    # check point 4: noise-free RV (ideal intraday estimator), SD from noise_share (delta method)
    sd_nf = ns["BTC"]["sd_premium_S1_if_noise_free"]
    null_nf = {n: sv[n]["qv_noisefree/S1"]["se_null_at_ref"] for n in ("184", "274", "365")}
    out["cp4_noise_free_rv"] = {
        "sd_noise_free": sd_nf,
        "c_rule_28.2": table(p_c, sd_nf, c_r, null_nf),
        "c_consensus_18.6": table(p_c, sd_nf, c_cons, null_nf),
    }
    # S3 (log, level-free) with the derivation's binding rule and review numbers
    s3 = nu["BTC/cc"]["S3"]
    null_s3 = {n: sv[n]["rv_cc/S3"]["se_null_at_ref"] for n in ("184", "274", "365")}
    out["S3_rule"] = table(ell["0.75"], s3["sd"], s3["c_rule_P3_max6"], null_s3)
    # monthly variant (c_m = 1 because ACF1 < 0, DEC-94 (4) no credit)
    m = nu["BTC/cc"]["S1"]["monthly"]
    out["monthly"] = {str(L): assign(p_c, m["sd_m"] / math.sqrt(L), m["sd_m"] / math.sqrt(L)) | {
        "se": round(m["sd_m"] / math.sqrt(L), 3)} for L in (6, 9, 12)}
    # days needed (nuisance only)
    out["days_needed_C10"] = {"rule_c": days_needed(p_c, sd_r, c_r), "c_consensus": days_needed(p_c, sd_r, c_cons),
                              "noise_free_c_consensus": days_needed(p_c, sd_nf, c_cons)}
    out["selection_z"] = {str(K): pp.selection_z(K) for K in (3, 6, 9, 12, 18)}
    (HERE / "power_review.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
