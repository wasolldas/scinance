"""Orchestrator recheck of Teil C formulas with the constants stated in NULL_SIMULATION_A2.md / PILOT_ROUTE_A2.md.
No data touched; pure arithmetic with scipy."""
from scipy.stats import norm
import numpy as np
z, z80 = 1.6449, 0.8416
W = {"W1": dict(se=(7.34, 7.93, 6.56), sd_null=6.70, d95=11.10, kappa=0.999),
     "W2": dict(se=(7.58, 7.93, 6.56), sd_null=6.24, d95=10.33, kappa=0.815)}
def prod_power(pi, w, k=1.0, with_null=True):
    p = norm.cdf(pi / w["se"][0] - z) * norm.cdf(pi / w["se"][1] - z) * norm.cdf(pi / w["se"][2] - z)
    if with_null: p *= norm.cdf((w["kappa"] * pi - k * w["d95"]) / w["sd_null"])
    return p
def mde(fn):
    lo, hi = 5.0, 60.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if fn(mid) >= 0.8: hi = mid
        else: lo = mid
    return hi
out = {}
for name, w in W.items():
    out[name] = dict(prod_null=mde(lambda p: prod_power(p, w)), prod_z=mde(lambda p: prod_power(p, w, with_null=False)),
                     prod_null_k1095=mde(lambda p: prod_power(p, w, k=1.0946)),
                     single_p2=(z + z80) * w["se"][0], single_p3fix=(z + z80) * w["se"][1],
                     null_cond=mde(lambda p: norm.cdf((w["kappa"] * p - w["d95"]) / w["sd_null"])))
    print(name, {k: round(v, 2) for k, v in out[name].items()})
c_a2 = max(out["W1"]["prod_null"], out["W2"]["prod_null"]); print("c_A2 (k=1):", round(c_a2, 2))
se_p = 4.10
for mu in (16.5, 25.0):
    pow_c = 1 - norm.cdf((c_a2 - mu) / se_p)           # contrast scale, condition (ii) alone
    pow_e = 1 - norm.cdf((c_a2 - 0.842 * mu) / se_p)   # event scale with OI attenuation on the pilot contrast
    print(f"pilot power mu={mu}: contrast {pow_c:.3f} (x sign P3 ~ {pow_c*norm.cdf(mu/4.43)*norm.cdf(mu/3.66):.3f}), event-scale {pow_e:.3f}")
print("pilot alpha:", f"{1 - norm.cdf(c_a2 / se_p):.1e}", "| t at threshold:", round(c_a2 / se_p, 2))
# Teil-B style product (DEC-103 E7) reproduction: SE 7.34/7.18/6.53 (W1), z-terms only
print("DEC-103 E7 product W1 (7.34/7.18/6.53):", round(mde(lambda p: norm.cdf(p/7.34-z)*norm.cdf(p/7.18-z)*norm.cdf(p/6.53-z)), 2))
