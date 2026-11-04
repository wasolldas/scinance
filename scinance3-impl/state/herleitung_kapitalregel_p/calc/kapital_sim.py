#!/usr/bin/env python3
"""Capital rule for class P (premium harvesting) without MinTRL - formulas and simulations.

Scinance 3.1, role Herleitung, 2026-11-04 (DEC-107 (5), P-10).
No market data, no sealed files. All numeric inputs are open numbers of the file:
  A1 (GL-033 / DEC-93): nuisance SD 354.4 bp/week, rho_1 -0.28, prior 147.6 bp/week at theta = 1,
     theta_min 0.766, Taker SESOI 36 bp/week (DEC-104 E3 (e)), W_eff = 0.41 W (DEC-67 E4, superseded by c = max(1, c_hat)).
  H-27 (GL-034 / DEC-97): SD S1 18.6 VP, c 28.2 (so ~12.9 independent 30-day periods per year),
     SE(L = 12 months) 5.17 VP, prior 7.14 VP (band 3.2..10.5, DEC-98 N2), SESOI ~1.5 VP [U].
Everything else (eps, kappa, drawdown budgets, stress loss bound) is a registered design parameter
or a sensitivity, never a measured number.

Runs in well under two minutes on one CPU core. Fixed seed.
"""
import json
import os
import sys
import time

import numpy as np
from scipy import stats

SEED = 20261104
RNG = np.random.default_rng(SEED)

ALPHA_TEST = 0.0025
Z_TEST = 2.8070                     # Phi^-1(1 - 0.0025) rounded as in the constitution
ALPHA_STAB = 0.05
Z_STAB = stats.norm.ppf(ALPHA_STAB)  # -1.6449 (rejection if Z_D below)
Z80 = 0.8416
Z95 = 1.6449
MAXDD_CONST = np.sqrt(np.pi / 2.0)  # 1.2533

OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = {"seed": SEED, "sections": {}}
T0 = time.time()


def say(*a):
    print(*a)
    sys.stdout.flush()


# ----------------------------------------------------------------------------------------------
# Capital rule (one function, used everywhere)
# ----------------------------------------------------------------------------------------------
def capital_rule(mu_hat, se, passed, sigma, cost, eps, z_ci, periods_per_year,
                 dd_tol, dd_T_years, n_stress, stress_n_min, s_up, stress_loss_tol):
    """Return the maximal notional per unit capital L* (leverage), elementwise.

    mu_hat, se, passed : arrays (estimator, its SE, boolean Mess-PASS)
    sigma              : per-period SD of the premium per unit notional (nuisance, same unit as mu)
    cost               : registered cost per period per unit notional (Tradability-Gate, constants_hash)
    eps                : registered ruin probability (ruin capital u(eps) = sigma^2/(2 mu) ln(1/eps))
    z_ci               : z of the one-sided lower confidence bound used as mu (ci_basis)
    dd_tol, dd_T_years : MaxDD budget over horizon T (driftless floor E[MaxDD] = 1.2533 sigma_ann sqrt(T))
    n_stress, stress_n_min, s_up, stress_loss_tol : stress leg (PRD 3.6 (4)): capital > 0 only with
                         n_stress >= stress_n_min; worst observed episode loss s_up (per unit notional)
                         may not cost more than stress_loss_tol of capital.
    Components: L_ruin = 2 mu_net / (sigma^2 ln(1/eps))  (= kappa * Kelly with kappa = 2 / ln(1/eps))
                L_dd   = dd_tol / (1.2533 sigma_ann sqrt(T))
                L_str  = stress_loss_tol / s_up  if n_stress >= stress_n_min else 0
    L* = 1[PASS] * min(L_ruin, L_dd, L_str);  mu_net = max(0, mu_hat - z_ci se - cost).
    """
    mu_L = mu_hat - z_ci * se
    mu_net = np.maximum(0.0, mu_L - cost)
    L_ruin = 2.0 * mu_net / (sigma ** 2 * np.log(1.0 / eps))
    sigma_ann = sigma * np.sqrt(periods_per_year)
    L_dd = dd_tol / (MAXDD_CONST * sigma_ann * np.sqrt(dd_T_years))
    if stress_n_min <= 0:
        L_str = np.inf                      # no stress leg registered (comparison line only)
    elif n_stress >= stress_n_min and s_up > 0:
        L_str = stress_loss_tol / s_up
    else:
        L_str = 0.0                         # stress leg UNBELEGT -> no capital
    L = np.minimum(np.minimum(L_ruin, L_dd), L_str)
    return np.where(passed, L, 0.0), {"L_dd": float(L_dd), "L_str": float(L_str)}


