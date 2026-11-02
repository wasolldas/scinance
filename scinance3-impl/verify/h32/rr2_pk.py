"""PK (Erstfassung 4) expected PASS share in the binding window, normal approximation from the v6b constants only:
world = stress, drift 0 (null mean = driftfree cell), injection = realised target z SE_T + z80 SD_T (literal section 4).
Compares the frozen q95 (builder: no scaling) with the production rule q95_eff (DEC-101 E2); k_world = 1 and 1.1."""
import json
from statistics import NormalDist
import yaml
N = NormalDist(); Z = N.inv_cdf(0.95); ZP = N.inv_cdf(0.80)
reg = yaml.safe_load(open("/home/user/scinance/scinance3-impl/state/herleitung_h32/h32_v1_TEMPLATE.yaml"))
js = json.load(open("/home/user/scinance/scinance3-impl/state/runs/h32_20261021_v6b/h32_prelaunch.json"))
out = {}
for v in ("mom1", "mom2", "mom4", "rev_gap"):
    for k in (1.0, 1.1):
        tgt = {}
        for wn in ("W1", "W2"):
            fz = reg["windows"][wn]["frozen_v6"]
            se_t = max(fz["e_se_rule"][v], k * fz["se_mean"][v]) if k > 1 else fz["e_se_rule"][v]
            sd_t = k * fz["se_mean"][v]
            tgt[wn] = (Z * se_t + ZP * sd_t, se_t, sd_t)
        b = max(tgt, key=lambda w: tgt[w][0])
        fz = reg["windows"][b]["frozen_v6"]
        m_df = js["windows"][b]["frozen_v6"]["null_mean_driftfree"][v]
        m = fz["null_mean"][v]
        mu = m_df + tgt[b][0]
        sd = k * fz["se_mean"][v]
        t1b = Z * k * fz["e_se_rule"][v]
        q_unsc = fz["q95"][v]
        q_sc = max(0.0, m) + k * (fz["q95"][v] - m)
        out[f"{v}_k{k}"] = {"binding": b, "target": tgt[b][0], "m_df": m_df,
                            "pass_unscaled": N.cdf((mu - max(t1b, q_unsc)) / sd), "pass_scaled": N.cdf((mu - max(t1b, q_sc)) / sd),
                            "neg_false_pass_unscaled": 1 - N.cdf((max(t1b, q_unsc) - m_df) / sd), "neg_false_pass_scaled": 1 - N.cdf((max(t1b, q_sc) - m_df) / sd)}
for key, x in out.items():
    print(key, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in x.items()})
json.dump(out, open("rr2_pk.json", "w"), indent=1)

# aligned target (proposal N-2/N-3): target_W = max(z SE_T + z80 SD_T, q95_eff(k_pred) - m_df + z80 SD_T), binding = argmax
al = {}
for v in ("mom1", "mom2", "mom4", "rev_gap"):
    for k in (1.0, 1.1):
        best = None
        for wn in ("W1", "W2"):
            fz = reg["windows"][wn]["frozen_v6"]
            se_t = max(fz["e_se_rule"][v], k * fz["se_mean"][v]) if k > 1 else fz["e_se_rule"][v]
            sd_t = k * fz["se_mean"][v]
            m, q = fz["null_mean"][v], fz["q95"][v]
            m_df = js["windows"][wn]["frozen_v6"]["null_mean_driftfree"][v]
            q_eff = max(0.0, m) + k * (q - m)
            t = max(Z * se_t + ZP * sd_t, q_eff - m_df + ZP * sd_t)
            if best is None or t > best[0]:
                best = (t, wn, m_df, q_eff, sd_t, k * fz["e_se_rule"][v])
        t, wn, m_df, q_eff, sd, ese = best
        mu = m_df + t
        al[f"{v}_k{k}"] = {"binding": wn, "target_aligned": t, "pass_scaled": N.cdf((mu - max(Z * ese, q_eff)) / sd)}
for key, x in al.items():
    print("aligned", key, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in x.items()})
json.dump({"literal": out, "aligned": al}, open("rr2_pk.json", "w"), indent=1)
