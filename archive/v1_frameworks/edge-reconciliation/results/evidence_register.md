# Evidence Register — Edge Reconciliation Framework
**Phase:** 2 — EVIDENCE_AUDIT
**Stand:** 2026-06-11
**Erstellt von:** evidence-auditor
**Quellen (Primär-Evidenz):**
- `input/ANALYSIS_REPORT_iter2.md` (Replay-Baseline iter-2, default vs `--invert-strategies S2,S3`, commit a77a366)
- `input/ANALYSIS_REPORT_iter3.md` (iter-3 Original-Arm, 5 Symbole, S1–S5)
- `input/ANALYSIS_REPORT_iter4.md` (iter-4 Push A Forensik: S1 ρ, S2 Maker-Only, S3 Bounded-Loss)
- `input/INVERTED_COMPARISON_iter3.md` (Mirror-Test S2/S3)
- `input/iter4_raw/replay_all_results.json` (Aggregate + Diagnostics, run 2026-06-10T02:26:03Z)
- `input/iter4_raw/rho_distribution_*.json` (5 Symbole, ρ-Quantile)
- `input/iter4_raw/trades_all.csv` (403 Trades roh; eigenständig nachgerechnet)

Sekundär-Urteile (P-01 STRATEGY_CONCEPT_REVIEW_iter3, P-02 PRD_VS_REALITY_SYNTHESIS) wurden NUR zur Lokalisierung gelesen; ihre Verdikte sind **nicht** als Evidenz registriert.

---

## GLOBALE METHODISCHE RAHMENBEDINGUNGEN (gelten für ALLE E-xx)

Diese Vorbehalte gelten transversal und werden bei den Einzeleinträgen nicht jedes Mal wiederholt:

- **GM-1 — Alles ist Replay/In-Sample (L0).** Jede Messung stammt aus einem `single_pass`-Replay über ein einzelnes ~24h-Fenster pro Symbol (~56k–88k Ticks). Es gibt **keinen** Train/Test-Split (L1), **kein** Walk-Forward / Purged CV (L2), **kein** Paper-/Live-Trading (L3). Maximale Validierungsstufe im gesamten Register: **L0**. Kein einziger Befund kann einen Claim auf CONFIRMED heben.
- **GM-2 — Multiple Testing.** 3 Iterationen (iter-2/3/4) × 5 Symbole × bis zu 5 Strategien × 2 Richtungs-Arme. Keine FDR-/Bonferroni-Korrektur in irgendeiner Quelle. Jeder „signifikant" wirkende Einzelbefund (z.B. 6.8% Hit-Rate) ist unkorrigiert.
- **GM-3 — qty = 1.0 Unit, nicht USD-notional.** `_make_trade` hardcodet `qty=1.0`. Cross-Symbol-Aggregate (`weighted_sharpe`, `total_return`) gewichten BTCUSDT ~50.000× stärker als XRPUSDT. Aggregate sind faktisch das BTC-Ergebnis. Symbol-übergreifende $-Summen sind NICHT interpretierbar; nur bps-Größen sind cross-symbol vergleichbar.
- **GM-4 — Single-Pass, kleine N.** Pro Symbol N=11–71 (S2), 16–62 (S3). Sharpe-Punktschätzer ohne CI/Bootstrap/Dispersion. |Sharpe|-Werte (-5 bis -88) sind durch Friktions-Determinismus (kleine Varianz) aufgebläht und NICHT als „invertierte Edge" lesbar.
- **GM-5 — Within-Sample-Kontamination.** Rolling-Referenzstatistiken (`_pressure_history`, `_entropy_history`, maxlen 50.000) werden VOR dem Gate-Check auf demselben Tick angehängt. Aktuelle Beobachtung ist in ihrer eigenen Referenz enthalten. Impact ~1/50k — numerisch vernachlässigbar, methodisch unsauber.
- **GM-6 — Testfenster-Eignung generell EINGESCHRÄNKT.** ~24h enthalten nur 3 Settlement-Zyklen/Symbol und keine garantierte Stress-/Kaskaden-Episode. Fenster kann Kaskaden-/Settlement-Claims nicht zuverlässig falsifizieren, nur Nicht-Feuern zeigen.

---

## KOSTENBASELINE (verbindlich für Advocate/Skeptic/Judge)

Aus den Quellen dokumentierte Friktionswerte — verbindlich zu verwenden, keine Schätzungen:

| Posten | Wert | Quelle |
|---|---|---|
| Taker-Fee (je Leg) | 0.00055 = **5.5 bps** | iter2 §1.3 (`FEE_TAKER=0.00055`) |
| Taker-Fee Round-Trip | **11.0 bps** auf Notional | iter3 §1, iter4 §4; CSV-nachgerechnet: S3 mean_fee_bps = **10.997** |
| Slippage (je Leg) | 2.0 bps adverse | iter2 §1.3 (`SLIPPAGE_DEFAULT_BPS=2.0`) |
| Slippage Round-Trip (Preis) | ~4 bps | iter2 §1.3 |
| **Round-Trip-Friktion gesamt** | **≈ 15 bps** of entry notional (qty=1) | iter2 §1.3 |
| Maker-Only (iter-4 S2-Run) | **0 bps** (entry_fee=exit_fee=0; CSV bestätigt alle 190) | iter4 §1, §3; CSV |
| Double-sided Slippage-Tax (S2 Mirror) | RMS(raw_o+raw_i) BTC=8.0 bps, ETH=8.0 bps | INVERTED §1 |
| Maker-Round-Trip (PRD-Referenz, Spread-Markt) | ~4 bps (nicht gemessen, Claim C-37) | claims_register (Kontext) |
| Options-Taker-Fee (PRD-Referenz) | 0.03% (nicht gemessen) | claims_register C-33 |

