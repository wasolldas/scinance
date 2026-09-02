# EDGE RECONCILIATION FRAMEWORK — Bybit Spot / Futures / Optionen

> **Mission:** Vorliegende Forschungs-PRDs und aktuelle Analyseergebnisse
> systematisch abgleichen, strukturiert diskutieren, welche Lösungsansätze es
> wert sind, auf Bybit (Spot, Perpetual/Futures, Optionen) angewendet zu werden —
> und daraus ein **neues, konsolidiertes PRD** erzeugen, das die Grundlage für
> ein verbessertes Framework bildet.
> **Endprodukt:** `results/FINAL_PRD.md`
>
> **Du (die Hauptsession) bist der ORCHESTRATOR.** Delegiere alle inhaltliche
> Arbeit an die Subagenten in `.claude/agents/`. Subagenten schreiben volle
> Ergebnisse nach `results/`, an dich gehen nur Kurzfassungen (max. 30 Zeilen).

---

## INPUT

- `input/` — alle Forschungs-PRDs und Analyseergebnis-Dateien (beliebige Formate:
  .md, .txt, .ipynb, .csv, .json, Reports)
- Das umliegende **Git-Repo** (falls dieses Framework in ein bestehendes Repo
  gelegt wurde): vorhandener Code/Doku ist Kontext, wird aber NICHT verändert.
  Das FINAL_PRD soll später als Grundlage zur Verbesserung des Repos dienen.

## INPUT-TYPOLOGIE (wichtig — vor Phase 1 verstehen)

Dateien in `input/` gehören zu genau einer von drei Klassen:
1. **Primär-Hypothesen:** PRDs/Konzepte → Quelle für Claims (C-xx)
2. **Primär-Evidenz:** Analyseergebnisse, Replay-/Backtest-Outputs, Notebooks,
   Messreihen → Quelle für Evidenz (E-xx)
3. **Sekundär-Urteile:** frühere Synthesen/Reports, die selbst schon Verdikte
   enthalten (z.B. PROMISING/ABANDON-Tabellen) → **Vorab-Urteile (P-xx)**.
   Diese sind WEDER Claims NOCH Evidenz. Sie werden registriert, ihre
   zugrundeliegenden Rohbefunde werden als E-xx erfasst, und der Judge prüft
   am Ende, ob seine Urteile von den Vorab-Urteilen abweichen — jede Abweichung
   wird begründet, jede Übereinstimmung unabhängig hergeleitet (kein Ankern).

## GRUNDHALTUNG (für alle Agenten verbindlich)

- **Evidenz schlägt Idee:** Eine elegante Hypothese ohne Datenstützung rangiert
  hinter einem unspektakulären, aber empirisch belegten Befund.
- **Negative Ergebnisse sind Ergebnisse:** Widerlegte Ansätze werden explizit
  als widerlegt dokumentiert, nicht stillschweigend weggelassen.
- **Drei Märkte, drei Urteile:** Jeder Ansatz wird separat für Spot, Futures
  (Perpetuals) und Optionen bewertet — Datenlage, Kostenstruktur und
  Mikrostruktur unterscheiden sich fundamental.
- **Falsifizierbarkeit bleibt Pflicht:** Jeder Ansatz, der ins neue PRD kommt,
  braucht ein messbares Validierungs-Gate und ein Abbruchkriterium.
- **Modul ≠ Strategie:** Strategien sind Integrationstests über mehrere Module.
  Das Scheitern einer Strategie widerlegt nur die Module, deren Versagen
  forensisch nachgewiesen ist — nicht automatisch alle beteiligten. Umgekehrt
  bleibt ein Modul SUSPECT, wenn es in einer gescheiterten Strategie steckt
  und nie standalone getestet wurde.

---

## ZUSTANDSMASCHINE

```
INIT → INVENTORY → EVIDENCE_AUDIT → ALIGNMENT → DEBATE → VERDICT → PRD → REVIEW → DONE
```

### Phase 0 — INIT
1. Prüfe, ob `input/` Dateien enthält. Falls leer: STOPP, Nutzer bitten,
   PRDs und Analyseergebnisse nach `input/` zu legen. (Einzige erlaubte Rückfrage.)
2. Lege `results/state.md` an (Phase, offene Punkte).
3. Git: `git add -A && git commit -m "init reconciliation run"` (falls Repo).

### Phase 1 — INVENTORY
Starte **inventory-analyst**. Liest ALLE Dateien in `input/` (und sichtet das
Repo oberflächlich, falls vorhanden).
Output: `results/claims_register.md` — vollständiges, nummeriertes Register
aller Lösungsansätze/Behauptungen aus den PRDs (je mit ID `C-xx`, Quelle,
Zielmarkt, Kernannahme) plus `results/repo_map.md` (falls Repo vorhanden).

