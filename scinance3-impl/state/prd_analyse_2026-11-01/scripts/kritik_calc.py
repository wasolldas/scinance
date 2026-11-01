"""Analytische Gegenrechnungen fuer KRITIK_PRD.md (keine Daten, nur Formeln aus der Akte)."""
import numpy as np
from scipy.stats import norm, multivariate_normal

Phi, Pinv = norm.cdf, norm.ppf
out = {}

# ---------- 1. K-0.1 Horizont-Friktions-Kurve ----------
s1d = 262.0                     # bp, BTC Tagesvol (PRD 9.2 K-0.1)
k = np.sqrt(2/np.pi)            # 0.798
def edge_prd(p, h_days):        # PRD/R4: (2p-1)*0.798*sigma_h
    return (2*p-1)*k*s1d*np.sqrt(h_days)
def edge_gauss_from_p(p, h_days):  # bivariate normal: rho = sin(pi*(p-1/2)); E[sign(s) r] = rho*0.798*sigma
    rho = np.sin(np.pi*(p-0.5))
    return rho*k*s1d*np.sqrt(h_days)
def edge_gauss_from_ic(ic, h_days):
    return ic*k*s1d*np.sqrt(h_days)
def p_from_ic(ic):
    return 0.5 + np.arcsin(ic)/np.pi
def hmin(fun, arg, cost):        # days, solve fun(arg, h) = cost (edge ~ sqrt(h))
    return (cost/fun(arg, 1.0))**2

oracle_1s = 1.0*k*s1d/np.sqrt(86400)
out['oracle_1s_bp'] = oracle_1s
for cost in (11.0, 4.0, 5.4):
    out[f'hmin_prd_p055_cost{cost}_h'] = 24*hmin(edge_prd, 0.55, cost)
    out[f'hmin_gauss_p055_cost{cost}_h'] = 24*hmin(edge_gauss_from_p, 0.55, cost)
    out[f'hmin_prd_ic005_cost{cost}_d'] = hmin(lambda ic, h: edge_prd(p_from_ic(ic), h), 0.05, cost)
    out[f'hmin_gauss_ic005_cost{cost}_d'] = hmin(edge_gauss_from_ic, 0.05, cost)
    # cost halved
    out[f'hmin_prd_p055_cost{cost/2}_h'] = 24*hmin(edge_prd, 0.55, cost/2)
out['ratio_gauss_vs_prd_small_ic'] = edge_gauss_from_ic(0.05, 1)/edge_prd(p_from_ic(0.05), 1)
# Break-even weekly IC single position (R4 1.2.d): 0.798*(2p-1)*693 = 11
s1w = s1d*np.sqrt(7)
out['sigma_1w_bp'] = s1w
ic_be_prd = np.sin(np.pi/2*11/(k*s1w))
ic_be_gauss = 11/(k*s1w)
out['IC_breakeven_week_prd'] = ic_be_prd
out['IC_breakeven_week_gauss'] = ic_be_gauss
out['IC_econ_min_prd_x2'] = np.sin(np.pi/2*22/(k*s1w))
out['IC_econ_min_gauss_x2'] = 22/(k*s1w)

# ---------- 2. Lo 2002 ----------
z = 1.6449 + 0.8416
def tmin(sr, q):
    return z**2*(1+sr**2/(2*q))/sr**2
out['Tmin_SR2_q365'] = tmin(2.0, 365)
out['Tmin_SR2_q12'] = tmin(2.0, 12)
out['Tmin_SR2_approx'] = z**2/4
out['Tmin_SR05'] = z**2/0.25
# premium t-test duration = same: n >= z^2 * sigma^2/mu^2 -> T = z^2/SR_ann^2
out['SR_eff_needed_per_12m_window'] = z
# VRP effective SR (GL-034): mean 9.47, SD 18.6, c 28.2, n 365
se12 = 18.6*np.sqrt(28.2/365)
out['VRP_SE12'] = se12
out['VRP_SReff_ann'] = 9.47/se12
out['VRP_window_years_needed'] = (z/(9.47/se12))**2
# A1 (GL-033, W1 projection): prem 100.7 bp/week (theta 1), SD 372.9, c=1
out['A1_SReff_ann_theta1'] = 100.7/(372.9/np.sqrt(52))
out['A1_MDE80_W1_bp'] = z*372.9/np.sqrt(52)
out['A1_econ_min_bp'] = 36.0
out['A1_years_per_window_at_econmin'] = (z*372.9/36.0)**2/52
# A3 raw IC (GL-032 W1 stress SD 0.13; measured 0.09)
for sd in (0.0486, 0.0901, 0.1302):
    out[f'A3_detect_perwindow_SD{sd}'] = 0.344886*sd

