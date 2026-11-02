"""Sign-adjusted selection ceiling K=4 (Gaussian approximation; synthetic, no data).
Means/SDs of the window means from v5e high-rep stress (driftfree and drifting), correlation of
window-mean ICs approximated by the cross-sectional correlation of the characteristics under iid
weekly returns (mom1=r_t, mom2=r_t+r_{t-1}, mom4=sum4, rev_gap=r_{t-1})."""
import json, math
import numpy as np
from statistics import NormalDist
d = json.load(open("/home/user/scinance/scinance3-impl/state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json"))
J = json.load(open("rv_nuis.json")); nu = J["nu"]
VAR = ["mom1", "mom2", "mom4", "rev_gap"]; S = np.array([1, 1, 1, -1.0])
Z = NormalDist().inv_cdf(0.95)
# char correlation (iid returns)
C = np.array([[1, 1/math.sqrt(2), 0.5, 0], [1/math.sqrt(2), 1, 2/math.sqrt(8), 1/math.sqrt(2)],
              [0.5, 2/math.sqrt(8), 1, 0.5], [0, 1/math.sqrt(2), 0.5, 1]])
D = np.diag(S); Cs = D @ C @ D        # sign-adjusted
print("eig sign-adjusted corr", np.linalg.eigvalsh(Cs).round(3))
rng = np.random.default_rng(1)
for W in ("W1", "W2"):
    for cal in ("stress", "stress_drifting"):
        hv = d["windows"][W]["beta_control_recommended_high_rep"][cal]["variants"]
        mu = np.array([S[i] * hv[v]["mean_ic_draws_mean"] for i, v in enumerate(VAR)])
        sd = np.array([hv[v]["mean_ic_draws_sd"] for v in VAR])
        out = {}
        for name, corr in (("indep", np.eye(4)), ("charcorr", Cs), ("allpos0.7", np.full((4, 4), 0.7) + 0.3 * np.eye(4))):
            L = np.linalg.cholesky(corr + 1e-12 * np.eye(4))
            x = mu + (rng.standard_normal((400000, 4)) @ L.T) * sd
            out[name] = x.max(axis=1).mean()
        thr = {v: Z * nu[v][W]["S1"] + nu[v][W]["credit"] for v in VAR}
        print(W, cal, "ceiling K4 sign-adj:", {k: round(v, 5) for k, v in out.items()},
              "| thresholds T:", {v: round(t, 5) for v, t in thr.items()},
              "| max ratio (charcorr):", round(out["charcorr"] / min(thr.values()), 3),
              "| v5e raw-signed K7 ceiling", round(d["windows"][W]["beta_control_recommended_high_rep"][cal]["ceiling_mean_of_max"], 5))
