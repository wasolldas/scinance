"""H-27 data probe (C.8) on deribit/dvol BTC/ETH 2021-03-24..2026-10-16 -- no level output.

Allowed (KONTAMINATION.md 5, DEC-96 E3): rows per day, gaps, timestamps, schema, equality /
continuity checks WITHOUT level output.  Continuity (close of hour h == open of hour h+1, and the
daily seam close(23h, d) == open(00h, d+1)) is evaluated only on days <= 2026-06-30 (blind seal
from 2026-07-01: rows/timestamps/schema only).  Magnitudes of mismatches are printed only for
days <= 2024-06-30 (DVOL level rule); later periods report counts only.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h27_common import harvest  # noqa: E402

LO, HI = "2021-03-24", "2026-10-16"
SEAL = "2026-06-30"          # continuity checks only up to here
LEVEL_OK = "2024-06-30"      # mismatch magnitudes only up to here
SEAM = ("2025-07-31", "2025-08-01")


def period(d: str) -> str:
    if d <= LEVEL_OK:
        return "a_2021-03-24..2024-06-30"
    if d <= "2025-07-31":
        return "b_2024-07-01..2025-07-31 (backfill)"
    if d <= SEAL:
        return "c_2025-08-01..2026-06-30 (stream)"
    return "d_2026-07-01..2026-10-16 (blind, schema only)"


def main() -> None:
    hd = harvest()
    out: dict = {}
    for sym in ("BTC", "ETH"):
        df = hd.load("dvol", [sym], LO, HI, exchange="deribit")
        by_day: dict[str, dict[int, dict]] = defaultdict(dict)
        dup = 0
        keysets: dict[str, Counter] = defaultdict(Counter)
        topics: dict[str, Counter] = defaultdict(Counter)
        ts_match = Counter()
        part_mismatch = 0
        nonnum = 0
        for row in df.select(["ts_exchange_ms", "topic", "payload_json"]).iter_rows(named=True):
            obj = json.loads(row["payload_json"])
            ts = int(obj["timestamp"])
            dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
            day = dt.date().isoformat()
            per = period(day)
            keysets[per][",".join(sorted(obj.keys()))] += 1
            topics[per][row["topic"]] += 1
            ts_match[per + (" ts_exchange_ms==timestamp" if row["ts_exchange_ms"] == ts else " ts_exchange_ms!=timestamp")] += 1
            if (dt.minute, dt.second) != (0, 0):
                part_mismatch += 1
            vals = {}
            for k in ("open", "high", "low", "close"):
                try:
                    vals[k] = float(obj[k])
                except (TypeError, ValueError, KeyError):
                    nonnum += 1
            if dt.hour in by_day[day]:
                dup += 1
            by_day[day][dt.hour] = vals
        days = sorted(d for d in by_day if LO <= d <= HI)
        rows_per_day = Counter(len(by_day[d]) for d in days)
        missing_23h = [d for d in days if 23 not in by_day[d]]
        # continuity (equality only)
        intra = defaultdict(Counter)
        seam = defaultdict(Counter)
        seam_mag_a = []
        intra_mag_a = []
        for i, d in enumerate(days):
            if d > SEAL:
                break
            per = period(d)
            hrs = by_day[d]
            for h in range(23):
                if h in hrs and h + 1 in hrs and "close" in hrs[h] and "open" in hrs[h + 1]:
                    eq = hrs[h]["close"] == hrs[h + 1]["open"]
                    intra[per]["equal" if eq else "differ"] += 1
                    if not eq and d <= LEVEL_OK:
                        intra_mag_a.append(abs(hrs[h]["close"] - hrs[h + 1]["open"]))
            if i + 1 < len(days) and days[i + 1] <= SEAL:
                nxt = by_day[days[i + 1]]
                if 23 in hrs and 0 in nxt:
                    eq = hrs[23]["close"] == nxt[0]["open"]
                    seam[per]["equal" if eq else "differ"] += 1
                    if not eq and d <= LEVEL_OK:
                        seam_mag_a.append(abs(hrs[23]["close"] - nxt[0]["open"]))
        s0, s1 = SEAM
        seam_eq = (23 in by_day.get(s0, {}) and 0 in by_day.get(s1, {})
                   and by_day[s0][23]["close"] == by_day[s1][0]["open"])
        # hour-structure equality across the seam (schema only)
        out[sym] = {
            "n_rows": df.height, "n_days": len(days), "first_day": days[0], "last_day": days[-1],
            "rows_per_day": dict(rows_per_day), "duplicate_hours": dup,
            "timestamps_not_on_full_hour": part_mismatch, "non_numeric_ohlc_fields": nonnum,
            "days_without_23h_candle": missing_23h[:10], "n_days_without_23h_candle": len(missing_23h),
            "payload_keysets_by_period": {k: dict(v) for k, v in keysets.items()},
            "topics_by_period": {k: dict(v) for k, v in topics.items()},
            "ts_exchange_ms_vs_payload_timestamp": dict(ts_match),
            "intraday_continuity_close_h_eq_open_h1": {k: dict(v) for k, v in intra.items()},
            "day_seam_close23_eq_open00_next": {k: dict(v) for k, v in seam.items()},
            "seam_2025_07_31_to_08_01_equal": bool(seam_eq),
            "mismatch_magnitude_upto_2024_06_30": {
                "intraday_n": len(intra_mag_a),
                "intraday_max_abs_volpts": max(intra_mag_a) if intra_mag_a else 0.0,
                "seam_n": len(seam_mag_a),
                "seam_max_abs_volpts": max(seam_mag_a) if seam_mag_a else 0.0},
        }
    (Path(__file__).resolve().parent / "dvol_probe.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
