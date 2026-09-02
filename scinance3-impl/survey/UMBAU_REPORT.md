# Umbau-Report -- Scinance 3.0 Phase 2 (Repo aufraeumen)

Datum: 2026-09-02. Branch: `claude/subagent-prd-development-T16fE`. Nichts committet
(Orchestrator committet nach Review).

## 1. Testergebnis: Baseline vs. Nachher

| | Baseline (vor Umbau) | Final (nach Umbau) |
|---|---|---|
| Collected (N, aus dem echten Lauf) | 1495 | 1495 |
| Passed | 1483 | 1483 |
| Failed | 3 | 3 (identische 3 Tests) |
| Skipped | 9 | 9 (identische 9 Tests) |
| Collection-Errors | 0 | 0 |
| Laufzeit | 901.4s | 882.4s |
| `pytest --collect-only -q` | 1491 | 1491 |

Ergebnis ist ein exakter Match -- gleiche Anzahl, gleiche 3 Fehlschlaege
(alle in `test_execution_live.py`, Sandbox-/torch-Abwesenheit-bedingt,
bereits vor dem Umbau rot), gleiche 9 Skips (5x torch fehlt: m1/m18/m19/
training/c15_grammar-Transformer-Pfad, 4x optuna fehlt: tuning). Kein
einziger Test verloren, keiner neu rot, keine neuen Skips. Details:
`scratchpad/survey/BASELINE_TESTS.txt`.

**Vier Forensik-Tests** (`test_replay_backtester_maker_only.py`,
`test_strategy3_bounded_exits.py`, `test_strategy_direction_inversion.py`,
`test_strategy1_rho_instrument.py`): `git diff --stat` = leer (byteidentisch),
29/29 gruen.

**DoD-Checks (alle erfuellt):**
- `grep -rn "bybit_edge\.\(layers\|strategies\|live_runner\|pipeline\)" src/bybit_edge/research scripts/c* scripts/wp*` -> leer.
- `python -c "import bybit_edge.research.bar_cache, bybit_edge.recorder, bybit_edge.persistence.db"` -> OK.
- `git status` zeigt nur Renames (173) + neue Dateien (9) + Import-Zeilen-Diffs (48 M) + 1 D (cosmetic, s. §5).

## 2. Verschiebungen (git mv, alle §1.1-1.3 umgesetzt)

- **§1.1** 4 Doku-Frameworks -> `archive/v1_frameworks/{edge_research_framework,edge-reconciliation,edge-research-v3,implementation_framework}/`.
  `FINAL_PRD.md` -> `scinance2-impl/FINAL_PRD_SCINANCE2.md` (als letzter Schritt).
- **§1.2** 9 Legacy-Skripte -> `archive/v1_scripts/` (backtest.py, backfill.py,
  dashboard.py, train_models.py, tune.py, replay_all.py, replay_backtest.py,
  _profile_replay.py, setup_local.sh).
- **§1.3** Toter Code -> `src/bybit_edge/_legacy_v1/` (Paketstruktur erhalten):
  `layers/`, `strategies/`, `collector/`, `dashboard/`, `execution/`, `risk/`,
  `training/`, `tuning/`, `backtester/`, `state/`, `persistence/backfill.py`
  (samt neuem `_legacy_v1/persistence/__init__.py`), `live_runner.py`,
  `multi_runner.py`, `pipeline.py`, `decision_aggregator.py`, `monitor.py`,
  `scheduler.py`, `__main__.py`, `replay_backtester.py`, `replay_all.py`.
  `src/bybit_edge/_legacy_v1/__init__.py` mit Docstring erstellt (warum tot,
  Zitate CLEANUP_PLAN.md/WAVE1_FINAL_REPORT.md §4/decisions.md DEC-14).

Insgesamt 173 saubere Git-Renames. `config.py`, `recorder/`, `persistence/db.py`,
`research/**` unangetastet.

## 3. Import-Umschreibung

**Automatisiert** (`bybit_edge.<X>` -> `bybit_edge._legacy_v1.<X>` fuer die
verschobenen Top-Level-Namen) in 49 Dateien innerhalb `_legacy_v1/` (Selbst-
referenzen) + 1 Docstring-Kommentar (`research/c14_panellag/encoder.py`,
zaehlt fuer den §4.5-Grep) + 41 nicht-forensische Testdateien (Import-Zeilen
und String-Patch-/Monkeypatch-/caplog-Logger-Targets, z. B.
`monkeypatch.setattr("bybit_edge.live_runner...")` ->
`"bybit_edge._legacy_v1.live_runner..."`).

