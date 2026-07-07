"""H-11 driver — AnEn vol-regime forecast vs. HAR-RV (KAPITALFREI, DATA-GATED).

Orchestrates the pre-registered H-11 measurement gate (registry
``scinance2-impl/state/hypothesis_registry.md`` §H-11, Welle 4):

  1. **Unlock check FIRST** (``check_unlock``): H-11 is GESPERRT until the
     harvester tree confirms gapless coverage for bybit ``publicTrade`` AND
     ``rest.fundingRate``, BTC+ETH, over 2024-03-27..2026-03-26 (>= 730 days).
     The check counts available ``date=`` partition folders (the programmatic
     analogue of the DATASET.md §7 manifest done_days query — works against
     the raw tree without needing the sqlite manifest). If it fails, the run
     is a clean SKIP (payload with ``status="SKIP"``), never a crash.
  2. Per symbol: daily panel -> 5-feature state matrix + 3-day log-RV target.
  3. LOO-CRPS weight tuning on region L (2024-03-27..2025-09-30), frozen.
  4. AnEn (k=20, 30-day embargo) vs. HAR-RV (expanding <= t-30, monthly
     refit) forecasts over W1 (2025-10-01..2026-03-26) and W2
     (2026-03-27..2026-06-30); CRPS = |forecast - obs|; CRPSS per cell.
  5. Block bootstrap (5-day blocks, 1000 reps) per symbol x window for
     H0: mean(CRPS_HAR - CRPS_AnEn) <= 0; BH-FDR alpha=0.10 over F-ANEN
     (2 symbols x 2 windows = 4 cells).

The payload is GATE-NEUTRAL (per-cell observations + rollup flags only); the
gate-auditor adjudicates against the registered H-11 gate. KAPITALFREI:
measurement gate only. The registry notes the 25-75x friction-magnitude
inversion at the 3-day horizon purely narratively — monetisation would be a
NEW H-11b and no cost quantity of any kind is computed here.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .analog import EMBARGO_DAYS, K_ANALOGS, WEIGHT_GRID, analog_forecast, tune_weights_loo_crps
from .baseline import har_forecast_series
from .features import (
    TARGET_HORIZON_DAYS,
    build_daily_panel,
    compute_feature_matrix,
    compute_target,
    date_range,
)
from .stats import (
    BLOCK_LEN_DAYS,
    BOOTSTRAP_P_MAX,
    CRPSS_MIN,
    FDR_ALPHA,
    N_BOOTSTRAP,
    benjamini_hochberg,
    block_bootstrap_p,
    crps_point,
    crpss,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-11"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-ANEN"

#: Pre-registered symbol universe (registry H-11: BTC/ETH perp).
DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT")

#: Pre-registered windows (registry H-11, all disjoint).
TUNE_RANGE = ("2024-03-27", "2025-09-30")   # region L (LOO-CRPS weight tuning)
W1_RANGE = ("2025-10-01", "2026-03-26")     # pre-discovery OOS (backfill)
W2_RANGE = ("2026-03-27", "2026-06-30")     # base-store OOS
WINDOW_LABELS = ("W1", "W2")

#: Pre-registered unlock condition (registry H-11, data-gated).
UNLOCK_RANGE = ("2024-03-27", "2026-03-26")
UNLOCK_MIN_DAYS = 730
UNLOCK_STREAMS = ("publicTrade", "rest.fundingRate")


# ----------------------------------------------------------------------------
# Unlock check (must run BEFORE any data run — registry H-11 Entsperr-Bedingung)
# ----------------------------------------------------------------------------

def check_unlock(
    base_dir: Path | str,
    *,
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    streams: tuple[str, ...] = UNLOCK_STREAMS,
    start: str = UNLOCK_RANGE[0],
    end: str = UNLOCK_RANGE[1],
    min_days: int = UNLOCK_MIN_DAYS,
    exchange: str = "bybit",
) -> dict[str, Any]:
    """Programmatic H-11 unlock check against the harvester tree (read-only).

    GAPLESS coverage is required: for EVERY calendar day in [start, end] and
    for every (stream, symbol) pair, a ``date=<d>`` partition folder with at
    least one parquet file must exist — the raw-tree analogue of the
    DATASET.md §7 done_days manifest query (done_days == last-first+1). The
    range itself must span >= ``min_days`` days (730 for the registered
    2024-03-27..2026-03-26 range).

    Never raises on missing data — a locked state is a NORMAL outcome
    (returns ``unlocked=False`` with per-pair diagnostics).
    """
    base = Path(base_dir)
    required = date_range(start, end)
    n_required = len(required)
    details: list[dict[str, Any]] = []
    unlocked = n_required >= int(min_days)
    for stream in streams:
        for sym in symbols:
            sym_dir = base / "raw" / exchange / stream / f"symbol={sym}"
            missing: list[str] = []
            for d in required:
                part = sym_dir / f"date={d}"
                if not part.is_dir() or not any(part.glob("*.parquet")):
                    missing.append(d)
            ok = not missing
            unlocked = unlocked and ok
            details.append({
                "exchange": exchange,
                "stream": stream,
                "symbol": sym,
                "days_present": n_required - len(missing),
                "days_required": n_required,
                "gapless": ok,
                "missing_days_count": len(missing),
                "missing_days_sample": missing[:5],
            })
    return {
        "unlocked": bool(unlocked),
        "range": [start, end],
        "days_required": n_required,
        "min_days": int(min_days),
        "streams": list(streams),
        "symbols": list(symbols),
        "details": details,
    }


# ----------------------------------------------------------------------------
# Full run
# ----------------------------------------------------------------------------

def _window_indices(dates: list[str], w_start: str, w_end: str) -> np.ndarray:
    return np.array([i for i, d in enumerate(dates) if w_start <= d <= w_end],
                    dtype=np.int64)


def _skip_payload(unlock: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "data_gated": True,
        "status": "SKIP",
        "reason": ("H-11 gesperrt — Manifest-Coverage <"
                   f"{unlock['min_days']} Tage lueckenlos, Entsperr-Bedingung nicht erfuellt"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "unlock_check": unlock,
        "results": [],
    }


def run(
    base_dir: Path | str,
    *,
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    tune_range: tuple[str, str] = TUNE_RANGE,
    w1_range: tuple[str, str] = W1_RANGE,
    w2_range: tuple[str, str] = W2_RANGE,
    unlock_range: tuple[str, str] = UNLOCK_RANGE,
    unlock_min_days: int = UNLOCK_MIN_DAYS,
    k: int = K_ANALOGS,
    embargo: int = EMBARGO_DAYS,
    weight_grid: tuple[float, ...] = WEIGHT_GRID,
    block_len: int = BLOCK_LEN_DAYS,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 42,
    skip_unlock_check: bool = False,
    source: str = "",
) -> dict[str, Any]:
    """Run the full H-11 measurement gate (gate-neutral payload).

    Checks the unlock condition FIRST; if unmet, returns a clean SKIP payload
    (``status="SKIP"``, ``data_gated=True``) without touching any data.
    ``skip_unlock_check`` exists ONLY for synthetic-fixture tests, never for a
    registered run. Weight tuning is per symbol on region L (the 5-feature
    state is per symbol, registry H-11) and frozen before any OOS forecast.
    """
    unlock = check_unlock(
        base_dir, symbols=symbols,
        start=unlock_range[0], end=unlock_range[1], min_days=unlock_min_days,
    )
    if not unlock["unlocked"] and not skip_unlock_check:
        print(f"[c11_anen] SKIP: {HYPOTHESIS_ID} locked — unlock condition unmet "
              f"({unlock['range'][0]}..{unlock['range'][1]}, min {unlock['min_days']} days)",
              file=sys.stderr, flush=True)
        return _skip_payload(unlock, source)

    # panel spill: +3 days beyond W2 so the last W2 days keep an observable
    # 3-day target (data permitting; missing spill days => NaN target, skipped)
    panel_start = tune_range[0]
    panel_end = (date.fromisoformat(w2_range[1])
                 + timedelta(days=TARGET_HORIZON_DAYS)).isoformat()

    cells: list[dict[str, Any]] = []
    tuning_info: list[dict[str, Any]] = []
    for sym in symbols:
        print(f"[c11_anen] {sym}: building daily panel {panel_start}..{panel_end}",
              file=sys.stderr, flush=True)
        panel = build_daily_panel(base_dir, sym, panel_start, panel_end)
        feats, log_rv22 = compute_feature_matrix(panel.rv_daily, panel.funding_daily)
        targets = compute_target(panel.rv_daily, TARGET_HORIZON_DAYS)
        dates = panel.dates

        tune_idx = _window_indices(dates, tune_range[0], tune_range[1])
        print(f"[c11_anen] {sym}: LOO-CRPS weight tuning on L "
              f"({tune_range[0]}..{tune_range[1]}, {tune_idx.size} days, "
              f"grid size {len(weight_grid)}^5)", file=sys.stderr, flush=True)
        weights, tune_crps = tune_weights_loo_crps(
            feats, targets, tune_idx, grid=weight_grid, k=k, embargo=embargo,
            verbose=True,
        )
        tuning_info.append({
            "symbol": sym,
            "tune_range": list(tune_range),
            "weight_grid": list(weight_grid),
            "weights_frozen": [float(w) for w in weights],
            "loo_mean_crps": float(tune_crps),
        })

        for w_label, (w_start, w_end) in zip(WINDOW_LABELS, (w1_range, w2_range)):
            w_idx = _window_indices(dates, w_start, w_end)
            anen_fc: list[float] = []
            har_days: list[int] = []
            for t in w_idx:
                t = int(t)
                if not np.isfinite(targets[t]):
                    continue
                fc, _sel = analog_forecast(feats, targets, t, weights, k=k, embargo=embargo)
                if np.isfinite(fc):
                    anen_fc.append(fc)
                    har_days.append(t)
            har_idx = np.asarray(har_days, dtype=np.int64)
            if har_idx.size:
                har_fc, n_refits = har_forecast_series(
                    feats[:, 0], feats[:, 1], log_rv22, targets, dates, har_idx,
                    embargo=embargo,
                )
            else:
                har_fc, n_refits = np.empty(0, dtype=np.float64), 0
            # paired scoring: only days where BOTH forecasts exist
            anen_arr = np.asarray(anen_fc, dtype=np.float64)
            paired = np.isfinite(har_fc)
            obs = targets[har_idx][paired]
            c_anen = crps_point(anen_arr[paired], obs)
            c_har = crps_point(har_fc[paired], obs)
            n_days = int(paired.sum())
            skill = crpss(c_anen, c_har) if n_days else float("nan")
            d = c_har - c_anen  # H0: mean(HAR - AnEn) <= 0
            p_boot = block_bootstrap_p(d, block_len=block_len,
                                       n_bootstrap=n_bootstrap, seed=seed)
            cells.append({
                "symbol": sym,
                "window": w_label,
                "window_range": [w_start, w_end],
                "n_forecast_days": n_days,
                "n_har_refits": int(n_refits),
                "sum_crps_anen": float(np.sum(c_anen)) if n_days else None,
                "sum_crps_har": float(np.sum(c_har)) if n_days else None,
                "mean_crps_anen": float(np.mean(c_anen)) if n_days else None,
                "mean_crps_har": float(np.mean(c_har)) if n_days else None,
                "crpss": float(skill) if np.isfinite(skill) else None,
                "crpss_ge_min": bool(np.isfinite(skill) and skill >= CRPSS_MIN),
                "mean_crps_diff_har_minus_anen": float(np.mean(d)) if n_days else None,
                "bootstrap_p": float(p_boot),
            })
            print(f"[c11_anen] {sym} {w_label}: n={n_days} CRPSS="
                  f"{skill if np.isfinite(skill) else float('nan'):.4f} p={p_boot:.4f}",
                  file=sys.stderr, flush=True)

    # BH-FDR over the F-ANEN family (2 symbols x 2 windows = 4 cells).
    p_values = [c["bootstrap_p"] for c in cells]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for c, rej in zip(cells, rejected):
        c["fdr_significant"] = bool(rej)
        c["cell_pass"] = bool(c["crpss_ge_min"] and rej)

    # Gate-neutral per-symbol rollup (WEITER needs BOTH windows for >= 1 symbol).
    rollup: list[dict[str, Any]] = []
    for sym in symbols:
        sym_cells = [c for c in cells if c["symbol"] == sym]
        rollup.append({
            "symbol": sym,
            "windows_measured": len(sym_cells),
            "windows_pass": sum(1 for c in sym_cells if c["cell_pass"]),
            "both_windows_pass": bool(sym_cells
                                      and all(c["cell_pass"] for c in sym_cells)
                                      and len(sym_cells) >= 2),
        })
    any_symbol_both = any(r["both_windows_pass"] for r in rollup)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "data_gated": True,
        "status": "RUN",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(symbols),
        "unlock_check": unlock,
        "windows": {
            "tune_L": list(tune_range),
            "W1": list(w1_range),
            "W2": list(w2_range),
        },
        "method": {
            "k_analogs": int(k),
            "embargo_days": int(embargo),
            "weight_grid": list(weight_grid),
            "target_horizon_days": TARGET_HORIZON_DAYS,
            "crps": "point-forecast degenerate distribution: |forecast - obs|",
            "block_len_days": int(block_len),
            "n_bootstrap": int(n_bootstrap),
            "seed": int(seed),
        },
        "fdr_family": FDR_FAMILY,
        "fdr_alpha": FDR_ALPHA,
        "fdr_p_crit": float(p_crit),
        "n_fdr_significant": int(sum(rejected)),
        "gate_thresholds": {
            "crpss_min": CRPSS_MIN,
            "bootstrap_p_max": BOOTSTRAP_P_MAX,
        },
        "tuning": tuning_info,
        "cells": cells,
        # gate-neutral observation flag (gate-auditor adjudicates):
        "any_symbol_both_windows_pass": bool(any_symbol_both),
        "per_symbol_rollup": rollup,
    }


# ----------------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------------

def render_markdown(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# H-11 — AnEn-Vol-Regime-Forecast vs. HAR-RV (KAPITALFREI, data-gated)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Status:** {payload['status']}")
    L.append(f"- **KAPITALFREI:** ja — reines Mess-Gate (CRPS-Verteilungsvergleich); "
             f"Monetarisierung waere NEUE H-11b.")
    u = payload["unlock_check"]
    L.append(f"- **Entsperr-Check:** {'ENTSPERRT' if u['unlocked'] else 'GESPERRT'} — "
             f"Coverage {u['range'][0]}..{u['range'][1]} "
             f"(>= {u['min_days']} Tage lueckenlos, publicTrade + rest.fundingRate, BTC+ETH)")
    if payload["status"] == "SKIP":
        L.append("")
        L.append(f"> **SKIP:** {payload['reason']}")
        L.append("")
        L.append("| Stream | Symbol | Tage vorhanden | Tage gefordert | lueckenlos |")
        L.append("|---|---|---:|---:|---|")
        for det in u["details"]:
            L.append(f"| {det['stream']} | {det['symbol']} | {det['days_present']} | "
                     f"{det['days_required']} | {'ja' if det['gapless'] else 'NEIN'} |")
        L.append("")
        L.append("*H-11 bleibt GESPERRT. Kein Datenlauf, kein Gate-Urteil. "
                 "Erneut pruefen, sobald der Deep-Backfill die Range abdeckt.*")
        return "\n".join(L)

    w = payload["windows"]
    m = payload["method"]
    L.append(f"- **Quelle:** `{payload['source']}` (Symbole: {', '.join(payload['symbols'])})")
    L.append(f"- **Fenster:** L={w['tune_L'][0]}..{w['tune_L'][1]} (Tuning) | "
             f"W1={w['W1'][0]}..{w['W1'][1]} | W2={w['W2'][0]}..{w['W2'][1]} (disjunkt)")
    L.append(f"- **Methode:** k={m['k_analogs']}, Embargo {m['embargo_days']} Tage, "
             f"Grid {m['weight_grid']}^5 (eingefroren nach L), Ziel log ann. RV "
             f"t+1..t+{m['target_horizon_days']}, CRPS=|Prognose-Beobachtung|")
    L.append(f"- **Null:** Block-Bootstrap (Blocklaenge {m['block_len_days']} Tage, "
             f"{m['n_bootstrap']} Reps, DM-artig), H0: mean(CRPS_HAR-CRPS_AnEn)<=0")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} · BH-FDR alpha={payload['fdr_alpha']} "
             f"· p_crit={payload['fdr_p_crit']:.4f}")
    L.append("")
    L.append("> Gate-Urteil faellt der gate-auditor gegen H-11. WEITER verlangt: fuer >=1 "
             "Symbol in {BTC,ETH} in BEIDEN Fenstern CRPSS>=0.05 UND Bootstrap-p<=0.05 "
             "nach BH-FDR alpha=0.10 ueber F-ANEN. Hartes Ein-Fenster-DROP, kein "
             "GRAUBEREICH, keine k-/Gewichts-/Feature-Nachsuche. A-priori: DROP.")
    L.append("")
    L.append("## Eingefrorene Gewichte (LOO-CRPS auf L)")
    L.append("")
    L.append("| Symbol | Gewichte (logRV1d, logRV5d, logRV20d, Funding-Mittel, Funding-Trend) | LOO-CRPS |")
    L.append("|---|---|---:|")
    for t in payload["tuning"]:
        L.append(f"| {t['symbol']} | {t['weights_frozen']} | {t['loo_mean_crps']:.5f} |")
    L.append("")
    L.append("## Zellen (F-ANEN: Symbol x Fenster)")
    L.append("")
    L.append("| Symbol | Fenster | n | mean CRPS AnEn | mean CRPS HAR | CRPSS | >=0.05 | boot-p | FDR-sig | Zelle |")
    L.append("|---|---|---:|---:|---:|---:|:---:|---:|:---:|:---:|")
    for c in payload["cells"]:
        L.append(
            f"| {c['symbol']} | {c['window']} | {c['n_forecast_days']} | "
            f"{_fmt(c['mean_crps_anen'])} | {_fmt(c['mean_crps_har'])} | "
            f"{_fmt(c['crpss'])} | {'ja' if c['crpss_ge_min'] else 'nein'} | "
            f"{c['bootstrap_p']:.4f} | {'ja' if c['fdr_significant'] else 'nein'} | "
            f"{'PASS' if c['cell_pass'] else 'nein'} |"
        )
    L.append("")
    L.append("## Symbol-Rollup (Gate-Kern, gate-neutral)")
    L.append("")
    L.append("| Symbol | Fenster gemessen | Fenster PASS | BEIDE Fenster PASS |")
    L.append("|---|---:|---:|:---:|")
    for r in payload["per_symbol_rollup"]:
        L.append(f"| {r['symbol']} | {r['windows_measured']} | {r['windows_pass']} | "
                 f"{'JA' if r['both_windows_pass'] else 'nein'} |")
    L.append("")
    L.append(f"**Mindestens ein Symbol mit beiden Fenstern PASS:** "
             f"{'ja' if payload['any_symbol_both_windows_pass'] else 'nein'}")
    L.append("")
    L.append("*Erzeugt von `c11_anen/driver.py` (read-only Harvester-Baum). "
             "capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-11.*")
    return "\n".join(L)


def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    return f"{float(v):.4f}"


__all__ = [
    "DEFAULT_SYMBOLS",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "TUNE_RANGE",
    "UNLOCK_MIN_DAYS",
    "UNLOCK_RANGE",
    "UNLOCK_STREAMS",
    "W1_RANGE",
    "W2_RANGE",
    "check_unlock",
    "render_markdown",
    "run",
]
