# EDGE CODING FRAMEWORK — Bybit Edge Implementierung
## Master Orchestration für Claude Code (CODING / IMPLEMENTATION-Phase)

> **Aufgabe:** Führe die vollständige, kontrollierte Implementierung des in `../edge_research_framework/results/FINAL_PRD.md` spezifizierten Trading-Systems aus. Das Ziel ist produktionsreifer, getesteter, reviewter Code unter `src/bybit_edge/` — strikt entlang der PRD-Roadmap (Abschnitt 8) und unter Beachtung der PRD-Risiken (Abschnitt 9).
>
> Dieses Framework ist das **Coding-Pendant** zum Research-Framework. Es erfindet KEINE neuen Methoden — die Mathematik und Priorisierung sind im PRD eingefroren. Es überführt das PRD diszipliniert in Code, Tests und ein sauberes Hardware-Handoff.

---

## QUELLEN / REFERENZEN (Spec of Record)

- **Spezifikation (verbindlich):** `../edge_research_framework/results/FINAL_PRD.md`
  - **Abschnitt 4** — Methoden-Katalog M1–M26 (Formeln, Bybit-Endpoints, Hardware).
  - **Abschnitt 7** — die 5 Kombinationsstrategien.
  - **Abschnitt 8** — IMPLEMENTIERUNGS-ROADMAP (Phase 0–4) → **Quelle der Wahrheit für Reihenfolge & Backlog.**
  - **Abschnitt 9** — RISIKEN: Overfitting-Guards (9.1), API-/Funding-Konfigurierbarkeit (9.2), Regime-Abhängigkeiten (9.3), VRAM-Grenzen (9.4), Reproduzierbarkeit/Seeds (9.6).
- **Code-Baseline:** Commit `d5ed327` ("…379 tests pass") ist der aktuelle Stand. M1–M26, 5 Strategien, Collector, Persistence (DuckDB), Backtester, LiveRunner, Execution (bybit_executor), DecisionAggregator, Pipeline existieren bereits.
- Bei jedem Konflikt zwischen Code und PRD gilt: **PRD ist Spec, Code ist Ist-Zustand.** Differenzen werden im Backlog als Tasks erfasst, nicht stillschweigend geändert.

---

## PFLICHTLEKTÜRE VOR BEGINN

Lies diese Dateien **in dieser Reihenfolge**, bevor du irgendwelche Schritte ausführst:

1. `agents/01_orchestrator.md` — Zustandsmaschine, Quality Gates, Hardware-Gating-Policy
2. `agents/02_planner.md` — Backlog-Ableitung aus PRD §8
3. `agents/03_implementer.md` — Coding-Standards, PRD-Mathematik, Config-Driven-Params
4. `agents/04_test_engineer.md` — Test-Strategie, Marker, deterministische Seeds
5. `agents/05_reviewer.md` — Code-Critic, PASS/CONDITIONAL/REJECT
6. `agents/06_integrator.md` — Pipeline-Wiring + HARDWARE-Handoff-Paket
7. `progress/STATUS.md` — aktueller Implementierungs-/Test-/Review-Stand (Living Board)

---

## CONTEXT ENGINEERING RULES (für alle Agenten verbindlich)

Das "Lost in the Middle"-Problem gilt auch im Coding: lange Diffs und rohe Test-Logs überlagern die relevanten Signale. Daher:

- **Jeder Agent komprimiert seinen Output** auf das Wesentliche, bevor er ihn übergibt.
- **Kein Agent übergibt rohe pytest-/ruff-/mypy-Logs** — nur strukturierte, komprimierte Verdikte (PASS/FAIL + die konkreten Befunde).
- **Format für Übergaben:** Immer `[AGENT_NAME → EMPFÄNGER] STATUS | INHALT`
- **Maximale Übergabelänge:** 2000 Tokens pro Agenten-Output (komprimiert, dicht). Code-Diffs werden als Pfad + Kurzbeschreibung referenziert, nicht inline dupliziert.
- **Vergangene Iterations-Outputs** werden als Zusammenfassung in einem Block gehalten, nicht inline wiederholt.
- **Niemals einen ganzen Modul-Quelltext in eine Übergabe kopieren** — verweise auf den Dateipfad.

---

## HARDWARE-GATING-POLICY (HARTE REGEL — gilt überall)

