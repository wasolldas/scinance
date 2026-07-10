"""C-16 Time-Arrow-CNN mess-gate (H-16, F-ARROW, KAPITALFREI, GPU).

Classifier two-sample test (Lopez-Paz & Oquab 2017) for TIME-IRREVERSIBILITY
of the 1s signed trade-imbalance series (buy minus sell taker volume, Bybit
perp ``publicTrade``, 5 symbols): a CNN classifies FORWARD vs. TIME-REVERSED
complex-Morlet-CWT log-power scalograms (512 s windows, 64 s stride, 64
scales 2 s..256 s). The Bayes-optimal AUC for a time-reversible process is
EXACTLY 0.5 — the main null needs no resampling. Two mandatory controls
(both part of the registered gate): (a) pipeline-leak control — the SAME
pipeline on IAAFT phase-randomised surrogates must stay at held-out
AUC <= 0.52 (else METHODICALLY INVALID, no verdict — a distinct state, NOT
a DROP); (b) volatility-asymmetry ablation on |imbalance| (report-only).

Registry: ``scinance2-impl/state/hypothesis_registry.md`` — "### H-16 ·
Time-Arrow-CNN" (Welle 5). KAPITALFREI: pure structure/existence question —
no cost or return accounting anywhere in this package (a trading consequence
would be a NEW H-16b, explicitly NOT implied).

DIFFERENTIATION vs. the locked information-theory / nonlinear-dynamics
cluster (PE/TE/RQA/MFDFA/TDA — H-04/H-06 lineage): this is NOT a duplicate.
No entropy estimator appears anywhere in this package; the measured property
is TIME-IRREVERSIBILITY (directional asymmetry of the process law under
t -> -t), not complexity or predictability; and the null is the EXACT
Bayes-optimal AUC = 0.5 of the classifier two-sample test, not an estimated
threshold from a surrogate-calibrated entropy statistic. See
``driver.DIFFERENTIATION_NOTE`` for the registry-mandated verbatim paragraph.

GPU gating: the full run is verdict-bearing ONLY on a real CUDA device
(registry: surrogate null = ~20 full CNN retrainings per symbol). Without
torch/CUDA the package imports fine and degrades honestly: the CLI's
``--check-gpu-only`` reports the truth and the driver refuses a
verdict-bearing run.
"""
from .driver import (  # noqa: F401
    DIFFERENTIATION_NOTE,
    HYPOTHESIS_ID,
    DataError,
    check_gpu,
    render_markdown,
    run,
)
from .iaaft import iaaft  # noqa: F401
from .scalogram import (  # noqa: F401
    cwt_complex,
    cwt_logpower,
    extract_windows,
    fourier_periods,
    scalogram_pair,
)
from .stats import benjamini_hochberg, evaluate_gate, mann_whitney_auc  # noqa: F401
