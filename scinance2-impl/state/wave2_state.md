# Scinance 2.0 — Wave 2 Implementation State

**Run gestartet:** 2026-06-15
**Branch:** `scinance2-wave2` (von `scinance2-wave1` @ `e13bae6` — alle Welle-1-Gates entschieden)
**Verfassung:** `/home/user/scinance/FINAL_PRD.md` §4 (Welle 2+, 13 sequenzierte Pilots)
**Welle-1-Audit-Trail:** `scinance2-impl/state/{state.md, gate_log.md, decisions.md (DEC-01..09), hypothesis_registry.md (H-01..H-03), WAVE1_FINAL_REPORT.md}`

## Welle-1-Stand (übernommen, unveränderlich)

| Pilot | Urteil | GL |
|---|---|---|
| H-01 S3 Pre-Settlement | DROP | GL-004 |
| H-02 C-42 Vol-Stack-Anker | DROP | GL-001 |
| H-03 C-31 CFAR | DROP | GL-005 |
| C-36 Recording-Engine | Fundament steht (~5 Mio RPI/8h, 0 Evictions) | kein Alpha-Gate |

Alle drei DROP-Verdikte sind **endgültig und kaskaden-wirksam** (Vol-Stack gesperrt, S1-S5-Portfolio empirisch erledigt, CFAR-Anomalie auf Inter-Arrivals widerlegt). Keine Welle-2-Aktion darf eine dieser Hypothesen still reaktivieren (Registry-Disziplin §2 — keine Post-hoc-Schwellen-Anpassung; eine neue Hypothese H-0xb wäre dafür nötig).

## Phase

`PLAN` (Phase 2 — läuft; WP-0 Welle 2 H-04/H-05/H-06 in `hypothesis_registry.md` registriert 2026-06-15, VOR Lauf-Start; Pilot-Auswahl A umgesetzt: C-17/C-41 Lead-Lag, C-01 OFI-Vorzeichen-Test, C-07 Permutation Entropy)

## Welle-2-Pilot-Universum (aus FINAL_PRD §4 + WAVE1_FINAL_REPORT §6)

| Status | Anzahl | Pilots (Kurz-IDs) |
|---|---|---|
| Offen (sofort baubar) | 6 | C-07, C-01, C-06-MR, C-20, C-17/C-41-Mess-Gate, C-40 als Forschungsasset |
| Blockiert (durch H-02-Kaskade / Wave-1-DROPs) | 8 | C-10, C-11, C-12, C-34, C-35, VRP-RV-Bein, C-08-Ockham, C-37, CS-12, C-31-Bein von CS-07 |
| Sequentially gated (Recording-Vorlauf) | 6 | C-33 VRP, C-27, C-28, C-29, CS-06, C-39 |

(Auflösung folgt aus dem Wave-2-SURVEY — wir bauen nicht alle 6 offenen Pilots gleichzeitig; Sequenzierung kommt aus dem PLAN.)

## Schutzgüter (übernommen aus Welle 1, unverändert)

1. Laufender Daten-Collector / Festplatten-Aufzeichnung 1.0 — Smoke-Test vor jedem Daten-Layer-Commit
2. Replay-Harness + Test-Suite (Welle-1-Endstand: ~800 Tests grün) — erweitern, nie reduzieren
3. Bestehende Parquet-Daten + `data/parquet/recording_f0/` (Welle-1-Recording) — read-only; neue Daten in neue Pfade
4. **NEU**: Welle-1-Code (`recorder/`, `research/c31_cfar/`, `research/c42_rv/`, `research/e15_eval/`) — bleibt als Tooling/Audit-Trail; KEINE Reaktivierung der gefallenen Pilot-CLIs ohne neue Hypothese

## Phasen-Log

- [x] Phase 0 INIT — Branch + State-Datei
- [x] Phase 1 SURVEY — Wave-2-Survey vorhanden (`scinance2-impl/state/wave2_survey.md`, 2026-06-15)
- [~] Phase 2 PLAN — läuft (WP-0 H-04/H-05/H-06 registriert 2026-06-15; Pilot-Auswahl A umgesetzt: C-17/C-41, C-01-Vorzeichen, C-07-PE; effektives Welle-2-Alpha-Test-Budget = 3, alle kapitalfrei, F-LEADLAG/F-OFI/F-ENTROPY je BH-FDR α=0.10 + Welle-2-Über-Familie F-WAVE2 BH-FDR α=0.10)
- [~] Phase 3/4 BUILD/VERIFY — WP-1 (H-04 Lead-Lag) gebaut+verifiziert ✓; WP-2 (H-05 OFI) ☐ · WP-3 (H-06 PE) ☐
- [ ] Phase 5 GATE_CHECK — je Pilot
- [ ] Phase 6 HANDOFF — Runner-Update für Wave 2
- [ ] Phase 7 ANALYZE — Gate-Auswertung

## CHANGELOG (Welle 2)

- W2-INIT (2026-06-15): Branch `scinance2-wave2` von `scinance2-wave1` @ `e13bae6` abgezweigt. Welle-1-state-Dateien als Audit-Trail erhalten, separate `wave2_state.md` für Welle-2-Tracking. Welle-1-Endstand: 3 Alpha-DROPs, C-36 Fundament steht, ~5 Mio RPI-Zeilen aufgezeichnet.
- W2-WP0 (2026-06-15): WP-0 Welle 2 abgeschlossen — Pre-Registration der drei Welle-2-Pilots VOR Lauf-Start in `state/hypothesis_registry.md`: **H-04** (C-17/C-41 Cross-Sectional Lead-Lag, 2-Symbol-Mess-Gate BTC/ETH, kapitalfrei, Familie F-LEADLAG), **H-05** (C-01 OFI-Vorzeichen-Test, INC-02-Anker, kapitalfrei, Familie F-OFI), **H-06** (C-07 Permutation Entropy, m=4/τ=1 vorab fixiert, ρ≥0.3 PRE-Gate, kapitalfrei, Familie F-ENTROPY). Registry-Disziplin um Welle-2-FDR-Nachtrag erweitert: drei neue Familien + Welle-2-Über-Familie F-WAVE2 (zweistufige BH-FDR α=0.10). Alle Gates aus PRD §4 wörtlich übernommen wo konkret, sonst konservativ aus verdict.md/claims_register abgeleitet und als solche markiert. Keine Code-/Test-Änderungen. Lauf für keinen der drei Pilots gestartet — gate-auditor-Veto würde sonst greifen.
- W2-WP1 (2026-06-16): H-04 Lead-Lag gebaut — `src/bybit_edge/research/c17_c41_lead_lag/` (TE + Wavelet-Coherence + Circular-Shift-Surrogate, 1410 LoC) + `scripts/c17_c41_lead_lag.py`. DEC-10 (Achsen/Surrogate/Grid/WINDOW_MAX). Verify: 24 Tests, Suite 776→800 grün. Falsch-Positiv-Kontrolle (3 Seeds) + Detektions-Power (Lag-3 exakt, Lead=X) + Richtungs-Asymmetrie bestanden. 1 Modul-Bug gefixt (split_pair_windows doppelt-inklusive Grenzen → halb-offen). Kapitalfreiheit im Output bestätigt (capital_free:true, keine bps/Edge/PnL). Lauf NICHT gestartet (T2/T3 beim User).
