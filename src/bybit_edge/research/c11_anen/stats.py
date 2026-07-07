"""Statistics for the H-11 AnEn vs. HAR-RV mess-gate (KAPITALFREI).

  * ``crps_point`` — the pre-registered degenerate-distribution CRPS of a
    point forecast: CRPS = |forecast - observation| (registry H-11 fixes
    EXACTLY this simplified variant; the full distributional CRPS integral is
    deliberately NOT implemented here).
  * ``crpss`` — skill score CRPSS = 1 - sum(CRPS_AnEn) / sum(CRPS_HAR).
  * ``block_bootstrap_p`` — Diebold-Mariano-style circular block bootstrap
    (block length 5 days, 1000 reps) for H0: mean CRPS difference
    (HAR - AnEn) <= 0, per symbol x window.
  * ``benjamini_hochberg`` — BH-FDR alpha=0.10 over the F-ANEN family
    (OWN copy per registry §8.2; no cross-import between research packages).

KAPITALFREI: pure forecast-scoring statistics. numpy only.
"""
from __future__ import annotations

import numpy as np

#: BH-FDR level for the F-ANEN family (registry H-11: 2 symbols x 2 windows).
FDR_ALPHA = 0.10

#: Pre-registered gate thresholds (registry H-11) — gate-neutral constants;
#: the gate-auditor adjudicates.
CRPSS_MIN = 0.05
BOOTSTRAP_P_MAX = 0.05

#: Pre-registered bootstrap parameters (registry H-11).
BLOCK_LEN_DAYS = 5
N_BOOTSTRAP = 1000


def crps_point(forecast: np.ndarray, observation: np.ndarray) -> np.ndarray:
    """Degenerate-distribution CRPS of the point forecast: |forecast - obs|.

    This is the registry-H-11 pre-registered scoring rule (a point forecast is
    a degenerate predictive distribution, for which the CRPS reduces exactly
    to the absolute error). Vectorised; NaN propagates.
    """
    return np.abs(np.asarray(forecast, dtype=np.float64)
                  - np.asarray(observation, dtype=np.float64))


def crpss(crps_anen: np.ndarray, crps_har: np.ndarray) -> float:
    """CRPSS = 1 - sum(CRPS_AnEn) / sum(CRPS_HAR) (registry H-11, verbatim).

    Positive values mean the AnEn beats the HAR baseline. NaN when the HAR
    CRPS sum is zero or either series is empty/non-finite.
    """
    a = np.asarray(crps_anen, dtype=np.float64)
    h = np.asarray(crps_har, dtype=np.float64)
    if a.size == 0 or h.size == 0:
        return float("nan")
    sum_a = float(np.sum(a))
    sum_h = float(np.sum(h))
    if not np.isfinite(sum_a) or not np.isfinite(sum_h) or sum_h <= 0.0:
        return float("nan")
    return 1.0 - sum_a / sum_h


def block_bootstrap_p(
    d: np.ndarray,
    *,
    block_len: int = BLOCK_LEN_DAYS,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 42,
) -> float:
    """DM-style circular block bootstrap p for H0: mean(d) <= 0.

    ``d`` is the daily CRPS difference (HAR - AnEn); positive mean = AnEn
    better. The series is centred at zero (imposing H0), resampled in circular
    contiguous blocks of ``block_len`` days (preserving short-range
    autocorrelation of the loss differential, Diebold-Mariano-artig), and the
    one-sided empirical p is

        p = (#{mean(d*_b) >= mean(d_obs)} + 1) / (n_bootstrap + 1).

    Returns 1.0 for degenerate input (fewer than 2 finite differences).
    """
    x = np.asarray(d, dtype=np.float64)
    x = x[np.isfinite(x)]
    n = x.size
    if n < 2 or n_bootstrap < 1:
        return 1.0
    observed = float(np.mean(x))
    centered = x - observed  # impose H0: mean(d) = 0 (boundary of <= 0)
    bs = max(1, min(int(block_len), n))
    n_blocks = int(np.ceil(n / bs))
    rng = np.random.default_rng(seed)
    offsets = np.arange(bs)
    count_ge = 0
    for _ in range(n_bootstrap):
        starts = rng.integers(0, n, size=n_blocks)
        idx = (starts[:, None] + offsets[None, :]) % n  # circular blocks
        resample = centered[idx.reshape(-1)][:n]
        if float(np.mean(resample)) >= observed:
            count_ge += 1
    return (count_ge + 1) / (n_bootstrap + 1)


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i`` is
    significant at FDR ``alpha`` and ``p_crit`` the largest passing p-value
    (0.0 if none). Input order preserved. OWN copy (registry §8.2 convention —
    each research package keeps its own; no cross-import between packages).
    """
    m = len(p_values)
    if m == 0:
        return [], 0.0
    order = sorted(range(m), key=lambda i: p_values[i])
    p_crit = 0.0
    k_max = -1
    for rank, idx in enumerate(order, start=1):
        if p_values[idx] <= (rank / m) * alpha:
            k_max = rank
            p_crit = p_values[idx]
    rejected = [False] * m
    if k_max >= 0:
        for rank, idx in enumerate(order, start=1):
            if rank <= k_max:
                rejected[idx] = True
    return rejected, p_crit


__all__ = [
    "BLOCK_LEN_DAYS",
    "BOOTSTRAP_P_MAX",
    "CRPSS_MIN",
    "FDR_ALPHA",
    "N_BOOTSTRAP",
    "benjamini_hochberg",
    "block_bootstrap_p",
    "crps_point",
    "crpss",
]
