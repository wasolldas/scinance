"""Orchestrator spot check of review B-5: joint power of D_i against its placebo set {P2', P3fix, P3all}.
Inputs are dispersion/SE values only (from a2_vorarbeit.json via the review table); no returns touched."""
import numpy as np
from scipy.stats import norm
z = 1.6449
# Contrast SEs from the derivation (W1): D_i vs P2' 7.340, vs P3fix 7.18, vs P3all 6.53
# Event term SE: SD_cluster_FRI 43.830 * sqrt(c_bind 1.149 / 52)
se_E = 43.830 * np.sqrt(1.149 / 52)
se_c = np.array([7.340, 7.18, 6.53])
se_P = np.sqrt(se_c**2 - se_E**2)          # placebo-term SEs (independent of each other, approx.)
print("se_E", round(se_E, 3), "se_P", np.round(se_P, 3))
rng = np.random.default_rng(11)
R = 400_000
eE = rng.standard_normal(R) * se_E
eP = rng.standard_normal((3, R)) * se_P[:, None]
def powers(delta, atten=(1.0, 1.0, 1.0)):
    single = []; joint = np.ones(R, bool)
    for k in range(3):
        stat = atten[k] * delta + eE + eP[k]
        ok = stat > z * se_c[k]
        single.append(ok.mean()); joint &= ok
    return np.array(single), joint.mean(), float(np.prod(single))
for d in (16.5, 18.25, 25.0):
    s, j, p = powers(d)
    print(f"delta {d}: single {np.round(s,3)} joint {j:.3f} product {p:.3f}")
# MDE80 by bisection for joint and product (event scale), and with OI attenuation 0.842 on P2'
def mde(target_fn):
    lo, hi = 10.0, 40.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if target_fn(mid) >= 0.8: hi = mid
        else: lo = mid
    return hi
print("MDE80 single(P2') analytic", round((z + 0.8416) * se_c[0], 2))
print("MDE80 joint", round(mde(lambda d: powers(d)[1]), 2), "product", round(mde(lambda d: powers(d)[2]), 2))
att = (0.842, 1.0, 1.0)
print("with OI attenuation on P2': single", round((z + 0.8416) * se_c[0] / 0.842, 2),
      "joint", round(mde(lambda d: powers(d, att)[1]), 2), "product", round(mde(lambda d: powers(d, att)[2]), 2))
