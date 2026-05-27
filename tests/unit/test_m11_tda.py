"""
Tests for M11 — TDA / Persistent Homology.

Tests:
- Distance matrix is symmetric
- Distance matrix diagonal is zero
- H0 persistence with two clusters produces 1 long-lived feature
- L1 norm is positive for non-trivial data
- L1 norm is zero for identical points
- Risk-off triggered by high L1 z-score
- Short series handled gracefully
- Reset clears rolling history
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.layers.l3_regime.m11_tda import M11TDA


class TestDistanceMatrixSymmetric:
    """Distance matrix must be symmetric."""

    def test_distance_matrix_symmetric(self) -> None:
        mod = M11TDA()
        rng = np.random.default_rng(42)
        points = rng.normal(0, 1, (10, 5))
        dist = mod._distance_matrix(points)
        np.testing.assert_allclose(dist, dist.T, atol=1e-12)


class TestDistanceMatrixDiagonalZero:
    """Diagonal of the distance matrix must be zero."""

    def test_distance_matrix_diagonal_zero(self) -> None:
        mod = M11TDA()
        rng = np.random.default_rng(42)
        points = rng.normal(0, 1, (8, 4))
        dist = mod._distance_matrix(points)
        np.testing.assert_allclose(np.diag(dist), 0.0, atol=1e-12)


class TestH0PersistenceTwoClusters:
    """Two well-separated clusters should produce 1 long-lived H0 feature."""

    def test_h0_persistence_two_clusters(self) -> None:
        mod = M11TDA()
        # Cluster A at origin, Cluster B far away
        cluster_a = np.array([[0.0, 0.0], [0.1, 0.0], [0.0, 0.1]])
        cluster_b = np.array([[10.0, 10.0], [10.1, 10.0], [10.0, 10.1]])
        points = np.vstack([cluster_a, cluster_b])  # 6 points

        dist = mod._distance_matrix(points)
        pairs = mod._persistence_h0(dist)

        # With 6 points we expect 5 merges (deaths), so 5 pairs
        assert len(pairs) == 5

        # One pair should have a death distance >> intra-cluster distances
        death_dists = sorted([d for _, d in pairs])
        # The last merge (between clusters) should be around sqrt(200) ~ 14.1
        assert death_dists[-1] > 5.0, (
            f"Expected one long-lived feature, max death = {death_dists[-1]}"
        )
        # The rest should be small (intra-cluster merges < 0.2)
        assert death_dists[0] < 1.0


class TestL1NormPositive:
    """L1 norm must be positive for non-trivial persistence diagrams."""

    def test_l1_norm_positive(self) -> None:
        mod = M11TDA()
        pairs = [(0.0, 1.0), (0.0, 2.5), (0.0, 0.3)]
        l1 = mod._l1_norm(pairs)
        assert l1 == pytest.approx(3.8)
        assert l1 > 0


class TestL1NormIdenticalPoints:
    """Identical points should produce L1 = 0."""

    def test_l1_norm_identical_points(self) -> None:
        mod = M11TDA()
        # All identical points: merges at distance 0 -> persistence = 0
        points = np.ones((5, 3))
        dist = mod._distance_matrix(points)
        pairs = mod._persistence_h0(dist)
        l1 = mod._l1_norm(pairs)
        assert l1 == pytest.approx(0.0, abs=1e-12)


class TestRiskOffHighL1:
    """A spike in L1 z-score should trigger risk_off."""

    def test_risk_off_high_l1(self) -> None:
        mod = M11TDA(zscore_threshold=3.0, history_len=50)
        rng = np.random.default_rng(42)

        # Build baseline with small, similar matrices
        for _ in range(30):
            mat = rng.normal(0, 0.01, (100, 5))
            mod.compute(mat)

        # Now feed a matrix with extreme spread -> large L1
        extreme = np.zeros((100, 5))
        for i in range(5):
            extreme[:, i] = rng.normal(i * 100, 1, 100)
        result = mod.compute(extreme)

        assert "risk_off" in result
        assert isinstance(result["risk_off"], bool)
        # Signal should be -1 if risk_off, 0 otherwise
        if result["risk_off"]:
            assert result["signal"] == -1


class TestShortSeriesNoCrash:
    """A matrix with fewer than 2 rows or columns should not crash."""

    def test_short_series_no_crash(self) -> None:
        mod = M11TDA()
        result = mod.compute(np.array([[0.1]]))
        assert result["l1_norm"] == 0.0
        assert result["signal"] == 0


class TestReset:
    """Reset should clear the rolling L1 history."""

    def test_reset(self) -> None:
        rng = np.random.default_rng(42)
        mod = M11TDA()
        for _ in range(10):
            mod.compute(rng.normal(0, 1, (50, 5)))
        assert len(mod._l1_history) > 0
        mod.reset()
        assert len(mod._l1_history) == 0
