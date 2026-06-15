# Welle-1-Abschlussbericht — Scinance 2.0

**Branch:** `scinance2-wave1`
**Stand:** 2026-06-15
**Status:** DONE (Welle 1) — alle vier Pilot-Gates entschieden

---

## 1. Executive Summary

Welle 1 ist abgeschlossen. Vier Pilots wurden gegen die vorregistrierten Tore der Hypothesen-Registry (H-01/H-02/H-03) und das C-36-Pilot-Statement (PRD §3) entschieden: **drei DROP-Verdikte auf den drei Alpha-Hypothesen, ein tragender Infrastruktur-Erfolg**. Die drei DROPs ergeben zusammen einen einzigen, harten Befund: keiner der drei in Welle 1 angegriffenen Edge-Claims (S3-Pre-Settlement-Exit, C-42-Vol-Anker, C-31-CFAR-Anomalie) überlebt ein vorregistriertes Out-of-Sample-Tor. Die Friction-Wand (FINAL_PRD §1: 11 bps Round-Trip) bleibt für alle drei mechanisch unberührt. Damit ist die letzte aus dem Scinance-1.0-Portfolio verbliebene Strategie (S3) gefallen *(GL-004)*, der Vol-Stack-Anker entfällt *(GL-001)*, die CFAR-Anomalie ist ~250× unter der Wand widerlegt *(GL-005)*. **Welle 2 ist offen** in der von FINAL_PRD §4 sequenzierten Form, allerdings ohne den Vol-Stack-Pfad — der bleibt ohne neue, sauber registrierte H-02b gesperrt.

## 2. Die drei DROP-Verdikte

### Übersicht

| Pilot | Vorregistrierte Schwelle | Messwert (worst-of) | Verfehlt um | GL-Referenz |
|---|---|---|---|---|
| **H-01 · S3 iter-5** | Netto-Edge ≥ −5 bps (WEITER) / ≤ −10 bps (DROP) | Netto −15.47 bps, RAW −4.48 bps | 5.47 bps unter DROP-Schwelle | *(GL-004 · 2026-06-13)* |
| **H-02 · C-42 RV** | OOS-R² ≥ 0.15 in ALLEN Fenstern UND QLIKE < HAR in ALLEN | min Fold-R²: BTC −0.32 · BNB −0.53 · ETH −0.15 · SOL −0.08 · XRP −0.03 (5/5 verfehlt); QLIKE-Schlag: 0/5 Symbole in allen Folds | Anker-Hypothese, 0/5 Symbole bestehen, 0/36 Features BH-FDR-signifikant | *(GL-001 · 2026-06-12)* |
| **H-03 · C-31 CFAR** | Surrogate p ≤ 0.05 in ≥ 2 Fenstern UND Lead > 50 ms UND Edge > 11 bps | p ∈ [0.801; 1.000] auf 4 Fenstern; Edge ∈ [0.01; 0.04] bps | Edge ~250× unter 11-bps-Wand; p deckungsgleich mit Null | *(GL-005 · 2026-06-15)* |

### H-01 — S3-Pre-Settlement (iter-5-Fix)

Die iter-5-Modifikation (Tick-Zeit-Time-Stop, friction-aware Hard-Stop) lieferte die mechanisch erwarteten Tail-Reduktionen sauber: `time_stop_exceeded` stieg 1 → 128, die maximale Haltedauer fiel von 2 124.9 s auf 178.4 s, der worst-trade von −56.60 bps auf −38.10 bps, `n<−30bps` von 33 auf 25 *(GL-004 Mechanik-Tabelle)*. Die mean Netto-Edge bewegte sich dabei nur von −16.81 bps auf −15.47 bps. Entscheidend: die **RAW-Edge bei null Friktion** verbessert sich nur von −5.81 auf −4.48 bps und bleibt **auf allen 5 Symbolen negativ** (RAW ∈ [−5.65; −3.07] bps je Symbol). Der Entry hat keine Edge; der Exit war Symptom, nicht Ursache. Die iter-4-Hypothese „S3 ist tail-driven, bounded-loss legt die Edge frei" ist damit kontrolliert widerlegt.

### H-02 — C-42-Reproduktion (LightGBM/HAR-RV)

