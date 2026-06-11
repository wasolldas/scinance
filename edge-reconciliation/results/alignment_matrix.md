# Alignment Matrix — Edge Reconciliation Framework
**Phase:** 3 — ALIGNMENT (Mapping-Modus)
**Stand:** 2026-06-11
**Erstellt von:** evidence-auditor
**Inputs:** `results/claims_register.md` (56 Claims: C-01..C-43, CS-01..CS-13), `results/evidence_register.md` (E-01..E-18, GM-1..6, Kostenbaseline)

---

## Vorbemerkung — verbindliche Statusregeln für diese Matrix

1. **CONFIRMED ist praktisch unerreichbar.** Das gesamte Evidence-Register ist L0 (GM-1: kein Train/Test, kein Walk-Forward, kein Live). 17×L0 + 1×PENDING. Ein L0-in-sample-Befund hebt nach Rollendefinition niemals auf CONFIRMED. → **0 CONFIRMED** in dieser Matrix; jede positive Evidenz führt höchstens auf PARTIAL.
2. **REFUTED nur aus GEEIGNETEM Testfenster.** Evidenz mit Testfenster-Eignung UNGEEIGNET kann nie REFUTED begründen (bleibt UNTESTED + Vermerk). REFUTED-Vergaben hier stützen sich ausschließlich auf E-01/E-03/E-04 (alle GEEIGNET).
3. **Modul ≠ Strategie.** Scheitert eine Strategie (CS-xx), wird ein konstituierendes Modul nur REFUTED, wenn die Forensik SEINEN Beitrag isoliert hat. Sonst bleibt es UNTESTED mit Vermerk **SUSPECT** (in gescheiterter Strategie verbaut, nie standalone getestet).
4. **Schwellen-Differenzierung.** Bei C-14/C-01 widerlegt E-01 die SCHWELLE (ρ>0.85) und den ESTIMATOR-Output, nicht zwangsläufig das Konzept. Dies wird im Status-Text getrennt.
5. **Multiple-Testing-Vorbehalt (GM-2):** keine FDR/Bonferroni-Korrektur in irgendeiner Quelle; jeder „signifikant"-wirkende Einzelbefund ist unkorrigiert.
6. **P-01/P-02 sind NICHT als Evidenz verwendet** — jede Statusvergabe ist allein aus E-xx hergeleitet.

Feldlegende je Claim: **Status** · **Evidenz** · **Begründung (1-3 Sätze)** · **Konfidenz-Note** (max. L-Stufe, Fenstergröße/-eignung, Multiple-Testing) · ggf. **Relevante Randbefunde** (indirekt relevante Evidenz) · ggf. **SUSPECT**-Vermerk.

---

## Teil I — Modul-Claims (C-01 .. C-43)

### [C-01] OFI Cont-Kukanov-Stoikov
- **Status:** UNTESTED — **SUSPECT** (in CS-02 verbaut, nie standalone getestet)
- **Evidenz:** E-05 (indirekt), E-04, INC-02
- **Begründung:** OFI ist nur als Gate-Glied in S2 (CS-02) aktiv; sein eigener direktionaler Beitrag (R²-Forecast, Hit-Rate) wurde nie isoliert gemessen. Die Forensik hat die GESAMT-S2-Edge widerlegt (E-03/E-04), nicht das OFI-Modul allein. INC-02 legt nahe, dass das OFI-Vorzeichen MM-Replenishment statt Aggression markiert — ein Verdacht, keine isolierte Widerlegung.
- **Konfidenz-Note:** L0; OFI-`>Q90`-Gate filtert nur sekundär (E-05: ofi_below_q90 ~1.4–3.2k Ticks); kein eigenständiges OOS-R²/AUC gemessen. Standalone-Test fehlt vollständig.

### [C-02] SpikeWavformer SNN+DWT Event-Ingestion
- **Status:** UNTESTED
- **Evidenz:** — (kein E-xx berührt C-02)
- **Begründung:** Kein Replay testet die SNN/DWT-Event-Ingestion. C-36 (F0-Trigger) wäre laut PRD-kestrel der Schatten-Benchmark, ist selbst aber unimplementiert/ungetestet.
- **Konfidenz-Note:** Keine Evidenz. Moonshot-Status laut Quelle; nicht in den Replay-Strategien verbaut → kein SUSPECT-Vermerk.

### [C-03] Iceberg-Detection via Queue-Replenishment
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Keine Evidenz; orderbook.200-Aufzeichnung für die Queue-Replenishment-Analyse liegt in keinem Replay vor.
- **Konfidenz-Note:** Keine Evidenz. Nicht in CS-01..05 verbaut.

### [C-04] Wavelet-Symlet-Denoising (Orderbuch-Imbalance)
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Kein E-xx berührt das Denoising-Modul; R²-Lift gegen Roh-Imbalance nie gemessen.
- **Konfidenz-Note:** Keine Evidenz.

### [C-05] Fraktionale Differenzierung (FFD)
- **Status:** UNTESTED — **SUSPECT** (in CS-04 verbaut, nie standalone getestet)
- **Evidenz:** E-13 (indirekt)
- **Begründung:** FFD ist Feature-Lieferant für S4 (CS-04); da S4 mit `insufficient_models` 96–99.99% 0 Trades feuerte (E-13), wurde FFD nie real durchlaufen. Auch als Q7-Mechanik-Zustand (dPreis×dOI) kein Test.
- **Konfidenz-Note:** L0/Mess-Lücke; FFD nie ausgeführt. SUSPECT, weil in gescheiterter (genauer: nie gelaufener) Integration verbaut.

