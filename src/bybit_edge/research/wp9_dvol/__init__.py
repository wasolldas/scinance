"""WP-9 -- Deribit DVOL REST backfill and source cross-validation (KAPITALFREI).

See ``scinance3-impl/WP9_SPEZIFIKATION.md`` for the registered questions
(F1 depth, F2 exchangeability) and the derived materiality band. Three
submodules, one per pipeline stage:

  * ``rest_client``    -- public REST fetch (paginated, throttled,
    wrapper-tolerant, SHA-256'd), field layout marked [sek].
  * ``harvest_close``  -- deterministic daily close from the harvested
    ``deribit/dvol`` stream (DuckDB, arg_max, manifest-DONE aware).
  * ``crossval``        -- daily differences, stationary block bootstrap
    CI, reachability-first verdict a/b/"nicht entscheidbar bei n".
"""
from __future__ import annotations
