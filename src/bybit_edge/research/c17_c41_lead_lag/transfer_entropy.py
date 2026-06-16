"""Directed-information estimators for the C-17/C-41 lead-lag mess-gate (H-04).

KAPITALFREI: this module measures the *existence* of directed information flow
BTC -> Alt between two symbols' return streams. It contains NO friction / edge /
bps / PnL / Sharpe logic — that would be a separate H-04b (registry H-04
"KAPITALFREIHEIT"). Anything tradability-flavoured here is a bug.

Two axes are provided, both counting into the F-LEADLAG family (registry H-04):

* **C-17 (primary): Shannon Transfer Entropy** on quantile-discretised log
  returns. Strictly causal: ``T_{X->Y}(lag)`` measures how much the past of X
  (at the given lag) reduces uncertainty about the *future* of Y *beyond* what
  Y's own immediate past already explains:

      T_{X->Y} = sum p(y_{t+1}, y_t, x_{t-lag+1})
                     * log2[ p(y_{t+1} | y_t, x_{t-lag+1})
                             / p(y_{t+1} | y_t) ]

  Conditioning on ``y_t`` is what makes this *directed* information rather than
  mere cross-correlation: a symmetric coupling cancels, only the genuine
  asymmetric BTC->Alt arrow survives. TE is non-negative; the surrogate null
  (surrogate.py) provides the significance reference.

* **C-41 (secondary): Wavelet / cross-spectral coherence phase-lead** via a
  numpy-FFT Morlet-style continuous-wavelet cross-spectrum. The cross-spectrum
  phase angle, weighted by coherence, gives a signed lead in seconds; a positive
  X->Y lead means X's oscillations precede Y's. We collapse it to a scalar
  "coherence-weighted lead" statistic so the same surrogate machinery applies.

Both estimators operate on two return series already resampled onto a *common*
time grid (see :func:`align_returns`); the grid synchronisation is what makes a
fixed integer ``lag`` interpretable as ``lag * grid_ms`` milliseconds.
"""
from __future__ import annotations

import numpy as np

#: Default discretisation: number of quantile bins for the log returns (DEC-10).
#: 3 bins (down / flat / up sign-ish terciles) keeps the joint histogram
#: ``n_bins**3`` small enough that TE is estimable from a few thousand samples
#: without crippling plug-in bias, yet captures directional structure.
DEFAULT_N_BINS = 3

#: Default lag universe in *grid steps* for the F-LEADLAG family.
DEFAULT_LAGS: tuple[int, ...] = (1, 2, 3, 5, 10)


# ---------------------------------------------------------------------------
# Grid synchronisation
# ---------------------------------------------------------------------------

