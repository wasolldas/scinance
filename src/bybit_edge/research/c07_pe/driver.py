"""Read-only driver for the C-07 Permutation-Entropy mess-gate (Welle-2 WP, H-06).

Loads ``kline_1min`` close series ``(ts, close)`` for up to 5 Futures-Perp
symbols (default BTC/ETH/SOL/BNB/XRP) from the existing DuckDB ``kline_1min``
table (PRD §4 wörtlich: "nur Kline, kein Tiefen-Stream" — NOT the trades table),
splits each symbol into >= 2 disjoint chronological windows (registry H-06,
WINDOW_MAX_BARS cap per DEC-12) and runs the TWO-STAGE gate per window:

* PRE-Gate: rho(PE-drop_t, forward vol-cluster_{(t,t+15min]}) per window
  (registry: rho >= 0.30 on >= 2 windows; rho < 0.30 in ONE window => DROP).
* Main-Gate: per pre-fixed delta in {1,5,15,60}min the conditional information
  MI(PE_t ; target_{t+delta}) against a block-shift surrogate null, plus the
  conditional AUC-lift in G1 (top vol quartile of the surrogate null). BH-FDR
  (alpha = 0.10) over the WHOLE F-ENTROPY family (all window-length x delta x
  symbol). Output reports rho, surrogate_p, fdr_significant, auc_lift, n_g1 per
  window/delta/symbol INDIVIDUALLY — NO overall verdict, NO bps/PnL.

Bandt-Pompe embedding m = 4 / tau = 1 are PRE-FIXED read-only constants
(``PE_M`` / ``PE_TAU`` in ``perm_entropy.py``), NOT CLI flags — any deviation is a
NEW H-06 line (verdict.md §1f, DEC-12). They are documented in the output.

KAPITALFREI (registry H-06): pure detection / information measurement. There is
NO friction, edge, bps, PnL or Sharpe column — adding one would be a gate
violation. The driver renders NO verdict (gate-auditor's call).

Mirrors the C-31 / C-17 / C-01 read-only pattern (DEC-03/DEC-09/DEC-11):
``_open_db_with_timeout`` (30s daemon thread), ``--db-copy`` temp-copy against
the collector RW lock, epoch-ms plausibility filter (on kline ts), deterministic-
chronological window split with a WINDOW_MAX_BARS cap, progress logging on stderr.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .info_test import (
    AUC_LIFT_FLOOR,
    DEFAULT_N_BINS,
    FDR_ALPHA,
    SURROGATE_P_MAX,
    benjamini_hochberg,
    info_test,
)
from .perm_entropy import (
    DEFAULT_PE_WINDOW,
    PE_M,
    PE_TAU,
    log_returns,
    pe_drop,
    rolling_permutation_entropy,
)
from .pre_gate import RHO_FLOOR, VOL_CLUSTER_BARS, forward_realized_vol, pre_gate

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-06"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
MIN_WINDOWS = 2  # registered (>= 2 disjoint windows)

#: Default symbol universe (registry H-06): Futures-Perp 5er-Universum.
DEFAULT_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
)

#: Pre-fixed forward-target lags in MINUTES (DEC-12). delta in {1,5,15,60}min;
#: each delta counts individually in the F-ENTROPY family. CLI ``--lags``.
DEFAULT_LAGS_MIN: tuple[int, ...] = (1, 5, 15, 60)

#: Deterministic per-window bar cap (DEC-12; datierter Nachtrag UNTER H-06).
#: 43_200 1-min bars = 30 days. NOT a tractability cap (kline has only 1440
#: bars/day/symbol) — a STATIONARITY cap: enough bars for a robust rolling PE
#: estimate (m! = 24 patterns) + >= 2 disjoint windows, while a ~30-day window
#: stays a defensible quasi-stationary crypto-vol horizon (multi-month windows
#: would mix regime changes and break PE stationarity). Gate thresholds UNCHANGED.
WINDOW_MAX_BARS = 43_200

DB_OPEN_TIMEOUT_S = 30.0
DB_LOCKED_HINT = (
    "DuckDB gesperrt — --db-copy nutzen oder Collector kurz stoppen "
    "(liest eine temporaere Kopie der .duckdb-Datei, lock-frei)"
)

# Epoch-ms plausibility window (collector kline ts contract).
TS_PLAUSIBLE_MIN_MS = 1_262_304_000_000  # 2010-01-01 UTC
TS_PLAUSIBLE_MAX_MS = 4_102_444_800_000  # 2100-01-01 UTC


class DataError(RuntimeError):
    """Raised on missing / malformed input (CLI maps this to exit-code 1)."""


# ----------------------------------------------------------------------------
# Read-only loaders (mirror c31_cfar / c01_ofi_sign driver)
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

    t = threading.Thread(target=_work, name="c07-db-open", daemon=True)
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


@dataclass(slots=True)
class KlineArrays:
    """Per-symbol kline columns (ts ascending) for the PE estimator."""

    ts: np.ndarray
    close: np.ndarray

    @property
    def size(self) -> int:
        return int(self.ts.size)


def load_kline_duckdb(
    db_path: Path,
    symbol: str,
    *,
    db_copy: bool = False,
    _shared_copy_dir: Path | None = None,
) -> KlineArrays:
    """Load ``(ts, close)`` for one symbol from the ``kline_1min`` table.

    Read-only with a 30s open timeout and the ``--db-copy`` escape hatch. When
    ``_shared_copy_dir`` is given (set by :func:`load_symbols_duckdb`) the copy
    is reused for all symbols rather than copied per symbol.
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

        copy_dir = Path(tempfile.mkdtemp(prefix="c07_dbcopy_"))
        copied = copy_dir / db_path.name
        print(f"[c07] --db-copy: copying {db_path} -> {copied}", file=sys.stderr, flush=True)
        shutil.copy2(db_path, copied)
        wal = db_path.with_name(db_path.name + ".wal")
        if wal.is_file():
            shutil.copy2(wal, copy_dir / wal.name)
        db_path = copied
    elif _shared_copy_dir is not None:
        db_path = _shared_copy_dir / Path(db_path).name

    print(f"[c07] opening duckdb read-only: {db_path} (symbol={symbol})", file=sys.stderr, flush=True)
    try:
        layer = _open_db_with_timeout(lambda: PersistenceLayer(db_path, read_only=True))
    except DataError:
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
        raise
    try:
        n_total = layer.conn.execute(
            "SELECT COUNT(*) FROM kline_1min WHERE symbol = ?", [symbol]
        ).fetchone()[0]
        rows = layer.conn.execute(
            "SELECT ts, close FROM kline_1min "
            "WHERE symbol = ? AND ts >= ? AND ts <= ? AND close IS NOT NULL "
            "ORDER BY ts",
            [symbol, TS_PLAUSIBLE_MIN_MS, TS_PLAUSIBLE_MAX_MS],
        ).fetchall()
    finally:
        layer.close()
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
            print(f"[c07] --db-copy: removed temp copy {copy_dir}", file=sys.stderr, flush=True)
    n_dropped = int(n_total) - len(rows)
    if n_dropped > 0:
        print(
            f"[c07] WARN: dropped {n_dropped} kline_1min row(s) for {symbol} with "
            f"implausible ts / null close — corrupt rows in {db_path}",
            file=sys.stderr,
        )
    if not rows:
        raise DataError(
            f"no kline_1min rows with plausible epoch-ms timestamps for "
            f"symbol={symbol} in {db_path} ({n_dropped} implausible/null row(s) dropped)"
        )
    ts = np.array([r[0] for r in rows], dtype=np.float64)
    close = np.array([r[1] for r in rows], dtype=np.float64)
    return KlineArrays(ts=ts, close=close)


