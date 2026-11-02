#!/usr/bin/env python3
"""Gesamt-Operationscharakteristik (OC) des Pakets "Verfassung 3.1" (2026-11-02).

Rolle: Herleitung mit eigenem Code. Nur Formeln und Simulation; keine Marktdaten, keine Siegeldatei,
kein Harvest-Client, kein Netz. Eingangszahlen ausschliesslich aus der Akte (Quellen im Kommentar je Konstante).
Deterministisch (feste Seeds je Abschnitt), nur numpy/scipy, lauffaehig mit `python3 -I oc_sim.py`.
Ausgaben: oc_results.json (neben diesem Skript) und die Konsolenausgabe (-> oc_sim.out).
Abschnitte (a)..(h) wie im Auftrag BRIEF_oc_verfassung31.md.
"""
import json
import math
import os
import sys
import time

import numpy as np
from scipy import integrate, optimize, special, stats
from scipy.stats import norm

T_START = time.process_time()
HERE = os.path.dirname(os.path.abspath(__file__))
RES = {"meta": {"skript": "oc_sim.py", "numpy": np.__version__, "python": sys.version.split()[0]}}

Z = norm.ppf
Z95 = float(Z(0.95))          # 1,6449 einseitig 0,05
Z9975 = float(Z(0.9975))      # 2,8070 einseitig 0,0025
Z80 = float(Z(0.80))          # 0,8416
MU_FIX = Z9975 + Z80          # Drift fuer gepoolt 0,0025 / Power 0,80 (3,6487)
C80_05 = Z95 + Z80            # 2,4865


def r6(x):
    if isinstance(x, (list, tuple)):
        return [r6(v) for v in x]
    if isinstance(x, dict):
        return {k: r6(v) for k, v in x.items()}
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


def f4(x):
    return f"{x:.4f}"


def biv_upper(a, b, rho):
    """P(X > a, Y > b) fuer standard-bivariat-normal mit Korrelation rho (1-D-Quadratur)."""
    if rho >= 1.0 - 1e-12:
        return float(norm.sf(max(a, b)))
    s = math.sqrt(1.0 - rho * rho)
    lo = max(a, -12.0)
    f = lambda x: norm.pdf(x) * norm.sf((b - rho * x) / s)
    val, _ = integrate.quad(f, lo, 14.0, epsabs=1e-14, epsrel=1e-11, limit=400)
    return float(val)


# =====================================================================================
# (a) Entscheidungsregel P-2 (a) gegen C.10 und DEC-52
# =====================================================================================
def p2a_power(mu, r, mu_rec=None, rho=None, zp=Z9975, zs=Z95):
    """P(Z_pool > zp, Z_rec > zs); Z_pool-Mittel mu, Z_rec-Mittel mu_rec (Default mu*sqrt(r))."""
    rho = math.sqrt(r) if rho is None else rho
    mu_rec = mu * rho if mu_rec is None else mu_rec
    return biv_upper(zp - mu, zs - mu_rec, rho)


def two_window_power(m_rec, m_old, z=Z95):
    """C.10-artig: juengster und aelterer Teil je einseitig 0,05 (unabhaengige Daten)."""
    return float(norm.sf(z - m_rec) * norm.sf(z - m_old))


def dec52_power(m_rec, m_old, r, zp=2.5287, screen="halb"):
    """DEC-52 in der DEC-94-Fassung: gepoolt Z >= zp und je Fenster Schaetzer >= 0,5 zp SE_gepoolt
    (z-Einheiten: Z_w >= 0,5 zp sqrt(Anteil_w)); screen='vorzeichen': nur Z_w > 0."""
    sr, so = math.sqrt(r), math.sqrt(1.0 - r)
    if screen == "halb":
        s_r, s_o = 0.5 * zp * sr, 0.5 * zp * so
    else:
        s_r, s_o = 0.0, 0.0
    f = lambda zr: norm.pdf(zr - m_rec) * norm.sf(max(s_o, (zp - sr * zr) / so) - m_old)
    val, _ = integrate.quad(f, s_r, m_rec + 14.0, epsabs=1e-14, epsrel=1e-11, limit=400)
    return float(val)


def sec_a():
    P("\n================ (a) Entscheidungsregel P-2 (a) gegen C.10 und DEC-52 ================")
    t0 = time.process_time()
    # Reproduktion Akte (review_calc C): DEC-52-H0-Raten bei r = 1/2
    rep = {}
    for zc in (2.3263, 2.5287):
        rep[f"z{zc}_nur_vorzeichen"] = dec52_power(0, 0, 0.5, zc, "vorzeichen")
        rep[f"z{zc}_mit_halbscreens"] = dec52_power(0, 0, 0.5, zc, "halb")
    put("a.reproduktion_dec52_H0", rep)
    P("Reproduktion DEC-52-H0-Rate (Akte 0,00991/0,00847 bei z 2,3263; 0,00571/0,00500 bei 2,5287):",
      {k: round(v, 5) for k, v in rep.items()})
    put("a.reproduktion_K4", {"gepoolt0025_vs_C10_je080": MU_FIX ** 2 / (2 * C80_05 ** 2),
                              "C10_gemeinsam080_vs_je080": (Z95 + Z(math.sqrt(0.8))) ** 2 / C80_05 ** 2,
                              "C10_gemeinsam080_vs_gepoolt0025": 2 * (Z95 + Z(math.sqrt(0.8))) ** 2 / MU_FIX ** 2,
                              "gepoolt0025_power_bei_C10_MDE": float(norm.sf(Z9975 - C80_05 * math.sqrt(2)))})
    P("Reproduktion K-4: 1,0766 / 1,3558 / 1,2593 / 0,761 ->",
      round(MU_FIX ** 2 / (2 * C80_05 ** 2), 4), round((Z95 + Z(math.sqrt(0.8))) ** 2 / C80_05 ** 2, 4),
      round(2 * (Z95 + Z(math.sqrt(0.8))) ** 2 / MU_FIX ** 2, 4), round(float(norm.sf(Z9975 - C80_05 * math.sqrt(2))), 4))

    info_C10_je = 2 * C80_05 ** 2                      # 12,366 (in 1/theta^2)
    info_C10_gem = 2 * (Z95 + Z(math.sqrt(0.8))) ** 2  # 16,762
    info_pool = MU_FIX ** 2                            # 13,313
    put("a.info_einheiten", {"C10_je080": info_C10_je, "C10_gemeinsam080": info_C10_gem, "gepoolt0025": info_pool})
    out = {}
    effs = (0.0, 0.5, 1.0, 1.5)
    P("Einheiten: Information in 1/theta^2; MDE = Effekt, bei dem P-2 (a) mit den gegebenen Daten Power 0,80 hat.")
    P(f"{'r':>6} {'alpha_P2a':>10} {'mu*':>7} {'Faktor/C10je':>12} {'/C10gem':>8} {'/gepoolt':>9} | "
      f"Power bei 0/0,5/1/1,5 MDE: P2a | gepoolt | C.10(-artig) | DEC-52(2,5287)")
    for r in (0.5, 1 / 3, 0.25):
        rho = math.sqrt(r)
        a_eff = p2a_power(0.0, r)
        mu_star = optimize.brentq(lambda m: p2a_power(m, r) - 0.8, 2.0, 9.0, xtol=1e-12)
        # C.10-artig (aelterer/juengster Teil je 0,05) und DEC-52: eigene Datenbedarfe fuer Power 0,80
        mu_c10 = optimize.brentq(lambda m: two_window_power(m * rho, m * math.sqrt(1 - r)) - 0.8, 2.0, 12.0, xtol=1e-12)
        mu_d52 = optimize.brentq(lambda m: dec52_power(m * rho, m * math.sqrt(1 - r), r) - 0.8, 2.0, 12.0, xtol=1e-12)
        cell = {"rho_pool_screen": rho, "alpha_eff_P2a": a_eff, "alpha_eff_C10artig": two_window_power(0, 0),
                "alpha_eff_DEC52_25287": dec52_power(0, 0, r), "alpha_eff_DEC52_23263": dec52_power(0, 0, r, 2.3263),
                "mu_star_P2a": mu_star, "info_P2a": mu_star ** 2,
                "faktor_P2a_vs_C10je080": mu_star ** 2 / info_C10_je,
                "faktor_P2a_vs_C10gem080": mu_star ** 2 / info_C10_gem,
                "faktor_P2a_vs_gepoolt": mu_star ** 2 / info_pool,
                "info_C10artig_gem080": mu_c10 ** 2, "faktor_C10artig_vs_C10je080": mu_c10 ** 2 / info_C10_je,
                "info_DEC52_080": mu_d52 ** 2, "faktor_DEC52_vs_C10je080": mu_d52 ** 2 / info_C10_je,
                "power": {}}
        for f in effs:
            m = f * mu_star
            cell["power"][str(f)] = {
                "P2a": p2a_power(m, r), "gepoolt_ohne_screen": float(norm.sf(Z9975 - m)),
                "C10artig": two_window_power(m * rho, m * math.sqrt(1 - r)),
                "DEC52_25287": dec52_power(m * rho, m * math.sqrt(1 - r), r),
                "DEC52_23263": dec52_power(m * rho, m * math.sqrt(1 - r), r, 2.3263)}
        # Regime: Effekt nur im aelteren Teil (juengster Teil 0); und Abklingen (juengster Teil halber Effekt)
        reg = {}
        for f in (0.5, 1.0, 1.5, 2.0, 3.0, 5.0):
            m_old = f * mu_star * math.sqrt(1 - r)
            m_pool = math.sqrt(1 - r) * m_old
            reg[str(f)] = {"P2a": p2a_power(m_pool, r, mu_rec=0.0),
                           "gepoolt_ohne_screen": float(norm.sf(Z9975 - m_pool)),
                           "C10artig": two_window_power(0.0, m_old),
                           "DEC52_25287": dec52_power(0.0, m_old, r)}
        cell["nur_aelterer_teil"] = reg
        cell["grenzwert_nur_aelterer_teil"] = {"P2a": float(norm.sf(Z95)), "C10artig": float(norm.sf(Z95)),
                                               "DEC52_25287": float(norm.sf(0.5 * 2.5287 * rho)), "gepoolt_ohne_screen": 1.0}
        dec = {}
        for f in (1.0, 1.5):
            m_old = f * mu_star * math.sqrt(1 - r)
            m_rec = 0.5 * f * mu_star * rho
            m_pool = math.sqrt(1 - r) * m_old + rho * m_rec
            dec[str(f)] = {"P2a": p2a_power(m_pool, r, mu_rec=m_rec), "gepoolt_ohne_screen": float(norm.sf(Z9975 - m_pool)),
                           "C10artig": two_window_power(m_rec, m_old), "DEC52_25287": dec52_power(m_rec, m_old, r)}
        cell["juengster_teil_halber_effekt"] = dec
        key = {0.5: "r1_2", 1 / 3: "r1_3", 0.25: "r1_4"}[r]
        out[key] = cell
        pw = cell["power"]
        P(f"{r:6.3f} {a_eff:10.6f} {mu_star:7.4f} {cell['faktor_P2a_vs_C10je080']:12.4f} {cell['faktor_P2a_vs_C10gem080']:8.4f} "
          f"{cell['faktor_P2a_vs_gepoolt']:9.4f} | " +
          " ".join(f"{pw[str(f)]['P2a']:.4f}" for f in effs) + " | " +
          " ".join(f"{pw[str(f)]['gepoolt_ohne_screen']:.4f}" for f in effs) + " | " +
          " ".join(f"{pw[str(f)]['C10artig']:.4f}" for f in effs) + " | " +
          " ".join(f"{pw[str(f)]['DEC52_25287']:.4f}" for f in effs))
        P(f"       alpha_eff C.10-artig {cell['alpha_eff_C10artig']:.6f}; DEC-52 z2,5287 {cell['alpha_eff_DEC52_25287']:.6f}, "
          f"z2,3263 {cell['alpha_eff_DEC52_23263']:.6f}; Datenbedarf C.10-artig gem.0,80 / C10je {cell['faktor_C10artig_vs_C10je080']:.4f}; "
          f"DEC-52 / C10je {cell['faktor_DEC52_vs_C10je080']:.4f}")
        P("       Effekt nur im aelteren Teil (f x MDE): " + "; ".join(
            f"f {k}: P2a {v['P2a']:.4f} gepoolt {v['gepoolt_ohne_screen']:.4f} C10 {v['C10artig']:.4f} DEC52 {v['DEC52_25287']:.4f}"
            for k, v in reg.items()))
        P("       Grenzwert f->inf: P2a/C10 0,05; DEC-52", round(cell["grenzwert_nur_aelterer_teil"]["DEC52_25287"], 4), "; gepoolt 1")
        P("       juengster Teil halber Effekt: " + "; ".join(
            f"f {k}: P2a {v['P2a']:.4f} gepoolt {v['gepoolt_ohne_screen']:.4f} C10 {v['C10artig']:.4f} DEC52 {v['DEC52_25287']:.4f}"
            for k, v in dec.items()))
    put("a.zellen", out)

    # Korrelationsannahme: Informationsanteil r_I des juengsten Fensters weicht vom Kalenderanteil ab (Vol-Regime)
    alt = {}
    for rI in (0.15, 0.25, 1 / 3, 0.5, 0.75):
        a_eff = p2a_power(0.0, rI)
        mu_s = optimize.brentq(lambda m: p2a_power(m, rI) - 0.8, 2.0, 9.0, xtol=1e-12)
        alt[f"{rI:.3f}"] = {"rho": math.sqrt(rI), "alpha_eff": a_eff, "faktor_vs_gepoolt": mu_s ** 2 / info_pool,
                            "faktor_vs_C10je080": mu_s ** 2 / info_C10_je}
    put("a.korrelationsannahme_infoanteil", alt)
    P("Informationsanteil r_I des juengsten Fensters (Korrelation sqrt(r_I)): " + "; ".join(
        f"r_I {k}: alpha {v['alpha_eff']:.6f}, Daten/gepoolt {v['faktor_vs_gepoolt']:.4f}, /C10je {v['faktor_vs_C10je080']:.4f}"
        for k, v in alt.items()))

    # MDE in Einheiten der SE eines 12-Monats-Fensters (SE_12) und Boden durch den REZENZ-Screen
    se12 = {}
    for r in (0.5, 1 / 3, 0.25):
        key = {0.5: "r1_2", 1 / 3: "r1_3", 0.25: "r1_4"}[r]
        se12[key] = {"P2a_MDE_in_SE12": out[key]["mu_star_P2a"] * math.sqrt(r)}
    se12["boden_T_unendlich"] = C80_05
    se12["C10_je080_in_SE12"] = C80_05
    se12["C10_gem080_in_SE12"] = Z95 + Z(math.sqrt(0.8))
    put("a.MDE_in_SE12", se12)
    P("MDE in SE_12-Einheiten (SE eines 12-Monats-Fensters): " + "; ".join(f"{k} {v:.4f}" if not isinstance(v, dict) else f"{k} {v['P2a_MDE_in_SE12']:.4f}" for k, v in se12.items()))
    # Screen-Alternativen: Niveau alpha_s des Screens -> Boden der MDE (T -> inf) und Grenzwert falsch-PASS (Effekt nur aelter)
    scr = {}
    for a_s in (0.05, 0.10, 0.20, 0.50):
        zs = float(Z(1 - a_s))
        cell = {"z_screen": zs, "MDE_boden_in_SE12": zs + Z80, "grenzwert_PASS_effekt_nur_aelter": a_s}
        for r in (0.5, 1 / 3, 0.25):
            mu = optimize.brentq(lambda m: p2a_power(m, r, zs=zs) - 0.8, 1.0, 12.0, xtol=1e-12)
            cell[f"r{r:.3f}"] = {"alpha_eff": p2a_power(0.0, r, zs=zs), "MDE_in_SE12": mu * math.sqrt(r),
                                 "daten_vs_gepoolt": mu ** 2 / info_pool,
                                 "PASS_nur_aelter_1MDE": p2a_power(mu * (1 - r), r, mu_rec=0.0, zs=zs),
                                 "PASS_nur_aelter_2MDE": p2a_power(2 * mu * (1 - r), r, mu_rec=0.0, zs=zs)}
        scr[str(a_s)] = cell
    put("a.screen_niveau_alternativen", scr)
    P("Screen-Niveau alpha_s: Boden MDE/SE_12, und je r: alpha_eff, MDE/SE_12, Daten/gepoolt, PASS bei Effekt nur aelter (1/2 MDE): ")
    for k, v in scr.items():
        P(f"   alpha_s {k}: Boden {v['MDE_boden_in_SE12']:.4f}; " + "; ".join(
            f"r {rk[1:]}: {vv['alpha_eff']:.6f}, {vv['MDE_in_SE12']:.4f}, {vv['daten_vs_gepoolt']:.4f}, {vv['PASS_nur_aelter_1MDE']:.4f}/{vv['PASS_nur_aelter_2MDE']:.4f}"
            for rk, vv in v.items() if rk.startswith("r")))
    # P-6-Lesart: gepoolt 0,0025 plus registrierter Stabilitaetstest (Abfall juengster gegen aelteren Teil, einseitig 0,05)
    stab = {}
    mu_s = Z9975 + float(Z(0.8 / 0.95))
    for r in (0.5, 1 / 3, 0.25):
        c = {"alpha_eff": 0.0025 * 0.95, "mu_star": mu_s, "daten_vs_gepoolt": mu_s ** 2 / info_pool,
             "daten_vs_C10je080": mu_s ** 2 / info_C10_je, "MDE_in_SE12": mu_s * math.sqrt(r), "korrelation_pool_diff": 0.0}
        for f in (1.0, 2.0, 3.0, 5.0):
            m_pool = (1 - r) * f * mu_s
            m_diff = -f * mu_s * math.sqrt(r * (1 - r))
            c[f"PASS_nur_aelter_{f:.0f}MDE"] = float(norm.sf(Z9975 - m_pool) * norm.sf(-Z95 - m_diff))
        for f in (1.0,):
            m_pool = (1 - r) * f * mu_s + r * 0.5 * f * mu_s
            m_diff = -0.5 * f * mu_s * math.sqrt(r * (1 - r))
            c["PASS_juengster_halber_effekt_1MDE"] = float(norm.sf(Z9975 - m_pool) * norm.sf(-Z95 - m_diff))
        stab[f"r{r:.3f}"] = c
    put("a.stabilitaetstest_P6", stab)
    P("P-6-Lesart (gepoolt 0,0025 + Stabilitaetstest Abfall einseitig 0,05; unabhaengig vom gepoolten Z): " + "; ".join(
        f"{k}: alpha {v['alpha_eff']:.6f}, Daten/gepoolt {v['daten_vs_gepoolt']:.4f}, /C10je {v['daten_vs_C10je080']:.4f}, MDE/SE12 {v['MDE_in_SE12']:.4f}, "
        f"PASS nur aelter 1/2/3/5 MDE {v['PASS_nur_aelter_1MDE']:.4f}/{v['PASS_nur_aelter_2MDE']:.4f}/{v['PASS_nur_aelter_3MDE']:.4f}/{v['PASS_nur_aelter_5MDE']:.4f}, "
        f"halber Effekt juengst {v['PASS_juengster_halber_effekt_1MDE']:.4f}" for k, v in stab.items()))

    # Monte-Carlo-Gegenprobe (1.000.000 Pfade je r, Seed 31001)
    rng = np.random.default_rng(31001)
    mc = {}
    n = 1_000_000
    for r in (0.5, 1 / 3, 0.25):
        zr = rng.standard_normal(n)
        zo = rng.standard_normal(n)
        cell = out[{0.5: "r1_2", 1 / 3: "r1_3", 0.25: "r1_4"}[r]]
        ms = cell["mu_star_P2a"]
        res = {}
        for f in (0.0, 1.0):
            mr, mo = f * ms * math.sqrt(r), f * ms * math.sqrt(1 - r)
            Zr, Zo = zr + mr, zo + mo
            Zp = math.sqrt(r) * Zr + math.sqrt(1 - r) * Zo
            p2a = np.mean((Zp > Z9975) & (Zr > Z95))
            d52 = np.mean((Zp >= 2.5287) & (Zr >= 0.5 * 2.5287 * math.sqrt(r)) & (Zo >= 0.5 * 2.5287 * math.sqrt(1 - r)))
            c10 = np.mean((Zr > Z95) & (Zo > Z95))
            res[str(f)] = {"P2a": p2a, "DEC52": d52, "C10artig": c10}
        mc[f"{r:.3f}"] = res
    put("a.monte_carlo_1e6", mc)
    P("MC-Gegenprobe (1e6, Seed 31001):", {k: {f: {kk: round(float(vv), 5) for kk, vv in v.items()} for f, v in d.items()} for k, d in mc.items()})
    P(f"[Zeit (a): {time.process_time() - t0:.1f} s CPU]")
    return out


