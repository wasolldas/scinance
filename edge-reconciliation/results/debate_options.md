# Debatte: Options / VRP

**Cluster:** options (Options / Variance Risk Premium)
**Phase:** 4 — DEBATE
**Stand:** 2026-06-11
**Cluster-Claims:** C-33 (VRP/Short-Vola Optionen), CS-09 (Topologisch-direktionaler Options-Block), Options-Anteile von C-11 (TDA/PH auf IV-Surface, M-S17) und CS-08 (Regime-konditioniertes Signal, Options-Leg via C-32). Querschnitt: C-34/C-35 (GMM-VRP), C-42 (Vol-Prognose als Enabler).
**Verbindliche Randbedingungen:** INC-04 (NULL Options-Dateninfrastruktur, kein IV-Archiv), Bybit-Options-Liquidität dünner als Deribit (CS-09: 60–80 % der Stunden fallen Liquiditäts-Check durch), Kostenbaseline (Options-Taker-Fee 0.03 %, PRD-Referenz, ungemessen).

---

## Advocate

### Vorbemerkung — die strukturelle Asymmetrie dieses Clusters

Der gesamte Rest des Registers kämpft gegen INC-05: Richtungs-AUC ≈ 0.50 (Münzwurf) auf 1h/4h mit klassischen Features. Jeder direktionale Edge-Kandidat (C-09, C-16, C-18, C-20, C-21; CS-08-Direktionsleg) trägt diese Hypothek. **Der VRP-Kern (C-33) ist der einzige Edge-Kandidat im ganzen Register, der KEINE Richtungsprognose benötigt** — er erntet eine Prämie, die aus der Differenz IV−RV entsteht, nicht aus einem Bet auf das Vorzeichen des nächsten Returns. Das ist kein rhetorischer Vorteil, sondern ein empirischer: VRP ist gegenüber dem härtesten dokumentierten Negativbefund des Registers (INC-05) strukturell immun. Ich baue mein Argument konsequent von dieser Asymmetrie aus auf.

Markt-Differenzierung dieses Clusters: Der **Optionen-Markt** ist Zentrum (VRP-Harvest lebt dort). **Spot/Futures** treten ausschließlich als **Hedge-Leg** (Delta-Hedge der Short-Vola-Position) auf — sie generieren hier keinen eigenen Edge, sondern sind Kostenposten und Ausführungs-Risiko der Options-Strategie.

---

### A-1 — VRP ist die am besten fundierte Prämie im Register; C-33 ist der einzige Claim, der sie adressiert

C-33 (Short-Vola, IV−RV-Harvest) ist mechanistisch durch eine **strukturelle Versicherungsnachfrage** begründet: systematische Hedger zahlen dauerhaft einen Aufschlag auf implizite über realisierte Volatilität (C-33-Kernidee). Das ist die ökonomisch transparenteste Edge-These im gesamten Claims-Register — sie braucht weder ein importiertes theoretisches Schwellwert-Konstrukt (anders als C-14/C-30, deren Schwellen laut E-01 nie erreicht werden) noch eine Richtungsprognose (anders als alle INC-05-belasteten Module). Der Mechanismus ist: Prämie existiert, weil jemand strukturell für Absicherung überzahlt. Das ist genau die Klasse von Edge, die der GRUNDHALTUNG „Evidenz schlägt Idee" am ehesten standhält, sobald sie gemessen wird — und A-2 zeigt, dass die Messbarkeit billig ist.

**Status-Ehrlichkeit:** C-33 ist UNTESTED (alignment_matrix: kein Options-Replay, kein E-xx berührt Optionen). Ich verteidige hier NICHT einen belegten Befund, sondern den **Mechanismus** und den **günstigsten Validierungspfad** — exakt der Modus, den meine Rolle für UNTESTED-Claims vorschreibt.

### A-2 — Der Validierungspfad ist asymmetrisch billig: VRP ist mit reiner Eigenaufzeichnung in ~3 Monaten falsifizierbar

Der entscheidende Kostenvorteil: Um C-33 zu testen, brauche ich **kein** Backtest-Framework mit Trade-Simulation, **keinen** Panel-Harness (der C-13/C-17/CS-05 blockiert, E-14), **keinen** Modell-Loader (der C-18/CS-04 blockiert, E-13). Ich brauche nur **zwei Zeitreihen**: ATM-markIv (aus `options-tickers` WS, public — C-33-Abhängigkeit) und realisierte Vol (RV ist bereits gelöst, siehe A-5/C-42). Die VRP-Schätzung IV²−RV ist eine Subtraktion zweier aufgezeichneter Reihen. Das Validierungs-Gate (IV−RV ≥ 3 % über 12 Monate, ≥ 2 Fenster — C-33-Gate) ist ein **reiner Beobachtungs-Test ohne Trading-Risiko**: man zeichnet auf und misst, ob die Prämie persistent positiv ist, BEVOR ein Cent eingesetzt wird.

