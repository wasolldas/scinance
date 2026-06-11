"""Metric extraction for the E-15 evaluation (hypothesis H-01, strategy S3).

Reads — strictly read-only — the multi-symbol replay artifacts produced by
``scripts/replay_all.py``:

- ``replay_all_results.json`` (per-strategy aggregates, per-symbol results and
  the ``diagnostics`` block with ``reason_counts`` per symbol/strategy), and
- the per-trade CSV export (``trades_all.csv``; columns: symbol, strategy,
  entry_ts, exit_ts, side, entry_price, exit_price, quantity, raw_pnl,
  entry_fee, exit_fee, pnl_net, pnl_bps; timestamps are epoch milliseconds).

It computes exactly the S3 metrics that the pre-registered H-01 gate
(``scinance2-impl/state/hypothesis_registry.md``) needs: trade counts, net and
raw (fees added back) edge in bps, exit-reason counters (``time_stop_exceeded``,
``hard_stop_loss``), holding-duration tails (>120 s) and loss tails (<-30 bps).
"""
from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

#: Strategy under test — H-01 is registered for S3 (pre-settlement) only.
STRATEGY_S3 = "S3"

#: Time-stop limit from the S3 fix (iter-5): 120 s market time.
TIME_STOP_LIMIT_SECONDS = 120.0

#: Hard-stop tail threshold from H-01: trades with net pnl below -30 bps.
TAIL_LOSS_THRESHOLD_BPS = -30.0

#: Exit-reason keys as emitted by strategy3_pre_settlement.py diagnostics.
REASON_TIME_STOP = "time_stop_exceeded"
REASON_HARD_STOP = "hard_stop_loss"

#: Required columns of the trades CSV (replay_all.py export schema).
TRADE_COLUMNS: tuple[str, ...] = (
    "symbol",
    "strategy",
    "entry_ts",
    "exit_ts",
    "side",
    "entry_price",
    "exit_price",
    "quantity",
    "raw_pnl",
    "entry_fee",
    "exit_fee",
    "pnl_net",
    "pnl_bps",
)


class DataError(RuntimeError):
    """Input data is missing, malformed or empty — maps to exit code 1."""


@dataclass(frozen=True)
class Trade:
    """One round-trip trade row from the replay trades CSV."""

    symbol: str
    strategy: str
    entry_ts: int  # epoch milliseconds
    exit_ts: int  # epoch milliseconds
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    raw_pnl: float
    entry_fee: float
    exit_fee: float
    pnl_net: float
    pnl_bps: float

    @property
    def duration_seconds(self) -> float:
        """Holding duration in market time (entry/exit are tick timestamps)."""
        return (self.exit_ts - self.entry_ts) / 1000.0

    @property
    def notional(self) -> float:
        return self.entry_price * self.quantity

    @property
    def raw_edge_bps(self) -> float:
        """Raw edge in bps: net PnL with entry+exit fees added back.

        ``raw_pnl`` in the CSV already equals ``pnl_net + entry_fee + exit_fee``;
        recomputing from the components keeps the metric honest even if one of
        the redundant columns drifts.
        """
        if self.notional == 0.0:
            return 0.0
        raw = self.pnl_net + self.entry_fee + self.exit_fee
        return raw / self.notional * 10_000.0


