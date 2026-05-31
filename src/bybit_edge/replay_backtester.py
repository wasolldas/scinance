"""
Replay-Backtester — spielt persistierte Ticks chronologisch durch die ECHTEN
Strategien des LiveRunners und berechnet pro Strategie Performance-Metriken.

Motivation:
    Der bestehende Kline-Backtester (``scripts/backtest.py``) kann nur
    OHLCV-Strategien testen. Die Microstructure-Edges (S1 Cascade, S3
    Pre-Settlement inkl. live erfasstem Premium-Index, sowie die M22/M23/M24-
    Familie) brauchen Ticker-/Trade-/Liquidations-Ticks. Diese werden vom
    LiveRunner in DuckDB persistiert (Tabellen ``tickers``/``trades``/
    ``liquidations``). Dieser Replay-Backtester ist der einzige Weg, jene
    novel Edges auf echten Tickdaten zu validieren.

Strikte Kausalität (kein Lookahead):
    Der gemergte Event-Stream wird streng in ``ts``-Reihenfolge verarbeitet.
    Beim Verarbeiten eines Events bei Zeit ``t`` sind ausschliesslich Events
    mit ``ts <= t`` in die State-Engines/Buffer eingeflossen. ``ticker_data``
    wird pro gethrotteltem Pipeline-Tick exakt im Format gebaut, das die
    Pipeline (siehe ``live_runner._build_ticker_data``) erwartet.

Ehrliche Einordnung der Daten-Limits:
    * Top-of-Book (bid1/ask1) ist immer persistiert. Wenn der LiveRunner
      zusätzlich mit ``PERSIST_ORDERBOOK=true`` lief, sind in DuckDB auch
      L2-Snapshots (Top-N Levels) gespeichert. In diesem Fall werden M6
      Shannon-L2-Entropie und damit S2 (Entropie-Momentum) auf den
      tatsächlich gesehenen Tiefenprofilen ausgewertet. Ohne L2-Persistenz
      fällt ``_build_ticker_data`` auf den 1-Level-Fallback zurück (S2 wird
      mangels Tiefe i.d.R. keinen Entropy-Collapse triggern).
    * S4 (Pattern-Ensemble) braucht Foundation-Modelle + lange Preisserien,
      S5 (Cross-Sectional) braucht Multi-Symbol-Panels — beides ist aus den
      Single-Symbol-Tickdaten nicht abbildbar. Beide sind ``datenlimitiert``.
    * Real testbar sind S1 (Liquidations-Kaskade) und S3 (Pre-Settlement /
      M22-M24-Familie, inkl. live erfasstem Premium-Index).
"""
from __future__ import annotations

import logging
from collections import deque
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Optional

import numpy as np

from bybit_edge.backtester.engine import BacktestEngine, BacktestResult, Trade
from bybit_edge.config import (
    WF_EMBARGO_MINUTES,
    WF_TEST_DAYS,
    WF_TRAIN_DAYS,
)
from bybit_edge.persistence.db import PersistenceLayer
from bybit_edge.state.liquidation_buffer import LiquidationBuffer, LiquidationEvent
from bybit_edge.state.trade_buffer import TradeBuffer, TradeEvent
from bybit_edge.strategies.strategy1_cascade import Strategy1CascadeDetector
from bybit_edge.strategies.strategy2_entropy_momentum import Strategy2EntropyMomentum
from bybit_edge.strategies.strategy3_pre_settlement import Strategy3PreSettlement
from bybit_edge.strategies.strategy4_pattern_ensemble import Strategy4PatternEnsemble
from bybit_edge.strategies.strategy5_cross_sectional import Strategy5CrossSectional

logger = logging.getLogger(__name__)

# Default seconds_to_settlement when next_funding_time is missing/invalid.
_DEFAULT_SECONDS_TO_SETTLEMENT: float = 3600.0

# Default funding window for liquidation/ trade history (one hour).
_LIQ_HISTORY_SECONDS: float = 3600.0

# How many recent trades to expose to Kyle's Lambda / event-time arrays.
_RECENT_TRADES: int = 100
_RECENT_EVENT_TIMES: int = 200

# Price-history length mirrors the LiveRunner (deque maxlen=512).
_PRICE_HISTORY_MAXLEN: int = 512

# Strategies that cannot be validated with the persisted single-symbol /
# top-of-book data set. Flagged ``datenlimitiert`` in the result metadata.
# Note: S2 becomes testable as soon as L2 ``orderbook_snapshots`` are present
# in the database — :meth:`ReplayBacktester.load_events` then surfaces depth
# arrays in the merged stream and removes S2 from the data-limited set on the
# fly (see ``self._data_limited``).
_DATA_LIMITED: frozenset[str] = frozenset({"S2", "S4", "S5"})


