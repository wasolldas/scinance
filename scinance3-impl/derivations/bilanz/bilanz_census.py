"""Programme balance P-2 (2026-10-18): power census over the remaining candidates.

Nuisance only (SD, c, floor, K, literature priors) read from the case files; no outcome
statistic is computed, no panel/DVOL/trade data is loaded.  Every power / MDE / assignment
number goes through ``bybit_edge.research.power_p1`` (DEC-94 (8)); closed forms
``n = c * (z_mde * SD / prior)^2`` are printed as a cross-check only.

Run:  PYTHONPATH=/home/user/scinance/src python3 -I bilanz_census.py
Writes: scinance3-impl/state/programm_bilanz.json and tables.md (scratchpad).
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1 as pp  # noqa: E402

REPO = Path("/home/user/scinance")
STATE = REPO / "scinance3-impl" / "state"
HERE = Path(__file__).resolve().parent
OUT_JSON = STATE / "programm_bilanz.json"
OUT_TABLES = HERE / "tables.md"

SEALED = ("*_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_*_UNION_REAL.csv")
FORBIDDEN_DIRS = ("wp10a2_", "wp10a_")          # WP-10(A2)/WP-10(A) IV-RV files: never opened
ALLOWED = {
    "a3": STATE / "runs" / "wp13a_20261012_v5e" / "wp13a_prelaunch.json",
    "a1": STATE / "herleitung_a1" / "feasibility.json",
    "h27": STATE / "herleitung_h27" / "feasibility.json",
    "wp7": STATE / "runs" / "wp7_20260921" / "wp7_report.json",
}


def load(key: str) -> dict:
    path = ALLOWED[key]
    if any(fnmatch.fnmatch(path.name, p) for p in SEALED):
        raise SystemExit(f"refusing sealed file {path}")
    if any(part.startswith(FORBIDDEN_DIRS) for part in path.parts):
        raise SystemExit(f"refusing WP-10(A) file {path}")
    raw = path.read_bytes()
    SHA[key] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


SHA: dict[str, str] = {}
Z = pp.z_krit(pp.ALPHA_WINDOW)                 # 1.6449
ZMDE = pp.mde_factor(pp.ALPHA_WINDOW)          # 2.4865
ZMDE_A3 = pp.Z_PER_WINDOW_A3_PRACTICE + pp.Z_POWER   # 3.3281 (A3 practice MDE factor)


# ----------------------------------------------------------------------------
# generic solver: smallest window length n (same n in every window) that meets a criterion
# ----------------------------------------------------------------------------

def _crit_ok(name: str, priors, ses) -> bool:
    if name == "p1_c10":
        return pp.assign_regime(priors, ses)["regime"] == pp.REGIME_C10
    if name == "p1_admit":
        return pp.assign_regime(priors, ses)["regime"] != pp.REGIME_GL012
    if name == "p1_dec52_gate":
        return pp.dec52_gate_power(priors, ses)["power_product"] >= pp.POWER_TARGET - 1e-12
    if name == "a3_c10":
        return pp.assign_regime_a3_practice(priors, ses)["regime"] == pp.REGIME_C10
    if name == "a3_admit_dec52":
        return pp.assign_regime_a3_practice(priors, ses, allow_dec52=True)["regime"] != pp.REGIME_GL012
    if name == "a3_dec52_gate":
        return (pp.dec52_gate_power(priors, ses, pp.Z_POOLED_A3_PRACTICE)["power_product"]
                >= pp.POWER_TARGET - 1e-12)
    raise ValueError(name)


def solve_n(priors, se_fns, crit: str, lo: float = 1e-3, hi: float = 1e7) -> float | None:
    """Smallest continuous n with crit(priors, [f(n) for f in se_fns]) True (bisection, log)."""
    def ok(n: float) -> bool:
        return _crit_ok(crit, priors, [f(n) for f in se_fns])
    if not ok(hi):
        return None
    if ok(lo):
        return lo
    a, b = math.log(lo), math.log(hi)
    for _ in range(200):
        m = 0.5 * (a + b)
        if ok(math.exp(m)):
            b = m
        else:
            a = m
        if b - a < 1e-12:
            break
    return math.exp(b)


def se_fn(sd: float, c: float, null_at: tuple[float, float] | None = None):
    """SE(n) = max(SD * sqrt(c / n), SE_null(n)); SE_null scaled ~1/sqrt(n) from a reference."""
    def f(n: float) -> float:
        s = sd * math.sqrt(c / n)
        if null_at is not None:
            se0, n0 = null_at
            s = max(s, se0 * math.sqrt(n0 / n))
        return s
    return f


def durations(prior: float, sd: float, c: float, null_at=None) -> dict:
    """Equal-window durations under P-1 and the A3 practice (double statement DEC-94 (9))."""
    f = se_fn(sd, c, null_at)
    pr = [prior, prior]
    out = {
        "c10_p1": solve_n(pr, [f, f], "p1_c10"),
        "dec52_gate_p1": solve_n(pr, [f, f], "p1_dec52_gate"),
        "admit_p1": solve_n(pr, [f, f], "p1_admit"),
        "c10_a3": solve_n(pr, [f, f], "a3_c10"),
        "dec52_gate_a3_3168": solve_n(pr, [f, f], "a3_dec52_gate"),
        "admit_a3_with_dec52": solve_n(pr, [f, f], "a3_admit_dec52"),
        "closed_form_c10_p1": c * (ZMDE * sd / prior) ** 2,
        "closed_form_c10_a3": c * (ZMDE_A3 * sd / prior) ** 2,
    }
    n = out["c10_p1"]
    if n is not None:
        se = f(n)
        out["check_window_power_at_c10_p1"] = pp.window_power(prior, se, Z)
        out["check_mde80_at_c10_p1"] = pp.mde80(se, Z)
    return out


def r(x, k=4):
    if x is None:
        return None
    if isinstance(x, float):
        return round(x, k)
    return x


def ceil_units(x):
    return None if x is None else int(math.ceil(x - 1e-9))


# ----------------------------------------------------------------------------
# dates
# ----------------------------------------------------------------------------

def weekly_full(start: dt.date, w_per_window) -> str | None:
    """Two consecutive windows of W holding weeks from Monday `start`; full on the last Sunday."""
    if w_per_window is None:
        return None
    w = ceil_units(w_per_window)
    return (start + dt.timedelta(days=14 * w - 1)).isoformat()


def daily_full(start: dt.date, n_days, rv_tail: int = 30) -> str | None:
    if n_days is None:
        return None
    n = ceil_units(n_days)
    return (start + dt.timedelta(days=2 * n - 1 + rv_tail)).isoformat()


def last_friday(y: int, m: int) -> dt.date:
    d = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
    while d.weekday() != 4:
        d -= dt.timedelta(days=1)
    return d


def quarterly_expiries(after: dt.date, n: int) -> list[dt.date]:
    out, y = [], after.year
    while len(out) < n:
        for m in (3, 6, 9, 12):
            d = last_friday(y, m)
            if d >= after and len(out) < n:
                out.append(d)
        y += 1
    return out


START_A3_A1 = dt.date(2026, 10, 5)     # first full ISO week of 2026-10 (earliest blind start)
START_VRP = dt.date(2026, 7, 1)        # DEC-96 E1 / DEC-97 blind seal start
REC_A4 = dt.date(2026, 6, 16)          # A4 quote recording start (catalog)
A4_REG = dt.date(2027, 6, 16)          # + 12 months recording (DEC-59)


# ----------------------------------------------------------------------------
# A3 (raw rank IC, weekly; mom1 / rev_gap; measured and stress)
# ----------------------------------------------------------------------------

def a3_block(d: dict) -> dict:
    prior = 0.03
    res: dict = {"prior": prior, "prior_quelle": "PRD 4.1/5.3 IC_prior 0,03 [sek: R2 0.3C]",
                 "einheit": "Wochen je Fenster (nicht ueberlappende Halte-Wochen)",
                 "start_blind": START_A3_A1.isoformat(), "windows": {}}
    for W in ("W1", "W2"):
        w = d["windows"][W]
        nf = w["noise_floor_and_threshold"]
        floor = nf["floor"]["e_floor"]
        ks = sorted(nf["floor"]["k_series"])
        kmed = ks[len(ks) // 2] if len(ks) % 2 else 0.5 * (ks[len(ks) // 2 - 1] + ks[len(ks) // 2])
        wj = nf["w_judged"]
        bc = w["beta_control_method_study"]
        wres = {"e_floor": floor, "w_judged": wj, "K_min": ks[0], "K_median": kmed, "K_max": ks[-1],
                "cells": {}}
        for cal in ("measured", "stress"):
            for v in ("mom1", "rev_gap"):
                for meth in ("none", "fm_neutral_8w"):
                    x = bc["calibrations"][cal]["methods"][meth]["variants"][v]
                    fsd = x["factor_sd"]
                    msd = x["mean_ic_draws_sd"]
                    nrep = x["n_reps_finite"]
                    c_hat = wj * msd * msd / (fsd * fsd)
                    c_use = max(1.0, c_hat)
                    sd_eff = max(floor, fsd)
                    cell = {
                        "method": meth, "factor_sd": fsd, "sd_used": sd_eff,
                        "c_hat_null": c_hat, "c_hat_mc_rel_se": math.sqrt(2.0 / (nrep - 1)),
                        "c_used": c_use, "n_reps": nrep,
                        "dur_c1": durations(prior, sd_eff, 1.0),
                        "dur_c": durations(prior, sd_eff, c_use),
                    }
                    cell["full_dates_c"] = {k: weekly_full(START_A3_A1, cell["dur_c"][k])
                                            for k in ("c10_p1", "dec52_gate_p1", "c10_a3",
                                                      "dec52_gate_a3_3168")}
                    # window report on the historical W (SE with registered w_judged), P-1 + A3
                    se_w = sd_eff / math.sqrt(wj)
                    cell["hist_se"] = se_w
                    cell["hist_power_p1"] = pp.window_power(prior, se_w, Z)
                    cell["hist_power_a3"] = pp.window_power(prior, se_w, pp.Z_PER_WINDOW_A3_PRACTICE)
                    cell["hist_mde80_p1"] = pp.mde80(se_w, Z)
                    cell["hist_mde80_a3"] = pp.mde80(se_w, pp.Z_PER_WINDOW_A3_PRACTICE)
                    # breadth lever (only for the raw IC): SD^2 = floor^2 + F^2 (additive approx.)
                    if meth == "none":
                        f2 = max(fsd * fsd - floor * floor, 0.0)
                        lev = {}
                        for mult in (1, 2, 4, None):
                            if mult is None:
                                fl = 0.0
                                key = "K_inf"
                            else:
                                fl = floor * math.sqrt((kmed - 1.0) / (mult * kmed - 1.0))
                                key = f"K_x{mult}"
                            sdk = math.sqrt(f2 + fl * fl)
                            lev[key] = {"floor": fl, "sd": sdk,
                                        "c10_p1": solve_n([prior] * 2, [se_fn(sdk, c_use)] * 2, "p1_c10"),
                                        "c10_a3": solve_n([prior] * 2, [se_fn(sdk, c_use)] * 2, "a3_c10")}
                        cell["breadth_lever"] = {"factor_component_sd": math.sqrt(f2), "levels": lev}
                    wres["cells"][f"{cal}|{v}|{meth}"] = cell
        res["windows"][W] = wres
    # historical W1/W2 assignment (report only: DEC-94 not retroactive, GL-032 stands)
    hist = {}
    for cal in ("measured", "stress"):
        for v in ("mom1", "rev_gap"):
            ses = [res["windows"][W]["cells"][f"{cal}|{v}|none"]["hist_se"] for W in ("W1", "W2")]
            a = pp.assign_regime_a3_practice([prior, prior], ses, exact_report=False)
            hist[f"{cal}|{v}"] = {"ses": ses, "p1_regime": a["p1_regime"],
                                  "p1_window_power": a["p1"]["window_power"],
                                  "p1_gate_product": a["p1"]["gate_power_product"],
                                  "a3_regime": a["regime"], "a3_window_power": a["window_power"]}
    res["historisch_W1_W2_bericht"] = hist
    # prior sensitivity (illustration band, no source): binding cell W1 stress mom1
    b = res["windows"]["W1"]["cells"]["stress|mom1|none"]
    sens = {}
    for p in (0.02, 0.025, 0.03, 0.04):
        sens[str(p)] = {"c10_p1": solve_n([p, p], [se_fn(b["sd_used"], b["c_used"])] * 2, "p1_c10"),
                        "c10_a3": solve_n([p, p], [se_fn(b["sd_used"], b["c_used"])] * 2, "a3_c10")}
    res["prior_sensitivitaet_W1_stress_mom1"] = sens
    # selection ceiling DEC-94 (7): z = max(z_krit, z_max(K))
    selk = {}
    for K in (1, 2, 7, 12, 20):
        ze = pp.effective_z(pp.ALPHA_WINDOW, K)
        sd_b, c_b = b["sd_used"], b["c_used"]
        # smallest W with window power >= 0.80 at z_eff (both windows equal)
        def ok(n, ze=ze, sd_b=sd_b, c_b=c_b):
            return pp.window_power(prior, sd_b * math.sqrt(c_b / n), ze) >= pp.POWER_TARGET - 1e-12
        lo, hi = 1e-3, 1e7
        for _ in range(200):
            m = math.sqrt(lo * hi)
            if ok(m):
                hi = m
            else:
                lo = m
        selk[str(K)] = {"z_eff": ze, "selection_z": pp.selection_z(K), "c10_weeks": hi}
    res["selektions_K_W1_stress_mom1"] = selk
    return res


# ----------------------------------------------------------------------------
# A1 (funding long leg D1 vs universe hedge; weekly)
# ----------------------------------------------------------------------------

def a1_block(d: dict) -> dict:
    A = d["configs"]["A_dec70_1h_eingeschlossen"]
    inp = A["power"]["inputs"]
    phi = inp["phi"]
    sets = A["formationsseitige_sensitivitaeten"]["sets"]
    spreads = {
        "nuisance_2022_04_2024_06": sets["nuisance_K_ge_117"]["spread_bp"]["all"]["mean"],
        "W1": sets["W1"]["spread_bp"]["all"]["mean"],
        "W2_ohne_1h": sets["W2"]["spread_bp"]["excl_any_1h_day"]["mean"],
        "W2": sets["W2"]["spread_bp"]["all"]["mean"],
    }
    sds = {"P1_nuisance_direkt": inp["sigma_projections"]["W1"]["P1_direct_nuisance_bp"],
           "W1_projektion_bindend": inp["sigma_projections"]["W1"]["binding_bp"]}
    cs = {"c1_P1": 1.0, "c_DEC67_E4": inp["c_options"]["c_dec67_E4"]}
    res = {"phi": phi, "spreads_bp": spreads, "sd_bp": sds, "c": cs,
           "c_hat_teststatistik": {"mbb": inp["c_options"]["c_mbb_measured"]},
           "einheit": "Wochen je Fenster", "start_blind": START_A3_A1.isoformat(), "grid": {}}
    for sk, sp in spreads.items():
        for th in (0.5, 0.77, 1.0):
            prem = sp * phi * th
            for sdk, sd in sds.items():
                for ck, c in cs.items():
                    dur = durations(prem, sd, c)
                    res["grid"][f"{sk}|theta={th}|{sdk}|{ck}"] = {
                        "prem_bp": prem, "dur": dur,
                        "full_c10_p1": weekly_full(START_A3_A1, dur["c10_p1"]),
                        "full_c10_a3": weekly_full(START_A3_A1, dur["c10_a3"]),
                    }
    # historical W1/W2 (report only, DEC-94 not retroactive; GL-033 stands on theta UNBELEGT)
    g = A["power"]["grid"]
    hist = {}
    for ck in ("c1_binding", "c_dec67_E4"):
        gg = g[f"{ck}|theta=1.0"]
        priors = [gg["W1"]["prem_bp"], gg["W2"]["prem_bp"]]
        ses = [gg["W1"]["se_bp"], gg["W2"]["se_bp"]]
        a = pp.assign_regime_a3_practice(priors, ses)
        # theta_min under P-1 (smallest theta admitted)
        lo, hi = 0.0, 5.0
        for _ in range(100):
            m = 0.5 * (lo + hi)
            if pp.assign_regime([m * p for p in priors], ses)["regime"] != pp.REGIME_GL012:
                hi = m
            else:
                lo = m
        hist[ck] = {"priors_theta1": priors, "ses": ses, "p1_regime": a["p1_regime"],
                    "p1_window_power": a["p1"]["window_power"],
                    "p1_gate_product": a["p1"]["gate_power_product"],
                    "a3_regime": a["regime"], "theta_min_p1": hi}
    res["historisch_W1_W2_bericht"] = hist
    # unequal windows (W1-like then W2-like prior), c = 1: DEC-52 can help here
    unequal = {}
    for th in (0.77, 1.0):
        p1_ = spreads["W1"] * phi * th
        p2_ = spreads["W2"] * phi * th
        f1 = se_fn(sds["W1_projektion_bindend"], 1.0)
        f2 = se_fn(sds["P1_nuisance_direkt"], 1.0)
        unequal[f"theta={th}"] = {
            "priors": [p1_, p2_],
            "c10_p1": solve_n([p1_, p2_], [f1, f2], "p1_c10"),
            "admit_p1": solve_n([p1_, p2_], [f1, f2], "p1_admit"),
            "c10_a3": solve_n([p1_, p2_], [f1, f2], "a3_c10"),
            "admit_a3_with_dec52": solve_n([p1_, p2_], [f1, f2], "a3_admit_dec52"),
        }
    res["ungleiche_fenster_W1_dann_W2"] = unequal
    # hedge lever: residual SD after A3 factors + market (nuisance R^2)
    r2 = A["nuisance"]["bases"]["K_ge_117"]["a3_factor_regression"]
    res["hedge_hebel_quelle"] = "nuisance.bases.K_ge_117.a3_factor_regression (nur R^2 und Residual-SD)"
    res["hedge_hebel"] = {k: {"r2": v["r2"], "resid_sd_bp": v["resid_dispersion"]["sd_bp"],
                              "resid_mbb_ratio": v["resid_dispersion"]["mbb_variance_ratio"]}
                          for k, v in r2.items() if isinstance(v, dict) and "r2" in v}
    # duration with the residual SD ratio (nuisance basis) applied to the binding SD, theta 1, W1 spread
    ratio = (res["hedge_hebel"]["total_on_mkt_mom1_mom2_mom4_rev"]["resid_sd_bp"]
             / sds["P1_nuisance_direkt"])
    prem1 = spreads["W1"] * phi
    res["hedge_hebel_dauer_theta1_W1"] = {
        "sd_ratio": ratio,
        "ohne": durations(prem1, sds["W1_projektion_bindend"], 1.0),
        "mit": durations(prem1, sds["W1_projektion_bindend"] * ratio, 1.0)}
    return res


# ----------------------------------------------------------------------------
# H-27 / VRP (daily, overlapping 30-day targets)
# ----------------------------------------------------------------------------

def h27_block(d: dict) -> dict:
    nu = d["nuisance"]
    btc = nu["BTC"]["S1"]
    leg = nu["LEG_MEAN"]["S1"]
    pri = d["power"]["configs"]["BTC/S1"]["priors"]
    pri_leg = d["power"]["configs"]["LEG_MEAN/S1"]["priors"]
    null365 = d["nullwelt"]["BTC"]["windows"]["365"]["S1"]["se_null_at_ref"]
    sd, c_bind = btc["sd"], btc["c_bind"]
    c_cons = 18.6          # REVIEW_H27 B-2 consensus (tapered ACF sum), [Review]
    c_bart = btc["c_bartlett"]["120"]
    sd_hf = 15.1           # REVIEW_H27 B-1: noise-free RV estimate, UNBELEGT
    se_null_hf = 1.39      # REVIEW_H27 B-1: noise-free SE_null at n 365
    res = {"einheit": "Tage je Fenster (IV-Tage, 30 Tage RV-Nachlauf)",
           "start_blind": START_VRP.isoformat(),
           "inputs": {"sd_S1_BTC": sd, "c_bind_P3": c_bind, "c_konsens_review": c_cons,
                      "c_bartlett_120": c_bart, "sd_hf_rv_unbelegt": sd_hf,
                      "se_null_365_at_ref": null365, "se_null_hf_365": se_null_hf,
                      "sd_leg_mean": leg["sd"], "c_leg_mean": leg["c_bind"],
                      "corr_btc_eth_S1": nu["corr_btc_eth"]["S1"],
                      "monthly_sd": btc["monthly"]["sd_m"], "monthly_acf1": btc["monthly"]["acf1"],
                      "monthly_c_bind": btc["monthly"]["c_bind_m"],
                      "priors_btc": pri, "priors_leg_mean": pri_leg},
           "configs": {}}
    configs = {
        "ref_daily_cc_c_bind": (sd, c_bind, (null365, 365)),
        "daily_cc_c_konsens": (sd, c_cons, (null365, 365)),
        "hf_rv_c_bind": (sd_hf, c_bind, (se_null_hf, 365)),
        "hf_rv_c_konsens": (sd_hf, c_cons, (se_null_hf, 365)),
        "leg_mean_btc_eth": (leg["sd"], leg["c_bind"], None),
    }
    for ck, (s, c, na) in configs.items():
        pr = pri_leg if ck == "leg_mean_btc_eth" else pri
        for pk in ("pi2_central", "pi2_low", "pi2_high", "pi1"):
            dur = durations(pr[pk], s, c, na)
            res["configs"][f"{ck}|{pk}"] = {
                "prior": pr[pk], "sd": s, "c": c, "dur": dur,
                "full_c10_p1": daily_full(START_VRP, dur["c10_p1"]),
                "full_dec52_gate_p1": daily_full(START_VRP, dur["dec52_gate_p1"]),
                "full_c10_a3": daily_full(START_VRP, dur["c10_a3"]),
            }
    # non-overlapping monthly targets: one observation per 30 days, c_m = 1 (no credit)
    m_sd, m_c = btc["monthly"]["sd_m"], max(1.0, btc["monthly"]["c_bind_m"])
    mon = {}
    for pk in ("pi2_central", "pi2_high"):
        dur = durations(pri[pk], m_sd, m_c)
        mon[pk] = {"dur_months": dur, "c10_p1_days": None if dur["c10_p1"] is None else 30 * dur["c10_p1"],
                   "full_c10_p1": daily_full(START_VRP, None if dur["c10_p1"] is None else 30 * dur["c10_p1"])}
        # power at 12 months (12 monthly obs) for comparison with the overlapping design
        se12 = m_sd * math.sqrt(m_c / 12.0)
        mon[pk]["power_12m_p1"] = pp.window_power(pri[pk], se12, Z)
    se_ov = max(sd * math.sqrt(c_bind / 365.0), null365)
    mon["overlap_power_12m_p1"] = pp.window_power(pri["pi2_central"], se_ov, Z)
    res["monatsziele_nicht_ueberlappend"] = mon
    # theoretical two-leg gain with equal SD/prior and correlation rho (DEC-62 E3)
    res["zwei_beine_theorie"] = {
        f"rho={rho}": {"varianzfaktor": (1.0 + rho) / 2.0,
                       "dur": durations(pri["pi2_central"], sd * math.sqrt((1.0 + rho) / 2.0), c_bind,
                                        (null365, 365))}
        for rho in (0.83, 0.88, 0.907)}
    return res


# ----------------------------------------------------------------------------
# A2 (event design; sigma unmeasured -> formula + PRD working values)
# ----------------------------------------------------------------------------

def a2_block(rho_btc_eth: float) -> dict:
    sigma30 = 36.0     # PRD 5.2 working value (BTC daily vol 2.5 % assumption), UNGEMESSEN
    res = {"formel": "SE(Delta) = sqrt( sigma30^2*(1+rho)/(2*N) + SE_placebo^2 );  "
                     "N_C10 ~ (1+rho)/2 * (2,4865*sigma30)^2 / (prior^2 - (2,4865*SE_placebo)^2)",
           "sigma30_arbeitswert_bp": sigma30, "rho_btc_eth_30min": rho_btc_eth,
           "sigma30_status": "UNGEMESSEN (PRD-Arbeitswert aus 2,5 % Tagesvol, BTC-only)",
           "rows": {}}
    # PRD placebo SE per 12-month window: weekly P2 1,93 bp; monthly P1 5,40 bp
    for label, n_per_year, se_pl_year in (("woechentlich", 52, 1.93), ("monatlich", 12, 5.40)):
        for years in (1, 2, 3):
            n = n_per_year * years
            se_ev = sigma30 * math.sqrt((1.0 + rho_btc_eth) / 2.0) / math.sqrt(n)
            se_pl = se_pl_year / math.sqrt(years)
            se = math.sqrt(se_ev ** 2 + se_pl ** 2)
            row = {"N_je_Fenster": n, "se_event": se_ev, "se_placebo": se_pl, "se_delta": se,
                   "mde80_p1": pp.mde80(se, Z), "mde80_a3": pp.mde80(se, pp.Z_PER_WINDOW_A3_PRACTICE)}
            if label == "monatlich":
                prior = 16.5
                row["prior_sek"] = prior
                a = pp.assign_regime_a3_practice([prior, prior], [se, se])
                row["power_p1"] = a["p1"]["window_power"][0]
                row["regime_p1"] = a["p1_regime"]
                row["regime_a3"] = a["regime"]
            res["rows"][f"{label}|{years}J"] = row
    # minimal window length (years) for monthly expiries at prior 16.5 [sek]
    def se_m(years):
        n = 12 * years
        return math.sqrt((sigma30 ** 2) * (1 + rho_btc_eth) / (2 * n) + (5.40 ** 2) / years)
    res["monatlich_prior_16_5_jahre_je_fenster"] = {
        "c10_p1": solve_n([16.5, 16.5], [se_m, se_m], "p1_c10"),
        "c10_a3": solve_n([16.5, 16.5], [se_m, se_m], "a3_c10")}
    # generic: events per window for C10 as a function of prior/sigma30 (placebo ignored, lower bound)
    gen = {}
    for ratio in (0.25, 0.33, 0.5):
        sd_cluster = math.sqrt((1 + rho_btc_eth) / 2.0)
        gen[str(ratio)] = {
            "N_c10_p1": solve_n([ratio, ratio], [se_fn(sd_cluster, 1.0)] * 2, "p1_c10"),
            "N_c10_a3": solve_n([ratio, ratio], [se_fn(sd_cluster, 1.0)] * 2, "a3_c10")}
    res["N_je_Fenster_nach_prior_durch_sigma30"] = gen
    return res


# ----------------------------------------------------------------------------
# A4 (cycles; sigma_w unmeasured -> formula)
# ----------------------------------------------------------------------------

def a4_block() -> dict:
    gen = {}
    for ratio in (0.5, 0.75, 1.0, 1.5):
        gen[str(ratio)] = {
            "N_c10_p1": solve_n([ratio, ratio], [se_fn(1.0, 1.0)] * 2, "p1_c10"),
            "N_c10_a3": solve_n([ratio, ratio], [se_fn(1.0, 1.0)] * 2, "a3_c10"),
            "N_dec52_gate_p1": solve_n([ratio, ratio], [se_fn(1.0, 1.0)] * 2, "p1_dec52_gate")}
    exps = quarterly_expiries(A4_REG, 61)
    res = {"formel": "MDE80 = 2,4865 * sigma_w * sqrt(c / N);  N_C10 = c * (2,4865 * sigma_w / prior)^2",
           "sigma_w_status": "UNGEMESSEN", "prior_status": "UNBELEGT",
           "aufzeichnung_seit": REC_A4.isoformat(), "registrierbar_fruehestens": A4_REG.isoformat(),
           "quartalsverfaelle_ab_registrierung": [e.isoformat() for e in exps[:13]],
           "voll_nach_N_zyklen_je_fenster": {str(n): exps[2 * n].isoformat() for n in (4, 6, 7, 11, 25)},
           "N_je_Fenster_nach_prior_durch_sigma_w": gen,
           "prd_design_4_zyklen_je_fenster_voll": exps[8].isoformat(),
           "mde80_4_zyklen_in_sigma_w": pp.mde80(1.0 / 2.0, Z),
           "mde80_8_zyklen_in_sigma_w": pp.mde80(1.0 / math.sqrt(8.0), Z)}
    return res


# ----------------------------------------------------------------------------
# programme-wide rule options (generic factors; DEC-94 pattern)
# ----------------------------------------------------------------------------

def rule_options() -> dict:
    base = 2.0 * pp.mde_factor(0.05, 0.80) ** 2      # two windows, C10 under P-1
    out = {}

    def add(key, label, total_units_factor, fp_joint, power_joint_at_prior, richtung):
        out[key] = {"label": label, "daten_faktor_gesamt": total_units_factor / base,
                    "fp_gemeinsam": fp_joint, "power_gemeinsam_am_prior": power_joint_at_prior,
                    "richtung": richtung}
    add("O0_geltend", "P-1: zwei Fenster, je alpha 0,05, je Power 0,80",
        base, 0.05 ** 2, 0.80 ** 2, "-")
    for pw in (0.5, 0.6, 0.7):
        add(f"O1_power_{pw}", f"Power-Ziel {pw} je Fenster (alpha unveraendert)",
            2.0 * pp.mde_factor(0.05, pw) ** 2, 0.05 ** 2, pw ** 2, "Testbarkeit")
    add("O2_alpha_0.10", "alpha 0,10 je Fenster, Power 0,80",
        2.0 * pp.mde_factor(0.10, 0.80) ** 2, 0.10 ** 2, 0.64, "Testbarkeit")
    add("O3_ein_fenster_0.05", "ein Fenster statt zwei, alpha 0,05, Power 0,80",
        pp.mde_factor(0.05, 0.80) ** 2, 0.05, 0.80, "Testbarkeit")
    add("O4_ein_fenster_0.01", "ein Fenster, alpha 0,01, Power 0,80",
        pp.mde_factor(0.01, 0.80) ** 2, 0.01, 0.80, "Testbarkeit")
    add("O5_ein_fenster_0.0025", "ein Fenster, alpha 0,0025 (gleiche Gesamtrate wie C.10), Power 0,80",
        pp.mde_factor(0.0025, 0.80) ** 2, 0.0025, 0.80, "neutral (Rate gleich)")
    pj = math.sqrt(0.80)
    add("O6_gemeinsame_power_0.80", "zwei Fenster, gemeinsame Power 0,80 (je Fenster 0,894)",
        2.0 * pp.mde_factor(0.05, pj) ** 2, 0.05 ** 2, 0.80, "Strenge")
    add("O7_a3_praxis", "A3-Praxis (Schwelle 2,4865 SE je Fenster), Power 0,80",
        2.0 * (pp.Z_PER_WINDOW_A3_PRACTICE + pp.Z_POWER) ** 2, (1 - pp._N.cdf(2.4865)) ** 2, 0.64,
        "Strenge")
    return out


def _n_for(prior: float, sd: float, c: float, alpha: float, power: float) -> float:
    """Smallest n with window_power(prior, SD*sqrt(c/n), z_krit(alpha)) >= power (power_p1)."""
    z = pp.z_krit(alpha)
    lo, hi = 1e-6, 1e9
    for _ in range(300):
        m = math.sqrt(lo * hi)
        if pp.window_power(prior, sd * math.sqrt(c / m), z) >= power - 1e-12:
            hi = m
        else:
            lo = m
    return hi


def options_per_candidate(a3: dict, a1: dict, h27: dict) -> dict:
    cell = a3["windows"]["W1"]["cells"]["stress|mom1|none"]
    cases = {
        "A3_W1_stress_mom1": (0.03, cell["sd_used"], cell["c_used"], "weekly", START_A3_A1),
        "A3_fm8_W1_stress_mom1": (0.03, a3["windows"]["W1"]["cells"]["stress|mom1|fm_neutral_8w"]["sd_used"],
                                  a3["windows"]["W1"]["cells"]["stress|mom1|fm_neutral_8w"]["c_used"],
                                  "weekly", START_A3_A1),
        "A1_W1spread_theta1_c1": (a1["spreads_bp"]["W1"] * a1["phi"], a1["sd_bp"]["W1_projektion_bindend"],
                                  1.0, "weekly", START_A3_A1),
        "H27_ref": (h27["inputs"]["priors_btc"]["pi2_central"], h27["inputs"]["sd_S1_BTC"],
                    h27["inputs"]["c_bind_P3"], "daily", START_VRP),
    }
    opts = {
        "O0_geltend": (0.05, 0.80, 2), "O1_power_0.5": (0.05, 0.50, 2), "O1_power_0.6": (0.05, 0.60, 2),
        "O1_power_0.7": (0.05, 0.70, 2), "O2_alpha_0.10": (0.10, 0.80, 2),
        "O3_ein_fenster_0.05": (0.05, 0.80, 1), "O4_ein_fenster_0.01": (0.01, 0.80, 1),
        "O5_ein_fenster_0.0025": (0.0025, 0.80, 1), "O6_gemeinsame_power_0.80": (0.05, math.sqrt(0.8), 2),
    }
    out = {}
    for ck, (prior, sd, c, unit, start) in cases.items():
        row = {}
        for ok, (alpha, power, nwin) in opts.items():
            n = _n_for(prior, sd, c, alpha, power)
            nn = int(math.ceil(n - 1e-9))
            if unit == "weekly":
                full = (start + dt.timedelta(days=7 * nwin * nn - 1)).isoformat()
            else:
                full = (start + dt.timedelta(days=nwin * nn - 1 + 30)).isoformat()
            row[ok] = {"n_je_fenster": n, "fenster": nwin, "voll": full}
        out[ck] = row
    return out


# ----------------------------------------------------------------------------
# static sections (Teil B / Teil C / UNBELEGT); numbers refer to the computed blocks
# ----------------------------------------------------------------------------

def static_sections() -> dict:
    datenbedarf = [
        {"id": "B-1", "prio": 1, "strom": "Variante B: bybit/rest.kline1d symbol=ALL, bybit/rest.instruments "
         "symbol=ALL (Tagesschnappschuss), Funding aller Perps als eigener Strom",
         "symbole": "alle linearen USDT-Perps (~820 aktiv)", "aufloesung": "1 Tag; Funding je Abrechnung",
         "zeitraum": "Backfill 2026-09-29..heute lueckenlos, dann taeglich laufend, selbstheilend",
         "kandidat": "A3, A1 (blinde Fenster ab 2026-10-05); PIT/Survivorship; BTC/ETH-Tagesschluss fuer VRP",
         "power": "Voraussetzung jedes blinden A3/A1-Fensters; siehe A3.*.full_dates_c, A1.grid",
         "irreversibel": True, "volumen": "< 5 MB/Tag"},
        {"id": "B-2", "prio": 2, "strom": "A4: Inhaltsprobe bybit/tickers (datierte Futures, Snapshot/Delta, "
         "Bid/Ask mit und ohne '1'); ggf. REST-Schnappschuss /v5/market/tickers alle 15 min; "
         "/v5/market/delivery-price; instruments-info linear+inverse taeglich",
         "symbole": "alle datierten Kontrakte, mindestens BTC/ETH, plus Perps", "aufloesung": "15 min / taeglich",
         "zeitraum": "laufend seit 2026-06-16 (Probe), Schnappschuss ab sofort, Settlement-Backfill",
         "kandidat": "A4 (sigma_w ab 2027-06-16), V-4(b)",
         "power": "UNBELEGT bis sigma_w gemessen; siehe A4", "irreversibel": True, "volumen": "~10 MB/Monat"},
        {"id": "B-3", "prio": 3, "strom": "bybit/rest.kline1m (GET /v5/market/kline interval 1)",
         "symbole": "BTCUSDT, ETHUSDT", "aufloesung": "1 min",
         "zeitraum": "Backfill 2021-03-01..heute (Probe der Historientiefe zuerst; optional ab 2020-03-25), "
                     "dann taeglich laufend",
         "kandidat": "VRP HF-RV-Nuisance (Vorperiode <= 2024-05-31); A2 sigma30/Placebo/r_pre",
         "power": "H27.configs hf_rv_* (UNBELEGT bis Messung)", "irreversibel": False,
         "volumen": "~5,9 Mio Zeilen Backfill, ~0,1-0,3 GB, ~5.900 REST-Aufrufe"},
        {"id": "B-4", "prio": 4, "strom": "Deribit public/get_delivery_prices, public/get_instruments (expired), "
         "public/get_last_settlements_by_currency", "symbole": "BTC, ETH", "aufloesung": "je Verfall",
         "zeitraum": "Backfill ab 2019 (mind. ab 2020-03-25), laufend",
         "kandidat": "A2 (V-5a, Datenteil V-5c, Placebo-Kalender)", "power": "A2 (Prior UNBELEGT)",
         "irreversibel": False, "volumen": "< 10 MB"},
        {"id": "B-5", "prio": 5, "strom": "Inhaltsprobe Options-Ticker (deribit/tickers, markprice.options, "
         "Bybit-Optionen im tickers-Strom); Ketten-Luecken-Karte R3-K-37 Stufe 1",
         "symbole": "BTC, ETH", "aufloesung": "wie aufgezeichnet", "zeitraum": "laeuft seit 2026-06-16",
         "kandidat": "A5 (E.6 (b)), H-26b", "power": "UNBELEGT", "irreversibel": True, "volumen": "laeuft"},
        {"id": "B-6", "prio": None, "strom": "Binance-Perp-Panel als zweites Universum - NICHT beauftragen",
         "kandidat": "A3, A1", "power": "A3 <= -14 % (K -> unendlich, bindend), gleiche Coins ~0; A1 ~0"},
        {"id": "B-7", "prio": None, "strom": "laeuft unveraendert: deribit/dvol BTC/ETH, bybit/publicTrade BTC/ETH",
         "kandidat": "jede kuenftige VRP-Hypothese auf blinden Fenstern"},
    ]
    optionen = [
        {"id": 1, "titel": "Recording-first mit vorab fixierten Entsperrdaten", "richtung": "keine Regel bewegt",
         "kosten": "1,5..5 Jahre ohne Urteil; Siegel-Pflege; Daten gering"},
        {"id": 2, "titel": "Ereignis-/Einheiten-Designs vorziehen (A2 nach V-5b/c, A4 nach 12 Monaten)",
         "richtung": "Testbarkeit durch Design, keine Regel bewegt", "kosten": "Recherche V-5b/c, V-4; B-2..B-4"},
        {"id": 3, "titel": "HF-Datenweg VRP (B-3, neue Hypothese)",
         "richtung": "Testbarkeit (Schaetzerwahl nach GL-034), Etikett noetig",
         "kosten": "klein; verbraucht die blinden VRP-Fenster"},
        {"id": 4, "titel": "programmweite Regelaenderung - nur ausgewiesen, nicht empfohlen",
         "richtung": "je Zeile in regel_optionen", "kosten": "Fehlerrate/Informationsgehalt, Etikett DEC-94-Muster"},
        {"id": 5, "titel": "Pause/Abschluss 3.0 mit Bilanz", "richtung": "neutral",
         "kosten": "kein Ergebnis; Sunset-Review PRD 8.3"},
    ]
    unbelegt = [
        "A3-Prior 0,03 [sek], kein Band", "Prior des beta-neutralisierten IC (fm8)",
        "SD des kuenftigen A3-Fensters (Annahme W1-stress)", "theta (A1)", "Spread-Regime kuenftiger A1-Fenster",
        "VRP-Prior-Niveau (Band 7,0..13,7), L-1-Volltext, ETH-Prior", "HF-RV-SD 15,1 und ihr c",
        "1-min-Historientiefe Bybit", "A2: sigma30, V-5a/b/c", "A4: sigma_w, Wedge-Prior, w_null, V-4, tickers-Inhalt",
        "A5: V-4, Spread-Zensus, H-26-Verdikt",
        "H-26: done_days-Zaehlung, Lesart nachgeladener Tage, Kollision mit Blind-Siegel DEC-96 E3",
        "Verfuegbarkeitsdatum Variante B", "A3-Breite: additive Zerlegung ist Naeherung",
    ]
    return {"datenbedarf": datenbedarf, "entscheidungsoptionen": optionen, "unbelegt": unbelegt,
            "start_annahmen": {"A3_A1": START_A3_A1.isoformat(), "VRP": START_VRP.isoformat(),
                               "A4_aufzeichnung": REC_A4.isoformat(), "A4_registrierbar": A4_REG.isoformat()}}


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def main() -> None:
    a3 = load("a3")
    a1 = load("a1")
    h27 = load("h27")
    wp7 = load("wp7")
    e = wp7["extra"]
    wp7_out = {"sd_null_per_window": wp7["findings"]["b1_b2"]["sd_null_per_window"],
               "sd_null_pooled": wp7["findings"]["b1_b2"]["sd_null_pooled"],
               "k_per_week": e["k_per_week"], "sigma_ls": e["sigma_ls"]["sigma_ls"],
               "n_eff_w52": e["n_eff_windows"]["w52"]["n_eff"],
               "n_eff_w104": e["n_eff_windows"]["w104"]["n_eff"],
               "funding_autocorr_lag1": e["funding_autocorrelation_dec58"]["median_autocorr"]["lag1"],
               "rho_btc_eth_30min_dec67": 0.815}
    out = {
        "titel": "Programm-Bilanz P-2: Power-Zensus (Nuisance-only)",
        "stand": "2026-10-18",
        "etikett": ("Nur Nuisance-Groessen aus den Akten (SD, c, Boden, K, Literatur-Prior); keine Outcome-"
                    "Statistik, keine Siegeldatei, keine WP-10(A)/(A2)-IV-RV-Datei geoeffnet, kein Panel-/DVOL-/"
                    "Trade-Laden; Blind-Siegel DEC-96 E3 gewahrt. Alle Power-/MDE-/Zuordnungszahlen mit "
                    "bybit_edge.research.power_p1."),
        "konvention": {"z_krit_fenster": Z, "mde_faktor_p1": ZMDE, "z_krit_dec52_gepoolt": pp.Z_KRIT_POOLED_DEC52,
                       "a3_praxis_schwelle": pp.Z_PER_WINDOW_A3_PRACTICE,
                       "a3_praxis_mde_faktor": ZMDE_A3, "a3_praxis_gepoolt": pp.Z_POOLED_A3_PRACTICE,
                       "power_ziel": pp.POWER_TARGET,
                       "formel": "n_C10 = c * (z_mde * SD / prior)^2 (Gegenprobe; Quelle ist der power_p1-Loeser)"},
        "quellen_sha256": {},
        "wp7": wp7_out,
        "A3": a3_block(a3),
        "A1": a1_block(a1),
        "H27": h27_block(h27),
        "A2": a2_block(0.815),
        "A4": a4_block(),
        "regel_optionen": rule_options(),
    }
    out["regel_optionen_je_kandidat"] = options_per_candidate(out["A3"], out["A1"], out["H27"])
    out.update(static_sections())
    out["quellen_sha256"] = {str(ALLOWED[k].relative_to(REPO)): v for k, v in SHA.items()}
    out["skript"] = {"pfad": "scratchpad/bilanz/bilanz_census.py",
                     "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    OUT_JSON.write_text(json.dumps(out, indent=1, ensure_ascii=True, default=float) + "\n", encoding="ascii")
    print("wrote", OUT_JSON)


if __name__ == "__main__":
    main()
