"""
REST-Backfill-CLI — historische Bybit-V5-Daten in DuckDB laden.

Backfillbare Datenarten:
    klines    — OHLCV-Klines via /v5/market/kline
    funding   — Funding-Rate-History via /v5/market/funding/history
    oi        — Open-Interest via /v5/market/open-interest
    ls        — Long/Short-Ratio via /v5/market/account-ratio

NICHT backfillbar (Bybit gibt's historisch nicht öffentlich):
    * L2-Orderbook-Tiefe
    * Tick-Trades (nur letzte ~1000)
    * Tickers-Snapshots (nur aktueller Wert)
    → Diese Datenarten müssen via Live-Collector mit ``PERSIST_ENABLED``
      bzw. ``PERSIST_ORDERBOOK`` gesammelt werden.

Beispiele
---------
Einzelnes Symbol, alle Sources, 6 Monate::

    python scripts/backfill.py --symbol BTCUSDT --months 6

Komplettes PRD-Universum, 6 Monate, 5-min-Klines::

    python scripts/backfill.py --universe --months 6 --kline-interval 5

Custom Symbol-Liste, nur Funding + OI, Force-Refresh::

    python scripts/backfill.py --symbols BTCUSDT,ETHUSDT,SOLUSDT \\
        --what funding --force
    python scripts/backfill.py --symbols BTCUSDT --what oi --oi-interval 1h
"""
from __future__ import annotations

import argparse
import sys
from typing import Callable

from bybit_edge.config import MULTI_SYMBOL_UNIVERSE
from bybit_edge.persistence.backfill import BackfillManager


def _resolve_symbols(args: argparse.Namespace) -> list[str]:
    if args.symbol:
        return [args.symbol.strip().upper()]
    if args.universe:
        return list(MULTI_SYMBOL_UNIVERSE)
    if args.symbols:
        return [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    raise SystemExit("Bitte --symbol, --symbols X,Y,Z oder --universe angeben.")


def _build_runner(args: argparse.Namespace, mgr: BackfillManager) -> Callable[[str], dict[str, int]]:
    skip = not args.force
    what = args.what

    def run(sym: str) -> dict[str, int]:
        if what == "all":
            return mgr.backfill_all(
                sym,
                months=args.months,
                kline_interval=args.kline_interval,
                oi_interval=args.oi_interval,
                ls_period=args.ls_period,
                skip_if_exists=skip,
            )
        if what == "klines":
            return {"klines": mgr.backfill_klines(
                sym, args.kline_interval, args.months, skip,
            )}
        if what == "funding":
            return {"funding": mgr.backfill_funding(sym, args.months, skip)}
        if what == "oi":
            return {"open_interest": mgr.backfill_open_interest(
                sym, args.oi_interval, args.months, skip,
            )}
        if what == "ls":
            return {"long_short_ratio": mgr.backfill_long_short_ratio(
                sym, args.ls_period, args.months, skip,
            )}
        raise SystemExit(f"Unbekanntes --what: {what}")

    return run


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bybit REST-Backfill (Klines + Funding + OI + L/S-Ratio)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--symbol", help="Einzelnes Symbol, z.B. BTCUSDT")
    group.add_argument("--symbols", help="Komma-Liste, z.B. BTCUSDT,ETHUSDT")
    group.add_argument(
        "--universe", action="store_true",
        help="Nutzt MULTI_SYMBOL_UNIVERSE aus config.py",
    )
    parser.add_argument("--months", type=int, default=6)
    parser.add_argument(
        "--kline-interval", default="5",
        help="Bybit-Kline-Intervall (1,3,5,15,30,60,120,240,360,720,D,W,M)",
    )
    parser.add_argument(
        "--oi-interval", default="5min",
        help="Open-Interest-Intervall (5min,15min,30min,1h,4h,1d)",
    )
    parser.add_argument(
        "--ls-period", default="5min",
        help="Long/Short-Ratio-Periode (5min,15min,30min,1h,4h,1d)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Deaktiviert skip_if_exists (lädt auch bestehende Daten neu)",
    )
    parser.add_argument(
        "--what", choices=("all", "klines", "funding", "oi", "ls"),
        default="all",
    )

    args = parser.parse_args()
    symbols = _resolve_symbols(args)

    mgr = BackfillManager()
    try:
        runner = _build_runner(args, mgr)

        print("=" * 72)
        print(f"  BACKFILL — {len(symbols)} Symbol(e) — {args.months} Monate "
              f"— what={args.what}")
        print(f"  skip_if_exists={not args.force}, kline_int={args.kline_interval}, "
              f"oi_int={args.oi_interval}, ls_period={args.ls_period}")
        print("=" * 72)

        totals: dict[str, int] = {}
        for sym in symbols:
            print(f"\n[ {sym} ]")
            counts = runner(sym)
            for src, n in counts.items():
                print(f"  {src:<20} {n:>10} Zeilen")
                totals[src] = totals.get(src, 0) + n

        print("\n" + "-" * 72)
        print("SUMME über alle Symbole:")
        for src, n in sorted(totals.items()):
            print(f"  {src:<20} {n:>10} Zeilen")

        print("\n" + "=" * 72)
        print("DuckDB row_counts():")
        for tbl, n in sorted(mgr.persist.row_counts().items()):
            print(f"  {tbl:<24} {n:>12}")
        print("=" * 72)
    finally:
        mgr.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