def load_results(path: Path) -> dict[str, Any]:
    """Load a ``replay_all_results.json`` file (read-only)."""
    if not path.is_file():
        raise DataError(f"results file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise DataError(f"cannot parse results JSON {path}: {exc}") from exc
    if not isinstance(data, dict) or "per_symbol" not in data:
        raise DataError(f"results JSON {path} lacks the 'per_symbol' block")
    return data


def load_trades(path: Path, strategy: str = STRATEGY_S3) -> list[Trade]:
    """Load all trades of ``strategy`` from a replay trades CSV (read-only)."""
    if not path.is_file():
        raise DataError(f"trades file not found: {path}")
    trades: list[Trade] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            header = reader.fieldnames or []
            missing = [c for c in TRADE_COLUMNS if c not in header]
            if missing:
                raise DataError(
                    f"trades CSV {path} is missing required columns: {missing}"
                )
            for lineno, row in enumerate(reader, start=2):
                if row.get("strategy") != strategy:
                    continue
                try:
                    trades.append(
                        Trade(
                            symbol=row["symbol"],
                            strategy=row["strategy"],
                            entry_ts=int(float(row["entry_ts"])),
                            exit_ts=int(float(row["exit_ts"])),
                            side=row["side"],
                            entry_price=float(row["entry_price"]),
                            exit_price=float(row["exit_price"]),
                            quantity=float(row["quantity"]),
                            raw_pnl=float(row["raw_pnl"]),
                            entry_fee=float(row["entry_fee"]),
                            exit_fee=float(row["exit_fee"]),
                            pnl_net=float(row["pnl_net"]),
                            pnl_bps=float(row["pnl_bps"]),
                        )
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise DataError(
                        f"trades CSV {path} line {lineno}: bad value ({exc})"
                    ) from exc
    except OSError as exc:
        raise DataError(f"cannot read trades CSV {path}: {exc}") from exc
    return trades


def extract_reason_counts(
    results: dict[str, Any], strategy: str = STRATEGY_S3
) -> Optional[dict[str, dict[str, int]]]:
    """Extract per-symbol ``reason_counts`` for ``strategy`` from diagnostics.

    Returns ``None`` when the results JSON has no ``diagnostics`` block at all
    (older schema) — callers must then report the criterion as not assessable
    instead of silently counting zero.
    """
    diagnostics = results.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return None
    out: dict[str, dict[str, int]] = {}
    for symbol, per_strategy in diagnostics.items():
        if not isinstance(per_strategy, dict):
            continue
        block = per_strategy.get(strategy)
        if not isinstance(block, dict):
            continue
        counts = block.get("reason_counts")
        if isinstance(counts, dict):
            out[symbol] = {str(k): int(v) for k, v in counts.items()}
    return out


def _trade_stats(trades: list[Trade]) -> dict[str, Any]:
    """Distribution statistics over a non-empty list of trades."""
    pnl_bps = [t.pnl_bps for t in trades]
    raw_bps = [t.raw_edge_bps for t in trades]
    durations = [t.duration_seconds for t in trades]
    worst = min(trades, key=lambda t: t.pnl_bps)
    return {
        "n_trades": len(trades),
        "mean_pnl_bps_net": statistics.fmean(pnl_bps),
        "median_pnl_bps_net": statistics.median(pnl_bps),
        "mean_raw_edge_bps": statistics.fmean(raw_bps),
        "median_raw_edge_bps": statistics.median(raw_bps),
        "sum_pnl_net": sum(t.pnl_net for t in trades),
        "sum_raw_pnl": sum(t.pnl_net + t.entry_fee + t.exit_fee for t in trades),
        "n_over_120s": sum(1 for d in durations if d > TIME_STOP_LIMIT_SECONDS),
        "n_below_minus_30bps": sum(
            1 for b in pnl_bps if b < TAIL_LOSS_THRESHOLD_BPS
        ),
        "max_duration_seconds": max(durations),
        "mean_duration_seconds": statistics.fmean(durations),
        "worst_trade": {
            "symbol": worst.symbol,
            "entry_ts": worst.entry_ts,
            "exit_ts": worst.exit_ts,
            "duration_seconds": worst.duration_seconds,
            "pnl_net": worst.pnl_net,
            "pnl_bps": worst.pnl_bps,
        },
    }


def compute_e15_metrics(
    trades: list[Trade], results: dict[str, Any], strategy: str = STRATEGY_S3
) -> dict[str, Any]:
    """Compute per-symbol and aggregate S3 metrics for the H-01 gate.

    Raises :class:`DataError` when no S3 trades are present — H-01 expects a
    populated 5-symbol replay; an empty trade set is a data defect, not a
    verdict.
    """
    if not trades:
        raise DataError(f"no {strategy} trades found in trades CSV — cannot evaluate H-01")

    reason_counts = extract_reason_counts(results, strategy)

    per_symbol: dict[str, dict[str, Any]] = {}
    for symbol in sorted({t.symbol for t in trades}):
        sym_trades = [t for t in trades if t.symbol == symbol]
        stats = _trade_stats(sym_trades)
        if reason_counts is None:
            stats["time_stop_exceeded_count"] = None
            stats["hard_stop_loss_count"] = None
        else:
            counts = reason_counts.get(symbol, {})
            stats["time_stop_exceeded_count"] = counts.get(REASON_TIME_STOP, 0)
            stats["hard_stop_loss_count"] = counts.get(REASON_HARD_STOP, 0)
        per_symbol[symbol] = stats

    aggregate = _trade_stats(trades)
    if reason_counts is None:
        aggregate["time_stop_exceeded_count"] = None
        aggregate["hard_stop_loss_count"] = None
    else:
        aggregate["time_stop_exceeded_count"] = sum(
            counts.get(REASON_TIME_STOP, 0) for counts in reason_counts.values()
        )
        aggregate["hard_stop_loss_count"] = sum(
            counts.get(REASON_HARD_STOP, 0) for counts in reason_counts.values()
        )

    # Cross-check trade count against the results JSON aggregate (if present);
    # a mismatch is reported, not fatal — the trades CSV is the ground truth.
    warnings: list[str] = []
    json_agg = results.get("per_strategy_aggregate", {}).get(strategy, {})
    json_n = json_agg.get("total_trades")
    if isinstance(json_n, int) and json_n != aggregate["n_trades"]:
        warnings.append(
            f"trade-count mismatch: results JSON reports {json_n} {strategy} "
            f"trades, trades CSV contains {aggregate['n_trades']}"
        )

    return {
        "strategy": strategy,
        "per_symbol": per_symbol,
        "aggregate": aggregate,
        "diagnostics_available": reason_counts is not None,
        "warnings": warnings,
    }
