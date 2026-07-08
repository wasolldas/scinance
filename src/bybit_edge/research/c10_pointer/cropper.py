"""Detrending + Cropper score + pointer-day detection for H-10 (KAPITALFREI).

Method (registry H-10, pre-fixed, thresholds NOT negotiable):

  1. trailing 63-day MEDIAN detrending per series (min_periods = 21 finite
     observations in the trailing window INCLUDING day t):
         resid[t] = x[t] - median(x[t-62 .. t])
  2. Cropper score on the residual with a CENTRED 11-day window (t-5 .. t+5,
     clipped at the series bounds; day t included in mean/SD, SD with ddof=1;
     at least 6 finite window values required, else NaN):
         C[t] = (resid[t] - mean_11(resid)) / sd_11(resid)
  3. Pointer day over the (T x N) score matrix:
         n_avail[t] >= 18  AND
         max(#{C[t,j] >= 1.5}, #{C[t,j] <= -1.5}) / n_avail[t] >= 0.60
     Direction = sign of the larger same-direction count.

KAPITALFREI: pure series statistics. numpy only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Trailing median detrend window in days (registry H-10: 63).
DETREND_WINDOW = 63

#: Minimum finite observations in the trailing window (registry H-10: 21).
DETREND_MIN_PERIODS = 21

#: Centred Cropper window half-width in days (11-day window => 5).
CROPPER_HALF_WINDOW = 5

#: Minimum finite values inside the (clipped) centred window for a score.
CROPPER_MIN_FINITE = 6

#: Cropper anomaly threshold (registry H-10: |C| >= 1.5, NOT negotiable).
C_THRESH = 1.5

#: Neuwirth-window crosscheck half-width (13-day centred window, Neuwirth et
#: al. 2007 pointer-year convention). Registered as "wird mitberichtet, ist
#: aber nicht-urteilstragend" (hardened_hypotheses.md H-10 "Methoden-
#: Fixierung") — a NON-judgment-bearing secondary diagnostic ONLY; the
#: 11-day Cropper window above is the sole judgment-bearing standardisation.
NEUWIRTH_HALF_WINDOW = 6

#: Same-direction share floor for a pointer day (registry H-10: >= 0.60).
SHARE_FLOOR = 0.60

#: Availability floor: >= 18 of the 30 series must have a score on day t.
N_AVAIL_FLOOR = 18

#: Float guard for the share comparison (0.60 boundary cases like 18/30).
_SHARE_EPS = 1e-12


def trailing_median_detrend(
    x: np.ndarray,
    *,
    window: int = DETREND_WINDOW,
    min_periods: int = DETREND_MIN_PERIODS,
) -> np.ndarray:
    """Trailing-median residual per day (window includes day t).

    ``resid[t] = x[t] - median`` of the finite values in ``x[t-window+1 .. t]``;
    NaN when ``x[t]`` is NaN or fewer than ``min_periods`` finite values are in
    the trailing window.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    out = np.full(n, np.nan, dtype=np.float64)
    for t in range(n):
        if not np.isfinite(x[t]):
            continue
        lo = max(0, t - window + 1)
        w = x[lo:t + 1]
        w = w[np.isfinite(w)]
        if w.size >= min_periods:
            out[t] = x[t] - float(np.median(w))
    return out


def cropper_score(
    resid: np.ndarray,
    *,
    half_window: int = CROPPER_HALF_WINDOW,
    min_finite: int = CROPPER_MIN_FINITE,
) -> np.ndarray:
    """Cropper score ``C[t] = (resid[t] - mean_11) / sd_11`` (centred window).

    The centred window is ``resid[t-half .. t+half]`` clipped at the bounds and
    INCLUDES day t; mean/SD are over its finite values (SD with ddof=1). NaN
    when ``resid[t]`` is NaN, fewer than ``min_finite`` finite values are in
    the window, or the window SD is zero/non-finite.
    """
    r = np.asarray(resid, dtype=np.float64)
    n = r.size
    out = np.full(n, np.nan, dtype=np.float64)
    for t in range(n):
        if not np.isfinite(r[t]):
            continue
        lo = max(0, t - half_window)
        hi = min(n, t + half_window + 1)
        w = r[lo:hi]
        w = w[np.isfinite(w)]
        if w.size < max(2, min_finite):
            continue
        sd = float(np.std(w, ddof=1))
        if sd <= 0.0 or not np.isfinite(sd):
            continue
        out[t] = (r[t] - float(np.mean(w))) / sd
    return out


