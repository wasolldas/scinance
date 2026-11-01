"""Gegenrechnung des adversarischen Reviews (nur Formeln/Simulation, keine Marktdaten).
Eingangszahlen ausschliesslich aus der Akte bzw. den geprueften Analysen."""
import math
import numpy as np
from scipy.stats import norm, multivariate_normal, spearmanr
Phi, Pinv = norm.cdf, norm.ppf
z95, z80 = Pinv(0.95), Pinv(0.80)
F = z95 + z80
k = math.sqrt(2/math.pi)
P = print

P("== A. K-1 Horizont-Friktions-Kurve ==")
for ic in (0.01, 0.03, 0.05, 0.10, 0.156):
    prd = (2/math.pi)*math.asin(ic)
    P(f"IC {ic}: Gauss/PRD-Kante {ic/prd:.4f}; Spearman-IC (Pearson=2sin(pi r/6)) / PRD {2*math.sin(math.pi*ic/6)/prd:.4f}")
P("Grenzwerte pi/2 =", round(math.pi/2,4), " Horizont x", round((math.pi/2)**2,3), "; Spearman pi^2/6 =", round(math.pi**2/6,4), " Horizont x", round((math.pi**2/6)**2,3))
s1d = 262.0
e_prd = lambda ic: (2/math.pi)*math.asin(ic)*k*s1d
P("PRD IC 0,05: Kante/Tag", round(e_prd(0.05),3), "bp; Taker 11 -> ", round((11/e_prd(0.05))**2,3), "Tage; Maker 4 ->", round(24*(4/e_prd(0.05))**2,2), "h (PRD nennt ~7 h)")
P("Gauss IC 0,05: Taker", round((11/(0.05*k*s1d))**2,3), "Tage; Maker 5,4 ->", round((5.4/(0.05*k*s1d))**2,3), "Tage")
p = 0.55; rho = math.sin(math.pi*(p-0.5))
P("p 0,55: PRD", round(24*(11/((2*p-1)*k*s1d))**2,2), "h; Gauss (rho", round(rho,4), ")", round(24*(11/(rho*k*s1d))**2,2), "h")
s1w = s1d*math.sqrt(7)
P("Break-even Wochen-IC PRD", round(math.sin(math.pi/2*11/(k*s1w)),4), " Gauss", round(11/(k*s1w),4))
rng = np.random.default_rng(11)
n = 4_000_000; r = 0.05
x = rng.standard_normal(n); y = r*x + math.sqrt(1-r*r)*rng.standard_normal(n)
P("MC bivariat normal rho 0,05: E[y sign(x)] =", round(np.mean(y*np.sign(x)),5), " Theorie rho*0,798 =", round(r*k,5), " PRD-Formel", round((2/math.pi)*math.asin(r)*k,5))

P("\n== B. K-2 Lo / Praemientest ==")
T = lambda sr, q: F**2*(1+sr**2/(2*q))/sr**2
P("SR 2: q365", round(T(2,365),3), " q12", round(T(2,12),3), " Kurzform", round(F**2/4,3))
for prior in (9.47, 7.14, 10.48, 3.16):
    se = 18.6*math.sqrt(28.2/365); sr = prior/se
    P(f"VRP prior {prior}: SR_eff {sr:.3f} -> Jahre je Fenster {(F/sr)**2:.3f} = {365*(F/sr)**2:.0f} Tage")
P("A1 theta 1: SR_eff", round(100.7/(372.9/math.sqrt(52)),3))
for L in (1,2,3): P("SR_eff noetig bei L Jahren", L, round(F/math.sqrt(L),3))

P("\n== C. K-4 C.10 vs gepoolt ==")
zj = Pinv(1-0.0025)
P("gepoolt alpha 0,0025 Power bei C.10-MDE:", round(Phi(F*math.sqrt(2)-zj),3))
pw = math.sqrt(0.8); P("C.10 gemeinsame Power 0,80 -> je Fenster", round(pw,4), " Datenfaktor", round(((z95+Pinv(pw))/F)**2,4))
P("gepoolt 0,0025/0,80 gegen C.10 0,80/0,80:", round((zj+z80)**2/(2*F**2),4), "; C.10(0,894 je Fenster) gegen gepoolt 0,0025/0,80:", round(2*(z95+Pinv(pw))**2/(zj+z80)**2,4))
m = 4_000_000; z1 = rng.standard_normal(m); z2 = rng.standard_normal(m); zp = (z1+z2)/math.sqrt(2)
for zc in (2.3263, 2.5287):
    a1 = np.mean((zp>=zc)&(z1>0)&(z2>0)); a2 = np.mean((zp>=zc)&(z1>=0.5*zc/math.sqrt(2))&(z2>=0.5*zc/math.sqrt(2)))
    P(f"DEC-52 H0-Rate z {zc}: nur Vorzeichen {a1:.5f}; mit Screens (je Fenster >= 0,5 z_krit SE_gepoolt, DEC-94 (6)) {a2:.5f}")