### [C-06] Shannon-Entropie L2-Orderbuch (Greenlight)
- **Status:** PARTIAL — **SUSPECT** (Beitrag in CS-02 nicht isoliert; siehe Begründung)
- **Evidenz:** E-05, E-03, E-04
- **Begründung:** Das Entropie-Kollaps-Gate ist in S2 der dominante Filter (~97% der Ticks, E-05) — das Modul FEUERT also messbar und strukturiert, ist nicht dekorativ. ABER bei Auslösung liegt die Roh-Hit-Rate bei 6–8% (BTC/ETH) und die Gesamt-S2-Edge ist negativ (E-03), ohne Anti-Signal-Eigenschaft (E-04). Der eigenständige prädiktive Wert des Entropie-Signals wurde nie von OFI/PE/Funding isoliert → PARTIAL (Gate wirkt, prädiktiver Edge nicht belegt), nicht REFUTED.
- **Konfidenz-Note:** L0; Fenster GEEIGNET für Funnel, EINGESCHRÄNKT für „Entropie prädiktiv?" (6–8% Hit auf N=59/71, GM-2 unkorrigiert). SUSPECT: Beitrag nicht von der gescheiterten S2-Kette getrennt.

### [C-07] Permutation Entropy (Bandt-Pompe)
- **Status:** UNTESTED — **SUSPECT** (in CS-02 als PE-Gate verbaut, nie standalone getestet)
- **Evidenz:** E-05 (indirekt)
- **Begründung:** PE ist in S2 nur tertiäres Gate (`pe_no_greenlight` 39–102 Ticks, E-05) — feuert kaum und wurde nie isoliert auf den ρ≥0.3-Vol-Cluster-Claim oder die bedingte AUC getestet. Cross-Sectional-Variante (Q12) gar nicht implementiert.
- **Konfidenz-Note:** L0; PE-Gate marginal aktiv, kein eigener Validierungsbefund. SUSPECT (S2-Glied).

### [C-08] BOCPD auf OI/Funding/RV
- **Status:** UNTESTED — **SUSPECT** (in CS-03 verbaut, dort als No-Op nie real getestet)
- **Evidenz:** E-12
- **Begründung:** In S3 feuerte BOCPD im gesamten Fenster KEINEN Changepoint (E-12) — das „kein Change-Point"-Gate war damit effektiv Pass-Through und wurde nie unter Stressbedingungen geprüft. Detection-Latenz/DD-Reduktions-Claims nie gemessen.
- **Konfidenz-Note:** L0; Fenster (~24h, GM-6) enthielt keinen garantierten Regime-Bruch → BOCPD-Nicht-Feuern ist nicht falsifizierend. SUSPECT (S3-Glied, dekorativ).

### [C-09] HMM Vola-OFI-Funding (3-State)
- **Status:** UNTESTED — **SUSPECT** (in CS-05 verbaut, nie ausgeführt)
- **Evidenz:** E-14 (indirekt), INC-05
- **Begründung:** HMM ist Gating-Modul in S5 (CS-05); S5 lief mit `single_symbol_replay_unsupported` 100% nie (E-14). Chi²-State-Differenzierung nie gemessen.
- **Konfidenz-Note:** L0/Mess-Lücke. **Relevante Randbefunde:** INC-05 (Kestrel-Baseline: Richtungs-AUC ≈ 0.50 mit klassischen Features) setzt den unkonditionalen HMM-Direktional-Anspruch unter Revisionsdruck. SUSPECT (S5-Glied).

### [C-10] MF-DFA Multifraktal / Hölder
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Kein E-xx berührt MF-DFA; nicht in CS-01..05 verbaut.
- **Konfidenz-Note:** Keine Evidenz.

### [C-11] TDA / Persistent Homology
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Kein Replay testet PH/Crash-Frühwarnung; M-S17-IV-Surface-Variante braucht Options-IV-Aufzeichnung (nicht vorhanden, INC-04).
- **Konfidenz-Note:** Keine Evidenz. Nicht in CS-01..05.

### [C-12] RQA (Recurrence Quantification Analysis)
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Kein E-xx berührt RQA.
- **Konfidenz-Note:** Keine Evidenz.

### [C-13] Cross-Sectional Ergodicity-Reversion Z-Score
- **Status:** UNTESTED — **SUSPECT** (in CS-05 verbaut, nie ausgeführt)
- **Evidenz:** E-14 (indirekt)
- **Begründung:** Kern-Direktionssignal von S5; S5 nie lauffähig (E-14, harness-bound). Sharpe/Hit-Rate-Claims ungemessen.
- **Konfidenz-Note:** L0/Mess-Lücke (architektonisch — Panel-Loader fehlt). SUSPECT (S5-Glied).

### [C-14] Hawkes-Spektralradius ρ(Φ)
- **Status:** REFUTED (Schwelle + Estimator-Output) / UNTESTED (Konzept)
- **Evidenz:** E-01, E-02, INC-01
- **Begründung:** E-01 widerlegt eindeutig und über alle 5 Symbole, dass der AKTUELLE ρ-Estimator den Threshold 0.85 erreicht (Median ~2e-7, 6 Größenordnungen darunter) — die SCHWELLE und der Single-Channel-Estimator-Output sind REFUTED (GEEIGNETES Fenster für genau diese Distributions-Aussage). Das Hawkes-/Reflexivitäts-KONZEPT als solches ist damit NICHT widerlegt: ob ein anders parametrisierter/normierter Branching-Ratio-Estimator (PRD-kestrel-Variante) Kritikalität misst, bleibt UNTESTED.
- **Konfidenz-Note:** L0, aber Belastbarkeit HOCH für die enge Aussage; Verteilungsbefund über 56k–87k Ticks/Symbol, kein Multiple-Testing-Problem (kein Signifikanztest). Für den übergeordneten Kaskaden-PRÄDIKTIONS-Claim bleibt das Fenster EINGESCHRÄNKT (keine garantierte Kaskade, GM-6).

