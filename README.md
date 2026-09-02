# Scinance 3.0

Dieses Repo ist der Nachfolgezustand von "Scinance 2.0" (siehe
`scinance2-impl/`). Es enthaelt EIN Python-Paket (`bybit_edge`) mit einem
einzigen Import-Graphen -- kein `v1/`/`v2/`/`v3/`-Ordner-Nebeneinander im
Code. Versionsordner gibt es nur fuer Akten und Artefakte (Registry,
Gate-Log, Decisions, Runner-Ergebnisse), nicht fuer Code. Details und
Begruendung: `scinance3-impl/UMBAU_SPEZIFIKATION.md` §0.

## Die drei Welten

| Welt | Wo | Status |
|---|---|---|
| **Scinance 1.0** -- der urspruengliche Live-Trading-Stack (26 Methoden L1-L5, Strategien S1-S5, Live-Order-Pfad) | Code: `src/bybit_edge/_legacy_v1/`. Aufraeum-Entscheidung: `scinance2-impl/state/CLEANUP_PLAN.md`, `scinance2-impl/state/WAVE1_FINAL_REPORT.md`, `scinance2-impl/state/decisions.md` (DEC-14) | **Tot, aber quarantaeniert** -- importierbar, getestet, sichtbar als tot. Alle fuenf Strategien S1-S5 sind empirisch DROP; die L1-L5-Layer-Module dienten ausschliesslich diesen Strategien. Live-Order-Code (`execution/`, `risk/`) ist durch das Projekt-Statut verboten. |
| **Scinance 2.0** -- die Forschungs-Akte (Hypothesen, Gate-Log, Wave-Reports, Handoff-Runner fuer die Nutzer-Maschine) | `scinance2-impl/` (Akte, append-only, historisch -- **nicht anpassen**) | Laufend gepflegt; `scinance2-impl/CLAUDE.md` ist ein historisches Dokument und bleibt unveraendert. |
| **Scinance 3.0** -- der aktuelle Umbau (dieses Repo aufraeumen, Doku aktualisieren) | `scinance3-impl/` | Phase 2 (Repo-Aufraeumung) abgeschlossen; Verfassung/Plan fuer die naechsten Phasen folgt dort. |

## Ordnerkarte

```
src/bybit_edge/
  config.py            Zentrale Konfiguration (Endpunkte, Universum, PRD-Konstanten) -- LEBEND
  recorder/             C-36-Recording-Engine (Schutzgut #1, laeuft kontinuierlich) -- LEBEND
  persistence/db.py     DuckDB-Layer, wird noch von 4 lebenden Research-Treibern gelesen -- LEBEND
  research/              RESEARCH-V2: alle c*/wp*-Subpakete, von scripts/c*.py und
                          scripts/wp*.py angetrieben -- LEBEND
  _legacy_v1/            Scinance-1.0-Stack (layers/, strategies/, collector/, dashboard/,
                          execution/, risk/, training/, tuning/, backtester/, state/,
                          persistence/backfill.py, live_runner.py, multi_runner.py,
                          pipeline.py, decision_aggregator.py, monitor.py, scheduler.py,
                          __main__.py, replay_backtester.py, replay_all.py) -- TOT, quarantaeniert
  strategies/, replay_backtester.py
                          Kompatibilitaets-Shims (siehe unten) -- NUR fuer 4 Forensik-Tests

scripts/                 RESEARCH-V2-Treiber (c*.py, wp*.py) -- LEBEND
archive/v1_scripts/       Scinance-1.0-Skripte (backtest.py, backfill.py, dashboard.py,
                          train_models.py, tune.py, replay_all.py, replay_backtest.py,
                          _profile_replay.py, setup_local.sh) -- nicht mehr gepflegt
archive/v1_frameworks/    Reine Markdown-Multiagenten-Frameworks (0 Code), die zu den
                          fruehen PRD-Entwuerfen fuehrten

scinance2-impl/           Scinance-2.0-Forschungsakte (append-only, historisch)
scinance3-impl/           Scinance-3.0-Umbau-Akte (Spezifikation, State, Survey)

tests/unit/                Testsuite -- deckt lebenden UND toten Code ab (letzterer bewusst,
                          als Audit-Trail; siehe Schutzguter unten)
```

## Kompatibilitaets-Shims (DEC-54)

Vier Forensik-Tests (`tests/unit/test_replay_backtester_maker_only.py`,
`test_strategy3_bounded_exits.py`, `test_strategy_direction_inversion.py`,
`test_strategy1_rho_instrument.py`) muessen byteidentisch bleiben und
importieren daher weiterhin die ALTEN Pfade
(`bybit_edge.strategies.*`, `bybit_edge.replay_backtester`). Diese Pfade
existieren als duenne Shims, die denselben Modul-Objekt-Verweis wie
`bybit_edge._legacy_v1.strategies.*` / `bybit_edge._legacy_v1.replay_backtester`
in `sys.modules` registrieren -- ein `mock.patch(...)` ueber den alten Pfad
trifft also exakt dasselbe Objekt, das der getestete Code tatsaechlich
benutzt. Kopfkommentar in den Shim-Dateien: "compat shim for untouchable
forensic tests (DEC-54)". Neuer Code soll NICHT gegen diese Shims schreiben
-- direkt `bybit_edge._legacy_v1.*` verwenden.

## Tests

```
pip install -e ".[dev,vol]" pykalman filterpy hmmlearn PyWavelets numba \
    statsmodels sortedcontainers structlog websockets aiohttp polars
PYTHONPATH=src python -m pytest tests/unit -q
```

`torch`/`streamlit` sind optionale Extras (`.[gpu]`, `.[dashboard]`); ohne
sie skippen/fallen einzelne Tests wie vorher -- das ist erwartet, nicht
kaputt. Die Testsuite wird durch diesen Umbau NICHT reduziert (Schutzgut,
siehe `scinance3-impl/UMBAU_SPEZIFIKATION.md` §0/§4).

## Schutzgueter (unangetastet)

- `start.bat`, `start_recorder.ps1`,
  `install_/uninstall_recorder_autostart.ps1` -- Windows-Task-Scheduler-
  Registrierungen zeigen per absolutem Pfad hierher.
- `src/bybit_edge/recorder/**`, `config.py`, `persistence/db.py`,
  `research/**` -- lebender Code.
- `scinance2-impl/**` -- komplett, insbesondere `handoff_local/*.ps1`
  (Scheduled Task "BybitOptChainSnap" zeigt darauf).
- `scripts/{c*.py, wp*.py, build_bar_cache.py, evaluate_e15.py, l2_census.py}`
  -- RESEARCH-V2-Treiber.
- `tests/fixtures/**`, `data/harvest` (read-only Junction),
  `data/parquet/recording_f0/` (wird vom Recorder geschrieben, auch wenn
  ungelesen -- kein toter Code zum Loeschen).

Vollstaendige Begruendung, Import-Graph-Evidenz und Einzelverdikte: siehe
`scinance3-impl/UMBAU_SPEZIFIKATION.md` und die Phase-1-Kartierung
(Code-Map, Infra/Ops-Map, Erkenntnis-Kompendium) unter
`scinance3-impl/survey/`.
