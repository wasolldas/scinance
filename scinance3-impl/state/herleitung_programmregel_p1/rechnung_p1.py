"""P-1 derivation (programme rule: threshold, power and SE from one piece).

Pure arithmetic on two EXISTING, unsealed artefacts -- no panel data, no outcome
data, no new simulation:
  * v5e prelaunch JSON  state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json  (A3, GL-032)
  * A1 feasibility JSON state/herleitung_a1/feasibility.json              (A1, GL-033)
Sealed files (*_L_window_sealed.json, weekly_ic_series.csv, ic_series_*_UNION_REAL.csv)
are never opened; the loader refuses any such name. Window "L" of the v5e JSON is
never read. Candidate-agnostic: no number of any future candidate is computed.

Run (from the repo root):  python3 -I scinance3-impl/state/herleitung_programmregel_p1/rechnung_p1.py
Writes rechnung_p1.json next to this script (deterministic, stdlib only).
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import math
import os
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.dirname(HERE)
V5E = os.path.join(STATE, "runs", "wp13a_20261012_v5e", "wp13a_prelaunch.json")
A1 = os.path.join(STATE, "herleitung_a1", "feasibility.json")
OUT = os.path.join(HERE, "rechnung_p1.json")

SEALED_PATTERNS = ("*_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_*_UNION_REAL.csv")

N = NormalDist()
PHI = N.cdf
Z05 = N.inv_cdf(0.95)          # 1.644854 critical value alpha 0.05 one-sided
Z01 = N.inv_cdf(0.99)          # 2.326348 critical value alpha 0.01 one-sided
ZB = N.inv_cdf(0.80)           # 0.841621 power 0.80
REG_Z_WIN = 2.4865             # registered A3 constant (gates.Z_PER_WINDOW) = MDE factor alpha 0.05
REG_Z_POOL = 3.1680            # PRD/DEC-52 "z" of the pooled regime = MDE factor alpha 0.01
PRIOR_A3 = 0.03                # PRD 4.1 / 5.3 IC_prior (registered, A3 only)

# Option definitions: critical value per window and pooled (DEC-52 branch).
OPTIONS = {
    "a": {"crit_w": Z05, "crit_p": Z01,
          "text": "Schwelle = kritischer Wert zum registrierten alpha (0,05 je Fenster, 0,01 gepoolt)"},
    "b": {"crit_w": REG_Z_WIN, "crit_p": REG_Z_POOL,
          "text": "Schwelle = MDE-Faktor des Regimes (2,4865 je Fenster, 3,1680 gepoolt), Power mit demselben Faktor"},
}


def _load(path: str) -> tuple[dict, str]:
    base = os.path.basename(path)
    for pat in SEALED_PATTERNS:
        if fnmatch.fnmatch(base, pat):
            raise SystemExit(f"refusing sealed file {base}")
    with open(path, "rb") as fh:
        raw = fh.read()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _r(x: float, nd: int = 5) -> float:
    return float(round(x, nd))


# ---------------------------------------------------------------------------
# A3 (GL-032) from v5e
# ---------------------------------------------------------------------------

def a3_inputs(v5e: dict) -> dict:
    out = {}
    for w in ("W1", "W2"):                      # window "L" is never touched
        win = v5e["windows"][w]
        nf = win["noise_floor_and_threshold"]
        cals = win["beta_control_method_study"]["calibrations"]
        hr = win["beta_control_recommended_high_rep"]
        wv = {"e_floor": nf["floor"]["e_floor"], "w_judged": nf["w_judged"], "variants": {}}
        for v in ("mom1", "mom2", "mom4", "rev_gap"):
            d = {"ic_min_capped": nf["ic_min_capped_per_variant"][v],
                 "c_rho_corrected": nf["persistence_null"]["variants"][v]["c_rho_corrected"],
                 "direction": hr["stress"]["variants"][v]["direction"]}
            for cal in ("measured", "stress"):
                d[f"factor_sd_{cal}"] = cals[cal]["methods"]["none"]["variants"][v]["factor_sd"]
            for key in ("stress", "stress_drifting"):
                hv = hr[key]["variants"][v]
                d[f"fm8_{key}"] = {"mean": hv["mean_ic_draws_mean"], "sd": hv["mean_ic_draws_sd"],
                                   "q9936": hv["quantile_one_sided"]}
            wv["variants"][v] = d
        out[w] = wv
    return out


def a3_window(inp_w: dict, v: str, cal: str, opt: str) -> dict:
    d = inp_w["variants"][v]
    sgn = 1.0 if d["direction"] == "positive" else -1.0
    crit = OPTIONS[opt]["crit_w"]
    sd_raw = d[f"factor_sd_{cal}"]
    se = max(inp_w["e_floor"], sd_raw) / math.sqrt(inp_w["w_judged"])       # DEC-75 (1) SE rule
    ic_min = d["ic_min_capped"] * (crit / REG_Z_WIN)                         # DEC-74 (a) with the option's factor
    # beta-control quantile: registered 0.9936 quantile for (b); for (a) the one-sided 0.95
    # quantile in normal approximation mean + sgn*1.6449*sd (approximation, labelled).
    qs = []
    for key in ("fm8_stress", "fm8_stress_drifting"):
        f = d[key]
        q = f["q9936"] if opt == "b" else f["mean"] + sgn * Z05 * f["sd"]
        qs.append((sgn * q, f["sd"]))
    q_dir, sd_beta = max(qs, key=lambda t: t[0])                              # DEC-87 (E): more extreme binds
    thr_beta = max(ic_min, q_dir)
    p_mag = PHI(PRIOR_A3 / se - crit)
    p_icmin = PHI((PRIOR_A3 - ic_min) / se)
    p_beta = PHI((PRIOR_A3 - thr_beta) / sd_beta)
    mde = max((crit + ZB) * se, ic_min + ZB * se, thr_beta + ZB * sd_beta)
    return {"se": se, "sd_raw": sd_raw, "ic_min": ic_min, "q_beta_dir": q_dir, "sd_beta": sd_beta,
            "P_mag": p_mag, "P_icmin": p_icmin, "P_beta": p_beta,
            "P_voll": min(p_mag, p_icmin, p_beta), "MDE80": mde}


def a3_pooled(inp: dict, v: str, cal: str, opt: str, se_w: dict) -> dict:
    w1, w2 = inp["W1"], inp["W2"]
    s1 = max(w1["e_floor"], w1["variants"][v][f"factor_sd_{cal}"])
    s2 = max(w2["e_floor"], w2["variants"][v][f"factor_sd_{cal}"])
    n1, n2 = w1["w_judged"], w2["w_judged"]
    se_p = math.sqrt(n1 * s1 ** 2 + n2 * s2 ** 2) / (n1 + n2)               # mean over the 103 judged weeks
    crit_p = OPTIONS[opt]["crit_p"]
    p_p = PHI(PRIOR_A3 / se_p - crit_p)
    screen = 0.5 * crit_p * se_p                                             # DEC-52 (ii) 0.5x registered threshold
    ps = {w: PHI((PRIOR_A3 - screen) / se_w[w]) for w in ("W1", "W2")}
    return {"se_p": se_p, "crit_p": crit_p, "P_pooled": p_p, "MDE80_pooled": (crit_p + ZB) * se_p,
            "screen_thr": screen, "P_screen": ps, "P_dec52_approx": p_p * ps["W1"] * ps["W2"],
            "note": "Beta-Kontrolle im DEC-52-Zweig nie definiert (Audit PC v3, 3.6) - nicht enthalten"}


# ---------------------------------------------------------------------------
# A1 (GL-033) from feasibility.json, theta = 1 (upper bound; theta is UNBELEGT)
# ---------------------------------------------------------------------------

def a1_inputs(fj: dict) -> dict:
    pw = fj["configs"]["A_dec70_1h_eingeschlossen"]["power"]
    out = {}
    for c in ("c_dec67_E4", "c1_binding", "c_mbb_measured"):
        g = pw["grid"][f"{c}|theta=1.0"]
        out[c] = {"c": pw["inputs"]["c_options"][c],
                  "se": {"W1": g["W1"]["se_bp"], "W2": g["W2"]["se_bp"], "pooled": g["pooled"]["se_pooled_bp"]},
                  "prem1": {"W1": g["W1"]["prem_bp"], "W2": g["W2"]["prem_bp"],
                            "pooled": g["pooled"]["prem_pooled_bp"]}}
    return out


def a1_eval(d: dict, opt: str, theta: float) -> dict:
    cw, cp = OPTIONS[opt]["crit_w"], OPTIONS[opt]["crit_p"]
    prem = {k: theta * v for k, v in d["prem1"].items()}
    se = d["se"]
    pw = {w: PHI(prem[w] / se[w] - cw) for w in ("W1", "W2")}
    mde = {w: (cw + ZB) * se[w] for w in ("W1", "W2")}
    p_p = PHI(prem["pooled"] / se["pooled"] - cp)
    screen = 0.5 * cp * se["pooled"]
    ps = {w: PHI((prem[w] - screen) / se[w]) for w in ("W1", "W2")}
    return {"P_W": pw, "MDE80_W": mde, "P_pooled": p_p, "MDE80_pooled": (cp + ZB) * se["pooled"],
            "prem": prem, "P_screen": ps, "P_dec52_approx": p_p * ps["W1"] * ps["W2"],
            "P_C10_joint": pw["W1"] * pw["W2"]}


# ---------------------------------------------------------------------------
# regime assignment rules
# ---------------------------------------------------------------------------

def assign(p1: float, p2: float, mde_p: float, prior_p: float, p_dec52: float, rule: str,
           dec52_built: bool = True) -> str:
    pmin = min(p1, p2)
    pooled_ok = mde_p <= prior_p
    if rule == "L1":      # PRD 5.1/5.3 literal: >= 0.60 -> C.10, else DEC-52; GL-012 via pooled check
        if not pooled_ok:
            return "GL-012"
        return "C.10" if pmin >= 0.60 else "DEC-52"
    if rule == "L2":      # DEC-87 (F) generalised: >=0.80 C.10; 0.60..0.80 GL-012; <0.60 DEC-52 if built+feasible
        if pmin >= 0.80:
            return "C.10"
        if pmin < 0.60 and dec52_built and pooled_ok:
            return "DEC-52"
        return "GL-012"
    if rule == "L3":      # gap -> DEC-52 (DEC-52 (i) cut-off raised to 0.80)
        if pmin >= 0.80:
            return "C.10"
        return "DEC-52" if pooled_ok else "GL-012"
    if rule == "L3v":     # L3 with full DEC-52 gate power (pooled x screens) >= 0.80 (recommended form)
        if pmin >= 0.80:
            return "C.10"
        return "DEC-52" if p_dec52 >= 0.80 else "GL-012"
    if rule == "L5":      # strict: < 0.80 anywhere -> GL-012, no DEC-52
        return "C.10" if pmin >= 0.80 else "GL-012"
    if rule == "G":       # joint power of the registered gate
        if p1 * p2 >= 0.80:
            return "C.10"
        return "DEC-52" if p_dec52 >= 0.80 else "GL-012"
    raise ValueError(rule)


RULES = ("L1", "L2", "L3", "L3v", "L5", "G")


def a1_segments(d: dict, opt: str, rule: str) -> list[list]:
    """Regime as a function of theta on the grid 0.001..3.000: list of [theta_from, theta_to, regime].
    Shows (non-)monotonicity of a rule in the prior."""
    segs: list[list] = []
    for i in range(1, 3001):
        th = i / 1000.0
        e = a1_eval(d, opt, th)
        reg = assign(e["P_W"]["W1"], e["P_W"]["W2"], e["MDE80_pooled"], e["prem"]["pooled"],
                     e["P_dec52_approx"], rule)
        if segs and segs[-1][2] == reg:
            segs[-1][1] = th
        else:
            segs.append([th, th, reg])
    return segs


def a1_theta_min(d: dict, opt: str, rule: str) -> float | None:
    """Smallest theta in (0, 3] at which the rule does not give GL-012 (bisection on a grid)."""
    lo_ok = None
    for i in range(1, 3001):
        th = i / 1000.0
        e = a1_eval(d, opt, th)
        reg = assign(e["P_W"]["W1"], e["P_W"]["W2"], e["MDE80_pooled"], e["prem"]["pooled"],
                     e["P_dec52_approx"], rule)
        if reg != "GL-012":
            lo_ok = th
            break
    return lo_ok


# ---------------------------------------------------------------------------
# false-positive rates (null true in both windows, equal window SE)
# ---------------------------------------------------------------------------

def dec52_fpr(crit_p: float, upper_band: bool, screen_frac: float = 0.5) -> float:
    """P(Z1+Z2 >= crit_p*sqrt2, Z_i >= s, [Z_i <= u]) for iid N(0,1) window z-scores,
    s = 0.5*crit_p/sqrt2 (screen 0.5x pooled threshold in window-SE units),
    u = 2.0*crit_p/sqrt2 (magnitude band upper end, optional)."""
    s = screen_frac * crit_p / math.sqrt(2.0)
    u = 2.0 * crit_p / math.sqrt(2.0) if upper_band else math.inf
    c = crit_p * math.sqrt(2.0)
    h = 1e-4
    total = 0.0
    z1 = s
    hi = min(u, 9.0)
    while z1 < hi:
        zm = z1 + h / 2
        lo2 = max(s, c - zm)
        p2 = (PHI(min(u, 9.0)) - PHI(lo2)) if lo2 < min(u, 9.0) else 0.0
        total += N.pdf(zm) * p2 * h
        z1 += h
    return total


def bailey_zmax(k: int) -> float:
    g = 0.5772156649015329
    if k < 2:
        return 0.0
    return (1 - g) * N.inv_cdf(1 - 1 / k) + g * N.inv_cdf(1 - 1 / (k * math.e))


def main() -> None:
    v5e, v5e_sha = _load(V5E)
    fj, fj_sha = _load(A1)
    res: dict = {"inputs": {"v5e_prelaunch_json_sha256": v5e_sha, "a1_feasibility_json_sha256": fj_sha},
                 "constants": {"z05": Z05, "z01": Z01, "zb80": ZB, "reg_z_win": REG_Z_WIN, "reg_z_pool": REG_Z_POOL,
                               "mde_factor_a_window": Z05 + ZB, "mde_factor_b_window": REG_Z_WIN + ZB,
                               "mde_factor_a_pooled": Z01 + ZB, "mde_factor_b_pooled": REG_Z_POOL + ZB,
                               "mde_ratio_b_over_a": (REG_Z_WIN + ZB) / (Z05 + ZB),
                               "n_ratio_b_over_a": ((REG_Z_WIN + ZB) / (Z05 + ZB)) ** 2}}

    # ---- A3
    inp = a3_inputs(v5e)
    a3 = {}
    for v in ("mom1", "rev_gap", "mom2", "mom4"):
        for cal in ("measured", "stress"):
            for opt in ("a", "b"):
                ws = {w: a3_window(inp[w], v, cal, opt) for w in ("W1", "W2")}
                pooled = a3_pooled(inp, v, cal, opt, {w: ws[w]["se"] for w in ws})
                reg = {}
                for rule in RULES:
                    reg[rule] = assign(ws["W1"]["P_voll"], ws["W2"]["P_voll"], pooled["MDE80_pooled"],
                                       PRIOR_A3, pooled["P_dec52_approx"], rule)
                reg["L2_A3_wie_registriert"] = assign(ws["W1"]["P_voll"], ws["W2"]["P_voll"],
                                                      pooled["MDE80_pooled"], PRIOR_A3,
                                                      pooled["P_dec52_approx"], "L2", dec52_built=False)
                a3[f"{v}|{cal}|{opt}"] = {
                    "windows": {w: {k: (_r(x) if isinstance(x, float) else x) for k, x in ws[w].items()}
                                for w in ws},
                    "pooled": {k: ({kk: _r(vv) for kk, vv in x.items()} if isinstance(x, dict)
                                   else (_r(x) if isinstance(x, float) else x)) for k, x in pooled.items()},
                    "P_C10_joint": _r(ws["W1"]["P_voll"] * ws["W2"]["P_voll"]),
                    "regime": reg}
    res["A3"] = a3
    # selection-ceiling interplay under (a): IC_min' against the registered stress ceiling
    ceil = {}
    for w in ("W1", "W2"):
        ceil[w] = {"ic_min_a_min_over_variants": _r(min(x * Z05 / REG_Z_WIN for x in
                   v5e["windows"][w]["noise_floor_and_threshold"]["ic_min_capped_per_variant"].values()))}
    res["A3_ic_min_a"] = ceil

    # ---- A1
    a1in = a1_inputs(fj)
    a1 = {}
    for c, d in a1in.items():
        for opt in ("a", "b"):
            e = a1_eval(d, opt, 1.0)
            reg = {rule: assign(e["P_W"]["W1"], e["P_W"]["W2"], e["MDE80_pooled"], e["prem"]["pooled"],
                                e["P_dec52_approx"], rule) for rule in RULES}
            tmin = {rule: a1_theta_min(d, opt, rule) for rule in RULES}
            segs = {rule: a1_segments(d, opt, rule) for rule in RULES}
            a1[f"{c}|{opt}"] = {"c": d["c"], "se": {k: _r(x, 2) for k, x in d["se"].items()},
                                "theta1": {"P_W": {k: _r(x, 3) for k, x in e["P_W"].items()},
                                           "MDE80_W": {k: _r(x, 1) for k, x in e["MDE80_W"].items()},
                                           "P_pooled": _r(e["P_pooled"], 3),
                                           "MDE80_pooled": _r(e["MDE80_pooled"], 1),
                                           "prem": {k: _r(x, 1) for k, x in e["prem"].items()},
                                           "P_screen": {k: _r(x, 3) for k, x in e["P_screen"].items()},
                                           "P_dec52_approx": _r(e["P_dec52_approx"], 3),
                                           "P_C10_joint": _r(e["P_C10_joint"], 3)},
                                "regime_theta1": reg, "theta_min": tmin, "regime_segments_theta": segs}
    res["A1"] = a1

    # ---- false-positive rates
    aw = {"a": 1 - PHI(Z05), "b": 1 - PHI(REG_Z_WIN)}
    fpr = {}
    for opt in ("a", "b"):
        cp = OPTIONS[opt]["crit_p"]
        fpr[opt] = {"alpha_window": aw[opt], "C10_joint": aw[opt] ** 2,
                    "pooled_alpha": 1 - PHI(cp),
                    "DEC52_joint_screens": dec52_fpr(cp, upper_band=False),
                    "DEC52_joint_screens_band": dec52_fpr(cp, upper_band=True),
                    "DEC52_joint_sign_only": dec52_fpr(cp, upper_band=False, screen_frac=0.0)}
    fpr["ratio_C10_a_over_b"] = fpr["a"]["C10_joint"] / fpr["b"]["C10_joint"]
    # pooled critical value at which the DEC-52 joint rate (screens 0.5x) equals the 0.5 % PRD 3.5 assumed
    lo, hi = 2.3, 3.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if dec52_fpr(mid, upper_band=False) > 0.005:
            lo = mid
        else:
            hi = mid
    fpr["DEC52_crit_p_for_joint_0p5pct"] = {"crit_p": mid, "pooled_alpha": 1 - PHI(mid)}
    # autocorrelation: true variance ratio c_true, SE built with c_used -> per-window alpha
    ac = {}
    for c_true in (0.60, 0.756, 1.0, 1.5, 2.439):
        row = {}
        for name, c_used in (("naiv_c1", 1.0), ("stat_floor_max1", max(1.0, c_true)), ("stat_exakt", c_true),
                             ("dec67_E4", 1 / 0.41)):
            row[name] = 1 - PHI(Z05 * math.sqrt(c_used / c_true))
        ac[str(c_true)] = row
    fpr["autocorr_alpha_window_a"] = ac
    # selection ceiling: smallest K whose Bailey/LdP expected max exceeds the window critical value
    kstar = {}
    for opt, zc in (("a", Z05), ("b", REG_Z_WIN)):
        k = 2
        while bailey_zmax(k) <= zc and k < 100000:
            k += 1
        kstar[opt] = {"K_star": k, "zmax_K_star": bailey_zmax(k), "zmax_K7": bailey_zmax(7)}
    fpr["selection_ceiling_K_star"] = kstar
    res["FPR"] = fpr

    # ---- generic admission thresholds (candidate-agnostic): two equal windows, window SE = 1,
    # prior d (same in both windows), DEC-52 pooled SE = 1/sqrt(2). Smallest d (grid 0.001) per rule.
    gen = {}
    for opt in ("a", "b"):
        cw, cp = OPTIONS[opt]["crit_w"], OPTIONS[opt]["crit_p"]
        sep = 1 / math.sqrt(2.0)
        for rule in ("L1", "L2", "L3", "L3v", "L5", "G"):
            segs: list[list] = []
            for i in range(1, 6001):
                dd = i / 1000.0
                pw = PHI(dd - cw)
                p_p = PHI(dd / sep - cp)
                ps = PHI(dd - 0.5 * cp * sep)
                reg = assign(pw, pw, (cp + ZB) * sep, dd, p_p * ps * ps, rule)
                if segs and segs[-1][2] == reg:
                    segs[-1][1] = dd
                else:
                    segs.append([dd, dd, reg])
            first_ok = next((s[0] for s in segs if s[2] != "GL-012"), None)
            gen[f"{opt}|{rule}"] = {"segments_d_in_SE": segs, "admission_d_in_SE": first_ok,
                                    "P_window_at_admission": PHI(first_ok - cw) if first_ok else None}
    res["generic_admission"] = gen

    with open(OUT, "w", encoding="ascii") as fh:
        json.dump(res, fh, indent=1, sort_keys=True, default=float)
        fh.write("\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
