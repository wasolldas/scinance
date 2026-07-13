"""Read-only driver for the C-01 OFI-fade tradability-gate (H-05c, capital_free=FALSE).

Loads SOLUSDT publicTrade windows from the read-only harvester backfill (reusing
``c01_ofi_sign.oos.load_harvest_window``), runs the pre-fixed OFI-fade rule
(:mod:`fade_rule`) per window per delta in the GL-010 survivor set {1 s, 5 s},
confronts each round-trip's directional SOL capture move with the 11 bps friction
wall + 4 bps slippage after a 300 ms latency haircut (:mod:`costs`), and tests
whether the mean net edge is > 0 AND statistically > 0 (bootstrap p <= 0.05 after
BH-FDR over F-OFI-INV-TRADE) on >= 2 disjoint windows (:mod:`net_edge`).

The gate VERDICT (WEITER / DROP / PARK) is the gate-auditor's against H-05c. This
driver reports each criterion individually + the ``gate_valid_assumptions`` flag
(anti-gaming) and renders NO overall verdict.

NON-KAPITALFREI but a historical backtest with a cost model — NO live orders,
NO real capital (CLAUDE.md §4). The capital status stays PARK regardless.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np

from .costs import (
    BPS_PER_LOGRET,
    FRICTION_WALL_BPS,
    LATENCY_MS,
    SLIPPAGE_BPS,
    CostModel,
    gate_assumptions_valid,
    round_trip_net_edges_bps,
)
from .fade_rule import SURVIVOR_DELTAS_S, generate_round_trips
from .net_edge import (
    DEFAULT_BOOTSTRAP,
    FDR_ALPHA,
    NET_EDGE_P_MAX,
    NetEdgeResult,
    benjamini_hochberg,
    block_len_for_overlap,
    bootstrap_mean_le_zero_p,
    sign_permutation_p,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-05c"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
MIN_WINDOWS = 2
DEFAULT_GRID_MS = 1000.0
#: Pass-bearing cells (registry H-05c / DEC-16): only the GL-010 SOL survivors.
PASS_SYMBOL = "SOLUSDT"


@dataclass(slots=True)
class WindowDeltaResult:
    window_index: int
    delta_s: int
    t0_ms: float
    t1_ms: float
    net: NetEdgeResult


def _measure(
    win, *, window_index: int, delta_s: int, grid_ms: float, cost: CostModel,
    n_bootstrap: int, seed: int,
) -> WindowDeltaResult:
    """Run the fade rule + net-edge stats for one (window, delta)."""
    trips = generate_round_trips(
        win.ts, win.price, win.volume, win.side,
        delta_s=delta_s, grid_ms=grid_ms, latency_ms=cost.latency_ms,
    )
    n = len(trips)
    if n == 0:
        net = NetEdgeResult(delta_s, 0, 0.0, 0.0, cost.wall_bps, 0.0, 1.0, 1.0, n_bootstrap)
    else:
        captured = np.array([t.sol_move_captured for t in trips], dtype=np.float64)
        full = np.array([t.sol_move_full for t in trips], dtype=np.float64)
        signs = np.array([t.position_sign for t in trips], dtype=np.float64)
        # RAW (unsigned-by-position) captured move for the surrogate null.
        raw_captured = captured * signs  # undo the directional multiply
        net_edges = round_trip_net_edges_bps(captured, cost)
        # Consecutive round-trips share overlapping forward-return windows whenever
        # delta_s * 1000 > grid_ms (~80% overlap at delta_s=5s/grid_ms=1000ms) — block
        # the bootstrap resample to that overlap instead of resampling i.i.d. single
        # round-trips (CRITICAL_REVIEW_2_2026-07-13.md, Lane research-modules).
        block_len = block_len_for_overlap(delta_s, grid_ms)
        boot_p = bootstrap_mean_le_zero_p(
            net_edges, n_bootstrap=n_bootstrap, block_len=block_len, seed=seed,
        )
        surr_p = sign_permutation_p(
            raw_captured, signs, cost.wall_bps,
            bps_per_logret=BPS_PER_LOGRET, n_surrogates=n_bootstrap, seed=seed,
        )
        net = NetEdgeResult(
            delta_s=delta_s, n_trips=n,
            gross_capture_bps_mean=float(np.mean(captured) * BPS_PER_LOGRET),
            gross_full_bps_mean=float(np.mean(full) * BPS_PER_LOGRET),
            wall_bps=cost.wall_bps,
            net_edge_bps_mean=float(np.mean(net_edges)),
            bootstrap_p=boot_p, surrogate_p=surr_p, n_bootstrap=n_bootstrap,
        )
    print(
        f"[h05c] window {window_index} delta={delta_s}s: n_trips={net.n_trips} "
        f"gross_capture={net.gross_capture_bps_mean:+.3f}bps wall={net.wall_bps:.1f} "
        f"net={net.net_edge_bps_mean:+.3f}bps boot_p={net.bootstrap_p:.4f}",
        file=sys.stderr, flush=True,
    )
    return WindowDeltaResult(window_index, delta_s, float(win.ts[0]) if win.size else 0.0,
                             float(win.ts[-1]) if win.size else 0.0, net)


def run(
    windows: list,
    *,
    symbol: str = PASS_SYMBOL,
    deltas_s: tuple[int, ...] = SURVIVOR_DELTAS_S,
    grid_ms: float = DEFAULT_GRID_MS,
    friction_bps: float = FRICTION_WALL_BPS,
    slippage_bps: float = SLIPPAGE_BPS,
    latency_ms: float = LATENCY_MS,
    maker: bool = False,
    n_bootstrap: int = DEFAULT_BOOTSTRAP,
    seed: int = 42,
    source: str = "",
) -> dict[str, Any]:
    """Run the H-05c OFI-fade tradability gate over >= 2 SOL windows.

    BH-FDR over the whole F-OFI-INV-TRADE family (all delta x window). Per
    (delta) the cell passes when net edge > 0 AND bootstrap p <= 0.05 AND
    FDR-significant in >= 2 disjoint windows. Gate-neutral payload.
    """
    if len(windows) < MIN_WINDOWS:
        raise ValueError(f"H-05c needs >= {MIN_WINDOWS} windows, got {len(windows)}")
    cost = CostModel(friction_bps=friction_bps, slippage_bps=slippage_bps,
                     latency_ms=latency_ms, maker=maker)
    haircut_applied = latency_ms > 0.0
    valid = gate_assumptions_valid(
        latency_ms=latency_ms, friction_bps=friction_bps,
        haircut_applied=haircut_applied, maker=maker,
    ) and (symbol == PASS_SYMBOL)

    results: list[WindowDeltaResult] = []
    for wi, win in enumerate(windows):
        for d in deltas_s:
            results.append(_measure(
                win, window_index=wi, delta_s=d, grid_ms=grid_ms,
                cost=cost, n_bootstrap=n_bootstrap, seed=seed + 13 * (wi + 1) + d,
            ))

    # BH-FDR over the whole family (all delta x window bootstrap p-values).
    flat_p = [r.net.bootstrap_p for r in results]
    rejected, p_crit = benjamini_hochberg(flat_p, FDR_ALPHA)
    variants: list[dict[str, Any]] = []
    for r, rej in zip(results, rejected):
        d = r.net.as_dict()
        d["window_index"] = r.window_index
        d["t0_ms"] = r.t0_ms
        d["t1_ms"] = r.t1_ms
        d["fdr_significant"] = bool(rej)
        d["net_positive"] = bool(r.net.net_edge_bps_mean > 0.0)
        # per-variant pass: net > 0 AND bootstrap p <= 0.05 AND FDR-sig
        d["variant_pass"] = bool(
            r.net.net_edge_bps_mean > 0.0
            and r.net.bootstrap_p <= NET_EDGE_P_MAX
            and rej
        )
        variants.append(d)

    # Per-delta >= 2-window consistency (the gate core).
    consistency: list[dict[str, Any]] = []
    for d in deltas_s:
        cells = [v for v in variants if v["delta_s"] == d]
        passing = sorted(v["window_index"] for v in cells if v["variant_pass"])
        consistency.append({
            "delta_s": d,
            "n_windows_measured": len(cells),
            "n_windows_pass": len(passing),
            "passing_windows": passing,
            "tradable_consistent": bool(len(passing) >= MIN_WINDOWS),
        })

    any_tradable = any(c["tradable_consistent"] for c in consistency)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": False,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbol": symbol,
        "n_windows": len(windows),
        "deltas_s": list(deltas_s),
        "grid_ms": grid_ms,
        "horizon_rule": "horizon = delta (DEC-16 default)",
        "friction_wall_bps": friction_bps,
        "slippage_bps": slippage_bps,
        "latency_ms": latency_ms,
        "wall_bps_total": cost.wall_bps,
        "maker_secondary": bool(maker),
        "latenz_haircut_applied": bool(haircut_applied),
        "latenz_haircut_window": "[t+latenz, t+delta] (SOL capture, causal, no lookahead)",
        "registered_friction_wall_bps": FRICTION_WALL_BPS,
        "registered_latency_ms": LATENCY_MS,
        "pass_cells": [f"{PASS_SYMBOL}-d{d}s" for d in SURVIVOR_DELTAS_S],
        "gate_valid_assumptions": bool(valid),
        "gate_valid_assumptions_note": (
            "WEITER nur gueltig bei latency>=300ms UND friction>=11bps UND Latenz-Haircut "
            "angewandt UND Taker UND Pass-Zelle in {SOL-d1s,SOL-d5s}. Abweichung -> "
            "gate_valid_assumptions=false (Anti-Gaming, registry H-05c/DEC-16; andere Annahme "
            "= NEUE H-05d)."
        ),
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": "F-OFI-INV-TRADE",
        "fdr_p_crit": p_crit,
        "net_edge_p_max": NET_EDGE_P_MAX,
        "any_tradable_consistent": bool(any_tradable),
        "weiter_indication": bool(any_tradable and valid),
        "tradability_consistency": consistency,
        "variants": variants,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# C-01 OFI-Fade-TRADABILITY-Gate (H-05c · Friction-Wand + Latenz-Haircut, capital_free=FALSE)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}` (+ DEC-16)")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Symbol {payload['symbol']})")
    L.append(f"- **Fenster:** {payload['n_windows']} · **delta (GL-010-Survivor):** {payload['deltas_s']} s "
             f"· **horizon = delta** (DEC-16) · **Grid:** {payload['grid_ms']:g} ms")
    L.append(f"- **Friction-Wand:** {payload['friction_wall_bps']} bps · **Slippage:** {payload['slippage_bps']} bps "
             f"· **Gesamt-Wand:** {payload['wall_bps_total']} bps · **Latenz:** {payload['latency_ms']} ms "
             f"· **Maker-Sekundaer:** {'ja' if payload['maker_secondary'] else 'nein'}")
    L.append(f"- **Latenz-Haircut angewandt:** {'ja' if payload['latenz_haircut_applied'] else 'nein'} "
             f"— Einfang-Fenster `{payload['latenz_haircut_window']}`")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} · **BH-FDR alpha:** {payload['fdr_alpha']} "
             f"· **p_crit:** {payload['fdr_p_crit']:.4f}")
    L.append(f"- **capital_free:** nein — Tradability-Gate. Bleibt historischer Backtest mit Kostenmodell, "
             "KEIN Live-Order-Code, KEIN Geldeinsatz (CLAUDE.md §4). Kapital-Status PARK.")
    L.append(f"- **gate_valid_assumptions:** {'ja' if payload['gate_valid_assumptions'] else 'nein'} "
             f"— {payload['gate_valid_assumptions_note']}")
    L.append("")
    L.append("> Das GATE-URTEIL (WEITER/DROP/PARK) faellt der gate-auditor gegen H-05c — hartes "
             "Ein-Fenster-PARK-Kriterium (PRD §8.5), KEIN GRAUBEREICH. Der A-priori erwartet PARK "
             "(schwaches Mess-Signal aus GL-010 vs. 15-bps-Wand).")
    L.append("")
    L.append(f"**Tradable-konsistent (Netto>0 + p<=0.05 + FDR-sig in >=2 Fenstern):** "
             f"{'JA' if payload['any_tradable_consistent'] else 'nein'} · "
             f"**WEITER-Indikation (nur bei gueltigen Annahmen):** "
             f"{'ja' if payload['weiter_indication'] else 'nein'}")
    L.append("")
    L.append("## Tradability-Konsistenz je delta")
    L.append("")
    L.append("| delta (s) | Fenster gemessen | Fenster bestanden | bestandene Fenster | tradable-konsistent (>=2) |")
    L.append("|---:|---:|---:|---|---|")
    for c in payload["tradability_consistency"]:
        L.append(f"| {c['delta_s']} | {c['n_windows_measured']} | {c['n_windows_pass']} | "
                 f"{c['passing_windows']} | {'JA' if c['tradable_consistent'] else 'nein'} |")
    L.append("")
    L.append("## Detail je Fenster / delta")
    L.append("")
    L.append("| Fenster | delta (s) | Trips | Brutto-Einfang (bps) | Brutto-voll (bps) | Wand (bps) | Netto-Edge (bps) | bootstrap p | surrogate p | FDR-sig | bestanden |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for v in payload["variants"]:
        L.append(
            f"| {v['window_index']} | {v['delta_s']} | {v['n_trips']} | "
            f"{v['gross_capture_bps_mean']:+.3f} | {v['gross_full_bps_mean']:+.3f} | "
            f"{v['wall_bps']:.1f} | {v['net_edge_bps_mean']:+.3f} | {v['bootstrap_p']:.4f} | "
            f"{v['surrogate_p']:.4f} | {'ja' if v['fdr_significant'] else 'nein'} | "
            f"{'ja' if v['variant_pass'] else 'nein'} |"
        )
    L.append("")
    L.append("*Erzeugt von `c01_ofi_tradability/driver.py` (H-05c/DEC-16, read-only Harvester-Backfill). "
             "capital_free=false (Tradability), KEIN Live-Order-Code. Endgueltiges Gate-Urteil: gate-auditor gegen H-05c.*")
    return "\n".join(L)