### [C-15] Gutenberg-Richter b-Wert + Omori-Utsu
- **Status:** UNTESTED — **SUSPECT** (in CS-01 verbaut, dort nie ausgelöst)
- **Evidenz:** E-02 (indirekt)
- **Begründung:** In S1 erreichte das vorgeschaltete ρ-Gate nie den Threshold → b-value/Omori-Glieder (`b_value_not_extreme` 4 auf BTC, E-02) wurden faktisch nie getestet. GR-Detection-Rate/Omori-R²-Claims ungemessen.
- **Konfidenz-Note:** L0; ~24h-Fenster ohne garantierte Mainshock-Kaskade (GM-6) → nicht falsifizierbar. SUSPECT (S1-Glied). **Relevante Randbefunde:** E-02 zeigt, dass Liquidationen (außer BNB) reichlich vorhanden waren — Omori-Fit wäre prinzipiell datenseitig möglich gewesen, wurde aber durch das ρ-Gate blockiert.

### [C-16] TFSAX + Smith-Waterman Sequence Alignment
- **Status:** UNTESTED — **SUSPECT** (in CS-04 verbaut, nie ausgeführt)
- **Evidenz:** E-13 (indirekt)
- **Begründung:** TFSAX/SW ist S4-Glied; S4 lief nie (E-13). M-S23-Orderflow-Variante (CS-07) unimplementiert. OOS-AUC-Gate (hartes Drop-Kriterium der Quelle) nie gemessen.
- **Konfidenz-Note:** L0/Mess-Lücke. SUSPECT (S4-Glied).

### [C-17] Renyi-Transfer-Entropy Lead-Lag-Graph
- **Status:** UNTESTED — **SUSPECT** (in CS-05 verbaut, nie ausgeführt)
- **Evidenz:** E-14 (indirekt)
- **Begründung:** Lead-Lag-Achse von S5; S5 nie lauffähig (E-14). ρ≥0.3 / AUC>0.55-Claims ungemessen.
- **Konfidenz-Note:** L0/Mess-Lücke. SUSPECT (S5-Glied).

### [C-18] PatchTST (Funding-Cycle / RV-Prognose)
- **Status:** PARTIAL (nur RV-Prognose, via Schwester-Modul C-42; PatchTST selbst UNTESTED) — **SUSPECT** (in CS-04 verbaut, nie ausgeführt)
- **Evidenz:** E-13, (Kontext C-42)
- **Begründung:** PatchTST selbst feuerte in S4 nie (E-13, insufficient_models). Die einzige stützende Evidenz für die RV-PROGNOSE-Domäne ist die separate Kestrel-v1.4-LightGBM/HAR-Baseline (C-42, R²=0.249) — das ist ein ANDERES Modell, nicht PatchTST. → PARTIAL nur für „RV-Prognose ist auf diesem Markt grundsätzlich machbar"; der PatchTST-Anspruch (OOS-R²>0.25 schlägt HAR-RV) ist UNTESTED.
- **Konfidenz-Note:** PatchTST: L0/Mess-Lücke. C-42-Baseline ist der einzige dokumentierte deployable-Befund, stammt aber NICHT aus diesem Replay (research_notes, ebenfalls nicht in dieser Pipeline validiert). SUSPECT (S4-Glied).

### [C-19] TimesNet 2D-Periodizität
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Kein E-xx; nicht in CS-01..05 verbaut (zurückgestellt laut PRD-kestrel).
- **Konfidenz-Note:** Keine Evidenz.

### [C-20] MOMENT Foundation Model
- **Status:** UNTESTED — **SUSPECT** (in CS-04 verbaut, nie ausgeführt)
- **Evidenz:** E-13 (indirekt)
- **Begründung:** MOMENT ist eines der 3 Modelle in S4; S4 lief nie (E-13). MASE/Sharpe-Claims ungemessen.
- **Konfidenz-Note:** L0/Mess-Lücke. **Relevante Randbefunde:** INC-05 (Münzwurf-Baseline) drückt auf unkonditionale Direktional-Ansprüche. SUSPECT (S4-Glied).

### [C-21] Long/Short-Account-Ratio Smart-Money-Divergenz
- **Status:** UNTESTED
- **Evidenz:** — (INC-05 indirekt)
- **Begründung:** L/S-Ratio-Modul ist in keiner getesteten Replay-Strategie (CS-01..05) verbaut; Hit-Rate/Sharpe-Claims nie gemessen.
- **Konfidenz-Note:** Keine direkte Evidenz. **Relevante Randbefunde:** INC-05 — unkonditionale Direktional-Ansprüche stehen unter Revisionsdruck. Kein SUSPECT (nicht in gescheiterter Strategie verbaut).

### [C-22] Funding-Rate-Clamp Pressure-Release (Settlement-Timing)
- **Status:** PARTIAL — **SUSPECT** (Entry-Beitrag in CS-03 nicht von der gescheiterten Exit-Logik isoliert)
- **Evidenz:** E-09, E-12, E-10, INC-03
- **Begründung:** C-22 ist das Entry-Signal von S3 (CS-03). S3 feuert real (N=213), aber die Netto-Edge ist auf ALLEN Symbolen negativ (mean -16.81 bps, E-09) und die Verluste sind exit-/tail-getrieben (E-10), nicht eindeutig entry-getrieben. Das Entry-Signal selbst ist weder als positiv noch als negativ isoliert nachgewiesen → PARTIAL (Strategie verliert, aber Ursache liegt nachweislich in Exit/Friktion, nicht zwingend im Entry). INC-03: Q90-Pressure-Threshold übertriggert (50–60 Trades/24h statt 3 Settlements) → der Pressure-Filter trennt nicht auf Settlement-Qualitätsniveau.
- **Konfidenz-Note:** L0; Fenster EINGESCHRÄNKT (GM-6: nur 3 Settlement-Zyklen/Symbol). Roh-Edge -5.8 bps < 11 bps Friktion ⇒ friction-bound. **— PENDING-UPGRADE möglich nach iter-5-Validierung (E-15):** iter-5 misst, ob Bounded-Loss-Fix die Netto-Edge hebt; erst dann ist der Entry-Beitrag sauber bewertbar. SUSPECT (Entry nie von Exit getrennt).