def q(x, qs=(0.05, 0.25, 0.5, 0.75, 0.95)):
    if x.size == 0:
        return {str(p): None for p in qs}
    v = np.quantile(x, qs)
    return {str(p): float(val) for p, val in zip(qs, v)}


# ----------------------------------------------------------------------------------------------
# S0  Identities: Kelly fraction <-> ruin probability; MDE in SE units
# ----------------------------------------------------------------------------------------------
say("=" * 100)
say("S0  Identities (closed form)")
sec = {}
kappa_to_eps = {str(k): float(np.exp(-2.0 / k)) for k in (0.25, 1 / 3, 0.5, 1.0)}
eps_to_kappa = {str(e): float(2.0 / np.log(1.0 / e)) for e in (0.05, 0.02, 0.01, 0.001)}
sec["kappa_to_eps"] = kappa_to_eps
sec["eps_to_kappa"] = eps_to_kappa
say("  fractional Kelly kappa -> ruin prob exp(-2/kappa):", {k: round(v, 5) for k, v in kappa_to_eps.items()})
say("  ruin eps -> equivalent kappa 2/ln(1/eps)        :", {k: round(v, 4) for k, v in eps_to_kappa.items()})
mde_factor_no_stab = Z_TEST + Z80
# with stability test: pooled power must be 0.80 / 0.95 (DEC-107 (1)(d))
mde_factor_stab = Z_TEST + stats.norm.ppf(0.80 / 0.95)
sec["mde_factor_no_stab"] = float(mde_factor_no_stab)
sec["mde_factor_stab"] = float(mde_factor_stab)
say(f"  MDE80 factor (SE units): without stability test {mde_factor_no_stab:.4f}, with (q 0.95) {mde_factor_stab:.4f}")
# expected lower bound given PASS, under the null and at the MDE (truncated normal)
def e_muL_given_pass(mu_over_se, z=Z_TEST):
    a = z - mu_over_se
    tail = 1.0 - stats.norm.cdf(a)
    return mu_over_se - z + stats.norm.pdf(a) / tail  # in SE units
sec["E_muL_given_pass_SEunits"] = {
    "null": float(e_muL_given_pass(0.0)),
    "mde80_no_stab": float(e_muL_given_pass(mde_factor_no_stab)),
    "mde80_stab": float(e_muL_given_pass(mde_factor_stab)),
}
say("  E[mu_L | PASS] in SE units: null %.4f, at MDE80 (no stab) %.4f, at MDE80 (stab) %.4f" % (
    sec["E_muL_given_pass_SEunits"]["null"], sec["E_muL_given_pass_SEunits"]["mde80_no_stab"],
    sec["E_muL_given_pass_SEunits"]["mde80_stab"]))
# CI95 (one-sided 1.6449) variant gated by PASS: lower bound at the PASS boundary jumps to (Z_TEST - Z95) SE
sec["ci95_jump_at_boundary_SEunits"] = float(Z_TEST - Z95)
sec["E_muL95_given_pass_null_SEunits"] = float(e_muL_given_pass(0.0) + (Z_TEST - Z95))
say(f"  ci_basis 0.95 variant: jump at PASS boundary {Z_TEST - Z95:.4f} SE; E[mu_L95 | PASS, null] "
    f"{sec['E_muL95_given_pass_null_SEunits']:.4f} SE (x{sec['E_muL95_given_pass_null_SEunits']/sec['E_muL_given_pass_SEunits']['null']:.2f})")
