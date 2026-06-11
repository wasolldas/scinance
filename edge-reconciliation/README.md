# Edge Reconciliation Framework — Schnellstart

Autonomes Claude-Code-Agentensystem. Auftrag: vorhandene Forschungs-PRDs mit
aktuellen Analyseergebnissen abgleichen, strukturiert diskutieren, welche
Lösungsansätze auf Bybit (Spot / Futures / Optionen) anwendungswürdig sind —
und ein neues, konsolidiertes PRD als Grundlage für das verbesserte Framework
erzeugen.

## Architektur

```
ORCHESTRATOR (Hauptsession, liest CLAUDE.md)
 ├─ Phase 1  inventory-analyst   Claims-Register aus allen PRDs (C-xx) + Repo-Map
 ├─ Phase 2  evidence-auditor    Evidenz-Register aus Analyseergebnissen (E-xx)
 │                               mit Validierungsstufen L0–L3
 ├─ Phase 3  evidence-auditor    Alignment-Matrix: CONFIRMED / PARTIAL /
 │                               REFUTED / UNTESTED je Claim
 ├─ Phase 4  advocate ↔ skeptic  Strukturierte Debatte je Themen-Cluster,
 │                               getrennt je Markt (Spot/Futures/Optionen)
 ├─ Phase 5  judge               Entscheidungsmatrix: ADOPT / PILOT / PARK / DROP
 ├─ Phase 6  prd-architect       FINAL_PRD.md (rückführbar auf alle Urteile)
 └─ Phase 7  judge               Abschluss-Review
```

Kernprinzipien:
- **Evidenz schlägt Idee** — In-Sample-Zahlen machen keinen Claim CONFIRMED
- **Drei Märkte, drei Urteile** — jeder Ansatz wird je Markt separat bewertet
- **Echte Debatte** — der Skeptic antwortet Punkt für Punkt auf den Advocate
  (mit Steelman-Pflicht), kein Parallel-Monolog
- **Volle Rückführbarkeit** — jede PRD-Aussage verweist auf C-xx/E-xx-IDs

## Setup

```bash
# 1. Dieses Gerüst in dein bestehendes Git-Repo legen (oder eigenständig nutzen)
# 2. Alle Forschungs-PRDs und Analyseergebnisse nach input/ kopieren:
cp /pfad/zu/deinen/PRDs/*.md input/
cp /pfad/zu/analysen/*.ipynb input/        # Notebooks, CSVs, Reports — alles ok

# 3. Claude Code starten
claude --model claude-fable-5
```

Startbefehl in der Session:

```
Starte den Reconciliation-Run gemäß CLAUDE.md. Arbeite autonom bis Phase DONE.
```

## Hinweise

- Das bestehende Repo wird **nur gelesen, nicht verändert** — das FINAL_PRD
  beschreibt das Delta (bleibt / ändert sich / neu) als spätere Arbeitsgrundlage.
- Alle Zwischenstände landen in `results/` und werden je Phase committet;
  über `results/state.md` ist der Lauf jederzeit fortsetzbar.
- Modelle: evidence-auditor, advocate, skeptic, judge und prd-architect laufen
  auf Opus (Urteils- und Argumentationsqualität), inventory-analyst auf Sonnet.
  Bei knappem Budget: alles auf `sonnet` umstellen (Frontmatter `model:`).
