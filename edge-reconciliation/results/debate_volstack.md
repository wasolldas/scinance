# Debatte: Vol-Stack / RV-Prognose

**Cluster:** volstack (Vol-Stack / RV-Prognose)
**Claims:** C-10 (MF-DFA/Hölder), C-18 (PatchTST-RV), C-19 (TimesNet), C-20 (MOMENT), C-34 (GMM-Vol-Regime+VRP), C-35 (CEEMDAN), C-42 (LightGBM/HAR-RV-Baseline), CS-04 (Pattern×Foundation-Ensemble)
**Stand:** 2026-06-11
**Phase:** 4 — DEBATE

---

## Advocate

### Vorbemerkung — der entscheidende Rahmen dieses Clusters

Dieser Cluster unterscheidet sich fundamental von allen anderen Clustern der Reconciliation, und zwar aus einem einzigen Grund: **C-42 ist der EINZIGE positive Modell-Befund im gesamten Register.** Test-R²=0.249, Pearson=0.578, Apr-2026-OOS nach Jan–Mar-Training (C-42, alignment_matrix: PARTIAL — die stärkste positive Evidenz im Register). Alles andere im Register ist REFUTED (C-14, CS-01, CS-02), friction-bound-PARTIAL (C-22, CS-03) oder UNTESTED (48 von 56 Claims). In einem Register, dessen Grundton „Friktion > jede gemessene Edge" lautet (Kostenbaseline, Kernrelation), ist der Vol-Stack der einzige Ort, an dem überhaupt ein reproduzierbares prädiktives Signal dokumentiert ist.

