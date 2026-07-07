"""Read-only daily stream loaders for the C-10 pointer mess-gate (H-10).

Four NEW loaders on top of the harvester raw Hive tree
(``data/harvest/raw/<exchange>/<stream>/symbol=<SYM>/date=<d>/*.parquet``),
all read-only (Schutzgut-Prinzip — the tree is NEVER written to). The existing
``c01_ofi_sign.oos.load_harvest_window`` covers only ``publicTrade`` tick
loads; H-10 needs DAILY aggregates over four streams:

  * RV (from ``publicTrade``): last trade price per DAILY bar via DuckDB
    ``arg_max(price, ts)`` per date partition; the daily RV series is the
    squared daily log-return of that daily last price. NOTE: with a DAILY
    last-price bar (registry wording "Last-Price je Tages-Bar,
    log-Return-Quadrate summiert") the "sum of squared log-returns" reduces
    to the SINGLE squared daily log-return per day — implemented exactly so.
  * Funding (``rest.fundingRate``): daily MEAN of the payload_json field
    ``fundingRate`` (Bybit REST form). Robustness fallback for Binance-form
    payloads: ``lastFundingRate`` (Binance premium-index REST naming) — an
    ASSUMPTION, flagged in README_H10.md.
  * OI (``rest.openInterest``): day-CLOSE (last-by-timestamp) of the field
    ``openInterest`` (fallback ``sumOpenInterest`` for Binance-form payloads
    — assumption, see README_H10.md); the detection series is the daily
    log-change (dlog).
  * Deribit ``dvol`` (HELD-OUT stage-2 target, symbols ``BTC``/``ETH`` — NOT
    ``BTCUSDT``): the payload_json structure is UNKNOWN-generic. The parser
    tries the field candidates ``dvol``, ``value``, ``index_value``,
    ``close``, ``price`` in that order; if none is present it falls back to
    the FIRST numeric top-level field in the payload and emits a WARN on
    stderr (documented assumption, see README_H10.md). Daily mean.

KAPITALFREI: pure data loading/resampling. No capital-metric logic anywhere.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_\-]+$")

#: Program-standard 5-symbol perp panel (registry H-10 / H-07 / H-01).
DEFAULT_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")

#: Detection exchanges (registry H-10: Bybit + Binance; Deribit is HELD OUT).
DEFAULT_EXCHANGES: tuple[str, ...] = ("bybit", "binance")

#: Per-exchange metric triple (registry H-10: RV, funding, dlog-OI).
DETECTION_METRICS: tuple[str, ...] = ("rv", "funding", "dlog_oi")

#: dvol payload field candidates, tried in order (ASSUMPTION — structure
#: unknown-generic; fallback = first numeric top-level field, with WARN).
DVOL_FIELD_CANDIDATES: tuple[str, ...] = ("dvol", "value", "index_value", "close", "price")


class DataError(RuntimeError):
    """Raised when a harvester stream/symbol cannot be loaded at all."""


def daily_grid(start_date: str, end_date: str) -> list[str]:
    """Inclusive list of ``YYYY-MM-DD`` strings from ``start_date`` to ``end_date``."""
    for d in (start_date, end_date):
        if not _DATE_RE.match(d):
            raise DataError(f"invalid date (want YYYY-MM-DD): {d!r}")
    y, m, dd = (int(x) for x in start_date.split("-"))
    d0 = date(y, m, dd)
    y, m, dd = (int(x) for x in end_date.split("-"))
    d1 = date(y, m, dd)
    if d1 < d0:
        raise DataError(f"end_date {end_date} before start_date {start_date}")
    n = (d1 - d0).days + 1
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


def _present_globs(base: Path, exchange: str, stream: str, symbol: str,
                   days: list[str]) -> list[str]:
    """Existing per-date parquet globs for one (exchange, stream, symbol)."""
    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    globs = [
        str(base / "raw" / exchange / stream / f"symbol={symbol}" / f"date={d}" / "*.parquet")
        for d in days
    ]
    return [g for g in globs if list(Path(g).parent.glob("*.parquet"))]


def _file_list_sql(globs: list[str]) -> str:
    return "[" + ", ".join("'" + g.replace("'", "''") + "'" for g in globs) + "]"


def _query_daily(base_dir: Path | str, exchange: str, stream: str, symbol: str,
                 days: list[str], value_sql: str, agg: str) -> dict[str, float]:
    """Daily aggregate of ``value_sql`` per date partition (read-only DuckDB).

    ``agg``: ``"mean"`` = daily mean; ``"last"`` = day-close, i.e.
    ``arg_max(value, ts_exchange_ms)``. Same Hive-glob pattern as
    ``c01_ofi_sign.oos.load_harvest_window`` (registry read-only convention).
    """
    import duckdb

    base = Path(base_dir)
    present = _present_globs(base, exchange, stream, symbol, days)
    if not present:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{symbol} in {days[0]}..{days[-1]} under {base}"
        )
    if agg == "mean":
        agg_sql = "avg(v)"
    elif agg == "last":
        agg_sql = "arg_max(v, ts)"
    else:  # pragma: no cover - guarded by callers
        raise ValueError(f"unknown agg {agg!r}")
    sql = f"""
        SELECT "date" AS day, {agg_sql} AS val
        FROM (
            SELECT "date", ts_exchange_ms AS ts, {value_sql} AS v
            FROM read_parquet({_file_list_sql(present)}, hive_partitioning=1, union_by_name=1)
        )
        WHERE v IS NOT NULL AND isfinite(v) AND ts IS NOT NULL
        GROUP BY "date"
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    return {str(r[0]): float(r[1]) for r in rows if r[1] is not None}


