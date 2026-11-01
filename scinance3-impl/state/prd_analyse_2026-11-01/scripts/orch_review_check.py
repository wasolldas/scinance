# Orchestrator-Nachrechnung der Review-Kernzahlen (nur Formeln und Simulation, keine Marktdaten).
import numpy as np
from math import sqrt, acos, pi
from scipy.stats import norm, multivariate_normal

z_a = norm.ppf(0.95); z_b = norm.ppf(0.80); c80 = z_a + z_b
print("c80 =", round(c80, 4))

# (1) Zwei Bedingungen je Power 0,90, gemeinsame Power bei Korrelation rho (bivariat normal, einseitig)
def joint_power(p_each, rho):
    # Jede Bedingung: P(Z_i > z_a - delta_i) = p_each -> delta = z_a - Phi^-1(1-p_each)
    d = z_a - norm.ppf(1 - p_each)
    cov = [[1, rho], [rho, 1]]
    # P(Z1 > z_a-d, Z2 > z_a-d) = P(Z1 < d-z_a, Z2 < d-z_a) by symmetry
    return multivariate_normal(mean=[0, 0], cov=cov).cdf([d - z_a, d - z_a])
for rho in (0.82, 0.91, 0.999999):
    print("gemeinsame Power je 0,90, rho", rho, "->", round(joint_power(0.90, rho), 3), "(Produkt 0,810)")

# (2) VRP H-27: SE 12 Monate, SR_eff, Tage je Fenster
se12 = 18.6 * sqrt(28.2 / 365)
for prior in (9.47, 7.14, 10.48, 3.16):
    sr = prior / se12
    years = (c80 / sr) ** 2
    print(f"VRP Prior {prior}: SE12 {se12:.3f}, SR_eff {sr:.3f}, Jahre je Fenster {years:.3f} = {years*365:.0f} Tage")

# (3) F1 MDE80 je Fenster (365 Tage) bei SD(IC_t) = 2,5/sqrt(K-1)
for K in (600, 500, 300):
    for N in (365, 730, 2130):
        print(f"F1 K {K} N {N}: MDE80 {c80*2.5/sqrt((K-1)*N):.4f}")

# (4) BTC/ETH Tages-Zeitreihe: MDE80 und Ausschlussgrenze
for N in (2400, 2000, 365):
    print(f"TS N {N}: MDE80 {c80/sqrt(N):.4f}, Ausschluss95 {z_a/sqrt(N):.4f}, bp/Tag MDE {c80/sqrt(N)*0.798*262:.1f}")

# (5) Taker/Maker IC_min nach Vorzeichenwechselrate AR(1)
for phi in (0.0, 0.5, 0.8):
    w = acos(phi) / pi
    print(f"phi {phi}: Wechselrate {w:.3f}, IC_min Maker4 {4*w/(0.798*262):.4f}, Taker11 {11*w/(0.798*262):.4f}, gesamt15 {15*w/(0.798*262):.4f}")

# (6) OBF gruppensequentiell, 4 Blicke, einseitig; MC mit 2 Mio Pfaden
def obf(alpha, power=0.80, K=4, n=2_000_000, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(1, K + 1) / K
    # OBF-Grenzen: c/sqrt(t); c so, dass P(irgendein Z_k > c/sqrt(t_k) | H0) = alpha
    inc = rng.standard_normal((n, K)) * sqrt(1 / K)
    B = np.cumsum(inc, axis=1)              # Brownsche Bewegung an t_k
    Z0 = B / np.sqrt(t)
    def cross_prob(c, theta=0.0):
        Z = Z0 + theta * np.sqrt(t)
        return np.mean((Z > c / np.sqrt(t)).any(axis=1))
    lo, hi = 1.0, 5.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if cross_prob(mid) > alpha: lo = mid
        else: hi = mid
    c = (lo + hi) / 2
    # Drift theta (in Einheiten von sqrt(I_max)): Power 0,80
    lo, hi = 0.5, 8.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if cross_prob(c, mid) < power: lo = mid
        else: hi = mid
    theta = (lo + hi) / 2
    # Fixed-sample Information fuer gleiche alpha/Power: (z_a+z_b)^2/delta^2 ; hier I_max*theta^2 = ... Verhaeltnis R = I_max/I_fix
    z_alpha = norm.ppf(1 - alpha)
    R = (theta / (z_alpha + z_b)) ** 2
    # erwartete Information unter H1 relativ zu I_fix
    Z = Z0 + theta * np.sqrt(t)
    crossed = Z > c / np.sqrt(t)
    first = np.where(crossed.any(axis=1), crossed.argmax(axis=1) + 1, K)
    EN_H1 = np.mean(first / K) * R
    EN_H0 = R  # ohne Futility
    return c, R, EN_H1
for alpha in (0.05, 0.0025):
    c, R, en = obf(alpha)
    print(f"OBF K4 alpha {alpha}: c {c:.3f}, Maximum/fix {R:.3f}, E[N|H1]/fix {en:.3f}")

# (7) PPV / erwartete Falsch-PASS je Jahr
for name, a, pw in (("C.10 heute (gemeinsam 0,64)", 0.0025, 0.64), ("gepoolt 0,0025 Power 0,80", 0.0025, 0.80), ("gepoolt 0,01 Power 0,80", 0.01, 0.80), ("ein Fenster alpha 0,05", 0.05, 0.80)):
    for base in (0.10, 0.25):
        ppv = pw * base / (pw * base + a * (1 - base))
        print(f"{name}: Basisrate {base}: PPV {ppv:.3f}; Falsch-PASS/Jahr bei 10 Nulltests {10*a:.3f}")

# (8) Datenfaktoren
print("C.10 gemeinsam 0,80 vs je 0,80:", round(((z_a + norm.ppf(sqrt(0.8))) / c80) ** 2, 3))
print("gepoolt 0,0025 vs C.10 je 0,80 (Power 0,80):", round(((norm.ppf(1 - 0.0025) + z_b) / c80) ** 2 / 2, 3))
print("C.10 gemeinsam 0,80 vs gepoolt 0,0025:", round(2 * ((z_a + norm.ppf(sqrt(0.8))) / (norm.ppf(1 - 0.0025) + z_b)) ** 2, 3))
