# Datenannahmen-Register (DEC-105; Kritik K-13) - Stand 2026-11-02

> Eine Datei fuer die Frage "welche Datenannahme des PRD und der Akte gilt heute noch". Fortzuschreiben bei jedem
> Katalog-Refresh und jeder Data-Harvest-Antwort (datierte Zeilen, append-only; ueberholte Zeilen bleiben stehen und
> erhalten einen Nachfolger). Quellen: `state/prd_analyse_2026-11-01/DATENINVENTAR_2026-11-01.md` (Katalog 2026-11-01),
> `state/H21_LUECKENLISTE_2026-11-02.md`, DEC-98 N4/N5/N7, DEC-100, DEC-103 N1. Keine Marktwerte, keine Hostnamen.
> Markierungen: [F] Fakt aus Katalog/Akte, [V] Vermutung, UNBELEGT.

| Nr. | Annahme (Fundstelle) | Stand 2026-11-02 | Folge | Quelle |
|---|---|---|---|---|
| 1 | PRD 7.1/7.2: Tages-OHLCV und Funding je Symbol muessen per REST-Backfill nachgeladen werden | Archiv fuehrt `rest.kline1d` ALL (2.130 Tage 2021-01..2026-10, K 300..600 inkl. delisteter Perps) und `rest.fundingRateAll` ab 2021-01 [F] | Backfill-Plan ueberholt; Panel vollstaendig (DEC-100: 45 delistete nachgeladen) | Dateninventar; DEC-98 N4; DEC-100 |
| 2 | PRD 7.2: Point-in-Time-Roster "irreversibel, muss laufen" | Roster aus `rest.instruments` + `delisting_dates` (306 Delistings, 268 WP-12-Ankuendigungen) rekonstruiert; Register-Datum = letzter Handelstag [F] | gilt; Ankuendigungs- vs. Handelsende-Datum beachten (F5) | DEC-100 |
| 3 | PRD 7.2 (3): OI-Probe aller Perps "kritischste Datenfrage" | still entfallen; OI vorhanden nur BTC/ETH ab 2024-03 (970 Tage, ~120 im Siegel) und 5 Symbole ab 2026-03; Tiefe einer OI-Historie aller Perps UNBELEGT | Datenauftrag 4 (PRD_ANALYSE Abschnitt 8) | Dateninventar; Kritik K-13 |
| 4 | Kompendium D.17: Optionskette "endgueltig tot" | `tardis/options_chain`: 91 Monatsstichtage 2019-04..2026-10 (1 Stichtag je Monat; 87 vor dem Siegel) [F]; Dichte unveraendert, Tiefe neu | D.17 bleibt fuer dichte Ketten; monatliche Designs = neue Hypothesen nach C.8-Inhaltsprobe (nur <= 2026-06-01) | Dateninventar; Review B-9; DEC-105 (10) |
| 5 | A2 braucht 1-min-Kerzen fuer das Negativ-Panel (DEC-103 E5) | `rest.kline1m` nur BTCUSDT (ab 2020-03-25) und ETHUSDT (ab 2021-03-15) [F]; XRP/BNB/SOL fehlen; Anfrage 2026-10-31 offen (Weiterleitung durch den Nutzer) | Alternative: Minutenbars aus `bybit/publicTrade` (5 Symbole ab 2020-03 / 2021-05) ableiten - Machbarkeit zu pruefen (nur Vorperiode) | `state/ANFRAGE_DATA_HARVEST_NEGATIVPANEL_2026-10-31.md` |
| 6 | Funding BTCUSDT/ETHUSDT im 8-h-Takt (A2-Placebo-Lesart) | 8-h-Takt an allen Tagen bis 2026-06-28 [F]; Auto-Switch (DEC-84) seit 2025-10-30 fuer andere Symbole | A2 unberuehrt; F2 (Funding-Dynamik) hat einen Regimebruch im Panel ab 2025-10-30 | DEC-103 N1; DEC-84 |
| 7 | Live-Stroeme ab 2026-06-16 (Options-Ticker, Liquidationen, Orderbuecher, Insurance) lueckenlos | 14 gemeinsame Ausfalltage des Live-Sammlers (2026-06-26, 07-06..07-16, 08-01, 08-14; 10,1 % der Tage) [F]; Deribit-Trades 7, Binance-Orderbuch 35..38 Fehltage | Ausfalltage-Budget >= 10 % je Quartal fuer prospektive Designs; keine "lueckenlos"-Bedingung ueber feste Kalenderfenster (DEC-104 E8 (d)) | `state/H21_LUECKENLISTE_2026-11-02.md` |
| 8 | H-21 (2.0) entsperrt sich Ende 2026 | W1 nicht lueckenlos (13 Fehltage allLiquidation BTC/ETH, 1 Fehltag publicTrade ETH); W2 bisher 33/33 [F]; Nachladbarkeit von `allLiquidation` [V] nicht gegeben | in der registrierten Form nicht entsperrbar; formale Schliessung nach Data-Harvest-Antwort | `state/H21_LUECKENLISTE_2026-11-02.md` |
| 9 | H-26 (2.0) "datenseitig entsperrt" (Chat 2026-11-01 vormittags) | nach DEC-98 N4 (b), strenge Lesart der Aufzeichnungstage (dvol und publicTrade >= 210 zusammenhaengende Tage): fruehestens 2027-04-06 [F] | H-26 bleibt gesperrt (DEC-98 E2) | DEC-98 N4 (b); DEC-105 (11) |
| 10 | Deribit-Verfallskalender: Wochen-/Monatsverfaelle (PRD 5.2 Placebos P1/P2) | seit 2020-03-25 taegliche Optionsverfaelle; seit 2026-04-04 taegliche Futures-Deliveries BTC und ETH [F]; `rest.settlements` ab 2017-05-25, `rest.deliveryPrices` ab 2016 | PRD-Placebos P1/P2 leer; DEC-103 E3 Placebosatz gilt | DEC-98 N5/N7; DEC-103 |
| 11 | DVOL-Historie fuer VRP | `deribit/dvol` ab 2021-03 [F] | ausreichend; VRP strukturell nicht testbar (DEC-104 E3 (e)) | DEC-95; Dateninventar |
| 12 | Trades und Orderbuecher als 3.0-Datenbasis | `bybit/publicTrade` 5 Symbole ab 2020-03 (BTCUSDT 2.412 Tage bis 2026-10-31, lueckenlos) [F]; L2-Orderbuecher 2023-2026; `binance/publicTrade` BTC ab 2025-01; `deribit/publicTrade` ab 2025-08 (Inhalt ungeprueft); bitmex 2026 | von keinem 3.0-Kandidaten benutzt; Zone-X-Programme (Kostenmodelle, Invarianten, Nullwelten) moeglich fuer Tage vor 2024-07-01 | Dateninventar |
| 13 | W2-Ende | 2026-06-28 (letzte vollstaendige Outcome-Woche vor dem Siegel) [F] | Zone V = 2024-07-01..2026-06-28 | DEC-99 (8) |
| 14 | Blind-Siegel | ab 2026-07-01 fuer alle BTC/ETH-Rendite-/Vol-Statistiken, Zaehlungen S0 erlaubt [F] | Zone K (DEC-104 E4) | DEC-96 E3; DEC-98 E1 (b) |
| 15 | Datendienst-Verfuegbarkeit | Endpunkt ~2 MB/s, geteilt; am 2026-11-02 vormittags nicht erreichbar, Arbeit mit dem Katalog-Cache vom 2026-11-01 18:46 UTC [F] | Stromcheck monatlich (PRD_ANALYSE 9.2 Nr. 10); Katalog-Cache als Rueckfall fuer S0 | diese Datei |
| 16 | `rest.deliveryPrice ALL` | 2 Partitionen in 92 Tagen (2026-06-26..09-25) [F]; Stromcharakter unklar | Inhaltsprobe (C.8) vor jeder Nutzung | Lueckenliste Abschnitt 2 |
| 17 | Marktkapitalisierung / Spot-Volumen je Coin fuer Universums-Zuordnung von Literatur-Priors | nicht im Archiv | Datenauftrag 1 (PRD_ANALYSE Abschnitt 8) | H-33-Lehre (GL-036) |

## Nachtraege (datiert, append-only)

| Datum | Nr. | Stand | Folge |
|---|---|---|---|
| 2026-11-02 13:48 UTC | 15 | Datendienst seit 2026-11-02 vormittags durchgehend nicht erreichbar (fuenf Pruefungen 11:00..13:48 UTC, Katalog-Refresh wirft RuntimeError); gearbeitet wird mit dem Katalog-Cache vom 2026-11-01 18:46 UTC [F] | Zone-X-Programm 1 (Konto 1/2) und Inhaltsproben warten; naechste automatische Pruefung in 2 Stunden; Ursache beim Data-Harvest-Betreiber zu klaeren (Nutzer) |
| 2026-11-02 16:50 UTC | 15 | Datendienst weiterhin nicht erreichbar (siebte Pruefung seit 11:00 UTC) [F] | naechste automatische Pruefung 2026-11-03 08:00 UTC; Nutzer informiert; Ursache beim Data-Harvest-Betrieb zu klaeren |
