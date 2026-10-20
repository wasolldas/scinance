# Belege aus den hochgeladenen PDFs (2026-10-20) - unter Ergebnisblindheit

Auftrag: `SPEC_PDF_belege` (Orchestrator, 2026-10-20). Grundlage: 12 vom Nutzer hochgeladene PDFs (Liste in
Abschnitt 1). Vorarbeit: `RECHERCHE_BELEGE_2026-10-18.md` (Abschnitte 1-4, 6). Nichts committet.

Kennzeichnung: `[PDF]` im Volltext des PDFs gelesen (Primaerquelle bzw. Autorenfassung); `[sek]` nur dort, wo die
Quelle selbst eine andere Studie zitiert; `[abg.]` hier abgeleitet, Formel offen. Fehlendes heisst UNBELEGT.
Fundstellen: "S." = Seitenzahl im PDF (Zaehlung des PDF-Readers, nicht die gedruckte Seitenzahl).
Technik: Text nur mit `python3 -I` und pypdf extrahiert (Pfade als Argumente, Skripte unter
`scratchpad/pdf_belege/`), Abbildungen nicht betrachtet. Stichprobenzeitraum je PDF zuerst per Datums-Suche
mit engem Kontextfenster festgestellt, erst danach weitergelesen.

## 1. Stichprobenpruefung (Ergebnisblindheit, Schritt 1)

| Datei | Bibliographie / Fassung | Stichprobe | Status |
|---|---|---|---|
| `w25882.pdf` | Liu/Tsyvinski/Wu, "Common Risk Factors in Cryptocurrency", NBER WP 25882, May 2019 (S. 1) | Anfang 2014 bis Ende 2018, Wochendaten (S. 6) | zulaessig |
| `WP_wps-202301-0003.pdf` | Ficura, "Impact of size and volume on cryptocurrency momentum and reversal", FFA Working Paper 3/2023, VSE Prag (S. 1-2); PDF erzeugt 2023-05-11, geaendert 2023-11-28 (Metadaten) | Analyse 2017/06-2022/12; Rohdaten 2014/04-2023/01 (S. 4, 6) | zulaessig |
| `ssrn-3239670.pdf` | Bianchi/Babiak/Dickerson, "Trading volume and liquidity provision in cryptocurrency markets", SSRN 3239670; kein Datum auf S. 1, PDF erzeugt 2022-06-19 (Metadaten) | 2017-03-01..2022-03-01, taeglich (S. 5, Tab. 1-10) | zulaessig |
| `2410.15195v1.pdf` | Almeida/Grith/Miftachov/Wang, "Risk Premia in the Bitcoin Market", arXiv 2410.15195v1, 19 Oct 2024 (Stempel S. 1) | Optionen 2017-07-01..2022-12-17; BTC-Preise 2014-01..2022-12; Anhangreihen bis 2023-12-31 (S. 8, 10, 56) | zulaessig |
| `2410.15195v2.pdf` | dieselben, arXiv 2410.15195v2, 1 Aug 2025 (Stempel S. 1) | Optionen 2017-07-01..2022-12-17; BTC 2014-01..2022-12; Anhangreihe 2014-06-06..2023-12-31 (S. 8, 37-38, 49) | **zulaessig** (entgegen der Erwartung im Auftrag; keine Daten nach 2023-12-31 gefunden). Nur zur Herkunftsklaerung der Zahlen 0,72/0,58 genutzt (Abschnitt 4) |
| `ssrn-5374295.pdf` | dieselben, "Option-Implied Risk Premia and Cryptocurrency Market Regimes", SSRN 5374295; kein Datum vor dem Abstract, PDF erzeugt 2026-06-26 (Metadaten) | Optionen 2017-07..2022-12 (S. 9-10), aber Anhang: "collected from CoinGecko from August 2015 to March 2026" (S. 52) | **GESPERRT** - nur Bibliographie und Zeitraum notiert, Datei geschlossen |
| `2212.06888v7.pdf` | He/Manela/Ross/von Wachter, "Fundamentals of Perpetual Futures", arXiv 2212.06888v7, 17 Sep 2026 ("First draft December 2022. This draft September 2026.", S. 1) | Binance, stuendlich, 5 Coins, **2020-01-08..2024-03-11** ("Our data ends on 2024-03-11", S. 25, Tab. 2; "January 8, 2020 to March 11, 2024", S. 48) | **zulaessig** (Stichprobe endet vor 2024-06-30); nur Tab. 8 gelesen (Abschnitt 6) |
| Deribit "Settlement" | support.deribit.com/hc/en-us/articles/29734325712413-Settlement; "Updated 1 month ago"; Druck 20.10.26 17:23 | Regeldokument, keine Stichprobe, keine Marktniveaus | zulaessig |
| Deribit "Features" | .../25944687755293-Features; "Updated 2 months ago"; Druck 20.10.26 17:22 | Regeldokument | zulaessig |
| Deribit "Contract Introduction Policy" | .../25944688876957-Contract-Introduction-Policy; "Updated 7 days ago"; Druck 20.10.26 17:20 | Regeldokument | zulaessig |
| Deribit (Medium) "Deribit General User Information" | medium.com/@Deribit/deribit-general-user-information-8d7d0235b68a; "Feb 1, 2019"; Druck 20.10.26 17:19 | Regeldokument (Fassung 2019) | zulaessig |
| Deribit Insights "Launch of BTC Daily Options on Deribit" | insights.deribit.com/exchange-updates/launch-of-btc-daily-options-on-deribit/; "January 29, 2020"; Druck 20.10.26 17:17 | Ankuendigung | zulaessig |

