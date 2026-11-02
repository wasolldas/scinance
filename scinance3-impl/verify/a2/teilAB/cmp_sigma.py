"""Compare review recomputation with the derivation's JSON (dispersion quantities only)."""
import json
me = json.load(open("rv_sigma.json"))
aj = json.load(open("/home/user/scinance/scinance3-impl/state/herleitung_a2/a2_vorarbeit.json"))
B = aj["teil_B_sigma30"]
rows = []
def cmp(name, mine, theirs):
    rel = (mine - theirs) / abs(theirs) if theirs else float("nan")
    rows.append((name, mine, theirs, rel))
print("meta", me["meta"]); print("class days", me["class_days"]); print("agent class days", B["class_day_counts"])
for k in ("FRI","FRI_W","FRI_M","FRI_Q","FRI_MQ","MODO","WE","NONFRI","ALL"):
    m = me["pre"][k]; a = B["dispersion"]["pre"][k]
    cmp(f"{k} n", m["n"], a["BTC"]["n"])
    cmp(f"{k} sd_btc", m["sd_btc"], a["BTC"]["sd"]); cmp(f"{k} sd_eth", m["sd_eth"], a["ETH"]["sd"])
    cmp(f"{k} sd_pooled", m["sd_pooled"], a["sigma_pooled"]); cmp(f"{k} sd_cluster", m["sd_cluster"], a["CLUSTER"]["sd"])
    cmp(f"{k} kurt_btc", m["kurt_excess_btc"], a["BTC"]["excess_kurtosis"])
    rr = B["rho_btc_eth"]["pre"][k]
    cmp(f"{k} rho_p", m["rho_pearson"], rr["pearson"]); cmp(f"{k} rho_s", m["rho_spearman"], rr["spearman"])
    if k in B["persistence"]["pre"]:
        p = B["persistence"]["pre"][k]["CLUSTER"]
        cmp(f"{k} c_bind", m["c_bind"], p["c_bind"])
        for j in (1, 2, 4):
            cmp(f"{k} acf{j}", m["acf_cluster"][j-1], p["acf"][str(j)])
        for Bw, v in m["c_bartlett_own"].items():
            cmp(f"{k} bartlett{Bw} own", v, p["c_bartlett"][Bw])
        for Bw, v in m["c_bartlett_power_p1"].items():
            cmp(f"{k} bartlett{Bw} p1", v, p["c_bartlett"][Bw])
        for L, v in m["c_bm"].items():
            if L in p["c_bm"]: cmp(f"{k} bm{L}", v, p["c_bm"][L])
    for y, v in m["sd_cluster_by_year"].items():
        if y in a["by_year"] and a["by_year"][y]["CLUSTER"].get("n", 0) >= 3:
            cmp(f"{k} sd_cluster {y}", v, a["by_year"][y]["CLUSTER"]["sd"])
o = me["other_series"]
cmp("fix1530 ALL sd_cluster", o["fix1530"]["ALL"]["sd_cluster"], B["dispersion"]["fix1530"]["ALL"]["CLUSTER"]["sd"])
cmp("fix1530 ALL c_bind", o["fix1530"]["ALL"]["c_bind"], B["persistence"]["fix1530"]["ALL"]["CLUSTER"]["c_bind"])
cmp("p3all ALL sd_cluster", o["p3all"]["ALL"]["sd_cluster"], B["dispersion"]["p3all_44slots"]["ALL"]["CLUSTER"]["sd"])
cmp("p3all ALL c_bind", o["p3all"]["ALL"]["c_bind"], B["persistence"]["p3all_44slots"]["ALL"]["CLUSTER"]["c_bind"])
cmp("pairdiff FRI sd", o["pairdiff_pre_minus_1530"]["FRI"]["sd_cluster"], B["dispersion"]["pre_minus_fix1530"]["FRI"]["CLUSTER"]["sd"])
cmp("pairdiff FRI c_bind", o["pairdiff_pre_minus_1530"]["FRI"]["c_bind"], B["persistence"]["pre_minus_fix1530"]["FRI"]["CLUSTER"]["c_bind"])
cmp("pre_oc ALL sd_cluster", o["pre_oc"]["ALL"]["sd_cluster"], B["dispersion"]["pre_oc"]["ALL"]["CLUSTER"]["sd"])
for k, v in me["pooled_ratio_bands_seed4711"].items():
    a = B["sd_ratios"][k]["POOLED"]
    print(f"band {k}: mine {v['point']:.4f} [{v['q025']:.3f}; {v['q975']:.3f}]  agent {a['ratio']:.4f} [{a['band']['q025']:.3f}; {a['band']['q975']:.3f}]")
print("corr cc/oc cluster mine", round(me["corr_pre_cc_oc_cluster"], 7), "agent", B["corr_pre_cc_vs_oc"]["CLUSTER"])
mx = 0
for name, a, b, rel in rows:
    flag = "  <-- >1%" if abs(rel) > 0.01 else ""
    print(f"{name:28s} mine {a:12.5f} agent {b:12.5f} rel {rel:+.2e}{flag}")
    mx = max(mx, abs(rel))
print("max |rel|", mx, "n compared", len(rows))
