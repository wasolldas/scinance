#!/usr/bin/env python3
"""A2 registration draft under Constitution 3.1 (variant (c) + BE-04): operating characteristic of the whole rule.

Role "Herleitung", 2026-11-04.  Deterministic (fixed seeds), numpy/scipy only, no market data, no sealed file, no
network.  Every input number carries its source in ``INPUTS`` (file / table row); the model is the Gaussian contrast
model of the A2 dossier (NULL_SIMULATION_A2.md T3, feasibility31.conjunction.shared_term_spec) extended to a sequence
of quarterly blocks (zone V = W1/W2, zone K from 2026-10-01) with O'Brien-Fleming looks, the registered stability test
(each efficacy stop, terminal), futility Z < 0 at looks 1-3 and the Gate-(4) factor as an independent Bernoulli.

Outputs: ``a2_reg_calc.json`` (all numbers) and ``a2_reg_calc.out`` (text); run with ``python3 -I a2_reg_calc.py``.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
from scipy.stats import norm, t as student_t

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "/home/user/scinance"
SEED = 20261104
N_PATHS = 300_000

# --------------------------------------------------------------------------------------------------------------------
# inputs (each with its source; no market data: only published nuisance, counts and calendar arithmetic)
# --------------------------------------------------------------------------------------------------------------------
INPUTS = {
    "z_pool": {"value": float(norm.isf(0.0025)), "source": "DEC-104 E2 / VR-b14: alpha 0,0025 einseitig, z_krit 2,8070"},
    "alpha_stab": {"value": 0.05, "source": "DEC-107 (1) (a): Welch-t einseitig 0,05 gegen Abfall"},
    "q_one_look": {"value": 0.95, "source": "DEC-107 (1) (d): Kostenquote q = 1 - alpha_stab bei einem Blick"},
    "gate4": {"value": 0.9025, "source": "NULL_SIMULATION_A2.md 5.2: Gate (4) als Faktor 0,95^2 (vorlaeufig, UNBELEGT); VR-e07"},
    "tau95": {"value": 1.6553, "source": "NULL_SIMULATION_A2.md 5 (Transfer): tau95 = 1,6553 (MC-Maximum; exakt 1,6533)"},
    "sesoi_bp": {"value": 22.0, "source": "KRITIK_PRD.md K-10 Tabelle Zeile A2: 2 x 11 bp Taker = 22 bp (Maker 2 x 5,4 = 10,8 bp)"},
    "prior_span_bp": {"value": [5.0, 25.0], "source": "NULL_SIMULATION_A2.md T6 Prior-Gitter 5,0..25,0 bp; feasibility/A2.yaml prior.sensitivity_span"},
    "prior_nominal_bp": {"value": 16.5, "source": "NULL_SIMULATION_A2.md T6 Referenzzeile 16,5 bp [sek]; UNBELEGT"},
    "se12_central_W2": {"value": 7.58, "source": "NULL_SIMULATION_A2.md T3 'W2 zentral': SE_bind P2'' 7,58 (Platzhalter fuer das Vorfenster, DEC-107 N1 (2))"},
    "se12_central_W1": {"value": 7.34, "source": "NULL_SIMULATION_A2.md T3 'W1 zentral': SE_bind P2'' 7,34 (Sensitivitaet)"},
    "se12_stress_W2": {"value": 8.52, "source": "NULL_SIMULATION_A2.md T3 'W2 stress': SE_bind P2'' 8,52 (Sensitivitaet, BE-04)"},
    "event_sd_c": {"value": {"central": [43.83, 1.1491], "stress": [49.37, 1.1491]},
                   "source": "NULL_SIMULATION_A2.md T2 VP / V1 P2ss: SD Klasse E 43,83 / 49,37; c_bind Freitag 1,1491 (Teil B Reproduktion)"},
    "se_W1": {"value": {"central": {"P2": 7.34, "P3fix": 7.93, "P3all": 6.56}, "stress": {"P2": 8.25, "P3fix": 8.66, "P3all": 7.39}},
              "source": "NULL_SIMULATION_A2.md T3 W1 zentral / stress"},
    "se_W2": {"value": {"central": {"P2": 7.58, "P3fix": 7.93, "P3all": 6.56}, "stress": {"P2": 8.52, "P3fix": 8.67, "P3all": 7.39}},
              "source": "NULL_SIMULATION_A2.md T3 W2 zentral / stress"},
    "null_W1": {"value": {"central": {"sd": 6.70, "centre_sd": 0.23}, "stress": {"sd": 7.53, "centre_sd": 0.26}},
                "source": "NULL_SIMULATION_A2.md T3 W1: Null-SD, SD Null-Verschiebung"},
    "null_W2": {"value": {"central": {"sd": 6.24, "centre_sd": 2.97}, "stress": {"sd": 7.01, "centre_sd": 3.34}},
                "source": "NULL_SIMULATION_A2.md T3 W2: Null-SD, SD Null-Verschiebung"},
    "counts_W1": {"value": {"E": 52, "P2": 208, "P3fix": 248, "P3all": 260}, "source": "NULL_SIMULATION_A2.md T3 W1"},
    "counts_W2": {"value": {"E": 52, "P2": 159, "P3fix": 247, "P3all": 259, "fixed_fridays": 12},
                  "source": "NULL_SIMULATION_A2.md T3 W2; 5.3 Befund 2 (12 feste Freitage 2026-04-10..06-26)"},
    "c_overlap": {"value": 1.3177, "source": "NULL_SIMULATION_A2.md T2 Kopf: c_bind Mo-Do 1,3177"},
    "obf_C_B": {"value": 2.886, "source": "stab_results.json s4b_blickplaene 'V24+K_30_33_36_39'.C_B_skala (exakte Gitterintegration)"},
    "q_plan_each_term": {"value": 0.963851, "source": "stab_results.json s4b_blickplaene 'V24+K_30_33_36_39'.each_term.q"},
    "R_max_plan_each_term": {"value": 1.08418, "source": "stab_results.json s4b 'V24+K_30_33_36_39'.each_term.R_max"},
    "nur_V_1MDE_plan": {"value": {"P_PASS": 0.298684, "veraltet": 0.04952},
                        "source": "stab_results.json s4b 'V24+K_30_33_36_39'.each_term.nur_V_teil_1MDE (ohne Konjunktion, ohne Gate)"},
    "oc_s0_r05": {"value": {"PASS_nur_aelter_1MDE": 0.0729293, "PASS_nur_aelter_2MDE": 0.0127842},
                  "source": "stab_results.json s0_reproduktion_oc r0.500 (ein Blick, Primaerstatistik allein)"},
    "V3_prewindow": {"value": {"E_sd": 32.26, "P_sd": 29.83, "n_E": 53, "n_P": 209, "se_analytic": 5.31, "null_sd": 4.51},
                     "source": "NULL_SIMULATION_A2.md T2 Zeile V3_2023-06..2024-05 P2ss (einzige veroeffentlichte 12-Monats-Vorfensterzeile nahe 2023-07..2024-06)"},
    "outlier_days": {"value": ["2020-08-27", "2024-08-19"], "source": "DEC-103 E1: Options-Delivery > 60 s"},
    "daily_futures_from": {"value": "2026-04-04", "source": "DATENANNAHMEN_REGISTER Nr. 10; KONTO_INVENTAR O-052"},
}

Z_POOL = INPUTS["z_pool"]["value"]
Z_STAB = float(norm.isf(INPUTS["alpha_stab"]["value"]))
Q1 = INPUTS["q_one_look"]["value"]
G = INPUTS["gate4"]["value"]
TAU95 = INPUTS["tau95"]["value"]
SESOI = INPUTS["sesoi_bp"]["value"]
C_B = INPUTS["obf_C_B"]["value"]

# --------------------------------------------------------------------------------------------------------------------
# calendar (pure arithmetic, no market data)
# --------------------------------------------------------------------------------------------------------------------
def daterange(a: dt.date, b: dt.date):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


def month_end_friday(d: dt.date) -> bool:
    if d.weekday() != 4:
        return False
    nxt = d + dt.timedelta(days=7)
    return nxt.month != d.month


def quarter_counts(a: dt.date, b: dt.date) -> dict:
    out = {"E": 0, "MoDo": 0, "P3fix": 0, "P3all": 0}
    outl = {dt.date.fromisoformat(x) for x in INPUTS["outlier_days"]["value"]}
    for d in daterange(a, b):
        if d in outl:
            continue
        wd = d.weekday()
        if wd == 4:
            out["E"] += 1
        if wd <= 3:
            out["MoDo"] += 1
        if wd <= 4:
            out["P3all"] += 1
            if not month_end_friday(d):
                out["P3fix"] += 1
    return out


K_QUARTERS = [(dt.date(2026, 10, 1), dt.date(2026, 12, 31)), (dt.date(2027, 1, 1), dt.date(2027, 3, 31)),
              (dt.date(2027, 4, 1), dt.date(2027, 6, 30)), (dt.date(2027, 7, 1), dt.date(2027, 9, 30)),
              (dt.date(2027, 10, 1), dt.date(2027, 12, 31))]
LOOK_DATES = [dt.date(2027, 4, 1), dt.date(2027, 7, 1), dt.date(2027, 10, 1), dt.date(2028, 1, 1)]
LOOK_MONTHS = [30, 33, 36, 39]

# --------------------------------------------------------------------------------------------------------------------
# block model
# --------------------------------------------------------------------------------------------------------------------
def build_blocks(line: str, k_placebo: str = "P2_all_modo") -> list[dict]:
    """13 quarterly blocks: W1 Q1..Q4, W2 Q1..Q4, K Q1..Q5.  Each block: counts and effective per-day variances."""
    e_sd, e_c = INPUTS["event_sd_c"]["value"][line]
    var_e_day = e_c * e_sd ** 2                      # effective per-event-day variance (c inside)
    blocks = []
    # effective per-placebo-day variance from the published window SEs (sigma_j^2 = (SE_j^2 - Var(Ebar)) * n_j)
    def sig2(se: float, n_p: int, n_e: int) -> float:
        return (se ** 2 - var_e_day / n_e) * n_p
    cw1, cw2 = INPUTS["counts_W1"]["value"], INPUTS["counts_W2"]["value"]
    s1, s2 = INPUTS["se_W1"]["value"][line], INPUTS["se_W2"]["value"][line]
    sig = {}
    for j in ("P2", "P3fix", "P3all"):
        a = sig2(s1[j], cw1[j], cw1["E"])
        b = sig2(s2[j], cw2[j], cw2["E"])
        sig[j] = 0.5 * (a + b)                        # W1 and W2 agree to < 1 % (checked in the output)
    # W1: four quarters of 13 Fridays, 52 P2'' days each
    for q in range(4):
        blocks.append({"name": f"W1Q{q + 1}", "zone": "V", "E": 13, "fixedE": 0, "P2": 52, "P3fix": 62, "P3all": 65})
    # W2: Q1..Q3 permutable, Q4 (2026-04..06) all Mo-Do are futures days: P2'' empty, 12 fixed Fridays (F-1)
    w2e = [13, 13, 14, 12]
    for q in range(4):
        blocks.append({"name": f"W2Q{q + 1}", "zone": "V", "E": w2e[q], "fixedE": 12 if q == 3 else 0,
                       "P2": 53 if q < 3 else 0, "P3fix": 62 if q < 3 else 61, "P3all": 65 if q < 3 else 64})
    # K quarters from the calendar; placebo P2' = all Mo-Do (daily futures since 2026-04-04 empty P2'')
    for i, (a, b) in enumerate(K_QUARTERS):
        c = quarter_counts(a, b)
        p2 = c["MoDo"] if k_placebo == "P2_all_modo" else 0
        blocks.append({"name": f"KQ{i + 1}", "zone": "K", "E": c["E"], "fixedE": 0 if p2 > 0 else c["E"],
                       "P2": p2, "P3fix": c["P3fix"], "P3all": c["P3all"], "von": a.isoformat(), "bis": b.isoformat()})
    for blk in blocks:
        blk["var_e_day"] = var_e_day
        blk["sig2"] = sig
    return blocks


def se_pooled(blocks, upto: int, j: str) -> float:
    n_e = sum(b["E"] for b in blocks[:upto])
    n_p = sum(b[j] for b in blocks[:upto])
    return math.sqrt(blocks[0]["var_e_day"] / n_e + blocks[0]["sig2"][j] / n_p)


class Sim:
    """Common random numbers for all effects: block sums of event and placebo noise."""

    def __init__(self, blocks, n_paths: int, seed: int):
        self.blocks = blocks
        rng = np.random.default_rng(seed)
        nb = len(blocks)
        self.sumE = np.empty((n_paths, nb))
        self.sumP = {j: np.empty((n_paths, nb)) for j in ("P2", "P3fix", "P3all")}
        for i, b in enumerate(blocks):
            self.sumE[:, i] = rng.standard_normal(n_paths) * math.sqrt(b["var_e_day"] * b["E"])
            for j in self.sumP:
                self.sumP[j][:, i] = rng.standard_normal(n_paths) * math.sqrt(b["sig2"][j] * b[j]) if b[j] > 0 else 0.0
        self.eps_null = rng.standard_normal((n_paths, 4))     # independent part of the null-condition statistic
        self.nE = np.array([b["E"] for b in blocks], dtype=float)
        self.nP = {j: np.array([b[j] for b in blocks], dtype=float) for j in self.sumP}
        self.nFixed = np.array([b["fixedE"] for b in blocks], dtype=float)
        self.looks = [10, 11, 12, 13]          # number of blocks included at looks 1..4 (30/33/36/39 months)
        self.n = n_paths

    def run(self, mu_blocks: np.ndarray, *, conditions=("P2", "P3fix", "P3all"), null_cond=True, stab=True,
            futility=True, kappa_mode="fixed", line_null=("central",)) -> dict:
        """P(PASS) per look for an effect vector mu_blocks (bp on event days of each block)."""
        n = self.n
        effE = self.sumE + mu_blocks[None, :] * self.nE[None, :]       # effect enters the event sums
        alive = np.ones(n, dtype=bool)
        passed = np.zeros(n, dtype=bool)
        pass_at = np.zeros((n, 4), dtype=bool)
        fail_stab = np.zeros(n, dtype=bool)
        stop_fut = np.zeros(n, dtype=bool)
        info_full = sum(self.nE[: self.looks[-1]])
        null_sd_w1 = INPUTS["null_W1"]["value"][line_null[0]]
        null_sd_w2 = INPUTS["null_W2"]["value"][line_null[0]]
        for k, upto in enumerate(self.looks):
            t_k = sum(self.nE[:upto]) / info_full
            z_k = C_B / math.sqrt(t_k)                                     # OBF boundary on the z-scale
            nE = self.nE[:upto].sum()
            Ebar = effE[:, :upto].sum(1) / nE
            cond = np.ones(n, dtype=bool)
            z_primary = None
            for j in conditions:
                nP = self.nP[j][:upto].sum()
                Pbar = self.sumP[j][:, :upto].sum(1) / nP
                D = Ebar - Pbar
                se = math.sqrt(self.blocks[0]["var_e_day"] / nE + self.blocks[0]["sig2"][j] / nP)
                z = D / se
                if j == "P2":
                    z_primary, D2, se2 = z, D, se
                cond &= z >= z_k
            if z_primary is None:
                raise ValueError("P2 must be among the conditions")
            if null_cond:
                # scaled null: threshold tau95 * SE_P2 (binding term), mean factor kappa = 1 - fixed/N_E,
                # centre noise from the fixed Fridays (SD scales with 52/N_E against the W2 value)
                n_fixed = self.nFixed[:upto].sum()
                kappa = 1.0 - n_fixed / nE
                centre_sd = (null_sd_w2["centre_sd"] * 52.0 / nE) if n_fixed > 0 else 0.0
                rho = math.sqrt(max(0.0, 1.0 - (centre_sd / se2) ** 2))
                mu_eff = (mu_blocks[:upto] * self.nE[:upto]).sum() / nE
                y = kappa * mu_eff + rho * (D2 - mu_eff) + math.sqrt(1.0 - rho ** 2) * se2 * self.eps_null[:, k]
                cond &= y >= TAU95 * se2
            cross = alive & (z_primary >= z_k)
            if stab and k >= 0:
                # stability test at every efficacy stop with an older part: J = last 4 blocks, A = earlier blocks
                jb = list(range(upto - 4, upto))
                ab = list(range(0, upto - 4))
                nEJ, nEA = self.nE[jb].sum(), self.nE[ab].sum()
                nPJ, nPA = self.nP["P2"][jb].sum(), self.nP["P2"][ab].sum()
                xJ = effE[:, jb].sum(1) / nEJ - self.sumP["P2"][:, jb].sum(1) / nPJ
                xA = effE[:, ab].sum(1) / nEA - self.sumP["P2"][:, ab].sum(1) / nPA
                v = self.blocks[0]["var_e_day"]
                s2 = self.blocks[0]["sig2"]["P2"]
                seD = math.sqrt(v / nEJ + s2 / nPJ + v / nEA + s2 / nPA)
                zD = (xJ - xA) / seD
                reject = cross & (zD < -Z_STAB)
                fail_stab |= reject
                alive &= ~reject
                cross &= ~reject
            ok = cross & cond
            pass_at[:, k] = ok
            passed |= ok
            alive &= ~ok
            if futility and k < 3:
                fut = alive & (z_primary < 0.0)
                stop_fut |= fut
                alive &= ~fut
        return {"p_pass": float(passed.mean()), "p_pass_by_look": [float(pass_at[:, :k + 1].any(1).mean()) for k in range(4)],
                "p_pass_at_look": [float(pass_at[:, k].mean()) for k in range(4)],
                "p_fail_stab": float(fail_stab.mean()), "p_futility": float(stop_fut.mean())}


def mde(sim: Sim, target: float, make_mu, lo=0.0, hi=80.0, **kw) -> float:
    """Effect (bp) with P(PASS) = target by bisection on common random numbers (monotone in the effect)."""
    f = lambda m: sim.run(make_mu(m), **kw)["p_pass"] - target
    if f(hi) < 0:
        return math.inf
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 0.005:
            break
    return 0.5 * (lo + hi)


def mde_by_look(sim: Sim, target: float, make_mu, look: int, lo=0.0, hi=120.0, **kw) -> float:
    f = lambda m: sim.run(make_mu(m), **kw)["p_pass_by_look"][look] - target
    if f(hi) < 0:
        return math.inf
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 0.005:
            break
    return 0.5 * (lo + hi)


def fixed_rule_mde(se12: float, t_months: float, q: float, g: float) -> float:
    """MDE80 of the fixed one-look rule (c): (z_krit + Phi^-1(0.80/(q g))) SE_12 sqrt(12/T) (feasibility31 R5)."""
    p = 0.80 / (q * g)
    if p >= 1.0:
        return math.inf
    return (Z_POOL + float(norm.ppf(p))) * se12 * math.sqrt(12.0 / t_months)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


# --------------------------------------------------------------------------------------------------------------------
def main() -> None:
    t0 = time.time()
    out: dict = {"meta": {"script": "a2_reg_calc.py", "seed": SEED, "paths": N_PATHS, "numpy": np.__version__,
                          "date": "2026-11-04", "role": "Herleitung"}, "inputs": INPUTS}
    lines = []
    P = lines.append
    P("A2 registration draft 3.1 - operating characteristic (variant (c) + BE-04), seed %d, paths %d" % (SEED, N_PATHS))

    # (0) calendar: K quarters, STRESS_ABS days in the judging windows
    P("\n(0) Kalender")
    kq = []
    for a, b in K_QUARTERS:
        c = quarter_counts(a, b)
        c.update({"von": a.isoformat(), "bis": b.isoformat()})
        kq.append(c)
        P(f"  K-Quartal {a}..{b}: Freitage {c['E']}, Mo-Do {c['MoDo']}, P3fix {c['P3fix']}, P3all {c['P3all']}, "
          f"P2'' (Mo-Do ohne Futures-Delivery) = 0 bei taeglichen Futures seit {INPUTS['daily_futures_from']['value']}")
    out["k_quarters"] = kq
    stress_path = os.path.join(REPO, "scinance3-impl/state/runs/stress_abs.json")
    with open(stress_path, encoding="utf-8") as fh:
        stress = json.load(fh)
    days = [dt.date.fromisoformat(x) for x in stress["days"]]
    wins = {"W1": (dt.date(2024, 7, 1), dt.date(2025, 6, 30)), "W2": (dt.date(2025, 7, 1), dt.date(2026, 6, 28)),
            "K_registriert": (dt.date(2026, 10, 1), dt.date(2027, 12, 31)), "K_Luecke_2026-07..09": (dt.date(2026, 7, 1), dt.date(2026, 9, 30)),
            "Vorfenster_2023-07..2024-06": (dt.date(2023, 7, 1), dt.date(2024, 6, 30))}
    wdn = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    st = {}
    for k, (a, b) in wins.items():
        hit = [(d.isoformat(), wdn[d.weekday()]) for d in days if a <= d <= b]
        st[k] = hit
        P(f"  STRESS_ABS-Tage in {k}: {len(hit)} {hit}")
    n_judge = len(st["W1"]) + len(st["W2"]) + len(st["K_registriert"])
    st["tage_in_urteilsfenstern"] = n_judge
    st["file_sha256"] = sha256(stress_path)
    st["fixture_sha256_field"] = stress["sha256"]
    st["n_days_total"] = stress["n_days"]
    out["stress_abs"] = st
    P(f"  STRESS_ABS-Tage in den Urteilsfenstern (W1+W2+K registriert): {n_judge}; Datei sha256 {st['file_sha256']}")

    # (1) fixed-rule MDE80 (feasibility31 R5 convention) per T and nuisance line
    P("\n(1) MDE80 der festen Ein-Blick-Regel (c), (z_krit + Phi^-1(0,80/(q g))) SE_12 sqrt(12/T), g 0,9025")
    fx = {}
    for name, se in (("zentral_7.58", 7.58), ("W1_7.34", 7.34), ("stress_8.52", 8.52)):
        row = {}
        for T in (12, 24, 27, 30, 33, 36, 39):
            q = 1.0 if T <= 12 else Q1
            row[str(T)] = fixed_rule_mde(se, T, q, G)
        row["T_fuer_22bp"] = 12.0 * ((Z_POOL + float(norm.ppf(0.80 / (Q1 * G)))) * se / SESOI) ** 2
        row["30_mit_GSD_x1.03_daten"] = row["30"] * math.sqrt(1.03)
        fx[name] = row
        P(f"  {name}: " + ", ".join(f"T{T} {row[str(T)]:.2f}" for T in (24, 27, 30, 33, 36, 39)) +
          f"; 22 bp ab {row['T_fuer_22bp']:.2f} Monaten; T30 x sqrt(1,03) = {row['30_mit_GSD_x1.03_daten']:.2f}")
    fx["mde_faktor_q095_g"] = Z_POOL + float(norm.ppf(0.80 / (Q1 * G)))
    fx["mde_faktor_q095"] = Z_POOL + float(norm.ppf(0.80 / Q1))
    fx["mde_faktor_qplan_g"] = Z_POOL + float(norm.ppf(0.80 / (INPUTS["q_plan_each_term"]["value"] * G)))
    P(f"  MDE-Faktor: q 0,95 ohne Gate {fx['mde_faktor_q095']:.4f}; mit Gate 0,9025 {fx['mde_faktor_q095_g']:.4f}; "
      f"q_plan 0,9639 mit Gate {fx['mde_faktor_qplan_g']:.4f}")
    out["fixed_rule"] = fx

    # (2) full plan Monte Carlo, central line
    P("\n(2) Gesamtregel (Plan V24 + K-Blicke 30/33/36/39 Monate, OBF C_B 2,886, Stabilitaetstest each_term, "
      "Futility Z<0 Blicke 1-3, Konjunktion P2''/P3fix/P3all + skalierte Null, Gate 0,9025 als Faktor)")
    blocks = build_blocks("central")
    out["blocks_central"] = [{k: v for k, v in b.items() if k not in ("sig2",)} for b in blocks]
    out["sigma2_placebo_day_central"] = blocks[0]["sig2"]
    for k, upto in enumerate((10, 11, 12, 13)):
        P(f"  Blick {k + 1} ({LOOK_DATES[k]}): N_E {int(sum(b['E'] for b in blocks[:upto]))}, N_P2 {int(sum(b['P2'] for b in blocks[:upto]))}, "
          f"SE P2'' {se_pooled(blocks, upto, 'P2'):.3f}, P3fix {se_pooled(blocks, upto, 'P3fix'):.3f}, P3all {se_pooled(blocks, upto, 'P3all'):.3f} bp; "
          f"OBF z-Grenze {C_B / math.sqrt(sum(b['E'] for b in blocks[:upto]) / sum(b['E'] for b in blocks)):.4f}")
    sim = Sim(blocks, N_PATHS, SEED)
    nb = len(blocks)
    homog = lambda m: np.full(nb, m)
    only_V = lambda m: np.array([m] * 8 + [0.0] * 5)
    only_W1 = lambda m: np.array([m] * 4 + [0.0] * 9)
    FULL = dict(conditions=("P2", "P3fix", "P3all"), null_cond=True, stab=True, futility=True)
    r0 = sim.run(homog(0.0), **FULL)
    alpha_rule = r0["p_pass"]
    P(f"  alpha_eff der Regel (ohne Gate) {alpha_rule:.5f}; mit Gate x0,9025 {alpha_rule * G:.5f}; je Blick {[round(x, 5) for x in r0['p_pass_at_look']]}; "
      f"Futility-Stopp unter H0 {r0['p_futility']:.4f}")
    r0p = sim.run(homog(0.0), conditions=("P2",), null_cond=False, stab=True, futility=True)
    r0pn = sim.run(homog(0.0), conditions=("P2",), null_cond=False, stab=False, futility=False)
    out["alpha_check"] = {"primaer_allein_stab_futility": r0p["p_pass"], "primaer_allein_ohne_alles": r0pn["p_pass"],
                          "quelle_vergleich": "stab_results.json s4b each_term alpha_eff 0,00249; none 0,002536"}
    P(f"  Kontrolle Primaerstatistik allein: alpha_eff mit Stabilitaetstest+Futility {r0p['p_pass']:.5f}, OBF-Plan ohne alles {r0pn['p_pass']:.5f} "
      f"(stab_results s4b: 0,00249 / 0,00254)")
    mde_full = mde(sim, 0.80 / G, homog, **FULL)
    mde_look = [mde_by_look(sim, 0.80 / G, homog, k, **FULL) for k in range(4)]
    P(f"  MDE80 Gesamtplan (P(PASS bis Blick 4) = 0,80 inkl. Gate): {mde_full:.2f} bp")
    P(f"  MDE80 je Blick (P(PASS bis Blick k) = 0,80 inkl. Gate): " + ", ".join(f"Blick {k + 1} {m:.2f}" for k, m in enumerate(mde_look)))
    r_ses = sim.run(homog(SESOI), **FULL)
    P(f"  P(PASS | 22 bp) gesamt {r_ses['p_pass'] * G:.4f} (ohne Gate {r_ses['p_pass']:.4f}); kumuliert je Blick "
      f"{[round(x * G, 4) for x in r_ses['p_pass_by_look']]}; Stabilitaets-FAIL {r_ses['p_fail_stab']:.4f}; Futility {r_ses['p_futility']:.4f}")
    oc = {"p_pass_0": alpha_rule * G, "p_pass_0_ohne_gate": alpha_rule, "p_pass_sesoi": r_ses["p_pass"] * G,
          "p_pass_sesoi_by_look": [x * G for x in r_ses["p_pass_by_look"]], "p_fail_stab_sesoi": r_ses["p_fail_stab"],
          "p_futility_0": r0["p_futility"], "p_pass_0_at_look": [x * G for x in r0["p_pass_at_look"]]}
    for m in (5.0, 16.5, 25.0):
        r = sim.run(homog(m), **FULL)
        oc[f"p_pass_{m}"] = r["p_pass"] * G
        P(f"  P(PASS | {m} bp) {r['p_pass'] * G:.4f}")
    # protection line: effect only in the older part (zone V), 1 MDE of the registered rule
    for lab, mk in (("nur_V_1MDE", only_V), ("nur_V_2MDE", lambda m: only_V(2 * m)), ("nur_W1_1MDE", only_W1)):
        r = sim.run(mk(mde_full), **FULL)
        oc[lab] = {"p_pass": r["p_pass"] * G, "p_pass_by_look": [x * G for x in r["p_pass_by_look"]],
                   "veraltet_blicke_3_4": (r["p_pass_at_look"][2] + r["p_pass_at_look"][3]) * G, "p_fail_stab": r["p_fail_stab"]}
        P(f"  Schutzzeile {lab}: P(PASS) {r['p_pass'] * G:.4f}; je Blick kumuliert {[round(x * G, 4) for x in r['p_pass_by_look']]}; "
          f"veraltet (Blicke 3-4, juengste 12 Monate effektfrei) {(r['p_pass_at_look'][2] + r['p_pass_at_look'][3]) * G:.4f}; "
          f"Stabilitaets-FAIL {r['p_fail_stab']:.4f}")
    # the same without the stability test (what the test buys)
    r_nostab = sim.run(only_V(mde_full), conditions=("P2", "P3fix", "P3all"), null_cond=True, stab=False, futility=True)
    oc["nur_V_1MDE_ohne_stabtest"] = r_nostab["p_pass"] * G
    P(f"  Vergleich ohne Stabilitaetstest, nur V 1 MDE: P(PASS) {r_nostab['p_pass'] * G:.4f}")
    oc["mde80_plan"] = mde_full
    oc["mde80_by_look"] = mde_look
    out["oc_central"] = oc

    # (3) strictness ratio: Grundfassung = primary alone, kappa 1 (no null condition), no gate, same plan
    P("\n(3) Strenge-Quotient (Grundfassung: P2''-Kontrast allein, zentrale Nuisance, dieselbe Regel (c) + Blickplan, kein Gate)")
    steps = []
    base = mde(sim, 0.80, homog, conditions=("P2",), null_cond=False, stab=True, futility=True)
    steps.append(("Grundfassung P2'' allein, (c), Plan", base))
    m1 = mde(sim, 0.80, homog, conditions=("P2", "P3fix"), null_cond=False, stab=True, futility=True)
    steps.append(("+ P3fix (exakt gemeinsam)", m1))
    m2 = mde(sim, 0.80, homog, conditions=("P2", "P3fix", "P3all"), null_cond=False, stab=True, futility=True)
    steps.append(("+ P3all (drei Placebos, exakt gemeinsam)", m2))
    m3 = mde(sim, 0.80, homog, conditions=("P2", "P3fix", "P3all"), null_cond=True, stab=True, futility=True)
    steps.append(("+ skalierte Null-Bedingung (kappa, feste Freitage W2)", m3))
    steps.append(("+ Gate-(4)-Faktor 0,9025", mde_full))
    sq = mde_full / base
    out["strictness"] = {"steps": [{"schritt": s, "mde80": v, "faktor": (v / steps[i - 1][1] if i else 1.0)} for i, (s, v) in enumerate(steps)],
                         "quotient": sq, "grundfassung": base}
    for i, (s, v) in enumerate(steps):
        P(f"  {s}: {v:.2f} bp" + (f" (x{v / steps[i - 1][1]:.4f})" if i else ""))
    P(f"  Strenge-Quotient {sq:.4f} ({'>= 1,3: Nutzer-Vorlage' if sq >= 1.3 else '< 1,3'})")
    # double statement product vs exact at look 1 (fixed test, 30 months, q 0.95)
    P("  Doppelausweis am Blick 1 (feste Regel, 30 Monate, q 0,95, OBF-Grenze Blick 1): Produkt der Einzel-Powers gegen exakt")
    upto = 10
    nE = sum(b["E"] for b in blocks[:upto])
    z1 = C_B / math.sqrt(nE / sum(b["E"] for b in blocks))
    ses = {j: se_pooled(blocks, upto, j) for j in ("P2", "P3fix", "P3all")}
    n_fixed = sum(b["fixedE"] for b in blocks[:upto])
    kappa1 = 1.0 - n_fixed / nE
    def prod_power(m):
        p = 1.0
        for j in ses:
            p *= float(norm.sf(z1 - m / ses[j]))
        p *= float(norm.sf(TAU95 - kappa1 * m / ses["P2"]))
        return p * Q1 * G
    lo, hi = 0.0, 80.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if prod_power(mid) < 0.80:
            lo = mid
        else:
            hi = mid
    mde_prod1 = 0.5 * (lo + hi)
    mde_exact1 = mde_look[0]
    out["strictness"]["doppelausweis_blick1"] = {"produkt": mde_prod1, "exakt_gemeinsam": mde_exact1, "z_grenze_blick1": z1, "kappa_blick1": kappa1, "se_blick1": ses}
    P(f"  Blick 1: Produkt {mde_prod1:.2f} bp, exakt gemeinsam (MC, P(PASS bis Blick 1) = 0,80) {mde_exact1:.2f} bp; z-Grenze {z1:.4f}; kappa {kappa1:.3f}")

    # (4) sensitivity: stress nuisance line, W1 line (primary only analytic), q sensitivity k
    P("\n(4) Sensitivitaet")
    blocks_s = build_blocks("stress")
    sim_s = Sim(blocks_s, N_PATHS, SEED + 1)
    r0s = sim_s.run(homog(0.0), line_null=("stress",), **FULL)
    mde_s = mde(sim_s, 0.80 / G, homog, line_null=("stress",), **FULL)
    r_ses_s = sim_s.run(homog(SESOI), line_null=("stress",), **FULL)
    out["oc_stress"] = {"p_pass_0": r0s["p_pass"] * G, "mde80_plan": mde_s, "p_pass_sesoi": r_ses_s["p_pass"] * G,
                        "p_pass_sesoi_by_look": [x * G for x in r_ses_s["p_pass_by_look"]]}
    P(f"  Stress-Linie (SE P2'' 8,52): alpha_eff {r0s['p_pass'] * G:.5f}, MDE80 Plan {mde_s:.2f} bp, P(PASS | 22 bp) {r_ses_s['p_pass'] * G:.4f}, "
      f"kumuliert {[round(x * G, 4) for x in r_ses_s['p_pass_by_look']]}")
    # effective alpha if the threshold used the registered SE 7.58 while the confirmation SE is 8.52 (E7 (c) caveat)
    z_eff = Z_POOL * 7.58 / 8.52
    out["e7c_vorbehalt"] = {"z_eff": z_eff, "alpha_eff_feste_SE": float(norm.sf(z_eff)), "lesart": "t-artig aus Konfirmations-SE -> alpha bleibt 0,0025 (DEC-107 N1 (2))"}
    P(f"  E7 (c): feste SE 7,58 in der Schwelle bei Stress 8,52: z_eff {z_eff:.3f}, alpha_eff {float(norm.sf(z_eff)):.4f} (> 0,0025); "
      f"t-artige Schwelle aus der Konfirmations-SE: alpha 0,0025")
    # variance ratio k (younger/older) sensitivity of q: from stab_results s2 (quoted)
    out["q_sensitivity_k"] = {"source": "HERLEITUNG_STABILITAETSTEST 2.3: k 0,7..1,5 -> q 0,943..0,966, realisierte Power 0,794..0,813 bei Planung mit q 0,95",
                              "k_0.7": 0.943, "k_1.5": 0.966}
    # V3 pre-window SE (published T2 row) rescaled to W2 and look-1 counts (arithmetic only)
    v3 = INPUTS["V3_prewindow"]["value"]
    se_v3_w2n = math.sqrt(1.1491 * v3["E_sd"] ** 2 / 52 + 1.3177 * v3["P_sd"] ** 2 / 159)
    se_v3_k1 = math.sqrt(1.1491 * v3["E_sd"] ** 2 / 52 + 1.3177 * v3["P_sd"] ** 2 / 209)
    out["vorfenster_hinweis"] = {"V3_se_analytic_T2": v3["se_analytic"], "V3_se_with_W2_counts": se_v3_w2n, "V3_null_sd": v3["null_sd"],
                                 "fixed_rule_mde_T30_with_V3_se": fixed_rule_mde(se_v3_w2n, 30, Q1, G),
                                 "hinweis": "Reine Arithmetik aus T2 (Zeile V3 2023-06..2024-05); das bindende Vorfenster 2023-07-01..2024-06-30 ist vom Orchestrator per Konto-Eintrag nachzuliefern (VR-b10 (i), DEC-107 N1 (2)); kein Mittel, kein Vorzeichen."}
    P(f"  Vorfenster-Hinweis [R]: T2-Zeile V3 (2023-06..2024-05) P2'' SE 5,31 (eigene N) / {se_v3_w2n:.2f} (W2-N 52/159) gegen Platzhalter 7,58; "
      f"feste Regel T30 damit {fixed_rule_mde(se_v3_w2n, 30, Q1, G):.2f} bp (nur Hinweis, Konto-Eintrag ausstehend)")

    # (5) annual book, n_eff, positive control criterion, Welch df
    P("\n(5) Jahresbuch, n_eff, Positivkontrolle")
    ab = {"jahr": 2027, "vorher": 0.0, "alpha_test": 0.0025,
          "p_falsch_pass_2027_blicke_1_3": sum(oc["p_pass_0_at_look"][:3]), "p_falsch_pass_2028_blick_4": oc["p_pass_0_at_look"][3],
          "mit_dieser_registrierung_summe_alpha": 0.0025}
    out["annual_book"] = ab
    P(f"  Jahresbuch 2027: vorher 0 (keine registrierte Hypothese mit Blick 2027, FENSTERREGISTER 8); mit A2: Summe alpha 0,0025 "
      f"(MC-Anteil Blicke 1-3 in 2027 {ab['p_falsch_pass_2027_blicke_1_3']:.5f}, Blick 4 am 2028-01-01 {ab['p_falsch_pass_2028_blick_4']:.5f})")
    neff = {}
    for k, upto in enumerate((8, 10, 11, 12, 13)):
        ne = int(sum(b["E"] for b in blocks[:upto]))
        neff[("V_allein" if upto == 8 else f"Blick_{k}")] = {"N_E": ne, "N_E_div_c_modo": ne / INPUTS["c_overlap"]["value"],
                                                            "N_P2": int(sum(b["P2"] for b in blocks[:upto]))}
    out["n_eff"] = neff
    P("  n_eff (Ereignis-Cluster): " + "; ".join(f"{k}: N_E {v['N_E']} (N_E/c 1,3177 = {v['N_E_div_c_modo']:.1f}), N_P2 {v['N_P2']}" for k, v in neff.items()))
    pk_se = math.sqrt(0.80 * 0.20 / 200)
    pk = {"ziel_pass_quote": 0.80, "seeds": 200, "binomial_se": pk_se, "kriterium": 0.80 - 2.3263 * pk_se,
          "injektion_bp": mde_full, "sd_grenze": "SD der Kontrollwelt <= 1,10 x SD der Power-Zeile (VR-b10, VR-f12)"}
    out["positive_control"] = pk
    P(f"  Positivkontrolle: Injektion {mde_full:.2f} bp (MDE80 des Plans), erwartete PASS-Quote 0,80, Kriterium 0,80 - 2,3263 x {pk_se:.4f} = {pk['kriterium']:.4f} bei 200 Seeds")
    df1 = int(sum(b["E"] for b in blocks[:10])) - 1
    out["t_grenze_blick1"] = {"df": df1, "t_0.0025": float(student_t.isf(0.0025, df1)), "z": Z_POOL}
    P(f"  t-artige Grenze am Blick 1: df {df1} (Ereignis-Cluster - 1), t_0,0025 {float(student_t.isf(0.0025, df1)):.4f} gegen z 2,8070")

    # (6) pins
    pins = {}
    for rel in ("scinance3-impl/state/herleitung_a2/NULL_SIMULATION_A2.md", "scinance3-impl/state/herleitung_stabilitaetstest/stab_results.json",
                "scinance3-impl/state/herleitung_stabilitaetstest/stab_sim.py", "scinance3-impl/state/feasibility/A2.yaml",
                "src/bybit_edge/research/feasibility31/rules.py", "scinance3-impl/state/runs/stress_abs.json",
                "scinance3-impl/state/prd_analyse_2026-11-01/KRITIK_PRD.md", "scinance3-impl/state/FENSTERREGISTER.md",
                "scinance3-impl/state/KONTO_INVENTAR_2026-11-02.md", "scinance3-impl/state/registered/TEMPLATE_3_1.yaml"):
        pins[rel] = sha256(os.path.join(REPO, rel))
    pins["calc/a2_reg_calc.py"] = sha256(os.path.abspath(__file__))
    out["sha256"] = pins
    P("\n(6) sha256-Pins")
    for k, v in pins.items():
        P(f"  {v}  {k}")
    out["meta"]["cpu_seconds"] = time.time() - t0
    P(f"\nLaufzeit {time.time() - t0:.1f} s")
    with open(os.path.join(HERE, "a2_reg_calc.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, default=str)
    text = "\n".join(lines) + "\n"
    with open(os.path.join(HERE, "a2_reg_calc.out"), "w", encoding="utf-8") as fh:
        fh.write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
