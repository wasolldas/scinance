"""A1 Stufe 1 -- prem_prior grid, SE of the registered test, power, assignment rule (PRD 5.1 / DEC-52)
and the GL-012 check. Reads ONLY the three intermediate JSONs (window census = formation-side,
nuisance = dispersion + persistence ratio, formation sensitivities) -- no panel access here.

Rules fixed BEFORE this script was run (FEASIBILITY.md section 4 states them verbatim):
  * sigma_W (weekly SD of the A1 total return D1 minus EW universe) binding = MAX over
    P1 direct nuisance SD (K >= 117 base), P2 kappa_total x PIT model (EW factor), P3 kappa_total x
    PIT model (BTC factor), P4 idiosyncratic-scaled nuisance variance + PIT factor term (EW).
  * long-run variance factor c binding = max(1, measured) -> c = 1 when the measured total-return
    autocorrelation is negative (no credit for negative autocorrelation); DEC-67 E4 (W_eff = 0.41 W)
    and the measured MBB ratio are reported as variants.
  * SE binding = max(SE of the mean test, SE of the residual-alpha test vs MOM1/REV).
  * W = 52 per window (task), pooled 104.
"""
from __future__ import annotations

import json
import math
import sys

sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")

from scipy.stats import norm  # noqa: E402

import a1_common as C  # noqa: E402

Z_A05, Z_A01 = 1.6449, 2.3263
Z_W, Z_POOL = 2.4865, 3.1680
W, W_POOL = 52, 104
THETAS = (0.25, 0.5, 1.0)


def load(name):
    return json.loads((C.WORK / name).read_text(encoding="utf-8"))


def assess(sig, c, prem, r2_alpha=None, n_reg=2):
    """Per-window and pooled power arithmetic for one (sigma, c, prem) configuration."""
    out = {}
    se = {}
    for wn in ("W1", "W2"):
        se_mean = sig[wn] * math.sqrt(c) / math.sqrt(W)
        se_alpha = (sig[wn] * math.sqrt(1 - r2_alpha) * math.sqrt(c) / math.sqrt(W) * math.sqrt(W / (W - n_reg - 1))
                    if r2_alpha is not None else se_mean)
        se[wn] = max(se_mean, se_alpha)
        p = norm.cdf(prem[wn] / se[wn] - Z_A05)
        out[wn] = {"sigma_bp": sig[wn] * 1e4, "se_mean_bp": se_mean * 1e4, "se_alpha_bp": se_alpha * 1e4,
                   "se_bp": se[wn] * 1e4, "prem_bp": prem[wn] * 1e4, "P_fenster": float(p),
                   "regime": "C10_hart" if p >= 0.60 else "DEC52",
                   "mde80_bp": Z_W * se[wn] * 1e4, "dec51_2_ok": bool(prem[wn] >= Z_W * se[wn]),
                   # power of a gate whose THRESHOLD is z*SE with z = 2.4865 (PRD 5.1 "Schwelle" text,
                   # A3 convention IC_min): Phi(prem/SE - 2.4865); MDE80 of that gate = 3.3281*SE
                   "P_gate_threshold_2_4865": float(norm.cdf(prem[wn] / se[wn] - Z_W)),
                   "mde80_gate_threshold_2_4865_bp": (Z_W + 0.8416) * se[wn] * 1e4}
    sig_pool = math.sqrt((sig["W1"] ** 2 + sig["W2"] ** 2) / 2)
    se_pool = math.sqrt(se["W1"] ** 2 + se["W2"] ** 2) / 2.0   # SE of (mean_W1 + mean_W2) / 2
    prem_pool = (prem["W1"] + prem["W2"]) / 2
    gl012 = Z_POOL * se_pool > prem_pool
    # DEC-52 branch (approximate): screens (ii) per window at 0.5 x registered threshold
    thr = Z_POOL * se_pool                      # z of the DEC-52 regime x pooled SE (PRD 5.1 Schwelle)
    p_screen = {wn: float(norm.cdf((prem[wn] - 0.5 * thr) / se[wn])) for wn in ("W1", "W2")}
    p_pool = float(norm.cdf(prem_pool / se_pool - Z_A01))
    out["pooled"] = {"sigma_pooled_bp": sig_pool * 1e4, "se_pooled_bp": se_pool * 1e4,
                     "prem_pooled_bp": prem_pool * 1e4, "gl012_bound_bp": Z_POOL * se_pool * 1e4,
                     "GL012": bool(gl012), "P_pooled_alpha001": p_pool,
                     "P_dec52_screens": p_screen,
                     "P_dec52_approx_product": p_pool * p_screen["W1"] * p_screen["W2"],
                     "P_pooled_gate_threshold_3_168": float(norm.cdf(prem_pool / se_pool - Z_POOL)),
                     # EV-4 option (a): DEC-52 with the pooled CRITICAL value 2.3263*SE_pooled as registered
                     # threshold; screens per window at 0.5 x that threshold (approximate product, independence)
                     "P_dec52_a_screens": {wn: float(norm.cdf((prem[wn] - 0.5 * Z_A01 * se_pool) / se[wn])) for wn in ("W1", "W2")},
                     "P_dec52_a_approx_product": p_pool * float(norm.cdf((prem["W1"] - 0.5 * Z_A01 * se_pool) / se["W1"]))
                                                 * float(norm.cdf((prem["W2"] - 0.5 * Z_A01 * se_pool) / se["W2"]))}
    out["P_C10_joint"] = out["W1"]["P_fenster"] * out["W2"]["P_fenster"]
    out["P_C10_joint_gate_threshold_2_4865"] = out["W1"]["P_gate_threshold_2_4865"] * out["W2"]["P_gate_threshold_2_4865"]
    # theta_min (prem scales linearly with theta): smallest theta passing each criterion
    return out, se, se_pool, prem_pool


