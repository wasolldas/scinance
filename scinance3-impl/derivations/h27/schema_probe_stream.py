"""H-27 data probe on the EXISTING deribit/dvol stream (from 2025-08-01): schema only.

Allowed after 2024-07-01: rows per day, timestamps, schema.  Prints NO DVOL value: payloads are
parsed and only their structure (type, length / key names) and the bucket timestamps (as UTC
hour of day) are reported.  Four partitions per symbol, a few KB.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from h27_common import harvest  # noqa: E402

DAYS = ["2025-08-01", "2025-08-31", "2026-03-20", "2026-06-30"]


def shape(obj) -> str:
    if isinstance(obj, dict):
        return "dict{" + ",".join(sorted(obj.keys())) + "}"
    if isinstance(obj, list):
        inner = sorted({type(x).__name__ for x in obj})
        return f"list[len={len(obj)}; types={inner}]"
    return type(obj).__name__


def main() -> None:
    hd = harvest()
    out = {}
    for sym in ("BTC", "ETH"):
        for day in DAYS:
            df = hd.load("dvol", [sym], day, day, exchange="deribit")
            shapes = Counter()
            hours = []
            topics = Counter(df["topic"].to_list()) if "topic" in df.columns else {}
            for pj in df["payload_json"].to_list():
                obj = json.loads(pj)
                shapes[shape(obj)] += 1
                ts = None
                if isinstance(obj, list) and obj:
                    ts = obj[0]
                elif isinstance(obj, dict):
                    for k in ("timestamp", "ts", "t", "tick"):
                        if k in obj:
                            ts = obj[k]
                            break
                if isinstance(ts, (int, float)):
                    dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                    hours.append(f"{dt.date().isoformat()}T{dt.hour:02d}")
            ex_ms = df["ts_exchange_ms"].drop_nulls().to_list() if "ts_exchange_ms" in df.columns else []
            out[f"{sym} {day}"] = {
                "rows": df.height, "columns": df.columns, "payload_shapes": dict(shapes),
                "topics": dict(topics), "bucket_hours_first_last": hours[:2] + hours[-2:],
                "n_distinct_bucket_hours": len(set(hours)),
                "ts_exchange_ms_nonnull": len(ex_ms),
            }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
