"""
Storage layer for the F0 Recording-Engine (C-36).

Two responsibilities, both *strictly additive* (DEC-06) — nothing here ever
reads or writes the existing ``data/parquet/`` cold storage:

1. :class:`ParquetStreamWriter` — buffers normalised rows per stream and
   flushes them to date-partitioned Parquet segments under
   ``data/parquet/recording_f0/{stream}/{date}/seg-*.parquet``. Each stream
   has an *explicit* :class:`pyarrow.Schema` (see :data:`STREAM_SCHEMAS`) and a
   ``schema_version`` stored in the Parquet key/value metadata so that schema
   drift is detectable at review time (Sunset).

2. :class:`StorageCap` — a hard GB ceiling enforced as a ring buffer: when the
   recording root exceeds the cap, the OLDEST segment files (of THIS engine's
   own streams only — never the 1.0 cold storage) are deleted until the engine
   is back under the cap, with a WARN log per eviction. Plus disk-usage
   telemetry (:meth:`StorageCap.usage_report`).

FINAL_PRD §3 (Pilot 3) mandates the hard, ring-buffer-based storage cap; the
PRD does not fix a GB number, so :data:`DEFAULT_CAP_GB` is a documented default
(see the comment there) and is overridable via the ``--cap-gb`` CLI flag.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Iterable, Optional

import pyarrow as pa
import pyarrow.parquet as pq

from bybit_edge.config import DATA_DIR, PARQUET_COMPRESSION

logger = logging.getLogger(__name__)

# Output root for ALL recorder data. Deliberately a NEW sub-path so the
# existing ``data/parquet/{table}_{date}.parquet`` cold storage (Schutzgut 3)
# is never touched.
RECORDING_ROOT: Path = DATA_DIR / "parquet" / "recording_f0"

# Schema version stamped into every Parquet segment's metadata. Bump this when
# any stream schema in STREAM_SCHEMAS changes so the Sunset review can flag
# drift between historical and current segments.
SCHEMA_VERSION: int = 1

# Hard storage ceiling default. The PRD (§3 Pilot 3) requires a fixed GB cap
# but does not name the number. config.py's §3 estimates put the *existing*
# 1.0 streams at ~80 GB/year compressed for one symbol; the NEW F0 streams are
# far lighter (insurance/adlAlert ~ a few MB/day, rpi orderbook + option
# tickers the bulk). 50 GB gives many weeks of single-operator headroom while
# staying well inside a desktop disk — overridable via --cap-gb. (ASSUMPTION.)
DEFAULT_CAP_GB: float = 50.0

# How many rows accumulate per stream buffer before an automatic flush, and the
# wall-clock flush interval. Both are belt-and-suspenders: whichever triggers
# first flushes the buffer.
DEFAULT_FLUSH_ROWS: int = 2_000
DEFAULT_FLUSH_SECONDS: float = 10.0

# If flushes keep failing, the in-memory buffer is retained for retry (rows
# are NEVER silently discarded) but it grows unboundedly. Once it exceeds
# this multiple of ``flush_rows`` an escalated alarm is logged every flush
# attempt so the operator sees the memory-growth risk long before OOM.
BUFFER_ALARM_FACTOR: int = 10


# ══════════════════════════════════════════════════════════════════════
# Explicit per-stream pyarrow schemas
# ══════════════════════════════════════════════════════════════════════
# Every stream writes a flat, columnar row set. ``recv_ts`` (float seconds,
# reception wall-clock) and ``ts`` (exchange ms, the event-time anchor) are
# present on every stream, mirroring the 1.0 envelope convention (WSMessage).
# ``raw_json`` keeps the untouched payload so nothing is lost even if the
# typed columns miss an exotic field — cheap insurance for a recording engine
# whose downstream consumers (Welle 2) are not yet built.

_RPI_ORDERBOOK_SCHEMA = pa.schema([
    ("ts", pa.int64()),            # exchange envelope ts (ms)
    ("symbol", pa.string()),
    ("update_id", pa.int64()),     # orderbook update id ("u")
    ("seq", pa.int64()),           # cross-sequence ("seq")
    ("msg_type", pa.string()),     # "snapshot" | "delta"
    ("side", pa.string()),         # "bid" | "ask"
    ("level", pa.int32()),         # 0-based level within side
    ("price", pa.float64()),
    ("size", pa.float64()),
    ("recv_ts", pa.float64()),
])

_INSURANCE_POOL_SCHEMA = pa.schema([
    ("ts", pa.int64()),            # exchange envelope ts (ms)
    ("coin", pa.string()),         # e.g. "USDT"
    ("balance", pa.float64()),     # insurance pool balance
    ("recv_ts", pa.float64()),
])

_ADL_ALERTS_SCHEMA = pa.schema([
    ("ts", pa.int64()),            # exchange envelope ts (ms)
    ("symbol", pa.string()),       # may be empty for account-wide alerts
    ("side", pa.string()),
    ("adl_rank", pa.int32()),      # ADL ranking indicator if present
    ("raw_json", pa.string()),     # full payload — schema is under-documented
    ("recv_ts", pa.float64()),
])

_PREMIUM_INDEX_KLINE_SCHEMA = pa.schema([
    ("ts", pa.int64()),            # kline open time (ms)
    ("symbol", pa.string()),
    ("interval", pa.string()),     # e.g. "1"
    ("open", pa.float64()),
    ("high", pa.float64()),
    ("low", pa.float64()),
    ("close", pa.float64()),
    ("recv_ts", pa.float64()),
])

_OPTION_TICKERS_SCHEMA = pa.schema([
    ("ts", pa.int64()),            # exchange envelope ts (ms)
    ("symbol", pa.string()),       # option symbol e.g. "BTC-27JUN25-60000-C"
    ("underlying", pa.string()),   # "BTC" | "ETH"
    ("mark_price", pa.float64()),
    ("index_price", pa.float64()),
    ("mark_iv", pa.float64()),     # implied volatility (mark)
    ("underlying_price", pa.float64()),
    ("delta", pa.float64()),
    ("gamma", pa.float64()),
    ("vega", pa.float64()),
    ("theta", pa.float64()),
    ("open_interest", pa.float64()),
    ("recv_ts", pa.float64()),
])

# Canonical mapping: stream-name -> explicit schema. The engine's StreamSpec
# names (see recording_engine.py) MUST match these keys.
STREAM_SCHEMAS: dict[str, pa.Schema] = {
    "rpi_orderbook": _RPI_ORDERBOOK_SCHEMA,
    "insurance_pool": _INSURANCE_POOL_SCHEMA,
    "adl_alerts": _ADL_ALERTS_SCHEMA,
    "premium_index_kline": _PREMIUM_INDEX_KLINE_SCHEMA,
    "option_tickers": _OPTION_TICKERS_SCHEMA,
}


def _utc_date(epoch_s: float) -> str:
    """Return the ``YYYY-MM-DD`` UTC date string for an epoch-seconds value."""
    return time.strftime("%Y-%m-%d", time.gmtime(epoch_s))


# ══════════════════════════════════════════════════════════════════════
# Parquet writer (one per stream)
# ══════════════════════════════════════════════════════════════════════
class ParquetStreamWriter:
    """Buffered, date-partitioned Parquet writer for a single stream.

    Rows are accumulated in memory and written as immutable segment files
    (``seg-<recv_ts_ms>-<n>.parquet``) on :meth:`flush`. Segments are never
    appended to — this keeps each file self-contained, which is exactly what
    the ring-buffer cap needs (delete whole oldest files, never rewrite).
    """

    def __init__(
        self,
        stream: str,
        root: Path = RECORDING_ROOT,
        flush_rows: int = DEFAULT_FLUSH_ROWS,
        flush_seconds: float = DEFAULT_FLUSH_SECONDS,
        compression: str = PARQUET_COMPRESSION,
    ) -> None:
        if stream not in STREAM_SCHEMAS:
            raise ValueError(
                f"Unknown stream {stream!r}; choose from {list(STREAM_SCHEMAS)}"
            )
        self.stream = stream
        self.schema = STREAM_SCHEMAS[stream]
        self.root = Path(root)
        self.flush_rows = flush_rows
        self.flush_seconds = flush_seconds
        self.compression = compression

        self._buffer: list[dict[str, Any]] = []
        self._last_flush: float = time.time()
        self._seg_counter: int = 0
        self.rows_written: int = 0
        self.segments_written: int = 0
        self.flush_failures: int = 0

    # ------------------------------------------------------------------
    def append(self, row: dict[str, Any]) -> None:
        """Add one normalised row to the buffer (does not flush)."""
        self._buffer.append(row)

    def should_flush(self, now: Optional[float] = None) -> bool:
        """True if the row-count or time threshold has been reached."""
        if not self._buffer:
            return False
        if len(self._buffer) >= self.flush_rows:
            return True
        now = time.time() if now is None else now
        return (now - self._last_flush) >= self.flush_seconds

    def flush(self) -> Optional[Path]:
        """Write the buffer to a new Parquet segment, then clear it.

        Returns the written segment path, or ``None`` if the buffer was empty
        or the write failed. Rows are projected onto the explicit schema
        (missing columns -> null, unknown columns dropped) so a malformed
        payload can never corrupt the column layout.

        Failure semantics (CRITICAL_REVIEW_2026-07-09, data-loss-write-
        ordering): the buffer is cleared only AFTER ``pq.write_table``
        succeeded. If any step of the write path fails, the rows stay
        buffered for a retry on the next flush call, an ERROR naming the
        number of at-risk rows is logged, and the exception is contained
        here — it must not escape into the WS transport loop (where it would
        masquerade as a connection loss) or abort the writer-close loop in
        ``RecordingEngine.stop()``.
        """
        if not self._buffer:
            return None

        # Snapshot — the buffer is only cleared after a successful write.
        rows = self._buffer

        try:
            # Build columnar arrays strictly from the declared schema.
            columns: dict[str, list[Any]] = {f.name: [] for f in self.schema}
            for row in rows:
                for name in columns:
                    columns[name].append(row.get(name))
            table = pa.table(columns, schema=self.schema)

            recv_ts = time.time()
            # Partition by the UTC date of the *first* row's recv_ts if
            # present, else by the flush wall-clock — keeps a segment inside
            # one date dir.
            anchor = rows[0].get("recv_ts") or recv_ts
            date_dir = self.root / self.stream / _utc_date(anchor)
            date_dir.mkdir(parents=True, exist_ok=True)

            self._seg_counter += 1
            seg_path = (
                date_dir / f"seg-{int(recv_ts * 1000)}-{self._seg_counter}.parquet"
            )

            metadata = {
                b"stream": self.stream.encode(),
                b"schema_version": str(SCHEMA_VERSION).encode(),
                b"written_recv_ts": str(recv_ts).encode(),
                b"row_count": str(table.num_rows).encode(),
            }
            table = table.replace_schema_metadata(metadata)
            pq.write_table(table, seg_path, compression=self.compression)
        except Exception:
            self.flush_failures += 1
            logger.exception(
                "[%s] flush FAILED — %d buffered row(s) retained for retry "
                "on the next flush (failure #%d)",
                self.stream, len(rows), self.flush_failures,
            )
            if len(self._buffer) > BUFFER_ALARM_FACTOR * self.flush_rows:
                logger.error(
                    "ALARM: [%s] retry buffer holds %d rows (> %d x "
                    "flush_rows=%d) after repeated flush failures — memory "
                    "keeps growing until a flush succeeds; rows are never "
                    "silently discarded.",
                    self.stream, len(self._buffer),
                    BUFFER_ALARM_FACTOR, self.flush_rows,
                )
            return None

        # Success: drop exactly the rows that were written. (flush() is
        # synchronous, so normally self._buffer is rows — the slice keeps
        # this correct even if appends ever interleave with a flush.)
        self._buffer = self._buffer[len(rows):]
        self.rows_written += table.num_rows
        self.segments_written += 1
        self._last_flush = recv_ts
        logger.debug(
            "Flushed %d rows -> %s", table.num_rows, seg_path.name
        )
        return seg_path

    def close(self) -> Optional[Path]:
        """Flush any remaining buffered rows (graceful shutdown)."""
        seg = self.flush()
        if self._buffer:
            logger.error(
                "[%s] close(): %d buffered row(s) could NOT be persisted "
                "(final flush failed)", self.stream, len(self._buffer),
            )
        return seg


# ══════════════════════════════════════════════════════════════════════
# Ring-buffer storage cap
# ══════════════════════════════════════════════════════════════════════
class StorageCap:
    """Hard GB ceiling over the recording root, enforced as a ring buffer.

    On :meth:`enforce`, if the total size of segment files under ``root``
    exceeds ``cap_gb``, the OLDEST segments are deleted (by file mtime) until
    the usage is back under the cap. Only files inside ``root`` are ever
    touched — the existing 1.0 cold storage lives one directory up and is
    never enumerated.
    """

    def __init__(self, cap_gb: float = DEFAULT_CAP_GB, root: Path = RECORDING_ROOT) -> None:
        if cap_gb <= 0:
            raise ValueError(f"cap_gb must be > 0, got {cap_gb}")
        self.cap_gb = cap_gb
        self.cap_bytes = int(cap_gb * 1024 ** 3)
        self.root = Path(root)
        self.evictions: int = 0
        self.bytes_evicted: int = 0

    # ------------------------------------------------------------------
    def _segment_files(self) -> list[Path]:
        """All Parquet segments under the recording root (recursive)."""
        if not self.root.exists():
            return []
        return [p for p in self.root.rglob("*.parquet") if p.is_file()]

    def current_bytes(self) -> int:
        """Total bytes of all recorder segments currently on disk."""
        total = 0
        for p in self._segment_files():
            try:
                total += p.stat().st_size
            except OSError:
                continue
        return total

    def enforce(self) -> int:
        """Evict oldest segments until usage <= cap. Returns bytes freed."""
        files = self._segment_files()
        total = 0
        sized: list[tuple[float, int, Path]] = []
        for p in files:
            try:
                st = p.stat()
            except OSError:
                continue
            sized.append((st.st_mtime, st.st_size, p))
            total += st.st_size

        if total <= self.cap_bytes:
            return 0

        # Oldest first.
        sized.sort(key=lambda t: t[0])
        freed = 0
        for mtime, size, path in sized:
            if total - freed <= self.cap_bytes:
                break
            try:
                path.unlink()
            except OSError as exc:
                logger.warning("Could not evict segment %s: %s", path, exc)
                continue
            freed += size
            self.evictions += 1
            self.bytes_evicted += size
            logger.warning(
                "Storage cap %.1f GB exceeded — evicted oldest segment %s "
                "(%.2f MB freed; now %.2f / %.1f GB)",
                self.cap_gb,
                path.name,
                size / 1024 ** 2,
                (total - freed) / 1024 ** 3,
                self.cap_gb,
            )
        return freed

    def usage_report(self) -> dict[str, Any]:
        """Disk-usage telemetry for the recording root (per-stream + total)."""
        per_stream: dict[str, dict[str, Any]] = {}
        total_bytes = 0
        total_segments = 0
        for p in self._segment_files():
            try:
                size = p.stat().st_size
            except OSError:
                continue
            # root/{stream}/{date}/seg-*.parquet -> stream is the first part.
            try:
                stream = p.relative_to(self.root).parts[0]
            except ValueError:
                stream = "?"
            slot = per_stream.setdefault(stream, {"bytes": 0, "segments": 0})
            slot["bytes"] += size
            slot["segments"] += 1
            total_bytes += size
            total_segments += 1
        return {
            "cap_gb": self.cap_gb,
            "used_gb": round(total_bytes / 1024 ** 3, 4),
            "used_pct": round(100.0 * total_bytes / self.cap_bytes, 2),
            "total_bytes": total_bytes,
            "total_segments": total_segments,
            "evictions": self.evictions,
            "bytes_evicted": self.bytes_evicted,
            "per_stream": per_stream,
        }
