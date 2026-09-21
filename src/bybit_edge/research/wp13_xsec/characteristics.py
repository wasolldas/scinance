"""WP-13 -- F-XSEC1 characteristics (PRD 5.3, DEC-73/74), PURE functions.

All "real-data" (daily-refined) characteristics here are point-in-time
(PIT): a characteristic at week ``t`` uses only data observed up to and
including week ``t`` (week ``t``'s own daily bars are all closed by the
end of week ``t``, so they are legitimately PIT for a signal meant to
predict week ``t+1``'s outcome -- the same convention
``wp7_universe.panel_load.momentum_signal`` already uses for momentum).
Every function here is agnostic to whether ``returns``/``alive`` come
from ``wp7_universe.panel_load.weekly_returns_and_mask`` or its
``_union`` variant (DEC-72/DEC-73's union panel is the real caller).

**DEC-74 Entscheidung 2(j) alignment convention.** Every characteristic
function below returns an array ``char[t, j]`` meant to be compared
against ``returns[t+1, j]`` -- the SAME "signal at t predicts outcome at
t+1" convention ``pit_universe.weekly_ic_series``/``momentum_ic_series``
already use. ``ic.weekly_ic_series`` (this package) is the sole caller
that performs that t -> t+1 lookup; nothing here shifts ``returns``
itself.

**Reversal Gap-Design deviation (PRD 5.3, verbatim: "Formation und
Halteperiode um einen Tag getrennt", i.e. a ONE-DAY gap) -- documented
here as required by the task brief, flagged for orchestrator confirmation
before the Zweitfassung run.** WP-13 operates exclusively on the WEEKLY
``panel_1d``/``panel_1d_delisted`` union (PRD 5.3: "Vollstaendig aus dem
WP-7-``panel_1d``"); there is no daily signal/outcome pipeline in this
package. The smallest gap representable on a weekly grid is therefore ONE
WEEK, not one day: formation is week ``t-1``'s return, held for week
``t+1``'s return, with week ``t`` entirely skipped as the gap (instead of
skipping the final day of week ``t-1`` / first day of week ``t+1`` as the
PRD's literal wording describes). This is a REAL, structural deviation
from the registered PRD text, not a rounding choice -- it changes what
the "Bid-Ask-Bounce" control actually eliminates (a full week of
mean-reversion opportunity between formation and holding, instead of one
day) and must be confirmed by the Orchestrator before the Zweitfassung
registration cites it as satisfying PRD 5.3's Gap-Design requirement.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any

import numpy as np

from ..wp7_universe import pit_universe

__all__ = [
    "MOMENTUM_TRAIL_WEEKS", "VOL_BETA_TRAIL_WEEKS", "LIQUIDITY_TRAIL_WEEKS",
    "VARIANT_NAMES", "momentum_characteristic", "reversal_gap_characteristic",
    "daily_log_returns", "realized_vol_characteristic", "max_return_characteristic",
    "beta_characteristic", "weekly_turnover", "trailing_median_turnover",
    "decile_bucket", "compute_all_characteristics",
    "weekly_only_proxy_characteristic", "WEEKLY_ONLY_VARIANT_NAMES",
]

#: PRD 5.3: momentum formation lengths 1/2/4 weeks.
MOMENTUM_TRAIL_WEEKS: tuple[int, ...] = (1, 2, 4)
#: PRD 5.3 A3-V: beta to BTCUSDT over a TRAILING 8-week window.
VOL_BETA_TRAIL_WEEKS = 8
#: DEC-74 (f): liquidity decile from a trailing 8-week MEDIAN turnover, PIT.
LIQUIDITY_TRAIL_WEEKS = 8

#: The K=7 F-XSEC1 cohort (DEC-73 Entscheidung 1), stable order used
#: everywhere a per-variant table is built (BH-FDR unit, DEC-74 (e)).
VARIANT_NAMES: tuple[str, ...] = (
    "mom1", "mom2", "mom4", "rev_gap", "vol_rv", "vol_max", "vol_beta",
)


# ----------------------------------------------------------------------------
# momentum / reversal-gap -- weekly-return-only (no daily data needed)
# ----------------------------------------------------------------------------

def momentum_characteristic(returns: np.ndarray, *, trail_win: int) -> np.ndarray:
    """Trailing ``trail_win``-week SUM of log returns ending at (and
    including) week ``t`` -- PRD 5.3 A3-M, identical arithmetic to
    ``wp7_universe.panel_load.momentum_signal`` (reused, not
    reimplemented, for ``trail_win=4``; generalised here to 1/2/4)."""
    n_weeks = returns.shape[0]
    trail = np.full_like(returns, np.nan)
    for t in range(n_weeks):
        lo = max(0, t - trail_win + 1)
        trail[t] = returns[lo:t + 1].sum(axis=0)
    return trail


def reversal_gap_characteristic(returns: np.ndarray) -> np.ndarray:
    """PRD 5.3 A3-R, PRIMARY Gap-Design (see module docstring for the
    one-day-vs-one-week deviation): ``char[t] = returns[t-1]`` (the single
    week ``t-1``'s return, i.e. formation ends a full week before the
    holding period, which starts at week ``t+1`` once ``ic.py`` applies
    its usual t -> t+1 lookup) -- week ``t`` itself is never touched, so
    it is the gap. ``char[0]`` is NaN (no week ``-1``)."""
    char = np.full_like(returns, np.nan)
    char[1:] = returns[:-1]
    return char


# ----------------------------------------------------------------------------
# vol characteristics -- daily-refined (REAL data only; never fed to ic.py
# with a real outcome -- used for descriptive reachability/feasibility only
# in --prelaunch, see prelaunch.py)
# ----------------------------------------------------------------------------

def daily_log_returns(panel: dict[str, Any]) -> np.ndarray:
    """``[n_days, n_symbols]`` daily log returns from ``panel['close']``.
    Same "a gap never manufactures a return" discipline as
    ``panel_load._daily_close_to_weekly``: only CONSECUTIVE observed days
    (row index difference of exactly 1) get a return; everything else is
    NaN."""
    close = panel["close"]
    n_days, n_symbols = close.shape
    out = np.full((n_days, n_symbols), np.nan, dtype=np.float64)
    for j in range(n_symbols):
        idx = np.flatnonzero(~np.isnan(close[:, j]))
        for k in range(1, idx.size):
            i0, i1 = int(idx[k - 1]), int(idx[k])
            if i1 - i0 != 1:
                continue
            c0, c1 = close[i0, j], close[i1, j]
            if c0 > 0 and c1 > 0:
                out[i1, j] = math.log(c1 / c0)
    return out


def _week_row_groups(panel: dict[str, Any], weeks: list[str]) -> dict[int, list[int]]:
    """Daily row indices of ``panel`` grouped by their position in
    ``weeks`` (ISO-week-start grid) -- shared helper for every
    daily-to-weekly aggregation in this module."""
    dates = panel["dates"]
    week_pos = {w: i for i, w in enumerate(weeks)}
    groups: dict[int, list[int]] = {}
    for i, d in enumerate(dates):
        wk = pit_universe.iso_week_start(date.fromisoformat(d)).isoformat()
        wi = week_pos.get(wk)
        if wi is None:
            continue
        groups.setdefault(wi, []).append(i)
    return groups


def realized_vol_characteristic(panel: dict[str, Any], weeks: list[str], *,
                                 daily_ret: np.ndarray | None = None,
                                 min_days: int = 2) -> np.ndarray:
    """Realized weekly vol: SD of week ``t``'s OWN daily log returns
    (``ddof=1``), NaN if fewer than ``min_days`` daily returns observed
    that week -- PRD 5.3 A3-V, computed from ``panel['close']`` (real
    daily data), PIT by construction (week ``t`` is fully observed by the
    time it ends)."""
    if daily_ret is None:
        daily_ret = daily_log_returns(panel)
    n_symbols = daily_ret.shape[1]
    n_weeks = len(weeks)
    out = np.full((n_weeks, n_symbols), np.nan, dtype=np.float64)
    groups = _week_row_groups(panel, weeks)
    for wi, rows in groups.items():
        block = daily_ret[rows, :]
        valid = ~np.isnan(block)
        n_valid = valid.sum(axis=0)
        for j in range(n_symbols):
            if n_valid[j] >= min_days:
                out[wi, j] = float(np.std(block[valid[:, j], j], ddof=1))
    return out


def max_return_characteristic(panel: dict[str, Any], weeks: list[str], *,
                               daily_ret: np.ndarray | None = None) -> np.ndarray:
    """MAX daily log return within week ``t`` (PRD 5.3 A3-V's "MAX"
    lottery-demand characteristic), NaN if the week has no observed daily
    return for that symbol."""
    if daily_ret is None:
        daily_ret = daily_log_returns(panel)
    n_symbols = daily_ret.shape[1]
    n_weeks = len(weeks)
    out = np.full((n_weeks, n_symbols), np.nan, dtype=np.float64)
    groups = _week_row_groups(panel, weeks)
    for wi, rows in groups.items():
        block = daily_ret[rows, :]
        valid = ~np.isnan(block)
        for j in range(n_symbols):
            col = block[valid[:, j], j]
            if col.size:
                out[wi, j] = float(col.max())
    return out


def beta_characteristic(returns: np.ndarray, symbols: list[str], *,
                         market_symbol: str = "BTCUSDT",
                         trail_win: int = VOL_BETA_TRAIL_WEEKS,
                         min_weeks: int = 4) -> np.ndarray:
    """OLS beta to ``market_symbol`` over the TRAILING ``trail_win`` weeks
    ending at (and including) week ``t`` -- weekly-returns-only (no daily
    data needed), PIT. NaN where the market symbol is absent from
    ``symbols``, where fewer than ``min_weeks`` of the trailing window
    have a finite market return, or where the market's trailing variance
    is zero."""
    n_weeks, n_symbols = returns.shape
    out = np.full((n_weeks, n_symbols), np.nan, dtype=np.float64)
    if market_symbol not in symbols:
        return out
    m = symbols.index(market_symbol)
    mkt = returns[:, m]
    for t in range(n_weeks):
        lo = max(0, t - trail_win + 1)
        mkt_win = mkt[lo:t + 1]
        valid_m = ~np.isnan(mkt_win)
        if int(valid_m.sum()) < min_weeks:
            continue
        mkt_v = mkt_win[valid_m]
        var_m = float(np.var(mkt_v, ddof=1)) if mkt_v.size > 1 else 0.0
        if var_m <= 0.0:
            continue
        mkt_c = mkt_v - mkt_v.mean()
        for j in range(n_symbols):
            sym_win = returns[lo:t + 1, j][valid_m]
            if np.isnan(sym_win).any():
                continue
            n_win = sym_win.size
            cov = float(np.sum((sym_win - sym_win.mean()) * mkt_c) / (n_win - 1))
            out[t, j] = cov / var_m
    return out


# ----------------------------------------------------------------------------
# liquidity / turnover (Gate (5) reachability, DEC-74 (f) sensitivity)
# ----------------------------------------------------------------------------

def weekly_turnover(panel: dict[str, Any], weeks: list[str]) -> np.ndarray:
    """``[n_weeks, n_symbols]`` weekly SUM of ``panel['turnover']`` (NaN
    days contribute 0, matching ``panel_load.funding_excess_weekly``'s
    "a missing day is 0, not NaN, in a SUM key" discipline)."""
    turnover = panel["turnover"]
    n_symbols = turnover.shape[1]
    n_weeks = len(weeks)
    out = np.zeros((n_weeks, n_symbols), dtype=np.float64)
    groups = _week_row_groups(panel, weeks)
    for wi, rows in groups.items():
        out[wi] = np.nansum(turnover[rows, :], axis=0)
    return out


def trailing_median_turnover(weekly_turnover_arr: np.ndarray, *,
                              trail_win: int = LIQUIDITY_TRAIL_WEEKS) -> np.ndarray:
    """Trailing ``trail_win``-week MEDIAN of ``weekly_turnover_arr``,
    ending at (and including) week ``t`` -- PIT, DEC-74 (f)'s liquidity
    key. Zero-turnover weeks (no data yet, or a genuinely dead week) are
    included as zeros -- ``weekly_turnover`` never returns NaN."""
    n_weeks, n_symbols = weekly_turnover_arr.shape
    out = np.full((n_weeks, n_symbols), np.nan, dtype=np.float64)
    for t in range(n_weeks):
        lo = max(0, t - trail_win + 1)
        out[t] = np.median(weekly_turnover_arr[lo:t + 1], axis=0)
    return out


def decile_bucket(values: np.ndarray, alive_row: np.ndarray) -> np.ndarray:
    """Per-symbol decile index (1..10, ascending value) among that week's
    ``alive_row`` symbols; -1 for a symbol not alive that week. Same
    "split the sorted alive list into 10 nearly-equal groups" convention
    as ``panel_load.funding_deadzone_census``'s decile assignment."""
    n_symbols = values.shape[0]
    out = np.full(n_symbols, -1, dtype=np.int64)
    idx = np.flatnonzero(alive_row)
    if idx.size == 0:
        return out
    order = idx[np.argsort(values[idx], kind="mergesort")]
    n = order.size
    for d in range(10):
        lo, hi = (n * d) // 10, (n * (d + 1)) // 10
        out[order[lo:hi]] = d + 1
    return out