class ReplayBacktester:
    """Replays persisted DuckDB ticks through the real strategies.

    Each of the five strategies is run in isolation (its own instance) so
    that the per-strategy edge can be assessed independently. Entry/exit
    decisions are converted into round-trip :class:`Trade` objects and scored
    with :meth:`BacktestEngine.compute_metrics`.
    """

    def __init__(self, symbol: str, db_path: Optional[Path] = None) -> None:
        self.symbol: str = symbol
        self._db_path: Optional[Path] = db_path

        # Persistence handle (DuckDB). Opened lazily / in load_events.
        self.persist: Optional[PersistenceLayer] = None

        # Merged, chronologically sorted event stream.
        # Each item: (ts_ms, kind, payload) where
        # kind in {"ticker", "trade", "liq", "ob"}. "ob" carries a full L2
        # snapshot reconstructed from the ``orderbook_snapshots`` table.
        self._events: list[tuple[int, str, dict[str, Any]]] = []

        # Backtest engine for fee/slippage-aware metrics.
        self.engine: BacktestEngine = BacktestEngine()

        # Mutable copy of the data-limited set. Becomes a strict subset
        # (S2 removed) when L2 snapshots are present in the loaded window.
        self._data_limited: set[str] = set(_DATA_LIMITED)
        # Whether the loaded window contains L2 orderbook snapshots.
        self._has_orderbook: bool = False
        # Number of folds executed by the last ``run_walkforward`` call.
        # 0 until a walk-forward run has been completed.
        self.last_walkforward_folds: int = 0

    # ------------------------------------------------------------------
    # Event loading
    # ------------------------------------------------------------------

    def _open(self) -> PersistenceLayer:
        """Return an open persistence layer, creating one if necessary."""
        if self.persist is None:
            self.persist = PersistenceLayer(db_path=self._db_path)
        return self.persist

    def load_events(
        self,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
    ) -> int:
        """Load tickers/trades/liquidations from DuckDB into a merged stream.

        The three tables are queried for *symbol* within the optional
        ``[start_ts, end_ts]`` (Unix milliseconds) window, tagged by kind, and
        merged into a single list sorted strictly ascending by ``ts``. Ties
        are broken deterministically by kind so the ordering is stable.

        Returns
        -------
        int
            Number of events loaded.
        """
        persist = self._open()
        conn = persist.conn

        lo = start_ts if start_ts is not None else 0
        hi = end_ts if end_ts is not None else 2**63 - 1

        # Reset depth-availability flags before re-querying — keeps load_events
        # idempotent across multiple calls.
        self._has_orderbook = False
        self._data_limited = set(_DATA_LIMITED)

        events: list[tuple[int, str, dict[str, Any]]] = []

        ticker_rows = conn.execute(
            """
            SELECT ts, symbol, last_price, mark_price, index_price,
                   funding_rate, next_funding_time, open_interest,
                   open_interest_value, bid1_price, bid1_size,
                   ask1_price, ask1_size, recv_ts
            FROM tickers
            WHERE symbol = ? AND ts >= ? AND ts <= ?
            ORDER BY ts
            """,
            [self.symbol, lo, hi],
        ).fetchall()
        for r in ticker_rows:
            events.append((
                int(r[0]),
                "ticker",
                {
                    "ts": int(r[0]),
                    "symbol": str(r[1]),
                    "last_price": float(r[2] or 0.0),
                    "mark_price": float(r[3] or 0.0),
                    "index_price": float(r[4] or 0.0),
                    "funding_rate": float(r[5] or 0.0),
                    "next_funding_time": int(r[6] or 0),
                    "open_interest": float(r[7] or 0.0),
                    "open_interest_value": float(r[8] or 0.0),
                    "bid1_price": float(r[9] or 0.0),
                    "bid1_size": float(r[10] or 0.0),
                    "ask1_price": float(r[11] or 0.0),
                    "ask1_size": float(r[12] or 0.0),
                    "recv_ts": float(r[13] or 0.0),
                },
            ))

        trade_rows = conn.execute(
            """
            SELECT ts, price, volume, side, is_block
            FROM trades
            WHERE symbol = ? AND ts >= ? AND ts <= ?
            ORDER BY ts
            """,
            [self.symbol, lo, hi],
        ).fetchall()
        for r in trade_rows:
            events.append((
                int(r[0]),
                "trade",
                {
                    "timestamp_ms": int(r[0]),
                    "price": float(r[1] or 0.0),
                    "volume": float(r[2] or 0.0),
                    "side": str(r[3] or ""),
                    "is_block": bool(r[4]),
                },
            ))

        liq_rows = conn.execute(
            """
            SELECT ts, symbol, side, volume, price, usd_value
            FROM liquidations
            WHERE symbol = ? AND ts >= ? AND ts <= ?
            ORDER BY ts
            """,
            [self.symbol, lo, hi],
        ).fetchall()
        for r in liq_rows:
            events.append((
                int(r[0]),
                "liq",
                {
                    "timestamp_ms": int(r[0]),
                    "symbol": str(r[1]),
                    "side": str(r[2] or ""),
                    "volume": float(r[3] or 0.0),
                    "price": float(r[4] or 0.0),
                    "usd_value": float(r[5] or 0.0),
                },
            ))

        # Optional L2 orderbook snapshots (opt-in via PERSIST_ORDERBOOK in the
        # LiveRunner). Reconstructed as one ``ob`` event per persisted snapshot
        # with full top-N bid/ask price+size arrays.
        ob_snaps = persist.query_orderbook_snapshots(
            self.symbol, lo, hi, depth=20
        )
        self._has_orderbook = bool(ob_snaps)
        if self._has_orderbook:
            # S2 (Entropy-Momentum) needs depth>1 to compute Shannon-L2 entropy
            # meaningfully. With persisted L2 snapshots present it is no longer
            # data-limited; remove it from the per-instance set.
            self._data_limited.discard("S2")
        for snap in ob_snaps:
            events.append((
                int(snap["ts"]),
                "ob",
                {
                    "ts": int(snap["ts"]),
                    "bid_prices": np.asarray(snap["bid_prices"], dtype=np.float64),
                    "bid_sizes": np.asarray(snap["bid_sizes"], dtype=np.float64),
                    "ask_prices": np.asarray(snap["ask_prices"], dtype=np.float64),
                    "ask_sizes": np.asarray(snap["ask_sizes"], dtype=np.float64),
                    "recv_ts": float(snap["recv_ts"]),
                },
            ))

        # Stable chronological sort. Tie-break by a fixed kind order so that
        # at equal ts we deterministically ingest market data first (ticker,
        # trade, liq, ob) — never a future event before a past one. The OB
        # snapshot lands last among equal-ts events so that the depth profile
        # observed at ts==T reflects state after all other market events at T.
        kind_order = {"ticker": 0, "trade": 1, "liq": 2, "ob": 3}
        events.sort(key=lambda e: (e[0], kind_order[e[1]]))

        self._events = events
        return len(events)

    # ------------------------------------------------------------------
    # Ticker-data builder (mirrors live_runner._build_ticker_data)
    # ------------------------------------------------------------------

    @staticmethod
    def _seconds_to_settlement(next_funding_time: int, ticker_ts: int) -> float:
        """Event-time seconds until the next funding settlement.

        Strictly uses *event* time (``ticker_ts``), never wall-clock, since
        the replay is historical. Falls back to a one-hour default when
        ``next_funding_time`` is missing/invalid or already in the past.
        """
        if next_funding_time <= 0:
            return _DEFAULT_SECONDS_TO_SETTLEMENT
        secs = (next_funding_time - ticker_ts) / 1000.0
        return secs if secs > 0 else _DEFAULT_SECONDS_TO_SETTLEMENT

    def _build_ticker_data(
        self,
        snap: dict[str, Any],
        trade_buffer: TradeBuffer,
        liq_buffer: LiquidationBuffer,
        price_history: deque[float],
        now_ms: int,
        ob_snap: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Build a ``ticker_data`` dict in the exact format the pipeline uses.

        Only data already ingested up to *now_ms* is used — strictly causal.
        When ``ob_snap`` is provided (the latest persisted L2 snapshot with
        ts <= now_ms) the depth profile arrays are taken from it; otherwise
        the order-book depth is reconstructed as a 1-level fallback from
        ``bid1``/``ask1``.
        """
        last_price: float = snap["last_price"]
        mark_price: float = snap["mark_price"] or last_price
        index_price: float = snap["index_price"] or last_price

        bid1_price: float = snap["bid1_price"]
        bid1_size: float = snap["bid1_size"]
        ask1_price: float = snap["ask1_price"]
        ask1_size: float = snap["ask1_size"]

        # Depth profile arrays. Prefer the persisted L2 snapshot (full top-N
        # bid/ask sizes) when present, otherwise fall back to a 1-level array
        # synthesised from bid1/ask1.
        use_ob = ob_snap is not None
        bid_sizes_from_ob = (
            use_ob
            and isinstance(ob_snap.get("bid_sizes"), np.ndarray)
            and ob_snap["bid_sizes"].size > 0
        )
        ask_sizes_from_ob = (
            use_ob
            and isinstance(ob_snap.get("ask_sizes"), np.ndarray)
            and ob_snap["ask_sizes"].size > 0
        )
        bid_prices_from_ob = (
            use_ob
            and isinstance(ob_snap.get("bid_prices"), np.ndarray)
            and ob_snap["bid_prices"].size > 0
        )
        ask_prices_from_ob = (
            use_ob
            and isinstance(ob_snap.get("ask_prices"), np.ndarray)
            and ob_snap["ask_prices"].size > 0
        )

        if bid_sizes_from_ob:
            bid_sizes: np.ndarray = np.asarray(
                ob_snap["bid_sizes"], dtype=np.float64
            )
        else:
            bid_sizes = (
                np.array([bid1_size], dtype=np.float64)
                if bid1_size > 0
                else np.ones(1, dtype=np.float64)
            )

        if ask_sizes_from_ob:
            ask_sizes: np.ndarray = np.asarray(
                ob_snap["ask_sizes"], dtype=np.float64
            )
        else:
            ask_sizes = (
                np.array([ask1_size], dtype=np.float64)
                if ask1_size > 0
                else np.ones(1, dtype=np.float64)
            )

        if bid_prices_from_ob and bid_sizes_from_ob:
            best_bid: tuple[float, float] = (
                float(ob_snap["bid_prices"][0]),
                float(ob_snap["bid_sizes"][0]),
            )
        else:
            best_bid = (
                (bid1_price, bid1_size)
                if bid1_price > 0
                else (last_price - 1.0, 1.0)
            )

        if ask_prices_from_ob and ask_sizes_from_ob:
            best_ask: tuple[float, float] = (
                float(ob_snap["ask_prices"][0]),
                float(ob_snap["ask_sizes"][0]),
            )
        else:
            best_ask = (
                (ask1_price, ask1_size)
                if ask1_price > 0
                else (last_price + 1.0, 1.0)
            )

        # premium_index follows the TickerSnapshot.basis definition.
        premium_index: float = (
            (mark_price - index_price) / index_price if index_price else 0.0
        )

        seconds_to_settlement: float = self._seconds_to_settlement(
            snap["next_funding_time"], snap["ts"]
        )

        liq_events = [
            {"timestamp_ms": e.timestamp_ms, "usd_value": e.usd_value, "side": e.side}
            for e in liq_buffer.recent_by_ts(_LIQ_HISTORY_SECONDS, now_ms=now_ms)
        ]

        trade_events = trade_buffer.recent_events(_RECENT_TRADES)
        trades = [
            {
                "price": t.price,
                "volume": t.volume,
                "side": t.side,
                "timestamp_ms": t.timestamp_ms,
            }
            for t in trade_events
        ]

        ts_ms = trade_buffer.recent_timestamps(_RECENT_EVENT_TIMES)
        event_times = (
            ts_ms / 1000.0 if ts_ms.size else np.array([], dtype=np.float64)
        )

        price_series = np.array(price_history, dtype=np.float64)

        return {
            "ts": now_ms / 1000.0,
            "last_price": last_price,
            "mark_price": mark_price,
            "index_price": index_price,
            "premium_index": premium_index,
            "funding_rate": snap["funding_rate"],
            "open_interest": snap["open_interest"],
            "seconds_to_settlement": seconds_to_settlement,
            "bid_sizes": bid_sizes,
            "ask_sizes": ask_sizes,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "liq_events": liq_events,
            "event_times": event_times,
            "trades": trades,
            "price_series": price_series,
        }

    # ------------------------------------------------------------------
    # Strategy dispatch (mirrors pipeline.process_ticker call signatures)
    # ------------------------------------------------------------------

    @staticmethod
    def _dominant_liq_side(liq_events: list[dict[str, Any]]) -> str:
        """Return the dominant liquidation side by USD volume ("Long"/"Short").

        Bybit liquidation ``side`` "Sell" represents a long liquidation, "Buy"
        a short liquidation. S1 wants the dominant *position* side that got
        liquidated, so map accordingly. Defaults to "Long".
        """
        if not liq_events:
            return "Long"
        long_usd = sum(e["usd_value"] for e in liq_events if e.get("side") == "Sell")
        short_usd = sum(e["usd_value"] for e in liq_events if e.get("side") == "Buy")
        return "Long" if long_usd >= short_usd else "Short"

    def _eval_strategy(
        self,
        strategy_id: str,
        strategy: Any,
        ticker_data: dict[str, Any],
        ts_seconds: float,
    ) -> dict[str, Any]:
        """Call the given strategy with the same arguments the pipeline uses.

        Returns the strategy's action dict, or a neutral ``wait`` dict if the
        strategy is gated off for this tick (e.g. no liquidations for S1, or
        missing multi-symbol data for S5).
        """
        price: float = float(ticker_data["last_price"])
        seconds_to_settlement: float = float(ticker_data["seconds_to_settlement"])
        open_interest: float = float(ticker_data["open_interest"])

        if strategy_id == "S1":
            liq_events = ticker_data["liq_events"]
            if not liq_events:
                return {"action": "wait", "direction": 0, "strategy": "S1"}
            liq_side = self._dominant_liq_side(liq_events)
            return strategy.on_data(
                liq_events=liq_events,
                event_times=ticker_data["event_times"],
                open_interest=open_interest,
                trades=ticker_data["trades"],
                current_ts=ts_seconds,
                liq_side=liq_side,
            )

        if strategy_id == "S2":
            return strategy.on_ticker(
                bid_sizes=ticker_data["bid_sizes"],
                ask_sizes=ticker_data["ask_sizes"],
                best_bid=ticker_data["best_bid"],
                best_ask=ticker_data["best_ask"],
                ticker_data=ticker_data,
                seconds_to_settlement=seconds_to_settlement,
                price=price,
                ts=ts_seconds,
            )

        if strategy_id == "S3":
            return strategy.on_ticker(
                ticker_data=ticker_data,
                seconds_to_settlement=seconds_to_settlement,
                open_interest=open_interest,
            )

        if strategy_id == "S4":
            price_series = ticker_data["price_series"]
            if len(price_series) <= 10:
                return {"action": "wait", "direction": 0, "strategy": "S4"}
            return strategy.on_data(
                price_series=price_series,
                library=None,
                current_price=price,
                ts=ts_seconds,
            )

        if strategy_id == "S5":
            # No multi-symbol panel is persisted, so S5 is never triggerable
            # in single-symbol replay. Kept for completeness / honesty.
            return {"action": "wait", "direction": 0, "strategy": "S5"}

        return {"action": "wait", "direction": 0, "strategy": strategy_id}

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------

    def run(self, pipeline_interval_seconds: float = 1.0) -> dict[str, BacktestResult]:
        """Replay the loaded events chronologically through every strategy.

        Events are ingested strictly in ``ts`` order. After ingesting an event
        the pipeline is (re-)evaluated at most once per
        ``pipeline_interval_seconds`` (throttled exactly like the LiveRunner).
        Each strategy keeps its own open position; an ``enter`` opens a
        position, an ``exit`` closes it into a round-trip :class:`Trade`.

        Returns
        -------
        dict[str, BacktestResult]
            One result per strategy id ("S1".."S5").
        """
        strategies: dict[str, Any] = self._build_strategies()
        for strat in strategies.values():
            strat.reset()

        # Per-strategy open position: {"side","entry_price","entry_ts"} or None.
        open_pos: dict[str, Optional[dict[str, Any]]] = {sid: None for sid in strategies}
        trades_out: dict[str, list[Trade]] = {sid: [] for sid in strategies}

        # Causal state engines built up incrementally from the event stream.
        trade_buffer = TradeBuffer(maxlen=2000)
        liq_buffer = LiquidationBuffer(maxlen=2000)
        price_history: deque[float] = deque(maxlen=_PRICE_HISTORY_MAXLEN)

        last_ticker, last_ob_snap, last_ts_ms = self._replay_events(
            events=self._events,
            strategies=strategies,
            trade_buffer=trade_buffer,
            liq_buffer=liq_buffer,
            price_history=price_history,
            open_pos=open_pos,
            trades_out=trades_out,
            pipeline_interval_seconds=pipeline_interval_seconds,
            record_trades=True,
            last_ticker=None,
            last_ob_snap=None,
            last_pipeline_ms=None,
        )

        # Force-close any open positions at the last observed price.
        final_price = (
            float(last_ticker["last_price"]) if last_ticker else 0.0
        )
        final_ts_ms = last_ts_ms if last_ts_ms is not None else 0
        for sid in strategies:
            pos = open_pos[sid]
            if pos is not None and final_price > 0:
                trades_out[sid].append(
                    self._make_trade(
                        side=pos["side"],
                        entry_price=pos["entry_price"],
                        entry_ts=pos["entry_ts"],
                        exit_price=final_price,
                        exit_ts=final_ts_ms,
                    )
                )
                open_pos[sid] = None

        return {
            sid: self.engine.compute_metrics(trades_out[sid]) for sid in strategies
        }

    # ------------------------------------------------------------------
    # Internal replay primitive — shared by run() and run_walkforward()
    # ------------------------------------------------------------------

    @staticmethod
    def _build_strategies() -> dict[str, Any]:
        """Construct one fresh instance per strategy id (mirrors live runner)."""
        return {
            "S1": Strategy1CascadeDetector(),
            "S2": Strategy2EntropyMomentum(),
            "S3": Strategy3PreSettlement(),
            "S4": Strategy4PatternEnsemble(),
            "S5": Strategy5CrossSectional(),
        }

    def _replay_events(
        self,
        events: list[tuple[int, str, dict[str, Any]]],
        strategies: dict[str, Any],
        trade_buffer: TradeBuffer,
        liq_buffer: LiquidationBuffer,
        price_history: deque[float],
        open_pos: dict[str, Optional[dict[str, Any]]],
        trades_out: dict[str, list[Trade]],
        pipeline_interval_seconds: float,
        record_trades: bool,
        last_ticker: Optional[dict[str, Any]],
        last_ob_snap: Optional[dict[str, Any]],
        last_pipeline_ms: Optional[int],
    ) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]], Optional[int]]:
        """Drive the causal replay loop over *events*.

        This is the single source of truth for the chronological replay logic
        — both :meth:`run` and :meth:`run_walkforward` use it. Behaviour is
        identical to the single-pass loop in the original ``run``:

        * Trades / liquidations / OB snapshots are ingested into the matching
          buffer immediately.
        * Tickers throttle the pipeline by ``pipeline_interval_seconds`` and
          drive ``_build_ticker_data`` + ``_eval_strategy`` per strategy.

        ``record_trades`` controls whether ``_apply_signal`` is allowed to
        push round-trip :class:`Trade` objects into ``trades_out``. When
        ``False`` (train / warmup phase) any closing signal still clears the
        per-strategy open position but the resulting trade is discarded —
        keeping the strategy state in sync without polluting fold results.

        Returns the (last_ticker, last_ob_snap, last_ts_ms) seen, so that the
        caller can pick up where the slice left off or force-close residual
        positions at the end of the run.
        """
        interval_ms: int = max(int(pipeline_interval_seconds * 1000), 1)
        if last_pipeline_ms is None:
            last_pipeline_ms = -interval_ms  # ensures first ticker fires

        last_ts_ms: Optional[int] = (
            events[-1][0] if events else None
        )

        for ts_ms, kind, payload in events:
            # --- Ingest event into the appropriate causal buffer ---
            if kind == "trade":
                evt = TradeEvent(
                    timestamp_ms=payload["timestamp_ms"],
                    price=payload["price"],
                    volume=payload["volume"],
                    side=payload["side"],
                    is_block=payload["is_block"],
                )
                trade_buffer.add(evt)
                if evt.price > 0:
                    price_history.append(evt.price)
                continue

            if kind == "liq":
                liq_buffer.add(
                    LiquidationEvent(
                        timestamp_ms=payload["timestamp_ms"],
                        symbol=payload["symbol"],
                        side=payload["side"],
                        volume=payload["volume"],
                        price=payload["price"],
                        usd_value=payload["usd_value"],
                    )
                )
                continue

            if kind == "ob":
                # Persisted L2 snapshot — stash it for the next pipeline tick.
                # Strictly causal: ts of this OB is <= the next ticker's ts
                # (events are sorted by ts ascending).
                last_ob_snap = payload
                continue

            # kind == "ticker"
            last_ticker = payload
            if payload["last_price"] <= 0:
                continue

            # Throttle: re-evaluate the pipeline at most every interval.
            if ts_ms - last_pipeline_ms < interval_ms:
                continue
            last_pipeline_ms = ts_ms

            ticker_data = self._build_ticker_data(
                snap=last_ticker,
                trade_buffer=trade_buffer,
                liq_buffer=liq_buffer,
                price_history=price_history,
                now_ms=ts_ms,
                ob_snap=last_ob_snap,
            )
            ts_seconds = ts_ms / 1000.0
            price = float(ticker_data["last_price"])

            for sid, strat in strategies.items():
                signal = self._eval_strategy(sid, strat, ticker_data, ts_seconds)
                self._apply_signal(
                    strategy_id=sid,
                    signal=signal,
                    price=price,
                    ts_ms=ts_ms,
                    open_pos=open_pos,
                    trades_out=trades_out,
                    record_trades=record_trades,
                )

        return last_ticker, last_ob_snap, last_ts_ms

    # ------------------------------------------------------------------
    # Walk-forward replay
    # ------------------------------------------------------------------

    def run_walkforward(
        self,
        pipeline_interval_seconds: float = 1.0,
        train_days: int = WF_TRAIN_DAYS,
        test_days: int = WF_TEST_DAYS,
        embargo_minutes: int = WF_EMBARGO_MINUTES,
        min_train_events: int = 100,
        param_overrides: Optional[dict[str, Any]] = None,
    ) -> dict[str, BacktestResult]:
        """Replay events in walk-forward folds: train (warmup, trades discarded)
        → embargo → test (trades counted). Slides by ``test_days``. Concatenates
        test-fold trades per strategy and returns one :class:`BacktestResult`
        per strategy.

        Layout per fold::

            |--- train_days ---|-- embargo --|--- test_days ---|
            ^                  ^             ^                 ^
            train_start     train_end    test_start         test_end

        Then the window advances by ``test_days``.

        Parameters
        ----------
        pipeline_interval_seconds
            Pipeline throttle (matches LiveRunner).
        train_days, test_days, embargo_minutes
            Fold geometry; defaults come from :mod:`bybit_edge.config`.
        min_train_events
            Folds with fewer events in their *train* slice are skipped (too
            little data to warm a strategy up meaningfully).
        param_overrides
            Optional ``{config_attribute_name: value}`` mapping applied via
            :class:`bybit_edge.tuning.ParameterContext` for the entire
            walk-forward sweep. Strategy instances are constructed *inside*
            the context (once per fold) so they pick up the overridden
            values; the context is torn down on return so subsequent calls
            see the originals. When ``None`` (default) behaviour is
            bit-identical to the pre-tuning implementation.

        Returns
        -------
        dict[str, BacktestResult]
            One result per strategy id, computed on the concatenation of all
            test-fold trades. The ``n_folds_executed`` count is exposed via
            :attr:`last_walkforward_folds` for the CLI.
        """
        # ParameterContext is only imported when actually needed — keeps the
        # backtester import-light and free of any tuning-only dependencies.
        if param_overrides:
            from bybit_edge.tuning.params import ParameterContext
            ctx: Any = ParameterContext(param_overrides)
        else:
            ctx = nullcontext()

        with ctx:
            return self._run_walkforward_inner(
                pipeline_interval_seconds=pipeline_interval_seconds,
                train_days=train_days,
                test_days=test_days,
                embargo_minutes=embargo_minutes,
                min_train_events=min_train_events,
            )

    def _run_walkforward_inner(
        self,
        pipeline_interval_seconds: float,
        train_days: int,
        test_days: int,
        embargo_minutes: int,
        min_train_events: int,
    ) -> dict[str, BacktestResult]:
        """Body of :meth:`run_walkforward` — executes the fold sweep.

        Extracted so that :meth:`run_walkforward` can optionally enter a
        :class:`bybit_edge.tuning.ParameterContext` around the entire sweep
        without altering the per-fold logic. When called directly (e.g.
        from tests) it preserves the pre-tuning behaviour exactly.
        """
        ms_per_day = 24 * 3600 * 1000
        ms_per_min = 60 * 1000
        train_ms = int(train_days) * ms_per_day
        test_ms = int(test_days) * ms_per_day
        embargo_ms = int(embargo_minutes) * ms_per_min

        events = self._events
        if not events:
            self.last_walkforward_folds = 0
            empty_strats = self._build_strategies()
            return {
                sid: self.engine.compute_metrics([]) for sid in empty_strats
            }

        first_ts = events[0][0]
        last_ts = events[-1][0]

        # Pre-bucket events by fold boundaries via simple linear sweep — the
        # event list is already sorted ascending by ts.
        cursor = first_ts
        test_trades_acc: dict[str, list[Trade]] = {
            sid: [] for sid in self._build_strategies()
        }
        folds_executed = 0

        # Index pointer to avoid O(N^2) repeated scans.
        idx = 0
        n_events = len(events)

        while True:
            train_start = cursor
            train_end = train_start + train_ms
            test_start = train_end + embargo_ms
            test_end = test_start + test_ms

            if test_end > last_ts:
                # No more full folds fit in the data window.
                break

            # Advance idx past any events strictly before train_start (sliding
            # windows can overlap when test_ms < train_ms; we re-scan from
            # ``idx_train_start`` so previous-fold events are not consumed).
            idx_train_start = idx
            while (
                idx_train_start < n_events
                and events[idx_train_start][0] < train_start
            ):
                idx_train_start += 1

            # Slice train events: [train_start, train_end).
            idx_train_end = idx_train_start
            while (
                idx_train_end < n_events
                and events[idx_train_end][0] < train_end
            ):
                idx_train_end += 1

            # Slice test events: [test_start, test_end).
            idx_test_start = idx_train_end
            while (
                idx_test_start < n_events
                and events[idx_test_start][0] < test_start
            ):
                idx_test_start += 1
            idx_test_end = idx_test_start
            while (
                idx_test_end < n_events
                and events[idx_test_end][0] < test_end
            ):
                idx_test_end += 1

            train_events = events[idx_train_start:idx_train_end]
            test_events = events[idx_test_start:idx_test_end]

            # Advance the outer cursor (sliding by test_days) regardless of
            # whether the fold is admissible, so we don't loop forever.
            cursor += test_ms

            if len(train_events) < min_train_events:
                # Not enough warmup data — skip this fold cleanly.
                idx = idx_train_start
                continue
            if not test_events:
                idx = idx_train_start
                continue

            # --- Fresh strategy instances + buffers per fold ---
            strategies = self._build_strategies()
            for strat in strategies.values():
                strat.reset()

            trade_buffer = TradeBuffer(maxlen=2000)
            liq_buffer = LiquidationBuffer(maxlen=2000)
            price_history: deque[float] = deque(maxlen=_PRICE_HISTORY_MAXLEN)
            open_pos: dict[str, Optional[dict[str, Any]]] = {
                sid: None for sid in strategies
            }
            train_trades_sink: dict[str, list[Trade]] = {
                sid: [] for sid in strategies
            }

            # 1) TRAIN phase — warm strategies; discard any trades.
            last_ticker, last_ob_snap, _ = self._replay_events(
                events=train_events,
                strategies=strategies,
                trade_buffer=trade_buffer,
                liq_buffer=liq_buffer,
                price_history=price_history,
                open_pos=open_pos,
                trades_out=train_trades_sink,
                pipeline_interval_seconds=pipeline_interval_seconds,
                record_trades=False,
                last_ticker=None,
                last_ob_snap=None,
                last_pipeline_ms=None,
            )
            # Clear any open positions accumulated during train so that the
            # test phase starts flat — the strategy *state* is what we want
            # to keep, not the in-flight position.
            for sid in strategies:
                open_pos[sid] = None

            # 2) EMBARGO — events in [train_end, test_start) are NOT replayed.
            # Strategy state stays exactly as it was at end-of-train.

            # 3) TEST phase — count trades into the fold accumulator.
            test_trades_fold: dict[str, list[Trade]] = {
                sid: [] for sid in strategies
            }
            last_ticker, last_ob_snap, last_ts_ms = self._replay_events(
                events=test_events,
                strategies=strategies,
                trade_buffer=trade_buffer,
                liq_buffer=liq_buffer,
                price_history=price_history,
                open_pos=open_pos,
                trades_out=test_trades_fold,
                pipeline_interval_seconds=pipeline_interval_seconds,
                record_trades=True,
                last_ticker=last_ticker,
                last_ob_snap=last_ob_snap,
                last_pipeline_ms=None,
            )

            # Force-close any positions still open at end-of-test.
            final_price = (
                float(last_ticker["last_price"]) if last_ticker else 0.0
            )
            final_ts_ms = last_ts_ms if last_ts_ms is not None else test_end
            for sid in strategies:
                pos = open_pos[sid]
                if pos is not None and final_price > 0:
                    test_trades_fold[sid].append(
                        self._make_trade(
                            side=pos["side"],
                            entry_price=pos["entry_price"],
                            entry_ts=pos["entry_ts"],
                            exit_price=final_price,
                            exit_ts=final_ts_ms,
                        )
                    )
                    open_pos[sid] = None

            # Concatenate this fold's test trades.
            for sid, trades in test_trades_fold.items():
                test_trades_acc[sid].extend(trades)

            folds_executed += 1
            idx = idx_train_start

        self.last_walkforward_folds = folds_executed
        return {
            sid: self.engine.compute_metrics(test_trades_acc[sid])
            for sid in test_trades_acc
        }

    # ------------------------------------------------------------------
    # Position / trade bookkeeping
    # ------------------------------------------------------------------

    def _apply_signal(
        self,
        strategy_id: str,
        signal: dict[str, Any],
        price: float,
        ts_ms: int,
        open_pos: dict[str, Optional[dict[str, Any]]],
        trades_out: dict[str, list[Trade]],
        record_trades: bool = True,
    ) -> None:
        """Update the per-strategy position from a strategy signal.

        When ``record_trades`` is ``False`` (used for the walk-forward train /
        warmup phase) the bookkeeping still happens — positions open and close
        so the strategy state stays consistent — but the resulting round-trip
        :class:`Trade` is discarded instead of being appended to
        ``trades_out``.
        """
        action: str = signal.get("action", "wait")
        direction: int = int(signal.get("direction", 0))
        pos = open_pos[strategy_id]

        if action == "enter" and pos is None and direction != 0:
            side = "Long" if direction > 0 else "Short"
            open_pos[strategy_id] = {
                "side": side,
                "entry_price": price,
                "entry_ts": ts_ms,
            }
        elif action == "exit" and pos is not None:
            if record_trades:
                trades_out[strategy_id].append(
                    self._make_trade(
                        side=pos["side"],
                        entry_price=pos["entry_price"],
                        entry_ts=pos["entry_ts"],
                        exit_price=price,
                        exit_ts=ts_ms,
                    )
                )
            open_pos[strategy_id] = None

    def _make_trade(
        self,
        side: str,
        entry_price: float,
        entry_ts: int,
        exit_price: float,
        exit_ts: int,
    ) -> Trade:
        """Build a fee/slippage-aware round-trip :class:`Trade` (qty=1.0)."""
        qty = 1.0
        slip_entry = self.engine._slipped_price(entry_price, side)
        exit_side = "Short" if side == "Long" else "Long"
        slip_exit = self.engine._slipped_price(exit_price, exit_side)

        entry_fee = self.engine._apply_fee(slip_entry, qty, "taker")
        exit_fee = self.engine._apply_fee(slip_exit, qty, "taker")

        if side == "Long":
            raw_pnl = (slip_exit - slip_entry) * qty
        else:
            raw_pnl = (slip_entry - slip_exit) * qty
        net_pnl = raw_pnl - entry_fee - exit_fee
        pnl_bps = (
            (net_pnl / (slip_entry * qty)) * 10_000.0 if slip_entry > 0 else 0.0
        )

        return Trade(
            symbol=self.symbol,
            entry_ts=entry_ts,
            exit_ts=exit_ts,
            side=side,
            entry_price=slip_entry,
            exit_price=slip_exit,
            quantity=qty,
            fee_type="taker",
            pnl=net_pnl,
            pnl_bps=pnl_bps,
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @staticmethod
    def is_data_limited(strategy_id: str) -> bool:
        """Whether a strategy is *statically* data-limited (S2/S4/S5).

        This is the conservative default and reflects the assumption that no
        L2 orderbook snapshots are persisted. For the actual runtime status
        (which can promote S2 to "real testbar" once L2 snapshots are loaded),
        prefer :meth:`is_data_limited_runtime` on a loaded instance.
        """
        return strategy_id in _DATA_LIMITED

    def is_data_limited_runtime(self, strategy_id: str) -> bool:
        """Per-instance data-limited check.

        After :meth:`load_events` has run, S2 is considered *not* data-limited
        if the loaded window contained at least one L2 orderbook snapshot.
        """
        return strategy_id in self._data_limited

    @property
    def has_orderbook(self) -> bool:
        """Whether the currently-loaded event stream contains L2 snapshots."""
        return self._has_orderbook

    def close(self) -> None:
        """Close the underlying persistence handle (if open)."""
        if self.persist is not None:
            self.persist.close()
            self.persist = None
