# FINAL_PRD — Scinance 2.0

**Phase:** 6 — PRD
**Stand:** 2026-06-11
**Erstellt von:** prd-architect
**Maßgebliche Quellen:** `verdict.md` (Entscheidungsmatrix, bindend), `alignment_matrix.md` (Evidenzstatus), `claims_register.md` (Claim-/ID-Mapping), `evidence_register.md` (E-01..E-18, GM-1..6, Kostenbaseline), `repo_map.md` (Ist-Zustand Scinance 1.0).

> **Rückführbarkeit ist oberstes Gebot.** Jede Aussage in diesem Dokument trägt die IDs der Befunde, auf denen sie steht (C-xx Module/Strategien, E-xx Evidenz, GM-x globale Methoden-Vorbehalte, A-x/S-x Debatten-Punkte aus verdict.md). Es kommt nichts „aus dem Nichts" ins Framework, und kein Urteil wird stillschweigend weggelassen. Wer dieses PRD liest, soll ohne die Debatten verstehen, **was** zu tun ist und **warum**.

---

## 1. Executive Summary

**Was Scinance 2.0 IST:** ein **Edge-Forschungssystem mit Falsifikations-Pipeline**. Sein Daseinszweck ist nicht, möglichst viele Strategien live zu schalten, sondern Hypothesen mit messbaren Gates und harten Abbruchkriterien systematisch zu **widerlegen oder zu härten**, bevor Kapital riskiert wird. Der zentrale Output ist nicht „ein Bot, der handelt", sondern „ein Register von Edges mit bekanntem Validierungsstand".

**Was Scinance 2.0 NICHT mehr ist:** ein **5-Strategien-Trading-Bot** (S1–S5), der parallel feuert. Genau dieses Selbstbild von Scinance 1.0 ist gescheitert: Von den fünf Strategien sind zwei forensisch **REFUTED** (CS-01/S1, CS-02/S2), zwei nie ausgeführt worden (CS-04/S4, CS-05/S5 — reine Infrastruktur-Lücken, E-13/E-14), und eine hängt an einem laufenden Bug-Fix-Run (CS-03/S3, E-15 PENDING).

**Die nicht verhandelbare Konsequenz der Evidenzlage:** Das gesamte Evidence-Register ist **L0** (in-sample, Single-Pass, ~24h-Fenster; GM-1). Kein einziger Befund ist out-of-sample oder live validiert. Damit ist **CONFIRMED praktisch unerreichbar** und es gibt in diesem PRD **kein einziges ADOPT für einen Alpha-Claim** (verdict §0.1, §8). Das Maximalurteil ohne neue Validierung ist **PILOT**. Das ist keine Vorsicht, sondern direkte Folge davon, dass nichts sauber validiert wurde.

**Die Friction-Wand (Kernrelation, verdict §0.2):** Round-Trip-Friktion **11 bps** (Taker) bzw. **~15 bps** inkl. Slippage übersteigt **jede** bisher gemessene Roh-Edge (max |Roh| ≈ 4–7 bps). Friktion > Signal auf JEDER gemessenen Strategie. Jeder Edge-PILOT in Scinance 2.0 muss explizit zeigen, **wie** er diese Wand umgeht: längerer Horizont, Maker-Execution, Friktionsersparnis durch Filterung, oder nicht-direktionale Prämie.

**Stoßrichtung:** Vier parallele Welle-1-Pilots, davon nur **einer** ein echter neuer Alpha-Test (C-31 CFAR); die übrigen drei sind Infrastruktur/Reproduktion (E-15-Auswertung, C-42-Reproduktion, C-36-Recording). Alles Weitere ist sequenziert hinter harten Vorbedingungen. Drei Befunde sind als tote Pferde markiert und dürfen nie wieder geritten werden (C-14, CS-01, CS-02).

**Markt-Muster (verdict §8):** Spot ist durchgehend mechanismuslos (DROP, außer C-42-RV/C-23-Basis als PARK). Optionen sind DROP außer dem einen VRP-PILOT (C-33). **Alle echten Pilots sind Futures-Perpetuals** (plus C-42 auf Spot/RV, C-33 auf Optionen).

---

## 2. Lehren aus Scinance 1.0

Diese fünf Lehren sind die empirische Grundlage des Umbaus. Sie sind der Grund, warum Scinance 2.0 ein Falsifikationssystem ist und kein Bot-Portfolio.

### 2.1 Die drei REFUTED-Forensikketten

- **C-14 / CS-01 (Hawkes-ρ-Kaskaden-Detektor, S1):** Der importierte Kritikalitäts-Schwellwert ρ>0.85 (aus fremder Mikrostruktur, INC-01) wird auf Bybit **strukturell nie erreicht**. E-01 misst über alle 5 Symbole (56k–87k Ticks) einen ρ-Median ≈ 2e-7 — **sechs Größenordnungen** unter der Schwelle. Folge: S1 feuert 0 Trades, Ursache `rho_below_threshold`, nicht Datenmangel (E-02; Liquidationen waren auf 4/5 Symbolen reichlich da). **Schwelle und Single-Channel-Estimator sind REFUTED.** Lehre: ein importierter theoretischer Threshold ohne Erreichbarkeits-Check ist wertlos.

- **CS-02 (Entropie-Momentum, S2):** Drei unabhängige Forensiken aus GEEIGNETEN Fenstern widerlegen die Strategie. (1) E-03 (Maker-Only, schärfster Test): Roh-Edge negativ auf JEDEM Symbol auch bei 0 Fees (-3.45 bps Aggregat). (2) E-04 (Mirror-Test): hit_sum 0.179 ≠ 1.0; Inversion macht es schlimmer (-4.55) → das Signal ist **execution-loss-bound**, kein invertierbares Anti-Signal. (3) E-16: Friktion dominiert Richtung ~35×. Lehre: ein Signal, das auch ohne Fees verliert und sich nicht invertieren lässt, ist Rauschen.