# ----------------------------------------------------------------------------
# dispatch -- the 7-variant F-XSEC1 cohort, REAL (daily-refined) construction
# ----------------------------------------------------------------------------

def compute_all_characteristics(
    returns: np.ndarray, panel: dict[str, Any], weeks: list[str], symbols: list[str],
) -> dict[str, np.ndarray]:
    """All 7 F-XSEC1 variants (real, daily-refined where the PRD calls for
    daily data), each ``[n_weeks, n_symbols]``, keyed by ``VARIANT_NAMES``.
    Never touches ``returns[t+1]`` (the outcome) -- purely a function of
    data available up to week ``t``."""
    daily_ret = daily_log_returns(panel)
    return {
        "mom1": momentum_characteristic(returns, trail_win=1),
        "mom2": momentum_characteristic(returns, trail_win=2),
        "mom4": momentum_characteristic(returns, trail_win=4),
        "rev_gap": reversal_gap_characteristic(returns),
        "vol_rv": realized_vol_characteristic(panel, weeks, daily_ret=daily_ret),
        "vol_max": max_return_characteristic(panel, weeks, daily_ret=daily_ret),
        "vol_beta": beta_characteristic(returns, symbols),
    }


# ----------------------------------------------------------------------------
# weekly-only proxies -- used EXCLUSIVELY by nulls.py's persistence-null
# simulation (an AR(1)-simulated return panel has no intraweek daily path
# and no designated market symbol to regress against -- see nulls.py
# module docstring for the full deviation writeup).
# ----------------------------------------------------------------------------

