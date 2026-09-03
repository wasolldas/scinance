# S4 - Kausalinferenz aus natuerlichen Experimenten

**Disziplin:** Oekonometrie der Politikevaluation / Epidemiologie der natuerlichen Experimente
(RDD, RKD, Diff-in-Disc, staggered DiD, IV, Event-Study-Inferenz).
**Scout:** S4, Phase 3b "Wissenschafts-Exkurs" (Scinance 3.0)
**Stand:** 2026-09-03
**Gelesen (vollstaendig):** ERKENNTNIS_KOMPENDIUM.md (A-F), PRD_SCINANCE3.md (1, 2, 3.1-3.12,
4.1-4.4, 5.1-5.2, 7.1-7.3, 9.1-9.3), CROSSDOMAIN_PARK.md, CROSSDOMAIN_PRD.md (H-09..H-13 woertlich).
**Sprache:** Deutsch, ASCII-safe, Umbruch bei 100 Spalten.
**Umfang:** ~670 Zeilen / ~6.400 Woerter. Das Ziel 300-500 Zeilen ist ueberschritten, weil die zehn
Pflichtfelder des Ausgabeformats viermal ausgefuellt sind und Abschnitt 1 die Boersenmechanik
traegt, auf der alle vier Identifikationen beruhen.
**Repo-Status:** read-only, nichts geschrieben ausser dieser Datei.

---

## 0. Die Luecke, die diese Disziplin schliesst

In 31 Gate-Eintraegen hat das Programm **kein einziges Mal** einen kausalen Identifikationsansatz
benutzt: gemessen wurden Korrelationen (H-04, H-05, H-22, H-24), Prognosekonkurrenzen (H-02, H-11,
H-11c), Verteilungs- und Spektraleigenschaften (H-03, H-06, H-12, H-16) und Klassifikationen (H-17,
H-23). Der einzige Ansatz in der Naehe einer Identifikationsstrategie - H-09, Bunching an
Risk-Limit-Tier-Kanten - modellierte die Kante als *Ziel* der Verhaltensanpassung, nicht als
*Zuweisungsregel eines Treatments*, und ist D.8-tot.

Die Beobachtung, die den Exkurs traegt: **Bybit ist ungewoehnlich reich an harten, oeffentlich
dokumentierten, mechanischen Zuweisungsregeln.** Die Funding-Formel ist stueckweise linear mit zwei
exakt bekannten Knickpunkten; die Abrechnungsfrequenz wird seit dem 30.10.2025 **automatisch durch
das Ueberschreiten einer berechenbaren Schwelle** ausgeloest; Risk-Limit- und Intervall-Aenderungen
werden symbolweise und gestaffelt angekuendigt. Genau dort spielen RDD/RKD/DiD ihren Vorteil aus:
die Zuweisung ist keine Selbstselektion des Haendlers, sondern eine Regel des Betreibers.

Alle vier Vorschlaege sind **kapitalfrei**, **CPU-only**, und keiner ist eine gerichtete Prognose
unter Tageshorizont (Randbedingung 3): X-NEXP-1/2/3 messen Praemien- und Regime-Groessen
(horizontfrei), X-NEXP-4 ist ausdruecklich eine **Kosten-/Struktur-Messung** (Impact-Koeffizient),
nie eine Kante.

---

## 1. Die Mechanik, aus der die Identifikation kommt (Herleitung, nachrechenbar)

### 1.1 Die Funding-Klemme erzeugt einen KNICK, keinen SPRUNG

Bybits Funding-Satz je 8h-Intervall:

```
F = P + clamp(I - P, -0,05 %, +0,05 %),      I = 0,01 % je 8h
```

[sek: Bybit Help Center "Introduction to Funding Rate" / Bybit Learn, ueber Suchtreffer; `bybit.com`
und `announcements.bybit.com` sind vom Egress-Proxy geblockt - Primaerseite nicht abrufbar. Der
Zins-Term I = 0,01 %/8h steht bereits als PRD-9.2-Wert (R1 0.2 [sek]) im Programm.]

Daraus folgt durch reines Aufloesen der drei Faelle (eigene Herleitung):

| Bereich des Praemien-Index P | Funding F | dF/dP |
|---|---|---|
| `P < -0,04 %` | `P + 0,05 %` | **1** |
| `-0,04 % <= P <= +0,06 %` (**Totzone**) | **exakt 0,01 %** | **0** |
| `P > +0,06 %` | `P - 0,05 %` | **1** |

Drei Konsequenzen, die das Dokument tragen:

1. **F ist an P = -0,04 % und P = +0,06 % stetig, die Ableitung springt von 0
   auf 1.** Das ist definitionsgemaess ein **Regression Kink Design**
   (Card/Lee/Pei/Weber 2015), **kein** RDD - wer hier "Sprung" sagt, misst
   nichts. Die Sprunghoehe des ersten Stadiums ist mit **exakt 1,0** bekannt:
   der seltene Fall eines RKD mit analytisch bekanntem erstem Stadium.
2. **Der oekonomische Hebel am Knick ist gewaltig.** Bei P = 0,06 % ist die
   Carry 0,01 %/8h = 10,95 % p.a., bei P = 0,07 % ist sie 0,02 %/8h =
   21,90 % p.a.: **ein Basispunkt Preisabweichung verdoppelt am Knick die
   annualisierte Carry**, waehrend dieselbe Bewegung innerhalb der Totzone
   exakt null bewirkt. Die Horizont-Friktions-Kurve (K-0.1) ist dafuer
   irrelevant - gemessen wird kein 1-bp-Preisereignis, sondern eine
   Praemien-Steigung ueber Tage.
3. **F ist ausserhalb der Totzone invertierbar** (`P = F +/- 0,05 %`) und
   **innerhalb intervall-zensiert**: alle Symbole der Totzone tragen denselben
   Wert 0,01 %. Das ist ein direkter Befund fuer A1s Sortierschluessel
   (X-NEXP-1, Entscheidungsrelevanz).

### 1.2 Die Funding-Kappe erzeugt einen echten SPRUNG - im Treatment

```
Cap = +/- min( (IMR - MMR) * k , MMR ),  k = 0,75, dynamisch in [0,5; 1,0];
IMR/MMR der NIEDRIGSTEN Risk-Limit-Stufe des Symbols
```
[sek: Bybit Help Center "Introduction to Funding Rate" ueber Suchtreffer.]

Und - das ist der Kern - seit **30.10.2025 08:00 UTC** (Vollausrollung **03.11.2025 06:00 UTC**):

> "When a Perpetual Contract's funding rate reaches its preset upper or lower
> limit during settlement, the system will automatically switch the settlement
> frequency to once per hour."

[sek: PRNewswire 2025-10-29, Chainwire 2025-10-29, CryptoTimes 2025-10-29, crypto-economy - alle
ueber Suchtreffer; Primaer-Announcement egress-gesperrt.]

Damit gilt: `Treatment(1h-Abrechnung) = 1{ |F_latent| >= Cap }` - eine **scharfe, deterministische
Zuweisung auf einer beobachtbaren Laufvariablen**. Ausgenommen waren zum Start ausdruecklich
BTCUSDT, BTCUSDC, BTCUSD, ETHUSDT, ETHUSDC, ETHUSD, ETHBTCUSDT, ETHWUSDT [sek, dieselbe Quelle] -
ein **betreiberdefinierter, nicht selbstgewaehlter Kontrollarm innerhalb der eigenen Boerse**.

Zwei technische Punkte, die die Identifikation retten bzw. begrenzen:
- **Die Laufvariable ist zensiert, das Treatment nicht.** F kann die Kappe nie
  ueberschreiten, es gibt in F also keine Beobachtungen knapp darueber. Die
  Laufvariable muss die **latente, unzensierte** Rate `F_latent = P -/+ 0,05 %`
  aus dem Praemien-Index sein - sonst baut man ein RDD ohne rechte Seite.
- **Der Cutoff ist beobachtbar, aber nicht konstant.** Weil k dynamisch in
  [0,5; 1,0] liegt, ist Cap nicht a priori bekannt - aber **jeder gekappte
  Print IST der Cap-Wert**. Vorab fixierte Regel: eine Symbol-Episode zaehlt
  nur, wenn ein gekappter Print innerhalb von +/-7 Tagen den Cap pinnt.

### 1.3 Warum das NICHT H-09 ist (D.8-Abgrenzung, verbindlich)