Druckzeitpunkte: Fusszeile "20.10.26, hh:mm" (Ortszeit); PDF-Metadaten 2026-10-20 14:17..14:23 UTC. "Updated n ago"
ist relativ zum Druckdatum (also etwa 2026-08, 2026-09, 2026-10-13); absolute Versionsdaten stehen nicht im PDF.

## 2. A - Liu/Tsyvinski/Wu, NBER w25882 (2019) [PDF]

### 2.1 Stichprobe und Definitionen

| Groesse | Wert | Fundstelle |
|---|---|---|
| Quelle/Universum | Coinmarketcap.com, alle Coins (inkl. eingestellter), Tagesschlusskurse; Filter Marktkap. >= 1 Mio USD; Nicht-Rendite-Variablen je Woche 1/99 % winsorisiert | S. 6 (Abschn. 2) |
| Zeitraum | "1,707 coins from the beginning of 2014 to the end of 2018" | S. 6 |
| Coins je Jahr | 2014: 109; 2015: 77; 2016: 155; 2017: 804; 2018: 1.583; gesamt 1.707 | S. 8, Tab. 1 Panel A |
| Definition Woche | Jahr in 52 Wochen; Woche 1 = erste 7 Tage; Wochen 1-51 je 7 Tage, letzte Woche 8 Tage (2016: 9 Tage) | S. 6 inkl. Fn. 2 |
| Zahl der Wochen | nicht genannt. [abg.] 5 Jahre x 52 = 260 Wochen (Long-Short-Reihe ggf. 259) | - |
| Momentum-Variable | r_{1,0} "One-week momentum" (analog 2/3/4/8/16/50/100 Wochen); Formationswoche, keine weitere Formel | S. 11, Tab. 2 |
| Gewichtung | "time-series averages of weekly value-weighted portfolio excess returns" (Quintile, woechentlich rebalanciert) | S. 12-13, Tab. 3/4 |
| SE-Korrektur der t-Werte | im NBER-PDF nicht angegeben (kein Newey-West-Hinweis gefunden): **UNBELEGT** | Suche ueber alle Seiten |
| Marktfaktor | CMKT = wertgewichteter Marktindex minus 1-Monats-T-Bill; Mittel 0,013/Woche, SD 0,117 | S. 7, S. 8 Tab. 1 Panel B |

### 2.2 Momentum-Tabelle (Quintil 5 minus 1, wertgewichtet, Rendite je Woche)

| Horizont | Long-Short | t | CAPM-alpha (t) | beta CMKT (t) | R^2 | Fundstelle |
|---|---:|---:|---|---|---:|---|
| 1 Woche r_{1,0} | 0,027 | 1,994 | 0,028 (2,012) | -0,021 (-0,175) | 0,000 | S. 13 Tab. 4; S. 19 Tab. 8 |
| 2 Wochen | 0,033 | 2,442 | 0,031 (2,306) | 0,169 (1,468) | 0,008 | S. 13; S. 19 |
| 3 Wochen | 0,041 | 2,742 | 0,040 (2,652) | 0,101 (0,782) | 0,002 | S. 13; S. 19 |
| 4 Wochen | 0,025 | 2,002 | 0,024 (1,906) | 0,125 (1,174) | 0,005 | S. 13; S. 20 (Tabellenkopf dort faelschlich "Table 3 Continued") |
| 8 / 16 Wochen | 0,006 / 0,004 | 0,421 / 0,310 | - | - | - | S. 16 Tab. 7 |

- Text: "R2s ranging from about zero percent for the one-week momentum strategy" (S. 18); Momentum-Strategien "not
  significantly exposed to the coin market returns" (S. 18).
- Terzil-Variante (Anhang): 1-Woche Long-Short 0,041 (t 3,719); CAPM-alpha 0,041 (t 3,633), beta 0,060 (0,628),
  R^2 0,002 (S. 48, Tab. A.5). Terzil-Spread > Quintil-Spread: Hinweis auf Rauschen der wertgewichteten Portfolios.
- Faktor CMOM (3-Wochen-Momentum, 30/40/30, wertgewichtet): Mittel 0,038, SD 0,184 je Woche (S. 43, Tab. A.1).
- Doppelsortierung Groesse x 3-Wochen-Momentum: unter Median 0,006 (t 0,30), ueber Median 0,042 (t 2,57) (S. 43,
  Tab. A.2; Text S. 30).

### 2.3 Fama-MacBeth (S. 32, Tab. 13; Text S. 30)

Regressor: "Each factor is first sorted into five portfolios at the end of each week" - also die Quintilsnummer
(1..5). Je Panel: Spalte 1 univariat, Spalte 2 gemeinsam mit den anderen Momentum-Variablen.

| Universum | r_{1,0} | r_{2,0} | r_{3,0} | r_{4,0} |
|---|---|---|---|---|
| Marktkap. > 1 Mio USD (Panel D) | -0,002 (t -0,692) | 0,000 (0,020) | -0,000 (-0,148) | -0,001 (-0,274) |
| Marktkap. > 10 Mio USD (Panel E) | 0,005 (t 1,668) | 0,007 (2,095) | 0,007 (1,978) | 0,003 (0,693) |

