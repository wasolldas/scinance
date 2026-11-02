"""Adversarial review of programme balance P-2: independent re-computation (nuisance only).

Reads only the four nuisance files the balance itself used (guarded: sealed names and
WP-10(A)/(A2) directories are refused).  No outcome statistic, no data loading.
Every power / assignment number via bybit_edge.research.power_p1; closed forms as cross-check.
Calendar arithmetic is done independently (ordinal day numbers, calendar module).
"""
from __future__ import annotations

import calendar
import datetime as dt
import fnmatch
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1 as pp  # noqa: E402

STATE = Path("/home/user/scinance/scinance3-impl/state")
OUT = Path(__file__).resolve().parent / "review_check.json"
SEALED = ("*_L_window_sealed.json", "weekly_ic_series.csv", "ic_series_*_UNION_REAL.csv")
FILES = {"a3": STATE / "runs/wp13a_20261012_v5e/wp13a_prelaunch.json",
         "a1": STATE / "herleitung_a1/feasibility.json",
         "h27": STATE / "herleitung_h27/feasibility.json"}
SHA = {}


def load(k):
    p = FILES[k]
    assert not any(fnmatch.fnmatch(p.name, s) for s in SEALED), p
    assert not any(part.startswith(("wp10a_", "wp10a2_")) for part in p.parts), p
    raw = p.read_bytes()
    SHA[k] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


Z = pp.z_krit(0.05)
F = pp.mde_factor(0.05)                     # 2.4865
FA3 = pp.Z_PER_WINDOW_A3_PRACTICE + pp.Z_POWER


def n_closed(prior, sd, c, f=F):
    return c * (f * sd / prior) ** 2


def smallest_int_c10(prior, sd, c, a3=False):
    """Smallest integer n per window (two equal windows) assigned C10 by power_p1."""
    n = max(1, int(n_closed(prior, sd, c, FA3 if a3 else F)) - 3)
    while True:
        se = sd * math.sqrt(c / n)
        reg = (pp.assign_regime_a3_practice([prior] * 2, [se] * 2)["regime"] if a3
               else pp.assign_regime([prior] * 2, [se] * 2)["regime"])
        if reg == pp.REGIME_C10:
            return n
        n += 1


def smallest_int_dec52gate(prior, sd, c, zp=pp.Z_KRIT_POOLED_DEC52):
    n = 1
    while True:
        se = sd * math.sqrt(c / n)
        if pp.dec52_gate_power([prior] * 2, [se] * 2, zp)["power_product"] >= 0.8 - 1e-12:
            return n
        n += 1


def full_weekly(start, w):            # two windows of w weeks, last day of last week
    return dt.date.fromordinal(start.toordinal() + 2 * 7 * w - 1).isoformat()


def full_daily(start, n, tail=30):
    return dt.date.fromordinal(start.toordinal() + 2 * n - 1 + tail).isoformat()


def quarterly_expiries_after(d0, k):
    out, y = [], d0.year
    while len(out) < k:
        for m in (3, 6, 9, 12):
            last = calendar.monthrange(y, m)[1]
            d = dt.date(y, m, last)
            d = d - dt.timedelta(days=(d.weekday() - 4) % 7)
            if d >= d0 and len(out) < k:
                out.append(d)
        y += 1
    return out


S_A3 = dt.date(2026, 10, 5)
S_VRP = dt.date(2026, 7, 1)
res = {}

# ---------------- A3 ----------------
a3 = load("a3")
a3r = {}
for W in ("W1", "W2"):
    w = a3["windows"][W]
    floor = w["noise_floor_and_threshold"]["floor"]["e_floor"]
    wj = w["noise_floor_and_threshold"]["w_judged"]
    for cal in ("measured", "stress"):
        for v in ("mom1", "rev_gap"):
            for m in ("none", "fm_neutral_8w"):
                x = w["beta_control_method_study"]["calibrations"][cal]["methods"][m]["variants"][v]
                sd = max(floor, x["factor_sd"])
                c = max(1.0, wj * x["mean_ic_draws_sd"] ** 2 / x["factor_sd"] ** 2)
                n = smallest_int_c10(0.03, sd, c)
                na3 = smallest_int_c10(0.03, sd, c, a3=True)
                a3r[f"{W}|{cal}|{v}|{m}"] = {
                    "sd": sd, "c": c, "floor": floor, "w_judged": wj,
                    "n_closed_p1": n_closed(0.03, sd, c), "n_int_c10_p1": n,
                    "n_int_c10_a3": na3, "n_int_dec52gate_p1": smallest_int_dec52gate(0.03, sd, c),
                    "full_p1": full_weekly(S_A3, n), "full_a3": full_weekly(S_A3, na3),
                    "factor_var_share": (sd ** 2 - floor ** 2) / sd ** 2 if m == "none" else None}
res["A3"] = a3r

