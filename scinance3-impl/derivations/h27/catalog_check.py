"""H-27 derivation: ONE catalog refresh and the deribit/dvol coverage check.

Order of the assignment: run once after stage 0 and the data-independent part of stage 1.
Downloads the catalog exactly once (refresh=True); later processes reuse the cached file via
``h27_common.harvest()`` (sets the client's in-process catalog from the local copy, no new
download).  Prints/stores only coverage facts (dates, counts, gaps) -- no DVOL values.
No endpoint/host is printed or stored.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harvest_client"))
import harvest_data as hd  # noqa: E402
import polars as pl  # noqa: E402

START = "2021-03-24"
END = "2026-07-31"


def main() -> None:
    hd.configure(cache_dir=HERE / "hcache")
    meta = hd.info()
    stamp = meta.get("generated_at_utc")
    cat = hd.catalog(refresh=True)
    d = cat.filter((pl.col("exchange") == "deribit") & (pl.col("stream") == "dvol"))
    out: dict = {"catalog_generated_at_utc": stamp, "catalog_partitions": cat.height,
                 "dvol": {}}
    for sym in ("BTC", "ETH"):
        s = d.filter(pl.col("symbol") == sym)
        gaps = hd.gaps("dvol", [sym], START, END, exchange="deribit")
        out["dvol"][sym] = {
            "n_partitions": s.height,
            "first_date": s["date"].min(), "last_date": s["date"].max(),
            "n_in_range": s.filter((pl.col("date") >= START) & (pl.col("date") <= END)).height,
            "n_gaps_in_range": gaps.height,
            "gaps_head": gaps["date"].head(20).to_list(),
            "rows_value_counts": {str(k): int(v) for k, v in
                                  s["rows"].value_counts().iter_rows()},
            "status_value_counts": {str(k): int(v) for k, v in
                                    s["status"].value_counts().iter_rows()},
            "location_value_counts": {str(k): int(v) for k, v in
                                      s["location"].value_counts().iter_rows()},
        }
    out["dvol_from_2021_03_24"] = all(
        out["dvol"][s]["first_date"] is not None and out["dvol"][s]["first_date"] <= START
        for s in ("BTC", "ETH"))
    (HERE / "catalog_check.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
