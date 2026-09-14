"""WP-12 -- own small ``panel_1d`` reader for the survivorship fixture.

Deliberately does NOT import ``wp7_universe.panel_load`` (a file the build
brief marks as concurrently edited by another builder) -- this is a
independent, minimal re-derivation of the same read path, built only from
``wp7_universe.panel_store`` (read-only, on-disk layout + manifest) and
``wp7_universe.pit_universe`` (read-only, PIT membership rule + weekly
aggregation helpers). It reads FEWER columns than ``panel_load.load_panel``
(only ``close``, since the survivorship fixture only needs weekly returns)
and skips several of that module's census-only derivations (funding
census, k_per_week summary, etc.) -- this is a narrower tool for a
narrower job, not a drop-in replacement.

Same loud-fail discipline as the rest of WP-7/WP-12: a manifest carrying
any PARTIAL/FAILED partition for the requested (symbol, year) universe
refuses to load unless the caller passes ``allow_partial=True`` -- WP-12's
own report then carries that label forward (never silently hidden).
"""
from __future__ import annotations

import math
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from ..wp7_universe import panel_store, pit_universe

__all__ = ["PanelReadError", "load_surviving_symbols", "load_daily_closes", "weekly_returns_and_alive"]

_EPOCH = date(1970, 1, 1)


class PanelReadError(RuntimeError):
    """Loud failure reading panel_1d for the survivorship fixture."""


def load_surviving_symbols(manifest_path: Path | str) -> list[str]:
    """All distinct symbols recorded in the panel_1d manifest, sorted --
    the canonical column order every array here uses (mirrors
    ``panel_load.load_panel_symbols``' ordering discipline independently)."""
    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        raise PanelReadError(
            f"panel_1d manifest not found at {manifest_path} -- WP-7 fetch has not run "
            "on this machine (real network required, PRD 4.1); the survivorship fixture "
            "cannot build the 'without delisted symbols' baseline without it")
    con = sqlite3.connect(f"file:{manifest_path.as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT DISTINCT symbol FROM partitions").fetchall()
    finally:
        con.close()
    return sorted(r[0] for r in rows)


def _partial_or_failed(manifest_path: Path, symbols: list[str], years: list[int]
                        ) -> list[tuple[str, int, str]]:
    con = sqlite3.connect(f"file:{manifest_path.as_posix()}?mode=ro", uri=True)
    try:
        placeholders = ",".join("?" * len(symbols))
        rows = con.execute(
            f"SELECT symbol, year, status FROM partitions WHERE symbol IN "
            f"({placeholders}) AND year BETWEEN ? AND ? AND status IN ('PARTIAL','FAILED')",
            [*symbols, years[0], years[-1]]).fetchall()
    finally:
        con.close()
    return [(s, y, st) for s, y, st in rows]


def load_daily_closes(
    base_dir: Path | str, manifest_path: Path | str, *, year_start: int, year_end: int,
    as_of: date, symbols: list[str] | None = None, allow_partial: bool = False,
) -> dict[str, Any]:
    """Read ``close`` out of every (symbol, year) partition in
    ``[year_start, year_end]`` into a dense ``[n_days, n_symbols]`` array
    (``NaN`` where the symbol has no bar that day) -- the minimal daily
    input the weekly momentum fixture needs, independently re-derived from
    ``panel_store`` (see module docstring)."""
    import pyarrow.parquet as pq

    base_dir = Path(base_dir)
    manifest_path = Path(manifest_path)
    years = list(range(year_start, year_end + 1))
    if symbols is None:
        symbols = load_surviving_symbols(manifest_path)
    symbols = sorted(symbols)
    if not symbols:
        raise PanelReadError(f"no symbols found in manifest {manifest_path}")

    bad = _partial_or_failed(manifest_path, symbols, years)
    if bad and not allow_partial:
        detail = ", ".join(f"{s}/{y}={st}" for s, y, st in bad[:20])
        raise PanelReadError(
            f"{len(bad)} partition(s) PARTIAL/FAILED -- refusing a judgement-bearing "
            f"survivorship-fixture read (pass allow_partial=True to proceed labelled "
            f"'nicht urteilstragend'): {detail}")

    per_symbol_days: dict[str, dict[int, float]] = {}
    all_days: set[int] = set()
    for s in symbols:
        day_rows: dict[int, float] = {}
        for y in years:
            frozen = y < as_of.year
            row = panel_store.manifest_get(manifest_path, s, y)
            if row is None or row["n_rows"] == 0:
                continue
            if row["status"] not in ("DONE", "PARTIAL"):
                continue
            if row["status"] == "PARTIAL" and not allow_partial:
                continue
            path = panel_store.partition_path(base_dir, s, y, frozen=frozen)
            if not path.is_file():
                path = panel_store.partition_path(base_dir, s, y, frozen=not frozen)
                if not path.is_file():
                    continue
            table = pq.read_table(path, columns=["start_ms", "close"])
            cols = table.to_pydict()
            for start_ms, close in zip(cols["start_ms"], cols["close"]):
                day_rows[int(start_ms) // 86_400_000] = close
        if day_rows:
            per_symbol_days[s] = day_rows
            all_days.update(day_rows.keys())

    if not all_days:
        raise PanelReadError(
            f"panel_1d yielded no usable daily closes for {len(symbols)} symbol(s), "
            f"years {year_start}..{year_end}")

    day_idx_sorted = sorted(all_days)
    n_days, n_symbols = len(day_idx_sorted), len(symbols)
    day_pos = {d: i for i, d in enumerate(day_idx_sorted)}
    dates = [(_EPOCH + timedelta(days=d)).isoformat() for d in day_idx_sorted]

    close = np.full((n_days, n_symbols), np.nan, dtype=np.float64)
    for j, s in enumerate(symbols):
        for d, c in per_symbol_days.get(s, {}).items():
            close[day_pos[d], j] = c

    return {"symbols": symbols, "dates": dates, "close": close, "allow_partial": allow_partial}


def weekly_returns_and_alive(
    daily: dict[str, Any], *, min_weeks_history: int = pit_universe.MIN_WEEKS_HISTORY,
) -> dict[str, Any]:
    """Daily ``{symbols, dates, close}`` (from ``load_daily_closes``) ->
    weekly ``returns``/``alive`` (``[n_weeks, n_symbols]``), same PIT rule
    and gap discipline as ``wp7_universe.panel_load.weekly_returns_and_mask``
    -- independently re-derived (see module docstring), built only on top
    of ``pit_universe``'s read-only helpers."""
    symbols, dates, close = daily["symbols"], daily["dates"], daily["close"]
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
        raise PanelReadError("no weekly closes derived from panel (empty daily input)")
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
                continue
            c0, c1 = close_mat[t0, j], close_mat[t1, j]
            if c0 > 0 and c1 > 0:
                returns[t1, j] = math.log(c1 / c0)

    alive = pit_universe.pit_alive_mask(first_week, last_week, n_weeks,
                                         min_weeks_history=min_weeks_history)
    return {"weeks": all_weeks, "returns": returns, "alive": alive, "symbols": symbols}
