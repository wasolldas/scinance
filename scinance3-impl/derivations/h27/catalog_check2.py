"""H-27 continuation (2026-10-17): ONE catalog refresh and coverage facts (no values).

deribit/dvol BTC/ETH 2021-03-24..2026-10-16 and bybit/publicTrade BTCUSDT/ETHUSDT from 2026-07-01:
partitions, gaps, rows/status counts.  Prints no host and no data value.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harvest_client"))
import harvest_data as hd  # noqa: E402
import polars as pl  # noqa: E402


def main() -> None:
    hd.configure(cache_dir=HERE / "hcache")
    meta = hd.info()
    safe_meta = {k: meta[k] for k in meta if k in (
        "generated_at_utc", "partitions_file", "partitions_bytes", "partitions_sha256",
        "client_version", "schema_version")}
    cat = hd.catalog(refresh=True)
    out = {"meta": safe_meta, "client_version_local": hd.__version__, "n_partitions": cat.height,
           "columns": cat.columns}
    for ex, st, syms, lo, hi in [("deribit", "dvol", ["BTC", "ETH"], "2021-03-24", "2026-10-16"),
                                 ("bybit", "publicTrade", ["BTCUSDT", "ETHUSDT"], "2026-07-01", "2026-10-16"),
                                 ("bybit", "publicTrade", ["BTCUSDT", "ETHUSDT"], "2021-03-01", "2024-05-31")]:
        for s in syms:
            c = cat.filter((pl.col("exchange") == ex) & (pl.col("stream") == st) & (pl.col("symbol") == s)
                           & (pl.col("date") >= lo) & (pl.col("date") <= hi))
            g = hd.gaps(st, [s], lo, hi, exchange=ex)
            out[f"{ex}/{st}/{s} {lo}..{hi}"] = {
                "n": c.height, "first": c["date"].min(), "last": c["date"].max(), "n_gaps": g.height,
                "gaps_head": g["date"].head(10).to_list(),
                "status": {str(k): int(v) for k, v in c["status"].value_counts().iter_rows()} if "status" in c.columns else None,
                "rows": {str(k): int(v) for k, v in c["rows"].value_counts().sort("count", descending=True).head(5).iter_rows()} if st == "dvol" else None,
                "bytes_total_mb": round(c["bytes"].sum() / 1e6, 1),
            }
    (HERE / "catalog_check2.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
