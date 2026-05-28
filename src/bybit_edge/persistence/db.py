"""
Persistence layer — DuckDB hot-storage (30 days) + Parquet cold-storage.

Tables: tickers, trades, liquidations, kline_1min.
Provides write_*() for real-time ingestion, query_kline() for analytics,
backfill_kline() for REST-based history loading, and archive_old_data()
for hot→cold migration.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import duckdb
import numpy as np

try:
    import polars as pl
except ImportError:
    pl = None  # type: ignore[assignment]

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore[assignment]

from bybit_edge.config import (
    DB_PATH,
    PARQUET_DIR,
    HOT_RETENTION_DAYS,
    PARQUET_COMPRESSION,
    rest_base_url,
    REST_KLINE,
    REST_RATE_LIMIT_UNAUTH,
)

logger = logging.getLogger(__name__)


class PersistenceLayer:
    """DuckDB-backed persistence with Parquet archival."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        resolved = db_path if db_path is not None else DB_PATH
        if str(resolved) == ":memory:":
            self.conn = duckdb.connect(":memory:")
        else:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            self.conn = duckdb.connect(str(resolved))
        self._init_schema()

    def close(self) -> None:
        """Close the underlying DuckDB connection."""
        self.conn.close()

    # ------------------------------------------------------------------
    # Schema initialisation
    # ------------------------------------------------------------------

    def _init_schema(self) -> None:
        """Create all required tables (idempotent)."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tickers (
                ts BIGINT NOT NULL,
                symbol VARCHAR NOT NULL,
                last_price DOUBLE,
                mark_price DOUBLE,
                index_price DOUBLE,
                funding_rate DOUBLE,
                next_funding_time BIGINT,
                open_interest DOUBLE,
                open_interest_value DOUBLE,
                bid1_price DOUBLE,
                bid1_size DOUBLE,
                ask1_price DOUBLE,
                ask1_size DOUBLE,
                recv_ts DOUBLE
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                ts BIGINT NOT NULL,
                symbol VARCHAR NOT NULL,
                price DOUBLE,
                volume DOUBLE,
                side VARCHAR,
                is_block BOOLEAN,
                recv_ts DOUBLE
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS liquidations (
                ts BIGINT NOT NULL,
                symbol VARCHAR NOT NULL,
                side VARCHAR,
                volume DOUBLE,
                price DOUBLE,
                usd_value DOUBLE
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS kline_1min (
                ts BIGINT NOT NULL,
                symbol VARCHAR NOT NULL,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume DOUBLE,
                turnover DOUBLE
            )
        """)

        # Indices for efficient time-range queries
        try:
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tickers_ts_sym ON tickers(ts, symbol)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trades_ts_sym ON trades(ts, symbol)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_liq_ts_sym ON liquidations(ts, symbol)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_kline_ts_sym ON kline_1min(ts, symbol)"
            )
        except duckdb.CatalogException:
            pass  # indices already exist

    # ------------------------------------------------------------------
    # Writers
    # ------------------------------------------------------------------

    def write_ticker(self, snap: object) -> None:
        """Insert a ``TickerSnapshot`` into the tickers table."""
        self.conn.execute(
            """
            INSERT INTO tickers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                snap.ts,  # type: ignore[attr-defined]
                snap.symbol,  # type: ignore[attr-defined]
                snap.last_price,  # type: ignore[attr-defined]
                snap.mark_price,  # type: ignore[attr-defined]
                snap.index_price,  # type: ignore[attr-defined]
                snap.funding_rate,  # type: ignore[attr-defined]
                snap.next_funding_time,  # type: ignore[attr-defined]
                snap.open_interest,  # type: ignore[attr-defined]
                snap.open_interest_value,  # type: ignore[attr-defined]
                snap.bid1_price,  # type: ignore[attr-defined]
                snap.bid1_size,  # type: ignore[attr-defined]
                snap.ask1_price,  # type: ignore[attr-defined]
                snap.ask1_size,  # type: ignore[attr-defined]
                snap.recv_ts,  # type: ignore[attr-defined]
            ],
        )

    def write_trade(self, evt: object) -> None:
        """Insert a ``TradeEvent`` into the trades table."""
        self.conn.execute(
            "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                evt.timestamp_ms,  # type: ignore[attr-defined]
                getattr(evt, "symbol", ""),
                evt.price,  # type: ignore[attr-defined]
                evt.volume,  # type: ignore[attr-defined]
                evt.side,  # type: ignore[attr-defined]
                evt.is_block,  # type: ignore[attr-defined]
                getattr(evt, "recv_ts", 0.0),
            ],
        )

    def write_liquidation(self, evt: object) -> None:
        """Insert a ``LiquidationEvent`` into the liquidations table."""
        self.conn.execute(
            "INSERT INTO liquidations VALUES (?, ?, ?, ?, ?, ?)",
            [
                evt.timestamp_ms,  # type: ignore[attr-defined]
                evt.symbol,  # type: ignore[attr-defined]
                evt.side,  # type: ignore[attr-defined]
                evt.volume,  # type: ignore[attr-defined]
                evt.price,  # type: ignore[attr-defined]
                evt.usd_value,  # type: ignore[attr-defined]
            ],
        )

    def write_kline(
        self,
        ts: int,
        symbol: str,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        turnover: float,
    ) -> None:
        """Insert a single kline (1-min candle) row."""
        self.conn.execute(
            "INSERT INTO kline_1min VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [ts, symbol, open_, high, low, close, volume, turnover],
        )

    # ------------------------------------------------------------------
    # Batch writers (efficient bulk ingestion for the live runner)
    # ------------------------------------------------------------------

    def write_tickers_batch(self, snaps: list) -> int:
        """Bulk-insert a list of ``TickerSnapshot`` objects. Returns count."""
        if not snaps:
            return 0
        rows = [
            [
                s.ts, s.symbol, s.last_price, s.mark_price, s.index_price,
                s.funding_rate, s.next_funding_time, s.open_interest,
                s.open_interest_value, s.bid1_price, s.bid1_size,
                s.ask1_price, s.ask1_size, s.recv_ts,
            ]
            for s in snaps
        ]
        self.conn.executemany(
            "INSERT INTO tickers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        return len(rows)

    def write_trades_batch(self, evts: list, symbol: str = "") -> int:
        """Bulk-insert a list of ``TradeEvent`` objects. Returns count."""
        if not evts:
            return 0
        rows = [
            [
                e.timestamp_ms, symbol, e.price, e.volume, e.side,
                e.is_block, getattr(e, "recv_ts", 0.0),
            ]
            for e in evts
        ]
        self.conn.executemany(
            "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?)", rows
        )
        return len(rows)

    def write_liquidations_batch(self, evts: list) -> int:
        """Bulk-insert a list of ``LiquidationEvent`` objects. Returns count."""
        if not evts:
            return 0
        rows = [
            [e.timestamp_ms, e.symbol, e.side, e.volume, e.price, e.usd_value]
            for e in evts
        ]
        self.conn.executemany(
            "INSERT INTO liquidations VALUES (?, ?, ?, ?, ?, ?)", rows
        )
        return len(rows)

    def row_counts(self) -> dict[str, int]:
        """Return current row counts per table (for monitoring)."""
        out: dict[str, int] = {}
        for table in ("tickers", "trades", "liquidations", "kline_1min"):
            r = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            out[table] = r[0] if r else 0
        return out

    # ------------------------------------------------------------------
    # Readers
    # ------------------------------------------------------------------

    def query_tickers(
        self, symbol: str, start_ts: int, end_ts: int
    ) -> list[tuple]:
        """Return raw ticker rows in ``[start_ts, end_ts]``."""
        result = self.conn.execute(
            "SELECT * FROM tickers WHERE symbol = ? AND ts >= ? AND ts <= ? ORDER BY ts",
            [symbol, start_ts, end_ts],
        ).fetchall()
        return result

    def query_kline(
        self,
        symbol: str,
        start_ts: int,
        end_ts: int,
        interval: str = "1min",
    ) -> "pl.DataFrame":
        """Return kline rows as a Polars DataFrame."""
        rows = self.conn.execute(
            """
            SELECT ts, symbol, open, high, low, close, volume, turnover
            FROM kline_1min
            WHERE symbol = ? AND ts >= ? AND ts <= ?
            ORDER BY ts
            """,
            [symbol, start_ts, end_ts],
        ).fetchall()
        return pl.DataFrame(
            rows,
            schema=["ts", "symbol", "open", "high", "low", "close", "volume", "turnover"],
            orient="row",
        )

    # ------------------------------------------------------------------
    # REST backfill
    # ------------------------------------------------------------------

    async def backfill_kline(
        self,
        symbol: str,
        months: int = 6,
        interval: str = "1",
    ) -> int:
        """Download historical klines via Bybit REST and insert into DuckDB.

        Returns the number of rows inserted.  Uses simple rate-limit
        handling (sleeps between requests).
        """
        if aiohttp is None:
            raise RuntimeError("aiohttp required for REST backfill")

        base = rest_base_url()
        url = f"{base}{REST_KLINE}"
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - months * 30 * 24 * 3600 * 1000
        cursor = start_ms
        total_inserted = 0
        # Rate limit: REST_RATE_LIMIT_UNAUTH req/min -> sleep between calls
        sleep_per_request = 60.0 / REST_RATE_LIMIT_UNAUTH + 0.05

        async with aiohttp.ClientSession() as session:
            while cursor < end_ms:
                params = {
                    "category": "linear",
                    "symbol": symbol,
                    "interval": interval,
                    "start": str(cursor),
                    "end": str(min(cursor + 200 * 60_000, end_ms)),
                    "limit": "200",
                }
                try:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 429:
                            logger.warning("Rate limited — sleeping 10 s")
                            await __import__("asyncio").sleep(10)
                            continue
                        if resp.status != 200:
                            logger.warning("Kline fetch HTTP %d — skipping batch", resp.status)
                            cursor += 200 * 60_000
                            continue
                        body = await resp.json()
                except Exception:
                    logger.exception("Kline fetch error — retrying after 5 s")
                    await __import__("asyncio").sleep(5)
                    continue

                candles = body.get("result", {}).get("list", [])
                if not candles:
                    cursor += 200 * 60_000
                    continue

                for c in candles:
                    # Bybit returns [startTime, open, high, low, close, volume, turnover]
                    self.write_kline(
                        ts=int(c[0]),
                        symbol=symbol,
                        open_=float(c[1]),
                        high=float(c[2]),
                        low=float(c[3]),
                        close=float(c[4]),
                        volume=float(c[5]),
                        turnover=float(c[6]),
                    )
                    total_inserted += 1

                # Advance cursor past last candle
                last_ts = int(candles[-1][0])
                cursor = max(last_ts + 60_000, cursor + 60_000)

                await __import__("asyncio").sleep(sleep_per_request)

        logger.info("Backfill complete: %d klines for %s", total_inserted, symbol)
        return total_inserted

    # ------------------------------------------------------------------
    # Archival (hot → cold)
    # ------------------------------------------------------------------

    def archive_old_data(self) -> None:
        """Move data older than ``HOT_RETENTION_DAYS`` to Parquet files
        and delete from DuckDB.
        """
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=HOT_RETENTION_DAYS)
        cutoff_ms = int(cutoff_dt.timestamp() * 1000)

        parquet_dir = PARQUET_DIR
        parquet_dir.mkdir(parents=True, exist_ok=True)

        date_tag = cutoff_dt.strftime("%Y%m%d")

        for table in ("tickers", "trades", "liquidations", "kline_1min"):
            count_row = self.conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE ts < ?", [cutoff_ms]
            ).fetchone()
            count = count_row[0] if count_row else 0
            if count == 0:
                continue

            out_path = parquet_dir / f"{table}_{date_tag}.parquet"
            self.conn.execute(
                f"""
                COPY (SELECT * FROM {table} WHERE ts < {cutoff_ms})
                TO '{out_path}' (FORMAT PARQUET, COMPRESSION '{PARQUET_COMPRESSION}')
                """
            )
            self.conn.execute(
                f"DELETE FROM {table} WHERE ts < ?", [cutoff_ms]
            )
            logger.info(
                "Archived %d rows from %s -> %s", count, table, out_path
            )
