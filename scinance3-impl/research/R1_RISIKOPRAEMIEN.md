# R1 -- Risikopraemien-Ernte in Krypto-Derivaten

> Quant-Researcher R1, Scinance-3.0-Programm, Phase 3, Stand 2026-09-02.
> Pflichtlektuere gelesen: `scinance3-impl/survey/ERKENNTNIS_KOMPENDIUM.md`
> (vollstaendig), `scinance3-impl/survey/INFRA_OPS_MAP.md` (Abschnitt 1, 2, 6),
> `FINAL_PRD.md` (Par.1, Par.2, Par.5 PARK-Register, Par.8 Multiple-Testing).
> Read-only auf das Repo, keine Datei ausserhalb dieses Scratchpads geschrieben.

---

## 0. Vorspann: die Kostenrechnung, auf der ALLE Kandidaten stehen

Kein Kandidat unten rechnet eigene Kosten aus. Alle zitieren diesen Block.
Neue, extern belegte Zahlen sind als **NEU** markiert; der Rest sind
Programm-Konstanten aus Kompendium B.

### 0.1 Gebuehren-Konstanten

| Groesse | Wert | Quelle |
|---|---|---|
| Perp Taker | 5,5 bp je Bein (11 bp RT) | Kompendium B.3 |
| Perp Maker | 2,0 bp je Bein (4,0 bp RT) | Kompendium B.3 |
| **Spot Bybit VIP0** | **10 bp je Bein -- Maker == Taker, KEIN Maker-Rabatt** | **NEU**, Sekundaerquellen (bitdegree/traders-union 2026); `bybit.com` ist egress-blockiert, vor Registrierung selbst nachpruefen |
| Perp/Futures Derivate-Gebuehr extern bestaetigt | 0,055% Taker / 0,020% Maker | **NEU**, deckt sich exakt mit `FEE_TAKER`/`FEE_MAKER` im Repo |
| Options Maker / Taker | 2 bp / 3 bp **des Index** je Fill | Kompendium B.4 (DEC-45) |
| **Options Delivery-/Exercise-Gebuehr** | **min(1,5 bp Index ; 12,5% des Intrinsic) je Kontrakt, NUR bei ITM-Auto-Exercise; 2 bp fuer SOL/XRP/DOGE/MNT** | **NEU** -- schliesst genau die in Kompendium E.6(a) als blockierend benannte Luecke; Sekundaerquelle, Primaerseite egress-blockiert |
| vega/S | 5,28 bp Index je Vol-Punkt (BTC), 5,10 (ETH) | Kompendium B.5 |
| Options-Quote-Breite (7-14 DTE, \|Delta\| 0,15-0,30) | 0,14 Vol-Punkte (BTC), 0,26 (ETH) voll; Halbspread 0,07 / 0,13 | Kompendium B.6 |
| Perp-Top-of-Book | exakt ein Tick, 0,016-0,054 bp | Kompendium B.2 |

**Umrechnung Gebuehr -> Vol-Punkte (abgeleitet, hier erstmals ausgerechnet):**

| Ereignis | BTC | ETH |
|---|---|---|
| 1 Options-Maker-Fill | 0,379 Vol-Punkte | 0,392 |
| 1 Options-Taker-Fill | 0,568 | 0,588 |
| 1 Delivery (nur ITM) | 0,284 | 0,294 |
| Halbspread ueberqueren | 0,070 | 0,130 |

### 0.2 Der Funding-Anker -- der wichtigste strukturelle Nulleffekt dieses Auftrags

Bybit rechnet `F = P + clamp(I - P, +/-0,05%)`, mit `P` = gewichteter
Premium-Index und `I` = Zins-Term. **NEU (belegt):** `I` ist fuer
Standard-USDT-Perps auf **0,03% pro Tag = 0,01% je 8h** gesetzt; die
Cap-Grenzen sind `min((IMR-MMR)*0,75 ; MMR)`, und bei Anschlag springt die
Frequenz auf stuendlich. Daraus:

> **Der Erwartungswert der Funding-Rate ist mechanisch bei +10,95% p.a.
> verankert, NICHT bei 0.** 0,01% je 8h = **3,0 bp je Tag**.

Das ist fuer diesen Auftrag genau das, was das Dressing-Artefakt (Kompendium
B.9 / DEC-31/33) fuer H-11 war: wer "mittlere Funding-Rate > 0" als Gate
setzt, misst den Zins-Term der Boerse und nicht eine Praemie. **Jeder
Funding-Kandidat unten setzt deshalb als Nulleffekt r_null = I-Anker minus
USD-Finanzierungsbenchmark, nie 0.**

### 0.3 Break-even-Haltedauer -- wie die Friktionswand hier ueberwunden wird

Die Wand ist eine Groesse **je Round-Trip**; eine Praemie akkumuliert **je
Tag**. Am Anker (3,0 bp/Tag):

| Struktur | Fills | RT-Kosten | Break-even |
|---|---|---|---|
| Spot/Perp, beide Taker | 2 Spot + 2 Perp | 10+10+5,5+5,5 = **31 bp** | **10,3 Tage** |
| Spot/Perp, Perp-Maker | wie oben | 10+10+2+2 = **24 bp** | **8,0 Tage** |
| Perp/Perp (2 Kontrakte), Taker | 4 Perp | **22 bp** | auf die Funding-*Differenz* bezogen: bei 3% p.a. Spread **27 Tage** |
| Perp/Perp, Maker | 4 Perp | **8 bp** | bei 3% p.a. Spread **9,7 Tage** |
| Perp/dat. Future, bis Delivery | 2 Entry + 1 Exit (Future settlet gebuehrenfrei am Index) | Taker **16,5 bp** / Maker **6 bp** | bei 3% p.a. Wedge: 20 / 7,3 Tage |

**Befund, der den ganzen Auftrag traegt:** die 11/15-bps-Wand ist bei
Haltedauern ab ~2 Wochen keine Wand mehr, sondern ein Abschlag von 2-4
Prozentpunkten p.a. Das ist der erste Punkt im ganzen Programm, an dem die
Kernrelation aus FINAL_PRD Par.1 nicht sofort toetet.

