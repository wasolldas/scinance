# Recherche: vier offene Belege (fm8-Prior, theta, V-5b/c, VRP-Volltext) - 2026-10-18

Auftrag: `SPEC_RECHERCHE_belege` (Orchestrator, 2026-10-18). Nur Literatur/Primaerquellen, keine Rechnung auf
Programmdaten. Nichts committet. Kennzeichnung: `[P-Snip]` Primaerquelle (Anbieter/Autoren selbst), Wortlaut nur
ueber Suchmaschinen-Auszug; `[P-Code]` Code der Autoren, direkt gelesen; `[sek]` Sekundaerquelle oder
Suchmaschinen-Zusammenfassung eines Papiers; `[abg.]` hier abgeleitet (Formel offen). Fehlendes = UNBELEGT.

## 0. Zugriffslage (zuerst lesen)

- WebFetch: `getaddrinfo ENOTFOUND` fuer jeden Host (arxiv.org, Verlage, Deribit, Medium, Repositorien).
  curl ueber den Agent-Proxy: `CONNECT 403` fuer arxiv.org, export.arxiv.org, ssrn, nber, researchgate,
  sciencedirect-nahe Repositorien, support.deribit.com, docs.deribit.com, insights.deribit.com, medium.com u. a.
  Erreichbar: nur raw.githubusercontent.com (oeffentliche Dateien) und WebSearch.
- Folge: **Kein Volltext eines Papiers gelesen.** Alle Papierzahlen sind `[sek]` (Such-Auszug). Die
  Such-Zusammenfassungen koennen irren (einmal beobachtet: Suchbegriffe der Anfrage als "Stichprobe" zurueckgespielt);
  jede Zahl unten ist vor einer Registrierung im PDF zu pruefen (Liste in Abschnitt 6).
- Direkt gelesen: Autoren-Code zu L-1 (GitHub `ratmir-miftachov/BTC-premia`, README, `config/*.yaml`,
  `src/05_risk_analysis/variance_risk_premium_analysis.m`, `src/06_volatility/bvix_calculation.py`) und README von
  `wang-zjin/OIRPCMR` - nur Code/Metadaten, keine Ergebnisdateien (die Repos enthalten keine Daten-CSV).

## 1. Frage 1 - Prior fuer den beta-neutralen Querschnitts-IC (Momentum / Kurzfrist-Reversal, Wochenhorizont)

### 1.1 Quellen (Stichprobe vor 2024-07)

