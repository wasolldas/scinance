"""Surrogate null test + BH-FDR for the C-31 CFAR pipeline (WP-3, H-03).

H-03 demands: the detected cyclostationary peak must be unexplainable by chance
under a null that *destroys the cyclic structure while preserving the marginal
inter-arrival distribution*. The canonical such null is a **permutation of the
inter-arrival times** (PRD §3: "geshuffelte Inter-Arrivals"): shuffling Δt
keeps the set of gaps identical (same marginal, same rate) but scrambles their
temporal order, killing any periodicity.

For each surrogate we rebuild the timeline from the shuffled gaps, run the exact
same bin → SCD → CA-CFAR pipeline, and record its top CFAR SNR. The empirical
p-value of the observed peak is the fraction of surrogates whose top SNR is
>= the observed top SNR (PRD §3: "Anteil Surrogates mit >= SNR"), with the
standard ``(+1)/(N+1)`` add-one correction so p is never exactly 0.

BH-FDR (Benjamini-Hochberg, alpha = 0.10) is applied across all parameter
variants tested in parallel — the F-CFAR family (registry H-03): different
bin grids / CFAR thresholds / spectral params are one family.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from .cfar_detector import CfarConfig, detect_peaks, top_snr
from .cyclic_spectrum import bin_counts, inter_arrivals, spectral_correlation_density

#: BH-FDR level for the F-CFAR family (registry H-03).
FDR_ALPHA = 0.10


@dataclass(slots=True)
class SurrogateResult:
    """Outcome of the surrogate null test for one parameter variant."""

    observed_snr: float
    surrogate_snrs: np.ndarray
    p_value: float
    n_surrogates: int
    bin_dt_ms: float
    threshold_factor: float

    def as_dict(self) -> dict[str, object]:
        return {
            "observed_snr": float(self.observed_snr),
            "p_value": float(self.p_value),
            "n_surrogates": int(self.n_surrogates),
            "surrogate_snr_mean": float(np.mean(self.surrogate_snrs))
            if self.surrogate_snrs.size
            else 0.0,
            "surrogate_snr_p95": float(np.percentile(self.surrogate_snrs, 95))
            if self.surrogate_snrs.size
            else 0.0,
            "bin_dt_ms": float(self.bin_dt_ms),
            "threshold_factor": float(self.threshold_factor),
        }


def _pipeline_top_snr(
    timestamps_ms: np.ndarray,
    bin_dt_ms: float,
    cfar: CfarConfig,
    *,
    segment_len: int,
    n_alpha: int,
    t0_ms: float | None,
    t1_ms: float | None,
) -> float:
    """Run bin → SCD → CA-CFAR and return the top CFAR SNR."""
    counts, fs_hz = bin_counts(timestamps_ms, bin_dt_ms, t0_ms=t0_ms, t1_ms=t1_ms)
    spectrum = spectral_correlation_density(
        counts, fs_hz, segment_len=segment_len, n_alpha=n_alpha
    )
    peaks = detect_peaks(spectrum, cfar)
    return top_snr(peaks)


def _rebuild_from_gaps(t0_ms: float, gaps: np.ndarray) -> np.ndarray:
    """Reconstruct a timeline from an (shuffled) inter-arrival sequence."""
    return t0_ms + np.concatenate([[0.0], np.cumsum(gaps)])


def surrogate_test(
    timestamps_ms: np.ndarray,
    *,
    bin_dt_ms: float,
    cfar: CfarConfig,
    n_surrogates: int = 200,
    seed: int = 42,
    segment_len: int = 256,
    n_alpha: int = 64,
    progress_cb: Callable[[int, int], None] | None = None,
    progress_every: int = 50,
) -> SurrogateResult:
    """Permutation surrogate null test for one parameter variant.

    The observed top CFAR SNR is compared against the distribution of top SNRs
    obtained from ``n_surrogates`` random permutations of the inter-arrival
    times. Empirical p = (#{surrogate >= observed} + 1) / (N + 1).

    The window bounds are held fixed (t0 = first tick, t1 = original last tick)
    across all surrogates so the count-process length — and therefore the SCD
    frequency grid — is identical, making the SNRs directly comparable.

    ``progress_cb(done, total)`` (if given) is called every ``progress_every``
    surrogates so a caller can surface progress and a future hang is visible
    (overnight 2026-06-14: 5400 s silent). It is purely observational and never
    touches the statistic.
    """
    ts = np.sort(np.asarray(timestamps_ms, dtype=np.float64))
    gaps = inter_arrivals(ts)
    if gaps.size < 4:
        return SurrogateResult(
            observed_snr=0.0,
            surrogate_snrs=np.zeros(0),
            p_value=1.0,
            n_surrogates=0,
            bin_dt_ms=bin_dt_ms,
            threshold_factor=cfar.threshold_factor,
        )

    t0 = float(ts[0])
    t1 = float(ts[-1])
    observed_snr = _pipeline_top_snr(
        ts, bin_dt_ms, cfar,
        segment_len=segment_len, n_alpha=n_alpha, t0_ms=t0, t1_ms=t1,
    )

    rng = np.random.default_rng(seed)
    surrogate_snrs = np.empty(n_surrogates, dtype=np.float64)
    every = max(1, int(progress_every))
    for k in range(n_surrogates):
        shuffled = rng.permutation(gaps)
        surro_ts = _rebuild_from_gaps(t0, shuffled)
        # Fix t0/t1 to the surrogate's own span so its grid matches the
        # observed run's bin count (cumsum of the same gaps => same total span).
        surrogate_snrs[k] = _pipeline_top_snr(
            surro_ts, bin_dt_ms, cfar,
            segment_len=segment_len, n_alpha=n_alpha,
            t0_ms=t0, t1_ms=float(surro_ts[-1]),
        )
        if progress_cb is not None and ((k + 1) % every == 0 or k + 1 == n_surrogates):
            progress_cb(k + 1, n_surrogates)

    n_ge = int(np.sum(surrogate_snrs >= observed_snr))
    p_value = (n_ge + 1) / (n_surrogates + 1)
    return SurrogateResult(
        observed_snr=observed_snr,
        surrogate_snrs=surrogate_snrs,
        p_value=p_value,
        n_surrogates=n_surrogates,
        bin_dt_ms=bin_dt_ms,
        threshold_factor=cfar.threshold_factor,
    )


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)`` where ``rejected[i]`` is True if hypothesis
    ``i`` is significant at FDR ``alpha`` and ``p_crit`` is the largest p-value
    that passes (0.0 if none). Order of the input list is preserved in the
    output mask.
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
