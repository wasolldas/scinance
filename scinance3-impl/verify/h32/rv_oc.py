"""Operating characteristic of handover rule U: analytic (as derivation) and Monte Carlo with
random SE_P, F2_real, c_real (synthetic Gaussian AR(1) weekly IC series; no data)."""
import json, math, sys
import numpy as np
from statistics import NormalDist
sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1 as P
N = NormalDist(); Z = P.z_krit(0.05); MF = P.mde_factor(0.05)
J = json.load(open("rv_nuis.json")); nu, win, PM = J["nu"], J["win"], J["PM"]
VAR = ("mom1", "mom2", "mom4", "rev_gap")
ICG = (0.0, 0.004, 0.008, 0.012, 0.015, 0.020, 0.025, 0.030, 0.033)
def thr_point(v, se_key="S1"):
    se = max(nu[v][W][se_key] for W in ("W1", "W2")); m = max(nu[v][W]["m"] for W in ("W1", "W2"))
    return MF * se + max(0.0, m)
print("== analytic OC (derivation method), reading A / B")
for v in VAR:
    sep = nu[v]["P"]["sep"]; mp = nu[v]["W1"]["m"]
    tA = max(thr_point(v), 2 * sep); tB = max(thr_point(v) + N.inv_cdf(0.9) * sep, 2 * sep)
    rowA = [1 - N.cdf((tA - ic - mp) / sep) for ic in ICG]; rowB = [1 - N.cdf((tB - ic - mp) / sep) for ic in ICG]
    print(v, "thrA %.4f thrB %.4f" % (tA, tB), "A:", " ".join("%.3f" % x for x in rowA), "| B:", " ".join("%.3f" % x for x in rowB))
    print("   IC50 A %.4f B %.4f ; IC80 A %.4f B %.4f" % (tA - mp, tB - mp, tA - mp + P.Z_POWER * sep, tB - mp + P.Z_POWER * sep))
print("== analytic OC if v6 se_mean = S2-like (c_sim, 52/50 weeks) instead of S1")
for v in VAR:
    sep = nu[v]["P"]["sep"]; mp = nu[v]["W1"]["m"]
    # pilot source expectation: sqrt(c)*sqrt(V_W + F2)/sqrt(wj) = S2 approx (same F2, same c)
    tA = max(thr_point(v, "S2"), 2 * sep)
    print(v, "thr %.4f" % tA, " ".join("%.4f" % (1 - N.cdf((tA - ic - mp) / sep)) for ic in ICG))

# --------------------------------------------------------------- Monte Carlo of the full rule
def sb_se(X, mean_block=4.0, n_rep=200, rng=None):
    """vectorised stationary bootstrap SE for each row of X (n_mc x n)."""
    n_mc, n = X.shape; p = 1.0 / mean_block; t = np.arange(n)
    out = np.empty(n_mc)
    for i in range(n_mc):
        starts = rng.integers(0, n, size=(n_rep, n)); jump = rng.random((n_rep, n)) < p; jump[:, 0] = True
        first = np.maximum.accumulate(np.where(jump, t, 0), axis=1)
        idx = (np.take_along_axis(starts, first, axis=1) + (t - first)) % n
        out[i] = X[i][idx].mean(axis=1).std(ddof=1)
    return out
def mc(v, ic_true, se_v6, n_mc=3000, seed=7, rho=None, sd_mult=1.0, m_pilot=None):
    rng = np.random.default_rng(seed)
    n = PM["n"]; sdp = nu[v]["P"]["sdp"] * sd_mult; c = nu[v]["P"]["c"]
    if rho is None:   # AR(1) rho giving Bartlett-4-like variance factor c for the mean: c ~ (1+rho)/(1-rho)
        rho = (c - 1) / (c + 1)
    mp = nu[v]["W1"]["m"] if m_pilot is None else m_pilot
    e = rng.standard_normal((n_mc, n)); x = np.empty_like(e); x[:, 0] = e[:, 0]
    for t in range(1, n): x[:, t] = rho * x[:, t - 1] + math.sqrt(1 - rho**2) * e[:, t]
    X = (ic_true + mp) + sdp * x
    xp = X.mean(axis=1); sd = X.std(axis=1, ddof=1)
    seb = sb_se(X, rng=rng)
    sep = np.maximum.reduce([np.full(n_mc, PM["E"] / math.sqrt(n)), sd / math.sqrt(n), seb])
    F2 = np.maximum(0, sd**2 - PM["V"]); creal = np.maximum(1, n * seb**2 / sd**2)
    seT = []
    for W in ("W1", "W2"):
        wje = nu[v][W]["wje"]
        pil = np.sqrt(creal) * np.sqrt(win[W]["V"] + F2) / math.sqrt(wje)
        seT.append(np.maximum(se_v6[W], pil))
    seT = np.maximum(seT[0], seT[1]); m = max(nu[v][W]["m"] for W in ("W1", "W2"))
    ok = (xp > 0) & (xp - max(0, m) >= MF * seT) & (xp / sep >= 2.0)
    pilot_bind = np.mean(seT > max(se_v6.values()) + 1e-15)
    cond_mean = float(xp[ok].mean() - mp) if ok.any() else float("nan")
    return float(ok.mean()), pilot_bind, cond_mean, float(np.mean(sep)), float(np.mean(seT))
res = {}
for v in ("mom1", "rev_gap", "mom2", "mom4"):
    for scen, key in (("S1", "S1"), ("v6~S2", "S2")):
        se_v6 = {W: nu[v][W][key] for W in ("W1", "W2")}
        row = []
        for ic in (0.0, 0.004, 0.008, 0.012, 0.015, 0.020, 0.025, 0.033):
            p, pb, cm, sep, seT = mc(v, ic, se_v6, n_mc=2000 if ic in (0.0, 0.004) else 1000, seed=int(ic * 1e4) + 11)
            row.append((ic, p, pb, cm, sep, seT))
        res[f"{v}_{scen}"] = row
        print(v, scen, " ".join("IC%.3f:p=%.4f(pilotSEbinds %.2f, E[x|U]-m %.4f)" % (ic, p, pb, cm) for ic, p, pb, cm, sep, seT in row))
json.dump(res, open("rv_oc_mc.json", "w"), indent=1)
