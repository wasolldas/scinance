# Orchestrator-Nachrechnung der OC-Kernzahlen (Regel P-2 (a) und Alternativen), nur Formeln.
from math import sqrt
from scipy.stats import norm, multivariate_normal
from scipy.optimize import brentq
za = norm.ppf(1 - 0.0025); zb = norm.ppf(0.80); c_c10 = norm.ppf(0.95) + zb
print("z_0.0025", round(za, 4), "C.10 je 0,80: MDE =", round(c_c10, 4), "SE_12")
def rule(alpha_s, r, d):
    """P(Z_pool > za and Z_rec > z_s) fuer Effekt d (in SE_12), juengstes Fenster Anteil r der Daten."""
    zs = norm.ppf(1 - alpha_s)
    rho = sqrt(r)
    m_pool = d / sqrt(r)   # SE_pool = SE_12 * sqrt(r)
    m_rec = d
    mvn = multivariate_normal(mean=[0, 0], cov=[[1, rho], [rho, 1]])
    return mvn.cdf([m_pool - za, m_rec - zs])
for alpha_s in (0.05, 0.10, 0.20, 0.50):
    for r in (0.5, 1/3, 0.25):
        a_eff = rule(alpha_s, r, 0.0)
        d80 = brentq(lambda d: rule(alpha_s, r, d) - 0.80, 0.1, 10)
        d_pool = brentq(lambda d: norm.cdf(d / sqrt(r) - za) - 0.80, 0.1, 10)
        print(f"screen {alpha_s:.2f} r {r:.3f}: alpha_eff {a_eff:.6f}; MDE {d80:.4f} SE_12; Daten vs C.10 je 0,80 {(d80/c_c10)**2:.4f}; vs gepoolt ohne Screen {(d80/d_pool)**2:.4f}; Boden {(norm.ppf(1-alpha_s)+zb):.4f}")
# P-6-Lesart: gepoolt 0,0025 und unabhaengiger Stabilitaetstest mit Power 0,95 -> gemeinsame Power 0,80 => Pool-Power 0,8/0,95
p_pool = 0.80 / 0.95
for r in (0.5, 1/3, 0.25):
    d = (za + norm.ppf(p_pool)) * sqrt(r)
    d_pool = (za + zb) * sqrt(r)
    print(f"P-6-Lesart r {r:.3f}: MDE {d:.4f} SE_12, Daten vs gepoolt {(d/d_pool)**2:.4f}, vs C.10 je 0,80 {(d/c_c10)**2:.4f}, alpha {0.0025*0.95:.6f}")
# A2 Boden
print("A2 Boden (1,6449 + Phi^-1(0,8/0,9025)) x 8,52 =", round((norm.ppf(0.95) + norm.ppf(0.8/0.9025)) * 8.52, 3))
# Klasse W Boden bei SD 0,13 / 0,09 je Woche, 52 Wochen
for sd in (0.13, 0.09):
    print(f"Klasse W SD {sd}: Boden {c_c10*sd/sqrt(52):.4f}; Wochen bis SESOI 0,040 gepoolt 0,0025: {((za+zb)*sd/0.040)**2:.1f}")
