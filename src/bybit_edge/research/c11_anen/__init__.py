"""C-11/IC-CLIM-1 — H-11 AnEn vol-regime forecast vs. HAR-RV (KAPITALFREI, data-gated).

Analog-ensemble (Delle Monache et al. 2013) distributional forecast of the
3-day-ahead log annualised realised volatility versus the HAR-RV (Corsi 2009)
point baseline. Registry H-11: the AnEn forecast IS the empirical
distribution of the 20 analog targets, scored with proper ensemble CRPS; the
degenerate point-CRPS (|forecast - observation|) applies ONLY to the HAR
baseline. Pure measurement gate — capital_free=true.

The hypothesis is **DATA-GATED** (registry H-11): the run only starts once the
harvester manifest confirms gapless done_days for bybit ``publicTrade`` AND
``rest.fundingRate``, BTC+ETH, over at least 2024-03-27..2026-03-26 (>= 730
days). ``driver.check_unlock`` performs that check programmatically before any
data is touched (primary source: ``harvest_manifest.sqlite`` done_days query;
partition-folder scan only as a fallback); if it fails, the driver reports a
clean SKIP payload.
"""
from .analog import analog_forecast, tune_weights_loo_crps, zscore_stats
from .baseline import har_fit, har_forecast_series
from .driver import check_unlock, render_markdown, run
from .features import (
    ANNUALISATION_DAYS,
    build_daily_panel,
    compute_feature_matrix,
    compute_target,
)
from .stats import (
    benjamini_hochberg,
    block_bootstrap_p,
    crps_ensemble,
    crps_point,
    crpss,
    pit_ranks,
)

__all__ = [
    "ANNUALISATION_DAYS",
    "analog_forecast",
    "benjamini_hochberg",
    "block_bootstrap_p",
    "build_daily_panel",
    "check_unlock",
    "compute_feature_matrix",
    "compute_target",
    "crps_ensemble",
    "crps_point",
    "crpss",
    "har_fit",
    "har_forecast_series",
    "pit_ranks",
    "render_markdown",
    "run",
    "tune_weights_loo_crps",
    "zscore_stats",
]
