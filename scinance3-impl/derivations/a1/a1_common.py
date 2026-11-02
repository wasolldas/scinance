"""A1 (H-31) derivation -- shared loader and constants.

Loads the union panel (panel_1d + panel_1d_delisted) READ-ONLY via the repo's
own loader (``wp7_universe.panel_load``), truncates the DAILY data at
``LAST_DAY_USED`` (2026-06-28: no day after the last judged W2 formation week
is ever touched -- the weeks after 2026-06-30 stay completely unused, the week
2026-06-29 is dropped as well because it is only a holding week), and builds the
weekly grid, PIT alive mask and the DEC-67 E2 sort key (weekly SUM of F - I).

Outcome blindness (task rule 1): this module only builds raw panel arrays. Any
A1 OUTCOME (holding-week price leg, holding-week funding leg, total return,
key -> next-week correlation of a funding sort) is computed exclusively in
``a1_nuisance.py`` and only for holding weeks that END on or before
``NUISANCE_END`` (2024-06-30); ``assert_nuisance_holding_week`` is the guard.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, "/home/user/scinance/src")

import numpy as np  # noqa: E402

from bybit_edge.research.wp7_universe import panel_load, pit_universe  # noqa: E402

PANEL_BASE = Path("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/panel/panel_1d")
DELISTED_BASE = Path("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/panel/panel_1d_delisted")
WORK = Path("/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a1_herleitung")
OUT = Path("/home/user/scinance/scinance3-impl/state/herleitung_a1")

AS_OF = date(2026, 9, 28)          # as_of of the v5e load (same Harvest export, DEC-84)
YEAR_START, YEAR_END = 2021, 2026  # CLI default start year of scripts/wp13_xsec.py
LAST_DAY_USED = "2026-06-28"       # last day of the last judged W2 formation week (2026-06-22)

# Windows (PRD 5.1, DEC-70). Formation weeks are ISO week starts; a formation week t is
# JUDGED in a window iff t and t+1 both lie in the window (W_judged = n_weeks - 1, DEC-75 (1)).
WINDOWS = {
    "W1": ("2024-07-01", "2025-06-30"),
    "W2": ("2025-07-01", "2026-06-30"),
}
# Nuisance period (task rule 1): outcome-side DISPERSION quantities only, holding weeks
# ending <= 2024-06-30. First formation week 2021-03-01.
NUISANCE_START = "2021-03-01"
NUISANCE_END = "2024-06-30"

#: DEC-67 E3 / DEC-70: D1 degenerate if the strictly negative share of the week's universe < 0.10
DEGENERACY_SHARE = 0.10
KEY_TOL = 1e-12                    # same tol as panel_load.decile_degeneration_weekly

#: Configuration B (DEC-58 E3 reading): exclude a symbol-week from the formation universe when the
#: FORMATION week t has at least one 1h funding day (funding_n == 24) -- look-ahead-free, decided on
#: week-t data only. Set by the environment variable A1_EXCL1H=1; every output file then carries the
#: suffix "_excl1h".
EXCL_1H = os.environ.get("A1_EXCL1H") == "1"
SUFFIX = "_excl1h" if EXCL_1H else ""


def _sha256_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def truncate_daily(panel: dict[str, Any], last_day: str) -> dict[str, Any]:
    """Drop every daily row after ``last_day`` (ISO). Returns a shallow copy."""
    keep = [i for i, d in enumerate(panel["dates"]) if d <= last_day]
    out = dict(panel)
    out["dates"] = [panel["dates"][i] for i in keep]
    out["day_index"] = [panel["day_index"][i] for i in keep]
    for k in ("close", "turnover", "funding_n", "funding_sum"):
        out[k] = panel[k][keep, :]
    return out


def load() -> dict[str, Any]:
    """Union panel -> dict with daily panel (truncated), weekly grid, alive mask, key."""
    manifest = PANEL_BASE / "panel_manifest.sqlite"
    dmanifest = DELISTED_BASE / "panel_manifest.sqlite"
    ddates = DELISTED_BASE / "delisting_dates.json"
    symbols = panel_load.load_panel_symbols(manifest)
    panel_full = panel_load.load_panel_union(
        PANEL_BASE, manifest, DELISTED_BASE, dmanifest, year_start=YEAR_START, year_end=YEAR_END,
        as_of=AS_OF, delisting_dates_path=ddates, symbols=symbols, allow_partial=True)
    fp = panel_load.union_range_fingerprint(
        PANEL_BASE, DELISTED_BASE, [s for s, d in zip(panel_full["symbols"], panel_full["is_delisted"]) if not d],
        list(panel_full["delisted_symbols"]), year_start=YEAR_START, year_end=YEAR_END, as_of=AS_OF)
    panel = truncate_daily(panel_full, LAST_DAY_USED)
    weekly = panel_load.weekly_returns_and_mask_union(panel, panel["last_alive_day"])
    fx = panel_load.funding_excess_weekly(panel, weekly["weeks"])
    # weekly SUM of raw F (for the funding leg) and of the interest term I, per symbol-week
    weeks = weekly["weeks"]
    week_pos = {w: i for i, w in enumerate(weeks)}
    n_w, n_s = len(weeks), len(panel["symbols"])
    fn, fs = panel["funding_n"], panel["funding_sum"]
    has_f = ~np.isnan(fn) & (fn > 0) & ~np.isnan(fs)
    f_sum_w = np.zeros((n_w, n_s))
    n_pay_w = np.zeros((n_w, n_s))
    # interval-class day counts per symbol-week (funding_n 24/12/6/3 -> 1h/2h/4h/8h, else "mixed")
    cls_days = {c: np.zeros((n_w, n_s), dtype=np.int64) for c in ("1h", "2h", "4h", "8h", "other")}
    fn_map = {24: "1h", 12: "2h", 6: "4h", 3: "8h"}
    fn_int = np.where(has_f, np.round(np.nan_to_num(fn)), -1).astype(np.int64)
    zero_mean_day = has_f & (np.abs(np.where(has_f, fs, 0.0)) < 1e-15)
    zero_days_w = np.zeros((n_w, n_s), dtype=np.int64)
    for i, d in enumerate(panel["dates"]):
        wk = pit_universe.iso_week_start(date.fromisoformat(d)).isoformat()
        wi = week_pos.get(wk)
        if wi is None:
            continue
        f_sum_w[wi] += np.where(has_f[i], fs[i], 0.0)
        n_pay_w[wi] += np.where(has_f[i], fn[i], 0.0)
        row = fn_int[i]
        for v, c in fn_map.items():
            cls_days[c][wi] += (row == v)
        cls_days["other"][wi] += has_f[i] & ~np.isin(row, list(fn_map))
        zero_days_w[wi] += zero_mean_day[i]
    sym = panel["symbols"]
    return {
        "panel": panel, "weekly": weekly, "weeks": weeks, "symbols": sym,
        "is_delisted": np.asarray(panel["is_delisted"], dtype=bool),
        "alive": weekly["alive"], "returns": weekly["returns"], "returns_valid": weekly["returns_valid"],
        "key": fx["key"], "n_days_with_funding": fx["n_days_with_funding"],
        "f_sum_w": f_sum_w, "n_pay_w": n_pay_w, "cls_days": cls_days, "zero_days_w": zero_days_w,
        "fingerprint": {"union_range_sha256": fp["sha256"], "n_symbols_union": len(fp["symbols"]),
                        "as_of": AS_OF.isoformat(), "year_range": [YEAR_START, YEAR_END],
                        "last_day_used": LAST_DAY_USED,
                        "delisting_dates_sha256": panel_load.sha256_file(ddates)},
        "panel_meta": {"n_symbols": n_s, "n_days": len(panel["dates"]), "first_day": panel["dates"][0],
                       "last_day": panel["dates"][-1], "n_weeks": n_w, "first_week": weeks[0],
                       "last_week": weeks[-1], "n_symbols_survivors": panel_full["n_symbols_survivors"],
                       "n_symbols_delisted": panel_full["n_symbols_delisted"]},
    }


def _next_week(w: str) -> str:
    return (date.fromisoformat(w) + timedelta(days=7)).isoformat()


def judged_formation_weeks(weeks: list[str], start: str, end: str) -> list[int]:
    """Indices t with week t inside [start, end] AND the next week start (t+1, the holding week)
    also <= end -- the judged formation weeks of the window (W_judged = n_weeks - 1, DEC-75 (1)).
    Computed from calendar arithmetic, so the formation week 2026-06-22 (holding week 2026-06-29,
    dropped from the truncated grid) still counts as a W2 formation week: W1 52, W2 51."""
    return [t for t, w in enumerate(weeks) if start <= w <= end and _next_week(w) <= end]


def still_trading_after(d: dict[str, Any], t: int) -> np.ndarray:
    """Per symbol: still trading at the CLOSE of formation week t (formation-side, PIT: the
    delisting date is public). Inside the grid this is alive[t+1] (the union alive mask ends at
    the delisting week, DEC-72); for the last grid week it is derived from the delisting dates."""
    if t + 1 < len(d["weeks"]):
        return d["alive"][t + 1]
    week_end = (date.fromisoformat(d["weeks"][t]) + timedelta(days=6)).isoformat()
    lad = d["panel"]["last_alive_day"]
    return np.array([(x is None) or (x > week_end) for x in lad], dtype=bool)


def universe_mask(d: dict[str, Any], t: int) -> np.ndarray:
    """Formation universe of week t: PIT alive at t AND still trading at the close of t
    (a symbol whose delisting date lies in week t is already gone at formation)."""
    m = d["alive"][t] & still_trading_after(d, t)
    if EXCL_1H:
        m = m & ~(d["cls_days"]["1h"][t] > 0)
    return m


def d1_members(key_row: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Indices of D1 (lowest decile of the key, size floor(n/10), stable order on ties)."""
    idx = np.flatnonzero(mask)
    n = idx.size
    k = max(1, n // 10)
    order = np.argsort(key_row[idx], kind="mergesort")
    return idx[order[:k]]


def nuisance_formation_weeks(weeks: list[str]) -> list[int]:
    """Formation weeks t >= NUISANCE_START whose HOLDING week t+1 ends <= NUISANCE_END
    (and whose holding week is the consecutive grid row t+1)."""
    out = []
    for t in range(len(weeks) - 1):
        if weeks[t] < NUISANCE_START:
            continue
        if weeks[t + 1] != _next_week(weeks[t]):
            continue
        if not hold_week_end_ok(weeks[t + 1]):
            continue
        out.append(t)
    return out


def hold_week_end_ok(week_start_iso: str) -> bool:
    end = date.fromisoformat(week_start_iso) + timedelta(days=6)
    return end.isoformat() <= NUISANCE_END


def assert_nuisance_holding_week(weeks: list[str], t_hold: int) -> None:
    """Hard guard (task rule 1): no outcome week may end after 2024-06-30."""
    if not hold_week_end_ok(weeks[t_hold]):
        raise RuntimeError(f"OUTCOME BLINDNESS VIOLATION: holding week {weeks[t_hold]} ends after {NUISANCE_END}")