- **CS-01-/CS-02-Differenzierung (Modul ≠ Strategie):** Eine gescheiterte Strategie widerlegt nur die Module, deren Versagen forensisch isoliert ist. Aus CS-01 ist **nur** C-14 REFUTED; C-15/C-26 bleiben SUSPECT (ρ-Gate blockierte ihre Auslösung). Aus CS-02 ist **kein** Modul automatisch REFUTED: C-06 bleibt PARTIAL (Gate feuert messbar, E-05), C-01/C-07 bleiben SUSPECT. Diese Disziplin verhindert, dass nützliche Bausteine mit gescheiterten Integrationen mitsterben.

### 2.2 Die L0-Decke (GM-1)

Jede Messung in Scinance 1.0 stammt aus einem `single_pass`-Replay über **ein** ~24h-Fenster pro Symbol. Kein Train/Test-Split (L1), kein Walk-Forward (L2), kein Live (L3). 17 Befunde L0 + 1 PENDING. **Kein L0-Befund kann je auf CONFIRMED heben.** Hinzu kommt GM-6: 24h enthalten nur 3 Settlement-Zyklen/Symbol und keine garantierte Stress-Episode — das Fenster kann Kaskaden-/Settlement-Claims nicht falsifizieren, nur Nicht-Feuern zeigen. Lehre: Scinance 2.0 misst gegen disjunkte Out-of-Sample-Fenster mit Stress-Anteil, nicht gegen ein einzelnes Tagesfenster.

### 2.3 Die Friction-Wand

Siehe §1. Die Kernrelation (Kostenbaseline aus evidence_register) ist die härteste Realität des gesamten Registers: 11/15 bps Friktion > 4–7 bps Roh-Edge. Sie ist der Grund, warum der einzige dokumentierte Friktions-Hebel (C-37 Spread-Markt, ~4 statt 11 bps) und nicht-direktionale Prämien (C-33 VRP) eine Sonderrolle erhalten.

### 2.4 Die S4/S5-Infrastruktur-Falle

S4 (CS-04) feuerte 0 Trades wegen `insufficient_models` 96–99.99 % — der Modell-Loader war nie verdrahtet (E-13). S5 (CS-05) feuerte 0 Trades wegen `single_symbol_replay_unsupported` 100 % — der Single-Symbol-Replayer kann Cross-Sectional-Logik prinzipiell nicht ausführen (E-14). Beides sind **Mess-Lücken, keine Niederlagen**: mehr Daten helfen nicht, nur Code/Harness. Lehre: aufwändige Multi-Modell-/Panel-Infrastruktur zu bauen, bevor das Basissignal validiert ist, ist die teuerste Form, nichts zu lernen. Deshalb ist der Panel-Harness in Scinance 2.0 **explizit nicht** in Welle 1 (verdict §4, crosssect S-5).

---

## 3. Welle-1-Programm

**Prinzip (verdict §4):** Max. 3–5 Pilots parallel (Einzelbetreiber-Realismus). Welle 1 = **4 Hypothesen-Gates**, davon 3 Infrastruktur/Reproduktion und nur **1 echter neuer Alpha-Test** (C-31). Drei nicht verhandelbare Sequenzierungs-Zwänge ordnen alles Weitere:

- **E-15-Resultat VOR allen S3-Folgeentscheidungen** (CS-03, C-22-Exit, C-08-Ockham-Test, RV-Stop, Vol-Targeting).
- **C-42-Reproduktion VOR allen Vol-Stack-Derivaten** (C-10, C-35, C-34, C-11/C-12-ΔR²-Gates messen sonst gegen ein Phantom).
- **Recording-Start (C-36) VOR allen recording-abhängigen Pilots** (C-39, C-40, C-33-Options, C-02, IV-Surface).

### Pilot 1 — E-15-Auswertung (CS-03 / C-22), bereits laufend

- **Markt-Zuordnung:** Futures (Perp). Spot/Optionen kein Mechanismus.
- **Benötigte Datenströme:** keine neuen — iter-5-Run läuft auf vorhandenen Replay-Daten; zusätzlich Roh-PnL-Export beider Runs (iter-3/iter-4) zur Auflösung des E-17-Widerspruchs.
- **Status/Begründung:** Einzige real feuernde Strategie (N=213) mit forensisch lokalisiertem, reparierbarem Verlust (Time-Stop-Bug E-07, friction-unbewusster Hard-Stop E-08). Höchste Evidenznähe, kein Neu-Aufwand.

**Die bedingten E-15-Tore (wörtlich aus verdict §3 übernommen):**

> **Gate 1 (E-15-Resultat, erstes Tor):** iter-5 liefert die in E-15 erwarteten Deltas: time_stop 1→60–70, n>120s 68→~0, n<-30bps 33→~0.
>
> **→ PILOT-fortführen (Richtung ADOPT-Kandidatur), falls** iter-5 mean pnl_bps netto **≥ -5** (signifikante Hebung der -16.81) UND E-17-Widerspruch (iter-3 -2113$ vs iter-4 -6857$) durch Roh-PnL-Export beider Runs aufgelöst. Erst dann Folge-Gate: PRD-kestrel-Schwelle **Sharpe ≥ 1.2 / WR ≥ 55 % / PF ≥ 1.3 über ≥ 200 Trades walk-forward (≥L2)**.
>
> **→ DROP/PRD-Redesign, falls** iter-5 mean pnl_bps netto **bleibt ≤ -10** ODER der Bug-Fix die Tail-/Time-Stop-Metriken nicht wie erwartet bewegt (Time-Stop feuert weiterhin <10×). Dann ist die negative Roh-Edge (-5.8 bps) NICHT exit-, sondern entry-/edge-knappheits-bedingt bestätigt → CS-03 fällt.
>
> **Graubereich (-10 < netto < -5):** PILOT bleibt, aber nur gekoppelt an C-37-Friktions-Hebel — ohne 7-bps-Friktionssenkung strukturell nicht heilbar.

