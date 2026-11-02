"""A1 derivation -- formation-side building blocks shared by the window census and the
nuisance measurement. NOTHING in this module reads a return or a funding value of a week
AFTER the formation week t: market factor series are per-week cross-sectional means of the
week's OWN return, the trailing regressions use weeks t-TRAIL+1..t only.
"""
from __future__ import annotations

from typing import Any

import numpy as np

import a1_common as C

TRAIL_WEEKS = 26          # = nulls.CALIBRATION_BETA_TRAIL_WEEKS (registered A3 calibration window)
MIN_VALID_WEEKS = 8       # = pit_universe.MIN_WEEKS_HISTORY


def returns_est(d: dict[str, Any]) -> np.ndarray:
    """DEC-85 (iii): NaN where no return was computed (never an observed zero)."""
    return np.where(d["returns_valid"], d["returns"], np.nan)


def market_factors(d: dict[str, Any]) -> dict[str, np.ndarray]:
    """Weekly market factor series (log returns), one value per grid week:
    ``ew``  = equal-weighted mean of week t's own return over the PIT-alive symbols with a valid
              return (the hedge's market); ``btc`` = BTCUSDT's week-t return."""
    r = returns_est(d)
    alive = d["alive"]
    n_w = r.shape[0]
    ew = np.full(n_w, np.nan)
    for t in range(n_w):
        m = alive[t] & ~np.isnan(r[t])
        if m.sum() >= 5:
            ew[t] = float(np.mean(r[t, m]))
    j = d["symbols"].index("BTCUSDT")
    return {"ew": ew, "btc": r[:, j].copy()}


def trailing_beta_idio(d: dict[str, Any], f: np.ndarray, t: int) -> tuple[np.ndarray, np.ndarray]:
    """OLS beta and residual variance of every symbol's weekly log return on factor ``f`` over
    the TRAILING weeks t-TRAIL_WEEKS+1..t (formation-side, PIT). NaN where fewer than
    MIN_VALID_WEEKS weeks have both a valid return and a finite factor value."""
    r = returns_est(d)
    lo = max(0, t - TRAIL_WEEKS + 1)
    R = r[lo:t + 1]                         # [n, S]
    F = f[lo:t + 1][:, None]                # [n, 1]
    v = ~np.isnan(R) & ~np.isnan(F)
    Rv = np.where(v, R, 0.0)
    Fv = np.where(v, F, 0.0)
    n = v.sum(axis=0).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        mf = Fv.sum(axis=0) / n
        mr = Rv.sum(axis=0) / n
        var_f = (Fv * Fv).sum(axis=0) / n - mf * mf
        cov = (Fv * Rv).sum(axis=0) / n - mf * mr
        var_r = (Rv * Rv).sum(axis=0) / n - mr * mr
        beta = cov / var_f
        resid = (var_r - beta * beta * var_f) * n / (n - 2.0)
    bad = (n < MIN_VALID_WEEKS) | ~(var_f > 0)
    beta = np.where(bad, np.nan, beta)
    resid = np.where(bad, np.nan, np.maximum(resid, 0.0))
    return beta, resid


def predicted_ls_price_variance(beta: np.ndarray, idio: np.ndarray, d1: np.ndarray, umask: np.ndarray,
                                var_f: float) -> dict[str, float]:
    """Formation-side prediction of Var(price leg of D1 minus EW universe) for one formation week:
    delta^2 * Var(f) + idiosyncratic part, delta = mean_D1(beta) - mean_U(beta), idiosyncratic
    part of mean_D1(e) - mean_U(e) with D1 inside U and independent residuals:
    (1/n1 - 1/nU)^2 * sum_D1 s_i^2 + (1/nU)^2 * sum_{U minus D1} s_i^2. Missing betas / residual
    variances are replaced by the universe median of the week (reported as coverage)."""
    u_idx = np.flatnonzero(umask)
    in_d1 = np.zeros(umask.shape, dtype=bool)
    in_d1[d1] = True
    b_u = beta[u_idx]
    s_u = idio[u_idx]
    cov_b = float(np.mean(~np.isnan(b_u)))
    med_b = float(np.nanmedian(b_u)) if np.any(~np.isnan(b_u)) else np.nan
    med_s = float(np.nanmedian(s_u)) if np.any(~np.isnan(s_u)) else np.nan
    b_fill = np.where(np.isnan(beta), med_b, beta)
    s_fill = np.where(np.isnan(idio), med_s, idio)
    n1, nu = int(d1.size), int(u_idx.size)
    beta_d1 = float(np.mean(b_fill[d1]))
    beta_u = float(np.mean(b_fill[u_idx]))
    delta = beta_d1 - beta_u
    rest = u_idx[~in_d1[u_idx]]
    idio_var = (1.0 / n1 - 1.0 / nu) ** 2 * float(np.sum(s_fill[d1])) + (1.0 / nu) ** 2 * float(np.sum(s_fill[rest]))
    return {"beta_d1": beta_d1, "beta_u": beta_u, "delta": delta, "factor_var": delta * delta * var_f,
            "idio_var": idio_var, "pred_var": delta * delta * var_f + idio_var, "beta_coverage_u": cov_b,
            "beta_coverage_d1": float(np.mean(~np.isnan(beta[d1]))), "n_d1": n1, "n_u": nu,
            "mean_idio_sd_d1": float(np.mean(np.sqrt(s_fill[d1]))),
            "mean_idio_sd_u": float(np.mean(np.sqrt(s_fill[u_idx])))}


def interval_class_of_week(d: dict[str, Any], t: int, j: np.ndarray) -> np.ndarray:
    """Modal interval class (by day count) of each symbol-week (formation-side). Ties resolve to the
    longer interval (8h > 4h > 2h > 1h), 'none' if no funding day."""
    names = ["8h", "4h", "2h", "1h", "other"]
    counts = np.stack([d["cls_days"][c][t, j] for c in names], axis=1)
    out = np.array([names[int(np.argmax(row))] if row.sum() > 0 else "none" for row in counts])
    return out


def fmt_bp(x: float) -> float:
    return float(x * 1e4)
