"""Cross-sectional-z + reversion + axis-B panel realized-vol (H-07, KAPITALFREI).

Implements the M13 formulas on the synchronised 5-min bar panel (``panel.py``):

  * ``E_t[X_i]`` = time-mean of symbol i's bar returns over L=12 bars (60 min,
    M13 "Rolling 1h Returns").
  * ``<X>_t``    = ensemble (cross-sectional) mean of the 5 ``E_t[X_j]``.
  * ``sigma_cross,t`` = cross-sectional std of the 5 ``E_t[X_j]`` at t.
  * ``z_{i,t}``  = (E_t[X_i] - <X>_t) / sigma_cross,t.

Over-stretch events (axis A): ``|z_{i,t}| >= Z_THRESH`` (2.5).

Axis B (non-crash regime): the panel realized-vol at t = sum of squared
contemporaneous 5-symbol bar returns over a forward 15-min window (= 3 bars),
mirroring the c07_pe ``forward_realized_vol`` definition (DEC-12). Axis B holds
when t is NOT in the top decile of the panel-RV distribution in the window.

Reversion-signed forward return per event over h in {1,3,6} bars:
``rev_ret = -sign(z_{i,t}) * R_{i, t->t+h}`` (last-price return over h bars,
strictly causal — never looks past t+h).

KAPITALFREI: pure measurement. No friction, bps, edge, PnL, Sharpe. numpy only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .panel import SyncedPanel

#: Lookback for the per-symbol time-mean (registry H-07 / M13: 12 bars = 60 min).
DEFAULT_LOOKBACK_BARS = 12

#: Over-stretch threshold (registry H-07 / PRD §7.5 / M13: |z| >= 2.5).
DEFAULT_Z_THRESH = 2.5

#: Forward window for panel realized-vol (axis B): 15 min = 3 bars at 5-min bars.
PANEL_RV_BARS = 3

#: Crash decile: axis B excludes the TOP decile of the panel-RV distribution.
DEFAULT_CRASH_DECILE = 0.9

#: Pre-fixed forward horizons in bars (registry H-07: h in {1,3,6}).
DEFAULT_HORIZONS: tuple[int, ...] = (1, 3, 6)


def time_mean_returns(returns: np.ndarray, lookback: int) -> np.ndarray:
    """Trailing mean of bar returns over the last ``lookback`` bars, per symbol.

    ``E_t[X_i] = (1/L) sum_{s=t-L+1..t} R_{i,s}``. Uses returns up to and
    INCLUDING bar t (causal). The first ``lookback`` rows (insufficient history)
    are NaN. ``returns`` is (T, N); row 0 of ``returns`` is itself NaN (no prior
    bar) and is excluded from every window.
    """
    r = np.asarray(returns, dtype=np.float64)
    T, N = r.shape
    out = np.full((T, N), np.nan, dtype=np.float64)
    # valid returns start at row 1 (row 0 has no prior bar).
    for t in range(lookback, T):
        window = r[t - lookback + 1: t + 1, :]
        if np.all(np.isfinite(window)):
            out[t, :] = window.mean(axis=0)
    return out


def cross_sectional_z(time_means: np.ndarray) -> np.ndarray:
    """Cross-sectional z of each symbol's time-mean vs the ensemble at each t.

    ``z_{i,t} = (E_t[X_i] - <X>_t) / sigma_cross,t`` where ``<X>_t`` is the mean
    and ``sigma_cross,t`` the population std of the N time-means at t. Rows with
    any NaN time-mean, or with zero cross-sectional variance, are NaN.
    """
    em = np.asarray(time_means, dtype=np.float64)
    T, N = em.shape
    z = np.full((T, N), np.nan, dtype=np.float64)
    for t in range(T):
        row = em[t, :]
        if not np.all(np.isfinite(row)):
            continue
        mu = row.mean()
        sigma = row.std()  # population std across the N symbols
        if sigma <= 0.0 or not np.isfinite(sigma):
            continue
        z[t, :] = (row - mu) / sigma
    return z


def panel_realized_vol(returns: np.ndarray, horizon_bars: int = PANEL_RV_BARS) -> np.ndarray:
    """Panel RV_t = sum of squared contemporaneous 5-symbol returns over (t, t+h].

    For each bar t, sum ``returns[t+k, j]^2`` over k=1..horizon and all symbols j
    — the forward 15-min panel realized-vol (axis-B crash proxy). Strictly
    forward (uses only bars after t). Trailing positions whose window runs past
    the panel are NaN. Output length == T.
    """
    r = np.asarray(returns, dtype=np.float64)
    T, N = r.shape
    out = np.full(T, np.nan, dtype=np.float64)
    if T <= horizon_bars or horizon_bars < 1:
        return out
    sq = r * r  # (T, N)
    row_sq = np.nansum(sq, axis=1)  # sum over symbols per bar
    # a bar with any non-finite return contributes NaN -> mark it
    row_bad = ~np.all(np.isfinite(r), axis=1)
    row_sq[row_bad] = np.nan
    csum = np.concatenate(([0.0], np.cumsum(np.nan_to_num(row_sq, nan=0.0))))
    bad_csum = np.concatenate(([0], np.cumsum(row_bad.astype(np.int64))))
    last_valid = T - horizon_bars
    for t in range(last_valid):
        # window (t, t+h] = rows t+1 .. t+h
        n_bad = bad_csum[t + 1 + horizon_bars] - bad_csum[t + 1]
        if n_bad > 0:
            out[t] = np.nan
        else:
            out[t] = csum[t + 1 + horizon_bars] - csum[t + 1]
    return out


def non_crash_mask(panel_rv: np.ndarray, crash_decile: float = DEFAULT_CRASH_DECILE) -> np.ndarray:
    """Axis B: True where panel-RV is NOT in the top decile of the window.

    The threshold is the ``crash_decile`` quantile (0.9 => top-10% excluded) of
    the finite panel-RV values in the window. Bars with NaN RV are False (cannot
    confirm non-crash). ``rv <= threshold`` passes.
    """
    rv = np.asarray(panel_rv, dtype=np.float64)
    finite = np.isfinite(rv)
    if int(np.sum(finite)) < 2:
        return np.zeros(rv.size, dtype=bool)
    thr = float(np.quantile(rv[finite], crash_decile))
    mask = np.zeros(rv.size, dtype=bool)
    mask[finite] = rv[finite] <= thr
    return mask


def forward_return_h(last_price: np.ndarray, h: int) -> np.ndarray:
    """Last-price return over h bars per symbol: ``P_{t+h}/P_t - 1`` (causal).

    ``out[t, i] = last_price[t+h, i] / last_price[t, i] - 1``. The trailing h
    rows (no t+h bar) are NaN. Uses only bars up to t+h (no look-ahead beyond).
    """
    px = np.asarray(last_price, dtype=np.float64)
    T, N = px.shape
    out = np.full((T, N), np.nan, dtype=np.float64)
    if h < 1 or T <= h:
        return out
    out[:T - h, :] = px[h:, :] / px[:T - h, :] - 1.0
    return out


@dataclass(slots=True)
class EventTable:
    """Per-(i,t) event columns for one horizon h, gate-neutral.

    All arrays are 1-D and aligned. ``rev_ret`` is the reversion-signed forward
    return; ``is_conditioned`` marks events passing axis A AND axis B; every row
    is a valid baseline (unconditioned) event.
    """

    horizon: int
    z: np.ndarray                 # z_{i,t}
    rev_ret: np.ndarray           # -sign(z) * R_{i,t->t+h}
    is_over_stretch: np.ndarray   # axis A: |z| >= z_thresh
    is_non_crash: np.ndarray      # axis B: not top-decile panel-RV
    is_conditioned: np.ndarray    # axis A AND axis B

    def baseline(self) -> np.ndarray:
        """All finite reversion-signed returns (unconditioned baseline)."""
        return self.rev_ret[np.isfinite(self.rev_ret)]

    def conditioned(self) -> np.ndarray:
        """Reversion-signed returns for events passing axis A AND B."""
        m = self.is_conditioned & np.isfinite(self.rev_ret)
        return self.rev_ret[m]

    @property
    def n_conditioned(self) -> int:
        return int(np.sum(self.is_conditioned & np.isfinite(self.rev_ret)))


def build_event_table(
    panel: SyncedPanel,
    *,
    lookback_bars: int = DEFAULT_LOOKBACK_BARS,
    z_thresh: float = DEFAULT_Z_THRESH,
    crash_decile: float = DEFAULT_CRASH_DECILE,
    panel_rv_bars: int = PANEL_RV_BARS,
    horizon: int = 1,
) -> EventTable:
    """Build the flat per-(i,t) event table for one forward horizon h.

    Computes z, the reversion-signed forward return, and the two conditioning
    axes, then flattens over (symbol, bar). Only rows with a finite z AND a
    finite forward return are retained as events (baseline + conditioned).
    """
    returns = panel.returns
    tmeans = time_mean_returns(returns, lookback_bars)
    z = cross_sectional_z(tmeans)
    rv = panel_realized_vol(returns, panel_rv_bars)
    non_crash = non_crash_mask(rv, crash_decile)  # (T,)
    fwd = forward_return_h(panel.last_price, horizon)  # (T, N)

    T, N = z.shape
    # broadcast axis B (per-bar) across symbols
    non_crash_mat = np.broadcast_to(non_crash[:, None], (T, N))

    z_flat = z.reshape(-1)
    fwd_flat = fwd.reshape(-1)
    non_crash_flat = non_crash_mat.reshape(-1)

    valid = np.isfinite(z_flat) & np.isfinite(fwd_flat)
    z_v = z_flat[valid]
    fwd_v = fwd_flat[valid]
    nc_v = non_crash_flat[valid]

    over_stretch = np.abs(z_v) >= z_thresh
    rev_ret = -np.sign(z_v) * fwd_v
    conditioned = over_stretch & nc_v

    return EventTable(
        horizon=horizon,
        z=z_v,
        rev_ret=rev_ret,
        is_over_stretch=over_stretch,
        is_non_crash=nc_v.astype(bool),
        is_conditioned=conditioned,
    )


__all__ = [
    "DEFAULT_LOOKBACK_BARS",
    "DEFAULT_Z_THRESH",
    "DEFAULT_CRASH_DECILE",
    "DEFAULT_HORIZONS",
    "PANEL_RV_BARS",
    "EventTable",
    "build_event_table",
    "cross_sectional_z",
    "forward_return_h",
    "non_crash_mask",
    "panel_realized_vol",
    "time_mean_returns",
]
