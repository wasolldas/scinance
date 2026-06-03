"""
Live-Runner — verbindet WebSocket-Collector, State-Engines, Pipeline und
Executor zu einem lauffähigen System.

Datenfluss::

    Bybit WS  ->  State-Engines  ->  (alle PIPELINE_INTERVAL_SECONDS)
              ->  Pipeline.process_ticker  ->  Decision  ->  Executor

Sicherheit:
    - Orders werden nur gesendet wenn EXECUTION_ENABLED=true.
    - Im LIVE-Modus (weder Demo noch Testnet) verweigert der Executor Orders.
    - Ohne Execution läuft alles read-only und loggt nur die Entscheidungen.
"""
from __future__ import annotations

import asyncio
import csv
import json
import logging
import time
from collections import deque
from pathlib import Path
from typing import Any, Optional

import numpy as np

from bybit_edge.collector.ws_collector import BybitWSCollector, WSMessage
from bybit_edge.config import (
    BYBIT_DEMO,
    BYBIT_TESTNET,
    DASHBOARD_SNAPSHOT_DIR,
    DATA_DIR,
    ENABLE_HEARTBEAT_FILE,
    EXECUTION_ENABLED,
    EXECUTION_LEVERAGE,
    EXECUTION_ORDER_USD,
    PERSIST_ENABLED,
    PERSIST_FLUSH_SECONDS,
    PERSIST_ORDERBOOK,
    PERSIST_ORDERBOOK_DEPTH,
    PERSIST_ORDERBOOK_SNAPSHOT_SECONDS,
    PIPELINE_INTERVAL_SECONDS,
    PRIMARY_SYMBOL,
    RISK_BUDGET_ENABLED,
    RISK_BUDGET_RESET,
    RISK_DAILY_LOSS_PCT,
    RISK_EQUITY_POLL_SECONDS,
    RISK_MAX_DRAWDOWN_PCT,
    RISK_STATE_PATH,
    RISK_VOL_LOOKBACK_BARS,
    RISK_VOL_SCALING_ENABLED,
    RISK_VOL_TARGET_BPS,
)
from bybit_edge.execution.bybit_executor import BybitExecutor
from bybit_edge.persistence.db import PersistenceLayer
from bybit_edge.pipeline import Pipeline
from bybit_edge.risk import RiskBudget
from bybit_edge.state.liquidation_buffer import LiquidationBuffer, LiquidationEvent
from bybit_edge.state.orderbook_state import OrderbookState
from bybit_edge.state.ticker_state import TickerSnapshot
from bybit_edge.state.trade_buffer import TradeBuffer, TradeEvent

logger = logging.getLogger(__name__)


