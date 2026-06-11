"""
Unit tests for the E-15 evaluation tooling (WP-1 / hypothesis H-01).

Covers, network-free and read-only on inputs:

- the registered H-01 gate table (WEITER / DROP / GRAUBEREICH, exact bounds),
- metric extraction on a synthetic trade set with hand-computed values
  (net/raw bps, >120 s and <-30 bps tail boundaries are strict),
- S2/S3 filtering of the trades CSV,
- the E-17 divergence check (known ratios, missing baseline -> inconclusive),
- end-to-end CLI runs over the three verdict fixtures
  (``tests/fixtures/e15/{weiter,drop,grau}``),
- a regression against the real iter-4 artifacts
  (``edge-reconciliation/input/iter4_raw/``, read-only), and
- robustness: defective inputs exit with code 1 and a clean message,
  never a traceback.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pytest

import scripts.evaluate_e15 as evaluate_e15
from bybit_edge.research.e15_eval import (
    DataError,
    Trade,
    check_e17,
    compute_e15_metrics,
    evaluate_h01_gate,
    extract_reason_counts,
    load_results,
    load_trades,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "e15"
ITER4_DIR = REPO_ROOT / "edge-reconciliation" / "input" / "iter4_raw"

_BASE_TS = 1_781_000_000_000
TRADES_HEADER = (
    "symbol,strategy,entry_ts,exit_ts,side,entry_price,exit_price,"
    "quantity,raw_pnl,entry_fee,exit_fee,pnl_net,pnl_bps"
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _aggregate(
    mean_net_bps: float,
    *,
    time_stop_count: Optional[int] = 65,
    n_over_120s: int = 0,
    n_below_minus_30bps: int = 0,
) -> dict[str, Any]:
    """Minimal aggregate block as produced by ``compute_e15_metrics``."""
    return {
        "mean_pnl_bps_net": mean_net_bps,
        "time_stop_exceeded_count": time_stop_count,
        "n_over_120s": n_over_120s,
        "n_below_minus_30bps": n_below_minus_30bps,
    }


def _trade_row(
    symbol: str,
    strategy: str,
    entry_ts: int,
    duration_ms: int,
    pnl_net: float,
    *,
    entry_fee: float = 0.05,
    exit_fee: float = 0.05,
    entry_price: float = 100.0,
    quantity: float = 1.0,
) -> str:
    """One CSV row; notional 100 -> pnl_bps == pnl_net * 100 by construction."""
    raw_pnl = pnl_net + entry_fee + exit_fee
    pnl_bps = pnl_net / (entry_price * quantity) * 10_000.0
    exit_price = entry_price + raw_pnl / quantity
    return (
        f"{symbol},{strategy},{entry_ts},{entry_ts + duration_ms},Long,"
        f"{entry_price},{exit_price},{quantity},{raw_pnl},"
        f"{entry_fee},{exit_fee},{pnl_net},{pnl_bps}"
    )


def _write_trades_csv(path: Path, rows: list[str]) -> Path:
    path.write_text("\n".join([TRADES_HEADER, *rows]) + "\n", encoding="utf-8")
    return path


def _results_json(
    *,
    total_return: float = -1.0,
    total_trades: int = 4,
    per_symbol: Optional[dict[str, dict[str, float | int]]] = None,
    diagnostics: Optional[dict[str, dict[str, int]]] = None,
    include_diagnostics: bool = True,
) -> dict[str, Any]:
    """Minimal ``replay_all_results.json`` dict in the real schema."""
    per_symbol = per_symbol or {}
    data: dict[str, Any] = {
        "mode": "single_pass",
        "symbols": sorted(per_symbol) or ["BTCUSDT"],
        "per_strategy_aggregate": {
            "S3": {"total_trades": total_trades, "total_return": total_return}
        },
        "per_symbol": {
            sym: {"S3": dict(block)} for sym, block in per_symbol.items()
        },
    }
    if include_diagnostics:
        data["diagnostics"] = {
            sym: {"S3": {"reason_counts": dict(counts)}}
            for sym, counts in (diagnostics or {}).items()
        }
    return data


def _write_results_json(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ----------------------------------------------------------------------
# 1. Gate logic table (H-01, registered bounds — exact)
# ----------------------------------------------------------------------

@pytest.mark.parametrize(
    ("mean_net_bps", "e17_resolved", "expected"),
    [
        # WEITER: net >= -5 AND e17 resolved (boundary -5.0 is inclusive)
        (-4.0, True, "WEITER"),
        (-5.0, True, "WEITER"),
        (0.0, True, "WEITER"),
        # net fine but E-17 open -> GRAUBEREICH (never WEITER)
        (-4.0, False, "GRAUBEREICH"),
        (-5.0, False, "GRAUBEREICH"),
        (-5.0, "inconclusive", "GRAUBEREICH"),
        # between the posts -> GRAUBEREICH regardless of E-17
        (-7.0, True, "GRAUBEREICH"),
        (-7.0, False, "GRAUBEREICH"),
        (-5.01, True, "GRAUBEREICH"),
        (-9.99, True, "GRAUBEREICH"),
        (-9.99, False, "GRAUBEREICH"),
        # DROP: net <= -10 (boundary -10.0 inclusive, beats E-17)
        (-10.0, True, "DROP"),
        (-10.0, False, "DROP"),
        (-10.01, True, "DROP"),
        (-10.01, False, "DROP"),
        (-16.81, True, "DROP"),
    ],
)
def test_h01_gate_verdict_table(
    mean_net_bps: float, e17_resolved: Any, expected: str
) -> None:
    gate = evaluate_h01_gate(_aggregate(mean_net_bps), e17_resolved)
    assert gate["gate_verdict"] == expected
    assert gate["aggregate_net_edge_bps"] == pytest.approx(mean_net_bps)


def test_h01_gate_details_carry_registry_criteria() -> None:
    gate = evaluate_h01_gate(_aggregate(-4.0), True)
    ids = {d["id"] for d in gate["gate_details"]}
    assert {
        "fix_time_stop_count",
        "fix_n_over_120s",
        "fix_n_below_minus_30bps",
        "weiter_net_edge",
        "weiter_e17_resolved",
        "drop_net_edge",
    } <= ids


def test_h01_fix_effectiveness_reported_but_not_verdict_flipping() -> None:
    # All three fix expectations FAIL (old iter-4 pattern), but net edge and
    # E-17 are fine -> verdict stays WEITER; fix_effectiveness_pass is False.
    gate = evaluate_h01_gate(
        _aggregate(-4.0, time_stop_count=1, n_over_120s=68, n_below_minus_30bps=33),
        True,
    )
    assert gate["gate_verdict"] == "WEITER"
    assert gate["fix_effectiveness_pass"] is False


def test_h01_gate_missing_diagnostics_yields_none_not_crash() -> None:
    gate = evaluate_h01_gate(_aggregate(-7.0, time_stop_count=None), True)
    assert gate["gate_verdict"] == "GRAUBEREICH"
    assert gate["fix_effectiveness_pass"] is None
    ts = next(d for d in gate["gate_details"] if d["id"] == "fix_time_stop_count")
    assert ts["passed"] is None


# ----------------------------------------------------------------------
# 2. Metrics on a synthetic trade set with hand-computed values
# ----------------------------------------------------------------------

def _synthetic_trades_csv(tmp_path: Path) -> Path:
    rows = [
        # S2 noise row: must NOT enter any S3 metric.
        _trade_row("BTCUSDT", "S2", _BASE_TS, 5_000, 9.99),
        # S3 #1: duration exactly 120.0 s -> NOT counted as >120s.
        _trade_row("BTCUSDT", "S3", _BASE_TS + 10_000, 120_000, 0.10),
        # S3 #2: duration 120.001 s -> counted as >120s.
        _trade_row("BTCUSDT", "S3", _BASE_TS + 200_000, 120_001, -0.20),
        # S3 #3: pnl exactly -30.0 bps -> NOT counted as <-30bps.
        _trade_row("ETHUSDT", "S3", _BASE_TS + 400_000, 60_000, -0.30),
        # S3 #4: pnl -30.01 bps -> counted as <-30bps.
        _trade_row("ETHUSDT", "S3", _BASE_TS + 600_000, 30_000, -0.3001),
    ]
    return _write_trades_csv(tmp_path / "trades_all.csv", rows)


def _synthetic_results(include_diagnostics: bool = True) -> dict[str, Any]:
    return _results_json(
        total_return=-0.7001,
        total_trades=4,
        per_symbol={
            "BTCUSDT": {"total_return": -0.10, "n_trades": 2},
            "ETHUSDT": {"total_return": -0.6001, "n_trades": 2},
        },
        diagnostics={
            "BTCUSDT": {"time_stop_exceeded": 5, "hard_stop_loss": 2},
            "ETHUSDT": {"time_stop_exceeded": 3, "hard_stop_loss": 0},
        },
        include_diagnostics=include_diagnostics,
    )


def test_metrics_synthetic_known_values(tmp_path: Path) -> None:
    trades = load_trades(_synthetic_trades_csv(tmp_path))
    metrics = compute_e15_metrics(trades, _synthetic_results())
    agg = metrics["aggregate"]

    assert agg["n_trades"] == 4
    # pnl_bps: 10.0, -20.0, -30.0, -30.01
    assert agg["mean_pnl_bps_net"] == pytest.approx(-70.01 / 4)
    assert agg["median_pnl_bps_net"] == pytest.approx(-25.0)
    # raw edge = (pnl_net + entry_fee + exit_fee) / notional * 1e4:
    # 20.0, -10.0, -20.0, -20.01 bps
    assert agg["mean_raw_edge_bps"] == pytest.approx(-30.01 / 4)
    assert agg["median_raw_edge_bps"] == pytest.approx(-15.0)
    assert agg["sum_pnl_net"] == pytest.approx(-0.7001)
    # fees add back 4 * 0.10
    assert agg["sum_raw_pnl"] == pytest.approx(-0.3001)
    # boundary semantics: exactly 120.0 s does NOT count, 120.001 s does.
    assert agg["n_over_120s"] == 1
    assert agg["max_duration_seconds"] == pytest.approx(120.001)
    # boundary semantics: exactly -30.0 bps does NOT count, -30.01 does.
    assert agg["n_below_minus_30bps"] == 1
    # diagnostics counters summed over symbols
    assert agg["time_stop_exceeded_count"] == 8
    assert agg["hard_stop_loss_count"] == 2
    assert metrics["diagnostics_available"] is True
    assert metrics["warnings"] == []
    # worst trade is the -30.01 bps ETH trade
    assert agg["worst_trade"]["symbol"] == "ETHUSDT"
    assert agg["worst_trade"]["pnl_bps"] == pytest.approx(-30.01)


def test_metrics_per_symbol_split(tmp_path: Path) -> None:
    trades = load_trades(_synthetic_trades_csv(tmp_path))
    metrics = compute_e15_metrics(trades, _synthetic_results())
    per_symbol = metrics["per_symbol"]
    assert set(per_symbol) == {"BTCUSDT", "ETHUSDT"}
    assert per_symbol["BTCUSDT"]["n_trades"] == 2
    assert per_symbol["BTCUSDT"]["mean_pnl_bps_net"] == pytest.approx(-5.0)
    assert per_symbol["BTCUSDT"]["time_stop_exceeded_count"] == 5
    assert per_symbol["ETHUSDT"]["hard_stop_loss_count"] == 0


def test_raw_edge_recomputed_from_components() -> None:
    # raw_pnl column is IGNORED; raw edge must come from pnl_net + fees.
    trade = Trade(
        symbol="BTCUSDT",
        strategy="S3",
        entry_ts=_BASE_TS,
        exit_ts=_BASE_TS + 1_000,
        side="Long",
        entry_price=200.0,
        exit_price=200.0,
        quantity=0.5,  # notional 100
        raw_pnl=999.0,  # deliberately inconsistent
        entry_fee=0.03,
        exit_fee=0.02,
        pnl_net=-0.10,
        pnl_bps=-10.0,
    )
    assert trade.raw_edge_bps == pytest.approx((-0.10 + 0.05) / 100.0 * 10_000.0)
    assert trade.duration_seconds == pytest.approx(1.0)


# ----------------------------------------------------------------------
# 3. S2/S3 filtering
# ----------------------------------------------------------------------

def test_load_trades_filters_to_s3_only(tmp_path: Path) -> None:
    trades = load_trades(_synthetic_trades_csv(tmp_path))
    assert len(trades) == 4
    assert {t.strategy for t in trades} == {"S3"}
    # The S2 row carried +9.99 USD; no S3 metric may contain it.
    metrics = compute_e15_metrics(trades, _synthetic_results())
    assert metrics["aggregate"]["sum_pnl_net"] == pytest.approx(-0.7001)


def test_load_trades_s2_only_csv_yields_empty_and_metrics_refuse(
    tmp_path: Path,
) -> None:
    csv_path = _write_trades_csv(
        tmp_path / "trades_all.csv",
        [_trade_row("BTCUSDT", "S2", _BASE_TS, 5_000, 0.01)],
    )
    trades = load_trades(csv_path)
    assert trades == []
    with pytest.raises(DataError):
        compute_e15_metrics(trades, _synthetic_results())


# ----------------------------------------------------------------------
# 4. E-17 divergence check
# ----------------------------------------------------------------------

def test_e17_known_ratios_resolved_true() -> None:
    current = _results_json(total_return=-100.0, total_trades=100)
    baseline = _results_json(total_return=-80.0, total_trades=100)
    out = check_e17(current, [], baseline)
    assert out["resolved"] is True
    assert out["details"]["trades_ratio"] == pytest.approx(1.0)
    assert out["details"]["return_ratio_abs"] == pytest.approx(100.0 / 80.0)
    assert out["details"]["total_return_gap"] == pytest.approx(-20.0)


def test_e17_unexplained_divergence_resolved_false() -> None:
    # Same trade count, ~3.2x return gap spread evenly over two symbols:
    # neither symbol concentration nor tail trades explain it -> False.
    current = _results_json(
        total_return=-320.0,
        total_trades=100,
        per_symbol={
            "BTCUSDT": {"total_return": -160.0, "n_trades": 50},
            "ETHUSDT": {"total_return": -160.0, "n_trades": 50},
        },
    )
    baseline = _results_json(
        total_return=-100.0,
        total_trades=100,
        per_symbol={
            "BTCUSDT": {"total_return": -50.0, "n_trades": 50},
            "ETHUSDT": {"total_return": -50.0, "n_trades": 50},
        },
    )
    out = check_e17(current, [], baseline)
    assert out["resolved"] is False
    assert out["details"]["return_ratio_abs"] == pytest.approx(3.2)
    assert out["details"]["top_gap_symbol"]["share_of_abs_gap"] == pytest.approx(0.5)


def test_e17_missing_baseline_is_inconclusive_not_crash() -> None:
    current = _results_json(total_return=-100.0, total_trades=100)
    out = check_e17(current, [], baseline_results=None)
    assert out["resolved"] == "inconclusive"
    assert "Baseline" in out["reasoning"]
    # the registered ~3.2x reference numbers must still be reported
    assert out["details"]["registered_divergence"]["ratio"] == pytest.approx(3.24)


def test_e17_inconclusive_blocks_weiter() -> None:
    gate = evaluate_h01_gate(_aggregate(-4.0), "inconclusive")
    assert gate["gate_verdict"] == "GRAUBEREICH"


# ----------------------------------------------------------------------
# 5. Fixture end-to-end through the CLI main()
# ----------------------------------------------------------------------

@pytest.mark.parametrize(
    ("fixture", "expected_verdict"),
    [("weiter", "WEITER"), ("drop", "DROP"), ("grau", "GRAUBEREICH")],
)
def test_cli_end_to_end_fixture_verdicts(
    fixture: str, expected_verdict: str, tmp_path: Path
) -> None:
    fdir = FIXTURE_DIR / fixture
    argv = [
        "--results-path", str(fdir / "replay_all_results.json"),
        "--trades-path", str(fdir / "trades_all.csv"),
        "--out", str(tmp_path),
    ]
    baseline = fdir / "baseline_results.json"
    if baseline.is_file():
        argv += ["--baseline-results", str(baseline)]

    rc = evaluate_e15.main(argv)
    assert rc == 0

    json_path = tmp_path / "e15_evaluation.json"
    md_path = tmp_path / "e15_evaluation.md"
    assert json_path.is_file()
    assert md_path.is_file()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["gate_verdict"] == expected_verdict
    # H-01 registry reference must be carried in the machine artifact.
    assert payload["hypothesis"] == "H-01"
    assert "hypothesis_registry" in payload
    assert payload["metrics"]["strategy"] == "S3"
    # Markdown carries verdict + hypothesis for the gate-auditor.
    md = md_path.read_text(encoding="utf-8")
    assert expected_verdict in md
    assert "H-01" in md


def test_cli_weiter_fixture_requires_resolved_e17(tmp_path: Path) -> None:
    # Same WEITER-net-edge fixture WITHOUT baseline -> E-17 inconclusive
    # -> verdict degrades to GRAUBEREICH.
    fdir = FIXTURE_DIR / "weiter"
    rc = evaluate_e15.main(
        [
            "--results-path", str(fdir / "replay_all_results.json"),
            "--trades-path", str(fdir / "trades_all.csv"),
            "--out", str(tmp_path),
        ]
    )
    assert rc == 0
    payload = json.loads(
        (tmp_path / "e15_evaluation.json").read_text(encoding="utf-8")
    )
    assert payload["e17_resolved"] == "inconclusive"
    assert payload["gate_verdict"] == "GRAUBEREICH"


# ----------------------------------------------------------------------
# 6. Real-data regression (iter-4 artifacts, read-only)
# ----------------------------------------------------------------------

@pytest.mark.skipif(
    not (ITER4_DIR / "replay_all_results.json").is_file()
    or not (ITER4_DIR / "trades_all.csv").is_file(),
    reason="iter-4 reference artifacts not present",
)
def test_real_iter4_regression_reference_numbers(tmp_path: Path) -> None:
    results = load_results(ITER4_DIR / "replay_all_results.json")
    trades = load_trades(ITER4_DIR / "trades_all.csv")
    metrics = compute_e15_metrics(trades, results)
    agg = metrics["aggregate"]

    # Frozen reference numbers (H-01 registration / builder smoke):
    assert agg["n_trades"] == 213
    assert agg["mean_pnl_bps_net"] == pytest.approx(-16.81, abs=0.01)
    assert agg["mean_raw_edge_bps"] == pytest.approx(-5.81, abs=0.01)
    assert agg["n_over_120s"] == 68
    assert agg["n_below_minus_30bps"] == 33
    assert agg["time_stop_exceeded_count"] == 1
    # trades CSV count matches the results JSON aggregate -> no warnings
    assert metrics["warnings"] == []

    # And the gate on the old iter-4 numbers must be DROP (net -16.81).
    gate = evaluate_h01_gate(agg, check_e17(results, trades)["resolved"])
    assert gate["gate_verdict"] == "DROP"

    # Full CLI pass over the real data stays exit 0 and writes both artifacts.
    rc = evaluate_e15.main(
        [
            "--results-path", str(ITER4_DIR / "replay_all_results.json"),
            "--trades-path", str(ITER4_DIR / "trades_all.csv"),
            "--out", str(tmp_path),
        ]
    )
    assert rc == 0
    payload = json.loads(
        (tmp_path / "e15_evaluation.json").read_text(encoding="utf-8")
    )
    assert payload["gate_verdict"] == "DROP"
    assert payload["hypothesis"] == "H-01"


# ----------------------------------------------------------------------
# 7. Robustness: defective inputs -> exit code 1, clean message, no traceback
# ----------------------------------------------------------------------

def _run_main_expect_data_error(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> str:
    rc = evaluate_e15.main(argv)
    assert rc == 1
    err = capsys.readouterr().err
    assert "E15-EVAL DATENDEFEKT" in err
    assert "Traceback" not in err
    return err


def test_cli_empty_trades_csv_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    results = _write_results_json(
        tmp_path / "replay_all_results.json", _synthetic_results()
    )
    empty_csv = _write_trades_csv(tmp_path / "trades_all.csv", [])
    err = _run_main_expect_data_error(
        [
            "--results-path", str(results),
            "--trades-path", str(empty_csv),
            "--out", str(tmp_path / "out"),
        ],
        capsys,
    )
    assert "no S3 trades" in err
    assert not (tmp_path / "out" / "e15_evaluation.json").exists()


def test_cli_missing_results_file_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    csv_path = _synthetic_trades_csv(tmp_path)
    _run_main_expect_data_error(
        [
            "--results-path", str(tmp_path / "does_not_exist.json"),
            "--trades-path", str(csv_path),
            "--out", str(tmp_path / "out"),
        ],
        capsys,
    )


def test_cli_results_without_per_symbol_block_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "replay_all_results.json"
    bad.write_text(json.dumps({"mode": "single_pass"}), encoding="utf-8")
    csv_path = _synthetic_trades_csv(tmp_path)
    err = _run_main_expect_data_error(
        [
            "--results-path", str(bad),
            "--trades-path", str(csv_path),
            "--out", str(tmp_path / "out"),
        ],
        capsys,
    )
    assert "per_symbol" in err


def test_cli_malformed_results_json_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "replay_all_results.json"
    bad.write_text("{not valid json", encoding="utf-8")
    csv_path = _synthetic_trades_csv(tmp_path)
    _run_main_expect_data_error(
        [
            "--results-path", str(bad),
            "--trades-path", str(csv_path),
            "--out", str(tmp_path / "out"),
        ],
        capsys,
    )


def test_cli_trades_csv_missing_columns_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    results = _write_results_json(
        tmp_path / "replay_all_results.json", _synthetic_results()
    )
    bad_csv = tmp_path / "trades_all.csv"
    bad_csv.write_text("symbol,strategy\nBTCUSDT,S3\n", encoding="utf-8")
    err = _run_main_expect_data_error(
        [
            "--results-path", str(results),
            "--trades-path", str(bad_csv),
            "--out", str(tmp_path / "out"),
        ],
        capsys,
    )
    assert "missing required columns" in err


def test_cli_trades_csv_bad_value_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    results = _write_results_json(
        tmp_path / "replay_all_results.json", _synthetic_results()
    )
    bad_row = _trade_row("BTCUSDT", "S3", _BASE_TS, 1_000, 0.1).replace(
        "100.0,", "not_a_number,", 1
    )
    bad_csv = _write_trades_csv(tmp_path / "trades_all.csv", [bad_row])
    err = _run_main_expect_data_error(
        [
            "--results-path", str(results),
            "--trades-path", str(bad_csv),
            "--out", str(tmp_path / "out"),
        ],
        capsys,
    )
    assert "line 2" in err


def test_missing_diagnostics_block_is_tolerated_no_crash(tmp_path: Path) -> None:
    # Older results schema without ANY diagnostics block: documented design is
    # "not assessable" (None) — the evaluation still completes (exit 0); the
    # fix-effectiveness criteria report None instead of fake zeros.
    results = _synthetic_results(include_diagnostics=False)
    assert extract_reason_counts(results) is None
    trades = load_trades(_synthetic_trades_csv(tmp_path))
    metrics = compute_e15_metrics(trades, results)
    assert metrics["diagnostics_available"] is False
    assert metrics["aggregate"]["time_stop_exceeded_count"] is None
    assert metrics["aggregate"]["hard_stop_loss_count"] is None

    results_path = _write_results_json(tmp_path / "replay_all_results.json", results)
    rc = evaluate_e15.main(
        [
            "--results-path", str(results_path),
            "--trades-path", str(tmp_path / "trades_all.csv"),
            "--out", str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    payload = json.loads(
        (tmp_path / "out" / "e15_evaluation.json").read_text(encoding="utf-8")
    )
    assert payload["fix_effectiveness_pass"] is None
