"""Panel load + calendar synchronisation for the C-06 XMR mess-gate (H-07).

This module builds the contemporaneously-synchronised 5-symbol bar matrix that
the cross-sectional-z estimator (``xsec.py``) needs. Unlike H-05b (per-symbol
``head(300k)`` ticks) the cross-sectional-z requires a COMMON calendar bar axis
across all symbols (registry H-07 / DEC-17 panel-synchronisation clause).

Pipeline per window:
  1. Load each of the 5 symbols over a fixed calendar window via the read-only
     harvester loader ``c01_ofi_sign.oos.load_harvest_window`` (import, not
     duplicated).
  2. Resample each symbol to 5-min bars: the LAST trade price in each
     ``[bar_start, bar_end)`` interval (last-price bar).
  3. Synchronise onto a common 5-min calendar grid over the window; forward-fill
     a missing last-price by AT MOST 1 bar, else the bar is DROPPED for ALL
     symbols (the panel needs contemporaneous completeness — a >1-bar gap in any
     one symbol drops the whole row).

Output: a ``SyncedPanel`` (bar timestamps x 5 symbols last-price) plus the
per-symbol bar returns.

KAPITALFREI: pure price resampling / synchronisation. No friction, bps, edge,
PnL, Sharpe logic anywhere. numpy only (+ the read-only harvester loader).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from ..c01_ofi_sign.oos import DataError, load_harvest_window

#: Program-standard 5-symbol perp panel (registry H-07 / H-01 / H-05).
DEFAULT_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")

#: Bar length in minutes (registry H-07 / DEC-17: 5 min, pre-fixed).
DEFAULT_BAR_MIN = 5

#: Calendar-window length in days (registry H-07 / DEC-15: 2 calendar days).
DEFAULT_CALENDAR_DAYS = 2

#: Max forward-fill gap in bars (registry H-07: <= 1 bar, else drop the row).
MAX_FFILL_BARS = 1


def _midnight_ms(start_date: str) -> int:
    """UTC midnight epoch-ms for a ``YYYY-MM-DD`` date."""
    y, m, d = (int(x) for x in start_date.split("-"))
    dt = datetime(y, m, d, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


@dataclass(slots=True)
class SyncedPanel:
    """Contemporaneously-synchronised 5-symbol last-price bar matrix.

    ``bar_ts_ms``  : (T,) common 5-min calendar bar-start timestamps (epoch ms).
    ``symbols``    : tuple of N symbol names (column order of ``last_price``).
    ``last_price`` : (T, N) last trade price per (bar, symbol).
    ``returns``    : (T, N) simple bar returns; row 0 is NaN (no prior bar).
    ``window_label``: descriptive label of the calendar window.
    """

    bar_ts_ms: np.ndarray
    symbols: tuple[str, ...]
    last_price: np.ndarray
    returns: np.ndarray
    window_label: str

    @property
    def n_bars(self) -> int:
        return int(self.bar_ts_ms.size)

    @property
    def n_symbols(self) -> int:
        return len(self.symbols)


def resample_last_price(
    ts_ms: np.ndarray,
    price: np.ndarray,
    grid_ms: np.ndarray,
    bar_ms: int,
) -> np.ndarray:
    """Last trade price in each ``[bar_start, bar_start+bar_ms)`` interval.

    ``grid_ms`` are the bar-START timestamps. For each grid bar the LAST trade
    price with ``bar_start <= ts < bar_start+bar_ms`` is taken; bars with no
    trade get NaN. ``ts_ms`` must be ascending (harvester loader guarantees it).
    """
    ts = np.asarray(ts_ms, dtype=np.float64)
    px = np.asarray(price, dtype=np.float64)
    out = np.full(grid_ms.size, np.nan, dtype=np.float64)
    if ts.size == 0:
        return out
    # For each bar, the last tick strictly before bar_end is the one at
    # searchsorted(ts, bar_end, 'left') - 1; keep it only if it is >= bar_start.
    bar_end = grid_ms + float(bar_ms)
    idx_end = np.searchsorted(ts, bar_end, side="left") - 1
    valid = idx_end >= 0
    cand_ts = np.where(valid, ts[np.clip(idx_end, 0, ts.size - 1)], -np.inf)
    in_bar = valid & (cand_ts >= grid_ms)
    sel = np.where(in_bar, idx_end, 0)
    out = np.where(in_bar, px[np.clip(sel, 0, px.size - 1)], np.nan)
    return out


def _ffill_capped(col: np.ndarray, max_bars: int) -> np.ndarray:
    """Forward-fill NaNs by at most ``max_bars`` consecutive bars.

    A run of NaNs longer than ``max_bars`` is left NaN beyond the cap (so the
    row-completeness filter drops those rows). The first value, if NaN, stays
    NaN (nothing to fill from).
    """
    out = col.copy()
    n = out.size
    last_valid = np.nan
    gap = 0
    for i in range(n):
        if np.isfinite(out[i]):
            last_valid = out[i]
            gap = 0
        else:
            if np.isfinite(last_valid) and gap < max_bars:
                out[i] = last_valid
                gap += 1
            else:
                gap += 1
    return out


def synchronise_panel(
    per_symbol_bars: dict[str, np.ndarray],
    grid_ms: np.ndarray,
    symbols: tuple[str, ...],
    *,
    window_label: str = "",
    max_ffill_bars: int = MAX_FFILL_BARS,
) -> SyncedPanel:
    """Synchronise per-symbol last-price bars onto the common calendar grid.

    Each column is forward-filled by <= ``max_ffill_bars``; then any bar row
    that is still incomplete (any symbol NaN) is DROPPED for ALL symbols. Bar
    returns are computed AFTER the drop on the surviving contemporaneous rows.
    """
    n_sym = len(symbols)
    mat = np.full((grid_ms.size, n_sym), np.nan, dtype=np.float64)
    for j, sym in enumerate(symbols):
        col = per_symbol_bars[sym]
        mat[:, j] = _ffill_capped(np.asarray(col, dtype=np.float64), max_ffill_bars)
    complete = np.all(np.isfinite(mat), axis=1)
    kept_ts = grid_ms[complete].astype(np.float64)
    kept_px = mat[complete, :]
    # Bar returns on the surviving contemporaneous rows (row 0 = NaN).
    returns = np.full_like(kept_px, np.nan)
    if kept_px.shape[0] >= 2:
        returns[1:, :] = kept_px[1:, :] / kept_px[:-1, :] - 1.0
    return SyncedPanel(
        bar_ts_ms=kept_ts,
        symbols=symbols,
        last_price=kept_px,
        returns=returns,
        window_label=window_label,
    )


def build_calendar_grid(start_date: str, calendar_days: int, bar_min: int) -> np.ndarray:
    """5-min (or ``bar_min``) calendar bar-START grid over the window (epoch ms)."""
    start_ms = _midnight_ms(start_date)
    bar_ms = bar_min * 60_000
    n_bars = (calendar_days * 24 * 60) // bar_min
    return start_ms + np.arange(n_bars, dtype=np.int64) * bar_ms


def load_panel_window(
    base_dir,
    symbols: tuple[str, ...],
    start_date: str,
    *,
    calendar_days: int = DEFAULT_CALENDAR_DAYS,
    bar_min: int = DEFAULT_BAR_MIN,
    max_ticks: int = 5_000_000,
    window_label: str = "",
) -> SyncedPanel:
    """Load + resample + synchronise the 5-symbol panel over a calendar window.

    Loads each symbol via ``load_harvest_window`` (read-only harvester tree),
    spilling enough days to cover the calendar window, resamples to last-price
    bars, and returns the contemporaneously-synchronised panel. Raises
    ``DataError`` if any symbol cannot be loaded (the panel needs all N).
    """
    bar_ms = bar_min * 60_000
    grid = build_calendar_grid(start_date, calendar_days, bar_min)
    # spill_days must cover the whole calendar window (+1 guard).
    spill = max(1, calendar_days)
    per_symbol: dict[str, np.ndarray] = {}
    for sym in symbols:
        arr = load_harvest_window(
            base_dir, sym, start_date,
            max_ticks=max_ticks, spill_days=spill,
        )
        per_symbol[sym] = resample_last_price(arr.ts, arr.price, grid.astype(np.float64), bar_ms)
    label = window_label or f"{start_date}..+{calendar_days}d"
    return synchronise_panel(
        per_symbol, grid.astype(np.float64), tuple(symbols), window_label=label,
    )


__all__ = [
    "DEFAULT_SYMBOLS",
    "DEFAULT_BAR_MIN",
    "DEFAULT_CALENDAR_DAYS",
    "MAX_FFILL_BARS",
    "DataError",
    "SyncedPanel",
    "build_calendar_grid",
    "load_panel_window",
    "resample_last_price",
    "synchronise_panel",
]
