"""Hard panel cut (DEC-96 E3, DEC-99 (3)/(8), Review B-6): the daily data are cut at the cut date BEFORE weekly returns,
characteristics, betas, calibrations or nulls are built.

Why a cut and not only an outcome-week guard: the characteristics and the 8-week betas are built on the whole panel
(DEC-75 (8)); a panel that reaches to the as-of date of the export would let BTC returns of the blind period (from
2026-07-01) enter the beta estimates even if no outcome is ever printed.  The cut makes that impossible by
construction; :func:`assert_panel_max_date` is the guard (loud fail) that the modes call themselves, so that a
mis-wired or patched cut cannot go unnoticed.

The fingerprint check of the registration is done on the FILES before this function (the cut changes the arrays, not the
files); the cut itself is outcome-free.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np

from . import constants as C
from .errors import PanelCutError

__all__ = ["cut_panel_days", "assert_panel_max_date", "assert_weeks_end_by", "check_cut_date"]

#: keys of the union panel dict whose first axis is the day axis.
_DAY_LIST_KEYS = ("dates", "day_index")
_DAY_ARRAY_KEYS = ("close", "turnover", "funding_n", "funding_sum")
#: keys aligned with the symbol axis (columns).
_SYMBOL_ARRAY_KEYS = ("close", "turnover", "funding_n", "funding_sum")


def check_cut_date(cut_date: str, *, limit: str | None = None) -> date:
    """The cut date must be an ISO date, a Sunday (the last day of a complete cluster unit, DEC-99 (1)) and not later than
    ``limit`` (the blind seal of DEC-96 E3 begins on the day after ``constants.CUT_TEST``)."""
    try:
        d = date.fromisoformat(str(cut_date))
    except ValueError as exc:
        raise PanelCutError(f"cut date {cut_date!r} is not an ISO date") from exc
    if d.isoformat() != str(cut_date):
        raise PanelCutError(f"cut date {cut_date!r} is not in canonical ISO form")
    if d.isoweekday() != 7:
        raise PanelCutError(f"cut date {cut_date} is not a Sunday: the last week would be an incomplete cluster unit (DEC-99 (1))")
    if limit is not None and cut_date > limit:
        raise PanelCutError(f"cut date {cut_date} lies after the allowed limit {limit} (blind seal DEC-96 E3 / DEC-99 (8))")
    return d


def cut_panel_days(panel: dict[str, Any], cut_date: str, *, limit: str | None = None,
                   drop_empty_symbols: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    """Cut the daily union panel at ``cut_date`` (inclusive).  Returns ``(cut_panel, report)``.

    * every day after the cut disappears from ``dates``/``day_index``/``close``/``turnover``/``funding_*``;
    * a symbol without any finite close up to the cut (listed later) is dropped (``drop_empty_symbols``) so that the
      result equals a panel that ends at the cut;
    * a ``last_alive_day`` after the cut is replaced by ``None`` (the symbol is alive at the cut) and a relisting day after
      the cut by the first day after the cut -- no date beyond the cut survives in the returned dict;
    * the report counts what was removed (numbers only, no post-cut value).
    """
    check_cut_date(cut_date, limit=limit)
    dates = [str(d) for d in panel["dates"]]
    keep = np.array([d <= cut_date for d in dates], dtype=bool)
    n_before = len(dates)
    n_after = int(keep.sum())
    if n_after == 0:
        raise PanelCutError(f"the panel has no day on or before the cut date {cut_date}")
    out: dict[str, Any] = dict(panel)
    for k in _DAY_LIST_KEYS:
        if k in panel:
            out[k] = [v for v, flag in zip(panel[k], keep) if flag]
    for k in _DAY_ARRAY_KEYS:
        if k in panel:
            out[k] = np.ascontiguousarray(np.asarray(panel[k])[keep])
    symbols = list(panel["symbols"])
    has_data = np.isfinite(out["close"]).any(axis=0)
    n_sym_before = len(symbols)
    if drop_empty_symbols and not bool(has_data.all()):
        cols = np.flatnonzero(has_data)
        for k in _SYMBOL_ARRAY_KEYS:
            if k in out:
                out[k] = np.ascontiguousarray(out[k][:, cols])
        out["symbols"] = [symbols[j] for j in cols]
        if "is_delisted" in panel:
            out["is_delisted"] = np.asarray(panel["is_delisted"])[cols]
        if "last_alive_day" in panel:
            out["last_alive_day"] = [panel["last_alive_day"][j] for j in cols]
        kept = set(out["symbols"])
        if "delisted_symbols" in panel:
            out["delisted_symbols"] = [s for s in panel["delisted_symbols"] if s in kept]
    n_nulled = 0
    if "last_alive_day" in out:
        lad = list(out["last_alive_day"])
        for j, v in enumerate(lad):
            if v is not None and str(v) > cut_date:
                lad[j] = None
                n_nulled += 1
        out["last_alive_day"] = lad
    if "relisted_gaps" in out:
        gaps = {}
        first_after = (date.fromisoformat(cut_date) + timedelta(days=1)).isoformat()
        kept_syms = set(out["symbols"])
        for s, g in (panel.get("relisted_gaps") or {}).items():
            if s not in kept_syms or str(g.get("delist_date")) > cut_date:
                continue
            g2 = dict(g)
            if str(g2.get("relist_first_day")) > cut_date:
                g2["relist_first_day"] = first_after
            gaps[s] = g2
        out["relisted_gaps"] = gaps
    if "n_symbols_survivors" in out and "is_delisted" in out:
        n_del = int(np.asarray(out["is_delisted"]).sum())
        out["n_symbols_delisted"] = n_del
        out["n_symbols_survivors"] = len(out["symbols"]) - n_del
    report = {
        "cut_date": cut_date, "n_days_before_cut": n_after, "n_days_removed": n_before - n_after,
        "max_date": out["dates"][-1], "n_symbols_in": n_sym_before, "n_symbols_out": len(out["symbols"]),
        "n_symbols_dropped_without_data": n_sym_before - len(out["symbols"]),
        "n_last_alive_day_nulled": n_nulled,
    }
    return out, report


def assert_panel_max_date(panel: dict[str, Any], cut_date: str) -> str:
    """Guard (loud fail): no day after ``cut_date`` is present.  Returns the maximum date."""
    dates = panel.get("dates")
    if not dates:
        raise PanelCutError("the panel has no dates")
    mx = max(str(d) for d in dates)
    if mx > cut_date:
        raise PanelCutError(
            f"panel not cut: the maximum date {mx} lies after the cut date {cut_date} (DEC-96 E3 / DEC-99 (3)) -- "
            "no calculation on this panel")
    return mx


def assert_weeks_end_by(weeks: list[str], cut_date: str) -> None:
    """Guard on the weekly grid: the last week (start + 6 days) ends on or before the cut date."""
    last = date.fromisoformat(weeks[-1]) + timedelta(days=6)
    if last.isoformat() > cut_date:
        raise PanelCutError(f"week {weeks[-1]} ends {last.isoformat()}, after the cut date {cut_date}")
