"""C-07 Permutation-Entropy research package (Welle-2 WP, H-06, KAPITALFREI).

KAPITALFREI standalone detection module (DEC-12): tests whether the Bandt-Pompe
Permutation Entropy (m = 4 / tau = 1, PRE-FIXED) of the ``kline_1min`` close
log-returns carries conditional predictive information about future returns /
realized vol beyond a surrogate null. TWO-STAGE gate (registry H-06):

* PRE-Gate: rank correlation rho between the PE-DROP and the downstream 15-min
  vol-cluster (rho >= 0.30 on >= 2 disjoint windows; rho < 0.30 in ONE window
  => DROP — the hard, cheap pre-filter that runs before the main gate).
* Main-Gate: per pre-fixed delta in {1,5,15,60}min the conditional information
  MI(PE_t ; target_{t+delta}) against a block-shift surrogate null (N >= 200),
  BH-FDR alpha = 0.10 over the F-ENTROPY family (all window-length x delta x
  symbol), plus a conditional AUC-lift >= +0.03 in G1 (top vol quartile of the
  surrogate null).

Driven read-only over the existing ``kline_1min`` table (PRD §4 wörtlich: "nur
Kline, kein Tiefen-Stream" — NOT the trades table). NOT wired into the live
pipeline / replay_backtester.

The embedding m = 4 / tau = 1 are pre-fixed read-only constants (``PE_M`` /
``PE_TAU``), NOT CLI flags — any deviation is a NEW H-06 line (verdict.md §1f).
There is NO friction / edge / bps / PnL / Sharpe logic — tradability would be a
separate H-06b. CLI: ``scripts/c07_pe.py``. The driver renders NO overall verdict
(gate-auditor's call); it reports each criterion individually (PRE-Gate rho,
surrogate_p, fdr_significant, auc_lift, n_g1) per window/delta/symbol.
"""
from __future__ import annotations

from .driver import (
    DEFAULT_LAGS_MIN,
    DEFAULT_SYMBOLS,
    HYPOTHESIS_ID,
    MIN_WINDOWS,
    WINDOW_MAX_BARS,
    DataError,
    KlineArrays,
    WindowSymbolResult,
    load_kline_duckdb,
    load_kline_file,
    load_symbols_duckdb,
    render_markdown,
    run,
    split_windows,
    write_outputs,
)
from .info_test import (
    AUC_LIFT_FLOOR,
    DEFAULT_N_BINS,
    FDR_ALPHA,
    SURROGATE_P_MAX,
    InfoTestResult,
    benjamini_hochberg,
    block_shift_surrogate_p,
    g1_auc_lift,
    info_test,
    mutual_information,
)
from .perm_entropy import (
    DEFAULT_PE_WINDOW,
    PE_M,
    PE_TAU,
    log_returns,
    pe_drop,
    permutation_entropy,
    rolling_permutation_entropy,
)
from .pre_gate import (
    RHO_FLOOR,
    VOL_CLUSTER_BARS,
    PreGateResult,
    forward_realized_vol,
    pre_gate,
    spearman_rho,
)

__all__ = [
    "AUC_LIFT_FLOOR",
    "DEFAULT_LAGS_MIN",
    "DEFAULT_N_BINS",
    "DEFAULT_PE_WINDOW",
    "DEFAULT_SYMBOLS",
    "FDR_ALPHA",
    "HYPOTHESIS_ID",
    "MIN_WINDOWS",
    "PE_M",
    "PE_TAU",
    "RHO_FLOOR",
    "SURROGATE_P_MAX",
    "VOL_CLUSTER_BARS",
    "WINDOW_MAX_BARS",
    "DataError",
    "InfoTestResult",
    "KlineArrays",
    "PreGateResult",
    "WindowSymbolResult",
    "benjamini_hochberg",
    "block_shift_surrogate_p",
    "forward_realized_vol",
    "g1_auc_lift",
    "info_test",
    "load_kline_duckdb",
    "load_kline_file",
    "load_symbols_duckdb",
    "log_returns",
    "mutual_information",
    "pe_drop",
    "permutation_entropy",
    "pre_gate",
    "render_markdown",
    "rolling_permutation_entropy",
    "run",
    "spearman_rho",
    "split_windows",
    "write_outputs",
]
