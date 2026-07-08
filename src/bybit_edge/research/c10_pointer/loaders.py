"""Read-only daily stream loaders for the C-10 pointer mess-gate (H-10).

Four NEW loaders on top of the harvester raw Hive tree
(``data/harvest/raw/<exchange>/<stream>/symbol=<SYM>/date=<d>/*.parquet``),
all read-only (Schutzgut-Prinzip — the tree is NEVER written to). The existing
``c01_ofi_sign.oos.load_harvest_window`` covers only ``publicTrade`` tick
loads; H-10 needs DAILY aggregates over four streams:

  * RV (from ``publicTrade``): registered definition (hardened spec,
    ``edge-research-v3/results/deep_validation/hardened_hypotheses.md``,
    H-10 "Methodik": "RV = log Σ r²(1-min-Last-Price) je Tag") — 1-MINUTE
    last-price bars per UTC day via DuckDB ``max_by(price, ts)`` per 60-s
    bucket (same bucketing pattern as
    ``c12_frag.panel.load_minute_last_price``), then
    ``rv_day = log(Σ (Δlog p_1min)²)`` over the WITHIN-day consecutive 1-min
    bars. Days with fewer than ``RV_MIN_BARS_PER_DAY`` 1-min bars give NaN
    (unregistered robustness floor, documented at the constant).
  * Funding (``rest.fundingRate``): daily MEAN of the payload_json field
    ``fundingRate`` (Bybit REST form). Robustness fallbacks for Binance-form
    payloads: ``lastFundingRate`` (Binance premium-index REST naming) and
    ``info.fundingRate`` (ccxt-normalised dict — raw fields nested under
    ``info``, DATASET.md §6) — ASSUMPTIONS, flagged in README_H10.md.
  * OI (``rest.openInterest``): day-CLOSE (last-by-timestamp) of the field
    ``openInterest`` (fallbacks ``openInterestAmount`` [ccxt unified
    top-level], ``sumOpenInterest`` and ``info.sumOpenInterest`` [raw
    Binance field, nested under ``info`` in ccxt-normalised dicts] —
    assumptions, see README_H10.md); the detection series is the daily
    log-change (dlog).
  * Deribit ``dvol`` (HELD-OUT stage-2 target, symbols ``BTC``/``ETH`` — NOT
    ``BTCUSDT``): the payload_json structure is UNKNOWN-generic. The parser
    tries the field candidates ``dvol``, ``value``, ``index_value``,
    ``close``, ``price``, ``volatility``, ``mark_iv`` in that order; if none
    is present it falls back to the first numeric top-level field that is
    NOT timestamp-like (key must not match ``time|ts|stamp|date|seq|id``,
    value must be <= 1e6 — dvol is a percent-scale index) and emits a WARN
    on stderr; the parse mode used is surfaced to the caller (documented
    assumption, see README_H10.md). Daily CLOSE — last value by exchange
    timestamp per day (hardened spec: "dvol-Tagesschlüsse").

KAPITALFREI: pure data loading/resampling. No capital-metric logic anywhere.
"""
from __future__ import annotations

import json
import math
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
#: unknown-generic; guarded fallback = first numeric, non-timestamp-like
#: top-level field, with WARN + parse mode surfaced to the caller).
DVOL_FIELD_CANDIDATES: tuple[str, ...] = (
    "dvol", "value", "index_value", "close", "price", "volatility", "mark_iv",
)

#: Keys the dvol first-numeric fallback must NEVER pick (case-insensitive):
#: epoch timestamps, sequence numbers and ids are numeric but are not a
#: volatility level. A leading ``timestamp`` field would otherwise silently
#: be mistaken for the dvol value (audit_h10 BUG-4).
_DVOL_SKIP_KEY_RE = re.compile(r"time|ts|stamp|date|seq|id", re.IGNORECASE)

#: Upper plausibility bound for a dvol level in the FALLBACK path. dvol is a
#: percent-scale volatility index (historically ~20..300); any fallback value
#: above 1e6 is certainly an epoch timestamp or an id, never a vol level.
DVOL_FALLBACK_MAX_VALUE = 1e6

