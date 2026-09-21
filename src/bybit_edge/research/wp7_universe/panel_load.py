"""WP-7 -- ``panel_1d`` loader + weekly derivation for the real census
driver (``scripts/wp7_universe_census.py::cmd_census``).

``panel_store.py`` owns the on-disk year-partition layout; this module is
the READ path that turns those partitions into the dense ``[n_weeks,
n_symbols]`` arrays every other WP-7 module (``pit_universe``, ``null_ic``,
``stats``) already consumes. Symbol order is always ``sorted()`` -- the
single deterministic ordering every array, fingerprint and CSV artifact in
this module and the census driver shares.

Loud-fail discipline (PRD 4.1 DoD point 2, CLAUDE.md): a manifest carrying
any PARTIAL/FAILED partition for the requested (symbol, year) universe
refuses to load (see ``_partial_or_failed``) unless the caller explicitly
passes ``allow_partial=True`` -- in which case the CALLER (the census
driver) is responsible for labelling its report ``nicht urteilstragend``
(not judgement-bearing); this module never makes that label itself, it
only refuses to hide the gap silently. A MISSING row or an EMPTY status is
never a failure here -- both are the expected shape of a real
point-in-time universe (no partition before listing, none after
delisting); ``panel_store.require_all_done``'s stricter "every (symbol,
year) pair must exist and be DONE" contract stays reserved for callers
that truly expect a complete grid (e.g. a single, freshly re-fetched
year), not this module's full historical read.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sqlite3
import struct
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from . import panel_store, pit_universe, stats

__all__ = [
    "PanelLoadError", "load_panel_symbols", "load_panel",
    "combined_range_fingerprint", "weekly_returns_and_mask",
    "momentum_signal", "k_per_week_summary", "funding_deadzone_census",
    "funding_autocorrelation", "delisting_cohorts", "stress_weeks",
    "sha256_file", "write_csv",
    # DEC-67 Entscheidung 6 (census correction, additive):
    "funding_i_per_payment", "funding_excess_daily", "funding_excess_weekly",
    "n_eff_windows", "decile_degeneration_weekly",
    "decile_degeneration_window_summary", "interval_class_switching",
    # WP-12b / DEC-70 (union of panel_1d + panel_1d_delisted, additive):
    "delisted_symbols_with_history", "load_delisting_dates", "load_panel_union",
    "weekly_returns_and_mask_union", "union_range_fingerprint",
]

_EPOCH = date(1970, 1, 1)

#: DEC-59: Bybit's interest term I = 0.01%/8h, normalised per settlement by
#: the symbol-day's OWN interval (derived from the observed ``funding_n``,
#: never assumed -- DEC-59's "4h/8h ist die Heterogenitaet, nicht 1h/8h"
#: finding is exactly why this is measured per day, not looked up once).
I_PER_8H = 0.0001
#: funding_n -> interval-minutes map for the interval classes DEC-59/DEC-67
#: found on the real book (60/120/240/480 min, WELLE1_BEFUND_TEIL4:
#: "120 min (funding_n = 12): 6.129" symbol-days); any other observed
#: funding_n is reported as its own bucket, never silently folded into one
#: of these.
_FUNDING_N_TO_MINUTES: dict[int, int] = {24: 60, 12: 120, 6: 240, 3: 480}


class PanelLoadError(RuntimeError):
    """Loud failure loading/deriving from panel_1d."""


def _partial_or_failed(manifest_path: Path | str, symbols: list[str],
                        years: list[int]) -> list[tuple[str, int, str]]:
    """Every ``(symbol, year)`` IN THE MANIFEST (within ``symbols``/
    ``years``) whose status is PARTIAL or FAILED -- a genuinely incomplete
    or errored fetch. A MISSING row or an EMPTY status is never flagged
    here: both are the EXPECTED shape of a real point-in-time universe (a
    symbol has no partition before its listing year, and none after its
    last trading year once delisted -- ``panel_store.require_all_done``'s
    stricter "every (symbol,year) must exist AND be DONE" contract is
    deliberately NOT reused here, since it would reject exactly those
    routine gaps on every real census run)."""
    con = sqlite3.connect(f"file:{Path(manifest_path).as_posix()}?mode=ro", uri=True)
    try:
        placeholders = ",".join("?" * len(symbols))
        rows = con.execute(
            f"SELECT symbol, year, status FROM partitions WHERE symbol IN "
            f"({placeholders}) AND year BETWEEN ? AND ? AND status IN ('PARTIAL','FAILED')",
            [*symbols, years[0], years[-1]]).fetchall()
    finally:
        con.close()
    return [(s, y, st) for s, y, st in rows]


def _frozen_for_year(year: int, as_of: date) -> bool:
    return year < as_of.year


# ----------------------------------------------------------------------------
# raw daily load
# ----------------------------------------------------------------------------

def load_panel_symbols(manifest_path: Path | str) -> list[str]:
    """All distinct symbols recorded in the manifest, sorted -- the
    canonical symbol order every array in this module uses."""
    con = sqlite3.connect(f"file:{Path(manifest_path).as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT DISTINCT symbol FROM partitions").fetchall()
    finally:
        con.close()
    return sorted(r[0] for r in rows)


def load_panel(
    base_dir: Path | str, manifest_path: Path | str, *, year_start: int, year_end: int,
    as_of: date, symbols: list[str] | None = None, allow_partial: bool = False,
) -> dict[str, Any]:
    """Read every (symbol, year) partition in ``[year_start, year_end]``
    into aligned daily arrays: ``dates`` (sorted ISO strings), and
    ``close``/``turnover``/``funding_n``/``funding_sum`` as
    ``[n_days, n_symbols]`` float64 (``NaN`` where the symbol has no bar
    that day). Loud-fails (``PanelLoadError``) on any PARTIAL/FAILED
    partition in the requested range unless ``allow_partial`` -- the
    caller then labels its report accordingly. A MISSING row or an EMPTY
    partition (no bars before listing / after delisting) is never a
    failure -- that is the expected shape of a real point-in-time universe
    (see ``_partial_or_failed``).
    """
    import pyarrow.parquet as pq

    base_dir = Path(base_dir)
    manifest_path = Path(manifest_path)
    years = list(range(year_start, year_end + 1))
    if symbols is None:
        symbols = load_panel_symbols(manifest_path)
    symbols = sorted(symbols)
    if not symbols:
        raise PanelLoadError(f"no symbols found in manifest {manifest_path}")

    status_counts = panel_store.manifest_status_counts(manifest_path)
    bad = _partial_or_failed(manifest_path, symbols, years)
    if bad and not allow_partial:
        detail = ", ".join(f"{s}/{y}={st}" for s, y, st in bad[:20])
        more = f" (+{len(bad) - 20} more)" if len(bad) > 20 else ""
        raise PanelLoadError(
            f"{len(bad)} partition(s) PARTIAL/FAILED -- refusing a judgement-bearing "
            f"census read (pass allow_partial=True / --allow-partial to proceed labelled "
            f"'nicht urteilstragend'): {detail}{more}")

    per_symbol_days: dict[str, dict[int, dict[str, float | None]]] = {}
    all_days: set[int] = set()
    n_partitions_used = 0
    for s in symbols:
        day_rows: dict[int, dict[str, float | None]] = {}
        for y in years:
            frozen = _frozen_for_year(y, as_of)
            row = panel_store.manifest_get(manifest_path, s, y)
            if row is None or row["n_rows"] == 0:
                continue
            if row["status"] not in ("DONE", "PARTIAL"):
                continue
            if row["status"] == "PARTIAL" and not allow_partial:
                continue  # the loud-fail check above would already have raised
            path = panel_store.partition_path(base_dir, s, y, frozen=frozen)
            if not path.is_file():
                path = panel_store.partition_path(base_dir, s, y, frozen=not frozen)
                if not path.is_file():
                    continue
            table = pq.read_table(path, columns=list(panel_store.PANEL_COLUMNS))
            cols = table.to_pydict()
            n_partitions_used += 1
            for i, start_ms in enumerate(cols["start_ms"]):
                day_idx = int(start_ms) // 86_400_000
                day_rows[day_idx] = {
                    "close": cols["close"][i], "turnover": cols["turnover"][i],
                    "funding_n": cols["funding_n"][i], "funding_sum": cols["funding_sum"][i],
                }
        if day_rows:
            per_symbol_days[s] = day_rows
            all_days.update(day_rows.keys())

    if not all_days:
        raise PanelLoadError(
            f"panel_1d yielded no usable daily bars for {len(symbols)} symbol(s), "
            f"years {year_start}..{year_end}")

    day_idx_sorted = sorted(all_days)
    n_days, n_symbols = len(day_idx_sorted), len(symbols)
    day_pos = {d: i for i, d in enumerate(day_idx_sorted)}
    dates = [(_EPOCH + timedelta(days=d)).isoformat() for d in day_idx_sorted]

    close = np.full((n_days, n_symbols), np.nan, dtype=np.float64)
    turnover = np.full((n_days, n_symbols), np.nan, dtype=np.float64)
    funding_n = np.full((n_days, n_symbols), np.nan, dtype=np.float64)
    funding_sum = np.full((n_days, n_symbols), np.nan, dtype=np.float64)
    for j, s in enumerate(symbols):
        rows = per_symbol_days.get(s)
        if not rows:
            continue
        for d, vals in rows.items():
            i = day_pos[d]
            close[i, j] = vals["close"]
            turnover[i, j] = vals["turnover"]
            fn, fs = vals["funding_n"], vals["funding_sum"]
            if fn is not None:
                funding_n[i, j] = fn
            if fs is not None:
                funding_sum[i, j] = fs

    return {
        "symbols": symbols, "dates": dates, "day_index": day_idx_sorted,
        "close": close, "turnover": turnover, "funding_n": funding_n,
        "funding_sum": funding_sum, "n_partitions_used": n_partitions_used,
        "status_counts": status_counts, "allow_partial": allow_partial,
        "year_range": [year_start, year_end], "as_of": as_of.isoformat(),
    }


def combined_range_fingerprint(
    base_dir: Path | str, symbols: list[str], year_start: int, year_end: int, *, as_of: date,
) -> dict[str, Any]:
    """Range fingerprint over (Symbolmenge, Jahresbereich), same discipline
    as ``panel_store.range_fingerprint`` but resolving ``frozen`` per YEAR
    (the loaded range spans frozen years AND the current open year) instead
    of a single flag for the whole range."""
    h = hashlib.sha256()
    sorted_symbols = sorted(set(symbols))
    h.update(json.dumps(sorted_symbols).encode("utf-8"))
    h.update(struct.pack("<qq", year_start, year_end))
    per_partition: dict[str, str] = {}
    for s in sorted_symbols:
        for y in range(year_start, year_end + 1):
            frozen = _frozen_for_year(y, as_of)
            path = panel_store.partition_path(base_dir, s, y, frozen=frozen)
            if not path.is_file():
                continue
            fp = panel_store.panel_fingerprint(base_dir, s, y, frozen=frozen)
            per_partition[f"{s}/{y}"] = fp
            h.update(f"{s}/{y}".encode("utf-8"))
            h.update(fp.encode("ascii"))
    return {"symbols": sorted_symbols, "year_range": [year_start, year_end],
            "n_partitions": len(per_partition), "sha256": h.hexdigest(),
            "per_partition": per_partition}


# ----------------------------------------------------------------------------
# daily -> weekly
# ----------------------------------------------------------------------------

def _daily_close_to_weekly(
    panel: dict[str, Any],
) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Shared core of ``weekly_returns_and_mask``/``weekly_returns_and_mask_
    union``: daily ``panel['close']`` -> ``(weeks, close_mat, returns,
    first_week, last_week)``, all ``[n_weeks, n_symbols]`` (or
    ``[n_symbols]`` for the two week-index arrays), ``panel['symbols']``
    column order. A gap never manufactures a weekly return (only
    CONSECUTIVE week indices get one, same discipline as
    ``pair_corr.log_returns``). Factored out so the union path (WP-12b)
    reuses the EXACT same close->weekly arithmetic instead of a parallel
    reimplementation -- the two callers only differ in how they turn
    ``first_week``/``last_week`` into an alive mask afterward."""
    symbols, dates, close = panel["symbols"], panel["dates"], panel["close"]
    n_days, n_symbols = close.shape

    weekly_close_per_symbol: list[dict[str, float]] = []
    for j in range(n_symbols):
        d_list = [dates[i] for i in range(n_days) if not math.isnan(close[i, j])]
        c_list = [float(close[i, j]) for i in range(n_days) if not math.isnan(close[i, j])]
        weekly_close_per_symbol.append(
            pit_universe.weekly_close_from_daily(d_list, c_list) if d_list else {})

    all_weeks = sorted({wk for wc in weekly_close_per_symbol for wk in wc})
    n_weeks = len(all_weeks)
    if n_weeks == 0:
        raise PanelLoadError("no weekly closes derived from panel (empty daily input)")
    week_pos = {w: i for i, w in enumerate(all_weeks)}

    close_mat = np.full((n_weeks, n_symbols), np.nan, dtype=np.float64)
    for j, wc in enumerate(weekly_close_per_symbol):
        for w, c in wc.items():
            close_mat[week_pos[w], j] = c

    returns = np.zeros((n_weeks, n_symbols), dtype=np.float64)
    first_week = np.full(n_symbols, n_weeks, dtype=np.int64)
    last_week = np.full(n_symbols, -1, dtype=np.int64)
    for j in range(n_symbols):
        idx = np.flatnonzero(~np.isnan(close_mat[:, j]))
        if idx.size == 0:
            continue
        first_week[j], last_week[j] = int(idx.min()), int(idx.max())
        for k in range(1, idx.size):
            t0, t1 = int(idx[k - 1]), int(idx[k])
            if t1 - t0 != 1:
                continue  # a gap never manufactures a return across missing weeks
            c0, c1 = close_mat[t0, j], close_mat[t1, j]
            if c0 > 0 and c1 > 0:
                returns[t1, j] = math.log(c1 / c0)

    return all_weeks, close_mat, returns, first_week, last_week


