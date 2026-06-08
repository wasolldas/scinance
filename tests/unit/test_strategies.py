"""
Tests for all 5 strategies + Decision Aggregator.

Tests cover entry conditions, exit conditions, direction logic,
position management, and aggregator vetoes/sizing.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from bybit_edge.strategies.strategy1_cascade import (
    Strategy1CascadeDetector,
    _B_HISTORY_MAXLEN,
    _MIN_B_SAMPLES,
)
from bybit_edge.strategies.strategy2_entropy_momentum import (
    Strategy2EntropyMomentum,
    _MIN_ENTROPY_SAMPLES,
)
from bybit_edge.strategies.strategy4_pattern_ensemble import (
    Strategy4PatternEnsemble,
)
from bybit_edge.strategies.strategy5_cross_sectional import (
    Strategy5CrossSectional,
    _TIME_STOP_SECONDS,
)
from bybit_edge.decision_aggregator import DecisionAggregator


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _make_liq_events(
    n: int = 100,
    base_usd: float = 50000.0,
    base_ts_ms: int = 1_700_000_000_000,
) -> list[dict[str, Any]]:
    """Create synthetic liquidation events."""
    events = []
    for i in range(n):
        events.append({
            "timestamp_ms": base_ts_ms + i * 1000,
            "usd_value": base_usd + np.random.default_rng(i).uniform(-1000, 1000),
            "volume": base_usd / 50000.0,
            "side": "Long",
        })
    return events


def _make_event_times(n: int = 100, base_ts: float = 1_700_000_000.0) -> np.ndarray:
    """Create synthetic event timestamps in seconds."""
    return np.array([base_ts + i for i in range(n)], dtype=np.float64)


def _make_trades(
    n: int = 20,
    base_price: float = 50000.0,
) -> list[dict[str, Any]]:
    """Create synthetic trade data."""
    rng = np.random.default_rng(42)
    trades = []
    price = base_price
    for i in range(n):
        price += rng.normal(0, 1)
        trades.append({
            "price": price,
            "volume": rng.uniform(0.1, 1.0),
            "side": "Buy" if rng.random() > 0.5 else "Sell",
            "timestamp_ms": 1_700_000_000_000 + i * 100,
        })
    return trades


# ═══════════════════════════════════════════════════════════════════
# Strategy 1: Seismischer Cascade Detector
# ═══════════════════════════════════════════════════════════════════

class TestStrategy1CascadeDetector:

    def test_s1_entry_all_conditions(self) -> None:
        """S1 fires when rho > 0.85, b-value extreme, omori active, R0 > 1."""
        strat = Strategy1CascadeDetector()

        # Warm up b-value history with 'normal' values around 1.0
        for i in range(_MIN_B_SAMPLES + 10):
            strat._b_history.append(1.0 + np.random.default_rng(i).uniform(-0.05, 0.05))

        # Warm up rho history (rising)
        strat._rho_history.append(0.80)
        strat._rho_history.append(0.86)

        # Mock module outputs for entry conditions
        with patch.object(strat.m14, "compute", return_value={
            "branching_ratio": 0.90,
            "intensity": 5.0,
            "mu": 0.1, "alpha": 0.9, "beta": 1.0,
            "critical": True, "signal": 1,
            "method_id": "M14", "confidence": 0.9, "ts": time.time(),
        }), patch.object(strat.m15, "compute", return_value={
            "b_value": 0.4,  # Well below mean - 2*sigma
            "b_low": True, "mainshock": True, "mainshock_ts": time.time() - 60,
            "omori_active": True, "aftershock_rate": 2.0,
            "omori_params": {"K": 10.0, "c": 5.0, "p": 1.0},
            "signal": 1, "method_id": "M15", "confidence": 0.8, "ts": time.time(),
        }), patch.object(strat.m26, "compute", return_value={
            "signal": 1, "r0": 1.5, "beta": 0.01, "gamma": 0.1,
            "s_current": 1000, "i_current": 10, "peak_i_forecast": 50,
            "cascade_risk": True, "method_id": "M26", "confidence": 0.7,
            "ts": time.time(),
        }), patch.object(strat.m25, "compute", return_value={
            "signal": 0, "kyle_lambda": 0.1, "lambda_q95": 0.5,
            "toxic_flow": False, "method_id": "M25", "confidence": 0.0,
            "ts": time.time(),
        }):
            result = strat.on_data(
                liq_events=_make_liq_events(10),
                event_times=_make_event_times(10),
                open_interest=10000.0,
                trades=_make_trades(5),
                current_ts=time.time(),
                liq_side="Long",
            )

        assert result["action"] == "enter"
        assert result["direction"] == 1  # Opposite to Long liquidations
        assert result["strategy"] == "S1"
        assert strat.in_trade is True

    def test_s1_no_entry_low_rho(self) -> None:
        """S1 does not fire when rho < 0.85."""
        strat = Strategy1CascadeDetector()

        with patch.object(strat.m14, "compute", return_value={
            "branching_ratio": 0.60,  # Below 0.85
            "intensity": 1.0, "mu": 0.1, "alpha": 0.3, "beta": 0.5,
            "critical": False, "signal": 0,
            "method_id": "M14", "confidence": 0.3, "ts": time.time(),
        }), patch.object(strat.m15, "compute", return_value={
            "b_value": 0.8, "b_low": True, "mainshock": True,
            "mainshock_ts": time.time(), "omori_active": True,
            "aftershock_rate": 1.0, "omori_params": {"K": 5, "c": 3, "p": 1},
            "signal": 1, "method_id": "M15", "confidence": 0.5, "ts": time.time(),
        }), patch.object(strat.m26, "compute", return_value={
            "signal": 1, "r0": 1.5, "beta": 0.01, "gamma": 0.1,
            "s_current": 1000, "i_current": 10, "peak_i_forecast": 50,
            "cascade_risk": True, "method_id": "M26", "confidence": 0.7,
            "ts": time.time(),
        }), patch.object(strat.m25, "compute", return_value={
            "signal": 0, "kyle_lambda": 0.1, "lambda_q95": 0.5,
            "toxic_flow": False, "method_id": "M25", "confidence": 0.0,
            "ts": time.time(),
        }):
            result = strat.on_data(
                liq_events=_make_liq_events(5),
                event_times=_make_event_times(5),
                open_interest=10000.0,
                trades=_make_trades(5),
                current_ts=time.time(),
            )

        assert result["action"] == "wait"
        assert result["reason"] == "rho_below_threshold"
        assert strat.in_trade is False

    def test_s1_exit_rho_decay(self) -> None:
        """S1 exits when rho decays below 0.5."""
        strat = Strategy1CascadeDetector()
        # Force into trade
        strat._in_trade = True
        strat._entry_direction = 1
        strat._entry_ts = time.time() - 60
        strat._pre_cascade_oi = 10000.0

        with patch.object(strat.m14, "compute", return_value={
            "branching_ratio": 0.30,  # Below 0.5 exit threshold
            "intensity": 0.5, "mu": 0.1, "alpha": 0.15, "beta": 0.5,
            "critical": False, "signal": 0,
            "method_id": "M14", "confidence": 0.15, "ts": time.time(),
        }), patch.object(strat.m15, "compute", return_value={
            "b_value": 1.0, "b_low": False, "mainshock": False,
            "mainshock_ts": None, "omori_active": False,
            "aftershock_rate": 0.0, "omori_params": None,
            "signal": 0, "method_id": "M15", "confidence": 0.0, "ts": time.time(),
        }), patch.object(strat.m26, "compute", return_value={
            "signal": 0, "r0": 0.5, "beta": 0.01, "gamma": 0.1,
            "s_current": 1000, "i_current": 1, "peak_i_forecast": 5,
            "cascade_risk": False, "method_id": "M26", "confidence": 0.0,
            "ts": time.time(),
        }), patch.object(strat.m25, "compute", return_value={
            "signal": 0, "kyle_lambda": 0.05, "lambda_q95": 0.5,
            "toxic_flow": False, "method_id": "M25", "confidence": 0.0,
            "ts": time.time(),
        }):
            result = strat.on_data(
                liq_events=[],
                event_times=np.array([]),
                open_interest=9800.0,
                trades=[],
                current_ts=time.time(),
            )

        assert result["action"] == "exit"
        assert result["reason"] == "rho_decay"
        assert strat.in_trade is False


# ═══════════════════════════════════════════════════════════════════
# Strategy 2: Entropie-Momentum
# ═══════════════════════════════════════════════════════════════════

class TestStrategy2EntropyMomentum:

    def _warm_up(self, strat: Strategy2EntropyMomentum, n: int = 150) -> None:
        """Feed enough data to build history for entropy z-score & OFI Q90."""
        for i in range(n):
            bid_sizes = np.random.default_rng(i).uniform(1, 10, size=20)
            ask_sizes = np.random.default_rng(i + 1000).uniform(1, 10, size=20)
            strat.on_ticker(
                bid_sizes=bid_sizes,
                ask_sizes=ask_sizes,
                best_bid=(50000.0 - i * 0.01, 1.0),
                best_ask=(50001.0 + i * 0.01, 1.0),
                ticker_data={"premium_index": 0.001, "funding_rate": 0.0001},
                seconds_to_settlement=3600.0,
                price=50000.0 + i * 0.1,
                ts=1_700_000_000.0 + i,
            )

    def test_s2_entry_entropy_collapse(self) -> None:
        """S2 fires when entropy collapses, OFI extreme, pressure aligned, PE greenlight."""
        strat = Strategy2EntropyMomentum()
        self._warm_up(strat)

        # Mock all modules for entry
        with patch.object(strat.m6, "compute", return_value={
            "greenlight": True, "h_bid": 0.5, "h_ask": 0.5,
            "h_combined": 0.1,  # Very low entropy
            "h_q5": 1.0, "signal": 1, "method_id": "M6",
            "confidence": 0.8, "ts": time.time(),
        }), patch.object(strat.m2, "update", return_value={
            "signal": 1, "ofi": 100.0, "ofi_q90": 50.0, "e_n": 10.0,
            "method_id": "M2", "confidence": 0.7, "ts": time.time(),
        }), patch.object(strat.m22, "compute", return_value={
            "signal": 1, "pressure": 0.001, "pressure_zscore": 3.0,
            "funding_rate": 0.0001, "seconds_to_settlement": 1000,
            "in_window": True, "method_id": "M22",
            "confidence": 0.6, "ts": time.time(),
        }), patch.object(strat.m7, "update", return_value={
            "greenlight": True, "pe": 0.3, "pe_median": 0.5,
            "signal": 1, "method_id": "M7",
            "confidence": 0.4, "ts": time.time(),
        }):
            # Force entropy collapse in history
            strat._entropy_history.clear()
            for _ in range(200):
                strat._entropy_history.append(2.0)  # Normal
            strat._entropy_history.append(0.1)  # Collapsed

            result = strat.on_ticker(
                bid_sizes=np.ones(20),
                ask_sizes=np.ones(20),
                best_bid=(50000.0, 1.0),
                best_ask=(50001.0, 1.0),
                ticker_data={"premium_index": 0.001, "funding_rate": 0.0001},
                seconds_to_settlement=1000.0,
                price=50000.0,
            )

        assert result["action"] == "enter"
        assert result["direction"] == 1  # OFI positive -> Long
        assert result["strategy"] == "S2"

    def test_s2_no_entry_no_greenlight(self) -> None:
        """S2 does not fire when PE > median (no greenlight)."""
        strat = Strategy2EntropyMomentum()
        self._warm_up(strat)

        with patch.object(strat.m6, "compute", return_value={
            "greenlight": True, "h_bid": 0.5, "h_ask": 0.5,
            "h_combined": 0.1, "h_q5": 1.0, "signal": 1,
            "method_id": "M6", "confidence": 0.8, "ts": time.time(),
        }), patch.object(strat.m2, "update", return_value={
            "signal": 1, "ofi": 100.0, "ofi_q90": 50.0, "e_n": 10.0,
            "method_id": "M2", "confidence": 0.7, "ts": time.time(),
        }), patch.object(strat.m22, "compute", return_value={
            "signal": 1, "pressure": 0.001, "pressure_zscore": 3.0,
            "funding_rate": 0.0001, "seconds_to_settlement": 1000,
            "in_window": True, "method_id": "M22",
            "confidence": 0.6, "ts": time.time(),
        }), patch.object(strat.m7, "update", return_value={
            "greenlight": False,  # No greenlight!
            "pe": 0.9, "pe_median": 0.5,
            "signal": 0, "method_id": "M7",
            "confidence": 0.0, "ts": time.time(),
        }):
            strat._entropy_history.clear()
            for _ in range(200):
                strat._entropy_history.append(2.0)

            result = strat.on_ticker(
                bid_sizes=np.ones(20),
                ask_sizes=np.ones(20),
                best_bid=(50000.0, 1.0),
                best_ask=(50001.0, 1.0),
                ticker_data={"premium_index": 0.001, "funding_rate": 0.0001},
                seconds_to_settlement=1000.0,
                price=50000.0,
            )

        assert result["action"] == "wait"
        assert result["reason"] == "pe_no_greenlight"

    def test_s2_exit_ofi_flip(self) -> None:
        """S2 exits when OFI sign flips."""
        strat = Strategy2EntropyMomentum()
        # Force into trade with positive OFI
        strat._in_trade = True
        strat._entry_direction = 1
        strat._entry_ofi_sign = 1
        strat._entry_ts = time.time() - 10
        # Entropy history with median = 2.0; h_combined = 1.5 stays below median
        for _ in range(200):
            strat._entropy_history.append(2.0)

        with patch.object(strat.m6, "compute", return_value={
            "greenlight": False, "h_bid": 1.5, "h_ask": 1.5,
            "h_combined": 1.5,  # Below median -> entropy_recovered won't fire
            "h_q5": 1.0, "signal": 0,
            "method_id": "M6", "confidence": 0.0, "ts": time.time(),
        }), patch.object(strat.m2, "update", return_value={
            "signal": -1, "ofi": -80.0,  # Flipped to negative!
            "ofi_q90": 50.0, "e_n": -8.0,
            "method_id": "M2", "confidence": 0.5, "ts": time.time(),
        }), patch.object(strat.m22, "compute", return_value={
            "signal": 0, "pressure": 0.0005, "pressure_zscore": 1.0,
            "funding_rate": 0.0001, "seconds_to_settlement": 3000,
            "in_window": False, "method_id": "M22",
            "confidence": 0.0, "ts": time.time(),
        }):
            result = strat.on_ticker(
                bid_sizes=np.ones(20),
                ask_sizes=np.ones(20),
                best_bid=(50000.0, 1.0),
                best_ask=(50001.0, 1.0),
                ticker_data={"premium_index": 0.001, "funding_rate": 0.0001},
                seconds_to_settlement=3000.0,
                price=49900.0,
            )

        assert result["action"] == "exit"
        assert result["reason"] == "ofi_sign_flip"


# ═══════════════════════════════════════════════════════════════════
# Strategy 4: Pattern x Foundation Ensemble
# ═══════════════════════════════════════════════════════════════════

class TestStrategy4PatternEnsemble:

    def test_s4_entry_consensus(self) -> None:
        """S4 fires when 2/3 models agree, Pearson > 0.6, TFSAX > 0.75."""
        strat = Strategy4PatternEnsemble()

        # Create correlated forecasts
        forecast = np.array([50001, 50002, 50003, 50004, 50005], dtype=np.float64)

        with patch.object(strat.m5, "compute", return_value={
            "transformed": np.zeros(100), "d": 0.5, "adf_pvalue": 0.01,
            "n_weights": 10, "method_id": "M5", "signal": 0,
            "confidence": 0.0, "ts": time.time(),
        }), patch.object(strat.m16, "compute", return_value={
            "top_matches": [{"score": 0.9}],
            "mean_forward_return": 0.01,
            "match_score": 0.85,  # > 0.75
            "signal": 1, "method_id": "M16",
            "confidence": 0.8, "ts": time.time(),
        }), patch.object(strat.m18, "compute", return_value={
            "forecast": forecast,
            "forecast_direction": 1, "forecast_magnitude": 0.01,
            "signal": 1, "method_id": "M18",
            "confidence": 0.7, "ts": time.time(),
        }), patch.object(strat.m20, "compute", return_value={
            "forecast": forecast + 0.1,  # Correlated with PatchTST
            "forecast_direction": 1, "forecast_magnitude": 0.01,
            "is_zero_shot": True, "model_loaded": False,
            "signal": 1, "method_id": "M20",
            "confidence": 0.6, "ts": time.time(),
        }):
            result = strat.on_data(
                price_series=np.linspace(49990, 50000, 100),
                current_price=50000.0,
            )

        assert result["action"] == "enter"
        assert result["direction"] == 1
        assert result["strategy"] == "S4"

    def test_s4_no_entry_no_consensus(self) -> None:
        """S4 does not fire when models disagree."""
        strat = Strategy4PatternEnsemble()

        with patch.object(strat.m5, "compute", return_value={
            "transformed": np.zeros(100), "d": 0.5, "adf_pvalue": 0.01,
            "n_weights": 10, "method_id": "M5", "signal": 0,
            "confidence": 0.0, "ts": time.time(),
        }), patch.object(strat.m16, "compute", return_value={
            "top_matches": [], "mean_forward_return": -0.01,
            "match_score": 0.85, "signal": -1,
            "method_id": "M16", "confidence": 0.5, "ts": time.time(),
        }), patch.object(strat.m18, "compute", return_value={
            "forecast": np.array([50001, 50002]), "forecast_direction": 1,
            "forecast_magnitude": 0.01, "signal": 1,
            "method_id": "M18", "confidence": 0.6, "ts": time.time(),
        }), patch.object(strat.m20, "compute", return_value={
            "forecast": np.array([49999, 49998]),
            "forecast_direction": -1,  # Disagrees!
            "forecast_magnitude": 0.01, "is_zero_shot": True,
            "model_loaded": False, "signal": -1,
            "method_id": "M20", "confidence": 0.5, "ts": time.time(),
        }):
            result = strat.on_data(
                price_series=np.linspace(49990, 50000, 100),
                current_price=50000.0,
            )

        assert result["action"] == "wait"
        # No consensus: 1 long, 1 short, 1 short -> 2 short but
        # PatchTST and MOMENT forecasts are anticorrelated (Pearson < 0.6)

    def test_s4_exit_time_stop(self) -> None:
        """S4 exits after horizon ticks."""
        strat = Strategy4PatternEnsemble(horizon_ticks=3)
        strat._in_trade = True
        strat._entry_direction = 1
        strat._entry_ts = time.time() - 100
        strat._last_consensus_direction = 1
        strat._ticks_since_entry = 2  # Will increment to 3

        with patch.object(strat.m5, "compute", return_value={
            "transformed": np.zeros(100), "d": 0.5, "adf_pvalue": 0.01,
            "n_weights": 10, "method_id": "M5", "signal": 0,
            "confidence": 0.0, "ts": time.time(),
        }), patch.object(strat.m16, "compute", return_value={
            "top_matches": [], "mean_forward_return": 0.0,
            "match_score": 0.0, "signal": 0,
            "method_id": "M16", "confidence": 0.0, "ts": time.time(),
        }), patch.object(strat.m18, "compute", return_value={
            "forecast": np.array([50001]), "forecast_direction": 1,
            "forecast_magnitude": 0.001, "signal": 1,
            "method_id": "M18", "confidence": 0.3, "ts": time.time(),
        }), patch.object(strat.m20, "compute", return_value={
            "forecast": np.array([50001]),
            "forecast_direction": 1, "forecast_magnitude": 0.001,
            "is_zero_shot": True, "model_loaded": False, "signal": 1,
            "method_id": "M20", "confidence": 0.3, "ts": time.time(),
        }):
            result = strat.on_data(
                price_series=np.linspace(49990, 50000, 100),
                current_price=50000.0,
            )

        assert result["action"] == "exit"
        assert result["reason"] == "time_stop"


# ═══════════════════════════════════════════════════════════════════
# Strategy 5: Cross-Sectional Ergodicity Reversion
# ═══════════════════════════════════════════════════════════════════

class TestStrategy5CrossSectional:

    def test_s5_entry_extreme_z(self) -> None:
        """S5 fires when |Z| > 2.5, TE > 0.05, HMM != HIGH_VOL."""
        strat = Strategy5CrossSectional()

        with patch.object(strat.m13, "compute", return_value={
            "z_scores": {"ETHUSDT": 3.5, "BTCUSDT": 0.1},
            "extreme_symbols": [
                {"symbol": "ETHUSDT", "z": 3.5, "direction": -1},
            ],
            "signal": 1, "method_id": "M13", "confidence": 0.7,
            "ts": time.time(),
        }), patch.object(strat.m17, "compute", return_value={
            "te_scores": {"ETHUSDT": 0.10},  # > 0.05
            "lead_lag_edges": [{"source": "BTCUSDT", "target": "ETHUSDT", "te": 0.10}],
            "signal": 1, "method_id": "M17", "confidence": 0.5,
            "ts": time.time(),
        }), patch.object(strat.m9, "compute", return_value={
            "state": 0,  # TREND_UP, not HIGH_VOL
            "state_label": "TREND_UP",
            "state_probs": [0.8, 0.15, 0.05],
            "signal": 1, "method_id": "M9",
            "confidence": 0.8, "ts": time.time(),
        }):
            result = strat.on_data(
                returns={"BTCUSDT": 0.001, "ETHUSDT": 0.005},
                returns_matrix={
                    "BTCUSDT": np.random.default_rng(42).normal(0, 0.01, 100),
                    "ETHUSDT": np.random.default_rng(43).normal(0, 0.01, 100),
                },
                hmm_features=np.array([0.02, 0.5, 0.0001]),
                target_symbol="ETHUSDT",
                current_price=3000.0,
            )

        assert result["action"] == "enter"
        assert result["direction"] == -1  # Against positive Z (mean-reversion)
        assert result["strategy"] == "S5"
        assert result["symbol"] == "ETHUSDT"

    def test_s5_no_entry_hmm_crash(self) -> None:
        """S5 does not fire when HMM is in HIGH_VOL crash state."""
        strat = Strategy5CrossSectional()

        with patch.object(strat.m13, "compute", return_value={
            "z_scores": {"ETHUSDT": 3.5},
            "extreme_symbols": [
                {"symbol": "ETHUSDT", "z": 3.5, "direction": -1},
            ],
            "signal": 1, "method_id": "M13", "confidence": 0.7,
            "ts": time.time(),
        }), patch.object(strat.m17, "compute", return_value={
            "te_scores": {"ETHUSDT": 0.10},
            "lead_lag_edges": [{"source": "BTCUSDT", "target": "ETHUSDT", "te": 0.10}],
            "signal": 1, "method_id": "M17", "confidence": 0.5,
            "ts": time.time(),
        }), patch.object(strat.m9, "compute", return_value={
            "state": 2,  # HIGH_VOL -> crash -> no entry!
            "state_label": "HIGH_VOL",
            "state_probs": [0.05, 0.10, 0.85],
            "signal": -1, "method_id": "M9",
            "confidence": 0.85, "ts": time.time(),
        }):
            result = strat.on_data(
                returns={"BTCUSDT": -0.05, "ETHUSDT": -0.08},
                returns_matrix={
                    "BTCUSDT": np.random.default_rng(42).normal(0, 0.01, 100),
                    "ETHUSDT": np.random.default_rng(43).normal(0, 0.01, 100),
                },
                hmm_features=np.array([0.05, -0.3, 0.0005]),
                target_symbol="ETHUSDT",
                current_price=2500.0,
            )

        assert result["action"] == "wait"
        assert result["reason"] == "hmm_high_vol_crash"

    def test_s5_exit_z_normalizes(self) -> None:
        """S5 exits when |Z| drops below 0.5."""
        strat = Strategy5CrossSectional()
        strat._in_trade = True
        strat._entry_direction = -1
        strat._entry_symbol = "ETHUSDT"
        strat._entry_ts = time.time() - 100
        strat._entry_hmm_state = 0

        with patch.object(strat.m13, "compute", return_value={
            "z_scores": {"ETHUSDT": 0.3},  # Below 0.5 -> exit
            "extreme_symbols": [],
            "signal": 0, "method_id": "M13", "confidence": 0.0,
            "ts": time.time(),
        }), patch.object(strat.m17, "compute", return_value={
            "te_scores": {}, "lead_lag_edges": [],
            "signal": 0, "method_id": "M17", "confidence": 0.0,
            "ts": time.time(),
        }), patch.object(strat.m9, "compute", return_value={
            "state": 0, "state_label": "TREND_UP",
            "state_probs": [0.8, 0.15, 0.05],
            "signal": 1, "method_id": "M9",
            "confidence": 0.8, "ts": time.time(),
        }):
            result = strat.on_data(
                returns={"BTCUSDT": 0.001, "ETHUSDT": 0.0005},
                returns_matrix={
                    "BTCUSDT": np.random.default_rng(42).normal(0, 0.01, 100),
                    "ETHUSDT": np.random.default_rng(43).normal(0, 0.01, 100),
                },
                hmm_features=np.array([0.02, 0.5, 0.0001]),
                target_symbol="ETHUSDT",
                current_price=3100.0,
            )

        assert result["action"] == "exit"
        assert result["reason"] == "z_normalized"
        assert strat.in_trade is False


# ═══════════════════════════════════════════════════════════════════
# Decision Aggregator
# ═══════════════════════════════════════════════════════════════════

class TestDecisionAggregator:

    def test_aggregator_kyle_veto(self) -> None:
        """Aggregator blocks trade when Kyle lambda shows toxic flow."""
        agg = DecisionAggregator()

        signals = [
            {"action": "enter", "direction": 1, "strategy": "S3", "confidence": 0.8},
        ]
        kyle = {"toxic_flow": True, "kyle_lambda": 0.8, "lambda_q95": 0.5}
        sir = {"r0": 0.5, "cascade_risk": False}

        result = agg.aggregate(signals, kyle, sir)
        assert result["action"] == "wait"
        assert result["strategy_id"] == "S3"

    def test_aggregator_sir_veto(self) -> None:
        """Aggregator blocks non-cascade strategies when R0 > 1."""
        agg = DecisionAggregator()

        signals = [
            {"action": "enter", "direction": -1, "strategy": "S3", "confidence": 0.7},
        ]
        kyle = {"toxic_flow": False, "kyle_lambda": 0.1, "lambda_q95": 0.5}
        sir = {"r0": 1.5, "cascade_risk": True}

        result = agg.aggregate(signals, kyle, sir)
        assert result["action"] == "wait"

        # But S1 (cascade detector) is exempted from SIR veto
        signals_s1 = [
            {"action": "enter", "direction": 1, "strategy": "S1", "confidence": 0.9},
        ]
        result_s1 = agg.aggregate(signals_s1, kyle, sir)
        assert result_s1["action"] in ("long", "short")
        assert result_s1["strategy_id"] == "S1"

    def test_aggregator_position_sizing(self) -> None:
        """Aggregator computes position size via Kelly x Kyle discount."""
        agg = DecisionAggregator()

        signals = [
            {"action": "enter", "direction": 1, "strategy": "S2", "confidence": 0.8},
        ]
        kyle = {"toxic_flow": False, "kyle_lambda": 0.1, "lambda_q95": 0.5}
        sir = {"r0": 0.5, "cascade_risk": False}

        result = agg.aggregate(signals, kyle, sir)
        assert result["action"] == "long"
        assert result["position_size_pct"] > 0.0
        assert result["position_size_pct"] <= 0.25  # Kelly cap
        assert result["strategy_id"] == "S2"
        assert result["confidence"] > 0.0


# ═══════════════════════════════════════════════════════════════════
# T3: diagnostics blind-spot regression — every S1/S5 wait dict
#     (including ReplayBacktester._eval_strategy short-circuits, the
#     actual source of the "unknown" buckets analyst flagged as W10)
#     must carry a named "reason" key.
# ═══════════════════════════════════════════════════════════════════


class TestS1S5DiagnosticsNoUnknown:

    def test_strategy1_wait_dict_carries_named_reason(self) -> None:
        """Drive S1 to a wait state (low rho); ensure the dict has a
        ``"reason"`` that is not ``"unknown"`` — covers the briefing's
        ``test_strategy1_diagnostics_no_unknown`` requirement."""
        strat = Strategy1CascadeDetector()
        with patch.object(strat.m14, "compute", return_value={
            "branching_ratio": 0.5, "intensity": 1.0, "mu": 0.1,
            "alpha": 0.3, "beta": 0.5, "critical": False, "signal": 0,
            "method_id": "M14", "confidence": 0.3, "ts": time.time(),
        }), patch.object(strat.m15, "compute", return_value={
            "b_value": None, "b_low": False, "mainshock": False,
            "mainshock_ts": None, "omori_active": False,
            "aftershock_rate": 0.0, "omori_params": None, "signal": 0,
            "method_id": "M15", "confidence": 0.0, "ts": time.time(),
        }), patch.object(strat.m26, "compute", return_value={
            "signal": 0, "r0": 0.5, "beta": 0.0, "gamma": 0.0,
            "s_current": 1000, "i_current": 0, "peak_i_forecast": 0,
            "cascade_risk": False, "method_id": "M26",
            "confidence": 0.0, "ts": time.time(),
        }), patch.object(strat.m25, "compute", return_value={
            "signal": 0, "kyle_lambda": 0.1, "lambda_q95": 0.5,
            "toxic_flow": False, "method_id": "M25",
            "confidence": 0.0, "ts": time.time(),
        }):
            result = strat.on_data(
                liq_events=_make_liq_events(5),
                event_times=_make_event_times(5),
                open_interest=10000.0, trades=_make_trades(5),
                current_ts=time.time(), liq_side="Long",
            )
        assert result["action"] == "wait"
        assert result.get("reason") not in (None, "unknown")

    def test_strategy5_wait_dict_carries_named_reason(self) -> None:
        """Drive S5 to a wait state (HMM HIGH_VOL veto)."""
        strat = Strategy5CrossSectional()
        with patch.object(strat.m13, "compute", return_value={
            "z_scores": {"ETHUSDT": 3.5},
            "extreme_symbols": [{"symbol": "ETHUSDT", "z": 3.5,
                                 "direction": -1}],
            "signal": 1, "method_id": "M13", "confidence": 0.7,
            "ts": time.time(),
        }), patch.object(strat.m17, "compute", return_value={
            "te_scores": {"ETHUSDT": 0.10}, "lead_lag_edges": [],
            "signal": 1, "method_id": "M17",
            "confidence": 0.5, "ts": time.time(),
        }), patch.object(strat.m9, "compute", return_value={
            "state": 2, "state_label": "HIGH_VOL",
            "state_probs": [0.05, 0.10, 0.85], "signal": -1,
            "method_id": "M9", "confidence": 0.85, "ts": time.time(),
        }):
            r = strat.on_data(
                returns={"ETHUSDT": -0.05},
                returns_matrix={
                    "ETHUSDT": np.random.default_rng(0).normal(0, 0.01, 100),
                },
                hmm_features=np.array([0.05, -0.3, 0.0005]),
                target_symbol="ETHUSDT", current_price=2500.0,
            )
        assert r["action"] == "wait"
        assert r.get("reason") not in (None, "unknown")

    def test_replay_eval_strategy_short_circuits_emit_reasons(self) -> None:
        """The neutral wait dicts built by ReplayBacktester._eval_strategy
        (the actual source of the diagnose-mode 'unknown' buckets analyst
        flagged on S1-on-BNB and S5-everywhere) must carry named reasons."""
        from bybit_edge.replay_backtester import ReplayBacktester

        bt = ReplayBacktester(symbol="BTCUSDT", db_path=None)
        ticker_data: dict[str, Any] = {
            "last_price": 30_000.0, "seconds_to_settlement": 3600.0,
            "open_interest": 1000.0, "liq_events": [],
            "event_times": np.array([], dtype=np.float64), "trades": [],
        }
        sig_s1 = bt._eval_strategy("S1", strategy=None,
                                   ticker_data=ticker_data,
                                   ts_seconds=1_700_000_000.0)
        sig_s5 = bt._eval_strategy("S5", strategy=None,
                                   ticker_data=ticker_data,
                                   ts_seconds=1_700_000_000.0)
        assert sig_s1.get("reason") == "liquidations_below_min_events"
        assert sig_s5.get("reason") == "single_symbol_replay_unsupported"
