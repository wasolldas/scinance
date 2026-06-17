"""C-17/C-41 Lead-Lag-TRADABILITY research package (Welle-2-Folge-WP, H-04b).

NON-KAPITALFREI (``capital_free=false``) — the FIRST non-kapitalfreie hypothesis
of the programme. Where the H-04 mess-gate (``c17_c41_lead_lag``) only measured
the *existence* of directed BTC->ETH information (capital_free=true), this module
asks the harder, registered follow-up: is that gerichtete Information tradable
AFTER a realistic latency haircut AND the binding 11 bps round-trip Taker
friction wall? (registry H-04b, DEC-13).

It remains a *historical backtest with a cost model* on the read-only ``trades``
stock — NO live-order code, NO real capital (CLAUDE.md §4 / Autonomie-Protokoll
§3). ``capital_free=false`` marks only that the gate confronts edge-bps /
friction / latency.

Pieces:

* :mod:`trading_rule` — pre-fixed lead-lag rule (BTC signal -> ETH position,
  unwound after horizon=lag) + the causal latency haircut (capture window cut at
  ``t + latency`` -> ``[t+latency, t+lag+horizon]``).
* :mod:`costs` — 11 bps Taker friction wall (primary) + 4 bps slippage + 300 ms
  latency constant, the marked adverse-selection Maker secondary case, and the
  anti-gaming validity check.
* :mod:`net_edge` — net edge per round-trip + bootstrap (mean > 0) /
  sign-permutation significance + BH-FDR alpha=0.10 over F-LEADLAG-TRADE.
* :mod:`driver` — read-only orchestration over >= 2 disjoint windows, reusing
  the bestand ``c17_c41_lead_lag`` loaders + half-open window splitter as an
  IMPORT (not duplicated, not modified). CLI: ``scripts/c17_c41_tradability.py``.

Gate (registry H-04b / DEC-13): net edge per round-trip > 0 AND statistically
> 0 (bootstrap p <= 0.05 after BH-FDR) on >= 2 disjoint windows, ONLY valid at
latency >= 300 ms AND friction >= 11 bps AND haircut applied. Hard one-window
PARK (§8.5), no GRAUBEREICH. The PRD-§4 a-priori expects PARK. The GATE VERDICT
is the gate-auditor's; this package reports each criterion individually.
"""
from __future__ import annotations

from .costs import (
    BPS_PER_LOGRET,
    FRICTION_WALL_BPS,
    LATENCY_MS,
    MAKER_WALL_BPS,
    SLIPPAGE_BPS,
    CostModel,
    gate_assumptions_valid,
    logret_to_bps,
    net_edge_bps,
    round_trip_net_edges_bps,
)
from .driver import (
    DEFAULT_GRID_MS,
    HYPOTHESIS_ID,
    MIN_WINDOWS,
    WINDOW_MAX_TICKS,
    DataError,
    WindowResult,
    load_pair_duckdb,
    load_trades_file,
    render_markdown,
    run,
    run_window,
    write_outputs,
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
from .trading_rule import (
    SURVIVOR_LAGS,
    RoundTrip,
    btc_signal_return,
    captured_eth_move,
    generate_round_trips,
)

__all__ = [
    "BPS_PER_LOGRET",
    "DEFAULT_BOOTSTRAP",
    "DEFAULT_GRID_MS",
    "FDR_ALPHA",
    "FRICTION_WALL_BPS",
    "HYPOTHESIS_ID",
    "LATENCY_MS",
    "MAKER_WALL_BPS",
    "MIN_WINDOWS",
    "NET_EDGE_P_MAX",
    "SLIPPAGE_BPS",
    "SURVIVOR_LAGS",
    "WINDOW_MAX_TICKS",
    "CostModel",
    "DataError",
    "NetEdgeResult",
    "RoundTrip",
    "WindowResult",
    "benjamini_hochberg",
    "bootstrap_mean_le_zero_p",
    "btc_signal_return",
    "captured_eth_move",
    "gate_assumptions_valid",
    "generate_round_trips",
    "load_pair_duckdb",
    "load_trades_file",
    "logret_to_bps",
    "net_edge_bps",
    "render_markdown",
    "round_trip_net_edges_bps",
    "run",
    "run_window",
    "sign_permutation_p",
    "write_outputs",
]
