"""PRE-Gate for the C-07 PE mess-gate (Welle-2 WP, H-06, KAPITALFREI).

The PRE-Gate is the hard, cheap pre-condition that MUST pass before the (more
expensive) main gate runs (registry H-06 / PRD §4 wörtlich): the rank
correlation rho between the PE-DROP at bar t and the downstream VOL-CLUSTER in
the forward 15-min window ``(t, t+15min]`` must be ``>= 0.30`` on ``>= 2``
disjoint windows. ``rho < 0.30`` in ONE window => DROP, no main run (hard
one-window criterion, PRD §8.5). This module measures rho PER WINDOW; it renders
NO verdict.

Vol-cluster definition (DEC-12, claims_register §C-07 wörtlich "[t, t+15min]"):
the realized volatility over the forward window is the sum of squared 1-min
log-returns over ``(t, t+15min]`` (i.e. the next 15 bars at 1-min resolution).
This is strictly causal — it uses only bars AFTER t, so it never overlaps the
returns the PE / PE-drop at t was computed from.

Correlation choice (DEC-12): SPEARMAN rank correlation. Rank is robust to the
heavy tails of crypto realized vol and to the nonlinear PE-vol monotonicity; the
rho >= 0.3 floor comes from PRD-v1 / claims_register and is, as a rank-association
floor, conservative and method-neutral.

KAPITALFREI: pure rank-correlation measurement. No friction, edge, bps, PnL,
Sharpe logic. numpy only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: PRE-Gate registered correlation floor (registry H-06 / PRD §4): rho >= 0.30.
RHO_FLOOR = 0.30

#: Forward vol-cluster horizon in bars (= 15 min at 1-min klines, claims_register
#: §C-07 "[t, t+15min]"). 1-min resolution -> 15 bars.
VOL_CLUSTER_BARS = 15


def forward_realized_vol(returns: np.ndarray, horizon_bars: int = VOL_CLUSTER_BARS) -> np.ndarray:
    """Forward realized vol: sum of squared returns over ``(t, t+horizon]`` bars.

    ``rv[i] = sum_{k=1..horizon} returns[i+k]^2`` — strictly forward, so it shares
    no bar with anything computed up to and including bar ``i``. The trailing
    ``horizon`` positions (whose forward window runs past the series) are NaN.
    Output length == len(returns).
    """
    r = np.asarray(returns, dtype=np.float64)
    n = r.size
    out = np.full(n, np.nan, dtype=np.float64)
    if n <= horizon_bars or horizon_bars < 1:
        return out
    sq = r * r
    # cumulative sum trick: forward window sum (i, i+horizon]
    csum = np.concatenate(([0.0], np.cumsum(sq)))
    # rv[i] = csum[i+1+horizon] - csum[i+1]
    last_valid = n - horizon_bars
    i = np.arange(last_valid)
    out[i] = csum[i + 1 + horizon_bars] - csum[i + 1]
    return out


def spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation; 0.0 if too few finite pairs or no variance."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = min(x.size, y.size)
    if n < 3:
        return 0.0
    x, y = x[:n], y[:n]
    mask = np.isfinite(x) & np.isfinite(y)
    if int(np.sum(mask)) < 3:
        return 0.0
    xr = _rankdata(x[mask])
    yr = _rankdata(y[mask])
    xs = xr - xr.mean()
    ys = yr - yr.mean()
    denom = float(np.sqrt(np.sum(xs * xs) * np.sum(ys * ys)))
    if denom == 0.0 or not np.isfinite(denom):
        return 0.0
    r = float(np.sum(xs * ys) / denom)
    if not np.isfinite(r):
        return 0.0
    return max(-1.0, min(1.0, r))


def _rankdata(a: np.ndarray) -> np.ndarray:
    """Average-rank of ``a`` (ties get the mean of their ranks)."""
    a = np.asarray(a, dtype=np.float64)
    order = np.argsort(a, kind="stable")
    ranks = np.empty(a.size, dtype=np.float64)
    ranks[order] = np.arange(1, a.size + 1, dtype=np.float64)
    # average ties
    _, inv, counts = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.zeros(counts.size, dtype=np.float64)
    np.add.at(sums, inv, ranks)
    avg = sums / counts
    return avg[inv]


@dataclass(slots=True)
class PreGateResult:
    """PRE-Gate outcome for one window: rho(PE-drop, forward vol-cluster)."""

    n_pairs: int
    rho: float
    rho_floor: float
    rho_floor_met: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "n_pairs": int(self.n_pairs),
            "rho": float(self.rho),
            "rho_floor": float(self.rho_floor),
            "rho_floor_met": bool(self.rho_floor_met),
        }


def pre_gate(
    pe_drop_series: np.ndarray,
    forward_rv: np.ndarray,
    *,
    rho_floor: float = RHO_FLOOR,
) -> PreGateResult:
    """Measure PRE-Gate rho between PE-drop and forward vol-cluster for a window.

    Both inputs are bar-aligned (PE-drop at t vs. forward RV starting just after
    t). Only positions finite in BOTH series enter the rank correlation. Reports
    rho and whether it clears the registered floor; renders NO verdict.
    """
    pd_ = np.asarray(pe_drop_series, dtype=np.float64)
    rv = np.asarray(forward_rv, dtype=np.float64)
    n = min(pd_.size, rv.size)
    pd_, rv = pd_[:n], rv[:n]
    mask = np.isfinite(pd_) & np.isfinite(rv)
    n_pairs = int(np.sum(mask))
    rho = spearman_rho(pd_[mask], rv[mask]) if n_pairs >= 3 else 0.0
    return PreGateResult(
        n_pairs=n_pairs,
        rho=rho,
        rho_floor=rho_floor,
        rho_floor_met=bool(rho >= rho_floor),
    )