| # | Quelle | Stichprobe / Markt | Befund | Beta-Bezug | Status |
|---|---|---|---|---|---|
| Q1-1 | Liu/Tsyvinski/Wu, "Common Risk Factors in Cryptocurrency", J. Finance 77(2) 2022, 1133-1177 (NBER WP 25882, 2019) | Spot, CoinMarketCap, Coins > 1 Mio USD; NBER-Fassung 1.707 Coins, 2014-01..2018-12 (Such-Auszug "beginning of 2014 to the end of 2018"); JF-Fassung 1.827 Coins, Ende UNBELEGT, jedenfalls vor 2022 | Quintil-Long-Short, woechentlich: 1-Wochen-Momentum **2,7 %/Woche** (NBER) bzw. **2,5 %/Woche** (JF), 2-/3-/4-Wochen 3,3/4,1/2,5 % (NBER) bzw. 3,1/3,1/2,2 % (JF); 16 Wochen insignifikant (0,4 %) | Krypto-CAPM (CMKT): **R^2 der Long-Short-Strategie "roughly zero" fuer 1-Wochen-Momentum**, CAPM-Alphas gross und signifikant; Drei-Faktor-Modell (CMKT, CSMB, CMOM) erklaert sie | [sek] Such-Auszug (NBER-PDF, Yale-PDF, vLex); t-Werte und Alpha-Zahlen NICHT gesehen |
| Q1-2 | Dobrynskaya, "Cryptocurrency Momentum and Reversal", SSRN 3913263; J. Altern. Invest. 2023 (doi 10.3905/jai.2023.1.189) | 2.000 groesste Coins, 2014-2020, Sortier-/Halteperioden 1 Woche..2 Jahre | Kurzfrist-Momentum bei 2-4 Wochen, Umschlag in Reversal nach etwa 1 Monat; Renditen "economically large, statistically significant" | "generally not exposed to standard cryptocurrency risk factors" (keine Zahlen gesehen) | [sek] Abstract; NW-t (12 Lags) im Volltext |
| Q1-3 | Ficura, "Impact of size and volume on cryptocurrency momentum and reversal", FFA Working Papers 5:003 (2023) | Spot; Stichprobe UNBELEGT, Veroeffentlichung 2023 -> Ende vor 2023-06 | Woechentliches Reversal nur bei kleinen/illiquiden Coins (**t = -7,31**); grosse/liquide Coins zeigen **woechentliches Momentum (t = 2,33)**; Abstand zum 1-Wochen-Hoch t = -9,03 (klein) / 4,93 (gross) | keiner gesehen | [sek] Abstract (RePEc); N Wochen, Regressionstyp UNBELEGT |
| Q1-4 | Bianchi/Babiak/Dickerson, "Trading volume and liquidity provision in cryptocurrency markets", J. Banking Finance 142 (2022) | USD-Paare, mehrere zentrale Boersen, 2017-03-01..2022-03-01 | Kurzfrist-Reversal (als Mass fuer Liquiditaetsbereitstellung) konzentriert in Paaren mit geringer Handelsaktivitaet, kleiner/volatiler/illiquider | keiner gesehen | [sek] Abstract; Horizont (woechentlich?) UNBELEGT |
| Q1-5 | Chi/Hao/Hu/Ran, "An empirical investigation on risk factors in cryptocurrency futures", J. Futures Markets 43(8) 2023, 1161-1180 | OKEx-Futures (datiert), 12 groesste Coins, 2017-11..2021-03 | Momentum-Faktor signifikant, aber "not statistically powerful"; Basis staerkster Querschnitts-Praediktor; Tagesfaktoren deutlich staerker als Wochenfaktoren, Monat insignifikant | keiner gesehen | [sek] Abstract |
| Q1-6 | "Is there a value premium in cryptoasset markets?", Economic Modelling (2022), S0264999322000232 | woechentlich, 2017-07-04..2020-10-06 (170 Wochen) | Fama-MacBeth je Woche mit Markt-Beta, Groesse, Momentum u. a. - Momentum-Koeffizient NICHT im Auszug | Beta als Kontrolle im FM-Modell | [sek]; Tabelle (Abschn. 5.3) zu pruefen |

Nicht verwendet (Stichprobe reicht in die Urteilsfenster oder unbekannt, Ergebniszahlen nicht weiter gelesen):
"On survivor cryptocurrency momentum" (Elsevier 2026; Stichprobe 2017-01..2024-08 - reicht in die Urteilsfenster);
Grobys/Kolari/Sandretto/Shahzad/Aijo, "Cryptocurrency momentum has (not) its moments", FMPM 2025 (Stichprobe
UNBELEGT; Abstract qualitativ gesehen, betrifft Ausreisser-Abhaengigkeit von Momentum-Renditen); "Cryptocurrency
Market Risk-Managed Momentum Strategies" (2025, Stichprobe UNBELEGT); Cao/Luo/Cheng/Dong, "Anatomy of
Cryptocurrency Perpetual Futures Returns", SSRN 6365329 (2026, Stichprobe UNBELEGT, Abstract qualitativ gesehen).

### 1.2 Umrechnung in einen IC (offen, zwei Wege)

**Weg A - Spread -> IC** [abg.]: Bei bivariat-normalem Signal/Rendite ist der erwartete Long-Short-Spread zwischen
oberstem und unterstem Anteil q: `S = IC * sigma_xs * 2 * phi(z_q) / q`, mit `k = 2 * phi(z_q)/q` =
**2,800 (Quintil)** bzw. **3,510 (Dezil)**; Rang-IC ~ 0,955 * Pearson-IC bei kleinem IC. Also `IC = S / (k * sigma_xs)`.
`sigma_xs` (Querschnitts-SD der Wochenrendite im LTW-Universum, wertgewichtet) ist **UNBELEGT** - Band als Annahme:

| S (LTW 1 Woche) | sigma_xs 10 % | 15 % | 20 % | 30 % | 45 % |
|---|---:|---:|---:|---:|---:|
| 2,5 %/Woche (JF) | 0,089 | 0,060 | 0,045 | 0,030 | 0,020 |
| 2,7 %/Woche (NBER) | 0,096 | 0,064 | 0,048 | 0,032 | 0,021 |

