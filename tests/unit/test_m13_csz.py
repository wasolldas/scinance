"""
Tests fuer M13 -- Cross-Sectional Ergodicity-Reversion Z-Score.

Testet:
- Uniform Returns -> z = 0
- Extreme Symbol Detection
- Mean-Reversion-Richtung
- Kein Signal bei normaler Streuung
- Single Symbol (kein Crash)
- Insufficient History
- Sigma-Zero-Schutz
- Reset
"""

from __future__ import annotations

import pytest

from bybit_edge._legacy_v1.layers.l3_regime.m13_cross_sectional_z import (
    M13CrossSectionalZ,
    _MIN_HISTORY,
)


class TestM13CrossSectionalZ:
    """Tests fuer das M13CrossSectionalZ Modul."""

    def test_uniform_returns_zero_z(self) -> None:
        """Alle Symbole mit identischen Returns -> z = 0 fuer alle."""
        mod = M13CrossSectionalZ(window=20)

        # Fuettere genug identische Returns
        for _ in range(_MIN_HISTORY + 5):
            result = mod.compute(
                {"BTCUSDT": 0.001, "ETHUSDT": 0.001, "SOLUSDT": 0.001},
                current_ts=1000.0,
            )

        # Alle Z-Scores sollten 0 sein (sigma_cross ~ 0 -> Division-by-Zero-Schutz)
        for z in result["z_scores"].values():
            assert z == pytest.approx(0.0, abs=1e-6)
        assert result["signal"] == 0

    def test_extreme_symbol_detected(self) -> None:
        """Ein Symbol mit stark abweichendem Return -> |z| > 2.5."""
        mod = M13CrossSectionalZ(window=20)

        # 10 Symbole: BTC stark positiv, Rest nahe Null mit leichter Varianz
        returns = {
            "BTCUSDT": 0.10,
            "ETHUSDT": -0.005,
            "SOLUSDT": -0.003,
            "BNBUSDT": 0.001,
            "XRPUSDT": -0.002,
            "DOGEUSDT": 0.002,
            "AVAXUSDT": -0.001,
            "ADAUSDT": 0.003,
            "LINKUSDT": -0.004,
            "MATICUSDT": 0.001,
        }

        for _ in range(_MIN_HISTORY + 5):
            mod.compute(returns, current_ts=1000.0)

        result = mod.compute(returns, current_ts=1000.0)

        assert result["signal"] == 1
        assert len(result["extreme_symbols"]) >= 1

        # BTC sollte extremes Symbol sein
        extreme_syms = [e["symbol"] for e in result["extreme_symbols"]]
        assert "BTCUSDT" in extreme_syms

    def test_direction_mean_reversion(self) -> None:
        """Positives z -> Signal gegen z: direction = -1 (short)."""
        mod = M13CrossSectionalZ(window=20)

        # 10 Symbole: BTC extrem positiv -> hoher Z -> Mean-Reversion short
        returns = {
            "BTCUSDT": 0.10,
            "ETHUSDT": -0.005,
            "SOLUSDT": -0.003,
            "BNBUSDT": 0.001,
            "XRPUSDT": -0.002,
            "DOGEUSDT": 0.002,
            "AVAXUSDT": -0.001,
            "ADAUSDT": 0.003,
            "LINKUSDT": -0.004,
            "MATICUSDT": 0.001,
        }

        for _ in range(_MIN_HISTORY + 5):
            mod.compute(returns, current_ts=1000.0)

        result = mod.compute(returns, current_ts=1000.0)

        # BTC hat positives z -> Reversion short
        btc_entry = [e for e in result["extreme_symbols"] if e["symbol"] == "BTCUSDT"]
        assert len(btc_entry) == 1
        assert btc_entry[0]["z"] > 0
        assert btc_entry[0]["direction"] == -1  # Mean reversion: short

    def test_no_signal_normal_spread(self) -> None:
        """Moderate Unterschiede -> kein extremes Symbol."""
        mod = M13CrossSectionalZ(window=20)

        for _ in range(_MIN_HISTORY + 5):
            result = mod.compute(
                {
                    "BTCUSDT": 0.001,
                    "ETHUSDT": 0.0008,
                    "SOLUSDT": 0.0012,
                    "BNBUSDT": 0.0009,
                    "XRPUSDT": 0.0011,
                },
                current_ts=1000.0,
            )

        assert result["signal"] == 0
        assert len(result["extreme_symbols"]) == 0

    def test_single_symbol_no_crash(self) -> None:
        """Nur ein Symbol -> kein Crash, signal = 0 (braucht min 2)."""
        mod = M13CrossSectionalZ(window=20)

        for _ in range(_MIN_HISTORY + 5):
            result = mod.compute(
                {"BTCUSDT": 0.001},
                current_ts=1000.0,
            )

        assert result["signal"] == 0
        assert result["z_scores"] == {}

    def test_insufficient_history(self) -> None:
        """Zu wenig Datenpunkte -> signal = 0."""
        mod = M13CrossSectionalZ(window=20)

        # Nur 1 Datenpunkt (weniger als _MIN_HISTORY)
        result = mod.compute(
            {"BTCUSDT": 0.001, "ETHUSDT": 0.002},
            current_ts=1000.0,
        )

        assert result["signal"] == 0
        assert result["z_scores"] == {}
        assert result["method_id"] == "M13"

    def test_sigma_zero_protection(self) -> None:
        """Identische Returns -> sigma_cross = 0 -> kein Crash, z = 0."""
        mod = M13CrossSectionalZ(window=20)

        for _ in range(_MIN_HISTORY + 5):
            result = mod.compute(
                {"BTCUSDT": 0.001, "ETHUSDT": 0.001, "SOLUSDT": 0.001},
                current_ts=1000.0,
            )

        # sigma_cross ~ 0, Z-Scores sollten alle 0 sein
        for z in result["z_scores"].values():
            assert z == pytest.approx(0.0, abs=1e-6)
        assert result["signal"] == 0
        assert result["extreme_symbols"] == []

    def test_reset(self) -> None:
        """Reset setzt History zurueck."""
        mod = M13CrossSectionalZ(window=20)

        for _ in range(50):
            mod.compute(
                {"BTCUSDT": 0.001, "ETHUSDT": -0.001},
                current_ts=1000.0,
            )

        mod.reset()

        assert len(mod._returns_history) == 0

        # Nach Reset: keine Daten -> signal = 0
        result = mod.compute(
            {"BTCUSDT": 0.001, "ETHUSDT": -0.001},
            current_ts=1000.0,
        )
        assert result["signal"] == 0
        assert result["z_scores"] == {}
