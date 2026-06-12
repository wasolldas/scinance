# Scinance 2.0 — Wave 1 Implementation State

**Run gestartet:** 2026-06-11
**Branch:** `scinance2-wave1` (von `claude/subagent-prd-development-T16fE` @ `ce16453`)
**Verfassung:** `/home/user/scinance/FINAL_PRD.md` (approved, Review 6/6 PASS)

## Phase

`HANDOFF` (Phase 6 — wartet auf lokale T2/T3-Läufe des Users)

## Welle-1-Piloten (PRD §3)

| Pilot | Inhalt | Status |
|---|---|---|
| P1: E-15-Auswertung | iter-5-Validierungslauf (CS-03/S3) gegen vorregistrierte Tore | WARTET auf User-Run-Ergebnis → HANDOFF/ANALYZE-Pfad |
| P2: C-42-Repro | LightGBM-Vol-Modell purged-WF, FDR über 36 Features | Build nötig |
| P3: C-36-Recording | Recording-Engine, gedeckelt, Sunset-Review; ERWEITERT Collector | Build nötig, früher Start (Vorlauf!) |
| P4: C-31-CFAR | CFAR-Falsifikations-Gate, billig, basis-unabhängig | Build nötig |
| WP-0: Hypothesen-Registry | Pflicht vor jedem Gate-Lauf (PRD §8) | H-01/H-02/H-03 registriert (WP-0 erledigt, 2026-06-11) |

## Schutzgüter (CLAUDE.md)

1. Laufender Daten-Collector / Festplatten-Aufzeichnung 1.0 — Smoke-Test vor jedem Daten-Layer-Commit
2. Replay-Harness + Test-Suite (616 Tests @ HEAD) — erweitern, nie reduzieren
3. Bestehende Parquet-Daten — read-only; neue Daten in neue Pfade

## Phasen-Log

- [x] Phase 0 INIT — Framework installiert, FINAL_PRD.md im Root, Branch `scinance2-wave1`, State-Dateien angelegt
- [x] Phase 1 SURVEY — 616 Tests grün (Baseline), alle 4 Pilot-Integrationspunkte kartiert; Sandbox OHNE Daten + OHNE Bybit-API → alle Live-Smokes nach T2/T3
- [x] Phase 2 PLAN — 6 WPs, DEC-02..06 gefällt; Reihenfolge WP-0 → WP-2 (Frühstart) → WP-1 → WP-4 ∥ WP-3 → WP-5
- [x] Phase 3/4 BUILD/VERIFY — alle 6 WPs gebaut+verifiziert; Suite 616 → 752 grün (+136), 0 Bugs in allen Verifies
- [x] Phase 6 HANDOFF — Runner ausgeliefert (run_short, run_overnight, README_RUN); wartet auf User-Ergebnisse in handoff_local/results/
- [ ] Phase 5 GATE_CHECK — je Pilot
- [ ] Phase 7 ANALYZE — Morgen-Auswertung, Schleife bis alle Welle-1-Gates entschieden

## CHANGELOG

- WP-0 (2026-06-11): H-02 (C-42-Repro) registriert — Gate OOS-R² ≥ 0.15 UND QLIKE schlägt naive HAR-RV (PRD §3 wörtlich); FDR F-VOL, BH α=0.10 über 36 Features; purged WF ≥L2, ≥2 OOS-Fenster.
- WP-0 (2026-06-11): H-03 (C-31-CFAR) registriert — Gate Surrogate p ≤ 0.05 in ≥2 Fenstern UND Lead > 50 ms UND Edge > 11 bps; hartes Ein-Fenster-DROP (§8.5); FDR F-CFAR.
- WP-0 (2026-06-11): Abschnitt „Registry-Disziplin" (PRD §8.2–8.5 + Gate-Auditor-Veto + GRAUBEREICH-Ein-Fenster-Wiederholung) in `hypothesis_registry.md` ergänzt; PRD-Lücken (Symbole, Friction-Wand-Herkunft) konservativ aus verdict.md abgeleitet und als Quelle markiert.
- WP-1 (2026-06-11): `scripts/evaluate_e15.py` + `src/bybit_edge/research/e15_eval/` (metrics/gate/e17/report) gebaut — pfad-parametrisiert (DEC-02), rein lesend, Output `e15_evaluation.json`/`.md` mit H-01-Referenz + Zeitstempel; Exit 0=ausgewertet, 1=Datendefekt.
- WP-1 (2026-06-11): H-01-Gate maschinell operationalisiert — DROP wenn Netto ≤ -10 bps; WEITER wenn Netto ≥ -5 bps UND e17_resolved==true; sonst GRAUBEREICH; Fix-Wirksamkeits-Tore („~60-70"→[54,77], „~0"→≤2) informativ in `gate_details`, nicht urteils-tragend.
- WP-1 (2026-06-11): Fixtures `tests/fixtures/e15/{weiter,drop,grau}/` (echtes iter-4-Schema) — Smoke: alle 3 Verdict-Pfade + Fehlpfad (Exit 1) grün; Lauf gegen echte iter-4-Daten reproduziert Report-Zahlen exakt (net -16.81 bps, raw -5.81, n>120s=68, n<-30bps=33, time_stop=1 → DROP-Pfad). pytest-Collection 661 unverändert; KEIN Bestands-File angefasst, nicht committet.
- DIAG (2026-06-12): Defekt 1 (C-31-Crash, 1.3-TiB-Bin-Grid durch ts≈0-Zeilen in der trades-Tabelle) gefixt — Epoch-ms-Plausibilitätsfilter im DuckDB-Loader + Spannen-Pre-Check (DataError) + MAX_BINS-Guard; 3 Regressionstests, 25/25 grün. Details: `state/diagnose_20260612.md`.
- DIAG (2026-06-12): Defekt 2 (C-42-Quick hängt am DuckDB-RW-Lock des Collectors) gefixt — Open-Timeout 30 s mit klarer Lock-Meldung + neues Flag `--db-copy` (Temp-Kopie lesen); Short-Runner geben `--db-copy` als Default mit; gegen echten gehaltenen Lock verifiziert, 33/33 grün.
- DIAG (2026-06-12): Defekt 3 (E-15-Trades-Pfad) per Runner-Pfad-Kaskade (results/ → trades_iter5/ → trades_*/, sonst SKIP) gefixt; Defekt 4 (Recorder NO_DATA): Option-WS-Keepalive (App-Ping statt Protokoll-Ping) gefixt + Subscribe-Ack-Logging instrumentiert — rpi/insurance brauchen T2-Retest; 22/22 grün. Nicht committet.
