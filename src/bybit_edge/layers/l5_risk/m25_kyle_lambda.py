"""
M25 — Kyle's Lambda (Adverse Selection) [L5]

Formeln (PRD):
    Δp_t = λ · v_t · sign_t + ε_t
    OLS über N letzte Trades
    Filter: if λ_5min > Q95(λ_30d) → Toxic Flow → KEINE Limit-Orders

Kyle's Lambda misst die Preis-Impact-Funktion: wie stark bewegt ein
Trade den Preis? Hohe λ-Werte deuten auf informed/toxic Flow hin —
in diesem Regime sind Limit-Orders riskant (Adverse Selection).
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import (
    KYLE_LOOKBACK_DAYS,
    KYLE_QUANTILE_THRESHOLD,
    KYLE_ROLLING_TRADES,
)
from bybit_edge.layers.base import BaseModule

# Minimale Trade-Anzahl für sinnvolle Regression
_MIN_TRADES: int = 10

# Lambda-History: 30d bei ~1 Schätzung/min = 43200
_LAMBDA_HISTORY_MAXLEN: int = KYLE_LOOKBACK_DAYS * 24 * 60


class M25KyleLambda(BaseModule):
    """Kyle's Lambda Adverse-Selection Modul.

    Schätzt den Preis-Impact-Koeffizienten λ via geschlossene OLS-Lösung
    und detektiert Toxic-Flow-Regime wenn λ den 95%-Quantil der
    30-Tage-Historie überschreitet.
    """

    def __init__(self) -> None:
        self._lambda_history: deque[float] = deque(maxlen=_LAMBDA_HISTORY_MAXLEN)
        self._trades: deque[dict[str, Any]] = deque(maxlen=KYLE_ROLLING_TRADES)

    # ------------------------------------------------------------------
    # OLS λ-Schätzung
    # ------------------------------------------------------------------

    def _estimate_lambda(
        self,
        delta_prices: np.ndarray,
        signed_volumes: np.ndarray,
    ) -> float:
        """Schätze Kyle's λ via geschlossene OLS-Lösung.

        Modell: Δp = λ · signed_volume + ε
        Lösung: λ = Σ(Δp · sv) / Σ(sv²)

        Parameters
        ----------
        delta_prices : Array der Preisänderungen
        signed_volumes : Array der vorzeichenbehafteten Volumen

        Returns
        -------
        float — geschätztes λ (≥ 0 theoretisch, aber OLS kann negativ liefern)
        """
        sv_sq_sum = float(np.dot(signed_volumes, signed_volumes))
        if sv_sq_sum < 1e-30:
            return 0.0
        return float(np.dot(delta_prices, signed_volumes)) / sv_sq_sum

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(self, trades: list[dict[str, Any]]) -> dict[str, Any]:
        """Berechne Kyle's Lambda und Toxic-Flow-Flag.

        Parameters
        ----------
        trades : Liste von Trade-Dicts
            Jeder Trade: {"price": float, "volume": float, "side": str,
                          "timestamp_ms": int}
            side: "Buy" oder "Sell"

        Returns
        -------
        dict mit signal, kyle_lambda, lambda_q95, toxic_flow,
        method_id, confidence, ts.
        """
        ts_now = time.time()

        # Trades in internen Buffer einfügen
        for trade in trades:
            self._trades.append(trade)

        trade_list = list(self._trades)

        # Zu wenig Trades → neutrales Signal
        if len(trade_list) < _MIN_TRADES:
            return {
                "signal": 0,
                "kyle_lambda": 0.0,
                "lambda_q95": 0.0,
                "toxic_flow": False,
                "method_id": "M25",
                "confidence": 0.0,
                "ts": ts_now,
            }

        # Delta-Prices berechnen
        prices = np.array(
            [float(t["price"]) for t in trade_list], dtype=np.float64,
        )
        delta_prices = np.diff(prices)

        # Signed Volumes: volume * sign(side)
        volumes = np.array(
            [float(t["volume"]) for t in trade_list], dtype=np.float64,
        )
        signs = np.array(
            [1.0 if t.get("side", "Buy") == "Buy" else -1.0 for t in trade_list],
            dtype=np.float64,
        )
        signed_volumes = volumes[1:] * signs[1:]  # Align mit delta_prices

        # λ schätzen
        kyle_lambda = self._estimate_lambda(delta_prices, signed_volumes)

        # In Historie einfügen
        self._lambda_history.append(kyle_lambda)

        # Q95-Quantil aus History
        if len(self._lambda_history) >= 2:
            lambda_q95 = float(
                np.quantile(list(self._lambda_history), KYLE_QUANTILE_THRESHOLD)
            )
        else:
            lambda_q95 = kyle_lambda

        # Toxic Flow Flag
        toxic_flow = kyle_lambda > lambda_q95 and len(self._lambda_history) > 1

        # Signal: -1 bei Toxic Flow (Risk-Off), 0 sonst
        signal = -1 if toxic_flow else 0

        # Confidence: basierend auf Datenqualität und Stärke des Signals
        data_quality = min(len(trade_list) / float(KYLE_ROLLING_TRADES), 1.0)
        history_quality = min(len(self._lambda_history) / 100.0, 1.0)
        if toxic_flow and lambda_q95 > 0:
            excess_ratio = min((kyle_lambda / lambda_q95 - 1.0) * 2.0, 1.0)
            confidence = min(data_quality * 0.3 + history_quality * 0.3 + excess_ratio * 0.4, 1.0)
        else:
            confidence = 0.0

        return {
            "signal": signal,
            "kyle_lambda": kyle_lambda,
            "lambda_q95": lambda_q95,
            "toxic_flow": toxic_flow,
            "method_id": "M25",
            "confidence": confidence,
            "ts": ts_now,
        }

    def validate(self) -> bool:
        """Prüft ob Konfiguration plausibel ist."""
        return KYLE_ROLLING_TRADES > 0 and KYLE_LOOKBACK_DAYS > 0

    def reset(self) -> None:
        """Setzt internen State zurück."""
        self._lambda_history.clear()
        self._trades.clear()
