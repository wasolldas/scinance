"""WP-7 -- point-in-time universe, delisting handling, survivorship check.

**PIT rule (PRD 4.1 DoD point 4, verbatim):** a symbol is IN the universe
of week ``t`` iff, at the start of week ``t``, it has **>= 8 weeks of
bars** (design parameter, never varied as a threshold -- its effect is
reported as a sensitivity at 4 and 12 weeks, not judged) **AND is still
trading**. A delisted symbol is **NOT retroactively removed**: it is kept
in every week up to and including its last bar, closed at the LAST
traded price ("ein '-100%'-Ansatz waere falsch und gegenlaeufig
verzerrt" -- an assumed-total-loss approach would be wrong and biased in
the opposite direction).

**Why this module also carries a deliberately WRONG reference estimator.**
The DEC-39 adversarial test (T1) requires demonstrating that an
UNCONTROLLED estimator -- one that does not close a delisted symbol at its
true last price but instead assumes the naive "-100%" (total-loss) return
right at delisting -- shows a spurious POSITIVE momentum IC on a
SIGNAL-FREE panel, while the PIT-controlled estimator (this module's
actual, correct API) does not. ``naive_delisting_overlay`` exists ONLY to
give that test something concrete and wrong to compare against; it is
never called by the census pipeline (``report.py`` never imports it for a
real finding) and its docstring says so loudly.

Everything below works on a dense ``[n_weeks, n_symbols]`` return matrix
(weeks in ascending order, symbols in a fixed column order) plus a
boolean "alive" mask of the same shape -- the array-of-weeks convention
already used by WP-7's other modules (``null_ic.py``, ``stats.py``) and by
the DEC-39 fixtures in the test suite. ``weekly_bars_from_daily`` /
``pit_alive_mask_from_bars`` bridge from the real per-symbol daily
``panel_1d`` data (dicts of dates/closes) into that matrix form.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

import numpy as np

__all__ = [
    "MIN_WEEKS_HISTORY", "SENSITIVITY_MIN_WEEKS",
    "spearman_rank_ic", "iso_week_start", "weekly_close_from_daily",
    "pit_alive_mask", "k_per_week", "weekly_ic_series", "pooled_momentum_ic",
    "naive_delisting_overlay", "momentum_ic_series",
]

#: Design parameter (PRD 4.1 DoD point 4): >= 8 weeks of bars required
#: before a symbol enters the point-in-time universe. Never varied as a
#: threshold that changes a verdict -- ONLY its effect is reported, at the
#: two sensitivity points below.
MIN_WEEKS_HISTORY = 8
SENSITIVITY_MIN_WEEKS: tuple[int, ...] = (4, 12)


# ----------------------------------------------------------------------------
# rank correlation (no scipy dependency, repo convention -- see wp5_optchain
# .census.quantile for the same "small, dependency-free, hand-tested" style)
# ----------------------------------------------------------------------------

def _average_ranks(a: np.ndarray) -> np.ndarray:
    """1-indexed ranks with ties resolved to the average rank of the tied
    group (standard Spearman tie-breaking)."""
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), dtype=np.float64)
    ranks[order] = np.arange(1, len(a) + 1, dtype=np.float64)
    sorted_a = a[order]
    i = 0
    n = len(a)
    while i < n:
        j = i
        while j + 1 < n and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    return ranks


def spearman_rank_ic(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation of ``x`` and ``y`` (equal length, no
    NaNs expected -- callers mask beforehand). Returns 0.0 for a
    degenerate (zero-variance) input rather than NaN, since a
    cross-section with a single distinct value carries no ranking
    information."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if len(x) < 2:
        return 0.0
    rx = _average_ranks(x) - _average_ranks(x).mean()
    ry = _average_ranks(y) - _average_ranks(y).mean()
    denom = math.sqrt(float((rx * rx).sum()) * float((ry * ry).sum()))
    if denom == 0.0:
        return 0.0
    return float((rx * ry).sum() / denom)


# ----------------------------------------------------------------------------
# daily -> weekly bridge
# ----------------------------------------------------------------------------

def iso_week_start(d: date) -> date:
    """Monday of ``d``'s ISO week (the week-bucket key used throughout)."""
    return d - timedelta(days=d.weekday())


def weekly_close_from_daily(dates: list[str], closes: list[float]) -> dict[str, float]:
    """Daily ``(date, close)`` pairs -> one close per ISO week (the LAST
    daily close of each week, deterministic given pre-sorted input; if
    unsorted, sorts by date first). Returns ``{week_start_iso: close}``."""
    pairs = sorted(zip(dates, closes), key=lambda p: p[0])
    out: dict[str, float] = {}
    for d_str, c in pairs:
        wk = iso_week_start(date.fromisoformat(d_str)).isoformat()
        out[wk] = c  # last write wins -> last close of the week
    return out


# ----------------------------------------------------------------------------
# PIT universe (array form)
# ----------------------------------------------------------------------------

def pit_alive_mask(first_bar_week: np.ndarray, last_bar_week: np.ndarray,
                    n_weeks: int, *, min_weeks_history: int = MIN_WEEKS_HISTORY) -> np.ndarray:
    """``[n_weeks, n_symbols]`` bool mask: symbol ``s`` is a member of
    ``U_t`` iff it has >= ``min_weeks_history`` weeks of bars as of week
    ``t`` (``t - first_bar_week[s] >= min_weeks_history``) AND has not yet
    been delisted (``t <= last_bar_week[s]``). A delisted symbol is kept
    through its ``last_bar_week`` (closed at the last price by the
    CALLER's return series -- this function only decides membership) and
    simply absent afterward -- never retroactively removed from earlier
    weeks.
    """
    first_bar_week = np.asarray(first_bar_week, dtype=np.int64)
    last_bar_week = np.asarray(last_bar_week, dtype=np.int64)
    t = np.arange(n_weeks, dtype=np.int64)[:, None]
    has_history = (t - first_bar_week[None, :]) >= min_weeks_history
    still_trading = t <= last_bar_week[None, :]
    started = t >= first_bar_week[None, :]
    return has_history & still_trading & started


