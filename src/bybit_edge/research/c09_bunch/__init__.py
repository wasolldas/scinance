"""H-09 Risk-Limit-Tier-Bunching research package (Welle 4, F-BUNCH, KAPITALFREI).

Registry: ``scinance2-impl/state/hypothesis_registry.md`` "### H-09 ·
Risk-Limit-Tier-Bunching" (Welle 4 — Cross-Domain-Track, bridged via DEC-19
from ``edge-research-v3/results/CROSSDOMAIN_PRD.md``, origin IC-MECH-2).

Hypothesis: taker-order notionals cluster systematically just BELOW the first
documented risk-limit tier kink ``K_s`` per symbol (MMR jump; Saez 2010 /
Chetty et al. 2011 excess-mass bunching), with an ASYMMETRIC signature
(excess below the kink, no comparable excess above) that is STRONGER than
plain round-number preference at the placebo round numbers ``0.50*K_s`` /
``0.75*K_s``. A-priori (registry, honest): DROP expected.

Pieces:

* :mod:`kinks` — the ``costs.py`` analog: K_s constants dict (BTC registry-
  quoted; ETH/SOL/BNB/XRP PLATZHALTER, dated append-only operationalisation
  addendum required before a real run), band/bin geometry, gate thresholds,
  and the anti-gaming validity check.
* :mod:`estimator` — order aggregation, binning, degree-7 polynomial
  counterfactual, excess-mass ``b_hat-`` / ``b_hat+``, residual bootstrap
  (500 reps), placebo re-estimation.
* :mod:`stats` — own BH-FDR copy for F-BUNCH (§8.2 convention, no
  cross-import of the FDR helper).
* :mod:`driver` — read-only orchestration over 5 symbols x 2 pre-registered
  windows at order level; gate-neutral payload with per-cell criteria +
  ``weiter_indication`` (H-04b/H-05c convention). CLI: ``scripts/c09_bunch.py``.

KAPITALFREI (``capital_free=true``): pure structural/behavioural measurement.
The GATE VERDICT is the gate-auditor's; this package renders NO overall verdict.
"""
from __future__ import annotations

from .driver import (
    DEFAULT_WINDOW_A,
    DEFAULT_WINDOW_B,
    FDR_FAMILY,
    HYPOTHESIS_ID,
    MIN_WINDOWS,
    WINDOW_MAX_TICKS,
    DataError,
    load_harvest_window,
    render_markdown,
    run,
    write_outputs,
)
from .estimator import (
    BUNCH_BINS,
    CTRL_BINS,
    EXCLUDED_BINS,
    INCLUDED_MASK,
    aggregate_orders,
    bin_centers_rel,
    bin_notionals,
    estimate_cell,
    excess_mass,
    fit_counterfactual,
    residual_bootstrap_p,
)
from .kinks import (
    ASYMMETRY_FLOOR,
    B_MINUS_FLOOR,
    BOOT_P_MAX,
    CF_EXPECTATION_FLOOR,
    FDR_ALPHA,
    KINK_PLACEHOLDER_NOTE,
    KINK_PLACEHOLDER_SYMBOLS,
    N_BINS,
    N_BOOTSTRAP,
    N_FLOOR_ORDERS,
    PLACEBO_FRACTIONS,
    POLY_DEGREE,
    RISK_LIMIT_TIER1_KINK_USDT,
    gate_assumptions_valid,
)
from .stats import benjamini_hochberg

__all__ = [
    "ASYMMETRY_FLOOR",
    "BOOT_P_MAX",
    "BUNCH_BINS",
    "B_MINUS_FLOOR",
    "CF_EXPECTATION_FLOOR",
    "CTRL_BINS",
    "DEFAULT_WINDOW_A",
    "DEFAULT_WINDOW_B",
    "EXCLUDED_BINS",
    "FDR_ALPHA",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "INCLUDED_MASK",
    "KINK_PLACEHOLDER_NOTE",
    "KINK_PLACEHOLDER_SYMBOLS",
    "MIN_WINDOWS",
    "N_BINS",
    "N_BOOTSTRAP",
    "N_FLOOR_ORDERS",
    "PLACEBO_FRACTIONS",
    "POLY_DEGREE",
    "RISK_LIMIT_TIER1_KINK_USDT",
    "WINDOW_MAX_TICKS",
    "DataError",
    "aggregate_orders",
    "benjamini_hochberg",
    "bin_centers_rel",
    "bin_notionals",
    "estimate_cell",
    "excess_mass",
    "fit_counterfactual",
    "gate_assumptions_valid",
    "load_harvest_window",
    "render_markdown",
    "residual_bootstrap_p",
    "run",
    "write_outputs",
]
