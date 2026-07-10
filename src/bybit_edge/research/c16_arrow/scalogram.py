"""Complex-Morlet CWT log-power scalograms for the H-16 time-arrow pipeline.

Registered representation (registry H-16, fixed): per 512 s window of the
1 s signed trade-imbalance series, a single-channel image of shape
(64 scales x 512 time bins); scales are 64 log-spaced Fourier periods from
2 s to 256 s; wavelet = complex Morlet (omega0 = 6); pixel value =
standardised log power. Window stride 64 s.

Implementation follows Torrence & Compo (1998): CWT as multiplication in the
frequency domain, ``W(s, t) = ifft(fft(x_pad) * psi_hat(s * omega))`` with
the analytic Morlet ``psi_hat(s w) = pi^{-1/4} sqrt(2 pi s / dt)
exp(-(s w - omega0)^2 / 2)`` supported on positive frequencies only.

Edge handling / cone of influence (builder documentation duty, registry
H-16 "CWT-Randeffekte"): each 512-sample window is REFLECT-padded to twice
its length before the FFT and the central 512 columns are kept, so no
circular wrap-around of real data occurs. The e-folding cone of influence
of the Morlet is sqrt(2)*s; for the largest registered period (256 s,
s ~ 248 s) the COI covers most of the window, i.e. large-scale pixels near
the window edges are smoothing over reflected data. This is IDENTICAL for
the forward and the reversed variant (reflection commutes with reversal),
so it cannot fabricate a time-arrow signal; it only dampens large-scale
contrast. Documented in README_H16.md.

Reversal semantics (registry H-16, binding): the TIME-REVERSED class is
built by reversing the RAW 1 s series BEFORE the CWT
(``cwt_logpower(x[::-1])``), never by flipping the finished image —
:func:`scalogram_pair` is the single place both classes are built.
Mathematical note (documented honesty, tested in the unit tests): for the
COMPLEX coefficients reversal and CWT do NOT commute
(``CWT(x[::-1]) == conj(flip(CWT(x)))``, imaginary parts differ), while for
the log-POWER image with symmetric padding the two coincide exactly
(``|CWT(x[::-1])| == flip(|CWT(x)|)``). The registered raw-series reversal
is implemented regardless — it stays correct under ANY later representation
change (e.g. adding a phase channel) and is what was pre-registered.

Torch path: :func:`cwt_logpower_batch_torch` mirrors the numpy reference
step for step with ``torch.fft`` for GPU batching. torch is OPTIONAL — the
module imports without it; :func:`verify_torch_parity` cross-checks the two
implementations at run start on the GPU machine (first-run safety, the
sandbox has no torch).

KAPITALFREI: pure signal representation. numpy (+ optional torch) only.
"""
from __future__ import annotations

from typing import Any

import numpy as np

try:  # torch optional (sandbox has none; GPU machine does)
    import torch

    _TORCH_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only without torch installed
    torch = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False

#: Registered window length in seconds (= samples at 1 Hz).
WINDOW_S = 512
#: Registered window stride in seconds.
STRIDE_S = 64
#: Registered number of scales.
N_SCALES = 64
#: Registered Fourier-period range of the scale axis, in seconds.
PERIOD_MIN_S = 2.0
PERIOD_MAX_S = 256.0
#: Morlet non-dimensional frequency (standard choice, admissible).
MORLET_OMEGA0 = 6.0
#: Sampling step of the imbalance series (1 s grid).
DT_S = 1.0
#: Floor inside the log to keep log power finite on all-zero windows.
LOG_EPS = 1e-12
#: Std floor for the per-window / per-image standardisation.
STD_EPS = 1e-12


def fourier_periods(
    n_scales: int = N_SCALES,
    period_min: float = PERIOD_MIN_S,
    period_max: float = PERIOD_MAX_S,
) -> np.ndarray:
    """The registered log-spaced Fourier-period axis (seconds), small first."""
    return np.geomspace(period_min, period_max, n_scales)


def periods_to_scales(periods: np.ndarray, omega0: float = MORLET_OMEGA0) -> np.ndarray:
    """Morlet scale ``s`` for each Fourier period ``T``.

    Torrence & Compo (1998), Table 1: ``T = 4 pi s / (omega0 +
    sqrt(2 + omega0^2))`` — inverted here.
    """
    fourier_factor = (4.0 * np.pi) / (omega0 + np.sqrt(2.0 + omega0 ** 2))
    return np.asarray(periods, dtype=np.float64) / fourier_factor