# fm8 as primary statistic on the REZENZ windows W1/W2 themselves (sealed, no real IC computed):
# SE = SD of the 52-week mean IC over 1000 null replicates (high-rep winner run), null mean shift
fm8_hist = {}
for cal in ("measured", "stress", "stress_drifting"):
    for v in ("mom1",):
        ses, means = [], []
        for W in ("W1", "W2"):
            x = a3["windows"][W]["beta_control_recommended_high_rep"][cal]["variants"][v]
            ses.append(x["mean_ic_draws_sd"])
            means.append(x["mean_ic_draws_mean"])
        p_eff = [0.03 - max(0.0, mu) for mu in means]     # prior net of the null mean (strict)
        r1 = pp.assign_regime([0.03, 0.03], ses)
        r2 = pp.assign_regime(p_eff, ses)
        r3 = pp.assign_regime_a3_practice(p_eff, ses)
        be = max(F * s + max(0.0, mu) for s, mu in zip(ses, means))
        be_a3 = max(FA3 * s + max(0.0, mu) for s, mu in zip(ses, means))
        fm8_hist[f"{cal}|{v}"] = {"ses_W1_W2": ses, "null_means": means,
                                  "p1_regime_prior_0.03": r1["regime"], "p1_power": r1["window_power"],
                                  "p1_regime_net_of_null_mean": r2["regime"], "p1_power_net": r2["window_power"],
                                  "a3_regime_net": r3["regime"], "a3_power_net": r3["window_power"],
                                  "breakeven_prior_p1": be, "breakeven_prior_a3": be_a3}
res["A3_fm8_on_W1_W2"] = fm8_hist
# fm8 break-even prior relative to raw on future blind windows (W1-stress mom1)
raw = a3r["W1|stress|mom1|none"]; fm = a3r["W1|stress|mom1|fm_neutral_8w"]
res["A3_fm8_breakeven_vs_raw_future"] = {
    "prior_fm8_equal_duration_as_raw": 0.03 * math.sqrt(fm["n_closed_p1"] / raw["n_closed_p1"]),
    "share_of_0.03": math.sqrt(fm["n_closed_p1"] / raw["n_closed_p1"]),
    "fm8_weeks_if_prior_0.015": n_closed(0.015, fm["sd"], fm["c"]),
    "fm8_weeks_if_prior_0.02": n_closed(0.02, fm["sd"], fm["c"])}

# ---------------- A1 ----------------
a1 = load("a1")
A = a1["configs"]["A_dec70_1h_eingeschlossen"]
phi = A["power"]["inputs"]["phi"]
sd_b = A["power"]["inputs"]["sigma_projections"]["W1"]["binding_bp"]
sd_n = A["power"]["inputs"]["sigma_projections"]["W1"]["P1_direct_nuisance_bp"]
sets = A["formationsseitige_sensitivitaeten"]["sets"]
spreads = {"nuis": sets["nuisance_K_ge_117"]["spread_bp"]["all"]["mean"],
           "W1": sets["W1"]["spread_bp"]["all"]["mean"], "W2": sets["W2"]["spread_bp"]["all"]["mean"]}
a1r = {}
for sk, sp in spreads.items():
    for th in (1.0, 0.77, 0.5):
        for (sdk, sd) in (("bind", sd_b), ("nuis", sd_n)):
            n = smallest_int_c10(sp * phi * th, sd, 1.0)
            a1r[f"{sk}|{th}|{sdk}"] = {"prem": sp * phi * th, "n_closed": n_closed(sp * phi * th, sd, 1.0),
                                       "n_int": n, "full": full_weekly(S_A3, n),
                                       "n_E4": n_closed(sp * phi * th, sd, 1 / 0.41)}
res["A1"] = a1r
hed = A["nuisance"]["bases"]["K_ge_117"]["a3_factor_regression"]["total_on_mkt_mom1_mom2_mom4_rev"]
res["A1_hedge"] = {"ratio_var": (hed["resid_dispersion"]["sd_bp"] / sd_n) ** 2}

# ---------------- H-27 ----------------
h = load("h27")
b = h["nuisance"]["BTC"]["S1"]
pri = h["power"]["configs"]["BTC/S1"]["priors"]
se0 = h["nullwelt"]["BTC"]["windows"]["365"]["S1"]["se_null_at_ref"]
h27 = {}
for lab, sd, c in (("ref", b["sd"], b["c_bind"]), ("cons", b["sd"], 18.6), ("hf", 15.1, b["c_bind"]),
                   ("hf_cons", 15.1, 18.6)):
    for pk in ("pi2_central", "pi2_low", "pi2_high", "pi1"):
        n = smallest_int_c10(pri[pk], sd, c)
        ng = smallest_int_dec52gate(pri[pk], sd, c)
        na3 = smallest_int_c10(pri[pk], sd, c, a3=True)
        # SE_null never binds: ratio constant in n
        h27[f"{lab}|{pk}"] = {"n_closed": n_closed(pri[pk], sd, c), "n_int": n, "full": full_daily(S_VRP, n),
                              "n_dec52": ng, "full_dec52": full_daily(S_VRP, ng),
                              "n_a3": na3, "full_a3": full_daily(S_VRP, na3),
                              "null_binds": se0 * math.sqrt(365) > sd * math.sqrt(c)}
