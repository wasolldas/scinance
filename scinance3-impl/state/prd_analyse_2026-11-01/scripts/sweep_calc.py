"""Methoden-Sweep 2026-11-02: analytic order-of-magnitude calculations.

Formulas only. Inputs are file numbers (marked F), own assumptions (marked V)
or secondary literature orientation values (marked SEK). No market data is
loaded; no sealed file is opened. Output: sweep_calc.out (same directory).
"""
import math
import numpy as np
from scipy import stats

Z = stats.norm.ppf
PHI = stats.norm.pdf
out = []


def p(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)
    print(s)


def hdr(t):
    p("")
    p("=" * 78)
    p(t)
    p("=" * 78)


z0025 = Z(1 - 0.0025)
z05 = Z(1 - 0.05)
z80 = Z(0.80)

# ---------------------------------------------------------------------------
hdr("A. Datenvolumen und Transferzeit (Inventar 2026-11-01 [F]; 2 MB/s [F Verfassung, Marktdaten])")
inv = {
    # stream: (GB, partitions, rows, days_span)
    "bybit/publicTrade": (309.26, 10519, 7035351849),
    "bybit/orderbook": (377.14, 2006, 1433565543),
    "tardis/options_chain": (386.63, 91, 5273863331),
    "binance/publicTrade": (46.23, 1486, 3255597900),
    "deribit/tickers": (542.12, 216243, 12050245836),
    "bybit/tickers": (504.61, 154306, 12395614446),
    "deribit/publicTrade": (3.12, 1004, 96988365),
}
MBps = 2.0
for k, (gb, parts, rows) in inv.items():
    mb_part = gb * 1000 / parts
    full_h = gb * 1000 / MBps / 3600
    p(f"{k:24s} {gb:8.2f} GB  {parts:7d} Part.  {mb_part:9.1f} MB/Part.  "
      f"{rows/parts/1e6:8.2f} Mio Zeilen/Part.  "
      f"{gb*1e9/rows:6.1f} Byte/Zeile  ganzer Strom {full_h:6.1f} h")
p("BTC publicTrade aktuell ~28 GB je Symbol-Jahr [F DEC-96 N] ->",
  f"{28e3/365:.1f} MB/Tag -> {28e3/365/MBps:.0f} s je BTC-Tag")
p("orderbook.500 0,4..1,3 GB/Tag [F WP-1] ->",
  f"{400/MBps/60:.1f}..{1300/MBps/60:.1f} min je BTC-Tag")
p("tardis 386,63 GB / 91 Tage ->", f"{386.63/91:.2f} GB/Tag ->",
  f"{386.63/91*1000/MBps/60:.1f} min/Tag; Zone X Stichtage 2019-04..2024-06 =",
  9 + 4 * 12 + 6, "(2019: 9, 2020-2023: 48, 2024: 6)")
# sampling plans
plans = [
    ("K-01 Trades 5 Symb., 2 Tage/Monat 2020-03..2024-06 + Stress", 5 * 104 + 40, 35.0),
    ("K-02 L2 BTC/ETH 40 Tage Zone X", 40, 850.0),
    ("K-06 Tardis 24 Stichtage, Spaltenauswahl 50 % [V]", 24, 4249.0 * 0.5),
    ("K-06 Tardis alle 63 Zone-X-Stichtage, 50 % [V]", 63, 4249.0 * 0.5),
    ("K-08 S0-Metadaten aller Stroeme (Katalog)", 1, 1.0),
]
for name, n, mb in plans:
    gb = n * mb / 1000
    p(f"Plan {name:58s}: {n:4d} Einheiten x {mb:7.1f} MB = {gb:7.1f} GB -> {gb*1000/MBps/3600:6.1f} h Transfer")

# ---------------------------------------------------------------------------
hdr("B. K-10 Tages-Querschnitts-IC (Price Delay): MDE80 und SESOI")
p("Annahme SD(IC_t) = 2,5/sqrt(K-1) [V, wie F1-Zeile PRD_ANALYSE; GL-035 2,3..2,6x]")


