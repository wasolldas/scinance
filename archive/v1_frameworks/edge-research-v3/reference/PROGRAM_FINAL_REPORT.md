# Programm-Gesamtbericht — Scinance 2.0

**Branch:** `scinance2-wave2` (Welle 3 lief ohne eigenen Branch auf dem Welle-2-Endstand)
**Stand:** 2026-07-06
**Status:** Programm inhaltlich abgeschlossen — alle drei Wellen DONE, 13 vorregistrierte Gate-Verdikte entschieden
**Vorgänger-Berichte:** `WAVE1_FINAL_REPORT.md`, `WAVE2_FINAL_REPORT.md`, `WAVE3_FINAL_REPORT.md` (dieser Bericht steht für sich allein)

---

## 1. Executive Summary

Scinance 2.0 war eine dreiwellige Falsifikations-Pipeline (kein Live-Trading), die den Anspruch des Vorgänger-Portfolios Scinance 1.0 und ein Register externer Alpha-Claims systematisch gegen vorregistrierte, kapitalfreie bzw. friktions-konfrontierte Tore prüfte. Ergebnis über 13 vorregistrierte Gate-Verdikte (GL-001..GL-013): **9 DROP, 2 PARK, 2 kapitalfreie Mess-WEITER** — konkret die gerichtete BTC→ETH-Lead-Lag-Information (H-04) und das inverse OFI-Vorzeichen auf SOL-Kurzlags (H-05b). Beide Mess-WEITER endeten in der gleich-vorregistrierten Tradability-Prüfung (H-04b, H-05c) ehrlich auf **PARK**: der handelbare Brutto-Einfang lag 80-500× unter der 11-bps-Friction-Wand *(GL-009/GL-011)*. Bilanz: **0 handelbare Kanten, 0 Torpfosten-Verschiebungen** über 13 Verdikte *(gate_log.md GL-013 Programm-Bilanz)*.

Das Scinance-1.0-Portfolio (S1-S5) ist damit empirisch vollständig erledigt — jedes mit eigenem, vor dem Lauf fixiertem Tor *(WAVE1_FINAL_REPORT §4; gate_log.md GL-004 2026-06-13)*. Zwei reale Mikrostruktur-Signale wurden nachgewiesen und surrogat-/OOS-bestätigt — und im selben Atemzug als nicht handelbar widerlegt. Die zentrale methodische Innovation (Trennung Mess-Gate vs. Tradability-Gate) wurde zweimal repliziert; erstmals fiel ein Gate rein strukturell (mathematisch, ohne Datenlauf, GL-012). Nach Welle 3 ist die Pipeline **daten-gated, nicht arbeits-gated**: es existiert keine sofort registrierbare Alpha-Hypothese mehr, deren Blocker Arbeitszeit statt Daten-Reife wäre *(WAVE3_FINAL_REPORT §6)*. Passiv laufen C-36-Recorder und externer Harvester weiter; nächster natürlicher Programm-Termin ist der Sunset-Review ~2026-09-11.

---

## 2. Was das Programm war — Mission und Methode

