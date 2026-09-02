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

Performance / GPU (ehrliche Einordnung — gemessen, nicht geraten):
    Ein cProfile-Lauf (``scripts/_profile_replay.py``) zeigt: der Replay ist
    CPU-gebunden, und der Hotspot ist M15 ``_fit_omori`` via
    ``scipy.optimize.curve_fit`` (~90 % der kumulativen Zeit auf einem
    Liquidations-Cascade-Stream). M14 ``_fit_mle`` ist dank des zeit-basierten
    ``HAWKES_REFIT_SECONDS``-Throttles vernachlässigbar (~1 % — refittet nur
    alle 30 s Event-Zeit, im Live identisch). S3 (M22/M23/M24/M8) inkl.
    ``np.quantile`` ist ebenfalls vernachlässigbar.

    Warum GPU hier NICHT hilft (kein Cargo-Cult): curve_fit / minimize sind
    SEQUENZIELLE Levenberg-Marquardt-/L-BFGS-Optimierungen auf winzigen
    (10..120-Punkte-) Fenstern. Der Host->Device-Transfer-Overhead pro Iter
    übersteigt den Rechen-Nutzen um Größenordnungen; es gibt nichts zu
    batchen. Die regelbasierten Strategien sind numpy-Skalar-Arithmetik —
    auch kein GPU-Fall. GPU lohnt sich nur im OFFLINE-Training der
    Torch-Modelle (M18/M19/M20, M1) via ``scripts/train_models.py --device
    cuda``; im Replay werden die ML-Module datenlimitiert kaum aufgerufen und
    Per-Tick-Inferenz ist die falsche Granularität fürs GPU-Batching. Der
    Replay bleibt daher korrekterweise CPU-gebunden.

    Behebbarer Overhead (verhaltens-erhaltend umgesetzt): M15 ``compute`` baute
    pro Tick mehrere Python-Listcomps über den (bis zu 100k großen)
    Liquidations-Buffer auf. Diese wurden auf einen einzigen vektorisierten
    ``np.fromiter`` + Boolean-Masken reduziert (bit-identische Ergebnisse,
    abgesichert durch ``test_replay_optimization_preserves_results`` /
    ``TestOptimizedComputeMatchesLegacy``).
