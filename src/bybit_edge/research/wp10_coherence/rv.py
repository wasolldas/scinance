"""WP-10 -- shared realized-volatility primitive from the WP-0 bar cache.

ONE definition, reused by ``stress_canon`` (STRESS_ABS/STRESS_REL
thresholds, DEC-55/56) and ``series`` (the IV-RV coherence proxy) -- so the
"realized vol" that decides which days are stress and the "RV" half of the
IV-RV difference series are, by construction, never two silently different
numbers.

``RV_day = sqrt(sum of squared consecutive 1-minute log returns of
px_last within one UTC day)`` -- the textbook Andersen/Bollerslev realized-
volatility estimator, using WHATEVER 1-minute bars are actually present
that day in consecutive order (same convention as
``c10_pointer.loaders`` RV: "log Sigma r^2(1-min-Last-Price) je Tag",
computed on the within-day consecutive bars, no synthetic gap-fill).
``MIN_BARS_PER_DAY`` is an unverified robustness floor (design parameter,
not a gate) below which a day is dropped rather than computed on a sparse
sample.

Annualisation multiplies by ``sqrt(ANNUALIZATION_DAYS_PER_YEAR)`` and
converts to percentage points, matching Deribit DVOL's published
percent-annualised scale (crypto trades 24/7, so 365 calendar days is the
day-count convention on BOTH sides of the WP-10(A) IV-RV difference --
[sek], unverified against a live DVOL methodology doc in this sandbox,
same caveat as ``wp9_dvol``).

KAPITALFREI: pure measurement. No cost quantity, no PASS/FAIL.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np

__all__ = [
    "MIN_BARS_PER_DAY", "ANNUALIZATION_DAYS_PER_YEAR",
    "daily_realized_vol", "annualize_pct", "daily_close_log_returns",
    "panel_returns",
]

#: Design floor (unverified against a benchmark): fewer bars -> day dropped.
MIN_BARS_PER_DAY = 60

#: [sek] -- crypto trades 24/7; matches Deribit DVOL's annualisation
#: convention as far as documented, not verified live in this sandbox.
ANNUALIZATION_DAYS_PER_YEAR = 365.0

_MIN_PER_DAY = 1_440


def _epoch_day_to_iso(day_idx: int) -> str:
    return (date(1970, 1, 1) + timedelta(days=int(day_idx))).isoformat()


def daily_realized_vol(bars: dict[str, np.ndarray]) -> dict[str, float]:
    """Non-annualized RV per UTC day from ``bar_cache.load_minute_bars`` output.

    Days with fewer than ``MIN_BARS_PER_DAY`` present 1-minute bars, or
    whose consecutive-bar log returns are all non-finite, are omitted
    (never a fabricated zero).
    """
    minute_idx = np.asarray(bars["minute_idx"])
    px = np.asarray(bars["px_last"], dtype=np.float64)
    if minute_idx.size == 0:
        return {}
    order = np.argsort(minute_idx, kind="mergesort")
    minute_idx = minute_idx[order]
    px = px[order]
    day_idx_all = minute_idx // _MIN_PER_DAY

    out: dict[str, float] = {}
    for d in np.unique(day_idx_all):
        sel = day_idx_all == d
        p = px[sel]
        if p.size < MIN_BARS_PER_DAY:
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.diff(np.log(p))
        r = r[np.isfinite(r)]
        if r.size == 0:
            continue
        out[_epoch_day_to_iso(int(d))] = float(np.sqrt(np.sum(r * r)))
    return out


def annualize_pct(rv_by_day: dict[str, float], *,
                  days_per_year: float = ANNUALIZATION_DAYS_PER_YEAR) -> dict[str, float]:
    """Non-annualized daily RV -> annualized percentage points."""
    factor = float(np.sqrt(days_per_year)) * 100.0
    return {d: v * factor for d, v in rv_by_day.items()}


def daily_close_log_returns(bars: dict[str, np.ndarray]) -> dict[str, float]:
    """UTC-day close-to-close log returns (last bar of each day as close).

    Only CONSECUTIVE calendar days produce a return (a coverage gap breaks
    the pair rather than being silently bridged) -- feeds
    ``portfolio_null``'s "this panel" input.
    """
    minute_idx = np.asarray(bars["minute_idx"])
    px = np.asarray(bars["px_last"], dtype=np.float64)
    if minute_idx.size == 0:
        return {}
    order = np.argsort(minute_idx, kind="mergesort")
    minute_idx = minute_idx[order]
    px = px[order]
    day_idx_all = minute_idx // _MIN_PER_DAY

    closes: dict[int, float] = {}
    for d in np.unique(day_idx_all):
        sel = day_idx_all == d
        m, p = minute_idx[sel], px[sel]
        closes[int(d)] = float(p[np.argmax(m)])

    days_sorted = sorted(closes)
    out: dict[str, float] = {}
    for i in range(1, len(days_sorted)):
        d0, d1 = days_sorted[i - 1], days_sorted[i]
        if d1 - d0 != 1:
            continue
        c0, c1 = closes[d0], closes[d1]
        if c0 <= 0.0 or c1 <= 0.0:
            continue
        out[_epoch_day_to_iso(d1)] = float(np.log(c1) - np.log(c0))
    return out


def panel_returns(cache_dir, exchange: str, symbols: list[str],
                  start: str, end: str) -> np.ndarray:
    """Equal-weighted daily log-return panel across ``symbols`` (mean
    across whichever symbols have data on a given day), sorted by date --
    the "auf diesem Bestand" input to ``portfolio_null``.
    """
    from bybit_edge.research.bar_cache import load_minute_bars

    per_symbol = {
        s: daily_close_log_returns(load_minute_bars(cache_dir, exchange, s, start, end))
        for s in symbols
    }
    all_days = sorted(set().union(*per_symbol.values())) if per_symbol else []
    out = []
    for d in all_days:
        vals = [per_symbol[s][d] for s in symbols if d in per_symbol[s]]
        if vals:
            out.append(float(np.mean(vals)))
    return np.asarray(out, dtype=np.float64)
