"""Read-only diagnosis for the WP-10(B) fillshadow store (Registrar-Rueckfragen DEC-68/71).

Lists per symbol the days by status (ok / no_raw / discarded / not_manifest_done),
prints the no_raw day list, and for every discarded day counts the orderbook
TOPICS in the raw harvest partition (orderbook.50 vs orderbook.1000 mixing =
the registrar's hypothesis for 277,792 sequence breaks). Never writes.
Usage: python scinance3-impl/handoff_local/wp10b_store_status.py [store_root] [harvest_base]
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

store = Path(sys.argv[1] if len(sys.argv) > 1 else "data/l2tilt") / "fillshadow_1min"
harvest = Path(sys.argv[2] if len(sys.argv) > 2 else "data/harvest")
try:
    import duckdb
except ImportError:  # pragma: no cover
    duckdb = None

for sym_dir in sorted(store.glob("exchange=*/symbol=*")):
    symbol = sym_dir.name.split("=", 1)[1]
    by_status = defaultdict(list)
    for part in sorted(sym_dir.glob("date=*")):
        mp = part / "manifest.json"
        if not mp.is_file():
            by_status["manifest_missing"].append(part.name[5:])
            continue
        meta = json.loads(mp.read_text(encoding="utf-8"))
        by_status[str(meta.get("status"))].append((part.name[5:], meta.get("reason", ""), meta.get("n_seq_breaks")))
    print(f"\n== {symbol} ==")
    for st, items in sorted(by_status.items()):
        print(f"  {st}: {len(items)}")
    print("  no_raw:", [d for d, *_ in by_status.get("no_raw", [])])
    ok_days = [d for d, *_ in by_status.get("ok", [])]
    sample = [(d, "ok-Stichprobe", None) for d in (ok_days[:1] + ok_days[-1:])]
    for day, reason, nb in list(by_status.get("discarded", [])) + sample:
        print(f"  {reason if reason == 'ok-Stichprobe' else 'discarded'} {day}: {reason}")
        part = harvest / "raw" / "bybit" / "orderbook" / f"symbol={symbol}" / f"date={day}"
        if duckdb is None or not part.is_dir():
            print("    (duckdb fehlt oder Partition nicht vorhanden)")
            continue
        try:
            rows = duckdb.connect().execute(
                "SELECT topic, count(*) FROM read_parquet(?) GROUP BY topic ORDER BY topic",
                [str(part / "*.parquet")]).fetchall()
            print("    topics:", rows)
        except Exception as exc:  # noqa: BLE001
            print("    topic-Zaehlung fehlgeschlagen:", exc)
