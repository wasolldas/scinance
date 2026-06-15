# Wave-2-SURVEY — Scinance 2.0

**Erstellt von:** repo-analyst · **Datum:** 2026-06-15 · **Branch:** `scinance2-wave2` · **Phase:** 1 (SURVEY, Welle 2)
**Methode:** Read-only, Delta zur Welle-1-Survey (`scinance2-impl/state/repo_survey.md`, 2026-06-11). Alle Pfade absolut.

---

## 1. Was sich seit Welle-1-SURVEY geändert hat

### 1.1 Neue Code-Pakete (alle additiv, Schutzgüter unberührt)

| Paket | Pfad | Inhalt | Status für Welle 2 |
|---|---|---|---|
| **Recording-Engine** (DEC-06/07/08) | `/home/user/scinance/src/bybit_edge/recorder/` (`recording_engine.py`, `storage.py`, `sunset.py`) | Eigener WS-Recorder + Ringpuffer-Storage-Deckel (50 GB Default) + Sunset-Review (90 Tage). Per-spec Subscribe + `phantom`-Flag. | **Höchster Welle-2-Hebel.** Bleibt produktionsstabil, wird strukturell erweitert nur mit neuem DEC (z.B. options-WS-Fix, neue Streams). |
| **C-31 CFAR** | `/home/user/scinance/src/bybit_edge/research/c31_cfar/` (`cyclic_spectrum.py`, `cfar_detector.py`, `surrogate.py`, `driver.py`, `lead_edge.py`) | Cyclic-Spectrum-Schätzer, CFAR-Peak-Detektor, Surrogate-Test, Driver. `WINDOW_MAX_TICKS=150_000` Fenster-Cap (DEC-09). | **Erledigtes Pilot-Tooling.** H-03 DROP. KEINE Reaktivierung ohne neue H-03b-Hypothese. Bleibt als Audit-Trail + wiederverwendbarer Surrogate-/SCD-Baustein für CS-07-Footprint-Variante (falls je entsperrt). |
| **C-42 RV** | `/home/user/scinance/src/bybit_edge/research/c42_rv/` (`features.py`, `splits.py`, `models.py`, `metrics.py`, `pipeline.py`, `target.py`) | 36 Features, purged-WF-Splitter (Purge 60 + Embargo 1440), FDR/BH α=0.10, QLIKE, LightGBM-Adapter. | **Erledigtes Pilot-Tooling.** H-02 DROP. KEINE Reaktivierung ohne neue H-02b mit bit-genauer Original-Feature-Spec (Registry §2; GL-001 Reproduktions-Treue-Vorbehalt). Vol-Stack bleibt **gesperrt** (C-10, C-11, C-12, C-34, C-35, VRP-RV-Bein). |
| **E-15 Eval** | `/home/user/scinance/src/bybit_edge/research/e15_eval/` (`metrics.py`, `gate.py`, `e17.py`, `report.py`) | Aggregations- und Gate-Auswertung des iter-5-S3-Replays. | **Erledigtes Pilot-Tooling.** H-01 DROP. Code bleibt als Archiv; S3-Strategie deaktiviert (PRD §7); keine Erweiterung. |

CLI-Scripts: `scripts/c31_cfar.py`, `scripts/c42_repro.py`, `scripts/evaluate_e15.py` — bleiben unverändert. Werden in Welle 2 **NICHT erweitert** (Hypothesen sind gefallen).

### 1.2 Test-Suite-Stand (neue Baseline für Welle 2)

```
python -m pytest tests/unit/ --collect-only -q | tail -3
→ 776 tests collected in 111.59s
```

