# climatology-ensemble — Discipline Scan (Phase DISCIPLINE-SCAN)

**Agent:** `climatology-ensemble` · **Stand:** 2026-07-07 · **Sonderrolle (CLAUDE.md §5):** ausschließlich
Halte-/Vorhersage-Horizont **≥ 1 Tag** — nicht optional. Grund: alle 13 bisherigen Verdikte betrafen
Sub-Minuten-Mikrostruktur (Friction-Wand, 11–15 bps) oder ein Einzelmodell-ML-Forecast (C-42/H-02,
0/5 Symbole OOS-R²≥0.15, 0/36 Features FDR-sig). Kein bisheriger Test hat den Zeithorizont selbst
variiert. Alle drei folgenden IC-Vorschläge sind **nichtparametrisch** (Analog-Ensemble-Familie) —
keiner ist eine global gefittete Parameterfunktion, also keiner fällt zurück ins C-42/H-02-Territorium.

---

## Pflicht-Schritt 1: Methodenrecherche (WebSearch, über den Werkzeugkasten der Agenten-Datei hinaus)

Recherchiert über den in der Agenten-Datei genannten Startpunkt (AnEn, CRPS, Teleconnection,
Ensemble-Spread) hinaus:

1. **Delle Monache et al. (2013), "Probabilistic Weather Prediction with an Analog Ensemble"** (Monthly
   Weather Review) — der methodische Referenzpunkt für AnEn: CRPS-Minimierung + PCA der Prädiktoren zur
   Merkmalsvektor-Gewichtung. **Aufgenommen** — direkt die Basis für IC-CLIM-1's Distanzmetrik-Gewichtung.
2. **Rank-Histogramm / PIT (Probability Integral Transform)** — Kalibrierungs-Diagnostik zusätzlich zu
   CRPS: prüft, ob die Ensemble-Verteilung als Ganzes kalibriert ist (U-Form = Unterdispersion,
   Dreiecksform = systematischer Bias). **Aufgenommen** als Sekundärdiagnose in IC-CLIM-1/IC-CLIM-3 (CRPS
   allein sagt nichts über Über-/Unterdispersion; das ist ein Pluspunkt gegenüber dem reinen R²-Ansatz
   von C-42).
3. **Brier Score** — Standardmaß für binäre Ereigniswahrscheinlichkeiten (z. B. "P(realisierte Vol über
   Schwelle X in 3 Tagen)"). **Erwogen, nicht separat aufgenommen** — für die hier verwendeten
   kontinuierlichen Verteilungsvorhersagen ist CRPS die strengere, informationsreichere Metrik; Brier
   Score wäre nur bei einer expliziten binären Schwellen-Formulierung nötig (redundant zu CRPS bei
   stetiger Zielgröße).
4. **Bayesian Model Averaging (BMA) / Multi-Model-Ensembling** (Raftery et al.; ECMWF-Multi-Modell-BMA)
   — gewichtete Kombination mehrerer Vorhersagemodelle nach rollierender Performance (EM-Algorithmus für
   Gewichte). **Erwogen, VERWORFEN als eigener IC-Vorschlag** — BMA fittet Gewichte über ein
   Trainingsfenster; das nähert sich strukturell wieder einer parametrischen Kombinationsfunktion und
   damit dem C-42/H-02-Risikobereich. Als Cross-Domain-Hinweis dokumentiert (s. u.), nicht als eigener
   IC.
5. **Schaake Shuffle / Ensemble-Copula-Kopplung** — Verfahren zur Rekonstruktion realistischer
   Multivariat-/Multi-Symbol-Abhängigkeitsstruktur zwischen Ensemble-Mitgliedern (in der Meteorologie:
   räumliche Kohärenz zwischen Stationen). **Erwogen, nicht aufgenommen** — adressiert ein
   Multi-Symbol-Kohärenzproblem, das erst relevant wird, wenn AnEn gleichzeitig für mehrere Symbole
   simuliert wird; für die hier vorgeschlagenen Single-Symbol- bzw. paarweisen Teleconnection-Tests (noch)
   nicht nötig, als Erweiterung für eine spätere Multi-Symbol-Portfolio-Version vermerkt.
