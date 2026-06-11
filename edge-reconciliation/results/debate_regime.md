# Debatte: Regime-Detektion / Komplexität

**Cluster:** regime — Regime-/Strukturbruch-Detektion und Komplexitätsmaße als Filter/Enabler
**Cluster-Claims:** C-08 (BOCPD), C-11 (TDA/Persistent Homology), C-12 (RQA), C-16 (TFSAX+Smith-Waterman), C-31 (Cyclostationary Cyclic Spectrum + CFAR), CS-07 (Footprint-Detektor).
**Querschnitt (mitgeführt):** C-43 (Conformal Prediction als Kalibrierungs-/Sizing-Layer).
**Phase:** 4 — DEBATE. **Stand:** 2026-06-11.

> **Rahmen des Advocate (verbindlich):** Regime-Detektion ist *kein eigenständiger Edge*, sondern ein **Filter/Enabler**. Mein Auftrag ist NICHT zu behaupten, BOCPD/PH/RQA/CFAR „verdienen Geld", sondern zu zeigen, WELCHE *nachgelagerte Entscheidung* (Positionsgröße, Strategie-Schalter, Risiko-Cap, Exit-Timing) durch Regime-Wissen **messbar** besser wird — und das je Markt falsifizierbar zu machen. Jeder Punkt, der diesen Test nicht besteht, gehört verworfen, nicht verteidigt. Ich vermeide explizit das „schöne Mathematik ohne Edge"-Muster, das C-14/CS-01 via E-01 gekillt hat (importierter theoretischer Schwellwert ρ>0.85, empirisch 6 Größenordnungen unerreichbar).

---

## Advocate

### Vorbemerkung — die Beweislast, die ich akzeptiere

