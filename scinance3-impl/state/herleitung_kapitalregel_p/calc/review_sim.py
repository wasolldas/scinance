#!/usr/bin/env python3
"""Review (adversarial, symmetric mandate) of HERLEITUNG_KAPITALREGEL_P - independent re-computation.

Scinance 3.1, role Review, 2026-11-04. Different seed from the Herleitung (20261104 -> 7071).
No market data, no sealed files. Open numbers of the file only (A1: DEC-93 / DEC-104 E3 (e);
H-27: GL-034 / DEC-98 N2; STRESS_ABS fixture counts: state/runs/stress_abs.json, dates only).

Sections:
  R0  closed-form checks of every formula in the Herleitung (ruin, Kelly<->eps, geometric DD law,
      E[MaxDD] constant via Richardson extrapolation, E[mu_L | PASS], A1 / H-27 arithmetic)
  R1  null rate P(L* > 0 | Null) with a different seed; relevant null mu = k
  R2  series level (n 104, t-crit, Welch) re-run with different seed
  R3  NEW: group-sequential O'Brien-Fleming looks (VR-d12, 4 looks): fixed z_ci 2.8070 vs look boundary
  R4  NEW: heavy tails - ruin probability with t(4) innovations at kappa 0.4343 (eps 0.01)
  R5  NEW: MaxDD distribution - P(realised MaxDD > dd_tol) when L = L_dd (floor is a mean, not a quantile)
  R6  NEW: Peso world with non-informative market stress days (N_stress >= 10, no strategy loss)
  R7  NEW: waiting time until N_stress >= stress_n_min under the fixture rates (3.65 / 4.8 / 1.35 per year)
  R8  s_up <= 0 behaviour of the Herleitung code (strategy gains in every stress episode -> L* = 0)
  R9  Peso fixture pass rate of the Mess-Gate as a function of n (PZ-05 'gate must fail')
"""
import json
import os
import sys
import time

import numpy as np
from scipy import stats

SEED = 7071
RNG = np.random.default_rng(SEED)
ALPHA = 0.0025
Z = 2.8070
ZSTAB = stats.norm.ppf(0.05)
Z80 = 0.8416
MDD_C = np.sqrt(np.pi / 2.0)
OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = {"seed": SEED, "sections": {}}
T0 = time.time()


def say(*a):
    print(*a)
    sys.stdout.flush()


def capital_rule(mu_hat, se, passed, sigma, cost, eps, z_ci, ppy, dd_tol, dd_T, n_stress, n_min, s_up, s_tol):
    """Verbatim semantics of the Herleitung's capital_rule (re-implemented, not imported)."""
    mu_net = np.maximum(0.0, mu_hat - z_ci * se - cost)
    L_ruin = 2.0 * mu_net / (sigma ** 2 * np.log(1.0 / eps))
    L_dd = dd_tol / (MDD_C * sigma * np.sqrt(ppy) * np.sqrt(dd_T))
    if n_min <= 0:
        L_str = np.inf
    elif n_stress >= n_min and s_up > 0:
        L_str = s_tol / s_up
    else:
        L_str = 0.0
    return np.where(passed, np.minimum(np.minimum(L_ruin, L_dd), L_str), 0.0)


# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R0  closed-form checks")
r0 = {}
# ruin probability of a Brownian motion with drift mu, variance s2, start u, absorbing at 0: exp(-2 mu u / s2)
# -> u(eps) = s2/(2 mu) ln(1/eps); L_ruin = 1/u. Kelly f* = mu/s2 -> kappa = L_ruin/f* = 2/ln(1/eps).
r0["kappa_eps_0.01"] = float(2.0 / np.log(100.0))
r0["eps_kappa_0.25"] = float(np.exp(-8.0))
r0["eps_kappa_0.5"] = float(np.exp(-4.0))
# geometric: log-wealth drift m = L mu - L^2 s2/2, var L^2 s2 -> P(hit x) = x^(2m/(L^2 s2)) = x^(2/kappa - 1)
kap = 0.5
L = kap * 1.0  # mu = s2 = 1 w.l.o.g.
m = L * 1.0 - 0.5 * L ** 2
r0["geometric_exponent_kappa_0.5"] = float(2 * m / L ** 2)
r0["geometric_exponent_formula"] = float(2 / kap - 1)
# E[mu_L | PASS, null] in SE units = phi(z)/alpha - z
r0["E_muL_pass_null"] = float(stats.norm.pdf(Z) / (1 - stats.norm.cdf(Z)) - Z)
# MDE factors
r0["mde_factor_stab"] = float(Z + stats.norm.ppf(0.80 / 0.95))
r0["mde_factor_nostab"] = float(Z + Z80)
# capital power at mu = k: 0.95 Phi(-z)
r0["p_cap_pos_at_mu_eq_k"] = float(0.95 * stats.norm.cdf(-Z))
say(f"  kappa(eps 0.01) {r0['kappa_eps_0.01']:.4f}; eps(kappa 1/4) {r0['eps_kappa_0.25']:.2e}; eps(kappa 1/2) {r0['eps_kappa_0.5']:.4f}")
say(f"  geometric exponent kappa 0.5: derived {r0['geometric_exponent_kappa_0.5']:.3f} = 2/kappa-1 {r0['geometric_exponent_formula']:.3f}")
say(f"  E[mu_L | PASS, null] = phi(z)/alpha - z = {r0['E_muL_pass_null']:.4f} SE (Herleitung 0.2973)")
say(f"  MDE80 factor stab {r0['mde_factor_stab']:.4f} (Herleitung 3.8101); P(L*>0 | mu = k) = {r0['p_cap_pos_at_mu_eq_k']:.6f} (= alpha x 0.95)")
# E[MaxDD] constant: driftless random walk, Richardson extrapolation over T (bias ~ 1/sqrt(T))
mdd_ratio = {}
for Tm in (250, 1000, 4000):
    pm = 20000
    z = RNG.standard_normal((pm, Tm))
    path = np.cumsum(z, axis=1)
    runmax = np.maximum.accumulate(np.maximum(path, 0.0), axis=1)
    mdd = (runmax - path).max(axis=1)
    mdd_ratio[Tm] = float(mdd.mean() / np.sqrt(Tm))
    if Tm == 1000:
        qs = np.quantile(mdd / np.sqrt(Tm), [0.5, 0.75, 0.9, 0.95])
        r0["mdd_quantiles_over_sqrtT_T1000"] = {"q50": float(qs[0]), "q75": float(qs[1]), "q90": float(qs[2]), "q95": float(qs[3])}
        r0["p_mdd_gt_mean_T1000"] = float(np.mean(mdd > mdd.mean()))
# fit ratio(T) = c0 + c1/sqrt(T)
A = np.array([[1.0, 1.0 / np.sqrt(T)] for T in mdd_ratio])
b = np.array([mdd_ratio[T] for T in mdd_ratio])
c0, c1 = np.linalg.lstsq(A, b, rcond=None)[0]
r0["mdd_ratio_by_T"] = {str(k): v for k, v in mdd_ratio.items()}
r0["mdd_const_extrapolated"] = float(c0)
r0["mdd_const_theory"] = float(MDD_C)
say(f"  E[MaxDD]/sqrt(T) MC: {', '.join(f'T {k}: {v:.4f}' for k, v in mdd_ratio.items())}; extrapolated T->inf {c0:.4f} vs sqrt(pi/2) {MDD_C:.4f}")
say(f"  MaxDD/(sigma sqrt T) quantiles (T 1000): {r0['mdd_quantiles_over_sqrtT_T1000']}; P(MaxDD > E[MaxDD]) {r0['p_mdd_gt_mean_T1000']:.3f}")
# A1 arithmetic (open numbers)
sig = 354.4e-4
k_a1 = 36e-4
sig_ann = sig * np.sqrt(52)
a1 = {"sigma_ann": float(sig_ann), "full_kelly_prior": float(147.6e-4 / sig ** 2), "sr_ann_prior": float(147.6e-4 * 52 / sig_ann),
      "L_dd_1y": float(0.30 / (MDD_C * sig_ann)), "L_str_4sig": float(0.20 / (4 * sig)),
      "se_104": float(sig / np.sqrt(104)), "mde80_104": float(r0["mde_factor_stab"] * sig / np.sqrt(104)),
      "cap_mde80": {str(n): float(k_a1 + r0["mde_factor_stab"] * sig / np.sqrt(n)) for n in (104, 260, 665)},
      "p_cap_pos_null_104_with_k": float(0.95 * stats.norm.cdf(-(Z + k_a1 / (sig / np.sqrt(104))))),
      "cap_power_prior_theta1_104": float(0.95 * stats.norm.cdf((147.6e-4 - k_a1) / (sig / np.sqrt(104)) - Z)),
      "strenge_quotient_104": float((k_a1 + r0["mde_factor_stab"] * sig / np.sqrt(104)) / (r0["mde_factor_stab"] * sig / np.sqrt(104))),
      "datenfaktor_prior_theta1": float((147.6 / (147.6 - 36)) ** 2)}