def _align(by_day: dict[str, float], days: list[str]) -> np.ndarray:
    out = np.full(len(days), np.nan, dtype=np.float64)
    for i, d in enumerate(days):
        v = by_day.get(d)
        if v is not None and np.isfinite(v):
            out[i] = v
    return out


# ----------------------------------------------------------------------------
# The four stream loaders
# ----------------------------------------------------------------------------

def load_daily_last_price(base_dir: Path | str, exchange: str, symbol: str,
                          days: list[str], *, stream: str = "publicTrade") -> np.ndarray:
    """Daily-bar LAST trade price per date partition (adapted load_harvest_window).

    Handles the backfill single-trade JSON form (``price``) with the live-form
    fallback (``p``), exactly like ``load_harvest_window``. NaN for days with
    no data.
    """
    value_sql = ("CAST(COALESCE(json_extract_string(payload_json,'$.price'),"
                 "json_extract_string(payload_json,'$.p')) AS DOUBLE)")
    return _align(_query_daily(base_dir, exchange, stream, symbol, days, value_sql, "last"), days)


def load_daily_funding_mean(base_dir: Path | str, exchange: str, symbol: str,
                            days: list[str], *, stream: str = "rest.fundingRate") -> np.ndarray:
    """Daily MEAN of the funding rate.

    Payload field ``fundingRate`` (Bybit REST form; registry H-10 binding).
    Fallback ``lastFundingRate`` for Binance-form payloads (ASSUMPTION,
    README_H10.md). NaN for days with no data.
    """
    value_sql = ("CAST(COALESCE(json_extract_string(payload_json,'$.fundingRate'),"
                 "json_extract_string(payload_json,'$.lastFundingRate')) AS DOUBLE)")
    return _align(_query_daily(base_dir, exchange, stream, symbol, days, value_sql, "mean"), days)


def load_daily_oi_close(base_dir: Path | str, exchange: str, symbol: str,
                        days: list[str], *, stream: str = "rest.openInterest") -> np.ndarray:
    """Day-CLOSE (last by exchange timestamp) open interest.

    Payload field ``openInterest`` (Bybit REST form; registry H-10 binding).
    Fallback ``sumOpenInterest`` for Binance-form payloads (ASSUMPTION,
    README_H10.md). NaN for days with no data.
    """
    value_sql = ("CAST(COALESCE(json_extract_string(payload_json,'$.openInterest'),"
                 "json_extract_string(payload_json,'$.sumOpenInterest')) AS DOUBLE)")
    return _align(_query_daily(base_dir, exchange, stream, symbol, days, value_sql, "last"), days)


def parse_dvol_value(payload: str, *, warn_state: dict | None = None,
                     symbol: str = "?") -> float:
    """Extract the dvol level from one unknown-generic payload_json string.

    Tries ``DVOL_FIELD_CANDIDATES`` in order; else falls back to the FIRST
    numeric top-level field (dict iteration order) with a one-time WARN on
    stderr per symbol (``warn_state`` carries the once-flag). Returns NaN if
    nothing numeric is found.
    """
    try:
        obj = json.loads(payload)
    except (TypeError, ValueError):
        return float("nan")
    if not isinstance(obj, dict):
        return float("nan")
    for key in DVOL_FIELD_CANDIDATES:
        if key in obj:
            try:
                v = float(obj[key])
            except (TypeError, ValueError):
                continue
            if np.isfinite(v):
                return v
    # Fallback: first numeric top-level field (documented assumption).
    for key, raw in obj.items():
        if isinstance(raw, bool):
            continue
        try:
            v = float(raw)
        except (TypeError, ValueError):
            continue
        if np.isfinite(v):
            if warn_state is not None and not warn_state.get("warned"):
                warn_state["warned"] = True
                print(f"[c10_pointer] WARN dvol {symbol}: no known field "
                      f"{DVOL_FIELD_CANDIDATES} in payload — falling back to first "
                      f"numeric field {key!r} (verify README_H10.md assumption)",
                      file=sys.stderr, flush=True)
            return v
    return float("nan")


