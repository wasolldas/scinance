"""
Tests für M22 — Funding-Rate-Clamp Pressure-Release.

Testet:
- Analytisch berechnete Pressure-Werte
- Signal-Erzeugung innerhalb/außerhalb des Settlement-Windows
- Division-by-Zero-Sicherheit bei sigma == 0
- Signal-Richtung (PRD 7.3/M22: positive Pressure/negative Premium → Long,
  negative Pressure/positive Premium → Short)
- Reset löscht History
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge.config import (
    FUNDING_CLAMP_LOWER,
    FUNDING_CLAMP_UPPER,
    FUNDING_INTEREST_RATE,
    PRESSURE_ENTRY_WINDOW_MINUTES,
    PRESSURE_ZSCORE_THRESHOLD,
)
from bybit_edge._legacy_v1.layers.l5_risk.m22_funding_pressure import (
    M22FundingPressure,
    _MIN_SAMPLES_FOR_SIGMA,
)


def _make_ticker(premium_index: float) -> dict:
    """Erzeugt minimales ticker_data dict."""
    return {
        "premium_index": premium_index,
        "funding_rate": 0.0001,
        "mark_price": 100_000.0,
        "index_price": 99_950.0,
        "last_price": 100_010.0,
    }


def _make_jittered_ticker(rng: np.random.Generator) -> dict:
    """Ticker whose pressure varies slightly around a small non-zero value.

    Used to build "quiet phase" history with a *genuine* non-degenerate
    sigma. A perfectly constant premium_index yields a perfectly constant
    pressure, whose std is either exactly 0.0 (if pressure lands exactly on
    0) or a meaningless ~1e-20 floating-point-summation artifact (if it
    doesn't) — neither is a real reference distribution. Offsetting the
    premium just past the clamp boundary by a small jittered amount
    produces a small but reliably non-zero, non-constant pressure series.
    """
    jitter = float(rng.uniform(0.0, 0.0002))
    premium_index = FUNDING_INTEREST_RATE - (FUNDING_CLAMP_UPPER + 0.0003 + jitter)
    return _make_ticker(premium_index)


class TestPressureCalculation:
    """Test analytisch berechnete Pressure-Werte."""

    def test_pressure_calculation_known_values(self) -> None:
        """Wenn Premium-Index weit vom Interest abweicht, entsteht Pressure."""
        mod = M22FundingPressure()

        # I_t = 0.0003 (FUNDING_INTEREST_RATE)
        # P_t = 0.002 (weit über I)
        # diff = I - P = 0.0003 - 0.002 = -0.0017
        # clamp(-0.0017, -0.0005, +0.0005) = -0.0005
        # pressure = diff - clamped = -0.0017 - (-0.0005) = -0.0012
        P_t = 0.002
        result = mod.compute(_make_ticker(P_t), seconds_to_settlement=900.0)

        expected_diff = FUNDING_INTEREST_RATE - P_t  # -0.0017
        expected_clamped = float(
            np.clip(expected_diff, FUNDING_CLAMP_LOWER, FUNDING_CLAMP_UPPER)
        )
        expected_pressure = expected_diff - expected_clamped

        assert result["pressure"] == pytest.approx(expected_pressure, abs=1e-12)
        assert result["method_id"] == "M22"

    def test_no_pressure_within_clamp_bounds(self) -> None:
        """Wenn diff innerhalb der Clamp-Grenzen liegt, ist Pressure == 0."""
        mod = M22FundingPressure()

        # P_t = I_t = 0.0003 → diff = 0 → clamp(0) = 0 → pressure = 0
        result = mod.compute(
            _make_ticker(FUNDING_INTEREST_RATE),
            seconds_to_settlement=900.0,
        )
        assert result["pressure"] == pytest.approx(0.0, abs=1e-12)

    def test_funding_rate_calculation(self) -> None:
        """F_t = P_t + clamp(I_t - P_t, lower, upper)."""
        mod = M22FundingPressure()
        P_t = 0.002
        result = mod.compute(_make_ticker(P_t), seconds_to_settlement=900.0)

        diff = FUNDING_INTEREST_RATE - P_t
        clamped = float(np.clip(diff, FUNDING_CLAMP_LOWER, FUNDING_CLAMP_UPPER))
        expected_F_t = P_t + clamped

        assert result["funding_rate"] == pytest.approx(expected_F_t, abs=1e-12)


class TestSignalInWindow:
    """Test Signal-Erzeugung innerhalb des Settlement-Windows."""

    def test_signal_in_window(self) -> None:
        """30 min vor Settlement mit extremem Pressure → Signal != 0."""
        mod = M22FundingPressure()
        rng = np.random.default_rng(1)

        # Erst History füllen mit kleinen, leicht schwankenden Pressure-Werten
        # (echte, kleine Sigma statt exakt-konstant/0).
        for _ in range(_MIN_SAMPLES_FOR_SIGMA + 50):
            mod.compute(
                _make_jittered_ticker(rng),
                seconds_to_settlement=3600.0,
            )

        # Jetzt extremen Pressure erzeugen (P_t weit weg von I_t)
        result = mod.compute(
            _make_ticker(0.01),  # sehr großer Premium
            seconds_to_settlement=900.0,  # 15 min = innerhalb 30-min-Window
        )

        assert result["signal"] != 0
        assert result["in_window"] is True

    def test_signal_outside_window(self) -> None:
        """60 min vor Settlement → Signal == 0 (außerhalb Window)."""
        mod = M22FundingPressure()
        rng = np.random.default_rng(2)

        # History füllen
        for _ in range(_MIN_SAMPLES_FOR_SIGMA + 50):
            mod.compute(
                _make_jittered_ticker(rng),
                seconds_to_settlement=7200.0,
            )

        result = mod.compute(
            _make_ticker(0.01),  # extremer Premium
            seconds_to_settlement=3600.0,  # 60 min = AUSSERHALB 30-min-Window
        )

        assert result["signal"] == 0
        assert result["in_window"] is False


class TestSigmaZeroSafety:
    """Test Division-by-Zero-Sicherheit."""

    def test_sigma_zero_no_crash(self) -> None:
        """Leere History → Signal == 0, kein Crash."""
        mod = M22FundingPressure()

        # Erster Aufruf: keine History, sigma == 0
        result = mod.compute(
            _make_ticker(0.01),
            seconds_to_settlement=900.0,
        )

        assert result["signal"] == 0
        assert result["pressure_zscore"] == 0.0
        assert result["method_id"] == "M22"

    def test_few_samples_no_signal(self) -> None:
        """Weniger als MIN_SAMPLES Einträge → kein Signal möglich."""
        mod = M22FundingPressure()

        for i in range(_MIN_SAMPLES_FOR_SIGMA - 1):
            result = mod.compute(
                _make_ticker(0.01),
                seconds_to_settlement=900.0,
            )

        # Sigma ist noch 0 → kein Signal
        assert result["signal"] == 0


class TestSignalDirection:
    """Test korrekte Signal-Richtung."""

    def _build_module_with_history(self) -> M22FundingPressure:
        """Baut ein Modul mit genug History (pressure klein, sigma klein > 0)."""
        mod = M22FundingPressure()
        rng = np.random.default_rng(3)
        for _ in range(_MIN_SAMPLES_FOR_SIGMA + 50):
            mod.compute(
                _make_jittered_ticker(rng),
                seconds_to_settlement=3600.0,
            )
        return mod

    def test_negative_pressure_gives_short(self) -> None:
        """Negativer Pressure (positive Premium, P >> I) → Short-Signal (-1).

        Korrigiert gegen PRD 7.3/M22 (S.682): positive Premium (Perp
        überbewertet, Longs zu wenig gezahlt) → Short-Reversion. Bei
        positiver Premium ist diff=(I-P)<0 → Pressure<0. Der frühere Test
        zementierte die ökonomisch invertierte Richtung (negative Pressure
        → Long).
        """
        mod = self._build_module_with_history()

        # P_t = 0.01 (positive Premium) → diff = I - P < 0 → pressure < 0
        result = mod.compute(
            _make_ticker(0.01),
            seconds_to_settlement=900.0,
        )

        assert result["pressure"] < 0
        if result["signal"] != 0:
            assert result["signal"] == -1  # Short

    def test_positive_pressure_gives_long(self) -> None:
        """Positiver Pressure (negative Premium, P << I) → Long-Signal (+1).

        Korrigiert gegen PRD 7.3/M22 (S.682): "aufgestaute Negative-Premium-
        Pressure ... Reversion kommt" → Long. Bei negativer Premium ist
        diff=(I-P)>0 → Pressure>0.
        """
        mod = self._build_module_with_history()

        # P_t = -0.01 (negative Premium) → diff = I - P = 0.0103
        # clamp(0.0103, -0.0005, 0.0005) = 0.0005
        # pressure = 0.0103 - 0.0005 = 0.0098 > 0
        result = mod.compute(
            _make_ticker(-0.01),
            seconds_to_settlement=900.0,
        )

        assert result["pressure"] > 0
        if result["signal"] != 0:
            assert result["signal"] == 1  # Long


class TestReset:
    """Test reset() Funktionalität."""

    def test_reset_clears_history(self) -> None:
        """Nach reset() ist die History leer und sigma == 0."""
        mod = M22FundingPressure()
        rng = np.random.default_rng(4)

        # Fülle History mit leicht schwankenden (nicht exakt konstanten)
        # Pressure-Werten, damit sigma auf einer echten Streuung beruht.
        for _ in range(_MIN_SAMPLES_FOR_SIGMA + 50):
            mod.compute(
                _make_jittered_ticker(rng),
                seconds_to_settlement=900.0,
            )

        assert len(mod._pressure_history) > 0
        assert mod._24h_sigma > 0

        mod.reset()

        assert len(mod._pressure_history) == 0
        assert mod._24h_sigma == 0.0

    def test_reset_then_compute_no_crash(self) -> None:
        """Nach reset() kann compute() ohne Crash aufgerufen werden."""
        mod = M22FundingPressure()
        mod.reset()
        result = mod.compute(_make_ticker(0.001), seconds_to_settlement=900.0)
        assert result["signal"] == 0


class TestValidate:
    """Test validate() Methode."""

    def test_validate_returns_true(self) -> None:
        """Standard-Konfiguration ist valide."""
        mod = M22FundingPressure()
        assert mod.validate() is True


class TestSigmaExcludesCurrentTickAndUsesTimeWindow:
    """Regression: `_24h_sigma` must not include the current tick in its own
    reference distribution, and its window must be time-based rather than a
    fixed sample count (CRITICAL_REVIEW_2 M22 finding).
    """

    def test_zscore_uses_prior_history_not_current_tick(self) -> None:
        """The z-score of the CURRENT tick must be computed from sigma over
        only the PRIOR history, not a sigma that already includes this
        tick's own (possibly extreme) pressure value."""
        mod = M22FundingPressure()

        # Deterministic, known pressures: push diff just past the upper
        # clamp by a small increasing amount so pressure = k * 1e-5
        # exactly (clamped term is constant once diff exceeds the bound).
        known_pressures = []
        for k in range(1, _MIN_SAMPLES_FOR_SIGMA + 1):
            diff = FUNDING_CLAMP_UPPER + k * 1e-5
            premium_index = FUNDING_INTEREST_RATE - diff
            mod.compute(_make_ticker(premium_index), seconds_to_settlement=3600.0)
            known_pressures.append(k * 1e-5)

        expected_sigma_prior = float(np.std(known_pressures))
        assert expected_sigma_prior > 0

        # One more, distinctly different pressure value as the "current" tick.
        current_diff = FUNDING_CLAMP_UPPER + 500 * 1e-5
        current_premium = FUNDING_INTEREST_RATE - current_diff
        result = mod.compute(_make_ticker(current_premium), seconds_to_settlement=3600.0)
        current_pressure = 500 * 1e-5

        expected_zscore = current_pressure / expected_sigma_prior
        assert result["pressure_zscore"] == pytest.approx(expected_zscore, rel=1e-9), (
            "pressure_zscore should be computed from sigma over the prior "
            "history only, excluding the current tick's own pressure"
        )

    def test_history_stores_timestamped_samples(self) -> None:
        """The pressure history must carry timestamps (for time-based
        pruning), not bare floats."""
        mod = M22FundingPressure()
        mod.compute(_make_ticker(0.001), seconds_to_settlement=900.0)
        assert len(mod._pressure_history) == 1
        entry = mod._pressure_history[0]
        assert isinstance(entry, tuple)
        assert len(entry) == 2

    def test_stale_samples_pruned_by_wall_clock_time(self) -> None:
        """Samples older than the 24h window must be pruned based on real
        elapsed time, not retained purely because a sample-count cap
        wasn't hit yet."""
        mod = M22FundingPressure()
        mod.compute(_make_ticker(0.001), seconds_to_settlement=900.0)
        assert len(mod._pressure_history) == 1

        # Simulate the one stored sample being > 24h old.
        stale_ts, stale_pressure = mod._pressure_history[0]
        mod._pressure_history[0] = (stale_ts - 25 * 60 * 60, stale_pressure)

        mod.compute(_make_ticker(0.001), seconds_to_settlement=900.0)

        # The stale entry should have been pruned; only the fresh one (from
        # this call) remains.
        assert len(mod._pressure_history) == 1
        remaining_ts, _ = mod._pressure_history[0]
        assert remaining_ts > stale_ts

    def test_compute_uses_ticker_data_ts_not_wall_clock(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """compute() must derive "now" from ticker_data["ts"] when present,
        not from real wall-clock time.time() — this module also runs inside
        ReplayBacktester, which feeds ticks at CPU speed while
        ticker_data["ts"] carries the SIMULATED/event time. If compute()
        used time.time() here, the 24h pruning window would be driven by
        backtest-loop processing speed instead of simulated elapsed market
        time, silently defeating the whole time-based-window fix.
        time.time() is monkeypatched to a constant so any use of it (instead
        of ticker_data["ts"]) would make this assertion fail."""
        monkeypatch.setattr(
            "bybit_edge._legacy_v1.layers.l5_risk.m22_funding_pressure.time.time",
            lambda: 999_999.0,
        )
        mod = M22FundingPressure()

        ticker = _make_ticker(0.001)
        mod.compute(ticker | {"ts": 10_000.0}, seconds_to_settlement=900.0)
        assert mod._pressure_history[0][0] == pytest.approx(10_000.0)

        mod.compute(ticker | {"ts": 10_000.0 + 25 * 60 * 60}, seconds_to_settlement=900.0)
        # The first sample (25h earlier in SIMULATED time) must be pruned
        # even though wall-clock time.time() never moved.
        assert len(mod._pressure_history) == 1
        assert mod._pressure_history[0][0] == pytest.approx(10_000.0 + 25 * 60 * 60)


class TestReturnFormat:
    """Test dass alle Required-Keys vorhanden sind."""

    def test_all_keys_present(self) -> None:
        mod = M22FundingPressure()
        result = mod.compute(_make_ticker(0.001), seconds_to_settlement=900.0)

        required_keys = {
            "signal", "pressure", "pressure_zscore", "funding_rate",
            "seconds_to_settlement", "in_window", "method_id",
            "confidence", "ts",
        }
        assert required_keys.issubset(result.keys())

    def test_signal_in_valid_range(self) -> None:
        mod = M22FundingPressure()
        result = mod.compute(_make_ticker(0.001), seconds_to_settlement=900.0)
        assert result["signal"] in {-1, 0, 1}
