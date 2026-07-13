"""
WP-2-VERIFY (T0, SANDBOX) — tests for the F0 recorder storage layer.

Covers ``src/bybit_edge/recorder/storage.py``:

* Parquet write with explicit schema projection + readable
  ``schema_version`` key/value metadata,
* ring-buffer storage cap (oldest-first eviction, ends under cap, WARN
  logged, never touches files outside the recording root),
* flush triggers (row-count AND time-based),
* path isolation: everything lands under ``data/parquet/recording_f0/``
  (tmp_path-based here) — the 1.0 cold storage is never written.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from bybit_edge.config import DATA_DIR
from bybit_edge.recorder.recording_engine import RecordingEngine
import bybit_edge.recorder.storage as storage_mod
from bybit_edge.recorder.storage import (
    BUFFER_ALARM_FACTOR,
    RECORDING_ROOT,
    SCHEMA_VERSION,
    STREAM_SCHEMAS,
    ParquetStreamWriter,
    StorageCap,
)


def _insurance_row(ts: int = 1718000000000, recv_ts: float = 1718000000.0) -> dict:
    return {"ts": ts, "coin": "USDT", "balance": 1.5, "recv_ts": recv_ts}


def _write_fake_segment(path: Path, size: int, mtime: float) -> None:
    """Create a fake .parquet segment file with exact size and mtime."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    os.utime(path, (mtime, mtime))


# ══════════════════════════════════════════════════════════════════════
# 5) Parquet write: schema projection + schema_version metadata
# ══════════════════════════════════════════════════════════════════════
class TestParquetWriter:
    def test_flush_writes_schema_and_version_metadata(self, tmp_path) -> None:
        writer = ParquetStreamWriter("insurance_pool", root=tmp_path)
        writer.append(_insurance_row())
        seg = writer.flush()
        assert seg is not None and seg.exists()

        table = pq.read_table(seg)
        assert table.num_rows == 1
        # Columns exactly match the declared explicit schema, in order.
        assert table.schema.names == STREAM_SCHEMAS["insurance_pool"].names
        for field in STREAM_SCHEMAS["insurance_pool"]:
            assert table.schema.field(field.name).type == field.type

        # schema_version is readable from the Parquet key/value metadata.
        meta = pq.read_metadata(seg).metadata
        assert meta[b"schema_version"] == str(SCHEMA_VERSION).encode()
        assert meta[b"stream"] == b"insurance_pool"
        assert meta[b"row_count"] == b"1"

    def test_flush_projects_rows_onto_schema(self, tmp_path) -> None:
        """Unknown columns are dropped, missing columns become null."""
        writer = ParquetStreamWriter("insurance_pool", root=tmp_path)
        row = _insurance_row()
        row["rogue_column"] = "must-not-appear"   # unknown -> dropped
        del row["balance"]                        # missing -> null
        writer.append(row)
        seg = writer.flush()
        table = pq.read_table(seg)
        assert "rogue_column" not in table.schema.names
        assert table.column("balance").null_count == 1
        assert table.column("coin").to_pylist() == ["USDT"]

    def test_segments_are_date_partitioned_per_stream(self, tmp_path) -> None:
        writer = ParquetStreamWriter("insurance_pool", root=tmp_path)
        # 2026-06-11 00:00:00 UTC = 1781136000
        writer.append(_insurance_row(recv_ts=1781136000.0))
        seg = writer.flush()
        rel = seg.relative_to(tmp_path)
        assert rel.parts[0] == "insurance_pool"
        assert rel.parts[1] == "2026-06-11"
        assert rel.parts[2].startswith("seg-") and rel.suffix == ".parquet"

    def test_unknown_stream_rejected(self, tmp_path) -> None:
        with pytest.raises(ValueError, match="Unknown stream"):
            ParquetStreamWriter("no_such_stream", root=tmp_path)

    def test_flush_empty_buffer_returns_none(self, tmp_path) -> None:
        writer = ParquetStreamWriter("adl_alerts", root=tmp_path)
        assert writer.flush() is None
        assert writer.close() is None
        assert list(tmp_path.rglob("*.parquet")) == []


