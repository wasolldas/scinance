"""Read-only driver for the C-31 CFAR research pipeline (WP-3, H-03).

Loads publicTrade ticks (timestamp + price) from either the existing DuckDB
``trades`` table OR a CSV/Parquet file (fixtures + exported replay data),
splits them into >= 2 disjoint chronological windows (registry H-03), runs the
full bin → SCD → CA-CFAR → surrogate → lead/edge pipeline per window across the
F-CFAR parameter family (BH-FDR alpha = 0.10), and writes ``c31_cfar_results.json``
+ a Markdown report listing — per window — peaks, FDR'd p-values, lead, edge and
the *status of each gate criterion*.

DEC-03: this is a standalone research package with a *read-only* driver — it
NEVER touches the live pipeline / replay_backtester and never writes to the
existing trades table. The GATE VERDICT itself is the gate-auditor's call; this
driver only reports each criterion individually.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .cfar_detector import CfarConfig, detect_peaks
from .cyclic_spectrum import (
    DEFAULT_BIN_GRID_MS,
    bin_counts,
    spectral_correlation_density,
)
from .lead_edge import EDGE_MIN_BPS, LEAD_MIN_MS, measure_lead_edge
from .surrogate import FDR_ALPHA, benjamini_hochberg, surrogate_test

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-03"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
SURROGATE_P_MAX = 0.05  # registered (PRD §3 Pilot 4)
MIN_WINDOWS = 2         # registered (>= 2 disjoint windows)


class DataError(RuntimeError):
    """Raised on missing / malformed input (CLI maps this to exit-code 1)."""


# ----------------------------------------------------------------------------
# Read-only loaders
# ----------------------------------------------------------------------------

def load_trades_duckdb(
    db_path: Path, symbol: str, start_ts: int | None = None, end_ts: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Load (ts_ms, price) from the existing DuckDB ``trades`` table, read-only.

    Uses ``PersistenceLayer(read_only=True)`` so it can attach concurrently to a
    DB held by the live runner without fighting the writer lock.
    """
    try:
        from bybit_edge.persistence.db import PersistenceLayer
    except Exception as exc:  # pragma: no cover - import guard
        raise DataError(f"cannot import PersistenceLayer: {exc}") from exc
    if not Path(db_path).exists():
        raise DataError(f"DuckDB file not found: {db_path}")
    layer = PersistenceLayer(Path(db_path), read_only=True)
    try:
        where = "symbol = ?"
        params: list[Any] = [symbol]
        if start_ts is not None:
            where += " AND ts >= ?"
            params.append(int(start_ts))
        if end_ts is not None:
            where += " AND ts <= ?"
            params.append(int(end_ts))
        rows = layer.conn.execute(
            f"SELECT ts, price FROM trades WHERE {where} ORDER BY ts", params
        ).fetchall()
    finally:
        layer.close()
    if not rows:
        raise DataError(f"no trades for symbol={symbol} in {db_path}")
    ts = np.array([r[0] for r in rows], dtype=np.float64)
    px = np.array([r[1] for r in rows], dtype=np.float64)
    return ts, px


