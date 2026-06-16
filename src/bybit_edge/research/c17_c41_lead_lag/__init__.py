"""C-17/C-41 Cross-Sectional Lead-Lag research package (Welle-2 WP, H-04).

KAPITALFREI standalone falsification module (DEC-10): measures the *existence*
of directed information flow BTC->Alt between two symbols' return streams via
Shannon Transfer Entropy (C-17 axis) and a numpy-FFT wavelet coherence
phase-lead (C-41 axis), tested against a circular block-shift surrogate null
(destroys cross-coupling, preserves each marginal + autocorrelation), with
BH-FDR alpha = 0.10 over the F-LEADLAG family. Driven read-only over the
existing ``trades`` table or CSV/Parquet files. NOT wired into the live
pipeline / replay_backtester. CLI: ``scripts/c17_c41_lead_lag.py``.

Gate (registry H-04): directed information significant > surrogate null,
p <= 0.05 after BH-FDR over F-LEADLAG, existence in >= 2 disjoint windows,
lead-symbol stability across windows. Hard one-window DROP (§8.5). There is NO
friction / edge / bps / PnL logic — that would be a separate H-04b.
"""
from __future__ import annotations

from .driver import (
    DEFAULT_GRID_MS,
    WINDOW_MAX_TICKS,
    DataError,
    WindowResult,
    load_pair_duckdb,
    load_trades_duckdb,
    load_trades_file,
    render_markdown,
    run,
    run_window,
    split_pair_windows,
    write_outputs,
)
from .surrogate import (
    FDR_ALPHA,
    SurrogateResult,
    benjamini_hochberg,
    surrogate_test_te,
    surrogate_test_wcoh,
)
from .transfer_entropy import (
    DEFAULT_LAGS,
    DEFAULT_N_BINS,
    align_returns,
    resample_log_returns,
    transfer_entropy,
    wavelet_coherence_lead,
)

__all__ = [
    "DEFAULT_GRID_MS",
    "DEFAULT_LAGS",
    "DEFAULT_N_BINS",
    "FDR_ALPHA",
    "WINDOW_MAX_TICKS",
    "DataError",
    "SurrogateResult",
    "WindowResult",
    "align_returns",
    "benjamini_hochberg",
    "load_pair_duckdb",
    "load_trades_duckdb",
    "load_trades_file",
    "render_markdown",
    "resample_log_returns",
    "run",
    "run_window",
    "split_pair_windows",
    "surrogate_test_te",
    "surrogate_test_wcoh",
    "transfer_entropy",
    "wavelet_coherence_lead",
    "write_outputs",
]
