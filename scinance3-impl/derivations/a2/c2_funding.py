"""C-2: Bybit funding interval BTCUSDT/ETHUSDT from funding timestamps only (no rate exists or is read; R-C10/R-C18):
W2 (2025-07-01..2026-06-28) and, Fassung 2, the pre-period 2021-03-24..2024-05-31 (pilot) and W1 2024-07-01..2025-06-30.
Prints only sha256 and counts.  Output: work/c2.json.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c_common as cc  # noqa: E402

EIGHT_H = ("00:00:00", "08:00:00", "16:00:00")
PERIODS = {  # name: (file, first day, last day)
    "VP_pilot_2021-03-24..2024-05-31": (cc.F_FUND_PRE, "2021-03-24", "2024-05-31"),
    "W1_2024-07-01..2025-06-30": (cc.F_FUND_PRE, "2024-07-01", "2025-06-30"),
    "W2_2025-07-01..2026-06-28": (cc.F_FUND, cc.W2_FUND_FIRST, cc.W2_FUND_LAST),
}
FILE_RANGE = {cc.F_FUND_PRE: ("2021-03-24", "2025-06-30"), cc.F_FUND: (cc.W2_FUND_FIRST, cc.W2_FUND_LAST)}


def read_fund(path: Path) -> tuple[dict, dict]:
    cols = set(pq.ParquetFile(path).schema_arrow.names)
    if cols != {"symbol", "fts"}:
        raise RuntimeError(f"funding columns {sorted(cols)}")
    t = pq.read_table(path, columns=["symbol", "fts"])
    sym = t.column("symbol").to_pylist()
    ms = cc._ms(t.column("fts").to_numpy())
    lo, hi = (date.fromisoformat(x) for x in FILE_RANGE[path])
    dts = [datetime.fromtimestamp(m / 1000.0, tz=timezone.utc) for m in ms.tolist()]
    if min(d.date() for d in dts) < lo or max(d.date() for d in dts) > hi:
        raise RuntimeError(f"funding timestamps outside {lo}..{hi}")
    per = defaultdict(lambda: defaultdict(list))
    seen, dup, off = set(), 0, 0
    for s, m, d in zip(sym, ms.tolist(), dts):
        if (s, m) in seen:
            dup += 1
            continue
        seen.add((s, m))
        if m % 1000 != 0 or d.second != 0:
            off += 1
        per[s][d.date()].append(d.strftime("%H:%M:%S"))
    return per, {"rows": t.num_rows, "duplicates_dropped": dup, "timestamps_off_full_second": off,
                 "file_range": list(FILE_RANGE[path])}


def protective_rule_hits(per: dict, d: date) -> bool:
    """G-C8: no 08:00:00 funding in one of the two symbols, or a funding time stamp in [07:30, 08:00)."""
    for s in ("BTCUSDT", "ETHUSDT"):
        ts = per[s].get(d, [])
        if "08:00:00" not in ts or any("07:30:00" <= x < "08:00:00" for x in ts):
            return True
    return False


def period_block(per: dict, lo: str, hi: str, flags: dict) -> dict:
    days = cc.days_range(lo, hi)
    S = cc.window_sets(lo, hi, flags)
    sets = {"E_Freitage": set(S["E"]), "P2ss_MoDo_ohne_Futures": set(S["P2ss"]),
            "MoDo_alle": {d for d in days if d.weekday() < 4 and not cc.day_flags(d, flags)["outlier"]},
            "Wochenende": {d for d in days if d.weekday() >= 5}}
    out_sym = {}
    for s in ("BTCUSDT", "ETHUSDT"):
        pd = per[s]
        patt = Counter()
        non8 = []
        by_month = defaultdict(lambda: {"days": 0, "days_8h": 0, "days_not_8h": 0, "timestamps": 0})
        for d in days:
            times = tuple(sorted(pd.get(d, [])))
            is8 = times == EIGHT_H
            patt[f"{len(times)}x" if not is8 else "8h_00_08_16"] += 1
            mk = d.strftime("%Y-%m")
            by_month[mk]["days"] += 1
            by_month[mk]["timestamps"] += len(times)
            by_month[mk]["days_8h" if is8 else "days_not_8h"] += 1
            if not is8:
                non8.append({"day": d.isoformat(), "n": len(times), "times_utc": list(times)})
        share = {}
        for nm, st in sets.items():
            st = sorted(st)
            has08 = sum("08:00:00" in pd.get(d, []) for d in st)
            share[nm] = {"n_days": len(st), "days_with_funding_0800": has08,
                         "share_0800": has08 / len(st) if st else None,
                         "days_8h_pattern": sum(tuple(sorted(pd.get(d, []))) == EIGHT_H for d in st),
                         "days_with_funding_in_0700_0800": sum(any("07:00:00" <= x < "08:00:00" for x in pd.get(d, []))
                                                               for d in st),
                         "days_with_funding_in_0730_0800": sum(any("07:30:00" <= x < "08:00:00" for x in pd.get(d, []))
                                                               for d in st)}
        out_sym[s] = {"days": len(days), "days_without_timestamp": sum(len(pd.get(d, [])) == 0 for d in days),
                      "timestamps": int(sum(len(pd.get(d, [])) for d in days)),
                      "pattern_counts": dict(sorted(patt.items())), "days_8h": patt["8h_00_08_16"],
                      "share_days_8h": patt["8h_00_08_16"] / len(days),
                      "by_month": {k: by_month[k] for k in sorted(by_month)}, "days_not_8h": non8[:50],
                      "n_days_not_8h": len(non8), "share_by_set": share}
    both = {}
    for nm, st in sets.items():
        st = sorted(st)
        ok = sum(all("08:00:00" in per[s].get(d, []) for s in ("BTCUSDT", "ETHUSDT")) for d in st)
        ok8 = sum(all(tuple(sorted(per[s].get(d, []))) == EIGHT_H for s in ("BTCUSDT", "ETHUSDT")) for d in st)
        both[nm] = {"n_days": len(st), "days_funding_0800_both": ok, "share_0800_both": ok / len(st) if st else None,
                    "days_8h_both": ok8, "share_8h_both": ok8 / len(st) if st else None,
                    "days_hit_by_protective_rule_G_C8": sum(protective_rule_hits(per, d) for d in st)}
    return {"range": [lo, hi], "per_symbol": out_sym, "both_symbols": both}


def main() -> dict:
    inputs = cc.check_inputs([cc.F_FUND.name, cc.F_FUND_PRE.name, cc.F_CAL.name])
    flags, _ = cc.load_calendar_flags()
    files = {}
    data = {}
    for path in (cc.F_FUND_PRE, cc.F_FUND):
        per, meta = read_fund(path)
        data[path], files[path.name] = per, meta
    periods = {nm: period_block(data[f], lo, hi, flags) for nm, (f, lo, hi) in PERIODS.items()}
    return {"label": cc.LABEL, "rules": "R-C10, R-C18", "inputs_sha256": inputs, "files": files,
            "periods": periods, "eight_hour_rule": "Tag mit genau {00:00, 08:00, 16:00} UTC",
            "protective_rule_G_C8": "Tag aus Ereignis- und Placebo-Menge, wenn ein Symbol kein Funding um 08:00:00 "
                                    "UTC hat oder einen Termin in [07:30, 08:00)"}


if __name__ == "__main__":
    res = main()
    h = cc.dump(res, cc.WORK / "c2.json")
    print("c2.json sha256", h)
    print("counts", {k: {s: v["per_symbol"][s]["days_8h"] for s in v["per_symbol"]} for k, v in res["periods"].items()})
