"""Read-only driver for the C-17/C-41 tradability-gate (Welle-2-Folge-WP, H-04b).

Loads publicTrade ticks for the BTC/ETH symbol PAIR from the existing DuckDB
``trades`` table, splits into >= 2 disjoint chronological windows, and per window
per survivor-lag (1/2/3 s) runs the pre-fixed lead-lag trading rule, applies the
latency haircut + the 11 bps friction wall + slippage, and bootstraps whether the
NET edge per round-trip is statistically > 0 (BH-FDR alpha = 0.10 over
F-LEADLAG-TRADE). It reuses the *bestand* ``c17_c41_lead_lag`` library
(loaders, ``--db-copy`` temp-copy, 30 s open timeout, epoch-ms filter, progress
logging, the half-open deterministic window splitter ``split_pair_windows`` —
WP-1 bugfix) as an IMPORT; that kapitalfreie H-04 module is NOT duplicated and
NOT modified.

NON-KAPITALFREI (registry H-04b, ``capital_free=false``): this driver DOES report
the bps / edge / friction columns that H-04 deliberately omitted. It remains a
*historical backtest with a cost model* on the read-only stock — NO live-order
code, NO real capital (CLAUDE.md §4 / Autonomie-Protokoll §3). ``capital_free``
marks only that the gate confronts edge-bps / friction / latency.

The GATE VERDICT (WEITER / DROP / PARK) is the gate-auditor's call against H-04b
(hard one-window PARK criterion, no GRAUBEREICH); this driver reports every gate
criterion INDIVIDUALLY per window per lag and renders NO overall verdict. The
anti-gaming flag ``gate_valid_assumptions`` is set false whenever the run
deviates from the registered 300 ms / 11 bps / haircut-applied point.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# Reuse the bestand kapitalfreie H-04 library (loaders + half-open splitter +
# grid constants). NOT duplicated, NOT modified — H-04 stays untouched.
from bybit_edge.research.c17_c41_lead_lag.driver import (
    DEFAULT_GRID_MS,
    WINDOW_MAX_TICKS,
    DataError,
    load_pair_duckdb,
    load_trades_file,
    split_pair_windows,
)

from .costs import (
    BPS_PER_LOGRET,
    FRICTION_WALL_BPS,
    LATENCY_MS,
    SLIPPAGE_BPS,
    CostModel,
    gate_assumptions_valid,
    round_trip_net_edges_bps,
)
from .net_edge import (
    DEFAULT_BOOTSTRAP,
    FDR_ALPHA,
    NET_EDGE_P_MAX,
    NetEdgeResult,
    benjamini_hochberg,
    bootstrap_mean_le_zero_p,
    sign_permutation_p,
)
from .trading_rule import SURVIVOR_LAGS, generate_round_trips

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-04b"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
MIN_WINDOWS = 2  # registered (>= 2 disjoint windows)

# Re-export so the CLI imports them from one place.
__all__ = [
    "DEFAULT_GRID_MS",
    "WINDOW_MAX_TICKS",
    "DataError",
    "WindowResult",
    "load_pair_duckdb",
    "load_trades_file",
    "render_markdown",
    "run",
    "run_window",
    "write_outputs",
]


@dataclass(slots=True)
class WindowResult:
    index: int
    n_trips_total: int
    t0_ms: float
    t1_ms: float
    variants: list[dict[str, Any]] = field(default_factory=list)
    criteria: dict[str, Any] = field(default_factory=dict)


def run_window(
    index: int,
    pair_btc: tuple[np.ndarray, np.ndarray],
    pair_eth: tuple[np.ndarray, np.ndarray],
    *,
    symbol_a: str,
    symbol_b: str,
    lags: tuple[int, ...],
    grid_ms: float,
    cost: CostModel,
    n_bootstrap: int,
    seed: int,
    n_windows: int,
    signal_eps: float = 0.0,
) -> WindowResult:
    """Run the trading rule + net-edge bootstrap for every lag over one window.

    ``horizon = lag`` (DEC-13 default). BH-FDR is applied across the lags of
    THIS window (the F-LEADLAG-TRADE family is the union over windows x lags —
    see :func:`run`, which also exposes a per-window family for the per-window
    PARK criterion; the global family is reported too).
    """
    ts_btc, px_btc = pair_btc
    ts_eth, px_eth = pair_eth
    print(
        f"[c17b] window {index + 1}/{n_windows}: btc_ticks={ts_btc.size} "
        f"eth_ticks={ts_eth.size} lags={list(lags)} latency={cost.latency_ms:g}ms "
        f"wall={cost.wall_bps:g}bps (maker={cost.maker}) bootstrap={n_bootstrap}",
        file=sys.stderr, flush=True,
    )

    per_variant: list[dict[str, Any]] = []
    for li, lag in enumerate(lags):
        horizon = lag  # DEC-13: horizon = lag (most conservative default)
        trips = generate_round_trips(
            ts_btc, px_btc, ts_eth, px_eth,
            lag=lag, horizon=horizon, grid_ms=grid_ms,
            latency_ms=cost.latency_ms, signal_eps=signal_eps,
        )
        n_trips = len(trips)
        if n_trips == 0:
            res = NetEdgeResult(
                lag=lag, horizon=horizon, n_trips=0,
                gross_capture_bps_mean=0.0, gross_full_bps_mean=0.0,
                wall_bps=cost.wall_bps, net_edge_bps_mean=0.0,
                bootstrap_p=1.0, surrogate_p=1.0, n_bootstrap=0,
            )
            print(
                f"[c17b] window {index + 1}/{n_windows} lag={lag}: 0 round-trips "
                f"-> net_edge=0 p=1.0",
                file=sys.stderr, flush=True,
            )
        else:
            captured = np.array([t.eth_move_captured for t in trips], dtype=np.float64)
            full = np.array([t.eth_move_full for t in trips], dtype=np.float64)
            signs = np.array([t.position_sign for t in trips], dtype=np.float64)
            raw_captured = captured * signs  # undo position sign -> raw ETH move
            net = round_trip_net_edges_bps(captured, cost)
            boot_p = bootstrap_mean_le_zero_p(
                net, n_bootstrap=n_bootstrap, seed=seed + 100 * li + index,
            )
            surr_p = sign_permutation_p(
                raw_captured, signs, cost.wall_bps,
                bps_per_logret=BPS_PER_LOGRET,
                n_surrogates=n_bootstrap, seed=seed + 100 * li + index + 7,
            )
            res = NetEdgeResult(
                lag=lag, horizon=horizon, n_trips=n_trips,
                gross_capture_bps_mean=float(np.mean(captured) * BPS_PER_LOGRET),
                gross_full_bps_mean=float(np.mean(full) * BPS_PER_LOGRET),
                wall_bps=cost.wall_bps,
                net_edge_bps_mean=float(np.mean(net)),
                bootstrap_p=boot_p, surrogate_p=surr_p, n_bootstrap=n_bootstrap,
            )
            print(
                f"[c17b] window {index + 1}/{n_windows} lag={lag} (horizon={horizon}): "
                f"{n_trips} trips brutto={res.gross_capture_bps_mean:.2f}bps "
                f"wall={cost.wall_bps:.1f}bps netto={res.net_edge_bps_mean:.2f}bps "
                f"boot_p={boot_p:.4f} surr_p={surr_p:.4f}",
                file=sys.stderr, flush=True,
            )

        entry = {
            "label": f"NET_{symbol_a}->{symbol_b}_lag{lag}_h{horizon}",
            "source": symbol_a,
            "target": symbol_b,
            "lag_ms": lag * grid_ms,
            "horizon_ms": horizon * grid_ms,
            "latency_ms": cost.latency_ms,
            "latenz_haircut_applied": True,
            "friction_bps": cost.effective_friction_bps,
            "slippage_bps": cost.slippage_bps,
            "maker_secondary": bool(cost.maker),
            **res.as_dict(),
        }
        per_variant.append(entry)

    # BH-FDR over this window's lag family (per-window F-LEADLAG-TRADE slice).
    p_values = [e["bootstrap_p"] for e in per_variant]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for entry, rej in zip(per_variant, rejected):
        entry["fdr_significant"] = bool(rej)
        entry["net_edge_positive"] = bool(entry["net_edge_bps_mean"] > 0.0)
        # A variant "passes" (per registry WEITER) iff net edge > 0 AND
        # bootstrap p <= 0.05 AND FDR-significant.
        entry["passed"] = bool(
            entry["net_edge_positive"]
            and (entry["bootstrap_p"] <= NET_EDGE_P_MAX)
            and entry["fdr_significant"]
        )

    wr = WindowResult(
        index=index,
        n_trips_total=sum(int(e["n_trips"]) for e in per_variant),
        t0_ms=float(ts_btc[0]) if ts_btc.size else 0.0,
        t1_ms=float(ts_btc[-1]) if ts_btc.size else 0.0,
    )
    wr.variants = per_variant
    any_pass = any(e["passed"] for e in per_variant)
    best = min(per_variant, key=lambda e: (e["bootstrap_p"], -e["net_edge_bps_mean"]))
    wr.criteria = {
        "net_edge": {
            "best_variant": best["label"],
            "best_net_edge_bps": best["net_edge_bps_mean"],
            "best_bootstrap_p": best["bootstrap_p"],
            "threshold_p": NET_EDGE_P_MAX,
            "registry_text": (
                "Netto-Edge/Round-Trip (Brutto-Move ueber [t+latenz, t+lag+horizon] "
                "- Friction-Wand 11 bps - Slippage) > 0 UND statistisch > 0 "
                "(Bootstrap p <= 0.05 nach BH-FDR alpha=0.10 ueber F-LEADLAG-TRADE)"
            ),
            "window_has_passing_variant": any_pass,
        },
        "fdr_p_crit": p_crit,
        "n_fdr_significant": sum(1 for e in per_variant if e["fdr_significant"]),
    }
    return wr


def run(
    pair_btc: tuple[np.ndarray, np.ndarray],
    pair_eth: tuple[np.ndarray, np.ndarray],
    *,
    symbol_a: str,
    symbol_b: str,
    n_windows: int,
    lags: tuple[int, ...] = SURVIVOR_LAGS,
    grid_ms: float = DEFAULT_GRID_MS,
    latency_ms: float = LATENCY_MS,
    friction_bps: float = FRICTION_WALL_BPS,
    slippage_bps: float = SLIPPAGE_BPS,
    maker_secondary: bool = False,
    n_bootstrap: int = DEFAULT_BOOTSTRAP,
    seed: int = 42,
    max_ticks_per_window: int = WINDOW_MAX_TICKS,
    signal_eps: float = 0.0,
    source: str = "",
) -> dict[str, Any]:
    """Run the full H-04b tradability backtest over >= 2 windows.

    Reuses ``split_pair_windows`` from the bestand H-04 library (half-open
    deterministic-chronological splitter, WP-1 bugfix) so the window scoping is
    identical to H-04 and not re-implemented here.
    """
    cost = CostModel(
        friction_bps=friction_bps, slippage_bps=slippage_bps,
        latency_ms=latency_ms, maker=maker_secondary,
    )
    # Anti-gaming validity (registry H-04b Z.132): a WEITER is gate-valid only
    # at latency >= 300, friction >= 11, haircut applied, Taker (not Maker).
    haircut_applied = True  # the trading rule ALWAYS cuts at t+latency
    gate_valid = gate_assumptions_valid(
        latency_ms=latency_ms, friction_bps=friction_bps,
        haircut_applied=haircut_applied, maker=maker_secondary,
    )

    ts_btc, px_btc = pair_btc
    ts_eth, px_eth = pair_eth
    windows = split_pair_windows(
        ts_btc, px_btc, ts_eth, px_eth, n_windows,
        max_ticks_per_window=max_ticks_per_window,
    )
    print(
        f"[c17b] pair {symbol_a}/{symbol_b}: {ts_btc.size}/{ts_eth.size} ticks, "
        f"{len(windows)} window(s) (cap {max_ticks_per_window}/window, "
        f"lags={list(lags)}, grid={grid_ms:g}ms, latency={latency_ms:g}ms, "
        f"wall={cost.wall_bps:g}bps, maker={maker_secondary}, "
        f"gate_valid_assumptions={gate_valid})",
        file=sys.stderr, flush=True,
    )

    win_results = [
        run_window(
            i, wb, we,
            symbol_a=symbol_a, symbol_b=symbol_b,
            lags=lags, grid_ms=grid_ms, cost=cost,
            n_bootstrap=n_bootstrap, seed=seed, n_windows=len(windows),
            signal_eps=signal_eps,
        )
        for i, (wb, we) in enumerate(windows)
    ]

    # Global F-LEADLAG-TRADE family BH-FDR over ALL (window x lag) variants.
    flat: list[tuple[int, int]] = []  # (window_index, variant_index)
    global_p: list[float] = []
    for wr in win_results:
        for vi, ev in enumerate(wr.variants):
            flat.append((wr.index, vi))
            global_p.append(ev["bootstrap_p"])
    global_rejected, global_p_crit = benjamini_hochberg(global_p, FDR_ALPHA)
    for (wi, vi), rej in zip(flat, global_rejected):
        wr = win_results[wi]
        ev = wr.variants[vi]
        ev["fdr_significant_global"] = bool(rej)
        ev["passed_global"] = bool(
            ev["net_edge_positive"]
            and (ev["bootstrap_p"] <= NET_EDGE_P_MAX)
            and rej
        )

    # Per-window pass (registry: a window passes iff it has a variant with net
    # edge > 0 AND bootstrap p <= 0.05 AND globally FDR-significant).
    per_window_pass = [
        any(ev["passed_global"] for ev in wr.variants) for wr in win_results
    ]
    # WEITER needs ALL >= 2 windows to pass (hard one-window PARK §8.5) AND the
    # gate assumptions to be valid. This is the criterion reading; the actual
    # verdict is the gate-auditor's.
    all_windows_pass = (
        len(win_results) >= MIN_WINDOWS and all(per_window_pass)
    )
    weiter_indication = bool(all_windows_pass and gate_valid)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        # NON-kapitalfrei: this gate confronts edge-bps / friction / latency.
        # It is STILL a historical backtest with a cost model — NO live orders,
        # NO real capital (CLAUDE.md §4).
        "capital_free": False,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbol_a": symbol_a,
        "symbol_b": symbol_b,
        "n_windows": len(win_results),
        "n_bootstrap": n_bootstrap,
        "seed": seed,
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": "F-LEADLAG-TRADE",
        "grid_ms": grid_ms,
        "lags": list(lags),
        "horizon_rule": "horizon = lag (DEC-13 default)",
        "signal_eps": signal_eps,
        # Cost model + latency haircut (registry H-04b Z.125-128).
        "friction_wall_bps": friction_bps,
        "slippage_bps": slippage_bps,
        "latency_ms": latency_ms,
        "wall_bps_total": cost.wall_bps,
        "maker_secondary": bool(maker_secondary),
        "latenz_haircut_applied": haircut_applied,
        "latenz_haircut_window": "[t+latenz, t+lag+horizon] (ETH capture, causal, no lookahead)",
        # Registered defaults (the pass point) + anti-gaming flag.
        "registered_friction_wall_bps": FRICTION_WALL_BPS,
        "registered_latency_ms": LATENCY_MS,
        "gate_valid_assumptions": gate_valid,
        "gate_valid_assumptions_note": (
            "WEITER nur gueltig bei latency >= 300 ms UND friction >= 11 bps UND "
            "Latenz-Haircut angewandt UND Taker (nicht Maker). Abweichung -> "
            "gate_valid_assumptions=false, ein WEITER waere ungueltig (Anti-Gaming, "
            "Registry H-04b Z.132; eine andere Annahme ist eine NEUE Hypothese H-04c)."
        ),
        "maker_secondary_caveat": (
            "Maker-Sekundaerfall ist adverse-selection-anfaellig (Fill bevorzugt "
            "wenn man falsch liegt); NIE Primaer-Pass. Ein Maker-WEITER bei "
            "Taker-DROP ist 'adverse-selection-vorbehaltlich, nicht handelbar "
            "bestaetigt' (registry H-04b Z.127)."
        ),
        "max_ticks_per_window": int(max_ticks_per_window),
        "n_ticks_total": {"btc": int(ts_btc.size), "eth": int(ts_eth.size)},
        "gate_thresholds": {
            "net_edge_bps_gt": 0.0,
            "bootstrap_p_max": NET_EDGE_P_MAX,
            "min_windows": MIN_WINDOWS,
            "friction_wall_bps": FRICTION_WALL_BPS,
            "latency_ms": LATENCY_MS,
        },
        "per_window_pass": per_window_pass,
        "all_windows_pass": all_windows_pass,
        "weiter_indication": weiter_indication,
        "fdr_p_crit_global": global_p_crit,
        "windows": [
            {
                "index": wr.index,
                "n_trips_total": wr.n_trips_total,
                "t0_ms": wr.t0_ms,
                "t1_ms": wr.t1_ms,
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
    """German Markdown report — one criterion per row, per window per lag (H-04b)."""
    L: list[str] = []
    L.append("# C-17/C-41 Lead-Lag-TRADABILITY-Gate (H-04b · Friction-Wand + Latenz-Haircut, capital_free=FALSE)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Paar `{payload['symbol_a']}`/`{payload['symbol_b']}`)")
    L.append(
        f"- **Fenster:** {payload['n_windows']} · **Bootstrap-N:** {payload['n_bootstrap']} · "
        f"**Seed:** {payload['seed']} · **BH-FDR alpha:** {payload['fdr_alpha']} "
        f"(Familie `{payload['fdr_family']}`)"
    )
    L.append(
        f"- **Grid:** {payload['grid_ms']:g} ms · **Lags (Survivor 1-3 s):** {payload['lags']} · "
        f"**{payload['horizon_rule']}**"
    )
    L.append(
        f"- **Friction-Wand:** {payload['friction_wall_bps']:g} bps · "
        f"**Slippage:** {payload['slippage_bps']:g} bps · "
        f"**Gesamt-Wand:** {payload['wall_bps_total']:g} bps · "
        f"**Latenz:** {payload['latency_ms']:g} ms · "
        f"**Maker-Sekundaer:** {_fmt(payload['maker_secondary'])}"
    )
    L.append(
        f"- **Latenz-Haircut angewandt:** {_fmt(payload['latenz_haircut_applied'])} — "
        f"Einfang-Fenster `{payload['latenz_haircut_window']}`"
    )
    L.append(
        f"- **capital_free:** {_fmt(payload['capital_free'])} — Tradability-Gate (Edge-bps/"
        "Friction/Latenz). Bleibt historischer Backtest mit Kostenmodell, KEIN Live-Order-Code, "
        "KEIN Geldeinsatz (CLAUDE.md §4)."
    )
    L.append(
        f"- **gate_valid_assumptions:** {_fmt(payload['gate_valid_assumptions'])} "
        f"(registriert: Wand {payload['registered_friction_wall_bps']:g} bps / "
        f"Latenz {payload['registered_latency_ms']:g} ms). {payload['gate_valid_assumptions_note']}"
    )
    L.append("")
    L.append(f"> {payload['maker_secondary_caveat']}")
    L.append("")
    L.append(
        "> Der Report liefert jedes Gate-Kriterium einzeln je Fenster/Lag. Das "
        "GATE-URTEIL (WEITER/DROP/PARK) faellt der gate-auditor gegen H-04b — "
        "hartes Ein-Fenster-PARK-Kriterium (PRD §8.5), KEIN GRAUBEREICH. Der "
        "PRD-§4-A-priori erwartet PARK (abgegraste HFT-Anomalie)."
    )
    L.append("")
    L.append(
        f"**Alle Fenster mit Netto-Edge-Survivor (FDR-global):** {_fmt(payload['all_windows_pass'])} "
        f"· **WEITER-Indikation (nur bei gueltigen Annahmen):** {_fmt(payload['weiter_indication'])}"
    )
    L.append(f"**Pass je Fenster:** {payload['per_window_pass']}")
    L.append(f"**BH-FDR p_crit (global):** {_fmt(payload['fdr_p_crit_global'])}")
    L.append("")
    for w in payload["windows"]:
        L.append(f"## Fenster {w['index']} — {w['n_trips_total']} Round-Trips gesamt")
        L.append(f"- Zeitspanne: {w['t0_ms']:.0f} .. {w['t1_ms']:.0f} ms")
        c = w["criteria"]["net_edge"]
        L.append(
            f"- Beste Variante: `{c['best_variant']}` (Netto {_fmt(c['best_net_edge_bps'], 2)} bps, "
            f"bootstrap p {_fmt(c['best_bootstrap_p'])})"
        )
        L.append(f"- Fenster hat Netto-Edge-Survivor (per-Fenster-FDR): {_fmt(c['window_has_passing_variant'])}")
        L.append("")
        L.append(
            "| Variante | Lag (ms) | Horizon (ms) | Trips | Brutto-Einfang (bps) | "
            "Brutto-voll (bps) | Wand (bps) | Netto-Edge (bps) | bootstrap p | surrogate p | "
            "FDR-sig (global) | bestanden |"
        )
        L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
        for v in w["variants"]:
            L.append(
                f"| `{v['label']}` | {_fmt(v['lag_ms'], 0)} | {_fmt(v['horizon_ms'], 0)} "
                f"| {v['n_trips']} | {_fmt(v['gross_capture_bps_mean'], 2)} "
                f"| {_fmt(v['gross_full_bps_mean'], 2)} | {_fmt(v['wall_bps'], 1)} "
                f"| {_fmt(v['net_edge_bps_mean'], 2)} | {_fmt(v['bootstrap_p'])} "
                f"| {_fmt(v['surrogate_p'])} | {_fmt(v.get('fdr_significant_global', False))} "
                f"| {_fmt(v.get('passed_global', False))} |"
            )
        L.append("")
        L.append(
            f"- BH-FDR p_crit (Fenster): {_fmt(w['criteria']['fdr_p_crit'])} · "
            f"FDR-signifikante Varianten (Fenster): {w['criteria']['n_fdr_significant']}"
        )
        L.append("")
    L.append("---")
    L.append(
        "*Erzeugt von `scripts/c17_c41_tradability.py` (Welle-2-Folge-WP, read-only Driver, "
        f"H-04b/DEC-13). capital_free=false (Tradability), KEIN Live-Order-Code. "
        f"Endgueltiges Gate-Urteil: gate-auditor gegen {HYPOTHESIS_ID}.*"
    )
    L.append("")
    return "\n".join(L)


def write_outputs(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    """Write ``c17_c41_tradability_results.json`` + ``.md`` to ``out_dir``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "c17_c41_tradability_results.json"
    md_path = out_dir / "c17_c41_tradability_results.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path