Diese Sandbox hat **kein numpy / torch / duckdb / scipy installiert und keine GPU**. Der Nutzer fährt dependency-schwere Tests, GPU-Training, große Backtests und Live/Testnet-Bybit-Läufe auf **eigener Hardware** (RTX 5060 Ti Workstation + VPS).

Jede Aufgabe fällt in genau eine von zwei Klassen:

### A) SANDBOX-VERIFIZIERBAR (hier ausführbar)
- Reine Logik / Algorithmik in Pure-Python (keine harten 3rd-Party-Imports).
- Refactors, Wiring, Verdrahtung von Modulen, Config-Pfade.
- Statische Qualität: `ruff`, `mypy`, AST-/Import-Checks, Docstring-Vollständigkeit.
- Deterministische Backtest-/Aggregations-**Logik**, sofern ohne numpy lauffähig.
- Review gegen PRD-Formeln (Lesen + Vergleichen, kein Ausführen).

### B) HARDWARE-GATED (NICHT in der Sandbox ausführen)
Wird **niemals** in der Sandbox "verifiziert grün" gemeldet. Stattdessen erzeugt der Integrator ein **copy-pasteable Handoff-Paket** (Befehle, Env-Vars, erwartete Metriken). Gilt für:
- **torch/GPU:** M20 MOMENT LoRA-FineTune / MOMENT-base Training; jegliche optionale `[gpu]`-Extra-Pfade.
- **numpy/scipy/statsmodels/pandas/polars-abhängige Tests:** der Großteil der M-Modul-Unit-Tests (Modul-Implementierungen importieren numpy). Diese sind **CPU**, aber dependency-gated → laufen auf User-Maschine, nicht in Sandbox.
- **duckdb/persistence:** Persistence-Layer-Tests, alle Disk-Roundtrips.
- **Live-Bybit / WebSocket / Testnet:** Collector-Live-Lauf, `bybit_executor` gegen `api-testnet.bybit.com`, LiveRunner.
- **Große Backtests:** Multi-GB-Voll-Historie, Walk-Forward über 5y, Optuna-Sweeps.

**Verifikations-Wahrheit:** Ein Task darf nur dann `Done in sandbox` sein, wenn er Klasse A ist UND `ruff`+`mypy`+ggf. Pure-Python-Smoke grün sind. Klasse B endet immer in `Pending user hardware test` mit fertigem Handoff.

---

## AUSFÜHRUNGSPROTOKOLL

### Schritt 0 — Baseline-Aufnahme
Lies `progress/STATUS.md`. Bestätige den Ist-Zustand gegen Commit `d5ed327`. Liste offene Lücken (Modul ohne Test, Modul ≠ PRD-Formel, fehlendes Wiring).

### Schritt 1 — PLAN (Planner)
Planner liest PRD §8 und erzeugt den priorisierten Backlog (Phase 0→4). Output: interne Backlog-Tabelle + Update von `progress/STATUS.md`.

### Schritt 2 — IMPLEMENT (Implementer)
Pro Modul/Strategie, **strikt in Phasen-Reihenfolge**. Code unter `src/bybit_edge/`. Keine Phase N+1, bevor Phase N die Gates passiert hat (außer reine Klasse-B-Wartepositionen).

### Schritt 3 — TEST (Test Engineer)
Tests unter `tests/`. Marker setzen (`@pytest.mark.gpu`, `@pytest.mark.live`, `@pytest.mark.slow`, `@pytest.mark.requires_numpy` etc.), damit Klasse-B-Tests in der Sandbox skippen und auf Hardware laufen.

### Schritt 4 — REVIEW (Reviewer)
Code-Critic vergibt PASS / CONDITIONAL / REJECT je Modul gegen PRD-Formel + Risiko-Checks.

### Schritt 5 — REFINE (wenn CONDITIONAL/REJECT)
Gezielter Rework-Brief an Implementer/Test Engineer. Max. 2 Refine-Runden pro Modul, dann Eskalation an Orchestrator.

### Schritt 6 — INTEGRATE (Integrator)
Modul → `pipeline.py` / `decision_aggregator.py` / `live_runner.py` / `backtester/engine.py` verdrahten. Run-/Verify-Checklisten.

