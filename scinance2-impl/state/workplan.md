# Workplan — Scinance 2.0 Welle 1

**Erstellt von:** architect · **Datum:** 2026-06-11 · **Branch:** `scinance2-wave1` · **Phase:** 2 (PLAN)
**Bindend:** FINAL_PRD.md (§3 Sequenzierung, §8 Multiple-Testing), CLAUDE.md (Zustandsmaschine, Testpyramide, Schutzgüter), repo_survey.md (Ist-Zustand, Sandbox-Grenzen), decisions.md (DEC-01..06).

Alle Pfade absolut ab `/home/user/scinance/`. Code/Kommentare Englisch, Doku Deutsch (Repo-Konvention).

---

## 0. Sandbox-Realität (gilt für jedes WP)

Die Sandbox ist eine reine **Code-Sandbox**: keine Bybit-API (Host-Allowlist blockt `api.bybit.com`), keine echten Tick-/Kline-Daten (`data/parquet/` leer, keine DuckDB), kein laufender Collector. Konsequenz für die Testpyramide:

- **T0/T1 (SANDBOX):** pytest, No-Lookahead-/Kausalitäts-Checks, Kurz-Replays auf **synthetischen** Fixtures, Schema-Checks. Vollständig hier ausführbar.
- **T2 (LOCAL_SHORT, 10–20 min):** Collector-Smoke (5 min live inkl. neuer Streams), Mini-Replay echter DuckDB-Daten, C-42-Quick-Fit 1 Symbol, E-15-Auswertung auf echten iter-Ergebnissen. → Runner-Deliverable nach `handoff_local/`.
- **T3 (LOCAL_LONG, über Nacht):** volle purged-Walk-Forward, Multi-Symbol-Replays, C-31-Surrogate über ≥2 disjunkte Fenster, Recording-Dauertest, iter-3/4-Roh-PnL-Export. → Runner-Deliverable nach `handoff_local/`.

**Sandbox-Testbarkeit-Feld je WP:**
- `SANDBOX` = WP voll in der Sandbox baubar+testbar (nur T0/T1).
- `LOCAL_SHORT` = baubar in Sandbox, Ausführung auf echten Daten = T2 (Runner).
- `LOCAL_LONG` = baubar in Sandbox, validierender Lauf = T3 (Runner).

Jedes T2/T3-Deliverable wird als Ein-Befehl-Runner nach `handoff_local/` geplant (Sammelpaket = WP-5).

---

## 1. Abhängigkeitsgraph

```
WP-0 (Registry)  ─┬─→ WP-1 (E-15-Auswertung)  ──→ [Gate H-01]  ──→ S3-Folgearbeit (Welle 2: C-37/C-08/CS-12)
                  ├─→ WP-3 (C-31 CFAR)         ──→ [Gate H-03]
                  └─→ WP-4 (C-42-Repro)        ──→ [Gate H-02]  ──→ Vol-Stack (Welle 2: C-10/C-35/C-11/C-12/C-34)

WP-2 (C-36 Recording)  ── unabhängig, START SO FRÜH WIE MÖGLICH (Vorlauf zählt ab User-Aufnahme) ──→ [Gate F0-Recall, Welle 2 Cascade/Options]

WP-5 (Handoff-Paket) ── sammelt die T2/T3-Runner aus WP-1..WP-4 ein; wächst inkrementell mit, finalisiert zuletzt.
```

**Harte PRD-Zwänge (§3), eingehalten:**
- E-15-Auswertung (WP-1) vor jeder S3-Folgearbeit → WP-1 liefert Gate H-01, das C-37/C-08/CS-12 freischaltet.
- C-42-Repro (WP-4) vor Vol-Stack-Derivaten → WP-4-Gate H-02 ist Anker für C-10/C-35/C-11/C-12/C-34.
- Recording-Start (WP-2) so früh wie möglich → WP-2 ist im Build früh, der **Recording-Start beim User** (T3-Runner) wird im allerersten Handoff mitgeschickt, damit der Vorlauf maximal früh beginnt.

