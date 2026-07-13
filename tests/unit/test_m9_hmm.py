"""
Tests for M9 — HMM Vola-OFI-Funding (3-State).

Tests:
- Initial state is uniform
- Forward step updates probabilities
- High volatility features -> HIGH_VOL state
- Calm features -> TREND_UP or MEAN_REVERT
- State labels map correctly
- Probabilities sum to 1.0
- HIGH_VOL signal is -1 (risk-off)
- TREND_UP signal is 1
- Fit with synthetic 3-cluster data separates states
- Reset restores uniform prior
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.layers.l3_regime.m9_hmm import M9HMM, _STATE_LABELS, _STATE_SIGNALS


class TestInitialStateUniform:
    """Prior should be uniform across all states."""

    def test_initial_state_uniform(self) -> None:
        hmm = M9HMM()
        probs = hmm._alpha
        expected = 1.0 / hmm.n_states
        np.testing.assert_allclose(probs, expected, atol=1e-10)


class TestForwardStepUpdatesProbs:
    """After a forward step, probabilities should change from uniform."""

    def test_forward_step_updates_probs(self) -> None:
        hmm = M9HMM()
        initial = hmm._alpha.copy()
        # Feed a high-vol observation
        obs = np.array([0.10, -0.5, 0.001])
        alpha = hmm._forward_step(obs)
        # Should no longer be uniform
        assert not np.allclose(alpha, initial, atol=1e-6), (
            "Forward step should update probabilities away from uniform"
        )


class TestHighVolFeaturesDetected:
    """Extreme volatility should push the model toward HIGH_VOL state."""

    def test_high_vol_features_detected(self) -> None:
        hmm = M9HMM()
        # Repeatedly feed high-vol, negative OFI, extreme funding
        obs = np.array([0.15, -0.8, 0.002])
        for _ in range(20):
            result = hmm.compute(obs)
        # HIGH_VOL = state 2 should be most probable
        assert result["state"] == 2, (
            f"Expected HIGH_VOL (2), got {result['state']} ({result['state_label']})"
        )
        assert result["state_label"] == "HIGH_VOL"


class TestCalmFeaturesDetected:
    """Low volatility, positive OFI should yield TREND_UP or MEAN_REVERT."""

    def test_calm_features_detected(self) -> None:
        hmm = M9HMM()
        obs = np.array([0.008, 0.6, 0.00005])
        for _ in range(20):
            result = hmm.compute(obs)
        # Should be TREND_UP (0) given low vol and positive OFI
        assert result["state"] in (0, 1), (
            f"Expected TREND_UP or MEAN_REVERT, got {result['state_label']}"
        )


class TestStateLabelsCorrect:
    """State label mapping must be consistent."""

    def test_state_labels_correct(self) -> None:
        assert _STATE_LABELS[0] == "TREND_UP"
        assert _STATE_LABELS[1] == "MEAN_REVERT"
        assert _STATE_LABELS[2] == "HIGH_VOL"


class TestProbsSumToOne:
    """State probabilities must always sum to 1.0."""

    def test_probs_sum_to_one(self) -> None:
        hmm = M9HMM()
        rng = np.random.default_rng(42)
        for _ in range(50):
            obs = rng.normal(size=3) * np.array([0.03, 0.5, 0.0003])
            result = hmm.compute(obs)
            total = sum(result["state_probs"])
            assert abs(total - 1.0) < 1e-8, (
                f"State probs sum to {total}, expected 1.0"
            )


class TestSignalHighVolRiskOff:
    """HIGH_VOL state should produce signal = -1."""

    def test_signal_high_vol_risk_off(self) -> None:
        assert _STATE_SIGNALS[2] == -1
        hmm = M9HMM()
        obs = np.array([0.15, -0.8, 0.002])
        for _ in range(20):
            result = hmm.compute(obs)
        if result["state"] == 2:
            assert result["signal"] == -1


class TestSignalTrendUp:
    """TREND_UP state should produce signal = 1."""

    def test_signal_trend_up(self) -> None:
        assert _STATE_SIGNALS[0] == 1
        hmm = M9HMM()
        obs = np.array([0.008, 0.6, 0.00005])
        for _ in range(20):
            result = hmm.compute(obs)
        if result["state"] == 0:
            assert result["signal"] == 1


class TestFitWithSyntheticData:
    """Three clear clusters should be separable after fit."""

    def test_fit_with_synthetic_data(self) -> None:
        rng = np.random.default_rng(42)
        n_per_cluster = 200

        # Cluster 0: TREND_UP — low vol, positive OFI, near-zero funding
        c0 = rng.normal(loc=[0.01, 0.5, 0.0001], scale=[0.002, 0.1, 0.00005],
                        size=(n_per_cluster, 3))
        # Cluster 1: MEAN_REVERT — medium vol, ~0 OFI, near-zero funding
        c1 = rng.normal(loc=[0.03, 0.0, 0.0000], scale=[0.005, 0.1, 0.00005],
                        size=(n_per_cluster, 3))
        # Cluster 2: HIGH_VOL — high vol, negative OFI, extreme funding
        c2 = rng.normal(loc=[0.08, -0.5, 0.001], scale=[0.01, 0.1, 0.0002],
                        size=(n_per_cluster, 3))

        # Interleave in blocks to create regime transitions
        features = np.vstack([c0, c1, c2])

        hmm = M9HMM()
        hmm.fit(features)

        # After fit, feeding a HIGH_VOL observation should detect state 2
        hmm.reset()
        obs_hv = np.array([0.08, -0.5, 0.001])
        for _ in range(10):
            result = hmm.compute(obs_hv)
        assert result["state"] == 2, (
            f"After fit, expected HIGH_VOL (2) for high-vol obs, got {result['state']}"
        )

        # Feeding a low-vol observation should detect state 0
        hmm.reset()
        obs_tu = np.array([0.01, 0.5, 0.0001])
        for _ in range(10):
            result = hmm.compute(obs_tu)
        assert result["state"] == 0, (
            f"After fit, expected TREND_UP (0) for calm obs, got {result['state']}"
        )


class TestMalformedFeaturesDegradeGracefully:
    """Regression: compute() must not crash on a malformed/empty features
    vector (CRITICAL_REVIEW_2 M9 finding).

    Previously an empty or wrong-length array crashed with an unhandled
    ValueError from numpy broadcasting in _gaussian_emission, unlike the
    neighbouring M6-M8/M10-M13 modules which tolerate degenerate inputs.
    """

    def test_empty_array_does_not_crash(self) -> None:
        hmm = M9HMM()
        result = hmm.compute(np.array([]))
        assert result["degraded"] is True
        assert result["method_id"] == "M9"
        assert result["state"] in (0, 1, 2)

    def test_wrong_length_array_does_not_crash(self) -> None:
        hmm = M9HMM()
        result = hmm.compute(np.array([0.1, 0.2]))  # length 2 != n_features=3
        assert result["degraded"] is True

    def test_degraded_call_does_not_advance_state(self) -> None:
        """A malformed call should return the last known state rather than
        silently drifting it via an invalid forward step."""
        hmm = M9HMM()
        obs = np.array([0.10, -0.5, 0.001])
        hmm.compute(obs)
        alpha_before = hmm._alpha.copy()

        hmm.compute(np.array([]))  # malformed — should not update _alpha

        np.testing.assert_array_equal(hmm._alpha, alpha_before)

    def test_valid_call_after_malformed_recovers(self) -> None:
        """After a malformed call, a subsequent valid call must work
        normally (no permanent degradation)."""
        hmm = M9HMM()
        hmm.compute(np.array([]))  # malformed, degrades gracefully
        result = hmm.compute(np.array([0.008, 0.6, 0.00005]))
        assert result["degraded"] is False
        assert result["method_id"] == "M9"

    def test_well_formed_call_marked_not_degraded(self) -> None:
        hmm = M9HMM()
        result = hmm.compute(np.array([0.01, 0.5, 0.0001]))
        assert result["degraded"] is False


class TestResetToPrior:
    """Reset should restore uniform prior."""

    def test_reset_to_prior(self) -> None:
        hmm = M9HMM()
        obs = np.array([0.10, -0.5, 0.001])
        for _ in range(10):
            hmm.compute(obs)
        # Alpha should have diverged from uniform
        assert not np.allclose(hmm._alpha, hmm.state_prior, atol=1e-3)
        # Reset
        hmm.reset()
        np.testing.assert_allclose(hmm._alpha, hmm.state_prior)