def load_trades_file(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load (ts_ms, price) from a CSV or Parquet file (read-only).

    Expected columns: a timestamp column (``ts`` | ``timestamp_ms`` | ``T``)
    and a price column (``price`` | ``p``).
    """
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
        raise DataError(
            f"file {p} missing ts/price columns (have {list(df.columns)})"
        )
    ts = df[ts_col].to_numpy(dtype=np.float64)
    px = df[px_col].to_numpy(dtype=np.float64)
    if ts.size == 0:
        raise DataError(f"file {p} contains no rows")
    order = np.argsort(ts, kind="stable")
    return ts[order], px[order]


def split_windows(
    ts: np.ndarray, px: np.ndarray, n_windows: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Split chronologically into ``n_windows`` disjoint, contiguous windows."""
    if n_windows < MIN_WINDOWS:
        raise DataError(
            f"H-03 requires >= {MIN_WINDOWS} disjoint windows, got {n_windows}"
        )
    n = ts.size
    if n < n_windows * 8:
        raise DataError(
            f"too few ticks ({n}) to form {n_windows} usable windows"
        )
    bounds = np.linspace(0, n, n_windows + 1, dtype=int)
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for k in range(n_windows):
        lo, hi = bounds[k], bounds[k + 1]
        out.append((ts[lo:hi], px[lo:hi]))
    return out


# ----------------------------------------------------------------------------
# F-CFAR parameter family
# ----------------------------------------------------------------------------

@dataclass(slots=True)
class ParamVariant:
    """One member of the F-CFAR parameter family."""

    bin_dt_ms: float
    threshold_factor: float

    @property
    def label(self) -> str:
        return f"dt{self.bin_dt_ms:g}ms_T{self.threshold_factor:g}"


def default_family(
    bin_grid: tuple[float, ...] = DEFAULT_BIN_GRID_MS,
    thresholds: tuple[float, ...] = (6.0,),
) -> list[ParamVariant]:
    """Default F-CFAR family: bin-grid sweep × CFAR-threshold sweep."""
    return [ParamVariant(dt, t) for dt in bin_grid for t in thresholds]


# ----------------------------------------------------------------------------
# Per-window pipeline
# ----------------------------------------------------------------------------

@dataclass(slots=True)
class WindowResult:
    index: int
    n_ticks: int
    t0_ms: float
    t1_ms: float
    variants: list[dict[str, Any]] = field(default_factory=list)
    best: dict[str, Any] | None = None
    criteria: dict[str, Any] = field(default_factory=dict)


def run_window(
    index: int,
    ts: np.ndarray,
    px: np.ndarray,
    family: list[ParamVariant],
    *,
    n_surrogates: int,
    seed: int,
    segment_len: int,
    n_alpha: int,
) -> WindowResult:
    """Run the full pipeline over one window across the F-CFAR family.

    BH-FDR (alpha = 0.10) is applied across the family's surrogate p-values.
    The window's "best" variant is the FDR-surviving variant with the lowest
    p-value (ties broken by SNR); lead/edge are measured on its top peak.
    """
    wr = WindowResult(
        index=index, n_ticks=int(ts.size),
        t0_ms=float(ts[0]) if ts.size else 0.0,
        t1_ms=float(ts[-1]) if ts.size else 0.0,
    )

    p_values: list[float] = []
    per_variant: list[dict[str, Any]] = []
    for vi, variant in enumerate(family):
        cfar = CfarConfig(threshold_factor=variant.threshold_factor)
        # Deterministic per-variant seed offset (reproducible).
        sres = surrogate_test(
            ts,
            bin_dt_ms=variant.bin_dt_ms,
            cfar=cfar,
            n_surrogates=n_surrogates,
            seed=seed + vi,
            segment_len=segment_len,
            n_alpha=n_alpha,
        )
        # Recover the top peak (alpha) for lead/edge measurement.
        counts, fs_hz = bin_counts(ts, variant.bin_dt_ms)
        spectrum = spectral_correlation_density(
            counts, fs_hz, segment_len=segment_len, n_alpha=n_alpha
        )
        peaks = detect_peaks(spectrum, cfar)
        top_alpha = peaks[0].alpha_hz if peaks else 0.0
        entry: dict[str, Any] = {
            "variant": variant.label,
            "bin_dt_ms": variant.bin_dt_ms,
            "threshold_factor": variant.threshold_factor,
            "n_peaks": len(peaks),
            "top_alpha_hz": top_alpha,
            "top_peak": peaks[0].as_dict() if peaks else None,
            "surrogate": sres.as_dict(),
            "nominal_pfa": cfar.nominal_pfa(),
        }
        per_variant.append(entry)
        p_values.append(sres.p_value)

    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for entry, rej in zip(per_variant, rejected):
        entry["fdr_significant"] = bool(rej)
    wr.variants = per_variant

    # Pick the best FDR-surviving variant (lowest p, then highest SNR).
    survivors = [e for e in per_variant if e["fdr_significant"]]
    pool = survivors if survivors else per_variant
    best = min(
        pool,
        key=lambda e: (e["surrogate"]["p_value"], -e["surrogate"]["observed_snr"]),
    )
    wr.best = best

    # Lead/edge on the best variant's top alpha (only meaningful if a peak exists).
    le: dict[str, Any] | None = None
    if best["top_alpha_hz"] > 0:
        ler = measure_lead_edge(ts, px, best["top_alpha_hz"])
        le = ler.as_dict()
    best_p = best["surrogate"]["p_value"]
    lead_ms = le["lead_ms"] if le else 0.0
    edge_bps = le["edge_bps"] if le else 0.0

    wr.criteria = {
        "surrogate_p": {
            "value": best_p,
            "threshold": SURROGATE_P_MAX,
            "fdr_significant": best["fdr_significant"],
            "passed": (best_p <= SURROGATE_P_MAX) and best["fdr_significant"],
            "registry_text": "Surrogate p <= 0.05 (FDR-korrigiert, F-CFAR)",
        },
        "lead_ms": {
            "value": lead_ms,
            "threshold": LEAD_MIN_MS,
            "passed": lead_ms > LEAD_MIN_MS,
            "registry_text": "Lead-Zeit > 50 ms (ueber Retail-Latenz)",
        },
        "edge_bps": {
            "value": edge_bps,
            "threshold": EDGE_MIN_BPS,
            "passed": edge_bps > EDGE_MIN_BPS,
            "registry_text": "Edge > 11 bps (ueber der Friction-Wand)",
        },
        "fdr_p_crit": p_crit,
        "lead_edge": le,
    }
    return wr


# ----------------------------------------------------------------------------
# Orchestration + report
# ----------------------------------------------------------------------------

def run(
    ts: np.ndarray,
    px: np.ndarray,
    *,
    n_windows: int,
    family: list[ParamVariant] | None = None,
    n_surrogates: int = 200,
    seed: int = 42,
    segment_len: int = 256,
    n_alpha: int = 64,
    source: str = "",
    symbol: str = "",
) -> dict[str, Any]:
    """Run the full C-31 pipeline over >= 2 windows and assemble the payload."""
    fam = family if family is not None else default_family()
    windows = split_windows(ts, px, n_windows)
    win_results = [
        run_window(
            i, w_ts, w_px, fam,
            n_surrogates=n_surrogates, seed=seed,
            segment_len=segment_len, n_alpha=n_alpha,
        )
        for i, (w_ts, w_px) in enumerate(windows)
    ]

    # Hard one-window criterion (PRD §8.5): a window fails if ANY criterion
    # fails in it. The driver reports each criterion; the gate-auditor rules.
    per_window_all_pass = []
    for wr in win_results:
        c = wr.criteria
        per_window_all_pass.append(
            bool(c["surrogate_p"]["passed"] and c["lead_ms"]["passed"] and c["edge_bps"]["passed"])
        )
    all_windows_pass = (
        len(win_results) >= MIN_WINDOWS and all(per_window_all_pass)
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbol": symbol,
        "n_windows": len(win_results),
        "n_surrogates": n_surrogates,
        "seed": seed,
        "fdr_alpha": FDR_ALPHA,
        "family": [v.label for v in fam],
        "gate_thresholds": {
            "surrogate_p_max": SURROGATE_P_MAX,
            "lead_min_ms": LEAD_MIN_MS,
            "edge_min_bps": EDGE_MIN_BPS,
            "min_windows": MIN_WINDOWS,
        },
        "all_windows_pass": all_windows_pass,
        "per_window_pass": per_window_all_pass,
        "windows": [
            {
                "index": wr.index,
                "n_ticks": wr.n_ticks,
                "t0_ms": wr.t0_ms,
                "t1_ms": wr.t1_ms,
                "best_variant": wr.best["variant"] if wr.best else None,
                "criteria": wr.criteria,
                "variants": wr.variants,
            }
            for wr in win_results
        ],
    }


def _fmt(v: Any, digits: int = 3) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_markdown(payload: dict[str, Any]) -> str:
    """German Markdown report — one criterion per row, per window (H-03)."""
    L: list[str] = []
    L.append("# C-31 CFAR-Auswertung (H-03 · Cyclostationary Footprint)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Symbol `{payload['symbol']}`)")
    L.append(
        f"- **Fenster:** {payload['n_windows']} · **Surrogates:** "
        f"{payload['n_surrogates']} · **Seed:** {payload['seed']} · "
        f"**BH-FDR alpha:** {payload['fdr_alpha']}"
    )
    L.append(f"- **F-CFAR-Familie:** {', '.join(payload['family'])}")
    L.append("")
    L.append(
        "> Der Report liefert jedes Gate-Kriterium einzeln je Fenster. Das "
        "GATE-URTEIL (WEITER/DROP) faellt der gate-auditor gegen H-03 — hartes "
        "Ein-Fenster-Kriterium (PRD §8.5)."
    )
    L.append("")
    L.append(
        f"**Alle Fenster bestehen alle Kriterien:** "
        f"{_fmt(payload['all_windows_pass'])}"
    )
    L.append("")
    for w in payload["windows"]:
        c = w["criteria"]
        L.append(f"## Fenster {w['index']} — {w['n_ticks']} Ticks")
        L.append(f"- Zeitspanne: {w['t0_ms']:.0f} .. {w['t1_ms']:.0f} ms")
        L.append(f"- Beste Variante (F-CFAR): `{w['best_variant']}`")
        L.append("")
        L.append("| Kriterium | Registry-Text | Messwert | Schwelle | Bestanden |")
        L.append("|---|---|---:|---:|---|")
        sp = c["surrogate_p"]
        L.append(
            f"| Surrogate p | {sp['registry_text']} | {_fmt(sp['value'])} "
            f"| <= {sp['threshold']} | {_fmt(sp['passed'])} (FDR sig: {_fmt(sp['fdr_significant'])}) |"
        )
        ld = c["lead_ms"]
        L.append(
            f"| Lead | {ld['registry_text']} | {_fmt(ld['value'], 1)} ms "
            f"| > {ld['threshold']} | {_fmt(ld['passed'])} |"
        )
        ed = c["edge_bps"]
        L.append(
            f"| Edge | {ed['registry_text']} | {_fmt(ed['value'], 2)} bps "
            f"| > {ed['threshold']} | {_fmt(ed['passed'])} |"
        )
        L.append("")
        L.append(f"- BH-FDR p_crit: {_fmt(c['fdr_p_crit'])}")
        le = c.get("lead_edge")
        if le:
            L.append(
                f"- Top-alpha: {_fmt(le['alpha_hz'])} Hz "
                f"(Periode {_fmt(le['period_ms'], 1)} ms), "
                f"n_events={le['n_events']}, best bucket "
                f"{_fmt(le['best_bucket_return_bps'], 2)} bps"
            )
        L.append("")
    L.append("---")
    L.append(
        "*Erzeugt von `scripts/c31_cfar.py` (WP-3, read-only Driver, DEC-03). "
        f"Endgueltiges Gate-Urteil: gate-auditor gegen {HYPOTHESIS_ID}.*"
    )
    L.append("")
    return "\n".join(L)


def write_outputs(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``c31_cfar_results.json`` + ``c31_cfar_results.md`` to ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c31_cfar_results.json"
    md_path = out_dir / "c31_cfar_results.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path
