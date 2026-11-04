# Fensterregister (Zonen, Vorwissens-Klassen, Bedarfsbilanz) - DEC-104 E4 (Stand 2026-11-02, von Hand bis F2)

> Eine Datei, eine Wahrheit fuer die Frage "welche Daten darf welche Statistik wann sehen". Append-only in den
> Tabellen "Oeffnungen"; die Zonen-Tabelle wird je Quartalsstichtag fortgeschrieben (datiert). Keine Marktwerte.

## 1. Zonen (DEC-104 E4 (a), (b))

| Zone | Zeitraum (Stand 2026-11-02) | Regel | Naechste Aenderung |
|---|---|---|---|
| X Exploration | alle Daten vor 2024-07-01 (Panel ab 2021-01, BTC/ETH-Minuten ab 2020-03/2021-03, A2-Vorperiode 2021-03-24..2024-05-31, Pilotabschnitt 2022-04-18..2024-06-24) | frei und wiederholt, nur mit Konto (`KONTO_ZONE_X.md`); Ausgaben Schaetzer/CI/Ausschlussgrenze, nie Verdikt | 2027-07-01: V-Quartale aelter als 36 Monate wandern nach X |
| V Validierung | W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-28 | blind fuer Klasse W (fm8 ungeoeffnet; rev1 in W2 vorbelastet, GL-036 (4)) und A2 (Disziplin, DEC-103 N1 (2)); genau ein vorab registrierter Blick je Familie und Kohorte; nur ungeoeffnete Quartale | 2027-07-01: 2026-Q3 wandert aus K nach V |
| K Konfirmation | ab 2026-07-01 (Siegel DEC-96 E3), heute 2026-07-01..2026-11-02 | versiegelt fuer alle Statistiken ausser Zaehlungen S0; gruppensequentielle Blicke nur fuer registrierte Hypothesen der Kohorte | fuellt sich bis 2027-06-30 auf 12 Monate; danach rollierend |

Kohorten-Stichtage: 2027-01-01 (Kohorte 1), danach erster Tag jedes Quartals.

## 2. Vorwissens-Klassen je Datenfamilie (DEC-104 E4 (i))

| Datenfamilie | Vorwissen der Agenten (Akte) | Konfirmation erlaubt | Exploration (Zone X) |
|---|---|---|---|
| BTC/ETH-Aggregate: Tages-/Wochenrenditen, RV, DVOL/IV, Funding BTC/ETH | W1/W2-RV bekannt (DEC-95 E2); 2.0 sah Mikrostruktur bis 2026-07-04; H-27-Formation; A2-Nuisance der Vorperiode veroeffentlicht (B-2-Kanal) | **nur prospektiv in Zone K**; Ausnahme A2 r_pre Freitage auf W1/W2 als registrierte Statistik (Disziplinsetikett) | ja, mit Konto |
| Panel-Querschnitte (lineare USDT-Perps, Tages-/Wochenrenditen, Charakteristiken) | Pilot 2022-04..2024-06 fuer Renditefamilie (mom/rev, GL-035); H-33 nicht gelaufen | W1/W2 (Zone V) blind, soweit nicht C.17-verbraucht; Zone K | ja, mit Konto (Renditefamilie: K kumuliert ab Pilot) |
| Funding aller Perps, OI, Umsatz (Nuisance-Zensen) | V-1/V-2-Zensen bis 2026-06 (Zaehlungen, Streuungen) | Zone V nur fuer nicht-outcome-beruehrende Statistiken; Zone K prospektiv | ja |
| Optionskette (tardis monatlich), Settlements, Deliveries | Kalender/OI-Zaehlungen bis 2026-06-30 (DEC-98 N7) | Zone K prospektiv; Stichtage ab 2026-07 nur S0 | ja (Stichtage <= 2026-06-01) |
| Live-Stroeme ab 2026-06 (Options-Ticker, Liquidationen, Orderbuecher) | nur Katalog-Zaehlungen | vollstaendig Zone K; vor Kohorte 1 nur S0 | nein (kein X-Anteil) |
| Trades/Orderbuecher 2020-2026 (5 Symbole) | 2.0-Mikrostruktur bis 2026-07-04 | Zone K prospektiv fuer Tagesaggregate (BTC/ETH-Aggregat-Regel) | ja fuer Tage vor 2024-07-01 (Kostenmodelle, Invarianten, Nullwelten) |