"""
from __future__ import annotations

import csv
import logging
import sys
import time
from collections import Counter, deque
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Optional

import numpy as np

from bybit_edge._legacy_v1.backtester.engine import BacktestEngine, BacktestResult, Trade
from bybit_edge.config import (
    WF_EMBARGO_MINUTES,
    WF_TEST_DAYS,
    WF_TRAIN_DAYS,
)
from bybit_edge.persistence.db import PersistenceLayer
from bybit_edge._legacy_v1.state.liquidation_buffer import LiquidationBuffer, LiquidationEvent
from bybit_edge._legacy_v1.state.trade_buffer import TradeBuffer, TradeEvent
from bybit_edge._legacy_v1.strategies.strategy1_cascade import Strategy1CascadeDetector
from bybit_edge._legacy_v1.strategies.strategy2_entropy_momentum import Strategy2EntropyMomentum
from bybit_edge._legacy_v1.strategies.strategy3_pre_settlement import Strategy3PreSettlement
from bybit_edge._legacy_v1.strategies.strategy4_pattern_ensemble import Strategy4PatternEnsemble
from bybit_edge._legacy_v1.strategies.strategy5_cross_sectional import Strategy5CrossSectional

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

# Default cadence (in processed events) for the optional progress reporter, and
# the wall-clock floor between two emitted progress lines. Used by the CLIs
# which pass ``progress=True``; the ReplayBacktester default stays OFF so the
# unit tests / bit-identical guarantees are unaffected.
_DEFAULT_PROGRESS_EVERY_EVENTS: int = 250_000
_PROGRESS_MIN_WALL_SECONDS: float = 10.0


def _effective_ts_ms(kind: str, payload: dict[str, Any]) -> int:
    """Effective event-time (ms) used for the chronological merge sort.

    The persisted exchange ``ts`` is authoritative whenever it is positive.
    Only legacy ``ticker`` rows suffer the Bybit V5 envelope-ts bug (every
    such row lands with ``ts == 0`` because the collector dropped the
    envelope timestamp), so they fall back to the per-row reception
    wall-clock ``recv_ts`` (seconds → ms). ``recv_ts`` is monotone in stream
    order and ``>=`` the event's exchange time, so the lookahead guarantee is
    preserved. ``trade``/``liq``/``ob`` events always carry a real exchange
    ``ts`` (from the "T"/timestamp field) — they never need the fallback, so
    this returns their raw ``ts`` unchanged.

    Crucially: when ``ts > 0`` (fresh data, synthetic test streams) this
    returns the raw ``ts`` for every event type, so the merge sort is
    bit-identical to the legacy raw-``ts`` sort.
    """
    ts = int(payload.get("ts", payload.get("timestamp_ms", 0)) or 0)
    if ts > 0 or kind != "ticker":
        return ts
    recv = payload.get("recv_ts", 0.0)
    return int(float(recv) * 1000.0) if recv else 0


class _ProgressReporter:
    """Optional, strictly-observational progress reporter for a replay run.

    Emits a single ``logging.INFO`` line every ``every_events`` processed
    events OR every :data:`_PROGRESS_MIN_WALL_SECONDS` of wall-clock (whichever
    comes first, but never more than once per the wall-clock floor so a tight
    event cadence cannot spam the log), plus a final ``fertig in Xs`` line.

    It tracks how many pipeline ticks evaluated each strategy so the operator
    sees activity, mirroring the requested layout::

        [BTCUSDT] 1.250.000 / 4.547.724 Events (27%) | S3 evaluated 8200x |
        38s elapsed | ETA ~95s

    The reporter never reads or mutates the trade path; building one and calling
    its hooks is the only overhead, and it is only constructed when the caller
    asks for progress.
    """

    def __init__(
        self,
        symbol: str,
        total_events: int,
        every_events: int,
        logger_: logging.Logger,
        focus_strategy: str = "S3",
    ) -> None:
        self._symbol = symbol
        self._total = max(int(total_events), 0)
        self._every = max(int(every_events), 1)
        self._log = logger_
        self._focus = focus_strategy
        self._processed = 0
        self._focus_evals = 0
        self._t0 = time.perf_counter()
        self._last_emit_wall = self._t0
        self._last_emit_count = 0

    def on_event(self) -> None:
        """Count one processed event and maybe emit a progress line."""
        self._processed += 1
        if self._processed - self._last_emit_count < self._every:
            return
        now = time.perf_counter()
        if now - self._last_emit_wall < _PROGRESS_MIN_WALL_SECONDS:
            # Respect the wall-clock floor even when the event cadence is hit
            # often (e.g. tiny ``every_events`` on a fast stream).
            return
        self._emit(now)
        self._last_emit_wall = now
        self._last_emit_count = self._processed

    def on_pipeline_tick(self) -> None:
        """Count one pipeline tick where the focus strategy was evaluated."""
        self._focus_evals += 1

    def _emit(self, now: float) -> None:
        elapsed = now - self._t0
        pct = (self._processed / self._total * 100.0) if self._total else 0.0
        if self._processed > 0 and self._total > 0:
            eta = elapsed * (self._total - self._processed) / self._processed
            eta_str = f"ETA ~{eta:.0f}s"
        else:
            eta_str = "ETA ~?s"
        self._log.info(
            "[%s] %s / %s Events (%.0f%%) | %s evaluated %dx | %.0fs elapsed | %s",
            self._symbol,
            f"{self._processed:,}".replace(",", "."),
            f"{self._total:,}".replace(",", "."),
            pct,
            self._focus,
            self._focus_evals,
            elapsed,
            eta_str,
        )

    def finish(self) -> None:
        """Emit the terminal ``fertig in Xs`` line."""
        elapsed = time.perf_counter() - self._t0
        self._log.info(
            "[%s] fertig in %.1fs (%s Events, %s evaluated %dx)",
            self._symbol,
            elapsed,
            f"{self._processed:,}".replace(",", "."),
            self._focus,
            self._focus_evals,
        )


class ReplayBacktester:
    """Replays persisted DuckDB ticks through the real strategies.

    Each of the five strategies is run in isolation (its own instance) so
    that the per-strategy edge can be assessed independently. Entry/exit
    decisions are converted into round-trip :class:`Trade` objects and scored
    with :meth:`BacktestEngine.compute_metrics`.
    """

    def __init__(
        self,
        symbol: str,
        db_path: Optional[Path] = None,
        collect_diagnostics: bool = False,
        m15_refit_seconds: float = 0.0,
    ) -> None:
        self.symbol: str = symbol
        self._db_path: Optional[Path] = db_path

        # Opt-in M15 Omori curve_fit throttle. Default 0.0 (per-tick refit,
        # bit-identical to the live/legacy behaviour). When > 0 the
        # ReplayBacktester forwards it to every Strategy1's internal
        # ``M15GROmori`` instance — see :meth:`_build_strategies`. Live
        # behaviour is unchanged because the LiveRunner constructs Strategy1
        # directly (no override), so its M15 keeps ``refit_seconds=0.0``.
        self._m15_refit_seconds: float = float(m15_refit_seconds)

        # Diagnostics: when enabled, count per-strategy "reason"/"wait_reason"
        # occurrences plus S3-specific gate counters so the operator can see
        # *which* entry gate blocks. Strictly observational — the trade path is
        # never altered. When False (default) NO counter is ever touched, so the
        # replay is bit-identical to the pre-diagnostics behaviour and carries
        # zero per-tick overhead.
        self._collect_diagnostics: bool = bool(collect_diagnostics)
        # Per-strategy reason-counter: {sid: Counter[reason -> n]}.
        self._reason_counts: dict[str, Counter] = {}
        # S3-specific scalar gate counters (see _record_diagnostics).
        self._s3_counters: dict[str, int] = {}
        if self._collect_diagnostics:
            self._init_diagnostics()

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
        # Strategies dict from the most recent run / run_walkforward call.
        # Set inside ``run`` / ``run_walkforward`` after construction. Exposed
        # read-only via :meth:`get_strategy` so CLI drivers can flush
        # opt-in instrumentation (e.g. S1 rho samples) after the replay.
        self._last_strategies: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Event loading
    # ------------------------------------------------------------------

    def _open(self) -> PersistenceLayer:
        """Return an open persistence layer, creating one if necessary.

        The replay backtester is strictly read-only — it never writes back
        into the DuckDB it consumes. Opening the connection with
        ``read_only=True`` allows it to attach concurrently while the
        LiveRunner is writing into the same file (DuckDB serialises
        multi-process access via the read-only flag).

        If the connect still fails (e.g. on Windows where the writer can
        hold an exclusive OS-level lock that even read-only attaches
        cannot bypass) we surface a clear, actionable hint and exit with
        code 2 instead of dumping a raw ``IOException`` traceback on the
        operator.
        """
        if self.persist is None:
            try:
                self.persist = PersistenceLayer(
                    db_path=self._db_path, read_only=True
                )
            except Exception as exc:  # noqa: BLE001 — operator-facing hint
                msg = (
                    "\nKonnte DuckDB nicht read-only oeffnen "
                    f"({type(exc).__name__}: {exc}).\n"
                    "Auf Windows haelt der LiveRunner manchmal einen "
                    "exklusiven Lock — stoppe den LiveRunner kurz fuer den "
                    "Replay\nODER kopiere data/bybit_edge.duckdb in eine "
                    "Replay-Kopie\n"
                    "  (z.B. `copy data\\bybit_edge.duckdb "
                    "data\\bybit_edge_replay.duckdb`)\n"
                    "und nutze `--db-path data/bybit_edge_replay.duckdb`.\n"
                )
                print(msg, file=sys.stderr)
                sys.exit(2)
        return self.persist

    def load_events(
        self,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
    ) -> int:
        """Load tickers/trades/liquidations from DuckDB into a merged stream.

        The three tables are queried for *symbol* within the optional
        ``[start_ts, end_ts]`` (Unix milliseconds) window, tagged by kind, and
        merged into a single list sorted strictly ascending by EFFECTIVE
        event-time (:func:`_effective_ts_ms` — the raw exchange ``ts`` when it
        is positive, else the ``recv_ts`` fallback for legacy ts=0 ticker
        rows). This interleaves legacy ts=0 tickers chronologically with
        real-ts trades/liquidations instead of clumping them at the front of
        the stream. Ties are broken deterministically by kind so the ordering
        is stable.

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
            payload = {
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
            }
            events.append(
                (_effective_ts_ms("ticker", payload), "ticker", payload)
            )

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

        # Stable chronological sort by EFFECTIVE event-time. Each tuple's first
        # element is already ``_effective_ts_ms`` (raw ``ts`` when ``ts > 0``,
        # else the ``recv_ts``-fallback for legacy ts=0 tickers), so legacy
        # ts=0 tickers interleave with real-ts trades instead of clumping at
        # the front of the stream. Tie-break by a fixed kind order so that at
        # equal effective ts we deterministically ingest *data* events
        # (trade, liq) into their buffers before any *evaluating* event
        # (ticker) fires the pipeline tick that reads those buffers — this
        # preserves the documented invariant "events with ts <= t are already
        # ingested" for the tick evaluating at ts==t. ``ob`` lands last among
        # equal-ts events so that the depth profile observed at ts==T
        # reflects state after all other market events at T. Never a future
        # event before a past one.
        kind_order = {"trade": 0, "liq": 1, "ticker": 2, "ob": 3}
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
        recv_ts: Optional[float] = None,
    ) -> dict[str, Any]:
        """Build a ``ticker_data`` dict in the exact format the pipeline uses.

        Only data already ingested up to *now_ms* is used — strictly causal.
        When ``ob_snap`` is provided (the latest persisted L2 snapshot with
        ts <= now_ms) the depth profile arrays are taken from it; otherwise
        the order-book depth is reconstructed as a 1-level fallback from
        ``bid1``/``ask1``.

        ``recv_ts`` (seconds) is the reception wall-clock of the ticker row.
        When explicitly provided AND the persisted exchange ``ts`` of the
        ticker is non-positive (``snap["ts"] <= 0`` — see the envelope-ts
        bug documented in :meth:`_replay_events`), it is used as the
        event-time anchor for ``seconds_to_settlement``. This mirrors the
        fallback the throttle in :meth:`_replay_events` already uses, so
        the settlement-window detection stays consistent with the cadence.
        Defaults to ``None`` — the legacy behaviour (event-time = ``snap["ts"]``)
        is bit-identical when the caller does not pass it in.
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

        # Event-time anchor for the settlement countdown. When the persisted
        # exchange ``ts`` is missing/non-positive (Bybit V5 envelope-ts bug —
        # see :meth:`_replay_events`) the cadence already falls back to
        # ``recv_ts * 1000`` for the throttle. Mirror that fallback here so
        # ``seconds_to_settlement`` is consistent with the cadence and not
        # ~next_funding_time/1000 (≈ 1.7e9 s, well past any 30-min window),
        # which would silently gate every single replay tick "out of window".
        snap_ts: int = int(snap["ts"])
        if snap_ts > 0 or recv_ts is None:
            eff_ticker_ts_ms: int = snap_ts
        else:
            eff_ticker_ts_ms = int(recv_ts * 1000.0)
        seconds_to_settlement: float = self._seconds_to_settlement(
            snap["next_funding_time"], eff_ticker_ts_ms
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
                # Named so the diagnose mode shows the actual structural
                # blocker (cascade strategy starves without a liquidation
                # stream) instead of the "unknown" fallback at line ~826.
                return {
                    "action": "wait",
                    "direction": 0,
                    "strategy": "S1",
                    "reason": "liquidations_below_min_events",
                }
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
                ts=ts_seconds,
            )

        if strategy_id == "S4":
            price_series = ticker_data["price_series"]
            if len(price_series) <= 10:
                return {
                    "action": "wait",
                    "direction": 0,
                    "strategy": "S4",
                    "reason": "insufficient_price_history",
                }
            return strategy.on_data(
                price_series=price_series,
                library=None,
                current_price=price,
                ts=ts_seconds,
            )

        if strategy_id == "S5":
            # No multi-symbol panel is persisted, so S5 is never triggerable
            # in single-symbol replay. Kept for completeness / honesty.
            return {
                "action": "wait",
                "direction": 0,
                "strategy": "S5",
                "reason": "single_symbol_replay_unsupported",
            }

        return {
            "action": "wait",
            "direction": 0,
            "strategy": strategy_id,
            "reason": "strategy_not_evaluated",
        }

    # ------------------------------------------------------------------
    # Diagnostics (opt-in, strictly observational)
    # ------------------------------------------------------------------

    # The S3 entry gates are checked in a fixed order inside
    # Strategy3PreSettlement._check_entry. The returned "reason" string
    # therefore pinpoints the *first* gate that failed (or "all_conditions_met"
    # on a pass). Mapping each reason to how far the tick progressed through the
    # gate chain lets us reconstruct the per-gate pass counts without touching
    # the strategy: a reason past gate K implies gates 1..K all passed.
    #
    #   outside_settlement_window  -> failed gate 1 (window)
    #   pressure_below_q90         -> passed window; failed Q90
    #   pressure_zero              -> passed window+Q90; failed (pressure==0)
    #   basis_wrong_direction      -> passed window+Q90; failed basis
    #   bocpd_changepoint_detected -> passed window+Q90+basis; failed BOCPD
    #   all_conditions_met         -> passed everything (entry)
    _S3_REASON_PRESSURE_EXTREME: frozenset[str] = frozenset({
        "pressure_zero",
        "basis_wrong_direction",
        "bocpd_changepoint_detected",
        "all_conditions_met",
    })
    _S3_REASON_BASIS_ALIGNED: frozenset[str] = frozenset({
        "bocpd_changepoint_detected",
        "all_conditions_met",
    })

    def _init_diagnostics(self) -> None:
        """(Re)initialise the per-strategy diagnostic accumulators."""
        self._reason_counts = {
            sid: Counter() for sid in ("S1", "S2", "S3", "S4", "S5")
        }
        self._s3_counters = {
            "n_ticks_total": 0,
            "n_in_window": 0,
            "n_pressure_extreme": 0,
            "n_basis_aligned": 0,
            "n_all_gates_passed": 0,
        }

    def _record_diagnostics(
        self, strategy_id: str, signal: dict[str, Any]
    ) -> None:
        """Observe a strategy signal and update the diagnostic counters.

        Called once per strategy per evaluated pipeline tick *only* when
        ``collect_diagnostics`` is enabled. It never mutates ``signal`` nor any
        trade state — it merely reads the strategy's own return dict.

        Every tick at which the strategy did not return ``action == "enter"``
        increments the per-strategy reason counter by the signal's ``reason``
        value (fallback ``"unknown"`` when the strategy exposes no reason key,
        e.g. the gated-off neutral ``wait`` dicts from :meth:`_eval_strategy`).
        Ticks that *do* enter are counted under the ``__enter__`` sentinel so
        the enter/no-enter split is always recoverable.
        """
        action: str = signal.get("action", "wait")
        # All five strategies put their human-readable gate reason under
        # "reason" (verified against each strategy's return dict). The
        # gated-off neutral dicts built in _eval_strategy carry no reason key
        # -> "unknown" fallback as specified.
        reason: str = str(signal.get("reason", "unknown"))

        counter = self._reason_counts.get(strategy_id)
        if counter is not None:
            if action == "enter":
                counter["__enter__"] += 1
            else:
                counter[reason] += 1

        if strategy_id == "S3":
            self._record_s3_diagnostics(signal, action, reason)

    def _record_s3_diagnostics(
        self, signal: dict[str, Any], action: str, reason: str
    ) -> None:
        """Update S3-specific gate counters from its module sub-results.

        ``n_in_window`` is read directly from the embedded M22 sub-result
        (``modules["M22"]["in_window"]``), which M22 computes on *every* tick
        regardless of trade state. The remaining gate counters are inferred
        from the ordered ``reason`` chain (see ``_S3_REASON_*``); these only
        advance on ticks where the entry check actually ran (i.e. not while a
        position is open).
        """
        c = self._s3_counters
        c["n_ticks_total"] += 1

        modules = signal.get("modules")
        if isinstance(modules, dict):
            m22 = modules.get("M22")
            if isinstance(m22, dict) and m22.get("in_window"):
                c["n_in_window"] += 1

        if reason in self._S3_REASON_PRESSURE_EXTREME or action == "enter":
            c["n_pressure_extreme"] += 1
        if reason in self._S3_REASON_BASIS_ALIGNED or action == "enter":
            c["n_basis_aligned"] += 1
        if action == "enter":
            c["n_all_gates_passed"] += 1

    def get_diagnostics(self) -> dict[str, dict[str, Any]]:
        """Return the collected diagnostics, keyed by strategy id.

        Each strategy maps to ``{"reason_counts": {reason: n, ...}}``. The S3
        entry adds the scalar gate counters (``n_ticks_total``, ``n_in_window``,
        ``n_pressure_extreme``, ``n_basis_aligned``, ``n_all_gates_passed``).

        Returns an empty dict when ``collect_diagnostics`` was not enabled, so
        callers can cheaply test ``if bt.get_diagnostics():``.
        """
        if not self._collect_diagnostics:
            return {}
        out: dict[str, dict[str, Any]] = {}
        for sid, counter in self._reason_counts.items():
            entry: dict[str, Any] = {"reason_counts": dict(counter)}
            if sid == "S3":
                entry.update(self._s3_counters)
            out[sid] = entry
        return out

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------

    def run(
        self,
        pipeline_interval_seconds: float = 1.0,
        progress: bool = False,
        progress_every_events: int = 0,
    ) -> dict[str, BacktestResult]:
        """Replay the loaded events chronologically through every strategy.

        Events are ingested strictly in ``ts`` order. After ingesting an event
        the pipeline is (re-)evaluated at most once per
        ``pipeline_interval_seconds`` (throttled exactly like the LiveRunner).
        Each strategy keeps its own open position; an ``enter`` opens a
        position, an ``exit`` closes it into a round-trip :class:`Trade`.

        Parameters
        ----------
        pipeline_interval_seconds
            Pipeline throttle (matches the LiveRunner).
        progress
            When ``True`` a progress line is logged to the module logger
            (``logging.INFO``) every ``progress_every_events`` processed events
            (or at least every ~10 s of wall-clock), plus a final
            ``fertig in Xs`` line. Default ``False`` so the replay stays
            bit-identical and overhead-free for the unit tests; the CLIs flip
            it on. Progress reporting is strictly observational — it never
            touches the trade path.
        progress_every_events
            Event cadence for the progress line. ``0`` (default) means: use
            :data:`_DEFAULT_PROGRESS_EVERY_EVENTS` when ``progress`` is on, and
            stay silent otherwise.

        Returns
        -------
        dict[str, BacktestResult]
            One result per strategy id ("S1".."S5").
        """
        strategies: dict[str, Any] = self._build_strategies()
        for strat in strategies.values():
            strat.reset()
        # Make the post-run strategy instances reachable via get_strategy()
        # so CLI drivers can flush opt-in instrumentation after the replay.
        self._last_strategies = strategies

        # Per-strategy open position: {"side","entry_price","entry_ts"} or None.
        open_pos: dict[str, Optional[dict[str, Any]]] = {sid: None for sid in strategies}
        trades_out: dict[str, list[Trade]] = {sid: [] for sid in strategies}

        # Causal state engines built up incrementally from the event stream.
        trade_buffer = TradeBuffer(maxlen=2000)
        liq_buffer = LiquidationBuffer(maxlen=2000)
        price_history: deque[float] = deque(maxlen=_PRICE_HISTORY_MAXLEN)

        reporter = self._make_progress_reporter(
            progress=progress,
            progress_every_events=progress_every_events,
            total_events=len(self._events),
        )

        # Only forward ``progress_reporter`` when active (see _run_walkforward_
        # inner for the rationale — keeps the default override signature intact).
        extra: dict[str, Any] = (
            {"progress_reporter": reporter} if reporter is not None else {}
        )
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
            **extra,
        )
        if reporter is not None:
            reporter.finish()

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
                        strategy_id=sid,
                    )
                )
                open_pos[sid] = None

        return {
            sid: self.engine.compute_metrics(trades_out[sid]) for sid in strategies
        }

    # ------------------------------------------------------------------
    # Internal replay primitive — shared by run() and run_walkforward()
    # ------------------------------------------------------------------

    def _make_progress_reporter(
        self,
        progress: bool,
        progress_every_events: int,
        total_events: int,
    ) -> Optional[_ProgressReporter]:
        """Build a :class:`_ProgressReporter` when progress is requested.

        Returns ``None`` (the default) when neither ``progress`` is set nor a
        positive ``progress_every_events`` is given, so the hot loop carries no
        reporting overhead and stays bit-identical to the no-progress path.
        """
        every = progress_every_events
        if every <= 0:
            if not progress:
                return None
            every = _DEFAULT_PROGRESS_EVERY_EVENTS
        return _ProgressReporter(
            symbol=self.symbol,
            total_events=total_events,
            every_events=every,
            logger_=logger,
        )

    def get_strategy(self, sid: str) -> Optional[Any]:
        """Return the post-run strategy instance for ``sid``, or None.

        Read-only accessor exposed so CLI drivers can flush opt-in
        instrumentation (e.g. S1 rho-distribution sampling, T2) after the
        replay finishes. Returns None before any ``run`` / ``run_walkforward``
        call and for unknown strategy ids.
        """
        return self._last_strategies.get(sid)

    def _build_strategies(self) -> dict[str, Any]:
        """Construct one fresh instance per strategy id (mirrors live runner).

        When :attr:`_m15_refit_seconds` is positive the Strategy1 instance's
        internal ``M15GROmori`` is replaced with a throttled copy. The default
        ``0.0`` skips the replacement entirely — the returned Strategy1 is then
        byte-for-byte identical to ``Strategy1CascadeDetector()``, matching the
        LiveRunner.
        """
        s1 = Strategy1CascadeDetector()
        if self._m15_refit_seconds > 0.0:
            # Lazy import to keep the module-level imports unchanged.
            from bybit_edge._legacy_v1.layers.l4_pattern.m15_gr_omori import M15GROmori
            s1.m15 = M15GROmori(refit_seconds=self._m15_refit_seconds)
        return {
            "S1": s1,
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
        progress_reporter: Optional[_ProgressReporter] = None,
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

        # Tracks the effective event-time (see ``eff_ts_ms`` below) of the most
        # recent ticker the pipeline actually evaluated. Returned to the caller
        # so residual open positions are force-closed at a timestamp that is
        # consistent with the entry timestamps (which also use the effective
        # clock) — critical when the persisted exchange ``ts`` is 0 and the
        # cadence runs off ``recv_ts`` instead.
        last_eff_ts_ms: Optional[int] = None

        for ts_ms, kind, payload in events:
            if progress_reporter is not None:
                progress_reporter.on_event()
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

            # Effective event-time clock that drives the throttle / cadence.
            #
            # Bybit V5 ticker WS payloads carry the message timestamp on the
            # *envelope* (``payload["ts"]``), NOT inside the ticker ``data``
            # object that ``TickerSnapshot.from_ws`` parses — so every
            # persisted ticker row historically lands with ``ts == 0``. With a
            # constant ``ts`` the event-time throttle below fires exactly once
            # (the first tick), then ``eff_ts_ms - last_pipeline_ms`` is always
            # ``0 < interval_ms`` and the pipeline is never re-evaluated again —
            # the "1 tick over millions of events" bug.
            #
            # Fall back to the per-row ``recv_ts`` (reception wall-clock, in
            # seconds, always strictly increasing in stream order and persisted
            # alongside every ticker) whenever the exchange ``ts`` is missing /
            # non-positive. recv_ts >= the event's exchange time, so using it as
            # ``now_ms`` for the causal buffer windows can only ever include
            # already-ingested (past) events — the lookahead guarantee is
            # preserved. When ``ts`` *is* present and advancing (e.g. synthetic
            # test streams) this branch is never taken and behaviour is
            # bit-identical to before.
            if ts_ms > 0:
                eff_ts_ms = ts_ms
            else:
                eff_ts_ms = int(payload.get("recv_ts", 0.0) * 1000.0)

            # Throttle: re-evaluate the pipeline at most every interval.
            if eff_ts_ms - last_pipeline_ms < interval_ms:
                continue
            last_pipeline_ms = eff_ts_ms
            last_eff_ts_ms = eff_ts_ms
            if progress_reporter is not None:
                progress_reporter.on_pipeline_tick()

            ticker_data = self._build_ticker_data(
                snap=last_ticker,
                trade_buffer=trade_buffer,
                liq_buffer=liq_buffer,
                price_history=price_history,
                now_ms=eff_ts_ms,
                ob_snap=last_ob_snap,
                recv_ts=float(last_ticker.get("recv_ts", 0.0)) or None,
            )
            ts_seconds = eff_ts_ms / 1000.0
            price = float(ticker_data["last_price"])

            for sid, strat in strategies.items():
                signal = self._eval_strategy(sid, strat, ticker_data, ts_seconds)
                if self._collect_diagnostics:
                    # Strictly observational — never alters the trade path.
                    self._record_diagnostics(sid, signal)
                self._apply_signal(
                    strategy_id=sid,
                    signal=signal,
                    price=price,
                    ts_ms=eff_ts_ms,
                    open_pos=open_pos,
                    trades_out=trades_out,
                    record_trades=record_trades,
                )

        # Prefer the effective time of the last evaluated ticker so the
        # caller's force-close stays consistent with the entry timestamps.
        # When no ticker fired (e.g. trade-only slice) fall back to the raw ts
        # of the final event, preserving the previous return contract.
        last_ts_ms: Optional[int] = (
            last_eff_ts_ms
            if last_eff_ts_ms is not None
            else (events[-1][0] if events else None)
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
        progress: bool = False,
        progress_every_events: int = 0,
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
            :class:`bybit_edge._legacy_v1.tuning.ParameterContext` for the entire
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
            from bybit_edge._legacy_v1.tuning.params import ParameterContext
            ctx: Any = ParameterContext(param_overrides)
        else:
            ctx = nullcontext()

        reporter = self._make_progress_reporter(
            progress=progress,
            progress_every_events=progress_every_events,
            total_events=len(self._events),
        )
        with ctx:
            results = self._run_walkforward_inner(
                pipeline_interval_seconds=pipeline_interval_seconds,
                train_days=train_days,
                test_days=test_days,
                embargo_minutes=embargo_minutes,
                min_train_events=min_train_events,
                progress_reporter=reporter,
            )
        if reporter is not None:
            reporter.finish()
        return results

    def _run_walkforward_inner(
        self,
        pipeline_interval_seconds: float,
        train_days: int,
        test_days: int,
        embargo_minutes: int,
        min_train_events: int,
        progress_reporter: Optional[_ProgressReporter] = None,
    ) -> dict[str, BacktestResult]:
        """Body of :meth:`run_walkforward` — executes the fold sweep.

        Extracted so that :meth:`run_walkforward` can optionally enter a
        :class:`bybit_edge._legacy_v1.tuning.ParameterContext` around the entire sweep
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
            # Track the latest fold's strategies so post-run flush hooks
            # (e.g. dump_rho_distribution) see the most recent state.
            self._last_strategies = strategies

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
            # to keep, not the in-flight position. Critically, the strategy
            # objects' OWN internal ``_in_trade``/entry bookkeeping must be
            # cleared here too, not just the backtester's ``open_pos``
            # mirror: otherwise a strategy that was still holding a
            # position at end-of-train enters TEST believing it is already
            # in a trade, evaluates only exit (not entry) conditions until
            # its stale TRAIN-era exit eventually fires, and by then
            # ``open_pos[sid]`` is already None so even that exit is
            # silently dropped — desyncing backtester and strategy state
            # and unpredictably suppressing trades/Sharpe for the fold.
            # ``reset_position_state()`` clears only the in-flight-position
            # fields (mirroring each strategy's own exit-branch), leaving
            # the warmed-up model state (Hawkes/HMM/entropy history/etc.)
            # that TRAIN exists to build fully intact.
            for sid, strat in strategies.items():
                open_pos[sid] = None
                reset_position_state = getattr(
                    strat, "reset_position_state", None
                )
                if reset_position_state is not None:
                    reset_position_state()
                else:
                    # Defensive fallback for any strategy implementation
                    # that has not (yet) grown a dedicated
                    # ``reset_position_state`` method.
                    if hasattr(strat, "_in_trade"):
                        strat._in_trade = False

            # 2) EMBARGO — events in [train_end, test_start) are NOT replayed.
            # Strategy state stays exactly as it was at end-of-train.

            # 3) TEST phase — count trades into the fold accumulator.
            test_trades_fold: dict[str, list[Trade]] = {
                sid: [] for sid in strategies
            }
            # Only forward ``progress_reporter`` when one is active. Keeping the
            # default call signature otherwise identical preserves compatibility
            # with subclasses/tests that override ``_replay_events`` with the
            # pre-progress signature.
            extra: dict[str, Any] = (
                {"progress_reporter": progress_reporter}
                if progress_reporter is not None
                else {}
            )
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
                **extra,
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
                            strategy_id=sid,
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
                        strategy_id=strategy_id,
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
        strategy_id: str = "",
    ) -> Trade:
        """Build a fee/slippage-aware round-trip :class:`Trade` (qty=1.0).

        Iter-4 Push A T3: when ``strategy_id == "S2"`` and the opt-in flag
        ``config.S2_MAKER_ONLY`` is True, both legs are charged 0.0 fees
        (worst-case-for-our-hypothesis vs. the ~-2.5 bps Bybit maker
        rebate — if S2 still loses with zero fees it would still lose
        with rebates). S3 (and every other strategy) is unaffected; this
        is strictly an S2 forensic flag. Default off -> bit-identical.
        """
        qty = 1.0
        slip_entry = self.engine._slipped_price(entry_price, side)
        exit_side = "Short" if side == "Long" else "Long"
        slip_exit = self.engine._slipped_price(exit_price, exit_side)

        from bybit_edge import config as _cfg
        if strategy_id == "S2" and _cfg.S2_MAKER_ONLY:
            entry_fee = 0.0
            exit_fee = 0.0
        else:
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
            raw_pnl=raw_pnl,
            entry_fee=entry_fee,
            exit_fee=exit_fee,
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

    # Stable column order for the per-trade CSV export. Kept as a class-level
    # constant so both drivers (and the aggregated trades_all.csv) emit the
    # same header.
    _TRADE_CSV_COLUMNS: tuple[str, ...] = (
        "symbol",
        "strategy",
        "entry_ts",
        "exit_ts",
        "side",
        "entry_price",
        "exit_price",
        "quantity",
        "raw_pnl",
        "entry_fee",
        "exit_fee",
        "pnl_net",
        "pnl_bps",
    )

    @staticmethod
    def export_trades_csv(
        trades_by_strategy: dict[str, list[Trade]],
        path: Path,
        symbol: str,
        mode: str,
    ) -> Path:
        """Write a per-(symbol, mode) trade CSV using :mod:`csv` (stdlib only).

        Emits one row per :class:`Trade` across all strategies, columns are
        :attr:`_TRADE_CSV_COLUMNS`. Float fields use ``repr()`` to preserve
        full precision; timestamps are written as integer ms; the ``side``
        and ``strategy`` strings are written unquoted unless the underlying
        :mod:`csv` writer decides quoting is required (commas / quotes).

        The caller is responsible for creating ``path`` 's parent directory.
        Returns the resolved output path (``path / f"trades_{symbol}_{mode}.csv"``).
        Bit-identity guarantee: this function is only invoked when the
        opt-in ``--export-trades`` flag is set on the driver CLI; no replay
        code path calls it implicitly.
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        out_path = path / f"trades_{symbol}_{mode}.csv"
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(ReplayBacktester._TRADE_CSV_COLUMNS)
            for sid in sorted(trades_by_strategy.keys()):
                for tr in trades_by_strategy[sid]:
                    writer.writerow(
                        ReplayBacktester._trade_to_csv_row(tr, sid)
                    )
        return out_path

    @staticmethod
    def _trade_to_csv_row(trade: Trade, strategy_id: str) -> list[str]:
        """Render a single :class:`Trade` as a list of strings for csv.writer.

        Floats use ``repr()`` so the round-trip is lossless; ints (timestamps,
        strategy id, side) pass through as their natural representations.
        """
        return [
            str(trade.symbol),
            str(strategy_id),
            str(int(trade.entry_ts)),
            str(int(trade.exit_ts)),
            str(trade.side),
            repr(float(trade.entry_price)),
            repr(float(trade.exit_price)),
            repr(float(trade.quantity)),
            repr(float(trade.raw_pnl)),
            repr(float(trade.entry_fee)),
            repr(float(trade.exit_fee)),
            repr(float(trade.pnl)),
            repr(float(trade.pnl_bps)),
        ]

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
