"""Surrogate null + BH-FDR for the C-17/C-41 lead-lag mess-gate (H-04).

H-04 demands the directed information (Transfer Entropy / wavelet coherence
phase-lead) be unexplainable by chance under a null that **destroys the
cross-coupling between the two symbols while preserving each symbol's own
marginal distribution AND autocorrelation**. For a lead-lag test this is the
correct null: a phase-randomisation would also kill the within-series structure,
making the comparison test the wrong thing.

The canonical null here is a **circular block shift of the source ("leader")
series relative to the target ("follower")**: the source is rolled by a random
offset (in whole bars). Rolling preserves the source's marginal histogram and
autocorrelation exactly while randomising its temporal alignment to the target,
so any genuine BTC->Alt directed coupling is destroyed. We require a minimum
shift so a near-zero roll cannot accidentally preserve the alignment.

For each surrogate we recompute the SAME statistic (TE at the tested lag, or the
coherence-weighted lead) and the empirical p-value is the fraction of surrogates
whose statistic is >= the observed one, with the standard ``(+1)/(N+1)``
add-one correction (so p is never exactly 0). BH-FDR (Benjamini-Hochberg,
alpha = 0.10) is applied across the whole F-LEADLAG family (all lags × axes ×
symbol-pair variants — registry H-04).

KAPITALFREI: no friction / edge / bps logic anywhere here.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from .transfer_entropy import transfer_entropy, wavelet_coherence_lead

#: BH-FDR level for the F-LEADLAG family (registry H-04).
FDR_ALPHA = 0.10

#: Minimum circular shift as a fraction of series length, so a surrogate cannot
#: land on a near-identity roll that would leave the coupling intact.
MIN_SHIFT_FRACTION = 0.05


@dataclass(slots=True)
class SurrogateResult:
    """Outcome of the circular-shift surrogate null test for one variant."""

    axis: str               # "TE" (C-17) or "WCOH" (C-41)
    lag: int                # lag in grid bars (TE axis); 0 for the WCOH axis
    observed_stat: float
    surrogate_stats: np.ndarray
    p_value: float
    n_surrogates: int

    def as_dict(self) -> dict[str, object]:
        ss = self.surrogate_stats
        return {
            "axis": self.axis,
            "lag": int(self.lag),
            "observed_stat": float(self.observed_stat),
            "p_value": float(self.p_value),
            "n_surrogates": int(self.n_surrogates),
            "surrogate_mean": float(np.mean(ss)) if ss.size else 0.0,
            "surrogate_p95": float(np.percentile(ss, 95)) if ss.size else 0.0,
        }


def _circular_shift(rng: np.random.Generator, x: np.ndarray) -> np.ndarray:
    """Roll ``x`` by a random offset bounded away from 0 and len(x)."""
    n = x.size
    lo = max(1, int(MIN_SHIFT_FRACTION * n))
    hi = n - lo
    if hi <= lo:
        return np.roll(x, max(1, n // 2))
    shift = int(rng.integers(lo, hi))
    return np.roll(x, shift)


def surrogate_test_te(
    source: np.ndarray,
    target: np.ndarray,
    lag: int,
    *,
    n_bins: int,
    n_surrogates: int = 200,
    seed: int = 42,
    progress_cb: Callable[[int, int], None] | None = None,
    progress_every: int = 50,
) -> SurrogateResult:
    """Circular-shift surrogate null for Transfer Entropy ``source -> target``.

    The source series is circularly shifted (preserving its marginal +
    autocorrelation) to destroy the directed coupling; TE is recomputed each
    time. Empirical p = (#{surrogate >= observed} + 1) / (N + 1).
    """
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    n = min(source.size, target.size)
    if n < lag + 16:
        return SurrogateResult("TE", lag, 0.0, np.zeros(0), 1.0, 0)
    source, target = source[:n], target[:n]
    observed = transfer_entropy(source, target, lag, n_bins=n_bins)

    rng = np.random.default_rng(seed)
    stats = np.empty(n_surrogates, dtype=np.float64)
    every = max(1, int(progress_every))
    for k in range(n_surrogates):
        shifted = _circular_shift(rng, source)
        stats[k] = transfer_entropy(shifted, target, lag, n_bins=n_bins)
        if progress_cb is not None and ((k + 1) % every == 0 or k + 1 == n_surrogates):
            progress_cb(k + 1, n_surrogates)

    n_ge = int(np.sum(stats >= observed))
    p_value = (n_ge + 1) / (n_surrogates + 1)
    return SurrogateResult("TE", lag, observed, stats, p_value, n_surrogates)


def surrogate_test_wcoh(
    source: np.ndarray,
    target: np.ndarray,
    grid_ms: float,
    *,
    n_surrogates: int = 200,
    seed: int = 42,
    progress_cb: Callable[[int, int], None] | None = None,
    progress_every: int = 50,
) -> tuple[SurrogateResult, float]:
    """Circular-shift surrogate null for the wavelet coherence statistic (C-41).

    The statistic is the coherence-weighted mean coherence; a genuine coupling
    raises it above the shift-null. Returns ``(SurrogateResult, observed_lead_s)``
    where the lead (in seconds) carries the sign/direction for stability checks.
    """
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    n = min(source.size, target.size)
    if n < 32:
        return SurrogateResult("WCOH", 0, 0.0, np.zeros(0), 1.0, 0), 0.0
    source, target = source[:n], target[:n]
    obs_lead, obs_coh = wavelet_coherence_lead(source, target, grid_ms)

    rng = np.random.default_rng(seed)
    stats = np.empty(n_surrogates, dtype=np.float64)
    every = max(1, int(progress_every))
    for k in range(n_surrogates):
        shifted = _circular_shift(rng, source)
        _, coh = wavelet_coherence_lead(shifted, target, grid_ms)
        stats[k] = coh
        if progress_cb is not None and ((k + 1) % every == 0 or k + 1 == n_surrogates):
            progress_cb(k + 1, n_surrogates)

    n_ge = int(np.sum(stats >= obs_coh))
    p_value = (n_ge + 1) / (n_surrogates + 1)
    res = SurrogateResult("WCOH", 0, obs_coh, stats, p_value, n_surrogates)
    return res, obs_lead


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)`` where ``rejected[i]`` is True if hypothesis
    ``i`` is significant at FDR ``alpha`` and ``p_crit`` is the largest p-value
    that passes (0.0 if none). Input order is preserved in the output mask.
    Identical contract to the C-31 implementation (registry §8.2 convention).
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
