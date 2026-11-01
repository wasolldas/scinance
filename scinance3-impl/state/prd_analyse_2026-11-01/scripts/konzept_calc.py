"""Analytische Rechnungen fuer KONZEPT_UND_FORSCHUNGSFELDER.md.
Nur Formeln + bekannte Nuisance-Zahlen aus der Akte; keine Daten, kein Netz."""
import math
from statistics import NormalDist
import numpy as np
N = NormalDist()
Z_KRIT = N.inv_cdf(0.95)          # 1.6449
Z_POW = N.inv_cdf(0.80)           # 0.8416
MDE_F = Z_KRIT + Z_POW            # 2.4865
Z_POOL = 2.5287 + Z_POW           # DEC-52 gepoolt unter P-1
print(f"z_krit {Z_KRIT:.4f} mde_f {MDE_F:.4f} pooled_mde_f {Z_POOL:.4f}")

print("\n== 1. Tages-Zeitreihen-IC (Rank-IC Praediktor_t vs Rendite_t+1), SE ~ 1/sqrt(N) ==")
print("N | MDE80 ein Fenster | MDE80 je Fenster bei C.10 (N/2) | MDE80 gepoolt DEC-52 | bp/Tag bei sigma 262 (ein Fenster/C.10) | bei sigma 210")
for Nd in (480, 970, 1200, 2000, 2130, 2400):
    m1 = MDE_F/math.sqrt(Nd); m2 = MDE_F/math.sqrt(Nd/2); mp = Z_POOL/math.sqrt(Nd)
    print(f"{Nd:5d} | {m1:.4f} | {m2:.4f} | {mp:.4f} | {0.798*262*m1:5.1f} / {0.798*262*m2:5.1f} | {0.798*210*m1:5.1f} / {0.798*210*m2:5.1f}")
print("gemeinsame Power C.10 bei wahrem Effekt = je-Fenster-MDE80:", round(0.8**2,2))
print("BTC+ETH gepoolt, rho 0.8 (DEC-67 0.815): N_eff-Faktor", round(2/(1+0.815),3))

print("\n== 2. Kostendeckung: IC_min = Kosten_RT * Umschlag / (0.798*sigma_1d) ==")
for sig in (262, 210):
    for c in (4.0, 11.0, 15.0):
        row = [c*tau/(0.798*sig) for tau in (1.0, 0.5, 0.33)]
        print(f"sigma {sig} Kosten {c:4.1f} bp: Umschlag 1/0.5/0.33 -> IC_min {row[0]:.3f} / {row[1]:.3f} / {row[2]:.3f}")
print("Vorzeichenwechsel-Rate eines AR(1)-Gauss-Signals je Tag = arccos(phi)/pi:",
      {phi: round(math.acos(phi)/math.pi,3) for phi in (0.0,0.3,0.5,0.8,0.9)})
print("Trefferquote p aus IC (Gauss): p = 0.5 + arcsin(IC)/pi:", {ic: round(0.5+math.asin(ic)/math.pi,3) for ic in (0.03,0.05,0.07,0.10,0.156)})

print("\n== 3. Tages-Querschnitt auf dem Perp-Panel (kline1d ALL 2021-01..2026-10, ~2130 Tage) ==")
for K in (300, 500):
    floor = 1/math.sqrt(K-1)
    for fac in (1.0, 2.5):
        sd = floor*fac
        for Nd in (730, 1065, 2130):
            mde = MDE_F*sd/math.sqrt(Nd)
            bp = 3.51*mde*370   # sigma_xs_daily ~ 9.85%/sqrt(7) = 3.7% = 370 bp (Annahme)
            print(f"K {K} Boden {floor:.4f} x{fac} -> SD(IC_t) {sd:.4f}; N {Nd}: MDE80 {mde:.4f} -> Dezil-L/S brutto {bp:.1f} bp/Tag")