| | **H-09 (D.8, tot)** | **X-NEXP-1/2 (hier)** |
|---|---|---|
| Laufvariable | Order-Notional - **vom Agenten frei waehlbar** | Praemien-Index / latente Funding-Rate - **Aggregatgroesse, vom einzelnen Agenten nicht positionierbar** |
| Schwelle | Risk-Limit-Tier-Kante K_s (zugleich Rundzahl) | Klemmengrenze bzw. Funding-Cap - **keine Rundzahl, aus IMR/MMR berechnet** |
| Estimand | **Excess Mass** in der DICHTE der Laufvariablen | **Knick/Sprung im bedingten ERWARTUNGSWERT eines Ergebnisses** |
| Identifizierende Annahme | glatte kontrafaktische Dichte | Stetigkeit der kontrafaktischen Ergebnisfunktion **plus** glatte Dichte |
| Rolle der Dichte | Dichte-Anomalie ist das **gesuchte Signal** | Dichte-Anomalie ist ein **Falsifikator** (RDD waere ungueltig) |
| Wer handelt | der einzelne Haendler (Margin-Kink-Vermeidung) | der Betreiber (Regel) und in der Antwort das **Arbitragekapital im Aggregat** |
| Was ein DROP bedeutete | Haendler steuern Ordergroesse nicht am Margin-Kink | - (offen, noch nie gemessen) |

**Das H-09-DROP ist kein Hindernis, sondern eine Vorbedingungs-Stuetze.** Mit 0/10 Zellen und
vorzeichen-wilden Schaetzern (-3,49 bis +10,20) hat H-09 gezeigt, dass an mechanischen Kanten dieses
Marktes **keine** systematische Manipulation der Laufvariablen stattfindet - genau die Annahme, die
ein RDD braucht (McCrary 2008; Cattaneo/Jansson/Ma 2020). D.8 wird hier also als Beleg **fuer** die
No-Manipulation-Annahme zitiert und am eigenen Cutoff mit umgekehrter Erwartung nachgemessen.
**Bunching-Estimatoren sind in keinem der vier Vorschlaege urteilstragend**; sie kommen nur als
Manipulationstest vor. Der Massenpunkt von F bei exakt 0,01 % ist kein Bunching, sondern ein
mechanisches Zensierungsartefakt der clamp-Funktion - ihn so zu nennen waere ein Kategorienfehler.

---

## 2. Die vier Vorschlaege

### X-NEXP-1 - Regression Kink Design an der Funding-Klemme: die Angebotselastizitaet des Arbitragekapitals

**Methode.** Sharp Regression Kink Design an den beiden exakt bekannten Knickpunkten P* = -0,04 %
und P** = +0,06 % des Praemien-Index. Das erste Stadium (dF/dP springt von 0 auf 1) ist analytisch
bekannt und muss nicht geschaetzt werden; geschaetzt wird der Knick im bedingten Erwartungswert
eines **verhaltensbasierten** Ergebnisses. Lokale lineare/quadratische Regression beidseits des
Knicks, MSE-optimale Bandbreite und bias-korrigierte robuste CIs nach Calonico/Cattaneo/Titiunik;
Inferenz **nicht** ueber konventionelle SEs, sondern ueber die Placebo-Knick-Verteilung nach
Ganong/Jaeger. *Primaerliteratur:* Card, Lee, Pei, Weber (2015), "Inference on Causal Effects in a
Generalized Regression Kink Design", **Econometrica 83(6), 2453-2483**; Ganong, Jaeger (2018), "A
Permutation Test for the Regression Kink Design", **JASA 113(522), 494-504**; Calonico, Cattaneo,
Titiunik (2014), Econometrica 82(6), 2295-2326; Kolesar, Rothe (2018), "Inference in RD Designs with
a Discrete Running Variable", AER 108(8), 2277-2304 (die Laufvariable ist tick-diskret); Cattaneo,
Jansson, Ma (2020), JASA 115(531), 1449-1455 (Manipulationstest). [Alle Zitate ueber
Suchtreffer/Abstract verifiziert; Volltexte egress-gesperrt - Seitenzahlen [sek].]

**Uebertragung auf den Bestand.** Strom: `premium-index-price-kline`
(`/v5/market/premium-index-price-kline`, category=linear, limit bis 1000, oeffentlich und keyfrei
[sek: Bybit-API-Doku ueber Suchtreffer]) plus `funding/history` (bereits als A1-Backfill in PRD 7.1
eingeplant) plus `kline?interval=60`. Aufloesung: 1h-Praemien-Index, daraus der
8h-Intervall-Mittelwert als Naeherung an Bybits Minuten-TWAP; der Approximationsfehler wird an einer
1-min-Stichprobe (5 Symbole, 90 Tage) gemessen und berichtet, nicht angenommen. Symbole: das
WP-7-Universum, soweit `premium-index-price-kline` Historie liefert (Tiefe **UNBELEGT**, Vorfrage
V-S4-1). Horizont: naechstes Funding-Intervall (8h) bis 3 Tage - **Praemien-Gradient, damit
horizontfrei** (Randbedingung 3). **Klasse: R (Regime-Konditionierer) mit X-Anteil (Enabler fuer
A1).**

*Urteilstragende Statistik (genau EINE, nach A2-Muster):* der Knick in `E[ dP_{t+1} | P_t ]` an P**
= +0,06 %, also die Aenderung der Kompressionsrate des Praemien-Ueberschusses. Interpretation: unter
einem linearen Arbitrage-Angebotsmodell ist der geschaetzte Knick **exakt die Elastizitaet e des
Arbitragekapitals bezueglich der Carry** - wieviel Kompression kauft ein zusaetzlicher Basispunkt
Kompensation. e = 0: niemand reagiert auf den Funding-Anreiz. e = 1: der Ueberschuss wird binnen
eines Intervalls vollstaendig wegarbitriert. Der untere Knick P* und die OI-Reaktion werden **nur
berichtet** (K = 1, FDR-Familie mit einem Test).

**Struktureller Nulleffekt der Metrik (C.4).** Drei Ebenen, alle gemessen: (a)
**Placebo-Knick-Verteilung (Ganong/Jaeger)** - derselbe Schaetzer an allen Nicht-Knick-Punkten des
Traegers von P im selben Bandbreitenraster; ihre SD ist die Nullverteilung, ihr 95-%-Quantil die
Schwelle. Ganong/Jaeger dokumentieren, dass RK-Signifikanz auf konventionellen SEs **regelmaessig
spurios** ist - die L-2-Falle dieser Disziplin. (b) **Analytische Null**: ein
Ornstein-Uhlenbeck-Praemienprozess mit konstanter Rueckkehrrate hat `E[dP|P] = -theta*P`, also Knick
exakt 0, auch unter der clamp-Funktion. (c) **Diskretisierungs-Null**: P ist tick-diskret, naives
lokales Polynomfitten erzeugt Schein-Knicke an Gitterpunkten (Lee/Card 2008; Kolesar/Rothe 2018) -
vorab fixiert: honest CIs fuer diskrete Laufvariablen, und P*/P** duerfen nicht auf einem
Gitterpunkt der Binning-Aufloesung liegen.

**Feasibility-Skizze.** Cluster-Einheit nach DEC-51 Punkt 3: **Kalendertag** (alle Symbole eines
Tages teilen den Marktschock). N_cluster = 365 je REZENZ-Fenster (W1 2024-09-01..2025-08-31, W2
2025-09-01..2026-08-31), 730 gepoolt. Die bindende Zahl ist **nicht** N_c, sondern N_eff mit dem
**gemessenen** rho zwischen Tagen:

```
N_eff = N_c / (1 + (N_c - 1) * rho)
  N_c = 365, rho = 0,00  -> 365
  N_c = 365, rho = 0,02  -> 44,4
  N_c = 365, rho = 0,05  -> 19,0   (unter dem N-Floor 20!)
```

Das ist der ehrliche Engpass **jedes** Tages-Cluster-Designs im Programm und gilt genauso fuer WP-7
und A1. Vorab fixiert: rho wird gemessen, und N_eff wird zusaetzlich per **stationaerem
Block-Bootstrap** bestimmt (Politis, Romano 1994, JASA 89(428), 1303-1313), weil die
Aequikorrelationsformel fuer *seriell* korrelierte Tagesschaetzer ein konservativer Grenzfall ist.
Beide Zahlen werden berichtet, die kleinere urteilt; N_eff < 20 in einem Fenster -> GL-012.
*Erwartete Effektgroesse:* **UNBELEGT** - es gibt keine Krypto-RKD-Literatur zur Funding-Klemme, und
ein importierter Skalar waere ein C-14-Wiedergaenger (L-1). L-1-konformer Weg: die Vorfrage misst
zuerst die unbedingte Kompressionsrate `theta`; die Schwelle ist dann `max(95-%-Quantil der
Placebo-Knick-Verteilung; 2,4865 * SD_placebo)`, die A-priori `e >= 0,25*theta`. Ohne diese
Vormessung ist der Vorschlag ein GL-012-Fall. *REZENZ (C.18):* beide Fenster liegen nach dem
Spot-ETF-Start, die Klemme gilt durchgehend. 1h-Symbole ab 11/2025 haben moeglicherweise andere I-
und clamp-Werte (**UNBELEGT**, Erweiterung von V-1) und werden bis zur Klaerung ausgeschlossen und
nur berichtet.