6. **Spread-Reliability-Slope (SRS)** (neueres Verfeinerungs-Framework der klassischen
   Spread-Skill-Beziehung, Wang et al. 2026 u. a.) — quantifiziert, OB die Ensemble-Spread-Fluktuation
   überhaupt reliable Information über den Fehler trägt (kontrolliert für Sampling-Rauschen).
   **Aufgenommen** — schärfere Formulierung als die klassische lineare Spread-Skill-Korrelation, direkt in
   IC-CLIM-3 als Verifikationsrahmen verwendet statt einer naiven linearen Korrelation.
7. **Constructed-Analog-Methode** (lineare Kombination mehrerer historischer Analoga statt Auswahl der
   k nächsten Nachbarn, verbreitet in der Klimarekonstruktion) — **erwogen, nicht aufgenommen**: die
   lineare Kombination mehrerer Zustände verwischt genau die Verteilungsinformation (Tail-Risiko
   einzelner Analoga), die AnEn gegenüber einem Punktschätzer auszeichnet; würde den nichtparametrischen
   Charakter unterlaufen.

---

### IC-CLIM-1 — AnEn-Vol-Regime-Forecast vs. HAR-RV-Baseline
Fachgebiet: Klimatologie/Meteorologie (Ensemble-/Analog-Forecasting)
Kernfrage: Liefert ein Analog-Ensemble (k nächste historische Markt-Zustände nach gewichtetem
Merkmalsabstand) eine über 3 Handelstage besser kalibrierte Verteilungsvorhersage der realisierten
Volatilität (gemessen via CRPS) als eine HAR-RV-Punktschätzer-Baseline — Horizont: 3 Tage Halte-/
Vorhersagefenster (explizit ≥1 Tag).
Erwogene Alternativen: siehe Methodenrecherche oben — insb. (1) Delle-Monache-CRPS-Minimierung als
Gewichtungsbasis übernommen, (2) Rank-Histogramm als Sekundärdiagnose ergänzt, (4) BMA verworfen
(parametrisches Rückfall-Risiko), (7) Constructed-Analog verworfen (verwischt Tail-Information).
Merkmalsvektor & Distanzmetrik: Vektor pro Tag t und Symbol s: [RV_1d, RV_5d, RV_20d (realisierte Vol aus
`publicTrade`/Kline), Funding-Rate-Niveau, Funding-Rate-5d-Trend (`rest.fundingRate`), OI-5d-Trend
(`rest.openInterest`)]. Distanz: gewichtete euklidische Distanz nach Feature-Standardisierung (z-Score
über die verfügbare Historie), Gewichte initial gleich, optional per Leave-one-out-CRPS-Minimierung
nachjustiert (Delle-Monache-Stil) — Gewichte werden VOR dem Test fixiert, keine Nachjustierung nach
Sichtung der Ergebnisse. k=15–25 Analoga (Faustregel aus AnEn-Literatur, gegen N der verfügbaren Historie
zu prüfen).
Datenbindung: **Basis-Bestand 2026-03-27…heute (lt. DATASET.md, nicht live geprüft), BTC/ETH zuerst**
(tiefste Symbol-Historie, DATASET.md §5) — das sind ca. 100–102 Handelstage. Das ist **knapp/nur
teilweise ausreichend**: eine robuste AnEn-Bibliothek will typischerweise Hunderte bis Tausende
Tageszustände über mehrere Vol-Regime/Zyklen; mit ~100 Tagen deckt das Basis-Fenster wahrscheinlich nur
EIN Vol-Regime ab (ehrlich als **teilweise data-gated** markiert). Die 2014–2026-Deep-Backfill-Historie
(BTC/ETH ab ~2019, volle Tiefe laut Audit "Reihenfolge/Fortschritt unbekannt") wäre die eigentliche
Zielbasis — **Entsperr-Bedingung:** Manifest-Coverage-Check zeigt `done_days` für BTC/ETH-`publicTrade`
und `rest.fundingRate`/`rest.openInterest` deutlich über die aktuelle ~100-Tage-Basis hinaus (Ziel:
mind. 2–3 Jahre, um mehrere Vol-Regime zu erfassen).
Verifikationsmetrik: CRPS von AnEn-Verteilungsvorhersage vs. CRPS der HAR-RV-Punktschätzer-Baseline
(als entartete Verteilung), zusätzlich Rank-Histogramm zur Kalibrierungsprüfung. Vorregistrierte Schwelle:
CRPS_AnEn < CRPS_HAR-RV auf ≥2 disjunkten Fenstern (Basis-Fenster + ein Out-of-Sample-Fenster sobald
Deep-Backfill verfügbar).
Nicht-Redundanz zu C-42/H-02/H-04: C-42/H-02 war ein global gefittetes parametrisches Modell
(LightGBM/HAR gegen eine feste Feature-Menge, ein funktionaler Zusammenhang für alle Regime) mit
gescheitertem OOS-R². IC-CLIM-1 fittet keine globale Funktion, sondern sucht pro Tag die empirisch
ähnlichsten historischen Zustände und nutzt deren TATSÄCHLICHE Folgeverteilung — regime-adaptiv per
Konstruktion. H-02s Scheitern (R²) ist kein Präzedenzfall gegen ein Verteilungsmaß wie CRPS.
Friktions-Rechnung: Bei 3-Tage-Horizont und typischer BTC/ETH-Tagesvol von 2–5 % ist die erwartete
kumulierte Bewegung (√3-Skalierung) ~3,5–8,7 % (350–870 bps). Gegen die 11–15-bps-Wand ist das ein
Verhältnis von ~25–75×, verglichen mit ~80–500× UNTER der Wand bei den bisherigen Sub-Minuten-Signalen —
eine Größenordnung, die die Wand strukturell überwinden kann. Wichtig: dies ist Mess-Gate zuerst (ist die
Vol-Verteilungsvorhersage kalibriert/besser als Baseline?); Tradability (welche Positionsstruktur —
Vol-Targeting, Straddle o. ä. — die Vorhersage tatsächlich monetarisiert) ist separate Folge-Hypothese
für `friction-tradability-auditor`.
Rechenaufwand: CPU (k-NN über Merkmalsvektoren, Größenordnung 100–3000 Tageszustände × 5 Features — auf
CPU trivial; GPU-vorteilhaft nur bei sehr großer Multi-Symbol-Merkmalsbibliothek und feiner
Zeitauflösung, hier nicht der Fall).
Cross-Domain-Hinweis (optional): BMA-Multi-Modell-Gewichtung (Kandidat 4 oben) wäre eine natürliche
Erweiterung (AnEn + HAR-RV + Momentum-Modell gewichtet kombinieren), fällt aber strukturell näher an
parametrische Kombinationsfunktionen — ggf. für `mechanism-design` oder eine spätere ML-Welle relevant,
nicht für diesen Agenten.
Offene Punkte für data-feasibility-scout: (a) exakte Tageszahl des Basis-Bestands (ca. 100–102 Tage) via
Manifest bestätigen; (b) Coverage-Check für BTC/ETH-Deep-Backfill (wie viele Tage vor 2026-03-27 sind
tatsächlich `done`?); (c) OI hat laut Audit strukturell nur ~30 Tage Rolling-Historie (Binance-OI-Caveat)
— prüfen, ob der OI-Trend-Feature dadurch für Analoga vor >30 Tagen unbrauchbar wird und ggf. aus dem
Merkmalsvektor fallen muss.