**Registry-Gate (WP-0) ist Vorbedingung:** H-02 (C-42) muss registriert sein VOR dem C-42-Lauf; H-03 (C-31) VOR dem CFAR-Lauf. H-01 (E-15) ist bereits registriert.

---

## 2. Arbeitspakete

### WP-0 · Hypothesen-Registry vervollständigen (Querschnitt)

- **Ziel:** H-02 (C-42-Repro) und H-03 (C-31-CFAR) in `state/hypothesis_registry.md` registrieren, mit Schwellwerten/Fenstern/FDR-Familie **wörtlich aus PRD §3** — VOR den jeweiligen Validierungsläufen (Pre-Registration, §8.3).
- **Betroffene Dateien:** `/home/user/scinance/scinance2-impl/state/hypothesis_registry.md` (nur Anhang, H-01 unberührt).
- **Definition of Done:**
  - **H-02 · C-42-Repro** registriert mit: Hypothese (LightGBM/HAR-RV-Vol-Regression reproduzierbar OOS); Gate **OOS-R² ≥ 0.15 UND QLIKE schlägt naive HAR-RV-Baseline**; Abbruch **OOS-R² < 0.15 in EINEM Fenster ODER HAR-RV nicht geschlagen → PARK/DROP, Vol-Stack gesperrt**; Fenster **purged Walk-Forward (≥L2), ≥2 disjunkte OOS-Fenster**; FDR-Familie **Vol-Feature-Familie, BH α=0.10 über die 36 Features**; Ziel-Target `log(realised_vol_60m)`.
  - **H-03 · C-31-CFAR** registriert mit: Hypothese (zyklostationäres Spektrum der publicTrade-Inter-Arrivals trägt prädiktive Lead-Information); Gate **Surrogate p ≤ 0.05 in ≥2 Fenstern UND Lead-Zeit > 50 ms UND Edge > 11 bps**; Abbruch **p > 0.05 ODER Lead < 50 ms ODER Edge ≤ 11 bps in EINEM Fenster → DROP**; Fenster **≥2 disjunkte Fenster, Surrogate = geshuffelte Inter-Arrivals**; FDR-Familie **F-CFAR (standalone; falls Quantil-/Parametervarianten getestet → BH α=0.10 darüber)**.
  - Jeder Eintrag trägt „registriert VOR Lauf-Start" + Quelle (PRD §3 wörtlich).
- **Testanforderung:** T0 — ein Konsistenz-Test/Lint, dass jede registrierte Hypothese die Pflichtfelder (Gate, Abbruch, Fenster, FDR-Familie) enthält (optional, leichtgewichtig). Kein Code-Risiko.
- **Schutzgut-Berührung:** nein.
- **Risiko + Mitigation:** Risiko = Post-hoc-Schwellen-Drift. Mitigation = wörtliche PRD-Übernahme, gate-auditor-Veto, Werte hier eingefroren.
- **Umfang:** **S**.
- **Sandbox-Testbarkeit:** **SANDBOX**.

---

### WP-1 · P1 / E-15-Auswertungs-Tooling (CS-03 / C-22)

- **Ziel:** Skript, das den iter-5-Lauf maschinell gegen H-01-Gate auswertet: liest `replay_all_results.json` + trades-CSVs, fällt **WEITER / DROP / GRAUBEREICH** und prüft die E-17-Klärung via iter-3-vs-iter-5-Vergleich (Roh-PnL).
- **Betroffene Dateien:**
  - NEU `/home/user/scinance/scripts/evaluate_e15.py` (CLI, pfad-parametrisiert — DEC-02).
  - NEU `/home/user/scinance/src/bybit_edge/research/e15_eval/` (Auswertungs-Logik: Diagnostik-Counter-Extraktion, Netto-bps-Aggregation, E-17-Divergenz-Check) + `__init__.py`.
  - NEU `/home/user/scinance/tests/unit/test_evaluate_e15.py` + synthetische Fixtures unter `tests/unit/fixtures/e15/`.
  - Liest (read-only): `edge_research_framework/results/replay_all_results.json`, `trades_all.csv` / `trades_{symbol}_{mode}.csv` (Default-Pfade; überschreibbar via `--results-path`/`--trades-path`/`--input-dir`).
  - Referenz (read-only): `src/bybit_edge/strategies/strategy3_pre_settlement.py` (Diagnostik-Feldnamen: `time_stop_exceeded`, `hard_stop_loss`), `replay_all_results.json`-`reason_counts`-Schema.