**Rechenbudget.** Backfill: 1h-Praemien-Index fuer K = 200 Symbole ueber 2 Jahre = 17.544
Punkte/Symbol, limit 1000 -> **18 Calls/Symbol = 3.600 Calls = 12 min** bei 5 Req/s (4,2 % des
120-Req/s-Limits, PRD 7.1); ~3,5 Mio Zeilen, 80-140 MB. 1-min-Kontrollstichprobe 5 Symbole x 90 Tage
= 648 Calls = 2 min. Rechnen: lokale Polynome + 1.000 Placebo-Knicke x 2 Fenster: **CPU, < 30 min**,
< 4 GB RAM. **GPU: 0.**

**Nicht-Duplikat-Nachweis.** Naechster Nachbar **D.8/H-09** - Abgrenzung in
1.3 (andere Laufvariable, anderer Estimand, Dichte als Falsifikator statt als
Signal). Zweitnaechster **D.17/DSM-03** ("Funding-Premium-Vorhersage", gestrichen wegen 43 Tagen
Delta-Strom): DSM-03 wollte den Praemien-Index **prognostizieren**; X-NEXP-1 prognostiziert nichts,
sondern schaetzt eine Steigungsaenderung - und nutzt den **oeffentlichen REST-Kline-Pfad** statt des
Delta-Stroms, also genau den Pfad, den PRD 7.1 fuer Klines oeffnet und den DSM-03 nie geprueft hat
(C.8: Abwesenheit eines Harvest-Stroms ist kein Beweis fuer Abwesenheit der Daten). Kein
PARK-Eintrag (IC-MECH-1..4, IC-NET-1..3, IC-EVT-2/3, IC-RMT-1/3/4, IC-CLIM-2/3, IC-DEND-2/3) benutzt
eine Identifikationsstrategie.

**Entscheidungsrelevanz.** *PASS (e deutlich > 0):* Das Arbitragekapital reagiert messbar auf die
Funding-Kompensation - die Funding-Praemie wird aktiv wegkonkurriert. Konsequenz fuer **A1**: der
Carry im obersten Dezil ist kein freies Mittagessen, sondern der Gleichgewichtspreis knapper
Arbitragekapazitaet, und A1s Praemie ist nach oben durch e gedeckelt; die A1-Registrierung erhaelt
eine Pflicht-Sensitivitaet gegen e. *PASS (e ~ 0):* niemand reagiert - die Praemie ist
unkontestiert; das ist die staerkste denkbare Vorab-Stuetze fuer A1 und macht die Zahler-Zeile
(3.3.9c) erstmals empirisch pruefbar. *DROP (kein Knick nachweisbar):* der Funding-Satz ist kein
handlungsleitender Anreiz auf dieser Zeitskala - das entwertet **jede** Interpretation von Funding
als "Kompensation" und trifft A1s Ertragsquellen-Erzaehlung direkt (nicht A1s Mess-Gate; C.2).
*Zwingender Nebenbefund in jedem Ausgang - der **Totzonen-Zensus**:* der Anteil der
Symbol-Intervalle mit F **exakt** 0,01 %. Alle diese Symbole tragen denselben Sortierschluessel; ist
der Anteil hoch (die Totzone ist 10 bp breit), ist A1s Dezil-Sortierung ueber weite Teile des
Querschnitts **degeneriert** und das effektive K bricht ein. Eine GL-012-relevante
A1-Feasibility-Zahl, die im PRD nicht vorkommt und in Minuten aus dem geplanten Funding-Backfill
faellt.

**Fixture-Paar (DEC-39/C.5).** *Positiv:* OU-Praemienprozess, in dem Arbitragekapital nur bei |F| >
I zufliesst (e = 0,30) - der Schaetzer muss 0,30 im CI wiederfinden und die Placebo-Verteilung muss
ihn klar trennen. *Negativ:* derselbe Prozess mit konstantem e und zusaetzlich **nichtlinearer**
Rueckkehr (kubisch) - der Knick muss innerhalb der Placebo-Verteilung bleiben. *Adversarial (3.3.5,
Klasse R analog W):* ein Praemienprozess, dessen Volatilitaet mechanisch mit |P| waechst - erzeugt
heteroskedastie-getriebene Scheinknicke; die honest-CI-Variante muss durchfallen lassen.

**Risiko-Etikett: Blick wert** - mit der ausdruecklichen Auflage, dass RKD ohne
Ganong/Jaeger-Permutation als methodisch invalide gilt (C.13-Muster).

---

### X-NEXP-2 - Difference-in-Discontinuities an der Funding-Kappe: der automatische 1h-Wechsel

**Methode.** Sharp RDD an `F_latent = Cap` mit dem Treatment "Umschaltung auf stuendliche
Funding-Abrechnung", **plus** derselbe RDD im Zeitraum **vor** dem 30.10.2025, in dem derselbe
Cutoff existierte, aber **kein** Treatment ausgeloest wurde. Urteilstragend ist die **Differenz der
beiden RD-Schaetzer** (Difference-in-Discontinuities). Damit wird jeder Effekt ausdifferenziert, der
schon vorher am Cutoff bestand (Zensierung, extreme Marktbedingungen, Liquidationswellen) - die
identifizierende Annahme schrumpft von "keine anderen Spruenge am Cutoff" auf "**die anderen
Spruenge am Cutoff aendern sich nicht ueber die Reform hinweg**". *Primaerliteratur:* Grembi,
Nannicini, Troiano (2016), "Do Fiscal Rules Matter?", **AEJ: Applied Economics 8(3), 1-30**
(diff-in-disc); Calonico/Cattaneo/Titiunik (2014) fuer die RD-Schaetzung; Hausman, Rapson (2018),
"Regression Discontinuity in Time", Annual Review of Resource Economics 10, 533-552 (die
Reform-Zeitgrenze); Cattaneo/Jansson/Ma (2020) fuer den Manipulationstest. [Seitenzahlen [sek],
Volltexte egress-gesperrt.]

**Uebertragung auf den Bestand.** Stroeme: `funding/history` (Treatment und Ergebnis in einem:
Zeitstempel-Abstaende zeigen die Frequenz, Werte zeigen Cap und realisierte Carry - **derselbe
Backfill, den PRD 7.1 fuer A1 ohnehin plant**), `premium-index-price-kline` (Laufvariable
`F_latent`), `instruments-info` (IMR/MMR/`fundingInterval` heute), `kline?interval=D` und
`interval=60` (Preisergebnisse). Symbole: das WP-7-Universum ohne die acht namentlich ausgenommenen
Major-Kontrakte - **diese acht sind der betreiberdefinierte Kontrollarm** und werden als zweite,
unabhaengige Falsifikation gefahren (an ihnen darf der Sprung nicht existieren). Horizont: 24h bis 7
Tage nach der Umschaltung; Ergebnis ist realisierte Carry und Praemien-Konvergenz - **Praemie,
horizontfrei**. **Klasse: E (Ereignis) mit R-Anteil.**

*Urteilstragende Statistik (genau EINE):* der Diff-in-Disc-Schaetzer auf der **Praemien-Konvergenz
in den 24h nach dem Settlement** (log-Abbau des Praemien-Ueberschusses). Realisierte Carry,
OI-Aenderung und Umsatz werden **nur berichtet**; die realisierte Carry ist zugleich die
**Positivkontrolle** (C.13/3.3.8): sie MUSS mechanisch springen, weil bei gleichbleibendem Satz die
achtfache Abrechnungsfrequenz die Zahlung vervielfacht. Wenn die Pipeline diesen bekannten Sprung
nicht sieht, ist ihr Nullbefund auf der Verhaltensgroesse uninformativ.

