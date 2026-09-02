"""WP-7 -- ``panel_1d`` store: year partitions, manifest, fingerprints.

Year- (not day-) partitions (spec section 2: day-partitions would be 3.3M
directories for ~1000 symbols x 5.5 years): ``panel_1d/{frozen,open}/
source=bybit/category=linear/symbol=<S>/year=<YYYY>/part.parquet``.

``frozen/`` holds COMPLETED years -- immutable once written, fingerprint-
bearing. ``open/`` holds the CURRENT (in-progress) year -- may be
rewritten; a judgement-bearing run uses only ``frozen/`` years OR pins the
``open/`` fingerprint at run time and quotes it (PRD 4.1, C.19).

``panel_manifest.sqlite`` (own file, distinct from the WP-0 bar-cache
manifest and from the harvester's manifest) carries one row per
``(symbol, year)`` with ``status in {DONE, PARTIAL, EMPTY, FAILED}``.
**DONE requires ``n_rows == expected_days``** (calendar days from the
listing date -- or year start, whichever is later -- through year end, or
``as_of_date`` for the still-open year); any mismatch is recorded as
PARTIAL, never silently upgraded (loud-fail lives in ``require_all_done``,
called by any judgement-bearing reader).

Fingerprints mirror ``bar_cache.py``'s DEC-34 discipline: SHA-256 over the
EXACT value bytes of every column, canonical order, per (symbol, year);
plus a range fingerprint over (symbol set, year range) that every
registration cites.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import struct
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "SCHEMA_VERSION", "PANEL_COLUMNS", "PanelStoreError",
    "partition_path", "expected_days_in_year", "write_year_partition",
    "open_manifest", "manifest_get", "manifest_status_counts",
    "require_all_done", "panel_fingerprint", "range_fingerprint",
    "reverify_sample", "daily_funding_stats", "merge_funding_daily",
    "listing_date_from_launch_time",
]

SCHEMA_VERSION = 2

#: Canonical column order -- also the fingerprint order. ``funding_n``/
#: ``funding_sum`` are the spec's mandatory funding columns (1h- vs
#: 8h-funding-symbol tagging, PRD 4.1 "sonst addiert man Aepfel und
#: Birnen"; ``funding_sum`` additionally feeds A1): ``funding_n`` = number
#: of settlements observed for that symbol-UTC-day, ``funding_sum`` = sum
#: of their rates. Populated by ``merge_funding_daily`` from
#: ``bybit_rest.fetch_funding_history`` (Nacharbeit #1); a caller that
#: never fetched funding history leaves both ``None`` (never silently 0).
PANEL_COLUMNS: tuple[str, ...] = (
    "start_ms", "open", "high", "low", "close", "volume", "turnover",
    "funding_n", "funding_sum",
)


class PanelStoreError(RuntimeError):
    """Loud failure of the panel_1d store (never a silent partial write,
    never a silent DONE-status lie, never an overwritten frozen year)."""


def partition_path(base_dir: Path | str, symbol: str, year: int, *,
                    frozen: bool) -> Path:
    tree = "frozen" if frozen else "open"
    return (Path(base_dir) / tree / "source=bybit" / "category=linear"
            / f"symbol={symbol}" / f"year={year}" / "part.parquet")


def expected_days_in_year(year: int, listing_date: date, as_of_date: date) -> int:
    """Calendar days a symbol should carry a daily bar within ``year``.

    Bybit perps trade 24/7 (no exchange holidays) -- expected coverage is
    the intersection of ``[listing_date, as_of_date]`` with the calendar
    year. Returns 0 if the symbol had not listed yet, or the intersection
    is empty (e.g. ``as_of_date`` before the year starts).
    """
    lo = max(date(year, 1, 1), listing_date)
    hi = min(date(year, 12, 31), as_of_date)
    if hi < lo:
        return 0
    return (hi - lo).days + 1


#: The two funding columns are appended after the price/volume float
#: columns and hashed with their own explicit null-sentinel handling (see
#: below) -- everything strictly between ``start_ms`` and them is a plain
#: non-nullable float64.
_FLOAT_COLUMNS: tuple[str, ...] = PANEL_COLUMNS[1:-2]  # open..turnover


def _rows_hash(rows: list[dict[str, Any]]) -> str:
    """SHA-256 over exact value bytes, canonical column order, rows sorted
    by ``start_ms`` (order-independent by construction, mirrors
    ``bar_cache._bars_hash``)."""
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda r: r["start_ms"]):
        h.update(struct.pack("<q", int(r["start_ms"])))
        for col in _FLOAT_COLUMNS:
            h.update(struct.pack("<d", float(r[col])))
        fn = r.get("funding_n")
        h.update(struct.pack("<q", -1 if fn is None else int(fn)))
        fs = r.get("funding_sum")
        h.update(struct.pack("<d", float("nan") if fs is None else float(fs)))
    return h.hexdigest()


def write_year_partition(
    base_dir: Path | str, manifest_path: Path | str,
    symbol: str, year: int, rows: list[dict[str, Any]], *,
    listing_date: date, as_of_date: date, frozen: bool,
    allow_overwrite: bool = False,
) -> dict[str, Any]:
    """Write one (symbol, year) partition + record its manifest status.

    ``rows``: dicts carrying at least ``start_ms, open, high, low, close,
    volume, turnover`` (``funding_n``/``funding_sum`` optional, default
    ``None`` -- populate them first via ``merge_funding_daily``).
    Refuses (``PanelStoreError``) to overwrite an existing FROZEN partition
    unless ``allow_overwrite=True`` -- frozen years are immutable by
    construction (spec section 2).
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = partition_path(base_dir, symbol, year, frozen=frozen)
    if frozen and path.is_file() and not allow_overwrite:
        raise PanelStoreError(
            f"refusing to overwrite FROZEN partition {path} "
            "(frozen years are immutable -- pass allow_overwrite=True "
            "only for a deliberate, audited rebuild)")
    path.parent.mkdir(parents=True, exist_ok=True)

    clean_rows = [dict(r, funding_n=r.get("funding_n"), funding_sum=r.get("funding_sum"))
                  for r in rows]
    clean_rows.sort(key=lambda r: r["start_ms"])
    table = pa.table({
        "start_ms": pa.array([r["start_ms"] for r in clean_rows], pa.int64()),
        **{col: pa.array([r[col] for r in clean_rows], pa.float64())
           for col in _FLOAT_COLUMNS},
        "funding_n": pa.array([r["funding_n"] for r in clean_rows], pa.int64()),
        "funding_sum": pa.array([r["funding_sum"] for r in clean_rows], pa.float64()),
    })
    pq.write_table(table, path)

    n_rows = len(clean_rows)
    expected = expected_days_in_year(year, listing_date, as_of_date)
    if n_rows == 0:
        status = "EMPTY"
    elif n_rows == expected:
        status = "DONE"
    else:
        status = "PARTIAL"
    fp = _rows_hash(clean_rows) if clean_rows else None

    con = open_manifest(manifest_path)
    try:
        con.execute(
            "INSERT INTO partitions (symbol, year, status, n_rows, "
            "expected_days, sha256, frozen, updated_at) VALUES "
            "(?,?,?,?,?,?,?,?) ON CONFLICT(symbol, year) DO UPDATE SET "
            "status=excluded.status, n_rows=excluded.n_rows, "
            "expected_days=excluded.expected_days, sha256=excluded.sha256, "
            "frozen=excluded.frozen, updated_at=excluded.updated_at",
            (symbol, year, status, n_rows, expected, fp, int(frozen),
             datetime.now(timezone.utc).isoformat(timespec="seconds")))
        con.commit()
    finally:
        con.close()
    return {"symbol": symbol, "year": year, "status": status, "n_rows": n_rows,
            "expected_days": expected, "sha256": fp, "path": str(path)}


