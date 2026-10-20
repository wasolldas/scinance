#!/usr/bin/env python3
"""DEC-100: baut den ``panel_1d_delisted``-Baum aus dem Data-Harvest-Register und den Data-Harvest-Backfill-Partitionen
(``rest.kline1d``, ``rest.fundingRateAll``).  Reiner Dateibau: liest ein LOKALES Verzeichnis (der Orchestrator laedt die
Partitionen per Harvest-Client in die Sitzung), kein Netz, keine Zugangsdaten, nie unter ``data/harvest``.

  python scripts/h32_build_delisted_tree.py --register scinance3-impl/state/data_harvest_delisting_register_2026-10-20.csv
        --partitions-dir DIR --out data/panel_1d_delisted_v2 --cut 2026-09-28 [--start-year 2021] [--listing-anchor register|observed]

Eingabe-Layout (``--partitions-dir``): unterhalb von DIR liegen Parquet-Dateien in Verzeichnissen ``rest.kline1d`` bzw.
``rest.fundingRateAll`` (z. B. ``bybit/rest.kline1d/symbol=ALL/date=2024-06-01/*.parquet``); Spalten ``symbol`` und
``payload_json`` (kline: ``[startTime, open, high, low, close, volume, turnover]``; funding: ``{symbol, fundingRate,
fundingRateTimestamp}``).

Symbolliste: Register-Zeilen mit ``category=linear``, ``quoteCoin=USDT`` und ``last_trading_day <= --cut``.  Ausgabe unter
``--out`` (muss leer sein oder fehlen): ``frozen/source=bybit/category=linear/symbol=S/year=Y/part.parquet`` +
``panel_manifest.sqlite`` (Layout und Manifest wie ``wp7_universe.panel_store``), ``delisting_dates.json`` (delist_date =
last_trading_day, source = data_harvest_register), ``delisting_register.csv`` (Kopie, sha256 = ``data_fingerprints.
delisting_register_sha256``) und ``delisted_tree_fingerprint.json`` (sha256 ueber Register-CSV und alle Parquets).  Der neue
Baum ersetzt den alten als ``--delisted-base`` der Modi von ``scripts/h32_fm8.py``.

Nichts wird gefuellt oder interpoliert: Symbole ohne API-Daten (NO_HISTORY), Symbole ohne Funding, fehlende Tage (PARTIAL,
Union-Lader braucht dann --allow-partial) und Jahre ohne Zeilen (FAILED, GAP_NO_ROWS) werden im Fingerprint-Bericht benannt.
rc 0 = sauber, 3 = gebaut mit benannten Luecken, 1 = Abbruch.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bybit_edge.research.h32_fm8 import delisted_tree  # noqa: E402
from bybit_edge.research.h32_fm8.errors import H32Abort  # noqa: E402
from bybit_edge.research.wp12_delisting import delisted_panel  # noqa: E402


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="DEC-100: panel_1d_delisted aus Data-Harvest-Register und Backfill-Partitionen")
    ap.add_argument("--register", required=True, help="Data-Harvest-Register (CSV)")
    ap.add_argument("--partitions-dir", required=True, help="lokales Verzeichnis mit den Partitionen rest.kline1d / rest.fundingRateAll")
    ap.add_argument("--out", required=True, help="Ausgabe-Baum (leer oder nicht vorhanden)")
    ap.add_argument("--cut", required=True, help="nur Register-Zeilen mit last_trading_day <= CUT (ISO-Datum)")
    ap.add_argument("--start-year", type=int, default=delisted_panel.DEFAULT_START_YEAR)
    ap.add_argument("--listing-anchor", choices=delisted_tree.LISTING_ANCHORS, default="register",
                    help="Beginn der erwarteten Tage: launch_day des Registers (streng, Standard) oder erste beobachtete Kerze")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    try:
        rep = delisted_tree.build_tree(a.register, a.partitions_dir, a.out, cut=a.cut, start_year=a.start_year,
                                       listing_anchor=a.listing_anchor, log=log)
    except (H32Abort, ValueError, OSError) as exc:
        log(f"FEHLER ({type(exc).__name__}): {exc}\nKEIN BAUM.")
        return 1
    st = rep["status_counts"]
    log(f"Symbole {rep['n_symbols']} (mit Historie {rep['n_symbols_with_history']}), Partitionen {rep['n_partitions']}, Status {st}")
    log(f"Register sha256 {rep['register']['sha256']}; Baum sha256 {rep['tree_sha256']}")
    gaps = False
    if rep["no_history_symbols"]:
        gaps = True
        log(f"NO_HISTORY ({len(rep['no_history_symbols'])}): {', '.join(rep['no_history_symbols'])}")
    if rep["not_done_partitions"]:
        gaps = True
        log(f"Partitionen nicht DONE ({len(rep['not_done_partitions'])}): "
            + "; ".join(f"{p['symbol']}/{p['year']}={p['status']} (fehlende Tage {p['missing_days']})" for p in rep["not_done_partitions"][:20]))
    if rep["funding_missing_symbols"]:
        gaps = True
        log(f"ohne Funding ({len(rep['funding_missing_symbols'])}): {', '.join(rep['funding_missing_symbols'])}")
    if rep["dropped_after_last_trading_day"]:
        log(f"Zeilen nach dem letzten Handelstag verworfen (Wiederlistung?): {sorted(rep['dropped_after_last_trading_day'])}")
    log(f"Baum geschrieben: {a.out}" + (" -- MIT BENANNTEN LUECKEN (rc 3)" if gaps else ""))
    return 3 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