def load_symbols_duckdb(
    db_path: Path,
    symbols: tuple[str, ...],
    *,
    db_copy: bool = False,
) -> dict[str, KlineArrays]:
    """Load all requested symbols, sharing a single ``--db-copy`` temp copy."""
    copy_dir: Path | None = None
    db_path = Path(db_path)
    out: dict[str, KlineArrays] = {}
    try:
        if db_copy:
            import shutil
            import tempfile

            if not db_path.exists():
                raise DataError(f"DuckDB file not found: {db_path}")
            copy_dir = Path(tempfile.mkdtemp(prefix="c07_dbcopy_"))
            copied = copy_dir / db_path.name
            print(f"[c07] --db-copy: copying {db_path} -> {copied}", file=sys.stderr, flush=True)
            shutil.copy2(db_path, copied)
            wal = db_path.with_name(db_path.name + ".wal")
            if wal.is_file():
                shutil.copy2(wal, copy_dir / wal.name)
        for sym in symbols:
            out[sym] = load_kline_duckdb(db_path, sym, _shared_copy_dir=copy_dir)
        return out
    finally:
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
            print(f"[c07] --db-copy: removed temp copy {copy_dir}", file=sys.stderr, flush=True)


def load_kline_file(path: Path, symbol: str = "FILE") -> dict[str, KlineArrays]:
    """Load ``(ts, close)`` from a CSV/Parquet file (read-only)."""
    p = Path(path)
    if not p.exists():
        raise DataError(f"input file not found: {p}")
    import pandas as pd

    if p.suffix.lower() in (".parquet", ".pq"):
        df = pd.read_parquet(p)
    else:
        df = pd.read_csv(p)
    ts_col = next((c for c in ("ts", "timestamp_ms", "T", "timestamp") if c in df.columns), None)
    close_col = next((c for c in ("close", "c", "close_price", "price") if c in df.columns), None)
    if ts_col is None or close_col is None:
        raise DataError(
            f"file {p} missing ts/close columns (have {list(df.columns)})"
        )
    ts = df[ts_col].to_numpy(dtype=np.float64)
    close = df[close_col].to_numpy(dtype=np.float64)
    if ts.size == 0:
        raise DataError(f"file {p} contains no rows")
    order = np.argsort(ts, kind="stable")
    return {symbol: KlineArrays(ts[order], close[order])}


