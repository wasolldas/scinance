"""Unit tests for the Optuna hyperparameter tuning stack.

Network-free. Optuna-only tests guarded by ``pytest.importorskip`` so the
suite stays green when the ``[tuning]`` extra is not installed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import bybit_edge.config as cfg
from bybit_edge._legacy_v1.backtester.engine import BacktestResult
from bybit_edge.persistence.db import PersistenceLayer
from bybit_edge._legacy_v1.replay_backtester import ReplayBacktester
from bybit_edge._legacy_v1.state.liquidation_buffer import LiquidationEvent
from bybit_edge._legacy_v1.state.ticker_state import TickerSnapshot
from bybit_edge._legacy_v1.state.trade_buffer import TradeEvent
from bybit_edge._legacy_v1.tuning import ParameterContext, SPACES, sample_from_space

_SYMBOL = "BTCUSDT"
_BASE_TS = 1_700_000_000_000


# ══════════════════════════════════════════════════════════════════════
# Fixtures / helpers (mirror test_replay_backtester.py)
# ══════════════════════════════════════════════════════════════════════
@pytest.fixture()
def persist() -> PersistenceLayer:
    layer = PersistenceLayer(db_path=Path(":memory:"))
    yield layer
    layer.close()


# Stride between successive synthetic ticks. 30 minutes per tick keeps
# fixtures small (60 events span ~1.25 days) while letting walk-forward
# folds with train_days/test_days >= 1 actually slide. Tuned so that a
# single (train_days=1, test_days=1, embargo=0) fold finds a meaningful
# slice over the synthetic window without the fold sweep degenerating
# into a zero-width-step infinite loop.
_TICK_STRIDE_MS: int = 30 * 60 * 1000


def _ticker(i: int, *, last_price: float = 30_000.0,
            ts: int | None = None) -> TickerSnapshot:
    return TickerSnapshot(
        symbol=_SYMBOL,
        last_price=last_price,
        mark_price=last_price,
        index_price=last_price,
        funding_rate=0.0001,
        next_funding_time=0,
        open_interest=1_000_000.0,
        open_interest_value=3.0e10,
        bid1_price=last_price - 1.0,
        bid1_size=5.0,
        ask1_price=last_price + 1.0,
        ask1_size=5.0,
        ts=ts if ts is not None else _BASE_TS + i * _TICK_STRIDE_MS,
        recv_ts=0.0,
    )


def _trade(i: int, price: float = 30_000.0, side: str = "Buy") -> TradeEvent:
    return TradeEvent(
        timestamp_ms=_BASE_TS + i * _TICK_STRIDE_MS,
        price=price,
        volume=1.0,
        side=side,
        is_block=False,
    )


def _liq(i: int, usd: float = 1.0e6, side: str = "Sell") -> LiquidationEvent:
    price = 30_000.0
    return LiquidationEvent(
        timestamp_ms=_BASE_TS + i * _TICK_STRIDE_MS,
        symbol=_SYMBOL,
        side=side,
        volume=usd / price,
        price=price,
        usd_value=usd,
    )


def _new_bt(persist: PersistenceLayer) -> ReplayBacktester:
    bt = ReplayBacktester(_SYMBOL, db_path=None)
    bt.persist = persist
    return bt


# ══════════════════════════════════════════════════════════════════════
# ParameterContext
# ══════════════════════════════════════════════════════════════════════
def test_parameter_context_overrides_and_restores() -> None:
    """Override two config values, check they take effect, then restore."""
    original_z = cfg.PRESSURE_ZSCORE_THRESHOLD
    original_q = cfg.S3_PRESSURE_QUANTILE

    overrides = {
        "PRESSURE_ZSCORE_THRESHOLD": 1.234,
        "S3_PRESSURE_QUANTILE": 0.876,
    }
    with ParameterContext(overrides):
        assert cfg.PRESSURE_ZSCORE_THRESHOLD == 1.234
        assert cfg.S3_PRESSURE_QUANTILE == 0.876
        # The strategy module imported S3_PRESSURE_QUANTILE via from-import;
        # the context must also patch its module-level binding so that
        # runtime reads inside the strategy see the override.
        from bybit_edge._legacy_v1.strategies import strategy3_pre_settlement as s3mod
        assert s3mod.S3_PRESSURE_QUANTILE == 0.876

    # Originals fully restored.
    assert cfg.PRESSURE_ZSCORE_THRESHOLD == original_z
    assert cfg.S3_PRESSURE_QUANTILE == original_q
    from bybit_edge._legacy_v1.strategies import strategy3_pre_settlement as s3mod
    assert s3mod.S3_PRESSURE_QUANTILE == original_q


def test_parameter_context_invalid_key_raises() -> None:
    """Unknown config keys must fail-fast on __enter__ before any patching."""
    with pytest.raises(ValueError, match="unknown config attribute"):
        with ParameterContext({"NOT_A_REAL_CONFIG_KEY": 42}):
            pass  # pragma: no cover — should never enter the body


def test_parameter_context_restores_on_exception() -> None:
    """Exceptions inside the context must still trigger full restoration."""
    original = cfg.HAWKES_CRITICAL_RHO

    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom):
        with ParameterContext({"HAWKES_CRITICAL_RHO": 0.42}):
            assert cfg.HAWKES_CRITICAL_RHO == 0.42
            # Verify strategy module is patched too.
            from bybit_edge._legacy_v1.strategies import strategy1_cascade as s1mod
            # S1 does not import HAWKES_CRITICAL_RHO directly, but the
            # M14 Hawkes layer module does — confirm at least one module
            # got patched besides config.
            from bybit_edge._legacy_v1.layers.l4_pattern import m14_hawkes
            assert m14_hawkes.HAWKES_CRITICAL_RHO == 0.42
            del s1mod  # silence unused-import lint
            raise Boom("intentional")

    assert cfg.HAWKES_CRITICAL_RHO == original
    from bybit_edge._legacy_v1.layers.l4_pattern import m14_hawkes
    assert m14_hawkes.HAWKES_CRITICAL_RHO == original


# ══════════════════════════════════════════════════════════════════════
# ReplayBacktester integration
# ══════════════════════════════════════════════════════════════════════
def test_replay_backtester_param_overrides_default_none_unchanged(
    persist: PersistenceLayer,
) -> None:
    """Default ``param_overrides=None`` must reproduce pre-tuning results.

    We compare a result-by-result equality of the metrics dict; trades and
    summary scalars must match between the two calls.
    """
    # ~150 ticks @ 30-min stride = ~3 days, enough for at least one
    # 1-train/1-test fold to actually fit in the window.
    persist.write_tickers_batch([_ticker(i) for i in range(150)])
    persist.write_trades_batch([_trade(i) for i in range(150)], symbol=_SYMBOL)

    bt = _new_bt(persist)
    bt.load_events()

    res1 = bt.run_walkforward(
        pipeline_interval_seconds=1.0,
        train_days=1,
        test_days=1,
        embargo_minutes=0,
        min_train_events=1,
    )
    res2 = bt.run_walkforward(
        pipeline_interval_seconds=1.0,
        train_days=1,
        test_days=1,
        embargo_minutes=0,
        min_train_events=1,
        param_overrides=None,
    )

    # Same set of strategies, same number of trades, same Sharpe.
    assert set(res1.keys()) == set(res2.keys())
    for sid in res1:
        assert res1[sid].n_trades == res2[sid].n_trades
        assert res1[sid].sharpe == res2[sid].sharpe
        assert res1[sid].max_drawdown == res2[sid].max_drawdown


def test_replay_backtester_param_overrides_applied_per_fold(
    persist: PersistenceLayer,
) -> None:
    """An aggressive override must materially change behaviour vs default.

    We inject a fake S1 strategy via ``_eval_strategy`` that consults the
    LIVE ``HAWKES_CRITICAL_RHO`` value at every call. With the default
    (~0.9) it never triggers; under an extreme override (0.0) it always
    fires. The walk-forward path must surface the override change.
    """
    prices = [30_000.0 + (i % 5) * 20 for i in range(150)]
    persist.write_tickers_batch(
        [_ticker(i, last_price=prices[i]) for i in range(150)]
    )

    bt = _new_bt(persist)
    bt.load_events()

    toggle = {"open": False}

    def fake_eval(strategy_id: str, strategy: Any,
                  ticker_data: dict, ts_seconds: float) -> dict:
        if strategy_id != "S1":
            return {"action": "wait", "direction": 0, "strategy": strategy_id}
        # Read the LIVE config value — under an override this changes.
        import bybit_edge.config as live_cfg
        if live_cfg.HAWKES_CRITICAL_RHO > 0.5:
            return {"action": "wait", "direction": 0, "strategy": "S1"}
        if not toggle["open"]:
            toggle["open"] = True
            return {"action": "enter", "direction": 1, "strategy": "S1"}
        toggle["open"] = False
        return {"action": "exit", "direction": 1, "strategy": "S1"}

    bt._eval_strategy = fake_eval  # type: ignore[assignment]

    # No override -> default rho ~0.9 -> S1 never fires.
    toggle["open"] = False
    res_no = bt.run_walkforward(
        pipeline_interval_seconds=1.0,
        train_days=1,
        test_days=1,
        embargo_minutes=0,
        min_train_events=1,
    )
    assert res_no["S1"].n_trades == 0

    # Aggressive override -> S1 alternates enter/exit -> trades > 0.
    toggle["open"] = False
    res_yes = bt.run_walkforward(
        pipeline_interval_seconds=1.0,
        train_days=1,
        test_days=1,
        embargo_minutes=0,
        min_train_events=1,
        param_overrides={"HAWKES_CRITICAL_RHO": 0.0},
    )
    assert res_yes["S1"].n_trades > 0

    # And the override is rolled back: subsequent default call is unchanged.
    assert cfg.HAWKES_CRITICAL_RHO > 0.5


# ══════════════════════════════════════════════════════════════════════
# Search-space helpers
# ══════════════════════════════════════════════════════════════════════
class _FakeTrial:
    """Minimal Optuna-trial stand-in for offline sampling tests.

    Each ``suggest_*`` call returns the midpoint of the supplied range
    (or the first categorical choice). That is enough to exercise the
    type plumbing in :func:`sample_from_space` without Optuna installed.
    """

    number: int = 0

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def suggest_float(self, name: str, low: float, high: float,
                      log: bool = False, step: float | None = None) -> float:
        self.calls.append((name, "float"))
        return (low + high) / 2.0

    def suggest_int(self, name: str, low: int, high: int,
                    step: int = 1) -> int:
        self.calls.append((name, "int"))
        mid = (low + high) // 2
        # Snap to step grid so callers see a valid value.
        return low + ((mid - low) // step) * step

    def suggest_categorical(self, name: str, choices: list) -> Any:
        self.calls.append((name, "categorical"))
        return choices[0]


def test_space_sampling() -> None:
    """``sample_from_space`` returns one value of the right type per key."""
    space = SPACES["S3"]
    trial = _FakeTrial()
    sample = sample_from_space(trial, space)

    assert set(sample.keys()) == set(space.keys())
    for name, spec in space.items():
        val = sample[name]
        if spec["type"] == "float":
            assert isinstance(val, float)
            assert spec["low"] <= val <= spec["high"]
        elif spec["type"] == "int":
            assert isinstance(val, int)
            assert spec["low"] <= val <= spec["high"]
    # Every parameter was queried exactly once.
    assert len(trial.calls) == len(space)


def test_space_sampling_unknown_type_raises() -> None:
    """Unsupported spec types must fail loudly."""
    bad_space = {"X": {"type": "uniform", "low": 0.0, "high": 1.0}}
    trial = _FakeTrial()
    with pytest.raises(ValueError, match="Unknown space spec type"):
        sample_from_space(trial, bad_space)


# ══════════════════════════════════════════════════════════════════════
# Optuna-driven tuner — guarded by importorskip
# ══════════════════════════════════════════════════════════════════════
def test_tuner_objective_returns_negative_sharpe_or_maximizes(
    persist: PersistenceLayer,
) -> None:
    """End-to-end: a 2-trial study runs cleanly and returns a sane summary."""
    optuna = pytest.importorskip("optuna")
    del optuna  # only needed for importorskip; OptunaTuner imports its own.

    from bybit_edge._legacy_v1.tuning.optuna_tuner import OptunaTuner

    # Enough data for at least one fold with min_train_events=1.
    persist.write_tickers_batch([_ticker(i) for i in range(150)])
    persist.write_trades_batch([_trade(i) for i in range(150)], symbol=_SYMBOL)

    bt = _new_bt(persist)
    bt.load_events()

    # Force-trade fake to ensure non-zero trades regardless of params.
    state = {"open": False}

    def fake_eval(strategy_id: str, strategy: Any,
                  ticker_data: dict, ts_seconds: float) -> dict:
        if strategy_id != "S3":
            return {"action": "wait", "direction": 0, "strategy": strategy_id}
        if not state["open"]:
            state["open"] = True
            return {"action": "enter", "direction": 1, "strategy": "S3"}
        state["open"] = False
        return {"action": "exit", "direction": 1, "strategy": "S3"}

    bt._eval_strategy = fake_eval  # type: ignore[assignment]

    tuner = OptunaTuner(
        backtester=bt,
        strategy_id="S3",
        space=SPACES["S3"],
        train_days=1,
        test_days=1,
        embargo_minutes=0,
        n_trials=2,
        study_path=None,
        min_train_events=1,
    )
    summary = tuner.run()

    assert summary["strategy_id"] == "S3"
    assert summary["n_trials"] == 2
    assert isinstance(summary["best_params"], dict)
    assert set(summary["best_params"].keys()) <= set(SPACES["S3"].keys())
    # The fake always trades, so best_value must be a finite float (not penalty).
    assert summary["best_value"] is not None
    assert summary["best_value"] > -100.0


def test_tuner_handles_zero_trades(persist: PersistenceLayer) -> None:
    """A space that produces zero trades must yield the penalty (no crash)."""
    pytest.importorskip("optuna")
    from bybit_edge._legacy_v1.tuning.optuna_tuner import OptunaTuner

    # Multi-day data without fake_eval -> S3 cannot reach its pressure
    # quantile gate on this short synthetic set, so every trial yields 0
    # trades and the penalty path is exercised.
    persist.write_tickers_batch([_ticker(i) for i in range(150)])

    bt = _new_bt(persist)
    bt.load_events()

    tuner = OptunaTuner(
        backtester=bt,
        strategy_id="S3",
        space=SPACES["S3"],
        train_days=1,
        test_days=1,
        embargo_minutes=0,
        n_trials=2,
        study_path=None,
        min_train_events=1,
    )
    summary = tuner.run()

    # Every trial saw 0 trades -> penalty wins; tuner does not crash.
    assert summary["n_trials"] == 2
    assert summary["best_value"] == pytest.approx(-100.0)


def test_tuner_empty_space_skipped(persist: PersistenceLayer) -> None:
    """S4 has an empty search space — the tuner must mark the run as skipped."""
    pytest.importorskip("optuna")
    from bybit_edge._legacy_v1.tuning.optuna_tuner import OptunaTuner

    persist.write_tickers_batch([_ticker(i) for i in range(150)])
    bt = _new_bt(persist)
    bt.load_events()

    tuner = OptunaTuner(
        backtester=bt,
        strategy_id="S4",
        space=SPACES["S4"],
        train_days=1,
        test_days=1,
        embargo_minutes=0,
        n_trials=2,
        study_path=None,
        min_train_events=1,
    )
    summary = tuner.run()
    assert summary["skipped"] is True
    assert summary["n_trials"] == 0
    assert summary["best_params"] == {}


def test_tuner_study_persists_to_sqlite(
    tmp_path: Path, persist: PersistenceLayer,
) -> None:
    """Passing a ``study_path`` materialises an Optuna SQLite study file."""
    pytest.importorskip("optuna")
    from bybit_edge._legacy_v1.tuning.optuna_tuner import OptunaTuner

    persist.write_tickers_batch([_ticker(i) for i in range(150)])
    bt = _new_bt(persist)
    bt.load_events()

    study_path = tmp_path / "S3.db"
    tuner = OptunaTuner(
        backtester=bt,
        strategy_id="S3",
        space=SPACES["S3"],
        train_days=1,
        test_days=1,
        embargo_minutes=0,
        n_trials=2,
        study_path=study_path,
        min_train_events=1,
    )
    summary = tuner.run()
    assert summary["study_path"] == str(study_path)
    assert study_path.exists()
    assert study_path.stat().st_size > 0