# ══════════════════════════════════════════════════════════════════════
# 5b) Flush failure: buffer retained for retry, NEVER cleared before the
#     Parquet segment is durably written (CRITICAL_REVIEW_2026-07-09,
#     data-loss-write-ordering regression tests)
# ══════════════════════════════════════════════════════════════════════
class TestFlushFailureRetainsBuffer:
    def test_failed_write_table_keeps_buffer_and_logs_row_count(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A failing pq.write_table must NOT clear the buffer: the rows stay
        for retry, an ERROR names the affected row count, and the exception
        does not escape (it would destabilise the calling WS loop)."""
        writer = ParquetStreamWriter("insurance_pool", root=tmp_path)
        writer.append(_insurance_row())
        writer.append(_insurance_row(ts=1718000001000))

        def boom(*args, **kwargs):
            raise OSError("simulated transient disk error")

        monkeypatch.setattr(storage_mod.pq, "write_table", boom)
        with caplog.at_level(logging.ERROR, logger="bybit_edge.recorder.storage"):
            seg = writer.flush()  # must not raise

        assert seg is None
        assert len(writer._buffer) == 2, "rows were discarded on failed write"
        assert writer.rows_written == 0
        assert writer.segments_written == 0
        assert writer.flush_failures == 1
        assert list(tmp_path.rglob("*.parquet")) == []
        errs = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert any(
            "2 buffered row" in r.getMessage() and "retained for retry" in r.getMessage()
            for r in errs
        ), "ERROR log must name the number of at-risk rows"

    def test_rows_survive_failed_flush_and_land_in_next_successful_one(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """First flush fails (transient), second succeeds: BOTH original rows
        plus a newly appended one must be in the written segment.

        The second attempt is made *after* the retry-backoff cooldown has
        elapsed (CRITICAL_REVIEW_2_2026-07-13) — an immediate retry within
        the cooldown window is exactly the retry-storm behavior the backoff
        exists to prevent; see TestFlushRetryBackoff below for that case."""
        writer = ParquetStreamWriter("insurance_pool", root=tmp_path)
        writer.append(_insurance_row())
        writer.append(_insurance_row(ts=1718000001000))

        real_write = storage_mod.pq.write_table
        calls = {"n": 0}

        def flaky(table, path, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("simulated transient disk error")
            return real_write(table, path, **kwargs)

        monkeypatch.setattr(storage_mod.pq, "write_table", flaky)
        t0 = 1_800_000_000.0
        assert writer.flush(now=t0) is None       # transient failure
        writer.append(_insurance_row(ts=1718000002000))  # new data keeps coming
        # Past the backoff cooldown -> retry actually attempts the write.
        seg = writer.flush(now=t0 + writer.flush_retry_backoff_seconds + 0.1)

        assert seg is not None and seg.exists()
        table = pq.read_table(seg)
        assert table.num_rows == 3, "retained rows missing after retry"
        assert sorted(table.column("ts").to_pylist()) == [
            1718000000000, 1718000001000, 1718000002000,
        ]
        assert writer._buffer == []
        assert writer.rows_written == 3
        assert writer.flush_failures == 1

    def test_repeated_failures_alarm_but_never_drop_rows(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Unbounded buffer growth under persistent failure is alarmed
        (ERROR) once the buffer exceeds BUFFER_ALARM_FACTOR x flush_rows —
        but rows are never silently discarded."""
        writer = ParquetStreamWriter(
            "insurance_pool", root=tmp_path, flush_rows=2, flush_seconds=0.0
        )

        def boom(*args, **kwargs):
            raise OSError("simulated persistent disk error")

        monkeypatch.setattr(storage_mod.pq, "write_table", boom)
        n_rows = BUFFER_ALARM_FACTOR * writer.flush_rows + 1
        with caplog.at_level(logging.ERROR, logger="bybit_edge.recorder.storage"):
            for i in range(n_rows):
                writer.append(_insurance_row(ts=1718000000000 + i))
                if writer.should_flush():
                    writer.flush()

        assert len(writer._buffer) == n_rows, "rows must never be dropped"
        alarms = [
            r for r in caplog.records
            if r.levelno == logging.ERROR and "ALARM" in r.getMessage()
        ]
        assert alarms, "buffer-growth ALARM was not logged"

    def test_close_logs_error_when_final_flush_fails(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """close() must not raise on a failing final flush and must log the
        unpersisted row count (shutdown data-loss visibility)."""
        writer = ParquetStreamWriter("insurance_pool", root=tmp_path)
        writer.append(_insurance_row())

        def boom(*args, **kwargs):
            raise OSError("simulated disk error at shutdown")

        monkeypatch.setattr(storage_mod.pq, "write_table", boom)
        with caplog.at_level(logging.ERROR, logger="bybit_edge.recorder.storage"):
            assert writer.close() is None  # must not raise
        assert any(
            "could NOT be persisted" in r.getMessage()
            for r in caplog.records if r.levelno == logging.ERROR
        )


# ══════════════════════════════════════════════════════════════════════
# 5c) Retry-storm regression (CRITICAL_REVIEW_2_2026-07-13,
#     resource-exhaustion-regression-from-fix): the 2026-07-09 fix stopped
#     advancing ``_last_flush`` on failure, so ``should_flush()`` stayed
#     permanently true and ``RecordingEngine._run_ws_transport`` (which calls
#     ``_maybe_flush`` after EVERY inbound message) turned a PERSISTENT flush
#     failure into a full synchronous ``pq.write_table`` attempt per message
#     -- blocking the event loop long enough to miss Bybit's keepalive and
#     drop the WS connection. These tests simulate a sustained failure across
#     many inbound messages and prove (a) rows are still never dropped and
#     (b) actual write attempts stay far below the message count thanks to
#     the retry backoff.
# ══════════════════════════════════════════════════════════════════════
class TestFlushRetryBackoff:
    def test_persistent_failure_throttles_attempts_but_keeps_all_rows(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """20+ inbound messages, pq.write_table permanently failing: no rows
        lost, and write attempts stay well below the message count."""
        writer = ParquetStreamWriter(
            "insurance_pool", root=tmp_path, flush_rows=5, flush_seconds=1.0,
        )

        attempts = {"n": 0}

        def always_boom(*args, **kwargs):
            attempts["n"] += 1
            raise OSError("simulated persistent full-disk error")

        monkeypatch.setattr(storage_mod.pq, "write_table", always_boom)

        n_messages = 40
        t0 = 1_800_000_000.0
        # Messages arriving in a tight burst (100ms apart) mirroring
        # RecordingEngine._run_ws_transport calling _maybe_flush() after
        # every inbound message.
        for i in range(n_messages):
            now = t0 + i * 0.1
            writer.append(_insurance_row(ts=1718000000000 + i))
            if writer.should_flush(now=now):
                writer.flush(now=now)

        # (a) no data loss: every appended row is still buffered for retry.
        assert len(writer._buffer) == n_messages, "rows must never be dropped"

        # (b) actual write attempts stay far below the inbound message
        # count -- proof the per-message retry storm is fixed. Without the
        # backoff, ``attempts["n"]`` would equal ``n_messages`` (minus the
        # few messages before the first flush trigger).
        assert 0 < attempts["n"] < n_messages / 3, (
            f"expected far fewer than {n_messages} write attempts under a "
            f"persistent failure, got {attempts['n']}"
        )
        assert writer.flush_failures == attempts["n"]
        assert writer._consecutive_flush_failures == attempts["n"]

    def test_backoff_doubles_then_recovers_once_writes_succeed_again(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Backoff grows across consecutive failures; once the underlying
        failure clears, the next attempt past the cooldown drains the whole
        retained buffer -- throttling never abandons a retry."""
        writer = ParquetStreamWriter(
            "insurance_pool", root=tmp_path, flush_rows=1000, flush_seconds=9999.0,
        )
        real_write = storage_mod.pq.write_table
        calls = {"n": 0}

        def flaky(table, path, **kwargs):
            calls["n"] += 1
            if calls["n"] <= 2:
                raise OSError("simulated disk error")
            return real_write(table, path, **kwargs)

        monkeypatch.setattr(storage_mod.pq, "write_table", flaky)

        t0 = 1_800_000_000.0
        writer.append(_insurance_row())
        assert writer.flush(now=t0) is None            # attempt #1 fails
        assert calls["n"] == 1

        writer.append(_insurance_row(ts=1718000001000))
        # Still inside the (1st-failure) backoff window -> no new attempt.
        assert writer.flush(now=t0 + 0.5) is None
        assert calls["n"] == 1, "retry attempted before backoff elapsed"

        # Past the 1st backoff window -> attempt #2 (still failing).
        t1 = t0 + writer.flush_retry_backoff_seconds + 0.1
        assert writer.flush(now=t1) is None
        assert calls["n"] == 2

        # Backoff has doubled after the 2nd consecutive failure; well past
        # it, the underlying failure has cleared -> attempt #3 succeeds and
        # drains everything retained so far.
        t2 = t1 + writer._retry_backoff_seconds() + 0.1
        seg = writer.flush(now=t2)
        assert seg is not None and seg.exists()
        assert writer._buffer == []
        assert writer.rows_written == 2
        assert writer._consecutive_flush_failures == 0
        table = pq.read_table(seg)
        assert sorted(table.column("ts").to_pylist()) == [
            1718000000000, 1718000001000,
        ]


# ══════════════════════════════════════════════════════════════════════
# 7) Flush triggers: row-count AND time-based
# ══════════════════════════════════════════════════════════════════════
class TestFlushTriggers:
    def test_row_count_trigger(self, tmp_path) -> None:
        writer = ParquetStreamWriter(
            "insurance_pool", root=tmp_path, flush_rows=3, flush_seconds=9999.0
        )
        assert writer.should_flush() is False  # empty buffer never flushes
        writer.append(_insurance_row())
        writer.append(_insurance_row())
        assert writer.should_flush(now=writer._last_flush) is False
        writer.append(_insurance_row())
        assert writer.should_flush(now=writer._last_flush) is True
        seg = writer.flush()
        assert pq.read_metadata(seg).num_rows == 3

    def test_time_based_trigger(self, tmp_path) -> None:
        writer = ParquetStreamWriter(
            "insurance_pool", root=tmp_path, flush_rows=10_000, flush_seconds=5.0
        )
        writer.append(_insurance_row())
        t0 = writer._last_flush
        assert writer.should_flush(now=t0 + 4.9) is False   # below interval
        assert writer.should_flush(now=t0 + 5.0) is True    # interval reached
        assert writer.should_flush(now=t0 + 60.0) is True

    def test_time_trigger_needs_buffered_rows(self, tmp_path) -> None:
        writer = ParquetStreamWriter(
            "insurance_pool", root=tmp_path, flush_rows=10, flush_seconds=0.0
        )
        # Even with an elapsed interval, an empty buffer must not flush.
        assert writer.should_flush(now=writer._last_flush + 1e6) is False


# ══════════════════════════════════════════════════════════════════════
# 6) Ring-buffer cap: oldest-first eviction, ends under cap, WARN logged
# ══════════════════════════════════════════════════════════════════════
class TestStorageCap:
    def test_eviction_oldest_first_ends_under_cap(
        self, tmp_path, caplog: pytest.LogCaptureFixture
    ) -> None:
        root = tmp_path / "recording_f0"
        # 5 artificially small segments, 1000 B each, strictly ordered mtimes.
        base = 1_700_000_000.0
        segs = []
        for i in range(5):
            p = root / "rpi_orderbook" / "2026-06-01" / f"seg-{i}.parquet"
            _write_fake_segment(p, size=1000, mtime=base + i * 60)
            segs.append(p)

        # Cap = 3000 B -> the two OLDEST segments must be evicted.
        cap = StorageCap(cap_gb=3000 / 1024**3, root=root)
        assert cap.current_bytes() == 5000
        with caplog.at_level(
            logging.WARNING, logger="bybit_edge.recorder.storage"
        ):
            freed = cap.enforce()

        assert freed == 2000
        assert not segs[0].exists() and not segs[1].exists()  # oldest two gone
        assert all(p.exists() for p in segs[2:])              # newest stay
        assert cap.current_bytes() <= cap.cap_bytes           # under the cap
        assert cap.evictions == 2 and cap.bytes_evicted == 2000
        warn = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warn) == 2
        assert all("evicted oldest segment" in r.message for r in warn)

    def test_enforce_noop_under_cap(self, tmp_path) -> None:
        root = tmp_path / "recording_f0"
        p = root / "adl_alerts" / "2026-06-01" / "seg-0.parquet"
        _write_fake_segment(p, size=100, mtime=1_700_000_000.0)
        cap = StorageCap(cap_gb=1.0, root=root)
        assert cap.enforce() == 0
        assert p.exists() and cap.evictions == 0

    def test_eviction_never_leaves_recording_root(self, tmp_path) -> None:
        """Files OUTSIDE the recorder root (1.0 cold storage analogue) survive."""
        root = tmp_path / "parquet" / "recording_f0"
        inside = root / "rpi_orderbook" / "2026-06-01" / "seg-0.parquet"
        _write_fake_segment(inside, size=5000, mtime=1_700_000_000.0)
        # Sibling = stand-in for existing data/parquet/{table}_{date}.parquet.
        legacy = tmp_path / "parquet" / "ticker_2026-06-01.parquet"
        _write_fake_segment(legacy, size=5000, mtime=1.0)  # much older

        cap = StorageCap(cap_gb=1000 / 1024**3, root=root)
        cap.enforce()
        assert legacy.exists(), "cold-storage sibling must never be evicted"
        assert not inside.exists()  # only the recorder's own segment went

    def test_invalid_cap_rejected(self, tmp_path) -> None:
        with pytest.raises(ValueError, match="cap_gb"):
            StorageCap(cap_gb=0.0, root=tmp_path)
        with pytest.raises(ValueError, match="cap_gb"):
            StorageCap(cap_gb=-1.0, root=tmp_path)

    def test_usage_report_telemetry(self, tmp_path) -> None:
        root = tmp_path / "recording_f0"
        _write_fake_segment(
            root / "rpi_orderbook" / "2026-06-01" / "seg-0.parquet", 1000, 1.0
        )
        _write_fake_segment(
            root / "insurance_pool" / "2026-06-01" / "seg-0.parquet", 500, 2.0
        )
        cap = StorageCap(cap_gb=1.0, root=root)
        report = cap.usage_report()
        assert report["total_bytes"] == 1500
        assert report["total_segments"] == 2
        assert report["per_stream"]["rpi_orderbook"]["bytes"] == 1000
        assert report["per_stream"]["insurance_pool"]["segments"] == 1
        assert report["cap_gb"] == 1.0
        assert report["evictions"] == 0


# ══════════════════════════════════════════════════════════════════════
# 8) Path isolation: only data/parquet/recording_f0/, no legacy writes
# ══════════════════════════════════════════════════════════════════════
class TestPathIsolation:
    def test_default_root_is_recording_f0_subpath(self) -> None:
        assert RECORDING_ROOT == DATA_DIR / "parquet" / "recording_f0"
        assert RECORDING_ROOT.name == "recording_f0"
        assert RECORDING_ROOT.parent == DATA_DIR / "parquet"

    def test_engine_writes_only_under_recording_root(self, tmp_path) -> None:
        # Snapshot the REAL repo parquet dir to prove it stays untouched.
        legacy_dir = Path("data") / "parquet"
        legacy_before = (
            sorted(str(p) for p in legacy_dir.rglob("*")) if legacy_dir.exists() else []
        )

        data_dir = tmp_path / "data"
        root = data_dir / "parquet" / "recording_f0"
        engine = RecordingEngine(
            linear_symbols=["BTCUSDT"],
            option_underlyings=["BTC"],
            root=root,
            flush_rows=1,
        )
        payload = {
            "topic": "insurance.USDT",
            "ts": 1718000001000,
            "data": [{"coin": "USDT", "balance": "42.0"}],
        }
        spec = next(s for s in engine.specs if s.stream == "insurance_pool")
        engine.record_payload(spec, payload, recv_ts=1718000001.0)
        for writer in engine.writers.values():
            writer.close()

        written = [p for p in data_dir.rglob("*") if p.is_file()]
        assert written, "expected at least one flushed segment"
        for p in written:
            assert root in p.parents, f"file escaped recording_f0 root: {p}"
            assert p.suffix == ".parquet"

        legacy_after = (
            sorted(str(p) for p in legacy_dir.rglob("*")) if legacy_dir.exists() else []
        )
        assert legacy_after == legacy_before, "legacy data/parquet was touched"

    def test_writer_creates_no_files_outside_given_root(self, tmp_path) -> None:
        root = tmp_path / "data" / "parquet" / "recording_f0"
        writer = ParquetStreamWriter("adl_alerts", root=root)
        writer.append({
            "ts": 1, "symbol": "BTCUSDT", "side": "Sell",
            "adl_rank": 1, "raw_json": "{}", "recv_ts": 1.0,
        })
        seg = writer.flush()
        assert root in seg.parents
        outside = [
            p for p in tmp_path.rglob("*")
            if p.is_file() and root not in p.parents
        ]
        assert outside == []