# ----------------------------------------------------------------------------
# Deterministic-chronological window split
# ----------------------------------------------------------------------------

def split_windows(
    arr: KlineArrays,
    n_windows: int,
    *,
    max_bars_per_window: int = WINDOW_MAX_BARS,
) -> list[KlineArrays]:
    """Split one symbol's klines into ``n_windows`` disjoint contiguous windows.

    DEC-12 (datierter Nachtrag unter H-06, DEC-09-Muster): first cap to the most
    recent ``n_windows x max_bars_per_window`` bars (deterministic-chronological,
    no discretionary selection — registry H-06 wording preserved), then cut the
    capped series into ``n_windows`` equal-time disjoint slices. The H-06 gate
    thresholds (rho >= 0.3, p <= 0.05, AUC-lift >= +0.03) are NOT affected by this
    scoping — it is a pure stationarity-motivated data-scoping parameter.
    """
    if n_windows < MIN_WINDOWS:
        raise DataError(f"H-06 requires >= {MIN_WINDOWS} disjoint windows, got {n_windows}")
    if max_bars_per_window < 64:
        raise DataError(f"max_bars_per_window must be >= 64, got {max_bars_per_window}")
    budget = n_windows * int(max_bars_per_window)
    ts, close = arr.ts, arr.close
    if ts.size > budget:
        ts, close = ts[-budget:], close[-budget:]
    if ts.size < n_windows * 64:
        raise DataError(
            f"too few klines ({ts.size}) to form {n_windows} windows "
            f"(need >= {n_windows * 64} bars for a robust PE estimate)"
        )
    t0, t1 = float(ts[0]), float(ts[-1])
    if t1 <= t0:
        raise DataError("symbol klines have zero time span")
    edges = np.linspace(t0, t1, n_windows + 1)
    out: list[KlineArrays] = []
    for k in range(n_windows):
        lo, hi = edges[k], edges[k + 1]
        last = k == n_windows - 1
        m = (ts >= lo) & ((ts <= hi) if last else (ts < hi))
        out.append(KlineArrays(ts[m], close[m]))
    return out


# ----------------------------------------------------------------------------
# Per-window / per-family pipeline
# ----------------------------------------------------------------------------

@dataclass(slots=True)
class WindowSymbolResult:
    symbol: str
    window_index: int
    t0_ms: float
    t1_ms: float
    pre_gate: dict[str, Any] = field(default_factory=dict)
    variants: list[dict[str, Any]] = field(default_factory=list)  # one per delta