Autoren (S. 30): FM "consider each observation equally and thus are close to strategies formed on equally weighted
portfolios" - im breiten Universum ist Momentum dort nicht signifikant. **Kurzfrist-Reversal (1 Woche)** wird nicht
als eigener Befund berichtet; einzige Spur: FM-Koeffizient r_{1,0} > 1 Mio USD negativ, insignifikant (-0,002,
t -0,692). Eine Querschnitts-Streuung der Wochenrenditen berichtet das Papier nicht (**UNBELEGT**; Tab. 1 Panel B
enthaelt nur Zeitreihen-SD: Markt 0,117, BTC 0,114, XRP 0,267, ETH 0,241, S. 8).

## 3. D - Ficura (2023) und E - Bianchi/Babiak/Dickerson [PDF]

### 3.1 Ficura, FFA WP 3/2023

| Groesse | Wert | Fundstelle |
|---|---|---|
| Daten | Coinmarketcap, 18.352 Coins mit Preisreihe (Stand 2023/01), inkl. eingestellter; nach Filter > 100 Tsd. USD 4.614 Coins; 96 Stable/Wrapped/Mirror-Coins entfernt; Kurs < 0,001 USD entfernt | S. 5-7 |
| Zeitraum | 2017/06-2022/12 ("insufficient number of large and liquid coins before 2017/06") | S. 4, alle Tabellen |
| Zahl der Wochen / Coins je Woche | nicht genannt: **UNBELEGT**; [abg.] 2017-06-01..2022-12-31 ~ 291 Wochen | - |
| Aufteilung | "Large and Liquid": Vorwochen-Marktkap. >= 50 Mio USD und Vorwochen-Volumen >= 5 Mio USD; "Small or Illiquid": 1-50 Mio USD oder Volumen < 5 Mio USD | S. 6-7 |
| Momentum-Variable | mom_{t,h} = Summe der logarithmischen Wochenrenditen der letzten h Wochen (Gl. 1); High-Momentum hmom = ln(C_t) - ln(H_{t,h}) (Gl. 2) | S. 7 |
| Form | Quintil-Sortierung je Woche, Folgewochenrendite, **gleichgewichtet**, einfache Renditen auf 1000 % winsorisiert; t-Werte **Newey-West** (Lag-Zahl nicht genannt); Zeitreihenregression auf **BTC-CAPM** (Gl. 3), fuer hmom zusaetzlich 3-Faktor (BTC, Groesse, 1-Wochen-Momentum; Gl. 4) | S. 7, 8, 10 |
| Beta-Kontrolle | ja, BTC-CAPM (nicht Krypto-Marktindex); Beta-Koeffizienten nicht berichtet | S. 10-11 |

Ergebnisse 1-Wochen-Momentum (Rendite je Woche, NW-t), S. 8 Tab. 3 und S. 11 Tab. 5:

| Gruppe | Q5-Q1 | t | BTC-alpha Q5-Q1 (t) | Signal-Mittel Q1 / Q5 (meanx, log) |
|---|---:|---:|---|---|
| Large and Liquid | +1,36 % | 2,332 | +1,31 % (2,603) | -0,169 / 0,245 |
| Small or Illiquid | -3,91 % | -7,309 | -3,90 % (-7,590) | -0,279 / 0,330 |

- Weitere Horizonte Large and Liquid: 2 W 1,44 % (t 2,686), 4 W 0,84 % (1,570), 12 W -0,88 % (-1,862), 26 W -0,71 %
  (-1,914); Small or Illiquid: 2 W -3,35 % (-6,352), 4 W -3,15 % (-6,769), 12 W -3,44 % (-7,969), 26 W -2,75 % (-5,606)
  (S. 8 Tab. 3). Textangabe "2.87" fuer 2 W (S. 8) widerspricht Tab. 3 (2,686) und Schluss (2,68, S. 16).
- Schwellen-Robustheit 1 W (S. 13 Tab. 7 Panel A): M > 1 Mio/V > 100 Tsd.: -0,12 % (t -0,216); M > 10 Mio/V > 1 Mio:
  1,44 % (2,075); M > 50 Mio/V > 5 Mio: 1,36 % (2,332); M > 250 Mio/V > 25 Mio: 1,82 % (2,816). Reversal haengt vor
  allem an Volumen < 100 Tsd. USD (Panel B M > 1 Mio, V < 100 Tsd.: -3,06 %, t -5,928).
- High-Momentum 1 W, Large and Liquid: 2,68 % (t 4,933), BTC-alpha 2,64 % (5,610), 3F-alpha 2,22 % (5,720)
  (S. 12 Tab. 6).
- **Stabilitaet (wichtig):** "the standard momentum seems to have stopped in the early months of 2021 and remains
  unprofitable since then" (S. 7, bezogen auf die Kumulativ-Charts in Anhang 1, Large and Liquid); Reversal der
  kleinen und High-Momentum der grossen Coins "stable over the entire period".

### 3.2 Bianchi/Babiak/Dickerson, SSRN 3239670