def weekly_returns_and_mask(
    panel: dict[str, Any], *, min_weeks_history: int = pit_universe.MIN_WEEKS_HISTORY,
) -> dict[str, Any]:
    """Daily ``panel`` (from ``load_panel``) -> weekly closes/returns/PIT
    alive mask, all ``[n_weeks, n_symbols]`` (ISO-week rows, ascending,
    ``panel['symbols']`` column order). A gap never manufactures a weekly
    return (only CONSECUTIVE week indices get one, same discipline as
    ``pair_corr.log_returns``)."""
    symbols = panel["symbols"]
    weeks, close_mat, returns, first_week, last_week = _daily_close_to_weekly(panel)
    n_weeks = len(weeks)
    alive = pit_universe.pit_alive_mask(first_week, last_week, n_weeks,
                                         min_weeks_history=min_weeks_history)
    return {"weeks": weeks, "close": close_mat, "returns": returns, "alive": alive,
            "first_week": first_week, "last_week": last_week, "symbols": symbols}


def momentum_signal(returns: np.ndarray, *, trail_win: int = 4) -> np.ndarray:
    """Trailing ``trail_win``-week cumulative return ending at each week --
    the pre-registered signal (PRD 4.1) fed to ``pit_universe.
    weekly_ic_series`` for the DEC-53 weekly-IC artifact. Same trailing
    window as ``pit_universe.momentum_ic_series``'s internal ``trail``."""
    n_weeks = returns.shape[0]
    trail = np.full_like(returns, np.nan)
    for t in range(n_weeks):
        lo = max(0, t - trail_win + 1)
        trail[t] = returns[lo:t + 1].sum(axis=0)
    return trail


