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
``data/harvest``), loaded via the bestand ``c01_ofi_sign.oos.load_harvest_window``
(re-exported here; NOT duplicated, NOT modified — read-only Schutzgut).

KAPITALFREI (registry H-09, ``capital_free=true``): pure structural /
behavioural measurement (notional counts + dimensionless excess-mass ratios).
A tradability follow-up would be a NEW H-09b, NOT implied.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# Bestand loader reuse (read-only harvester Hive tree, backfill single-trade
# JSON form). Re-exported for the CLI; NOT duplicated, NOT modified.
from bybit_edge.research.c01_ofi_sign.oos import (  # noqa: F401
    DataError,
    load_harvest_window,
)

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
    RISK_LIMIT_TIER1_KINK_USDT,
    gate_assumptions_valid,
)
from .stats import benjamini_hochberg

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-09"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-BUNCH"
MIN_WINDOWS = 2  # registered: >= 1 symbol must pass in BOTH windows

#: Pre-registered calendar windows (registry H-09, verbatim).
DEFAULT_WINDOW_A = ("2026-03-27", "2026-05-15")
DEFAULT_WINDOW_B = ("2026-05-16", "2026-07-04")

#: Per-window tick cap for the loader (operational memory bound, NOT a
#: registered threshold — the registered unit is the order aggregate).
WINDOW_MAX_TICKS = 50_000_000

__all__ = [
    "DEFAULT_WINDOW_A",
    "DEFAULT_WINDOW_B",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "MIN_WINDOWS",
    "WINDOW_MAX_TICKS",
    "DataError",
    "load_harvest_window",
    "render_markdown",
    "run",
    "write_outputs",
]


def _stable_symbol_offset(symbol: str) -> int:
    """Deterministic per-symbol seed offset (``hash()`` is process-randomised)."""
    return sum(ord(ch) * (i + 1) for i, ch in enumerate(symbol)) % 997


def run(
    symbol_windows: dict[str, list[Any]],
    *,
    window_labels: tuple[str, ...],
    kinks: dict[str, float] | None = None,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = 42,
    n_floor_orders: int = N_FLOOR_ORDERS,
    cf_expectation_floor: float = CF_EXPECTATION_FLOOR,
    source: str = "",
) -> dict[str, Any]:
    """Run the H-09 bunching gate over explicit pre-registered windows.

    ``symbol_windows[sym]`` is the ordered list of per-window trade arrays
    (objects with ``ts`` / ``side`` / ``price`` / ``volume``, e.g. the bestand
    ``TradeArrays``) for that symbol; window ``i`` corresponds to
    ``window_labels[i]``. ``kinks`` overrides the K_s dict (tests); by default
    the module constants (BTC registry-quoted, rest PLACEHOLDER) are used.

    Gate-neutral: reports every criterion individually per cell plus the
    ``weiter_indication`` flag; the gate-auditor adjudicates against H-09.
    """
    kink_map = dict(RISK_LIMIT_TIER1_KINK_USDT if kinks is None else kinks)
    symbols = tuple(symbol_windows.keys())
    n_windows = max((len(w) for w in symbol_windows.values()), default=0)
    if n_windows < MIN_WINDOWS:
        raise DataError(f"H-09 needs >= {MIN_WINDOWS} windows, got {n_windows}")

    gate_valid = gate_assumptions_valid(
        n_bootstrap=n_bootstrap,
        poly_degree=POLY_DEGREE,
        n_floor_orders=n_floor_orders,
        cf_expectation_floor=cf_expectation_floor,
    )

    cells: list[dict[str, Any]] = []
    for sym in symbols:
        if sym not in kink_map:
            raise DataError(f"no K_s kink registered for symbol {sym!r}")
        kink = float(kink_map[sym])
        for wi, win in enumerate(symbol_windows[sym]):
            notionals = aggregate_orders(win.ts, win.side, win.price, win.volume)
            print(
                f"[h09] {sym} window {wi} ({window_labels[wi] if wi < len(window_labels) else '?'}): "
                f"{win.ts.size} records -> {notionals.size} order aggregates, "
                f"K_s={kink:g} USDT, bootstrap={n_bootstrap}",
                file=sys.stderr, flush=True,
            )
            cell = estimate_cell(
                notionals, kink,
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
            cell["n_records_raw"] = int(win.ts.size)
            cell["kink_is_placeholder"] = bool(sym in KINK_PLACEHOLDER_SYMBOLS)
            cells.append(cell)
            print(
                f"[h09] {sym} window {wi}: n_band={cell['n_orders_in_band']} "
                f"b-={cell['b_minus']:.3f} b+={cell['b_plus']:.3f} "
                f"p={cell['bootstrap_p']:.4f} placebo_max={cell['b_placebo_max']:.3f} "
                f"valid={cell['cell_valid']}",
                file=sys.stderr, flush=True,
            )

    # BH-FDR over the WHOLE registered F-BUNCH family (all symbol x window
    # order-level cells — 10 tests in the full run; invalid cells stay in the
    # family with their measured p, the fixed family size is not shrunk).
    p_values = [c["bootstrap_p"] for c in cells]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for c, rej in zip(cells, rejected):
        c["fdr_significant"] = bool(rej)
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
    for sym in symbols:
        sym_cells = [c for c in cells if c["symbol"] == sym]
        passed_windows = sorted(c["window_index"] for c in sym_cells if c["passed"])
        per_symbol.append({
            "symbol": sym,
            "kink_usdt": float(kink_map[sym]),
            "kink_is_placeholder": bool(sym in KINK_PLACEHOLDER_SYMBOLS),
            "n_windows_measured": len(sym_cells),
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
    any_symbol_passed_both = any(s["passed_both_windows"] for s in per_symbol)
    weiter_indication = bool(any_symbol_passed_both and gate_valid)

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
        "gate_valid_assumptions": gate_valid,
        "gate_valid_assumptions_note": (
            "WEITER nur gueltig bei n_bootstrap >= 500 UND Polynom-Grad 7 UND "
            "N-Floor >= 2000 UND Counterfactual-Floor >= 50 (keine Band-/Bin-/"
            "Placebo-Anpassung, Registry H-09). Abweichung -> "
            "gate_valid_assumptions=false, eine WEITER-Indikation waere ungueltig."
        ),
        "fdr_p_crit": p_crit,
        "n_fdr_significant": sum(1 for c in cells if c["fdr_significant"]),
        "all_cells_invalid_by_window": all_cells_invalid_by_window,
        # Gate-neutral observation flags (the gate-auditor adjudicates):
        "any_symbol_passed_both_windows": bool(any_symbol_passed_both),
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
