"""Read-only view of the external harvester manifest for the WP-10(B) inputs.

Prints, for bybit orderbook/publicTrade x BTCUSDT/ETHUSDT: DONE-day count and
range since 2026-06-22, the non-DONE statuses in that range, and -- as a
harvester health line -- the newest date per stream over ALL symbols.
Never writes. Usage: python scinance3-impl/handoff_local/harvest_manifest_status.py
"""
import sqlite3
from pathlib import Path

CANDIDATES = [
    Path("data/harvest/state/harvest_manifest.backup.sqlite"),
    Path("data/harvest/state/harvest_manifest.sqlite"),
]
START = "2026-06-22"

path = next((p for p in CANDIDATES if p.is_file()), None)
if path is None:
    raise SystemExit(f"kein Manifest gefunden: {[str(p) for p in CANDIDATES]}")
print(f"Manifest: {path}")
con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)

print("\n== DONE-Tage seit", START, "(bybit orderbook/publicTrade, BTCUSDT/ETHUSDT) ==")
q = ("SELECT stream, symbol, count(*), min(date), max(date) FROM partitions "
     "WHERE exchange='bybit' AND stream IN ('orderbook','publicTrade') "
     "AND symbol IN ('BTCUSDT','ETHUSDT') AND status='DONE' AND date>=? "
     "GROUP BY stream, symbol ORDER BY stream, symbol")
for r in con.execute(q, (START,)):
    print(r)

print("\n== Nicht-DONE-Status im selben Bereich ==")
q = ("SELECT stream, symbol, status, count(*), min(date), max(date) FROM partitions "
     "WHERE exchange='bybit' AND stream IN ('orderbook','publicTrade') "
     "AND symbol IN ('BTCUSDT','ETHUSDT') AND status<>'DONE' AND date>=? "
     "GROUP BY stream, symbol, status ORDER BY stream, symbol, status")
rows = list(con.execute(q, (START,)))
print(rows if rows else "(keine)")

print("\n== Welche Stream-Namen kennt das Manifest fuer bybit? ==")
for r in con.execute("SELECT stream, count(DISTINCT symbol), max(date) FROM partitions "
                     "WHERE exchange='bybit' GROUP BY stream ORDER BY stream"):
    print(r)

print("\n== Harvester-Gesundheit: neuester Tag je Exchange/Stream (alle Symbole) ==")
for r in con.execute("SELECT exchange, stream, max(date), max(ts_done) FROM partitions "
                     "GROUP BY exchange, stream ORDER BY exchange, stream"):
    print(r)

print("\n== Detail: bybit orderbook BTCUSDT, drei Tage (Kompaktierungs-Semantik) ==")
for r in con.execute("SELECT date, status, rows, size_bytes, archived_at, error, ts_done FROM partitions "
                     "WHERE exchange='bybit' AND stream='orderbook' AND symbol='BTCUSDT' "
                     "AND date IN ('2026-07-01','2026-08-02','2026-09-05')"):
    print(r)