Der vorregistrierte purged-Walk-Forward-Lauf (Purge 60 Bars + Embargo 1440 Bars, 3 disjunkte Folds, n_test = 12 925 je Fold; FDR-Familie F-VOL mit BH α = 0.10 über 36 Features) liefert auf allen fünf Symbolen ein **min OOS-R² < 0.15** und schlägt die HAR-RV-Baseline auf keinem Symbol in allen drei Folds *(GL-001 Befund-Tabelle je Symbol × Fold)*. Die FDR über die 36-Feature-Familie ist auf **0/36 signifikant** in jedem Symbol — kein einzelnes Feature trägt nach Korrektur. Das bestätigt die Forensik-Hypothese: der dokumentierte Test-R²≈0.249 *(research_notes/claims_register C-42)* war ein L1-Selbstauskunfts-Artefakt und überlebt sauberes Testdesign nicht. Da die Feature-Provenance **1 DOCUMENTED / 35 ASSUMED** ist, ist eine Erbschaftsfrage offen; die Stärke des Negativbefunds (5/5 Symbole × beide Kriterien × FDR 0/36) macht es jedoch unwahrscheinlich, dass die Feature-Spec allein das Vorzeichen kippt *(GL-001 Reproduktions-Treue-Vorbehalt)*.

### H-03 — C-31 Cyclostationary CFAR

Auf den vier unabhängig gemessenen, vorregistrierten Fenstern (BTC × 2, ETH × 2) liegt der **Surrogate-p-Wert bei [0.801; 1.000]** und ist damit statistisch nicht von der geshuffelten Inter-Arrival-Null zu unterscheiden. Die geschätzte Edge ist **0.01 – 0.04 bps**, ~250× unter der 11-bps-Friction-Wand *(GL-005)*. Die Lead-Zeit ist zwar 100 ms (> 50 ms-Schwelle), aber der gemessene Effekt ist ökonomisch tot. Drei Symbole timeouteten (SOL/BNB/XRP — 1 800 s je Symbol); methodisch nicht entscheidungsrelevant, weil das Gate je Symbol operiert und das harte Ein-Fenster-DROP-Kriterium *(PRD §8.5, Registry §6)* bereits durch BTC-F0 ausgelöst wurde. Die F-CFAR-Familie (3 Varianten × BH α = 0.10) ergibt p_crit = 0.000 — kein Test überlebt die Korrektur. Die im verdict.md §1f formulierte Skeptic-Vorhersage (HFT-abgegraste Anomalie, adaptiver Gegner, kein Retail-überlebender Lead) ist auf publicTrade-Inter-Arrivals bestätigt.

## 3. C-36 Recording-Engine — was funktioniert und wie viel

C-36 ist **kein registriertes Alpha-Gate** *(GL-004 Pilot-Statement)*, sondern Infrastruktur (PRD §3). Das vorregistrierte F0-Recall-≥95%-Gate ist ein 2–4-Wochen-Ziel und in Welle 1 nicht fällig. Gemessen wurde der Betriebsstatus:

| Datum / Stream | Messwert | Quelle |
|---|---|---|
| 8h-Recorder-Dauerlauf 2026-06-13 | 263 865 Frames, 40.06 MB, 3 945 Segmente, 0 Evictions | *(upload_20260614/.../RECORDER_LONG.err.log)* |
| T2-Smoke 2026-06-13 (Anschluss-Test) | rpi_orderbook 29 886 rows / insurance_pool 8 rows / premium_index_kline 1 000 rows | *(state.md ANALYZE 2026-06-13)* |
| Stand 2026-06-15 (Cumulative) | rpi_orderbook 4 987 255 rows · insurance_pool 58 rows · premium_index_kline 95 600 rows · option_tickers NO_DATA · adl_alerts EMPTY_OK | *(upload_20260615/.../recording_check.json)* |
| Storage-Deckel | 0.076 GB / 50 GB → 0.15 % belegt, kein Eviction-Druck | *(recording_check.json `cap`)* |

