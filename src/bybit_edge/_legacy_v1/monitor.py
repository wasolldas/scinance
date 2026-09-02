# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Monitor — zeigt periodisch Position, PnL und Equity des (Demo-)Accounts.

Läuft eigenständig und read-only neben dem LiveRunner. Pollt die Bybit-
REST-API alle ``interval`` Sekunden.

Start:  python -m bybit_edge._legacy_v1.monitor  [--interval 10]
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import sys
import time
from pathlib import Path
from typing import Any

from bybit_edge.config import (
    BYBIT_DEMO,
    BYBIT_TESTNET,
    DATA_DIR,
    PRIMARY_SYMBOL,
)
from bybit_edge._legacy_v1.execution.bybit_executor import BybitExecutor

logger = logging.getLogger("bybit_edge._legacy_v1.monitor")

JOURNAL_PATH: Path = DATA_DIR / "trades_journal.csv"


def _read_journal_summary() -> dict[str, Any]:
    """Aggregiert das Trade-Journal pro Strategie (Anzahl Orders)."""
    if not JOURNAL_PATH.exists():
        return {}
    per_strategy: dict[str, int] = {}
    try:
        with JOURNAL_PATH.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sid = row.get("strategy_id", "?")
                per_strategy[sid] = per_strategy.get(sid, 0) + 1
    except Exception:
        pass
    return per_strategy


async def monitor_loop(symbol: str, interval: float) -> None:
    mode = "DEMO" if BYBIT_DEMO else "TESTNET" if BYBIT_TESTNET else "LIVE"
    ex = BybitExecutor(symbol)
    start_equity: float | None = None

    print("=" * 64)
    print(f"  MONITOR — {symbol} — Modus {mode} — alle {interval:.0f}s")
    print("=" * 64)

    try:
        while True:
            try:
                equity = await ex.get_equity()
                pos = await ex.get_position()
            except Exception as exc:
                print(f"[Fehler] {exc}")
                await asyncio.sleep(interval)
                continue

            if start_equity is None and equity > 0:
                start_equity = equity

            pnl_since_start = (equity - start_equity) if start_equity else 0.0
            ts = time.strftime("%H:%M:%S")

            if pos["size"] > 0:
                pos_str = (
                    f"{pos['side']} {pos['size']:.4f} @ {pos['avg_price']:.2f} "
                    f"| uPnL {pos['unrealised_pnl']:+.2f} USDT"
                )
            else:
                pos_str = "flat"

            print(
                f"[{ts}] Equity {equity:,.2f} USDT "
                f"(seit Start {pnl_since_start:+.2f}) | Pos: {pos_str}"
            )

            journal = _read_journal_summary()
            if journal:
                summary = ", ".join(f"{k}:{v}" for k, v in sorted(journal.items()))
                print(f"          Orders im Journal: {summary}")

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass
    finally:
        await ex.close()


def run() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser(description="Bybit Edge Monitor")
    parser.add_argument("--symbol", default=PRIMARY_SYMBOL)
    parser.add_argument("--interval", type=float, default=10.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    try:
        asyncio.run(monitor_loop(args.symbol, args.interval))
    except KeyboardInterrupt:
        print("\nMonitor beendet.")


if __name__ == "__main__":
    run()
