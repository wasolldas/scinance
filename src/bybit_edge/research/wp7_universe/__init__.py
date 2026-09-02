"""WP-7 -- Universums-Zensus (Klasse-W-Feasibility), KAPITALFREI.

See ``scinance3-impl/WP7_SPEZIFIKATION.md`` (Bauanleitung) and
``PRD_SCINANCE3.md`` Abschnitt 4.1 (massgeblicher Volltext) for the
registered questions this package answers: K je Kalenderwoche,
``SD_null(IC_t)`` (Permutations-Rauschboden), deskriptiv ``N_eff``,
``sigma_xs``, ``sigma_LS``, ``rho(BTC,ETH)``, ``PERP_SPREAD_BP`` je
Symbol-Dezil, ``funding_n``. Kein Alpha-Gate, binaerer Befund (B1..B5).

Submodules, one per pipeline stage:

  * ``bybit_rest``     -- public REST client (instruments-info + kline +
    funding/history), Cursor-/Rueckwaerts-Paginierung, Drossel, Rohantwort-
    SHA-256; NO network assumptions in tests (fixture-based, [sek] layout).
  * ``panel_store``    -- Jahrespartitionen ``panel_1d``, eigenes
    ``panel_manifest.sqlite`` (DONE/PARTIAL/EMPTY/FAILED), Fingerprints,
    ``frozen/`` (unveraenderlich) vs ``open/`` (laufendes Jahr).
  * ``pit_universe``   -- point-in-time-Universum (>= 8 Wochen Bars UND
    noch handelnd; delistetes Symbol bis zum letzten Bar gehalten, zum
    letzten Kurs geschlossen); Momentum-IC-Kern fuer den DEC-39-Survivor-
    ship-Adversarial-Test (inkl. der bewusst FALSCHEN Referenz-Variante
    "-100% bei Delisting", NUR fuer den Test, kein Produktionscode).
  * ``null_ic``        -- Permutations-Rauschboden ``SD_null(IC_t)``,
    Seed + Wochen-Serie als Pflichtartefakte (DEC-53).
  * ``stats``           -- ``N_eff`` (Ledoit-Wolf-geschrumpfte Partizipa-
    tionszahl der Residual-Korrelationsmatrix -- deskriptiv, kein Urteil),
    ``sigma_xs``, ``sigma_LS`` (Zufalls-Sortierschluessel), Feasibility-
    Arithmetik (DEC-51/52-z), ``sigma_xs_min``-Formel.
  * ``spread_probe``   -- Tickers-Inhaltsprobe (bid1Price/ask1Price/
    openInterest/fundingRate) + Dezil-Spread, REST-Fallback.
  * ``pair_corr``       -- ``rho(BTC,ETH)`` auf 30-Minuten-Renditen aus dem
    WP-0-Bar-Cache (``bybit_edge.research.bar_cache.load_minute_bars``),
    Pearson + Spearman mit Block-Bootstrap-CI (Block=1 Tag), Seed als
    DEC-53-Artefakt.
  * ``report``          -- Befund B1..B5 mit vorab fixierter Konsequenz
    (woertlich aus PRD 4.1), N_eff/rho(BTC,ETH) mitberichtet, JSON+MD.

Everything in here is read-only with respect to existing data and NEVER
writes under ``data/harvest`` (Schutzgut).
"""
from __future__ import annotations
