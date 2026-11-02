"""Synthetic: expected value of the P-1 (4) realized SE rule max(floor/sqrt(W), SD/sqrt(W), SE_stat) vs the true
SD of the window mean (W1 mom1 nuisance), and the resulting power at MDE80 computed with the true SD."""
import json, math, sys
import numpy as np
from statistics import NormalDist
N = NormalDist()
J = json.load(open("rv_nuis.json")); nu, win = J["nu"], J["win"]
rng = np.random.default_rng(5)
def sb_se(X, n_rep=500, mb=4.0):
    n = X.shape[1]; t = np.arange(n); out = np.empty(X.shape[0])
    for i in range(X.shape[0]):
        st = rng.integers(0, n, size=(n_rep, n)); j = rng.random((n_rep, n)) < 1/mb; j[:, 0] = True
        f = np.maximum.accumulate(np.where(j, t, 0), axis=1); idx = (np.take_along_axis(st, f, axis=1) + (t - f)) % n
        out[i] = X[i][idx].mean(axis=1).std(ddof=1)
    return out
for v in ("mom1", "rev_gap"):
    for W in ("W1", "W2"):
        sd = nu[v][W]["sd"]; c = max(1.0, nu[v][W]["csim"]); rho = (c - 1) / (c + 1); n = nu[v][W]["wje"]
        M = 3000
        e = rng.standard_normal((M, n)); x = np.empty_like(e); x[:, 0] = e[:, 0]
        for t in range(1, n): x[:, t] = rho * x[:, t-1] + math.sqrt(1 - rho**2) * e[:, t]
        X = sd * x
        true_sd_mean = X.mean(axis=1).std(ddof=1)
        rule = np.maximum.reduce([np.full(M, win[W]["E"] / math.sqrt(n)), X.std(axis=1, ddof=1) / math.sqrt(n), sb_se(X)])
        mde = 2.4865 * true_sd_mean
        # empirical power of condition mean >= 1.6449*rule at true effect = mde (shift)
        pw = np.mean(X.mean(axis=1) + mde >= 1.6449 * rule)
        print(f"{v} {W} c {c:.3f} true SD(mean) {true_sd_mean:.5f} E[rule] {rule.mean():.5f} ratio {rule.mean()/true_sd_mean:.3f} "
              f"power at MDE80(true SD) {pw:.3f} (analytic with E[rule] {N.cdf(2.4865 - 1.6449*rule.mean()/true_sd_mean):.3f})")
