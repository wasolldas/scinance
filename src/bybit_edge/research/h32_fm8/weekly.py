"""Weekly arrays of the CUT panel, window slices (P / W1 / W2) and the outcome-free K_fm8 series (ERSTFASSUNG 1.3, 1.6).

Everything here is built from an already cut panel (``panel_cut``).  The characteristics and the 8-week PIT betas are
built on the whole cut panel first and sliced afterwards (DEC-75 (8)); the lead into the pilot period is formation, not
outcome (DEC-75 (8), ERSTFASSUNG 1.3).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..wp7_universe import panel_load
from ..wp13_xsec import characteristics, nulls, prelaunch
from . import constants as C
from . import panel_cut
from .errors import KMinError, PinError

__all__ = ["Weekly", "Window", "build_weekly", "make_window", "k_alive_series", "k_fm8_series", "floor_and_v",
           "k_summary", "int_series_sha256", "check_k_min", "window_geometry_report"]


@dataclass
class Weekly:
    """Weekly arrays ``[n_weeks, n_symbols]`` of the cut panel (``panel_load`` conventions)."""
    weeks: list[str]
    symbols: list[str]
    returns: np.ndarray            # zero-filled where no return is computable (IC outcomes, characteristics)
    returns_valid: np.ndarray      # True exactly where a return was computed from two consecutive weekly closes
    returns_est: np.ndarray        # NaN where not valid (every beta / vol ESTIMATE, DEC-85 (iii))
    alive: np.ndarray              # PIT alive mask (>= 8 weeks of history, not yet delisted)
    chars: dict[str, np.ndarray]   # the four F-H32 characteristics
    beta8: np.ndarray              # 8-week PIT beta to BTCUSDT from returns_est (min_weeks = 8)
    turnover_trail: np.ndarray | None
    cut_date: str


@dataclass
class Window:
    """One window slice plus the extended (8 lead weeks + window) mask arrays the null needs."""
    name: str
    start: str
    end: str
    lo: int
    hi: int
    weeks: list[str]
    symbols: list[str]
    alive: np.ndarray
    returns: np.ndarray
    returns_est: np.ndarray
    valid: np.ndarray
    beta8: np.ndarray
    chars: dict[str, np.ndarray]
    turnover_trail: np.ndarray | None
    alive_ext: np.ndarray = field(repr=False)
    valid_ext: np.ndarray = field(repr=False)

    @property
    def n_weeks(self) -> int:
        return len(self.weeks)

    @property
    def w_judged(self) -> int:
        return nulls.w_judged_of(self.n_weeks)


def build_weekly(panel: dict[str, Any], cut_date: str, *, with_turnover: bool = True) -> Weekly:
    """Weekly arrays from the CUT daily union panel.  The maximum-date guard runs here again (independently of whoever
    cut the panel): a panel with a day after ``cut_date`` is a loud fail BEFORE any weekly return is formed."""
    panel_cut.assert_panel_max_date(panel, cut_date)
    last_alive = panel.get("last_alive_day")
    if last_alive is None:
        last_alive = [None] * len(panel["symbols"])
    weekly = panel_load.weekly_returns_and_mask_union(panel, last_alive)
    panel_cut.assert_weeks_end_by(weekly["weeks"], cut_date)
    symbols = list(panel["symbols"])
    returns = np.asarray(weekly["returns"], dtype=np.float64)
    est = nulls.estimation_returns(weekly)
    chars = {
        "mom1": characteristics.momentum_characteristic(returns, trail_win=1),
        "mom2": characteristics.momentum_characteristic(returns, trail_win=2),
        "mom4": characteristics.momentum_characteristic(returns, trail_win=4),
        "rev_gap": characteristics.reversal_gap_characteristic(returns),
    }
    beta8 = characteristics.beta_characteristic(est, symbols, market_symbol=C.MARKET_SYMBOL,
                                                trail_win=C.BETA_WINDOW_WEEKS, min_weeks=C.BETA_WINDOW_WEEKS)
    turnover_trail = None
    if with_turnover and "turnover" in panel:
        turnover_trail = characteristics.trailing_median_turnover(characteristics.weekly_turnover(panel, weekly["weeks"]))
    return Weekly(weeks=list(weekly["weeks"]), symbols=symbols, returns=returns,
                  returns_valid=np.asarray(weekly["returns_valid"], dtype=bool), returns_est=est,
                  alive=np.asarray(weekly["alive"], dtype=bool), chars=chars, beta8=beta8,
                  turnover_trail=turnover_trail, cut_date=cut_date)


def make_window(wk: Weekly, name: str, start: str | None = None, end: str | None = None, *,
                lead: int = C.LEAD_WEEKS) -> Window:
    """Slice window ``name`` (default calendar ``constants.WINDOWS``) out of ``wk``.  ``lead`` weeks in front of it
    must exist (beta lead of the null; the real beta at the first week is already built on the whole panel)."""
    s0, e0 = C.WINDOWS[name]
    start = s0 if start is None else start
    end = e0 if end is None else end
    sl = prelaunch.slice_window(wk.weeks, start, end)
    lo, hi = sl["lo"], sl["hi"]
    if lo < lead:
        raise PinError(f"window {name} starts at week index {lo} of the cut panel: fewer than the {lead} beta lead weeks "
                       "(ERSTFASSUNG 1.6) exist in front of it")
    return Window(
        name=name, start=start, end=end, lo=lo, hi=hi, weeks=list(sl["weeks"]), symbols=wk.symbols,
        alive=wk.alive[lo:hi], returns=wk.returns[lo:hi], returns_est=wk.returns_est[lo:hi],
        valid=wk.returns_valid[lo:hi], beta8=wk.beta8[lo:hi], chars={v: a[lo:hi] for v, a in wk.chars.items()},
        turnover_trail=None if wk.turnover_trail is None else wk.turnover_trail[lo:hi],
        alive_ext=wk.alive[lo - lead:hi], valid_ext=wk.returns_valid[lo - lead:hi])


def k_alive_series(win: Window) -> np.ndarray:
    """K_t = alive count of the judged formation weeks (the numbers PRD 5.3 Kill (2) and the WP-7 K series quote)."""
    return win.alive[:win.w_judged].sum(axis=1).astype(np.int64)


def k_fm8_series(win: Window) -> np.ndarray:
    """K_fm8,t (outcome-free, from ``returns_valid`` through the 8-week beta): the number of symbols in the fm8 IC of
    formation week t: alive at t, and -- if still alive at t+1 -- with a finite 8-week PIT beta (a symbol that is not
    alive at t+1 enters with outcome 0.0, ``close_at_last``)."""
    a, b = win.alive, win.beta8
    out = np.empty(win.w_judged, dtype=np.int64)
    for t in range(win.w_judged):
        out[t] = int((a[t] & (~a[t + 1] | ~np.isnan(b[t]))).sum())
    return out


def floor_and_v(k_series: np.ndarray) -> tuple[float, float]:
    """``floor = mean_t 1/sqrt(K_t - 1)`` and ``v = mean_t 1/(K_t - 1)`` (weeks with K_t >= 2)."""
    k = np.asarray(k_series, dtype=np.float64)
    ok = k >= 2.0
    if not ok.any():
        return float("nan"), float("nan")
    return float(np.mean(1.0 / np.sqrt(k[ok] - 1.0))), float(np.mean(1.0 / (k[ok] - 1.0)))


def k_summary(k_series: np.ndarray) -> dict[str, float]:
    k = np.asarray(k_series)
    return {"min": int(k.min()), "median": float(np.median(k)), "max": int(k.max())}


def int_series_sha256(series: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(np.asarray(series, dtype="<i8")).tobytes()).hexdigest()


def check_k_min(win: Window, k_min: int) -> dict[str, float]:
    """PRD 5.3 Kill (2): abort if any judged week has K_t below ``k_min`` (117 in the pilot, 134 in W1/W2)."""
    k = k_alive_series(win)
    if int(k.min()) < int(k_min):
        raise KMinError(f"window {win.name}: minimal K_t {int(k.min())} < {int(k_min)} (PRD 5.3 Kill (2)) -- abort")
    return k_summary(k)


def window_geometry_report(win: Window) -> dict[str, Any]:
    """Outcome-free description of the window (week labels and counts only)."""
    return {"start": win.start, "end": win.end, "n_weeks": win.n_weeks, "w_judged": win.w_judged,
            "first_formation_week": win.weeks[0], "last_formation_week": win.weeks[win.w_judged - 1],
            "first_outcome_week": win.weeks[1], "last_outcome_week": win.weeks[-1]}
