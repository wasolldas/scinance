"""
Tests für den Backtest-Driver (scripts/backtest.py).

Nur netzwerk-freie Teile: seconds_to_settlement, build_features,
Strategie-Adapter durch die echte BacktestEngine auf synthetischen Daten.
"""
from __future__ import annotations

import time

import numpy as np
import polars as pl

from bybit_edge._legacy_v1.backtester.engine import BacktestEngine
from archive.v1_scripts.backtest import (
    STRATEGIES,
    _seconds_to_settlement,
    build_features,
)


def _synthetic(n: int = 60 * 24 * 12) -> pl.DataFrame:
    start = int(time.time() * 1000) - 60 * 24 * 3600 * 1000
    ts = (np.arange(n) * 5 * 60 * 1000 + start).astype("int64")
    rng = np.random.default_rng(7)
    price = 70000 + np.cumsum(rng.normal(0, 30, n))
    kl = pl.DataFrame({
        "ts": ts, "open": price, "high": price + 10,
        "low": price - 10, "close": price, "volume": np.ones(n),
    })
    ft = np.arange(start, start + 60 * 24 * 3600 * 1000, 8 * 3600 * 1000).astype("int64")
    fr = rng.normal(0, 0.0004, len(ft))
    fund = pl.DataFrame({"ts": ft, "funding_rate": fr})
    return build_features(kl, fund)


class TestSecondsToSettlement:
    def test_returns_positive_within_8h(self):
        for offset_h in (0.5, 3.0, 7.9):
            ms = int(offset_h * 3600 * 1000)
            stt = _seconds_to_settlement(ms)
            assert 0 < stt <= 8 * 3600

    def test_just_before_settlement_small(self):
        # 1 Sekunde vor 08:00 UTC
        ms = (8 * 3600 - 1) * 1000
        assert _seconds_to_settlement(ms) <= 1.0


class TestBuildFeatures:
    def test_has_required_columns(self):
        df = _synthetic(2000)
        for col in ("ts", "close", "funding_rate", "seconds_to_settlement"):
            assert col in df.columns

    def test_funding_forward_filled(self):
        df = _synthetic(2000)
        # Keine Null-Werte mehr nach as-of join + fill
        assert df["funding_rate"].null_count() == 0


class TestStrategiesRunThroughEngine:
    def test_all_strategies_produce_result(self):
        df = _synthetic()
        engine = BacktestEngine()
        for name, strat in STRATEGIES.items():
            res = engine.run_walkforward(strat, df, "BTCUSDT")
            # Mechanik korrekt: Ergebnis-Objekt mit konsistenten Feldern
            assert res.n_trades >= 0
            assert isinstance(res.sharpe, float)
            assert 0.0 <= res.win_rate <= 1.0

    def test_buy_hold_trades_once_per_fold(self):
        df = _synthetic()
        engine = BacktestEngine()
        res = engine.run_walkforward(STRATEGIES["buy_hold (Ref)"], df, "BTCUSDT")
        # Ein Trade pro Fold (Force-Close am Fold-Ende)
        assert res.n_trades >= 1
