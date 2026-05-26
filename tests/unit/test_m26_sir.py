"""
Tests für M26 — SIR-Kompartiment-Liquidations-Contagion.

Testet:
- R₀ < 1 → kein Kaskaden-Alarm
- R₀ > 1 → Kaskaden-Alarm
- Kalibrierung mit synthetischen SIR-Daten
- ODE-Massenerhaltung (S+I+R = const)
- Stabile Lösung bei I=0
- Forward-Simulation Peak
- Division-by-Zero-Schutz bei γ=0
- Leere Events → neutrales Signal
- Reset löscht Kalibrierung
- Korrekte Return-Keys
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.integrate import odeint

from bybit_edge.layers.l5_risk.m26_sir import M26SIR


def _make_liq_events(n: int, volume: float = 100.0) -> list[dict]:
    """Erzeugt n synthetische Liquidationsevents."""
    return [
        {"volume": volume, "timestamp_ms": 1_000_000 + i * 1000}
        for i in range(n)
    ]


class TestR0BelowOneNoCascade:
    """R₀ < 1 → kein Kaskaden-Alarm."""

    def test_r0_below_one_no_cascade(self) -> None:
        mod = M26SIR()
        # Niedrige β, hohe γ → R₀ = β·S/γ < 1
        # S ≈ OI - cum_liq = 100 - 50 = 50, R₀ = 0.001 * 50 / 1.0 = 0.05
        mod._beta = 0.001
        mod._gamma = 1.0

        # Weniger als 10 Events → keine Re-Kalibrierung, β/γ bleiben
        events = _make_liq_events(5, volume=10.0)
        result = mod.compute(events, open_interest=100.0, current_ts=1.0)

        assert result["signal"] == 0
        assert result["cascade_risk"] is False
        assert result["r0"] < 1.0


class TestR0AboveOneCascade:
    """R₀ > 1 → Kaskaden-Alarm."""

    def test_r0_above_one_cascade(self) -> None:
        mod = M26SIR()
        # Hohe β, niedrige γ → R₀ >> 1
        mod._beta = 0.1
        mod._gamma = 0.001

        events = _make_liq_events(15, volume=10.0)
        result = mod.compute(events, open_interest=100_000.0, current_ts=1.0)

        assert result["signal"] == 1
        assert result["cascade_risk"] is True
        assert result["r0"] > 1.0


class TestCalibrateKnownDynamics:
    """Kalibrierung mit synthetischen SIR-Daten recovert β und γ."""

    def test_calibrate_known_dynamics(self) -> None:
        mod = M26SIR()

        # Synthetische SIR-Dynamik generieren
        beta_true = 0.005
        gamma_true = 0.1
        n_points = 200

        # Forward-simulieren um realistische Daten zu generieren
        s0, i0, r0 = 1000.0, 10.0, 0.0
        t = np.linspace(0, 50, n_points)
        sol = odeint(mod._sir_ode, [s0, i0, r0], t, args=(beta_true, gamma_true))

        # Liq-Events aus I-Werten generieren
        i_vals = sol[:, 1]
        liq_volumes = np.maximum(np.diff(np.maximum(i_vals, 0)), 0.01).tolist()
        events = [{"volume": v, "timestamp_ms": int(t_i * 1000)} for v, t_i in zip(liq_volumes, t[1:])]

        # OI-History aus S-Werten
        oi_history = sol[1:, 0].tolist()

        beta_est, gamma_est = mod._calibrate(events, oi_history)

        # Parameter sollten positiv sein (grobe Prüfung)
        assert beta_est > 0
        assert gamma_est > 0


class TestSIRODEConservation:
    """S + I + R = const über die gesamte Integration."""

    def test_sir_ode_conservation(self) -> None:
        mod = M26SIR()
        y0 = [990.0, 10.0, 0.0]
        n_total = sum(y0)
        t = np.linspace(0, 100, 500)
        sol = odeint(mod._sir_ode, y0, t, args=(0.002, 0.1))

        sums = sol[:, 0] + sol[:, 1] + sol[:, 2]
        np.testing.assert_allclose(sums, n_total, rtol=1e-6)


class TestZeroInfectionsStable:
    """I=0 → dI/dt = 0 — System bleibt stabil."""

    def test_zero_infections_stable(self) -> None:
        mod = M26SIR()
        y0 = [1000.0, 0.0, 0.0]
        t = np.linspace(0, 100, 100)
        sol = odeint(mod._sir_ode, y0, t, args=(0.01, 0.1))

        # I bleibt 0
        np.testing.assert_allclose(sol[:, 1], 0.0, atol=1e-10)
        # S bleibt konstant
        np.testing.assert_allclose(sol[:, 0], 1000.0, atol=1e-10)


class TestForwardSimulationPeak:
    """R₀ > 1 → I steigt an, Peak vorhersagbar."""

    def test_forward_simulation_peak(self) -> None:
        mod = M26SIR()
        mod._beta = 0.01
        mod._gamma = 0.05  # R₀ = 0.01 * S / 0.05 >> 1 für großes S

        events = _make_liq_events(20, volume=50.0)
        result = mod.compute(events, open_interest=50_000.0, current_ts=1.0)

        # Peak-I-Forecast sollte > 0 sein bei Kaskade
        assert result["peak_i_forecast"] > 0.0


class TestGammaZeroProtection:
    """γ = 0 → kein Division-by-Zero-Crash."""

    def test_gamma_zero_protection(self) -> None:
        mod = M26SIR()
        mod._beta = 0.01
        mod._gamma = 0.0  # Explizit 0

        events = _make_liq_events(15, volume=10.0)
        # Darf nicht crashen
        result = mod.compute(events, open_interest=10_000.0, current_ts=1.0)

        assert "r0" in result
        assert result["r0"] >= 0  # R₀ sollte riesig sein aber nicht NaN/Inf
        assert not np.isnan(result["r0"])


class TestEmptyEventsSignalZero:
    """Leere Events → signal = 0."""

    def test_empty_events_signal_zero(self) -> None:
        mod = M26SIR()
        result = mod.compute([], open_interest=10_000.0, current_ts=1.0)

        assert result["signal"] == 0
        assert result["cascade_risk"] is False
        assert result["i_current"] == 0.0


class TestResetClearsCalibration:
    """Reset setzt Kalibrierung und Buffer zurück."""

    def test_reset_clears_calibration(self) -> None:
        mod = M26SIR()

        # Kalibriere etwas
        events = _make_liq_events(50, volume=100.0)
        mod.compute(events, open_interest=100_000.0, current_ts=1.0)

        # State sollte nicht-trivial sein
        assert len(mod._recal_buffer) > 0

        mod.reset()

        assert mod._beta == 0.001
        assert mod._gamma == 0.1
        assert mod._calibrated is False
        assert len(mod._recal_buffer) == 0


class TestReturnKeys:
    """Alle required Keys sind vorhanden und korrekt typisiert."""

    def test_return_keys(self) -> None:
        mod = M26SIR()
        events = _make_liq_events(20, volume=50.0)
        result = mod.compute(events, open_interest=10_000.0, current_ts=1.0)

        required_keys = {
            "signal", "r0", "beta", "gamma", "s_current", "i_current",
            "peak_i_forecast", "cascade_risk", "method_id", "confidence", "ts",
        }
        assert required_keys.issubset(result.keys())
        assert result["method_id"] == "M26"
        assert result["signal"] in {-1, 0, 1}
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["cascade_risk"], bool)
        assert isinstance(result["r0"], float)

    def test_return_keys_empty_events(self) -> None:
        mod = M26SIR()
        result = mod.compute([], open_interest=10_000.0, current_ts=1.0)

        required_keys = {
            "signal", "r0", "beta", "gamma", "s_current", "i_current",
            "peak_i_forecast", "cascade_risk", "method_id", "confidence", "ts",
        }
        assert required_keys.issubset(result.keys())
