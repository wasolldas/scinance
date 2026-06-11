# Verdict — Edge Reconciliation Framework

**Phase:** 5 — VERDICT
**Stand:** 2026-06-11
**Erstellt von:** judge
**Inputs:** alignment_matrix.md (0 CONFIRMED / 5 PARTIAL / 3 REFUTED / 48 UNTESTED, 16 SUSPECT), claims_register.md (56 Claims, INC-01..06, P-01/P-02), evidence_register.md (E-01..E-18, GM-1..6, Kostenbaseline), 7 Debatten (cascade, funding, volstack, crosssectional, microstructure, regime, options).

---

## 0. Verbindliche Urteils-Grundlagen (aus CLAUDE.md + judge.md)

1. **CONFIRMED ist unerreichbar.** Gesamtes Register L0 (GM-1: 17×L0 + 1 PENDING). Kein E-xx hebt einen Claim auf CONFIRMED. → **Maximalurteil ohne neue Validierung = PILOT, nicht ADOPT.** Es gibt in diesem Verdict **kein einziges ADOPT** für einen Alpha-Claim — das ist eine direkte, nicht verhandelbare Konsequenz der Evidenzlage, nicht Vorsicht.
2. **Kernrelation (Kostenbaseline):** Round-Trip-Friktion 11 bps (Taker) / ~15 bps (inkl. Slippage) > jede gemessene Roh-Edge (max |Roh| ≈ 4–7 bps). Friktion > Signal auf JEDER gemessenen Strategie. Jeder Edge-PILOT muss zeigen, wie er diese Wand umgeht (längerer Horizont / Maker-Execution / Filter-Friktionsersparnis / nicht-direktionale Prämie).
3. **INC-05:** unkonditionale Richtungsprognose = AUC ≈ 0.50. Jeder Direktional-Claim ist nur regime-konditioniert (bedingte AUC > 0.55) überlebensfähig.
4. **PENDING-Regel (judge.md #3):** Hängt ein Urteil an E-15 (PENDING), ist es zwingend PILOT mit E-15 als erstem Gate und Vorab-Festlegung der Tore (kein Verschieben der Torpfosten). Erwartete iter-5-Deltas: time_stop 1→60–70, n>120s 68→~0, n<-30bps 33→~0, mean pnl_bps -16.81→≥-5.
5. **Modul ≠ Strategie.** Kein SUSPECT-Modul wird durch Strategie-Niederlage automatisch REFUTED.
6. **Vorab-Urteile P-01/P-02 unabhängig hergeleitet**, Abgleich in §6.

---

## 1. Entscheidungsmatrix — JEDER nicht-REFUTED Claim × Markt

Legende: ADOPT / PILOT / PARK / DROP. Spot=S, Futures(Perp)=F, Optionen=O.
„DROP (kM)" = kein Mechanismus auf diesem Markt. Begründungsspalte verweist auf C-/E-/Debatten-IDs (A-x Advocate, S-x Skeptic).

### 1a. Module mit positiver/teil-positiver Evidenz (PARTIAL)

| Claim | S | F | O | Begründung (ID-gestützt) |
|---|---|---|---|---|
| **C-42** LightGBM/HAR-RV | PILOT | **PILOT** | PARK | Einziger positiver OOS-Befund (R²=0.249), aber L1-Selbstauskunft, kein E-xx, keine FDR über 36 Features (volstack S-1). ADOPT abgelehnt (kein CONFIRMED). Reproduktion ist Pflicht-Vorbedingung des gesamten Vol-Stacks. O=PARK: RV nur halbe VRP-Gleichung, IV fehlt. |
| **C-06** Shannon-Entropie | DROP | **PILOT** | DROP (kM) | Einziges Modul, das in GEEIGNETEM Fenster strukturiert feuert (E-05, ~97 %). ABER Sign-Flip-MR-Lesart durch E-04 (hit_sum 0.179) bereits widerlegt (microstr S-A4); Rest = Vol-Cluster-Detektor (Feature). PILOT nur für NICHT-triviale MR-Hypothese, FDR-korrigiert. |
| **C-18** PatchTST-RV | PARK | **DROP** | n/a | PARTIAL nur geliehen via C-42; Advocate erwartet selbst HAR-Gate-Niederlage (volstack S-7). Auf RV-Ziel: billiges Negativexperiment nach Loader-Fix, gehört in REFUTED-nahe Doku, kein PILOT-Pfad. |
| **C-22** Funding-Pressure-Entry | DROP (kM) | **PILOT** | DROP (kM) | Einziges real feuerndes Entry (N=213). „Nie negativ isoliert" ist symmetrisch — auch nie positiv (funding S-2). INC-03-Übertriggern trifft Entry. PILOT = settlement-gebundener, FDR-korr. Isolationstest. |

### 1b. Cascade-Cluster (C-27..C-30, C-39, C-15, C-26, C-14-Konzept)

| Claim | S | F | O | Begründung |
|---|---|---|---|---|
| **C-27** Cori-Rₜ | DROP (kM) | **PILOT** | DROP (kM) | Cluster-Spitze; ersetzt toten Import-Threshold (E-01) durch self-calibrating Rₜ=1. ABER freier Parameter wandert zu ω_s (cascade S-1); Posterior-Varianz-Gate auf Intervall-Untergrenze Pflicht. |
| **C-28** NB-k | DROP (kM) | **PILOT (= EIN Test mit C-27)** | DROP (kM) | Teilt ω_s-Kernel → statistisch NICHT unabhängig von C-27 (cascade S-2, GM-2). Keine getrennte Zählung. Power-Analyse vor Run. |
| **C-29** Avalanche Shape-Collapse | DROP (kM) | **PILOT (eigenständig)** | DROP (kM) | Einziger kernel-unabhängiger, E-10-motivierter Kandidat. Muss reparierten Time-Stop (E-15) UND simplen Hazard schlagen, nicht nur Konstant-Mittel (cascade S-3). |
| **C-30** Natural-Time κ₁ | DROP (kM) | **PARK** | DROP (kM) | Importierter Theorie-Threshold κ₁≈0.070 = C-14-Wiedergänger (E-01-Fehlertyp); dritter korrelierter Schuss (cascade S-7). Erst nach C-27-Validierung. |
| **C-39** Kaskaden-Anatomie | DROP (kM) | **PARK** | PARK (Overlay) | Orthogonale Stress-Achse (Bankruptcy-Preis), aber monatelang datenleer (kein REST-Archiv), Recall-Gate misst Detektion≠Profit (cascade S-5). |
| **C-26** SIR R₀ | DROP (kM) | PARK (geht in C-39 auf) | DROP (kM) | SUSPECT (CS-01, ρ-Gate blockierte, E-02); in C-39 absorbiert. |
| **C-15** GR+Omori | DROP (kM) | **PARK** (nur als Erschöpfungs-Exit in CS-06/11) | DROP (kM) | SUSPECT (nie ausgelöst, E-02). Kein eigenständiger PILOT; Exit-Glied. |
| **C-14** Konzeptrest | DROP | DROP (in C-27 absorbiert) | DROP | Beide Debattenseiten einig: kein eigener Posten, geht in C-27 auf (cascade S-4). M14-Form ist REFUTED (§2). |

### 1c. Funding-Cluster (C-22 oben; C-23, C-24, C-32, C-37, C-38)

| Claim | S | F | O | Begründung |
|---|---|---|---|---|
| **C-37** Spread-Execution | PARK (Hedge-Bein) | **PILOT** | DROP (kM) | Einziger dokumentierter Friction-Killer (11→~4 bps). ABER 4-bps ungemessen, Maker-Quote ≥70 % adversariell selektiert genau im Release-Regime (funding S-4). PILOT = Live-Mikro-Pilot mit konditionalem Maker-Quoten-Gate IN Release-Fenstern. |
| **C-32** Funding-Contrarian 24h | DROP (kM) | **PILOT (FDR-Pflicht-Falsifikation)** | PARK (VRP-Flag) | Horizont schlägt Friktion math.; REST-only, sofort laufbar. ABER null Evidenz, Quelle erwartet selbst Zerfall, ≥6 Carry-Regeln ohne FDR (funding S-5). PILOT nur als FDR-korr. Pflicht-Falsifikation, hartes Abbruch (1 Fenster ≤0 → DROP). |
| **C-23** Basis-Convergence | **PARK** (Spot-Perp-Paar) | PARK | DROP (kM) | No-Op in S3 (E-12, Pass-Through). No-Arbitrage robust WEIL klein; 2-Bein = ~22 bps gegen <0.08 % Konvergenz (funding S-8). Standalone-Verdrahtung + Konvergenz>Friktion zeigen, sonst PARK. |
| **C-24** Kalman-Premium | DROP (kM) | **DROP** | DROP (kM) | Kein eigener Befund (Matrix), rein spekulativ, strikt nachrangig zu C-23 das selbst PARK ist (funding S-8). Wissensspeicher: zu wenig Substanz für eigenes Budget. |
| **C-38** TFT Known-Future | DROP (kM) | **PARK** (DROP falls C-22 in E-15 scheitert) | DROP (kM) | Vorteil kalendarisch, Aufgabe direktional (INC-05). DL auf unbestätigtes Basissignal (funding S-7). |

### 1d. Vol-Stack (C-42 oben; C-10, C-19, C-20, C-34, C-35)

| Claim | S | F | O | Begründung |
|---|---|---|---|---|
| **Vol-Targeting** (Risk-Layer, aus C-42) | PARK | **PARK** | n/a | Mathematisch korrekter Verstärker, aber 0×Verstärker=0 — keine positive Basis-E[R] im Register (volstack S-2). Risk-Schicht, NICHT Edge-Liste; aktiviert erst bei netto-positiver Basis (E-15-PENDING). |
| **RV-Stop / Regime-Filter** (aus C-42) | DROP/PARK | **PARK** (hinter E-15) | n/a | Adressiert E-10-Tail, aber einzige Direktevidenz negativ (E-07/E-08); iter-5 testet erst statische Stops, vol-adaptiv ist 2. Iteration (volstack S-3). |
| **C-10** MF-DFA/Hölder | PILOT* | **PILOT*** | DROP | Inkrementelles ΔR²-Gate (Anti-S1), aber gegen unreproduzierte C-42-Baseline. *=strikt hinter C-42-Reproduktion (volstack S-4). |
| **C-35** CEEMDAN | PILOT* | **PILOT*** | DROP | Wie C-10, ZUSÄTZLICH Lookahead-KILL-Gate (bit-für-bit-Kausalität) VOR ΔR²-Interpretation (volstack S-4). |
| **C-34** GMM-Vol-Regime+VRP | PARK | **PARK** | PARK | Enabler ohne Enablement (kein zu konditionierendes Basissignal); Flatter ungeprüft; 24h-Fenster untauglich für 24h-Persistenz (volstack S-6). Billiger Persistenz-Vorab-Check auf Bulk-Historie. |
| **C-19** TimesNet | PARK | **DROP** | n/a | DL-Direktional unter INC-05; redundant zu C-42/C-18 (volstack S-7). |
| **C-20** MOMENT | DROP | **PILOT (nur Zero-Shot-Neulisting)** | n/a | Einziger Fall ohne verlorenen HAR-Vergleich: RV auf neu gelistete Symbole ohne Lookback (volstack S-7). Sonst DROP. |
| **C-33** VRP/Short-Vola | n/a | mittelbar/PARK | **PILOT (verschärftes Gate)** | siehe 1g (Options). |

### 1e. Cross-Sectional / Lead-Lag (C-09, C-13, C-17, C-41)

| Claim | S | F | O | Begründung |
|---|---|---|---|---|
| **C-17** Renyi-Transfer-Entropy | DROP | **PARK** (PILOT nur im Mess-Gate) | DROP (kM) | Bedingte exogene Kante (INC-05-kompatibel), ABER abgegraste HFT-Anomalie 30–60 s, Multiple-Testing über Konditionierungen (crosssect S-2). Nur im kapitalfreien 2-Symbol-Mess-Gate. |
| **C-41** Wavelet-Coherence | DROP | **PARK** (mit C-17 im Mess-Gate) | DROP (kM) | Orthogonal zu C-17, aber selbst UNTESTED; „Robustheitskreuz" aus 2 ungemessenen + 1 kontaminierten (C-01/INC-02) Achsen (crosssect S-8). |
| **C-13** Cross-Sectional-Z | DROP | **PARK** | DROP (kM) | Long-Short bias-immun (gut), ABER Fee-Verdopplung 22–30 bps/Paar gegen 4–7 bps Roh-Edge (crosssect S-3). Panel-Harness = S4/S5-Falle-Wiederholung (S-5). |
| **C-09** HMM 3-State | DROP | **PARK** (nur als Gating, nicht Direktional) | DROP (kM) | SUSPECT (S5 nie gelaufen, E-14); INC-05-Revisionsdruck auf Direktional-Anspruch. Auf reines Gating zurückstufen (crosssect A-10). |

### 1f. Mikrostruktur / Regime (C-01, C-02, C-03, C-04, C-07, C-08, C-11, C-12, C-16, C-25, C-31, C-36, C-40, C-43)

| Claim | S | F | O | Begründung |
|---|---|---|---|---|
| **C-36** F0-Trigger / Recording | PILOT (gedeckelt) | **PILOT (gedeckelt, Prio 1 Infra)** | PARK (IV-Rec.) | Fundament: macht ALLE recording-abhängigen Claims erst testbar. ABER „hypothesenfrei nützlich" = Data-Lake ohne Abbruch (microstr S-A1). PILOT NUR mit Storage-Deckel + F0-Recall≥95 % (2–4 Wo) + Sunset-Review nach 3 Mon. KEIN unbeschränktes ADOPT. |
| **C-31** Cyclostationary CFAR | DROP | **PILOT (priorisiert)** | DROP (kM) | Einziges billiges, eigenständiges, friktions-ehrliches Falsifikations-Gate (eingebaute FP-Kontrolle, regime S-A3). Surrogate p≤0.05 + Lead>50 ms + Edge>11 bps ZUERST. |
| **C-16** TFSAX+SW | DROP | **PILOT (nachgeordnet)** | DROP | Bringt eigenes hartes Drop-Gate (OOS-AUC>0.55 sonst raus); CS-04 = Mess-Lücke, nicht Niederlage (E-13). Datenhungrig, Multiple-Testing-Magnet (regime S-A4). |
| **C-07** Permutation Entropy | DROP | **PILOT (billigster Lottoschein)** | DROP (kM) | Datenmäßig billigstes Regime-Gate (nur Kline, kein Tiefen-Stream/INC-06). „Billig testbar" ≠ „erfolgswahrscheinlich"; m/τ vorab fixiert, ρ-Vorprüfung ≥0.3 sonst DROP (microstr S-A5). |
| **C-01** OFI | DROP | **PILOT (nur nach INC-02-Vorzeichen-Test)** | DROP (kM) | Direktionaler Beitrag nie isoliert (UNTESTED, nicht REFUTED). ABER INC-02: Vorzeichen markiert evtl. MM-Replenishment. Reihenfolge nicht verhandelbar: Vorzeichen-Test ZUERST, scheitert er → DROP für C-01/C-09/C-14-OFI-Erbe (microstr S-A7). |
| **C-08** BOCPD | DROP | **PARK** (PILOT nur falls iter-5-Time-Stop E-10-Tail NICHT schneidet) | n/a | Ockham: `if elapsed>120s: exit` adressiert E-10 trivial (regime S-A1). No-Op in S3 (E-12). Muss gegen iter-5-Baseline antreten, nicht ungate-t. + Erreichbarkeits-Check auf Bulk-Brüchen. |
| **C-11** TDA/Persistent Homology | DROP | **PARK** (bis C-42 reproduziert) | PARK (IV-Surface, INC-04) | ΔR²/Tail-AUC-Gate steht auf unreproduzierter Baseline (regime S-A2). IV-Surface-Variante (M-S17) datenlos. |
| **C-12** RQA | DROP | **PARK** (bis C-42 reproduziert) | n/a | Wie C-11; Preis-RQA solo liefert gegen HAR-RV kaum ΔR² (regime S-A2). |
| **C-25** Kyle-λ / VPIN | DROP | **PARK** | DROP (kM) | Veto spart Friktion (gut), ABER Zirkularität: braucht positive Basis-Strategie (existiert nicht); E-04-Verlust ist Friktion, nicht inform. Flow; VPIN-Bucketing = 3+ unkorr. Parameter (microstr S-A3). |
| **C-40** RPI Hidden-Liquidity | PARK | **PARK** (Recording als Grenzkosten-Anhängsel) | n/a | First-Mover beim Recording ≠ beim Edge (HFT liest RPI-Buch live); selbstzerstörender Edge (microstr S-A2). Recording an C-36-Engine koppeln, als Forschungs-/S-R-Asset, kein Handels-Edge-Claim. |
| **C-03** Iceberg-Detection | DROP | **PARK** | n/a | Von C-40 inhaltlich dominiert (RPI liefert dieselbe Info direkt); nur falls C-40-Recording NICHT realisiert (microstr S-A8). |
| **C-04** Wavelet-Symlet-Denoising | DROP | **PARK** | n/a | Vorverarbeitungs-Layer ohne validierten Abnehmer (C-01 SUSPECT); erst nach Abnehmer-Signal PARTIAL+positiv (microstr S-A8). |
| **C-02** SpikeWavformer | PARK | **PARK** (an C-36 gekoppelt) | n/a | Effizienz-Claim, kein Edge; Benchmark F0 (C-36) selbst ungemessen → doppelt deferiert (microstr S-A9). |
| **C-43** Conformal Prediction | PARK | **PARK** (Architektur-Notiz, auto-aktiv ab 1. L3-Outcome-E-xx) | PARK | Reinster Enabler-Fall; Coverage-Gate trivial, ökonom. Gate hängt an nicht-existentem Basissignal (regime S-A5). Kein PILOT-Substrat. |

### 1g. Options (C-33 zentral)

| Claim | S | F | O | Begründung |
|---|---|---|---|---|
| **C-33** VRP / Short-Vola | n/a (Hedge) | Hedge-Bein (datenseitig beherrscht) | **PILOT (verschärftes Gate)** | Einziger INC-05-immuner Edge (nicht-direktional). ABER immun ≠ risikoarm: short Gamma/Vega, Single-Name-Krypto-Tail, 60–80 % illiquide, kein MM-Backstop; 3-Mon.-Recorder misst Peso-verzerrt nur die ruhige Hälfte (options S-1/S-2). |
| **C-11-M-S17** IV-Surface-PH | n/a | n/a | **PARK** (an C-33-Fortschritt gekoppelt) | Tail-Schutz ist bei Short-Vol Eintrittsbedingung, nicht optionales Gate 3 (options S-4); selbst UNTESTED, datenhungrig (volle Surface). |

### 1h. Strategien (CS-xx, nicht-REFUTED)

| Strategie | S | F | O | Begründung |
|---|---|---|---|---|
| **CS-03** Pre-Settlement (S3) | n/a | **PILOT (BEDINGT, Gate = E-15)** | n/a | siehe §3 (bedingtes Urteil). |
| **CS-12** Funding-Uhr K2 | n/a | **PARK** (bis E-15+C-37 positiv) | n/a | Produkt aus 4 offenen Faktoren (E-15 pending, C-37 ungemessen, C-08 No-Op, C-22 friction-bound) (funding S-6). |
| **CS-06** Kaskaden-Cockpit | DROP | **PILOT (sauberster Cascade-Pilot, ω_s-kernel-gekoppelt)** | DROP | Einzige Cascade-Strategie ohne REFUTED/SUSPECT-PRD-v1-Modul; ABER „Diversität" ist ω_s-ID-Artefakt (cascade S-6). = C-27+C-28+C-29+C-43 als ein Pilot. |
| **CS-04** Pattern×Foundation (S4) | PARK | **PARK** (Loader-Fix = billiges Negativexp.) | n/a | UNTESTED (E-13, Loader). Auf RV-Ziel erwartet Advocate selbst HAR-Niederlage (volstack S-7); Ergebnis gehört zu REFUTED-Doku. |
| **CS-05** Cross-Sectional Reversion (S5) | DROP | **PARK** | DROP | UNTESTED (E-14, Panel-Harness); Voll-Cluster PARK (crosssect S-Verdikt). |
| **CS-07** Footprint-Detektor | DROP | **PARK** (bis C-16 UND C-31 je einzeln Gate bestehen) | n/a | Konsens-Filter erst nach Einzel-Validierung (regime S-CS07). |
| **CS-08** Regime-Richtungs-Signal | DROP | **PARK** | DROP | 4+ SUSPECT/UNTESTED-Glieder; INC-02 auf OFI-Richtungsachse fatal; erst nach Einzel-Rehabilitierung (microstr S-A6). |
| **CS-09** Options-Block | DROP | Hedge-Bein | **DROP als Monolith / PILOT dekomponiert** | Monolith verstößt Modul≠Strategie; C-33-Kern zuerst, Topologie/CP später (options S-4). |
| **CS-10** Cross-Coin-Contagion | DROP | **PARK** | DROP | Panel-Lücke (E-14) + geteilter ω_s-Kernel + CCM „gestreckt" (cascade S-6). |
| **CS-11** Seismograph K1 | DROP | **PARK / redundant** | DROP | Konvergiert nach C-14→C-27-Ersetzung auf CS-06; erbt C-14/C-15-Lasten (cascade S-6). |
| **CS-13** Rudel-Läufer K3 | DROP | **PARK** | DROP | = Cross-Sectional Voll-Cluster (PARK); enthält C-01 (INC-02) (crosssect). |

---

## 2. REFUTED-Abschnitt — die 3 widerlegten Claims (forensische Begründungskette)

> Diese drei sind die einzigen forensisch isoliert belasteten Befunde des Registers. Sie kommen NICHT ins Framework. Wissensspeicher mit voller Kette.

### C-14 — Hawkes-Spektralradius ρ(Φ): SCHWELLE + ESTIMATOR-OUTPUT REFUTED (Konzept UNTESTED)
**Kette:** E-01 misst über alle 5 Symbole, 56k–87k Ticks (GEEIGNETES Fenster für die Distributions-Aussage): ρ-Median ≈ 2e-7 — **sechs Größenordnungen** unter dem importierten Threshold 0.85. p95 (SOL/BNB/XRP) ~6e-7; BTC/ETH-Floor-Saturation bei ~1e-3 ist laut E-01 numerisches Artefakt, kein zweiter Modus. INC-01: der Threshold 0.85 stammt aus fremder Mikrostruktur (Bacry-Mastromatteo-Muzy), nie auf Bybit-Erreichbarkeit geprüft. E-02: S1 feuert 0 Trades, Ursache `rho_below_threshold` (nicht Datenmangel — Liquidationen auf 4/5 Symbolen reichlich).
**Urteil:** Der AKTUELLE Single-Channel-ρ-Estimator + die 0.85-Schwelle sind **REFUTED** (Belastbarkeit HOCH, kein Multiple-Testing-Problem — Verteilungsbefund). Das Branching-/Reflexivitäts-KONZEPT bleibt UNTESTED und ist in C-27 (Rₜ, self-calibrating) sauber re-inkarniert. **C-14 erhält KEIN eigenes Pilot-Budget** (cascade A-4/S-4 konvergent).

### CS-01 — „Seismischer Cascade Detector" (S1): REFUTED (aktuelle Implementierung)
**Kette:** CS-01 = C-14 (ρ-Gate) + C-15 (GR+Omori) + C-26 (SIR R₀). Das ρ-Eingangsgate (C-14) erreicht den Threshold strukturell nie (E-01) → die Strategie feuert 0 Trades auf allen 5 Symbolen (E-02). Die M14-basierte Implementierung ist damit **REFUTED**. Forensik-Differenzierung (Modul≠Strategie): nur C-14 ist isoliert belastet; C-15/C-26 bleiben **SUSPECT/UNTESTED** (nie ausgelöst, weil das ρ-Gate vorgeschaltet blockierte — E-02: GR-/SIR-Glieder faktisch nie getestet, Liquidationen wären datenseitig da gewesen). Das übergeordnete Kaskaden-KONZEPT ist UNTESTED (nie ausgelöst → keine Outcome-Evidenz), Fenster für Kaskaden-Prädiktion EINGESCHRÄNKT (GM-6).
**Urteil:** Aktuelle Strategie **DROP/REFUTED**. Saubere Neugeburt = CS-06 (threshold-frei, ohne REFUTED/SUSPECT-Module).

### CS-02 — „Entropie-Momentum" (S2): REFUTED (einzige eindeutig widerlegte Strategie)
**Kette (drei unabhängige Forensiken aus GEEIGNETEN Fenstern):**
1. **E-03 (Maker-Only, schärfster Test):** Roh-Edge negativ auf JEDEM Symbol auch ohne Fees — BTC -3.61, ETH -3.71, SOL -3.99, BNB -1.65, XRP -4.06; Aggregat -3.45 bps. Selbst bei 0 Friktion verliert jedes Symbol roh.
2. **E-04 (Mirror-Test):** hit_sum = 0.179 ≠ 1.0; Inversion macht es schlimmer (-3.45 → -4.55). → S2 ist NICHT anti-prädiktiv invertierbar, sondern **execution-loss-bound** (doppelseitige Slippage RMS 8.0 bps BTC/ETH).
3. **E-16:** Friktion dominiert Richtung ~35× (iter-2-Inversions-Delta).
**Modul-Implikation (Modul≠Strategie):** C-06 bleibt PARTIAL (Gate feuert messbar, E-05); C-01/C-07 bleiben SUSPECT (Beitrag nie isoliert). **KEIN Modul wird durch CS-02 automatisch REFUTED.** Wichtig fürs Verdict: Die simple Sign-Flip-MR-Rehabilitierung von C-06 ist durch E-04 bereits gescheitert — nur eine NICHT-triviale MR-Hypothese (separates Folge-Signal) bleibt als C-06-PILOT offen.
**Urteil:** Strategie **DROP/REFUTED**, Belastbarkeit HOCH (5 Symbole konsistent, schärfster Test bestanden).

---

## 3. Bedingtes Urteil CS-03 / Funding (E-15-PENDING)

CS-03 und der C-22-Entry hängen am laufenden iter-5-Run (E-15). Tore werden hier VORAB festgelegt (judge.md #3 — kein Verschieben):

**CS-03 (S3) — BEDINGTES PILOT:**
- **Gate 1 (E-15-Resultat, erstes Tor):** iter-5 liefert die in E-15 erwarteten Deltas: time_stop 1→60–70, n>120s 68→~0, n<-30bps 33→~0.
- **→ PILOT-fortführen (Richtung ADOPT-Kandidatur), falls** iter-5 mean pnl_bps netto **≥ -5** (signifikante Hebung der -16.81) UND E-17-Widerspruch (iter-3 -2113$ vs iter-4 -6857$) durch Roh-PnL-Export beider Runs aufgelöst (funding S-1, verschärft). Erst dann Folge-Gate: PRD-kestrel-Schwelle Sharpe ≥1.2 / WR ≥55 % / PF ≥1.3 über ≥200 Trades walk-forward (≥L2).
- **→ DROP/PRD-Redesign, falls** iter-5 mean pnl_bps netto **bleibt ≤ -10** ODER der Bug-Fix die Tail-/Time-Stop-Metriken nicht wie erwartet bewegt (Time-Stop feuert weiterhin <10×). Dann ist die negative Roh-Edge (-5.8 bps) NICHT exit-, sondern entry-/edge-knappheits-bedingt bestätigt → CS-03 fällt.
- **Graubereich (-10 < netto < -5):** PILOT bleibt, aber nur gekoppelt an C-37-Friktions-Hebel (s.u.) — ohne 7-bps-Friktionssenkung strukturell nicht heilbar.

**C-22 (Entry) — PILOT unabhängig vom CS-03-Exit:** settlement-event-gebundener (`n_settlement_events`, nicht `n_in_window`) Isolationstest, Pressure-Threshold Q97/Q99, FDR-korr. über Quantil-Varianten; Erfolg: Roh-Edge > 0 vor Friktion auf ≥3 Symbolen. Scheitert → INC-03-Edge-Knappheit bestätigt.

**C-37 (Friction-Killer) — PILOT, der CS-03 retten kann:** Live-Mikro-Pilot über /v5/spread/*; Gate: Maker-Quote ≥70 % UND realisierter Round-Trip ≤6 bps SPEZIELL in Pressure-Release-Fenstern (nicht Tagesdurchschnitt). Verfehlt → C-37 DROP, gesamter Funding-Cluster bleibt friction-bound.

**Kipp-Punkt-Logik (beide Debattenseiten einig):** Liefern E-15 (netto-positiv) UND C-37 (4-bps real) zusammen, kippt die Kernrelation für DIESEN Cluster → C-22/CS-12 werden ADOPT-fähig (frühestens nach L2-Walk-Forward). Liefert keines → Cluster fällt auf PARK.

---

## 4. Priorisierung — Welle-1-Pilots (Ressourcen-Realismus: Einzelbetreiber)

**Prinzip:** Max. 3–5 Pilots parallel (judge.md #5). Rangkriterien: (1) Evidenznähe, (2) Kosten/Aufwand invers, (3) Zeitkritikalität, (4) Sequenzierungs-Zwänge aus den Debatten, (5) Hebel (schaltet mehrere Claims frei). Drei harte Sequenzierungs-Zwänge sind nicht verhandelbar:
- **E-15-Resultat VOR allen S3-Folgeentscheidungen** (CS-03, C-22-Exit, C-08-Ockham-Test, RV-Stop, Vol-Targeting).
- **C-42-Reproduktion VOR allen Vol-Stack-Derivaten** (C-10, C-35, C-34, C-11/C-12-ΔR²-Gates messen sonst gegen ein Phantom).
- **Recording-Start (C-36) VOR allen recording-abhängigen Pilots** (C-39, C-40, C-33-Options, C-02, IV-Surface).

### Welle 1 — die 4 parallelen Pilots (Hypothesen-Gate-Budget = 4, FDR-kontrolliert)

| Rang | Pilot | Aufwand | Warum jetzt / Gate (Kurz) |
|---|---|---|---|
| **1** | **E-15 abwarten + auswerten (CS-03/C-22)** | bereits laufend (S) | Einzige real feuernde Strategie mit forensisch lokalisiertem, reparierbarem Verlust. Kein Neu-Aufwand — Run läuft. Tore in §3. Höchste Evidenznähe. |
| **2** | **C-42-Reproduktion** (LightGBM/HAR-RV, purged-WF L2, ≥2 OOS-Fenster, FDR über 36 Features) | klein–mittel (1–2 Wo, Kline vorhanden) | Einziger positiver OOS-Befund; Pflicht-Vorbedingung des gesamten Vol-Stacks. Gate: OOS-R² ≥ 0.15 + QLIKE schlägt naive HAR. Schaltet C-10/C-35/C-11/C-12/C-34/VRP-RV-Bein frei. |
| **3** | **C-36 Recording-Engine starten (gedeckelt)** | klein Build (2–3 Tage) + Dauerbetrieb | Zeitkritisch + höchster Hebel: schaltet C-39/C-40/C-33-IV/C-02/IV-Surface frei. ABER mit Storage-Deckel + F0-Recall-Gate (≥95 %, 2–4 Wo) + Sunset-Review (3 Mon.). Recorder läuft passiv parallel. |
| **4** | **C-31 CFAR-Erreichbarkeits-/Handelbarkeits-Test** | klein (Surrogate + Latenz/Edge-Check) | Einziges billiges, eigenständiges, friktions-ehrliches, basis-unabhängiges Falsifikations-Gate des Regime-Clusters. Gate: Surrogate p≤0.05 + Lead>50 ms + Edge>11 bps. Schnell DROP-bar. |

**Begründung der Auswahl gegen Alternativen:** C-31 vor C-16 (C-16 datenhungriger, 5y-Bibliothek — regime S-A4). C-42-Repro vor allen Vol-Modulen (Sand-Baseline, volstack S-1). Recording vor Cascade/Options-Pilots (datenleer ohne Vorlauf). Cross-Sectional-Panel-Harness explizit NICHT in Welle 1 (S4/S5-Falle, Fee-Verdopplung, abgegraste Anomalie — crosssect S-5/S-3/S-2).

### Welle 2 — sequenziell NACH Welle-1-Gates (je 1 Vorbedingung erfüllt)

| Pilot | Entsperr-Bedingung |
|---|---|
| C-10 / C-35 (RV-Features) | nach C-42-Reproduktion (ΔR²-Gate; C-35 zusätzlich Lookahead-KILL-Gate) |
| C-08 BOCPD (Ockham-Test) | nach E-15: nur falls Time-Stop den E-10-Tail NICHT schneidet |
| C-27+C-28 (= 1 Test) + C-29 (Cascade / CS-06) | nach Recording-Vorlauf (Bulk-Historie ≥30 Kaskaden) + ω_s-Stabilitäts-Test + E-01-analoger Distributions-Check auf Intervall-Untergrenze |
| C-33 VRP (Options) | nach ≥12-Mon.-Recording mit ≥1 Stress-Periode (NICHT 3 Mon.) + Netto-Roll-Gate + Tail-Cap-Klausel |
| C-37 Spread-Execution | nach E-15 (nur sinnvoll, wenn CS-03 in den Graubereich kommt) |
| C-06 / C-07 / C-01 (Mikrostruktur-Gates) | C-01 erst nach INC-02-Vorzeichen-Test; C-06 nur NICHT-triviale MR; C-07 nur falls ρ-Vorprüfung ≥0.3 |
| Cross-Sectional 2-Symbol-Mess-Gate | nach Welle 1 (E-15/C-42), kapitalfrei, NUR Lead-Lag-Existenz prüfen |

---

## 5. Multiple-Testing-Budget (judge.md #4)

**Problem:** GM-2 — keine FDR/Bonferroni in irgendeiner Quelle; 3 Iter × 5 Symbole × 5 Strategien × 2 Arme bereits unkorrigiert. Über alle PILOT/PARK summieren sich ~25 potenzielle Hypothesen-Gates.

**Festlegung:**
1. **Welle-1-Parallelität gedeckelt auf 4 Hypothesen-Gates** (Tabelle §4). Davon sind 2 reine Infrastruktur/Reproduktion (E-15-Auswertung, C-42-Repro, C-36-Recording) — also nur **C-31** ist ein echter neuer Edge-Hypothesentest in Welle 1. Effektives neues Alpha-Test-Budget Welle 1 = **1**. Das hält das FDR-Risiko minimal.
2. **FDR-Korrektur (Benjamini-Hochberg, α=0.10) verpflichtend** über jede Familie parallel getesteter Varianten:
   - Funding-Familie (C-22-Quantilvarianten, C-32, C-23) — gemeinsame FDR.
   - Vol-Feature-Familie (C-10, C-35, C-11, C-12 ΔR² gegen C-42) — gemeinsame FDR.
   - Cascade (C-27+C-28 = EIN Test, nicht zwei — geteilter ω_s-Kernel; C-29 separat).
   - Cross-Sectional Konditionierungs-Suche (vor dem finalen FDR-Gate, nicht nur darin).
3. **Schwellen-Verschärfung wegen Peso/L0:** Da alle Erstläufe L0/Single-Pass sind, gilt: ein einzelnes „> Schwelle in 2 Fenstern" zählt NICHT als bestanden ohne walk-forward (≥L2). Insbesondere VRP (C-33): 3-Monats-Verdikt ist Peso-verzerrt → Schwelle = ≥12 Mon. mit Stress-Periode (options S-2).
4. **Hartes Ein-Fenster-Abbruchkriterium beibehalten** (C-27/C-28/C-29/C-32/C-16): Schwelle in EINEM disjunkten Fenster verfehlt → DROP, kein Nachverhandeln.

---

## 6. Abgleich mit Vorab-Urteilen (P-01 / P-02)

Eigene Urteile oben UNABHÄNGIG aus Alignment + Debatten hergeleitet. Hier der Pflicht-Abgleich.

| Claim/Strat | P-01 (CONCEPT_REVIEW) | P-02 (PRD_VS_REALITY) | Mein Urteil (F) | Übereinstimmung / Abweichung |
|---|---|---|---|---|
| CS-01 (S1) | UNTESTABLE | **ABANDON** | DROP/REFUTED (Implementierung); Konzept→C-27 | **Übereinstimmung** (unabhängig via E-01/E-02). Nuance: ich trenne REFUTED-Implementierung von UNTESTED-Konzept schärfer als P-02 („ABANDON"). |
| CS-02 (S2) | BROKEN (thesis inverted) | **ABANDON** | DROP/REFUTED | **Übereinstimmung.** ABER: P-01s „inverted = Mean-Reversion-Signal" ist durch E-04 (hit_sum 0.179, Inversion schlimmer) **widerlegt** — die simple MR-Lesart trägt nicht. Das ist eine **inhaltliche Korrektur an P-01**: nicht „Signal invertieren", sondern „Signal ist Rauschen, nur NICHT-triviale MR offen". |
| CS-03 (S3) | CONFIRMED entry / BROKEN exit | **PROMISING** (pending iter-5) → MODIFY | PILOT bedingt (Gate E-15, §3) | **Teil-Abweichung:** Ich übernehme P-01s „CONFIRMED entry" NICHT — C-22-Entry ist „nie isoliert gemessen" und INC-03 beschädigt die Settlement-Selektivität; Entry ist symmetrisch UNTESTED, nicht confirmed (funding S-2). Mein Urteil ist konservativer als P-01, deckt sich aber mit P-02s „pending iter-5". |
| CS-04 (S4) | UNTESTABLE | UNTESTED | PARK (Loader-Fix = Negativexp.) | **Übereinstimmung.** Zusatz: auf RV-Ziel erwarteter HAR-Gate-Fail → Richtung REFUTED-Doku. |
| CS-05 (S5) | UNTESTABLE | UNTESTED | PARK (Panel-Harness) | **Übereinstimmung.** Verschärfung: Voll-Cluster PARK auch wegen Fee-Verdopplung (S-3), nicht nur Harness. |
| C-14 (M14) | ρ-Threshold-Problem | ABANDON aktuelle Form | REFUTED (Schwelle+Estimator), Konzept→C-27 | **Übereinstimmung.** |
| C-01 (OFI) | — | **SUSPECT** | PILOT nur nach INC-02-Test (sonst DROP) | **Übereinstimmung** mit P-02; ich präzisiere die Entsperr-Bedingung (Vorzeichen-Test). |
| C-22 (M22) | (entry confirmed) | **NEEDS INSTRUMENTATION** | PILOT (Isolationstest) | Näher an P-02 als P-01; **Abweichung von P-01** (nicht confirmed). |
| C-08 (BOCPD) | — | **NEEDS INSTRUMENTATION** | PARK (Ockham, gegen iter-5-Baseline) | **Abweichung/Verschärfung:** ich gehe über „instrumentieren" hinaus — C-08 muss gegen den trivialen Time-Stop antreten (regime S-A1); evtl. überflüssig (Ockham), nicht nur uninstrumentiert. |

**Neu vom Judge bewertet (in P-01/P-02 nicht enthalten):** Alle C-27..C-43, CS-06..CS-13, C-42, C-33-VRP, C-36-Recording — unabhängig aus claims_register + Debatten hergeleitet (P-01/P-02 deckten nur S1–S5 + Kernmodule). Kein Ankern an Vorab-Urteilen, da diese hierzu schweigen.

**Systemische P-02-Befunde übernommen:** fehlende Bounded-Loss-Policy (→ §3), 100 %-Long-Bias S2/S3 (→ E-06/E-12, Long-Short-Argument C-13), Friction-vs-Holding-Horizon-Constraint (→ Kernrelation §0.2, durchgängig).

---

## 7. Überraschungen / Querschnitt (judge.md #6)

- **C-42 ist der einzige positive OOS-Befund** und war in keiner Strategie-Niederlage verbaut — er ist faktisch ein „Evidenz-ohne-erfolgreiche-Strategie"-Fall. Behandlung: zum Anker der Welle 1 gemacht (Reproduktion Rang 2), NICHT als ADOPT (unreproduziert).
- **C-36/Recording ist kein Alpha, aber der höchste Infrastruktur-Hebel** — als gedeckelter PILOT (nicht ADOPT) ins PRD, mit Sunset-Review, damit kein ungedeckelter Data-Lake entsteht.
- **VRP (C-33) ist der einzige strukturell INC-05-immune Edge** — verdient den einzigen Options-PILOT, aber unter verschärftem Tail-/Roll-/Stress-Gate.

---

## 8. Verdikt-Verteilung (Zählung)

Gezählt über Claims × Märkte für alle **nicht-REFUTED** Claims (REFUTED separat). Pro Zelle ein Urteil. „kM/n/a" als DROP gezählt.

| Urteil | Anzahl (Zellen) | Schwerpunkt |
|---|---|---|
| **ADOPT** | **0** | keiner (CONFIRMED unerreichbar, GM-1) |
| **PILOT** | ~16 Futures-Zellen + wenige S/O | C-42(F/S), C-06(F), C-22(F), C-27(F), C-28(F), C-29(F), C-37(F), C-32(F), C-20(F), C-36(F/S), C-31(F), C-16(F), C-07(F), C-01(F), C-10(F/S), C-35(F/S), C-33(O), CS-03(F bedingt), CS-06(F), CS-09(F dekomponiert) |
| **PARK** | ~25 | Cross-Sectional-Cluster, C-08/C-11/C-12/C-25/C-40/C-43/C-34/C-23/C-38/C-39/C-30, Vol-Targeting/RV-Stop, CS-04/05/07/08/10/11/12/13, C-33-Hedge |
| **DROP** | ~70 (überwiegend Spot/Optionen kM) | alle Spot-Zellen kaskaden/funding/mikrostruktur; C-24(F), C-18(F), C-19(F); + REFUTED unten |
| **REFUTED** (eigener Abschnitt) | 3 Claims | C-14, CS-01, CS-02 |

**Markt-Muster:** Spot durchgehend DROP (kein Mechanismus außer C-42-RV/C-23-Basis-PARK); Optionen DROP außer C-33-PILOT; **alle echten Pilots sind Futures-Perp** (plus C-42-Spot, C-33-Optionen).

---

*Ende verdict.md*
