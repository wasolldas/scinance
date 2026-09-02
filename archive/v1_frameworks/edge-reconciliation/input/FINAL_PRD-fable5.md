# FINAL PRD — Interdisziplinäre Edge-Forschung für Bybit Retail-Trading

**Dokumenttyp:** Konzept- und Validierungs-PRD (Forschungs-Roadmap, KEIN Implementierungs-Spec, KEIN Code)
**Rolle:** prd-architect | **Phase:** 5 (PRD) | **Datum:** 2026-06-10
**Input:** `results/synthesis.md`, `results/data_audit.md`, `results/critic_report_1.md`, `results/critic_report_2.md`
**Verbindliche Scores:** critic_report_2.md §4 · **Verbindliches Ranking:** synthesis.md §4 (korrigierte Reihenfolge)

> **Grundhaltung (verbindlich aus CLAUDE.md):** Nullhypothese — es existiert kein Edge.
> Jede Methode trägt die Beweislast und muss durch ein messbares, out-of-sample formuliertes
> Gate widerlegt werden, bevor sie als „nicht verworfen" gilt. Kein Gate-Schwellwert ist „TBD";
> jeder Wert unten ist ein begründeter Startwert mit Quelle oder als Hypothese markiert.

---

## 1. Executive Summary

**These des Gesamtkonzepts:** Bybit liefert Retail-Tradern öffentliche Datenströme (Liquidationen,
Orderflow, Orderbuch-Tiefe, Funding/Basis, Options-IV-Surface), deren *strukturelle Form* von
Methoden aus liquidationsfernen Wissenschaftsfeldern — Epidemiologie, Statistische Physik,
Seismologie, Bioinformatik, Topologie — präziser beschrieben wird als von den im Markt etablierten
Quant-Standardtools. Der vermutete Edge liegt nicht in schnellerer Ausführung (Retail hat keine
Co-Location, Latenz 10–300 ms, siehe §3), sondern in **überlegener Mustererkennung auf Minuten- bis
Stunden-Horizont**, vor allem in der **Liquidations-Kaskaden-Dynamik**, die Standard-Risikomaße
(nur Mittelwerte: OI, Gesamtvolumen) nicht erfassen.

**Top-3-Methoden (nach Synthese-Gesamtwert):**
1. **M-S21 Cori-Rₜ Renewal** (Epidemiologie, Score 15/15, NOV 4) — normierte Selbstverstärkungs-Rate
   der Liquidations-Contagion; geschlossene Posterior-Form, minimale Infrastruktur, Quick Win.
2. **M-S22 NB-k Superspreading** (Epidemiologie, Score 15/15, NOV 5) — Tail-Heterogenität der
   Kaskaden-Verzweigung; bildet mit M-S21 ein kohärentes Branching-Framework.
3. **M-S13 Avalanche Shape Collapse** (Stat. Physik, Score 14/15, NOV 5) — Restdauer-Prognose
   einer laufenden Kaskade aus universeller Skalenfunktion.

**Weg zum ersten falsifizierbaren Test (siehe §6 Roadmap):** Beginne mit den zwei Quick Wins —
**M-S21** (höchstes Ranking-Profil, reiner `allLiquidation`-Stream) und **M-Q11 OB Imbalance**
(bestbelegte Baseline, sofort walk-forward-testbar). Beide brauchen nur öffentliche Bybit-Streams,
einen VPS und Python. M-S21 ist in Tagen bis zum ersten Gate testbar: Wenn die Balanced Accuracy
out-of-sample über zwei disjunkte Zeitfenster ≤ 0.55 bleibt UND der Brier-Score einen reinen
Volumen-Schwellwert nicht schlägt, wird die Methode verworfen und dokumentiert.

---

## 2. Nullhypothese & Edge-Definition

**Nullhypothese H₀:** Für jede Methode M gilt — M liefert kein out-of-sample, nach Kosten
verwertbares Signal, das über eine triviale Baseline (Persistenz, unbedingte Ereignisrate,
Random) hinausgeht. H₀ wird nur durch ein bestandenes Validierungs-Gate (§4) zurückgewiesen.

**„Edge" ist in diesem Dokument messbar definiert als die gleichzeitige Erfüllung von:**

1. **Out-of-Sample-Performance:** Die methodenspezifische Kennzahl (Balanced Accuracy, IC,
   Precision@k-Lift, MAE-Reduktion, Sharpe — je nach Zielsignal) übertrifft ihren Gate-Schwellwert
   auf Daten, die **nicht** in Kalibrierung/Training eingingen.
2. **Zeitliche Robustheit:** Das Gate ist in **≥ 2 disjunkten Zeitfenstern** bestanden (z. B. zwei
   nicht überlappende OOS-Quartale oder zwei walk-forward-Folds), nicht nur in einem Glücksfenster.
