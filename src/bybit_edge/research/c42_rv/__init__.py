"""C-42 volatility-regression reproduction package (WP-4, DEC-04/DEC-05).

Reproduces the one positive OOS finding of the Kestrel project — the LightGBM
regression on ``log(realised_vol_60m)`` (Test R^2 = 0.249, research_notes.md) —
under a clean purged walk-forward design with FDR control, evaluated against the
pre-registered H-02 gate (``scinance2-impl/state/hypothesis_registry.md``).

Read-only with respect to ``kline_1min``; the gate verdict is the gate-auditor's
call, not the pipeline's. CLI entry point: ``scripts/c42_repro.py``.
"""
from __future__ import annotations

from .features import FEATURE_PROVENANCE, build_features, feature_names
from .metrics import benjamini_hochberg, oos_r2, permutation_importance, qlike
from .models import (
    HARRVBaseline,
    HistGBMVolModel,
    LightGBMVolModel,
    VolModel,
    build_model,
)
from .pipeline import render_markdown, run_pipeline
from .splits import Fold, assert_disjoint_and_purged, purged_walk_forward
from .target import HORIZON_BARS, build_target

__all__ = [
    "FEATURE_PROVENANCE",
    "Fold",
    "HARRVBaseline",
    "HORIZON_BARS",
    "HistGBMVolModel",
    "LightGBMVolModel",
    "VolModel",
    "assert_disjoint_and_purged",
    "benjamini_hochberg",
    "build_features",
    "build_model",
    "build_target",
    "feature_names",
    "oos_r2",
    "permutation_importance",
    "purged_walk_forward",
    "qlike",
    "render_markdown",
    "run_pipeline",
]
