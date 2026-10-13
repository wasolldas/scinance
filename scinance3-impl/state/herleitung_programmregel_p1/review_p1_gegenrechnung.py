"""Reviewer's independent re-computation for REVIEW_P1.md (programme rule P-1).

Own implementation (scipy quadrature + numpy Monte Carlo), not derived from rechnung_p1.py.
Reads ONLY two existing, unsealed artefacts:
  * state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json  -- windows W1/W2 only, window "L" is never accessed
  * state/herleitung_a1/feasibility.json                 -- config A, power grid, theta = 1
No panel data, no outcome data, no data of any future candidate. Sealed names are refused.

Run from the repo root:
  python3 -I scinance3-impl/state/herleitung_programmregel_p1/review_p1_gegenrechnung.py
Prints all reviewer numbers (deterministic; MC seed 7). Writes nothing.
"""
from __future__ import annotations

import fnmatch
import json
import math
import os

import numpy as np
from scipy import integrate, optimize, stats

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.dirname(HERE)
V5E = os.path.join(STATE, "runs", "wp13a_20261012_v5e", "wp13a_prelaunch.json")
FJ = os.path.join(STATE, "herleitung_a1", "feasibility.json")
SEALED = ("*_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_*_UNION_REAL.csv")

N = stats.norm
Z05, Z01, ZB = N.ppf(0.95), N.ppf(0.99), N.ppf(0.80)
ZW, ZP = 2.4865, 3.1680          # registered A3 factor / PRD pooled factor
PRIOR_A3 = 0.03
SEP_EQ = 1 / math.sqrt(2.0)      # pooled SE for two equal windows, window SE = 1


def load(path: str) -> dict:
    if any(fnmatch.fnmatch(os.path.basename(path), p) for p in SEALED):
        raise SystemExit("refusing sealed file")
    with open(path, "rb") as fh:
        return json.loads(fh.read())


# ---------------------------------------------------------------- null rates
def dec52_fpr(cp: float, screen_frac: float = 0.5, band: bool = False) -> float:
    """P(Z1+Z2 >= cp*sqrt2, Z_i >= screen, [Z_i <= 2x]) for iid N(0,1) window z-scores (equal windows)."""
    s = screen_frac * cp / math.sqrt(2.0)
    u = 2.0 * cp / math.sqrt(2.0) if band else np.inf
    c = cp * math.sqrt(2.0)

    def inner(z1: float) -> float:
        lo = max(s, c - z1)
        return N.pdf(z1) * max(0.0, N.cdf(u) - N.cdf(lo)) if lo < u else 0.0

    val, _ = integrate.quad(inner, s, (u if band else 12.0), points=[c - s], limit=400)
    return val


# ---------------------------------------------------------------- DEC-52 gate power
def gate_exact(mu1, mu2, se1, se2, n1, n2, cp, se_p) -> float:
    """Exact P(pooled >= cp*se_p, m1 >= screen, m2 >= screen), m_i ~ N(mu_i, se_i^2) independent,
    pooled = (n1 m1 + n2 m2)/(n1+n2); screen = 0.5 * cp * se_p (P-1 (6) reading)."""
    thr, scr = cp * se_p, 0.5 * cp * se_p

    def inner(m1: float) -> float:
        return N.pdf(m1, mu1, se1) * N.sf(max(scr, ((n1 + n2) * thr - n1 * m1) / n2), mu2, se2)

    kink = ((n1 + n2) * thr - n2 * scr) / n1
    pts = [kink] if kink > scr else None
    val, _ = integrate.quad(inner, scr, mu1 + 12 * se1, points=pts, limit=400)
    return val


def gate_product(mu1, mu2, se1, se2, cp, se_p, mu_p) -> float:
    scr = 0.5 * cp * se_p
    return N.sf(cp * se_p, mu_p, se_p) * N.sf(scr, mu1, se1) * N.sf(scr, mu2, se2)


def admission(cw: float, cp: float, rule: str, exact: bool) -> float | None:
    """Smallest prior d (grid 0.001, SE units, two equal windows) not assigned GL-012."""
    for i in range(1500, 6001):
        d = i / 1000
        pw = N.cdf(d - cw)
        if pw >= 0.8:
            return d
        if rule == "L3v":
            g = gate_exact(d, d, 1, 1, 52, 52, cp, SEP_EQ) if exact else gate_product(d, d, 1, 1, cp, SEP_EQ, d)
            if g >= 0.8:
                return d
    return None


