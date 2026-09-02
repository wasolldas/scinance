"""bybit_edge._legacy_v1 -- Scinance-1.0-Live-Stack, quarantaeniert (tot, aber sichtbar).

Was das ist
-----------
Der komplette Scinance-1.0-Live-Trading-Stack: L1-L5-Methoden-Layer
(``layers/``), die fuenf Kombinationsstrategien S1-S5 (``strategies/``),
der Live-Order-Pfad (``execution/``, ``risk/``), der WS-Collector
(``collector/``), das Streamlit-Dashboard (``dashboard/``), der klassische
Bar-Backtester (``backtester/``), Training/Tuning fuer die L4-Pattern-
Modelle (``training/``, ``tuning/``), die Online-State-Aggregatoren
(``state/``), der REST-Kline-Backfill (``persistence/backfill.py``) sowie
die Runner/Glue-Module (``live_runner.py``, ``multi_runner.py``,
``pipeline.py``, ``decision_aggregator.py``, ``monitor.py``,
``scheduler.py``, ``__main__.py``) und die Forensik-Werkzeuge
(``replay_backtester.py``, ``replay_all.py``).

Warum es tot ist
-----------------
- Alle fuenf Strategien S1-S5 sind empirisch DROP -- siehe
  ``scinance2-impl/state/WAVE1_FINAL_REPORT.md`` Abschnitt 4/5. Die
  L1-L5-Layer-Module wurden ausschliesslich von diesen Strategien
  konsumiert; ohne sie haben sie keinen lebenden Aufrufer mehr.
- Der Cleanup-Schnitt DEC-14 (2026-06-23,
  ``scinance2-impl/state/CLEANUP_PLAN.md``, ``scinance2-impl/state/decisions.md``)
  hat den gesamten Live-Stack DEPRECATE gesetzt: kein Live-Order-Betrieb
  mehr, der Bybit-Collector wird operativ durch den externen Harvester
  ersetzt, ``m8_bocpd.py``s bekannter Off-by-One-Bug bleibt bewusst
  ungefixt (der Live-Pfad, der ihn ausloesen wuerde, existiert nicht mehr).
- Live-Order-Code (``execution/``, ``risk/``) ist durch das Projekt-Statut
  (``scinance2-impl/CLAUDE.md``, Autonomie-Protokoll) explizit verboten;
  dieser Code stammt aus der Zeit vor dieser Regel und ist inert.
- Die Verschiebung hierher (Phase 2, Umbau-Spezifikation
  ``scinance3-impl/UMBAU_SPEZIFIKATION.md``) ist rein organisatorisch:
  das DEPRECATE-Verdikt selbst wurde bereits am 2026-06-23 gefaellt, hier
  wird nur die Quarantaene im Dateibaum sichtbar gemacht.

Was das NICHT betrifft
-----------------------
``bybit_edge.config``, ``bybit_edge.recorder`` (Schutzgut #1, laeuft
kontinuierlich), ``bybit_edge.persistence.db`` (wird noch von vier
lebenden RESEARCH-V2-Treibern gelesen) und ``bybit_edge.research`` sind
NICHT hier drin -- die sind lebender Code und bleiben an ihrem Platz.

Import-Regel
------------
Aus diesem Package darf NICHTS von aussen importiert werden -- ausser von
seinen eigenen Tests (``tests/unit/test_m*.py``, ``test_strategies.py``,
``test_strategy3.py``, ``test_pipeline.py``, ``test_multi_runner.py``,
``test_execution_live.py``, ``test_risk_budget.py``, ``test_training.py``,
``test_tuning.py``, ``test_dashboard.py``, ``test_backfill.py``,
``test_replay_backtester.py``, ``test_replay_all.py``,
``test_replay_backtest_cli.py``, ``test_backtest_driver.py``,
``test_infrastructure.py``) sowie den vier byteidentischen Forensik-Tests,
die ueber Kompatibilitaets-Shims am alten Pfad weiterlaufen (siehe
``bybit_edge._legacy_v1.strategies`` und ``bybit_edge._legacy_v1.replay_backtester`` -- Kopfkommentar
"compat shim for untouchable forensic tests (DEC-51)"). Kein lebender
RESEARCH-V2-Code (``bybit_edge.research.*``) und keine ``scripts/c*.py``/
``scripts/wp*.py``-Treiber duerfen hierher importieren.
"""
