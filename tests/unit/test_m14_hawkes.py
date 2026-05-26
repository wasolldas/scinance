"""
Tests for M14a — Hawkes 1-D Single Channel.

Tests:
- No events: intensity = mu
- Recent event: intensity > mu
- Distant event: intensity ~ mu (decay)
- Subcritical branching ratio
- Critical branching ratio triggers signal
- MLE fit recovers parameters from synthetic Hawkes process
- Log-likelihood is finite for valid events
- Rolling window evicts old events
- Empty events do not crash
- Reset clears state
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.layers.l4_pattern.m14_hawkes import M14HawkesSingleChannel


class TestIntensityNoEvents:
    """With no events, intensity should equal mu."""

    def test_intensity_no_events(self) -> None:
        events = np.array([], dtype=np.float64)
        lam = M14HawkesSingleChannel._intensity(100.0, events, mu=0.5, alpha=0.3, beta=1.0)
        assert abs(lam - 0.5) < 1e-10, f"Expected mu=0.5, got {lam}"


class TestIntensityRecentEvent:
    """A very recent event should push intensity above mu."""

    def test_intensity_recent_event(self) -> None:
        events = np.array([99.99])
        lam = M14HawkesSingleChannel._intensity(100.0, events, mu=0.5, alpha=0.5, beta=1.0)
        assert lam > 0.5, f"Recent event should increase intensity, got {lam}"


class TestIntensityDecay:
    """An event far in the past should contribute almost nothing."""

    def test_intensity_decay(self) -> None:
        events = np.array([0.0])
        lam = M14HawkesSingleChannel._intensity(1000.0, events, mu=0.5, alpha=0.5, beta=1.0)
        # exp(-1000) ~ 0, so lam ~ mu
        assert abs(lam - 0.5) < 1e-6, f"Old event should decay, got {lam}"


class TestBranchingRatioSubcritical:
    """Alpha/beta < 0.9 should yield critical=False."""

    def test_branching_ratio_subcritical(self) -> None:
        hawkes = M14HawkesSingleChannel(critical_rho=0.9)
        hawkes._mu = 1.0
        hawkes._alpha = 0.3
        hawkes._beta = 1.0
        hawkes._last_fit_ts = 1e18  # prevent re-fit

        events = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = hawkes.compute(events, current_ts=6.0)

        assert result["branching_ratio"] < 0.9
        assert result["critical"] is False
        assert result["signal"] == 0


class TestBranchingRatioCritical:
    """Alpha/beta > 0.9 should yield critical=True, signal=1."""

    def test_branching_ratio_critical(self) -> None:
        hawkes = M14HawkesSingleChannel(critical_rho=0.9)
        hawkes._mu = 0.5
        hawkes._alpha = 5.0
        hawkes._beta = 1.0
        hawkes._last_fit_ts = 1e18  # prevent re-fit

        events = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = hawkes.compute(events, current_ts=6.0)

        assert result["branching_ratio"] > 0.9
        assert result["critical"] is True
        assert result["signal"] == 1


class TestMLEFitSyntheticHawkes:
    """MLE should approximately recover parameters from a synthetic Hawkes process."""

    def test_mle_fit_synthetic_hawkes(self) -> None:
        # Simulate a Hawkes process with known parameters
        rng = np.random.default_rng(42)
        mu_true = 1.0
        alpha_true = 0.5
        beta_true = 2.0
        T_max = 200.0

        events = []
        t = 0.0
        lam_max = mu_true + alpha_true * beta_true * 50  # generous upper bound

        while t < T_max:
            # Thinning algorithm
            dt = rng.exponential(1.0 / lam_max)
            t += dt
            if t >= T_max:
                break
            # Compute actual intensity
            ev_arr = np.array(events) if events else np.array([], dtype=np.float64)
            lam_t = mu_true
            if len(ev_arr) > 0:
                causal = ev_arr[ev_arr < t]
                if len(causal) > 0:
                    lam_t += alpha_true * np.sum(beta_true * np.exp(-beta_true * (t - causal)))
            # Accept/reject
            if rng.uniform() < lam_t / lam_max:
                events.append(t)

        events_arr = np.array(events)
        assert len(events_arr) > 20, "Simulation should produce enough events"

        hawkes = M14HawkesSingleChannel()
        mu_fit, alpha_fit, beta_fit = hawkes._fit_mle(events_arr)

        # Parameters should be in the right ballpark (not exact due to stochasticity)
        assert 0.2 < mu_fit < 5.0, f"mu_fit={mu_fit} out of range"
        assert 0.01 < alpha_fit < 5.0, f"alpha_fit={alpha_fit} out of range"
        assert 0.1 < beta_fit < 20.0, f"beta_fit={beta_fit} out of range"


class TestLogLikelihoodFinite:
    """Log-likelihood should be finite for valid event data."""

    def test_log_likelihood_positive_events(self) -> None:
        events = np.array([1.0, 2.0, 3.5, 4.0, 5.5, 7.0, 8.2])
        ll = M14HawkesSingleChannel._log_likelihood(events, mu=1.0, alpha=0.3, beta=1.0)
        assert np.isfinite(ll), f"Log-likelihood should be finite, got {ll}"


class TestRollingWindowEviction:
    """Events outside the window should be evicted."""

    def test_rolling_window_eviction(self) -> None:
        hawkes = M14HawkesSingleChannel(window_seconds=10.0)
        hawkes._last_fit_ts = 1e18  # prevent re-fit

        # Events spread over a wide range
        events = np.array([1.0, 5.0, 50.0, 95.0, 99.0, 100.0])
        result = hawkes.compute(events, current_ts=100.0)

        # Only events >= 90.0 should remain (window = 10s)
        remaining = list(hawkes._events)
        assert all(e >= 90.0 for e in remaining), (
            f"Old events should be evicted, got {remaining}"
        )


class TestEmptyEventsNoCrash:
    """Empty event array should not crash."""

    def test_empty_events_no_crash(self) -> None:
        hawkes = M14HawkesSingleChannel()
        events = np.array([], dtype=np.float64)
        result = hawkes.compute(events, current_ts=100.0)

        assert "branching_ratio" in result
        assert "intensity" in result
        assert result["method_id"] == "M14"
        assert result["signal"] in (-1, 0, 1)


class TestReset:
    """Reset should clear events and restore default parameters."""

    def test_reset(self) -> None:
        hawkes = M14HawkesSingleChannel()
        hawkes._events.extend([1.0, 2.0, 3.0])
        hawkes._mu = 99.0
        hawkes._alpha = 99.0
        hawkes._beta = 99.0
        hawkes._last_fit_ts = 999.0

        hawkes.reset()

        assert len(hawkes._events) == 0
        assert hawkes._mu == 0.1
        assert hawkes._alpha == 0.3
        assert hawkes._beta == 1.0
        assert hawkes._last_fit_ts == 0.0