**Manuell nachgezogen** (Formen, die das automatisierte Muster nicht erfasst
hat -- `from bybit_edge.X import Y`-Paketform und in Funktionskoerpern
eingerueckte Imports):
- `tests/unit/test_backfill.py`: `from bybit_edge.persistence import backfill`
  -> `from bybit_edge._legacy_v1.persistence import backfill`; sowie zwei
  eingerueckte `import scripts.backfill` -> `import archive.v1_scripts.backfill`.
- `tests/unit/test_dashboard.py`: eingeruecktes
  `from bybit_edge import live_runner as lr_mod` ->
  `from bybit_edge._legacy_v1 import live_runner as lr_mod` (dieser Fund kam
  erst durch den vollen Testlauf ans Licht, s. §6).
- `tests/unit/test_backtest_driver.py`, `test_replay_all.py`,
  `test_replay_backtest_cli.py`: `scripts.{backtest,replay_all,replay_backtest}`
  -> `archive.v1_scripts.{...}` (3 archivierte Skripte werden von 32 Tests
  importiert; ihre `bybit_edge.*`-Imports wurden auf `_legacy_v1` umgestellt,
  damit sie importierbar bleiben -- s. §5).
- `tests/unit/test_e15_eval.py`: `ITER4_DIR`-Konstante zeigte hart auf
  `edge-reconciliation/input/iter4_raw/` (jetzt
  `archive/v1_frameworks/edge-reconciliation/input/iter4_raw/`) -- ohne Fix
  haette der reale iter-4-Regressionstest lautlos geskippt (s. §6).
- `src/bybit_edge/_legacy_v1/dashboard/data.py`: Default-Pfad-Konstante
  `_DEFAULT_REPLAY_RESULTS_DIR` von `edge_research_framework/results` auf
  `archive/v1_frameworks/edge_research_framework/results` aktualisiert
  (toter Code, aber jetzt korrekt statt still falsch).

Insgesamt 42 Testdateien mit Import-Edits (41 automatisiert + `test_e15_eval.py`
manuell; `test_backfill.py`/`test_dashboard.py`/`test_backtest_driver.py`/
`test_replay_all.py`/`test_replay_backtest_cli.py` zaehlen in den 41 automatisiert
mit UND hatten zusaetzlich einen manuellen Nachschlag).

## 4. Kompatibilitaets-Shims (DEC-51)

- `src/bybit_edge/strategies/__init__.py`: registriert die 5 realen
  `_legacy_v1.strategies.*`-Submodule unter den ALTEN Namen in `sys.modules`
  (identisches Modul-Objekt unter altem UND neuem Pfad) -- notwendig, weil
  `test_strategy3_bounded_exits.py` mit
  `patch("bybit_edge.strategies.strategy3_pre_settlement.time.time", ...)`
  arbeitet; ein reiner Re-Export haette ein zweites, unabhaengiges Modul-Objekt
  erzeugt und der Patch waere wirkungslos geblieben.
- `src/bybit_edge/replay_backtester.py`: ersetzt `sys.modules[__name__]` waehrend
  des eigenen Imports durch das reale `_legacy_v1.replay_backtester`-Objekt
  (Self-Replace-Pattern) -- gleicher Grund.
- Verifiziert per `is`-Identitaetscheck (`bybit_edge.strategies.strategy3_pre_settlement
  is bybit_edge._legacy_v1.strategies.strategy3_pre_settlement` -> `True`) und
  per Testlauf: alle 29 Tests in den 4 Forensik-Dateien gruen.

## 5. Bewusste Abweichung von "Skripte muessen nicht lauffaehig bleiben"

Drei archivierte Skripte (`backtest.py`, `replay_all.py`, `replay_backtest.py`)
werden von 32 lebenden Tests importiert (`test_backtest_driver.py`,
`test_replay_all.py`, `test_replay_backtest_cli.py`) -- die Testsuite ist per
§0 ein Schutzgut ("wird NICHT reduziert"), das hoeher wiegt als "archivierte
Skripte muessen nicht lauffaehig sein". Deshalb wurden bei genau diesen 3
Skripten (+ `backfill.py`, ebenfalls von `test_backfill.py` importiert) die
`bybit_edge.*`-Imports auf `_legacy_v1` umgestellt -- macht sie importierbar,
nicht produktiv nutzbar (Config/Datenpfade/Live-Verbindungen bleiben
ungepflegt). Die anderen 5 archivierten Skripte (`dashboard.py`,
`train_models.py`, `tune.py`, `_profile_replay.py`, `setup_local.sh`) sind von
keinem Test erreicht und wurden NICHT angefasst.

