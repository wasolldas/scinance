"""Compare review numbers against the derivation JSON (relative deviation, flag > 1 %)."""
import json
R = json.load(open("review_hfrv.json"))
A = json.load(open("/home/user/scinance/scinance3-impl/state/herleitung_hfrv/nuisance_hfrv.json"))
VARS = ("v1_1min", "v2_5min", "v3_5min_sub", "v4_15min", "v5_30min", "v6_cc")
rows = []
def cmp(name, a, r):
    if a is None or r is None:
        rows.append((name, a, r, None)); return
    dev = (r - a) / a if a != 0 else float("nan")
    rows.append((name, a, r, dev))
for v in VARS:
    ra = R["symbols"]["BTC"]["variants"][v]; aa = A["stats"]["BTC"][v]["S1"]
    cmp(f"BTC {v} SD S1", aa["sd"], ra["S1"]["sd"])
    for k in ("1", "10", "20", "30", "60", "120", "180"):
        cmp(f"BTC {v} ACF{k}", aa["acf_out"][k], ra["S1"]["acf"][k])
    for B in ("60", "90", "120"):
        cmp(f"BTC {v} Bartlett{B}", aa["c_bartlett"][B], ra["S1"]["c_bartlett"][B])
        cmp(f"BTC {v} BM{B}", aa["c_batch_means"][B], ra["S1"]["c_bm_head"][B])
    cmp(f"BTC {v} c_rule", aa["c_bind"], ra["S1"]["c_rule_P3"])
    cmp(f"BTC {v} c_consensus", aa["c_consensus_tapered_acf"], ra["S1"]["c_consensus_tapered"])
    for mb in ("30", "60", "90"):
        cmp(f"BTC {v} statboot{mb}", aa["c_stationary_bootstrap"][mb], ra["S1"]["c_stat_bootstrap"][mb])
    cmp(f"BTC {v} kurt", aa["excess_kurtosis"], ra["S1"]["excess_kurtosis"])
    cmp(f"BTC {v} first_lag<0.1", aa["first_lag_acf_below_0_10"], ra["S1"]["first_lag_below_0_10"])
    cmp(f"BTC {v} SD S3", A["stats"]["BTC"][v]["S3"]["sd"], ra["S3_sd"])
    cmp(f"BTC {v} SD S2", A["stats"]["BTC"][v]["S2"]["sd"], ra["S2_sd"])
    cmp(f"BTC {v} c_rule S3", A["stats"]["BTC"][v]["S3"]["c_bind"], ra["S3_c_rule"])
    cmp(f"BTC {v} rms", A["rv_level"]["BTC"][v]["rms_rv_fwd30"] * 100, ra["rms_rv30_pct"])
    cmp(f"BTC {v} ratio30", A["rv_level"]["BTC"][v]["ratio_rms_to_30min"], ra["ratio_rms_30min"])
    cmp(f"BTC {v} kappa", A["kappa_rv_day"]["BTC"][v]["kappa_L2_3_5_review"], ra["kappa_L235"])
    cmp(f"BTC {v} noiseSD", A["kappa_rv_day"]["BTC"][v]["sd_noise_volpts_delta"], ra["noise_sd_delta_volpts"])
    if v != "v6_cc":
        dd = A["decomposition_P_cc_eq_P_v_plus_D"]["BTC"][v]
        cmp(f"BTC {v} sd_D", dd["sd_D_volpts"], ra["sd_D"])
        cmp(f"BTC {v} corr_D_P", dd["corr_D_with_P_v_S1"], ra["corr_D_P_v"])
    re_ = R["symbols"]["ETH"]["variants"][v]; ae = A["stats"]["ETH"][v]["S1"]
    cmp(f"ETH {v} SD S1", ae["sd"], re_["S1"]["sd"])
    cmp(f"ETH {v} c_rule", ae["c_bind"], re_["S1"]["c_rule_P3"])
    cmp(f"ETH {v} ratio30", A["rv_level"]["ETH"][v]["ratio_rms_to_30min"], re_["ratio_rms_30min"])
    cmp(f"corr BTC/ETH S1 {v}", A["correlations"]["pearson_btc_eth"][v]["S1"], R["corr_btc_eth_S1"][v])
    # power
    pa = A["power"]["BTC_S1"][v]; pr = R["power_BTC_S1"][v]
    for ca, cr in (("c_rule_P3", "c_rule"), ("c_consensus_measured", "c_consensus"), ("c_consensus_review_18_6", "c_review_18_6")):
        blk = pa[f"{ca}|se_null_h27"]
        for n in ("335", "365"):
            cmp(f"pow {v} {cr} n{n} SE", blk["windows_L12"]["pi2_central"][n]["se"], pr[cr][f"L12_n{n}"]["se"])
            cmp(f"pow {v} {cr} n{n} power", blk["windows_L12"]["pi2_central"][n]["window_power_p1"], pr[cr][f"L12_n{n}"]["power_p1"])
            if blk["windows_L12"]["pi2_central"][n]["regime_p1"] != pr[cr][f"L12_n{n}"]["regime_p1"]:
                rows.append((f"REGIME MISMATCH {v} {cr} {n}", None, None, None))
        d = blk["durations"]["pi2_central"]
        cmp(f"days {v} {cr} C10 P-1", d["days"]["c10_p1"], pr[cr]["days_pi2_central"]["c10_p1"])
        cmp(f"days {v} {cr} DEC52 P-1", d["days"]["dec52_gate_p1"], pr[cr]["days_pi2_central"]["dec52_gate_p1"])
        cmp(f"days {v} {cr} C10 A3", d["days"]["c10_a3"], pr[cr]["days_pi2_central"]["c10_a3"])
        if d["full_c10_p1"] != pr[cr]["days_pi2_central"]["full_c10_p1"] or d["full_c10_a3"] != pr[cr]["days_pi2_central"]["full_c10_a3"]:
            rows.append((f"DATE MISMATCH {v} {cr}", d["full_c10_p1"], pr[cr]["days_pi2_central"]["full_c10_p1"], None))
        d7 = blk["durations"]["dec98n2_pi2_7_14"]
        cmp(f"days {v} {cr} C10 P-1 prior 7.14", d7["days"]["c10_p1"], pr[cr]["days_pi2_7_14"]["c10_p1"])
bad = [r for r in rows if r[3] is None or abs(r[3]) > 0.01]
mx = max(abs(r[3]) for r in rows if r[3] is not None and r[3] == r[3])
print("n compared", len(rows), "max |rel dev|", mx)
for r in rows:
    if r[3] is None or abs(r[3]) > 0.002:
        print(r)
