"""C-13 tail-shape consistency mess-gate (H-13, F-TAILSHAPE, KAPITALFREI, data-gated).

Compares the statistical GPD shape parameter xi_P (POT on 1-min losses,
Bybit perp publicTrade) against the risk-neutral tail shape xi_Q implied by
the Deribit ``markprice.options`` IV surface (SVI -> Breeden-Litzenberger RND
-> GPD-PWM on the left-tail excess distribution).

Registry: ``scinance2-impl/state/hypothesis_registry.md`` — "### H-13 ·
Tail-Form-Konsistenz" (Welle 4). The hypothesis is LOCKED (data-gated): the
unlock condition (two vol-regime-disjoint live IV snapshot days D1 < D2) is
searched programmatically by :mod:`snapshot_selection`; without it the driver
reports a clean SKIP. Pure measurement question — no cost or return
accounting anywhere in this package (any tail/skew trading consequence would
be a NEW H-13b, not implied here).
"""
from .driver import HYPOTHESIS_ID, check_unlock, render_markdown, run  # noqa: F401
from .returns_tail import DataError, estimate_xi_p  # noqa: F401
from .snapshot_selection import SelectionResult, select_days  # noqa: F401
from .stats import benjamini_hochberg, combined_bootstrap_p, evaluate_gate  # noqa: F401
from .svi_rnd import estimate_xi_q, fit_svi, gpd_fit_pwm, rnd_from_svi  # noqa: F401