def k_per_week(alive: np.ndarray) -> np.ndarray:
    """K(t) = |U_t| -- the participation count per week."""
    return alive.sum(axis=1)


def weekly_ic_series(signal: np.ndarray, outcome: np.ndarray, alive: np.ndarray,
                      *, min_universe: int = 10) -> np.ndarray:
    """Per-week Spearman IC of ``signal[t]`` (any characteristic, one row
    per week) against ``outcome[t]`` (the same week's realised value --
    typically ``returns[t+1]`` passed in already shifted by the caller),
    restricted to ``alive[t]`` each week. ``NaN`` for a week below
    ``min_universe``. General-purpose: this is the SAME per-week-then-
    average style the spec's ``SD_null`` measurement uses (``null_ic.py``),
    just fed a real characteristic instead of a permutation.
    """
    n_weeks = signal.shape[0]
    out = np.full(n_weeks, np.nan, dtype=np.float64)
    for t in range(n_weeks):
        mask = alive[t]
        if int(mask.sum()) < min_universe:
            continue
        out[t] = spearman_rank_ic(signal[t, mask], outcome[t, mask])
    return out


# ----------------------------------------------------------------------------
# survivorship-adversarial machinery (DEC-39 trio, item 3)
# ----------------------------------------------------------------------------

def naive_delisting_overlay(returns: np.ndarray, alive: np.ndarray,
                             *, naive_return: float = -1.0) -> np.ndarray:
    """**ANTI-PATTERN -- reference implementation ONLY, never for
    production use.** Returns a COPY of ``returns`` where every symbol's
    LAST alive week is overwritten with ``naive_return`` (default -100%,
    the exact "-100%-Ansatz" the spec names and rejects, PRD 4.1 DoD point
    4) instead of the true observed return at that week. This is what an
    estimator looks like when it does NOT close a delisted position at
    its last traded price -- the wrong alternative the PIT-controlled
    estimator (``momentum_ic_series`` fed the real ``returns``/``alive``)
    is tested against in the DEC-39 adversarial fixture.
    """
    out = np.array(returns, dtype=np.float64, copy=True)
    n_weeks, n_symbols = alive.shape
    for s in range(n_symbols):
        col = alive[:, s]
        if not col.any():
            continue
        last_week = int(np.nonzero(col)[0].max())
        out[last_week, s] = naive_return
    return out


def momentum_ic_series(
    returns: np.ndarray, alive: np.ndarray, *, trail_win: int = 4,
    min_start: int | None = None,
) -> dict[str, Any]:
    """Pooled cross-week momentum-IC significance check.

    Signal at week ``t`` = trailing ``trail_win``-week cumulative return
    ending at ``t``; outcome = week ``t+1``'s return. Every week's
    universe is ``alive[t] & alive[t+1]`` (a symbol contributes a pair
    only where BOTH weeks are real, PIT-correctly excluding a delisted
    symbol from every week after its last bar -- no special-casing
    needed, the mask alone gives point-in-time behaviour). All
    (signal, outcome) pairs across the window are POOLED into one
    Spearman correlation and its Fisher-z significance (not a per-week
    IC average) -- pooling is what gives DEC-39's adversarial fixture the
    statistical power to tell a `t<sub>0</sub>10` contamination episode
    per doomed symbol apart from a signal-free background at a fixed,
    modest ``K``/``W``; the main SD_null measurement (``null_ic.py``)
    remains the per-week estimator the spec's arithmetic (DEC-51/52) is
    built on -- this pooled statistic is a DIAGNOSTIC for the
    survivorship check only, not a WP-7 headline number.
    """
    n_weeks, n_symbols = returns.shape
    if min_start is None:
        min_start = trail_win
    trail = np.full((n_weeks, n_symbols), np.nan)
    for t in range(n_weeks):
        lo = max(0, t - trail_win + 1)
        trail[t] = returns[lo:t + 1].sum(axis=0)

    sigs: list[np.ndarray] = []
    outs: list[np.ndarray] = []
    for t in range(min_start, n_weeks - 1):
        mask = alive[t] & alive[t + 1]
        if mask.sum() < 10:
            continue
        sigs.append(trail[t, mask])
        outs.append(returns[t + 1, mask])
    if not sigs:
        return {"rho": 0.0, "t_stat": 0.0, "n_pairs": 0, "n_weeks_used": 0}
    sig = np.concatenate(sigs)
    out = np.concatenate(outs)
    rho = spearman_rank_ic(sig, out)
    n = len(sig)
    if n <= 3 or abs(rho) >= 1.0:
        t_stat = float("inf") if abs(rho) >= 1.0 else 0.0
    else:
        se = 1.0 / math.sqrt(n - 3)
        z = 0.5 * math.log((1 + rho) / (1 - rho))
        t_stat = z / se
    return {"rho": rho, "t_stat": t_stat, "n_pairs": n, "n_weeks_used": len(sigs)}


def pooled_momentum_ic(returns: np.ndarray, alive: np.ndarray, **kwargs: Any) -> dict[str, Any]:
    """Alias of :func:`momentum_ic_series` (name used by the adversarial
    test for readability at the call site: "the pooled momentum IC of
    this estimator")."""
    return momentum_ic_series(returns, alive, **kwargs)
