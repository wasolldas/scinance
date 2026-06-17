#!/usr/bin/env python3
"""
C-17/C-41 Lead-Lag-TRADABILITY-Gate (Welle-2-Folge-WP, H-04b): testet maschinell,
ob die in H-04 (GL-006) messbar bestaetigte gerichtete Lead-Lag-Information
BTC->ETH nach realistischem Latenz-Haircut + der verbindlichen 11-bps-Friction-
Wand eine handelbare Netto-Kante traegt — gegen das vorregistrierte H-04b-Gate
(scinance2-impl/state/hypothesis_registry.md, DEC-13).

NON-KAPITALFREI (``capital_free=false``, erste nicht-kapitalfreie Hypothese):
das Gate konfrontiert Edge-bps / Friction / Latenz. Es bleibt ein HISTORISCHER
BACKTEST MIT KOSTENMODELL auf dem read-only ``trades``-Bestand — KEIN Live-
Order-Code, KEIN Geldeinsatz (CLAUDE.md §4 / Autonomie-Protokoll §3).

Read-only Driver (DEC-03/DEC-10): laedt Tick-Timestamps+Preise beider Symbole
aus der DuckDB-``trades``-Tabelle (``--db`` + ``--pair``) ODER aus CSV/Parquet
(``--file-a``/``--file-b``), wiederverwendet den bestand H-04-Splitter (halb-
offene, deterministisch-chronologische Fenster), und faehrt je Fenster je
Survivor-Lag (1/2/3 s) die Trading-Regel -> Latenz-Haircut -> Friction-Wand ->
Bootstrap (Netto-Edge statistisch > 0?), BH-FDR alpha=0.10 ueber F-LEADLAG-TRADE.

ANTI-GAMING (registry H-04b Z.132): Defaults sind Wand=11 bps, Latenz=300 ms.
CLI darf sie fuer Sensitivitaet ueberschreiben, ABER der Output setzt dann
``gate_valid_assumptions=false`` — ein WEITER ist NUR am 300ms/11bps-Punkt mit
angewandtem Haircut gueltig.

Das GATE-URTEIL faellt der gate-auditor; dieser Lauf liefert jedes Kriterium
einzeln je Fenster/Lag.

Aufruf::

    python scripts/c17_c41_tradability.py --db data/duckdb/bybit.db --pair BTCUSDT,ETHUSDT --windows 2

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
        description="C-17/C-41 Lead-Lag-TRADABILITY / H-04b gate on a symbol pair "
                    "(read-only historical backtest with cost model, capital_free=false).",
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--db", type=Path, help="DuckDB-Datei mit trades-Tabelle (read-only)")
    src.add_argument("--file-a", type=Path, help="CSV/Parquet mit ts+price fuer Symbol A (mit --file-b)")
    p.add_argument("--file-b", type=Path, help="CSV/Parquet mit ts+price fuer Symbol B")
    p.add_argument(
        "--pair", type=_parse_pair, default=("BTCUSDT", "ETHUSDT"),
        help="Symbol-Paar A,B (Lead,Lag) fuer den DuckDB-Pfad (Default BTCUSDT,ETHUSDT)",
    )
    p.add_argument(
        "--db-copy", action="store_true",
        help="DuckDB vor dem Lesen in ein Temp-Verzeichnis kopieren (umgeht den "
             "RW-Lock des laufenden 1.0-Collectors; Kopie wird danach geloescht).",
    )
    p.add_argument("--windows", type=int, default=2, help="Anzahl disjunkter Fenster (>= 2, H-04b)")
    p.add_argument("--lags", type=_parse_lags, default=None,
                   help="Lag-Universum in Bars (Default Survivor 1,2,3 — H-04-Survivor, horizon=lag)")
    p.add_argument("--latency-ms", type=float, default=None,
                   help="Latenz-Haircut in ms (Default 300; < 300 -> gate_valid_assumptions=false)")
    p.add_argument("--friction-bps", type=float, default=None,
                   help="Friction-Wand Round-Trip Taker in bps (Default 11; < 11 -> gate_valid_assumptions=false)")
    p.add_argument("--slippage-bps", type=float, default=None,
                   help="Round-Trip-Slippage in bps (Default 4; verdict.md ~15 bps all-in - 11 bps Taker)")
    p.add_argument("--maker-secondary", action="store_true",
                   help="Maker-Sekundaerfall (adverse-selection-vorbehaltlich, NIE Primaer-Pass; "
                        "setzt gate_valid_assumptions=false).")
    p.add_argument("--bootstrap", type=int, default=200, help="Bootstrap-N (Default 200, >= 200 Pflicht)")
    p.add_argument("--seed", type=int, default=42, help="RNG-Seed (Pflicht-Default 42, reproduzierbar)")
    p.add_argument(
        "--signal-eps", type=float, default=0.0,
        help="Mindest-|BTC-Signal-Return| fuer einen Trade (Default 0.0 = jedes "
             "nicht-flache Signal handelt, registry-woertlich). Ein positiver "
             "Schwellwert ist konservativ (weniger Trades) und veraendert die "
             "Gate-Schwellen NICHT.",
    )
    p.add_argument("--grid-ms", type=float, default=None, help="Resample-Raster in ms (Default 1000)")
    p.add_argument(
        "--max-ticks-per-window", type=int, default=None,
        help="Deterministische Tick-Obergrenze je Fenster je Symbol (DEC-10, Default 150000). "
             "Reines Daten-Scoping — die H-04b-Gate-Schwellen bleiben UNVERAENDERT.",
    )
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output-Verzeichnis (Default: {DEFAULT_OUT})")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        import numpy  # noqa: F401
        import scipy  # noqa: F401  (available; not strictly needed here)
    except Exception as exc:  # pragma: no cover - dependency guard
        print(f"C17-C41-TRADE DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    try:
        from bybit_edge.research.c17_c41_tradability.costs import (
            FRICTION_WALL_BPS,
            LATENCY_MS,
            SLIPPAGE_BPS,
        )
        from bybit_edge.research.c17_c41_tradability.driver import (
            DEFAULT_GRID_MS,
            WINDOW_MAX_TICKS,
            DataError,
            load_pair_duckdb,
            load_trades_file,
            run,
            write_outputs,
        )
        from bybit_edge.research.c17_c41_tradability.trading_rule import SURVIVOR_LAGS
    except Exception as exc:  # pragma: no cover - import guard
        print(f"C17-C41-TRADE DEPENDENCY fehlt: {exc}", file=sys.stderr)
        return 2

    lags = args.lags if args.lags is not None else SURVIVOR_LAGS
    grid_ms = args.grid_ms if args.grid_ms is not None else DEFAULT_GRID_MS
    latency_ms = args.latency_ms if args.latency_ms is not None else LATENCY_MS
    friction_bps = args.friction_bps if args.friction_bps is not None else FRICTION_WALL_BPS
    slippage_bps = args.slippage_bps if args.slippage_bps is not None else SLIPPAGE_BPS
    max_ticks = args.max_ticks_per_window if args.max_ticks_per_window is not None else WINDOW_MAX_TICKS

    try:
        if args.db is not None:
            sym_a, sym_b = args.pair
            (a, b) = load_pair_duckdb(args.db, sym_a, sym_b, db_copy=args.db_copy)
            source = f"{args.db}::trades"
        else:
            if args.file_b is None:
                print("C17-C41-TRADE DATENDEFEKT: --file-a benoetigt --file-b", file=sys.stderr)
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
            grid_ms=grid_ms,
            latency_ms=latency_ms,
            friction_bps=friction_bps,
            slippage_bps=slippage_bps,
            maker_secondary=args.maker_secondary,
            n_bootstrap=args.bootstrap,
            seed=args.seed,
            max_ticks_per_window=max_ticks,
            signal_eps=args.signal_eps,
            source=source,
        )
        json_path, md_path = write_outputs(payload, args.out)
    except DataError as exc:
        print(f"C17-C41-TRADE DATENDEFEKT: {exc}", file=sys.stderr)
        return 1

    passes = sum(1 for x in payload["per_window_pass"] if x)
    print(
        f"C17-C41-TRADE H-04b | pair={payload['symbol_a']}/{payload['symbol_b']} "
        f"windows={payload['n_windows']} ({passes}/{payload['n_windows']} Fenster Netto-Edge-Survivor) "
        f"weiter_indication={payload['weiter_indication']} "
        f"gate_valid_assumptions={payload['gate_valid_assumptions']} "
        f"capital_free={payload['capital_free']} "
        f"wall={payload['wall_bps_total']:g}bps latency={payload['latency_ms']:g}ms "
        f"maker={payload['maker_secondary']} bootstrap={payload['n_bootstrap']} seed={payload['seed']} "
        f"-> {json_path}, {md_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
