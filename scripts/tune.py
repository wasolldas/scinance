"""Optuna hyperparameter tuner CLI for the five Bybit-Edge strategies.

Drives :class:`bybit_edge.tuning.OptunaTuner` over the same DuckDB ticks
that the replay backtester uses. Writes a per-strategy summary JSON and
optionally persists each Optuna study as a SQLite DB so resumed runs can
build on prior trials.

Example
-------
Five-trial study of S3 only::

    python scripts/tune.py --strategy S3 --n-trials 5

All five strategies, default trials, custom DB / output paths::

    python scripts/tune.py --strategy all \\
        --db data/bybit_edge.duckdb \\
        --out edge_research_framework/results/tuning_results.json
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

from bybit_edge.config import (
    DB_PATH,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    LOG_LEVEL,
    PRIMARY_SYMBOL,
    WF_EMBARGO_MINUTES,
    WF_TEST_DAYS,
    WF_TRAIN_DAYS,
)
from bybit_edge.replay_backtester import ReplayBacktester
from bybit_edge.tuning.optuna_tuner import OptunaTuner
from bybit_edge.tuning.spaces import SPACES

_VALID_STRATS: tuple[str, ...] = ("S1", "S2", "S3", "S4", "S5")
_DEFAULT_OUT: Path = Path("edge_research_framework/results/tuning_results.json")
_DEFAULT_STUDY_DIR: Path = Path("data/tuning")


def _setup_logging() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Optuna walk-forward tuner over persisted DuckDB ticks. "
            "Optimises per-strategy Sharpe via TPE sampling."
        )
    )
    parser.add_argument(
        "--strategy",
        choices=[*_VALID_STRATS, "all"],
        default="all",
        help="Strategy id to tune, or 'all' to sweep every strategy.",
    )
    parser.add_argument("--symbol", default=PRIMARY_SYMBOL)
    parser.add_argument(
        "--db-path",
        default=str(DB_PATH),
        help=f"DuckDB path (default: {DB_PATH}).",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=50,
        help="Optuna trials per strategy.",
    )
    parser.add_argument("--train-days", type=int, default=WF_TRAIN_DAYS)
    parser.add_argument("--test-days", type=int, default=WF_TEST_DAYS)
    parser.add_argument(
        "--embargo-minutes", type=int, default=WF_EMBARGO_MINUTES
    )
    parser.add_argument(
        "--pipeline-interval",
        type=float,
        default=1.0,
        help="Pipeline throttle in seconds (mirrors the live runner).",
    )
    parser.add_argument(
        "--out",
        default=str(_DEFAULT_OUT),
        help=(
            "Output JSON file for the per-strategy best params / Sharpe."
        ),
    )
    parser.add_argument(
        "--study-dir",
        default=str(_DEFAULT_STUDY_DIR),
        help=(
            "Directory for persisted Optuna study SQLite files. Pass "
            "'-' to keep studies purely in-memory."
        ),
    )
    return parser.parse_args()


def _data_sufficient(n_events: int, train_days: int, test_days: int) -> tuple[bool, str]:
    """Sanity-check the loaded event count before kicking off Optuna.

    The walk-forward sweep needs at least one fold's worth of data. A
    very loose heuristic (100 events / day) flags catastrophically empty
    databases without falsely rejecting low-volume symbols.
    """
    min_events = 100 * max(1, train_days + test_days)
    if n_events < min_events:
        return False, (
            f"Only {n_events} events loaded but tuning needs at least "
            f"~{min_events} (covering {train_days + test_days} days). "
            "Collect more data first by running the LiveRunner with "
            "PERSIST_ENABLED=true for the requested window."
        )
    return True, ""


def _run_one(
    strategy_id: str,
    backtester: ReplayBacktester,
    args: argparse.Namespace,
    study_dir: Path | None,
) -> dict[str, Any]:
    space = SPACES.get(strategy_id, {})
    study_path: Path | None = None
    if study_dir is not None:
        study_path = study_dir / f"{strategy_id}.db"

    tuner = OptunaTuner(
        backtester=backtester,
        strategy_id=strategy_id,
        space=space,
        train_days=args.train_days,
        test_days=args.test_days,
        embargo_minutes=args.embargo_minutes,
        n_trials=args.n_trials,
        study_path=study_path,
        pipeline_interval_seconds=args.pipeline_interval,
    )
    summary = tuner.run()
    summary["space"] = space
    return summary


def main() -> int:
    _setup_logging()
    args = _parse_args()

    db_path = Path(args.db_path)
    out_path = Path(args.out)
    study_dir: Path | None
    if args.study_dir == "-":
        study_dir = None
    else:
        study_dir = Path(args.study_dir)

    strategies: list[str]
    if args.strategy == "all":
        strategies = list(_VALID_STRATS)
    else:
        strategies = [args.strategy]

    logging.info(
        "Tuning %s on symbol=%s db=%s n_trials=%d",
        strategies, args.symbol, db_path, args.n_trials,
    )

    bt = ReplayBacktester(symbol=args.symbol, db_path=db_path)
    n_events = bt.load_events()
    ok, msg = _data_sufficient(n_events, args.train_days, args.test_days)
    if not ok:
        logging.error(msg)
        bt.close()
        return 2

    started = time.time()
    results: dict[str, Any] = {
        "symbol": args.symbol,
        "db_path": str(db_path),
        "n_events": n_events,
        "n_trials": args.n_trials,
        "train_days": args.train_days,
        "test_days": args.test_days,
        "embargo_minutes": args.embargo_minutes,
        "strategies": {},
    }

    for sid in strategies:
        logging.info("=== Tuning %s ===", sid)
        summary = _run_one(sid, bt, args, study_dir)
        results["strategies"][sid] = summary
        logging.info(
            "%s | best_sharpe=%s | n_trials=%d | elapsed=%.1fs",
            sid,
            summary.get("best_value"),
            summary.get("n_trials"),
            summary.get("elapsed_seconds", 0.0),
        )

    results["total_elapsed_seconds"] = time.time() - started
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        json.dump(results, fh, indent=2, default=str)
    logging.info("Wrote tuning results -> %s", out_path)

    bt.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
