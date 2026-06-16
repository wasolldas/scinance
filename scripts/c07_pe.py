#!/usr/bin/env python3
"""
C-07 Permutation-Entropy-Mess-Gate (Welle-2-WP): misst maschinell das
ZWEISTUFIGE H-06-Gate auf dem Bestands-``kline_1min``-Stream
(scinance2-impl/state/hypothesis_registry.md).

KAPITALFREI: reiner Detektions-/Info-Mess-Test. KEINE bps/Edge/PnL/Sharpe/
Friction-Metrik. Bandt-Pompe Permutation Entropy auf log-Returns, m = 4 / tau = 1
VORAB FIXIERT (KEIN CLI-Flag — read-only Konstanten PE_M/PE_TAU; jede Abweichung
waere eine NEUE H-06-Zeile, verdict.md §1f, DEC-12).

Read-only Driver (DEC-03/DEC-12): laedt (ts, close) je Symbol wahlweise aus der
DuckDB-``kline_1min``-Tabelle (``--db`` + ``--symbols``) ODER aus einer
CSV/Parquet-Datei (``--file``), zerlegt je Symbol in >= 2 disjunkte
chronologische Fenster (WINDOW_MAX_BARS-Cap, Stationaritaet) und faehrt je
Fenster:
  * PRE-Gate: rho(PE-Drop, 15-min-Vol-Cluster) — rho >= 0.30 Floor.
  * Haupt-Gate je delta in {1,5,15,60}min: MI(PE, target_{t+delta}) gegen
    Block-Shift-Surrogate, BH-FDR alpha=0.10 ueber F-ENTROPY, AUC-Lift in G1.
Meldet je Fenster/delta/Symbol: rho (PRE-Gate), surrogate_p, fdr_sig, auc_lift,
n_g1 — EINZELN, KEIN Gesamturteil.

Das GATE-URTEIL (WEITER/DROP) faellt der gate-auditor; PRE-Gate rho < 0.30 in
EINEM Fenster -> DROP (hartes Ein-Fenster-Kriterium, PRD §8.5).

Aufruf::

    python scripts/c07_pe.py --db data/duckdb/bybit.db --windows 2 --db-copy
    python scripts/c07_pe.py --db data/duckdb/bybit.db --symbols BTCUSDT,ETHUSDT
    python scripts/c07_pe.py --file klines.csv --windows 2

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
        raise argparse.ArgumentTypeError(
            f"invalid --lags '{s}' (positive ints in minutes, comma-separated)"
        )
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
        description="C-07 Permutation-Entropy / H-06 mess-gate (read-only, KAPITALFREI)."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--db", type=Path, help="DuckDB-Datei mit kline_1min-Tabelle (read-only)")
    src.add_argument("--file", type=Path, help="CSV/Parquet mit ts+close (Einzel-Symbol)")
    p.add_argument(
        "--symbols", type=_parse_symbols, default=None,
        help="Symbol-Universum (Komma-getrennt, Default BTC/ETH/SOL/BNB/XRP USDT)",
    )
    p.add_argument(
        "--db-copy", action="store_true",
        help="DuckDB vor dem Lesen in ein Temp-Verzeichnis kopieren (umgeht den "
             "RW-Lock des laufenden 1.0-Collectors; Kopie wird danach geloescht).",
    )
    p.add_argument("--windows", type=int, default=2, help="Anzahl disjunkter Fenster (>= 2, H-06)")
    p.add_argument("--surrogates", type=int, default=200, help="Surrogate-N (Default 200, >=200 empfohlen)")
    p.add_argument(
        "--lags", type=_parse_lags, default=None,
        help="delta-Lag-Universum in MINUTEN (Default 1,5,15,60)",
    )
    p.add_argument("--seed", type=int, default=42, help="RNG-Seed (Pflicht-Default 42, reproduzierbar)")
    p.add_argument(
        "--pe-window", type=int, default=None,
        help="Rolling-PE-Fenster in Bars (Default 240 = 4h). m/tau sind NICHT setzbar.",
    )
    p.add_argument("--n-bins", type=int, default=None, help="MI-Quantil-Bins (Default 4)")
    p.add_argument(
        "--max-bars-per-window", type=int, default=None,
        help="Deterministische Bar-Obergrenze je Fenster je Symbol (DEC-12, Default 43200 "
             "= 30 Tage). Stationaritaets-Scoping — die H-06-Gate-Schwellen bleiben UNVERAENDERT.",
    )
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output-Verzeichnis (Default: {DEFAULT_OUT})")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        import numpy  # noqa: F401
    except Exception as exc:  # pragma: no cover - dependency guard
        print(f"C07 DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    try:
        from bybit_edge.research.c07_pe.driver import (
            DEFAULT_LAGS_MIN,
            DEFAULT_SYMBOLS,
            WINDOW_MAX_BARS,
            DataError,
            load_kline_file,
            load_symbols_duckdb,
            run,
            write_outputs,
        )
        from bybit_edge.research.c07_pe.info_test import DEFAULT_N_BINS
        from bybit_edge.research.c07_pe.perm_entropy import DEFAULT_PE_WINDOW
    except Exception as exc:  # pragma: no cover - import guard
        print(f"C07 DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    lags_min = args.lags if args.lags is not None else DEFAULT_LAGS_MIN
    pe_window = args.pe_window if args.pe_window is not None else DEFAULT_PE_WINDOW
    n_bins = args.n_bins if args.n_bins is not None else DEFAULT_N_BINS
    max_bars = args.max_bars_per_window if args.max_bars_per_window is not None else WINDOW_MAX_BARS
    symbols = args.symbols if args.symbols is not None else DEFAULT_SYMBOLS

    try:
        if args.db is not None:
            symbol_arrays = load_symbols_duckdb(args.db, symbols, db_copy=args.db_copy)
            source = f"{args.db}::kline_1min"
        else:
            symbol_arrays = load_kline_file(args.file)
            source = str(args.file)

        payload = run(
            symbol_arrays,
            n_windows=args.windows,
            lags_min=lags_min,
            pe_window=pe_window,
            n_bins=n_bins,
            n_surrogates=args.surrogates,
            seed=args.seed,
            max_bars_per_window=max_bars,
            source=source,
        )
        json_path, md_path = write_outputs(payload, args.out)
    except DataError as exc:
        print(f"C07 DATENDEFEKT: {exc}", file=sys.stderr)
        return 1

    print(
        f"C07 H-06 | symbols={','.join(payload['symbols'])} "
        f"windows={payload['n_windows']} m={payload['pe_m']}/tau={payload['pe_tau']} "
        f"pre_rhos={[round(x, 3) for x in payload['pre_gate_rhos']]} "
        f"all_pre_pass={payload['all_windows_pre_gate_pass']} "
        f"fdr_sig={payload['n_fdr_significant']} surrogates={payload['n_surrogates']} "
        f"seed={payload['seed']} "
        f"(KAPITALFREI, kein Gesamturteil — gate-auditor) -> {json_path}, {md_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
