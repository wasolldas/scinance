"""C-17-VENUE — H-17 Venue-Fingerprint contrastive-embedding gate (KAPITALFREI).

Symbol-invariant venue-identity classification (Bybit vs. Binance) on
shape-normalized order flow via InfoNCE contrastive embedding + frozen
linear probe, Leave-One-Symbol-Out. Registry: H-17 in
``scinance2-impl/state/hypothesis_registry.md`` (Welle 5). Read-only against
the harvester backfill tree; gate-neutral payload — the gate-auditor
adjudicates. Pre-registered non-redundancy gate against c12_frag/H-12.

PyTorch is OPTIONAL (m18_patchtst pattern): without torch, ``encoder.py``
stays importable and honestly reports ``TORCH_AVAILABLE = False`` /
``cuda_available() = False``; a full run without a real CUDA device is
NEVER verdict-bearing (``driver.run`` sets ``compute.verdict_bearing =
False`` and forces ``weiter_indication = False``).
"""
from .driver import render_markdown, run  # noqa: F401
from .encoder import (  # noqa: F401
    TORCH_AVAILABLE,
    NumpyFallbackEncoder,
    cuda_available,
    gpu_report,
    make_encoder_factory,
)
from .features import (  # noqa: F401
    DEFAULT_EXCHANGES,
    DEFAULT_SYMBOLS,
    DataError,
    NodeWindows,
    build_node_windows,
    load_panel,
)
from .redundancy import redundancy_gate  # noqa: F401
