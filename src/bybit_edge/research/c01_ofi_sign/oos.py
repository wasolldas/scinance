"""H-05b OOS confirmation path for the inverse OFI-sign reading (KAPITALFREI).

This module is the **out-of-sample confirmation** runner for H-05b (registry
``scinance2-impl/state/hypothesis_registry.md`` + DEC-15). It is deliberately
SEPARATE from ``driver.py`` so the GL-007-bearing H-05 path stays untouched.

Difference from ``driver.run`` (H-05):
  * Data source: the read-only harvester backfill (Hive tree under
    ``data/harvest/raw/bybit/publicTrade/symbol=<SYM>/date=<d>/``), NOT the
    collector DuckDB. Read directly with DuckDB (backfill single-trade JSON
    form), no dependency on the harvester scripts.
  * Windows: EXPLICIT, pre-registered by date (DEC-15) — window A from
    2026-04-15, window B from 2026-05-15, first ``max_ticks`` per symbol each.
    NOT the "most recent N x cap" split of ``driver.split_windows``.
  * Gate framing: the H-05b INVERSE reading. The payload adds a per-(symbol,
    delta) >= 2-window inverse-consistency rollup (gate-neutral; the
    gate-auditor adjudicates against H-05b). The discovery cell (ETHUSDT,
    June, delta 1 s) is excluded BY CONSTRUCTION because the OOS data is
    April/May only (registry rules 1-3, DEC-15).

KAPITALFREI: pure sign / correlation test (identical to H-05). No friction,
bps, edge, PnL or Sharpe column. The runner renders NO overall verdict.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .driver import TradeArrays, WindowSymbolResult, _build_variants
from .ofi import DEFAULT_GRID_MS, DEFAULT_LAGS_S
from .sign_test import (
    ABS_CORR_FLOOR,
    FDR_ALPHA,
    HIT_RATE_FLOOR,
    SURROGATE_P_MAX,
    benjamini_hochberg,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-05b"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
MIN_WINDOWS = 2  # registered (>= 2 disjoint windows, discovery cell excluded)

#: H-05 default tick cap (registry / DEC-11 / DEC-15: 300k per symbol per window).
WINDOW_MAX_TICKS = 300_000

#: The discovery cell, excluded by construction (April/May OOS contains no June).
DISCOVERY_CELL = "ETHUSDT / June-collector w0 / delta=1s (not present in April-May OOS)"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_]+$")


class DataError(RuntimeError):
    """Raised when the harvester window cannot be loaded."""


# ----------------------------------------------------------------------------
# Harvester raw-tree loader (read-only, backfill single-trade JSON form)
# ----------------------------------------------------------------------------

def _date_dirs(start: str, n_days: int) -> list[str]:
    """List ``YYYY-MM-DD`` strings from ``start`` over ``n_days`` (start + spill)."""
    if not _DATE_RE.match(start):
        raise DataError(f"invalid start date (want YYYY-MM-DD): {start!r}")
    y, m, d = (int(x) for x in start.split("-"))
    d0 = date(y, m, d)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(max(1, n_days))]


def _midnight_ms(start: str) -> int:
    """UTC midnight epoch-ms for a ``YYYY-MM-DD`` date."""
    y, m, d = (int(x) for x in start.split("-"))
    dt = datetime(y, m, d, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def load_harvest_window(
    base_dir: Path | str,
    symbol: str,
    start_date: str,
    *,
    max_ticks: int = WINDOW_MAX_TICKS,
    spill_days: int = 1,
    exchange: str = "bybit",
    stream: str = "publicTrade",
) -> TradeArrays:
    """Load the first ``max_ticks`` ticks at/after ``start_date`` 00:00 UTC.

    Reads the harvester raw Hive tree directly with DuckDB. Handles the
    BACKFILL single-trade JSON form (keys ``side``/``price``/``size``) with a
    fallback to the LIVE per-trade keys (``S``/``p``/``v``) for robustness;
    ``ts_exchange_ms`` is taken from the dedicated column. Side is normalised to
    exactly ``"Buy"``/``"Sell"`` (the OFI estimator treats anything != ``"Buy"``
    as a sell, so buy-variants MUST map to ``"Buy"``).

    Read-only: never writes into the harvester tree (Schutzgut-Prinzip).
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    base = Path(base_dir)
    dirs = _date_dirs(start_date, 1 + max(0, spill_days))
    globs = [
        str(base / "raw" / exchange / stream / f"symbol={symbol}" / f"date={d}" / "*.parquet")
        for d in dirs
    ]
    present = [g for g in globs if list(Path(g).parent.glob("*.parquet"))]
    if not present:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{symbol} in dates {dirs} under {base}"
        )
    start_ms = _midnight_ms(start_date)
    file_list = "[" + ", ".join("'" + g.replace("'", "''") + "'" for g in present) + "]"
    sql = f"""
        SELECT ts_exchange_ms AS ts,
               CASE
                 WHEN lower(COALESCE(json_extract_string(payload_json,'$.side'),
                                     json_extract_string(payload_json,'$.S'))) = 'buy'  THEN 'Buy'
                 WHEN lower(COALESCE(json_extract_string(payload_json,'$.side'),
                                     json_extract_string(payload_json,'$.S'))) = 'sell' THEN 'Sell'
                 ELSE COALESCE(json_extract_string(payload_json,'$.side'),
                               json_extract_string(payload_json,'$.S'))
               END AS side,
               CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                             json_extract_string(payload_json,'$.p')) AS DOUBLE) AS price,
               CAST(COALESCE(json_extract_string(payload_json,'$.size'),
                             json_extract_string(payload_json,'$.v')) AS DOUBLE) AS volume
        FROM read_parquet({file_list}, hive_partitioning=1, union_by_name=1)
        WHERE ts_exchange_ms IS NOT NULL AND ts_exchange_ms >= {start_ms}
          AND json_extract_string(payload_json,'$.side') IS NOT NULL
              OR json_extract_string(payload_json,'$.S') IS NOT NULL
        ORDER BY ts_exchange_ms
        LIMIT {int(max_ticks)}
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    if not rows:
        raise DataError(f"window {symbol}@{start_date} loaded 0 rows (start_ms={start_ms})")
    ts = np.array([r[0] for r in rows], dtype=np.float64)
    side = np.array([str(r[1] or "") for r in rows], dtype=object)
    price = np.array([r[2] for r in rows], dtype=np.float64)
    volume = np.array([r[3] for r in rows], dtype=np.float64)
    # drop rows with NaN price/volume (defensive against malformed payloads)
    good = np.isfinite(price) & np.isfinite(volume)
    n_bad = int((~good).sum())
    if n_bad:
        print(f"[h05b] {symbol}@{start_date}: dropped {n_bad} rows with NaN price/volume",
              file=sys.stderr, flush=True)
        ts, side, price, volume = ts[good], side[good], price[good], volume[good]
    if ts.size == 0:
        raise DataError(f"window {symbol}@{start_date} empty after NaN filter")
    n_buy = int(np.sum(side == "Buy"))
    print(
        f"[h05b] {symbol}@{start_date}: {ts.size} ticks (cap {max_ticks}), "
        f"buy={n_buy} sell={ts.size - n_buy}, "
        f"span {int(ts[0])}..{int(ts[-1])} ms",
        file=sys.stderr, flush=True,
    )
    return TradeArrays(ts=ts, price=price, volume=volume, side=side)


# ----------------------------------------------------------------------------
# OOS run over explicit pre-registered windows
# ----------------------------------------------------------------------------

def run_oos(
    symbol_windows: dict[str, list[TradeArrays]],
    *,
    window_labels: tuple[str, ...],
    lags_s: tuple[int, ...] = DEFAULT_LAGS_S,
    grid_ms: float = DEFAULT_GRID_MS,
    n_surrogates: int = 200,
    seed: int = 42,
    max_ticks_per_window: int = WINDOW_MAX_TICKS,
    source: str = "",
) -> dict[str, Any]:
    """Run the inverse OFI-sign gate over EXPLICIT pre-registered windows.

    ``symbol_windows[sym]`` is the ordered list of windows (>= 2) for that
    symbol. Mirrors ``driver.run`` cell-by-cell (reusing ``_build_variants``),
    but with H-05b framing + a per-(symbol, delta) >= 2-window inverse-
    consistency rollup. Gate-neutral: the gate-auditor adjudicates.
    """
    symbols = tuple(symbol_windows.keys())
    n_windows = max((len(w) for w in symbol_windows.values()), default=0)
    if n_windows < MIN_WINDOWS:
        raise DataError(f"H-05b needs >= {MIN_WINDOWS} windows, got {n_windows}")

    all_results: list[WindowSymbolResult] = []
    for sym in symbols:
        windows = symbol_windows[sym]
        print(
            f"[h05b] {sym}: {len(windows)} explicit window(s) "
            f"(deltas={list(lags_s)}s, grid={grid_ms:g}ms, surrogates={n_surrogates})",
            file=sys.stderr, flush=True,
        )
        for wi, win in enumerate(windows):
            all_results.append(_build_variants(
                win, symbol=sym, window_index=wi, n_windows=len(windows),
                lags_s=lags_s, grid_ms=grid_ms,
                n_surrogates=n_surrogates, seed=seed,
            ))

    # BH-FDR over the WHOLE F-OFI-INV family (all delta x symbol x window).
    flat = [v for r in all_results for v in r.variants]
    p_values = [float(v["surrogate_p"]) for v in flat]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for v, rej in zip(flat, rejected):
        v["fdr_significant"] = bool(rej)
        sd = int(v["sign_direction"])
        mag_ok = (v["abs_corr"] >= ABS_CORR_FLOOR) or (v["hit_rate"] <= (1.0 - HIT_RATE_FLOOR))
        v["magnitude_floor_met"] = bool(mag_ok)
        v["abs_corr_floor_met"] = bool(v["abs_corr"] >= ABS_CORR_FLOOR)
        # Inverse hit-rate floor: mirror of H-05's 0.53 -> <= 0.47.
        v["inverse_hit_rate_floor_met"] = bool(v["hit_rate"] <= (1.0 - HIT_RATE_FLOOR))
        # INVERSE significance per H-05b: negative sign, FDR sig, magnitude floor.
        v["inverse_significant"] = bool(sd < 0 and v["fdr_significant"] and mag_ok)

    # Per-(symbol, delta) >= 2-window inverse-consistency rollup (gate core).
    by_cell: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for r in all_results:
        for v in r.variants:
            key = (r.symbol, int(v["delta_s"]) if "delta_s" in v else _delta_from_label(v["label"]))
            by_cell.setdefault(key, []).append({"window_index": r.window_index, **v})
    consistency: list[dict[str, Any]] = []
    for (sym, delta), cells in sorted(by_cell.items()):
        n_inv = sum(1 for c in cells if c["inverse_significant"])
        inv_windows = sorted(c["window_index"] for c in cells if c["inverse_significant"])
        consistency.append({
            "symbol": sym,
            "delta_s": delta,
            "n_windows_measured": len(cells),
            "n_windows_inverse_significant": n_inv,
            "inverse_significant_windows": inv_windows,
            # >= 2 disjoint windows inverse-significant => inverse-consistent
            "inverse_consistent": bool(n_inv >= MIN_WINDOWS),
        })

    n_fdr_sig = sum(1 for v in flat if v["fdr_significant"])
    any_inverse_consistent = any(c["inverse_consistent"] for c in consistency)
    n_inverse_consistent_cells = sum(1 for c in consistency if c["inverse_consistent"])

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(symbols),
        "window_labels": list(window_labels),
        "n_windows": n_windows,
        "n_surrogates": n_surrogates,
        "seed": seed,
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": "F-OFI-INV",
        "grid_ms": grid_ms,
        "lags_s": list(lags_s),
        "max_ticks_per_window": int(max_ticks_per_window),
        "discovery_cell": DISCOVERY_CELL,
        "discovery_cell_excluded_by_construction": True,
        "gate_thresholds": {
            "surrogate_p_max": SURROGATE_P_MAX,
            "abs_corr_floor": ABS_CORR_FLOOR,
            "inverse_hit_rate_floor": round(1.0 - HIT_RATE_FLOOR, 4),
            "min_windows": MIN_WINDOWS,
            "negative_sign_required_for_weiter": True,
        },
        "fdr_p_crit": p_crit,
        "n_fdr_significant": n_fdr_sig,
        # Gate-neutral family-level observation flags (gate-auditor adjudicates):
        "any_inverse_consistent": bool(any_inverse_consistent),
        "n_inverse_consistent_cells": int(n_inverse_consistent_cells),
        "inverse_consistency": consistency,
        "results": [
            {
                "symbol": r.symbol,
                "window_index": r.window_index,
                "window_label": window_labels[r.window_index] if r.window_index < len(window_labels) else "",
                "t0_ms": r.t0_ms,
                "t1_ms": r.t1_ms,
                "variants": r.variants,
            }
            for r in all_results
        ],
    }


def _delta_from_label(label: str) -> int:
    """Extract the integer delta seconds from a ``..._d<delta>s`` variant label."""
    m = re.search(r"_d(\d+)s$", label)
    return int(m.group(1)) if m else -1


# ----------------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------------

def render_markdown_oos(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# C-01 OFI-Vorzeichen INVERSE Lesart — H-05b OOS-Konfirmation (KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}` (+ DEC-15)")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Symbole: {', '.join(payload['symbols'])})")
    L.append(f"- **Fenster (vorregistriert):** {', '.join(payload['window_labels'])} "
             f"· je {payload['max_ticks_per_window']} Ticks/Symbol")
    L.append(f"- **delta-Lags:** {payload['lags_s']} s · **Grid:** {payload['grid_ms']:g} ms · "
             f"**Surrogates:** {payload['n_surrogates']} · **Seed:** {payload['seed']}")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} · **BH-FDR alpha:** {payload['fdr_alpha']} "
             f"· **p_crit:** {payload['fdr_p_crit']:.4f}")
    L.append(f"- **Entdeckungszelle ausgeschlossen (per Konstruktion):** {payload['discovery_cell']}")
    L.append(f"- **KAPITALFREI:** ja — reiner Vorzeichen-/Korrelations-Test, keine bps/Edge/PnL.")
    L.append("")
    L.append("> Gate-Urteil faellt der gate-auditor gegen H-05b. WEITER (inverse Mess-Existenz) "
             "verlangt: sign=- UND p<=0.05 (BH-FDR F-OFI-INV) UND inverse-Konsistenz in >=2 "
             "disjunkten Fenstern (Entdeckungszelle ausgeschlossen) UND |corr|>="
             f"{payload['gate_thresholds']['abs_corr_floor']} ODER Hit-Rate<="
             f"{payload['gate_thresholds']['inverse_hit_rate_floor']}. Hartes Ein-Fenster-DROP, "
             "kein GRAUBEREICH.")
    L.append("")
    L.append("## Inverse-Konsistenz je (Symbol, delta) — Gate-Kern")
    L.append("")
    L.append("| Symbol | delta (s) | Fenster gemessen | Fenster inverse-sig | inverse-Fenster | inverse-konsistent (>=2) |")
    L.append("|---|---:|---:|---:|---|---|")
    for c in payload["inverse_consistency"]:
        L.append(f"| {c['symbol']} | {c['delta_s']} | {c['n_windows_measured']} | "
                 f"{c['n_windows_inverse_significant']} | {c['inverse_significant_windows']} | "
                 f"{'JA' if c['inverse_consistent'] else 'nein'} |")
    L.append("")
    L.append(f"**Inverse-konsistente Zellen (>=2 Fenster):** {payload['n_inverse_consistent_cells']} "
             f"· **mind. eine inverse-konsistent:** {'ja' if payload['any_inverse_consistent'] else 'nein'}")
    L.append("")
    L.append("## Detail je Fenster / Symbol / delta")
    for r in payload["results"]:
        L.append("")
        L.append(f"### {r['symbol']} — Fenster {r['window_index']} "
                 f"({r.get('window_label','')}) — {int(r['t0_ms'])}..{int(r['t1_ms'])} ms")
        L.append("")
        L.append("| delta (s) | n | corr | sign | \\|corr\\| | hit | surr_p | FDR-sig | inverse-sig |")
        L.append("|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|")
        for v in r["variants"]:
            sgn = "+" if int(v["sign_direction"]) > 0 else ("-" if int(v["sign_direction"]) < 0 else "0")
            dlt = _delta_from_label(v["label"])
            L.append(
                f"| {dlt} | {v.get('n_pairs','?')} | {v['corr']:+.4f} | {sgn} | "
                f"{v['abs_corr']:.4f} | {v['hit_rate']:.3f} | {v['surrogate_p']:.4f} | "
                f"{'ja' if v['fdr_significant'] else 'nein'} | "
                f"{'JA' if v['inverse_significant'] else 'nein'} |"
            )
    L.append("")
    L.append("*Erzeugt von `c01_ofi_sign/oos.py` (H-05b OOS, read-only Harvester-Backfill, "
             "DEC-15). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-05b.*")
    return "\n".join(L)