Das ist die ehrliche Antwort auf INC-04: Ja, es existiert NULL Options-Dateninfrastruktur, und ja, die Bootstrap-Kosten sind ein ≥ 3-Monats-Aufzeichnungsvorlauf (C-33: Aufwand L; C-34: ≥ 3 Monate IV-Vorlauf). Aber dieser Vorlauf ist (a) **passiv** (ein WS-Recorder, kein Strategie-Code), (b) **mehrfach verwertbar** (dieselbe IV-Aufzeichnung speist C-33, C-34-VRP-Kanal, C-11-M-S17-IV-Surface und CS-09 — vier Claims aus EINEM Datenstrom), und (c) **risikofrei in der Messphase**. Verglichen mit den drei Infrastruktur-Sackgassen des Futures-Stacks (E-13 Loader, E-14 Panel-Harness, E-07 Time-Stop-Bug) ist ein WS-Recorder die mit Abstand billigste Lücke im ganzen Register.

### A-3 — Optionen: ADVOCATE-Empfehlung PILOT (nicht ADOPT) — der Liquiditäts-Stresstest ist Teil des Gates, nicht ein Hindernis davor

Ich gestehe sofort die zentrale Schwäche zu (CS-09: Bybit-Options-Liquiditäts-Check fällt in 60–80 % der Stunden durch; INC-04 nennt Liquidität als größtes Risiko). Aber genau hier liegt die Stärke des VRP-Profils: **VRP ist eine niederfrequente Harvest-Strategie, keine Mikrostruktur-Strategie.** Ein Vol-Verkäufer muss nicht in jeder Stunde handeln — er braucht **wenige, gut getimte Roll-Fenster** (typisch Entry nahe ATM mit Wochen-/Monats-Laufzeit). Dass 60–80 % der Stunden illiquide sind, ist tödlich für eine Sekunden-Horizont-Strategie (vgl. C-31-Warnung) — aber für eine Strategie, die pro Woche evtl. 1–2 ATM-Positionen aufbaut und delta-hedged, genügt das verbleibende 20–40 %-Liquiditätsfenster, sofern es die ATM-Tiefe trägt.

**Der Spread-Kosten-Stresstest gehört deshalb direkt ins Validierungs-Gate**, nicht als Vorab-Ausschluss. Konkret: Das aufgezeichnete Options-Orderbuch erlaubt vor jedem Live-Einsatz die Messung des realisierten ATM-Bid-Ask in genau den Stunden, in denen man handeln würde. Die ökonomische Bedingung ist hart und ehrlich: **geernteter VRP (IV−RV, Gate ≥ 3 %) muss den effektiven ATM-Spread plus 2× Options-Taker-Fee (0.03 % je Leg, Kostenbaseline) plus die Delta-Hedge-Friktion am Futures-Leg übersteigen.** Bei dünner Bybit-Liquidität ist das ein scharfes Gate — aber 3 % Jahres-VRP gegen einen ATM-Spread im einstelligen Prozentbereich der Prämie ist nicht von vornherein verloren, anders als die Futures-Befunde, wo die Roh-Edge (max. 4–7 bps) die 11-bps-Friktion NIE schlug (Kostenbaseline-Kernrelation, E-03/E-09/E-16). VRP startet auf der richtigen Seite dieser Ungleichung — das ist der qualitative Unterschied zu jedem gemessenen Futures-Edge.

### A-4 — Spot/Futures in diesem Cluster: nur als Delta-Hedge-Leg, und dort ist die Datenlage bereits gut

Für **Spot** gibt es in diesem Cluster keine eigenständige Empfehlung — Spot tritt allenfalls als Delta-Hedge-Instrument auf, wo Perpetual-Futures wegen Funding-Mechanik meist überlegen sind. Für **Futures als Hedge-Leg** ist die Lage günstig: Der Delta-Hedge der Short-Vola-Position handelt liquide BTC-Perps, deren Mikrostruktur und Kosten im Register am besten dokumentiert sind (Kostenbaseline: 11 bps Taker round-trip, ggf. C-37-Spread-Markt mit ~4 bps Maker als Hebel). Der Hedge erzeugt keinen Edge, sondern definiert die Hedge-Kosten, die das VRP-Gate (A-3) schlagen muss. **Entscheidend:** Die Hedge-Frequenz ist ein freier Designparameter — seltener hedgen senkt Friktion, erhöht aber Gamma-Restrisiko. Das ist eine messbare, im Backtest tunebare Größe, kein unbekanntes Risiko. Damit ist das Futures-Leg dieses Clusters das technisch am besten beherrschte Element der gesamten Konstruktion.

