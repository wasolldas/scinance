"""Batched Shannon Transfer Entropy for the H-18 resolution audit.

Numerically replicates ``c17_c41_lead_lag.transfer_entropy.transfer_entropy``
(same quantile discretisation via double stable argsort, same index alignment,
same plug-in estimator, same guards) but evaluates a whole BATCH of source
series against one target in a single vectorised pass:

* joint 3D histograms as one batched ``bincount`` (numpy) / ``scatter_add``
  (torch) over flat per-row-offset indices — the registry-named GPU pattern,
* the TE sum as a masked vectorised reduction over the ``(B, b, b, b)`` cube.

The ONLY tolerated deviation from the serial original is floating-point
summation order (pairwise vs. sequential over <= b**3 = 27 cells), i.e.
~1e-16-level differences; the self-test/unit tests bound this explicitly.

KAPITALFREI: pure directed-information measurement, no tradability logic.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bybit_edge.research.c17_c41_lead_lag.transfer_entropy import DEFAULT_N_BINS

from .surrogate_gpu import backend_device, batch_circular_shift, generate_shift_offsets


def _quantise_rows_np(x2d: np.ndarray, n_bins: int) -> np.ndarray:
    """Row-wise equal-frequency quantisation, identical to the original
    ``_quantise`` (double STABLE argsort ranks -> ``int(q * n_bins)``)."""
    n = x2d.shape[1]
    if n == 0:
        return np.zeros_like(x2d, dtype=np.int64)
    ranks = np.argsort(np.argsort(x2d, axis=1, kind="stable"), axis=1, kind="stable")
    q = ranks / max(1, n - 1)
    return np.clip((q * n_bins).astype(np.int64), 0, n_bins - 1)


def _quantise_rows_torch(x2d, n_bins: int, torch):
    n = x2d.shape[1]
    if n == 0:
        return torch.zeros_like(x2d, dtype=torch.int64)
    ranks = torch.argsort(torch.argsort(x2d, dim=1, stable=True), dim=1, stable=True)
    q = ranks.to(torch.float64) / max(1, n - 1)
    return torch.clamp((q * n_bins).to(torch.int64), 0, n_bins - 1)


def transfer_entropy_batch(
    src_batch,
    target: np.ndarray,
    lag: int,
    *,
    n_bins: int = DEFAULT_N_BINS,
    backend: str = "numpy",
) -> np.ndarray:
    """TE ``source_i -> target`` for every row of ``src_batch`` at once.

    ``src_batch``: ``(B, n)`` float array (numpy array or torch tensor already
    on the backend device); ``target``: ``(n,)``. Returns a ``(B,)`` float64
    NUMPY array of TE values in bits (the caller-facing contract is numpy on
    every backend). Guards identical to the original: ``lag < 1`` or
    ``n < lag + 8`` or effective sample ``m < 8`` -> 0.0 for the whole batch.
    """
    target = np.asarray(target, dtype=np.float64)
    if backend == "numpy":
        src_batch = np.asarray(src_batch, dtype=np.float64)
        n = min(src_batch.shape[1], target.size)
    else:
        n = min(int(src_batch.shape[1]), target.size)
    b_rows = int(src_batch.shape[0])
    if lag < 1 or n < lag + 8:
        return np.zeros(b_rows, dtype=np.float64)
    m = n - lag  # == len(target[lag:n]) == len(source[0:n-lag])
    if m < 8:
        return np.zeros(b_rows, dtype=np.float64)
    b = int(n_bins)
    b3 = b * b * b

    if backend == "numpy":
        s_codes = _quantise_rows_np(src_batch[:, :n], b)
        t_code = _quantise_rows_np(target[None, :n], b)[0]
        t_next = t_code[lag:n]                # target[k+1]
        t_now = t_code[lag - 1 : n - 1]      # target[k]
        s_past = s_codes[:, 0 : n - lag]      # source[k+1-lag], per row
        joint_idx = (t_next[None, :] * b + t_now[None, :]) * b + s_past  # (B, m)
        flat = (np.arange(b_rows, dtype=np.int64)[:, None] * b3 + joint_idx).ravel()
        counts = np.bincount(flat, minlength=b_rows * b3).astype(np.float64)
        p_joint = counts.reshape(b_rows, b, b, b) / float(m)
        p_now_past = p_joint.sum(axis=1)          # (B, b_now, b_past)
        p_next_now = p_joint.sum(axis=3)          # (B, b_next, b_now)
        p_now = p_joint.sum(axis=(1, 3))          # (B, b_now)
        num = p_joint * p_now[:, None, :, None]
        den = p_next_now[:, :, :, None] * p_now_past[:, None, :, :]
        mask = (p_joint > 0) & (num > 0) & (den > 0)
        ratio = np.where(mask, num / np.where(mask, den, 1.0), 1.0)
        contrib = np.where(mask, p_joint * np.log2(ratio), 0.0)
        te = contrib.sum(axis=(1, 2, 3))
        return np.maximum(te, 0.0)

    torch, device = backend_device(backend)
    src_t = src_batch if not isinstance(src_batch, np.ndarray) else torch.as_tensor(
        src_batch, dtype=torch.float64, device=device
    )
    tgt_t = torch.as_tensor(target[:n], dtype=torch.float64, device=device)
    s_codes = _quantise_rows_torch(src_t[:, :n], b, torch)
    t_code = _quantise_rows_torch(tgt_t[None, :], b, torch)[0]
    t_next = t_code[lag:n]
    t_now = t_code[lag - 1 : n - 1]
    s_past = s_codes[:, 0 : n - lag]
    joint_idx = (t_next[None, :] * b + t_now[None, :]) * b + s_past
    flat = (
        torch.arange(b_rows, dtype=torch.int64, device=device)[:, None] * b3 + joint_idx
    ).reshape(-1)
    counts = torch.zeros(b_rows * b3, dtype=torch.float64, device=device)
    counts.scatter_add_(0, flat, torch.ones_like(flat, dtype=torch.float64))
    p_joint = counts.reshape(b_rows, b, b, b) / float(m)
    p_now_past = p_joint.sum(dim=1)
    p_next_now = p_joint.sum(dim=3)
    p_now = p_joint.sum(dim=(1, 3))
    num = p_joint * p_now[:, None, :, None]
    den = p_next_now[:, :, :, None] * p_now_past[:, None, :, :]
    mask = (p_joint > 0) & (num > 0) & (den > 0)
    one = torch.ones((), dtype=torch.float64, device=device)
    ratio = torch.where(mask, num / torch.where(mask, den, one), one)
    contrib = torch.where(mask, p_joint * torch.log2(ratio), torch.zeros_like(p_joint))
    te = contrib.sum(dim=(1, 2, 3))
    return torch.clamp(te, min=0.0).cpu().numpy()


@dataclass(slots=True)
class BatchedSurrogateResult:
    """Same fields/serialisation as the original ``SurrogateResult``."""

    axis: str
    lag: int
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


def surrogate_test_te_batched(
    source: np.ndarray,
    target: np.ndarray,
    lag: int,
    *,
    n_bins: int,
    n_surrogates: int,
    seed: int,
    backend: str = "numpy",
    chunk_size: int = 8192,
) -> BatchedSurrogateResult:
    """Batched replica of the original ``surrogate_test_te``.

    Identical null (circular shift, identical RNG consumption — see
    ``generate_shift_offsets``), identical guards, identical p-value
    ``(#{surrogate >= observed} + 1) / (N + 1)``; the surrogate ensemble is
    evaluated in ``chunk_size`` batches (VRAM/RAM bound), which changes
    nothing statistically.
    """
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    n = min(source.size, target.size)
    if n < lag + 16:
        return BatchedSurrogateResult("TE", lag, 0.0, np.zeros(0), 1.0, 0)
    source, target = source[:n], target[:n]
    observed = float(transfer_entropy_batch(source[None, :], target, lag, n_bins=n_bins, backend=backend)[0])

    offsets = generate_shift_offsets(n, n_surrogates, seed)
    stats = np.empty(n_surrogates, dtype=np.float64)
    for k0 in range(0, n_surrogates, max(1, int(chunk_size))):
        k1 = min(n_surrogates, k0 + max(1, int(chunk_size)))
        shifted = batch_circular_shift(source, offsets[k0:k1], backend=backend)
        stats[k0:k1] = transfer_entropy_batch(shifted, target, lag, n_bins=n_bins, backend=backend)
    n_ge = int(np.sum(stats >= observed))
    p_value = (n_ge + 1) / (n_surrogates + 1)
    return BatchedSurrogateResult("TE", lag, observed, stats, p_value, n_surrogates)