P("K-0.6: Phi(1,4-1,6449)^2 =", round(Phi(1.4-z95)**2,4), " Retention-Faktor", round(Phi(1.4)**2/Phi(1.4-z95)**2,2))

P("\n== D. K-5 Produkt vs exakt (Illustration K-5 (b)) ==")
sE, sP = 6.5, np.array([3.4, 4.5, 1.5]); seD = np.sqrt(sE**2+sP**2)
C = np.full((3,3), sE**2) + np.diag(sP**2); R = C/np.outer(seD, seD)
for d in (20.0, 22.0):
    pw_i = Phi(d/seD - z95); prod = pw_i.prod()
    up = d/seD - z95
    joint = multivariate_normal(mean=np.zeros(3), cov=R).cdf(up)
    P(f"delta {d}: Einzel {np.round(pw_i,3)}, Produkt {prod:.3f}, exakt gemeinsam {joint:.3f}; Korrelationen {np.round(R[np.triu_indices(3,1)],3)}")
for mm in (2,3,5):
    q = 0.8**(1/mm); f = (z95+Pinv(q))/F
    P(f"m {mm}: je Bedingung {q:.4f}, MDE x{f:.3f}, Daten x{f*f:.3f}")
P("A2-Kette W2: 24,4 + Stress 2,8 =", 24.4+2.8, "+ skal. Null 2,1 =", round(24.4+2.8+2.1,1), "+ Gate(4) 2,8 =", round(24.4+2.8+2.1+2.8,1))
P("Datenfaktoren gegen 18,8:", {v: round((v/18.8)**2,3) for v in (19.7,23.1,23.77,24.4,27.2,29.3,32.1)})
# Null-Faktor bei Korrelation rho_m statt 1: P(beide) vs Produkt, je Einzelpower 0,9
for rc in (0.82, 0.91, 1.0):
    u = Pinv(0.9)
    j = multivariate_normal(mean=[0,0], cov=[[1,rc],[rc,1]]).cdf([u,u]) if rc<1 else 0.9
    P(f"zwei Bedingungen je Power 0,9, Korrelation {rc}: exakt {j:.3f} gegen Produkt 0,810")

P("\n== E. K-6 PPV / A2 gepoolt ==")
for a, pwr, lab in ((0.0025, 0.64, "C.10"), (0.01, 0.80, "gepoolt 0,01"), (0.05, 0.80, "ein Fenster")):
    P(lab, [round(pwr*b/(pwr*b+a*(1-b)),3) for b in (0.05,0.10,0.20)])
sep = 1/math.sqrt(1/7.34**2+1/7.58**2); sep_eq = math.sqrt(7.34**2+7.58**2)/2
for a in (0.01, 0.0025):
    P(f"A2 P2'' gepoolt alpha {a}: MDE80 (inv.-var.) {(Pinv(1-a)+z80)*sep:.2f}, (gleichgew.) {(Pinv(1-a)+z80)*sep_eq:.2f}; Power bei 16,5 {Phi(16.5/sep_eq-Pinv(1-a)):.3f}")
for sw1, sw2, lab in ((0.090,0.061,"measured"),(0.130,0.082,"stress")):
    s1, s2 = sw1/math.sqrt(52), sw2/math.sqrt(52); se = math.sqrt(s1**2+s2**2)/2
    P(f"A3 Roh-IC {lab}: je Fenster MDE80 W1 {F*s1:.4f} W2 {F*s2:.4f}; gepoolt alpha 0,01 {(Pinv(0.99)+z80)*se:.4f}")

P("\n== F. K-9 Pilot-Uebergabe A2 ==")
for mu in (16.5, 25.0, 32.1):
    P(f"mu {mu}: P(x_P >= 32,1 | SE 4,10) = {1-Phi((32.1-mu)/4.10):.2e}")
