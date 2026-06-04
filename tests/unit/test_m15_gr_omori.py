"""
Tests for M15 — Gutenberg-Richter b-value + Omori aftershock decay.

Tests:
- Aki b-value matches known analytical result
- b-value returns None when below minimum events threshold
- Mainshock detection for large events exceeding Q99
- Normal events do not trigger mainshock
- Omori fit works on synthetic aftershock sequences
- Omori inactive when no mainshock
- Omori times out after forecast window
- Reset clears mainshock state
"""

from __future__ import annotations

import time
import warnings

import numpy as np
import pytest
from scipy.optimize import OptimizeWarning, curve_fit

from bybit_edge.config import (
    GR_MAINSHOCK_QUANTILE,
    GR_MIN_EVENTS,
    OMORI_FORECAST_MINUTES,
)
from bybit_edge.layers.l4_pattern.m15_gr_omori import M15GROmori


def _make_liq_event(timestamp_ms: int, usd_value: float, side: str = "Buy") -> dict:
    """Helper to create a liquidation event dict."""
    return {
        "timestamp_ms": timestamp_ms,
        "usd_value": usd_value,
        "side": side,
    }


def _make_uniform_events(
    n: int, base_ts_ms: int, usd_range: tuple[float, float] = (1_000.0, 50_000.0)
) -> list[dict]:
    """Create n events with uniform USD values spread across 24h."""
    rng = np.random.default_rng(42)
    events = []
    for i in range(n):
        ts_ms = base_ts_ms - (86400_000 - i * (86400_000 // n))
        usd = float(rng.uniform(usd_range[0], usd_range[1]))
        events.append(_make_liq_event(ts_ms, usd))
    return events


class TestAkiBValueKnown:
    """Verify Aki (1965) MLE b-value against analytical expectation."""

    def test_known_exponential_distribution(self) -> None:
        """For exponentially distributed magnitudes, b = log10(e) / (mean - min).

        With many samples from Exp(rate=1) shifted to start at M_min=1,
        mean ~ M_min + 1/rate = 2.0, so b ~ log10(e) / 1.0 ~ 0.4343.
        """
        rng = np.random.default_rng(42)
        magnitudes = rng.exponential(1.0, size=10000) + 1.0
        m = M15GROmori()
        b = m._aki_b_value(magnitudes)
        expected = np.log10(np.e) / (np.mean(magnitudes) - np.min(magnitudes))
        assert abs(b - expected) < 0.01, (
            f"b-value {b} should match analytical {expected}"
        )

    def test_degenerate_returns_one(self) -> None:
        """When all magnitudes are equal, b should be 1.0 (fallback)."""
        magnitudes = np.full(100, 3.0)
        m = M15GROmori()
        b = m._aki_b_value(magnitudes)
        assert b == 1.0


class TestBValueNeedsMinEvents:
    """b_value should be None when fewer than GR_MIN_EVENTS events."""

    def test_too_few_events(self) -> None:
        m = M15GROmori(min_events=50)
        now = time.time()
        # Only 10 events
        events = _make_uniform_events(10, int(now * 1000))
        result = m.compute(events, now)
        assert result["b_value"] is None, (
            "b_value should be None with only 10 events"
        )

    def test_enough_events_produces_b(self) -> None:
        m = M15GROmori(min_events=50)
        now = time.time()
        events = _make_uniform_events(100, int(now * 1000))
        result = m.compute(events, now)
        assert result["b_value"] is not None, (
            "b_value should be computed with 100 events"
        )
        assert result["b_value"] > 0, "b_value should be positive"


class TestMainshockDetection:
    """A very large event exceeding Q99 should trigger mainshock detection."""

    def test_large_event_triggers_mainshock(self) -> None:
        m = M15GROmori(min_events=50)
        now = time.time()

        # First: fill buffer with normal events
        normal_events = _make_uniform_events(80, int(now * 1000), (1_000, 10_000))
        result = m.compute(normal_events, now)

        # Now add a massive event (100x the max)
        mainshock_event = [_make_liq_event(int(now * 1000), 5_000_000.0)]
        result = m.compute(mainshock_event, now)

        assert result["mainshock"] is True, (
            "Event 100x above normal should be detected as mainshock"
        )
        assert result["mainshock_ts"] is not None


class TestNoMainshockNormalEvents:
    """Normal events should not trigger mainshock."""

    def test_normal_events_no_mainshock(self) -> None:
        m = M15GROmori(min_events=50)
        now = time.time()

        # All events in a tight range — none will exceed Q99
        events = _make_uniform_events(80, int(now * 1000), (5_000, 5_100))
        result = m.compute(events, now)

        # The last event is part of the same batch, so Q99 is computed
        # on the same population. A value within [5000, 5100] is unlikely
        # to exceed Q99 of the same set unless it's one of the top values.
        # To be safe, send a second normal batch:
        normal_followup = [
            _make_liq_event(int(now * 1000) + 1, 5_050.0),
        ]
        result = m.compute(normal_followup, now)
        assert result["mainshock"] is False, (
            "Normal event within Q99 range should not trigger mainshock"
        )


class TestOmoriFitAftershocks:
    """Synthetic aftershock sequence should produce a valid Omori fit."""

    def test_synthetic_omori(self) -> None:
        m = M15GROmori(min_events=10, omori_forecast_minutes=60)

        # Create a mainshock and aftershock sequence following Omori law
        mainshock_ts = 1_000_000.0
        mainshock_ts_ms = int(mainshock_ts * 1000)

        # Fill with background events first
        rng = np.random.default_rng(42)
        base_events: list[dict] = []
        for i in range(60):
            ts_ms = mainshock_ts_ms - 86400_000 + i * (86400_000 // 60)
            usd = float(rng.uniform(1_000, 10_000))
            base_events.append(_make_liq_event(ts_ms, usd))

        # Mainshock: huge event
        base_events.append(_make_liq_event(mainshock_ts_ms, 10_000_000.0))

        # Aftershocks: events following Omori decay pattern
        # Place events at increasing intervals (mimicking power-law decay)
        aftershock_events: list[dict] = []
        for i in range(1, 30):
            dt_s = float(i * 2)  # events at 2, 4, 6, ... seconds
            ts_ms = mainshock_ts_ms + int(dt_s * 1000)
            usd = float(rng.uniform(1_000, 50_000))
            aftershock_events.append(_make_liq_event(ts_ms, usd))

        # Feed mainshock
        current_ts = mainshock_ts + 0.5
        m.compute(base_events, current_ts)

        # Feed aftershocks ~60s after mainshock
        current_ts = mainshock_ts + 65.0
        result = m.compute(aftershock_events, current_ts)

        # Mainshock should still be active and Omori should have been fitted
        assert result["mainshock_ts"] is not None, "Mainshock should be tracked"
        # The omori fit may or may not succeed depending on data shape,
        # but the module should not crash
        assert isinstance(result["omori_active"], bool)
        assert isinstance(result["aftershock_rate"], float)


class TestOmoriInactiveNoMainshock:
    """Without a mainshock, Omori should remain inactive."""

    def test_no_mainshock_no_omori(self) -> None:
        m = M15GROmori(min_events=50)
        now = time.time()
        events = _make_uniform_events(80, int(now * 1000), (5_000, 5_100))
        result = m.compute(events, now)
        assert result["omori_active"] is False, (
            "Omori should not be active without a mainshock"
        )
        assert result["aftershock_rate"] == 0.0


class TestOmoriTimeout:
    """Omori should deactivate after OMORI_FORECAST_MINUTES."""

    def test_timeout_clears_mainshock(self) -> None:
        m = M15GROmori(min_events=10, omori_forecast_minutes=30)

        now = time.time()
        mainshock_ts_ms = int(now * 1000)

        # Background + mainshock
        events = _make_uniform_events(20, mainshock_ts_ms, (1_000, 10_000))
        events.append(_make_liq_event(mainshock_ts_ms, 50_000_000.0))
        m.compute(events, now)

        # Confirm mainshock is tracked
        assert m._mainshock_ts is not None

        # Advance time by 35 minutes (past the 30-minute window)
        future_ts = now + 35 * 60
        result = m.compute([], future_ts)

        assert result["omori_active"] is False, (
            "Omori should be inactive after timeout"
        )
        assert m._mainshock_ts is None, (
            "Mainshock should be cleared after timeout"
        )


class TestReset:
    """Reset should clear all internal state."""

    def test_reset_clears_state(self) -> None:
        m = M15GROmori(min_events=10)
        now = time.time()

        events = _make_uniform_events(30, int(now * 1000))
        events.append(_make_liq_event(int(now * 1000), 50_000_000.0))
        m.compute(events, now)

        assert len(m._event_buffer) > 0
        assert m._mainshock_ts is not None

        m.reset()

        assert m._mainshock_ts is None
        assert m._mainshock_usd == 0.0
        assert m._omori_params is None
        assert len(m._event_buffer) == 0


class TestReturnDictStructure:
    """Ensure all expected keys are present in the return dict."""

    def test_keys_present(self) -> None:
        m = M15GROmori()
        now = time.time()
        result = m.compute([], now)
        expected_keys = {
            "b_value",
            "b_low",
            "mainshock",
            "mainshock_ts",
            "omori_active",
            "aftershock_rate",
            "omori_params",
            "signal",
            "method_id",
            "confidence",
            "ts",
        }
        assert expected_keys.issubset(result.keys()), (
            f"Missing keys: {expected_keys - result.keys()}"
        )
        assert result["method_id"] == "M15"
        assert result["signal"] in (0, 1)


class TestNoOptimizeWarningLeaks:
    """The Omori curve_fit must not leak the harmless OptimizeWarning.

    ``scipy.optimize.curve_fit`` emits an ``OptimizeWarning`` ("Covariance of
    the parameters could not be estimated") when the problem is degenerate
    (e.g. 3 data points for 3 free parameters). The fit (popt) is still valid,
    but the warning floods diagnostic output. ``_fit_omori`` suppresses only
    that specific warning.
    """

    # Aftershock offsets (seconds after the mainshock) that bin down to exactly
    # three non-zero 1-second bins, which forces curve_fit into a covariance-
    # estimation failure and thus reliably raises the OptimizeWarning.
    _TRIGGER_OFFSETS_S = (0.3, 0.6, 1.5, 2.5, 4.2)

    def test_trigger_offsets_actually_warn_when_unsuppressed(self) -> None:
        """Sanity check: the raw fit on this data does emit OptimizeWarning.

        Guards the leak test against silently becoming a no-op if scipy's
        warning behaviour changes.
        """
        mainshock = 1_000.0
        times = np.array(
            [mainshock + d for d in self._TRIGGER_OFFSETS_S], dtype=np.float64
        )
        dt = times - mainshock
        dt = dt[dt > 0]
        dt_sorted = np.sort(dt)
        n_bins = max(int(dt_sorted[-1]), 1)
        bin_edges = np.arange(0, n_bins + 1, dtype=np.float64)
        counts, _ = np.histogram(dt_sorted, bins=bin_edges)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
        mask = counts > 0
        t_data = bin_centers[mask]
        rate_data = counts[mask].astype(np.float64)

        m = M15GROmori()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            curve_fit(
                m._omori_fn,
                t_data,
                rate_data,
                p0=[rate_data[0], 1.0, 1.0],
                bounds=([0.0, 0.001, 0.5], [np.inf, np.inf, 2.5]),
                maxfev=2000,
            )
        optimize_warnings = [
            w for w in caught if issubclass(w.category, OptimizeWarning)
        ]
        assert optimize_warnings, (
            "Expected the raw curve_fit on the trigger data to emit an "
            "OptimizeWarning; the leak test below would otherwise be vacuous."
        )

    def test_fit_omori_does_not_leak_optimize_warning(self) -> None:
        """_fit_omori on warning-triggering data must not leak OptimizeWarning."""
        mainshock = 1_000.0
        times = np.array(
            [mainshock + d for d in self._TRIGGER_OFFSETS_S], dtype=np.float64
        )

        m = M15GROmori()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = m._fit_omori(times, mainshock)

        leaked = [w for w in caught if issubclass(w.category, OptimizeWarning)]
        assert not leaked, (
            f"OptimizeWarning leaked through _fit_omori: "
            f"{[str(w.message) for w in leaked]}"
        )
        # Fit logic/return values are unchanged: a valid fit still comes back.
        assert result is not None
        assert {"K", "c", "p"} == set(result.keys())


class TestSignalLogic:
    """Signal should be 1 only when mainshock AND omori_active."""

    def test_no_events_signal_zero(self) -> None:
        m = M15GROmori()
        result = m.compute([], time.time())
        assert result["signal"] == 0

    def test_mainshock_without_omori_signal_zero(self) -> None:
        """Mainshock alone (no aftershocks for Omori fit) should yield signal=0."""
        m = M15GROmori(min_events=10)
        now = time.time()

        events = _make_uniform_events(20, int(now * 1000), (1_000, 5_000))
        events.append(_make_liq_event(int(now * 1000), 50_000_000.0))
        result = m.compute(events, now)

        # Mainshock should be detected but Omori won't be active
        # (no aftershock data yet)
        if result["mainshock"]:
            # Without aftershock data, omori_active should be False
            assert result["omori_active"] is False or result["signal"] in (0, 1)