Drei strukturelle Lehren aus dem Recording-Aufbau, die als wiederverwendbare Praxis in Welle 2 weiterleben:
- **DEC-08 Per-Spec-Subscribe + Phantom-Flag** *(decisions.md)*: Die gebündelte Subscribe-Request der ersten Iteration wurde durch ein einziges nicht-existierendes Topic (`adlAlert`) komplett abgelehnt — Bybit-Antwort `error:handler not found,topic:adlAlert`. Folge des Fixes: jede `StreamSpec` sendet eine eigene Subscribe-Request (Isolation); `adl_alerts` ist als `phantom=True` markiert, das Schema/Normaliser/Writer als Wissensspeicher bleibt erhalten. **INC-06-Bestätigung:** PRD-referenzierte Endpoints können falsch sein; Phantom-Markierung mit Audit-Trail ist die reversibelste Behebung.
- **`option_tickers` NO_DATA bleibt offen**: Subscribe wird akzeptiert (success=true), aber 0 Frames in 5 min + WS-Drops alle ~30 s mit `1011 keepalive ping timeout` *(GL-004)*. Kein Phantom — wahrscheinlich event-arme Push-Frequenz oder Reconnect-Bug. Diagnose-WP für Welle-2-Vorlauf, blockiert nichts in Welle 1.
- **Storage-Deckel-Logik (DEC-07)** *(decisions.md)*: 50-GB-Default ratifiziert, ringpuffer-basiert, CLI-überschreibbar. Bei 0.15 % Belegung nach 8h-Dauerbetrieb ist die Sunset-Review-Tiefe (3 Monate, PRD §9) bequem erreichbar.

## 4. Was empirisch erledigt ist

- **Scinance-1.0-Portfolio (S1–S5) vollständig empirisch erledigt** *(FINAL_PRD §6 + ANALYZE 2026-06-13)*. S1: GL/iter-4 ρ-Estimator gebrochen (C-14 REFUTED, E-01: ρ-Median ≈ 2e-7 sechs Größenordnungen unter Schwelle 0.85). S2: drei Forensiken (E-03/E-04/E-16) widerlegen die Richtungsthese. S3: jetzt nach bounded-loss-Test definitiv, der Entry hat keine Edge auf keinem Symbol *(GL-004)*. S4/S5: nie tragfähig (Loader-/Panel-Harness-Lücken, E-13/E-14). Der letzte Eintrag des Original-PRDs ist gefallen.
- **Vol-Stack-Kaskade gesperrt** *(GL-001 Konsequenzen)*: H-02-DROP entzieht C-42 den Anker. **C-10, C-35, C-11, C-12, C-34 und das VRP-RV-Bein** dürfen nicht starten — alle ΔR²-Gates messen sonst gegen ein Phantom *(FINAL_PRD §3 Pilot-2-Abbruchkriterium, verdict §7)*. Reaktivierung erfordert eine neue, separat registrierte H-02b mit bit-genauer Original-Feature-Spezifikation; eine Torpfosten-Verschiebung am bestehenden H-02 ist verboten *(Registry §2)*.
- **CFAR-Anomalie auf publicTrade-Inter-Arrivals widerlegt** *(GL-005)*. 4 unabhängige Fenster auf BTC und ETH, p ≈ 1.0, Edge ~250× unter der 11-bps-Wand. Selbst wenn ein zukünftiges Surrogate-Setup ein signifikantes p liefern würde, wäre die handelbare Edge inhaltlich tot. Konsistent mit der iter-3-Skeptic-Argumentation aus verdict §1f.

## 5. Was als Werkzeug / Infrastruktur in Welle 2 weiterlebt

Kategorisiert, aus state.md CHANGELOG + decisions.md aufgesammelt:

