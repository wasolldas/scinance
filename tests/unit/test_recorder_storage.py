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
from bybit_edge.recorder.storage import (
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