| Groesse | Wert | Fundstelle |
|---|---|---|
| Daten | CryptoCompare (OHLC, Volumen, > 80 Boersen, volumengewichtet) + CoinGecko (Marktkap.), USD-Paare, Tag ab 00:00 UTC; > 300 Paare nach Filtern; je Monat Top-100 liquideste Paare (Amihud des Vormonats); mind. 365 Handelstage | S. 5-6 |
| Zeitraum | 2017-03-01..2022-03-01; 1.827 Tage | S. 5; S. 28 Tab. 6 (Obs.) |
| Reversal-Horizont | **1 Tag**: Gewichte zur Zeit t aus der Rendite t-1, Haltedauer 1 Tag, taeglich rebalanciert, Dezile | S. 9 |
| Groesse der Paare | Marktkap. Median 297,46 Mio USD, Mittel 5.435 Mio USD (Zeitmittel der Querschnittsverteilung) | S. 24 Tab. 1 |
| Querschnitts-SD der Tagesrendite | 6,889 % (Zeitmittel der Querschnittsverteilung) | S. 24 Tab. 1 |
| Einfaches Reversal Q1-Q10 | gleichgewichtet 2,187 %/Tag (SD 5,918, Sharpe 0,37 taeglich); wertgewichtet 0,558 %/Tag (SD 9,212, Sharpe 0,061); NW mit 20 Lags | S. 25 Tab. 2 Panel A; S. 10 |
| Markt-Beta-Kontrolle | nur fuer die bedingte Niedrigvolumen-Reversal-Strategie: 5 Faktoren (mkt, illiq, vol, mom, size); gleichgewichtet alpha 0,012/Tag, mkt-beta 0,064 (SE 0,026); wertgewichtet alpha 0,006, beta 0,124 (0,053); adj. R^2 0,007..0,020 | S. 28 Tab. 6; S. 14 |

## 4. IC-Naeherungen (offen; alle Werte [abg.] aus den Abschnitten 2-3)

Formeln (wie in RECHERCHE_BELEGE 1.2): Weg A `IC = S / (k * sigma_xs)` mit k = 2,800 (Quintil), 2,182 (Terzil),
3,510 (Dezil) bei Normalverteilung. Weg A* (neu): `IC ~ S_r / S_x`, wenn Signal- und Renditestreuung gleich sind
(Signal = Vorwochenrendite, Rendite = Folgewochenrendite derselben Gruppe) - braucht keine externe sigma-Annahme.
Weg FM: Regressor Quintilsnummer 1..5 hat Querschnitts-SD sqrt(2), also `IC ~ b * sqrt(2) / sigma_xs`.
Weg B: `IC_aequiv = (t / sqrt(N)) * SD(IC_t)` mit Programm-SD 0,0511 (W1-stress mom1) bzw. 0,0425 (W2-stress mom1),
PROGRAMM_BILANZ_2026-10-18 Abschn. 2.1. Rang-IC ~ 0,955 x Pearson-IC (nicht eingerechnet).

sigma_xs-Anker (neu, statt reiner Annahme): (a) Ficura Large and Liquid: S_x = 0,245 + 0,169 = 0,414 -> sigma_x =
0,414 / 2,800 = **0,148** (Small or Illiquid: 0,609 -> 0,218) [S. 11 Tab. 5]; (b) Bianchi: 6,889 %/Tag x sqrt(7) =
**0,182** je Woche (iid-Annahme) [S. 24 Tab. 1]. Beide 2017-2022, Spot-Coins, nicht Bybit-Perps.

| Quelle / Konstruktion | Weg A bzw. A* bzw. FM (sigma 0,148 / 0,182 / 0,25) | Weg B (SD 0,0511 / 0,0425) |
|---|---|---|
| LTW 1 W, Quintil, wertgew., S 0,027 (t 1,994, N 260) | 0,065 / 0,053 / 0,039 | 0,0063 / 0,0053 |
| LTW 1 W, CAPM-alpha 0,028 (t 2,012) | 0,068 / 0,055 / 0,040 | 0,0064 / 0,0053 |
| LTW 1 W, Terzil, S 0,041 (t 3,719) | 0,127 / 0,103 / 0,075 | 0,0118 / 0,0098 |
| LTW FM > 10 Mio, b 0,005 (t 1,668) | 0,048 / 0,039 / 0,028 | 0,0053 / 0,0044 |
| LTW FM > 1 Mio, b -0,002 (t -0,692) | -0,019 / -0,016 / -0,011 | -0,0022 / -0,0018 |
| Ficura Large and Liquid, Weg A*: 0,0136 / 0,414 | **0,033** (BTC-alpha: 0,032) | 0,0070 / 0,0058 (t 2,332, N ~291) |
| Ficura Small or Illiquid, Weg A*: -0,0391 / 0,609 | **-0,064** | - |
| Ficura M > 1 Mio/V > 100 Tsd. (breit), S -0,0012 (t -0,216) | ~ -0,003 (sigma 0,148) | ~ -0,0006 |
| Bianchi 1 Tag, Dezil, gleichgew., S 2,187 %, sigma 6,889 % | 0,090 (Reversal-IC, Tageshorizont) | - |
| Bianchi 1 Tag, Dezil, wertgew., S 0,558 % | 0,023 (Reversal-IC, Tageshorizont) | - |

