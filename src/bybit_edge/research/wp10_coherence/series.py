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
    raised) when the fields are simply absent from this stream -- spec:
    "soweit vorhanden".

KAPITALFREI: pure data loading. No cost quantity, no PASS/FAIL.
"""
from __future__ import annotations

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
#: [sek] -- unverified against a live bybit/tickers frame in this sandbox
#: (probe-first is exactly the point: never assumed present).
PERP_BASIS_FIELD_MARK = "markPrice"
PERP_BASIS_FIELD_INDEX = "indexPrice"


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


def probe_perp_basis(con: Any, base_dir: Path | str, symbol: str) -> dict[str, Any]:
    """Probe-first (spec: "soweit vorhanden") -- markPrice/indexPrice on
    ``bybit/tickers``. Never raises; reports FIELDS_ABSENT distinctly from
    NO_PARTITIONS/NO_FRAMES/UNREADABLE so the caller can label the skip.
    """
    base = Path(base_dir)
    root = _basis_partition_root(base, symbol)
    if not root.is_dir() or not any(root.glob("date=*/*.parquet")):
        return {"symbol": symbol, "status": "NO_PARTITIONS"}
    glob = str(root / "date=*" / "*.parquet")
    try:
        row = con.execute(f"""
            SELECT count(*) AS n,
                   count(*) FILTER (
                       WHERE json_extract_string(payload_json,'$.{PERP_BASIS_FIELD_MARK}') IS NOT NULL
                         AND json_extract_string(payload_json,'$.{PERP_BASIS_FIELD_INDEX}') IS NOT NULL
                   ) AS n_both,
                   arg_max(payload_json, ts_exchange_ms) AS sample
            FROM read_parquet(?, hive_partitioning=1, union_by_name=1)
        """, [glob]).fetchone()
    except Exception as exc:  # noqa: BLE001 -- glob may match nothing readable
        return {"symbol": symbol, "status": "UNREADABLE", "detail": str(exc)}
    n, n_both, sample = row
    if not n:
        return {"symbol": symbol, "status": "NO_FRAMES"}
    if not n_both:
        return {"symbol": symbol, "status": "FIELDS_ABSENT", "n_rows": int(n),
                "sample_head": sample[:300] if sample else None}
    return {"symbol": symbol, "status": "OK", "n_rows": int(n),
            "n_with_both_fields": int(n_both), "sample_head": sample[:300] if sample else None}


def perp_basis_proxy_series(con: Any, base_dir: Path | str, symbol: str, *,
                            start: str | None = None, end: str | None = None) -> dict[str, Any]:
    """Daily mean relative basis ``(markPrice - indexPrice) / indexPrice``.

    Probe-first: skips LOUDLY (status field, never raised) the moment the
    probe reports anything other than OK -- an absent field on this
    stream is an EXPECTED outcome for an optional proxy (spec: "soweit
    vorhanden"), not a layout drift.
    """
    base = Path(base_dir)
    p = probe_perp_basis(con, base, symbol)
    provenance = {"exchange": "bybit", "stream": PERP_BASIS_STREAM,
                  "field_mark": PERP_BASIS_FIELD_MARK, "field_index": PERP_BASIS_FIELD_INDEX,
                  "probe": p}
    if p["status"] != "OK":
        return _series(f"basis_{symbol}", "perp_basis_proxy", symbol, provenance, {},
                       status=f"SKIPPED_{p['status']}",
                       reason=p.get("detail") or "probe-first: no usable markPrice/indexPrice data")

    glob = str(_basis_partition_root(base, symbol) / "date=*" / "*.parquet")
    rows = con.execute(f"""
        SELECT date AS d,
               AVG((CAST(json_extract_string(payload_json,'$.{PERP_BASIS_FIELD_MARK}') AS DOUBLE)
                    - CAST(json_extract_string(payload_json,'$.{PERP_BASIS_FIELD_INDEX}') AS DOUBLE))
                   / NULLIF(CAST(json_extract_string(payload_json,'$.{PERP_BASIS_FIELD_INDEX}') AS DOUBLE), 0)) AS basis
        FROM read_parquet(?, hive_partitioning=1, union_by_name=1)
        WHERE json_extract_string(payload_json,'$.{PERP_BASIS_FIELD_MARK}') IS NOT NULL
          AND json_extract_string(payload_json,'$.{PERP_BASIS_FIELD_INDEX}') IS NOT NULL
        GROUP BY date
        ORDER BY date
    """, [glob]).fetchall()
    days_values = {d: float(v) for d, v in rows if v is not None}
    if start:
        days_values = {d: v for d, v in days_values.items() if d >= start}
    if end:
        days_values = {d: v for d, v in days_values.items() if d <= end}
    return _series(f"basis_{symbol}", "perp_basis_proxy", symbol, provenance, days_values)
