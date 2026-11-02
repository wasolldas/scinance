# Auftrag: Systematischer Methoden-Sweep "Naturwissenschaft und Technik auf grosse Tradingdaten" (2026-11-02)

Rolle: Grundsatzanalyst (Herleitung). Du schreibst Volltexte in Dateien; an den Orchestrator geht eine Kurzfassung
(<= 12 Zeilen). Du aenderst nichts im Repo, committest nichts, rechnest keine Marktdaten, oeffnest keine Siegeldatei.

## Warum dieser Auftrag

Die PRD-Gesamtanalyse vom 2026-11-01 (`scinance3-impl/state/PRD_ANALYSE_2026-11-01.md`) hat zwoelf Forschungsfelder
F1..F12 tabelliert. Der Nutzer fragt zu Recht: "Haben wir den Auftrag abgearbeitet, nochmal komplett neue
Forschungsansaetze abzugrasen?" Ehrliche Antwort des Orchestrators: nein, nicht systematisch. F1..F12 sind
hypothesengetriebene Finanzfelder, die in das heutige Klassenschema (P/W/E) passen. Die Grundidee des Programms -
Erkenntnisse und Methoden aus Naturwissenschaft und Technik auf die grossen Datenmengen des Data-Harvest-Archivs
anzuwenden - wurde nur in einer Liste "fehlender Instrumente" (PRD_ANALYSE Abschnitt 3) angerissen. Dieser Auftrag
holt das nach: ein **systematischer Sweep** Methodenfamilie x Datenstrom x Horizont, mit ehrlicher Bewertung.

## Rahmen (bindend)

- Verfassung 3.1 ist am 2026-11-02 vom Nutzer als Paket angenommen (PRD_ANALYSE Abschnitt 9.1, P-1..P-7 mit den
  Default-Vorschlaegen): Messinstitution (Schaetzer, CI, Ausschlussgrenze als Pflichtausgabe); Fehlerbudget mit festem
  alpha je Test 0,0025 (gepoolt + REZENZ-Screen); SESOI statt Literatur-Punktprior, Literatur als Etikett, UNBELEGT
  symmetrisch; Drei-Zonen-Datenregime (Zone X Exploration mit Konto auf der Vorperiode, Zone V Validierung, Zone K
  versiegelte Konfirmation mit gruppensequentiellen Blicken, Kohorten-Stichtage); nuisance-adaptive Designwahl;
  REZENZ als pruefbare Hypothese; A2-Zuordnung ueber die exakte Bedingung. **Unveraendert:** Blind-Siegel DEC-96 E3
  (keine BTC/ETH-Rendite-/Vol-Statistik ab 2026-07-01 ausser Zaehlungen S0), W1/W2 (2024-07..2026-06) bleiben blinde
  Klasse-W-Fenster, Pilotabschnitt 2022-04..2024-06 ist fuer die Renditefamilie verbraucht (C.17), Vorwissens-Regel
  (BTC/ETH-Aggregate nur prospektiv konfirmierbar), Kompendium C.1..C.19 und D.1..D.17, "kein Live-Order-Code", Wand
  als Etikett (C.2).
- Zone X erlaubt heute: jede Explorationsmessung auf der Vorperiode (Panel 2021-01..2024-06 ohne Pilot-Verbrauch fuer
  Renditefamilien; BTC/ETH bis 2026-06 als agentenbekannte Aggregate), Ausgaben als Schaetzer mit CI, nie Verdikt,
  jede Abfrage im Konto. Das ist der Hebel, den dieser Sweep nutzen soll: **was koennen wir ab morgen messen und
  lernen**, und was davon fuehrt zu registrierbaren, zeitnah konfirmierbaren Hypothesen?
- Bisher versucht (nicht wiederholen, aber als Vergleichsbasis): 2.0 H-01..H-26 (Mikrostruktur, Sekunden/Minuten;
  `scinance2-impl/state/PROGRAM_FINAL_REPORT.md`, Kompendium D), 3.0 A1..A5, H-27..H-33, Felder F1..F12.

