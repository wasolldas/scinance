"""Two-stage null models for the H-12 mess-gate (KAPITALFREI).

(a) BASE REFERENCE (NOT verdict-bearing): Marchenko-Pastur bulk (Q = T/N =
    240) with a Monte-Carlo Gaussian-Wishart null (1000 draws). Registered
    rationale: the Tracy-Widom asymptotics are unreliable at N = 6, hence MC
    instead of the closed-form tail — the MC quantiles of lambda1/lambda2
    under the iid null are reported as orientation only.

(b) VERDICT-BEARING, STRICTER NULL: per-day one-factor Gaussian null
    calibrated from the observed (lambda1, v1):
        beta_i    = v1_i * sqrt(max(lambda1 - 1, 0))
        r~_it     = beta_i * f_t + eps_it,  f_t ~ N(0,1) iid,
        Var(eps_i)= 1 - beta_i^2
    1000 replications -> null distribution of lambda2 AND IPR(v2). The
    simulated panels run through the SAME pipeline as the observation
    (z-standardise per column, correlation matrix, eigen-decomposition).
    Day p-value: p = P(lambda2_sim >= lambda2_obs), add-one convention
    (n_ge + 1) / (n_reps + 1) as everywhere in this repo.

KAPITALFREI: pure simulation statistics. numpy only.
"""
from __future__ import annotations

from typing import Any

import numpy as np

#: Registered MC draw count for both nulls (registry H-12: 1000).
DEFAULT_N_MC = 1000

#: |beta_i| clip so Var(eps_i) = 1 - beta_i^2 stays positive (technical guard).
_BETA_ABS_MAX = 0.999


def mp_bulk(q: float) -> tuple[float, float]:
    """Marchenko-Pastur bulk support [lambda-, lambda+] for aspect Q = T/N.

    lambda+- = (1 +- sqrt(1/Q))^2. For the registered Q = 240:
    lambda+ ~= 1.133.
    """
    if q <= 0:
        raise ValueError(f"Q must be > 0, got {q}")
    s = np.sqrt(1.0 / q)
    return float((1.0 - s) ** 2), float((1.0 + s) ** 2)


def _standardize_columns(x: np.ndarray) -> np.ndarray:
    """Z-standardise per column of a stacked (..., T, N) array (population std)."""
    mu = x.mean(axis=-2, keepdims=True)
    sd = x.std(axis=-2, keepdims=True)
    sd = np.where(sd <= 0.0, 1.0, sd)
    return (x - mu) / sd


def _stacked_corr_eigs(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Correlation eigen-decomposition per stacked draw.

    ``x`` is (R, T, N). Returns ``(lams, vecs)`` with lams (R, N) DESCENDING
    and vecs (R, N, N), ``vecs[r, :, k]`` the eigenvector of ``lams[r, k]``.
    """
    z = _standardize_columns(np.asarray(x, dtype=np.float64))
    t = z.shape[-2]
    c = np.einsum("rti,rtj->rij", z, z) / float(t)
    c = 0.5 * (c + np.swapaxes(c, -1, -2))
    lams, vecs = np.linalg.eigh(c)          # ascending
    return lams[:, ::-1], vecs[:, :, ::-1]  # descending


def wishart_null_mc(
    n_series: int,
    t_obs: int,
    *,
    n_draws: int = DEFAULT_N_MC,
    seed: int = 42,
) -> dict[str, Any]:
    """MC Gaussian-Wishart null reference (stage a — NOT verdict-bearing).

    Draws ``n_draws`` iid N(0,1) panels (t_obs x n_series), runs the
    observation pipeline, and returns quantiles of lambda1 and lambda2 under
    the iid null next to the theoretical MP bulk of Q = t_obs / n_series.
    """
    rng = np.random.default_rng(seed)
    x = rng.standard_normal((int(n_draws), int(t_obs), int(n_series)))
    lams, _ = _stacked_corr_eigs(x)
    l1 = lams[:, 0]
    l2 = lams[:, 1]
    q = float(t_obs) / float(n_series)
    lo, hi = mp_bulk(q)
    qs = (0.50, 0.95, 0.99)
    return {
        "verdict_bearing": False,
        "n_draws": int(n_draws),
        "t_obs": int(t_obs),
        "n_series": int(n_series),
        "q_aspect": q,
        "mp_lambda_minus": lo,
        "mp_lambda_plus": hi,
        "lambda1_null_quantiles": {f"q{int(p * 100)}": float(np.quantile(l1, p)) for p in qs},
        "lambda2_null_quantiles": {f"q{int(p * 100)}": float(np.quantile(l2, p)) for p in qs},
    }


def one_factor_betas(lambda1: float, v1: np.ndarray) -> np.ndarray:
    """Calibrated one-factor loadings beta_i = v1_i * sqrt(max(lambda1 - 1, 0)).

    v1 is normalised first; |beta_i| is clipped just below 1 so the residual
    variance 1 - beta_i^2 stays positive (technical guard, not a threshold).
    """
    v = np.asarray(v1, dtype=np.float64)
    nrm = float(np.linalg.norm(v))
    if nrm > 0:
        v = v / nrm
    beta = v * np.sqrt(max(float(lambda1) - 1.0, 0.0))
    return np.clip(beta, -_BETA_ABS_MAX, _BETA_ABS_MAX)


def one_factor_null_day(
    lambda1: float,
    v1: np.ndarray,
    t_obs: int,
    *,
    n_reps: int = DEFAULT_N_MC,
    seed: int | tuple[int, ...] = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Stage-b null: per-day one-factor Gaussian replications (verdict-bearing).

    Returns ``(lambda2_sims, ipr_v2_sims)`` of shape (n_reps,), obtained by
    running each replication through the SAME z-standardise -> correlation ->
    eigen pipeline as the observed day.
    """
    beta = one_factor_betas(lambda1, v1)
    n = beta.size
    eps_sd = np.sqrt(np.maximum(1.0 - beta ** 2, 0.0))
    rng = np.random.default_rng(seed)
    f = rng.standard_normal((int(n_reps), int(t_obs), 1))
    eps = rng.standard_normal((int(n_reps), int(t_obs), n))
    x = f * beta[None, None, :] + eps * eps_sd[None, None, :]
    lams, vecs = _stacked_corr_eigs(x)
    lambda2 = lams[:, 1].copy()
    v2 = vecs[:, :, 1]
    ipr2 = np.sum(v2 ** 4, axis=1)
    return lambda2, ipr2


def empirical_p_ge(null_stats: np.ndarray, observed: float) -> float:
    """One-sided add-one empirical p: (#{null >= observed} + 1) / (n + 1)."""
    stats = np.asarray(null_stats, dtype=np.float64)
    stats = stats[np.isfinite(stats)]
    if stats.size == 0 or not np.isfinite(observed):
        return 1.0
    n_ge = int(np.sum(stats >= observed))
    return float((n_ge + 1) / (stats.size + 1))


__all__ = [
    "DEFAULT_N_MC",
    "empirical_p_ge",
    "mp_bulk",
    "one_factor_betas",
    "one_factor_null_day",
    "wishart_null_mc",
]
