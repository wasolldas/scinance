"""C-10 cross-stream pointer-day mess-gate (H-10, F-POINTER, KAPITALFREI).

Stage 1: existence of cross-stream synchronisation ("pointer days") over the
pre-fixed 30 detection series (5 symbols x {bybit, binance} x {RV, funding,
dlog-OI}) against a circular-surrogate null. Stage 2: pre-event drift of the
HELD-OUT Deribit dvol target index (BTC+ETH) over the 1-5 days BEFORE pointer
days against a permutation null. Gate-neutral throughout — the gate-auditor
adjudicates against the H-10 registry entry.

KAPITALFREI: pure measurement, no capital-metric anywhere.
"""
from .cropper import (
    C_THRESH,
    CROPPER_HALF_WINDOW,
    DETREND_MIN_PERIODS,
    DETREND_WINDOW,
    N_AVAIL_FLOOR,
    SHARE_FLOOR,
    PointerDays,
    cropper_score,
    detect_pointer_days,
    trailing_median_detrend,
)
from .driver import HYPOTHESIS_ID, render_markdown, run
from .loaders import (
    DataError,
    build_detection_panel,
    daily_grid,
    load_daily_dvol,
    load_daily_funding_mean,
    load_daily_last_price,
    load_daily_oi_close,
)
from .stats import (
    FDR_ALPHA,
    FDR_FAMILY,
    MIN_NULL_GAP_DAYS,
    N_POINTER_FLOOR,
    SURROGATE_P_MAX,
    benjamini_hochberg,
    delta_pre,
    dvol_index,
    stage1_surrogate_p,
    stage2_permutation_p,
)

__all__ = [
    "C_THRESH",
    "CROPPER_HALF_WINDOW",
    "DETREND_MIN_PERIODS",
    "DETREND_WINDOW",
    "DataError",
    "FDR_ALPHA",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "MIN_NULL_GAP_DAYS",
    "N_AVAIL_FLOOR",
    "N_POINTER_FLOOR",
    "PointerDays",
    "SHARE_FLOOR",
    "SURROGATE_P_MAX",
    "benjamini_hochberg",
    "build_detection_panel",
    "cropper_score",
    "daily_grid",
    "delta_pre",
    "detect_pointer_days",
    "dvol_index",
    "load_daily_dvol",
    "load_daily_funding_mean",
    "load_daily_last_price",
    "load_daily_oi_close",
    "render_markdown",
    "run",
    "stage1_surrogate_p",
    "stage2_permutation_p",
    "trailing_median_detrend",
]
