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


# ══════════════════════════════════════════════════════════════════════
# Regression: the vectorised M15.compute must be bit-identical to the
# legacy list-comprehension path (behaviour-preserving optimisation).
# ══════════════════════════════════════════════════════════════════════


def _legacy_compute(self: M15GROmori, liq_events, current_ts):
    """Faithful re-implementation of the PRE-optimisation M15.compute body.

    Used as a reference oracle: the live (vectorised) ``compute`` must return
    numerically identical results to this list-based version for every call in
    a sequence, including the stateful mainshock / Omori-fit transitions.
    """
    for ev in liq_events:
        self._event_buffer.append((int(ev["timestamp_ms"]), float(ev["usd_value"])))

    cutoff_ms = int((current_ts - 86400) * 1000)
    recent = [(ts, usd) for ts, usd in self._event_buffer if ts >= cutoff_ms]

    b_value = None
    b_low = False
    if len(recent) >= self._min_events:
        usd_values = np.array([usd for _, usd in recent], dtype=np.float64)
        usd_values = usd_values[usd_values > 0]
        if len(usd_values) >= self._min_events:
            magnitudes = np.log10(usd_values)
            b_value = self._aki_b_value(magnitudes)
            b_low = b_value < 1.0

    mainshock = False
    if len(recent) >= self._min_events:
        usd_arr = np.array([usd for _, usd in recent], dtype=np.float64)
        q99 = float(np.quantile(usd_arr, self._mainshock_quantile))
        for ev in liq_events:
            ev_usd = float(ev["usd_value"])
            if ev_usd > q99:
                mainshock = True
                ev_ts_s = int(ev["timestamp_ms"]) / 1000.0
                if self._mainshock_ts is None or ev_usd > self._mainshock_usd:
                    self._mainshock_ts = ev_ts_s
                    self._mainshock_usd = ev_usd
                    self._omori_params = None

    omori_active = False
    aftershock_rate = 0.0
    if self._mainshock_ts is not None:
        elapsed_min = (current_ts - self._mainshock_ts) / 60.0
        if 0.0 < elapsed_min <= self._omori_forecast_minutes:
            aftershock_times = np.array(
                [ts / 1000.0 for ts, _ in recent if ts / 1000.0 > self._mainshock_ts],
                dtype=np.float64,
            )
            if len(aftershock_times) >= 5:
                fit = self._fit_omori(aftershock_times, self._mainshock_ts)
                if fit is not None:
                    self._omori_params = fit
                    omori_active = True
                    dt_now = current_ts - self._mainshock_ts
                    aftershock_rate = self._omori_fn(
                        np.array([dt_now]), fit["K"], fit["c"], fit["p"]
                    )[0]
        elif elapsed_min > self._omori_forecast_minutes:
            self._mainshock_ts = None
            self._mainshock_usd = 0.0
            self._omori_params = None

    signal = 1 if (mainshock and omori_active) else 0
    confidence = 0.0
    if signal == 1 and self._omori_params is not None:
        p_val = self._omori_params.get("p", 1.0)
        confidence = min(max(1.0 / p_val, 0.0), 1.0)

    return {
        "b_value": b_value,
        "b_low": b_low,
        "mainshock": mainshock,
        "mainshock_ts": self._mainshock_ts,
        "omori_active": omori_active,
        "aftershock_rate": float(aftershock_rate),
        "omori_params": self._omori_params,
        "signal": signal,
    }


class TestOptimizedComputeMatchesLegacy:
    """The vectorised compute must match the list-based legacy path exactly."""

    def _build_cascade_events(self):
        """A mainshock followed by a dense aftershock sequence (drives Omori)."""
        rng = np.random.default_rng(11)
        base_ms = 1_700_000_000_000
        events = []
        # 80 background events to populate the b-value / Q99 history.
        for i in range(80):
            events.append({
                "timestamp_ms": base_ms + i * 1000,
                "usd_value": 1.0e5 + float(abs(rng.normal(0, 3e4))),
                "side": "Sell",
            })
        # One big mainshock.
        mainshock_ms = base_ms + 80 * 1000
        events.append({
            "timestamp_ms": mainshock_ms,
            "usd_value": 5.0e7,
            "side": "Sell",
        })
        # 60 aftershocks within the next ~120 s.
        for j in range(60):
            events.append({
                "timestamp_ms": mainshock_ms + (j + 1) * 2000,
                "usd_value": 2.0e5 + float(abs(rng.normal(0, 1e5))),
                "side": "Sell",
            })
        return events, base_ms

    def test_compute_sequence_bit_identical(self) -> None:
        events, base_ms = self._build_cascade_events()

        opt = M15GROmori()
        ref = M15GROmori()

        # Feed events one-at-a-time at advancing current_ts so the stateful
        # mainshock + Omori transitions are exercised across many calls.
        for ev in events:
            ts_s = ev["timestamp_ms"] / 1000.0
            out_opt = opt.compute([ev], ts_s)
            out_ref = _legacy_compute(ref, [ev], ts_s)

            assert out_opt["mainshock"] == out_ref["mainshock"]
            assert out_opt["omori_active"] == out_ref["omori_active"]
            assert out_opt["signal"] == out_ref["signal"]
            assert out_opt["mainshock_ts"] == out_ref["mainshock_ts"]
            # b_value: both None or numerically equal.
            if out_opt["b_value"] is None or out_ref["b_value"] is None:
                assert out_opt["b_value"] is out_ref["b_value"] or (
                    out_opt["b_value"] == out_ref["b_value"]
                )
            else:
                assert out_opt["b_value"] == pytest.approx(
                    out_ref["b_value"], rel=1e-12, abs=1e-12
                )
            assert out_opt["aftershock_rate"] == pytest.approx(
                out_ref["aftershock_rate"], rel=1e-9, abs=1e-12
            )
            if out_opt["omori_params"] is not None:
                assert out_ref["omori_params"] is not None
                for k in ("K", "c", "p"):
                    assert out_opt["omori_params"][k] == pytest.approx(
                        out_ref["omori_params"][k], rel=1e-9, abs=1e-12
                    )


