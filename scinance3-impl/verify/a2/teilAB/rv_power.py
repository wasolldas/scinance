"""Review recomputation of N per window (own calendar code), SE(contrast), MDE80 (power_p1) and the
JOINT window power of the conjunction 'significant against all placebos' (PRD 5.2 gate (2)).
Inputs: rv_sigma.json (dispersion only) and the calendar extract (no price column).  No returns read."""
from __future__ import annotations

import calendar
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, "/home/user/scinance/src")
from bybit_edge.research import power_p1  # noqa: E402

HERE = Path(__file__).resolve().parent
CAL = Path("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hf_data/raw/"
           "deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet")
S = json.loads((HERE / "rv_sigma.json").read_text())
Z1, Z3 = power_p1.z_krit(0.05), power_p1.Z_PER_WINDOW_A3_PRACTICE


def last_friday(y, m):
    d = date(y, m, calendar.monthrange(y, m)[1])
    while d.weekday() != 4:
        d -= timedelta(1)
    return d


def fine(d):
    if d.weekday() == 4:
        if d == last_friday(d.year, d.month):
            return "FRI_Q" if d.month % 3 == 0 else "FRI_M"
        return "FRI_W"
    return "WE" if d.weekday() >= 5 else "MODO"


SETS = {"FRI": {"FRI_W", "FRI_M", "FRI_Q"}, "FRI_W": {"FRI_W"}, "FRI_MQ": {"FRI_M", "FRI_Q"},
        "MODO": {"MODO"}, "WE": {"WE"}, "NONFRI": {"MODO", "WE"}, "ALL": {"FRI_W", "FRI_M", "FRI_Q", "MODO", "WE"}}


