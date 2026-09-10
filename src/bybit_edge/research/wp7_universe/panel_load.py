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

from . import panel_store, pit_universe

__all__ = [
    "PanelLoadError", "load_panel_symbols", "load_panel",
    "combined_range_fingerprint", "weekly_returns_and_mask",
    "momentum_signal", "k_per_week_summary", "funding_deadzone_census",
    "funding_autocorrelation", "delisting_cohorts", "stress_weeks",
    "sha256_file", "write_csv",
]

_EPOCH = date(1970, 1, 1)

#: DEC-59: Bybit's interest term I = 0.01%/8h, normalised per settlement by
#: the symbol-day's OWN interval (derived from the observed ``funding_n``,
#: never assumed -- DEC-59's "4h/8h ist die Heterogenitaet, nicht 1h/8h"
#: finding is exactly why this is measured per day, not looked up once).
I_PER_8H = 0.0001
#: funding_n -> interval-minutes map for the interval classes DEC-59 found
#: on the real book (240/480/60 min); any other observed funding_n is
#: reported as its own bucket, never silently folded into one of these.
_FUNDING_N_TO_MINUTES: dict[int, int] = {24: 60, 6: 240, 3: 480}


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

def weekly_returns_and_mask(
    panel: dict[str, Any], *, min_weeks_history: int = pit_universe.MIN_WEEKS_HISTORY,
) -> dict[str, Any]:
    """Daily ``panel`` (from ``load_panel``) -> weekly closes/returns/PIT
    alive mask, all ``[n_weeks, n_symbols]`` (ISO-week rows, ascending,
    ``panel['symbols']`` column order). A gap never manufactures a weekly
    return (only CONSECUTIVE week indices get one, same discipline as
    ``pair_corr.log_returns``)."""
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

    alive = pit_universe.pit_alive_mask(first_week, last_week, n_weeks,
                                         min_weeks_history=min_weeks_history)
    return {"weeks": all_weeks, "close": close_mat, "returns": returns, "alive": alive,
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