### [C-23] Mark-Index-Basis Settlement Convergence
- **Status:** UNTESTED — **SUSPECT** (in CS-03 als No-Op verbaut, nie real getestet)
- **Evidenz:** E-12
- **Begründung:** In S3 ist das Basis-Gate per Konstruktion Pass-Through (`sign(pressure)≡-sign(basis)`, E-12: n_pressure_extreme == n_basis_aligned auf JEDEM Symbol) — es trug keine eigenständige Information bei und wurde nie als Convergence-Signal isoliert geprüft.
- **Konfidenz-Note:** L0; Fenster GEEIGNET für „Basis-Gate trägt keine Information" (Counter-Gleichheit fakten-fest), aber der eigenständige Convergence-Claim (Hit-Rate≥58%) ist ungemessen. SUSPECT (S3-Glied, dekorativ).

### [C-24] Kalman-Funding-Premium-Decomposition
- **Status:** UNTESTED — **SUSPECT** (in CS-03 verbaut, Beitrag nicht isoliert)
- **Evidenz:** E-12 (indirekt)
- **Begründung:** Kalman-Premium ist S3-Glied; der Sentiment-Spike-Fade-Claim wurde nie isoliert gemessen (S3-Funnel zeigt nur Pressure-/Basis-Gates, E-12). Kein eigener Befund.
- **Konfidenz-Note:** L0; kein isolierter Test. SUSPECT (S3-Glied).

### [C-25] Kyle's Lambda (Adverse Selection / Toxic Flow)
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** In CS-01 nur „implizit als Sizing" gelistet, in keinem Replay-Funnel aktiv messbar; Loss-Reduktions-/Odds-Ratio-Claims nie geprüft. In den neuen Strategien CS-11/12/13 als Veto vorgesehen, dort aber nichts implementiert.
- **Konfidenz-Note:** Keine direkte Evidenz; in CS-01 nur nominell verbaut (kein Funnel-Eintrag) → grenzwertiger SUSPECT, hier konservativ ohne Vermerk, da kein Replay-Trace existiert.

### [C-26] SIR-Kompartiment-Liquidations-Contagion
- **Status:** UNTESTED — **SUSPECT** (in CS-01 verbaut, dort nie ausgelöst)
- **Evidenz:** E-02 (indirekt)
- **Begründung:** SIR R₀ ist S1-Glied; S1 erreichte das ρ-Gate nie (E-02) → R₀>1-Detektions-Claim wurde nie getestet.
- **Konfidenz-Note:** L0; ~24h-Fenster ohne garantierte Mainshock-Kaskade (GM-6). **Relevante Randbefunde:** E-02 — `liquidations_below_min_events` nur auf BNB relevant (28.192 = 33%), d.h. auf 4/5 Symbolen waren genug Liquidationen für SIR-Kalibrierung da; das Nicht-Feuern ist ρ-Gate-bedingt, nicht datenbedingt. SUSPECT (S1-Glied).

---

### Neue Module C-27..C-43 (PRD-fable5 / PRD-kestrel / research_notes) — fast durchweg ohne direkte Evidenz

