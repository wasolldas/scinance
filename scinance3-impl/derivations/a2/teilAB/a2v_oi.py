"""Part A-2 / A-3 data: event size (delivered option contracts per expiry date and class) from the raw
settlement partitions (allow-listed fields only, R-2), event counts per year / window from the
calendar, and the timing check of the delivery timestamps (A-3).  Counts and sums only (R-1, R-2).
"""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.compute as pc

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a2v_common as c  # noqa: E402

QS = (0.05, 0.25, 0.5, 0.75, 0.95)
PERIODS = {
    "gesamt_2020-03-25..2026-06-30": ("2020-03-25", "2026-06-30"),
    "vorperiode_2020-03-25..2024-05-31": ("2020-03-25", "2024-05-31"),
    "nuisance_2021-03-24..2024-05-31": ("2021-03-24", "2024-05-31"),
    "W1_2024-07-01..2025-06-30": ("2024-07-01", "2025-06-30"),
    "W2_2025-07-01..2026-06-30": ("2025-07-01", "2026-06-30"),
    "W2_DEC99_2025-07-01..2026-06-28": ("2025-07-01", "2026-06-28"),
}
YEARS = {str(y): (f"{y}-01-01", f"{y}-12-31") for y in range(2021, 2026)}
YEARS["2020_ab_03-25"] = ("2020-03-25", "2020-12-31")
YEARS["2026_bis_06-30"] = ("2026-01-01", "2026-06-30")
FINE = ("FRI_W", "FRI_M", "FRI_Q", "MODO", "WE")


def qd(a) -> dict:
    a = np.asarray(a, dtype=float)
    if a.size == 0:
        return {"n": 0}
    out = {"n": int(a.size), "min": float(a.min())}
    out.update({f"q{int(round(q * 100)):02d}": float(np.quantile(a, q)) for q in QS})
    out["max"] = float(a.max())
    out["total"] = float(a.sum())
    return out


def secs_after_8(ms: int) -> float:
    dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    base = datetime(dt.year, dt.month, dt.day, 8, 0, 0, tzinfo=timezone.utc)
    return (dt - base).total_seconds()


