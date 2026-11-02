"""IK-04: moments for the minimal null world on the daily panel (Zone X).

What is measured (all second or higher moments, shapes and dependence; never a mean or a sign of a return)
  * excess kurtosis and skewness of the daily returns r and of the market residuals e of every symbol; output
    only the quantiles q10 / q25 / q50 / q75 / q90 over symbols, for all symbols and for the three terciles of the
    median daily turnover (a disjoint partition: t1_low, t2_mid, t3_high);
  * the cross-sectional SD of the returns of each day (sigma_xs,t): quantiles over days, the average level over days
    (a dispersion, hence allowed), and its autocorrelation at lags 1..5;
  * volatility clustering: the autocorrelation of |r_M,t| (absolute market return; the sign is dropped) at lags 1..5
    and, for each symbol, of |r_i,t| (quantiles over symbols);
  * the effective number of clusters of a 365-day window, n_eff = 365 / max(1, 1 + 2 sum_{k=1..L} rho_k), from the
    autocorrelation of |r_M,t| (L = 5 is the specification; L = 10 / 20 / 40 are sensitivities).  c_hat is the
    unfloored variance factor; ``c_overlap`` = 1 because daily returns do not overlap;
  * the share of missing candle days of each symbol between its first and last observed day (quantiles and max).

Estimators: moment estimators m3 / m2^1.5 and m4 / m2^2 - 3 on the observed days of a symbol (no small-sample
correction, no interpolation), at least ``MIN_OBS_MOMENTS`` observations.  The autocorrelation uses the usual
estimator sum (x_t - m)(x_{t+k} - m) / sum (x_t - m)^2 with the pairs that contain a gap dropped from the numerator.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from . import common

__all__ = [
    "ACF_LAGS", "N_EFF_WINDOW", "QUANTILE_LABELS", "QUANTILE_LEVELS", "autocorrelation", "column_moments",
    "effective_clusters", "median_turnover", "missing_day_share", "quantile_block", "run_ik04",
    "turnover_terciles",
]

QUANTILE_LEVELS: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90)
QUANTILE_LABELS: tuple[str, ...] = ("q10", "q25", "q50", "q75", "q90")
ACF_LAGS = 5
#: Lags for the n_eff sensitivity (the specification is the first one).
N_EFF_LAGS: tuple[int, ...] = (5, 10, 20, 40)
N_EFF_WINDOW = 365
MIN_OBS_MOMENTS = 30
TERCILE_LABELS: tuple[str, ...] = ("t1_low", "t2_mid", "t3_high")


# ----------------------------------------------------------------------------
# moments
# ----------------------------------------------------------------------------

def column_moments(x: np.ndarray, min_obs: int = MIN_OBS_MOMENTS) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per column of ``x`` (days x symbols, NaN = missing): ``(n_obs, skewness, excess_kurtosis)``.

    Moment estimators on the observed entries; NaN where fewer than ``min_obs`` observations or zero variance."""
    a = np.asarray(x, dtype=np.float64)
    if a.ndim != 2:
        raise ValueError("x must be 2-D")
    valid = np.isfinite(a)
    n = valid.sum(axis=0)
    safe = np.maximum(n, 1)
    mean = np.where(valid, a, 0.0).sum(axis=0) / safe
    d = np.where(valid, a - mean, 0.0)
    d2 = d * d
    m2 = d2.sum(axis=0) / safe
    m3 = (d2 * d).sum(axis=0) / safe
    m4 = (d2 * d2).sum(axis=0) / safe
    ok = (n >= min_obs) & (m2 > 0.0)
    m2s = np.where(ok, m2, 1.0)
    skew = np.where(ok, m3 / m2s ** 1.5, np.nan)
    kurt = np.where(ok, m4 / m2s ** 2 - 3.0, np.nan)
    return n, skew, kurt


def quantile_block(values: np.ndarray) -> dict[str, Any]:
    """``{"n": count, "q10": ..., ..., "q90": ...}`` over the finite entries (None when there are none)."""
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    out: dict[str, Any] = {"n": int(v.size)}
    if v.size == 0:
        out.update({lab: None for lab in QUANTILE_LABELS})
        return out
    q = np.quantile(v, QUANTILE_LEVELS)
    out.update({lab: float(val) for lab, val in zip(QUANTILE_LABELS, q, strict=True)})
    return out


def median_turnover(turnover: np.ndarray) -> np.ndarray:
    """Median daily turnover of each symbol over its observed days (NaN if it has none)."""
    out = np.full(turnover.shape[1], np.nan)
    for j in range(turnover.shape[1]):
        col = turnover[:, j]
        col = col[np.isfinite(col)]
        if col.size:
            out[j] = float(np.median(col))
    return out


def turnover_terciles(median_turn: np.ndarray, symbols: Sequence[str]) -> np.ndarray:
    """Class index 0 / 1 / 2 (low / mid / high turnover) per symbol: rank by median turnover, ties by symbol name,
    split into three groups of nearly equal size.  Symbols without turnover rank lowest."""
    m = np.asarray(median_turn, dtype=np.float64)
    key = np.where(np.isfinite(m), m, -np.inf)
    order = np.lexsort((np.asarray(list(symbols), dtype=str), key))
    cls = np.empty(m.size, dtype=np.int64)
    for g, idx in enumerate(np.array_split(order, 3)):
        cls[idx] = g
    return cls


def missing_day_share(close: np.ndarray) -> np.ndarray:
    """Share of missing candle days of each symbol between its first and its last observed day (0 = no gap)."""
    obs = np.isfinite(close)
    n = obs.sum(axis=0)
    first = np.where(n > 0, obs.argmax(axis=0), 0)
    last = np.where(n > 0, close.shape[0] - 1 - obs[::-1].argmax(axis=0), 0)
    span = np.maximum(last - first + 1, 1)
    return np.where(n > 0, 1.0 - n / span, np.nan)