# nonparametric exceedance of the worst observed stress loss
sec["p_next_worse_than_max"] = {str(n): float(1.0 / (n + 1)) for n in (1, 3, 5, 9, 10, 19)}
say("  P(next stress loss > worst of N observed) = 1/(N+1):", {k: round(v, 3) for k, v in sec["p_next_worse_than_max"].items()})
# capital-power: P(L* > 0) = Phi((mu - cost)/SE - z). With MDE80 = SESOI = cost: 0.80 reached at mu = SESOI + MDE80 = 2 SESOI
sec["capital_power_at_mu_eq_sesoi_when_mde80_eq_sesoi"] = float(stats.norm.cdf(0.0 - Z_TEST))
sec["capital_power_at_mu_eq_2sesoi_when_mde80_eq_sesoi"] = float(stats.norm.cdf(mde_factor_no_stab - Z_TEST))
say("  Capital power P(L*>0) when MDE80 = SESOI = cost: at mu = SESOI %.5f, at mu = 2 SESOI %.4f" % (
    sec["capital_power_at_mu_eq_sesoi_when_mde80_eq_sesoi"], sec["capital_power_at_mu_eq_2sesoi_when_mde80_eq_sesoi"]))
RESULTS["sections"]["S0_identities"] = sec

# ----------------------------------------------------------------------------------------------
# S1  z-level model: P(PASS), P(L*>0 | null), distribution of mu_L | PASS
# ----------------------------------------------------------------------------------------------
say("=" * 100)
say("S1  z-level model (SE known), 2e6 draws per scenario; stability test as independent N(0,1) under constancy")
N1 = 2_000_000
sec = {"n_draws": N1, "scenarios": {}}
for mu_se in (0.0, 1.0, 2.0, float(mde_factor_no_stab), float(mde_factor_stab), 5.0):
    T = RNG.standard_normal(N1) + mu_se
    ZD = RNG.standard_normal(N1)
    pass_pooled = T >= Z_TEST
    pass_full = pass_pooled & (ZD >= Z_STAB)
    muL = T - Z_TEST
    muL95 = T - Z95
    r = {
        "mu_over_se": mu_se,
        "p_pass_pooled_only": float(pass_pooled.mean()),
        "p_pass_with_stab": float(pass_full.mean()),
        "p_pass_pooled_analytic": float(1 - stats.norm.cdf(Z_TEST - mu_se)),
        "muL_given_pass_SEunits": q(muL[pass_full]),
        "mean_muL_given_pass": float(muL[pass_full].mean()) if pass_full.any() else None,
        "mean_muL95_given_pass": float(muL95[pass_full].mean()) if pass_full.any() else None,
        "share_of_true_mu_in_muL_median": (float(np.median(muL[pass_full]) / mu_se) if (mu_se > 0 and pass_full.any()) else None),
    }
    sec["scenarios"][f"mu_se_{mu_se:.4f}"] = r
    say(f"  mu/SE {mu_se:6.4f}: P(PASS pooled) {r['p_pass_pooled_only']:.6f} (analytic {r['p_pass_pooled_analytic']:.6f}); "
        f"P(PASS with stab) {r['p_pass_with_stab']:.6f}; mu_L|PASS median {r['muL_given_pass_SEunits']['0.5']:.3f} SE, "
        f"mean {r['mean_muL_given_pass']:.3f} SE; mu_L95 mean {r['mean_muL95_given_pass']:.3f} SE"
        + (f"; median share of true mu {r['share_of_true_mu_in_muL_median']:.3f}" if r['share_of_true_mu_in_muL_median'] else ""))
null = sec["scenarios"]["mu_se_0.0000"]
sec["p_capital_positive_given_null"] = null["p_pass_with_stab"]
sec["p_capital_positive_given_null_le_alpha"] = bool(null["p_pass_with_stab"] <= ALPHA_TEST)
sec["mc_se_of_p"] = float(np.sqrt(ALPHA_TEST * (1 - ALPHA_TEST) / N1))
say(f"  => P(Kapital > 0 | Null) = P(PASS | Null) = {null['p_pass_with_stab']:.6f} (MC SE {sec['mc_se_of_p']:.6f}); "
    f"analytic 0.0025 x 0.95 = {ALPHA_TEST * (1 - ALPHA_STAB):.6f}; <= alpha: {sec['p_capital_positive_given_null_le_alpha']}")
RESULTS["sections"]["S1_zlevel"] = sec