- **Definition of Done:**
  - Skript liest Results+Trades, extrahiert `time_stop_exceeded`-Count, `n>120s`-Trades, `n<-30bps`-Trades, aggregierte Netto-bps (über 5 Symbole).
  - Fällt maschinelles Urteil exakt nach H-01: WEITER (Netto ≥ -5 UND E-17 geklärt), DROP (Netto ≤ -10), GRAUBEREICH (dazwischen).
  - **E-17-Check:** vergleicht iter-3- vs. iter-5-Roh-PnL-Export (zwei Result-Sätze) und meldet „aufgelöst/offen" (Voraussetzung für WEITER).
  - Output: maschinenlesbares `e15_verdict.json` + Markdown-Zeile, Exit-Code (0=ausgewertet, ≠0=Datendefekt/fehlend).
  - Läuft fehlerfrei gegen synthetische Fixtures (gebautes Result-Schema), die alle drei Urteils-Zweige abdecken.
- **Testanforderung:**
  - **T0/T1 (SANDBOX):** pytest gegen synthetische Fixtures — je ein Fixture für WEITER/DROP/GRAUBEREICH + E-17-aufgelöst/offen; Schema-Robustheit (fehlende Felder → sauberer Exit-Code, kein Crash).
  - **T2 (lokal):** Ausführung auf den **echten** iter-5-Ergebnissen + iter-3/iter-5-Roh-PnL-Export (Runner in WP-5).
- **Schutzgut-Berührung:** nein (rein lesend; keine Replay-/Collector-/Schema-Änderung). Kein Collector-Smoke nötig.
- **Risiko + Mitigation:** Risiko = Schema-Mismatch zwischen synthetischem Fixture und echtem `replay_all_results.json` → Fehlurteil. Mitigation = Fixture exakt aus dem realen Result-Schema (Survey §2.P1 Feldnamen) ableiten; T2 verifiziert gegen Echtdaten, bevor das Gate gilt; gate-auditor prüft das Verdict gegen Registry.
- **Umfang:** **M**.
- **Sandbox-Testbarkeit:** **LOCAL_SHORT** (baubar+T1 in Sandbox; verbindliches Urteil = T2 auf Echtdaten).

---

### WP-2 · P3 / C-36 Recording-Engine (gedeckelt) — FRÜHER START

- **Ziel:** Eigene Recording-Engine neben dem Collector (DEC-06), die die PRD-§3-Streams aufzeichnet, mit Storage-Deckel + Sunset-Logik wörtlich aus PRD §3, in eigene Tabellen/Parquet-Pfade (Schutzgut 3). Streamfähig erweiterbar (Welle-2-Andockpunkt).
- **Betroffene Dateien:**
  - NEU `/home/user/scinance/src/bybit_edge/recorder/recording_engine.py` (eigene Klasse; nutzt/parallelisiert `BybitWSCollector`, NICHT umbauen).
  - NEU `/home/user/scinance/src/bybit_edge/recorder/storage_cap.py` (Ringpuffer/Rotation, harter GB-Deckel) + `recorder/__init__.py`.
  - NEU `/home/user/scinance/src/bybit_edge/recorder/schema_f0.py` (DDL für neue Tabellen `rpi_orderbook`, `insurance_pool`, `adl_alerts`, `premium_index_kline`, `option_tickers` — getrennt vom Bestands-`db.py`-Schema).
  - NEU `/home/user/scinance/scripts/record_f0.py` (CLI-Start, Default-Deckel, Default-Streams).
  - Erweiterung (additiv, neue Methode): `src/bybit_edge/persistence/backfill.py`-Stil für Premium-Index-Kline (REST `premium-index-price-kline`) — als neue Datei `recorder/premium_index_backfill.py`, kein Edit am Bestand.
  - Neue Daten nach `/home/user/scinance/data/parquet/recording_f0/` (eigener Unterpfad).
  - NEU `/home/user/scinance/tests/unit/test_recording_engine.py`, `test_storage_cap.py`, `test_schema_f0.py`.
  - Referenz (read-only): `src/bybit_edge/collector/ws_collector.py` (`STREAMS`, `_dispatch`, `WSMessage`-Envelope), Options-WS-URL `wss://stream.bybit.com/v5/public/option`.
