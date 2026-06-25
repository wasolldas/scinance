# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""Per-strategy hyperparameter search spaces.

Each entry in :data:`SPACES` maps a strategy id (``"S1".."S5"``) to a dict of
``{config_attribute_name: spec}``. Each ``spec`` is a plain dict so the whole
table is JSON-serialisable and trivially inspectable from the CLI / notebooks
without an Optuna dependency.

Supported spec shapes
---------------------
``{"type": "float", "low": x, "high": y, "log": False, "step": None}``
``{"type": "int",   "low": x, "high": y, "step": 1}``
``{"type": "categorical", "choices": [...]}``

Range rationale
---------------
Bounds bracket the PRD defaults by a factor of ~2-3 each side, anchored at
values that remain economically meaningful (e.g. quantiles stay in (0, 1),
windows stay positive). Every name has been cross-checked against
:mod:`bybit_edge.config` to ensure spelling matches.

Notes per strategy
------------------
S1 (Cascade Detector): tunes the Hawkes critical-rho / window and the GR
mainshock quantile.
S2 (Entropy-Momentum): tunes the entropy greenlight quantile, OFI window /
quantile, and permutation-entropy window. Real testability of S2 requires
persisted L2 snapshots in the DuckDB; otherwise S2 effectively never
triggers and the tuner will reject the configuration via the zero-trade
penalty in :mod:`bybit_edge.tuning.optuna_tuner`.
S3 (Pre-Settlement): tunes pressure z-score, pressure quantile, the entry
window (made tunable via the strategy-3 runtime shim), and the basis
thresholds.
S4 (Pattern Ensemble): the strategy depends on trained Foundation models
(M18 / M20) and on a long denoised price series. With untrained defaults
in a replay backtest it produces no actionable signals, so its tunable
surface is empty. Listed for completeness.
S5 (Cross-Sectional Reversion): needs a multi-symbol panel that the
single-symbol replay does not provide. Listed with its theoretical tunable
parameters for use once multi-symbol replay is wired up.
"""
from __future__ import annotations

from typing import Any


SPACES: dict[str, dict[str, dict[str, Any]]] = {
    # ─────────────────────────── S1 ────────────────────────────────────
    "S1": {
        "HAWKES_CRITICAL_RHO": {"type": "float", "low": 0.70, "high": 0.95},
        "HAWKES_WINDOW_SECONDS": {
            "type": "int", "low": 60, "high": 600, "step": 30,
        },
        "GR_MAINSHOCK_QUANTILE": {
            "type": "float", "low": 0.95, "high": 0.999,
        },
        "S1_RHO_ENTRY": {"type": "float", "low": 0.70, "high": 0.95},
        "S1_RHO_EXIT": {"type": "float", "low": 0.30, "high": 0.70},
    },
    # ─────────────────────────── S2 ────────────────────────────────────
    "S2": {
        "ENTROPY_GREENLIGHT_QUANTILE": {
            "type": "float", "low": 0.02, "high": 0.20,
        },
        "OFI_QUANTILE_THRESHOLD": {
            "type": "float", "low": 0.85, "high": 0.99,
        },
        "OFI_WINDOW_SECONDS": {"type": "int", "low": 1, "high": 30},
        "PE_WINDOW_TICKS": {
            "type": "int", "low": 50, "high": 400, "step": 50,
        },
        "S2_ENTROPY_ZSCORE": {"type": "float", "low": 1.0, "high": 3.0},
    },
    # ─────────────────────────── S3 ────────────────────────────────────
    "S3": {
        "PRESSURE_ZSCORE_THRESHOLD": {
            "type": "float", "low": 1.0, "high": 3.0,
        },
        "PRESSURE_ENTRY_WINDOW_MINUTES": {
            "type": "int", "low": 10, "high": 60, "step": 5,
        },
        "S3_PRESSURE_QUANTILE": {
            "type": "float", "low": 0.80, "high": 0.98,
        },
        "BASIS_LONG_THRESHOLD": {
            "type": "float", "low": -0.002, "high": -0.0002,
        },
        "BASIS_SHORT_THRESHOLD": {
            "type": "float", "low": 0.0002, "high": 0.002,
        },
    },
    # ─────────────────────────── S4 ────────────────────────────────────
    # No tunable surface in single-symbol replay without trained foundation
    # models. Kept as an explicit empty dict so the tuner CLI can iterate
    # over SPACES.items() without special-casing.
    "S4": {},
    # ─────────────────────────── S5 ────────────────────────────────────
    "S5": {
        "CSZ_Z_THRESHOLD": {"type": "float", "low": 1.5, "high": 3.5},
        "CSZ_WINDOW_HOURS": {"type": "int", "low": 1, "high": 24},
        "RENYI_TE_THRESHOLD": {
            "type": "float", "low": 0.01, "high": 0.10,
        },
        "S5_Z_ENTRY": {"type": "float", "low": 1.5, "high": 3.5},
        "S5_Z_EXIT": {"type": "float", "low": 0.1, "high": 1.0},
    },
}


def sample_from_space(trial: Any, space: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Materialise a concrete ``{name: value}`` override dict for *trial*.

    Parameters
    ----------
    trial:
        An object exposing ``suggest_float`` / ``suggest_int`` /
        ``suggest_categorical`` (the Optuna trial protocol). Passed by
        :class:`bybit_edge.tuning.optuna_tuner.OptunaTuner.objective`.
    space:
        One entry of :data:`SPACES`, e.g. ``SPACES["S3"]``.

    Returns
    -------
    dict mapping config attribute names to concrete sampled values, ready
    to be handed to :class:`bybit_edge.tuning.ParameterContext`.
    """
    out: dict[str, Any] = {}
    for name, spec in space.items():
        kind = spec["type"]
        if kind == "float":
            out[name] = trial.suggest_float(
                name,
                float(spec["low"]),
                float(spec["high"]),
                log=bool(spec.get("log", False)),
                step=spec.get("step"),
            )
        elif kind == "int":
            out[name] = trial.suggest_int(
                name,
                int(spec["low"]),
                int(spec["high"]),
                step=int(spec.get("step", 1)),
            )
        elif kind == "categorical":
            out[name] = trial.suggest_categorical(name, spec["choices"])
        else:
            raise ValueError(
                f"Unknown space spec type {kind!r} for parameter {name!r}; "
                "supported: 'float', 'int', 'categorical'."
            )
    return out
