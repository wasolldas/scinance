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

---

## SKEPTIC — Antwort

### Vorbemerkung — das eine Wort, das der Advocate-Rahmen verschweigt: „Untergrund"

Der Advocate gibt seine zwei Achillesfersen am Ende selbst zu (Advocate-Zusammenfassung): C-42 ist nicht-reproduziert, und Vol-Targeting/VRP brauchen eine positive Basis bzw. einen IV-Strom, die beide fehlen. Damit ist die Kern-These bereits halbiert. Mein Auftrag ist nicht, das zu wiederholen, sondern den Hebel zu zeigen, den diese zwei Geständnisse auf den GESAMTEN Cluster ausüben: **Fast jeder Edge-Kanal des Advocates ist multiplikativ oder konstitutiv von genau einem unreproduzierten Befund (C-42) abhängig.** A-2 (Vol-Targeting) multipliziert C-42 mit einer nicht existenten Basis-E[R]. A-4 (C-10/C-35) misst ΔR² GEGEN die C-42-Baseline. A-5 (VRP) baut auf C-42 als einem von zwei Beinen, dem zweiten fehlt der Datenstrom komplett. A-6 (GMM) konditioniert ein nicht existentes Signal. A-7 (DL) muss C-42 schlagen. Der Cluster ist kein Stack mit breitem Fundament — er ist ein **Fächer auf einem einzigen, nie in dieser Pipeline gemessenen Pfeiler (C-42)**, plus zwei Module mit eigener Direktevidenz, die beide NEGATIV ist (E-07/E-08 für die Stop-Reparatur in A-3). Das ist die durchgehende Linie aller folgenden Punkte.

---

### S-1 (auf A-1) — C-42 als Anker: ein einzelner, nicht reproduzierter Selbstbericht trägt keine Cluster-Architektur

