"""Review recomputation of the event size (sum of 'position' of option deliveries per expiry day and
class) from the raw settlement partitions.  ALLOW-LIST: only type, instrument_name, timestamp,
position are extracted (own Arrow regexes); the payload is never JSON-decoded; partitions with
date > 2026-06-30 are never opened.  Counts and sums only."""
from __future__ import annotations

import calendar
import glob
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

RAW = Path("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/hcache/raw/deribit/rest.settlements")
LAST, FIRST = "2026-06-30", "2020-03-25"
ALLOWED = {"type": r'"type"\s*:\s*"([a-z_]+)"',
           "instrument_name": r'"instrument_name"\s*:\s*"([^"]+)"',
           "timestamp": r'"timestamp"\s*:\s*([0-9]+)',
           "position": r'"position"\s*:\s*([-0-9.eE+]+|null)'}
FORBID = re.compile(r"price|profit|loss|mark|index", re.I)
for k in ALLOWED:
    assert not FORBID.search(k)
OPT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})-[0-9d.]+-[CP]$")
FUT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})$")
MON = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}


def extract(path):
    col = pq.read_table(path, columns=["payload_json"]).column("payload_json")
    out = {}
    for k, rx in ALLOWED.items():
        out[k] = pc.struct_field(pc.extract_regex(col, pattern=rx.replace("(", "(?P<v>", 1)), [0]).to_pylist()
    del col
    return out


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


def main():
    per_day = defaultdict(float)        # (ccy, day) -> contracts
    fut_rows = defaultdict(int)         # (ccy, fine class) -> futures delivery rows (count only)
    other_names = defaultdict(int)
    seen = set()
    n_dup = 0
    for ccy in ("BTC", "ETH"):
        for dpath in sorted(glob.glob(str(RAW / f"symbol={ccy}" / "date=*"))):
            day = dpath.rsplit("date=", 1)[1]
            if not (FIRST <= day <= LAST):
                continue
            for f in sorted(glob.glob(dpath + "/*.parquet")):
                e = extract(f)
                for ty, nm, ts, pos in zip(e["type"], e["instrument_name"], e["timestamp"], e["position"]):
                    if ty != "delivery":
                        continue
                    if (nm, ts) in seen:
                        n_dup += 1
                        continue
                    seen.add((nm, ts))
                    m = OPT.match(nm or "")
                    if m:
                        exp = date(2000 + int(m.group(4)), MON[m.group(3)], int(m.group(2)))
                        assert str(exp) <= LAST
                        per_day[(ccy, exp)] += float(pos)
                        continue
                    m = FUT.match(nm or "")
                    if m:
                        exp = date(2000 + int(m.group(4)), MON[m.group(3)], int(m.group(2)))
                        fut_rows[(ccy, fine(exp))] += 1
                        continue
                    other_names[re.sub(r"[0-9]", "#", nm or "None")] += 1
    periods = {"nuis": ("2021-03-24", "2024-05-31"), "W1": ("2024-07-01", "2025-06-30"),
               "W2": ("2025-07-01", "2026-06-28")}
    excl = {date(2020, 8, 27), date(2024, 8, 19)}
    res = {"dup_rows": n_dup, "non_option_non_future_delivery_name_patterns": dict(other_names),
           "future_delivery_rows_by_class": {f"{a}|{b}": v for (a, b), v in sorted(fut_rows.items())}}
    for pl, (lo, hi) in periods.items():
        a, b = date.fromisoformat(lo), date.fromisoformat(hi)
        for ccy in ("BTC", "ETH"):
            by = defaultdict(list)
            for i in range((b - a).days + 1):
                d = a + timedelta(i)
                if d in excl or (ccy, d) not in per_day:
                    continue
                fc = fine(d)
                by[fc].append(per_day[(ccy, d)])
                if fc.startswith("FRI"):
                    by["FRI"].append(per_day[(ccy, d)])
                if fc in ("FRI_M", "FRI_Q"):
                    by["FRI_MQ"].append(per_day[(ccy, d)])
            q50 = {k: float(np.quantile(v, 0.5)) for k, v in by.items()}
            res[f"{pl}|{ccy}"] = {"n": {k: len(v) for k, v in by.items()}, "q50": q50,
                                  "ratio_FRI/MODO": q50["FRI"] / q50["MODO"],
                                  "ratio_FRI_MQ/FRI_W": q50["FRI_MQ"] / q50["FRI_W"],
                                  "ratio_FRI_W/MODO": q50["FRI_W"] / q50["MODO"]}
    # within-week minimum Friday / q50(Mo-Do same ISO week), whole 2020-03-25..2026-06-28
    for ccy in ("BTC", "ETH"):
        wk = defaultdict(lambda: {"f": None, "m": []})
        for (c, d), v in per_day.items():
            if c != ccy or d in excl or str(d) > "2026-06-28" or str(d) < "2021-03-24":
                continue
            fc = fine(d)
            k = d.isocalendar()[:2]
            if fc.startswith("FRI"):
                wk[k]["f"] = v
            elif fc == "MODO":
                wk[k]["m"].append(v)
        rr = [w["f"] / float(np.quantile(w["m"], 0.5)) for w in wk.values() if w["f"] is not None and len(w["m"]) >= 2]
        res[f"within_week_min_{ccy}_2021-03-24..2026-06-28"] = float(min(rr))
    (Path(__file__).resolve().parent / "rv_oi.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r, indent=1))