Annahmen/Schwaechen: Normalitaet (Krypto-Renditen stark leptokurtisch, Spread dann von Ausreissern getragen);
wertgewichtete Quintile (Spread spiegelt grosse Coins, deren sigma_xs kleiner ist); Brutto-Spread; Universum
Spot-Coins 2014-2018 inkl. Mikro-Caps, nicht Bybit-Perps; Beta-Anteil laut LTW nahe null (CAPM-R^2 ~ 0), d. h. fuer
1-Wochen-Momentum waere roh ~ beta-neutral - nur fuer diese Konstruktion.

**Weg B - Informationsquote -> IC** [abg.]: Wenn `LS_t ~ k * sigma_xs * IC_t`, ist die Wochen-IR der Long-Short-Reihe
(`t / sqrt(N)`) ungefaehr die IR der IC-Reihe; uebertragen auf das Programm: `IC_aequiv = (t / sqrt(N)) * SD(IC_t)`.
Mit der Programm-Nuisance SD fm8 = 0,0511 (W1-stress mom1, PROGRAMM_BILANZ 2.1, kein neuer Datenzugriff) braucht
IC >= 0,020 eine Wochen-IR >= **0,391** (W2-SD 0,0425: 0,471), d. h. t >= 0,391 * sqrt(N): **N = 170 -> t >= 5,1;
N = 260 -> t >= 6,3; N = 365 -> t >= 7,5**. Beispiele: t = 2,33 (Ficura) bei N = 260 bzw. 415 -> 0,0074 bzw. 0,0058;
hypothetisch t = 3,0 bei N = 260 -> 0,0095. Schwaechen: Long-Short-IR <= IC-IR (wertgewichtete Konzentration erhoeht
das Rauschen), also eher Untergrenze; LTW-t-Werte nicht gesehen.

### 1.3 Ergebnis Frage 1

- Ein **Rang-IC nach Beta-Neutralisierung** wird in keiner gefundenen Quelle berichtet. **IC >= 0,020 fuer den
  beta-neutralen Effekt: UNBELEGT.** Die beiden Umrechnungswege liegen fuer dieselbe Literatur um Faktor ~5..10
  auseinander (A: 0,02..0,10 je nach unbelegtem sigma_xs; B: ~0,006..0,010 bei den gesehenen t-Groessen) - keine
  belastbare Zuordnung oberhalb oder unterhalb von 0,020.
- Belegt [sek] sind nur: (a) Richtung bei Wochenhorizont: Momentum bei grossen/liquiden Coins (LTW 2014-2018, Ficura
  t = 2,33), Reversal bei kleinen/illiquiden (Ficura t = -7,31; Bianchi et al. 2017-2022); Umschlag in Reversal nach
  ~1 Monat (Dobrynskaya 2014-2020); (b) Beta-Anteil fuer LTW-1-Wochen-Momentum klein (CAPM-R^2 ~ 0); (c) in datierten
  Futures (OKEx, 12 Coins, 2017-2021) Momentum schwach, Tagesfrequenz staerker als Woche.
- Fuer Bybit-Perps (Universum 514..603) existiert keine Quelle mit Stichprobe vor 2024-07, die gefunden wurde.

## 2. Frage 2 - theta fuer den Funding-Carry im Querschnitt (Wochenhorizont)

- **UNBELEGT.** Keine Quelle gefunden, die fuer Perp-Funding im Querschnitt (niedrigstes Funding-Dezil gegen
  Universum, Wochenhorizont, Stichprobe vor 2024-07) den nicht durch die Preisbewegung kompensierten Anteil angibt.
- Naechste, aber nicht zaehlende Quellen:
  - Chi/Hao/Hu/Ran (JFM 2023; OKEx-datierte Futures, 12 Coins, 2017-11..2021-03): Basis ist der staerkste
    Querschnitts-Praediktor; Basis-Faktor "abnormal return of 329,21 % per year (t = 7,10)" [sek, Such-Auszug].
    Qualitativ: der Carry wird im Querschnitt datierter Futures nicht voll durch die Preisbewegung kompensiert
    (theta > 0). Zaehlt nicht: datierte Futures (Konvergenz in der Rendite), Tagesrebalancing, 12 Coins, keine
    Basis-Spreizung der Portfolios gesehen -> theta nicht berechenbar.
  - He/Manela/Ross/von Wachter, "Fundamentals of Perpetual Futures", arXiv 2212.06888 (v1 2022-12; spaetere
    Fassungen mit Stichprobe bis 2024 -> nur v1 zulaessig): Zeitreihen-Arbitrage je Coin (Zerlegung in Konvergenz
    und Funding), kein Querschnitt.
  - Koijen/Moskowitz/Pedersen/Vrugt (2018, Carry), Christin et al. (2022, Crypto Carry Trade), Schmeling/Schrimpf/
    Todorov (BIS, Crypto carry): Zeitreihen- bzw. anlageklassenuebergreifend, wie in DEC-93 E2 bereits gefuehrt.
