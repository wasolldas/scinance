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

`DONE (Welle 2)` — alle 3 Gates entschieden: H-04 WEITER (kapitalfrei/PARK), H-05 DROP, H-06 DROP

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
- [x] Phase 3/4 BUILD/VERIFY — WP-1 ✓ · WP-2 ✓ · WP-3 ✓ — alle 3 Welle-2-Pilots gebaut+verifiziert, Suite 776→872 grün (+96), 0 Modul-Bugs
- [x] Phase 5 GATE_CHECK — H-04/H-05/H-06 gegen Registry ge-AUDIT-tet (GL-006/007/008)
- [x] Phase 6 HANDOFF — run_wave2.{ps1,sh} + aggregate_wave2_fdr.py + README_WAVE2.md (T3, 2-4h, F-WAVE2 zweistufige BH-FDR)
- [x] Phase 7 ANALYZE — Welle 2 DONE: H-04 WEITER (Mess-Existenz, Kapital PARK, GL-006), H-05 DROP (GL-007, + ETH inverse → H-05b empfohlen), H-06 DROP (GL-008, PRE-Gate-Fail)

## CHANGELOG (Welle 2)

- W2-INIT (2026-06-15): Branch `scinance2-wave2` von `scinance2-wave1` @ `e13bae6` abgezweigt. Welle-1-state-Dateien als Audit-Trail erhalten, separate `wave2_state.md` für Welle-2-Tracking. Welle-1-Endstand: 3 Alpha-DROPs, C-36 Fundament steht, ~5 Mio RPI-Zeilen aufgezeichnet.
- W2-WP0 (2026-06-15): WP-0 Welle 2 abgeschlossen — Pre-Registration der drei Welle-2-Pilots VOR Lauf-Start in `state/hypothesis_registry.md`: **H-04** (C-17/C-41 Cross-Sectional Lead-Lag, 2-Symbol-Mess-Gate BTC/ETH, kapitalfrei, Familie F-LEADLAG), **H-05** (C-01 OFI-Vorzeichen-Test, INC-02-Anker, kapitalfrei, Familie F-OFI), **H-06** (C-07 Permutation Entropy, m=4/τ=1 vorab fixiert, ρ≥0.3 PRE-Gate, kapitalfrei, Familie F-ENTROPY). Registry-Disziplin um Welle-2-FDR-Nachtrag erweitert: drei neue Familien + Welle-2-Über-Familie F-WAVE2 (zweistufige BH-FDR α=0.10). Alle Gates aus PRD §4 wörtlich übernommen wo konkret, sonst konservativ aus verdict.md/claims_register abgeleitet und als solche markiert. Keine Code-/Test-Änderungen. Lauf für keinen der drei Pilots gestartet — gate-auditor-Veto würde sonst greifen.
- W2-WP1 (2026-06-16): H-04 Lead-Lag gebaut — `src/bybit_edge/research/c17_c41_lead_lag/` (TE + Wavelet-Coherence + Circular-Shift-Surrogate, 1410 LoC) + `scripts/c17_c41_lead_lag.py`. DEC-10 (Achsen/Surrogate/Grid/WINDOW_MAX). Verify: 24 Tests, Suite 776→800 grün. Falsch-Positiv-Kontrolle (3 Seeds) + Detektions-Power (Lag-3 exakt, Lead=X) + Richtungs-Asymmetrie bestanden. 1 Modul-Bug gefixt (split_pair_windows doppelt-inklusive Grenzen → halb-offen). Kapitalfreiheit im Output bestätigt (capital_free:true, keine bps/Edge/PnL). Lauf NICHT gestartet (T2/T3 beim User).
- W2-WP2 (2026-06-16): H-05 OFI-Vorzeichen gebaut — `src/bybit_edge/research/c01_ofi_sign/` (eigener Trade-Flow-OFI-Schätzer Σ signed_qty, Vorzeichen/|corr|/Hit-Rate + Permutations-Surrogat + BH-FDR über F-OFI, ~1118 LoC) + `scripts/c01_ofi_sign.py`. DEC-11 (eigener OFI statt verdächtigem m2_ofi.py Book-OFI). Verify: 33 Tests, Suite 800→833 grün, 0 Modul-Bugs. KRITISCH bestanden: Inverse-Falle (β<0 → inverse_significant=true, NICHT passed — S2-2023-Trennung bewiesen). Null-Kontrolle + Positiv-Aggression + No-Lookahead + halb-offene Fenster (kein WP-1-Bug). Kapitalfreiheit im Output bestätigt. m2_ofi.py unberührt. Lauf NICHT gestartet (T2/T3 beim User).

- W2-WP3 (2026-06-16): H-06 Permutation Entropy gebaut — research/c07_pe/ (Bandt-Pompe m=4/τ=1 fix, PRE-Gate Spearman-ρ PE-Drop↔Vol-Cluster, Haupt-Gate MI + Block-Shift-Surrogat + AUC-Lift in G1, ~1500 LoC) + scripts/c07_pe.py. WINDOW_MAX_BARS=43200 (30 Tage, Stationarität) als append-only H-06-Nachtrag + DEC-12. Verify: 39 Tests, Suite 833→872 grün, 0 Modul-Bugs. PE-Korrektheit + Null + Positiv (ρ≥0.36, p=0.0196, AUC-Lift≥0.057) + PRE-Gate-Blocker + Kausalität + halb-offene Fenster. Datenbasis kline_1min. Kapitalfrei. Lauf NICHT gestartet (T3 beim User).
- W2 BUILD-PHASE KOMPLETT (2026-06-16): Alle 3 kapitalfreien Mess-Gates H-04/H-05/H-06 gebaut+verifiziert. Suite 776→872 (+96), 0 Modul-Bugs. Nächster Schritt: WP-4 Handoff (Welle-2-Runner + zweistufige F-WAVE2-FDR).

