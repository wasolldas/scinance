#!/usr/bin/env python3
"""Herleitung des registrierten Stabilitaetstests (P-2 Variante (c), DEC-104 Nachtrag 2 (4)) - 2026-11-02.

Rolle: Herleitung mit eigenem Code. Nur Formeln und Simulation; keine Marktdaten, keine Siegeldatei, kein
Harvest-Client, kein Netz. Eingangszahlen ausschliesslich aus der Akte (OC-Bericht 2026-11-02 und dessen Skript
oc_sim.py; A2-Konstanten dort woertlich uebernommen, Quelle je Konstante im Kommentar).
Deterministisch (feste Seeds 31104..31107 und 31108 + T_max), nur numpy/scipy, lauffaehig mit `python3 -I stab_sim.py`.
Ausgaben: stab_results.json (neben diesem Skript) und die Konsolenausgabe (-> stab_sim.out).
Abschnitte (0)..(6) wie im Auftrag BRIEF_stabilitaetstest.md (Nr. 1..6).

Einheiten: Effekte in SE_12 = Standardfehler eines 12-Monats-Fensters (Varianz je Beobachtung wie im aelteren
Teil). r = Anteil des juengsten 12-Monats-Teils an den Konfirmationsdaten (r = 12 / T Monate).
m_j ~ N(mu_j, k^2), m_a ~ N(mu_a, r/(1-r)) (unabhaengig); gepoolt = r m_j + (1-r) m_a (Mittel ueber alle Cluster).
"""
import json
import math
import os
import sys
import time

import numpy as np
from scipy import integrate, optimize
from scipy.stats import norm, t as student_t

T_START = time.process_time()
HERE = os.path.dirname(os.path.abspath(__file__))
RES = {"meta": {"skript": "stab_sim.py", "numpy": np.__version__, "python": sys.version.split()[0]}}

Z = norm.ppf
Z95 = float(Z(0.95))          # 1,6449
Z9975 = float(Z(0.9975))      # 2,8070
Z80 = float(Z(0.80))          # 0,8416
MU_FIX = Z9975 + Z80          # 3,6487 gepoolt 0,0025 / 0,80
C80_05 = Z95 + Z80            # 2,4865 ein Fenster 0,05 / 0,80
MU_C = Z9975 + float(Z(0.8 / 0.95))   # 3,8102 gepoolt bei Pool-Power 0,8/0,95
INFO_POOL = MU_FIX ** 2
INFO_C10_JE = 2 * C80_05 ** 2


def r6(x):
    if isinstance(x, (list, tuple)):
        return [r6(v) for v in x]
    if isinstance(x, dict):
        return {str(k): r6(v) for k, v in x.items()}
    if isinstance(x, (np.floating, float)):
        x = float(x)
        if math.isnan(x) or math.isinf(x):
            return None
        return float(f"{x:.6g}")
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def put(path, value):
    d = RES
    keys = path.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = r6(value)


def P(*a):
    print(*a, flush=True)


def g4(x):
    return "nie" if (x is None or (isinstance(x, float) and not math.isfinite(x))) else f"{x:.4g}"


def biv_upper(a, b, rho):
    """P(X > a, Y > b), standard-bivariat-normal mit Korrelation rho (1-D-Quadratur; wie oc_sim.py)."""
    if rho >= 1.0 - 1e-12:
        return float(norm.sf(max(a, b)))
    if rho <= -1.0 + 1e-12:
        return float(max(0.0, norm.sf(a) - norm.cdf(-b)))
    s = math.sqrt(1.0 - rho * rho)
    lo = max(a, -12.0)
    f = lambda x: norm.pdf(x) * norm.sf((b - rho * x) / s)
    val, _ = integrate.quad(f, lo, max(lo, 0.0) + 14.0, epsabs=1e-14, epsrel=1e-11, limit=400)
    return float(val)


def months_to_ym(y, m, months):
    tot = y * 12 + (m - 1) + math.ceil(months - 1e-9)
    return f"{tot // 12:04d}-{tot % 12 + 1:02d}"


# =====================================================================================
# Zwei-Teile-Modell: lineare Statistiken in (m_j, m_a)
# =====================================================================================
def stat(vec, var):
    """Mittel-Koeffizienten und SD einer linearen Statistik vec . (m_j, m_a)."""
    vec = np.asarray(vec, float)
    return vec, math.sqrt(float(vec @ (var * vec)))


def rule_pass(rule, mu_j, mu_a, r, k=1.0, alpha_s=0.05, alpha_stab=0.05, f=0.5):
    """P(PASS) der Regel im Zwei-Teile-Modell (exakt, bivariat normal, Varianzen bekannt).
    rule: 'pool' | 'screen' | 'stab' | 'ni_last' (Nachweis m_j - f m_p > 0) | 'ni_marge' (kein Abfall unter f x gepoolt)
          (f = 0,5)."""
    var = np.array([k * k, r / (1.0 - r)])
    mu = np.array([mu_j, mu_a])
    a, sa = stat([r, 1.0 - r], var)
    ea = float(a @ mu) / sa
    if rule == "pool":
        return float(norm.sf(Z9975 - ea))
    if rule == "screen":
        b, cb = np.array([1.0, 0.0]), float(norm.isf(alpha_s))
    elif rule == "stab":
        b, cb = np.array([1.0, -1.0]), -float(norm.isf(alpha_stab))
    elif rule == "ni_last":
        b, cb = np.array([1.0, 0.0]) - f * a, Z95
    elif rule == "ni_marge":
        b, cb = np.array([1.0, 0.0]) - f * a, -Z95
    else:
        raise ValueError(rule)
    sb = math.sqrt(float(b @ (var * b)))
    eb = float(b @ mu) / sb
    rho = float(a @ (var * b)) / (sa * sb)
    return biv_upper(Z9975 - ea, cb - eb, rho)


def corr_pool(rule, r, k=1.0, f=0.5):
    var = np.array([k * k, r / (1.0 - r)])
    a = np.array([r, 1.0 - r])
    b = {"stab": np.array([1.0, -1.0]), "screen": np.array([1.0, 0.0]),
         "ni_last": np.array([1.0, 0.0]) - f * a, "ni_marge": np.array([1.0, 0.0]) - f * a}[rule]
    return float(a @ (var * b)) / math.sqrt(float(a @ (var * a)) * float(b @ (var * b)))


def mde(rule, r, k=1.0, target=0.8, **kw):
    """Effekt (SE_12, homogen) mit P(PASS) = target; inf, wenn unerreichbar (Boden-Regeln bis 60 SE_12 gesucht)."""
    fn = lambda m: rule_pass(rule, m, m, r, k, **kw) - target
    if fn(60.0) < 0:
        return float("inf")
    return float(optimize.brentq(fn, 1e-6, 60.0, xtol=1e-12))


def sd_pool(r, k=1.0):
    return math.sqrt(r * r * k * k + r * (1.0 - r))


# =====================================================================================
# (0) Reproduktion der OC-Zahlen zur Variante (c)
# =====================================================================================
def sec0():
    P("\n================ (0) Reproduktion OC (a) Nr. 6 / DEC-104 N2 (4) ================")
    out = {}
    for r in (0.5, 1 / 3, 0.25):
        m = mde("stab", r)
        cell = {"alpha_eff": rule_pass("stab", 0, 0, r), "MDE_SE12": m, "MDE_formel": MU_C * math.sqrt(r),
                "daten_vs_gepoolt": (m / (MU_FIX * math.sqrt(r))) ** 2, "daten_vs_C10je080": (m / math.sqrt(r)) ** 2 / INFO_C10_JE,
                "PASS_nur_aelter_1MDE": rule_pass("stab", 0, m, r), "PASS_nur_aelter_2MDE": rule_pass("stab", 0, 2 * m, r),
                "PASS_abklingend_1MDE": rule_pass("stab", 0.5 * m, m, r)}
        out[f"r{r:.3f}"] = cell
        P(f"r {r:.3f}: alpha_eff {cell['alpha_eff']:.6f}, MDE {m:.4f} SE_12, Daten/gepoolt {cell['daten_vs_gepoolt']:.4f}, "
          f"/C.10 je 0,80 {cell['daten_vs_C10je080']:.4f}, PASS nur aelter 1/2 MDE {cell['PASS_nur_aelter_1MDE']:.4f}/"
          f"{cell['PASS_nur_aelter_2MDE']:.4f}, abklingend {cell['PASS_abklingend_1MDE']:.4f}")
    put("s0_reproduktion_oc", out)
    P(f"Konstanten: z95 {Z95:.4f}, z9975 {Z9975:.4f}, z80 {Z80:.4f}, MU_FIX {MU_FIX:.4f}, C80_05 {C80_05:.4f}, "
      f"MU_C = z9975 + Phi^-1(0,8/0,95) = {MU_C:.4f}, Phi^-1(0,8/0,95) = {float(Z(0.8 / 0.95)):.4f}")
    put("konstanten", {"z95": Z95, "z9975": Z9975, "z80": Z80, "mu_fix": MU_FIX, "c80_005": C80_05, "mu_c": MU_C})


