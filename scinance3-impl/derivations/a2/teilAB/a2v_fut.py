"""Fassung 2, A-3 (R-14): Deribit FUTURES delivery calendar from the raw settlement partitions
<= 2026-06-30 -- instrument names, type and date only (no position, no price).  Counts only."""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import pyarrow.compute as pc

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a2v_common as c  # noqa: E402

WINDOWS = {"vorperiode_2020-03-25..2024-05-31": ("2020-03-25", "2024-05-31"),
           "nuisance_2021-03-24..2024-05-31": ("2021-03-24", "2024-05-31"),
           "W1_2024-07-01..2025-06-30": ("2024-07-01", "2025-06-30"),
           "W2_DEC99_2025-07-01..2026-06-28": ("2025-07-01", "2026-06-28"),
           "gesamt_bis_2026-06-30": ("0000-00-00", "2026-06-30")}
FINE = ("FRI_W", "FRI_M", "FRI_Q", "MODO", "WE")


def parse_future(name: str):
    m = c.RE_FUT.match(name or "")
    if not m:
        return None, None
    return m.group(1), date(2000 + int(m.group(4)), c.MON[m.group(3)], int(m.group(2)))


def main() -> dict:
    fut = defaultdict(set)          # (ccy, expiry date) -> set of instrument names
    checks = {}
    for ccy in ("BTC", "ETH"):
        parts = c.raw_partitions_upto(ccy)
        n_rows = n_fut = n_bad = 0
        for day, f in parts:
            t = c.read_settlement_fields(f, ("type", "instrument_name", "timestamp"))
            n_rows += t.num_rows
            t = t.filter(pc.equal(t.column("type"), "delivery"))
            for nm, tsv in zip(t.column("instrument_name").to_pylist(), t.column("timestamp").to_pylist()):
                cc, exp = parse_future(nm)
                if exp is None:
                    continue
                assert cc == ccy
                ts_day = datetime.fromtimestamp(tsv / 1000.0, tz=timezone.utc).date().isoformat()
                if not (exp.isoformat() == day == ts_day):
                    n_bad += 1
                    continue
                n_fut += 1
                fut[(ccy, exp)].add(nm)
        checks[ccy] = {"partitions_read": len(parts), "first_partition": parts[0][0], "last_partition": parts[-1][0],
                       "rows_all_types": n_rows, "future_delivery_rows": n_fut,
                       "rows_expiry_ne_partition_or_ts_date": n_bad}
    out: dict = {"label": c.LABEL, "quelle": "S:a2v_fut.py (R-14; nur Namen/Typ/Datum der Futures-Deliveries)",
                 "raw_partition_checks": checks}
    first_nonfri = {}
    for ccy in ("BTC", "ETH"):
        ds = sorted(d for (cc, d) in fut if cc == ccy)
        nf = [d for d in ds if d.weekday() != 4]
        first_nonfri[ccy] = {"first_future_delivery": ds[0].isoformat(), "last_future_delivery": ds[-1].isoformat(),
                             "first_non_friday_future_delivery": nf[0].isoformat() if nf else None,
                             "non_friday_future_delivery_days_total": len(nf),
                             "non_friday_days_before_2026": sum(1 for d in nf if d.year < 2026)}
    out["first_non_friday_future_delivery"] = first_nonfri
    per_win = {}
    for lab, (lo, hi) in WINDOWS.items():
        cell = {}
        for ccy in ("BTC", "ETH"):
            deliv = {k: 0 for k in FINE}
            days = {k: 0 for k in FINE}
            for (cc, d), names in fut.items():
                if cc != ccy or not (lo <= d.isoformat() <= hi):
                    continue
                fc = c.day_class(d)
                deliv[fc] += len(names)
                days[fc] += 1
            cell[ccy] = {"future_deliveries_by_class": deliv, "days_with_future_delivery_by_class": days}
        # Mo-Do days with a futures delivery (one / both currencies)
        modo_days = set()
        both = 0
        allmodo = [d for d in (c.days_range(lo if lo > "2000" else "2017-05-25", hi)) if c.day_class(d) == "MODO"]
        for d in allmodo:
            b = ("BTC", d) in fut
            e = ("ETH", d) in fut
            if b or e:
                modo_days.add(d)
            if b and e:
                both += 1
        we_days = [d for d in (c.days_range(lo if lo > "2000" else "2017-05-25", hi)) if c.day_class(d) == "WE"
                   and (("BTC", d) in fut or ("ETH", d) in fut)]
        cell["modo_days_total"] = len(allmodo)
        cell["modo_days_with_future_delivery_any_ccy"] = len(modo_days)
        cell["modo_days_with_future_delivery_both_ccy"] = both
        cell["we_days_with_future_delivery_any_ccy"] = len(we_days)
        cell["first_modo_day_with_future_delivery"] = min(modo_days).isoformat() if modo_days else None
        per_win[lab] = cell
    out["by_window"] = per_win
    # Mo-Do days with futures in W2 per month (where they lie)
    lo, hi = WINDOWS["W2_DEC99_2025-07-01..2026-06-28"]
    by_month = defaultdict(int)
    for d in c.days_range(lo, hi):
        if c.day_class(d) == "MODO" and (("BTC", d) in fut or ("ETH", d) in fut):
            by_month[d.strftime("%Y-%m")] += 1
    out["W2_modo_days_with_future_by_month"] = dict(sorted(by_month.items()))
    c.check_out(out)
    return out


if __name__ == "__main__":
    print("sha256", c.dump(main(), c.WORK / "a2v_fut.json"))
