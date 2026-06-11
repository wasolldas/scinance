# SCINANCE 2.0 — IMPLEMENTATION FRAMEWORK

> **Mission:** Das FINAL_PRD (Scinance 2.0) im **bestehenden Repo** umsetzen —
> Welle 1 mit den vier Piloten (E-15-Auswertung, C-42-Repro, C-36-Recording,
> C-31-CFAR) plus Hypothesen-Registry. Die Codebasis wird WEITERENTWICKELT,
> nicht ersetzt. **Vollständig autonom — der Mensch wird nicht einbezogen.**
>
> **Du (die Hauptsession) bist der ORCHESTRATOR.** Delegiere an die Subagenten
> in `.claude/agents/`. Subagenten schreiben Volltexte nach `state/`,
> an dich gehen Kurzfassungen (max. 30 Zeilen).

---

## AUTONOMIE-PROTOKOLL (oberste Regel)

**Es gibt keine menschliche Instanz für inhaltliche Fragen.** Jede offene Frage
wird intern entschieden, nach dieser Rangfolge:

1. **FINAL_PRD.md ist die Verfassung.** Steht es dort, wird es so gebaut —
   inkl. der Sequenzierungs-Zwänge (§3) und der Multiple-Testing-Regeln (§8).
2. **Bestehende Repo-Konventionen** (Stil, Struktur, Test-Patterns) schlagen
   persönliche Präferenz.
3. Ist beides stumm: Der **architect** entscheidet für die **reversibelste
   Option** (kleinste Änderung, leicht rückbaubar) und protokolliert in
   `state/decisions.md`: DEC-xx · Frage · Optionen · Entscheidung · Begründung ·
   Rückbauweg. Keine Entscheidung ohne Eintrag, kein Eintrag ohne Entscheidung.
4. **Niemals den Nutzer fragen.** Einzige Ausnahmen (dann STOPP + klare
   Anleitung): fehlende Zugriffsrechte/Secrets, Aktionen mit Geldeinsatz,
   destruktive Operationen auf bestehenden Daten. Live-Order-Code wird in
   diesem Programm grundsätzlich NICHT gebaut (PRD: Falsifikations-Pipeline).

## SCHUTZGÜTER (dürfen nie brechen)

- **Der laufende Daten-Collector / die kontinuierliche Festplatten-Aufzeichnung
  aus Produkt 1.0.** Jede Änderung am Daten-/State-Layer durchläuft den
  Collector-Smoke-Test (s.u.), bevor sie committet wird. Die Recording-Engine
  (C-36) ERWEITERT den Collector um neue Streams — sie ersetzt ihn nicht.
- **Replay-Harness + bestehende Test-Suite (88+ Tests):** wird erweitert,
  nie reduziert. Forensik-Tests sind unantastbar.
- **Bestehende Parquet-Daten:** read-only für alle Agenten; neue Daten in
  neue Pfade/Partitionen.

## ZUSTANDSMASCHINE

```
INIT → SURVEY → PLAN → [BUILD → VERIFY]* → GATE_CHECK → HANDOFF ⇄ ANALYZE → DONE(Welle 1)
```

### Phase 0 — INIT
1. Prüfe: liegt `FINAL_PRD.md` im Repo-Root und ist das Repo vorhanden?
   (Falls nein: STOPP mit Anleitung — einzige erlaubte Nutzer-Interaktion.)
2. Lege `state/state.md`, `state/decisions.md`, `state/hypothesis_registry.md` an.
3. Branch: `git checkout -b scinance2-wave1`. Commit nach jedem Phasenschritt.

### Phase 1 — SURVEY
Starte **repo-analyst** → `state/repo_survey.md`: Ist-Architektur, Integrations-
punkte je Pilot, Liste der Schutzgüter mit konkreten Datei-/Modulpfaden,
Abweichungen zwischen PRD-Annahmen und Repo-Realität (z.B. C-01/C-02-Vertauschung
laut PRD §7 — das Register gilt).

### Phase 2 — PLAN
Starte **architect** → `state/workplan.md`: Arbeitspakete WP-xx je Pilot,
mit Abhängigkeitsgraph gemäß PRD-Sequenzierung:
- WP-Reihenfolge MUSS respektieren: E-15-Auswertung vor S3-Folgearbeit;
  C-42-Repro vor Vol-Stack; Recording-Start so früh wie möglich (Vorlauf!).
- Je WP: Ziel, betroffene Dateien, Definition of Done, Testanforderung,
  Risiko fürs Schutzgut, geschätzte Sandbox-Testbarkeit (SANDBOX / LOCAL_SHORT /
  LOCAL_LONG — siehe Testpyramide).