---

### IC-CLIM-2 — Cross-Asset-Teleconnection auf Tages-Lag (Extremperzentil-Trigger)
Fachgebiet: Klimatologie/Meteorologie (Teleconnection-Analyse)
Kernfrage: Löst ein Extremperzentil-Ereignis (z. B. Funding-Rate- oder OI-Spike über dem 95./99.
Perzentil) in Symbol A eine Regimeänderung (Sprung in nachfolgender realisierter Vol oder gerichteter
Drift) in einem ANDEREN Symbol B mit einer Verzögerung von **1–5 Handelstagen** aus (nicht Sekunden wie
H-04)?
Erwogene Alternativen: ENSO-Nino3.4-Lag-Korrelations-Literatur als methodisches Vorbild (Lag-Korrelation
zwischen Fernkopplungs-Index und Zielgröße); Granger-Kausalität für Teleconnection-Detektion **erwogen,
verworfen** — Granger testet lineare Vorhersagbarkeit im Mittel, nicht speziell das Extremperzentil-Ereignis
als diskreten Trigger, das hier die eigentliche Fragestellung ist (Ereignis-getriggert, nicht
kontinuierlich); Schaake-Shuffle (Kandidat 5 oben) **erwogen, verworfen** — löst Multivariat-Kohärenz
zwischen Ensemble-MITGLIEDERN, nicht zwischen ASSETS, falsches Analogie-Ziel für dieses IC.
Merkmalsvektor & Distanzmetrik: Kein AnEn-Analogsuche hier, sondern Ereignis-Trigger-Definition:
Trigger_A(t) = 1, wenn Funding-Rate(A,t) oder OI-5d-Δ(A,t) über dem rollierenden 95./99.-Perzentil der
Basis-Historie liegt. Zielgröße: realisierte Vol(B, t+1…t+5) bzw. gerichtete kumulierte Rendite(B,
t+1…t+5), verglichen gegen die unbedingte Verteilung von B (Bootstrap/Permutations-Vergleich, kein
Analogon-k-NN nötig).
Datenbindung: Basis-Bestand 2026-03-27…heute, alle 5 Symbole (5-Symbol-Parität laut Audit für dieses
Fenster gegeben), Streams `rest.fundingRate`/`rest.openInterest` + `publicTrade`. **Data-gated-Warnung:**
bei ~100 Tagen und einer 95./99.-Perzentil-Schwelle sind strukturell nur ~5/~1 Trigger-Ereignisse pro
Symbol zu erwarten (analog zur GL-012-Feasibility-Lehre: Schwelle vor Test auf Erreichbarkeit prüfen) —
für belastbare FDR-Statistik über 5×4=20 Symbolpaare vermutlich zu wenig N. Die tiefe Historie
(2014–2026) würde die Ereigniszahl vervielfachen. **Entsperr-Bedingung:** Deep-Backfill-Coverage für
mind. BTC/ETH/BNB (die am längsten laufenden Serien) liefert genug Historie, dass ≥30 Trigger-Ereignisse
pro Symbolpaar erwartbar sind (Analogie-Richtwert aus PROGRAM_FINAL_REPORT §8 für Kaskaden-Events
übernommen).
Verifikationsmetrik: Permutationstest (Ziehen zufälliger Zeitfenster statt Trigger-Fenster) auf
Verschiebung der bedingten vs. unbedingten Verteilung von B, FDR-Korrektur über alle getesteten
Symbolpaare (Benjamini-Hochberg α=0.10, `registry-keeper`-Familie).
Nicht-Redundanz zu C-42/H-02/H-04: H-04 testete BTC→ETH-Lead-Lag auf Sub-Minuten-/Sekunden-Skala
(Mikrostruktur-Preisführerschaft). IC-CLIM-2 testet eine strukturell andere Kausalkette: ein
Extremperzentil-EREIGNIS in einem Merkmal (Funding/OI, nicht Preis) triggert eine Regimeänderung Tage
später in einem ANDEREN Symbol — anderer Zeitmaßstab (Tage vs. Sekunden), andere Triggergröße (Ereignis
vs. kontinuierliche Preisführerschaft), kein Widerspruch zu H-04's Mess-Ergebnis.
Friktions-Rechnung: Bei einem erwarteten 1–5-Tage-Regimewechsel-Move von grob 2–6 % (konservativ kleiner
als IC-CLIM-1, da hier ein SEKUNDÄR-Effekt in Symbol B, nicht das primäre Vol-Regime) gegen 11–15 bps
Wand: Verhältnis ~13–55×. Deutlich über der Wand, aber die Ereigniszahl (s. o.) ist der eigentliche
Flaschenhals, nicht die Friktion.
Rechenaufwand: CPU (Perzentil-Schwellen + Permutationstest über ~100–1000 Tage × 5 Symbole — trivial).
Offene Punkte für data-feasibility-scout: (a) exakte Perzentil-Erreichbarkeit bei N≈100 Tagen
durchrechnen (analog GL-012: bei N=100 ist das 99. Perzentil im Basis-Fenster nur ~1 Beobachtung — zu
knapp für irgendeine Aussage, ggf. auf 90. Perzentil absenken müssen und das VOR dem Test fixieren, nicht
danach); (b) OI-30-Tage-Rolling-Caveat prüfen (Trigger-Definition auf OI-Δ könnte durch die
strukturelle Kürze der OI-Historie verzerrt sein).

