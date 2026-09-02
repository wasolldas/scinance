# Scinance 3.0 - Umbau-Spezifikation (Phase 2: Repo aufraeumen)

> Orchestrator-Entscheidung 2026-09-02, Grundlage: Code-Map, Infra/Ops-Map
> (Phase-1-Kartierung, drei unabhaengige Agenten) und der bestehende
> `scinance2-impl/state/CLEANUP_PLAN.md` (2026-06-23), dessen Verdikte
> per Import-Graph bestaetigt wurden.

## 0. Grundsatz: Versionsordner fuer AKTEN und ARTEFAKTE, nicht fuer Code

Der Code ist EIN Python-Paket mit einem Import-Graphen. Starre `v1/`, `v2/`,
`v3/`-Ordner fuer Code wuerden entweder ~13.000 Zeilen Import-Umschreibungen
erzwingen oder doppelte Pakete erzeugen. Deshalb:

| Ebene | Regel |
|---|---|
| Programm-Akten (Registry, Gate-Log, Decisions, Befunde, Runner) | je Version ein Ordner: `scinance2-impl/` (bleibt UNVERAENDERT, append-only), `scinance3-impl/` (neu) |
| Verworfene Ansaetze ohne Code (Agent-Frameworks, alte PRD-Entwuerfe) | `archive/v1_frameworks/<name>/` mit README je Ordner |
| Toter Code (Scinance-1.0-Stack) | bleibt im Paket, aber quarantaeniert unter `src/bybit_edge/_legacy_v1/` - importierbar, getestet, sichtbar als tot |
| Lebender Code | `src/bybit_edge/{config.py, recorder/, persistence/db.py, research/}` |
| Legacy-Skripte | `archive/v1_scripts/` (nicht gewartet, README) |

Schutzgueter bleiben unangetastet: Recorder-Pfade, Junction, Scheduled-Task-
Ziele, Harvest-Baum read-only, Test-Suite wird NICHT reduziert.

## 1. Verschiebungen (alle per `git mv`, nie loeschen)

### 1.1 Doku-Frameworks (0 Code, 0 Automations-Referenzen)
- `edge_research_framework/`  -> `archive/v1_frameworks/edge_research_framework/`
- `edge-reconciliation/`      -> `archive/v1_frameworks/edge-reconciliation/`
- `implementation_framework/` -> `archive/v1_frameworks/implementation_framework/`
- `edge-research-v3/`         -> `archive/v1_frameworks/edge-research-v3/`
- `FINAL_PRD.md`              -> `scinance2-impl/FINAL_PRD_SCINANCE2.md`
  (die 2.0-Verfassung gehoert zur 2.0-Akte; `scinance2-impl/CLAUDE.md` bleibt
  wie sie ist - historisches Dokument, nicht anpassen)

### 1.2 Legacy-Skripte
`scripts/{backtest.py, backfill.py, dashboard.py, train_models.py, tune.py,
replay_all.py, replay_backtest.py, _profile_replay.py, setup_local.sh}`
-> `archive/v1_scripts/`. Nicht lauffaehig halten muessen; README sagt das.

### 1.3 Toter Code -> `src/bybit_edge/_legacy_v1/`
Verschieben (Paketstruktur darunter beibehalten):
`layers/`, `strategies/`, `collector/`, `dashboard/`, `execution/`, `risk/`,
`training/`, `tuning/`, `backtester/`, `state/`, `persistence/backfill.py`,
`live_runner.py`, `multi_runner.py`, `pipeline.py`, `decision_aggregator.py`,
`monitor.py`, `scheduler.py`, `__main__.py` (der Live-Entry), `replay_backtester.py`,
`replay_all.py`.

NICHT verschieben: `config.py`, `recorder/`, `persistence/db.py` (wird von 4
lebenden Research-Treibern gelesen), `research/`.

Import-Umschreibung: in ALLEN verschobenen Modulen und in ALLEN Tests, die sie
importieren, `bybit_edge.<x>` -> `bybit_edge._legacy_v1.<x>` fuer genau die
verschobenen Namen. `bybit_edge.config` und `bybit_edge.persistence.db` bleiben.

**Ausnahme - die 4 Forensik-Tests bleiben byteidentisch:**
`test_replay_backtester_maker_only.py`, `test_strategy3_bounded_exits.py`,
`test_strategy_direction_inversion.py`, `test_strategy1_rho_instrument.py`.
Fuer die Module, die sie importieren, werden am ALTEN Pfad Kompatibilitaets-
Shims angelegt (Ein-Zeilen-Re-Export, z. B. `src/bybit_edge/strategies/__init__.py`
+ `strategy1_cascade.py` mit `from bybit_edge._legacy_v1.strategies.strategy1_cascade import *`
plus expliziten Namen, falls `__all__` fehlt). Shims tragen einen Kopfkommentar
"compat shim for untouchable forensic tests (DEC-51)".

`src/bybit_edge/_legacy_v1/__init__.py` erhaelt einen Docstring: was das ist,
warum es tot ist (WAVE1_FINAL_REPORT, CLEANUP_PLAN), dass nichts davon
importiert werden darf ausser durch seine eigenen Tests.

### 1.4 Tests
Bleiben unter `tests/unit/`. Nur Import-Zeilen werden angepasst (ausser
Forensik-Tests, s. o.). Anzahl gesammelter Tests VORHER == NACHHER (Abnahme).

## 2. Was NICHT angefasst wird (Schutzgueter / Kopplungen)
- `start.bat`, `start_recorder.ps1`, `install_/uninstall_recorder_autostart.ps1`
- `scinance2-impl/**` (komplett; insbesondere `handoff_local/*.ps1`, weil
  Scheduled Task "BybitOptChainSnap" und `start.bat` darauf zeigen)
- `src/bybit_edge/recorder/**`, `config.py`, `persistence/db.py`, `research/**`
- `scripts/{c*.py, wp*.py, build_bar_cache.py, evaluate_e15.py, l2_census.py}`
- `tests/fixtures/**`, `pyproject.toml` (ausser Beschreibung), `.gitignore`

## 3. Neue Dateien
- `README.md` (Root) neu: Was das Repo JETZT ist (3.0), Ordnerkarte, die drei
  Welten, wo die Akten liegen, wie Tests laufen, Schutzgueter.
- `archive/README.md`, `archive/v1_frameworks/README.md`, `archive/v1_scripts/README.md`
- `scinance3-impl/README.md` (Zeiger auf Verfassung/Plan, folgt in Phase 3/4)

## 4. Abnahme (Definition of Done)
1. `pytest tests/unit -q` sammelt vorher N Tests; nachher ebenfalls N (oder mehr),
   alle gruen, in derselben Umgebung. Sandbox-Deps installieren:
   `pip install -e ".[dev,vol]" pykalman filterpy hmmlearn PyWavelets numba
   statsmodels sortedcontainers structlog websockets aiohttp polars`.
   Torch/streamlit optional: Tests, die sie brauchen, muessen wie VORHER
   skippen/failen - nicht schlechter.
2. `git status` zeigt nur Renames + die neuen Dateien + Import-Zeilen-Diffs.
3. Die 4 Forensik-Tests: `git diff --stat` zeigt 0 Zeilen Aenderung.
4. `python -c "import bybit_edge.research.bar_cache, bybit_edge.recorder"` ok.
5. `grep -rn "bybit_edge\.\(layers\|strategies\|live_runner\|pipeline\)" src/bybit_edge/research scripts/c* scripts/wp*` liefert NICHTS (kein lebender Code haengt am Legacy).