def resample_log_returns(
    ts_ms: np.ndarray,
    px: np.ndarray,
    grid_ms: float,
    *,
    t0_ms: float | None = None,
    t1_ms: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Resample an irregular (ts, price) tick stream onto a regular bar grid.

    The last trade price within each ``grid_ms`` bar is used (last-tick / step
    sampling, strictly backward-looking — no interpolation across the bar edge,
    so no look-ahead). Empty bars forward-fill the previous price. Returns
    ``(bar_edges_ms, log_returns)`` where ``log_returns[k]`` is the log return
    over bar ``k`` (``len == n_bars - 1``).
    """
    ts_ms = np.asarray(ts_ms, dtype=np.float64)
    px = np.asarray(px, dtype=np.float64)
    if ts_ms.size < 2:
        return np.zeros(0), np.zeros(0)
    lo = float(ts_ms[0]) if t0_ms is None else float(t0_ms)
    hi = float(ts_ms[-1]) if t1_ms is None else float(t1_ms)
    if hi <= lo:
        return np.zeros(0), np.zeros(0)
    n_bars = int(np.floor((hi - lo) / grid_ms)) + 1
    if n_bars < 3:
        return np.zeros(0), np.zeros(0)
    edges = lo + grid_ms * np.arange(n_bars + 1, dtype=np.float64)
    # Bar index of each tick; clip the final edge into the last bar.
    idx = np.clip(((ts_ms - lo) / grid_ms).astype(np.int64), 0, n_bars - 1)
    last_px = np.full(n_bars, np.nan, dtype=np.float64)
    # Last tick wins within a bar: assigning in chronological order leaves the
    # latest price per bar (ts is sorted by the loaders / caller).
    last_px[idx] = px
    # Forward-fill empty bars with the previous known price.
    valid = ~np.isnan(last_px)
    if not valid.any():
        return np.zeros(0), np.zeros(0)
    first = int(np.argmax(valid))
    last_px[:first] = last_px[first]
    fill_idx = np.maximum.accumulate(np.where(valid, np.arange(n_bars), 0))
    last_px = last_px[fill_idx]
    # Guard against non-positive prices before the log: mark them invalid and
    # forward-fill from the last strictly-positive price.
    good = last_px > 0
    if not good.any():
        return np.zeros(0), np.zeros(0)
    if not good.all():
        f = int(np.argmax(good))
        last_px[:f] = last_px[f]
        fi = np.maximum.accumulate(np.where(good, np.arange(n_bars), 0))
        last_px = last_px[fi]
    log_ret = np.diff(np.log(last_px))
    return edges[: n_bars], log_ret


def align_returns(
    ts_a: np.ndarray,
    px_a: np.ndarray,
    ts_b: np.ndarray,
    px_b: np.ndarray,
    grid_ms: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Resample two tick streams onto a *shared* bar grid and align lengths.

    The common grid spans the overlapping time range of both series so bar ``k``
    refers to the same wall-clock interval in both. Returns ``(ret_a, ret_b)``
    of equal length.
    """
    ts_a = np.asarray(ts_a, dtype=np.float64)
    ts_b = np.asarray(ts_b, dtype=np.float64)
    if ts_a.size < 2 or ts_b.size < 2:
        return np.zeros(0), np.zeros(0)
    t0 = max(float(ts_a[0]), float(ts_b[0]))
    t1 = min(float(ts_a[-1]), float(ts_b[-1]))
    if t1 <= t0:
        return np.zeros(0), np.zeros(0)
    _, ra = resample_log_returns(ts_a, px_a, grid_ms, t0_ms=t0, t1_ms=t1)
    _, rb = resample_log_returns(ts_b, px_b, grid_ms, t0_ms=t0, t1_ms=t1)
    n = min(ra.size, rb.size)
    return ra[:n], rb[:n]


# ---------------------------------------------------------------------------
# C-17: Shannon Transfer Entropy
# ---------------------------------------------------------------------------

def _quantise(x: np.ndarray, n_bins: int) -> np.ndarray:
    """Map a series to ``0..n_bins-1`` by empirical quantile (equal-frequency).

    Equal-frequency binning is robust to the heavy tails of crypto returns and
    keeps each symbol's marginal distribution uniform, so TE reflects coupling
    rather than marginal-shape artefacts.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return np.zeros(0, dtype=np.int64)
    # Quantile edges; ranks break ties deterministically so constant stretches
    # do not collapse all mass into one bin.
    ranks = np.argsort(np.argsort(x, kind="stable"), kind="stable")
    q = ranks / max(1, x.size - 1)
    codes = np.clip((q * n_bins).astype(np.int64), 0, n_bins - 1)
    return codes


def transfer_entropy(
    source: np.ndarray,
    target: np.ndarray,
    lag: int,
    *,
    n_bins: int = DEFAULT_N_BINS,
) -> float:
    """Shannon Transfer Entropy ``T_{source -> target}`` at integer ``lag`` bars.

    Strictly causal plug-in estimator (history length 1 on both series):

        T = sum p(t_next, t_now, s_past) * log2[ p(t_next | t_now, s_past)
                                                 / p(t_next | t_now) ]

    where ``t_next = target[k+1]``, ``t_now = target[k]`` and
    ``s_past = source[k+1-lag]`` (the source value ``lag`` bars before the
    predicted target step). Conditioning on ``t_now`` removes the target's own
    autocorrelation, leaving only the directed source->target contribution.
    Returns a non-negative value in bits; 0.0 when there are too few samples.
    """
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    n = min(source.size, target.size)
    if lag < 1 or n < lag + 8:
        return 0.0
    s_code = _quantise(source[:n], n_bins)
    t_code = _quantise(target[:n], n_bins)
    # Index alignment for k in [lag-1, n-2]: predict target[k+1] from
    # target[k] and source[k+1-lag].
    t_next = t_code[lag:n]            # target[k+1], k from lag-1 .. n-2
    t_now = t_code[lag - 1 : n - 1]  # target[k]
    s_past = s_code[0 : n - lag]     # source[k+1-lag]
    m = min(t_next.size, t_now.size, s_past.size)
    t_next, t_now, s_past = t_next[:m], t_now[:m], s_past[:m]
    if m < 8:
        return 0.0

    b = n_bins
    # Joint histogram over (t_next, t_now, s_past) via flat indexing.
    joint_idx = (t_next * b + t_now) * b + s_past
    joint = np.bincount(joint_idx, minlength=b * b * b).astype(np.float64)
    joint = joint.reshape(b, b, b)
    total = joint.sum()
    if total <= 0:
        return 0.0
    p_joint = joint / total                       # p(t_next, t_now, s_past)
    p_now_past = p_joint.sum(axis=0)              # p(t_now, s_past)
    p_next_now = p_joint.sum(axis=2)              # p(t_next, t_now)
    p_now = p_joint.sum(axis=(0, 2))             # p(t_now)

    te = 0.0
    nz = np.argwhere(p_joint > 0)
    for i, j, k in nz:
        pj = p_joint[i, j, k]
        denom_cond = p_next_now[i, j] * p_now_past[j, k]
        num_cond = pj * p_now[j]
        if denom_cond <= 0 or num_cond <= 0:
            continue
        te += pj * np.log2(num_cond / denom_cond)
    # Numerical floor: plug-in TE is >= 0 in expectation; clamp tiny negatives.
    return float(max(te, 0.0))


# ---------------------------------------------------------------------------
# C-41: Wavelet / cross-spectral coherence phase-lead
# ---------------------------------------------------------------------------

def _morlet_cwt(x: np.ndarray, scales: np.ndarray, w0: float = 6.0) -> np.ndarray:
    """FFT-based complex Morlet continuous wavelet transform.

    Returns a ``(len(scales), len(x))`` complex array. Uses only numpy FFT, no
    scipy special functions, so it carries no extra hard dependency.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    xf = np.fft.fft(x)
    omega = 2.0 * np.pi * np.fft.fftfreq(n)
    out = np.empty((scales.size, n), dtype=np.complex128)
    for i, s in enumerate(scales):
        # Morlet daughter in frequency domain (admissible, normalised).
        sw = s * omega
        psi = (np.pi ** -0.25) * np.exp(-0.5 * (sw - w0) ** 2)
        psi[omega <= 0] = 0.0  # analytic (one-sided) wavelet
        psi *= np.sqrt(2.0 * np.pi * s)
        out[i] = np.fft.ifft(xf * psi)
    return out


def wavelet_coherence_lead(
    source: np.ndarray,
    target: np.ndarray,
    grid_ms: float,
    *,
    n_scales: int = 16,
    min_scale: float = 2.0,
    max_scale: float | None = None,
) -> tuple[float, float]:
    """Coherence-weighted phase-lead of ``source`` over ``target`` (C-41 axis).

    Computes the wavelet cross-spectrum ``W_s * conj(W_t)`` over a bank of
    scales, smooths it in time, and forms the coherence and cross-phase. The
    phase is converted to a lead in seconds per scale (``phase / angular_freq``)
    and averaged weighted by coherence and power.

    Returns ``(lead_seconds, mean_coherence)``. Positive ``lead_seconds`` means
    the source leads the target. ``mean_coherence`` in [0, 1] is the statistic
    the surrogate null is run against (coherence destroyed by shifting kills the
    directed phase relation). KAPITALFREI: pure phase/coherence measurement.
    """
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    n = min(source.size, target.size)
    if n < 16:
        return 0.0, 0.0
    source = source[:n] - np.mean(source[:n])
    target = target[:n] - np.mean(target[:n])
    if max_scale is None:
        max_scale = max(min_scale * 2.0, n / 4.0)
    scales = np.geomspace(min_scale, max_scale, n_scales)
    ws = _morlet_cwt(source, scales)
    wt = _morlet_cwt(target, scales)

    cross = ws * np.conj(wt)            # cross-wavelet spectrum
    # Time smoothing (boxcar) to stabilise the coherence estimate per scale.
    win = max(3, int(n / 16))
    kernel = np.ones(win) / win
    sxx = np.apply_along_axis(lambda r: np.convolve(r, kernel, mode="same"), 1, np.abs(ws) ** 2)
    syy = np.apply_along_axis(lambda r: np.convolve(r, kernel, mode="same"), 1, np.abs(wt) ** 2)
    sxy = np.empty_like(cross)
    sxy.real = np.apply_along_axis(lambda r: np.convolve(r, kernel, mode="same"), 1, cross.real)
    sxy.imag = np.apply_along_axis(lambda r: np.convolve(r, kernel, mode="same"), 1, cross.imag)

    denom = sxx * syy
    coh = np.where(denom > 0, (np.abs(sxy) ** 2) / denom, 0.0)
    coh = np.clip(coh, 0.0, 1.0)
    phase = np.angle(sxy)               # cross-phase (radians)

    # Angular frequency per scale for a Morlet wavelet (w0=6): f ~ w0/(2*pi*s),
    # in cycles per bar; convert to rad/s using grid_ms.
    w0 = 6.0
    freq_per_bar = w0 / (2.0 * np.pi * scales)        # cycles per bar
    bar_s = grid_ms / 1000.0
    ang_freq = 2.0 * np.pi * freq_per_bar / bar_s     # rad / second
    ang_freq = ang_freq[:, None]
    # phase / ang_freq = time lead in seconds, per scale & time.
    lead_s = np.where(ang_freq != 0, phase / ang_freq, 0.0)

    weight = coh * (sxx * syy)          # coherence × power weighting
    wsum = weight.sum()
    if wsum <= 0:
        return 0.0, float(np.mean(coh))
    lead_seconds = float(np.sum(lead_s * weight) / wsum)
    mean_coh = float(np.sum(coh * (sxx * syy)) / max(np.sum(sxx * syy), 1e-30))
    return lead_seconds, mean_coh