P("Pilot-alpha bei c 32,1:", f"{1-Phi(32.1/4.10):.2e}", "; bei c 24,36:", f"{1-Phi(24.36/4.10):.2e}")


P("\n== G. Gruppensequentiell exakt (Gitterintegration, OBF auf B-Skala konstant) ==")
def oc(C, theta, K, fut_looks=(), f=0.0, h=0.002):
    t = np.arange(1, K+1)/K; dt = 1.0/K; sd = math.sqrt(dt)
    grid = np.arange(-9.0, 9.0 + max(theta,0)*1.0 + h, h)
    m = int(round(7*sd/h)); offs = np.arange(-m, m+1)*h
    kern = norm.pdf(offs, theta*dt, sd)*h
    dens = None; prej = 0.0; Et = 0.0
    for i in range(K):
        if i == 0:
            d = norm.pdf(grid, theta*dt, sd)
        else:
            d = np.convolve(dens, kern, mode="same")
        rej = grid >= C
        fut = (grid < f*math.sqrt(t[i])) if (i in fut_looks and i < K-1) else np.zeros_like(rej)
        pr = d[rej].sum()*h; prej += pr
        if i < K-1:
            ps = d[rej | fut].sum()*h
            Et += t[i]*ps
            dens = np.where(~rej & ~fut, d, 0.0)
        else:
            Et += t[i]*d.sum()*h
    return prej, Et
def calib(K, alpha):
    lo, hi = 1.0, 4.5
    for _ in range(50):
        c = (lo+hi)/2
        a, _ = oc(c, 0.0, K)
        lo, hi = (c, hi) if a > alpha else (lo, c)
    return (lo+hi)/2
def design(K, alpha, fut_looks=(), f=0.0):
    c = calib(K, alpha); th_fix = Pinv(1-alpha) + z80
    lo, hi = th_fix*0.9, th_fix*1.5
    for _ in range(45):
        th = (lo+hi)/2; pw, _ = oc(c, th, K, fut_looks, f)
        lo, hi = (th, hi) if pw < 0.8 else (lo, th)
    th = (lo+hi)/2; R = (th/th_fix)**2
    _, e1 = oc(c, th, K, fut_looks, f); _, e0 = oc(c, 0.0, K, fut_looks, f); _, e2 = oc(c, 2*th, K, fut_looks, f)
    pwfix, efix = oc(c, th_fix, K, fut_looks, f)
    a0, _ = oc(c, 0.0, K)
    return dict(c=round(c,4), alpha=round(a0,5), R=round(R,4), EN_H1=round(R*e1,3), EN_H0=round(R*e0,3), EN_2x=round(R*e2,3),
                power_at_fixed_MDE=round(pwfix,3), Einfo_at_fixed_MDE_noinfl=round(efix,3))
for K in (2, 4, 8):
    for a in (0.05, 0.0025):
        P(f"OBF K={K} alpha={a}: ", design(K, a))
P("mit Futility Z<0 an Blicken 1..K-1 (KRITIK-Variante), Grenze ohne Futility kalibriert:")
for a in (0.05, 0.0025):
    P(f"  K=4 alpha={a}: ", design(4, a, fut_looks=(0,1,2), f=0.0))
P("mit Futility Z<0 ab halber Information (KONZEPT-Variante, Blicke 2,3 von 4):")
for a in (0.05, 0.0025):
    P(f"  K=4 alpha={a}: ", design(4, a, fut_looks=(1,2), f=0.0))

P("\n== H. Vergleich KONZEPT T-12 'ein Drittel bei gleicher Fehlerrate' ==")
N05 = F**2; N0025 = (Pinv(1-0.0025)+z80)**2
P("Fixed-Einheiten (in N_0,05):", "C.10 0,80/0,80 je Fenster: 2,000; C.10 gemeinsam 0,80:", round(2*((z95+Pinv(math.sqrt(0.8)))/F)**2,3),
  "; ein Fenster alpha 0,0025 Power 0,80:", round(N0025/N05,3))

P("\n== I. ARCHITEKTUR Kohorten-Faktor (Bonferroni je Fenster) ==")
for mm in (1,2,4,8,12):
    P(mm, round(((Pinv(1-0.05/mm)+z80)/F)**2,3))

