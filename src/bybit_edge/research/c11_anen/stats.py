"""Statistics for the H-11 AnEn vs. HAR-RV mess-gate (KAPITALFREI).

  * ``crps_ensemble`` — proper CRPS of the empirical k-member ensemble
    distribution (registry H-11: the AnEn forecast IS the empirical
    distribution of the log-RV(t'+1..t'+3) targets of the 20 analogs):
    CRPS(F, y) = (1/k) sum_i |x_i - y| - (1/(2 k^2)) sum_i sum_j |x_i - x_j|.
  * ``crps_point`` — degenerate-distribution CRPS of a point forecast:
    CRPS = |forecast - observation|. Per registry H-11 this applies ONLY to
    the HAR-RV baseline ("CRPS der Punktprognose"), never to the AnEn.
  * ``pit_ranks`` — PIT rank of the observation within the k-member ensemble
    (non-judgment-bearing calibration diagnostic, registry: "mitberichtet").
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
    """Degenerate-distribution CRPS of a point forecast: |forecast - obs|.

    A point forecast is a degenerate predictive distribution, for which the
    CRPS reduces exactly to the absolute error. Registry H-11 assigns this
    rule to the HAR-RV BASELINE only ("Baseline: ... CRPS der Punktprognose =
    |Prognose - Beobachtung|"); the AnEn is scored by ``crps_ensemble`` on its
    full 20-member distribution. Vectorised; NaN propagates.
    """
    return np.abs(np.asarray(forecast, dtype=np.float64)
                  - np.asarray(observation, dtype=np.float64))


def crps_ensemble(members: np.ndarray, observation: np.ndarray) -> np.ndarray:
    """Proper CRPS of the empirical k-member ensemble distribution.

    Standard closed form for an empirical-CDF forecast with members x_1..x_k
    (Gneiting & Raftery 2007):

        CRPS(F, y) = (1/k) sum_i |x_i - y| - (1/(2 k^2)) sum_i sum_j |x_i - x_j|

    This is the registered H-11 scoring rule for the AnEn ("AnEn-
    Vorhersageverteilung = empirische Verteilung der log-RV(t'+1..t'+3) der
    20 Analoga"). ``members`` has shape (n_days, k) (a single (k,) vector is
    accepted and treated as one forecast day); ``observation`` has shape
    (n_days,). Returns per-day CRPS values; NaN propagates. A degenerate
    ensemble (all members identical) reduces exactly to ``crps_point``.
    """
    x = np.asarray(members, dtype=np.float64)
    y = np.asarray(observation, dtype=np.float64)
    if x.ndim == 1:
        x = x[None, :]
    y = np.atleast_1d(y)
    if x.shape[0] != y.shape[0]:
        raise ValueError(f"members rows ({x.shape[0]}) != observations ({y.shape[0]})")
    if x.shape[1] < 1:
        raise ValueError("ensemble must have at least one member")
    term_obs = np.mean(np.abs(x - y[:, None]), axis=1)
    term_spread = 0.5 * np.mean(np.abs(x[:, :, None] - x[:, None, :]), axis=(1, 2))
    return term_obs - term_spread


def pit_ranks(members: np.ndarray, observation: np.ndarray) -> np.ndarray:
    """PIT rank of each observation within its k-member ensemble (0..k).

    rank(t) = #{ members of day t strictly below the observation } — a
    deterministic tie rule (ties count as members >= obs). For a calibrated
    ensemble the ranks are ~uniform over the k+1 bins (rank histogram).
    NON-JUDGMENT-BEARING secondary diagnostic (registry H-11: "Rank-
    Histogramm/PIT ... mitberichtet"); no gate condition reads it.
    """
    x = np.asarray(members, dtype=np.float64)
    y = np.asarray(observation, dtype=np.float64)
    if x.ndim == 1:
        x = x[None, :]
    y = np.atleast_1d(y)
    if x.shape[0] != y.shape[0]:
        raise ValueError(f"members rows ({x.shape[0]}) != observations ({y.shape[0]})")
    return np.sum(x < y[:, None], axis=1).astype(np.int64)


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

    NOTE: BH rejection at alpha=0.10 does NOT imply p <= 0.05 — the registered
    H-11 gate additionally requires the raw bootstrap p <= BOOTSTRAP_P_MAX,
    enforced separately in the driver (``boot_p_le_max``).
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
    "crps_ensemble",
    "crps_point",
    "crpss",
    "pit_ranks",
]
