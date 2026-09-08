"""WP-10(A) -- daily premium-proxy series loaders (KAPITALFREI, read-only).

Three series types (spec Teil A "Eingang"), each returned in ONE canonical
shape (see ``_series``) with provenance + coverage, so ``coherence.py``
can treat them uniformly:

  * ``funding_daily_cashflow``  -- SUM of ``bybit/rest.fundingRate`` per
    UTC day, bucketed by the payload's OWN ``fundingRateTimestamp`` field
    (not the harvest partition's ``date=`` column -- the spec names the
    payload fields explicitly). Field names [sek]: ``fundingRate``,
    ``fundingRateTimestamp``. Loud-fail (``SeriesError``) the moment ANY
    row in a present partition is missing either field -- never a silent
    drop or a cross-exchange fallback guess (unlike ``c10_pointer`` /
    ``c11_anen``'s Binance-fallback loaders, this stream is Bybit-only by
    construction, so there is no legitimate alternate field name to fall
    back to).
  * ``iv_rv_diff_series``  -- ``deribit/dvol`` daily close (via
    ``wp9_dvol.harvest_close``, reused verbatim) minus WP-0 realized vol
    (``rv.py``), BOTH annualized with the SAME day-count convention
    (``rv.ANNUALIZATION_DAYS_PER_YEAR``).
  * ``perp_basis_proxy_series``  -- ``bybit/tickers`` markPrice vs.
    indexPrice, PROBE-FIRST: ``probe_perp_basis`` is always run before any
    aggregate query, and the series is SKIPPED (loud, status field, never
    raised) when the fields don't clear the coverage threshold -- spec:
    "soweit vorhanden". DELTA-STREAM LAYOUT [sek]: harvested
    ``bybit/tickers`` frames are WS DELTAS -- each payload carries only the
    fields that CHANGED, so ``markPrice`` and ``indexPrice`` typically show
    up in DIFFERENT frames, never both in the frame with the highest
    ``ts_exchange_ms``. The daily basis therefore uses STATEFUL
    last-known-value semantics: per UTC day, the LAST frame containing
    ``markPrice`` and (separately) the LAST frame containing ``indexPrice``
    -- exactly how a live ticker consumer would reconstruct current state
    from a delta stream. A day counts toward coverage only when BOTH
    last-known values are present; the series is OK when that holds for
    >=50% of the symbol's harvested days, else SKIPPED with the measured
    fraction (still optional -- see ``probe_perp_basis``).

KAPITALFREI: pure data loading. No cost quantity, no PASS/FAIL.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bybit_edge.research.bar_cache import load_minute_bars
from bybit_edge.research.wp9_dvol import harvest_close as _dvol

from . import rv as _rv

__all__ = [
    "SeriesError",
    "FUNDING_STREAM", "FUNDING_FIELD_RATE", "FUNDING_FIELD_TS",
    "PERP_BASIS_STREAM", "PERP_BASIS_FIELD_MARK", "PERP_BASIS_FIELD_INDEX",
    "probe_funding", "funding_daily_cashflow",
    "iv_rv_diff_series",
    "probe_perp_basis", "perp_basis_proxy_series",
]

FUNDING_STREAM = "rest.fundingRate"
#: [sek] -- Bybit REST funding payload field names (DATASET.md sec 6 / the
#: c10_pointer/c11_anen Bybit-form convention). No cross-exchange fallback
#: here: this stream is Bybit-only, so a missing field is a real drift.
FUNDING_FIELD_RATE = "fundingRate"
FUNDING_FIELD_TS = "fundingRateTimestamp"

PERP_BASIS_STREAM = "tickers"
#: [sek] -- confirmed against a real harvest tree: bybit/tickers frames are
#: WS deltas, e.g. ``{"topic":"tickers.BTCUSDT","type":"delta",
#: "data":{"symbol":"BTCUSDT","ask1Price":"...","markPrice":"..."},...}``
#: -- markPrice/indexPrice appear NESTED under ``data`` on real frames, but
#: ``_extract_field`` also accepts a bare top-level field for tolerance.
PERP_BASIS_FIELD_MARK = "markPrice"
PERP_BASIS_FIELD_INDEX = "indexPrice"
#: Minimum fraction of a symbol's harvested days that must carry a
#: last-known value for BOTH fields for the series to be reported OK
#: instead of skipped (spec: "soweit vorhanden" -- optional, never fatal).
PERP_BASIS_MIN_DAY_COVERAGE = 0.5


class SeriesError(RuntimeError):
    """Loud failure: a WP-10(A) series source does not match its [sek] layout."""


def _series(name: str, kind: str, symbol: str, provenance: dict[str, Any],
           days_values: dict[str, float], *, status: str = "OK",
           reason: str | None = None) -> dict[str, Any]:
    days = sorted(days_values)
    values = [days_values[d] for d in days]
    return {
        "name": name, "kind": kind, "symbol": symbol, "provenance": provenance,
        "days": days, "values": values,
        "coverage": {"n_days": len(days), "first": days[0] if days else None,
                    "last": days[-1] if days else None},
        "status": status, "reason": reason,
    }


# --------------------------------------------------------------- funding

def _funding_partition_root(base: Path, symbol: str) -> Path:
    return base / "raw" / "bybit" / FUNDING_STREAM / f"symbol={symbol}"


def _funding_glob(base: Path, symbol: str) -> str:
    return str(_funding_partition_root(base, symbol) / "date=*" / "*.parquet")


def probe_funding(con: Any, base_dir: Path | str, symbol: str) -> dict[str, Any]:
    """Probe ONE funding symbol: presence + [sek] field-layout check.

    Never raises on a missing field itself -- returns a status dict, so
    ``--probe`` and ``funding_daily_cashflow`` share the exact same check
    without duplicating the DuckDB query (mirrors ``wp9_dvol.harvest_close.
    probe_day``).
    """
    base = Path(base_dir)
    root = _funding_partition_root(base, symbol)
    if not root.is_dir() or not any(root.glob("date=*/*.parquet")):
        return {"symbol": symbol, "status": "NO_PARTITIONS"}
    glob = _funding_glob(base, symbol)
    try:
        row = con.execute(f"""
            SELECT count(*) AS n,
                   count(*) FILTER (
                       WHERE json_extract_string(payload_json,'$.{FUNDING_FIELD_TS}') IS NULL
                          OR json_extract_string(payload_json,'$.{FUNDING_FIELD_RATE}') IS NULL
                   ) AS n_missing,
                   arg_max(payload_json, ts_exchange_ms) FILTER (
                       WHERE json_extract_string(payload_json,'$.{FUNDING_FIELD_TS}') IS NULL
                          OR json_extract_string(payload_json,'$.{FUNDING_FIELD_RATE}') IS NULL
                   ) AS sample_missing
            FROM read_parquet(?, hive_partitioning=1, union_by_name=1)
        """, [glob]).fetchone()
    except Exception as exc:  # noqa: BLE001 -- glob may match nothing readable
        return {"symbol": symbol, "status": "UNREADABLE", "detail": str(exc)}
    n, n_missing, sample = row
    if not n:
        return {"symbol": symbol, "status": "NO_FRAMES"}
    return {"symbol": symbol, "status": "OK", "n_rows": int(n),
            "n_missing_fields": int(n_missing or 0),
            "sample_missing_head": sample[:300] if sample else None}


def funding_daily_cashflow(con: Any, base_dir: Path | str, symbol: str, *,
                            start: str | None = None, end: str | None = None) -> dict[str, Any]:
    """Daily SUM of ``fundingRate`` events, bucketed by ``fundingRateTimestamp``.

    Raises ``SeriesError`` the moment the probe finds ANY row missing
    either [sek] field. No data at all is NOT an error (spec: 113-day
    coverage today is an expected, reportable coverage gap) -- the series
    comes back with ``status="SKIPPED_NO_DATA"``.
    """
    base = Path(base_dir)
    p = probe_funding(con, base, symbol)
    provenance = {"exchange": "bybit", "stream": FUNDING_STREAM,
                  "field_rate": FUNDING_FIELD_RATE, "field_ts": FUNDING_FIELD_TS,
                  "glob": _funding_glob(base, symbol), "probe": p}
    if p["status"] in ("NO_PARTITIONS", "NO_FRAMES"):
        return _series(f"funding_{symbol}", "funding_cashflow", symbol, provenance, {},
                       status="SKIPPED_NO_DATA", reason=p["status"])
    if p["status"] == "UNREADABLE":
        raise SeriesError(f"funding {symbol}: partitions present but unreadable -- {p['detail']}")
    if p["n_missing_fields"] > 0:
        raise SeriesError(
            f"funding {symbol}: {p['n_missing_fields']}/{p['n_rows']} row(s) missing "
            f"{FUNDING_FIELD_RATE!r} or {FUNDING_FIELD_TS!r} ([sek] field layout) -- "
            f"sample raw (300 ch): {p['sample_missing_head']!r}")

    glob = _funding_glob(base, symbol)
    rows = con.execute(f"""
        WITH ev AS (
            SELECT CAST(json_extract_string(payload_json,'$.{FUNDING_FIELD_TS}') AS BIGINT) AS ts_ms,
                   CAST(json_extract_string(payload_json,'$.{FUNDING_FIELD_RATE}') AS DOUBLE) AS rate
            FROM read_parquet(?, hive_partitioning=1, union_by_name=1)
        )
        SELECT strftime(to_timestamp(ts_ms / 1000.0), '%Y-%m-%d') AS ts_day, SUM(rate) AS cashflow
        FROM ev
        WHERE ts_ms IS NOT NULL AND rate IS NOT NULL
        GROUP BY ts_day
        ORDER BY ts_day
    """, [glob]).fetchall()
    days_values = {d: float(v) for d, v in rows if v is not None}
    if start:
        days_values = {d: v for d, v in days_values.items() if d >= start}
    if end:
        days_values = {d: v for d, v in days_values.items() if d <= end}
    return _series(f"funding_{symbol}", "funding_cashflow", symbol, provenance, days_values)


# --------------------------------------------------------------- iv - rv

def iv_rv_diff_series(con: Any, harvest_base: Path | str, cache_dir: Path | str, *,
                      dvol_symbol: str, bar_exchange: str, bar_symbol: str,
                      days: list[str]) -> dict[str, Any]:
    """IV (Deribit DVOL daily close) minus WP-0 realized vol, both annualized.

    ``days`` bounds the query on both sides; ``wp9_dvol.harvest_close.
    daily_close`` DvolFieldLayoutError propagates unchanged (a genuine
    [sek] drift on the IV side must not be silently absorbed here).
    """
    provenance = {
        "dvol_symbol": dvol_symbol, "bar_exchange": bar_exchange, "bar_symbol": bar_symbol,
        "annualization_days_per_year": _rv.ANNUALIZATION_DAYS_PER_YEAR,
        "min_bars_per_day": _rv.MIN_BARS_PER_DAY,
    }
    if not days:
        return _series(f"ivrv_{dvol_symbol}", "iv_rv_diff", dvol_symbol, provenance, {},
                       status="SKIPPED_NO_DATA", reason="empty day list")

    dvol_rows = _dvol.daily_close(con, harvest_base, dvol_symbol, days)
    dvol_by_day = {r["date"]: r["close"] for r in dvol_rows if "close" in r}

    bars = load_minute_bars(cache_dir, bar_exchange, bar_symbol, days[0], days[-1])
    rv_by_day = _rv.annualize_pct(_rv.daily_realized_vol(bars))

    common = sorted(set(dvol_by_day) & set(rv_by_day) & set(days))
    days_values = {d: dvol_by_day[d] - rv_by_day[d] for d in common}
    status = "OK" if days_values else "SKIPPED_NO_OVERLAP"
    reason = None if days_values else "no overlapping day between dvol harvest and bar cache"
    return _series(f"ivrv_{dvol_symbol}", "iv_rv_diff", dvol_symbol, provenance, days_values,
                   status=status, reason=reason)


# --------------------------------------------------------------- basis

def _basis_partition_root(base: Path, symbol: str) -> Path:
    return base / "raw" / "bybit" / PERP_BASIS_STREAM / f"symbol={symbol}"


def _basis_glob(base: Path, symbol: str) -> str:
    return str(_basis_partition_root(base, symbol) / "date=*" / "*.parquet")


def _basis_partition_days(base: Path, symbol: str) -> list[str]:
    """Every ``date=`` partition directory on disk for this symbol -- a
    directory listing only, used as the denominator for the coverage
    fraction (cheap: no parquet I/O)."""
    root = _basis_partition_root(base, symbol)
    if not root.is_dir():
        return []
    return sorted(p.name[len("date="):] for p in root.iterdir()
                  if p.is_dir() and p.name.startswith("date="))


def _extract_field(payload_json: str | None, field: str) -> float | None:
    """The numeric value of ``field`` from a raw frame -- bare top level
    OR nested under ``data`` (the real bybit/tickers delta shape). ``None``
    for a missing frame, unparseable JSON, or a non-numeric value."""
    if payload_json is None:
        return None
    try:
        obj = json.loads(payload_json)
    except (TypeError, ValueError):
        return None
    if not isinstance(obj, dict):
        return None
    val = obj.get(field)
    if val is None:
        data = obj.get("data")
        if isinstance(data, dict):
            val = data.get(field)
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _basis_last_values_per_day(con: Any, base: Path, symbol: str) -> list[tuple[str, str | None, str | None]]:
    """Per UTC day (the harvest partition's own ``date=`` column), the LAST
    frame (by ``ts_exchange_ms``) containing ``markPrice``, and SEPARATELY
    the LAST frame containing ``indexPrice`` -- delta-stream stateful
    last-known-value semantics (a WS ``tickers`` delta only carries
    CHANGED fields, so mark/index routinely land in different frames, and
    the frame with the highest ``ts_exchange_ms`` overall need carry
    neither).

    Efficiency for the ~30M-row scan: the ``LIKE`` substring filter is
    pushed into the read_parquet scan (DuckDB can skip rows before any
    JSON parsing), and only ``ts_exchange_ms``/``payload_json`` are read
    per row (``date`` is a free hive-partition column, no extra I/O).
    Returns ``[]`` when no frame in the whole symbol matches either LIKE
    filter (distinct from "no partitions at all" -- see
    ``probe_perp_basis``).
    """
    glob = _basis_glob(base, symbol)
    mark_like = f'%"{PERP_BASIS_FIELD_MARK}"%'
    index_like = f'%"{PERP_BASIS_FIELD_INDEX}"%'
    rows = con.execute(f"""
        WITH filtered AS (
            SELECT CAST(date AS VARCHAR) AS d, ts_exchange_ms, payload_json
            FROM read_parquet(?, hive_partitioning=1, union_by_name=1)
            WHERE payload_json LIKE '{mark_like}' OR payload_json LIKE '{index_like}'
        )
        SELECT d,
               arg_max(payload_json, ts_exchange_ms)
                   FILTER (WHERE payload_json LIKE '{mark_like}') AS mark_payload,
               arg_max(payload_json, ts_exchange_ms)
                   FILTER (WHERE payload_json LIKE '{index_like}') AS idx_payload
        FROM filtered
        GROUP BY d
        ORDER BY d
    """, [glob]).fetchall()
    return rows


def probe_perp_basis(con: Any, base_dir: Path | str, symbol: str) -> dict[str, Any]:
    """Probe-first (spec: "soweit vorhanden") -- last-known markPrice/
    indexPrice coverage on the ``bybit/tickers`` delta stream. Never
    raises; reports FIELDS_ABSENT (neither field ever seen) and
    FIELDS_SPARSE (seen, but below ``PERP_BASIS_MIN_DAY_COVERAGE`` of
    harvested days) distinctly from NO_PARTITIONS/UNREADABLE so the caller
    can label the skip.
    """
    base = Path(base_dir)
    root = _basis_partition_root(base, symbol)
    if not root.is_dir() or not any(root.glob("date=*/*.parquet")):
        return {"symbol": symbol, "status": "NO_PARTITIONS"}
    try:
        rows = _basis_last_values_per_day(con, base, symbol)
    except Exception as exc:  # noqa: BLE001 -- glob may match nothing readable
        return {"symbol": symbol, "status": "UNREADABLE", "detail": str(exc)}

    n_total_days = len(_basis_partition_days(base, symbol)) or len(rows)
    n_covered = 0
    sample = None
    for _d, mark_pj, idx_pj in rows:
        if sample is None:
            sample = mark_pj or idx_pj
        if (_extract_field(mark_pj, PERP_BASIS_FIELD_MARK) is not None
                and _extract_field(idx_pj, PERP_BASIS_FIELD_INDEX) is not None):
            n_covered += 1

    if not rows or n_covered == 0:
        return {"symbol": symbol, "status": "FIELDS_ABSENT", "n_total_days": n_total_days,
                "occurrence_fraction": 0.0, "sample_head": sample[:300] if sample else None}
    fraction = n_covered / n_total_days if n_total_days else 0.0
    status = "OK" if fraction >= PERP_BASIS_MIN_DAY_COVERAGE else "FIELDS_SPARSE"
    return {"symbol": symbol, "status": status, "n_total_days": n_total_days,
            "n_days_both_fields": n_covered, "occurrence_fraction": fraction,
            "sample_head": sample[:300] if sample else None}


def perp_basis_proxy_series(con: Any, base_dir: Path | str, symbol: str, *,
                            start: str | None = None, end: str | None = None) -> dict[str, Any]:
    """Daily relative basis ``markPrice/indexPrice - 1``, built from the
    LAST-known value of each field per UTC day (delta-stream stateful
    semantics -- see ``_basis_last_values_per_day``).

    Probe-first: skips LOUDLY (status field, never raised) the moment the
    probe reports anything other than OK -- sparse/absent fields on this
    optional proxy stream are an EXPECTED outcome (spec: "soweit
    vorhanden"), not a layout drift.
    """
    base = Path(base_dir)
    p = probe_perp_basis(con, base, symbol)
    provenance = {"exchange": "bybit", "stream": PERP_BASIS_STREAM,
                  "field_mark": PERP_BASIS_FIELD_MARK, "field_index": PERP_BASIS_FIELD_INDEX,
                  "min_day_coverage": PERP_BASIS_MIN_DAY_COVERAGE, "probe": p}
    if p["status"] != "OK":
        frac = p.get("occurrence_fraction")
        reason = p.get("detail") or (
            f"probe-first: markPrice+indexPrice last-known coverage "
            f"{frac if frac is not None else 0.0:.2f} < "
            f"{PERP_BASIS_MIN_DAY_COVERAGE} threshold ({p['status']})")
        return _series(f"basis_{symbol}", "perp_basis_proxy", symbol, provenance, {},
                       status=f"SKIPPED_{p['status']}", reason=reason)

    rows = _basis_last_values_per_day(con, base, symbol)
    days_values: dict[str, float] = {}
    for d, mark_pj, idx_pj in rows:
        mark_val = _extract_field(mark_pj, PERP_BASIS_FIELD_MARK)
        idx_val = _extract_field(idx_pj, PERP_BASIS_FIELD_INDEX)
        if mark_val is None or idx_val is None or idx_val == 0:
            continue
        days_values[d] = mark_val / idx_val - 1.0
    if start:
        days_values = {d: v for d, v in days_values.items() if d >= start}
    if end:
        days_values = {d: v for d, v in days_values.items() if d <= end}
    return _series(f"basis_{symbol}", "perp_basis_proxy", symbol, provenance, days_values)