### [C-27] Cori-Rₜ Renewal-Equation auf Liquidations-Inzidenz
- **Status:** UNTESTED
- **Evidenz:** — (E-01/E-02 indirekt als Randbedingung)
- **Begründung:** Nicht implementiert (Idee/spezifiziert); kein Replay berührt das Rₜ-Modul.
- **Konfidenz-Note:** Keine direkte Evidenz. **Relevante Randbefunde:** C-27 adressiert dieselbe Liquidations-Cascade-Domäne wie das gescheiterte C-14/CS-01. Die E-01/E-02-Lektion ist als Randbedingung höchst relevant: Liquidations-Events sind in ~24h-Fenstern spärlich (E-02: `liquidations_below_min_events` 794–28k auf BNB; nur 4/5 Symbole mit ausreichend Events) → ein Rₜ-Validierungsdesign braucht Bulk-Historie mit garantierten Kaskaden-Episoden (vgl. C-27-Abhängigkeit #34 Bulk-Download), ein ~24h-Replay-Fenster (GM-6) kann den BA≥0.55-OOS-Claim nicht prüfen.

### [C-28] NB-k Superspreading-Dispersion
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; an C-27-ω_s-Fenster gebunden, ebenfalls ungetestet.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Wie C-27 — die E-02-Spärlichkeit der Liquidations-Events begrenzt die k-Schätz-Stabilität; Überdispersions-LR-Test (p<0.05) braucht viele Kaskaden, die ein 24h-Fenster nicht liefert.

### [C-29] Avalanche Shape Collapse / universelle Skalenfunktion
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; kein Burst-Profil-Befund in der Evidenz.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** E-10 (S3-Tail-Signatur: schlechteste Trades 1.7–3.0× länger gehalten) zeigt empirisch, dass Halte-/Burst-DAUER ein realer Verlusttreiber ist — das motiviert grundsätzlich Restdauer-Prognose, ist aber kein Test des Shape-Collapse-Mechanismus selbst.

### [C-30] Natural Time κ₁-Ordnungsparameter
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; theoretischer Schwellwert (κ₁≈0.070), kein empirischer Befund.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Adressiert dieselbe Kaskaden-Kritikalitäts-Domäne wie das REFUTED-Schwellen-Problem von C-14 (E-01). Wichtige Lehre: C-14 scheiterte, weil ein importierter theoretischer Threshold (0.85) empirisch nie erreicht wurde — C-30 trägt mit κ₁≈0.070 dasselbe Risiko eines unkalibrierten theoretischen Schwellwerts; Validierung muss die Erreichbarkeit der Schwelle zuerst prüfen (Distributions-Check analog E-01).

### [C-31] Cyclostationary Cyclic Spectrum + CFAR
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; kein E-xx.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Kostenbaseline (11 bps Round-Trip) ist als Randbedingung relevant — die Quelle selbst flaggt, dass der Sekunden-Horizont evtl. unter der Fee-Schwelle liegt; jede gemessene Mikro-Edge muss >11 bps schlagen (Kernrelation Evidence-Register: Friktion > jede bisher gemessene Roh-Edge).

### [C-32] Funding-Rate Contrarian (Extremwert)
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert (REST-only, 24h-Horizont).
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Verwandt mit C-22 (Funding-Pressure), aber anderer Horizont. INC-05/Carry-Kompression: die Quelle selbst erwartet schnellen Signal-Zerfall unter aktuellem Carry-Regime. Kosten-Gate >0.11% je Round-Trip deckt sich mit Kostenbaseline.

### [C-33] Volatilitäts-Risikoprämie / Short-Vola Optionen
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; einziger Options-Claim, kein Options-Replay vorhanden (INC-04: Options als Zielmarkt neu, IV-Archiv fehlt).
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** INC-04 (Bybit-Options-Liquidität als größtes Risiko, kein IV-Archiv → Eigenaufzeichnung). Keine der vorhandenen Evidenz berührt Optionen — komplett unadressierter Markt.

### [C-34] GMM-Vol-Regime + Variance Risk Premium (G3-Gate)
- **Status:** UNTESTED
- **Evidenz:** — (C-42 indirekt)
- **Begründung:** Nicht implementiert; kein IV-Archiv (Aufzeichnungs-Vorlauf nötig).
- **Konfidenz-Note:** Keine direkte Evidenz. **Relevante Randbefunde:** Der RV-Teil des VRP teilt die Domäne mit C-42/E-05? Nein — relevant ist: die einzige stützbare Vol-Regime-/RV-Evidenz ist die C-42-Baseline (R²=0.249), die zeigt, dass RV-Schätzung machbar ist; der VRP-Mehrwert (IV²−RV) bleibt unbelegt, da kein IV-Strom existiert. ΔR²≥+0.02-Gate über RV-only ist ungemessen.

### [C-35] CEEMDAN-Dekomposition streng kausal
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; Kausalitäts-Nachweis (bit-für-bit) und ΔR² nie geprüft.
- **Konfidenz-Note:** Keine Evidenz.

### [C-36] F0 Fallback-Schwellwert-Trigger
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Neu spezifiziert (nicht im Repo); Recall≥95%-Claim ungemessen. F0 sollte Benchmark für C-02 sein, ist aber selbst unimplementiert.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Deterministisches Perzentil-Regelwerk — am schnellsten prüfbar mit vorhandenen Phase-0-Recordings (kritische Datenlücke, leicht schließbar).

### [C-37] Basis/Carry über den Spread-Markt (Execution-Schiene)
- **Status:** UNTESTED
- **Evidenz:** — (Kostenbaseline indirekt)
- **Begründung:** Neu spezifiziert; Bybit-Spread-Markt kein Archiv → nur Proxy-Backtest/Live möglich, nichts gemessen.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Kostenbaseline ist zentral: C-37 behauptet ~4 bps Maker-Round-Trip statt 11 bps Taker — das ist der einzige dokumentierte Hebel, um die Kernrelation „Friktion > Edge" (Evidence-Register) potenziell zu kippen. Der 4-bps-Wert ist jedoch unmeasured (Kostenbaseline: „PRD-Referenz, nicht gemessen"); die Maker-Quote≥70%-Annahme ist ungeprüft.

### [C-38] TFT mit Known-Future-Funding
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Neu spezifiziert; explizit erst nach C-22-Live-Proof vorgesehen; nichts gemessen.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** INC-05 (Münzwurf-Direktional-Baseline) — der Quantil-Kalibrierungs- und Direktional-AUC>0.55-Anspruch steht unter demselben Revisionsdruck wie alle DL-Direktional-Claims.

### [C-39] Liquidations-Kaskaden-Anatomie (Bankruptcy/Insurance/ADL)
- **Status:** UNTESTED
- **Evidenz:** — (E-02 indirekt)
- **Begründung:** Neu spezifiziert; Insurance/ADL ohne REST-Archiv → Aufzeichnung nötig, nichts gemessen.
- **Konfidenz-Note:** Keine direkte Evidenz. **Relevante Randbefunde:** Erweitert C-26 (SIR); teilt dessen Cascade-Domäne. E-02-Lektion (Liquidations-Events spärlich, nur 4/5 Symbole ausreichend; ~24h-Fenster ohne garantierte Kaskade, GM-6) ist als Validierungs-Randbedingung direkt übertragbar: der Recall≥90%-Claim braucht ein Stress-reiches Fenster.

### [C-40] RPI-/Iceberg-Hidden-Liquidity-Karte
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Neu spezifiziert (Moonshot); kein RPI-Buch aufgezeichnet, nichts gemessen.
- **Konfidenz-Note:** Keine Evidenz.

### [C-41] Cross-Asset Wavelet Coherence (K3-Achse 2)
- **Status:** UNTESTED
- **Evidenz:** — (E-14 indirekt)
- **Begründung:** Neu spezifiziert; komplementär zu C-17 in der nie-lauffähigen Cross-Sectional-Domäne (vgl. S5/E-14).
- **Konfidenz-Note:** Keine direkte Evidenz. **Relevante Randbefunde:** Teilt die Multi-Asset-Lead-Lag-Domäne mit C-17 (SUSPECT, S5 nie lauffähig, E-14) — dieselbe Panel-Harness-Datenlücke blockiert auch C-41.

