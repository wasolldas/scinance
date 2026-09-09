# Welle 1 - Vorfragen V-1..V-6: Befund (Lauf 2026-09-08 14:43 UTC, Nutzer-PC)

> Rohausgabe: `state/runs/welle1_vorfragen_20260908/vorfragen_20260908_1443.txt`.
> Jede Konsequenz unten war VORAB fixiert (PRD 3.0 Par. 4.4, Par. 11); hier
> wird nur festgestellt, welcher Zweig eingetreten ist. V-4 (Delivery-Fee)
> ist manuell und steht noch aus.

## V-1 Funding-Historie: VOLLSTAENDIG oeffentlich nachladbar
| Symbol | Records | von | Tage |
|---|---:|---|---:|
| BTCUSDT | 7.074 | 2020-03-25 | 2.358 |
| ETHUSDT | 6.445 | 2020-10-21 | 2.148 |
| SOLUSDT / BNBUSDT | 6.052 / 5.692 | 2021-06-29 | 1.897 |
| XRPUSDT / DOGEUSDT / AVAXUSDT | 5.832 / 5.772 / 5.457 | 2021-05..09 | 1.819-1.944 |
**Zweig:** Historie reicht ueber beide A1-Fenster fuer jedes geprobte Symbol.
Die A1-Datenbedingung (>= 117 Symbole ueber beide Fenster) ist damit NICHT
widerlegt; die volle Universumszaehlung liefert WP-7.

## V-1b Zins-Term, Intervall, Cap je Kontrakt (instruments-info, 862 linear)
- **Funding-Intervall:** 480 min = 409 Symbole, **240 min = 412 Symbole**,
  60 min = 1, 0 min = 40 (datierte Futures). Die im PRD und im Exkurs
  gefuehrte Zweiteilung "8h vs 1h" war UNVOLLSTAENDIG: die Hauptheterogenitaet
  ist **4h vs 8h**, je zur Haelfte. `funding_n`-Normierung (WP-7) ist damit
  keine Randbedingung, sondern Kern; der "1h-Ausschluss" in A1 betrifft heute
  genau EIN Symbol und ist als Regel gegenstandslos - die Selektionsfrage
  (DEC-58) stellt sich stattdessen fuer den 4h/8h-WECHSEL je Symbol, dessen
  Auslese-Mechanik an der Primaerquelle zu klaeren bleibt (V-1 erweitert).
- **Caps (upper/lowerFundingRate je Intervall):** BTC/ETH 0,333 %, SOL 0,5 %,
  DOGE 0,58 %, Masse bei 2,0 % (411) und 2,5 % (169) - je Intervall, also
  Cap-Treffer fuer Alt-Perps 6-8x seltener als fuer BTC. `I` ist in
  instruments-info nicht als Feld enthalten; der Zins-Term je Klasse bleibt
  [sek] 0,01 %/8h und ist ueber die Totzone (V-6) empirisch bestaetigt.
- `deliveryFeeRate` ist ein Feld von instruments-info - **V-4(b) ist damit
  maschinell lesbar** (naechster Lauf), V-4(a) Optionen bleibt manuell.

## V-2 Datierte Futures: VORHANDEN, aber ILLIQUIDE -> A4 wird RECORDING-FIRST
40 datierte USDT-Futures (woechentlich bis quartalsweise, 8 Basiswerte) und
4 inverse Quartale. `turnover24h` der vordersten BTC-Kontrakte: 73.043 USD
(11SEP26), 45.421 (18SEP26), 526.839 (25SEP26); ETH 520.053 / 143.895 /
342.498; inverse Quartale 2-77 USD. Gegen einen Perp-Tagesumsatz in
Milliarden liegt das um Groessenordnungen unter der vorab fixierten
1-%-Marke. **Vorab fixierte Konsequenz tritt ein:** A4 (Perp vs. datierter
Future) ist nicht gestrichen, sondern RECORDING-FIRST - erst nach >= 12
Monaten Quote-Aufzeichnung der datierten Kontrakte registrierbar. Kein
Alpha-Slot in Welle 1/2. Die Bybit-Verfaelle liegen freitags (11/18/25 SEP)
- derselbe Takt wie Deribit (A2-Relevanz: Cross-Venue-Verfallsfluesse).

