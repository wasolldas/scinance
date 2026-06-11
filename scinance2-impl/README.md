# Scinance 2.0 — Implementation Framework · Schnellstart

Autonomes Claude-Code-Agentennetzwerk, das das FINAL_PRD (Scinance 2.0,
Welle 1) im **bestehenden Repo** umsetzt. Die Codebasis wird weiterentwickelt,
nicht ersetzt; die laufende Datenaufzeichnung ist oberstes Schutzgut.

## Architektur

```
ORCHESTRATOR (Hauptsession, liest CLAUDE.md)
 ├─ repo-analyst    Ist-Aufnahme, Integrationspunkte, Schutzgut-Liste
 ├─ architect       Arbeitsplan (WP-xx) + interne Entscheidungsinstanz
 │                  → state/decisions.md (DEC-xx, nie Rückfrage an Mensch)
 ├─ builder         setzt WPs um, additiv, Repo-Konventionen, kein Order-Code
 ├─ test-engineer   T0/T1 in der Sandbox (inkl. Live-Stichproben von der
 │                  öffentlichen Bybit-API), baut T2/T3-Runner
 └─ gate-auditor    Hypothesen-Registry (Pre-Registration, FDR), Gate-Urteile,
                    Morgen-Auswertung der Nacht-Läufe — mit Veto
```

## Autonomie

Offene Fragen werden intern entschieden (PRD → Repo-Konvention →
reversibelste Option) und in `state/decisions.md` protokolliert.
Der Mensch wird nur einbezogen bei: fehlenden Rechten/Secrets, Geldeinsatz,
destruktiven Operationen auf Bestandsdaten. Live-Order-Code wird nicht gebaut.

## Deine Rolle (bewusst minimal)

1. **Setup:** Gerüst-Inhalt ins Repo-Root kopieren (CLAUDE.md, .claude/,
   handoff_local/, state/), FINAL_PRD.md ebenfalls ins Root legen.
2. **Start:** `claude --model claude-fable-5` →
   „Starte die Umsetzung gemäß CLAUDE.md. Arbeite autonom."
3. **Lokale Tests, wenn das Netzwerk sie anfordert** (steht dann in
   `handoff_local/README_RUN.md`):
   - `run_short.bat` — 10–20 Minuten, Ergebnis sofort lesbar
   - `run_overnight.bat` — abends starten, läuft unbeaufsichtigt durch,
     schreibt `handoff_local/results/SUMMARY_<datum>.md`
4. **Morgens:** Claude-Code-Session öffnen → „Werte die Nacht-Ergebnisse aus."
   Der gate-auditor erstellt `state/morning_report.md` mit Urteilen und
   nächsten Schritten — du musst nichts interpretieren.

## Leitplanken (im Gerüst verankert)

- Branch `scinance2-wave1`, kleine Commits, nie History-Rewrite
- Bestehende Parquet-Daten read-only; Recording-Deckel rotiert nur eigene Streams
- S1/S2 → `retired` in Config (Wissensspeicher), kein Löschen
- Jeder Validierungslauf: erst Registry-Eintrag (Torpfosten fix), dann Lauf,
  dann Urteil — FDR-Familien nach PRD §8
- Sequenzierung bindend: E-15 zuerst, C-42 vor Vol-Stack, Recording früh