def mark_failed(manifest_path: Path | str, symbol: str, year: int,
                 reason: str) -> None:
    """Record a FAILED partition (e.g. a REST error mid-fetch) -- no
    parquet is written; the manifest alone remembers the failure so a
    retry knows what's missing."""
    con = open_manifest(manifest_path)
    try:
        con.execute(
            "INSERT INTO partitions (symbol, year, status, n_rows, "
            "expected_days, sha256, frozen, updated_at, failure_reason) "
            "VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(symbol, year) DO UPDATE "
            "SET status=excluded.status, failure_reason=excluded.failure_reason, "
            "updated_at=excluded.updated_at",
            (symbol, year, "FAILED", 0, 0, None, 0,
             datetime.now(timezone.utc).isoformat(timespec="seconds"), reason))
        con.commit()
    finally:
        con.close()


# ----------------------------------------------------------------------------
# funding_n / funding_sum (Nacharbeit #1)
# ----------------------------------------------------------------------------

def daily_funding_stats(funding_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group ``bybit_rest.fetch_funding_history`` rows (``{symbol,
    funding_rate, ts_ms}``) into per-UTC-day ``{funding_n, funding_sum}``.

    ``funding_n`` = count of settlements that UTC day (3/day for an 8h-
    funding symbol, 24/day for a 1h-funding symbol -- Bybit runs both,
    and a symbol's own interval can change mid-history, which this
    function handles for free: it counts the REAL observed timestamps,
    no interval assumed or hard-coded anywhere). ``funding_sum`` = sum of
    that day's rates (A1 input).
    """
    out: dict[str, dict[str, Any]] = {}
    for r in funding_rows:
        day = datetime.fromtimestamp(r["ts_ms"] / 1000.0, tz=timezone.utc).date().isoformat()
        bucket = out.setdefault(day, {"funding_n": 0, "funding_sum": 0.0})
        bucket["funding_n"] += 1
        bucket["funding_sum"] += r["funding_rate"]
    return out


def merge_funding_daily(rows: list[dict[str, Any]],
                         funding_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach ``funding_n``/``funding_sum`` to daily kline ``rows`` (each
    carrying ``start_ms``) by UTC day. A day with funding history fetched
    but genuinely zero settlements gets ``funding_n=0`` (measured zero,
    should not happen in practice but is not the same as "never fetched")
    -- ``write_year_partition``'s own default (``None``, "never
    populated") only applies when this function is never called at all.
    """
    stats = daily_funding_stats(funding_rows)
    out = []
    for r in rows:
        day = datetime.fromtimestamp(r["start_ms"] / 1000.0, tz=timezone.utc).date().isoformat()
        st = stats.get(day, {"funding_n": 0, "funding_sum": 0.0})
        out.append({**r, "funding_n": st["funding_n"], "funding_sum": st["funding_sum"]})
    return out


# ----------------------------------------------------------------------------
# listing_date (Nacharbeit #3)
# ----------------------------------------------------------------------------

def listing_date_from_launch_time(launch_time_ms: Any) -> date:
    """Instruments-info's ``launchTime`` (epoch ms, as a numeric string)
    -> the instrument's real UTC listing date. Nacharbeit #3: replaces the
    year-start approximation ``--fetch`` used before -- ``launchTime`` is
    the real anchor ``expected_days_in_year`` needs to avoid inflating a
    symbol's first partial year into a false PARTIAL/DONE mismatch.

    Loud-fail (``PanelStoreError``) on a missing/non-numeric/non-positive
    value -- a caller with no usable ``launchTime`` must pick its own
    documented fallback explicitly (e.g. year start for a pre-launchTime-
    era symbol), never silently get one here.
    """
    if launch_time_ms in (None, "", "0", 0):
        raise PanelStoreError(f"no usable launchTime: {launch_time_ms!r}")
    try:
        ms = int(launch_time_ms)
    except (TypeError, ValueError) as exc:
        raise PanelStoreError(f"launchTime not numeric: {launch_time_ms!r}") from exc
    if ms <= 0:
        raise PanelStoreError(f"launchTime not positive: {launch_time_ms!r}")
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).date()