## Pflichtlektuere (Pfade unter /home/user/scinance/)

1. `scinance3-impl/state/PRD_ANALYSE_2026-11-01.md` (vollstaendig; Abschnitte 3, 4, 5, 6, 9 genau).
2. `scinance3-impl/state/prd_analyse_2026-11-01/KONZEPT_UND_FORSCHUNGSFELDER.md` (T-1..T-9, Felder, Anhaenge).
3. `scinance3-impl/state/prd_analyse_2026-11-01/DATENINVENTAR_2026-11-01.md` (29 Stroeme; was wir haben).
4. `scinance3-impl/state/prd_analyse_2026-11-01/EDGE_INVENTUR.md` (Abschnitt 0, Rangliste, S-1..S-6).
5. `scinance3-impl/survey/ERKENNTNIS_KOMPENDIUM.md` (Abschnitte C und D: Lehren und tote Richtungen).
6. `scinance3-impl/CLAUDE.md`, `scinance3-impl/PRD_SCINANCE3.md` Par. 1-3 (Mission, Klassen, Pflichtzeilen).
7. `scinance2-impl/state/PROGRAM_FINAL_REPORT.md` (was 2.0 mit Mikrostruktur gelernt hat).
8. `scinance3-impl/state/prd_analyse_2026-11-01/REGELN_UND_LESELISTE.md` (Regeln aller Analysen).
Nicht oeffnen: `scinance3-impl/state/runs/*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`.
Kein Zugriff auf den Harvest-Client, keine Daten laden. Keine Netzsuche noetig; Literatur nur mit [sek]-Etikett aus
deinem Wissen, Primaerbelege als "zu beschaffen" fuehren.

## Lieferung

Datei `state/prd_analyse_2026-11-01/METHODEN_SWEEP.md`
(ASCII, Deutsch, keine Modellnamen - Rollen; keine Hostnamen; Markierungen [F] Fakt aus Akte, [R] eigene Rechnung,
[U] Urteil, [V] Vermutung, [sek] Sekundaerbeleg). Rechenskripte (nur Formeln) unter `sweep/calc/`.

Gliederung:

**1. Methodenkatalog** (mindestens 25 Methodenfamilien, nach Disziplin gruppiert): Physik/Statistische Mechanik
(Skalengesetze, Invarianten wie Kyle-Obizhaeva, Multifraktalitaet, Warteschlangenmodelle des Orderbuchs, Omori-/
Nachbeben-Gesetze fuer Liquidationskaskaden), Punktprozesse (Hawkes, Branching, Ereigniszeit), Extremwerttheorie
(GPD-Raender, Tail-Index, Rekordstatistik), Informationstheorie (Transfer-Entropie, Kompressionsmasse, Mutual
Information, Permutationsentropie), Signalverarbeitung (Spektren, Wavelets, Saisonalitaet, Zustandsraummodelle,
Kalman), Netzwerkwissenschaft (Lead-Lag-Graphen ueber Assets/Venues, Zentralitaet, Community-Drift), Regelungstechnik/
Zuverlaessigkeit (Datenqualitaet als Instrument, Ausfallbudgets, Kalibrierung), Metrologie (Unsicherheitsbudgets,
systematische Fehler, Blindanalyse, Look-elsewhere-Effekt, Entdeckungsstatistik mit oberen Grenzen/CLs), klinische
Studienmethodik (gruppensequentiell, adaptiv, Futility, SESOI, Assurance), Epidemiologie/Survival (Delisting-Hazard,
IPCW, Cox), Kausalinferenz mit natuerlichen Experimenten (Listings/Delistings, Regelaenderungen der Boerse wie
Funding-Cap/Auto-Switch, Wartungsfenster, Ausfaelle, Kontraktumstellungen), Oekologie/Capture-Recapture (verdeckte
Liquiditaet), Geophysik (Ereigniszeit, Aftershocks), Maschinelles Lernen (nur als Exploration in Zone X mit
verschachtelter CV und Konto; Repraesentationslernen; Anomalie-Erkennung), Robuste Statistik (M-Schaetzer, Rang-
Statistiken, Permutationen). Je Familie: was sie misst, Voraussetzungen, Beispiel in der Finanzliteratur [sek],
Anwendbarkeit auf unsere Stroeme, Zone (X sofort / K nach Registrierung / tot nach D.x).