- Nicht verwendet (Stichprobe reicht in die Urteilsfenster): Fayez Junior, SSRN 6701738 (Binance-Perps 2022-07..
  2026-04); Yang, SSRN 7397158 (BTC/ETH 2020-2026); Inan, "Predictability of Funding Rates", SSRN 5576424 (2025,
  Stichprobe UNBELEGT); "Cryptocurrency as an Investable Asset Class: Coming of Age", arXiv 2510.14435 (2020-2025);
  Cao et al. SSRN 6365329 (s. o.). Siehe Abschnitt 5 (Kontamination).

## 3. Frage 3 - V-5b/c (A2, Deribit-Verfallskalender, r_pre 07:30-08:00 UTC)

### 3.1 Zeitlage Settlement/Delivery (V-5c, Datenteil)

| Aussage | Quelle | Status |
|---|---|---|
| Fuer Instrumente mit Verfall 08:00 UTC ist der Delivery-Preis der **30-Minuten-TWAP des jeweiligen Deribit-Index, 07:30-08:00 UTC**, Schnappschuss alle 4 Sekunden | Deribit Support, "Settlement", support.deribit.com/hc/en-us/articles/29734325712413-Settlement (aktuell, Datum UNBELEGT) | [P-Snip] |
| "time-weighted average of 450 index prices recorded in the last 30 minutes before the expiry" | Deribit Support, "Features", .../25944687755293-Features | [P-Snip] |
| Delta verfallender Optionen und Futures faellt in den letzten 30 Minuten linear auf null | Deribit Support, "Settlement" | [P-Snip] |
| Taegliches Settlement (Futures/Perps) 08:00 UTC; Optionen ohne taegliches Settlement; an Nicht-Verfallstagen Indexpreis um 08:00 statt TWAP | Deribit Support, "Settlement" | [P-Snip]; der Wortlaut "Indexpreis um 08:00" nur sinngemaess im Auszug |
| Aeltere Fassung: "The price used for settlement and delivery of contracts will be calculated as the time-weighted average of the Deribit index over the last half hour before expiration. The Deribit index gets calculated every 6 seconds" (300 Werte); "Future trades settle daily at 08.00 UTC" | Deribit Official (Medium), "Deribit General User Information", medium.com/deribitofficial/deribit-general-user-information-8d7d0235b68a (undatiert) | [P-Snip]; Datum UNBELEGT |
| Neueres Delivery-Verfahren fuer inverse Optionen geaendert, Verfallspreis weiterhin 30-Minuten-TWAP vor Verfall | Deribit Support "Inverse Options" (.../31424939096093) und Deribit Insights "Change To Inverse Option Delivery Process" | [P-Snip]; Datum der Aenderung UNBELEGT |

Folge: Die Zeitlage "Settlement = TWAP 07:30-08:00 UTC" ist fuer die aktuelle Regel [P-Snip] belegt; dieselbe
Regel (30 Minuten vor Verfall) steht in einer aelteren Deribit-Fassung mit 6-Sekunden-Index. **Seit wann genau
(und ob ohne Unterbrechung 2020-2024): UNBELEGT** - pruefbar datenseitig ueber B-4 (`public/get_delivery_prices`
gegen Index-TWAP, falls Indexhistorie vorliegt) oder per archivierter Doku.

### 3.2 Verfallskalender (V-5a/b Ereignismenge)

- Woechentliche Optionen verfallen jeden Freitag 08:00 UTC; Monats-/Quartalsoptionen am letzten Freitag des
  Monats/Quartals 08:00 UTC (Deribit "Contract Introduction Policy", .../25944688876957) [P-Snip].
- **Taegliche BTC-Optionen seit 2020-02-03** (handelbar ab dem Vortag; Deribit Insights "Launch of BTC Daily Options
  on Deribit") [P-Snip]; **ETH-Tagesoptionen ab 2020-02-17/18** (Deribit-Ankuendigung laut [sek] tokenpost/
  cryptoworld); **dritter Tagesverfall BTC/ETH ab 2023-04-26** (Deribit, LinkedIn-Post) [P-Snip].
