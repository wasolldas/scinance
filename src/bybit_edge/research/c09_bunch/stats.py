"""BH-FDR for the F-BUNCH family (H-09). Own copy per §8.2 convention.

The F-BUNCH family is registered as 5 symbols x 2 windows (order level) = 10
tests, BH-FDR alpha = 0.10 (registry H-09). Identical contract to the C-31 /
C-17 / C-01 / C-06 implementations — each research package keeps its OWN copy
of the FDR helper, no cross-import between research packages.
"""
from __future__ import annotations

from .kinks import FDR_ALPHA

__all__ = ["FDR_ALPHA", "benjamini_hochberg"]


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i`` is
    significant at FDR ``alpha`` and ``p_crit`` the largest passing p-value
    (0.0 if none). Input order preserved. Identical contract to the C-31 / C-17 /
    C-01 implementations (registry §8.2 convention; each research package keeps
    its own copy — no cross-import between research packages).
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