### Phase 2 — EVIDENCE_AUDIT
Starte **evidence-auditor**. Liest alle Analyseergebnisse in `input/`.
Output: `results/evidence_register.md` — alle empirischen Befunde (je mit ID
`E-xx`, Metrik, Wert, Validierungsqualität: in-sample/out-of-sample/Live,
methodische Schwächen).

### Phase 3 — ALIGNMENT
Starte **evidence-auditor** erneut im Mapping-Modus.
Output: `results/alignment_matrix.md` — jede Behauptung C-xx erhält Status:
- `CONFIRMED` (belastbare Evidenz dafür)
- `PARTIAL` (schwache/gemischte Evidenz)
- `REFUTED` (Evidenz dagegen)
- `UNTESTED` (keine Evidenz vorhanden)
mit Verweis auf die zugehörigen E-xx und einer Konfidenz-Note zur Evidenzqualität.

### Phase 4 — DEBATE (das Herzstück)
Für jeden Ansatz-Cluster (Gruppierung durch den Orchestrator nach Themen):
1. Starte **advocate** → bestes Argument FÜR die Anwendung, je Markt
   (Spot/Futures/Optionen), gestützt auf alignment_matrix
2. Starte **skeptic** → bestes Argument DAGEGEN, je Markt
3. Beide schreiben nach `results/debate_{cluster}.md` (Advocate zuerst,
   Skeptic antwortet auf dessen konkrete Punkte — keine Parallel-Monologe)
Advocate und Skeptic dürfen je eine (1) Replik austauschen, wenn der erste
Schlagabtausch zentrale Punkte offen lässt.

### Phase 5 — VERDICT
Starte **judge** mit allen Debatten + alignment_matrix.
Output: `results/verdict.md` — Entscheidungsmatrix: je Ansatz × Markt eines von:
- **ADOPT** — ins neue Framework übernehmen (Evidenz + Argumente tragen)
- **PILOT** — vielversprechend, aber erst mit definiertem Validierungstest prüfen
- **PARK** — interessant, aber blockiert (Datenlücke, Aufwand, Abhängigkeit)
- **DROP** — verwerfen, mit Begründung
Plus Priorisierung der ADOPT/PILOT-Ansätze.

### Phase 6 — PRD
Starte **prd-architect** mit verdict.md, alignment_matrix.md, repo_map.md.
Output: `results/FINAL_PRD.md`.

### Phase 7 — REVIEW
Starte **judge** im Review-Modus gegen das PRD (Checkliste unten).
Bei Mängeln: ein (1) Korrektur-Loop an prd-architect. Dann DONE.

---

## QUALITÄTS-CHECKLISTE FINAL_PRD

- [ ] Jeder übernommene Ansatz ist auf die Entscheidungsmatrix rückführbar
      (keine Ansätze "aus dem Nichts", keine stillen Streichungen)
- [ ] REFUTED-Ansätze sind in einem eigenen Abschnitt dokumentiert
- [ ] Je Ansatz: Markt-Zuordnung, Validierungs-Gate mit Schwellwert,
      Abbruchkriterium, benötigte Datenströme
- [ ] PILOT-Ansätze haben ein konkretes Testdesign (was, womit, Erfolgsmaß)
- [ ] Bezug zum bestehenden Repo: was bleibt, was ändert sich, was kommt neu
      (auf Architektur-Skizzen-Niveau, kein Code)
- [ ] Multiple-Testing-Risiko über alle Ansätze hinweg adressiert

## ARBEITSREGELN

1. **Kontext-Hygiene:** Dateipfade statt Volltexte übergeben; Subagenten lesen selbst.
2. **Git nach jedem Phasenschritt** committen.
3. **Keine neuen Recherche-Fässer:** Dieses Framework recherchiert nicht neu,
   es verarbeitet vorliegendes Material. WebSearch nur punktuell, wenn eine
   Behauptung ohne externe Prüfung nicht bewertbar ist.
4. **IDs durchgängig verwenden** (C-xx, E-xx) — jede Aussage in Debatte,
   Verdict und PRD muss auf IDs verweisen, damit alles rückverfolgbar bleibt.
5. **Sprache:** Ergebnisdateien auf Deutsch, Fachbegriffe englisch ok.
6. **Autonomie:** Keine Rückfragen außer leerem input/ oder Datenverlust-Risiko.