- Fuer IC >= 0,020 verlangt Weg B t >= 6,31 (N 260) bzw. 6,68 (N 291) bei SD 0,0511; bei SD 0,0425 t >= 7,59 /
  8,03. Keine Quelle erreicht das (max. 3,72, LTW-Terzil).
- Diagnose der Luecke A vs. B: aus Ficura folgt eine implizite SD(IC_t) der Quelle von 0,033 / 0,137 = **0,24** je
  Woche (Programm 0,051). Die Long-Short-Reihe ist durch zeitlich stark schwankendes sigma_xs,t und Ausreisser
  verrauscht; Weg B ist daher eine Untergrenze, Weg A/A* ein Mittelwert unter Normalitaet. Welcher Weg fuer die
  Programm-Registrierung massgeblich ist, bleibt Entscheidung des Orchestrators.
- Beta: LTW 1-Wochen-Long-Short beta -0,021, R^2 0,000; Ficura BTC-alpha 1,31 % vs. roh 1,36 % - die
  Beta-Neutralisierung aendert den Spread in beiden Quellen kaum (fuer diese Konstruktionen).

## 5. B - VRP (Almeida et al., v1) [PDF]

| Pruefpunkt | Befund v1 | Fundstelle |
|---|---|---|
| Stichprobe exakt | Deribit-Optionstransaktionen 2017-07-01..2022-12-17 (1.301 Handelstage, 7.832.590 Transaktionen); taegliche BTC-Preise (Blockchain Research Center; Deribit-Index) 2014-01..2022-12 | S. 8, S. 10 Tab. 1 |
| Tage im VRP-Mittel | 547 Tage mit interpolierter 27-Tage-IV; im Cluster-Mittel 482 Tage (BVIX-Route) bzw. 505 (Q-Dichte-Route) | S. 17; S. 25 Tab. 2 |
| Tabelle (unbedingt, annualisiert, **Varianz**) | BVIX-Route: sigma^2_Q **0,71**, sigma^2_P **0,57**, VRP **0,14**; Q-Dichte-Route: 0,63 / 0,57 / 0,07 | S. 25 Tab. 2 Panel B; Text S. 24 |
| Regime (BVIX-Route) | HV: 0,88 / 0,76 / 0,12; LV: 0,50 / 0,33 / 0,17 ("low volatility cluster ... higher VRP") | S. 25 |
| Herkunft 0,72 / 0,58 / 0,14 | **nicht v1, sondern v2**: "proxied by the squared Bitcoin Volatility Index (BVIX) and the realized variance (BRV) ... 0.72 and 0.58 ... The corresponding variance risk premium is 0.14" (v2 S. 21; Tab. 2 S. 22, 1.017 Tage; HV 0,86/0,74/0,12, LV 0,46/0,29/0,17) | v2 S. 21-22 |
| Herkunft "7-14 %" | v1 S. 3: "the annualized BTC VRP ... averaging between 7 and 14%, compared to a 2% VRP for the S&P500" = die zwei Q-Routen der Tab. 2 (Q-Dichte 0,07; BVIX 0,14). Einheit: annualisierte Varianz x 100 (vgl. Umrechnung BTZ 18,30 %^2 monatl. -> 2,196 %, S. 59 Tab. B12) - **keine Vol-Punkte** | v1 S. 3, 25, 59 |
| Q-Proxy | VIX-Methode (CBOE), nahe/naechste Laufzeit auf tau interpoliert, x 365/tau (Gl. 27); Horizont **27 Tage** ("27-day investment horizon", S. 24; "monthly (tau = 27)", S. 17; tau = 27/365, S. 18); Q-Varianz = Mittel von BVIX^2 ueber die Cluster-Tage | S. 21, 42 (Anh. A.2) |
| P-Definition | RV_t = 365/tau x Summe_{l=1..tau} r^2_{d,t-l}, r_d = log S_t/S_{t-1}: **Tagesrenditen, nachlaufend** ("over the past tau days"), tau = 27; P-Varianz = Stichprobenmittel der RV_t | S. 16, 21 |
| Alternative P (Dichte) | Fn. 17: unbedingt 0,66, VRP 0,05 (-0,02); Anhang Tab. B5: VarP 0,68, VRP 0,04 (BVIX) / -0,04 (Q-Dichte) - Fn. und Tabelle widersprechen sich leicht | S. 24 Fn. 17; S. 54 Tab. B5 |
| IV-Niveau | Transaktions-IV Mittel 0,82 (Calls) / 0,89 (Puts), Median 0,77 / 0,82 (alle Laufzeiten/Moneyness); Text "average BTC IV level of 0.82 basis points" (sic); ATM (0,97-1,03), 27-33 Tage: 0,73 (Calls) / 0,74 (Puts) | S. 10 Tab. 1; S. 9; S. 39 Tab. A1 |
| Underlying / Boerse | BTC, Deribit, bar abgerechnete europaeische Optionen, Lot 1 BTC; Zins = 0 gesetzt | S. 8-9 |
| Rundung | Q-Dichte: 0,63 - 0,57 = 0,06, Tabelle 0,07 (Rundung der Quelle) | S. 25 |

Umrechnung in Vol-Punkte [abg.] (RMS-Niveau = sqrt der mittleren Varianz; L = 0,5 ln(Q/P); pi-2 = 61,55 % x
(exp(L) - 1); pi-1 = sqrt(61,55 %^2 + V) - 61,55 %; Regeln wie RECHERCHE_BELEGE 4.3):

