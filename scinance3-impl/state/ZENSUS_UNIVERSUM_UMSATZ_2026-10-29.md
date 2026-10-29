# Zensus des Bybit-USDT-Perp-Universums nach USD-Wochenumsatz (nur Zaehlungen; Vorarbeit fuer kuenftige Querschnitts-Priors)

> Orchestrator, 2026-10-29 (Nutzerauftrag "Vorarbeit 2" nach GL-036). Quelle: Data-Harvest `bybit/rest.kline1d`, Feld
> `turnover` (Quote-Volumen in USDT je UTC-Tag), Extrakt 2021-01-01..2026-09-28, **Tage > 2026-06-28 vor jeder Rechnung
> entfernt**; lineare USDT-Perps (DEC-101 E1); nur volle Wochen (7 Tageskerzen, Montag-Start). Keine Renditen, keine
> Preise, keine BTC/ETH-Vol-Statistik. Skript `zensus_universum_umsatz_2026-10-29.py`, Zahlen
> `zensus_universum_umsatz_2026-10-29.json`. Klassen nach Ficura (FFA WP 3/2023): Wochenvolumen < 100 Tsd. / 100 Tsd.-1 Mio /
> 1-5 Mio / 5-50 Mio / >= 50 Mio USD - **Vorbehalt: Perp-Turnover ist nicht das Spot-Volumen von CoinMarketCap**, das
> Ficura verwendet; die Zuordnung ist nur eine Groessenordnung.

## Ergebnis

| Fenster | Wochen | K je Woche (Median) | Anteil je Klasse, Median ueber Wochen: <100k / 100k-1M / 1M-5M / 5M-50M / >=50M | Median-Wochenumsatz je Symbol (Mio USD): Q5 / Q25 / Median / Q75 / Q95 |
|---|---:|---:|---|---|
| P 2022-04-18..2024-06-23 | 114 | 212,5 | 0,0 / 1,5 / 14,1 / 51,3 / 31,1 % | 2,1 / 8,3 / 24,1 / 89,1 / 677 |
| W1 2024-07-01..2025-06-29 | 52 | 465,5 | 0,0 / 0,2 / 11,6 / 54,0 / 32,9 % | 2,8 / 9,0 / 24,6 / 93,1 / 722 |
| W2 2025-07-07..2026-06-28 | 51 | 553,0 | 0,0 / 5,7 / 29,7 / 43,5 / 21,6 % | 1,0 / 3,5 / 10,5 / 40,8 / 409 |
| gesamt 2021-01-04..2026-06-28 | 286 | 250,5 | 0,0 / 0,5 / 12,7 / 49,8 / 31,6 % | 1,6 / 6,3 / 18,9 / 74,7 / 631 |

Symbole nach ihrem Median-Wochenumsatz im Fenster: P 0 / 1 / 26 / 237 / 132; W1 0 / 1 / 40 / 389 / 180; W2 0 / 17 / 226 /
404 / 104 (Klassen wie oben).

## Lesart
- Kein Symbol liegt in der Klasse "< 100 Tsd. USD/Woche", in der Ficura (Tab. 7 B) das Wochen-Reversal findet; auch bei
  einem Umrechnungsfaktor Perp-Turnover zu Spot-Volumen von 10..50 bliebe der Median des Universums (10..25 Mio USD/Woche)
  deutlich ueber 100 Tsd. USD. Das Universum entspricht nach Umsatz eher Ficuras Gruppen "M > 10 Mio / V > 1 Mio" bis
  "Large and Liquid" (Momentum, seit 2021 "unprofitable"), also den Lesarten R3..R4 der H-33-Herleitung - konsistent mit
  GL-036 (kein Reversal-Prior) und mit dem Pilot-Vorzeichen? **Nein, nicht pruefbar:** der Pilot (GL-035) zeigte negatives
  Momentum in einem Universum, das nach diesem Zensus "liquide" ist; die Literatur-Zuordnung erklaert das nicht. Etikett:
  Zensus und Pilot widersprechen der Literaturerwartung fuer liquide Universen - ein Befund, kein Verdikt.
- W2 ist umsatzschwaecher und breiter (29,7 % in 1-5 Mio, 21,6 % >= 50 Mio gegen 31..33 % in P/W1): mehr kleine Listungen.
- Fuer kuenftige Querschnitts-Hypothesen: eine Umsatz-Mindestschwelle (z. B. >= 5 Mio USD/Woche, PIT) als Universum
  waere vorab fixierbar und wuerde ~75..85 % der Symbole behalten; sie waere eine Gabelung Richtung Testbarkeit oder
  Strenge je nach Hypothese und ist hier nur benannt.

## Was nicht folgt
Kein Prior, keine Hypothese, keine Registrierung; keine Rendite gesehen; GL-035/GL-036 unveraendert. Die Marktkapitalisierung
je Symbol bleibt UNBELEGT (nicht in der Akte).