# ----------------------------------------------------------------------------
# manifest
# ----------------------------------------------------------------------------

def open_manifest(manifest_path: Path | str) -> sqlite3.Connection:
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.execute(
        "CREATE TABLE IF NOT EXISTS partitions ("
        " symbol TEXT NOT NULL, year INTEGER NOT NULL, status TEXT NOT NULL,"
        " n_rows INTEGER NOT NULL, expected_days INTEGER NOT NULL,"
        " sha256 TEXT, frozen INTEGER NOT NULL, updated_at TEXT NOT NULL,"
        " failure_reason TEXT,"
        " PRIMARY KEY (symbol, year))")
    con.commit()
    return con


def manifest_get(manifest_path: Path | str, symbol: str, year: int) -> dict[str, Any] | None:
    con = sqlite3.connect(f"file:{Path(manifest_path).as_posix()}?mode=ro", uri=True)
    try:
        row = con.execute(
            "SELECT symbol, year, status, n_rows, expected_days, sha256, "
            "frozen, updated_at, failure_reason FROM partitions "
            "WHERE symbol=? AND year=?", (symbol, year)).fetchone()
    finally:
        con.close()
    if row is None:
        return None
    keys = ("symbol", "year", "status", "n_rows", "expected_days", "sha256",
            "frozen", "updated_at", "failure_reason")
    return dict(zip(keys, row))


def manifest_status_counts(manifest_path: Path | str) -> dict[str, int]:
    con = sqlite3.connect(f"file:{Path(manifest_path).as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT status, count(*) FROM partitions GROUP BY status").fetchall()
    finally:
        con.close()
    return {s: n for s, n in rows}