| Route | sqrt(Q) | sqrt(P) | Vol-Punkte | L | pi-2 | pi-1 |
|---|---:|---:|---:|---:|---:|---:|
| v1 BVIX (0,71/0,57) | 0,8426 | 0,7550 | 8,76 | 0,1098 | **7,14** | 10,48 (V 0,14) |
| v1 Q-Dichte (0,63/0,57) | 0,7937 | 0,7550 | 3,87 | 0,0500 | **3,16** | 5,45 (V 0,07) |
| v1 BVIX HV (0,88/0,76) | 0,9381 | 0,8718 | 6,63 | 0,0733 | 4,68 | 9,08 (V 0,12) |
| v1 BVIX LV (0,50/0,33) | 0,7071 | 0,5745 | 13,27 | 0,2078 | 14,21 | 12,53 (V 0,17) |
| v2 BVIX (0,72/0,58) | 0,8485 | 0,7616 | 8,70 | 0,1081 | 7,03 | 10,48 (V 0,14) |

Bei Mittel-IV 0,82 (Tab. 1) und V 0,14: RV 0,730, 9,03 VP; bei ATM-27-Tage-IV 0,73: 10,32 VP; bei V 0,07: 4,4..5,0 VP.

Regime-Aussage: v1 und v2 (beide zulaessig) sagen uebereinstimmend LV -> hoehere VRP (v1 S. 1, 25; v2 S. 1, 21).
Die gegenteilige Formulierung im OIRPCMR-README (RECHERCHE_BELEGE 4.2) stammt nicht aus v1/v2; ob sie der
SSRN-Fassung 2026 entspricht, wurde wegen Sperre nicht geprueft (UNBELEGT).

## 6. C - Deribit-Dokumente (V-5a/c) [PDF, Wortlaut]

| Aussage (woertlich) | Dokument / Stand | S. |
|---|---|---|
| "settlement refers to the routine daily mark-to-market process that occurs every day at 08:00 UTC for futures and perpetual contracts" | Settlement, ~2026-09 | 1 |
| "Daily settlement at 08:00 UTC: Every day at 08:00 UTC, Deribit runs the official settlement process for all instruments." Handelspause waehrend des Settlements ("settlement_in_progress") | Settlement | 2 |
| "Non-expiry days: The prevailing index price around 08:00 UTC is used for daily settlements of perpetuals and futures." | Settlement | 4 |
| "Final expiry days: For instruments expiring at 08:00 UTC, the delivery price is the 30-minute time-weighted average price (TWAP) of the relevant Deribit Index, calculated from 07:30 to 08:00 UTC. A snapshot is taken every 4 seconds during this period." | Settlement | 4 |
| "The delta of expiring options and futures decays linearly to zero over the last 30 minutes before expiry" | Settlement | 4 |
| "Futures: At expiry (usually Friday 08:00 UTC), the contract is cash-settled at the official delivery price (30-minute TWAP of the index)." Optionen europaeisch, bar | Settlement | 4 |
| "The price used for the settlement and delivery of most of the derivatives contracts on Deribit is calculated as the time-weighted average of the relevant Deribit index over the last 30 min before the expiry. The Deribit index gets calculated every 4 seconds. Therefore, the final delivery price is the time-weighted average of the 450 index prices recorded in the last 30 minutes before the expiry." "Daily settlement happens every day at 08:00 UTC." | Features, ~2026-08 | 2 |
| Index neu: Mid aus Best Bid/Ask der einbezogenen Boersen, Werte ausserhalb +/-0,5 % um den Median auf die Bandgrenze gesetzt, dann gleichgewichtetes Mittel | Features | 1 |
| "The price used for settlement and delivery of contracts will be calculated as the time-weighted average of the Deribit index over the last half hour before expiration. The Deribit index gets calculated every 6 seconds. So the final delivery price is the average of 300 index prices taken in the last 30 minutes before expiration." | Medium, 2019-02-01 | 5 |
| "(future trades settle daily at 08.00 UTC)" | Medium, 2019-02-01 | 6 |
| Index alt: 6 Boersen (Bitstamp, Gemini, Bitfinex, Itbit, Coinbase, Kraken), hoechster und tiefster Mid gestrichen, 4 x 25 %; "Currently Bitfinex is disabled" | Medium, 2019-02-01 | 4-5 |
| "As of 3 February 2020 Deribit will start offering daily Deribit BTC index options ... The daily options will be tradable the day immediately preceding the expiry day (8 AM UTC) and will therefore have an initial lifetime of two trading days ... they will expire every day at 08 AM UTC" | Insights, 2020-01-29 | 1 |
| "Monday 3 Feb 2020 between around 12 AM UTC we will launch the Tuesday and Wednesday expiry. As of then the new series will be listed automatically every day 8 AM UTC expiring 2 days (48 hours) later." -> erste Tagesverfaelle **2020-02-04 und 2020-02-05** 08:00 UTC [abg.] | Insights, 2020-01-29 | 2 |
| "Daily options expire every day at 08:00 UTC. Weekly options expire on each Friday of each week at 08:00 UTC. Monthly options expire on the last Friday of each calendar month at 08:00 UTC. Quarterly options expire on the last Friday of each calendar quarter at 08:00 UTC." | Contract Introduction Policy, ~2026-10-13 | 3-4 |
| "New daily options are listed each day at 08:00 UTC. For BTC and ETH options ... there are four daily expiries." Futures: "Daily futures expire every day at 08:00 UTC"; weekly "every Friday at 08:00 AM UTC"; monthly letzter Freitag; quarterly letzter Freitag im Quartal; Ueberschneidungen werden nicht dupliziert | Contract Introduction Policy | 1-4 |
| Lineare Optionen: Ausuebung zuerst in den Future gleicher Faelligkeit, "live for all linear options from early April 2026" | Contract Introduction Policy | 2 |

