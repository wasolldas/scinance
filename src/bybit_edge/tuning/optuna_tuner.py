# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""Optuna-driven walk-forward hyperparameter tuner.

This module is the ONLY place in :mod:`bybit_edge.tuning` that imports
``optuna``. Keeping the import here (rather than at package level) lets
the package be used in non-tuning contexts even when the optional
``[tuning]`` extra is not installed.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

from bybit_edge.config import RANDOM_SEED
from bybit_edge.replay_backtester import ReplayBacktester
from bybit_edge.tuning.spaces import sample_from_space

logger = logging.getLogger(__name__)

# Penalty score assigned when a trial yields zero trades or otherwise
# fails. Chosen low enough that any valid Sharpe (typically in [-3, 3])
# wins, but finite so Optuna does not refuse to update its TPE model.
_ZERO_TRADE_PENALTY: float = -100.0


class OptunaTuner:
    """Walk-forward Sharpe-maximising tuner over the persisted DuckDB ticks.

    The tuner samples a trial parameter dict from ``space``, hands it to
    :meth:`ReplayBacktester.run_walkforward` as ``param_overrides``, and
    returns the resulting test-fold Sharpe of ``strategy_id``.

    Reproducibility
    ---------------
    The TPE sampler is seeded from :data:`bybit_edge.config.RANDOM_SEED`
    so consecutive runs with identical data + spaces produce identical
    sample sequences.
    """

    def __init__(
        self,
        backtester: ReplayBacktester,
        strategy_id: str,
        space: dict[str, dict[str, Any]],
        train_days: int,
        test_days: int,
        embargo_minutes: int,
        n_trials: int = 50,
        study_path: Optional[Path] = None,
        pipeline_interval_seconds: float = 1.0,
        min_train_events: int = 100,
    ) -> None:
        self.backtester: ReplayBacktester = backtester
        self.strategy_id: str = strategy_id
        self.space: dict[str, dict[str, Any]] = space
        self.train_days: int = int(train_days)
        self.test_days: int = int(test_days)
        self.embargo_minutes: int = int(embargo_minutes)
        self.n_trials: int = int(n_trials)
        self.study_path: Optional[Path] = study_path
        self.pipeline_interval_seconds: float = float(pipeline_interval_seconds)
        self.min_train_events: int = int(min_train_events)

    # ------------------------------------------------------------------
    # Objective
    # ------------------------------------------------------------------
    def objective(self, trial: Any) -> float:
        """Run one walk-forward replay under sampled parameters; return Sharpe.

        Returns the test-fold Sharpe of ``self.strategy_id``. When the
        configuration produces zero trades the trial is heavily penalised
        (see :data:`_ZERO_TRADE_PENALTY`) so the TPE sampler steers away
        from inert regions of the search space.
        """
        params = sample_from_space(trial, self.space)
        try:
            results = self.backtester.run_walkforward(
                pipeline_interval_seconds=self.pipeline_interval_seconds,
                train_days=self.train_days,
                test_days=self.test_days,
                embargo_minutes=self.embargo_minutes,
                min_train_events=self.min_train_events,
                param_overrides=params,
            )
        except Exception:
            # A bad parameter combination must not crash the whole study —
            # log loudly and treat as the worst possible outcome instead.
            logger.exception(
                "Trial %d crashed under params=%s — penalised.",
                getattr(trial, "number", -1), params,
            )
            return _ZERO_TRADE_PENALTY

        result = results.get(self.strategy_id)
        if result is None or result.n_trades == 0:
            logger.info(
                "Trial %d: strategy %s produced 0 trades under %s — penalty.",
                getattr(trial, "number", -1), self.strategy_id, params,
            )
            return _ZERO_TRADE_PENALTY

        sharpe = float(result.sharpe)
        logger.info(
            "Trial %d | %s | sharpe=%.4f | n_trades=%d | params=%s",
            getattr(trial, "number", -1),
            self.strategy_id,
            sharpe,
            result.n_trades,
            params,
        )
        return sharpe

    # ------------------------------------------------------------------
    # Driver
    # ------------------------------------------------------------------
    def run(self) -> dict[str, Any]:
        """Create a study, run ``n_trials`` trials, return a summary dict.

        Returns
        -------
        dict with keys ``best_params``, ``best_value``, ``n_trials``,
        ``strategy_id``, ``study_path``, ``elapsed_seconds``.
        """
        import optuna  # local import — ``[tuning]`` extra is optional.

        if not self.space:
            # No tunable surface — nothing to do. Return a sentinel result
            # so callers can iterate over strategies uniformly.
            logger.warning(
                "Strategy %s has no tunable parameters — skipping study.",
                self.strategy_id,
            )
            return {
                "strategy_id": self.strategy_id,
                "best_params": {},
                "best_value": float("nan"),
                "n_trials": 0,
                "study_path": str(self.study_path) if self.study_path else None,
                "elapsed_seconds": 0.0,
                "skipped": True,
            }

        sampler = optuna.samplers.TPESampler(seed=RANDOM_SEED)
        storage: Optional[str]
        if self.study_path is not None:
            self.study_path.parent.mkdir(parents=True, exist_ok=True)
            storage = f"sqlite:///{self.study_path}"
        else:
            storage = None

        study_name = f"tune_{self.strategy_id}"
        study = optuna.create_study(
            study_name=study_name,
            direction="maximize",
            sampler=sampler,
            storage=storage,
            load_if_exists=storage is not None,
        )

        start = time.time()
        study.optimize(self.objective, n_trials=self.n_trials, gc_after_trial=True)
        elapsed = time.time() - start

        best_trial = study.best_trial
        return {
            "strategy_id": self.strategy_id,
            "best_params": dict(best_trial.params),
            "best_value": float(best_trial.value)
            if best_trial.value is not None
            else float("nan"),
            "n_trials": len(study.trials),
            "study_path": str(self.study_path) if self.study_path else None,
            "elapsed_seconds": elapsed,
            "skipped": False,
        }