res["H27"] = h27
m = b["monthly"]
nm = n_closed(pri["pi2_central"], m["sd_m"], max(1.0, m["c_bind_m"]))
res["H27_monthly"] = {"months": nm, "days": 30 * nm, "ratio_vs_overlap": 30 * nm / h27["ref|pi2_central"]["n_closed"],
                      "eff_obs_per_year_overlap_c_rule": 365 / b["c_bind"], "eff_obs_per_year_overlap_c_cons": 365 / 18.6,
                      "obs_per_year_monthly": 12.0,
                      "power12_monthly": pp.window_power(pri["pi2_central"], m["sd_m"] / math.sqrt(12), Z),
                      "power12_overlap": pp.window_power(pri["pi2_central"], b["sd"] * math.sqrt(b["c_bind"] / 365), Z)}
# c rule illustration: c at the Monte-Carlo median of the rule (REVIEW_H27 B-2: 20.3 at true 18.6)
res["H27_c_median_rule"] = {"n_closed_c20.3": n_closed(pri["pi2_central"], b["sd"], 20.3)}

# ---------------- DEC-52 equal windows, practice factor, one vs two windows -------------
lo, hi = 2.0, 3.5
for _ in range(200):
    x = 0.5 * (lo + hi)
    if pp.dec52_gate_power([x, x], [1.0, 1.0])["power_product"] >= 0.8:
        hi = x
    else:
        lo = x
res["DEC52_equal"] = {"x_needed": hi, "ratio_vs_c10": (hi / F) ** 2}
res["A3_practice_factor"] = (FA3 / F) ** 2
two = 2 * F ** 2
res["windows_compare"] = {
    "one_window_alpha0.0025_power0.80": pp.mde_factor(0.0025, 0.80) ** 2 / two,
    "one_window_alpha0.0025_power0.64": pp.mde_factor(0.0025, 0.64) ** 2 / two,
    "two_windows_joint_power0.80": 2 * pp.mde_factor(0.05, math.sqrt(0.8)) ** 2 / two,
    "cost_two_vs_one_at_power0.64": 1 / (pp.mde_factor(0.0025, 0.64) ** 2 / two),
    "cost_two_vs_one_at_power0.80": (2 * pp.mde_factor(0.05, math.sqrt(0.8)) ** 2) / pp.mde_factor(0.0025, 0.80) ** 2}

# ---------------- A4 ----------------
ex = quarterly_expiries_after(dt.date(2027, 6, 16), 60)
res["A4"] = {"first": ex[0].isoformat(), "full_4_cycles_per_window": ex[8].isoformat(),
             "full_7": ex[14].isoformat(), "N_c10_prior_eq_sigma": n_closed(1.0, 1.0, 1.0)}

# ---------------- H-26 calendar readings (dates only, from DEC-96 / 2.0 registry facts) ---------
def h26(first_day):
    s = first_day
    return {"stream_start": s.isoformat(), "W1": [s.isoformat(), (s + dt.timedelta(89)).isoformat()],
            "W2": [(s + dt.timedelta(90)).isoformat(), (s + dt.timedelta(179)).isoformat()],
            "unlock_day210": (s + dt.timedelta(209)).isoformat(),
            "days_W1_incl_fwd_in_blind": max(0, (s + dt.timedelta(89 + 30) - dt.date(2026, 7, 1)).days + 1)}
res["H26"] = {
    "a_2.0_inventory_112_days_on_2026-08-10": h26(dt.date(2026, 8, 10) - dt.timedelta(111)),
    "b_harvester_since_gap_end_2026-03-20_healed_days_count": h26(dt.date(2026, 3, 20)),
    "c_restart_after_gap_2026-09-20_healed_days_do_not_count": h26(dt.date(2026, 9, 21)),
    "d_full_backfill_counts_publicTrade_contiguous_since_2025-08-01": h26(dt.date(2025, 8, 1))}
shift = (dt.date.fromisoformat(res["H26"]["a_2.0_inventory_112_days_on_2026-08-10"]["unlock_day210"])
         - S_VRP).days + 1
res["VRP_after_H26_a"] = {"blind_start": (S_VRP + dt.timedelta(shift)).isoformat(),
                          "full_c10_p1": full_daily(S_VRP + dt.timedelta(shift), h27["ref|pi2_central"]["n_int"])}

res["sha256_inputs"] = SHA
res["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="ascii")
print("wrote", OUT)
