# Scinance 2.0 — Wave 1 Implementation State

**Run gestartet:** 2026-06-11
**Branch:** `scinance2-wave1` (von `claude/subagent-prd-development-T16fE` @ `ce16453`)
**Verfassung:** `/home/user/scinance/FINAL_PRD.md` (approved, Review 6/6 PASS)

## Phase

`DONE (Wave 1)` — alle 4 Pilot-Gates entschieden, alle 3 Hypothesen DROP

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
- [x] Phase 5 GATE_CHECK — H-01/H-02/H-03 alle gegen Registry ge-AUDIT-tet
- [x] Phase 7 ANALYZE — Welle 1 DONE: H-01 DROP (GL-004), H-02 DROP (GL-001), H-03 DROP (GL-005); C-36 Fundament steht

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
- DIAG2 (2026-06-12): Recorder-Streams Root-Cause aus T2-Retest behoben — Bybit-Antwort `error:handler not found,topic:adlAlert` zeigte: gebündelte Subscribe-Request killte ALLE Sibling-Streams. Fix in `recording_engine.py`: (a) per-spec subscribe (`_subscribe_per_spec`, je StreamSpec eine eigene Request → Isolation), (b) `StreamSpec.phantom: bool`-Feld + `adl_alerts` als phantom markiert mit WARN-Skip (DEC-08, Schema/Normaliser/Writer als Audit-Trail erhalten). 2 neue Tests (`TestPerSpecSubscribeAndPhantom`) + bestehende Subscribe-Asserts auf per-spec/no-phantom umgestellt. Recorder-Suite: 24/24 grün (+2). Options-Subscribe-Form (`tickers.BTC`) per repo_survey §2.P3 als korrekt bestätigt — 0-Frames-Beobachtung braucht eigenen verlängerten T2-Retest (RECORDER_SMOKE 20 min statt 5 min). Nicht committet.
- ANALYZE (2026-06-13): H-01 (S3 iter-5) GEURTEILT → **DROP** (GL-004). iter-5-Replay (trades_iter5, 01:11Z): Netto-Edge -15.47 bps (≤ -10 DROP-Schwelle), RAW-Edge -4.48 bps. Fix wirkte mechanisch (time_stop 1→128, max Hold 2125s→178s, worst -57→-38 bps) aber Edge unverändert — Tail war nicht das Problem, Entry-Signal hat keine Edge (RAW negativ auf allen 5 Symbolen). Damit ist das gesamte Scinance-1.0-Portfolio (S1-S5) empirisch erledigt.
- ANALYZE (2026-06-13): C-36 Recorder per-spec-Fix (DEC-08) VERIFIZIERT auf Echtdaten — rpi_orderbook OK (29886 rows), insurance_pool OK (8 rows), premium_index OK; nur option_tickers NO_DATA (separates event-arm/Keepalive-Thema). 3/4 required Streams liefern jetzt (vorher 1/4). adl_alerts korrekt EMPTY (phantom).
- ANALYZE (2026-06-13): H-02 (C-42) DROP auf diesem Lauf erneut bestätigt (HAR fold-0 r2 +0.013 < 0.15, qlike schlägt HAR nicht). H-03 (CFAR) bleibt PENDING bis Overnight-Lauf mit dem 1.3-TiB-Fix.
- CFAR-TIMEOUT-FIX (2026-06-15, DEC-09): C-31 lief overnight 2026-06-14 auf allen 5 Symbolen in den 5400s-Timeout — `split_windows()` teilte die GESAMTE tage-/wochentiefe `trades`-Serie, also spannte jedes Fenster Tage → Millionen Bins × F-CFAR-Familie (3 Varianten) × 200 Surrogates ≈ 1206 SCD. Fix 1: deterministische Tick-Obergrenze `WINDOW_MAX_TICKS=150_000` (jüngste `windows × max_ticks` Ticks, in ≥2 disjunkte Fenster) + CLI `--max-ticks-per-window`; methodisch korrekter (Stationarität innerhalb Fenster) UND rechenbar.
- CFAR-TIMEOUT-FIX (2026-06-15): Fix 2 Progress-Logging je Fenster/Variante/Surrogate-Schub auf stderr (Hang jetzt diagnostizierbar) + Runner-Timeout 5400→1800s. Fix 4: `--max-ticks-per-window 150000` in run_cfar_only/run_overnight (.sh/.ps1). Gate-Schwellen p≤0.05/Lead>50ms/Edge>11bps, n_surrogates=200, BH-FDR α=0.10 EXAKT unverändert (Registry §8.3) — H-03-Nachtrag append-only ergänzt. c31-Suite 29→36 grün (Poisson-Null + Periodik-Detektion weiterhin korrekt). Nicht committet.
- ANALYZE (2026-06-15): H-03 (CFAR) GEURTEILT → **DROP** (GL-005). Standalone-Runner: BTC 712s OK, ETH 661s OK, SOL/BNB/XRP TIMEOUT. BTC+ETH liefern 4 unabhängig gemessene Fenster — auf ALLEN ist p ∈ [0.80, 1.00] (≫ 0.05) und Edge ∈ [0.01, 0.04] bps (~250× unter 11-bps-Wand). Hartes Ein-Fenster-DROP (PRD §8.5) bereits durch BTC F0 ausgelöst. Timeouts methodisch nicht entscheidungs-relevant (Gate je Symbol). **Welle 1 formal abgeschlossen: H-01/H-02/H-03 alle DROP, C-36 als Fundament tragfähig.**
