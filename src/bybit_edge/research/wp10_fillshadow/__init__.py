"""WP-10 Teil B -- Maker-Fill-Schattenmessung (kapitalfrei, KEIN Alpha-Gate).

See ``scinance3-impl/WP10_SPEZIFIKATION.md`` Teil B. The question: with
what probability would a hypothetical own passive quote joined at the
touch have been FILLED within 10 s / 60 s (design parameters),
reconstructed purely from public L2 (``orderbook.1000``) and
``publicTrade``? No PASS/FAIL, no threshold on ``p_fill`` itself --
``adv_sel <= 1,75 bp`` is a LABEL ("Maker-Vorteil traegt"/"traegt
nicht"), not a gate. Submodules, one per pipeline stage:

  * ``queue_model``       -- pure queue-position fill simulation, two
    bounding conventions (FIFO-conservative lower bound, pro-rata-cancel
    upper bound) reported side by side, plus adverse selection.
  * ``replay``             -- reuses the WP-2/WP-4 snapshot+delta book
    replay (``c22_l2tilt.extract``) to reconstruct top-of-book, joins
    ``publicTrade`` (shared ``payload_sql``/``bar_cache`` dialect
    helpers), places one hypothetical quote per minute per side, writes
    the OWN ``fillshadow_1min`` store (WP-2/WP-4 stores provably
    untouched) with manifest-DONE gating on top of the break-budget
    discard rules.
  * ``positive_control``   -- the PRD 3.3.8 pre-run: a synthetic quote
    with a KNOWN queue position must reproduce a KNOWN fill through the
    real ``queue_model`` entry point BEFORE the real replay runs.
  * ``report``              -- fill-rate curves p_fill(10s/60s) per
    symbol/side/hour-of-day/STRESS_ABS-vs-quiet, adverse-selection
    distribution + label, DEC-53 artefacts (per-quote outcome CSV +
    bootstrap seed), loud "KEIN VERDIKT" if artefacts are missing.

KAPITALFREI throughout: no cost quantity, no PASS/FAIL, no live orders.
"""
from __future__ import annotations
