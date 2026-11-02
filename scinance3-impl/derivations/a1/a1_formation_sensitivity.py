"""A1 Stufe 1 -- formation-side sensitivities (task rule 1: only data of the formation week t or earlier).

(1) Key spread D1 vs universe when 1h symbol-weeks are excluded by a look-ahead-free FORMATION-WEEK
    rule (DEC-58 E3): (a) any 1h day in week t, (b) the last funding day of week t is 1h.
(2) Within-formation-week persistence proxy psi: sort on the key of Mon-Wed of week t (days 0-2),
    take the D1 of that sort, and compare its spread on Thu-Sun (days 3-6) of the SAME week, per day,
    with its spread on Mon-Wed per day: psi = sum(later-day spread per day) / sum(sort-day spread per
    day). Everything lies inside week t, i.e. before the A1 formation at the close of week t -- no
    data of a holding week is used. psi is computed on the nuisance base AND on W1/W2 and only
    serves to scale the nuisance persistence phi as a SENSITIVITY (never binding).
(3) Per-symbol time-series lag-1 autocorrelation of the key on the nuisance base (same estimator as
    the window census) for comparison with W1/W2.
"""
from __future__ import annotations

import json
import pickle
import sys
from datetime import date

sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")

import numpy as np  # noqa: E402

import a1_common as C  # noqa: E402
import a1_window_census as WC  # noqa: E402
from bybit_edge.research.wp7_universe import panel_load, pit_universe  # noqa: E402

K_MIN = 117


def daily_excess_by_week(d):
    """Map week index -> list of daily row indices (Mon..Sun order) and the daily excess array."""
    panel = d["panel"]
    exc, has = panel_load.funding_excess_daily(panel)
    week_pos = {w: i for i, w in enumerate(d["weeks"])}
    rows = {}
    for i, ds in enumerate(panel["dates"]):
        wk = pit_universe.iso_week_start(date.fromisoformat(ds)).isoformat()
        wi = week_pos.get(wk)
        if wi is not None:
            rows.setdefault(wi, []).append(i)
    return exc, has, rows


def main():
    d = pickle.load(open(C.WORK / "cache" / "a1_data.pkl", "rb"))
    weeks, key = d["weeks"], d["key"]
    exc, has, rows = daily_excess_by_week(d)
    fn = d["panel"]["funding_n"]
    sets = {}
    for wn, (a, b) in C.WINDOWS.items():
        sets[wn] = C.judged_formation_weeks(weeks, a, b)
    # nuisance base (formation-side only; same K>=117 filter as a1_nuisance)
    nb = [t for t in C.nuisance_formation_weeks(weeks) if C.universe_mask(d, t).sum() >= K_MIN]
    sets["nuisance_K_ge_117"] = nb
    out = {"label": "formationsseitig: nur Daten der Formationswoche t oder frueher", "sets": {}}
    for name, ts in sets.items():
        res = {"n_weeks": len(ts)}
        # (1) spreads with 1h exclusion
        sp = {"all": [], "excl_any_1h_day": [], "excl_last_day_1h": []}
        for t in ts:
            m = C.universe_mask(d, t)
            any1h = d["cls_days"]["1h"][t] > 0
            rr = rows[t]
            last_1h = np.zeros(m.shape, dtype=bool)
            # last day of week t with funding, per symbol: is it a 24-settlement day?
            for j in np.flatnonzero(m):
                for i in reversed(rr):
                    if has[i, j]:
                        last_1h[j] = int(round(fn[i, j])) == 24
                        break
            for lab, mm in (("all", m), ("excl_any_1h_day", m & ~any1h), ("excl_last_day_1h", m & ~last_1h)):
                d1 = C.d1_members(key[t], mm)
                u = np.flatnonzero(mm)
                sp[lab].append((key[t, u].mean() - key[t, d1].mean()) * 1e4)
        res["spread_bp"] = {k: {"mean": float(np.mean(v)), "median": float(np.median(v))} for k, v in sp.items()}
        # (2) within-week persistence proxy
        num = den = 0.0
        ratios = []
        for t in ts:
            rr = rows[t]
            if len(rr) != 7:
                continue
            m = C.universe_mask(d, t)
            first = exc[rr[:3]].sum(axis=0)
            later = exc[rr[3:]].sum(axis=0)
            d1 = C.d1_members(first, m)
            u = np.flatnonzero(m)
            s_first = (first[u].mean() - first[d1].mean()) / 3.0
            s_later = (later[u].mean() - later[d1].mean()) / 4.0
            num += s_later
            den += s_first
            ratios.append(s_later / s_first)
        res["psi_within_week"] = {"ratio_of_sums": float(num / den), "median_weekly_ratio": float(np.median(ratios)),
                                  "n_weeks": len(ratios)}
        # (3) per-symbol time-series key autocorrelation (formation-side)
        member = np.zeros_like(d["alive"])
        for t in ts:
            member[t] = C.universe_mask(d, t)
        lo, hi = min(ts), max(ts) + 1
        res["key_ts_autocorr"] = WC.ts_lag1_autocorr(key[lo:hi], member[lo:hi])
        res["buehlmann_straub"] = WC.buehlmann_straub(key[lo:hi], member[lo:hi])
        out["sets"][name] = res
        print(name, json.dumps(res, default=float))
    (C.WORK / f"formation_sensitivity{C.SUFFIX}.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