Alt/neu: Index-Takt 6 s (2019) -> 4 s (2026); 300 -> 450 Werte; Fenster unveraendert die letzten 30 Minuten vor
Verfall, Verfall 08:00 UTC (2019 indirekt ueber "settle daily at 08.00 UTC", 2020 ausdruecklich fuer Optionen,
2026 ausdruecklich 07:30-08:00 UTC). Tagesoptionen: 2020 Laufzeit 2 Tage, 2026 vier Tagesverfaelle (4 Tage).
**UNBELEGT** bleiben: Datum der Umstellung 6 s -> 4 s und der Index-Methodik; Beginn der Wochenverfaelle; dritter
Tagesverfall 2023-04-26 (nur LinkedIn-[P-Snip] aus der Vorarbeit); Kontinuitaet 2020-2024 ohne Unterbrechung.

## 7. F - He/Manela/Ross/von Wachter, v7 (Sep 2026; Stichprobe bis 2024-03-11) [PDF]

- Fassung: v7, arXiv-Stempel 17 Sep 2026; "First draft December 2022. This draft September 2026." (S. 1).
- Daten: BTC, ETH, BNB, DOGE, ADA; Perp- und Spotpreise stuendlich von Binance, Funding alle 8 h; Beginn je Coin
  2020-01-08 (BTC/ETH), 2020-02-10 (BNB), 2020-07-10 (DOGE), 2020-01-31 (ADA); Ende 2024-03-11 (S. 24-25, Tab. 2).
- Strategie: Zeitreihe je Coin, kein Querschnitt; bei rho > 0 Perp short / Spot long, umgekehrt bei rho < 0,
  Schliessen bei erstem Nulldurchgang; ohne Handelskosten (S. 34). Einheit laut Tab. 6: annualisierte
  Ueberschussrenditen in % (S. 36); Tab. 8 selbst nennt keine Einheit [abg.: gleiche Einheit].
- Zerlegung (S. 40, Tab. 8), Spalte "All" (2020..2024-03): BTC Rendite 52,55 = Preis 37,61 + Funding 14,94;
  ETH 62,83 = 45,05 + 17,78; BNB 134,91 = 111,75 + 23,16; DOGE 180,96 = 164,26 + 16,70; ADA 155,13 = 135,50 + 19,62.
  Funding-Anteil [abg.]: BTC 28 %, ETH 28 %, BNB 17 %, DOGE 9 %, ADA 13 %. Jahresweise BTC-Funding: 2020 19,63;
  2021 30,05; 2022 4,09; 2023 5,46; 2024 (bis 03-11) 18,15. Autoren: "price convergence plays a dominant role in
  total trading returns, while funding rate payments have a more minor role" (S. 40).
- Bezug zu theta: nur indirekt - Arbitrage-Zeitreihe (Spot gegen Perp, gehedgt), kein Querschnitts-Carry; daraus
  ist der unkompensierte Carry-Anteil eines Querschnitts-Funding-Sorts nicht ableitbar. **theta: weiter UNBELEGT.**

## 8. Folgen fuer das Programm

1. **IC-Prior (A, D, E):** Ein beta-neutraler Wochen-IC >= 0,020 ist **nicht als Punkt belegt**. Primaer belegt
   ist ein Band: Weg B (gleiche SE-Logik wie das Programm) 0,004..0,012 fuer alle positiven Befunde; Weg A* aus
   einer Quelle ohne externe sigma-Annahme 0,033 (Ficura, nur Large and Liquid >= 50 Mio/5 Mio USD,
   gleichgewichtet, 2017/06-2022/12); LTW 0,03..0,07 (wertgewichtet, sigma-abhaengig) bzw. FM > 10 Mio 0,03..0,05
   bei t 1,67. Das Vorzeichen haengt am Universum: breit/gleichgewichtet ~0 oder negativ (LTW FM > 1 Mio:
   -0,011..-0,019; Ficura M > 1 Mio/V > 100 Tsd.: ~0), klein/illiquide Reversal (-0,064). Ficura berichtet zudem,
   dass das Standard-Momentum der grossen Coins seit Anfang 2021 nicht mehr profitabel ist (S. 7). Ein Prior
   >= 0,020 waere nur ueber die Spread-Route und nur fuer ein Large-and-Liquid-Universum vertretbar; die
   Zuordnung des Bybit-Universums (514..603 Perps) zu einer dieser Gruppen ist hier nicht pruefbar.
