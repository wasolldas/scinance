"""C-15 trade-tape event-grammar mess-gate (H-15, F-GRAMMAR, KAPITALFREI, GPU).

Existence-of-structure measurement on the TOKENISED Bybit publicTrade stream
(Side x Signed-Size-Quantile-8 x Log-Inter-Arrival-8, vocab 128): does a
small decoder-only causal transformer (~2-4M params, context 1024) achieve a
>= 2% relatively lower OOS token-level cross-entropy than the best
KT-smoothed variable-order Markov baseline (k <= 4) — beyond an intraday-
seasonality-preserving within-hour-of-day block-shuffle null (block 256
events, >= 200 surrogates)? Purged walk-forward (4 folds, 1-day embargo, 3
seeds), BH-FDR alpha=0.10 over F-GRAMMAR (5 symbols). Gate-neutral — the
gate-auditor adjudicates against the H-15 registry entry.

DIFFERENZIERUNG (Pflicht, Registry H-15): dies ist NICHT der gesperrte
Informationstheorie-Cluster (PE/TE, H-06/H-04) — Event-Stream statt
Renditen, Cross-Entropy als Scoring-Rule statt Entropie-Schaetzer, kein
rho-/Trading-Gate (Volltext: ``driver.DIFFERENTIATION_NOTE``).

COMPUTE GATE: a verdict-bearing run REQUIRES torch + CUDA (registry: "GPU,
zwingend"); without CUDA the driver either refuses (full mode) or stamps
``gate_valid: false`` / ``ran_on_gpu: false`` (mechanics mode).

KAPITALFREI: pure measurement, no capital metric anywhere.
"""
from .driver import (
    DEFAULT_DATA_END,
    DEFAULT_DATA_START,
    DEFAULT_SEEDS,
    DEFAULT_SYMBOLS,
    DIFFERENTIATION_NOTE,
    DataError,
    EventStream,
    HYPOTHESIS_ID,
    count_trade_events,
    daily_grid,
    load_trade_events,
    prepare_fold,
    render_markdown,
    run,
)
from .markov_baseline import (
    CE_WARMUP,
    InterpolatedMarkov,
    MAX_ORDER,
    MarkovError,
    MarkovKT,
    best_baseline_ce,
    fit_all_baselines,
)
from .stats import (
    BLOCK_LEN_EVENTS,
    EMBARGO_DAYS,
    FAMILY_SIZE,
    FDR_ALPHA,
    FDR_FAMILY,
    Fold,
    FoldError,
    N_FOLDS,
    N_SEEDS,
    N_SURROGATES_DEFAULT,
    REL_CE_GAP_MIN,
    SURROGATE_PERCENTILE,
    SYMBOLS_PASS_MIN,
    benjamini_hochberg,
    hour_block_shuffle,
    relative_ce_gap,
    surrogate_gap_p,
    walk_forward_folds,
)
from .tokenizer import (
    N_IAT_BUCKETS,
    N_SIZE_BUCKETS,
    TokenizerError,
    TokenizerSpec,
    VOCAB_BASE,
    VOCAB_TICKDIR,
    decompose_token,
    derive_event_features,
    fit_tokenizer,
    tokenize,
)
from .transformer import (
    ComputeUnavailableError,
    GrammarTransformerConfig,
    torch_cuda_status,
)

__all__ = [
    "BLOCK_LEN_EVENTS",
    "CE_WARMUP",
    "ComputeUnavailableError",
    "DEFAULT_DATA_END",
    "DEFAULT_DATA_START",
    "DEFAULT_SEEDS",
    "DEFAULT_SYMBOLS",
    "DIFFERENTIATION_NOTE",
    "DataError",
    "EMBARGO_DAYS",
    "EventStream",
    "FAMILY_SIZE",
    "FDR_ALPHA",
    "FDR_FAMILY",
    "Fold",
    "FoldError",
    "GrammarTransformerConfig",
    "HYPOTHESIS_ID",
    "InterpolatedMarkov",
    "MAX_ORDER",
    "MarkovError",
    "MarkovKT",
    "N_FOLDS",
    "N_IAT_BUCKETS",
    "N_SEEDS",
    "N_SIZE_BUCKETS",
    "N_SURROGATES_DEFAULT",
    "REL_CE_GAP_MIN",
    "SURROGATE_PERCENTILE",
    "SYMBOLS_PASS_MIN",
    "TokenizerError",
    "TokenizerSpec",
    "VOCAB_BASE",
    "VOCAB_TICKDIR",
    "benjamini_hochberg",
    "best_baseline_ce",
    "count_trade_events",
    "daily_grid",
    "decompose_token",
    "derive_event_features",
    "fit_all_baselines",
    "fit_tokenizer",
    "hour_block_shuffle",
    "load_trade_events",
    "prepare_fold",
    "relative_ce_gap",
    "render_markdown",
    "run",
    "surrogate_gap_p",
    "tokenize",
    "torch_cuda_status",
    "walk_forward_folds",
]
