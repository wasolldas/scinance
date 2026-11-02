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
