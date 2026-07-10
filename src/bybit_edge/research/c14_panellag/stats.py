"""Statistics helpers for the H-14 PANEL-LAG gate (KAPITALFREI).

Provides the OWN Benjamini-Hochberg copy for the F-PANELLAG family (registry
paragraph 8.2 convention: each research package keeps its own copy; no
cross-import between research packages) plus the null-delta construction for
the retrain-ablation statistic.

Null-delta construction (builder-fixed BEFORE any real run; the registry
fixes ~100 all-surrogate retrainings per window and the 95th-percentile /
BH-FDR thresholds but not the pairing): under the per-edge null, the
observed T(j->i) = L_ablate_j(i) - L_full(i) is the difference of the OOS
losses of TWO independently retrained models whose cross-node inputs carry
no usable information about target i beyond retrain noise. The ~100
all-surrogate null retrainings provide i.i.d. draws of exactly such losses;
the null distribution of the DELTA per target i is therefore formed as ALL
ORDERED PAIR differences ``L_null_k(i) - L_null_k'(i)`` (k != k'), which is
symmetric around 0 by construction, needs no arbitrary centering choice and
mirrors the observed statistic's form. With 100 retrainings this yields
9900 null deltas per target — enough tail resolution for the BH-FDR family
(smallest attainable add-one p ~= 1/9901, well under alpha/m ~= 5e-4 for
the ~198-test family). Documented in README_H14.md.

KAPITALFREI: pure statistics. No friction, bps, PnL, Sharpe.
"""
from __future__ import annotations

import numpy as np

#: BH-FDR level for the F-PANELLAG family (registry H-14).
FDR_ALPHA = 0.10

#: Registered null-percentile criterion (registry H-14: 95. Perzentil).
NULL_PERCENTILE = 95.0


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i``
    is significant at FDR ``alpha`` and ``p_crit`` the largest passing p-value
    (0.0 if none). Input order preserved. OWN copy (registry paragraph 8.2
    convention — each research package keeps its own; no cross-import).
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


def paired_null_deltas(null_losses: np.ndarray) -> np.ndarray:
    """All ordered pair differences of the null-retrain losses for ONE target.

    ``null_losses``: (n_null,) OOS log-losses of the all-surrogate null
    retrainings on one target node. Returns (n_null * (n_null - 1),) deltas
    ``L_k - L_k'`` for k != k' (symmetric around 0 by construction).
    """
    x = np.asarray(null_losses, dtype=np.float64)
    n = x.size
    if n < 2:
        raise ValueError(f"need >= 2 null retrainings, got {n}")
    diff = x[:, None] - x[None, :]
    mask = ~np.eye(n, dtype=bool)
    return diff[mask]


def empirical_p_ge(null_values: np.ndarray, observed: float) -> float:
    """Add-one empirical p-value P(null >= observed)."""
    x = np.asarray(null_values, dtype=np.float64)
    return float((1 + int(np.sum(x >= observed))) / (1 + x.size))


def null_q95(null_values: np.ndarray, q: float = NULL_PERCENTILE) -> float:
    """Registered 95th-percentile threshold of the null-delta distribution."""
    return float(np.percentile(np.asarray(null_values, dtype=np.float64), q))


__all__ = [
    "FDR_ALPHA",
    "NULL_PERCENTILE",
    "benjamini_hochberg",
    "empirical_p_ge",
    "null_q95",
    "paired_null_deltas",
]
