"""C-12-FRAG — H-12 Cross-Exchange fragmentation matrix mess-gate (KAPITALFREI).

RMT/MP-IPR measurement gate over the 6-series cross-exchange panel
(BTC/ETH x Bybit/Binance/Deribit). Registry: H-12 in
``scinance2-impl/state/hypothesis_registry.md`` (Welle 4). Read-only against
the harvester backfill tree; gate-neutral payload — the gate-auditor
adjudicates.
"""
from .driver import render_markdown, run  # noqa: F401
from .panel import (  # noqa: F401
    DEFAULT_EXCHANGES,
    DEFAULT_SYMBOLS,
    DataError,
    DayPanel,
    WindowDays,
    build_window,
    map_exchange_symbol,
)