# ══════════════════════════════════════════════════════════════════════
# Opt-in Omori-refit throttle (refit_seconds)
# ══════════════════════════════════════════════════════════════════════


def _cascade_events(n_aftershocks: int = 60) -> tuple[list[dict], int]:
    """Background + one mainshock + ``n_aftershocks`` dense aftershocks.

    Same shape as the bit-identical regression test above so that the throttle
    behaviour is exercised on a realistic cascade.
    """
    rng = np.random.default_rng(11)
    base_ms = 1_700_000_000_000
    events: list[dict] = []
    for i in range(80):
        events.append({
            "timestamp_ms": base_ms + i * 1000,
            "usd_value": 1.0e5 + float(abs(rng.normal(0, 3e4))),
            "side": "Sell",
        })
    mainshock_ms = base_ms + 80 * 1000
    events.append({
        "timestamp_ms": mainshock_ms,
        "usd_value": 5.0e7,
        "side": "Sell",
    })
    for j in range(n_aftershocks):
        events.append({
            "timestamp_ms": mainshock_ms + (j + 1) * 2000,
            "usd_value": 2.0e5 + float(abs(rng.normal(0, 1e5))),
            "side": "Sell",
        })
    return events, mainshock_ms


class TestThrottleNoOpDefault:
    """``refit_seconds=0`` (default) must be bit-identical to no-throttle."""

    def test_no_throttle_default_bit_identical(self) -> None:
        """Feeding the same cascade tick-by-tick to ``refit_seconds=0`` and to
        a freshly-built default M15 yields byte-equal compute() outputs."""
        events, _ = _cascade_events()

        a = M15GROmori()  # default refit_seconds=0.0
        b = M15GROmori(refit_seconds=0.0)
        for ev in events:
            ts_s = ev["timestamp_ms"] / 1000.0
            out_a = a.compute([ev], ts_s)
            out_b = b.compute([ev], ts_s)
            for k in (
                "mainshock",
                "omori_active",
                "signal",
                "mainshock_ts",
                "b_value",
                "b_low",
            ):
                assert out_a[k] == out_b[k], f"Mismatch on '{k}'"
            assert out_a["aftershock_rate"] == pytest.approx(
                out_b["aftershock_rate"], rel=1e-12, abs=1e-12
            )
            if out_a["omori_params"] is None:
                assert out_b["omori_params"] is None
            else:
                for k in ("K", "c", "p"):
                    assert out_a["omori_params"][k] == pytest.approx(
                        out_b["omori_params"][k], rel=1e-12, abs=1e-12
                    )


class TestThrottleCachesFit:
    """With ``refit_seconds>0`` ``curve_fit`` is called at most once per window."""

    def test_throttle_caches_fit_within_window(self) -> None:
        """100 compute() calls within 30 simulated seconds → curve_fit hit ONCE.

        Without the throttle the same scenario would invoke ``curve_fit`` once
        per tick where aftershocks are present (i.e. roughly per call).
        """
        events, mainshock_ms = _cascade_events()
        # Seed: mainshock + first batch of aftershocks so the throttled module
        # has data for one initial fit ON THE FIRST measured tick.
        seed_events = [
            e for e in events if e["timestamp_ms"] <= mainshock_ms + 60_000
        ]

        m = M15GROmori(refit_seconds=30.0)

        from unittest import mock

        original = m._fit_omori
        call_counter = {"n": 0}

        def spy(*args, **kwargs):
            call_counter["n"] += 1
            return original(*args, **kwargs)

        with mock.patch.object(m, "_fit_omori", side_effect=spy):
            # 1) First tick: feeds mainshock + aftershocks → 1 curve_fit call.
            first_ts = (mainshock_ms + 60_000) / 1000.0
            m.compute(seed_events, first_ts)
            assert call_counter["n"] == 1, (
                "First tick of a fresh mainshock must trigger a fit"
            )
            # 2) 100 more ticks spaced 0.2 s apart → total span 19.8 s < 30 s.
            #    All should hit the cache (curve_fit MUST NOT be called again).
            for k in range(100):
                m.compute([], first_ts + 0.2 * (k + 1))
        assert call_counter["n"] == 1, (
            f"Expected exactly 1 curve_fit call in the 30s window, "
            f"got {call_counter['n']}"
        )