- **Steelman:** Der Advocate hat recht — in einem Register mit 0 CONFIRMED, 3 REFUTED und 48 UNTESTED (alignment_matrix, Endverteilung) ist C-42 (PARTIAL, R²=0.249, Pearson=0.578, OOS) tatsächlich die methodisch sauberste positive Einzelevidenz, und er gesteht den Mangel offen ein (A-1 „Was ich zugestehe"). Das ist faire, ehrliche Advocacy.
- **Kerneinwand — Gewichtungsfrage:** Wie viel Gewicht trägt ein unreproduzierter Befund? **Im Register-eigenen Maßstab: keines, das über PILOT hinausgeht.** Die alignment_matrix stuft C-42 ausdrücklich als L1-**Selbstauskunft** ein, „NICHT in dieser Pipeline als E-xx re-validiert", „keine unabhängige Reproduktion, keine FDR-Betrachtung über die 36 Features" (alignment_matrix C-42; A-1 wiederholt es). Es gibt **kein E-xx** für C-42 — das Evidence-Register führt E-01..E-18, keines berührt C-42 (E-13 sagt sogar explizit: „PatchTST-Vol-Baseline R²=0.25 stammt separat aus research_notes (C-42), nicht aus diesem Replay"). Damit ist C-42 evidenzrechtlich auf derselben Stufe wie die 48 UNTESTED-Claims, nur mit einem freundlicheren Etikett, weil die Quelle einen Split behauptet.
- **Multiple-Testing — der ungenannte Multiplikator:** Der atr_60-Feature trägt 35.8 %, Trade-Flow-Features 38 % der Wichtigkeit (claims_register C-42), über 36 Features, **ohne jede FDR-Korrektur** (GM-2 gilt; A-1 nennt „GM-2-Geist"). Ein R²=0.249 aus einem einzigen Train/Test-Split über 36 ungekorkte Features auf EINEM Asset-Set ist genau der Befund-Typ, den GM-2 als „unkorrigierter Einzeltreffer" markiert. Der Advocate sagt selbst, es gebe „keine FDR-Betrachtung" — er behandelt diesen Mangel als Fußnote, obwohl er der Kern der Gewichtungsfrage ist.
- **Spot:** Rebuttal des PILOT-Optimismus. „RV-Persistenz ist asset-, nicht venue-spezifisch" (A-1) ist eine plausible Hypothese, aber im Register **UNTESTED** — kein E-xx misst RV-Prognose auf Spot-Klines. Der Transfer Perp→Spot ist nicht belegt, nur behauptet. PILOT vertretbar, aber nicht stärker als jeder andere UNTESTED-PILOT.
- **Futures:** Hier ist der Befund erhoben (C-42-Zielmarkt = Futures, claims_register), aber eben als Selbstauskunft. ADOPT-Kandidat ist **abzulehnen** — ADOPT verlangt laut CLAUDE.md „Evidenz + Argumente tragen"; eine nicht in dieser Pipeline reproduzierte L1-Selbstauskunft trägt ADOPT definitionsgemäß nicht (CONFIRMED ist im Register unerreichbar, GM-1). Maximal PILOT.
- **Optionen:** siehe S-5 — das RV-Bein ist hier nur so stark wie C-42 selbst, also nicht stark.
- **Härtester Einwand (1 Satz):** Der gesamte Cluster hängt an einem einzigen Befund ohne ein einziges E-xx, ohne Reproduktion und ohne FDR über 36 Features — das ist kein Anker, das ist ein Einzelnagel.
- **Reproduktions-Gate (Minimalbedingung für PILOT, NICHT ADOPT):** Das vom Advocate selbst vorgeschlagene Gate (A-1: Re-Train auf Bybit-Klines, purged-walk-forward L2, ≥2 disjunkte OOS-Fenster, OOS-R² ≥ 0.15, QLIKE schlägt naive HAR) ist **korrekt und ich übernehme es** — mit zwei Verschärfungen: (a) das Gate ist PILOT-Vorbedingung, nicht PILOT-Belohnung, d.h. C-42 zählt erst als „stützend" NACH bestandener Reproduktion; (b) FDR-Korrektur über die 36 Features ist Pflichtbestandteil des Gates, nicht optional. Solange dieses Gate offen ist, darf KEIN nachgelagerter Kanal (A-2/A-4/A-5/A-6/A-7) C-42 als „belegt" zitieren — sie alle erben den unreproduzierten Status.

### S-2 (auf A-2) — Vol-Targeting: mathematisch korrekt, aber 0 × Verstärker = 0; Reihenfolge-Fehler im PRD

- **Steelman (echt, ich würdige ihn ausdrücklich):** Vol-Targeting als **Risk-Layer** ist legitim und von INC-05 unberührt — der Sharpe-Lift bei informativem σ̂ ist tatsächlich eine mathematische Identität (Sharpe = E[R]/σ(R), Targeting senkt σ(R) ohne E[R] zu berühren), und die Richtungsneutralität ist real: kein Vorzeichen-Anspruch, also kein AUC≈0.50-Problem (INC-05). Das ist der stärkste konzeptionelle Punkt des ganzen Clusters und ich bestreite ihn NICHT. Vol-Targeting gehört als Risiko-Normalisierer ins Framework.
- **Kerneinwand — der Advocate widerlegt sich selbst:** A-2 „Was ich zugestehe": „Existiert KEINE positive Basis-Strategie (und im Register existiert bisher keine einzige gemessene positive Edge!), dann hebt Vol-Targeting Null auf Null." Das ist nicht eine Fußnote — das ist das Urteil. Die Kostenbaseline (Evidence-Register, Kernrelation) sagt: **„Friktion > Signal auf jeder gemessenen Strategie"**, Roh-Edge max ≈4–7 bps < 11 bps Friktion. Jede gemessene Basis-E[R] im Register ist NEGATIV (E-03: S2 -3.45 bps Maker-Only; E-09: S3 -16.81 bps netto). Vol-Targeting auf eine negative E[R] glättet die Verlustkurve — es macht den Verlust gleichmäßiger, nicht kleiner. Der „Lift" ist real, aber er liftet eine Zahl unter Null.
- **Reihenfolge-Frage (die eigentliche PRD-Konsequenz):** Gehört Vol-Targeting ins PRD, BEVOR eine Basis-Edge existiert? **Als Risk-Layer ja, als Edge-Kanal nein.** Die saubere Trennung: Vol-Targeting ist Querschnitts-Infrastruktur (wie C-43 Conformal Prediction, alignment_matrix: „Kein Alpha-Generator — Wirkung nur sinnvoll messbar, sobald ein L3-Basissignal existiert"). Es als eigenständigen „Edge-Kanal 1" (A-2-Framing) zu führen, ist eine Kategorienverwechslung. Im PRD gehört es in die Sizing-/Risk-Schicht mit der expliziten Vorbedingung „aktiviert erst, wenn eine Basis-Strategie netto-positiv gemessen ist" — nicht in die Edge-Liste.
- **Spot/Futures/Optionen:** identisch — die Markt-Differenzierung des Advocates (Spot „stark", Futures „am stärksten") ist irreführend, weil der Lift in ALLEN drei Märkten auf dasselbe nicht existente positive E[R] multipliziert. Futures ist nicht „am stärksten", sondern nur „am meisten von einer negativen Basis (E-09) abhängig".
- **Härtester Einwand (1 Satz):** Vol-Targeting ist ein mathematisch korrekter Verstärker, der seinen Verstärkungsgegenstand (positive E[R]) im gesamten Register nicht hat — ein Lautstärkeregler ohne Tonquelle.
- **Minimale Bedingung für PILOT:** Aufnahme als **Risk-Layer-Modul** (nicht Edge), Gate wie A-2 vorschlägt (Sharpe-Differenz ≥ +0.2 bei gleichem Brutto-E[R]), ABER mit harter Vorbedingung: eine Basis-Strategie mit gemessenem netto-positivem E[R] (das ist exakt das, worauf iter-5/E-15 für S3 noch wartet — PENDING). Ohne diese Vorbedingung: PARK, nicht PILOT, weil unbacktestbar gegen reale Edge.

### S-3 (auf A-3) — RV-Stop/Regime-Filter: adressiert einen L0-Tail aus EINEM 24h-Fenster, und die einzige Direktevidenz ist negativ

- **Steelman:** A-3 ist konzeptionell der beste Anwendungsfall, weil er an den EINZIGEN forensisch isolierten Verlusttreiber andockt (E-10: schlechteste Trades 1.7–3.0× länger gehalten, robust über 5 Symbole UND beide Richtungs-Arme — die einzige iter-3-Evidenz, die im Mirror hält). Eine vol-skalierte Stop-Kalibrierung ist die plausibelste konkrete Reparatur im Register.
- **Kerneinwand:** Die Reparatur, die A-3 vorschlägt (vol-adaptiver Stop), ist im Register **nicht gemessen**, und die ÄHNLICHSTE gemessene Reparatur ist gescheitert. E-07 zeigt: der Time-Stop, der genau die lange Halte-Dauer (E-10) absorbieren sollte, feuerte wegen Wall-Clock-Bug **1× statt 68×** — die Time-Stop-Wirkung ist NIE gemessen worden. E-08: der real gemessene Hard-Stop feuerte 13×, ließ aber 33 Trades unter -30 bps durch (friktion-unbewusst). Der Advocate gesteht das zu (A-3: „iter-5 testet nur statische friktion-bewusste Stops, noch nicht vol-adaptive"), aber die Konsequenz ist härter als er einräumt: Wir haben **null Evidenz**, dass irgendein Stop-Mechanismus die S3-Netto-Edge hebt, und die einzige laufende Messung dafür (iter-5/E-15) ist PENDING — ein Ergebnis existiert nicht.
- **L0-/Fenster-Problem:** E-10 ist L0 aus EINEM ~24h-Fenster (GM-6), und der schärfste Tail (BNB -195 bps, E-11) ist ein **Ein-Trade-Artefakt auf N=16**, in iter-4 NICHT reproduziert (E-11 Belastbarkeit: NIEDRIG). Die Tail-Signatur, an die A-3 andockt, ist robust in der Form, aber dünn in der Stichprobe. Eine RV-Prognose, die diesen Tail adressiert, hängt zudem wieder an C-42 (unreproduziert, S-1).
- **Spot:** schwach — ohne Hebel ist die Stop-Kritikalität gering (A-3 gesteht „mittel"), und Spot hat keinen E-10-Tail-Befund (E-10 ist Perp/S3).
- **Futures:** der einzige Markt mit Direktevidenz — aber diese ist NEGATIV (E-07/E-08) bzw. PENDING (E-15). „Stark" (A-3) überschätzt; korrekt ist „einziger testbarer, aber bislang gescheiterter Reparaturpfad".
- **Optionen:** spekulativ (Regime-Gate für VRP, hängt an A-5/A-6, beide UNTESTED).
- **Härtester Einwand (1 Satz):** Der Verlusttreiber ist real isoliert (E-10), aber jede bisher gemessene Reparatur ist entweder gar nicht gelaufen (E-07) oder zu locker (E-08) — A-3 verkauft eine ungemessene Hoffnung als Anwendungsfall.
- **Minimale Bedingung für PILOT:** A-3-Gate (vol-skalierter vs. statischer Stop auf S3-Population, Tail-Reduktion worst-Dezil ≥20 % bei Win-Rate-Verlust ≤5 %) ist akzeptabel, ABER **nachgelagert hinter E-15**: erst muss iter-5 zeigen, dass überhaupt ein friktion-bewusster Stop die Netto-Edge nicht-negativ macht; vol-Adaptivität ist die zweite Iteration darauf, nicht die erste. Reihenfolge: E-15 abwarten → dann A-3-Gate. Vorher PARK.

### S-4 (auf A-4) — C-10/C-35: billiges, hartes Gate — aber gemessen gegen einen unreproduzierten Nullpunkt, und C-35 mit echtem Lookahead-Risiko

- **Steelman:** Korrekt und der stärkste strukturelle Punkt von A-4 — ein **inkrementelles ΔR²-Gate** gegen eine Baseline (statt eines absoluten Direktionsanspruchs) begrenzt Overfitting strukturell und ist billig falsifizierbar (C-10: ΔR² ≥ +0.02; C-35: ΔR² ≥ +0.01 + Kausalitätsnachweis). Das ist sauberes Gate-Design.
- **Kerneinwand:** Die Baseline, gegen die ΔR² gemessen wird, ist C-42 — also der unreproduzierte Nullpunkt aus S-1. Ein ΔR² ≥ +0.02 über einem nicht reproduzierten R²=0.249 ist ein Inkrement über einer Zahl, die selbst noch nicht steht. Das Gate ist erst sinnvoll, NACHDEM das C-42-Reproduktions-Gate (S-1) bestanden ist — sonst misst man ein Delta gegen ein Phantom. Beide Claims sind **UNTESTED, „Keine Evidenz"** (alignment_matrix C-10, C-35).
- **C-35-Lookahead — vom Advocate verharmlost:** A-4 nennt es „Kausalitätsnachweis ist Pflicht, nicht Beiwerk" — richtig, aber die Schwere unterschätzt. Naive EMD/CEEMDAN ist **nicht-kausal** (claims_register C-35: „NUR streng kausale Online-Variante; naive EMD ist Lookahead-behaftet"). Ein ΔR², das aus einem Lookahead-Leak stammt, ist nicht inkrementeller Edge, sondern ein Messfehler, der wie Edge aussieht — der gefährlichste Fehlertyp im ganzen Cluster, weil er positiv aussieht. Der bit-für-bit-Kausalitätstest ist daher KILL-Gate, nicht Feature-Gate.
- **Spot/Futures:** PILOT vertretbar (asset-generisch), aber strikt nachgelagert hinter S-1.
- **Optionen:** schwach, wie A-4 selbst sagt (nur mittelbar via RV-Schätzung).
- **Härtester Einwand (1 Satz):** Hartes Inkrement-Gate gegen eine noch nicht reproduzierte Baseline, plus bei C-35 ein Lookahead-Risiko, das ein Scheinedge-ΔR² produzieren kann.
- **Minimale Bedingung für PILOT:** (a) C-42-Reproduktion (S-1) zuerst; (b) Add-one-Feature-Test mit purged-CV gegen die REPRODUZIERTE Baseline; (c) für C-35 zusätzlich bestandener bit-für-bit-Kausalitätstest als Vorab-KILL-Gate, BEVOR ΔR² überhaupt interpretiert wird. Erfüllt → PILOT; sonst DROP (ΔR² ≤ 0 ist explizit möglich, A-4 gesteht es).

### S-5 (auf A-5) — VRP/Optionen: das IV-Bein ist 100 % unbelegt, der Markt ist dünn, und es gibt KEINE einzige Kosten-Zahl

- **Steelman (Richtungsneutralität würdigen):** A-5 hat den stärksten konzeptionellen Hebel des Optionsteils — VRP = IV²−RV ist per Konstruktion **delta-gehedged richtungsneutral** (verkauft teure Vola, liefert günstigere realisierte Vola), also vollständig immun gegen INC-05; und das RV-Bein ist tatsächlich das eine Bein, das auf C-42 ruht statt auf reiner Hypothese. Als KONZEPT ist VRP der sauberste Options-Eintritt im Register.
- **Kerneinwand 1 — das IV-Bein existiert nicht, also ist A-5 = A-1 in neuem Gewand:** A-5 gesteht selbst: „Ohne IV-Strom ist das alles RV-only — also faktisch nur A-1 in neuem Gewand, bis ≥3 Monate IV aufgezeichnet sind." Das ist das ganze Urteil. C-33 und C-34 sind **UNTESTED, „Keine Evidenz"** (alignment_matrix); es gibt **kein IV-Archiv** (INC-04, claims_register C-34: „kein IV-Archiv → Aufzeichnungs-Vorlauf"). Die VRP-Strategie hat eines von zwei Beinen (RV, unreproduziert) und das zweite Bein (IV) erfordert eine komplett neue Optionsdaten-Infrastruktur mit ≥3 Monaten Vorlauf. Das ist kein PILOT, das ist ein Bau-Projekt vor dem PILOT.
- **Kerneinwand 2 — gibt es im Register IRGENDEINE Spread-/Kosten-Zahl für Bybit-Optionen? Nein.** Die Kostenbaseline (Evidence-Register) führt für Optionen genau eine Zeile: „Options-Taker-Fee (PRD-Referenz) 0.03% — **nicht gemessen**". Es gibt **keine** gemessene Bid-Ask-Spread-Zahl, keine Buchtiefe, keine Slippage für Bybit-Optionen im gesamten Register. Gleichzeitig: Liquidität fällt in **60–80 % der Stunden** durch den Check (alignment_matrix CS-09 / claims_register CS-09 „Schwächste Annahme"). Die VRP-Prämie ist laut C-33 ≥3 % auf 12-Monats-Basis (claims_register C-33) — aber auf einem Markt, wo der Spread ungemessen ist und die Quelle selbst Liquidität als „größtes Risiko" flaggt (INC-04), kann ein einziger Round-Trip-Spread die annualisierte Prämie auffressen. **Es gibt keine Zahl, die das ausschließt.** Das ist der härteste Punkt: Der Edge ist eine Differenz zweier Zahlen, von denen eine unreproduziert (RV) und eine nicht existent (IV) ist, gehandelt durch einen Spread, der nie gemessen wurde.
- **Spot:** n/a (korrekt, A-5).
- **Futures:** mittelbar (VRP-Regime als Gate) — hängt an A-6, UNTESTED.
- **Optionen:** der einzige Eintrittspunkt, aber faktisch ein **PARK**, kein PILOT: ein PILOT verlangt ein konkretes Testdesign mit vorhandenen Daten (CLAUDE.md); hier fehlt der gesamte Datenstrom (IV) UND jede Kostenkennzahl.
- **Härtester Einwand (1 Satz):** VRP handelt eine Prämie, deren eines Bein unreproduziert, deren anderes Bein nicht aufgezeichnet und deren Transaktionskosten nirgends gemessen sind — drei Unbekannte, ein behaupteter Edge.
- **Minimale Bedingung für PILOT:** strikt zweistufig. **Phase 0 (Gate vor PILOT):** ≥3 Monate ATM-markIv-Aufzeichnung UND eine gemessene Liquiditäts-/Spread-Kennzahl (ATM-Buchtiefe ≥ Ordergröße in ≥40 % der Stunden, A-5-Gate — das übernehme ich, es ist das einzige im Cluster, das die Kostenrealität adressiert). Erst NACH bestandenem Phase-0-Liquiditäts-Gate: (IV−RV) ≥ 3 % OOS in ≥2 Fenstern + VRP-Kanal-ΔR² ≥ +0.02 über RV-only. Vor Phase 0: **PARK** (Datenlücke), nicht PILOT.

### S-6 (auf A-6) — GMM-Regime-Gate: Enabler ohne zu enablendes Signal; Flatter-Risiko ungeprüft

- **Steelman:** A-6 ist klug, weil er INC-05 gegen sich selbst wendet: INC-05 nennt Regime-Konditionierung („bedingte AUC > 0.55") explizit als den EINZIGEN Rettungsweg für Direktional-Claims — und C-34 IST dieser Klassifikator. Als Enabling-Infrastruktur ist das ein realer, von INC-05 selbst legitimierter Punkt.
- **Kerneinwand — der Advocate liefert die Widerlegung mit:** A-6 „Was ich zugestehe": „C-34 ist ein Gate/Enabler, kein Alpha-Generator — sein Wert ist vollständig davon abhängig, dass es ein zu konditionierendes Basissignal gibt, das ohne Gate verliert und mit Gate gewinnt. Ein solches Signal existiert im Register noch nicht." Das ist exakt das Problem von A-2 in anderer Form: ein Multiplikator ohne Multiplikand. C-34 ist **UNTESTED, „Keine direkte Evidenz"** (alignment_matrix). Ein Regime-Gate, das nichts hat, was es freischalten/sperren könnte, ist leere Infrastruktur.
- **Flatter-Risiko — konkret und billig prüfbar, aber ungeprüft:** A-6 nennt es selbst — „ein flatternder Regime-Klassifikator wäre schlimmer als keiner (Whipsaw-Kosten)". Die kritische Annahme „GMM-Cluster persistent ≥24h ohne Flattern" (claims_register C-34 Kernannahme) ist ungeprüft. Und das Fenster, in dem man Persistenz prüfen würde, ist dasselbe ~24h-L0-Fenster (GM-6), das nur 3 Settlement-Zyklen enthält — eine 24h-Persistenz-Aussage aus einem ~24h-Fenster ist methodisch grenzwertig.
- **Spot/Futures/Optionen:** überall „mittel/stark" laut A-6, aber überall an dasselbe nicht existente Basissignal gekoppelt. Die G3-Zustandsmaschine (Carry nur Range, Kaskaden-Fade nur Stress) ist elegant — aber „Carry" und „Kaskaden-Fade" sind selbst ungetestete/REFUTED-nahe Strategien (CS-01 REFUTED, CS-03 PARTIAL/PENDING).
- **Härtester Einwand (1 Satz):** Ein Regime-Gate ist nur so wertvoll wie das Signal, das es konditioniert — und dieses Signal existiert im Register nicht, während die einzige billig prüfbare Vorbedingung (Persistenz) am 24h-Fenster scheitert.
- **Minimale Bedingung für PILOT:** Der vom Advocate vorgeschlagene **billige Vorab-Check** ist gut und ich übernehme ihn: GMM auf RV-Features fitten, Median-Regime-Persistenz ≥24h prüfen (Anti-Flatter) — ABER auf Bulk-Historie, nicht im 24h-Fenster (GM-6 macht den 24h-Test untauglich). Persistenz bestanden UND mindestens ein nachgelagertes Signal mit bedingter AUC > 0.55 in ≥1 Regime → PILOT. Persistenz allein, ohne konditioniertes Signal → PARK (Enabler ohne Enablement).

### S-7 (auf A-7) — DL-Modelle C-18/19/20: der Advocate hat den Fall selbst aufgegeben — also DROP, nicht PILOT

- **Steelman:** A-7 ist die ehrlichste Passage des ganzen Advocate-Parts. Der eine tragende Punkt: auf das **RV-Ziel** (nicht Richtung) gerichtet, müssen diese Modelle nur eine erreichbare Baseline schlagen, und der Test kostet bloß einen Loader-Fix (E-13 ist Infrastruktur-Lücke, kein negativer Outcome) — der billigste Validierungspfad im Register. C-20 (MOMENT Zero-Shot) hat zudem einen echten Nischenwert: Vol-Prognose auf neu gelistete Altcoins ohne Trainingshistorie (claims_register C-20).
- **Kerneinwand — der Advocate gesteht die Niederlage explizit:** A-7 „Was ich zugestehe": „Realistisch erwarte ich, dass C-18/19/20 das HAR-Gate NICHT schlagen und damit zugunsten von C-42 verworfen werden." Das ist kein Zugeständnis, das ist eine **Prognose der eigenen Widerlegung**. Wenn der Advocate selbst erwartet, dass das harte Gate (OOS-R² > 0.25 UND QLIKE ≥5 % besser als HAR) nicht bestanden wird, dann ist die korrekte Konsequenz DROP, nicht PILOT — das Framework verlangt Falsifizierbarkeit (CLAUDE.md), und ein Ansatz, dessen eigener Verteidiger das Scheitern erwartet, hat seine Beweislast bereits verloren. Status: C-18 PARTIAL nur **geliehen** über C-42 (alignment_matrix: „PARTIAL nur via Schwester-Baseline"); C-19/C-20 UNTESTED; alle SUSPECT (CS-04 nie gelaufen, E-13).
- **HAR-Baseline-Vergleich fehlt vollständig:** Es gibt im Register **keinen einzigen** Befund, dass ein 110M-Parameter-Transformer eine simple HAR/LightGBM-Baseline beim RV-R² schlägt — A-7 räumt ein, die DL-Vol-Literatur zeige oft das Gegenteil. Ohne HAR-Vergleichswert ist der gesamte DL-Mehrwert reine Spekulation gegen einen Befund (C-42), der wiederum unreproduziert ist (S-1). Doppelt unbelegt.
- **CS-04 (Ensemble):** E-13 (0 Trades, insufficient_models 96–99.99 %) ist Loader-Lücke, kein Outcome — korrekt. Aber „billigster Pfad" heißt nur „billig zu MESSEN", nicht „wahrscheinlich positiv". Der Loader-Fix macht S4 messbar; was er misst, erwartet der Advocate selbst negativ.
- **Spot:** PARK/schwach — DL-Overkill, wo C-42 (wenn reproduziert) bereits R²=0.249 liefert. Korrekt.
- **Futures:** als Direktional-Ensemble **DROP** (INC-05, unstrittig — A-7 stimmt zu). Auf RV-Ziel: bestenfalls ein billig zu schließendes Negativ-Experiment, kein PILOT-Kandidat.
- **Optionen:** n/a.
- **Härtester Einwand (1 Satz):** Wenn der Advocate selbst erwartet, dass die DL-Modelle das HAR-Gate nicht schlagen, und kein einziger HAR-Vergleich im Register existiert, ist der ehrliche Schluss DROP zugunsten C-42 — nicht ein PILOT, der nur die erwartete Niederlage formalisiert.
- **Minimale Bedingung für PILOT (eng, sonst DROP):** Ich akzeptiere PILOT NUR für **C-20/MOMENT im spezifischen Nischenfall** (Zero-Shot-RV auf neu gelistete Symbole ohne Lookback, wo HAR/LightGBM mangels Historie strukturell NICHT antreten können — dort gibt es keine HAR-Baseline, also ist der Vergleich nicht verloren, sondern n/a). Für C-18/C-19 und das RV-Ensemble auf etablierten Symbolen: **DROP** — der Loader-Fix darf als billiges Einmal-Negativexperiment laufen (E-13), aber das Ergebnis gehört in den REFUTED-Abschnitt, nicht in einen PILOT-Pfad, weil das harte HAR-Gate (C-18/Q4) nach Selbsteinschätzung des Advocates nicht bestanden wird.

---

### Skeptic — Markt-Urteile (Antwort auf die Advocate-Tabelle)

| Claim | Spot | Futures | Optionen | Skeptic-Kern |
|---|---|---|---|---|
| C-42 (LightGBM/HAR-RV) | PILOT* | **PILOT** (nicht ADOPT) | PARK | unreproduzierte L1-Selbstauskunft, kein E-xx, keine FDR (S-1) |
| Vol-Targeting (A-2) | Risk-Layer, PARK* | Risk-Layer, PARK* | n/a | 0 × Verstärker = 0; gehört in Risk-Schicht, nicht Edge-Liste (S-2) |
| RV-Stop/Regime (A-3) | DROP/PARK | PARK (hinter E-15) | spekulativ | einzige Direktevidenz negativ (E-07/E-08), Reparatur ungemessen (S-3) |
| C-10 / C-35 | PILOT* | PILOT* | schwach | ΔR² gegen Phantom-Baseline; C-35-Lookahead = KILL-Gate (S-4) |
| C-34 (GMM-Regime) | PARK | PARK | PARK | Enabler ohne Enablement; Flatter ungeprüft (S-6) |
| C-33-VRP (A-5) | n/a | mittelbar/PARK | **PARK** (Phase-0 zuerst) | IV-Bein fehlt, 0 Kosten-Zahl, 60–80 % illiquide (S-5) |
| C-18/C-19 + Ensemble | PARK | **DROP** | n/a | Advocate erwartet selbst HAR-Gate-Niederlage (S-7) |
| C-20 (MOMENT Nische) | DROP | **PILOT (nur Zero-Shot-Neulisting)** | n/a | einziger Fall ohne verlorenen HAR-Vergleich (S-7) |

\* PILOT/PARK jeweils strikt **nachgelagert hinter dem C-42-Reproduktions-Gate (S-1)** — solange C-42 nicht in dieser Pipeline reproduziert ist (purged-WF L2, ≥2 OOS-Fenster, FDR über 36 Features), erben alle abgeleiteten Kanäle (A-2/A-4/A-5/A-6/A-7) den unreproduzierten Status und dürfen C-42 nicht als „belegt" zitieren.

**Skeptic-Kern-These:** Der Vol-Stack ist kein Stack mit Fundament, sondern ein Fächer auf einem einzigen, nie in dieser Pipeline gemessenen Pfeiler (C-42). Die echten, zu würdigenden Punkte — Vol-Targeting als Risk-Layer und die Richtungsneutralität von VRP — sind real, aber beide Multiplikatoren ohne Multiplikand: sie verstärken/konditionieren ein positives Basissignal, das im gesamten Register (0 CONFIRMED, jede gemessene Roh-Edge < Friktion) nicht existiert. Die korrekte Reihenfolge ist nicht „Stack bauen", sondern: erst C-42 reproduzieren (S-1-Gate), erst eine netto-positive Basis messen (E-15-PENDING), dann Verstärker/Enabler/VRP — nicht umgekehrt.

*— Ende Skeptic-Part.*