## 3. Bedarfsbilanz der knappen Blinddaten (PRD_ANALYSE Abschnitt 6; fortzuschreiben je Kandidat)

| Ressource | Nachfrager | Status |
|---|---|---|
| Zone V (W1/W2), Panel-Querschnitte | F1 Tages-Reversal (Gap), A3-fm8, H-33-artige Reversals, F5-Ereignisse bis 2026-06 | gemeinsame Registrierung in Kohorte 1 mit BY; rev1 in W2 vorbelastet |
| Zone V (W1/W2), BTC/ETH r_pre Freitage | A2 (einzige zugelassene BTC/ETH-Aggregatstatistik auf V) | Feasibility unter 3.1 nach OC (DEC-104 E7 (d)) |
| Zone K ab 2026-07-01 | VRP (strukturell geschlossen, E3 (e)), A1 (strukturell geschlossen), R-1 Reversal prospektiv (74..113 Wochen je Fenster), F8 GEX, F9, F2/F3/F4/F6-Tageszeitreihen, H-21 (2.0, Lueckenliste) | Kohorte 1 teilt die Scheiben; GSD-Blicke je Quartal |

## 4. Oeffnungen (append-only; Nachtrag des Konto-Inventars folgt)

| Datum | Statistik | Fenster | Zone | Registrierung / Zensus | Quelle (C.17-Liste) |
|---|---|---|---|---|---|
| (Inventar aus den C.17-Listen aller Registrierungen folgt mit PRD_ANALYSE 9.2 Nr. 6) | | | | | |

---

## Nachtrag 2026-11-02 (Konto-Inventar; DEC-104 Nachtrag 1)

Die vollstaendige Inventur aller bisher geoeffneten Statistik-x-Fenster-Paare steht in `state/KONTO_INVENTAR_2026-11-02.md`
(72 Zeilen O-001..O-133, O-901..O-905, O-980 mit Fundstellen; Verdichtung je Datenfamilie und Zone; kumuliertes K;
21 Unklarheiten W-01..W-21). Sie ist ab heute die **massgebliche Oeffnungsliste**; die C.17-Listen kuenftiger
Registrierungen zitieren ihre Zeilennummern. Abschnitt 4 oben wird nicht mehr fortgeschrieben.

### 5. Legende (W-17)

S0..S3 bezeichnen in diesem Register und in DEC-104/105 **Statistikklassen** (S0 Zaehlung, S1 Streuung ohne Mittel, S2 Screen
mit Mittel oder Vorzeichen, S3 Gate-Bit); in neuen Texten als **SK0..SK3** schreiben. Nicht zu verwechseln mit den
Praemien-Definitionen S1/S2/S3 (H-27/HFRV), den SE-Lesarten S1..S3 (H-32 EV-5), den Befunden S-1..S-6 der Edge-Inventur und
den Scouts S1-S5 des Wissenschafts-Exkurses. Zone K (DEC-104) heisst in ARCHITEKTUR_AUTOMATION "C".

### 6. Zonen je Datenfamilie, korrigiert (W-02, W-03, W-04, W-08; DEC-104 Nachtrag 1 (3))