## V-3 + V-6 Zinsanker und Totzone: der Anker ist ein TOTZONEN-WERT, kein Mittelwert
| Symbol | Median(F-I) je 8h | p.a. | Totzone (F exakt = I) |
|---|---:|---:|---:|
| BTCUSDT | -0,0059 % | -6,4 % | 13,0 % |
| ETHUSDT | -0,0059 % | -6,5 % | 11,0 % |
| SOLUSDT | -0,0062 % | -6,8 % | 19,0 % |
| XRPUSDT | -0,0051 % | -5,6 % | 20,5 % |
| BNBUSDT | 0,0000 % | 0,0 % | **46,0 %** |
| DOGEUSDT | -0,0043 % | -4,7 % | 26,5 % |
| AVAXUSDT | -0,0045 % | -4,9 % | 28,0 % |
**Lesart:** Alle sieben Symbole liegen im 43-Tage-Fenster systematisch UNTER
dem Anker (F ~ 0,004 %/8h ~ 4,5 % p.a. statt 10,95 %). Das widerlegt nicht
die Formel `F = P + clamp(I-P, +-0,05 %)`, sondern bestaetigt sie: I ist der
Wert der TOTZONE (11-46 % aller Intervalle sitzen exakt dort), nicht der
unbedingte Erwartungswert. **Vorab fixierte Konsequenz "systematische
Abweichung -> Funding-Rechnung neu aufsetzen, bevor A1 registriert wird"
tritt ein.** Konkret (DEC-59): (1) A1s Nulleffekt wird nicht als "Anker
kuerzt sich heraus" formuliert, sondern als Totzonen-Modell: der Querschnitt
enthaelt einen Klumpen bei exakt I, dessen Anteil je Symbol 11-46 % betraegt
und der Rang-Ties erzeugt; (2) der Sortierschluessel muss die Wochen-SUMME
nutzen und den Tie-Anteil je Woche/Dezil ausweisen; (3) WP-7 misst den
Totzonen-Anteil je Symbol-Dezil auf dem vollen Backfill; (4) die A1-
Feasibility bekommt eine Kill-Bedingung: liegt der Median-Tie-Anteil im
obersten und untersten Dezil ueber einer vorab zu fixierenden Grenze, ist
die Dezil-Sortierung degeneriert (Zahl wird VOR dem Lauf aus dem WP-7-
Befund hergeleitet, nicht danach). 43 Tage sind eine Plausibilitaets-,
keine Regime-Aussage (2025-10-10 nicht enthalten).

## V-5a Deribit-Verfallskalender: TAEGLICH, woechentlich, monatlich, quartalsweise
BTC/ETH je 11 offene Termine: 09./10./11./12.09. (Mi/Do/Fr/Sa - Tagesverfaelle),
18./25.09. (Freitage), 30.10., 27.11., 25.12. (Monatsenden), 26.03., 25.06.
(Quartale). **Zweig:** woechentliche Freitags-Verfaelle existieren - A2-P1-
Variante (a) ist real, Placebo P1 "Nicht-Verfalls-Freitag" ist leer; die
Tagesverfaelle verduennen die Ereignismenge zusaetzlich. A2 bleibt bis V-5b
(Effektgroesse fuer die gewaehlte Ereignismenge) und V-5c (Zeitlage der
Umkehr um 08:00 UTC) ein GL-012-Fall. Bybit-datierte Futures verfallen
ebenfalls freitags - Cross-Venue-Flussfrage fuer eine spaetere A2-Fassung.

## Offen
V-4(a) Options-Delivery-Fee (manuell), V-5b/c (Literatur), V-1 erweitert
(Auslese-Mechanik des 4h/8h-Wechsels an der Primaerquelle).
