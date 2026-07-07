"""HAR-RV baseline (Corsi 2009) for the H-11 AnEn mess-gate (KAPITALFREI).

OWN copy per registry §8.2 convention (no cross-import between research
packages) — modelled on the technically reusable ``c42_rv/models.py::
HARRVBaseline`` numpy-OLS pattern from wave 1 (H-02/C-42 itself is DROP; the
HAR implementation pattern is not).

Pre-registered baseline (registry H-11): OLS of the 3-day-ahead log annualised
RV target on the three log-RV HAR regressors (RV_1d, RV_5d, RV_22d), expanding
fit on samples <= t - 30 (same causal embargo as the AnEn candidate library),
refit MONTHLY (calendar month of the forecast day changes -> refit), point
forecast scored by CRPS = |forecast - observation|.

KAPITALFREI: pure point-forecast baseline. numpy only.
"""
from __future__ import annotations

import numpy as np

#: Same causal fit embargo as the AnEn library (registry H-11: fit <= t-30).
FIT_EMBARGO_DAYS = 30

#: Minimum samples for a stable 4-parameter OLS fit.
MIN_FIT_SAMPLES = 30


def har_fit(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """OLS fit of ``y`` on ``[1, x]`` via numpy lstsq. Returns beta (4,)."""
    design = np.column_stack([np.ones(len(y), dtype=np.float64), x])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    return beta


def har_predict(beta: np.ndarray, x_row: np.ndarray) -> float:
    """Point prediction for one regressor row."""
    return float(beta[0] + np.dot(beta[1:], x_row))


def har_forecast_series(
    log_rv1: np.ndarray,
    log_rv5: np.ndarray,
    log_rv22: np.ndarray,
    targets: np.ndarray,
    dates: list[str],
    forecast_idx: np.ndarray,
    *,
    embargo: int = FIT_EMBARGO_DAYS,
    min_fit_samples: int = MIN_FIT_SAMPLES,
) -> tuple[np.ndarray, int]:
    """HAR-RV forecasts for the requested days with monthly expanding refit.

    For each forecast day t (ascending), the model is fit on all samples s
    with s <= t - embargo and finite regressors/target — strictly causal (the
    sample target at s uses days s+1..s+3 <= t - 27 < t). The fit is refreshed
    only when the calendar month (``dates[t][:7]``) changes relative to the
    previous refit (pre-registered monthly refit); between refits the frozen
    coefficients are reused. NaN forecast when fewer than ``min_fit_samples``
    training samples exist.

    Returns ``(forecasts aligned to forecast_idx, n_refits)``.
    """
    x_all = np.column_stack([
        np.asarray(log_rv1, dtype=np.float64),
        np.asarray(log_rv5, dtype=np.float64),
        np.asarray(log_rv22, dtype=np.float64),
    ])
    y_all = np.asarray(targets, dtype=np.float64)
    row_ok = np.all(np.isfinite(x_all), axis=1)
    sample_ok = row_ok & np.isfinite(y_all)

    forecast_idx = np.asarray(forecast_idx, dtype=np.int64)
    if np.any(np.diff(forecast_idx) < 0):
        raise ValueError("forecast_idx must be ascending")

    out = np.full(forecast_idx.size, np.nan, dtype=np.float64)
    beta: np.ndarray | None = None
    fit_month: str | None = None
    n_refits = 0

    for i, t in enumerate(forecast_idx):
        t = int(t)
        month = dates[t][:7]
        if beta is None or month != fit_month:
            hi = t - embargo
            if hi >= 0:
                mask = sample_ok.copy()
                mask[hi + 1 :] = False
                n_train = int(mask.sum())
                if n_train >= min_fit_samples:
                    beta = har_fit(x_all[mask], y_all[mask])
                    n_refits += 1
            fit_month = month
        if beta is None or not row_ok[t]:
            continue
        out[i] = har_predict(beta, x_all[t])
    return out, n_refits


__all__ = [
    "FIT_EMBARGO_DAYS",
    "MIN_FIT_SAMPLES",
    "har_fit",
    "har_forecast_series",
    "har_predict",
]
