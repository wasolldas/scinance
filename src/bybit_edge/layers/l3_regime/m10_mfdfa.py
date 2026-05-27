"""
M10 — MF-DFA Multifractal Detrended Fluctuation Analysis [L3]

Eigene Implementierung (~120 LOC, kein MFDFA-Package).

Formeln (PRD):
    F_q(s) = { (1/2N_s) * Sum [F^2(v,s)]^{q/2} }^{1/q}  ~  s^{h(q)}
    tau(q) = q*h(q) - 1
    Delta_h = h(q_min) - h(q_max)
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import (
    MFDFA_Q_RANGE,
    MFDFA_SCALE_RANGE,
    MFDFA_WINDOW_N,
    MFDFA_ZSCORE_THRESHOLD,
)
from bybit_edge.layers.base import BaseModule


class M10MFDFA(BaseModule):
    """Multifractal Detrended Fluctuation Analysis for regime-change detection.

    Computes the generalised Hurst exponent h(q) across a range of moment
    orders q.  A large spread Delta_h = h(q_min) - h(q_max) indicates
    multifractality; a z-score spike signals regime change.
    """

    def __init__(
        self,
        q_list: list[float] | None = None,
        scales: list[int] | None = None,
        window_n: int = MFDFA_WINDOW_N,
        zscore_threshold: float = MFDFA_ZSCORE_THRESHOLD,
        history_len: int = 200,
    ) -> None:
        self.q_list: list[float] = q_list or [-5.0, -3.0, -1.0, 0.0, 1.0, 3.0, 5.0]
        self.scales: list[int] = scales or [16, 32, 64, 128, 256]
        self.window_n: int = window_n
        self.zscore_threshold: float = zscore_threshold
        self._delta_h_history: deque[float] = deque(maxlen=history_len)

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def _profile(self, series: np.ndarray) -> np.ndarray:
        """Cumulative sum of the mean-centred series (random-walk profile).

        Parameters
        ----------
        series : np.ndarray
            1-D input series.

        Returns
        -------
        np.ndarray
            Profile Y_i = Sum_{k=1}^{i} (x_k - x_mean).
        """
        centred = series - series.mean()
        return np.cumsum(centred)

    def _fluctuation(self, profile: np.ndarray, scale: int) -> np.ndarray:
        """Per-segment variance F^2(v,s) for a given scale *s*.

        Parameters
        ----------
        profile : np.ndarray
            Integrated (cumulative-sum) profile.
        scale : int
            Segment length *s*.

        Returns
        -------
        np.ndarray
            Array of F^2 values, one per non-overlapping segment.
        """
        n = len(profile)
        n_seg = n // scale
        if n_seg == 0:
            return np.array([0.0])

        f2 = np.empty(n_seg, dtype=np.float64)
        x_idx = np.arange(scale, dtype=np.float64)
        for v in range(n_seg):
            seg = profile[v * scale : (v + 1) * scale]
            # Linear detrend (polyfit degree 1)
            coeffs = np.polyfit(x_idx, seg, 1)
            fit = np.polyval(coeffs, x_idx)
            f2[v] = np.mean((seg - fit) ** 2)
        return f2

    def _mfdfa(
        self,
        series: np.ndarray,
        q_list: list[float],
        scales: list[int],
    ) -> dict[float, float]:
        """Compute generalised Hurst exponents h(q) via MF-DFA.

        Parameters
        ----------
        series : np.ndarray
            1-D returns series (length >= max(scales) * 4).
        q_list : list[float]
            Moment orders.
        scales : list[int]
            Segment scales.

        Returns
        -------
        dict[float, float]
            Mapping q -> h(q).
        """
        profile = self._profile(series)

        # Pre-compute fluctuation per scale
        f2_by_scale: dict[int, np.ndarray] = {}
        for s in scales:
            f2_by_scale[s] = self._fluctuation(profile, s)

        log_scales = np.log(np.array(scales, dtype=np.float64))
        h_q: dict[float, float] = {}

        for q in q_list:
            log_fq = np.empty(len(scales), dtype=np.float64)
            for i, s in enumerate(scales):
                f2 = f2_by_scale[s]
                # Remove zeros to avoid log(0)
                f2_pos = f2[f2 > 0]
                if len(f2_pos) == 0:
                    log_fq[i] = 0.0
                    continue

                if q == 0.0:
                    # Geometric mean: exp(mean(log(F)))
                    log_fq[i] = 0.5 * np.mean(np.log(f2_pos))
                else:
                    # F_q(s) = { (1/N_s) * Sum [F^2]^{q/2} }^{1/q}
                    fq = np.mean(f2_pos ** (q / 2.0)) ** (1.0 / q)
                    log_fq[i] = np.log(max(fq, 1e-300))

            # OLS: log(F_q) vs log(s) -> slope = h(q)
            if len(log_scales) >= 2:
                coeffs = np.polyfit(log_scales, log_fq, 1)
                h_q[q] = float(coeffs[0])
            else:
                h_q[q] = 0.5

        return h_q

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute(self, returns: np.ndarray) -> dict[str, Any]:
        """Compute MF-DFA multifractal width and regime-change signal.

        Parameters
        ----------
        returns : np.ndarray
            1-min returns array.  Ideally >= 2048 points; shorter series
            are handled gracefully with reduced confidence.

        Returns
        -------
        dict
            Keys: delta_h, delta_h_zscore, h_values, regime_change,
            signal, method_id, confidence, ts.
        """
        ts = time.time()

        # Graceful handling of insufficient data
        min_required = max(self.scales) * 4
        if len(returns) < min_required:
            return {
                "delta_h": 0.0,
                "delta_h_zscore": 0.0,
                "h_values": {q: 0.5 for q in self.q_list},
                "regime_change": False,
                "signal": 0,
                "method_id": "M10",
                "confidence": 0.0,
                "ts": ts,
            }

        h_values = self._mfdfa(returns, self.q_list, self.scales)

        q_min = min(self.q_list)
        q_max = max(self.q_list)
        delta_h = h_values[q_min] - h_values[q_max]

        # z-score against rolling history
        self._delta_h_history.append(delta_h)
        if len(self._delta_h_history) >= 3:
            arr = np.array(self._delta_h_history)
            mu = arr.mean()
            std = arr.std()
            delta_h_zscore = (delta_h - mu) / std if std > 1e-12 else 0.0
        else:
            delta_h_zscore = 0.0

        regime_change = bool(abs(delta_h_zscore) > self.zscore_threshold)
        signal = 1 if regime_change else 0
        confidence = min(abs(delta_h_zscore) / (self.zscore_threshold * 2.0), 1.0)

        return {
            "delta_h": float(delta_h),
            "delta_h_zscore": float(delta_h_zscore),
            "h_values": {float(q): float(h) for q, h in h_values.items()},
            "regime_change": regime_change,
            "signal": signal,
            "method_id": "M10",
            "confidence": float(confidence),
            "ts": ts,
        }

    def reset(self) -> None:
        """Clear rolling history."""
        self._delta_h_history.clear()