def _build_variants(
    win: KlineArrays,
    *,
    symbol: str,
    window_index: int,
    n_windows: int,
    lags_min: tuple[int, ...],
    pe_window: int,
    n_bins: int,
    n_surrogates: int,
    seed: int,
) -> WindowSymbolResult:
    """Run PRE-Gate + main-gate for every delta on one (symbol, window)."""
    res = WindowSymbolResult(
        symbol=symbol, window_index=window_index,
        t0_ms=float(win.ts[0]) if win.size else 0.0,
        t1_ms=float(win.ts[-1]) if win.size else 0.0,
    )
    rets = log_returns(win.close)
    pe = rolling_permutation_entropy(rets, window=pe_window, m=PE_M, tau=PE_TAU)
    drop = pe_drop(pe)
    fwd_rv = forward_realized_vol(rets, horizon_bars=VOL_CLUSTER_BARS)

    # --- PRE-Gate: rho(PE-drop, forward 15-min vol-cluster) ---
    pg = pre_gate(drop, fwd_rv)
    res.pre_gate = pg.as_dict()
    print(
        f"[c07] {symbol} window {window_index + 1}/{n_windows} PRE-Gate: "
        f"n={pg.n_pairs} rho={pg.rho:+.4f} floor_met={pg.rho_floor_met}",
        file=sys.stderr, flush=True,
    )

    # --- Main-Gate: MI(PE, target_{t+delta}) per delta ---
    for di, delta_min in enumerate(lags_min):
        # forward target at delta = forward realized vol over (t, t+delta] bars
        target = forward_realized_vol(rets, horizon_bars=int(delta_min))
        st = info_test(
            pe, drop, target, fwd_rv, float(delta_min),
            n_bins=n_bins, n_surrogates=n_surrogates,
            seed=seed + 1000 * (window_index + 1) + 7 * (di + 1) + abs(hash(symbol)) % 991,
        )
        entry = st.as_dict()
        entry["label"] = f"{symbol}_w{window_index}_d{delta_min}min"
        res.variants.append(entry)
        print(
            f"[c07] {symbol} window {window_index + 1}/{n_windows} "
            f"delta={delta_min}min: n={st.n_pairs} mi={st.mi:.5f} "
            f"surr_p={st.surrogate_p:.4f} auc_lift={st.auc_lift:+.4f} n_g1={st.n_g1}",
            file=sys.stderr, flush=True,
        )
    return res