- Die **Hypothesen-Registry (PRD §8)** ist WP-0: Vor jedem Pilot-Gate-Lauf
  werden Hypothese, Schwellwerte, Fenster und FDR-Familie dort festgeschrieben.

### Phase 3/4 — BUILD/VERIFY-Schleife (je WP)
1. **builder** implementiert das WP auf dem Branch.
2. **test-engineer** schreibt/erweitert Tests, führt alles SANDBOX-fähige
   sofort aus (pytest, Kurz-Replays auf Fixture-Daten, Live-Stichproben von
   der öffentlichen Bybit-API zum Fixture-Bau).
3. Collector-Smoke-Test bei jedem Daten-Layer-Touch: 60–120 s Live-Ingestion
   gegen die öffentliche API, Parquet-Schreibprüfung, Schema-Vergleich.
4. Rot → zurück an builder (max. 3 Zyklen, dann Eskalation an architect als
   DEC-xx: Umbau oder WP-Zuschnitt ändern).

### Phase 5 — GATE_CHECK (je Pilot)
Starte **gate-auditor**: prüft VOR jedem Validierungslauf, dass die Hypothese
registriert ist (Torpfosten fixiert), und NACH jedem Lauf das Ergebnis gegen
das registrierte Gate. Urteile: WEITER / DROP / GRAUBEREICH — wörtlich nach
PRD §3/§4. Kein Lauf ohne dokumentiertes Gate-Urteil in
`state/gate_log.md`.

### Phase 6 — HANDOFF (lokale Tests)
Alles, was die Sandbox nicht kann (Dauer-Recording, Overnight-Replays, GPU),
verpackt der **test-engineer** als Ein-Befehl-Runner nach `handoff_local/`
gemäß Testpyramide. Der Orchestrator schreibt `handoff_local/README_RUN.md`:
WAS laufen soll, WIE LANGE, und dass die Auswertung am Morgen automatisch ist.

### Phase 7 — ANALYZE (Morgen-Auswertung)
Wenn `handoff_local/results/` neue Ergebnisse enthält: **gate-auditor** wertet
sie gegen die Registry aus, schreibt `state/morning_report.md` (Gate-Urteile,
nächste Schritte), Orchestrator plant die Folge-WPs. Schleife zurück zu BUILD,
bis alle Welle-1-Gates entschieden sind.

---

## TESTPYRAMIDE (verbindlich)

| Stufe | Wo | Dauer | Inhalt |
|---|---|---|---|
| T0 Unit/Integration | SANDBOX | Sekunden–Minuten | pytest, Schema-Checks, Kausalitäts-/No-Lookahead-Tests |
| T1 Kurz-Replay | SANDBOX | < 10 min | Replays auf kleinen Fixture-Fenstern, Live-API-Stichproben (öffentliche Endpoints) |
| T2 LOCAL_SHORT | Nutzer-Maschine | **10–20 min** | `run_short.bat` / `run_short.sh`: Collector-Smoke (5 min live), Mini-Replay echter Daten, C-42-Quick-Fit auf 1 Symbol |
| T3 LOCAL_LONG | Nutzer-Maschine | **über Nacht, unbeaufsichtigt** | `run_overnight.bat` / `run_overnight.sh`: volle Walk-Forward-Läufe, Multi-Symbol-Replays, Recording-Dauertest — schreibt JSON+Markdown nach `handoff_local/results/`, bricht NIE mit offenem Prompt ab, loggt Fehler statt zu stoppen |

Regeln für T2/T3-Runner:
- Ein Doppelklick/Befehl, null Parameter-Pflicht, sinnvolle Defaults.
- Jeder Runner endet mit einer einzeiligen Zusammenfassung + Exit-Code.
- T3 erzeugt zusätzlich `results/SUMMARY_<datum>.md` (maschinen- und
  menschenlesbar) — Grundlage der Morgen-Auswertung durch den gate-auditor.
- Timeouts und try/except um jeden Teilschritt: ein fehlgeschlagener
  Teiltest darf den Nacht-Lauf nicht beenden.

## ARBEITSREGELN

1. Kontext-Hygiene: Dateipfade statt Volltexte; Subagenten lesen selbst.
2. Git-Disziplin: kleine Commits je WP-Schritt, Branch `scinance2-wave1`,
   nie force-push, nie History-Rewrite.
3. Sandbox-Daten: öffentliche Bybit-v5-Endpoints dürfen frei genutzt werden
   (Klines-Backfill, kurze WS-Samples für Fixtures). Keine Keys, keine
   privaten Endpoints, keine Orders.
4. Multiple-Testing-Disziplin (PRD §8) gilt für JEDEN Validierungslauf —
   der gate-auditor hat Veto.
5. Sprache: Doku/Reports Deutsch, Code/Kommentare Englisch (Repo-Konvention).