#: Minimum number of 1-minute last-price bars per UTC day for a defined RV
#: value. UNREGISTERED robustness floor (the hardened spec registers only
#: "RV = log Σ r²(1-min-Last-Price) je Tag", no bar floor): 30 bars ≈ 2% of
#: the 1440 possible 1-min buckets. A real harvested day carries O(10^2..10^3)
#: bars; below 30 bars the estimate is gap noise, not realised variance —
#: such days give NaN (absorbed by the registered n_avail >= 18 floor),
#: never a crash.
RV_MIN_BARS_PER_DAY = 30

_MS_PER_MINUTE = 60_000


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

def load_daily_rv(base_dir: Path | str, exchange: str, symbol: str,
                  days: list[str], *, stream: str = "publicTrade",
                  min_bars_per_day: int = RV_MIN_BARS_PER_DAY) -> np.ndarray:
    """Registered daily RV series: ``rv_day = log(Σ (Δlog p_1min)²)`` per day.

    Ground truth (hardened_hypotheses.md, H-10 "Methodik"):
    "RV = log Σ r²(1-min-Last-Price) je Tag". Implementation: 1-minute
    last-price bars per UTC day inside DuckDB (``max_by(price, ts)`` per 60-s
    bucket — same bucketing pattern as
    ``c12_frag.panel.load_minute_last_price``), squared log-returns over the
    CONSECUTIVE non-empty 1-min bars WITHIN the day (no cross-day return),
    summed per day, outer natural log. Price is extracted via
    ``COALESCE($.price, $.p)`` (Bybit backfill / live + Binance forms).

    NaN (never a crash) when the day has fewer than ``min_bars_per_day``
    1-min bars (see ``RV_MIN_BARS_PER_DAY`` — documented, unregistered
    robustness floor) or the within-day return sum is zero/non-finite
    (log undefined).
    """
    import duckdb

    base = Path(base_dir)
    present = _present_globs(base, exchange, stream, symbol, days)
    if not present:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{symbol} in {days[0]}..{days[-1]} under {base}"
        )
    # 1-min last-price bars per (day, minute bucket), then within-day squared
    # log-return sum. lag() is partitioned by day => strictly intraday returns.
    sql = f"""
        WITH bars AS (
            SELECT day, minute_idx, max_by(px, ts) AS px
            FROM (
                SELECT "date" AS day,
                       ts_exchange_ms AS ts,
                       CAST(ts_exchange_ms // {_MS_PER_MINUTE} AS BIGINT) AS minute_idx,
                       CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                                     json_extract_string(payload_json,'$.p')) AS DOUBLE) AS px
                FROM read_parquet({_file_list_sql(present)}, hive_partitioning=1, union_by_name=1)
            )
            WHERE px IS NOT NULL AND isfinite(px) AND px > 0 AND ts IS NOT NULL
            GROUP BY day, minute_idx
        ),
        rets AS (
            SELECT day,
                   ln(px) - lag(ln(px)) OVER (PARTITION BY day ORDER BY minute_idx) AS r
            FROM bars
        )
        SELECT day,
               sum(r * r) AS ssq,
               count(r) AS n_rets
        FROM rets
        WHERE r IS NOT NULL AND isfinite(r)
        GROUP BY day
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    by_day: dict[str, float] = {}
    min_rets = max(1, int(min_bars_per_day) - 1)  # n bars -> n-1 intraday returns
    for day, ssq, n_rets in rows:
        if ssq is None or n_rets is None or int(n_rets) < min_rets:
            continue
        ssq = float(ssq)
        if ssq > 0.0 and math.isfinite(ssq):
            by_day[str(day)] = math.log(ssq)
    return _align(by_day, days)


def load_daily_funding_mean(base_dir: Path | str, exchange: str, symbol: str,
                            days: list[str], *, stream: str = "rest.fundingRate") -> np.ndarray:
    """Daily MEAN of the funding rate.

    Payload field ``fundingRate`` (Bybit REST form; registry H-10 binding).
    Fallbacks for Binance-form payloads (ASSUMPTIONS, README_H10.md):
    ``lastFundingRate`` (Binance premium-index REST) and ``info.fundingRate``
    (ccxt-normalised dict — DATASET.md §6 says the Binance stream is stored
    as ccxt-normalised dicts, whose raw exchange fields sit under ``info``).
    NaN for days with no data.
    """
    value_sql = ("CAST(COALESCE(json_extract_string(payload_json,'$.fundingRate'),"
                 "json_extract_string(payload_json,'$.lastFundingRate'),"
                 "json_extract_string(payload_json,'$.info.fundingRate')) AS DOUBLE)")
    return _align(_query_daily(base_dir, exchange, stream, symbol, days, value_sql, "mean"), days)


def load_daily_oi_close(base_dir: Path | str, exchange: str, symbol: str,
                        days: list[str], *, stream: str = "rest.openInterest") -> np.ndarray:
    """Day-CLOSE (last by exchange timestamp) open interest.

    Payload field ``openInterest`` (Bybit REST form; registry H-10 binding).
    Fallbacks for Binance-form payloads (ASSUMPTIONS, README_H10.md):
    ``openInterestAmount`` (ccxt unified top-level field), ``sumOpenInterest``
    (raw Binance REST) and ``info.sumOpenInterest`` (raw field nested under
    ``info`` in ccxt-normalised dicts — DATASET.md §6). NaN for days with no
    data.
    """
    value_sql = ("CAST(COALESCE(json_extract_string(payload_json,'$.openInterest'),"
                 "json_extract_string(payload_json,'$.openInterestAmount'),"
                 "json_extract_string(payload_json,'$.sumOpenInterest'),"
                 "json_extract_string(payload_json,'$.info.sumOpenInterest')) AS DOUBLE)")
    return _align(_query_daily(base_dir, exchange, stream, symbol, days, value_sql, "last"), days)


def parse_dvol_value(payload: str, *, warn_state: dict | None = None,
                     symbol: str = "?") -> float:
    """Extract the dvol level from one unknown-generic payload_json string.

    Tries ``DVOL_FIELD_CANDIDATES`` in order; else falls back to the first
    numeric top-level field that is NOT timestamp-like — fallback keys
    matching ``time|ts|stamp|date|seq|id`` (case-insensitive) are skipped and
    fallback values above ``DVOL_FALLBACK_MAX_VALUE`` are rejected (dvol is a
    percent-scale index; an epoch ms timestamp is ~1.7e12 — audit_h10 BUG-4).
    The fallback emits a one-time WARN on stderr per symbol. ``warn_state``
    (if given) carries the once-flag AND records the parse mode used in
    ``warn_state["mode"]`` (``"candidate:<key>"`` / ``"fallback:<key>"``) so
    the caller can surface it in the JSON payload. Returns NaN if nothing
    plausible is found.
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
                if warn_state is not None and "mode" not in warn_state:
                    warn_state["mode"] = f"candidate:{key}"
                return v
    # Guarded fallback: first numeric, non-timestamp-like top-level field
    # (documented assumption; surfaced via warn_state["mode"] + stderr WARN).
    for key, raw in obj.items():
        if isinstance(raw, bool):
            continue
        if _DVOL_SKIP_KEY_RE.search(key):
            continue
        try:
            v = float(raw)
        except (TypeError, ValueError):
            continue
        if np.isfinite(v) and abs(v) <= DVOL_FALLBACK_MAX_VALUE:
            if warn_state is not None:
                if "mode" not in warn_state:
                    warn_state["mode"] = f"fallback:{key}"
                if not warn_state.get("warned"):
                    warn_state["warned"] = True
                    print(f"[c10_pointer] WARN dvol {symbol}: no known field "
                          f"{DVOL_FIELD_CANDIDATES} in payload — falling back to first "
                          f"plausible numeric field {key!r} (verify README_H10.md "
                          f"assumption; parse mode is surfaced in the JSON payload)",
                          file=sys.stderr, flush=True)
            return v
    return float("nan")