**2. Matrix Methode x Datenstrom x Horizont**: Zeilen Methodenfamilien, Spalten die Stromgruppen (Tages-OHLCV-Panel;
1-min BTC/ETH; Funding aller Perps; OI; Trades 5 Symbole 2020-26; L2-Orderbuecher 2023-26; Optionskette tardis
monatlich 2019-26; Options-Ticker/Greeks ab 2026-06; DVOL; Settlements/Delivery; Liquidationen/Insurance ab 2026-06;
Delisting-/Listing-Register; Binance/Bitmex/Deribit-Trades). Zellen: "X jetzt" / "K prospektiv" / "Daten fehlen" /
"tot (D.x)" / "unter Wand, nur Messung". Mit kurzer Begruendung je nicht-trivialer Zelle.

**3. Zwoelf neue Forschungsprogramme ("Ideenkarten")**, die weder F1..F12 noch 2.0/3.0-Kandidaten abdecken, je Karte:
Mechanismus und Zahler (wer zahlt die Praemie / woher kommt die Struktur), zu messende Groesse und Statistik, Nullmodell,
Daten (haben / fehlen), Zone und fruehester Konfirmationszeitpunkt unter 3.1, Aufloesungsgrenze (Groessenordnung aus
Akten-Nuisance mit markierten Annahmen; keine Effektgroessen), Wand-Etikett, Konflikte mit Kompendium D, Vorwissens-
und Siegel-Etikett, noetiger Datenauftrag. Mindestens vier Karten muessen **Messprogramme** sein (Invarianten,
Skalengesetze, Nullwelten, Kostenmodelle), die auch ohne Praemie Wissen erzeugen und die Nullmodelle der Konfirmation
kalibrieren; mindestens vier muessen **zeitnah konfirmierbar** sein (Konfirmation innerhalb 12 Monaten unter 3.1).

**4. Grosse Daten konkret**: Was laesst sich nur mit den 309 GB Trades, 377 GB Orderbuechern und 387 GB Optionskette
lernen (ohne zu handeln)? Mess-Invarianten, Skalengesetze, Kostenmodelle (Slippage als Kurve statt Konstante),
Nullwelten fuer die Konfirmation, Datenqualitaet. Mit Rechenaufwand-Schaetzung (Sandbox-CPU, 2 MB/s Endpunkt) und
Sampling-Strategie (Stichprobentage, Stress-Tage) - nie ganze Stroeme ziehen.

**5. Negativliste**: Methoden, die du geprueft und verworfen hast, mit Grund (tot nach D.x; unter der Wand ohne
Messwert; Daten fehlen irreversibel; Horizont falsch; nicht falsifizierbar).

**6. Datenauftraege an Data-Harvest**, die der Sweep neu begruendet (priorisiert, mit "wofuer").

**7. Kurzfassung (<= 12 Zeilen)** fuer den Orchestrator: die drei wichtigsten neuen Programme, die groesste Luecke der
bisherigen Felderliste, was sofort in Zone X messbar ist.

## Regeln

- Keine Marktdaten laden, keine Siegeldatei oeffnen, keine Registrierung, kein Verdikt.
- Jede Zahl mit Herleitung oder Quelle; Fehlendes heisst UNBELEGT. Keine Effektgroessen aus dem Gedaechtnis als
  belegt ausgeben - nur als [sek]-Hinweis "zu beschaffen".
- Ehrlichkeit vor Fuelle: lieber 8 tragfaehige Karten als 12 duenne. Sag, was du nicht beurteilen kannst.
- ASCII, Deutsch, keine Modellnamen (Rollen: Orchestrator, Herleitung, Review, Bau, Kartierung), keine Hostnamen,
  keine Zugangsdaten, keine Pfade ausserhalb des Repos ausser deinem Ausgabeverzeichnis.
