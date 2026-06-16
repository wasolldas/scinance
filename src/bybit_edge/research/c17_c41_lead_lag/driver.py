"""Read-only driver for the C-17/C-41 lead-lag mess-gate (Welle-2 WP, H-04).

Loads publicTrade ticks for a SYMBOL PAIR (default BTCUSDT/ETHUSDT) from the
existing DuckDB ``trades`` table OR CSV/Parquet files, resamples both onto a
common bar grid, splits into >= 2 disjoint chronological windows (registry
H-04), and per window measures directed information BTC->Alt on two axes:

* **C-17 Transfer Entropy** at each lag of the F-LEADLAG family,
* **C-41 wavelet coherence phase-lead**,

each tested against a circular-shift surrogate null, then BH-FDR (alpha = 0.10)
across the whole family. It determines the lead symbol per window and checks its
stability across windows. Output: ``c17_c41_results.json`` + a Markdown report
listing — per window, per criterion — the surrogate p, FDR significance, lead
symbol and lag length.

KAPITALFREI (registry H-04): this driver measures the *existence* of directed
information only. There is NO friction / edge / bps / PnL / Sharpe column —
adding one would be a gate violation. The GATE VERDICT (WEITER / DROP) is the
gate-auditor's call; this driver reports each criterion individually.

Mirrors the C-31 read-only pattern (DEC-03/DEC-09): ``_open_db_with_timeout``
(30s daemon thread), ``--db-copy`` temp-copy against the collector RW lock,
epoch-ms plausibility filter, deterministic-chronological window split with a
WINDOW_MAX_TICKS cap, and progress logging on stderr.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .surrogate import (
    FDR_ALPHA,
    benjamini_hochberg,
    surrogate_test_te,
    surrogate_test_wcoh,
)
from .transfer_entropy import (
    DEFAULT_LAGS,
    DEFAULT_N_BINS,
    align_returns,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-04"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
SURROGATE_P_MAX = 0.05  # registered (derived, registry H-04)
MIN_WINDOWS = 2         # registered (>= 2 disjoint windows)

#: Default common resample grid (DEC-10): 1000 ms bars from publicTrade.
DEFAULT_GRID_MS = 1000.0

#: Deterministic per-window tick cap (DEC-10, mirrors DEC-09 reasoning). Lead-lag
#: needs no day-long windows; ~150k ticks per symbol span ample minutes of
#: sub-minute structure while keeping the (lags × surrogates × 2 symbols)
#: workload tractable and within-window stationarity intact.
WINDOW_MAX_TICKS = 150_000

DB_OPEN_TIMEOUT_S = 30.0
DB_LOCKED_HINT = (
    "DuckDB gesperrt — --db-copy nutzen oder Collector kurz stoppen "
    "(liest eine temporaere Kopie der .duckdb-Datei, lock-frei)"
)

# Epoch-ms plausibility window (collector contract TradeEvent.timestamp_ms);
# corrupt ts=0 / wrong-unit rows would wreck the common-grid span (DEC-09 lesson).
TS_PLAUSIBLE_MIN_MS = 1_262_304_000_000  # 2010-01-01 UTC
TS_PLAUSIBLE_MAX_MS = 4_102_444_800_000  # 2100-01-01 UTC


class DataError(RuntimeError):
    """Raised on missing / malformed input (CLI maps this to exit-code 1)."""


# ----------------------------------------------------------------------------
# Read-only loaders (mirror c31_cfar.driver)
# ----------------------------------------------------------------------------

def _open_db_with_timeout(opener, timeout_s: float = DB_OPEN_TIMEOUT_S):
    """Run ``opener()`` in a daemon thread with a hard timeout (DuckDB lock)."""
    import threading

    box: dict = {}

    def _work() -> None:
        try:
            box["layer"] = opener()
        except Exception as exc:  # noqa: BLE001 - re-raised below
            box["error"] = exc

    t = threading.Thread(target=_work, name="c17-db-open", daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        raise DataError(f"DuckDB-Open haengt seit {timeout_s:.0f}s — {DB_LOCKED_HINT}")
    if "error" in box:
        exc = box["error"]
        msg = str(exc)
        if "lock" in msg.lower() or "Conflicting" in msg:
            raise DataError(f"DuckDB-Open fehlgeschlagen ({msg}) — {DB_LOCKED_HINT}")
        raise exc
    return box["layer"]


def load_trades_duckdb(
    db_path: Path,
    symbol: str,
    *,
    db_copy: bool = False,
    _shared_copy_dir: Path | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Load (ts_ms, price) for one symbol from the DuckDB ``trades`` table.

    Read-only with a 30s open timeout and the ``--db-copy`` escape hatch. When
    ``_shared_copy_dir`` is given (set by :func:`load_pair_duckdb`), the copy is
    reused for both symbols rather than copied twice.
    """
    try:
        from bybit_edge.persistence.db import PersistenceLayer
    except Exception as exc:  # pragma: no cover - import guard
        raise DataError(f"cannot import PersistenceLayer: {exc}") from exc
    if not Path(db_path).exists():
        raise DataError(f"DuckDB file not found: {db_path}")

    db_path = Path(db_path)
    copy_dir: Path | None = None
    if db_copy and _shared_copy_dir is None:
        import shutil
        import tempfile

        copy_dir = Path(tempfile.mkdtemp(prefix="c17_dbcopy_"))
        copied = copy_dir / db_path.name
        print(f"[c17] --db-copy: copying {db_path} -> {copied}", file=sys.stderr, flush=True)
        shutil.copy2(db_path, copied)
        wal = db_path.with_name(db_path.name + ".wal")
        if wal.is_file():
            shutil.copy2(wal, copy_dir / wal.name)
        db_path = copied
    elif _shared_copy_dir is not None:
        db_path = _shared_copy_dir / Path(db_path).name

    print(f"[c17] opening duckdb read-only: {db_path} (symbol={symbol})", file=sys.stderr, flush=True)
    try:
        layer = _open_db_with_timeout(lambda: PersistenceLayer(db_path, read_only=True))
    except DataError:
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
        raise
    try:
        where = "symbol = ?"
        params: list[Any] = [symbol]
        n_total = layer.conn.execute(
            f"SELECT COUNT(*) FROM trades WHERE {where}", params
        ).fetchone()[0]
        where += " AND ts >= ? AND ts <= ?"
        params.extend([TS_PLAUSIBLE_MIN_MS, TS_PLAUSIBLE_MAX_MS])
        rows = layer.conn.execute(
            f"SELECT ts, price FROM trades WHERE {where} ORDER BY ts", params
        ).fetchall()
    finally:
        layer.close()
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
            print(f"[c17] --db-copy: removed temp copy {copy_dir}", file=sys.stderr, flush=True)
    n_dropped = int(n_total) - len(rows)
    if n_dropped > 0:
        print(
            f"[c17] WARN: dropped {n_dropped} trades row(s) for {symbol} with "
            f"implausible ts (outside [{TS_PLAUSIBLE_MIN_MS}, {TS_PLAUSIBLE_MAX_MS}] "
            f"ms epoch) — corrupt rows in {db_path}",
            file=sys.stderr,
        )
    if not rows:
        raise DataError(
            f"no trades with plausible epoch-ms timestamps for symbol={symbol} "
            f"in {db_path} ({n_dropped} implausible row(s) dropped)"
        )
    ts = np.array([r[0] for r in rows], dtype=np.float64)
    px = np.array([r[1] for r in rows], dtype=np.float64)
    return ts, px


