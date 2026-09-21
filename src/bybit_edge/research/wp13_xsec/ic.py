"""WP-13 -- the ONE Spearman-IC entry point (PRD 5.3, DEC-74), PURE.

**THE SEAL (task brief, verbatim).** ``--prelaunch`` must NEVER compute a
real-characteristic-vs-real-next-week-outcome IC. This is enforced
STRUCTURALLY, not by convention: :func:`weekly_ic_series` is the single
function in this whole package that ever calls
``pit_universe.spearman_rank_ic`` on a per-week cross-section, and it
takes ``returns`` (the outcome source) as an EXPLICIT argument -- nothing
here reaches into a module-level "the real panel" global. ``prelaunch.py``
therefore only ever calls this function with a SIMULATED returns array
(the persistence null, ``nulls.py``) or FIXTURE data; it is
monkeypatch-observable (``tests/unit/test_wp13_xsec.py``'s two SEAL tests
wrap this exact function and assert, by object identity / SHA-256 of the
value bytes, that no call's ``returns`` argument is the real union
panel's weekly-return matrix).

**Delisting conventions (PRD 4.1 DoD (4), DEC-74 (i)).**
  - ``"drop"``: pair ``(t, t+1)`` requires ``alive[t] & alive[t+1]`` -- a
    symbol delisted between the two weeks contributes nothing that week
    (the estimator ``wp7_universe.pit_universe.momentum_ic_series`` /
    ``weekly_ic_series`` already use).
  - ``"close_at_last"``: the URTEILSTRAGEND convention for H-28/H-29/H-30
    (DEC-74 (i)). Pair requires only ``alive[t]``; if the symbol is ALSO
    alive at ``t+1`` its outcome is the real ``returns[t+1]`` as usual, but
    if it is alive at ``t`` and NOT at ``t+1`` (i.e. week ``t`` IS its
    delisting week) its outcome is exactly ``0.0`` and it STAYS in the
    cross-section -- "zum letzten Schlusskurs geschlossen" (PRD 4.1 DoD
    (4)): the position is closed at the last traded price, realising
    neither a further gain nor the naive "-100%" loss the PRD explicitly
    rejects. ``n_affected`` counts these symbol-weeks per week.

**Cross-sectional outcome demeaning (DEC-39 adversarial default).** PRD
5.3's adversarial fixture is "ein Faktor, der mechanisch mit dem
Markt-Beta korreliert ... auf einem Panel mit dominantem Marktfaktor" --
in crypto, "practically everything is beta to BTC" (PRD 5.3, verbatim).
Demeaning each week's outcome cross-sectionally (subtracting that week's
mean return over the SAME alive set the IC is computed on) before ranking
removes exactly that common market-timing component, so a
market-beta-correlated characteristic scores an IC near zero instead of
picking up the market's own mean return as a spurious cross-sectional
signal. This is the DEFAULT (``demean_outcome=True``) for every caller in
this package, not an opt-in -- Gate (2)'s Querschnitts-Permutations-Null
and every DEC-39 fixture in the test suite rely on it being on by
default.
"""
from __future__ import annotations

from typing import Any, Literal

import numpy as np

from ..wp7_universe.pit_universe import spearman_rank_ic

__all__ = [
    "DELISTING_CONVENTIONS", "weekly_ic_series", "mean_ic", "vol_weighted_outcome_with_drag",
]

DELISTING_CONVENTIONS: tuple[str, ...] = ("drop", "close_at_last")

Convention = Literal["drop", "close_at_last"]


