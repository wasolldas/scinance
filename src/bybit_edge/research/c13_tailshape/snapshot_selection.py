"""Deterministic D1/D2 snapshot-day search for H-13 (unlock condition).

Registry H-13 (pre-registered, threshold NEVER lowered): the hypothesis is
LOCKED until the live feed contains two snapshot days D1 < D2 with
  (i)   |log(RV_5d(D1) / RV_5d(D2))| >= log(1.5)   (vol-regime disjoint),
  (ii)  >= 10 calendar days between D1 and D2,
  (iii) >= 12 strikes inside the delta band 0.01 <= |delta| <= 0.5 in the
        20-45 DTE tenor on each day.

Deterministic choice (no cherry-picking): D1 = EARLIEST day satisfying (iii);
D2 = EARLIEST later day satisfying (i)+(ii)+(iii) against that D1. The search
runs PROGRAMMATICALLY over all available snapshot dates; if the condition is
not met the result reports ``found=False`` with a reason — never an exception.

RV_5d definition (fixed here, documented in README_H13): root-mean-square of
the 1-min log-returns over the 5 calendar days strictly before the snapshot
day (scaling cancels in the ratio).
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .options_loader import MIN_STRIKES, list_snapshot_dates, load_smile
from .returns_tail import DataError, load_returns_window

#: Unlock condition constants (registry H-13, non-negotiable).
LOG_RV_RATIO_MIN = math.log(1.5)
MIN_GAP_DAYS = 10
RV_WINDOW_DAYS = 5


@dataclass(slots=True)
class DayInfo:
    """Per-snapshot-day diagnostics feeding the deterministic selection."""

    date: str
    n_strikes: int
    rv_5d: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "n_strikes": int(self.n_strikes),
            "rv_5d": float(self.rv_5d) if math.isfinite(self.rv_5d) else None,
        }


@dataclass(slots=True)
class SelectionResult:
    """Outcome of the D1/D2 search for one symbol (never raises)."""

    found: bool
    d1: str | None = None
    d2: str | None = None
    reason: str = ""
    day_infos: list[DayInfo] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "found": bool(self.found),
            "d1": self.d1,
            "d2": self.d2,
            "reason": self.reason,
            "days_scanned": [d.as_dict() for d in self.day_infos],
        }


def _gap_days(d1: str, d2: str) -> int:
    from datetime import date

    a = date(*(int(x) for x in d1.split("-")))
    b = date(*(int(x) for x in d2.split("-")))
    return (b - a).days


def select_days(
    day_infos: list[DayInfo],
    *,
    min_strikes: int = MIN_STRIKES,
    min_gap_days: int = MIN_GAP_DAYS,
    log_rv_ratio_min: float = LOG_RV_RATIO_MIN,
) -> SelectionResult:
    """Pure deterministic D1/D2 selection over per-day diagnostics.

    D1 = earliest day with ``n_strikes >= min_strikes`` and a finite positive
    RV_5d. D2 = earliest LATER day with (i) |log(RV(D1)/RV(D2))| >=
    ``log_rv_ratio_min``, (ii) gap >= ``min_gap_days`` calendar days, (iii)
    ``n_strikes >= min_strikes`` (and finite positive RV). Reports cleanly
    when no such pair exists.
    """
    infos = sorted(day_infos, key=lambda d: d.date)
    ok = [
        d for d in infos
        if d.n_strikes >= min_strikes and math.isfinite(d.rv_5d) and d.rv_5d > 0
    ]
    if not ok:
        return SelectionResult(
            found=False, day_infos=infos,
            reason=f"no snapshot day with >= {min_strikes} strikes in the "
                   f"delta band (and a measurable RV_5d)",
        )
    d1 = ok[0]
    for cand in ok[1:]:
        if _gap_days(d1.date, cand.date) < min_gap_days:
            continue
        if abs(math.log(d1.rv_5d / cand.rv_5d)) < log_rv_ratio_min:
            continue
        return SelectionResult(found=True, d1=d1.date, d2=cand.date, day_infos=infos)
    return SelectionResult(
        found=False, d1=d1.date, day_infos=infos,
        reason=f"D1={d1.date} found, but no later day with gap >= "
               f"{min_gap_days} d AND |log RV ratio| >= {log_rv_ratio_min:.4f} "
               f"AND >= {min_strikes} strikes",
    )


def scan_and_select(
    base_dir: Path | str,
    option_symbol: str,
    perp_symbol: str,
    *,
    min_strikes: int = MIN_STRIKES,
    min_gap_days: int = MIN_GAP_DAYS,
    log_rv_ratio_min: float = LOG_RV_RATIO_MIN,
    rv_window_days: int = RV_WINDOW_DAYS,
    snapshot_hour: int = 8,
) -> SelectionResult:
    """IO wrapper: scan the harvester tree and run :func:`select_days`.

    For every available ``markprice.options`` snapshot date of
    ``option_symbol``: count the tenor/delta-filtered strikes (via the smile
    builder) and compute RV_5d from the trailing 1-min Bybit returns of
    ``perp_symbol``. Days where either side fails to load get n_strikes = 0 /
    RV = NaN and are thereby excluded — the scan itself never raises.
    """
    dates = list_snapshot_dates(base_dir, option_symbol)
    infos: list[DayInfo] = []
    for d in dates:
        smile = load_smile(base_dir, option_symbol, d, snapshot_hour=snapshot_hour)
        n_strikes = smile.n_strikes if smile is not None else 0
        rv = float("nan")
        try:
            r, _meta = load_returns_window(
                base_dir, perp_symbol, d,
                n_days=rv_window_days, min_days=max(2, rv_window_days - 2),
            )
            rv = float(np.sqrt(np.mean(r * r))) if r.size else float("nan")
        except DataError as exc:
            print(f"[h13] RV_5d {perp_symbol}@{d}: {exc}", file=sys.stderr, flush=True)
        infos.append(DayInfo(date=d, n_strikes=n_strikes, rv_5d=rv))
    if not infos:
        return SelectionResult(
            found=False,
            reason=f"no markprice.options snapshot dates for {option_symbol}",
        )
    return select_days(
        infos, min_strikes=min_strikes, min_gap_days=min_gap_days,
        log_rv_ratio_min=log_rv_ratio_min,
    )
