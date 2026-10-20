"""The H-32 primary statistic: the weekly fm8 IC series of one window and variant (ERSTFASSUNG 1.4).

Exactly ``ic.apply_beta_control("fm_neutral_8w", ...)`` followed by ``ic.weekly_ic_series(..., "close_at_last")`` -- the
IC_res of the third version H-28..H-30.  This is the ONLY place of the driver that sets a characteristic against an
outcome on real windows; it is monkeypatch-observable (it calls ``ic.weekly_ic_series``) and carries the seal guard
(PP4/P7): the outcome weeks of the slice (``weeks[1:]``) must lie inside the allowed outcome range.  No raw IC, no lag
profile and no beta-calibration IC exist in this package.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..wp13_xsec import ic
from . import constants as C
from .errors import SealError

__all__ = ["guard_outcome_weeks", "fm8_weekly_ic", "window_ic", "mean_finite", "outcome_bounds"]


def outcome_bounds(window_name: str) -> tuple[str, str]:
    """Allowed (first, last) outcome-week start of the window (ERSTFASSUNG 1.3)."""
    if window_name == "P":
        return C.PILOT_OUTCOME_FIRST, C.PILOT_OUTCOME_LAST
    return C.TEST_OUTCOME_FIRST[window_name], C.TEST_OUTCOME_LAST[window_name]


def guard_outcome_weeks(weeks: list[str], first: str, last: str) -> None:
    """Seal guard: ``weeks[1:]`` are the outcome weeks that ``ic.weekly_ic_series`` sets against the characteristics of
    ``weeks[:-1]``; none may lie outside ``[first, last]`` (week-start strings)."""
    if len(weeks) < 2:
        raise SealError("window with fewer than two weeks")
    if weeks[1] < first or weeks[-1] > last:
        raise SealError(f"outcome weeks {weeks[1]}..{weeks[-1]} reach outside the allowed range {first}..{last} -- no IC")


def fm8_weekly_ic(char: np.ndarray, returns: np.ndarray, alive: np.ndarray, beta8: np.ndarray, symbols: list[str], *,
                  weeks: list[str] | None = None, bounds: tuple[str, str] | None = None) -> dict[str, Any]:
    """fm8 weekly IC series of one characteristic on window arrays (``[n_weeks, n_symbols]``).  Returns
    ``ic.weekly_ic_series``' dict.  If ``weeks`` and ``bounds`` are given the seal guard runs first."""
    if weeks is not None and bounds is not None:
        guard_outcome_weeks(weeks, *bounds)
    applied = ic.apply_beta_control(C.PRIMARY_STATISTIC, char, returns, alive, beta_pit=beta8, symbols=symbols,
                                    market_symbol=C.MARKET_SYMBOL)
    return ic.weekly_ic_series(applied["characteristic"], applied["returns"], alive, convention=C.CONVENTION)


def window_ic(win, variant: str, *, alive: np.ndarray | None = None) -> dict[str, Any]:
    """fm8 IC series of ``variant`` on window ``win`` (``weekly.Window``).  Result adds ``ic_weekly`` (list of floats,
    NaN where K < 10) and ``k_weekly`` (K of every judged week)."""
    res = fm8_weekly_ic(win.chars[variant], win.returns, win.alive if alive is None else alive, win.beta8, win.symbols,
                        weeks=win.weeks, bounds=outcome_bounds(win.name))
    res = dict(res)
    res["ic_weekly"] = [float(w["ic"]) for w in res["weekly"]]
    res["k_weekly"] = [int(w["k"]) for w in res["weekly"]]
    return res


def mean_finite(values: np.ndarray | list[float]) -> float:
    a = np.asarray(values, dtype=np.float64)
    a = a[np.isfinite(a)]
    return float(a.mean()) if a.size else float("nan")


def sd_finite(values: np.ndarray | list[float]) -> float:
    a = np.asarray(values, dtype=np.float64)
    a = a[np.isfinite(a)]
    return float(a.std(ddof=1)) if a.size > 1 else float("nan")


def _is_nan(x: float) -> bool:
    return isinstance(x, float) and math.isnan(x)