**Der zentrale konzeptionelle Hebel — und die direkte Antwort auf INC-05:** INC-05 stellt fest, dass Richtungsprognose AUC ≈ 0.50 ist (Münzwurf, 1h/4h, klassische Features). Das ist KEIN Argument gegen den Vol-Stack — es ist das **stärkste Argument FÜR ihn**. Volatilität und Richtung sind orthogonale Prognoseziele. Dass die zweite Ordnung der Rendite (Varianz) mit R²=0.25 prognostizierbar ist, während die erste Ordnung (Vorzeichen) ein Münzwurf ist, ist genau das Muster, das die akademische Vol-Literatur seit Jahrzehnten dokumentiert: Vol clustert und ist persistent, Returns sind martingalnah. Der Vol-Stack erhebt **nirgends** einen Richtungsanspruch (C-42 ausdrücklich: „NICHT als Richtungssignal"). Damit ist er von der INC-05-Nullhypothese überhaupt nicht betroffen. Mein gesamtes Argument zeigt im Folgenden, welcher konkrete, geldwerte Edge aus reiner Vol-Prognose OHNE Richtungswissen entsteht.

Drei Edge-Kanäle existieren ohne jedes Richtungswissen:
1. **Positionssizing / Vol-Targeting** — konstante Risiko-Exposure statt konstanter Notional-Exposure hebt den Sharpe JEDER bereits positiven Strategie (mechanisch, nicht prognostisch).
2. **Options-Pricing / VRP-Ernte** — wenn man RV besser prognostiziert als der Markt sie in IV einpreist, ist die Differenz (IV²−RV) ein ernterbarer Edge, der die Optionsprämie und nicht die Spotrichtung handelt.
3. **Regime-/Stop-Kalibrierung** — friktionsbewusste, vol-skalierte Stops adressieren direkt den einzigen forensisch isolierten Verlusttreiber im ganzen Register (E-10: schlechteste Trades 1.7–3.0× länger gehalten; E-08: friktion-unbewusste Hard-Stops).

---

### A-1 — C-42 ist der Anker und der einzige deployable-Befund des gesamten Registers (alle Märkte, am stärksten Futures)

C-42 (LightGBM/HAR-RV, R²=0.249, Pearson=0.578, OOS) ist laut alignment_matrix der einzige Claim mit dokumentiertem deployable-Befund und „die stärkste positive Evidenz im gesamten Register". Die Quelle gibt explizit einen Train/Test-Split mit zeitlich disjunktem OOS-Fenster an (Jan–Mar Training → Apr Test) — also de facto **L1**, während das gesamte übrige Evidence-Register auf **L0** stagniert (GM-1: 17×L0). Damit ist C-42 nicht nur positiv, sondern auch das methodisch sauberste Einzelstück Evidenz im Register.

- **Spot:** Empfehlung PILOT. RV-Persistenz ist asset-, nicht venue-spezifisch; das LightGBM/HAR-Feature-Set (atr_60, Trade-Flow, MODWT-Wavelets) ist auf Spot-Klines unmittelbar reproduzierbar. Vol-Targeting auf Spot ist der direkteste, kostenärmste Anwendungsfall (kein Funding, keine Settlement-Mechanik).
- **Futures:** Empfehlung ADOPT-Kandidat / PILOT. Hier wurde C-42 erhoben (Bybit-Perp-nahe Features inkl. Funding/OI), und hier zahlt Vol-Targeting doppelt: Sizing + vol-skalierte Stops gegen den E-10-Tail.
- **Optionen:** Empfehlung PILOT (RV-Bein des VRP). RV-Prognose ist das eine der zwei Beine jeder VRP-Strategie (siehe A-5).
- **Stärkstes Einzelargument:** In einem Register, in dem jede gemessene Roh-Edge unter der Friktion liegt, ist R²=0.249 OOS der einzige dokumentierte, reproduzierbare prädiktive Befund — und er braucht für seinen primären Nutzen (Sizing) gar keine Richtungs-Edge.
- **Was ich zugestehe:** C-42 stammt aus research_notes (Kestrel-v1.4) und wurde NICHT in dieser Pipeline als E-xx re-validiert (alignment_matrix: „nicht unabhängig nachgeprüft → PARTIAL, nicht CONFIRMED"). Es gibt keine FDR-Betrachtung über die 36 Features (GM-2-Geist), keine unabhängige Reproduktion. Der Wert ist eine Selbstauskunft, kein durch diese Reconciliation bestätigter Befund.
- **Validierungs-Gate (PILOT):** Re-Train LightGBM/HAR auf Bybit-Klines mit purged-walk-forward (L2) über ≥ 2 disjunkte OOS-Fenster; Gate: OOS-R² ≥ 0.15 (konservativ unter dem behaupteten 0.249) UND QLIKE schlägt naive HAR-RV-Baseline. Mit vorhandenem Kline-Backfill in ~1–2 Wochen prüfbar — kein neuer Datenstrom nötig.

### A-2 — Vol-Targeting liefert einen Sharpe-Edge OHNE jede Richtungsprognose (direkte INC-05-Antwort)

Dies ist der mechanische Kern der INC-05-Antwort. Vol-Targeting skaliert die Positionsgröße invers zur prognostizierten Vola (size_t ∝ 1/σ̂_t). Bei R²=0.249 (C-42) ist σ̂_t informativ genug, um die realisierte Portfolio-Vola zu glätten — das hebt den Sharpe **jeder Strategie mit nicht-negativem Erwartungswert** rein mechanisch, weil Sharpe = E[R]/σ(R) und Vol-Targeting σ(R) senkt, ohne E[R] zu berühren. Es ist kein Alpha-Generator, sondern ein Risiko-Normalisierer — und genau deshalb von INC-05 unberührt.

- **Spot:** stark. Spot-Buy-and-Hold + Vol-Targeting ist die kanonische Anwendung; keine Hebel-, Funding- oder Liquidationsrisiken.
- **Futures:** am stärksten. Hier liegt der zweite Verlusttreiber des Registers: S3 verlor exit-/tail-getrieben (E-10), und vol-skalierte Position-Size dämpft die Tail-Exposure direkt. Vol-Targeting ist zudem Voraussetzung dafür, dass GM-3 (qty=1.0-Notional-Artefakt) überhaupt sinnvoll behoben werden kann — risikoäquivalentes statt notional-äquivalentes Sizing.
- **Optionen:** mittelbar (Delta-Hedge-Sizing in der VRP-Strategie, A-5).
- **Stärkstes Einzelargument:** Sharpe-Lift aus Vol-Targeting ist eine mathematische Identität bei informativem σ̂, kein empirisch zu hoffender Effekt — und vollständig immun gegen die AUC≈0.50-Nullhypothese.
- **Was ich zugestehe:** Der Lift ist multiplikativ auf eine bestehende positive E[R]. Existiert KEINE positive Basis-Strategie (und im Register existiert bisher keine einzige gemessene positive Edge!), dann hebt Vol-Targeting Null auf Null. Vol-Targeting ist Verstärker, nicht Quelle.
- **Validierungs-Gate (PILOT):** Backtest identische Basis-Strategie mit/ohne Vol-Targeting; Gate: Sharpe-Differenz ≥ +0.2 absolut bei gleichem Brutto-E[R] (analog C-34-Sizing-Gate). Sofort mit vorhandenen Replay-Daten prüfbar.

### A-3 — Vol-Prognose als Regime-Filter und friktionsbewusster Stop-Kalibrator adressiert den EINZIGEN isolierten Verlusttreiber des Registers

Die einzige Strategie mit forensisch isolierter Verlustursache ist S3/CS-03: E-10 zeigt, dass die schlechtesten Trades 1.7–3.0× länger gehalten wurden (Tail-Signatur, robust über 5 Symbole UND beide Richtungs-Arme), und E-08, dass die Hard-Stops friktion-unbewusst feuerten (33 Trades schlossen < −30 bps trotz Stop). Eine RV-Prognose liefert genau die fehlende Größe: einen vol-skalierten, friktionsbewussten Stop-Abstand und ein Regime-Gate, das in High-Vol-Phasen Exposure drosselt. Das ist reine Vol-Anwendung — kein Vorzeichen nötig.

- **Spot:** mittel (Stops weniger kritisch ohne Hebel, aber Regime-Drosselung in Crash-Phasen wertvoll).
- **Futures:** stark. Vol-skalierte Stops sind die direkte Reparatur des E-08/E-10-Defekts; der iter-5-Run (E-15) testet ohnehin friktion-bewusste Stops — eine RV-Prognose macht diese Stops adaptiv statt statisch.
- **Optionen:** mittel (Regime-Gate für VRP-Aktivierung, siehe A-5/A-6).
- **Stärkstes Einzelargument:** Der einzige Verlusttreiber, den das Register je forensisch isoliert hat (Halte-Dauer-Tail, E-10), ist exakt das, was eine RV-Prognose adressiert — und zwar ohne Richtungswissen.
- **Was ich zugestehe:** Die Tail-Signatur ist L0 aus einem einzigen ~24h-Fenster (GM-6); der stärkste Einzel-Tail (BNB −195 bps, E-11) ist ein Ein-Trade-Artefakt (N=16) und in iter-4 nicht reproduziert. Dass vol-skalierte Stops netto helfen, ist plausibel, aber im Register nicht gemessen — iter-5 (E-15) testet nur statische friktion-bewusste Stops, noch nicht vol-adaptive.
- **Validierungs-Gate (PILOT):** vol-skalierter Stop vs. statischer Stop auf S3-Trade-Population; Gate: Reduktion des mittleren Tail-Verlusts (worst-Dezil) ≥ 20 % bei Win-Rate-Verlust ≤ 5 %. Mit vorhandenem trades_all.csv + RV-Reihe in Tagen prüfbar.

### A-4 — C-10 (MF-DFA/Hölder) und C-35 (CEEMDAN) sind inkrementelle RV-Feature-Lieferanten mit billigem, hartem Falsifikations-Gate

C-10 (MF-DFA, ΔR² ≥ +0.02 / Tail-AUC > 0.60) und C-35 (CEEMDAN, ΔR² ≥ +0.01 + bit-für-bit-Kausalitätsnachweis) sind beide UNTESTED, aber sie teilen einen entscheidenden Vorzug gegenüber dem Rest des UNTESTED-Bergs: Ihr Validierungsanspruch ist **inkrementell und hart messbar** — ΔR² über die C-42-Baseline hinaus, nicht ein absoluter Direktionsanspruch. Das macht sie billig falsifizierbar und ankert sie an dem einen Befund, der funktioniert (C-42).

- **Spot:** PILOT (Feature-Beitrag asset-generisch; MF-DFA auf 1-min-Klines reproduzierbar).
- **Futures:** PILOT, primärer Markt. C-10 zielt zusätzlich auf Tail-AUC > 0.60 für „RV-Spike in 24h" — ein Regime-Frühwarner, der wieder reine Vol, keine Richtung ist.
- **Optionen:** schwach direkt; nur mittelbar über bessere RV-Schätzung fürs VRP-Bein.
- **Stärkstes Einzelargument:** Beide Module müssen sich gegen einen existierenden, funktionierenden Baseline-R² (C-42) beweisen — ein selten sauberes, hartes Inkrement-Gate, das Overfitting strukturell begrenzt.
- **Was ich zugestehe:** Keinerlei direkte Evidenz (alignment_matrix: beide UNTESTED, „Keine Evidenz"). C-35 trägt zudem ein reales Lookahead-Risiko (naive EMD ist nicht-kausal) — der Kausalitätsnachweis ist Pflicht, nicht Beiwerk, und nicht-trivial. Der inkrementelle Wert beider kann auch schlicht ΔR² ≤ 0 sein, dann sind sie wertlos.
- **Validierungs-Gate (PILOT):** Add-one-Feature-Test gegen C-42-Baseline mit purged-CV; Gate C-10: ΔR² ≥ +0.02; Gate C-35: ΔR² ≥ +0.01 UND bestandener bit-für-bit-Kausalitätstest, sonst Drop. Mit Kline-Backfill in 1–2 Wochen prüfbar.

### A-5 — Der Vol-Stack ist der EINZIGE evidenzgestützte Zugang zum Optionsmarkt — via VRP (C-34/C-33)

Optionen sind im ganzen Register ein unadressierter Markt (INC-04: kein IV-Archiv, Liquidität größtes Risiko). Aber genau hier ist die RV-Prognose nicht nur nützlich, sondern **konstitutiv**: Die Variance Risk Premium VRP = IV²−RV ist per Definition halb RV. Wer RV mit R²=0.249 prognostiziert (C-42), hat ein Bein des VRP-Trades bereits empirisch belegt. C-34 (GMM-Vol-Regime+VRP) und C-33 (Short-Vola/VRP-Ernte) sind damit die einzigen Options-Claims, deren prädiktiver Kern auf einem real gemessenen Befund ruht statt auf reiner Hypothese.

Entscheidend für die INC-05-Frage: VRP handelt die **Optionsprämie**, nicht die Spotrichtung. Der Edge entsteht, weil strukturelle Absicherungsnachfrage IV systematisch über die realisierte Vola hebt (C-33-Kernidee); man verkauft teure Vola und liefert günstigere realisierte Vola — delta-gehedged, also richtungsneutral. Das ist der Paradefall eines Edges aus reiner Vol-Prognose ohne Richtungswissen.

- **Spot:** n/a (kein Optionsmarkt-Bezug auf Spot direkt).
- **Futures:** mittelbar (VRP-Regime als G3-Gate konditioniert Futures-Strategien; C-34-Doppelfunktion L3-Gate + L5-Sizing).
- **Optionen:** PILOT — der einzige Markt-Eintritt mit empirischem Fundament. RV-Bein belegt (C-42), IV-Bein per Eigenaufzeichnung in 3 Monaten beschaffbar.
- **Stärkstes Einzelargument:** VRP ist der einzige Options-Edge im Register, dessen prädiktiver Kern (RV-Prognose) bereits mit OOS-R²=0.249 belegt ist statt nur behauptet — und er ist konstruktionsbedingt richtungsneutral.
- **Was ich zugestehe:** Das IV-Bein ist vollständig unbelegt — kein IV-Archiv existiert (INC-04, C-34/C-33: „kein IV-Archiv → Aufzeichnungs-Vorlauf"). Bybit-Options-Liquidität fällt laut Quelle in 60–80 % der Stunden durch den Liquiditäts-Check (CS-09-Annahme). Der ΔR²≥+0.02-Mehrwert des VRP-Kanals über RV-only ist ungemessen (C-34-Konfidenz-Note). Ohne IV-Strom ist das alles RV-only — also faktisch nur A-1 in neuem Gewand, bis ≥ 3 Monate IV aufgezeichnet sind.
- **Validierungs-Gate (PILOT):** Phase 0: ≥ 3 Monate ATM-markIv-Aufzeichnung. Dann Gate (IV−RV) ≥ 3 % im OOS in ≥ 2 Fenstern (C-33) UND VRP-Kanal-ΔR² ≥ +0.02 über RV-only (C-34); zusätzlich Liquiditäts-Gate: ATM-Buchtiefe ≥ Ordergröße in ≥ 40 % der Stunden, sonst Drop.

### A-6 — C-34 (GMM-Vol-Regime) liefert das Regime-Gate, das INC-05 selbst als Rettungsweg für ALLE Direktional-Claims benennt

INC-05 sagt nicht nur „unkonditional = Münzwurf" — es sagt auch explizit: „direktionale Claims nur regime-konditioniert (bedingte AUC > 0.55)". Damit benennt INC-05 selbst den Vol-Regime-Filter als die Bedingung, unter der Richtungssignale überhaupt eine Chance haben. C-34 (GMM auf RV-Feature-Vektoren → 4–6 diskrete Vol-Regime) IST dieser Filter. Der Vol-Stack liefert also nicht nur eigenständige Edges (A-1 bis A-5), sondern ist die **Enabling-Infrastruktur**, ohne die jeder Direktional-Ansatz im Register an INC-05 scheitert.

- **Spot:** mittel (Regime-Klassifikation generisch; aktiviert/drosselt Spot-Strategien).
- **Futures:** stark. C-34 ist als G3-Zustandsmaschine konzipiert, die Strategie-Familien regime-bedingt freischaltet (Carry nur Range, Kaskaden-Fade nur Stress) — exakt die regime-Konditionierung, die INC-05 fordert.
- **Optionen:** mittel (VRP-Kanal, siehe A-5).
- **Stärkstes Einzelargument:** INC-05 selbst nennt Regime-Konditionierung als einzigen Weg zu bedingter AUC > 0.55 — und C-34 ist genau dieser Regime-Klassifikator, gebaut auf dem einen funktionierenden Befund (RV).
- **Was ich zugestehe:** C-34 ist UNTESTED (alignment_matrix: „Keine direkte Evidenz"). Die kritische Annahme — GMM-Cluster persistent ≥ 24h ohne Flattern — ist ungeprüft; ein flatternder Regime-Klassifikator wäre schlimmer als keiner (Whipsaw-Kosten). Und: C-34 ist ein Gate/Enabler, kein Alpha-Generator — sein Wert ist vollständig davon abhängig, dass es ein zu konditionierendes Basissignal gibt, das ohne Gate verliert und mit Gate gewinnt. Ein solches Signal existiert im Register noch nicht.
- **Validierungs-Gate (PILOT):** GMM auf RV-Features fitten; Gate: Median-Regime-Persistenz ≥ 24h (Anti-Flatter) UND mindestens ein nachgelagertes Signal mit bedingter AUC > 0.55 in ≥ 1 Regime gegen unkonditional ≈ 0.50. Regime-Persistenz allein mit Kline-Backfill in Tagen prüfbar (billiger Vorab-Check, bevor Signal-Aufwand investiert wird).

### A-7 — CS-04 / C-18 / C-19 / C-20: schwächster Cluster-Teil, aber mit dem billigsten denkbaren Validierungspfad und einem klaren Mechanismus

Hier bin ich am defensivsten. CS-04 (Pattern×Foundation-Ensemble) lief nie (E-13: 0 Trades, insufficient_models 96–99.99 %), und C-18 (PatchTST), C-19 (TimesNet), C-20 (MOMENT) sind reine DL-Forecaster, die als Direktional-Ansprüche unter vollem INC-05-Revisionsdruck stehen. **Aber:** Drei Punkte tragen sie trotzdem in einen PILOT statt DROP.

Erstens — der Mechanismus ist real und C-42-validiert: Sobald diese Modelle auf das **RV-Ziel** (nicht das Richtungsziel) gerichtet werden — was PRD-kestrel für C-18/Q4 explizit tut („einziges empirisch belegtes Signal… Vol-Targeting und Stops, hartes R²-Gate") — fallen sie unter denselben funktionierenden Befund wie C-42. PatchTST-RV vs. HAR-RV ist ein reiner Modell-Wettbewerb gegen eine Baseline, die bei R²=0.249 nachweislich erreichbar ist. Zweitens — E-13 ist eine reine Loader-/Infrastruktur-Lücke, kein negativer Outcome-Befund (alignment_matrix, kritische Datenlücke #1: „Ein Verdrahtungs-Fix macht S4 sofort messbar"). Das ist der billigste Validierungspfad im ganzen Register: kein neuer Datenstrom, nur ein Verdrahtungs-Fix. Drittens — C-20 (MOMENT, Zero-Shot) hat einen spezifischen Nischenwert: Vol-Prognose auf neu gelistete Altcoins ohne Trainings-Historie, wo HAR/LightGBM mangels Lookback versagen.

- **Spot:** schwach/PARK (DL-Overkill, wo HAR/LightGBM bereits R²=0.249 liefern).
- **Futures:** PILOT, aber nur auf dem RV-Ziel und nur mit hartem „schlägt-HAR"-Gate; als Direktional-Ensemble DROP (INC-05).
- **Optionen:** n/a.
- **Stärkstes Einzelargument:** Auf das RV-Ziel gerichtet, müssen diese Modelle nur eine nachweislich erreichbare Baseline (C-42, R²=0.249) schlagen — und der Test dafür kostet bloß einen Loader-Fix (E-13), keinen neuen Datenstrom.
- **Was ich zugestehe:** Das ist der schwächste Teil meines gesamten Arguments. Die DL-Modelle sind UNTESTED/SUSPECT (C-18 PARTIAL nur geliehen über C-42, C-19/C-20 UNTESTED), ihre ursprünglichen Direktional-Gates (Dir-Accuracy ≥ 55 %) sind durch INC-05 faktisch widerlegt-erwartbar, und es gibt keinerlei Evidenz, dass ein 110M-Parameter-Transformer auf Single-GPU eine simple HAR/LightGBM-Baseline beim RV-R² überhaupt schlägt — die DL-Vol-Literatur zeigt oft, dass HAR schwer zu schlagen ist. Realistisch erwarte ich, dass C-18/19/20 das HAR-Gate NICHT schlagen und damit zugunsten von C-42 verworfen werden.
- **Validierungs-Gate (PILOT):** Loader-Fix (E-13) → PatchTST/TimesNet/MOMENT auf RV-Ziel; hartes Gate: OOS-R² > 0.25 UND QLIKE ≥ 5 % besser als HAR-RV (C-18/Q4-Gate), sonst ersatzloser Drop zugunsten C-42. Loader-Fix in Tagen, Modell-Bench in 1–2 Wochen.

---

### Zusammenfassung Advocate — Markt-Tendenzen

| Claim | Spot | Futures | Optionen |
|---|---|---|---|
| C-42 (LightGBM/HAR-RV) | PILOT | **ADOPT-Kandidat** | PILOT (RV-Bein) |
| Vol-Targeting (A-2, aus C-42) | stark | **am stärksten** | mittelbar |
| RV-Stop/Regime-Filter (A-3) | mittel | stark | mittel |
| C-10 (MF-DFA) / C-35 (CEEMDAN) | PILOT | PILOT | schwach |
| C-34 (GMM-Regime+VRP) | mittel | stark (G3-Gate) | **PILOT (einziger Options-Eintritt)** |
| C-33-VRP-Ernte (via A-5) | n/a | mittelbar | PILOT |
| CS-04 / C-18 / C-19 / C-20 | PARK | PILOT (nur RV-Ziel) | n/a |

**Kern-These:** Der Vol-Stack ist der einzige Cluster mit einem positiven OOS-Befund (C-42) und der einzige, dessen primärer Edge (Sizing/Stops/VRP) von der INC-05-Münzwurf-Nullhypothese überhaupt nicht berührt wird, weil er Varianz statt Vorzeichen handelt. Mein ehrlich schwächster Punkt: C-42 ist eine nicht-reproduzierte Selbstauskunft, und Vol-Targeting/VRP brauchen eine positive Basis-Strategie bzw. einen IV-Strom, die beide im Register noch nicht existieren — der Vol-Stack ist ein Verstärker und Enabler, der seinen eigenen Alpha-Untergrund noch nicht hat.

*— Ende Advocate-Part; Skeptic antwortet nachfolgend Punkt für Punkt auf A-1 … A-7.*