# =====================================================================================
# (1) Definition: Unabhaengigkeit, ungleiche Varianzen, Nicht-Unterlegenheits-Formulierungen
# =====================================================================================
def sec1():
    P("\n================ (1) Definition, Unabhaengigkeit, Nicht-Unterlegenheit ================")
    out = {}
    # (i) Korrelation gepoolt / D bei gleicher Varianz: 0 fuer jedes r; ungleiche Varianz: r (k^2 - 1) / ...
    tab = {}
    for r in (0.5, 1 / 3, 0.25):
        row = {}
        for k in (0.5, 0.7, 0.85, 1.0, 1.25, 1.5, 2.0):
            rI = (r / k ** 2) / (r / k ** 2 + 1 - r)
            row[f"k{k}"] = {"rho_pool_D": corr_pool("stab", r, k), "info_anteil_rI": rI}
        tab[f"r{r:.3f}"] = row
    out["korrelation_pool_D"] = tab
    P("Korrelation gepoolt (Mittel aller Cluster) / D je r und SD-Verhaeltnis k = SD_juengst / SD_aelter [Info-Anteil r_I]:")
    for rk, row in tab.items():
        P(f"  {rk}: " + "; ".join(f"k {kk[1:]}: {v['rho_pool_D']:+.4f} [r_I {v['info_anteil_rI']:.4f}]" for kk, v in row.items()))
    # (ii) Studentisierung: Gesamtvarianz enthaelt (m_j - m_a)^2 -> Abhaengigkeit endlich (Abschnitt 5 simuliert)
    # (iii) Nicht-Unterlegenheit, f = 0,5
    ni = {}
    for r in (0.5, 1 / 3, 0.25, 1 / 6, 0.1):
        c = {"MDE_stab": mde("stab", r), "MDE_ni_last": mde("ni_last", r), "MDE_ni_marge": mde("ni_marge", r),
             "MDE_screen005": mde("screen", r), "rho_pool_ni": corr_pool("ni_last", r)}
        c["q_ni_marge_bei_MDE"] = rule_pass("ni_marge", c["MDE_ni_marge"], c["MDE_ni_marge"], r) / rule_pass("pool", c["MDE_ni_marge"], c["MDE_ni_marge"], r)
        ni[f"r{r:.3f}"] = c
    ni["boden_ni_last_f05"] = (Z95 + Z80) / (1 - 0.5)
    ni["boden_screen005"] = C80_05
    out["nicht_unterlegenheit_f05"] = ni
    P("Nicht-Unterlegenheit f 0,5 (MDE in SE_12; gemeinsame Power 0,80): je r MDE stab / NI-Nachweis (Last beim Effekt) / "
      "NI-Marge (Abfall unter 0,5 x gepoolt verwirft) / Screen 0,05; q(NI-Marge) an ihrer MDE:")
    for rk, c in ni.items():
        if rk.startswith("r"):
            P(f"  {rk}: {c['MDE_stab']:.4f} / {c['MDE_ni_last']:.4f} / {c['MDE_ni_marge']:.4f} / {c['MDE_screen005']:.4f}; "
              f"corr(gepoolt, NI) {c['rho_pool_ni']:.4f}; q_NI-Marge {c['q_ni_marge_bei_MDE']:.4f}")
    P(f"  Boden NI-Nachweis f 0,5 (r -> 0): (z95 + z80)/(1 - f) = {ni['boden_ni_last_f05']:.4f} SE_12 (Screen 0,05: {C80_05:.4f})")
    put("s1_definition", out)
    return out


# =====================================================================================
# (2) Entscheidungsregel und Power-Planung (fester Blick)
# =====================================================================================
def sec2():
    P("\n================ (2) Entscheidungsregel und Power-Planung (ein Blick) ================")
    out = {}
    # homogen, gleiche Varianz: q = P(D > -z95 | gepoolt besteht) = 0,95 exakt fuer jedes r
    base = {}
    for r in (0.5, 1 / 3, 0.25, 1 / 6, 0.1):
        m = mde("stab", r)
        q = rule_pass("stab", m, m, r) / rule_pass("pool", m, m, r)
        base[f"r{r:.3f}"] = {"MDE": m, "q": q, "daten_vs_gepoolt": (m / (MU_FIX * math.sqrt(r))) ** 2,
                             "daten_vs_C10je080": (m / math.sqrt(r)) ** 2 / INFO_C10_JE,
                             "daten_vs_C10gem080": (m / math.sqrt(r)) ** 2 / (2 * (Z95 + float(Z(math.sqrt(0.8)))) ** 2),
                             "power_stabtest_gegen_abfall_auf_0_bei_MDE": float(norm.sf(Z95 - m * math.sqrt(1 - r)))}
    out["homogen_gleiche_varianz"] = base
    P("Homogen, gleiche Varianz: je r MDE (SE_12), q = P(Stabilitaet haelt | gepoolt besteht), Daten gegen gepoolt / C.10 je 0,80 / "
      "C.10 gemeinsam 0,80, Power des Stabilitaetstests gegen Abfall auf 0 an der MDE:")
    for rk, c in base.items():
        P(f"  {rk}: {c['MDE']:.4f}, q {c['q']:.6f}, {c['daten_vs_gepoolt']:.4f} / {c['daten_vs_C10je080']:.4f} / "
          f"{c['daten_vs_C10gem080']:.4f}, Power gegen Abfall {c['power_stabtest_gegen_abfall_auf_0_bei_MDE']:.4f}")
    # ungleiche Varianzen: alpha_eff, q, Datenfaktor gegen gepoolt (gleiches k)
    uv = {}
    for r in (0.5, 1 / 3, 0.25):
        row = {}
        for k in (0.5, 0.7, 0.85, 1.0, 1.25, 1.5, 2.0):
            m = mde("stab", r, k)
            mp = MU_FIX * sd_pool(r, k)
            row[f"k{k}"] = {"alpha_eff": rule_pass("stab", 0, 0, r, k), "MDE": m,
                            "q_bei_MDE": rule_pass("stab", m, m, r, k) / rule_pass("pool", m, m, r, k),
                            "daten_vs_gepoolt_gleiches_k": (m / mp) ** 2,
                            "power_bei_plan_q095": rule_pass("stab", MU_C * sd_pool(r, k), MU_C * sd_pool(r, k), r, k)}
        uv[f"r{r:.3f}"] = row
    out["ungleiche_varianz"] = uv
    P("Ungleiche Varianz (k = SD juengst / SD aelter je Cluster): alpha_eff, q an der MDE, Daten gegen gepoolt (gleiches k), "
      "realisierte Power bei Planung mit q = 0,95:")
    for rk, row in uv.items():
        P(f"  {rk}: " + "; ".join(f"k {kk[1:]}: {v['alpha_eff']:.6f}, q {v['q_bei_MDE']:.4f}, x{v['daten_vs_gepoolt_gleiches_k']:.4f}, "
                                  f"P {v['power_bei_plan_q095']:.4f}" for kk, v in row.items()))
    allf = [v["daten_vs_gepoolt_gleiches_k"] for row in uv.values() for kk, v in row.items() if kk in ("k0.7", "k0.85", "k1.0", "k1.25", "k1.5")]
    allp = [v["power_bei_plan_q095"] for row in uv.values() for kk, v in row.items() if kk in ("k0.7", "k0.85", "k1.0", "k1.25", "k1.5")]
    out["spanne_k07_bis_15"] = {"daten_faktor_min": min(allf), "daten_faktor_max": max(allf), "power_min": min(allp), "power_max": max(allp)}
    P(f"  Spanne k 0,7..1,5 (r 1/2..1/4): Datenfaktor {min(allf):.4f}..{max(allf):.4f}; Power bei Planung q 0,95: {min(allp):.4f}..{max(allp):.4f}")
    # Niveau des Stabilitaetstests als Stellschraube
    lev = {}
    for a_st in (0.05, 0.10, 0.15, 0.20):
        if 0.8 / (1 - a_st) >= 1.0:
            lev[str(a_st)] = {"unerreichbar": True, "grund": "1 - alpha_stab <= 0,80: gemeinsame Power 0,80 unerreichbar"}
            continue
        mu_s = Z9975 + float(Z(0.8 / (1 - a_st)))
        lev[str(a_st)] = {"mu": mu_s, "daten_vs_gepoolt": mu_s ** 2 / INFO_POOL, "daten_vs_C10je080": mu_s ** 2 / INFO_C10_JE,
                          "alpha_eff": 0.0025 * (1 - a_st)}
        for r in (0.5, 0.25):
            m = mu_s * math.sqrt(r)
            lev[str(a_st)][f"r{r:.3f}_PASS_nur_aelter_1MDE"] = rule_pass("stab", 0, m, r, alpha_stab=a_st)
            lev[str(a_st)][f"r{r:.3f}_PASS_nur_aelter_2MDE"] = rule_pass("stab", 0, 2 * m, r, alpha_stab=a_st)
    out["niveau_stabilitaetstest"] = lev
    P("Niveau alpha_stab des Stabilitaetstests: Daten gegen gepoolt / C.10 je 0,80, alpha_eff, PASS nur aelter 1/2 MDE (r 1/2; r 1/4):")
    for k_, v in lev.items():
        if v.get("unerreichbar"):
            P(f"  {k_}: unerreichbar (1 - alpha_stab <= 0,80)")
            continue
        P(f"  {k_}: x{v['daten_vs_gepoolt']:.4f} / x{v['daten_vs_C10je080']:.4f}, {v['alpha_eff']:.6f}; "
          f"{v['r0.500_PASS_nur_aelter_1MDE']:.4f}/{v['r0.500_PASS_nur_aelter_2MDE']:.4f}; "
          f"{v['r0.250_PASS_nur_aelter_1MDE']:.4f}/{v['r0.250_PASS_nur_aelter_2MDE']:.4f}")
    put("s2_entscheidungsregel", out)
    return out


# =====================================================================================
# (3) Schutzwirkung
# =====================================================================================
RULES3 = [("pool", {}), ("screen005", {"alpha_s": 0.05}), ("screen020", {"alpha_s": 0.20}), ("stab", {}),
          ("ni_last", {}), ("ni_marge", {})]


def rname(n):
    return "screen" if n.startswith("screen") else n