# =====================================================================================
# (b) GSD O'Brien-Fleming, 4 Blicke, alpha 0,0025 einseitig, Power 0,80
# =====================================================================================
def oc_grid(C, theta, K=4, fut=False, h=0.002):
    """Exakte Dichte-Propagation auf der B-Skala (B(t) = W(t) + theta t); Wirksamkeit B >= C (OBF),
    Futility (nicht bindend kalibriert) B < 0 an den Blicken 1..K-1. Liefert (P(PASS), E[t_stop])."""
    dt = 1.0 / K
    sd = math.sqrt(dt)
    lo, hi = -10.0, 10.0 + max(theta, 0.0)
    grid = np.arange(lo, hi + h / 2, h)
    m = int(round(8 * sd / h))
    offs = np.arange(-m, m + 1) * h
    kern = norm.pdf(offs, theta * dt, sd) * h
    dens = None
    prej = 0.0
    Et = 0.0
    for i in range(K):
        d = norm.pdf(grid, theta * dt, sd) if i == 0 else np.convolve(dens, kern, mode="same")
        rej = grid >= C
        futm = (grid < 0.0) if (fut and i < K - 1) else np.zeros_like(rej)
        prej += d[rej].sum() * h
        if i < K - 1:
            Et += (i + 1) * dt * d[rej | futm].sum() * h
            dens = np.where(~rej & ~futm, d, 0.0)
        else:
            Et += 1.0 * d.sum() * h
    return prej, Et


def grid_design(alpha, fut=False):
    lo, hi = 1.0, 4.5
    for _ in range(55):
        c = 0.5 * (lo + hi)
        a, _ = oc_grid(c, 0.0)
        lo, hi = (c, hi) if a > alpha else (lo, c)
    c = 0.5 * (lo + hi)
    th_fix = Z(1 - alpha) + Z80
    lo, hi = th_fix * 0.9, th_fix * 1.6
    for _ in range(50):
        th = 0.5 * (lo + hi)
        pw, _ = oc_grid(c, th, fut=fut)
        lo, hi = (th, hi) if pw < 0.8 else (lo, th)
    th = 0.5 * (lo + hi)
    R = (th / th_fix) ** 2
    _, e1 = oc_grid(c, th, fut=fut)
    a0, e0 = oc_grid(c, 0.0, fut=fut)
    _, eh = oc_grid(c, 0.5 * th, fut=fut)
    return {"c": c, "alpha_eff": a0, "R_max": R, "EN_H1": R * e1, "EN_H0": R * e0, "EN_halbMDE": R * eh, "theta": th}


class GSDMC:
    """Monte Carlo der Brownschen Bewegung auf 12 Teilschritten (Blicke bei 3/12, 6/12, 9/12, 12/12)."""

    def __init__(self, n, seed):
        rng = np.random.default_rng(seed)
        self.W = np.cumsum(rng.standard_normal((n, 12)) * math.sqrt(1.0 / 12), axis=1)
        self.W = np.concatenate([np.zeros((n, 1)), self.W], axis=1)   # Index j = t*12, j = 0..12
        self.n = n

    def run(self, theta, C, screen="none", r=None, fut=False, t_eff_end=None):
        """screen: 'none' | 'all' (jeder Wirksamkeits-Stopp braucht Z_rec > 1,645 auf den letzten r) | 'last'.
        t_eff_end: Drift nur bis zu dieser Info-Zeit (Effekt nur in aelteren Daten)."""
        js = np.arange(13)
        tt = js / 12.0
        drift = theta * (tt if t_eff_end is None else np.minimum(tt, t_eff_end))
        looks = [3, 6, 9, 12]
        B = {j: self.W[:, j] + drift[j] for j in set(looks + [j - int(round(r * 12)) for j in looks if r] + [0])
             if 0 <= j <= 12}
        n = self.n
        stop = np.zeros(n, dtype=bool)
        passed = np.zeros(n, dtype=bool)
        stale = np.zeros(n, dtype=bool)
        t_stop = np.ones(n)
        for k, j in enumerate(looks):
            tk = j / 12.0
            eff = B[j] >= C
            if screen == "all" or (screen == "last" and k == 3):
                jr = j - int(round(r * 12))
                if jr >= 0:
                    zrec = (B[j] - B[jr]) / math.sqrt(r)
                else:
                    zrec = B[j] / math.sqrt(tk)
                eff = eff & (zrec > Z95)
            if k < 3:
                fu = (B[j] < 0.0) if fut else np.zeros(n, dtype=bool)
                new_pass = ~stop & eff
                new_stop = ~stop & (eff | fu)
            else:
                new_pass = ~stop & eff
                new_stop = ~stop
            passed |= new_pass
            if t_eff_end is not None and r is not None and tk - r >= t_eff_end - 1e-9:
                stale |= new_pass       # PASS an einem Blick, dessen juengstes Fenster ganz effektfrei ist
            t_stop[new_stop] = tk
            stop |= new_stop
        if t_eff_end is not None:
            self.last_stale = float(stale.mean())
        return float(passed.mean()), float(t_stop.mean())

    def design(self, C, screen="none", r=None, fut=False):
        lo, hi = 0.9, 3.0
        for _ in range(42):
            R = 0.5 * (lo + hi)
            pw, _ = self.run(MU_FIX * math.sqrt(R), C, screen, r, fut)
            lo, hi = (R, hi) if pw < 0.8 else (lo, R)
        R = 0.5 * (lo + hi)
        th = MU_FIX * math.sqrt(R)
        pw1, e1 = self.run(th, C, screen, r, fut)
        a0, e0 = self.run(0.0, C, screen, r, fut)
        ph, eh = self.run(0.5 * th, C, screen, r, fut)
        p15, e15 = self.run(1.5 * th, C, screen, r, fut)
        out = {"R_max": R, "power_H1": pw1, "alpha_eff": a0, "EN_H1": R * e1, "EN_H0": R * e0,
               "power_halbMDE": ph, "EN_halbMDE": R * eh, "power_1_5MDE": p15, "EN_1_5MDE": R * e15}
        if r is not None:
            for t0 in (1.0 - r, 0.5):
                for fm in (1.0, 2.0):
                    pr, _ = self.run(fm * th, C, screen, r, fut, t_eff_end=t0)
                    out[f"effekt_bis_t{t0:.3f}_{fm:.0f}MDE"] = {"P_PASS": pr, "P_PASS_veraltet": self.last_stale}
        return out


