"""
Tests for M8 — Bayesian Online Changepoint Detection (BOCPD).

Tests:
- Constant data produces no changepoints
- Mean shift triggers changepoint detection
- Variance shift triggers changepoint detection
- Run-length increases monotonically without changepoints
- Multiple mean shifts produce multiple detections
- First few updates are numerically stable
- Reset reinitializes all state
- Signal is binary (0 or 1)
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge._legacy_v1.layers.l3_regime.m8_bocpd import M8BOCPD


class TestNoChangepointConstantData:
    """Constant input should never trigger a changepoint."""

    def test_constant_data_no_changepoint(self) -> None:
        detector = M8BOCPD(hazard_lambda=100, prior_mean=5.0, prior_var=1.0)
        results = []
        for _ in range(200):
            r = detector.compute(5.0)
            results.append(r)
        # After burn-in, no changepoint should be detected
        # (skip first few where prior dominates)
        late_results = results[20:]
        assert all(r["changepoint"] is False for r in late_results), (
            "Constant data should not trigger changepoints after burn-in"
        )


class TestChangepointMeanShift:
    """A sudden mean shift should be detected as a changepoint."""

    def test_mean_shift_detected(self) -> None:
        rng = np.random.default_rng(42)
        detector = M8BOCPD(hazard_lambda=200, prior_mean=0.0, prior_var=1.0)

        # Phase 1: stable regime around mean=0
        for _ in range(100):
            detector.compute(rng.normal(0.0, 0.5))

        # Phase 2: sudden shift to mean=10
        changepoints = []
        for i in range(50):
            r = detector.compute(rng.normal(10.0, 0.5))
            if r["changepoint"]:
                changepoints.append(i)

        assert len(changepoints) > 0, (
            "Mean shift from 0 to 10 should trigger at least one changepoint"
        )
        # Should detect early in phase 2
        assert changepoints[0] < 10, (
            "Changepoint should be detected within first 10 observations of shift"
        )


class TestChangepointVarianceShift:
    """A sudden variance change should be detectable."""

    def test_variance_shift_detected(self) -> None:
        rng = np.random.default_rng(123)
        detector = M8BOCPD(hazard_lambda=200, prior_mean=0.0, prior_var=0.1)

        # Phase 1: low variance
        for _ in range(150):
            detector.compute(rng.normal(0.0, 0.1))

        # Phase 2: high variance (10x increase)
        changepoints = []
        for i in range(100):
            r = detector.compute(rng.normal(0.0, 5.0))
            if r["changepoint"]:
                changepoints.append(i)

        assert len(changepoints) > 0, (
            "Variance shift from 0.1 to 5.0 should trigger changepoint detection"
        )


class TestRunLengthIncreases:
    """Without changepoints, the MAP run-length should grow monotonically."""

    def test_run_length_grows(self) -> None:
        detector = M8BOCPD(hazard_lambda=500, prior_mean=0.0, prior_var=1.0)

        run_lengths = []
        for _ in range(80):
            r = detector.compute(0.0)
            run_lengths.append(r["run_length_map"])

        # After initial stabilization, run-length MAP should be increasing
        # (monotonically or at least trending upward)
        later = run_lengths[10:]
        increasing_count = sum(
            1 for i in range(1, len(later)) if later[i] >= later[i - 1]
        )
        assert increasing_count > len(later) * 0.8, (
            "Run-length MAP should be mostly increasing for constant data"
        )


class TestMultipleChangepoints:
    """Multiple mean shifts should produce multiple changepoint detections."""

    def test_multiple_shifts(self) -> None:
        rng = np.random.default_rng(77)
        detector = M8BOCPD(hazard_lambda=100, prior_mean=0.0, prior_var=1.0)

        means = [0.0, 8.0, -5.0, 12.0]
        cp_counts = 0

        for mean_val in means:
            for _ in range(80):
                r = detector.compute(rng.normal(mean_val, 0.3))
                if r["changepoint"]:
                    cp_counts += 1

        # At least 2 of the 3 transitions should be detected
        assert cp_counts >= 2, (
            f"Expected at least 2 changepoints across 3 transitions, got {cp_counts}"
        )


class TestFirstFewUpdatesNoCrash:
    """The first few updates should not raise exceptions or produce NaN."""

    def test_initial_stability(self) -> None:
        detector = M8BOCPD()
        for i in range(5):
            r = detector.compute(float(i))
            assert not np.isnan(r["changepoint_prob"]), (
                f"changepoint_prob should not be NaN at step {i}"
            )
            assert isinstance(r["signal"], int)
            assert isinstance(r["run_length_map"], int)

    def test_single_observation(self) -> None:
        detector = M8BOCPD()
        r = detector.compute(42.0)
        assert "changepoint" in r
        assert "method_id" in r
        assert r["method_id"] == "M8"


class TestResetReinitializes:
    """After reset(), state should match a fresh instance."""

    def test_reset(self) -> None:
        detector = M8BOCPD(hazard_lambda=100, prior_mean=0.0, prior_var=1.0)

        # Feed data to build up state
        for _ in range(50):
            detector.compute(1.0)

        assert len(detector._R) > 1, "Run-length distribution should have grown"

        detector.reset()

        assert len(detector._R) == 1, "After reset, R should have length 1"
        assert detector._R[0] == 1.0, "After reset, R[0] should be 1.0"
        assert detector._t == 0, "After reset, time counter should be 0"
        assert len(detector._mu) == 1
        assert len(detector._kappa) == 1
        assert len(detector._alpha) == 1
        assert len(detector._beta) == 1


class TestSignalIsBinary:
    """Signal should always be 0 or 1."""

    def test_signal_values(self) -> None:
        rng = np.random.default_rng(99)
        detector = M8BOCPD(hazard_lambda=100, prior_mean=0.0, prior_var=1.0)

        signals = set()
        # Phase 1: stable
        for _ in range(50):
            r = detector.compute(rng.normal(0.0, 1.0))
            signals.add(r["signal"])
        # Phase 2: shift
        for _ in range(50):
            r = detector.compute(rng.normal(20.0, 1.0))
            signals.add(r["signal"])

        assert signals.issubset({0, 1}), (
            f"Signal should only be 0 or 1, got {signals}"
        )
        # Should have both 0 and 1
        assert 0 in signals, "Should have at least one neutral signal"
        assert 1 in signals, "Should have at least one changepoint signal"


class TestNaNObservationSelfHeals:
    """Regression: a single non-finite observation must not poison the
    run-length posterior forever (CRITICAL_REVIEW_2 M8 finding).

    Previously, `evidence > 0` is False for NaN, so the NaN-contaminated
    unnormalised array was adopted as the new state directly, and every
    subsequent compute() call — even with perfectly normal data — kept
    returning NaN silently.
    """

    def test_single_nan_does_not_poison_state_forever(self) -> None:
        rng = np.random.default_rng(5)
        detector = M8BOCPD(hazard_lambda=200, prior_mean=0.0, prior_var=1.0)

        for _ in range(30):
            detector.compute(rng.normal(0.0, 0.5))

        # Poison with a single NaN tick (e.g. from an upstream 0/0).
        poisoned = detector.compute(float("nan"))
        assert not np.isnan(poisoned["changepoint_prob"])

        # Every call *after* the NaN tick must recover — not stay NaN.
        for _ in range(10):
            r = detector.compute(rng.normal(0.0, 0.5))
            assert not np.isnan(r["changepoint_prob"]), (
                "State should self-heal after a single NaN tick instead of "
                "staying poisoned forever"
            )
            assert not np.isnan(detector._R).any(), (
                "Internal run-length distribution should not carry NaN "
                "after recovering from a poisoned tick"
            )

    def test_inf_observation_also_skipped(self) -> None:
        detector = M8BOCPD(hazard_lambda=200, prior_mean=0.0, prior_var=1.0)
        for _ in range(10):
            detector.compute(0.0)
        t_before = detector._t

        r = detector.compute(float("inf"))
        assert not np.isnan(r["changepoint_prob"])
        assert r["changepoint"] is False
        # A skipped tick must not advance the internal time counter.
        assert detector._t == t_before

        # Follow-up calls remain healthy.
        r2 = detector.compute(0.0)
        assert not np.isnan(r2["changepoint_prob"])


class TestReturnDictStructure:
    """Ensure all expected keys are present in the return dict."""

    def test_keys_present(self) -> None:
        detector = M8BOCPD()
        r = detector.compute(1.0)
        expected_keys = {
            "changepoint",
            "changepoint_prob",
            "run_length_map",
            "signal",
            "method_id",
            "confidence",
            "ts",
        }
        assert expected_keys.issubset(r.keys()), (
            f"Missing keys: {expected_keys - r.keys()}"
        )
        assert r["method_id"] == "M8"
        assert isinstance(r["changepoint"], bool)
        assert isinstance(r["changepoint_prob"], float)
        assert isinstance(r["run_length_map"], int)
        assert isinstance(r["confidence"], float)
        assert 0.0 <= r["confidence"] <= 1.0