# ---------- 3. IC floor N=5 ----------
out['IC_floor_N5_z2_W104'] = 2*0.5/np.sqrt(104)
out['IC_floor_N5_z24865_W104'] = z*0.5/np.sqrt(104)
out['IC_floor_N5_z24865_W52'] = z*0.5/np.sqrt(52)

# ---------- 4. Two windows / pooled ----------
out['C10_joint_power_at_08'] = 0.8**2
# pooled single test, same joint alpha 0.0025, at signal/SE_w = 2.4865
za = Pinv(1-0.0025)
out['pooled_power_same_alpha'] = Phi(z*np.sqrt(2) - za)
# per-window power needed for joint 0.8
pw = np.sqrt(0.8)
out['C10_perwindow_power_for_joint08'] = pw
out['C10_data_factor_for_joint08'] = ((1.6449+Pinv(pw))/z)**2
# pooled with alpha 0.0025, power 0.8: signal/SE_w
out['pooled_data_factor_vs_C10(0.8each)'] = (((za+0.8416)/np.sqrt(2))/z)**2

# ---------- 5. Product rule vs exact joint power (shared event term) ----------
def joint_power(mu, se_e, se_p_list, zc=1.6449):
    """Conditions Delta_j = E - P_j >= zc*SE_j, E~N(mu,se_e^2), P_j indep N(0,se_pj^2)."""
    ses = np.sqrt(se_e**2 + np.array(se_p_list)**2)
    n = len(se_p_list)
    cov = np.full((n, n), se_e**2) + np.diag(np.array(se_p_list)**2)
    # P(all Delta_j >= zc*SE_j) = P(-Delta_j <= -zc SE_j)
    mvn = multivariate_normal(mean=-mu*np.ones(n), cov=cov)
    pj = mvn.cdf(-zc*ses)
    prod = np.prod(Phi((mu - zc*ses)/ses))
    return pj, prod, ses
# illustrative A2-like: event SE 6.5, placebo SEs 3.4 (P2''), 4.5 (P3fix-like), 1.5 (P3all)
for mu in (20.0, 22.0, 24.0):
    pj, prod, ses = joint_power(mu, 6.5, [3.4, 4.5, 1.5])
    out[f'A2like_mu{mu}_joint'] = pj
    out[f'A2like_mu{mu}_product'] = prod
# duplicate condition (null cond ~ identical to P2'' cond): product squares
for p in (0.8, 0.9, 0.95):
    out[f'dup_condition_true_{p}'] = p
    out[f'dup_condition_product_{p}'] = p*p
# per-condition power implied by product>=0.8 with m equal factors
for m in (2, 3, 4, 5):
    pc = 0.8**(1/m)
    out[f'per_condition_power_m{m}'] = pc
    out[f'mde_inflation_m{m}'] = (1.6449+Pinv(pc))/z
    out[f'data_inflation_m{m}'] = ((1.6449+Pinv(pc))/z)**2

# ---------- 6. A2 MDE chain (numbers from DEC-98 N7, DEC-103 E7/N1) ----------
chain_w2 = [('Einzel P2pp', 18.8), ('Einzel max (P3fix)', 19.7), ('Produkt z-Terme', 23.1),
            ('+Null-Faktor', 24.4), ('+stress bindend', 27.2), ('+Gate(4)-Faktor', 32.1)]
base = chain_w2[0][1]
out['A2_chain_W2'] = [(n, v, round(v/base, 3), round((v/base)**2, 3)) for n, v in chain_w2]
out['A2_exact_joint_vs_final_W2_datafactor'] = (32.1/22.3)**2

# ---------- 7. Pilot handover operating characteristics ----------
# U-4 type rule: handover iff x_P >= c (c = MDE80 of test at pilot point). P(handover|mu=c) = 0.5
out['pilot_handover_at_mu_eq_c'] = 0.5
# A2 numbers (DEC-103 N1 (9)): c = 32.1, SE_P = 4.10 (contrast scale)
for mu in (16.5, 25.0, 32.1, 40.0):
    out[f'A2_pilot_handover_mu{mu}'] = Phi((mu - 32.1)/4.10)