def morlet_filter_bank(
    n_fft: int,
    scales: np.ndarray,
    dt: float = DT_S,
    omega0: float = MORLET_OMEGA0,
) -> np.ndarray:
    """Frequency-domain Morlet bank, shape ``(n_scales, n_fft)`` (real).

    Analytic wavelet: non-zero on strictly positive FFT frequencies only.
    Normalisation ``sqrt(2 pi s / dt) pi^{-1/4}`` (T&C 1998 eq. 6) gives
    scale-comparable power.
    """
    omega = 2.0 * np.pi * np.fft.fftfreq(n_fft, d=dt)  # angular frequencies
    s = np.asarray(scales, dtype=np.float64)[:, None]  # (n_scales, 1)
    pos = omega > 0.0
    bank = np.zeros((s.shape[0], n_fft), dtype=np.float64)
    arg = s * omega[None, :]  # (n_scales, n_fft)
    bank[:, pos] = (
        np.sqrt(2.0 * np.pi * s / dt)
        * (np.pi ** -0.25)
        * np.exp(-0.5 * (arg[:, pos] - omega0) ** 2)
    )
    return bank


def _reflect_pad(x: np.ndarray, pad: int) -> np.ndarray:
    """Reflect-pad a batch ``(B, n)`` (or 1D) by ``pad`` samples on each side."""
    return np.pad(x, [(0, 0)] * (x.ndim - 1) + [(pad, pad)], mode="reflect")