# ----------------------------------------------------------------------------
# autocorrelation and effective cluster number
# ----------------------------------------------------------------------------

def autocorrelation(x: np.ndarray, max_lag: int) -> np.ndarray:
    """Autocorrelation at lags 1..max_lag of a series with gaps (NaN).

    rho_k = sum_t (x_t - m)(x_{t+k} - m) / sum_t (x_t - m)^2, m = mean of the observed entries; pairs with a missing
    member contribute nothing to the numerator.  NaN for all lags if too few observations."""
    a = np.asarray(x, dtype=np.float64)
    ok = np.isfinite(a)
    if int(ok.sum()) < max_lag + 2:
        return np.full(max_lag, np.nan)
    d = np.where(ok, a - a[ok].mean(), 0.0)
    c0 = float((d * d).sum())
    if c0 <= 0.0:
        return np.full(max_lag, np.nan)
    return np.array([float((d[:-k] * d[k:]).sum()) / c0 for k in range(1, max_lag + 1)])


def effective_clusters(rho: Sequence[float], n: int = N_EFF_WINDOW, max_lag: int = ACF_LAGS
                       ) -> tuple[float | None, float | None]:
    """``(c_hat, n_eff)`` with c_hat = 1 + 2 sum_{k<=max_lag} rho_k and n_eff = n / max(1, c_hat) (never above n)."""
    r = np.asarray(list(rho)[:max_lag], dtype=np.float64)
    if r.size < max_lag or not np.isfinite(r).all():
        return None, None
    c_hat = float(1.0 + 2.0 * r.sum())
    return c_hat, float(n / max(1.0, c_hat))


# ----------------------------------------------------------------------------
# driver
# ----------------------------------------------------------------------------

def run_ik04(r: np.ndarray, close: np.ndarray, turnover: np.ndarray, symbols: Sequence[str], *,
             min_cross_section: int = common.MIN_CROSS_SECTION) -> dict[str, Any]:
    """IK-04 on the analysed symbols.

    ``r`` (days x symbols) log returns, ``close`` / ``turnover`` (calendar days x symbols) of the same symbols."""
    if r.shape[1] != close.shape[1] or r.shape[1] != turnover.shape[1] or r.shape[1] != len(symbols):
        raise ValueError("r, close, turnover and symbols disagree on the number of symbols")
    mm = common.market_model(r, min_cross_section)
    cls = turnover_terciles(median_turnover(turnover), symbols)
    n_no_turn = int((~np.isfinite(median_turnover(turnover))).sum())

    groups: list[tuple[str, np.ndarray]] = [("all", np.ones(cls.size, dtype=bool))]
    groups += [(lab, cls == g) for g, lab in enumerate(TERCILE_LABELS)]
    moments: dict[str, Any] = {}
    for name, mat in (("r_daily", r), ("e_market_resid", mm.resid)):
        _, skew, kurt = column_moments(mat)
        block: dict[str, Any] = {}
        for lab, mask in groups:
            block[lab] = {
                "n_symbols": int(mask.sum()),
                "excess_kurtosis": quantile_block(kurt[mask]),
                "skewness": quantile_block(skew[mask]),
            }
        moments[name] = block

    sd_xs = common.cross_section_sd(r, min_cross_section)
    fin = sd_xs[np.isfinite(sd_xs)]
    acf_sd = autocorrelation(sd_xs, ACF_LAGS)
    xs = {
        "n_days": int(fin.size),
        "level_over_days": float(fin.mean()) if fin.size else None,
        "quantiles": quantile_block(sd_xs),
        "acf": {str(k): float(v) for k, v in enumerate(acf_sd, start=1)},
    }

    abs_rm = np.abs(mm.rm)
    acf_long = autocorrelation(abs_rm, max(N_EFF_LAGS))
    c_hat, n_eff = effective_clusters(acf_long, N_EFF_WINDOW, ACF_LAGS)
    by_lag = {str(L): effective_clusters(acf_long, N_EFF_WINDOW, L)[1] for L in N_EFF_LAGS}
    market = {
        "n_days": int(np.isfinite(abs_rm).sum()),
        "acf": {str(k): float(acf_long[k - 1]) for k in range(1, ACF_LAGS + 1)},
        "c_hat": c_hat,
        "n_eff_365": n_eff,
        "n_eff_by_max_lag": by_lag,
        "c_overlap": 1.0,
    }

    abs_r = np.abs(r)
    sym_acf = np.array([autocorrelation(abs_r[:, j], ACF_LAGS) for j in range(r.shape[1])]).reshape(-1, ACF_LAGS)
    sym_block = {str(k): quantile_block(sym_acf[:, k - 1]) for k in range(1, ACF_LAGS + 1)}

    miss = missing_day_share(close)
    share = quantile_block(miss)
    share["max"] = float(np.nanmax(miss)) if np.isfinite(miss).any() else None
    missing = {"n_symbols": int(np.isfinite(miss).sum()), "n_symbols_with_gaps": int((miss > 0.0).sum()),
               "share": share}

    return {
        "moment_min_obs": MIN_OBS_MOMENTS,
        "n_symbols_without_turnover": n_no_turn,
        "moments": moments,
        "xs_dispersion": xs,
        "abs_r_market": market,
        "abs_r_symbol_acf": sym_block,
        "missing_days": missing,
        "n_days_below_min_cross_section": int((mm.n_xs < min_cross_section).sum()),
    }
