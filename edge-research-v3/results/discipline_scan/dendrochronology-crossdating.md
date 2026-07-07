# Fachgebiets-Scan — Dendrochronologie (Cross-Dating/Pointer-Year)

**Agent:** `dendrochronology-crossdating` | **Phase:** DISCIPLINE-SCAN | **Stand:** 2026-07-07

## Schritt 1 — Methodenrecherche (Pflicht, über den Werkzeugkasten der Agenten-Datei hinaus)

Recherchiert via WebSearch (Primärquellen: dplR-Dokumentation, pointRes-CRAN-Vignette, ScienceDirect/
Dendrochronologia-Artikel, sheppard.ltrr.arizona.edu COFECHA-Manual). Ergebnisse unten fließen in
`Erwogene Alternativen:` der IC-Vorschläge ein; hier die volle Fundstellen-Liste:

1. **Cropper-Normalisierung (1979), gleitendes Fenster** — bereits im Werkzeugkasten der Agenten-Datei;
   bestätigt: |C| > 0.75 SD in einem 13-Jahres-Fenster als Einzelserien-Ereignisschwelle, danach
   Prozentsatz der Bäume als Pointer-Year-Kriterium. **Übernommen** als Kernbaustein (angepasste
   Fensterbreite, siehe IC-DEND-1).
2. **Neuwirth-Methode / alternative Fensterbreiten** (in `pointRes` neben Cropper implementiert) — nutzt
   andere Fenster-/Schwellenkombination für dieselbe Grundidee. **Verworfen als Ersatz**, aber als
   Robustheits-Cross-Check aufgenommen (zwei unabhängige Standardisierungen, die dieselben Pointer-Tage
   finden müssen — reduziert Method-Choice-Bias, siehe Punkt 7 unten).
3. **COFECHA-Segment-Kreuzkorrelation** (überlappende 50-Jahr-Segmente, 25 Jahre Overlap) — bereits im
   Werkzeugkasten der Agenten-Datei skizziert; hier konkretisiert mit den Original-Parametern aus dem
   COFECHA-Manual. **Übernommen**, aber ausschließlich als Infrastruktur-/Datenqualitäts-Beitrag (IC-DEND-2),
   kein Alpha-Claim.
4. **Gleichläufigkeit / Gegenläufigkeit (GLK, Eckstein & Bauch 1969, korrigiert nach Visser 2021)** —
   paarweiser Vorzeichentest auf synchrone Jahr-zu-Jahr-Veränderung zwischen zwei Serien, mit
   geschlossener z-Score-Signifikanzformel (GLK = SGC + SSGC/2). **Übernommen** als methodisch schärfere
   Alternative zum reinen Schwellenwert-Prozentsatz für die Pointer-Tag-Aggregation (Nebenbaustein in
   IC-DEND-1, s.u.) — statt "X% der Serien überschreiten Schwelle Y" liefert GLK einen testbaren
   Signifikanz-Score pro Serienpaar, der sich zu einer Netzwerk-Synchronizität aggregieren lässt.
5. **Expressed Population Signal (EPS) / Signal-to-Noise Ratio (SNR)** aus der Chronologie-Qualitätsliteratur
   — EPS = n·r̄/(1+(n−1)·r̄), ursprünglich zur Beurteilung, wie viele Bäume nötig sind, damit eine
   Chronologie den "wahren" Klimasignal-Anteil zuverlässig abbildet (üblicher, umstrittener Richtwert
   0.85, siehe Buras 2017 "A comment on the Expressed Population Signal" — die Schwelle war ursprünglich
   für Subsample Signal Strength gedacht, nicht 1:1 übertragbar). **Übernommen** als Infrastruktur-Beitrag
   (IC-DEND-3): liefert `data-feasibility-scout` eine quantitative Mindest-Serienanzahl-Formel statt einer
   Bauchentscheidung.
6. **ARSTAN-artige robuste Chronologie-Mittelung (Biweight Robust Mean statt arithmetischem Mittel)** —
   reduziert den Einfluss einzelner Ausreißer-"Bäume" (hier: einzelner Symbole/Börsen mit Datenlücken oder
   Flash-Moves) auf die Referenz-Serie. **Verworfen als eigener IC**, aber als konkrete Implementierungs-
   Empfehlung in die Standardisierungsmethode von IC-DEND-1 eingearbeitet (robuste statt arithmetische
   Aggregation über die Serien beim Bilden der Pointer-Tag-Statistik).