print("\n== 4. Ereignisstudien ==")
for name, n, sd in (("Delisting (letzter Handelstag), Alt-Tagesvol 650 bp", 300, 650),
                    ("Delisting-Ankuendigung, Alt-Tagesvol 650 bp", 300, 650),
                    ("Listing Tag 1..5, Alt-Tagesvol 900 bp", 800, 900),
                    ("FOMC 1-Tages-Fenster BTC (6 J x 8)", 48, 262),
                    ("FOMC 30-min-Slot 18:00 UTC, Slot-SD ~74 bp (A2-Profil 12:30-14:00 als Proxy)", 48, 74),
                    ("CPI 30-min-Slot 12:30 UTC, Slot-SD 74 bp", 72, 74),
                    ("CPI 1-Tag", 72, 262),
                    ("A2 Freitage mit GEX seit 2026-06 (bis 2027-06), Freitags-SD 43.8", 52, 43.8),
                    ("dto. bis 2028-06", 104, 43.8),
                    ("dto. nur oberstes OI-Dezil der Freitage bis 2028-06", 10, 43.8)):
    se = sd/math.sqrt(n)
    print(f"{name}: N {n}, SE {se:.1f} bp, MDE80 {MDE_F*se:.1f} bp (ein Fenster); C.10 je Haelfte {MDE_F*sd/math.sqrt(n/2):.1f} bp")

print("\n== 5. OI / Funding / Stablecoin als Tages-Praediktor (Zeitreihe) ==")
for name, n in (("OI Bybit BTC/ETH seit 2024-03", 970), ("Funding alle Perps seit 2021-01", 2130),
                ("Stablecoin-Supply (DefiLlama, ab ~2021)", 1800), ("DVOL seit 2021-03", 2048), ("binance OI seit 2026-05", 165)):
    print(f"{name}: N {n} -> MDE80 IC {MDE_F/math.sqrt(n):.4f} (ein Fenster), {MDE_F/math.sqrt(n/2):.4f} (C.10 je Haelfte)")
print("VRP als Monatspraediktor (BTZ-Typ), 68 nicht ueberlappende Monate:", f"r_min {MDE_F/math.sqrt(68):.3f} -> R^2 {(MDE_F/math.sqrt(68))**2:.3f}")

print("\n== 6. Selektionsdecke (Bailey/LdP) E[max z] ueber K Varianten ==")
g = 0.5772
for K in (3, 5, 10, 20, 50):
    emax = (1-g)*N.inv_cdf(1-1/K) + g*N.inv_cdf(1-1/(K*math.e))
    print(f"K {K}: E[max z] {emax:.3f}  (gegen z_krit 1.6449)")

print("\n== 7. Gruppensequentiell (O'Brien-Fleming-artig), einseitig alpha 0.05, Monte Carlo ==")
rng = np.random.default_rng(7)
def gs_sim(K, drift, c, n=200000, futility=None):
    # Brownian: Z_k = (B(t_k)) / sqrt(t_k), t_k = k/K ; drift in units of final-z (theta*sqrt(1)=theta)
    inc = rng.normal(size=(n, K))/math.sqrt(K) + drift/K
    B = np.cumsum(inc, axis=1)
    t = np.arange(1, K+1)/K
    Z = B/np.sqrt(t)
    bound = c/np.sqrt(t)   # OBF: constant on B-scale
    stop_eff = np.full(n, K+1); stop_fut = np.full(n, K+1)
    for k in range(K):
        hit = (Z[:, k] >= bound[k]) & (stop_eff == K+1) & (stop_fut == K+1)
        stop_eff[hit] = k+1
        if futility is not None:
            fut = (B[:, k] < futility[k]) & (stop_eff == K+1) & (stop_fut == K+1)
            stop_fut[fut] = k+1
    rejected = stop_eff <= K
    stop = np.minimum(np.minimum(stop_eff, stop_fut), K)
    return rejected.mean(), stop.mean()/K
