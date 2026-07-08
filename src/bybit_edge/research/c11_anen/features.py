"""Daily feature panel for the H-11 AnEn vol-regime mess-gate (KAPITALFREI).

Builds, per symbol and per UTC calendar day, the pre-registered 5-feature
state vector (registry H-11, OI features EXCLUDED by pre-registration):

  0. log RV_1d   — log annualised realised vol of day t
  1. log RV_5d   — log annualised RMS realised vol over days t-4..t
  2. log RV_20d  — log annualised RMS realised vol over days t-19..t
  3. funding day mean — mean bybit funding rate of day t
  4. funding 5d trend — OLS slope of the daily funding means over t-4..t

plus the HAR-RV regressor log RV_22d and the forecast target

  y(t) = log annualised RV over t+1..t+3   (3-day horizon, registry H-11).

CAUSALITY: every feature at day t uses data of days <= t only; the target at
day t uses days t+1..t+3 only (strictly future — it is the OBSERVATION the
forecasts are scored against, never a model input at time t).

Data source: the read-only harvester Hive tree (DATASET.md §2/§3) — bybit
``publicTrade`` for the realised vol (aggregated INSIDE DuckDB to 1-minute
last-price bars, then daily RV from 1-min log returns — the registered
"1-min-RV"; mirrors the ``c12_frag/panel.py`` minute-bar pattern, no
tick-level fetch into Python) and ``rest.fundingRate`` records for the
funding features. Never writes into the harvester tree (Schutzgut).

KAPITALFREI: pure measurement features. No cost model of any kind.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np

#: Annualisation basis for daily realised vol (crypto trades 365 days/year).
ANNUALISATION_DAYS = 365

#: Pre-registered lookbacks (registry H-11: RV_1d/5d/20d; HAR uses 22d).
RV_WINDOWS = (1, 5, 20)
HAR_RV_LONG_WINDOW = 22
FUNDING_TREND_WINDOW = 5

#: Forecast horizon in days (target = log annualised RV over t+1..t+3).
TARGET_HORIZON_DAYS = 3

N_FEATURES = 5

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_]+$")


class DataError(RuntimeError):
    """Raised when the harvester tree cannot provide the requested panel."""


def date_range(start: str, end: str) -> list[str]:
    """Inclusive list of ISO dates from ``start`` to ``end``."""
    for s in (start, end):
        if not _DATE_RE.match(s):
            raise DataError(f"invalid date (want YYYY-MM-DD): {s!r}")
    d0 = date.fromisoformat(start)
    d1 = date.fromisoformat(end)
    if d1 < d0:
        raise DataError(f"end date {end} before start date {start}")
    return [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]


@dataclass(slots=True)
class DailyPanel:
    """Per-day arrays for one symbol, aligned on a gapless calendar axis."""

    symbol: str
    dates: list[str]
    rv_daily: np.ndarray       # daily realised vol (NOT annualised), NaN if no data
    funding_daily: np.ndarray  # daily mean funding rate, NaN if no data

    @property
    def n_days(self) -> int:
        return len(self.dates)


# ----------------------------------------------------------------------------
# Harvester loaders (read-only)
# ----------------------------------------------------------------------------

def _glob_for(base: Path, exchange: str, stream: str, symbol: str) -> str:
    return str(base / "raw" / exchange / stream / f"symbol={symbol}" / "date=*" / "*.parquet")


#: Milliseconds per 1-minute bar / per UTC day (registered 1-min-RV raster).
MS_PER_MINUTE = 60_000
MS_PER_DAY = 86_400_000


def load_daily_rv(
    base_dir: Path | str,
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    exchange: str = "bybit",
    stream: str = "publicTrade",
) -> dict[str, float]:
    """Daily realised vol from 1-MINUTE returns (registry H-11: "1-min-RV").

    Aggregation happens entirely INSIDE DuckDB (c12_frag minute-bar pattern):
    1-minute last-price bars (bucket ``ts_exchange_ms // 60000``, last trade
    per bucket via ``max_by``), 1-min log returns WITHIN each UTC day
    (partitioned lag — no cross-midnight return), then per day
    RV = sqrt(sum r_1min^2). Only ~1 row per day ever reaches Python — no
    tick-level fetchall (real BTCUSDT volume is 10^6+ trades/day). Tick-to-
    tick returns are deliberately NOT used: bid-ask bounce inflates tick RV,
    and the registered quantity is the 1-min-return RV. Days with < 2 minute
    bars are omitted (NaN downstream). Read-only.
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    base = Path(base_dir)
    glob = _glob_for(base, exchange, stream, symbol)
    if not list((base / "raw" / exchange / stream / f"symbol={symbol}").glob("date=*")):
        raise DataError(f"no partitions for {exchange}/{stream}/{symbol} under {base}")
    sql = f"""
        WITH bars AS (
            SELECT CAST(ts_exchange_ms // {MS_PER_MINUTE} AS BIGINT) AS minute_idx,
                   max_by(
                     CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                                   json_extract_string(payload_json,'$.p')) AS DOUBLE),
                     ts_exchange_ms) AS px
            FROM read_parquet('{glob}', hive_partitioning=1, union_by_name=1)
            WHERE ts_exchange_ms IS NOT NULL
              AND date >= '{start_date}' AND date <= '{end_date}'
              AND COALESCE(json_extract_string(payload_json,'$.price'),
                           json_extract_string(payload_json,'$.p')) IS NOT NULL
            GROUP BY 1
        ),
        rets AS (
            SELECT minute_idx * {MS_PER_MINUTE} // {MS_PER_DAY} AS day_idx,
                   ln(px) - ln(lag(px) OVER (
                       PARTITION BY minute_idx * {MS_PER_MINUTE} // {MS_PER_DAY}
                       ORDER BY minute_idx)) AS r
            FROM bars
            WHERE px IS NOT NULL AND px > 0.0 AND isfinite(px)
        )
        SELECT day_idx, sqrt(sum(r * r)) AS rv
        FROM rets
        WHERE r IS NOT NULL AND isfinite(r)
        GROUP BY day_idx
        ORDER BY day_idx
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    epoch = date(1970, 1, 1)
    out: dict[str, float] = {}
    for day_idx, rv in rows:
        if rv is None or not np.isfinite(rv):
            continue
        d = (epoch + timedelta(days=int(day_idx))).isoformat()
        if start_date <= d <= end_date:
            out[d] = float(rv)
    return out


def load_daily_funding(
    base_dir: Path | str,
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    exchange: str = "bybit",
    stream: str = "rest.fundingRate",
) -> dict[str, float]:
    """Daily mean funding rate from ``rest.fundingRate`` records
    (payload key ``fundingRate``, DATASET.md §6). Read-only.
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    base = Path(base_dir)
    glob = _glob_for(base, exchange, stream, symbol)
    if not list((base / "raw" / exchange / stream / f"symbol={symbol}").glob("date=*")):
        raise DataError(f"no partitions for {exchange}/{stream}/{symbol} under {base}")
    sql = f"""
        SELECT date AS d,
               AVG(CAST(json_extract_string(payload_json,'$.fundingRate') AS DOUBLE)) AS f
        FROM read_parquet('{glob}', hive_partitioning=1, union_by_name=1)
        WHERE date >= '{start_date}' AND date <= '{end_date}'
          AND json_extract_string(payload_json,'$.fundingRate') IS NOT NULL
        GROUP BY date
        ORDER BY date
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    return {str(d): float(f) for d, f in rows if f is not None and np.isfinite(f)}


def build_daily_panel(
    base_dir: Path | str,
    symbol: str,
    start_date: str,
    end_date: str,
) -> DailyPanel:
    """Gapless calendar-axis panel of (daily RV, daily funding mean)."""
    dates = date_range(start_date, end_date)
    rv_map = load_daily_rv(base_dir, symbol, start_date, end_date)
    fu_map = load_daily_funding(base_dir, symbol, start_date, end_date)
    rv = np.array([rv_map.get(d, np.nan) for d in dates], dtype=np.float64)
    fu = np.array([fu_map.get(d, np.nan) for d in dates], dtype=np.float64)
    return DailyPanel(symbol=symbol, dates=dates, rv_daily=rv, funding_daily=fu)


# ----------------------------------------------------------------------------
# Causal feature / target computation (numpy only, no I/O)
# ----------------------------------------------------------------------------

def _log_ann_rms_rv(rv_daily: np.ndarray, window: int) -> np.ndarray:
    """log( sqrt(mean(rv_d^2 over t-window+1..t)) * sqrt(ANNUALISATION_DAYS) ).

    Strictly causal/trailing: entry t uses days t-window+1..t only. NaN if any
    day in the window is missing or the RMS is non-positive.
    """
    rv = np.asarray(rv_daily, dtype=np.float64)
    n = rv.size
    out = np.full(n, np.nan, dtype=np.float64)
    ann = np.sqrt(float(ANNUALISATION_DAYS))
    for t in range(window - 1, n):
        w = rv[t - window + 1 : t + 1]
        if not np.all(np.isfinite(w)):
            continue
        rms = np.sqrt(np.mean(w * w))
        if rms > 0.0:
            out[t] = np.log(rms * ann)
    return out


def _funding_trend(funding_daily: np.ndarray, window: int = FUNDING_TREND_WINDOW) -> np.ndarray:
    """OLS slope of the daily funding mean over the trailing ``window`` days.

    Strictly causal: entry t regresses funding[t-window+1..t] on 0..window-1.
    NaN if any day in the window is missing.
    """
    f = np.asarray(funding_daily, dtype=np.float64)
    n = f.size
    out = np.full(n, np.nan, dtype=np.float64)
    x = np.arange(window, dtype=np.float64)
    x_c = x - x.mean()
    denom = float(np.sum(x_c * x_c))
    for t in range(window - 1, n):
        w = f[t - window + 1 : t + 1]
        if not np.all(np.isfinite(w)):
            continue
        out[t] = float(np.sum(x_c * (w - w.mean())) / denom)
    return out


def compute_feature_matrix(
    rv_daily: np.ndarray, funding_daily: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """The pre-registered 5-feature state matrix plus the HAR log RV_22d column.

    Returns ``(features, log_rv22)`` where ``features`` has shape (n, 5) with
    columns [log RV_1d, log RV_5d, log RV_20d, funding day mean, funding 5d
    trend]. Every row t is computed from days <= t only (causal; verified by
    the no-lookahead unit test). OI features are EXCLUDED (registry H-11).
    """
    rv = np.asarray(rv_daily, dtype=np.float64)
    fu = np.asarray(funding_daily, dtype=np.float64)
    if rv.shape != fu.shape:
        raise ValueError("rv_daily and funding_daily must be aligned")
    n = rv.size
    feats = np.full((n, N_FEATURES), np.nan, dtype=np.float64)
    feats[:, 0] = _log_ann_rms_rv(rv, RV_WINDOWS[0])
    feats[:, 1] = _log_ann_rms_rv(rv, RV_WINDOWS[1])
    feats[:, 2] = _log_ann_rms_rv(rv, RV_WINDOWS[2])
    feats[:, 3] = fu
    feats[:, 4] = _funding_trend(fu, FUNDING_TREND_WINDOW)
    log_rv22 = _log_ann_rms_rv(rv, HAR_RV_LONG_WINDOW)
    return feats, log_rv22


def compute_target(
    rv_daily: np.ndarray, horizon: int = TARGET_HORIZON_DAYS
) -> np.ndarray:
    """Target y(t) = log annualised RV over days t+1..t+horizon (registry H-11).

    y(t) = log( sqrt(mean(rv_d^2 over t+1..t+3)) * sqrt(365) ). Strictly
    future-only: day t itself is NOT part of the target window. NaN when any
    of the 3 future days is missing (end of sample / data gap).
    """
    rv = np.asarray(rv_daily, dtype=np.float64)
    n = rv.size
    out = np.full(n, np.nan, dtype=np.float64)
    ann = np.sqrt(float(ANNUALISATION_DAYS))
    for t in range(n - horizon):
        w = rv[t + 1 : t + 1 + horizon]
        if not np.all(np.isfinite(w)):
            continue
        rms = np.sqrt(np.mean(w * w))
        if rms > 0.0:
            out[t] = np.log(rms * ann)
    return out


__all__ = [
    "ANNUALISATION_DAYS",
    "DailyPanel",
    "DataError",
    "FUNDING_TREND_WINDOW",
    "HAR_RV_LONG_WINDOW",
    "N_FEATURES",
    "RV_WINDOWS",
    "TARGET_HORIZON_DAYS",
    "build_daily_panel",
    "compute_feature_matrix",
    "compute_target",
    "date_range",
    "load_daily_funding",
    "load_daily_rv",
]