### [C-42] Volatilitäts-Prognose-Baseline (LightGBM/HAR-RV)
- **Status:** PARTIAL
- **Evidenz:** — (research_notes-Eigenangabe; kein E-xx aus dieser Pipeline)
- **Begründung:** Einziger Claim mit dokumentiertem deployable-Befund (Test-R²=0.249, Pearson=0.578, Apr-2026-OOS nach Jan–Mar-Training). Das ist die stärkste positive Evidenz im gesamten Register — ABER sie stammt aus research_notes (Kestrel-v1.4), wurde NICHT in dieser Reconciliation-Pipeline als E-xx re-validiert und ist damit nicht unabhängig nachgeprüft → PARTIAL, nicht CONFIRMED.
- **Konfidenz-Note:** Quelle behauptet einen Train/Test-Split (de facto L1, evtl. höher), aber NICHT in dieser Pipeline geprüft → konservativ als L1-Selbstauskunft behandelt. GM-1 gilt nicht direkt (anderer Datensatz), aber: keine unabhängige Reproduktion, keine FDR-Betrachtung über die 36 Features. Der R²≈0.25-Wert ist die de-facto-Referenz für den gesamten Vol-Stack (C-18/C-34/C-35/C-38).

### [C-43] Konforme Prädiktion als Querschnitts-Kalibrator
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; Sizing-Wrapper über L3-Signale, die selbst alle ungetestet/SUSPECT sind. Coverage≥85%-Gate ungemessen.
- **Konfidenz-Note:** Keine Evidenz. Kein Alpha-Generator — Wirkung nur sinnvoll messbar, sobald ein L3-Basissignal existiert.

---

## Teil II — Strategie-Claims (CS-01 .. CS-13)

### [CS-01] „Seismischer Cascade Detector" (S1)
- **Status:** REFUTED (in aktueller Implementierung) / Konzept UNTESTED
- **Evidenz:** E-01, E-02, INC-01
- **Begründung:** Die Strategie feuert 0 Trades auf allen 5 Symbolen, weil das ρ-Eingangsgate (C-14) den Threshold 0.85 strukturell nie erreicht (E-01/E-02, GEEIGNETES Fenster für die Distributions-Aussage). Die aktuelle M14-basierte Implementierung ist damit REFUTED. Das übergeordnete Kaskaden-Konzept bleibt UNTESTED (nie ausgelöst → keine Outcome-Evidenz).
- **Konfidenz-Note:** L0; HOCH für „aktuelles Gate erreicht Threshold nie", EINGESCHRÄNKT für Kaskaden-Prädiktion (GM-6). Konstituierende Module C-15/C-26 bleiben SUSPECT (nie ausgelöst), nur C-14 ist forensisch isoliert belastet.

### [CS-02] „Entropie-Momentum" (S2)
- **Status:** REFUTED
- **Evidenz:** E-03, E-04, E-05, E-06, E-16
- **Begründung:** Drei unabhängige Forensiken aus GEEIGNETEN Testfenstern widerlegen die Strategie: (1) Roh-Edge negativ auf JEDEM Symbol auch ohne Fees (Maker-Only, E-03: -3.45 bps Aggregat); (2) Mirror-Test scheitert, hit_sum=0.179≠1.0 → kein invertierbares Anti-Signal, sondern Execution-Loss (E-04); (3) Friktion dominiert Richtung ~35× (E-16). Dies ist die einzige eindeutig REFUTED Strategie mit isolierter Forensik.
- **Konfidenz-Note:** L0, Belastbarkeit HOCH (über 5 Symbole konsistent, schärfster Test = Maker-Only bestanden). Modul-Implikation: C-06 (PARTIAL, Gate wirkt), C-01/C-07 bleiben SUSPECT (Beitrag nicht isoliert); KEIN Modul wird durch CS-02 automatisch REFUTED (Modul ≠ Strategie).

### [CS-03] „Pre-Settlement Pressure-Release" (S3)
- **Status:** PARTIAL — **— PENDING-UPGRADE möglich nach iter-5-Validierung (E-15)**
- **Evidenz:** E-07, E-08, E-09, E-10, E-11, E-12, E-17, E-18
- **Begründung:** S3 feuert real (N=213) und verliert netto auf allen Symbolen (-16.81 bps, E-09), ABER die zentrale Exit-Logik wurde nie korrekt gemessen: der Time-Stop feuerte wegen eines Wall-Clock-Bugs 1× statt 68× (E-07, Testfenster UNGEEIGNET für die Time-Stop-Hypothese) → die Strategie ist NICHT sauber widerlegt, nur ihre defekte Variante verliert. Tail-Signatur (E-10) und friction-bound-Befund deuten auf reparierbare Exit-Probleme. → PARTIAL, nicht REFUTED.
- **Konfidenz-Note:** L0; Fenster EINGESCHRÄNKT (GM-6, 3 Settlements/Symbol). E-17-Widerspruch (iter-3 -2113$ vs. iter-4 -6857$) ungelöst. **PENDING (E-15):** iter-5 misst Time-Stop-Fix (Tick-Zeit) + friction-aware Hard-Stop; erst dieser Run entscheidet, ob Netto-Edge positiv wird (→ Upgrade) oder PRD-Redesign nötig. Entry-Modul C-22 = PARTIAL/SUSPECT; C-23/C-24/C-08 = SUSPECT (No-Op/nie ausgelöst).

### [CS-04] „Pattern × Foundation Ensemble" (S4)
- **Status:** UNTESTED
- **Evidenz:** E-13
- **Begründung:** 0 Trades, `insufficient_models` 96–99.99% — der Modell-Loader ist nicht verdrahtet, die Strategie lief nie (E-13, Testfenster UNGEEIGNET: reine Infrastruktur-Lücke, mehr Daten helfen nicht).
- **Konfidenz-Note:** L0/Mess-Lücke (architektur-/loader-bound). Alle Module C-05/C-16/C-18/C-20 = SUSPECT. Schnell schließbar nur durch Loader-Fix, nicht durch Daten.

