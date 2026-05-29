# Edge Coding Framework

Autonomes **Implementierungs-Framework** für das Projekt *Bybit Edge*. Es überführt das eingefrorene Spezifikationsdokument `../edge_research_framework/results/FINAL_PRD.md` diszipliniert in produktionsreifen, getesteten und reviewten Code unter `src/bybit_edge/`.

Dies ist das Coding-Pendant zum `edge_research_framework/`: dort wurde *geforscht und ein PRD erzeugt*, hier wird *implementiert*. Es werden **keine neuen Trading-Methoden erfunden** — die Mathematik (M1–M26) und Priorisierung (PRD §8) sind fixiert.

## Kernidee

Ein Orchestrator dirigiert fünf spezialisierte Agenten entlang einer Zustandsmaschine
(`INIT → PLAN → IMPLEMENT → TEST → REVIEW → REFINE → INTEGRATE → HARDWARE_HANDOFF → DONE`).
Jeder Schritt hat explizite **Quality Gates** und eine harte **Hardware-Gating-Policy**: Diese Sandbox hat
kein numpy/torch/duckdb und keine GPU — dependency-schwere Tests, GPU-Training, große Backtests und
Live/Testnet-Bybit-Läufe werden **nicht hier ausgeführt**, sondern als copy-pasteable Handoff-Paket
an die Nutzer-Hardware (RTX 5060 Ti + VPS) übergeben.

## Struktur

```
edge_coding_framework/
├── CLAUDE.md                  Master-Orchestration: Protokoll, Gates, Hardware-Policy, Referenzen
├── README.md                  Diese Datei
├── agents/
│   ├── 01_orchestrator.md     Zustandsmaschine, Task-Decomposition aus PRD §8, Gates, Gating
│   ├── 02_planner.md          Backlog aus PRD §8 (per Modul/Strategie/Integration), Dependencies, Dateiziele
│   ├── 03_implementer.md      Produktionscode nach PRD-Mathematik; async/numba/config-driven; Docstrings
│   ├── 04_test_engineer.md    pytest unit/integration/backtest; Coverage-Ziele; Seeds; GPU/Live-Marker
│   ├── 05_reviewer.md         Code-Critic vs. PRD-Formeln + Overfitting/API-Guards; PASS/CONDITIONAL/REJECT
│   └── 06_integrator.md       Wiring in pipeline/aggregator/live_runner/backtester; HARDWARE-Handoff-Paket
└── progress/
    └── STATUS.md              Living Board: Implement/Test/Review-Stand je Modul; Sandbox vs. Hardware
```

## Konventionen

- **Sprache:** Deutsch (technische Begriffe / Code bleiben englisch), analog zum Research-Framework.
- **Übergabeformat:** `[AGENT → EMPFÄNGER] STATUS | INHALT`, ≤ 2000 Tokens, komprimiert, keine rohen Logs.
- **Spec of Record:** `../edge_research_framework/results/FINAL_PRD.md` (§4 Methoden, §7 Strategien, §8 Roadmap, §9 Risiken).
- **Baseline:** Commit `d5ed327` ("…379 tests pass").
- **Git:** Dieses Framework committet/pusht NICHT selbst — das übernimmt der übergeordnete Orchestrator/Mensch.

## Einstieg

Lies `CLAUDE.md`, dann die Agent-Dateien in nummerierter Reihenfolge, dann `progress/STATUS.md`.
Beginne mit der Baseline-Aufnahme und durchlaufe anschließend den Zyklus pro Roadmap-Phase.