7. **"Pointer years revisited: Does one method fit all?" (Dendrochronologia 2023) / "Towards the extremes:
   A critical analysis of pointer year detection methods" (2019)** — zeigen empirisch, dass verschiedene
   Pointer-Year-Methoden (Cropper vs. Neuwirth vs. absolute Schwellenwerte) auf denselben Daten
   unterschiedliche Jahre als "Pointer" markieren. **Nicht als eigener IC übernommen**, aber als
   Warnung eingebaut: IC-DEND-1 verlangt deshalb explizit Methoden-Fixierung VOR Datensicht (keine
   Nachträgliche Auswahl der Methode, die die meisten/saubersten Treffer liefert — sonst Data-Snooping
   über die Methodenwahl selbst, nicht nur über die Schwelle).
8. **Event Synchronization (Quian Quiroga et al., in Klimatologie/Neurowissenschaft für Klimanetzwerke
   verwendet)** — paarweise Ereignis-Synchronizität mit dynamischem Zeitfenster statt festem Kalendertag.
   **Verworfen für dieses Fachgebiet und als Cross-Domain-Hinweis weitergereicht** (s.u.) — das ist im
   Kern Netzwerktheorie/Graphenkonstruktion aus Ereigniszeiten, liegt näher an `network-topology`
   als an Cross-Dating.

## IC-Vorschläge