# ----------------------------------------------------------------------------------------------
# S2  A1 example with open numbers (weekly, bp/week -> fraction of notional)
# ----------------------------------------------------------------------------------------------
say("=" * 100)
say("S2  A1 (Funding-Carry, GL-033) - what the capital rule would have been, open numbers only")
A1 = {
    "sigma_week": 354.4e-4,      # nuisance SD, 2022-04..2024-06 (DEC-93)
    "rho1": -0.28,
    "cost_week": 36e-4,          # Taker-SESOI 36 bp/week (DEC-104 E3 (e)) used as registered cost k [U]
    "prior_theta1_week": 147.6e-4,
    "theta_min": 0.766,
    "periods_per_year": 52,
}
EPS = 0.01
Z_CI = Z_TEST
DD_TOL, DD_T = 0.30, 1.0
STRESS_N_MIN = 10
STRESS_TOL = 0.20
S_UP_MULT = 4.0                  # worst stress-episode loss assumed 4 sigma_week of notional (UNBELEGT, sensitivity 3..6)
N2 = 300_000
sec = {"inputs": dict(A1, eps=EPS, z_ci=Z_CI, dd_tol=DD_TOL, dd_T_years=DD_T, stress_n_min=STRESS_N_MIN,
                      stress_loss_tol=STRESS_TOL, s_up_mult_sigma=S_UP_MULT, n_draws=N2), "rows": []}
sig = A1["sigma_week"]
sigma_ann = sig * np.sqrt(52)
sec["sigma_ann"] = float(sigma_ann)
sec["full_kelly_at_prior_theta1"] = float(A1["prior_theta1_week"] / sig ** 2)
sec["implied_annual_sr_at_prior_theta1"] = float(A1["prior_theta1_week"] * 52 / sigma_ann)
say(f"  sigma_ann {sigma_ann:.4f}; full Kelly at prior (theta 1) {sec['full_kelly_at_prior_theta1']:.2f}x; "
    f"implied annual SR at prior {sec['implied_annual_sr_at_prior_theta1']:.2f} (prior itself UNBELEGT, theta)")
L_dd_1y = DD_TOL / (MAXDD_CONST * sigma_ann * np.sqrt(DD_T))
L_dd_3y = DD_TOL / (MAXDD_CONST * sigma_ann * np.sqrt(3.0))
sec["L_dd_1y"], sec["L_dd_3y"] = float(L_dd_1y), float(L_dd_3y)
say(f"  MaxDD leg: L_dd (dd_tol 0.30, T 1y) {L_dd_1y:.3f}x; T 3y {L_dd_3y:.3f}x  [driftless floor = expected damage of a false PASS]")
s_up = S_UP_MULT * sig
sec["L_stress_if_n_ok"] = float(STRESS_TOL / s_up)
say(f"  Stress leg: s_up = {S_UP_MULT:.0f} sigma_week = {s_up:.4f} of notional -> L_str {STRESS_TOL / s_up:.3f}x if N_stress >= {STRESS_N_MIN}; "
    f"file: STRESS_ABS W1 2 / W2 1 days (DEC-74 N (1)) -> N_stress <= 3 -> L_str = 0")
for n_weeks in (104, 260, 665):
    for c in (1.0, 1.0 / 0.41):
        se = sig * np.sqrt(c / n_weeks)
        mde80 = mde_factor_stab * se
        for mu_name, mu in (("null", 0.0), ("sesoi", A1["cost_week"]), ("prior_theta_min", A1["theta_min"] * A1["prior_theta1_week"]),
                            ("prior_theta1", A1["prior_theta1_week"])):
            mu_hat = mu + se * RNG.standard_normal(N2)
            zd = RNG.standard_normal(N2)
            passed = (mu_hat / se >= Z_TEST) & (zd >= Z_STAB)
            for n_stress in (3, 10):
                L, parts = capital_rule(mu_hat, se, passed, sig, A1["cost_week"], EPS, Z_CI, 52, DD_TOL, DD_T,
                                        n_stress, STRESS_N_MIN, s_up, STRESS_TOL)
                pos = L > 0
                row = {
                    "n_weeks": n_weeks, "c": round(c, 3), "se_week": float(se), "mde80_week": float(mde80),
                    "mu_true_week": mu, "mu_name": mu_name, "n_stress": n_stress,
                    "p_pass": float(passed.mean()), "p_capital_pos": float(pos.mean()),
                    "L_given_pos": q(L[pos]), "u_median_given_pos": (float(1.0 / np.median(L[pos])) if pos.any() else None),
                    "binding_share_dd": (float(np.mean(np.isclose(L[pos], parts["L_dd"]))) if pos.any() else None),
                    "binding_share_stress": (float(np.mean(np.isclose(L[pos], parts["L_str"]))) if pos.any() else None),
                }
                sec["rows"].append(row)
                if n_stress == 10 or mu_name == "null":
                    med = row["L_given_pos"]["0.5"]
                    say(f"  n {n_weeks:4d} c {c:4.2f} SE {se*1e4:6.1f} bp MDE80 {mde80*1e4:6.1f} bp | mu {mu*1e4:6.1f} bp ({mu_name:15s}) N_str {n_stress:2d}: "
                        f"P(PASS) {row['p_pass']:.4f} P(L*>0) {row['p_capital_pos']:.4f}"
                        + (f" L* med {med:.3f}x (q05 {row['L_given_pos']['0.05']:.3f}, q95 {row['L_given_pos']['0.95']:.3f}); u med {row['u_median_given_pos']:.2f}; "
                           f"DD-bound binds {row['binding_share_dd']:.2f}, stress binds {row['binding_share_stress']:.2f}" if pos.any() else " L* = 0 always"))