- **Recording-Engine F0 (C-36)** — produktionsstabil, ~5 Mio rpi_orderbook-Zeilen / Cumulative bis 2026-06-15 *(recording_check.json)*; per-spec-Subscribe + Phantom-Flag *(DEC-08)*; 50-GB-Ringpuffer-Default *(DEC-07)*; Sunset-Review nach 3 Monaten *(PRD §9)*. Höchster Welle-2-Hebel.
- **Hypothesen-Registry-Disziplin** — die vorregistrierten Tore haben in 3/3 Fällen gehalten: keine Torpfosten-Verschiebung, kein Nachregistrieren von Schwellen. Der Append-Only-Nachtrag *(DEC-09)* — Fenster-Tick-Cap `WINDOW_MAX_TICKS=150 000` für CFAR — ist ein sauberes Pattern für Daten-Scoping-Klärungen ohne Schwellen-Verstoß.
- **9 DEC-Entscheidungen als Architektur-Audit-Trail** (DEC-01 PRD-Platzierung, DEC-02 Pfad-Parametrisierung, DEC-03 research-Paket-Layout, DEC-04 LightGBM-Extra, DEC-05 C-42-Heimat, DEC-06 additive Recording-Engine, DEC-07 50-GB-Deckel, DEC-08 per-spec subscribe, DEC-09 Fenster-Tick-Cap). Alle reversibel, alle mit Rückbauweg dokumentiert.
- **T2/T3-Runner-Suite** *(state.md HANDOFF)*: `run_short.{sh,ps1}`, `run_overnight.{sh,ps1}`, `run_cfar_only.{sh,ps1}` mit `--db-copy`, `--max-ticks-per-window`, Pfad-Kaskade `trades_all.csv ↔ trades_iter5/`, Tick-Cap, Progress-Logging auf stderr, Per-Step-Timeout.
- **Test-Suite-Wachstum:** 616 → 752 grün (+136), gestartet 2026-06-11, alle Forensik-Tests *(test_replay_backtester_maker_only.py, test_strategy3_bounded_exits.py, test_strategy_direction_inversion.py)* unangetastet. Plus die zwei neuen `TestPerSpecSubscribeAndPhantom`-Tests *(DEC-08)*. c31-Suite 29→36 nach CFAR-Timeout-Fix.
- **Diagnose-Werkzeug:** DuckDB-Lock-Detektor mit 30-s-Timeout, `--db-copy`-Flag (kollisionsfrei mit laufendem Collector); Epoch-ms-Plausibilitätsfilter + Spannen-Pre-Check + `MAX_BINS=1e9`-Guard in `cyclic_spectrum.py`; WS-Subscribe-Ack-Logging; Schema-Drift-Reporting in `recording_check.json`.
- **iter-5 S3-Bounded-Loss-Code** — der Code funktioniert mechanisch (Tick-Zeit-Stop wirkt, Tail-Reduktion bestätigt), nur die Edge fehlt. Bei künftigen Strategien, die einen friction-aware Hard-Stop benötigen, wiederverwendbar.

## 6. Welle-2-Implikationen

Aus FINAL_PRD §4 (sequenzierte Welle-2-Pilots) gegen die Welle-1-DROPs geprüft. Status-Logik: **offen** = keine Welle-1-Blockade, kann starten sobald registriert; **gated** = unabhängig von Welle 1, braucht aber Recording-Vorlauf (Wochen); **blockiert** = von Welle-1-DROP versperrt.