def sec3():
    P("\n================ (3) Schutzwirkung ================")
    out = {}
    for r in (0.5, 1 / 3, 0.25, 1 / 6, 0.1):
        cell = {}
        m_c = mde("stab", r)
        for name, kw in RULES3:
            m = mde(rname(name), r, **kw)
            c = {"MDE": m, "alpha_eff": rule_pass(rname(name), 0, 0, r, **kw)}
            if math.isfinite(m):
                for f in (0.5, 1.0, 1.5, 2.0):
                    c[f"nur_aelter_{f}MDE_eigen"] = rule_pass(rname(name), 0, f * m, r, **kw)
                c["abklingend_1MDE_eigen"] = rule_pass(rname(name), 0.5 * m, m, r, **kw)
                c["nur_juengst_1MDE_eigen"] = rule_pass(rname(name), m, 0, r, **kw)
            for f in (0.5, 1.0, 1.5, 2.0):
                c[f"nur_aelter_{f}MDEc"] = rule_pass(rname(name), 0, f * m_c, r, **kw)
            c["abklingend_1MDEc"] = rule_pass(rname(name), 0.5 * m_c, m_c, r, **kw)
            c["nur_juengst_1MDEc"] = rule_pass(rname(name), m_c, 0, r, **kw)
            c["homogen_1MDEc"] = rule_pass(rname(name), m_c, m_c, r, **kw)
            # schlechtester Fall "nur aelter" ueber alle Effektgroessen (Gitter + Verfeinerung)
            grid = np.linspace(0.0, 25.0, 126)
            vals = [rule_pass(rname(name), 0, g, r, **kw) for g in grid]
            i = int(np.argmax(vals))
            lo, hi = grid[max(i - 1, 0)], grid[min(i + 1, len(grid) - 1)]
            res = optimize.minimize_scalar(lambda g: -rule_pass(rname(name), 0, g, r, **kw), bounds=(lo, hi), method="bounded",
                                           options={"xatol": 1e-6})
            c["sup_nur_aelter"] = max(-res.fun, max(vals))
            c["argsup_nur_aelter_SE12"] = float(res.x) if -res.fun >= max(vals) else float(grid[i])
            # Effekt (nur aelter), ab dem P(PASS) unter 0,05 faellt (nur fuer stab)
            cell[name] = c
        out[f"r{r:.3f}"] = cell
        P(f"r {r:.3f} (MDE_c {m_c:.4f} SE_12): Regel | MDE | nur aelter 0,5/1/1,5/2 x eigene MDE | abklingend | nur juengst | "
          f"nur aelter 1/2 x MDE_c | sup nur aelter (bei SE_12)")
        for name, c in cell.items():
            if math.isfinite(c["MDE"]):
                P(f"   {name:>10} | {c['MDE']:.4f} | {c['nur_aelter_0.5MDE_eigen']:.4f}/{c['nur_aelter_1.0MDE_eigen']:.4f}/"
                  f"{c['nur_aelter_1.5MDE_eigen']:.4f}/{c['nur_aelter_2.0MDE_eigen']:.4f} | {c['abklingend_1MDE_eigen']:.4f} | "
                  f"{c['nur_juengst_1MDE_eigen']:.4f} | {c['nur_aelter_1.0MDEc']:.4f}/{c['nur_aelter_2.0MDEc']:.4f} | "
                  f"{c['sup_nur_aelter']:.4f} ({c['argsup_nur_aelter_SE12']:.3f})")
    # Effektschwelle: Effekt im aelteren Teil (SE_12), ab dem die Variante (c) mit >= 0,80 verwirft (PASS <= 0,2 x ...)
    thr = {}
    for r in (0.5, 1 / 3, 0.25, 1 / 6, 0.1):
        # P(Stabilitaet verwirft | nur aelter, Effekt mu) = Phi(mu sqrt(1-r) - z95) = 0,80
        thr[f"r{r:.3f}"] = {"abfall_80proz_verworfen_SE12": C80_05 / math.sqrt(1 - r),
                            "in_MDE_c": C80_05 / math.sqrt(1 - r) / mde("stab", r)}
    out["abfall_mit_power080_erkannt"] = thr
    P("Abfall (Effekt nur im aelteren Teil), den der Stabilitaetstest mit 0,80 verwirft: " +
      "; ".join(f"{k}: {v['abfall_80proz_verworfen_SE12']:.4f} SE_12 = {v['in_MDE_c']:.4f} MDE_c" for k, v in thr.items()))
    put("s3_schutz", out)
    return out


# =====================================================================================
# (4) Gruppensequentiell: OBF, K Blicke, Stabilitaetstest an den Blicken
# =====================================================================================
def oc_grid(C, theta, K=4, h=0.002):
    """Exakte Dichte-Propagation auf der B-Skala (wie oc_sim.py, ohne Futility): (P(PASS), E[t_stop])."""
    dt = 1.0 / K
    sd = math.sqrt(dt)
    grid = np.arange(-10.0, 10.0 + max(theta, 0.0) + h / 2, h)
    m = int(round(8 * sd / h))
    offs = np.arange(-m, m + 1) * h
    kern = norm.pdf(offs, theta * dt, sd) * h
    dens = None
    prej, Et = 0.0, 0.0
    for i in range(K):
        d = norm.pdf(grid, theta * dt, sd) if i == 0 else np.convolve(dens, kern, mode="same")
        rej = grid >= C
        prej += d[rej].sum() * h
        if i < K - 1:
            Et += (i + 1) * dt * d[rej].sum() * h
            dens = np.where(~rej, d, 0.0)
        else:
            Et += d.sum() * h
    return prej, Et


def obf_const(alpha, K):
    if K == 1:
        return float(norm.isf(alpha))
    lo, hi = 1.0, 4.5
    for _ in range(55):
        c = 0.5 * (lo + hi)
        a, _ = oc_grid(c, 0.0, K)
        lo, hi = (c, hi) if a > alpha else (lo, c)
    return 0.5 * (lo + hi)


