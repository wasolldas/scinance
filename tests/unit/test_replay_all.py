"""
Unit tests for the multi-symbol replay aggregator (``scripts/replay_all.py``).

All tests are network-free and use an in-memory DuckDB filled with synthetic
ticks via the real ``write_*_batch`` helpers and the real dataclasses.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import archive.v1_scripts.replay_all as replay_all
from bybit_edge._legacy_v1.backtester.engine import BacktestResult, Trade
from bybit_edge.persistence.db import PersistenceLayer
from bybit_edge._legacy_v1.replay_backtester import ReplayBacktester
from bybit_edge._legacy_v1.state.ticker_state import TickerSnapshot

_BASE_TS = 1_700_000_000_000


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _ticker(symbol: str, i: int, *, last_price: float = 100.0) -> TickerSnapshot:
    return TickerSnapshot(
        symbol=symbol,
        last_price=last_price,
        mark_price=last_price,
        index_price=last_price,
        funding_rate=0.0001,
        next_funding_time=0,
        open_interest=1_000_000.0,
        open_interest_value=1.0e8,
        bid1_price=last_price - 0.1,
        bid1_size=10.0,
        ask1_price=last_price + 0.1,
        ask1_size=10.0,
        ts=_BASE_TS + i * 1000,
        recv_ts=0.0,
    )


def _make_db(tmp_path: Path, symbols_with_events: dict[str, int]) -> Path:
    """Create a fresh on-disk DuckDB with a few ticker rows per symbol.

    Each entry ``{symbol: n_ticks}`` writes ``n_ticks`` synthetic ticker
    snapshots. A symbol with ``n_ticks == 0`` is *not* inserted so it stays
    absent from the ``tickers`` table.
    """
    db_path = tmp_path / "bybit_edge.duckdb"
    persist = PersistenceLayer(db_path=db_path)
    try:
        for sym, n in symbols_with_events.items():
            if n <= 0:
                continue
            persist.write_tickers_batch(
                [_ticker(sym, i, last_price=100.0 + i) for i in range(n)]
            )
    finally:
        persist.close()
    return db_path


def _trade(symbol: str, entry_price: float, exit_price: float) -> Trade:
    return Trade(
        symbol=symbol,
        entry_ts=_BASE_TS,
        exit_ts=_BASE_TS + 60_000,
        side="Long",
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=1.0,
        fee_type="taker",
        pnl=exit_price - entry_price,
        pnl_bps=(exit_price - entry_price) / max(entry_price, 1e-9) * 10_000.0,
    )


def _fake_result(*, n_trades: int, sharpe: float, win_rate: float,
                 max_dd: float = 0.05, total_return: float = 0.01) -> BacktestResult:
    """Build a BacktestResult with the metric fields needed for aggregation.

    The aggregator only reads the float / int fields on the result wrapper that
    we expose through ``_result_row`` — so the synthetic trade list can stay
    minimal.
    """
    trades = [
        _trade("X", 100.0, 100.0 + (1.0 if i % 2 == 0 else -1.0))
        for i in range(n_trades)
    ]
    return BacktestResult(
        trades=trades,
        sharpe=float(sharpe),
        max_drawdown=float(max_dd),
        win_rate=float(win_rate),
        total_return=float(total_return),
        n_trades=int(n_trades),
        equity_curve=__import__("numpy").asarray([0.0] * max(n_trades, 1)),
    )


# ----------------------------------------------------------------------
# Auto symbol discovery
# ----------------------------------------------------------------------

def test_replay_all_auto_symbol_discovery(tmp_path: Path) -> None:
    """SELECT DISTINCT symbol FROM tickers — both symbols must come back."""
    db_path = _make_db(tmp_path, {"AAA": 3, "BBB": 5})
    syms = replay_all.discover_symbols(db_path)
    assert set(syms) == {"AAA", "BBB"}
    # Order is deterministic (alphabetical from SQL)
    assert syms == sorted(syms)


def test_replay_all_auto_fallback_to_universe(tmp_path: Path) -> None:
    """Empty tickers table → fallback to MULTI_SYMBOL_UNIVERSE."""
    db_path = tmp_path / "empty.duckdb"
    persist = PersistenceLayer(db_path=db_path)
    persist.close()
    syms, source = replay_all.resolve_symbols(None, True, db_path)
    from bybit_edge.config import MULTI_SYMBOL_UNIVERSE
    assert syms == list(MULTI_SYMBOL_UNIVERSE)
    assert "fallback" in source


def test_replay_all_explicit_symbols_override_auto(tmp_path: Path) -> None:
    """--symbols beats --auto even when DB has different symbols."""
    db_path = _make_db(tmp_path, {"AAA": 3})
    syms, source = replay_all.resolve_symbols("X,Y,Z", True, db_path)
    assert syms == ["X", "Y", "Z"]
    assert source == "explicit"


# ----------------------------------------------------------------------
# Status classification
# ----------------------------------------------------------------------

@pytest.mark.parametrize(
    "n,expected",
    [
        (0, "no-trades"),
        (1, "data-limited"),
        (4, "data-limited"),
        (5, "OK"),
        (100, "OK"),
    ],
)
def test_replay_all_status_classification(n: int, expected: str) -> None:
    assert replay_all.classify_status(n) == expected


# ----------------------------------------------------------------------
# Aggregation
# ----------------------------------------------------------------------

def test_replay_all_aggregates_per_strategy() -> None:
    """Aggregation across two symbols — weighted Sharpe + Win-Rate."""
    per_symbol = {
        "AAA": {
            "S1": {"sharpe": 2.0, "win_rate": 0.60, "max_drawdown": 0.05,
                   "total_return": 0.10, "n_trades": 10, "data_limited": False},
            "S3": {"sharpe": 0.5, "win_rate": 0.50, "max_drawdown": 0.02,
                   "total_return": 0.01, "n_trades": 4, "data_limited": False},
        },
        "BBB": {
            "S1": {"sharpe": 1.0, "win_rate": 0.40, "max_drawdown": 0.10,
                   "total_return": 0.05, "n_trades": 20, "data_limited": False},
            "S3": {"sharpe": 0.0, "win_rate": 0.0, "max_drawdown": 0.0,
                   "total_return": 0.0, "n_trades": 0, "data_limited": False},
        },
    }
    agg = replay_all.aggregate_per_strategy(per_symbol)

    # S1: total = 30, weighted sharpe = (2*10 + 1*20)/30 = 40/30 = 1.333..
    assert agg["S1"]["total_trades"] == 30
    assert agg["S1"]["weighted_sharpe"] == pytest.approx(40.0 / 30.0, rel=1e-4)
    # Win-rate weighted = (0.6*10 + 0.4*20)/30 = (6+8)/30 = 14/30
    assert agg["S1"]["mean_win_rate"] == pytest.approx(14.0 / 30.0, rel=1e-4)
    # worst-case MaxDD = max(0.05, 0.10) = 0.10
    assert agg["S1"]["worst_max_dd"] == pytest.approx(0.10)
    # total return summed
    assert agg["S1"]["total_return"] == pytest.approx(0.15, rel=1e-4)
    # best_symbol = BBB (n=20 >= 5 with sharpe 1.0)? Actually AAA has 10 >=5
    # with sharpe 2.0 > 1.0 — so AAA wins.
    assert agg["S1"]["best_symbol"] == "AAA"

    # S3: total = 4 (AAA only had 4, BBB 0); both data_limited
    assert agg["S3"]["total_trades"] == 4
    assert "AAA" in agg["S3"]["data_limited_symbols"]
    assert "BBB" in agg["S3"]["data_limited_symbols"]
    # No symbol with n>=5 → best_symbol falls back to argmax over n>0
    assert agg["S3"]["best_symbol"] == "AAA"


def test_replay_all_aggregate_empty_input() -> None:
    """No per-symbol results → empty aggregate."""
    assert replay_all.aggregate_per_strategy({}) == {}


def test_replay_all_handles_empty_symbol(tmp_path: Path, monkeypatch) -> None:
    """A symbol with no events is gracefully skipped (no NaN / crash)."""
    db_path = _make_db(tmp_path, {"AAA": 30})
    # "ZZZ" is requested but never written to DuckDB → must be skipped.
    per_symbol, agg, skipped, wf_meta = replay_all.run(
        symbols=["AAA", "ZZZ"],
        db_path=db_path,
        interval=1.0,
        walkforward=False,
        train_days=7,
        test_days=1,
        embargo_minutes=30,
    )
    assert "ZZZ" in skipped
    assert "AAA" in per_symbol
    # Aggregate must contain finite numbers (no NaN) for every strategy.
    for sid, row in agg.items():
        assert isinstance(row["weighted_sharpe"], float)
        assert row["weighted_sharpe"] == row["weighted_sharpe"]  # NaN check
        assert row["mean_win_rate"] == row["mean_win_rate"]
    assert wf_meta is None


# ----------------------------------------------------------------------
# Both JSON outputs written
# ----------------------------------------------------------------------

def test_replay_all_writes_both_json_files(tmp_path: Path) -> None:
    """Output lands in replay_all_results.json AND replay_backtest_results.json."""
    per_symbol = {
        "AAA": {
            "S1": {"sharpe": 1.5, "win_rate": 0.6, "max_drawdown": 0.05,
                   "total_return": 0.10, "n_trades": 10, "data_limited": False,
                   "status": "OK"},
        },
    }
    agg = replay_all.aggregate_per_strategy(per_symbol)
    payload = replay_all.build_payload(
        mode="single_pass",
        symbols=["AAA"],
        per_symbol=per_symbol,
        per_strategy_aggregate=agg,
        skipped=[],
        walkforward_meta=None,
        interval_seconds=1.0,
    )
    legacy = replay_all.build_legacy_payload(
        mode="single_pass",
        symbols=["AAA"],
        per_strategy_aggregate=agg,
        interval_seconds=1.0,
    )
    primary, legacy_path = replay_all.write_outputs(
        payload=payload, legacy_payload=legacy, out_dir=tmp_path
    )
    assert primary.exists()
    assert legacy_path.exists()
    assert primary.name == "replay_all_results.json"
    assert legacy_path.name == "replay_backtest_results.json"

    primary_data = json.loads(primary.read_text())
    legacy_data = json.loads(legacy_path.read_text())

    # Primary uses the multi-symbol schema
    assert "per_strategy_aggregate" in primary_data
    assert "per_symbol" in primary_data
    assert primary_data["symbols"] == ["AAA"]
    assert primary_data["mode"] == "single_pass"
    # Legacy uses the {"results": [...]} schema the dashboard already reads
    assert "results" in legacy_data
    assert any(r["strategy"] == "S1" for r in legacy_data["results"])


# ----------------------------------------------------------------------
# End-to-end with monkey-patched ReplayBacktester (fast, deterministic)
# ----------------------------------------------------------------------

def test_replay_all_end_to_end_with_patched_backtester(
    tmp_path: Path, monkeypatch
) -> None:
    """Smoke test: monkey-patch the backtester to emit known per-strategy
    results; verify that ``run`` aggregates them and skips empty symbols."""
    db_path = _make_db(tmp_path, {"AAA": 3, "BBB": 3})

    class _FakeBT:
        def __init__(self, symbol: str, db_path: Any = None) -> None:
            self.symbol = symbol
            self.last_walkforward_folds = 0

        def load_events(self) -> int:
            return 100 if self.symbol in ("AAA", "BBB") else 0

        def run(self, pipeline_interval_seconds: float = 1.0):
            if self.symbol == "AAA":
                return {
                    "S1": _fake_result(n_trades=10, sharpe=2.0, win_rate=0.6),
                    "S3": _fake_result(n_trades=3, sharpe=0.5, win_rate=0.5),
                }
            return {
                "S1": _fake_result(n_trades=20, sharpe=1.0, win_rate=0.4),
                "S3": _fake_result(n_trades=0, sharpe=0.0, win_rate=0.0),
            }

        def close(self) -> None:
            pass

    monkeypatch.setattr(replay_all, "ReplayBacktester", _FakeBT)

    per_symbol, agg, skipped, wf_meta = replay_all.run(
        symbols=["AAA", "BBB"],
        db_path=db_path,
        interval=1.0,
        walkforward=False,
        train_days=7,
        test_days=1,
        embargo_minutes=30,
    )
    assert skipped == []
    assert set(per_symbol.keys()) == {"AAA", "BBB"}
    assert agg["S1"]["total_trades"] == 30
    assert agg["S1"]["best_symbol"] == "AAA"  # 2.0 sharpe with n>=5


# ----------------------------------------------------------------------
# Real ReplayBacktester smoke run (no patching) — single tiny DuckDB
# ----------------------------------------------------------------------

def test_replay_all_single_symbol_smoke(tmp_path: Path) -> None:
    """Confirm the driver wires up a real ReplayBacktester correctly."""
    db_path = _make_db(tmp_path, {"AAA": 20})
    per_symbol, agg, skipped, wf_meta = replay_all.run(
        symbols=["AAA"],
        db_path=db_path,
        interval=1.0,
        walkforward=False,
        train_days=7,
        test_days=1,
        embargo_minutes=30,
    )
    assert skipped == []
    assert "AAA" in per_symbol
    # All five strategies should appear (n_trades likely 0 for synthetic data)
    assert set(per_symbol["AAA"].keys()) == {"S1", "S2", "S3", "S4", "S5"}
    # Aggregate contains the same strategy keys
    assert set(agg.keys()) == {"S1", "S2", "S3", "S4", "S5"}
    # data-limited classification: 0 trades → no-trades
    for sid, m in per_symbol["AAA"].items():
        assert m["status"] in {"no-trades", "data-limited", "OK"}


# ----------------------------------------------------------------------
# CLI parsing
# ----------------------------------------------------------------------

def test_replay_all_cli_parses_flags() -> None:
    ns = replay_all._parse_args(
        ["--symbols", "BTCUSDT,ETHUSDT", "--walkforward",
         "--train-days", "3", "--test-days", "1", "--embargo-minutes", "15",
         "--interval", "2.0"]
    )
    assert ns.symbols == "BTCUSDT,ETHUSDT"
    assert ns.walkforward is True
    assert ns.train_days == 3
    assert ns.test_days == 1
    assert ns.embargo_minutes == 15
    assert ns.interval == 2.0


def test_replay_all_cli_auto_default() -> None:
    ns = replay_all._parse_args([])
    assert ns.symbols is None
    assert ns.auto is False
    assert ns.walkforward is False
    # --diagnose defaults off.
    assert ns.diagnose is False


def test_replay_all_cli_parses_diagnose_flag() -> None:
    ns = replay_all._parse_args(["--diagnose"])
    assert ns.diagnose is True


# ----------------------------------------------------------------------
# Diagnostics wiring (opt-in)
# ----------------------------------------------------------------------

def test_replay_all_collects_diagnostics_into_sink(tmp_path: Path) -> None:
    """With ``diagnose=True`` and a sink dict, ``run`` fills per-symbol
    diagnostics in-place while preserving the 4-tuple return shape."""
    db_path = _make_db(tmp_path, {"AAA": 20})
    sink: dict[str, Any] = {}
    per_symbol, agg, skipped, wf_meta = replay_all.run(
        symbols=["AAA"],
        db_path=db_path,
        interval=1.0,
        walkforward=False,
        train_days=7,
        test_days=1,
        embargo_minutes=30,
        diagnose=True,
        diagnostics_sink=sink,
    )
    assert "AAA" in per_symbol
    assert "AAA" in sink
    # Per-strategy reason counters present for all five strategies.
    assert set(sink["AAA"].keys()) == {"S1", "S2", "S3", "S4", "S5"}
    assert "reason_counts" in sink["AAA"]["S3"]
    assert "n_ticks_total" in sink["AAA"]["S3"]


def test_replay_all_diagnose_off_leaves_sink_empty(tmp_path: Path) -> None:
    """Without ``diagnose`` the sink stays empty (no overhead, default off)."""
    db_path = _make_db(tmp_path, {"AAA": 20})
    sink: dict[str, Any] = {}
    replay_all.run(
        symbols=["AAA"],
        db_path=db_path,
        interval=1.0,
        walkforward=False,
        train_days=7,
        test_days=1,
        embargo_minutes=30,
        diagnostics_sink=sink,
    )
    assert sink == {}


# ----------------------------------------------------------------------
# --fast-omori CLI flag
# ----------------------------------------------------------------------


def test_replay_all_fast_omori_flag_absent_resolves_to_zero() -> None:
    """Without ``--fast-omori`` the resolver returns 0.0 (no throttle)."""
    ns = replay_all._parse_args([])
    assert ns.fast_omori is None
    assert replay_all._resolve_fast_omori(ns.fast_omori) == 0.0


def test_replay_all_fast_omori_flag_no_value_uses_config_default() -> None:
    """``--fast-omori`` without a value falls back to OMORI_REFIT_SECONDS."""
    from bybit_edge.config import OMORI_REFIT_SECONDS
    ns = replay_all._parse_args(["--fast-omori"])
    # argparse stores the const sentinel; the resolver maps it to the config.
    assert ns.fast_omori is replay_all._FAST_OMORI_DEFAULT_SENTINEL
    assert replay_all._resolve_fast_omori(ns.fast_omori) == float(
        OMORI_REFIT_SECONDS
    )


def test_replay_all_fast_omori_flag_with_value_parsed() -> None:
    """``--fast-omori 15`` is parsed as the float 15.0."""
    ns = replay_all._parse_args(["--fast-omori", "15"])
    assert replay_all._resolve_fast_omori(ns.fast_omori) == 15.0