**Kernrelation:** Round-Trip-Friktion 11 bps (taker) bzw. 15 bps (inkl. Slippage) übersteigt jede gemessene Roh-Edge (max. |Roh| ≈ 4–7 bps Mittel pro Symbol). Friktion > Signal auf jeder gemessenen Strategie.

---

## TEIL A — S1 (CS-01 / C-14 Hawkes ρ): ρ-Distribution

### [E-01] ρ-Verteilung ist unimodal bei ~2×10⁻⁷ — sechs Größenordnungen unter Threshold 0.85
- **Quelle:** `iter4_raw/rho_distribution_*.json` (alle 5); `ANALYSIS_REPORT_iter4.md` §2
- **Metrik & Wert:** Median (p50) ρ je Symbol: BTC 2.13e-7, ETH 2.05e-7, SOL 1.92e-7, BNB 1.84e-7, XRP 1.94e-7. Threshold = **0.85**. Distanz Median→Threshold ≈ **6 Größenordnungen**.
  - p95: SOL 6.02e-7, BNB 5.59e-7, XRP 5.75e-7 (alle ~6 Größenordnungen unter Threshold). BTC/ETH p90/p95 springen auf ~9e-4/1e-3 (numerischer Floor-Saturation), max BTC 9.40, ETH 7.16, XRP 0.49 — isolierte Einzelspikes, kein zweiter Modus.
