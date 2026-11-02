"""Proposal F for the PK target (follow-up N-2): target_W = max(z SE_T + z80 SD_T - min(0, m_df), q95_eff(k_pred) - m_df + z80 SD_T),
binding window = argmax; expected binding-window PASS share with the scaled gate (normal approximation, v6b constants)."""
import json
from statistics import NormalDist
import yaml
N = NormalDist(); Z = N.inv_cdf(0.95); ZP = N.inv_cdf(0.80)
reg = yaml.safe_load(open("/home/user/scinance/scinance3-impl/state/herleitung_h32/h32_v1_TEMPLATE.yaml"))
js = json.load(open("/home/user/scinance/scinance3-impl/state/runs/h32_20261021_v6b/h32_prelaunch.json"))
res = {}
for v in ("mom1", "mom2", "mom4", "rev_gap"):
    for k in (1.0, 1.1, 1.2):
        best = None
        for wn in ("W1", "W2"):
            fz = reg["windows"][wn]["frozen_v6"]
            se_t = max(fz["e_se_rule"][v], k * fz["se_mean"][v]) if k > 1 else fz["e_se_rule"][v]
            sd_t = k * fz["se_mean"][v]
            m, q = fz["null_mean"][v], fz["q95"][v]
            m_df = js["windows"][wn]["frozen_v6"]["null_mean_driftfree"][v]
            q_eff = max(0.0, m) + k * (q - m)
            t = max(Z * se_t + ZP * sd_t - min(0.0, m_df), q_eff - m_df + ZP * sd_t)
            if best is None or t > best["t"]:
                best = {"t": t, "w": wn, "m_df": m_df, "q_eff": q_eff, "sd": sd_t, "t1b": Z * k * fz["e_se_rule"][v]}
        mu = best["m_df"] + best["t"]
        res[f"{v}_k{k}"] = {"binding": best["w"], "target": best["t"], "share": N.cdf((mu - max(best["t1b"], best["q_eff"])) / best["sd"])}
        print(v, k, {kk: (round(x, 4) if isinstance(x, float) else x) for kk, x in res[f"{v}_k{k}"].items()})
json.dump(res, open("rr2_pk_f.json", "w"), indent=1)