def bailey_zmax(k: int) -> float:
    g = 0.5772156649015329
    return (1 - g) * N.ppf(1 - 1 / k) + g * N.ppf(1 - 1 / (k * math.e))


def main() -> None:
    print("== constants")
    print("z05 %.4f z01 %.4f zb %.4f mde_a %.4f mde_p %.4f ratio %.4f data %.4f" % (
        Z05, Z01, ZB, Z05 + ZB, Z01 + ZB, (ZW + ZB) / (Z05 + ZB), ((ZW + ZB) / (Z05 + ZB)) ** 2))

    print("== null rates")
    aw = N.sf(ZW)
    print("alpha_W(b) %.6f C10(a) %.6f C10(b) %.4e ratio %.2f size factor %.2f" % (aw, 0.05 ** 2, aw ** 2,
                                                                                  0.05 ** 2 / aw ** 2, 0.05 / aw))
    for name, cp in (("a", Z01), ("b", ZP)):
        print("DEC52 %s screens %.5f band %.5f sign %.5f" % (name, dec52_fpr(cp), dec52_fpr(cp, band=True),
                                                             dec52_fpr(cp, 0.0)))
    rng = np.random.default_rng(7)
    hits, hits_w, n_tot = 0, 0, 0
    s_p, s_w = 0.5 * Z01 / math.sqrt(2), 0.5 * Z05
    for _ in range(10):
        z = rng.standard_normal((2_000_000, 2))
        pooled = z[:, 0] + z[:, 1] >= Z01 * math.sqrt(2)
        hits += int(np.sum(pooled & (z[:, 0] >= s_p) & (z[:, 1] >= s_p)))
        hits_w += int(np.sum(pooled & (z[:, 0] >= s_w) & (z[:, 1] >= s_w)))
        n_tot += z.shape[0]
    print("MC 2e7 seed 7: screens 0.5x pooled thr %.5f | 0.5x per-window thr %.5f (screen %.5f vs %.5f SE_W)" % (
        hits / n_tot, hits_w / n_tot, s_p, s_w))
    for target in (0.005, 0.0025):
        cp = optimize.brentq(lambda c: dec52_fpr(c) - target, 2.3, 3.5)
        print("pooled z_krit for DEC-52 joint rate %.4f: %.4f (alpha_p %.5f)" % (target, cp, N.sf(cp)))

    print("== admission (two equal windows, SE units)")
    for label, cw, cp, rule in (("(b)+L2/L5 = A3-Praxis", ZW, ZP, "L2"), ("(b)+L3v", ZW, ZP, "L3v"),
                                ("(a)+L3v", Z05, Z01, "L3v"), ("(a)+L3v cp 2.5287", Z05, 2.5287, "L3v"),
                                ("(a)+L3v cp 2.7720", Z05, 2.7720, "L3v")):
        print("%-22s product %s exact %s" % (label, admission(cw, cp, rule, False), admission(cw, cp, rule, True)))
    print("L1 pooled bound (a) %.4f (b) %.4f" % ((Z01 + ZB) / math.sqrt(2), (ZP + ZB) / math.sqrt(2)))

    print("== lever 'stricter alpha' (P-1 (2)), equal windows")
    for d in (2.5, 2.6, 2.8):
        pa, pb = N.cdf(d - Z05), N.cdf(d - ZW)
        print("d %.1f default: P_W %.3f (C.10, joint %.3f) | alpha 0.00645: P_W %.3f, DEC-52 gate product %.3f exact %.3f"
              % (d, pa, pa * pa, pb, gate_product(d, d, 1, 1, Z01, SEP_EQ, d), gate_exact(d, d, 1, 1, 52, 52, Z01, SEP_EQ)))

    print("== selection ceiling")
    for zc in (Z05, ZW):
        k = 2
        while bailey_zmax(k) <= zc:
            k += 1
        print("crit %.4f K* %d zmax %.4f" % (zc, k, bailey_zmax(k)))

    print("== A3 retro (v5e, W1/W2 only)")
    v = load(V5E)
    win = {w: v["windows"][w] for w in ("W1", "W2")}
    for var in ("mom1", "mom2", "mom4", "rev_gap"):
        for cal in ("stress", "measured"):
            for opt in ("b", "a"):
                cw, cp = (Z05, Z01) if opt == "a" else (ZW, ZP)
                o = {}
                for w, ww in win.items():
                    nf = ww["noise_floor_and_threshold"]
                    sd = max(nf["floor"]["e_floor"],
                             ww["beta_control_method_study"]["calibrations"][cal]["methods"]["none"]["variants"][var]["factor_sd"])
                    se = sd / math.sqrt(nf["w_judged"])
                    icm = nf["ic_min_capped_per_variant"][var] * cw / ZW
                    hr = ww["beta_control_recommended_high_rep"]
                    sgn = 1 if hr["stress"]["variants"][var]["direction"] == "positive" else -1
                    qs = []
                    for key in ("stress", "stress_drifting"):
                        h = hr[key]["variants"][var]
                        q = h["quantile_one_sided"] if opt == "b" else h["mean_ic_draws_mean"] + sgn * Z05 * h["mean_ic_draws_sd"]
                        qs.append((sgn * q, h["mean_ic_draws_sd"]))
                    qd, sdb = max(qs)
                    tb = max(icm, qd)
                    p = min(N.cdf(PRIOR_A3 / se - cw), N.cdf((PRIOR_A3 - icm) / se), N.cdf((PRIOR_A3 - tb) / sdb))
                    mde = max((cw + ZB) * se, icm + ZB * se, tb + ZB * sdb)
                    o[w] = (se, sd, nf["w_judged"], p, mde)
                n1, n2 = o["W1"][2], o["W2"][2]
                sep = math.sqrt(n1 * o["W1"][1] ** 2 + n2 * o["W2"][1] ** 2) / (n1 + n2)
                gp = gate_product(PRIOR_A3, PRIOR_A3, o["W1"][0], o["W2"][0], cp, sep, PRIOR_A3)
                ge = gate_exact(PRIOR_A3, PRIOR_A3, o["W1"][0], o["W2"][0], n1, n2, cp, sep)
                print("%-7s %-8s %s W1 %.3f/%.4f W2 %.3f/%.4f pooled MDE80 %.4f gate prod %.3f exact %.3f" % (
                    var, cal, opt, o["W1"][3], o["W1"][4], o["W2"][3], o["W2"][4], (cp + ZB) * sep, gp, ge))
    for w, ww in win.items():
        vals = ww["noise_floor_and_threshold"]["ic_min_capped_per_variant"].values()
        print("IC_min under (a), smallest over variants, %s: %.5f" % (w, min(x * Z05 / ZW for x in vals)))

    print("== A1 retro (feasibility.json config A, theta = 1)")
    grid = load(FJ)["configs"]["A_dec70_1h_eingeschlossen"]["power"]["grid"]
    for c in ("c_dec67_E4", "c1_binding", "c_mbb_measured"):
        g = grid[c + "|theta=1.0"]
        se1, se2, sep = g["W1"]["se_bp"], g["W2"]["se_bp"], g["pooled"]["se_pooled_bp"]
        p1, p2, pp = g["W1"]["prem_bp"], g["W2"]["prem_bp"], g["pooled"]["prem_pooled_bp"]
        for opt in ("a", "b"):
            cw, cp = (Z05, Z01) if opt == "a" else (ZW, ZP)
            line = "%-15s %s P %.3f/%.3f MDE80_p %.1f prem_p %.1f gate prod %.3f exact %.3f" % (
                c, opt, N.cdf(p1 / se1 - cw), N.cdf(p2 / se2 - cw), (cp + ZB) * sep, pp,
                gate_product(p1, p2, se1, se2, cp, sep, pp), gate_exact(p1, p2, se1, se2, 52, 52, cp, sep))
            if opt == "a":
                line += " | cp 2.5287 prod %.3f exact %.3f | cp 2.7720 prod %.3f exact %.3f" % (
                    gate_product(p1, p2, se1, se2, 2.5287, sep, pp), gate_exact(p1, p2, se1, se2, 52, 52, 2.5287, sep),
                    gate_product(p1, p2, se1, se2, 2.7720, sep, pp), gate_exact(p1, p2, se1, se2, 52, 52, 2.7720, sep))
            print(line)


if __name__ == "__main__":
    main()
