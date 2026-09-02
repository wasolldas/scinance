"""
Profiling-Harness fuer den Replay-Backtester.

Misst WO die Zeit im Replay hingeht (cProfile, sortiert nach kumulativer
Zeit), statt zu raten. Baut einen synthetischen, aber realistischen
Event-Stream (Ticker + Trades + Liquidations) in eine In-Memory-DuckDB,
sodass sowohl S3 (Pre-Settlement, M22/M23/M24/M8 jeden Tick) als auch S1
(Liquidations-Kaskade -> M14 Hawkes-MLE + M15 Omori-curve_fit) aktiv werden.

Aufruf::

    python scripts/_profile_replay.py                 # synthetisch, ~50k Events
    python scripts/_profile_replay.py --events 50000
    python scripts/_profile_replay.py --db data/bybit_edge.duckdb --symbol BTCUSDT
    python scripts/_profile_replay.py --top 20

Wenn ``--db`` eine echte DuckDB angegeben wird, wird die erste Scheibe
(``--events``) der echten Events fuer dieses Symbol profiliert.

Das Skript ist bewusst NICHT Teil der Tests — es ist ein Operator-Werkzeug,
das man bei Performance-Regressionen erneut laufen laesst.
"""
from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

from bybit_edge.persistence.db import PersistenceLayer
from bybit_edge.replay_backtester import ReplayBacktester
from bybit_edge.state.liquidation_buffer import LiquidationEvent
from bybit_edge.state.ticker_state import TickerSnapshot
from bybit_edge.state.trade_buffer import TradeEvent

_SYMBOL = "BTCUSDT"
_BASE_TS = 1_700_000_000_000


def build_synthetic_db(n_events: int) -> PersistenceLayer:
    """Build an in-memory DuckDB with a realistic mixed event stream.

    Layout (event-time at 1 event / 100 ms so the 1 s cadence fires often):
        * a benign warmup of tickers (mark==index) to fill the S3 Q90 history,
        * a pre-settlement pressure phase (index 0.5% above mark, funding
          window open) so S3 actually enters/exits, and
        * a dense liquidation cascade interleaved with trades so S1 -> M14
          Hawkes-MLE + M15 Omori curve_fit are exercised.

    The split is ~50% tickers / ~35% trades / ~15% liquidations, roughly the
    production mix on the smaller alt symbols where S1 is active.
    """
    persist = PersistenceLayer(db_path=Path(":memory:"))

    step_ms = 100  # 10 events/s of event time
    n_tickers = int(n_events * 0.50)
    n_trades = int(n_events * 0.35)
    n_liqs = n_events - n_tickers - n_trades

    # --- Tickers: 70% benign warmup, 30% in-window pressure phase ---
    warmup = int(n_tickers * 0.70)
    tickers: list[TickerSnapshot] = []
    for i in range(n_tickers):
        ts = _BASE_TS + i * step_ms
        if i < warmup:
            mark = 30_000.0
            index = 30_000.0
            nft = ts + 2 * 3600 * 1000  # 2h ahead -> out of window
        else:
            mark = 30_000.0
            index = mark * (1.0 + 0.005)  # +0.5% -> positive pressure
            nft = ts + 600_000  # 10 min ahead -> in window
        tickers.append(
            TickerSnapshot(
                symbol=_SYMBOL,
                last_price=30_000.0 + (i % 7),
                mark_price=mark,
                index_price=index,
                funding_rate=0.0001,
                next_funding_time=nft,
                open_interest=1_000_000.0 + (i % 50) * 100.0,
                open_interest_value=3.0e10,
                bid1_price=29_999.0,
                bid1_size=5.0,
                ask1_price=30_001.0,
                ask1_size=5.0,
                ts=ts,
                recv_ts=ts / 1000.0,
            )
        )
    persist.write_tickers_batch(tickers)

    # --- Trades spread across the same span (drives Kyle / price history) ---
    rng = np.random.default_rng(7)
    trades: list[TradeEvent] = []
    for i in range(n_trades):
        ts = _BASE_TS + int(rng.integers(0, n_tickers)) * step_ms
        trades.append(
            TradeEvent(
                timestamp_ms=ts,
                price=30_000.0 + float(rng.normal(0, 15)),
                volume=float(abs(rng.normal(1.0, 0.5)) + 0.01),
                side="Buy" if rng.random() > 0.5 else "Sell",
                is_block=False,
            )
        )
    persist.write_trades_batch(trades, symbol=_SYMBOL)

    # --- Liquidation cascade: dense cluster so M14/M15 fit repeatedly ---
    liqs: list[LiquidationEvent] = []
    # Spread liquidations across the stream with bursts every ~3000 ticks so
    # the recent-liq window is non-empty for long stretches -> S1 calls M14/M15.
    for i in range(n_liqs):
        # Cluster index: bursts of ~80 liqs.
        burst = i // 80
        within = i % 80
        center_tick = (burst * 3000 + 1500) % max(n_tickers, 1)
        ts = _BASE_TS + (center_tick + within) * step_ms
        usd = 1.0e6 + abs(float(rng.normal(0, 5e5)))
        liqs.append(
            LiquidationEvent(
                timestamp_ms=ts,
                symbol=_SYMBOL,
                side="Sell" if rng.random() > 0.4 else "Buy",
                volume=usd / 30_000.0,
                price=30_000.0,
                usd_value=usd,
            )
        )
    if liqs:
        persist.write_liquidations_batch(liqs)

    return persist


def _load_real_slice(
    db_path: Path, symbol: str, max_events: int
) -> ReplayBacktester:
    """Load the first ``max_events`` of the real stream for ``symbol``."""
    bt = ReplayBacktester(symbol, db_path=db_path)
    bt.load_events()
    if len(bt._events) > max_events:
        bt._events = bt._events[:max_events]
    return bt


def profile_run(
    bt: ReplayBacktester, interval: float, top: int
) -> tuple[str, float, int]:
    """cProfile a single replay run and return (stats_text, wall_s, n_events)."""
    n_events = len(bt._events)
    pr = cProfile.Profile()
    t0 = time.perf_counter()
    pr.enable()
    bt.run(pipeline_interval_seconds=interval)
    pr.disable()
    wall = time.perf_counter() - t0

    buf = io.StringIO()
    stats = pstats.Stats(pr, stream=buf).sort_stats("cumulative")
    stats.print_stats(top)
    return buf.getvalue(), wall, n_events


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Profile the replay backtester")
    p.add_argument("--events", type=int, default=50_000)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--db", default=None, help="echte DuckDB (sonst synthetisch)")
    p.add_argument("--symbol", default=_SYMBOL)
    args = p.parse_args(argv)

    if args.db:
        print(f"Profiling REAL slice: {args.db} symbol={args.symbol} "
              f"first {args.events} events")
        bt = _load_real_slice(Path(args.db), args.symbol, args.events)
        persist = None
    else:
        print(f"Profiling SYNTHETIC stream: ~{args.events} events")
        persist = build_synthetic_db(args.events)
        bt = ReplayBacktester(args.symbol, db_path=None)
        bt.persist = persist
        bt.load_events()

    stats_text, wall, n_events = profile_run(bt, args.interval, args.top)
    bt.close()
    if persist is not None:
        persist.close()

    print("=" * 78)
    print(f"  Wall-clock: {wall:.2f}s  over  {n_events} events  "
          f"({n_events / wall:,.0f} events/s)")
    print("=" * 78)
    print(stats_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