### [CS-05] „Cross-Sectional Ergodicity Reversion" (S5)
- **Status:** UNTESTED
- **Evidenz:** E-14
- **Begründung:** 0 Trades, `single_symbol_replay_unsupported` 100% — der Single-Symbol-Replayer kann Cross-Sectional-Logik prinzipiell nicht ausführen (E-14, Testfenster UNGEEIGNET: braucht Panel-Daten-Loader).
- **Konfidenz-Note:** L0/Mess-Lücke (architektonisch). Module C-13/C-17/C-09 = SUSPECT. Schließbar nur durch Panel-Harness, nicht durch Daten.

### [CS-06] „Epidemiologisches Kaskaden-Cockpit" (Strategie A)
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; aus C-27/C-28/C-29/C-43 zusammengesetzt, alle UNTESTED.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Adressiert dieselbe Liquidations-Cascade-Domäne wie das REFUTED CS-01. E-01/E-02-Lektion (spärliche Liquidations-Events, Threshold-Erreichbarkeit zuerst prüfen) ist Validierungs-Randbedingung; schwächste Annahme (stabiles ω_s über Regime) ist genau der Typ unkalibrierter Annahme, der C-14 fällte.

### [CS-07] „Algorithmischer Footprint-Detektor" (Strategie B)
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; aus C-16(M-S23)/C-31/C-43.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Kostenbaseline (11 bps) ist harte Randbedingung — Sekunden-Horizont evtl. unter Fee-Schwelle (Quelle flaggt selbst).

### [CS-08] „Regime-konditioniertes Richtungs-Signal" (Strategie C)
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; aus C-07/C-08/C-01/C-32/C-21/C-43.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Enthält C-01 (SUSPECT aus CS-02) und C-08/C-07 (SUSPECT aus S3/S2). INC-05 stützt grundsätzlich den regime-KONDITIONIERTEN Ansatz (unkonditional = Münzwurf), liefert aber keinen Test.

### [CS-09] „Topologisch-direktionaler Options-Block" (Strategie D)
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; aus C-11/C-33/C-43; einzige Options+Futures-Strategie.
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** INC-04 — Options-Markt komplett unadressiert in der Evidenz; Liquiditäts-Check fällt laut Quelle in 60–80% der Stunden durch. Höchste Datenlücke.

### [CS-10] „Cross-Coin-Contagion-Lead" (Strategie E)
- **Status:** UNTESTED
- **Evidenz:** —
- **Begründung:** Nicht implementiert; aus CCM/C-27/C-28/C-43; laut Critic „CCM-Analogie gestreckt".
- **Konfidenz-Note:** Keine Evidenz. **Relevante Randbefunde:** Multi-Symbol-Liquidations-Domäne — dieselbe Panel-Datenlücke wie S5 (E-14) und Cascade-Spärlichkeit wie E-02.

### [CS-11] „Seismograph" / Kaskaden-Lebenszyklus-Trader (K1)
- **Status:** UNTESTED
- **Evidenz:** E-01 (indirekt)
- **Begründung:** Nicht implementiert; verwandt mit CS-01 (K1≈Seismograph). Baut u.a. auf C-14 (REFUTED-Schwelle) und C-39/C-15 auf.
- **Konfidenz-Note:** Keine direkte Evidenz. **Relevante Randbefunde:** Erbt das C-14-Schwellen-Risiko (E-01: ρ-Estimator erreicht Threshold nie). PRD-kestrel adressiert dies via Branching-Ratio-Approximation statt 0.85-Threshold — genau der Punkt, den E-01 als REFUTED markiert. Validierung braucht 3+ Monate Aufzeichnung mit Kaskaden-Episoden (E-02/GM-6-Randbedingung).

### [CS-12] „Funding-Uhr" / Settlement-Fenster-Harvester (K2)
- **Status:** UNTESTED — **— PENDING-relevant (teilt C-22-Domäne mit CS-03/E-15)**
- **Evidenz:** E-09, E-12, INC-03 (indirekt)
- **Begründung:** Nicht implementiert; verwandt mit CS-03 (K2≈Funding-Uhr, beide C-22-zentriert). Direkte Evidenz fehlt, aber CS-03 ist der empirische Vorläufer derselben Funding-Pressure-These.
- **Konfidenz-Note:** Keine direkte Evidenz. **Relevante Randbefunde:** Erbt die CS-03/C-22-Befunde: INC-03 (Q90 übertriggert), friction-bound (E-09). K2 verbessert genau die zwei Schwachstellen von S3 — Execution via Spread-Markt (C-37, ~4 bps statt 11 bps) und BOCPD-Regime-Gate (C-08). **Damit hängt K2 indirekt am iter-5-Ausgang (E-15)**: bestätigt iter-5 eine reparierbare Entry-Edge, gewinnt K2 an Plausibilität.

### [CS-13] „Rudel-Läufer" / Lead-Lag-Follower-Rotation (K3)
- **Status:** UNTESTED
- **Evidenz:** E-14 (indirekt)
- **Begründung:** Nicht implementiert; verwandt mit CS-05 (K3≈Rudel-Läufer, beide Cross-Sectional/Lead-Lag). Aus C-17/C-41/C-01/C-13.
- **Konfidenz-Note:** Keine direkte Evidenz. **Relevante Randbefunde:** Dieselbe Panel-Harness-Datenlücke wie S5 (E-14) blockiert auch K3; enthält C-01 (SUSPECT). INC-05 stützt den regime-/G1-konditionierten Ansatz gegenüber unkonditionalem.

---

## Zusammenfassungstabelle — Status nach Quell-PRD

