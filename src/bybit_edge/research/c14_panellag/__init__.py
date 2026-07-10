"""C-14-PANELLAG — H-14 conditional cross-venue lead-lag graph (KAPITALFREI, GPU).

Node-ablation cross-attention forecaster over the 12-node cross-venue
1s-panel (BTC/ETH x {Bybit, Binance, Deribit-PERP} + SOL/BNB/XRP x
{Bybit, Binance}). Registry: H-14 in
``scinance2-impl/state/hypothesis_registry.md`` (Welle 5). Read-only against
the harvester backfill tree; gate-neutral payload — the gate-auditor
adjudicates. GPU-gated: a full run without real CUDA training is NEVER
verdict-bearing (see ``driver.build_compute_gating``).
"""
from .ablation import make_dummy_train_fn, make_torch_train_fn  # noqa: F401
from .driver import build_compute_gating, make_compute_info, render_markdown, run  # noqa: F401
from .encoder import ComputeGateError, check_gpu  # noqa: F401
from .panel import (  # noqa: F401
    DEFAULT_NODES,
    DataError,
    PanelWindow,
    build_window,
    map_exchange_symbol,
)