**Struktureller Nulleffekt (C.4).** (a) Der **Vor-Reform-RDD** ist der empirische Nulleffekt - der
eigentliche Grund fuer das Design. (b) Placebo- Cutoffs bei 0,5*Cap und 0,75*Cap - dieselben zwei
Placebos wie H-09, hier mit umgekehrter Erwartung (sie muessen **null** liefern). (c)
Manipulationstest auf der Dichte von `F_latent` am Cap (Cattaneo/Jansson/Ma 2020); ein Dichtesprung
waere fatal, die Erwartung "kein Sprung" ist durch D.8 gestuetzt. (d) Randomisierungs-Inferenz:
Reformdatum auf 20 Placebo-Daten mit identischer Kalenderstruktur verschieben.

**Feasibility-Skizze.** Cluster: **Kalendertag** (Kappen-Treffer sind massiv tages-gebuendelt - an
einem Stresstag treffen Dutzende Symbole gleichzeitig; genau der Kolari/Pynnoenen-Fall). N_cluster =
Zahl der Tage mit >= 1 Kappen-Treffer im Post-Reform-Fenster (2025-11-03..2026-08-31, 302 Tage) -
**UNGEMESSEN**, Vorfrage V-S4-2. Groessenordnungsrechnung: ein Cap von 0,375 % (BTCUSDT-Beispiel:
IMR 1,0 %, MMR 0,5 % -> min(0,375; 0,5) = 0,375 % [sek, Formel + typische Tier-Werte]) wird
erreicht, wenn P > 0,425 % je 8h = 1,275 %/Tag Praemie - das sind ausgepraegte Squeeze-Zustaende,
bei Alts regelmaessig, bei Majors selten. Vorab fixierte Kill-Regel: **N_eff < 20 (mit gemessenem
rho und Block-Bootstrap-Gegenrechnung) -> GL-012, keine Registrierung; keine Absenkung des Floors.**
Wegen des Reformdatums kann die Zwei-Fenster-Regel nicht ueber die REZENZ-Haelften laufen; vorab
fixiert: W2a = 2025-11-03..2026-03-31, W2b = 2026-04-01..2026-08-31, und der Vor-Reform-Zeitraum ist
**Kontrolle, kein zweites Urteilsfenster**. DEC-52 greift nur, wenn die Power-Zeile vor dem Lauf <
0,60 ausweist. *Erwartete Effektgroesse:* mechanisch bekannt fuer die Positivkontrolle (Faktor bis 8
in der Zahlungsfrequenz); fuer die Verhaltensgroesse **UNBELEGT** - Schwelle daher wie bei X-NEXP-1
aus der gemessenen Placebo-Verteilung, nicht importiert.

**Rechenbudget.** Kein zusaetzlicher Backfill ueber X-NEXP-1 hinaus (Funding 31 min, Praemien-Index
12 min - beide bereits gezaehlt). Rechnen: RD-Fits +
1.000 Placebo-Ziehungen: **CPU, < 20 min.** **GPU: 0.**

**Nicht-Duplikat-Nachweis.** Naechster Nachbar **H-01** (Pre-Settlement- Funding-Pressure, DROP):
H-01 war ein gerichtetes Einstiegssignal auf der Funding-Uhr (-15,47 bps). X-NEXP-2 hat keine
Richtung, kein Einstiegssignal und keinen Preishorizont unter einem Tag; es misst, ob eine
**Regelaenderung des Betreibers** die Praemien-Dynamik veraendert. Zweitnaechster **A1**: A1 nutzt
Funding als Sortierschluessel, X-NEXP-2 prueft die Mechanik, die diesen Schluessel erzeugt. Kein
PARK-Eintrag beruehrt Funding-Frequenz.

**Entscheidungsrelevanz - der wichtigste Punkt dieses Dokuments.** Der 1h-Wechsel wird **durch A1s
Sortierschluessel selbst ausgeloest**: A1 sortiert nach dem intervall-normierten Funding-Satz, das
oberste Dezil ist per Konstruktion angereichert mit genau den Symbolen, die die Kappe treffen - und
die schalten daraufhin auf stuendliche Abrechnung um. Bei gleichem normierten Satz zahlt ein
1h-Symbol pro Kalendertag bis zu **achtmal** so oft. A1s Normierung blendet damit einen
zustandsabhaengigen, **durch die Sortierung selbst ausgeloesten** Frequenzeffekt aus - ein
mechanischer Selektionseffekt, den weder das PRD noch die vier Reviews nennen. *PASS:* A1 braucht
vor der Registrierung eine frequenzbereinigte Schluesseldefinition und eine Sensitivitaet gegen den
Wechselzustand; `funding_n` wird von einer Buchhaltungsspalte zur urteilsrelevanten
Zustandsvariablen. *DROP:* der Wechsel ist rein buchhalterisch - dann genuegt A1 die
`funding_n`-Normierung, und das ist dann belegt statt angenommen.

**Fixture-Paar.** *Positiv:* synthetische Funding-/Praemienserie, in der das Ueberschreiten des Cap
die Kompressionsgeschwindigkeit verdoppelt - der Diff-in-Disc muss den Faktor finden, der
Vor-Reform-RDD muss null sein. *Negativ:* Cap-Ueberschreitung ohne jede Verhaltensaenderung, nur mit
mechanischer Umetikettierung des Zahlungsplans - Verhaltensgroesse null, Positivkontrolle
(realisierte Carry) MUSS springen. *Adversarial:* Ereignisse, die auf vergangenen Renditen
selektiert werden (H-20-Fehlerklasse), plus ein kuenstlicher Dichtesprung am Cutoff - der
Manipulationstest MUSS anschlagen und das Gate MUSS durchfallen.

**Risiko-Etikett: Blick wert** - beste Identifikation im Feld, aber **N_eff ist der
wahrscheinlichste Killer**; die Vorfrage kostet Minuten und laeuft auf einem Backfill, der ohnehin
gebaut wird.

---

### X-NEXP-3 - Gestaffelte DiD auf angekuendigte, symbolweise Bybit-Regeleingriffe, mit demselben Asset auf Binance als Kontrolle

**Methode.** Staggered Difference-in-Differences mit variierendem Behandlungszeitpunkt. Kein
Two-Way-Fixed-Effects-Schaetzer (verbotene Negativgewichte bei heterogenen Effekten), sondern
Gruppen-Zeit-Behandlungseffekte ATT(g,t) mit **noch nicht behandelten** Einheiten als Kontrolle;
Event-Study-Aggregation ueber den interaction-weighted Schaetzer; Parallel-Trend-Frage nicht per
Vortest, sondern per Sensitivitaets-Analyse. Inferenz zweistufig: (i) Wild-Cluster- Bootstrap auf
der Kohorte, (ii) fuer den Event-Study-Arm zusaetzlich die Korrektur fuer **querschnittliche
Korrelation der abnormalen Renditen**, die das Programm bereits zitiert. *Primaerliteratur:*
Callaway, Sant'Anna (2021), "Difference-in-Differences with multiple time periods", **J.
Econometrics 225(2), 200-230** (verifiziert); Sun, Abraham (2021), J. Econometrics 225(2), 175-199;
de Chaisemartin, D'Haultfoeuille (2020), AER 110(9), 2964-2996; Borusyak, Jaravel, Spiess (2024),
REStud 91(6); Roth (2022), AEJ: Insights 4(3), 305-322 (Vortest-Warnung); Rambachan, Roth (2023),
REStud 90(5), 2555-2591; **Kolari, Pynnoenen (2010)**, "Event Study Testing with Cross-sectional
Correlation of Abnormal Returns", RFS 23(11), 3996-4025 [sek - vom Programm in R4 1.3c bereits
zitiert]; Boehmer, Musumeci, Poulsen (1991), JFE 30(2), 253-272 (ereignis-induzierte Varianz);
Cameron, Gelbach, Miller (2008), REStat 90(3), 414-427; MacKinnon, Webb (2017) (wenige Cluster).
[Seitenzahlen [sek].]

