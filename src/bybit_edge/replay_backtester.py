# compat shim for untouchable forensic tests (DEC-54)
"""Compatibility shim: ``bybit_edge.replay_backtester`` -> ``bybit_edge._legacy_v1.replay_backtester``.

The forensic replay/backtest engine moved to
``bybit_edge._legacy_v1.replay_backtester`` in the 3.0 repo restructure (see
``scinance3-impl/UMBAU_SPEZIFIKATION.md`` §1.3). The forensic test
``tests/unit/test_replay_backtester_maker_only.py`` is contractually
byte-identical and still imports this old path.

Rather than a plain re-export (which would create a second, distinct module
object at this path), this module replaces its own entry in ``sys.modules``
with the real module object during import. CPython re-reads
``sys.modules[__name__]`` after executing a module's code, so any caller of
``import bybit_edge.replay_backtester`` / ``from bybit_edge.replay_backtester
import X`` -- including this very import statement -- ends up holding the
one real module object, identical to ``bybit_edge._legacy_v1.replay_backtester``.
"""

from __future__ import annotations

import sys as _sys

from bybit_edge._legacy_v1 import replay_backtester as _real

_sys.modules[__name__] = _real
