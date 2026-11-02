"""N-3: window power of the scaled (1c) at the U-3 threshold when the pilot predicts k_pred > 1 (SE_W,Pilot = k * se_mean binds,
SD_T = k * se_mean); compare with U-4 ((1c) term with k_pred).  v6b constants only."""
import json
from statistics import NormalDist
import yaml
N = NormalDist(); Z = N.inv_cdf(0.95); ZP = N.inv_cdf(0.80)
reg = yaml.safe_load(open("/home/user/scinance/scinance3-impl/state/herleitung_h32/h32_v1_TEMPLATE.yaml"))
out = {}
for v in ("mom1", "mom2", "mom4", "rev_gap"):
    for k in (1.0, 1.1, 1.2, 1.3):
        per = {}
        for wn in ("W1", "W2"):
            fz = reg["windows"][wn]["frozen_v6"]
            se_t = max(fz["e_se_rule"][v], k * fz["se_mean"][v]); sd_t = k * fz["se_mean"][v]
            m, q = fz["null_mean"][v], fz["q95"][v]
            per[wn] = {"u": Z * se_t + ZP * sd_t, "c3": q + ZP * sd_t, "c4": max(0.0, m) + k * (q - m) + ZP * sd_t,
                       "qeff": max(0.0, m) + k * (q - m), "sd": sd_t, "t1b": Z * k * fz["e_se_rule"][v], "m": m}
        mstar = max(0.0, reg["pilot_window"]["frozen_v6"]["m_P"][v], *(reg["windows"][w]["frozen_v6"]["null_mean"][v] for w in ("W1", "W2")))
        thr_u = mstar + max(p["u"] for p in per.values())
        c3 = max(thr_u, max(p["c3"] for p in per.values()))
        c4 = max(thr_u, max(p["c4"] for p in per.values()))
        pw3 = min(N.cdf((c3 - max(p["qeff"], p["t1b"] + max(0.0, p["m"]))) / p["sd"]) for p in per.values())
        pw4 = min(N.cdf((c4 - max(p["qeff"], p["t1b"] + max(0.0, p["m"]))) / p["sd"]) for p in per.values())
        out[f"{v}_k{k}"] = {"c_v_U3": c3, "c_v_U4": c4, "min_window_power_U3": pw3, "min_window_power_U4": pw4}
        print(v, k, {kk: round(x, 4) for kk, x in out[f"{v}_k{k}"].items()})
json.dump(out, open("rr2_u3k.json", "w"), indent=1)
