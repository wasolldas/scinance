# WP-5 - Bybit-Options-Quote-Zensus: Befund und Korrektur einer eigenen Fehlaussage

> Snapshot 2026-08-24, oeffentlicher Endpoint `/v5/market/tickers?category=option`
> (BTC 762 Symbole, ETH 658 Symbole; vom Nutzer auf seiner Maschine gezogen,
> weil der Proxy dieser Umgebung `api.bybit.com` mit 403 blockt).
> Rohdaten: `state/wp5_20260824/bybit_{btc,eth}_option_chain_20260824.json`
> (SHA-256 im Zensus-JSON gepinnt).
> Zensus: `state/wp5_20260824/wp5_optchain_census.json`,
> erzeugt von `scripts/wp5_option_chain_census.py`.

---

## 0. Vorab: eine Aussage von mir war falsch und wird hier zurueckgezogen

Vor diesem Zensus hatte ich dem Nutzer aus **einem einzigen Ticker-Sample**
(`BTC-25AUG26-76500-C-USDT`, bid1Iv 0,4012 / ask1Iv 0,4967 = **9,55 Vol-Punkte**
Quote-Breite) geschrieben:

> „Der einseitige Eintrittsabschlag ist doppelt so gross wie die gesamte
> erhoffte Kante. ... Und dieses Sample ist vermutlich ein guenstiger Fall,
> kein schlechter."

**Beides ist falsch.** Der Zensus zeigt:

1. Das Sample war **kein guenstiger, sondern der schlechteste denkbare Fall**.
   Es liegt exakt in der einen degenerierten Ecke der Kette: **1 Tag bis
   Verfall UND tief im Geld (Delta 0,77)**. Dort ist der Optionspreis
   praktisch der innere Wert, Vega geht gegen null, und die Umrechnung einer
   Ein-Tick-Preisbreite in implizite Volatilitaet dividiert durch fast null.
   Die 9,55 Vol-Punkte messen **keine Handelsbereitschaft**, sondern eine
   numerische Division.
2. In dem Bereich, den eine Strangle-Strategie tatsaechlich handelt
   (7-14 Tage, abs(Delta) 0,15-0,30), betraegt die **volle** Quote-Breite
   **0,14 Vol-Punkte (BTC)** bzw. **0,26 Vol-Punkte (ETH)** - also
   **Faktor 37-68 enger** als das Sample, aus dem ich extrapoliert habe.

Der Fehler war methodisch, nicht rechnerisch: Extrapolation von n=1 ohne
Kontrolle der Achse, die den Wert erzeugt. Genau dieselbe Klasse Fehler wie
die zurueckgezogene GL-024-Behauptung („Nicht-Determinismus ausgeschlossen"
nach zwei uebereinstimmenden Laeufen). Konsequenz ist im Modul verankert:
jede IV-Statistik wird **nur noch nach abs(Delta) getrennt** ausgewiesen, und
ein Unit-Test (`test_deep_itm_poisons_the_pooled_iv_width_but_not_the_otm_bucket`)
pinnt das Artefakt als Fixture fest.

---

## 1. Deckung

| | Symbole | zweiseitig quotiert | davon mit verwertbarem bid1Iv>0 |
|---|---:|---:|---:|
| BTC | 762 | 744 (98 %) | 635 (83 %) |
| ETH | 658 | 637 (97 %) | 499 (76 %) |

`bid1Iv = 0` bei zweiseitigem Preis wird als **fehlende Quote** gezaehlt,
nicht als 40-Vol-Punkte-Spread (per Test gepinnt). 11 Verfalltermine je
Basiswert, von 1 Tag bis 305 Tagen.

## 2. Die pooled-Sicht - und warum sie in die Irre fuehrt

| DTE | BTC n / IV p25/p50/p75 (Vol-Pkt) | ETH n / IV p25/p50/p75 |
|---|---|---|
| 0-7 | 212 / 0,44 / **1,14** / 6,88 | 175 / 0,72 / **1,94** / 14,76 |
| 8-21 | 108 / 0,20 / **0,56** / 5,95 | 93 / 0,36 / **0,82** / 6,94 |
| 22-45 | 74 / 0,20 / **1,32** / 7,78 | 54 / 0,41 / **1,81** / 9,50 |
| 46-120 | 73 / 0,22 / **0,72** / 3,30 | 41 / 0,63 / **0,92** / 10,30 |
| >120 | 168 / 1,16 / **2,23** / 10,14 | 136 / 6,05 / **18,12** / 26,80 |

Die grossen p75-Werte sind **fast vollstaendig** das ITM-Artefakt aus
Abschnitt 0. Aufgeloest nach abs(Delta) im Horizont 7-14 Tage:

