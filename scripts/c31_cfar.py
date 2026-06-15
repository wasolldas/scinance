#!/usr/bin/env python3
"""
C-31 CFAR-Auswertung (WP-3): wertet die zyklostationaere Struktur der
publicTrade-Inter-Arrivals maschinell gegen das vorregistrierte H-03-Gate aus
(scinance2-impl/state/hypothesis_registry.md).

Read-only Driver (DEC-03): laedt Tick-Timestamps+Preise wahlweise aus der
DuckDB-``trades``-Tabelle (``--db`` + ``--symbol``) ODER aus einer CSV/Parquet-
Datei (``--file``; Fixtures + exportierte Replay-Daten), zerlegt in >= 2
disjunkte chronologische Fenster, faehrt bin -> SCD -> CA-CFAR -> Surrogate ->
Lead/Edge je Fenster ueber die F-CFAR-Parameterfamilie (BH-FDR alpha=0.10) und
schreibt ``c31_cfar_results.json`` + Markdown-Report.

Das GATE-URTEIL faellt der gate-auditor; dieser Lauf liefert jedes Kriterium
einzeln je Fenster.

Aufruf::

    python scripts/c31_cfar.py --file tests/unit/fixtures/c31/cyclic.csv --windows 2
    python scripts/c31_cfar.py --db data/duckdb/bybit.db --symbol BTCUSDT --windows 2

Exit-Codes: 0 = ausgewertet (unabhaengig vom Urteil), 1 = Datendefekt/fehlende
Eingabe.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from bybit_edge.research.c31_cfar.cyclic_spectrum import WINDOW_MAX_TICKS
from bybit_edge.research.c31_cfar.driver import (
    DataError,
    default_family,
    load_trades_duckdb,
    load_trades_file,
    run,
    write_outputs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "scinance2-impl" / "state"


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="C-31 CFAR / H-03 gate evaluation on publicTrade inter-arrivals (read-only)."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", type=Path, help="CSV/Parquet mit ts+price (Fixtures/Replay-Export)")
    src.add_argument("--db", type=Path, help="DuckDB-Datei mit trades-Tabelle (read-only)")
    p.add_argument("--symbol", type=str, default="BTCUSDT", help="Symbol fuer den DuckDB-Pfad")
    p.add_argument(
        "--db-copy", action="store_true",
        help="DuckDB vor dem Lesen in ein Temp-Verzeichnis kopieren (umgeht den "
             "RW-Lock des laufenden 1.0-Collectors; Kopie wird danach geloescht).",
    )
    p.add_argument("--windows", type=int, default=2, help="Anzahl disjunkter Fenster (>= 2, H-03)")
    p.add_argument(
        "--max-ticks-per-window", type=int, default=WINDOW_MAX_TICKS,
        help=(
            "Deterministische Tick-Obergrenze je Fenster (DEC-09, Default "
            f"{WINDOW_MAX_TICKS}). Es werden die JUENGSTEN windows x max-ticks "
            "Ticks genommen und in disjunkte Fenster geteilt. Reines Daten-"
            "Scoping (Stationaritaet + Rechenbarkeit) — die H-03-Gate-Schwellen "
            "(p/Lead/Edge/Surrogates/FDR) bleiben UNVERAENDERT."
        ),
    )
    p.add_argument("--surrogates", type=int, default=200, help="Surrogate-N (Default 200)")
    p.add_argument("--seed", type=int, default=42, help="RNG-Seed (Pflicht-Default 42, reproduzierbar)")
    p.add_argument("--segment-len", type=int, default=256, help="FFT-Segmentlaenge")
    p.add_argument("--n-alpha", type=int, default=64, help="Anzahl zyklischer Frequenzen alpha")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output-Verzeichnis (Default: {DEFAULT_OUT})")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        if args.file is not None:
            ts, px = load_trades_file(args.file)
            source = str(args.file)
            symbol = ""
        else:
            ts, px = load_trades_duckdb(args.db, args.symbol, db_copy=args.db_copy)
            source = f"{args.db}::trades"
            symbol = args.symbol

        payload = run(
            ts, px,
            n_windows=args.windows,
            family=default_family(),
            n_surrogates=args.surrogates,
            seed=args.seed,
            segment_len=args.segment_len,
            n_alpha=args.n_alpha,
            max_ticks_per_window=args.max_ticks_per_window,
            source=source,
            symbol=symbol,
        )
        json_path, md_path = write_outputs(payload, args.out)
    except DataError as exc:
        print(f"C31-CFAR DATENDEFEKT: {exc}", file=sys.stderr)
        return 1

    passes = sum(1 for x in payload["per_window_pass"] if x)
    print(
        f"C31-CFAR H-03 | windows={payload['n_windows']} "
        f"all_pass={payload['all_windows_pass']} ({passes}/{payload['n_windows']} Fenster) "
        f"surrogates={payload['n_surrogates']} seed={payload['seed']} "
        f"-> {json_path}, {md_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