| §4-Pilot | Markt | Vorbedingung (PRD §4) | Welle-1-Auswirkung | Status |
|---|---|---|---|---|
| **C-10** MF-DFA/Hölder | F | nach C-42-Reproduktion | H-02 DROP entzieht Anker | **blockiert** (H-02b) |
| **C-35** CEEMDAN | F | nach C-42-Reproduktion + Lookahead-KILL-Gate | H-02 DROP | **blockiert** (H-02b) |
| **C-11** TDA/Persistent Homology | F | nach C-42-Reproduktion | H-02 DROP | **blockiert** (H-02b) |
| **C-12** RQA | F | nach C-42-Reproduktion | H-02 DROP | **blockiert** (H-02b) |
| **C-34** GMM-Vol-Regime + VRP | S/F/O | Bulk-Persistenz-Check + C-42 | H-02 DROP für die C-42-Hälfte | **blockiert** (H-02b) |
| **C-08** BOCPD (Ockham) | F | nach E-15: nur falls Time-Stop E-10-Tail NICHT schneidet | H-01 DROP, Time-Stop wirkte sauber (Tail eliminiert) → Ockham-Test überflüssig | **blockiert** (Ockham-tot) |
| **C-37** Spread-Execution | F | nur falls CS-03 in Graubereich | H-01 DROP klar unter −10 bps, kein Graubereich | **blockiert** |
| **CS-12** Funding-Uhr K2 | F | nach E-15 + C-37 positiv | beide kollabiert | **blockiert** |
| **CS-07** Footprint-Detektor | F | nach C-16 UND C-31 je einzeln | C-31 DROP | **blockiert** für C-31-Bein; offen nur via C-16-Pfad |
| **C-33** VRP / Short-Vola | O | ≥ 12-Mon. IV-Recording + Stress-Periode | Recording läuft, IV-Stream noch tot (option_tickers NO_DATA) | **gated** (Datenvorlauf + Recorder-Bug-Fix) |
| **C-27 + C-28** (= ein Test) | F | Recording-Vorlauf ≥ 30 Kaskaden + ω_s-Stabilität + Distributions-Check | rpi/insurance-Recording läuft | **gated** (Datenvorlauf, Wochen) |
| **C-29** Avalanche Shape-Collapse | F | Recording-Vorlauf | rpi-Recording läuft | **gated** (Datenvorlauf) |
| **CS-06** Kaskaden-Cockpit | F | nach C-27/C-28/C-29 | folgt der Cascade-Kette | **gated** (sequenziell) |
| **C-39** Kaskaden-Anatomie | F | nach C-36 + Stress-reichem Fenster | insurance.USDT + adl_alerts: insurance läuft (58 rows), adl_alerts ist phantom → blockiert für ADL-Bein | **gated** (Bybit-Topic-Klärung adl_alerts; insurance-Datenvorlauf) |
| **C-40** RPI Hidden-Liquidity | F | Recording an C-36 koppeln, kein Edge-Claim | rpi_orderbook läuft (~5 Mio rows) | **offen** (als Forschungs-/S-R-Asset, kein Edge-Pilot) |
| **C-07** Permutation Entropy | F | ρ-Vorprüfung ≥ 0.3 (m/τ vorab fixiert) | unabhängig von Welle-1-DROPs | **offen** |
| **C-01** OFI | F | INC-02-Vorzeichen-Test ZUERST | unabhängig | **offen** (Vorzeichen-Test billig) |
| **C-06** (NICHT-triviale MR) | F | neue Hypothese (Sign-Flip durch E-04 widerlegt) | unabhängig | **offen** (Hypothesen-Arbeit) |
| **C-20** MOMENT (Zero-Shot Neulisting) | F | RV auf neu gelistete Symbole | unabhängig | **offen** (Datenbedarf: Listings) |
| **C-25** Toxic Flow / Kyle-λ / VPIN | F | erst sobald positive Basis-Strategie existiert | unabhängig — aber zirkulär: braucht Basis | **gated** (Basis-Existenz) |
| **Cross-Sectional 2-Symbol-Mess-Gate** (C-17/C-41) | F | kapitalfrei, nur Lead-Lag-Existenz | unabhängig | **offen** (klein, FDR-Pflicht) |

Zählung: **6 offen, 8 blockiert, 6 gated.** Reconciliation-Verdict §4 hat C-31 und C-42 als die billigsten/zeitkritischsten Pilots ausgewählt; ihre Verdikte verschieben das Welle-2-Schwergewicht jetzt auf die nicht-Vol/nicht-CFAR-Pilots (C-07, C-01-nach-INC-02, C-06-NICHT-triviale-MR, C-17/C-41-Mess-Gate) und auf die Recording-abhängigen Welle-2-Pfade (C-27/C-28/C-29, C-33-VRP, C-39), die jetzt Datenvorlauf sammeln.

## 7. Welle-1-Kosten-Ehrlichkeit

Beziffert (alle Zahlen aus state.md CHANGELOG + Recorder-Logs + handoff_local/results):