for K in (4, 8):
    # kalibriere c so, dass alpha 0.05 unter H0
    lo, hi = 1.5, 3.5
    for _ in range(30):
        c = (lo+hi)/2
        a, _ = gs_sim(K, 0.0, c, n=100000)
        if a > 0.05: lo = c
        else: hi = c
    c = (lo+hi)/2
    a0, _ = gs_sim(K, 0.0, c)
    # Drift so, dass fixed design Power 0.80 hat: theta = 2.4865 (in z-Einheiten der vollen Information)
    theta = MDE_F
    p1, et1 = gs_sim(K, theta, c)
    # mit Futility: B(t) < 0 ab halber Information (nicht bindend, aber verwendet)
    fut = [(-np.inf if (k+1)/K < 0.5 else 0.0) for k in range(K)]
    p2, et2 = gs_sim(K, theta, c, futility=fut)
    p0f, et0f = gs_sim(K, 0.0, c, futility=fut)
    print(f"K={K} Looks: c_OBF(B-Skala) {c:.3f} (final z-Grenze {c:.3f}, erste Grenze {c*math.sqrt(K):.2f}); alpha {a0:.4f}; "
          f"Power am Fixed-MDE {p1:.3f}, E[Info-Anteil] {et1:.3f}; mit Futility: Power {p2:.3f}, E[Info] H1 {et2:.3f}, E[Info] H0 {et0f:.3f}")
    # Max-Information-Inflation: finde theta, bei dem Power 0.80 erreicht wird
    lo, hi = 1.5, 4.0
    for _ in range(25):
        th = (lo+hi)/2
        p, _ = gs_sim(K, th, c, n=100000)
        if p < 0.80: lo = th
        else: hi = th
    th = (lo+hi)/2
    print(f"   Drift fuer Power 0.80: {th:.3f} gegen fixed {MDE_F:.3f} -> Max-Informations-Inflation {(th/MDE_F)**2:.3f}")

print("\n== 8. Zwei-Fenster-Regel vs. gruppensequentiell bei gleicher Fehlerrate ==")
# C.10: zwei Fenster je alpha 0.05, gemeinsame Rate 0.0025, gemeinsame Power 0.64 bei je-Fenster-MDE.
# Ein Fenster mit alpha 0.0025: z_krit
zk = N.inv_cdf(1-0.0025)
print(f"ein Fenster alpha 0.0025: z_krit {zk:.3f}, MDE-Faktor {zk+Z_POW:.3f} auf voller Information N; C.10 je Fenster {MDE_F:.3f} auf N/2 -> entspricht {MDE_F*math.sqrt(2):.3f} auf N")
print(f"Verhaeltnis Datenbedarf C.10 (Power 0.64 gemeinsam) zu Einfenster alpha 0.0025 (Power 0.80): {(MDE_F*math.sqrt(2)/(zk+Z_POW))**2:.3f}")

print("\n== 9. Ausschlussgrenze (obere 95-%-Schranke) statt binaerem DROP ==")
for Nd in (1000, 2000, 2400):
    print(f"N {Nd}: bei beobachtetem IC 0 liegt die einseitige 95-%-Obergrenze bei {Z_KRIT/math.sqrt(Nd):.4f} ({0.798*262*Z_KRIT/math.sqrt(Nd):.1f} bp/Tag bei sigma 262)")

print("\n== 10. Wochen-Querschnitt (A3) zum Vergleich: IC 0.03, sigma_xs 9.85 %, f 3.51 ==")
print(f"Brutto {3.51*0.03*985:.0f} bp/Woche gegen 18 bp Wochenkosten (Turnover 0.6, Taker) -> Faktor {3.51*0.03*985/18:.1f}")
print(f"Tages-TS-IC 0.05 auf BTC: {0.798*262*0.05*7:.0f} bp/Woche brutto gegen 7 RT/Woche Taker 77 bp / Maker 28 bp")
