"""WP-10 Teil A -- Praemien-Kohaerenz im Stress (deskriptiv, KEIN Alpha-Gate).

See ``scinance3-impl/WP10_SPEZIFIKATION.md`` Teil A. Rein deskriptiv: kein
PASS/FAIL, keine rho-Schwelle (Review R1-R4 hat erfundene Schwellen
gestrichen). Submodule, one per pipeline stage:

  * ``rv``             -- shared realized-volatility primitive from the
    WP-0 minute bar cache (own module so ``stress_canon`` and ``series``
    see EXACTLY the same RV number, no drift between the stress threshold
    and the IV-RV coherence proxy).
  * ``series``          -- daily premium-proxy series loaders (funding
    cashflow, IV-RV difference, perp-basis proxy), each with provenance
    + coverage, loud-fail on [sek] field-layout drift.
  * ``stress_canon``    -- STRESS_REL (DEC-55) and STRESS_ABS (DEC-56)
    fixtures, deterministic, append-only.
  * ``coherence``        -- Spearman correlation matrices STRESS_ABS vs.
    quiet, cluster (=calendar day) bootstrap CI, Bonett/Wright SE anchor,
    effective N per regime.
  * ``portfolio_null``   -- expected Sharpe of an equal-weighted k=2..5
    pure-noise-signal combination on this panel, reported as a CONSTANT
    with CI (no threshold) -- calibration input for a later portfolio
    gate (R4 6.2a), never itself a verdict.
  * ``report``           -- JSON + Markdown report, DEC-53 artefacts
    (cluster-level daily series + bootstrap seed/replicates), loud "KEIN
    VERDIKT" if artefacts are missing.

KAPITALFREI throughout: no cost quantity, no PASS/FAIL, no live orders.
"""
from __future__ import annotations
