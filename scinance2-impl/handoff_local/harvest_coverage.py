#!/usr/bin/env python3
"""Harvester-Coverage-Report (read-only).

Liest das Harvester-Manifest (ueber die Junction `data/harvest/`) und gibt
zwei Tabellen aus:
  1. Coverage-Matrix: first/last DONE-Tag + done_days je exchange/stream/symbol.
  2. ETHUSDT publicTrade je-Tag-Status (DONE/EMPTY/FAILED) - fuer die
     H-05b-OOS-Fenster-Vorregistrierung.

Aufruf (vom Repo-Root, mit venv-Python):
    python scinance2-impl/handoff_local/harvest_coverage.py
    python scinance2-impl/handoff_local/harvest_coverage.py --symbol ETHUSDT

Kein Schreibzugriff. Beruehrt nur die SQLite-Index-DB (read-only geoeffnet).
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

DEFAULT_MANIFEST = Path("data/harvest/state/harvest_manifest.sqlite")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Harvester coverage report (read-only).")
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST),
                   help=f"Pfad zur harvest_manifest.sqlite (Default {DEFAULT_MANIFEST}).")
    p.add_argument("--symbol", default="ETHUSDT",
                   help="Symbol fuer die Je-Tag-Detailtabelle (Default ETHUSDT).")
    p.add_argument("--stream", default="publicTrade",
                   help="Stream fuer die Je-Tag-Detailtabelle (Default publicTrade).")
    p.add_argument("--exchange", default="bybit",
                   help="Exchange fuer die Je-Tag-Detailtabelle (Default bybit).")
    args = p.parse_args(argv)

    mpath = Path(args.manifest)
    # DEC-50: die aktuelle Wahrheit ist harvest_manifest.backup.sqlite
    # (Offload-Export mit Registrar-Zeilen); die alte harvest_manifest.sqlite
    # ist die eingefrorene Windows-Aera OHNE Registrar-Zeilen.
    if args.manifest == str(DEFAULT_MANIFEST):
        backup = mpath.with_name("harvest_manifest.backup.sqlite")
        if backup.exists():
            mpath = backup
            print(f"HINWEIS: nutze aktuelles Manifest {mpath}")
    if not mpath.exists():
        print(f"FEHLER: Manifest nicht gefunden: {mpath}", file=sys.stderr)
        print("Junction angelegt? -> data\\harvest sollte auf den Harvester-data-Ordner zeigen.",
              file=sys.stderr)
        return 1

    # read-only oeffnen (URI-Modus)
    con = sqlite3.connect(f"file:{mpath.as_posix()}?mode=ro", uri=True)
    try:
        print("=" * 78)
        print("COVERAGE-MATRIX (first/last DONE je exchange/stream/symbol)")
        print("=" * 78)
        rows = con.execute(
            "SELECT exchange, stream, symbol, "
            "SUM(CASE WHEN status='DONE' THEN 1 ELSE 0 END) AS done_days, "
            "MIN(CASE WHEN status='DONE' THEN date END) AS first_done, "
            "MAX(CASE WHEN status='DONE' THEN date END) AS last_done "
            "FROM partitions GROUP BY exchange, stream, symbol "
            "HAVING done_days > 0 ORDER BY exchange, stream, symbol"
        ).fetchall()
        hdr = f"{'exchange':<10} {'stream':<22} {'symbol':<16} {'days':>5} {'first':>12} {'last':>12}"
        print(hdr)
        print("-" * len(hdr))
        for ex, st, sym, days, first, last in rows:
            # Luecken-Heuristik: done_days vs. Kalenderspanne
            print(f"{ex:<10} {st:<22} {sym:<16} {days:>5} {str(first):>12} {str(last):>12}")

        print()
        print("=" * 78)
        print(f"JE-TAG-STATUS: {args.exchange} / {args.stream} / {args.symbol}")
        print("=" * 78)
        det = con.execute(
            "SELECT date, status FROM partitions "
            "WHERE exchange=? AND stream=? AND symbol=? ORDER BY date",
            [args.exchange, args.stream, args.symbol],
        ).fetchall()
        if not det:
            print("(keine Manifest-Eintraege - evtl. Live-only, nicht im Manifest)")
        else:
            non_done = [(d, s) for d, s in det if s != "DONE"]
            print(f"Eintraege gesamt: {len(det)}  |  DONE: {sum(1 for _, s in det if s == 'DONE')}  "
                  f"|  nicht-DONE: {len(non_done)}")
            print(f"Spanne: {det[0][0]} .. {det[-1][0]}")
            if non_done:
                print("\nNICHT-DONE Tage (wichtig fuer Fenster-Wahl):")
                for d, s in non_done:
                    print(f"  {d}  {s}")
            else:
                print("Alle Manifest-Tage DONE (keine EMPTY/FAILED).")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
