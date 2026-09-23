"""Read-only: are the frames of one harvest orderbook day duplicated (DEC-76)?
Usage: python scinance3-impl/handoff_local/wp10b_dup_check.py BTCUSDT 2026-08-13 [2026-08-11 ...]
Prints total frames, distinct (ts_exchange_ms, payload_json) frames, and the
share of exact duplicates, plus the same for a normal reference day if given.
"""
import sys
from pathlib import Path
import duckdb

symbol, *days = sys.argv[1:]
con = duckdb.connect()
STREAMS = [("bybit", "orderbook"), ("bybit", "publicTrade"), ("bybit", "tickers"),
           ("deribit", "publicTrade"), ("deribit", "dvol")]
for day in days:
    for exch, stream in STREAMS:
        root = Path("data/harvest/raw") / exch / stream
        cands = [root / f"symbol={symbol}"] if exch == "bybit" else sorted(root.glob("symbol=*"))[:1]
        for sym_dir in cands:
            part = sym_dir / f"date={day}"
            if not part.is_dir():
                print(f"{exch}/{stream} {sym_dir.name} {day}: keine Partition")
                continue
            glob = str(part / "*.parquet")
            try:
                n, nd = con.execute("SELECT count(*), count(DISTINCT (ts_local_ns, topic, payload_json)) "
                                    "FROM read_parquet(?, union_by_name=1)", [glob]).fetchone()
            except Exception as exc:  # noqa: BLE001
                print(f"{exch}/{stream} {sym_dir.name} {day}: Lesefehler {exc}")
                continue
            print(f"{exch}/{stream} {sym_dir.name} {day}: rows={n} distinct={nd} "
                  f"exact_duplicates={n - nd} ({100.0 * (n - nd) / max(n, 1):.1f} %)")