| Datenfamilie | Zone X | Zone V | Zone K rein ab | Begruendung (Inventar) |
|---|---|---|---|---|
| F1 BTC/ETH-Aggregate (Renditen, RV, DVOL/IV, Funding BTC/ETH, Mid-Bewegung) | bis 2024-06-30 (frei mit Konto) | 2024-07-01..2026-06-30 (Tage) bzw. ..2026-06-28 (Wochen); **verbraucht** fuer Vol/RV/VRP (DEC-96 E1; H-11/H-11c RV-Prognosen O-116/O-117), fuer Stunden-/Tagesvorzeichen der 2.0-Statistiken (H-19/H-20/H-22/H-24) und fuer die Funding-Lage (A1-Formation O-030); blind nur fuer A2 r_pre (Disziplin) | **2026-10-01** (letzte Oeffnung: Mid-Bewegung WP-10(B) bis 2026-09-24, O-013; Funding-Lage bis 2026-09-14, O-002/O-011; H-24 W-R2 bis 07-31; 2.0-Gate-Bits bis 07-19; WP-6-Text 2026-08-19, O-133) | Abschnitt 2 F1/K des Inventars |
| F2 Panel-Querschnitte (Tages-/Wochenrenditen, Charakteristiken) | bis 2024-06-30; Renditefamilie fm8/Roh-IC durch Pilot gesehen (O-027, K = 4) | 2024-07-01..2026-06-28 **blind durch Disziplin** (IC-Rohserien berechnet, versiegelt, ungelesen, O-010/O-014); fuer fm8-Reversal-Varianten vorbelastet durch die Persistenz-Null (O-020; W-13 konservativ: alle rev-Varianten, nicht nur rev1) | **2026-07-01** (blind; Disziplin fuer die K-Wochen der versiegelten IC-Serien bis 2026-09-14; Survivorship-Differenz-IC O-014 als S2 offengelegt) | Abschnitt 2 F2 |
| F3 Funding aller Perps, OI, Umsatz | bis 2024-06-30 | V: Funding-Lage formationsseitig verbraucht (O-030, O-011); OI/Umsatz S0/S1 | **2026-09-15** fuer Funding-Lage (O-002/O-011); OI/Umsatz 2026-07-01 | Abschnitt 2 F3 |
| F4 Optionskette, Settlements, Deliveries | bis 2024-06-30 (Stichtage <= 2026-06-01 fuer tardis) | blind (S0/S1-Proxys offengelegt, O-051/O-052) | **2026-07-01** (Vorbehalt WP-5-Snapshot 2026-08-24, O-132 UNKLAR) | Abschnitt 2 F4 |
| F5 Live-Stroeme ab 2026-06 | kein X-Anteil | 2026-06-16..06-28 blind | **2026-07-01** (Vorbehalt WP-6-Text O-133) | Abschnitt 2 F5 |
| F6 Trades/Orderbuecher 5 Symbole | bis 2024-06-30 (2.0-Statistiken gesehen, O-122..O-125) | verbraucht fuer 2.0-Mikrostruktur (O-101..O-121, O-013) | **2026-10-01** fuer Mikrostruktur-Statistiken (WP-10(B) bis 09-24); Tagesaggregate wie F1 | Abschnitt 2 F6 |

Folge fuer Kohorte 1 (2027-01-01): Fuer F1/F3/F6-Statistiken beginnt das erste reine K-Quartal am 2026-10-01; ein 12-Monats-
K-Fenster endet dort am 2027-09-30, nicht am 2027-06-30. Zone V fuer Tagesstatistiken endet am 2026-06-30 (W-02); die Tage
2026-06-29/30 gehoeren zu V, nicht zu K.

### 7. Berechnet, versiegelt, ungelesen (W-11; Lesestatus je Datei zu dokumentieren)

| Datei(en) | Inhalt | Fenster | Status |
|---|---|---|---|
| `state/runs/weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv` | WP-7-IC-Rohserien, 271 Wochen | 2021-03..2026-09-14 (X, V, K) | versiegelt (CLAUDE.md), ungelesen laut Akte; Waechter nur Disziplin |
| `state/runs/wp13a_*_L_window_sealed.json` (7) | L-IC-Details | 2021-03-01..2024-06-30 (X) | versiegelt, ungelesen |
| IV-RV- und DVOL-Niveau-Serien (H-27-Vorarbeit) | Tages-CSV | bis 2026-07-31..08-13 (V, K) | tracked, laut Akte ungelesen; Lesestatus teils undokumentiert (O-040ff) |
| `h32_pilot_*_P_ic_weekly.csv` | Pilot-Wochenreihen | 2022-04-18..2024-06-24 (X) | tracked; Ergebnisse gelesen (GL-035) |

### 8. Kumuliertes Selektions-K (Stand 2026-11-02; Inventar Abschnitt 3)

F-XSEC1 7 (0 gerechnet); F-H32 4 (4 Pilot, Zone X); H-33 3 (0); F-WEEK m = 0 (Doppelausweis 11); A1, H-27, A2 je 0;
Renditefamilie Panel-Querschnitt kumuliert: 4 Outcome-gerechnete Varianten (Pilot), 14 benannte. Zone-X-Konto unter DEC-104: 0.

## Nachtrag 2026-11-02 (abends): Fremdoeffnung und Offenlegung (Pruefung der Nutzer-Konzepte)