**Zweiter Befund, ebenso hart:** die **Spot-Seite** kostet 10 bp je Bein und
ist **nicht** durch passive Ausfuehrung verbilligbar (Maker == Taker). Das
Spot-Bein allein ist 20 bp von den 31. Analog zu WP-4 ("Spread-Capture ist
tot") ergibt sich hier eine neue Programm-Konstante-Kandidatin:
**derivatefreie Beine sind auf Bybit teuer; jede Praemien-Struktur, die
ohne Spot auskommt, spart 65% ihrer Friktion.** Das ordnet die Rangliste.

### 0.4 Delta-Hedge-Kosten in Vol-Punkten (abgeleitete Formel)

Fuer jede Options-Praemie ist die Rehedging-Kasse auf dem Perp der zweite,
bisher im Programm nirgends gerechnete Kostenblock:

```
c_hedge [Vol-Punkte] = N_tage * Gamma*S * sigma_tag * E|z| * fee_perp_bp / (vega/S)
```
mit `E|z| = 0,798`, `sigma_tag = sigma_ann/sqrt(365)`.
Numerisch (BTC, sigma_ann 50%, sigma_tag 2,62%, taegliches Rehedge):

| Struktur | Netto-Gamma*S | 14 Tage, Perp-Taker | 14 Tage, Perp-Maker |
|---|---|---|---|
| Einzelnes 25-Delta-Bein | 3,25 | 0,99 Vol-Punkte | 0,36 |
| Risk Reversal 25d (Gammas heben sich weitgehend auf) | ~0 (Rest) | ~0,2 + statischer Hedge 1,04 | ~0,2 + 0,38 |
| ATM-Straddle | 8,15 | **2,49** | 0,90 |
| Kalender 7/30 DTE, 1:1 | 2,98 | 0,45 | 0,16 |

> **Konsequenz (a priori, GL-012-Klasse):** Jede Options-Praemien-Ernte, die
> mit **Taker**-Rehedging auf dem Perp gerechnet wird, verliert 1-2,5
> Vol-Punkte allein an die Hedge-Kasse -- bei einer C-33-Schwelle von 3
> Vol-Punkten sind das 33-83% der Kante. **Maker-Rehedging auf dem Perp ist
> keine Optimierung, sondern Existenzbedingung**, und WP-4 (Top-of-Book =
> ein Tick) sagt, dass ein Maker-Fill dort erreichbar, aber
> adverse-selection-behaftet ist. Das ist eine eigenstaendige, vorab
> messbare Vorfrage (siehe K-07).

### 0.5 Datenzugang -- was oeffentlich ohne Keys erreichbar ist

Direkte API-Probes waren **nicht moeglich** (`api.bybit.com`,
`bybit-exchange.github.io`, `bybit.com`, `arxiv.org`, `bis.org` sind vom
Egress-Proxy blockiert). Die Endpunkt-Spezifikationen wurden aus dem
**Quell-Repo der Bybit-Doku** (`raw.githubusercontent.com/bybit-exchange/docs`)
gelesen -- das ist Primaerquelle fuer die Schnittstelle, aber nicht fuer die
tatsaechlich ausgelieferte Historientiefe.

| Endpunkt | Spezifikation (belegt) | Historientiefe |
|---|---|---|
| `/v5/market/funding/history` | `category`, `symbol`, `startTime`+`endTime` (nur startTime allein = Fehler), `limit` 1-200, Default 200. Deckt USDT-, USDC- und Inverse-Perps. | **UNBELEGT.** Kein dokumentiertes Limit. 200 Saetze = 66 Tage je Request; 6 Jahre BTCUSDT = ~33 Requests. IP-Limit 600 Requests/5 s -> der ganze 5-Symbol-Backfill kostet Sekunden. **In 5 Minuten pruefbar, muss vor Registrierung geprueft werden.** |
| `/v5/market/premium-index-price-kline` | `category=linear`, `interval` bis `D`, `start`/`end`, `limit` 1-**1000**. | **Das loest DSM-03s Blocker.** Kompendium D.17 sagt "Premium-Index nur 43 Tage und nur als Delta-Strom" -- das galt fuer den WS-`tickers`-Strom im Harvest-Baum, NICHT fuer diesen oeffentlichen REST-Kline-Endpunkt. Tiefe unbelegt, aber die Existenz eines Kline-Endpunkts impliziert Historie. |
| `/v5/market/index-price-kline`, `/v5/market/mark-price-kline` | dito, `limit` 1-1000 | Referenz-/Markpreis fuer die Basis-Rekonstruktion |
| `/v5/market/kline?category=spot` | Spot-Klines | Spot-Bein ohne Harvest-Abhaengigkeit |
| `/v5/market/delivery-price` | `category=linear\|inverse\|option`, `limit` 1-200, Cursor-Paginierung | Historische Settlement-Preise datierter Kontrakte |
| `/v5/market/instruments-info` | `contractType` Enum: `LinearPerpetual`, **`LinearFutures` (= USDC-Futures)**, `InversePerpetual`, **`InverseFutures`** | **Antwort auf Teilfrage (b): JA.** Symbol-Enum belegt `BTC-24MAR23` (USDC-Future) und `BTCUSDH23/M23/U23/Z23` (Inverse-Quartale); Bybit fuehrt zudem live die Seiten `BTCUSD_Q` (Quartal) und `BTCUSD_BIQ` (Bi-Quartal). **Liquiditaet: UNBELEGT** -- muss aus `turnover24h`/Klines gemessen werden. |

**Der Harvest-Bestand allein reicht fuer KEINEN der Funding-Kandidaten:**
`bybit/rest.fundingRate` hat 113 Tage (ab 2026-03-19). Das schliesst die
groesste bekannte Stress-Episode (10.10.2025) **aus** und verletzt damit die
Stress-Pflicht aus PRD Par.8.4. Der REST-Backfill ist nicht "nice to have",
sondern Vorbedingung.

---

## 1. Kandidaten

### K-01 Funding-Carry-Zensus auf Bybit (Spot/Perp, delta-neutral)
- **Ertragsquelle:** **Praemie.** Perps haben keinen Verfall; der Funding-Mechanismus ist der einzige Anker an den Spot. Wer gehebelte Long-Exposure will, muss die Position dauerhaft mieten -- er zahlt Funding an den, der die Gegenseite mit echtem Bilanzeinsatz (voll bezahltes Spot) haelt. Der Preis dieser Miete ist einseitig teuer zu arbitrieren: die Long-Spot/Short-Perp-Seite braucht nur Kapital, die Gegenseite braucht einen **Coin-Borrow** (variabel, stuendlich, unmessbar ohne Keys) -- deshalb kann die Praemie strukturell positiv bleiben, ohne dass ein Arbitrageur sie wegdrueckt. Zahler: gehebelte Retail-Longs. Empfaenger: Bilanz.
- **Horizont & Instrument:** 2 Wochen bis 6 Monate; Bybit Spot BTC/ETH + BTCUSDT/ETHUSDT-Perp, Unified Trading Account (Portfolio-Margin mit aktiviertem Spot-Hedging nettet das Delta, belegt).
- **Literatur/Evidenz:**
  - Schmeling / Schrimpf / Todorov, "Crypto Carry", BIS WP 1087 (2022), Working Paper 2025: Carry (Futures-vs-Spot) erreicht zeitweise >40% p.a.; Mechanismus explizit = trendfolgende Kleinanleger-Nachfrage nach Hebel **plus** begrenztes Arbitragekapital wegen Regulierungs-/Margin-Friktionen. *(Primaerquelle bis.org egress-blockiert; Zahlen ueber CEPR-/Survey-Sekundaerzitate.)*
  - Survey "Cryptocurrency as an Investable Asset Class" (2026, arXiv 2510.14435): annualisierter Sharpe der Krypto-Carry **6,45 ueber 2020-2025; 4,06 in 2024; NEGATIV in 2025**. Mittlere Rendite ~8% p.a. bei ~0,8% Vol. *(Sekundaerzitat, Volltext egress-blockiert.)* **Das ist die Crowding-Zahl, die dieser Kandidat beweisen oder widerlegen muss.**
  - Front-Month-Basis: Spitze ~25% p.a. (Feb 2024) -> **4,46% (Dez 2025), 93% der Handelstage unter der 5%-Break-even-Schwelle**. *(Sekundaerquelle, mittleres Vertrauen.)*
  - Bybit-Anker `I` = 0,01%/8h = 10,95% p.a. (belegt, s. Par.0.2).
  - Tail-Beleg: 10.10.2025, ~19 Mrd USD Liquidationen in ~24 h, halber Schaden in 40 Minuten; Top-of-Book-Tiefe auf Leitboersen **-90%**, Spreads von einstelligen bp auf zweistellige **Prozent**; USDe/BNSOL/WBETH-Depegs; ADL-Spiralen; dYdX 8 h offline. *(Mehrere unabhaengige Sekundaerquellen, hohes Vertrauen fuer das Ereignis, niedriges fuer Einzelzahlen.)*
- **Erwartete Groessenordnung vs. Friktion:** Brutto am Anker 10,95% p.a. = 3,0 bp/Tag. Friktion 31 bp (Taker) bzw. 24 bp (Perp-Maker) je Round-Trip. Bei 30-Tage-Halten: Drag 3,8% p.a. -> **netto ~5-7% p.a.**; bei 90-Tage-Halten: Drag 1,26% p.a. -> **netto ~8-10% p.a.** Break-even 8-10 Tage (Par.0.3). Die relevante Frage ist NICHT ob netto>0, sondern ob netto > Nulleffekt (s. Gate).
- **Daten:** Aus dem Bestand: nichts Ausreichendes (113 Tage `rest.fundingRate`, ohne Stress-Fenster). Nachzuladen, alles keyfrei: (i) `/v5/market/funding/history` fuer 5 Symbole x 3 Kontraktklassen, ~33 Requests je Symbol/Klasse, **<1 MB, Minuten**; (ii) `/v5/market/kline?category=spot` Tagesbars, ~10 Requests/Symbol; (iii) `/v5/market/premium-index-price-kline` fuer die Zerlegung F = P + clamp(...). Ergebnis: ein neuer, deterministischer, fingerabdruck-gepinnter Store `data/premstore/funding_8h/` nach dem WP-0-Muster (SCHEMA_VERSION + SHA-256, Manifest-Gate entfaellt, weil REST-Antworten selbstdatierend sind).
- **Rechenaufwand:** CPU, **Sekunden**. Der gesamte Kandidat ist ~6.600 Zeilen je Symbol-Jahr. Kein GPU-Lauf, kein Overnight, kein Checkpoint noetig. Das ist der billigste registrierbare Kandidat, den das Programm je hatte.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Metrik:** `r_excess` = annualisierte Netto-Carry nach dem vorab gepinnten Kostenmodell (31 bp Taker-Primaerfall, Anti-Gaming: NICHT absenkbar) **minus** `r_null`.
  - **Struktureller Nulleffekt (DEC-31/33-Pflicht):** `r_null = I_Anker - r_USD`, mit `I_Anker` = 10,95% p.a. aus Par.0.2 und `r_USD` = der stablecoin-seitige Opportunitaetszins im selben Fenster (z. B. Bybit-Savings-/Earn-Basisrate; **falls nicht keyfrei belegbar: konservativ r_USD = 0, was den Nulleffekt MAXIMIERT und das Gate verschaerft**). Ohne diese Zeile misst das Gate den Boersen-Zinsterm.
  - **Fenster (REZENZ-Klausel):** zwei disjunkte 12-Monats-Fenster, das juengste endet am Laufdatum. **Stress-Pflicht:** jedes Fenster muss >=1 dokumentierte Stress-Episode enthalten (Fenster 1 zwingend 10.10.2025). Fehlt sie: **KEIN VERDIKT**, nicht WEITER (PRD Par.8.4-Analogie).
  - **Schwellen (Herleitung, nicht importiert):** (i) `r_excess >= 4,0% p.a.` in BEIDEN Fenstern -- hergeleitet als 2x die Kostendrift bei 30-Tage-Halten (3,8%), damit die Kante die Friktion um Faktor 2 schlaegt, nicht knapp; (ii) `SR_block >= 0,60`, hergeleitet aus dem Rauschboden `SE(SR) = sqrt((1+SR^2/2)/N_eff)`: bei 12 Monaten taeglicher PnL und einer aus dem integrierten Autokorrelations-Zeitmass geschaetzten Blocklaenge L ~ 30 Tage ist `N_eff ~ 12`, also `SE(SR) ~ 0,31` -> 0,60 ist ~2 Sigma; (iii) **Tail-Ratio** `TR = |CVaR_1%(tgl. PnL)| / mean(tgl. PnL) <= 250 Tage` (ein 1%-Tail-Tag darf weniger kosten als eine Jahresernte); (iv) **Crowding-Klausel**: `r_excess(juengstes Fenster) >= 0,5 * r_excess(aelteres Fenster)` -- sonst PARK statt WEITER, weil die Literatur (Sharpe 6,45 -> 4,06 -> negativ) genau diesen Zerfall behauptet.
  - **FDR-Familie:** `F-PREM1` (Funding-/Basis-Kohorte: K-01, K-02, K-03) BH bei alpha=0,10; zusaetzlich zweistufige Ueber-Familien-FDR `F-PREM-ALL` ueber die gepoolten Survivor von F-PREM1 und F-PREM2 (DEC-22).
  - **Fixtures (DEC-39-Pflicht):** *positiv* = synthetische 8h-Funding-Serie mit konstantem +12% p.a. plus AR(1)-Rauschen und einem eingebauten -20-Sigma-Tag; das Gate MUSS bestehen und die Tail-Ratio muss den Tag sehen. *negativ* = Serie, deren Mittelwert **exakt** der I-Anker ist und deren Abweichungen reines weisses Rauschen sind; das Gate MUSS scheitern (`r_excess ~ 0`). Genau dieses zweite Fixture ist der Dressing-Artefakt-Waechter dieses Kandidaten.
- **Was ihn a priori toetet:**
  1. `/v5/market/funding/history` liefert weniger als 24 Monate -> Stress-Pflicht unerfuellbar -> **kein Lauf**, bis eine andere keyfreie Quelle die Historie liefert. **Dies ist vor jeder Registrierung zu pruefen (GL-012-Check).**
  2. `r_excess` ist ex ante rechnerisch nicht erreichbar, wenn `r_USD >= 7% p.a.` -- dann frisst der Nulleffekt die Schwelle. Zahl vorab einsetzen, nicht nach dem Sehen.
  3. Wenn die Spot-Gebuehr in Wahrheit >10 bp ist (VIP0 unverifiziert), steigt die Break-even-Haltedauer ueber 12 Tage; ab ~20 bp/Bein waere die 4%-Schwelle bei 30-Tage-Halten unerreichbar.
- **Bezug zu Kompendium D/E:** Wiederholt **nicht** D.17/DSM-03 (Funding-**Prognose**) und **nicht** H-01/CS-03 (Pre-Settlement-Funding-**Richtung**, DROP bei -15,47 bps) -- beide sind Prognose-Ansaetze; K-01 prognostiziert nichts, sondern misst eine gehaltene Position. Nutzt E-Faden 10 nicht (keine Tradability-Implikation), fuehrt aber die Doktrin C.2 sauber fort: dies ist ein reines Mess-Gate, die Tradability-Frage bekommt einen eigenen Eintrag (K-01b, hier NICHT registriert).
- **Vertrauen:** **hoch.** Der Mechanismus ist boersenseitig dokumentiert (Formel + Anker), die Literatur ist einschlaegig und liefert sogar die Erosionsthese als Falsifikator, die Daten sind keyfrei und in Minuten beschaffbar, der Rechenaufwand ist Sekunden. Das einzige echte Risiko ist die Historientiefe des Endpunkts.

---

### K-02 Intra-Venue-Funding-Spread (USDT-Perp vs. USDC-Perp vs. Inverse-Perp, alles auf Bybit)
- **Ertragsquelle:** **Praemie/Struktur.** Bybit fuehrt auf denselben Basiswert drei Perps mit **drei getrennten Premium-Indizes und drei getrennten Funding-Raten**: `BTCUSDT` (USDT-margined), `BTCPERP` (USDC-margined), `BTCUSD` (inverse, coin-margined). Die Raten weichen ab, weil die Nutzerbasen und die Sicherheiten-Waehrungen verschieden sind. Wer die Differenz einsammelt, wird fuer das **Sicherheiten-Waehrungs- und Quanto-Risiko** bezahlt, nicht fuer eine Richtungsmeinung. Zahler: Trader, die aus Bilanz-/Steuer-/Waehrungsgruenden an eine bestimmte Kontraktklasse gebunden sind.
- **Horizont & Instrument:** 1-8 Wochen; zwei Perp-Beine, beide in **einem** UTA (Portfolio-Margin nettet das Delta ueber Produktklassen hinweg -- belegt: PM umfasst Spot, Margin, USDT-Perp, USDC-Perp, USDC-Futures, USDC-Optionen). **Kein Cross-Venue-Transfer, kein zweites Gegenparteirisiko** -- das ist der entscheidende Vorteil gegenueber der ueblichen Cross-Exchange-Variante.
- **Literatur/Evidenz:** Die Existenz persistenter Funding-Dispersion **zwischen** Boersen ist breit dokumentiert (Scanner-Landschaft ueber 7 Boersen; berichtete Durchschnitts-Spreads 5,98-11,4% p.a. BTC/ETH Hyperliquid-vs-Binance, Spitzen >23% p.a.; strukturelle Basis-Differenz z. B. BNB 0% vs. 10,95% Anker) -- **Sekundaerquellen, kommerzielle Anbieter, niedriges Vertrauen fuer die Zahlen, mittleres fuer das Phaenomen.** Fuer die **Intra-Venue**-Variante (drei Kontraktklassen derselben Boerse) habe ich **keine Literatur gefunden -- unbelegt.** Das ist genau der Grund, sie zu messen: sie ist der billigste Fall und der am wenigsten abgegraste.
- **Erwartete Groessenordnung vs. Friktion:** 4 Perp-Fills; Taker 22 bp, Maker 8 bp. Erwarteter Spread: **unbelegt**, Arbeitsannahme 1-4% p.a. Break-even bei 3% p.a.: 27 Tage (Taker) / 9,7 Tage (Maker). Die Kante ist klein, aber die Friktion ist die kleinste im ganzen Feld (kein Spot-Bein!) und die Kapitalbindung dank Margin-Netting die niedrigste.
- **Daten:** `/v5/market/funding/history` fuer je 3 Symbole x 2 Coins = 6 Serien, plus Mark-Klines fuer den Basis-Drift. **Aus dem Bestand nicht ausreichend** (dieselbe 113-Tage-Grenze). Der Harvest-`tickers`-Strom (3.751 Symbole, 43 Tage) enthaelt die drei Klassen bereits, ist aber Delta-kodiert und zu kurz.
- **Rechenaufwand:** CPU, Sekunden. Identische Pipeline wie K-01.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Metrik:** `s_net` = annualisierter Netto-Funding-Spread (bezahlte Rate der teuren Klasse minus erhaltene Rate der billigen) nach 8-bp-Maker-Kostenmodell bei 30-Tage-Halten, plus ein **Quanto-Residual-Term** fuer das Inverse-Bein.
  - **Struktureller Nulleffekt:** hier **0**, aber nicht trivial: der I-Anker kuerzt sich zwischen zwei Perps **nur dann heraus, wenn beide denselben `I` haben.** Vorab pruefen (Instruments-Info) und, falls verschieden, `r_null = I_A - I_B` setzen. Zweiter Nulleffekt: das Inverse-Bein ist **nicht delta-linear**; ein 1:1-Notional-Paar USDT-Perp/Inverse-Perp hat ein Konvexitaets-Residual ~ (dS/S)^2. Dessen Erwartungswert unter der gemessenen Tagesvol ist vorab auszurechnen und von `s_net` abzuziehen -- sonst wird Konvexitaets-PnL als Praemie fehlgelesen.
  - **Fenster/Schwellen/FDR:** wie K-01 (2 disjunkte 12-Monats-Fenster mit Stress-Pflicht, REZENZ, F-PREM1). Schwelle: `s_net >= 1,6% p.a.` in beiden Fenstern -- hergeleitet als 2x die 8-bp-Maker-Drift bei 30-Tage-Halten (0,8% p.a. -> 1,6%). Zusaetzlich `SR_block >= 0,60` und Tail-Ratio <= 250 Tage.
  - **Fixtures:** *positiv* = zwei synthetische Funding-Serien mit konstantem 3%-p.a.-Versatz plus gemeinsamem Rauschen; *negativ* = zwei Serien mit identischem Erwartungswert, aber unterschiedlicher Varianz (das Gate darf Varianzunterschiede nicht als Spread lesen).
- **Was ihn a priori toetet:** (i) Wenn alle drei Klassen denselben Premium-Index verwenden (dann waere der Spread strukturell 0) -- **vorab pruefbar an 43 Tagen Harvest-`tickers`, kostet nichts**; (ii) wenn die Median-Absolutdifferenz auf diesen 43 Tagen **unter 0,4% p.a.** liegt, ist die 1,6%-Schwelle strukturell unerreichbar -> DROP ohne Backfill (exakter GL-012-Check nach H-07-Muster); (iii) wenn das Inverse-Bein wegen Coin-Sicherheit die Kapitalbindung verdoppelt, halbiert sich die Rendite auf eingesetztes Kapital.
- **Bezug zu Kompendium D/E:** Beruehrt keinen D-Eintrag. Nutzt E.9/E.6 nicht. Es ist bewusst **nicht** die Cross-Exchange-Variante: die harte Randbedingung "Einzelner Retail-Betreiber auf Bybit" wuerde bei Binance/Deribit-Beinen Transfer-, Verwahr- und Ausfallrisiko einfuehren, das kein Mess-Gate abbildet.
- **Vertrauen:** **mittel.** Mechanismus plausibel und billig pruefbar, aber die Groessenordnung ist unbelegt und koennte den 0,4%-Vorab-Check nicht ueberleben. Genau deshalb steht der Vorab-Check vor der Registrierung.

---

### K-03 Term-Structure-Carry: Perp gegen datierten Bybit-Future
- **Ertragsquelle:** **Praemie/Struktur.** Ein datierter Future preist einen **festen** Terminzins bis zum Verfall; ein Perp preist denselben Zins **fortlaufend neu** ueber Funding. Die Differenz ist eine Terminpraemie: wer den Future kauft und den Perp verkauft (oder umgekehrt), traegt das Risiko, dass das realisierte Funding vom eingepreisten Terminzins abweicht, und wird dafuer bezahlt. Zahler: Marktteilnehmer, die Laufzeitsicherheit kaufen (Hedger, strukturierte Produkte). Es ist **keine Konvergenz-Wette auf den Spot** -- die Konvergenz ist am Verfall mechanisch garantiert.
- **Horizont & Instrument:** bis zum Verfall (1-3 Monate, ggf. 6). Bybit-Instrumente **belegt vorhanden**: `contractType = LinearFutures` (USDC-Futures, Symbolform `BTC-24MAR23`) und `InverseFutures` (Quartale `BTCUSDH/M/U/Z<yy>`, live als `BTCUSD_Q` / `BTCUSD_BIQ`). Beide sind in Portfolio-Margin marginfaehig (USDC-Futures explizit belegt).
- **Literatur/Evidenz:** Schmeling et al. definieren Carry ueber genau diesen Futures-vs-Spot-Abstand und dokumentieren >40% p.a. in Spitzen. Front-Month-Basis Feb-2024 ~25% p.a. -> Dez-2025 **4,46%**, 93% der Tage unter 5% (Sekundaerquelle). Der **Wedge Perp-vs-Future** speziell: **unbelegt** -- ich habe keine Arbeit gefunden, die ihn separat quantifiziert. Ackerer/Hugonnier/Jermann, "Perpetual Futures Pricing" (Mathematical Finance 2026) liefert den theoretischen Rahmen (Perp-Preis als Funktion des Funding-Prozesses), aber keine Bybit-Zahlen. *(Volltext egress-blockiert; nur ueber Suchtreffer belegt.)*
- **Erwartete Groessenordnung vs. Friktion:** **Der billigste Fall des ganzen Auftrags**, weil beide Beine Derivate sind und das Future-Bein am Verfall **gebuehrenfrei gegen den Index settlet** -- nur 3 Fills statt 4. Taker 16,5 bp, Maker 6 bp. Bei einem Wedge von 3% p.a. ueber 90 Tage: brutto 74 bp, netto **57-68 bp = 2,3-2,8% p.a.** Bei 5% Wedge: netto 4,3-4,7% p.a. **Bei 0% Wedge (dem oekonomisch erwarteten Fall in einem effizienten Markt) ist der Kandidat tot** -- das ist die Falsifikation.
- **Daten:** **Der schwierigste Punkt.** Klines fuer bereits **verfallene** Kontraktsymbole sind ueber `/v5/market/kline` vermutlich nicht mehr abfragbar (`instruments-info` filtert auf `status=Trading`) -- **unbelegt, aber wahrscheinlich.** Belegbar rekonstruierbar ist nur: (i) `/v5/market/delivery-price` (historische Settlement-Preise, 200/Seite, Cursor) als Ankerpunkt-Serie; (ii) der Harvest-`tickers`-Strom (43 Tage, 3.751 Symbole) enthaelt die aktuell gelisteten datierten Kontrakte bereits. **Konsequenz: K-03 ist mit hoher Wahrscheinlichkeit ein RECORDING-FIRST-Kandidat** wie H-21/H-26 -- ein Sampler nach dem Muster von `snap_bybit_optchain.ps1` (15-min-Takt), der die Basis-Kurve `mark(Future) / mark(Perp) / index` je Verfall protokolliert, und ein Gate-Lauf in 12+ Monaten. Aufwand: ein 100-Zeilen-PowerShell/Python-Sampler + ein Scheduled Task; Volumen ~10 MB/Monat.
- **Rechenaufwand:** CPU, Sekunden. Der Aufwand liegt vollstaendig in der Kalenderzeit, nicht in der Rechnung.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Metrik:** `w` = realisierter Wedge = (implizierter Terminzins des Futures beim Einstieg) minus (tatsaechlich realisierte, ueber die Laufzeit akkumulierte Funding-Rate des Perps), annualisiert, nach 6-bp-Maker-Kostenmodell.
  - **Struktureller Nulleffekt:** `w_null = 0` **nur in einem arbitragefreien Markt mit reibungsfreiem Kapital**. Real ist `w_null` = die Margin-Bindungsdifferenz zwischen den beiden Beinen mal dem Opportunitaetszins -- vorab auszurechnen aus den `instruments-info`-Margin-Parametern. Zweiter Nulleffekt: der Wedge ist per Konstruktion **ex post** gemessen; ein positiver Mittelwert kann reine Jensen-Kruemmung sein (Terminzins ist ein Erwartungswert unter dem Terminmass). Der Test muss daher gegen die **ex-ante-implizierte** Kurve laufen, nicht gegen den Nachhinein-Mittelwert.
  - **Fenster:** >=8 vollstaendige Verfallzyklen (bei Quartalen = 2 Jahre; bei Monatsverfaellen = 8 Monate) ueber zwei disjunkte Haelften; REZENZ: die juengste Haelfte endet am Laufdatum. Stress-Pflicht: >=1 Zyklus mit dokumentierter Stress-Episode.
  - **Schwellen:** `w >= 2,0% p.a.` in beiden Haelften (= 2x die 6-bp-Maker-Drift bei 90-Tage-Halten von ~0,24% p.a. ... die Herleitung ergibt 0,5%; ich setze **bewusst hoeher auf 2,0%**, weil die Kapitalbindung ueber 90 Tage die eigentliche Kostenstelle ist und ein Ertrag unter 2% p.a. gegen jede Alternativverwendung verliert). `N_zyklen >= 8`. Vorzeichenkonsistenz in >=6 von 8 Zyklen.
  - **FDR-Familie:** F-PREM1 gemeinsam mit K-01/K-02.
  - **Fixtures:** *positiv* = synthetische Terminkurve mit konstantem +3%-p.a.-Aufschlag ueber den simulierten realisierten Funding-Pfad; *negativ* = Terminkurve, die exakt dem Erwartungswert des Funding-Pfads entspricht, mit zufaelliger Realisation (das Gate muss `w ~ 0` finden und darf die Realisationsstreuung nicht als Praemie lesen).
- **Was ihn a priori toetet:** (i) **Liquiditaet**: wenn `turnover24h` des vordersten datierten Kontrakts unter ~1% des Perp-Umsatzes liegt, ist der Quote-Spread der bindende Kostenblock und nicht die Gebuehr -- **das ist die erste zu messende Zahl, vor jeder Registrierung**, und sie ist heute in einem einzigen `/v5/market/tickers`-Call verfuegbar; (ii) wenn Bybit die datierten Kontrakte nur sporadisch listet (keine durchgehende Quartalsleiter), ist `N_zyklen >= 8` unerreichbar; (iii) wenn historische Klines verfallener Symbole nicht abrufbar sind, ist ein rueckblickendes Gate unmoeglich und der Kandidat wird auf 12+ Monate Recording vertagt.
- **Bezug zu Kompendium D/E:** **Dies ist die Entsperr-Bedingung von C-23 (PARK-Register, FINAL_PRD Par.5)**, woertlich: "Standalone-Verdrahtung + Nachweis Konvergenz > Friktion". Der alte Park-Grund war "2-Bein ~22 bps gegen <0,08% Konvergenz" -- das war eine Rechnung auf **kurzem** Horizont. Par.0.3 zeigt: auf 90 Tagen kehrt sich die Arithmetik um (74 bp brutto gegen 6-16,5 bp). Das ist der geforderte "nachweislich neue" Sachverhalt, nicht eine Wiederholung. Beruehrt keinen D-Eintrag.
- **Vertrauen:** **mittel.** Mechanismus und Instrumente belegt, Friktion exzellent, aber Liquiditaet und Historien-Abrufbarkeit sind beide unbelegt und beide potenziell toedlich.

---

### K-04 Skew-Praemie (25-Delta-Risk-Reversal, delta-gehedgt) -- die einzige Options-Praemie mit tragbarer Hedge-Kasse
- **Ertragsquelle:** **Praemie.** Krypto-Halter kaufen systematisch Abwaertsschutz; Krypto-Optimisten kaufen Aufwaerts-Hebel billiger anderswo (Perps). Der Preis dieser Asymmetrie ist der Skew. Wer den 25d-Put verkauft und den 25d-Call kauft, wird fuer das Tragen genau der Crash-Asymmetrie bezahlt, gegen die alle anderen sich versichern. Zahler: Hedger. **Klar abgegrenzt von H-26/C-33:** die VRP ist das **Niveau** (IV vs. RV); die Skew-Praemie ist die **Schiefe** (IV_put vs. IV_call bei gleichem \|Delta\|). Ein Risk Reversal ist bei symmetrischen Deltas naeherungsweise **vega-neutral** -- er handelt genau das, was die VRP-Messung herauskuerzt.
- **Horizont & Instrument:** 7-21 DTE, Halten bis Verfall; Bybit-Optionen BTC/ETH im gemessenen Bein-Band (7-14 DTE, \|Delta\| 0,15-0,30), Delta-Hedge auf dem USDT-Perp.
- **Literatur/Evidenz:**
  - "Delta hedging bitcoin options with a smile" (Quantitative Finance 2023, Deribit Jan-2020..Jun-2022): nach "Black Thursday" 03/2020 bildet BTC eine **negative Skew wie Aktienindizes**; **OTM-Puts sind teuer, weil Investoren eine Praemie fuer Absicherung zahlen; ATM-Optionen sind ebenfalls teuer -> negative Renditen fuer ATM-Put UND -Call.**
  - Deribit-Insights-Backtest ueber vier Vol-Regime: Risikopraemie auf Deribit negativ und signifikant, Vol-Verkauf risikoadjustiert positiv. *(Volltext egress-blockiert; nur ueber Suchtreffer belegt -- mittleres Vertrauen.)*
  - Atanasova et al., "Illiquidity Premium and Crypto Option Returns" (AUT/ScienceDirect 2025): delta-gehedgte Optionsrenditen nach Coval-Shumway; **Illiquiditaet ist ein Haupttreiber der Querschnittsvariation** -- d. h. ein Teil dessen, was wie Skew-Praemie aussieht, ist Liquiditaetspraemie.
  - **Die konkrete Groesse der Skew-*Praemie* (implizite minus realisierte Skew) auf Bybit ist unbelegt.** Das ist die Messfrage.
- **Erwartete Groessenordnung vs. Friktion (voll durchgerechnet mit den Bybit-Konstanten):**

  | Posten | BTC | ETH |
  |---|---|---|
  | 2 Options-Maker-Fills (Einstieg) | 0,758 | 0,784 |
  | Erwartete Delivery-Gebuehr (~50% Chance, ein Bein ITM) | 0,142 | 0,147 |
  | Statischer Perp-Hedge (Delta ~0,5, RT Maker 4 bp -> 2 bp Index) | 0,379 | 0,392 |
  | Rehedge-Rest (Gammas heben sich weitgehend auf) | ~0,20 | ~0,21 |
  | **Summe, Maker durchgehend** | **~1,48 Vol-Punkte** | **~1,53** |
  | Summe, Taker durchgehend | ~2,6 | ~2,7 |

  Gegen die C-33-Schwelle von 3 Vol-Punkten: **Maker frisst 49%, Taker 87%.**
  Das ist deutlich haerter als der bisher zitierte DEC-45-Wert (25/26%) --
  DEC-45 rechnete 2 Options-Fills ohne Delivery-Gebuehr und **ohne
  Delta-Hedge**. Diese Zeile ist ein eigenstaendiger, entscheidungsrelevanter
  Befund fuer den ganzen Options-Pfad und sollte unabhaengig von K-04
  protokolliert werden.
- **Daten:** Aus dem Bestand: `deribit/tickers` (5.964 Symbole, volle Kette inkl. Greeks, ~38 Tage) als **Messbasis** fuer die Skew-Serie; `state/wp5_20260824/` + `data/optchain_snaps/` (15-min-REST-Sampler seit 2026-08-24) als Bybit-Quote-Referenz; WP-0-Bar-Cache fuer die realisierte Schiefe der Renditen. **Zu wenig fuer ein Gate** (38 Tage). Nachzuladen: nichts Keyfreies mit Tiefe -- Bybit liefert keine historischen Options-Quotes. **Realistischer Pfad: der laufende REST-Sampler waechst kalendarisch; ein Gate ist ab ~2027Q1 moeglich.** Das deckt sich mit E.7 (C-33 bleibt an >=12 Monate IV-Recording MIT Stress-Periode gebunden).
- **Rechenaufwand:** CPU, Minuten. Die Skew-Zeitreihe ist ein Tageswert je Symbol.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Metrik:** `skew_prem` = (implizite 25d-Skew beim Einstieg) minus (realisierte Skew, gemessen als die aus der tatsaechlichen Renditeverteilung des Verfallfensters implizierte 25d-Schiefe), in Vol-Punkten, **minus 1,48 Vol-Punkte Kostenmodell (vorab gepinnt, nicht absenkbar)**.
  - **Struktureller Nulleffekt:** **nicht 0.** Zwei Terme vorab auszurechnen: (i) die **Jensen-/Konvexitaets-Verzerrung**, weil ein Risk Reversal aus zwei Optionen mit unterschiedlichem Vega-Profil besteht -- der Erwartungswert unter der physischen Verteilung ist auch bei fairer Preisung ungleich 0; (ii) das **Illiquiditaets-Bein** (Atanasova et al.) -- die 25d-Fluegel sind duenner als ATM, ein Teil der Praemie ist Entschaedigung dafuer und nicht Skew. Konservativ: `skew_null` = die auf synthetischen, aus der historischen Renditeverteilung gebootstrappten Pfaden erzeugte mittlere RR-Rendite bei **fairer** Preisung. Ohne diese Zeile ist das Gate der H-11-Fehler in neuem Gewand.
  - **Fenster:** >=12 zusammenhaengende Monate Bybit-Quote-Historie MIT Stress-Periode (PRD Par.8.4 woertlich), aufgeteilt in 2 disjunkte Haelften; REZENZ: juengste Haelfte endet am Laufdatum.
  - **Schwellen:** `skew_prem >= 1,5 Vol-Punkte` netto in beiden Haelften -- hergeleitet als 1x das Kostenmodell (1,48), damit die Kante die Friktion mindestens verdoppelt statt sie knapp zu schlagen; plus `SR_block >= 0,60`; plus Tail-Ratio <= 250 Tage (ein Risk Reversal ist **short Crash** -- die Tail-Ratio ist hier das eigentliche Gate, nicht der Mittelwert).
  - **FDR-Familie:** `F-PREM2` (Options-Praemien: K-04, K-05, K-06), plus F-PREM-ALL.
  - **Fixtures:** *positiv* = synthetische Kette mit eingebautem 3-Vol-Punkte-Skew-Aufschlag ueber einer symmetrischen Renditeverteilung plus einem -25%-Tag; *negativ* = Kette, deren Skew **exakt** die realisierte Schiefe der erzeugenden Verteilung wiedergibt (faire Preisung) -- das Gate MUSS scheitern, und die Tail-Ratio MUSS im positiven Fixture ausschlagen.
- **Was ihn a priori toetet:** (i) wenn die gemessene mediane 25d-Skew auf Bybit **unter 1,5 Vol-Punkten** liegt, ist die Schwelle strukturell unerreichbar -- **auf den vorhandenen 38 Tagen `deribit/tickers` heute pruefbar, kostet Minuten** (GL-012-Check); (ii) wenn Maker-Fills auf beiden Options-Beinen nicht erreichbar sind (Fill-Rate im gehandelten Band unbekannt), springt das Kostenmodell auf 2,6 Vol-Punkte und die Schwelle stirbt; (iii) wenn WP-6s Stress-Verbreiterung (BTC Spitze 9,53, ETH 53,8 Vol-Punkte) einen Not-Ausstieg erzwingt, ist eine einzige Episode teurer als ein Jahresertrag -- deshalb ist **"Halten bis Verfall, kein Stop-Loss"** konstitutiver Teil der Hypothese und nicht ein spaeter Parameter.
- **Bezug zu Kompendium D/E:** Dupliziert **nicht** H-26 (VRP = Vol-Niveau; K-04 ist vega-neutral und handelt die Schiefe). Wiederholt **nicht** D.15 (reaktives Long-Vol) -- K-04 ist ein geplanter, kalendergetriebener Einstieg, kein Reaktionskauf in die Schockminute. Nutzt E.6(a) direkt: die dort als blockierend benannte Delivery-Gebuehr ist jetzt beziffert (1,5 bp Index / 0,284 Vol-Punkte, nur ITM) -- **die Reihenfolge aus E.6 bleibt aber verbindlich: (a) verifiziert, (b) durchgaengiger Bybit-Quote-Zensus fehlt weiter, (c) H-26 ungemessen. K-04 ist damit fruehestens nach H-26 registrierbar.**
- **Vertrauen:** **mittel.** Mechanismus stark belegt, Kostenrechnung jetzt vollstaendig, aber die Datenlage (38 Tage) ist heute weit von einem Gate entfernt und die Reihenfolge-Bindung aus E.6 ist bindend.

---

### K-05 Kalender-/Forward-Vol-Praemie (Term-Structure der IV)
- **Ertragsquelle:** **Praemie.** Die IV-Terminkurve ist im Mittel aufwaerts geneigt, weil Vol-Verkaeufer fuer laengere Bindung mehr verlangen und Hedger Ereignisrisiko in bestimmte Verfaelle konzentrieren. Wer den kurzen Verfall kauft und den langen verkauft (oder umgekehrt), vereinnahmt die Differenz zwischen implizierter Forward-Vol und der spaeter realisierten.
- **Horizont & Instrument:** 7 DTE gegen 30 DTE, gleicher Strike (ATM); Bybit-Optionen BTC/ETH.
- **Literatur/Evidenz:** Forward-Vol-Konzept und Kalender-Handel sind Standard und in Krypto-Marktkommentaren beschrieben; **die Groesse einer Krypto-spezifischen Term-Praemie ist unbelegt.** Belegt ist nur die Existenz von VRP im Niveau (BVRP 0,14 gegen ~0,02 fuer den S&P, Deribit 2017-2022, Sekundaerzitat) -- daraus folgt nichts ueber die Steigung.
- **Erwartete Groessenordnung vs. Friktion -- und warum das hier wahrscheinlich a priori toetet:** Ein Kalender ist **delta- und weitgehend richtungsneutral**, seine Hedge-Kasse ist die niedrigste im Feld (0,16-0,45 Vol-Punkte, Par.0.4). Aber: sein **Netto-Vega ist die Differenz zweier Vegas.** Bei 7 vs. 30 DTE ist das Vega-Verhaeltnis sqrt(7/30) = 0,483, das Netto-Vega also nur **51,7%** eines Einzelbeins -- waehrend die Gebuehr auf **beiden** Beinen voll anfaellt. Kosten je Einheit **Netto**-Vega:

  | Posten (BTC, Maker) | roh | je Netto-Vega |
  |---|---|---|
  | 3 Options-Fills (2 Entry + 1 Exit des langen Beins) | 1,137 | **2,20** |
  | Rehedge 7 Tage | 0,16 | 0,31 |
  | **Summe** | 1,30 | **~2,51 Vol-Punkte** |

  Gegen die 3-Vol-Punkte-Schwelle: **84% der Kante weg, im BESTEN (Maker-)Fall.** Bei Taker: >125% -- negativ.
- **Daten:** wie K-04 (`deribit/tickers` als Messbasis, Bybit-Sampler waechst).
- **Rechenaufwand:** CPU, Minuten.
- **Kapitalfreies Mess-Gate (Entwurf):** **Der Feasibility-Check kommt VOR dem Gate.** Vorab auszurechnen (nicht zu messen): die minimale Forward-Vol-Praemie, die die 2,51 Vol-Punkte schlaegt, ist **>=5,0 Vol-Punkte** (2x-Regel). Falls die auf den vorhandenen 38 Tagen `deribit/tickers` gemessene mediane Differenz (IV_30 - IV_7) diesen Wert nicht ueberschreitet, ist die Schwelle **mathematisch unerreichbar** und der Kandidat ist ein **struktureller A-priori-DROP nach GL-012/H-07-Muster ohne Datenlauf.** Nur falls er ueberlebt: Metrik = realisierte Forward-Vol minus implizierte, netto; Nulleffekt = die aus der Vol-Mean-Reversion folgende systematische Kurvenneigung bei **fairer** Preisung (analytisch aus einem kalibrierten OU-Prozess auf log-IV); Fenster/FDR wie K-04 (F-PREM2).
- **Was ihn a priori toetet:** die Vega-Verduennung oben. Ich rechne mit hoher Wahrscheinlichkeit damit, dass dieser Kandidat den Feasibility-Check nicht besteht. **Ich fuehre ihn trotzdem auf, weil der Vorab-Kill selbst ein Ergebnis ist** (GL-012-Muster: ein Kandidat, der ohne Datenlauf stirbt, ist der billigste moegliche Erkenntnisgewinn) -- und weil er die allgemeine Lehre liefert: **auf Bybit ist jede Options-Struktur, deren Nutzen eine Differenz zweier Greeks ist, durch Gebuehren-Verduennung strukturell benachteiligt.**
- **Bezug zu Kompendium D/E:** Beruehrt keinen D-Eintrag; dupliziert H-26 nicht (Steigung statt Niveau). Konkretisiert das PARK-Register-Muster "Erreichbarkeit der Schwelle zuerst" (C-30, FINAL_PRD Par.5).
- **Vertrauen:** **niedrig** fuer den Ertrag, **hoch** fuer den Wert des Vorab-Kills.

---

### K-06 Relative-Vol-Praemie ETH gegen BTC (das, was in Krypto von "Dispersion" uebrig bleibt)
- **Ertragsquelle:** **Praemie (schwach).** Klassische Dispersion verkauft Index-Vol und kauft Komponenten-Vol; die Praemie ist die ueberpreiste implizite Korrelation. **In Krypto existiert dieses Konstrukt nicht:** es gibt auf Bybit keine Index-Option und keine Komponenten -- nur zwei Underlyings. Was bleibt, ist eine **relative Vol-Praemie**: ETH-IV notiert dauerhaft ueber BTC-IV; die Frage ist, ob der Aufschlag die realisierte Vol-Differenz uebersteigt.
- **Horizont & Instrument:** 14-30 DTE, ATM-Straddle ETH short gegen ATM-Straddle BTC long, vega-gematcht, beide delta-gehedgt.
- **Literatur/Evidenz:** Belegt ist nur die **Existenz** und Variabilitaet des Spreads: ETH-7d-IV lag am 2026-05-15 nur 4,08 Vol-Punkte ueber BTC-7d (engster Stand seit 03/2025); der 30d-IV-Index-Spread fiel auf 16, nach einem Hoch >30 im Vorjahres-August. **Ob dieser Spread eine PRAEMIE enthaelt, ist unbelegt.** Der klassische Dispersions-Mechanismus (implizite Korrelation) ist hier **nicht anwendbar** -- das sage ich ausdruecklich, statt die Analogie zu strecken.
- **Erwartete Groessenordnung vs. Friktion:** Zwei Straddles = **4 Options-Fills** plus **zwei Gamma-Hedges auf maximalem Gamma** (Straddle-Gamma = 2x Einzeloption). Nach Par.0.4: Hedge je Seite 0,90 Vol-Punkte (Maker) bzw. 2,49 (Taker).

  | Posten (Maker durchgehend) | Vol-Punkte |
  |---|---|
  | 4 Options-Fills (2 BTC + 2 ETH) | 1,542 |
  | Delivery (ATM -> ~50% ITM je Bein, 2 Beine erwartet) | ~0,58 |
  | Gamma-Hedge beide Seiten, 14 Tage | ~1,80 |
  | **Summe** | **~3,9 Vol-Punkte** |

  Bei Taker: **~9 Vol-Punkte.** Gegen einen Spread, dessen *Praemien*-Anteil
  unbekannt und mit Sicherheit kleiner als die 4-30 Vol-Punkte Rohspread ist.
  **Das ist der teuerste Kandidat im Feld und der mit dem schwaechsten
  Mechanismus.**
- **Daten:** wie K-04/K-05.
- **Rechenaufwand:** CPU, Minuten.
- **Kapitalfreies Mess-Gate (Entwurf):** Feasibility zuerst: erforderliche Praemie >=7,8 Vol-Punkte (2x Kostenmodell). Metrik: (IV_ETH - IV_BTC) beim Einstieg minus (RV_ETH - RV_BTC) ueber das Verfallfenster, netto. Struktureller Nulleffekt: **erheblich** -- ETH hat systematisch hoehere realisierte Vol als BTC; der Erwartungswert des Spreads bei fairer Preisung ist die mittlere realisierte Vol-Differenz, die vorab aus dem WP-0-Bar-Cache (10.054 Cache-Tage, 5 Symbole) exakt berechenbar ist. Fenster/FDR wie K-04 (F-PREM2).
- **Was ihn a priori toetet:** die 7,8-Vol-Punkte-Schwelle gegen einen Spread, dessen Praemienanteil vermutlich <2 Vol-Punkte ist. Ausserdem: ETH-Optionen haben die **doppelte** Quote-Breite (0,26 vs. 0,14) und die schlechtere Stress-Stabilitaet (WP-6: ETH 2,82% der Minuten breit, laengste Episode 75 min, Spitze 53,8 Vol-Punkte gegen BTC 0,66%/8 min/9,53).
- **Bezug zu Kompendium D/E:** Kein D-Eintrag beruehrt. Nutzt WP-0 und WP-6 direkt fuer den Nulleffekt bzw. den Kill.
- **Vertrauen:** **niedrig.** Ich fuehre ihn nur auf, weil der Auftrag Dispersion explizit nennt und die ehrliche Antwort lautet: **in dieser Marktstruktur existiert sie nicht, und ihr naechster Verwandter ist rechnerisch tot.**

---

### K-07 Praemien-Kohaerenz im Stress + Perp-Maker-Fill-Zensus (die Vorfrage zu (d), und die zu allen Options-Kandidaten)
- **Ertragsquelle:** **Keine -- reine Struktur-/Messhypothese.** Dieser Kandidat verdient kein Geld; er entscheidet, ob die anderen sechs ueberhaupt zu einem Portfolio kombinierbar sind, und ob ihre Kostenmodelle halten. Zwei Teilfragen, gemeinsam messbar, weil sie dieselbe Datenbasis brauchen.
  - **(A) Kohaerenz:** Die Diversifikations-These ("mehrere kleine Praemien statt einer grossen") setzt voraus, dass die Praemien-PnLs im Stress **nicht** perfekt korrelieren. Die 10.10.2025-Evidenz legt das Gegenteil nahe: Funding kippt tief negativ, Basis kollabiert, IV explodiert, Buchtiefe -90%, ADL greift -- **alle Praemienquellen sind Verkaeufer derselben Liquiditaets-/Crash-Versicherung.** Wenn das stimmt, ist ein "Portfolio aus Praemien" ein einziger gehebelter Trade mit vier Etiketten. **Diese These muss gemessen und nicht angenommen werden.**
  - **(B) Perp-Maker-Fill-Rate:** Par.0.4 zeigt, dass Maker-Rehedging auf dem Perp fuer K-04/K-05/K-06 **Existenzbedingung** ist. WP-4 hat gemessen, dass der Top-of-Book exakt ein Tick breit ist -- aber **nicht**, mit welcher Wahrscheinlichkeit eine Order dort in <60 s gefuellt wird und welchen Adverse-Selection-Abschlag der Fill traegt. Ohne diese Zahl ist jedes Maker-Kostenmodell im Options-Pfad eine Annahme.
- **Horizont & Instrument:** taegliche und minuetliche Aggregate; alle fuenf Harvest-Symbole plus die Optionsketten.
- **Literatur/Evidenz:** 10.10.2025 (s. K-01, mehrere unabhaengige Sekundaerquellen); Glassnode/ScienceDirect (Juni 2026) zu Dealer-Gamma auf Deribit: Renditeumkehr um BTC-Verfaelle konzentriert sich auf Tage mit hohem ATM-Open-Interest und ist **am staerksten bei negativem Netto-Gamma** -- d. h. Short-Gamma-Regime verstaerken Bewegungen, was genau die Korrelation der Praemien-Verluste im Stress erzeugt. *(Sekundaerzitate.)*
- **Erwartete Groessenordnung vs. Friktion:** entfaellt -- kapitalfrei, kein Ertrag.
- **Daten:** **Vollstaendig aus dem Bestand.** (A): WP-0-Bar-Cache (10.054 Cache-Tage) + `bybit/publicTrade` (lueckenlos ab 2020-03-25) fuer Renditen/RV; `deribit/dvol` (112 Tage) und `deribit/tickers` fuer IV; der REST-Funding-Backfill aus K-01 fuer die Funding-Serie. (B): `bybit/orderbook` L2 BTC/ETH (961/530 Tage) plus die bestehende, hash-gepinnte WP-2/WP-4-Replay-Maschinerie (`c22_l2tilt/extract.py`) -- die Sequenz-Replay-Regeln, das `discarded`-Sidecar und der Fingerabdruck-Mechanismus sind bereits gebaut und getestet. **Kein Nachladen, keine neue Infrastruktur.**
- **Rechenaufwand:** CPU. (A) Minuten. (B) ein Ein-Pass-Replay pro Fenster -- WP-4 brauchte dafuer 86 min bei rc=0; PC-tauglich, kein GPU, kein Overnight.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **(A) Metrik:** `rho_stress` = Spearman-Korrelation der taeglichen Praemien-Proxy-PnLs (Funding-Carry, Perp/Future-Wedge, Short-Skew, Short-Vol) **konditioniert auf das schlechteste 1%-Perzentil der gemeinsamen Marktbewegung**, gegen `rho_ruhig` auf dem Rest. **Schwelle:** Diversifikation gilt als widerlegt, wenn `rho_stress >= 0,70` UND `rho_stress - rho_ruhig >= 0,25` in beiden Fenstern. **Struktureller Nulleffekt:** Korrelationen steigen in Extremstichproben **mechanisch** (Selektion auf gemeinsame Groesse); der Nulleffekt ist per Block-Bootstrap aus unkorrelierten Surrogaten mit identischer Randverteilung zu erzeugen, **nicht** mit 0 anzusetzen. Das ist exakt die Dirac-vs-Verteilung-Lehre (C.4) auf Korrelationen uebertragen.
  - **(B) Metrik:** `p_fill(60s)` = Anteil der simulierten Top-of-Book-Maker-Orders, die binnen 60 s gefuellt werden, und `adv_sel` = mittlere Mid-Bewegung in den 10 s **nach** dem Fill, in bp. **Schwelle (Herleitung):** das Maker-Kostenmodell der Options-Kandidaten haelt nur, wenn `p_fill(60s) >= 0,70` UND `adv_sel <= 1,5 bp` (bei groesserem Abschlag uebersteigt der effektive Maker-Preis den Taker-Preis von 5,5 bp und Par.0.4 kippt auf die Taker-Zeile).
  - **Fenster:** zwei disjunkte Halbjahre, REZENZ-konform; (A) zusaetzlich zwingend mit der 10.10.2025-Episode in einem der Fenster.
  - **FDR-Familie:** eigenstaendig (`F-PREM0`), weil dieser Kandidat kein Ertrags-Claim ist und nicht mit K-01..K-06 gepoolt gehoert.
  - **Fixtures:** (A) *positiv* = vier synthetische PnL-Serien mit einem gemeinsamen Crash-Faktor (rho_stress muss ausschlagen); *negativ* = vier unabhaengige Serien mit identischen Randverteilungen inkl. fetter Tails (rho_stress darf NICHT ausschlagen -- genau hier stirbt ein naives Gate). (B) *positiv* = synthetisches Buch mit hoher Queue-Rotation; *negativ* = Buch, in dem der Touch nur bei adverser Bewegung geraeumt wird (p_fill hoch, adv_sel toedlich -- das Gate muss den zweiten Fall trennen).
- **Was ihn a priori toetet:** nichts -- er ist per Konstruktion beantwortbar. Das einzige Risiko ist, dass (A) auf zu wenigen Stress-Tagen steht (N-Floor >= 15 gemeinsame Extremtage; bei Unterschreitung **KEIN VERDIKT**, nicht DROP -- die H-10/H-13-Falle).
- **Bezug zu Kompendium D/E:** Wiederholt **nichts** aus D. Nutzt E-Faden 5 (WP-3 war die vertagte L2-Ereignis-Extraktion) nur teilweise -- (B) braucht kein Sweep-Modell, nur die vorhandene Replay-Maschinerie. Schliesst die von WP-4 offen gelassene Luecke (Spread gemessen, Fill-Wahrscheinlichkeit nie).
- **Vertrauen:** **hoch.** Vollstaendig aus dem Bestand, bekannte Werkzeuge, klarer Nulleffekt, und beide Teilbefunde sind unabhaengig von jedem Ertrags-Claim wertvoll.

---

## 2. Gate-Design fuer Praemien-Strategien (Antwort auf Teilfrage (e))

Die bisherigen Gates (IC, AUC, CRPS, rho) messen **Signal**. Eine Praemie hat
kein Signal: sie hat einen Erwartungswert und eine Schadenverteilung. Die
Uebertragung der Programm-Doktrin auf diese Klasse:

**(G1) Ertragsmetrik statt Signalmetrik.** `r_excess` = annualisierte
Netto-Rendite nach einem **vor dem Lauf gepinnten** Kostenmodell, **minus dem
strukturellen Nulleffekt**. Das Kostenmodell ist Anti-Gaming-geschuetzt wie
die 11-bps-Wand (DEC-13/16): Gebuehrensatz, Ausfuehrungsannahme (Maker/Taker),
Rehedge-Frequenz und Haltedauer werden vorher fixiert und **duerfen nicht
gesenkt werden, um ein WEITER zu erzwingen.**

**(G2) Der Nulleffekt ist bei Praemien NIE 0.** Fuer jede Familie vorab
analytisch auszurechnen (DEC-31/33-Pflichtzeile):

| Familie | Nulleffekt |
|---|---|
| Funding-Carry | Boersen-Zins-Anker `I` (10,95% p.a.) minus Stablecoin-Opportunitaetszins |
| Perp-vs-Future | Margin-Bindungsdifferenz x Opportunitaetszins + Jensen-Kruemmung der Terminkurve |
| Skew | RR-Rendite unter **fairer** Preisung auf gebootstrappten historischen Pfaden + Illiquiditaetsbein |
| Term-Vol | systematische Kurvenneigung aus Vol-Mean-Reversion (kalibrierter OU auf log-IV) |
| ETH-vs-BTC-Vol | mittlere realisierte Vol-Differenz aus dem WP-0-Bar-Cache |
| Stress-Korrelation | Extremstichproben-Selektionseffekt aus Surrogaten mit identischer Randverteilung |

**(G3) Sharpe mit Stationary-Block-Bootstrap, nicht mit i.i.d.-t-Test.**
Praemien-PnL ist stark autokorreliert (Funding ist AR(1) mit Halbwertszeit
in Tagen). Verfahren: Politis-Romano-Stationary-Bootstrap, mittlere
Blocklaenge `L` aus dem integrierten Autokorrelations-Zeitmass
`L = 1 + 2*sum_k rho_k` der taeglichen PnL, `B = 10.000`.
**Rauschboden, hergeleitet statt importiert:**
`SE(SR) = sqrt((1 + SR^2/2) / N_eff)` mit `N_eff = T/L`.
Beispiel 12 Monate, `L = 30 Tage`: `N_eff ~ 12`, `SE(SR) ~ 0,31`
-> **Schwelle SR >= 0,60 ist ~2 Sigma.** Wer bei `N_eff = 12` eine Schwelle
von 0,2 setzt, misst Rauschen -- das ist die H-11-Lehre, auf Sharpe uebertragen.

**(G4) Tail-Ratio als eigenstaendiges, nicht verhandelbares Gate.**
`TR = |CVaR_1%(taegliche PnL)| / mean(taegliche PnL)`, in Tagen gelesen:
"wie viele Tage Praemie frisst ein Tag im schlechtesten Prozent". Schwelle
**TR <= 250 Tage** (ein Tail-Tag darf weniger kosten als eine Jahresernte).
Begruendung, warum das ein SEPARATES Gate ist und kein Bestandteil des
Sharpe: eine Praemie mit Sharpe 6 und TR 2.000 ist kein Ertrag, sondern eine
noch nicht praesentierte Rechnung. Genau das dokumentiert die
Literatur-Zeitreihe (Sharpe 6,45 -> 4,06 -> negativ) und der 10.10.2025.

**(G5) Stress-Pflicht (PRD Par.8.4, woertlich uebertragen).** Jedes
urteilstragende Fenster muss **>=1 dokumentierte Stress-Episode** enthalten.
Fehlt sie: **KEIN VERDIKT**, nicht WEITER. Ein Praemien-PASS auf einem
stressfreien Fenster ist per Konstruktion ein Peso-Artefakt.

**(G6) Regime-Bedingtheit.** `r_excess` je Regime-Bucket (Funding-Vorzeichen-
Terzil, IV-Terzil, Trend-Terzil; fuer Options-Kandidaten zusaetzlich das
Dealer-Gamma-Vorzeichen). Anforderung: gleiches Vorzeichen in **>=4 von 6**
Buckets UND kein Bucket mit `r_excess < -2x` der Gesamtpraemie. Das trennt
"Praemie" von "ein Regime, das zufaellig lange anhielt".

**(G7) Crowding-/Erosions-Klausel (neu, spezifisch fuer diese Klasse).**
`r_excess(juengstes Fenster) >= 0,5 * median(r_excess der aelteren Fenster)`.
Verfehlt -> **PARK ("Praemie erodiert"), nicht DROP.** Begruendung: ein
6-Jahres-Mittelwert kann einen 2026 toten Ertrag ausweisen; die REZENZ-Klausel
(C.18) verlangt genau diese Trennung, und die Literatur behauptet den Zerfall
explizit.

**(G8) Hartes Ein-Fenster-Abbruchkriterium (C.10) bleibt unveraendert** ueber
>=2 disjunkte 12-Monats-Fenster, das juengste endet am Laufdatum.

**(G9) FDR.** Familien-BH bei alpha=0,10 innerhalb `F-PREM1`
(K-01/K-02/K-03) und `F-PREM2` (K-04/K-05/K-06); `F-PREM0` (K-07) separat,
weil kein Ertrags-Claim. Zweistufig darueber `F-PREM-ALL` ueber die
gepoolten Survivor (DEC-22) -- rein verschaerfend.

**(G10) Mess-Gate != Tradability-Gate bleibt bindend (C.2).** Ein PASS auf
G1-G9 ist ein **kapitalfreies** WEITER. Die Tradability-Folge (Fill-Annahmen,
Margin-Call-Pfad, ADL-Risiko, Borrow-Verfuegbarkeit) braucht einen eigenen
Registry-Eintrag mit eigenen Schwellen -- hier ausdruecklich **nicht**
registriert und **nicht** impliziert.

---

## 3. Rangliste

| Rang | Kandidat | Warum hier |
|---|---|---|
| **1** | **K-01 Funding-Carry-Zensus** | Bester Mechanismus-Beleg, billigste Daten (keyfrei, Minuten), Sekunden Rechenzeit, klarer und ausrechenbarer Nulleffekt, und die Literatur liefert den Falsifikator (Erosion) gleich mit. Der einzige Blocker ist eine 5-Minuten-Pruefung der Endpunkt-Tiefe. |
| **2** | **K-07 Kohaerenz + Maker-Fill-Zensus** | Kein Ertrag, aber die hoechste Entscheidungsdichte je Rechenstunde: entscheidet ueber die gesamte Portfolio-These (d) UND ueber die Gueltigkeit jedes Maker-Kostenmodells im Options-Pfad. Vollstaendig aus dem Bestand, bekannte Werkzeuge. **Sollte VOR K-04/K-05/K-06 laufen.** |
| **3** | **K-03 Perp-vs-datierter-Future** | Beste Friktion im ganzen Feld (3 Fills, 6 bp Maker, gebuehrenfreies Settlement), entsperrt formal C-23. Abgewertet nur wegen zweier unbelegter, potenziell toedlicher Punkte: Liquiditaet der datierten Kontrakte und Abrufbarkeit historischer Klines. Beide in einem einzigen Call pruefbar. |
| **4** | **K-02 Intra-Venue-Funding-Spread** | Sauber, kein Cross-Venue-Risiko, exzellente Kapitaleffizienz -- aber unbelegte und vermutlich kleine Kante. Der 0,4%-Vorab-Check auf 43 vorhandenen Tagen kostet nichts und entscheidet. |
| **5** | **K-04 Skew-Praemie** | Staerkster Options-Mechanismus mit Literaturdeckung, und die einzige Options-Struktur, deren Hedge-Kasse tragbar ist (Gamma-Neutralitaet des Risk Reversal). Abgewertet, weil die Datenlage 38 Tage betraegt und die E.6-Reihenfolge (H-26 zuerst) bindend ist. |
| **6** | **K-05 Kalender-/Forward-Vol** | Wahrscheinlich struktureller A-priori-DROP wegen Netto-Vega-Verduennung (84% der Kante an Gebuehren). Wert liegt im Vorab-Kill und in der verallgemeinerbaren Lehre. |
| **7** | **K-06 ETH-vs-BTC-Relative-Vol** | Teuerster Kandidat (~3,9 Vol-Punkte Maker), schwaechster Mechanismus, und der klassische Dispersions-Mechanismus existiert in dieser Marktstruktur gar nicht. Nur der Vollstaendigkeit halber aufgefuehrt. |

**Empfohlene Sequenz (Einzelbetreiber-Realismus, PRD Par.9, max. 1 neuer
Alpha-Test je Welle):** zuerst die drei kostenlosen Vorab-Checks
(Funding-Endpunkt-Tiefe; `turnover24h` der datierten Kontrakte; mediane
Intra-Venue-Funding-Differenz auf den 43 Harvest-Tagen). Dann **K-01 als
einziger registrierter Alpha-Kandidat der Welle**, mit **K-07 parallel als
Infrastruktur-/Zensus-Paket** (kein Alpha-Budget, analog WP-4/WP-5). K-03
folgt, sobald sein Liquiditaets-Check steht. Der Options-Block (K-04..K-06)
bleibt hinter H-26 gesperrt.

---

## 4. Was ich NICHT vorschlage und warum

1. **Funding-Rate-PROGNOSE in jeder Form** (DSM-03, CS-12-Funding-Uhr,
   C-08/C-22-Quantilvarianten). Das ist eine Richtungsprognose mit
   Praemien-Etikett und dupliziert D.17 sowie H-01 (DROP bei -15,47 bps).
   Der Auftrag verlangt ausdruecklich Ertragsquellen **ohne** Prognose.
   Dass der `premium-index-price-kline`-Endpunkt DSM-03s Datenblocker
   aufloest, aendert daran nichts -- das ist ein Datenbefund, kein Signalbefund.
2. **Pre-Settlement-Funding-Druck (H-01/CS-03) in jeder Neuauflage.**
   Endgueltig adjudiziert, RAW-Edge -4,48 bps.
3. **Reaktives Long-Vol / Strangle-Kauf auf ein Bewegungssignal** (D.15).
   WP-6 hat es quantifiziert getoetet; K-04/K-05 sind kalendergetriebene
   Einstiege, keine Reaktionskaeufe.
4. **Spread-Capture / Market-Making** (D.1). Ein Tick Top-of-Book. Tot.
   K-07(B) fragt ausdruecklich **nicht** nach Spread-Ertrag, sondern nach
   Fill-Wahrscheinlichkeit als Kostenparameter.
5. **Eine zweite VRP-Messung.** H-26 ist registriert und gesperrt.
   K-04/K-05/K-06 sind bewusst **vega-neutral bzw. Steigungs-/Schiefe-
   basiert**, damit sie H-26 nicht duplizieren; K-04 kuerzt das Vol-Niveau
   per Konstruktion heraus.
6. **Cross-Exchange-Funding-Arbitrage mit Binance/Deribit als HANDELSplatz.**
   Verletzt die harte Randbedingung (Bybit-only, Deribit nur als Datenquelle)
   und fuehrt Transfer-, Verwahr- und Ausfallrisiko ein, das kein
   kapitalfreies Mess-Gate abbildet. K-02 holt denselben Mechanismus
   **innerhalb** einer Boerse.
7. **Die Short-Spot-Seite des Carry (Ernte negativer Funding-Raten).**
   Braucht einen Coin-Borrow zu variablen, stuendlichen, **ohne API-Keys
   nicht messbaren** Saetzen. Ein Gate mit einer geratenen Kostenzeile ist
   kein Gate. Die Asymmetrie ist zugleich der Grund, warum die Praemie
   ueberhaupt existiert -- sie gehoert in K-01 als Mechanismus-Argument,
   nicht als Handelsseite.
8. **Nackte Strangle-/Put-Verkaeufe ohne Delta-Hedge.** Das ist eine
   Richtungswette mit Praemien-Etikett; Tail-Ratio-Gate (G4) wuerde sie
   ohnehin toeten, und WP-6 zeigt, dass der Not-Ausstieg im Stress
   9,5-53,8 Vol-Punkte kostet.
9. **Ethena-artige Yield-Produkte, Staking-, Earn- oder Savings-Renditen.**
   Kein Derivat, kein oeffentlicher Messpfad, und das 10.10.2025-USDe-Depeg
   zeigt, dass genau dort die Praemie und das Tail zusammenfallen.
10. **Klassische Dispersion (Index-Vol vs. Komponenten-Vol).** Existiert auf
    Bybit nicht -- es gibt keine Index-Option. Ich strecke die Analogie nicht,
    sondern nenne K-06 beim Namen (relative Vol-Praemie) und weise sie als
    schwach aus.
11. **Jede GPU-/Deep-Learning-Aufbereitung dieser Praemien.** S4/S5-Falle
    (D.16): schwere Infrastruktur vor validiertem Basissignal. Alle sieben
    Kandidaten laufen in Sekunden bis Minuten auf CPU. Das ist ein Merkmal,
    kein Mangel.

---

## 5. Belegstatus -- was ich NICHT verifizieren konnte

Der Egress-Proxy blockiert `api.bybit.com`, `bybit.com`,
`bybit-exchange.github.io`, `arxiv.org`, `bis.org`, `cepr.org`,
`insights.deribit.com` und `bitmex.com`. Daraus:

| Punkt | Status |
|---|---|
| Endpunkt-Spezifikationen (`funding/history`, `premium-index-price-kline`, `instruments-info`, `delivery-price`, Enums, Rate-Limit) | **belegt** -- aus dem Doku-Quell-Repo `bybit-exchange/docs` (main) gelesen |
| Existenz von `LinearFutures` (USDC) und `InverseFutures` (Quartale) | **belegt** (Enum + Symbolbeispiele) |
| **Historientiefe** von `funding/history` und `premium-index-price-kline` | **UNBELEGT** -- kein dokumentiertes Limit, kein Probe moeglich. Erster Schritt jeder Registrierung. |
| **Liquiditaet** der datierten Bybit-Kontrakte | **UNBELEGT** -- ein `tickers`-Call klaert es |
| Bybit Spot-Gebuehr VIP0 = 0,1% Maker == Taker | **sekundaerbelegt** (mehrere unabhaengige Gebuehren-Uebersichten 2026) |
| Options-Delivery-Gebuehr min(1,5 bp Index; 12,5% Intrinsic), nur ITM | **sekundaerbelegt** -- schliesst E.6(a), muss aber vor der H-26b-Registrierung an der Primaerquelle bestaetigt werden |
| Funding-Formel + Zins-Anker `I` = 0,01%/8h + Cap-Regel | **sekundaerbelegt**, mehrfach konsistent |
| Schmeling/Schrimpf/Todorov-Zahlen (Sharpe 6,45 / 4,06 / negativ; ~8% Mittel bei 0,8% Vol; >40% Spitzen-Carry) | **sekundaerbelegt** -- Volltext (BIS WP 1087) nicht abrufbar; vor Zitation in einer Registrierung im Original nachschlagen |
| Basis-Kompression 25% (02/2024) -> 4,46% (12/2025), 93% der Tage <5% | **sekundaerbelegt**, niedriges Vertrauen fuer die Praezision |
| 10.10.2025-Ereignis (Groessenordnung, ADL, Depegs, Tiefenverlust) | **sekundaerbelegt** aus mehreren unabhaengigen Quellen; Einzelzahlen niedriges Vertrauen, Ereignis selbst hohes |
| Intra-Venue-Funding-Spread (K-02) -- Groessenordnung | **UNBELEGT**, keine Literatur gefunden |
| Skew-**Praemie** (nicht: Skew) auf Bybit, Groesse | **UNBELEGT** |
| Forward-Vol-Praemie in Krypto, Groesse | **UNBELEGT** |

*Ende R1_RISIKOPRAEMIEN.md*