**Uebertragung auf den Bestand.** **Treatment-Kohorte 1 (traegt das Urteil):** symbolweise
**angekuendigte** Aenderungen des Funding-Intervalls vor dem automatischen System (2025-07 bis
2025-10) plus die Batch-Ankuendigungen danach. Belegt [sek, Suchtreffer-Snippets mit Symbol und
UTC-Zeitstempel; `announcements.bybit.com` egress-gesperrt]: HYPERUSDT 2025-07-10 04:35 UTC; FUSDT
2025-10-21 08:35 UTC; MEUSDT 2025-10-27 14:05 UTC; IPUSDT (Datum nicht extrahiert); DATAUSDT
2026-07-09 10:50 UTC; Sammeltermine 2026-03-02 und "Apr 11" (Jahr nicht eindeutig). **Entscheidend:
das Treatment braucht kein Ankuendigungs-Scraping** - es ist direkt im Funding-Backfill sichtbar,
weil sich der Abstand der Funding-Zeitstempel aendert, also exakt in der WP-7-Pflichtspalte
`funding_n`; die Ankuendigungen dienen nur der Datierungskontrolle. **Kontrollgruppen, drei
Ebenen:** (i) noch nicht behandelte Bybit-Symbole; (ii) die acht dauerhaft ausgenommenen Majors;
(iii) **dasselbe Asset auf Binance**, durchgaengig 8h - die staerkste Parallel-Trend-Begruendung,
die es gibt: identischer Basiswert, dieselbe Minute, andere Boersenregel. *Ergebnis:* die
**Cross-Venue-Basis** (Bybit- gegen Binance-Perp, 1h-Klines) und die Funding-Differenz -
Praemiengroessen, horizontfrei. **Klasse: E.** *Urteilstragend genau EINE Statistik:* der
aggregierte Event-Study-ATT der Cross-Venue-Basis in [0, +7 Tage]. OI und Umsatz werden nur
berichtet.

