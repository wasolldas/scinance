"""WP-11 -- Relaxationsrate der Aktivitaet nach Schockstunden (X-OEKO-1 Arm
(a), PRD 11.3, DEC-58). Deskriptiv, KEIN Gate, KEIN PASS/FAIL.

Submodules:

  * ``measure``  -- event definition INHERITED from H-20 (imports
    ``c20_tail.driver``, no re-implementation); post-shock exponential
    relaxation fit (AR(1)-equivalent) of the excess of three activity
    variables over their pre-shock baseline; empirical time-to-return
    distribution with day-cluster bootstrap CI; a matched-null of
    randomly placed pseudo-shock hours as the structural-null diagnostic.
  * ``report``   -- JSON + Markdown summary and DEC-53 artefacts
    (per-event cluster-level CSV + bootstrap seed/fingerprint), loud
    "KEIN BEFUND" below the 30-cluster floor.

KAPITALFREI throughout: no cost quantity, no PASS/FAIL, no live orders.
"""
from __future__ import annotations