def joint_mde(n1, n2, a_pool=0.0025, a_screen=0.05, power=0.80):
    """MDE (in units of per-day SD/1) for: pooled Z over n1+n2 days > z(a_pool)
    AND screen Z over the youngest n2 days > z(a_screen). Exact bivariate normal."""
    zp, zs = Z(1 - a_pool), Z(1 - a_screen)
    n = n1 + n2
    rho = math.sqrt(n2 / n)
    mvn = stats.multivariate_normal(mean=[0, 0], cov=[[1, rho], [rho, 1]])

    def pw(d):
        mp, ms = d * math.sqrt(n), d * math.sqrt(n2)
        # P(Zp>zp, Zs>zs) = P(-Zp<-zp, -Zs<-zs)
        return mvn.cdf([mp - zp, ms - zs])

    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if pw(mid) < power:
            lo = mid
        else:
            hi = mid
    return hi, pw


for K in (200, 300, 500, 600):
    sd = 2.5 / math.sqrt(K - 1)
    d_v, _ = joint_mde(365, 365)          # Zone V: W1+W2 pooled, screen W2
    mde_v = d_v * sd
    mde_pool_only = (z0025 + z80) * sd / math.sqrt(730)
    mde_k = 1.008 * (z0025 + z80) * sd / math.sqrt(365)  # Zone K 12 M, GSD OBF 4 looks
    mde_x = (Z(0.95) + z80) * sd / math.sqrt(1277)        # Zone X exploration, 1-seitig 0,05
    ul_x = Z(0.95) * sd / math.sqrt(1277)
    p(f"K {K:3d}: SD(IC_t) {sd:.4f} | Zone V (730 d, pooled 0,0025 + Screen W2 0,05, gem. Power 0,8) "
      f"MDE {mde_v:.4f} (nur pooled {mde_pool_only:.4f}) | Zone K 12 M GSD {mde_k:.4f} | "
      f"Zone X 1.277 d MDE(0,05) {mde_x:.4f}, Ausschlussgrenze bei IC 0 {ul_x:.4f}")
sig_xs_d = 370.0  # bp, [V] Konzept Anhang 3 (9,85 %/sqrt 7)
for name, cost_rt in (("Maker 4 bp RT", 4.0), ("Taker 11 bp RT", 11.0), ("gesamt 15 bp RT", 15.0)):
    # L/S = long decile minus short decile; full daily turnover: one RT per leg per day
    for turn in (1.0, 0.5):
        ic_min = 2 * cost_rt * turn / (3.51 * sig_xs_d)
        p(f"SESOI {name:16s} Umschlag {turn:.1f}/Tag: IC_min = 2*c*u/(3,51*370) = {ic_min:.4f}")
p("Rang-IC: Gauss-Kante x pi^2/6 Korrektur (K-1) hier NICHT angewandt (3,51-Formel ist Pearson-Dezil) [U]")

# ---------------------------------------------------------------------------
hdr("C. K-09 Delisting-Hazard (Cox): Ereignisraten und MDE")
yrs = (np.datetime64("2026-10-31") - np.datetime64("2021-01-01")).astype(int) / 365.25
p(f"Spanne 2021-01-01..2026-10-31 = {yrs:.2f} Jahre; 306 Delistungen [F DEC-100] -> {306/yrs:.1f}/Jahr; "
  f"~800 Listungen [F Konzept F5] -> {800/yrs:.0f}/Jahr")
x_years = (np.datetime64("2024-07-01") - np.datetime64("2021-01-01")).astype(int) / 365.25
p(f"Zone X 2021-01-01..2024-06-30 = {x_years:.2f} Jahre -> erwartete Delistungen ~{306/yrs*x_years:.0f} [V gleichmaessig]")
for D in (52, 105, 186):
    for deff in (1.0, 2.0, 3.0):
        se = math.sqrt(deff / D)  # SE(beta) per SD of covariate ~ 1/sqrt(D) (Schoenfeld), x deff
        mde = (z0025 + z80) * 1.008 * se
        mde05 = (Z(0.95) + z80) * se
        p(f"D {D:3d} Ereignisse, Design-Effekt {deff:.0f}: SE(log HR je SD) {se:.3f} -> "
          f"MDE80 (0,0025, GSD) log HR {mde:.2f} = HR {math.exp(mde):.2f} je SD; "
          f"(alpha 0,05: HR {math.exp(mde05):.2f})")