def outlier_days():
    t = pq.read_table(CAL, columns=["type", "instrument_name", "timestamp_ms"]).to_pydict()
    out = set()
    for ty, nm, ms in zip(t["type"], t["instrument_name"], t["timestamp_ms"]):
        parts = nm.split("-")
        if ty != "delivery" or len(parts) != 4 or parts[3] not in ("C", "P"):
            continue          # option deliveries only (BTC-DDMMMYY-K-C/P)
        sec = (ms % 86_400_000) / 1000.0 - 8 * 3600
        d = date(1970, 1, 1) + timedelta(ms // 86_400_000)
        if str(d) > "2026-06-30" or str(d) < "2020-03-25":
            continue
        if abs(sec) > 60:
            out.add(d)
    return out


def counts(lo, hi, excl):
    a, b = date.fromisoformat(lo), date.fromisoformat(hi)
    res = {k: 0 for k in SETS}
    for i in range((b - a).days + 1):
        d = a + timedelta(i)
        if d in excl:
            continue
        f = fine(d)
        for k, v in SETS.items():
            res[k] += f in v
    return res


def se_term(cls, n, slot="pre"):
    if slot == "pre":
        c = S["pre"][cls]
        return c["sd_cluster"] * math.sqrt(c["c_bind"] / n)
    c = S["other_series"][slot][cls]
    return c["sd_cluster"] * math.sqrt(c["c_bind"] / n)


def joint_power(prior_vec, se_e, se_p, z, n_draw=400_000, seed=11):
    """P(all contrasts >= z*SE_k); contrasts share the event-mean term (cov = se_e^2), placebo means
    treated as independent of each other and of the event mean (approximation, see review)."""
    k = len(se_p)
    se_c = np.sqrt(se_e ** 2 + np.asarray(se_p) ** 2)
    cov = np.full((k, k), se_e ** 2) + np.diag(np.asarray(se_p) ** 2)
    rng = np.random.default_rng(seed)
    x = rng.multivariate_normal(np.asarray(prior_vec, float), cov, size=n_draw)
    return float(np.all(x >= z * se_c, axis=1).mean())


def main():
    excl = outlier_days()
    W = {"W1": ("2024-07-01", "2025-06-30"), "W2": ("2025-07-01", "2026-06-28"),
         "W2full": ("2025-07-01", "2026-06-30")}
    N = {w: counts(lo, hi, excl) for w, (lo, hi) in W.items()}
    N_raw = {w: counts(lo, hi, set()) for w, (lo, hi) in W.items()}
    years = {y: counts(f"{y}-01-01", f"{y}-12-31", excl) for y in range(2021, 2026)}
    res = {"outlier_days": sorted(str(d) for d in excl), "N": N, "N_raw": N_raw, "years": years}
    des = {}
    for w in ("W1", "W2"):
        n = N[w]
        se_E = se_term("FRI", n["FRI"])
        d_i = {"P2_MODO": se_term("MODO", n["MODO"]), "P3fix": se_term("ALL", n["ALL"], "fix1530"),
               "P3all": se_term("ALL", n["ALL"], "p3all")}
        se_c = {k: math.hypot(se_E, v) for k, v in d_i.items()}
        prd_a = math.hypot(se_E, se_term("NONFRI", n["NONFRI"]))
        se_EM = se_term("FRI_MQ", n["FRI_MQ"])
        d_ii = math.hypot(se_EM, se_term("FRI_W", n["FRI_W"]))
        d_iw = math.hypot(se_term("FRI_W", n["FRI_W"]), d_i["P2_MODO"])
        # paired: SD of the per-day difference
        pr = S["other_series"]["pairdiff_pre_minus_1530"]["FRI"]
        d_is = pr["sd_cluster"] * math.sqrt(pr["c_bind"] / n["FRI"])
        cell = {"se_event_FRI": se_E, "D_i_se_by_placebo": se_c, "D_i_binding_se": max(se_c.values()),
                "D_i_mde80_p1": power_p1.mde80(max(se_c.values()), Z1),
                "D_i_mde80_a3": power_p1.mde80(max(se_c.values()), Z3),
                "PRD_a_se": prd_a, "PRD_a_mde80_p1": power_p1.mde80(prd_a, Z1),
                "D_ii_se": d_ii, "D_ii_mde80_p1": power_p1.mde80(d_ii, Z1),
                "D_i_W_se": d_iw, "D_i_W_mde80_p1": power_p1.mde80(d_iw, Z1),
                "D_i_s_paired_se": d_is, "D_i_s_mde80_p1": power_p1.mde80(d_is, Z1)}
        # joint power of D_i over its three placebos (unattenuated and OI-attenuated P2' prior 0.842)
        se_p = [d_i["P2_MODO"], d_i["P3fix"], d_i["P3all"]]
        jp = {}
        for prior in (16.5, 18.25, 20.0, 21.0, 25.0):
            single = [power_p1.window_power(prior, s, Z1) for s in se_c.values()]
            jp[str(prior)] = {"single_min": min(single), "product": float(np.prod(single)),
                              "joint_mc": joint_power([prior] * 3, se_E, se_p, Z1),
                              "joint_mc_att_0842": joint_power([0.842 * prior, prior, prior], se_E, se_p, Z1),
                              "single_min_att_0842": min(power_p1.window_power(0.842 * prior, se_c["P2_MODO"], Z1),
                                                         power_p1.window_power(prior, se_c["P3fix"], Z1),
                                                         power_p1.window_power(prior, se_c["P3all"], Z1))}
        # joint MDE80 by bisection (unattenuated)
        lo, hi = 10.0, 40.0
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if joint_power([mid] * 3, se_E, se_p, Z1, n_draw=200_000) >= 0.8:
                hi = mid
            else:
                lo = mid
        cell["D_i_joint_mde80_p1_mc"] = hi
        cell["D_i_joint_power"] = jp
        # D_i with D_i_s paired placebo added: joint over 4 conditions (paired difference independent approx.)
        des[w] = cell
    res["designs"] = des
    # Bilanz reproduction
    se_w = math.hypot(36 * math.sqrt(1.815 / 104), 36 * math.sqrt(1.8 / 626))
    se_m = math.hypot(36 * math.sqrt(1.815 / 24), 36 * math.sqrt(1.8 / 80))
    res["bilanz"] = {"weekly_se": se_w, "monthly_se": se_m, "weekly_mde80": power_p1.mde80(se_w, Z1),
                     "monthly_mde80": power_p1.mde80(se_m, Z1)}
    (HERE / "rv_power.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: r[k] for k in ("outlier_days", "N", "N_raw", "years", "bilanz")}, indent=0))
    for w, c in r["designs"].items():
        print(w, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in c.items() if k != "D_i_joint_power"})
        for p, v in c["D_i_joint_power"].items():
            print("   prior", p, {k: round(x, 3) for k, x in v.items()})