def cwt_complex(
    x: np.ndarray,
    *,
    scales: np.ndarray | None = None,
    dt: float = DT_S,
    omega0: float = MORLET_OMEGA0,
) -> np.ndarray:
    """Complex Morlet CWT of a 1D window, shape ``(n_scales, len(x))``.

    Reflect-pads to twice the window length, transforms, keeps the central
    ``len(x)`` columns (see module docstring for the COI discussion).
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError(f"cwt_complex expects a 1D window, got shape {x.shape}")
    n = x.size
    if scales is None:
        scales = periods_to_scales(fourier_periods(), omega0)
    pad = n // 2
    xpad = _reflect_pad(x[None, :], pad)[0]
    n_fft = xpad.size
    bank = morlet_filter_bank(n_fft, scales, dt, omega0)
    xf = np.fft.fft(xpad)
    w = np.fft.ifft(xf[None, :] * bank, axis=-1)
    return w[:, pad:pad + n]


def _standardise(img: np.ndarray) -> np.ndarray:
    """Zero-mean / unit-std standardisation of one image (direction-neutral)."""
    mu = float(img.mean())
    sd = float(img.std())
    return (img - mu) / (sd + STD_EPS)


def normalise_window(x: np.ndarray) -> np.ndarray:
    """Per-window standardisation of the RAW series before the CWT.

    Mean and std are invariant under time reversal, so this removes only
    level/scale tells (which carry no arrow-of-time information) and cannot
    fabricate one.
    """
    x = np.asarray(x, dtype=np.float64)
    return (x - x.mean()) / (x.std() + STD_EPS)


def cwt_logpower(
    x: np.ndarray,
    *,
    scales: np.ndarray | None = None,
    dt: float = DT_S,
    omega0: float = MORLET_OMEGA0,
) -> np.ndarray:
    """Standardised log-power scalogram of one raw window, ``(n_scales, n)``.

    Steps (the torch batch path mirrors them 1:1): per-window standardise the
    raw series -> complex Morlet CWT (reflect pad 2x) -> ``log(|W|^2 + eps)``
    -> per-image standardisation.
    """
    w = cwt_complex(normalise_window(x), scales=scales, dt=dt, omega0=omega0)
    return _standardise(np.log(np.abs(w) ** 2 + LOG_EPS))


def scalogram_pair(
    window: np.ndarray,
    *,
    scales: np.ndarray | None = None,
    dt: float = DT_S,
    omega0: float = MORLET_OMEGA0,
) -> tuple[np.ndarray, np.ndarray]:
    """(FORWARD, TIME-REVERSED) scalogram pair for one raw window.

    THE binding construction point (registry H-16): the reversed class is
    ``cwt_logpower(window[::-1])`` — reversal on the RAW series BEFORE the
    CWT, never a flip of the finished forward image.
    """
    window = np.asarray(window, dtype=np.float64)
    fwd = cwt_logpower(window, scales=scales, dt=dt, omega0=omega0)
    rev = cwt_logpower(window[::-1], scales=scales, dt=dt, omega0=omega0)
    return fwd, rev


# ----------------------------------------------------------------------------
# Windowing
# ----------------------------------------------------------------------------


def window_starts(n: int, window: int = WINDOW_S, stride: int = STRIDE_S) -> np.ndarray:
    """Start indices of full windows over a series of length ``n``."""
    if n < window:
        return np.zeros(0, dtype=np.int64)
    return np.arange(0, n - window + 1, stride, dtype=np.int64)


def extract_windows(
    series: np.ndarray, window: int = WINDOW_S, stride: int = STRIDE_S
) -> np.ndarray:
    """All full ``(window,)`` slices at ``stride`` spacing, ``(n_win, window)``.

    Windows never cross a day boundary because the driver calls this PER DAY
    (day = registered analysis/split unit).
    """
    series = np.asarray(series, dtype=np.float64)
    starts = window_starts(series.size, window, stride)
    if starts.size == 0:
        return np.zeros((0, window), dtype=np.float64)
    return np.stack([series[s:s + window] for s in starts])


# ----------------------------------------------------------------------------
# Torch batch path (GPU) — mirrors the numpy reference step for step
# ----------------------------------------------------------------------------


def cwt_logpower_batch_torch(
    X: "torch.Tensor",
    bank: "torch.Tensor",
) -> "torch.Tensor":
    """Batched standardised log-power scalograms on a torch device.

    ``X``    : (B, n) float32/float64 raw windows (already on the device).
    ``bank`` : (n_scales, 2 n) Morlet bank from :func:`torch_filter_bank`.
    Returns (B, n_scales, n). Same steps as :func:`cwt_logpower`:
    per-window standardise -> reflect pad to 2 n -> FFT -> bank multiply ->
    iFFT -> log power -> per-image standardise.
    """
    if not _TORCH_AVAILABLE:  # pragma: no cover - guarded by callers
        raise RuntimeError("torch not available — cwt_logpower_batch_torch needs torch")
    n = X.shape[-1]
    pad = n // 2
    X = X.to(torch.float64)
    X = (X - X.mean(dim=-1, keepdim=True)) / (X.std(dim=-1, unbiased=False, keepdim=True) + STD_EPS)
    # reflect pad (B, 2n): indices mirror numpy mode="reflect"
    left = X[:, 1:pad + 1].flip(-1)
    right = X[:, -pad - 1:-1].flip(-1)
    xpad = torch.cat([left, X, right], dim=-1)
    xf = torch.fft.fft(xpad, dim=-1)  # (B, 2n) complex
    w = torch.fft.ifft(xf[:, None, :] * bank[None, :, :], dim=-1)  # (B, S, 2n)
    w = w[:, :, pad:pad + n]
    img = torch.log(w.real ** 2 + w.imag ** 2 + LOG_EPS)
    mu = img.mean(dim=(-2, -1), keepdim=True)
    sd = img.std(dim=(-2, -1), unbiased=False, keepdim=True)
    return ((img - mu) / (sd + STD_EPS)).to(torch.float32)


def torch_filter_bank(
    n: int = WINDOW_S,
    *,
    dt: float = DT_S,
    omega0: float = MORLET_OMEGA0,
    device: str = "cpu",
) -> "torch.Tensor":
    """Morlet bank for padded length ``2 n`` as a complex torch tensor."""
    if not _TORCH_AVAILABLE:  # pragma: no cover - guarded by callers
        raise RuntimeError("torch not available — torch_filter_bank needs torch")
    scales = periods_to_scales(fourier_periods(), omega0)
    bank = morlet_filter_bank(2 * n, scales, dt, omega0)
    return torch.as_tensor(bank, dtype=torch.complex128, device=device)


def verify_torch_parity(
    *, device: str = "cpu", n_windows: int = 4, seed: int = 0, atol: float = 1e-6
) -> dict[str, Any]:
    """Cross-check torch batch CWT against the numpy reference (run-start).

    Called by the driver before any verdict-bearing GPU run: the sandbox can
    only test the numpy reference, so the FIRST real run must self-verify
    that the torch path reproduces it. Returns a diagnostics dict; raises
    ``RuntimeError`` on disagreement (fail loudly, never train on a wrong
    representation).
    """
    if not _TORCH_AVAILABLE:
        return {"checked": False, "reason": "torch not available"}
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n_windows, WINDOW_S))
    ref = np.stack([cwt_logpower(x) for x in X])
    bank = torch_filter_bank(WINDOW_S, device=device)
    got = (
        cwt_logpower_batch_torch(torch.as_tensor(X, device=device), bank)
        .cpu()
        .numpy()
    )
    max_abs = float(np.max(np.abs(got.astype(np.float64) - ref)))
    if max_abs > atol:
        raise RuntimeError(
            f"torch/numpy scalogram parity FAILED on {device}: "
            f"max|diff|={max_abs:.3e} > atol={atol:.1e}"
        )
    return {"checked": True, "device": device, "max_abs_diff": max_abs, "atol": atol}


__all__ = [
    "DT_S",
    "LOG_EPS",
    "MORLET_OMEGA0",
    "N_SCALES",
    "PERIOD_MAX_S",
    "PERIOD_MIN_S",
    "STRIDE_S",
    "WINDOW_S",
    "cwt_complex",
    "cwt_logpower",
    "cwt_logpower_batch_torch",
    "extract_windows",
    "fourier_periods",
    "morlet_filter_bank",
    "normalise_window",
    "periods_to_scales",
    "scalogram_pair",
    "torch_filter_bank",
    "verify_torch_parity",
    "window_starts",
]
