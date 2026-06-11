# Scinance 2.0 — Wave 1 Implementation State

**Run gestartet:** 2026-06-11
**Branch:** `scinance2-wave1` (von `claude/subagent-prd-development-T16fE` @ `ce16453`)
**Verfassung:** `/home/user/scinance/FINAL_PRD.md` (approved, Review 6/6 PASS)

## Phase

`BUILD/VERIFY` (Phase 3/4 — Schleife läuft)

## Welle-1-Piloten (PRD §3)

| Pilot | Inhalt | Status |
|---|---|---|
| P1: E-15-Auswertung | iter-5-Validierungslauf (CS-03/S3) gegen vorregistrierte Tore | WARTET auf User-Run-Ergebnis → HANDOFF/ANALYZE-Pfad |
| P2: C-42-Repro | LightGBM-Vol-Modell purged-WF, FDR über 36 Features | Build nötig |
| P3: C-36-Recording | Recording-Engine, gedeckelt, Sunset-Review; ERWEITERT Collector | Build nötig, früher Start (Vorlauf!) |
| P4: C-31-CFAR | CFAR-Falsifikations-Gate, billig, basis-unabhängig | Build nötig |
| WP-0: Hypothesen-Registry | Pflicht vor jedem Gate-Lauf (PRD §8) | Angelegt (leer), Befüllung in PLAN |

## Schutzgüter (CLAUDE.md)

1. Laufender Daten-Collector / Festplatten-Aufzeichnung 1.0 — Smoke-Test vor jedem Daten-Layer-Commit
2. Replay-Harness + Test-Suite (616 Tests @ HEAD) — erweitern, nie reduzieren
3. Bestehende Parquet-Daten — read-only; neue Daten in neue Pfade

## Phasen-Log

- [x] Phase 0 INIT — Framework installiert, FINAL_PRD.md im Root, Branch `scinance2-wave1`, State-Dateien angelegt
- [x] Phase 1 SURVEY — 616 Tests grün (Baseline), alle 4 Pilot-Integrationspunkte kartiert; Sandbox OHNE Daten + OHNE Bybit-API → alle Live-Smokes nach T2/T3
- [x] Phase 2 PLAN — 6 WPs, DEC-02..06 gefällt; Reihenfolge WP-0 → WP-2 (Frühstart) → WP-1 → WP-4 ∥ WP-3 → WP-5
- [ ] Phase 3/4 BUILD/VERIFY — WP-0 ☐ · WP-1 ☐ · WP-2 ☐ · WP-3 ☐ · WP-4 ☐ · WP-5 ☐
- [ ] Phase 5 GATE_CHECK — je Pilot
- [ ] Phase 6 HANDOFF — handoff_local Runner (T2/T3)
- [ ] Phase 7 ANALYZE — Morgen-Auswertung, Schleife bis alle Welle-1-Gates entschieden
