"""Read-only driver for the H-09 Risk-Limit-Tier-Bunching mess-gate (F-BUNCH).

Orchestrates the registered estimator (:mod:`estimator`) over 5 symbols x 2
pre-registered calendar windows (W1 = 2026-03-27..2026-05-15, W2 =
2026-05-16..2026-07-04) at ORDER level (the judgement-bearing observation
unit), applies BH-FDR alpha = 0.10 over the F-BUNCH family (10 cells), and
emits a GATE-NEUTRAL payload: every gate criterion is reported INDIVIDUALLY
per cell plus a ``weiter_indication`` flag (H-04b/H-05c convention) — the
driver renders NO overall verdict; the gate-auditor adjudicates against the
H-09 registry entry.

Data source: the read-only harvester backfill Hive tree (junction
``data/harvest``), loaded via :func:`load_window_orders` — the order
aggregation runs INSIDE DuckDB (``GROUP BY ts_exchange_ms, side`` +
``SUM(price*size)``), so raw ticks are never materialised in Python, no
per-window tick cap is needed (audit_h09.md Bugs 1+2 fix), and both window
bounds are enforced in SQL (Bug-9 fix). Only the small per-order notional
array in the estimation-relevant band is retained per window.

KAPITALFREI (registry H-09, ``capital_free=true``): pure structural /
behavioural measurement (notional counts + dimensionless excess-mass ratios).
A tradability follow-up would be a NEW H-09b, NOT implied.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import date as _date
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

# Bestand DataError reuse (read-only; the bestand tick-level loader
# ``load_harvest_window`` stays re-exported for backward compatibility but the
# H-09 CLI now uses :func:`load_window_orders` below, which aggregates inside
# DuckDB and has NO tick cap — silent window truncation is structurally
# impossible; audit_h09.md Bug 1).
from bybit_edge.research.c01_ofi_sign.oos import (  # noqa: F401
    DataError,
    load_harvest_window,
)
from bybit_edge.research.payload_sql import cross_form_dedup_qualify, trade_rows_sql

from .estimator import aggregate_orders, estimate_cell
from .kinks import (
    ASYMMETRY_FLOOR,
    B_MINUS_FLOOR,
    BAND_HI_REL,
    BAND_LO_REL,
    BIN_WIDTH_REL,
    BOOT_P_MAX,
    BUNCH_HI_REL,
    BUNCH_LO_REL,
    CF_EXPECTATION_FLOOR,
    CTRL_HI_REL,
    CTRL_LO_REL,
    EXCLUDE_HI_REL,
    EXCLUDE_LO_REL,
    FDR_ALPHA,
    KINK_PLACEHOLDER_NOTE,
    KINK_PLACEHOLDER_SYMBOLS,
    N_BINS,
    N_BOOTSTRAP,
    N_FLOOR_ORDERS,
    PLACEBO_FRACTIONS,
    POLY_DEGREE,
    REGISTERED_FAMILY_SIZE,
    REGISTERED_PANEL_SYMBOLS,
    REGISTERED_WINDOW_A,
    REGISTERED_WINDOW_B,
    RISK_LIMIT_TIER1_KINK_USDT,
    gate_assumptions_valid,
    panel_matches_registered,
    windows_match_registered,
)
from .stats import benjamini_hochberg

SCHEMA_VERSION = 2
HYPOTHESIS_ID = "H-09"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-BUNCH"
MIN_WINDOWS = 2  # registered: >= 1 symbol must pass in BOTH windows

#: Pre-registered calendar windows (registry H-09, verbatim; single source of
#: truth lives in :mod:`kinks`).
DEFAULT_WINDOW_A = REGISTERED_WINDOW_A
DEFAULT_WINDOW_B = REGISTERED_WINDOW_B

# Retention band for per-order notionals kept in Python (relative to K_s).
# The union of everything the estimator ever touches: the main estimation
# band [0.40, 1.30)*K_s plus the placebo re-estimations at 0.50*K_s / 0.75*K_s
# (their bands are frac*[0.40, 1.30)*K_s, minimum 0.20*K_s) and the exact
# B+ boundary values (kink, 1.05*kink per pseudo-kink, all < 1.30*K_s).
# A small symmetric margin makes the filter a strict SUPERSET of every
# registered quantity except ``n_orders_total``, which is carried as metadata.
_RETAIN_LO_REL = min(PLACEBO_FRACTIONS) * BAND_LO_REL  # 0.20
_RETAIN_HI_REL = BAND_HI_REL                           # 1.30
_RETAIN_MARGIN_REL = 0.005

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_]+$")

__all__ = [
    "DEFAULT_WINDOW_A",
    "DEFAULT_WINDOW_B",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "MIN_WINDOWS",
    "REGISTERED_FAMILY_SIZE",
    "REGISTERED_PANEL_SYMBOLS",
    "DataError",
    "WindowOrders",
    "load_harvest_window",
    "load_window_orders",
    "render_markdown",
    "run",
    "write_outputs",
]


@dataclass
class WindowOrders:
    """Pre-aggregated taker orders of ONE (symbol, window) — the run() input.

    ``notionals`` holds only the per-order USDT notionals inside the retention
    band (estimation band + placebo bands + margin); ``n_orders_total`` /
    ``n_records_raw`` carry the full-window counts. ``window_truncated`` MUST
    be True whenever the loader could not deliver the complete pre-registered
    window (e.g. a capped legacy load) — the driver then invalidates the cell
    AND voids ``gate_valid_assumptions`` (audit_h09.md Bug 1: silent
    truncation must be impossible).
    """

    notionals: np.ndarray          # float64, retention-band per-order notionals
    n_records_raw: int             # raw publicTrade fills in the window
    n_orders_total: int            # order aggregates in the window (pre-filter)
    first_ts_ms: int | None        # first loaded ts_exchange_ms
    last_ts_ms: int | None         # last loaded ts_exchange_ms
    window_truncated: bool = False
    max_ticks: int | None = None   # cap in force, if any (None = uncapped)


def _stable_symbol_offset(symbol: str) -> int:
    """Deterministic per-symbol seed offset (``hash()`` is process-randomised)."""
    return sum(ord(ch) * (i + 1) for i, ch in enumerate(symbol)) % 997


def _utc_midnight_ms(day: str) -> int:
    """UTC midnight epoch-ms for a ``YYYY-MM-DD`` date string."""
    y, m, d = (int(x) for x in day.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def _date_dirs(start_date: str, end_date: str) -> list[str]:
    """All ``YYYY-MM-DD`` partition dates from start to end, both inclusive."""
    for s in (start_date, end_date):
        if not _DATE_RE.match(s):
            raise DataError(f"invalid date (want YYYY-MM-DD): {s!r}")
    d0 = _date.fromisoformat(start_date)
    d1 = _date.fromisoformat(end_date)
    if d1 < d0:
        raise DataError(f"window end {end_date} before start {start_date}")
    return [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]


def load_window_orders(
    base_dir: Path | str,
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    kink: float,
    exchange: str = "bybit",
    stream: str = "publicTrade",
    dedup_cross_form: bool = True,
) -> WindowOrders:
    """Load one full pre-registered window as DuckDB-aggregated taker orders.

    The registered observation unit (publicTrade records with identical
    (symbol, side, ts_exchange_ms) merged into ONE order, notional =
    sum(price*size)) is built INSIDE DuckDB via ``GROUP BY ts_exchange_ms,
    side`` — raw ticks never reach Python, so there is NO tick cap and NO
    silent truncation (audit_h09.md Bugs 1+2). The grouping is also
    deterministic where the previous consecutive-scan over an unstable
    ``ORDER BY ts_exchange_ms`` was not (within-ms Buy/Sell interleavings).

    Both window bounds are enforced in SQL (``start <= ts < end+1d``), so
    window disjointness does not rest on the hive ``date=`` partition labels
    (audit_h09.md Bug 9). Only notionals inside the retention band around
    ``kink`` are returned (everything the estimator touches, see
    ``_RETAIN_*``); full-window counts are carried as metadata.

    BOTH harvester payload forms are read (``payload_sql.trade_rows_sql``):
    the FLAT backfill row is passed through byte-for-byte, and the multi-trade
    LIVE ENVELOPE (``$.data[*]`` / JSON-RPC ``$.params.data[*]``) is expanded
    to one row per trade on the PER-TRADE timestamp (``$.T``/``$.timestamp``).
    The envelope element carries exactly the live keys the extraction below
    already knows (``S``/``p``/``v``), so no extraction expression changes.
    The per-trade timestamp is decisive TWICE here: it is the ORDER grouping
    key (``GROUP BY ts_exchange_ms, side``), so the packet ``ts`` would merge
    every fill of one WS message into a single phantom order.

    DE-DUPLICATION IS REQUIRED HERE and is on by default: the registered
    observation unit is an ORDER notional ``SUM(price*size)`` over a
    (ts, side) group plus a fill COUNT — a trade delivered in BOTH forms on a
    mixed backfill+live day (DATASET.md §9 caveat 4) would double that
    order's notional and shift it across the tier-kink bands, unlike the
    last-price-per-bar loaders (c12/c14) where a duplicate is inert.
    ``dedup_cross_form`` drops an envelope trade whose exchange trade id also
    appears in a flat row of the same scan (see
    ``payload_sql.cross_form_dedup_qualify``); it is a provable no-op on a
    backfill-only or live-only window, so the flat-form results the
    registered H-09 verdicts rest on stay bit-identical.

    Read-only: never writes into the harvester tree (Schutzgut-Prinzip).
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    if not np.isfinite(kink) or kink <= 0:
        raise DataError(f"kink must be a finite positive USDT value, got {kink!r}")
    base = Path(base_dir)
    dirs = _date_dirs(start_date, end_date)
    globs = [
        str(base / "raw" / exchange / stream / f"symbol={symbol}" / f"date={d}" / "*.parquet")
        for d in dirs
    ]
    present = [g for g in globs if list(Path(g).parent.glob("*.parquet"))]
    if not present:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{symbol} in dates "
            f"{dirs[0]}..{dirs[-1]} under {base}"
        )
    start_ms = _utc_midnight_ms(start_date)
    end_ms = _utc_midnight_ms(end_date) + 86_400_000  # end date inclusive
    file_list = "[" + ", ".join("'" + g.replace("'", "''") + "'" for g in present) + "]"
    # One trade per row for BOTH payload forms; the flat branch is a literal
    # pass-through of the parquet row (bit-identity of the registered runs).
    trade_rows = trade_rows_sql(
        f"read_parquet({file_list}, hive_partitioning=1, union_by_name=1)"
    )
    dedup = cross_form_dedup_qualify() if dedup_cross_form else ""
    # NOTE: the side predicate is parenthesised (the bestand loader's
    # ``A AND B OR C`` precedence bug is NOT inherited here) and BOTH window
    # bounds are in the WHERE clause.
    sql = f"""
        SELECT ts_exchange_ms AS ts,
               SUM(price * size) AS notional,
               COUNT(*) AS n_fills
        FROM (
            SELECT ts_exchange_ms,
                   lower(COALESCE(json_extract_string(payload_json, '$.side'),
                                  json_extract_string(payload_json, '$.S'))) AS side,
                   TRY_CAST(COALESCE(json_extract_string(payload_json, '$.price'),
                                     json_extract_string(payload_json, '$.p')) AS DOUBLE) AS price,
                   TRY_CAST(COALESCE(json_extract_string(payload_json, '$.size'),
                                     json_extract_string(payload_json, '$.v')) AS DOUBLE) AS size
            FROM {trade_rows}
            WHERE ts_exchange_ms IS NOT NULL
              AND ts_exchange_ms >= {start_ms} AND ts_exchange_ms < {end_ms}
              AND (json_extract_string(payload_json, '$.side') IS NOT NULL
                   OR json_extract_string(payload_json, '$.S') IS NOT NULL)
            {dedup}
        )
        WHERE price IS NOT NULL AND size IS NOT NULL
        GROUP BY ts_exchange_ms, side
    """
    con = duckdb.connect()
    try:
        res = con.execute(sql).fetchnumpy()
    finally:
        con.close()

    def _col(name: str, dtype: type) -> np.ndarray:
        a = res[name]
        if np.ma.isMaskedArray(a):
            fill = np.nan if np.issubdtype(np.dtype(dtype), np.floating) else 0
            a = a.filled(fill)
        return np.asarray(a, dtype=dtype)

    ts = _col("ts", np.int64)
    notional = _col("notional", np.float64)
    n_fills = _col("n_fills", np.int64)
    if ts.size == 0:
        raise DataError(
            f"window {symbol}@{start_date}..{end_date} loaded 0 orders "
            f"(start_ms={start_ms}, end_ms={end_ms})"
        )
    good = np.isfinite(notional)
    n_bad = int((~good).sum())
    if n_bad:
        print(
            f"[h09] {symbol}@{start_date}..{end_date}: dropped {n_bad} order "
            f"aggregates with non-finite notional",
            file=sys.stderr, flush=True,
        )
        ts, notional, n_fills = ts[good], notional[good], n_fills[good]
    if ts.size == 0:
        raise DataError(
            f"window {symbol}@{start_date}..{end_date} empty after NaN filter"
        )
    n_records_raw = int(n_fills.sum())
    n_orders_total = int(ts.size)
    lo = (_RETAIN_LO_REL - _RETAIN_MARGIN_REL) * float(kink)
    hi = (_RETAIN_HI_REL + _RETAIN_MARGIN_REL) * float(kink)
    keep = (notional >= lo) & (notional <= hi)
    retained = np.ascontiguousarray(notional[keep], dtype=np.float64)
    print(
        f"[h09] {symbol}@{start_date}..{end_date}: {n_records_raw} fills -> "
        f"{n_orders_total} order aggregates (DuckDB GROUP BY, uncapped), "
        f"{retained.size} retained in [{lo:.0f}, {hi:.0f}] USDT, "
        f"span {int(ts.min())}..{int(ts.max())} ms",
        file=sys.stderr, flush=True,
    )
    return WindowOrders(
        notionals=retained,
        n_records_raw=n_records_raw,
        n_orders_total=n_orders_total,
        first_ts_ms=int(ts.min()),
        last_ts_ms=int(ts.max()),
        window_truncated=False,   # no cap exists on this path
        max_ticks=None,
    )