3. **Nach Kosten:** Wo die Methode ein **Entry-Signal** ist, muss der erwartete Edge die
   Round-Trip-Kostenschwelle übersteigen — **> 0.11 % Preisvorteil** je Round-Trip auf Perpetuals
   (VIP-0-Taker 0.055 % × 2; data_audit §5.1). Wo die Methode ein **Risiko-/Exit-Signal** ist
   (Positionsreduktion bei drohender Kaskade), ist die Fee-Schwelle nachrangig, weil jede vermiedene
   Kaskaden-Verlust positiv-EV ist; dort zählt allein die Klassifikationsgüte (Critic R1 §M-S11/#3).

**Nachweisdisziplin (Pflicht für alle Methoden):**
- **Walk-Forward / rollierendes OOS** ist die Pflicht-Validierungsform. Reine In-Sample-Backtests
  zählen nicht als Nachweis.
- **Purged / embargoed CV** wo Train- und Test-Fenster über überlappende Feature-Fenster
  benachbart sind (Orderflow-, Orderbuch-Methoden mit gleitenden Aggregaten), um Leakage über die
  Fenstergrenze zu verhindern.
- **Surrogate-Tests** (block-permutierte / block-bootstrap Zeitreihen) sind Pflicht für alle
  Methoden, deren Signal aus Sequenz-/Spektral-/Topologie-Struktur stammt (M-S14, M-S18, M-S23,
  M-S17) — sie trennen echte Struktur von Zufallsartefakten.
- **Baseline-Vergleich** ist Pflicht: jede Methode schlägt eine explizit benannte triviale Baseline,
  sonst gilt das Gate als gerissen.

---

## 3. Datenfundament (Kurzfassung des data_audit)

Vollständiger belegter Katalog: `results/data_audit.md` (41 Streams, davon 31 CONFIRMED). Hier nur
die für die Top-10 relevanten Streams und die harten Realitätsgrenzen.

**Verfügbare Streams (alle CONFIRMED, kein API-Key für Public Topics):**

| Stream | Verwendung in Top-10 | Auflösung / Limit |
|---|---|---|
| `allLiquidation.{symbol}` (WS, #12) | M-S21, M-S22, M-S13, M-S11 | Event-driven, vollständiger Feed (nicht der alte 1/s-Feed) |
| `publicTrade.{symbol}` (WS, #8) | M-S23, M-S14 | Event-driven, Felder: ts, side, price, size, isBlockTrade, tradeId |
| `orderbook.50/200/500.{symbol}` (WS, #2–4) | M-Q11, M-S17 | 20 ms / 100 ms / 100 ms Push |
| `tickers.{symbol}` linear (WS, #9) | M-Q12 | live Funding Rate, Open Interest, mark/index |
| `tickers.{symbol}` option (WS, #10) | M-S17, M-Q14 | bid/ask/markIv, delta/gamma/vega/theta, OI — **public** |
| Funding History REST (#26), OI REST (#27) | M-Q12 | max 200 records/Req, paginierbar; OI min. 5-min-Granularität |
| Hist. Volatility REST (#29) | M-Q14 | max 30 Tage/Req, bis 2 Jahre zurück |
| Bulk-Download (#34) | alle (Backtest/Kalibrierung) | Kline/Trades/Orderbook ab 2019 (Inverse) / 2020 (Linear), kostenlos, max 5 Pairs |

**Harte Limits (Realitätsgrenze):**
- **Latenz:** Retail ohne Co-Location 10–50 ms (VPS Singapore) bis 150–300 ms (Consumer). **Edge-
  Horizonte < 50 ms sind nicht handelbar** (data_audit §5.3). Alle Top-10 zielen bewusst auf
  Sekunden–Stunden.
- **Fees:** VIP-0 Perp-Taker 0.055 %, Round-Trip-Break-Even 0.11 %; Options-Taker 0.03 %.
- **Rate-Limits:** REST 600 Req/5 s (IP); WS max 60 Topics/Verbindung, 1000 Verbindungen/IP.
  Empfehlung: Live-Marktdaten ausschließlich über WS (zählt nicht gegen REST-Limit).
- **Nicht verfügbar:** L2-Orderbuch-Historie nur als Bulk (nicht REST-paginierbar); kein
  historisches Greeks-Archiv per API; OI sub-5-min nicht verfügbar; kein Co-Location-Feed.

**Datenlücken-Konsequenz:** Methoden, die L2-Historie für Backtests brauchen (M-Q11, M-S17), sind
auf den kostenlosen Bulk-Download (#34, max 5 Pairs) oder Tardis.dev (#35, nur 1 Tag/Monat frei)
angewiesen — das begrenzt die historische OOS-Tiefe für Orderbuch-Methoden.

---

## 4. Methodenkatalog (Top 10)

Reihenfolge **nach Synthese-Gesamtwert** (synthesis.md §4, korrigierte verbindliche Reihenfolge),
nicht nach Entdeckungsreihenfolge. Aufwand: S/M/L (S = Tage, reiner Stream-Konsum; M = Wochen,
Kalibrierung/Bibliothek/Topologie; L = Wochen+, Margin/Hedging/Optionsinfrastruktur).

---

### 4.1 M-S21 — Cori-Rₜ Renewal-Equation auf Liquidations-Inzidenz (Rang 1)

- **Ursprungsdomäne & Analogie:** Epidemiologie. Strukturmatch: Liquidations-Punktprozess ↔
  epidemischer Inzidenz-Punktprozess; beide markierte Punktprozesse mit Ansteckungsdynamik,
  charakterisierbar durch eine Verzweigungs-Reproduktionszahl. Exakter Strukturmatch, kein
  Metaphernproblem (Critic R2 §M-S21/#5).
- **Mechanismus:** Renewal-Gleichung Iₜ = Rₜ · Σ_{s≥1} I_{t−s}·ω_s, mit ω_s = Generationszeit-/
  Serienintervall-Kernel. Rₜ > 1 zeigt selbstverstärkende Kaskade **vor** messbarer
  Volumenseskalation. Edge-Hypothese: Der Markt preist die *normierte, vom absoluten Volumen
  unabhängige* Selbstverstärkungs-Rate nicht ein.
- **Datenbedarf:** `allLiquidation.{symbol}` (#12, live); Bulk-Download (#34) für einmalige
  Serienintervall-Schätzung. Beide CONFIRMED.
- **Validierungsdesign:** Serienintervall ω_s einmalig aus Bulk-Historie schätzen und **fixieren**
  (kein In-Loop-Fitting). Gleitendes Rₜ(t) mit Gamma-Konjugat-Posterior (geschlossene Form).
  Walk-forward über ≥ 2 disjunkte OOS-Quartale. Kaskaden-Label X (Großkaskade) a priori definiert.
- **Validierungs-Gate:** **Balanced Accuracy ≥ 0.55 out-of-sample (walk-forward) in ≥ 2 disjunkten
  Zeitfenstern** für die Vorhersage „Großkaskade in Folgefenster", UND **Brier-Score besser als der
  einer reinen Volumen-Schwellwert-Baseline** (Critic R2 §M-S21/FA). Begründung Startwert: 0.55 ist
  die im Scout/Critic durchgehend genutzte Mindest-Trefferquote über Zufall (0.50) für direktionale
  Liquidations-Signale.
- **Abbruchkriterium:** Balanced Accuracy ≤ 0.55 OOS in einem der beiden Fenster ODER Brier-Score
  nicht besser als Volumen-Baseline → verwerfen, in §7 dokumentieren.
- **Aufwand:** **S** (geschlossene Posterior-Form, reiner WS-Stream, kein ML-Training).

---

### 4.2 M-S22 — NB-k Superspreading-Dispersion der Liquidations-Contagion (Rang 2)

- **Ursprungsdomäne & Analogie:** Epidemiologie (Lloyd-Smith et al. 2005, Nature 438). Strukturmatch:
  Offspring-Verteilung = Zahl der Folgeliquidationen je Auslöser-Liquidation, modelliert als
  NB(R, k). Präziser Strukturmatch (Critic R2 §M-S22/#5).
- **Mechanismus:** Der Dispersionsparameter k misst die *Heterogenität* der Verzweigung. Kleines k =
  fettere Tail-Last (höhere Varianz bei gleichem Mittel) → seltenere, aber explosivere Kaskaden.
  Edge-Hypothese: Diese Tail-Heterogenität ist nicht eingepreist, weil Standard-Risikomaße nur
  Mittelwerte (OI, Gesamtvolumen) betrachten.
- **Datenbedarf:** `allLiquidation.{symbol}` (#12); Bulk-Download (#34) für Offspring-Zählung über
  das Generationszeit-Fenster. Beide CONFIRMED.
- **Validierungsdesign:** Generationszeit-Fenster aus M-S21-Serienintervall **gebunden** (kein
  freier Parameter). Rollierende ML-Schätzung von (R, k) der NB-Offspring-Verteilung (scipy
  nbinom). Tertil-Grenze für „niedrig-k" als Ordnungsstatistik (kein Fitting).
- **Validierungs-Gate:** **Precision@k-Lift ≥ 1.2 gegenüber der unbedingten Tail-Event-Rate
  out-of-sample in ≥ 2 disjunkten Zeitfenstern**, UND **NB signifikant überdispers gegen Poisson
  per Likelihood-Ratio-Test (p < 0.05)** — sonst ist k nicht identifizierbar (Critic R2 §M-S22/FA).
  Begründung Startwert: Lift 1.2 = 20 % über Basisrate, die minimal verwertbare Anhebung der
  Tail-Treffergenauigkeit aus der Scout-Spezifikation.
- **Abbruchkriterium:** Lift ≤ 1.2 OOS in einem Fenster ODER NB nicht signifikant überdispers
  (p ≥ 0.05) → verwerfen, dokumentieren.
- **Aufwand:** **S** (Standard-NB-ML; kritisch nur Mindest-Kaskadenzahl — für BTC/ETH ausreichend,
  für illiquide Alts nicht).

---

### 4.3 M-S13 — Avalanche Shape Collapse / universelle Skalenfunktion (Rang 3)

- **Ursprungsdomäne & Analogie:** Statistische Physik / crackling noise (Nature 2001, Nat. Phys.
  2011, Nat. Commun. 2014/2017). Strukturmatch: Liquidationskaskade = Burst-Profil (Aktivitätsrate
  über Zeit) — exaktes Objekt der crackling-noise-Theorie (Critic R1 §M-S13/#5).
- **Mechanismus:** Reskaliert man Bursts auf gemeinsame Dauer/Höhe, kollabieren sie (universell) auf
  eine invertierte Parabel. Aus der Profilform der *laufenden* Kaskade lässt sich die **Restdauer**
  prognostizieren. Edge-Hypothese: nirgends repliziertes Restdauer-Signal.
- **Datenbedarf:** `allLiquidation.{symbol}` (#12); Bulk-Download (#34) für Kaskaden-Statistik.
  Beide CONFIRMED.
- **Validierungsdesign:** Burst-Detektion + Reskalierung; Collapse-Funktion aus Trainings-Bursts,
  Restdauer-Prognose OOS. Parameterfrei bis auf Detektionsschwelle und Fenstergröße.
- **Validierungs-Gate:** **Collapse-Residual ≤ 30 % in ≥ 2 disjunkten Zeitfenstern OOS** UND
  **Restdauer-MAE besser als die einer Konstant-Mittelwert-Baseline** (Critic R1 §M-S13/FA).
  Begründung Startwert: 30 % Residual ist die im Scout gesetzte Grenze für einen tragfähigen
  universellen Kollaps; darüber ist keine universelle Form gegeben.
- **Abbruchkriterium:** Collapse-Residual > 30 % OOS ODER MAE nicht besser als Konstant-Baseline →
  verwerfen, dokumentieren.
- **Aufwand:** **M** (braucht viele Kaskaden für stabilen Collapse; Burst-Detektion/Reskalierung
  rechenintensiver als Schwellwert-Signale).

---

### 4.4 M-S11 — Natural Time κ₁-Ordnungsparameter (Rang 4)

- **Ursprungsdomäne & Analogie:** Seismologie / Natural Time Analysis (PNAS 2011, EPL 2010).
  Strukturmatch: Liquidations-Punktprozess identisch zur seismischen Sequenz (markierter
  Punktprozess mit Energiemarken) (Critic R1 §M-S11/#5).
- **Mechanismus:** κ₁ (Varianz der natural-time-gewichteten Marken) nähert sich beim Übergang zur
  Kritikalität dem universellen Wert **0.070**. Edge-Hypothese: Annäherung an Kritikalität
  signalisiert bevorstehende Kaskade. **Eigenständiger zweiter Kaskaden-Indikator** mit anderem
  math. Kern als M-S21 (Ensemble-Diversität, synthesis.md §3-Redundanztabelle).
- **Datenbedarf:** `allLiquidation.{symbol}` (#12), `publicTrade.{symbol}` (#8); Bulk-Download (#34).
  Alle CONFIRMED.
- **Validierungsdesign:** κ₁ über rollierendes Ereignisfenster N; Schwelle aus Theorie fix
  (0.065–0.075 um den universellen Wert 0.070), nicht gefittet. Walk-forward.
- **Validierungs-Gate:** **ROC-AUC ≥ 0.55 out-of-sample (walk-forward) in ≥ 2 disjunkten
  Zeitfenstern** für die Kaskaden-Vorhersage (Critic R1 §M-S11/FA). Begründung Startwert: AUC 0.55
  ist die in der Rollendefinition genannte Mindest-OOS-Diskriminierung über Zufall (0.50).
  Zusatz-Disziplin: gegen M-S21 als Schwester-Indikator vergleichen (liefert κ₁ inkrementelle
  Information über Rₜ hinaus?).
- **Abbruchkriterium:** ROC-AUC ≤ 0.55 OOS in einem Fenster → verwerfen; falls AUC > 0.55, aber kein
  inkrementeller Beitrag über M-S21 → als redundant zurückstellen (nicht verwerfen).
- **Aufwand:** **S** (reiner WS-Stream; κ₁ = Varianz einer gewichteten Folge, trivial).

---

### 4.5 M-S23 — Smith-Waterman Local Alignment + Profil-HMM auf symbolisiertem Orderflow (Rang 5)

- **Ursprungsdomäne & Analogie:** Bioinformatik (Smith & Waterman 1981; Eddy 1998). Strukturmatch:
  symbolisierter Orderflow ↔ DNA/Protein-Sequenz — diskrete Symbolsequenzen mit lokalem
  Wiederholungsmuster; SW wurde für genau diese Objektklasse entwickelt (Critic R2 §M-S23/#5).
- **Mechanismus:** Algorithmische Ausführungs-Engines erzeugen lokal wiederkehrende, längenvariable,
  verrauschte Teilsequenzen. SW/Profil-HMM tolerieren Gaps/Insertionen, die exakte Muster-Suche und
  LZ/DTW verfehlen. Edge-Hypothese: Antizipation von Bot-/Iceberg-Orderwellen über Motiv-Alignment.
  Absorbiert M-S18 (das die L1-Symbolisierung liefert, synthesis.md §3).
- **Datenbedarf:** `publicTrade.{symbol}` (#8); Bulk-Download (#34) für Motiv-Bibliotheks-Kuratierung.
  Beide CONFIRMED.
- **Validierungsdesign:** Festes Symbolisierungsschema {B,b,S,s} (aus M-S18 rev.2, 90.-Perzentil-
  Größenschwelle, kein Fitting). **Motiv-Bibliothek ausschließlich auf Trainings-Split kuratiert**
  (Look-Ahead-Sperre). Walk-forward.
- **Validierungs-Gate:** **Balanced Accuracy ≥ Zufallsbasis out-of-sample (walk-forward) in ≥ 2
  disjunkten Zeitfenstern** (konkret ≥ 0.55 über 0.50-Basis), UND **Surrogate-Test bestanden:
  dieselbe Pipeline auf blockweise permutierten Sequenzen liefert kein Signal (p < 0.05)** (Critic
  R2 §M-S23/FA). Begründung Startwert: Surrogate-Schwelle p < 0.05 ist Standard; 0.55 wie bei den
  übrigen direktionalen Gates.
- **Abbruchkriterium:** Balanced Accuracy ≤ 0.55 OOS ODER Surrogate-Test nicht bestanden (p ≥ 0.05,
  Signal nicht von Zufallsstruktur unterscheidbar) → verwerfen, dokumentieren.
- **Aufwand:** **M** (Bibliotheks-Kuratierung aufwändig; Overfitting-Risiko mittel-hoch über
  Substitutionsmatrix/Gap-Penalties — Surrogate-Test + strikter Split sind hinreichende, aber nicht
  eliminierende Kontrolle, Critic R2 §M-S23/#1).

---

### 4.6 M-Q11 — Multi-Level Order Book Imbalance (Rang 6)

- **Ursprungsdomäne & Analogie:** Marktmikrostruktur (Cont et al. 2014, OFI). Keine Cross-Domain —
  klassische Quant-Methode, **breitester L3-Anker für Synergien** und schnellster Baseline-Test.
- **Mechanismus:** Informierter Flow hinterlässt Imbalance-Muster in der Orderbuch-Tiefe. Retail-
  Edge durch *längere* Aggregationsfenster (5–60 s), die unter der HFT-Arbitragegrenze liegen.
- **Datenbedarf:** `orderbook.50/200.{symbol}` (#2–3), `publicTrade.{symbol}` (#8), Bulk-Snapshots
  (#34) fürs Backtesting. Alle CONFIRMED.
- **Validierungsdesign:** OBI-Aggregation über 5–60 s; walk-forward über 90-Tage-OOS-Fenster,
  wiederholt für ≥ 2 disjunkte Fenster. Purged CV wegen überlappender Aggregationsfenster.
- **Validierungs-Gate:** **Information Coefficient (IC) ≥ 0.03 in 90-Tage-OOS-Fenster, in ≥ 2
  disjunkten Fenstern** (Critic R1 §M-Q11/FA). Begründung Startwert: Literatur berichtet IC ~0.10
  (Coinmonks 2025); 0.03 ist die konservative Mindestschwelle, unter der das Signal als verschwunden
  gilt. Nach-Kosten-Prüfung: erwarteter Edge bei 60-s-Horizont muss > 0.11 % sein.
- **Abbruchkriterium:** IC < 0.03 OOS in einem Fenster → verwerfen; falls IC ≥ 0.03, aber
  Nach-Kosten-Edge < 0.11 % → als nicht eigenständig profitabel kennzeichnen, nur als Synergie-/
  CP-Testfall (M-Q17) weiterführen.
- **Aufwand:** **S** (Aggregation trivial; Engpass ist L2-Bulk-Historie für OOS-Tiefe, §3).

---

### 4.7 M-S14 — Cyclostationary Cyclic Spectrum + CFAR-Detektion (Rang 7)

- **Ursprungsdomäne & Analogie:** Radar/Kommunikationstechnik (Gardner, cyclostationary signal
  processing). Strukturmatch: Inter-Arrival-Zeitreihe ↔ moduliertes Signal im Rauschen (Critic R1
  §M-S14/#5).
- **Mechanismus:** TWAP/Iceberg-Bots erzeugen periodische Muster in Inter-Arrival-Zeiten; das Cyclic
  Spectrum (SCF) macht sie sichtbar, CFAR detektiert Peaks bei kontrollierter Falschalarmrate.
  Edge-Hypothese: Bots ändern ihr Muster nur, wenn sie erkannt werden (Persistenz testbar).
  Orthogonal zu M-S23 (Frequenz- vs. Sequenzdomäne) → Kreuzvalidierung (synthesis.md §5-B).
- **Datenbedarf:** `publicTrade.{symbol}` (#8), Inter-Arrival-Zeiten aus dem Event-Stream. CONFIRMED.
- **Validierungsdesign:** Zyklusfrequenzen im Trainingsfenster entdeckt, im Test-Fenster validiert;
  rollierende SCF-Schätzung (SSCA). Walk-forward.
- **Validierungs-Gate:** **Peak-Stabilität gegen Surrogate (geshuffelte Inter-Arrivals) bestanden,
  p ≤ 0.05, in ≥ 2 disjunkten Zeitfenstern** (Critic R1 §M-S14/FA). Begründung Startwert: p ≤ 0.05
  trennt echte zyklische Struktur von Zufalls-Peaks; Standard-Surrogate-Schwelle.
- **Abbruchkriterium:** Peak nicht stabil gegen Surrogate (p > 0.05) in einem Fenster ODER
  detektierte Lead-Zeit < 50 ms Retail-Latenz (nicht handelbar, data_audit §5.3) → verwerfen.
- **Aufwand:** **M** (SCF rechenintensiv, VPS nötig; gelbe Flagge Kostenrealität — Sekunden-Horizont
  kann unter Fee-Schwelle fallen; als Forschungssignal, nicht HFT, behandeln, Critic R1 §M-S14/#3).

---

### 4.8 M-Q12 — Funding-Rate Contrarian (Extremwert) (Rang 8)

- **Ursprungsdomäne & Analogie:** Derivate-Mikrostruktur. Keine Cross-Domain — robuster, REST-only,
  mittelfristiger Anker (fee-tauglich).
- **Mechanismus:** Extreme Funding-Rate → Überextension durch Haltekosten und Arbitrage-Kapital →
  Zwangskorrektur. Konträres Direktionalsignal auf 24-h-Horizont. Abgegrenzt vom (arbitrierten)
  naiven Carry.
- **Datenbedarf:** `tickers.{symbol}` (#9), Funding History REST (#26), Premium-Index (#21), OI (#27).
  Alle CONFIRMED.
- **Validierungsdesign:** Extremwert-Trigger ±2σ über 30-Tage-Fenster; walk-forward über
  180-Tage-OOS, ≥ 2 disjunkte Fenster.
- **Validierungs-Gate:** **Mittlerer Contrarian-Return > 0 auf 24-h-Basis, out-of-sample über
  180-Tage-Fenster, in ≥ 2 disjunkten Fenstern, nach Kosten (> 0.11 % je Round-Trip)** (Critic R1
  §M-Q12/FA). Begründung Startwert: Vorzeichen-positiver Nach-Kosten-Return auf 24-h-Horizont ist
  das minimale Profitabilitätskriterium; engere Sharpe-Schwellen sind bei 180 Tagen schätzunsicher.
- **Abbruchkriterium:** Contrarian-Return ≤ 0 (nach Kosten) OOS in einem Fenster → verwerfen.
  Hinweis: schneller Zerfall erwartet (Community-bekannt, Critic R1 §M-Q12/#4) — Persistenz mitprüfen.
- **Aufwand:** **S** (REST-only, kein Echtzeitbedarf, kein HFT).

---

### 4.9 M-S17 — Persistent Homology auf Orderbuch-/IV-Surface (Rang 9)

- **Ursprungsdomäne & Analogie:** Topologische Datenanalyse (Gidea & Katz 2018; arXiv 2604.13311).
  Strukturmatch: Orderbuch als 2D-Punktwolke (Preis × Volumen), IV-Surface als 3D-Mannigfaltigkeit
  (Strike × Expiry × IV) — native PH-Eingabeobjekte (Critic R1 §M-S17/#5).
- **Mechanismus:** Topologische Löcher = Liquiditätslücken; PH erfasst globale Form, die skalare
  Features verpassen. Ein topologischer Bruch in der IV-Surface dient als Tail-Risk-/Vola-
  Frühwarnung. Eigenständige Vola/Risiko-Schicht.
- **Datenbedarf:** `orderbook.200/500.{symbol}` (#3–4), `tickers.{symbol}` Option (#10) für
  IV-Surface; Bulk-Download (#34) für L2-Historie. CONFIRMED (Einschränkung: L2-Historie nur Bulk).
- **Validierungsdesign:** Rips-Komplex / Persistence-Diagramm (Ripser/Gudhi); Schwellwert für
  „signifikanten" Topologie-Bruch als einziger Parameter. Walk-forward; Snapshot-Historie aus Bulk.
- **Validierungs-Gate:** **Precision@k über Zufallsbasis out-of-sample in ≥ 2 disjunkten
  Zeitfenstern** (konkret Precision@k ≥ 1.2× Zufallsbasis, analog M-S22-Lift) (Critic R1 §M-S17/FA).
  Begründung Startwert: 1.2× Lift ist die minimal verwertbare Anhebung der Ereignis-Treffergenauig-
  keit, konsistent mit M-S22.
- **Abbruchkriterium:** Precision@k ≤ Zufallsbasis (Lift ≤ 1.2) OOS in einem Fenster → verwerfen.
- **Aufwand:** **M** (PH rechenintensiv; Ripser/Gudhi retail-tauglich, aber nicht trivial; OOS-Tiefe
  durch L2-Bulk-Limit beschränkt).

---

### 4.10 M-Q14 — Volatilitäts-Risikoprämie (Short-Vola Options) (Rang 10)

- **Ursprungsdomäne & Analogie:** Optionspreistheorie (arXiv 2410.15195; J. Futures Markets 2025).
  Keine Cross-Domain — strukturell langlebigster Edge (Risikoprämie), aber höchste Eintrittsschwelle.
- **Mechanismus:** Strukturelle Absicherungsnachfrage → systematisch überbewertete IV → ernterbare
  Prämie (IV − RV). Aus Aktienoptionen bewährt, für Krypto empirisch bestätigt.
- **Datenbedarf:** `tickers.{symbol}` Option (#10, IV/Greeks public), Hist. Volatility REST (#29),
  Kline (#18). Alle CONFIRMED.
- **Validierungsdesign:** Short-Vola mit Delta-Hedge; ATM-fokussiert (geringes Overfitting). OOS über
  12 Monate, walk-forward, ≥ 2 disjunkte Fenster. Options-Taker-Fee 0.03 % (niedriger als Perp).
- **Validierungs-Gate:** **(IV − RV) ≥ 3 % im 12-Monats-OOS, in ≥ 2 disjunkten Fenstern**, als
  Bedingung dafür, dass die Prämie nach Hedging-Kosten ernterbar bleibt (Critic R1 §M-Q14/FA).
  Begründung Startwert: 3 % ist die in der Quant-Literatur als ernterbar belegte Mindest-VRP für
  Krypto nach Transaktions-/Hedging-Reibung.
- **Abbruchkriterium:** (IV − RV) < 3 % OOS in einem Fenster → verwerfen. Zusätzliche Schwelle:
  Mindestkapital ~$5k wegen Margin/Delta-Hedge — unter dieser Schwelle nicht für Retail (Critic R1
  §M-Q14/RM).
- **Aufwand:** **L** (Delta-Hedging, Margin, Rollover; Options-Liquidität auf Bybit limitiert).

---

## 5. Kombinationsstrategien

Aus synthesis.md §5. Jede Strategie mit ihrer **schwächsten Annahme** (Bruchpunkt). Alle Pipelines
nutzen M-Q17 Conformal Prediction als **L4-Querschnitts-Kalibrator** (kein Alpha-Generator,
synthesis.md §7): er liefert ein verteilungsfreies Konfidenzband über das jeweilige L3-Signal →
Sizing nur bei engem Intervall. CP-Gate (Critic R1 §M-Q17/FA): 90 %-Intervall deckt ≥ 85 % der
OOS-Fälle.

### Strategie A — „Epidemiologisches Kaskaden-Cockpit" (L5-Kern)
**Pipeline:** `allLiquidation` → M-S21 (Rₜ) + M-S22 (NB-k) + M-S13 (Restdauer) → gemeinsames
Kaskaden-Risiko-Gate → M-Q17 (CP) → Sizing/Exit.
**Stärke:** Höchstgerankte Methoden, kohärentes Branching-Framework.
**Schwächste Annahme:** Liquidations-Folgeereignisse lassen sich über ein **stabiles
Generationszeit-/Serienintervall-Fenster** zuverlässig dem Auslöser zuordnen. Ist das Fenster
instabil oder mehrskalig, brechen Rₜ und NB-k **gemeinsam** (korrelierter Fehler — beide teilen ω_s).

### Strategie B — „Algorithmischer Footprint-Detektor" (L1→L3)
**Pipeline:** `publicTrade` → M-S18-Symbolisierung (L1) → M-S23 (Motiv-Alignment) ∥ M-S14 (Cyclic
Spectrum) → Konsens-Filter (beide einig = Signal) → M-Q17.
**Stärke:** Zwei orthogonale Detektoren auf gemeinsamer Symbolisierung; Kreuzvalidierung senkt
Falsch-Positive.
**Schwächste Annahme:** Algorithmische Muster **persistieren** über das Validierungsfenster hinaus.
Bei adaptivem Gegner (Bots ändern Muster) zerfällt der Edge in beiden Detektoren gleichzeitig.
Zusatzrisiko: Sekunden-Horizont unter Fee-Schwelle.

### Strategie C — „Regime-konditioniertes Richtungs-Signal" (L2→L3→L4)
**Pipeline:** M-S15 (Funding-Rauschregime) + M-Q16 (OI-Strukturbruch) → Regime-Gate → M-Q11 (OBI) +
M-Q12 (Funding-Contrarian) + M-Q18 (L/S-Extrem) regime-gefiltert → M-Q17 → Sizing.
**Stärke:** Verbindet die robustesten Quant-Signale (Score 15) mit einem Regime-Filter gegen ihre
bekannte Achillesferse (Regime-Abhängigkeit).
**Schwächste Annahme:** Das detektierte Regime ist zum Handelszeitpunkt **noch gültig** (keine zu
hohe Detektions-Latenz). Bei trägem Regime-Signal handelt man im bereits gewechselten Regime.

### Strategie D — „Topologisch-direktionaler Options-Block" (L3 Vola+Richtung)
**Pipeline:** IV-Surface (`tickers` Option) → M-S17 (PH-Bruch) + M-Q15 (25Δ-Skew, mit
Liquiditäts-Check) → konditioniert M-Q14 (VRP-Short-Vola, Strike-/Hedge-Wahl) → M-Q17.
**Stärke:** Nutzt die öffentliche Greeks/IV-Surface; M-S17 liefert Tail-Frühwarnung, die das nackte
Short-Vola-Risiko von M-Q14 absichert.
**Schwächste Annahme:** **Bybit-Options-Liquidität reicht** für verlässliche Skew-/Surface-Messung.
Laut M-Q15 rev.2 fällt der Liquiditäts-Vorab-Check an 60–80 % der Stunden für OTM-Strikes durch →
Signalfrequenz/Surface-Auflösung möglicherweise zu dünn. (M-Q15 nur als Synergiesignal hier, nicht
standalone — synthesis.md §7.)

### Strategie E — „Cross-Coin-Contagion-Lead" (L2/L3 Risiko-Timing)
**Pipeline:** Multi-Symbol `allLiquidation` → M-S16 (CCM, Kopplungsrichtung) → treibender vs.
nachlaufender Coin → M-S21/M-S22 auf den nachlaufenden Coin → M-Q17.
**Stärke:** Einzige Strategie, die Cross-Asset-Information nutzt.
**Schwächste Annahme:** Die **CCM-Takens-Einbettung** gilt für höherdimensionale, verrauschte
Multi-Coin-Liquidationsströme (Critic: Analogie gestreckt). Zusatz: detektierter Lead-Lag muss >
50 ms Retail-Latenz sein, sonst nicht handelbar.

---

## 6. Validierungs-Roadmap

**Prinzip:** Quick Wins zuerst (niedrigster Aufwand × höchster Ranking-Wert), dann das
Kaskaden-Framework vervollständigen, dann die rechenintensiven und kapitalintensiven Methoden.
Reihenfolge folgt dem Synthese-Ranking, moduliert um den Aufwand (S vor M vor L).

### Entscheidungsbaum (für jede Methode identisch)
```
Methode aufsetzen → Kalibrierung auf Trainings-Split (Parameter fixieren)
   → Walk-Forward-OOS über ≥ 2 disjunkte Fenster
      → Gate bestanden in BEIDEN Fenstern?
          JA  → Methode „nicht verworfen"; in Kombinationsstrategie integrieren (§5),
                CP-Kalibrierung (M-Q17) anlegen → nächste Methode
          NEIN → VERWERFEN, in §7-Wissensspeicher mit Gate-Wert + Fenster dokumentieren
                 → nächste Methode (kein Re-Tuning desselben Gates — sonst Multiple Testing, §8)
```

### Phasen & grobe Zeitschätzung

| Phase | Methoden | Aufwand | Zeit (grobe Schätzung) |
|---|---|---|---|
| **P1 — Quick Wins** | M-S21 (Rₜ), M-Q11 (OBI) | S | 1–2 Wochen |
| **P2 — Kaskaden-Framework vervollständigen** | M-S22 (NB-k), M-S11 (κ₁), M-S13 (Shape Collapse) | S/S/M | 3–4 Wochen |
| **P3 — Strategie A zusammensetzen** | A = M-S21+M-S22+M-S13 + M-Q17 (CP) | M | 2 Wochen |
| **P4 — Footprint & Regime** | M-S23, M-S14 (Strategie B); M-Q12 (Strategie C) | M/M/S | 4–5 Wochen |
| **P5 — Topologie & Options** | M-S17, M-Q14 (Strategie D) | M/L | 4–6 Wochen |
| **P6 — Cross-Coin (optional)** | M-S16 + Kaskaden-Paar (Strategie E) | M | 2–3 Wochen |

**Gesamthorizont:** grob 16–22 Wochen für die volle Top-10-Validierung; erstes falsifizierbares
Ergebnis (M-S21-Gate) bereits in P1 nach Tagen verfügbar.

**Quick-Win-Begründung (synthesis.md §6):** M-S21 maximiert das Ranking-Profil bei minimaler
Infrastruktur (geschlossene Posterior-Form, reiner Stream); M-Q11 maximiert Belegtheit und
Geschwindigkeit (Standard-Walk-Forward) und dient zugleich als L3-Synergie-Anker und CP-Testfall.
Zusammen decken sie L5 (Risiko) und L3 (Richtung) ab.

---

## 7. Verworfene / zurückgestellte Methoden (Wissensspeicher)

Negative Ergebnisse und bewusste Zurückstellungen sind Wissen. Diese Tabelle hält fest, was **nicht**
in die Top-10 ging und warum (alle aus den 19 methodPASS-Methoden; keine wurde fachlich „verworfen",
aber die folgenden wurden im Ranking/in der Synthese zurückgestellt). Verworfen wird zur Laufzeit
zusätzlich jede Top-10-Methode, deren Gate (§4) reißt — dann hier mit Gate-Wert nachzutragen.

| Methode | Score/NOV | Status | Begründung |
|---|---|---|---|
| **M-S18** NCD / Lempel-Ziv | 13/3 | Zurückgestellt → **Infrastruktur** | Redundant zu M-S23 als Signalgenerator (gleiche symbolisierte `publicTrade`-Basis); bleibt wertvoll als L1-Symbolisierungs-Layer für M-S23 (synthesis.md §3). |
| **M-Q13** Liquidations-Hawkes | 14/2 | Zurückgestellt → **Baseline** | Redundant zu M-S21 in der Kaskaden-Detektion; niedrigere Novelty (2 vs. 4). Bleibt als etablierte Brier-Score-Referenz im M-S21-Gate. |
| **M-S15** Allan-Varianz | 13/3 | Knapp außerhalb | Tragfähiger formaler Match, aber NOV nur 3 und schwächerer kausaler Mechanismus (Beschreibungsebene). Nutzbar als Regime-Layer in Strategie C. |
| **M-S16** Convergent Cross Mapping | 12/3 | Knapp außerhalb | Takens-Analogie für höherdimensionale, verrauschte Multi-Coin-Ströme gestreckt (Critic R1 §M-S16/#5); Lead-Lag-Handelbarkeit gegen 50-ms-Latenz unsicher. Kern von Strategie E. |
| **M-S12** AE Improved b-value | 12/3 | Knapp außerhalb | Schwächerer Mechanismus (Whale-Akkumulation spekulativ), schwächeres Falsifizierungskriterium in R1; NOV 3. |
| **M-Q15** IV-Skew-Dynamik | 12/2 | Zurückgestellt → **nur Synergie** | Bybit-Options-Liquidität strukturell limitierend (OI 2–3 % global; Liquiditäts-Check fällt 60–80 % der Stunden durch). Nur als Synergiesignal mit M-Q14 in Strategie D. |
| **M-Q16** OI-Strukturbruch CUSUM | 12/2 | Knapp außerhalb | NOV 2, Community-bekannt → schneller Zerfall erwartet. Nutzbar als Regime-Layer in Strategie C. |
| **M-Q17** Conformal Prediction | 12/3 | **Querschnitts-L4** | Kein Alpha-Generator; bewusst nicht als eigenständige Methode gerankt, sondern als universeller Kalibrator über alle L3-Signale (synthesis.md §7). |
| **M-Q18** L/S-Ratio Extreme | 12/2 | Knapp außerhalb | NOV 2, eine Nicht-Peer-Review-Quelle, Sharpe-Gate aus 90 Tagen schätzunsicher. Nutzbar als Sentiment-Input in Strategie C. |

---

## 8. Risiken & offene Fragen

**Multiple-Testing / Selbsttäuschung (Hauptrisiko):** Über 10 Methoden × ≥ 2 Fenster werden viele
Gates geprüft. Bei α = 0.05 pro Surrogate-/Signifikanztest ist mit Falsch-Positiven zu rechnen.
**Gegenmaßnahmen (Pflicht):** (a) Kein Re-Tuning eines gerissenen Gates und erneuter Test mit
demselben Datensatz — das ist verdecktes Multiple Testing; eine Methode wird beim ersten gerissenen
Fenster verworfen. (b) Family-wise-Korrektur (z. B. Holm-Bonferroni) über die Gesamtzahl der
parallelen Signifikanztests, oder vorab pro Methode auf je *ein* primäres Gate festlegen. (c) Die
≥-2-disjunkte-Fenster-Regel ist selbst eine Replikationshürde gegen Glücksfunde.

**Datenrisiken:**
- L2-Orderbuch-Historie nur als Bulk (#34, max 5 Pairs) oder Tardis 1 Tag/Monat (#35) → begrenzte
  OOS-Tiefe für M-Q11, M-S17. Offene Frage: reicht die freie Historie für ≥ 2 disjunkte 90-Tage-OOS?
- OI nur 5-min-Granularität → begrenzt M-Q16-Auflösung.
- Kein historisches Greeks-Archiv → M-Q14/M-S17-IV-Surface-Backtests müssen live mitgeschrieben
  werden (Vorlauf nötig).
- `allLiquidation` ist der neue vollständige Feed (ab 2024); Bulk-Historie davor kann unvollständig
  sein → Serienintervall-Schätzung (M-S21/M-S22) auf hinreichend rezenter Historie kalibrieren.

**Methodikrisiken:**
- **Korrelierter Fehler im Kaskaden-Framework:** M-S21 und M-S22 teilen ω_s; ein falsch geschätztes
  Generationszeit-Fenster bricht beide. Strategie A ist daher nicht so diversifiziert wie sie wirkt.
- **Adaptiver Gegner:** M-S14/M-S23-Edges hängen von Muster-Persistenz ab; Bots können adaptieren.
- **Regime-Latenz:** Strategie C handelt evtl. im bereits gewechselten Regime.
- **Kostenrealität bei Sekunden-Signalen:** M-S14 (und teils M-S23) könnten unter die 0.11-%-Schwelle
  fallen → als Forschungs-/Risiko-Signal behandeln, nicht als HFT-Entry.

**Offene Fragen:**
1. Ist das Serienintervall ω_s über Marktregime stabil, oder mehrskalig/zeitvariabel?
2. Reicht die kostenlose L2-Bulk-Historie für zwei disjunkte OOS-Fenster auf BTC/ETH?
3. Liefert M-S11 (κ₁) inkrementelle Information über M-S21 (Rₜ) hinaus, oder ist es redundant?
4. Genügt die Bybit-Options-Liquidität für eine verlässliche IV-Surface (Strategie D)?

---

## 9. Anhang — Quellenliste (URLs)

**Bybit-Datenfundament (data_audit.md):**
- Bybit API v5 Doku — https://bybit-exchange.github.io/docs/v5/
- WS Orderbook — https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
- WS Trade — https://bybit-exchange.github.io/docs/v5/websocket/public/trade
- WS Ticker — https://bybit-exchange.github.io/docs/v5/websocket/public/ticker
- WS All Liquidation — https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation
- WS Kline — https://bybit-exchange.github.io/docs/v5/websocket/public/kline
- REST Kline — https://bybit-exchange.github.io/docs/v5/market/kline
- REST Premium Index Kline — https://bybit-exchange.github.io/docs/api-explorer/v5/market/premium-index-kline
- REST Funding History — https://bybit-exchange.github.io/docs/v5/market/history-fund-rate
- REST Open Interest — https://bybit-exchange.github.io/docs/v5/market/open-interest
- REST Long/Short Ratio — https://bybit-exchange.github.io/docs/v5/market/long-short-ratio
- REST Historical Volatility — https://bybit-exchange.github.io/docs/v5/market/iv
- REST Tickers — https://bybit-exchange.github.io/docs/v5/market/tickers
- Rate Limits — https://bybit-exchange.github.io/docs/v5/rate-limit
- Fee Structure — https://www.bybit.com/en/help-center/article/Trading-Fee-Structure
- Historical Data (Bulk) — https://www.bybit.com/derivatives/en/history-data
- Tardis.dev Bybit — https://docs.tardis.dev/historical-data-details/bybit

**Methoden-Primärquellen (aus critic_report_1/2 und round-Dateien):**
- M-S21 Cori et al. 2013, Am. J. Epidemiology (Renewal-Rₜ); Wallinga & Teunis 2004, Am. J. Epidemiology
- M-S22 Lloyd-Smith et al. 2005, Nature 438 (Superspreading/NB-k); BMC Public Health 2023 (Meta-Analyse)
- M-S13 Crackling noise: Nature 2001; Nature Physics 2011; Nature Communications 2014/2017
- M-S11 Natural Time: PNAS 2011; EPL 2010; Mintzelas & Kiriakopoulos 2016 (Finanz-Vorarbeit)
- M-S23 Smith & Waterman 1981, J. Mol. Biol.; Eddy 1998, Bioinformatics; Lin/Keogh 2007 (SAX)
- M-S14 Gardner (cyclostationary signal processing, foundational)
- M-S17 Gidea & Katz 2018, Physica A; arXiv:2604.13311 (2026); Ripser/Gudhi
- M-S18 Cilibrasi & Vitányi 2005, IEEE Trans. Inf. Theory
- M-S15 Hampton 2012, Physica A; Maciuca, SSRN
- M-S16 Sugihara et al. 2012, Science (CCM); Ye et al. 2015, Sci. Rep.
- M-Q11 Cont et al. 2014 (OFI); arXiv:2602.00776 (2026); Coinmonks 2025 (IC ~0.10)
- M-Q12 SSRN 5576424 (2025); BIS WP 1087 (2024); arXiv:2510.14435 (2025)
- M-Q13 SSRN 5611392 (2025); Springer 2026 (Hawkes + Orderbuch)
- M-Q14 arXiv:2410.15195 (2024, BVRP); SSRN 6233752 (2025); Journal of Futures Markets 2025
- M-Q15 ScienceDirect 2024/2025 (IV-Skew); arXiv:2510.21297 (Jump-Risk-Premia)
- M-Q16 MDPI JRFM 18 (2025); MDPI Mathematics 14 (2025); arXiv:2512.00893
- M-Q17 arXiv:2511.13608 (2025); arXiv:2509.02844 (2025); arXiv:2601.18509 (2026)
- M-Q18 ScienceDirect 2025 (Sentiment); PubsOnLine 2024 (Crypto Carry)

> **Hinweis zu nicht-peer-reviewten/sekundären Quellen:** Coinmonks- und ainvest.com-Angaben sind
> als Praxisbelege markiert, nicht als peer-reviewte Primärquellen (Critic R1 §M-Q18/EQ).
> Latenz-/Infrastrukturangaben (data_audit §5.3) stammen aus Sekundärquellen (Medium, TradeWithVPS)
> und sind als Größenordnung, nicht als exakte Messung zu verstehen.

---

*Ende FINAL_PRD.md — Konzept- und Validierungs-Roadmap. Kein Code, Architektur nur auf
Skizzen-Niveau. Alle Top-10-Methoden mit out-of-sample Validierungs-Gate (≥ 2 disjunkte Fenster) und
explizitem Abbruchkriterium; Walk-Forward/OOS als Pflicht; Priorisierung nach Synthese-Score.*