out['A2_pilot_alpha'] = 1 - Phi(32.1/4.10)
# H-32 mom1: threshold 0.020538 on x_P, SE_P 0.01157
for mu in (0.01, 0.02, 0.03):
    out[f'H32_mom1_handover_mu{mu}'] = Phi((mu - 0.020538)/0.01157)

# ---------- 8. PPV of a measurement gate under different error budgets ----------
for base_rate in (0.05, 0.1, 0.2):
    for name, a, pw in (('C10(0.0025,0.64)', 0.0025, 0.64), ('pooled(0.0025,0.80)', 0.0025, 0.80),
                        ('pooled(0.01,0.80)', 0.01, 0.80), ('one(0.05,0.80)', 0.05, 0.80)):
        ppv = pw*base_rate/(pw*base_rate + a*(1-base_rate))
        out[f'PPV_base{base_rate}_{name}'] = round(ppv, 4)

# ---------- 9. Group sequential (O'Brien-Fleming, 4 equal looks, one-sided) ----------
def gsd_sim(alpha, power, looks=4, nsim=400000, seed=53, futility=False):
    rng = np.random.default_rng(seed)
    t = np.arange(1, looks+1)/looks
    # find OBF constant c: boundary c/sqrt(t)
    def crossing_prob(c, drift, inflate):
        incr = rng_incr * 1.0
        Z = np.cumsum(incr + drift*inflate*np.diff(np.r_[0, t])[None, :], axis=1)/np.sqrt(t)[None, :]
        return Z, (Z >= c/np.sqrt(t)[None, :])
    rng_incr = rng.standard_normal((nsim, looks))*np.sqrt(np.diff(np.r_[0, t]))[None, :]
    # calibrate c under H0
    lo, hi = 1.0, 4.0
    for _ in range(50):
        c = 0.5*(lo+hi)
        Z = np.cumsum(rng_incr, axis=1)/np.sqrt(t)[None, :]
        rej = (Z >= c/np.sqrt(t)[None, :]).any(axis=1).mean()
        if rej > alpha: lo = c
        else: hi = c
    c = 0.5*(lo+hi)
    zfix = Pinv(1-alpha)+Pinv(power)
    # find inflation R so that power is reached; drift theta*sqrt(R) at t=1
    lo, hi = 1.0, 1.5
    for _ in range(40):
        R = 0.5*(lo+hi)
        theta = zfix*np.sqrt(R)
        B = np.cumsum(rng_incr + theta*np.diff(np.r_[0, t])[None, :], axis=1)
        Z = B/np.sqrt(t)[None, :]
        cross = Z >= c/np.sqrt(t)[None, :]
        pw = cross.any(axis=1).mean()
        if pw < power: lo = R
        else: hi = R
    R = 0.5*(lo+hi)
    theta = zfix*np.sqrt(R)
    B = np.cumsum(rng_incr + theta*np.diff(np.r_[0, t])[None, :], axis=1)
    Z = B/np.sqrt(t)[None, :]
    cross = Z >= c/np.sqrt(t)[None, :]
    first = np.where(cross.any(axis=1), cross.argmax(axis=1), looks-1)
    EN_H1 = (t[first]*R).mean()
    Z0 = np.cumsum(rng_incr, axis=1)/np.sqrt(t)[None, :]
    cross0 = Z0 >= c/np.sqrt(t)[None, :]
    first0 = np.where(cross0.any(axis=1), cross0.argmax(axis=1), looks-1)
    EN_H0 = (t[first0]*R).mean()
    return dict(c=c, R_max=R, EN_H1=EN_H1, EN_H0=EN_H0)
out['GSD_OBF4_a0.05_p0.8'] = gsd_sim(0.05, 0.8)
out['GSD_OBF4_a0.0025_p0.8'] = gsd_sim(0.0025, 0.8)

# ---------- 10. SESOI vs MDE (A2) ----------
out['A2_SESOI_taker_2x11'] = 22.0
out['A2_SESOI_maker_2x(4+2*0.7)'] = 2*(4+2*0.7)

for kk, v in out.items():
    print(kk, '=', v)