# capital-MDE for A1: mu needed for P(L*>0) = 0.80 at each n (c = 1)
sec["capital_mde80_week"] = {str(n): float(A1["cost_week"] + mde_factor_stab * sig / np.sqrt(n)) for n in (104, 260, 665)}
say("  Capital-MDE80 (mu with P(L*>0) = 0.80, c = 1) = cost + MDE80:", {k: f"{v*1e4:.1f} bp/week" for k, v in sec["capital_mde80_week"].items()})
RESULTS["sections"]["S2_A1"] = sec

# ----------------------------------------------------------------------------------------------
# S3  H-27 / VRP example (VP units per unit vega notional; 30-day periods, c 28.2)
# ----------------------------------------------------------------------------------------------
say("=" * 100)
say("S3  H-27 / VRP (GL-034) - capital per unit vega notional in VP units, open numbers only")
H27 = {"sd_premium_VP": 18.6, "c": 28.2, "prior_center_VP": 7.14, "prior_band_VP": [3.2, 10.5],
       "cost_VP": 1.5, "periods_per_year": 365.0 / 28.2}
sig_v = H27["sd_premium_VP"]
ppy = H27["periods_per_year"]
sec = {"inputs": H27, "rows": []}
for months in (12, 36, 90):
    n_days = months * 365.0 / 12.0
    se = sig_v * np.sqrt(H27["c"] / n_days)
    mde80 = mde_factor_stab * se
    for mu_name, mu in (("null", 0.0), ("sesoi", H27["cost_VP"]), ("prior_low", 3.2), ("prior_center", 7.14), ("prior_high", 10.5)):
        mu_hat = mu + se * RNG.standard_normal(N2)
        zd = RNG.standard_normal(N2)
        passed = (mu_hat / se >= Z_TEST) & (zd >= Z_STAB)
        mu_L = mu_hat - Z_CI * se
        mu_net = np.maximum(0.0, mu_L - H27["cost_VP"])
        with np.errstate(divide="ignore"):
            u_eps = np.where(passed & (mu_net > 0), sig_v ** 2 / (2.0 * mu_net) * np.log(1.0 / EPS), np.inf)
        pos = np.isfinite(u_eps)
        row = {"months": months, "se_VP": float(se), "mde80_VP": float(mde80), "mu_true_VP": mu, "mu_name": mu_name,
               "p_pass": float(passed.mean()), "p_capital_pos": float(pos.mean()),
               "u_eps_VP_per_vega_given_pos": q(u_eps[pos]) if pos.any() else None,
               "u_eps_at_true_mu_minus_cost_VP": (float(sig_v ** 2 / (2.0 * (mu - H27["cost_VP"])) * np.log(1.0 / EPS)) if mu > H27["cost_VP"] else None)}
        sec["rows"].append(row)
        say(f"  L {months:3d} mo SE {se:5.2f} VP MDE80 {mde80:5.2f} VP | mu {mu:5.2f} VP ({mu_name:12s}): P(PASS) {row['p_pass']:.4f} "
            f"P(u finite) {row['p_capital_pos']:.4f}"
            + (f" u(0.01) med {row['u_eps_VP_per_vega_given_pos']['0.5']:.0f} VP/vega (q05 {row['u_eps_VP_per_vega_given_pos']['0.05']:.0f}, "
               f"q95 {row['u_eps_VP_per_vega_given_pos']['0.95']:.0f}); at true mu-cost {row['u_eps_at_true_mu_minus_cost_VP']:.0f}" if pos.any() and row['u_eps_at_true_mu_minus_cost_VP'] else ""))