WEEKLY_ONLY_VARIANT_NAMES = VARIANT_NAMES


def weekly_only_proxy_characteristic(name: str, sim_returns: np.ndarray) -> np.ndarray:
    """The persistence-null's per-variant characteristic, computed
    EXCLUSIVELY from a simulated ``[n_weeks, n_symbols]`` weekly-return
    panel (``nulls.py``'s AR(1) simulation has no daily granularity and no
    real BTCUSDT column to regress against). ``mom1/mom2/mom4/rev_gap``
    are IDENTICAL to the real construction (they were already weekly-only
    -- no proxy needed). ``vol_rv``/``vol_max`` use ``abs(sim_returns[t])``
    as a documented single-week realized-vol/MAX proxy (the null pipeline
    cannot see inside a week); ``vol_beta`` regresses each symbol's
    trailing window against the simulated panel's OWN cross-sectional
    mean return each week (a market-factor proxy, since no symbol is
    designated "BTC" under the per-symbol-independent AR(1) null) --
    documented deviations, NOT the real-data construction, used only to
    calibrate the persistence-null quantile/`c_rho` (DEC-74 (b)/(c))."""
    if name in ("mom1", "mom2", "mom4"):
        return momentum_characteristic(sim_returns, trail_win=int(name[-1]))
    if name == "rev_gap":
        return reversal_gap_characteristic(sim_returns)
    if name in ("vol_rv", "vol_max"):
        return np.abs(sim_returns)
    if name == "vol_beta":
        n_weeks, n_symbols = sim_returns.shape
        mkt = np.nanmean(sim_returns, axis=1)
        synthetic_symbols = ["__mkt__" if j == n_symbols else f"s{j}" for j in range(n_symbols + 1)]
        padded = np.concatenate([sim_returns, mkt[:, None]], axis=1)
        beta = beta_characteristic(padded, synthetic_symbols, market_symbol="__mkt__")
        return beta[:, :n_symbols]
    raise ValueError(f"unknown variant {name!r} -- expected one of {VARIANT_NAMES}")
