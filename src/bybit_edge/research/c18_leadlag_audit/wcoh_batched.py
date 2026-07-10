"""Batched Morlet-CWT wavelet-coherence phase-lead for the H-18 audit.

Numerically replicates ``c17_c41_lead_lag.transfer_entropy.wavelet_coherence_lead``
(same Morlet daughter bank, w0 = 6, same ``n_scales = 16`` geomspace scale set
— NOTE: registry H-18's "~50 Skalen" was the research-scan's estimate; the
byte-identical-pipeline clause wins, so the ORIGINAL 16 scales are kept — same
boxcar time smoothing window ``max(3, n // 16)``, same coherence/phase/lead
formulas and guards) but evaluates a whole BATCH of source series against one
target per pass:

* the CWT as one batched FFT multiply (``fft(x) * psi_bank`` -> ``ifft``),
* the boxcar "same" smoothing as an FFT convolution (identical to
  ``np.convolve(mode="same")`` up to float rounding ~1e-13, bounded by the
  self-test), applied to the whole ``(B, S, n)`` block at once.

KAPITALFREI: pure phase/coherence measurement, no tradability logic.
"""
from __future__ import annotations

import numpy as np

from .surrogate_gpu import backend_device, batch_circular_shift, generate_shift_offsets
from .te_batched import BatchedSurrogateResult

#: Original constants (c17_c41_lead_lag.transfer_entropy.wavelet_coherence_lead).
W0 = 6.0
N_SCALES = 16
MIN_SCALE = 2.0


def _scales(n: int, n_scales: int = N_SCALES, min_scale: float = MIN_SCALE) -> np.ndarray:
    """The original scale bank: geomspace(min_scale, max(2*min_scale, n/4))."""
    max_scale = max(min_scale * 2.0, n / 4.0)
    return np.geomspace(min_scale, max_scale, n_scales)


def _psi_bank(n: int, scales: np.ndarray, w0: float = W0) -> np.ndarray:
    """Frequency-domain Morlet daughters, identical to ``_morlet_cwt``."""
    omega = 2.0 * np.pi * np.fft.fftfreq(n)
    psi = np.empty((scales.size, n), dtype=np.float64)
    for i, s in enumerate(scales):
        sw = s * omega
        row = (np.pi ** -0.25) * np.exp(-0.5 * (sw - w0) ** 2)
        row[omega <= 0] = 0.0
        row *= np.sqrt(2.0 * np.pi * s)
        psi[i] = row
    return psi


def _smooth_same_np(x: np.ndarray, win: int) -> np.ndarray:
    """Boxcar ``np.convolve(row, ones(win)/win, mode="same")`` along the last
    axis for an arbitrary-shaped real block, via FFT convolution."""
    n = x.shape[-1]
    nfull = n + win - 1
    kernel = np.ones(win, dtype=np.float64) / win
    xf = np.fft.rfft(x, n=nfull, axis=-1)
    kf = np.fft.rfft(kernel, n=nfull)
    full = np.fft.irfft(xf * kf, n=nfull, axis=-1)
    start = (win - 1) // 2
    return full[..., start : start + n]


