"""Independent re-count of the A2 event census (calendar and timestamps only) for the review.

Own parser and own counting (no import of the derivation agent's code).  The extracts carry no
price column (asserted).  Option strike counts are used ONLY for expiry dates <= 2024-05-31
(class signature in the pre-period); nothing per date is written for dates >= 2024-06-01 except
the calendar (date exists / class) and settlement timestamps (DEC-96 E3: completeness, timestamps).
Run: python3 -I a2_review.py   (writes a2_review.json next to this file)
"""
from __future__ import annotations

import calendar
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "hf_data" / "raw"
SETT = RAW / "deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet"
DELP = RAW / "deribit_rest_deliveryPrices_DATES_2016-03-18_2026-10-20.parquet"
MON = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
NAME = re.compile(r"^(BTC|ETH)-(?:(PERPETUAL)|(\d{1,2})([A-Z]{3})(\d{2})(?:-([0-9]+(?:d[0-9]+)?)-([CP]))?)$")
PERIODS = {"gesamt": (date(2020, 3, 25), date(2026, 6, 30)), "vor": (date(2020, 3, 25), date(2024, 5, 31)),
           "W1": (date(2024, 7, 1), date(2025, 6, 30)), "W2": (date(2025, 7, 1), date(2026, 6, 30)),
           "W2_dec99": (date(2025, 7, 1), date(2026, 6, 28)), "blind": (date(2026, 7, 1), date(2026, 10, 20))}


def parse(n: str):
    m = NAME.match(n or "")
    if not m:
        return None
    ccy = m.group(1)
    if m.group(2):
        return ccy, "perp", None, None
    exp = date(2000 + int(m.group(5)), MON[m.group(4)], int(m.group(3)))
    return ccy, ("option" if m.group(7) else "future"), exp, m.group(6)


def klass(d: date) -> str:
    if d.weekday() != 4:
        return "daily"
    last = max(dd for dd in (date(d.year, d.month, k) for k in range(1, calendar.monthrange(d.year, d.month)[1] + 1))
               if dd.weekday() == 4)
    if d != last:
        return "weekly"
    return "quarterly" if d.month % 3 == 0 else "monthly"


def q(a, qs=(0.01, 0.5, 0.99)) -> dict:
    a = np.asarray(a, float)
    return {"n": int(a.size), **{f"q{int(x*100):02d}": float(np.quantile(a, x)) for x in qs}, "max": float(a.max())}