- W2-WP4 (2026-06-16): Handoff-Paket gebaut — `scinance2-impl/handoff_local/run_wave2.{ps1,sh}` (220+199 LoC, sequenziell H-04→H-05→H-06→Aggregation, PS-5.1 BOM+ASCII+handle-cache+BelowNormal, --db-copy default, try/except je Schritt, dry-run via HANDOFF_DRY_RUN), `aggregate_wave2_fdr.py` (551 LoC, KRITISCH: zweistufige F-WAVE2-BH-FDR — Stage 1 aus Driver-Flag `family_fdr_significant` verbatim, Stage 2 BH-FDR α=0.10 über alle Stage-1-Survivor-p gemeinsam aus H-04∪H-05∪H-06; H-06-PRE-Gate + H-05 inverse_significant separat ausgewiesen, NICHT in F-WAVE2), `README_WAVE2.md` (85 LoC). Verify: 13 Tests, Suite 872→885 grün (Stage-1-Survivor verbatim, Stage-2-Kill-Pfad, Schema-Robustheit, Determinismus, Runner-Statik-Lint). Dry-Run-Mechanik bestätigt (HANDOFF_DRY_RUN OK, HANDOFF_DRY_RC=1 FAIL-Pfad). Lauf NICHT gestartet (T3 beim User).
- W2 HANDOFF-PHASE KOMPLETT (2026-06-16): Welle 2 bereit für lokalen Lauf. Drei kapitalfreie Mess-Gates + zweistufige F-WAVE2-FDR-Aggregation. Suite 776→885 (+109 Tests gesamt Welle 2), 0 Modul-Bugs. Nächster Schritt: User-Lauf, dann Phase 5 GATE_CHECK + Phase 7 ANALYZE durch gate-auditor.

- W2-H05b (2026-06-17): **Folge-Pre-Registration nach GL-007** — H-05b in `state/hypothesis_registry.md` registriert (append-only, nach H-06/DEC-12-Nachtrag, vor Registry-Disziplin-Abschnitt; H-01..H-06 + alle Nachträge UNVERÄNDERT). H-05b = inverse OFI-Vorzeichen-Lesart (MM-Replenishment / Fade), die im H-05-Gate explizit als „NEUE H-05b" antizipierte konkurrierende These; ausgelöst durch die FDR-sig inverse Entdeckungszelle ETHUSDT w0 δ1s (corr −0.0550, p=0.0050) des H-05-Laufs. **Data-Snooping-Guard ist Herzstück:** Entdeckungszelle NICHT konfirmatorisch + Konfirmation erfordert inverse-Vorzeichen-Konsistenz über ≥2 disjunkte Fenster (Entdeckungszelle ausgeschlossen) + Out-of-Sample-Anforderung (bevorzugt erweiterter `trades`-Bestand; bei demselben Bestand Entdeckungszellen-Ausschluss). Gate spiegelbildlich zu H-05: WEITER bei sign=− UND p≤0.05 nach BH-FDR über NEUE Familie **F-OFI-INV** UND ≥2-Fenster-Konsistenz UND |corr|≥0.05 ODER Hit-Rate≤0.47; DROP bei Vorzeichen≥0/Magnitude-Fehler/FDR-p>0.05/Konsistenz-nur-aus-Entdeckungszelle, hartes Ein-Fenster-Kriterium, kein Graubereich; **Symmetrie-Falle** explizit (weder konsistent positiv noch negativ → beide Lesarten verworfen, KEIN H-05c). KAPITALFREI (voller Edge-Test wäre H-05c, L2/Wochen). F-OFI-INV = eigene Familie; allein laufend nur Familien-interne BH-FDR α=0.10, F-WAVE2 abgeschlossen und NICHT erweitert; gemeinsam mit künftigen Pilots → neue Über-Familie separat registrieren. Code-Bedarf: bestehendes `research/c01_ofi_sign/` ausreichend (gate-neutrale Zell-Outputs + `inverse_significant`); optionale F-OFI-INV-FDR-Familie + Entdeckungszellen-Ausschluss-Flag als künftiges WP vermerkt, NICHT gebaut. KEIN Code, KEINE Tests, Lauf NICHT gestartet.
- W2-GATE (2026-06-17): Welle-2-T3-Lauf wave2_20260617_090618 ausgewertet (gate-auditor, GL-006/007/008). **H-04 WEITER** — erstes Nicht-DROP des Programms: gerichtete Info BTC→ETH FDR-sig in beiden Fenstern (WCOH p=0.0050), Lead=BTC stabil, beide F-WAVE2-Stufen überlebt. KAPITALFREI: Lags 1-3s = HFT, Kapital bleibt PARK, Tradability = NEUE H-04b. Lead-Stabilitäts-Frage nach Registry-Wortlaut (Lesart B) entschieden — bidirektionale Signifikanz ≠ Lead-Kippen; Lesart A verworfen als Torpfosten-Verschiebung (§2). **H-05 DROP** (C-01 + C-09-OFI-Bein + C-14-OFI-Erbe) — keine ≥2-Fenster-positive-Konsistenz; ETHUSDT signifikant INVERS (corr -0.0550, p=0.0050) → repliziert INC-02/S2-2023, H-05b empfohlen (NICHT registriert, WP-0). **H-06 DROP** — PRE-Gate ρ≥0.3 in ALLEN 10 Symbol×Fenster verfehlt (ρ∈[-0.006,+0.015]); XRP-Survivor AUC-Lift +0.0072 < +0.03. F-WAVE2 Stage 2 änderte nichts (0 Survivor verloren). Details: gate_log.md GL-006/007/008 + morning_report.md.