Zuordnung über ID-Mapping (Spalte „erste/primäre Quelle"). PRD-v1 = C-01..C-26, CS-01..CS-05; PRD-fable5 = C-27..C-33, C-43, CS-06..CS-10; PRD-kestrel = C-34..C-41, CS-11..CS-13; research_notes = C-42.

| Quell-PRD | CONFIRMED | PARTIAL | REFUTED | UNTESTED | Σ |
|---|---|---|---|---|---|
| **PRD-v1** (Module C-01..C-26) | 0 | C-06, C-18, C-22 = **3** | C-14 = **1** | C-01,C-02,C-03,C-04,C-05,C-07,C-08,C-09,C-10,C-11,C-12,C-13,C-15,C-16,C-17,C-19,C-20,C-21,C-23,C-24,C-25,C-26 = **22** | 26 |
| **PRD-v1** (Strategien CS-01..CS-05) | 0 | CS-03 = **1** | CS-01, CS-02 = **2** | CS-04, CS-05 = **2** | 5 |
| **PRD-fable5** (C-27..C-33, C-43) | 0 | 0 | 0 | C-27,C-28,C-29,C-30,C-31,C-32,C-33,C-43 = **8** | 8 |
| **PRD-fable5** (Strategien CS-06..CS-10) | 0 | 0 | 0 | CS-06,CS-07,CS-08,CS-09,CS-10 = **5** | 5 |
| **PRD-kestrel** (C-34..C-41) | 0 | 0 | 0 | C-34,C-35,C-36,C-37,C-38,C-39,C-40,C-41 = **8** | 8 |
| **PRD-kestrel** (Strategien CS-11..CS-13) | 0 | 0 | 0 | CS-11,CS-12,CS-13 = **3** | 3 |
| **research_notes** (C-42) | 0 | C-42 = **1** | 0 | 0 | 1 |
| **GESAMT (56 Claims)** | **0** | **5** | **3** | **48** | 56 |

**Gegenprobe:** 0 + 5 + 3 + 48 = 56 ✓ (PARTIAL: C-06, C-18, C-22, C-42 Module + CS-03 Strategie = 5)

**Maßgebliche Endverteilung: CONFIRMED 0 · PARTIAL 5 · REFUTED 3 · UNTESTED 48 (Σ 56).**

| Status | Anzahl | Claims |
|---|---|---|
| CONFIRMED | 0 | — |
| PARTIAL | 5 | C-06, C-18, C-22, C-42, CS-03 |
| REFUTED | 3 | C-14, CS-01, CS-02 |
| UNTESTED | 48 | alle übrigen |

---

## SUSPECT-Module (UNTESTED + in gescheiterter/nie-gelaufener Strategie verbaut)

| Modul | Verbaut in | Grund (nie standalone getestet) |
|---|---|---|
| C-01 (OFI) | CS-02 (REFUTED) | Direktionaler Beitrag nie isoliert; INC-02-Verdacht falsche Orientierung |
| C-05 (FFD) | CS-04 (nie gelaufen, E-13) | Modell-Loader feuerte nie |
| C-06 (Entropie) | CS-02 (REFUTED) | Gate wirkt (PARTIAL), prädiktiver Edge nicht isoliert |
| C-07 (Permutation Entropy) | CS-02 (REFUTED) | PE-Gate marginal, nie isoliert |
| C-08 (BOCPD) | CS-03 (PARTIAL) | No-Op: kein Changepoint im Fenster (E-12) |
| C-09 (HMM) | CS-05 (nie gelaufen, E-14) | S5 harness-bound |
| C-13 (Cross-Sectional-Z) | CS-05 (nie gelaufen, E-14) | S5 harness-bound |
| C-15 (GR+Omori) | CS-01 (REFUTED) | ρ-Gate blockierte Auslösung (E-02) |
| C-16 (TFSAX+SW) | CS-04 (nie gelaufen, E-13) | Modell-Loader feuerte nie |
| C-17 (Renyi-TE) | CS-05 (nie gelaufen, E-14) | S5 harness-bound |
| C-18 (PatchTST) | CS-04 (nie gelaufen, E-13) | PatchTST nie geladen (PARTIAL nur via Schwester-Baseline C-42) |
| C-20 (MOMENT) | CS-04 (nie gelaufen, E-13) | Modell-Loader feuerte nie |
| C-22 (Funding-Pressure) | CS-03 (PARTIAL) | Entry nie von Exit-Logik getrennt |
| C-23 (Basis Convergence) | CS-03 (PARTIAL) | No-Op: Basis-Gate Pass-Through (E-12) |
| C-24 (Kalman-Premium) | CS-03 (PARTIAL) | Beitrag nie isoliert |
| C-26 (SIR R₀) | CS-01 (REFUTED) | ρ-Gate blockierte Auslösung (E-02) |

(C-25 Kyle-λ: in CS-01 nur nominell als „implizites Sizing", kein Replay-Trace → grenzwertig, konservativ NICHT als SUSPECT gelistet.)

**SUSPECT-Kernaussage:** 16 Module wurden in gescheiterten oder nie-gelaufenen Strategien mitgeführt, ohne dass ihr Einzelbeitrag je gemessen wurde. Kein einziges dieser Module ist durch die Strategie-Niederlage automatisch widerlegt (Modul ≠ Strategie). Nur C-14 ist forensisch isoliert belastet (REFUTED-Schwelle, E-01).

---

## Kritische Datenlücken (UNTESTED-Claims, mit vorhandener/naher Infrastruktur schnell prüfbar)

1. **CS-04 / C-05, C-16, C-18, C-20:** kein Daten-, sondern Loader-Problem (E-13). Ein Verdrahtungs-Fix macht S4 sofort messbar.
2. **CS-05 / C-13, C-17, C-09 (+C-41):** Panel-Daten-Loader fehlt (E-14). Ein Multi-Symbol-Replayer schließt die gesamte Cross-Sectional-Familie auf einmal.
3. **C-36 (F0-Trigger):** deterministisches Perzentil-Regelwerk — mit vorhandenen Phase-0-Recordings in Tagen testbar; liefert zugleich den fehlenden Benchmark für C-02.
4. **C-14-Konzept / C-30:** ein reiner Distributions-Check (analog E-01) auf normierten Branching-Ratio- bzw. κ₁-Schätzern beantwortet billig, ob die theoretischen Schwellen überhaupt erreichbar sind — bevor Strategie-Aufwand investiert wird.

---

*Ende alignment_matrix.md*