P("\n== J. KONZEPT T-9 / F1 ==")
for Nd in (365, 480, 970, 2000, 2130, 2400):
    P(f"N {Nd}: MDE80 TS {F/math.sqrt(Nd):.4f}; C.10 je Haelfte {F/math.sqrt(Nd/2):.4f}; 95%-Obergrenze bei IC 0 {z95/math.sqrt(Nd):.4f}")
for phi in (0.0, 0.5, 0.8):
    q = math.acos(phi)/math.pi
    P(f"phi {phi}: Vorzeichenwechsel/Tag {q:.3f}; Taker-IC_min {11*q/(k*262):.4f}; Maker {4*q/(k*262):.4f}")
for K in (300, 500, 600):
    fl = 1/math.sqrt(K-1)
    for Nd, lab in ((365,"W1 oder W2 je Fenster"), (1065,"C.10-Haelfte aller 2.130 Tage"), (2130,"alle 2.130 Tage")):
        mde = F*2.5*fl/math.sqrt(Nd)
        P(f"K {K}: SD 2,5xBoden {2.5*fl:.4f}; {lab}: MDE80 {mde:.4f} (L/S brutto {3.51*mde*370:.1f} bp/Tag)")
P("Bianchi Weg A: EW", round(2.187/(3.51*6.889),4), " VW", round(0.558/(3.51*6.889),4), "; EW t ~", round(0.37*math.sqrt(1827),1), " VW t ~", round(0.061*math.sqrt(1827),2))

P("\n== K. EDGE R-1 ==")
for lab, x, sd in (("mom1",0.03847,0.12351),("mom2",0.05003,0.13015),("mom4",0.04463,0.13415)):
    ir = x/sd*math.sqrt(52)
    for share in (1.0, 0.75, 0.5):
        n = (F*sd/(share*x))**2
        if share == 1.0:
            P(f"{lab}: Informationsrate {ir:.3f}/Jahr; Wochen je Fenster {n:.1f}; Power je 52 Wochen {Phi(ir - z95):.3f}")
        else:
            P(f"   Anteil {share}: {n:.1f} Wochen")
P("Literatur 0,014 mom1:", round((F*0.12351/0.014)**2,0), "Wochen")
P("Vergleich Literatur-IR: Ficura L&L 1W t 2,332 / 291 W ->", round(2.332*math.sqrt(52/291),2), "; Ficura S/I -7,309 ->", round(7.309*math.sqrt(52/291),2),
  "; LTW Terzil t 3,719 / 260 W ->", round(3.719*math.sqrt(52/260),2), "; Bianchi VW taeglich ->", round(0.061*math.sqrt(365),2), " EW", round(0.37*math.sqrt(365),2))
import datetime as dt_
for w in (41.8, 63.7):
    P(f"2 x {w} Wochen ab 2026-10-05 -> {dt_.date(2026,10,5)+dt_.timedelta(days=round(2*w*7)-1)}; ab 2026-07-06 -> {dt_.date(2026,7,6)+dt_.timedelta(days=round(2*w*7)-1)}")

P("\n== L. K-10 SESOI ==")
P("zweiseitig: MDE x", round((Pinv(0.975)+z80)/F,4), " Daten x", round(((Pinv(0.975)+z80)/F)**2,4))
P("A1 Jahre je Fenster bei SESOI 36:", round((F*372.9/math.sqrt(52)/36)**2,2))
for ses in (22.0, 10.8):
    P(f"A2 SESOI {ses}: Einzel 18,8 {'ok' if 18.8<=ses else 'nein'}; exakt gemeinsam W2 22,3 {'ok' if 22.3<=ses else 'nein'}; Produkt zentral 24,4 {'ok' if 24.4<=ses else 'nein'}; stress 27,2 {'ok' if 27.2<=ses else 'nein'}")

P("\n== M. K-3 Identitaet des Permutations-Bodens (Faktorwelt) ==")
K_ = 200; W = 3000
sds = []
for load in (0.0, 0.9):
    ics = []
    for w in range(W):
        f = rng.standard_normal(); beta = rng.lognormal(0, 0.5, K_)
        vol = rng.lognormal(0, 0.6, K_)
        ret = load*beta*f + vol*rng.standard_normal(K_)
        ch = rng.permutation(K_).astype(float)
        ics.append(spearmanr(ch, ret)[0])
    sds.append(np.std(ics))
P("SD Spearman(perm, Rendite) ohne/mit starkem Faktor:", np.round(sds,4), " Identitaet 1/sqrt(K-1) =", round(1/math.sqrt(K_-1),4))
