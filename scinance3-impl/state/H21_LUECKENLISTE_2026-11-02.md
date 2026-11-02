# H-21 (2.0, LIQ-TAG): Lueckenliste der Entsperr-Bedingung und Ausfalltage der Live-Stroeme (S0, Stand Katalog 2026-11-01 18:46 UTC)

> Reine Vollstaendigkeitszaehlung aus dem Data-Harvest-Katalog (gecachter Partitionskatalog; der Datendienst war am
> 2026-11-02 vormittags nicht erreichbar). Keine Marktwerte, keine Dateipfade, kein Hostname. Erlaubt im Siegel
> (DEC-96 E3: Zaehlungen S0). Skript: `state/prd_analyse_2026-11-01/scripts/live_gap_list.py`; Tabelle aller Stroeme ab
> 2026-06-01 ohne Options-Instrumente: `state/data_harvest_live_coverage_2026-06-01_to_2026-10-31.csv`.
> Der Tag 2026-11-01 fehlt ueberall, weil der Katalog vor Tagesschluss exportiert wurde - kein Ausfall.

## 1. H-21 Entsperr-Bedingung (Registrierung 2026-08-15, `scinance2-impl/state/hypothesis_registry.md`)

Bedingung: lueckenlose `done_days` fuer bybit `allLiquidation` **und** `publicTrade`, BTCUSDT **und** ETHUSDT, ueber
**beide** Fenster W1 = 2026-07-01..2026-09-28 und W2 = 2026-09-29..2026-12-27 (je 90 Tage). Gate: WEITER nur in beiden
Fenstern (hartes Ein-Fenster-Kriterium).

| Strom / Symbol | W1 Tage | W1 vorhanden | W1 fehlend | W2 Tage bis 2026-10-31 | W2 vorhanden | W2 fehlend |
|---|---:|---:|---:|---:|---:|---:|
| allLiquidation BTCUSDT | 90 | 77 | **13** | 33 | 33 | 0 |
| allLiquidation ETHUSDT | 90 | 77 | **13** | 33 | 33 | 0 |
| publicTrade BTCUSDT | 90 | 90 | 0 | 33 | 33 | 0 |
| publicTrade ETHUSDT | 90 | 89 | **1** (2026-09-21) | 33 | 33 | 0 |

Fehltage allLiquidation (BTC und ETH identisch): 2026-07-06 bis 2026-07-16 (11 Tage), 2026-08-01, 2026-08-14.

**Feststellung [F]:** W1 ist fuer die registrierte Form nicht lueckenlos (13 bzw. 1 Fehltage). Da die Registrierung beide
Fenster lueckenlos verlangt, ist H-21 **in der registrierten Form nicht entsperrbar**, es sei denn, die 13
Liquidations-Tage und der Trade-Tag liessen sich nachladen. Nachladbarkeit von `allLiquidation` (Bybit-WebSocket-Strom
ohne oeffentliche Historie) ist nach Aktenlage **[V] nicht gegeben**; eine Anfrage an Data-Harvest kann das klaeren
(Datenauftrag 9 der PRD-Analyse). W2 laeuft bisher lueckenlos (33 von 33 Tagen bis 2026-10-31).

**Folge (kein Verdikt):** H-21 bleibt GESPERRT; formale Schliessung ("GL-012 Daten, registrierte Form nicht erfuellbar")
erst nach der Data-Harvest-Antwort zur Nachladbarkeit. Eine Neuregistrierung mit anderen Fenstern waere eine neue
Hypothese (2.0-Akte ist abgeschlossen; in 3.0 nur ueber Kohorte 1 und unter der Wand-Etikettierung "Messfrage").

## 2. Ausfalltage der Live-Sammler (Review-Luecke 4; Budget fuer prospektive Designs)

Gemeinsame Ausfalltage von bybit-Live-Stroemen (allLiquidation, orderbook, tickers, insurance) und deribit-Live-Stroemen
(markprice.options) seit 2026-06-16, identisch je Strom: **2026-06-26, 2026-07-06..2026-07-16, 2026-08-01, 2026-08-14**
(14 Tage; Luecken-Karte DEC-98 N4 (f) bestaetigt). bybit `tickers_1h/OPTIONS`: 23 Fehltage (dazu 2026-06-17..06-27
sporadisch, 2026-07-17, 2026-07-25, 2026-08-02). deribit `publicTrade` BTC/ETH: 2026-07-22..07-26, 2026-08-02/03 (7 Tage).
binance `orderbook` (5 Symbole): 35..38 Fehltage, darunter ein Block 2026-08-17..2026-09-19 (Binance-spezifisch).
binance `rest.openInterest`: 2026-06-25..07-10 und 2026-08-02/03 (18 Tage). REST-Stroeme (fundingRate, openInterest bybit):
2026-08-02/03 (BTCUSDT bybit zusaetzlich 2026-07-31, 2026-08-01) - rueckfuellbar, Luecke im Katalog zu fuehren.
`tardis/options_chain`: 1 Stichtag je Monat (keine Luecke, Sampling). `rest.deliveryPrice ALL`: 2 Tage in 92 (Stromcharakter
unklar, Inhaltsprobe faellig).

**Budget-Regel (Vorschlag, DEC-104 E8 (d) Erreichbarkeit):** prospektive Designs auf Live-Stroemen rechnen mit
mindestens 10 % Ausfalltagen je Quartal (beobachtet: 14 von 138 Tagen = 10,1 % seit 2026-06-16; im Fenster 2026-07-01..
2026-10-31: 13 von 123 = 10,6 %) und duerfen keine "lueckenlos"-Bedingung ueber feste Kalenderfenster registrieren;
stattdessen Mindestzahl gueltiger Tage je Fenster. Rueckfuellbare REST-Stroeme sind davon ausgenommen.

## 3. Was nicht folgt

Kein Verdikt ueber Liquidationen oder einen Markteffekt; keine Marktwerte gesehen; keine Siegeldatei geoeffnet; keine
Registrierung. Die Zaehlung beruht auf dem Katalogstand 2026-11-01 18:46 UTC; ein Katalog-Refresh kann einzelne Tage
nachtraeglich als vorhanden ausweisen (dann Nachtrag).