def load_daily_dvol(base_dir: Path | str, symbol: str, days: list[str], *,
                    exchange: str = "deribit", stream: str = "dvol",
                    info: dict | None = None) -> np.ndarray:
    """Daily CLOSE of the Deribit dvol level (HELD-OUT stage-2 target).

    Hardened spec (hardened_hypotheses.md, H-10 "Zielgröße Stufe 2"):
    "BTC- und ETH-dvol-Tagesschlüsse" — the day's LAST value by exchange
    timestamp, not the daily mean (audit_h10 BUG-2a). Symbols are
    ``BTC``/``ETH`` (Deribit currency naming, NOT ``BTCUSDT``). The payload
    structure is unknown-generic — parsed row-by-row in Python via
    ``parse_dvol_value`` (candidates + guarded first-numeric fallback with
    WARN). If ``info`` is given it is filled with ``parse_mode`` (the mode
    used for the first parsed row, e.g. ``"candidate:dvol"``) and
    ``finite_days`` (number of days with a defined close) for post-hoc
    coverage auditing.
    """
    import duckdb

    base = Path(base_dir)
    present = _present_globs(base, exchange, stream, symbol, days)
    if not present:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{symbol} in {days[0]}..{days[-1]} under {base}"
        )
    sql = f"""
        SELECT "date" AS day, ts_exchange_ms AS ts, payload_json
        FROM read_parquet({_file_list_sql(present)}, hive_partitioning=1, union_by_name=1)
        WHERE payload_json IS NOT NULL AND ts_exchange_ms IS NOT NULL
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    warn_state: dict = {}
    close_ts: dict[str, int] = {}
    close_val: dict[str, float] = {}
    for day, ts, payload in rows:
        v = parse_dvol_value(payload, warn_state=warn_state, symbol=symbol)
        if np.isfinite(v):
            d = str(day)
            t = int(ts)
            if d not in close_ts or t >= close_ts[d]:
                close_ts[d] = t
                close_val[d] = v
    out = _align(close_val, days)
    if info is not None:
        info["parse_mode"] = warn_state.get("mode", "none")
        info["finite_days"] = int(np.isfinite(out).sum())
    return out


# ----------------------------------------------------------------------------
# Derived daily detection series + 30-series panel
# ----------------------------------------------------------------------------

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
    of this panel (held-out target, loaded separately; hardened_hypotheses.md
    H-10). A series whose stream is missing entirely stays all-NaN (WARN; the
    n_avail >= 18 floor absorbs gaps); a series whose partitions EXIST but
    parse to 0 finite days also triggers a WARN (silent all-NULL field
    extraction, audit_h10 BUG-3). If NO series loads at all, ``DataError`` is
    raised.
    """
    loaders = {
        "rv": load_daily_rv,
        "funding": load_daily_funding_mean,
        "dlog_oi": lambda b, e, s, d: dlog_series(load_daily_oi_close(b, e, s, d)),
    }
    names: list[str] = []
    cols: list[np.ndarray] = []
    n_loaded = 0
    for exchange in exchanges:
        for symbol in symbols:
            per_metric: dict[str, np.ndarray] = {}
            for metric in DETECTION_METRICS:
                try:
                    per_metric[metric] = loaders[metric](base_dir, exchange, symbol, days)
                except DataError as exc:
                    print(f"[c10_pointer] WARN series {exchange}:{symbol}:{metric} "
                          f"missing ({exc})", file=sys.stderr, flush=True)
                    per_metric[metric] = np.full(len(days), np.nan)
                else:
                    # Partitions existed (no DataError) — an all-NaN result
                    # here means the JSON field names matched NOTHING; that
                    # must never stay silent (audit_h10 BUG-3).
                    if int(np.isfinite(per_metric[metric]).sum()) == 0:
                        print(f"[c10_pointer] WARN series {exchange}:{symbol}:{metric} "
                              f"partitions exist but parse to 0 finite days — check "
                              f"payload field names (README_H10.md)",
                              file=sys.stderr, flush=True)
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
    "DVOL_FALLBACK_MAX_VALUE",
    "DVOL_FIELD_CANDIDATES",
    "DataError",
    "RV_MIN_BARS_PER_DAY",
    "build_detection_panel",
    "daily_grid",
    "dlog_series",
    "load_daily_dvol",
    "load_daily_funding_mean",
    "load_daily_oi_close",
    "load_daily_rv",
    "parse_dvol_value",
]