r0["A1"] = a1
say(f"  A1: sigma_ann {a1['sigma_ann']:.4f}, Kelly(prior) {a1['full_kelly_prior']:.2f}x, SR {a1['sr_ann_prior']:.2f}, L_dd {a1['L_dd_1y']:.3f}, L_str {a1['L_str_4sig']:.3f}, "
    f"SE104 {a1['se_104']*1e4:.1f} bp, MDE80 {a1['mde80_104']*1e4:.1f} bp, Kap-MDE80 {a1['cap_mde80']['104']*1e4:.1f} bp, "
    f"P(L*>0|0,k) {a1['p_cap_pos_null_104_with_k']:.1e}, cap-power prior {a1['cap_power_prior_theta1_104']:.3f}, SQ {a1['strenge_quotient_104']:.3f}, Datenfaktor {a1['datenfaktor_prior_theta1']:.3f}")
# H-27 arithmetic
sv, c27, k27 = 18.6, 28.2, 1.5
se12 = sv * np.sqrt(c27 / 365.0)
h27 = {"se_12m": float(se12), "mde80_12m": float(r0["mde_factor_stab"] * se12),
       "months_mess_power_080_at_7.14": float((r0["mde_factor_stab"] * sv / 7.14) ** 2 * c27 / 365 * 12),
       "months_cap_power_080_at_7.14": float((r0["mde_factor_stab"] * sv / (7.14 - k27)) ** 2 * c27 / 365 * 12),
       "u_eps_at_true_mu_minus_k": float(sv ** 2 / (2 * (7.14 - k27)) * np.log(100.0)),
       "ratio_cap_to_mess": float((7.14 / (7.14 - k27)) ** 2)}
r0["H27"] = h27
say(f"  H-27: SE12 {h27['se_12m']:.2f} VP, MDE80 {h27['mde80_12m']:.1f} VP, months Mess 0.80 {h27['months_mess_power_080_at_7.14']:.0f}, "
    f"months Kap 0.80 {h27['months_cap_power_080_at_7.14']:.0f}, u(true mu-k) {h27['u_eps_at_true_mu_minus_k']:.0f} VP/vega, ratio {h27['ratio_cap_to_mess']:.3f}")
RES["sections"]["R0"] = r0

# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R1  null rate with different seed (z-level, SE known), 2e6 draws; relevant null mu = k")
N1 = 2_000_000
r1 = {}
for label, mu_se, cost_se in (("null_k0", 0.0, 0.0), ("null_k1", 0.0, 1.0), ("mu_eq_k", 1.0, 1.0), ("mde80_k0", r0["mde_factor_stab"], 0.0)):
    T = RNG.standard_normal(N1) + mu_se
    ZD = RNG.standard_normal(N1)
    passed = (T >= Z) & (ZD >= ZSTAB)
    L = capital_rule(T, np.ones(N1), passed, 1.0, cost_se, 0.01, Z, 52, 10.0, 1.0, 10, 10, 1.0, 0.2)
    r1[label] = {"p_pass": float(passed.mean()), "p_cap_pos": float((L > 0).mean()),
                 "mean_muL_given_pass": float((T - Z)[passed].mean()), "median_muL_given_pass": float(np.median((T - Z)[passed]))}
    say(f"  {label:10s}: P(PASS) {r1[label]['p_pass']:.6f}, P(L*>0) {r1[label]['p_cap_pos']:.6f}, "
        f"mu_L|PASS mean {r1[label]['mean_muL_given_pass']:.3f} SE median {r1[label]['median_muL_given_pass']:.3f} SE")
r1["mc_se"] = float(np.sqrt(ALPHA * (1 - ALPHA) / N1))
RES["sections"]["R1"] = r1

# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R2  series level n 104, estimated SE, t-crit, Welch stability test (different seed), 3e5 series")
N2, n, nJ = 300_000, 104, 52
t_crit = stats.t.ppf(1 - ALPHA, n - 1)


