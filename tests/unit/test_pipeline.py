"""
Tests for the Pipeline orchestrator.

Tests cover initialization, ticker processing, regime gating,
risk vetoes, and full signal flow.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from bybit_edge._legacy_v1.pipeline import Pipeline


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _make_ticker_data(
    last_price: float = 50000.0,
    open_interest: float = 10000.0,
    seconds_to_settlement: float = 3600.0,
    funding_rate: float = 0.0001,
    premium_index: float = 0.001,
) -> dict[str, Any]:
    """Build a minimal ticker_data dict for Pipeline."""
    return {
        "last_price": last_price,
        "mark_price": last_price + 10,
        "index_price": last_price,
        "premium_index": premium_index,
        "funding_rate": funding_rate,
        "open_interest": open_interest,
        "seconds_to_settlement": seconds_to_settlement,
        "bid_sizes": np.random.default_rng(42).uniform(1, 10, size=20),
        "ask_sizes": np.random.default_rng(43).uniform(1, 10, size=20),
        "best_bid": (last_price - 0.5, 1.0),
        "best_ask": (last_price + 0.5, 1.0),
        "liq_events": [],
        "event_times": np.array([]),
        "trades": [],
        "price_series": np.linspace(last_price - 100, last_price, 100),
        "ts": time.time(),
    }


def _run_async(coro: Any) -> Any:
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════

class TestPipeline:

    def test_pipeline_initialization(self) -> None:
        """All modules and strategies are properly instantiated."""
        pipeline = Pipeline(symbol="BTCUSDT")

        # L1
        assert pipeline.m2 is not None

        # L2
        assert pipeline.m4 is not None
        assert pipeline.m5 is not None

        # L3
        assert pipeline.m6 is not None
        assert pipeline.m7 is not None
        assert pipeline.m8 is not None
        assert pipeline.m9 is not None

        # L4
        assert pipeline.m14 is not None
        assert pipeline.m15 is not None

        # L5
        assert pipeline.m22 is not None
        assert pipeline.m23 is not None
        assert pipeline.m24 is not None
        assert pipeline.m25 is not None
        assert pipeline.m26 is not None

        # Strategies
        assert pipeline.strategy1 is not None
        assert pipeline.strategy2 is not None
        assert pipeline.strategy3 is not None
        assert pipeline.strategy4 is not None
        assert pipeline.strategy5 is not None

        # Aggregator
        assert pipeline.aggregator is not None
        assert pipeline.symbol == "BTCUSDT"

    def test_pipeline_process_ticker_returns_dict(self) -> None:
        """process_ticker returns a dict or None."""
        pipeline = Pipeline()
        ticker = _make_ticker_data()

        result = _run_async(pipeline.process_ticker(ticker))

        # In calm market with no history, likely returns None (wait)
        assert result is None or isinstance(result, dict)

    def test_pipeline_no_signal_calm_market(self) -> None:
        """Pipeline returns None in a calm market with no extreme conditions."""
        pipeline = Pipeline()

        # Feed a few calm tickers
        for i in range(5):
            ticker = _make_ticker_data(
                last_price=50000.0 + i * 0.1,
                seconds_to_settlement=7200.0,  # 2h away from settlement
            )
            result = _run_async(pipeline.process_ticker(ticker))

        # Should not produce a signal in calm conditions
        assert result is None

    def test_pipeline_regime_greenlight_propagates(self) -> None:
        """When L3 provides greenlight, L4 pattern modules are evaluated."""
        pipeline = Pipeline()
        ticker = _make_ticker_data()

        # Mock L3 to provide greenlight
        with patch.object(pipeline.m6, "compute", return_value={
            "greenlight": True, "h_bid": 0.5, "h_ask": 0.5,
            "h_combined": 0.5, "h_q5": 1.0, "signal": 1,
            "method_id": "M6", "confidence": 0.8, "ts": time.time(),
        }), patch.object(pipeline.m7, "update", return_value={
            "greenlight": True, "pe": 0.3, "pe_median": 0.5,
            "signal": 1, "method_id": "M7",
            "confidence": 0.4, "ts": time.time(),
        }):
            # Spy on M14 to verify it gets called when greenlight
            original_m14_compute = pipeline.m14.compute
            m14_called = False

            def mock_m14_compute(*args: Any, **kwargs: Any) -> dict[str, Any]:
                nonlocal m14_called
                m14_called = True
                return original_m14_compute(*args, **kwargs)

            pipeline.m14.compute = mock_m14_compute  # type: ignore[method-assign]

            _run_async(pipeline.process_ticker(ticker))

        assert m14_called, "M14 (Hawkes) should be called when L3 greenlight is active"

    def test_pipeline_risk_veto_overrides(self) -> None:
        """When Kyle lambda detects toxic flow, all signals are vetoed."""
        pipeline = Pipeline()
        ticker = _make_ticker_data()

        # Mock M25 to return toxic flow
        with patch.object(pipeline.m25, "compute", return_value={
            "signal": -1, "kyle_lambda": 1.0, "lambda_q95": 0.5,
            "toxic_flow": True, "method_id": "M25",
            "confidence": 0.9, "ts": time.time(),
        }):
            # Mock a strategy to produce a signal
            with patch.object(pipeline.strategy3, "on_ticker", return_value={
                "action": "enter", "direction": 1, "price": 50000.0,
                "strategy": "S3", "modules": {},
                "reason": "all_conditions_met",
            }):
                result = _run_async(pipeline.process_ticker(ticker))

        # Toxic flow should veto: result should be None (wait)
        assert result is None

    def test_pipeline_reset(self) -> None:
        """Pipeline reset clears all internal state."""
        pipeline = Pipeline()

        # Feed some data
        ticker = _make_ticker_data()
        _run_async(pipeline.process_ticker(ticker))

        # Reset
        pipeline.reset()

        # Verify strategies are reset
        assert pipeline.strategy1.in_trade is False
        assert pipeline.strategy2.in_trade is False
        assert pipeline.strategy3.in_trade is False
        assert pipeline.strategy4.in_trade is False
        assert pipeline.strategy5.in_trade is False