| Nr | Datum | Statistik | Fenster | Zone | Art | Quelle | Bemerkung |
|---|---|---|---|---|---|---|---|
| O-981 | 2026-11-02 | Anzahl/Mittel/Maximum/Quantil/b-Wert der BTCUSDT-Liquidationen eines Tages; Payload-Beispiele mit Zeitstempeln und BTC-Preisniveaus | ein Tag August 2026 (K); ein Tag Ende W2 (V) | K, V | SK2-nah (Fremdquelle, Echtheit [V]) | Nutzer-Eingabe research_seismology.md (nicht im Repo); `state/PRUEFUNG_PHYSIK_KONZEPTE_2026-11-02.md` Abschnitt 4 | Oeffnung durch Fremdquelle (Praezedenz DEC-97 A-3); Tag auf C.17-Liste von IK-12 und BTC-Renditestatistiken; keine Rohwerte im Repo |
| O-982 | 2026-11-02 | Namenssuche (grep -l) ueber `state/runs/*_L_window_sealed.json` | - | - | keine Oeffnung (0 Treffer, kein Inhalt) | Review-Agent, Offenlegung | dokumentiert; Suchen kuenftig mit `--exclude-dir=runs` |
| O-983 | 2026-11-03 | Zeilenzahlen je Tag (Quantile ueber Tage) der `allLiquidation`-Partitionen, 5 Symbole; Parquet-Metadaten (Zeilenzahl, Schema) je eines Stichtags tardis/options_chain (2026-06-01), deribit/publicTrade (2026-06-30), allLiquidation BTCUSDT (2026-10-31), rest.deliveryPrice (2026-09-25) | 2026-06-16..2026-10-31 (K) | K | SK0 (Zaehlung) | Orchestrator, `scripts/sk0_probe.py` | Aktivitaets-Stellvertreter in Zone K (DEC-97 A-3): Tagesquantile nicht veroeffentlicht (nur Scratchpad); keine Werte, keine Vorzeichen |

## Nachtrag 2026-11-04 (DEC-107): P-13 Lockerung, Zonen-Ausnahme fuer Mikrostruktur-Zaehlgroessen; Stabilitaetstest statt Screen

### 9. Zonen-Ausnahme P-13 (DEC-107 (4); Etikett Lockerung, Entscheider N, Richtung Testbarkeit)

| Datenfamilie | Zeitraum | Statistiken (erlaubt) | Zone | Auflagen |
|---|---|---|---|---|
| BTC/ETH-Mikrostruktur (`bybit/publicTrade`, `bybit/orderbook`, Tardis-Trades/-Buecher) | 2024-07-01..2026-06-30 (W1/W2) | **Nicht-Rendite-Zaehl- und Formgroessen:** Tradezahlen je Intervall, Groessenverteilungen (Clauset-Protokoll), Queue-Intensitaeten, Wartezeiten zwischen Trades/Orders, Zeitstempel-Statistiken, Tiefe in Stueck je Preisstufe relativ (ohne Preisniveau) | **X** (Exploration mit Konto, nie Verdikt) | **A2-Maske:** Freitags-Slots 07:30-08:00 UTC ausgeschlossen (PRD_ANALYSE Nachtrag 1 (10)); Statistikklasse nur SK0/SK1; Konto-Eintrag `KONTO_ZONE_X.md` je Statistik mit Code-Hash; C.17-Eintrag; **verboten:** jede Groesse mit Rendite, Preisniveau, Vol oder Vorzeichen einer Preisaenderung als Eingang (bleibt Zone V blind, Abschnitt 1/6) |

Zweck: Kostenkurven IK-01 (Taker-Impact) und IK-02 (Maker-Queue) auf dem der Konfirmation naechsten Fenster. Preis
(offengelegt): weiteres Agentenwissen ueber W1/W2-Aktivitaet (Schutzzweck schwach, weil die W1/W2-Vol bekannt ist, DEC-95 E2).
Abschnitt 6 (Zone K rein je Familie) bleibt unveraendert; Abschnitt 2 (Vorwissens-Klasse BTC/ETH-Aggregate "nur prospektiv")
gilt fuer Renditegroessen fort.

### 10. Konfirmationsregel an den Blicken (DEC-107 (1))

Der REZENZ-Screen (DEC-104 E2) ist durch den registrierten Stabilitaetstest ersetzt: an jedem Wirksamkeits-Stopp mit aelterem
Teil wird "juengster Teil (12 Monate / vier Quartale) faellt nicht ab" einseitig bei 0,05 (Welch-t) geprueft; Verwerfung =
FAIL (terminal). Bei <= 12 Monaten Konfirmationsdaten entfaellt der Test. Pflicht-OC-Zeile je Registrierung: P(PASS bei Effekt
nur im aelteren Teil, 1 MDE). Herleitung: `state/herleitung_stabilitaetstest/`.
