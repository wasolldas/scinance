# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Decision Aggregator -- combines strategy signals with risk filters.

Architecture (PRD Section 5):
    1. Kyle-Lambda Veto: toxic flow -> wait (no limit orders).
    2. SIR R0 Veto: R0 > 1 and not cascade_detector -> wait.
    3. Position-Sizing: Kelly-Fraction x Kyle-Lambda-Discount.
    4. Final output: action, direction, position_size, stop, confidence.
"""

from __future__ import annotations

from typing import Any

import numpy as np


# Maximum Kelly fraction cap (25% of portfolio)
_MAX_KELLY: float = 0.25

# Minimum edge for any position
_MIN_EDGE: float = 0.005


class DecisionAggregator:
    """Aggregates strategy signals with risk-layer vetoes and sizing.

    Receives a list of strategy signals and L5 risk outputs (Kyle Lambda,
    SIR R0) to produce a final trading decision with position sizing.
    """

    def aggregate(
        self,
        strategy_signals: list[dict[str, Any]],
        kyle_lambda: dict[str, Any],
        sir: dict[str, Any],
    ) -> dict[str, Any]:
        """Produce a final aggregated trading decision.

        Parameters
        ----------
        strategy_signals : list[dict]
            Each dict from a strategy's on_ticker / on_data output.
            Required keys: action, direction, strategy, confidence.
        kyle_lambda : dict
            Output from M25.compute(). Must have: toxic_flow, kyle_lambda,
            lambda_q95.
        sir : dict
            Output from M26.compute(). Must have: r0, cascade_risk.

        Returns
        -------
        dict with action, direction, position_size_pct, stop_level,
        strategy_id, confidence.
        """
        wait_result: dict[str, Any] = {
            "action": "wait",
            "direction": 0,
            "position_size_pct": 0.0,
            "stop_level": 0.0,
            "strategy_id": "",
            "confidence": 0.0,
        }

        # ----------------------------------------------------------
        # 1. Find best active signal (highest confidence entry)
        # ----------------------------------------------------------
        active_signals: list[dict[str, Any]] = [
            s for s in strategy_signals
            if s.get("action") == "enter" and s.get("direction", 0) != 0
        ]

        if not active_signals:
            # Check for exit signals
            exit_signals = [
                s for s in strategy_signals
                if s.get("action") == "exit"
            ]
            if exit_signals:
                best_exit = max(exit_signals, key=lambda s: s.get("confidence", 0.0))
                return {
                    "action": "exit",
                    "direction": best_exit.get("direction", 0),
                    "position_size_pct": 0.0,
                    "stop_level": 0.0,
                    "strategy_id": best_exit.get("strategy", ""),
                    "confidence": best_exit.get("confidence", 0.0),
                }
            return wait_result

        best_signal: dict[str, Any] = max(
            active_signals,
            key=lambda s: s.get("confidence", 0.0),
        )
        strategy_id: str = best_signal.get("strategy", "")

        # ----------------------------------------------------------
        # 2. Kyle-Lambda Veto: toxic flow -> wait
        # ----------------------------------------------------------
        toxic_flow: bool = kyle_lambda.get("toxic_flow", False)
        if toxic_flow:
            return {
                **wait_result,
                "strategy_id": strategy_id,
                "action": "wait",
                "confidence": best_signal.get("confidence", 0.0),
            }

        # ----------------------------------------------------------
        # 3. SIR R0 Veto: R0 > 1 and not cascade_detector -> wait
        # ----------------------------------------------------------
        r0: float = sir.get("r0", 0.0)
        if r0 > 1.0 and strategy_id != "S1":
            return {
                **wait_result,
                "strategy_id": strategy_id,
                "action": "wait",
                "confidence": best_signal.get("confidence", 0.0),
            }

        # ----------------------------------------------------------
        # 4. Position Sizing: Kelly x Kyle-Lambda-Discount
        # ----------------------------------------------------------
        confidence: float = best_signal.get("confidence", 0.5)
        direction: int = best_signal.get("direction", 0)

        # Kelly fraction (simplified)
        win_rate: float = max(0.5 + confidence * 0.1, 0.5)
        edge: float = win_rate - (1.0 - win_rate)
        kelly_fraction: float = max(0.0, min(edge, _MAX_KELLY))

        # Kyle-Lambda discount
        kyle_q95: float = kyle_lambda.get("lambda_q95", 0.0)
        kyle_val: float = kyle_lambda.get("kyle_lambda", 0.0)
        if kyle_q95 > 0:
            lambda_ratio: float = min(kyle_val / kyle_q95, 1.0)
        else:
            lambda_ratio = 0.5
        kyle_discount: float = 1.0 - lambda_ratio * 0.5

        position_size_pct: float = kelly_fraction * kyle_discount

        # Minimum edge check
        if edge < _MIN_EDGE:
            position_size_pct = 0.0

        return {
            "action": "long" if direction > 0 else "short",
            "direction": direction,
            "position_size_pct": round(position_size_pct, 4),
            "stop_level": 0.0,
            "strategy_id": strategy_id,
            "confidence": round(confidence, 4),
        }
