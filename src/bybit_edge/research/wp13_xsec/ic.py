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
**DEC-77 Entscheidung 1 (b) / Vorlauf v4 -- beta-control METHODS, pure.**
Nine methods total (:data:`BETA_CONTROL_METHODS`, ``"none"`` = the raw
reference plus eight beta-controlled variants), dispatched by
:func:`apply_beta_control` -- the SINGLE entry point both the calibration
simulation (``nulls.beta_controlled_factor_null``) and the real run
(``run.py``'s ``variant_window_payload``) call, so a method behaves
IDENTICALLY whether it is being calibrated on a simulated panel or applied
to the real one:

  - ``ts_resid_{8,13,26}w`` -- time-series residualisation (DEC-75 (3)'s
    ``residualize_outcome``, generalised from its old fixed 8-week window):
    ``r_i - beta_i^{Nw,PIT} * r_BTC``. :func:`residualize_outcome` itself is
    UNCHANGED (still just ``returns - beta*r_btc``); only the ``N`` the PIT
    beta is estimated over varies.
  - ``fm_neutral_{8,13,26}w`` -- Fama-MacBeth: EVERY outcome week ``t+1``,
    an OLS cross-sectional regression of that week's realised return on
    the PIT beta known as of week ``t`` (:func:`fm_neutralize_outcome`);
    the residual of THAT regression (not a fixed-loading subtraction) is
    the beta-neutralised outcome. Structurally orthogonal to beta BY
    CONSTRUCTION (OLS residuals sum to zero against their own regressor),
    so this method needs no fixed assumption about what the realised
    market factor return "was" that week.
  - ``double_sort_{13,26}w`` -- neutralises the CHARACTERISTIC, not the
    outcome (:func:`double_sort_characteristic`): each week, symbols are
    bucketed into beta quintiles (equal-count, ascending beta), and the
    characteristic is RE-RANKED within its own quintile only; the outcome
    stays the raw next-week return. A characteristic that is a pure proxy
    for beta gets an (approximately) flat within-quintile rank everywhere,
    same effect as the outcome-side methods, from the other direction.
  - ``"none"`` -- pure passthrough, the raw (uncontrolled) reference.

Every method with a trailing window (all but ``"none"``) requires the PIT
beta array to have been estimated with ``min_weeks = trail_win`` (DEC-77
item 2(i): "exclude symbols with fewer than the window's weeks") -- a
symbol-week without a FULL ``N``-week trailing history gets NaN, never a
partial-window estimate; :func:`trailing_beta_coverage` reports what
fraction of alive symbol-weeks that leaves.
"""
from __future__ import annotations

from typing import Any, Literal

import numpy as np

from ..wp7_universe.pit_universe import spearman_rank_ic

__all__ = [
    "DELISTING_CONVENTIONS", "weekly_ic_series", "mean_ic", "vol_weighted_outcome_with_drag",
    "residualize_outcome", "BETA_CONTROL_METHODS", "beta_control_trail_weeks",
    "trailing_beta_coverage", "fm_neutralize_outcome", "double_sort_characteristic",
    "apply_beta_control",
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
    returns: np.ndarray, weekly_vol: np.ndarray, *, weight_source: str = "pit",
    target_vol: float | None = None, floor: float = 1e-8,
) -> dict[str, Any]:
    """DEC-75 Entscheidung 1 (4) / task brief item 4 -- H-30, corrected
    (v2) construction (Review B-5/B-6 fixes, verbatim):

      B-6 fix: ``weekly_vol[t]`` is the FORMATION week's realised vol
      (``characteristics.realized_vol_characteristic``'s ``vol_rv[t]``,
      known PIT by week ``t``'s end) and it now weights
      ``returns[t+1]`` -- the NEXT week's outcome -- not
      ``returns[t]`` paired with the same row index (the v1 bug B-6
      names explicitly: "Helfer nutzt Zeilenindex des Outcomes").
      B-5 fix: the drag term ``sigma_w[t]^2/2`` is subtracted from the
      UNWEIGHTED outcome ``returns[t+1]`` FIRST, and only THEN is the
      (drag-adjusted) outcome scaled by the weight -- so the reported
      drag is heterogeneous ACROSS symbol-weeks again (``sigma_w[t]`` is
      the formation week's own vol, not the post-weighting constant
      ``target_vol`` every leg shares -- v1's bug B-5, verbatim:
      "target_vol^2/2 ist rangneutral (misst nichts)").

    Formally, for formation week ``t`` (``t in [0, n_weeks-2]``):
      ``weight[t]   = target_vol / max(weekly_vol[t], floor)``
      ``drag[t]     = 0.5 * weekly_vol[t]**2``               (log-return units)
      ``weighted_outcome[t] = (returns[t+1] - drag[t]) * weight[t]``
    ``weight_source`` MUST be the literal string ``"pit"`` (C.14 loud
    fail, DEC-75: the task brief explicitly requires this so a future
    caller can never silently swap in a non-PIT vol source -- e.g. the
    OUTCOME week's own realised vol, which would leak the outcome into
    its own weight). ``target_vol`` defaults to the CROSS-SECTIONAL
    MEDIAN of ``weekly_vol`` over its finite entries (unchanged from v1).

    Returns ``{"weighted_outcome", "weight", "drag", "target_vol",
    "weight_source"}`` all shaped ``[n_weeks, n_symbols]`` (row ``t`` =
    formation week ``t``'s weighted, drag-adjusted view of week ``t+1``'s
    outcome; the LAST row is NaN -- no ``t+1`` inside the array) except
    ``target_vol`` (scalar). Units: weekly LOG return throughout (NOT
    basis points -- callers that want bp multiply by 1e4 themselves, same
    convention as ``characteristics.realized_vol_characteristic``'s
    output). NaN propagates from ``weekly_vol``'s own NaNs and from
    ``returns[t+1]``'s own NaNs."""
    if weight_source != "pit":
        raise ValueError(f"weight_source must be the literal 'pit' (C.14 loud fail), got {weight_source!r}")
    finite_vol = weekly_vol[~np.isnan(weekly_vol)]
    if target_vol is None:
        target_vol = float(np.median(finite_vol)) if finite_vol.size else float("nan")
    n_weeks, n_symbols = returns.shape
    safe_vol = np.where(np.isnan(weekly_vol), np.nan, np.maximum(weekly_vol, floor))
    weight_full = target_vol / safe_vol
    drag_full = 0.5 * weekly_vol ** 2

    weighted_outcome = np.full((n_weeks, n_symbols), np.nan, dtype=np.float64)
    weight = np.full((n_weeks, n_symbols), np.nan, dtype=np.float64)
    drag = np.full((n_weeks, n_symbols), np.nan, dtype=np.float64)
    for t in range(n_weeks - 1):
        weight[t] = weight_full[t]
        drag[t] = drag_full[t]
        weighted_outcome[t] = (returns[t + 1] - drag_full[t]) * weight_full[t]

    return {
        "weighted_outcome": weighted_outcome, "weight": weight, "drag": drag,
        "target_vol": target_vol, "weight_source": weight_source,
        "note": "Einheit: woechentliche Log-Rendite; weighted_outcome[t] gehoert zu Woche t+1's "
                "Outcome, gewichtet mit Formationswoche t's PIT-Vol (DEC-75 (4)).",
    }


def residualize_outcome(returns: np.ndarray, beta_8w_pit: np.ndarray, r_btc: np.ndarray) -> np.ndarray:
    """DEC-75 Entscheidung 1 (3) / task brief item 6: market-residualised
    outcome, ``r_i - beta_i^{8W,PIT} * r_BTC`` -- ``beta_8w_pit`` is
    ``characteristics.beta_characteristic``'s TRAILING-8-week PIT beta
    (already computed elsewhere in this package, reused unchanged here,
    never recomputed), ``r_btc`` is BTCUSDT's own weekly-return COLUMN
    (``[n_weeks]``, e.g. ``returns[:, symbols.index('BTCUSDT')]``). Pure
    function, no I/O; ``returns``/``beta_8w_pit`` are ``[n_weeks,
    n_symbols]``, broadcasting ``r_btc`` over the symbol axis. NaN
    propagates from either input (a symbol-week with no trailing beta yet
    gets no residual)."""
    return returns - beta_8w_pit * r_btc[:, None]


# ----------------------------------------------------------------------------
# DEC-77 Entscheidung 1 (b) / Vorlauf v4 -- beta-control METHODS
# ----------------------------------------------------------------------------

#: The K=9 beta-control method cohort ("none" = raw reference).
BETA_CONTROL_METHODS: tuple[str, ...] = (
    "none",
    "ts_resid_8w", "ts_resid_13w", "ts_resid_26w",
    "fm_neutral_8w", "fm_neutral_13w", "fm_neutral_26w",
    "double_sort_13w", "double_sort_26w",
)

_BETA_CONTROL_TRAIL_WEEKS: dict[str, int | None] = {
    "none": None,
    "ts_resid_8w": 8, "ts_resid_13w": 13, "ts_resid_26w": 26,
    "fm_neutral_8w": 8, "fm_neutral_13w": 13, "fm_neutral_26w": 26,
    "double_sort_13w": 13, "double_sort_26w": 26,
}


def beta_control_trail_weeks(method: str) -> int | None:
    """The trailing PIT-beta window (weeks) a :data:`BETA_CONTROL_METHODS`
    name implies -- ``None`` for ``"none"`` (no beta control at all). C.14
    loud fail (:class:`ValueError`) on an unrecognised name -- never a
    silent ``None``/default fallback, since a mistyped method name must
    never quietly become "no beta control"."""
    if method not in _BETA_CONTROL_TRAIL_WEEKS:
        raise ValueError(f"unknown beta_control method {method!r} -- expected one of {BETA_CONTROL_METHODS}")
    return _BETA_CONTROL_TRAIL_WEEKS[method]


def trailing_beta_coverage(beta_pit: np.ndarray, alive: np.ndarray) -> dict[str, Any]:
    """DEC-77 item 2(i): the fraction of ALIVE symbol-weeks that carry a
    finite PIT beta at ``beta_pit``'s trailing window -- the "exclude
    symbols with fewer than the window's weeks; report coverage"
    requirement, as a plain descriptive ratio (never a gate input by
    itself)."""
    denom = int(alive.sum())
    numer = int((alive & ~np.isnan(beta_pit)).sum())
    return {"n_alive_symbol_weeks": denom, "n_covered_symbol_weeks": numer,
            "coverage_fraction": (numer / denom) if denom else float("nan")}


def fm_neutralize_outcome(returns: np.ndarray, beta_pit: np.ndarray, alive: np.ndarray, *,
                           min_universe: int = 5) -> np.ndarray:
    """DEC-77 item 2(ii): Fama-MacBeth beta-neutralised outcome. For every
    outcome week ``t+1`` (``t in [0, n_weeks-2]``), an OLS cross-sectional
    regression (intercept + slope) of ``returns[t+1]`` on the PIT beta
    known as of week ``t`` (``beta_pit[t]``) is fit over the symbols alive
    at BOTH ``t`` and ``t+1`` with a finite beta and outcome (at least
    ``min_universe``, else that week's row stays all-NaN -- an
    under-powered week's cross-section is worse than an honest gap, same
    discipline as :func:`weekly_ic_series`'s own ``min_universe``); the
    residual (``y - (intercept + slope*x)``) REPLACES ``returns[t+1]`` for
    those symbols. Returned array is ``returns``-shaped, ready for
    :func:`weekly_ic_series` (row ``t+1`` = that week's neutralised
    outcome, EXACTLY :func:`residualize_outcome`'s output convention --
    the delisting-convention handling (``"drop"``/``"close_at_last"``)
    still happens downstream, in ``weekly_ic_series`` itself, on whatever
    value lands here; a delisted symbol's ``close_at_last`` 0.0 outcome is
    substituted there regardless of this function's own value at that
    position). Structurally orthogonal to ``beta_pit[t]`` BY CONSTRUCTION:
    an OLS residual has EXACTLY zero (Pearson) correlation with its own
    regressor, to floating-point precision -- the "FM residuals have zero
    cross-sectional correlation with beta" property DEC-77 item 6 asks for
    a test of.
    """
    n_weeks, n_symbols = returns.shape
    resid = np.full_like(returns, np.nan)
    for t in range(n_weeks - 1):
        mask = alive[t] & alive[t + 1] & ~np.isnan(beta_pit[t]) & ~np.isnan(returns[t + 1])
        k = int(mask.sum())
        if k < min_universe:
            continue
        x = beta_pit[t, mask]
        y = returns[t + 1, mask]
        x_c = x - x.mean()
        var_x = float(np.dot(x_c, x_c))
        if var_x <= 0.0:
            continue
        slope = float(np.dot(x_c, y - y.mean()) / var_x)
        intercept = float(y.mean() - slope * x.mean())
        resid[t + 1, mask] = y - (intercept + slope * x)
    return resid


def double_sort_characteristic(characteristic: np.ndarray, beta_pit: np.ndarray, alive: np.ndarray, *,
                                n_quintiles: int = 5) -> np.ndarray:
    """DEC-77 item 2(iii): the characteristic, RE-RANKED WITHIN its own
    beta quintile each week (outcome stays raw -- the caller hands this
    output, not a residualised ``returns`` array, to
    :func:`weekly_ic_series`). Per week ``t``: symbols alive with a finite
    ``beta_pit[t]`` and ``characteristic[t]`` are sorted ascending by beta
    and split into ``n_quintiles`` equal(-ish) buckets (same
    "``(n*q)//n_quintiles``" split :func:`characteristics.decile_bucket`
    already uses, generalised from 10 buckets to ``n_quintiles``); WITHIN
    each bucket, the characteristic values are converted to plain ranks
    ``1..bucket_size`` (ties broken by stable sort order, matching
    :func:`characteristics.decile_bucket`'s ``mergesort`` discipline) --
    so the OUTPUT for every week is, bucket by bucket, an exact
    PERMUTATION of ``1..bucket_size`` (DEC-77 item 6's "double-sort ranks
    are within-quintile permutations" property). A week with fewer than
    ``n_quintiles`` valid symbols is skipped entirely (NaN row -- no
    meaningful quintile split possible)."""
    n_weeks, n_symbols = characteristic.shape
    out = np.full_like(characteristic, np.nan)
    for t in range(n_weeks):
        mask = alive[t] & ~np.isnan(beta_pit[t]) & ~np.isnan(characteristic[t])
        idx = np.flatnonzero(mask)
        n = idx.size
        if n < n_quintiles:
            continue
        beta_vals = beta_pit[t, idx]
        order = idx[np.argsort(beta_vals, kind="mergesort")]
        for q in range(n_quintiles):
            lo, hi = (n * q) // n_quintiles, (n * (q + 1)) // n_quintiles
            members = order[lo:hi]
            if members.size == 0:
                continue
            vals = characteristic[t, members]
            ranks = np.argsort(np.argsort(vals, kind="mergesort"), kind="mergesort").astype(np.float64) + 1.0
            out[t, members] = ranks
    return out


def apply_beta_control(
    method: str, characteristic: np.ndarray, returns: np.ndarray, alive: np.ndarray, *,
    beta_pit: np.ndarray | None = None, symbols: list[str] | None = None,
    market_symbol: str = "BTCUSDT", min_universe: int = 5,
) -> dict[str, Any]:
    """DEC-77 item 2, THE single dispatcher every caller (calibration
    simulation AND real run) uses for ONE :data:`BETA_CONTROL_METHODS`
    name -- returns ``{"characteristic", "returns", "coverage"}`` ready to
    hand straight to :func:`weekly_ic_series` (``"none"`` is a pure
    passthrough, ``coverage=None``). C.14 loud fail on an unrecognised
    method (via :func:`beta_control_trail_weeks`) or a missing
    ``beta_pit``/``symbols`` a non-``"none"`` method needs -- NEVER a
    silent fallback to raw/uncontrolled. ``beta_pit`` must already be the
    CORRECT trailing-window PIT beta for ``method`` (computed with
    ``min_weeks = beta_control_trail_weeks(method)`` -- the caller's job,
    so this function can stay a cheap dispatcher, reusable per-replicate
    inside a simulation loop without recomputing beta from scratch for
    every method that happens to share a window)."""
    trail_win = beta_control_trail_weeks(method)     # raises on an unknown method name
    if method == "none":
        return {"characteristic": characteristic, "returns": returns, "coverage": None}
    if beta_pit is None:
        raise ValueError(f"apply_beta_control({method!r}) requires a precomputed beta_pit array "
                          f"(trail_win={trail_win}, min_weeks={trail_win})")
    coverage = trailing_beta_coverage(beta_pit, alive)
    if method.startswith("ts_resid_"):
        if symbols is None or market_symbol not in symbols:
            raise ValueError(f"apply_beta_control({method!r}) requires symbols containing {market_symbol!r}")
        r_btc = returns[:, symbols.index(market_symbol)]
        resid_returns = residualize_outcome(returns, beta_pit, r_btc)
        return {"characteristic": characteristic, "returns": resid_returns, "coverage": coverage}
    if method.startswith("fm_neutral_"):
        resid_returns = fm_neutralize_outcome(returns, beta_pit, alive, min_universe=min_universe)
        return {"characteristic": characteristic, "returns": resid_returns, "coverage": coverage}
    if method.startswith("double_sort_"):
        ds_char = double_sort_characteristic(characteristic, beta_pit, alive)
        return {"characteristic": ds_char, "returns": returns, "coverage": coverage}
    raise AssertionError(f"unhandled beta_control method {method!r}")  # unreachable: BETA_CONTROL_METHODS is exhaustive
