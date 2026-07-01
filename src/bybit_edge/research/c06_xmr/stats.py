"""Statistics for the C-06 XMR mess-gate (H-07, KAPITALFREI).

Provides, on the reversion-signed forward-return samples:

  * ``surrogate_p_mu_positive`` — permutation/block-shift surrogate p for
    "mu_rev > 0". The z-series is decoupled from the forward returns (destroying
    the z->forward coupling that the conditioning exploits) while preserving the
    marginal forward-return distribution; the statistic is the conditioned mean.
  * ``block_bootstrap_ci`` — block-bootstrap 95% CI of mu_rev (conditioned AND
    baseline), preserving short-range autocorrelation.
  * ``benjamini_hochberg`` — BH-FDR alpha=0.10 (OWN copy per registry §8.2; no
    cross-import between research packages).
  * ``ci_non_overlap`` — the non-triviality anchor: do the conditioned and
    baseline 95% CIs NOT overlap (with conditioned strictly greater)?

KAPITALFREI: pure statistics on a measurement sample. No friction, bps, edge,
PnL, Sharpe. numpy only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: BH-FDR level for the F-XMR family (registry H-07).
FDR_ALPHA = 0.10

#: Surrogate-p threshold (registry H-07: p <= 0.05).
SURROGATE_P_MAX = 0.05

#: Bootstrap CI level (registry H-07: 95%).
CI_LEVEL = 0.95


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


def surrogate_p_mu_positive(
    z: np.ndarray,
    rev_ret: np.ndarray,
    conditioned_mask: np.ndarray,
    *,
    n_surrogates: int = 200,
    seed: int = 42,
) -> tuple[float, float]:
    """Permutation surrogate p for "conditioned mu_rev > 0".

    Each surrogate independently PERMUTES the forward-return-derived sample
    against the conditioning membership: it draws a random subset of the SAME
    size as the conditioned set from the full baseline sample and takes its mean.
    This destroys the z->forward coupling (the conditioning carries no
    information under the null) while preserving the marginal reversion-return
    distribution. One-sided empirical p for the observed conditioned mean being
    exceeded:
        ``p = (#{surrogate_mean >= observed_mean} + 1) / (N + 1)``.

    Returns ``(p_value, surrogate_mean_mean)``. ``z`` is accepted for signature
    symmetry with the block-shift variant but the decoupling is by resampling.
    """
    rr = np.asarray(rev_ret, dtype=np.float64)
    cond = np.asarray(conditioned_mask, dtype=bool)
    finite = np.isfinite(rr)
    base = rr[finite]
    cond_sample = rr[cond & finite]
    n_cond = cond_sample.size
    if n_cond < 1 or base.size < 1 or n_surrogates < 1:
        return 1.0, 0.0
    observed = float(np.mean(cond_sample))
    rng = np.random.default_rng(seed)
    stats = np.empty(n_surrogates, dtype=np.float64)
    n_base = base.size
    for k in range(n_surrogates):
        idx = rng.integers(0, n_base, size=n_cond)  # random subset (with repl.)
        stats[k] = float(np.mean(base[idx]))
    n_ge = int(np.sum(stats >= observed))
    p_value = (n_ge + 1) / (n_surrogates + 1)
    return p_value, float(np.mean(stats))


def block_bootstrap_ci(
    sample: np.ndarray,
    *,
    n_bootstrap: int = 1000,
    block_size: int = 12,
    ci_level: float = CI_LEVEL,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Block-bootstrap CI of the mean, preserving short-range autocorrelation.

    Resamples contiguous blocks of length ``block_size`` (circular) until the
    sample length is covered, computes the mean per resample, and returns
    ``(mean, ci_low, ci_high)`` at the given two-sided ``ci_level``. Falls back
    to ``(mean, nan, nan)`` for an empty sample.
    """
    x = np.asarray(sample, dtype=np.float64)
    x = x[np.isfinite(x)]
    n = x.size
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    mean = float(np.mean(x))
    if n == 1 or n_bootstrap < 1:
        return mean, mean, mean
    bs = max(1, min(block_size, n))
    n_blocks = int(np.ceil(n / bs))
    rng = np.random.default_rng(seed)
    means = np.empty(n_bootstrap, dtype=np.float64)
    starts_pool = np.arange(n)
    for b in range(n_bootstrap):
        starts = rng.choice(starts_pool, size=n_blocks, replace=True)
        # circular contiguous blocks
        offs = (starts[:, None] + np.arange(bs)[None, :]) % n
        resample = x[offs.reshape(-1)][:n]
        means[b] = float(np.mean(resample))
    lo_q = (1.0 - ci_level) / 2.0
    hi_q = 1.0 - lo_q
    ci_low = float(np.quantile(means, lo_q))
    ci_high = float(np.quantile(means, hi_q))
    return mean, ci_low, ci_high


def ci_non_overlap(
    cond_low: float,
    cond_high: float,
    base_low: float,
    base_high: float,
) -> bool:
    """Non-triviality anchor: conditioned CI strictly ABOVE the baseline CI.

    True iff the conditioned 95% CI and the baseline 95% CI do NOT overlap AND
    the conditioned interval lies above the baseline one (``cond_low >
    base_high``). Amplification only counts as conditioned > baseline (registry
    H-07 criterion 4). NaN bounds => False.
    """
    vals = (cond_low, cond_high, base_low, base_high)
    if any(not np.isfinite(v) for v in vals):
        return False
    return bool(cond_low > base_high)


@dataclass(slots=True)
class CellStats:
    """Statistics for one (horizon x window x {conditioned|baseline}) cell."""

    mu_rev: float
    ci_low: float
    ci_high: float
    n_events: int


__all__ = [
    "FDR_ALPHA",
    "SURROGATE_P_MAX",
    "CI_LEVEL",
    "CellStats",
    "benjamini_hochberg",
    "block_bootstrap_ci",
    "ci_non_overlap",
    "surrogate_p_mu_positive",
]
