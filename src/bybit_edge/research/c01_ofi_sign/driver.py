"""Read-only driver for the C-01 OFI-sign mess-gate (Welle-2 WP, H-05).

Loads publicTrade ticks ``(ts, price, volume, side)`` for up to 5 Futures-Perp
symbols (default BTC/ETH/SOL/BNB/XRP) from the existing DuckDB ``trades`` table,
splits each symbol into >= 2 disjoint chronological windows (registry H-05),
and per window per symbol per pre-fixed lag delta in {1,5,15,60,300}s measures
the OFI-sign statistics (corr, sign_direction, |corr|, hit_rate) of
``sign(OFI_t) -> sign(forward_return_{t+delta})`` against a permutation surrogate
null. BH-FDR (alpha = 0.10) is applied across the WHOLE F-OFI family
(all delta x symbols x windows). Output: ``c01_ofi_sign_results.json`` +
a Markdown report listing, per window per delta per symbol, every gate criterion
INDIVIDUALLY plus ``sign_direction`` and ``inverse_significant``.

The OFI estimator is OWN (``ofi.py``), built directly from the trade aggressor
side; the bestand ``l1_ingestion/m2_ofi.py`` (known C-01/C-02 swap, book-update
based, streaming, suspect) is NOT imported and stays untouched (DEC-11).

KAPITALFREI (registry H-05): pure sign / correlation test. There is NO friction,
edge, bps, PnL or Sharpe column — adding one would be a gate violation. This
driver reports each criterion individually and emits ``sign_direction`` +
``inverse_significant`` so the gate-auditor can tell an H-05 pass apart from an
H-05b trigger (significant inverse direction). It renders NO overall verdict.

Mirrors the C-31 / C-17 read-only pattern (DEC-03/DEC-09/DEC-10):
``_open_db_with_timeout`` (30s daemon thread), ``--db-copy`` temp-copy against
the collector RW lock, epoch-ms plausibility filter, deterministic-chronological
window split with a WINDOW_MAX_TICKS cap, progress logging on stderr.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .ofi import DEFAULT_GRID_MS, DEFAULT_LAGS_S, ofi_and_forward_return
from .sign_test import (
    ABS_CORR_FLOOR,
    FDR_ALPHA,
    HIT_RATE_FLOOR,
    SURROGATE_P_MAX,
    benjamini_hochberg,
    sign_test,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-05"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
MIN_WINDOWS = 2  # registered (>= 2 disjoint windows)

#: Default symbol universe (registry H-05): Futures-Perp 5er-Universum.
DEFAULT_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
)

#: Deterministic per-window tick cap (DEC-11, mirrors DEC-09/DEC-10). The
#: bestand trades table spans days/weeks; a sign test needs no day-long windows.
#: ~300k trades per window span ample minutes of the 1-300 s structure while
#: keeping the (deltas x surrogates x symbols) workload tractable and
#: within-window stationarity intact.
WINDOW_MAX_TICKS = 300_000

DB_OPEN_TIMEOUT_S = 30.0
DB_LOCKED_HINT = (
    "DuckDB gesperrt — --db-copy nutzen oder Collector kurz stoppen "
    "(liest eine temporaere Kopie der .duckdb-Datei, lock-frei)"
)

# Epoch-ms plausibility window (collector contract TradeEvent.timestamp_ms).
TS_PLAUSIBLE_MIN_MS = 1_262_304_000_000  # 2010-01-01 UTC
TS_PLAUSIBLE_MAX_MS = 4_102_444_800_000  # 2100-01-01 UTC


class DataError(RuntimeError):
    """Raised on missing / malformed input (CLI maps this to exit-code 1)."""


# ----------------------------------------------------------------------------
# Read-only loaders (mirror c31_cfar / c17_c41 driver)
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

    t = threading.Thread(target=_work, name="c01-db-open", daemon=True)
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
class TradeArrays:
    """Per-symbol trade columns (ts ascending) for the OFI estimator."""

    ts: np.ndarray
    price: np.ndarray
    volume: np.ndarray
    side: np.ndarray

    @property
    def size(self) -> int:
        return int(self.ts.size)


def load_trades_duckdb(
    db_path: Path,
    symbol: str,
    *,
    db_copy: bool = False,
    _shared_copy_dir: Path | None = None,
) -> TradeArrays:
    """Load ``(ts, price, volume, side)`` for one symbol from ``trades``.

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

        copy_dir = Path(tempfile.mkdtemp(prefix="c01_dbcopy_"))
        copied = copy_dir / db_path.name
        print(f"[c01] --db-copy: copying {db_path} -> {copied}", file=sys.stderr, flush=True)
        shutil.copy2(db_path, copied)
        wal = db_path.with_name(db_path.name + ".wal")
        if wal.is_file():
            shutil.copy2(wal, copy_dir / wal.name)
        db_path = copied
    elif _shared_copy_dir is not None:
        db_path = _shared_copy_dir / Path(db_path).name

    print(f"[c01] opening duckdb read-only: {db_path} (symbol={symbol})", file=sys.stderr, flush=True)
    try:
        layer = _open_db_with_timeout(lambda: PersistenceLayer(db_path, read_only=True))
    except DataError:
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
        raise
    try:
        n_total = layer.conn.execute(
            "SELECT COUNT(*) FROM trades WHERE symbol = ?", [symbol]
        ).fetchone()[0]
        rows = layer.conn.execute(
            "SELECT ts, price, volume, side FROM trades "
            "WHERE symbol = ? AND ts >= ? AND ts <= ? ORDER BY ts",
            [symbol, TS_PLAUSIBLE_MIN_MS, TS_PLAUSIBLE_MAX_MS],
        ).fetchall()
    finally:
        layer.close()
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
            print(f"[c01] --db-copy: removed temp copy {copy_dir}", file=sys.stderr, flush=True)
    n_dropped = int(n_total) - len(rows)
    if n_dropped > 0:
        print(
            f"[c01] WARN: dropped {n_dropped} trades row(s) for {symbol} with "
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
    price = np.array([r[1] for r in rows], dtype=np.float64)
    volume = np.array([r[2] for r in rows], dtype=np.float64)
    side = np.array([str(r[3] or "") for r in rows], dtype=object)
    return TradeArrays(ts=ts, price=price, volume=volume, side=side)


def load_symbols_duckdb(
    db_path: Path,
    symbols: tuple[str, ...],
    *,
    db_copy: bool = False,
) -> dict[str, TradeArrays]:
    """Load all requested symbols, sharing a single ``--db-copy`` temp copy."""
    copy_dir: Path | None = None
    db_path = Path(db_path)
    out: dict[str, TradeArrays] = {}
    try:
        if db_copy:
            import shutil
            import tempfile

            if not db_path.exists():
                raise DataError(f"DuckDB file not found: {db_path}")
            copy_dir = Path(tempfile.mkdtemp(prefix="c01_dbcopy_"))
            copied = copy_dir / db_path.name
            print(f"[c01] --db-copy: copying {db_path} -> {copied}", file=sys.stderr, flush=True)
            shutil.copy2(db_path, copied)
            wal = db_path.with_name(db_path.name + ".wal")
            if wal.is_file():
                shutil.copy2(wal, copy_dir / wal.name)
        for sym in symbols:
            out[sym] = load_trades_duckdb(db_path, sym, _shared_copy_dir=copy_dir)
        return out
    finally:
        if copy_dir is not None:
            import shutil

            shutil.rmtree(copy_dir, ignore_errors=True)
            print(f"[c01] --db-copy: removed temp copy {copy_dir}", file=sys.stderr, flush=True)


def load_trades_file(path: Path, symbol: str = "FILE") -> dict[str, TradeArrays]:
    """Load ``(ts, price, volume, side)`` from a CSV/Parquet file (read-only)."""
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
    vol_col = next((c for c in ("volume", "v", "qty", "size") if c in df.columns), None)
    side_col = next((c for c in ("side", "S") if c in df.columns), None)
    if ts_col is None or px_col is None or vol_col is None or side_col is None:
        raise DataError(
            f"file {p} missing ts/price/volume/side columns (have {list(df.columns)})"
        )
    ts = df[ts_col].to_numpy(dtype=np.float64)
    price = df[px_col].to_numpy(dtype=np.float64)
    volume = df[vol_col].to_numpy(dtype=np.float64)
    side = df[side_col].astype(str).to_numpy(dtype=object)
    if ts.size == 0:
        raise DataError(f"file {p} contains no rows")
    order = np.argsort(ts, kind="stable")
    return {symbol: TradeArrays(ts[order], price[order], volume[order], side[order])}


# ----------------------------------------------------------------------------
# Deterministic-chronological window split
# ----------------------------------------------------------------------------

def split_windows(
    arr: TradeArrays,
    n_windows: int,
    *,
    max_ticks_per_window: int = WINDOW_MAX_TICKS,
) -> list[TradeArrays]:
    """Split one symbol's trades into ``n_windows`` disjoint contiguous windows.

    DEC-11 (mirrors DEC-09/DEC-10): first cap to the most recent
    ``n_windows x max_ticks_per_window`` trades (deterministic-chronological, no
    discretionary selection — registry H-05 wording preserved), then cut the
    capped series into ``n_windows`` equal-time disjoint slices. The H-05 gate
    thresholds are NOT affected by this scoping.
    """
    if n_windows < MIN_WINDOWS:
        raise DataError(f"H-05 requires >= {MIN_WINDOWS} disjoint windows, got {n_windows}")
    if max_ticks_per_window < 8:
        raise DataError(f"max_ticks_per_window must be >= 8, got {max_ticks_per_window}")
    budget = n_windows * int(max_ticks_per_window)
    ts, price, volume, side = arr.ts, arr.price, arr.volume, arr.side
    if ts.size > budget:
        ts, price, volume, side = ts[-budget:], price[-budget:], volume[-budget:], side[-budget:]
    if ts.size < n_windows * 4:
        raise DataError(f"too few trades ({ts.size}) to form {n_windows} windows")
    t0, t1 = float(ts[0]), float(ts[-1])
    if t1 <= t0:
        raise DataError("symbol trades have zero time span")
    edges = np.linspace(t0, t1, n_windows + 1)
    out: list[TradeArrays] = []
    for k in range(n_windows):
        lo, hi = edges[k], edges[k + 1]
        last = k == n_windows - 1
        m = (ts >= lo) & ((ts <= hi) if last else (ts < hi))
        out.append(TradeArrays(ts[m], price[m], volume[m], side[m]))
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
    variants: list[dict[str, Any]] = field(default_factory=list)  # one per delta


def _build_variants(
    win: TradeArrays,
    *,
    symbol: str,
    window_index: int,
    n_windows: int,
    lags_s: tuple[int, ...],
    grid_ms: float,
    n_surrogates: int,
    seed: int,
) -> WindowSymbolResult:
    """Run the OFI-sign test for every delta on one (symbol, window)."""
    res = WindowSymbolResult(
        symbol=symbol, window_index=window_index,
        t0_ms=float(win.ts[0]) if win.size else 0.0,
        t1_ms=float(win.ts[-1]) if win.size else 0.0,
    )
    for di, delta_s in enumerate(lags_s):
        ofi, fwd = ofi_and_forward_return(
            win.ts, win.price, win.volume, win.side, grid_ms, float(delta_s),
        )
        st = sign_test(
            ofi, fwd, float(delta_s),
            n_surrogates=n_surrogates,
            # deterministic per (symbol, window, delta) seed offset
            seed=seed + 1000 * (window_index + 1) + 7 * (di + 1) + abs(hash(symbol)) % 991,
        )
        entry = st.as_dict()
        entry["label"] = f"{symbol}_w{window_index}_d{delta_s}s"
        res.variants.append(entry)
        print(
            f"[c01] {symbol} window {window_index + 1}/{n_windows} "
            f"delta={delta_s}s: n={st.n_pairs} corr={st.corr:+.4f} "
            f"sign={st.sign_direction:+d} |corr|={st.abs_corr:.4f} "
            f"hit={st.hit_rate:.3f} surr_p={st.surrogate_p:.4f}",
            file=sys.stderr, flush=True,
        )
    return res


def run(
    symbol_arrays: dict[str, TradeArrays],
    *,
    n_windows: int,
    lags_s: tuple[int, ...] = DEFAULT_LAGS_S,
    grid_ms: float = DEFAULT_GRID_MS,
    n_surrogates: int = 200,
    seed: int = 42,
    max_ticks_per_window: int = WINDOW_MAX_TICKS,
    source: str = "",
) -> dict[str, Any]:
    """Run the full C-01 OFI-sign pipeline over all symbols x >= 2 windows.

    BH-FDR is applied across the WHOLE F-OFI family (all delta x symbol x window
    variants), per registry H-05. Each criterion is reported individually; the
    payload carries ``sign_direction`` and ``inverse_significant`` but NO overall
    verdict (gate-auditor's call).
    """
    symbols = tuple(symbol_arrays.keys())
    # 1) Split + measure every (symbol, window, delta) variant.
    all_results: list[WindowSymbolResult] = []
    for sym in symbols:
        windows = split_windows(
            symbol_arrays[sym], n_windows, max_ticks_per_window=max_ticks_per_window,
        )
        print(
            f"[c01] {sym}: {symbol_arrays[sym].size} trades loaded, "
            f"{len(windows)} window(s) (cap {max_ticks_per_window}/window, "
            f"deltas={list(lags_s)}s, grid={grid_ms:g}ms, surrogates={n_surrogates})",
            file=sys.stderr, flush=True,
        )
        for wi, win in enumerate(windows):
            all_results.append(_build_variants(
                win, symbol=sym, window_index=wi, n_windows=len(windows),
                lags_s=lags_s, grid_ms=grid_ms,
                n_surrogates=n_surrogates, seed=seed,
            ))

    # 2) BH-FDR over the whole F-OFI family (all variants across all results).
    flat = [v for r in all_results for v in r.variants]
    p_values = [float(v["surrogate_p"]) for v in flat]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for v, rej in zip(flat, rejected):
        v["fdr_significant"] = bool(rej)
        # Per-variant criterion read-outs (reported, NOT adjudicated here):
        sd = int(v["sign_direction"])
        mag_ok = (v["abs_corr"] >= ABS_CORR_FLOOR) or (v["hit_rate"] >= HIT_RATE_FLOOR)
        # WEITER (aggression-follow) requires sign +, FDR sig, magnitude floor.
        v["weiter_direction_positive"] = sd > 0
        v["magnitude_floor_met"] = bool(mag_ok)
        v["abs_corr_floor_met"] = bool(v["abs_corr"] >= ABS_CORR_FLOOR)
        v["hit_rate_floor_met"] = bool(v["hit_rate"] >= HIT_RATE_FLOOR)
        # H-05 per-variant existence with CORRECT (positive) direction.
        v["h05_positive_consistent"] = bool(
            sd > 0 and v["fdr_significant"] and mag_ok
        )
        # INVERSE significance = negative direction, FDR sig, magnitude floor.
        # This is the H-05b trigger (MM-replenishment), NOT an H-05 pass.
        v["inverse_significant"] = bool(
            sd < 0 and v["fdr_significant"] and mag_ok
        )

    n_fdr_sig = sum(1 for v in flat if v["fdr_significant"])
    any_inverse = any(v["inverse_significant"] for v in flat)
    any_nonpositive_window = any(int(v["sign_direction"]) <= 0 for v in flat)

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
        "grid_ms": grid_ms,
        "lags_s": list(lags_s),
        "max_ticks_per_window": int(max_ticks_per_window),
        "gate_thresholds": {
            "surrogate_p_max": SURROGATE_P_MAX,
            "abs_corr_floor": ABS_CORR_FLOOR,
            "hit_rate_floor": HIT_RATE_FLOOR,
            "min_windows": MIN_WINDOWS,
            "positive_sign_required_for_weiter": True,
        },
        "fdr_p_crit": p_crit,
        "n_fdr_significant": n_fdr_sig,
        # Family-level observation flags (NEUTRAL — gate-auditor adjudicates):
        "any_inverse_significant": bool(any_inverse),
        "any_nonpositive_sign_window": bool(any_nonpositive_window),
        "results": [
            {
                "symbol": r.symbol,
                "window_index": r.window_index,
                "t0_ms": r.t0_ms,
                "t1_ms": r.t1_ms,
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


def _sign_str(s: int) -> str:
    return "+" if s > 0 else ("-" if s < 0 else "0")


def render_markdown(payload: dict[str, Any]) -> str:
    """German Markdown report — one criterion per delta per window per symbol."""
    L: list[str] = []
    L.append("# C-01 OFI-Vorzeichen-Mess-Gate (H-05 · INC-02-Anker, KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Symbole: {', '.join(payload['symbols'])})")
    L.append(
        f"- **Fenster:** {payload['n_windows']} · **Surrogates:** {payload['n_surrogates']} · "
        f"**Seed:** {payload['seed']} · **BH-FDR alpha:** {payload['fdr_alpha']}"
    )
    L.append(
        f"- **Grid:** {payload['grid_ms']:g} ms · **delta-Lags:** {payload['lags_s']} s · "
        f"**Tick-Cap/Fenster:** {payload['max_ticks_per_window']}"
    )
    L.append(
        f"- **KAPITALFREI:** {_fmt(payload['capital_free'])} — reiner Vorzeichen-/"
        "Korrelations-Mess-Test, KEINE bps/Edge/PnL/Sharpe/Friction-Metrik."
    )
    L.append("")
    L.append(
        "> Der Report liefert jedes Gate-Kriterium EINZELN je Fenster/delta/Symbol. "
        "`sign_direction` (+/-/0) und `inverse_significant` sind NEUTRAL gemeldet — "
        "ein signifikant INVERSES Vorzeichen ist KEIN H-05-Bestehen, sondern Ausloeser "
        "fuer eine separate H-05b (MM-Replenishment). Das GATE-URTEIL "
        "(WEITER/DROP/H-05b) faellt der gate-auditor gegen H-05 (hartes Ein-Fenster-"
        "Kriterium, PRD §8.5)."
    )
    L.append("")
    L.append(
        f"**F-OFI BH-FDR p_crit:** {_fmt(payload['fdr_p_crit'])} · "
        f"**FDR-signifikante Varianten:** {payload['n_fdr_significant']}"
    )
    L.append(
        f"**Beobachtung (NEUTRAL):** inverse Richtung irgendwo signifikant: "
        f"{_fmt(payload['any_inverse_significant'])} · nicht-positives Vorzeichen "
        f"in >=1 Fenster: {_fmt(payload['any_nonpositive_sign_window'])}"
    )
    L.append("")
    L.append(
        "| Symbol | Fenster | delta (s) | n | corr | sign | \\|corr\\| | Hit-Rate "
        "| Surr p | FDR sig | Magnitude-Floor | pos.+konsistent | inverse_sig |"
    )
    L.append("|---|---:|---:|---:|---:|:--:|---:|---:|---:|:--:|:--:|:--:|:--:|")
    for r in payload["results"]:
        for v in r["variants"]:
            L.append(
                f"| {r['symbol']} | {r['window_index']} | {v['delta_s']:.0f} "
                f"| {v['n_pairs']} | {_fmt(v['corr'])} | {_sign_str(int(v['sign_direction']))} "
                f"| {_fmt(v['abs_corr'])} | {_fmt(v['hit_rate'], 3)} | {_fmt(v['surrogate_p'])} "
                f"| {_fmt(v['fdr_significant'])} | {_fmt(v['magnitude_floor_met'])} "
                f"| {_fmt(v['h05_positive_consistent'])} | {_fmt(v['inverse_significant'])} |"
            )
    L.append("")
    L.append("---")
    L.append(
        "**Gate-Schwellen (registriert, NICHT hier beurteilt):** "
        f"Surrogate p <= {payload['gate_thresholds']['surrogate_p_max']} (BH-FDR alpha "
        f"{payload['fdr_alpha']} ueber F-OFI) UND Vorzeichen = + (Aggression-Folge) UND "
        f"(\\|corr\\| >= {payload['gate_thresholds']['abs_corr_floor']} ODER Hit-Rate >= "
        f"{payload['gate_thresholds']['hit_rate_floor']}) in >= "
        f"{payload['gate_thresholds']['min_windows']} disjunkten Fenstern. "
        "Vorzeichen <= 0 in >=1 Fenster ODER Magnitude verfehlt ODER FDR-p > 0.05 = DROP. "
        "Signifikant INVERS = H-05b-Ausloeser, kein Bestehen."
    )
    L.append("")
    L.append(
        "*Erzeugt von `scripts/c01_ofi_sign.py` (Welle-2-WP, read-only Driver, DEC-11, "
        "eigener OFI-Schaetzer — `m2_ofi.py` unberuehrt). KAPITALFREI. "
        f"Endgueltiges Gate-Urteil: gate-auditor gegen {HYPOTHESIS_ID}.*"
    )
    L.append("")
    return "\n".join(L)


def write_outputs(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``c01_ofi_sign_results.json`` + ``.md`` to ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c01_ofi_sign_results.json"
    md_path = out_dir / "c01_ofi_sign_results.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path
