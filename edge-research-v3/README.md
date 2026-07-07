# edge-research-v3 — Cross-Domain Track

Dritte Generation des Edge-Research-Gerüsts (nach `edge-research-v2` → Scinance 2.0
FINAL_PRD → drei Wellen, siehe `reference/PROGRAM_FINAL_REPORT.md`). Fokus diesmal:
**ausschließlich Fachgebiete, die weder in v2's Horizon-Scout (Geophysik, Bioinformatik,
Neurowissenschaft, Quantenmechanik, Informationstheorie) noch in den drei Scinance-2.0-
Wellen bereits abgegrast wurden** (Details: `CLAUDE.md` §1).

Noch kein Code. Ergebnis ist ein Pre-Registration-Dokument
(`results/CROSSDOMAIN_PRD.md`), keine Implementierung.

## Setup (3 Schritte)

```bash
cd edge-research-v3
git init && git add -A && git commit -m "v3 cross-domain track init"
```

Optional, falls die Original-Repos lokal vorliegen: `reference/` enthält bereits
bereinigte Kopien von FINAL_PRD.md, PROGRAM_FINAL_REPORT.md, DATASET.md und EXPORT.md
(aus den GitHub-HTML-Exports extrahiert — die Original-Uploads waren gerenderte
GitHub-Seiten, keine rohen .md-Dateien; falls sich die Quellen inzwischen geändert haben,
einfach die aktuellen Versionen aus `scinance` bzw. `data-harvest` drüberkopieren).

Claude Code starten — `CLAUDE.md` wird automatisch gelesen:

```
claude
```

Dann:

```
Starte den Cross-Domain-Research-Run gemäß CLAUDE.md. Arbeite autonom bis Phase DONE.
```

## Ablauf

```
INIT → AUDIT (data-feasibility-scout)
     → DISCIPLINE-SCAN (6 Fachgebiets-Agenten ∥: erst eigene Methodenrecherche,
                         dann 2–4 IC-Vorschläge je Agent)
     → PRE-SCREEN (friction-tradability-auditor + data-feasibility-scout)
     → CRITIQUE (critic, ≤3 Rework-Runden)
     → DECONFLICT (Orchestrator + registry-keeper, Deckel 4–5 Kandidaten)
     → DEEP-VALIDATION (fable5-deep-validator, läuft auf Fable 5)
     → REGISTRY-WRITE (CROSSDOMAIN_PRD.md + CROSSDOMAIN_PARK.md)
     → REVIEW → DONE
```

Alle Zwischenergebnisse landen in `results/` und sind einzeln nachvollziehbar — der Lauf
lässt sich jederzeit unterbrechen und fortsetzen.

## Methodenoffenheit — der Werkzeugkasten je Agent ist ein Startpunkt, kein Deckel

Jede Agenten-Datei nennt bekannte Beispielmethoden (z. B. Marchenko-Pastur für RMT,
POT/GPD für EVT). Das ist bewusst keine abschließende Zuteilung: Schritt 1 im
„Vorgehen" jedes Fachgebiets-Agenten verpflichtet ihn, zuerst per WebSearch/WebFetch
mindestens 3–4 weitere Kandidatenmethoden aus seinem Feld zu recherchieren und mit
Begründung im Feld `Erwogene Alternativen:` zu dokumentieren (nachvollziehbar in
`results/discipline_scan/<agent>.md`), bevor er IC-Vorschläge formuliert. Findet ein
Agent dabei etwas, das erkennbar in ein anderes Fachgebiet fällt, geht das als
`Cross-Domain-Hinweis:` an den Orchestrator statt verloren zu gehen — `registry-keeper`
sammelt solche Hinweise während DECONFLICT für eine mögliche spätere Runde.

## Projektstruktur

```
edge-research-v3/
├── CLAUDE.md                          # Orchestrator-Instruktionen (Pflichtlektüre zuerst)
├── README.md                          # diese Datei
├── reference/                         # bereinigte Kopien der Quelldokumente
│   ├── FINAL_PRD.md
│   ├── PROGRAM_FINAL_REPORT.md
│   ├── DATASET.md
│   └── EXPORT.md
├── .claude/agents/
│   ├── econophysics-rmt.md
│   ├── evt-actuarial.md
│   ├── network-topology.md
│   ├── mechanism-design.md
│   ├── climatology-ensemble.md
│   ├── dendrochronology-crossdating.md
│   ├── data-feasibility-scout.md
│   ├── friction-tradability-auditor.md
│   ├── registry-keeper.md
│   ├── critic.md
│   └── fable5-deep-validator.md
└── results/                           # wird während des Laufs befüllt
```

## Modell- und Kostenpolitik

- Die sechs Fachgebiets-Agenten laufen standardmäßig auf **Sonnet** (breite parallele
  Exploration, günstig).
- `fable5-deep-validator` läuft auf **Fable 5** (`model: fable` im Frontmatter) — bewusst
  nur für die Handvoll Kandidaten, die DECONFLICT überleben, nicht für den gesamten
  Discipline-Scan. Das setzt die Vorgabe „sofern erfolgversprechend, Fable 5 nutzen" so
  kosteneffizient wie möglich um.
- Bekannter Vorbehalt: in manchen Claude-Code-Versionen wurde das `model:`-Feld im
  Subagent-Frontmatter als wirkungslos gemeldet (Subagent erbt dann das Modell der
  Hauptsession). Falls `fable5-deep-validator` erkennbar nicht auf Fable 5 läuft: das
  Modell explizit beim Agent-Aufruf mit angeben, statt sich nur auf das Frontmatter zu
  verlassen.
- Jede Hypothese wird zusätzlich mit `Rechenaufwand: CPU | GPU-vorteilhaft` getaggt
  (Zielsystem: Windows/WSL2, RTX 5060 Ti, CUDA 12.8+/PyTorch 2.7+) — Planungshilfe für
  die spätere Implementierungs-Welle, nicht für diese Recherche-Runde selbst.

## Was dieses Framework NICHT tut

- Kein Backtest, keine Live-Daten-Anbindung, keine Änderung an `data/`, `state/` oder
  bestehenden Skripten aus dem `scinance`- oder `data-harvest`-Repo.
- Keine Wiederholung von REFUTED/DROP-Verdikten oder bereits gescouteten Disziplinen
  (Seismologie/SOC, Informationstheorie/Entropie, Radartechnik/CFAR, Epidemiologie/SIR,
  TDA/RQA — siehe `CLAUDE.md` §1 für die vollständige Begründung je Cluster).