def wavelet_coherence_lead_batch(
    src_batch,
    target: np.ndarray,
    grid_ms: float,
    *,
    backend: str = "numpy",
) -> tuple[np.ndarray, np.ndarray]:
    """Coherence-weighted phase-lead of every source row over ``target``.

    Returns ``(leads_seconds, mean_coherences)`` as ``(B,)`` float64 numpy
    arrays (numpy contract on every backend). Replicates the original
    function row-by-row: centering, CWT, cross-spectrum, boxcar smoothing,
    coherence clip, phase -> lead conversion, coherence*power weighting and
    the degenerate ``wsum <= 0`` fallback (plain mean coherence, lead 0).
    """
    target = np.asarray(target, dtype=np.float64)
    if backend == "numpy":
        src = np.asarray(src_batch, dtype=np.float64)
        n = min(src.shape[1], target.size)
    else:
        n = min(int(src_batch.shape[1]), target.size)
        src = src_batch
    b_rows = int(src.shape[0])
    if n < 16:
        return np.zeros(b_rows, dtype=np.float64), np.zeros(b_rows, dtype=np.float64)

    scales = _scales(n)
    psi = _psi_bank(n, scales)
    win = max(3, int(n / 16))
    freq_per_bar = W0 / (2.0 * np.pi * scales)
    bar_s = grid_ms / 1000.0
    ang_freq = 2.0 * np.pi * freq_per_bar / bar_s  # (S,), rad/s, > 0

    if backend == "numpy":
        s_c = src[:, :n] - src[:, :n].mean(axis=1, keepdims=True)
        t_c = target[:n] - target[:n].mean()
        ws = np.fft.ifft(np.fft.fft(s_c, axis=1)[:, None, :] * psi[None, :, :], axis=2)
        wt = np.fft.ifft(np.fft.fft(t_c)[None, :] * psi, axis=1)  # (S, n)
        cross = ws * np.conj(wt)[None, :, :]
        sxx = _smooth_same_np(np.abs(ws) ** 2, win)
        syy = _smooth_same_np(np.abs(wt) ** 2, win)[None, :, :]
        sxy = _smooth_same_np(cross.real, win) + 1j * _smooth_same_np(cross.imag, win)
        denom = sxx * syy
        coh = np.where(denom > 0, (np.abs(sxy) ** 2) / np.where(denom > 0, denom, 1.0), 0.0)
        coh = np.clip(coh, 0.0, 1.0)
        phase = np.angle(sxy)
        lead_s = phase / ang_freq[None, :, None]
        weight = coh * denom
        wsum = weight.sum(axis=(1, 2))
        pow_sum = denom.sum(axis=(1, 2))
        lead = np.where(wsum > 0, (lead_s * weight).sum(axis=(1, 2)) / np.where(wsum > 0, wsum, 1.0), 0.0)
        mean_coh_w = (coh * denom).sum(axis=(1, 2)) / np.maximum(pow_sum, 1e-30)
        mean_coh_plain = coh.mean(axis=(1, 2))
        mean_coh = np.where(wsum > 0, mean_coh_w, mean_coh_plain)
        return lead, mean_coh

    torch, device = backend_device(backend)
    src_t = src if not isinstance(src, np.ndarray) else torch.as_tensor(
        src, dtype=torch.float64, device=device
    )
    src_t = src_t[:, :n]
    tgt_t = torch.as_tensor(target[:n], dtype=torch.float64, device=device)
    psi_t = torch.as_tensor(psi, dtype=torch.float64, device=device)
    s_c = src_t - src_t.mean(dim=1, keepdim=True)
    t_c = tgt_t - tgt_t.mean()
    ws = torch.fft.ifft(torch.fft.fft(s_c, dim=1)[:, None, :] * psi_t[None, :, :], dim=2)
    wt = torch.fft.ifft(torch.fft.fft(t_c)[None, :] * psi_t, dim=1)
    cross = ws * torch.conj(wt)[None, :, :]

    def _smooth_same_torch(x):
        nfull = n + win - 1
        kernel = torch.full((win,), 1.0 / win, dtype=torch.float64, device=device)
        xf = torch.fft.rfft(x, n=nfull, dim=-1)
        kf = torch.fft.rfft(kernel, n=nfull)
        full = torch.fft.irfft(xf * kf, n=nfull, dim=-1)
        start = (win - 1) // 2
        return full[..., start : start + n]

    sxx = _smooth_same_torch(torch.abs(ws) ** 2)
    syy = _smooth_same_torch(torch.abs(wt) ** 2)[None, :, :]
    sxy = _smooth_same_torch(cross.real) + 1j * _smooth_same_torch(cross.imag)
    denom = sxx * syy
    one = torch.ones((), dtype=torch.float64, device=device)
    coh = torch.where(denom > 0, (torch.abs(sxy) ** 2) / torch.where(denom > 0, denom, one), torch.zeros_like(denom))
    coh = torch.clamp(coh, 0.0, 1.0)
    phase = torch.angle(sxy)
    ang = torch.as_tensor(ang_freq, dtype=torch.float64, device=device)
    lead_s = phase / ang[None, :, None]
    weight = coh * denom
    wsum = weight.sum(dim=(1, 2))
    pow_sum = denom.sum(dim=(1, 2))
    lead = torch.where(wsum > 0, (lead_s * weight).sum(dim=(1, 2)) / torch.where(wsum > 0, wsum, one), torch.zeros_like(wsum))
    floor = torch.full_like(pow_sum, 1e-30)
    mean_coh_w = (coh * denom).sum(dim=(1, 2)) / torch.maximum(pow_sum, floor)
    mean_coh_plain = coh.mean(dim=(1, 2))
    mean_coh = torch.where(wsum > 0, mean_coh_w, mean_coh_plain)
    return lead.cpu().numpy(), mean_coh.cpu().numpy()


def surrogate_test_wcoh_batched(
    source: np.ndarray,
    target: np.ndarray,
    grid_ms: float,
    *,
    n_surrogates: int,
    seed: int,
    backend: str = "numpy",
    chunk_size: int = 512,
) -> tuple[BatchedSurrogateResult, float]:
    """Batched replica of the original ``surrogate_test_wcoh``.

    Identical circular-shift null / RNG consumption, identical guards and
    p-value; the coherence statistic per surrogate is evaluated in
    ``chunk_size`` CWT batches. Returns ``(result, observed_lead_seconds)``.
    """
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    n = min(source.size, target.size)
    if n < 32:
        return BatchedSurrogateResult("WCOH", 0, 0.0, np.zeros(0), 1.0, 0), 0.0
    source, target = source[:n], target[:n]
    leads, cohs = wavelet_coherence_lead_batch(source[None, :], target, grid_ms, backend=backend)
    obs_lead, obs_coh = float(leads[0]), float(cohs[0])

    offsets = generate_shift_offsets(n, n_surrogates, seed)
    stats = np.empty(n_surrogates, dtype=np.float64)
    for k0 in range(0, n_surrogates, max(1, int(chunk_size))):
        k1 = min(n_surrogates, k0 + max(1, int(chunk_size)))
        shifted = batch_circular_shift(source, offsets[k0:k1], backend=backend)
        _, coh_chunk = wavelet_coherence_lead_batch(shifted, target, grid_ms, backend=backend)
        stats[k0:k1] = coh_chunk
    n_ge = int(np.sum(stats >= obs_coh))
    p_value = (n_ge + 1) / (n_surrogates + 1)
    res = BatchedSurrogateResult("WCOH", 0, obs_coh, stats, p_value, n_surrogates)
    return res, obs_lead