def sec_b(a_out):
    P("\n================ (b) GSD O'Brien-Fleming, 4 Blicke ================")
    t0 = time.process_time()
    grid = {}
    for alpha in (0.05, 0.0025):
        for fut in (False, True):
            g = grid_design(alpha, fut)
            grid[f"alpha{alpha}_{'fut' if fut else 'nofut'}"] = g
            P(f"Gitter alpha {alpha} {'Futility Z<0 Blicke 1-3' if fut else 'ohne Futility'}: c {g['c']:.4f}, alpha {g['alpha_eff']:.5f}, "
              f"Max/fix {g['R_max']:.4f}, E[N|H1] {g['EN_H1']:.4f}, E[N|H0] {g['EN_H0']:.4f}, E[N|0,5 MDE] {g['EN_halbMDE']:.4f}")
    put("b.gitter", grid)
    C = grid["alpha0.0025_nofut"]["c"]
    mc = GSDMC(1_000_000, 31002)
    res = {}
    for fut in (False, True):
        d = mc.design(C, "none", None, fut)
        res[f"ohne_screen_{'fut' if fut else 'nofut'}"] = d
        th = MU_FIX * math.sqrt(d["R_max"])
        for t0 in (0.5, 0.75):
            pr, _ = mc.run(th, C, "none", 0.5 if t0 == 0.5 else 0.25, fut, t_eff_end=t0)
            d[f"effekt_bis_t{t0:.3f}_1MDE"] = {"P_PASS": pr, "P_PASS_veraltet_r": mc.last_stale}
        P(f"MC 1e6 OBF ohne Screen {'mit' if fut else 'ohne'} Futility: Max/fix {d['R_max']:.4f}, Power {d['power_H1']:.4f}, "
          f"alpha {d['alpha_eff']:.5f}, E[N|H1] {d['EN_H1']:.4f}, E[N|H0] {d['EN_H0']:.4f}; Effekt nur bis t0 0,5 (r 1/2) / 0,75 (r 1/4): "
          f"P(PASS) {d['effekt_bis_t0.500_1MDE']['P_PASS']:.4f} / {d['effekt_bis_t0.750_1MDE']['P_PASS']:.4f}, veraltet "
          f"{d['effekt_bis_t0.500_1MDE']['P_PASS_veraltet_r']:.4f} / {d['effekt_bis_t0.750_1MDE']['P_PASS_veraltet_r']:.4f}")
    for r in (0.5, 1 / 3, 0.25):
        for scr in ("all", "last"):
            for fut in (False, True):
                d = mc.design(C, scr, r, fut)
                key = f"screen_{scr}_r{r:.3f}_{'fut' if fut else 'nofut'}"
                res[key] = d
                P(f"MC GSD+REZENZ-Screen ({'jeder Stopp' if scr == 'all' else 'nur letzter Blick'}), r {r:.3f}, "
                  f"{'Futility' if fut else 'ohne Fut.'}: Max/fix {d['R_max']:.4f}, alpha {d['alpha_eff']:.5f}, "
                  f"E[N|H1] {d['EN_H1']:.4f}, E[N|H0] {d['EN_H0']:.4f}, E[N|0,5MDE] {d['EN_halbMDE']:.4f} (Power {d['power_halbMDE']:.3f}); "
                  "Effekt nur bis t0 [P(PASS), davon veraltet]: " + "; ".join(
                      f"{kk.replace('effekt_bis_', '')}: {vv['P_PASS']:.4f}/{vv['P_PASS_veraltet']:.4f}"
                      for kk, vv in d.items() if kk.startswith("effekt_bis_")))
    put("b.monte_carlo_1e6", res)
    # Umrechnung in Einheiten: N_fix(gepoolt 0,0025) und gegen C.10
    conv = {"N_fix_gepoolt0025_in_C10je080": MU_FIX ** 2 / (2 * C80_05 ** 2),
            "N_fix_gepoolt0025_in_N005": MU_FIX ** 2 / C80_05 ** 2,
            "C10_je080_in_N005": 2.0, "C10_gem080_in_N005": 2 * (Z95 + Z(math.sqrt(0.8))) ** 2 / C80_05 ** 2}
    for k, v in (("GSD_ohne_screen", grid["alpha0.0025_nofut"]["EN_H1"]),
                 ("GSD_screen_all_r0.5", res["screen_all_r0.500_nofut"]["EN_H1"]),
                 ("GSD_screen_all_r0.333", res["screen_all_r0.333_nofut"]["EN_H1"])):
        conv[f"{k}_EN_H1_in_N005"] = v * MU_FIX ** 2 / C80_05 ** 2
        conv[f"{k}_EN_H1_vs_C10gem080"] = v * MU_FIX ** 2 / (2 * (Z95 + Z(math.sqrt(0.8))) ** 2)
        conv[f"{k}_EN_H1_vs_C10je080"] = v * MU_FIX ** 2 / (2 * C80_05 ** 2)
    put("b.umrechnung", conv)
    P("Umrechnung (N_0,05-Einheiten; Ersparnis gegen C.10):", {k: round(v, 4) for k, v in conv.items()})
    P(f"[Zeit (b): {time.process_time() - t0:.1f} s CPU]")
    return grid, res


# =====================================================================================
# (c) Selektion in Zone X: Winner's Curse, Basisrate, Power-Ueberschaetzung, alpha
# =====================================================================================
def med_unbiased(x, M):
    """Bedingt median-unverzerrter Schaetzer der ausgewaehlten Variante (Truncated-Normal-Inversion):
    theta_hat loest  [1 - Phi(x - theta)] / [1 - Phi(M - theta)] = 1/2  (x = Gewinner, M = Maximum der anderen)."""
    g = lambda th: special.log_ndtr(th - x) - special.log_ndtr(th - M) - math.log(0.5)
    gap = np.maximum(x - M, 1e-9)
    lo = np.minimum(x, 0.5 * (x + M) - 1.0 / gap) - 12.0
    hi = x.copy()
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        v = g(mid)
        up = v > 0          # Verhaeltnis > 1/2 -> theta kleiner
        hi = np.where(up, mid, hi)
        lo = np.where(up, lo, mid)
    return 0.5 * (lo + hi)


def sec_c(a_out):
    P("\n================ (c) Selektion in Zone X ================")
    t0 = time.process_time()
    r = 0.5
    mu_star = a_out["r1_2"]["mu_star_P2a"]
    a_eff = a_out["r1_2"]["alpha_eff_P2a"]
    mus = np.arange(-3.0, 25.0, 0.01)
    pw_grid = np.array([p2a_power(m, r) for m in mus])
    powf = lambda m: np.interp(m, mus, pw_grid, left=0.0, right=1.0)
    put("c.planung", {"regel": "P-2(a) r=1/2", "mu_star": mu_star, "alpha_eff": a_eff})
    n = 200_000
    out = {}
    keep = {}
    P(f"Planung: Konfirmation mit P-2(a), r 1/2 (mu* {mu_star:.4f}); Info so, dass Power 0,80 bei d_plan; X-SE = 1.")
    P(f"{'K':>3} {'pi':>5} {'d':>3} | {'pi_K':>6} {'E[x_sel]':>8} {'E[th_sel]':>9} {'E[x|echt]':>9} {'P(med<=th)':>10} | "
      f"G0 roh: reg/pi_K/Power_echt/Pass | G0 ber.: reg/pi_K/Power_echt/Pass | G1 (x>1,645) roh: reg/pi_K/Power_echt | ber.: Power_echt | alpha|null")
    seed = 31003
    for K in (4, 10, 25):
        for pi in (0.0, 0.1, 0.25, 0.5):
            for delta in (1.0, 2.0, 3.0):
                if pi == 0.0 and delta > 1.0:
                    continue   # pi = 0: delta wirkungslos (eine Zelle je K)
                rng = np.random.default_rng(seed)
                seed += 1
                real = rng.random((n, K)) < pi
                th = np.where(real, delta, 0.0)
                x = th + rng.standard_normal((n, K))
                ar = np.arange(n)
                sel = np.argmax(x, axis=1)
                xs = x[ar, sel]
                ths = th[ar, sel]
                rs = real[ar, sel]
                xo = x.copy()
                xo[ar, sel] = -np.inf
                M = xo.max(axis=1)
                tm = med_unbiased(xs, M)
                cell = {"pi_K_basisrate": rs.mean(), "E_x_sel": xs.mean(), "E_theta_sel": ths.mean(),
                        "bias_roh": (xs - ths).mean(), "P_med_le_theta": np.mean(tm <= ths),
                        "median_med_minus_theta": np.median(tm - ths), "E_med_minus_theta": np.mean(tm - ths)}
                if rs.any():
                    cell["E_x_sel_gegeben_echt"] = xs[rs].mean()
                    cell["ratio_E_x_echt_zu_delta"] = xs[rs].mean() / delta
                    cell["E_med_gegeben_echt"] = tm[rs].mean()
                    cell["median_med_gegeben_echt"] = np.median(tm[rs])
                # Planung und realisierte Power
                for gate, gname in ((0.0, "G0"), (Z95, "G1")):
                    for plan, d_plan in (("roh", xs), ("bereinigt", tm)):
                        reg = (xs > gate) & (d_plan > 0)
                        mu_real = np.where(reg & rs, mu_star * ths / np.where(reg, d_plan, 1.0), 0.0)
                        any_rr = bool((reg & rs).any())
                        pw_real = powf(mu_real[reg & rs]) if any_rr else np.zeros(0)
                        n_reg = reg.sum()
                        pass_exp = pw_real.sum() + a_eff * (reg & ~rs).sum()
                        sub = {"anteil_registriert": reg.mean(),
                               "pi_K_unter_registrierten": (rs & reg).sum() / max(n_reg, 1),
                               "power_echt_mittel": float(pw_real.mean()) if any_rr else None,
                               "power_echt_median": float(np.median(pw_real)) if any_rr else None,
                               "anteil_echt_power_unter_050": float(np.mean(pw_real < 0.5)) if any_rr else None,
                               "P_PASS_je_registrierung": pass_exp / max(n_reg, 1),
                               "PPV": pw_real.sum() / max(pass_exp, 1e-300),
                               "info_relativ_zum_orakel_median_echt": float(np.median((mu_real[reg & rs] / mu_star) ** 2)) if any_rr else None}
                        cell[f"{gname}_{plan}"] = sub
                        if gname == "G0" and plan == "roh":
                            keep[(K, pi, delta)] = (rs.mean(), mu_real[reg & rs].copy(), reg.mean())
                # (iv) alpha: ausgewaehlte Null-Varianten, Konfirmation auf disjunkten Daten
                nul = ~rs
                if nul.any():
                    zr = rng.standard_normal(nul.sum())
                    zo = rng.standard_normal(nul.sum())
                    zp = math.sqrt(r) * zr + math.sqrt(1 - r) * zo
                    cell["alpha_konfirmation_null_gewaehlt_MC"] = np.mean((zp > Z9975) & (zr > Z95))
                    cell["alpha_wiederverwendung_X_daten"] = np.mean(xs[nul] > Z9975)
                    cell["n_null_gewaehlt"] = int(nul.sum())
                out[f"K{K}_pi{pi}_d{delta}"] = cell
                g0r, g0b, g1r, g1b = cell["G0_roh"], cell["G0_bereinigt"], cell["G1_roh"], cell["G1_bereinigt"]
                nz = lambda v: float("nan") if v is None else v
                P(f"{K:3d} {pi:5.2f} {delta:3.0f} | {cell['pi_K_basisrate']:6.4f} {cell['E_x_sel']:8.4f} {cell['E_theta_sel']:9.4f} "
                  f"{cell.get('E_x_sel_gegeben_echt', float('nan')):9.4f} {cell['P_med_le_theta']:10.4f} | "
                  f"{g0r['anteil_registriert']:.3f}/{g0r['pi_K_unter_registrierten']:.4f}/{nz(g0r['power_echt_mittel']):.3f}/{g0r['P_PASS_je_registrierung']:.4f} | "
                  f"{g0b['anteil_registriert']:.3f}/{g0b['pi_K_unter_registrierten']:.4f}/{nz(g0b['power_echt_mittel']):.3f}/{g0b['P_PASS_je_registrierung']:.4f} | "
                  f"{g1r['anteil_registriert']:.3f}/{g1r['pi_K_unter_registrierten']:.4f}/{nz(g1r['power_echt_mittel']):.3f} | {nz(g1b['power_echt_mittel']):.3f} | "
                  f"{cell.get('alpha_konfirmation_null_gewaehlt_MC', float('nan')):.5f} (n {cell.get('n_null_gewaehlt', 0)}; X-Wiederverw. {cell.get('alpha_wiederverwendung_X_daten', float('nan')):.4f}); "
                  f"Info/Orakel med. roh {nz(g0r['info_relativ_zum_orakel_median_echt']):.3f} ber. {nz(g0b['info_relativ_zum_orakel_median_echt']):.3f}; P(Power<0,5) roh {nz(g0r['anteil_echt_power_unter_050']):.3f}")
    put("c.zellen", out)
    analyt = {f"K{K}": 1 - (1 - 0.0025) ** K for K in (4, 10, 25)}
    put("c.alpha_wiederverwendung_analytisch", analyt)
    P("alpha bei Wiederverwendung der X-Daten (alle Null, analytisch 1-(1-0,0025)^K):", {k: round(v, 5) for k, v in analyt.items()},
      "; Konfirmation auf disjunkten Daten: alpha_eff P-2(a) r 1/2 =", round(a_eff, 6))
    P(f"[Zeit (c): {time.process_time() - t0:.1f} s CPU]")
    return out, keep, powf


# =====================================================================================
# (d) Programmebene je Jahr
# =====================================================================================
def by_reject(p, q=0.10):
    m = p.shape[1]
    cm = np.sum(1.0 / np.arange(1, m + 1))
    ps = np.sort(p, axis=1)
    thr = np.arange(1, m + 1) * q / (m * cm)
    ok = ps <= thr
    kmax = np.where(ok.any(axis=1), m - np.argmax(ok[:, ::-1], axis=1), 0)
    cut = np.where(kmax > 0, ps[np.arange(p.shape[0]), np.maximum(kmax - 1, 0)], -1.0)
    return p <= cut[:, None], cm