- **Definition of Done:**
  - Engine abonniert die neuen Streams: `orderbook.rpi` (100ms RPI-Orderbook), `insurance.USDT` (1s Insurance-Pool), `adlAlert` (1s), Premium-Index-Kline (REST), Options-Tickers (IV/Greeks, eigene WS-URL). Symbol-lose Topics (`insurance.USDT`, `adlAlert`) korrekt behandelt.
  - **Storage-Deckel** (harte GB-Obergrenze, ringpuffer-/rotationsbasiert, PRD §3 wörtlich): Engine respektiert fixe Obergrenze, rotiert/verwirft älteste Partitionen, überschreitet nie. Default-Wert konfigurierbar, dokumentiert.
  - **Sunset-Logik** (PRD §3/§9 wörtlich): je Stream Metadaten „Start-Datum + 3-Monats-Sunset-Marker"; Engine/CLI meldet beim Start fällige Sunset-Reviews. (Abschaltung manuell/per Config — kein Live-Order-/Geld-Code.)
  - Schreibt ausschließlich in neue Tabellen + `data/parquet/recording_f0/`; Bestands-Schema (`db.py`) und Collector unverändert (Diff zeigt 0 Edits an Schutzgut-Dateien).
  - F0-Recall-Regelwerk (deterministisches Perzentil-Regelwerk, Gate ≥ 95 %) als Skelett/Hook vorhanden; volle Recall-Messung = recording-abhängig (T3, später, Welle-2-nah) — in Welle 1 nur die Aufzeichnung + Deckel + Sunset müssen stehen.
- **Testanforderung:**
  - **T0 (SANDBOX):** pytest — Storage-Deckel-Logik (Rotation/Verwerfen, nie über Limit) mit Fake-Daten; Schema-DDL erzeugt neue Tabellen in `PersistenceLayer(":memory:")`; Sunset-Marker-Berechnung; Dispatch symbol-loser Topics. Mock-WS-Smoke (kein Netz).
  - **T2 (lokal):** **5-min-Smoke** gegen die öffentliche Bybit-API (neue Streams live, Parquet-Schreibprüfung, Deckel greift) — Runner in WP-5. **Plus** Bestands-Collector-Smoke (60–120 s) zum Nachweis, dass der laufende Collector unberührt weiterläuft.
  - **T3 (lokal):** **Recording-Dauertest** (über Nacht, Deckel-Rotation real, Schema-Stabilität, kein Abbruch) — Runner in WP-5; dies ist der **früheste Vorlauf-Start** für Welle-2.
- **Schutzgut-Berührung:** **ja** (Daten-/State-Layer-Nähe, aber strikt additiv). → **Collector-Smoke-Test Pflicht** vor jedem Commit, der den Recorder berührt (T2 lokal; in Sandbox: Mock-WS + Schema-Vergleich vor/nach). Bestehende Parquet-Daten read-only.
- **Risiko + Mitigation:** Risiko 1 = Recorder destabilisiert/verlangsamt den laufenden Collector (Schutzgut 1). Mitigation = eigene Engine/zweite WS-Verbindung, kein Edit an `ws_collector.py`, Collector-Smoke Pflicht. Risiko 2 = Data-Lake-Wildwuchs (PRD-Warnung). Mitigation = harter Storage-Deckel + Sunset-Marker ab Tag 1. Risiko 3 = neue Tabellen kollidieren mit Bestands-Schema. Mitigation = eigenes `schema_f0.py`, eigener Parquet-Unterpfad, Schema-Vergleich.
- **Umfang:** **L**.
- **Sandbox-Testbarkeit:** **LOCAL_LONG** (baubar+T0 in Sandbox; 5-min-Smoke = T2, Dauertest = T3).

