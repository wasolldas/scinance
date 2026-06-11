"""
WP-2-VERIFY (T0, SANDBOX) — tests for the F0 recorder Sunset-Review logic.

Covers ``src/bybit_edge/recorder/sunset.py``:

* ``is_due()`` boundary behaviour around the 90-day sunset period
  (89 / 90 / 91 days),
* report generation: per-stream volumes (segments / rows / MB) and the
  schema-drift section, incl. drift detection from per-segment
  ``schema_version`` metadata,
* report writing into a tmp report dir (no repo paths touched).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bybit_edge.recorder.storage import (
    SCHEMA_VERSION,
    STREAM_SCHEMAS,
    ParquetStreamWriter,
)
from bybit_edge.recorder.sunset import SUNSET_PERIOD_DAYS, SunsetReviewer

START = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _reviewer(tmp_path, start: datetime = START) -> SunsetReviewer:
    return SunsetReviewer(
        start, root=tmp_path / "recording_f0", report_dir=tmp_path / "results"
    )


def _write_real_segment(root, n_rows: int = 2) -> None:
    """Flush ``n_rows`` insurance rows through the production writer."""
    writer = ParquetStreamWriter("insurance_pool", root=root)
    for i in range(n_rows):
        writer.append({
            "ts": 1718000000000 + i,
            "coin": "USDT",
            "balance": 1.0 + i,
            "recv_ts": 1718000000.0 + i,
        })
    assert writer.flush() is not None


def _write_drifted_segment(root, stream: str = "adl_alerts") -> None:
    """Write a segment whose schema_version metadata differs (drift)."""
    table = pa.table(
        {
            "ts": [1],
            "symbol": ["BTCUSDT"],
            "side": ["Buy"],
            "adl_rank": [1],
            "raw_json": ["{}"],
            "recv_ts": [1.0],
        },
        schema=STREAM_SCHEMAS[stream],
    )
    table = table.replace_schema_metadata({b"schema_version": b"999"})
    seg_dir = root / stream / "2026-03-15"
    seg_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, seg_dir / "seg-1-1.parquet")


# ══════════════════════════════════════════════════════════════════════
# 9a) is_due() boundaries: 89 / 90 / 91 days
# ══════════════════════════════════════════════════════════════════════
class TestIsDue:
    def test_period_is_90_days(self) -> None:
        assert SUNSET_PERIOD_DAYS == 90  # PRD §3/§9: 3-Monats-Sunset

    def test_not_due_at_89_days(self, tmp_path) -> None:
        rev = _reviewer(tmp_path)
        now = START + timedelta(days=89)
        assert rev.days_recorded(now) == pytest.approx(89.0)
        assert rev.is_due(now) is False

    def test_due_exactly_at_90_days(self, tmp_path) -> None:
        rev = _reviewer(tmp_path)
        now = START + timedelta(days=90)
        assert rev.days_recorded(now) == pytest.approx(90.0)
        assert rev.is_due(now) is True

    def test_due_at_91_days(self, tmp_path) -> None:
        rev = _reviewer(tmp_path)
        assert rev.is_due(START + timedelta(days=91)) is True

    def test_just_below_90_days_not_due(self, tmp_path) -> None:
        rev = _reviewer(tmp_path)
        now = START + timedelta(days=90) - timedelta(seconds=1)
        assert rev.is_due(now) is False

    def test_naive_datetimes_treated_as_utc(self, tmp_path) -> None:
        rev = SunsetReviewer(
            START.replace(tzinfo=None),
            root=tmp_path / "recording_f0",
            report_dir=tmp_path / "results",
        )
        assert rev.is_due(START.replace(tzinfo=None) + timedelta(days=90)) is True


# ══════════════════════════════════════════════════════════════════════
# 9b) Report: volumes + schema-drift section
# ══════════════════════════════════════════════════════════════════════
class TestReport:
    def test_stats_volumes_and_drift_flags(self, tmp_path) -> None:
        root = tmp_path / "recording_f0"
        _write_real_segment(root, n_rows=2)      # insurance_pool, version OK
        _write_drifted_segment(root)             # adl_alerts, version 999

        stats = _reviewer(tmp_path).collect_stream_stats()
        # Every declared stream is covered, even empty ones.
        assert set(stats) == set(STREAM_SCHEMAS)

        ins = stats["insurance_pool"]
        assert ins["segments"] == 1
        assert ins["rows"] == 2
        assert ins["bytes"] > 0 and ins["mb"] > 0
        assert ins["schema_versions"] == [SCHEMA_VERSION]
        assert ins["schema_drift"] is False
        assert ins["delivering"] is True
        assert ins["date_span"]  # at least one date partition

        adl = stats["adl_alerts"]
        assert adl["schema_versions"] == [999]
        assert adl["schema_drift"] is True  # != current SCHEMA_VERSION
        assert adl["date_span"] == ["2026-03-15"]

        empty = stats["rpi_orderbook"]
        assert empty["segments"] == 0 and empty["rows"] == 0
        assert empty["delivering"] is False
        assert empty["schema_drift"] is False

    def test_report_contains_volumes_and_drift_section(self, tmp_path) -> None:
        root = tmp_path / "recording_f0"
        _write_real_segment(root, n_rows=2)
        _write_drifted_segment(root)
        rev = _reviewer(tmp_path)
        now = START + timedelta(days=91)

        report = rev.build_report(now)
        # Header facts.
        assert "Sunset-Review" in report
        assert "Review fällig:** JA" in report
        assert f"{rev.period_days} Tage" in report
        # Volume table: every stream is listed with segment/row/MB columns.
        assert "| Stream | liefert Daten | Segmente | Zeilen | MB |" in report
        for stream in STREAM_SCHEMAS:
            assert f"`{stream}`" in report
        assert "| 1 | 2 |" in report  # insurance_pool: 1 segment, 2 rows
        # Schema-drift section flags the drifted stream.
        assert "Schema-Drift erkannt" in report
        assert "`adl_alerts`" in report.split("Schema-Drift erkannt")[1]
        # Due + non-delivering streams are switch-off candidates.
        assert "Abschalt-Kandidaten" in report
        assert "`rpi_orderbook`" in report.split("Abschalt-Kandidaten")[1]
        # Switch-off stays a manual operator decision (no live/money code).
        assert "manuell" in report.lower()

    def test_report_not_due_recommends_no_switch_off(self, tmp_path) -> None:
        root = tmp_path / "recording_f0"
        _write_real_segment(root)
        report = _reviewer(tmp_path).build_report(START + timedelta(days=10))
        assert "Review fällig:** nein" in report
        assert "noch nicht fällig" in report
        assert "Abschalt-Kandidaten" not in report

    def test_due_and_all_delivering_no_candidates(self, tmp_path) -> None:
        root = tmp_path / "recording_f0"
        for stream in STREAM_SCHEMAS:
            # Minimal delivering segment per stream via the real writer.
            writer = ParquetStreamWriter(stream, root=root)
            writer.append({"ts": 1, "recv_ts": 1.0})  # projection fills nulls
            writer.flush()
        report = _reviewer(tmp_path).build_report(START + timedelta(days=120))
        assert "Abschalt-Kandidaten" not in report
        assert "Alle Streams liefern Daten" in report
        assert "Schema-Drift erkannt" not in report

    def test_write_report_lands_in_report_dir_only(self, tmp_path) -> None:
        root = tmp_path / "recording_f0"
        _write_real_segment(root)
        rev = _reviewer(tmp_path)
        now = START + timedelta(days=95)
        path = rev.write_report(now)
        assert path.exists()
        assert path.parent == tmp_path / "results"
        assert path.name == f"sunset_review_recording_{now.strftime('%Y%m%d')}.md"
        assert "Sunset-Review" in path.read_text(encoding="utf-8")
        # Nothing but parquet segments + the one report under tmp_path.
        extra = [
            p for p in tmp_path.rglob("*")
            if p.is_file() and p.suffix not in (".parquet", ".md")
        ]
        assert extra == []