def sec_d(a_out, keep):
    P("\n================ (d) Programmebene je Jahr ================")
    t0 = time.process_time()
    r = 0.5
    rho = math.sqrt(r)
    mu_star = a_out["r1_2"]["mu_star_P2a"]
    n = 200_000
    out = {}
    scen = [("fest_0.05", 0.05, None), ("fest_0.10", 0.10, None), ("fest_0.25", 0.25, None)]
    for kk in ((4, 0.1, 2.0), (10, 0.1, 2.0), (25, 0.1, 2.0), (10, 0.25, 2.0), (10, 0.1, 1.0), (10, 0.1, 3.0), (10, 0.5, 2.0)):
        piK, mus, _ = keep[kk]
        scen.append((f"aus_c_K{kk[0]}_pi{kk[1]}_d{kk[2]}", float(piK), mus))
    bythr = {}
    for m in (4, 8, 12, 13, 20):
        cm = float(np.sum(1.0 / np.arange(1, m + 1)))
        bythr[str(m)] = {"c_m": cm, "kleinste_BY_schwelle": 0.10 / (m * cm)}
    put("d.BY_schwellen", bythr)
    P("BY q 0,10: kleinste Schwelle q/(m c_m):", {k: round(v["kleinste_BY_schwelle"], 5) for k, v in bythr.items()},
      "-> bei festem alpha 0,0025 ist BY fuer m <= 12 nie bindend")
    seed = 31004
    P(f"{'Szenario':>26} {'m':>3} {'pi_K':>6} | fest 0,0025: E[V] E[S] PPV FDR P(V>=1) | BY allein: E[V] E[S] FDR | BY+fest: E[V] E[S] FDR")
    for name, piK, mus in scen:
        for m in (4, 8, 12):
            rng = np.random.default_rng(seed)
            seed += 1
            true = rng.random((n, m)) < piK
            if mus is None:
                mu = np.where(true, mu_star, 0.0)
            else:
                draw = mus[rng.integers(0, mus.size, size=(n, m))] if mus.size else np.zeros((n, m))
                mu = np.where(true, draw, 0.0)
            zr = rng.standard_normal((n, m)) + mu * rho
            zo = rng.standard_normal((n, m)) + mu * math.sqrt(1 - r)
            zp = rho * zr + math.sqrt(1 - r) * zo
            scr = zr > Z95
            p = norm.sf(zp)
            fixed = (zp > Z9975) & scr
            byr, _ = by_reject(p)
            by_only = byr & scr
            by_fix = byr & fixed
            cell = {}
            for lab, rej in (("fest", fixed), ("BY_allein", by_only), ("BY_plus_fest", by_fix)):
                V = (rej & ~true).sum(axis=1)
                S = (rej & true).sum(axis=1)
                Rr = V + S
                cell[lab] = {"E_V": V.mean(), "E_S": S.mean(), "PPV": S.sum() / max(Rr.sum(), 1),
                             "FDR": np.mean(V / np.maximum(Rr, 1)), "P_V_ge1": np.mean(V >= 1), "E_R": Rr.mean()}
            cell["identisch_BY_plus_fest_und_fest"] = bool(np.array_equal(fixed, by_fix))
            cell["pi_K"] = piK
            out[f"{name}_m{m}"] = cell
            f_, b_, bf = cell["fest"], cell["BY_allein"], cell["BY_plus_fest"]
            P(f"{name:>26} {m:3d} {piK:6.4f} | {f_['E_V']:.4f} {f_['E_S']:.3f} {f_['PPV']:.4f} {f_['FDR']:.4f} {f_['P_V_ge1']:.4f} | "
              f"{b_['E_V']:.4f} {b_['E_S']:.3f} {b_['FDR']:.4f} | {bf['E_V']:.4f} {bf['E_S']:.3f} {bf['FDR']:.4f} (ident. {cell['identisch_BY_plus_fest_und_fest']})")
    put("d.zellen", out)
    # analytische PPV-Tabelle (Normalnaeherung) heute / 3.1
    ppv = {}
    a31 = a_out["r1_2"]["alpha_eff_P2a"]
    for lab, a, pw in (("C10_heute_je080", 0.0025, 0.64), ("P2a_r1_2_power080", a31, 0.80), ("gepoolt0025_power080", 0.0025, 0.80),
                       ("gepoolt001_power080", 0.01, 0.80), ("ein_fenster005", 0.05, 0.80)):
        ppv[lab] = {str(b): pw * b / (pw * b + a * (1 - b)) for b in (0.05, 0.10, 0.25)}
        ppv[lab]["falsch_PASS_je_Nulltest"] = a
    put("d.ppv_analytisch", ppv)
    P("PPV analytisch (Basisrate 0,05/0,10/0,25):", {k: [round(v[s], 4) for s in ("0.05", "0.1", "0.25")] for k, v in ppv.items()})
    P(f"[Zeit (d): {time.process_time() - t0:.1f} s CPU]")
    return out


# =====================================================================================
# (e) Schwere Raender und kleine Clusterzahlen
# =====================================================================================
FS_GAMMA = 1.5


def fs_moments(nu, g):
    e_abs = 2 * math.sqrt(nu) * math.gamma((nu + 1) / 2) / (math.sqrt(math.pi) * (nu - 1) * math.gamma(nu / 2))
    mean = e_abs * (g ** 3 - 1 / g) / (1 + g ** 2)
    ex2 = (nu / (nu - 2)) * (g ** 4 + 1 / g ** 2) / (1 + g ** 2)
    return mean, math.sqrt(ex2 - mean ** 2)


def draw(rng, dist, shape):
    if dist == "normal":
        return rng.standard_normal(shape)
    if dist.startswith("t"):
        nu = float(dist[1:])
        return rng.standard_t(nu, shape) / math.sqrt(nu / (nu - 2))
    if dist.startswith("skewt4"):
        nu, g = 4.0, (FS_GAMMA if dist == "skewt4" else float(dist[len("skewt4g"):]))
        t = np.abs(rng.standard_t(nu, shape))
        pos = rng.random(shape) < g ** 2 / (1 + g ** 2)
        x = np.where(pos, g * t, -t / g)
        mu, sd = fs_moments(nu, g)
        return (x - mu) / sd
    raise ValueError(dist)


def fs_skewness(nu, g):
    def eabs(k):
        return nu ** (k / 2) * math.gamma((k + 1) / 2) * math.gamma((nu - k) / 2) / (math.sqrt(math.pi) * math.gamma(nu / 2))
    def mom(k):
        return eabs(k) * (g ** (k + 2) + (-1) ** k * g ** (-k)) / (1 + g ** 2)
    m1, m2, m3 = mom(1), mom(2), mom(3)
    var = m2 - m1 ** 2
    return (m3 - 3 * m1 * m2 + 2 * m1 ** 3) / var ** 1.5


def sb_weights(n, mean_block=4.0):
    q = 1.0 - 1.0 / mean_block
    k = np.arange(1, n)
    return 2.0 * (1.0 - k / n) * q ** k


def se_rules(x, mean_block=4.0):
    """naive SE (ddof 1) und SE nach DEC-94 (4): max(naiv, ideale stationaere Bootstrap-SE, B -> inf)."""
    n = x.shape[1]
    xb = x.mean(axis=1)
    d = x - xb[:, None]
    s = np.sqrt((d * d).sum(axis=1) / (n - 1))
    F = np.fft.rfft(d, axis=1)
    cc = np.fft.irfft(F * np.conj(F), n=n, axis=1) / n      # zirkulaere Autokovarianz
    var_sb = cc[:, 0] + cc[:, 1:] @ sb_weights(n, mean_block)
    se_naive = s / math.sqrt(n)
    se_sb = np.sqrt(np.maximum(var_sb, 0.0) / n)
    return xb, se_naive, np.maximum(se_naive, se_sb), se_sb


def sb_check():
    """Gegenprobe: ideale SB-Varianz (Formel) gegen die power_p1-Konvention (geometrische Bloecke, zirkulaer)."""
    rng = np.random.default_rng(31010)
    out = []
    for n, phi in ((52, 0.0), (104, 0.3)):
        e = rng.standard_normal(n)
        x = np.empty(n)
        x[0] = e[0]
        for i in range(1, n):
            x[i] = phi * x[i - 1] + e[i]
        _, _, _, se_f = se_rules(x[None, :])
        p = 1 / 4.0
        t = np.arange(n)
        reps = 100_000
        means = np.empty(reps)
        for rr in range(reps):
            starts = rng.integers(0, n, size=n)
            jump = rng.random(n) < p
            jump[0] = True
            first = np.maximum.accumulate(np.where(jump, t, 0))
            idx = (starts[first] + (t - first)) % n
            means[rr] = x[idx].mean()
        out.append({"n": n, "phi": phi, "se_formel": float(se_f[0]), "se_bootstrap_1e5": float(np.std(means, ddof=1))})
    return out


def sec_e():
    P("\n================ (e) Schwere Raender und kleine Clusterzahlen ================")
    t0 = time.process_time()
    chk = sb_check()
    put("e.sb_formel_gegenprobe", chk)
    P("Gegenprobe ideale SB-SE (Formel) gegen SB-Simulation (power_p1-Konvention, 1e5 Replikate):", chk)
    exk = {"t5": 6.0, "t4": "unendlich", "t3": "unendlich (4. Moment existiert nicht)", "normal": 0.0}
    put("e.exzess_kurtosis_hinweis", exk)
    sk = {"skewt4_gamma1.5": fs_skewness(4.0, 1.5), "skewt4_gamma1.2": fs_skewness(4.0, 1.2)}
    put("e.schiefe_fs_t4", sk)
    P("Schiefe der standardisierten Fernandez-Steel-t4 (gamma 1,5 / 1,2):", {k: round(v, 4) for k, v in sk.items()})
    n_paths = 200_000
    out = {}
    seed = 31005
    dists = ("normal", "t5", "t4", "t3", "skewt4", "skewt4g1.2")
    P(f"{'Vert.':>7} {'n':>4} | wahres alpha nominal 0,0025: z-naiv  t-krit  SB-max(z) | nominal 0,05: z-naiv t-krit SB-max | "
      f"Power bei Normal-MDE80 (0,0025): Normalnaeh. 0,80 -> z-naiv t-krit SB-max | 0,05: z t SB | untere Flanke 0,0025 SB")
    for dist in dists:
        for n in (40, 52, 104):
            rng = np.random.default_rng(seed)
            seed += 1
            cell = {}
            for lab, shift in (("H0", 0.0), ("H1_0025", MU_FIX / math.sqrt(n)), ("H1_005", C80_05 / math.sqrt(n))):
                acc = {}
                chunks = []
                for c0 in range(0, n_paths, 50_000):
                    x = draw(rng, dist, (50_000, n)) + shift
                    xb, sn, sm, _ = se_rules(x)
                    chunks.append((xb / sn, xb / sm))
                tn = np.concatenate([c[0] for c in chunks])
                tm = np.concatenate([c[1] for c in chunks])
                for a in (0.0025, 0.05):
                    za = Z(1 - a)
                    ta = stats.t.ppf(1 - a, n - 1)
                    acc[str(a)] = {"z_naiv": np.mean(tn > za), "t_krit": np.mean(tn > ta), "SB_max_z": np.mean(tm > za),
                                   "SB_max_t": np.mean(tm > ta)}
                    if lab == "H0":
                        acc[str(a)]["untere_flanke_SB_max_z"] = np.mean(tm < -za)
                        acc[str(a)]["untere_flanke_z_naiv"] = np.mean(tn < -za)
                cell[lab] = acc
            out[f"{dist}_n{n}"] = cell
            h0, h1, h5 = cell["H0"], cell["H1_0025"], cell["H1_005"]
            P(f"{dist:>10} {n:4d} | {h0['0.0025']['z_naiv']:.5f} {h0['0.0025']['t_krit']:.5f} {h0['0.0025']['SB_max_z']:.5f} | "
              f"{h0['0.05']['z_naiv']:.4f} {h0['0.05']['t_krit']:.4f} {h0['0.05']['SB_max_z']:.4f} | "
              f"{h1['0.0025']['z_naiv']:.4f} {h1['0.0025']['t_krit']:.4f} {h1['0.0025']['SB_max_z']:.4f} | "
              f"{h5['0.05']['z_naiv']:.4f} {h5['0.05']['t_krit']:.4f} {h5['0.05']['SB_max_z']:.4f} | "
              f"{h0['0.0025']['untere_flanke_SB_max_z']:.5f}")
    put("e.einzeltest", out)

    # Abhaengigkeit: AR(1) phi 0,3 (Normal und t4), SB-Regel gegen naiv
    from scipy.signal import lfilter
    dep = {}
    for dist in ("normal", "t4"):
        for n in (52, 104):
            rng = np.random.default_rng(seed)
            seed += 1
            phi = 0.3
            e = draw(rng, dist, (n_paths, n + 50))
            x = lfilter([1.0], [1.0, -phi], e, axis=1)[:, 50:]
            xb, sn, sm, _ = se_rules(x)
            dep[f"{dist}_n{n}"] = {str(a): {"z_naiv": np.mean(xb / sn > Z(1 - a)), "SB_max_z": np.mean(xb / sm > Z(1 - a))}
                                   for a in (0.0025, 0.05)}
            dep[f"{dist}_n{n}"]["c_wahr"] = (1 + phi) / (1 - phi)
    put("e.ar1_phi0_3", dep)
    P("AR(1) phi 0,3 (c wahr 1,857): wahres alpha naiv / SB-max:", {k: {a: (round(float(v[a]['z_naiv']), 5), round(float(v[a]['SB_max_z']), 5)) for a in ('0.0025', '0.05')} for k, v in dep.items()})

    # GSD mit geschaetzter Varianz: z-Grenzen gegen t-artige Grenzen
    C = 2.832136   # OBF B-Skala, alpha 0,0025 (Gitter, Abschnitt b)
    gsd = {}
    P("GSD mit geschaetzter Varianz (OBF c 2,8321, 4 Blicke, nominal 0,0025): alpha_eff [z-Grenzen naiv | t-Grenzen naiv | z-Grenzen SB-max | t-Grenzen SB-max]; Power bei Design-Drift")
    for dist in ("normal", "t4", "t3"):
        for n in (40, 52, 104):
            rng = np.random.default_rng(seed)
            seed += 1
            nks = [int(round(n * k / 4)) for k in (1, 2, 3, 4)]
            tks = [nk / n for nk in nks]
            bz = [C / math.sqrt(t) for t in tks]
            bt = [float(stats.t.ppf(norm.cdf(b), nk - 1)) for b, nk in zip(bz, nks)]
            cell = {"n_je_blick": nks, "z_grenzen": bz, "t_grenzen": bt}
            for lab, shift in (("H0", 0.0), ("H1", MU_FIX * math.sqrt(1.0074) / math.sqrt(n))):
                cnt = {"z_naiv": 0, "t_naiv": 0, "z_sb": 0, "t_sb": 0}
                for c0 in range(0, n_paths, 50_000):
                    x = draw(rng, dist, (50_000, n)) + shift
                    cz = np.zeros(50_000, bool); ct = cz.copy(); czs = cz.copy(); cts = cz.copy()
                    for nk, b1, b2 in zip(nks, bz, bt):
                        xb, sn, sm, _ = se_rules(x[:, :nk])
                        cz |= xb / sn >= b1
                        ct |= xb / sn >= b2
                        czs |= xb / sm >= b1
                        cts |= xb / sm >= b2
                    cnt["z_naiv"] += cz.sum(); cnt["t_naiv"] += ct.sum(); cnt["z_sb"] += czs.sum(); cnt["t_sb"] += cts.sum()
                cell[lab] = {k: v / n_paths for k, v in cnt.items()}
            gsd[f"{dist}_n{n}"] = cell
            P(f"  {dist:>6} n {n:3d} (Blicke {nks}): H0 {cell['H0']['z_naiv']:.5f} | {cell['H0']['t_naiv']:.5f} | {cell['H0']['z_sb']:.5f} | "
              f"{cell['H0']['t_sb']:.5f}; Power {cell['H1']['z_naiv']:.4f} | {cell['H1']['t_naiv']:.4f} | {cell['H1']['z_sb']:.4f} | {cell['H1']['t_sb']:.4f}; "
              f"t-Grenzen {[round(v, 3) for v in bt]}")
    put("e.gsd_geschaetzte_varianz", gsd)
    P(f"[Zeit (e): {time.process_time() - t0:.1f} s CPU]")
    return out, gsd


