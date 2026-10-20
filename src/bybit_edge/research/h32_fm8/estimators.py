"""Pure estimators of H-32 (DEC-99, DEC-94): SE by rule P-1 (4), the pilot statistics, the signed selection ceiling,
``mu_sel`` and the end power after F-WEEK.  No I/O, no panel access.

All statistics are in the REGISTERED direction ``y = s * IC`` (s = +1 for mom1/mom2/mom4, -1 for rev_gap); the frozen
constants of the registration (``null_mean``, ``q95``, ``ceiling_k4``) are in the same unit.
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Any, Sequence

import numpy as np

from .. import power_p1
from . import constants as C

__all__ = ["se_rule", "pilot_statistics", "signed_selection_ceiling", "mu_sel", "end_power", "by_threshold",
           "harmonic_number", "bootstrap_means_sha256", "series_sha256"]

_N = NormalDist()


def _fin(a: Sequence[float] | np.ndarray) -> np.ndarray:
    x = np.asarray(a, dtype=np.float64)
    return x[np.isfinite(x)]


def series_sha256(series: Sequence[float] | np.ndarray) -> str:
    import hashlib
    return hashlib.sha256(np.ascontiguousarray(np.asarray(series, dtype="<f8")).tobytes()).hexdigest()


def bootstrap_means_sha256(means: np.ndarray) -> str:
    return series_sha256(means)


def se_rule(ic_weekly: Sequence[float] | np.ndarray, floor: float, w_judged: int, *,
            mean_block: float = C.MEAN_BLOCK, n_boot: int = C.N_BOOT_MIN, seed: int = C.SEED,
            with_sha: bool = False) -> dict[str, Any]:
    """SE of a window mean by rule P-1 (4) (ERSTFASSUNG 1.9, Test mode and v6):

        ``SE = max(floor / sqrt(W), SD(IC_t) / sqrt(W), SE_stat)``

    with ``floor`` the frozen ``floor_fm8``, ``W`` the registered ``w_judged`` and ``SE_stat`` the SD (ddof 1) of the means of
    the stationary bootstrap (``power_p1.stationary_bootstrap_means``, mean block 4, ``n_boot`` replicates, registered seed;
    identical to ``power_p1.stationary_bootstrap_se``) of the finite weekly series.  A series with fewer than two finite weeks
    gives NaN (fails closed in the gate).  ``with_sha`` adds the fingerprint of the bootstrap means (DEC-53)."""
    fin = _fin(ic_weekly)
    if fin.size < 2 or not (w_judged > 0):
        return {"se": float("nan"), "floor_term": float("nan"), "sd_term": float("nan"), "stat_term": float("nan"),
                "sd_ic": float("nan"), "w_judged": int(w_judged), "n_finite": int(fin.size), "bootstrap_means_sha256": None}
    sd = float(fin.std(ddof=1))
    means = power_p1.stationary_bootstrap_means(fin, mean_block, n_boot, seed=seed)
    stat = float(np.std(means, ddof=1))
    floor_term = float(floor) / math.sqrt(w_judged)
    sd_term = sd / math.sqrt(w_judged)
    return {"se": max(floor_term, sd_term, stat), "floor_term": floor_term, "sd_term": sd_term, "stat_term": stat,
            "sd_ic": sd, "w_judged": int(w_judged), "n_finite": int(fin.size),
            "bootstrap_means_sha256": bootstrap_means_sha256(means) if with_sha else None}


def pilot_statistics(ic_weekly: Sequence[float] | np.ndarray, k_weekly: Sequence[float] | np.ndarray, sign: int, *,
                     mean_block: float = C.MEAN_BLOCK, n_boot: int = C.N_BOOT_MIN, seed: int = C.SEED) -> dict[str, Any]:
    """ERSTFASSUNG 1.7: the pilot statistics of one variant from its weekly fm8 IC series (raw IC) and the K of the weeks.

    * ``x_P`` = mean of ``y = s * IC``, ``SD_P`` = sample SD (ddof 1), ``W_P`` = number of finite weeks;
    * ``SE_P = max(B_P / sqrt(W_P), SD_P / sqrt(W_P), SE_stat)``, ``B_P = mean_t 1/sqrt(k_t - 1)``;
    * ``t_P = x_P / SE_P``; 80 % band ``x_P +- 1.2816 SE_P`` (normal) and the percentile band of the bootstrap means;
    * ``v_P = mean_t 1/(k_t - 1)``, ``F2_real = max(0, SD_P^2 - v_P)``, ``c_real = max(1, W_P SE_stat^2 / SD_P^2)``.
    """
    ic = np.asarray(ic_weekly, dtype=np.float64)
    k = np.asarray(k_weekly, dtype=np.float64)
    if ic.shape != k.shape:
        raise ValueError("ic_weekly and k_weekly differ in length")
    fin = np.isfinite(ic)
    y = float(sign) * ic[fin]
    kf = k[fin]
    w_p = int(y.size)
    if w_p < 3 or np.any(kf < 2.0):
        raise ValueError("pilot series too short or K < 2")
    x_p = float(y.mean())
    sd_p = float(y.std(ddof=1))
    b_p = float(np.mean(1.0 / np.sqrt(kf - 1.0)))
    v_p = float(np.mean(1.0 / (kf - 1.0)))
    means = power_p1.stationary_bootstrap_means(y, mean_block, n_boot, seed=seed)
    se_stat = float(np.std(means, ddof=1))
    se_p = max(b_p / math.sqrt(w_p), sd_p / math.sqrt(w_p), se_stat)
    c_real = max(1.0, w_p * se_stat ** 2 / sd_p ** 2) if sd_p > 0.0 else 1.0
    f2_real = max(0.0, sd_p ** 2 - v_p)
    q_lo, q_hi = (float(v) for v in np.quantile(means, [(1.0 - C.BAND_LEVEL) / 2.0, 1.0 - (1.0 - C.BAND_LEVEL) / 2.0]))
    return {
        "x_p": x_p, "sd_p": sd_p, "w_p": w_p, "b_p": b_p, "v_p": v_p, "se_stat": se_stat, "se_p": se_p,
        "t_p": x_p / se_p, "band80_normal": [x_p - C.BAND_Z * se_p, x_p + C.BAND_Z * se_p],
        "band80_bootstrap_percentile": [q_lo, q_hi], "f2_real": f2_real, "c_real": c_real,
        "bootstrap_means_sha256": bootstrap_means_sha256(means),
        "se_terms": {"floor": b_p / math.sqrt(w_p), "sd": sd_p / math.sqrt(w_p), "stat": se_stat},
    }


def signed_selection_ceiling(draws: dict[str, Sequence[float] | np.ndarray], signs: dict[str, int]) -> float:
    """B-5 / Review B-15: sign-adjusted selection ceiling -- the mean over replicates of the maximum over the variants of
    ``s_v * mean_v`` (the window means of the replicate, raw IC units times the registered sign).  A new function: the
    ``nulls._mean_of_max`` of the third version takes the raw signs.  Replicates in which a variant is NaN use the
    finite variants; a replicate with no finite variant is skipped."""
    names = list(draws)
    if not names:
        return float("nan")
    arr = np.vstack([float(signs[v]) * np.asarray(draws[v], dtype=np.float64) for v in names])     # [K, n_reps]
    with np.errstate(invalid="ignore"):
        finite_any = np.isfinite(arr).any(axis=0)
        mx = np.where(np.isfinite(arr), arr, -np.inf).max(axis=0)
    mx = mx[finite_any]
    return float(mx.mean()) if mx.size else float("nan")


def _log_sf(z: float) -> float:
    """log of the standard-normal upper tail; asymptotic series for large z (no underflow)."""
    if z < 30.0:
        v = 0.5 * math.erfc(z / math.sqrt(2.0))
        if v > 0.0:
            return math.log(v)
    z2 = z * z
    return (-0.5 * z2 - math.log(z) - 0.5 * math.log(2.0 * math.pi)
            + math.log(1.0 - 1.0 / z2 + 3.0 / (z2 * z2) - 15.0 / (z2 * z2 * z2)))


def mu_sel(x_p: float, se_p: float, c: float) -> float | None:
    """DEC-99 (3) / Review B-5: the selection-adjusted pilot estimator -- the solution ``mu`` of

        ``P_mu(X >= x_P | X >= c) = 0.5``,  ``X ~ N(mu, SE_P^2)``,

    i.e. the ``mu`` for which ``x_P`` is the median of ``X`` given the hand-over threshold ``c`` (conditionally
    median-unbiased).  Defined for ``x_P > c``; for ``x_P <= c`` (not handed over) returns ``None``.  Bisection on the
    monotone map ``mu -> P`` over ``[x_P - 40 SE_P, x_P + 40 SE_P]`` with log tails (no underflow)."""
    x_p, s, c = float(x_p), float(se_p), float(c)
    if not (s > 0.0) or not (x_p > c):
        return None

    def f(mu: float) -> float:
        return math.exp(_log_sf((x_p - mu) / s) - _log_sf((c - mu) / s)) - 0.5

    lo, hi = x_p - 40.0 * s, x_p + 40.0 * s
    if f(lo) > 0.0:                 # the root lies below the bracket (x_P barely above c): report the bracket edge
        return lo
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0.0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-15 * max(1.0, abs(mid)):
            break
    return 0.5 * (lo + hi)


def harmonic_number(m: int) -> float:
    return float(sum(1.0 / i for i in range(1, int(m) + 1)))


def by_threshold(m: int, alpha: float = C.BY_ALPHA) -> float:
    """BY single-rejection bound ``alpha / (m H_m)`` (DEC-99 (7))."""
    if int(m) < 1:
        raise ValueError("m must be >= 1")
    return float(alpha) / (int(m) * harmonic_number(m))


def end_power(prior: float, m: int, windows: dict[str, dict[str, float]], *, alpha: float = C.BY_ALPHA) -> dict[str, Any]:
    """ERSTFASSUNG 1.9: end power after F-WEEK at the prior ``prior`` (y units).  ``windows[W]`` = ``{"se_t", "sd_t",
    "null_mean"}``.  The BY bound for one rejection is ``alpha / (m H_m)``; ``z_eff = max(z_krit, Phi^-1(1 - bound))``;
    window power ``Phi((prior - max(0, null_mean_W) - z_eff SE_T,W) / SD_T,W)``; end power = product over the windows.
    Display only -- never an assignment basis."""
    thr = by_threshold(m, alpha)
    z_eff = max(C.Z_KRIT, _N.inv_cdf(1.0 - thr))
    wp: dict[str, float] = {}
    for wn, w in windows.items():
        wp[wn] = power_p1.condition_power(float(prior) - max(0.0, float(w["null_mean"])), z_eff * float(w["se_t"]),
                                          float(w["sd_t"]))
    return {"m": int(m), "by_threshold_p": thr, "z_eff": z_eff, "window_power": wp, "joint": math.prod(wp.values())}