- **~5 000 LoC Welle-1-Produktion** verteilt auf `recorder/recording_engine.py` (+ Schema/Normaliser/Writer), `research/e15_eval/` (metrics/gate/e17/report), `research/c42_rv/` (Feature-Engineering 36 Features, purged-WF-Splitter, FDR/BH, QLIKE, LightGBM-Adapter), `research/c31_cfar/` (Cyclic Spectrum, CFAR, Surrogate), `scripts/{evaluate_e15.py, c42_repro.py, c31_cfar.py, replay_all.py-erweitert}`.
- **~140 neue Tests** (Suite 616 → 752 grün), davon der Großteil in `tests/recorder/`, `tests/research/{e15_eval, c42_rv, c31_cfar}/` plus `tests/fixtures/e15/{weiter,drop,grau}/` mit echtem iter-4-Schema.
- **~20 GB Replay-Output** in `handoff_local/results/upload_2026061*` über alle Iterationen.
- **~40 MB Recording-Output** je 8h-Lauf *(RECORDER_LONG.err.log)*; aufkumuliert bis 2026-06-15: 0.076 GB / 50 GB Deckel *(recording_check.json)*.
- **Nutzer-Replay-Stunden** (handoff_local-getrieben): iter-5-Vollreplay ≈ 12 h, 2× `run_short` à ~20 min, 2× `run_overnight` à 24 h+, 1× `run_cfar_only` (BTC 712 s + ETH 661 s + 3× 1 800 s Timeouts → ~2 h gemessene CFAR-Last).
- **9 architekturelle DEC-Entscheidungen**, alle reversibel dokumentiert.

Diese Kosten sind, was eine **ehrliche Falsifikation** kostet — und sie sind dramatisch billiger als Live-Trading auf einer dieser nicht-existenten Edges. Die Welle-1-DROPs ersparen Welle 2 die Phantom-ΔR²-Vergleiche der Vol-Stack-Kaskade und das Live-Risiko einer abgegrasten CFAR-Anomalie.

## 8. Empfehlung für Welle 2

- **Nicht alle §4-Pilots gleichzeitig starten.** Die 6 offenen Pilots sequenziert anziehen — Welle-1-Parallelitäts-Deckel (max. 3–5 Pilots, max. 1 neuer Alpha-Test pro Welle, FINAL_PRD §8.1) gilt unverändert.
- **Billigste Falsifikationstests zuerst:** C-01-INC-02-Vorzeichen-Test (kapitalfrei, schnell DROP-bar), C-17/C-41-Mess-Gate (kapitalfrei), C-07 Permutation Entropy nur nach ρ ≥ 0.3-Vorprüfung. Datenbedarf gering, FDR-Pflicht über Konditionierungs-Suche.
- **Recording-Engine weiterlaufen lassen.** Sie sammelt den Vorlauf für die 6 gated Pilots (C-33 12-Mon.-IV, C-27/C-28/C-29 ≥ 30 Kaskaden). Sunset-Review (3 Monate) als Anti-Data-Lake-Bremse beibehalten. Zwei laufende Reparatur-WPs: `option_tickers` NO_DATA + `adl_alerts` Bybit-Topic-Klärung.
- **Vor jedem Welle-2-Pilot: Pre-Registration in der Hypothesen-Registry.** Schwellen, Fenster, FDR-Familie wörtlich vor Lauf-Start. Die Welle-1-Disziplin (3/3 DROP-Verdikte gegen vorregistrierte Tore, kein Nachverhandeln) ist das Schutzgut.
- **KEINE Vol-Stack-Reaktivierung ohne H-02b.** Eine bit-genaue Original-Feature-Spezifikation für C-42 ist die einzig zulässige Wiederaufnahme — und sie ist eine NEUE Hypothese mit eigener Registry-Zeile, keine Erweiterung von H-02. Torpfosten-Verschiebung ist verboten *(Registry §2; GL-001 Reproduktions-Treue-Vorbehalt)*.

---

*Quellen durchgängig: `state/gate_log.md` (GL-001 – GL-005), `state/hypothesis_registry.md` (H-01/H-02/H-03 + DEC-09-Nachtrag), `state/decisions.md` (DEC-01 – DEC-09), `state/state.md` (Phasen-Log + CHANGELOG), `FINAL_PRD.md` (§3 Welle 1, §4 Welle 2+, §6 REFUTED, §8 Multiple-Testing-Disziplin, §9 Betriebsmodell), `edge-reconciliation/results/verdict.md` (§1 Entscheidungsmatrix, §4 Welle-1-Auswahl), `handoff_local/results/upload_20260614/.../RECORDER_LONG.err.log` (8h-Recording-Volumina), `handoff_local/results/upload_20260615/.../recording_check.json` (aktueller Recording-Stand), `handoff_local/results/upload_20260615_cfar/cfar_20260615_120813/SUMMARY.md` (CFAR-Standalone-Lauf).*