def require_all_done(manifest_path: Path | str, symbols: list[str],
                      years: list[int]) -> None:
    """Loud-fail gate for judgement-bearing reads (PRD 4.1 DoD point 2):
    raises ``PanelStoreError`` naming every ``(symbol, year)`` that is
    missing from the manifest or not DONE. A census must call this before
    trusting ``panel_1d`` data."""
    con = sqlite3.connect(f"file:{Path(manifest_path).as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT symbol, year, status FROM partitions").fetchall()
    finally:
        con.close()
    have = {(s, y): st for s, y, st in rows}
    bad = []
    for s in symbols:
        for y in years:
            st = have.get((s, y))
            if st != "DONE":
                bad.append((s, y, st or "MISSING"))
    if bad:
        detail = ", ".join(f"{s}/{y}={st}" for s, y, st in bad[:20])
        more = f" (+{len(bad) - 20} more)" if len(bad) > 20 else ""
        raise PanelStoreError(
            f"{len(bad)} partition(s) not DONE -- refusing a judgement-"
            f"bearing read: {detail}{more}")


# ----------------------------------------------------------------------------
# fingerprints
# ----------------------------------------------------------------------------

def panel_fingerprint(base_dir: Path | str, symbol: str, year: int, *,
                       frozen: bool) -> str:
    """SHA-256 over the exact value bytes of ``(symbol, year)`` -- the
    per-partition figure every registration that cites WP-7's panel must
    be able to reproduce. Forensic only, never a gate flag (DEC-34 point
    4's rationale applies identically here)."""
    import pyarrow.parquet as pq

    path = partition_path(base_dir, symbol, year, frozen=frozen)
    if not path.is_file():
        raise PanelStoreError(f"no partition at {path}")
    table = pq.read_table(path, columns=list(PANEL_COLUMNS))
    cols = table.to_pydict()
    rows = [dict(zip(PANEL_COLUMNS, vals)) for vals in zip(*[cols[c] for c in PANEL_COLUMNS])]
    return _rows_hash(rows)


def range_fingerprint(base_dir: Path | str, symbols: list[str],
                       year_start: int, year_end: int, *, frozen: bool) -> dict[str, Any]:
    """Range fingerprint over (Symbolmenge, Jahresbereich) -- SHA-256 over
    the sorted symbol set, the year range, and every per-partition
    fingerprint in canonical (symbol, year) order."""
    h = hashlib.sha256()
    sorted_symbols = sorted(set(symbols))
    h.update(json.dumps(sorted_symbols).encode("utf-8"))
    h.update(struct.pack("<qq", year_start, year_end))
    per_partition: dict[str, str] = {}
    for s in sorted_symbols:
        for y in range(year_start, year_end + 1):
            path = partition_path(base_dir, s, y, frozen=frozen)
            if not path.is_file():
                continue
            fp = panel_fingerprint(base_dir, s, y, frozen=frozen)
            per_partition[f"{s}/{y}"] = fp
            h.update(f"{s}/{y}".encode("utf-8"))
            h.update(fp.encode("ascii"))
    return {"symbols": sorted_symbols, "year_range": [year_start, year_end],
            "n_partitions": len(per_partition),
            "sha256": h.hexdigest(), "per_partition": per_partition}


def reverify_sample(base_dir: Path | str, manifest_path: Path | str, *,
                     fraction: float = 0.01, seed: int | None = None) -> dict[str, Any]:
    """Provenance check (PRD 4.1): re-draw a ``fraction`` random sample of
    FROZEN DONE partitions, recompute their fingerprint from the parquet
    on disk, and compare against the manifest's stored value. A mismatch
    is a LOUD alarm (returned, never silently swallowed) -- the caller
    (CLI ``--reverify``) is expected to surface it prominently.
    """
    import random

    con = sqlite3.connect(f"file:{Path(manifest_path).as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT symbol, year, sha256 FROM partitions "
            "WHERE status='DONE' AND frozen=1").fetchall()
    finally:
        con.close()
    if not rows:
        return {"n_checked": 0, "n_mismatch": 0, "mismatches": [],
                "note": "no FROZEN DONE partitions to reverify"}
    rng = random.Random(seed)
    n_sample = max(1, round(len(rows) * fraction))
    sample = rng.sample(rows, min(n_sample, len(rows)))
    mismatches = []
    for symbol, year, stored_fp in sample:
        actual_fp = panel_fingerprint(base_dir, symbol, year, frozen=True)
        if actual_fp != stored_fp:
            mismatches.append({"symbol": symbol, "year": year,
                                "stored_sha256": stored_fp, "actual_sha256": actual_fp})
    return {"n_checked": len(sample), "n_mismatch": len(mismatches),
            "mismatches": mismatches}