### IC-DEND-1 — Cross-Stream-Pointer-Day-Detektion + Pre-Event-Drift
Fachgebiet: Dendrochronologie (Cross-Dating/Pointer-Year)
Kernfrage: Zeigen an Tagen, die von ≥60% der verfügbaren Symbol×Stream-„Serien" gleichzeitig als
Cropper-Anomalie (gleiche Richtung) markiert werden („Pointer-Tag"), die 1–5 Handelstage DAVOR ein von
der Baseline abweichendes Verhalten in mind. einer nicht direkt an der Schwellenbildung beteiligten
Zielmetrik (z. B. Realized-Vol-Drift oder Funding-Rate-Krümmung)?
Erwogene Alternativen: siehe Schritt-1-Liste Punkte 1, 2, 4, 6, 7 oben (Cropper übernommen als
Kernmethode; Neuwirth-Fenster als Robustheits-Cross-Check; GLK als Alternative/Ergänzung zur reinen
Prozentschwelle für die Aggregation; Biweight-Robust-Mean statt arithmetischer Mittelung beim
Serien-Aggregat; Methodenwahl-Sensitivität aus den 2019/2023-Kritikpapieren als Grund für strikte
Vorab-Fixierung).
Standardisierungsmethode: Zweistufig, analog zum Dendro-Detrending: (1) Regimetrend-Entfernung je Serie
via 63-Tage-rollierendem Median (≈ "Baumalter/Marktzyklus"-Trend, ersetzt die negative Exponentialfunktion/
den kubischen Spline aus der Dendro-Literatur); (2) Cropper-artiger Anomalie-Score auf dem Residuum in
einem 11-Tage-Fenster (zentriert), Ausgabe als Z-analoger „Cropper-Wert" C_t je Serie und Tag.
Pointer-Schwellenwert: |C_t| ≥ 1.5 (Einzelserien-Ereignis, angepasst von Croppers 0.75-SD-Original wegen
kürzerer Historie/höherer Tagesvolatilität in Krypto vs. Jahresringen) UND ≥ 60% der an diesem Tag
verfügbaren Serien zeigen ein Ereignis in dieselbe Richtung → „Pointer-Tag". Beide Zahlen VOR jeder
Datensichtung fixiert, nicht verhandelbar nach Ergebnis-Vorschau.
Datenbindung: Basis-Bestand 2026-03-27…heute (~103 Tage, lt. DATASET.md, NICHT live verifiziert –
Audit-Dokument bestätigt keinen Manifest-Zugriff). „Serien" = Symbol×Stream-Kombinationen aus dem
5-Symbol-Paritäts-Kernbestand: je Symbol {Bybit-Trades(RV-Proxy), Bybit-Funding, Bybit-OI,
Binance-Trades(RV-Proxy), Binance-Funding, Binance-OI} = 30 Serien, plus für BTC/ETH zusätzlich
Deribit-book_summary und Deribit-dvol (2 weitere je Symbol) = bis zu 34 Serien. Das ist die zentrale
methodische Pointe dieses Vorschlags: Pointer-Year-Statistik braucht NICHT primär lange Historie, sondern
viele unabhängige Serien — die Serien-BREITE (34 Streams) ist im Basis-Bestand schon jetzt gegeben, auch
wenn die Serien-TIEFE (Jahre) fehlt. Dadurch ist die Kern-Pointer-Tag-Detektion **sofort testbar**, ohne auf
den Deep-Backfill zu warten. Live-only-Streams (Liquidationen, Insurance, L2) NICHT in die 34-Serien-Basis
aufgenommen (nur ~3 Wochen Historie, s. Audit-Inventar) — optional als zusätzliche Bestätigungs-Serien für
das Live-Fenster, aber nicht Teil der Kernschwelle.
Nicht-Redundanz zu C-08: C-08 (BOCPD) erkennt einen Strukturbruch in EINER Serie über die Zeit. Dieser
Vorschlag testet, ob VIELE unabhängige Serien an DEMSELBEN Tag synchron ein Ereignis zeigen — das
Kernobjekt ist die Tages-Spalte der Serien×Zeit-Matrix (Querschnitt), nicht eine Zeitreihen-Spalte. Ein
einzelnes Symbol/Stream allein kann diesen Vorschlag nicht auslösen; er ist strukturell nicht auf eine
Serie reduzierbar.
Typ: Alpha-Hypothese (capital_free)
Rechenaufwand: CPU (Detrending + Kreuzkorrelation über 34 Serien × ~103 Tage ist trivial)
Cross-Domain-Hinweis (optional): Die GLK-basierte paarweise Aggregation (Punkt 4 oben) UND die
Event-Synchronization-Methode aus Klimanetzwerken (Punkt 8) laufen beide auf eine Serien×Serien-
Synchronizitätsmatrix hinaus — das ist im Kern ein Netzwerkkonstruktions-Schritt. Sollte `network-topology`
bereits eine Korrelations-/Synchronizitäts-Netzwerk-Hypothese verfolgen, ist eine Deduplizierung in
DECONFLICT nötig (gleiche Matrix, andere Fragestellung: Netzwerktopologie fragt nach Struktur DER Matrix
selbst, dieser Vorschlag fragt nach Vorlauf-Verhalten VOR Extremtagen der Matrix-Diagonalen-Aggregation).
Offene Punkte für data-feasibility-scout: (a) exakte Serienanzahl pro Tag ist nicht konstant (Deribit nur
BTC/ETH, Live-Streams kürzer) — Schwellenprozentsatz muss ggf. auf verfügbare Serienzahl je Tag normiert
werden, nicht auf eine fixe Zahl 34; (b) bei ~103 Tagen und einer erwartbaren Pointer-Tag-Rate von
vielleicht 5–15% ergeben sich nur ~5–15 Pointer-Tage — für eine FDR-robuste Pre/Post-Signifikanzaussage
ist das eine kleine, aber nicht-triviale Stichprobe; **DATA-GATED für die robuste/finale Version**: Eine
belastbare Kalibrierung der 60%-Schwelle über mehrere Markt-Regime (Bull/Bear/Crash) verlangt die
BTC/ETH/BitMEX/Deribit-Tiefe aus dem laufenden Deep-Backfill (Ziel 2014–2026, mehrere Zyklen/Crashes,
lt. DATASET.md §5/§7). **Entsperr-Bedingung:** Manifest-Coverage-Check (DATASET.md §7-Query) bestätigt
`done_days` für mind. BTC/ETH/BitMEX zurück bis mind. 2019 (idealerweise 2014) — erst dann ist eine
Multi-Zyklen-Version dieses Vorschlags vorregistrierbar; bis dahin läuft nur die Basis-Bestand-Version
mit entsprechend niedrigerer Power.

### IC-DEND-2 — COFECHA-artige Cross-Exchange-Ausrichtungsprüfung (Infrastruktur)
Fachgebiet: Dendrochronologie (Cross-Dating, Datenqualitäts-Anwendung)
Kernfrage: Sind die Tages-Zeitstempel/Aggregationsgrenzen von Bybit-, Binance- und Deribit-Trades-Serien
im gemeinsamen Basis-Bestand-Fenster (BTC/ETH) korrekt zueinander ausgerichtet, oder gibt es einen
Off-by-one-Tag-Versatz bzw. stille Lücken, die downstream jede Cross-Exchange-Hypothese verfälschen würden?
Erwogene Alternativen: siehe Schritt-1 Punkt 3 (COFECHA-Original-Parametrisierung mit 50/25-Jahre-Segmenten
— hier auf 20/10-Tage-Segmente reskaliert, da nur ~103 Tage Basis-Bestand statt Jahrhunderte an
Jahresringen vorliegen); alternativ wurde ein reiner globaler Korrelationskoeffizient über das gesamte
Fenster erwogen und verworfen, weil er einen lokalen (z. B. einwöchigen) Versatz durch die lange
Mittelung verwässern würde — genau das Problem, das COFECHA durch Segmentierung löst.
Standardisierungsmethode: Wie IC-DEND-1 Schritt (1)+(2), aber Fenster auf Tagesbasis reskaliert:
20-Tage-Segmente mit 10-Tage-Overlap, Korrelation der hochfrequenten (detrendeten) Serie je Segment
zwischen Bybit-BTC- und Binance-BTC-Trades-Aktivität sowie Bybit-BTC vs. Deribit-BTC.
Pointer-Schwellenwert: entfällt (kein Alpha-Claim) — Prüfkriterium stattdessen: Segment-Korrelation < 0.5
in ≥2 aufeinanderfolgenden Segmenten löst einen Ausrichtungs-Alarm aus (Schwellenwert aus COFECHA-Praxis
übernommen, vorab fixiert).
Datenbindung: Basis-Bestand 2026-03-27…heute, BTC/ETH (einzige Symbole mit Bybit+Binance+Deribit-Parität).
Nicht-Redundanz zu C-08: Kein Alpha-Claim, daher gegenstandslos — reine Zeitachsen-Integritätsprüfung.
Typ: Infrastruktur-/Datenqualitäts-Beitrag (explizit KEIN Alpha-Claim — `critic` bitte nicht gegen
Novelty/Alpha-Dimension scoren, sondern als Voraussetzungs-Check für alle anderen Cross-Exchange-ICs werten)
Rechenaufwand: CPU
Offene Punkte für data-feasibility-scout: Ergebnis dieser Prüfung ist Voraussetzung für JEDE Hypothese
(auch außerhalb dieses Fachgebiets), die Bybit/Binance/Deribit-Serien tagesgenau gegeneinander verrechnet
— sollte daher priorisiert vor IC-DEND-1 der Multi-Zyklen-Version laufen.

### IC-DEND-3 — EPS/SNR-abgeleitete Mindest-Serienzahl-Formel (Infrastruktur)
Fachgebiet: Dendrochronologie (Chronologie-Qualitätsmaß, übertragen)
Kernfrage: Wie viele unabhängige Symbol×Stream-Serien sind mindestens nötig, damit die Pointer-Tag-Statistik
aus IC-DEND-1 ein stabiles, nicht rein zufälliges Synchronizitätssignal misst statt Rauschen?
Erwogene Alternativen: siehe Schritt-1 Punkt 5 (EPS-Formel n·r̄/(1+(n−1)·r̄) übernommen, aber der
konventionelle 0.85-Richtwert NICHT unkritisch übernommen — Buras (2017) zeigt, dass 0.85 ursprünglich
für Subsample Signal Strength gedacht war, nicht als generischer Reliability-Cutoff; deshalb hier als
sensitivitätsgeprüfter Vorschlag, nicht als hartes Kriterium); GLK-Signifikanztest (Punkt 4) als
alternative Formel erwogen und als Ergänzung (nicht Ersatz) aufgenommen, da GLK paarweise, EPS
populationsweit rechnet — beide zusammen ergeben ein robusteres Bild als jede Formel allein.
Standardisierungsmethode: r̄ = mittlere paarweise Korrelation der Cropper-Residuen (aus IC-DEND-1 Schritt 2)
über alle verfügbaren Serienpaare im Basis-Bestand-Fenster.
Pointer-Schwellenwert: entfällt (kein Alpha-Claim) — Ausgabe ist eine Kennzahl (EPS-Wert je Kandidaten-N),
kein Handelssignal.
Datenbindung: Basis-Bestand 2026-03-27…heute, alle bis zu 34 Serien aus IC-DEND-1.
Nicht-Redundanz zu C-08: Kein Alpha-Claim, daher gegenstandslos.
Typ: Infrastruktur-/methodischer Beitrag (explizit KEIN Alpha-Claim)
Rechenaufwand: CPU
Offene Punkte für data-feasibility-scout: Ergebnis (Mindest-N) direkt verwendbar, um IC-DEND-1s
60%-Schwelle bzw. die Interpretierbarkeit der Pointer-Tag-Rate gegen Zufallsrauschen abzusichern, bevor
`fable5-deep-validator` das Fenster hart macht.

## Selbstkill-Check (durchgeführt)
- Alle drei Vorschläge auf Reduzierbarkeit auf eine einzelne Serie geprüft: IC-DEND-1 erfordert
  strukturell die Serien×Zeit-Matrix (Querschnitt an einem Tag), nicht reduzierbar → kein C-08-Territorium,
  bleibt bei diesem Agenten. IC-DEND-2/3 sind ohnehin kein Alpha-Claim, daher nicht C-08-relevant.
- Pointer-Schwellenwert (60% / |C|≥1.5) und COFECHA-Alarmschwelle (<0.5 Korrelation) sind hier VOR jeder
  Datensichtung fixiert — kein Data-Snooping-Risiko über die Schwellenwahl selbst.
- Kein Berührungspunkt mit den sechs in CLAUDE.md §1 gesperrten Clustern (Seismologie/Statistische Physik,
  Informationstheorie/Nichtlineare Dynamik, Physiologie-nahe Signalverarbeitung, Radartechnik, Epidemiologie,
  sowie C-06/C-07/C-08/C-14 u.a. explizit REFUTED/DROP) — einziger berührter Nachbar ist die
  Event-Synchronization-Methode (Punkt 8), die explizit NICHT übernommen, sondern als Cross-Domain-Hinweis
  an `network-topology` weitergereicht wurde.
