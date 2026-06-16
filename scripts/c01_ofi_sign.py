#!/usr/bin/env python3
"""
C-01 OFI-Vorzeichen-Mess-Gate (Welle-2-WP): misst maschinell das VORZEICHEN des
konditionalen Zusammenhangs sign(OFI_t) -> sign(forward_return_{t+delta}) auf dem
Bestands-``trades``-Stream gegen das vorregistrierte H-05-Gate
(scinance2-impl/state/hypothesis_registry.md, INC-02-Anker).

KAPITALFREI: prueft NUR die Mess-Existenz + Richtung des gerichteten OFI-Return-
Zusammenhangs gegen eine Permutations-Surrogate-Null. KEINE bps/Edge/PnL/Sharpe/
Friction-Metrik. Eigener OFI-Schaetzer (aggressor-signiertes Volumen je Bin) —
das Bestands-``m2_ofi.py`` (bekannte C-01/C-02-Vertauschung) bleibt unberuehrt
(DEC-11).

Read-only Driver (DEC-03/DEC-11): laedt (ts, price, volume, side) je Symbol
wahlweise aus der DuckDB-``trades``-Tabelle (``--db`` + ``--symbols``) ODER aus
einer CSV/Parquet-Datei (``--file``), zerlegt je Symbol in >= 2 disjunkte
chronologische Fenster und faehrt je Fenster je Symbol je delta in
{1,5,15,60,300}s den OFI-Vorzeichen-Test + Permutations-Surrogate ueber die
F-OFI-Familie (BH-FDR alpha=0.10 ueber alle delta x Symbole). Meldet je
Fenster/delta/Symbol: corr, sign_direction (+/-/0), |corr|, hit_rate,
surrogate_p, fdr_sig, inverse_significant — EINZELN, KEIN Gesamturteil.

Das GATE-URTEIL (WEITER/DROP/H-05b) faellt der gate-auditor; ein signifikant
INVERSES Vorzeichen ist KEIN H-05-Bestehen, sondern H-05b-Ausloeser.

Aufruf::

    python scripts/c01_ofi_sign.py --db data/duckdb/bybit.db --windows 2 --db-copy
    python scripts/c01_ofi_sign.py --db data/duckdb/bybit.db --symbols BTCUSDT,ETHUSDT
    python scripts/c01_ofi_sign.py --file trades.csv --windows 2

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
        raise argparse.ArgumentTypeError(f"invalid --lags '{s}' (positive ints in seconds, comma-separated)")
    return out


def _parse_symbols(s: str) -> tuple[str, ...]:
    out = tuple(p.strip() for p in s.split(",") if p.strip())
    if not out:
        raise argparse.ArgumentTypeError(f"--symbols is empty: '{s}'")
    return out


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "scinance2-impl" / "state"


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="C-01 OFI-Vorzeichen / H-05 mess-gate (read-only, KAPITALFREI)."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--db", type=Path, help="DuckDB-Datei mit trades-Tabelle (read-only)")
    src.add_argument("--file", type=Path, help="CSV/Parquet mit ts+price+volume+side (Einzel-Symbol)")
    p.add_argument(
        "--symbols", type=_parse_symbols, default=None,
        help="Symbol-Universum (Komma-getrennt, Default BTC/ETH/SOL/BNB/XRP USDT)",
    )
    p.add_argument(
        "--db-copy", action="store_true",
        help="DuckDB vor dem Lesen in ein Temp-Verzeichnis kopieren (umgeht den "
             "RW-Lock des laufenden 1.0-Collectors; Kopie wird danach geloescht).",
    )
    p.add_argument("--windows", type=int, default=2, help="Anzahl disjunkter Fenster (>= 2, H-05)")
    p.add_argument("--surrogates", type=int, default=200, help="Surrogate-N (Default 200, >=200 empfohlen)")
    p.add_argument(
        "--lags", type=_parse_lags, default=None,
        help="delta-Lag-Universum in SEKUNDEN (Default 1,5,15,60,300)",
    )
    p.add_argument("--seed", type=int, default=42, help="RNG-Seed (Pflicht-Default 42, reproduzierbar)")
    p.add_argument("--grid-ms", type=float, default=None, help="OFI-Bin-Breite in ms (Default 1000)")
    p.add_argument(
        "--max-ticks-per-window", type=int, default=None,
        help="Deterministische Trade-Obergrenze je Fenster je Symbol (DEC-11, Default 300000). "
             "Reines Daten-Scoping — die H-05-Gate-Schwellen bleiben UNVERAENDERT.",
    )
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output-Verzeichnis (Default: {DEFAULT_OUT})")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        import numpy  # noqa: F401
    except Exception as exc:  # pragma: no cover - dependency guard
        print(f"C01 DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    try:
        from bybit_edge.research.c01_ofi_sign.driver import (
            DEFAULT_GRID_MS,
            DEFAULT_LAGS_S,
            DEFAULT_SYMBOLS,
            WINDOW_MAX_TICKS,
            DataError,
            load_symbols_duckdb,
            load_trades_file,
            run,
            write_outputs,
        )
    except Exception as exc:  # pragma: no cover - import guard
        print(f"C01 DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    lags_s = args.lags if args.lags is not None else DEFAULT_LAGS_S
    grid_ms = args.grid_ms if args.grid_ms is not None else DEFAULT_GRID_MS
    max_ticks = args.max_ticks_per_window if args.max_ticks_per_window is not None else WINDOW_MAX_TICKS
    symbols = args.symbols if args.symbols is not None else DEFAULT_SYMBOLS

    try:
        if args.db is not None:
            symbol_arrays = load_symbols_duckdb(args.db, symbols, db_copy=args.db_copy)
            source = f"{args.db}::trades"
        else:
            symbol_arrays = load_trades_file(args.file)
            source = str(args.file)

        payload = run(
            symbol_arrays,
            n_windows=args.windows,
            lags_s=lags_s,
            grid_ms=grid_ms,
            n_surrogates=args.surrogates,
            seed=args.seed,
            max_ticks_per_window=max_ticks,
            source=source,
        )
        json_path, md_path = write_outputs(payload, args.out)
    except DataError as exc:
        print(f"C01 DATENDEFEKT: {exc}", file=sys.stderr)
        return 1

    print(
        f"C01 H-05 | symbols={','.join(payload['symbols'])} "
        f"windows={payload['n_windows']} fdr_sig={payload['n_fdr_significant']} "
        f"any_inverse_sig={payload['any_inverse_significant']} "
        f"any_nonpos_sign={payload['any_nonpositive_sign_window']} "
        f"surrogates={payload['n_surrogates']} seed={payload['seed']} "
        f"(KAPITALFREI, kein Gesamturteil — gate-auditor) -> {json_path}, {md_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