def load_pair_duckdb(
    db_path: Path,
    symbol_a: str,
    symbol_b: str,
    *,
    db_copy: bool = False,
) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    """Load both symbols of the pair, sharing a single ``--db-copy`` temp copy."""
    copy_dir: Path | None = None
    db_path = Path(db_path)
    try:
        if db_copy:
            import shutil
            import tempfile

            if not db_path.exists():
                raise DataError(f"DuckDB file not found: {db_path}")
            copy_dir = Path(tempfile.mkdtemp(prefix="c17_dbcopy_"))
            copied = copy_dir / db_path.name
            print(f"[c17] --db-copy: copying {db_path} -> {copied}", file=sys.stderr, flush=True)
            shutil.copy2(db_path, copied)
            wal = db_path.with_name(db_path.name + ".wal")
            if wal.is_file():
                shutil.copy2(wal, copy_dir / wal.name)
        a = load_trades_duckdb(db_path, symbol_a, _shared_copy_dir=copy_dir)
        b = load_trades_duckdb(db_path, symbol_b, _shared_copy_dir=copy_dir)
        return a, b
    finally:
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
            print(f"[c17] --db-copy: removed temp copy {copy_dir}", file=sys.stderr, flush=True)


def load_trades_file(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load (ts_ms, price) from a CSV or Parquet file (read-only)."""
    p = Path(path)
    if not p.exists():
        raise DataError(f"input file not found: {p}")
    import pandas as pd

    if p.suffix.lower() in (".parquet", ".pq"):
        df = pd.read_parquet(p)
    else:
        df = pd.read_csv(p)
    ts_col = next((c for c in ("ts", "timestamp_ms", "T", "timestamp") if c in df.columns), None)
    px_col = next((c for c in ("price", "p", "last_price") if c in df.columns), None)
    if ts_col is None or px_col is None:
        raise DataError(f"file {p} missing ts/price columns (have {list(df.columns)})")
    ts = df[ts_col].to_numpy(dtype=np.float64)
    px = df[px_col].to_numpy(dtype=np.float64)
    if ts.size == 0:
        raise DataError(f"file {p} contains no rows")
    order = np.argsort(ts, kind="stable")
    return ts[order], px[order]


def _cap_tail(ts: np.ndarray, px: np.ndarray, budget: int) -> tuple[np.ndarray, np.ndarray]:
    """Keep only the most recent ``budget`` ticks (deterministic-chronological)."""
    if ts.size > budget:
        return ts[-budget:], px[-budget:]
    return ts, px


def split_pair_windows(
    ts_a: np.ndarray, px_a: np.ndarray,
    ts_b: np.ndarray, px_b: np.ndarray,
    n_windows: int,
    *,
    max_ticks_per_window: int = WINDOW_MAX_TICKS,
) -> list[tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]]:
    """Split BOTH symbols into ``n_windows`` disjoint, contiguous windows.

    The split is done on a SHARED wall-clock time axis so window ``k`` covers the
    same interval for both symbols (required for a meaningful common-grid resample
    later). DEC-10: each symbol is first capped to its most recent
    ``n_windows × max_ticks_per_window`` ticks (deterministic-chronological, no
    discretionary selection — registry H-04 wording preserved); the overlapping
    time range of the two capped series is then cut into ``n_windows`` equal-time
    disjoint slices. The H-04 gate thresholds are NOT affected by this scoping.
    """
    if n_windows < MIN_WINDOWS:
        raise DataError(f"H-04 requires >= {MIN_WINDOWS} disjoint windows, got {n_windows}")
    if max_ticks_per_window < 8:
        raise DataError(f"max_ticks_per_window must be >= 8, got {max_ticks_per_window}")
    budget = n_windows * int(max_ticks_per_window)
    ts_a, px_a = _cap_tail(ts_a, px_a, budget)
    ts_b, px_b = _cap_tail(ts_b, px_b, budget)
    if ts_a.size < n_windows * 4 or ts_b.size < n_windows * 4:
        raise DataError(
            f"too few ticks (a={ts_a.size}, b={ts_b.size}) to form {n_windows} windows"
        )
    t0 = max(float(ts_a[0]), float(ts_b[0]))
    t1 = min(float(ts_a[-1]), float(ts_b[-1]))
    if t1 <= t0:
        raise DataError("symbols have no overlapping time range")
    edges = np.linspace(t0, t1, n_windows + 1)
    out: list[tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]] = []
    for k in range(n_windows):
        lo, hi = edges[k], edges[k + 1]
        # Half-open [lo, hi) for interior windows so a tick landing exactly on
        # an interior edge is assigned to a SINGLE window (disjointness); the
        # last window is closed [lo, hi] so the final tick is never dropped.
        last = k == n_windows - 1
        ma = (ts_a >= lo) & ((ts_a <= hi) if last else (ts_a < hi))
        mb = (ts_b >= lo) & ((ts_b <= hi) if last else (ts_b < hi))
        out.append(((ts_a[ma], px_a[ma]), (ts_b[mb], px_b[mb])))
    return out


# ----------------------------------------------------------------------------
# Per-window pipeline
# ----------------------------------------------------------------------------

@dataclass(slots=True)
class WindowResult:
    index: int
    n_bars: int
    t0_ms: float
    t1_ms: float
    variants: list[dict[str, Any]] = field(default_factory=list)
    best: dict[str, Any] | None = None
    criteria: dict[str, Any] = field(default_factory=dict)


def run_window(
    index: int,
    pair_a: tuple[np.ndarray, np.ndarray],
    pair_b: tuple[np.ndarray, np.ndarray],
    *,
    symbol_a: str,
    symbol_b: str,
    lags: tuple[int, ...],
    n_bins: int,
    grid_ms: float,
    n_surrogates: int,
    seed: int,
    n_windows: int,
) -> WindowResult:
    """Run all F-LEADLAG variants over one window and BH-FDR across them.

    For each lag, BOTH directions (A->B and B->A) of the TE axis are measured so
    the lead SYMBOL can be determined; the wavelet axis is run once per window.
    The window's "best" variant is the FDR-surviving variant with the lowest
    p-value. Lead symbol = the direction whose significant TE is strongest.
    """
    ts_a, px_a = pair_a
    ts_b, px_b = pair_b
    ret_a, ret_b = align_returns(ts_a, px_a, ts_b, px_b, grid_ms)
    n_bars = int(ret_a.size)

    print(
        f"[c17] window {index + 1}/{n_windows}: {n_bars} common bars "
        f"(grid {grid_ms:g}ms), lags={list(lags)}, {n_surrogates} surrogates/variant",
        file=sys.stderr, flush=True,
    )

    per_variant: list[dict[str, Any]] = []
    p_values: list[float] = []
    n_variants = 2 * len(lags) + 1  # both TE directions per lag + 1 wavelet

    if n_bars < max(lags) + 16:
        # Too few bars: emit empty, p=1 variants so the window cleanly fails.
        print(
            f"[c17] window {index + 1}/{n_windows}: too few common bars ({n_bars}) "
            f"— variants report p=1.0",
            file=sys.stderr, flush=True,
        )

    vi = 0
    for lag in lags:
        for src_sym, dst_sym, src, dst in (
            (symbol_a, symbol_b, ret_a, ret_b),
            (symbol_b, symbol_a, ret_b, ret_a),
        ):
            vi += 1
            print(
                f"[c17] window {index + 1}/{n_windows} variant {vi}/{n_variants}: "
                f"TE {src_sym}->{dst_sym} lag={lag} — surrogate test...",
                file=sys.stderr, flush=True,
            )
            res = surrogate_test_te(
                src, dst, lag, n_bins=n_bins,
                n_surrogates=n_surrogates, seed=seed + vi,
            )
            entry = {
                "axis": "TE",
                "label": f"TE_{src_sym}->{dst_sym}_lag{lag}",
                "lag": lag,
                "lag_ms": lag * grid_ms,
                "source": src_sym,
                "target": dst_sym,
                "surrogate": res.as_dict(),
            }
            per_variant.append(entry)
            p_values.append(res.p_value)
            print(
                f"[c17] window {index + 1}/{n_windows} variant {vi}/{n_variants}: "
                f"{entry['label']} done — TE={res.observed_stat:.5f} p={res.p_value:.4f}",
                file=sys.stderr, flush=True,
            )

    # C-41 wavelet coherence axis (A as putative leader); the sign of the lead
    # tells which symbol leads, the coherence statistic carries significance.
    vi += 1
    print(
        f"[c17] window {index + 1}/{n_windows} variant {vi}/{n_variants}: "
        f"WCOH {symbol_a}/{symbol_b} — surrogate test...",
        file=sys.stderr, flush=True,
    )
    wres, lead_s = surrogate_test_wcoh(
        ret_a, ret_b, grid_ms, n_surrogates=n_surrogates, seed=seed + vi,
    )
    lead_symbol_wcoh = symbol_a if lead_s > 0 else symbol_b
    wentry = {
        "axis": "WCOH",
        "label": f"WCOH_{symbol_a}/{symbol_b}",
        "lag": 0,
        "lag_ms": abs(lead_s) * 1000.0,
        "source": lead_symbol_wcoh,
        "target": symbol_b if lead_symbol_wcoh == symbol_a else symbol_a,
        "lead_seconds": float(lead_s),
        "surrogate": wres.as_dict(),
    }
    per_variant.append(wentry)
    p_values.append(wres.p_value)
    print(
        f"[c17] window {index + 1}/{n_windows} variant {vi}/{n_variants}: "
        f"{wentry['label']} done — coh={wres.observed_stat:.4f} "
        f"lead={lead_s:.3f}s (leader {lead_symbol_wcoh}) p={wres.p_value:.4f}",
        file=sys.stderr, flush=True,
    )

    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for entry, rej in zip(per_variant, rejected):
        entry["fdr_significant"] = bool(rej)

    wr = WindowResult(
        index=index, n_bars=n_bars,
        t0_ms=float(ts_a[0]) if ts_a.size else 0.0,
        t1_ms=float(ts_a[-1]) if ts_a.size else 0.0,
    )
    wr.variants = per_variant

    # Best variant for the p-value criterion: lowest p among FDR survivors
    # (ties -> lowest p_crit-relative rank, then most extreme observed stat).
    survivors = [e for e in per_variant if e["fdr_significant"]]
    pool = survivors if survivors else per_variant
    best = min(
        pool,
        key=lambda e: (e["surrogate"]["p_value"], -e["surrogate"]["observed_stat"]),
    )
    wr.best = best
    best_p = best["surrogate"]["p_value"]

    # Lead-symbol determination: the SOURCE symbol of the directed information.
    # Only the TE axis (C-17) is directional within a single statistic — the
    # WCOH coherence magnitude is symmetric and its signed lead is noise-prone,
    # so direction is taken from TE whenever a TE variant survives FDR. The
    # WCOH lead-sign is used only as a fallback when NO TE variant is
    # significant (still a valid C-41 lead reading, just less robust). Among
    # significant TE variants we pick the one with the largest TE (strongest
    # directed information), whose source is the lead symbol.
    te_survivors = [e for e in survivors if e["axis"] == "TE"]
    if te_survivors:
        lead_var = max(te_survivors, key=lambda e: e["surrogate"]["observed_stat"])
    elif survivors:
        # No directional TE survivor; fall back to the strongest survivor's
        # source (WCOH lead-sign or a TE that did not make it — direction is
        # then only weakly determined, which the gate-auditor sees in the table).
        lead_var = max(survivors, key=lambda e: e["surrogate"]["observed_stat"])
    else:
        lead_var = best
    lead_source = lead_var["source"]
    lead_lag_ms = lead_var["lag_ms"]

    wr.criteria = {
        "surrogate_p": {
            "value": best_p,
            "threshold": SURROGATE_P_MAX,
            "fdr_significant": best["fdr_significant"],
            "passed": (best_p <= SURROGATE_P_MAX) and best["fdr_significant"],
            "registry_text": "Konditionale gerichtete Information signifikant > Surrogate-Null, p <= 0.05 (BH-FDR, F-LEADLAG)",
        },
        "lead_symbol": {
            "value": lead_source,
            "axis": lead_var["axis"],
            "variant": lead_var["label"],
            "lag_ms": lead_lag_ms,
            "registry_text": "Lead-Symbol (Vorzeichen/Richtung) ueber Fenster konsistent",
        },
        "fdr_p_crit": p_crit,
        "n_fdr_significant": len(survivors),
    }
    return wr


# ----------------------------------------------------------------------------
# Orchestration + report
# ----------------------------------------------------------------------------

def run(
    pair_a: tuple[np.ndarray, np.ndarray],
    pair_b: tuple[np.ndarray, np.ndarray],
    *,
    symbol_a: str,
    symbol_b: str,
    n_windows: int,
    lags: tuple[int, ...] = DEFAULT_LAGS,
    n_bins: int = DEFAULT_N_BINS,
    grid_ms: float = DEFAULT_GRID_MS,
    n_surrogates: int = 200,
    seed: int = 42,
    max_ticks_per_window: int = WINDOW_MAX_TICKS,
    source: str = "",
) -> dict[str, Any]:
    """Run the full C-17/C-41 pipeline over >= 2 windows and assemble the payload."""
    ts_a, px_a = pair_a
    ts_b, px_b = pair_b
    windows = split_pair_windows(
        ts_a, px_a, ts_b, px_b, n_windows,
        max_ticks_per_window=max_ticks_per_window,
    )
    n_total_a, n_total_b = int(ts_a.size), int(ts_b.size)
    print(
        f"[c17] pair {symbol_a}/{symbol_b}: {n_total_a}/{n_total_b} ticks loaded, "
        f"{len(windows)} window(s) (cap {max_ticks_per_window}/window, "
        f"lags={list(lags)}, grid={grid_ms:g}ms, surrogates={n_surrogates})",
        file=sys.stderr, flush=True,
    )

    win_results = [
        run_window(
            i, wa, wb,
            symbol_a=symbol_a, symbol_b=symbol_b,
            lags=lags, n_bins=n_bins, grid_ms=grid_ms,
            n_surrogates=n_surrogates, seed=seed,
            n_windows=len(windows),
        )
        for i, (wa, wb) in enumerate(windows)
    ]

    # Per-window existence pass = best variant FDR-significant AND p <= 0.05.
    per_window_existence = [bool(wr.criteria["surrogate_p"]["passed"]) for wr in win_results]
    # Lead-symbol stability: the lead symbol of every window's best (significant)
    # variant must be identical (registry H-04: sign/lead consistent across both
    # windows). Only meaningful among windows that show existence.
    lead_symbols = [wr.criteria["lead_symbol"]["value"] for wr in win_results]
    lead_stable = len(set(lead_symbols)) == 1

    all_windows_pass = (
        len(win_results) >= MIN_WINDOWS
        and all(per_window_existence)
        and lead_stable
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "n_windows": len(win_results),
        "n_surrogates": n_surrogates,
        "seed": seed,
        "fdr_alpha": FDR_ALPHA,
        "grid_ms": grid_ms,
        "n_bins": n_bins,
        "lags": list(lags),
        "axes": ["TE (C-17)", "WCOH (C-41)"],
        # Data-scoping record (DEC-10): NOT a gate threshold.
        "max_ticks_per_window": int(max_ticks_per_window),
        "n_ticks_total": {"a": n_total_a, "b": n_total_b},
        "gate_thresholds": {
            "surrogate_p_max": SURROGATE_P_MAX,
            "min_windows": MIN_WINDOWS,
            "lead_symbol_stable_required": True,
        },
        "all_windows_pass": all_windows_pass,
        "per_window_existence": per_window_existence,
        "lead_symbols": lead_symbols,
        "lead_symbol_stable": lead_stable,
        "windows": [
            {
                "index": wr.index,
                "n_bars": wr.n_bars,
                "t0_ms": wr.t0_ms,
                "t1_ms": wr.t1_ms,
                "best_variant": wr.best["label"] if wr.best else None,
                "criteria": wr.criteria,
                "variants": wr.variants,
            }
            for wr in win_results
        ],
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
    """German Markdown report — one criterion per row, per window (H-04)."""
    L: list[str] = []
    L.append("# C-17/C-41 Lead-Lag-Mess-Gate (H-04 · Cross-Sectional, KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Paar `{payload['symbol_a']}`/`{payload['symbol_b']}`)")
    L.append(
        f"- **Fenster:** {payload['n_windows']} · **Surrogates:** {payload['n_surrogates']} · "
        f"**Seed:** {payload['seed']} · **BH-FDR alpha:** {payload['fdr_alpha']}"
    )
    L.append(
        f"- **Grid:** {payload['grid_ms']:g} ms · **Quantil-Bins:** {payload['n_bins']} · "
        f"**Lags (Bars):** {payload['lags']} · **Achsen:** {', '.join(payload['axes'])}"
    )
    L.append(
        f"- **KAPITALFREI:** {_fmt(payload['capital_free'])} — reines Mess-Gate fuer "
        "gerichteten Informationsfluss, KEINE bps/Edge/PnL/Friction-Metrik."
    )
    L.append("")
    L.append(
        "> Der Report liefert jedes Gate-Kriterium einzeln je Fenster. Das "
        "GATE-URTEIL (WEITER/DROP) faellt der gate-auditor gegen H-04 — hartes "
        "Ein-Fenster-Kriterium (PRD §8.5), Lead-Symbol-Stabilitaet ueber Fenster."
    )
    L.append("")
    L.append(f"**Existenz in allen Fenstern + Lead-Stabilitaet:** {_fmt(payload['all_windows_pass'])}")
    L.append(
        f"**Lead-Symbole je Fenster:** {payload['lead_symbols']} "
        f"(stabil: {_fmt(payload['lead_symbol_stable'])})"
    )
    L.append("")
    for w in payload["windows"]:
        c = w["criteria"]
        L.append(f"## Fenster {w['index']} — {w['n_bars']} gemeinsame Bars")
        L.append(f"- Zeitspanne: {w['t0_ms']:.0f} .. {w['t1_ms']:.0f} ms")
        L.append(f"- Beste Variante (F-LEADLAG): `{w['best_variant']}`")
        L.append("")
        L.append("| Kriterium | Registry-Text | Messwert | Schwelle | Bestanden |")
        L.append("|---|---|---:|---:|---|")
        sp = c["surrogate_p"]
        L.append(
            f"| Surrogate p | {sp['registry_text']} | {_fmt(sp['value'])} "
            f"| <= {sp['threshold']} | {_fmt(sp['passed'])} (FDR sig: {_fmt(sp['fdr_significant'])}) |"
        )
        ls = c["lead_symbol"]
        L.append(
            f"| Lead-Symbol | {ls['registry_text']} | {ls['value']} (Achse {ls['axis']}, "
            f"Lag {_fmt(ls['lag_ms'], 1)} ms) | konsistent | siehe oben |"
        )
        L.append("")
        L.append(f"- BH-FDR p_crit: {_fmt(c['fdr_p_crit'])} · FDR-signifikante Varianten: {c['n_fdr_significant']}")
        L.append("")
        L.append("| Variante | Achse | Quelle->Ziel | Lag (ms) | Statistik | Surrogate p | FDR sig |")
        L.append("|---|---|---|---:|---:|---:|---|")
        for v in w["variants"]:
            tgt = v.get("target", "")
            L.append(
                f"| `{v['label']}` | {v['axis']} | {v['source']}->{tgt} "
                f"| {_fmt(v['lag_ms'], 1)} | {_fmt(v['surrogate']['observed_stat'])} "
                f"| {_fmt(v['surrogate']['p_value'])} | {_fmt(v['fdr_significant'])} |"
            )
        L.append("")
    L.append("---")
    L.append(
        "*Erzeugt von `scripts/c17_c41_lead_lag.py` (Welle-2-WP, read-only Driver, DEC-10). "
        f"KAPITALFREI. Endgueltiges Gate-Urteil: gate-auditor gegen {HYPOTHESIS_ID}.*"
    )
    L.append("")
    return "\n".join(L)


def write_outputs(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``c17_c41_results.json`` + ``c17_c41_results.md`` to ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c17_c41_results.json"
    md_path = out_dir / "c17_c41_results.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path
