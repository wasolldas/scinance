"""H-32 derivation (two-stage design): every power / MDE / assignment / handover number from the
NUISANCE of the record only (v5e prelaunch JSON, WP-7 K series), computed with power_p1.

No real IC, no panel, no outcome: inputs are
  * v5e prelaunch JSON (open artifact, never the *_L_window_sealed.json),
  * WP-7 union per-week symbol count (columns 'week' and 'n_symbols' only),
  * A1 feasibility pilot-base metadata (dates, K summary) as a cross-check.
Deterministic: no random numbers here (the synthetic sector check lives in sector_check.py).

Usage: PYTHONPATH=<repo>/src python3 h32_power.py <repo_root> <out_json>
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
from statistics import NormalDist

REPO = sys.argv[1]
OUT = sys.argv[2]
sys.path.insert(0, os.path.join(REPO, "src"))
from bybit_edge.research import power_p1 as P  # noqa: E402

N = NormalDist()
SEALED_SUFFIX = ("_L_window_sealed.json", "weekly_ic_series.csv")

V5E = os.path.join(REPO, "scinance3-impl/state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json")
V5E_SHA = "94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2"
KCSV = os.path.join(REPO, "scinance3-impl/state/runs/wp7_20260921/decile_degeneration_weekly.csv")
A1J = os.path.join(REPO, "scinance3-impl/state/herleitung_a1/feasibility.json")

VARIANTS = ("mom1", "mom2", "mom4", "rev_gap")
SIGN = {"mom1": 1.0, "mom2": 1.0, "mom4": 1.0, "rev_gap": -1.0}
WINDOWS = ("W1", "W2")
PRIOR_GRID = (0.010, 0.015, 0.020, 0.025, 0.033)
IC_GRID = (0.0, 0.004, 0.008, 0.010, 0.012, 0.015, 0.018, 0.020, 0.022, 0.025, 0.030, 0.033)
Z = P.z_krit(P.ALPHA_WINDOW)              # 1.6449
MDE_F = P.mde_factor(P.ALPHA_WINDOW)      # 2.4865
Z_A3 = P.Z_PER_WINDOW_A3_PRACTICE         # 2.4865 as threshold (A3 practice)
Z_BAND80 = N.inv_cdf(0.90)                # two-sided 80 % band: +-1.2816 SE
T_MIN_PILOT = 2.0
W2_CUT_W_JUDGED = 50

# pilot window (formation weeks; outcome weeks end 2024-06-24..06-30, before W1)
PILOT_FIRST_117 = None   # derived below from the K series (first week with K_t >= 117)
PILOT_LAST_FORMATION = "2024-06-17"
SPEC_PILOT_FIRST = "2022-04-04"
SPEC_PILOT_LAST = "2024-06-24"
# annual listing counts of the union panel (WELLE1_BEFUND_TEIL6 table "Delisting-Kohorten (gelistet / delistet)")
LISTINGS_PER_YEAR = {"2022": 86, "2023": 113, "2024": 228}


def sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def guard(path: str) -> None:
    b = os.path.basename(path)
    if b.endswith(SEALED_SUFFIX) or (b.startswith("ic_series_") and b.endswith("_UNION_REAL.csv")):
        raise SystemExit(f"REFUSED (sealed): {path}")


def r6(x):
    if isinstance(x, float):
        return float(f"{x:.6g}")
    if isinstance(x, dict):
        return {k: r6(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [r6(v) for v in x]
    return x


# ---------------------------------------------------------------- inputs
guard(V5E)
guard(KCSV)
v5e_sha = sha256(V5E)
assert v5e_sha == V5E_SHA, v5e_sha
v5e = json.load(open(V5E))
kcsv_sha = sha256(KCSV)
kweek: dict[str, int] = {}
with open(KCSV) as f:
    for row in csv.DictReader(f):
        kweek[row["week"]] = int(row["n_symbols"])     # only these two columns are read
a1 = json.load(open(A1J))
a1_base = a1["configs"]["A_dec70_1h_eingeschlossen"]["nuisance"]["bases"]["K_ge_117"]
a1_meta = {k: a1_base[k] for k in ("first_formation_week", "last_formation_week", "last_holding_week", "n_weeks", "K")}

# ---------------------------------------------------------------- K series: test windows and pilot
win = {}
for W in WINDOWS:
    w = v5e["windows"][W]
    fl = w["noise_floor_and_threshold"]["floor"]
    ks = fl["k_series"]
    mism = [wk for wk, k in zip(fl["weeks"], ks) if kweek.get(wk) != k]
    win[W] = {
        "start": w["start"], "end": w["end"], "w_judged": fl["w_judged"], "e_floor": fl["e_floor"],
        "v_floor": sum(1.0 / (k - 1) for k in ks) / len(ks),
        "k_min": min(ks), "k_median": sorted(ks)[len(ks) // 2], "k_max": max(ks),
        "k_series_matches_wp7_csv": not mism, "n_mismatch": len(mism),
        "first_judged_week": fl["weeks"][0], "last_judged_week": fl["weeks"][-1],
    }

weeks_sorted = sorted(kweek)
first117 = next(wk for wk in weeks_sorted if kweek[wk] >= 117)
first134 = next(wk for wk in weeks_sorted if kweek[wk] >= 134)
assert all(kweek[wk] >= 117 for wk in weeks_sorted if wk >= first117)


def pilot_block(first: str, last: str = PILOT_LAST_FORMATION, shrink: float = 1.0, listings_adj: bool = False):
    wks = [wk for wk in weeks_sorted if first <= wk <= last]
    ks = []
    for wk in wks:
        k = kweek[wk]
        if listings_adj:   # fm8 needs 8 valid weeks of history: drop ~8 weeks of gross listings
            k = k - 8.0 * LISTINGS_PER_YEAR[wk[:4]] / 52.0
        k = k * shrink if shrink != 1.0 else k
        ks.append(k)
    return {
        "first_formation_week": wks[0], "last_formation_week": wks[-1], "w_pilot": len(wks),
        "k_min": min(ks), "k_median": sorted(ks)[len(ks) // 2], "k_max": max(ks),
        "e_floor": sum(1.0 / math.sqrt(k - 1) for k in ks) / len(ks),
        "v_floor": sum(1.0 / (k - 1) for k in ks) / len(ks),
    }


pilot_main = pilot_block(first117)
pilot_134 = pilot_block(first134)
pilot_spec = pilot_block(SPEC_PILOT_FIRST, SPEC_PILOT_LAST)    # spec reading (incl. weeks with K < 117 and a W1 outcome week)
pilot_listadj = pilot_block(first117, listings_adj=True)

# ---------------------------------------------------------------- nuisance per variant/window (fm8, stress, 1000 rep)
nuis: dict[str, dict[str, dict]] = {v: {} for v in VARIANTS}
for W in WINDOWS:
    w = v5e["windows"][W]
    hr = w["beta_control_recommended_high_rep"]
    st = w["beta_control_method_study"]["calibrations"]["stress"]["methods"]["fm_neutral_8w"]
    n_reps_study = v5e["windows"][W]["beta_control_method_study"]["n_reps"]
    for v in VARIANTS:
        s = SIGN[v]
        free, drift = hr["stress"]["variants"][v], hr["stress_drifting"]["variants"][v]
        meas = hr["measured"]["variants"][v]
        n_sim_weeks = st["variants"][v]["n_ic_pooled"] / n_reps_study
        sd = max(free["factor_sd"], drift["factor_sd"])
        dsd = max(free["mean_ic_draws_sd"], drift["mean_ic_draws_sd"])
        m_dir = max(s * free["mean_ic_draws_mean"], s * drift["mean_ic_draws_mean"])  # more extreme in direction
        c_hat_sim = n_sim_weeks * dsd ** 2 / sd ** 2
        c_hat_bilanz = win[W]["w_judged"] * dsd ** 2 / sd ** 2
        wj = win[W]["w_judged"]
        # main design: W2 ends with the outcome week 2026-06-22..28 (blind seal DEC-96 E3) -> w_judged 50
        wj_eff = W2_CUT_W_JUDGED if W == "W2" else wj
        cut = math.sqrt(wj / wj_eff)
        se = {
            "S1_draws_sd_bindend": dsd * cut,
            "S2_c_sim_ueber_wjudged": math.sqrt(max(1.0, c_hat_sim)) * sd / math.sqrt(wj_eff),
            "S3_spec_c1": sd / math.sqrt(wj_eff),
        }
        se_uncut = {
            "S1_draws_sd_bindend": dsd,
            "S2_c_sim_ueber_wjudged": math.sqrt(max(1.0, c_hat_sim)) * sd / math.sqrt(wj),
            "S3_spec_c1": sd / math.sqrt(wj),
        }
        nuis[v][W] = {
            "sd_fm8_stress": sd, "sd_fm8_measured": meas["factor_sd"],
            "draws_sd_stress": dsd, "draws_sd_measured": meas["mean_ic_draws_sd"],
            "null_mean_dir_binding": m_dir, "null_mean_dir_free": s * free["mean_ic_draws_mean"],
            "null_mean_dir_drift": s * drift["mean_ic_draws_mean"],
            "q9936_frozen_binding": w["frozen_null_constants"]["res_quantile_binding"][v],
            "n_sim_weeks": n_sim_weeks, "c_hat_sim": c_hat_sim, "c_hat_bilanz_convention": c_hat_bilanz,
            "excess_var_F2": sd ** 2 - win[W]["v_floor"],
            "se": se, "se_uncut_w2_51": se_uncut, "w_judged_main": wj_eff,
            "ceiling_k7_stress_v5e": w["frozen_null_constants"]["ceiling_method_stress"],
        }

# ---------------------------------------------------------------- test-window power line (P-1)
SE_KEYS = ("S1_draws_sd_bindend", "S2_c_sim_ueber_wjudged", "S3_spec_c1")


def credit(v, W):
    return max(0.0, nuis[v][W]["null_mean_dir_binding"])


def thresholds(v, W, sek):
    se = nuis[v][W]["se"][sek]
    t = Z * se + credit(v, W)
    mde = P.mde80(se, Z) + credit(v, W)
    mde_a3 = P.mde80(se, Z_A3) + credit(v, W)
    return {"se": se, "threshold_T": t, "mde80": mde, "mde80_a3_praxis": mde_a3,
            "null_mean_credit": credit(v, W)}


def regime_at(v, prior, sek):
    pr = [prior - credit(v, W) for W in WINDOWS]
    se = [nuis[v][W]["se"][sek] for W in WINDOWS]
    p1 = P.assign_regime(pr, se)
    a3 = P.assign_regime_a3_practice(pr, se)
    return {
        "prior": prior, "window_power": dict(zip(WINDOWS, p1["window_power"])),
        "joint_power_product": p1["window_power_joint_product"], "regime_p1": p1["regime"],
        "dec52_gate_power_product": p1["gate_power_product"],
        "regime_a3_praxis": a3["regime"], "window_power_a3_praxis": dict(zip(WINDOWS, a3["window_power"])),
        "zugelassen_nur_durch_dec94": a3["zugelassen_nur_durch_dec94"],
    }


def breakeven(v, sek, which="p1"):
    """Smallest prior with regime C10 (P-1) or C10 under the A3 practice (bisection on power_p1)."""
    lo, hi = 0.0, 0.2
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        r = regime_at(v, mid, sek)
        ok = (r["regime_p1"] == P.REGIME_C10) if which == "p1" else (r["regime_a3_praxis"] == P.REGIME_C10)
        if ok:
            hi = mid
        else:
            lo = mid
    return hi


def first_dec52(v, sek):
    lo, hi = 0.0, 0.2
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        r = regime_at(v, mid, sek)
        if r["regime_p1"] in (P.REGIME_C10, P.REGIME_DEC52):
            hi = mid
        else:
            lo = mid
    return hi


power_table = {}
for v in VARIANTS:
    power_table[v] = {}
    for sek in SE_KEYS:
        power_table[v][sek] = {
            "thresholds": {W: thresholds(v, W, sek) for W in WINDOWS},
            "grid": [regime_at(v, p, sek) for p in PRIOR_GRID],
            "breakeven_C10_p1": breakeven(v, sek, "p1"),
            "breakeven_C10_a3_praxis": breakeven(v, sek, "a3"),
            "first_prior_dec52_or_c10": first_dec52(v, sek),
        }

# ---------------------------------------------------------------- pilot precision
def pilot_se(v, pb, f2_mult=1.0):
    f2 = max(nuis[v][W]["excess_var_F2"] for W in WINDOWS) * f2_mult
    c = max(max(1.0, nuis[v][W]["c_hat_sim"]) for W in WINDOWS)
    sd = math.sqrt(pb["v_floor"] + f2)
    se = math.sqrt(c) * sd / math.sqrt(pb["w_pilot"])
    floor_se = pb["e_floor"] / math.sqrt(pb["w_pilot"])
    return {"sd_pilot": sd, "c": c, "F2": f2, "se_pilot": max(se, floor_se), "floor_se": floor_se,
            "w_pilot": pb["w_pilot"]}


pilot = {}
for v in VARIANTS:
    pilot[v] = {
        "main_K117": pilot_se(v, pilot_main),
        "alt_K134": pilot_se(v, pilot_134),
        "spec_reading_2022-04-04_bis_2024-06-24": pilot_se(v, pilot_spec),
        "sens_listings_adjusted_K": pilot_se(v, pilot_listadj),
        "sens_F_doubled": pilot_se(v, pilot_main, f2_mult=4.0),
        "spec_naive_0.0511_sqrt117": 0.0511 / math.sqrt(117) if v == "mom1" else None,
    }

# ---------------------------------------------------------------- handover rule: operating characteristic
def handover_threshold(v, sek="S1_draws_sd_bindend"):
    return max(thresholds(v, W, sek)["mde80"] for W in WINDOWS)


def oc_for(v, reading, se_p, sek="S1_draws_sd_bindend"):
    h = handover_threshold(v, sek)
    m_p = nuis[v]["W1"]["null_mean_dir_binding"]      # pilot mechanical mean proxied by W1 stress
    if reading == "A_punkt":
        thr = max(h, T_MIN_PILOT * se_p, 1e-12)
    else:  # "B_untere_80": point - 1.2816 SE_P >= h  and  t >= 2
        thr = max(h + Z_BAND80 * se_p, T_MIN_PILOT * se_p)
    rows = []
    for ic in IC_GRID:
        p_hand = P.condition_power(ic + m_p, thr, se_p)
        wp = [P.window_power(ic + nuis[v][W]["null_mean_dir_binding"] - credit(v, W),
                             nuis[v][W]["se"][sek], Z) for W in WINDOWS]
        joint = wp[0] * wp[1]
        rows.append({"ic_true": ic, "p_handover": p_hand, "test_joint_power_c10": joint,
                     "two_stage_power": p_hand * joint, "test_window_power": dict(zip(WINDOWS, wp))})
    # IC (excess) for 50 % / 80 % handover
    ic50 = thr - m_p
    ic80 = thr - m_p + P.Z_POWER * se_p
    return {"pilot_threshold_on_point": thr, "handover_mde80_T": h, "m_pilot_proxy": m_p,
            "ic_for_50pct_handover": ic50, "ic_for_80pct_handover": ic80, "rows": rows}


oc = {}
for v in VARIANTS:
    se_p = pilot[v]["main_K117"]["se_pilot"]
    oc[v] = {"se_pilot": se_p, "A_punkt": oc_for(v, "A_punkt", se_p), "B_untere_80": oc_for(v, "B_untere_80", se_p)}

lit = {}
for v in VARIANTS:
    se_p = pilot[v]["main_K117"]["se_pilot"]
    lit[v] = {}
    for reading in ("A_punkt", "B_untere_80"):
        thr = oc[v][reading]["pilot_threshold_on_point"]
        m_p = oc[v][reading]["m_pilot_proxy"]
        lit[v][reading] = {str(ic): P.condition_power(ic + m_p, thr, se_p)
                           for ic in (0.004, 0.012, 0.020, 0.033)}

# ---------------------------------------------------------------- universe variant U1: mom1 on turnover buckets 3..10
def keep_frac(k):
    return k - (2 * k) // 10


u1 = {}
for W in WINDOWS:
    ks = v5e["windows"][W]["noise_floor_and_threshold"]["floor"]["k_series"]
    kl = [keep_frac(k) for k in ks]
    vfl = sum(1.0 / (k - 1) for k in kl) / len(kl)
    f2 = nuis["mom1"][W]["excess_var_F2"]
    sd = math.sqrt(vfl + f2)
    c = max(1.0, nuis["mom1"][W]["c_hat_sim"])
    # S1-analogue: scale the binding draws_sd by the SD ratio
    se = nuis["mom1"][W]["se"]["S1_draws_sd_bindend"] * sd / nuis["mom1"][W]["sd_fm8_stress"]
    u1[W] = {"k_min": min(kl), "k_median": sorted(kl)[len(kl) // 2], "sd": sd, "se_S1_scaled": se,
             "mde80": P.mde80(se, Z) + credit("mom1", W)}
first_liq = next(wk for wk in weeks_sorted if keep_frac(kweek[wk]) >= 117)
wks_liq = [wk for wk in weeks_sorted if first_liq <= wk <= PILOT_LAST_FORMATION]
kl_p = [keep_frac(kweek[wk]) for wk in wks_liq]
vfl_p = sum(1.0 / (k - 1) for k in kl_p) / len(kl_p)
f2 = max(nuis["mom1"][W]["excess_var_F2"] for W in WINDOWS)
c = max(max(1.0, nuis["mom1"][W]["c_hat_sim"]) for W in WINDOWS)
u1["pilot"] = {"first_formation_week_K_liq_ge_117": first_liq, "w_pilot": len(wks_liq), "k_min": min(kl_p),
               "se_pilot": math.sqrt(c) * math.sqrt(vfl_p + f2) / math.sqrt(len(wks_liq))}
u1["handover_mde80_T"] = max(u1[W]["mde80"] for W in WINDOWS)

# ---------------------------------------------------------------- selection
selection = {str(k): {"selection_z": P.selection_z(k), "effective_z": P.effective_z(P.ALPHA_WINDOW, k)}
             for k in (1, 4, 5, 7, 11, 12)}
ceiling_check = {}
for v in VARIANTS:
    ceiling_check[v] = {}
    for W in WINDOWS:
        t = thresholds(v, W, "S1_draws_sd_bindend")["threshold_T"]
        ceil7 = nuis[v][W]["ceiling_k7_stress_v5e"]
        approx4 = credit(v, W) + P.selection_z(4) * nuis[v][W]["se"]["S1_draws_sd_bindend"]
        ceiling_check[v][W] = {"threshold_T": t, "ceiling_k7_v5e_rawsigned": ceil7, "ratio_k7": ceil7 / t,
                               "approx_ceiling_k4_dirsigned": approx4, "ratio_k4": approx4 / t}

# ---------------------------------------------------------------- report rows: measured calibration, W2 cut at the seal
measured_rows = {}
for v in VARIANTS:
    measured_rows[v] = {}
    for W in WINDOWS:
        hrm = v5e["windows"][W]["beta_control_recommended_high_rep"]["measured"]["variants"][v]
        se_m = hrm["mean_ic_draws_sd"]
        m_m = max(0.0, SIGN[v] * hrm["mean_ic_draws_mean"])
        measured_rows[v][W] = {"se_draws_sd_measured": se_m, "credit": m_m, "mde80": P.mde80(se_m, Z) + m_m}
w2_cut = {}
for v in VARIANTS:
    se_unc = nuis[v]["W2"]["se_uncut_w2_51"]["S1_draws_sd_bindend"]
    w2_cut[v] = {"w_judged": 51, "se_S1": se_unc, "mde80": P.mde80(se_unc, Z) + credit(v, "W2"),
                 "mde80_main_cut": thresholds(v, "W2", "S1_draws_sd_bindend")["mde80"],
                 "binding_window_W1_unchanged": thresholds(v, "W2", "S1_draws_sd_bindend")["mde80"]
                 < thresholds(v, "W1", "S1_draws_sd_bindend")["mde80"]}

# ---------------------------------------------------------------- spec reconciliation
spec = {
    "spec_mde80_W1_stress_mom1": 0.0176, "computed_c1_no_credit": MDE_F * 0.0511 / math.sqrt(52),
    "p1_S1_with_credit_W1_mom1": thresholds("mom1", "W1", "S1_draws_sd_bindend")["mde80"],
    "p1_S2_with_credit_W1_mom1": thresholds("mom1", "W1", "S2_c_sim_ueber_wjudged")["mde80"],
    "spec_pilot_se_mom1": 0.0047, "computed_pilot_se_mom1_main": pilot["mom1"]["main_K117"]["se_pilot"],
    "spec_pilot_first_week": SPEC_PILOT_FIRST, "k_at_spec_first_week": kweek[SPEC_PILOT_FIRST],
    "first_week_K_ge_117": first117, "k_at_first117": kweek[first117],
    "first_week_K_ge_134": first134, "k_at_first134": kweek[first134],
    "spec_last_formation_week": SPEC_PILOT_LAST,
    "note_last_week": "Formationswoche 2024-06-24 haette das Outcome 2024-07-01..07-07 = erste W1-Woche; letzte zulaessige Formationswoche 2024-06-17",
}

# ---------------------------------------------------------------- F-WEEK (BY) end power, DEC-99 (7)
# p of an entry = Max-p over W1/W2 (DEC-74 (e)); approximated here by the normal p of y_W / SE_W (the run uses the
# block-permutation p with >= 10.000 permutations). A single rejection under BY with m hypotheses needs
# p <= alpha / (m * H_m), H_m = sum_{i<=m} 1/i  (conservative: no other rejection helps).
BY_ALPHA = 0.10


def by_single_threshold(m: int) -> float:
    return BY_ALPHA / (m * sum(1.0 / i for i in range(1, m + 1)))


def end_power(v, prior, m, sek="S1_draws_sd_bindend"):
    t = by_single_threshold(m)
    z_t = max(Z, N.inv_cdf(1.0 - t))
    wp = [P.window_power(prior - credit(v, W), nuis[v][W]["se"][sek], z_t) for W in WINDOWS]
    return {"by_threshold_p": t, "z_eff": z_t, "window_power": dict(zip(WINDOWS, wp)), "joint": wp[0] * wp[1]}


def mde80_by(v, m, sek="S1_draws_sd_bindend"):
    t = by_single_threshold(m)
    z_t = max(Z, N.inv_cdf(1.0 - t))
    return max(P.mde80(nuis[v][W]["se"][sek], z_t) + credit(v, W) for W in WINDOWS)


M_GRID = (1, 2, 3, 4, 11)
fweek = {"rule": "DEC-99 (7): m = Zahl der tatsaechlich getesteten (uebergebenen) Eintraege; m = 11 = alte Zaehlung, report-only",
         "by_alpha": BY_ALPHA, "p_approximation": "normal p aus y/SE je Fenster, Max-p",
         "thresholds": {str(m): by_single_threshold(m) for m in M_GRID}, "variants": {}}
for v in VARIANTS:
    mde_w = max(thresholds(v, W, "S1_draws_sd_bindend")["mde80"] for W in WINDOWS)
    fweek["variants"][v] = {
        "prior_mde80_binding": mde_w,
        "end_power_at_mde80": {str(m): end_power(v, mde_w, m) for m in M_GRID},
        "end_power_grid": {str(p): {str(m): end_power(v, p, m)["joint"] for m in M_GRID} for p in PRIOR_GRID},
        "mde80_per_window_through_by": {str(m): mde80_by(v, m) for m in M_GRID},
    }

out = {
    "inputs": {
        "v5e_prelaunch_json": {"path": "scinance3-impl/state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json", "sha256": v5e_sha},
        "wp7_k_series_csv": {"path": "scinance3-impl/state/runs/wp7_20260921/decile_degeneration_weekly.csv",
                              "sha256": kcsv_sha, "columns_read": ["week", "n_symbols"]},
        "a1_pilot_base_crosscheck": a1_meta,
        "listings_per_year_source": "state/WELLE1_BEFUND_TEIL6_2026-09-21.md Tabelle Delisting-Kohorten",
        "power_p1": "src/bybit_edge/research/power_p1.py",
        "constants": {"z_krit": Z, "mde_factor": MDE_F, "z_a3_practice": Z_A3, "z_band80": Z_BAND80,
                      "t_min_pilot": T_MIN_PILOT, "z_power": P.Z_POWER},
    },
    "windows": win,
    "pilot_windows": {"main_K117": pilot_main, "alt_K134": pilot_134, "spec_reading": pilot_spec,
                      "sens_listings_adjusted": pilot_listadj},
    "nuisance": nuis,
    "power_table": power_table,
    "pilot_precision": pilot,
    "handover_oc": oc,
    "handover_literature_band": lit,
    "universe_variant_U1_mom1_buckets_3_10": u1,
    "selection": selection,
    "ceiling_check": ceiling_check,
    "spec_reconciliation": spec,
    "report_measured_calibration": measured_rows,
    "sensitivity_W2_uncut_w_judged_51": w2_cut,
    "f_week_by_end_power": fweek,
}
with open(OUT, "w") as f:
    json.dump(r6(out), f, indent=1, sort_keys=True)
print("written", OUT)