## 6. Was der volle Testlauf zusaetzlich aufgedeckt hat

Ein rein grep-basierter Scan uebersieht eingerueckte (Funktionskoerper-)
Imports. Zwei Fund-Runden ueber den vollen Testlauf (14-15 Min. je Lauf)
deckten das auf und wurden gefixt (s. §3): `scripts.backfill` in
`test_backfill.py` (2 Stellen), `bybit_edge.live_runner`-Paketimport in
`test_dashboard.py`, und die hartcodierte `edge-reconciliation/`-Pfad-
Konstante in `test_e15_eval.py` (haette den echten iter-4-Regressionstest
lautlos zum Skip statt zum Pass gemacht -- deshalb wich Lauf 1 mit
10 Skips/1482 Passed vom Baseline-Bild ab; nach dem Fix exakter Match).
Drei volle Laeufe insgesamt durchgefuehrt, der letzte ist der massgebliche
(s. §1).

## 7. Neue Dateien (§3)

`README.md` (Root, komplett neu -- die drei Welten, Ordnerkarte, Shims,
Tests, Schutzgueter), `archive/README.md`, `archive/v1_frameworks/README.md`,
`archive/v1_scripts/README.md`, `scinance3-impl/README.md`. Alle ASCII-safe
(ae/oe/ue/ss), Verdikte zitieren CODE_MAP.md und WAVE1_FINAL_REPORT.md §4
("S1-S5 vollstaendig empirisch erledigt"). `pyproject.toml`: nur die
`description`-Zeile geaendert (3.0-Beschreibung), sonst unangetastet.

## 8. Nicht angefasst (wie verlangt, verifiziert)

`data/`, `scinance2-impl/**` (inkl. `CLAUDE.md`, das laut Spezifikation
historisch bleibt), `recorder/`, `config.py`, `persistence/db.py`,
`research/**`, root `.ps1`/`.bat`, `tests/fixtures/**` -- `git status`/
`git diff` fuer alle diese Pfade leer verifiziert.

## 9. Kleinere kosmetische Unschaerfe (kein Funktionsproblem)

`git status` zeigt EINE Datei (`src/bybit_edge/layers/l5_risk/__init__.py`)
als separates D statt als Teil eines Renames, weil Gits Aehnlichkeits-
Heuristik bei der sehr kurzen Datei nach der Pfad-Umschreibung unter die
Standard-Schwelle rutscht (der Inhalt liegt korrekt und vollstaendig unter
`_legacy_v1/layers/l5_risk/__init__.py`, als "A" gelistet). Ebenso wurden
zwei inhaltlich leere `__init__.py`-Dateien (state/, persistence/) von Git
untereinander statt mit ihrem eigentlichen Ziel gepaart (beide 0 Byte, fuer
Git ununterscheidbar) -- ebenfalls rein kosmetisch, Baumzustand korrekt.

## 10. Nicht editiert trotz Bezug auf verschobene Pfade (bewusst, Schutzgut)

`scripts/evaluate_e15.py` (explizit als Schutzgut in Spezifikation §2
gelistet) hat zwei Default-Pfad-Konstanten (`DEFAULT_RESULTS`/`DEFAULT_TRADES`),
die auf `edge_research_framework/results/` zeigen -- nach dem Umbau eine
tote Referenz. Betrifft aber KEINEN Test (alle Aufrufe in
`test_e15_eval.py` uebergeben `--results-path`/`--trades-path` explizit;
das Skript selbst dokumentiert "T2/T3-Runner setzen die Pfade explizit"
DEC-02). Da die Datei namentlich geschuetzt ist und nichts davon abhaengt,
wurde sie nicht angefasst -- Empfehlung fuer eine spaetere, entscheidungs-
protokollierte Bereinigung. `src/bybit_edge/research/c09_bunch/__init__.py`
und `c10_pointer/loaders.py` zitieren `edge-research-v3/results/*.md` in
Docstrings (Provenienz-Angaben) -- `research/**` ist Schutzgut, nicht
angefasst; rein kosmetisch (Kommentar), keine Funktionsauswirkung.
