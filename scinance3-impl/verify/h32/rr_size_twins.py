"""Per-window size of the gate (1b)+(1c) under the v6 null model when the real null SD is r times the simulated one
(twin contracts / cross-sectional dependence beyond the one-factor null).  Normal approximation, SE at its expectation."""
import json
from statistics import NormalDist
import yaml
N = NormalDist()
reg = yaml.safe_load(open("/home/user/scinance/scinance3-impl/state/herleitung_h32/h32_v1_TEMPLATE.yaml"))
Z = N.inv_cdf(0.95)
out = {}
for wn, r in (("W1", 1.05), ("W2", 1.13)):
    fz = reg["windows"][wn]["frozen_v6"]
    for v in ("mom1", "mom2", "mom4", "rev_gap"):
        nm, se, ese, q = fz["null_mean"][v], fz["se_mean"][v], fz["e_se_rule"][v], fz["q95"][v]
        t_model = max(Z * ese, q)
        t_real = max(Z * ese * r, q)
        out[f"{wn}_{v}"] = {"r": r, "size_model": 1 - N.cdf((t_model - nm) / se), "size_real_r": 1 - N.cdf((t_real - nm) / (se * r)),
                            "size_with_q95_scaled": 1 - N.cdf((max(Z * ese * r, nm + r * (q - nm)) - nm) / (se * r))}
for k, x in out.items():
    print(k, {kk: round(vv, 4) for kk, vv in x.items()})
for r in (1.05, 1.13):
    print("r", r, {a: round(1 - N.cdf(N.inv_cdf(1 - a) / r), 4) for a in (0.05, 0.0333, 0.012, 0.00301)})
json.dump(out, open("rr_size_twins.json", "w"), indent=1)