### A-5 — C-42 macht die HÄLFTE des VRP-Inputs schon heute belastbar (ohne INC-04-Vorlauf)

Der VRP ist IV²−RV. Die **RV-Komponente ist bereits der stärkste positive Befund des ganzen Registers**: C-42 (LightGBM/HAR-RV) liefert Test-R²=0.249, Pearson=0.578 OOS (Apr-2026 nach Jan–Mar-Training) und ist als einziger Claim PARTIAL statt UNTESTED. Das bedeutet: Von den zwei VRP-Inputs ist einer — die realisierte/prognostizierte Volatilität — **schon heute deployable-ready** und unabhängig von INC-04. Nur die IV-Komponente fehlt und wird durch die Aufzeichnung aus A-2 geschlossen.

Das senkt das Bootstrap-Risiko erheblich: Wir bauen nicht „auf null" auf, sondern setzen den fehlenden IV-Strom auf eine bereits validierte RV-Schätzung auf. C-34 formalisiert genau das (VRP-Kanal ΔR² ≥ +0.02 über RV-only) und C-35 (CEEMDAN, ΔR² ≥ +0.01) liefert optionale RV-Verfeinerung. Cross-Cluster-Ehrlichkeit: C-42 ist eine research_notes-Selbstauskunft, in dieser Pipeline NICHT als E-xx re-validiert (alignment_matrix C-42-Note) — ich überschätze sie nicht. Aber als L1-Selbstauskunft ist sie der belastbarste Ankerpunkt, den dieser Cluster hat, und sie liegt bereits vor.

### A-6 — C-11 (IV-Surface-PH, M-S17) und CS-09: VRP als Kern, Topologie als optionaler Konditionierer — getrennt bewerten

CS-09 koppelt C-33 (VRP) mit C-11-M-S17 (Persistent Homology auf der IV-Surface als Tail-Frühwarnung) und C-43 (Conformal Sizing). Hier trenne ich scharf, wie es meine Rolle verlangt:

- **C-33 (VRP-Kern):** trägt allein, siehe A-1/A-2 — PILOT-würdig auch ohne jeden topologischen Überbau.
- **C-11-M-S17 (IV-Surface-Topologie):** UNTESTED, datenhungriger (braucht volle IV-Surface über Strikes/Laufzeiten, nicht nur ATM), und teilt das generische Crash-Frühwarn-Risiko. Mechanistisch plausibel als **Risk-Off-Schalter** (topologischer Bruch der IV-Surface → Vol-Short schließen/reduzieren vor Tail), aber NICHT als eigenständiger Alpha-Generator. Sein Wert ist defensiv: VRP-Short-Vola hat ein asymmetrisches Verlustprofil (kleine stetige Gewinne, seltene große Verluste bei Vol-Spikes) — ein verlässliches Tail-Frühwarnsignal verbessert genau das schwächste Glied des VRP-Profils.

**CS-09-Empfehlung:** Die Strategie ist sinnvoll **dekomponierbar** — zuerst C-33 standalone pilotieren (ATM-VRP + simpler Delta-Hedge), C-11-Topologie und C-43-Sizing erst als Verstärker hinzunehmen, wenn der VRP-Kern das Spread-Gate besteht. Das entspricht der GRUNDHALTUNG „Modul ≠ Strategie": CS-09 darf nicht als Monolith stehen oder fallen.

### A-7 — CS-08-Options-Anteil: C-32 (Funding-Contrarian) als Vol-Regime-Konditionierer, nicht als Direktionssignal

CS-08 (Regime-konditioniertes Signal) ist primär Futures-direktional und damit voll INC-05-belastet. Sein einziger options-relevanter Anteil ist C-32 (Funding-Contrarian, Extremwert): Extreme Funding-Raten signalisieren Überextension und korrelieren typischerweise mit Vol-Regime-Wechseln. Für den Options-Cluster ist C-32 NICHT als eigener direktionaler Trade interessant (dort gilt INC-05 und die von der Quelle selbst erwartete Carry-Kompression/schneller Signalzerfall), sondern **als Konditionierungs-Input für das VRP-Timing**: Extreme Funding markiert Stress-Regime, in denen IV typischerweise spiked — also Fenster, in denen man Vola NICHT blind shorten sollte. C-32 verdient im Options-Cluster damit nur eine schwache Rolle: als eines von mehreren Regime-Flags (neben C-34-GMM-Regime), das den VRP-Harvest in Stressphasen drosselt. Eigenständig (Options-Leg von CS-08) DROP-Tendenz; als Regime-Flag für C-33 PARK-würdig.

### A-8 — Das Multiple-Testing-Argument läuft hier ZUGUNSTEN von VRP

