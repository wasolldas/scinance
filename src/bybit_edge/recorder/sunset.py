"""
Sunset-Review logic for the F0 Recording-Engine (C-36).

FINAL_PRD §3 (Pilot 3) / §9 mandate a **Sunset-Review every 3 months**: for
each recorded stream, check whether a recording-dependent pilot actually uses
it; unused streams get switched off (Anti-Data-Lake, microstr S-A1). The first
sunset falls 3 months after the recording start.

This module is the *reporting* half: given the recording start date and the
recording root, it inspects each stream's segments (volume, segment count,
date span, schema-version drift) and writes a Markdown review report to
``handoff_local/results/``. Switching a stream off stays MANUAL / config-side
(no money / no live-order code) — the report only flags candidates.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pyarrow.parquet as pq

from bybit_edge.recorder.storage import (
    RECORDING_ROOT,
    SCHEMA_VERSION,
    STREAM_SCHEMAS,
)

logger = logging.getLogger(__name__)

# 3-month sunset period (PRD §3/§9 — "Sunset-Review nach 3 Monaten").
SUNSET_PERIOD_DAYS: int = 90

# Default destination for the review report (Deutsch-Doku convention, but the
# directory is the standard handoff results sink — gate-auditor reads here).
DEFAULT_REPORT_DIR: Path = Path("handoff_local/results")


def _segment_files(stream_dir: Path) -> list[Path]:
    if not stream_dir.exists():
        return []
    return [p for p in stream_dir.rglob("*.parquet") if p.is_file()]


def _read_schema_version(path: Path) -> Optional[int]:
    """Read the ``schema_version`` from a segment's Parquet metadata."""
    try:
        meta = pq.read_metadata(path).metadata or {}
        raw = meta.get(b"schema_version")
        return int(raw) if raw is not None else None
    except Exception:
        return None


class SunsetReviewer:
    """Generates the periodic Sunset-Review report over recorded streams."""

    def __init__(
        self,
        start_date: datetime,
        root: Path = RECORDING_ROOT,
        period_days: int = SUNSET_PERIOD_DAYS,
        report_dir: Path = DEFAULT_REPORT_DIR,
    ) -> None:
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        self.start_date = start_date
        self.root = Path(root)
        self.period_days = period_days
        self.report_dir = Path(report_dir)

    # ------------------------------------------------------------------
    def days_recorded(self, now: Optional[datetime] = None) -> float:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return (now - self.start_date).total_seconds() / 86400.0

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """True once the recording has run at least ``period_days``."""
        return self.days_recorded(now) >= self.period_days

    # ------------------------------------------------------------------
    def collect_stream_stats(self) -> dict[str, dict[str, Any]]:
        """Per-stream volume / segment / date-span / schema-drift stats."""
        stats: dict[str, dict[str, Any]] = {}
        for stream in STREAM_SCHEMAS:
            stream_dir = self.root / stream
            segments = _segment_files(stream_dir)
            total_bytes = 0
            total_rows = 0
            versions: set[int] = set()
            dates: set[str] = set()
            for seg in segments:
                try:
                    total_bytes += seg.stat().st_size
                except OSError:
                    pass
                ver = _read_schema_version(seg)
                if ver is not None:
                    versions.add(ver)
                try:
                    total_rows += pq.read_metadata(seg).num_rows
                except Exception:
                    pass
                # root/{stream}/{date}/seg-*.parquet
                try:
                    dates.add(seg.relative_to(stream_dir).parts[0])
                except ValueError:
                    pass
            stats[stream] = {
                "segments": len(segments),
                "rows": total_rows,
                "bytes": total_bytes,
                "mb": round(total_bytes / 1024 ** 2, 3),
                "date_span": sorted(dates),
                "schema_versions": sorted(versions),
                "schema_drift": len(versions) > 1
                or (bool(versions) and versions != {SCHEMA_VERSION}),
                "delivering": total_rows > 0,
            }
        return stats

    # ------------------------------------------------------------------
    def build_report(self, now: Optional[datetime] = None) -> str:
        """Render the Sunset-Review report as Markdown (Deutsch)."""
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        days = self.days_recorded(now)
        stats = self.collect_stream_stats()

        lines: list[str] = []
        lines.append(f"# Sunset-Review — F0 Recording-Engine (C-36)")
        lines.append("")
        lines.append(f"- **Erstellt:** {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append(f"- **Recording-Start:** {self.start_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append(f"- **Aufzeichnungsdauer:** {days:.1f} Tage")
        lines.append(f"- **Sunset-Periode (PRD §3/§9):** {self.period_days} Tage")
        lines.append(f"- **Review fällig:** {'JA' if self.is_due(now) else 'nein'}")
        lines.append("")
        lines.append("## Streams")
        lines.append("")
        lines.append(
            "| Stream | liefert Daten | Segmente | Zeilen | MB | Datums-Span | Schema-Versionen | Drift |"
        )
        lines.append(
            "|---|---|---|---|---|---|---|---|"
        )
        for stream, s in stats.items():
            span = (
                f"{s['date_span'][0]}…{s['date_span'][-1]}"
                if s["date_span"] else "—"
            )
            lines.append(
                f"| `{stream}` | {'ja' if s['delivering'] else '**NEIN**'} "
                f"| {s['segments']} | {s['rows']} | {s['mb']} | {span} "
                f"| {s['schema_versions'] or '—'} "
                f"| {'**JA**' if s['schema_drift'] else 'nein'} |"
            )
        lines.append("")

        # Sunset candidates: due + not delivering = recommend switch-off.
        non_delivering = [k for k, v in stats.items() if not v["delivering"]]
        drifted = [k for k, v in stats.items() if v["schema_drift"]]
        lines.append("## Empfehlung")
        lines.append("")
        if not self.is_due(now):
            lines.append(
                f"- Review noch nicht fällig ({days:.1f} < {self.period_days} Tage). "
                "Keine Stream-Abschaltung."
            )
        elif non_delivering:
            lines.append(
                "- **Abschalt-Kandidaten (kein Stream-relevanter Datenfluss):** "
                + ", ".join(f"`{s}`" for s in non_delivering)
                + ". Abschaltung manuell/per Config (kein Live-/Geld-Code)."
            )
        else:
            lines.append("- Alle Streams liefern Daten — keine Abschaltung empfohlen.")
        if drifted:
            lines.append(
                "- **Schema-Drift erkannt** in: "
                + ", ".join(f"`{s}`" for s in drifted)
                + " — Schema-Versionen je Segment prüfen."
            )
        lines.append("")
        lines.append("*Ende Sunset-Review — Abschaltung bleibt manuelle Operator-Entscheidung.*")
        return "\n".join(lines) + "\n"

    def write_report(self, now: Optional[datetime] = None) -> Path:
        """Write the Markdown report to ``handoff_local/results/`` and return its path."""
        now = now or datetime.now(timezone.utc)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        stamp = now.strftime("%Y%m%d")
        path = self.report_dir / f"sunset_review_recording_{stamp}.md"
        path.write_text(self.build_report(now), encoding="utf-8")
        logger.info("Sunset-Review report written to %s", path)
        return path