# =====================================================================================
# (f) Ueberlappung: 1-3-Tages-Horizont mit taeglichem Schritt
# =====================================================================================
def nw_c(d, L):
    n = d.shape[1]
    g0 = (d * d).sum(axis=1) / n
    lrv = g0.copy()
    for k in range(1, L + 1):
        lrv += 2.0 * (1.0 - k / (L + 1.0)) * (d[:, k:] * d[:, :-k]).sum(axis=1) / n
    return lrv / g0


def sec_f():
    P("\n================ (f) Ueberlappung ================")
    t0 = time.process_time()
    N = 365
    ana = {}
    for h in (1, 2, 3):
        w = np.zeros(N + h - 1)
        for t in range(N):
            w[t:t + h] += 1
        c_ts_exact = float((w ** 2).sum() / (N * h))
        rho_ts = [(h - k) / h for k in range(1, h)]
        rho_x = [((h - k) / h) ** 2 for k in range(1, h)]
        c_x = 1 + 2 * sum((1 - k / N) * v for k, v in zip(range(1, h), rho_x))
        nw = {}
        for L in (h - 1, 4, 2 * h):
            nw[f"L{L}"] = {"TS": 1 + 2 * sum((1 - k / (L + 1)) * (rho_ts[k - 1] if k < h else 0.0) for k in range(1, L + 1)),
                           "XS_formation_h": 1 + 2 * sum((1 - k / (L + 1)) * (rho_x[k - 1] if k < h else 0.0) for k in range(1, L + 1))}
        ana[f"h{h}"] = {"c_TS_persistenter_praediktor_exakt_N365": c_ts_exact, "c_TS_grenz": float(h),
                        "c_XS_formation_gleich_h": c_x, "c_XS_iid_praediktor": 1.0, "NW_erwartung_ohne_schaetzfehler": nw}
    put("f.analytisch", ana)
    P("c analytisch (N 365): ", {k: (round(v['c_TS_persistenter_praediktor_exakt_N365'], 4), round(v['c_XS_formation_gleich_h'], 4),
                                    {L: (round(x['TS'], 4), round(x['XS_formation_h'], 4)) for L, x in v['NW_erwartung_ohne_schaetzfehler'].items()})
                                for k, v in ana.items()})
    mc = {}
    n_paths = 200_000
    seed = 31006
    for typ in ("TS", "XS"):
        for h in (2, 3):
            rng = np.random.default_rng(seed)
            seed += 1
            if typ == "TS":
                rho = np.array([1.0] + [(h - k) / h for k in range(1, h)])
            else:
                rho = np.array([1.0] + [((h - k) / h) ** 2 for k in range(1, h)])
            col = np.zeros(N)
            col[:h] = rho
            S = np.array([[col[abs(i - j)] for j in range(N)] for i in range(N)])
            Lc = np.linalg.cholesky(S)
            c_true = float(S.sum() / N)
            stats_acc = {"naiv": [], "NW_Lh-1": [], "NW_L4": [], "NW_L2h": [], "SB_max": [], "c_hat_Lh-1": [], "c_hat_L4": [], "c_hat_L2h": []}
            for c0 in range(0, n_paths, 25_000):
                y = rng.standard_normal((25_000, N)) @ Lc.T
                xb = y.mean(axis=1)
                d = y - xb[:, None]
                s = np.sqrt((d * d).sum(axis=1) / (N - 1))
                sn = s / math.sqrt(N)
                stats_acc["naiv"].append(xb / sn)
                for L, nm in ((h - 1, "Lh-1"), (4, "L4"), (2 * h, "L2h")):
                    c = nw_c(d, L)
                    stats_acc[f"c_hat_{nm}"].append(c)
                    stats_acc[f"NW_{nm}"].append(xb / (sn * np.sqrt(np.maximum(1.0, c))))
                _, _, sm, _ = se_rules(y)
                stats_acc["SB_max"].append(xb / sm)
            cat = {k: np.concatenate(v) for k, v in stats_acc.items()}
            cell = {"c_wahr": c_true}
            for k in ("naiv", "NW_Lh-1", "NW_L4", "NW_L2h", "SB_max"):
                cell[k] = {str(a): np.mean(cat[k] > Z(1 - a)) for a in (0.0025, 0.05)}
            for k in ("c_hat_Lh-1", "c_hat_L4", "c_hat_L2h"):
                cell[f"E_{k}"] = cat[k].mean()
            cell["oracle"] = {str(a): float(norm.sf(Z(1 - a))) for a in (0.0025, 0.05)}
            mc[f"{typ}_h{h}"] = cell
            P(f"MC {typ} h {h}: c wahr {c_true:.4f}; E[c_hat] L=h-1 {cell['E_c_hat_Lh-1']:.4f}, L=4 {cell['E_c_hat_L4']:.4f}, L=2h {cell['E_c_hat_L2h']:.4f}; "
              f"wahres alpha 0,0025/0,05: naiv {cell['naiv']['0.0025']:.5f}/{cell['naiv']['0.05']:.4f}, NW(h-1) {cell['NW_Lh-1']['0.0025']:.5f}/{cell['NW_Lh-1']['0.05']:.4f}, "
              f"NW(4) {cell['NW_L4']['0.0025']:.5f}/{cell['NW_L4']['0.05']:.4f}, NW(2h) {cell['NW_L2h']['0.0025']:.5f}/{cell['NW_L2h']['0.05']:.4f}, "
              f"SB-max {cell['SB_max']['0.0025']:.5f}/{cell['SB_max']['0.05']:.4f}")
    put("f.monte_carlo", mc)
    # F1-Beispiel: MDE80 je Fenster (365 Tage) aus der Akte x sqrt(c), Datenbedarf x c
    f1 = {}
    for K, mde in ((600, 0.0133), (500, 0.0146), (300, 0.0188)):
        f1[f"K{K}"] = {"MDE80_c1": mde}
        for h in (2, 3):
            for lab, c in (("TS_persistent", ana[f"h{h}"]["c_TS_persistenter_praediktor_exakt_N365"]),
                           ("XS_formation_h", ana[f"h{h}"]["c_XS_formation_gleich_h"])):
                f1[f"K{K}"][f"h{h}_{lab}"] = {"c": c, "MDE80": mde * math.sqrt(c), "datenfaktor": c}
    put("f.F1_beispiel", f1)
    P("F1 MDE80 je Fenster x sqrt(c):", {k: {kk: (round(vv['MDE80'], 4) if isinstance(vv, dict) else vv) for kk, vv in v.items()} for k, v in f1.items()})
    P(f"[Zeit (f): {time.process_time() - t0:.1f} s CPU]")
    return ana, mc


# =====================================================================================
# (g) Strenge-Quotient und A2 unter 3.1 (nur Akten-Zahlen)
# =====================================================================================
# Akten-Zahlen: NULL_SIMULATION_A2.md T2/T3/T4/T5, DEC-103 N1 (6)/(8)/(9), REVIEW_A2_TEILC B-4
A2 = {
    "W1": {"N": {"E": 52, "P2": 208, "P3fix": 248, "P3all": 260}, "kappa": 0.999,
           "zentral": {"SE": {"P2": 7.34, "P3fix": 7.93, "P3all": 6.56}, "nullSD": 6.70, "d95": 11.10, "zentrumSD": 0.23},
           "stress": {"SE": {"P2": 8.25, "P3fix": 8.66, "P3all": 7.39}, "nullSD": 7.53, "d95": 12.47, "zentrumSD": 0.26}},
    "W2": {"N": {"E": 52, "P2": 159, "P3fix": 247, "P3all": 259}, "kappa": 0.815,
           "zentral": {"SE": {"P2": 7.58, "P3fix": 7.93, "P3all": 6.56}, "nullSD": 6.24, "d95": 10.33, "zentrumSD": 2.97},
           "stress": {"SE": {"P2": 8.52, "P3fix": 8.67, "P3all": 7.39}, "nullSD": 7.01, "d95": 11.61, "zentrumSD": 3.34}},
    # Klassen-SD (disjunkte Klassen, T2) und c_bind: zentral = VP gepoolt, stress = V1
    "klassen": {"zentral": {"E": 43.83, "P2": 42.45, "P3fix": 61.39, "P3all": 8.53},
                "stress": {"E": 49.37, "P2": 47.45, "P3fix": 62.11, "P3all": 9.67}},
    "c_bind": {"E": 1.1491, "P2": 1.3177, "P3fix": 1.168, "P3all": 1.000},
    "tau95": 1.6553, "gate4": 0.9025,
}
COND = ("P2", "P3fix", "P3all")


def a2_cov(win, lin):
    """Kovarianz der drei Kontraste D_j = E - P_j in einem Fenster (Annahme Cov(P_i,P_j)=0;
    Cov(E,P_j) aus der Akten-SE, Var(E), Var(P_j) aus Klassen-SD und c_bind)."""
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
    return S, vE, cEP


RHO_SCALED_MODE = {"mode": "zentrum"}   # 'zentrum': corr = sqrt(1 - SD_Zentrum^2/SE^2); 'nullSD': corr = nullSD/SE


def a2_full_cov(win, lin, scaled):
    """4x4: drei Kontraste + Null-Statistik Y (Projektionsmodell: Y = lambda D_P2 + unabh. Rest,
    corr(Y, D_P2) = nullSD/SE_P2 wie im Akten-Modell [rj3]). Liefert Kovarianz, Mittelfaktoren, Schwellen."""
    w = A2[win]
    L = w[lin]
    S3, vE, cEP = a2_cov(win, lin)
    se2 = L["SE"]["P2"]
    if scaled and RHO_SCALED_MODE["mode"] == "zentrum":
        rho = math.sqrt(max(0.0, 1.0 - (L["zentrumSD"] / se2) ** 2))
    else:
        rho = L["nullSD"] / se2
    sY = se2 if scaled else L["nullSD"]
    S = np.zeros((4, 4))
    S[:3, :3] = S3
    covY = rho * sY * S3[0, :] / se2
    S[3, :3] = covY
    S[:3, 3] = covY
    S[3, 3] = sY ** 2
    mean_fac = np.array([1.0, 1.0, 1.0, w["kappa"]])
    thr_z = np.array([L["SE"][j] for j in COND])          # Schwelle = z * SE
    thr_null = A2["tau95"] * se2 if scaled else L["d95"]    # skalierte Null: tau95 x SE_bind
    return S, mean_fac, thr_z, thr_null, rho


def solve_mde(pfun, target=0.8, lo=5.0, hi=80.0):
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if pfun(mid) < target else (lo, mid)
    return 0.5 * (lo + hi)


