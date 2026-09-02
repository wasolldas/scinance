"""
Tests für M25 — Kyle's Lambda (Adverse Selection).

Testet:
- Positive Market-Impact (Käufe treiben Preis hoch → λ > 0)
- Random Walk → λ ≈ 0
- Bekannte Regression → λ analytisch korrekt
- Toxic Flow bei extremem λ
- Kein Toxic Flow bei normalem λ
- Signal = -1 bei Toxic Flow
- Zu wenige Trades → neutrales Signal
- Zero Volume Protection
- Reset
- Return-Keys
"""

from __future__ import annotations

import numpy as np
import pytest

from bybit_edge._legacy_v1.layers.l5_risk.m25_kyle_lambda import M25KyleLambda


def _make_trades(
    n: int,
    base_price: float = 100_000.0,
    volume: float = 1.0,
    side: str = "Buy",
    price_increment: float = 0.0,
) -> list[dict]:
    """Erzeugt n synthetische Trades."""
    return [
        {
            "price": base_price + i * price_increment,
            "volume": volume,
            "side": side,
            "timestamp_ms": 1_000_000 + i * 100,
        }
        for i in range(n)
    ]


def _make_impact_trades(n: int = 50) -> list[dict]:
    """Buy-Trades die den Preis konsistent nach oben treiben → λ > 0."""
    trades = []
    price = 100_000.0
    for i in range(n):
        price += 1.0  # Preis steigt monoton
        trades.append({
            "price": price,
            "volume": 10.0,
            "side": "Buy",
            "timestamp_ms": 1_000_000 + i * 100,
        })
    return trades


def _make_random_trades(n: int = 100, seed: int = 42) -> list[dict]:
    """Random-Walk-Trades → λ ≈ 0."""
    rng = np.random.default_rng(seed)
    trades = []
    price = 100_000.0
    for i in range(n):
        price += rng.normal(0, 1)
        side = "Buy" if rng.random() > 0.5 else "Sell"
        trades.append({
            "price": price,
            "volume": rng.uniform(0.5, 2.0),
            "side": side,
            "timestamp_ms": 1_000_000 + i * 100,
        })
    return trades


class TestLambdaPositiveMarketImpact:
    """Käufe treiben Preis hoch → λ > 0."""

    def test_lambda_positive_market_impact(self) -> None:
        mod = M25KyleLambda()
        trades = _make_impact_trades(50)
        result = mod.compute(trades)

        assert result["kyle_lambda"] > 0.0


class TestLambdaZeroRandomWalk:
    """Random Trades → λ ≈ 0."""

    def test_lambda_zero_random_walk(self) -> None:
        mod = M25KyleLambda()
        trades = _make_random_trades(100)
        result = mod.compute(trades)

        # λ sollte nahe 0 sein (nicht exakt, da finites Sample)
        assert abs(result["kyle_lambda"]) < 1.0


class TestLambdaKnownRegression:
    """Analytisch bekanntes λ: Δp = λ * signed_volume → Recovery."""

    def test_lambda_known_regression(self) -> None:
        mod = M25KyleLambda()

        # Konstruiere Trades mit bekanntem λ = 0.5
        lambda_true = 0.5
        n = 50
        rng = np.random.default_rng(123)
        trades = []
        price = 100_000.0
        for i in range(n):
            volume = rng.uniform(1.0, 10.0)
            side = "Buy" if rng.random() > 0.5 else "Sell"
            sign = 1.0 if side == "Buy" else -1.0
            # Preis folgt exakt: Δp = λ * volume * sign
            delta_p = lambda_true * volume * sign
            price += delta_p
            trades.append({
                "price": price,
                "volume": volume,
                "side": side,
                "timestamp_ms": 1_000_000 + i * 100,
            })

        result = mod.compute(trades)

        # λ sollte nahe 0.5 sein
        assert abs(result["kyle_lambda"] - lambda_true) < 0.1


