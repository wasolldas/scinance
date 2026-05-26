"""
M5 — Fraktionale Differenzierung FFD [L2]

Formeln (PRD):
    (1 - B)^d X_t = sum_{k=0}^inf (-1)^k * C(d,k) * X_{t-k}
    C(d,k) = d*(d-1)*...*(d-k+1) / k!
    FFD: Weights gekuerzt bei |w_k| < tau (tau ~ 1e-4)

Transformiert Preis-/Imbalance-Serien fraktional differenziert,
um Stationaritaet zu erreichen bei maximaler Gedaechtniserhaltung.
Waehlt das kleinste d mit ADF-Stationaritaet.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from bybit_edge.config import FFD_ADF_P_THRESHOLD, FFD_D_GRID, FFD_WEIGHT_THRESHOLD
from bybit_edge.layers.base import BaseModule

# Versuche statsmodels fuer ADF-Test
try:
    from statsmodels.tsa.stattools import adfuller

    _HAS_STATSMODELS: bool = True
except ImportError:
    _HAS_STATSMODELS = False

# Default d-Grid fuer Suche (erweitert gegenueber config fuer _find_optimal_d)
_DEFAULT_D_GRID: list[float] = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


class M5FFD(BaseModule):
    """Fraktionale Differenzierung (Fixed-Width Window, FFD).

    Berechnet FFD-Weights iterativ und wendet sie via Convolution an.
    Kann optional das optimale d per ADF-Test finden.
    """

    def __init__(
        self,
        default_d: float = 0.5,
        weight_threshold: float = FFD_WEIGHT_THRESHOLD,
        adf_p_threshold: float = FFD_ADF_P_THRESHOLD,
    ) -> None:
        self._default_d = default_d
        self._weight_threshold = weight_threshold
        self._adf_p_threshold = adf_p_threshold
        self._last_d: float = default_d
        self._last_adf_pvalue: float | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_weights(self, d: float, threshold: float = 1e-4) -> np.ndarray:
        """Berechne FFD-Weights iterativ.

        w_0 = 1
        w_k = w_{k-1} * (d - k + 1) / k   fuer k >= 1
        Stoppe wenn |w_k| < threshold.

        Parameters
        ----------
        d : float
            Fraktionaler Differenzierungsgrad.
        threshold : float
            Abbruchschwelle fuer Weights.

        Returns
        -------
        np.ndarray
            Array der FFD-Weights (w_0, w_1, ..., w_K).
        """
        weights: list[float] = [1.0]
        k = 1
        w = 1.0
        while True:
            w = w * (d - k + 1) / k
            if abs(w) < threshold:
                break
            weights.append(w)
            k += 1
            # Sicherheits-Obergrenze
            if k > 100_000:
                break
        return np.array(weights, dtype=np.float64)

    def _ffd_transform(self, series: np.ndarray, d: float) -> np.ndarray:
        """Wende FFD-Weights via Dot-Product an.

        Parameters
        ----------
        series : np.ndarray
            1D-Input-Zeitreihe.
        d : float
            Fraktionaler Differenzierungsgrad.

        Returns
        -------
        np.ndarray
            FFD-transformierte Serie (gleiche Laenge, fuehrende NaNs
            wo nicht genug History).
        """
        weights = self._compute_weights(d, self._weight_threshold)
        n_weights = len(weights)
        n = len(series)

        result = np.full(n, np.nan, dtype=np.float64)

        for t in range(n_weights - 1, n):
            window = series[t - n_weights + 1: t + 1][::-1]
            result[t] = float(np.dot(weights, window))

        return result

    def _find_optimal_d(
        self,
        series: np.ndarray,
        d_grid: list[float] | None = None,
    ) -> float:
        """Finde kleinstes d mit ADF-Stationaritaet.

        Parameters
        ----------
        series : np.ndarray
            1D-Input-Zeitreihe.
        d_grid : list[float] | None
            Grid von d-Werten zum Testen. Default: [0.1, ..., 1.0].

        Returns
        -------
        float
            Optimales d. Fallback auf default_d wenn statsmodels nicht
            vorhanden oder kein d gefunden.
        """
        if not _HAS_STATSMODELS:
            return self._default_d

        if d_grid is None:
            d_grid = _DEFAULT_D_GRID

        for d in sorted(d_grid):
            transformed = self._ffd_transform(series, d)
            # Entferne NaNs
            valid = transformed[~np.isnan(transformed)]
            if len(valid) < 20:
                continue
            try:
                adf_result = adfuller(valid, maxlag=min(20, len(valid) // 4 - 1))
                p_value = float(adf_result[1])
                if p_value < self._adf_p_threshold:
                    self._last_adf_pvalue = p_value
                    return d
            except Exception:
                continue

        # Kein d gefunden — fallback
        return 1.0

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(self, series: np.ndarray, d: float | None = None) -> dict[str, Any]:
        """Wende FFD-Transformation an.

        Parameters
        ----------
        series : np.ndarray
            1D-Input-Zeitreihe (z.B. Preise).
        d : float | None
            Fraktionaler Grad. Wenn None, wird optimal per ADF-Test bestimmt.

        Returns
        -------
        dict mit transformed, d, adf_pvalue, n_weights, method_id,
        signal, confidence, ts.
        """
        now = time.time()
        series = np.asarray(series, dtype=np.float64)

        if d is None:
            d = self._find_optimal_d(series)

        self._last_d = d

        transformed = self._ffd_transform(series, d)
        weights = self._compute_weights(d, self._weight_threshold)
        n_weights = len(weights)

        # ADF p-value auf das Ergebnis (wenn moeglich)
        adf_pvalue: float | None = self._last_adf_pvalue
        if adf_pvalue is None and _HAS_STATSMODELS:
            valid = transformed[~np.isnan(transformed)]
            if len(valid) >= 20:
                try:
                    adf_result = adfuller(valid, maxlag=min(20, len(valid) // 4 - 1))
                    adf_pvalue = float(adf_result[1])
                except Exception:
                    adf_pvalue = None
            self._last_adf_pvalue = adf_pvalue

        # Confidence: ADF basiert (kleiner p -> hoehere Confidence)
        confidence: float = 0.0
        if adf_pvalue is not None and adf_pvalue < self._adf_p_threshold:
            confidence = min(1.0 - adf_pvalue, 1.0)

        return {
            "transformed": transformed,
            "d": d,
            "adf_pvalue": adf_pvalue,
            "n_weights": n_weights,
            "method_id": "M5",
            "signal": 0,  # Preprocessing-Modul, kein Trading-Signal
            "confidence": confidence,
            "ts": now,
        }

    def validate(self) -> bool:
        """Prueft ob FFD-Parameter sinnvoll konfiguriert sind."""
        return (
            self._weight_threshold > 0.0
            and 0.0 < self._adf_p_threshold < 1.0
        )

    def reset(self) -> None:
        """Setzt internen State zurueck."""
        self._last_d = self._default_d
        self._last_adf_pvalue = None
