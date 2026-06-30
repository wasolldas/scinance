"""Friction wall + latency cost model for the C-01 OFI-fade tradability-gate (H-05c).

VERBINDLICH (registry H-05c, DEC-16). Identical programme baseline to H-04b
(verdict.md §2 Kernrelation): 11 bps round-trip Taker wall, 4 bps slippage,
300 ms latency haircut, Maker only as a marked adverse-selection secondary case.
A WEITER verdict is ONLY valid at the registered point (friction >= 11 bps Taker
AND latency >= 300 ms AND the haircut applied AND a pass-cell in {SOL-δ1s,
SOL-δ5s}) — see :func:`gate_assumptions_valid` and the anti-gaming clause
(registry H-05c, DEC-16).

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

#: Registered conservative latency haircut (DEC-16), retail/non-colocated.
LATENCY_MS: float = 300.0

#: Maker round-trip fee — ONLY the marked secondary case (adverse-selection caveat).
MAKER_WALL_BPS: float = 2.0

#: bps per 1.0 of natural-log return (1 bp = 1e-4).
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
        fric = MAKER_WALL_BPS if self.maker else self.friction_bps
        return float(fric + self.slippage_bps)

    @property
    def effective_friction_bps(self) -> float:
        return float(MAKER_WALL_BPS if self.maker else self.friction_bps)


def logret_to_bps(x: float) -> float:
    return float(x * BPS_PER_LOGRET)


def net_edge_bps(captured_move_logret: float, cost: CostModel) -> float:
    """Net edge per round-trip in bps = captured-move bps − wall bps.

    ``captured_move_logret`` is the DIRECTIONAL (position-signed, i.e. fade-signed)
    SOL move over the latency-haircut window ``[t+latency, t+delta]``.
    """
    return logret_to_bps(captured_move_logret) - cost.wall_bps


def round_trip_net_edges_bps(captured_moves_logret: np.ndarray, cost: CostModel) -> np.ndarray:
    cm = np.asarray(captured_moves_logret, dtype=np.float64)
    return cm * BPS_PER_LOGRET - cost.wall_bps


def gate_assumptions_valid(
    *,
    latency_ms: float,
    friction_bps: float,
    haircut_applied: bool,
    maker: bool,
) -> bool:
    """Anti-gaming check (registry H-05c, DEC-16 anti-gaming clause).

    A WEITER verdict is ONLY gate-valid when ALL hold: ``latency_ms >= 300``,
    ``friction_bps >= 11``, ``haircut_applied`` True, ``maker`` False. The
    pass-cell restriction ({SOL-δ1s, SOL-δ5s}) is enforced in the driver, not
    here. Any other assumption is a NEW hypothesis (H-05d), not a goalpost shift.
    """
    return (
        (latency_ms >= LATENCY_MS)
        and (friction_bps >= FRICTION_WALL_BPS)
        and bool(haircut_applied)
        and (not maker)
    )
