"""C-06 Cross-Sectional Ergodic Mean-Reversion mess-gate (Welle-3 WP, H-07/H-08).

H-08 extension (DEC-18): the driver takes an ``overextension`` mode — ``"z"``
(default, the UNCHANGED H-07 path, |z| >= 2.5, family F-XMR) or ``"rank"``
(H-08: axis A = per-bar rank-1 symbol argmax|z|, threshold-free, tie ->
alphabetically first symbol, family F-XMR-RANK). Everything else (axis B,
baseline, surrogates, CIs, FDR, N-floor) is shared unchanged between modes.

KAPITALFREI cross-sectional measurement + amplification module (DEC-17). On the
read-only harvester backfill it builds a contemporaneously-synchronised 5-symbol
5-min last-price bar panel (BTC/ETH/SOL/BNB/XRP), computes the M13
cross-sectional-z of each symbol's 60-min return time-mean vs the ensemble, and
tests whether the reversion-signed forward return of over-stretched (|z|>=2.5),
non-crash (panel-RV not top-decile) events is significantly STRONGER than the
unconditioned panel baseline — the non-triviality anchor that separates H-07
from the E-04-refuted / PRD-§6-forbidden trivial sign-flip MR.

Two conditioning axes (registry H-07, exactly 2 pre-fixed): A = |z| >= 2.5,
B = panel-15min-realized-vol NOT in the top decile. Horizons h in {1,3,6} bars.
Surrogate null decouples z from the forward returns; BH-FDR alpha=0.10 over the
F-XMR family; block-bootstrap 95% CIs; non-triviality = conditioned CI does NOT
overlap (lies above) the baseline CI in >= 2 windows. N-floor >= 30 conditioned
events per window. The driver renders NO overall verdict (gate-auditor's call).

The bestand modules ``c01_ofi_sign`` and ``c07_pe`` are imported read-only
(``load_harvest_window``; the RV formula is replicated locally) and left
completely untouched. There is NO friction / edge / bps / PnL / Sharpe logic —
tradability would be a separate H-07b. CLI: ``scripts/c06_xmr.py``.
"""
from __future__ import annotations

from .driver import (
    DEFAULT_N_FLOOR,
    FDR_FAMILY,
    FDR_FAMILY_RANK,
    HYPOTHESIS_ID,
    HYPOTHESIS_ID_RANK,
    MIN_WINDOWS,
    OVEREXTENSION_MODES,
    REGISTRY_PATH,
    SCHEMA_VERSION,
    render_markdown,
    run,
)
from .panel import (
    DEFAULT_BAR_MIN,
    DEFAULT_CALENDAR_DAYS,
    DEFAULT_SYMBOLS,
    MAX_FFILL_BARS,
    DataError,
    SyncedPanel,
    build_calendar_grid,
    load_panel_window,
    resample_last_price,
    synchronise_panel,
)
from .stats import (
    CI_LEVEL,
    FDR_ALPHA,
    SURROGATE_P_MAX,
    benjamini_hochberg,
    block_bootstrap_ci,
    ci_non_overlap,
    surrogate_p_mu_positive,
)
from .xsec import (
    DEFAULT_CRASH_DECILE,
    DEFAULT_HORIZONS,
    DEFAULT_LOOKBACK_BARS,
    DEFAULT_Z_THRESH,
    PANEL_RV_BARS,
    EventTable,
    build_event_table,
    build_event_table_rank,
    cross_sectional_z,
    forward_return_h,
    non_crash_mask,
    panel_realized_vol,
    rank_over_stretch_mask,
    time_mean_returns,
)

__all__ = [
    "CI_LEVEL",
    "DEFAULT_BAR_MIN",
    "DEFAULT_CALENDAR_DAYS",
    "DEFAULT_CRASH_DECILE",
    "DEFAULT_HORIZONS",
    "DEFAULT_LOOKBACK_BARS",
    "DEFAULT_N_FLOOR",
    "DEFAULT_SYMBOLS",
    "DEFAULT_Z_THRESH",
    "FDR_ALPHA",
    "FDR_FAMILY",
    "FDR_FAMILY_RANK",
    "HYPOTHESIS_ID",
    "HYPOTHESIS_ID_RANK",
    "MAX_FFILL_BARS",
    "MIN_WINDOWS",
    "OVEREXTENSION_MODES",
    "PANEL_RV_BARS",
    "REGISTRY_PATH",
    "SCHEMA_VERSION",
    "SURROGATE_P_MAX",
    "DataError",
    "EventTable",
    "SyncedPanel",
    "benjamini_hochberg",
    "block_bootstrap_ci",
    "build_calendar_grid",
    "build_event_table",
    "build_event_table_rank",
    "ci_non_overlap",
    "cross_sectional_z",
    "forward_return_h",
    "load_panel_window",
    "non_crash_mask",
    "panel_realized_vol",
    "rank_over_stretch_mask",
    "render_markdown",
    "resample_last_price",
    "run",
    "surrogate_p_mu_positive",
    "synchronise_panel",
    "time_mean_returns",
]