sec["months_for_capital_power_080_at_prior_center"] = float(((mde_factor_stab * sig_v) / (H27["prior_center_VP"] - H27["cost_VP"])) ** 2 * H27["c"] / 365.0 * 12.0)
sec["months_for_mess_power_080_at_prior_center"] = float(((mde_factor_stab * sig_v) / H27["prior_center_VP"]) ** 2 * H27["c"] / 365.0 * 12.0)
sec["stress_n_in_judgement_windows"] = "UNBELEGT (WD-13; reachability VR-f07 / DEC-104 E8 (d) outstanding)"
say(f"  Months for Mess-power 0.80 at prior 7.14 VP: {sec['months_for_mess_power_080_at_prior_center']:.0f}; "
    f"for capital-power 0.80 (mu - cost): {sec['months_for_capital_power_080_at_prior_center']:.0f}")
RESULTS["sections"]["S3_H27"] = sec

# ----------------------------------------------------------------------------------------------
# S4  Series level: estimated SE, t-type critical values, Welch stability test, AR(1) nuisance
# ----------------------------------------------------------------------------------------------
say("=" * 100)
say("S4  Series-level null check (n = 104 weeks, estimated SE, t-type critical values, Welch stability test)")
N4 = 300_000
n = 104
nJ = 52
t_crit = stats.t.ppf(1 - ALPHA_TEST, n - 1)
sec = {"n_series": N4, "n_weeks": n, "t_crit_0025_df103": float(t_crit), "rows": []}


def series_test(x):
    m = x.mean(axis=1)
    s = x.std(axis=1, ddof=1)
    se = s / np.sqrt(n)
    t = m / se
    xJ, xA = x[:, -nJ:], x[:, :-nJ]
    mJ, mA = xJ.mean(axis=1), xA.mean(axis=1)
    vJ, vA = xJ.var(axis=1, ddof=1) / nJ, xA.var(axis=1, ddof=1) / (n - nJ)
    seD = np.sqrt(vJ + vA)
    df = (vJ + vA) ** 2 / (vJ ** 2 / (nJ - 1) + vA ** 2 / (n - nJ - 1))
    zD = (mJ - mA) / seD
    stab_ok = zD >= stats.t.ppf(ALPHA_STAB, df)
    return m, se, t, stab_ok


for label, rho, mu_se_units in (("iid_null", 0.0, 0.0), ("ar1_neg_null", A1["rho1"], 0.0), ("iid_mde80_stab", 0.0, float(mde_factor_stab))):
    e = RNG.standard_normal((N4, n))
    if rho != 0.0:
        x = np.empty_like(e)
        x[:, 0] = e[:, 0]
        for t_ in range(1, n):
            x[:, t_] = rho * x[:, t_ - 1] + np.sqrt(1 - rho ** 2) * e[:, t_]
    else:
        x = e
    x = x + mu_se_units / np.sqrt(n)   # SD 1 per period -> SE(mean) = 1/sqrt(n)
    m, se, t, stab_ok = series_test(x)
    pass_z = t >= Z_TEST
    pass_t = t >= t_crit
    pass_full = pass_t & stab_ok
    L, _ = capital_rule(m, se, pass_full, 1.0, 0.0, EPS, Z_CI, 52, 10.0, 1.0, 10, STRESS_N_MIN, 4.0, STRESS_TOL)
    row = {"label": label, "rho": rho, "mu_in_SE_units": mu_se_units,
           "p_pass_pooled_zcrit": float(pass_z.mean()), "p_pass_pooled_tcrit": float(pass_t.mean()),
           "p_stab_reject": float(1 - stab_ok.mean()), "p_pass_full": float(pass_full.mean()),
           "p_capital_pos": float((L > 0).mean()), "mc_se": float(np.sqrt(max(pass_full.mean(), 1e-9) * (1 - pass_full.mean()) / N4))}
    sec["rows"].append(row)
    say(f"  {label:16s} rho {rho:5.2f} mu {mu_se_units:.4f} SE: P(PASS, z 2.8070) {row['p_pass_pooled_zcrit']:.5f}; "
        f"P(PASS, t {t_crit:.4f}) {row['p_pass_pooled_tcrit']:.5f}; stab reject {row['p_stab_reject']:.4f}; "
        f"P(PASS full) {row['p_pass_full']:.5f} (MC SE {row['mc_se']:.5f}); P(L*>0) {row['p_capital_pos']:.5f}")