def main():
    wc, nu, fs = (load(f"window_census{C.SUFFIX}.json"), load(f"nuisance{C.SUFFIX}.json"),
                  load(f"formation_sensitivity{C.SUFFIX}.json"))
    base = nu["bases"]["K_ge_117"]
    var_x = base["total"]["sd"] ** 2
    cal_ew, cal_btc = base["pit_model_calibration"]["ew"], base["pit_model_calibration"]["btc"]
    realized_factor_var_ew = base["market_regression"]["total_on_ew"]["r2"] * var_x
    kappa_idio = (var_x - realized_factor_var_ew) / cal_ew["idio_var_mean"]
    sig = {}
    proj = {}
    for wn in ("W1", "W2"):
        pm = wc["windows"][wn]["pit_beta_model"]
        p1 = base["total"]["sd"]
        p2 = math.sqrt(cal_ew["kappa_total"] * pm["ew"]["pred_var_mean"])
        p3 = math.sqrt(cal_btc["kappa_total"] * pm["btc"]["pred_var_mean"])
        p4 = math.sqrt(kappa_idio * pm["ew"]["idio_var_mean"] + pm["ew"]["factor_var_mean"])
        proj[wn] = {"P1_direct_nuisance_bp": p1 * 1e4, "P2_kappa_pit_ew_bp": p2 * 1e4, "P3_kappa_pit_btc_bp": p3 * 1e4,
                    "P4_idio_scaled_plus_pit_factor_ew_bp": p4 * 1e4}
        sig[wn] = max(p1, p2, p3, p4)
        proj[wn]["binding_bp"] = sig[wn] * 1e4
    phi = base["persistence"]["phi_funding_leg_ratio_of_sums"]
    spread = {wn: wc["windows"][wn]["spread_bp_per_week"]["mean"] / 1e4 for wn in ("W1", "W2")}
    tot = base["total"]
    c_meas = max(tot["c_lrv_trunc4"], tot["c_lrv_bartlett4"], tot["mbb_variance_ratio"])
    c_opts = {"c1_binding": max(1.0, c_meas), "c_mbb_measured": tot["mbb_variance_ratio"],
              "c_dec67_E4": 1.0 / 0.41}
    r2a = base["a3_factor_regression"]["total_on_mom1_rev"]["r2"]
    res = {"inputs": {"phi": phi, "spread_mean_bp": {k: v * 1e4 for k, v in spread.items()},
                      "sigma_projections": proj, "kappa_idio": kappa_idio, "c_options": c_opts,
                      "r2_alpha_mom1_rev": r2a, "W": W, "W_pool": W_POOL},
           "grid": {}}
    for cname, c in c_opts.items():
        for th in THETAS:
            prem = {wn: spread[wn] * phi * th for wn in ("W1", "W2")}
            a, se, se_pool, prem_pool = assess(sig, c, prem, r2_alpha=r2a)
            res["grid"][f"{cname}|theta={th}"] = a
        # theta_min per criterion for this c
        prem1 = {wn: spread[wn] * phi for wn in ("W1", "W2")}
        a1, se, se_pool, prem_pool1 = assess(sig, c, prem1, r2_alpha=r2a)
        tm = {"GL012_pooled": Z_POOL * se_pool / prem_pool1}
        for wn in ("W1", "W2"):
            tm[f"P_fenster_ge_0.60_{wn}"] = (Z_A05 + norm.ppf(0.60)) * se[wn] / prem1[wn]
            tm[f"MDE80_{wn}"] = Z_W * se[wn] / prem1[wn]
            tm[f"P_gate_2_4865_ge_0.80_{wn}"] = (Z_W + 0.8416) * se[wn] / prem1[wn]
        res["grid"][f"{cname}|theta_min"] = tm
    # sensitivities at theta = 1 under the binding c
    sens = {}
    c = c_opts["c1_binding"]
    variants = {
        "phi_slope": ({wn: spread[wn] for wn in spread}, base["persistence"]["phi_funding_leg_slope_through_origin"]),
        "phi_median_weekly": ({wn: spread[wn] for wn in spread}, base["persistence"]["phi_funding_leg_median_weekly_ratio"]),
        "W2_spread_excl_any_1h": ({"W1": spread["W1"], "W2": fs["sets"]["W2"]["spread_bp"]["excl_any_1h_day"]["mean"] / 1e4}, phi),
        "spread_median_instead_of_mean": ({wn: wc["windows"][wn]["spread_bp_per_week"]["q050"] / 1e4 for wn in spread}, phi),
    }
    for name, (spr, ph) in variants.items():
        prem = {wn: spr[wn] * ph for wn in spr}
        sens[name] = assess(sig, c, prem, r2_alpha=r2a)[0]
    # psi- and key-ts-autocorr-scaled persistence (window-specific phi), formation-side proxies
    psi_n = fs["sets"]["nuisance_K_ge_117"]["psi_within_week"]["ratio_of_sums"]
    ac_n = fs["sets"]["nuisance_K_ge_117"]["key_ts_autocorr"]["median_symbol_lag1"]
    for name, getter, ref in (("phi_scaled_by_psi", lambda wn: fs["sets"][wn]["psi_within_week"]["ratio_of_sums"], psi_n),
                              ("phi_scaled_by_key_ts_autocorr", lambda wn: fs["sets"][wn]["key_ts_autocorr"]["median_symbol_lag1"], ac_n)):
        prem = {wn: spread[wn] * phi * getter(wn) / ref for wn in ("W1", "W2")}
        sens[name] = assess(sig, c, prem, r2_alpha=r2a)[0]
        sens[name]["phi_used"] = {wn: phi * getter(wn) / ref for wn in ("W1", "W2")}
    # sigma alternatives at theta = 1
    blk = max(b["sd_bp"] for b in base["sd_by_52w_block"]) / 1e4
    for name, s_alt in (("sigma_max_52w_block_K_ge_117", {"W1": blk, "W2": blk}),
                        ("sigma_all_K_ge_10_base", {"W1": nu["bases"]["all_K_ge_10"]["total"]["sd"],
                                                    "W2": nu["bases"]["all_K_ge_10"]["total"]["sd"]})):
        prem = {wn: spread[wn] * phi for wn in ("W1", "W2")}
        sens[name] = assess(s_alt, c, prem, r2_alpha=r2a)[0]
    res["sensitivities_theta1_c_binding"] = sens
    (C.WORK / f"power{C.SUFFIX}.json").write_text(json.dumps({"fingerprint": wc["fingerprint"], "config": "B_excl1h" if C.EXCL_1H else "A_dec70_1h_included", **res}, indent=1, default=float),
                                           encoding="utf-8")
    print(json.dumps(res["inputs"], indent=1))
    for k, v in res["grid"].items():
        if k.endswith("theta_min"):
            print(k, {a: round(b, 3) for a, b in v.items()})
        else:
            print(k, "W1 P=%.3f %s SE=%.1f prem=%.1f | W2 P=%.3f %s SE=%.1f prem=%.1f | pooled bound=%.1f prem=%.1f GL012=%s joint=%.3f dec52=%.3f" % (
                v["W1"]["P_fenster"], v["W1"]["regime"], v["W1"]["se_bp"], v["W1"]["prem_bp"],
                v["W2"]["P_fenster"], v["W2"]["regime"], v["W2"]["se_bp"], v["W2"]["prem_bp"],
                v["pooled"]["gl012_bound_bp"], v["pooled"]["prem_pooled_bp"], v["pooled"]["GL012"], v["P_C10_joint"],
                v["pooled"]["P_dec52_approx_product"]))
            print("    gate(thr 2.4865 SE): W1 %.3f W2 %.3f joint %.3f | pooled gate(thr 3.168) %.3f" % (
                v["W1"]["P_gate_threshold_2_4865"], v["W2"]["P_gate_threshold_2_4865"],
                v["P_C10_joint_gate_threshold_2_4865"], v["pooled"]["P_pooled_gate_threshold_3_168"]))
    for k, v in sens.items():
        print("SENS", k, "W1 P=%.3f %s prem=%.1f | W2 P=%.3f %s prem=%.1f | bound=%.1f prem=%.1f GL012=%s" % (
            v["W1"]["P_fenster"], v["W1"]["regime"], v["W1"]["prem_bp"], v["W2"]["P_fenster"], v["W2"]["regime"],
            v["W2"]["prem_bp"], v["pooled"]["gl012_bound_bp"], v["pooled"]["prem_pooled_bp"], v["pooled"]["GL012"]))


if __name__ == "__main__":
    main()
