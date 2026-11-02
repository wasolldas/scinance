"""Recheck of Fassung-2 thresholds: stress line, scaled null (k_W = SE_T/Null-SD), gate-4 factor 0.9025.
Null condition modelled as Phi((kappa*pi - k*d95)/SD_null) (as in Fassung 1), product with three z-conditions."""
from scipy.stats import norm
z = 1.6449
W = {"W1_stress": dict(se=(8.25, 8.66, 7.39), sd_null=7.53, d95=12.47, kappa=0.999),
     "W2_stress": dict(se=(8.52, 8.67, 7.39), sd_null=7.01, d95=11.61, kappa=0.815),
     "W1_zentral": dict(se=(7.34, 7.93, 6.56), sd_null=6.70, d95=11.10, kappa=0.999),
     "W2_zentral": dict(se=(7.58, 7.93, 6.56), sd_null=6.24, d95=10.33, kappa=0.815)}
def power(pi, w, k, gate):
    p = norm.cdf(pi / w["se"][0] - z) * norm.cdf(pi / w["se"][1] - z) * norm.cdf(pi / w["se"][2] - z)
    p *= norm.cdf((w["kappa"] * pi - k * w["d95"]) / w["sd_null"])
    return p * gate
def mde(fn):
    lo, hi = 5.0, 80.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if fn(mid) >= 0.8: hi = mid
        else: lo = mid
    return hi
for name, w in W.items():
    k = max(1.0, w["se"][0] / w["sd_null"])
    r = {"k": round(k, 3), "R0_gate": round(mde(lambda p: power(p, w, k, 0.9025)), 2), "R0_nogate": round(mde(lambda p: power(p, w, k, 1.0)), 2),
         "unscaled_nogate": round(mde(lambda p: power(p, w, 1.0, 1.0)), 2)}
    print(name, r)
# pilot power at c_A2 = 32.1 (stress, bindend) and 28.8 (zentral), SE_P 4.10
for c in (32.1, 29.3, 28.8):
    for mu in (16.5, 25.0):
        print(f"c_A2 {c}: mu {mu}: contrast {1-norm.cdf((c-mu)/4.10):.4f}, event-scale {1-norm.cdf((c-0.842*mu)/4.10):.4f}")
print("t at 32.1:", round(32.1/4.10, 2))
# PK criterion: expected pass 0.825 at 200 seeds -> minus 2.3263 * binomial SE
import math
pexp = 0.914 * 0.9025; print("expected PASS", round(pexp, 4), "criterion", round(pexp - 2.3263 * math.sqrt(pexp * (1 - pexp) / 200), 3))
