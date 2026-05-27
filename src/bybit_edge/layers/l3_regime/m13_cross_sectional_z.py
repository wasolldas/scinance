"""
M13 -- Cross-Sectional Ergodicity-Reversion Z-Score [L3] [Standard]

Formeln (PRD):
    E_t[X_i] = (1/W) * sum_{s=t-W}^{t} R_{i,s}    (zeitlicher Mittelwert von Symbol i)
    <X>_t    = (1/N) * sum_{j=1}^{N} R_{j,t}        (Ensemble-Mittelwert)
    sigma_cross = std({E_t[X_j]} fuer j=1..N)
    z_{i,t}  = (E_t[X_i] - <X>_t) / sigma_cross

Signal: |z| > 2.5 => Mean-Reversion-Entry gegen Z

Cross-Sectional Z misst, wie weit ein einzelnes Symbol zeitlich
vom Ensemble-Durchschnitt abweicht. Extreme Z-Scores deuten auf
ergodizitaetsbasierte Mean-Reversion-Gelegenheiten hin.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import (
    CSZ_WINDOW_HOURS,
    CSZ_Z_THRESHOLD,
)
from bybit_edge.layers.base import BaseModule

# 1h = 60 bars bei 1-min-Intervall
_DEFAULT_WINDOW: int = CSZ_WINDOW_HOURS * 60

# Minimum an Datenpunkten bevor Z-Scores sinnvoll sind
_MIN_HISTORY: int = 10

# Schutz gegen Division durch Null
_SIGMA_EPSILON: float = 1e-12


class M13CrossSectionalZ(BaseModule):
    """Cross-Sectional Ergodicity-Reversion Z-Score Detektor.

    Berechnet fuer jedes Symbol den Z-Score der zeitlichen Mittelwerte
    gegenueber dem Ensemble-Mittelwert. Extreme Abweichungen (|z| > 2.5)
    signalisieren Mean-Reversion-Gelegenheiten.
    """

    def __init__(self, window: int = _DEFAULT_WINDOW) -> None:
        self._window: int = window
        self._returns_history: dict[str, deque[float]] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_symbol(self, symbol: str) -> None:
        """Legt History-Deque fuer ein Symbol an, falls noch nicht vorhanden."""
        if symbol not in self._returns_history:
            self._returns_history[symbol] = deque(maxlen=self._window)

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(
        self,
        returns: dict[str, float],
        current_ts: float | None = None,
    ) -> dict[str, Any]:
        """Berechne Cross-Sectional Z-Scores fuer alle Symbole.

        Parameters
        ----------
        returns : dict[str, float]
            Aktuelle Returns aller Symbole, z.B.
            {"BTCUSDT": 0.001, "ETHUSDT": -0.002, ...}.
        current_ts : float | None
            Zeitstempel. Falls None, wird time.time() verwendet.

        Returns
        -------
        dict mit z_scores, extreme_symbols, signal, method_id,
        confidence, ts.
        """
        now = current_ts if current_ts is not None else time.time()

        # Returns in History aufnehmen
        for symbol, ret in returns.items():
            self._ensure_symbol(symbol)
            self._returns_history[symbol].append(ret)

        # Pruefe ob genuegend Daten vorhanden
        symbols_with_data = [
            s for s in returns
            if len(self._returns_history[s]) >= _MIN_HISTORY
        ]

        if len(symbols_with_data) < 2:
            return {
                "z_scores": {},
                "extreme_symbols": [],
                "signal": 0,
                "method_id": "M13",
                "confidence": 0.0,
                "ts": now,
            }

        # E_t[X_i] = rolling mean pro Symbol (zeitlicher Mittelwert)
        temporal_means: dict[str, float] = {}
        for symbol in symbols_with_data:
            hist = self._returns_history[symbol]
            temporal_means[symbol] = float(np.mean(list(hist)))

        # <X>_t = cross-sectional mean ueber alle zeitlichen Mittelwerte
        mean_values = np.array(list(temporal_means.values()))
        ensemble_mean: float = float(np.mean(mean_values))

        # sigma_cross = cross-sectional std
        sigma_cross: float = float(np.std(mean_values, ddof=0))

        # Division-by-Zero-Schutz
        if sigma_cross < _SIGMA_EPSILON:
            z_scores = {s: 0.0 for s in symbols_with_data}
            return {
                "z_scores": z_scores,
                "extreme_symbols": [],
                "signal": 0,
                "method_id": "M13",
                "confidence": 0.0,
                "ts": now,
            }

        # Z-Scores berechnen
        z_scores: dict[str, float] = {}
        for symbol in symbols_with_data:
            z_scores[symbol] = (temporal_means[symbol] - ensemble_mean) / sigma_cross

        # Extreme Symbole finden: |z| > threshold
        extreme_symbols: list[dict[str, Any]] = []
        for symbol, z in z_scores.items():
            if abs(z) > CSZ_Z_THRESHOLD:
                # Mean-Reversion: Signal gegen Z-Richtung
                # positives z -> Symbol hat outperformed -> short (revert)
                # negatives z -> Symbol hat underperformed -> long (revert)
                direction = -1 if z > 0 else 1
                extreme_symbols.append({
                    "symbol": symbol,
                    "z": z,
                    "direction": direction,
                })

        # Sortiere nach absoluter Z-Groesse (extremste zuerst)
        extreme_symbols.sort(key=lambda x: abs(x["z"]), reverse=True)

        signal: int = 1 if len(extreme_symbols) > 0 else 0

        # Confidence: basiert auf dem extremsten Z-Score
        confidence: float = 0.0
        if extreme_symbols:
            max_abs_z = abs(extreme_symbols[0]["z"])
            # Skalierung: z=2.5 -> conf ~0.5, z=5.0 -> conf ~1.0
            confidence = min(max_abs_z / 5.0, 1.0)

        return {
            "z_scores": z_scores,
            "extreme_symbols": extreme_symbols,
            "signal": signal,
            "method_id": "M13",
            "confidence": confidence,
            "ts": now,
        }

    def validate(self) -> bool:
        """Prueft ob Konfiguration sinnvoll ist."""
        return self._window >= 1 and CSZ_Z_THRESHOLD > 0.0

    def reset(self) -> None:
        """Setzt internen State vollstaendig zurueck."""
        self._returns_history.clear()
