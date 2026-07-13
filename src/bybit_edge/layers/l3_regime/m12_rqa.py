"""
M12 — RQA Recurrence Quantification Analysis [L3]

Eigene Implementierung (~100 LOC, kein pyrqa).

Formeln (PRD):
    R_{ij} = Theta(epsilon - ||x_i - x_j||)
    DET = Sum_{l>=l_min} l*P(l) / Sum_l l*P(l)     (Determinismus)
    LAM = Sum_{v>=v_min} v*P(v) / Sum_v v*P(v)     (Laminaritaet)
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from bybit_edge.config import (
    RQA_DET_THRESHOLD,
    RQA_EMBEDDING_DIM,
    RQA_WINDOW_BARS,
)
from bybit_edge.layers.base import BaseModule

# Below this standard deviation, an input series is treated as (near-)
# constant/frozen (e.g. stuck WS feed, illiquid symbol, repeated last price
# during a reconnect). Auto-epsilon would otherwise collapse toward the
# numerical floor, making the recurrence matrix fully recurrent and
# producing a spurious maximum-confidence "breakout imminent" signal for a
# market that is not moving at all. See CRITICAL_REVIEW_2 M12 finding.
_CONSTANT_SERIES_STD_FLOOR: float = 1e-9


class M12RQA(BaseModule):
    """Recurrence Quantification Analysis for breakout detection.

    Uses Takens time-delay embedding, builds a binary recurrence matrix,
    and computes DET (determinism) and LAM (laminarity).  High DET *and*
    high LAM indicate consolidation preceding a breakout.
    """

    def __init__(
        self,
        embedding_dim: int = RQA_EMBEDDING_DIM,
        delay: int = 1,
        det_threshold: float = RQA_DET_THRESHOLD,
        lam_threshold: float = RQA_DET_THRESHOLD,
        l_min: int = 2,
        v_min: int = 2,
    ) -> None:
        self.embedding_dim: int = embedding_dim
        self.delay: int = delay
        self.det_threshold: float = det_threshold
        self.lam_threshold: float = lam_threshold
        self.l_min: int = l_min
        self.v_min: int = v_min

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def _embed(self, series: np.ndarray, dim: int, delay: int) -> np.ndarray:
        """Takens time-delay embedding.

        Parameters
        ----------
        series : np.ndarray
            1-D time series.
        dim : int
            Embedding dimension *m*.
        delay : int
            Time delay *tau*.

        Returns
        -------
        np.ndarray
            Shape (N - (dim-1)*delay, dim).
        """
        n = len(series)
        rows = n - (dim - 1) * delay
        if rows <= 0:
            return np.empty((0, dim), dtype=np.float64)
        indices = np.arange(rows)[:, None] + np.arange(dim)[None, :] * delay
        return series[indices]

    def _recurrence_matrix(
        self, embedded: np.ndarray, epsilon: float
    ) -> np.ndarray:
        """Binary recurrence matrix R_ij = 1 if ||x_i - x_j|| < epsilon.

        Parameters
        ----------
        embedded : np.ndarray
            Embedded state-space trajectory, shape (N, dim).
        epsilon : float
            Distance threshold.

        Returns
        -------
        np.ndarray
            Boolean recurrence matrix of shape (N, N), dtype int8.
        """
        # Pairwise squared distances
        diff = embedded[:, None, :] - embedded[None, :, :]
        dist = np.sqrt(np.sum(diff ** 2, axis=2))
        return (dist < epsilon).astype(np.int8)

    def _diagonal_lines(self, R: np.ndarray, l_min: int = 2) -> list[int]:
        """Lengths of diagonal lines in the recurrence matrix (excl. LOI).

        Parameters
        ----------
        R : np.ndarray
            Recurrence matrix of shape (N, N).
        l_min : int
            Minimum line length to include.

        Returns
        -------
        list[int]
            Lengths of all diagonal lines >= l_min.
        """
        n = R.shape[0]
        lengths: list[int] = []

        # Scan all diagonals (upper triangle, k > 0)
        for k in range(1, n):
            line_len = 0
            for i in range(n - k):
                if R[i, i + k]:
                    line_len += 1
                else:
                    if line_len >= l_min:
                        lengths.append(line_len)
                    line_len = 0
            if line_len >= l_min:
                lengths.append(line_len)

        return lengths

    def _vertical_lines(self, R: np.ndarray, v_min: int = 2) -> list[int]:
        """Lengths of vertical lines in the recurrence matrix.

        Parameters
        ----------
        R : np.ndarray
            Recurrence matrix of shape (N, N).
        v_min : int
            Minimum line length to include.

        Returns
        -------
        list[int]
            Lengths of all vertical lines >= v_min.
        """
        n = R.shape[0]
        lengths: list[int] = []

        for j in range(n):
            line_len = 0
            for i in range(n):
                if R[i, j]:
                    line_len += 1
                else:
                    if line_len >= v_min:
                        lengths.append(line_len)
                    line_len = 0
            if line_len >= v_min:
                lengths.append(line_len)

        return lengths

    def _det(self, R: np.ndarray, l_min: int = 2) -> float:
        """Determinism: fraction of recurrent points on diagonal lines.

        DET = Sum_{l>=l_min} l*P(l) / Sum_l l*P(l)

        Parameters
        ----------
        R : np.ndarray
            Recurrence matrix.
        l_min : int
            Minimum diagonal line length.

        Returns
        -------
        float
            Determinism in [0, 1].
        """
        total_recurrent = int(np.sum(np.triu(R, k=1)))
        if total_recurrent == 0:
            return 0.0

        diag_lengths = self._diagonal_lines(R, l_min)
        if not diag_lengths:
            return 0.0

        diag_points = sum(diag_lengths)
        return diag_points / total_recurrent

    def _lam(self, R: np.ndarray, v_min: int = 2) -> float:
        """Laminarity: fraction of recurrent points on vertical lines.

        LAM = Sum_{v>=v_min} v*P(v) / Sum_v v*P(v)

        Parameters
        ----------
        R : np.ndarray
            Recurrence matrix.
        v_min : int
            Minimum vertical line length.

        Returns
        -------
        float
            Laminarity in [0, 1].
        """
        total_recurrent = int(np.sum(R))
        if total_recurrent == 0:
            return 0.0

        vert_lengths = self._vertical_lines(R, v_min)
        if not vert_lengths:
            return 0.0

        vert_points = sum(vert_lengths)
        return vert_points / total_recurrent

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute(
        self, series: np.ndarray, epsilon: float | None = None
    ) -> dict[str, Any]:
        """Compute RQA metrics and breakout signal.

        Parameters
        ----------
        series : np.ndarray
            1-D time series (e.g. 500 5-min returns).
        epsilon : float, optional
            Recurrence threshold.  Default: 10% of std(series).

        Returns
        -------
        dict
            Keys: det, lam, recurrence_rate, breakout_signal, signal,
            method_id, confidence, ts.
        """
        ts = time.time()

        # Minimum data check
        min_len = (self.embedding_dim - 1) * self.delay + 2
        if len(series) < min_len:
            return {
                "det": 0.0,
                "lam": 0.0,
                "recurrence_rate": 0.0,
                "breakout_signal": False,
                "signal": 0,
                "method_id": "M12",
                "confidence": 0.0,
                "degenerate": False,
                "ts": ts,
            }

        # Guard: a (near-)constant/frozen series must never produce a
        # high-confidence signal. Report an explicit low-confidence,
        # degenerate result instead of letting epsilon collapse to its
        # numerical floor.
        std = float(np.std(series))
        if std <= _CONSTANT_SERIES_STD_FLOOR:
            return {
                "det": 0.0,
                "lam": 0.0,
                "recurrence_rate": 0.0,
                "breakout_signal": False,
                "signal": 0,
                "method_id": "M12",
                "confidence": 0.0,
                "degenerate": True,
                "ts": ts,
            }

        # Auto-epsilon: 10% of standard deviation
        if epsilon is None:
            epsilon = 0.1 * std

        embedded = self._embed(series, self.embedding_dim, self.delay)
        R = self._recurrence_matrix(embedded, epsilon)

        det = self._det(R, self.l_min)
        lam = self._lam(R, self.v_min)

        # Recurrence rate (fraction of 1s in upper triangle)
        n = R.shape[0]
        n_pairs = n * (n - 1) // 2
        recurrence_rate = float(np.sum(np.triu(R, k=1))) / n_pairs if n_pairs > 0 else 0.0

        breakout_signal = bool(det > self.det_threshold and lam > self.lam_threshold)
        signal = 1 if breakout_signal else 0
        confidence = float(min((det + lam) / 2.0, 1.0))

        return {
            "det": float(det),
            "lam": float(lam),
            "recurrence_rate": float(recurrence_rate),
            "breakout_signal": breakout_signal,
            "signal": signal,
            "method_id": "M12",
            "confidence": confidence,
            "degenerate": False,
            "ts": ts,
        }

    def reset(self) -> None:
        """No rolling state to clear — included for interface conformance."""
        pass