def _as_window_orders(win: Any) -> WindowOrders:
    """Normalise a run() window input to :class:`WindowOrders`.

    Accepts either a :class:`WindowOrders` (CLI path, already DuckDB-
    aggregated) or a legacy trade-array object with ``ts/side/price/volume``
    (tests / synthetic paths) — the latter is aggregated immediately and the
    raw arrays are NOT retained (audit_h09.md Bug 2).
    """
    if isinstance(win, WindowOrders):
        return win
    notionals = aggregate_orders(win.ts, win.side, win.price, win.volume)
    n = int(win.ts.size)
    return WindowOrders(
        notionals=notionals,
        n_records_raw=n,
        n_orders_total=int(notionals.size),
        first_ts_ms=int(win.ts[0]) if n else None,
        last_ts_ms=int(win.ts[-1]) if n else None,
        window_truncated=bool(getattr(win, "window_truncated", False)),
        max_ticks=getattr(win, "max_ticks", None),
    )


def _sentinel_cell(
    sym: str, wi: int, label: str, kink: float | None
) -> dict[str, Any]:
    """p=1.0 sentinel cell for a registered symbol x window that failed to load.

    Keeps the F-BUNCH family at its registered size m=10 (audit_h09.md Bug 3:
    BH must never run anti-conservatively on a silently shrunken family).
    Sentinels can never pass and never make the BH threshold easier.
    """
    return {
        "kink_usdt": float(kink) if kink is not None else None,
        "n_orders_total": 0,
        "n_orders_retained": 0,
        "n_orders_in_band": 0,
        "bin_counts": None,
        "b_minus": None,
        "b_plus": None,
        "b_asymmetry": None,
        "obs_bminus": None,
        "obs_bplus": None,
        "cf_expectation_bminus": None,
        "cf_expectation_bplus": None,
        "degenerate_counterfactual": None,
        "bootstrap_p": 1.0,
        "bootstrap_b_null_sd": None,
        "n_bootstrap": 0,
        "n_floor_met": False,
        "cf_floor_met": False,
        "cell_valid": False,
        "invalid_reason": "sentinel_missing_data (symbol/window failed to load)",
        "placebos": {f"P_{f:.2f}": {"b_minus": None} for f in PLACEBO_FRACTIONS},
        "b_placebo_max": None,
        "sentinel_missing_data": True,
        "symbol": sym,
        "window_index": wi,
        "window_label": label,
        "n_records_raw": 0,
        "first_ts_ms": None,
        "last_ts_ms": None,
        "window_truncated": False,
        "max_ticks": None,
        "kink_is_placeholder": bool(sym in KINK_PLACEHOLDER_SYMBOLS),
    }


