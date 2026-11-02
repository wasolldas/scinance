"""A2 event census (calendar and timing ONLY) from the Deribit settlement calendar extract and the
deliveryPrices date list.  No price, no return, no volatility (the extracts contain none).

Pre-fixed rules (before any count):
C-1  Instrument types from the name: perpetual ``CCY-PERPETUAL``; future ``CCY-DDMMMYY``; option
     ``CCY-DDMMMYY-STRIKE-C|P``; everything else "other" (counted, examples listed).
C-2  Expiry date from the name; event = one expiry date (BTC and ETH on the same date = one cluster,
     DEC-67); counts also per currency.
C-3  Calendar class of an expiry date (checked against the data, not assumed): not a Friday ->
     "daily"; Friday that is not the last Friday of its month -> "weekly"; last Friday of Mar/Jun/
     Sep/Dec -> "quarterly"; other last Fridays -> "monthly".  Sets: W_ohne_M = weekly;
     M = monthly + quarterly; M_ohne_Q = monthly; Q = quarterly.
C-4  Periods: total 2020-03-25..2026-06-30; Vorperiode 2020-03-25..2024-05-31; W1 2024-07-01..
     2025-06-30; W2 2025-07-01..2026-06-30 (DEC-99: W2 ends 2026-06-28, shown separately);
     blind 2026-07-01..2026-10-20 (calendar only, end of extract).
C-5  Timing: seconds of the timestamp after 08:00:00 UTC of its own UTC day; quantiles q0, q01,
     q05, q25, q50, q75, q95, q99, q100; outliers |dt| > 60 s listed; per year.
C-6  Placebo calendar per period: Fridays with / without any delivery, by class; other weekdays
     with / without a daily delivery; weekend days.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hfrv_common as hc  # noqa: E402

SETT = hc.D / "deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet"
DELP = hc.D / "deribit_rest_deliveryPrices_DATES_2016-03-18_2026-10-20.parquet"
LABEL = ("A2-Ereigniszensus: nur Kalender und Zeitlage (Zeitstempel) der Deribit-Settlements/-Deliveries "
         "und Datumsliste der deliveryPrices; keine Preise, Renditen oder Volatilitaeten (nicht im Extrakt).")
MON = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
RE_PERP = re.compile(r"^(BTC|ETH)-PERPETUAL$")
RE_FUT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})$")
RE_OPT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})-([0-9d.]+)-([CP])$")
PERIODS = {"gesamt_2020-03-25..2026-06-30": ("2020-03-25", "2026-06-30"),
           "vorperiode_2020-03-25..2024-05-31": ("2020-03-25", "2024-05-31"),
           "W1_2024-07-01..2025-06-30": ("2024-07-01", "2025-06-30"),
           "W2_2025-07-01..2026-06-30": ("2025-07-01", "2026-06-30"),
           "W2_DEC99_2025-07-01..2026-06-28": ("2025-07-01", "2026-06-28"),
           "W_2024-07-01..2026-06-30": ("2024-07-01", "2026-06-30"),
           "blind_2026-07-01..2026-10-20": ("2026-07-01", "2026-10-20")}
QS = (0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0)


def parse_name(name: str):
    if name is None:
        return "other", None
    if RE_PERP.match(name):
        return "perpetual", None
    m = RE_FUT.match(name) or RE_OPT.match(name)
    if m:
        kind = "future" if RE_FUT.match(name) else "option"
        dd, mmm, yy = int(m.group(2)), m.group(3), int(m.group(4))
        if mmm not in MON:
            return "other", None
        try:
            return kind, date(2000 + yy, MON[mmm], dd)
        except ValueError:
            return "other", None
    return "other", None


def last_friday(y: int, m: int) -> date:
    d = date(y, m, calendar.monthrange(y, m)[1])
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d


def cal_class(d: date) -> str:
    if d.weekday() != 4:
        return "daily"
    if d != last_friday(d.year, d.month):
        return "weekly"
    return "quarterly" if d.month in (3, 6, 9, 12) else "monthly"


def quant(x) -> dict:
    a = np.asarray(x, dtype=float)
    if a.size == 0:
        return {"n": 0}
    return {"n": int(a.size), **{f"q{int(q*100):02d}" if q < 1 else "q100": float(np.quantile(a, q)) for q in QS}}


def in_period(d: str, p: tuple[str, str]) -> bool:
    return p[0] <= d <= p[1]


def main() -> None:
    out: dict = {"label": LABEL, "regeln": "C-1..C-6 im Docstring von a2_census.py (vor jeder Zaehlung fixiert)",
                 "inputs_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (SETT, DELP)}}
    df = pl.read_parquet(SETT)
    out["schema"] = {k: str(v) for k, v in df.schema.items()}
    if set(df.columns) != {"column_symbol", "instrument_name", "type", "timestamp_ms"}:
        raise RuntimeError(f"unexpected columns {df.columns} (price columns must not exist)")
    out["rows"] = df.height
    out["rows_by_ccy_type"] = {f"{a}|{b}": int(n) for (a, b), n in
                               Counter(zip([str(x).split("-")[0] for x in df["instrument_name"].to_list()],
                                           df["type"].to_list())).items()}
    out["timestamp_zero_or_missing"] = int((df["timestamp_ms"] <= 0).sum())
    # exact duplicate rows
    out["exact_duplicate_rows"] = int(df.height - df.unique().height)
    df = df.unique().sort(["timestamp_ms", "instrument_name"])
    names = df["instrument_name"].to_list()
    parsed = [parse_name(n) for n in names]
    kinds = [p[0] for p in parsed]
    exp = [p[1] for p in parsed]
    ts = df["timestamp_ms"].to_list()
    typ = df["type"].to_list()
    # column_symbol carries the instrument name (= instrument_name), not the currency; the currency
    # is the name prefix before the first '-' (deviation from the task text, stated in the file)
    out["column_symbol_eq_instrument_name"] = int(sum(1 for a, b in zip(df["column_symbol"].to_list(), names) if a == b))
    ccy = [n.split("-")[0] if n else None for n in names]
    out["currency_prefix_counts"] = dict(Counter(ccy))
    tsd = [datetime.fromtimestamp(t / 1000, tz=timezone.utc) for t in ts]
    out["kinds_by_type"] = {f"{k}|{t}": int(n) for (k, t), n in Counter(zip(kinds, typ)).items()}
    other = Counter(n for n, k in zip(names, kinds) if k == "other")
    out["other_names_n"] = sum(other.values())
    out["other_names_examples"] = [n for n, _ in other.most_common(15)]
    out["ccy_mismatch_name_vs_column"] = int(sum(1 for n, c, k in zip(names, ccy, kinds)
                                                 if k != "other" and not n.startswith(c + "-")))
    out["first_last_ts_by_ccy_type"] = {}
    for c in ("BTC", "ETH"):
        for t in sorted(set(typ)):
            sel = [x for x, cc, tt in zip(tsd, ccy, typ) if cc == c and tt == t]
            if sel:
                out["first_last_ts_by_ccy_type"][f"{c}|{t}"] = [min(sel).isoformat(), max(sel).isoformat()]

    # ---------------- B-1 deliveries per expiry date ----------------
    deliv = [(c, n, k, e, d) for c, n, k, e, d, t in zip(ccy, names, kinds, exp, tsd, typ) if t == "delivery"]
    out["delivery_rows"] = len(deliv)
    out["delivery_kinds"] = dict(Counter(k for _, _, k, _, _ in deliv))
    dup_inst = Counter(n for _, n, _, _, _ in deliv)
    out["instruments_delivered_more_than_once"] = sorted(n for n, m in dup_inst.items() if m > 1)[:20]
    out["n_instruments_delivered_more_than_once"] = sum(1 for m in dup_inst.values() if m > 1)
    per_date: dict[date, dict] = defaultdict(lambda: {"BTC": Counter(), "ETH": Counter()})
    perp_deliv = []
    for c, n, k, e, d in deliv:
        if k in ("future", "option") and e is not None:
            per_date[e][c][k] += 1
        elif k == "perpetual":
            perp_deliv.append((c, d.isoformat()))
    out["perpetual_delivery_rows"] = perp_deliv[:20]
    dates = sorted(per_date)
    # expiry date (name) vs timestamp date
    same, diff = 0, []
    for c, n, k, e, d in deliv:
        if e is None:
            continue
        if d.date() == e:
            same += 1
        else:
            diff.append((n, d.isoformat()))
    out["delivery_ts_date_eq_name_date"] = {"equal": same, "differ": len(diff), "differ_examples": diff[:20]}
    # weekday distribution per kind (check, not assume)
    wd = {}
    for kind in ("future", "option"):
        ds = sorted({e for e in dates if any(per_date[e][c][kind] for c in ("BTC", "ETH"))})
        wd[kind] = {"n_dates": len(ds), "weekday_counts": dict(Counter(calendar.day_abbr[d.weekday()] for d in ds)),
                    "class_counts": dict(Counter(cal_class(d) for d in ds)),
                    "first": ds[0].isoformat() if ds else None, "last": ds[-1].isoformat() if ds else None,
                    "gap_days_hist": dict(Counter(str((b - a).days) for a, b in zip(ds, ds[1:])))}
        # first date per class and per year counts
        fc = {}
        for cl in ("daily", "weekly", "monthly", "quarterly"):
            dd = [d for d in ds if cal_class(d) == cl]
            fc[cl] = {"first": dd[0].isoformat() if dd else None, "n": len(dd),
                      "per_year": dict(Counter(str(d.year) for d in dd))}
        wd[kind]["by_class"] = fc
    out["expiry_dates_by_kind"] = wd
    # since when every Friday / every day has an option expiry (continuity)
    opt_dates = {e for e in dates if any(per_date[e][c]["option"] for c in ("BTC", "ETH"))}
    fut_dates = {e for e in dates if any(per_date[e][c]["future"] for c in ("BTC", "ETH"))}

    def continuous_since(dset: set, step_filter, lo: date, hi: date):
        """Earliest start s such that every day d in [s, hi] with step_filter(d) is in dset."""
        days = [lo + timedelta(i) for i in range((hi - lo).days + 1)]
        days = [d for d in days if step_filter(d)]
        missing = [d for d in days if d not in dset]
        start = (missing[-1] + timedelta(1)) if missing else lo
        return start, missing

    cont = {}
    for c in ("BTC", "ETH", "pooled"):
        for kind in ("option", "future"):
            cs = ("BTC", "ETH") if c == "pooled" else (c,)
            ds = {e for e in dates if any(per_date[e][x][kind] for x in cs)}
            if not ds:
                continue
            hi_k = max(ds)            # coverage end of this kind in the extract (never extended)
            for lab, filt in (("every_friday", lambda d: d.weekday() == 4),
                              ("every_day", lambda d: True)):
                s0, miss = continuous_since(ds, filt, min(ds), hi_k)
                later = [m for m in miss if m >= date(2019, 1, 1)]
                cont[f"{c}|{kind}|{lab}"] = {"coverage_end_in_extract": hi_k.isoformat(),
                                             "continuous_since": s0.isoformat(), "n_missing_total": len(miss),
                                             "last_missing_before_continuity": [m.isoformat() for m in later][-8:]}
    out["continuity_within_coverage"] = cont
    # coverage gap of option deliveries at the end of the extract (named, never filled)
    last_opt = max(opt_dates)
    tail = [last_opt + timedelta(i) for i in range(1, (date(2026, 10, 20) - last_opt).days + 1)]
    out["option_delivery_coverage_gap"] = {
        "last_option_delivery_date": last_opt.isoformat(), "days_after_without_option_delivery": len(tail),
        "of_which_with_future_delivery": sum(1 for d in tail if d in fut_dates),
        "option_expiry_dates_per_month_2026": dict(sorted(Counter(e.strftime("%Y-%m") for e in opt_dates if e.year == 2026).items()))}
    # per-currency first weekly (non-monthly Friday) and first daily option/future expiry
    firsts = {}
    for c in ("BTC", "ETH"):
        for kind in ("option", "future"):
            ds = sorted(e for e in dates if per_date[e][c][kind])
            firsts[f"{c}|{kind}"] = {cl: next((d.isoformat() for d in ds if cal_class(d) == cl), None)
                                     for cl in ("daily", "weekly", "monthly", "quarterly")}
            firsts[f"{c}|{kind}"]["first_any"] = ds[0].isoformat() if ds else None
    out["first_expiry_by_class"] = firsts
    # last-Friday check: months whose last Friday has no future/option delivery, and months whose
    # largest-future expiry is not the last Friday (holiday shifts)
    months_check = []
    m_lo, m_hi = date(2018, 1, 1), date(2026, 9, 30)
    y, m = m_lo.year, m_lo.month
    while date(y, m, 1) <= m_hi:
        lf = last_friday(y, m)
        has = lf in per_date and any(per_date[lf][c]["future"] + per_date[lf][c]["option"] for c in ("BTC", "ETH"))
        fut_in_month = sorted(e for e in fut_dates if e.year == y and e.month == m)
        if not has or (fut_in_month and lf not in fut_in_month):
            months_check.append({"month": f"{y}-{m:02d}", "last_friday": lf.isoformat(), "delivery_on_last_friday": has,
                                 "future_expiries_in_month": [d.isoformat() for d in fut_in_month]})
        m += 1
        if m == 13:
            y, m = y + 1, 1
    out["last_friday_check_2018_01..2026_09"] = months_check
    # instruments per expiry date (summary by class and year)
    per_date_rows = []
    for d in dates:
        r = {"date": d.isoformat(), "weekday": calendar.day_abbr[d.weekday()], "class": cal_class(d)}
        for c in ("BTC", "ETH"):
            r[f"{c}_fut"] = per_date[d][c]["future"]
            r[f"{c}_opt"] = per_date[d][c]["option"]
        per_date_rows.append(r)
    inst_summary = {}
    for cl in ("daily", "weekly", "monthly", "quarterly"):
        rows = [r for r in per_date_rows if r["class"] == cl and "2020-03-25" <= r["date"] <= "2026-06-30"]
        for c in ("BTC", "ETH"):
            for k in ("fut", "opt"):
                inst_summary[f"{cl}|{c}_{k}"] = quant([r[f"{c}_{k}"] for r in rows])
    out["instruments_per_expiry_date_quantiles_2020-03-25..2026-06-30"] = inst_summary
    out["expiry_dates_table"] = per_date_rows

    # ---------------- event counts per period / year ----------------
    def ev_sets(d_list):
        cnt = Counter(cal_class(d) for d in d_list)
        return {"W_ohne_M": cnt["weekly"], "M_inkl_Q": cnt["monthly"] + cnt["quarterly"],
                "M_ohne_Q": cnt["monthly"], "Q": cnt["quarterly"], "daily": cnt["daily"],
                "alle": len(d_list)}

    counts = {}
    for scope in ("pooled", "BTC", "ETH", "BTC_and_ETH_same_date"):
        if scope == "pooled":
            ev = [d for d in dates if any(per_date[d][c]["future"] + per_date[d][c]["option"] for c in ("BTC", "ETH"))]
        elif scope == "BTC_and_ETH_same_date":
            ev = [d for d in dates if all(per_date[d][c]["future"] + per_date[d][c]["option"] for c in ("BTC", "ETH"))]
        else:
            ev = [d for d in dates if per_date[d][scope]["future"] + per_date[d][scope]["option"]]
        sc = {}
        for pname, p in PERIODS.items():
            sc[pname] = ev_sets([d for d in ev if in_period(d.isoformat(), p)])
        sc["per_year"] = {str(y): ev_sets([d for d in ev if d.year == y and "2020-03-25" <= d.isoformat() <= "2026-10-20"])
                          for y in range(2020, 2027)}
        counts[scope] = sc
    out["event_counts"] = counts
    # same with futures-only and options-only (which instrument carries the event)
    for kind in ("future", "option"):
        ev = [d for d in dates if any(per_date[d][c][kind] for c in ("BTC", "ETH"))]
        out["event_counts"][f"pooled_{kind}_only"] = {pname: ev_sets([d for d in ev if in_period(d.isoformat(), p)])
                                                      for pname, p in PERIODS.items()}

    # ---------------- B-2 timing ----------------
    def secs_after_8(d: datetime) -> float:
        base = datetime(d.year, d.month, d.day, 8, 0, 0, tzinfo=timezone.utc)
        return (d - base).total_seconds()

    timing = {}
    for t in sorted(set(typ)):
        for kind in ("future", "option", "perpetual", "other"):
            sel = [(d, n) for d, k, tt in zip(tsd, kinds, typ) for n in [None] if k == kind and tt == t]
            if not sel:
                continue
            secs = [secs_after_8(d) for d, _ in sel]
            key = f"{t}|{kind}"
            blk = {"all": quant(secs), "per_year": {}}
            for y in sorted({d.year for d, _ in sel}):
                blk["per_year"][str(y)] = quant([s for (d, _), s in zip(sel, secs) if d.year == y])
            outl = [(d.isoformat(), round(s, 3)) for (d, _), s in zip(sel, secs) if abs(s) > 60]
            blk["n_outliers_abs_gt_60s"] = len(outl)
            by_day = defaultdict(lambda: [0, 0.0])
            for dts, sec in outl:
                by_day[dts[:10]][0] += 1
                by_day[dts[:10]][1] = max(by_day[dts[:10]][1], sec)
            blk["outliers_by_utc_day"] = {k: {"n": v[0], "max_s_after_0800": v[1]} for k, v in sorted(by_day.items())}
            blk["n_rows_abs_gt_5s"] = int(sum(1 for x in secs if abs(x) > 5))
            blk["n_rows_before_0800"] = int(sum(1 for x in secs if x < 0))
            blk["hour_of_day_counts"] = dict(Counter(str(d.hour) for d, _ in sel))
            timing[key] = blk
    out["timing_seconds_after_0800_utc"] = timing
    # daily settlement coverage gaps (days without any 'settlement' row) per currency
    gaps = {}
    for c in ("BTC", "ETH"):
        sdays = sorted({d.date() for d, cc, tt in zip(tsd, ccy, typ) if cc == c and tt == "settlement"})
        if not sdays:
            continue
        allds = [sdays[0] + timedelta(i) for i in range((sdays[-1] - sdays[0]).days + 1)]
        miss = [d.isoformat() for d in allds if d not in set(sdays)]
        gaps[c] = {"first": sdays[0].isoformat(), "last": sdays[-1].isoformat(), "n_days": len(allds),
                   "n_days_without_settlement_row": len(miss), "missing_days": miss[:60]}
    out["settlement_row_day_gaps"] = gaps

    # ---------------- B-3 placebo calendar ----------------
    ev_pooled = set(d for d in dates if any(per_date[d][c]["future"] + per_date[d][c]["option"] for c in ("BTC", "ETH")))
    plc = {}
    for pname, (lo, hi_) in PERIODS.items():
        a, b = date.fromisoformat(lo), date.fromisoformat(hi_)
        dd = [a + timedelta(i) for i in range((b - a).days + 1)]
        fr = [d for d in dd if d.weekday() == 4]
        oth = [d for d in dd if d.weekday() < 4]
        we = [d for d in dd if d.weekday() >= 5]
        plc[pname] = {
            "fridays": len(fr),
            "fridays_with_delivery_by_class": dict(Counter(cal_class(d) for d in fr if d in ev_pooled)),
            "fridays_without_delivery": len([d for d in fr if d not in ev_pooled]),
            "fridays_without_delivery_list": [d.isoformat() for d in fr if d not in ev_pooled][:40],
            "mon_thu": len(oth), "mon_thu_with_daily_delivery": len([d for d in oth if d in ev_pooled]),
            "mon_thu_without_delivery": len([d for d in oth if d not in ev_pooled]),
            "weekend_days": len(we), "weekend_with_delivery": len([d for d in we if d in ev_pooled]),
            "non_expiry_fridays_relative_to_monthly": len([d for d in fr if cal_class(d) == "weekly"])}
    out["placebo_calendar"] = plc

    # ---------------- deliveryPrices dates ----------------
    dp = pl.read_parquet(DELP)
    if set(dp.columns) != {"index_name", "date"}:
        raise RuntimeError(f"unexpected deliveryPrices columns {dp.columns}")
    out["deliveryPrices_rows"] = dp.height
    out["deliveryPrices_index_names"] = dict(Counter(dp["index_name"].to_list()))
    dpo = {}
    for idx in sorted(set(dp["index_name"].to_list())):
        raw = dp.filter(pl.col("index_name") == idx)["date"].to_list()
        ds = sorted({date.fromisoformat(str(x)[:10]) for x in raw})
        dup = len(raw) - len(ds)
        gaps_ = [(a, b) for a, b in zip(ds, ds[1:])]
        per_year = {}
        for y in sorted({d.year for d in ds}):
            yd = [d for d in ds if d.year == y]
            g = [(b - a).days for a, b in zip(yd, yd[1:])]
            per_year[str(y)] = {"n": len(yd), "gap_hist": dict(Counter(str(x) for x in g)),
                                "weekday_counts": dict(Counter(calendar.day_abbr[d.weekday()] for d in yd))}
        # since when daily without interruption
        miss_after = [b for a, b in gaps_ if (b - a).days > 1]
        daily_since = (miss_after[-1]).isoformat() if miss_after else (ds[0].isoformat() if ds else None)
        dpo[idx] = {"n_dates": len(ds), "duplicates": dup, "first": ds[0].isoformat() if ds else None,
                    "last": ds[-1].isoformat() if ds else None, "per_year": per_year,
                    "daily_without_gap_since": daily_since,
                    "gaps_gt_1_day_since_2020": [(a.isoformat(), b.isoformat(), (b - a).days)
                                                 for a, b in gaps_ if (b - a).days > 1 and a.year >= 2020][:40],
                    "dates_in_extract_vs_delivery_days": None}
        # compare with expiry dates of the settlement calendar (pooled ccy of the index)
        c = "BTC" if idx.startswith("btc") else ("ETH" if idx.startswith("eth") else None)
        if c:
            ev_c = {d for d in dates if per_date[d][c]["future"] + per_date[d][c]["option"]}
            lo_c = max(min(ds), min(ev_c)) if ev_c and ds else None
            if lo_c:
                a_set = {d for d in ds if d >= lo_c}
                b_set = {d for d in ev_c if d >= lo_c and d <= max(ds)}
                dpo[idx]["dates_in_extract_vs_delivery_days"] = {
                    "from": lo_c.isoformat(), "only_in_deliveryPrices": len(a_set - b_set),
                    "only_in_settlement_deliveries": len(b_set - a_set),
                    "examples_only_deliveryPrices": sorted(d.isoformat() for d in a_set - b_set)[:15],
                    "examples_only_settlements": sorted(d.isoformat() for d in b_set - a_set)[:15]}
    out["deliveryPrices_dates"] = dpo
    out["skript_sha256"] = {p_.name: hashlib.sha256(p_.read_bytes()).hexdigest()
                            for p_ in (Path(__file__).resolve(), HERE / "hfrv_common.py", HERE / "h27_common.py")}
    hc.check_out(out)
    hc.OUT_DIR.mkdir(parents=True, exist_ok=True)
    (hc.OUT_DIR / "a2_census.json").write_text(json.dumps(out, indent=1))
    print("WROTE a2_census.json")


if __name__ == "__main__":
    main()
