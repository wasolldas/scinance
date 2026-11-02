# Orchestrator-Nachrechnung der Sweep-Kernzahlen (nur Formeln).
import numpy as np
from math import sqrt, log, pi, exp
from scipy.stats import norm, multivariate_normal, t as tdist
from scipy.optimize import brentq
za = norm.ppf(1 - 0.0025); zs = norm.ppf(0.95); zb = norm.ppf(0.80)
print("z_0.0025 =", round(za, 4))
# B: IK-10 Zone V: Z_pool(730) > za und Z_W2(365) > zs, Korrelation sqrt(365/730)
rho = sqrt(365 / 730)
mvn = multivariate_normal(mean=[0, 0], cov=[[1, rho], [rho, 1]])
def joint_power(d_sd):  # d_sd = delta/SD(IC_t)
    m1 = d_sd * sqrt(730); m2 = d_sd * sqrt(365)
    return mvn.cdf([m1 - za, m2 - zs])  # P(Z1>za-m1, Z2>zs-m2) by symmetry
d80 = brentq(lambda d: joint_power(d) - 0.80, 0.01, 1.0)
for K in (600, 500, 300):
    SD = 2.5 / sqrt(K - 1)
    print(f"IK-10 Zone V K {K}: SD {SD:.4f} MDE80 {d80*SD:.4f}; Zone K 12M (OBF 1,008): {1.008*(za+zb)*SD/sqrt(365):.4f}; Zone X 1.277 d: {(zs+zb)*SD/sqrt(1277):.4f}")
# SESOI Portfoliorahmen: 2 c / (3,51 * 370 bp)
for c in (11, 4, 15):
    print(f"SESOI Dezil-L/S c {c} bp: IC {2*c/(3.51*370):.4f}")
# F: schwere Raender, df_eff und Faktor
for kappa in (5, 10):
    for n in (40, 52, 365):
        v = 2/(n-1) + kappa/n; df = 2/v
        tcrit = tdist.ppf(1-0.0025, df); tb = tdist.ppf(0.80, df)
        print(f"kappa {kappa} n {n}: df_eff {df:.1f} t_crit {tcrit:.3f} MDE-Faktor {(tcrit+tb)/(za+zb):.3f}")
# Edgeworth Schiefe
for g in (-0.5, -1.0):
    for n in (40, 52):
        a = 0.0025 - (g/6)*(2*za**2+1)*norm.pdf(za)/sqrt(n)
        print(f"Schiefe {g} n {n}: alpha_eff ~ {a:.4f}")
# E: MP-Kante und Eigenwert
T = 1277
for K in (200, 500):
    print(f"MP-Kante K {K} T {T}: {(1+sqrt(K/T))**2:.3f}")
print("Eigenwert fuer SD-Verhaeltnis 2,5 (cos^2 = 1 / 0,5):", 1+5.25, 1+5.25/0.5)
# M: Drift-SE
print("Drift-SE BTC sigma 50 % nach 6,6 J:", round(0.5/sqrt(6.6), 3), "; rel. Var-SE 1-min (N=6,6*365*1440, kappa 10):", round(sqrt((2+10)/(6.6*365*1440)), 5), " Tage (kappa 6):", round(sqrt((2+6)/(6.6*365)), 4))