- Erste BTC-Optionen auf Deribit November 2016 [sek]. **Beginn der Wochenverfaelle: UNBELEGT** (Literatur und Snippets
  ohne Datum) -> B-4 (`get_instruments`, expired=true, `settlement_period`).

### 3.3 Literatur zum Preisverhalten um Verfaelle (V-5b, V-5c Richtung)

| # | Quelle | Stichprobe / Markt | Befund | Status |
|---|---|---|---|---|
| V-1 | Weiss et al., "Bitcoin option expiration, gamma exposure, and intraday price reversals", Finance Research Letters 107 (2026) 110340, doi 10.1016/j.frl.2026.110340 | **Deribit-Optionsdaten 2021-01-01..2023-12-31** (laut Such-Auszug), Spot-Boersen des Index und Deribit-Perps; Settlement als 30-Min-Mittel vor 08:00 UTC beschrieben | **V-foermig: signifikant negative Rendite vor dem Verfall, Umkehr danach**; konzentriert an Tagen mit hohem ATM-Open-Interest, am staerksten bei negativer kumulierter Gamma-Exposure (Market-Maker netto short); Handelsaktivitaet steigt um den Verfall; Vermoegenstransfer ~50 Mio USD/Jahr | [sek] Abstract/Auszug. **Groesse von r_pre in bp, genaues Fenster (07:30-08:00?), Verfallsmenge (taeglich/woechentlich/monatlich), N, t: UNBELEGT** |
| V-2 | Blasco/Corredor/Satrustegui, "Is there an expiration effect in the bitcoin market?", Int. Rev. Econ. Finance 85 (2023) 647-663 | regulierte BTC-Futures (CME u. a.), Intraday; Stichprobe UNBELEGT, Veroeffentlichung 2023 -> vor 2024-07 | Volumen, Volatilitaet und Renditen aendern sich signifikant um den Verfall, staerker nahe am Verfallszeitpunkt; CME am deutlichsten; Volatilitaet bis 12 h vor Verfall erhoeht | [sek]; betrifft CME-Verfall (nicht Deribit 08:00 UTC); Renditerichtung UNBELEGT |
| V-3 | Ni/Pearson/Poteshman (2005) | US-Aktien | 16,5 bp (bereits in der Akte) | [sek], Aktien |

Nicht verwendet: "Time-of-day effects in the Bitcoin options market", FRL 2026 (S1544612326005374; Stichprobe UNBELEGT;
Auszug: Aktivitaetsspitze 08:00-09:00 GMT am Settlement); Lachowicz, "Do Gamma Walls Actually Move Bitcoin Prices at
Deribit?", SSRN 5782822 (2025; Stichprobe UNBELEGT; Abstract qualitativ gesehen).

**Ergebnis Frage 3:** Zeitlage [P-Snip] belegt (aktuelle Regel; Kontinuitaet seit 2020 UNBELEGT). Richtung von r_pre
[sek]: negativ vor dem Verfall (V-1, 2021-2023, Deribit) - einzige gefundene Quelle, Volltext ungeprueft.
**Effektgroesse V-5b: UNBELEGT** (V-1 nennt im Auszug keine bp-Zahl).

## 4. Frage 4 - VRP-Volltext (L-1)

### 4.1 Bibliographie

- Almeida, Grith, Miftachov, Wang, "Risk Premia in the Bitcoin Market", arXiv 2410.15195, **v1 2024-10-19, v2
  2025-08-01**; SSRN 5374295 (2025-08-01, dort auch als "Option-Implied Risk Premia and Cryptocurrency Market
  Regimes"). Code: github.com/ratmir-miftachov/BTC-premia; zweites Repo github.com/wang-zjin/OIRPCMR (BTC und
  ETH-Erweiterung). Volltext NICHT gelesen (Egress).

### 4.2 Pruefpunkte

