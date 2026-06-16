#!/usr/bin/env python3
"""
C-17/C-41 Lead-Lag-Mess-Gate (Welle-2-WP): wertet gerichteten Informationsfluss
BTC->Alt zwischen einem Symbol-PAAR maschinell gegen das vorregistrierte
H-04-Gate aus (scinance2-impl/state/hypothesis_registry.md).

KAPITALFREI: prueft NUR die Mess-Existenz von gerichteter Information
(Transfer-Entropy C-17 + Wavelet-Coherence-Phasen-Lead C-41) gegen eine
zirkulaere Block-Shift-Surrogate-Null. KEINE bps/Edge/PnL/Friction-Metrik.

Read-only Driver (DEC-03/DEC-10): laedt Tick-Timestamps+Preise beider Symbole
wahlweise aus der DuckDB-``trades``-Tabelle (``--db`` + ``--pair``) ODER aus
CSV/Parquet-Dateien (``--file-a``/``--file-b``), resampelt beide auf ein
gemeinsames Bar-Raster, zerlegt in >= 2 disjunkte chronologische Fenster und
faehrt je Fenster TE (beide Richtungen je Lag) + Wavelet-Coherence + Surrogate
ueber die F-LEADLAG-Familie (BH-FDR alpha=0.10), bestimmt das Lead-Symbol und
prueft dessen Stabilitaet ueber die Fenster.

Das GATE-URTEIL faellt der gate-auditor; dieser Lauf liefert jedes Kriterium
einzeln je Fenster.

Aufruf::

    python scripts/c17_c41_lead_lag.py --db data/duckdb/bybit.db --pair BTCUSDT,ETHUSDT --windows 2
    python scripts/c17_c41_lead_lag.py --file-a a.csv --file-b b.csv --windows 2

Exit-Codes: 0 = ausgewertet (unabhaengig vom Urteil), 1 = Datendefekt/fehlende
Eingabe, 2 = fehlende Dependency.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


def _parse_lags(s: str) -> tuple[int, ...]:
    out = tuple(int(x) for x in s.replace(" ", "").split(",") if x)
    if not out or any(v < 1 for v in out):
        raise argparse.ArgumentTypeError(f"invalid --lags '{s}' (positive ints, comma-separated)")
    return out


def _parse_pair(s: str) -> tuple[str, str]:
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"--pair needs exactly two symbols, got '{s}'")
    return parts[0], parts[1]


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "scinance2-impl" / "state"


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="C-17/C-41 Lead-Lag / H-04 mess-gate on a symbol pair (read-only, KAPITALFREI)."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--db", type=Path, help="DuckDB-Datei mit trades-Tabelle (read-only)")
    src.add_argument("--file-a", type=Path, help="CSV/Parquet mit ts+price fuer Symbol A (mit --file-b)")
    p.add_argument("--file-b", type=Path, help="CSV/Parquet mit ts+price fuer Symbol B")
    p.add_argument(
        "--pair", type=_parse_pair, default=("BTCUSDT", "ETHUSDT"),
        help="Symbol-Paar A,B fuer den DuckDB-Pfad (Default BTCUSDT,ETHUSDT)",
    )
    p.add_argument(
        "--db-copy", action="store_true",
        help="DuckDB vor dem Lesen in ein Temp-Verzeichnis kopieren (umgeht den "
             "RW-Lock des laufenden 1.0-Collectors; Kopie wird danach geloescht).",
    )
    p.add_argument("--windows", type=int, default=2, help="Anzahl disjunkter Fenster (>= 2, H-04)")
    p.add_argument("--surrogates", type=int, default=200, help="Surrogate-N (Default 200)")
    p.add_argument("--lags", type=_parse_lags, default=None, help="Lag-Universum in Bars (Default 1,2,3,5,10)")
    p.add_argument("--seed", type=int, default=42, help="RNG-Seed (Pflicht-Default 42, reproduzierbar)")
    p.add_argument("--grid-ms", type=float, default=None, help="Resample-Raster in ms (Default 1000)")
    p.add_argument("--n-bins", type=int, default=None, help="Quantil-Bins fuer TE-Diskretisierung (Default 3)")
    p.add_argument(
        "--max-ticks-per-window", type=int, default=None,
        help="Deterministische Tick-Obergrenze je Fenster je Symbol (DEC-10, Default 150000). "
             "Reines Daten-Scoping — die H-04-Gate-Schwellen bleiben UNVERAENDERT.",
    )
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output-Verzeichnis (Default: {DEFAULT_OUT})")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        import numpy  # noqa: F401
        import scipy  # noqa: F401  (available; wavelet axis uses numpy FFT only)
    except Exception as exc:  # pragma: no cover - dependency guard
        print(f"C17-C41 DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    try:
        from bybit_edge.research.c17_c41_lead_lag.driver import (
            DataError,
            DEFAULT_GRID_MS,
            DEFAULT_LAGS,
            DEFAULT_N_BINS,
            WINDOW_MAX_TICKS,
            load_pair_duckdb,
            load_trades_file,
            run,
            write_outputs,
        )
    except Exception as exc:  # pragma: no cover - import guard
        print(f"C17-C41 DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    lags = args.lags if args.lags is not None else DEFAULT_LAGS
    grid_ms = args.grid_ms if args.grid_ms is not None else DEFAULT_GRID_MS
    n_bins = args.n_bins if args.n_bins is not None else DEFAULT_N_BINS
    max_ticks = args.max_ticks_per_window if args.max_ticks_per_window is not None else WINDOW_MAX_TICKS

    try:
        if args.db is not None:
            sym_a, sym_b = args.pair
            (a, b) = load_pair_duckdb(args.db, sym_a, sym_b, db_copy=args.db_copy)
            source = f"{args.db}::trades"
        else:
            if args.file_b is None:
                print("C17-C41 DATENDEFEKT: --file-a benoetigt --file-b", file=sys.stderr)
                return 1
            a = load_trades_file(args.file_a)
            b = load_trades_file(args.file_b)
            sym_a, sym_b = args.pair
            source = f"{args.file_a} / {args.file_b}"

        payload = run(
            a, b,
            symbol_a=sym_a, symbol_b=sym_b,
            n_windows=args.windows,
            lags=lags,
            n_bins=n_bins,
            grid_ms=grid_ms,
            n_surrogates=args.surrogates,
            seed=args.seed,
            max_ticks_per_window=max_ticks,
            source=source,
        )
        json_path, md_path = write_outputs(payload, args.out)
    except DataError as exc:
        print(f"C17-C41 DATENDEFEKT: {exc}", file=sys.stderr)
        return 1

    passes = sum(1 for x in payload["per_window_existence"] if x)
    print(
        f"C17-C41 H-04 | pair={payload['symbol_a']}/{payload['symbol_b']} "
        f"windows={payload['n_windows']} all_pass={payload['all_windows_pass']} "
        f"({passes}/{payload['n_windows']} Fenster Existenz, lead_stable="
        f"{payload['lead_symbol_stable']}, leads={payload['lead_symbols']}) "
        f"surrogates={payload['n_surrogates']} seed={payload['seed']} "
        f"-> {json_path}, {md_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
