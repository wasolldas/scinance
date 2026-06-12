"""Cyclostationary spectrum estimator on publicTrade inter-arrival times (WP-3).

The core object of C-31 (H-03): TWAP/iceberg execution bots imprint *periodic*
structure onto the inter-arrival times of trades. A cyclostationary signal has
spectral correlation between frequency components separated by a *cyclic
frequency* alpha; ordinary (stationary) noise does not. We estimate the
**Spectral Correlation Density** (SCD) of the binned event-count process and
return it as an ``(alpha, f)`` matrix that the CA-CFAR detector then scans for
peaks.

Pipeline
--------
1. ``bin_counts``       — turn an irregular event timeline (trade timestamps,
                          ms) into a regular count process on a Δt grid.
2. ``spectral_correlation_density`` — FFT-Accumulation-Method estimator of the
                          SCD over a grid of cyclic frequencies alpha.

Numpy + Scipy only (scipy 1.17 is available in this repo; we use
``scipy.signal.get_window`` for tapering and ``numpy.fft`` for transforms — no
new dependency). Causality note: every estimator here consumes a *closed*
slice of the timeline; it never reads a sample beyond the window it is given.
The No-Lookahead discipline lives one layer up (``lead_edge``), which only ever
hands this module *past* ticks.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import get_window

# Default Δt grids the driver sweeps as the F-CFAR parameter family.
DEFAULT_BIN_GRID_MS: tuple[float, ...] = (10.0, 50.0, 100.0)

# Hard safety cap on the bin-grid size. Legitimate windows stay far below this
# (60 days at Δt = 10 ms ≈ 5.2e8 bins); anything above signals corrupt input —
# e.g. a single ts ≈ 0 row among epoch-ms timestamps stretches the grid to
# ~1.8e11 bins (a 1.3 TiB histogram, the T3 crash of 2026-06-11). Guarding
# here turns a runaway allocation into a clear ValueError.
MAX_BINS: int = 1_000_000_000


@dataclass(slots=True)
class CyclicSpectrum:
    """Result of :func:`spectral_correlation_density`.

    Attributes
    ----------
    scd:
        ``(n_alpha, n_freq)`` non-negative magnitude of the spectral
        correlation density. ``scd[i, j]`` is the coupling strength at cyclic
        frequency ``alphas[i]`` and spectral frequency ``freqs[j]``.
    alphas:
        Cyclic frequencies (Hz). ``alphas[0]`` is 0 (the ordinary PSD row).
    freqs:
        Spectral frequencies (Hz), non-negative (real input).
    bin_dt_ms:
        Δt grid width used to build the count process (ms).
    n_bins:
        Number of count-process samples the estimate was built from.
    """

    scd: np.ndarray
    alphas: np.ndarray
    freqs: np.ndarray
    bin_dt_ms: float
    n_bins: int


def inter_arrivals(timestamps_ms: np.ndarray) -> np.ndarray:
    """Return strictly chronological inter-arrival times (ms) from timestamps.

    Non-positive gaps (duplicate / out-of-order exchange timestamps) are kept
    as ``0`` so the marginal distribution is preserved for the surrogate test;
    the caller decides whether to drop them. Input is sorted defensively.
    """
    ts = np.asarray(timestamps_ms, dtype=np.float64)
    if ts.size < 2:
        return np.array([], dtype=np.float64)
    ts = np.sort(ts)
    dt = np.diff(ts)
    dt[dt < 0] = 0.0
    return dt


def bin_counts(
    timestamps_ms: np.ndarray,
    bin_dt_ms: float,
    *,
    t0_ms: float | None = None,
    t1_ms: float | None = None,
) -> tuple[np.ndarray, float]:
    """Bin an event timeline into a regular count process on a Δt grid.

    Parameters
    ----------
    timestamps_ms:
        Trade timestamps in milliseconds (need not be sorted).
    bin_dt_ms:
        Grid width in milliseconds (e.g. 10/50/100).
    t0_ms, t1_ms:
        Optional explicit window bounds (ms). Default: min/max of the data.
        Passing explicit bounds keeps windows comparable across surrogates.

    Returns
    -------
    counts:
        ``int`` count per bin (events that fell in ``[t0 + k·Δt, t0 + (k+1)·Δt)``).
    fs_hz:
        Sampling rate of the count process (Hz) = ``1000 / bin_dt_ms``.
    """
    if bin_dt_ms <= 0:
        raise ValueError(f"bin_dt_ms must be positive, got {bin_dt_ms}")
    ts = np.asarray(timestamps_ms, dtype=np.float64)
    if ts.size == 0:
        return np.zeros(0, dtype=np.int64), 1000.0 / bin_dt_ms
    lo = float(np.min(ts)) if t0_ms is None else float(t0_ms)
    hi = float(np.max(ts)) if t1_ms is None else float(t1_ms)
    if hi <= lo:
        return np.zeros(1, dtype=np.int64), 1000.0 / bin_dt_ms
    n_bins = int(np.ceil((hi - lo) / bin_dt_ms))
    if n_bins > MAX_BINS:
        raise ValueError(
            f"bin grid would need {n_bins} bins (span {hi - lo:.0f} ms at "
            f"dt={bin_dt_ms:g} ms) — exceeds MAX_BINS={MAX_BINS}. This almost "
            "always means corrupt timestamps (e.g. a ts=0 row among epoch-ms "
            "data) or a wrong timestamp unit."
        )
    edges = lo + bin_dt_ms * np.arange(n_bins + 1)
    counts, _ = np.histogram(ts, bins=edges)
    fs_hz = 1000.0 / bin_dt_ms
    return counts.astype(np.int64), fs_hz


def spectral_correlation_density(
    counts: np.ndarray,
    fs_hz: float,
    *,
    segment_len: int = 256,
    overlap: float = 0.5,
    window: str = "hann",
    alpha_max_hz: float | None = None,
    n_alpha: int = 64,
) -> CyclicSpectrum:
    """Estimate the Spectral Correlation Density via the FFT Accumulation Method.

    The count process is mean-removed, split into overlapping tapered segments,
    each FFT'd, and for every candidate cyclic frequency ``alpha`` we average
    the conjugate product ``X(f + alpha/2) · conj(X(f - alpha/2))`` over
    segments (the consistent SCD estimator). ``alpha = 0`` reduces to the
    Welch PSD.

    Parameters
    ----------
    counts:
        Count process from :func:`bin_counts`.
    fs_hz:
        Sampling rate of ``counts`` (Hz).
    segment_len:
        FFT length per segment. Reduced automatically if the series is short.
    overlap:
        Fractional overlap between segments (0..1).
    window:
        Taper passed to ``scipy.signal.get_window``.
    alpha_max_hz:
        Largest cyclic frequency probed. Default: ``fs_hz / 4`` (captures the
        bot-cadence band of interest; periods >= 4·Δt).
    n_alpha:
        Number of cyclic-frequency bins in ``[0, alpha_max_hz]``.

    Returns
    -------
    CyclicSpectrum
    """
    x = np.asarray(counts, dtype=np.float64)
    n = x.size
    if n < 4:
        # Not enough samples for any meaningful estimate.
        alphas = np.zeros(1, dtype=np.float64)
        freqs = np.zeros(1, dtype=np.float64)
        return CyclicSpectrum(
            scd=np.zeros((1, 1), dtype=np.float64),
            alphas=alphas,
            freqs=freqs,
            bin_dt_ms=1000.0 / fs_hz,
            n_bins=n,
        )

    x = x - x.mean()  # remove DC: cyclostationarity lives in the fluctuations
    seg = int(min(segment_len, n))
    # Keep segment length even for a clean rfft frequency grid.
    if seg % 2:
        seg -= 1
    seg = max(seg, 2)
    step = max(1, int(round(seg * (1.0 - overlap))))

    win = get_window(window, seg, fftbins=True).astype(np.float64)
    win_norm = np.sqrt(np.sum(win ** 2))
    if win_norm == 0:
        win_norm = 1.0

    starts = list(range(0, n - seg + 1, step))
    if not starts:
        starts = [0]

    # Full (two-sided) FFT per segment so we can shift by alpha symmetrically.
    freqs_full = np.fft.fftfreq(seg, d=1.0 / fs_hz)
    segs_fft = np.empty((len(starts), seg), dtype=np.complex128)
    for i, s in enumerate(starts):
        segment = x[s:s + seg] * win
        segs_fft[i] = np.fft.fft(segment) / win_norm

    if alpha_max_hz is None:
        alpha_max_hz = fs_hz / 4.0
    n_alpha = max(1, int(n_alpha))
    alphas = np.linspace(0.0, float(alpha_max_hz), n_alpha)

    # Bin spacing of the FFT grid (Hz). alpha is realised as an integer shift
    # of FFT bins (half to +, half to -) so the conjugate product is exact on
    # the grid; we round alpha to the nearest even bin shift.
    df = fs_hz / seg
    half_freqs = freqs_full[: seg // 2 + 1]  # non-negative frequency axis
    n_freq = half_freqs.size

    scd = np.zeros((n_alpha, n_freq), dtype=np.float64)
    for ai, alpha in enumerate(alphas):
        shift = int(round(alpha / df))
        half = shift // 2
        other = shift - half
        # X(f + alpha/2)
        xp = np.roll(segs_fft, -half, axis=1)
        # X(f - alpha/2)
        xm = np.roll(segs_fft, other, axis=1)
        prod = xp * np.conj(xm)            # (n_seg, seg)
        cyclic = prod.mean(axis=0)          # average over segments
        scd[ai] = np.abs(cyclic[:n_freq])

    return CyclicSpectrum(
        scd=scd,
        alphas=alphas,
        freqs=half_freqs,
        bin_dt_ms=1000.0 / fs_hz,
        n_bins=n,
    )