| Pruefpunkt | Befund | Status |
|---|---|---|
| Stichprobe 2017-07..2022-12? | "Bitcoin options data traded on Deribit from July 2017 to December 2022" | [sek] (Substack-Zusammenfassung des Papiers, nur ueber Such-Auszug, nicht geoeffnet). Code: BVIX-Reihe ab `'2017-07-01'` gefiltert; Rohdaten-Ordner `17Jul_18Dec`, `deribit20192020`, Kursdatei `BTC_USD_Quandl_2011_2023.csv`; DVOL-Vergleich nur bis `2023-08-30` (Grafik) [P-Code]. Ende 2022-12 im Code nicht ablesbar |
| Underlying / Quelle | BTC, Deribit-Optionen | [sek] + [P-Code] (DVOL-Vergleichsdatei, Deribit-Ordner) |
| Definition BVRP | Q-Varianz minus P-Varianz, beide **annualisiert**; Tabelle des Skripts: Zeilen "VRP", "Q ann variance", "P ann variance", je Gesamt/Cluster; **zwei Q-Proxys**: Q-Dichte-basiert und VIX-Methode ("Q average vs. VIX average") | [P-Code] `variance_risk_premium_analysis.m` ("This version is what we use in the draft") |
| BVIX / Horizont | CBOE-VIX-Formel, zwei Laufzeiten auf **tau = 27 Tage** interpoliert, Annualisierung mit 365 Tagen | [P-Code] `bvix_calculation.py` (`tau=27`, `T=[ttm1/365, ttm2/365]`, `*365/tau`); Papier: BVIX in Anhang A.2 [sek] |
| P-Varianz (RV) | Dateinamen `VRP_VIX_logRV_*` -> RV aus Log-Renditen; Fenster vorwaerts/rueckwaerts und Laenge: **UNBELEGT** (Code liest nur Zwischendateien) | [P-Code] Dateinamen |
| Mittelwerte | "annualized risk-neutral and physical monthly variances ... 0.72 and 0.58, respectively. The corresponding variance risk premium is 0.14, much higher than that of the S&P 500 Index - approximately 2%" (Bollerslev/Tauchen/Zhou 2009) | [sek] Such-Auszug (Substack-Zitat, vermutlich Papierwortlaut); Tabelle/Seite UNBELEGT |
| Abweichende Angabe | ResearchGate-Fassung: "annualized BTC VRP ... averaging between 7 and 14%, compared to a 2% VRP for the S&P500" | [sek]; Fassung UNBELEGT. Vermutung [abg.]: 7 % und 14 % = die zwei Q-Proxys (Q-Dichte vs. VIX) - im PDF zu pruefen |
| Regime-Aussage | v1-Abstract: Niedrigvol-Regime -> **hohe** BVRP. Abstract im OIRPCMR-README (v2/SSRN 2025): "The low-volatility regime is associated with **lower** BP and BVRP" | Widerspruch zwischen Fassungen. Stichprobe von v2 UNBELEGT (Repo-Ordner `CL2020`, `CL2024`, `SS2025`) - reicht v2 in die Urteilsfenster, ist die v2-Aussage nicht verwendbar. FEASIBILITY A-2 stuetzt pi-1 auf die v1-Aussage |

### 4.3 IV-Niveau und Umrechnung [abg.]

Aus Q = 0,72, P = 0,58 (annualisierte Mittel der Varianzen, [sek]):
- RMS-IV `sqrt(0,72)` = **0,8485**, RMS-RV `sqrt(0,58)` = 0,7616; Vol-Praemie 8,70 Vol-Punkte; `ln(IV/RV)` =
  `0,5 * ln(0,72/0,58)` = **0,1081**.
- Das entspricht der Zeile "0,85" der Tabelle FEASIBILITY A-2 (8,7 VP; 0,108), **nicht** dem zentralen Wert 0,75.
  Mit der Regel pi-2 (`prior = sigma_n * (exp(L) - 1)`, sigma_n 61,55 %) folgt **7,03 Vol-Punkte** = unterer
  Bandrand 7,00 (statt zentral 9,47). pi-1 (V = 0,14 konstant) bleibt 10,48.
- Vorbehalte: `sqrt(Mittel IV^2)` >= Mittel IV (Jensen), das mittlere IV-Niveau liegt also unter 0,85; fuer die
  Programmformel `RV = sqrt(IV^2 - V)` auf Mittelwerten der Varianz ist der RMS-Wert die konsistente Eingabe. Falls die
  massgebliche BVRP 0,07 waere (bei Q 0,72): 4,23 VP, L = 0,051, pi-2 3,23 VP - Faktor ~2 kleiner.