def run(
    symbol_windows: dict[str, list[Any]],
    *,
    window_labels: tuple[str, ...],
    kinks: dict[str, float] | None = None,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 42,
    n_floor_orders: int = N_FLOOR_ORDERS,
    cf_expectation_floor: float = CF_EXPECTATION_FLOOR,
    missing_symbols: tuple[str, ...] = (),
    source: str = "",
) -> dict[str, Any]:
    """Run the H-09 bunching gate over explicit pre-registered windows.

    ``symbol_windows[sym]`` is the ordered list of per-window inputs for that
    symbol — either :class:`WindowOrders` (CLI path, DuckDB-aggregated) or
    legacy trade-array objects with ``ts/side/price/volume`` (tests); window
    ``i`` corresponds to ``window_labels[i]``. ``kinks`` overrides the K_s
    dict (tests); by default the module constants (BTC registry-quoted, rest
    PLACEHOLDER) are used.

    ``missing_symbols`` lists REQUESTED symbols that failed to load: they are
    padded into the F-BUNCH family as p=1.0 sentinel cells so BH never runs on
    a silently shrunken family (Bug 3); any sentinel (or a family size other
    than the registered 10) sets ``family_size_deviation`` and voids
    ``gate_valid_assumptions``. A truncated window (``window_truncated``)
    invalidates its cell and also voids ``gate_valid_assumptions`` (Bug 1).
    Panel / window / K_s identity deviations void it too (Bug 4).

    Gate-neutral: reports every criterion individually per cell plus the
    ``weiter_indication`` flag; the gate-auditor adjudicates against H-09.
    """
    kink_map = dict(RISK_LIMIT_TIER1_KINK_USDT if kinks is None else kinks)
    symbols = tuple(symbol_windows.keys())
    missing_symbols = tuple(s for s in missing_symbols if s not in symbols)
    requested_symbols = symbols + missing_symbols
    n_windows = max((len(w) for w in symbol_windows.values()), default=0)
    if n_windows < MIN_WINDOWS:
        raise DataError(f"H-09 needs >= {MIN_WINDOWS} windows, got {n_windows}")

    cells: list[dict[str, Any]] = []
    for sym in symbols:
        if sym not in kink_map:
            raise DataError(f"no K_s kink registered for symbol {sym!r}")
        kink = float(kink_map[sym])
        for wi, win in enumerate(symbol_windows[sym]):
            wo = _as_window_orders(win)
            print(
                f"[h09] {sym} window {wi} ({window_labels[wi] if wi < len(window_labels) else '?'}): "
                f"{wo.n_records_raw} records -> {wo.n_orders_total} order aggregates "
                f"({wo.notionals.size} retained), K_s={kink:g} USDT, "
                f"bootstrap={n_bootstrap}, truncated={wo.window_truncated}",
                file=sys.stderr, flush=True,
            )
            cell = estimate_cell(
                wo.notionals, kink,
                n_bootstrap=n_bootstrap,
                seed=seed + 1000 * wi + _stable_symbol_offset(sym),
                n_floor_orders=n_floor_orders,
                cf_expectation_floor=cf_expectation_floor,
                with_placebos=True,
            )
            cell["symbol"] = sym
            cell["window_index"] = wi
            cell["window_label"] = (
                window_labels[wi] if wi < len(window_labels) else ""
            )
            cell["n_orders_total"] = int(wo.n_orders_total)
            cell["n_orders_retained"] = int(wo.notionals.size)
            cell["n_records_raw"] = int(wo.n_records_raw)
            cell["first_ts_ms"] = wo.first_ts_ms
            cell["last_ts_ms"] = wo.last_ts_ms
            cell["window_truncated"] = bool(wo.window_truncated)
            cell["max_ticks"] = wo.max_ticks
            cell["sentinel_missing_data"] = False
            cell["kink_is_placeholder"] = bool(sym in KINK_PLACEHOLDER_SYMBOLS)
            if wo.window_truncated:
                # Bug-1 fix: a truncated window does NOT measure the
                # pre-registered window — the cell is invalid, loudly.
                cell["cell_valid"] = False
                cell["invalid_reason"] = (
                    "window_truncated (raw-record cap hit; pre-registered "
                    "window not fully loaded)"
                )
            cells.append(cell)
            print(
                f"[h09] {sym} window {wi}: n_band={cell['n_orders_in_band']} "
                f"b-={cell['b_minus']:.3f} b+={cell['b_plus']:.3f} "
                f"p={cell['bootstrap_p']:.4f} placebo_max={cell['b_placebo_max']:.3f} "
                f"valid={cell['cell_valid']}",
                file=sys.stderr, flush=True,
            )

    # Bug-3 fix: registered symbols that failed to load are padded into the
    # family as p=1.0 sentinel cells (one per window) — the F-BUNCH family
    # size never silently shrinks below the registered m.
    for sym in missing_symbols:
        for wi in range(n_windows):
            label = window_labels[wi] if wi < len(window_labels) else ""
            cells.append(_sentinel_cell(sym, wi, label, kink_map.get(sym)))
            print(
                f"[h09] {sym} window {wi}: SENTINEL cell (missing data, p=1.0) "
                f"— family padded, gate_valid_assumptions will be False",
                file=sys.stderr, flush=True,
            )

    # BH-FDR over the WHOLE registered F-BUNCH family (all symbol x window
    # order-level cells — 10 tests in the full run; invalid cells stay in the
    # family with their measured p, sentinel cells with p=1.0; the fixed
    # family size is not shrunk).
    p_values = [c["bootstrap_p"] for c in cells]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for c, rej in zip(cells, rejected):
        c["fdr_significant"] = bool(rej)
        if c.get("sentinel_missing_data"):
            c["boot_p_le_max"] = False
            c["b_minus_floor_met"] = False
            c["asymmetry_met"] = False
            c["placebo_dominance_met"] = False
            c["passed"] = False
            continue
        c["boot_p_le_max"] = bool(c["bootstrap_p"] <= BOOT_P_MAX)
        c["b_minus_floor_met"] = bool(c["b_minus"] >= B_MINUS_FLOOR)
        c["asymmetry_met"] = bool(c["b_asymmetry"] >= ASYMMETRY_FLOOR)
        c["placebo_dominance_met"] = bool(c["b_minus"] > c["b_placebo_max"])
        # All four registered conditions, ONLY on a valid cell:
        c["passed"] = bool(
            c["cell_valid"]
            and c["boot_p_le_max"]
            and c["fdr_significant"]
            and c["b_minus_floor_met"]
            and c["asymmetry_met"]
            and c["placebo_dominance_met"]
        )

    # Per-symbol rollup: WEITER needs >= 1 symbol passing in BOTH windows.
    per_symbol: list[dict[str, Any]] = []
    for sym in requested_symbols:
        sym_cells = [c for c in cells if c["symbol"] == sym]
        measured = [c for c in sym_cells if not c.get("sentinel_missing_data")]
        passed_windows = sorted(c["window_index"] for c in sym_cells if c["passed"])
        k = kink_map.get(sym)
        per_symbol.append({
            "symbol": sym,
            "kink_usdt": float(k) if k is not None else None,
            "kink_is_placeholder": bool(sym in KINK_PLACEHOLDER_SYMBOLS),
            "missing_data": bool(sym in missing_symbols),
            "n_windows_measured": len(measured),
            "n_windows_valid": sum(1 for c in sym_cells if c["cell_valid"]),
            "n_windows_passed": len(passed_windows),
            "passed_windows": passed_windows,
            "passed_both_windows": bool(len(passed_windows) >= MIN_WINDOWS),
        })

    # Power-DROP observation: all cells of a window invalid (registry N-floor).
    all_cells_invalid_by_window = [
        not any(c["cell_valid"] for c in cells if c["window_index"] == wi)
        for wi in range(n_windows)
    ]

    # ------------------------------------------------------------------
    # Composite anti-gaming validity (Bugs 1, 3, 4): run parameters AND
    # panel/window identity AND K_s identity AND family integrity AND
    # untruncated windows. Each component is reported individually.
    # ------------------------------------------------------------------
    n_sentinel_cells = sum(1 for c in cells if c.get("sentinel_missing_data"))
    family_size_deviation = bool(
        n_sentinel_cells > 0 or len(cells) != REGISTERED_FAMILY_SIZE
    )
    any_window_truncated = any(bool(c.get("window_truncated")) for c in cells)
    panel_ok = panel_matches_registered(requested_symbols)
    windows_ok = windows_match_registered(window_labels)
    kinks_ok = all(
        s in RISK_LIMIT_TIER1_KINK_USDT
        and s in kink_map
        and float(kink_map[s]) == float(RISK_LIMIT_TIER1_KINK_USDT[s])
        for s in requested_symbols
    )
    run_params_ok = gate_assumptions_valid(
        n_bootstrap=n_bootstrap,
        poly_degree=POLY_DEGREE,
        n_floor_orders=n_floor_orders,
        cf_expectation_floor=cf_expectation_floor,
    )
    gate_valid = bool(
        gate_assumptions_valid(
            n_bootstrap=n_bootstrap,
            poly_degree=POLY_DEGREE,
            n_floor_orders=n_floor_orders,
            cf_expectation_floor=cf_expectation_floor,
            symbols=requested_symbols,
            window_labels=window_labels,
        )
        and kinks_ok
        and not family_size_deviation
        and not any_window_truncated
    )

    any_symbol_passed_both = any(s["passed_both_windows"] for s in per_symbol)
    # Bug-8 fix: the headline WEITER indication is conditioned on a
    # NON-placeholder K_s symbol — a pass driven only by unverified placeholder
    # kinks must never read as a headline WEITER.
    any_nonplaceholder_passed_both = any(
        s["passed_both_windows"] and not s["kink_is_placeholder"]
        for s in per_symbol
    )
    placeholder_driven_pass_only = bool(
        any_symbol_passed_both and not any_nonplaceholder_passed_both
    )
    weiter_indication = bool(any_nonplaceholder_passed_both and gate_valid)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(symbols),
        "requested_symbols": list(requested_symbols),
        "window_labels": list(window_labels),
        "n_windows": n_windows,
        "observation_unit": (
            "Taker-Order-Aggregat (konsekutive publicTrade-Records gleichen "
            "symbol/side/ts_exchange_ms gemerged), Notional in USDT"
        ),
        "n_bootstrap": n_bootstrap,
        "seed": seed,
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": FDR_FAMILY,
        "kinks_usdt": {s: float(kink_map[s]) for s in symbols},
        "kink_placeholder_symbols": [
            s for s in symbols if s in KINK_PLACEHOLDER_SYMBOLS
        ],
        "kink_placeholder_note": KINK_PLACEHOLDER_NOTE,
        "method": {
            "band_rel": [BAND_LO_REL, BAND_HI_REL],
            "bin_width_rel": BIN_WIDTH_REL,
            "n_bins": N_BINS,
            "poly_degree": POLY_DEGREE,
            "exclusion_rel": [EXCLUDE_LO_REL, EXCLUDE_HI_REL],
            "bunching_window_rel": [BUNCH_LO_REL, BUNCH_HI_REL],
            "control_window_rel": [CTRL_LO_REL, CTRL_HI_REL],
            "placebo_fractions": list(PLACEBO_FRACTIONS),
            "bootstrap": "Residuen-Bootstrap (Chetty et al. 2011), Null b-=0",
        },
        "gate_thresholds": {
            "bootstrap_p_max": BOOT_P_MAX,
            "b_minus_floor": B_MINUS_FLOOR,
            "asymmetry_floor": ASYMMETRY_FLOOR,
            "placebo_dominance": "b_minus > max(b_P1, b_P2)",
            "n_floor_orders": n_floor_orders,
            "cf_expectation_floor": cf_expectation_floor,
            "min_windows": MIN_WINDOWS,
        },
        "registered_n_bootstrap": N_BOOTSTRAP,
        "registered_n_floor_orders": N_FLOOR_ORDERS,
        "registered_cf_expectation_floor": CF_EXPECTATION_FLOOR,
        # Full anti-gaming composite (audit_h09.md Bugs 1/3/4): run parameters
        # AND panel identity AND window identity AND K_s identity AND family
        # integrity (no sentinel/shrunk family) AND no truncated window. This
        # is the flag ``weiter_indication`` is conditioned on.
        "gate_valid_assumptions": gate_valid,
        "gate_valid_assumptions_note": (
            "WEITER nur gueltig bei n_bootstrap >= 500 UND Polynom-Grad 7 UND "
            "N-Floor >= 2000 UND Counterfactual-Floor >= 50 UND Panel = "
            "registrierte 5 Symbole UND Fenster = registrierte W1/W2 UND K_s "
            "= registrierte Werte UND F-BUNCH-Familiengroesse = 10 (keine "
            "Sentinel-Zellen) UND kein Fenster truncated (keine Band-/Bin-/"
            "Placebo-Anpassung, Registry H-09). Abweichung -> "
            "gate_valid_assumptions=false, eine WEITER-Indikation waere ungueltig."
        ),
        # Sub-flags of the composite above (introspection / targeted testing):
        "gate_valid_run_params": bool(run_params_ok),
        "panel_matches_registered": bool(panel_ok),
        "windows_match_registered": bool(windows_ok),
        "kinks_match_registered": bool(kinks_ok),
        "family_size_deviation": bool(family_size_deviation),
        "any_window_truncated": bool(any_window_truncated),
        "n_sentinel_cells": int(n_sentinel_cells),
        "missing_symbols": list(missing_symbols),
        "fdr_p_crit": p_crit,
        "n_fdr_significant": sum(1 for c in cells if c["fdr_significant"]),
        "all_cells_invalid_by_window": all_cells_invalid_by_window,
        # Gate-neutral observation flags (the gate-auditor adjudicates):
        "any_symbol_passed_both_windows": bool(any_symbol_passed_both),
        "any_nonplaceholder_symbol_passed_both_windows": bool(any_nonplaceholder_passed_both),
        "placeholder_driven_pass_only": placeholder_driven_pass_only,
        "weiter_indication": weiter_indication,
        "per_symbol": per_symbol,
        "cells": cells,
    }


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_markdown(payload: dict[str, Any]) -> str:
    """German Markdown report — one criterion per column, per cell (H-09)."""
    L: list[str] = []
    L.append("# H-09 · Risk-Limit-Tier-Bunching Mess-Gate (F-BUNCH, KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}` (+ DEC-19)")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Symbole: {', '.join(payload['symbols'])})")
    L.append(f"- **Fenster (vorregistriert):** {', '.join(payload['window_labels'])}")
    L.append(
        f"- **Beobachtungseinheit:** {payload['observation_unit']}"
    )
    m = payload["method"]
    L.append(
        f"- **Methodik:** Band {m['band_rel']}·K_s, {m['n_bins']} Bins a "
        f"{m['bin_width_rel']}·K_s · Polynom Grad {m['poly_degree']} "
        f"(Ausschluss {m['exclusion_rel']}·K_s) · B- {m['bunching_window_rel']}·K_s, "
        f"B+ {m['control_window_rel']}·K_s · Placebos {m['placebo_fractions']}·K_s "
        f"(NICHT in FDR-Familie) · {m['bootstrap']} ({payload['n_bootstrap']} Reps, "
        f"Seed {payload['seed']})"
    )
    L.append(
        f"- **FDR-Familie:** {payload['fdr_family']} · BH-FDR alpha {payload['fdr_alpha']} "
        f"· p_crit {_fmt(payload['fdr_p_crit'])} · FDR-signifikant: {payload['n_fdr_significant']}"
    )
    L.append(
        f"- **K_s je Symbol (USDT):** "
        + ", ".join(f"{s}={payload['kinks_usdt'][s]:,.0f}" for s in payload["symbols"])
    )
    if payload["kink_placeholder_symbols"]:
        L.append(f"- **PLATZHALTER-WARNUNG:** {payload['kink_placeholder_note']}")
    L.append(
        "- **KAPITALFREI:** ja — reiner Struktur-/Verhaltensfakt (Notional-Zaehlungen, "
        "dimensionslose Excess-Mass-Ratios). Tradability waere NEUE H-09b, NICHT impliziert."
    )
    L.append(
        f"- **gate_valid_assumptions:** {_fmt(payload['gate_valid_assumptions'])} — "
        f"{payload['gate_valid_assumptions_note']}"
    )
    L.append("")
    L.append(
        "> Gate-Urteil faellt der gate-auditor gegen H-09. WEITER verlangt fuer "
        ">= 1 Symbol in BEIDEN Fenstern (gueltige Zelle): Bootstrap-p <= 0,05 "
        "nach BH-FDR alpha=0,10 ueber F-BUNCH UND b- >= 1,0 UND b- - b+ >= 0,5 "
        "UND b- > max(b_P1, b_P2). N-Floor: >= 2.000 Order-Beobachtungen im "
        "Schaetzband UND Counterfactual-Erwartung in B- >= 50, sonst Zelle "
        "ungueltig; alle 5 Zellen eines Fensters ungueltig -> DROP wegen Power. "
        "Hartes Ein-Fenster-DROP, kein GRAUBEREICH. A-priori: DROP "
        "(Rundzahl-Praeferenz)."
    )
    L.append("")
    L.append(
        f"**Mind. ein Symbol besteht BEIDE Fenster:** "
        f"{_fmt(payload['any_symbol_passed_both_windows'])} · "
        f"**WEITER-Indikation (nur bei gueltigen Annahmen):** "
        f"{_fmt(payload['weiter_indication'])} · "
        f"**Alle Zellen ungueltig je Fenster:** {payload['all_cells_invalid_by_window']}"
    )
    L.append("")
    L.append("## Rollup je Symbol")
    L.append("")
    L.append("| Symbol | K_s (USDT) | Platzhalter | Fenster gueltig | Fenster bestanden | beide Fenster |")
    L.append("|---|---:|:---:|---:|---:|:---:|")
    for s in payload["per_symbol"]:
        L.append(
            f"| {s['symbol']} | {s['kink_usdt']:,.0f} | {_fmt(s['kink_is_placeholder'])} "
            f"| {s['n_windows_valid']}/{s['n_windows_measured']} | {s['n_windows_passed']} "
            f"| {_fmt(s['passed_both_windows'])} |"
        )
    L.append("")
    L.append("## Zellen (Symbol x Fenster, Order-Level)")
    L.append("")
    L.append(
        "| Symbol | Fenster | N Band | b- | b+ | b- − b+ | b_P1 | b_P2 | boot p | "
        "FDR-sig | b->=1,0 | Asym>=0,5 | Placebo-Dominanz | Zelle gueltig | bestanden |"
    )
    L.append("|---|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for c in payload["cells"]:
        pl = list(c["placebos"].values())
        L.append(
            f"| {c['symbol']} | {c['window_label']} | {c['n_orders_in_band']} "
            f"| {_fmt(c['b_minus'], 3)} | {_fmt(c['b_plus'], 3)} | {_fmt(c['b_asymmetry'], 3)} "
            f"| {_fmt(pl[0]['b_minus'], 3)} | {_fmt(pl[1]['b_minus'], 3)} "
            f"| {_fmt(c['bootstrap_p'])} | {_fmt(c['fdr_significant'])} "
            f"| {_fmt(c['b_minus_floor_met'])} | {_fmt(c['asymmetry_met'])} "
            f"| {_fmt(c['placebo_dominance_met'])} | {_fmt(c['cell_valid'])} "
            f"| {_fmt(c['passed'])} |"
        )
    L.append("")
    L.append(
        "*Erzeugt von `scripts/c09_bunch.py` (Welle-4, read-only Harvester-Backfill, "
        "DEC-19). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-09.*"
    )
    L.append("")
    return "\n".join(L)


def write_outputs(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``c09_bunch_results.json`` + ``.md`` to ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c09_bunch_results.json"
    md_path = out_dir / "c09_bunch_results.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path