def load_daily_dvol(base_dir: Path | str, symbol: str, days: list[str], *,
                    exchange: str = "deribit", stream: str = "dvol") -> np.ndarray:
    """Daily MEAN of the Deribit dvol level (HELD-OUT stage-2 target).

    Symbols are ``BTC``/``ETH`` (Deribit currency naming, NOT ``BTCUSDT``).
    The payload structure is unknown-generic — parsed row-by-row in Python via
    ``parse_dvol_value`` (candidates + first-numeric fallback with WARN).
    """
    import duckdb

    base = Path(base_dir)
    present = _present_globs(base, exchange, stream, symbol, days)
    if not present:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{symbol} in {days[0]}..{days[-1]} under {base}"
        )
    sql = f"""
        SELECT "date" AS day, payload_json
        FROM read_parquet({_file_list_sql(present)}, hive_partitioning=1, union_by_name=1)
        WHERE payload_json IS NOT NULL
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    warn_state: dict = {}
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    for day, payload in rows:
        v = parse_dvol_value(payload, warn_state=warn_state, symbol=symbol)
        if np.isfinite(v):
            d = str(day)
            sums[d] = sums.get(d, 0.0) + v
            counts[d] = counts.get(d, 0) + 1
    by_day = {d: sums[d] / counts[d] for d in sums}
    return _align(by_day, days)


# ----------------------------------------------------------------------------
# Derived daily detection series + 30-series panel
# ----------------------------------------------------------------------------

def rv_from_daily_last_price(px: np.ndarray) -> np.ndarray:
    """Daily RV from the daily-bar last price: squared daily log-return.

    ``rv[t] = (log px[t] - log px[t-1])^2``; NaN where either price is missing
    or non-positive; ``rv[0]`` is NaN (no prior day). With DAILY bars this IS
    the registry "log-Return-Quadrate summiert" (a one-element sum per day).
    """
    px = np.asarray(px, dtype=np.float64)
    out = np.full(px.size, np.nan, dtype=np.float64)
    if px.size < 2:
        return out
    with np.errstate(divide="ignore", invalid="ignore"):
        lp = np.where(px > 0, np.log(px), np.nan)
    d = lp[1:] - lp[:-1]
    out[1:] = d * d
    return out


def dlog_series(x: np.ndarray) -> np.ndarray:
    """Daily log-change ``log x[t] - log x[t-1]``; NaN on gaps/non-positive."""
    x = np.asarray(x, dtype=np.float64)
    out = np.full(x.size, np.nan, dtype=np.float64)
    if x.size < 2:
        return out
    with np.errstate(divide="ignore", invalid="ignore"):
        lx = np.where(x > 0, np.log(x), np.nan)
    out[1:] = lx[1:] - lx[:-1]
    return out


def build_detection_panel(
    base_dir: Path | str,
    days: list[str],
    *,
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    exchanges: tuple[str, ...] = DEFAULT_EXCHANGES,
) -> tuple[list[str], np.ndarray]:
    """Build the pre-fixed 30-series daily detection matrix (T x 30).

    Series order is DETERMINISTIC: for each exchange (bybit, binance), for each
    symbol, the metric triple (rv, funding, dlog_oi). Deribit dvol is NOT part
    of this panel (held-out target, loaded separately). A series whose stream
    is missing entirely stays all-NaN (WARN; the n_avail >= 18 floor absorbs
    gaps); if NO series loads at all, ``DataError`` is raised.
    """
    names: list[str] = []
    cols: list[np.ndarray] = []
    n_loaded = 0
    for exchange in exchanges:
        for symbol in symbols:
            per_metric: dict[str, np.ndarray] = {}
            try:
                px = load_daily_last_price(base_dir, exchange, symbol, days)
                per_metric["rv"] = rv_from_daily_last_price(px)
            except DataError as exc:
                print(f"[c10_pointer] WARN series {exchange}:{symbol}:rv missing ({exc})",
                      file=sys.stderr, flush=True)
                per_metric["rv"] = np.full(len(days), np.nan)
            try:
                per_metric["funding"] = load_daily_funding_mean(base_dir, exchange, symbol, days)
            except DataError as exc:
                print(f"[c10_pointer] WARN series {exchange}:{symbol}:funding missing ({exc})",
                      file=sys.stderr, flush=True)
                per_metric["funding"] = np.full(len(days), np.nan)
            try:
                oi = load_daily_oi_close(base_dir, exchange, symbol, days)
                per_metric["dlog_oi"] = dlog_series(oi)
            except DataError as exc:
                print(f"[c10_pointer] WARN series {exchange}:{symbol}:dlog_oi missing ({exc})",
                      file=sys.stderr, flush=True)
                per_metric["dlog_oi"] = np.full(len(days), np.nan)
            for metric in DETECTION_METRICS:
                names.append(f"{exchange}:{symbol}:{metric}")
                col = per_metric[metric]
                cols.append(col)
                if int(np.isfinite(col).sum()) > 0:
                    n_loaded += 1
    if n_loaded == 0:
        raise DataError(f"no detection series loadable under {base_dir}")
    return names, np.column_stack(cols)


__all__ = [
    "DEFAULT_EXCHANGES",
    "DEFAULT_SYMBOLS",
    "DETECTION_METRICS",
    "DVOL_FIELD_CANDIDATES",
    "DataError",
    "build_detection_panel",
    "daily_grid",
    "dlog_series",
    "load_daily_dvol",
    "load_daily_funding_mean",
    "load_daily_last_price",
    "load_daily_oi_close",
    "parse_dvol_value",
    "rv_from_daily_last_price",
]
