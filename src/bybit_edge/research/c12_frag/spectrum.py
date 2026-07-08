"""Correlation-matrix spectrum + IPR for the H-12 mess-gate (KAPITALFREI).

Per valid UTC day window:
  1. keep the minutes where ALL N series have a valid last price,
  2. log-returns per series over the surviving contemporaneous minutes,
  3. z-standardise per series (registry H-12: per series per day),
  4. correlation matrix C (N x N), eigen-decomposition lambda1 >= .. >= lambdaN,
  5. IPR(v) = sum_i v_i^4 per eigenvector (delocalised ~ 1/N, localised -> 1),
  6. per-exchange v2^2 load (criterion c: largest load on the same exchange).

KAPITALFREI: pure spectral measurement. No friction, bps, PnL, Sharpe.
numpy only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Technical degeneracy guard: minimum contemporaneous returns per day. This is
#: NOT a registered threshold — with the registered day validity (>= 1380/1440
#: valid minutes per series) the intersection has >= 1080 minutes; this guard
#: only catches degenerate synthetic inputs (zero variance / near-empty days).
MIN_RETURNS_PER_DAY = 10


def day_zscored_returns(minute_prices: np.ndarray) -> np.ndarray | None:
    """Z-standardised log-returns on the contemporaneously-valid minutes.

    ``minute_prices`` is (T, N) with NaN for invalid minutes. Rows with any
    NaN are dropped (the correlation matrix needs contemporaneous rows); the
    log-returns are taken between consecutive SURVIVING rows and standardised
    per column (mean 0, population std 1). Returns None if the day is
    degenerate (too few rows or a zero-variance series).
    """
    px = np.asarray(minute_prices, dtype=np.float64)
    keep = np.all(np.isfinite(px), axis=1)
    kept = px[keep, :]
    if kept.shape[0] < MIN_RETURNS_PER_DAY + 1:
        return None
    logret = np.diff(np.log(kept), axis=0)
    mu = logret.mean(axis=0)
    sd = logret.std(axis=0)
    if np.any(~np.isfinite(sd)) or np.any(sd <= 0.0):
        return None
    return (logret - mu) / sd


def correlation_matrix(z: np.ndarray) -> np.ndarray:
    """Correlation matrix of z-standardised returns: C = Z^T Z / T (symmetrised)."""
    z = np.asarray(z, dtype=np.float64)
    t = z.shape[0]
    c = (z.T @ z) / float(t)
    c = 0.5 * (c + c.T)
    np.fill_diagonal(c, 1.0)
    return c


def eig_desc(c: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Eigen-decomposition of a symmetric matrix, DESCENDING eigenvalues.

    Returns ``(lams, vecs)`` with ``lams[0] >= lams[1] >= ...`` and
    ``vecs[:, k]`` the unit eigenvector of ``lams[k]``.
    """
    lams, vecs = np.linalg.eigh(np.asarray(c, dtype=np.float64))
    order = np.argsort(lams)[::-1]
    return lams[order], vecs[:, order]


def ipr(v: np.ndarray) -> float:
    """Inverse participation ratio IPR(v) = sum_i v_i^4 (v normalised first)."""
    v = np.asarray(v, dtype=np.float64)
    nrm = float(np.linalg.norm(v))
    if nrm <= 0.0 or not np.isfinite(nrm):
        return float("nan")
    u = v / nrm
    return float(np.sum(u ** 4))


def exchange_loads(v: np.ndarray, series_exchanges: tuple[str, ...]) -> dict[str, float]:
    """Per-exchange squared eigenvector load: sum of v_i^2 over that exchange's series."""
    v = np.asarray(v, dtype=np.float64)
    if v.size != len(series_exchanges):
        raise ValueError(
            f"eigenvector size {v.size} != n series {len(series_exchanges)}"
        )
    nrm = float(np.linalg.norm(v))
    u = v / nrm if nrm > 0 else v
    loads: dict[str, float] = {}
    for x, ex in zip(u, series_exchanges):
        loads[ex] = loads.get(ex, 0.0) + float(x * x)
    return loads


def dominant_exchange(loads: dict[str, float]) -> str:
    """Exchange with the largest v^2 load; ties break alphabetically (deterministic)."""
    return sorted(loads.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


@dataclass(slots=True)
class DaySpectrum:
    """Spectral measurement of one valid day."""

    t_eff: int
    lams: np.ndarray            # (N,) descending eigenvalues
    v1: np.ndarray              # (N,) top eigenvector
    v2: np.ndarray              # (N,) second eigenvector
    ipr_v1: float
    ipr_v2: float
    exchange_loads_v2: dict[str, float]
    dominant_exchange_v2: str


def analyze_day(
    minute_prices: np.ndarray,
    series_exchanges: tuple[str, ...],
) -> DaySpectrum | None:
    """Full spectral measurement for one day; None if the day is degenerate."""
    z = day_zscored_returns(minute_prices)
    if z is None:
        return None
    c = correlation_matrix(z)
    lams, vecs = eig_desc(c)
    v1 = vecs[:, 0]
    v2 = vecs[:, 1]
    loads = exchange_loads(v2, series_exchanges)
    return DaySpectrum(
        t_eff=int(z.shape[0]),
        lams=lams,
        v1=v1,
        v2=v2,
        ipr_v1=ipr(v1),
        ipr_v2=ipr(v2),
        exchange_loads_v2=loads,
        dominant_exchange_v2=dominant_exchange(loads),
    )


__all__ = [
    "MIN_RETURNS_PER_DAY",
    "DaySpectrum",
    "analyze_day",
    "correlation_matrix",
    "day_zscored_returns",
    "dominant_exchange",
    "eig_desc",
    "exchange_loads",
    "ipr",
]