GM-2 (kein FDR/Bonferroni) entwertet im Register jeden „signifikanten" Einzelbefund, der aus vielen Strategie/Symbol/Richtungs-Kombinationen herausgefischt wurde (E-03/E-04/E-16-Kontext). VRP ist die Ausnahme: Es ist **eine** ökonomisch a priori begründete Hypothese mit **einem** Vorzeichen (IV>RV), nicht ein aus einem großen Suchraum selektierter Mikro-Effekt. Damit hat C-33 das geringste Data-Mining-Risiko des gesamten Registers — der Befund muss nicht gegen ein riesiges Test-Multiplikat verteidigt werden, weil die Hypothese vor der Datenansicht feststand. Das adressiert direkt die FINAL_PRD-Checklisten-Anforderung „Multiple-Testing-Risiko über alle Ansätze adressiert": VRP ist der Ansatz, der diese Hürde am elegantesten nimmt.

---

## Zusammenfassung Advocate — Empfehlungstendenz je Claim × Markt

| Claim | Spot | Futures | Optionen |
|---|---|---|---|
| **C-33 (VRP/Short-Vola)** | — (nur Hedge) | Hedge-Leg, datenseitig beherrscht | **PILOT** — billigster falsifizierbarer Edge im Register |
| **C-11-M-S17 (IV-Surface-PH)** | — | — | PARK→Pilot als defensiver Tail-Schalter, NICHT standalone |
| **CS-09 (Options-Block)** | — | Hedge-Leg | **PILOT, dekomponiert** — VRP-Kern zuerst, Topologie/CP später |
| **CS-08-Options-Leg (C-32)** | — | INC-05-belastet | DROP standalone / PARK als VRP-Regime-Flag |
| **C-34/C-35 (Querschnitt)** | — | RV-Stack (Futures) | VRP-Kanal speist C-33; Aufzeichnung gemeinsam nutzen |
| **C-42 (Enabler)** | — | PARTIAL (RV-Baseline) | liefert die halbe VRP-Gleichung bereits heute |

### Stärkstes Einzelargument (1 Satz)
VRP (C-33) ist der einzige Edge-Kandidat im ganzen Register, der gegen den härtesten Negativbefund (INC-05, Direction-AUC≈0.50) strukturell immun ist, weil er keine Richtungsprognose braucht — und seine halbe Input-Gleichung (RV) ist via C-42 bereits der einzige PARTIAL-Vol-Befund des Registers.

### Was ich zugestehe (ehrlich schwächste Stelle)
**Die Spread-Kosten auf Bybits dünnem Options-Markt sind nicht gemessen und könnten die 3 %-VRP-These vollständig auffressen.** CS-09 selbst nennt 60–80 % illiquide Stunden; die Options-Taker-Fee (0.03 %) ist eine ungemessene PRD-Referenz; der ATM-Bid-Ask in den handelbaren Stunden ist völlig unbekannt. Es ist denkbar, dass der realisierte Spread + Hedge-Friktion die geerntete Prämie genau dort frisst, wo Bybit handelbar ist — exakt das Schicksal, das jeden Futures-Edge ereilte (Friktion > Signal, Kostenbaseline). Ich kann den Mechanismus und die ökonomische Plausibilität belegen; ich kann NICHT belegen, dass Bybit-Spezifisch genug Netto-VRP übrigbleibt. Das ist genau die Frage, die der Pilot zuerst beantworten muss — und sie kann negativ ausfallen.

### Vorgeschlagenes Validierungs-Gate (PILOT C-33)
1. **Phase 0 — Aufzeichnung (≥ 3 Monate, passiv, risikofrei):** `options-tickers` WS (ATM-markIv) + Options-Orderbuch-Tiefe + RV aus C-42-Pipeline. Schließt INC-04 für VRP mit EINEM Recorder.
2. **Gate 1 — Prämie persistent:** (IV−RV) ≥ 3 % im OOS über ≥ 2 disjunkte Fenster (C-33-Gate). Abbruch bei < 3 % in einem Fenster.
3. **Gate 2 — Spread-Stresstest (das entscheidende Bybit-Gate):** Netto-VRP nach realisiertem ATM-Spread + 2× 0.03 % Options-Fee + gemessener Delta-Hedge-Friktion (Futures-Leg) bleibt > 0 in den tatsächlich handelbaren Stunden. Abbruch, wenn ATM-Tiefe < Ordergröße in > 60 % der Entry-Fenster ODER Netto-VRP ≤ 0.
4. **Gate 3 (optional, nur falls C-33 besteht):** C-11-M-S17-Tail-Schalter senkt Max-DD ≥ 20 % ohne Sharpe-Verlust > 10 %; sonst C-33 standalone fahren.