---

### WP-3 · P4 / C-31 Cyclostationary CFAR (der EINZIGE neue Alpha-Test)

- **Ziel:** Standalone-CFAR-Analysemodul (research-Paket, DEC-03) + read-only Replay-Anbindung über die `trades`-Tabelle; wertet gegen H-03-Gate aus (Surrogate p ≤ 0.05 in ≥2 Fenstern, Lead > 50 ms, Edge > 11 bps).
- **Betroffene Dateien:**
  - NEU `/home/user/scinance/src/bybit_edge/research/c31_cfar/` mit:
    - `cyclic_spectrum.py` (Cyclic-Spectrum-Schätzer auf Inter-Arrival-Zeiten),
    - `cfar_detector.py` (CFAR-Peak-Detektor mit Falsch-Alarm-Kontrolle),
    - `surrogate_test.py` (geshuffelte Inter-Arrivals vs. gemessenes Spektrum, p-Wert),
    - `lead_edge.py` (Lead-Zeit- + Edge-Messung in bps),
    - `replay_driver.py` (eigener read-only Driver über DuckDB-`trades`-Tabelle, NICHT `replay_backtester` umbauen),
    - `__init__.py`.
  - NEU `/home/user/scinance/scripts/c31_cfar.py` (CLI, ≥2-Fenster-Lauf).
  - NEU `/home/user/scinance/tests/unit/test_c31_cfar_cyclic.py`, `test_c31_cfar_surrogate.py`, `test_c31_cfar_no_lookahead.py`.
  - Referenz (read-only): `src/bybit_edge/state/trade_buffer.py` (`recent_timestamps(n)`), `layers/base.py` (Interface-Stil), DuckDB-`trades`-Schema.
- **Definition of Done:**
  - Inter-Arrival-Berechnung aus Trade-Timestamps (live: `TradeBuffer`; historisch: `trades`-Tabelle).
  - Cyclic-Spectrum-Schätzer + CFAR-Detektor liefern reproduzierbare Peaks; Surrogate-Test liefert p-Wert gegen geshuffeltes Inter-Arrival-Null.
  - Lead-Zeit (ms) und Edge (bps, friktions-ehrlich gegen die 11-bps-Wand) gemessen, je Fenster.
  - CLI fällt H-03-Urteil über ≥2 disjunkte Fenster (DROP bei Verfehlen in EINEM Fenster — hartes Ein-Fenster-Kriterium §8.5).
  - **No-Lookahead-Test grün** (Forensik-Disziplin): Spektrum/Detektor nutzen nie zukünftige Ticks.
  - Output: `c31_verdict.json` + Markdown, Exit-Code.
- **Testanforderung:**
  - **T0/T1 (SANDBOX):** pytest — Cyclic-Spectrum auf **synthetischem** zyklostationärem Signal (bekannter Peak → muss detektiert werden); Surrogate-Null auf reinem Poisson-Inter-Arrival (p sollte ~uniform, kein falscher Peak); **No-Lookahead-Test**; CFAR-Falsch-Alarm-Rate auf Rausch-Fixture.
  - **T3 (lokal):** Surrogate-Lauf über echte Tick-Bestände, ≥2 disjunkte Fenster (Runner in WP-5).
