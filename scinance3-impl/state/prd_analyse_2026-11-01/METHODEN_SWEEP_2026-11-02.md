# Methoden-Sweep 2026-11-02: Naturwissenschaft und Technik x Datenstroeme des Data-Harvest-Archivs x Horizonte

> Rolle: Herleitung (Grundsatzanalyst). Auftrag: `sweep/BRIEF_methoden_sweep.md` im Arbeitsverzeichnis der PRD-Analyse.
> Nur Lesearbeit im Repo und analytische Rechnung aus Akten-Zahlen; **keine Marktdaten geladen, kein Harvest-Client,
> keine Siegeldatei geoeffnet, keine Registrierung, kein Verdikt, nichts im Repo geaendert.** Rechenskript (nur Formeln):
> `scripts/sweep_calc.py` (sha256 ab4541f6...fa3ced), Ausgabe `sweep/calc/sweep_calc.out` (sha256 c668eef0...e15256).
>
> **Markierungen:** [F] Fakt aus der Akte (Fundstelle) - [R] eigene Rechnung (Skript-Abschnitt) - [U] Urteil -
> [V] Vermutung/Annahme ohne Fundstelle - [sek] Sekundaerbeleg aus dem Gedaechtnis der Herleitung, **ungeprueft, Primaerquelle
> zu beschaffen** (Netz gesperrt; Literatur ist unter Verfassung 3.1 Etikett, nicht Vorbedingung, DEC-104 E3 (b)).
> Literaturwerte stehen nur als Orientierung ("Groessenordnung"), nie als belegte Effektgroesse.
>
> **Gelesen:** PRD_ANALYSE_2026-11-01 (vollstaendig), KONZEPT_UND_FORSCHUNGSFELDER (vollstaendig), DATENINVENTAR_2026-11-01,
> EDGE_INVENTUR (vollstaendig), ERKENNTNIS_KOMPENDIUM (A-F), Verfassung 3.0 (Verfassungsdatei von scinance3-impl, mit dem Nachtrag DEC-104 vom
> 2026-11-02), PRD Par. 1-3, 9.1, 11, scinance2 PROGRAM_FINAL_REPORT, REGELN_UND_LESELISTE, **DEC-104 (Verfassung 3.1,
> vollstaendig)**, DEC-55/56/71/96 (Auszuege), KONTO_ZONE_X.md, ZENSUS_UNIVERSUM_UMSATZ_2026-10-29, Wissenschafts-Exkurs
> (Synthese; Rangfolgen und Ablehnungslisten S1-S5), Modulliste `src/bybit_edge/research/` und `_legacy_v1/layers/`.
>
> **Rahmen-Hinweis (wichtig).** Der Auftrag beschreibt Zone X als "Panel 2021-01..2024-06; BTC/ETH bis 2026-06 als
> agentenbekannte Aggregate". Die seit heute bindende DEC-104 E4 (a) definiert enger: **Zone X = alle Daten vor
> 2024-07-01**; W1/W2 (2024-07-01..2026-06-28) sind **Zone V** (blind fuer Klasse W und A2, ein Blick je Familie und
> Kohorte); Zone K = ab 2026-07-01; BTC/ETH-Aggregate sind **nur in Zone K prospektiv** konfirmierbar (E4 (i)). Dieser
> Sweep rechnet durchgehend mit DEC-104. Folge: W1/W2-BTC/ETH-Daten sind fuer Nicht-A2-Statistiken weder explorierbar
> noch konfirmierbar ("Brachland", Abschnitt 4.6) - das ist eine Programmfrage (N), keine Entscheidung dieses Sweeps.

---

## 0. Befund in Kuerze

1. [U] **Der Sweep findet kaum neue Praemienquellen, aber eine Reihe von Mess-, Kosten- und Nullwelt-Programmen, die
   unter Verfassung 3.1 auf dem kritischen Pfad liegen.** 37 Methodenfamilien in 13 Disziplingruppen (Abschnitt 1) gegen 13
   Stromgruppen (Abschnitt 2): die Familien, die auf unseren Daten etwas tragen, messen zweite Momente, Kosten,
   Skalengesetze, Abhaengigkeitsstrukturen und Datenqualitaet - nicht erste Momente (Mittelrenditen). Das ist kein
   Mangel der Methoden, sondern Arithmetik: [R, calc M] die Drift-SE von BTC ist nach 6,6 Jahren 19,5 % p.a.,
   **unabhaengig von der Abtastrate** (Merton 1980 [sek]); hohe Abtastrate kauft Praezision fuer Varianzen, Kosten und
   Strukturen (relative Varianz-SE 0,08 % auf 1-min gegen 2,9 % auf Tagen), nicht fuer Tagesmittel.
