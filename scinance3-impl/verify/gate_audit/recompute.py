import json, math, sys
d = json.load(open(sys.argv[1]))
for wn in ("W1", "W2"):
    w = d["windows"][wn]
    nf = w["noise_floor_and_threshold"]
    e_floor = nf["floor"]["e_floor"]; wj = nf["w_judged"]
    pnc = w["selection_ceiling_measured"]["ceiling_ic_mean"]
    pnc_sd = w["selection_ceiling_measured"]["ceiling_ic_sd"]
    nrep_pnc = w["selection_ceiling_measured"]["n_replicates"]
    mb = 0.25 * e_floor / math.sqrt(wj); cb = 1.5 * pnc
    dec = w["beta_control_decision"]
    print(f"=== {wn}: e_floor={e_floor:.6f} W_judged={wj} null_mean_bound={mb:.6f} (json {dec['null_mean_bound']:.6f}) "
          f"pure_noise_ceiling={pnc:.6f} sd={pnc_sd:.6f} n={nrep_pnc} se={pnc_sd/math.sqrt(nrep_pnc):.6f} ceiling_bound={cb:.6f} (json {dec['ceiling_bound']:.6f})")
    st = w["beta_control_method_study"]
    print("study n_reps", st["n_reps"], "seed", st["seed"], "stress_mult", st["stress_multiplier"], "sigma_f", st["sigma_f"], "sigma_e", st["sigma_e_used"])
    for cal in ("measured", "stress", "zero"):
        c = st["calibrations"][cal]
        print(f" -- {cal}: rho_f={c['rho_f']:.5f} beta_sd={c['beta_sd_calibrated']:.5f} target={c['target_factor_share']:.5f} mask_k_med={c.get('calibration_mask_k_median')}")
        for m in st["methods"]:
            mm = c["methods"][m]
            vs = mm["variants"]
            worst_v = max(vs, key=lambda v: abs(vs[v]["mean_ic_draws_mean"]))
            x = vs[worst_v]
            se = x["mean_ic_draws_sd"]/math.sqrt(x["n_reps_finite"])
            excess = (abs(x["mean_ic_draws_mean"]) - mb)/se
            print(f"    {m:16s} worst={worst_v:8s} mean={x['mean_ic_draws_mean']:+.5f} sd={x['mean_ic_draws_sd']:.5f} n={x['n_reps_finite']} se={se:.5f} (|m|-bound)/se={excess:+.2f}  ceiling={mm['ceiling_mean_of_max']:.5f} ceil-bound={mm['ceiling_mean_of_max']-cb:+.5f} beta_sd={mm.get('beta_sd')} rho={mm.get('rho_f'):.4f} cov={mm.get('coverage_mean')}")
    for r in dec["rows"]:
        print("   ROW", r["method"], "meas", round(r["measured"]["worst_abs_null_mean"],5), r["measured"]["null_mean_ok"], round(r["measured"]["ceiling"],5), r["measured"]["ceiling_ok"],
              "stress", round(r["stress"]["worst_abs_null_mean"],5), r["stress"]["null_mean_ok"], round(r["stress"]["ceiling"],5), r["stress"]["ceiling_ok"], "PASS", r["pass"])
    print("  passing", dec["passing_methods"], dec["note"])