### Schritt 7 — HARDWARE_HANDOFF (Integrator)
Erzeuge das Handoff-Paket für alle Klasse-B-Arbeiten der aktuellen Phase: exakte Befehle, Env-Vars, erwartete Metriken (PRD §8: **Sharpe ≥ 1.5, Max-DD < 15 %, Win-Rate > 52 %**).

> **Git:** Dieses Framework committet/pusht NICHT selbst. Der übergeordnete Orchestrator/Mensch übernimmt Git.

---

## QUALITÄTSSCHWELLEN (Orchestrator prüft vor jedem Phasen-Übergang)

| Gate | Kriterium | Klasse |
|------|-----------|--------|
| G1 | `ruff check src tests` clean (0 Fehler) | A (Sandbox) |
| G2 | `mypy src/bybit_edge` clean (keine neuen Fehler vs. Baseline) | A (Sandbox) |
| G3 | Kein Modul ohne mindestens 1 Testdatei (`tests/unit/test_m<#>_*.py`) | A (Sandbox-prüfbar via Dateiexistenz) |
| G4 | Pure-Python-Smoke der Logik importierbar/aufrufbar, wo ohne numpy möglich | A (Sandbox) |
| G5 | Alle CPU-Unit-Tests grün **auf User-Hardware** (numpy verfügbar) | B (Handoff) |
| G6 | Coverage ≥ 80 % je neuem/geändertem Modul (Messung auf User-Hardware) | B (Handoff) |
| G7 | GPU-/Live-/Slow-Tests korrekt markiert und in Sandbox geskippt | A (Sandbox) |
| G8 | Backtest-Metriken erfüllen PRD-Ziel (Sharpe ≥1.5, MaxDD <15 %, WinRate >52 %) | B (Handoff) |
| G9 | Reviewer-Verdikt = PASS für das Modul | A (Sandbox) |

**Regel:** Eine Phase gilt erst als abgeschlossen, wenn alle Klasse-A-Gates grün sind UND alle Klasse-B-Gates ein vollständiges, übergebenes Handoff besitzen.

---

## REFERENZ-ARCHITEKTUR (Ist-Zustand des Repos)

```
src/bybit_edge/
├── collector/ws_collector.py        Bybit WebSocket (asyncio) — [LIVE-GATED]
├── persistence/db.py                DuckDB + Parquet              — [DUCKDB-GATED]
├── state/                           orderbook/ticker/trade/liquidation buffers (Pub/Sub)
├── layers/
│   ├── l1_ingestion/  M1, M2, M3
│   ├── l2_denoising/  M4, M5
│   ├── l3_regime/     M6–M13
│   ├── l4_pattern/    M14–M21
│   └── l5_risk/       M22–M26
├── strategies/        strategy1_cascade … strategy5_cross_sectional
├── decision_aggregator.py           Strategie-Selector + Sizing
├── pipeline.py                      Layer-Kaskade
├── backtester/engine.py             Event-Loop, Walk-Forward, Fees/Slippage
├── execution/bybit_executor.py      Signed REST — TESTNET-only       — [LIVE-GATED]
├── live_runner.py                   Live/Paper-Loop                  — [LIVE-GATED]
├── scheduler.py / monitor.py / config.py
```

Methoden-Layer-Mapping und Strategie-Methoden-Sets siehe PRD §4 und §7.

---

## ERGEBNIS-STRUKTUR

```
edge_coding_framework/
├── CLAUDE.md                  ← Diese Datei
├── README.md
├── agents/
│   ├── 01_orchestrator.md
│   ├── 02_planner.md
│   ├── 03_implementer.md
│   ├── 04_test_engineer.md
│   ├── 05_reviewer.md
│   └── 06_integrator.md
└── progress/
    └── STATUS.md              ← Living Status Board
```

---

## START

**Lies jetzt alle Agent-Dateien und `progress/STATUS.md`, beginne mit Schritt 0 (Baseline) und gehe dann in den Zyklus PLAN → IMPLEMENT → TEST → REVIEW → REFINE → INTEGRATE → HARDWARE_HANDOFF.**

Berichte nach jedem abgeschlossenen Schritt mit:
`[ORCHESTRATOR] PHASE: {0-4} | STEP: {step} | SANDBOX_GATES: {G1..G4,G7,G9 PASS/FAIL} | HANDOFF_PENDING: {liste} | NEXT: {action}`