| abs(Delta) | BTC n / IV p50 | BTC rel. Spread p50 | ETH n / IV p50 | ETH rel. Spread p50 |
|---|---|---:|---|---:|
| 0,00-0,10 | 16 / 0,79 | 8,1 % | 13 / 0,39 | 3,0 % |
| **0,10-0,20** | 6 / **0,17** | **1,1 %** | 4 / **0,24** | **1,1 %** |
| **0,20-0,35** | 4 / **0,17** | **0,7 %** | 7 / **0,33** | **1,1 %** |
| 0,35-0,65 (ATM) | 10 / 0,33 | 0,8 % | 12 / 0,68 | 1,2 % |
| 0,65-1,00 (ITM) | 18 / **7,88** | 1,6 % | 17 / **9,59** | 2,3 % |

Man liest die Zeile ITM richtig, indem man **nicht** die IV-Spalte nimmt,
sondern die relative Preisspalte: 1,6 % bzw. 2,3 % - das Buch ist dort
normal eng, nur die IV-Umrechnung ist unbrauchbar.

## 3. Der belastbare Kern: OTM-Beine je Verfall

abs(Delta) 0,15-0,30, alle Verfalltermine (Median der vollen Quote-Breite):

| Verfall | DTE | BTC IV p50 | BTC OI p50 | ETH IV p50 | ETH OI p50 |
|---|---:|---:|---:|---:|---:|
| 25AUG26 | 1 | 0,43 | 53,5 | 1,21 | 894,5 |
| 26AUG26 | 2 | 0,29 | 8,6 | 0,38 | 520,6 |
| 27AUG26 | 3 | 0,24 | 0,0 | 0,69 | 142,7 |
| 28AUG26 | 4 | 0,20 | 60,6 | 0,26 | 778,2 |
| **4SEP26** | **11** | **0,14** | 27,6 | **0,26** | 896,8 |
| 11SEP26 | 18 | 0,12 | 14,5 | 0,36 | 447,7 |
| 25SEP26 | 32 | 0,14 | 46,9 | 0,26 | 681,1 |
| 30OCT26 | 67 | 0,20 | 17,6 | 0,47 | 218,4 |
| 25DEC26 | 123 | 0,40 | 16,8 | 0,71 | 328,1 |
| 26MAR27 | 214 | 1,03 | 1,3 | **18,09** | 19,1 |
| 25JUN27 | 305 | 1,62 | 1,0 | **27,86** | 90,3 |

Das ist der eigentliche Befund: **an OTM-Strikes mit realem Open Interest
ist das Bybit-Optionsbuch bis etwa vier Monate hinaus eng** - 0,12-0,43
Vol-Punkte (BTC), 0,26-0,71 (ETH). Erst die LEAPS-Termine brechen weg, bei
ETH katastrophal (18-28 Vol-Punkte). Die Enge ist also **kein Artefakt eines
einzelnen Verfalls**, sondern gilt ueber neun aufeinanderfolgende Termine.

Groessenordnung der Tiefe an der Spitze des Buchs (Median bid1Size im
Bein-Band, 4SEP26): BTC 2,24 Kontrakte bei ~800 USDT Praemie = ~1.800 USDT;
ETH 510 Kontrakte bei ~36 USDT = ~18.000 USDT. Klein, aber fuer ein kleines
Buch nicht bindend.

## 4. Die Umrechnung, die alles vergleichbar macht

`vega / S` ist dimensionslos und uebersetzt eine als Bruchteil des Index
quotierte Gebuehr in Vol-Punkte:

    Kosten [Vol-Pkt] = n_Fills * Gebuehr [bp des Index] / (vega/S) [bp je Vol-Pkt]

Gemessen im Bein-Band (7-14 DTE, abs(Delta) 0,15-0,30):

| | vega/S (bp Index je Vol-Punkt) |
|---|---:|
| BTC | **5,28** |
| ETH | **5,10** |

Die beiden Werte stimmen ueberein, obwohl die Basiswerte um Faktor 31
auseinanderliegen - das ist der erwartete Skalen-Invarianz-Check und per
Unit-Test gepinnt.

**Spread-Kosten gegen Gebuehren-Kosten, gemessen in derselben Einheit:**

| Kostenquelle | BTC | ETH |
|---|---:|---:|
| Quote-Spread, 2 Beine, rein + raus voll ueber den Spread | **0,28 Vol-Pkt** | **0,52 Vol-Pkt** |
| Gebuehr 1 bp/Fill, 4 Fills | 0,76 | 0,78 |
| Gebuehr 2 bp/Fill, 4 Fills | 1,51 | 1,57 |
| Gebuehr 3 bp/Fill, 4 Fills | 2,27 | 2,35 |

**Break-even-Gebuehr** (Gebuehr je Fill in bp des Index, bei der eine Kante
vollstaendig aufgezehrt ist):