# ---------------------------------------------------------------------------
hdr("D. K-07 Lebenszyklus (APC): Alterskontrast log-Vol")
for n_list, lab in ((480, "Zone X ~3,5 J x 137/J"), (275, "Zone V W1/W2"), (137, "Zone K 12 M")):
    for s_between in (0.4, 0.6):
        for deff in (1.0, 2.0):
            se_c = s_between * math.sqrt(2 * deff / n_list)  # contrast of two age bins, paired by symbol ~ conservative
            mde = (z0025 + z80) * se_c
            p(f"{lab:22s} n {n_list:3d}, SD(log Vol) zwischen Symbolen {s_between} [V], deff {deff:.0f}: "
              f"MDE80 Alterskontrast {mde:.3f} log = Faktor {math.exp(mde):.2f}")

# ---------------------------------------------------------------------------
hdr("E. K-05 RMT: Marchenko-Pastur-Kante und noetiger Eigenwert fuer die 2,3..2,6-fache IC-Streuung")
for K, T in ((200, 1277), (300, 1277), (500, 1277), (300, 181 * 5)):
    q = K / T
    lmax = (1 + math.sqrt(q)) ** 2
    p(f"K {K}, T {T}: q {q:.3f}, MP-Oberkante {lmax:.2f}")
for r in (2.3, 2.5, 2.6):
    need = r ** 2 - 1
    for cos2 in (1.0, 0.5, 0.25):
        p(f"SD-Verhaeltnis {r}: sum (x'l)^2/(K-1) = {need:.2f}; bei Ausrichtung cos^2 {cos2}: "
          f"Eigenwert der Residual-Korrelation >= {1 + need / cos2:.1f}")
p("Lesart: x'Rx/(K-1) = 1 + sum_f (x'l_f)^2/(K-1); Eigenwert = 1 + |l|^2 [R, Normalnaeherung, Spearman ~ Pearson]")

# ---------------------------------------------------------------------------
hdr("F. K-04 Schwere Raender: effektive Freiheitsgrade, t-Kritik, Edgeworth-alpha")
for n in (40, 52, 104, 365):
    for kappa in (0.0, 2.6, 5.0, 10.0):
        var_s2 = 2 / (n - 1) + kappa / n
        df = 2 / var_s2
        tc0025 = stats.t.ppf(1 - 0.0025, df)
        tc05 = stats.t.ppf(1 - 0.05, df)
        tb = stats.t.ppf(0.80, df)
        infl = (tc0025 + tb) / (z0025 + z80)
        p(f"n {n:3d}, Exzess-Kurtosis {kappa:4.1f}: df_eff {df:6.1f}; t_krit(0,0025) {tc0025:.3f} vs z 2,807; "
          f"t_krit(0,05) {tc05:.3f} vs 1,645; MDE-Faktor (0,0025) {infl:.3f}")
p("Edgeworth (Hall 1987 [sek]): P(T > z) ~ alpha - n^-1/2 (g/6)(2z^2+1) phi(z); g = Schiefe der Clusterstatistik")
for a in (0.0025, 0.05):
    z = Z(1 - a)
    for n in (40, 52, 104, 365):
        row = []
        for g in (-1.0, -0.5, 0.5):
            act = a - (g / 6) * (2 * z * z + 1) * PHI(z) / math.sqrt(n)
            row.append(f"g {g:+.1f}: {act:.4f}")
        p(f"alpha {a}: n {n:3d} -> " + "; ".join(row))
p("Vorbehalt: Edgeworth ist in den aeussersten Raendern (z 2,8) nur Groessenordnung [U].")

# ---------------------------------------------------------------------------
hdr("G. K-04 Ereigniszeit / Vol-Gewichtung: Effizienzgewinn bei Varianzheterogenitaet")
for r in (1.67, 2.3, 2.8):
    # two equal halves with variance v and r*v
    eq = (1 + r) / 2
    ivw = 2 / (1 + 1 / r)
    gain = eq / ivw
    p(f"Varianzverhaeltnis {r}: gleichgewichtet {eq:.3f}, invers-varianzgewichtet {ivw:.3f} (x v/N) -> "
      f"Datenersparnis {1-1/gain:.1%}, MDE-Faktor {math.sqrt(1/gain):.3f}")