**Struktureller Nulleffekt (C.4).** (a) 1.000 Placebo-Behandlungstermine mit **identischer
Kalenderverteilung** (Wochentag, Tageszeit, Kohortengroesse) - exakt der Klasse-E-Nulleffekt des PRD
(3.2). (b) Pre-Trends nicht als Vortest, sondern als Rambachan/Roth-Sensitivitaet ("wie stark
muessten Trends abweichen, damit der Effekt verschwindet"). (c) **Kolari/Pynnoenen:** bei
gebuendelten Terminen ist die Standard-Event-Study-Statistik nachweislich zu liberal - die
korrigierte urteilt, die unkorrigierte wird nur nachrichtlich berichtet. (d)
Boehmer/Musumeci/Poulsen gegen ereignis-induzierte Varianz (ein Intervallwechsel erhoeht plausibel
die Varianz, nicht nur den Mittelwert).

**Feasibility-Skizze.** Cluster-Einheit = **Kohorte** (alle Symbole desselben Ankuendigungstermins =
EIN Cluster; DEC-51 Punkt 3, wortgleich mit der A2-Regel "alle Symbole desselben Verfalls = ein
Cluster"). N_cluster = Zahl distinkter Ankuendigungstermine mit >= 1 Symbol - **UNGEMESSEN**,
Vorfrage V-S4-3; die Suchtreffer belegen mindestens 6 distinkte Termine fuer Intervall-Aenderungen,
die tatsaechliche Zahl ist aus `funding_n` in Minuten auszaehlbar. Vorab fixierte Kill-Regel:
**N_cluster < 20 -> GL-012.** *Zweite, konditionale Kohorte:* die **Risk-Limit-Anpassungen**, nahezu
woechentlich in Symbol-Batches angekuendigt - belegt [sek] 2025-01-08 (wirksam), 2025-10-12,
2025-10-24, 2025-11-07, 2025-11-08, 2025-11-27, 2025-12-19, 2025-12-24, 2025-12-25. Bei dieser
Frequenz ist **N_cluster >> 20/Jahr** praktisch sicher, und der Arm ist mechanisch mit X-NEXP-2
verknuepft, weil eine MMR-Aenderung ueber `Cap = min((IMR-MMR)*k, MMR)` **den RD-Cutoff
verschiebt**. **Aber:** er ist historisch nicht aus dem Bestand rekonstruierbar - das taegliche
Point-in-Time-Instrument-Roster ist genau der Strom, den PRD 7.2 als Prioritaet 1 und
"grundsaetzlich nicht nachholbar" fuehrt und der noch nicht gesammelt wird; ohne ihn braucht der Arm
Ankuendigungs-Scraping, das PRD 4.1 (B3) ausdruecklich nicht zur Welle-1-Aufgabe erklaert.
Konsequenz: Arm 1 sofort laufbereit, Arm 2 als vorab fixierte Erweiterung, nicht als Teil des
Urteils. *Effektgroesse:* **UNBELEGT**; Schwelle aus der Placebo-Verteilung. *REZENZ:* Kohorte 1
liegt vollstaendig in W2 - das juengste Regime ist urteilstragend, aeltere Termine gibt es nicht.

**Rechenbudget.** Zusatz-Backfill Binance: 1h-Klines (limit 1500) = 12 Calls/Symbol,
Funding-Historie (limit 1000, 8h) = 3 Calls/Symbol; bei 100 Symbolen **1.500 Calls, wenige
Minuten**, < 200 MB. Rechnen: ATT(g,t) + Wild-Cluster-Bootstrap 10.000 Replikate: **CPU, < 30 min.**
**GPU: 0.** **Scope-Hinweis, ehrlich markiert:** PRD 7.1 listet nur Bybit-Klines, Bybit-Funding und
Deribit-DVOL als Backfill. Binance-Klines und Binance-Funding sind ebenso oeffentlich und keyfrei,
stehen aber **nicht** in der Tabelle. Das ist eine Orchestrator-Entscheidung, keine
Scout-Entscheidung; ohne sie laeuft der Vorschlag mit den Kontrollebenen (i) und (ii) statt (iii)
weiter, verliert aber sein staerkstes Argument.

**Nicht-Duplikat-Nachweis.** Naechste Nachbarn **H-12** (Fragmentierungs- matrix, DROP) und
**H-23/H-17** (Venue-Fingerprint, WEITER): beide beschreiben die **Struktur** der
Cross-Venue-Beziehung (Eigenmodus bzw. Klassifizierbarkeit), X-NEXP-3 schaetzt einen
**Behandlungseffekt** auf die Cross-Venue-Basis. Die dort gebauten Loader (inkl. Deribit-Umbenennung
und der zwei `publicTrade`-Dialekte) sind wiederverwendbar - Kostenvorteil, nicht Duplikat. Zu
**H-01**: dort war die Funding-*Uhr* das Signal, hier ist die *Aenderung des Uhrentakts* das
Treatment.

**Entscheidungsrelevanz.** *PASS:* Eine reine Regel-/Buchungsaenderung des Betreibers bewegt die
Cross-Venue-Basis kausal - damit ist erstmals im Programm ein Ereignis-Mechanismus **kausal**
nachgewiesen (was A2 nicht kann, weil A2 bis V-5 ein GL-012-Fall ist), und die
Kolari/Pynnoenen-korrigierte Maschinerie steht fuer A2 fertig bereit. *DROP:* Regeleingriffe dieser
Art sind fuer die Praemienstruktur folgenlos - dann darf A1 `funding_n` als reine Normierungsspalte
behandeln, und der Risk-Limit-Arm muss nicht gebaut werden.

**Fixture-Paar.** *Positiv:* Panel mit gestaffelter Behandlung und **kohortenabhaengigem** Effekt,
konstruiert so, dass TWFE das falsche Vorzeichen liefert und Callaway/Sant'Anna nicht - beide Zahlen
werden im Test gepinnt (das ist zugleich die Positivkontrolle der Maschinerie, C.13). *Negativ:*
gestaffelte Behandlung mit Effekt null, aber kohortenspezifischen Trends - die
Rambachan/Roth-Sensitivitaet MUSS den Befund als nicht robust ausweisen. *Adversarial:* alle
Kohorten am selben Kalendertag mit stark korrelierten Einheiten - die unkorrigierte
Event-Study-Statistik MUSS ueberverwerfen, die Kolari/Pynnoenen-Statistik nicht.

**Risiko-Etikett: Blick wert** (Arm 1) / **Enabler, data-gated** (Arm 2).

---

### X-NEXP-4 - Instrumentvariable: der Verfallstakt als Instrument fuer mechanischen Fluss - der kausale Impact-Koeffizient

**Methode.** Zweistufige Kleinste-Quadrate-Schaetzung. Endogener Regressor: der Netto-Taker-Fluss im
Settlement-Fenster [07:30, 08:00) UTC. Instrument: der **Options-Verfallskalender** (Deribit), also
ein rein kalendarisch exogener Indikator. Ergebnis: die Perp-Log-Rendite im selben Fenster. Der
2SLS-Koeffizient ist ein **kausaler Preisimpact je Einheit Fluss** (ein Kyle-Lambda), identifiziert
aus **uninformiertem, mechanisch getaktetem** Fluss - im Gegensatz zum OLS-Koeffizienten, der
informierten und uninformierten Fluss vermischt. Der Vergleich lambda_2SLS gegen lambda_OLS ist ein
Hausman-artiger Test darauf, wieviel der gemessenen Fluss-Preis-Beziehung Information und wieviel
Impact ist. *Primaerliteratur:* Imbens, Angrist (1994), Econometrica 62(2), 467-475 (LATE); Lee,
McCrary, Moreira, Porter (2022), "Valid t-ratio Inference for IV", **AER 112(10), 3260-3290**
(tF-Korrektur - ersetzt die Faustregel F > 10); Anderson-Rubin-Inferenz fuer schwache Instrumente;
Kolari, Pynnoenen (2010) fuer die Cluster-Inferenz auf gebuendelten Verfallsterminen. [Seitenzahlen
[sek].]

**Uebertragung auf den Bestand.** Strom: `bybit/publicTrade` BTC/ETH (lueckenlos ab 2020-03-25,
B.16) fuer Fluss und Rendite - **kein Nachladen**; Verfallskalender aus der Deribit-Konvention
(Freitag 08:00 UTC), dessen Bestand und Beginn **UNBELEGT** und exakt Gegenstand der bestehenden
Vorfrage **V-5(a)** sind. Aufloesung 1-Minute, aggregiert auf das 30-Minuten-Fenster. Horizont 30
Minuten - **ausschliesslich Kosten-/Struktur-Messung** (Randbedingung 3), nie eine Kante; Ergebnis
ist eine `tradability3`-Konstante, kein Signal. **Klasse: X (Enabler-Messung).** *Urteilstragend
genau EINE Statistik:* `lambda_2SLS` mit Anderson-Rubin-CI. Das erste Stadium (Verfall -> Fluss) und
`lambda_OLS` werden berichtet.

**Struktureller Nulleffekt (C.4).** (a) Placebo-Instrumente: Nicht-Verfalls-Freitage 08:00 UTC (A2s
P1) und Nicht-Freitags-08:00-Slots (A2s P2, zwingend wegen des Funding-Settlements) - dort MUSS das
erste Stadium schwach und lambda_2SLS undefiniert sein. (b) Negativ-Panel aus Realdaten: XRP/BNB
ohne liquide Optionskette - dort MUSS das erste Stadium verschwinden; harter Relevanztest, kostet
nichts. (c) Nulleffekt von lambda: auf einem Random Walk mit exogenem Fluss ist lambda = 0, bei
*endogenem* Fluss ist lambda_OLS > 0 und lambda_2SLS = 0 - genau diese Trennung ist der Zweck. (d)
**Schwache-Instrumente-Null:** die 2SLS-t-Statistik ist bei schwachem Instrument massiv verzerrt,
deshalb tF/Anderson-Rubin; ohne diesen Schritt waere der Vorschlag ein L-2-Wiedergaenger in neuer
Metrik.

**Feasibility-Skizze.** Cluster: **das Verfallsereignis ueber beide Symbole** (wie A2, DEC-51 Punkt
3). N_cluster = 52 je Fenster, falls V-5(a) woechentliche Verfaelle belegt; nur 12 je Fenster bei
reinen Monatsverfaellen. Vorab fixierte Kill-Regel: **belegt V-5(a) keine woechentlichen Verfaelle,
ist N_cluster = 12 < 20 je Fenster -> GL-012, keine Registrierung** (nicht: gepoolt auf 24
ausweichen; das waere Torpfostenverschiebung). Bei 52 Clustern und rho(BTC,ETH) = 0,8 [sek, in WP-7
zu messen] ist N_eff = 52*2/1,8 = 57,8 - dieselbe Arithmetik wie A2 Variante (a). *Effektgroesse:*
das **erste Stadium** ist aus dem Bestand vormessbar (Fluss-Spitze am Verfall gegen Nicht-Verfall,
Minuten); fuer lambda gibt es eine **programminterne** Referenz - H-24s gleichzeitiger IC +0,53 bis
+0,61 (B.14). Registrierbare A-priori: lambda_2SLS liegt zwischen 0 und dem aus B.14 implizierten
OLS-Wert, und urteilstragend ist, ob das AR-CI den OLS-Wert **ausschliesst**. Eine aus
Programm-Konstanten hergeleitete Schwelle, kein importierter Skalar. *REZENZ:* beide Fenster in
W1/W2; publicTrade deckt sie vollstaendig ab.

**Rechenbudget.** Kein Backfill. Fluss-Aggregation aus dem WP-0-Bar-Cache bzw. `publicTrade`: **CPU,
Minuten**; 2SLS + AR-Grid + Block-Bootstrap: Minuten. **GPU: 0.**

**Nicht-Duplikat-Nachweis.** Naechster Nachbar **H-24** (D.14): H-24 hat den **korrelativen** IC
gemessen und ist DROP fuer die Fortsetzungsthese. X-NEXP-4 wiederholt weder die Fortsetzungsfrage
noch den Forward-IC, sondern schaetzt den **gleichzeitigen** Koeffizienten kausal und fragt, ob B.14
Impact oder Information ist. Zweiter Nachbar **A2/EXP-CLOCK**: A2 misst die reduzierte Form (CAR),
X-NEXP-4 zerlegt sie in erstes Stadium x lambda - und **lebt auch dann, wenn A2s reduzierte Form
null ist** (starkes erstes Stadium bei nullem reduzierten Effekt heisst lambda ~ 0, was mit B.14
vereinbar und selbst ein Befund ist). Dritter Nachbar **R3-K-32/GEX-KOND**, in 9.1 gestrichen weil
es einen neuen Harvester-Strom braucht - X-NEXP-4 braucht keinen.

**Entscheidungsrelevanz.** *PASS (lambda_2SLS << lambda_OLS):* der gemessene
Fluss-Preis-Zusammenhang ist ueberwiegend Information, nicht Impact - die Slippage-Komponente der
15-bp-Wand ist fuer *unseren* (uninformierten) Fluss zu hoch angesetzt, und
`tradability3/constants.py` bekommt erstmals einen **gemessenen** Impact-Parameter. *PASS
(lambda_2SLS ~ lambda_OLS):* der Impact ist echt auch fuer uninformierten Fluss - die Wand steht,
und jede kuenftige Kapazitaetsrechnung hat einen Beleg. *DROP (erstes Stadium schwach):* der
Verfallstakt erzeugt auf Bybit-Perps keinen messbaren mechanischen Fluss - ein **direkter
Vorab-Befund gegen A2**, billiger als A2 selbst, der A2s Mechanismus-Erzaehlung untergraebt, bevor
ein Alpha-Slot verbraucht wird.

**Fixture-Paar.** *Positiv:* synthetischer Tape mit injizierten Fluss-Spitzen an bekannten
Verfallsterminen und bekanntem lambda - 2SLS muss lambda im AR-CI wiederfinden. *Negativ:* dieselben
Termine ohne Fluss-Spitze - erstes Stadium schwach, AR-CI muss die ganze reelle Achse abdecken (und
darf **nicht** still eine Punktschaetzung ausweisen; Loud-Fail, C.14). *Adversarial:*
Verfallstermine, die zugleich einen Informationsschock tragen (Exklusionsverletzung) - der
2SLS-Schaetzer MUSS sichtbar vom wahren lambda abweichen, und das Negativ-Panel XRP/BNB MUSS die
Verletzung anzeigen.

**Risiko-Etikett: spekulativ** - die Exklusionsrestriktion ("der Verfall wirkt NUR ueber den Fluss")
ist nicht beweisbar, nur plausibilisierbar. Sie ist die einzige Annahme in diesem Dokument, die
nicht aus einer publizierten Boersenregel folgt.

---

## 3. Rangliste

| Rang | ID | Warum dort | Etikett |
|---|---|---|---|
| **1** | **X-NEXP-2** (Diff-in-Disc, Funding-Kappe -> 1h-Wechsel) | Sauberste Identifikation im Feld: deterministische, oeffentlich dokumentierte Zuweisungsregel; der Vor-Reform-Zeitraum liefert den empirischen Nulleffekt gratis; betreiberdefinierter Kontrollarm (8 ausgenommene Majors); **null zusaetzlicher Backfill** ueber den ohnehin geplanten A1-Funding-Backfill hinaus; und die hoechste Entscheidungsrelevanz des Dokuments (mechanischer Selektionseffekt auf A1s Sortierschluessel). Einziges echtes Risiko: N_eff. | Blick wert |
| **2** | **X-NEXP-1** (RKD an der Funding-Klemme) | Analytisch bekanntes erstes Stadium, riesiger oekonomischer Hebel am Knick (Verdopplung der annualisierten Carry je bp), N_cluster gross. Rang 2 statt 1, weil RKD-Schaetzer nachweislich fragil sind (Ganong/Jaeger) und die Historientiefe von `premium-index-price-kline` UNBELEGT ist. Liefert nebenbei den **Totzonen-Zensus**, eine A1-Feasibility-Zahl, die im PRD fehlt. | Blick wert |
| **3** | **X-NEXP-3** (gestaffelte DiD, Cross-Venue-Kontrolle) | Identifikation stuetzt sich auf Parallel-Trends statt auf eine Regel - eine Stufe schwaecher, aber durch die Same-Asset-Cross-Venue-Kontrolle sehr stark gestuetzt. Bringt dem Programm die Kolari/Pynnoenen-korrekte Event-Study-Maschinerie, die A2 spaeter braucht. Rang 3 wegen des Binance-Backfills (PRD-7.1-Scope) und der ungemessenen Kohortenzahl. | Blick wert / Enabler |
| **4** | **X-NEXP-4** (IV, Verfallstakt -> Fluss -> lambda) | Einzige echte kausale Lesart der Programm-Konstante B.14 und der einzige Weg zu einem **gemessenen** Impact-Parameter fuer `tradability3`. Rang 4, weil die Exklusionsrestriktion nicht aus einer Boersenregel folgt und weil die Registrierbarkeit an V-5(a) haengt. | spekulativ |

**Gemeinsame Vorfragen (im 10-Minuten-Format von PRD 4.4, alle auf der Nutzer-Maschine wegen der
Egress-Sperre):**
- **V-S4-1:** Historientiefe von `/v5/market/premium-index-price-kline`
  (category=linear, interval=60), BTCUSDT rueckwaerts paginieren bis zur
  ersten leeren Antwort, dann Stichprobe ueber 20 Alt-Symbole. Reicht sie
  nicht ueber beide REZENZ-Fenster: X-NEXP-1 tot, X-NEXP-2 nur mit
  approximierter Laufvariablen (dann **nicht** registrierbar).
- **V-S4-2:** Zahl der Kalendertage mit >= 1 Kappen-Treffer im Fenster
  2025-11-03..2026-08-31 und das **gemessene** rho zwischen Tagen; direkt aus
  dem A1-Funding-Backfill. N_eff < 20 -> X-NEXP-2 ist GL-012.
- **V-S4-3:** Zahl distinkter Termine, an denen sich `funding_n` fuer >= 1
  Symbol aendert (2025-07-01..2026-08-31). < 20 -> X-NEXP-3 Arm 1 ist GL-012.
- **Erweiterung der bestehenden Vorfrage V-1 (empfohlen, kostet nichts):**
  V-1 fragt bereits, ob der Zins-Term `I` ueber Kontraktklassen identisch ist
  und vermerkt `I` fuer 1h-Symbole als UNBELEGT. **Zusaetzlich zu erheben:
  die clamp-Grenze (+/-0,05 %) und die Cap-Formel-Konstante k fuer Symbole mit
  Nicht-8h-Intervall.** Ohne diese Werte sind die Knickpunkte fuer 1h-Symbole
  unbekannt, und X-NEXP-1/2 muessen sie ausschliessen.

---

## 4. NICHT vorgeschlagen - und warum (Pflichtabschnitt)

**1. Synthetic Control fuer den Bybit-Hack (2025-02-21, ~1,5 Mrd USD, [sek]).** Das sauberste
Bybit-spezifische Exogenitaetsereignis der Historie, im Fenster W1 - und trotzdem **nicht
vorgeschlagen**, aus einem strukturellen A-priori-Grund im Stil von GL-012/H-07, der keinen
Datenlauf braucht: die Inferenz von Abadie/Diamond/Hainmueller laeuft ueber In-Space-Placebos, und
der kleinste erreichbare Permutations-p-Wert ist `1/(J+1)` mit J Spendereinheiten. Der Spenderpool
auf Boersenebene ist Binance, Deribit, BitMEX - **J = 3, also p_min = 0,25 > 0,05**. Der Ausweg
"Spender auf Symbolebene" hilft nicht, weil alle Spender **denselben Ereignistag** teilen und ihre
Abweichungen damit querschnittlich korreliert sind (der Kolari/Pynnoenen-Fall). N_cluster = 1: ein
Einzelereignis-Synthetic-Control kann in diesem Programm kein Gate bestehen, und es zu registrieren
hiesse, eine strukturell unerreichbare Schwelle zu setzen.

**2. Der Bybit-Derivate-Gebuehrenwechsel vom 2026-09-01 10:00 UTC** [sek: Bybit-Announcement ueber
Suchtreffer; Altcoin-Maker-Gebuehr auf 0 % ueber alle Pro-Stufen, Taker sinkt fuer Altcoin/TradFi,
**G1-Majors (BTC/ETH/SOL/XRP USDT) unveraendert**, VIP-Retail unveraendert]. Als DiD waere die
Struktur ideal (klarer behandelter Arm, klarer Kontrollarm). Nicht vorgeschlagen, weil (a) das
Ereignis **zwei Tage alt** ist und keine Nachperiode existiert, (b) N_cluster = 1, (c) die
Behandlungsintensitaet an der unbeobachtbaren Gebuehrenstufe des einzelnen Haendlers haengt. **Zwei
Hinweise, die trotzdem sofort relevant sind:**
- Das ist die einzige Situation, in der dieses Programm je ein **echtes
  ex-ante-Design** haben koennte: eine Vorregistrierung, die **heute**
  geschrieben und vor Anfall der Nachperiode eingefroren wird. Wenn der
  Orchestrator das will, ist jetzt der Zeitpunkt - in drei Monaten nicht mehr.
- Unabhaengig davon: **B.3/DEC-42 (`FEE_MAKER` 2,0 bp, `FEE_TAKER` 5,5 bp)
  koennte fuer die Altcoin-Gruppe seit 2026-09-01 veraltet sein.** Die
  Altcoin-Gruppe ist genau das Universum, in dem A1 und A3 handeln wuerden.
  Der Snippet sagt "Pro levels" und "VIP retail pricing remains unchanged",
  also ist die Einzelbetreiber-Konstante vermutlich unberuehrt - aber
  "vermutlich" ist unter Belegregel kein Status. Das ist eine
  Konstanten-Pruefung fuer `tradability3` (V-4-Nachbarschaft), keine Hypothese.

**3. Ein neuer Bunching-Vorschlag an irgendeiner Kante.** D.8 ist tot, und keiner der vier
Vorschlaege reaktiviert ihn. Die Excess-Mass-Maschinerie (Saez 2010; Chetty et al. 2011; Kleven
2016) kommt hier **nur als Manipulationstest** vor, also mit umgekehrter Erwartung. Der Massenpunkt
bei F = 0,01 % ist mechanische Zensierung, kein Bunching.

**4. RDD direkt an den Risk-Limit-Tier-Kanten.** Die naheliegendste RDD-Uebertragung - und die
falsche. Die Laufvariable waere das **Positions**-Notional; der Bestand enthaelt Trades, keine
Positionen. Was messbar waere, ist die Order-Notional-Verteilung - und das **ist** H-09 unter
anderem Namen. Explizit ausgeschlossen.

**5. DiD auf Bybit-Listings/Delistings.** Der Zeitpunkt einer Listung waehlt die Boerse in Reaktion
auf Aufmerksamkeit und Momentum des Assets. Parallele Trends sind nicht verteidigbar, und Roth
(2022) zeigt, dass ein bestandener Pre-Trend-Test die Verzerrung eher verschleiert als ausschliesst.
Ohne ein Instrument fuer den Listungszeitpunkt - das wir nicht haben - ist das keine saubere
Identifikation, sondern eine Korrelation mit DiD-Etikett.

**6. DiD auf Bybit-Wartungsfenstern / Ausfaellen.** Reizvoll, weil ein Tape-Gap bei gleichzeitig
aktivem Binance-Tape die Behandlung **ohne jedes Scraping** aus dem Bestand markiert und weil PRD
3.3.9(c) eine Venue-Ereignis-Zahl verlangt, die heute frei gesetzt ist (1 %/Jahr). Nicht als
kausaler Vorschlag aufgenommen, weil (a) geplante Fenster in erwartete Ruhephasen fallen (endogene
Terminwahl) und ungeplante Ausfaelle in Stressminuten (endogen zum Ergebnis), und (b) die
verwertbare Groesse eine **Verteilung** ist, kein Behandlungseffekt - deskriptiv zustaendig ist
bereits WP-10(A). **Empfehlung ohne Registrierungsanspruch:** der Tape-Gap-Zensus (Bybit-Luecken bei
aktivem Binance-Tape, 5 Symbole, 6 Jahre) kostet Minuten und liefert WP-10(A) die dort fehlende Zahl
- ein Zensus-Nachtrag, keine Hypothese ("billig ist kein Registrierungsgrund", DEC-38).

**7. IV mit verfallendem Open Interest als Instrumentstaerke-Variable.** Die oekonomisch richtige
Instrumentvariante waere die *Groesse* des verfallenden OI, nicht der blosse Verfallsindikator.
`deribit/tickers` hat ~38 Tage, `markprice.options` 43 Tage (F.1) - das deckt kein REZENZ-Fenster
ab. Das ist dieselbe N-Falle wie H-10/H-13, und sie wird nicht wiederholt. X-NEXP-4 laeuft deshalb
mit dem binaeren Kalender-Instrument und sagt das offen.

**8. RDD auf dem Zins-Term I.** I ist nach Doku ueber Zeit und Symbole konstant (0,01 %/8h) - ohne
Variation gibt es keine Diskontinuitaet auszunutzen. Sollte V-1 belegen, dass I je Kontraktklasse
**verschieden** ist (das PRD haelt das ausdruecklich fuer moeglich, Review R1-R4 3.2), entstuende
eine Grenze zwischen Kontraktklassen, an der ein RDD moeglich waere - allerdings ist die
Klassenzugehoerigkeit nicht auf einer stetigen Laufvariablen angeordnet, sondern kategorial. Ein RDD
gibt es dort nicht; eine DiD nach einer Aenderung von I gaebe es. Kein solcher Aenderungstermin ist
belegt. Vertagt bis V-1.

**9. Regression Discontinuity in Time auf den Reformtermin 2025-10-30 allein.** Als eigenstaendiges
Design (Hausman/Rapson 2018) nicht vorgeschlagen: eine scharfe Zeitgrenze ohne
Querschnitts-Kontrolle konfundiert mit allem, was am selben Tag geschah, und N_cluster = 1. Der
Reformtermin wird ausschliesslich als **zweite Dimension** in X-NEXP-2 verwendet, wo er durch den
Cutoff-Querschnitt identifiziert ist.

---

## 5. Belegstatus

| Aussage / Zahl | Status | Quelle |
|---|---|---|
| `F = P + clamp(I - P, +/-0,05 %)`, `I = 0,01 %/8h` | **[sek]** | Bybit Help Center "Introduction to Funding Rate" / Bybit Learn, ueber Suchtreffer; `bybit.com` egress-gesperrt. Kompatibel mit PRD 9.2 (R1 0.2 [sek]) |
| Totzone `P in [-0,04 %; +0,06 %]`, `dF/dP` springt 0 -> 1 | **hergeleitet** (nachrechenbar), zusaetzlich [sek] bestaetigt | eigene Auflloesung der clamp-Faelle; Suchtreffer-Text nennt dieselben Grenzen |
| 10,95 % p.a. bei P = 0,06 %; 21,90 % p.a. bei P = 0,07 % | **hergeleitet** | `0,01 % * 3 * 365 = 10,95 %`; `0,02 % * 3 * 365 = 21,90 %` |
| `Cap = +/- min((IMR-MMR)*k, MMR)`, `k = 0,75` dynamisch in [0,5; 1,0], niedrigste Tier-Stufe | **[sek]** | Bybit Help Center ueber Suchtreffer |
| Cap-Beispiel 0,375 % (IMR 1,0 %, MMR 0,5 %) | **[sek] / illustrativ** | Formel + typische Tier-Werte; die tatsaechlichen IMR/MMR je Symbol sind aus `instruments-info` zu ziehen |
| Automatischer Wechsel auf 1h-Abrechnung bei Cap-Treffer; live 2025-10-30 08:00 UTC, Vollausrollung 2025-11-03 06:00 UTC | **[sek]** | PRNewswire / Chainwire / CryptoTimes / crypto-economy, alle 2025-10-29, ueber Suchtreffer; Primaer-Announcement egress-gesperrt |
| Ausnahmeliste BTCUSDT, BTCUSDC, BTCUSD, ETHUSDT, ETHUSDC, ETHUSD, ETHBTCUSDT, ETHWUSDT | **[sek]** | dieselbe Quelle |
| Rueckkehr auf laengere Intervalle "ohne Vorankuendigung" (also diskretionaer) | **[sek]** | dieselbe Quelle - Grund, warum nur der Einschaltvorgang registriert wird |
| Symbolweise Intervall-Ankuendigungen: HYPERUSDT 2025-07-10 04:35 UTC; FUSDT 2025-10-21 08:35 UTC; MEUSDT 2025-10-27 14:05 UTC; DATAUSDT 2026-07-09 10:50 UTC; Sammelankuendigungen 2026-03-02 und "Apr 11" | **[sek]** | announcements.bybit.com ueber Suchtreffer-Snippets; Seiten egress-gesperrt. IPUSDT-Datum **nicht extrahiert** |
| Risk-Limit-Anpassungen 2025-01-08 (wirksam), 2025-10-12, 2025-10-24, 2025-11-07, 2025-11-08, 2025-11-27, 2025-12-19, 2025-12-24, 2025-12-25 | **[sek]** | announcements.bybit.com ueber Suchtreffer; Inhalte (betroffene Symbole, alte/neue MMR) **nicht verifiziert** |
| Bybit-Hack 2025-02-21, ~1,5 Mrd USD | **[sek]** | TRM Labs, Chainalysis, CSIS, DL News ueber Suchtreffer |
| Gebuehrenaenderung wirksam 2026-09-01 10:00 UTC; Altcoin-Maker 0 % (Pro), G1-Majors und VIP-Retail unveraendert | **[sek]** | Bybit-Announcement ueber Suchtreffer; Primaerseite egress-gesperrt |
| `/v5/market/premium-index-price-kline`, category=linear, limit bis 1000 | **[sek]** | Bybit-API-Doku / pybit / bybit-api ueber Suchtreffer; `bybit-exchange.github.io` egress-gesperrt |
| Historientiefe von `premium-index-price-kline` | **UNBELEGT** | Vorfrage V-S4-1 |
| Zahl der Kappen-Treffer-Tage, rho zwischen Tagen, Zahl der Intervall-Wechsel-Termine | **UNGEMESSEN** | Vorfragen V-S4-2 / V-S4-3 |
| `I` und clamp-Grenze fuer Nicht-8h-Intervalle | **UNBELEGT** | Erweiterung von V-1 |
| Card/Lee/Pei/Weber 2015, Econometrica 83(6), 2453-2483 | verifiziert (Abstract/Verlagsseite) | Suchtreffer |
| Ganong/Jaeger 2018, JASA 113(522), 494-504 | verifiziert (Abstract/Verlagsseite) | Suchtreffer |
| Callaway/Sant'Anna 2021, J. Econometrics 225(2), 200-230 | verifiziert (RePEc/ScienceDirect) | Suchtreffer |
| Alle uebrigen Literaturangaben (Grembi et al., Sun/Abraham, de Chaisemartin/D'Haultfoeuille, Borusyak et al., Roth, Rambachan/Roth, Kolari/Pynnoenen, Boehmer et al., Calonico et al., Cattaneo/Jansson/Ma, Kolesar/Rothe, McCrary, Lee/Card, Imbens/Angrist, Lee et al. 2022, Politis/Romano, Cameron et al., MacKinnon/Webb, Abadie et al., Saez, Chetty et al., Kleven, Hausman/Rapson) | **[sek]** | aus Fachkenntnis zitiert, Volltexte egress-gesperrt; Jahrgang/Venue nach bestem Wissen, Seitenzahlen nicht einzeln primaerverifiziert |

**Egress-Vermerk (PRD 4, Laufort).** `bybit.com`, `announcements.bybit.com`, `api.bybit.com` und
`bybit-exchange.github.io` sind vom Proxy dieser Sandbox geblockt; ein direkter WebFetch auf eine
Risk-Limit-Ankuendigung wurde mit `EGRESS_BLOCKED` abgewiesen. Alle Boersen-Fakten oben stammen
daher aus Suchtreffer-Snippets und sind konsequent `[sek]`. Jede Registrierung muss sie auf der
Nutzer-Maschine gegen die Primaerquelle pruefen - insbesondere die clamp-Grenze, die Cap-Formel und
die Ausnahmeliste, weil an ihnen die Cutoff-Definitionen haengen.

---

*Ende S4_NATUERLICHE_EXPERIMENTE.md*