def k_per_week_summary(alive: np.ndarray, weeks: list[str]) -> dict[str, Any]:
    k = pit_universe.k_per_week(alive)
    nz = np.flatnonzero(k > 0)
    if nz.size == 0:
        return {"min": 0, "median": 0.0, "max": 0, "n_weeks": len(weeks),
                "first_week_with_members": None, "last_week_with_members": None}
    return {"min": int(k[nz].min()), "median": float(np.median(k[nz])),
            "max": int(k[nz].max()), "n_weeks": len(weeks),
            "first_week_with_members": weeks[int(nz.min())],
            "last_week_with_members": weeks[int(nz.max())]}


# ----------------------------------------------------------------------------
# DEC-59: deadzone/interval-class census + funding autocorrelation
# ----------------------------------------------------------------------------

def funding_deadzone_census(
    panel: dict[str, Any], *, tol: float = 1e-9, n_deciles: int = 10,
) -> dict[str, Any]:
    """DEC-59 mandatory lines: per symbol-day, is the day's mean funding
    rate (``funding_sum/funding_n``) EXACTLY the interest term ``I``
    normalised to that day's OWN interval (derived from the observed
    ``funding_n``, never assumed -- DEC-59: heterogeneity is 4h/8h, and a
    symbol's interval can change mid-history)? Reported overall, per
    interval class, and per decile of each symbol's WEEK-SUM funding
    (DEC-59 point 2's sort key), averaged over weeks."""
    symbols = panel["symbols"]
    funding_n, funding_sum, dates = panel["funding_n"], panel["funding_sum"], panel["dates"]
    n_days, n_symbols = funding_n.shape

    # Vectorised elementwise classification (n_days x n_symbols is up to a
    # few million cells on the real book -- a Python double loop here would
    # blow the "minutes, not tens of minutes" runtime target).
    has_funding = ~np.isnan(funding_n) & (funding_n > 0)
    fn_int = np.where(has_funding, np.round(funding_n), -1).astype(np.int64)
    minutes = np.full(fn_int.shape, -1, dtype=np.int64)
    for fn_val, mins in _FUNDING_N_TO_MINUTES.items():
        minutes[fn_int == fn_val] = mins
    classified = has_funding & (minutes > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        avg_rate = np.where(has_funding, funding_sum / np.where(has_funding, fn_int, 1), np.nan)
        i_settlement = np.where(classified, I_PER_8H * (minutes / 480.0), np.nan)
        is_deadzone = classified & (np.abs(avg_rate - i_settlement) < tol)

    interval_counts: dict[str, int] = {}
    vals, cnts = np.unique(fn_int[has_funding], return_counts=True)
    for v, c in zip(vals.tolist(), cnts.tolist()):
        mins = _FUNDING_N_TO_MINUTES.get(v)
        label = f"{mins}min" if mins is not None else f"funding_n={v} (unklassifiziert)"
        interval_counts[label] = interval_counts.get(label, 0) + c

    n_with_funding = int(has_funding.sum())
    n_deadzone = int(is_deadzone.sum())
    overall_share = (n_deadzone / n_with_funding) if n_with_funding else None

    # weekly funding SUM per symbol (DEC-59 sort key) -> decile assignment
    # per week, deadzone share aggregated by decile across all weeks.
    week_start = [pit_universe.iso_week_start(date.fromisoformat(d)).isoformat() for d in dates]
    week_order: list[str] = sorted(set(week_start))
    week_rows: dict[str, list[int]] = {}
    for i, w in enumerate(week_start):
        week_rows.setdefault(w, []).append(i)

    decile_deadzone = [0] * n_deciles
    decile_total = [0] * n_deciles
    decile_symbol_weeks = [0] * n_deciles
    for w in week_order:
        rows = week_rows[w]
        week_sum = np.nansum(funding_sum[rows, :], axis=0)
        week_has = has_funding[rows, :].any(axis=0)
        ranked = [j for j in range(n_symbols) if week_has[j]]
        if not ranked:
            continue
        ranked.sort(key=lambda j: -week_sum[j])
        n = len(ranked)
        for d in range(n_deciles):
            lo, hi = (n * d) // n_deciles, (n * (d + 1)) // n_deciles
            group = ranked[lo:hi]
            if not group:
                continue
            dz = int(is_deadzone[np.ix_(rows, group)].sum())
            tot = int(has_funding[np.ix_(rows, group)].sum())
            decile_deadzone[d] += dz
            decile_total[d] += tot
            decile_symbol_weeks[d] += len(group)

    by_decile = [
        {"decile": d + 1, "n_symbol_weeks": decile_symbol_weeks[d],
         "n_symbol_days_with_funding": decile_total[d],
         "n_deadzone_symbol_days": decile_deadzone[d],
         "deadzone_share": (decile_deadzone[d] / decile_total[d]) if decile_total[d] else None}
        for d in range(n_deciles)
    ]
    return {"overall_share": overall_share, "n_symbol_days_with_funding": n_with_funding,
            "n_deadzone_symbol_days": n_deadzone, "interval_class_counts": interval_counts,
            "by_decile": by_decile, "n_symbols": len(symbols), "descriptive_only": True}


def funding_autocorrelation(panel: dict[str, Any], *, max_lag: int = 4,
                             min_weeks: int = 12) -> dict[str, Any]:
    """Weekly-funding-SUM autocorrelation lag 1..``max_lag`` per symbol,
    median across symbols with at least ``min_weeks`` weeks of funding
    data -- descriptive only, no verdict."""
    symbols, dates, funding_sum = panel["symbols"], panel["dates"], panel["funding_sum"]
    n_days, n_symbols = funding_sum.shape
    week_start = [pit_universe.iso_week_start(date.fromisoformat(d)).isoformat() for d in dates]
    week_order = sorted(set(week_start))
    week_rows: dict[str, list[int]] = {}
    for i, w in enumerate(week_start):
        week_rows.setdefault(w, []).append(i)
    weekly = np.full((len(week_order), n_symbols), np.nan, dtype=np.float64)
    for wi, w in enumerate(week_order):
        rows = week_rows[w]
        weekly[wi] = np.nansum(funding_sum[rows, :], axis=0)

    lag_values: dict[int, list[float]] = {lag: [] for lag in range(1, max_lag + 1)}
    n_symbols_used = 0
    for j in range(n_symbols):
        series = weekly[:, j]
        valid = ~np.isnan(series)
        if int(valid.sum()) < min_weeks:
            continue
        s = series[valid]
        if s.std() == 0.0:
            continue
        n_symbols_used += 1
        for lag in range(1, max_lag + 1):
            if len(s) <= lag:
                continue
            a, b = s[:-lag], s[lag:]
            if a.std() == 0.0 or b.std() == 0.0:
                continue
            r = float(np.corrcoef(a, b)[0, 1])
            if not math.isnan(r):
                lag_values[lag].append(r)

    medians = {f"lag{lag}": (float(np.median(vals)) if vals else None)
               for lag, vals in lag_values.items()}
    return {"median_autocorr": medians, "n_symbols_used": n_symbols_used,
            "n_symbols_total": len(symbols), "descriptive_only": True}


# ----------------------------------------------------------------------------
# DEC-58(g): delisting hazard "Beifahrer" -- descriptive cohort table
# ----------------------------------------------------------------------------

def delisting_cohorts(weekly: dict[str, Any], *, as_of_week: str) -> list[dict[str, Any]]:
    """Per listing-year cohort (year of a symbol's FIRST week), count of
    symbols and how many had their LAST bar week before ``as_of_week`` --
    descriptive number, not a hazard model (DEC-58 point g: "Zahl statt
    Haekchen fuer die Survivorship-Verzerrung")."""
    weeks, symbols = weekly["weeks"], weekly["symbols"]
    first_week, last_week = weekly["first_week"], weekly["last_week"]
    as_of_idx = len(weeks) - 1
    if as_of_week in weeks:
        as_of_idx = weeks.index(as_of_week)

    cohorts: dict[int, dict[str, int]] = {}
    for j, s in enumerate(symbols):
        fw = int(first_week[j])
        if fw < 0 or fw >= len(weeks):
            continue
        cohort_year = int(weeks[fw][:4])
        c = cohorts.setdefault(cohort_year, {"n_listed": 0, "n_delisted": 0})
        c["n_listed"] += 1
        if 0 <= int(last_week[j]) < as_of_idx:
            c["n_delisted"] += 1
    return [{"listing_year": y, **v} for y, v in sorted(cohorts.items())]


# ----------------------------------------------------------------------------
# DEC-67 Entscheidung 2: A1 sort key (funding_excess_sum = SUM(F - I))
# ----------------------------------------------------------------------------

def funding_i_per_payment(funding_n: np.ndarray | float) -> np.ndarray | float:
    """DEC-67 Entscheidung 2 -- interest term ``I`` per SETTLEMENT, derived
    ALWAYS from the day's own ``funding_n`` (never a fixed-interval
    lookup): ``I_per_payment = I_PER_8H * (24/funding_n)/8 = I_PER_8H *
    3/funding_n``. Matches every interval class DEC-59/DEC-67 measured on
    the real book (funding_n=3/480min -> I_PER_8H; funding_n=6/240min ->
    I_PER_8H/2; funding_n=12/120min -> I_PER_8H/4; funding_n=24/60min ->
    I_PER_8H/8) and ALSO covers any other observed funding_n without
    inventing a bucket for it -- the A1 sort key must never silently drop
    an unclassified symbol-day (unlike ``funding_deadzone_census``'s
    ``classified`` restriction, which is fine to leave narrow since it
    only reports a share)."""
    return I_PER_8H * 3.0 / funding_n


def funding_excess_daily(panel: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """DEC-67 Entscheidung 2 -- A1 sort key, daily building block:
    ``[n_days, n_symbols]`` array of ``funding_sum - funding_n *
    funding_i_per_payment(funding_n)`` (a day's payments minus their
    combined interest term). A day with no funding (``funding_n`` NaN, 0,
    or its ``funding_sum`` counterpart NaN) contributes EXACTLY 0.0, never
    NaN -- it is a MISSING day, not a measured deadzone day, but it must
    not poison a weekly SUM by turning it into NaN (the entire point of a
    SUM key, DEC-67 E2). The second return value is the ``has_funding``
    mask so callers can still tell missing from measured-zero when they
    need to (``funding_excess_weekly``'s ``n_days_with_funding``)."""
    funding_n, funding_sum = panel["funding_n"], panel["funding_sum"]
    has_funding = ~np.isnan(funding_n) & (funding_n > 0) & ~np.isnan(funding_sum)
    with np.errstate(invalid="ignore", divide="ignore"):
        safe_n = np.where(has_funding, funding_n, 1.0)
        i_per_payment = funding_i_per_payment(safe_n)
        excess = np.where(has_funding, funding_sum - funding_n * i_per_payment, 0.0)
    return excess, has_funding


def funding_excess_weekly(panel: dict[str, Any], weeks: list[str]) -> dict[str, Any]:
    """DEC-67 Entscheidung 2 -- weekly A1 sort key: per symbol-week, the
    SUM of ``funding_excess_daily`` over the ISO week's days. Aligned to
    the EXACT SAME ``weeks`` grid ``weekly_returns_and_mask`` returns --
    row ``t`` here lines up with ``returns[t]``/``alive[t]`` everywhere
    downstream, the convention every WP-7 IC/permutation-null call already
    relies on (``pit_universe.weekly_ic_series``, ``null_ic.
    permutation_null_sd``). A week with zero funding-bearing days for a
    symbol gets key 0.0 (DEC-67: "Totzonen-Wochen liegen ... bei 0" --
    a genuine deadzone week and a no-data week are INDISTINGUISHABLE for
    the sort key by design, DEC-67 E2's "kein Tie-Break innerhalb des
    Klumpens"); ``n_days_with_funding``/``n_days_total`` keep the
    distinction available for descriptive use (the decile-degeneration
    census does not need it, but a future audit might)."""
    symbols, dates = panel["symbols"], panel["dates"]
    excess_daily, has_funding = funding_excess_daily(panel)
    n_days, n_symbols = excess_daily.shape
    week_start = [pit_universe.iso_week_start(date.fromisoformat(d)).isoformat() for d in dates]
    week_pos = {w: i for i, w in enumerate(weeks)}
    n_weeks = len(weeks)
    key = np.zeros((n_weeks, n_symbols), dtype=np.float64)
    n_days_with_funding = np.zeros((n_weeks, n_symbols), dtype=np.int64)
    n_days_total = np.zeros((n_weeks, n_symbols), dtype=np.int64)
    for i, w in enumerate(week_start):
        wi = week_pos.get(w)
        if wi is None:
            continue  # a calendar week outside the returns/alive grid (no weekly close anywhere)
        key[wi] += excess_daily[i]
        n_days_with_funding[wi] += has_funding[i].astype(np.int64)
        n_days_total[wi] += 1
    return {"weeks": weeks, "symbols": symbols, "key": key,
            "n_days_with_funding": n_days_with_funding, "n_days_total": n_days_total}


# ----------------------------------------------------------------------------
# DEC-67 Entscheidung 3: decile-degeneration census of the A1 sort key
# ----------------------------------------------------------------------------

def decile_degeneration_weekly(
    key: np.ndarray, alive: np.ndarray, weeks: list[str], *, tol: float = 1e-12,
) -> dict[str, Any]:
    """DEC-67 Entscheidung 3 -- per-week decile-degeneration census of the
    A1 sort key (``key``, e.g. ``funding_excess_weekly``'s ``key``): for
    each week's ALIVE symbols, the share with key EXACTLY 0 (the deadzone
    lump, within ``tol``), strictly negative, and strictly positive. D1
    (the long leg) is degenerate that week if the strictly-negative share
    is below 0.10; D10 (the short leg) if the strictly-positive share is
    below 0.10 (DEC-67 E3: below that, the zero-lump reaches into the
    decile and its ranking inside is arbitrary). This is the raw per-week
    table only -- window summaries are ``decile_degeneration_window_
    summary``'s job; this function makes NO verdict, only reports shares.
    """
    n_weeks, n_symbols = key.shape
    rows: list[dict[str, Any]] = []
    for t in range(n_weeks):
        mask = alive[t]
        n = int(mask.sum())
        if n == 0:
            rows.append({"week": weeks[t], "n_symbols": 0, "lump_share": None,
                         "neg_share": None, "pos_share": None,
                         "d1_degenerate": None, "d10_degenerate": None})
            continue
        k = key[t, mask]
        n_zero = int(np.sum(np.abs(k) < tol))
        n_neg = int(np.sum(k < -tol))
        n_pos = int(np.sum(k > tol))
        neg_share = n_neg / n
        pos_share = n_pos / n
        rows.append({
            "week": weeks[t], "n_symbols": n, "lump_share": n_zero / n,
            "neg_share": neg_share, "pos_share": pos_share,
            "d1_degenerate": neg_share < 0.10, "d10_degenerate": pos_share < 0.10,
        })
    return {"weekly": rows, "tol": tol, "descriptive_only": True}


def decile_degeneration_window_summary(
    weekly_rows: list[dict[str, Any]], *, last_n: int, offset: int = 0,
) -> dict[str, Any]:
    """DEC-67 Entscheidung 3 -- window summary of ``decile_degeneration_
    weekly``'s per-week table: the ``last_n`` weeks starting ``offset``
    weeks before the very end of ``weekly_rows`` (``offset=0`` -> the most
    recent ``last_n`` weeks; ``offset=52`` with ``last_n=52`` -> the 52
    weeks BEFORE that -- DEC-67's "letzte 52 / vorherige 52" window pair).
    Reports the CHRONOLOGICAL MEDIAN week of the window (positional median
    -- for an even count, the lower of the two middle weeks, a fixed,
    documented convention) and whether THAT week's shares flag a
    degenerate leg (DEC-67 E3: "die Median-Woche des Fensters"), plus how
    many weeks in the window are individually degenerate. Weeks with no
    alive symbols (``lump_share`` ``None``) are excluded before taking the
    median."""
    n = len(weekly_rows)
    hi = n - offset
    lo = max(0, hi - last_n)
    window = [r for r in weekly_rows[lo:hi] if r["lump_share"] is not None]
    if not window:
        return {"n_weeks": 0, "week_start": None, "week_end": None, "median_week": None,
                "median_week_lump_share": None, "median_week_neg_share": None,
                "median_week_pos_share": None, "median_week_d1_degenerate": None,
                "median_week_d10_degenerate": None,
                "n_weeks_d1_degenerate": 0, "n_weeks_d10_degenerate": 0}
    mid = window[(len(window) - 1) // 2]
    return {
        "n_weeks": len(window), "week_start": window[0]["week"], "week_end": window[-1]["week"],
        "median_week": mid["week"], "median_week_lump_share": mid["lump_share"],
        "median_week_neg_share": mid["neg_share"], "median_week_pos_share": mid["pos_share"],
        "median_week_d1_degenerate": mid["d1_degenerate"],
        "median_week_d10_degenerate": mid["d10_degenerate"],
        "n_weeks_d1_degenerate": sum(1 for r in window if r["d1_degenerate"]),
        "n_weeks_d10_degenerate": sum(1 for r in window if r["d10_degenerate"]),
    }


# ----------------------------------------------------------------------------
# DEC-67 Entscheidung 6: interval-class switching per symbol
# ----------------------------------------------------------------------------

def interval_class_switching(panel: dict[str, Any]) -> dict[str, Any]:
    """DEC-67 Entscheidung 6 -- per-symbol interval-CLASS switching
    (DEC-59: a symbol's settlement interval can change mid-history). For
    each symbol, days are filtered to CLASSIFIED days only (480/240/120/
    60-min -- unclassified/missing days are ignored, they neither start
    nor end a transition), then the number of transitions between
    consecutive classified days' classes is counted (a run of the SAME
    class counts zero transitions no matter how long it is). Returns the
    per-symbol switch count + days-per-class, the DISTRIBUTION over
    symbols (never switches / switches once / 2-5 times />5 times), and
    the total symbol-days per class (same totals ``funding_deadzone_
    census``'s ``interval_class_counts`` reports, repeated here so this
    section is self-contained) -- descriptive, no verdict."""
    symbols = panel["symbols"]
    funding_n = panel["funding_n"]
    n_days, n_symbols = funding_n.shape
    has_funding = ~np.isnan(funding_n) & (funding_n > 0)
    fn_int = np.where(has_funding, np.round(funding_n), -1).astype(np.int64)
    minutes = np.full(fn_int.shape, -1, dtype=np.int64)
    for fn_val, mins in _FUNDING_N_TO_MINUTES.items():
        minutes[fn_int == fn_val] = mins
    classified = has_funding & (minutes > 0)

    per_symbol: list[dict[str, Any]] = []
    days_per_class_total: dict[str, int] = {}
    n_switch_distribution = {"0": 0, "1": 0, "2-5": 0, ">5": 0}
    for j, sym in enumerate(symbols):
        idx = np.flatnonzero(classified[:, j])  # rows are already date-sorted (load_panel)
        classes = [int(minutes[i, j]) for i in idx]
        days_per_class: dict[str, int] = {}
        for m in classes:
            label = f"{m}min"
            days_per_class[label] = days_per_class.get(label, 0) + 1
            days_per_class_total[label] = days_per_class_total.get(label, 0) + 1
        n_switches = sum(1 for k in range(1, len(classes)) if classes[k] != classes[k - 1])
        bucket = "0" if n_switches == 0 else "1" if n_switches == 1 else (
            "2-5" if n_switches <= 5 else ">5")
        n_switch_distribution[bucket] += 1
        per_symbol.append({"symbol": sym, "n_switches": n_switches,
                            "n_classified_days": len(classes), "days_per_class": days_per_class})
    return {"per_symbol": per_symbol, "n_switch_distribution": n_switch_distribution,
            "days_per_class_total": days_per_class_total, "n_symbols": len(symbols),
            "descriptive_only": True}


# ----------------------------------------------------------------------------
# STRESS_ABS weeks (DEC-62 N_eff-in-stress line -- optional, label only)
# ----------------------------------------------------------------------------

def stress_weeks(stress_abs_path: Path | str, weeks: list[str]) -> dict[str, Any]:
    """Map ``STRESS_ABS`` fixture days (DEC-56) to the ISO weeks they fall
    in, restricted to ``weeks`` (the loaded panel's week grid). Returns
    ``available: False`` (never a computed value) when the fixture file
    does not exist yet -- DEC-62's N_eff-in-stress line is then reported
    as "nicht verfuegbar", not silently skipped."""
    path = Path(stress_abs_path)
    if not path.is_file():
        return {"available": False, "note": f"{path} nicht gefunden -- "
                "WP-10(A2)-Stress-Kanon noch nicht abgelegt"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"available": False, "note": f"{path} nicht lesbar: {exc}"}
    days = payload if isinstance(payload, list) else payload.get("days", [])
    stress_week_set = {pit_universe.iso_week_start(date.fromisoformat(d)).isoformat()
                        for d in days}
    week_pos = {w: i for i, w in enumerate(weeks)}
    idx = sorted(week_pos[w] for w in stress_week_set if w in week_pos)
    return {"available": True, "n_stress_days": len(days), "n_stress_weeks_in_panel": len(idx),
            "week_indices": idx}


# ----------------------------------------------------------------------------
# DEC-67 Entscheidung 6: N_eff bug fix -- judgement-window N_eff, not full history
# ----------------------------------------------------------------------------

def n_eff_windows(
    returns: np.ndarray, alive: np.ndarray, weeks: list[str], *,
    stress_week_indices: list[int] | None = None,
) -> dict[str, Any]:
    """DEC-67 Entscheidung 6 -- N_eff bug fix (WELLE1_BEFUND_TEIL4: "N_eff
    nan (Bau-Fehler)"). ``stats.n_eff`` needs a BALANCED panel (every
    symbol alive every week of the array it is given); the full
    multi-year history is never balanced (listings/delistings span all
    298 weeks), so calling it on the whole history legitimately returns
    ``nan``/``n_symbols_balanced=0`` -- that was the WRONG WINDOW being
    passed in, not a data finding. This computes N_eff on the JUDGEMENT
    windows instead -- the last 52 and the last 104 weeks, each balanced
    only WITHIN that window -- plus the STRESS_ABS weeks
    (``stress_week_indices``, absolute row indices into ``returns``/
    ``alive``, from ``stress_weeks``) RESTRICTED to the last 104 weeks,
    balanced across just those weeks. ``stats.n_eff`` itself is untouched;
    only the slice passed to it is new (the old full-history call, e.g.
    ``stats.n_eff(returns, alive)``, is left exactly as it was -- callers
    keep reporting it too, labelled why it may legitimately be n/a)."""
    n_weeks = returns.shape[0]

    def _tail(n: int) -> tuple[int, int]:
        lo = max(0, n_weeks - n)
        return lo, n_weeks

    def _window_result(lo: int, hi: int, window_weeks: int) -> dict[str, Any]:
        res = stats.n_eff(returns[lo:hi], alive[lo:hi])
        return {**res, "window_weeks": window_weeks, "n_weeks_in_window": hi - lo,
                "week_start": weeks[lo] if hi > lo else None,
                "week_end": weeks[hi - 1] if hi > lo else None}

    lo52, hi52 = _tail(52)
    lo104, hi104 = _tail(104)
    out: dict[str, Any] = {
        "w52": _window_result(lo52, hi52, 52),
        "w104": _window_result(lo104, hi104, 104),
    }

    if stress_week_indices:
        idx = sorted(i for i in stress_week_indices if lo104 <= i < hi104)
        if len(idx) >= 2:
            res = stats.n_eff(returns[idx], alive[idx])
            out["stress_abs_last104"] = {
                **res, "n_weeks_in_window": len(idx), "week_indices": idx,
                "restricted_to": "letzte 104 Wochen",
            }
        else:
            out["stress_abs_last104"] = {
                "n_eff": float("nan"), "n_symbols_balanced": 0, "inv_n_eff": None,
                "n_weeks_in_window": len(idx),
                "note": "weniger als 2 STRESS_ABS-Wochen in den letzten 104 Wochen",
            }
    else:
        out["stress_abs_last104"] = {
            "n_eff": float("nan"), "n_symbols_balanced": 0, "inv_n_eff": None,
            "n_weeks_in_window": 0,
            "note": "STRESS_ABS-Fixture nicht verfuegbar oder keine Stress-Wochen im Panel",
        }
    return out


# ----------------------------------------------------------------------------
# WP-12b / DEC-70: union of panel_1d (survivors) + panel_1d_delisted
# ----------------------------------------------------------------------------

def delisted_symbols_with_history(manifest_path: Path | str) -> tuple[list[str], list[str]]:
    """Symbols recorded in a WP-12b ``panel_1d_delisted`` manifest, split
    into (a) symbols with at least one NON-FAILED partition row (usable,
    sorted) and (b) symbols whose ONLY row(s) are FAILED (the
    ``delisted_panel.NO_HISTORY_REASON`` marker -- a symbol
    ``delisted_panel.fetch_delisted_panel`` reports loudly but never
    writes a parquet partition for). A NO_HISTORY-only symbol must never
    silently trip ``load_panel``'s PARTIAL/FAILED loud-fail gate on every
    ``--include-delisted`` census run -- it is an EXPECTED, already-
    reported condition (the kline endpoint genuinely serves nothing for
    that symbol), not a fetch error to gate a run on; excluding it from
    the "usable" set here is how that distinction is kept without
    weakening ``load_panel``'s general PARTIAL/FAILED discipline for
    every other caller."""
    con = sqlite3.connect(f"file:{Path(manifest_path).as_posix()}?mode=ro", uri=True)
    try:
        all_syms = {r[0] for r in con.execute("SELECT DISTINCT symbol FROM partitions").fetchall()}
        ok_syms = {r[0] for r in con.execute(
            "SELECT DISTINCT symbol FROM partitions WHERE status != 'FAILED'").fetchall()}
    finally:
        con.close()
    return sorted(ok_syms), sorted(all_syms - ok_syms)


def load_delisting_dates(path: Path | str) -> dict[str, date]:
    """``delisted_panel.write_delisting_dates_json``'s payload ->
    ``{symbol: delist_date}`` (dropping the announcement-id/source
    provenance fields -- callers that need those read the JSON directly)."""
    path = Path(path)
    if not path.is_file():
        raise PanelLoadError(f"delisting_dates.json not found at {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, date] = {}
    for sym, info in (payload.get("symbols") or {}).items():
        out[sym] = date.fromisoformat(info["delist_date"])
    return out


def _scatter_panel(dst: dict[str, np.ndarray], day_pos: dict[int, int],
                    sym_pos: dict[str, int], panel: dict[str, Any]) -> None:
    """Vectorised in-place scatter of one ``load_panel`` result's daily
    columns into pre-allocated (NaN-filled) union arrays, at the day/symbol
    positions the union grid assigns them. Safe to call once per source
    tree in sequence PROVIDED the trees' symbol sets are disjoint (the
    caller, ``load_panel_union``, asserts this before ever calling here)."""
    i_idx = np.array([day_pos[d] for d in panel["day_index"]], dtype=np.int64)
    j_idx = np.array([sym_pos[s] for s in panel["symbols"]], dtype=np.int64)
    for key in ("close", "turnover", "funding_n", "funding_sum"):
        dst[key][np.ix_(i_idx, j_idx)] = panel[key]


def load_panel_union(
    base_dir: Path | str, manifest_path: Path | str,
    delisted_base: Path | str, delisted_manifest_path: Path | str, *,
    year_start: int, year_end: int, as_of: date,
    delisting_dates_path: Path | str | None = None,
    symbols: list[str] | None = None, delisted_symbols: list[str] | None = None,
    allow_partial: bool = False,
) -> dict[str, Any]:
    """Survivors ``panel_1d`` (``load_panel``) UNION the ``panel_1d_
    delisted`` tree (WP-12b, DEC-70), on one dense day/symbol grid with
    symbols sorted GLOBALLY across both trees -- the same single
    deterministic ordering ``load_panel``'s module docstring already
    promises, just extended over the union symbol set. A symbol present
    in BOTH trees is a loud ``PanelLoadError`` (a delisted symbol must
    NEVER also be a live ``panel_1d`` symbol -- that would double-count it
    and silently corrupt every downstream K(t)/IC/N_eff figure).

    ``delisted_manifest_path`` must exist (a caller only reaches this
    function because it explicitly asked for the union path, e.g.
    ``--include-delisted`` -- a missing delisted tree is then a loud
    precondition failure, not a silent fall-back to survivors-only;
    contrast ``load_panel``'s own MISSING/EMPTY-is-expected discipline,
    which is about individual (symbol, year) gaps within an existing
    manifest, not a whole missing tree).

    Symbol selection on the delisted side defaults to
    ``delisted_symbols_with_history``'s "usable" set (excludes NO_HISTORY-
    only symbols, see that function's docstring); pass ``delisted_symbols``
    explicitly to override (e.g. a test fixture with a hand-picked set).

    Returns everything ``load_panel`` returns (on the UNION day/symbol
    grid) plus: ``last_alive_day`` (``[n_symbols]``, ISO date string or
    ``None`` per symbol -- the registered delisting date for a delisted
    symbol, ``None`` for a survivor), ``is_delisted`` (``[n_symbols]``
    bool), ``delisted_symbols`` (sorted list), ``n_symbols_survivors``,
    ``n_symbols_delisted``.
    """
    surv = load_panel(base_dir, manifest_path, year_start=year_start, year_end=year_end,
                       as_of=as_of, symbols=symbols, allow_partial=allow_partial)

    delisted_manifest_path = Path(delisted_manifest_path)
    if not delisted_manifest_path.is_file():
        raise PanelLoadError(
            f"panel_1d_delisted manifest not found at {delisted_manifest_path} -- "
            "run scripts/wp12_delisting.py --fetch-delisted-panel first (WP-12b, DEC-70) "
            "before --include-delisted")

    if delisted_symbols is not None:
        dsyms = sorted(delisted_symbols)
        no_history_only: list[str] = []
    else:
        dsyms, no_history_only = delisted_symbols_with_history(delisted_manifest_path)

    # RELISTINGS (DEC-72; real tree 2026-09-21: ICXUSDT delisted and later
    # relisted under the same name). A symbol in BOTH trees is a relisting
    # iff its delisted episode ends strictly BEFORE the survivor listing
    # starts -- then it becomes TWO panel columns: the survivor column
    # keeps the symbol name, the earlier episode becomes
    # ``<symbol>#delisted`` with its own last_alive_day. Any overlap in
    # days between the two episodes stays a loud error (a contract cannot
    # be alive twice on the same day).
    overlap = sorted(set(surv["symbols"]) & set(dsyms))
    relisted: list[str] = []

    if not dsyms:
        out = dict(surv)
        out["last_alive_day"] = [None] * len(surv["symbols"])
        out["is_delisted"] = np.zeros(len(surv["symbols"]), dtype=bool)
        out["delisted_symbols"] = []
        out["n_symbols_survivors"] = len(surv["symbols"])
        out["n_symbols_delisted"] = 0
        out["n_no_history_only"] = len(no_history_only)
        return out

    delisted = load_panel(delisted_base, delisted_manifest_path, year_start=year_start,
                           year_end=year_end, as_of=as_of, symbols=dsyms, allow_partial=allow_partial)

    if overlap:
        conflicts = []
        for s_ in overlap:
            js = surv["symbols"].index(s_)
            jd = delisted["symbols"].index(s_)
            surv_days = [d for d, v in zip(surv["day_index"], surv["close"][:, js]) if not math.isnan(v)]
            del_days = [d for d, v in zip(delisted["day_index"], delisted["close"][:, jd]) if not math.isnan(v)]
            if not surv_days or not del_days or max(del_days) >= min(surv_days):
                conflicts.append(s_)
            else:
                relisted.append(s_)
        if conflicts:
            raise PanelLoadError(
                f"{len(conflicts)} symbol(s) present in BOTH panel_1d and panel_1d_delisted with "
                f"OVERLAPPING trading days -- a contract cannot be alive twice on the same day: "
                f"{conflicts[:20]}")
        delisted = dict(delisted)
        delisted["symbols"] = [f"{s_}#delisted" if s_ in relisted else s_ for s_ in delisted["symbols"]]

    all_symbols = sorted(surv["symbols"] + delisted["symbols"])
    all_days = sorted(set(surv["day_index"]) | set(delisted["day_index"]))
    n_days, n_symbols = len(all_days), len(all_symbols)
    day_pos = {d: i for i, d in enumerate(all_days)}
    sym_pos = {s: j for j, s in enumerate(all_symbols)}
    dates = [(_EPOCH + timedelta(days=d)).isoformat() for d in all_days]

    dst = {
        "close": np.full((n_days, n_symbols), np.nan, dtype=np.float64),
        "turnover": np.full((n_days, n_symbols), np.nan, dtype=np.float64),
        "funding_n": np.full((n_days, n_symbols), np.nan, dtype=np.float64),
        "funding_sum": np.full((n_days, n_symbols), np.nan, dtype=np.float64),
    }
    _scatter_panel(dst, day_pos, sym_pos, surv)
    _scatter_panel(dst, day_pos, sym_pos, delisted)

    delisting_dates = load_delisting_dates(delisting_dates_path) if delisting_dates_path else {}
    is_delisted = np.zeros(n_symbols, dtype=bool)
    last_alive_day: list[str | None] = [None] * n_symbols
    missing_dates = []
    for s in delisted["symbols"]:
        j = sym_pos[s]
        is_delisted[j] = True
        d = delisting_dates.get(s.split("#", 1)[0])
        if d is None:
            missing_dates.append(s)
        else:
            last_alive_day[j] = d.isoformat()
    if missing_dates:
        raise PanelLoadError(
            f"{len(missing_dates)} delisted symbol(s) loaded from panel_1d_delisted have no "
            f"entry in delisting_dates.json -- last_alive_day would be undefined "
            f"(pass delisting_dates_path): {missing_dates[:20]}")

    return {
        "symbols": all_symbols, "dates": dates, "day_index": all_days,
        "close": dst["close"], "turnover": dst["turnover"],
        "funding_n": dst["funding_n"], "funding_sum": dst["funding_sum"],
        "n_partitions_used": surv["n_partitions_used"] + delisted["n_partitions_used"],
        "status_counts": {"survivors": surv["status_counts"], "delisted": delisted["status_counts"]},
        "allow_partial": allow_partial, "year_range": [year_start, year_end], "as_of": as_of.isoformat(),
        "last_alive_day": last_alive_day, "is_delisted": is_delisted,
        "delisted_symbols": delisted["symbols"], "n_symbols_survivors": len(surv["symbols"]),
        "n_symbols_delisted": len(delisted["symbols"]), "n_no_history_only": len(no_history_only),
        "relisted_symbols": sorted(relisted),
    }


def weekly_returns_and_mask_union(
    panel: dict[str, Any], last_alive_day: list[str | None], *,
    min_weeks_history: int = pit_universe.MIN_WEEKS_HISTORY,
) -> dict[str, Any]:
    """Like ``weekly_returns_and_mask``, but for a UNION panel
    (``load_panel_union``'s output) carrying delisted symbols alongside
    survivors.

    **Delisting-week convention (WP-12b task brief item 2 -- documented
    here as the single source of truth for this repo):**

      * A delisted symbol's alive mask ends at the WEEK CONTAINING its
        registered delisting date (``last_alive_day[j]``) -- that week is
        the LAST week the symbol is a member of the universe, never
        later. This is a defensive CAP on the real observed
        ``last_week`` computed from its close series (``delisted_panel``'s
        fetch never writes klines past ``delist_date`` in the first
        place, so the cap is normally a no-op; it exists so a data-layer
        change elsewhere can never silently extend a dead symbol's
        membership).
      * The delisting week's OWN return is the REAL, observed
        last-traded-price return -- the exact same "closed at the last
        traded price" rule ``pit_universe``'s module docstring already
        states for any symbol's last week. There is NO overwrite with an
        assumed total-loss (-100%) return anywhere in this function.
        ``pit_universe.naive_delisting_overlay`` is the DELIBERATELY WRONG
        reference estimator that performs that overwrite (for the DEC-39
        adversarial test only, per its own docstring) -- this function
        never calls it and never reproduces its behaviour.
      * Because every (signal, outcome) pair at week ``t`` downstream
        (``pit_universe.weekly_ic_series``/``momentum_ic_series``,
        ``wp12_delisting.survivorship_fixture.weekly_signal_outcome_
        pairs``) requires ``alive[t] & alive[t+1]``, a delisted symbol's
        delisting week is AUTOMATICALLY excluded as a signal week too (no
        week-``t+1`` outcome exists for it, since ``alive`` is False from
        the week after delisting onward) -- it simply stops contributing
        after its last alive week. No special-cased outcome value is
        substituted anywhere.
      * NO return imputation of any kind (a -100% overlay or similar
        would be a SEPARATE, not-yet-registered choice, per the task
        brief -- this function implements ONLY the cap + natural-alive-
        mask-exclusion convention above, nothing else).
    """
    symbols = panel["symbols"]
    weeks, close_mat, returns, first_week, last_week = _daily_close_to_weekly(panel)
    n_weeks = len(weeks)
    week_pos = {w: i for i, w in enumerate(weeks)}

    capped_last_week = last_week.copy()
    for j, lad in enumerate(last_alive_day):
        if lad is None:
            continue
        delist_week = pit_universe.iso_week_start(date.fromisoformat(lad)).isoformat()
        cap_idx = week_pos.get(delist_week)
        if cap_idx is None:
            # the delisting week itself falls outside this panel's loaded
            # week grid (e.g. the union's day range is shorter than the
            # register implies) -- cap at the last week actually in range,
            # NEVER extend membership past what this panel can see.
            cap_idx = n_weeks - 1
        if capped_last_week[j] > cap_idx:
            capped_last_week[j] = cap_idx

    alive = pit_universe.pit_alive_mask(first_week, capped_last_week, n_weeks,
                                         min_weeks_history=min_weeks_history)
    return {"weeks": weeks, "close": close_mat, "returns": returns, "alive": alive,
            "first_week": first_week, "last_week": capped_last_week,
            "last_week_uncapped": last_week, "symbols": symbols,
            "last_alive_day": last_alive_day}


def union_range_fingerprint(
    base_dir: Path | str, delisted_base: Path | str,
    survivor_symbols: list[str], delisted_symbols: list[str], *,
    year_start: int, year_end: int, as_of: date,
) -> dict[str, Any]:
    """Range fingerprint over the UNION panel (survivors tree + delisted
    tree, WP-12b/DEC-70). Computed as a SHA-256 over the two trees' OWN
    ``combined_range_fingerprint`` results (each fingerprinted from its
    own base_dir -- a delisted symbol lives under a physically different
    tree, ``data/panel_1d_delisted/`` by convention) plus the sorted union
    symbol set -- never merges the two trees' file layouts into one
    lookup, so a survivors-only reader's fingerprint stays unaffected and
    independently reproducible."""
    surv_fp = combined_range_fingerprint(base_dir, survivor_symbols, year_start, year_end, as_of=as_of)
    del_fp = combined_range_fingerprint(
        delisted_base, [d.split("#", 1)[0] for d in delisted_symbols], year_start, year_end, as_of=as_of)
    h = hashlib.sha256()
    h.update(surv_fp["sha256"].encode("ascii"))
    h.update(del_fp["sha256"].encode("ascii"))
    all_symbols = sorted(set(survivor_symbols) | set(delisted_symbols))
    h.update(json.dumps(all_symbols).encode("utf-8"))
    return {"symbols": all_symbols, "year_range": [year_start, year_end],
            "n_partitions": surv_fp["n_partitions"] + del_fp["n_partitions"],
            "sha256": h.hexdigest(),
            "survivors_fingerprint": surv_fp["sha256"], "delisted_fingerprint": del_fp["sha256"]}


# ----------------------------------------------------------------------------
# artifact helpers
# ----------------------------------------------------------------------------

def sha256_file(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path: Path | str, header: list[str], rows: list[list[Any]]) -> dict[str, str]:
    path = Path(path)
    if "data/harvest" in path.as_posix():
        raise PanelLoadError(f"refusing to write under data/harvest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return {"path": str(path), "sha256": sha256_file(path)}