def run(
    symbol_arrays: dict[str, KlineArrays],
    *,
    n_windows: int,
    lags_min: tuple[int, ...] = DEFAULT_LAGS_MIN,
    pe_window: int = DEFAULT_PE_WINDOW,
    n_bins: int = DEFAULT_N_BINS,
    n_surrogates: int = 200,
    seed: int = 42,
    max_bars_per_window: int = WINDOW_MAX_BARS,
    source: str = "",
) -> dict[str, Any]:
    """Run the full C-07 PE two-stage pipeline over all symbols x >= 2 windows.

    BH-FDR is applied across the WHOLE F-ENTROPY family (all delta x symbol x
    window variants), per registry H-06. Each criterion is reported individually
    (PRE-Gate rho, surrogate_p, fdr_significant, auc_lift, n_g1); the payload
    carries NO overall verdict (gate-auditor's call) and NO bps/PnL.
    """
    symbols = tuple(symbol_arrays.keys())
    all_results: list[WindowSymbolResult] = []
    for sym in symbols:
        windows = split_windows(
            symbol_arrays[sym], n_windows, max_bars_per_window=max_bars_per_window,
        )
        print(
            f"[c07] {sym}: {symbol_arrays[sym].size} klines loaded, "
            f"{len(windows)} window(s) (cap {max_bars_per_window}/window, "
            f"PE m={PE_M}/tau={PE_TAU} window={pe_window}, deltas={list(lags_min)}min, "
            f"n_bins={n_bins}, surrogates={n_surrogates})",
            file=sys.stderr, flush=True,
        )
        for wi, win in enumerate(windows):
            all_results.append(_build_variants(
                win, symbol=sym, window_index=wi, n_windows=len(windows),
                lags_min=lags_min, pe_window=pe_window, n_bins=n_bins,
                n_surrogates=n_surrogates, seed=seed,
            ))

    # BH-FDR over the whole F-ENTROPY family (all variants across all results).
    flat = [v for r in all_results for v in r.variants]
    p_values = [float(v["surrogate_p"]) for v in flat]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for v, rej in zip(flat, rejected):
        v["fdr_significant"] = bool(rej)
        v["surrogate_p_floor_met"] = bool(v["surrogate_p"] <= SURROGATE_P_MAX)
        v["auc_lift_floor_met"] = bool(v["auc_lift"] >= AUC_LIFT_FLOOR)
        # main-gate per-variant existence (FDR sig AND AUC-lift floor). Reported,
        # NOT adjudicated (gate-auditor combines with PRE-Gate + >=2-window rule).
        v["main_gate_variant_met"] = bool(v["fdr_significant"] and v["auc_lift_floor_met"])

    n_fdr_sig = sum(1 for v in flat if v["fdr_significant"])
    # PRE-Gate family observation (NEUTRAL): does every window clear rho >= 0.3?
    pre_rhos = [r.pre_gate.get("rho", 0.0) for r in all_results]
    all_windows_pre_pass = all(r.pre_gate.get("rho_floor_met", False) for r in all_results)
    any_window_pre_fail = any(not r.pre_gate.get("rho_floor_met", False) for r in all_results)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(symbols),
        "n_windows": n_windows,
        "n_surrogates": n_surrogates,
        "seed": seed,
        "fdr_alpha": FDR_ALPHA,
        # Pre-fixed embedding (DEC-12, claims_register §C-07) — documented, NOT a flag.
        "pe_m": PE_M,
        "pe_tau": PE_TAU,
        "pe_window_bars": pe_window,
        "n_bins": n_bins,
        "vol_cluster_bars": VOL_CLUSTER_BARS,
        "lags_min": list(lags_min),
        "max_bars_per_window": int(max_bars_per_window),
        "gate_thresholds": {
            "pre_gate_rho_floor": RHO_FLOOR,
            "surrogate_p_max": SURROGATE_P_MAX,
            "auc_lift_floor": AUC_LIFT_FLOOR,
            "min_windows": MIN_WINDOWS,
            "g1_definition": "top vol quartile of the surrogate-null distribution (pre-fixed)",
        },
        "fdr_p_crit": p_crit,
        "n_fdr_significant": n_fdr_sig,
        # Family-level observation flags (NEUTRAL — gate-auditor adjudicates):
        "pre_gate_rhos": [float(x) for x in pre_rhos],
        "all_windows_pre_gate_pass": bool(all_windows_pre_pass),
        "any_window_pre_gate_fail": bool(any_window_pre_fail),
        "results": [
            {
                "symbol": r.symbol,
                "window_index": r.window_index,
                "t0_ms": r.t0_ms,
                "t1_ms": r.t1_ms,
                "pre_gate": r.pre_gate,
                "variants": r.variants,
            }
            for r in all_results
        ],
    }


# ----------------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------------

