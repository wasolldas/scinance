"""C-31 Cyclostationary CFAR research package (WP-3, H-03).

Standalone falsification module (DEC-03): cyclic-spectrum estimator + CA-CFAR
peak detector + surrogate null test + lead/edge measurement, driven read-only
over the existing ``trades`` table or a CSV/Parquet file. NOT wired into the
live pipeline / replay_backtester. CLI: ``scripts/c31_cfar.py``.

Gate (registry H-03, PRD §3 Pilot 4): Surrogate p <= 0.05 in >= 2 windows AND
Lead > 50 ms AND Edge > 11 bps; hard one-window DROP criterion (§8.5);
parameter variants are the F-CFAR family under BH-FDR alpha = 0.10.
"""
from __future__ import annotations

from .cfar_detector import CfarConfig, CfarPeak, detect_peaks, top_snr
from .cyclic_spectrum import (
    DEFAULT_BIN_GRID_MS,
    CyclicSpectrum,
    bin_counts,
    inter_arrivals,
    spectral_correlation_density,
)
from .driver import (
    DataError,
    ParamVariant,
    default_family,
    load_trades_duckdb,
    load_trades_file,
    render_markdown,
    run,
    run_window,
    split_windows,
    write_outputs,
)
from .lead_edge import (
    EDGE_MIN_BPS,
    LEAD_MIN_MS,
    LeadEdgeResult,
    LookaheadError,
    measure_lead_edge,
)
from .surrogate import (
    FDR_ALPHA,
    SurrogateResult,
    benjamini_hochberg,
    surrogate_test,
)

__all__ = [
    "CfarConfig",
    "CfarPeak",
    "CyclicSpectrum",
    "DEFAULT_BIN_GRID_MS",
    "DataError",
    "EDGE_MIN_BPS",
    "FDR_ALPHA",
    "LEAD_MIN_MS",
    "LeadEdgeResult",
    "LookaheadError",
    "ParamVariant",
    "SurrogateResult",
    "benjamini_hochberg",
    "bin_counts",
    "default_family",
    "detect_peaks",
    "inter_arrivals",
    "load_trades_duckdb",
    "load_trades_file",
    "measure_lead_edge",
    "render_markdown",
    "run",
    "run_window",
    "spectral_correlation_density",
    "split_windows",
    "surrogate_test",
    "top_snr",
    "write_outputs",
]