class LiveRunner:
    """Orchestriert Datenerfassung, Pipeline und Order-Ausführung."""

    def __init__(
        self,
        symbol: str = PRIMARY_SYMBOL,
        shared_persist: Optional[PersistenceLayer] = None,
        execution_override: Optional[bool] = None,
    ) -> None:
        self.symbol = symbol

        # State-Engines
        self.orderbook = OrderbookState(symbol)
        self.liq_buffer = LiquidationBuffer(maxlen=2000)
        self.trade_buffer = TradeBuffer(maxlen=2000)
        self.price_history: deque[float] = deque(maxlen=512)

        # Roher Ticker-Merge-State (Bybit sendet Deltas)
        self._raw_ticker: dict[str, Any] = {"symbol": symbol}
        self.ticker: Optional[TickerSnapshot] = None

        # Pipeline + Collector + Executor
        self.pipeline = Pipeline(symbol)
        self.collector = BybitWSCollector(symbol)
        self.executor: Optional[BybitExecutor] = None

        # Risiko-Budget (opt-in via RISK_BUDGET_ENABLED).
        self.risk_budget: Optional[RiskBudget] = None
        if RISK_BUDGET_ENABLED:
            self.risk_budget = RiskBudget(
                daily_loss_pct=RISK_DAILY_LOSS_PCT,
                max_dd_pct=RISK_MAX_DRAWDOWN_PCT,
                vol_scaling_enabled=RISK_VOL_SCALING_ENABLED,
                vol_target_bps=RISK_VOL_TARGET_BPS,
                state_path=RISK_STATE_PATH,
                vol_lookback_bars=RISK_VOL_LOOKBACK_BARS,
                logger=logger,
            )

        # Optional vom MultiSymbolRunner injizierte Persistenz-Schicht.
        # Falls gesetzt, übernimmt sie KEINE Ownership (kein close in stop()).
        self._shared_persist: Optional[PersistenceLayer] = shared_persist
        self._owns_persist: bool = shared_persist is None
        # Execution-Override: True = erzwingen, False = unterdrücken,
        # None = Default-Verhalten (EXECUTION_ENABLED-Config greift).
        self._execution_override: Optional[bool] = execution_override

        # Persistenz (optional): Puffer + DuckDB-Schicht
        self.persist: Optional[PersistenceLayer] = None
        self._buf_tickers: list[TickerSnapshot] = []
        self._buf_trades: list[TradeEvent] = []
        self._buf_liqs: list[LiquidationEvent] = []
        # L2-Orderbook-Snapshots (Opt-in via PERSIST_ORDERBOOK).
        self._buf_orderbook_snaps: list[dict[str, Any]] = []
        self._last_ob_snap_ts: float = 0.0
        self._persisted = 0
        self._ob_snaps_persisted = 0

        # Positions-Tracking ("", "Buy", "Sell")
        self._position_side: str = ""
        self._last_pipeline_ts: float = 0.0
        self._running = False
        self._msg_count = 0

        # Trade-Journal (CSV) für spätere Strategie-Auswertung
        self._journal_path: Path = DATA_DIR / "trades_journal.csv"
        self._journal_fields = [
            "ts_iso", "ts_unix", "symbol", "strategy_id", "action",
            "side", "qty", "price", "confidence", "ret_code", "order_id",
        ]

        self._register_handlers()

    def _journal(self, row: dict[str, Any]) -> None:
        """Hängt eine Order-Zeile an das Trade-Journal an (CSV)."""
        try:
            self._journal_path.parent.mkdir(parents=True, exist_ok=True)
            write_header = not self._journal_path.exists()
            with self._journal_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._journal_fields)
                if write_header:
                    writer.writeheader()
                writer.writerow({k: row.get(k, "") for k in self._journal_fields})
        except Exception:
            logger.exception("Trade-Journal konnte nicht geschrieben werden")

    # ------------------------------------------------------------------
    # Handler-Registrierung
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        self.collector.add_handler("tickers", self._on_ticker)
        self.collector.add_handler("orderbook50", self._on_orderbook)
        self.collector.add_handler("trades", self._on_trade)
        self.collector.add_handler("liquidation", self._on_liquidation)

    def _on_ticker(self, msg: WSMessage) -> None:
        # Delta-Merge: nur vorhandene Felder überschreiben
        self._raw_ticker.update(msg.data)
        self._raw_ticker["symbol"] = self.symbol
        self.ticker = TickerSnapshot.from_ws(self._raw_ticker, recv_ts=msg.recv_ts)
        self._msg_count += 1
        if self.persist is not None and self.ticker.last_price > 0:
            self._buf_tickers.append(self.ticker)

    def _on_orderbook(self, msg: WSMessage) -> None:
        if msg.msg_type == "snapshot":
            self.orderbook.apply_snapshot(msg.data)
        else:
            self.orderbook.apply_delta(msg.data)
        # Optionale L2-Persistenz: erst nach apply_*, damit die Snapshot-Tiefe
        # konsistent ist. Strikt opt-in (PERSIST_ORDERBOOK=false → kein I/O,
        # kein Buffer-Wachstum). Wir throttlen via PERSIST_ORDERBOOK_SNAPSHOT_
        # SECONDS, sodass aus den ~20-ms-Deltas ~1 Snapshot/s wird (PRD-Schätzung
        # 500 MB/Tag pro Symbol für volle Deltas → ~5-15 MB/Tag pro Symbol mit
        # Snapshot-Modus + ZSTD-Parquet-Archivierung).
        if self.persist is None or not PERSIST_ORDERBOOK:
            return
        recv_ts = float(msg.recv_ts)
        if (recv_ts - self._last_ob_snap_ts) < PERSIST_ORDERBOOK_SNAPSHOT_SECONDS:
            return
        depth = int(PERSIST_ORDERBOOK_DEPTH)
        (bid_p, bid_s), (ask_p, ask_s) = self.orderbook.top_n_arrays(depth)
        if bid_p.size == 0 and ask_p.size == 0:
            return
        self._last_ob_snap_ts = recv_ts
        self._buf_orderbook_snaps.append({
            "ts": int(recv_ts * 1000),
            "symbol": self.symbol,
            "bid_prices": bid_p,
            "bid_sizes": bid_s,
            "ask_prices": ask_p,
            "ask_sizes": ask_s,
            "recv_ts": recv_ts,
            "depth": depth,
        })

    def _on_trade(self, msg: WSMessage) -> None:
        evt = TradeEvent.from_ws(msg.data)
        self.trade_buffer.add(evt)
        if evt.price > 0:
            self.price_history.append(evt.price)
        if self.persist is not None:
            self._buf_trades.append(evt)

    def _on_liquidation(self, msg: WSMessage) -> None:
        evt = LiquidationEvent.from_ws(msg.data)
        self.liq_buffer.add(evt)
        if self.persist is not None:
            self._buf_liqs.append(evt)
        logger.info(
            "LIQUIDATION: %s %.4f @ %.2f (%.0f USD)",
            evt.side, evt.volume, evt.price, evt.usd_value,
        )

    # ------------------------------------------------------------------
    # Pipeline-Eingabe bauen
    # ------------------------------------------------------------------

    def _build_ticker_data(self) -> Optional[dict[str, Any]]:
        if self.ticker is None or self.ticker.last_price <= 0:
            return None

        snap = self.ticker
        (bid_p, bid_s), (ask_p, ask_s) = self.orderbook.top_n_arrays(20)

        # seconds_to_settlement absichern (next_funding_time kann 0/fehlen)
        if snap.next_funding_time > 0:
            seconds_to_settlement = max(snap.seconds_to_funding, 0.0)
        else:
            seconds_to_settlement = 3600.0

        # Liquidations-Events der letzten Stunde als Dicts
        liq_events = [
            {"timestamp_ms": e.timestamp_ms, "usd_value": e.usd_value, "side": e.side}
            for e in self.liq_buffer.recent_by_ts(3600.0)
        ]

        # Trades für Kyle's Lambda
        trade_events = self.trade_buffer.recent_events(100)
        trades = [
            {
                "price": t.price,
                "volume": t.volume,
                "side": t.side,
                "timestamp_ms": t.timestamp_ms,
            }
            for t in trade_events
        ]

        # Event-Zeiten (Sekunden) für Hawkes
        ts_ms = self.trade_buffer.recent_timestamps(200)
        event_times = ts_ms / 1000.0 if ts_ms.size else np.array([], dtype=np.float64)

        price_series = np.array(self.price_history, dtype=np.float64)

        return {
            "ts": time.time(),
            "last_price": snap.last_price,
            "mark_price": snap.mark_price or snap.last_price,
            "index_price": snap.index_price or snap.last_price,
            "premium_index": snap.premium_index,
            "funding_rate": snap.funding_rate,
            "open_interest": snap.open_interest,
            "seconds_to_settlement": seconds_to_settlement,
            "bid_sizes": bid_s if bid_s.size else np.ones(20),
            "ask_sizes": ask_s if ask_s.size else np.ones(20),
            "best_bid": self.orderbook.best_bid,
            "best_ask": self.orderbook.best_ask,
            "liq_events": liq_events,
            "event_times": event_times,
            "trades": trades,
            "price_series": price_series,
        }

    # ------------------------------------------------------------------
    # Entscheidung ausführen
    # ------------------------------------------------------------------

    async def _act_on_decision(self, decision: dict[str, Any]) -> None:
        action = decision.get("action", "wait")
        strat = decision.get("strategy_id", "?")
        size_pct = decision.get("position_size_pct", 0.0)
        conf = decision.get("confidence", 0.0)

        logger.info(
            "SIGNAL [%s] action=%s dir=%s size=%.4f conf=%.3f",
            strat, action, decision.get("direction", 0), size_pct, conf,
        )

        if not self._execution_active() or self.executor is None:
            logger.info("  -> (read-only, keine Order gesendet)")
            return

        price = self.ticker.last_price if self.ticker else 0.0
        if price <= 0:
            return

        if action in ("long", "short"):
            target_side = "Buy" if action == "long" else "Sell"
            if self._position_side == target_side:
                logger.info("  -> Position bereits %s, halte.", target_side)
                return

            # Risiko-Budget: Max-DD -> Position schließen, kein neuer Entry.
            if self.risk_budget is not None and self.risk_budget.should_force_close():
                if self._position_side:
                    logger.warning(
                        "RISK FORCE-CLOSE: max drawdown — schließe %s.",
                        self._position_side,
                    )
                    await self.executor.close_position()
                    self._position_side = ""
                self._journal({
                    "ts_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "ts_unix": time.time(),
                    "symbol": self.symbol,
                    "strategy_id": strat,
                    "action": "risk_block",
                    "side": target_side,
                    "qty": "",
                    "price": price,
                    "confidence": conf,
                    "ret_code": -1,
                    "order_id": "",
                })
                return

            # Gegenposition schließen
            if self._position_side:
                await self.executor.close_position()
                self._position_side = ""
            # Order-Größe aus Notional
            raw_qty = EXECUTION_ORDER_USD / price
            # Vol-Scaling (opt-in) vor dem qty-Rounding anwenden.
            if self.risk_budget is not None:
                raw_qty = self.risk_budget.adjust_qty(
                    raw_qty, list(self.price_history)
                )
            qty = self.executor.round_qty(raw_qty)
            if qty <= 0:
                logger.warning("  -> qty zu klein (Notional %s USD), übersprungen.", EXECUTION_ORDER_USD)
                return

            # Risiko-Budget: Entry-Check (Daily-Loss / Max-DD).
            if self.risk_budget is not None:
                allowed, reason = self.risk_budget.check_entry_allowed(qty)
                if not allowed:
                    logger.warning("RISK BLOCK: %s — Order übersprungen.", reason)
                    self._journal({
                        "ts_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "ts_unix": time.time(),
                        "symbol": self.symbol,
                        "strategy_id": strat,
                        "action": "risk_block",
                        "side": target_side,
                        "qty": qty,
                        "price": price,
                        "confidence": conf,
                        "ret_code": -1,
                        "order_id": reason,
                    })
                    return

            result = await self.executor.place_market_order(target_side, qty)
            self._journal({
                "ts_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
                "ts_unix": time.time(),
                "symbol": self.symbol,
                "strategy_id": strat,
                "action": action,
                "side": target_side,
                "qty": qty,
                "price": price,
                "confidence": conf,
                "ret_code": result.get("retCode"),
                "order_id": result.get("result", {}).get("orderId", ""),
            })
            if result.get("retCode") == 0:
                self._position_side = target_side

        elif action == "exit":
            if self._position_side:
                result = await self.executor.close_position()
                self._journal({
                    "ts_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "ts_unix": time.time(),
                    "symbol": self.symbol,
                    "strategy_id": strat,
                    "action": "exit",
                    "side": "",
                    "qty": "",
                    "price": price,
                    "confidence": conf,
                    "ret_code": result.get("retCode"),
                    "order_id": result.get("result", {}).get("orderId", ""),
                })
                self._position_side = ""

    # ------------------------------------------------------------------
    # Hauptschleife
    # ------------------------------------------------------------------

    async def _pipeline_loop(self) -> None:
        while self._running:
            await asyncio.sleep(PIPELINE_INTERVAL_SECONDS)
            try:
                ticker_data = self._build_ticker_data()
                if ticker_data is None:
                    continue
                decision = await self.pipeline.process_ticker(ticker_data)
                if decision is not None:
                    await self._act_on_decision(decision)
            except Exception:
                logger.exception("Fehler im Pipeline-Loop")

    def _flush_persist(self) -> None:
        """Schreibt die gepufferten Ticks gebündelt in DuckDB."""
        if self.persist is None:
            return
        t, tr, lq = self._buf_tickers, self._buf_trades, self._buf_liqs
        ob = self._buf_orderbook_snaps
        self._buf_tickers, self._buf_trades, self._buf_liqs = [], [], []
        self._buf_orderbook_snaps = []
        try:
            n = 0
            n += self.persist.write_tickers_batch(t)
            n += self.persist.write_trades_batch(tr, symbol=self.symbol)
            n += self.persist.write_liquidations_batch(lq)
            self._persisted += n
            if ob:
                # write_orderbook_snapshots_batch returns row count (depth*2 per snap).
                self.persist.write_orderbook_snapshots_batch(ob)
                self._ob_snaps_persisted += len(ob)
        except Exception:
            logger.exception("Persist-Flush fehlgeschlagen")
        # Dashboard-Snapshots im Anschluss schreiben — strikt getrennt vom
        # Hauptflush, damit ein Snapshot-Fehler die DuckDB-Writes nicht
        # zerstört. DuckDB hält ein Lock auf die DB-Datei; das Dashboard
        # kann daher NICHT parallel read-only verbinden. Stattdessen liest
        # es diese Parquet-Snapshots.
        self._export_dashboard_snapshots()

    def _export_dashboard_snapshots(self) -> None:
        """Exportiert kompakte Dashboard-Snapshots als Parquet.

        Nutzt die bestehende ``self.persist.conn`` (kein zweiter Connect,
        kein Lock-Konflikt) und schreibt drei Dateien nach
        ``DASHBOARD_SNAPSHOT_DIR``:

        - ``row_counts.parquet`` — eine Zeile pro Tabelle (table_name, count, exported_at)
        - ``liquidations_recent.parquet`` — letzte 200 Liquidationen (alle Symbole)
        - ``coverage.parquet`` — min_ts/max_ts/count pro Tabelle

        Fehler werden geloggt, aber NIE weitergereicht — ein temporäres
        File-Lock unter Windows darf den Persist-Flush nicht abreissen.
        """
        if self.persist is None:
            return
        conn = getattr(self.persist, "conn", None)
        if conn is None:
            return
        try:
            DASHBOARD_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.exception("Snapshot-Verzeichnis konnte nicht erstellt werden.")
            return

        tables = (
            "tickers", "trades", "liquidations", "kline_1min",
            "orderbook_snapshots",
            "open_interest", "long_short_ratio", "funding_history",
        )

        # 1) row_counts.parquet
        try:
            union_parts = [
                f"SELECT '{tbl}' AS table_name, "
                f"COUNT(*)::BIGINT AS row_count, "
                f"CURRENT_TIMESTAMP AS exported_at "
                f"FROM {tbl}"
                for tbl in tables
            ]
            select_sql = " UNION ALL ".join(union_parts)
            out_path = DASHBOARD_SNAPSHOT_DIR / "row_counts.parquet"
            conn.execute(
                f"COPY ({select_sql}) TO '{out_path.as_posix()}' (FORMAT PARQUET)"
            )
        except Exception:
            logger.warning("Snapshot row_counts.parquet konnte nicht geschrieben werden.",
                           exc_info=True)

        # 2) liquidations_recent.parquet — letzte 200 Liquidationen
        try:
            out_path = DASHBOARD_SNAPSHOT_DIR / "liquidations_recent.parquet"
            conn.execute(
                f"""
                COPY (
                    SELECT ts, symbol, side, volume, price, usd_value
                    FROM liquidations
                    ORDER BY ts DESC
                    LIMIT 200
                ) TO '{out_path.as_posix()}' (FORMAT PARQUET)
                """
            )
        except Exception:
            logger.warning("Snapshot liquidations_recent.parquet konnte nicht geschrieben werden.",
                           exc_info=True)

        # 3) coverage.parquet — min_ts/max_ts/count pro Tabelle
        try:
            cov_parts = [
                f"SELECT '{tbl}' AS table_name, "
                f"MIN(ts) AS min_ts, MAX(ts) AS max_ts, "
                f"COUNT(*)::BIGINT AS row_count "
                f"FROM {tbl}"
                for tbl in tables
            ]
            cov_sql = " UNION ALL ".join(cov_parts)
            out_path = DASHBOARD_SNAPSHOT_DIR / "coverage.parquet"
            conn.execute(
                f"COPY ({cov_sql}) TO '{out_path.as_posix()}' (FORMAT PARQUET)"
            )
        except Exception:
            logger.warning("Snapshot coverage.parquet konnte nicht geschrieben werden.",
                           exc_info=True)

    async def _persist_loop(self) -> None:
        while self._running:
            await asyncio.sleep(PERSIST_FLUSH_SECONDS)
            self._flush_persist()

    async def _risk_loop(self) -> None:
        """Periodisch Equity abfragen und Risiko-Budget aktualisieren."""
        if self.risk_budget is None or self.executor is None:
            return
        while self._running:
            await asyncio.sleep(RISK_EQUITY_POLL_SECONDS)
            try:
                equity = await self.executor.get_equity()
                if equity > 0:
                    # Recovery-Check zuerst, damit ein neuer Tag die Sperre löst.
                    self.risk_budget.reset_if_recovered(equity)
                    self.risk_budget.on_equity_update(equity)
            except Exception:
                logger.exception("Fehler im Risk-Loop")

    async def _heartbeat_loop(self) -> None:
        while self._running:
            await asyncio.sleep(30.0)
            mid = self.orderbook.mid_price
            px = self.ticker.last_price if self.ticker else 0.0
            if self.persist is not None:
                ob_pending = len(self._buf_orderbook_snaps)
                extra = (
                    f" persisted={self._persisted}"
                    f" ob={self._ob_snaps_persisted + ob_pending}"
                )
            else:
                extra = ""
            logger.info(
                "HEARTBEAT: msgs=%d last=%.2f mid=%.2f trades=%d liqs=%d pos=%s%s",
                self._msg_count, px, mid,
                len(self.trade_buffer), len(self.liq_buffer),
                self._position_side or "flat", extra,
            )

            if ENABLE_HEARTBEAT_FILE:
                self._write_heartbeat_file(px=px, mid=mid)

    def _write_heartbeat_file(self, px: float, mid: float) -> None:
        """Schreibt JSON-Heartbeat in DATA_DIR/dashboard_state.json.

        Wird vom Streamlit-Dashboard im Tab "Pipeline-Stats" gelesen.
        Fehler werden geloggt, aber niemals weitergereicht.
        """
        mode = "DEMO" if BYBIT_DEMO else "TESTNET" if BYBIT_TESTNET else "LIVE"
        payload = {
            "ts": time.time(),
            "symbol": self.symbol,
            "msgs": int(self._msg_count),
            "last_price": float(px),
            "mid_price": float(mid),
            "trade_buffer_len": len(self.trade_buffer),
            "liq_buffer_len": len(self.liq_buffer),
            "persisted": int(self._persisted),
            "position_side": self._position_side or "",
            "mode": mode,
        }
        try:
            path = DATA_DIR / "dashboard_state.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(payload, f)
            tmp.replace(path)
        except Exception:
            logger.exception("Heartbeat-File konnte nicht geschrieben werden.")

    def _execution_active(self) -> bool:
        """Effektive Execution-Entscheidung: Override schlägt Config-Default."""
        if self._execution_override is None:
            return bool(EXECUTION_ENABLED)
        return bool(self._execution_override)

    async def run(self) -> None:
        """Startet Collector, Pipeline-Loop und (optional) Executor."""
        mode = "DEMO" if BYBIT_DEMO else "TESTNET" if BYBIT_TESTNET else "LIVE"
        exec_active = self._execution_active()
        logger.info("LiveRunner startet — Symbol=%s Modus=%s Execution=%s",
                    self.symbol, mode, exec_active)

        self._running = True

        if self._shared_persist is not None:
            # Geteilte Persistenz vom MultiSymbolRunner: nicht selbst öffnen,
            # nicht selbst schließen.
            self.persist = self._shared_persist
        elif PERSIST_ENABLED:
            try:
                self.persist = PersistenceLayer()
                logger.info("Persistenz aktiv -> DuckDB (Tickers/Trades/Liquidationen)")
            except Exception:
                logger.exception("Persistenz-Init fehlgeschlagen — laufe ohne weiter.")
                self.persist = None

        if exec_active:
            self.executor = BybitExecutor(self.symbol)
            await self.executor.load_instrument()
            try:
                await self.executor.set_leverage(EXECUTION_LEVERAGE)
                equity = await self.executor.get_equity()
                logger.info("Account-Equity: %.2f USDT", equity)
                pos = await self.executor.get_position()
                self._position_side = pos["side"]
                if pos["size"] > 0:
                    logger.info("Bestehende Position: %s %.4f", pos["side"], pos["size"])
                if self.risk_budget is not None:
                    self.risk_budget.load(equity)
                    if RISK_BUDGET_RESET:
                        self.risk_budget.manual_reset(equity)
                    self.risk_budget.on_equity_update(equity)
            except Exception:
                logger.exception("Executor-Init fehlgeschlagen — laufe read-only weiter.")

        tasks = [
            asyncio.create_task(self.collector.connect()),
            asyncio.create_task(self._pipeline_loop()),
            asyncio.create_task(self._heartbeat_loop()),
        ]
        if self.persist is not None:
            tasks.append(asyncio.create_task(self._persist_loop()))
        if self.risk_budget is not None and exec_active:
            tasks.append(asyncio.create_task(self._risk_loop()))
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def stop(self) -> None:
        self._running = False
        await self.collector.disconnect()
        if self.executor is not None:
            await self.executor.close()
        if self.risk_budget is not None:
            self.risk_budget.save()
        if self.persist is not None:
            self._flush_persist()  # finaler Flush der Restpuffer
            if self._owns_persist:
                try:
                    counts = self.persist.row_counts()
                    logger.info("Persistenz-Stand: %s", counts)
                except Exception:
                    pass
                self.persist.close()
            # Geteilte Verbindung: Referenz lokal lösen, aber NICHT schließen
            # (anderer Runner / MultiSymbolRunner besitzt sie).
            self.persist = None
        logger.info("LiveRunner gestoppt.")