RESULTS["sections"]["S4_series"] = sec

# ----------------------------------------------------------------------------------------------
# S5  Peso fixture (PZ-05 analogue): zero mean premium with rare -35 % jumps; stress leg as protection
# ----------------------------------------------------------------------------------------------
say("=" * 100)
say("S5  Peso world: calm premium + Merton jumps (rate 1/3 years, -35 %), overall mean 0, n = 104 weeks")
lam = 1.0 / 156.0
jump = -0.35
calm_sigma = 0.01
calm_drift = -jump * lam   # overall mean exactly 0
e = RNG.standard_normal((N4, n)) * calm_sigma + calm_drift
jumps = RNG.random((N4, n)) < lam
x = e + jumps * jump
n_jumps = jumps.sum(axis=1)
m, se, t, stab_ok = series_test(x)
pass_full = (t >= t_crit) & stab_ok
sec = {"n_series": N4, "lambda_per_week": lam, "jump": jump, "calm_sigma": calm_sigma, "calm_drift": float(calm_drift),
       "p_no_jump_in_sample": float((n_jumps == 0).mean()), "p_no_jump_analytic": float((1 - lam) ** n),
       "p_pass_full": float(pass_full.mean()), "p_pass_given_no_jump": float(pass_full[n_jumps == 0].mean()),
       "p_pass_given_jump": float(pass_full[n_jumps > 0].mean()) if (n_jumps > 0).any() else None}
# stress leg: N_stress = in-sample jump count (market stress days coincide with the jumps in this world)
for smin in (0, 1, STRESS_N_MIN):
    Ls = np.zeros(N4)
    for k in np.unique(n_jumps):
        idx = n_jumps == k
        s_up_k = -jump if k > 0 else 0.0
        Lk, _ = capital_rule(m[idx], se[idx], pass_full[idx], calm_sigma, 0.0, EPS, Z_CI, 52, DD_TOL, DD_T, int(k), smin, s_up_k, STRESS_TOL)
        Ls[idx] = Lk
    sec[f"p_capital_pos_stress_n_min_{smin}"] = float((Ls > 0).mean())
    sec[f"L_median_given_pos_stress_n_min_{smin}"] = float(np.median(Ls[Ls > 0])) if (Ls > 0).any() else None
say(f"  P(no jump in 104 weeks) {sec['p_no_jump_in_sample']:.4f} (analytic {sec['p_no_jump_analytic']:.4f}); "
    f"P(Mess-PASS) {sec['p_pass_full']:.4f} (given no jump {sec['p_pass_given_no_jump']:.4f}; given >= 1 jump {sec['p_pass_given_jump']:.5f})")
for smin in (0, 1, STRESS_N_MIN):
    say(f"  stress_n_min {smin:2d}: P(L* > 0) {sec[f'p_capital_pos_stress_n_min_{smin}']:.5f}"
        + (f", L* median given > 0: {sec[f'L_median_given_pos_stress_n_min_{smin}']:.3f}x" if sec[f'L_median_given_pos_stress_n_min_{smin}'] else ""))
say("  => the Mess-Gate alone is not Peso-proof at 104 weeks (this is why PZ-05 demands the gate fail on the fixture);")
say("     the stress leg (N_stress >= stress_n_min) sets the capital of a Peso-PASS to zero.")
RESULTS["sections"]["S5_peso"] = sec