Alle sechs Cluster-Claims sind in der Alignment-Matrix **UNTESTED** (C-08 zusätzlich SUSPECT/No-Op via E-12; C-16 SUSPECT in CS-04 via E-13; C-11/C-12/C-31/C-43 ohne jedes E-xx). Ich kann also **keinen** positiven Outcome-Befund zitieren. Mein Argument steht und fällt mit zwei Dingen: (a) einem **mechanistischen** Grund, warum Regime-Konditionierung die nachgelagerte Entscheidung verbessern *muss*, und (b) einem **billigen, harten Falsifizierungspfad**, der die S1-Falle (unerreichbarer Schwellwert) vorab ausschließt. Wo ich das nicht liefern kann, sage ich es (siehe „Was ich zugestehe").

**Der eine empirische Anker, den ich habe:** C-42 (PARTIAL, Test-R²=0.249, Pearson=0.578, OOS Apr-2026). Das ist der einzige dokumentierte deployable-Befund im gesamten Register — und er ist ein **Vol-Prognose**-Signal, dessen erklärter Nutzen *exakt* der Enabler-Use-Case ist: „Risk Gauge, Position Sizing, Stop-Loss-Kalibrierung. NICHT als Richtungssignal." C-42 ist damit die **Existenzbeweis-Vorlage** für meine gesamte These: ein nicht-direktionales Komplexitäts-/Vol-Signal, das eine nachgelagerte Sizing-Entscheidung trägt, hat als einziges im Register einen OOS-Wert über der Münzwurf-Linie geliefert.

**Der zweite Anker (mechanistisch):** INC-05. Unkonditionale Richtungsprognose = AUC ≈ 0.50 (Münzwurf) auf 1h/4h mit klassischen Features. PRD-fable5/PRD-kestrel übernehmen das explizit als Nullhypothese und lassen Direktional-Claims *nur* regime-konditioniert zu (bedingte AUC > 0.55). Das ist keine Mode — es ist die direkte Konsequenz daraus, dass das *unbedingte* Problem nachweislich kein Signal trägt. **Wenn überhaupt irgendwo Edge ist, dann konditional.** Damit ist Regime-Detektion nicht Beiwerk, sondern die *notwendige Bedingung* dafür, dass irgendein nachgelagertes Signal über die Münzwurf-Linie kommt.

---

### A-1 — BOCPD (C-08) als Risk-Cap-Schalter, nicht als Signalgeber — Futures

**Tendenz: PILOT (Futures), DROP-Kandidat (Spot), N/A (Optionen).**

C-08 ist in CS-03 als No-Op verbaut (E-12: kein Changepoint im ~24h-Fenster) und damit **dekorativ getestet, nicht widerlegt** — GM-6: das Fenster enthielt keinen garantierten Regime-Bruch, also kann das Nicht-Feuern den Detektor weder bestätigen noch falsifizieren. Das ist genau der Punkt, an dem ich NICHT die S1-Falle wiederhole: ich behaupte nicht, BOCPD „funktioniert trotzdem". Ich behaupte: **die einzige relevante nachgelagerte Entscheidung von C-08 ist ein binärer Risk-Cap-/De-Aktivierungs-Schalter** — „Regime gebrochen → Modelle deaktivieren und neu fitten / Positionsgröße auf 0" (PRD-v1-Kernidee, PRD-kestrel-Gate G2: DD-Reduktion ≥ 20 % bei Sharpe-Verlust ≤ 10 %).

- **Futures:** Der nachgelagerte Mehrwert ist **Drawdown-Vermeidung**, nicht Alpha. Die mechanistische Begründung liefert E-10: Die schlechtesten S3-Trades wurden 1.7–3.0× länger gehalten (robust über 5 Symbole UND beide Richtungs-Arme) — Verluste sind in dieser Pipeline nachweislich **dauer-/regime-getrieben**, nicht entry-getrieben. Ein Strukturbruch-Detektor, der genau solche Regime-Wechsel früh flaggt und die Halte-/Sizing-Entscheidung kappt, greift an der einzigen empirisch belegten Verlustquelle an.
- **Spot:** schwächer — Spot hat kein Funding/OI-Regime mit hartem Bruch-Charakter; BOCPD auf RV-Spot wäre redundant zur Vol-Baseline C-42. Tendenz DROP, außer als billiges Add-on.
- **Optionen:** N/A in dieser Form (Bruch-Detektion auf IV gehört thematisch zu C-11/C-34, nicht hierher).

**Falsifizierungs-Gate (das die S1-Falle ausschließt):** *Zuerst* ein reiner **Detektions-/Erreichbarkeits-Check** analog E-01 — feuert BOCPD auf einem Bulk-Fenster mit *bekannten* historischen Brüchen (z.B. der Carry-Kompressions-Übergang 2024, oder ein dokumentierter Liquidations-Kaskadentag) überhaupt, und mit welcher Latenz? **Wenn der Detektor auf bekannten Brüchen nicht feuert, ist er wie C-14 gestorben — bevor ein Cent Strategie-Aufwand fließt.** Erst danach das Outcome-Gate: G2-gated DD-Reduktion ≥ 20 % bei Sharpe-Verlust ≤ 10 % gegen identische ungate-te Strategie, walk-forward über ≥ 2 disjunkte Fenster.

**Stärkstes Einzelargument:** Die einzige in dieser Pipeline *isolierte* Verlustsignatur (E-10: Tail = lange Trades, cross-symbol + cross-arm robust) ist exakt das, was ein Strukturbruch-Schalter adressiert — das ist kein theoretischer, sondern ein datengestützter Angriffspunkt.

---

### A-2 — Komplexitätsmaße (C-12 RQA, C-11 PH) als Vol-/Tail-Stack-Feature, kalibriert gegen die C-42-Baseline — Futures

**Tendenz: PILOT (Futures, nur als Feature mit ΔR²-Gate), DROP (Spot solo), PARK (Optionen, IV-Surface-Variante).**

C-11 und C-12 sind beide UNTESTED ohne jedes E-xx. Ihr direktionaler Anspruch (RQA: DET>0.7 → Breakout-Hit ≥ 55 %; PH: ρ(L¹→Forward-DD) ≥ 0.4) steht unter dem INC-05-Revisionsdruck und ist die schwache Form. **Die starke Form ist nicht-direktional:** beide sind Regime-/Tail-Indikatoren, deren nachgelagerte Entscheidung **Positionsgröße und Risk-Off-Cap** ist.

- **Futures:** Der entscheidende Punkt ist, dass C-42 (R²=0.249) bereits eine **harte Mess-Latte** für genau diesen Use-Case setzt. Damit ist die Frage für C-11/C-12 NICHT „ist da Edge?", sondern die *billig und sauber falsifizierbare* Frage: **liefert RQA-DET/-LAM bzw. PH-L¹-Norm ein ΔR² ≥ +0.02 über die C-42-Baseline hinaus** (für RV-Prognose) bzw. einen **Tail-AUC > 0.60** für „RV-Spike/DD in 24h"? Das ist exakt das Gate-Schema, das PRD-kestrel für den Vol-Stack (C-34/C-35) etabliert hat — inkrementeller Beitrag *über* eine etablierte Baseline, nicht Stand-alone-Magie. Ein Feature, das das C-42-Modell messbar verbessert, hat per Konstruktion einen nachgelagerten Nutzen (besseres Vol-Targeting → besseres Sizing → besseres Stop-Niveau), unabhängig davon, ob es je ein Richtungssignal ist.
- **Spot:** DROP solo — ohne Funding/OI/Liquidations-Mikrostruktur reduziert sich der Informationsgehalt auf reine Preis-RQA, die gegen HAR-RV kaum ΔR² liefern dürfte. Allenfalls als Multi-Asset-PH-Panel-Input.
- **Optionen:** Die PH-IV-Surface-Variante (C-11/M-S17) ist mechanistisch die *interessanteste* Anwendung — topologische Brüche der IV-Fläche als Tail-Frühwarnung — aber an die fehlende IV-Aufzeichnung gebunden (INC-04). PARK bis IV-Archiv existiert.

**Falsifizierungs-Gate:** ΔR² ≥ +0.02 über C-42 (RV-Prognose) ODER Tail-AUC > 0.60 (24h-DD), walk-forward ≥ 2 Fenster, FDR-korrigiert über die getesteten Komplexitäts-Features (GM-2!). Abbruch bei ΔR² ≤ 0 — kein zweiter Versuch.

**Stärkstes Einzelargument:** Es existiert bereits eine quantitative Baseline (C-42), gegen die der Mehrwert von C-11/C-12 in Wochen, nicht Monaten, *inkrementell* messbar ist — das ist der Anti-S1-Pfad schlechthin: keine importierte Schwelle, sondern ein gemessenes ΔR² gegen ein laufendes Modell.

---

### A-3 — Cyclostationary CFAR (C-31) als Mikrostruktur-Regime-Detektor mit eingebauter Falschalarm-Kontrolle — Futures

**Tendenz: PILOT mit scharfem Vorbehalt (Futures), DROP (Spot), N/A (Optionen).**

C-31 ist UNTESTED. Sein Alleinstellungsmerkmal gegenüber dem gesamten Rest des Clusters: **CFAR (Constant False Alarm Rate) hat die Falschalarm-Kontrolle im Mechanismus eingebaut.** Das adressiert direkt GM-2 (Multiple-Testing, in *keiner* Quelle korrigiert) und INC-03 (S3-Q90-Threshold übertriggert: 50–60 Trades/24h statt 3 Settlements). Ein Detektor, der seine Trigger-Rate per Konstruktion an eine kontrollierte Falschalarmrate bindet, ist *strukturell* gegen das Über-Trigger-Problem immun, das S3 plagte.

- **Futures:** Der nachgelagerte Use-Case ist **Strategie-Schalter** — algorithmischen Footprint (TWAP/Iceberg-Bots) als Regime-Marker nutzen, in dem nachgelagerte Mikrostruktur-Signale (OFI, C-16) überhaupt erst eingeschaltet werden. Das ist die CS-07-Architektur (C-16 ∥ C-31 → Konsens-Filter → C-43-Sizing). Der Witz: C-31 (Frequenzdomäne) und C-16 (Sequenzdomäne) sind *orthogonal* — ein Konsens-Gate aus zwei mathematisch unabhängigen Detektoren reduziert die effektive Falsch-Positiv-Rate multiplikativ, ohne dass beide denselben Fehler teilen (anders als der korrelierte ω_s-Fehler in CS-06).
- **Spot/Optionen:** DROP/N/A — algorithmischer Ausführungs-Footprint ist ein Perp-Phänomen mit hoher Bot-Dichte; Spot-Footprint ist dünner, Optionen irrelevant.

**Falsifizierungs-Gate (das die Fee-Falle ausschließt):** Die Quelle flaggt selbst die gelbe Flagge — Sekunden-Horizont evtl. unter der Fee-Schwelle (Kostenbaseline: 11 bps Round-Trip > jede bisher gemessene Roh-Edge). Daher zweistufig: (1) **Surrogate-Test** (geshuffelte Inter-Arrivals, p ≤ 0.05 in ≥ 2 Fenstern) — gibt es das periodische Muster real oder ist es Rauschen? (2) **Handelbarkeits-Gate:** detektierte Lead-Zeit > 50 ms Retail-Latenz UND realisierter Edge-Horizont trägt > 11 bps. **Wenn die Lead-Zeit < 50 ms oder der Edge < Fee — sofortiger Drop, kein Strategie-Bau.** Das ist die direkte Lehre aus C-14: Erreichbarkeit/Handelbarkeit *zuerst*, Strategie *danach*.

**Stärkstes Einzelargument:** C-31 ist der einzige Detektor im Cluster mit *eingebauter* Falschalarm-Kontrolle (CFAR) — er löst das Über-Trigger-Problem (INC-03), an dem S3 strukturell krankte, auf Mechanismus-Ebene statt per nachträglicher Schwellen-Bastelei.

---

### A-4 — TFSAX + Smith-Waterman (C-16) als Präzedenz-Regime-Klassifikator mit hartem Selbst-Gate — Futures

**Tendenz: PILOT (Futures, hartes OOS-AUC-Gate), DROP (Spot/Optionen).**

C-16 ist UNTESTED/SUSPECT (in CS-04 verbaut, die nie lief — E-13, reiner Loader-Defekt, *keine* inhaltliche Widerlegung). Wichtig für die Beweislast: **CS-04 ist eine Mess-Lücke, keine Niederlage** (E-13: „mehr Daten helfen nicht", reine Verdrahtung). C-16 wurde also nie inhaltlich getestet — sein hartes Selbst-Gate (PRD-kestrel: OOS-AUC > 0.55, *sonst ersatzloser Drop*) ist nie ausgewertet worden.

- **Futures:** Der nachgelagerte Use-Case ist **Strategie-Schalter via Präzedenz-Match**: aktuelle Marktsequenz gegen historische Bibliothek aligned → wenn ein hochsignifikanter Match existiert, ist das ein Regime-Label, das ein nachgelagertes Signal (oder dessen Sizing) konditioniert. Die M-S23-Variante (symbolisierter *Orderflow* statt Preis) ist die stärkere — Orderflow-Sequenzen sind mikrostrukturell informativer und weniger durch Regime-Drift kontaminiert als Preis-SAX. Smith-Waterman toleriert per Konstruktion zeitliche Verzerrungen (Insertions/Deletions) — das ist genau die Robustheit gegen Tempo-Variation, die ein starrer Schwellwert-Detektor (C-14) nicht hat.
- **Spot/Optionen:** DROP — Präzedenz-Bibliotheken brauchen mikrostrukturell reiche, hochfrequente Sequenzen; Spot-Tape ist dünner, Optionen ungeeignet.

**Falsifizierungs-Gate:** Das härteste im Cluster und das mag ich daran — die Quelle gibt es selbst vor: **OOS-AUC > 0.55 (PRD-kestrel) bzw. Balanced Accuracy ≥ 0.55 + Surrogate-Test p < 0.05 (M-S23)**, sonst **ersatzloser Drop**. Kein Nachverhandeln. Das ist ein PRD, das sein eigenes Abbruchkriterium scharf gestellt hat — vorbildlich gegen das S1-Muster.

**Stärkstes Einzelargument:** C-16 bringt sein eigenes hartes Drop-Gate mit (OOS-AUC > 0.55 sonst raus) — ein Ansatz, der bereit ist, sich selbst zu falsifizieren, ist genau das Gegenteil der „schönen Mathematik ohne Abbruchkriterium" von C-14.

---

### A-5 — Conformal Prediction (C-43) als Querschnitts-Sizing-Kalibrator — alle Märkte

**Tendenz: PILOT als Querschnitts-Layer (Futures zuerst), nachgelagert auf jeden L3-Stack.**

C-43 ist UNTESTED und — das gestehe ich vorweg — **kein Alpha-Generator**; seine Wirkung ist erst messbar, sobald *ein* L3-Basissignal existiert (Alignment-Matrix C-43). Genau deshalb gehört er als *Kalibrierungs-Layer* in dieses Cluster: er ist die formale Brücke zwischen „Regime erkannt" und „Positionsgröße gewählt".

- **Mechanismus (markt-übergreifend):** Conformal Prediction liefert ein *verteilungsfreies* Konfidenzband um jedes nachgelagerte Signal → **Sizing nur bei engem Intervall, Veto bei breitem Intervall.** Das ist die mathematisch sauberste Umsetzung der Enabler-These: das Regime-/Unsicherheits-Wissen wird direkt in die *Positionsgröße* (die nachgelagerte Entscheidung) übersetzt, mit einer prüfbaren Garantie (90 %-Intervall deckt ≥ 85 % der OOS-Fälle).
- **Warum das die S2-Falle adressiert:** S2 verlor, weil Friktion (11 bps) die Richtung ~35× dominierte (E-16) und das Signal ein Münzwurf war (E-04, hit_sum 0.179). Ein CP-Layer, der bei breitem Intervall *nicht handelt*, hätte genau die Münzwurf-Trades unterdrückt, die unter der Fee-Schwelle Geld verbrannten. CP ist damit der natürliche **Friktions-Filter**: nur Trades mit ausreichend enger Konfidenz, dass der erwartete Edge > 11 bps liegt, werden überhaupt gefeuert.
- **Spot:** voll anwendbar (niedrigere Friktion → Schwelle leichter zu schlagen). **Optionen:** anwendbar auf VRP-Sizing (C-33), aber an Liquidität (INC-04) gebunden.

**Falsifizierungs-Gate:** Coverage ≥ 85 % OOS (CP-Gate) — das ist eine *direkt prüfbare* Kalibrierungs-Eigenschaft, unabhängig vom Basissignal, sobald eines existiert. Zweitens: gated Sharpe/PF muss über dem un-kalibrierten Basissignal liegen (sonst ist CP nur Reibungsverlust).

**Stärkstes Einzelargument:** CP übersetzt Unsicherheit *garantiert und prüfbar* in Positionsgröße — und hätte als Friktions-Filter (nur handeln, wenn Konfidenz > Fee-Schwelle) exakt das S2-Verlustmuster (E-16: Friktion ≫ Signal) unterdrückt.

---

### A-6 — Der Cluster-Synthese-Punkt: Regime ist die notwendige Bedingung, nicht das Nice-to-have

**Tendenz: Das Cluster gehört als L3-Gate-/L5-Sizing-Schicht ins Framework, NICHT als Alpha-Quelle.**

Die übergreifende Verteidigung, unabhängig vom Einzelmodul: Die gesamte Evidenzlage sagt zwei Dinge gleichzeitig. (1) *Unkonditional* ist kein Richtungs-Edge da (INC-05, AUC ≈ 0.50). (2) Das einzige, was OOS über die Münzwurf-Linie kam, war ein nicht-direktionales *Vol-/Regime*-Signal (C-42, R²=0.249), dessen Nutzen ausdrücklich Sizing/Stops ist. **Beide Befunde zusammen sind das Argument für dieses Cluster:** Wenn Edge nur konditional existiert, dann ist der Mechanismus, der die Konditionierung liefert — Regime-/Strukturbruch-/Komplexitäts-Detektion — die *notwendige Vorbedingung* für jeden nachgelagerten Edge, nicht ein dekoratives Extra.

Die nachgelagerten Entscheidungen, die dieses Cluster messbar verbessern soll, sind präzise benennbar und je einzeln falsifizierbar:
- **Positionsgröße** (C-43-CP-Intervall, C-42/C-11/C-12-Vol-Targeting) — Gate: gated Sharpe > un-gated.
- **Strategie-Schalter** (C-08-Bruch → de-aktivieren; C-16/C-31-Regime-Label → Mikrostruktur-Signale freischalten) — Gate: DD-Reduktion ≥ 20 % bei Sharpe-Verlust ≤ 10 %.
- **Risiko-Cap / Exit-Timing** (C-08/C-11 Tail-Frühwarnung → Risk-Off) — Gate: Tail-AUC > 0.60, motiviert durch die einzige isolierte Verlustsignatur E-10.

---

## Zusammenfassung Advocate (1 Zeile je Ansatz, Tendenz je Markt)

| Claim | Spot | Futures | Optionen |
|---|---|---|---|
| C-08 BOCPD (Risk-Cap-Schalter) | DROP | **PILOT** (DD-Gate, +Erreichbarkeits-Check zuerst) | N/A |
| C-11 PH / TDA (Tail-Feature) | DROP | **PILOT** (ΔR²/Tail-AUC gg. C-42) | PARK (IV-Archiv fehlt, INC-04) |
| C-12 RQA (Vol-Stack-Feature) | DROP | **PILOT** (ΔR² ≥ +0.02 gg. C-42) | N/A |
| C-16 TFSAX+SW (Präzedenz-Label) | DROP | **PILOT** (hartes OOS-AUC>0.55-Selbst-Gate) | DROP |
| C-31 CFAR (Footprint-Regime) | DROP | **PILOT** (Surrogate + >50ms + >11bps) | N/A |
| CS-07 (C-16 ∥ C-31 → CP) | DROP | **PILOT** (orthogonaler Konsens-Filter) | N/A |
| C-43 Conformal Prediction | PILOT | **PILOT** (Querschnitts-Sizing, Coverage≥85%) | PILOT (an Liquidität gebunden) |

---

## Was ich zugestehe — die ehrlich schwächsten Stellen

1. **Null Outcome-Evidenz im gesamten Cluster.** Kein einziger der sechs Claims hat ein E-xx, das einen *Outcome* misst. Meine gesamte positive Argumentation hängt an *einem* fremden, nicht in dieser Pipeline re-validierten Befund (C-42, L1-Selbstauskunft aus research_notes) plus einem mechanistischen Negativ-Argument (INC-05). Das ist dünn, und der Skeptic darf darauf bestehen.

2. **Das Enabler-Argument ist potenziell unfalsifizierbar-bequem.** „Regime-Detektion macht das nachgelagerte Signal besser" lässt sich immer behaupten, solange das nachgelagerte Signal selbst nie existiert. C-43 ist hier am verletzlichsten: er kann *erst* getestet werden, wenn ein L3-Basissignal da ist — und *kein* L3-Basissignal in diesem Register hat je die Münzwurf-Linie überschritten (außer dem Vol-Signal C-42, das selbst kein Direktionssignal ist). Das Cluster könnte ein perfekter Filter für ein nicht-existentes Signal sein.

3. **GM-6 trifft mich härter als jeden anderen Cluster.** Regime-/Strukturbruch-Detektion ist *per Definition* nur an Regime-Brüchen testbar — und das ~24h-Replay-Fenster enthält per GM-6 keine garantierte Stress-/Kaskaden-Episode. Genau wie C-08 in S3 (E-12: kein Changepoint) wird *jeder* Detektor in diesem Cluster im vorhandenen Fenster nicht-feuern, ohne dass das etwas beweist. Die Validierung braucht zwingend Bulk-Historie mit dokumentierten Bruch-Episoden — das ist Wochen bis Monate Aufzeichnungs-/Download-Vorlauf, nicht „nächste Iteration".

4. **C-31s Fee-Risiko ist real, nicht hypothetisch.** Die Quelle flaggt selbst, dass der Sekunden-Horizont unter der 11-bps-Fee-Schwelle liegen könnte. Die Kernrelation des Evidence-Registers (Friktion > jede gemessene Roh-Edge) ist die empirisch *bestbelegte* Aussage im ganzen Projekt — und sie steht gegen C-31. Ich halte C-31 für PILOT-würdig *nur* wegen des CFAR-Mechanismus und nur mit dem harten >11-bps-Handelbarkeits-Gate vorgeschaltet; ohne das wäre es DROP.

5. **Die schwächste Einzelannahme (geteilt mit CS-06/C-30): unkalibrierte theoretische Schwellen.** Mehrere Komplexitätsmaße tragen importierte „universelle" Schwellwerte (RQA DET>0.7, PH z=3, analog κ₁≈0.070). Das ist *strukturell dieselbe Annahme*, die C-14 via E-01 gefällt hat. Mein Erreichbarkeits-Check-Gate (Distributions-Check zuerst) ist die Gegenmaßnahme — aber bis er gelaufen ist, teilt dieses Cluster das S1-Risiko vollständig.

---

## SKEPTIC — Antwort

> **Vorbemerkung des Skeptic (verbindlich):** Ich würdige zwei Dinge vorab uneingeschränkt, weil sie methodisch tragen. (a) **E-10 ist die sauberste isolierte Verlustquelle im ganzen Register** — die Tail-Signatur (worst-Trades 1.7–3.0× länger gehalten) ist cross-symbol UND cross-arm robust (Belastbarkeit MITTEL-HOCH, die einzige iter-3-Evidenz, die in beiden Richtungs-Armen hält). Der Advocate baut hier auf dem Festesten, was es gibt. (b) **„Anti-S1" — inkrementelle ΔR²-Gates statt importierter Schwellen (A-2) — ist ein echter methodischer Fortschritt.** Genau diese Importschwellen-Annahme hat C-14 via E-01 gekillt (ρ-Median 2e-7, 6 Größenordnungen unter 0.85); ein gemessenes ΔR² gegen ein laufendes Modell ist die richtige Lehre daraus. Beides bleibt nach meiner Kritik stehen.
>
> **Mein Generaleinwand (gilt unter allem):** Die gesamte positive Argumentation des Clusters hängt an **null Outcome-Evidenz** (Advocate-Zugeständnis #1, Alignment: alle sechs Claims UNTESTED, kein E-xx misst einen Outcome) plus *einem* nicht-reproduzierten Fremdbefund (C-42, in der Matrix als **L1-Selbstauskunft aus research_notes** geführt, „NICHT in dieser Pipeline re-validiert"). Das ist keine Basis für sechs PILOTs — es ist eine Basis für **eine Reproduktion und einen Erreichbarkeits-Check**, danach für Reihenfolge.

---

### A-1 — C-08 BOCPD als Risk-Cap-Schalter (Futures)

- **Steelman:** Der nachgelagerte Use-Case ist sauber benannt (binärer Risk-Cap, kein Alpha), und er zielt auf **E-10** — die einzige isoliert belegte Verlustsignatur. Der vorgeschaltete Erreichbarkeits-Check (analog E-01) ist intellektuell ehrlich: er akzeptiert vorab das Risiko, an dem C-14 starb.
- **Spot:** Zustimmung zu DROP. BOCPD auf RV-Spot ist redundant zur Vol-Baseline (C-42); kein eigener Mechanismus.
- **Futures — Härtester Einwand (Ockham):** **E-10 motiviert einen Time-Stop, keinen bayesianischen Changepoint-Detektor.** Die Tail-Signatur ist „lange Trades verlieren" — das adressiert iter-5 (E-15) bereits mit zwei trivialen Parametern: Time-Stop auf Tick-Zeit (`now = ts_ms/1000.0`) + friction-aware Hard-Stop. Wenn `if elapsed > 120s: exit` denselben Tail schneidet wie BOCPD, trägt der Detektor **null inkrementelle Erklärung** für E-10. C-08 muss seinen Mehrwert *gegen die iter-5-Baseline* zeigen, nicht gegen die ungate-te Strategie. Hinzu kommt: C-08 ist in CS-03 ein dokumentierter **No-Op** (E-12: kein Changepoint im Fenster, n_pressure_extreme==n_basis_aligned) — d.h. der Detektor hat in der einzigen Pipeline, in der er lief, *nichts beigetragen*. Das ist kein Beweis gegen ihn (GM-6), aber es verschiebt die Beweislast: er muss zeigen, dass er *überhaupt feuert*, bevor er einen Risk-Cap rechtfertigt.
- **Optionen:** N/A — unstrittig.
- **Falsifikations-Gate-Test (eigenständig, nicht basis-abhängig?):** Der Erreichbarkeits-Check (feuert BOCPD auf einem Bulk-Fenster mit *bekannten* historischen Brüchen?) ist tatsächlich basis-unabhängig. Das ist das eigenständigste Falsifikations-Gate im Cluster. **Aber:** es braucht Bulk-Historie mit dokumentierten Bruch-Episoden (GM-6, siehe unten) — Wochen bis Monate Vorlauf.
- **Minimale Bedingung für PILOT:** Reihenfolge erzwingen — (1) iter-5 (E-15) abwarten; schneidet der triviale Time-Stop den E-10-Tail bereits ausreichend, ist C-08 für diesen Zweck **DROP** (Ockham). (2) Nur falls iter-5 zeigt, dass der Restbtail *regime-getrieben statt dauer-getrieben* ist, geht C-08 in einen reinen Erreichbarkeits-Check (feuert auf bekannten Brüchen, Latenz messbar) — und *erst danach* in ein Outcome-Gate (DD-Reduktion ≥20% bei Sharpe-Verlust ≤10% gegen die iter-5-Baseline, nicht gegen die ungate-te Strategie). Bis dahin: **PARK, nicht PILOT.**

---

### A-2 — C-11/C-12 als Vol-/Tail-Feature gegen die C-42-Baseline (Futures)

- **Steelman:** Das ΔR²-Gate gegen eine laufende Baseline ist der Anti-S1-Pfad schlechthin — keine importierte Schwelle, sondern ein gemessenes Inkrement. Methodisch ist das der stärkste Punkt des gesamten Advocate-Parts, und ich würdige ihn ausdrücklich.
- **Spot:** Zustimmung zu DROP solo.
- **Optionen:** Zustimmung zu PARK (INC-04, kein IV-Archiv).
- **Futures — Härtester Einwand:** **Das ΔR²-Gate misst gegen eine Baseline, die selbst nicht reproduziert ist.** C-42 ist in der Alignment-Matrix PARTIAL mit *keinem E-xx* — „research_notes-Eigenangabe", „NICHT in dieser Reconciliation-Pipeline als E-xx re-validiert", „konservativ als L1-Selbstauskunft behandelt", „keine unabhängige Reproduktion, keine FDR-Betrachtung über die 36 Features". Ein ΔR² ≥ +0.02 *über C-42* ist nur dann interpretierbar, wenn C-42s R²=0.249 selbst in *dieser* Pipeline mit *demselben* Split/Fenster steht. Sonst misst man ein Inkrement gegen eine fremde Zahl aus einem fremden Datensatz (Apr-2026-OOS nach Jan–Mar-Training) — und ein positives ΔR² könnte reines Baseline-Artefakt sein. **Das Gate ist methodisch sauber, aber es steht auf Sand, solange die Baseline nicht steht.** Die Anti-S1-Logik ist richtig; ihre Voraussetzung (laufende, validierte Baseline) ist unerfüllt.
- **Falsifikations-Gate-Test:** Das ΔR²-Gate ist *nicht* eigenständig — es hängt definitionsgemäß an C-42. Damit fällt es unter das Enabler-Falsifikations-Kriterium (siehe A-6).
- **Minimale Bedingung für PILOT:** **Reproduktions-Reihenfolge zwingend:** Schritt 0 = C-42 in dieser Pipeline als E-xx reproduzieren (LightGBM/HAR-RV, eigener Walk-Forward, FDR über die Features). Erst wenn C-42 ein eigenes E-xx ≥ L1 hat, ist das ΔR²-Gate für C-11/C-12 sinnvoll. Dann PILOT mit FDR-Korrektur über die getesteten Komplexitäts-Features (GM-2!), Abbruch bei ΔR² ≤ 0. Vor Schritt 0: **PARK.**

---

### A-3 — C-31 Cyclostationary CFAR (Futures)

- **Steelman:** Korrekt und stark — C-31 ist der **einzige** Detektor im Cluster mit *eingebauter* Falschalarm-Kontrolle (CFAR). Das adressiert GM-2 (in keiner Quelle FDR-korrigiert) und INC-03 (Q90 übertriggert, 50–60 Trades/24h) auf Mechanismus-Ebene statt per Schwellen-Bastelei. Das ist ein echtes Alleinstellungsmerkmal.
- **Spot/Optionen:** Zustimmung zu DROP/N/A.
- **Futures — Härtester Einwand (Kostenehrlichkeit):** Die **bestbelegte Aussage des ganzen Projekts** steht gegen C-31: Round-Trip-Friktion 11 bps (Kostenbaseline) übersteigt jede gemessene Roh-Edge (max |Roh| ≈ 4–7 bps). Die Quelle selbst flaggt den Sekunden-Horizont als evtl. unter der Fee-Schwelle. CFAR kontrolliert die *Falschalarmrate*, nicht die *Edge-Größe* — ein perfekt kalibrierter Detektor eines Musters, das < 11 bps trägt, ist trotzdem wertlos. Der Advocate gesteht das in Zugeständnis #4 selbst zu. Die eingebaute Falschalarm-Kontrolle adressiert das *Trigger*-Problem (INC-03), nicht das *Friktions*-Problem (E-16: Friktion ~35× Richtung auf S2).
- **Falsifikations-Gate-Test:** Das Handelbarkeits-Gate (Lead-Zeit > 50 ms, Edge > 11 bps) ist **eigenständig** — es prüft eine physikalische/ökonomische Erreichbarkeit, nicht ein nachgelagertes Signal. Zusammen mit A-1s Erreichbarkeits-Check ist das eines der zwei Gates im Cluster, die das Enabler-Kriterium bestehen.
- **Minimale Bedingung für PILOT:** Surrogate-Test (p ≤ 0.05, ≥ 2 Fenster) UND Handelbarkeits-Gate (Lead-Zeit > 50 ms UND realisierter Edge-Horizont > 11 bps) *vor* jedem Strategie-Bau. Besteht eines davon nicht: sofortiger DROP. Unter diesem strikt vorgeschalteten Gate akzeptiere ich PILOT — der CFAR-Mechanismus rechtfertigt den Erreichbarkeits-Test, mehr nicht.

---

### A-4 — C-16 TFSAX + Smith-Waterman als Präzedenz-Label (Futures)

- **Steelman:** Bestechend — C-16 bringt sein **eigenes hartes Drop-Gate** mit (PRD-kestrel: OOS-AUC > 0.55, *sonst ersatzloser Drop*). Ein Ansatz, der bereit ist, sich selbst zu falsifizieren, ist das Gegenteil der „schönen Mathematik ohne Abbruchkriterium" von C-14. Und CS-04 ist nachweislich eine **Mess-Lücke, keine Niederlage** (E-13: reiner Loader-Defekt, „mehr Daten helfen nicht").
- **Spot/Optionen:** Zustimmung zu DROP.
- **Futures — Härtester Einwand (Multiple Testing + Datenbedarf):** Das harte Gate ist genau richtig — aber der M-S23-Orderflow-Variante fehlt jede Evidenz (UNTESTED, kein E-xx), und ein Präzedenz-Match-Verfahren über eine 5y-Bibliothek mit Smith-Waterman-Scoring ist ein **Multiple-Testing-Magnet** (GM-2, in keiner Quelle korrigiert): viele Templates × viele Alignments → ein hochsignifikanter Match ist als Zufallstreffer wahrscheinlich, wenn nicht surrogat-kontrolliert. Das PRD-fable5-Gate verlangt zu Recht *zusätzlich* einen Surrogate-Test (p < 0.05). Mein Einwand ist nicht gegen das Gate, sondern gegen die Priorisierung: C-16 ist der **datenhungrigste** Kandidat (5y-Bibliothek, publicTrade-Archiv) bei null Vorbefund — die Opportunitätskosten gegenüber A-3/C-31 (billiger Surrogate-Test) sind hoch.
- **Falsifikations-Gate-Test:** Das OOS-AUC-Gate ist **eigenständig** im Sinne, dass es C-16 als Klassifikator direkt prüft (Regime-Label vs. Forward-Outcome), nicht über ein fremdes Basissignal. Das ist sauber — C-16 ist neben C-31 der Kandidat mit dem klarsten eigenen Falsifikations-Gate.
- **Minimale Bedingung für PILOT:** Akzeptiert — aber **nachgeordnet** hinter C-31 (billiger) und der C-42-Reproduktion. Gate: OOS-AUC > 0.55 (bzw. BA ≥ 0.55) + Surrogate p < 0.05, walk-forward ≥ 2 Fenster, sonst ersatzloser Drop. Kein Nachverhandeln — das ist der Vorbild-Teil.

---

### A-5 — C-43 Conformal Prediction als Sizing-Kalibrator (alle Märkte)

- **Steelman:** Mechanistisch elegant — CP übersetzt Unsicherheit *verteilungsfrei und prüfbar* (Coverage ≥ 85% OOS) in Positionsgröße, und als Friktions-Filter („nur handeln wenn Konfidenz-Intervall eng genug, dass Edge > 11 bps") hätte es das S2-Verlustmuster (E-16: Friktion ~35× Signal; E-04: hit_sum 0.179) tatsächlich unterdrückt.
- **Härtester Einwand (Unfalsifizierbarkeit):** **C-43 ist der reinste Fall des Enabler-Problems.** Der Advocate gesteht es in Zugeständnis #2 selbst: CP ist „kein Alpha-Generator", testbar *erst* wenn ein L3-Basissignal existiert — und **kein einziges L3-Basissignal im Register hat je die Münzwurf-Linie überschritten** (außer C-42, das selbst kein Direktionssignal ist). Das Coverage-Gate (≥ 85%) ist trivial erfüllbar (ein hinreichend breites Intervall deckt immer ≥ 85%) und sagt *nichts* über ökonomischen Nutzen. Das zweite Gate (gated Sharpe > un-kalibriert) ist das ökonomisch relevante — aber es ist **per Konstruktion nicht ausführbar ohne Basissignal.** C-43 ist „ein perfekter Filter für ein nicht-existentes Signal" (Advocate-Wortlaut).
- **Spot/Optionen:** dieselbe Abhängigkeit; Optionen zusätzlich an INC-04 gebunden.
- **Falsifikations-Gate-Test:** **Besteht nicht.** Das einzige eigenständige Gate (Coverage ≥ 85%) ist nicht-ökonomisch und trivial; das ökonomische Gate hängt vollständig an einer nicht-existenten Basis-Strategie.
- **Minimale Bedingung für PILOT:** **DROP als eigenständiger PILOT — stattdessen PARK als Querschnitts-Wrapper**, der *automatisch* aktiviert wird, sobald *irgendein* L3-Signal ein eigenes Outcome-E-xx > Münzwurf erreicht. C-43 ist kein PILOT-Kandidat, sondern eine Architektur-Notiz fürs FINAL_PRD. Es zuerst zu pilotieren hieße, Validierungszeit in einen Layer ohne Substrat zu stecken (Opportunitätskosten).

---

### A-6 — Cluster-Synthese: „Regime ist die notwendige Bedingung" (INC-05)

- **Steelman:** Die Doppelbeobachtung ist real und nicht-trivial: (1) unkonditional kein Richtungs-Edge (INC-05, AUC ≈ 0.50), (2) das einzige OOS-über-Münzwurf-Signal war nicht-direktional (C-42). Daraus folgt korrekt: *falls* Edge existiert, *muss* er konditional sein.
- **Härtester Einwand (logischer Fehlschluss):** Der Advocate macht aus einer **notwendigen Bedingung eine Verheißung.** Aus „unkonditional = Münzwurf" (INC-05) folgt logisch *nur*: WENN Edge existiert, DANN ist er konditional. Es folgt **nicht**, dass Edge existiert. Die Existenz eines konditionalen Edges ist im gesamten Register **unbewiesen** (alle sechs Cluster-Claims UNTESTED, kein Outcome-E-xx; das einzige PARTIAL-Outcome C-42 ist nicht-direktional und nicht reproduziert). „Regime-Detektion ist notwendige Vorbedingung für jeden nachgelagerten Edge" ist nur dann ein Argument *für* das Cluster, wenn ein nachgelagerter Edge existiert — und genau das ist offen. Andernfalls ist Regime-Detektion die notwendige Vorbedingung für **nichts.** INC-05 adelt das Cluster nicht; es verlagert nur die Beweislast auf das nachgelagerte Signal, das niemand hat.
- **Das harte Enabler-Falsifikations-Kriterium (auf Auftrag):** *Welches Regime-Modul hat ein eigenständiges Falsifikations-Gate, das NICHT von einer noch-nicht-existenten Basis-Strategie abhängt?* Antwort nach Durchsicht:
  - **C-08** (A-1): JA, der Erreichbarkeits-Check (feuert auf bekannten Brüchen?) ist basis-unabhängig — aber teuer (Bulk-Historie, GM-6).
  - **C-31** (A-3): JA, das Handelbarkeits-Gate (Lead-Zeit > 50 ms, Edge > 11 bps, Surrogate) ist basis-unabhängig und *billig*.
  - **C-16** (A-4): JA, das OOS-AUC-Gate prüft C-16 als Klassifikator direkt gegen Forward-Outcomes — basis-unabhängig.
  - **C-11/C-12** (A-2): NEIN — das ΔR²-Gate hängt an C-42 (die selbst reproduziert werden muss). Bedingt eigenständig *nach* C-42-Reproduktion.
  - **C-43** (A-5): NEIN — hängt vollständig an einem nicht-existenten L3-Signal.
- **GM-6 — Kostenehrlichkeit:** Der Advocate gesteht es in Zugeständnis #3 selbst, und es ist der härteste Cluster-Vorbehalt: **Regime-Brüche sind in 24h-Fenstern nicht enthalten** (GM-6, E-02: Liquidations-Events spärlich, nur 4/5 Symbole ausreichend; E-12: BOCPD feuert nie). *Jeder* Detektor in diesem Cluster wird im vorhandenen Fenster nicht-feuern, ohne dass das etwas beweist. Die Validierung — *jede* — braucht zwingend Bulk-Historie mit dokumentierten Bruch-Episoden: **Wochen bis Monate Aufzeichnungs-/Download-Vorlauf, bevor irgendein Test läuft.** Das ist keine „nächste Iteration", und kein PRD darf diesen Vorlauf verschweigen.

---

### Skeptic — Urteilstabelle (Gegenvorschlag zur Advocate-Tabelle)

| Claim | Advocate | Skeptic-Gegenvorschlag (Futures) | Kern-Grund |
|---|---|---|---|
| C-08 BOCPD | PILOT | **PARK** → PILOT nur falls iter-5-Time-Stop den E-10-Tail NICHT schneidet | Ockham: `if elapsed>120s: exit` adressiert E-10 trivial; C-08 muss gegen iter-5-Baseline antreten, nicht ungate-t |
| C-11 PH | PILOT | **PARK** bis C-42 reproduziert (E-xx) | ΔR²-Gate steht auf nicht-validierter Baseline (C-42 = L1-Selbstauskunft) |
| C-12 RQA | PILOT | **PARK** bis C-42 reproduziert (E-xx) | dito |
| C-16 TFSAX+SW | PILOT | **PILOT** (nachgeordnet), hartes OOS-AUC>0.55 + Surrogate | eigenständiges Gate ok; datenhungrig, Multiple-Testing-Magnet |
| C-31 CFAR | PILOT | **PILOT** (priorisiert), Surrogate + >50ms + >11bps ZUERST | einziges billiges, eigenständiges, friktions-ehrliches Gate |
| CS-07 (C-16∥C-31) | PILOT | **PARK** bis C-16 UND C-31 je einzeln das Gate bestehen | Konsens-Filter erst sinnvoll nach Einzel-Validierung |
| C-43 CP | PILOT | **PARK** (Architektur-Notiz), auto-aktiv ab erstem L3-Outcome-E-xx | unfalsifizierbar ohne Basissignal — Filter für nichts |

---

### An den Orchestrator (≤ 10 Zeilen)

1. **A-6/INC-05 = logischer Fehlschluss:** „unkonditional=Münzwurf" beweist NICHT, dass konditionaler Edge existiert — nur, dass er, falls er existiert, konditional sein muss. Existenz ist registerweit unbewiesen (alle 6 Claims UNTESTED, kein Outcome-E-xx). INC-05 adelt das Cluster nicht, es verlagert die Beweislast.
2. **A-2/C-42 = Gate auf Sand:** ΔR²-Gate misst gegen eine nicht-reproduzierte L1-Selbstauskunft (research_notes, kein E-xx). Reproduktions-Reihenfolge erzwingen: C-42 als E-xx zuerst, dann C-11/C-12 → bis dahin PARK statt PILOT.
3. **A-1/C-08 = Ockham:** iter-5-Time-Stop (`if elapsed>120s`) schneidet den E-10-Tail bereits mit 2 trivialen Parametern; BOCPD muss gegen die iter-5-Baseline antreten, nicht gegen die ungate-te Strategie → PARK bis iter-5 (E-15).
- **Stehengelassen (gewürdigt):** E-10 ist die sauberste isolierte Verlustquelle; „Anti-S1" (ΔR² statt Importschwelle) ist echter Fortschritt. **C-31 (CFAR) und C-16 (OOS-AUC) bleiben PILOT** — sie haben die einzigen eigenständigen, basis-unabhängigen Falsifikations-Gates; C-31 priorisiert (billig, friktions-ehrlich).
- **GM-6 Kostenwahrheit:** JEDE Cluster-Validierung braucht Monate Bulk-Historie mit Bruch-Episoden vor dem ersten Test — kein PRD darf das verschweigen.
- **NICHT committet** (gemäß Auftrag).