2. **VRP-Prior (B):** v1 liefert 0,71 / 0,57 / 0,14 (BVIX-Route), nicht 0,72 / 0,58 (das ist v2). In
   Vol-Punkten 8,76 VP, L 0,110, pi-2 **7,14 VP** (v2: 7,03), pi-1 10,48 VP. Die zweite Q-Route der Quelle
   (Q-Dichte) gibt 0,07 -> pi-2 **3,16 VP**, pi-1 5,45 VP; mit Dichte-P ist die VRP der Q-Dichte-Route negativ
   (Tab. B5). Der zentrale FEASIBILITY-Wert 9,47 VP wird von v1/v2 nicht gestuetzt; 7,0 VP ist die obere der
   beiden Quellrouten, nicht die untere. RV ist nachlaufend (27 Tage) - fuer Mittelwerte unkritisch.
3. **V-5c:** Zeitlage primaer belegt: TWAP 07:30-08:00 UTC, 4-s-Takt (Deribit Settlement, Stand ~2026-09,
   woertlich); dieselbe 30-Minuten-Regel vor dem 08:00-Verfall bereits 2019 (Deribit selbst, Medium, 6-s-Takt) und
   08:00-UTC-Verfall 2020 (Insights). Fuer 2020-2024 gilt die Regel an beiden Endpunkten gleich; ein Beleg fuer
   lueckenlose Geltung und das Umstellungsdatum 6 s -> 4 s fehlt (datenseitig ueber B-4 pruefbar).
4. **V-5a/b Ereignismenge:** Tagesverfaelle BTC ab 2020-02-04 (Listung 2020-02-03), Wochen Freitag 08:00 UTC,
   Monat/Quartal letzter Freitag 08:00 UTC primaer belegt (Stand 2026); Beginn der Wochenverfaelle UNBELEGT.

## 9. Kontamination (bitte ins Register)

- `ssrn-5374295.pdf` (gesperrt, Daten bis 2026-03): beim Datums-Scan Satzfragmente ohne Zahlen gesehen (S. 3 "...
  during our sample period, so we expect such interactio..."; S. 25 "The average total retu..."; S. 28 "These
  variables span f..."; S. 47 "At their peak, the BP"); S. 62 Literaturtabelle anderer Studien (identisch mit v1
  S. 59 / v2 S. 50). Kein Ergebniswert der SSRN-Fassung gesehen, nichts verwendet. Abstract nicht gelesen.
- `2212.06888v7.pdf` (zulaessig): S. 10 erwaehnt Liquidationen "during the October 2025 crypto flash crash"
  (Ereignis im Urteilsfenster; kein Marktniveau gesehen, nicht verwendet). S. 7 Satzfragment aus der Einleitung
  beim Scan gesehen. Abbildungen (u. a. Funding-Verlauf, Fig. 2) nicht betrachtet.
- v2 S. 8 / SSRN S. 9: Firmenereignis "In May 2025 ... acquired by Coinbase" (kein Marktniveau).
- Deribit Contract Introduction Policy S. 2: Produktaenderung "early April 2026" (Abwicklung linearer Optionen ueber
  Futures) - Regel, kein Marktniveau. Deribit Insights S. 2: Titel von Beitraegen Sep/Okt 2026 (Produktnachrichten,
  keine Niveaus). Medium S. 8: Leserkommentar 2025 (Spam, ignoriert, Inhalt nicht uebernommen).
- v1/v2 Abbildungen A4 (BVIX vs. DVOL), B4-B6 nicht betrachtet (nur Text). Keine BTC-, DVOL-, Funding- oder
  Volatilitaetsniveaus ab 2024-07-01 gesehen.

## 10. Weiter fehlende PDFs

1. Liu/Tsyvinski/Wu, J. Finance 77(2) 2022 (Endfassung; JF-Zahlen 2,5 %/3,1 %/... bleiben [sek] aus der Vorarbeit;
   SE-Korrektur dort pruefen).
2. Liebi, "Is there a value premium in cryptoasset markets?", Economic Modelling 109 (2022) 105777 (Bibliographie
   laut Ficura S. 17, Ref. [9]): FM mit Beta-Kontrolle.
3. Dobrynskaya, SSRN 3913263 / JAI 2023 (1-4-Wochen-Momentum, NW-t, Faktor-Alphas).
4. Shen/Urquhart/Wang (2020) FRL 34, 101248 (woechentliches Reversal, gleichgewichtet) und Zaremba et al. (2021)
   IRFA 78, 101908 (groessenabhaengiges Tages-Reversal/Momentum) - neue Spuren aus Ficura S. 17; Stichproben
   UNBELEGT.
5. Chi/Hao/Hu/Ran, JFM 43(8) 2023 (Basis-Spreizung je Portfolio; theta-Analogon).
6. Weiss et al., FRL 107 (2026) 110340 (V-5b: Groesse r_pre in bp, Fenster, Verfallsmenge; Stichprobe pruefen).
7. Blasco/Corredor/Satrustegui, IREF 85 (2023) (Renditerichtung vor Verfall).
8. Deribit: archivierte Doku mit Datum der Umstellung 6 s -> 4 s und neuer Index-Methodik; Ankuendigung der
   Wochenverfaelle; Ankuendigung dritter Tagesverfall (2023-04-26); "Inverse Options"/"Change To Inverse Option
   Delivery Process" mit Datum.

Skripte (ausserhalb des Repos): `scratchpad/pdf_belege/extract.py`, `header.py`, `period.py`, `calc.py`.
