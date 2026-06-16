"""C-01 OFI-sign research package (Welle-2 WP, H-05, INC-02-Anker, KAPITALFREI).

KAPITALFREI standalone falsification module (DEC-11): measures the *sign* of the
conditional relation ``sign(OFI_t) -> sign(forward_return_{t+delta})`` on the
existing ``trades`` stream via an OWN trade-flow OFI estimator (aggressor-signed
volume per time bin) — does aggressive order flow LEAD price in the SAME
direction (aggression-follow, PRD-v1 / CS-02) or the INVERSE direction (the
MM-replenishment reading the S2 implementation produced, INC-02 / E-04 anchor)?
Per pre-fixed delta in {1,5,15,60,300}s it reports corr, sign_direction, |corr|,
conditional hit-rate, a permutation surrogate p (OFI independently shuffled
against the return, N >= 200) and BH-FDR alpha = 0.10 over the F-OFI family
(all delta x symbols). Driven read-only over the existing ``trades`` table.
NOT wired into the live pipeline / replay_backtester.

The bestand ``l1_ingestion/m2_ofi.py`` (known C-01/C-02 swap, book-update based,
streaming, suspect) is NOT imported and left completely untouched — this gate
must not hinge on the implementation under suspicion (DEC-11).

Gate (registry H-05): WEITER = sign = + (aggression-follow) UND p <= 0.05 after
BH-FDR over F-OFI UND (|corr| >= 0.05 ODER hit-rate >= 0.53) in >= 2 disjoint
windows. Sign <= 0 in >= 1 window OR magnitude missed OR FDR-p > 0.05 = DROP.
A significant INVERSE direction is NOT an H-05 pass — it triggers a separate
H-05b. There is NO friction / edge / bps / PnL / Sharpe logic — that would be a
separate H-05c. CLI: ``scripts/c01_ofi_sign.py``. The driver renders NO overall
verdict (gate-auditor's call); it reports each criterion individually plus
``sign_direction`` and ``inverse_significant``.
"""
from __future__ import annotations

from .driver import (
    DEFAULT_SYMBOLS,
    HYPOTHESIS_ID,
    MIN_WINDOWS,
    WINDOW_MAX_TICKS,
    DataError,
    TradeArrays,
    WindowSymbolResult,
    load_symbols_duckdb,
    load_trades_duckdb,
    load_trades_file,
    render_markdown,
    run,
    split_windows,
    write_outputs,
)
from .ofi import (
    DEFAULT_GRID_MS,
    DEFAULT_LAGS_S,
    bin_ofi,
    last_price_at,
    ofi_and_forward_return,
    signed_volume,
)
from .sign_test import (
    ABS_CORR_FLOOR,
    FDR_ALPHA,
    HIT_RATE_FLOOR,
    SURROGATE_P_MAX,
    SignTestResult,
    benjamini_hochberg,
    conditional_hit_rate,
    permutation_surrogate_p,
    sign_test,
)

__all__ = [
    "ABS_CORR_FLOOR",
    "DEFAULT_GRID_MS",
    "DEFAULT_LAGS_S",
    "DEFAULT_SYMBOLS",
    "FDR_ALPHA",
    "HIT_RATE_FLOOR",
    "HYPOTHESIS_ID",
    "MIN_WINDOWS",
    "SURROGATE_P_MAX",
    "DataError",
    "SignTestResult",
    "TradeArrays",
    "WINDOW_MAX_TICKS",
    "WindowSymbolResult",
    "benjamini_hochberg",
    "bin_ofi",
    "conditional_hit_rate",
    "last_price_at",
    "load_symbols_duckdb",
    "load_trades_duckdb",
    "load_trades_file",
    "ofi_and_forward_return",
    "permutation_surrogate_p",
    "render_markdown",
    "run",
    "sign_test",
    "signed_volume",
    "split_windows",
    "write_outputs",
]
