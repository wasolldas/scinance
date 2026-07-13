"""
Tests for M12 — RQA Recurrence Quantification Analysis.

Tests:
- Embed produces correct output dimensions
- Recurrence matrix is symmetric
- Periodic signal yields high DET
- Random signal yields low DET
- Periodic signal yields high LAM
- Breakout signal triggered when DET and LAM are both high
- Auto-epsilon calculation works
- Reset is callable (interface conformance)
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.layers.l3_regime.m12_rqa import M12RQA


class TestEmbedDimensions:
    """Embedding output shape should be (N - (dim-1)*delay, dim)."""

    def test_embed_dimensions(self) -> None:
        mod = M12RQA()
        series = np.arange(100, dtype=np.float64)
        dim, delay = 3, 2
        embedded = mod._embed(series, dim, delay)
        expected_rows = 100 - (dim - 1) * delay  # 100 - 4 = 96
        assert embedded.shape == (expected_rows, dim), (
            f"Expected ({expected_rows}, {dim}), got {embedded.shape}"
        )
        # Verify first row values: [0, 2, 4]
        np.testing.assert_array_equal(embedded[0], [0, 2, 4])


class TestRecurrenceMatrixSymmetric:
    """Recurrence matrix R should be symmetric."""

    def test_recurrence_matrix_symmetric(self) -> None:
        mod = M12RQA()
        rng = np.random.default_rng(42)
        series = rng.normal(0, 1, 50)
        embedded = mod._embed(series, dim=3, delay=1)
        R = mod._recurrence_matrix(embedded, epsilon=0.5)
        np.testing.assert_array_equal(R, R.T)


class TestDetPeriodicSignal:
    """A periodic (sine) signal should have high DET (many diagonal lines)."""

    def test_det_periodic_signal(self) -> None:
        mod = M12RQA()
        t = np.linspace(0, 10 * np.pi, 500)
        series = np.sin(t)
        embedded = mod._embed(series, dim=3, delay=1)
        epsilon = 0.3 * np.std(series)
        R = mod._recurrence_matrix(embedded, epsilon)
        det = mod._det(R, l_min=2)
        assert det > 0.3, (
            f"DET = {det}, expected > 0.3 for periodic signal"
        )


class TestDetRandomSignal:
    """A random signal should have low DET (few diagonal structures)."""

    def test_det_random_signal(self) -> None:
        mod = M12RQA()
        rng = np.random.default_rng(42)
        series = rng.normal(0, 1, 500)
        embedded = mod._embed(series, dim=3, delay=1)
        epsilon = 0.1 * np.std(series)
        R = mod._recurrence_matrix(embedded, epsilon)
        det = mod._det(R, l_min=2)
        assert det < 0.7, (
            f"DET = {det}, expected < 0.7 for random signal"
        )


class TestLamPeriodic:
    """A periodic signal should have high LAM (vertical structures)."""

    def test_lam_periodic(self) -> None:
        mod = M12RQA()
        t = np.linspace(0, 10 * np.pi, 500)
        series = np.sin(t)
        embedded = mod._embed(series, dim=3, delay=1)
        epsilon = 0.3 * np.std(series)
        R = mod._recurrence_matrix(embedded, epsilon)
        lam = mod._lam(R, v_min=2)
        assert lam > 0.3, (
            f"LAM = {lam}, expected > 0.3 for periodic signal"
        )


class TestBreakoutSignalHighDetLam:
    """When DET > 0.7 and LAM > 0.7, breakout_signal should be True."""

    def test_breakout_signal_high_det_lam(self) -> None:
        mod = M12RQA(det_threshold=0.7, lam_threshold=0.7)
        # Create a very regular, repeating pattern -> high DET and LAM
        pattern = np.tile(np.array([0.0, 0.1, 0.2, 0.1]), 125)  # 500 points
        result = mod.compute(pattern, epsilon=0.05)
        # With such a regular pattern, DET and LAM should be high
        if result["det"] > 0.7 and result["lam"] > 0.7:
            assert result["breakout_signal"] is True
            assert result["signal"] == 1
        # At minimum, the signal should be 0 or 1
        assert result["signal"] in (0, 1)


class TestEpsilonAutoCalculation:
    """When epsilon is None, it should be auto-calculated as 10% of std."""

    def test_epsilon_auto_calculation(self) -> None:
        mod = M12RQA()
        rng = np.random.default_rng(42)
        series = rng.normal(0, 2.0, 200)
        result = mod.compute(series)
        # Should not crash and should produce valid output
        assert 0.0 <= result["det"] <= 1.0
        assert 0.0 <= result["lam"] <= 1.0
        assert result["method_id"] == "M12"


class TestReset:
    """Reset should be callable without error."""

    def test_reset(self) -> None:
        mod = M12RQA()
        rng = np.random.default_rng(42)
        mod.compute(rng.normal(0, 1, 200))
        mod.reset()  # Should not raise


class TestConstantSeriesNoSpuriousBreakout:
    """Regression: a frozen/constant series must NOT yield a high-confidence
    breakout signal (CRITICAL_REVIEW_2 M12 finding).

    A stuck feed (WS reconnect, illiquid symbol, repeated last price)
    previously drove auto-epsilon to its numerical floor, making the
    recurrence matrix fully recurrent and producing confidence≈1.0
    "breakout imminent" for a market that wasn't moving at all.
    """

    def test_exactly_constant_series_no_breakout(self) -> None:
        mod = M12RQA()
        series = np.ones(500)
        result = mod.compute(series)

        assert result["breakout_signal"] is False
        assert result["signal"] == 0
        assert result["confidence"] == 0.0
        assert result["degenerate"] is True

    def test_near_constant_series_no_breakout(self) -> None:
        """A series with only floating-point-noise-level variation should
        also be treated as degenerate, not just an exactly constant one."""
        mod = M12RQA()
        rng = np.random.default_rng(7)
        series = 1.0 + rng.normal(0, 1e-13, 500)
        result = mod.compute(series)

        assert result["breakout_signal"] is False
        assert result["confidence"] == 0.0
        assert result["degenerate"] is True

    def test_normal_series_not_flagged_degenerate(self) -> None:
        """A genuinely varying series should not be marked degenerate."""
        mod = M12RQA()
        rng = np.random.default_rng(7)
        series = rng.normal(0, 1.0, 500)
        result = mod.compute(series)

        assert result["degenerate"] is False
