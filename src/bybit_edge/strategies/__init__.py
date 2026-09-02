# compat shim for untouchable forensic tests (DEC-54)
"""Compatibility shim: ``bybit_edge.strategies`` -> ``bybit_edge._legacy_v1.strategies``.

The Scinance-1.0 strategy modules (S1-S5) moved to
``bybit_edge._legacy_v1.strategies`` in the 3.0 repo restructure (see
``scinance3-impl/UMBAU_SPEZIFIKATION.md`` §1.3 and
``src/bybit_edge/_legacy_v1/__init__.py`` for why the code is dead).

Four forensic tests are contractually byte-identical and still import the
OLD path (``bybit_edge.strategies.strategy3_pre_settlement`` etc.), including
string-based ``unittest.mock.patch("bybit_edge.strategies.strategy3_pre_settlement...")``
targets. A plain re-export (``from ... import *``) would create a SECOND,
distinct module object at the old path, so a patch applied there would not
affect the real module the code under test actually runs.

Instead, this package registers the SAME module objects under both the old
and new dotted paths in ``sys.modules`` -- so importing
``bybit_edge.strategies.strategy3_pre_settlement`` and importing
``bybit_edge._legacy_v1.strategies.strategy3_pre_settlement`` yield the
identical object, and a mock.patch through either path patches the one and
only module.
"""

from __future__ import annotations

import sys as _sys

from bybit_edge._legacy_v1.strategies import strategy1_cascade as _s1
from bybit_edge._legacy_v1.strategies import strategy2_entropy_momentum as _s2
from bybit_edge._legacy_v1.strategies import strategy3_pre_settlement as _s3
from bybit_edge._legacy_v1.strategies import strategy4_pattern_ensemble as _s4
from bybit_edge._legacy_v1.strategies import strategy5_cross_sectional as _s5
from bybit_edge._legacy_v1.strategies import (
    Strategy1CascadeDetector,
    Strategy2EntropyMomentum,
    Strategy3PreSettlement,
    Strategy4PatternEnsemble,
    Strategy5CrossSectional,
)

# Register the real module objects under the old dotted names, so
# `from bybit_edge.strategies.strategy1_cascade import X` and
# `mock.patch("bybit_edge.strategies.strategy3_pre_settlement....")` resolve
# to the exact same module the live (well, dead-but-tested) code runs.
_sys.modules[__name__ + ".strategy1_cascade"] = _s1
_sys.modules[__name__ + ".strategy2_entropy_momentum"] = _s2
_sys.modules[__name__ + ".strategy3_pre_settlement"] = _s3
_sys.modules[__name__ + ".strategy4_pattern_ensemble"] = _s4
_sys.modules[__name__ + ".strategy5_cross_sectional"] = _s5

strategy1_cascade = _s1
strategy2_entropy_momentum = _s2
strategy3_pre_settlement = _s3
strategy4_pattern_ensemble = _s4
strategy5_cross_sectional = _s5

__all__: list[str] = [
    "Strategy1CascadeDetector",
    "Strategy2EntropyMomentum",
    "Strategy3PreSettlement",
    "Strategy4PatternEnsemble",
    "Strategy5CrossSectional",
]