def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_markdown(payload: dict[str, Any]) -> str:
    """German Markdown report — PRE-Gate + each main-gate criterion per variant."""
    L: list[str] = []
    L.append("# C-07 Permutation-Entropy-Mess-Gate (H-06, KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Symbole: {', '.join(payload['symbols'])})")
    L.append(
        f"- **Fenster:** {payload['n_windows']} · **Surrogates:** {payload['n_surrogates']} · "
        f"**Seed:** {payload['seed']} · **BH-FDR alpha:** {payload['fdr_alpha']}"
    )
    L.append(
        f"- **Bandt-Pompe Embedding (VORAB FIXIERT, DEC-12):** m = {payload['pe_m']}, "
        f"tau = {payload['pe_tau']} · **Rolling-PE-Fenster:** {payload['pe_window_bars']} Bars · "
        f"**MI-Bins:** {payload['n_bins']}"
    )
    L.append(
        f"- **Vol-Cluster:** RV ueber {payload['vol_cluster_bars']}-min-Forward-Fenster "
        f"(Summe quadrierter 1-min-log-Returns) · **delta-Lags:** {payload['lags_min']} min · "
        f"**Bar-Cap/Fenster:** {payload['max_bars_per_window']} (= {payload['max_bars_per_window'] // 1440} Tage, "
        "Stationaritaets-Cap)"
    )
    L.append(
        f"- **G1:** {payload['gate_thresholds']['g1_definition']}"
    )
    L.append(
        f"- **KAPITALFREI:** {_fmt(payload['capital_free'])} — reiner Detektions-/"
        "Info-Mess-Test, KEINE bps/Edge/PnL/Sharpe/Friction-Metrik."
    )
    L.append("")
    L.append(
        "> Der Report liefert das ZWEISTUFIGE Gate je Fenster EINZELN: PRE-Gate rho "
        "(rho >= 0.30 Floor) und je delta das Haupt-Gate (surrogate_p, FDR-sig, "
        "AUC-Lift in G1, n_g1). KEIN Gesamturteil. Das GATE-URTEIL (WEITER/DROP) "
        "faellt der gate-auditor gegen H-06 (PRE-Gate rho < 0.30 in EINEM Fenster "
        "-> DROP; hartes Ein-Fenster-Kriterium PRD §8.5)."
    )
    L.append("")
    L.append(
        f"**PRE-Gate rho je Fenster:** {[round(x, 4) for x in payload['pre_gate_rhos']]} · "
        f"alle Fenster rho >= 0.30: {_fmt(payload['all_windows_pre_gate_pass'])} · "
        f">=1 Fenster rho < 0.30: {_fmt(payload['any_window_pre_gate_fail'])}"
    )
    L.append(
        f"**F-ENTROPY BH-FDR p_crit:** {_fmt(payload['fdr_p_crit'])} · "
        f"**FDR-signifikante Varianten:** {payload['n_fdr_significant']}"
    )
    L.append("")
    # PRE-Gate table
    L.append("## PRE-Gate (rho PE-Drop vs. 15-min-Vol-Cluster)")
    L.append("")
    L.append("| Symbol | Fenster | n | rho | rho >= 0.30 |")
    L.append("|---|---:|---:|---:|:--:|")
    for r in payload["results"]:
        pg = r["pre_gate"]
        L.append(
            f"| {r['symbol']} | {r['window_index']} | {pg.get('n_pairs', 0)} "
            f"| {_fmt(pg.get('rho'))} | {_fmt(pg.get('rho_floor_met'))} |"
        )
    L.append("")
    # Main-gate table
    L.append("## Haupt-Gate (bedingte Information PE -> ret/vol_{t+delta})")
    L.append("")
    L.append(
        "| Symbol | Fenster | delta (min) | n | MI | Surr p | FDR sig "
        "| AUC-Lift | n_g1 | AUC-Lift >= 0.03 | Variante OK |"
    )
    L.append("|---|---:|---:|---:|---:|---:|:--:|---:|---:|:--:|:--:|")
    for r in payload["results"]:
        for v in r["variants"]:
            L.append(
                f"| {r['symbol']} | {r['window_index']} | {v['delta_min']:.0f} "
                f"| {v['n_pairs']} | {_fmt(v['mi'], 5)} | {_fmt(v['surrogate_p'])} "
                f"| {_fmt(v['fdr_significant'])} | {_fmt(v['auc_lift'])} | {v['n_g1']} "
                f"| {_fmt(v['auc_lift_floor_met'])} | {_fmt(v['main_gate_variant_met'])} |"
            )
    L.append("")
    L.append("---")
    L.append(
        "**Gate-Schwellen (registriert, NICHT hier beurteilt):** "
        f"PRE-Gate rho >= {payload['gate_thresholds']['pre_gate_rho_floor']} in >= "
        f"{payload['gate_thresholds']['min_windows']} disjunkten Fenstern (rho < 0.30 in "
        "EINEM Fenster -> DROP, kein Voll-Lauf). Haupt-Gate: Surrogate p <= "
        f"{payload['gate_thresholds']['surrogate_p_max']} nach BH-FDR alpha "
        f"{payload['fdr_alpha']} ueber F-ENTROPY in >= {payload['gate_thresholds']['min_windows']} "
        f"Fenstern UND bedingter AUC-Lift >= +{payload['gate_thresholds']['auc_lift_floor']} in "
        "G1-Fenstern. Hartes Ein-Fenster-DROP-Kriterium (PRD §8.5), kein GRAUBEREICH."
    )
    L.append("")
    L.append(
        "*Erzeugt von `scripts/c07_pe.py` (Welle-2-WP, read-only Driver, DEC-12, "
        "kline_1min — NICHT trades). Bandt-Pompe m=4/tau=1 VORAB FIXIERT (kein CLI-Flag). "
        f"KAPITALFREI. Endgueltiges Gate-Urteil: gate-auditor gegen {HYPOTHESIS_ID}.*"
    )
    L.append("")
    return "\n".join(L)


def write_outputs(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``c07_pe_results.json`` + ``.md`` to ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c07_pe_results.json"
    md_path = out_dir / "c07_pe_results.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path
