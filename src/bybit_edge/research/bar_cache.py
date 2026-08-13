"""WP-0 shared 1-minute bar cache — DETERMINISTIC by construction (DEC-34/35).

Wave 6 infrastructure (WELLE6_KANDIDATEN_SYNTHESE §3): one tick pass over the
harvester's ``publicTrade`` history builds immutable per-day 1-minute bars
(last/first price, high/low, buy/sell volume, trade counts) so that every
Wave-6 hypothesis reads a few MB of bars instead of 0.5-1 TB of raw JSONL.

WHY THIS EXISTS (DEC-34): three H-11c runs on identical code and an identical
harvest snapshot produced different daily panels — the raw-tick aggregation
path is NON-deterministic (parallel float summation order, and a tie in
``max_by(price, ts_exchange_ms)`` when two trades share one millisecond).
Registered runs must be reproducible, so Wave 6 reads ONLY from this cache,
whose every column is an ORDER-INDEPENDENT aggregate:

  * ``px_last``/``px_first``  — ``arg_max``/``arg_min`` over the composite
    ordering key ``(ts_exchange_ms, px)``: among trades tying on the
    millisecond, the higher price wins ``px_last`` and the lower wins
    ``px_first`` (deterministic tie-break; when all tying trades carry the
    same price the choice is trivially unique). Scan order cannot matter.
  * ``px_high``/``px_low``    — plain max/min, order-independent.
  * ``vol_buy``/``vol_sell``/``vol_total`` — ``SUM(TRY_CAST(size AS
    DECIMAL(38,12)))``: sizes are cast from their original JSON STRINGS
    straight into exact decimal arithmetic, so the sum is integer-exact and
    commutative — no float association order, no double rounding. Only the
    final total is converted to DOUBLE once.
  * ``n_trades``/``n_buy``/``n_sell``/``n_size_unparsed`` — exact counts.

Both harvester payload forms are read through ``payload_sql.trade_rows_sql``
(flat backfill rows byte-for-byte + live envelopes expanded on the per-trade
timestamp), with the cross-form de-duplication QUALIFY applied — signed
volume sums are exactly the quantity DATASET.md §9 caveat 4 warns about.

IMMUTABILITY + PROVENANCE: a day is written once (parquet + sidecar
``manifest.json`` carrying row count and the SHA-256 of every column's exact
value bytes) and then only ever read back — reproducibility by construction,
re-reads are byte-identical. Days are cached only when the harvest manifest
marks them DONE (a live store may rewrite partial days; freezing one would
persist bad data). ``bars_fingerprint`` returns the range hash that every
Wave-6 registration must quote (DEC-34 point 4).

Loud-fail (GL-018 lesson): a DONE day whose partition holds raw rows but
yields 0 parsable trades raises ``BarCacheError`` instead of writing an
empty bar file.

The cache directory is a NEW path (default ``<repo>/data/barcache``) — it
never writes inside the read-only harvester tree (Schutzgut). Existing
adjudicated hypotheses (H-01..H-18, H-11c) are NOT rewired onto this cache;
their registered read paths stay untouched (DEC-34 point 1).

KAPITALFREI: pure measurement infrastructure. No cost quantity of any kind.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .payload_sql import cross_form_dedup_qualify, trade_rows_sql

#: Bump when the bar definition changes — a cache built by another version
#: is never silently mixed in (the sidecar records it; reads verify it).
SCHEMA_VERSION = 1

MS_PER_MINUTE = 60_000
MINUTES_PER_DAY = 1_440

#: Cached columns in canonical order (also the fingerprint order).
BAR_COLUMNS = (
    "minute_idx",        # int64, epoch minutes (UTC)
    "px_first", "px_last", "px_high", "px_low",   # float64
    "vol_buy", "vol_sell", "vol_total",           # float64 (exact-decimal sums)
    "n_trades", "n_buy", "n_sell", "n_size_unparsed",  # int64
)

#: Price across all dialects (same COALESCE the registered loaders use).
_PX_SQL = ("TRY_CAST(COALESCE(json_extract_string(payload_json,'$.price'),"
           " json_extract_string(payload_json,'$.p')) AS DOUBLE)")

#: Size/qty/amount as the ORIGINAL JSON STRING (bybit size/v, binance qty/q,
#: deribit amount) — cast to DECIMAL only, never through DOUBLE.
_SIZE_STR_SQL = ("COALESCE(json_extract_string(payload_json,'$.size'),"
                 " json_extract_string(payload_json,'$.v'),"
                 " json_extract_string(payload_json,'$.qty'),"
                 " json_extract_string(payload_json,'$.q'),"
                 " json_extract_string(payload_json,'$.amount'))")

#: Normalised aggressor side: 'buy' / 'sell' / NULL (unknown dialect field).
#: binance ``is_buyer_maker``/``m`` = true means the BUYER was the maker,
#: i.e. the aggressor SOLD.
_SIDE_SQL = """CASE
        WHEN lower(COALESCE(json_extract_string(payload_json,'$.side'),
                            json_extract_string(payload_json,'$.S'),
                            json_extract_string(payload_json,'$.direction')))
             IN ('buy','sell')
        THEN lower(COALESCE(json_extract_string(payload_json,'$.side'),
                            json_extract_string(payload_json,'$.S'),
                            json_extract_string(payload_json,'$.direction')))
        WHEN lower(COALESCE(json_extract_string(payload_json,'$.is_buyer_maker'),
                            json_extract_string(payload_json,'$.m'))) = 'true'
        THEN 'sell'
        WHEN lower(COALESCE(json_extract_string(payload_json,'$.is_buyer_maker'),
                            json_extract_string(payload_json,'$.m'))) = 'false'
        THEN 'buy'
        ELSE NULL
    END"""


class BarCacheError(RuntimeError):
    """Loud failure of the bar cache (never a silent empty partition)."""


# ----------------------------------------------------------------------------
# harvest-manifest DONE-day gate (own copy of the DATASET.md §7 query)
# ----------------------------------------------------------------------------

def manifest_done_days(
    base_dir: Path | str, exchange: str, stream: str, symbol: str,
    start: str, end: str,
) -> set[str]:
    """DONE days from ``<base>/state/harvest_manifest.sqlite`` (read-only).

    Raises ``BarCacheError`` when the manifest is missing or unreadable —
    the cache NEVER falls back to a folder scan: freezing a day that the
    harvester has not marked DONE could persist a partial day forever.
    """
    path = Path(base_dir) / "state" / "harvest_manifest.sqlite"
    if not path.is_file():
        raise BarCacheError(
            f"harvest manifest not found: {path} — the bar cache only "
            "freezes manifest-DONE days (no folder-scan fallback)")
    try:
        con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            rows = con.execute(
                "SELECT date FROM partitions "
                "WHERE exchange=? AND stream=? AND symbol=? "
                "AND status='DONE' AND date>=? AND date<=?",
                [exchange, stream, symbol, start, end],
            ).fetchall()
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise BarCacheError(f"harvest manifest unreadable ({path}): {exc}") from exc
    return {r[0] for r in rows}


# ----------------------------------------------------------------------------
# build
# ----------------------------------------------------------------------------

def _day_partition(cache_dir: Path, exchange: str, symbol: str, day: str) -> Path:
    return (cache_dir / "bars_1min" / f"exchange={exchange}"
            / f"symbol={symbol}" / f"date={day}")


def _raw_glob(base: Path, exchange: str, stream: str, symbol: str, day: str) -> str:
    return (base / "raw" / exchange / stream / f"symbol={symbol}"
            / f"date={day}" / "*.parquet").as_posix()


def _bars_hash(arrays: dict[str, np.ndarray]) -> str:
    """SHA-256 over the exact value bytes of all columns, canonical order."""
    h = hashlib.sha256()
    for col in BAR_COLUMNS:
        h.update(col.encode("ascii"))
        h.update(np.ascontiguousarray(arrays[col]).tobytes())
    return h.hexdigest()


def _day_bars_sql(raw_glob: str) -> str:
    trade_rows = trade_rows_sql(
        f"(SELECT * FROM read_parquet('{raw_glob}', hive_partitioning=0,"
        f" union_by_name=1)) AS src")
    return f"""
        WITH trades AS (
            SELECT ts_exchange_ms AS ts,
                   {_PX_SQL} AS px,
                   TRY_CAST({_SIZE_STR_SQL} AS DECIMAL(38,12)) AS sz,
                   {_SIDE_SQL} AS side
            FROM {trade_rows}
            WHERE ts_exchange_ms IS NOT NULL
            {cross_form_dedup_qualify()}
        )
        SELECT CAST(ts // {MS_PER_MINUTE} AS BIGINT)  AS minute_idx,
               arg_min(px, (ts, px))                  AS px_first,
               arg_max(px, (ts, px))                  AS px_last,
               max(px)                                AS px_high,
               min(px)                                AS px_low,
               CAST(COALESCE(sum(sz) FILTER (WHERE side = 'buy'),  0) AS DOUBLE) AS vol_buy,
               CAST(COALESCE(sum(sz) FILTER (WHERE side = 'sell'), 0) AS DOUBLE) AS vol_sell,
               CAST(COALESCE(sum(sz), 0)              AS DOUBLE) AS vol_total,
               count(*)                               AS n_trades,
               count(*) FILTER (WHERE side = 'buy')   AS n_buy,
               count(*) FILTER (WHERE side = 'sell')  AS n_sell,
               count(*) FILTER (WHERE sz IS NULL)     AS n_size_unparsed
        FROM trades
        WHERE px IS NOT NULL AND px > 0.0 AND isfinite(px)
        GROUP BY 1
        ORDER BY 1
    """


def build_day(
    con: Any,
    base_dir: Path | str,
    cache_dir: Path | str,
    exchange: str,
    stream: str,
    symbol: str,
    day: str,
    *,
    rebuild: bool = False,
) -> dict[str, Any]:
    """Build (or skip) ONE day partition. Returns a status dict.

    status: ``cached`` (fresh build) · ``exists`` (immutable skip) ·
    ``no_raw`` (no raw partition on disk). A raw partition with rows but 0
    parsable trades raises ``BarCacheError`` (loud-fail).
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    base, cache = Path(base_dir), Path(cache_dir)
    part = _day_partition(cache, exchange, symbol, day)
    bars_path = part / "bars.parquet"
    meta_path = part / "manifest.json"
    if bars_path.is_file() and meta_path.is_file() and not rebuild:
        return {"day": day, "status": "exists"}

    raw_dir = base / "raw" / exchange / stream / f"symbol={symbol}" / f"date={day}"
    if not list(raw_dir.glob("*.parquet")):
        return {"day": day, "status": "no_raw"}
    glob = _raw_glob(base, exchange, stream, symbol, day)

    n_raw = con.execute(
        f"SELECT count(*) FROM read_parquet('{glob}', union_by_name=1)"
    ).fetchone()[0]
    rows = con.execute(_day_bars_sql(glob)).fetchall()
    if n_raw > 0 and not rows:
        raise BarCacheError(
            f"{exchange}/{stream}/{symbol} {day}: {n_raw} raw rows but 0 "
            "parsable trades — refusing to freeze an empty bar day "
            "(payload dialect? corrupt partition?)")

    cols = list(zip(*rows)) if rows else [[] for _ in BAR_COLUMNS]
    arrays: dict[str, np.ndarray] = {}
    for i, col in enumerate(BAR_COLUMNS):
        dtype = np.int64 if col == "minute_idx" or col.startswith("n_") else np.float64
        arrays[col] = np.asarray(cols[i], dtype=dtype)

    part.mkdir(parents=True, exist_ok=True)
    table = pa.table({
        col: pa.array(arrays[col],
                      pa.int64() if arrays[col].dtype == np.int64 else pa.float64())
        for col in BAR_COLUMNS
    })
    pq.write_table(table, bars_path)
    meta = {
        "schema_version": SCHEMA_VERSION,
        "exchange": exchange, "stream": stream, "symbol": symbol, "date": day,
        "n_minutes": int(len(rows)),
        "n_trades_day": int(arrays["n_trades"].sum()) if len(rows) else 0,
        "n_size_unparsed_day": int(arrays["n_size_unparsed"].sum()) if len(rows) else 0,
        "sha256_values": _bars_hash(arrays),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "raw_rows_scanned": int(n_raw),
        "columns": list(BAR_COLUMNS),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"day": day, "status": "cached", "n_minutes": len(rows),
            "sha256_values": meta["sha256_values"]}


def build_range(
    base_dir: Path | str,
    cache_dir: Path | str,
    exchange: str,
    stream: str,
    symbol: str,
    start: str,
    end: str,
    *,
    rebuild: bool = False,
    require_manifest_done: bool = True,
    progress: Any = None,
) -> dict[str, Any]:
    """Build every manifest-DONE day of ``[start, end]`` incrementally.

    ``require_manifest_done=False`` exists ONLY for synthetic-fixture tests.
    Returns a summary dict (counts per status + the days skipped as not-DONE).
    """
    import duckdb

    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    if d1 < d0:
        raise ValueError(f"end {end} before start {start}")
    all_days = [(d0 + timedelta(days=i)).isoformat()
                for i in range((d1 - d0).days + 1)]
    if require_manifest_done:
        done = manifest_done_days(base_dir, exchange, stream, symbol, start, end)
        days = [d for d in all_days if d in done]
    else:
        days = all_days

    counts = {"cached": 0, "exists": 0, "no_raw": 0}
    con = duckdb.connect()
    try:
        for day in days:
            res = build_day(con, base_dir, cache_dir, exchange, stream,
                            symbol, day, rebuild=rebuild)
            counts[res["status"]] += 1
            if progress is not None:
                progress(symbol, res)
    finally:
        con.close()
    return {
        "symbol": symbol, "exchange": exchange, "stream": stream,
        "range": [start, end],
        "days_in_range": len(all_days),
        "days_manifest_done": len(days),
        "days_not_done": len(all_days) - len(days),
        **counts,
    }


# ----------------------------------------------------------------------------
# read + fingerprint
# ----------------------------------------------------------------------------

def load_minute_bars(
    cache_dir: Path | str,
    exchange: str,
    symbol: str,
    start: str,
    end: str,
) -> dict[str, np.ndarray]:
    """Read cached bars for ``[start, end]`` as numpy arrays (canonical order).

    Reads ONLY the cache (never the raw tree). Sidecar-less or version-alien
    partitions raise — a half-written day must never be silently served.
    Missing days are simply absent from the arrays (the caller decides what
    a gap means for its hypothesis).
    """
    cache = Path(cache_dir)
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    frames: list[dict[str, np.ndarray]] = []
    for i in range((d1 - d0).days + 1):
        day = (d0 + timedelta(days=i)).isoformat()
        part = _day_partition(cache, exchange, symbol, day)
        bars_path = part / "bars.parquet"
        if not bars_path.is_file():
            continue
        meta_path = part / "manifest.json"
        if not meta_path.is_file():
            raise BarCacheError(f"cache partition without sidecar: {part}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("schema_version") != SCHEMA_VERSION:
            raise BarCacheError(
                f"{part}: schema_version {meta.get('schema_version')} != "
                f"{SCHEMA_VERSION} — rebuild required, never mixed")
        import pyarrow.parquet as pq
        table = pq.read_table(bars_path, columns=list(BAR_COLUMNS))
        frames.append({col: table.column(col).to_numpy(zero_copy_only=False)
                       for col in BAR_COLUMNS})
    if not frames:
        return {col: np.empty(0, dtype=np.int64 if col == "minute_idx"
                              or col.startswith("n_") else np.float64)
                for col in BAR_COLUMNS}
    return {col: np.concatenate([f[col] for f in frames]) for col in BAR_COLUMNS}


def bars_fingerprint(
    cache_dir: Path | str,
    exchange: str,
    symbol: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    """Range fingerprint every Wave-6 registration must quote (DEC-34).

    SHA-256 over the exact value bytes of all columns across the range, plus
    coverage counts. Forensic only — NEVER a gate flag (a single last-bit
    change flips it; as a validity switch it would be unusable, as a change
    detector it is ideal).
    """
    bars = load_minute_bars(cache_dir, exchange, symbol, start, end)
    n_days = int(np.unique(bars["minute_idx"] * MS_PER_MINUTE
                           // 86_400_000).size) if bars["minute_idx"].size else 0
    return {
        "schema_version": SCHEMA_VERSION,
        "exchange": exchange, "symbol": symbol, "range": [start, end],
        "n_minutes": int(bars["minute_idx"].size),
        "n_days_present": n_days,
        "sha256_values": _bars_hash(bars),
    }


__all__ = [
    "BAR_COLUMNS",
    "BarCacheError",
    "SCHEMA_VERSION",
    "bars_fingerprint",
    "build_day",
    "build_range",
    "load_minute_bars",
    "manifest_done_days",
]