- **Datengrundlage:** 5 Symbole, n_samples 56.425 (BNB) – 87.379 (SOL), ~24h-Fenster.
- **Validierungsqualität:** L0 (in-sample, instrumentierte Verteilungsmessung, kein Trade-Outcome).
- **Testfenster-Eignung:** GEEIGNET (für die Distributions-Aussage). Eine ρ-Verteilung über 56k–87k Ticks ist für die Frage „erreicht ρ je 0.85?" ausreichend; das Fenster KANN diese Spezifik-Aussage falsifizieren und tut es eindeutig. (Für den übergeordneten Kaskaden-PRÄDIKTIONS-Claim bleibt das Fenster EINGESCHRÄNKT, da keine garantierte Kaskade enthalten ist — siehe E-03.)
- **Kosten:** N/A (kein Trade).
- **Methodische Schwächen:** Misst den Estimator-Output, nicht ob „echte Kaskaden" im Fenster lagen. BTC/ETH-Floor-Saturation bei 0.001 deutet auf numerische Artefakte im oberen Quantil. Single-Channel-Hawkes; Aussage gilt nur für DIESEN Estimator.
- **Belastbarkeit:** HOCH (für die enge Aussage „der aktuelle ρ-Estimator erreicht den Threshold strukturell nie"). Konsistent über alle 5 Symbole, kein Multiple-Testing-Problem (Verteilungsbefund, kein Signifikanztest).

### [E-02] S1 feuert 0 Trades — Grund ist rho_below_threshold, nicht Datenmangel
- **Quelle:** `replay_all_results.json` (S1 total_trades=0; diagnostics reason_counts); iter3 §S1; iter4 §1.
- **Metrik & Wert:** S1 n_trades = 0 auf allen 5 Symbolen, alle Iterationen. `rho_below_threshold`: BNB 56.425, BTC 83.482, ETH 80.525, SOL 87.379, XRP 86.088 (≈67–99% aller Ticks). `liquidations_below_min_events` nur BNB relevant (28.192 = 33%). Weitere: BTC `rho_not_rising` 111, `b_value_not_extreme` 4; ETH analog klein.
- **Datengrundlage:** 5 Symbole, ~24h, ~81k–88k Ticks/Symbol.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** EINGESCHRÄNKT — Null-Trades zeigen nur Nicht-Feuern; ohne Kaskaden-Episode im Fenster lässt sich der Detektor nicht WIDERLEGEN, nur als „nicht ausgelöst" feststellen. Die Kombination mit E-01 (Estimator strukturell zu niedrig) macht das Nicht-Feuern aber estimator-bedingt erklärbar, nicht fenster-bedingt.
- **Kosten:** N/A.
- **Methodische Schwächen:** Liquidationen sind reichlich vorhanden (außer BNB), d.h. NICHT data-bound, sondern parametrisch/estimator-bound. `unknown`-Counts (iter-2 erwähnt 28k BNB) = Diagnostik-Blindfleck.
- **Belastbarkeit:** HOCH (Nicht-Feuern + Ursachenlokalisierung); negatives Ergebnis.

---

## TEIL B — S2 (CS-02 / C-06,C-01,C-22,C-07 Entropie-Momentum): Forensik-Kette (NEGATIV)

### [E-03] S2 Roh-Edge negativ auf JEDEM Symbol, auch ohne Fees (Maker-Only-Run, iter-4)
- **Quelle:** `ANALYSIS_REPORT_iter4.md` §3; `trades_all.csv` (190 S2-Trades, alle Fees=0 — CSV-bestätigt); `replay_all_results.json` S2.
- **Metrik & Wert:** mean pnl_bps (= Roh-Edge, da Fee=0): BTC **-3.61**, ETH **-3.71**, SOL **-3.99**, BNB **-1.65**, XRP **-4.06**; Aggregat **-3.45 bps**. Min/Max bps: BTC -11.13/+7.92, BNB -10.62/+12.76. Raw-positive Hit-Rate: 7–13% (BTC/ETH/SOL/XRP), 35% BNB. Aggregat-Win-Rate (JSON `mean_win_rate`) = 0.1211.
- **Datengrundlage:** 5 Symbole, N=190 (26/59/71/11/23), ~24h.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** GEEIGNET — S2 feuert 11–71×/Symbol; genug Trades, um „hat eine Roh-Edge" zu falsifizieren. Maker-Only ist der schärfste Test (worst-case-für-Hypothese: 0 Fees), und die Edge bleibt negativ.
- **Kosten:** Fees = 0 (Maker-Only). Selbst ohne jede Friktion verliert jedes Symbol roh.
- **Methodische Schwächen:** GM-2 (unkorrigiert), GM-4 (kleine N, v.a. SOL N=11), GM-5. Maker-Only setzt unrealistisch Fill ohne Queue-Risiko voraus (optimistisch); reale Maker-Fills wären nicht garantiert.
- **Belastbarkeit:** HOCH (negatives Ergebnis, über 5 Symbole konsistent, schärfster Test bestanden = Edge widerlegt).

### [E-04] S2 ist NICHT anti-prädiktiv — Mirror-Test scheitert (Inversion macht es schlimmer)
- **Quelle:** `INVERTED_COMPARISON_iter3.md` §1; iter2 §1.2/§3.2 (Mechanik der Inversion bestätigt korrekt).
- **Metrik & Wert:** Aggregat raw_bps original **-3.45** → invertiert **-4.55** (mirror ratio **-1.32**; perfekter Mirror wäre +1.0). Hit-Rate original 0.121 → invertiert 0.058; **hit_sum = 0.179** (bei echtem Sign-Flip müsste ~1.0 herauskommen). Trade-by-trade RMS(raw_o+raw_i) BTC=8.0, ETH=8.0 bps = doppelseitige Slippage. Inversions-Mechanik korrekt: 190 Trades in beiden Armen identisch (S2-Flag flippt nur Emissions-Richtung, nicht die Gates — iter2 §1.2).
- **Datengrundlage:** 5 Symbole, N=190, beide Arme, ~24h.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** GEEIGNET — symmetrischer Replay testet die Anti-Prädiktiv-Hypothese direkt; sie scheitert sauber.
- **Kosten:** Fees 11 bps round-trip identisch beide Arme (CSV/Report bestätigt zu 3 Dezimalstellen).
- **Methodische Schwächen:** Die iter-3-„anti-prädiktiv"-Lesart (6–8% Hit) war Artefakt des Konditionierens auf negative Outcomes; der Mirror-Test korrigiert sie. GM-2/GM-4.
- **Belastbarkeit:** HOCH. Schlüsselzahl: **hit_sum = 0.179 ≠ 1.0** → S2 ist execution-loss-bound, nicht direction-bound. Negatives Ergebnis.

### [E-05] S2 Entry-Funnel: Entropie-Kollaps-Gate ist der dominante Filter (~97% der Ticks)
- **Quelle:** `replay_all_results.json` diagnostics S2; iter2 §2.1, iter3 §4.
- **Metrik & Wert:** `entropy_not_collapsed`: BNB 81.302, BTC 82.391, ETH 78.912, SOL 84.785, XRP 86.523 (~97% aller Ticks). Sekundär `ofi_below_q90` 1.430–3.166; tertiär `pressure_ofi_misaligned` 117–187, `pe_no_greenlight` 39–102. `__enter__` 11–71. Roh-Hit-Rate bei Feuern (iter3 §4): BTC 6.8%, ETH 8.5% (≪50%).
- **Datengrundlage:** 5 Symbole, ~24h, ~79k–88k Ticks.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** GEEIGNET für Funnel-Charakterisierung; EINGESCHRÄNKT für „Entropie-Kollaps prädiktiv?" — 6–8% Hit auf N=59/71 ist nicht-zufällig, aber unkorrigiert (GM-2).
- **Kosten:** N/A (Funnel).
- **Methodische Schwächen:** Niedrige Hit-Rate kann „falsche Richtung" ODER „Friktion frisst Coin-Flip" sein — E-04 entscheidet zugunsten Letzterem (Signal ist Rauschen, nicht invers). Richtungs-Bias: 189/190 Long (siehe E-06).
- **Belastbarkeit:** MITTEL-HOCH (Funnel-Struktur robust; prädiktive Interpretation durch E-03/E-04 als „kein Signal" geklärt).

### [E-06] S2 ist strukturell ~100% Long (189/190 Trades Long)
- **Quelle:** `trades_all.csv` (CSV-nachgerechnet: S2 Long=189, Short=1); iter3 §1, iter4 §3.
- **Metrik & Wert:** Side-Verteilung S2: 189 Long, 1 Short (einziger Short auf XRP). Pro Symbol: BNB 26 Long, BTC 59 Long, ETH 71 Long, SOL 11 Long, XRP 22 Long + 1 Short.
- **Datengrundlage:** N=190, 5 Symbole.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** EINGESCHRÄNKT — ob Long-Bias strukturell oder fenster-spezifisch ist, lässt sich aus EINEM ~24h-Fenster nicht entscheiden (offene Frage in P-02, hier nur als Messung registriert).
- **Kosten:** N/A.
- **Methodische Schwächen:** Long-Bias könnte window-spezifischer Drift sein; OFI-Vorzeichen-Mapping potenziell falsch orientiert (Kontext INC-02).
- **Belastbarkeit:** HOCH (reine Side-Auszählung, fakten-fest); Interpretation offen.

---

## TEIL C — S3 (CS-03 / C-22,C-23,C-24,C-08 Pre-Settlement): Bounded-Loss + Time-Stop-Bug

### [E-07] ⚠️ TIME-STOP-BUG: 120s-Time-Stop feuerte 1× statt erwartet 68× (Wall-Clock statt Tick-Zeit)
- **Quelle:** `ANALYSIS_REPORT_iter4.md` §4 Finding 2; `replay_all_results.json` diagnostics (`time_stop_exceeded`: nur BNB=1, alle anderen 0); `trades_all.csv` (CSV-nachgerechnet: 68 Trades >120s Dauer, n>120s je Symbol: BNB 14, BTC 14, ETH 13, SOL 13, XRP 14).
- **Metrik & Wert:** 68 von 213 S3-Trades (32%) > 120s Marktzeit (worst 2125s = 35 min, BNB). Time-Stop-Reason feuerte **insgesamt 1×**. **Root Cause:** `strategy3_pre_settlement.py:129` nutzt `now = time.time()` (Wall-Clock) statt Replay-Tick-Zeit; im schnellen Replay ist Wall-Clock-Δ ≈ Sekunden während Markt-Δ Minuten — `(now_wall − entry_ts_wall)*1000 > 120_000` greift fast nie.
- **Datengrundlage:** 5 Symbole, N=213, ~24h.
- **Validierungsqualität:** L0 — **und für die Time-Stop-WIRKUNG faktisch L-kein-Messwert** (das Feature lief nicht).
- **Testfenster-Eignung:** UNGEEIGNET für die Time-Stop-Hypothese — der Bug verhindert, dass die Time-Stop-Wirkung überhaupt gemessen wurde. **Dieser E-Eintrag invalidiert alle iter-4-S3-Exit-Metriken bzgl. Time-Stop.**
- **Kosten:** N/A (Implementierungs-Befund).
- **Methodische Schwächen:** Der Bug ist selbst Evidenz (Validierungs-Infrastruktur-Defekt). iter-5-Fix (Tick-Zeit) ist committet aber UNVALIDIERT → siehe E-13 (PENDING).
- **Belastbarkeit:** HOCH (Bug eindeutig isoliert, durch Daten bestätigt: 68 lange Trades vs. 1 Firing).

### [E-08] S3 Hard-Stop feuerte 13× (real gemessen), aber 33 Trades schlossen dennoch < -30 bps
- **Quelle:** `ANALYSIS_REPORT_iter4.md` §4 Finding 1; `replay_all_results.json` diagnostics (`hard_stop_loss`: BNB 6, BTC 2, SOL 3, XRP 2, ETH 0 = **13** gesamt); `trades_all.csv` (CSV-nachgerechnet n<-30bps: BNB 8, BTC 5, ETH 7, SOL 9, XRP 4 = **33**).
- **Metrik & Wert:** Hard-Stop-Firings = 13 (4 von 5 Symbolen; ETH=0). Dennoch 33 Trades (15%) mit pnl_bps < -30. **Ursache:** Hard-Stop misst Roh-MTM gegen Entry, aber `pnl_bps` ist NETTO (− ~11 bps Friktion); ein Trade, der via `pressure_dissipated` bei roh -20 bps schließt, zeigt netto ≈ -31 bps. Threshold zu locker bzw. friktion-unbewusst.
- **Datengrundlage:** 5 Symbole, N=213, ~24h.
- **Validierungsqualität:** L0. (Dies ist der EINZIGE real gemessene Bounded-Loss-Mechanismus in iter-4 — Hard-Stop, nicht Time-Stop.)
- **Testfenster-Eignung:** EINGESCHRÄNKT — 13 Firings sind eine sehr kleine Stichprobe für eine Exit-Policy-Bewertung.
- **Kosten:** Friktion 11 bps round-trip ist relevant (genau der Grund für die Netto/Roh-Lücke).
- **Methodische Schwächen:** Hard-Stop fing nicht den schlimmsten BNB-Trade (-56.6 bps, Exit-Reason vermutlich `pressure_dissipated`). Threshold-Kalibrierung offen.
- **Belastbarkeit:** MITTEL (Mechanismus feuert real, aber zu locker; iter-5-Fix `friction-aware` committet, UNVALIDIERT → E-13).

### [E-09] S3 iter-4 Aggregat: mean pnl_bps = -16.81 (netto), alle Symbole negativ; total_return -6857.56 (BTC-dominiert)
- **Quelle:** `ANALYSIS_REPORT_iter4.md` §4; `replay_all_results.json` (S3 total_return -6857.555675, weighted_sharpe -19.606, mean_win_rate 0.0939; per-symbol total_return: BTC -6680.50, ETH -147.68, SOL -4.66, BNB -24.64, XRP -0.08); `trades_all.csv` nachgerechnet.
- **Metrik & Wert:** mean pnl_bps (netto) je Symbol: BTC -16.57, ETH -16.34, SOL -18.20, BNB -21.08, XRP -14.78; Aggregat **-16.81**. min bps: BNB -56.60, SOL -48.93, BTC -47.70, XRP -46.39, ETH -37.72. Netto −11 bps Friktion ⇒ Roh ≈ **-5.8 bps** (innerhalb iter-3-Band -3.31…-20.09). N=213 (BTC 62, ETH 50, SOL 36, BNB 19, XRP 46). Win-Rate netto je Symbol (JSON): BNB 0.158, BTC 0.048, ETH 0.060, SOL 0.139, XRP 0.130.
- **Datengrundlage:** 5 Symbole, N=213, ~24h.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** EINGESCHRÄNKT — Roh-Edge per Trade unverändert ggü. iter-3 (Bounded-Loss ändert Entry-Signal nicht); aber Exit-Wirkung durch Time-Stop-Bug (E-07) verfälscht. **METHODISCHER VORBEHALT: iter-4-S3-Exit-Metriken messen NUR Hard-Stop-Wirkung (13 Firings, E-08), NICHT Time-Stop-Wirkung (Bug, E-07).**
- **Kosten:** Friktion 11 bps round-trip dominiert; Roh-Edge -5.8 bps < Friktion ⇒ friction-bound.
- **Methodische Schwächen:** GM-3 (BTC = 97% des $-Total), GM-4. **⚠️ KONSISTENZ-WIDERSPRUCH: iter-4 S3 total_return = -6857.56 (BTC -6680.50) vs. iter-3 S3 total_return = -2113.26 (BTC -2042.77).** Mean bps netto iter-4 ≈ -16.8 vs. iter-3 raw -6.27. Die iter-4-Zahlen sind ~3× schlechter — teils Netto-vs-Roh, teils anderes/erweitertes Fenster (iter-4 N=213 vs iter-3 N=204) bzw. anderer Run. Beide Werte notiert; Diskrepanz markiert.
- **Belastbarkeit:** MITTEL (Roh-Edge-Größenordnung robust über Iterationen; absolute $-Zahlen wegen GM-3 + Cross-Iter-Widerspruch nur eingeschränkt).

### [E-10] S3 Tail-Signatur: schlechteste Trades sind 1.7–3.0× länger gehalten als Durchschnitt (iter-3, robust auf BTC/ETH/SOL)
- **Quelle:** `ANALYSIS_REPORT_iter3.md` §3; `INVERTED_COMPARISON_iter3.md` §3.
- **Metrik & Wert:** dur-ratio (worst-3 mean / all-trades mean), iter-3 original: BNB 2.0×, BTC 3.0×, ETH 2.4×, SOL 1.7×, XRP 2.6×. worst-1-share am Gesamtverlust: BNB 60.9%, BTC 11.2%. Mean dur (s): BNB 937, BTC 108, ETH 103, SOL 186, XRP 149. Mirror-Test (invertiert) bestätigt Tail-Signatur robust auf BTC/ETH/SOL (inv ratio BTC 2.63, ETH 5.66, SOL 2.56); BNB-Ratio kollabiert invertiert (Lang-Trades werden dort Gewinner).
- **Datengrundlage:** 5 Symbole, iter-3 N=204 (S3), beide Arme.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** EINGESCHRÄNKT — Tail-Signatur konsistent über 5 Symbole UND über beide Richtungs-Arme (das stärkt sie über reines Multiple-Testing hinaus), aber dennoch nur 1 Fenster.
- **Kosten:** Berücksichtigt (bps netto/raw getrennt ausgewiesen in iter-3).
- **Methodische Schwächen:** „Tail = lange Trades" motiviert Time-Stop — aber dessen Wirkung wurde wegen E-07 nie gemessen. GM-4.
- **Belastbarkeit:** MITTEL-HOCH (Cross-Symbol + Cross-Arm konsistent; die einzige iter-3-Evidenz, die in beiden Armen hält).

### [E-11] S3 BNB-Direction-Pocket: -195 bps-Trade spiegelt sauber zu +187 bps in der Inversion
- **Quelle:** `INVERTED_COMPARISON_iter3.md` §2.
- **Metrik & Wert:** Aggregat S3 mirror ratio **-0.28** (überwiegend symmetrisches, friktions-dominiertes Rauschen). AUSNAHME BNB: mirror **+0.60**, hit_sum 0.88. Trade-Match (worst BNB original→invertiert): -194.99→+187.14, -87.53→+79.59, -53.70→+45.74, -27.51→+19.53, -25.47→+17.49. ⇒ BNB-Tail ist **direction-specific UND tail-driven**; andere 4 Symbole friction-bound (mirror BTC -0.56, ETH -0.50, SOL -0.14, XRP -1.42).
- **Datengrundlage:** 5 Symbole, iter-3 N=204 (S3 BNB N=16), beide Arme.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** UNGEEIGNET für Generalisierung — BNB-Befund beruht auf N=16, davon 1 Trade (-195 bps) der 60% des Verlusts erklärt. Ein-Trade-Artefakt; kann „S3 ist direction-bound" weder bestätigen noch generalisieren.
- **Kosten:** Berücksichtigt.
- **Methodische Schwächen:** Extreme Kleinst-Stichprobe (N=16, 1 Outlier). iter-4 reproduzierte den -195-bps-Tail NICHT (worst BNB nur -56.6 bps) — laut iter-4 fehlte äquivalentes Stress-Moment im Fenster, nicht Bounded-Loss-Wirkung. Bestätigt Fragilität.
- **Belastbarkeit:** NIEDRIG (isolierter Ein-Trade-/Ein-Symbol-Pocket; nicht reproduziert in iter-4).

### [E-12] S3 ist ebenfalls ~100% Long; Entry-Funnel zeigt Basis-Gate als No-Op in Default-Richtung
- **Quelle:** `trades_all.csv` (CSV: S3 Long=213, Short=0); `replay_all_results.json` diagnostics S3; iter2 §1.1/§2.2.
- **Metrik & Wert:** S3 Side: 213 Long, 0 Short. Funnel (iter-4): `n_pressure_extreme == n_basis_aligned == n_all_gates_passed` auf JEDEM Symbol (BNB 19/19/19, BTC 62/62/62, ETH 50/50/50, SOL 36/36/36, XRP 46/46/46). `outside_settlement_window` 74k–81k. `n_in_window` 6.417–6.925 (~7–8% der Ticks; 30-min-Fenster/8h ≈ 6.25% erwartet). Basis-Gate ist Pass-Through, weil `sign(pressure) ≡ -sign(basis)` per Konstruktion (Code-Comment strategy3:275-278). BOCPD feuert keinen Changepoint im Fenster.
- **Datengrundlage:** 5 Symbole, N=213, ~24h.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** GEEIGNET für „Basis-Gate trägt keine Information" (Counter-Gleichheit über alle Symbole). S3-Inversion in iter-2 produzierte 0 Trades, weil das Flip das Basis-Gate von Auto-Pass zu Auto-Fail kippte (Inversions-Bug iter2 §1.1, W1) — daher S3-Mirror nur indirekt via iter-3-Daten.
- **Kosten:** N/A (Funnel).
- **Methodische Schwächen:** Basis-Gate (C-23) und BOCPD (C-08) sind in S3 effektiv dekorativ/nie ausgelöst → diese Module wurden in S3 NICHT real getestet (SUSPECT-Kandidaten für Phase 3). INC-03: S3 feuert 50–62 Trades/24h, weit mehr als das Settlement-Framing (3 Settlements/Tag) impliziert → Q90-Threshold übertriggert.
- **Belastbarkeit:** MITTEL-HOCH (Funnel-Gleichheit fakten-fest; Modul-Implikationen für Phase 3).

---

## TEIL D — S4 / S5: Mess-Lücken (keine Trades, Infrastruktur-Blocker)

### [E-13] S4 (CS-04 / C-18 PatchTST-Ensemble): 0 Trades — insufficient_models 96–99.99% (architektur-/loader-bound)
- **Quelle:** `replay_all_results.json` (S4 total_trades=0; diagnostics `insufficient_models`: BNB 84.607, BTC 84.389, ETH 81.358, SOL 88.255, XRP 88.403; `insufficient_price_history` 2–10); iter3 §S4, iter4 §1.
- **Metrik & Wert:** S4 n_trades = 0 alle Symbole/Iterationen. `insufficient_models` deckt ≈96–99.99% aller Ticks. `data_limited: true`.
- **Datengrundlage:** 5 Symbole, ~24h.
- **Validierungsqualität:** L0 — faktisch **keine Messung der Strategie** (Modell-Layer produziert keine Prädiktionen).
- **Testfenster-Eignung:** UNGEEIGNET — Strategie lief nie; mehr Daten helfen nicht. Reine Infrastruktur-Lücke (Modell-Artefakt fehlt/nicht verdrahtet/Symbol-Key-Mismatch).
- **Kosten:** N/A.
- **Methodische Schwächen:** **MESS-LÜCKE.** S4 und alle konstituierenden Module (C-05 FFD, C-16 TFSAX, C-20 MOMENT, C-18 PatchTST) sind in dieser Strategie UNGETESTET. PatchTST-Vol-Baseline R²=0.25 stammt separat aus research_notes (C-42), nicht aus diesem Replay.
- **Belastbarkeit:** HOCH (für die Tatsache „nicht getestet"); kein Outcome-Befund.

### [E-14] S5 (CS-05 / C-13,C-17,C-09 Cross-Sectional): 0 Trades — single_symbol_replay_unsupported 100% (harness-bound by design)
- **Quelle:** `replay_all_results.json` (S5 total_trades=0; diagnostics `single_symbol_replay_unsupported` = n_ticks_total auf jedem Symbol: BNB 84.617, BTC 84.391, ETH 81.362, SOL 88.263, XRP 88.407 = **100%**); iter3 §S5, iter4 §1.
- **Metrik & Wert:** S5 n_trades = 0. `single_symbol_replay_unsupported` = 100% aller Ticks, identisch über alle Symbole.
- **Datengrundlage:** 5 Symbole, ~24h.
- **Validierungsqualität:** L0 — keine Messung möglich.
- **Testfenster-Eignung:** UNGEEIGNET — Single-Symbol-Replayer kann Cross-Sectional-Logik prinzipiell nicht ausführen. Braucht Panel-Daten-Loader, keinen Code-Fix in der Strategie.
- **Kosten:** N/A.
- **Methodische Schwächen:** **MESS-LÜCKE (architektonisch).** S5 + Module C-13 (Cross-Sectional-Z), C-17 (Renyi-TE), C-09 (HMM) komplett UNGETESTET.
- **Belastbarkeit:** HOCH (für „strukturell nicht testbar im aktuellen Harness").

---

## TEIL E — PENDING (iter-5, committet aber empirisch UNVALIDIERT)

### [E-15] PENDING — iter-5 S3-Code-Fixes (Time-Stop Tick-Zeit + Hard-Stop friction-aware): committet, User-Run läuft
- **Quelle:** Auftragskontext (Orchestrator); `ANALYSIS_REPORT_iter4.md` §5 (iter-5-Scope); P-02 (CS-03 PROMISING pending iter-5).
- **Status:** **PENDING** — Code committet, empirisch noch nicht gemessen (User-Run läuft zum Stichtag 2026-06-11).
- **Was der Run beantworten soll:**
  1. Time-Stop-Fix (`now = ts_ms/1000.0` statt `time.time()`): erwartet ~60–70 Time-Stop-Exits statt 1; drastische Reduktion von `n>120s` (aktuell 68). **Erst dieser Run misst die Time-Stop-Wirkung, die iter-4 wegen E-07 NICHT gemessen hat.**
  2. Hard-Stop friction-aware (Threshold auf `-20 bps raw` oder `raw_mtm + projected_round_trip_fee < -30 bps`): soll die 33 sub-(-30bps)-Trades (E-08) absorbieren.
  3. Messung: wird aggregate mean pnl_bps nach Bounded-Loss-Fix netto-positiv? Falls ja = erste Strategie mit gemessener Edge (gated Push C / Demo). Falls nein = PRD-Redesign.
- **Validierungsqualität:** N/A (kein Ergebnis). Stützt KEINEN Status; macht sichtbar, dass jedes iter-4-S3-Exit-Urteil vorläufig ist.
- **Belastbarkeit:** N/A.

---

## TEIL F — Cross-Iteration-Konsistenz & Widersprüche

### [E-16] Friktion dominiert Richtungs-Edge auf S2 (~35× im iter-2-Inversions-Delta)
- **Quelle:** `ANALYSIS_REPORT_iter2.md` §3.2.
- **Metrik & Wert:** S2 original→invertiert aggregate total_return -5.716,8 → -6.032,8 $ (gleiche 190 Trades). Delta -316 $ ⇒ orig_raw_sum ≈ -158 $ (~-0,83 $/Trade roh). Friktions-Beitrag ≈ -5.559 $ (~-29,3 $/Trade) dominiert ~35×. Per-Symbol-Sharpe S2 uniform stark negativ (-43 bis -88), kein Symbol-Outlier.
- **Datengrundlage:** 5 Symbole, N=190, iter-2.
- **Validierungsqualität:** L0.
- **Testfenster-Eignung:** EINGESCHRÄNKT (GM-3: $-Aggregate BTC-dominiert).
- **Methodische Schwächen:** iter-2-$-Zahlen (-5.717) weichen von iter-3/4-S2-$-Zahlen ab (iter-3/4 nutzen andere Fee-Modi: iter-4 Maker-Only=0). Beide Regime notiert; nicht direkt vergleichbar (verschiedene Fee-Settings). GM-3.
- **Belastbarkeit:** MITTEL (Friktion≫Richtung qualitativ robust; absolute $-Werte GM-3-belastet).

### [E-17] WIDERSPRUCH-MARKER: S3-Aggregate divergieren stark zwischen iter-3 und iter-4
- **Quelle:** `replay_all_results.json` (iter-4) vs. `ANALYSIS_REPORT_iter3.md` §1 (iter-3).
- **Metrik & Wert:**
  - iter-3 S3: N=204, total_return -2.113,26 $ (BTC -2.042,77), mean raw -6.27 bps, mean_win_rate (S3 aggregat, iter-2 JSON nannte 9.3%).
  - iter-4 S3: N=213, total_return **-6.857,56 $** (BTC **-6.680,50**), mean netto -16.81 bps, mean_win_rate 0.0939.
  - Faktor ~3,2× schlechter im $-Total bei nur +9 Trades. Teilweise Netto-vs-Roh (iter-4 bps sind netto), teilweise verschiedener Run/Fenster.
- **Validierungsqualität:** L0.
- **Methodische Schwächen:** Nicht eindeutig auflösbar ohne Roh-PnL-Export beider Runs. Möglich: (a) anderes Replay-Fenster, (b) Hard-Stop-Exits erzeugen schlechtere Realisierungen als „natürliche" Exits, (c) bps-Definition (netto vs raw). **Beide Zahlensätze registriert; Widerspruch explizit markiert für Phase 3.**
- **Belastbarkeit:** N/A (Widerspruchs-Flag, kein eigenständiger Befund).

### [E-18] Implementierungs-Defekt (Kontext): S3-Inversions-Flag deaktiviert die Strategie still (iter-2)
- **Quelle:** `ANALYSIS_REPORT_iter2.md` §1.1, §5 (W1/W2).
- **Metrik & Wert:** `S3_INVERT_DIRECTION=True` ⇒ S3 total_trades = 0 auf allen 5 Symbolen (`data_limited=false`). Ursache: `_direction_from_pressure` wird 2× aufgerufen (Gate UND Entry); Flag flippt beide; Basis-Gate `basis*direction<0` kippt von Auto-Pass zu Auto-Fail. Deshalb existiert KEIN sauberer S3-Mirror aus iter-2; S3-Mirror-Analyse (E-11) stammt aus iter-3-Daten.
- **Validierungsqualität:** L0 (Code-/Mechanik-Befund, code-reading-verifiziert).
- **Methodische Schwächen:** Erklärt, warum S3-Inversions-Vergleich methodisch limitiert ist. Reiner Implementierungsbefund.
- **Belastbarkeit:** HOCH (code-reading + 0-Trade-Evidenz über 5 Symbole).

---

## ZUSAMMENFASSUNG: E-xx-Übersicht

| E-xx | Strategie/Modul | Befund (Kurz) | Stufe | Belastbarkeit |
|---|---|---|---|---|
| E-01 | S1/C-14 | ρ-Median 2e-7, 6 Größenord. unter Threshold 0.85 | L0 | HOCH |
| E-02 | S1/C-14 | 0 Trades, rho_below_threshold-bound (nicht data) | L0 | HOCH |
| E-03 | S2/CS-02 | Roh-Edge -3.45 bps NEGATIV auch Maker-Only (0 Fee) | L0 | HOCH |
| E-04 | S2/CS-02 | Mirror scheitert, hit_sum 0.179≠1.0 (kein Anti-Signal) | L0 | HOCH |
| E-05 | S2/C-06 | Entropie-Gate filtert ~97%; Hit 6–8% BTC/ETH | L0 | MITTEL-HOCH |
| E-06 | S2 | 189/190 Long (Bias) | L0 | HOCH (Messung) |
| E-07 | S3/CS-03 | ⚠️ TIME-STOP-BUG: 1× statt 68× (Wall-Clock) | L0 | HOCH |
| E-08 | S3/CS-03 | Hard-Stop 13× real, aber 33 Trades <-30bps | L0 | MITTEL |
| E-09 | S3/CS-03 | mean -16.81 bps netto, alle neg; total -6857 (BTC-dom.) | L0 | MITTEL |
| E-10 | S3/CS-03 | Tail-Signatur 1.7–3.0× Dur, robust BTC/ETH/SOL+Mirror | L0 | MITTEL-HOCH |
| E-11 | S3/BNB | -195→+187 bps Mirror-Flip (N=16, 1-Trade-Artefakt) | L0 | NIEDRIG |
| E-12 | S3/C-23,C-08 | 213 Long; Basis-Gate No-Op; BOCPD nie gefeuert | L0 | MITTEL-HOCH |
| E-13 | S4/CS-04 | 0 Trades, insufficient_models 96–99.99% (loader) | L0 | HOCH (Lücke) |
| E-14 | S5/CS-05 | 0 Trades, single_symbol_unsupported 100% (harness) | L0 | HOCH (Lücke) |
| E-15 | S3/iter-5 | PENDING: Time-Stop+Hard-Stop-Fix, Run läuft | — | N/A |
| E-16 | S2 | Friktion ~35× Richtungs-Edge (iter-2) | L0 | MITTEL |
| E-17 | S3 | WIDERSPRUCH iter-3 (-2113$) vs iter-4 (-6857$) | L0 | N/A (Flag) |
| E-18 | S3 | Inversions-Flag deaktiviert S3 still (0 Trades) | L0 | HOCH |

**Validierungsstufen-Verteilung:** L0 = 17 (E-01–E-14, E-16–E-18); PENDING = 1 (E-15). **L1/L2/L3 = 0.** Kein einziger Befund out-of-sample; nichts kann einen Claim auf CONFIRMED heben (GM-1).

**Negative/Null-Ergebnisse (vollständig erfasst):** E-01/E-02 (S1 Estimator gebrochen), E-03/E-04/E-05/E-16 (S2-Forensik-Kette: Maker-Only, Mirror, Funnel, Friktion — alle negativ), E-13/E-14 (S4/S5 Mess-Lücken).

**Mess-Lücken explizit:** S4 (E-13, Modell-Loader), S5 (E-14, Panel-Harness), S3-Time-Stop (E-07, Bug → Wirkung ungemessen, nur Hard-Stop real).

*Ende evidence_register.md*
