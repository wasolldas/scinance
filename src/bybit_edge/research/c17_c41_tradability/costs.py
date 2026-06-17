"""Friction wall + latency cost model for the C-17/C-41 tradability-gate (H-04b).

VERBINDLICH (registry H-04b Z.125-128, DEC-13b/c). These constants are the
programme baseline (verdict.md §2 Kernrelation) and the registered defaults; the
CLI MAY override them for sensitivity/robustness reporting, but a WEITER verdict
is ONLY valid at the registered point (friction >= 11 bps Taker AND latency
>= 300 ms AND the latency haircut applied) — see :func:`gate_assumptions_valid`
and the anti-gaming clause (registry H-04b Z.132).

* **Friction wall: 11 bps round-trip Taker** — primary, binding pass threshold
  (verdict.md §2 wörtlich "Round-Trip-Friktion 11 bps (Taker)").
* **Slippage: 4 bps round-trip** — derived from verdict.md §2 ("~15 bps inkl.
  Slippage"): 15 bps all-in − 11 bps Taker fee = 4 bps slippage. Reported
  separately so the friction wall and slippage are never conflated.
* **Latency: 300 ms** — retail-realistic, non-colocated; mid of the conservative
  100-500 ms band. The haircut itself (cutting the capture window at
  ``t + latency``) lives in :mod:`trading_rule`; this module only carries the
  constant and the validity check.
* **Maker secondary case** — a separate, clearly marked mode with an
  adverse-selection caveat; NEVER the primary pass criterion (registry H-04b
  Z.127). A Maker-WEITER under a Taker-DROP is flagged "adverse-selection-
  vorbehaltlich, nicht handelbar bestätigt".

NON-KAPITALFREI but still a historical backtest with a cost model — NO live
orders, NO real capital (CLAUDE.md §4).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Primary binding friction wall: 11 bps round-trip Taker (verdict.md §2).
FRICTION_WALL_BPS: float = 11.0

#: Round-trip slippage (verdict.md §2: ~15 bps all-in − 11 bps Taker = 4 bps).
SLIPPAGE_BPS: float = 4.0

#: Registered conservative latency haircut (DEC-13c), retail/non-colocated.
LATENCY_MS: float = 300.0

#: Maker round-trip fee (Bybit Perp maker ~ 1 bps each side -> 2 bps RT). Used
#: ONLY in the marked secondary case; carries the adverse-selection caveat.
MAKER_WALL_BPS: float = 2.0

#: bps per 1.0 of natural-log return (1 bp = 1e-4). A log-move of x corresponds
#: to ~ x * 1e4 bps for the small moves at play here.
BPS_PER_LOGRET: float = 1.0e4


@dataclass(slots=True)
class CostModel:
    """Round-trip cost model. ``maker`` switches to the marked secondary case."""

    friction_bps: float = FRICTION_WALL_BPS
    slippage_bps: float = SLIPPAGE_BPS
    latency_ms: float = LATENCY_MS
    maker: bool = False

    @property
    def wall_bps(self) -> float:
        """Total round-trip cost wall in bps (friction + slippage)."""
        fric = MAKER_WALL_BPS if self.maker else self.friction_bps
        return float(fric + self.slippage_bps)

    @property
    def effective_friction_bps(self) -> float:
        """The friction component actually charged (Taker wall or Maker wall)."""
        return float(MAKER_WALL_BPS if self.maker else self.friction_bps)


def logret_to_bps(x: float) -> float:
    """Convert a (directional) log-return to bps."""
    return float(x * BPS_PER_LOGRET)


def net_edge_bps(captured_move_logret: float, cost: CostModel) -> float:
    """Net edge per round-trip in bps = captured-move bps − wall bps.

    ``captured_move_logret`` is the DIRECTIONAL (position-signed) ETH move over
    the latency-haircut window ``[t+latency, t+lag+horizon]`` (from
    :func:`trading_rule.generate_round_trips`). The gross capture is converted
    to bps and the round-trip cost wall (friction + slippage) is subtracted.
    """
    return logret_to_bps(captured_move_logret) - cost.wall_bps


def round_trip_net_edges_bps(captured_moves_logret: np.ndarray, cost: CostModel) -> np.ndarray:
    """Vectorised per-round-trip net edges in bps for an array of captured moves."""
    cm = np.asarray(captured_moves_logret, dtype=np.float64)
    return cm * BPS_PER_LOGRET - cost.wall_bps


def gate_assumptions_valid(
    *,
    latency_ms: float,
    friction_bps: float,
    haircut_applied: bool,
    maker: bool,
) -> bool:
    """Anti-gaming check (registry H-04b Z.132, DEC-13 anti-gaming clause).

    A WEITER verdict is ONLY gate-valid when ALL hold:

    * ``latency_ms >= 300`` (the registered haircut was not shortened),
    * ``friction_bps >= 11`` (the Taker wall was not lowered),
    * ``haircut_applied`` is True (the move was measured over ``[t+latency, ...]``
      not ``[t, ...]``),
    * ``maker`` is False (the Maker case is never a primary pass).

    Any other assumption is a NEW hypothesis (H-04c), not a goalpost shift on
    this gate. When this returns False the driver MUST set
    ``gate_valid_assumptions: false`` in the output and the default pass verdict
    is always read at the 300 ms / 11 bps point.
    """
    return (
        (latency_ms >= LATENCY_MS)
        and (friction_bps >= FRICTION_WALL_BPS)
        and bool(haircut_applied)
        and (not maker)
    )