def sec_g():
    P("\n================ (g) Strenge-Quotient und A2 unter 3.1 ================")
    t0 = time.process_time()
    rng = np.random.default_rng(31007)
    NMC = 2_000_000
    E4 = rng.standard_normal((NMC, 4))
    E8 = rng.standard_normal((NMC, 8))
    out = {"eingaben_akte": {k: v for k, v in A2.items()}}
    # Modellpruefung Kovarianz
    chk = {}
    for win in ("W1", "W2"):
        for lin in ("zentral", "stress"):
            S3, vE, cEP = a2_cov(win, lin)
            chk[f"{win}_{lin}"] = {"SE_E": math.sqrt(vE), "Cov_E_P": cEP,
                                   "corr_P2_P3fix": S3[0, 1] / math.sqrt(S3[0, 0] * S3[1, 1]),
                                   "corr_P2_P3all": S3[0, 2] / math.sqrt(S3[0, 0] * S3[2, 2]),
                                   "corr_null_P2": A2[win][lin]["nullSD"] / A2[win][lin]["SE"]["P2"]}
    out["modell_korrelationen"] = chk
    P("Modell-Korrelationen:", {k: {kk: (round(vv, 3) if isinstance(vv, float) else {a: round(b, 3) for a, b in vv.items()}) for kk, vv in v.items()} for k, v in chk.items()})

    def window_power(win, lin, conds, scaled, mode, gate=1.0):
        """Power je Fenster (alpha 0,05 je Bedingung). conds: Teilmenge von ['P2','P3fix','P3all','null'];
        mode 'produkt' | 'bivariat' (P2&null exakt, Rest Produkt) | 'gemeinsam' (alles exakt)."""
        S, mf, thr_z, thr_null, rho = a2_full_cov(win, lin, scaled)
        idx = [i for i, c in enumerate(("P2", "P3fix", "P3all", "null")) if c in conds]
        sd = np.sqrt(np.diag(S))
        thr = np.array([Z95 * thr_z[0], Z95 * thr_z[1], Z95 * thr_z[2], thr_null])
        Lc = np.linalg.cholesky(S + 1e-12 * np.eye(4))
        Y0 = E4 @ Lc.T

        def pw(pi):
            m = mf * pi
            if mode == "produkt":
                return gate * float(np.prod([norm.sf((thr[i] - m[i]) / sd[i]) for i in idx]))
            if mode == "bivariat":
                p = 1.0
                rest = [i for i in idx if i not in (0, 3)]
                for i in rest:
                    p *= norm.sf((thr[i] - m[i]) / sd[i])
                pair = [i for i in idx if i in (0, 3)]
                if len(pair) == 2:
                    p *= biv_upper((thr[0] - m[0]) / sd[0], (thr[3] - m[3]) / sd[3], rho)
                else:
                    for i in pair:
                        p *= norm.sf((thr[i] - m[i]) / sd[i])
                return gate * p
            ok = np.ones(NMC, dtype=bool)
            for i in idx:
                ok &= (Y0[:, i] + m[i]) > thr[i]
            return gate * float(ok.mean())
        return pw

    rows = {}
    spec = [
        ("Grundfassung_P2_zentral", "zentral", ["P2"], False, "produkt", 1.0),
        ("P3fix_einzeln_zentral", "zentral", ["P3fix"], False, "produkt", 1.0),
        ("drei_z_produkt_zentral", "zentral", ["P2", "P3fix", "P3all"], False, "produkt", 1.0),
        ("drei_z_gemeinsam_zentral", "zentral", ["P2", "P3fix", "P3all"], False, "gemeinsam", 1.0),
        ("produkt_mit_null_zentral_unskaliert", "zentral", ["P2", "P3fix", "P3all", "null"], False, "produkt", 1.0),
        ("bivariat_zentral_unskaliert", "zentral", ["P2", "P3fix", "P3all", "null"], False, "bivariat", 1.0),
        ("gemeinsam_zentral_unskaliert", "zentral", ["P2", "P3fix", "P3all", "null"], False, "gemeinsam", 1.0),
        ("produkt_stress_unskaliert", "stress", ["P2", "P3fix", "P3all", "null"], False, "produkt", 1.0),
        ("bivariat_stress_unskaliert", "stress", ["P2", "P3fix", "P3all", "null"], False, "bivariat", 1.0),
        ("gemeinsam_stress_unskaliert", "stress", ["P2", "P3fix", "P3all", "null"], False, "gemeinsam", 1.0),
        ("produkt_stress_skaliert", "stress", ["P2", "P3fix", "P3all", "null"], True, "produkt", 1.0),
        ("bivariat_stress_skaliert", "stress", ["P2", "P3fix", "P3all", "null"], True, "bivariat", 1.0),
        ("gemeinsam_stress_skaliert", "stress", ["P2", "P3fix", "P3all", "null"], True, "gemeinsam", 1.0),
        ("produkt_stress_skaliert_gate4", "stress", ["P2", "P3fix", "P3all", "null"], True, "produkt", A2["gate4"]),
        ("bivariat_stress_skaliert_gate4", "stress", ["P2", "P3fix", "P3all", "null"], True, "bivariat", A2["gate4"]),
        ("gemeinsam_stress_skaliert_gate4", "stress", ["P2", "P3fix", "P3all", "null"], True, "gemeinsam", A2["gate4"]),
        ("produkt_zentral_skaliert", "zentral", ["P2", "P3fix", "P3all", "null"], True, "produkt", 1.0),
        ("bivariat_zentral_skaliert", "zentral", ["P2", "P3fix", "P3all", "null"], True, "bivariat", 1.0),
        ("produkt_zentral_skaliert_gate4", "zentral", ["P2", "P3fix", "P3all", "null"], True, "produkt", A2["gate4"]),
        ("gemeinsam_zentral_skaliert_gate4", "zentral", ["P2", "P3fix", "P3all", "null"], True, "gemeinsam", A2["gate4"]),
        ("bivariat_zentral_skaliert_gate4", "zentral", ["P2", "P3fix", "P3all", "null"], True, "bivariat", A2["gate4"]),
    ]
    akte = {"Grundfassung_P2_zentral": (18.25, 18.8), "drei_z_produkt_zentral": (22.8, 23.1),
            "produkt_mit_null_zentral_unskaliert": (23.43, 24.36), "bivariat_zentral_unskaliert": (22.93, 23.77),
            "gemeinsam_zentral_unskaliert": (21.2, 22.3), "produkt_stress_unskaliert": (26.1, 27.2),
            "bivariat_stress_unskaliert": (25.5, 26.5), "produkt_stress_skaliert": (26.6, 29.3),
            "bivariat_stress_skaliert": (25.4, 28.5), "produkt_stress_skaliert_gate4": (29.0, 32.1),
            "gemeinsam_stress_skaliert_gate4": (26.2, 30.6), "produkt_zentral_skaliert": (23.9, 26.2),
            "bivariat_zentral_skaliert": (22.9, 25.5), "produkt_zentral_skaliert_gate4": (26.0, 28.8),
            "gemeinsam_zentral_skaliert_gate4": (23.7, 27.4), "P3fix_einzeln_zentral": (19.7, 19.7)}
    P(f"{'Zeile':>40} | {'W1':>6} {'W2':>6} | Akte W1/W2")
    for name, lin, conds, scaled, mode, gate in spec:
        v = {}
        for win in ("W1", "W2"):
            v[win] = solve_mde(window_power(win, lin, conds, scaled, mode, gate))
        v["akte"] = akte.get(name)
        rows[name] = v
        P(f"{name:>40} | {v['W1']:6.2f} {v['W2']:6.2f} | {v['akte']}")
    out["fenster_zeilen"] = rows
    alt_rows = {}
    RHO_SCALED_MODE["mode"] = "nullSD"
    for name, lin, conds, scaled, mode, gate in spec:
        if scaled and mode in ("bivariat", "gemeinsam"):
            alt_rows[name] = {win: solve_mde(window_power(win, lin, conds, scaled, mode, gate)) for win in ("W1", "W2")}
    RHO_SCALED_MODE["mode"] = "zentrum"
    out["fenster_zeilen_alternativ_korrelation_nullSD"] = alt_rows
    P("Alternative Korrelation skaliert (nullSD/SE wie unskaliert):", {k: (round(v['W1'], 2), round(v['W2'], 2)) for k, v in alt_rows.items()})
    g18 = rows["Grundfassung_P2_zentral"]["W2"]
    chain_today = [("Grundfassung P2'' (zentral)", g18), ("P3fix bindend", rows["P3fix_einzeln_zentral"]["W2"]),
                   ("Produkt drei z", rows["drei_z_produkt_zentral"]["W2"]),
                   ("+ Null-Faktor (Produkt)", rows["produkt_mit_null_zentral_unskaliert"]["W2"]),
                   ("+ Stress bindend", rows["produkt_stress_unskaliert"]["W2"]),
                   ("+ skalierte Null", rows["produkt_stress_skaliert"]["W2"]),
                   ("+ Gate-(4)-Faktor 0,9025", rows["produkt_stress_skaliert_gate4"]["W2"])]
    chain_min = [("Grundfassung P2'' (zentral)", g18),
                 ("exakte P2''-Bedingung (bivariat), zentral", rows["bivariat_zentral_unskaliert"]["W2"]),
                 ("+ Stress bindend", rows["bivariat_stress_unskaliert"]["W2"]),
                 ("+ skalierte Null", rows["bivariat_stress_skaliert"]["W2"]),
                 ("+ Gate-(4)-Faktor 0,9025", rows["bivariat_stress_skaliert_gate4"]["W2"])]
    chain_full = [("Grundfassung P2'' (zentral)", g18),
                  ("drei z exakt gemeinsam, zentral", rows["drei_z_gemeinsam_zentral"]["W2"]),
                  ("+ Null exakt gemeinsam, zentral", rows["gemeinsam_zentral_unskaliert"]["W2"]),
                  ("+ Stress bindend", rows["gemeinsam_stress_unskaliert"]["W2"]),
                  ("+ skalierte Null", rows["gemeinsam_stress_skaliert"]["W2"]),
                  ("+ Gate-(4)-Faktor 0,9025", rows["gemeinsam_stress_skaliert_gate4"]["W2"])]
    for lab, ch in (("heute_produkt", chain_today), ("P7_minimal_bivariat", chain_min), ("P7_voll_gemeinsam", chain_full)):
        out[f"kette_W2_{lab}"] = [{"schritt": s, "MDE80": v, "MDE_faktor": v / g18, "daten_faktor": (v / g18) ** 2} for s, v in ch]
        out[f"strenge_quotient_W2_{lab}"] = ch[-1][1] / g18
        P(f"Kette W2 {lab}: " + " -> ".join(f"{v:.2f}" for _, v in ch) + f"; Strenge-Quotient {ch[-1][1] / g18:.3f} (Daten x{(ch[-1][1] / g18) ** 2:.3f})")

    # ---- 3.1: gepoolt W1+W2 bei alpha 0,0025 je Bedingung + REZENZ-Screen (P2'' in W2 bei 0,05) ----
    tau_p = Z9975 * A2["tau95"] / Z95       # Annahme: Tail-Faktor der Null wie bei 95 %
    def pooled_builder(lin, scaled, weights=(0.5, 0.5), T_months=24.0, screen_all=False):
        """Poolt n = T/12 Fenster (Kovarianz = Mittel W1/W2 je Fenster) gleichgewichtet; Screen = W2-Fenster.
        Bei T = 24: exakt W1 + W2."""
        S1, mf1, _, _, _ = a2_full_cov("W1", lin, scaled)
        S2, mf2, _, _, _ = a2_full_cov("W2", lin, scaled)
        if abs(T_months - 24.0) < 1e-9:
            Sp = weights[0] ** 2 * S1 + weights[1] ** 2 * S2
            Cps = weights[1] * S2            # Cov(gepoolt, W2-Fenster)
            mfp = weights[0] * mf1 + weights[1] * mf2
        else:
            f = 12.0 / T_months
            Sp = 0.5 * (S1 + S2) * f
            Cps = S2 * f
            mfp = 0.5 * (mf1 + mf2)
        big = np.zeros((8, 8))
        big[:4, :4] = Sp
        big[4:, 4:] = S2
        big[:4, 4:] = Cps
        big[4:, :4] = Cps.T
        Lc = np.linalg.cholesky(big + 1e-10 * np.eye(8))
        Y = E8 @ Lc.T
        sdp = np.sqrt(np.diag(Sp))
        sdw = np.sqrt(np.diag(S2))
        thr_p = np.array([Z9975 * sdp[0], Z9975 * sdp[1], Z9975 * sdp[2], (tau_p * sdp[3])])
        if not scaled:
            # unskalierte Null: Schwelle tau_p x gepoolte Null-SD (Statistik-SD = Null-SD)
            thr_p[3] = tau_p * sdp[3]
        return Y, mfp, mf2, thr_p, sdw

    def pooled_power_fun(lin, scaled, conds, gate=1.0, screen=True, T_months=24.0, screen_all=False, weights=(0.5, 0.5)):
        Y, mfp, mf2, thr_p, sdw = pooled_builder(lin, scaled, weights, T_months)
        idx = [i for i, c in enumerate(("P2", "P3fix", "P3all", "null")) if c in conds]

        def pw(pi):
            ok = np.ones(NMC, dtype=bool)
            for i in idx:
                ok &= (Y[:, i] + mfp[i] * pi) > thr_p[i]
            if screen:
                ok &= (Y[:, 4] + pi) > Z95 * sdw[0]
                if screen_all:
                    ok &= (Y[:, 5] + pi) > Z95 * sdw[1]
                    ok &= (Y[:, 6] + pi) > Z95 * sdw[2]
            return gate * float(ok.mean())
        return pw

    pool = {}
    pspec = [("Q0_P2_gepoolt_ohne_screen_zentral", "zentral", False, ["P2"], 1.0, False),
             ("Q1_P2_gepoolt_mit_screen_zentral", "zentral", False, ["P2"], 1.0, True),
             ("Q2_drei_z_gemeinsam_zentral", "zentral", False, ["P2", "P3fix", "P3all"], 1.0, True),
             ("Q3_plus_null_unskaliert_zentral", "zentral", False, ["P2", "P3fix", "P3all", "null"], 1.0, True),
             ("Q4_stress", "stress", False, ["P2", "P3fix", "P3all", "null"], 1.0, True),
             ("Q5_skalierte_null", "stress", True, ["P2", "P3fix", "P3all", "null"], 1.0, True),
             ("Q6_gate4_09025", "stress", True, ["P2", "P3fix", "P3all", "null"], A2["gate4"], True),
             ("Q6alt_gate4_bei_0025_09950", "stress", True, ["P2", "P3fix", "P3all", "null"], 0.9975 ** 2, True)]
    for name, lin, scaled, conds, gate, scr in pspec:
        pool[name] = solve_mde(pooled_power_fun(lin, scaled, conds, gate, scr))
    pool["Q5b_screen_alle_drei_z_W2"] = solve_mde(pooled_power_fun("stress", True, ["P2", "P3fix", "P3all", "null"], A2["gate4"], True, screen_all=True))
    pool["analytisch_P2_gepoolt_zentral"] = MU_FIX * math.sqrt(7.34 ** 2 + 7.58 ** 2) / 2
    pool["strenge_quotient_vs_Q1"] = pool["Q6_gate4_09025"] / pool["Q1_P2_gepoolt_mit_screen_zentral"]
    pool["strenge_quotient_vs_Q0"] = pool["Q6_gate4_09025"] / pool["Q0_P2_gepoolt_ohne_screen_zentral"]
    pool["tau_9975_annahme"] = tau_p
    out["gepoolt_31"] = pool
    P("3.1 gepoolt W1+W2 (alpha 0,0025 je Bedingung, REZENZ-Screen P2'' W2 bei 0,05):",
      {k: round(v, 3) for k, v in pool.items()})
    # MDE als Funktion der Konfirmationslaenge T (Monate) fuer (h): alle Festlegungen (Q6) und Grundfassung (Q1)
    scan = {}
    for T in (24, 30, 36, 42, 48, 60, 72, 84, 96, 120):
        TT = float(T) + (1e-6 if T == 24 else 0.0)
        scan[str(T)] = {"Q6": solve_mde(pooled_power_fun("stress", True, ["P2", "P3fix", "P3all", "null"], A2["gate4"], True, TT)),
                        "Q1": solve_mde(pooled_power_fun("zentral", False, ["P2"], 1.0, True, TT)),
                        "Q6_P6_stabilitaet": solve_mde(pooled_power_fun("stress", True, ["P2", "P3fix", "P3all", "null"], A2["gate4"], False, TT), target=0.8 / 0.95)}
    out["gepoolt_31_laengen_scan"] = scan
    P("MDE80 (bp) gegen Konfirmationslaenge T Monate [Q6 alle Festlegungen mit Screen, Q1 Grundfassung mit Screen, Q6 mit P-6-Stabilitaetstest statt Screen]: ",
      {k: (round(v['Q6'], 2), round(v['Q1'], 2), round(v['Q6_P6_stabilitaet'], 2)) for k, v in scan.items()})
    floor = {"Q6_boden_analytisch": (Z95 + float(Z(0.8 / A2["gate4"]))) * A2["W2"]["stress"]["SE"]["P2"],
             "Q1_boden_analytisch": C80_05 * A2["W2"]["zentral"]["SE"]["P2"]}
    out["boden_rezenz_screen"] = floor
    P("Boden durch REZENZ-Screen (T -> inf): Q6 (z95 + Phi^-1(0,8/0,9025)) x SE_W2,stress =", round(floor["Q6_boden_analytisch"], 3),
      "; Q1 2,4865 x SE_W2,zentral =", round(floor["Q1_boden_analytisch"], 3))
    # heute (C.10 je Fenster): Fensterlaenge L fuer MDE 22 bp mit der Produktkette W2 (32,1 bei 12 Monaten)
    L_c10 = 12.0 * (rows["produkt_stress_skaliert_gate4"]["W2"] / 22.0) ** 2
    out["heute_C10_fensterlaenge_monate_fuer_22bp"] = L_c10
    out["heute_C10_P7min_fensterlaenge_monate_fuer_22bp"] = 12.0 * (rows["bivariat_stress_skaliert_gate4"]["W2"] / 22.0) ** 2
    P(f"Heute (C.10, Produktkette W2 {rows['produkt_stress_skaliert_gate4']['W2']:.2f} bp bei 12 Monaten): Fensterlaenge fuer 22 bp {L_c10:.1f} Monate je Fenster")
    put("g", out)
    P(f"[Zeit (g): {time.process_time() - t0:.1f} s CPU]")
    return out


