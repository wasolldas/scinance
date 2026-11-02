"""Review A2 Teil C: extra checks from r1.json and the calendar only (no return is loaded).
(1) P2'' single condition with threshold max(centre + d95; z SE) evaluated exactly (bivariate normal) instead of
    two independent factors -> MDE80 product and pilot threshold under that reading (report, fork P-G3/G-C5);
(2) joint power at the product target (PK expectation), (3) SD of the null shift under H0 (iid) in W1/W2,
(4) pilot power under alternative mechanical hand-over rules (report), (5) PK criterion arithmetic.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rv_common as rv  # noqa: E402

P1 = rv.load_power_p1()
Z, Z80 = P1.z_krit(0.05), P1.Z_POWER
N = NormalDist()
o = json.loads((rv.WORK / "r1.json").read_text())
rng = np.random.default_rng(31031)
E2 = rng.standard_normal((2_000_000, 2))


def biv_upper(m1, s1, t1, m2, s2, t2, r):
    """P(Y1 >= t1, Y2 >= t2) for a bivariate normal (common random numbers)."""
    a = E2[:, 0]
    b = r * E2[:, 0] + math.sqrt(1 - r * r) * E2[:, 1]
    return float(np.mean((m1 + s1 * a >= t1) & (m2 + s2 * b >= t2)))


def bis(f, lo=1.0, hi=60.0):
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if f(mid) >= 0.8 else (mid, hi)
    return hi


out = {}
flags, _ = rv.load_calendar()
for w in ("W1", "W2"):
    t = o["test"][w]["zentral"]
    seb, nsd, d95, kap = t["se_bind"], t["null_sd"], t["d95"], t["kappa"]
    r = nsd / seb["P2ss"]                          # corr(y, y - centre) in the model (Cov = null SD^2)

    def p2_exact(p, f=1.0):
        return biv_upper(f * p, seb["P2ss"], Z * seb["P2ss"], kap * f * p, nsd, d95, r)

    def prod_exact(p, f=1.0):
        return p2_exact(p, f) * P1.window_power(p, seb["P3fix"], Z) * P1.window_power(p, seb["P3all"], Z)
    out[w] = {"corr_y_ycentred_model": r, "mde80_product_P2exact": bis(prod_exact),
              "mde80_P2_single_exact": bis(p2_exact)}
    # null shift SD under H0 (iid, pooled sigma), calendar only
    S = rv.sets_of(*({"W1": (rv.date(2024, 7, 1), rv.date(2025, 6, 30)), "W2": (rv.W2_LO, rv.W2_HI)}[w]), flags)
    nl = rv.Null(S["E"], S["P2ss"])
    sig = o["sigma_within_central"]
    v = sum((1 / nl.W - (len(i) - 1) / nl.NP) ** 2 * sig ** 2 / len(i) for i in nl.perm)
    v += len(nl.fix_ev) * (sig / nl.W) ** 2 + sum(len(i) for i in nl.fix_pl) * (sig / nl.NP) ** 2
    out[w]["null_shift_sd_iid"] = math.sqrt(v)
    out[w]["fixed_placebo_days"] = sum(len(i) for i in nl.fix_pl)
c_exact = max(out[w]["mde80_product_P2exact"] for w in ("W1", "W2"))
pil = o["pilot"]
se_p = pil["se_pilot"]


def pp(mu, c):
    t = max(c, 2.0 * se_p["P2ss"])
    return (1 - N.cdf((t - mu) / se_p["P2ss"])) * N.cdf(mu / se_p["P3fix"]) * N.cdf(mu / se_p["P3all"])


rules = {"R0_U-A2_default_c": pil["c_A2_k1"], "R1_P2_exact_max_threshold_c": c_exact,
         "R2_without_null_factor_c": pil["c_A2_without_null"], "R3_stress_line_c": pil["c_A2_stress"]}
grid = {}
for prior in (12.0, 16.5, 20.0, 25.0, 30.0):
    g = {k: pp(prior, c) for k, c in rules.items()}
    g["R4_t_ge_2_only (verletzt DEC-94 (6))"] = pp(prior, 0.0)
    # R5 lower 80 % bound must reach the MDE80: x_P - z80 SE_P >= c  (stricter)
    g["R5_lower80_bound_ge_c"] = pp(prior, pil["c_A2_k1"] + Z80 * se_p["P2ss"])
    grid[str(prior)] = g
out["pilot_rules_c"] = rules
out["pilot_power_by_rule"] = grid
# PK expectation: joint power at the product target (my joint model) and criterion arithmetic
for w in ("W1", "W2"):
    gj = o["test"][w]["zentral"]["mde_u"]
    out[w]["joint_mde80"] = gj["joint_null"]
n_seeds = 200
for p_exp in (0.80, 0.871, 0.876):
    out[f"pk_criterion_expected_{p_exp}"] = p_exp - 2.3263 * math.sqrt(p_exp * (1 - p_exp) / n_seeds)
# probability that a pipeline with true PASS rate q passes the 0.734 criterion (binomial, 200 seeds)
from math import comb
def p_pass(q, thr=0.734, n=200):
    k0 = math.ceil(thr * n)
    return sum(comb(n, k) * q ** k * (1 - q) ** (n - k) for k in range(k0, n + 1))
out["pk_pass_prob_at_true_rate"] = {str(q): p_pass(q) for q in (0.70, 0.75, 0.78, 0.80, 0.871)}
h = rv.dump(out, rv.WORK / "r3.json")
print("r3.json sha256", h)