@dataclass(slots=True)
class PointerDays:
    """Pointer-day detection outcome over a (T x N) Cropper-score matrix.

    ``n_avail``   : (T,) finite scores per day across series.
    ``n_pos``     : (T,) count of ``C >= +C_THRESH``.
    ``n_neg``     : (T,) count of ``C <= -C_THRESH``.
    ``share``     : (T,) ``max(n_pos, n_neg) / n_avail`` (NaN if n_avail = 0).
    ``is_pointer``: (T,) boolean pointer-day flag.
    ``direction`` : (T,) +1 / -1 direction of the larger count (0 elsewhere).
    """

    n_avail: np.ndarray
    n_pos: np.ndarray
    n_neg: np.ndarray
    share: np.ndarray
    is_pointer: np.ndarray
    direction: np.ndarray

    @property
    def pointer_indices(self) -> np.ndarray:
        return np.flatnonzero(self.is_pointer)


def detect_pointer_days(
    scores: np.ndarray,
    *,
    c_thresh: float = C_THRESH,
    share_floor: float = SHARE_FLOOR,
    n_avail_floor: int = N_AVAIL_FLOOR,
) -> PointerDays:
    """Detect pointer days on a (T x N) Cropper-score matrix.

    Day t is a pointer day iff ``n_avail[t] >= n_avail_floor`` AND
    ``max(n_pos, n_neg) / n_avail >= share_floor`` (registry H-10 wording;
    thresholds 18 / 0.60 / 1.5 are pre-registered and NOT lowered).
    """
    C = np.asarray(scores, dtype=np.float64)
    if C.ndim != 2:
        raise ValueError(f"scores must be 2-D (T x N), got shape {C.shape}")
    finite = np.isfinite(C)
    n_avail = finite.sum(axis=1).astype(np.int64)
    with np.errstate(invalid="ignore"):
        n_pos = ((C >= c_thresh) & finite).sum(axis=1).astype(np.int64)
        n_neg = ((C <= -c_thresh) & finite).sum(axis=1).astype(np.int64)
    n_max = np.maximum(n_pos, n_neg).astype(np.float64)
    share = np.full(C.shape[0], np.nan, dtype=np.float64)
    ok = n_avail > 0
    share[ok] = n_max[ok] / n_avail[ok]
    is_pointer = ok & (n_avail >= n_avail_floor) & (share >= share_floor - _SHARE_EPS)
    direction = np.zeros(C.shape[0], dtype=np.int64)
    direction[is_pointer & (n_pos >= n_neg)] = 1
    direction[is_pointer & (n_neg > n_pos)] = -1
    return PointerDays(
        n_avail=n_avail, n_pos=n_pos, n_neg=n_neg,
        share=share, is_pointer=is_pointer, direction=direction,
    )


def score_matrix(panel: np.ndarray, *,
                 half_window: int = CROPPER_HALF_WINDOW) -> np.ndarray:
    """Detrend + Cropper-score every column of a (T x N) daily panel.

    ``half_window`` defaults to the judgment-bearing 11-day Cropper window;
    pass ``NEUWIRTH_HALF_WINDOW`` (13-day window) ONLY for the registered
    non-judgment-bearing Neuwirth crosscheck.
    """
    X = np.asarray(panel, dtype=np.float64)
    if X.ndim != 2:
        raise ValueError(f"panel must be 2-D (T x N), got shape {X.shape}")
    out = np.full_like(X, np.nan)
    for j in range(X.shape[1]):
        out[:, j] = cropper_score(trailing_median_detrend(X[:, j]),
                                  half_window=half_window)
    return out


__all__ = [
    "C_THRESH",
    "CROPPER_HALF_WINDOW",
    "CROPPER_MIN_FINITE",
    "DETREND_MIN_PERIODS",
    "DETREND_WINDOW",
    "N_AVAIL_FLOOR",
    "NEUWIRTH_HALF_WINDOW",
    "SHARE_FLOOR",
    "PointerDays",
    "cropper_score",
    "detect_pointer_days",
    "score_matrix",
    "trailing_median_detrend",
]
