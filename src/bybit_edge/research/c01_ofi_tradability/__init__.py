"""C-01 OFI-fade tradability-gate (H-05c, capital_free=FALSE).

The tradability counterpart to the capital-free H-05b inverse OFI mess-gate
(``c01_ofi_sign``), exactly mirroring the H-04 -> H-04b separation. It asks
whether the GL-010-confirmed inverse OFI signal on SOLUSDT (delta 1s/5s) carries
a tradable net edge after the binding 11 bps friction wall and a 300 ms latency
haircut. Historical backtest with a cost model — NO live orders (CLAUDE.md §4);
capital status stays PARK.

Reuses ``c01_ofi_sign.oos.load_harvest_window`` (read-only harvester loader) and
``c01_ofi_sign.ofi.signed_volume`` (aggressor convention). New here: the fade
trading rule, the friction/latency cost model, and the net-edge/bootstrap/BH-FDR
logic over the F-OFI-INV-TRADE family — all of which the capital-free H-05b
module deliberately omits.
"""
from __future__ import annotations

from .costs import (
    FRICTION_WALL_BPS,
    LATENCY_MS,
    SLIPPAGE_BPS,
    CostModel,
    gate_assumptions_valid,
    net_edge_bps,
)
from .driver import HYPOTHESIS_ID, PASS_SYMBOL, render_markdown, run
from .fade_rule import SURVIVOR_DELTAS_S, generate_round_trips
from .net_edge import benjamini_hochberg, bootstrap_mean_le_zero_p

__all__ = [
    "FRICTION_WALL_BPS",
    "LATENCY_MS",
    "SLIPPAGE_BPS",
    "CostModel",
    "gate_assumptions_valid",
    "net_edge_bps",
    "HYPOTHESIS_ID",
    "PASS_SYMBOL",
    "render_markdown",
    "run",
    "SURVIVOR_DELTAS_S",
    "generate_round_trips",
    "benjamini_hochberg",
    "bootstrap_mean_le_zero_p",
]