- **C-22 (Entry) — PILOT unabhängig vom CS-03-Exit:** settlement-event-gebundener (`n_settlement_events`, nicht `n_in_window`) Isolationstest, Pressure-Threshold Q97/Q99, FDR-korr. über Quantil-Varianten. **Erfolgsmaß:** Roh-Edge > 0 vor Friktion auf ≥ 3 Symbolen. **Abbruch:** scheitert → INC-03-Edge-Knappheit bestätigt, C-22 DROP.
- **Abhängigkeiten/Sequenzierung:** blockiert C-37, CS-12, C-08, RV-Stop, Vol-Targeting. Muss zuerst auswerten.

### Pilot 2 — C-42-Reproduktion (LightGBM/HAR-RV)

- **Markt-Zuordnung:** Futures (PILOT) + Spot (PILOT für RV-Ziel); Optionen PARK (RV ist nur halbe VRP-Gleichung, IV fehlt).
- **Benötigte Datenströme:** Kline-Backfill (vorhanden); keine neue Aufzeichnung.
- **Begründung:** Einziger positiver OOS-Befund des Registers (Test-R² 0.249, research_notes), aber L1-Selbstauskunft, kein E-xx aus dieser Pipeline, keine FDR über 36 Features (C-42 PARTIAL, volstack S-1). Reproduktion ist Pflicht-Vorbedingung des **gesamten** Vol-Stacks — alle ΔR²-Gates (C-10/C-35/C-11/C-12/C-34) messen sonst gegen ein Phantom (verdict §7).
- **Testdesign:** purged Walk-Forward (≥ L2), ≥ 2 disjunkte OOS-Fenster, FDR (Benjamini-Hochberg α=0.10) über die 36 Features.
- **Validierungs-Gate:** **OOS-R² ≥ 0.15** UND QLIKE schlägt naive HAR-RV-Baseline.
- **Abbruchkriterium:** OOS-R² < 0.15 in einem Fenster ODER HAR-RV nicht geschlagen → der gesamte Vol-Stack verliert seinen Anker, C-42 fällt auf PARK/DROP, alle abhängigen Vol-Module bleiben gesperrt.
- **Sequenzierung:** schaltet bei Erfolg C-10/C-35/C-11/C-12/C-34/VRP-RV-Bein frei (Welle 2).

### Pilot 3 — C-36 Recording-Engine (gedeckelt)

- **Markt-Zuordnung:** Futures (PILOT, Prio-1-Infra) + Spot (PILOT); Optionen PARK (IV-Recorder als Sub-Komponente, an C-33 gekoppelt).
- **Benötigte Datenströme (neu aufzuzeichnen, repo_map §5):** `orderbook.rpi` (100ms, First-Mover-Dataset), `insurance.USDT` (1s), `adlAlert` (1s), Premium-Index-Kline (REST), Options-Tickers (IV/Greeks). Bestehender Collector deckt tickers/allLiquidation/orderbook/publicTrade ab.
- **Begründung:** Kein Alpha, aber höchster Infrastruktur-Hebel — macht ALLE recording-abhängigen Claims (C-39, C-40, C-33-IV, C-02, IV-Surface) erst testbar (verdict §7). Zeitkritisch: ohne Vorlauf bleiben Cascade-/Options-Pilots datenleer.
- **Gefahr und Gegenmaßnahme (microstr S-A1):** „hypothesenfrei nützlich" = Risiko eines unbegrenzten Data-Lake ohne Abbruch. Deshalb **KEIN ADOPT, sondern gedeckelter PILOT**.
- **Validierungs-Gate:** **F0-Recall ≥ 95 %** innerhalb 2–4 Wochen (deterministisches Perzentil-Regelwerk; dient zugleich als Benchmark für C-02).
- **Abbruchkriterium / Deckel:** harter **Storage-Deckel** (fixe GB-Obergrenze, ringpuffer-/rotationsbasiert) + **Sunset-Review nach 3 Monaten** (siehe §9): liefert ein recording-abhängiger Pilot bis dahin kein Gate-relevantes Ergebnis, wird der zugehörige Stream abgeschaltet.
- **Sequenzierung:** Recorder läuft passiv parallel; Vorbedingung für alle Welle-2/2+-Recording-Pilots.

### Pilot 4 — C-31 Cyclostationary CFAR (der EINZIGE neue Alpha-Test in Welle 1)