# =====================================================================================
# (h) Gegenueberstellung heute / 3.1 und fruehester Konfirmationszeitpunkt
# =====================================================================================
def add_months(y, m, months):
    tot = y * 12 + (m - 1) + months
    yy = int(tot // 12)
    mm = int(tot % 12) + 1
    frac = tot - math.floor(tot)
    return f"{yy:04d}-{mm:02d}" if frac < 1e-9 else f"{yy:04d}-{mm:02d}(+{frac:.2f} Mon.)"


def months_to_ym(y, m, months):
    tot = y * 12 + (m - 1) + math.ceil(months - 1e-9)
    return f"{tot // 12:04d}-{tot % 12 + 1:02d}"


def sec_h(a_out, b_grid, b_mc, g_out, d_out):
    P("\n================ (h) Gegenueberstellung heute / 3.1 ================")
    t0 = time.process_time()
    out = {}
    # Klasse W: Wochen-IC, SESOI 0,040 (und 0,020), SD je Woche 0,130 (stress) / 0,090 (gemessen W1)
    R_scr = {0.5: b_mc["screen_all_r0.500_nofut"]["R_max"], 1 / 3: b_mc["screen_all_r0.333_nofut"]["R_max"],
             0.25: b_mc["screen_all_r0.250_nofut"]["R_max"]}
    EN_scr = {0.5: b_mc["screen_all_r0.500_nofut"]["EN_H1"], 1 / 3: b_mc["screen_all_r0.333_nofut"]["EN_H1"],
              0.25: b_mc["screen_all_r0.250_nofut"]["EN_H1"]}
    rr = np.array([0.25, 1 / 3, 0.5])
    Rint = lambda r: float(np.interp(min(max(r, 0.25), 0.5), rr, [R_scr[0.25], R_scr[1 / 3], R_scr[0.5]]))
    ENint = lambda r: float(np.interp(min(max(r, 0.25), 0.5), rr, [EN_scr[0.25], EN_scr[1 / 3], EN_scr[0.5]]))
    W = {}
    mu_stab = Z9975 + float(Z(0.8 / 0.95))
    for sd in (0.130, 0.090):
        for ses in (0.040, 0.020):
            n_c10 = (C80_05 * sd / ses) ** 2                  # Wochen je Fenster, C.10 je 0,80
            floor = C80_05 * sd / math.sqrt(52.0)              # MDE-Boden des REZENZ-Screens (52 Wochen, 0,05, Power 0,80)
            if floor >= ses:
                T, r, Tmax, Een = float("inf"), 0.0, float("inf"), float("inf")
            else:
                def f_T(T):
                    r_ = min(1.0, 52.0 / T)
                    mu_ = optimize.brentq(lambda m: p2a_power(m, r_) - 0.8, 2.0, 3.0 / math.sqrt(r_) + 12.0)
                    return mu_ * sd / ses - math.sqrt(T)
                T = optimize.brentq(f_T, 52.0 + 1e-6, 52.0 * 2000) if f_T(52.0 + 1e-6) > 0 else (MU_FIX * sd / ses) ** 2
                r = min(1.0, 52.0 / T)
                Tmax = T * Rint(r)
                Een = T * ENint(r)
            W[f"sd{sd}_sesoi{ses}"] = {"C10_wochen_je_fenster": n_c10, "C10_testbar_W1W2": n_c10 <= 52.0,
                                       "C10_prospektiv_ab_2026_07_ende_monate": 2 * n_c10 * 12 / 52,
                                       "P2a_MDE_boden_52W": floor,
                                       "P2a_fest_wochen": T, "r": r, "GSD_max_wochen": Tmax, "GSD_EN_H1_wochen": Een,
                                       "P6_stabilitaet_fest_wochen": (mu_stab * sd / ses) ** 2}
    out["klasse_W"] = W
    P("Klasse W (Wochen): ", {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in W.items()})
    # Daten-Startpunkte (Monate ab 2024-07): Lesart B (W1/W2 + K-Quartale nutzbar), Lesart A (nur Quartale in K bei Registrierung: ab 2026-01)
    dates = {}
    for k, v in W.items():
        for lab, Tw in (("fest", v["P2a_fest_wochen"]), ("GSD_max", v["GSD_max_wochen"]), ("GSD_EN_H1", v["GSD_EN_H1_wochen"]),
                        ("P6_stabilitaet_fest", v["P6_stabilitaet_fest_wochen"])):
            mon = Tw * 12 / 52
            if not math.isfinite(mon):
                dates[f"{k}_{lab}"] = {"monate": None, "termin": "nie (REZENZ-Screen-Boden ueber SESOI)"}
                continue
            dates[f"{k}_{lab}"] = {"monate": mon,
                                   "lesart_B_ab_2024_07": months_to_ym(2024, 7, mon) if mon > 30 else "2027-01 (Registrierung, Daten liegen vor)",
                                   "lesart_A_ab_2026_01": months_to_ym(2026, 1, mon) if mon > 12 else "2027-01 (Registrierung, Daten liegen vor)"}
        nc = v["C10_wochen_je_fenster"]
        dates[f"{k}_heute_C10"] = {"wochen_je_fenster": nc,
                                   "W1W2": "nach Registrierung (Fenster blind, liegen vor)" if nc <= 52 else "nein (MDE > SESOI auf 12 Monaten)",
                                   "prospektiv_2_Fenster_ab_2026_07": months_to_ym(2026, 7, 2 * nc * 12 / 52),
                                   "DEC96_E2_L_max_12": "GL-012" if nc > 52 else "zulaessig"}
    out["klasse_W_termine"] = dates
    for k, v in dates.items():
        P("  ", k, v)
    # Klasse E: A2 (SESOI Taker 22 bp)
    scan = g_out["gepoolt_31_laengen_scan"]
    Ts = np.array([float(t) for t in scan.keys()])
    q6 = np.array([v["Q6"] for v in scan.values()])
    q1 = np.array([v["Q1"] for v in scan.values()])
    def T_for(target, arr):
        if arr[0] <= target:
            return float(Ts[0]) * (arr[0] / target) ** 2
        for i in range(1, len(Ts)):
            if arr[i] <= target:
                # MDE ~ T^-1/2 zwischen Stuetzstellen: log-lineare Interpolation
                x0, x1 = math.log(Ts[i - 1]), math.log(Ts[i])
                y0, y1 = math.log(arr[i - 1]), math.log(arr[i])
                return math.exp(x0 + (math.log(target) - y0) * (x1 - x0) / (y1 - y0))
        return float("inf")
    E = {}
    q6s = np.array([v["Q6_P6_stabilitaet"] for v in scan.values()])
    for ses in (22.0, 25.0):
        T6 = T_for(ses, q6)
        T1 = T_for(ses, q1)
        T6s = T_for(ses, q6s)
        if not math.isfinite(T6):
            E[f"sesoi{ses}"] = {"T_fest_alle_festlegungen_monate": None, "termin_3_1": "nie (REZENZ-Screen-Boden ueber SESOI)",
                                "boden_Q6_T120": float(q6[-1]), "T_fest_grundfassung_monate": T1,
                                "T_P6_stabilitaet_monate": T6s,
                                "lesart_B_ende_P6_stabilitaet": months_to_ym(2024, 7, T6s) if math.isfinite(T6s) and T6s > 30 else ("2027-01" if math.isfinite(T6s) else "nie"),
                                "heute_C10_fensterlaenge_monate": 12.0 * (g_out["fenster_zeilen"]["produkt_stress_skaliert_gate4"]["W2"] / ses) ** 2,
                                "heute_C10_prospektiv_ende": months_to_ym(2026, 7, 2 * 12.0 * (g_out["fenster_zeilen"]["produkt_stress_skaliert_gate4"]["W2"] / ses) ** 2)}
            continue
        r6_ = min(1.0, 12.0 / T6)
        E[f"sesoi{ses}"] = {"T_P6_stabilitaet_monate": T6s,
                            "lesart_B_ende_P6_stabilitaet": months_to_ym(2024, 7, T6s) if math.isfinite(T6s) and T6s > 30 else "2027-01","T_fest_alle_festlegungen_monate": T6, "T_fest_grundfassung_monate": T1,
                            "T_GSD_max_monate": T6 * Rint(r6_), "T_GSD_EN_H1_monate": T6 * ENint(r6_),
                            "lesart_B_ende_fest": months_to_ym(2024, 7, T6) if T6 > 30 else "2027-01",
                            "lesart_B_ende_GSD_max": months_to_ym(2024, 7, T6 * Rint(r6_)),
                            "lesart_B_EN_H1": months_to_ym(2024, 7, T6 * ENint(r6_)),
                            "lesart_A_ende_fest": months_to_ym(2026, 1, T6) if T6 > 12 else "2027-01",
                            "lesart_A_ende_GSD_max": months_to_ym(2026, 1, T6 * Rint(r6_)),
                            "heute_C10_fensterlaenge_monate": 12.0 * (g_out["fenster_zeilen"]["produkt_stress_skaliert_gate4"]["W2"] / ses) ** 2,
                            "heute_C10_prospektiv_ende": months_to_ym(2026, 7, 2 * 12.0 * (g_out["fenster_zeilen"]["produkt_stress_skaliert_gate4"]["W2"] / ses) ** 2)}
    out["klasse_E_A2"] = E
    P("Klasse E (A2):", {k: {kk: (round(float(vv), 2) if isinstance(vv, (float, np.floating)) else vv) for kk, vv in v.items()} for k, v in E.items()})
    # Tabelle heute / 3.1
    a = a_out["r1_2"]
    tab = {
        "heute_C10_je080": {"alpha_je_test": 0.0025, "entscheidungs_power": 0.64, "EN_H1_in_Nfix0025": 2 * C80_05 ** 2 / MU_FIX ** 2,
                            "ppv": {str(b): 0.64 * b / (0.64 * b + 0.0025 * (1 - b)) for b in (0.05, 0.10, 0.25)},
                            "falsch_PASS_jahr_m8_basis0.10": 8 * 0.9 * 0.0025, "falsch_PASS_jahr_real_m0": 0.0},
        "3.1_fest_P2a_r1_2": {"alpha_je_test": a["alpha_eff_P2a"], "entscheidungs_power": 0.80,
                              "EN_H1_in_Nfix0025": a["info_P2a"] / MU_FIX ** 2,
                              "ppv": {str(b): 0.8 * b / (0.8 * b + a["alpha_eff_P2a"] * (1 - b)) for b in (0.05, 0.10, 0.25)},
                              "falsch_PASS_jahr_m8_basis0.10": 8 * 0.9 * a["alpha_eff_P2a"]},
        "3.1_GSD_screen_all_r1_2": {"alpha_je_test": b_mc["screen_all_r0.500_nofut"]["alpha_eff"], "entscheidungs_power": 0.80,
                                    "EN_H1_in_Nfix0025": b_mc["screen_all_r0.500_nofut"]["EN_H1"],
                                    "R_max": b_mc["screen_all_r0.500_nofut"]["R_max"],
                                    "ppv": {str(b): 0.8 * b / (0.8 * b + b_mc["screen_all_r0.500_nofut"]["alpha_eff"] * (1 - b)) for b in (0.05, 0.10, 0.25)},
                                    "falsch_PASS_jahr_m8_basis0.10": 8 * 0.9 * b_mc["screen_all_r0.500_nofut"]["alpha_eff"]},
        "3.1_GSD_screen_all_r1_3_fut": {"alpha_je_test": b_mc["screen_all_r0.333_fut"]["alpha_eff"], "entscheidungs_power": 0.80,
                                        "EN_H1_in_Nfix0025": b_mc["screen_all_r0.333_fut"]["EN_H1"],
                                        "EN_H0_in_Nfix0025": b_mc["screen_all_r0.333_fut"]["EN_H0"],
                                        "R_max": b_mc["screen_all_r0.333_fut"]["R_max"],
                                        "ppv": {str(b): 0.8 * b / (0.8 * b + b_mc["screen_all_r0.333_fut"]["alpha_eff"] * (1 - b)) for b in (0.05, 0.10, 0.25)},
                                        "falsch_PASS_jahr_m8_basis0.10": 8 * 0.9 * b_mc["screen_all_r0.333_fut"]["alpha_eff"]},
    }
    n005 = MU_FIX ** 2 / C80_05 ** 2
    for k, v in tab.items():
        v["EN_H1_in_N005"] = v["EN_H1_in_Nfix0025"] * n005
        if "R_max" in v:
            v["max_in_N005"] = v["R_max"] * n005
    tab["heute_C10_gemeinsam080_referenz"] = {"alpha_je_test": 0.0025, "entscheidungs_power": 0.80,
                                              "EN_H1_in_N005": 2 * (Z95 + Z(math.sqrt(0.8))) ** 2 / C80_05 ** 2}
    tab["3.1_fest_P2a_r1_3"] = {"alpha_je_test": a_out["r1_3"]["alpha_eff_P2a"], "entscheidungs_power": 0.80,
                                "EN_H1_in_N005": a_out["r1_3"]["info_P2a"] / C80_05 ** 2}
    tab["3.1_GSD_ohne_screen"] = {"alpha_je_test": b_grid["alpha0.0025_nofut"]["alpha_eff"], "entscheidungs_power": 0.80,
                                  "EN_H1_in_N005": b_grid["alpha0.0025_nofut"]["EN_H1"] * n005,
                                  "max_in_N005": b_grid["alpha0.0025_nofut"]["R_max"] * n005}
    out["tabelle"] = tab
    for k, v in tab.items():
        P("  ", k, {kk: (round(vv, 5) if isinstance(vv, float) else ({a_: round(b_, 4) for a_, b_ in vv.items()} if isinstance(vv, dict) else vv)) for kk, vv in v.items()})
    put("h", out)
    P(f"[Zeit (h): {time.process_time() - t0:.1f} s CPU]")
    return out


def sec_t():
    """Abgeleitete Textzahlen (Verhaeltnisse, Differenzen, Spannweiten) aus den Ergebnissen dieses Laufs."""
    P("\n================ (t) Abgeleitete Textzahlen ================")
    T = {}
    a = RES["a"]["zellen"]
    T["a_datenfaktor_prozent_vs_C10je080"] = {k: 100 * (v["faktor_P2a_vs_C10je080"] - 1) for k, v in a.items()}
    T["a_datenfaktor_prozent_vs_C10gem080"] = {k: 100 * (v["faktor_P2a_vs_C10gem080"] - 1) for k, v in a.items()}
    T["a_datenfaktor_prozent_vs_gepoolt"] = {k: 100 * (v["faktor_P2a_vs_gepoolt"] - 1) for k, v in a.items()}
    T["a_alpha_P2a_relativ_0025"] = {k: v["alpha_eff_P2a"] / 0.0025 for k, v in a.items()}
    T["a_MDE_P2a_r1_2_vs_C10je_SE12"] = RES["a"]["MDE_in_SE12"]["r1_2"]["P2a_MDE_in_SE12"] / RES["a"]["MDE_in_SE12"]["C10_je080_in_SE12"]
    u = RES["b"]["umrechnung"]
    T["b_prozent"] = {k: 100 * (v - 1) for k, v in u.items() if "_vs_" in k}
    gr = RES["b"]["gitter"]
    T["b_OBF_grenzen"] = {}
    for key in ("alpha0.0025_nofut", "alpha0.05_nofut"):
        cc = gr[key]["c"]
        zb = [cc / math.sqrt(k / 4.0) for k in (1, 2, 3, 4)]
        T["b_OBF_grenzen"][key] = {"z_grenze_je_blick": zb, "nominales_p_je_blick": [float(norm.sf(z)) for z in zb]}
    mc = RES["b"]["monte_carlo_1e6"]
    T["b_futility_mehr_maximum"] = {r: mc[f"screen_all_r{r}_fut"]["R_max"] - mc[f"screen_all_r{r}_nofut"]["R_max"]
                                     for r in ("0.500", "0.333", "0.250")}
    c = RES["c"]["zellen"]
    def rng_of(vals):
        vals = [v for v in vals if v is not None]
        return [min(vals), max(vals)]
    T["c_spannweiten"] = {
        "ratio_E_x_echt_zu_delta": rng_of([v.get("ratio_E_x_echt_zu_delta") for v in c.values()]),
        "power_echt_roh": rng_of([v["G0_roh"]["power_echt_mittel"] for v in c.values()]),
        "power_echt_bereinigt": rng_of([v["G0_bereinigt"]["power_echt_mittel"] for v in c.values()]),
        "anteil_power_unter_050_roh": rng_of([v["G0_roh"]["anteil_echt_power_unter_050"] for v in c.values()]),
        "anteil_registriert_bereinigt": rng_of([v["G0_bereinigt"]["anteil_registriert"] for v in c.values()]),
        "alpha_null_gewaehlt_n_ab_1000": rng_of([v.get("alpha_konfirmation_null_gewaehlt_MC") for v in c.values() if v.get("n_null_gewaehlt", 0) >= 1000]),
        "pi_K_bei_pi_0.1": rng_of([v["pi_K_basisrate"] for k, v in c.items() if "_pi0.1_" in k]),
        "P_med_le_theta": rng_of([v["P_med_le_theta"] for v in c.values()]),
        "alpha_wiederverwendung_bedingt": rng_of([v.get("alpha_wiederverwendung_X_daten") for v in c.values() if v.get("n_null_gewaehlt", 0) >= 1000]),
    }
    d = RES["d"]["zellen"]
    T["d_verhaeltnis_EV_BYallein_zu_fest"] = {k: v["BY_allein"]["E_V"] / max(v["fest"]["E_V"], 1e-12) for k, v in d.items()}
    T["d_spannweite_EV_m8"] = rng_of([v["fest"]["E_V"] for k, v in d.items() if k.endswith("_m8")])
    e = RES["e"]["einzeltest"]
    T["e_vielfache_nominal_0025"] = {k: {"z_naiv": v["H0"]["0.0025"]["z_naiv"] / 0.0025, "t_krit": v["H0"]["0.0025"]["t_krit"] / 0.0025,
                                         "SB_max_z": v["H0"]["0.0025"]["SB_max_z"] / 0.0025,
                                         "untere_flanke_SB": v["H0"]["0.0025"]["untere_flanke_SB_max_z"] / 0.0025} for k, v in e.items()}
    T["e_vielfache_ar1"] = {k: {a_: {kk: vv / float(a_) for kk, vv in v[a_].items()} for a_ in ("0.0025", "0.05")}
                            for k, v in RES["e"]["ar1_phi0_3"].items()}
    T["e_vielfache_gsd"] = {k: {kk: vv / 0.0025 for kk, vv in v["H0"].items()} for k, v in RES["e"]["gsd_geschaetzte_varianz"].items()}
    f = RES["f"]["monte_carlo"]
    T["f_vielfache_0025"] = {k: {m: v[m]["0.0025"] / 0.0025 for m in ("naiv", "NW_Lh-1", "NW_L4", "NW_L2h", "SB_max")} for k, v in f.items()}
    g = RES["g"]
    inc = {}
    for lab in ("heute_produkt", "P7_minimal_bivariat", "P7_voll_gemeinsam"):
        ch = g[f"kette_W2_{lab}"]
        inc[lab] = [{"schritt": ch[i]["schritt"], "zuwachs_bp": ch[i]["MDE80"] - ch[i - 1]["MDE80"]} for i in range(1, len(ch))]
    T["g_ketten_zuwachs"] = inc
    end = {lab: g[f"kette_W2_{lab}"][-1]["MDE80"] for lab in ("heute_produkt", "P7_minimal_bivariat", "P7_voll_gemeinsam")}
    T["g_P7_effekt_bp"] = {"minimal": end["heute_produkt"] - end["P7_minimal_bivariat"], "voll": end["heute_produkt"] - end["P7_voll_gemeinsam"]}
    q = g["gepoolt_31"]
    T["g_gepoolt_zuwachs"] = {"screen": q["Q1_P2_gepoolt_mit_screen_zentral"] - q["Q0_P2_gepoolt_ohne_screen_zentral"],
                              "placebos": q["Q2_drei_z_gemeinsam_zentral"] - q["Q1_P2_gepoolt_mit_screen_zentral"],
                              "null": q["Q3_plus_null_unskaliert_zentral"] - q["Q2_drei_z_gemeinsam_zentral"],
                              "stress": q["Q4_stress"] - q["Q3_plus_null_unskaliert_zentral"],
                              "skalierte_null": q["Q5_skalierte_null"] - q["Q4_stress"],
                              "gate4": q["Q6_gate4_09025"] - q["Q5_skalierte_null"],
                              "festlegungen_Q3_bis_Q6": q["Q6_gate4_09025"] - q["Q3_plus_null_unskaliert_zentral"]}
    T["g_SQ_datenfaktor_gepoolt"] = {"vs_Q1": q["strenge_quotient_vs_Q1"] ** 2, "vs_Q0": q["strenge_quotient_vs_Q0"] ** 2}
    put("t", T)
    def show(x):
        if isinstance(x, dict):
            return {k: show(v) for k, v in x.items()}
        if isinstance(x, list):
            return [show(v) for v in x]
        if isinstance(x, float):
            return round(x, 4)
        return x
    for k, v in T.items():
        P(f"{k}: {show(v)}")


REPO_SCRIPTS = "/home/user/scinance/scinance3-impl/state/prd_analyse_2026-11-01/scripts"


def sec_0():
    """Reproduktion der Vorarbeiten: die drei Skripte (nur Ausgabe auf stdout, keine Dateien) werden mit python3 -I
    ausgefuehrt; orch_review_check wird gegen die abgelegte .out-Datei verglichen."""
    import hashlib
    import resource
    import subprocess
    P("\n================ (0) Reproduktion der Vorarbeiten ================")
    out = {}
    for name in ("orch_review_check.py", "review_calc.py", "gsd_fut.py"):
        path = os.path.join(REPO_SCRIPTS, name)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        res = subprocess.run([sys.executable, "-I", path], capture_output=True, text=True, timeout=900, cwd=HERE)
        lines = res.stdout.rstrip("\n").split("\n")
        cell = {"sha256": sha, "returncode": res.returncode, "stdout": lines}
        if name == "orch_review_check.py":
            ref = open(os.path.join(REPO_SCRIPTS, "orch_review_check.out")).read().rstrip("\n").split("\n")
            cell["identisch_mit_abgelegter_out"] = (lines == ref)
        out[name] = cell
        P(f"--- {name} (sha256 {sha[:16]}..., rc {res.returncode})" +
          (f", identisch mit orch_review_check.out: {cell['identisch_mit_abgelegter_out']}" if "identisch_mit_abgelegter_out" in cell else ""))
        for ln in lines:
            P("    " + ln)
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    out["cpu_sekunden_kindprozesse"] = ru.ru_utime + ru.ru_stime
    put("reproduktion", out)


def main():
    P("OC Verfassung 3.1 - oc_sim.py (deterministisch; Seeds 31001..31010 + Zellindex)")
    P(f"Konstanten: z95 {Z95:.4f}, z9975 {Z9975:.4f}, z80 {Z80:.4f}, MDE-Faktor gepoolt 0,0025 {MU_FIX:.4f}, 0,05 {C80_05:.4f}")
    put("konstanten", {"z95": Z95, "z9975": Z9975, "z80": Z80, "mu_fix_0025": MU_FIX, "c80_005": C80_05})
    sec_0()
    a_out = sec_a()
    b_grid, b_mc = sec_b(a_out)
    c_out, keep, powf = sec_c(a_out)
    d_out = sec_d(a_out, keep)
    e_out = sec_e()
    f_out = sec_f()
    g_out = sec_g()
    h_out = sec_h(a_out, b_grid, b_mc, g_out, d_out)
    sec_t()
    import resource
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    put("meta.cpu_sekunden", time.process_time() - T_START)
    put("meta.cpu_sekunden_inkl_kindprozesse", time.process_time() - T_START + ru.ru_utime + ru.ru_stime)
    P(f"CPU inkl. Reproduktions-Kindprozesse: {time.process_time() - T_START + ru.ru_utime + ru.ru_stime:.1f} s")
    with open(os.path.join(HERE, "oc_results.json"), "w", encoding="ascii") as fh:
        json.dump(RES, fh, indent=1, ensure_ascii=True, default=str)
    P(f"\nGesamt-CPU: {time.process_time() - T_START:.1f} s; oc_results.json geschrieben.")


if __name__ == "__main__":
    main()