- **Status:** IV-Niveau der L-1-Stichprobe [sek] ~0,85 (RMS); im PDF zu bestaetigen (Tabelle mit 0,72/0,58/0,14,
  Fassung v1, welcher Q-Proxy).

## 5. Kontamination und Ergebnisblindheit (bitte ins Register)

Kein Dokument mit Stichprobe in den Urteilsfenstern wurde geoeffnet. Die Suchmaschinen-Zusammenfassungen haben jedoch
**unaufgefordert** Ergebnisaussagen angezeigt; sie sind nicht verwendet und hier nicht wiedergegeben:
- K-R1 (dreimal): eine Kennzahl der Performance einer **Zeitreihen-Carry-Strategie** (Short-Perp/Long-Spot) fuer 2024
  und fuer 2025, aus arXiv 2510.14435 (Stichprobe 2020-2025). Betrifft Funding/Carry (A1-nah), nicht den Querschnitt.
- K-R2: qualitative Ergebnisrichtung zweier Arbeiten mit Stichprobe bis 2026 (SSRN 6701738: Querschnitts-Signale
  OHLCV/Funding auf 10 Binance-Perps, 8h; SSRN 7397158: Funding-Asymmetrie BTC/ETH).
- K-R3: Presseschlagzeilen zu einem Deribit-Verfall 2026 mit BTC-Preisniveau (kein Vol/Funding/Momentum-Wert).
- K-R4: Abstracts mit unbekannter Stichprobe qualitativ gesehen: Cao et al. SSRN 6365329 (Perp-Querschnitt, 170
  Praediktoren), Lachowicz SSRN 5782822, Grobys et al. FMPM 2025, OIRPCMR/v2-Abstract (BVRP-Regime).
- Die Programm-Nuisance SD fm8 (0,0511 / 0,0425) in 1.2 Weg B stammt aus PROGRAMM_BILANZ (bereits in der Akte),
  nicht aus einem neuen Datenzugriff.

## 6. PDFs, die der Nutzer nachliefern koennte (mit Pruefauftrag)

1. Almeida/Grith/Miftachov/Wang, arXiv 2410.15195 **v1 und v2** (und SSRN 5374295): Datenabschnitt (Ende 2022-12?),
   Tabelle mit 0,72/0,58/0,14 (Seite), Q-Proxy dazu, Herkunft "7-14 %", RV-Definition (vorwaerts? Tage? Log),
   Anhang A.2 (27 Tage), Regime-Aussage v1 vs v2, Stichprobenende v2.
2. Weiss et al., FRL 107 (2026) 110340: Stichprobe 2021-01-01..2023-12-31 bestaetigen; Verfallsmenge; Fenster der
   Pre-Expiry-Rendite (07:30-08:00?); Groesse in bp, t, N; Unterschied taeglich/woechentlich/monatlich.
3. Liu/Tsyvinski/Wu, JF 2022 (doi 10.1111/jofi.13119) bzw. NBER w25882: Momentum-Tabelle (Long-Short, t, CAPM-Alpha,
   Beta/R^2), Stichprobenende JF-Fassung, Gewichtung.
4. Dobrynskaya, SSRN 3913263 / JAI 2023: 1-4-Wochen-Long-Short, NW-t, Faktor-Alphas, Beta.
5. Ficura, FFA WP 5:003 (2023): Stichprobe, N Wochen, Regressionsform (FM? Rang?), Koeffizienten-Einheit.
6. Bianchi/Babiak/Dickerson, JBF 142 (2022) bzw. SSRN 3239670: Reversal-Horizont, Rendite, Markt-Beta.
7. "Is there a value premium in cryptoasset markets?", Econ. Modelling 2022: FM-Tabelle (Momentum mit Beta-Kontrolle).
8. Chi/Hao/Hu/Ran, JFM 43(8) 2023 (Wiley open access): Basis-Spreizung je Portfolio vs. Rendite (theta-Analogon).
9. He/Manela/Ross/von Wachter, arXiv 2212.06888 **v1** (2022-12): Zerlegung Funding vs. Konvergenz (Zeitreihe).
10. Blasco/Corredor/Satrustegui, IREF 85 (2023): Stichprobe, Renditerichtung vor dem Verfall.
11. Deribit-Doku als PDF/Archiv: "Settlement", "Features", "Contract Introduction Policy", Medium "General User
    Information" (Datum), Insights "Launch of BTC Daily Options" (Datum) - fuer [P-Snip] -> Primaer im Wortlaut.
