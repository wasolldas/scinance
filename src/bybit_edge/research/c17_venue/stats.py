"""Statistics helpers for the H-17 venue-fingerprint gate (KAPITALFREI).

Own Benjamini-Hochberg copy for the F-VENUE family (registry §8.2
convention: each research package keeps its own copy; no cross-import
between research packages). Plus balanced accuracy (the registered gate
metric), the add-one empirical p convention, Spearman rho (own copy, for
the pre-registered non-redundancy gate against c12_frag) and the
within-group label permutation primitive of the registered null.

KAPITALFREI: pure statistics. No friction, bps, PnL, Sharpe.
"""
from __future__ import annotations

import numpy as np

#: BH-FDR level for the F-VENUE family (registry H-17).
FDR_ALPHA = 0.10


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i``
    is significant at FDR ``alpha`` and ``p_crit`` the largest passing
    p-value (0.0 if none). Input order preserved. OWN copy (registry §8.2).
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


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean per-class recall (the registered H-17 gate metric)."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if y_true.size == 0 or y_true.shape != y_pred.shape:
        raise ValueError("balanced_accuracy needs equal-length non-empty arrays")
    recalls: list[float] = []
    for c in np.unique(y_true):
        sel = y_true == c
        recalls.append(float(np.mean(y_pred[sel] == c)))
    return float(np.mean(recalls))


def empirical_p_ge(null_stats: np.ndarray, observed: float) -> float:
    """One-sided add-one empirical p: (#{null >= observed} + 1) / (n + 1)."""
    stats = np.asarray(null_stats, dtype=np.float64)
    stats = stats[np.isfinite(stats)]
    if stats.size == 0 or not np.isfinite(observed):
        return 1.0
    n_ge = int(np.sum(stats >= observed))
    return float((n_ge + 1) / (stats.size + 1))


def _rankdata_average(v: np.ndarray) -> np.ndarray:
    """Average ranks (own copy — no cross-import from features)."""
    v = np.asarray(v, dtype=np.float64)
    n = v.size
    order = np.argsort(v, kind="mergesort")
    sv = v[order]
    inv = np.empty(n, dtype=np.int64)
    inv[order] = np.arange(n)
    obs = np.concatenate(([True], sv[1:] != sv[:-1]))
    dense = np.cumsum(obs)[inv]
    bounds = np.concatenate((np.nonzero(obs)[0], [n]))
    return 0.5 * (bounds[dense - 1] + bounds[dense] + 1).astype(np.float64)


def spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation (average ranks + Pearson on ranks). Own copy.

    Used by the pre-registered non-redundancy gate against the c12_frag
    daily lambda2/IPR series (registry H-17). NaN if degenerate (constant
    series or < 2 points).
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.size != y.size or x.size < 2:
        return float("nan")
    rx = _rankdata_average(x)
    ry = _rankdata_average(y)
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    denom = float(np.sqrt(np.sum(rx ** 2) * np.sum(ry ** 2)))
    if denom <= 0.0 or not np.isfinite(denom):
        return float("nan")
    return float(np.sum(rx * ry) / denom)


def permute_within_groups(
    labels: np.ndarray, groups: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Permute ``labels`` independently WITHIN each group (registered null).

    Registry H-17: Within-Symbol-Within-Day-Label-Permutation — ``groups``
    are the (symbol, UTC day) cell ids of the TRAIN windows; the venue
    labels are shuffled only inside each cell, so per-cell label counts
    (and thus any symbol/day composition effect) are exactly preserved.
    """
    labels = np.asarray(labels)
    groups = np.asarray(groups)
    if labels.shape != groups.shape:
        raise ValueError("labels/groups shape mismatch")
    out = labels.copy()
    for g in np.unique(groups):
        sel = np.nonzero(groups == g)[0]
        out[sel] = labels[sel[rng.permutation(sel.size)]]
    return out


__all__ = [
    "FDR_ALPHA",
    "balanced_accuracy",
    "benjamini_hochberg",
    "empirical_p_ge",
    "permute_within_groups",
    "spearman_rho",
]