- **Schutzgut-Berührung:** nein (eigener read-only Driver; `replay_backtester`/Pipeline unberührt — DEC-03).
- **Risiko + Mitigation:** Risiko 1 = Lookahead-Leak im Spektral-Schätzer → Scheinedge. Mitigation = expliziter No-Lookahead-Test (Forensik-Tafelsilber-Muster). Risiko 2 = Multiple-Testing über Fenster/Parameter. Mitigation = H-03 ist konfirmatorisch, Parametervarianten gehen FDR-korrigiert in F-CFAR (WP-0). Risiko 3 = abgegraste HFT-Anomalie (PRD-Hauptrisiko). Mitigation = hartes Edge>11bps-/Lead>50ms-Gate, schnell DROP-bar.
- **Umfang:** **L**.
- **Sandbox-Testbarkeit:** **LOCAL_LONG** (baubar+T0/T1 voll in Sandbox; verbindlicher Lauf auf Echt-Ticks = T3).

---

### WP-4 · P2 / C-42-Reproduktions-Pipeline (LightGBM/HAR-RV)

- **Ziel:** Reproduktion des einzigen positiven OOS-Befunds (Vol-Regression `log(realised_vol_60m)`, Test-R² 0.249) als Anker des Vol-Stacks: 36-Feature-Set, purged Walk-Forward (≥L2, ≥2 OOS-Fenster), FDR (BH α=0.10), QLIKE-Metrik. Auswertung gegen H-02-Gate.
- **Betroffene Dateien:**
  - NEU `/home/user/scinance/src/bybit_edge/research/c42_rv/` mit:
    - `features.py` (36-Feature-Engineering aus Klines + Trade-Flow; `atr_60` u.a. lt. research_notes),
    - `har_baseline.py` (naive HAR-RV-Baseline für QLIKE-Vergleich),
    - `purged_wf.py` (purged-Walk-Forward-Splitter, ≥2 disjunkte OOS-Fenster, Purge/Embargo gegen Label-Leak),
    - `fdr.py` (Benjamini-Hochberg α=0.10 über die 36 Features),
    - `metrics.py` (QLIKE + OOS-R²),
    - `model.py` (LightGBM-Adapter, Estimator austauschbar — DEC-04),
    - `__init__.py`.
  - NEU `/home/user/scinance/scripts/c42_repro.py` (CLI: `--symbol` Quick-Fit / `--all-symbols` Voll-WF).
  - EDIT (additiv) `/home/user/scinance/pyproject.toml`: neuer Extra `[project.optional-dependencies].vol = ["lightgbm>=4.0", "scikit-learn>=1.4"]` (DEC-04).
  - NEU `/home/user/scinance/tests/unit/test_c42_features.py`, `test_c42_purged_wf.py`, `test_c42_no_lookahead.py`, `test_c42_metrics.py`.
  - Datenzugriff (read-only): `src/bybit_edge/persistence/db.py` `query_kline` / DuckDB-`kline_1min`; Backfill-Weg `scripts/backfill.py`. Referenz: `src/bybit_edge/training/dataset.py` (chronologischer Split — als Negativ-Referenz: KEIN Purging).
- **Definition of Done:**
  - 36 Features deterministisch+kausal aus Klines/Trade-Flow erzeugt; Target `log(realised_vol_60m)`.
  - purged-WF-Splitter mit Purge+Embargo (kein Label-Leak über Fenstergrenzen), ≥2 disjunkte OOS-Fenster.
  - FDR (BH α=0.10) über die 36 Features angewandt und berichtet.
  - QLIKE-Metrik + OOS-R² je Fenster; HAR-RV-Baseline als Vergleich.
  - CLI fällt H-02-Urteil: WEITER (OOS-R² ≥ 0.15 UND QLIKE < HAR-RV in ALLEN Fenstern), DROP/PARK (R² < 0.15 in EINEM Fenster ODER HAR-RV nicht geschlagen → Vol-Stack gesperrt).
  - **No-Lookahead-Test grün** (Feature-Causality + Split-Causality).
  - Output: `c42_verdict.json` + `SUMMARY`-Zeile, Exit-Code.