def weekly_ic_series(
    characteristic: np.ndarray, returns: np.ndarray, alive: np.ndarray, *,
    convention: Convention = "drop", demean_outcome: bool = True, min_universe: int = 10,
) -> dict[str, Any]:
    """Per-week Spearman IC of ``characteristic[t]`` (any of
    ``characteristics.py``'s 7 variants, or a fixture/simulated array of
    the same shape) against week ``t+1``'s outcome, drawn from
    ``returns`` under ``convention`` -- see module docstring. Returns
    ``{"weekly": [...], "mean_ic": float, "k_series": [...],
    "n_affected_series": [...], "convention": ..., "demean_outcome": ...}``;
    ``mean_ic`` is the plain mean (not weighted) of the per-week IC values
    with ``K_t >= min_universe`` (NaN entries excluded -- a week below
    ``min_universe`` simply does not enter the mean, same discipline as
    ``pit_universe.weekly_ic_series``).
    """
    if convention not in DELISTING_CONVENTIONS:
        raise ValueError(f"convention must be one of {DELISTING_CONVENTIONS}, got {convention!r}")
    n_weeks, n_symbols = returns.shape
    weekly: list[dict[str, Any]] = []
    for t in range(n_weeks - 1):
        alive_t = alive[t]
        if convention == "drop":
            mask = alive_t & alive[t + 1]
            outcome_row = returns[t + 1]
            n_affected = 0
        else:  # close_at_last
            mask = alive_t
            outcome_row = np.where(alive[t + 1], returns[t + 1], 0.0)
            n_affected = int((alive_t & ~alive[t + 1]).sum())
        k = int(mask.sum())
        if k < min_universe:
            weekly.append({"t": t, "ic": float("nan"), "k": k, "n_affected": n_affected})
            continue
        char_vals = characteristic[t, mask]
        out_vals = outcome_row[mask]
        valid = ~np.isnan(char_vals) & ~np.isnan(out_vals)
        k_valid = int(valid.sum())
        if k_valid < min_universe:
            weekly.append({"t": t, "ic": float("nan"), "k": k_valid, "n_affected": n_affected})
            continue
        char_vals = char_vals[valid]
        out_vals = out_vals[valid]
        if demean_outcome:
            out_vals = out_vals - out_vals.mean()
        ic_val = spearman_rank_ic(char_vals, out_vals)
        weekly.append({"t": t, "ic": ic_val, "k": k_valid, "n_affected": n_affected})

    ic_arr = np.array([w["ic"] for w in weekly], dtype=np.float64)
    finite = ic_arr[~np.isnan(ic_arr)]
    mean = float(finite.mean()) if finite.size else float("nan")
    return {
        "weekly": weekly, "mean_ic": mean, "n_weeks_used": int(finite.size),
        "k_series": [w["k"] for w in weekly], "n_affected_series": [w["n_affected"] for w in weekly],
        "convention": convention, "demean_outcome": demean_outcome, "min_universe": min_universe,
    }


def mean_ic(characteristic: np.ndarray, returns: np.ndarray, alive: np.ndarray, **kwargs: Any) -> float:
    """Convenience wrapper: just the window mean IC from
    :func:`weekly_ic_series`."""
    return weekly_ic_series(characteristic, returns, alive, **kwargs)["mean_ic"]


def vol_weighted_outcome_with_drag(
    returns: np.ndarray, weekly_vol: np.ndarray, *, target_vol: float | None = None, floor: float = 1e-8,
) -> dict[str, Any]:
    """PRD 5.3 A3-V's mandatory (i)/(ii) construction: each symbol-week's
    return is scaled by ``target_vol / weekly_vol`` (risk-parity-style
    inverse-vol weighting, capping every leg's contributed variance at the
    same ``target_vol``), and the analytic vol-drag term
    ``E[r_arith] - E[r_geom] = sigma^2/2`` (PRD 5.3, verbatim) is returned
    alongside it -- BOTH the raw per-symbol-week drag (``sigma_j^2/2``,
    what the position would carry UNWEIGHTED) and the drag AFTER
    vol-weighting (``target_vol^2/2`` for every leg, since vol-weighting
    normalises every leg's realised vol to the SAME ``target_vol`` --
    documented here as ``prelaunch.py``'s ``Drag_rest`` computation
    verbatim, PRD 5.3 (ii)/(iii)). ``target_vol`` defaults to the
    CROSS-SECTIONAL MEDIAN of ``weekly_vol`` over its finite entries (a
    single scalar, not per-week -- the simplest defensible "normalise to a
    common risk budget" choice; the caller may override it).

    Returns ``{"weighted_returns", "weight", "drag_raw", "drag_after_weighting",
    "target_vol"}``, all ``[n_weeks, n_symbols]`` except ``target_vol``
    (scalar). NaN propagates from ``weekly_vol``'s own NaNs (a
    symbol-week with no measurable vol gets no weight, no drag)."""
    finite_vol = weekly_vol[~np.isnan(weekly_vol)]
    if target_vol is None:
        target_vol = float(np.median(finite_vol)) if finite_vol.size else float("nan")
    safe_vol = np.where(np.isnan(weekly_vol), np.nan, np.maximum(weekly_vol, floor))
    weight = target_vol / safe_vol
    weighted_returns = returns * weight
    drag_raw = 0.5 * weekly_vol ** 2
    drag_after_weighting = np.where(np.isnan(weekly_vol), np.nan, 0.5 * target_vol ** 2)
    return {
        "weighted_returns": weighted_returns, "weight": weight,
        "drag_raw": drag_raw, "drag_after_weighting": drag_after_weighting,
        "target_vol": target_vol,
    }
