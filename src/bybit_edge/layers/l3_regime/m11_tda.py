"""
M11 — TDA / Persistent Homology [L3]

Eigene Implementierung (~100 LOC, kein ripser/gudhi).

Formeln (PRD):
    Persistence Landscape: lambda_k(t) = max_k-max{ min(t - b_i, d_i - t), 0 }
    L1-Norm: L1(lambda) = Sum_k integral |lambda_k(t)| dt

Simplified H0 persistence via single-linkage clustering with Union-Find.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np

from bybit_edge.config import (
    TDA_L1_ZSCORE_THRESHOLD,
    TDA_WINDOW_BARS,
)
from bybit_edge.layers.base import BaseModule


class _UnionFind:
    """Weighted Union-Find (disjoint-set) with path compression."""

    def __init__(self, n: int) -> None:
        self.parent: list[int] = list(range(n))
        self.rank: list[int] = [0] * n
        self.n_components: int = n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        # Path compression
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        """Merge sets containing *a* and *b*.  Returns True if a merge occurred."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        self.n_components -= 1
        return True


class M11TDA(BaseModule):
    """Topological Data Analysis via simplified H0 persistent homology.

    Uses pairwise distance matrix + single-linkage Union-Find to compute
    H0 persistence diagram.  The L1 norm of persistence lifetimes serves
    as a crash-precursor indicator: a z-score spike triggers risk-off.
    """

    def __init__(
        self,
        zscore_threshold: float = TDA_L1_ZSCORE_THRESHOLD,
        window_bars: int = TDA_WINDOW_BARS,
        history_len: int = 200,
    ) -> None:
        self.zscore_threshold: float = zscore_threshold
        self.window_bars: int = window_bars
        self._l1_history: deque[float] = deque(maxlen=history_len)

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def _distance_matrix(self, points: np.ndarray) -> np.ndarray:
        """Pairwise Euclidean distance matrix.

        Parameters
        ----------
        points : np.ndarray
            Shape (M, N) — M points in N-dimensional space.

        Returns
        -------
        np.ndarray
            Shape (M, M) symmetric distance matrix.
        """
        # ||a - b||^2 = ||a||^2 + ||b||^2 - 2 a.b
        sq_norms = np.sum(points ** 2, axis=1)
        dot = points @ points.T
        dist_sq = sq_norms[:, None] + sq_norms[None, :] - 2.0 * dot
        # Clamp numerical noise
        np.maximum(dist_sq, 0.0, out=dist_sq)
        # Zero out diagonal explicitly to avoid floating-point noise
        np.fill_diagonal(dist_sq, 0.0)
        return np.sqrt(dist_sq)

    def _persistence_h0(
        self, dist_matrix: np.ndarray
    ) -> list[tuple[float, float]]:
        """Compute H0 (connected components) persistence via single-linkage.

        Every point is born at distance 0.  Two components merge at the
        distance of the shortest edge connecting them (single-linkage).
        The younger component dies at that distance.

        Parameters
        ----------
        dist_matrix : np.ndarray
            Symmetric distance matrix of shape (M, M).

        Returns
        -------
        list[tuple[float, float]]
            Persistence pairs (birth, death).  The final component that
            never dies is excluded (infinite persistence).
        """
        m = dist_matrix.shape[0]
        if m <= 1:
            return []

        # Build sorted edge list (upper triangle only)
        rows, cols = np.triu_indices(m, k=1)
        weights = dist_matrix[rows, cols]
        order = np.argsort(weights)

        uf = _UnionFind(m)
        pairs: list[tuple[float, float]] = []

        for idx in order:
            i, j = int(rows[idx]), int(cols[idx])
            w = float(weights[idx])
            if uf.union(i, j):
                # A merge happened — the younger component dies
                pairs.append((0.0, w))
            if uf.n_components == 1:
                break

        return pairs

    def _l1_norm(self, persistence_pairs: list[tuple[float, float]]) -> float:
        """Simplified L1 norm: sum of |death - birth| over all pairs.

        Parameters
        ----------
        persistence_pairs : list[tuple[float, float]]
            Persistence diagram pairs.

        Returns
        -------
        float
            L1 norm (total persistence).
        """
        if not persistence_pairs:
            return 0.0
        return float(sum(abs(d - b) for b, d in persistence_pairs))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute(self, returns_matrix: np.ndarray) -> dict[str, Any]:
        """Compute TDA-based crash-precursor signal.

        Parameters
        ----------
        returns_matrix : np.ndarray
            Shape (N, M) — N time bars, M symbols.  Transposed internally
            so each symbol becomes a point in N-dimensional space.

        Returns
        -------
        dict
            Keys: l1_norm, l1_zscore, n_features, risk_off, signal,
            method_id, confidence, ts.
        """
        ts = time.time()

        if returns_matrix.ndim != 2 or returns_matrix.shape[0] < 2 or returns_matrix.shape[1] < 2:
            return {
                "l1_norm": 0.0,
                "l1_zscore": 0.0,
                "n_features": 0,
                "risk_off": False,
                "signal": 0,
                "method_id": "M11",
                "confidence": 0.0,
                "ts": ts,
            }

        # Transpose: M points in N-dim space
        points = returns_matrix.T  # (M, N)

        dist = self._distance_matrix(points)
        pairs = self._persistence_h0(dist)
        l1 = self._l1_norm(pairs)

        # z-score against rolling history
        self._l1_history.append(l1)
        if len(self._l1_history) >= 3:
            arr = np.array(self._l1_history)
            mu = arr.mean()
            std = arr.std()
            l1_zscore = (l1 - mu) / std if std > 1e-12 else 0.0
        else:
            l1_zscore = 0.0

        risk_off = bool(l1_zscore > self.zscore_threshold)
        signal = -1 if risk_off else 0
        confidence = min(abs(l1_zscore) / (self.zscore_threshold * 2.0), 1.0)

        return {
            "l1_norm": float(l1),
            "l1_zscore": float(l1_zscore),
            "n_features": len(pairs),
            "risk_off": risk_off,
            "signal": signal,
            "method_id": "M11",
            "confidence": float(confidence),
            "ts": ts,
        }

    def reset(self) -> None:
        """Clear rolling history."""
        self._l1_history.clear()