def main() -> dict:
    out: dict = {"label": c.LABEL, "quelle": "S:a2v_oi.py (R-1, R-2, R-4)"}
    # ------------------------------------------------------------------ raw positions (R-2)
    per_day: dict = {}          # (ccy, date) -> dict
    raw_checks = {}
    raw_option_ts: dict = {}    # (instrument) -> timestamp (cross-check with the calendar)
    for ccy in ("BTC", "ETH"):
        parts = c.raw_partitions(ccy)
        n_rows = n_opt = n_dup = n_bad_date = n_null_pos = n_neg = n_zero = 0
        n_partitions = len(parts)
        seen = set()
        for day, f in parts:
            t = c.read_settlement_partition(f)
            n_rows += t.num_rows
            mask = pc.equal(t.column("type"), "delivery")
            t = t.filter(mask)
            names = t.column("instrument_name").to_pylist()
            ts = t.column("timestamp").to_pylist()
            pos = t.column("position_raw").to_pylist()
            for nm, tsv, pv in zip(names, ts, pos):
                ccy_n, exp = c.parse_option_expiry(nm)
                if exp is None:
                    continue                      # futures deliveries are not used
                assert ccy_n == ccy, (ccy_n, ccy)
                key = (nm, tsv)
                if key in seen:
                    n_dup += 1
                    continue
                seen.add(key)
                n_opt += 1
                ts_day = datetime.fromtimestamp(tsv / 1000.0, tz=timezone.utc).date()
                if not (exp.isoformat() == day == ts_day.isoformat()):
                    n_bad_date += 1
                    continue
                if exp.isoformat() > c.LAST_CAL_DAY:
                    raise RuntimeError("position after LAST_CAL_DAY")
                if pv is None or pv == "null":
                    n_null_pos += 1
                    continue
                p = float(pv)
                if p < 0:
                    n_neg += 1
                if p == 0:
                    n_zero += 1
                rec = per_day.setdefault((ccy, exp), {"contracts": 0.0, "n_instr": 0, "n_pos_gt0": 0})
                rec["contracts"] += p
                rec["n_instr"] += 1
                rec["n_pos_gt0"] += int(p > 0)
                raw_option_ts[nm] = tsv
        raw_checks[ccy] = {"partitions_read": n_partitions, "rows_all_types": n_rows,
                           "option_delivery_rows": n_opt, "duplicate_rows_dropped": n_dup,
                           "rows_expiry_ne_partition_or_ts_date": n_bad_date,
                           "position_null": n_null_pos, "position_negative": n_neg,
                           "position_zero": n_zero}
    out["raw_partition_checks"] = raw_checks

    # ------------------------------------------------------------------ calendar (R-1, R-4)
    cal = c.load_calendar()
    cal = cal.with_columns(pl.col("instrument_name").map_elements(
        lambda s: c.parse_option_expiry(s)[1], return_dtype=pl.Date).alias("exp"))
    opt = cal.filter((pl.col("type") == "delivery") & pl.col("exp").is_not_null())
    opt = opt.with_columns(pl.col("instrument_name").str.slice(0, 3).alias("ccy"))
    # cross-check counts and timestamps raw vs calendar extract for 2020-03-25..2026-06-30
    opt_p = opt.filter(pl.col("exp") >= date.fromisoformat(c.FIRST_CAL_DAY))
    cal_cnt = opt_p.group_by(["ccy", "exp"]).len()
    cal_map = {(r[0], r[1]): r[2] for r in cal_cnt.iter_rows()}
    raw_map = {k: v["n_instr"] for k, v in per_day.items()}
    diff_days = sorted({k for k in set(cal_map) | set(raw_map) if cal_map.get(k) != raw_map.get(k)})
    ts_equal = ts_diff = ts_missing = 0
    for nm, tsv in zip(opt_p["instrument_name"].to_list(), opt_p["timestamp_ms"].to_list()):
        r = raw_option_ts.get(nm)
        if r is None:
            ts_missing += 1
        elif r == tsv:
            ts_equal += 1
        else:
            ts_diff += 1
    out["raw_vs_calendar"] = {"days_compared": len(set(cal_map) | set(raw_map)),
                              "days_with_count_difference": len(diff_days),
                              "count_difference_examples": [[k[0], k[1].isoformat(), cal_map.get(k), raw_map.get(k)]
                                                            for k in diff_days[:10]],
                              "timestamp_equal": ts_equal, "timestamp_differ": ts_diff,
                              "calendar_instrument_missing_in_raw": ts_missing}

    # timing (A-3) and outlier days (R-4)
    secs = np.array([secs_after_8(v) for v in opt_p["timestamp_ms"].to_list()])
    days_p = opt_p["exp"].to_list()
    outlier_days = sorted({d.isoformat() for d, s in zip(days_p, secs) if abs(s) > 60})
    nuis = np.array([c.FIRST_RETURN_DAY <= d.isoformat() <= c.LAST_RETURN_DAY for d in days_p])
    tq = (0.0, 0.01, 0.5, 0.99, 0.999, 1.0)
    out["timing_option_delivery_seconds_after_0800"] = {
        "rule": "Sekunden des Delivery-Zeitstempels nach 08:00:00 UTC des eigenen UTC-Tages (Kalender-Extrakt)",
        "range_2020-03-25..2026-06-30": {"n": int(secs.size), **{f"q{q}": float(np.quantile(secs, q)) for q in tq},
                                          "n_before_0800": int((secs < 0).sum()), "n_gt_1s": int((secs > 1).sum()),
                                          "n_gt_60s": int((secs > 60).sum())},
        "range_2021-03-24..2024-05-31": {"n": int(nuis.sum()),
                                          **{f"q{q}": float(np.quantile(secs[nuis], q)) for q in tq},
                                          "n_before_0800": int((secs[nuis] < 0).sum()),
                                          "n_gt_1s": int((secs[nuis] > 1).sum()),
                                          "n_gt_60s": int((secs[nuis] > 60).sum())},
        "outlier_days_gt_60s_until_2026-06-30": outlier_days,
    }
    outlier_set = {date.fromisoformat(s) for s in outlier_days}

    # every day 2020-03-25..2026-06-30 must carry BTC and ETH option deliveries (R-4 check)
    all_days = c.days_range(c.FIRST_CAL_DAY, c.LAST_CAL_DAY)
    missing = [d.isoformat() for d in all_days for ccy in ("BTC", "ETH") if (ccy, d) not in per_day]
    out["every_day_has_btc_and_eth_option_delivery"] = {"days": len(all_days), "missing_ccy_days": missing[:20],
                                                        "n_missing": len(missing)}

    # ------------------------------------------------------------------ event counts (calendar only)
    def counts(lo, hi, excl_outliers=True):
        res = {k: 0 for k in ("FRI", "FRI_W", "FRI_M", "FRI_Q", "FRI_MQ", "MODO", "WE", "NONFRI", "ALL")}
        n_out = 0
        for d in c.days_range(lo, hi):
            if excl_outliers and d in outlier_set:
                n_out += 1
                continue
            fc = c.day_class(d)
            for k, members in c.CLASS_SETS.items():
                if fc in members:
                    res[k] += 1
        res["outlier_days_excluded"] = n_out
        return res
    ev = {}
    for lab, (lo, hi) in {**{f"jahr_{k}": v for k, v in YEARS.items()},
                          "W1_2024-07-01..2025-06-30": ("2024-07-01", "2025-06-30"),
                          "W2_2025-07-01..2026-06-30": ("2025-07-01", "2026-06-30"),
                          "W2_DEC99_2025-07-01..2026-06-28": ("2025-07-01", "2026-06-28"),
                          "nuisance_2021-03-24..2024-05-31": ("2021-03-24", "2024-05-31")}.items():
        ev[lab] = {"ohne_ausreisser_regel_R4": counts(lo, hi, True), "kalender_roh": counts(lo, hi, False)}
    out["event_counts"] = ev

    # ------------------------------------------------------------------ size distribution (A-2)
    size = {}
    for plab, (lo, hi) in {**PERIODS, **{f"jahr_{k}": v for k, v in YEARS.items()}}.items():
        cell = {}
        for ccy in ("BTC", "ETH"):
            byc = defaultdict(list)
            for d in c.days_range(lo, hi):
                if d in outlier_set:
                    continue
                rec = per_day.get((ccy, d))
                if rec is None:
                    continue
                fc = c.day_class(d)
                for k, members in c.CLASS_SETS.items():
                    if fc in members and k in ("FRI", "FRI_W", "FRI_M", "FRI_Q", "FRI_MQ", "MODO", "WE", "NONFRI", "ALL"):
                        byc[k].append(rec["contracts"])
            dist = {k: qd(v) for k, v in byc.items()}
            def ratio_q50(a, b):
                return dist[a]["q50"] / dist[b]["q50"] if dist.get(a, {}).get("n") and dist.get(b, {}).get("n") else None
            def ratio_tpd(a, b):
                if not (dist.get(a, {}).get("n") and dist.get(b, {}).get("n")):
                    return None
                return (dist[a]["total"] / dist[a]["n"]) / (dist[b]["total"] / dist[b]["n"])
            pairs = (("FRI", "MODO"), ("FRI", "NONFRI"), ("FRI_W", "MODO"), ("FRI_MQ", "MODO"), ("FRI_MQ", "FRI_W"),
                     ("FRI_Q", "FRI_W"), ("FRI_M", "FRI_W"), ("WE", "MODO"))
            cell[ccy] = {"contracts_per_expiry_date_by_class": dist,
                         "ratio_q50": {f"{a}/{b}": ratio_q50(a, b) for a, b in pairs},
                         "ratio_total_per_day": {f"{a}/{b}": ratio_tpd(a, b) for a, b in pairs}}
        size[plab] = cell
    out["size_by_period_and_class"] = size

    # within-week ratio Friday / q50(Mo-Do of the same ISO week); within-month M/Q vs weekly Fridays
    ww = {}
    for plab, (lo, hi) in PERIODS.items():
        cell = {}
        for ccy in ("BTC", "ETH"):
            weeks = defaultdict(lambda: {"fri": None, "modo": [], "fri_cls": None})
            months = defaultdict(lambda: {"mq": None, "w": []})
            for d in c.days_range(lo, hi):
                if d in outlier_set or (ccy, d) not in per_day:
                    continue
                v = per_day[(ccy, d)]["contracts"]
                fc = c.day_class(d)
                wk = d.isocalendar()[:2]
                if fc.startswith("FRI"):
                    weeks[wk]["fri"] = v
                    weeks[wk]["fri_cls"] = fc
                    if fc in ("FRI_M", "FRI_Q"):
                        months[(d.year, d.month)]["mq"] = v
                    else:
                        months[(d.year, d.month)]["w"].append(v)
                elif fc == "MODO":
                    weeks[wk]["modo"].append(v)
            r_all, r_w, r_mq = [], [], []
            for wk, rec in weeks.items():
                if rec["fri"] is None or len(rec["modo"]) < 2:
                    continue
                r = rec["fri"] / float(np.quantile(rec["modo"], 0.5))
                r_all.append(r)
                (r_mq if rec["fri_cls"] in ("FRI_M", "FRI_Q") else r_w).append(r)
            r_month = [rec["mq"] / float(np.quantile(rec["w"], 0.5)) for rec in months.values()
                       if rec["mq"] is not None and len(rec["w"]) >= 2]
            cell[ccy] = {"fri_over_q50_modo_same_week": {"FRI": qd(r_all), "FRI_W": qd(r_w), "FRI_MQ": qd(r_mq)},
                         "mq_over_q50_weekly_fridays_same_month": qd(r_month)}
            for blk in cell[ccy]["fri_over_q50_modo_same_week"].values():
                blk.pop("total", None)
            cell[ccy]["mq_over_q50_weekly_fridays_same_month"].pop("total", None)
        ww[plab] = cell
    out["within_week_and_month_ratios"] = ww

    # ------------------------------------------------------------------ design (iii) OI-sorted (report)
    oi_sorted = {}
    for plab, (lo, hi) in {"nuisance_2021-03-24..2024-05-31": ("2021-03-24", "2024-05-31"),
                           "W1_2024-07-01..2025-06-30": ("2024-07-01", "2025-06-30"),
                           "W2_DEC99_2025-07-01..2026-06-28": ("2025-07-01", "2026-06-28")}.items():
        ds = [d for d in c.days_range(lo, hi) if d not in outlier_set
              and ("BTC", d) in per_day and ("ETH", d) in per_day]
        score = np.zeros(len(ds))
        for ccy in ("BTC", "ETH"):
            v = np.array([per_day[(ccy, d)]["contracts"] for d in ds])
            ranks = v.argsort().argsort().astype(float) / (len(v) - 1)
            score += ranks / 2.0
        cell = {"n_days": len(ds)}
        for qlab, q in (("quintil", 0.2), ("terzil", 1 / 3)):
            hi_cut, lo_cut = np.quantile(score, 1 - q), np.quantile(score, q)
            top = [d for d, s in zip(ds, score) if s >= hi_cut]
            bot = [d for d, s in zip(ds, score) if s <= lo_cut]
            comp = lambda L: {k: sum(1 for d in L if c.day_class(d) == k) for k in FINE}
            cell[qlab] = {"n_top": len(top), "n_bottom": len(bot), "top_composition": comp(top),
                          "bottom_composition": comp(bot)}
        oi_sorted[plab] = cell
    out["design_iii_oi_sorted_report"] = {
        "rule": "Cluster-Score je Tag = halbe Summe der Perzentil-Raenge (je Waehrung, innerhalb der Periode) der gelieferten "
                "Kontrakte; oberes gegen unteres Quintil/Terzil; ex post (position am Verfall) -> nur Bericht",
        "by_period": oi_sorted}
    c.check_out(out)
    return out


if __name__ == "__main__":
    res = main()
    h = c.dump(res, c.WORK / "a2v_oi.json")
    print("sha256", h)