- **Testanforderung:**
  - **T0/T1 (SANDBOX):** pytest — Feature-Causality (kein Future-Leak), purged-WF-Splitter (Purge/Embargo korrekt, Fenster disjunkt), QLIKE-Korrektheit auf bekanntem Beispiel, FDR-Korrektur auf konstruierten p-Werten. Mini-Fit auf **synthetischem** Kline-Fixture (sofern `vol`-Extra in Sandbox installierbar; sonst Adapter-Mock). LightGBM-Sandbox-Fit nur falls Paket installierbar.
  - **T2 (lokal):** **Quick-Fit auf 1 Symbol** (echte Klines, schneller WF) — Runner in WP-5.
  - **T3 (lokal):** **Voller purged Walk-Forward, multi-symbol**, ≥2 OOS-Fenster — Runner in WP-5.
- **Schutzgut-Berührung:** nein für Daten (read-only `kline_1min`); `pyproject.toml`-Edit ist additiv (neuer Extra, Bestands-Deps unberührt → Suite-Zählung 616 bleibt). Kein Collector-/Schema-Touch.
- **Risiko + Mitigation:** Risiko 1 = Label-Leak im WF → falsch-positives Gate (Vol-Stack baut auf Phantom). Mitigation = Purge/Embargo + No-Lookahead-Test verpflichtend; gate-auditor-Veto. Risiko 2 = LightGBM lokal nicht baubar. Mitigation = Estimator-Adapter (DEC-04, Notausgang HistGradientBoosting als DEC-04a). Risiko 3 = Reproduktion misst anderes Modell als Original → unvergleichbar. Mitigation = LightGBM beibehalten, Target/Feature-Set wörtlich aus research_notes.
- **Umfang:** **L**.
- **Sandbox-Testbarkeit:** **LOCAL_LONG** (baubar+T0/T1 in Sandbox; Quick-Fit = T2, Voll-WF = T3).

---

### WP-5 · Handoff-Paket (`handoff_local/`)

- **Ziel:** Alle T2/T3-Anteile der WP-1..WP-4 als Ein-Befehl-Runner gemäß Testpyramide-Regeln verpacken, plus Bedienungs-Doku. **Recording-Start (WP-2-T3) so früh wie möglich mitschicken** (Vorlauf!).
- **Betroffene Dateien:**
  - NEU `/home/user/scinance/handoff_local/README_RUN.md` (Deutsch: WAS läuft, WIE LANGE, dass Auswertung am Morgen automatisch ist).
  - NEU `/home/user/scinance/handoff_local/run_short.sh` + `run_short.bat` (T2, 10–20 min: Collector-Smoke 5 min, Recording-5-min-Smoke, C-42-Quick-Fit 1 Symbol, E-15-Auswertung auf Echtdaten falls vorhanden).
  - NEU `/home/user/scinance/handoff_local/run_overnight.sh` + `run_overnight.bat` (T3: C-42-Voll-WF multi-symbol, C-31-Surrogate ≥2 Fenster, Recording-Dauertest, iter-3/4-Roh-PnL-Export).
  - NEU `/home/user/scinance/handoff_local/results/` (Ausgabe-Verzeichnis; `.gitkeep`).
  - NEU `/home/user/scinance/tests/unit/test_handoff_runners.py` (Lint/Smoke: Skripte syntaktisch valide, Exit-Code-Konvention, kein interaktiver Prompt).
- **Definition of Done:**
  - **Ein Befehl, null Pflichtparameter, sinnvolle Defaults** (Testpyramide-Regel).
  - Jeder Runner endet mit **einzeiliger Zusammenfassung + Exit-Code**.
  - **`run_overnight`** erzeugt `results/SUMMARY_<datum>.md` (maschinen- + menschenlesbar) als Morgen-Auswertungs-Grundlage.
  - **try/except + Timeout um JEDEN Teilschritt** — ein fehlgeschlagener Teiltest beendet den Nacht-Lauf NIE, Fehler werden geloggt statt zu stoppen; kein offener Prompt.
  - `README_RUN.md` benennt explizit: Recording so früh wie möglich starten (Vorlauf für Welle-2), iter-5-Ergebnisse für E-15-Auswertung bereitstellen.
  - Schreibt nur nach `handoff_local/results/`; Ergebnisse fließen in Phase 7 (gate-auditor → `morning_report.md`).