Welle-1-Endstand laut `WAVE1_FINAL_REPORT §5` war 752. Differenz +24 (vermutlich kleinere Patches/Stabilisierungen nach Welle-1-Abschluss; Suite ist im Wachstum, nicht Schrumpfen). **Welle-2-Floor: 776 grün — darf NICHT sinken.** Neue Test-Dateien aus Welle 1, die nicht angetastet werden:
- `/home/user/scinance/tests/unit/test_recorder_engine.py`, `test_recorder_storage.py`, `test_recorder_sunset.py`
- `/home/user/scinance/tests/unit/test_c31_cfar.py`, `test_c42_rv.py`, `test_e15_eval.py`
- Welle-1-Forensik-Tests (`test_replay_backtester_maker_only.py`, `test_strategy3_bounded_exits.py`, `test_strategy_direction_inversion.py`) — unverändert grün.
- Fixtures: `/home/user/scinance/tests/fixtures/{c42, e15/{weiter,drop,grau}}/` — read-only.

### 1.3 Neue Daten-Pfade

- **Sandbox:** `/home/user/scinance/data/parquet/` ist **leer** (`ls -la` → 0 Dateien, 8 KB metadata). `data/bybit_edge.duckdb` existiert nicht. `data/trades_journal.csv` (15 KB) ist die einzige Datendatei. **Konsequenz wie in Welle 1:** Sandbox ist code-only; Daten leben auf der User-Maschine.
- **User-Maschine** (laut `handoff_local/results/upload_20260615/.../recording_check.json`): `E:\Claude\Projects\scinance\data\parquet\recording_f0\` mit aktuell **3 378 rpi_orderbook-Files / 4 987 255 Rows, 27 insurance_pool-Files / 58 Rows, 478 premium_index_kline-Files / 95 600 Rows**; option_tickers NO_DATA, adl_alerts EMPTY_OK (phantom). Storage 0.076 GB / 50 GB → 0.15 % belegt.
- **Recording_f0 ist in der Sandbox NICHT vorhanden.** Alle Welle-2-Datenanalyse-Schritte, die auf diesen Bestand zugreifen, müssen via T2/T3-Runner auf der User-Maschine laufen.

### 1.4 Neue Architektur-DECs als Lehre

- **DEC-06** (Recording-Engine additiv, eigene Tabellen, eigener Parquet-Subpath) — Muster für jeden neuen Welle-2-Datenstrom: NIE den Bestands-Collector erweitern, IMMER neue Datei + neue Tabellen.
- **DEC-08** (Per-spec Subscribe + `phantom=True`) — Muster für PRD-referenzierte aber Bybit-seitig nicht existierende Endpoints: skippen mit WARN, Schema/Normaliser/Writer als Wissensspeicher erhalten, Audit-Trail in DEC.
- **DEC-09** (Append-only Daten-Scoping ohne Schwellen-Verschiebung) — Muster für jede Welle-2-Hypothese, deren Tractability nach Registrierung scheitert: Daten-Scoping als Nachtrag, NICHT Schwellen umverhandeln.

---

## 2. Welle-2-Pilot-Universum (datengestützt)

### 2.1 Die 6 OFFENEN Pilots

Quelle-Notation: `CR` = `edge-reconciliation/results/claims_register.md`, `V` = `edge-reconciliation/results/verdict.md`, `W1` = `WAVE1_FINAL_REPORT.md` §6.

| Pilot | Quelle | Datenbasis (Tabelle/Stream) | Repo-Integrationspunkt | Daten-Verfügbarkeit | Falsifizierbarkeit (H-04+-Skizze) |
|---|---|---|---|---|---|
| **C-07 Permutation Entropy** | CR §C-07, V §1f, W1 | `kline_1min` (Backfill vorhanden) **oder** `trades` für Inter-Arrivals — billigster Datenpfad. | Neues Paket `src/bybit_edge/research/c07_pe/` analog zu c31_cfar; CLI `scripts/c07_pe.py`. Driver read-only über `PersistenceLayer.query_kline`. | **Sofort baubar** — nur Kline, kein Tiefen-Stream/INC-06, vorhandener Bestand reicht. | H-04: bedingte AUC ≥ 0.55 in ≥ 2 disjunkten OOS-Fenstern auf den 5 Standardsymbolen, m/τ VORAB FIXIERT (Verdict S-A5: „m/τ vorab fixiert sonst DROP"), Vorbedingung ρ-Vorprüfung ≥ 0.3 (CR §C-07; sonst Ein-Fenster-DROP, kein Lauf). FDR-Familie F-PE über die m/τ-Konditionierungen, BH α=0.10. |
| **C-01 OFI** (nur Vorzeichen-Test ZUERST) | CR §C-01, V §1f, W1; INC-02 | `trades` + `orderbook_snapshots` (publicTrade + L2-Tiefe); Bestand der `trades`-Tabelle reicht für Vorzeichen-Test. | Vorzeichen-Test: schmaler Driver `src/bybit_edge/research/c01_ofi_sign/` (read-only); kein BaseModule-Wiring. Bestehendes `m2_ofi.py` bleibt unangetastet (bekannte C-01/C-02-Vertauschung, repo_survey §4). | **Sofort baubar** für den Vorzeichen-Test (kapitalfrei, `trades` reicht). Voller Edge-Test braucht L2-Tiefen-Stream über längeren Zeitraum (Wochen). | H-04: hit-rate Vorzeichen-OFI vs. signierte Marktrichtung (Aggressor-erkennbar via taker_buy) auf disjunkten Fenstern; INC-02-Test = ob OFI-Vorzeichen Aggression markiert oder MM-Replenishment. Schwelle aus Verdict: scheitert Vorzeichen-Test → DROP für C-01 + C-09/C-14-OFI-Erbe. Edge-Folge-Test nur wenn Vorzeichen besteht. |
| **C-06 (NICHT-triviale MR)** | CR §C-06, V §1a, W1 | `kline_1min` + ggf. L2-Entropie-Snapshots. Simple Sign-Flip-MR durch E-04 (hit_sum 0.179) bereits widerlegt (Verdict §2 CS-02). | Hypothesen-Arbeit ZUERST, KEIN Code-Pfad ohne sauber registrierte H-04. `m6_entropy.py` existiert (L3-Regime), aber als Direktions-Generator falsifiziert. | **Sofort baubar wenn die NICHT-triviale MR-Hypothese formuliert ist** — sonst blockiert auf Hypothesen-Ebene. | H-04: separates Folge-Signal, das nicht die einfache Entropie-Inversion ist (Verbot Sign-Flip-MR; PRD §6). Beispielsweise: Entropie-Spike → Vol-Cluster → spezifisches MR-Profil über T+1..T+k mit Schwelle X. Erfordert Hypothesen-Arbeit, BEVOR ein Lauf zulässig ist. Risiko: nicht formulierbar, dann **nicht offen, sondern „blockiert auf H-Ebene"**. |
| **C-20 MOMENT (Zero-Shot Neulisting)** | CR §C-20, V §1d, W1 | `kline_1min` auf **neu gelistete Symbole** (KEIN Lookback) — Verdict-Bedingung: einziger Fall ohne verlorenen HAR-Vergleich. | Neues Paket `src/bybit_edge/research/c20_moment_zs/`; CLI; Datenquelle = REST-Backfill (Klines neu gelisteter Symbole) via `persistence/backfill.py`-Stil. | **Tage Vorlauf** für Listings-Stream: Bybit listet ~wenige Symbole/Monat; konfirmatorische N=10–20 Listings sammeln → Wochen, evtl. Monate. Für T2-Quick-Fit reicht der vorhandene Listings-Bestand der letzten Monate aus dem öffentlichen Kline-Backfill (sofort baubar als Demonstrator), aber das gate-konfirmatorische Volumen braucht Vorlauf. | H-04: MASE < 1.0 auf RV-Zero-Shot in ≥ 2 disjunkten OOS-Fenstern (verschiedene Listings als Fenster). Kein HAR-Vergleich (Verdict: „Sonst DROP"). FDR-Familie F-MOMENT-ZS klein (1–2 Konditionierungen). Risiko: Heavy-Foundation-Model-Dep — DEC-Kandidat analog DEC-04 für `momentfm`-Extra. |
| **C-17/C-41 Cross-Sectional 2-Symbol-Mess-Gate** | CR §C-17/C-41, V §1e, W1 | `trades`/`tickers` zweier Symbole (Standardpaar BTC/ETH; ggf. ETH/SOL). Kein neuer Stream nötig. | Neues Paket `src/bybit_edge/research/c17_c41_lead_lag/`; CLI. Kapitalfrei: nur Lead-Lag-Existenz prüfen, keine Backtest-Friction-Integration. | **Sofort baubar** — `trades`-Bestand reicht. | H-04: Renyi-Transfer-Entropy + Wavelet-Coherence-Lift ≥ Schwelle X gegen Surrogate-Null, in ≥ 2 disjunkten Fenstern, AUF KAPITALFREIEM MESS-GATE (keine Edge-Behauptung, nur Lead-Lag-Existenz). FDR-Familie F-LL über Konditionierungen (Lag-Längen, Quantile, beide Achsen C-17 ∧ C-41). BH α=0.10. Wichtig: Risiko = abgegraste 30–60s-HFT-Anomalie (Verdict S-2) — Schwelle muss „handelbare" Asymmetrie sein, nicht jede Mikro-Asymmetrie. |
| **C-40 RPI Hidden-Liquidity (FORSCHUNGS-/S-R-Asset, kein Edge-Pilot)** | CR §C-40, V §1f, W1, PRD §5 PARK | `rpi_orderbook` (~5 Mio Zeilen vorhanden, Welle 1). | Neues read-only-Analysepaket `src/bybit_edge/research/c40_rpi_obs/` für Auswertungen (Aggregation, Snapshot-Statistiken, evtl. Hidden-Size-Distribution). **KEIN Edge-Gate.** | **Sofort baubar** — die ~5 Mio Zeilen sind das größte Welle-1-Datenkapital. | KEINE Alpha-Hypothese registrieren (Verdict: selbstzerstörender Edge, HFT liest RPI live; PRD §5: „kein Handels-Edge-Claim"). Forschungs-Lauf liefert Snapshot-Statistiken / Provenance-Reports für spätere Pilots (z.B. C-39-Stress-Anatomie). Falsifizierbarkeit = N/A (kein Gate); Lieferprodukt = Daten-Beschreibung, Sunset-Review nach 3 Monaten. |

### 2.2 Die 8 BLOCKIERTEN Pilots

| Pilot | Welle-1-Blockade | Entblockungs-Bedingung (Notiz, NICHT Auftrag) |
|---|---|---|
| **C-10 MF-DFA/Hölder** | H-02 DROP entzieht den C-42-Anker; ΔR²-Gate misst sonst gegen ein Phantom (GL-001). | Neue H-02b mit bit-genauer Original-Feature-Spec (Kestrel-v1.4-Notebook). Bestätigt diese das C-42-OOS-R²-Tor, kann C-10 starten. |
| **C-11 TDA/Persistent Homology** | Wie C-10. | Wie C-10; IV-Surface-Variante zusätzlich an C-33-Fortschritt gekoppelt. |
| **C-12 RQA** | Wie C-10. | Wie C-10. |
| **C-34 GMM-Vol-Regime + VRP** | H-02 DROP für die C-42-Hälfte; VRP-Bein zusätzlich gated (Options-Stream). | Wie C-10 (RV-Hälfte) + IV-Stream-Fix (Options-Hälfte). |
| **C-35 CEEMDAN** | H-02 DROP. | Wie C-10; zusätzlich Lookahead-KILL-Gate vor ΔR². |
| **VRP-RV-Bein** | H-02 DROP. | Neue H-02b. |
| **C-08 BOCPD (Ockham-tot)** | H-01 DROP: iter-5-Time-Stop hat den E-10-Tail sauber gekappt (max Hold 178 s; n<−30bps 33→25) — der Ockham-Test ist überflüssig, weil der triviale Time-Stop bereits funktioniert. | Würde nur dann lohnen, falls eine NEUE Time-Stop-bezogene Hypothese auftaucht, die einen Bayes'schen Change-Point-Detektor verlangt. Aktuell „tote Spur". |
| **C-37 Spread-Execution / CS-12 Funding-Uhr K2 / C-31-Bein von CS-07** | C-37: H-01 DROP klar unter −10 bps, kein Graubereich → der Friction-Killer hat nichts zu retten. CS-12: Produkt aus E-15/C-37 — beide kollabiert. CS-07-C-31-Bein: H-03 DROP. | C-37: nur wenn eine NEUE Funding-Cluster-Strategie auftaucht, die im Graubereich landet. CS-07-C-31-Bein: nur via C-16-Pfad (C-16 ist NICHT in Welle 2 priorisiert — datenhungrig). |

### 2.3 Die 6 GATED Pilots (Recording-Vorlauf-Schätzung)

Datenbasis: aktueller Recording-Stand `recording_check.json` 2026-06-15 (4 987 255 RPI / 95 600 premium-index / 58 insurance) und 8h-Lauf-Telemetrie (`upload_20260614/.../RECORDER_LONG.err.log`: 263 865 Frames in 8h → ~33 k Frames/h; 40 MB / 8h → ~5 MB/h; ~330k rpi-Zeilen/h hochgerechnet).

| Pilot | Vorlauf-Schätzung | Begründung |
|---|---|---|
| **C-33 VRP / Short-Vola** | **≥ 12 Monate ab funktionierendem IV-Stream + ≥ 1 Stress-Periode** (PRD §4 explizit „NICHT 3 Mon., Peso-verzerrt"). Stand 2026-06-15: IV-Stream tot (`option_tickers` NO_DATA aus DIAG2, nicht final geklärt). | Bybit-Options-WS bricht alle ~30 s mit 1011 keepalive ping timeout (GL-004). Diagnose-WP für Welle-2-Vorlauf erforderlich. Selbst wenn der Stream MORGEN funktioniert, **Earliest-Gate-Lauf ≈ Juni 2027**. |
| **C-27 Cori-Rₜ + C-28 NB-k** (= EIN Test, geteilter ω_s-Kernel) | **Wochen bis Monate** ab funktionierendem `insurance_pool`+`adl_alerts`-Stream. Stand: insurance_pool 58 Zeilen / 8h → ~7 Events/h, event-arm; adl_alerts ist phantom. | PRD §4 + Verdict §4: „Bulk-Historie ≥ 30 Kaskaden" benötigt. Bei ~7 Insurance-Events/h und unklarer Kaskaden-Definition → Größenordnung ≥ 8–12 Wochen, eher länger; harter Stress-Anteil nicht garantiert (GM-6). adl_alerts-Bybit-Topic-Klärung ist offene Vorbedingung. |
| **C-29 Avalanche Shape-Collapse** | **Wochen** ab kontinuierlichem rpi/insurance-Recording. | Recording läuft; Kaskaden-Anzahl analog C-27/C-28. PRD §4: „Recording-Vorlauf + ω_s-Stabilität". Earliest ≥ 6–8 Wochen. |
| **CS-06 Kaskaden-Cockpit** | **sequenziell NACH C-27/C-28/C-29** — also frühestens 3–4 Monate. | Verdict §4: „nach Validierung von C-27/C-28/C-29". |
| **C-39 Kaskaden-Anatomie** | **Monate** + Bybit-Topic-Klärung für `adl_alerts`. | PRD §5 PARK: monatelang datenleer, kein REST-Archiv. insurance läuft (58 rows), adl_alerts phantom blockiert das ADL-Bein bis Bybit-Topic-Klärung. Stress-reiches Fenster nicht garantiert. |
| **C-25 Toxic Flow / Kyle-λ / VPIN** | **Zirkulär gated**: braucht positive Basis-Strategie (Verdict §1f). | Mit allen drei Welle-1-Alpha-DROPs gibt es derzeit keine positive Basis-Strategie. C-25 bleibt gated bis ein Welle-2-Pilot eine positive Basis liefert. Nicht aktiv planbar. |

---

## 3. Daten-Vorlauf-Zeitachse (konsolidiert)

| Zeithorizont | Was geht | Quelle |
|---|---|---|
| **HEUTE / sofort** | C-07 Permutation Entropy (Kline-Bestand reicht); C-01-Vorzeichen-Test (publicTrade-Bestand); C-17/C-41-Mess-Gate (publicTrade-Bestand, 2 Symbole); C-40 Forschungs-Asset (4.99 Mio RPI-Zeilen vorhanden); C-06-Hypothesen-Arbeit (kein Lauf, aber Vorbereitung) | `kline_1min`, `trades`, `rpi_orderbook` Bestand |
| **1 Woche** | C-20 MOMENT-Zero-Shot (Demonstrator-Lauf auf letzten 3–6 Monate Listings); zusätzlicher Recording-Daten-Akkumulationsbedarf gering | öffentliche Kline-API + REST-Backfill für Listings |
| **1 Monat** | Recording-Akkumulation: rpi_orderbook von 4.99 Mio → ~10–13 Mio Zeilen (bei ~330k/h × 24 × 30 ≈ 240 Mio rohe Events; real-Bypass: ~+5–7 Mio gespeicherte Zeilen/Monat aus Telemetrie). premium_index_kline-Backfill substantiell. C-29-Skala beginnt erreichbar wenn Stress-Periode trifft. | recording_check.json + RECORDER_LONG-Hochrechnung |
| **≥ 3 Monate** | C-27/C-28/C-29-Schwellen ≥ 30 Kaskaden erreichbar (wenn Stress trifft); CS-06 sequenziell danach. | PRD §4 + Verdict §4 |
| **≥ 12 Monate** | C-33 VRP (Vorbedingung: IV-Stream-Defekt vorher geklärt + Stress-Periode in den 12 Monaten enthalten) | PRD §4 wörtlich |

Storage-Cap-Hochrechnung: 0.076 GB / 8h ⇒ ~0.23 GB / Tag ⇒ ~7 GB / Monat ⇒ **50-GB-Deckel erreicht nach ~7 Monaten** Dauerbetrieb (DEC-07 ringpuffer, danach Eviction). Sunset-Review nach 3 Monaten (PRD §9) greift VOR Cap-Eviction → kein Daten-Lake-Risiko in Welle 2.

---

## 4. Recording-Infrastruktur-Diagnose-Liste (offene Defekte aus Welle 1)

| Defekt | Welle-1-Stand (Quelle) | Welle-2-Auswirkung | Empfehlung |
|---|---|---|---|
| **`option_tickers` NO_DATA** | Subscribe wird `success=true` bestätigt, 0 Frames in 5 min, WS-Drop alle ~30 s mit `1011 keepalive ping timeout`. DEC-08 hat `adlAlert` als phantom geklärt, aber **dieser Defekt ist offen** (GL-004, W1 §3). | **Blockiert C-33 VRP** (12-Monat-Vorlauf kann nicht beginnen, bis IV-Datenfluss läuft). Blockiert IV-Surface (C-11-M-S17). Nicht für die C-07/C-01/C-17-Welle-2-Pilots blockierend. | Diagnose-WP in Welle 2: Bybit-v5-Doc-Verifikation Topic-Spelling (`tickers.BTC` vs `tickers.<expiry>`?), Keepalive-Frequenz, evtl. Sub-Underlying-Pattern. NICHT in Phase 2 (PLAN) priorisieren falls Welle 2 nur Sandbox-baubare Pilots wählt; aber für Phase 3+ als parallele Vorlauf-Reparatur (DEC-08-Pattern: per-spec subscribe schützt vor Kollateral). |
| **`insurance_pool` event-arm (58 rows / 8h)** | recording_check.json 2026-06-15: 27 files / 58 rows. ~7 Events/h. | **C-27/C-28/C-29/C-39** brauchen ≥ 30 Kaskaden — bei dieser Rate Monate. Plus Stress-Anteil nicht garantiert (GM-6). | Akzeptieren als Vorlauf-Realität. Statistische Modelle (NB-k, Cori-Rₜ) sind grundsätzlich für seltene Events designed; aber Welle-2-Auswahl muss berücksichtigen: cascade-Pilots sind NICHT „1-Monat-baubar". |
| **`adl_alerts` phantom (DEC-08)** | Bybit-Topic `adlAlert` existiert nicht. Schema/Normaliser/Writer als Wissensspeicher erhalten. | Blockiert C-39-ADL-Bein (PRD §5 PARK). | Bybit-Doc-Recherche als parallele Welle-2-Sub-WP; falls echtes Topic gefunden → `phantom=False` umstellen (1-Zeilen-Revert). |
| **Recording-Engine-Cap (50 GB) vs. Tages-Volumen** | ~0.23 GB / Tag (Hochrechnung aus 0.076 GB / 8h). | Bei ungehinderter Akkumulation: Cap erreicht nach ~7 Monaten Dauerbetrieb. | Sunset-Review nach 3 Monaten (PRD §9) greift VOR Cap. Kein akutes Problem für Welle 2. |
| **WS-Subscribe-Ack-Logging-Bug (PS-5.1)** | `rc=` leer in T3-Runner-summary.txt (GL-001 Statusvorbehalt). | Welle-2-Auswertung muss auch Inhalte (results.json) lesen, nicht nur summary. Bekanntes Muster — gate-auditor handhabt das bereits korrekt. | Keine Aktion. |

---

## 5. Schutzgüter-Status für Welle 2

1. **Laufender Collector / Festplatten-Aufzeichnung 1.0** — `src/bybit_edge/collector/ws_collector.py`, `live_runner.py`, `multi_runner.py`, `persistence/db.py`. Welle-2-Regel unverändert: KEINE Edits ohne Collector-Smoke-Test (T2, User-Maschine). DEC-06-Pattern weiter befolgen: neue Streams via Recording-Engine, NICHT via Collector-Erweiterung.
2. **Test-Suite Welle-1-Endstand: 776 grün** (gemessen 2026-06-15, `tests/unit/`). Floor für Welle 2. Forensik-Tests unantastbar.
3. **Bestehende Parquet-Daten + `data/parquet/recording_f0/`** — read-only. Neue Welle-2-Daten in NEUE Pfade/Tabellen.
4. **Welle-1-Code (Tooling-Status):**
   - `src/bybit_edge/recorder/`: bleibt produktionsstabil. STRUKTURELLE Erweiterung (z.B. options-WS-Fix, neue Streams) nur mit eigenem DEC.
   - `src/bybit_edge/research/{c31_cfar, c42_rv, e15_eval}/`: **eingefroren als Audit-Trail.** Bug-Fixes nur via neuer Hypothesen-Registry-Zeile.
   - `scripts/{c31_cfar.py, c42_repro.py, evaluate_e15.py}`: bleiben. Werden NICHT erweitert.
   - Welle-1-Tests (`test_recorder_*.py`, `test_c31_cfar.py`, `test_c42_rv.py`, `test_e15_eval.py`): bleiben grün, werden NICHT angefasst außer wenn das `recorder/`-Paket strukturell weiterentwickelt wird (dann mit eigenem DEC).
5. **9 DEC-Entscheidungen** als Architektur-Audit-Trail. Welle-2-DECs werden ab **DEC-10** nummeriert, gleiches Format. Welle-1-DECs unverändert.

---

## 6. Sandbox-Fähigkeiten (Update zur Welle-1-Survey §5)

- **Bybit-API-Erreichbarkeit (Test 2026-06-15):** `curl -s -m 5 "https://api.bybit.com/v5/market/time"` → **`Host not in allowlist: api.bybit.com`** (Sandbox-Netzwerk-Egress-Blocker). **Identisch zu Welle 1.** Konsequenz: alle Live-Stichproben, Recording-Smoke-Tests, REST-Backfill-Live-Calls sind T2/T3 (User-Maschine). T0/T1-Fixtures müssen aus eingecheckten Mini-Beständen oder synthetisch generiert werden.
- **Python-Test-Suite läuft in Sandbox** (`python -m pytest tests/unit/ --collect-only -q` → 776 in 111 s). T0/T1 voll fähig.
- **Sandbox-Datenlage unverändert:** `data/parquet/` leer, `data/bybit_edge.duckdb` nicht vorhanden. Alle Replay-/Recording-Outputs der User-Maschine sind über `scinance2-impl/handoff_local/results/upload_*` versioniert nachvollziehbar.
- **Welle-2-Konsequenz:** identisch zur Welle 1 — alle Welle-2-Pilots werden in der Sandbox bis T1-Stufe gebaut/getestet (Code + Fixtures + Unit-Tests + Kurz-Replays auf Fixtures); die konfirmatorischen Voll-Läufe (T3) gehen via `handoff_local/` an die User-Maschine.

---

## Anhang: konkrete Welle-2-Empfehlungs-Reihenfolge (für Phase 2 / architect)

Aus W1 §8 + Verdict §4 + datengestütztem Status oben, **FDR-Familien-Budget bedenkend** (PRD §8: Welle-1-Parallelitäts-Deckel max. 3–5 Pilots, max. 1 neuer Alpha-Test pro Welle — Multiple-Testing-Korrektur über alle Welle-2-Alpha-Hypothesen verpflichtend):

1. **C-17/C-41 Cross-Sectional 2-Symbol-Mess-Gate** — kapitalfrei, sofort baubar, schmaler Code-Pfad, kann früh DROP-en. Niedrigste FDR-Last weil kein Kapital, nur Existenzprüfung.
2. **C-01-Vorzeichen-Test (INC-02)** — kapitalfrei, sofort baubar, schmal. Falls DROP → kaskaden-wirksam auf C-01/C-09/C-14-OFI-Erbe.
3. **C-07 Permutation Entropy** — sofort baubar, billigster Alpha-Lottoschein (Verdict-Wortlaut), nur Kline. ρ-Vorprüfung ≥ 0.3 schützt vor unnötigem Voll-Lauf.
4. **Optional 4. Slot (eines von):** C-20 MOMENT Zero-Shot (Demonstrator-Lauf in 1 Woche möglich); ODER C-40-Forschungs-Asset (kein Alpha-Gate, FDR-frei, liefert Daten-Beschreibung der ~5 Mio RPI-Zeilen). C-06 NICHT-triviale MR erst NACH Hypothesen-Formulierungsarbeit als WP-0 — vorher kein Lauf zulässig (Registry §1).

Parallel als Vorlauf-/Diagnose-WPs (NICHT als Alpha-Gates):
- Recording-Engine läuft weiter (Vorlauf für C-27/C-28/C-29/C-33/C-39).
- `option_tickers`-Defekt-Diagnose-WP (Bybit-v5-Doc-Verifikation + Keepalive-Fix) als unabhängige Reparatur-Aufgabe.
- `adl_alerts`-Bybit-Topic-Klärung (DEC-08-Rückbau falls echtes Topic gefunden).

**Empfohlenes effektives Alpha-Test-Budget Welle 2 = 2–3 (nicht 4).** Begründung: drei der vier Welle-1-Tests waren Reproduktion/Infrastruktur, nur C-31 war echter neuer Alpha-Test (PRD §8.1). Welle 2 kann mit 2–3 neuen Alpha-Tests (C-07, C-01-Vorzeichen, C-17/C-41) bei verschärfter FDR fahren; C-06 erst nach Hypothesen-Formulierung; C-20 als optionaler 4. Slot je nach Listings-Datenlage.

---

*Quellen durchgängig: `scinance2-impl/state/{WAVE1_FINAL_REPORT.md, wave2_state.md, gate_log.md (GL-001..005), decisions.md (DEC-01..09), hypothesis_registry.md (H-01..H-03), repo_survey.md}`, `FINAL_PRD.md §3/§4/§5/§7/§8/§9`, `edge-reconciliation/results/{verdict.md, claims_register.md}`, `handoff_local/results/upload_20260615/.../recording_check.json`, `handoff_local/results/upload_20260614/.../RECORDER_LONG.err.log`, Sandbox-Probe `python -m pytest tests/unit/ --collect-only -q` (2026-06-15 → 776 grün), Sandbox-Probe `curl https://api.bybit.com/v5/market/time` (2026-06-15 → blockiert).*
