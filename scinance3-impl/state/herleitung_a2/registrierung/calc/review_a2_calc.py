#!/usr/bin/env python3
"""Review (adversarial, symmetric mandate VR-f06) of the A2 registration draft 3.1: independent re-computation.

Own implementation (not a copy of a2_reg_calc.py), different seed (7), 400.000 paths, numpy/scipy only, no market
data, no sealed file, no network.  Same published nuisance inputs (NULL_SIMULATION_A2.md T3: SEs, null SDs, counts;
stab_results.json s4b: C_B 2,886).  Checks:
  (1) calendar counts (K quarters, W1/W2) and STRESS_ABS days in the judging windows (dates only);
  (2) exact O'Brien-Fleming alpha for the registered information fractions (recursive numerical integration);
  (3) Monte Carlo of the whole rule: alpha_eff and its decomposition (primary -> +P3fix -> +P3all -> +null -> x gate),
      P(PASS | 22), MDE80 of the plan and per look, protection line variants, strictness chain;
  (4) hidden-strictness / hidden-leniency probes: side conditions at fixed 2,8070 (G-03); t-boundaries instead of z;
      "12 calendar months" against "four data quarters" for the youngest part; placebo dilution in zone K (P2' carries
      part of the effect); alternative Grundfassung definitions for the strictness ratio;
  (5) fixed-rule MDE80 (feasibility31 R5 convention) reproduction.
Run: python3 -I review_a2_calc.py  (writes review_a2_calc.out and review_a2_calc.json next to it).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import time

import numpy as np
from scipy.stats import norm, t as student_t

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "/home/user/scinance"
SEED = 7
N = 400_000

# ---------------------------------------------------------------------------------------------------------------------
# published inputs (NULL_SIMULATION_A2.md T3, T2 header; DEC-104 E2; DEC-107 (1); stab_results.json s4b)
# ---------------------------------------------------------------------------------------------------------------------
Z_POOL = float(norm.isf(0.0025))          # 2.8070
Z_STAB = float(norm.isf(0.05))            # 1.6449
GATE = 0.9025
TAU95 = 1.6553
SESOI = 22.0
C_B = 2.886
SD_E, C_E = 43.83, 1.1491                 # class-E SD (pooled pre-period), c_bind Friday
SE_W1 = {"P2": 7.34, "P3fix": 7.93, "P3all": 6.56}
SE_W2 = {"P2": 7.58, "P3fix": 7.93, "P3all": 6.56}
SE_W1_S = {"P2": 8.25, "P3fix": 8.66, "P3all": 7.39}
SE_W2_S = {"P2": 8.52, "P3fix": 8.67, "P3all": 7.39}
SD_E_S = 49.37
CNT_W1 = {"E": 52, "P2": 208, "P3fix": 248, "P3all": 260}
CNT_W2 = {"E": 52, "P2": 159, "P3fix": 247, "P3all": 259}
CENTRE_SD_W2 = 2.97
OUTLIERS = {dt.date(2020, 8, 27), dt.date(2024, 8, 19)}
LOOKS = [10, 11, 12, 13]                  # blocks included at looks 1..4
LOOK_DATES = ["2027-04-01", "2027-07-01", "2027-10-01", "2028-01-01"]

OUT: dict = {"meta": {"seed": SEED, "paths": N, "role": "Review", "date": "2026-11-04"}}
LINES: list[str] = []


def P(s: str = "") -> None:
    LINES.append(s)


# ---------------------------------------------------------------------------------------------------------------------
# (1) calendar
# ---------------------------------------------------------------------------------------------------------------------
def count_days(a: dt.date, b: dt.date) -> dict:
    c = {"Fr": 0, "MoDo": 0, "P3fix": 0, "P3all": 0, "days": 0}
    d = a
    while d <= b:
        c["days"] += 1
        if d not in OUTLIERS:
            wd = d.weekday()
            if wd == 4:
                c["Fr"] += 1
                # month-end Friday: next Friday falls into another month
                if (d + dt.timedelta(days=7)).month == d.month:
                    c["P3fix"] += 1
            elif wd <= 3:
                c["MoDo"] += 1
                c["P3fix"] += 1
            if wd <= 4:
                c["P3all"] += 1
        d += dt.timedelta(days=1)
    return c


KQ = [("2026-10-01", "2026-12-31"), ("2027-01-01", "2027-03-31"), ("2027-04-01", "2027-06-30"),
      ("2027-07-01", "2027-09-30"), ("2027-10-01", "2027-12-31")]
W1 = (dt.date(2024, 7, 1), dt.date(2025, 6, 30))
W2 = (dt.date(2025, 7, 1), dt.date(2026, 6, 28))
W2Q4 = (dt.date(2026, 4, 4), dt.date(2026, 6, 28))   # daily futures deliveries from 2026-04-04


def calendar() -> dict:
    P("(1) Kalender (eigene Zaehlung, Ausreisser 2024-08-19 ausgeschlossen)")
    out = {"K": []}
    tot = {"Fr": 0, "MoDo": 0, "P3fix": 0, "P3all": 0}
    for a, b in KQ:
        c = count_days(dt.date.fromisoformat(a), dt.date.fromisoformat(b))
        out["K"].append({"von": a, "bis": b, **c})
        for k in tot:
            tot[k] += c[k]
        P(f"  K {a}..{b}: Fr {c['Fr']}, Mo-Do {c['MoDo']}, P3fix {c['P3fix']}, P3all {c['P3all']}")
    out["K_total"] = tot
    P(f"  K gesamt: Fr {tot['Fr']}, Mo-Do {tot['MoDo']}, P3fix {tot['P3fix']}, P3all {tot['P3all']}  "
      f"(Entwurf: 66 / 261 / 312 / 327)")
    c1, c2, c24 = count_days(*W1), count_days(*W2), count_days(*W2Q4)
    out["W1"], out["W2"], out["W2Q4"] = c1, c2, c24
    P(f"  W1: Fr {c1['Fr']}, Mo-Do {c1['MoDo']}, P3fix {c1['P3fix']}, P3all {c1['P3all']}  (T3: 52 / 208 / 248 / 260)")
    P(f"  W2: Fr {c2['Fr']}, Mo-Do {c2['MoDo']} (davon Futures-Tage 2026-04-04..06-28 Mo-Do {c24['MoDo']}, Fr {c24['Fr']}), "
      f"P3fix {c2['P3fix']}, P3all {c2['P3all']}  (T3: 52 / 159+48 / 247 / 259)")
    P(f"  P2'' woertlich (Mo-Do ohne Futures-Delivery) in W2: {c2['MoDo'] - c24['MoDo']} (T3: 159); in Zone K: 0 "
      f"(taegliche Futures seit 2026-04-04, DATENANNAHMEN 10) -> K-Kontrast nach DEC-103 E3 nicht definiert")
    # STRESS_ABS days (dates only)
    with open(os.path.join(REPO, "scinance3-impl/state/runs/stress_abs.json"), encoding="utf-8") as fh:
        days = [dt.date.fromisoformat(x) for x in json.load(fh)["days"]]
    wins = {"W1": W1, "W2": W2, "K_reg": (dt.date(2026, 10, 1), dt.date(2027, 12, 31)),
            "gap_2026Q3": (dt.date(2026, 7, 1), dt.date(2026, 9, 30)),
            "Vorfenster_2023-07..2024-06": (dt.date(2023, 7, 1), dt.date(2024, 6, 30))}
    st = {}
    for k, (a, b) in wins.items():
        hit = [d.isoformat() for d in days if a <= d <= b]
        st[k] = hit
        P(f"  STRESS_ABS in {k}: {len(hit)} {hit}")
    st["in_judging_windows"] = len(st["W1"]) + len(st["W2"]) + len(st["K_reg"])
    fri = [d for d in days if W1[0] <= d <= W2[1] and d.weekday() == 4]
    st["event_fridays_with_stress"] = [d.isoformat() for d in fri]
    P(f"  STRESS_ABS in den Urteilsfenstern: {st['in_judging_windows']} (Entwurf 3); Ereignis-Freitage darunter: "
      f"{st['event_fridays_with_stress']}")
    out["stress_abs"] = st
    OUT["calendar"] = out
    return out


# ---------------------------------------------------------------------------------------------------------------------
# (2) exact OBF alpha by recursive numerical integration (Armitage-McPherson-Rowe)
# ---------------------------------------------------------------------------------------------------------------------
def obf_alpha(C: float, t: list[float], ngrid: int = 2001, lo: float = -12.0) -> float:
    """P(B_k >= C sqrt(t_k) for some k) for Brownian motion B on information t (B-scale constant boundary C)."""
    t = list(t)
    b = [C * math.sqrt(tk) for tk in t]             # boundary on the B-scale: C (constant); on z: C/sqrt(t)
    # we work on the B-scale: boundary constant C at every look
    alpha = 0.0
    # density of B_1 restricted to continuation region (-inf, C)
    x = np.linspace(lo * math.sqrt(t[-1]), C, ngrid)
    f = norm.pdf(x, scale=math.sqrt(t[0]))
    alpha += float(norm.sf(C, scale=math.sqrt(t[0])))
    for k in range(1, len(t)):
        dtk = t[k] - t[k - 1]
        # P(cross at k) = int f(x) P(x + N(0,dt) >= C) dx
        cross = np.trapezoid(f * norm.sf(C - x, scale=math.sqrt(dtk)), x)
        alpha += float(cross)
        # new density on grid
        g = np.empty_like(x)
        dx = x[1] - x[0]
        # convolution f * N(0,dt) evaluated at grid points, truncated at C
        for i, xi in enumerate(x):
            g[i] = np.sum(f * norm.pdf(xi - x, scale=math.sqrt(dtk))) * dx
        f = g
    return alpha, b


def obf_section() -> dict:
    P("\n(2) O'Brien-Fleming: exaktes alpha der registrierten Grenze (rekursive Integration)")
    t_events = [130 / 170, 143 / 170, 156 / 170, 1.0]
    t_months = [30 / 39, 33 / 39, 36 / 39, 1.0]
    res = {}
    for lab, t in (("ereignisse_130_143_156_170", t_events), ("monate_30_33_36_39", t_months)):
        a, b = obf_alpha(C_B, t)
        zb = [C_B / math.sqrt(tk) for tk in t]
        res[lab] = {"t": t, "alpha_exact": a, "z_bounds": zb}
        P(f"  {lab}: t {[round(x, 4) for x in t]}, z-Grenzen {[round(z, 4) for z in zb]}, alpha exakt {a:.6f}")
    # solve C for alpha 0.0025 with event fractions
    lo, hi = 2.7, 3.1
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if obf_alpha(mid, t_events, ngrid=1201)[0] > 0.0025:
            lo = mid
        else:
            hi = mid
    res["C_B_fuer_0.0025_ereignisse"] = 0.5 * (lo + hi)
    P(f"  C_B fuer alpha 0,0025 bei Ereignis-Anteilen: {0.5 * (lo + hi):.4f} (registriert 2,886 aus Monats-Anteilen)")
    # t-boundaries: same per-look alpha with df = N_E - 1
    nE = [130, 143, 156, 170]
    tb = []
    for k, z in enumerate(res["ereignisse_130_143_156_170"]["z_bounds"]):
        a_k = float(norm.sf(z))
        tq = float(student_t.isf(a_k, nE[k] - 1))
        tb.append({"look": k + 1, "df": nE[k] - 1, "z": z, "t": tq, "ratio": tq / z})
    res["t_bounds"] = tb
    P("  t-artige Grenzen (df = N_E - 1, gleiches alpha je Blick): " +
      "; ".join(f"Blick {d['look']} z {d['z']:.3f} -> t {d['t']:.3f} (x{d['ratio']:.4f})" for d in tb))
    OUT["obf"] = res
    return res


# ---------------------------------------------------------------------------------------------------------------------
# (3) block model, own implementation
# ---------------------------------------------------------------------------------------------------------------------
def make_blocks(line: str = "central", k_placebo: str = "P2strich") -> dict:
    sd_e = SD_E if line == "central" else SD_E_S
    se1 = SE_W1 if line == "central" else SE_W1_S
    se2 = SE_W2 if line == "central" else SE_W2_S
    vE = C_E * sd_e ** 2                                   # effective per-event-day variance
    sig = {}
    for j in ("P2", "P3fix", "P3all"):
        a = (se1[j] ** 2 - vE / CNT_W1["E"]) * CNT_W1[j]
        b = (se2[j] ** 2 - vE / CNT_W2["E"]) * CNT_W2[j]
        sig[j] = {"W1": a, "W2": b, "used": 0.5 * (a + b), "agreement": a / b}
    E, P2, P3f, P3a, fixE, zone = [], [], [], [], [], []
    for q in range(4):                                     # W1
        E.append(13); P2.append(52); P3f.append(62); P3a.append(65); fixE.append(0); zone.append("V")
    w2e = [13, 13, 14, 12]
    for q in range(4):                                     # W2 (Q4: all Mo-Do are futures days)
        E.append(w2e[q]); P2.append(53 if q < 3 else 0); P3f.append(62 if q < 3 else 61)
        P3a.append(65 if q < 3 else 64); fixE.append(12 if q == 3 else 0); zone.append("V")
    for a, b in KQ:
        c = count_days(dt.date.fromisoformat(a), dt.date.fromisoformat(b))
        p2 = c["MoDo"] if k_placebo == "P2strich" else 0
        E.append(c["Fr"]); P2.append(p2); P3f.append(c["P3fix"]); P3a.append(c["P3all"])
        fixE.append(0 if p2 > 0 else c["Fr"]); zone.append("K")
    return {"vE": vE, "sig": {j: sig[j]["used"] for j in sig}, "sig_detail": sig, "E": np.array(E, float),
            "P": {"P2": np.array(P2, float), "P3fix": np.array(P3f, float), "P3all": np.array(P3a, float)},
            "fixE": np.array(fixE, float), "zone": zone}


class Paths:
    """Common random numbers: block sums of the event noise and of each placebo noise (independent placebos)."""

    def __init__(self, blk: dict, n: int, seed: int):
        rng = np.random.default_rng(seed)
        nb = len(blk["E"])
        self.blk = blk
        self.sE = rng.standard_normal((n, nb)) * np.sqrt(blk["vE"] * blk["E"])[None, :]
        self.sP = {}
        for j, cnt in blk["P"].items():
            self.sP[j] = rng.standard_normal((n, nb)) * np.sqrt(blk["sig"][j] * cnt)[None, :]
        self.eps = rng.standard_normal((n, 4))
        self.n = n


def run_rule(ps: Paths, mu: np.ndarray, *, conds=("P2", "P3fix", "P3all"), null_cond=True, stab=True, futility=True,
             bounds=None, side_bounds=None, j_mode="4q", t_bounds=False) -> dict:
    """One pass of the whole rule.  mu: effect per block (bp, event-day scale, positive = registered direction).
    bounds: per-look boundary for the primary z (default OBF by event information); side_bounds: for P3fix/P3all
    (default same as primary); j_mode: '4q' = last four data quarters, '12m' = last 12 calendar months."""
    blk, n = ps.blk, ps.n
    E, Pc, fixE = blk["E"], blk["P"], blk["fixE"]
    effE = ps.sE + (mu * E)[None, :]
    info_full = E[:LOOKS[-1]].sum()
    nE_look = [E[:u].sum() for u in LOOKS]
    if bounds is None:
        bounds = [C_B / math.sqrt(ne / info_full) for ne in nE_look]
        if t_bounds:
            bounds = [float(student_t.isf(norm.sf(z), int(ne) - 1)) for z, ne in zip(bounds, nE_look)]
    if side_bounds is None:
        side_bounds = bounds
    alive = np.ones(n, bool)
    pass_at = np.zeros((n, 4), bool)
    fail_stab = np.zeros(n, bool)
    fut = np.zeros(n, bool)
    for k, u in enumerate(LOOKS):
        nE = E[:u].sum()
        Ebar = effE[:, :u].sum(1) / nE
        ok = np.ones(n, bool)
        zP = None
        for j in conds:
            nP = Pc[j][:u].sum()
            D = Ebar - ps.sP[j][:, :u].sum(1) / nP
            se = math.sqrt(blk["vE"] / nE + blk["sig"][j] / nP)
            z = D / se
            if j == "P2":
                zP, D2, se2 = z, D, se
                ok &= z >= bounds[k]
            else:
                ok &= z >= side_bounds[k]
        if null_cond:
            nfix = fixE[:u].sum()
            kappa = 1.0 - nfix / nE
            mu_eff = (mu[:u] * E[:u]).sum() / nE
            csd = CENTRE_SD_W2 * 52.0 / nE if nfix > 0 else 0.0
            rho = math.sqrt(max(0.0, 1.0 - (csd / se2) ** 2))
            y = kappa * mu_eff + rho * (D2 - mu_eff) + math.sqrt(1 - rho ** 2) * se2 * ps.eps[:, k]
            ok &= y >= TAU95 * se2
        cross = alive & (zP >= bounds[k])
        if stab:
            if j_mode == "4q":
                jb = list(range(u - 4, u))
            else:   # last 12 calendar months of data before the look: look1 W2Q4+KQ1+KQ2, look2 KQ1..KQ3, then 4 K quarters
                jb = {10: [7, 8, 9], 11: [8, 9, 10], 12: [8, 9, 10, 11], 13: [9, 10, 11, 12]}[u]
            ab = [i for i in range(u) if i not in jb]
            nEJ, nEA = E[jb].sum(), E[ab].sum()
            nPJ, nPA = Pc["P2"][jb].sum(), Pc["P2"][ab].sum()
            xJ = effE[:, jb].sum(1) / nEJ - ps.sP["P2"][:, jb].sum(1) / nPJ
            xA = effE[:, ab].sum(1) / nEA - ps.sP["P2"][:, ab].sum(1) / nPA
            seD = math.sqrt(blk["vE"] / nEJ + blk["sig"]["P2"] / nPJ + blk["vE"] / nEA + blk["sig"]["P2"] / nPA)
            rej = cross & ((xJ - xA) / seD < -Z_STAB)
            fail_stab |= rej
            alive &= ~rej
            cross &= ~rej
        hit = cross & ok
        pass_at[:, k] = hit
        alive &= ~hit
        if futility and k < 3:
            f = alive & (zP < 0)
            fut |= f
            alive &= ~f
    anyp = pass_at.any(1)
    return {"p_pass": float(anyp.mean()), "by_look": [float(pass_at[:, :k + 1].any(1).mean()) for k in range(4)],
            "at_look": [float(pass_at[:, k].mean()) for k in range(4)], "p_fail_stab": float(fail_stab.mean()),
            "p_futility": float(fut.mean())}


def solve_mde(ps: Paths, target: float, shape, look: int | None = None, lo=0.0, hi=90.0, **kw) -> float:
    def f(m):
        r = run_rule(ps, shape(m), **kw)
        return (r["p_pass"] if look is None else r["by_look"][look]) - target
    if f(hi) < 0:
        return math.inf
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 0.004:
            break
    return 0.5 * (lo + hi)


def se_pooled(blk, u, j):
    return math.sqrt(blk["vE"] / blk["E"][:u].sum() + blk["sig"][j] / blk["P"][j][:u].sum())


def mc_section() -> dict:
    P("\n(3) Monte Carlo der Gesamtregel (eigene Implementierung, Seed 7, 400.000 Pfade)")
    blk = make_blocks("central")
    P("  Placebo-Tagesvarianz aus W1 / W2 (Uebereinstimmung W1/W2): " +
      ", ".join(f"{j} {d['used']:.0f} (W1/W2 {d['agreement']:.3f})" for j, d in blk["sig_detail"].items()))
    for k, u in enumerate(LOOKS):
        P(f"  Blick {k + 1} {LOOK_DATES[k]}: N_E {int(blk['E'][:u].sum())}, N_P2 {int(blk['P']['P2'][:u].sum())}, "
          f"SE P2 {se_pooled(blk, u, 'P2'):.3f}, P3fix {se_pooled(blk, u, 'P3fix'):.3f}, P3all {se_pooled(blk, u, 'P3all'):.3f}")
    ps = Paths(blk, N, SEED)
    nb = len(blk["E"])
    homog = lambda m: np.full(nb, m)
    onlyV = lambda m: np.array([m] * 8 + [0.0] * 5)
    onlyW1 = lambda m: np.array([m] * 4 + [0.0] * 9)
    older1 = lambda m: np.array([m] * 6 + [0.0] * 7)        # older part as defined at look 1 (W1 + W2Q1-Q2)
    FULL = dict(conds=("P2", "P3fix", "P3all"), null_cond=True, stab=True, futility=True)
    res = {}
    # alpha decomposition
    a_prim = run_rule(ps, homog(0.0), conds=("P2",), null_cond=False, stab=True, futility=True)
    a_prim_none = run_rule(ps, homog(0.0), conds=("P2",), null_cond=False, stab=False, futility=False)
    a_p3f = run_rule(ps, homog(0.0), conds=("P2", "P3fix"), null_cond=False, stab=True, futility=True)
    a_all = run_rule(ps, homog(0.0), conds=("P2", "P3fix", "P3all"), null_cond=False, stab=True, futility=True)
    a_full = run_rule(ps, homog(0.0), **FULL)
    res["alpha"] = {"obf_plan_ohne_alles": a_prim_none["p_pass"], "primaer_stab_futility": a_prim["p_pass"],
                    "plus_P3fix": a_p3f["p_pass"], "plus_P3all": a_all["p_pass"], "plus_null": a_full["p_pass"],
                    "mit_gate": a_full["p_pass"] * GATE, "at_look": [x * GATE for x in a_full["at_look"]],
                    "futility_H0": a_full["p_futility"]}
    P(f"  alpha: OBF-Plan allein {a_prim_none['p_pass']:.5f}; + Stabilitaetstest + Futility {a_prim['p_pass']:.5f}; "
      f"+ P3fix (OBF-Grenze) {a_p3f['p_pass']:.5f}; + P3all {a_all['p_pass']:.5f}; + Null {a_full['p_pass']:.5f}; "
      f"x Gate {a_full['p_pass'] * GATE:.5f}  (Entwurf: 0,00251 / 0,00246 / - / - / 0,00037 / 0,00033)")
    P(f"  Futility-Stopp unter H0 {a_full['p_futility']:.4f} (Entwurf 0,580)")
    # power at SESOI, MDE of the plan and per look
    r22 = run_rule(ps, homog(SESOI), **FULL)
    mde_plan = solve_mde(ps, 0.80 / GATE, homog, **FULL)
    mde_look = [solve_mde(ps, 0.80 / GATE, homog, look=k, hi=130.0, **FULL) for k in range(4)]
    r_mde = run_rule(ps, homog(mde_plan), **FULL)
    res["power"] = {"p_pass_22": r22["p_pass"] * GATE, "by_look_22": [x * GATE for x in r22["by_look"]],
                    "fail_stab_22": r22["p_fail_stab"], "mde80_plan": mde_plan, "mde80_by_look": mde_look,
                    "p_pass_at_mde": r_mde["p_pass"] * GATE}
    P(f"  P(PASS | 22 bp) {r22['p_pass'] * GATE:.4f}, kumuliert {[round(x * GATE, 3) for x in r22['by_look']]}, "
      f"Stabilitaets-FAIL {r22['p_fail_stab']:.4f}  (Entwurf 0,8421; 0,713/0,784/0,822/0,842)")
    P(f"  MDE80 Plan {mde_plan:.2f} bp (Entwurf 19,50); je Blick kumuliert {[round(m, 2) for m in mde_look]} "
      f"(Entwurf 24,56 / 22,60 / 20,96 / 19,50); Kontrolle P(PASS | MDE) {r_mde['p_pass'] * GATE:.4f}")
    for m in (5.0, 16.5, 25.0):
        r = run_rule(ps, homog(m), **FULL)
        res["power"][f"p_pass_{m}"] = r["p_pass"] * GATE
        P(f"  P(PASS | {m} bp) {r['p_pass'] * GATE:.4f}")
    # protection line variants
    prot = {}
    for lab, shape, mult in (("nur_V_1MDE", onlyV, 1.0), ("nur_V_2MDE", onlyV, 2.0), ("nur_W1_1MDE", onlyW1, 1.0),
                             ("nur_aelterer_Teil_Blick1_1MDE", older1, 1.0), ("nur_aelterer_Teil_Blick1_2MDE", older1, 2.0)):
        r = run_rule(ps, shape(mult * mde_plan), **FULL)
        prot[lab] = {"p_pass": r["p_pass"] * GATE, "by_look": [x * GATE for x in r["by_look"]],
                     "veraltet_3_4": (r["at_look"][2] + r["at_look"][3]) * GATE, "fail_stab": r["p_fail_stab"]}
        P(f"  Schutzzeile {lab}: P(PASS) {r['p_pass'] * GATE:.4f}, kumuliert {[round(x * GATE, 3) for x in r['by_look']]}, "
          f"veraltet (Blicke 3-4) {(r['at_look'][2] + r['at_look'][3]) * GATE:.4f}, Stab-FAIL {r['p_fail_stab']:.4f}")
    r_ns = run_rule(ps, onlyV(mde_plan), conds=("P2", "P3fix", "P3all"), null_cond=True, stab=False, futility=True)
    prot["nur_V_1MDE_ohne_stab"] = r_ns["p_pass"] * GATE
    P(f"  nur V 1 MDE ohne Stabilitaetstest: {r_ns['p_pass'] * GATE:.4f} (Entwurf 0,405)")
    res["protection"] = prot
    # strictness chain (Grundfassung as in the draft: primary alone, same rule and plan, no gate)
    base = solve_mde(ps, 0.80, homog, conds=("P2",), null_cond=False, stab=True, futility=True)
    s1 = solve_mde(ps, 0.80, homog, conds=("P2", "P3fix"), null_cond=False, stab=True, futility=True)
    s2 = solve_mde(ps, 0.80, homog, conds=("P2", "P3fix", "P3all"), null_cond=False, stab=True, futility=True)
    s3 = solve_mde(ps, 0.80, homog, conds=("P2", "P3fix", "P3all"), null_cond=True, stab=True, futility=True)
    chain = {"grundfassung_plan_primaer": base, "plus_P3fix": s1, "plus_P3all": s2, "plus_null": s3, "plus_gate": mde_plan,
             "quotient_entwurf_definition": mde_plan / base}
    P(f"  Strenge-Kette (Entwurfs-Grundfassung): {base:.2f} -> {s1:.2f} (x{s1 / base:.4f}) -> {s2:.2f} (x{s2 / s1:.4f}) -> "
      f"{s3:.2f} (x{s3 / s2:.4f}) -> {mde_plan:.2f} (x{mde_plan / s3:.4f}); Quotient {mde_plan / base:.4f} (Entwurf 1,2548)")
    # alternative Grundfassungen: fixed one-look test, primary alone, central nuisance, alpha 0.0025, same data
    se39 = se_pooled(blk, 13, "P2")
    se30 = se_pooled(blk, 10, "P2")
    g_fix39 = (Z_POOL + 0.8416) * se39
    g_fix30 = (Z_POOL + 0.8416) * se30
    g_fix39_stab = (Z_POOL + float(norm.ppf(0.80 / 0.95))) * se39
    # GSD plan, primary alone, without stability test and futility (what DEC-104 E2 "gepoolt" alone would be)
    base_nostab = solve_mde(ps, 0.80, homog, conds=("P2",), null_cond=False, stab=False, futility=False)
    chain.update({"grundfassung_fest_39M_primaer_ohne_stab": g_fix39, "quotient_fest_39M": mde_plan / g_fix39,
                  "grundfassung_fest_30M_primaer_ohne_stab": g_fix30, "quotient_fest_30M_blick1": mde_look[0] / g_fix30,
                  "grundfassung_fest_39M_primaer_mit_q095": g_fix39_stab, "quotient_fest_39M_q095": mde_plan / g_fix39_stab,
                  "grundfassung_plan_primaer_ohne_stab_futility": base_nostab, "quotient_plan_ohne_stab": mde_plan / base_nostab})
    P(f"  Alternative Grundfassungen: fester Ein-Blick-Test 39 Monate, Primaer allein, ohne Stabilitaetstest: {g_fix39:.2f} bp -> "
      f"Quotient {mde_plan / g_fix39:.4f}; mit q 0,95: {g_fix39_stab:.2f} -> {mde_plan / g_fix39_stab:.4f}; "
      f"Plan Primaer allein ohne Stabilitaetstest/Futility: {base_nostab:.2f} -> {mde_plan / base_nostab:.4f}; "
      f"am Blick 1 gegen festen Test 30 Monate ({g_fix30:.2f}): {mde_look[0] / g_fix30:.4f}")
    res["strictness"] = chain
    # product double statement at look 1
    u = 10
    nE = blk["E"][:u].sum()
    z1 = C_B / math.sqrt(nE / blk["E"].sum())
    ses = {j: se_pooled(blk, u, j) for j in ("P2", "P3fix", "P3all")}
    kappa1 = 1 - blk["fixE"][:u].sum() / nE

    def prod_pow(m):
        p = 1.0
        for j in ses:
            p *= float(norm.sf(z1 - m / ses[j]))
        return p * float(norm.sf(TAU95 - kappa1 * m / ses["P2"])) * 0.95 * GATE
    lo, hi = 0.0, 90.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if prod_pow(mid) < 0.80:
            lo = mid
        else:
            hi = mid
    res["doppelausweis_blick1"] = {"produkt": 0.5 * (lo + hi), "exakt": mde_look[0]}
    P(f"  Doppelausweis Blick 1: Produkt {0.5 * (lo + hi):.2f} gegen exakt {mde_look[0]:.2f} (Entwurf 25,10 / 24,56)")
    OUT["mc"] = res
    return blk, ps, res, mde_plan


# ---------------------------------------------------------------------------------------------------------------------
# (4) probes: hidden strictness / leniency
# ---------------------------------------------------------------------------------------------------------------------
def probes(blk, ps, mde_plan: float) -> dict:
    P("\n(4) Sonden")
    nb = len(blk["E"])
    homog = lambda m: np.full(nb, m)
    onlyV = lambda m: np.array([m] * 8 + [0.0] * 5)
    FULL = dict(conds=("P2", "P3fix", "P3all"), null_cond=True, stab=True, futility=True)
    res = {}
    # (a) G-03: side conditions at fixed 2.8070 instead of the OBF boundary
    fixed = [Z_POOL] * 4
    a = run_rule(ps, homog(0.0), side_bounds=fixed, **FULL)
    m = solve_mde(ps, 0.80 / GATE, homog, side_bounds=fixed, **FULL)
    r22 = run_rule(ps, homog(SESOI), side_bounds=fixed, **FULL)
    res["G03_nebenbed_fest_2.807"] = {"alpha": a["p_pass"] * GATE, "mde80": m, "p_pass_22": r22["p_pass"] * GATE}
    P(f"  (a) G-03 Nebenbedingungen fest 2,8070: alpha_eff {a['p_pass'] * GATE:.5f}, MDE80 {m:.2f} bp, P(PASS | 22) "
      f"{r22['p_pass'] * GATE:.4f}  (Plan: 0,00033 / 19,50 / 0,842)")
    # (a2) side conditions at alpha 0.05 (z 1.6449) - "Placebo as screen" reading (not decided; for the record)
    scr = [Z_STAB] * 4
    a2 = run_rule(ps, homog(0.0), side_bounds=scr, **FULL)
    m2 = solve_mde(ps, 0.80 / GATE, homog, side_bounds=scr, **FULL)
    res["nebenbed_1.645_nur_Vergleich"] = {"alpha": a2["p_pass"] * GATE, "mde80": m2}
    P(f"  (a2) nur Vergleich, nicht beschlossen - Nebenbedingungen bei 1,6449: alpha_eff {a2['p_pass'] * GATE:.5f}, MDE80 {m2:.2f} bp")
    # (b) t-boundaries (df = N_E - 1) instead of z for all conditions
    at = run_rule(ps, homog(0.0), t_bounds=True, **FULL)
    mt = solve_mde(ps, 0.80 / GATE, homog, t_bounds=True, **FULL)
    r22t = run_rule(ps, homog(SESOI), t_bounds=True, **FULL)
    res["t_grenzen"] = {"alpha": at["p_pass"] * GATE, "mde80": mt, "p_pass_22": r22t["p_pass"] * GATE}
    P(f"  (b) t-artige Grenzen (df N_E - 1) statt z: alpha_eff {at['p_pass'] * GATE:.5f}, MDE80 {mt:.2f} bp "
      f"(+{100 * (mt / mde_plan - 1):.1f} %), P(PASS | 22) {r22t['p_pass'] * GATE:.4f}")
    # (c) youngest part: last 12 calendar months instead of last four data quarters
    a12 = run_rule(ps, homog(0.0), j_mode="12m", **FULL)
    m12 = solve_mde(ps, 0.80 / GATE, homog, j_mode="12m", **FULL)
    r22_12 = run_rule(ps, homog(SESOI), j_mode="12m", **FULL)
    pv12 = run_rule(ps, onlyV(mde_plan), j_mode="12m", **FULL)
    pv4 = run_rule(ps, onlyV(mde_plan), **FULL)
    res["J_12_kalendermonate"] = {"alpha": a12["p_pass"] * GATE, "mde80": m12, "p_pass_22": r22_12["p_pass"] * GATE,
                                  "schutz_nur_V": pv12["p_pass"] * GATE, "schutz_nur_V_4q": pv4["p_pass"] * GATE,
                                  "fail_stab_22": r22_12["p_fail_stab"]}
    P(f"  (c) juengster Teil = letzte 12 Kalendermonate (Blick 1: W2Q4 + KQ1 + KQ2, 39 Freitage) statt vier Datenquartale: "
      f"alpha_eff {a12['p_pass'] * GATE:.5f}, MDE80 {m12:.2f} bp, P(PASS | 22) {r22_12['p_pass'] * GATE:.4f} "
      f"(Stab-FAIL {r22_12['p_fail_stab']:.4f}), Schutzzeile nur V {pv12['p_pass'] * GATE:.4f} gegen {pv4['p_pass'] * GATE:.4f}")
    # (d) placebo dilution in zone K: P2' (all Mo-Do incl. daily futures deliveries) carries a fraction f of the effect
    dil = {}
    for f in (0.0, 0.25, 0.5, 0.75):
        mu = np.array([SESOI] * 8 + [SESOI * (1 - f)] * 5)
        r = run_rule(ps, mu, **FULL)
        dil[str(f)] = {"p_pass_22": r["p_pass"] * GATE, "fail_stab": r["p_fail_stab"], "by_look": [x * GATE for x in r["by_look"]]}
        P(f"  (d) Verduennung des K-Kontrasts (P2' traegt Anteil f {f:.2f} des Effekts): P(PASS | 22 in V) {r['p_pass'] * GATE:.4f}, "
          f"Stabilitaets-FAIL {r['p_fail_stab']:.4f}, kumuliert {[round(x * GATE, 3) for x in r['by_look']]}")
    res["verduennung_K"] = dil
    # (e) literal P2'' in zone K: no placebo days -> K Fridays all fixed; contrast in K undefined; pooled test = V only
    blkV = make_blocks("central", k_placebo="P2ss_literal")
    res["P2ss_woertlich_K"] = {"P2_days_K": float(blkV["P"]["P2"][8:].sum()), "fixed_fridays_K": float(blkV["fixE"][8:].sum()),
                              "kappa_blick4": 1 - blkV["fixE"].sum() / blkV["E"].sum()}
    P(f"  (e) P2'' woertlich in K: P2-Tage in K {res['P2ss_woertlich_K']['P2_days_K']:.0f}, feste Freitage K "
      f"{res['P2ss_woertlich_K']['fixed_fridays_K']:.0f}, kappa am Endblick {res['P2ss_woertlich_K']['kappa_blick4']:.3f} -> "
      f"K liefert keinen Placebo-Kontrast; Stabilitaetstest (juengster Teil ohne Placebo) nicht definierbar")
    # (f) stress line
    blkS = make_blocks("stress")
    psS = Paths(blkS, N, SEED + 11)
    aS = run_rule(psS, homog(0.0), **FULL)
    mS = solve_mde(psS, 0.80 / GATE, homog, **FULL)
    r22S = run_rule(psS, homog(SESOI), **FULL)
    res["stress"] = {"alpha": aS["p_pass"] * GATE, "mde80": mS, "p_pass_22": r22S["p_pass"] * GATE,
                     "by_look_22": [x * GATE for x in r22S["by_look"]]}
    P(f"  (f) Stress (SE 8,52): alpha_eff {aS['p_pass'] * GATE:.5f}, MDE80 {mS:.2f} bp (Entwurf 21,46), P(PASS | 22) "
      f"{r22S['p_pass'] * GATE:.4f} (Entwurf 0,812), kumuliert {[round(x * GATE, 3) for x in r22S['by_look']]}")
    # (g) V3 pre-window hint (published SE 5.31 / recomputed 5.51) - planning sensitivity, arithmetic only
    se_v3 = 5.51
    scale = se_v3 / 7.58
    res["vorfenster_V3_skaliert"] = {"se": se_v3, "mde80_plan_skaliert": mde_plan * scale,
                                     "hinweis": "Skalierung der Plan-MDE mit SE-Verhaeltnis (alle Terme proportional)"}
    P(f"  (g) Vorfenster-Hinweis: bei SE 5,51 (V3 mit W2-N) skaliert die Plan-MDE80 auf {mde_plan * scale:.2f} bp "
      f"(nur Planungsgroesse; alpha unveraendert)")
    # (h) positive-control criterion
    se_bin = math.sqrt(0.8 * 0.2 / 200)
    res["pk"] = {"kriterium": 0.80 - 2.3263 * se_bin, "P_fail_pk_bei_power_0.80": float(norm.cdf(-2.3263)),
                 "P_fail_pk_bei_power_0.75": float(norm.cdf((0.80 - 2.3263 * se_bin - 0.75) / math.sqrt(0.75 * 0.25 / 200)))}
    P(f"  (h) PK-Kriterium 0,80 - 2,3263 x {se_bin:.4f} = {res['pk']['kriterium']:.4f}; P(NICHT BESTANDEN | wahre Quote 0,80) "
      f"{res['pk']['P_fail_pk_bei_power_0.80']:.3f}; bei wahrer Quote 0,75: {res['pk']['P_fail_pk_bei_power_0.75']:.3f}")
    OUT["probes"] = res
    return res


# ---------------------------------------------------------------------------------------------------------------------
# (5) fixed-rule MDE80 (R5 convention) reproduction
# ---------------------------------------------------------------------------------------------------------------------
def fixed_rule() -> dict:
    P("\n(5) Feste Ein-Blick-Regel (c): MDE80 = (z_krit + Phi^-1(0,80/(q g))) SE_12 sqrt(12/T)")
    fac = Z_POOL + float(norm.ppf(0.80 / (0.95 * GATE)))
    res = {"faktor": fac}
    for se in (7.58, 7.34, 8.52):
        row = {str(T): fac * se * math.sqrt(12 / T) for T in (24, 27, 30, 33, 36, 39)}
        row["T22"] = 12 * (fac * se / SESOI) ** 2
        row["30x1.03"] = row["30"] * math.sqrt(1.03)
        row["30xRmax1.084"] = row["30"] * math.sqrt(1.08418)
        res[str(se)] = row
        P(f"  SE {se}: " + ", ".join(f"T{T} {row[str(T)]:.2f}" for T in (24, 27, 30, 33, 36, 39)) +
          f"; 22 bp ab {row['T22']:.2f} Monaten; T30 x sqrt(1,03) {row['30x1.03']:.2f}; T30 x sqrt(R_max 1,084) {row['30xRmax1.084']:.2f}")
    P(f"  MDE-Faktor {fac:.4f} (Entwurf 4,3062); DEC-107 N1 (1): 23,08 / 21,76 / 20,64 / 26,4 Monate / 20,95")
    OUT["fixed_rule"] = res
    return res


def main() -> None:
    t0 = time.time()
    P(f"Review A2-Registrierungsentwurf 3.1 - eigene Gegenrechnung, Seed {SEED}, {N} Pfade")
    calendar()
    obf_section()
    blk, ps, _, mde_plan = mc_section()
    probes(blk, ps, mde_plan)
    fixed_rule()
    OUT["meta"]["seconds"] = time.time() - t0
    P(f"\nLaufzeit {time.time() - t0:.1f} s")
    txt = "\n".join(LINES) + "\n"
    with open(os.path.join(HERE, "review_a2_calc.out"), "w", encoding="utf-8") as fh:
        fh.write(txt)
    with open(os.path.join(HERE, "review_a2_calc.json"), "w", encoding="utf-8") as fh:
        json.dump(OUT, fh, indent=1, sort_keys=True, default=str)
    print(txt)


if __name__ == "__main__":
    main()
