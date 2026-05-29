"""
Replay-Backtest-Driver — spielt persistierte Ticks (DuckDB) durch die echten
Microstructure-Strategien und vergleicht sie pro Strategie.

Im Gegensatz zu ``scripts/backtest.py`` (nur OHLCV) testet dieser Treiber die
novel Edges, die Tickdaten brauchen:

    Real testbar (aus persistierten Ticks):
        * S1 Cascade        — Liquidations-Stream + Hawkes/GR-Omori/SIR
        * S3 Pre-Settlement — M22/M23/M24-Familie inkl. live Premium-Index
    Datenlimitiert (mit dem persistierten Datensatz NICHT validierbar):
        * S2 Entropie-Momentum — braucht volle L2-Tiefe (nur Top-of-Book da)
        * S4 Pattern-Ensemble  — braucht Foundation-Modelle + lange Serien
        * S5 Cross-Sectional   — braucht Multi-Symbol-Panel

Aufruf:
    python scripts/replay_backtest.py --symbol BTCUSDT --interval 1.0
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bybit_edge.config import DB_PATH
from bybit_edge.replay_backtester import ReplayBacktester


def main() -> None:
    parser = argparse.ArgumentParser(description="Bybit Edge Replay-Backtest-Driver")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument(
        "--db",
        default=None,
        help="Pfad zur DuckDB-Datei (Default: config.DB_PATH)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Pipeline-Throttle in Sekunden (wie im LiveRunner)",
    )
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else DB_PATH

    print("=" * 75)
    print(f"  REPLAY-BACKTEST — {args.symbol} — interval={args.interval}s")
    print(f"  DuckDB: {db_path}")
    print("=" * 75)

    if str(db_path) != ":memory:" and not Path(db_path).exists():
        print(
            "\nKeine DuckDB-Datei gefunden. Erst Daten sammeln mit "
            "PERSIST_ENABLED=true\n(LiveRunner laufen lassen, dann erneut "
            "ausfuehren)."
        )
        return

    bt = ReplayBacktester(symbol=args.symbol, db_path=db_path)
    try:
        n_events = bt.load_events()
        print(f"  Geladene Events: {n_events}")
        if n_events == 0:
            print(
                "\nDuckDB ist leer (keine Ticks fuer dieses Symbol). "
                "Erst Daten sammeln mit PERSIST_ENABLED=true."
            )
            return

        results = bt.run(pipeline_interval_seconds=args.interval)
    finally:
        bt.close()

    rows: list[dict[str, Any]] = []
    for sid, res in results.items():
        rows.append({
            "strategy": sid,
            "sharpe": round(res.sharpe, 3),
            "win_rate": round(res.win_rate, 3),
            "max_dd": round(res.max_drawdown, 4),
            "total_return": round(res.total_return, 4),
            "n_trades": res.n_trades,
            "data_limited": ReplayBacktester.is_data_limited(sid),
        })

    rows.sort(key=lambda r: r["sharpe"], reverse=True)

    print(
        f"\n{'Strategie':<12}{'Sharpe':>9}{'Hit':>7}{'MaxDD':>11}"
        f"{'Return':>11}{'Trades':>8}  Hinweis"
    )
    print("-" * 75)
    for r in rows:
        note = "datenlimitiert" if r["data_limited"] else "real testbar"
        print(
            f"{r['strategy']:<12}{r['sharpe']:>9.2f}{r['win_rate']:>7.2f}"
            f"{r['max_dd']:>11.4f}{r['total_return']:>11.4f}{r['n_trades']:>8}"
            f"  {note}"
        )

    out = (
        Path(__file__).resolve().parent.parent
        / "edge_research_framework"
        / "results"
        / "replay_backtest_results.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "symbol": args.symbol,
        "interval_seconds": args.interval,
        "n_events": n_events,
        "results": rows,
        "notes": {
            "real_testable": ["S1", "S3"],
            "data_limited": ["S2", "S4", "S5"],
            "reason": (
                "Nur Top-of-Book (bid1/ask1) persistiert; keine volle L2-Tiefe "
                "(M6 Shannon-Entropie nicht testbar -> S2). S4 braucht "
                "Foundation-Modelle + lange Serien, S5 ein Multi-Symbol-Panel."
            ),
        },
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nErgebnisse gespeichert: {out}")
    print(
        "\nHinweis: S2/S4/S5 sind datenlimitiert (Top-of-Book / Single-Symbol). "
        "Real validierbar sind S1 (Cascade) und S3 (Pre-Settlement)."
    )


if __name__ == "__main__":
    main()
