"""Orchestrator: pre-pilot power line from the v6 template (ERSTFASSUNG 1.8/1.9/1.10) with the package's own constants."""
import math, yaml, json
from bybit_edge.research.h32_fm8 import handover, constants as C
from bybit_edge.research import power_p1
from scipy.stats import norm
reg = yaml.safe_load(open("scinance3-impl/state/herleitung_h32/h32_v1_TEMPLATE.yaml"))
Z = reg["z_krit"]; Z80 = 0.8416
print("z_krit", Z, "windows", {w: reg["windows"][w]["w_judged"] for w in ("W1", "W2")}, "w_pilot", reg["pilot_window"]["w_pilot"])
rows = {}
for v in ("mom1", "mom2", "mom4", "rev_gap"):
    k = handover.handover_constants(reg, v)
    # expected keys: per window e_se_rule, se_mean, null_mean, v_fm8, w_judged; m_P
    mde = {}; T = {}; ceil_ratio = {}
    for w in ("W1", "W2"):
        fz = reg["windows"][w]["frozen_v6"]
        se_t = fz["e_se_rule"][v]; sd_t = fz["se_mean"][v]; nm = fz["null_mean"][v]
        mde[w] = Z * se_t + Z80 * sd_t
        T[w] = Z * se_t + max(0.0, nm)
        ceil_ratio[w] = fz["ceiling_k4"] / T[w]
    m_star = max(0.0, reg["pilot_window"]["frozen_v6"]["m_P"][v], reg["windows"]["W1"]["frozen_v6"]["null_mean"][v], reg["windows"]["W2"]["frozen_v6"]["null_mean"][v])
    mde_star = max(mde.values())
    thr_on_xP = mde_star + m_star
    # window power at pi = thr_on_xP (prior = pilot point exactly at the handover threshold) and F-WEEK end power
    pw = {}
    for w in ("W1", "W2"):
        fz = reg["windows"][w]["frozen_v6"]
        pw[w] = norm.cdf((thr_on_xP - max(0.0, fz["null_mean"][v]) - Z * fz["e_se_rule"][v]) / fz["se_mean"][v])
    def endpower(m):
        H = sum(1.0 / i for i in range(1, m + 1)); z_eff = max(Z, norm.ppf(1 - 0.10 / (m * H)))
        return math.prod(norm.cdf((thr_on_xP - max(0.0, reg["windows"][w]["frozen_v6"]["null_mean"][v] ) - z_eff * reg["windows"][w]["frozen_v6"]["e_se_rule"][v]) / reg["windows"][w]["frozen_v6"]["se_mean"][v]) for w in ("W1", "W2"))
    rows[v] = {"MDE80_W1": mde["W1"], "MDE80_W2": mde["W2"], "MDE80_star": mde_star, "m_star": m_star, "threshold_on_xP": thr_on_xP,
               "T_W1": T["W1"], "T_W2": T["W2"], "ceiling_over_T_W1": ceil_ratio["W1"], "ceiling_over_T_W2": ceil_ratio["W2"],
               "power_W1_at_thr": pw["W1"], "power_W2_at_thr": pw["W2"], "joint_at_thr": pw["W1"] * pw["W2"],
               "endpower_m1": endpower(1), "endpower_m2": endpower(2), "endpower_m3": endpower(3), "endpower_m4": endpower(4), "endpower_m11": endpower(11),
               "handover_constants_keys": sorted(k.keys())}
    print(v, {kk: (round(vv, 5) if isinstance(vv, float) else vv) for kk, vv in rows[v].items() if kk != "handover_constants_keys"})
print("handover_constants keys:", rows["mom1"]["handover_constants_keys"])
# selection z (DEC-94 (7)) and a3 practice MDE80 (2.4865 * e_se_rule + 0.8416 * se_mean) for the double statement
for v in ("mom1", "rev_gap"):
    fz = reg["windows"]["W1"]["frozen_v6"]
    print(v, "A3-Praxis MDE80 W1:", round(2.4865 * fz["e_se_rule"][v] + Z80 * fz["se_mean"][v], 5))
json.dump(rows, open("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/orch_check/h32_v6_power.json", "w"), indent=1, default=str)
