"""IK-05: random-matrix factor count of the residual correlation matrix of daily returns (Zone X).

Question (PRD_ANALYSE addendum 1, sweep IK-05, S-4): does the correlation matrix of the market residuals of the
daily returns have eigenvalues above the Marchenko-Pastur edge (1 + sqrt(K/T))^2, and how many?  An eigenvalue of
at least ``LAMBDA_NEEDED`` = 6.25 (= 1 + 2.5^2 - 1) is the minimum for a factor structure to explain a 2.5-fold
inflation of the cross-sectional IC dispersion of class W; no such eigenvalue means the inflation comes from
variation over time.

Design choices (documented as the specification demands)
  * Balanced sub-panel, not pairwise deletion.  On the days with a market factor (>= ``MIN_CROSS_SECTION`` symbols)
    a symbol is kept if it has a return on at least ``coverage_min`` (default 90 %) of those days; the matrix is then
    estimated on the days on which ALL kept symbols have a return (complete cases).  K is the number of kept symbols,
    T the number of complete days.  A pairwise-deleted matrix is not positive semi-definite and has no clean MP
    edge; the price of balancing is that T can be well below the window length (reported as ``t_days``).
  * Raw returns and residuals use exactly the same K x T block, so the two spectra are directly comparable.
  * Residuals e = r - beta r_M with the equal-weighted market factor of the window (see ``common``).  The market
    factor, betas and residuals are recomputed inside every sub-window.
  * Spearman: the same blocks after average ranking of every column.
  * The MP edge is the formula edge only; heavy tails raise the true noise edge, so ``n_above_edge`` is an upper
    bound for the factor count.  ``n_ge_lambda_needed`` is the decision-relevant count.
Only eigenvalues, counts and shares are output: no mean, no sign, no series.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import date
from typing import Any

import numpy as np
from scipy.stats import rankdata

from . import common

__all__ = [
    "LAMBDA_NEEDED", "SUBWINDOWS", "TOP_EIGENVALUES", "analyse_window", "balanced_subpanel",
    "correlation_eigenvalues", "mp_edge", "run_ik05", "spectrum_summary",
]

#: Eigenvalue needed for SD ratio 2.5 at full alignment: 1 + (2.5^2 - 1) = 6.25.
LAMBDA_NEEDED = 6.25
TOP_EIGENVALUES = 20
#: Robustness sub-windows (inclusive ISO dates); each is re-analysed from scratch.
SUBWINDOWS: tuple[tuple[str, str, str], ...] = (
    ("sub1", "2021-01-01", "2022-02-28"),
    ("sub2", "2022-03-01", "2023-04-30"),
    ("sub3", "2023-05-01", "2024-06-30"),
)
MIN_BALANCED_SYMBOLS = 3
MIN_BALANCED_DAYS = 30
METHOD_TEXT = ("balanced sub-panel: symbols with coverage >= coverage_min of the days that have a market factor, "
               "then the days on which all of them have a return; MP edge (1+sqrt(K/T))^2; "
               "residual = r - beta r_M; Spearman = Pearson of average ranks")


def mp_edge(k: int, t: int) -> float:
    """Upper edge of the Marchenko-Pastur law for K variables and T observations: (1 + sqrt(K/T))^2."""
    if k <= 0 or t <= 0:
        raise ValueError(f"mp_edge needs K > 0 and T > 0, got K={k}, T={t}")
    return (1.0 + math.sqrt(k / t)) ** 2


def correlation_eigenvalues(x: np.ndarray, *, rank: bool = False) -> np.ndarray:
    """Eigenvalues (descending) of the correlation matrix of the columns of ``x`` (T x K, no missing values).

    ``rank=True`` replaces every column by its average ranks first (Spearman).  Columns must not be constant."""
    a = np.asarray(x, dtype=np.float64)
    if a.ndim != 2 or a.shape[0] < 2 or a.shape[1] < 1:
        raise ValueError("x must be a 2-D array with at least two rows")
    if not np.isfinite(a).all():
        raise ValueError("x contains missing values")
    if rank:
        a = rankdata(a, axis=0, method="average")
    z = a - a.mean(axis=0)
    sd = z.std(axis=0)
    if not (sd > 0.0).all():
        raise ValueError("x contains a constant column")
    z = z / sd
    c = (z.T @ z) / z.shape[0]
    c = 0.5 * (c + c.T)
    return np.linalg.eigvalsh(c)[::-1].copy()


def spectrum_summary(eigenvalues: np.ndarray, edge: float) -> dict[str, Any]:
    """Top eigenvalues, count and variance share above the edge, count at or above ``LAMBDA_NEEDED``."""
    eig = np.asarray(eigenvalues, dtype=np.float64)
    above = eig > edge
    return {
        "top_eigenvalues": [float(v) for v in eig[:TOP_EIGENVALUES]],
        "n_above_edge": int(above.sum()),
        "explained_share_above_edge": float(eig[above].sum() / eig.size),
        "n_ge_lambda_needed": int((eig >= LAMBDA_NEEDED).sum()),
    }


def balanced_subpanel(r: np.ndarray, eligible: np.ndarray, coverage_min: float
                      ) -> tuple[np.ndarray, np.ndarray, int]:
    """Rows and columns of the balanced sub-panel of ``r`` (days x symbols).

    ``eligible`` (bool per day) marks the days with a market factor.  Returns ``(rows, cols, n_covered)`` where
    ``cols`` are the symbols with coverage >= ``coverage_min`` on the eligible days and ``rows`` the eligible days on
    which all of ``cols`` have a return."""
    rows0 = np.flatnonzero(eligible)
    if rows0.size == 0:
        return rows0, np.array([], dtype=np.int64), 0
    finite = np.isfinite(r[rows0])
    coverage = finite.mean(axis=0)
    cols = np.flatnonzero(coverage >= coverage_min)
    full = finite[:, cols].all(axis=1)
    return rows0[full], cols, int(cols.size)


def analyse_window(r: np.ndarray, *, coverage_min: float, min_cross_section: int) -> dict[str, Any]:
    """Complete IK-05 block of one window: ``r`` is (days x symbols) of that window only."""
    out: dict[str, Any] = {"n_return_days": int(r.shape[0])}
    mm = common.market_model(r, min_cross_section)
    eligible = np.isfinite(mm.rm)
    out["n_eligible_days"] = int(eligible.sum())
    out["n_symbols_in_window"] = int(np.isfinite(r).any(axis=0).sum())
    rows, cols, n_cov = balanced_subpanel(r, eligible, coverage_min)
    out["n_symbols_covered"] = n_cov
    if cols.size < MIN_BALANCED_SYMBOLS or rows.size < MIN_BALANCED_DAYS:
        out.update({"status": "skipped", "reason": "balanced sub-panel too small",
                    "k_symbols": int(cols.size), "t_days": int(rows.size)})
        return out
    raw = r[np.ix_(rows, cols)]
    res = mm.resid[np.ix_(rows, cols)]
    const = (raw.std(axis=0) <= 0.0) | (res.std(axis=0) <= 0.0)
    out["n_zero_variance_dropped"] = int(const.sum())
    raw, res = raw[:, ~const], res[:, ~const]
    k, t = int(raw.shape[1]), int(raw.shape[0])
    if k < MIN_BALANCED_SYMBOLS:
        out.update({"status": "skipped", "reason": "balanced sub-panel too small", "k_symbols": k, "t_days": t})
        return out
    edge = mp_edge(k, t)
    out.update({"status": "ok", "k_symbols": k, "t_days": t, "q_ratio": k / t, "mp_edge": edge})
    out["pearson"] = {
        "residual": spectrum_summary(correlation_eigenvalues(res), edge),
        "raw": spectrum_summary(correlation_eigenvalues(raw), edge),
    }
    out["spearman"] = {
        "residual": spectrum_summary(correlation_eigenvalues(res, rank=True), edge),
        "raw": spectrum_summary(correlation_eigenvalues(raw, rank=True), edge),
    }
    return out


def run_ik05(r: np.ndarray, return_days: np.ndarray, *, coverage_min: float = 0.9,
             min_cross_section: int = common.MIN_CROSS_SECTION,
             subwindows: Sequence[tuple[str, str, str]] = SUBWINDOWS) -> dict[str, Any]:
    """IK-05 on the whole window and on each sub-window.

    ``r`` is (days x symbols) of daily log returns (NaN = missing), ``return_days`` the epoch-day number of each row.
    A sub-window is clipped to the available days; a window without rows is reported as skipped."""
    days = np.asarray(return_days, dtype=np.int64)
    if days.size != r.shape[0]:
        raise ValueError("return_days and r differ in length")
    full = analyse_window(r, coverage_min=coverage_min, min_cross_section=min_cross_section)
    full["start"] = _iso(int(days[0]))
    full["end"] = _iso(int(days[-1]))
    subs: dict[str, Any] = {}
    for name, s_txt, e_txt in subwindows:
        s, e = common.day_number(date.fromisoformat(s_txt)), common.day_number(date.fromisoformat(e_txt))
        sel = (days >= s) & (days <= e)
        if not sel.any():
            subs[name] = {"start": s_txt, "end": e_txt, "status": "skipped", "reason": "no return days in window"}
            continue
        block = analyse_window(r[sel], coverage_min=coverage_min, min_cross_section=min_cross_section)
        block["start"] = _iso(int(days[sel][0]))
        block["end"] = _iso(int(days[sel][-1]))
        subs[name] = block
    return {"method": METHOD_TEXT, "full": full, "sub_windows": subs}


def _iso(day_num: int) -> str:
    return date.fromordinal(common.EPOCH.toordinal() + day_num).isoformat()
