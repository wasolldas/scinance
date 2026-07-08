"""Statistics helpers for the H-12 mess-gate (KAPITALFREI).

Provides the OWN Benjamini-Hochberg copy for the F-FRAG family (registry
§8.2 convention: each research package keeps its own copy; no cross-import
between research packages).

KAPITALFREI: pure statistics. No friction, bps, PnL, Sharpe.
"""
from __future__ import annotations

#: BH-FDR level for the F-FRAG family (registry H-12).
FDR_ALPHA = 0.10


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i``
    is significant at FDR ``alpha`` and ``p_crit`` the largest passing p-value
    (0.0 if none). Input order preserved. OWN copy (registry §8.2 convention —
    each research package keeps its own; no cross-import between packages).
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


__all__ = ["FDR_ALPHA", "benjamini_hochberg"]
