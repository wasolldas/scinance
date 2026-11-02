"""Synthetic only: how much do twin contracts (same underlying, e.g. BTCUSDT / BTCPERP / BTCUSDT-25DEC26) inflate the
null SD of the weekly Spearman IC and of the window mean, against the independent-column null of v6?

No real data.  K independent underlyings + n_twin duplicated columns (twin = underlying return + small basis noise).
Characteristic = this week's return (mom1 proxy), outcome = next week's return; both iid N(0,1) per column under H0.
"""
import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

rng = np.random.default_rng(20261021)


def spearman(a, b):
    ra, rb = rankdata(a), rankdata(b)
    ra -= ra.mean(); rb -= rb.mean()
    return float((ra * rb).sum() / np.sqrt((ra * ra).sum() * (rb * rb).sum()))


def weekly_ic_sd(k_total, n_twin, basis_sd=0.02, n_weeks=4000, cluster=None):
    """Weekly IC SD for k_total columns of which n_twin are twins of distinct underlyings (pairs);
    ``cluster`` adds extra clusters: list of cluster sizes (e.g. BTC: USDT, PERP, 2 dated = 4)."""
    cluster = cluster or []
    n_extra = sum(c - 1 for c in cluster)
    n_base = k_total - n_twin - n_extra
    ics = np.empty(n_weeks)
    for t in range(n_weeks):
        r0 = rng.standard_normal(n_base)
        r1 = rng.standard_normal(n_base)
        cols0 = [r0, r0[:n_twin] + basis_sd * rng.standard_normal(n_twin)]
        cols1 = [r1, r1[:n_twin] + basis_sd * rng.standard_normal(n_twin)]
        j = n_twin
        for c in cluster:
            for _ in range(c - 1):
                cols0.append(r0[j:j + 1] + basis_sd * rng.standard_normal(1))
                cols1.append(r1[j:j + 1] + basis_sd * rng.standard_normal(1))
            j += 1
        ics[t] = spearman(np.concatenate(cols0), np.concatenate(cols1))
    return float(ics.std(ddof=1))


out = {}
for label, k, tw, cl in (("W2_like", 570, 58, [4, 4]), ("W1_like", 440, 25, []), ("P_like", 213, 8, []),
                          ("W2_like_no_twins", 570, 0, [])):
    sd = weekly_ic_sd(k, tw, cluster=cl)
    out[label] = {"K": k, "twin_pairs": tw, "clusters": cl, "weekly_ic_sd": sd, "indep_1_over_sqrt_k_minus_1": 1 / np.sqrt(k - 1),
                  "ratio": sd * np.sqrt(k - 1)}
    print(label, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in out[label].items()})

# consequence for a one-sided p from a null that is too narrow by factor r: P(p_null <= a | H0)
from statistics import NormalDist
N = NormalDist()
cons = {}
for r in (1.03, 1.05, 1.10, 1.15, 1.20):
    cons[str(r)] = {str(a): 1 - N.cdf(N.inv_cdf(1 - a) / r) for a in (0.05, 0.0333, 0.012, 0.0073, 0.00301)}
print(json.dumps(cons, indent=1))
out["p_inflation"] = cons
Path(__file__).with_name("rr_twins.json").write_text(json.dumps(out, indent=1))