class GSD:
    """Brownsche Bewegung auf 12 Teilschritten (Info-Zeit j/12); Blicke bei j = 12 k / K."""

    def __init__(self, n, seed):
        rng = np.random.default_rng(seed)
        W = np.cumsum(rng.standard_normal((n, 12)) * math.sqrt(1.0 / 12), axis=1)
        self.W = np.concatenate([np.zeros((n, 1)), W], axis=1)
        self.n = n

    def run(self, theta, C, K, r, variant, t0=None, alpha_stab=0.05, fut=False):
        """variant: 'none' | 'last' | 'each_cont' | 'each_term' | 'screen_each'. t0: Effekt nur bis Info-Zeit t0."""
        zst = float(norm.isf(alpha_stab))
        n = self.n
        jr_off = int(round(12 * r))
        looks = [12 * k // K for k in range(1, K + 1)]
        tt = np.arange(13) / 12.0
        drift = theta * (tt if t0 is None else np.minimum(tt, t0))
        stop = np.zeros(n, bool)
        passed = np.zeros(n, bool)
        crossed = np.zeros(n, bool)
        stale = np.zeros(n, bool)
        t_stop = np.ones(n)
        for i, j in enumerate(looks):
            t = j / 12.0
            Bj = self.W[:, j] + drift[j]
            eff = Bj >= C
            jr = j - jr_off
            last = (i == K - 1)
            check = variant in ("each_cont", "each_term", "screen_each") or (variant == "last" and last)
            if check:
                if variant == "screen_each":
                    if jr >= 0:
                        hold = (Bj - (self.W[:, jr] + drift[jr])) / math.sqrt(r) > Z95
                    else:
                        hold = Bj / math.sqrt(t) > Z95
                elif jr > 0:
                    s = jr / 12.0
                    Bs = self.W[:, jr] + drift[jr]
                    zD = ((Bj - Bs) / (t - s) - Bs / s) / math.sqrt(1.0 / (t - s) + 1.0 / s)
                    hold = zD > -zst
                else:
                    hold = np.ones(n, bool)
            else:
                hold = np.ones(n, bool)
            act = ~stop
            crossed |= act & eff
            if variant == "each_term":
                new_pass = act & eff & hold
                new_stop = act & eff
            else:
                new_pass = act & eff & hold
                new_stop = act & eff & hold
            if fut and not last:
                new_stop = new_stop | (act & (Bj < 0.0) & ~new_pass)
            if last:
                new_stop = act
            passed |= new_pass
            if t0 is not None and t - r >= t0 - 1e-9:
                stale |= new_pass
            t_stop[new_stop & ~stop] = t
            stop |= new_stop
        return {"pass": float(passed.mean()), "Et": float(t_stop.mean()), "crossed": float(crossed.mean()),
                "stale": float(stale.mean())}

    def design(self, C, K, r, variant, fut=False, alpha_stab=0.05):
        lo, hi = 2.0, 8.0
        for _ in range(44):
            th = 0.5 * (lo + hi)
            pw = self.run(th, C, K, r, variant, alpha_stab=alpha_stab, fut=fut)["pass"]
            lo, hi = (th, hi) if pw < 0.8 else (lo, th)
        th = 0.5 * (lo + hi)
        R = (th / MU_FIX) ** 2
        h1 = self.run(th, C, K, r, variant, alpha_stab=alpha_stab, fut=fut)
        h0 = self.run(0.0, C, K, r, variant, alpha_stab=alpha_stab, fut=fut)
        hh = self.run(0.5 * th, C, K, r, variant, alpha_stab=alpha_stab, fut=fut)
        return {"theta": th, "R_max": R, "power_H1": h1["pass"], "alpha_eff": h0["pass"], "EN_H1": R * h1["Et"],
                "EN_H0": R * h0["Et"], "q": h1["pass"] / h1["crossed"], "P_kreuzt_H1": h1["crossed"],
                "power_halbMDE": hh["pass"]}


def sec4():
    P("\n================ (4) Gruppensequentiell (OBF, alpha 0,0025, Power 0,80 der gemeinsamen Regel) ================")
    t0c = time.process_time()
    out = {}
    consts = {K: obf_const(0.0025, K) for K in (1, 2, 3, 4)}
    out["obf_konstante_B_skala"] = {str(K): v for K, v in consts.items()}
    P("OBF-Konstante (B-Skala, alpha 0,0025, Gitter): " + ", ".join(f"K {K}: {v:.4f}" for K, v in consts.items()))
    g = GSD(1_000_000, 31104)
    des = {}
    for K in (1, 2, 3, 4):
        for r in (0.5, 1 / 3, 0.25):
            variants = ["none", "last", "each_cont", "each_term"] if K > 1 else ["none", "last"]
            if K == 4 and r == 0.5:
                variants = variants + ["screen_each"]
            for v in variants:
                if v == "none" and r != 0.5:
                    continue   # ohne Stabilitaetstest unabhaengig von r
                d = g.design(consts[K], K, r, v)
                des[f"K{K}_r{r:.3f}_{v}"] = d
                P(f"K {K}, r {r:.3f}, {v:>11}: Max/N_fix {d['R_max']:.4f}, alpha {d['alpha_eff']:.5f}, E[N|H1] {d['EN_H1']:.4f}, "
                  f"E[N|H0] {d['EN_H0']:.4f}, q {d['q']:.4f}, Power {d['power_H1']:.4f}, Power 0,5 MDE {d['power_halbMDE']:.4f}")
    # Futility fuer die empfohlene Variante
    for v in ("each_cont", "each_term"):
        for r in (0.5, 1 / 3, 0.25):
            d = g.design(consts[4], 4, r, v, fut=True)
            des[f"K4_r{r:.3f}_{v}_fut"] = d
            P(f"K 4, r {r:.3f}, {v} + Futility Z<0 Blicke 1-3: Max {d['R_max']:.4f}, alpha {d['alpha_eff']:.5f}, "
              f"E[N|H1] {d['EN_H1']:.4f}, E[N|H0] {d['EN_H0']:.4f}, q {d['q']:.4f}")
    out["designs"] = des
    # veraltete Effekte (Effekt nur bis t0), K 4
    stale = {}
    for r in (0.5, 1 / 3, 0.25):
        for v in ("none", "last", "each_cont", "each_term"):
            key = f"K4_r{r:.3f}_{v}" if v != "none" else "K4_r0.500_none"
            th = des[key]["theta"]
            for t0 in sorted({0.5, round(1 - r, 6)}):
                for fm in (1.0, 2.0):
                    res = g.run(fm * th, consts[4], 4, r, v, t0=t0)
                    stale[f"r{r:.3f}_{v}_t0{t0:.3f}_{fm:.0f}MDE"] = {"P_PASS": res["pass"], "P_PASS_veraltet": res["stale"]}
    for t0 in (0.5,):
        res = g.run(des["K4_r0.500_screen_each"]["theta"], consts[4], 4, 0.5, "screen_each", t0=t0)
        stale[f"r0.500_screen_each_t0{t0:.3f}_1MDE"] = {"P_PASS": res["pass"], "P_PASS_veraltet": res["stale"]}
    out["veraltete_effekte"] = stale
    P("Effekt nur bis Info-Zeit t0 (K 4; Effekt = f x Design-theta der Variante): P(PASS) / davon veraltet")
    for k, v in stale.items():
        P(f"   {k}: {v['P_PASS']:.4f} / {v['P_PASS_veraltet']:.4f}")
    # Umrechnung N_0,05, gegen C.10
    n005 = MU_FIX ** 2 / C80_05 ** 2
    c10gem = 2 * (Z95 + float(Z(math.sqrt(0.8)))) ** 2 / C80_05 ** 2
    conv = {}
    for key in ("K4_r0.500_none", "K4_r0.500_each_cont", "K4_r0.333_each_cont", "K4_r0.250_each_cont",
                "K4_r0.500_each_term", "K4_r0.333_each_term", "K4_r0.250_each_term",
                "K4_r0.500_last", "K4_r0.500_screen_each"):
        e = des[key]["EN_H1"] * n005
        conv[key] = {"EN_H1_N005": e, "vs_C10gem080": e / c10gem, "vs_C10je080": e / 2.0, "max_N005": des[key]["R_max"] * n005,
                     "EN_vs_GSD_ohne": des[key]["EN_H1"] / des["K4_r0.500_none"]["EN_H1"],
                     "max_vs_GSD_ohne": des[key]["R_max"] / des["K4_r0.500_none"]["R_max"]}
    out["umrechnung"] = conv
    P("Umrechnung (N_0,05-Einheiten; gegen C.10 gemeinsam 0,80 / je 0,80; gegen GSD ohne Stabilitaetstest):")
    for k, v in conv.items():
        P(f"   {k}: E[N|H1] {v['EN_H1_N005']:.4f} N_0,05, x{v['vs_C10gem080']:.4f} / x{v['vs_C10je080']:.4f}; Max {v['max_N005']:.4f}; "
          f"E[N] x{v['EN_vs_GSD_ohne']:.4f}, Max x{v['max_vs_GSD_ohne']:.4f} gegen GSD ohne")
    put("s4_gsd", out)
    P(f"[Zeit (4): {time.process_time() - t0c:.1f} s CPU]")
    return out


# =====================================================================================
# (4b) Blickplaene in Monaten (Zone V + Zone K, Lesart B) und Niveau-Sensitivitaet
# =====================================================================================
def oc_grid_t(C, theta, times, h=0.002):
    """Wie oc_grid, aber beliebige Blickzeiten (Info-Anteile) times; Grenze B >= C an jedem Blick."""
    grid = np.arange(-12.0, 12.0 + max(theta, 0.0) + h / 2, h)
    dens = None
    prej = 0.0
    prev = 0.0
    for i, tk in enumerate(times):
        dt = tk - prev
        sd = math.sqrt(dt)
        if i == 0:
            d = norm.pdf(grid, theta * dt, sd)
        else:
            m = int(round(8 * sd / h))
            offs = np.arange(-m, m + 1) * h
            kern = norm.pdf(offs, theta * dt, sd) * h
            d = np.convolve(dens, kern, mode="same")
        rej = grid >= C
        prej += d[rej].sum() * h
        dens = np.where(~rej, d, 0.0)
        prev = tk
    return prej


def obf_const_t(alpha, times):
    lo, hi = 1.0, 4.5
    for _ in range(55):
        c = 0.5 * (lo + hi)
        a = oc_grid_t(c, 0.0, times)
        lo, hi = (c, hi) if a > alpha else (lo, c)
    return 0.5 * (lo + hi)


class GSDm:
    """Brownsche Bewegung mit Monatsschritten bis T_max Monate (Info-Zeit = Monat / T_max); Blicke an Monaten looks."""

    def __init__(self, n, seed, T_max):
        rng = np.random.default_rng(seed)
        W = np.cumsum(rng.standard_normal((n, T_max)) * math.sqrt(1.0 / T_max), axis=1)
        self.W = np.concatenate([np.zeros((n, 1)), W], axis=1)
        self.n, self.T = n, T_max

    def run(self, theta, C, looks, variant, t0_month=None, alpha_stab=0.05):
        zst = float(norm.isf(alpha_stab))
        n, T = self.n, self.T
        mm = np.arange(T + 1)
        drift = theta * (mm if t0_month is None else np.minimum(mm, t0_month)) / T
        stop = np.zeros(n, bool)
        passed = np.zeros(n, bool)
        crossed = np.zeros(n, bool)
        stale = np.zeros(n, bool)
        t_stop = np.ones(n)
        for i, j in enumerate(looks):
            t = j / T
            Bj = self.W[:, j] + drift[j]
            eff = Bj >= C
            jr = j - 12
            last = (i == len(looks) - 1)
            check = variant in ("each_cont", "each_term", "screen_each") or (variant == "last" and last)
            hold = np.ones(n, bool)
            if check and jr > 0:
                Bs = self.W[:, jr] + drift[jr]
                s = jr / T
                if variant == "screen_each":
                    hold = (Bj - Bs) / math.sqrt(t - s) > Z95
                else:
                    zD = ((Bj - Bs) / (t - s) - Bs / s) / math.sqrt(1.0 / (t - s) + 1.0 / s)
                    hold = zD > -zst
            elif check and variant == "screen_each":
                hold = Bj / math.sqrt(t) > Z95
            act = ~stop
            crossed |= act & eff
            new_pass = act & eff & hold
            if last:
                new_stop = act
            elif variant == "each_term":
                new_stop = act & eff
            else:
                new_stop = new_pass
            passed |= new_pass
            if t0_month is not None and jr >= t0_month:
                stale |= new_pass
            t_stop[new_stop & ~stop] = t
            stop |= new_stop
        return {"pass": float(passed.mean()), "Et": float(t_stop.mean()), "crossed": float(crossed.mean()),
                "stale": float(stale.mean())}

    def design(self, C, looks, variant, alpha_stab=0.05):
        lo, hi = 2.0, 8.0
        for _ in range(44):
            th = 0.5 * (lo + hi)
            pw = self.run(th, C, looks, variant, alpha_stab=alpha_stab)["pass"]
            lo, hi = (th, hi) if pw < 0.8 else (lo, th)
        th = 0.5 * (lo + hi)
        h1 = self.run(th, C, looks, variant, alpha_stab=alpha_stab)
        h0 = self.run(0.0, C, looks, variant, alpha_stab=alpha_stab)
        R = (th / MU_FIX) ** 2
        return {"theta": th, "R_max": R, "alpha_eff": h0["pass"], "EN_H1": R * h1["Et"], "q": h1["pass"] / h1["crossed"],
                "EN_H1_monate_bei_Tmax": h1["Et"] * self.T}


def sec4b(gsd_out):
    P("\n================ (4b) Blickplaene in Monaten (Zone V + K) und Niveau des Stabilitaetstests ================")
    t0c = time.process_time()
    out = {}
    plans = {"V24+K_27_30_33_36": (36, (27, 30, 33, 36)), "V24+K_30_33_36_39": (39, (30, 33, 36, 39)),
             "V24+K_33_36_39_42": (42, (33, 36, 39, 42))}
    for name, (Tm, looks) in plans.items():
        times = [j / Tm for j in looks]
        C = obf_const_t(0.0025, times)
        g = GSDm(500_000, 31108 + Tm, Tm)
        cell = {"C_B_skala": C, "blicke_monate": list(looks), "info_anteile": times,
                "r_je_blick": [12.0 / j for j in looks]}
        for v in ("none", "last", "each_cont", "each_term", "screen_each"):
            d = g.design(C, looks, v)
            for t0m, lab in ((24, "nur_V_teil"),):
                for fm in (1.0, 2.0):
                    res = g.run(fm * d["theta"], C, looks, v, t0_month=t0m)
                    d[f"{lab}_{fm:.0f}MDE"] = {"P_PASS": res["pass"], "P_PASS_veraltet": res["stale"]}
            cell[v] = d
        out[name] = cell
        P(f"{name}: C {C:.4f}, Info-Anteile {', '.join(f'{x:.3f}' for x in times)}")
        for v in ("none", "last", "each_cont", "each_term", "screen_each"):
            d = cell[v]
            P(f"   {v:>11}: Max/N_fix {d['R_max']:.4f}, alpha {d['alpha_eff']:.5f}, E[N|H1] {d['EN_H1']:.4f}, q {d['q']:.4f}; "
              f"Effekt nur in den ersten 24 Monaten (1/2 x theta): P(PASS) {d['nur_V_teil_1MDE']['P_PASS']:.4f}/"
              f"{d['nur_V_teil_2MDE']['P_PASS']:.4f}, veraltet {d['nur_V_teil_1MDE']['P_PASS_veraltet']:.4f}/{d['nur_V_teil_2MDE']['P_PASS_veraltet']:.4f}")
    # Niveau alpha_stab 0,10 / 0,20 an jedem Stopp (gleichverteilte Blicke, K 4)
    lev = {}
    g4m = GSD(1_000_000, 31104)
    C4 = gsd_out["obf_konstante_B_skala"]["4"]
    for r in (0.5, 0.25):
        for a_st in (0.10, 0.20):
            d = g4m.design(C4, 4, r, "each_term", alpha_stab=a_st)
            for t0 in sorted({0.5, round(1 - r, 6)}):
                for fm in (1.0, 2.0):
                    res = g4m.run(fm * d["theta"], C4, 4, r, "each_term", t0=t0, alpha_stab=a_st)
                    d[f"t0{t0:.3f}_{fm:.0f}MDE"] = {"P_PASS": res["pass"], "P_PASS_veraltet": res["stale"]}
            lev[f"r{r:.3f}_astab{a_st}"] = d
            P(f"K 4 gleichverteilt, r {r:.3f}, each_term, alpha_stab {a_st}: Max {d['R_max']:.4f}, alpha {d['alpha_eff']:.5f}, "
              f"E[N|H1] {d['EN_H1']:.4f}, q {d['q']:.4f}; " + "; ".join(
                  f"{k}: {v['P_PASS']:.4f}/{v['P_PASS_veraltet']:.4f}" for k, v in d.items() if k.startswith("t0")))
    out["niveau_sensitivitaet_K4"] = lev
    put("s4b_blickplaene", out)
    P(f"[Zeit (4b): {time.process_time() - t0c:.1f} s CPU]")
    return out


# =====================================================================================
# (5) Schwere Raender, t-Grenzen, Autokorrelation
# =====================================================================================
FS_G = 1.5


def fs_moments(nu, g):
    e_abs = 2 * math.sqrt(nu) * math.gamma((nu + 1) / 2) / (math.sqrt(math.pi) * (nu - 1) * math.gamma(nu / 2))
    mean = e_abs * (g ** 3 - 1 / g) / (1 + g ** 2)
    ex2 = (nu / (nu - 2)) * (g ** 4 + 1 / g ** 2) / (1 + g ** 2)
    return mean, math.sqrt(ex2 - mean ** 2)


def fs_skewness(nu, g):
    def eabs(k):
        return nu ** (k / 2) * math.gamma((k + 1) / 2) * math.gamma((nu - k) / 2) / (math.sqrt(math.pi) * math.gamma(nu / 2))
    def mom(k):
        return eabs(k) * (g ** (k + 2) + (-1) ** k * g ** (-k)) / (1 + g ** 2)
    m1, m2, m3 = mom(1), mom(2), mom(3)
    return (m3 - 3 * m1 * m2 + 2 * m1 ** 3) / (m2 - m1 ** 2) ** 1.5


DISTS = {"normal": None, "t7_kurt5": 7.0, "t4.857_kurt10": 4.0 + 6.0 / 7.0, "t5.2_exkurt5": 5.2, "t4.6_exkurt10": 4.6,
         "skewt7_pos": ("skew", 7.0, FS_G), "skewt7_neg": ("skew", 7.0, 1.0 / FS_G)}


def draw(rng, spec, shape):
    if spec is None:
        return rng.standard_normal(shape)
    if isinstance(spec, float):
        return rng.standard_t(spec, shape) / math.sqrt(spec / (spec - 2))
    _, nu, g = spec
    t = np.abs(rng.standard_t(nu, shape))
    pos = rng.random(shape) < g ** 2 / (1 + g ** 2)
    x = np.where(pos, g * t, -t / g)
    mu, sd = fs_moments(nu, g)
    return (x - mu) / sd


def part_stats(rng, spec, n_paths, n_j, n_a, chunk=20000):
    mj, vj, ma, va = [], [], [], []
    for s in range(0, n_paths, chunk):
        m = min(chunk, n_paths - s)
        xj = draw(rng, spec, (m, n_j))
        xa = draw(rng, spec, (m, n_a))
        mj.append(xj.mean(1)); vj.append(xj.var(1, ddof=1)); ma.append(xa.mean(1)); va.append(xa.var(1, ddof=1))
    return np.concatenate(mj), np.concatenate(vj), np.concatenate(ma), np.concatenate(va)


def rule_eval(mj, vj, ma, va, n_j, n_a, shift_j, shift_a, se_mult_j=None, se_mult_a=None):
    """Entscheidungsgroessen fuer verschobene Mittel (Effekt je Beobachtung shift_j / shift_a)."""
    mj = mj + shift_j
    ma = ma + shift_a
    n = n_j + n_a
    aj, aa = vj / n_j, va / n_a
    if se_mult_j is not None:
        aj, aa = aj * se_mult_j, aa * se_mult_a
    se_d = np.sqrt(aj + aa)
    zD = (mj - ma) / se_d
    df_ws = (aj + aa) ** 2 / (aj ** 2 / (n_j - 1) + aa ** 2 / (n_a - 1))
    sp2 = ((n_j - 1) * vj + (n_a - 1) * va) / (n - 2)
    zD_st = (mj - ma) / np.sqrt(sp2 * (1.0 / n_j + 1.0 / n_a))
    mp = (n_j * mj + n_a * ma) / n
    ss = (n_j - 1) * vj + (n_a - 1) * va + n_j * n_a / n * (mj - ma) ** 2
    vp = ss / (n - 1) / n
    if se_mult_j is not None:
        vp = vp * (n_j * se_mult_j + n_a * se_mult_a) / n
    zp = mp / np.sqrt(vp)
    return {"rej_z": zD < -Z95, "rej_welch": zD < student_t.ppf(0.05, df_ws), "rej_student": zD_st < student_t.ppf(0.05, n - 2),
            "pool_z": zp > Z9975, "pool_t": zp > student_t.isf(0.0025, n - 1)}


def sec5():
    P("\n================ (5) Schwere Raender, t-Grenzen, Autokorrelation ================")
    t0c = time.process_time()
    rng = np.random.default_rng(31105)
    out = {"schiefe_skewt7": fs_skewness(7.0, FS_G)}
    P(f"Schiefe Fernandez-Steel t(7), gamma 1,5: {out['schiefe_skewt7']:.4f} (neg: Vorzeichen gespiegelt)")
    NP = 200_000
    cells = {}
    for n_j in (40, 52):
        for r in (0.5, 0.25):
            n_a = int(round(n_j * (1 - r) / r))
            n = n_j + n_a
            for dname, spec in DISTS.items():
                mj, vj, ma, va = part_stats(rng, spec, NP, n_j, n_a)
                h0 = rule_eval(mj, vj, ma, va, n_j, n_a, 0.0, 0.0)
                mu1 = MU_C / math.sqrt(n)               # homogener Effekt: Gauss-Pool-Power 0,8/0,95
                h1 = rule_eval(mj, vj, ma, va, n_j, n_a, mu1, mu1)
                delta = C80_05 * math.sqrt(1.0 / n_j + 1.0 / n_a)   # Abfall: Gauss-Power 0,80 des Stabilitaetstests
                dr = rule_eval(mj, vj, ma, va, n_j, n_a, 0.0, delta)
                c = {"n_aelter": n_a,
                     "alpha_stab_z": h0["rej_z"].mean(), "alpha_stab_welch": h0["rej_welch"].mean(),
                     "alpha_stab_student": h0["rej_student"].mean(),
                     "alpha_gemeinsam_z": (h0["pool_z"] & ~h0["rej_z"]).mean(),
                     "alpha_gemeinsam_t_welch": (h0["pool_t"] & ~h0["rej_welch"]).mean(),
                     "power_gemeinsam_z": (h1["pool_z"] & ~h1["rej_z"]).mean(),
                     "power_gemeinsam_t_welch": (h1["pool_t"] & ~h1["rej_welch"]).mean(),
                     "q_t_welch": (h1["pool_t"] & ~h1["rej_welch"]).mean() / h1["pool_t"].mean(),
                     "power_abfall_z": dr["rej_z"].mean(), "power_abfall_welch": dr["rej_welch"].mean(),
                     "PASS_nur_aelter_t_welch": (dr["pool_t"] & ~dr["rej_welch"]).mean()}
                cells[f"nj{n_j}_r{r:.2f}_{dname}"] = c
    out["zellen"] = cells
    P("Stabilitaetstest (nominal 0,05) und gemeinsame Regel (nominal alpha 0,002375, Power 0,80) mit geschaetzter Varianz, 200.000 Pfade:")
    P("  Zelle: alpha_stab z / Welch / Student | alpha gemeinsam z / t+Welch | Power gemeinsam z / t+Welch | q t+Welch | "
      "Power gegen Abfall z / Welch (nominal 0,80)")
    for k, c in cells.items():
        P(f"  {k} (n_a {c['n_aelter']}): {c['alpha_stab_z']:.4f} / {c['alpha_stab_welch']:.4f} / {c['alpha_stab_student']:.4f} | "
          f"{c['alpha_gemeinsam_z']:.5f} / {c['alpha_gemeinsam_t_welch']:.5f} | {c['power_gemeinsam_z']:.4f} / "
          f"{c['power_gemeinsam_t_welch']:.4f} | {c['q_t_welch']:.4f} | {c['power_abfall_z']:.4f} / {c['power_abfall_welch']:.4f}")
    # Autokorrelation AR(1): naive SE, SB-max (Block 4, Formel wie oc_sim.py), analytisches c (bekanntes phi)
    ar = {}
    rng2 = np.random.default_rng(31106)
    for phi in (0.0, 0.3):
        for r in (0.5, 0.25):
            n_j = 52
            n_a = int(round(n_j * (1 - r) / r))
            n = n_j + n_a
            NA = 100_000
            # exakte Varianzfaktoren eines Mittels der Laenge m unter AR(1) (Varianz 1)
            def cfac(m):
                k = np.arange(1, m)
                return 1 + 2 * np.sum((1 - k / m) * phi ** k)
            cj, ca = cfac(n_j), cfac(n_a)
            res = {"c_juengst": cj, "c_aelter": ca}
            acc = {key: 0 for key in ("naiv", "sbmax", "c_analytisch", "sbmax_welch")}
            accp = {key: 0 for key in ("naiv", "sbmax", "c_analytisch")}
            chunk = 10000
            for s in range(0, NA, chunk):
                e = rng2.standard_normal((chunk, n))
                x = np.empty_like(e)
                x[:, 0] = e[:, 0] / math.sqrt(1 - phi * phi) if phi else e[:, 0]
                for i in range(1, n):
                    x[:, i] = phi * x[:, i - 1] + e[:, i]
                xa, xj = x[:, :n_a], x[:, n_a:]
                sej = se_rules(xj)
                sea = se_rules(xa)
                D = sej[0] - sea[0]
                mp = x.mean(1)
                sdp = se_rules(x)
                for key, (a_j, a_a, a_p) in {"naiv": (sej[1], sea[1], sdp[1]), "sbmax": (sej[2], sea[2], sdp[2]),
                                             "c_analytisch": (sej[1] * math.sqrt(cj), sea[1] * math.sqrt(ca), sdp[1] * math.sqrt(cfac(n)))}.items():
                    zD = D / np.sqrt(a_j ** 2 + a_a ** 2)
                    acc[key] += int((zD < -Z95).sum())
                    accp[key] += int((mp / a_p > Z9975).sum())
                aj2, aa2 = sej[2] ** 2, sea[2] ** 2
                df = (aj2 + aa2) ** 2 / (aj2 ** 2 / (n_j - 1) + aa2 ** 2 / (n_a - 1))
                acc["sbmax_welch"] += int((D / np.sqrt(aj2 + aa2) < student_t.ppf(0.05, df)).sum())
            for key in acc:
                res[f"alpha_stab_{key}"] = acc[key] / NA
            for key in accp:
                res[f"alpha_gepoolt_{key}"] = accp[key] / NA
            ar[f"phi{phi}_r{r:.2f}"] = res
    out["ar1"] = ar
    P("AR(1), n_juengst 52, 100.000 Pfade: alpha_stab (nominal 0,05) naiv / SB-max Block 4 / c analytisch / SB-max+Welch; gepoolt (nominal 0,0025) naiv / SB-max / c analytisch:")
    for k, v in ar.items():
        P(f"  {k} (c_j {v['c_juengst']:.4f}, c_a {v['c_aelter']:.4f}): {v['alpha_stab_naiv']:.4f} / {v['alpha_stab_sbmax']:.4f} / "
          f"{v['alpha_stab_c_analytisch']:.4f} / {v['alpha_stab_sbmax_welch']:.4f}; {v['alpha_gepoolt_naiv']:.5f} / "
          f"{v['alpha_gepoolt_sbmax']:.5f} / {v['alpha_gepoolt_c_analytisch']:.5f}")
    # analytisch: falsche Varianz -> q = Phi(z95 sqrt(c_used / c_true))
    qa = {}
    for c_true in (1.857, 1.5):
        for c_used in (1.0, 1.3, c_true):
            qa[f"c_true{c_true}_c_used{c_used:.3f}"] = float(norm.cdf(Z95 * math.sqrt(c_used / c_true)))
    out["q_bei_falschem_c"] = qa
    P("q = Phi(z95 sqrt(c_benutzt / c_wahr)) (Abhaengigkeit unterschaetzt): " + "; ".join(f"{k}: {v:.4f}" for k, v in qa.items()))
    put("s5_raender", out)
    P(f"[Zeit (5): {time.process_time() - t0c:.1f} s CPU]")
    return out


def sb_weights(n, mean_block=4.0):
    q = 1.0 - 1.0 / mean_block
    k = np.arange(1, n)
    return 2.0 * (1.0 - k / n) * q ** k


def se_rules(x, mean_block=4.0):
    """(Mittel, naive SE, SB-max-SE, SB-SE) - Formel wie oc_sim.py (ideale stationaere Bootstrap-Varianz, B -> inf)."""
    n = x.shape[1]
    xb = x.mean(axis=1)
    d = x - xb[:, None]
    s = np.sqrt((d * d).sum(axis=1) / (n - 1))
    F = np.fft.rfft(d, axis=1)
    cc = np.fft.irfft(F * np.conj(F), n=n, axis=1) / n
    var_sb = cc[:, 0] + cc[:, 1:] @ sb_weights(n, mean_block)
    se_naive = s / math.sqrt(n)
    se_sb = np.sqrt(np.maximum(var_sb, 0.0) / n)
    return xb, se_naive, np.maximum(se_naive, se_sb), se_sb


# =====================================================================================
# (6) Beispiele A2 und Klasse W
# =====================================================================================
# Akten-Zahlen woertlich aus oc_sim.py (dort: NULL_SIMULATION_A2.md T2/T3/T4/T5, DEC-103 N1 (6)/(8)/(9), REVIEW_A2_TEILC B-4)
A2 = {
    "W1": {"N": {"E": 52, "P2": 208, "P3fix": 248, "P3all": 260}, "kappa": 0.999,
           "zentral": {"SE": {"P2": 7.34, "P3fix": 7.93, "P3all": 6.56}, "nullSD": 6.70, "d95": 11.10, "zentrumSD": 0.23},
           "stress": {"SE": {"P2": 8.25, "P3fix": 8.66, "P3all": 7.39}, "nullSD": 7.53, "d95": 12.47, "zentrumSD": 0.26}},
    "W2": {"N": {"E": 52, "P2": 159, "P3fix": 247, "P3all": 259}, "kappa": 0.815,
           "zentral": {"SE": {"P2": 7.58, "P3fix": 7.93, "P3all": 6.56}, "nullSD": 6.24, "d95": 10.33, "zentrumSD": 2.97},
           "stress": {"SE": {"P2": 8.52, "P3fix": 8.67, "P3all": 7.39}, "nullSD": 7.01, "d95": 11.61, "zentrumSD": 3.34}},
    "klassen": {"zentral": {"E": 43.83, "P2": 42.45, "P3fix": 61.39, "P3all": 8.53},
                "stress": {"E": 49.37, "P2": 47.45, "P3fix": 62.11, "P3all": 9.67}},
    "c_bind": {"E": 1.1491, "P2": 1.3177, "P3fix": 1.168, "P3all": 1.000},
    "tau95": 1.6553, "gate4": 0.9025,
}
COND = ("P2", "P3fix", "P3all")


def a2_cov(win, lin):
    w = A2[win]
    se = w[lin]["SE"]
    k = A2["klassen"][lin]
    vE = k["E"] ** 2 * A2["c_bind"]["E"] / w["N"]["E"]
    vP = {j: k[j] ** 2 * A2["c_bind"][j] / w["N"][j] for j in COND}
    cEP = {j: 0.5 * (vE + vP[j] - se[j] ** 2) for j in COND}
    S = np.zeros((3, 3))
    for a, i in enumerate(COND):
        for b, j in enumerate(COND):
            S[a, b] = se[i] ** 2 if a == b else vE - cEP[i] - cEP[j]
    return S


def a2_full_cov(win, lin, scaled):
    w = A2[win]
    L = w[lin]
    S3 = a2_cov(win, lin)
    se2 = L["SE"]["P2"]
    rho = math.sqrt(max(0.0, 1.0 - (L["zentrumSD"] / se2) ** 2)) if scaled else L["nullSD"] / se2
    sY = se2 if scaled else L["nullSD"]
    S = np.zeros((4, 4))
    S[:3, :3] = S3
    covY = rho * sY * S3[0, :] / se2
    S[3, :3] = covY
    S[:3, 3] = covY
    S[3, 3] = sY ** 2
    return S, np.array([1.0, 1.0, 1.0, w["kappa"]])


def solve_mde(pfun, target=0.8, lo=5.0, hi=80.0):
    if pfun(hi) < target:
        return float("inf")
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if pfun(mid) < target else (lo, mid)
    return 0.5 * (lo + hi)


def sec6(gsd_out):
    P("\n================ (6) Beispiele A2 und Klasse W ================")
    t0c = time.process_time()
    out = {}
    rng = np.random.default_rng(31107)
    NMC = 2_000_000
    E8 = rng.standard_normal((NMC, 8))
    tau_p = Z9975 * A2["tau95"] / Z95

    def builder(lin, scaled, T):
        """Juengster Teil R (12 Monate, Kovarianz W2) und aelterer Teil O (T-12 Monate), so dass die gepoolte Kovarianz
        der OC-Konvention 0,5 (S1 + S2) 12/T entspricht (bei T = 24 exakt W1 / W2)."""
        S1, mf1 = a2_full_cov("W1", lin, scaled)
        S2, mf2 = a2_full_cov("W2", lin, scaled)
        r = 12.0 / T
        Sbar = 0.5 * (S1 + S2)
        SO = (r * Sbar - r * r * S2) / (1 - r) ** 2
        mfp = 0.5 * (mf1 + mf2)
        mfO = (mfp - r * mf2) / (1 - r)
        LO = np.linalg.cholesky(SO + 1e-10 * np.eye(4))
        LR = np.linalg.cholesky(S2 + 1e-10 * np.eye(4))
        YO = E8[:, :4] @ LO.T
        YR = E8[:, 4:] @ LR.T
        Yp = r * YR + (1 - r) * YO
        Sp = r * r * S2 + (1 - r) ** 2 * SO
        sdp = np.sqrt(np.diag(Sp))
        thr_p = np.array([Z9975 * sdp[0], Z9975 * sdp[1], Z9975 * sdp[2], tau_p * sdp[3]])
        se_D = math.sqrt(S2[0, 0] + SO[0, 0])
        D = YR[:, 0] - YO[:, 0]
        return {"Yp": Yp, "mfp": mfp, "thr_p": thr_p, "YR0": YR[:, 0], "sdR0": math.sqrt(S2[0, 0]), "D": D, "se_D": se_D,
                "mfR0": mf2[0], "mfO0": mfO[0], "r": r}

    def pfun(lin, scaled, conds, gate, T, mode):
        B = builder(lin, scaled, T)
        idx = [i for i, c in enumerate(("P2", "P3fix", "P3all", "null")) if c in conds]
        base_ok = None

        def pw(pi):
            ok = np.ones(NMC, bool)
            for i in idx:
                ok &= (B["Yp"][:, i] + B["mfp"][i] * pi) > B["thr_p"][i]
            if mode == "screen":
                ok &= (B["YR0"] + B["mfR0"] * pi) > Z95 * B["sdR0"]
            elif mode == "stab":
                ok &= (B["D"] + (B["mfR0"] - B["mfO0"]) * pi) / B["se_D"] > -Z95
            return gate * float(ok.mean())
        return pw, B

    FULL = ["P2", "P3fix", "P3all", "null"]
    scan = {}
    for T in (24, 27, 30, 36, 42, 48, 60, 72, 84, 96, 120):
        TT = float(T) + (1e-6 if T == 24 else 0.0)
        row = {}
        f6s, B = pfun("stress", True, FULL, A2["gate4"], TT, "screen")
        row["Q6_a_screen"] = solve_mde(f6s)
        f6c, _ = pfun("stress", True, FULL, A2["gate4"], TT, "stab")
        row["Q6_c_stab_exakt"] = solve_mde(f6c)
        f6i, _ = pfun("stress", True, FULL, A2["gate4"], TT, "none")
        row["Q6_c_unabh_0.8_0.95"] = solve_mde(f6i, target=0.8 / 0.95)
        row["Q6_pool_ohne"] = solve_mde(f6i)
        m = row["Q6_c_stab_exakt"]
        row["q_bei_MDE"] = f6c(m) / f6i(m)
        f1c, B1 = pfun("zentral", False, ["P2"], 1.0, TT, "stab")
        row["Q1_c_grundfassung"] = solve_mde(f1c)
        f1s, _ = pfun("zentral", False, ["P2"], 1.0, TT, "screen")
        row["Q1_a_grundfassung"] = solve_mde(f1s)
        row["SE_D_stress_bp"] = B["se_D"]
        row["SQ_c"] = row["Q6_c_stab_exakt"] / row["Q1_c_grundfassung"]
        row["SQ_a"] = row["Q6_a_screen"] / row["Q1_a_grundfassung"]
        scan[str(T)] = row
    out["a2_laengen_scan"] = scan
    P("A2 MDE80 (bp) gegen Konfirmationslaenge T Monate: Q6 (a) Screen | Q6 (c) exakt | Q6 (c) unabh. Ziel 0,8/0,95 (OC) | "
      "Q6 gepoolt ohne | q an MDE | Q1 (c) / Q1 (a) | SQ (c) / SQ (a) | SE(D) stress")
    for T, v in scan.items():
        P(f"   T {T}: {v['Q6_a_screen']:.3f} | {v['Q6_c_stab_exakt']:.3f} | {v['Q6_c_unabh_0.8_0.95']:.3f} | {v['Q6_pool_ohne']:.3f} | "
          f"{v['q_bei_MDE']:.4f} | {v['Q1_c_grundfassung']:.3f} / {v['Q1_a_grundfassung']:.3f} | {v['SQ_c']:.4f} / {v['SQ_a']:.4f} | {v['SE_D_stress_bp']:.3f}")
    # Schutz A2 bei T = 24: Effekt nur in W1 (aelter), Groesse = MDE (c)
    prot = {}
    for T in (24, 42):
        TT = float(T) + (1e-6 if T == 24 else 0.0)
        B = builder("stress", True, TT)
        r = B["r"]
        m = scan[str(T)]["Q6_c_stab_exakt"]
        for lab, (ej, ea) in {"nur_aelter_1MDE": (0.0, 1.0), "nur_aelter_2MDE": (0.0, 2.0), "abklingend_1MDE": (0.5, 1.0),
                              "homogen_1MDE": (1.0, 1.0)}.items():
            pi_R, pi_O = ej * m, ea * m
            S2mf = a2_full_cov("W2", "stress", True)[1]
            mfO = np.array([1.0, 1.0, 1.0, (0.5 * (A2["W1"]["kappa"] + A2["W2"]["kappa"]) - r * A2["W2"]["kappa"]) / (1 - r)])
            mean_p = r * S2mf * pi_R + (1 - r) * mfO * pi_O
            res = {}
            for mode in ("screen", "stab"):
                ok = np.ones(NMC, bool)
                for i in range(4):
                    ok &= (B["Yp"][:, i] + mean_p[i]) > B["thr_p"][i]
                if mode == "screen":
                    ok &= (B["YR0"] + pi_R) > Z95 * B["sdR0"]
                else:
                    ok &= (B["D"] + pi_R - pi_O) / B["se_D"] > -Z95
                res[mode] = A2["gate4"] * float(ok.mean())
            prot[f"T{T}_{lab}"] = res
    out["a2_schutz"] = prot
    P("A2 Schutz (Effekt in bp als Vielfaches der MDE (c) dieser Laenge; gleiche Effektgroesse fuer beide Regeln): P(PASS) Screen (a) / Stabilitaet (c): " +
      "; ".join(f"{k}: {v['screen']:.4f} / {v['stab']:.4f}" for k, v in prot.items()))

    # Zeitpunkte A2: Lesart B, F1: V = 24 Monate (2024-07..2026-06), Luecke 2026-07..09, K ab 2026-10-01
    Ts = np.array([float(t) for t in scan.keys()])

    def T_for(target, arr):
        arr = np.asarray(arr)
        if not np.isfinite(arr).any() or np.nanmin(arr) > target:
            return float("inf")
        if arr[0] <= target:
            return float(Ts[0]) * (arr[0] / target) ** 2
        for i in range(1, len(Ts)):
            if arr[i] <= target:
                x0, x1 = math.log(Ts[i - 1]), math.log(Ts[i])
                y0, y1 = math.log(arr[i - 1]), math.log(arr[i])
                return math.exp(x0 + (math.log(target) - y0) * (x1 - x0) / (y1 - y0))
        return float("inf")

    def date_F1(T):
        if not math.isfinite(T):
            return "nie"
        if T <= 27.0:
            return "2027-01"
        return months_to_ym(2026, 10, T - 24.0)

    def date_cont(T, avail=30.0):
        if not math.isfinite(T):
            return "nie"
        return "2027-01" if T <= avail else months_to_ym(2024, 7, T)

    A2d = {}
    for ses in (22.0, 25.0):
        c = {}
        for key in ("Q6_a_screen", "Q6_c_stab_exakt", "Q6_c_unabh_0.8_0.95"):
            T = T_for(ses, [v[key] for v in scan.values()])
            c[key] = {"T_monate": T, "termin_F1_K_ab_2026_10": date_F1(T), "termin_OC_konvention_ab_2024_07": date_cont(T, 27.0)}
        A2d[f"sesoi{ses:.0f}"] = c
    out["a2_termine"] = A2d
    P("A2 fruehester Konfirmationszeitpunkt (Lesart B; F1: V 24 Monate + K ab 2026-10-01; OC-Konvention: durchgehend ab 2024-07):")
    for k, c in A2d.items():
        P("   " + k + ": " + "; ".join(f"{kk}: T {g4(v['T_monate'])} Mon. -> {v['termin_F1_K_ab_2026_10']} (OC-Konv. {v['termin_OC_konvention_ab_2024_07']})"
                                  for kk, v in c.items()))
    floor_a = (Z95 + float(Z(0.8 / A2["gate4"]))) * A2["W2"]["stress"]["SE"]["P2"]
    out["a2_boden_a"] = floor_a
    P(f"A2 Boden unter (a): {floor_a:.3f} bp")

    # Klasse W: Wochen-IC; SE_12 = SD / sqrt(52)
    des = gsd_out["designs"]
    rr = np.array([0.25, 1 / 3, 0.5])
    Rm = [des[f"K4_r{x:.3f}_each_term"]["R_max"] for x in (0.25, 1 / 3, 0.5)]
    En = [des[f"K4_r{x:.3f}_each_term"]["EN_H1"] for x in (0.25, 1 / 3, 0.5)]
    Rint = lambda r: float(np.interp(min(max(r, 0.25), 0.5), rr, Rm))
    Eint = lambda r: float(np.interp(min(max(r, 0.25), 0.5), rr, En))
    W = {}
    for sd in (0.09, 0.13):
        for ses in (0.040, 0.0085):
            se12 = sd / math.sqrt(52.0)
            # (a) Screen 0,05: Boden und T
            floor = C80_05 * se12
            if floor >= ses:
                Ta = float("inf")
            else:
                # MDE in SE_12-Einheiten haengt nur von r = 52/T ab
                g_ = lambda T: mde("screen", min(52.0 / T, 0.999999)) * se12 - ses
                Ta = optimize.brentq(g_, 52.0 + 1e-6, 52.0 * 4000) if g_(52.0 + 1e-6) > 0 else (MU_FIX * sd / ses) ** 2
            # (c) Stabilitaet: T <= 52 Wochen -> kein aelterer Teil (Test entfaellt), sonst Pool-Power 0,8/0,95
            Tp = (MU_FIX * sd / ses) ** 2
            Tc = Tp if Tp <= 52.0 else (MU_C * sd / ses) ** 2
            rc = min(1.0, 52.0 / Tc)
            cell = {"SE12": se12, "boden_a": floor, "T_a_wochen": Ta, "T_c_wochen": Tc, "T_pool_ohne_wochen": Tp, "r_c": rc,
                    "T_c_GSD_max_wochen": Tc * Rint(rc), "T_c_GSD_EN_H1_wochen": Tc * Eint(rc),
                    "MDE_a_bei_130W": mde("screen", 52.0 / 130.0) * se12, "MDE_c_bei_130W": MU_C * sd / math.sqrt(130.0),
                    "MDE_a_bei_104W": mde("screen", 0.5) * se12, "MDE_c_bei_104W": MU_C * sd / math.sqrt(104.0)}
            for lab in ("T_a_wochen", "T_c_wochen", "T_c_GSD_max_wochen"):
                Tm = cell[lab] * 12 / 52 if math.isfinite(cell[lab]) else float("inf")
                cell[lab.replace("wochen", "monate")] = Tm
                cell[lab.replace("_wochen", "_termin_B")] = date_cont(Tm, 30.0)
                cell[lab.replace("_wochen", "_jahre")] = Tm / 12 if math.isfinite(Tm) else float("inf")
            W[f"sd{sd}_sesoi{ses}"] = cell
    out["klasse_W"] = W
    P("Klasse W (Wochen-IC, SE_12 = SD/sqrt(52)); Lesart B, F2 durchgehend ab 2024-07, bei Registrierung 2027-01 30 Monate:")
    for k, c in W.items():
        P(f"   {k}: SE_12 {c['SE12']:.5f}, Boden (a) {c['boden_a']:.4f}; MDE80 bei 104 / 130 Wochen (a) {c['MDE_a_bei_104W']:.4f} / "
          f"{c['MDE_a_bei_130W']:.4f}, (c) {c['MDE_c_bei_104W']:.4f} / {c['MDE_c_bei_130W']:.4f}; T (a) {g4(c['T_a_monate'])} Mon. -> "
          f"{c['T_a_termin_B']}; T (c) {g4(c['T_c_monate'])} Mon. ({g4(c['T_c_jahre'])} J.) -> {c['T_c_termin_B']}; "
          f"GSD-Max (c) {g4(c['T_c_GSD_max_monate'])} Mon. -> {c['T_c_GSD_max_termin_B']}")
    put("s6_beispiele", out)
    P(f"[Zeit (6): {time.process_time() - t0c:.1f} s CPU]")
    return out


# =====================================================================================
# (7) Zusatzrechnungen fuer den Text
# =====================================================================================
def sec7():
    P("\n================ (7) Zusatzrechnungen ================")
    out = {}
    C4 = RES["s4_gsd"]["obf_konstante_B_skala"]["4"]
    # Erstkreuzung am letzten Blick (B(1-r) < C, B(1) >= C) erzwingt z_D > -C sqrt(r/(1-r)) wenn 1-r ein Blick ist
    out["schranke_zD_letzter_blick_r025_K4"] = -C4 * math.sqrt(0.25 / 0.75)
    P(f"Schranke: Erstkreuzung am letzten Blick (K 4, r 1/4, Blick 3 bei 1 - r) => z_D > -C sqrt(r/(1-r)) = {out['schranke_zD_letzter_blick_r025_K4']:.4f} > -1,6449")
    # Drop-Erkennung in SE_12: mittleres z_D bei Effekt nur aelter = -mu sqrt(1-r)
    out["mittleres_zD_nur_aelter_MDEc"] = {f"r{r:.3f}": -MU_C * math.sqrt(r) * math.sqrt(1 - r) for r in (0.5, 1 / 3, 0.25, 1 / 6, 0.1)}
    P("Mittleres z_D bei Effekt nur im aelteren Teil in Hoehe MDE_c (= -MU_C sqrt(r(1-r))): " +
      "; ".join(f"{k}: {v:.4f}" for k, v in out["mittleres_zD_nur_aelter_MDEc"].items()))
    # Screen 0,20: Boden (z_0,80 + z80) SE_12 (OC (a) Nr. 6)
    out["boden_screen020"] = float(norm.isf(0.20)) + Z80
    P(f"Boden Screen 0,20: {out['boden_screen020']:.4f} SE_12")
    # aelterer Teil am ersten Blick der Monatsplaene
    out["aelterer_teil_erster_blick_monate"] = {"27_30_33_36": 27 - 12, "30_33_36_39": 30 - 12, "33_36_39_42": 33 - 12}
    P("Aelterer Teil am ersten Blick (Monate): " + ", ".join(f"Plan {k}: {v}" for k, v in out["aelterer_teil_erster_blick_monate"].items()))
    # Zitierte OC-Werte (nur gelesen, Repository unveraendert)
    oc_path = os.path.join("/home/user/scinance/scinance3-impl/state/prd_analyse_2026-11-01/scripts", "oc_results.json")
    try:
        with open(oc_path, encoding="ascii") as fh:
            oc = json.load(fh)
        cit = {"gitter_fut_R_max": oc["b"]["gitter"]["alpha0.0025_fut"]["R_max"],
               "gitter_fut_EN_H1": oc["b"]["gitter"]["alpha0.0025_fut"]["EN_H1"],
               "gitter_fut_EN_H0": oc["b"]["gitter"]["alpha0.0025_fut"]["EN_H0"],
               "screen_all_r05_R_max": oc["b"]["monte_carlo_1e6"]["screen_all_r0.500_nofut"]["R_max"],
               "screen_all_r05_EN_H1": oc["b"]["monte_carlo_1e6"]["screen_all_r0.500_nofut"]["EN_H1"],
               "screen_all_r025_t05_veraltet": oc["b"]["monte_carlo_1e6"]["screen_all_r0.250_nofut"]["effekt_bis_t0.500_1MDE"]["P_PASS_veraltet"],
               "A2_sesoi22_P6_lesartB": oc["h"]["klasse_E_A2"]["sesoi22.0"]["lesart_B_ende_P6_stabilitaet"],
               "A2_sesoi25_P6_lesartB": oc["h"]["klasse_E_A2"]["sesoi25.0"]["lesart_B_ende_P6_stabilitaet"],
               "A2_sesoi25_fest_lesartB": oc["h"]["klasse_E_A2"]["sesoi25.0"]["lesart_B_ende_fest"],
               "W_sd013_P6_lesartB": oc["h"]["klasse_W_termine"]["sd0.13_sesoi0.04_P6_stabilitaet_fest"]["lesart_B_ab_2024_07"]}
    except (OSError, KeyError, ValueError) as exc:
        cit = {"fehler": str(exc)}
    out["zitierte_oc_werte"] = cit
    P("Zitierte OC-Werte (oc_results.json, nur gelesen): " + "; ".join(f"{k}: {v}" for k, v in cit.items()))
    put("s7_zusatz", out)


def main():
    P("Stabilitaetstest P-2 (c) - stab_sim.py (deterministisch; Seeds 31104..31107, 31144/31147/31150)")
    sec0()
    sec1()
    sec2()
    sec3()
    g = sec4()
    sec4b(g)
    sec5()
    sec6(g)
    sec7()
    put("meta.cpu_sekunden", time.process_time() - T_START)
    with open(os.path.join(HERE, "stab_results.json"), "w", encoding="ascii") as fh:
        json.dump(RES, fh, indent=1, ensure_ascii=True, default=str)
    P(f"\nGesamt-CPU: {time.process_time() - T_START:.1f} s; stab_results.json geschrieben.")


if __name__ == "__main__":
    main()