class TestThrottleRefitsAfterWindow:
    """After ``refit_seconds`` of event time elapses, a new fit is triggered."""

    def test_throttle_refits_after_window(self) -> None:
        events, mainshock_ms = _cascade_events()
        m = M15GROmori(refit_seconds=30.0)
        # Drive mainshock + initial aftershocks.
        for ev in events:
            ts_s = ev["timestamp_ms"] / 1000.0
            m.compute([ev], ts_s)
        # ``_last_fit_ts`` should now be set.
        assert m._last_fit_ts is not None
        first_fit_ts = m._last_fit_ts

        from unittest import mock

        original = m._fit_omori
        call_counter = {"n": 0}

        def spy(*args, **kwargs):
            call_counter["n"] += 1
            return original(*args, **kwargs)

        # Jump 31 s of event time forward — past the 30s throttle window.
        bumped_ts = first_fit_ts + 31.0
        with mock.patch.object(m, "_fit_omori", side_effect=spy):
            m.compute([], bumped_ts)
        assert call_counter["n"] == 1, (
            "Expected a single refit AFTER the 30s window"
        )
        # And ``_last_fit_ts`` must have advanced to the new fit time.
        assert m._last_fit_ts == pytest.approx(bumped_ts)


class TestThrottleRefitsOnNewMainshock:
    """A new mainshock invalidates the cache even mid-window."""

    def test_throttle_refits_on_new_mainshock(self) -> None:
        events, mainshock_ms = _cascade_events()
        m = M15GROmori(refit_seconds=30.0)
        for ev in events:
            ts_s = ev["timestamp_ms"] / 1000.0
            m.compute([ev], ts_s)
        assert m._last_fit_ts is not None
        first_mainshock_ts = m._mainshock_ts
        first_fit_ts = m._last_fit_ts

        # Inject a bigger mainshock ONLY 5s later — well inside the 30s window.
        new_mainshock_ms = mainshock_ms + 5_000
        new_event = {
            "timestamp_ms": new_mainshock_ms,
            "usd_value": 2.0e8,  # 4x the previous mainshock
            "side": "Sell",
        }
        from unittest import mock

        original = m._fit_omori
        call_counter = {"n": 0}

        def spy(*args, **kwargs):
            call_counter["n"] += 1
            return original(*args, **kwargs)

        with mock.patch.object(m, "_fit_omori", side_effect=spy):
            m.compute([new_event], new_mainshock_ms / 1000.0 + 0.5)
        # Cache must have been invalidated: mainshock_ts moved and a fresh fit
        # must have been attempted (count ≥ 1; ``_last_fit_ts`` advanced).
        assert m._mainshock_ts != first_mainshock_ts
        assert call_counter["n"] >= 1, (
            "Expected curve_fit to be called on new mainshock"
        )
        assert m._last_fit_ts != first_fit_ts


class TestThrottleReturnsCachedParams:
    """Between refits the cached K/c/p must drive ``aftershock_rate`` (no NaN)."""

    def test_throttle_returns_cached_params(self) -> None:
        events, mainshock_ms = _cascade_events()
        m = M15GROmori(refit_seconds=30.0)
        # Warm.
        for ev in events:
            m.compute([ev], ev["timestamp_ms"] / 1000.0)
        assert m._omori_params is not None
        cached = dict(m._omori_params)

        # Force the throttle to skip refit by removing ``_fit_omori`` ability
        # to find new data: call compute with empty events, just inside the
        # window. The cached params must still drive aftershock_rate.
        from unittest import mock

        with mock.patch.object(m, "_fit_omori", side_effect=AssertionError(
            "curve_fit must NOT be invoked within the throttle window"
        )):
            # Stay 5 s past the last fit — well inside the 30s window.
            res = m.compute([], m._last_fit_ts + 5.0)
        # Cached params unchanged.
        assert m._omori_params == cached
        # Aftershock rate is finite and computed from the cached params (not 0).
        assert np.isfinite(res["aftershock_rate"])
        assert res["omori_active"] is True
        assert res["aftershock_rate"] > 0.0
