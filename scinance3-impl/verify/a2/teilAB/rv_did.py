"""Dispersion of the paired slot difference (pre - [15:30,16:00)) on Mo-Do days (cluster) for a
difference-in-differences variant; joint MDE80 of D_i with OI attenuation.  SD/c only, no mean."""
import json, math, sys
import numpy as np
sys.path.insert(0, ".")
import rv_sigma as R
import rv_power as P
from bybit_edge.research import power_p1
days, cl, comp = {}, {}, {}
for s in ("BTC", "ETH"):
    days[s], cl[s], _, comp[s], _ = R.load(s)
fine = np.array([R.fine_class(d) for d in days["BTC"]])
pre = 0.5 * (R.slot(cl["BTC"], comp["BTC"], 450, 480) + R.slot(cl["ETH"], comp["ETH"], 450, 480))
f15 = 0.5 * (R.slot(cl["BTC"], comp["BTC"], 930, 960) + R.slot(cl["ETH"], comp["ETH"], 930, 960))
out = {}
for k in ("MODO", "FRI"):
    x = (pre - f15)[np.isin(fine, list(R.SETS[k]))]
    cands = [R.bartlett_c(x, B) for B in (4, 8, 13)] + [R.bm_c(x, L) for L in (4, 8, 13) if x.size // L >= 8]
    out[k] = {"n": int(x.size), "sd_pairdiff": float(np.std(x, ddof=1)), "c_bind": max(1.0, *cands)}
se_did = math.hypot(out["FRI"]["sd_pairdiff"] * math.sqrt(out["FRI"]["c_bind"] / 52),
                    out["MODO"]["sd_pairdiff"] * math.sqrt(out["MODO"]["c_bind"] / 208))
out["DiD_se_W1"] = se_did
out["DiD_mde80_p1"] = power_p1.mde80(se_did, P.Z1)
# joint MDE80 (event-effect scale) with P2' prior attenuated by 0.842, W1 SEs
r = json.load(open("rv_power.json"))["designs"]["W1"]
se_E = r["se_event_FRI"]
se_p = [math.sqrt(r["D_i_se_by_placebo"][k] ** 2 - se_E ** 2) for k in ("P2_MODO", "P3fix", "P3all")]
lo, hi = 15.0, 40.0
for _ in range(40):
    mid = 0.5 * (lo + hi)
    if P.joint_power([0.842 * mid, mid, mid], se_E, se_p, P.Z1, n_draw=200_000) >= 0.8:
        hi = mid
    else:
        lo = mid
out["D_i_joint_mde80_event_scale_att0842"] = hi
out["D_i_single_mde80_event_scale_att0842"] = r["D_i_mde80_p1"] / 0.842
R.guard(out)
print(json.dumps(out, indent=1))