def series_test(x):
    m = x.mean(axis=1)
    se = x.std(axis=1, ddof=1) / np.sqrt(x.shape[1])
    xJ, xA = x[:, -nJ:], x[:, :-nJ]
    vJ, vA = xJ.var(axis=1, ddof=1) / nJ, xA.var(axis=1, ddof=1) / (x.shape[1] - nJ)
    df = (vJ + vA) ** 2 / (vJ ** 2 / (nJ - 1) + vA ** 2 / (x.shape[1] - nJ - 1))
    zD = (xJ.mean(axis=1) - xA.mean(axis=1)) / np.sqrt(vJ + vA)
    return m, se, m / se, zD >= stats.t.ppf(0.05, df)


r2 = {"t_crit": float(t_crit)}
x = RNG.standard_normal((N2, n))
m, se, t, ok = series_test(x)
r2["p_pass_z"] = float((t >= Z).mean())
r2["p_pass_t"] = float((t >= t_crit).mean())
r2["p_pass_full"] = float(((t >= t_crit) & ok).mean())
r2["p_pass_z_analytic_t103"] = float(1 - stats.t.cdf(Z, n - 1))
say(f"  iid null: P(t >= z 2.8070) {r2['p_pass_z']:.5f} (analytic t103 {r2['p_pass_z_analytic_t103']:.5f}); P(t >= t_crit {t_crit:.4f}) {r2['p_pass_t']:.5f}; full {r2['p_pass_full']:.5f}")
RES["sections"]["R2"] = r2

# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R3  NEW: O'Brien-Fleming 4 looks (VR-d12), one-sided alpha 0.0025: capital rule at an early efficacy stop")
# classic OBF boundary z_k = C * sqrt(K/k); calibrate C by MC so that P(any crossing | null) = 0.0025
N3, K = 4_000_000, 4
inc = RNG.standard_normal((N3, K))           # increments per quarter, unit variance each
S = np.cumsum(inc, axis=1)                   # cumulative sums
Zk = S / np.sqrt(np.arange(1, K + 1))        # standardised statistics at looks
t_frac = np.arange(1, K + 1) / K


def cross_prob(C):
    bnd = C / np.sqrt(t_frac)
    return float((Zk >= bnd).any(axis=1).mean())


lo, hi = 2.0, 4.0
for _ in range(40):
    mid = 0.5 * (lo + hi)
    if cross_prob(mid) > ALPHA:
        lo = mid
    else:
        hi = mid
C = 0.5 * (lo + hi)
bnd = C / np.sqrt(t_frac)
crossed = Zk >= bnd
first = np.where(crossed.any(axis=1), crossed.argmax(axis=1), -1)
r3 = {"C": float(C), "boundaries": [float(b) for b in bnd], "p_any_cross_null": cross_prob(C)}
say(f"  OBF boundaries (z at looks 1..4): {[round(float(b), 3) for b in bnd]}; P(PASS | null) {r3['p_any_cross_null']:.6f}")
# at the stopping look k: mu_hat_k = S_k / k (per-quarter units), SE_k = 1/sqrt(k)
# mu_L fixed z: mu_hat_k - 2.8070 SE_k ; mu_L look-specific: mu_hat_k - z_k SE_k ; all in SE_final (= 1/sqrt(4)) units
SE_final = 1.0 / np.sqrt(K)
stopped = first >= 0
k_idx = first[stopped]
mu_hat_k = S[stopped, k_idx] / (k_idx + 1)
SE_k = 1.0 / np.sqrt(k_idx + 1)
muL_fixed = (mu_hat_k - Z * SE_k) / SE_final
muL_look = (mu_hat_k - bnd[k_idx] * SE_k) / SE_final
muL_fixed_jump = (bnd - Z) / np.sqrt(t_frac) / 1.0 * SE_final / SE_final  # jump at boundary in SE_k units: (z_k - Z)
r3["share_stops_by_look_null"] = [float((k_idx == j).mean()) for j in range(K)]
r3["E_muL_fixed_z_given_pass_null_SEfinal"] = float(muL_fixed.mean())
r3["E_muL_look_z_given_pass_null_SEfinal"] = float(muL_look.mean())
r3["min_muL_fixed_z_given_pass_null_SEfinal"] = float(muL_fixed.min())
r3["jump_at_boundary_SEk_units"] = [float(b - Z) for b in bnd]
r3["E_muL_fixed_by_look_SEfinal"] = [float(muL_fixed[k_idx == j].mean()) if (k_idx == j).any() else None for j in range(K)]
say(f"  share of null-PASS stops by look: {[round(s, 3) for s in r3['share_stops_by_look_null']]}")
say(f"  jump of mu_L at the boundary with fixed z_ci 2.8070 (in SE_k units): {[round(j, 3) for j in r3['jump_at_boundary_SEk_units']]}")
say(f"  E[mu_L | PASS, null] in SE_final units: fixed z {r3['E_muL_fixed_z_given_pass_null_SEfinal']:.3f} vs look-specific z {r3['E_muL_look_z_given_pass_null_SEfinal']:.3f} "
    f"(single-look reference 0.297); min mu_L fixed z {r3['min_muL_fixed_z_given_pass_null_SEfinal']:.3f} (> 0: not continuous)")