def main() -> None:
    pf = pq.ParquetFile(SETT)
    assert set(pf.schema_arrow.names) == {"column_symbol", "instrument_name", "type", "timestamp_ms"}, "price column?"
    t = pq.read_table(SETT)
    names = t.column("instrument_name").to_pylist()
    typ = t.column("type").to_pylist()
    ts = [datetime.fromtimestamp(x / 1000, tz=timezone.utc) for x in t.column("timestamp_ms").to_pylist()]
    parsed = [parse(n) for n in names]
    out: dict = {"rows": len(names), "unparsed": sum(p is None for p in parsed),
                 "type_kind": dict(Counter(f"{ty}|{p[1] if p else 'x'}" for ty, p in zip(typ, parsed)))}
    # ---- deliveries per expiry date ----
    deliv = [(p, d) for p, ty, d in zip(parsed, typ, ts) if ty == "delivery" and p and p[1] in ("future", "option")]
    out["delivery_rows"] = len(deliv)
    out["delivery_date_eq_name_date"] = sum(1 for p, d in deliv if d.date() == p[2])
    dates_kind = defaultdict(set)          # (ccy, kind) -> expiry dates
    for p, _ in deliv:
        dates_kind[(p[0], p[1])].add(p[2])
    all_dates = sorted(set().union(*dates_kind.values()))
    # ---- futures lifetime (first row of the instrument to delivery) by calendar class ----
    first_seen: dict = {}
    for n, p, d in zip(names, parsed, ts):
        if p and p[1] == "future":
            first_seen[n] = min(first_seen.get(n, d), d)
    life = defaultdict(list)
    for n, p, ty, d in zip(names, parsed, typ, ts):
        if ty == "delivery" and p and p[1] == "future" and date(2018, 6, 1) <= p[2] <= date(2026, 6, 30):
            life[klass(p[2])].append((d - first_seen[n]).total_seconds() / 86400)
    out["future_lifetime_days_by_class"] = {k: q(v, (0.05, 0.5, 0.95)) for k, v in life.items()}
    # ---- option strikes per expiry date (pre-period only) by class ----
    strikes = defaultdict(set)
    for p, _ in deliv:
        if p[1] == "option" and p[2] <= date(2024, 5, 31):
            strikes[(p[0], p[2])].add(p[3])
    sig = defaultdict(list)
    for (ccy, d), s in strikes.items():
        if d >= date(2020, 3, 25):
            sig[f"{ccy}|{klass(d)}"].append(len(s))
    out["option_distinct_strikes_per_expiry_preperiod"] = {k: q(v, (0.05, 0.5, 0.95)) for k, v in sorted(sig.items())}
    # ---- first dates / continuity ----
    firsts = {}
    for ccy in ("BTC", "ETH"):
        for kind in ("option", "future"):
            ds = sorted(dates_kind[(ccy, kind)])
            rec = {k: next((d.isoformat() for d in ds if klass(d) == k), None) for k in ("daily", "weekly", "monthly", "quarterly")}
            end = ds[-1]
            dset = set(ds)
            fr = [d for d in (ds[0] + timedelta(i) for i in range((end - ds[0]).days + 1)) if d.weekday() == 4 and d not in dset]
            al = [d for d in (ds[0] + timedelta(i) for i in range((end - ds[0]).days + 1)) if d not in dset]
            rec["coverage_end"] = end.isoformat()
            rec["every_friday_since"] = (fr[-1] + timedelta(1)).isoformat() if fr else ds[0].isoformat()
            rec["every_day_since"] = (al[-1] + timedelta(1)).isoformat() if al else ds[0].isoformat()
            firsts[f"{ccy}|{kind}"] = rec
    out["firsts_continuity"] = firsts
    # ---- event counts per period / year (pooled dates, any future/option delivery) ----
    def sets(ds):
        c = Counter(klass(d) for d in ds)
        return {"W_ohne_M": c["weekly"], "M_inkl_Q": c["monthly"] + c["quarterly"], "Q": c["quarterly"],
                "daily": c["daily"], "alle": len(ds)}
    btc = set(dates_kind[("BTC", "option")]) | set(dates_kind[("BTC", "future")])
    eth = set(dates_kind[("ETH", "option")]) | set(dates_kind[("ETH", "future")])
    pooled = btc | eth
    out["event_counts"] = {k: sets([d for d in pooled if lo <= d <= hi]) for k, (lo, hi) in PERIODS.items()}
    out["event_counts_both_ccy"] = {k: sets([d for d in (btc & eth) if lo <= d <= hi]) for k, (lo, hi) in PERIODS.items()}
    out["event_counts_per_year"] = {str(y): sets([d for d in pooled if d.year == y and date(2020, 3, 25) <= d <= date(2026, 10, 20)])
                                    for y in range(2020, 2027)}
    out["calendar_days_without_expiry_2020-03-25..2026-06-30"] = sum(
        1 for i in range((date(2026, 6, 30) - date(2020, 3, 25)).days + 1) if date(2020, 3, 25) + timedelta(i) not in pooled)
    out["future_only_event_counts"] = {k: sets([d for d in (set(dates_kind[("BTC", "future")]) | set(dates_kind[("ETH", "future")]))
                                                if lo <= d <= hi]) for k, (lo, hi) in PERIODS.items()}
    # ---- timing: seconds after 08:00:00 UTC of the row's own UTC day ----
    tim = {}
    for key in sorted(set(f"{ty}|{p[1]}" for ty, p in zip(typ, parsed) if p)):
        secs, yrs, dd = [], [], []
        for ty, p, d in zip(typ, parsed, ts):
            if p and f"{ty}|{p[1]}" == key:
                s = (d - datetime(d.year, d.month, d.day, 8, tzinfo=timezone.utc)).total_seconds()
                secs.append(s); yrs.append(d.year); dd.append(d.date().isoformat())
        a = np.array(secs)
        rec = {"all": q(a), "before_0800": int((a < 0).sum()), "gt_60s_rows": int((a > 60).sum()),
               "gt_60s_days": sorted({x for x, s in zip(dd, secs) if s > 60}),
               "q50_by_year": {str(y): float(np.quantile(a[np.array(yrs) == y], 0.5)) for y in sorted(set(yrs))}}
        tim[key] = rec
    out["timing"] = tim
    # ---- deliveryPrices dates ----
    dp = pq.read_table(DELP)
    assert set(dp.column_names) == {"index_name", "date"}
    by = defaultdict(set)
    for i, d in zip(dp.column("index_name").to_pylist(), dp.column("date").to_pylist()):
        by[i].add(date.fromisoformat(d[:10]))
    dpo = {}
    for i, s in by.items():
        ds = sorted(s)
        gaps = [(a, b) for a, b in zip(ds, ds[1:]) if (b - a).days > 1]
        ccy = "BTC" if i.startswith("btc") else "ETH"
        ev = (set(dates_kind[(ccy, "option")]) | set(dates_kind[(ccy, "future")]))
        lo = max(ds[0], min(ev))
        dpo[i] = {"n": len(ds), "first": ds[0].isoformat(), "last": ds[-1].isoformat(),
                  "daily_since": (gaps[-1][1]).isoformat() if gaps else ds[0].isoformat(),
                  "non_friday_before_daily": sum(1 for d in ds if d < gaps[-1][1] and d.weekday() != 4) if gaps else 0,
                  "gap_hist_before_daily": dict(Counter(str((b - a).days) for a, b in zip(ds, ds[1:]) if b <= gaps[-1][1])) if gaps else {},
                  "sym_diff_with_delivery_dates_from": lo.isoformat(),
                  "only_dp": len({d for d in ds if d >= lo} - {d for d in ev if lo <= d <= ds[-1]}),
                  "only_deliv": len({d for d in ev if lo <= d <= ds[-1]} - {d for d in ds if d >= lo})}
    out["deliveryPrices"] = dpo
    (HERE / "a2_review.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("rows", "unparsed", "type_kind", "delivery_rows", "delivery_date_eq_name_date")}, indent=0))


if __name__ == "__main__":
    main()
