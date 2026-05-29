# BYBIT EDGE SYSTEM — Implementierungs-Framework
## Claude Code · Python · Phase 0–4 · 24 Wochen

> **Aufgabe:** Implementiere das PRD `FINAL_PRD.md` vollständig in Python. Das Ergebnis ist ein lauffähiges, getestetes Bybit-Algotrading-System, das auf Windows (RTX 5060 Ti) entwickelt und auf einem Linux-VPS (Docker) deployed wird. Alle Ergebnisse werden laufend in ein GitHub-Repository gepusht.

---

## PFLICHTLEKTÜRE VOR BEGINN

Lies in dieser Reihenfolge:
1. `FINAL_PRD.md` (oder die mitgelieferte PRD-Datei) — die Spezifikation
2. `agents/01_analyst.md` — einmalige PRD-Analyse, erzeugt `results/task_graph.json`
3. `agents/02_infra_builder.md` — Phase 0: Infrastruktur
4. `agents/03_module_builder.md` — Phase 1–4: Methoden M1–M26
5. `agents/04_test_engineer.md` — Tests nach jedem Modul
6. `agents/05_integrator.md` — Pipeline + Strategien + Decision Aggregator
7. `agents/06_devops.md` — GitHub, Windows-Setup, Docker-VPS

---

## PROJEKT-STRUKTUR (Target)

```
bybit-edge/
├── src/bybit_edge/
│   ├── collector/          # WebSocket-Streams
│   ├── state/              # OrderbookState, TickerState etc.
│   ├── persistence/        # DuckDB + Parquet
│   ├── layers/
│   │   ├── l1_ingestion/   # M1 SpikeWavformer, M2 OFI, M3 Iceberg
│   │   ├── l2_denoising/   # M4 Wavelet-Symlet, M5 FFD
│   │   ├── l3_regime/      # M6–M13
│   │   ├── l4_pattern/     # M14–M21
│   │   └── l5_risk/        # M22–M26
│   ├── strategies/         # Strategie 1–5
│   ├── backtester/         # Walk-Forward, Fees, Slippage
│   ├── execution/          # Bybit V5 REST (Testnet/Live)
│   └── config.py           # Alle konfigurierbaren Parameter
├── tests/
│   ├── unit/               # pro Modul
│   ├── integration/        # Layer-Kombinationen
│   └── backtests/          # Walk-Forward-Ergebnisse
├── scripts/
│   ├── setup_windows.bat   # conda + CUDA-Setup
│   ├── start_collector.bat
│   └── run_backtest.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── pyproject.toml          # gepinnte Abhängigkeiten
├── environment.yml         # conda (Windows + CUDA)
└── README.md
```

---

## CONTEXT ENGINEERING RULES

- **Jeder Agent** produziert ausschließlich Python-Code + Tests
- **Keine Platzhalter:** `pass`, `TODO`, `...` sind verboten — jede Funktion ist vollständig implementiert
- **PRD ist Gesetz:** Formeln, Schwellenwerte, Library-Namen exakt aus dem PRD übernehmen
- **Event-Time-Indexing:** absolut kein Lookahead — strikt in allen Berechnungen
- **Nach jedem Modul:** `pytest tests/unit/test_{modul}.py` ausführen, dann git commit

---

## AUSFÜHRUNGSPROTOKOLL

### Session 1 — Analyse + Infrastruktur
```
1. Analyst ausführen → results/task_graph.json
2. GitHub-Setup: bash setup_github.sh
3. Infra Builder ausführen → komplette Phase 0
4. Tests: pytest tests/unit/ -v
5. git commit -m "Phase 0: Infrastructure complete"
6. git push
```

### Session 2+ — Module (phasenweise)
```
Pro Modul M_N:
1. Module Builder: Implementiere M_N nach PRD-Spec
2. Test Engineer: pytest tests/unit/test_M{N}.py
3. Wenn Tests PASS: git commit -m "M{N}: {name} implemented + tested"
4. Wenn Tests FAIL: debugge, max. 3 Versuche, dann Fehler dokumentieren
5. git push
```

Reihenfolge strikt nach PRD-Priorität:
Phase 0 → M22 → M23 → M24 → M2 → M7 → M8 → M15 → M26 → M14a → M25 → M6 → M4 → M9 → M5 → M14b → M16 → M18 → M19 → M20 → M17 → M13 → M21 → M1 → M11 → M12 → M10 → M3

### Session N — Integration
```
1. Integrator: Pipeline L1→L2→L3→L4→L5
2. Decision Aggregator
3. Strategie 3 (Pre-Settlement, erste live-paper-Version)
4. Backtest Walk-Forward auf 6M Daten
5. Strategie 1, 2, 4, 5
6. git push mit Backtest-Ergebnissen
```

---

## QUALITÄTSSCHWELLEN (Agent prüft selbst)

| Kriterium | Schwelle |
|-----------|----------|
| Unit-Test-Pass-Rate | 100 % vor Commit |
| Walk-Forward-Sharpe M22 | ≥ 1.5 |
| Walk-Forward-Sharpe M2 (OFI) | ≥ 1.0 |
| Backtest Max-DD | < 15 % |
| Python-Linting (ruff) | 0 Errors |
| Type-Hints | alle öffentlichen Funktionen |

---

## WINDOWS-SPEZIFIK

```bash
# Windows-kritische Probleme, die du kennen musst:
# 1. `tick` Library (Hawkes MLE) → NUR Linux/macOS nativ
#    Windows: conda WSL2-Installation ODER ticklib-alternative (hawkeslib)
#    → Immer hawkeslib als Windows-kompatiblen Fallback implementieren
#
# 2. asyncio unter Windows: ProactorEventLoop (Python 3.11+) — explizit setzen
#    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
#
# 3. PyTorch + CUDA: conda install pytorch torchvision torchaudio
#    pytorch-cuda=12.1 -c pytorch -c nvidia
#
# 4. Paths: immer pathlib.Path(), niemals hardcodierte Slashes
#
# 5. .env-Datei für Bybit API-Keys (python-dotenv)
```

---

## GIT-WORKFLOW

```bash
# Nach jedem Schritt:
git add src/ tests/ scripts/ docker/ pyproject.toml
git commit -m "[Phase {n}] {Modulname}: {was wurde gemacht}"
git push origin main

# Tags für Meilensteine:
git tag -a v0.1.0 -m "Phase 0: Infrastructure"
git tag -a v0.2.0 -m "Phase 1: Quick Wins + Strategie 3 live-paper"
git push --tags
```

---

## STARTREIHENFOLGE

**Lies jetzt `agents/01_analyst.md` und starte die Analyse.**
Berichte nach jedem abgeschlossenen Schritt:
`[IMPL] MODULE: {name} | STATUS: {DONE/FAIL} | TESTS: {n/n} | COMMIT: {hash}`