Scinance 2.0 setzte das FINAL_PRD (die „Verfassung") im bestehenden Repo um: eine **Falsifikations-Pipeline statt Live-Trading** *(FINAL_PRD §6, CLAUDE.md §4)*. Es wurde grundsätzlich **kein Live-Order-Code** gebaut, kein Kapital eingesetzt; auch die nicht-kapitalfreien Tradability-Gates sind historische Backtests mit Kostenmodell auf read-only-Daten. Sechs methodische Säulen trugen das Programm:

- **(a) Hypothesen-Registry mit Pre-Registration.** Hypothese, Schwellwerte, Fenster und FDR-Familie werden VOR jedem Lauf wörtlich fixiert; der gate-auditor hat Veto gegen jeden Lauf ohne registrierten Eintrag *(hypothesis_registry.md Registry-Disziplin §1-3)*. Torpfosten-Verschiebung ist in BEIDE Richtungen verboten — weder darf eine Schwelle nachträglich erleichtert (WEITER erzwingen) noch erschwert werden (DROP erzwingen) *(GL-010 Disziplin-Frage 4)*.
- **(b) BH-FDR-Multiple-Testing je Familie.** Benjamini-Hochberg α=0.10 über jede Familie parallel getesteter Varianten; in Welle 2 zusätzlich eine zweistufige Über-Familie F-WAVE2 *(FINAL_PRD §8.2; hypothesis_registry.md Welle-2-Nachtrag)*.
- **(c) Hartes Ein-Fenster-DROP-Kriterium.** Schwelle in EINEM disjunkten Fenster verfehlt → DROP/PARK, kein Nachverhandeln, kein GRAUBEREICH (außer wo für H-01 explizit registriert) *(FINAL_PRD §8.5, Registry-Disziplin §6)*.
- **(d) Mess-Gate (kapitalfrei) vs. Tradability-Gate (Friction-Wand + Latenz) getrennt — die zentrale Innovation.** Ein Mess-WEITER heißt ausschließlich „Signal existiert messbar", NIE „handelbar". Handelbarkeit ist stets eine SEPARATE, nicht-kapitalfreie Folge-Hypothese (Muster H-0xb) mit verbindlicher 11-bps-Wand, 300-ms-Latenz-Haircut und Anti-Gaming-Klausel. Diese Trennung fängt den „S2-2023-Trap" ab — die Verwechslung von Signal-Existenz mit Handelbarkeit, die in Scinance 1.0 zur zirkulären Lesart „OFI hat Signal → OFI ist handelbar" führte *(GL-009, GL-011; hypothesis_registry.md H-04b Anti-Gaming-Klausel)*.
- **(e) Data-Snooping- und Forking-Paths-Guards.** Aus Daten geborene Hypothesen tragen einen Entdeckungszellen-Ausschluss plus OOS-Pflicht (H-05b); Konditionierungs-Suchen werden durch vorab gebundene Achsen neutralisiert (H-07/H-08) *(hypothesis_registry.md H-05b Entstehungs-Offenlegung; DEC-17/DEC-18)*.
- **(f) Schutzgüter.** Der laufende C-36-Recorder ist unantastbar (Schutzgut #1); Forensik-Tests bleiben unverändert; Bestands-Parquet und Audit-DuckDB sind read-only *(CLAUDE.md Schutzgüter; DEC-06)*.

Governance-Spur: 18 Architektur-Entscheidungen (DEC-01..DEC-18), alle reversibel mit dokumentiertem Rückbauweg protokolliert *(decisions.md)*.

---

## 3. Die drei Wellen chronologisch

### Welle 1 (Stand 2026-06-15) — das Fundament und drei DROP

Vier Pilots: E-15/S3 (H-01), C-42-Vol (H-02), C-31-CFAR (H-03), C-36-Recording (Infrastruktur). Alle drei Alpha-Hypothesen fielen; C-36 wurde als tragendes Fundament etabliert.

- **H-01 · S3-Pre-Settlement (iter-5).** Der bounded-loss-Fix wirkte mechanisch sauber (max Haltedauer 2124.9 s → 178.4 s, worst-trade −56.60 → −38.10 bps), rettete die Edge aber nicht: Netto −15.47 bps (unter der −10-bps-DROP-Schwelle), und die **RAW-Edge bei null Friktion bleibt −4.48 bps, auf allen 5 Symbolen negativ** (RAW −3.07..−5.65 bps). Der Entry hat keine Edge, der Exit war nur Symptom → DROP *(GL-004 2026-06-13)*.
- **H-02 · C-42-Vol-Anker.** Purged Walk-Forward (Purge 60 + Embargo 1440 Bars, 3 Folds), F-VOL über 36 Features. **0/5 Symbole bestehen** (min Fold-R² BTC −0.32 / BNB −0.53 / ETH −0.15 / SOL −0.08 / XRP −0.03, alle < 0.15), QLIKE schlägt HAR auf keinem Symbol in allen Folds, **0/36 Features FDR-signifikant**. Der dokumentierte Test-R²≈0.249 war ein L1-Selbstauskunfts-Artefakt → DROP *(GL-001)*.
- **H-03 · C-31-CFAR.** 4 unabhängige Fenster (BTC×2, ETH×2), Surrogate-p ∈ [0.801; 1.000] (deckungsgleich mit der Null), Edge 0.01-0.04 bps — **~250× unter der 11-bps-Wand**. Lead 100 ms > 50-ms-Schwelle, aber ökonomisch tot → DROP *(GL-005)*.
- **C-36 Recording (kein Alpha-Gate).** Als Infrastruktur pilotiert, F0-Recall-Gate ist ein 2-4-Wochen-Ziel und nicht fällig. Betriebsstand am Welle-1-Ende: rpi_orderbook ~5 Mio Zeilen, 0.076 GB / 50 GB Deckel *(GL-004 2026-06-12 Pilot-Statement; recording_check.json)*.

Kernbefund Welle 1: S3-Entry hat keine RAW-Edge, der Vol-Stack-Anker fällt (sperrt die gesamte Vol-Kaskade), die CFAR-Anomalie ist abgegrast.

### Welle 2 (Stand 2026-06-18) — der erste Nicht-DROP und seine Tradability-Widerlegung

- **H-04 · Cross-Sectional Lead-Lag (kapitalfrei) — WEITER.** Auf dem BTC/ETH-Perp-Paar (1s-Grid, 2 Fenster) ist gerichtete Information BTC→ETH FDR-signifikant: WCOH-Phasen-Lead p=0.0050 in beiden Fenstern, TE BTC→ETH signifikant auf Lags 1-3 s, Lead-Symbol stabil BTC, 12/22 F-LEADLAG-Survivor. **Erster nicht-trivialer Nicht-DROP des Programms** — aber ausdrücklich als kapitalfreies Mess-Gate; Kapital-Status PARK, Tradability = neue H-04b *(GL-006)*.
- **H-04b · Lead-Lag-Tradability (`capital_free=false`) — PARK.** Erste nicht-kapitalfreie Hypothese. Trading-Regel BTC-Signal → ETH-Position, 11-bps-Taker-Wand + 4 bps Slippage (~15 bps), 300-ms-Latenz-Haircut. PRIMARY-Block (19 603 Round-Trips): **Netto −14.95 / −14.83 bps, Bootstrap p=1.0000, 0 FDR-Survivor**; maximaler Brutto-Einfang +0.19 bps — **~80× unter der Wand**. Anti-Gaming respektiert (LAT100/LAT500/MAKER MIT-berichtet, kein WEITER erzwungen) → PARK *(GL-009)*.
- **H-05 · C-01 OFI-Vorzeichen (kapitalfrei) — DROP.** Kein Symbol/δ ist in beiden Fenstern FDR-signifikant positiv; BTC/ETH durchgängig negativ. **ETHUSDT w0 δ1s: corr −0.0550, p=0.0050 (FDR-sig, invers)** — die MM-Replenishment-Lesart, die INC-02/E-04 (das fälschlich invertierte S2-Vorzeichen) read-only reproduziert. Kaskaden-wirksamer DROP für C-01 + C-09-OFI-Bein + C-14-OFI-Erbe; der inverse Befund löst die Folge-Hypothese H-05b aus *(GL-007)*.
- **H-06 · C-07 Permutation Entropy (kapitalfrei) — DROP.** Das vorgeschaltete PRE-Gate ρ≥0.30 wird in ALLEN 10 Symbol×Fenster-Paaren verfehlt (max +0.0145, **~20× unter Schwelle**); zusätzlich Haupt-Gate-AUC-Lift +0.0072 (~4× zu klein), beide Survivor im selben Fenster → doppelt verfehlt *(GL-008)*.

Die Über-Familie F-WAVE2 (zweistufige BH-FDR über 17 Stage-1-Survivor) kippte **kein einziges Urteil** (0 Survivor in Stage 2 verloren) *(WAVE2_FINAL_REPORT §3)*.

### Welle 3 (Stand 2026-07-02) — Erschöpfung und die Harvester-Wende

Welle 3 lief erstmals vollständig auf dem **externen Datenharvester** (read-only Junction `data/harvest`, Backfill bis 2026-03-20) statt der Collector-DuckDB. Das ermöglichte echte **Pre-Discovery-OOS-Fenster** (April/Mai, per Datum fixiert) statt wochenlangem Warten auf Forward-Daten *(DEC-15)*.

- **H-05b · Inverses OFI OOS (kapitalfrei) — WEITER.** Konfirmatorischer Lauf auf April/Mai-Backfill (Entdeckungszelle ETHUSDT-Juni per Konstruktion ausgeschlossen). 16 FDR-signifikante Zellen (12 negativ / 4 positiv, p_crit 0.0199), davon genau **2 inverse-konsistent über beide Fenster: SOLUSDT δ1s und δ5s** (sign− beide Fenster, HR 0.4095-0.4605 ≤ 0.47). WEITER schmal und ehrlich dokumentiert: nur 1 Symbol, 2 Lags, Magnitude überwiegend über den sekundären Hit-Rate-Anker; das Entdeckungssymbol ETH trägt die Konfirmation selbst nicht → WEITER, Kapital PARK *(GL-010)*.
- **H-05c · OFI-Fade-Tradability (`capital_free=false`) — PARK.** Fade-Regel auf SOL-δ1s/δ5s. Alle 4 Zellen **Netto −14.97..−14.90 bps, Bootstrap p=1.0000, 0 FDR-Survivor**. Doppel-Aussage: Surrogate-p=0.0050 (die Fade-Richtung ist real, konsistent mit H-05b), aber Brutto-Einfang nur +0.031..+0.099 bps — **~150-500× unter der 15-bps-Wand**. Anti-Gaming respektiert → PARK *(GL-011)*.
- **H-07 · C-06 absolute Über-Dehnung (kapitalfrei) — DROP (strukturell).** Erstes rein mathematisches Verdikt des Programms, ohne Datenlauf: die Cross-Sectional-z-Statistik über N=5 Symbole ist hart beschränkt durch **max|z| = √(N−1) = 2.0** (Population) bzw. 1.79 (Sample) — beides unter der registrierten Schwelle 2.5 (für ein Top-20-Panel gesetzt, √19≈4.36). Achse A feuert nie → 0 konditionierte Events → der N-Floor (≥30/Fenster) reißt mit Sicherheit. Z_THRESH wurde NICHT abgesenkt; der DROP wurde angenommen, nicht umgangen *(GL-012)*.
- **H-08 · C-06 Rang-Über-Dehnung (kapitalfrei) — DROP (empirisch).** Schwellen-freie Rang-Definition (argmax|z| je Bar) — der einzige forking-paths-freie Ausweg. N-Floor erfüllt (501-508 Events/Fenster, Konstruktion feasible), aber **0 FDR-Survivor** (p 0.0796-0.9453), Nicht-Trivialitäts-Anker in allen 6 Zellen verfehlt; Fenster B (Mai) kollabiert (μ_rev(h6) = −0.8 bp, Momentum statt Reversion), während Fenster A (April, μ_rev +0.9/+2.2/+2.3 bp) schwach positiv war. Der vorregistrierte ≥2-Fenster-Survivorship-Guard sortierte den April-only-Effekt wie vorhergesagt aus → DROP. **C-06 damit dreifach geschlossen** (E-04-verboten / H-07 strukturell / H-08 empirisch) *(GL-013)*.

---

## 4. Gesamt-Verdikt-Tabelle (alle 13)

Hinweis zur GL-004-Doppelung: GL-004 trägt zwei getrennte Einträge — ein **Pilot-Statement** zu C-36 (2026-06-12, kein Alpha-Gate, Betriebsstatus) und ein **H-01-Verdikt** (2026-06-13, DROP). GL-002 und GL-003 sind PENDING-Einträge (Mess-Lücken durch Runner-Bugs), die durch die späteren Voll-Läufe GL-004/GL-005 abgelöst wurden und keine eigenständigen Alpha-Verdikte sind.

| Hypothese | Pilot / Signal | Familie | Urteil | GL | Ein-Satz-Grund |
|---|---|---|---|---|---|
| H-01 | S3 Pre-Settlement (E-15, iter-5) | F-S3 | DROP | GL-004 (2026-06-13) | RAW-Edge −4.48 bps, auf allen 5 Symbolen negativ — Entry hat keine Edge |
| H-02 | C-42 Vol-RV (LightGBM/HAR) | F-VOL | DROP | GL-001 | 0/5 Symbole, 0/36 Features FDR-sig — Vol-Stack-Anker fällt |
| H-03 | C-31 Cyclostationary CFAR | F-CFAR | DROP | GL-005 | p≈1.0 auf 4 Fenstern, Edge ~250× unter der 11-bps-Wand |
| (C-36) | Recording-Engine (Infrastruktur) | — | PILOT (kein Alpha-Gate) | GL-004 (2026-06-12) | ~5 Mio rpi-Zeilen, F0-Recall-Gate nicht fällig |
| H-04 | C-17/C-41 Lead-Lag (kapitalfrei) | F-LEADLAG | WEITER (Mess, Kapital PARK) | GL-006 | BTC→ETH-Info FDR-sig 1-3 s, Lead-Symbol stabil |
| H-04b | Lead-Lag-Tradability | F-LEADLAG-TRADE | PARK | GL-009 | Netto −14.9 bps, Einfang +0.19 bps, ~80× unter Wand |
| H-05 | C-01 OFI-Vorzeichen (kapitalfrei) | F-OFI | DROP (+ C-09/C-14) | GL-007 | keine positive ≥2-Fenster-Konsistenz; ETH invers sig |
| H-06 | C-07 Permutation Entropy (kapitalfrei) | F-ENTROPY | DROP | GL-008 | PRE-Gate ρ max +0.0145 (~20× unter 0.30) |
| H-05b | Inverses OFI OOS (kapitalfrei) | F-OFI-INV | WEITER (Mess, Kapital PARK) | GL-010 | SOL δ1s/δ5s sign− beide Fenster, OOS-konsistent |
| H-05c | OFI-Fade-Tradability | F-OFI-INV-TRADE | PARK | GL-011 | Netto −14.9 bps, Einfang +0.03..+0.10 bps, ~150-500× unter Wand |
| H-07 | C-06 absolute Über-Dehnung (kapitalfrei) | F-XMR | DROP (strukturell) | GL-012 | max|z|=√(N−1)=2.0 < 2.5 → N=0 garantiert |
| H-08 | C-06 Rang-Über-Dehnung (kapitalfrei) | F-XMR-RANK | DROP (empirisch) | GL-013 | 0 FDR-Survivor, CI-Anker in allen 6 Zellen verfehlt, Mai kollabiert |

Bilanz: **9 DROP · 2 PARK · 2 kapitalfreie Mess-WEITER · 0 handelbare Kanten · 0 Torpfosten-Verschiebungen** *(GL-013)*.

---

## 5. Die drei Kern-Erkenntnisse (was wir WISSEN)

### (a) Zwei reale Mikrostruktur-Signale existieren — und sind tot

Das Programm hat zwei echte Signale gefunden, beide surrogat-signifikant und beide OOS bzw. über zwei disjunkte Fenster reproduziert:

1. **Gerichtete BTC→ETH-Lead-Lag-Information auf 1-3 s** (H-04, WCOH p=0.0050 in beiden Fenstern, Lead-Symbol BTC stabil) *(GL-006)*.
2. **Inverses OFI-Vorzeichen / MM-Replenishment auf SOL-Kurzlags** (H-05b, SOL δ1s/δ5s sign− und FDR-sig in beiden OOS-Fenstern) *(GL-010)*.

Aber: beide liegen nach realistischem 300-ms-Latenz-Haircut **80-500× unter der 11-bps-Friction-Wand** — H-04b Brutto-Einfang max +0.19 bps *(GL-009)*, H-05c +0.03..+0.10 bps *(GL-011)*. Das ist kein diffuses Nullergebnis, sondern ein präzises: die Signale sind echt, gerichtet und nicht-zufällig (Surrogate-p 0.0050) — und ökonomisch tot. Genau diese Asymmetrie ist der A-priori der Verfassung („abgegraste 30-60s-HFT-Anomalie → PARK", FINAL_PRD §4 Z.133), hier zweimal empirisch reproduziert.

### (b) Das gesamte Scinance-1.0-Portfolio ist erledigt

Jede Strategie mit eigenem, vorregistriertem Tor widerlegt, kein Selbstbetrug *(WAVE1_FINAL_REPORT §4; gate_log.md)*:

- **S1** — ρ-Estimator gebrochen (C-14 REFUTED, ρ-Median ≈ 2e-7, sechs Größenordnungen unter Schwelle 0.85).
- **S2** — Richtung invertiert (drei Forensiken E-03/E-04/E-16; auf ETH read-only reproduziert, GL-007).
- **S3** — kein Entry-Edge (RAW −4.48 bps auf allen 5 Symbolen, GL-004).
- **S4/S5** — nie tragfähig (Loader-/Panel-Harness-Lücken, E-13/E-14).
- **Vol-Stack** — Anker-DROP (H-02, GL-001), sperrt die gesamte Kaskade.
- **CFAR** — abgegrast (H-03 ~250× unter Wand, GL-005).
- **OFI-Komplex** — vollständig erschöpft: positiv DROP (H-05), invers Mess-WEITER (H-05b), invers-Tradability PARK (H-05c); kein H-05d *(GL-011)*.
- **C-06** — dreifach geschlossen (E-04 / H-07 / H-08); kein H-08b/H-09 *(GL-013)*.

### (c) Die Methode selbst ist das Ergebnis

- **Mess-vs-Tradability-Trennung zweimal repliziert:** H-04→H-04b und H-05b→H-05c fangen beide den S2-2023-Trap ab; beide mit Anti-Gaming-Klausel und MIT-berichteter Robustheits-Spanne (LAT100/LAT500/MAKER), keine drehte das PARK *(GL-009, GL-011)*.
- **Erster struktureller A-priori-DROP:** H-07 fiel aus einer beweisbaren Eigenschaft von (Gate, Panel) statt aus einem Datenlauf — Mathematik statt Rechenlauf, ohne Torpfosten-Schub *(GL-012)*.
- **Data-Snooping- und Forking-Paths-Guards nachweislich wirksam:** der Entdeckungszellen-Ausschluss (H-05b, ETH-Juni konstruktiv nie berührt) und der Survivorship-Guard (H-08, Mai-Kollaps sortierte den April-only-Effekt aus) griffen jeweils genau wie vorregistriert *(GL-010, GL-013)*.
- **0 Torpfosten-Verschiebungen über 13 Verdikte** — die Disziplin hielt in beide Richtungen (weder WEITER noch DROP wurde je durch Schwellen-Anpassung erzwungen).

---

## 6. Was gebaut wurde — Infrastruktur und Werkzeug-Erbe

- **C-36 Recording-Engine** (Schutzgut #1): additiv neben dem Collector, eigene Tabellen/Parquet-Pfad, 50-GB-Ringpuffer *(DEC-06/DEC-07)*. Stand Welle-3-Ende **rpi_orderbook > 102 Mio Zeilen** (102 167 231), Autostart via Task Scheduler + Single-Instance-Guard gegen Doppel-Writer *(wave2_state.md RECORDER-OPS)*. Dokumentierter Dedup-Caveat 2026-06-23..06-27 (zeitweise zwei Recorder).
- **research/-Module** (alle standalone, read-only, per Verzeichnis-Löschung rückbaubar): `e15_eval`, `c42_rv` (36 Features, purged-WF, FDR/BH, QLIKE, LightGBM-Adapter), `c31_cfar`, `c17_c41_lead_lag`, `c17_c41_tradability`, `c01_ofi_sign` (+`oos.py`), `c01_ofi_tradability`, `c07_pe`, `c06_xmr` *(CLEANUP_PLAN.md; WAVE3_FINAL_REPORT §5)*.
- **Harvester-Anschluss:** read-only Junction `data/harvest` (Hive-Tree bybit/publicTrade + Binance + Deribit-IV), `harvest_coverage.py`, Loader-Adapter `load_harvest_window`; ersetzt funktional den Scinance-1.0-Collector *(DEC-14/DEC-15)*.
- **Test-Suite:** 616 → 752 (Welle 1) → 908 (Welle 2) → **≈957 grün** (Welle 3), Forensik-Tests durchgängig unangetastet, 0 Modul-Bugs zur Gate-Laufzeit *(WAVE1/2/3 §7)*.
- **T2/T3-Runner-Familie:** `run_short/run_overnight/run_cfar_only`, `run_wave2/run_h04b`, `run_h05b_oos/run_h05c/run_h08` (Ein-Befehl, `--db-copy`, Tick-Cap, Per-Step-Timeout, try/except je Schritt) *(WAVE1/2/3 §5)*.
- **Repo-Cleanup & Audit-Freeze:** `CLEANUP_PLAN.md` (378 Zeilen, 19 KEEP / 21 DEPRECATE / 2 REMOVE / 3 REPLACE, 16 TODOs, 22 DEPRECATE-Header-Marker); Scinance-1.0-Live-Stack (live_runner, multi_runner, Pipeline, S1-S5, Dashboard, Backtester, Executor) DEPRECATE; `bybit_edge.duckdb` (1 048 326 144 Bytes ≈ 1.0 GB, SHA-256 22EE0451…F087902) als read-only Audit-Bestand eingefroren *(DEC-14; wave2_state.md CLEANUP/AUDIT-FREEZE)*.
- **Größenordnung Produktion:** ~5 000 LoC Welle 1 + ~6 200 LoC Welle 2 + ~2 300 LoC Welle 3 ≈ **~13 500 LoC**; 18 DEC-Entscheidungen als Architektur-Audit-Trail *(CLEANUP_PLAN.md §0; WAVE1/2/3 §7)*.

---

## 7. Was NICHT umgesetzt wurde und warum

**(1) Daten-gated (warten auf Datenreife, kein Arbeits-Blocker).** C-20 MOMENT Zero-Shot braucht frische Bybit-Neulistings (N=10-20, Wochen-Monate Vorlauf); C-27/C-28/C-29 + C-39/CS-06 brauchen ≥30 Kaskaden Recording-Vorlauf (insurance_pool ~7 Events/h → C-29 ca. Anfang Aug. 2026, C-27/28 ca. Sept.-Okt. 2026); C-33 VRP braucht ≥12 Monate IV-Recording + Stress-Periode (option_tickers-NO_DATA-Defekt offen) → frühestens Mitte 2027 *(wave3_survey.md §3, WAVE3_FINAL_REPORT §6)*.

**(2) Kaskaden-blockiert (durch einen Welle-1/2-DROP versperrt).** Der gesamte Vol-Stack (C-10/C-11/C-12/C-34/C-35 + VRP-RV-Bein) bleibt durch H-02-DROP ohne Anker gesperrt — Reaktivierung nur über eine neue H-02b mit bit-genauer Original-Feature-Spec (Außen-Arbeit). Ebenso C-08 (BOCPD, Ockham-tot nach H-01), C-37/CS-12 (kein Graubereich), CS-07-C-31-Bein (H-03-DROP), C-25 (zirkulär — braucht positive Basis-Strategie, existiert nicht) *(WAVE1_FINAL_REPORT §6; wave3_survey.md §1)*.

**(3) Bewusst nie gebaut per Verfassung.** Live-Order-Code (grundsätzlich, FINAL_PRD §6 / CLAUDE.md §4); die Tradability-Nachfolger H-04c/H-05d/H-07b/H-08b (nicht registriert, durch die PARK/DROP NICHT nahegelegt); C-40 RPI ausschließlich als Forschungs-/Sicherungs-Asset, KEIN Alpha-Gate (selbstzerstörender Edge) *(GL-011/GL-013; wave3_survey.md §2.4)*.

**(4) Gestundete Ops-TODOs.** Endgültige Legacy-Löschung (DEPRECATE-Marker gesetzt, physische Entfernung offen); DuckDB→Harvester-Umstellung als operativer Schnitt (strukturell vollzogen, Rest-TODOs sequenziell offen); der Branch `scinance2-wave3` wurde nie abgezweigt (Welle 3 lief auf dem Welle-2-Endstand); die zwei Reparatur-WPs option_tickers-Keepalive und adl_alerts-Bybit-Topic-Klärung *(DEC-14 Akteur-Verteilung; wave3_survey.md §6)*.

---

## 8. Aktueller Zustand und Ausblick

Das Programm ist sauber abgeschlossen; alle Verdikte, Registry-Einträge, DEC-Entscheidungen und Roh-Daten-Verzeichnisse sind auf `scinance2-wave2` gepusht, jedes Verdikt bleibt gegen sein Roh-JSON reproduzierbar. Passiv laufen weiter und werden mit der Zeit wertvoller: der **C-36-Recorder** (Autostart + Single-Instance-Guard) und der **Harvester** (inkl. Deribit-Options-IV, der langfristig den C-33-Vorlauf entsperrt) *(WAVE3_FINAL_REPORT §3/§6)*.

Der entscheidende Zustandswechsel: die Pipeline ist **daten-gated, nicht arbeits-gated** — es gibt keine sofort lauffähige, ehrlich registrierbare Alpha-Hypothese mehr, deren Blocker Arbeitszeit wäre. Die natürlichen Wecker sind:

| Wecker | Bedingung | Horizont |
|---|---|---|
| Bybit-Neulisting | N=10-20 frische Perp-Symbole (C-20) | Wochen-Monate |
| 30-Kaskaden-Schwelle | insurance-Recording-Vorlauf (C-27/28/29) | Aug.-Okt. 2026 |
| Sunset-Review | 3 Monate nach Recording-Start (Anti-Data-Lake-Bremse) | ~2026-09-11 |
| IV-Historie | ≥12 Monate Deribit-IV + Stress (C-33) | ~Mitte 2027 |

**Empfehlungen:**

- **Keine Welle 4 auf Vorrat.** Alle verbliebenen Pfade sind daten-gated; bis zum Sunset-Review nur passives Sammeln plus die zwei Reparatur-WPs. Keine Hypothese erfinden, um beschäftigt zu sein *(WAVE3_FINAL_REPORT §8)*.
- **Feasibility-Check als Pflicht vor jeder Pre-Registration (GL-012-Lehre).** Prüfe VOR dem Lauf mathematisch, ob die registrierte Schwelle auf der verfügbaren Datenbasis überhaupt erreichbar ist — ein struktureller DROP ist billiger und ehrlicher als ein leerer Datenlauf.
- **Pre-Discovery-OOS als Standard** für jede aus Daten geborene Folge-Hypothese: temporal unabhängiger Backfill, Entdeckungszellen-Ausschluss per Konstruktion — dem Forward-Warten methodisch und operativ überlegen *(DEC-15)*.
- **Mess-Gate/Tradability-Gate-Trennung bleibt Verfassungsrang;** keine Reaktivierung gefallener Pilots ohne neue H-0xb-Zeile; Torpfosten-Verschiebung bleibt in beide Richtungen verboten.
- **Ehrliche Erwartung an die daten-gated Pilots:** die A-priori-Skepsis (13 Verdikte, 0 handelbare Kanten) gilt unverändert — es sind Falsifikationstests mit erwartetem DROP, keine Hoffnungsträger. Das Programm misst seinen Wert in sauberen Verdikten, nicht in Überlebenden.

---

*Quellen durchgängig: `scinance2-impl/state/gate_log.md` (GL-001..GL-013 inkl. GL-004-Doppelung Pilot-Statement 2026-06-12 + H-01-Verdikt 2026-06-13, GL-002/003 PENDING-abgelöst, Programm-Bilanzen GL-011/012/013), `state/hypothesis_registry.md` (H-01..H-08 inkl. H-04b/H-05b/H-05c + WP-0-/Struktur-Nachträge, Registry-Disziplin §1-8, Welle-2-Nachtrag), `state/decisions.md` (DEC-01..DEC-18), `state/WAVE1_FINAL_REPORT.md`, `state/WAVE2_FINAL_REPORT.md`, `state/WAVE3_FINAL_REPORT.md`, `state/wave3_survey.md` (§1-6 Pilot-Universum/Reife/Sequenzierung), `state/CLEANUP_PLAN.md` (Inventar, Audit-Freeze), `state/wave2_state.md` (CHANGELOG, RECORDER-OPS, AUDIT-FREEZE), `FINAL_PRD.md` (§3 Welle 1, §4 Welle 2+ Z.129/130/131/133, §6 REFUTED, §8 Multiple-Testing, §9 Betriebsmodell), `handoff_local/results/{upload_20260615/.../recording_check.json, wave2_20260617_090618/WAVE2_SUMMARY.md, h04b_20260618_091937/, h05b_oos_20260630_091035/, h05c_20260701_153543/, h08_20260702_085014/}`. Wo Einzelberichte und gate_log leicht abweichen, gilt gate_log (die Verdikte sind die Wahrheit).*