p("Gilt fuer Effekte konstant in bp; fuer vol-proportionale Effekte ist Standardisierung ohnehin die natuerliche Skala [U].")

# ---------------------------------------------------------------------------
hdr("H. K-03 Diskretes Delta-Hedging: Leland-Aufschlag dsigma = kappa*sqrt(2/pi)/sqrt(dt)")
p("Herleitung: Kosten je Intervall kappa*Gamma*S^2*sigma*sqrt(dt)*E|z|; Gamma-P&L 1/2 Gamma S^2 dsigma^2 dt;"
  " gleichsetzen -> dsigma = kappa*E|z|/sqrt(dt) (annualisiert, unabhaengig von sigma) [R]")
dts = (("1 min", 1 / (365 * 1440)), ("5 min", 5 / (365 * 1440)), ("1 h", 1 / 8760), ("4 h", 4 / 8760),
       ("8 h", 8 / 8760), ("1 d", 1 / 365))
for lab, kap in (("Maker 2 bp", 2e-4), ("Taker 5,5 bp", 5.5e-4), ("Taker+Slippage 7,5 bp", 7.5e-4)):
    row = []
    for dl, dt in dts:
        ds_g = kap * math.sqrt(2 / math.pi) / math.sqrt(dt) * 100
        row.append(f"{dl}: {ds_g:5.2f}")
    p(f"{lab:22s} Aufschlag in VP (Gauss E|z| 0,798): " + " | ".join(row))
et4 = math.sqrt(2) * math.gamma(1.5) / (math.sqrt(math.pi) * math.gamma(2.0))
p(f"E|z| Student-t4 auf Einheitsvarianz = {et4:.4f} (Gauss 0,7979): Formfaktor {et4/0.7979:.3f};"
  " Kurzfrist-Umkehr (H-24, Bid-Ask-Bounce) wirkt entgegen - Nettowirkung UNGEMESSEN")
p("Vergleich: Options-Gebuehr 2/3 bp Index [F B.4]; C-33-Schwelle 3 VP [F]; VRP-Prior 7,14 VP [F/sek]; "
  "VRP-MDE80 12,9 VP [F DEC-104 E3 (e)]")

# ---------------------------------------------------------------------------
hdr("I. K-01 Quadratwurzel-Impact: Groessenordnung I = Y*sigma_d*sqrt(Q/V) [Y aus SEK, nur Orientierung]")
for sig, lab in ((262.0, "BTC sigma_d 262 bp [F]"), (650.0, "Alt sigma_d 650 bp [V]")):
    for Y in (0.5, 1.0):
        row = []
        for q in (1e-5, 1e-4, 1e-3, 1e-2):
            row.append(f"Q/V {q:g}: {Y*sig*math.sqrt(q):6.2f} bp")
        p(f"{lab:24s} Y {Y}: " + " | ".join(row))
p("Vergleich: 'ungemessene ~4 bp Slippage' (B.1, K-11): bei BTC Y 0,5..1 entspricht das Q/V ~ "
  f"{(4/(1.0*262))**2:.1e}..{(4/(0.5*262))**2:.1e} des Tagesvolumens")

# ---------------------------------------------------------------------------
hdr("J. K-01 Akten-Vorpruefung Kyle-Obizhaeva: Spread-Dezile gegen Umsatzquantile (nur Groessenordnung)")
spread_ratio = 30.6 / 1.6   # [F E-12, ein Snapshot]
turn_ratio = 631 / 1.6      # [F Zensus gesamt Q95/Q5, Wochenumsatz; Dezil-Quantil-Zuordnung V]
expo = math.log(spread_ratio) / math.log(turn_ratio)
p(f"Spread-Verhaeltnis D10/D1 {spread_ratio:.1f}; Umsatz-Verhaeltnis Q95/Q5 {turn_ratio:.0f}; "
  f"implizierter Exponent bei gleicher Vol {expo:.3f}")