| Kante | 2 Fills (bis Verfall halten) | 4 Fills (rein und raus) |
|---|---:|---:|
| 1 Vol-Punkt | 2,64 bp (BTC) / 2,55 (ETH) | 1,32 / 1,27 |
| 2 Vol-Punkte | 5,28 / 5,10 | 2,64 / 2,55 |
| **3 Vol-Punkte** (C-33-Kante) | **7,92 / 7,65** | **3,96 / 3,82** |
| 5 Vol-Punkte | 13,21 / 12,75 | 6,60 / 6,37 |

## 5. Was daraus folgt - und was ausdruecklich NICHT

**Folgt:** Die Behauptung „der Options-Quote-Spread auf Bybit toetet eine
Vol-Strategie a priori" ist **widerlegt**. Im gehandelten Band frisst der
Spread rund **9 % (BTC) bzw. 17 % (ETH)** einer 3-Vol-Punkte-Kante. Das ist
eine Steuer, kein Todesurteil. Der Kontrast zum WP-4-Befund ist scharf und
konsistent: auf Perps ist der Spread der **harte Boden von einem Tick** und
damit als Ertragsquelle zwei Groessenordnungen zu klein; auf Optionen ist
derselbe Spread als **Kostenposten** klein genug, um eine Vol-Kante
durchzulassen. Beide Male entscheidet dieselbe Groesse in verschiedener
Rolle.

**Folgt NICHT - die bindende Nebenbedingung ist jetzt die Gebuehr, und die
ist ungeprueft.** `FEE_MAKER`/`FEE_TAKER` im Repo sind **Perp**-Konstanten
und gelten hier nicht. Bybit quotiert Options-Gebuehren als Bruchteil des
**Index** (mit einer Deckelung als Anteil der Praemie) - eine ganz andere
Groesse als die Perp-bp auf das Notional. Die Break-even-Tabelle in
Abschnitt 4 liegt bei 3,8-4,0 bp je Fill (3 Vol-Punkte Kante, 4 Fills) und
damit **in derselben Groessenordnung wie eine plausible Options-Gebuehr**.
Ob die Kante uebrig bleibt oder nicht, entscheidet sich also an einer Zahl,
die ich in dieser Umgebung nicht verifizieren kann. Sie wird hier bewusst
**nicht geraten**; das Modul nimmt die Gebuehr als Parameter entgegen und
setzt keine eigene Konstante.

**Folgt NICHT - n=1 in der Zeit.** Das ist **ein** Snapshot, ein Moment.
Er kann die Aussage „die Spreads sind immer prohibitiv" widerlegen, und das
tut er. Er kann die Aussage „die Spreads sind verlaesslich eng" **nicht**
belegen. Insbesondere fehlt die Frage, wie sich die Breite genau dann
verhaelt, wenn eine Vol-Strategie handeln will - naemlich im Stress. Die
Erfahrung aus Abschnitt 3 (1-DTE-ETH bei 1,21 gegen 0,26 im ruhigen Band)
legt nahe, dass die Verbreiterung real ist. Diese Frage ist **nur** mit
einer Zeitreihe zu beantworten, und die entsteht erst, wenn der Harvester
Bybit-Options-Ticker aufzeichnet (`AUFTRAG_HARVESTER_BYBIT_OPTIONS.md`).

## 6. Offene Punkte in der Reihenfolge ihrer Verbindlichkeit

1. **Options-Gebuehrenschema verifizieren** (Nutzer-Maschine, ohne Keys aus
   der Bybit-Dokumentation oder mit Keys aus `/v5/account/fee-rate`). Ergebnis
   als eigene, klar von `FEE_MAKER`/`FEE_TAKER` getrennte Repo-Konstante
   eintragen. Bis dahin ist jede Aussage zur Handelbarkeit von H-26b/C-33
   **unentschieden**, nicht „positiv".
2. **Harvester-Auftrag ausloesen.** Ohne Zeitreihe bleibt der Spread-Zensus
   bei n=1 und die Stress-Frage unbeantwortbar.
3. Erst danach: Registrierung eines Handelbarkeits-Beins (H-26b) mit dem
   dann bekannten Gebuehrensatz. Vorher nicht - die Schwelle wuerde sonst
   nach dem Sehen der Zahl gesetzt.

## 7. Bleibender Ertrag

`src/bybit_edge/research/wp5_optchain/census.py` + Runner + 17 Unit-Tests.
Jeder kuenftige Options-Snapshot ist damit in Sekunden nach DTE, abs(Delta),
Verfall, Liquiditaet und Gebuehren-Break-even auswertbar, ohne numpy und
ohne Netzzugang. Die beiden Fixture-Ketten („eng" und „weit") erfuellen die
DEC-39-Pflicht in beide Richtungen.
