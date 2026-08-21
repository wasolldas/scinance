# WP-4 · Quote-Spread-Zensus — Befund und Konsequenz

> Lauf 2026-08-21 (5.170 s, rc=0). Rohdaten: `state/wp4_20260821/wp4_spread_census.json`.
> Vorab fixierte Entscheidungsregel (DEC-40/41): liegt der halbe Median-Spread
> unter der Maker-Gebuehr je Bein, ist der Maker-Spread-Capture-Kandidat
> **ohne weiteren Aufwand tot**. Die Regel hat gefeuert.

## 1. Messergebnis

| Symbol | Fenster | ok-Tage | Median-Spread | p10 | p90 | **halber Spread** | deckt Maker-Bein? |
|---|---|---:|---:|---:|---:|---:|:---:|
| BTC | RECENT (ab 2026-06-22) | 38 | **0,0157 bp** | 0,01553 | 0,01573 | **0,0079 bp** | **NEIN** |
| ETH | RECENT (ab 2026-06-19) | 39 | **0,0537 bp** | 0,05337 | 0,05378 | **0,0268 bp** | **NEIN** |
| BTC | HIST 2024Q1 | 90 | **0,0196 bp** | 0,01943 | 0,01995 | **0,0098 bp** | **NEIN** |

Maker-Gebuehr (kanonische Repo-Konstante `FEE_MAKER`): **2,0 bp je Bein**, also **4,0 bp Roundtrip**. Taker 5,5 bp je Bein.

## 2. Die Groessenordnung

| Fenster | eingefangener Spread | Maker-Roundtrip | **Fehlbetrag-Faktor** |
|---|---:|---:|---:|
| BTC RECENT | 0,0157 bp | 4,0 bp | **255×** |
| ETH RECENT | 0,0537 bp | 4,0 bp | **75×** |
| BTC 2024Q1 | 0,0196 bp | 4,0 bp | **204×** |

Der gesamte Bruttoertrag der Strategie — der eingefangene Spread — ist **zwei Groessenordnungen kleiner als allein die Gebuehr**, vor jeder Adverse Selection, vor Inventar-, Funding- und Latenzkosten.

## 3. Warum die Zahl belastbar ist: der Spread ist EXAKT EIN TICK

Die Dispersion ist verschwindend (p90−p10 = 0,8–2,7 % des Medians) — der Spread ist praktisch **konstant**. Die Rueckrechnung erklaert warum:

| Fenster | Spread | Tick | implizierter Preis |
|---|---:|---:|---:|
| BTC 2024Q1 | 0,01956 bp | 0,10 USD | ~51.100 |
| BTC RECENT | 0,01569 bp | 0,10 USD | ~63.700 |
| ETH RECENT | 0,05365 bp | 0,02 USD | ~3.728 |

Alle drei Fenster zeigen **exakt einen Tick**, bei plausiblen Preisniveaus. Das ist der **harte Boden**: enger als ein Tick kann ein Buch nicht sein. Eine Unterschaetzung durch Mess- oder Rekonstruktionsfehler ist damit ausgeschlossen — man kann nicht unter den Boden messen. Und es bedeutet zugleich, dass die Signatur die eines **maximal kompetitiven Buchs** ist: der Spread liegt permanent am Minimum, weil immer jemand dort quotet.

**Konsequenz fuer die Entwurfs-Idee „Spread in Stress verbreitern":** gegenstandslos. Man kann nicht INNERHALB eines Ticks quotieren; wer AUSSERHALB quotet, steht hinter der gesamten Warteschlange und wird nicht gefuellt.

## 4. Robustheit gegen die Gebuehren-Annahme

Der Befund haengt NICHT an der genauen Gebuehr:
- **Bei 2 bp Maker (Standard):** Faktor 75–255 zu klein. Tot.
- **Bei Gebuehr NULL:** Bruttoertrag 0,008–0,027 bp je Roundtrip — oekonomisch vernachlaessigbar, und davon gehen Adverse Selection, Inventar-, Funding- und Infrastrukturkosten noch ab. Tot.
- **Bei NEGATIVER Gebuehr (Rebate):** Dann waere der Ertrag die REBATE, nicht der Spread — das ist eine andere Strategie (Rebate-Farming) und setzt ein Market-Maker-Abkommen voraus. Das ist eine **Zugangs-**, keine Forschungsfrage; das Programm kann sie nicht messen.

Damit ist auch die im Entwurf zitierte „−2,5 bps Rebate" (Code-Kommentar-Artefakt, dem die kanonische Konstante `FEE_MAKER = +2 bp` widerspricht) endgueltig irrelevant fuer die Frage: unter keiner der drei Gebuehren-Lesarten traegt der Spread selbst eine Strategie.

## 5. URTEIL: **Maker-Spread-Capture auf Bybit-Perp-Majors ist TOT.**

Nicht knapp, nicht bedingt, nicht „mit besserem Signal vielleicht": um den Faktor 75–255. Kein Signal, kein Envelope, keine Kill-Regel und keine Fill-Optimierung kann eine Bruttokante von 0,01–0,05 bp ueber eine 4-bp-Gebuehrenwand heben. **H-25 wird NICHT registriert.**

### Verallgemeinerbarer Programm-Befund (dauerhaft)
Jede kuenftige Strategie-Idee, deren Ertragsquelle „den Spread einfangen" ist, ist auf Bybit-Perp-Majors **a priori tot** und braucht keine eigene Untersuchung mehr — der Spread liegt permanent bei einem Tick, also bei 0,01–0,05 bp. Handelbare Ertragsquellen muessen dort **Preisbewegung** sein, nicht Spread. Diese Zahl ist ab sofort als Konstante des Programms zu zitieren.

### Was der Zensus zusaetzlich geliefert hat
Ein wiederverwendbarer, deterministischer `spread_1min`-Store (gleiche Replay-Maschinerie wie WP-2, eigener Pfad, WP-2-Store nachweislich unberuehrt). Jede kuenftige Frage nach Buch-Enge, Spread-Regimen oder Execution-Timing ist damit in Minuten beantwortbar statt in Naechten.

### Ehrliche Randnotizen
- Abdeckung der RECENT-Fenster: 38 bzw. 39 ok-Tage bei 15 no_raw-Tagen und 2 bzw. 4 laut verworfenen Tagen — die Loecher sind die aus dem WP-1-Zensus bekannten. Fuer einen Befund dieser Groessenordnung ist die Abdeckung mehr als ausreichend; bei einem knappen Ergebnis waere sie es nicht gewesen.
- Gemessen ist der **Top-of-Book-Spread**, nicht die realisierte Fill-Qualitaet. Fuer die Widerlegung genuegt das: die Fill-Qualitaet kann den Bruttoertrag nur SENKEN, nie erhoehen.
