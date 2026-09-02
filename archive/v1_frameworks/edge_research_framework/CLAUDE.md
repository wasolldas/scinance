# EDGE RESEARCH FRAMEWORK — Bybit Retail Trader Edge
## Master Orchestration für Claude Code

> **Aufgabe:** Führe das vollständige autonome Forschungssystem zur Entdeckung eines statistischen Edges für Retail Trader auf Bybit Perpetual Futures aus. Das Ziel ist ein vollständiges, mathematisch fundiertes PRD (Product Requirements Document) mit priorisierten, implementierbaren Methoden.

---

## PFLICHTLEKTÜRE VOR BEGINN

Lies diese Dateien **in dieser Reihenfolge** bevor du irgendwelche Schritte ausführst:

1. `agents/01_orchestrator.md` — Zustandsmaschine und Qualitätsschwellen
2. `agents/02_scout.md` — Cross-Domain Horizon Scanner Briefing
3. `agents/03_quant_researcher.md` — Quant Researcher Briefing
4. `agents/04_critic.md` — Critic / Evaluator Briefing
5. `agents/05_synthesizer.md` — Synthesizer Briefing
6. `agents/06_prd_architect.md` — PRD Architect Briefing

---

## CONTEXT ENGINEERING RULES (für alle Agenten verbindlich)

Das "Lost in the Middle"-Problem: Bei langen Agenten-Outputs sinkt die Qualität, weil irrelevante Logs vergangene Muster überlagern. Daher gilt:

- **Jeder Agent komprimiert seinen Output** auf das Wesentliche, bevor er ihn übergibt
- **Kein Agent übergibt rohe Logs** — nur strukturierte, komprimierte Erkenntnisse
- **Format für Übergaben:** Immer `[AGENT_NAME → EMPFÄNGER] STATUS | INHALT`
- **Maximale Übergabelänge:** 2000 Tokens pro Agenten-Output (komprimiert, dicht)
- **Vergangene Iterations-Outputs** werden als Zusammenfassung in einem Block gespeichert, nicht inline wiederholt

---

## AUSFÜHRUNGSPROTOKOLL

### Schritt 0 — GitHub Setup
```bash
# Führe aus, falls noch nicht geschehen:
bash setup_github.sh
```

### Schritt 1 — Research Round 1 (Parallel)
Starte Scout und Quant Researcher simultan. Schreibe Outputs in:
- `results/round_1_scout.md`
- `results/round_1_quant.md`

```bash
git add results/ && git commit -m "Round 1: Scout + Quant Research complete" && git push
```

### Schritt 2 — Critic Evaluation
Übergib beide Round-1-Outputs an den Critic. Schreibe Output in:
- `results/critic_report_1.md`

```bash
git add results/ && git commit -m "Round 1: Critic evaluation complete" && git push
```

### Schritt 3 — Refinement (wenn Critic: CONDITIONAL oder REJECT)
Generiere gezielten Rework-Auftrag. Wiederhole max. 2× (Round 2, Round 3).
Speichere in `results/round_{n}_*.md` und `results/critic_report_{n}.md`.

```bash
git add results/ && git commit -m "Round {n}: Refinement complete" && git push
```

### Schritt 4 — Synthese (wenn Critic: PASS)
Starte Synthesizer mit allen validierten Methoden.
- `results/synthesis.md`

```bash
git add results/ && git commit -m "Synthesis complete" && git push
```

### Schritt 5 — PRD
Starte PRD Architect mit Synthesis-Output.
- `results/FINAL_PRD.md`

```bash
git add results/ && git commit -m "FINAL PRD complete" && git push
```

---

## QUALITÄTSSCHWELLEN (Orchestrator prüft vor jedem Schritt)

| Kriterium | Minimum |
|-----------|---------|
| Gesamt validierte Methoden | ≥ 12 |
| Cross-Domain Scout-Methoden | ≥ 5 |
| Methoden mit Novelty-Score ≥ 4 | ≥ 4 |
| Bybit-Endpoint CONFIRMED | ≥ 8 |
| Methoden mit konkreter Formel/Mathematik | ≥ 4 |
| PRD-Abschnitte vollständig | 9/9 |

---

## REFERENZ-PIPELINE (Zielarchitektur für PRD)

Die im PRD zu beschreibende Zielarchitektur folgt dieser Kaskade:

```
[Bybit WebSocket]
    tickers (100ms) + allLiquidation (500ms)
           │
    [SNN Ingestion Layer]
    Spiking Neural Network als event-driven Membran
    → feuert NUR bei Anomalien (OI-Sprung, Liquidations-Cluster)
           │
    [Wavelet Denoising]
    Diskrete Wavelet-Transformation (Symlets)
    → Trennt Market-Maker-Rauschen von Smart-Money-Bewegung
           │
    [Entropy Greenlight]
    Shannon-Entropie + KL-Divergenz des L2-Orderbuchs
    → Signal NUR wenn Entropie kollabiert (Markt verlässt Random Walk)
           │
    ┌──────┴───────────────┐
    │                      │
[TFSAX + DNABERT]    [Hawkes Matrix Engine]
Pattern Matching     Spektralradius ρ(Φ)
historischer         → kritischer Zustand
Sequenzen            → Kaskaden-Prognose
    │                      │
    └──────┬───────────────┘
           │
    [Quantum Risk Module]
    Schrödinger-Gleichung für Preiswahrscheinlichkeit
    Funding-Rate Clamp-Funktion als Potenzialbarriere
           │
    [EXECUTION DECISION]
```

---

## ERGEBNIS-STRUKTUR

```
edge_research_framework/
├── CLAUDE.md                     ← Diese Datei
├── README.md
├── setup_github.sh
├── agents/
│   ├── 01_orchestrator.md
│   ├── 02_scout.md
│   ├── 03_quant_researcher.md
│   ├── 04_critic.md
│   ├── 05_synthesizer.md
│   └── 06_prd_architect.md
└── results/
    ├── round_1_scout.md
    ├── round_1_quant.md
    ├── critic_report_1.md
    ├── [round_2_* wenn nötig]
    ├── synthesis.md
    └── FINAL_PRD.md              ← Das Zieldokument
```

---

## START

**Lies jetzt alle Agent-Dateien und beginne mit Schritt 0 (GitHub Setup), dann Schritt 1.**

Berichte nach jedem abgeschlossenen Schritt mit:
`[ORCHESTRATOR] STEP: {n} | STATUS: {status} | METHODS_VALIDATED: {n} | NEXT: {action}`