- **Testanforderung:** T0 (SANDBOX) — Runner-Lint/Trockenlauf (Argument-Parsing, Exit-Code-Pfade, kein Hängen). Echter Lauf = T2/T3 auf User-Maschine (das ist der Zweck des Pakets).
- **Schutzgut-Berührung:** nein direkt (Runner orchestrieren; der WP-2-Smoke-Teil ruft den Collector-Smoke auf — dieser ist die Schutzgut-Prüfung). 
- **Risiko + Mitigation:** Risiko = Nacht-Lauf bricht mit offenem Prompt/Crash ab → verlorene Nacht. Mitigation = try/except+Timeout je Teilschritt, keine Interaktivität, Exit-Code-Disziplin, Lint-Test.
- **Umfang:** **M**.
- **Sandbox-Testbarkeit:** **SANDBOX** (baubar+T0-Lint in Sandbox; Ausführungszweck = T2/T3 beim User).

---

## 3. Empfohlene Build-Reihenfolge (BUILD/VERIFY-Schleife)

1. **WP-0** (Registry H-02/H-03) — S, blockiert die Läufe von WP-3/WP-4, schnell erledigt, fixiert Torpfosten.
2. **WP-2-Skelett zuerst anbauen, dann WP-2 fertigstellen** — Recording so früh wie möglich, damit der **Vorlauf beim User** im ersten Handoff (WP-5) startet. (Build früh; der eigentliche Vorlauf-Gewinn entsteht erst beim User-Start.)
3. **WP-1** (E-15-Auswertung) — liefert das erste echte Gate-Urteil (S3-Folgearbeit hängt daran); rein lesend, geringes Risiko.
4. **WP-4** (C-42-Repro) — Vol-Stack-Anker; größter Pipeline-Neubau, früh starten wegen L-Umfang.
5. **WP-3** (C-31-CFAR) — einziger neuer Alpha-Test; parallelisierbar zu WP-4 (unabhängige Pfade).
6. **WP-5** (Handoff) — wächst inkrementell mit WP-1/2/4 mit; **`run_overnight` mit Recording-Dauertest + E-15-Auswertung wird so früh wie möglich erstmals ausgeliefert**, danach um C-42/C-31 ergänzt.

**Welle-2-Andockpunkte (nicht bauen, nur schnittstellenfähig halten):** Recording-Engine streamfähig (C-39/C-40/C-33-IV), Registry familienfähig (Vol-Feature-/Funding-/Cascade-FDR-Familien), C-31-research-Paket erweiterbar (CS-07).

---

## 4. Schutzgut-Übersicht je WP

| WP | Schutzgut berührt | Collector-Smoke Pflicht | T-Stufe verbindliches Urteil |
|----|-------------------|--------------------------|------------------------------|
| WP-0 | nein | nein | T0 (SANDBOX) |
| WP-1 | nein (read-only) | nein | T2 |
| WP-2 | **ja** (additiv, Daten-Layer-Nähe) | **ja** | T2 (5-min-Smoke) + T3 (Dauertest) |
| WP-3 | nein (read-only Driver) | nein | T3 |
| WP-4 | nein (read-only Klines; pyproject additiv) | nein | T2 (Quick-Fit) + T3 (Voll-WF) |
| WP-5 | nein (orchestriert; ruft WP-2-Smoke) | indirekt (via WP-2) | T2/T3 beim User |

**Regel:** Test-Suite-Zählung (616) darf nie sinken; Forensik-Tests bleiben grün; neue Daten nur in neue Tabellen/Pfade.

---
*Ende workplan.md — geschrieben in Phase 2 (PLAN), nicht committet. DEC-02..06 in decisions.md ergänzt.*