- **Markt-Zuordnung:** Futures (PILOT, priorisiert). Spot/Optionen DROP (kein Mechanismus).
- **Benötigte Datenströme:** publicTrade WS (#8), Inter-Arrival-Zeiten der Trades. Kein Tiefen-Stream, keine Aufzeichnung nötig.
- **Begründung:** Einziges billiges, eigenständiges, friktions-ehrliches, basis-unabhängiges Falsifikations-Gate des Regime-Clusters mit eingebauter Falsch-Alarm-Kontrolle (CFAR; regime S-A3). Schnell DROP-bar.
- **Testdesign:** Surrogate-Test (geshuffelte Inter-Arrivals) gegen das gemessene Cyclic Spectrum; Lead-Zeit- und Edge-Messung in ≥ 2 disjunkten Fenstern.
- **Validierungs-Gate:** **Surrogate p ≤ 0.05** in ≥ 2 Fenstern UND **Lead-Zeit > 50 ms** (über Retail-Latenz) UND **Edge > 11 bps** (über der Friction-Wand).
- **Abbruchkriterium:** p > 0.05 ODER Lead-Zeit < 50 ms ODER Edge ≤ 11 bps in einem Fenster → DROP (adaptiver Gegner / abgegraste HFT-Anomalie, Hauptrisiko laut Quelle).
- **Sequenzierung:** standalone; Vorbedingung (zusammen mit C-16) für CS-07-Footprint-Detektor in Welle 2+.

**Begründung der Auswahl gegen Alternativen (verdict §4):** C-31 vor C-16 (C-16 datenhungriger, 5y-Bibliothek). C-42-Repro vor allen Vol-Modulen. Recording vor Cascade/Options-Pilots. Cross-Sectional-Panel-Harness explizit NICHT in Welle 1 (S4/S5-Falle, Fee-Verdopplung, abgegraste Anomalie).

---

## 4. Welle-2+-Programm (sequenziert)

Jeder Eintrag startet erst, wenn seine Vorbedingung aus Welle 1 erfüllt ist (verdict §4 „Welle 2"). Gates und Abbruchkriterien aus claims_register/verdict.

| Pilot | Markt | Vorbedingung (Unlock) | Validierungs-Gate | Abbruchkriterium |
|---|---|---|---|---|
| **C-10** MF-DFA/Hölder | F (S) | nach C-42-Reproduktion | inkrementelles **ΔR² ≥ +0.02** über reproduzierte C-42-Baseline | ΔR² < +0.02 → DROP (Anti-S1: kein Feature ohne Mehrwert) |
| **C-35** CEEMDAN | F (S) | nach C-42-Reproduktion | **Lookahead-KILL-Gate** (bit-für-bit-Kausalität) VOR ΔR²; dann ΔR² ≥ +0.02 | Kausalitäts-Leak ODER ΔR² < +0.02 → DROP |
| **C-08** BOCPD (Ockham-Test) | F | nach E-15 | muss gegen trivialen Time-Stop (`if elapsed>120s: exit`) antreten und den E-10-Tail messbar besser schneiden | Time-Stop schneidet Tail bereits → C-08 überflüssig (Ockham), PARK/DROP |
| **C-27 + C-28** (= EIN Test, geteilter ω_s-Kernel) | F | Recording-Vorlauf (Bulk-Historie ≥ 30 Kaskaden) + ω_s-Stabilitäts-Test + E-01-analoger Distributions-Check auf Intervall-Untergrenze | C-27: **BA ≥ 0.55 OOS** in ≥ 2 disjunkten Fenstern + Brier < Volumen-Baseline. C-28: **Lift ≥ 1.2 OOS** + NB p < 0.05 LR-Test | C-27: BA ≤ 0.55 in einem Fenster → DROP. C-28: Lift ≤ 1.2 ODER p ≥ 0.05 → DROP |
| **C-29** Avalanche Shape-Collapse (eigenständig) | F | Recording-Vorlauf | muss reparierten Time-Stop (E-15) UND simplen Hazard schlagen; **Collapse-Residual ≤ 30 %** + Restdauer-MAE < Konstant-Mittel | Residual > 30 % ODER MAE nicht besser → DROP |
| **CS-06** Kaskaden-Cockpit (= C-27+C-28+C-29+C-43) | F | nach Validierung von C-27/C-28/C-29 | sauberster Cascade-Pilot ohne REFUTED/SUSPECT-Modul; Gate = Summe der Modul-Gates | Modul-Gate gerissen → entsprechendes Glied fällt |
| **C-33** VRP / Short-Vola | **O** | **nach ≥ 12-Mon.-Recording mit ≥ 1 Stress-Periode** (NICHT 3 Mon.; Peso-Verzerrung) + Netto-Roll-Gate + Tail-Cap-Klausel | **(IV − RV) ≥ 3 %** im 12-Mon.-OOS in ≥ 2 Fenstern, ernterbar nach Hedging-Kosten | < 3 % in einem Fenster ODER Liquidität unzureichend (60–80 % illiquide Stunden) → DROP |
| **C-37** Spread-Execution | F | nach E-15 (nur falls CS-03 in Graubereich) | Live-Mikro-Pilot über `/v5/spread/*`: **Maker-Quote ≥ 70 %** UND realisierter Round-Trip **≤ 6 bps** SPEZIELL in Pressure-Release-Fenstern | verfehlt → C-37 DROP, Funding-Cluster bleibt friction-bound |
| **C-06** (NICHT-triviale MR) | F | nach Welle 1 | FDR-korrigiertes Gate für separates Folge-Signal (simple Sign-Flip-MR durch E-04 bereits widerlegt) | trivial-MR-Lesart verboten; ohne neue Hypothese kein PILOT |
| **C-07** Permutation Entropy (billigster Lottoschein) | F | ρ-Vorprüfung ≥ 0.3 (m/τ vorab fixiert) | bedingte AUC-Lift in G1-Fenstern; nur Kline, kein Tiefen-Stream | ρ < 0.3 → DROP |
| **C-01** OFI | F | **erst nach INC-02-Vorzeichen-Test** (Reihenfolge nicht verhandelbar) | Vorzeichen-Test ZUERST: markiert OFI-Vorzeichen Aggression oder MM-Replenishment? | scheitert Vorzeichen-Test → DROP für C-01 und C-09/C-14-OFI-Erbe |
| **C-20** MOMENT (nur Zero-Shot-Neulisting) | F | nach Welle 1 | RV-Zero-Shot auf neu gelistete Symbole ohne Lookback; MASE < 1.0 | sonst DROP (kein verlorener HAR-Vergleich) |
| **Cross-Sectional 2-Symbol-Mess-Gate** (C-17/C-41) | F | nach Welle 1 (E-15/C-42), **kapitalfrei** | NUR Lead-Lag-Existenz prüfen, kein Kapitaleinsatz; Multiple-Testing über Konditionierungen FDR-korr. | keine handelbare Kante (abgegraste 30–60s-HFT-Anomalie) → bleibt PARK |

**Sequenzierungs-Logik in einem Satz:** Vol-Stack-Derivate hängen an C-42 (Pilot 2); alle Cascade-/Options-/Hidden-Liquidity-Pilots hängen an C-36-Recording-Vorlauf (Pilot 3); alle S3-/Funding-Folge-Entscheidungen hängen am E-15-Ausgang (Pilot 1).

**Kipp-Punkt-Logik Funding-Cluster (verdict §3):** Liefern E-15 (netto-positiv) UND C-37 (≤ 6 bps real) zusammen, kippt die Kernrelation für diesen Cluster → C-22/CS-12 werden ADOPT-fähig (frühestens nach L2-Walk-Forward). Liefert keines → Cluster fällt auf PARK.

---

## 5. PARK-Register

Geparkte Ansätze sind weder verworfen noch aktiv — sie warten auf eine Entsperr-Bedingung. Nichts hier startet ohne erfüllten Trigger (verdict §1, §8).

| Eintrag | Markt | Park-Grund (ID) | Entsperr-Bedingung |
|---|---|---|---|
| **C-30** Natural-Time κ₁ | F | importierter Theorie-Threshold κ₁≈0.070 = C-14-Wiedergänger-Risiko (cascade S-7) | erst nach C-27-Validierung; Distributions-Check (Erreichbarkeit der Schwelle) analog E-01 zuerst |
| **C-39** Kaskaden-Anatomie (Bankruptcy/Insurance/ADL) | F (O Overlay) | monatelang datenleer, kein REST-Archiv (cascade S-5) | nach C-36-Recording von insurance.USDT/adlAlert + Stress-reichem Fenster; Recall-Gate ≥ 90 %, aber Detektion ≠ Profit |
| **C-26** SIR R₀ | F | SUSPECT (CS-01, E-02); in C-39 absorbiert | geht in C-39 auf; kein eigener Pilot |
| **C-15** GR+Omori | F | SUSPECT, nie ausgelöst (E-02) | nur als Erschöpfungs-Exit-Glied in CS-06/CS-11; kein eigenständiger PILOT |
| **C-11** TDA/Persistent Homology | F (O IV-Surface) | ΔR²/Tail-AUC-Gate steht auf unreproduzierter Baseline (regime S-A2); IV-Surface datenlos (INC-04) | nach C-42-Reproduktion; IV-Surface zusätzlich an C-33-Fortschritt gekoppelt |
| **C-12** RQA | F | wie C-11; Preis-RQA solo liefert kaum ΔR² gegen HAR-RV | nach C-42-Reproduktion |
| **C-25** Kyle-λ / VPIN | F | Zirkularität: braucht positive Basis-Strategie (existiert nicht); E-04-Verlust ist Friktion, nicht inform. Flow (microstr S-A3) | erst sobald eine positive Basis-Strategie existiert (als Friktions-Veto) |
| **C-40** RPI Hidden-Liquidity | S/F | selbstzerstörender Edge (HFT liest RPI-Buch live); First-Mover beim Recording ≠ beim Edge (microstr S-A2) | Recording an C-36 koppeln als Forschungs-/Sicherungs-Asset, KEIN Handels-Edge-Claim |
| **C-03** Iceberg-Detection | F | von C-40 inhaltlich dominiert (RPI liefert dieselbe Info direkt) | nur falls C-40-Recording NICHT realisiert wird |
| **C-04** Wavelet-Symlet-Denoising | F | Vorverarbeitungs-Layer ohne validierten Abnehmer (C-01 SUSPECT) | erst nach Abnehmer-Signal (z.B. C-01) PARTIAL + positiv |
| **C-02** SpikeWavformer | S/F | Effizienz-Claim, kein Edge; Benchmark F0 (C-36) selbst ungemessen (microstr S-A9) | an C-36 gekoppelt; erst nach gemessenem F0-Recall als Effizienz-Benchmark |
| **C-43** Conformal Prediction | S/F/O | reinster Enabler; ökonom. Gate hängt an nicht-existentem Basissignal (regime S-A5) | Architektur-Notiz; auto-aktiv ab erstem L3-Outcome-E-xx |
| **C-34** GMM-Vol-Regime + VRP | S/F/O | Enabler ohne Enablement; 24h-Fenster untauglich für 24h-Persistenz (volstack S-6) | billiger Persistenz-Vorab-Check auf Bulk-Historie; voller Test erst nach C-42 + IV-Recording |
| **C-23** Basis-Convergence | S/F | No-Op in S3 (E-12, Pass-Through); 2-Bein ~22 bps gegen <0.08 % Konvergenz (funding S-8) | Standalone-Verdrahtung + Nachweis Konvergenz > Friktion |
| **C-38** TFT Known-Future | F | DL auf unbestätigtes Basissignal (funding S-7) | nach C-22-Live-Proof; DROP falls C-22 in E-15 scheitert |
| **C-19** TimesNet | S | DL-Direktional unter INC-05, redundant zu C-42/C-18 (volstack S-7) | kein realistischer Trigger; faktisch eingefroren |
| **Vol-Targeting** (Risk-Layer aus C-42) | S/F | 0×Verstärker = 0; keine positive Basis-E[R] (volstack S-2) | aktiviert erst bei netto-positiver Basis (E-15) |
| **RV-Stop / Regime-Filter** (aus C-42) | F | einzige Direktevidenz negativ (E-07/E-08); vol-adaptiv ist 2. Iteration | nach E-15 (statische Stops zuerst) |
| **C-17 / C-41** Lead-Lag | F | abgegraste HFT-Anomalie; „Robustheitskreuz" aus ungemessenen Achsen (crosssect S-2/S-8) | nur im kapitalfreien 2-Symbol-Mess-Gate (Welle 2+) |
| **C-13** Cross-Sectional-Z | F | Fee-Verdopplung 22–30 bps/Paar gegen 4–7 bps Roh-Edge; Panel-Harness = S4/S5-Falle (crosssect S-3/S-5) | nur falls 2-Symbol-Mess-Gate handelbare Kante findet |
| **C-09** HMM 3-State | F | SUSPECT (E-14); INC-05-Druck auf Direktional-Anspruch | nur als Gating (nicht direktional) nach Cross-Sectional-Unlock |
| **CS-04** Pattern×Foundation (S4) | F | UNTESTED (E-13, Loader) | Loader-Fix = billiges Negativexperiment; Ergebnis → REFUTED-Doku (HAR-Niederlage erwartet) |
| **CS-05** Cross-Sectional Reversion (S5) | F | UNTESTED (E-14, Panel-Harness) | nur falls Cross-Sectional-Cluster Kante zeigt |
| **CS-07** Footprint-Detektor | F | Konsens-Filter vor Einzel-Validierung sinnlos | erst nachdem C-16 UND C-31 je einzeln ihr Gate bestehen |
| **CS-08** Regime-Richtungs-Signal | F | 4+ SUSPECT/UNTESTED-Glieder; INC-02 auf OFI-Achse fatal | erst nach Einzel-Rehabilitierung der Glieder |
| **CS-10** Cross-Coin-Contagion | F | Panel-Lücke (E-14) + geteilter ω_s-Kernel + CCM gestreckt | nach Panel-Harness + Cascade-Validierung |
| **CS-11** Seismograph K1 | F | konvergiert nach C-14→C-27-Ersetzung auf CS-06; erbt C-14/C-15-Lasten | redundant; geht in CS-06 auf |
| **CS-12** Funding-Uhr K2 | F | Produkt aus 4 offenen Faktoren (E-15, C-37, C-08, C-22) | erst wenn E-15 + C-37 positiv |
| **CS-13** Rudel-Läufer K3 | F | = Cross-Sectional Voll-Cluster (PARK); enthält C-01 (INC-02) | nach Cross-Sectional-Unlock + C-01-Vorzeichen-Test |
| **C-11-M-S17** IV-Surface-PH | O | Tail-Schutz ist bei Short-Vol Eintrittsbedingung, selbst UNTESTED, datenhungrig (options S-4) | an C-33-Fortschritt gekoppelt (volle IV-Surface) |
| **C-18** PatchTST-RV | S | PARTIAL nur geliehen via C-42; Advocate erwartet selbst HAR-Niederlage (volstack S-7) | billiges Negativexperiment nach Loader-Fix; gehört in REFUTED-nahe Doku |

---

## 6. REFUTED-Register

> Diese drei Befunde sind die einzigen forensisch isoliert belasteten des gesamten Registers (alle aus GEEIGNETEN Testfenstern, Belastbarkeit HOCH). Sie kommen NICHT ins Framework. Dieser Abschnitt ist Wissensspeicher: damit nie wieder jemand dieselben toten Pferde reitet. Forensische Kette je Eintrag aus verdict §2.

### C-14 — Hawkes-Spektralradius ρ(Φ): Schwelle + Estimator-Output REFUTED (Konzept UNTESTED)

**Kette:** E-01 misst über alle 5 Symbole, 56k–87k Ticks (GEEIGNETES Fenster für die Distributions-Aussage): ρ-Median ≈ 2e-7 — **sechs Größenordnungen** unter dem importierten Threshold 0.85. p95 (SOL/BNB/XRP) ~6e-7; BTC/ETH-Floor-Saturation bei ~1e-3 ist laut E-01 numerisches Artefakt, kein zweiter Modus. INC-01: der Threshold 0.85 stammt aus fremder Mikrostruktur (Bacry-Mastromatteo-Muzy), nie auf Bybit-Erreichbarkeit geprüft. E-02: S1 feuert 0 Trades, Ursache `rho_below_threshold` (nicht Datenmangel — Liquidationen auf 4/5 Symbolen reichlich).
**Urteil:** Der aktuelle Single-Channel-ρ-Estimator + die 0.85-Schwelle sind **REFUTED** (Belastbarkeit HOCH, kein Multiple-Testing-Problem — Verteilungsbefund). Das Branching-/Reflexivitäts-**Konzept** bleibt UNTESTED und ist in C-27 (Rₜ, self-calibrating) sauber re-inkarniert. **C-14 erhält KEIN eigenes Pilot-Budget.**
**Verbotene Wiederholung:** kein erneuter Test der 0.85-Schwelle; jeder Branching-Ratio-Ansatz muss zuerst die Erreichbarkeit seiner Schwelle per Distributions-Check beweisen (gilt auch für C-30 κ₁).

### CS-01 — „Seismischer Cascade Detector" (S1): REFUTED (aktuelle Implementierung)

**Kette:** CS-01 = C-14 (ρ-Gate) + C-15 (GR+Omori) + C-26 (SIR R₀). Das ρ-Eingangsgate (C-14) erreicht den Threshold strukturell nie (E-01) → die Strategie feuert 0 Trades auf allen 5 Symbolen (E-02). Die M14-basierte Implementierung ist **REFUTED**. Forensik-Differenzierung (Modul ≠ Strategie): nur C-14 ist isoliert belastet; C-15/C-26 bleiben SUSPECT/UNTESTED (nie ausgelöst, weil das ρ-Gate vorgeschaltet blockierte; Liquidationen wären datenseitig da gewesen). Das übergeordnete Kaskaden-Konzept ist UNTESTED, Fenster für Kaskaden-Prädiktion EINGESCHRÄNKT (GM-6).
**Urteil:** Aktuelle Strategie **DROP/REFUTED**. Saubere Neugeburt = CS-06 (threshold-frei, ohne REFUTED/SUSPECT-Module).
**Verbotene Wiederholung:** keine Reaktivierung von S1 mit der M14-Pipeline; jeder Cascade-Pilot startet bei CS-06 mit C-27/C-28/C-29.

### CS-02 — „Entropie-Momentum" (S2): REFUTED (einzige eindeutig widerlegte Strategie)

**Kette (drei unabhängige Forensiken aus GEEIGNETEN Fenstern):**
1. **E-03 (Maker-Only, schärfster Test):** Roh-Edge negativ auf JEDEM Symbol auch ohne Fees — BTC -3.61, ETH -3.71, SOL -3.99, BNB -1.65, XRP -4.06; Aggregat -3.45 bps. Selbst bei 0 Friktion verliert jedes Symbol roh.
2. **E-04 (Mirror-Test):** hit_sum = 0.179 ≠ 1.0; Inversion macht es schlimmer (-3.45 → -4.55). → S2 ist NICHT anti-prädiktiv invertierbar, sondern **execution-loss-bound** (doppelseitige Slippage RMS 8.0 bps BTC/ETH).
3. **E-16:** Friktion dominiert Richtung ~35× (iter-2-Inversions-Delta).
**Modul-Implikation (Modul ≠ Strategie):** C-06 bleibt PARTIAL (Gate feuert messbar, E-05); C-01/C-07 bleiben SUSPECT (Beitrag nie isoliert). **KEIN Modul wird durch CS-02 automatisch REFUTED.** Die simple Sign-Flip-MR-Rehabilitierung von C-06 ist durch E-04 bereits gescheitert — nur eine NICHT-triviale MR-Hypothese bleibt als C-06-PILOT offen.
**Urteil:** Strategie **DROP/REFUTED**, Belastbarkeit HOCH (5 Symbole konsistent, schärfster Test bestanden).
**Verbotene Wiederholung:** kein Re-Test der S2-Richtungsthese und keine simple Invertierung; ein C-06-PILOT braucht ein nachweislich anderes Signal.

---

## 7. Architektur-Delta zum Repo (Skizzen-Niveau, kein Code)

Bezug: repo_map.md (Scinance 1.0 = 5-Layer-Pipeline L1–L5, S1–S5, Replay-Harness, 88+ Tests, Live-Runner, Dashboard). Hinweis: das kanonische Claim-Mapping ist `claims_register.md` (C-01 = OFI in `m2_ofi.py`, C-02 = SpikeWavformer in `m1_spikewavformer.py`); die Modul-Spalte in repo_map §2.1 vertauscht C-01/C-02 — hier gilt das Register.

### Was BLEIBT (das Fundament, das funktioniert)

- **Replay-Harness** (`replay_backtester.py`, `replay_all.py`) — die Falsifikations-Maschine; jeder Pilot-Gate läuft darüber.
- **Test-Suite** (88+ Tests) — wird erweitert, nicht ersetzt; insbesondere die Forensik-Tests (`test_replay_backtester_maker_only.py`, `test_strategy3_bounded_exits.py`, `test_strategy_direction_inversion.py`) sind methodisches Tafelsilber.
- **Friction-Modell / Kostenbaseline** (Fee/Slippage in der Replay-Engine) — die Kernrelation muss in jedem Gate sichtbar bleiben; netto-bps ist die Standard-Berichtsgröße.
- **Diagnostik / Funnel-Counter** (`reason_counts`, Diagnostics in `replay_all_results.json`) — hat S1/S2/S3-Versagen erst lokalisierbar gemacht; bleibt verpflichtend.
- **Daten-/State-Layer** (Orderbook-State, Trade-/Liquidation-Buffer, Collector, Persistence, Backfill).

### Was sich ÄNDERT (Retirement, Vorbehalt, Einfrieren)

- **S1 / S2 — Retirement in Config:** CS-01/CS-02 sind REFUTED (§6). Sie werden NICHT gelöscht (Wissensspeicher), aber in der Strategie-Config auf `retired` gesetzt und aus jedem Live-/Aggregat-Pfad entfernt. Die Module C-14 bleiben als REFUTED markiert; C-06/C-01/C-07/C-15/C-26 bleiben als SUSPECT verfügbar, aber deaktiviert.
- **S3 unter E-15-Vorbehalt:** CS-03 bleibt nur aktiv, solange Pilot 1 (§3) im Korridor läuft. Der iter-5-Fix (Time-Stop Tick-Zeit, friction-aware Hard-Stop) ist committet aber unvalidiert (E-15); die Strategie bleibt bedingt, bis das Gate entscheidet.
- **S4 / S5 — Einfrierung:** CS-04/CS-05 bleiben UNTESTED-Mess-Lücken (E-13/E-14). Der Modell-Loader (S4) und der Panel-Harness (S5) werden **nicht** in Welle 1 gebaut (S4/S5-Falle, §2.4). S4-Loader-Fix nur als billiges Negativexperiment mit erwarteter HAR-Niederlage → REFUTED-Doku.

### Was NEU kommt (Module für Scinance 2.0)

- **Recording-Engine F0 (C-36) mit Storage-Deckel** — neue Streams `orderbook.rpi`, `insurance.USDT`, `adlAlert`, Premium-Index-Kline, Options-Tickers (repo_map §5); deterministisches Perzentil-Regelwerk, F0-Recall-Gate ≥ 95 %, ringpuffer-basierter Storage-Deckel, Sunset-Review. **Höchster Infrastruktur-Hebel.**
- **C-42-Repro-Pipeline** — purged-Walk-Forward-Harness (≥ L2) mit FDR über die 36 Features; reproduziert die LightGBM/HAR-RV-Baseline als Anker des Vol-Stacks. C-42 lebt heute außerhalb des `src/bybit_edge`-Baums (separates Kestrel-v1.4-Notebook) und muss in die Pipeline geholt werden.
- **CFAR-Modul (C-31)** — Cyclic-Spectrum-Schätzer + CFAR-Peak-Detektor + Surrogate-Test auf publicTrade-Inter-Arrivals; der einzige neue Alpha-Test der Welle 1.
- **Multiple-Testing-/Hypothesen-Registry** (siehe §8) — neues Querschnitts-Modul: registriert jede Hypothese VOR dem Test, führt FDR-Familien, blockiert Post-hoc-Anpassungen.
- **Später, gate-abhängig:** Panel-Harness (nur falls Cross-Sectional-Mess-Gate eine Kante zeigt), IV-Recorder/VRP-Pipeline (nur nach ≥ 12-Mon.-IV-Archiv inkl. Stress-Periode), Cascade-Module C-27/C-28/C-29 (nur nach Recording-Vorlauf).

### Die 3 wichtigsten Deltas

1. **Identitätswechsel:** vom 5-Strategien-Live-Portfolio (S1–S5) zur Falsifikations-Pipeline mit Hypothesen-Registry; S1/S2 retired, S3 bedingt, S4/S5 eingefroren.
2. **Recording-Engine F0 (C-36) als gedeckeltes Fundament:** schaltet ~5 nachgelagerte Claims frei, mit hartem Storage-Deckel und Sunset-Review gegen Data-Lake-Wildwuchs.
3. **C-42-Repro als Vol-Stack-Anker:** der einzige positive OOS-Befund wird zuerst reproduziert; ohne ihn ist jedes Vol-Feature-Gate ein Phantom-Vergleich.

---

## 8. Multiple-Testing-Disziplin (verbindliche Systemregel)

Problem (GM-2): keine FDR/Bonferroni in irgendeiner Quelle; 3 Iter × 5 Symbole × 5 Strategien × 2 Arme bereits unkorrigiert. Über alle PILOT/PARK summieren sich ~25 potenzielle Hypothesen-Gates. Festlegung aus verdict §5, als Systemregel:

1. **Welle-1-Parallelität hart auf 4 Hypothesen-Gates gedeckelt.** Davon sind 3 Infrastruktur/Reproduktion (E-15-Auswertung, C-42-Repro, C-36-Recording); **effektives neues Alpha-Test-Budget Welle 1 = 1** (nur C-31). Das hält das FDR-Risiko minimal.
2. **FDR-Korrektur (Benjamini-Hochberg, α = 0.10) verpflichtend** über jede Familie parallel getesteter Varianten:
   - **Funding-Familie** (C-22-Quantilvarianten, C-32, C-23) — gemeinsame FDR.
   - **Vol-Feature-Familie** (C-10, C-35, C-11, C-12 ΔR² gegen C-42) — gemeinsame FDR.
   - **Cascade** (C-27 + C-28 = EIN Test, geteilter ω_s-Kernel; C-29 separat).
   - **Cross-Sectional Konditionierungs-Suche** — FDR bereits VOR dem finalen Gate, nicht nur darin.
3. **Hypothesen-Registrierung VOR dem Test (Pre-Registration):** jede Hypothese, jeder Schwellwert, jedes Fenster wird in der Hypothesen-Registry festgeschrieben, bevor der Run startet. **Keine Post-hoc-Schwellenanpassung** — die E-15-Tore (§3) sind das Muster: Torpfosten vorab fixiert, kein Verschieben (judge.md #3).
4. **Schwellen-Verschärfung wegen Peso/L0:** alle Erstläufe sind L0/Single-Pass → ein einzelnes „> Schwelle in 2 Fenstern" zählt NICHT als bestanden ohne Walk-Forward (≥ L2). VRP (C-33) insbesondere: 3-Monats-Verdikt ist Peso-verzerrt → Schwelle = ≥ 12 Mon. mit Stress-Periode.
5. **Hartes Ein-Fenster-Abbruchkriterium** (C-27/C-28/C-29/C-32/C-16): Schwelle in EINEM disjunkten Fenster verfehlt → DROP, kein Nachverhandeln.

---

## 9. Betriebsmodell (Einzelbetreiber-Realismus)

Scinance 2.0 wird von einer Person betrieben. Das Betriebsmodell trennt kontinuierliche von episodischen Lasten und schreibt feste Review-Kadenzen fest (verdict §4 Ressourcen-Realismus, §3 PENDING-Regel, C-36 Sunset).

**Läuft kontinuierlich (passiv, niedrige Aufmerksamkeit):**
- **Recording-Engine F0 (C-36):** sammelt durchgehend die neuen Streams unter Storage-Deckel. Einzige dauerhaft laufende Komponente. Erzeugt den Vorlauf, ohne den Cascade-/Options-Pilots datenleer bleiben.

**Läuft episodisch (aktiv, hohe Aufmerksamkeit, je Pilot):**
- **Replay-Validierungen:** jeder Pilot-Gate ist ein abgegrenzter Replay-/Walk-Forward-Lauf (Pilot 1 läuft bereits; Pilot 2/4 sind 1–3-Wochen-Läufe; Welle-2-Pilots starten erst bei erfülltem Unlock).
- **Maximal 3–5 Pilots parallel**, davon höchstens 1 neuer Alpha-Test pro Welle (siehe §8).

**Review-Kadenz:**
- **Gate-Review je Pilot:** bei Abschluss jedes Replay-Laufs Entscheidung gegen das vorab registrierte Gate (PILOT-fortführen / DROP / Graubereich). Kein Lauf ohne dokumentiertes Gate-Urteil.
- **Sunset-Review für Recording (alle 3 Monate):** prüft je aufgezeichnetem Stream, ob ein recording-abhängiger Pilot ihn tatsächlich nutzt. Ungenutzte Streams werden abgeschaltet (Anti-Data-Lake, microstr S-A1). Der erste Sunset fällt 3 Monate nach Recording-Start (C-36-Gate).
- **E-15-Review (einmalig, sofort):** sobald der laufende iter-5-Run abschließt, Auswertung gegen die §3-Tore — entscheidet über den gesamten Funding-Cluster und die Folge-Pilots C-37/CS-12/C-08.

---

## Anhang — Referenzlisten

**REFUTED (3):** C-14, CS-01, CS-02.
**Welle-1-Pilots (4):** E-15-Auswertung (CS-03/C-22), C-42-Reproduktion, C-36-Recording, C-31-CFAR. Effektives neues Alpha-Budget = 1 (C-31).
**Welle-2+-Pilots (sequenziert):** C-10, C-35, C-08, C-27+C-28, C-29, CS-06, C-33-VRP, C-37, C-06, C-07, C-01, C-20, Cross-Sectional-2-Symbol-Mess-Gate.
**ADOPT:** 0 (CONFIRMED unerreichbar, GM-1).

**Verwendete E-xx:** E-01, E-02 (S1/C-14), E-03, E-04, E-05, E-06, E-16 (S2/CS-02), E-07, E-08, E-09, E-10, E-11, E-12, E-17, E-18 (S3/CS-03), E-13 (S4), E-14 (S5), E-15 (PENDING/iter-5).
**Globale Vorbehalte:** GM-1 (L0-Decke), GM-2 (Multiple Testing), GM-3 (qty=1 Notional), GM-4 (kleine N), GM-5 (Within-Sample-Kontamination), GM-6 (Fenster-Eignung).
**Inkonsistenzen aus claims_register:** INC-01 (importierter ρ-Threshold), INC-02 (OFI-Vorzeichen-Orientierung), INC-03 (Pressure-Threshold übertriggert), INC-04 (Options-Markt/IV-Archiv fehlt), INC-05 (unkonditionale Richtungs-AUC ≈ 0.50).
**Verwendete C-xx:** C-01..C-43 (Module), CS-01..CS-13 (Strategien) — vollständig in claims_register.md, Status je Claim in alignment_matrix.md, Urteil je Claim × Markt in verdict.md §1.
**Vorab-Urteile:** P-01 (CONCEPT_REVIEW), P-02 (PRD_VS_REALITY) — Abgleich in verdict §6; keine Ankerung, jede Übereinstimmung unabhängig hergeleitet.

*Ende FINAL_PRD.md*