2. [F/U] **DEC-104 E3 macht die SESOI zur Kostenkurve** ("registriertes Kostenmodell als Kurve ueber Horizont und
   Signal-Persistenz", Default Taker). Diese Kurve existiert nicht: die Wand ist eine Konstante (11/15 bp), die
   Slippage "~4 bp ungemessen" (Kritik K-11), der Maker-Pfad ein Band 0,06..0,37 (DEC-71). Die Kostenkurven-Programme IK-01
   (Taker-Impact, Invarianz) und IK-02 (Maker-Queue) sind deshalb **Vorbedingung jeder 3.1-Registrierung**, nicht
   Beifang. [R, calc B] Beispiel Tages-Querschnitt: die Taker-SESOI bei vollem Tagesumschlag ist IC 0,0169, die
   Maker-SESOI 0,0062 - der Faktor 2,7 entscheidet, ob ein Querschnittsdesign testbar ist (Zone-V-MDE80 0,015..0,021).
3. [R, calc F] **Schwere Raender sind quantifizierbar und relevant.** Mit der Akten-Kurtosis 5..10 (r_pre, NUISANCE_SIGMA30/E-27; Merkposten 2,6 DEC-98 N5)
   und 40..52 Clustern sinken die effektiven Freiheitsgrade der SE auf 7..15; der kritische Wert zu alpha 0,0025 steigt
   von 2,807 auf 3,29..4,12, die MDE um Faktor 1,14..1,38. Eine Schiefe der Clusterstatistik von -0,5..-1 hebt das
   effektive einseitige alpha 0,0025 auf ~0,004..0,006 (Edgeworth, Groessenordnung). Bei 365 Clustern verschwinden die
   Effekte (MDE-Faktor <= 1,03). Das gilt fuer Tests mit geschaetzter SE und Normal-Kritik (Bootstrap-SE, gepoolte
   z-Tests); Permutationstests unter Austauschbarkeit (A2-Label-Permutation) halten alpha exakt, dort kosten schwere
   Raender nur Power. IK-04 misst die noetigen Momente und baut die minimale Nullwelt, die die OC (DEC-104 E0) vor
   Kohorte 1 braucht.
4. [R, calc E] **Der groesste ungepruefte Hebel der Klasse W (S-4) ist in Zone X entscheidbar.** Eine
   Faktorstruktur, die die 2,5-fache IC-Streuung (E-14) erklaert, braucht in der residualen Korrelationsmatrix einen
   Eigenwert >= 6,2 (bei voller Ausrichtung auf die Charakteristik; >= 11,5 bei halber) gegen eine Marchenko-Pastur-Kante
   von 1,95..2,64 bei T 1.277 Tagen und K 200..500. Gibt es solche Eigenwerte nicht, ist die Faktor-Erklaerung falsch
   und die Streuung kommt aus Zeitvariation/Heteroskedastizitaet (IK-04). IK-05 instrumentiert S-4 mit RMT.
5. [U] **Elf Ideenkarten** (Abschnitt 3): neun Messprogramme (IK-01..IK-08 und die Reservekarte IK-11
   Funding-Regelkreis, deren Abgrenzung zu A1 und X-NEXP-1 offen ist) und zwei Hypothesen (IK-09 Delisting-Hazard,
   IK-10 verzoegerte Marktreaktion im Querschnitt). **Sechs sind innerhalb von 12 Monaten konfirmierbar** (IK-01, IK-02, IK-06 Teil b, IK-07, IK-09, IK-10):
   Zone-V-Blick in Kohorte 1 (Q1 2027) oder Zone-K-Fenster 2026-07..2027-06 mit letztem Blick Anfang Juli 2027 (wo
   K-Monate schon fuer dieselbe Statistik geoeffnet wurden - H-24 bis 2026-07, WP-10(B) bis 2026-09 - spaeter, bis 10/2027). Den
   zwoelften Platz lasse ich frei: die Kandidaten dafuer waren duenn (Abschnitte 3.12 und 5).
6. [R, calc B] **Der einzige neue Querschnittskandidat (IK-10) liegt genau an der Kante:** Zone V (W1+W2 gepoolt bei
   alpha 0,0025 plus REZENZ-Screen auf W2, gemeinsame Power 0,80) loest IC 0,0148 / 0,0162 / 0,0209 bei K 600/500/300
   auf, gegen die Taker-SESOI 0,0169; Zone K allein (12 Monate) nur 0,020..0,028 - dort strukturell nicht testbar.
7. [F/R] **Grosse Daten konkret** (Abschnitt 4): ganze Stroeme kosten 43 h (Trades), 52 h (L2), 54 h (Optionskette)
   Transfer bei 2 MB/s; die vorgeschlagenen Stichproben ~20 GB (IK-01, 2,7 h), ~34 GB (IK-02, 4,7 h, Nutzer-PC),
   ~51 GB (IK-06, 7,1 h, erst nach Inhaltsprobe). Die Tardis-Kette ist mit 58 Mio Zeilen je Stichtag [R] kein
   Monatsschnappschuss, sondern ein Intraday-Kettenstrom an 63 Zone-X-Tagen (Inhalt UNBELEGT bis C.8-Probe) - daraus
   folgt eine **implizite Basis-Terminstruktur seit 2019** (F10-Einstiegsbasis) mit +-1..6 bp p.a. Genauigkeit [R, calc L].
8. [U] **Groesste Luecke der Felderliste F1..F12:** die Felder sind im Kern Erst-Moment-Hypothesen (IC, CAR,
   Praemie), deren Feasibility auf ungemessenen Zweit-Moment- und Kosteneingaben ruht (SD-Faktor 2,5 [V], Alt-Vol 650 bp
   [V], Wand als Konstante, Normalnaeherung). Nur F4 enthaelt eine Invarianz (Kyle-lambda auf Tagesskala) und F9 eine
   Verteilungsmessung (im Siegel); kein Feld misst Kosten, Nullwelt-Momente oder Datenfehler, und die 1,07 TB
   Trades/L2/Kette (309 + 377 + 387 GB [F]) werden nur als Tagesaggregat (F4) oder im Siegel (F8/F9) beruehrt - nicht
   dort, wo sie einen komparativen Vorteil haben.
9. [U] **Was ich nicht beurteilen kann:** die Streuungs-Nuisance aller neuen Groessen (ueberall [V], in Zone X zu messen),
   den Feldinhalt der Tardis-Kette, ob `kline1d` eine Tradezahl fuehrt, ob Index-/Mark-Kerzen delisteter Perps
   nachladbar sind, ob Bybit-L3 oeffentlich existiert, und ob die Literaturwerte stimmen ([sek]).

---

## 1. Methodenkatalog (37 Familien, nach Disziplin)

Spalten: was die Familie misst; Voraussetzungen; Beispiel Finanzliteratur [sek, zu beschaffen]; Anwendbarkeit auf
unsere Stroeme; Stand im Programm (Fundstelle); Zone unter DEC-104 (X sofort / V ein Blick / K nach Registrierung /
tot nach D.x / unter Wand nur Messung). "Karte" verweist auf Abschnitt 3.

### 1.1 Physik / Statistische Mechanik

| Nr | Familie | misst | Voraussetzungen | Finanzliteratur [sek] | Anwendbarkeit | Stand im Programm | Zone |
|---|---|---|---|---|---|---|---|
| M01 | Skalengesetze, Aggregations-Normalitaet (Varianz-Zeit, Kurtosis-Zerfall, Signaturplot) | wie Verteilung und Abhaengigkeit mit dem Horizont skalieren | lange, dichte Reihen; Rauschmodell fuer kleine Skalen | Mantegna/Stanley 1995 (Nature); Cont 2001 (QF, stilisierte Fakten) | kline1m, Trades, kline1d ALL | fehlt (T-6); 48-Slot-Profil als Beifang | X sofort -> Karte IK-04 |
| M02 | Mikrostruktur-Invarianz (Kyle-Obizhaeva) | Skalierung von Wett-Ankunftsrate und -groesse mit Handelsaktivitaet W = P V sigma (Exponenten 2/3, -2/3) | Trades mit Groesse; Vol und Umsatz je Tag | Kyle/Obizhaeva 2016 (Econometrica) | Trades 5 Symbole; Querschnitt nur mit Tradezahl aller Perps | fehlt; Legacy `m25_kyle_lambda` (1.0, nie validiert) | X sofort -> IK-01 |
| M03 | Konkaver Preisimpact (Quadratwurzelgesetz, aggregierter Impact) | Impact als Funktion von Q/V und Horizont | signierter Fluss; fuer Metaorders eigentlich Orderkennung | Toth et al. 2011 (PRX); Patzelt/Bouchaud 2018 (PRE); Bouchaud et al. 2018 (Buch) | Trades, L2 BTC/ETH | gleichzeitiger IC +0,53..0,61, permanent (B.14) | X sofort / unter Wand nur Messung -> IK-01 |
| M04 | Multifraktalitaet, Multifraktaler Random Walk (MRW) | Intermittenz, Skalenexponenten; MRW als Generator mit 3 Parametern | lange Reihen; Strukturfunktionen nur als Diagnostik | Bacry/Delour/Muzy 2001 (PRE); Kantelhardt 2002 (MFDFA) | kline1m, Trades, kline1d | Legacy `m10_mfdfa` (1.0); Strukturfunktionen als Gate verworfen (Exkurs S3) | X sofort, nur als Nullwelt -> IK-04 |
| M05 | Warteschlangenmodelle des Orderbuchs (Poisson-, queue-reaktiv) | Intensitaeten von Limit/Market/Storno je Level -> Fill-Wahrscheinlichkeit, Resilienz | L2 mit Deltas; Queue-Position nur mit L3 identifiziert | Cont/Stoikov/Talreja 2010 (OR); Huang/Lehalle/Rosenbaum 2015 (JASA) | L2 BTC/ETH 2023-01..2024-06 | WP-10(B) Schattenmessung 2026-06..09 (DEC-71) | X sofort / nur Messung -> IK-02 |
| M06 | Omori-/Nachbebengesetze | Relaxation nach Schocks (Potenzgesetz) | Schockdefinition vorab | Lillo/Mantegna 2003 (PRE); Petersen et al. 2010 (PRE) | kline1m, Trades, DVOL, Liquidationen | **gemessen**: Exponent 0,23..0,32, Halbwertszeit 22..31 h (WP-11, DEC-63, E-24) | erledigt (Preise); Liquidationen = F9 (Siegel) |
| M07 | Zufallsmatrixtheorie (RMT) | Signal-Eigenwerte gegen Rauschband; Faktorzahl; Eigenvektor-Stabilitaet | T > K; Korrektur fuer schwere Raender | Laloux et al. 1999 (PRL); Plerou et al. 2002 (PRE); Biroli/Bouchaud/Potters 2007 | kline1d ALL (K 200..600) | Kreuzboersen-RMT tot (H-12, D.10); Panel nie | X sofort -> IK-05 |
| M08 | Fluktuationsskalierung (Taylor-Gesetz) | Varianz-Mittelwert-Skalierung der Aktivitaet ueber Assets | viele Assets, Aktivitaetsreihen | Eisler/Bartos/Kertesz 2008 (Adv. Phys.) | kline1d-Umsatz, Trades | fehlt | X sofort, Teil von IK-01/IK-07 |

### 1.2 Punktprozesse, Geophysik

| Nr | Familie | misst | Voraussetzungen | Finanzliteratur [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M09 | Hawkes / Verzweigung (Endogenitaet) | Anteil selbst-erregter Ereignisse | Ereigniszeitstempel; Kernwahl; Erreichbarkeit jeder Schwelle (D.2) | Filimonov/Sornette 2012 (PRE); Hardiman/Bercot/Bouchaud 2013 (EPJB) | Trades, Liquidationen | C-14 REFUTED (Schwelle 0,85, rho ~2e-7), Legacy `m14_hawkes` | unter Wand, nur Messung; Schwellen tot (D.2) |
| M10 | Ereigniszeit / Subordination (Volumen-, Vol-, Trade-Uhr) | Renditen in Aktivitaetszeit; Informationsgehalt je Kalenderfenster | Aktivitaetsmass je Intervall | Clark 1973 (Econometrica); Ane/Geman 2000 (JF) | Trades, kline1m, kline1d | fehlt (T-6); A2-Akte: Faktor 2,3 Streuung 2021 gegen 2023 | X sofort -> IK-04 |
| M11 | Gutenberg-Richter / ETAS (Groessenverteilung, Nachbeben-Kaskaden) | Groessenexponent, Kaskadenstruktur | Ereigniskatalog | Ogata 1988 (JASA, ETAS) | Trade-Groessen; Liquidationen (Siegel) | C-15 SUSPECT, nie ausgeloest; Legacy `m15_gr_omori` | Trades: X (in IK-01 als Groessenverteilung); Liquidationen K |

### 1.3 Extremwerttheorie

| Nr | Familie | misst | Voraussetzungen | Finanzliteratur [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M12 | GPD-Raender, Tail-Index (Hill, POT) | Randexponent, Quantile jenseits der Daten | Schwellenwahl vorab; Abhaengigkeit (Declustering) | Gopikrishnan et al. 1998 (EPJB, "inverse cubic"); McNeil/Frey 2000 (JEF) | kline1d ALL, kline1m, Trades, Optionskette (risikoneutral) | H-13 (2.0) gesperrt; H-20 Tail-Aftermath tot (D.12) | X sofort als Nuisance (IK-04); als Signal D.12 |
| M13 | Rekordstatistik | Rekordrate gegen iid-Erwartung (log n) als Stationaritaetstest | lange Reihen | Wergen 2013 (J. Phys. A, Uebersicht) | kline1d, kline1m | fehlt | X, aber verworfen (Abschnitt 5) |

### 1.4 Informationstheorie

| Nr | Familie | misst | Voraussetzungen | Finanzliteratur [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M14 | Transfer-Entropie, Mutual Information | gerichtete/nichtlineare Abhaengigkeit | viele Punkte (Schaetzer-Bias); Surrogate | Schreiber 2000 (PRL); Dimpfl/Peter 2013 (SNDE) | Sekunden: erledigt; Tage: 2.000 Punkte | H-04 WEITER (Sekunden, tot fuer Handel); Tage = F7 | Tage X, aber F7 / IK-10 bevorzugt |
| M15 | Kompressions- und Entropiemasse (LZ, Permutationsentropie) | Vorhersagbarkeit/Effizienz einer Symbolfolge | Diskretisierung vorab | Bandt/Pompe 2002 (PRL); Giglio et al. 2008 (EPL) [zu pruefen] | Trades, kline1m | H-06 PE tot (D.6); CS-02 Entropie-Momentum tot (D.3); Legacy `m6`/`m7`/`m17` | tot als Signal (D.3, D.6); Messung ohne Entscheidungswert |

### 1.5 Signalverarbeitung

| Nr | Familie | misst | Voraussetzungen | Finanzliteratur [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M16 | Spektren, Periodizitaet (Lomb-Scargle, Epoch-Folding) | Perioden, Saisonalitaet | Perioden meist kalendarisch bekannt | - | kline1m, Funding, Optionen | Exkurs X-ASTRO-3 verworfen; 48-Slot-Profil vorhanden | Diagnostik; gerichtet unter Wand (Exkurs S3 Nr. 3) |
| M17 | Wavelets (Kohaerenz, Multiskalen) | skalenabhaengige Kopplung | lange Reihen | Gencay et al. 2002 (Buch) | Sekunden erledigt | H-04 WCOH; Legacy `m4_wavelet` | X, ohne Zusatznutzen auf Tagen (Abschnitt 5) |
| M18 | Zustandsraum / Kalman (latenter effizienter Preis, Rauschvarianz, Filter) | latente Groessen, Messrauschen | Modellspezifikation vorab | Hasbrouck 1993 (RFS); Ait-Sahalia/Mykland/Zhang 2005 (RFS) | Trades, Funding-Premium, impliziter Forward | Legacy `m24_kalman_premium`; HF-RV fuer VRP ohne Gewinn (DEC-98 N5) | X sofort (in IK-04, IK-06, IK-11) |
| M19 | Matched Filter / Ereignis-Templates | bekannte Form im Rauschen | Template vorab | - | Verfallsfenster | Exkurs X-ASTRO-2 (A2-Nachbarschaft) | nicht aufgenommen (Exkurs) |

### 1.6 Netzwerkwissenschaft

| Nr | Familie | misst | Voraussetzungen | Finanzliteratur [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M20 | Lead-Lag-Graphen ueber Assets (Price Delay, Granger-Netze) | verzoegerte Informationsdiffusion | synchrone Schlusskurse; Stale-Kontrolle | Hou/Moskowitz 2005 (RFS); Lo/MacKinlay 1990 (RFS); Billio et al. 2012 (JFE) | kline1d ALL (Tag) | Sekunden: H-04, H-14 (D.11); Tag/Assets nie | X sofort, V in Kohorte 1 -> IK-10 |
| M21 | Zentralitaet, MST, Community-Drift | Clusterstruktur und ihre zeitliche Drift | Korrelationsschaetzung, Stabilitaet | Mantegna 1999 (EPJB); Onnela et al. 2003 (PRE) | kline1d ALL, Funding | fehlt | X sofort (Teil von IK-05; Regimevariable fuer F11) |

### 1.7 Regelungstechnik, Zuverlaessigkeit

| Nr | Familie | misst | Voraussetzungen | Finanzliteratur [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M22 | Systemidentifikation von Regelkreisen (Impulsantwort, Zeitkonstante, Verstaerkung) | Rueckkopplung Premium -> Funding -> Arbitragekapital | Eingangs- und Ausgangsgroesse; Zensierung an der Klemme | He/Manela/Ross/von Wachter 2022 (Perpetual Futures); Ljung (Lehrbuch) | Funding aller Perps; Index-Preis fehlt | Exkurs X-NEXP-1 (RKD an der Klemme) parkiert | X teilweise; Rest Daten fehlen -> IK-11 |
| M23 | Abtastregelung mit Stellkosten (diskretes Delta-Hedging, Leland) | Kosten und Fehler eines Hedges als Funktion des Abtastintervalls | Pfade mit feiner Aufloesung | Leland 1985 (JF); Hoggard/Whalley/Wilmott 1994; Bertsimas/Kogan/Lo 2000 (JFE) | kline1m, Trades, Optionskette | fehlt ("Delta-Hedge zahlt die Wand je Rehedge", R-2, ohne Zahl) | X sofort -> IK-03 |
| M24 | Zuverlaessigkeit, Ausfallbudgets, Verfuegbarkeit | Ausfallraten, gemeinsame Ursachen | Katalog, Luecken | Lehrbuch Zuverlaessigkeitstechnik | alle Stroeme (S0, auch im Siegel) | 14-Tage-Muster der Live-Stroeme (Review-Luecke 4), DEC-71 (4) | X/S0 sofort -> IK-08 |
| M25 | Kalibrierung von Vorhersagen (Reliability, PIT) | stimmen vorhergesagte SE/MDE mit realisierten ueberein? | Buch der Prognosen | Gneiting/Raftery 2007 (JASA) | Akte (Feasibility-Prognosen gegen Laeufe) | GL-035: reale IC-Streuung 2,3..2,6x der Null = Kalibrierfehler | X sofort -> IK-08 |

### 1.8 Metrologie

| Nr | Familie | misst | Voraussetzungen | Finanzliteratur / Fachquelle [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M26 | Unsicherheitsbudget (Typ A/B), systematische Fehler | getrennte statistische und systematische Unsicherheit je Konstante | Liste der Fehlerquellen | JCGM 100:2008 (GUM) | jede Konstante (p_fill-Band 0,06..0,37 ist ein Typ-B-Fehler) | fehlt als Form | X sofort -> IK-08 |
| M27 | Blindanalyse | Schutz vor Analytiker-Bias | Siegel, Lockbox | Klein/Roodman 2005 (Annu. Rev.) | alle | realisiert (DEC-96 E3; Lockbox F6) | realisiert |
| M28 | Look-elsewhere / Trials-Faktor | Selektionsdeflation | diskretes K oder Kontinuum | Gross/Vitells 2010 (EPJC) | Varianten-Scans | DEC-51 (4) E[max z]; Upcrossings verworfen (Exkurs X-ASTRO-4) | realisiert (diskret) |
| M29 | Obere Grenzen, CLs, Feldman-Cousins | Ausschlussgrenzen, Intervalle fuer beschraenkte Parameter | Modell der Teststatistik | Read 2002 (J. Phys. G); Feldman/Cousins 1998 (PRD) | jede Messung; FC fuer Varianzverhaeltnisse, Hazard-Ratios | DEC-104 E1 (Pflichtausgabe) | sofort (Berichtsform) |

### 1.9 Klinische Studienmethodik

| Nr | Familie | misst / leistet | Voraussetzungen | Fachquelle [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M30 | Gruppensequentiell, Futility, SESOI, Aequivalenz (TOST) | fruehes Ende, Ausschluss, Gesetzestests ("Exponent liegt in [a, b]") | Spending-Plan vorab | Jennison/Turnbull 2000; Schuirmann 1987; Lakens 2017 | jede K-Konfirmation; TOST fuer Invarianzgesetze (IK-01, IK-02, IK-07) | GSD/Futility/SESOI in DEC-104; TOST fehlt | K nach Registrierung |
| M31 | Adaptive Enrichment, Master-/Plattform-Protokolle, Assurance, dynamisches Borrowing | Subpopulationswahl am Zwischenblick; geteilte Kontrolle; Prior aus Vordaten mit Abschlag | vorab fixierte Regeln | Simon/Simon 2013 (Biostatistics); Woodcock/LaVange 2017 (NEJM); O'Hagan et al. 2005; Hobbs et al. 2011 (Biometrics) | Kohorten = Plattform; Enrichment fuer Querschnitt (illiquide Dezile); Borrowing Zone X -> K | Assurance in DEC-104 E7 (b); Rest fehlt | K (Design), Nutzerfrage fuer Enrichment |

### 1.10 Epidemiologie, Demografie, Survival

| Nr | Familie | misst | Voraussetzungen | Fachquelle [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M32 | Cox, Fine-Gray, IPCW (konkurrierende Risiken) | Hazard und seine Kovariaten; Zensierungskorrektur | Ereignisregister, Risikomenge | Fine/Gray 1999 (JASA); Robins/Finkelstein 2000 | Delisting-Register, Fill-Zeiten, Funding-Regime | X-SURV-1/2/3 (DEC-58 E1, deskriptiv) | X sofort, K/V -> IK-09 |
| M33 | Alters-Perioden-Kohorten (APC) | Trennung von Alter seit Listung, Kalenderperiode, Listungskohorte | Identifikationsrestriktion (a + c = p) | Holford 1983 (Biometrics); Yang/Land 2013 (Buch) | kline1d ALL, Funding, Register | fehlt; 8-Wochen-Regel unterstellt (E-32) | X sofort, V/K -> IK-07 |

### 1.11 Kausalinferenz mit natuerlichen Experimenten

| Nr | Familie | misst | Voraussetzungen | Fachquelle [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M34 | RD/RKD, DiD, IV, synthetische Kontrolle an Regelaenderungen (Funding-Kappe/-Klemme, Auto-Switch, Tick-Size, Gebuehren, Wartung, Kontraktumstellung, Listung) | kausale Wirkung einer Regel | exogene Zuweisung, Kontrollgruppe, N_cluster | Imbens/Angrist 1994; Abadie et al. 2010 (JASA) | Funding (Kappe/Klemme), Register; Kontrolle Binance fehlt | Exkurs S4 X-NEXP-1..4: parkiert/verworfen; R-7 | Funding: K nach V-1; DiD mit Binance: tot (D.16, Daten fehlen) |

### 1.12 Oekologie

| Nr | Familie | misst | Voraussetzungen | Fachquelle [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M35 | Capture-Recapture; Diversitaetsindizes; Fruehwarnsignale | verdeckte Populationen (Liquiditaet); Konzentration; kritische Uebergaenge | zwei unabhaengige "Fangmethoden" | Chao 1987 (Biometrics); Hill 1973; Scheffer et al. 2009 (Nature) | Trades gegen L2 (RPI verdeckt); Umsatzkonzentration | Fruehwarnsignale verworfen (Exkurs S2); C-40 RPI PARK | verworfen bzw. nur Messung (Abschnitt 5) |

### 1.13 Maschinelles Lernen und Robuste Statistik

| Nr | Familie | misst / leistet | Voraussetzungen | Fachquelle [sek] | Anwendbarkeit | Stand | Zone |
|---|---|---|---|---|---|---|---|
| M36a | ML: verschachtelte CV, Repraesentationslernen, Anomalie-Erkennung; TDA, RQA | Exploration nichtlinearer Struktur; Datenfehler finden | Konto, K im Selektionsbuch; GPU-Default 0 (DEC-57) | Dwork et al. 2015 (Science, wiederverwendbarer Holdout) | Zone X; Anomalie-Erkennung fuer IK-08 | H-15 WEITER ohne Bruecke (DAY-BRIDGE nie registriert); Legacy `m11_tda`, `m12_rqa`, `m18`/`m19` | X nur Exploration; als Registrierungsweg D.16-nah |
| M36b | Robuste Statistik, Rang-/Permutationstests (M-Schaetzer, Theil-Sen, Median-of-means) | Schaetzer mit beschraenktem Einfluss schwerer Raender | Symmetrie-/Austauschbarkeitsannahmen pruefen | Huber 1964; Theil 1950 / Sen 1968 | Standard in allen Karten | Permutations-Identitaet K-3 (Varianz 1/(K-1)) als Lehre | X sofort (Standard) |

Zaehlung: 37 Familien (M01..M35, M36a, M36b); die Klinik-, Metrologie- und Oekologiezeilen buendeln je mehrere
Verfahren, die zusammen angewendet oder zusammen verworfen werden. Davon tragen auf unseren Daten **neue Programme**: M01,
M02, M03, M04, M05, M07, M10, M12 (als Nuisance), M18, M20, M22, M23, M24, M25, M26, M30 (TOST), M32, M33.

---

## 2. Matrix Methode x Datenstrom x Horizont

**Spalten (Stromgruppen, Zone-X-Anteil nach DEC-104 E4 (a), Inventar 2026-11-01 [F]):**
P1d = Tages-OHLCV-Panel `rest.kline1d` ALL (X 2021-01-01..2024-06-30 = 1.277 Tage; V W1/W2; K ab 2026-07-01) -
m1 = 1-min BTC/ETH `rest.kline1m` (X BTC ab 2020-03-25, ETH ab 2021-03-15) - FR = Funding aller Perps `fundingRateAll`
(X ab 2021-01) - OI = Open Interest (BTC/ETH ab 2024-03 -> nur 122 Tage in X; 5 Symbole ab 2026-03; Binance ab 2026-05)
- TR = Trades `bybit/publicTrade` 5 Symbole (X BTC 2020-03.., ETH 2020-10.., XRP 2021-05.., SOL/BNB 2021-06..) -
L2 = Orderbuecher Bybit BTC/ETH (X 2023-01-18..2024-06, Abdeckung 74 % / 41 % [F F.1]; Alts erst ab 2026-06-24 = K) -
OC = Optionskette `tardis/options_chain` (63 Stichtage X, 24 V, 4 K) - OT = Options-Ticker/Greeks/Markprice ab
2026-06-16 (praktisch nur K) - DV = DVOL (X 2021-03-24..) - SD = Settlements/Delivery (Deribit BTC ab 2017-05, ETH ab
2019-03; Bybit deliveryPrice ab 2021-06) - LQ = Liquidationen/Insurance ab 2026-06-16 (K) - REG = Delisting-/Listing-
Register (306 Delistungen, 268 Ankuendigungen, instruments ab 2026-10-20) - XV = Binance/Bitmex/Deribit-Trades
(fruehester Tag 2025-01-01: **keine Zone-X-Daten**).

**Zellwerte:** X = X jetzt (Exploration mit Konto, Schaetzer/CI/Ausschlussgrenze) - V = ein Zone-V-Blick (W1/W2) in
einer Kohorte, nur fuer Nicht-BTC/ETH-Aggregate und Panel-Querschnitte - K = K prospektiv (ab 2026-07-01, nach
Registrierung in einer Kohorte, gruppensequentiell) - S0 = bis zur Registrierung nur Zaehlung - DF = Daten fehlen -
T(D.n) = tot nach Kompendium D.n - M = unter der Wand, nur Messung (Kosten/Struktur, nie Kandidat) - F# = bereits
Forschungsfeld F# der PRD-Analyse - erl. = in der Akte gemessen - "-" = keine sinnvolle Anwendung. Ziffern in
Klammern verweisen auf die Begruendungen unter der Tabelle. **Horizont** in der letzten Spalte.

| Familie | P1d | m1 | FR | OI | TR | L2 | OC | OT | DV | SD | LQ | REG | XV | Horizont |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M01 Skalengesetze | X | X | X | DF(1) | X | X/M | X | K | X | - | K | - | K(2) | 1 min..4 Wo |
| M02 KO-Invarianz | X/DF(3) | - | - | - | X | X | - | - | - | - | K | - | K(2) | Tag (Intraday-Aggregat) |
| M03 Impact | F4 | - | - | - | X/M | X/M | - | - | - | - | K/M | - | K/M | s..Tag |
| M04 MRW/Multifraktal | X(4) | X(4) | - | - | X(4) | - | - | - | X | - | - | - | - | min..Wo |
| M05 Warteschlangen | - | - | - | - | X/M(5) | X/M | - | K/M | - | - | - | - | K/M | s..min |
| M06 Omori | X | erl.(6) | X | DF | erl./M | X/M | - | K | X(7) | - | F9/K | - | K | h..Tage |
| M07 RMT | X | - | X | - | - | - | X(8) | K | - | - | - | - | T(D.10) | Tag/Wo |
| M08 Taylor-Skalierung | X | - | - | - | X | - | - | - | - | - | - | - | K | Tag |
| M09 Hawkes | - | - | - | - | M(9) | M | - | - | - | - | F9/T(D.2) | X(10) | K/M | s..h |
| M10 Ereigniszeit | X | X | - | - | X | - | - | - | - | - | K | - | K | Intraday..Wo |
| M11 GR/ETAS | - | - | - | - | X (Groessen) | - | - | - | - | - | F9/K | - | - | Ereignis |
| M12 EVT/Tail-Index | X | X | X(11) | - | X | - | X(12) | K | X | - | K | - | K | Tag..Monat |
| M13 Rekorde | X(13) | X(13) | - | - | - | - | - | - | - | - | - | - | - | Tag |
| M14 TE/MI | X(14) | erl./M | F2 | F3 | erl./T(D.11) | - | - | K | X | - | K | - | F7 | Tag |
| M15 Kompression/Entropie | X(15) | T(D.6) | - | - | T(D.3) | - | - | - | - | - | - | - | - | s..Tag |
| M16 Spektral/Periodizitaet | X(16) | erl./M | X | - | T(D.4) | M | - | K | X | - | K | - | K | min..Wo |
| M17 Wavelets | X(17) | erl. | - | - | erl. | - | - | - | - | - | - | - | - | s..Tag |
| M18 Zustandsraum/Kalman | X | X | X | - | X | X | X | K | X | X | - | - | K | s..Wo |
| M19 Matched Filter | - | A2(18) | - | - | A2(18) | - | - | - | - | A2 | - | - | - | 30 min |
| M20 Lead-Lag Assets | X->V(19) | erl./M | X | - | T(D.11)/M | - | - | - | X | - | - | - | F7 | Tag |
| M21 Community-Drift | X | - | X | - | - | - | - | - | - | - | - | - | - | Wo..Quartal |
| M22 Systemidentifikation | X/DF(20) | - | X | X(122 d) | - | - | X(21) | - | - | X | - | - | K | 8 h..Wo |
| M23 Leland/Abtastregelung | - | X | - | - | X | X | X | K | X | X | - | - | - | 1 min..1 Tag |
| M24 Zuverlaessigkeit | X/S0 | X/S0 | X/S0 | X/S0 | X/S0 | X/S0 | X/S0 | S0 | X/S0 | X/S0 | S0 | X/S0 | S0 | - |
| M25 Kalibrierung eig. Prognosen | Akte(22) | | | | | | | | | | | | | - |
| M26-M29 Metrologie | Berichtsform fuer alle Spalten (23) | | | | | | | | | | | | | - |
| M30-M31 Klinik-Designs | K fuer alle Spalten (24) | | | | | | | | | | | | | - |
| M32 Survival/IPCW | X->V/K | - | X(25) | - | - | X(26) | - | - | - | - | K | X->K | - | Tage..Monate |
| M33 APC | X->V/K | - | X | DF | - | - | - | - | - | - | - | X | - | Wochen..Jahre |
| M34 Natuerliche Experimente | F5 / T(D.16)(27) | - | K(28) | - | X(29) | - | - | - | - | A2(30) | K | F5 | DF(31) | Tag..Wo |
| M35 Capture-Recapture/EWS | T(Exkurs)(32) | T(Exkurs) | - | - | M(33) | M(33) | - | - | - | - | - | - | - | - |
| M36a ML | X(34) | X | X | - | X(35) | X(36) | X | K | X | - | K | - | K | alle |
| M36b Robuste Statistik | X | X | X | X | X | X | X | K | X | X | K | X | K | alle |

**Begruendungen der nicht-trivialen Zellen:**
1. OI BTC/ETH beginnt 2024-03-01; in Zone X liegen nur 2024-03-01..06-30 (122 Tage) [R aus Inventar]; Alts ab 2026-03
   (nur V/K). Die OI-Historie aller Perps ist der bestehende Datenauftrag 4 der PRD-Analyse.
2. Kreuzvenue-Trades beginnen 2025-01-01 (Binance BTC), 2025-08-01 (Deribit), 2026-03 (Bitmex, Binance Alts) [F] -
   keine Zone-X-Daten; Zone V nur fuer Nicht-BTC/ETH-Aggregate, also praktisch nur S0 bis Zone K.
3. Das Panel traegt Umsatz und Vol, aber nach meiner Kenntnis keine Tradezahl je Tag [V, Feldliste nicht geprueft]; die
   Querschnittsform der Invarianz braucht sie (Datenauftrag 3). Ein KO-implizites Illiquiditaetsmass
   (sigma^2/(P V))^(1/3) ist ohne Tradezahl rechenbar.
4. MRW nur als Nullwelt-Generator, nie als Signal; Strukturfunktionen nie als Gate (Exkurs S3 Nr. 1).
5. Trade-through-Untergrenze der Fill-Wahrscheinlichkeit braucht nur Trades (Trade jenseits des Limits => Fill
   sicher) und reicht damit bis 2020-03 inklusive der meisten STRESS_ABS-Tage [V, Zaehlung S0 noetig].
6. Nach-Schock-Zerfall gemessen (WP-11 v2, DEC-63, E-24); keine Wiederholung ohne neue Frage.
7. IV-Relaxation nach Schocks (DVOL) ist nicht gemessen; X fuer 2021-03..2024-06; Konfirmation nur K (BTC/ETH-IV ist
   Aggregat, E4 (i)).
8. Hauptkomponenten der IV-Flaeche (Niveau, Steigung, Kruemmung) an 63 Stichtagen; Inhalt UNBELEGT bis Probe.
9. Endogenitaetsgrad als Messung zulaessig, wenn keine Schwelle importiert wird und die Erreichbarkeit jeder spaeteren
   Schwelle zuerst geprueft ist (D.2); ohne Entscheidungsrelevanz unter 3.1 [U] - nicht vorgeschlagen.
10. Chargen-Clustering der Delistungen als Punktprozess (Zaehlung, S0) - Teil von IK-09 (Design-Effekt).
11. Funding-Extreme an der Kappe = R-7 (Edge-Inventur); hier nur als Nuisance-Rand.
12. Risikoneutrale Raender gegen physische ist die Frage von H-13 (2.0, gesperrt): nur als Messung in IK-06, keine
    H-13-Neuauflage ohne neue Registrierung.
13. Rekordstatistik geprueft und verworfen (Abschnitt 5): durch EVT und Change-Point (DEC-58 E1 (h)) abgedeckt.
14. Transfer-Entropie auf ~1.277 Tagesreihen zwischen Assets: nichtlinearer Schaetzer mit hohem Bias bei kurzer Reihe;
    die lineare Fassung ist IK-10 [U].
15. LZ-/Entropie-Effizienzindex als Messung moeglich, Entscheidungswert nicht erkennbar (Abschnitt 5).
16. Wochenzyklus im Panel: Power-Grenze R2-K-06 (33 bp/Tag MDE) und Welle-6 (113 bp) [F]; nur Diagnostik.
17. Wavelet-Kohaerenz auf Tagesreihen ohne Zusatznutzen gegenueber Kreuzkorrelation bei 1.277 Punkten [U].
18. Template-Suche im Verfallsfenster ist A2-Nachbarschaft (Exkurs X-ASTRO-2 nicht aufgenommen); jede Statistik im
    Fenster 07:00..08:30 UTC in Zone V/K beruehrt A2 und ist auszuschliessen (A2-Maske, Abschnitt 4.7).
19. X auf 2021-01..2024-06 (Pilotabschnitt ist Zone X, C.17-Etikett "Renditefamilie" Pflicht), Konfirmation als
    Zone-V-Blick in Kohorte 1 (IK-10).
20. Funding-Regelkreis aus den Funding-Drucken allein (zensiert an der Klemme, Totzone 46,7 % [F]) ist X; das
    theta-Analogon braucht Index-/Mark-Preis-Kerzen (Datenauftrag 2).
21. Die implizite Basis je Verfall aus der Kette ist die Eingangsgroesse fuer F10/A4-Analoga (IK-06).
22. Kalibrierbuch: vorhergesagte SE/MDE aller Akten-Feasibilities gegen spaeter realisierte SE (IK-08); nicht
    stromgebunden.
23. Unsicherheitsbudget, Blindanalyse, Trials-Faktor, CLs/Feldman-Cousins sind Berichts- und Verfahrensformen, keine
    Datenprogramme; DEC-104 E1 setzt die Pflichtausgabe.
24. GSD/Futility/SESOI/Assurance sind ab Kohorte 1 Regel (DEC-104 E2-E7); neu waeren TOST fuer Gesetzeshypothesen und
    Enrichment fuer Querschnittsdesigns (Abschnitt 3, Methodennotiz).
25. Funding-Regime-Dauern (X-SURV-2) als Zaehlvorfrage aufgenommen (DEC-58 E1 (b)); nichts Neues.
26. Time-to-Fill als konkurrierendes Risiko (X-SURV-3) ist der Schaetzer fuer IK-02.
27. Lebenszyklus-Ereignisse sind F5; gestaffelte DiD mit demselben Asset auf Binance als Kontrolle ist D.16 in Reinform
    und datenlos (Exkurs S4 X-NEXP-3; Binance-Panel nur 5 Symbole).
28. Klemme/Kappe/Auto-Switch (X-NEXP-1/2, R-7): nur nach erweiterter V-1 und mit gemessenem N_cluster; Auto-Switch
    existiert erst ab 2025-10-30 [F], liegt also in V/K.
29. Tick-Size-Wechsel der 5 Symbole als natuerliches Experiment fuer Spread/Tiefe: wenige Ereignisse, Minutenhorizont -
    geprueft und verworfen (N), Abschnitt 5.
30. Verfallstakt als Instrument (X-NEXP-4) beruehrt das A2-Fenster; erst nach A2-Klaerung.
31. Ein Binance-Listungsregister (Kontrolle fuer Listungseffekte ueber Venues) existiert im Archiv nicht.
32. Fruehwarnsignale verworfen (Exkurs S2: Literatur negativ, n_eff = T/w = 2).
33. Capture-Recapture verdeckter (RPI-)Liquiditaet: Kostenfolge fuer API-Taker nicht erkennbar [V, RPI-Berechtigung an
    der Primaerquelle zu pruefen]; C-40-Nachbarschaft; verworfen (Abschnitt 5).
34. ML nur Exploration in Zone X mit verschachtelter CV und Selektions-K im Konto; ohne Registrierungsweg D.16-nah.
35. GPU-Default 0 (DEC-57); die DAY-BRIDGE (H-15 -> Tag) ist nie registriert (E-3, E.11).
36. Anomalie-Erkennung auf L2 (Sequenzbrueche, defekte Tage wie DEC-71 "277.792 Brueche") ist Teil von IK-08.

**Lesart der Matrix [U].** (a) Zone X ist fuer alle Stroeme mit Historie vor 2024-07 reich (P1d, m1, FR, TR, L2, OC, DV,
SD); arm oder leer fuer OI, OT, LQ, XV - alle Programme auf diesen Stroemen sind entweder S0 oder K. (b) Die tragfaehige
Flaeche (X ohne D-Konflikt, ohne F-Dopplung) konzentriert sich in den Zeilen M01-M05, M07, M10, M12, M18, M20-M25, M32,
M33 - also bei Skalengesetzen, Kosten, Abhaengigkeitsstruktur, Datenqualitaet, Survival/Demografie. (c) Die
Zeilen mit Signal-Ehrgeiz (M09, M14, M15, M16, M17, M19, M34, M35) sind weitgehend tot (D.2, D.3, D.4, D.6, D.11,
D.16), schon Feld (F2, F3, F5, F7, F9) oder A2-Nachbarschaft.

---

## 3. Ideenkarten (elf neue Programme; Platz zwoelf bewusst frei)

Abgrenzung: keine Karte deckt F1..F12, H-01..H-33 oder A1..A5 ab; wo eine Karte an ein Feld oder einen Kandidaten
grenzt, steht die Abgrenzung in der Zeile "Konflikte". Typ MP = Messprogramm (erzeugt Wissen ohne Praemie und
kalibriert Nullmodelle/Kosten der Konfirmation); Typ H = Hypothese mit Konfirmationsweg. "Frueheste Konfirmation"
nach DEC-104: Kohorte 1 = 2027-01-01 (Vorbedingung: OC des Pakets, E0); Zone-V-Blick in Q1 2027; Zone-K-Fenster
2026-07-01..2027-06-30 mit GSD-Blicken, letzter Blick Anfang Juli 2027 [R, calc N]. Alle Aufloesungsgrenzen sind
Normalnaeherungen aus Akten-Nuisance mit markierten Annahmen, **keine Effektgroessen**.

### 3.0 Uebersicht und Rang

| Rang | Karte | Typ | Methodenfamilien | Zone X jetzt? | frueheste Konfirmation (DEC-104) | Hauptdaten | Datenauftrag | Wofuer (Entscheidungsrelevanz) |
|---|---|---|---|---|---|---|---|---|
| 1 | IK-01 Mikrostruktur-Invarianz und Taker-Kostenkurve | MP (+ Gesetzes-H) | M02, M03, M08, M11 | ja | Alts (Zaehl-/Groessen-Exponenten): V-Blick Q1 2027; Impact und BTC/ETH: K ab 2026-08, bis 08/2027 | Trades, L2, kline1d | 3 (Tradezahl aller Perps) | SESOI-Kurve (E3) fuer jede 3.1-Registrierung |
| 2 | IK-04 Skalengesetze, Ereigniszeit, schwere Raender -> minimale Nullwelt | MP (Nullwelt) | M01, M04, M10, M12, M36b | ja | keine noetig (Kalibrierbuch prospektiv) | kline1m, Trades, kline1d | - | OC vor Kohorte 1 (E0); wahre alpha/Power |
| 3 | IK-05 RMT-Faktorzahl und Netzwerk-Nullwelt Klasse W | MP (Nullwelt) | M07, M21 | ja | keine noetig | kline1d ALL | (Marktkap) | S-4: Fensterlaenge Klasse W, Neutralisierung |
| 4 | IK-02 Warteschlangen-Orderbuch und Maker-Kostenkurve | MP (+ Gesetzes-H) | M05, M32 | ja (L2 schwer: Nutzer-PC) | K: Alts bis 07/2027; BTC/ETH ab 2026-10, bis 10/2027 | L2 BTC/ETH, Trades | 4 (L2-Vorextraktion) | Maker-SESOI (Faktor 2,7 in IC_min); Stress-RAISE |
| 5 | IK-08 Metrologie der Datenstroeme und Kalibrierbuch | MP (Datenqualitaet) | M24, M25, M26, M36a | ja (S0 auch im Siegel) | keine noetig | Katalog, alle Stroeme | 5 (Ausfall-/Wartungsregister) | Ausfallbudget, Erreichbarkeit (E8 (d)), Automation |
| 6 | IK-07 Demografie des Perp-Lebenszyklus (APC) | MP (+ H) | M33, M08, M32 | ja | V-Blick Q1 2027; K bis 07/2027 | kline1d, Funding, Register | 6 (Spezifikations-Historie) | ersetzt die unbewiesene 8-Wochen-Regel; Nullwelt-Heterogenitaet |
| 7 | IK-09 Delisting-Hazard mit registrierten Kovariaten | H | M32, M09 | ja | K bis 07/2027 (V nur mit C.17) | kline1d, Register | (Marktkap, OI aller Perps) | IPCW fuer jeden Querschnittstest; F5-Antizipation |
| 8 | IK-06 Optionsketten-Invarianten (Tardis) | MP (+ H Teil b) | M18, M12, M07, M23 | nach Inhaltsprobe | Teil b: K bis 07/2027 | Tardis 63 X-Stichtage, deribit/tickers | 1 (Inhaltsprobe, Pushdown) | F10-Einstiegsbasis; Optionsnullwelt (A4/A5) |
| 9 | IK-10 Verzoegerte Marktreaktion (Price Delay) im Querschnitt | H | M20, M36b | ja | V-Blick Q1 2027 | kline1d ALL | 2 (Index-Kerzen) | einziger neuer Querschnittskandidat; an der Taker-Kante |
| 10 | IK-03 Diskretes Delta-Hedging (Leland-Kurve) | MP (Kosten) | M23, M01 | ja | keine noetig | kline1m, Trades | - | Kostenkomponente Klasse P (A5, H-26b); aendert VRP-Testbarkeit nicht |
| 11 | IK-11 Funding-Regelkreis (Reserve) | MP | M22, M18 | teilweise | keine als Praemie | Funding, kline1d | 2 (Index-Kerzen) | Funding-Bein der L/S-Renditen; Mechanik-Konstanten F2/R-7 |

Konfirmierbar innerhalb von 12 Monaten (Auftrag: mindestens vier): IK-01, IK-02, IK-06 (Teil b), IK-07, IK-09, IK-10.
Messprogramme (Auftrag: mindestens vier): IK-01..IK-08 und IK-11.

---

### IK-01 Mikrostruktur-Invarianz und Taker-Kostenkurve (Kyle-Obizhaeva, Quadratwurzel-Impact)

- **Typ.** Messprogramm (Invariante + Kostenmodell); der Gesetzesteil ist als Aequivalenzhypothese konfirmierbar.
- **Mechanismus und Zahler.** Keine Praemie. Struktur: Wett-Ankunftsrate und Wettgroesse skalieren mit der
  Handelsaktivitaet W = P x V x sigma (Invarianz-Hypothese, Exponenten 2/3 und -2/3 [sek: Kyle/Obizhaeva 2016]); Impact
  ist konkav in Q/V [sek: Toth et al. 2011; Patzelt/Bouchaud 2018]. Zahler der Kosten sind wir als Liquiditaetsnehmer.
- **Groessen und Statistik.** (a) Steigungen von log(Tradezahl), log(mittlere Tradegroesse/V) und log(Spread-Proxy) auf
  log W je Symbol-Tag; (b) aggregierter Impact R(Q, tau) = E[r(t, t+tau) | signierter Fluss Q] als Funktion von Q/V_tau
  fuer tau 1 min..1 Tag (Skalenkollaps pruefen); (c) Buchlauf-Kosten einer hypothetischen Market-Order aus L2
  (BTC/ETH 2023-01..2024-06); (d) Uebertragung auf das Panel: KO-implizites Illiquiditaetsmass (sigma^2/(P V))^(1/3) aus
  kline1d fuer ~500 Perps, geprueft gegen die einmal gemessenen Spread-Dezile (E-12). Schaetzer: OLS mit Tages-Cluster
  (stationaerer Bootstrap), Theil-Sen als robuste Gegenprobe; Ausgabe Schaetzer, 95-%-CI, Ausschlussgrenze (E1).
- **Nullmodell.** (i) Vorzeichen-Permutation der Trades innerhalb von Minuten (Impact 0); (ii) zeitpermutierte Tage
  (Aktivitaet und Groesse entkoppelt -> Exponent 0); Positivkontrolle: gleichzeitiger Minuten-IC +0,53..0,61 (B.14) muss
  in derselben Pipeline reproduziert werden.
- **Daten.** Haben: `bybit/publicTrade` 5 Symbole (X 2020-03..2024-06), WP-0-Bar-Cache (vol_buy/vol_sell, n_trades),
  L2 BTC/ETH (X), kline1d ALL. Fehlen: Tradezahl/Tagesaggregate aller Perps (Querschnittsform), L2 der Alts vor 2026-06.
- **Zone und frueheste Konfirmation.** X sofort (Konto-Zeile vor jeder Abfrage). Konfirmation, Form TOST "Exponent in
  [2/3 - m, 2/3 + m]" je Gesetz, m vorab aus Zone X: (i) **Zaehl-/Groessen-Exponenten** fuer SOL/BNB/XRP (keine
  BTC/ETH-Aggregate) als ein Zone-V-Blick in Kohorte 1, Rechnung Q1 2027; (ii) **Impact-Gesetz** nicht auf W1/W2: der
  gleichzeitige Fluss-Rendite-IC aller 5 Symbole ist ueber alle Halbjahre 2021H2..2026H1 gesehen (H-24-Positivkontrolle,
  B.14) und H-24 W-R2 reicht bis 2026-07-31 in Zone K (E-31) -> Impact nur Zone K ab 2026-08-01, 12-M-Fenster bis
  2027-07-31, letzter Blick August 2027; BTC/ETH-Exponenten ebenfalls nur Zone K.
- **Aufloesungsgrenze [R, calc I/J/K].** Steigungs-SE bei 365 Tagen, sd(log W) 0,4..0,5 [V], Residual-SD 0,2..0,3 [V]:
  0,021..0,039 -> TOST-Marge >= 0,08..0,16 (alpha 0,0025 je Seite, Power 0,8); bei ~1.500 Zone-X-Tagen SE ~0,02.
  Kostenkurve, Groessenordnung mit Y 0,5..1 [sek]: BTC (sigma_d 262 bp [F]) 0,4..0,8 bp bei Q/V 1e-5, 4..8 bp bei 1e-3,
  13..26 bp bei 1e-2; Alt (sigma_d 650 bp [V]) 1..2 / 10..21 / 33..65 bp. Die "~4 bp Slippage" der Wand entspricht bei
  BTC einem Auftrag von 2e-4..9e-4 des Tagesvolumens. **Akten-Vorpruefung (nur Groessenordnung):** Spread-Verhaeltnis
  der Extrem-Dezile 19,1 (E-12, ein Snapshot) gegen Umsatz-Verhaeltnis Q95/Q5 394 (Zensus 2026-10-29) ergibt bei gleicher
  Vol einen Exponenten 0,49; das KO-Gesetz (1/3) braucht ein Vol-Verhaeltnis 4,2 zwischen den Extrem-Dezilen - die
  Daten koennen beide Lesarten trennen, sobald die Vol je Dezil gemessen ist [V: Dezil-Quantil-Zuordnung, Tick-Bindung am
  liquiden Ende, Perp- statt Spot-Umsatz].
- **Wand-Etikett.** Entfaellt (Messung); das Ergebnis **ist** die Wand als Kurve (DEC-104 E3 (a)).
- **Konflikte mit Kompendium D.** D.1 (Spread-Capture tot) unberuehrt - keine Ertragsidee. D.5/D.14 (OFI als Signal):
  hier kein Fortsetzungs-Claim; Etikett "Kosten-Messung". F4 (Tagesfluss -> Tagesrendite, Kyle-lambda auf Tagesskala)
  ist abgegrenzt: IK-01 misst die Intraday-Skalierung und die Invarianz ueber Symbole und Jahre.
- **Vorwissen und Siegel.** BTC/ETH-Mikrostruktur ist BTC/ETH-Aggregat (E4 (i)): Zone V nicht nutzbar, Zone K nur
  prospektiv; Siegel ab 2026-07-01: bis zur Registrierung S0. A2-Maske (07:00..08:30 UTC) in V/K.
- **Datenauftrag.** Nr. 3 (Tagesaggregate aus dem Trade-Archiv fuer alle Perps); optional Nr. 4.
- **Was nicht folgt.** Kein Signal, keine Handelbarkeit; Metaorder-Impact ist aus anonymen Trades nicht identifiziert -
  gemessen wird aggregierter Impact plus Buchlauf; die Uebertragung auf eigene Auftraege ist eine Modellannahme (Typ-B).

### IK-02 Warteschlangen-Orderbuch und Maker-Kostenkurve

- **Typ.** Messprogramm (Kostenmodell); Queue-Gesetze konfirmierbar.
- **Mechanismus und Zahler.** Ein Maker-Fill ist die Erschoepfung der Warteschlange vor der eigenen Order durch
  Market-Orders und Stornos; adverse Selektion heisst, Fills haeufen sich vor unguenstigen Bewegungen [sek: Cont/Stoikov/
  Talreja 2010; Huang/Lehalle/Rosenbaum 2015]. Kein Praemienzahler; Ergebnis ist die Maker-Seite der SESOI.
- **Groessen und Statistik.** Intensitaeten lambda(q, Imbalance, Tageszeit, Vol-Zustand) fuer Limit-, Market- und
  Storno-Ereignisse je Level (Poisson-MLE je Zustandszelle, Tages-Cluster); daraus p_fill(t | Zustand) und adv_sel(t) als
  Kurvenschar; Resilienz (Rueckfuellzeit nach grossen Market-Orders); Schaetzer fuer Time-to-Fill als konkurrierendes
  Risiko (X-SURV-3, DEC-58 E1 (f)). **Untergrenze ohne L2:** Trade-through (Trade jenseits des Limits => Fill sicher) aus
  Trades 2020-03..2024-06; **Obergrenze:** pro-rata verteilte Stornos. Die Spanne ist ein Typ-B-Fehler, weil L2 die
  Queue-Position nicht identifiziert (L3 oeffentlich nicht vorhanden [V]).
- **Nullmodell.** Poisson mit konstanten Intensitaeten (Cont-Stoikov-Talreja) gegen zustandsabhaengige Intensitaeten;
  Positivkontrolle auf einem synthetischen Buch mit bekannten Intensitaeten. Die WP-10(B)-Konstanten (DEC-71) dienen nur
  als Abgleich der Groessenordnung - sie liegen in Zone K und werden nicht neu gerechnet.
- **Daten.** Haben: L2 BTC (74 %) / ETH (41 %) X 2023-01-18..2024-06 (orderbook.500, Snapshot+Delta, 0,4..1,3 GB/Tag
  [F WP-1]); Trades fuer die Untergrenze. Fehlen: L3; Alt-L2 vor 2026-06.
- **Zone und frueheste Konfirmation.** X sofort (Transfer schwer: Nutzer-PC oder Vorextraktion, Abschnitt 4). Queue-
  Gesetze (z. B. Depletionsrate als Potenz der Queue-Groesse) als TOST-Hypothese nur in Zone K: fuer SOL/BNB/XRP (L2 ab
  2026-06-24, von WP-10(B) unberuehrt) 12-M-Fenster 2026-07..2027-06, letzter Blick Juli 2027; fuer BTC/ETH erst ab
  2026-10-01, weil WP-10(B) p_fill und adverse Selektion auf 2026-06-22..09-16 bereits gerechnet hat (DEC-71, E-31) ->
  letzter Blick Oktober 2027, noch innerhalb von 12 Monaten.
- **Aufloesungsgrenze [F/R].** Statistik nicht bindend: DEC-71 hatte auf 64..66 Tagen CI +-0,005 fuer p_fill(60 s).
  Bindend sind (i) der systematische Faktor ~6 zwischen FIFO 0,06 und pro-rata 0,37 [F] und (ii) die Stress-Zelle:
  STRESS_ABS = Tage ueber dem 99-Perzentil der Gesamthistorie (DEC-56), also rund 1 % der ~2.400 Tage seit 2020-03
  [R]; im L2-Fenster 2023-01..2024-06 vermutlich nur wenige davon [V], die Trade-through-Untergrenze erreicht
  dagegen wahrscheinlich >= 10 STRESS_ABS-Tage in 2020-03..2024-06 (DEC-71 (2) verlangt >= 10) [V, S0-Zaehlung].
  SESOI-Relevanz [R, calc B]: Tages-Querschnitt bei vollem Umschlag IC_min Maker 0,0062 gegen Taker 0,0169.
- **Wand-Etikett.** Entfaellt (liefert die Maker-Kurve; Taker bleibt Default-Etikett nach E3).
- **Konflikte.** D.1 (Spread-Capture) - keine Ertragsidee, nur Kostenkonstante; WP-10(B) wird erweitert (Zone X,
  Stress, Zustaende), nicht ersetzt; E-31 (WP-10(B)-Kontamination) gilt fuer jede K-Nutzung als C.17-Zeile.
- **Vorwissen und Siegel.** wie IK-01; A2-Maske in V/K.
- **Datenauftrag.** Nr. 4 (L2-Vorextraktion fuer Stichprobentage), sonst Lauf auf dem Nutzer-PC (Verfassung, Abschnitt Marktdaten: grosse
  Orderbuch-Laeufe dort).
- **Was nicht folgt.** Kein Maker-Ertrag; die Fill-Kurve einer hypothetischen Order bleibt modellabhaengig, weil es
  keinen Live-Order-Code gibt (Verfassung) und damit keine echte Fill-Validierung.

### IK-03 Diskretes Delta-Hedging: die Leland-Kurve auf echten Pfaden

- **Typ.** Messprogramm (Kostenmodell Klasse P).
- **Mechanismus.** Delta-Hedging ist eine abgetastete Regelung mit Stellkosten: Kosten je Intervall ~ kappa x Gamma x S^2
  x E|dS/S| [sek: Leland 1985; Hoggard/Whalley/Wilmott 1994; Bertsimas/Kogan/Lo 2000]. Reale Pfade (Spruenge, schwere
  Raender, Kurzfrist-Umkehr B.14/H-24, Bid-Ask-Bounce) verschieben die Brown-Kurve in unbekannte Richtung.
- **Groessen und Statistik.** H(dt) = Summe |Delta-Aenderung| je Tag fuer ein standardisiertes ATM-Gamma-Profil aus
  realen BTC/ETH-Pfaden, relativ zur Brown-Vorhersage, fuer dt 1 min..1 Tag; daraus Kostenaufschlag dsigma(dt, kappa)
  in Vol-Punkten und die Hedge-Fehler-Varianz als Risikokurve; Tages-Cluster-CI, Zerlegung nach STRESS_REL/ABS.
- **Nullmodell.** Brownsche Bewegung mit gleicher Tagesvol (Leland exakt); zweite Null: MRW aus IK-04.
- **Daten.** Haben: kline1m BTC (X 2020-03..2024-06), ETH (X 2021-03..2024-06), Trades fuer < 1 min, Tardis-Gamma-Profile
  (optional). Fehlen: nichts fuer den Kern.
- **Zone.** X sofort; keine Konfirmation noetig (Kostenkonstante); Stabilitaetspruefung nur prospektiv in K.
- **Aufloesungsgrenze [R, calc H].** Brown-Baseline dsigma = kappa x sqrt(2/pi) / sqrt(dt) (annualisiert, unabhaengig von
  sigma): Taker 5,5 bp je Bein [F B.3]: 0,84 VP (taeglich), 1,45 (8 h), 4,1 (stuendlich), 14 (5 min); Maker 2 bp: 0,30 /
  0,53 / 1,49 / 5,2. Formfaktor fuer schwere Raender (t4) 0,886 senkt, Kurzfrist-Umkehr hebt - Nettowirkung UNGEMESSEN.
  Statistische Praezision auf > 1.000 Tagen nicht bindend [U].
- **Wand-Etikett.** Kostenmodell, keine Ertragsidee.
- **Konflikte.** D.15 (reaktives Long-Vol) unberuehrt; H-26b-Reihenfolge (E.6) bleibt - IK-03 liefert eine der
  fehlenden Kostenkomponenten, hebt die Sperre nicht auf.
- **Vorwissen und Siegel.** BTC/ETH-Vol-Statistik: X bis 2024-06, sonst K.
- **Datenauftrag.** Keiner (Kern); fuer reale Gamma-Profile Nr. 1 (Tardis-Inhaltsprobe).
- **Ehrliche Einordnung [U].** Die Testbarkeit der VRP aendert IK-03 nicht: MDE80 12,9 VP liegt ueber jeder hier
  plausiblen Hedge-SESOI (DEC-104 E3 (e)). Wert fuer A5 (Risk-Reversal-Hedge), H-26b und jede kuenftige
  Klasse-P-Optionsidee; deshalb Rang 10.

### IK-04 Skalengesetze, Ereigniszeit und Korrektur fuer schwere Raender -> minimale Nullwelt

- **Typ.** Messprogramm (Skalengesetz + Nullwelt); Vorbedingung der OC (DEC-104 E0, E8 (a)).
- **Mechanismus.** Aggregationsverhalten (Varianz-Zeit-Funktion, Kurtosis-Zerfall, Tail-Index-Stabilitaet),
  Vol-Clustering und Leverage-Korrelation bestimmen die Verteilung jeder Clusterstatistik; Ereigniszeit (Volumen-/Vol-Uhr)
  gaussifiziert Renditen [sek: Clark 1973; Ane/Geman 2000]; ein MRW reproduziert Clustering und Skalierung mit drei
  Parametern je Faktor [sek: Bacry/Delour/Muzy 2001].
- **Groessen und Statistik.** (a) V(h)/h fuer h = 1 min..4 Wochen (BTC/ETH m1 und Trades; Panel kline1d); (b) Schiefe und
  Exzess-Kurtosis der **Clusterstatistiken je Familie** (Tagesrendite, Wochen-IC unter Null, Ereignis-CAR) als Funktion
  von h; (c) Hill-Tail-Index je h; (d) Leverage-Funktion L(tau); (e) Varianzhomogenisierung durch Volumen-/Vol-Uhr;
  (f) MRW-plus-Faktor-Nullwelt, kalibriert auf (a)-(d) in der ersten Haelfte von Zone X und validiert gegen eine vorab
  fixierte Liste einbehaltener Momente in der zweiten Haelfte (Split 2021-01..2022-09 / 2022-10..2024-06).
- **Nullmodell.** iid-Gauss und iid-t als Vergleichsnullen; Surrogat-Daten (IAAFT, Block-Bootstrap) als Gegenprobe.
- **Daten.** Haben: kline1m, publicTrade, kline1d ALL, fundingRateAll (X). Fehlen: nichts.
- **Zone.** X sofort. Keine eigene Konfirmation; prospektive Pruefung ueber das Kalibrierbuch (IK-08): vorhergesagte SE
  der Kohorte-1-Tests gegen realisierte.
- **Aufloesungsgrenze und Wirkung [R, calc F/G].** Mit Exzess-Kurtosis 5..10 (r_pre-Akte) und 40..52 Clustern:
  df_eff 6,6..14,8, t_krit(0,0025) 3,29..4,12 statt 2,807, MDE-Faktor 1,14..1,38; bei 104 Clustern 1,07..1,12, bei 365
  Clustern 1,02..1,03 (Satterthwaite-Naeherung, Unabhaengigkeit von Zaehler und Nenner angenommen). Schiefe -0,5..-1:
  effektives einseitiges alpha 0,0040..0,0059 statt 0,0025 bei n 40..52, 0,0031..0,0036 bei n 365 (Edgeworth erster
  Ordnung [sek: Hall 1987]; in den aeussersten Raendern nur Groessenordnung). Vol-Zeit-Gewichtung bei
  Varianzverhaeltnis 1,67..2,8 zwischen Regimen (A2-Akte: Faktor 2,3 zwischen 2021 und 2023 [F]): 6..22 % weniger Daten,
  MDE-Faktor 0,97..0,88 - nur fuer Effekte konstant in bp [U]. Geltungsbereich der Korrekturen: Tests mit geschaetzter
  SE und Normal-Kritik; exakte Permutationstests unter Austauschbarkeit (A2) verlieren unter schweren Raendern Power,
  nicht alpha.
- **Wand-Etikett.** Entfaellt.
- **Konflikte.** D.16 (Infrastruktur vor Signal): nur minimale, je Familie validierte Nullwelt - kein Voll-Marktmodell
  (das bleibt N, PRD_ANALYSE 3). Exkurs S3: Strukturfunktionen nie als Gate. B.9-Lehre: strukturellen Nulleffekt jeder
  Kalibriergroesse vorab ausrechnen.
- **Vorwissen und Siegel.** Nur Zone X (vor 2024-07-01); keine W1/W2-Beruehrung.
- **Datenauftrag.** Keiner.
- **Entscheidungsrelevanz [U].** Hoch: Review-Luecke 3 ("wahre Power niedriger, wahres alpha hoeher") wird von einem
  Vermerk zu einer Zahl; die OC des Pakets (E0) braucht genau diese Nullwelt.

### IK-05 RMT-Faktorzahl und Netzwerk-Nullwelt fuer die Klasse W (Instrumentierung von S-4)

- **Typ.** Messprogramm (Nullwelt). Ehrlich: nicht neu im Ziel (S-4 der Edge-Inventur), neu im Instrument.
- **Mechanismus.** Querschnittsabhaengigkeit jenseits des Marktfaktors (Sektoren/Narrative, Listungskohorten,
  Delisting-Chargen) erzeugt die 2,3..2,6-fache Streuung des Wochen-IC (E-14 [F]); RMT trennt Signal-Eigenwerte vom
  Rauschband [sek: Laloux et al. 1999; Plerou et al. 2002]; Overlap-Matrizen und Community-Drift messen ihre Stabilitaet
  [sek: Mantegna 1999; Onnela et al. 2003].
- **Groessen und Statistik.** Eigenwerte der residualen (marktbereinigten) Korrelationsmatrix taeglich ueber 2021-01..
  2024-06 gegen eine **empirische** Rauschkante (zeitliche Permutation je Symbol; MP-Kante nur als Referenz, weil schwere
  Raender sie anheben [sek: Biroli/Bouchaud/Potters 2007]); Faktorzahl k; Eigenvektor-Overlap zwischen Halbjahren;
  Communities und Drift; dann die eigentliche S-4-Frage: reproduziert eine k-Faktor-Null (outcome-only) die gemessene
  SD(IC_t)-Inflation des Piloten (2022-04..2024-06 liegt jetzt in Zone X, DEC-104 E4 (a))?
- **Nullmodell.** MP / permutierte Panels; Ein-Faktor-Null (DEC-75..88); k-Faktor-Null.
- **Daten.** Haben: kline1d ALL inkl. Delisteter, Union-Panel (DEC-72); die Pilot-IC-Serie wird in Zone X mit Konto neu
  gerechnet - kein Rueckgriff auf Dateien der Siegelliste.
  Fehlen: Marktkapitalisierung (fuer die Deutung eines Groessenfaktors; PRD_ANALYSE-Auftrag 1).
- **Zone.** X sofort; keine Konfirmation (Nuisance); prospektiver Nutzen: die k-Faktor-Null wird als Null der
  Kohorte-1-Querschnittstests registriert (IK-10, F1).
- **Aufloesungsgrenze [R, calc E].** Var(IC_t) ~ (1/(K-1)) x (1 + Summe_f (x'l_f)^2/(K-1)); fuer SD-Verhaeltnis 2,5 muss
  Summe_f (x'l_f)^2/(K-1) = 5,25 sein - bei voller Ausrichtung der Charakteristik auf einen Faktor ein residualer
  Eigenwert >= 6,2 (cos^2 0,5: 11,5; 0,25: 22), gegen MP-Kanten 1,95 / 2,20 / 2,64 bei K 200 / 300 / 500 und T 1.277.
  Ein solcher Faktor ist in Zone X nachweisbar, wenn es ihn gibt; fehlt er, ist die Faktor-Erklaerung der Streuung falsch
  und Zeitvariation/Heteroskedastizitaet (IK-04) wird die Kandidatin. Unbalanciertes Panel (Listungen/Delistungen) ist
  die Hauptstoergroesse [U].
- **Wand-Etikett.** Entfaellt.
- **Konflikte.** D.10 (H-12, Kreuzboersen-RMT BTC/ETH x 3 Boersen) ist ein anderer Gegenstand. S-4 identisch im Ziel.
- **Vorwissen und Siegel.** Nur X; W1/W2 nicht beruehren (Zone V, blind fuer Klasse W).
- **Datenauftrag.** Keiner fuer den Kern; Marktkapitalisierung (PRD_ANALYSE-Auftrag 1) fuer die Deutung.
- **Entscheidungsrelevanz.** Hoch fuer Klasse W: faellt die Wochen-SD durch k-Faktor-Neutralisierung von ~0,12 auf
  0,05..0,066, sinkt die Fensterlaenge auf 16..29 % (E-14 [abg., V]); entscheidet, ob Querschnittsregistrierungen in
  Kohorte 1 eine Mehrfaktor-Neutralisierung tragen.

### IK-06 Optionsketten-Invarianten aus der Tardis-Kette (63 Zone-X-Stichtage)

- **Typ.** Messprogramm (Invarianten, Optionsnullwelt, Datenersatz fuer F10); Teil b als Hypothese konfirmierbar.
- **Mechanismus.** Put-Call-Paritaet erzwingt den impliziten Forward je Verfall (Arbitrage); die Kopplung von IV und Spot
  (sticky strike gegen sticky moneyness) und die Skew-Dynamik sind Marktstruktur; risikoneutrale Momente [sek: Bakshi/
  Kapadia/Madan 2003]. Kein Praemienzahler (F10-Zahler, Hedger der Laufzeit, bleibt bei F10).
- **Datenfund [R/V].** 386,63 GB / 91 Stichtage = 4,25 GB und ~58 Mio Zeilen je Stichtag: das ist kein
  Monatsschnappschuss, sondern ein Intraday-Kettenstrom (vermutlich alle Quote-/Greeks-Updates aller Instrumente) an je
  einem Tag pro Monat [V bis C.8-Inhaltsprobe]. Zone X: 2019-04-01..2024-06-01 = 63 Stichtage [R].
- **Groessen und Statistik.** (a) Implizite Basis-Terminstruktur b(T) je Stichtag (aus dem Basiswertfeld je Verfall,
  falls vorhanden [V], sonst Put-Call-Paritaet) - liefert fuer jeden Quartalskontrakt seit 2019 mehrere Basisbeobachtungen
  vor Verfall, also die Einstiegsbasis, die F10 fehlt; (b) Intraday-Spot-Vol-Beta dIV_ATM/dln S je Stichtag und Laufzeit
  (sticky-Index); (c) Smile-Form (25-Delta-Risk-Reversal, Butterfly) monatlich; (d) risikoneutrale gegen physische Raender
  (IK-04) - nur als Messung. Je Stichtag Intraday-Block-CI (5-min-Bloecke), ueber Stichtage Cluster = Tag.
- **Nullmodell.** Arbitragefreiheit als Positivkontrolle der Datenqualitaet (zwei Forward-Schaetzer muessen innerhalb des
  Quote-Bands uebereinstimmen); sticky-strike-Null (Beta 0) und sticky-moneyness-Null (Beta = Skew-Steigung).
- **Daten.** Haben: tardis/options_chain (Inhalt UNBELEGT); deribit/tickers ab 2026-06-16 (K; 125/139-Ausfallmuster der
  Live-Stroeme [F]). Fehlen: dichte Wochen-IV-Historie vor 2026-06 (E-22).
- **Zone und frueheste Konfirmation.** X nach Inhaltsprobe. Teil (b) als Gesetzeshypothese ("Spot-Vol-Beta im Band
  [b1, b2]") nur Zone K (BTC/ETH-IV = Aggregat, E4 (i)) ueber deribit/tickers taeglich: 12-M-Fenster bis Juli 2027
  (Ausfallbudget ~10 % [R, IK-08]). Teil (a) ist Nuisance/Datenersatz, keine Konfirmation.
- **Aufloesungsgrenze [R, calc L].** Halber Quote-Spread 0,07 VP [F B.6] x 5,28 bp Index je VP [F B.5] -> Forward-Fehler
  0,52 bp je Strike-Paar -> 30-Tage-Basis +-6,4 bp p.a. (1 Paar) bzw. +-1,4 bp p.a. (20 Paare, unabhaengige Fehler [V]);
  7-Tage-Verfall +-6..27 bp p.a. Spot-Vol-Beta: Zwischen-Tages-Streuung UNGEMESSEN, MDE offen.
- **Wand-Etikett.** Entfaellt (Messung); F10 traegt sein eigenes Etikett.
- **Konflikte.** D.17 (Ketten-Kandidaten tot, gestuetzt auf Dichte) bleibt unberuehrt - IK-06 ist Messung und
  monatliches Design, kein dichter Kettenkandidat (PRD_ANALYSE K-13). H-13 (2.0, gesperrt) fuer Teil (d): keine
  Neuauflage ohne Registrierung. A5 (gesperrt, E.6): Teil (c) ist Nuisance, kein Test. F8 (GEX): falls OI je Strike im
  Strom ist, waere GEX an 63 Monatsersten rekonstruierbar - Hinweis an F8, kein Teil dieser Karte.
- **Vorwissen und Siegel.** IV ist BTC/ETH-Aggregat -> Konfirmation nur K; Stichtage ab 2026-07-01 im Siegel; die 24
  V-Stichtage sind nach DEC-104 nicht explorierbar.
- **Datenauftrag.** Nr. 1 (Inhaltsprobe mit Feldliste, Zeitaufloesung, Pushdown nach Verfall).

### IK-07 Demografie des Perp-Lebenszyklus (Alters-Perioden-Kohorten)

- **Typ.** Messprogramm; das Altersprofil ist als Hypothese konfirmierbar.
- **Mechanismus.** Liquiditaet, Vol und Funding-Verhalten eines Perps aendern sich mit dem Alter seit Listung
  (Aufmerksamkeit, Market-Maker-Einstieg, Hebelaufbau), mit der Kalenderperiode und mit der Listungskohorte (W2: 29,7 %
  der Symbol-Wochen in 1..5 Mio USD, "mehr kleine Listungen" [F Zensus 2026-10-29]). APC-Zerlegung [sek: Holford 1983;
  Yang/Land 2013]. Kein Praemienzahler.
- **Groessen und Statistik.** Altersprofile (Wochen seit erstem Handelstag) von log-Vol, log-Umsatz, Totzonen-Anteil
  (F = I; Universumsmittel 46,7 % [F]), Intervallklasse, Range-Spread-Proxy [sek: Corwin/Schultz 2012] und
  Delisting-Hazard (Uebergang zu IK-09). **Keine Mittelrenditen** (Abgrenzung F5; Renditefamilie bleibt unberuehrt).
  Identifikation a + c = p: Periodeneffekt ueber eine beobachtete Kovariate (Marktfaktor-Vol, Panel-Umsatz) statt freier
  Periodendummies [U]; Cluster = Listungsdatum (Chargen).
- **Nullmodell.** Flaches Altersprofil nach Perioden- und Kohortenkontrolle; Permutation der Listungsdaten innerhalb des
  Quartals.
- **Daten.** Haben: kline1d ALL inkl. Delisteter, fundingRateAll, delisting_dates, WP-12-Ankuendigungen. Fehlen:
  launchTime vor 2026-10-20 (Listungsdatum = erster kline1d-Tag [V]; Listungen vor 2021-01-01 sind linkszensiert);
  Tick-Size-Historie fuer die Spread-Normierung (Datenauftrag 6); Marktkapitalisierung.
- **Zone und frueheste Konfirmation.** X sofort. Vorhersage des Altersprofils (z. B. Vol-Verhaeltnis Woche 1-8 gegen
  13-26) auf den Listungskohorten in Zone V (W1/W2, ~275 Listungen [R]) als ein Blick in Kohorte 1 (Q1 2027), mit
  C.17-Etikett (Umsatz-Zensus W1/W2 und A3-Vol-Kalibrierung W1/W2 gesehen); alternativ Zone K (~137 Listungen
  2026-07..2027-06 [R]), letzter Blick Juli 2027.
- **Aufloesungsgrenze [R, calc D].** Alterskontrast log-Vol, alpha 0,0025, Power 0,8, Zwischen-Symbol-SD 0,4..0,6 [V],
  Design-Effekt 1..2 [V]: Zone X (~480 Listungen) Faktor 1,10..1,22; Zone V (~275) 1,13..1,30; Zone K (~137) 1,19..1,45.
- **Wand-Etikett.** Entfaellt.
- **Konflikte.** Keine mit D; F5 (Post-Listing-Drift, Renditen) abgegrenzt; die 8-Wochen-PIT-Regel (PRD 4.1 DoD (4))
  wird erstmals gemessen statt unterstellt (E-32).
- **Vorwissen und Siegel.** Alts sind keine BTC/ETH-Aggregate; in Zone K darf die Periodenkovariate nicht aus BTC-Vol
  kommen (Siegel DEC-96 E3) - dort Panel-Umsatz verwenden.
- **Datenauftrag.** Nr. 6 (Spezifikations-Historie), optional Marktkapitalisierung (PRD_ANALYSE-Auftrag 1).
- **Entscheidungsrelevanz.** Mittel: Universumsregel jeder Querschnittshypothese (Gabelung "8 Wochen" wird eine gemessene
  Groesse); Alters-Heterogenitaet als Baustein der Nullwelt (IK-04/IK-05).

### IK-08 Metrologie der Datenstroeme: Unsicherheitsbudget, Kreuzvenue-Uhren, Ausfall- und Kalibrierbuch

- **Typ.** Messprogramm (Datenqualitaet als Instrument).
- **Mechanismus.** Jede Statistik erbt systematische Fehler der Stroeme: 14-Tage-Ausfallmuster der Live-Stroeme
  (125/139 Tage [F]), doppelte Live-Zeilen 2026-08-13 [F Verfassung, Abschnitt Marktdaten], Herkunftsmischung Archiv/Live (DEC-96 N2),
  falsche Katalog-Metadaten (DEC-96 N), Formatbruch orderbook.500/1000 (F.1), ein defekter Orderbuch-Tag mit 277.792
  Sequenzbruechen (DEC-71) [F]. Werkzeuge: GUM-Budget Typ A/B [sek: JCGM 100:2008], Zuverlaessigkeitstechnik,
  Kalibrierdiagnostik [sek: Gneiting/Raftery 2007].
- **Groessen und Statistik.** (a) Verfuegbarkeit je Strom als Zeitreihe, gemeinsame Ausfallursachen (Korrelation der
  Ausfalltage zwischen Stroemen); (b) Konsistenzpruefungen in Zone X: kline1d-Schluss gegen letzten Trade, kline1m gegen
  Bar-Cache, gemeldete Funding-Rate gegen die Formel F = P + clamp(I - P) soweit P rekonstruierbar, Deribit-Settlement
  gegen Index; (c) Kreuzvenue-Zeitstempelversatz nur als Zeitstempelstatistik (keine Preisniveaus) - Binance/Deribit
  beginnen 2025, also nur S0 bis zur Orchestrator-Freigabe [U]; (d) **Kalibrierbuch** der eigenen Vorhersagen:
  vorhergesagte SE/MDE jeder Akten-Feasibility gegen spaeter realisierte SE (Beispiel GL-035: reale IC-Streuung
  2,3..2,6x der Null war ein Kalibrierfehler [F]) als Reliability-Kurve; (e) Typ-B-Band je Konstante in `tradability3`
  (p_fill 0,06..0,37 ist das Musterbeispiel).
- **Nullmodell.** Unabhaengige (Poisson-)Ausfaelle gegen geclusterte; Kalibrierung: Verhaeltnis realisiert/vorhergesagt = 1.
- **Daten.** Katalog, `hd.gaps`, Manifest (S0, im Siegel erlaubt, DEC-96 E3); Konsistenzpruefungen auf Zone-X-Daten.
- **Zone.** X/S0 sofort; keine Konfirmation noetig.
- **Aufloesungsgrenze [R].** Nicht statistisch bindend. Ausfallbudget: bei 125/139 verfuegbaren Tagen verliert ein
  12-Monats-Fenster auf einem Live-Strom ~10 % (~36 Tage); jede "lueckenlos"-Bedingung ist unerfuellbar (H-21).
- **Wand-Etikett.** Entfaellt.
- **Konflikte.** Keine; macht DEC-104 E8 (d) (Erreichbarkeit je Design-Parameter) und den Baustein 4 der Architektur
  (Datenzugangsschicht mit Ausfalltage-Budget) maschinell.
- **Vorwissen und Siegel.** S0 ist im Siegel erlaubt (DEC-96 E3); Konsistenzpruefungen mit Preisen nur in Zone X; aus V/K
  nur Zeilen, Luecken, Zeitstempel, Schema.
- **Datenauftrag.** Nr. 5 (Ausfallprotokoll des Sammlers, Wartungs-/Upgrade-Fenster der Boersen).

### IK-09 Delisting-Hazard mit registrierten Kovariaten (Survival, konkurrierende Risiken)

- **Typ.** Hypothese mit Messcharakter (konfirmierbar innerhalb 12 Monaten).
- **Mechanismus und Zahler.** Delisting ist eine Regelentscheidung der Boerse, ausgeloest durch Liquiditaets-/
  Umsatzkriterien [sek: Boersenregeln, Primaerquelle zu beschaffen]. Kein Praemienzahler; Nutzen: IPCW-Gewichte fuer jede
  Querschnittsstatistik (Survivorship; Rendite am Delisting-Tag, PRD_ANALYSE 4.15) und Antizipation fuer F5.
- **Groessen und Statistik.** Ursachenspezifische Hazard-Ratios je SD der Kovariaten (Umsatzniveau, Umsatztrend,
  Alter aus IK-07, Totzonen-Anteil, Intervallklasse); konkurrierendes Risiko Umbenennung/Wiederlistung (DEC-72);
  Ereigniszeit Ankuendigung (WP-12, 268) gegen letzter Handelstag (Median +2 Tage, DEC-100) [F]. Cox/Fine-Gray,
  Cluster = Ankuendigungs-Charge; C-Index als Bericht.
- **Nullmodell.** HR = 1; Placebo: zufaellige Ereigniszuordnung innerhalb des Chargen-Datums.
- **Daten.** Haben: kline1d ALL inkl. Delisteter, delisting_dates (306), WP-12-Ankuendigungen, Union-Panel. Fehlen:
  OI aller Perps, Marktkapitalisierung (bestehende Auftraege 1 und 4 der PRD-Analyse).
- **Zone und frueheste Konfirmation.** X sofort (~184 Delistungen 2021-01..2024-06 bei gleichmaessiger Rate [R/V]).
  Konfirmation in Zone K: Ereignisse 2026-07-01..2027-06-30 (~52 [R]), GSD-Blicke, letzter Blick Juli 2027. Ein
  Zone-V-Blick (W1/W2, ~105 Ereignisse) nur mit C.17-Etikett (Delisting-Zaehlung W2 und Umsatz-Zensus W1/W2 gesehen [F]).
- **Aufloesungsgrenze [R, calc C].** SE(log HR je SD) ~ sqrt(deff/D): D 52, Design-Effekt 1..3 [V Chargen]: MDE80 HR
  1,67..2,42 je SD (alpha 0,0025, GSD); D 105: 1,43..1,86; Zone X D 186: 1,31..1,60 (Exploration).
- **Wand-Etikett.** Entfaellt (keine Ertragsidee; ein Delisting-Short ist praktisch unhandelbar, F5).
- **Konflikte.** Keine mit D; X-SURV-1 (deskriptives IPCW in WP-7, DEC-58 E1 (g)) wird praediktiv erweitert; F5 (CAR)
  abgegrenzt.
- **Vorwissen und Siegel.** Alts, keine BTC/ETH-Aggregate; im Siegel S0-Zaehlung der Ereignisse erlaubt, Kovariaten ab
  2026-07-01 versiegelt bis zur Registrierung.
- **Datenauftrag.** Bestehende Auftraege 1 und 4 der PRD-Analyse (Marktkapitalisierung, OI aller Perps) als Kovariaten;
  fuer den Kern keiner.

### IK-10 Verzoegerte Marktreaktion (Price Delay) im Perp-Querschnitt

- **Typ.** Hypothese (konfirmierbar innerhalb 12 Monaten ueber Zone V).
- **Mechanismus und Zahler.** Informationsdiffusion im Netz: Marktinformation erreicht wenig beachtete oder illiquide
  Perps verzoegert [sek: Hou/Moskowitz 2005 (Aktien); Lo/MacKinlay 1990]; Zahler sind Gegenparteien, die zu veralteten
  Preisen handeln. **Artefaktrisiko:** nicht-synchrone, veraltete Schlusskurse illiquider Perps erzeugen dieselbe Statistik
  [sek: Lo/MacKinlay 1990] - daher Gap-Variante und Index-Preis-Kontrolle Pflicht.
- **Groessen und Statistik.** Taeglicher Rang-IC von s_i,t = b_lag,i x r_M,t (b_lag aus rollierender PIT-Regression von
  r_i auf r_M,t und r_M,t-1 ueber 60 Tage) gegen r_i,t+1, Gap-Variante gegen r_i,t+2; Delay-Mass D_i als vorab
  registrierte Konditionierung; Cluster = Tag; skalierte Null.
- **Nullmodell.** Faktorerhaltende Null (Permutation der b_lag-Zuordnung innerhalb des Tages), k-Faktor-Null aus IK-05;
  Positivkontrolle auf einem synthetischen Panel mit eingebauter Verzoegerung.
- **Daten.** Haben: kline1d ALL (X 2021-01..2024-06; V; K). Fehlen: Index-Preis-Kerzen fuer die Stale-Kontrolle
  (Datenauftrag 2); Marktkapitalisierung.
- **Zone und frueheste Konfirmation.** X sofort (Konto; Familie "vergangene Renditen", C.17-Etikett Pilotabschnitt).
  Konfirmation: Zone-V-Blick in Kohorte 1 (W1+W2 gepoolt bei 0,0025 plus REZENZ-Screen W2 bei 0,05), Rechnung Q1 2027.
  **Achtung:** "ein Blick je Familie" (E4 (d)) - gehoeren F1 und IK-10 zur selben Familie, muessen sie in derselben
  Kohorte registriert werden, sonst verbraucht die erste den V-Blick der zweiten [U].
- **Aufloesungsgrenze [R, calc B].** SD(IC_t) = 2,5/sqrt(K-1) [V]: Zone V (730 Tage, gemeinsame Power 0,80 der Regel E2):
  MDE80 0,0148 / 0,0162 / 0,0209 bei K 600 / 500 / 300 (gepoolt allein 0,0138..0,0195); Zone K 12 Monate (GSD):
  0,0197..0,0278; Zone X (1.277 Tage, K ~200 [V]): Explorations-MDE (alpha 0,05) 0,0123, Ausschlussgrenze bei IC 0
  0,0082. SESOI (E3, sigma_xs_d 370 bp [V], L/S = 3,51 x IC x sigma, voller Tagesumschlag): Taker 0,0169, Maker 0,0062,
  gesamt 15 bp 0,0231. **Lesart:** in Zone V testbar nur bei K >= ~500 und Taker-SESOI, also genau an der Kante; in Zone K
  allein strukturell nicht testbar.
- **Wand-Etikett.** `unter_wand` beim Taker sehr wahrscheinlich (voller Tagesumschlag) [U].
- **Konflikte.** D.11 (Lead-Lag-Graph, Sekunden) und D.14 (Minutenfluss) sind andere Horizonte; H-04 (Sekunden); F7
  (Venues, nicht Assets) abgegrenzt; F1 (eigenes Reversal) ist ueber die Renditefamilie korreliert -> gemeinsame
  Kohorte und BY (E4 (f)); rev1-Vorbelastung W2 (GL-036 (4)) im C.17-Etikett.
- **Vorwissen und Siegel.** Panel-Querschnitt: W1/W2 blind (Zone V); ab 2026-07-01 Siegel.
- **Datenauftrag.** Nr. 2 (Index-Preis-Kerzen fuer die Stale-Close-Kontrolle).
- **Ehrliche Einordnung [U].** A-priori geringe Plausibilitaet fuer liquide Perps mit synchronem Tagesschnitt; die
  Ausschlussgrenze aus Zone X ist auch ohne spaeteres PASS informativ und schliesst die Linie "taegliches Lead-Lag ueber
  Assets" sauber, falls sie bei IC < 0,008 liegt.

### IK-11 Funding-Regelkreis: Systemidentifikation der Basis-Relaxation (Reservekarte)

- **Typ.** Messprogramm; **Reserve**, weil die Abgrenzung zu A1 (theta) und zum Exkurs-Vorschlag X-NEXP-1 (RKD an der
  Klemme) offen ist - der Orchestrator entscheidet, ob es als A1-Nuisance-Paket statt als Karte gefuehrt wird.
- **Mechanismus.** Funding ist ein Regler: eine Premium-Abweichung erzeugt Zahlungen, die Arbitragekapital anziehen und
  die Abweichung abbauen [sek: He/Manela/Ross/von Wachter 2022]. Zeitkonstante und Verstaerkung messen die Elastizitaet
  des Arbitragekapitals.
- **Groessen und Statistik.** Impulsantwort und Halbwertszeit des Premiums je Symbol, Intervallklasse und Regime
  (zensiertes ARX/Tobit, weil die Klemme 46,7 % der Symbol-Tage auf F = I legt [F]); mit Index-/Mark-Kerzen zusaetzlich
  der Anteil der Funding-Zahlung, der durch Preiskonvergenz statt Zahlung ausgeglichen wird (theta-Analogon).
- **Nullmodell.** Unabhaengige Premium-Schocks (keine Rueckkopplung); Totzone als mechanische Null.
- **Daten.** Haben: fundingRateAll (X 2021-01..2024-06; Intervalle aus Zeitstempeln, DEC-84), kline1d. Fehlen:
  Index-/Mark-Preis-Kerzen aller Perps (Datenauftrag 2); Premium-Index-Historie (D.17: DSM-03 nur 43 Tage Delta-Strom).
- **Zone.** X teilweise sofort; keine Konfirmation als Praemie (A1 strukturell nicht testbar, DEC-104 E3 (e)).
- **Aufloesungsgrenze.** Streuung der Halbwertszeiten UNGEMESSEN; die Zensierung halbiert grob die informativen
  Beobachtungen [U].
- **Wand-Etikett.** Entfaellt (Messung).
- **Konflikte.** A1/GL-033; X-NEXP-1 (parkiert, Auflage V-1-Erweiterung); Auto-Switch ab 2025-10-30 nur in V/K.
- **Vorwissen und Siegel.** BTC/ETH-Funding ist BTC/ETH-Aggregat (E4 (i)) -> nur K; Alts in V nur mit C.17-Etikett
  (A1-Formation in W1/W2 gesehen, E-20).
- **Datenauftrag.** Nr. 2 (Index-/Mark-Preis-Kerzen).
- **Entscheidungsrelevanz [U].** Niedrig bis mittel: Funding-Bein der L/S-Renditen jeder Querschnittshypothese
  (PRD_ANALYSE 4.15), Mechanik-Konstanten fuer F2/R-7, messbare Wiedervorlage-Bedingung fuer A1 ("neues Kostenmodell").

### 3.12 Platz zwoelf: bewusst frei

Gepruefte Kandidaten fuer den zwoelften Platz waren duenn: Taylor-Fluktuationsskalierung (als Teil in IK-01/IK-07
aufgegangen), Kompressions-Effizienzindex, Rekordstatistik, Settlement-Pinning (A2-Konflikt), Tick-Size-Experiment (N zu
klein), Capture-Recapture verdeckter Liquiditaet (keine Kostenfolge). Gruende in Abschnitt 5.

### 3.13 Methodennotiz: zwei Designbausteine aus der Klinik fuer Kohorte 1 (keine Karten)

- **TOST fuer Gesetzeshypothesen** (IK-01, IK-02, IK-06 b, IK-07): eine Invariante wird nicht "verworfen", sondern ihr
  Exponent in ein vorab registriertes Aequivalenzband gelegt. DEC-104 kennt nur einseitige Tests auf Effekt > 0; eine
  Aequivalenzform braucht eine Zeile in PRD v3 (Etikett neutral, O-Vorschlag, N-Beschluss) [U].
- **Adaptive Enrichment** fuer Querschnittsdesigns: Start auf dem vollen Panel, am ersten K-Blick vorab regelgebunden
  Einschraenkung auf die Subpopulation (z. B. Delay-Terzil, Umsatzklasse) mit kontrolliertem alpha [sek: Simon/Simon
  2013]. Lockerung in der Zeit, alpha-neutral bei korrekter Kombinationsregel; Nutzerfrage.

---

## 4. Grosse Daten konkret: was nur 309 GB Trades, 377 GB Orderbuecher und 387 GB Optionskette lehren

### 4.1 Was die grossen Daten koennen - und was nicht

**Nicht [R, calc M]:** erste Momente auf Tages- oder Wochenhorizont schneller bestimmen. Die SE einer Drift haengt nur
von der Kalenderlaenge ab: BTC sigma_annual 50,1 % (aus 262 bp/Tag [F]) -> Drift-SE 35 % p.a. nach 2 Jahren, 19,5 % nach
6,6 Jahren - gleich, ob man Tages- oder Millisekundendaten hat (Merton 1980 [sek]). Die 309 GB Trades enthalten 2.413
BTC-Tage, nicht mehr. Wo hohe Frequenz die Zahl der unabhaengigen Beobachtungen tatsaechlich erhoeht (30-min-IC:
MDE80 0,019 je Jahr gegen 0,130 auf Tagen), liegt der Horizont unter der Wand (48 Umschlaege je Tag; Exkurs S3: 96 x
11 bp = 1.056 bp/Tag Friktion bei Viertelstunden) - die Horizont-Schere der PRD-Analyse (4.1) bleibt. HF-RV fuer die
VRP ist geschlossen (DEC-98 N5).

**Doch [R/U]:** zweite Momente, Kosten, Strukturen, Datenqualitaet - relative Varianz-SE 0,08 % (1-min ueber 6,6 Jahre,
ohne Rauschen) gegen 2,9 % (Tage). Konkret:

| Was | Strom | warum nur mit grossen Daten | Karte |
|---|---|---|---|
| Taker-Kostenkurve (Impact als Funktion von Q/V und Horizont), Buchlauf | Trades, L2 | Impact ist eine Intraday-Groesse; Skalenkollaps braucht viele Groessen- und Zeitklassen | IK-01 |
| Maker-Kostenkurve (Queue-Intensitaeten, Fill, adverse Selektion, Resilienz) | L2, Trades | Ereignisse auf Sekundenebene; Zustandszellen brauchen Millionen Ereignisse | IK-02 |
| Invarianzgesetze ueber 6 Jahre und 5 Symbole (wie B.14, die einzige regime-invariante Groesse) | Trades | Regime-Invarianz ist nur ueber viele Regime pruefbar | IK-01 |
| Skalengesetze von 1 min bis 4 Wochen, Ereigniszeit, Kurtosis der Clusterstatistiken | Trades, kline1m | die feinen Skalen kalibrieren die Nullwelt, aus der die groben folgen | IK-04 |
| Kosten des diskreten Hedgings als Funktion des Abtastintervalls | kline1m, Trades | Pfadeigenschaften unterhalb einer Stunde | IK-03 |
| Optionsflaechen-Dynamik intraday, implizite Basis-Terminstruktur seit 2019 | Tardis-Kette | 58 Mio Zeilen je Stichtag [R]; die Basis je Verfall ist sonst nicht im Archiv | IK-06 |
| Datenqualitaet (Sequenzbrueche, Duplikate, Herkunftsmischung, Uhrversatz) | alle | Fehler zeigen sich erst auf Rohdatenebene | IK-08 |

### 4.2 Rechenaufwand und Transfer (2 MB/s geteilt [F Verfassung, Abschnitt Marktdaten]; Sandbox dieser Sitzung 4 Kerne, 15 GB RAM [F nproc/free; Orchestrator-Sandbox vermutlich gleichartig, V])

| Strom | MB je Partition [R] | Zeilen je Partition [R] | ganzer Strom [R] | vorgeschlagene Stichprobe | Transfer [R] | CPU [V] | wo |
|---|---:|---:|---:|---|---:|---|---|
| bybit/publicTrade | 29 (BTC aktuell ~77) | 0,67 Mio (BTC ~1,7 Mio) | 43 h | IK-01: 5 Symbole x 2 Tage/Monat 2020-03..2024-06 + 40 Stress-/Kontrolltage = 560 Symbol-Tage, `columns=` (ts, Preis, Groesse, Seite) | ~20 GB, 2,7 h | 10..30 s je Symbol-Tag vektorisiert -> 2..5 h (1 Kern) | Sandbox |
| bybit/orderbook | 188 (0,4..1,3 GB je BTC-Tag [F WP-1]) | 0,7 Mio Nachrichten (1,5..5 Mio je BTC-Tag) | 52 h | IK-02: 40 Tage (20 BTC, 20 ETH) inkl. aller Stress-Tage mit Abdeckung | ~34 GB, 4,7 h | Replay 5..20 min je Tag -> 3..13 h | Nutzer-PC oder Vorextraktion (Auftrag 4) |
| tardis/options_chain | 4.250 | 58 Mio | 54 h | IK-06: 1 Tag Inhaltsprobe -> 12..24 Tage -> ggf. alle 63 X-Tage; Spaltenauswahl ~50 % [V] | 2,1 / 51 / 134 GB; 0,3 / 7,1 / 18,6 h | spaltenweises Streaming 2..5 min je Tag; nie ganz in den RAM (58 Mio x 10 Spalten x 8 B ~ 4,6 GB) | Sandbox (streamend) |
| kline1d, kline1m, fundingRateAll | 0,04 / 0,28 / 0,04 GB gesamt [F] | - | Minuten | IK-03/04/05/07/09/10/11 vollstaendig (Zone X) | < 0,4 GB | Minuten | Sandbox |
| Katalog / gaps / Manifest | - | - | - | IK-08 alle Stroeme (S0) | ~0 | Minuten | Sandbox |

Summe Phase 1 (IK-01, IK-02, IK-06 mit 24 Tagen): ~105 GB, ~15 h Transfer; bei geteiltem Endpunkt ueber mindestens eine
Woche strecken, Reihenfolge IK-01 (Trades, billig, hoechste Entscheidungsrelevanz) -> Tardis-Inhaltsprobe -> IK-02.
Gerechnet wird in der Sandbox oder auf dem Nutzer-PC, nie auf dem Thin Client [F Verfassung, Abschnitt Marktdaten].

### 4.3 Sampling-Strategie (nie ganze Stroeme)

1. **Einheit** ist die Partition (Symbol-Tag); Zeitfilter und `columns=` immer; die Stichprobenliste wird
   deterministisch (Seed) erzeugt und **vor dem Laden** mit sha256 als Konto-Zeile in `state/KONTO_ZONE_X.md` gebucht.
2. **Schichtung:** Jahr x Vol-Terzil (aus kline1d/kline1m, Zone X) x Wochentagsklasse (Mo-Do / Fr / Wochenende - das
   Wochenende ist ein eigenes Liquiditaetsregime, 0,82x [F E-27]); 2 Tage je Monat und Symbol.
3. **Stress-Ueberstichprobe:** alle STRESS_ABS-Tage in Zone X (Zaehlung S0 zuerst), je Stress-Tag ein gematchter Ruhetag
   (gleicher Wochentag, gleiches Quartal); Gewichte fuer die Populationsschaetzung zurueckrechnen.
4. **Zweistufig (DEC-104 E5):** Pilotstichprobe (~20 Einheiten) schaetzt nur die Nuisance (Streuung), daraus mechanisch die
   Fallzahl der Hauptstichprobe; keine Effektgroesse aus dem Pilot.
5. **Tardis:** ein Tag fuer die C.8-Inhaltsprobe; dann je Halbjahr ein Stichtag plus die Stichtage nach den groessten
   Stressmonaten; alle 63 nur, wenn die Inhaltsprobe Pushdown nach Verfall/Instrument erlaubt.
6. **L2:** nur Tage mit vollstaendiger Sequenz (Sequenzbruch-Budget wie DEC-71); defekte Tage werden als Luecke benannt,
   nie interpoliert [F Verfassung, Abschnitt Marktdaten].

### 4.4 Nullwelten fuer die Konfirmation (Bausteine aus den Karten)

- **Klasse W:** Marktfaktor als MRW (IK-04) + k Residualfaktoren mit gemessener Stabilitaet (IK-05) + Alters- und
  Kohorten-Heterogenitaet (IK-07) + Delisting-Hazard (IK-09) + Funding-Mechanik (Totzone, Intervalle, Klemme; DEC-84,
  IK-11). Eine Nullwelt gilt fuer eine Familie erst, wenn sie die vorab gelisteten, einbehaltenen Invarianten der zweiten
  Zone-X-Haelfte innerhalb ihrer CI reproduziert ("Invarianten-Pass", kein Marktverdikt).
- **Klasse E:** Placebo-Kalender (bestehend) + Ereigniszeit-Uhr und Tageszeitprofil (IK-04) + Kurtosis-/Schiefe-Korrektur
  der Ereignis-CAR (IK-04).
- **Klasse P / Optionen:** Spot-Vol-Kopplung und Smile-Dynamik (IK-06) + Hedge-Kostenkurve (IK-03).
- **Zweck:** die OC je Registrierung (DEC-104 E8 (a)) und des Pakets (E0) mit realistischen Raendern und Clusterzahlen
  statt Normalnaeherung; daraus die Korrekturfaktoren in 0.3.

### 4.5 Datenqualitaet als Instrument

IK-08 macht aus "Ausfalltage sind bekannt" eine Zahl je Strom und Design: Verfuegbarkeit, gemeinsame Ausfallursachen,
Typ-B-Baender je Konstante, Kalibrierbuch der eigenen Prognosen. Das ist die Voraussetzung, dass der Feasibility-Rechner
(F3) und die Erreichbarkeitspruefung (E8 (d)) ohne Handarbeit laufen. Auf Live-Stroemen (OT, LQ, XV, Deribit-Orderbuch)
kostet das Ausfallmuster ~10 % eines 12-Monats-Fensters [R aus 125/139].

### 4.6 Ein Fund aus DEC-104: Brachland W1/W2-BTC/ETH-Mikrostruktur

[F] Zone X endet am 2024-06-30 (E4 (a)); BTC/ETH-Aggregate sind nur in Zone K prospektiv konfirmierbar (E4 (i)), mit der
einzigen Ausnahme A2. [R/V] Damit sind die BTC/ETH-Trades und -Orderbuecher 2024-07..2026-06 (grob 2 Symbole x 2 Jahre
x ~28 GB Trades [F DEC-96 N] plus L2 BTC bis 2025-08) fuer **jede Nicht-A2-Statistik weder explorierbar noch
konfirmierbar**. Fuer Renditestatistiken ist das gewollt (Vorwissen der Agenten, DEC-96 E1). Fuer Nicht-Rendite-
Mikrostruktur (Tradezahlen, Groessenverteilungen, Queue-Intensitaeten, Zeitstempel) ist der Schutzzweck schwach: die
Vol von W1/W2 ist ohnehin bekannt (DEC-95 E2) [F], und Aktivitaet traegt kaum Information ueber r_pre-Mittel [U].
**Vorschlag (Lockerung, Richtung Testbarkeit, Entscheider N):** Nicht-Rendite-Mikrostrukturstatistiken auf
W1/W2-BTC/ETH mit A2-Maske (4.7) als Zone X fuehren; Preis: weiteres Agentenwissen ueber W1/W2-Aktivitaet. Ohne
Entscheidung rechnen IK-01/IK-02 nur auf 2020..2024-06 (X) und 2026-07+ (K). Der Auftrag selbst ging von "BTC/ETH bis
2026-06 als agentenbekannte Aggregate in Zone X" aus - Brief und DEC-104 widersprechen sich hier.

### 4.7 Zonen-Hygiene fuer alle Karten

1. **Konto** vor jeder Zone-X-Abfrage (Familie, Statistik, Fenster, K, Code-Hash, Zweck); Ausgabe nur Schaetzer/CI/
   Ausschlussgrenze (DEC-104 E1/E4 (c)).
2. **A2-Maske** in Zone V und K: jede Intraday-Statistik auf BTC/ETH schliesst [07:00, 08:30) UTC an allen Tagen aus
   (A2-Fenster [07:30, 08:00) plus Placebo-Slot 08:00 Funding/Settlement). In Zone X ist die A2-Vorperiode freigegeben
   (E4 (a)); dort keine Maske, aber keine Ausgabe "Wochentagsklasse x Slot 07:30..08:00" unter einer fremden Familie -
   eine solche Zahl waere eine A2-Exploration und braucht ihre eigene Konto-Zeile (Familie A2, Selektions-K).
3. **Ausgabeform** fuer Nuisance-Werte nach DEC-103 N1 (2c) (Partition, keine geschachtelten Klassenstreuungen im
   oeffentlichen Repo); keine Marktniveaus im Konto.
4. **Familienzuordnung** vor der ersten Rechnung: IK-10 gehoert zur Renditefamilie (C.17-Liste des Piloten), IK-01/02/03/
   04/06 zur Familie "Kosten/Struktur", IK-05 zu "Querschnitts-Nuisance", IK-07/09 zu "Lebenszyklus (ohne Renditen)".

---

## 5. Negativliste: geprueft und verworfen

Kategorien: **D** = tot nach Kompendium D.x; **W** = unter der Wand ohne Messwert; **DF** = Daten fehlen irreversibel bzw.
im Siegel; **H** = Horizont falsch; **NF** = nicht falsifizierbar bzw. ohne Nullverteilung; **ER** = ohne
Entscheidungsrelevanz unter 3.1; **DUP** = bereits Feld/Exkurs/Kandidat.

| Nr | Methode / Idee | geprueft gegen | Kategorie | Grund (ein Satz) | Fundstelle |
|---|---|---|---|---|---|
| N-1 | Hawkes-Verzweigungsgrad als Schwelle oder Kritikalitaetssignal | D.2, C-14 | D, ER | Schwelle sechs Groessenordnungen unerreichbar; als reine Messung ohne Entscheidung unter 3.1 | D.2; FINAL_PRD 2.0 |
| N-2 | SIR-/Epidemie-Kontagion (Liquidationen, Listungswellen) | Exkurs S1 | D, DUP | R0 ist ein Verzweigungsgrad, also D.2 umbenannt | Exkurs-Synthese 3 |
| N-3 | Permutationsentropie, LZ-Komplexitaet als Signal | D.3, D.6 | D | PRE-Korrelation max 0,0145; Entropie-Momentum verliert auch ohne Gebuehren | H-06, CS-02 |
| N-4 | Kompressions-Effizienzindex als Regimevariable | - | ER | REZENZ-Operationalisierung ist Change-Point (DEC-58 E1 (h)); ein weiterer Index ist K-Inflation [U] | - |
| N-5 | Rekordstatistik als Stationaritaetstest | - | ER | durch EVT (IK-04) und Change-Point abgedeckt [U] | - |
| N-6 | Fruehwarnsignale (Critical Slowing Down) | Exkurs S2 | NF, ER | Literatur negativ; n_eff = T/w = 2 beim Default | Exkurs-Synthese 3 |
| N-7 | Strukturfunktionen als Gate; Lomb-Scargle/BLS-Periodensuche | Exkurs S3 | NF, W | Scheinbrueche im strukturellen Nulleffekt; Perioden kalendarisch bekannt; gerichtete Intraday-Nutzung 96 x 11 bp/Tag | Exkurs S3 |
| N-8 | Transfer-Entropie / Wavelet-Kohaerenz auf Tagesreihen ueber Assets | - | H, ER | nichtlineare Schaetzer auf 1.277 Punkten ohne Vorteil; die lineare Fassung ist IK-10 [U] | - |
| N-9 | Capture-Recapture verdeckter (RPI-)Liquiditaet | C-40 | ER, W | keine Kostenfolge fuer API-Taker erkennbar [V, Primaerquelle]; RPI-Kante selbstzerstoerend | FINAL_PRD 2.0, C-40 |
| N-10 | Settlement-Pinning (Spot nahe Max-OI-Strike am Verfall) | A2 | DUP (vertagt) | gleiches Ereignisfenster wie A2; W1/W2 sind fuer A2 blind -> erst nach A2-Klaerung; **vertagt, nicht verworfen** | DEC-104 E4 (a), E7 |
| N-11 | Tick-Size-Aenderungen als natuerliches Experiment | - | DF, H | 5 Symbole, wenige Ereignisse, Minutenhorizont; Tick-Size-Historie fehlt | Datenauftrag 6 |
| N-12 | Gestaffelte DiD / synthetische Kontrolle mit Binance-Assets | D.16, Exkurs S4 | D, DF | Binance-Alt-Historie fehlt (Archiv: 5 Symbole ab 2025/2026); Infrastruktur vor Signal | X-NEXP-3 |
| N-13 | Generatives Voll-Marktmodell ("digitaler Zwilling") | D.16 | D | Infrastruktur vor validiertem Signal; ersetzt durch minimale, validierte Nullwelt (IK-04) | PRD_ANALYSE 3, Review B-18 |
| N-14 | Tiefes Repraesentationslernen auf dem Trade-Tape (DAY-BRIDGE) als Registrierungsweg | D.16, DEC-57 | D, ER | GPU-Default 0; kein Tradability-Pfad; nur Zone-X-Exploration mit Konto | E-3, E.11 |
| N-15 | HMM/BOCPD als Signal | C-08 | D, DUP | Ockham-tot nach H-01; als Konditionierung = F11 | Kompendium 2.0 |
| N-16 | Gutenberg-Richter-b-Wert / ETAS als Zustandsvariable | C-15, F9 | DF, DUP | Liquidationen im Siegel; Groessenverteilung der Trades steckt als Invariante in IK-01 | - |
| N-17 | Liquidations-Kaskaden (Hawkes, Omori) | F9, D.2 | DUP, DF | bereits Feld F9; fast vollstaendig im Siegel | PRD_ANALYSE F9 |
| N-18 | Kalender-/Wochenperiodizitaet als Signal | R2-K-06, Welle 6 | W, ER | Nachweisgrenze 33 bp/Tag bzw. 113 bp | PRD 9.1 |
| N-19 | Anytime-valid e-Werte | Exkurs S2, DEC-104 | DUP | 3.1 waehlt GSD; ein zweites Regime waere ein offener Torpfosten | Exkurs-Synthese 3 |
| N-20 | TDA (persistente Homologie), RQA (Legacy m11/m12) | - | NF, ER | kein Mechanismus, keine Nullverteilung mit bekannter Erreichbarkeit; K-Inflation [U] | Legacy 1.0 |
| N-21 | Matched Filter im Verfallsfenster | Exkurs X-ASTRO-2 | DUP | A2-Nachbarschaft | Exkurs-Synthese 3 |
| N-22 | Vol-Prognose mit HF-Daten (HAR plus Features) als Vorsprung | H-02, H-11c, DEC-98 N5 | D | muss gedresste HAR schlagen; HF-RV aendert die VRP-Streuung nicht | B.9, B.10 |
| N-23 | RMT ueber Boersen (Fragmentierung) | D.10 | D | zweiter Eigenmodus voll delokalisiert (IPR ~1/6) | H-12 |
| N-24 | Hawkes-Endogenitaet auf Trades als Messprogramm | D.2 | ER | zulaessig ohne Schwelle, aber ohne Abnehmer: weder Kostenkurve noch Nullwelt braucht sie [U] | - |

---

## 6. Datenauftraege an Data-Harvest, die der Sweep neu begruendet (priorisiert)

Nur Auftraege, die der Sweep neu begruendet oder erweitert; die bestehende Liste der PRD-Analyse (Abschnitt 8) bleibt
gueltig. Charakter: Probe zuerst, dann Backfill; irreversible Stroeme benannt. Reihenfolge: Nr. 1 ist die billigste
und schaltet IK-06 frei; Nr. 2 und 3 sind die inhaltlich wichtigsten neuen Auftraege (IK-10/IK-11 bzw. IK-01).

| Prio | Auftrag | wofuer | Charakter |
|---|---|---|---|
| 1 | **Inhaltsprobe `tardis/options_chain`** (bestehend Prio 2) **erweitert:** Feldliste (Basiswert je Verfall, Open Interest je Instrument, Bid/Ask-IV, Greeks), Zeitaufloesung, Boerse(n), ob Zeilengruppen nach Verfall/Instrument gefiltert geladen werden koennen | IK-06 (Basis-Terminstruktur = F10-Einstiegsbasis), IK-03 (Gamma-Profile), Hinweis F8 (OI je Strike an 63 Monatsersten?) | Pruefung; nur Stichtage <= 2026-06-01 |
| 2 | **Index- und Mark-Preis-Tageskerzen (optional 1 h) aller linearen USDT-Perps ab 2021-01, inklusive Delisteter** (oeffentliche REST-Endpunkte [V, Nachladbarkeit Delisteter UNBELEGT]) | IK-10 (Stale-Close-Kontrolle), IK-11 (theta-Analogon), Funding-/Basis-Bein der L/S-Renditen in F1/F2/IK-10 (PRD_ANALYSE 4.15), IK-08 (Konsistenz) | neu; Probe, dann Backfill |
| 3 | **Tagesaggregate aus dem Bybit-Trade-Archiv fuer alle linearen Perps ab 2021**: Tradezahl, Buy-/Sell-Volumen, Groessenquantile (p50/p90/p99), Zahl der Preisaenderungen | IK-01 Querschnittsform der Invarianz (~500 statt 5 Symbole), IK-07, F4-Querschnitt | neu; Ableitung auf Data-Harvest-Seite (das Archiv der Boerse fuehrt Trades je Symbol [sek]; Machbarkeit [V]) |
| 4 | **L2-Vorextraktion fuer eine Stichtagsliste:** Top-10-Level im 1-s-Raster plus Sequenzbruch-Zaehlung, BTC/ETH 2023-01..2024-06, 40 Tage (Liste vom Orchestrator, Seed) | IK-02; senkt den Transfer von ~34 GB auf grob 1..3 GB [V] | neu; alternativ Nutzer-PC |
| 5 | **Ausfall- und Wartungsregister:** Protokoll des Live-Sammlers (Ursache des 14-Tage-Musters, Ausfallzeiten je Strom) und Wartungs-/Upgrade-Fenster von Bybit und Deribit | IK-08 (Ausfallbudget, gemeinsame Ursachen), natuerliche Experimente (N-11-Nachbarschaft) | erweitert PRD_ANALYSE Prio 9 |
| 6 | **Kontraktspezifikations-Historie** (tickSize, lotSize, maxLeverage, Risk-Limits, Funding-Kappe/-Intervall) ab 2021 aus Ankuendigungen; die taeglichen `rest.instruments`-Schnappschuesse (ab 2026-10-20) weiterfuehren | IK-07 (Spread-Normierung), IK-01 (Tick-Bindung am liquiden Ende), R-7 | Schnappschuesse irreversibel; Historie Probe |
| 7 | bestehend Prio 1 (Marktkapitalisierung/Spot-Volumen) und Prio 4 (OI aller Perps): **zusaetzlich begruendet** durch IK-05 (Groessenfaktor), IK-07, IK-09 (Kovariaten) | siehe PRD_ANALYSE 8 | bestehend |

Nicht noetig nach diesem Sweep: L3-Orderbuch (oeffentlich nicht vorhanden [V]; IK-02 arbeitet mit Typ-B-Band),
Binance-Alt-Panel (nur fuer eine Kreuzvenue-Invarianz; Bilanz B-6 bleibt), HF-RV (DEC-98 N5).

---

## 7. Kurzfassung an den Orchestrator (12 Zeilen)

1. Sweep 37 Methodenfamilien x 13 Stromgruppen: Naturwissenschafts-Methoden tragen auf unseren Daten Mess-, Kosten- und Nullwelt-Programme, kaum neue Praemien; 11 Karten (9 Messprogramme, 2 Hypothesen), Platz 12 bewusst frei.
2. Top 1 - Kostenkurven IK-01 (Taker-Impact, Kyle-Obizhaeva-Invarianz) und IK-02 (Maker-Queue): DEC-104 E3 macht die SESOI zur Kostenkurve, die es nicht gibt; Taker- gegen Maker-SESOI im Tages-Querschnitt 0,0169 gegen 0,0062.
3. Top 2 - IK-04 Skalengesetze/schwere Raender/MRW-Nullwelt fuer die OC vor Kohorte 1: Kurtosis 5..10 bei 40..52 Clustern hebt die MDE um 1,14..1,38, Schiefe -0,5..-1 das alpha 0,0025 auf ~0,004..0,006 (Tests mit geschaetzter SE; Permutationstests nur Power).
4. Top 3 - IK-05 RMT-Faktor-Null (S-4 instrumentiert): die 2,5-fache IC-Streuung braucht einen Eigenwert >= 6 gegen MP-Kante 2,0..2,6 - in Zone X entscheidbar.
5. Groesste Luecke der Felderliste: F1..F12 sind im Kern Erst-Moment-Hypothesen auf ungemessenen Zweit-Moment- und Kosteneingaben (nur F4 hat eine Invarianz); die 1,07 TB koennen Tagesmittel nicht beschleunigen (Drift-SE 19,5 % p.a. nach 6,6 J, abtastratenunabhaengig), wohl aber Kosten, Nullwelten, Invarianten.
6. Sofort in Zone X: IK-04/05/07/09/10/03/11 auf kline1d/kline1m/Funding (Minuten CPU); IK-01 auf ~20 GB Trades (2,7 h); IK-02 auf ~34 GB L2 (Nutzer-PC); IK-08 als S0 auch im Siegel; IK-06 erst nach Tardis-Inhaltsprobe.
7. Innerhalb 12 Monaten konfirmierbar: IK-10 Price Delay (Zone V, Q1 2027; MDE 0,015..0,021 gegen Taker-SESOI 0,017 - an der Kante), IK-09 Delisting-Hazard, IK-07 Altersprofil, IK-01/IK-02-Gesetze (TOST; wo K-Monate schon geoeffnet sind, bis 08..10/2027), IK-06 Spot-Vol-Beta (Zone K bis 07/2027).
8. Datenfund: Tardis-Kette = 58 Mio Zeilen je Stichtag (Intraday), 63 Zone-X-Tage; implizite Basis-Terminstruktur seit 2019 (+-1..6 bp p.a.) = F10-Einstiegsbasis [V bis Probe].
9. Neue Datenauftraege: Index-/Mark-Kerzen aller Perps; Tagesaggregate (Tradezahl) aus dem Trade-Archiv; Tardis-Probe mit Feld-/Pushdown-Fragen; L2-Vorextraktion; Ausfall-/Wartungsregister; Spezifikations-Historie.
10. Konflikt Brief/DEC-104: W1/W2-BTC/ETH-Mikrostruktur ist fuer Nicht-A2-Statistiken weder X noch konfirmierbar (Brachland); Freigabe mit A2-Maske waere Lockerung, N.
11. Neu fuer PRD v3: TOST-Form fuer Gesetzeshypothesen; Enrichment fuer Querschnitt (N); F1 und IK-10 teilen ggf. den einen V-Blick ihrer Familie.
12. Nicht beurteilbar: alle neuen Streuungs-Nuisancen ([V], in X zu messen), Tardis-Feldinhalt, Tradezahl im Panel, Nachladbarkeit Index-Kerzen, Literaturwerte ([sek]).

---

## Anhang A: Rechenweg (`scripts/sweep_calc.py`, Ausgabe `sweep_calc.out`)

- **A Datenvolumen:** MB je Partition = GB/Partitionen; Byte je Zeile = GB/Zeilen; Transfer = GB / 2 MB/s. Inventar-Zahlen [F].
- **B Tages-Querschnitt (IK-10):** SD(IC_t) = 2,5/sqrt(K-1) [V]; Zone V: exakte bivariate Normalrechnung fuer
  P(Z_pool(730) > 2,807 und Z_W2(365) > 1,645) = 0,80 (Korrelation sqrt(1/2)); Zone K: 1,008 x 3,649 x SD/sqrt(365)
  (OBF-Inflation [F PRD_ANALYSE 6]); Zone X: (1,645 + 0,842) x SD/sqrt(1.277), Ausschlussgrenze 1,645 x SD/sqrt(1.277);
  SESOI = 2 x c_RT x Umschlag / (3,51 x 370 bp) [3,51 F PRD 9.2; 370 bp V].
- **C Delisting-Hazard (IK-09):** Raten aus 306 / 5,83 Jahre, 800 / 5,83; SE(log HR je SD) = sqrt(deff/D) (Schoenfeld-
  Naeherung); MDE = 1,008 x 3,649 x SE.
- **D APC (IK-07):** Kontrast zweier Altersklassen, SE = s x sqrt(2 deff / n), MDE = 3,649 x SE.
- **E RMT (IK-05):** MP-Kante (1 + sqrt(K/T))^2; Var(IC_t)(K-1) = 1 + Summe (x'l)^2/(K-1); Eigenwert = 1 + |l|^2 bzw.
  1 + 5,25/cos^2 fuer SD-Verhaeltnis 2,5.
- **F Schwere Raender (IK-04):** Var(s^2)/sigma^4 = 2/(n-1) + kappa/n, df_eff = 2 / Var(s^2)/sigma^4; t-Kritik; Edgeworth
  P(T > z) ~ alpha - n^(-1/2) (g/6)(2 z^2 + 1) phi(z) [sek: Hall 1987].
- **G Vol-Zeit-Gewichtung (IK-04):** zwei gleich grosse Regime mit Varianz v und r v: gleichgewichtet (1 + r)/2,
  invers-varianzgewichtet 2/(1 + 1/r).
- **H Leland (IK-03):** dsigma = kappa x E|z| / sqrt(dt), E|z| = sqrt(2/pi) (Gauss), t4 auf Einheitsvarianz 0,7071.
- **I/J/K Impact und Invarianz (IK-01):** I = Y sigma_d sqrt(Q/V) [Y sek]; Exponent = ln(19,1)/ln(394); TOST-Marge
  = (z_0,9975 + z_0,90) x SE; Steigungs-SE = s_res / (sd(log W) sqrt(D)).
- **L Put-Call-Paritaet (IK-06):** Forward-Fehler = sqrt(2) x 0,07 VP x 5,28 bp/VP je Paar; annualisiert / (T/365).
- **M Merton:** Drift-SE = sigma_a / sqrt(T); relative Varianz-SE = sqrt((2 + kappa)/N).
- **N Zeitlinie:** DEC-104 E0/E4 (f): Kohorte 1 = 2027-01-01; K-Fenster 2026-07-01..2027-06-30.

## Anhang B: Belegstatus (alle [sek], aus dem Gedaechtnis, Primaerquelle zu beschaffen)

Kyle/Obizhaeva 2016 (Econometrica 84); Toth et al. 2011 (Phys. Rev. X 1); Patzelt/Bouchaud 2018 (Phys. Rev. E 97);
Bouchaud/Bonart/Donier/Gould 2018 (Trades, Quotes and Prices, CUP); Cont/Stoikov/Talreja 2010 (Operations Research 58);
Huang/Lehalle/Rosenbaum 2015 (JASA 110); Leland 1985 (J. Finance 40); Hoggard/Whalley/Wilmott 1994; Bertsimas/Kogan/
Lo 2000 (JFE 55); Clark 1973 (Econometrica 41); Ane/Geman 2000 (J. Finance 55); Bacry/Delour/Muzy 2001 (Phys. Rev. E
64); Kantelhardt et al. 2002 (Physica A); Mantegna/Stanley 1995 (Nature 376); Cont 2001 (Quant. Finance 1);
Gopikrishnan et al. 1998 (Eur. Phys. J. B 3); McNeil/Frey 2000 (J. Empirical Finance 7); Laloux et al. 1999 (PRL 83);
Plerou et al. 2002 (Phys. Rev. E 65); Biroli/Bouchaud/Potters 2007 (Acta Phys. Pol. B 38); Mantegna 1999 (Eur. Phys.
J. B 11); Onnela et al. 2003 (Phys. Rev. E 68); Eisler/Bartos/Kertesz 2008 (Adv. Phys. 57); Filimonov/Sornette 2012
(Phys. Rev. E 85); Hardiman/Bercot/Bouchaud 2013 (Eur. Phys. J. B 86); Lillo/Mantegna 2003 (Phys. Rev. E 68); Petersen
et al. 2010 (Phys. Rev. E 82); Ogata 1988 (JASA 83); Wergen 2013 (J. Phys. A 46); Schreiber 2000 (PRL 85); Dimpfl/Peter
2013; Bandt/Pompe 2002 (PRL 88); Giglio et al. 2008 (EPL, zu pruefen); Gencay/Selcuk/Whitcher 2002 (Buch); Hasbrouck
1993 (RFS 6); Ait-Sahalia/Mykland/Zhang 2005 (RFS 18); Hou/Moskowitz 2005 (RFS 18); Lo/MacKinlay 1990 (RFS 3); Billio et
al. 2012 (JFE 104); He/Manela/Ross/von Wachter 2022 (Fundamentals of Perpetual Futures, Arbeitspapier); Gneiting/
Raftery 2007 (JASA 102); JCGM 100:2008 (GUM); Klein/Roodman 2005 (Annu. Rev. Nucl. Part. Sci. 55); Gross/Vitells 2010
(Eur. Phys. J. C 70); Read 2002 (J. Phys. G 28); Feldman/Cousins 1998 (Phys. Rev. D 57); Jennison/Turnbull 2000 (Buch);
Schuirmann 1987 (J. Pharmacokinet. Biopharm. 15); Lakens 2017 (Soc. Psychol. Personal. Sci. 8); Simon/Simon 2013
(Biostatistics 14); Woodcock/LaVange 2017 (NEJM 377); O'Hagan/Stevens/Campbell 2005 (Pharm. Stat. 4); Hobbs et al.
2011 (Biometrics 67); Fine/Gray 1999 (JASA 94); Robins/Finkelstein 2000 (Biometrics 56); Holford 1983 (Biometrics 39);
Yang/Land 2013 (Buch); Corwin/Schultz 2012 (J. Finance 67); Imbens/Angrist 1994 (Econometrica 62); Abadie et al. 2010
(JASA 105); Chao 1987 (Biometrics 43); Hill 1973 (Ecology 54); Scheffer et al. 2009 (Nature 461); Dwork et al. 2015
(Science 349); Huber 1964 (Ann. Math. Stat. 35); Theil 1950 / Sen 1968; Merton 1980 (JFE 8); Hall 1987 (Ann. Probab.
15); Bakshi/Kapadia/Madan 2003 (RFS 16). Boersenregeln zu Delisting-Kriterien, RPI-Berechtigung und REST-Endpunkten
fuer Index-/Mark-Kerzen: Primaerquelle (Boersen-Dokumentation) zu beschaffen.

## Anhang C: Was NICHT folgt

- Kein Verdikt, keine Registrierung, keine Effektgroesse; alle Zahlen sind Aufloesungsgrenzen, Kostengroessenordnungen
  oder Korrekturfaktoren aus Akten-Nuisance mit markierten Annahmen.
- Keine Karte ist eine Registrierungsempfehlung; unter DEC-104 E0 kommt Kohorte 1 erst nach der OC des Pakets.
- Die Kostenkurven (IK-01..IK-03) aendern kein bestehendes GL; A1 und VRP bleiben "strukturell nicht testbar" (E3 (e)).
- Der Brachland-Vorschlag (4.6) und Enrichment (3.13) sind Lockerungen und Nutzerfragen.
- Literaturwerte sind Orientierung [sek], nie Prior; Prior unter 3.1 nur selektionsbereinigt aus Zone X (E3 (c)).
- Nichts hier betrifft Kapital, Steuer oder Ausfuehrung; kein Live-Order-Code.