# ----------------------------------------------------------------------------------------------
# S6  MC checks of the three formulas: ruin exp(-2/kappa), geometric drawdown law x^(2/kappa-1), MaxDD floor
# ----------------------------------------------------------------------------------------------
say("=" * 100)
say("S6  Monte Carlo checks of the formulas")
sec = {}
mu0, sg0 = 0.01, 0.10
fstar = mu0 / sg0 ** 2
paths, steps, block = 40_000, 6000, 500
for kappa in (0.25, 0.5):
    Lv = kappa * fstar
    cap = np.ones(paths)
    ruined = np.zeros(paths, dtype=bool)
    logw = np.zeros(paths)
    hit_half = np.zeros(paths, dtype=bool)
    for b in range(steps // block):
        z = RNG.standard_normal((paths, block))
        inc = Lv * (mu0 + sg0 * z)
        cum = cap[:, None] + np.cumsum(inc, axis=1)
        ruined |= (cum.min(axis=1) <= 0.0)
        cap = cum[:, -1]
        # geometric (continuously rebalanced fraction Lv of wealth): log-wealth increments
        ginc = Lv * mu0 - 0.5 * Lv ** 2 * sg0 ** 2 + Lv * sg0 * z
        gcum = logw[:, None] + np.cumsum(ginc, axis=1)
        hit_half |= (gcum.min(axis=1) <= np.log(0.5))
        logw = gcum[:, -1]
    # discrete-time continuity correction (Siegmund 1985; Broadie/Glasserman/Kou 1997 [sek]): barrier shifted by 0.5826 * step SD
    u_corr = 1.0 + 0.5826 * Lv * sg0
    ruin_discrete = float(np.exp(-2.0 * Lv * mu0 * u_corr / (Lv * sg0) ** 2))
    half_corr = float(np.exp(-2.0 * (Lv * mu0 - 0.5 * Lv ** 2 * sg0 ** 2) * (np.log(2.0) + 0.5826 * Lv * sg0) / (Lv * sg0) ** 2))
    sec[f"kappa_{kappa}"] = {"ruin_mc": float(ruined.mean()), "ruin_theory_exp(-2/kappa)": float(np.exp(-2 / kappa)),
                            "ruin_theory_discrete_corrected": ruin_discrete, "p_halve_theory_discrete_corrected": half_corr,
                            "p_halve_wealth_mc_geometric": float(hit_half.mean()), "p_halve_theory_0.5^(2/kappa-1)": float(0.5 ** (2 / kappa - 1)),
                            "mc_se_ruin": float(np.sqrt(np.exp(-2 / kappa) * (1 - np.exp(-2 / kappa)) / paths))}
    r = sec[f"kappa_{kappa}"]
    say(f"  kappa {kappa}: additive ruin MC {r['ruin_mc']:.5f} vs exp(-2/kappa) {r['ruin_theory_exp(-2/kappa)']:.5f} (MC SE {r['mc_se_ruin']:.5f}); "
        f"geometric P(halve) MC {r['p_halve_wealth_mc_geometric']:.4f} vs {r['p_halve_theory_0.5^(2/kappa-1)']:.4f}; "
        f"discrete-step corrected theory: ruin {r['ruin_theory_discrete_corrected']:.5f}, halve {r['p_halve_theory_discrete_corrected']:.4f}")
# MaxDD floor
pm, Tm = 20_000, 1000
z = RNG.standard_normal((pm, Tm))
path = np.cumsum(z, axis=1)
runmax = np.maximum.accumulate(np.maximum(path, 0.0), axis=1)
mdd = (runmax - path).max(axis=1)
sec["maxdd"] = {"T": Tm, "mc_mean": float(mdd.mean()), "theory_1.2533_sqrtT": float(MAXDD_CONST * np.sqrt(Tm)),
                "ratio": float(mdd.mean() / (MAXDD_CONST * np.sqrt(Tm)))}
say(f"  MaxDD driftless, T {Tm}: MC mean {sec['maxdd']['mc_mean']:.2f} vs 1.2533 sqrt(T) {sec['maxdd']['theory_1.2533_sqrtT']:.2f} "
    f"(ratio {sec['maxdd']['ratio']:.4f}; discrete-time bias downward)")
# with drift the expected MaxDD is smaller: quick check mu = 0.05 sigma per step
path2 = np.cumsum(z + 0.05, axis=1)
runmax2 = np.maximum.accumulate(np.maximum(path2, 0.0), axis=1)
sec["maxdd_with_drift_0.05sigma"] = float((runmax2 - path2).max(axis=1).mean())
say(f"  MaxDD with drift 0.05 sigma/step: MC mean {sec['maxdd_with_drift_0.05sigma']:.2f} (< driftless floor; the floor is the null-world expectation)")
RESULTS["sections"]["S6_checks"] = sec

# ----------------------------------------------------------------------------------------------
RESULTS["runtime_s"] = float(time.time() - T0)
out = os.path.join(OUT_DIR, "kapital_results.json")
with open(out, "w") as f:
    json.dump(RESULTS, f, indent=1)
say("=" * 100)
say(f"written {out}; runtime {RESULTS['runtime_s']:.1f} s")
