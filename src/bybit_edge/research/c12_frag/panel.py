"""Cross-exchange minute-panel synchronisation for the H-12 mess-gate.

Builds, per pre-registered calendar window, the day-wise 6-series minute
last-price panel (2 symbols x 3 exchanges) that ``spectrum.py`` analyses:

  * Series: BTC/ETH perp on Bybit, Binance and Deribit. Internal symbol
    notation is the Bybit one (``BTCUSDT``/``ETHUSDT``); the Deribit storage
    partitions use ``BTC-PERPETUAL``/``ETH-PERPETUAL`` (registry H-12 /
    DATASET.md SRC-10/11) — see ``map_exchange_symbol``.
  * Minute bars: LAST trade price per ``[t, t+60s)`` (registry H-12).
  * Forward-fill <= 1 minute per series WITHIN a day, else the minute stays
    invalid for that series.
  * Day window (UTC, T=1440) is the analysis unit; a day is VALID iff EVERY
    series has >= 1380/1440 valid minutes (registry H-12, pre-fixed).

Structure generalises the ``c06_xmr.panel`` pattern (multi-series sync on a
calendar bar grid, capped forward-fill) from "5 symbols, one exchange" to
"6 series = 2 symbols x 3 exchanges".

Loader note (why ``c01_ofi_sign.oos.load_harvest_window`` is NOT imported
here despite its ``exchange`` parameter): that loader is Bybit-trade-shaped —
its SQL requires a ``$.side``/``$.S`` payload key (Binance aggTrades carry
``p/q/m``, Deribit carries ``price/amount/direction`` — all rows would be
filtered out), it requires a ``$.size``/``$.v`` volume (absent there, NaN
filter drops everything), and its symbol regex rejects the hyphen in
``BTC-PERPETUAL``. H-12 needs ONLY (ts, price), so this module ships its own
exchange-aware, price-only loader following the identical read-only DuckDB
Hive pattern. Other modules stay untouched (Schutzgut / no cross-edit).

KAPITALFREI: pure price resampling / synchronisation. No friction, bps,
PnL, Sharpe logic anywhere. numpy + duckdb (read-only) only.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from bybit_edge.research.payload_sql import trade_rows_sql

#: Program-standard internal symbol notation (Bybit) for the H-12 panel.
DEFAULT_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT")

#: The three pre-registered exchanges (registry H-12).
DEFAULT_EXCHANGES: tuple[str, ...] = ("bybit", "binance", "deribit")

#: Deribit perp instrument notation (registry H-12 / DATASET.md SRC-10/11).
DERIBIT_SYMBOL_MAP: dict[str, str] = {
    "BTCUSDT": "BTC-PERPETUAL",
    "ETHUSDT": "ETH-PERPETUAL",
}

#: Minute grid per UTC day window (registry H-12: T = 1440).
MINUTES_PER_DAY = 1440

#: Max forward-fill gap in minutes (registry H-12: <= 1, else minute invalid).
MAX_FFILL_MINUTES = 1

#: Day validity floor (registry H-12: >= 1380/1440 valid minutes per series).
MIN_VALID_MINUTES_PER_DAY = 1380

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
#: Storage symbols may contain a hyphen (Deribit ``BTC-PERPETUAL``).
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_\-]+$")

MS_PER_MINUTE = 60_000
MS_PER_DAY = 24 * 3600_000


class DataError(RuntimeError):
    """Raised when a harvester window cannot be loaded."""


def map_exchange_symbol(exchange: str, symbol: str) -> str:
    """Storage-partition symbol for (exchange, internal Bybit-notation symbol).

    Bybit and Binance share the USDT-perp notation (``BTCUSDT``); Deribit uses
    ``BTC-PERPETUAL``/``ETH-PERPETUAL``. Unknown Deribit symbols fall back to
    ``<BASE>-PERPETUAL`` (base = symbol without the USDT suffix).
    """
    if exchange == "deribit":
        mapped = DERIBIT_SYMBOL_MAP.get(symbol)
        if mapped is None:
            base = symbol[:-4] if symbol.endswith("USDT") else symbol
            mapped = f"{base}-PERPETUAL"
        return mapped
    return symbol


def _midnight_ms(day: str) -> int:
    """UTC midnight epoch-ms for a ``YYYY-MM-DD`` date."""
    y, m, d = (int(x) for x in day.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def _date_list(start_date: str, end_date: str) -> list[str]:
    """Inclusive ``YYYY-MM-DD`` list from ``start_date`` to ``end_date``."""
    for s in (start_date, end_date):
        if not _DATE_RE.match(s):
            raise DataError(f"invalid date (want YYYY-MM-DD): {s!r}")
    y0, m0, d0 = (int(x) for x in start_date.split("-"))
    y1, m1, d1 = (int(x) for x in end_date.split("-"))
    a, b = date(y0, m0, d0), date(y1, m1, d1)
    if b < a:
        raise DataError(f"end_date {end_date} before start_date {start_date}")
    return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


def load_minute_last_price(
    base_dir: Path | str,
    exchange: str,
    storage_symbol: str,
    dates: list[str],
    *,
    stream: str = "publicTrade",
) -> np.ndarray:
    """Minute last-price series over the date list (read-only harvester tree).

    Reads ``<base>/raw/<exchange>/<stream>/symbol=<SYM>/date=<d>/*.parquet``
    and aggregates INSIDE DuckDB to the last trade price per ``[t, t+60s)``
    minute (``max_by(price, ts_exchange_ms)``), so full tick windows never
    enter Python memory. Price is extracted exchange-agnostically via
    ``COALESCE($.price, $.p)`` — covers the Bybit backfill (``price``),
    Binance aggTrades/REST backfill (``p``/``price``) and Deribit
    (``price``, a native JSON number) payload forms.

    BOTH harvester payload forms are read (``payload_sql.trade_rows_sql``):
    the FLAT backfill form (one trade per parquet row, top-level keys) and
    the multi-trade LIVE ENVELOPE (``{"topic":..,"data":[{..,"p":..},..]}``
    and the JSON-RPC ``$.params.data[*]`` variant), which is expanded to one
    row per trade using the PER-TRADE timestamp (``$.T``/``$.timestamp``).
    Before that expansion existed, envelope rows produced NULL prices and
    fell out silently — bybit from 2026-07-17 and deribit from ~2026-06-16
    delivered 0 parsable trades, which is what flipped 19/50 W2 days of the
    H-12 run to ``panel_valid=False``.

    NO de-duplication is applied here, and none is needed: a mixed
    backfill+live day (DATASET.md §9 caveat 4) can contain the same trade in
    both forms, but this loader only takes the LAST price per minute — the
    duplicate carries the SAME price at the SAME timestamp, so
    ``max_by(price, ts_exchange_ms)`` returns the identical value whether the
    trade appears once or twice. Counts/sums, which duplicates WOULD
    corrupt, are never formed here.

    Returns a ``(len(dates) * 1440,)`` float array of last prices, NaN where
    the minute has no trade. Read-only: never writes into the harvester tree.
    """
    import duckdb

    if not _SYMBOL_RE.match(storage_symbol):
        raise DataError(f"invalid symbol: {storage_symbol!r}")
    if not dates:
        raise DataError("empty date list")
    base = Path(base_dir)
    globs = [
        str(base / "raw" / exchange / stream / f"symbol={storage_symbol}" / f"date={d}" / "*.parquet")
        for d in dates
    ]
    present = [g for g in globs if list(Path(g).parent.glob("*.parquet"))]
    if not present:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{storage_symbol} in "
            f"{dates[0]}..{dates[-1]} under {base}"
        )
    start_ms = _midnight_ms(dates[0])
    end_ms = _midnight_ms(dates[-1]) + MS_PER_DAY
    minute0 = start_ms // MS_PER_MINUTE
    n_minutes = len(dates) * MINUTES_PER_DAY
    file_list = "[" + ", ".join("'" + g.replace("'", "''") + "'" for g in present) + "]"
    # One trade per row for BOTH payload forms (flat backfill row passed
    # through unchanged, live envelope exploded on the per-trade timestamp).
    trade_rows = trade_rows_sql(
        f"read_parquet({file_list}, hive_partitioning=1, union_by_name=1)"
    )
    sql = f"""
        SELECT CAST(ts_exchange_ms // {MS_PER_MINUTE} AS BIGINT) AS minute_idx,
               max_by(
                 CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                               json_extract_string(payload_json,'$.p')) AS DOUBLE),
                 ts_exchange_ms) AS last_price
        FROM {trade_rows}
        WHERE ts_exchange_ms IS NOT NULL
          AND ts_exchange_ms >= {start_ms} AND ts_exchange_ms < {end_ms}
          AND COALESCE(json_extract_string(payload_json,'$.price'),
                       json_extract_string(payload_json,'$.p')) IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    out = np.full(n_minutes, np.nan, dtype=np.float64)
    n_used = 0
    for minute_idx, price in rows:
        off = int(minute_idx) - minute0
        if 0 <= off < n_minutes and price is not None and np.isfinite(price) and price > 0.0:
            out[off] = float(price)
            n_used += 1
    if n_used == 0:
        raise DataError(
            f"{exchange}/{storage_symbol} {dates[0]}..{dates[-1]}: 0 usable minute bars"
        )
    print(
        f"[c12_frag] {exchange}/{storage_symbol} {dates[0]}..{dates[-1]}: "
        f"{n_used}/{n_minutes} minutes with trades",
        file=sys.stderr, flush=True,
    )
    return out


def ffill_minutes_capped(col: np.ndarray, max_minutes: int = MAX_FFILL_MINUTES) -> np.ndarray:
    """Forward-fill NaN minutes by at most ``max_minutes`` consecutive minutes.

    A gap longer than the cap stays NaN beyond the cap (those minutes are
    invalid). The first minute, if NaN, stays NaN (nothing to fill from).
    """
    out = np.asarray(col, dtype=np.float64).copy()
    last_valid = np.nan
    gap = 0
    for i in range(out.size):
        if np.isfinite(out[i]):
            last_valid = out[i]
            gap = 0
        else:
            if np.isfinite(last_valid) and gap < max_minutes:
                out[i] = last_valid
            gap += 1
    return out


@dataclass(slots=True)
class DayPanel:
    """One UTC day window of the 6-series minute last-price panel.

    ``date``          : YYYY-MM-DD (UTC day).
    ``minute_prices`` : (1440, N) last price per (minute, series); NaN invalid.
    ``valid_minutes`` : (N,) count of valid minutes per series (post-ffill).
    ``valid``         : registered day validity (every series >= 1380/1440).
    """

    date: str
    minute_prices: np.ndarray
    valid_minutes: np.ndarray
    valid: bool


@dataclass(slots=True)
class WindowDays:
    """A pre-registered calendar window as a list of day panels.

    ``series_labels``    : e.g. ``bybit:BTCUSDT`` .. ``deribit:ETH-PERPETUAL``.
    ``series_exchanges`` : exchange per series column (criterion-c bookkeeping).
    """

    label: str
    start_date: str
    end_date: str
    series_labels: tuple[str, ...]
    series_exchanges: tuple[str, ...]
    days: list[DayPanel]

    @property
    def n_days_total(self) -> int:
        return len(self.days)

    @property
    def n_days_valid(self) -> int:
        return sum(1 for d in self.days if d.valid)


def build_day_panels(
    per_series_minutes: dict[str, np.ndarray],
    series_labels: tuple[str, ...],
    dates: list[str],
    *,
    max_ffill_minutes: int = MAX_FFILL_MINUTES,
    min_valid_minutes: int = MIN_VALID_MINUTES_PER_DAY,
) -> list[DayPanel]:
    """Split per-series minute arrays into day panels with validity flags.

    Forward-fill is applied PER DAY (no cross-day fill — the day window is the
    self-contained analysis unit). A day is valid iff EVERY series has
    ``>= min_valid_minutes`` valid minutes after the capped fill.
    """
    n_series = len(series_labels)
    days: list[DayPanel] = []
    for di, day in enumerate(dates):
        mat = np.full((MINUTES_PER_DAY, n_series), np.nan, dtype=np.float64)
        for j, lab in enumerate(series_labels):
            seg = per_series_minutes[lab][di * MINUTES_PER_DAY:(di + 1) * MINUTES_PER_DAY]
            mat[:, j] = ffill_minutes_capped(seg, max_ffill_minutes)
        valid_minutes = np.sum(np.isfinite(mat), axis=0).astype(np.int64)
        valid = bool(np.all(valid_minutes >= min_valid_minutes))
        days.append(DayPanel(date=day, minute_prices=mat,
                             valid_minutes=valid_minutes, valid=valid))
    return days


def build_window(
    base_dir: Path | str,
    symbols: tuple[str, ...],
    start_date: str,
    end_date: str,
    *,
    exchanges: tuple[str, ...] = DEFAULT_EXCHANGES,
    label: str = "",
) -> WindowDays:
    """Load + synchronise one pre-registered calendar window (read-only).

    Series order is exchange-major: for exchanges (bybit, binance, deribit)
    and symbols (BTCUSDT, ETHUSDT) the six columns are
    bybit:BTCUSDT, bybit:ETHUSDT, binance:..., deribit:BTC-PERPETUAL, ...
    Raises ``DataError`` if ANY series cannot be loaded (the correlation
    matrix needs all N series).
    """
    dates = _date_list(start_date, end_date)
    series_labels: list[str] = []
    series_exchanges: list[str] = []
    per_series: dict[str, np.ndarray] = {}
    for ex in exchanges:
        for sym in symbols:
            storage = map_exchange_symbol(ex, sym)
            lab = f"{ex}:{storage}"
            per_series[lab] = load_minute_last_price(base_dir, ex, storage, dates)
            series_labels.append(lab)
            series_exchanges.append(ex)
    days = build_day_panels(per_series, tuple(series_labels), dates)
    return WindowDays(
        label=label or f"{start_date}..{end_date}",
        start_date=start_date,
        end_date=end_date,
        series_labels=tuple(series_labels),
        series_exchanges=tuple(series_exchanges),
        days=days,
    )


__all__ = [
    "DEFAULT_EXCHANGES",
    "DEFAULT_SYMBOLS",
    "DERIBIT_SYMBOL_MAP",
    "MAX_FFILL_MINUTES",
    "MINUTES_PER_DAY",
    "MIN_VALID_MINUTES_PER_DAY",
    "DataError",
    "DayPanel",
    "WindowDays",
    "build_day_panels",
    "build_window",
    "ffill_minutes_capped",
    "load_minute_last_price",
    "map_exchange_symbol",
]
