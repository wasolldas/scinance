"""IAAFT surrogates for the H-16 pipeline-leak control (registry, mandatory).

IAAFT = Iterative Amplitude Adjusted Fourier Transform (Schreiber & Schmitz
1996, "Improved surrogate data for nonlinearity tests", PRL 77(4)). The
surrogate preserves BOTH the amplitude spectrum (|FFT|, i.e. the linear
autocorrelation structure) and the marginal value distribution of the
original series while randomising the Fourier phases. A stationary linear
Gaussian process under a static monotone transform — which is exactly what
the surrogate emulates — is TIME-REVERSIBLE (Weiss 1975), so the registered
Bayes-null AUC = 0.5 holds for it and any classifier AUC materially above
0.5 on surrogates exposes a PIPELINE LEAK (label/feature leakage, edge
artefacts, augmentation asymmetry), not market structure. Registry H-16
gate: same pipeline on IAAFT surrogates MUST stay at held-out AUC <= 0.52,
else the run is METHODICALLY INVALID (no verdict — a distinct state, not a
DROP; the driver marks it as such).

Algorithm (exact, not approximated):
  0.  target amplitudes A_k = |rfft(x)|; sorted original values v.
  1.  s <- random permutation of x.
  2.  repeat: (i) SPECTRUM step: keep phases of rfft(s), impose A_k, irfft;
      (ii) AMPLITUDE step: rank-remap the result onto v.
  3.  stop when the rank permutation is unchanged (fixed point) or after
      ``max_iter`` iterations.
Ending on the AMPLITUDE step (default) makes the marginal distribution
EXACT and the spectrum approximate (relative error reported and typically
< a few percent after convergence); ``end="spectrum"`` makes the spectrum
exact instead. The unit tests verify both invariants explicitly.

KAPITALFREI: pure surrogate construction. numpy only.
"""
from __future__ import annotations

from typing import Any

import numpy as np

#: Default iteration cap (Schreiber & Schmitz converge in O(10..100) iters).
MAX_ITER = 200


def _spectrum_rel_err(s: np.ndarray, target_amp: np.ndarray) -> float:
    """Relative RMS error between |rfft(s)| and the target amplitudes."""
    amp = np.abs(np.fft.rfft(s))
    denom = float(np.linalg.norm(target_amp))
    if denom <= 0.0:
        return 0.0
    return float(np.linalg.norm(amp - target_amp) / denom)


def iaaft(
    x: np.ndarray,
    rng: np.random.Generator,
    *,
    max_iter: int = MAX_ITER,
    end: str = "amplitude",
) -> tuple[np.ndarray, dict[str, Any]]:
    """One IAAFT surrogate of the 1D series ``x``.

    Parameters
    ----------
    x        : 1D series (e.g. one UTC day of the 1 s signed imbalance).
    rng      : numpy Generator — drives ONLY the initial permutation
               (the iteration itself is deterministic given it).
    max_iter : iteration cap.
    end      : ``"amplitude"`` (exact marginal, default) or ``"spectrum"``
               (exact amplitude spectrum).

    Returns ``(surrogate, info)`` with info keys ``n_iter``, ``converged``
    (rank fixed point reached), ``spectrum_rel_err`` (relative RMS |FFT|
    error of the returned surrogate) and ``end``.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError(f"iaaft expects a 1D series, got shape {x.shape}")
    if end not in ("amplitude", "spectrum"):
        raise ValueError(f"end must be 'amplitude' or 'spectrum', got {end!r}")
    n = x.size
    if n < 4 or np.ptp(x) == 0.0:
        # Degenerate series: nothing to randomise, return a copy (honest no-op).
        return x.copy(), {
            "n_iter": 0, "converged": True,
            "spectrum_rel_err": 0.0, "end": end,
        }

    target_amp = np.abs(np.fft.rfft(x))
    sorted_vals = np.sort(x)
    s = rng.permutation(x)

    prev_ranks: np.ndarray | None = None
    converged = False
    it = 0
    for it in range(1, max_iter + 1):
        # (i) spectrum step: impose target amplitudes, keep current phases.
        f = np.fft.rfft(s)
        phases = np.angle(f)
        s = np.fft.irfft(target_amp * np.exp(1j * phases), n=n)
        # (ii) amplitude step: rank-remap onto the original values.
        ranks = np.argsort(np.argsort(s, kind="stable"), kind="stable")
        s = sorted_vals[ranks]
        if prev_ranks is not None and np.array_equal(ranks, prev_ranks):
            converged = True
            break
        prev_ranks = ranks

    if end == "spectrum":
        f = np.fft.rfft(s)
        s = np.fft.irfft(target_amp * np.exp(1j * np.angle(f)), n=n)

    return s, {
        "n_iter": it,
        "converged": bool(converged),
        "spectrum_rel_err": _spectrum_rel_err(s, target_amp),
        "end": end,
    }


__all__ = ["MAX_ITER", "iaaft"]
