"""Winner's curse: conditional median-unbiased estimate of the pilot mean given selection x_P >= c (truncated
normal, known SE_P), and test power at that estimate (mom1, S1). Pure arithmetic."""
import json, math, sys
from statistics import NormalDist
sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1 as P
N = NormalDist(); J = json.load(open("rv_nuis.json")); nu = J["nu"]
v = "mom1"; s = nu[v]["P"]["sep"]; c = 2.4865 * max(nu[v][W]["S1"] for W in ("W1", "W2")) + max(nu[v][W]["m"] for W in ("W1", "W2"))
def cond_tail(mu, x):  # P(X >= x | X >= c)
    return (1 - N.cdf((x - mu) / s)) / max(1e-300, 1 - N.cdf((c - mu) / s))
def mue(x):
    lo, hi = -0.2, x
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if cond_tail(mid, x) < 0.5: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)
for k in (0.25, 0.5, 1.0, 1.5, 2.0, 3.0):
    x = c + k * s; mu = mue(x)
    pr = [mu - max(0, nu[v][W]["m"]) for W in ("W1", "W2")]
    wp = [P.window_power(p, nu[v][W]["S1"], 1.6449) for p, W in zip(pr, ("W1", "W2"))]
    wp_point = [P.window_power(x - max(0, nu[v][W]["m"]), nu[v][W]["S1"], 1.6449) for W in ("W1", "W2")]
    print(f"x_P = c + {k:.2f} SE_P = {x:.4f}: median-unbiased mu_sel {mu:+.4f}; joint power at x_P {wp_point[0]*wp_point[1]:.2f}, at mu_sel {wp[0]*wp[1]:.2f}")
print("c", round(c, 5), "SE_P", round(s, 5))
lo, hi = c, c + 3 * s
for _ in range(100):
    mid = 0.5 * (lo + hi)
    if mue(mid) < c: lo = mid
    else: hi = mid
k = (hi - c) / s
mp = nu[v]["W1"]["m"]
print(f"Lesart C (mu_sel >= c): x_P >= c + {k:.3f} SE_P = {hi:.4f}; IC50 {hi - mp:.4f}; P(U|IC 0) {1 - N.cdf((hi - mp) / s):.4f}; "
      f"P(U|0.012) {1 - N.cdf((hi - mp - 0.012) / s):.3f}; P(U|0.020) {1 - N.cdf((hi - mp - 0.020) / s):.3f}; P(U|0.025) {1 - N.cdf((hi - mp - 0.025) / s):.3f}")
