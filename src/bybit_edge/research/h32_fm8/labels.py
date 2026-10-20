"""Report-only labels on window arrays (never a gate input): liquidity sensitivity of the fm8 statistic (ERSTFASSUNG 2,
"Etiketten"; DEC-74 (f)) -- the mean fm8 IC without bucket 1 of the trailing-8-week median turnover and on buckets 3..10.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from ..wp13_xsec import characteristics
from . import constants as C
from . import fm8
from .weekly import Window

__all__ = ["liquidity_masks", "liquidity_means"]


def liquidity_masks(win: Window, *, min_universe: int = 10) -> dict[str, np.ndarray]:
    """Alive masks restricted by the PIT turnover decile: ``without_b1`` (bucket 1 excluded) and ``b3_10`` (buckets 3..10).
    A week below ``min_universe`` keeps its full mask (the IC of such a week is NaN anyway)."""
    if win.turnover_trail is None:
        raise ValueError("window carries no turnover (liquidity label needs panel['turnover'])")
    wo1 = win.alive.copy()
    b310 = win.alive.copy()
    for t in range(win.n_weeks):
        m = win.alive[t]
        if int(m.sum()) < min_universe:
            continue
        b = characteristics.decile_bucket(win.turnover_trail[t], m)
        wo1[t] = m & (b != 1)
        b310[t] = m & (b >= 3)
    return {"without_b1": wo1, "b3_10": b310}


def liquidity_means(win: Window, variant: str, sign: int) -> dict[str, Any]:
    """Window mean (direction ``y``) of the fm8 IC of ``variant`` without bucket 1 and on buckets 3..10."""
    masks = liquidity_masks(win)
    out: dict[str, Any] = {}
    for name, m in masks.items():
        res = fm8.fm8_weekly_ic(win.chars[variant], win.returns, m, win.beta8, win.symbols, weeks=win.weeks,
                                bounds=fm8.outcome_bounds(win.name))
        out[f"y_{name}"] = float(sign) * res["mean_ic"] if np.isfinite(res["mean_ic"]) else float("nan")
        out[f"n_weeks_{name}"] = int(res["n_weeks_used"])
    return out
