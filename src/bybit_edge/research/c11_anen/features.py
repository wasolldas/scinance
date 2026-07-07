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
``publicTrade`` ticks for the realised vol and ``rest.fundingRate`` records
for the funding features. Loading mirrors ``c01_ofi_sign/oos.py::
load_harvest_window`` (DuckDB over ``payload_json``, backfill keys with live
fallback). Never writes into the harvester tree (Schutzgut).

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


def load_daily_rv(
    base_dir: Path | str,
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    exchange: str = "bybit",
    stream: str = "publicTrade",
) -> dict[str, float]:
    """Daily realised vol from publicTrade ticks: sqrt(sum of squared log
    returns of consecutive trade prices within the UTC day). Days with < 2
    valid ticks are omitted (NaN downstream). Read-only.
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    base = Path(base_dir)
    glob = _glob_for(base, exchange, stream, symbol)
    if not list((base / "raw" / exchange / stream / f"symbol={symbol}").glob("date=*")):
        raise DataError(f"no partitions for {exchange}/{stream}/{symbol} under {base}")
    sql = f"""
        SELECT date AS d, ts_exchange_ms AS ts,
               CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                             json_extract_string(payload_json,'$.p')) AS DOUBLE) AS price
        FROM read_parquet('{glob}', hive_partitioning=1, union_by_name=1)
        WHERE ts_exchange_ms IS NOT NULL
          AND date >= '{start_date}' AND date <= '{end_date}'
        ORDER BY date, ts_exchange_ms
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    out: dict[str, float] = {}
    cur_day: str | None = None
    prices: list[float] = []

    def _flush() -> None:
        if cur_day is None or len(prices) < 2:
            return
        p = np.asarray(prices, dtype=np.float64)
        p = p[np.isfinite(p) & (p > 0.0)]
        if p.size < 2:
            return
        r = np.diff(np.log(p))
        out[cur_day] = float(np.sqrt(np.sum(r * r)))

    for d, _ts, price in rows:
        d = str(d)
        if d != cur_day:
            _flush()
            cur_day = d
            prices = []
        prices.append(price)
    _flush()
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