p(f"KO (Spread ~ (sigma^2/PV)^(1/3)) braucht Vol-Verhaeltnis {(spread_ratio/turn_ratio**(1/3))**1.5:.2f} "
  f"zwischen den Extrem-Dezilen; Exponent 1/2 braucht {(spread_ratio/turn_ratio**0.5)**(1/1):.2f} (sigma^1)")
p("Vorbehalt: Tick-Bindung am liquiden Ende, Snapshot n=1 je Dezil, Perp-Turnover statt Spot [V].")

# ---------------------------------------------------------------------------
hdr("K. K-01 Aequivalenztest (TOST) fuer Invarianz-Exponenten: noetige Marge")
for se in (0.01, 0.02, 0.03):
    m = (z0025 + Z(1 - 0.20 / 2)) * se
    p(f"SE(Exponent) {se}: TOST alpha 0,0025 je Seite, Power 0,8 bei wahrem Wert in der Mitte -> Marge >= {m:.3f}")
for s_res, s_x, D in ((0.2, 0.5, 365), (0.3, 0.4, 365), (0.3, 0.4, 1500)):
    se = s_res / (s_x * math.sqrt(D))
    p(f"Steigung log N_trades auf log W: s_res {s_res} [V], sd(log W) {s_x} [V], D {D} Tage -> SE {se:.4f}")

# ---------------------------------------------------------------------------
hdr("L. K-06 Put-Call-Paritaet: Genauigkeit der impliziten Basis")
half_spread_vp = 0.14 / 2   # BTC Bein-Band [F B.6]
vega_bp_per_vp = 5.28       # [F B.5]
err_bp = math.sqrt(2) * half_spread_vp * vega_bp_per_vp
for T_days in (7, 30, 90):
    for n_pairs in (1, 10, 20):
        ann = err_bp / math.sqrt(n_pairs) / (T_days / 365)
        p(f"T {T_days:3d} d, {n_pairs:2d} Strike-Paare: Forward-Fehler {err_bp/math.sqrt(n_pairs):.2f} bp -> "
          f"annualisierte Basis +-{ann:.1f} bp p.a. (unabhaengige Fehler [V])")

# ---------------------------------------------------------------------------
hdr("M. Erstes gegen zweites Moment: was hohe Abtastrate kauft (Merton 1980 [sek])")
sig_a = 262 * math.sqrt(365) / 1e4
p(f"BTC sigma_annual = 262 bp x sqrt(365) = {sig_a:.1%} [R aus F]")
for T in (2.0, 4.25, 6.6):
    p(f"Drift-SE nach {T} Jahren: {sig_a/math.sqrt(T):.1%} p.a. - unabhaengig von der Abtastrate")
for lab, n in (("Tage 6,6 J", 2413), ("1-min 6,6 J", 2413 * 1440)):
    for kappa in (0.0, 5.0):
        p(f"rel. SE der Varianz, {lab:12s} (N {n:9d}), Kurtosis {kappa}: {math.sqrt((2+kappa)/n):.4%}"
          " (ohne Mikrostrukturrauschen)")
for lab, n in (("Tage/Jahr", 365), ("30-min/Jahr", 17520), ("1-min/Jahr", 525600)):
    p(f"IC-MDE80 (0,05) bei {lab:12s}: {(Z(0.95)+z80)/math.sqrt(n):.4f}")

# ---------------------------------------------------------------------------
hdr("N. Zeitlinie unter DEC-104 (Kohorte 1 = 2027-01-01)")
p("Zone V (W1/W2): ein Blick je Familie in Kohorte 1 -> Rechnung Q1 2027 (sofern OC E0 vorliegt)")
p("Zone K 12-M-Konfirmation 2026-07-01..2027-06-30: Blicke nach Q3-2026/Q4-2026 (bei Registrierung schon vorhanden),"
  " Q1-2027, Q2-2027 -> letzter Blick Anfang Juli 2027; Kohorte 2 (2027-04-01) aendert das Ende nicht")
p("GSD OBF 4 Blicke alpha 0,0025: Maximum-Inflation 1,008, E[N|H1] 0,872 [F PRD_ANALYSE 6]")

with open(__file__.replace(".py", ".out"), "w") as f:
    f.write("\n".join(out) + "\n")