class TestToxicFlowExtremeLambda:
    """Extremes λ (>> Q95) → toxic_flow = True."""

    def test_toxic_flow_extreme_lambda(self) -> None:
        mod = M25KyleLambda()

        # Phase 1: Baue normale λ-Historie auf
        normal_trades = _make_random_trades(50, seed=10)
        for _ in range(100):
            mod.compute(normal_trades)
            # Refresh trades-Buffer mit neuen Random-Trades
            mod._trades.clear()

        # Phase 2: Extremer Impact → sehr hohes λ
        extreme_trades = _make_impact_trades(50)
        result = mod.compute(extreme_trades)

        # Bei extrem hohem λ nach normalem Regime → toxic_flow
        assert result["toxic_flow"] is True
        assert result["signal"] == -1


class TestNoToxicFlowNormal:
    """Normales λ → toxic_flow = False."""

    def test_no_toxic_flow_normal(self) -> None:
        mod = M25KyleLambda()

        # Konsistent gleiche Art von Trades → λ stabil → kein Toxic
        for i in range(20):
            trades = _make_random_trades(50, seed=i)
            result = mod.compute(trades)
            mod._trades.clear()

        # Am Ende sollte kein Toxic Flow sein (alle λ ähnlich)
        assert result["toxic_flow"] is False
        assert result["signal"] == 0


class TestSignalRiskOffOnToxic:
    """Toxic Flow → signal = -1."""

    def test_signal_risk_off_on_toxic(self) -> None:
        mod = M25KyleLambda()

        # Baue niedrige λ-Historie auf
        for i in range(50):
            trades = _make_random_trades(30, seed=i + 100)
            mod.compute(trades)
            mod._trades.clear()

        # Jetzt extremer Impact
        extreme = _make_impact_trades(50)
        result = mod.compute(extreme)

        if result["toxic_flow"]:
            assert result["signal"] == -1


class TestInsufficientTrades:
    """Weniger als 10 Trades → signal = 0, confidence = 0."""

    def test_insufficient_trades(self) -> None:
        mod = M25KyleLambda()
        trades = _make_trades(5, price_increment=1.0)
        result = mod.compute(trades)

        assert result["signal"] == 0
        assert result["kyle_lambda"] == 0.0
        assert result["confidence"] == 0.0


class TestZeroVolumeProtection:
    """Trades mit Volume = 0 → kein Crash, λ = 0."""

    def test_zero_volume_protection(self) -> None:
        mod = M25KyleLambda()
        trades = _make_trades(20, volume=0.0, price_increment=1.0)
        result = mod.compute(trades)

        # Darf nicht crashen
        assert result["kyle_lambda"] == 0.0
        assert not np.isnan(result["kyle_lambda"])


class TestReset:
    """Reset löscht History und Trade-Buffer."""

    def test_reset(self) -> None:
        mod = M25KyleLambda()

        # Fülle State
        trades = _make_impact_trades(50)
        mod.compute(trades)

        assert len(mod._lambda_history) > 0
        assert len(mod._trades) > 0

        mod.reset()

        assert len(mod._lambda_history) == 0
        assert len(mod._trades) == 0


class TestReturnKeys:
    """Alle required Keys sind vorhanden und korrekt typisiert."""

    def test_return_keys(self) -> None:
        mod = M25KyleLambda()
        trades = _make_impact_trades(30)
        result = mod.compute(trades)

        required_keys = {
            "signal", "kyle_lambda", "lambda_q95", "toxic_flow",
            "method_id", "confidence", "ts",
        }
        assert required_keys.issubset(result.keys())
        assert result["method_id"] == "M25"
        assert result["signal"] in {-1, 0, 1}
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["toxic_flow"], bool)
        assert isinstance(result["kyle_lambda"], float)

    def test_return_keys_insufficient(self) -> None:
        mod = M25KyleLambda()
        result = mod.compute([{"price": 100.0, "volume": 1.0, "side": "Buy", "timestamp_ms": 1}])

        required_keys = {
            "signal", "kyle_lambda", "lambda_q95", "toxic_flow",
            "method_id", "confidence", "ts",
        }
        assert required_keys.issubset(result.keys())
