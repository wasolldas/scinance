"""Robustness of the variance factor c (rule P-3 vs. stable estimators), HF (iii) and others vs cc.
Premium only in memory (review_hfrv loaders); outputs are c values, SD^2*c ratios and C10 days.
Run: python3 -I c_robust.py   (writes c_robust.json)"""
import json, math, sys
from datetime import date, timedelta
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_hfrv as rv  # own review code
from bybit_edge.research import power_p1 as pp

def bm_offsets(x, L):
    m = x.size // L
    vals = [L * x[o:o + m * L].reshape(m, L).mean(axis=1).var(ddof=1) / x.var(ddof=1) for o in range(x.size - m * L + 1)]
    a = np.array(vals)
    return {"blocks": m, "n_offsets": a.size, "min": float(a.min()), "q50": float(np.quantile(a, .5)), "max": float(a.max()),
            "head": float(a[0]), "tail": float(a[-1])}

def obm(x, L):
    n = x.size
    cs = np.concatenate([[0.0], np.cumsum(x - x.mean())])
    bm = (cs[L:] - cs[:-L]) / L
    return float(n * L / ((n - L) * (n - L + 1)) * np.sum(bm * bm) / x.var(ddof=1))

def main():
    t_days = [rv.IV_LO + timedelta(days=i) for i in range((rv.IV_HI - rv.IV_LO).days + 1)]
    iv, _ = rv.load_iv()
    days, lg, _ = rv.load_logclose("BTC")
    r = rv.one_min_returns(lg)
    rvd = rv.rv_variants(r)
    ivs = np.array([iv["BTC"][t] for t in t_days])
    zm = pp.mde_factor(0.05)
    prior = 9.469267123892108
    out = {}
    for v in rv.VARS:
        x = 100 * (ivs - rv.rv30_series(rvd[v], days, t_days))
        sd = float(x.std(ddof=1))
        est = {f"B{B}": rv.bartlett(x, B) for B in (60, 90, 120)}
        for L in (60, 90, 120):
            o = bm_offsets(x, L)
            est[f"BM{L}_head"] = o["head"]; est[f"BM{L}_tail"] = o["tail"]; est[f"BM{L}_q50_offsets"] = o["q50"]
            est[f"BM{L}_min_offsets"] = o["min"]; est[f"BM{L}_max_offsets"] = o["max"]
            est[f"OBM{L}"] = obm(x, L)
        est["consensus_tapered"] = rv.tapered_c(x)
        for mb in (30, 60, 90):
            est[f"statboot{mb}"] = float(x.size * pp.stationary_bootstrap_se(x, float(mb), 2000, seed=27) ** 2 / x.var(ddof=1))
        est["rule_P3_head"] = max(1, est["B60"], est["B90"], est["B120"], est["BM60_head"], est["BM90_head"], est["BM120_head"])
        est["rule_P3_tail"] = max(1, est["B60"], est["B90"], est["B120"], est["BM60_tail"], est["BM90_tail"], est["BM120_tail"])
        est["rule_P3_q50_offsets"] = max(1, est["B60"], est["B90"], est["B120"], est["BM60_q50_offsets"], est["BM90_q50_offsets"], est["BM120_q50_offsets"])
        out[v] = {"sd": sd, "c": est, "lrv": {k: sd * sd * c for k, c in est.items()},
                  "c10_days_closed": {k: max(1.0, c) * (zm * sd / prior) ** 2 for k, c in est.items()}}
    for v in rv.VARS:
        out[v]["lrv_ratio_to_cc"] = {k: out[v]["lrv"][k] / out["v6_cc"]["lrv"][k] for k in out[v]["lrv"]}
    rv.guard(out)
    (HERE / "c_robust.json").write_text(json.dumps(out, indent=1))
    keys = ["B90", "BM90_head", "BM90_tail", "BM90_q50_offsets", "BM90_min_offsets", "BM90_max_offsets", "OBM90", "consensus_tapered",
            "statboot60", "rule_P3_head", "rule_P3_tail", "rule_P3_q50_offsets"]
    for v in ("v3_5min_sub", "v5_30min", "v6_cc"):
        print(v, "SD %.2f" % out[v]["sd"])
        for k in keys:
            print(f"   {k:20s} c {out[v]['c'][k]:6.2f}  days {out[v]['c10_days_closed'][k]:7.1f}  lrv/cc {out[v]['lrv_ratio_to_cc'][k]:.3f}")
main()
