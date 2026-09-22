"""Read-only: are the frames of one harvest orderbook day duplicated (DEC-76)?
Usage: python scinance3-impl/handoff_local/wp10b_dup_check.py BTCUSDT 2026-08-13 [2026-08-11 ...]
Prints total frames, distinct (ts_exchange_ms, payload_json) frames, and the
share of exact duplicates, plus the same for a normal reference day if given.
"""
import sys
from pathlib import Path
import duckdb

symbol, *days = sys.argv[1:]
base = Path("data/harvest/raw/bybit/orderbook") / f"symbol={symbol}"
con = duckdb.connect()
for day in days:
    glob = str(base / f"date={day}" / "*.parquet")
    n, nd, nts = con.execute(
        "SELECT count(*), count(DISTINCT (ts_exchange_ms, payload_json)), count(DISTINCT ts_exchange_ms) "
        "FROM read_parquet(?)", [glob]).fetchone()
    print(f"{symbol} {day}: frames={n} distinct_frames={nd} distinct_ts={nts} "
          f"exact_duplicates={n - nd} ({100.0 * (n - nd) / max(n, 1):.1f} %)")