---

### IC-CLIM-3 — Ensemble-Spread als Multi-Tage-Regime-Signal (Spread-Reliability-Slope)
Fachgebiet: Klimatologie/Meteorologie (Ensemble-Spread-Skill / SRS-Framework)
Kernfrage: Sagt die Streuung (Spread) der AnEn-Analog-Mitglieder aus IC-CLIM-1 eine höhere
Wahrscheinlichkeit einer großen realisierten Bewegung (Regimewechsel) im nachfolgenden 1–3-Tage-Fenster
voraus — geprüft nicht über die klassische lineare Spread-Skill-Korrelation, sondern über das schärfere
Spread-Reliability-Slope-Kriterium (trägt die Spread-Fluktuation NACHWEISLICH Information über den
Fehler, kontrolliert für Sampling-Rauschen)?
Erwogene Alternativen: klassische lineare Spread-Skill-Korrelation (Grimit & Mass 1998 / Whitaker-Loughe-
Tradition) **erwogen, als Baseline übernommen, aber NICHT als Hauptmetrik** — die neuere SRS-Verfeinerung
(2026) korrigiert genau den Fehler, den eine naive lineare Korrelation bei kleinem N (Sampling-Rauschen)
begeht, was bei unserem knappen ~100-Tage-Fenster besonders relevant ist; Brier Score auf ein binäres
"großer-Move-Ja/Nein"-Ereignis **erwogen, verworfen** — würde die kontinuierliche Spread-Information
unnötig binarisieren, bevor überhaupt eine kontinuierliche SRS-Prüfung versucht wurde.
Merkmalsvektor & Distanzmetrik: baut direkt auf IC-CLIM-1 auf — kein eigener neuer Merkmalsvektor, sondern
die Streuung (z. B. Interquartilsabstand oder Standardabweichung) der k=15–25 Analog-Mitglieder-
Folgeverteilung aus IC-CLIM-1 als abgeleitete Zielgröße; Distanzmetrik identisch zu IC-CLIM-1 (muss VOR
dem Test fixiert und mit IC-CLIM-1 identisch sein, keine getrennte Nachjustierung).
Datenbindung: identisch zu IC-CLIM-1 (Basis-Bestand 2026-03-27…heute, BTC/ETH zuerst) — **dieselbe
knapp/teilweise-data-gated-Einstufung**, da IC-CLIM-3 auf denselben ~100 Analog-Läufen aufsetzt und die
SRS-Schätzung selbst zusätzliches N für die Sampling-Rausch-Korrektur braucht (SRS ist per Konstruktion
darauf ausgelegt, bei kleinem N ehrlich "nicht reliable" statt falsch-positiv "reliable" zu melden — ein
struktureller Vorteil bei knapper Datenlage). Entsperr-Bedingung identisch zu IC-CLIM-1 (Deep-Backfill-
Coverage BTC/ETH).
Verifikationsmetrik: Spread-Reliability-Slope (Steigung von tatsächlichem Vorhersagefehler gegen
Ensemble-Spread-Quantile, korrigiert für Sampling-Fehler) statt naiver Pearson-Korrelation;
vorregistrierte Schwelle: SRS signifikant von 0 verschieden (Bootstrap-CI) auf ≥2 disjunkten Fenstern.
Nicht-Redundanz zu C-42/H-02/H-04: unterscheidet sich von C-42/H-02 dadurch, dass hier NICHT der
Punktschätzer-Fehler eines Einzelmodells getestet wird, sondern ob die BREITE der nichtparametrischen
Analog-Verteilung selbst Information trägt — eine Fragestellung, die in einem Einzelmodell-Regressionsrahmen
(wie C-42) gar nicht formulierbar ist, weil dort kein Ensemble-Spread existiert. Keine Überschneidung mit
H-04 (Preisführerschaft) oder H-05/H-05b (OFI-Vorzeichen).
Friktions-Rechnung: identische Größenordnung zu IC-CLIM-1 (~25–75× über der Wand für den 1–3-Tage-
Bewegungsschätzer), da IC-CLIM-3 dieselbe Zielgröße (künftige Bewegungsgröße) nur über ein anderes
Signal (Spread statt Verteilungs-Median) vorhersagt.
Rechenaufwand: CPU (Spread-Berechnung ist eine einfache Quantils-/Streuungsoperation über bereits
berechnete Analog-Ensembles aus IC-CLIM-1 — kein zusätzlicher Suchlauf nötig).
Offene Punkte für data-feasibility-scout: gleiche Coverage-Fragen wie IC-CLIM-1 (a)/(b); zusätzlich:
Mindest-N für eine belastbare SRS-Bootstrap-CI abschätzen (Literatur nennt i. d. R. deutlich mehr als
100 Fälle für robuste Sampling-Rausch-Korrektur) — falls N zu klein, IC-CLIM-3 explizit als PARK statt
WEITER kennzeichnen, bis Deep-Backfill greift.

---

## Cross-Domain-Hinweise (zusammengefasst)

- **BMA/Multi-Modell-Gewichtung** (Methodenrecherche Punkt 4): natürliche Erweiterung, aber strukturell
  näher an einer parametrischen Kombinationsfunktion (EM-geschätzte Gewichte) → Risiko, ins C-42/H-02-
  Territorium zurückzufallen. Für `mechanism-design` oder eine spätere ML-Welle als Idee vermerkt, nicht
  von mir umgesetzt.
- **Schaake Shuffle / Ensemble-Copula-Kopplung** (Punkt 5): Multi-Symbol-Abhängigkeitsstruktur zwischen
  gleichzeitig simulierten Analog-Ensembles — relevant, falls `network-topology` oder eine spätere
  Portfolio-Erweiterung mehrere Symbole gemeinsam (nicht nur paarweise) modellieren will.

## Selbstkill-Check (durchgeführt)
Alle drei IC-Vorschläge: Horizont 1–5 Tage (≥1 Tag erfüllt); alle nichtparametrisch (Analog-Auswahl bzw.
direkt aus Analog-Ensemble abgeleitete Streuungsmaße, keine global gefittete Parameterfunktion) — kein
Selbstkill-Kriterium ausgelöst.
