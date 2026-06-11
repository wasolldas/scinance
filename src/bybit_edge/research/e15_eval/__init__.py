"""E-15 evaluation tooling (WP-1): machine check of the H-01 gate.

Read-only over the replay artifacts (``replay_all_results.json`` +
``trades_all.csv``); produces ``e15_evaluation.json`` / ``.md``. CLI entry
point: ``scripts/evaluate_e15.py`` (path-parametrised per DEC-02).
"""
from __future__ import annotations

from .e17 import check_e17
from .gate import (
    VERDICT_DROP,
    VERDICT_GRAUBEREICH,
    VERDICT_WEITER,
    evaluate_h01_gate,
)
from .metrics import (
    DataError,
    Trade,
    compute_e15_metrics,
    extract_reason_counts,
    load_results,
    load_trades,
)
from .report import build_payload, render_markdown, write_outputs

__all__ = [
    "DataError",
    "Trade",
    "VERDICT_DROP",
    "VERDICT_GRAUBEREICH",
    "VERDICT_WEITER",
    "build_payload",
    "check_e17",
    "compute_e15_metrics",
    "evaluate_h01_gate",
    "extract_reason_counts",
    "load_results",
    "load_trades",
    "render_markdown",
    "write_outputs",
]