say(f"  E[mu_L fixed z | stop at look j]: {[round(v, 3) if v else None for v in r3['E_muL_fixed_by_look_SEfinal']]}")
# under H1 at the single-look MDE80 (3.8101 SE_final): bias of mu_hat at early stops
mu1 = r0["mde_factor_stab"] * SE_final
S1 = np.cumsum(inc + mu1, axis=1)
Zk1 = S1 / np.sqrt(np.arange(1, K + 1))
cr1 = Zk1 >= bnd
f1 = np.where(cr1.any(axis=1), cr1.argmax(axis=1), -1)
st1 = f1 >= 0
ki = f1[st1]
mh = S1[st1, ki] / (ki + 1)
r3["H1_mde80_p_pass"] = float(st1.mean())
r3["H1_mde80_E_muhat_over_mu_by_look"] = [float(mh[ki == j].mean() / mu1) if (ki == j).any() else None for j in range(K)]
r3["H1_mde80_E_muL_fixed_over_mu_by_look"] = [float(((mh - Z / np.sqrt(ki + 1))[ki == j]).mean() / mu1) if (ki == j).any() else None for j in range(K)]
say(f"  H1 at MDE80: P(PASS) {r3['H1_mde80_p_pass']:.3f}; E[mu_hat/mu | stop at look j] {[round(v, 2) if v else None for v in r3['H1_mde80_E_muhat_over_mu_by_look']]}; "
    f"E[mu_L(fixed z)/mu | look j] {[round(v, 2) if v else None for v in r3['H1_mde80_E_muL_fixed_over_mu_by_look']]}")
del inc, S, Zk, S1, Zk1
RES["sections"]["R3"] = r3

# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R4  NEW: heavy tails - additive ruin with t(4) innovations (same mu, sigma) at kappa 0.4343 (eps 0.01) and 0.5")
mu0, sg0 = 0.01, 0.10
paths, steps, block = 40_000, 6000, 500
r4 = {}
for dist in ("gauss", "t4", "t3"):
    for kappa in (2 / np.log(100.0), 0.5):
        Lv = kappa * mu0 / sg0 ** 2
        cap = np.ones(paths)
        ruined = np.zeros(paths, dtype=bool)
        for b in range(steps // block):
            if dist == "gauss":
                z = RNG.standard_normal((paths, block))
            elif dist == "t4":
                z = RNG.standard_t(4, (paths, block)) / np.sqrt(2.0)       # var of t4 = 2
            else:
                z = RNG.standard_t(3, (paths, block)) / np.sqrt(3.0)       # var of t3 = 3
            cum = cap[:, None] + np.cumsum(Lv * (mu0 + sg0 * z), axis=1)
            ruined |= cum.min(axis=1) <= 0.0
            cap = cum[:, -1]
        key = f"{dist}_kappa_{kappa:.4f}"
        r4[key] = {"ruin_mc": float(ruined.mean()), "theory_gauss": float(np.exp(-2 / kappa)), "mc_se": float(np.sqrt(ruined.mean() * (1 - ruined.mean()) / paths))}
        say(f"  {dist:5s} kappa {kappa:.4f}: ruin MC {r4[key]['ruin_mc']:.4f} (MC SE {r4[key]['mc_se']:.4f}) vs Gaussian theory {r4[key]['theory_gauss']:.4f} -> factor {r4[key]['ruin_mc']/r4[key]['theory_gauss']:.2f}")
RES["sections"]["R4"] = r4

# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R5  NEW: MaxDD leg - realised MaxDD when L = L_dd (dd_tol 0.30, T 1y, A1 sigma_ann 0.2556), driftless and with the A1 prior drift")
pm, Tw = 40_000, 52
L_dd = a1["L_dd_1y"]
r5 = {}
for label, drift in (("driftless", 0.0), ("prior_theta1", 147.6e-4), ("sesoi", 36e-4)):
    z = RNG.standard_normal((pm, Tw)) * sig + drift
    path = np.cumsum(L_dd * z, axis=1)
    runmax = np.maximum.accumulate(np.maximum(path, 0.0), axis=1)
    mdd = (runmax - path).max(axis=1)
    r5[label] = {"E_mdd": float(mdd.mean()), "q50": float(np.median(mdd)), "q90": float(np.quantile(mdd, 0.9)), "q95": float(np.quantile(mdd, 0.95)),
                 "p_mdd_gt_dd_tol": float((mdd > 0.30).mean()), "p_mdd_gt_045": float((mdd > 0.45).mean())}
    say(f"  {label:12s}: E[MaxDD] {r5[label]['E_mdd']:.3f} (budget 0.30), q50 {r5[label]['q50']:.3f}, q90 {r5[label]['q90']:.3f}, q95 {r5[label]['q95']:.3f}, "
        f"P(MaxDD > 0.30) {r5[label]['p_mdd_gt_dd_tol']:.3f}, P(> 0.45) {r5[label]['p_mdd_gt_045']:.3f}")
RES["sections"]["R5"] = r5

# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R6  NEW: Peso world with NON-informative market stress days (N_stress 10 in window, strategy loss in them small)")
N6, nw = 300_000, 104
lam, jump, calm_sigma = 1.0 / 156.0, -0.35, 0.01
calm_drift = -jump * lam
x = RNG.standard_normal((N6, nw)) * calm_sigma + calm_drift
jumps = RNG.random((N6, nw)) < lam
x = x + jumps * jump
nj = jumps.sum(axis=1)
m, se, t, ok = series_test(x)
passed = (t >= t_crit) & ok
r6 = {"p_pass": float(passed.mean()), "p_pass_no_jump": float(passed[nj == 0].mean())}
# market stress days: 10 per window (assumed reachable), strategy's worst loss in them = 2 calm sigma (no jump fell on them)
for s_up_mult in (1.0, 2.0, 4.0):
    s_up = s_up_mult * calm_sigma
    L = capital_rule(m, se, passed, calm_sigma, 0.0, 0.01, Z, 52, 0.30, 1.0, 10, 10, s_up, 0.20)
    pos = L > 0
    r6[f"s_up_{s_up_mult:.0f}sig"] = {"p_cap_pos": float(pos.mean()), "L_median": float(np.median(L[pos])) if pos.any() else None,
                                      "L_q90": float(np.quantile(L[pos], 0.9)) if pos.any() else None,
                                      "loss_on_jump_median": float(-jump * np.median(L[pos])) if pos.any() else None,
                                      "L_str": float(0.20 / s_up), "L_dd": float(0.30 / (MDD_C * calm_sigma * np.sqrt(52)))}
    r = r6[f"s_up_{s_up_mult:.0f}sig"]
    say(f"  s_up {s_up_mult:.0f} sigma_calm: P(L*>0) {r['p_cap_pos']:.4f}; L* median {r['L_median']:.2f}x (q90 {r['L_q90']:.2f}); L_str {r['L_str']:.1f}, L_dd {r['L_dd']:.2f}; "
        f"a -35 % jump costs {100*r['loss_on_jump_median']:.0f} % of capital at the median L*")
# with a registered scenario floor s_scen = 0.35 (PZ-05 jump): L_str <= 0.20/0.35
r6["L_str_with_scenario_floor_035"] = float(0.20 / 0.35)
say(f"  with a registered scenario floor s_scen 0.35 (PZ-05 fixture): L_str <= {r6['L_str_with_scenario_floor_035']:.3f}x -> jump costs <= 20 % by construction")
RES["sections"]["R6"] = r6

# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R7  NEW: waiting time until N_stress >= stress_n_min (Poisson episodes from 2026-07-01)")
# fixture state/runs/stress_abs.json (dates only): 30 days / 19 episodes 2020-05..2026-08 (6.3 years);
# 2023-01..2026-08 (3.67 years): 5 days (incl. the two named days 2025-10-10, 2026-08-19) -> 1.36 / year
rates = {"construction_1pct_days": 3.65, "fixture_all_episodes": 19 / 6.3, "fixture_2023plus_days": 5 / 3.67, "W1W2_days": 3 / 2.0}
r7 = {"rates_per_year": rates, "rows": {}}
for nm in (5, 10, 19):
    r7["rows"][str(nm)] = {}
    for rn, rate in rates.items():
        # time until the nm-th event ~ Gamma(nm, rate); median and P(by year Y)
        med = stats.gamma.ppf(0.5, nm, scale=1 / rate)
        q10 = stats.gamma.ppf(0.1, nm, scale=1 / rate)
        p29 = stats.gamma.cdf(2.5, nm, scale=1 / rate)   # by 2029-01
        p31 = stats.gamma.cdf(4.5, nm, scale=1 / rate)   # by 2031-01
        p33 = stats.gamma.cdf(6.5, nm, scale=1 / rate)   # by 2033-01
        r7["rows"][str(nm)][rn] = {"median_years": float(med), "q10_years": float(q10), "p_by_2029": float(p29), "p_by_2031": float(p31), "p_by_2033": float(p33)}
        say(f"  n_min {nm:2d} rate {rate:.2f}/a ({rn:24s}): median {med:5.1f} a (-> {2026.5 + med:.0f}), q10 {q10:4.1f} a; P(by 2029) {p29:.2f}, 2031 {p31:.2f}, 2033 {p33:.2f}")
RES["sections"]["R7"] = r7

# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R8  s_up <= 0 (strategy gained in every stress episode) in the Herleitung's capital_rule semantics")
L_a = capital_rule(np.array([5.0]), np.array([1.0]), np.array([True]), 1.0, 0.0, 0.01, Z, 52, 10.0, 1.0, 12, 10, -0.5, 0.2)
L_b = capital_rule(np.array([5.0]), np.array([1.0]), np.array([True]), 1.0, 0.0, 0.01, Z, 52, 10.0, 1.0, 12, 10, 1e-6, 0.2)
r8 = {"L_star_s_up_negative": float(L_a[0]), "L_star_s_up_tiny_positive": float(L_b[0])}
say(f"  N_stress 12 >= 10, s_up = -0.5 (gain): L* = {r8['L_star_s_up_negative']:.3f}; s_up = 1e-6: L* = {r8['L_star_s_up_tiny_positive']:.3f} (L_str = 2e5, non-binding)")
say("  -> a tiny observed stress loss removes the stress leg entirely; a stress GAIN removes all capital. Both are artefacts of 'max observed loss' without a scenario floor.")
RES["sections"]["R8"] = r8

# ------------------------------------------------------------------------------------------
say("=" * 100)
say("R9  Peso fixture (PZ-05: Mess-Gate MUST fail) - pass rate of the pooled t-test as a function of n (no stability test, 1e5 series)")
r9 = {}
for nw in (52, 104, 260, 520):
    N9 = 100_000
    x = RNG.standard_normal((N9, nw)) * calm_sigma + calm_drift
    jm = RNG.random((N9, nw)) < lam
    x = x + jm * jump
    mm = x.mean(axis=1)
    ss = x.std(axis=1, ddof=1) / np.sqrt(nw)
    tt = mm / ss
    tc = stats.t.ppf(1 - ALPHA, nw - 1)
    pp = tt >= tc
    r9[str(nw)] = {"p_no_jump": float((jm.sum(axis=1) == 0).mean()), "p_pass": float(pp.mean()), "p_pass_given_no_jump": float(pp[jm.sum(axis=1) == 0].mean())}
    say(f"  n {nw:3d} weeks: P(no jump) {r9[str(nw)]['p_no_jump']:.3f}; P(PASS) {r9[str(nw)]['p_pass']:.3f}; P(PASS | no jump) {r9[str(nw)]['p_pass_given_no_jump']:.3f}")
say("  -> the pass rate on the Peso fixture is ~0.08..0.15 for n 52..260 weeks and falls only once jumps are almost surely in sample (n 520):")
say("     PZ-05 (gate MUST fail) is not satisfied by the pooled test on 2-5-year windows; Peso protection of the capital step cannot be delegated to it.")
RES["sections"]["R9"] = r9

RES["runtime_s"] = float(time.time() - T0)
out = os.path.join(OUT_DIR, "review_results.json")
with open(out, "w") as f:
    json.dump(RES, f, indent=1)
say("=" * 100)
say(f"written {out}; runtime {RES['runtime_s']:.1f} s")
