# R2 -- Tages- bis Wochen-Horizont: Faktoren, bei denen die 11-15-bps-Wand zur Fussnote wird

> Quant-Researcher R2, Scinance-3.0-Programm, Phase 3. Erstellt 2026-09-02.
> Gelesen: `ERKENNTNIS_KOMPENDIUM.md` (vollstaendig, A-F), `INFRA_OPS_MAP.md` Abschnitt 1/Abschnitt 2/Abschnitt 6,
> `FINAL_PRD.md` Abschnitt 1/Abschnitt 2/Abschnitt 5/Abschnitt 8. Read-only auf das Repo.
> Netzzugang: WebSearch verfuegbar, WebFetch fuer die meisten Wissenschafts-Hosts
> (nber.org, link.springer.com, arxiv.org, acfr.aut.ac.nz, osuva.uwasa.fi) und fuer
> `api.bybit.com` / `bybit-exchange.github.io` durch den Egress-Proxy GEBLOCKT.
> Alle Literaturzahlen unten stammen daher aus Suchmaschinen-Zusammenfassungen der
> Primaerquellen, nicht aus dem Volltext -- sie sind durchgehend als
> **[sek]** (Sekundaerquelle, nicht primaer verifiziert) markiert. Alles ohne
> Quellenmarkierung und ohne Rechenweg ist **unbelegt**.

---

## 0. Vorbemerkung: die eigentliche Erkenntnis dieses Auftrags

Der Auftragstitel unterstellt, der Hebel gegen die Friktionswand sei der **Horizont**.
Das ist nur zur Haelfte richtig. Die Rechnung zeigt: der Horizont senkt die Kosten
pro Zeiteinheit, aber er **zerstoert gleichzeitig die statistische Power**, und zwar
schneller, als er die Kosten senkt. Der eigentliche Hebel ist die **Breite (K)** des
Universums. Das ist die zentrale, quantitative Aussage dieses Dokuments, und sie
faellt genau mit der strukturellen Schwaeche zusammen, an der H-07/H-08 gestorben
sind (Kompendium D.7, GL-012: max|z| = sqrt(N-1) = 2,0 bei N=5).

### 0.1 Die Friktionsrechnung auf Wochenhorizont

Round-Trip 15 bps inkl. Slippage (Programm-Konstante B.1), ein Rebalance pro Woche:

| Turnover/Woche (Anteil ersetzter Positionen) | Kosten bei 2x Brutto-Exposure | Kosten p.a. |
|---|---|---|
| 0,2 | 6,0 bps/Woche | 3,13 % |
| 0,4 | 12,0 bps/Woche | 6,26 % |
| 0,6 | 18,0 bps/Woche | 9,39 % |
| 0,8 | 24,0 bps/Woche | 12,52 % |
| 1,0 (voller Umschlag) | 30,0 bps/Woche | 15,65 % |

Ein 1-4-Wochen-Momentum-Signal hat typisch 0,5-0,7 Turnover/Woche, also
**~18 bps/Woche = ~9,4 % p.a.** Das ist die Wand auf diesem Horizont. Sie ist
absolut betrachtet gross -- aber sie ist relativ zur **Querschnitts-Dispersion**
klein, und das ist der Unterschied zu allen bisherigen Programm-Befunden.

### 0.2 Warum die Wand zur Fussnote wird -- Dispersion statt Horizont

Auf Minutenskala war die gemessene Rohkante 0,03-0,19 bps gegen 15 bps Wand
(Faktor 80-500 **darunter**, H-04b/H-05c). Auf Wochenskala im **breiten**
Perp-Universum kehrt sich das Verhaeltnis um. Die Bruttorendite eines
Dezil-Long-Short-Portfolios laesst sich naeherungsweise schreiben als
`R_LS ~= 2,0 * IC * sigma_xs` (Dezil-Spreadfaktor ~2,0 unter Normal-Approximation;
`sigma_xs` = wochenweise Querschnitts-Streuung der Renditen):

| sigma_xs (bps/Woche) | IC=0,02 | IC=0,03 | IC=0,05 | Kosten (Turnover 0,6, 2x) |
|---|---|---|---|---|
| 400 (Majors-artig) | 16 bps | 24 bps | 40 bps | 18 bps |
| 800 | 32 bps | 48 bps | 80 bps | 18 bps |
| 1200 (Alt-Perps, plausibel) | 48 bps | 72 bps | 120 bps | 18 bps |
| 1600 | 64 bps | 96 bps | 160 bps | 18 bps |

`sigma_xs` ist die zu messende Groesse (V-0 unten); die Werte 1200-1600 bps/Woche
fuer ein Alt-Perp-Universum sind **unbelegt** und explizit Messauftrag, nicht
Annahme. Aber die Struktur der Rechnung ist robust: sobald `sigma_xs` in die
Groessenordnung 1000 bps/Woche kommt, ist eine Wand von 18 bps **1,5 % der
Dispersion** statt der 12.500 %, die sie auf Minutenskala war. Genau das ist
gemeint mit "die Wand wird zur Fussnote". Sie wird es nicht durch den Horizont
allein, sondern durch **Horizont x Dispersion x Breite**.

### 0.3 Die Power-Rechnung (Pflichtteil, GL-012-Check fuer alles Weitere)

Alle folgenden Zahlen: 80 % Power, alpha = 0,05 zweiseitig, also |t| >= 2,802.

**(A) Ein-Serien-Fall (Time-Series-Momentum, Markt-Timing, Kalendereffekte auf
Aggregatebene).** Der t-Wert einer mittleren Rendite ist `t ~= SR_ann * sqrt(T_Jahre)`.

| T | minimal detektierbarer annualisierter Sharpe |
|---|---|
| 3 a | 1,62 |
| 4 a | 1,40 |
| 5 a | 1,25 |
| 5,5 a | **1,20** |
| 6 a | 1,14 |

Die 5 Symbole helfen dabei **fast nicht**: bei einer durchschnittlichen paarweisen
Wochenrendite-Korrelation `rho_bar` ist die effektive Zahl unabhaengiger Serien
`K/(1+(K-1)*rho_bar)`:

| rho_bar | N_eff bei K=5 | detektierbarer SR (5,5 a) |
|---|---|---|
| 0,6 | 1,47 | 0,99 |
| 0,7 | 1,32 | 1,04 |
| 0,8 | 1,19 | **1,10** |
| 0,9 | 1,09 | 1,15 |

BTC/ETH/SOL/BNB/XRP-Wochenrenditen liegen erfahrungsgemaess bei rho_bar 0,7-0,85
(**unbelegt**, in V-0 zu messen). **Das ganze 5-Symbol-Panel ist auf Wochenhorizont
statistisch ungefaehr EINE Beobachtungsserie.** 5,5 Jahre liefern 286 Wochen, also
**~340 effektiv unabhaengige Wochenbeobachtungen** -- nicht 1430.

**(B) Der REZENZ-Killer.** Kompendium C.18 (DEC-38) verlangt, dass urteilstragende
Fenster das juengste Marktregime abdecken; der D3-Uebergang endet ~Mitte 2024.
Zwei disjunkte urteilstragende Fenster nach Mitte 2024 sind also je maximal
~12 Monate = **52 Wochen**. Damit sinkt der detektierbare Sharpe je Fenster auf
`2,802/sqrt(1)` = **2,80** -- ein annualisierter Sharpe von 2,8 muss in JEDEM der
beiden Fenster erreicht werden. Kein glaubwuerdiges Krypto-Trendsignal leistet das.
**Time-Series-Momentum ist auf diesem Datenbestand unter REZENZ-Klausel strukturell
nicht urteilsfaehig.** Das ist die ehrliche Antwort auf die Kernfrage des Auftrags
und der Grund, warum K-03 unten nur mit einer Zusatzbedingung existiert.

**(C) Der Ausweg: Breite.** Fuer einen Querschnittsfaktor gilt (Fundamental Law)
`IR_je_Rebalance = IC * sqrt(K)`, annualisiert `SR = IC * sqrt(K) * sqrt(52)`.
Aequivalent und aus dem Rauschboden der Rangkorrelation hergeleitet:
`SE(Wochen-Rank-IC) = 1/sqrt(K-1)`, ueber W Wochen `SE = 1/sqrt((K-1)*W)`.
Beide Wege liefern dieselbe Feasibility-Schwelle. Minimal noetige Breite K,
damit ein Rank-IC in EINEM Urteilsfenster t >= 2,80 erreicht:

| Fensterlaenge | IC=0,02 | IC=0,03 | IC=0,04 | IC=0,05 |
|---|---|---|---|---|
| 12 Monate (W=52) | K >= 378 | K >= **169** | K >= 95 | K >= 61 |
| 18 Monate (W=78) | K >= 253 | K >= 113 | K >= 64 | K >= 41 |
| 24 Monate (W=104) | K >= 190 | K >= 85 | K >= 48 | K >= 31 |

**Feasibility-Kernaussage (GL-012-Analogie):** Bei zwei disjunkten
12-Monats-Fenstern und einem realistisch angesetzten IC von 0,03 braucht jede
Querschnittshypothese dieses Berichts **K >= ~170 gleichzeitig handelbare Perps**.
Bei K=5 waere K_min um Faktor 34 verfehlt -- dasselbe strukturelle DROP wie H-07,
nur an einer anderen Achse. **Ob K >= 170 auf Bybit ueberhaupt erreichbar ist,
ist die eine Frage, die vor jeder Registrierung beantwortet sein muss.** Das ist
V-0.

**(D) Tageshorizont, Nachweisgrenzen.** SE der mittleren Tagesrendite bei
Tagesvolatilitaet sigma, n Tagen. 5,5 Jahre = 2008 Tage.

| Serie | alle Tage (n=2008) | Wochenendtage (n=574) | Monatsende 3 T/M (n=198) | letzter Freitag (n=66) |
|---|---|---|---|---|
| BTC gerichtet (sigma=350 bps) | 21,9 bps | 40,9 bps | 69,7 bps | 120,7 bps |
| Alt gerichtet (sigma=550 bps) | 34,4 bps | 64,3 bps | 109,5 bps | 189,7 bps |
| dollarneutral L/S (sigma=120 bps) | 7,5 bps | 14,0 bps | 23,9 bps | 41,4 bps |
| dollarneutral L/S (sigma=80 bps) | 5,0 bps | 9,4 bps | 15,9 bps | 27,6 bps |

Lesart: **jeder gerichtete Kalendereffekt auf Aggregatebene ist tot, bevor er
gemessen wird.** Ein Wochenend-Werktag-Renditeunterschied muesste auf BTC
> 41 bps/Tag (= 150 % p.a.) betragen, um mit 80 % Power detektierbar zu sein.
Solche Effekte gibt es nicht; die Literatur findet fuer 2020-2024 explizit
**keinen** Wochenend-Renditeeffekt [sek: "Bitcoin's Weekend Effect: Returns,
Volatility, and Volume (2014-2024)" -- kein detektierbarer Wochenend-Werktag-Gap
in Gesamt- und Teilstichproben; niedrigere Volatilitaet/Volumen am Wochenende].
Nur die **dollarneutrale Querschnitts-Interaktion** (Spalte 3/4) hat eine
brauchbare Nachweisgrenze -- deshalb ist K-06 unten so und nicht anders gebaut.

---

### V-0 -- Vorleistung (KEIN Kandidat): Universums- und Survivorship-Zensus

Ohne V-0 ist keiner der Kandidaten K-01..K-06 registrierbar; V-0 ist die
GL-012-Feasibility-Pruefung fuer die gesamte Familie und folgt exakt dem
Programm-Muster WP-4 (Spread-Zensus: eine Frage, ein binaerer Befund, toetet
oder oeffnet eine ganze Kandidatenklasse).

**Fragen (alle binaer beantwortbar):**
1. Wie viele Bybit-Linear-Perps (USDT/USDC) hatten in **jedem** Kalendermonat der
   Fenster W1/W2 durchgehend Tagesbars? Liefert das >= 170 (Schwelle aus 0.3C)?
2. Liefert `/v5/market/instruments-info?category=linear` Zeilen mit
   `status != Trading` (also delistete/geschlossene Kontrakte), und liefert
   `/v5/market/kline` fuer ein solches Symbol noch Historie? **Unbelegt** -- 
   die Bybit-Doku ist ueber den Proxy nicht erreichbar, `api.bybit.com` ist
   geblockt. Faellt die Antwort NEIN aus, existiert kein Survivorship-freies
   Universum aus Bybit-Bordmitteln und der gesamte Querschnittsblock muss
   entweder mit einem externen Delisting-Register (Bybit-Announcement-Seiten,
   kostenlos, aber Scraping-Aufwand) oder gar nicht laufen.
3. Wie gross ist die tatsaechliche wochenweise Querschnitts-Dispersion
   `sigma_xs` (Median ueber Wochen) im Universum? Das ist die Zahl, an der
   Abschnitt 0.2 haengt.
4. Wie gross ist rho_bar (mittlere paarweise Wochenrendite-Korrelation) im
   5-Symbol-Panel und im breiten Universum? Liefert N_eff fuer alle
   Power-Rechnungen.

**Nachlade-Arithmetik** (`/v5/market/kline`, oeffentlich, keine Keys,
1000 Bars/Call [sek: Bybit-Doku ueber Suchtreffer; Ratelimit 600 Requests je
5-s-Fenster je IP [sek]]). 5,5 Jahre = 2008 Tage, K=300 Symbole, konservativ
selbstgedrosselt auf 10 req/s:

| Intervall | Bars/Symbol | Calls/Symbol | Calls gesamt | Laufzeit | Zeilen gesamt |
|---|---|---|---|---|---|
| 1d | 2.008 | 3 | 900 | 1,5 min | 0,6 Mio |
| 4h | 12.048 | 13 | 3.900 | 6,5 min | 3,6 Mio |
| 1h | 48.192 | 49 | 14.700 | **24,5 min** | 14,5 Mio |
| 15m | 192.768 | 193 | 57.900 | 96,5 min | 57,8 Mio |
| 1m | 2.891.520 | 2.892 | 867.600 | 24,1 h | 867,5 Mio |

**Empfehlung: nur 1d + 1h laden** (~26 min, ~15 Mio Zeilen, < 1 GB Parquet).
1-min fuer 300 Symbole ist ein Mehrtagesjob ohne Nutzen fuer Wochenhorizonte
und waere genau die S4/S5-Infrastrukturfalle (Kompendium D.16). Funding-Historie
zusaetzlich ueber `/v5/market/funding/history` (200 Records/Call [sek]):
5,5 a x 3/Tag = 6.023 Records = 31 Calls/Symbol, K=300 -> 9.300 Calls, ~15 min.
Ob die Funding-Historie so weit zurueckreicht: **unbelegt**, Teil der V-0-Probe.

**Survivorship-Kontrolle (verbindlicher Bauplan, gilt fuer K-01..K-06):**
- Universum wird **point-in-time** rekonstruiert: ein Symbol ist in Woche t im
  Universum, wenn es zu Wochenbeginn t bereits >= 8 Wochen Bars hat UND in
  Woche t noch handelt. Erste 8 Wochen ausgeschlossen (Listing-Pump-Artefakt).
- Ein delistetes Symbol wird **nicht** rueckwirkend entfernt, sondern bis zum
  letzten vorhandenen Bar gehalten und dann zum letzten Schlusskurs geschlossen.
  Perps werden nicht auf Null abgewickelt -- ein "-100 %"-Ansatz waere falsch und
  in die andere Richtung verzerrt.
- **Bias-Richtung (wichtig, wird oft falsch herum angenommen):** Verschwundene
  Perps sind ueberwiegend solche nach langem Drawdown und Volumenverfall. Ihr
  Fehlen macht die **Short-Seite eines Momentum-Portfolios kuenstlich gut** und
  die **Long-Seite eines Reversal-Portfolios kuenstlich gut** -- beides in
  Richtung "Kante existiert". Die Literatur bestaetigt die Richtung
  [sek: Grobys/Sandretto, "On survivor cryptocurrency momentum" -- Momentum-Praemie
  auf Ueberlebenden-Stichproben deutlich ueberzeichnet; konkrete Prozentzahl
  konnte nicht primaer verifiziert werden, Host geblockt].
- **Negativ-Fixture (DEC-39-Pflicht):** synthetisches Panel ohne jedes Signal,
  aus dem 30 % der Symbole nach einem simulierten Drawdown-Trigger geloescht
  werden. Der unkontrollierte Schaetzer muss darauf eine scheinbare
  Momentum-Praemie ausweisen, der kontrollierte nicht. Faellt dieser Test
  durch, ist die gesamte Panel-Maschinerie methodisch invalide (H-14-Muster,
  Kompendium C.13).

**Aufwand:** ~1 Personentag Code + ~40 min Download + ~1 h Rechnen. CPU-only.
**Was V-0 a priori toetet:** nichts -- V-0 kann nur die Kandidaten toeten.

---

### K-01 Querschnitts-Momentum (1-4 Wochen) auf dem breiten Bybit-Perp-Universum

- **Ertragsquelle:** Prognose (Verhaltens-/Fluss-getrieben). Underreaction auf
  langsam diffundierende Information plus Aufmerksamkeits-/Flussdynamik im
  Retail-dominierten Alt-Perp-Segment; wer zahlt: der spaet einsteigende Momentum-
  Chaser und der aus einer Verlustposition getriebene Halter. Der Mechanismus ist
  in Krypto ausserdem strukturell verstaerkt, weil Leerverkaufsbeschraenkungen
  fehlen -- jeder Perp ist symmetrisch shortbar, was den Faktor sauberer
  handelbar macht als sein Aktien-Pendant.
- **Horizont & Instrument:** Formation 1/2/4 Wochen, Halteperiode 1 Woche
  (ueberlappende Portfolios nach Jegadeesh-Titman-Muster zur Turnoverdaempfung),
  Bybit-Linear-Perps USDT, dollarneutral Dezil-Long-Short, wochentlicher
  Rebalance zu einem fixen Zeitpunkt (Vorschlag: Montag 00:00 UTC).
- **Literatur/Evidenz:**
  - Liu/Tsyvinski/Wu (2022), *Journal of Finance* 77(2):1133-1177: drei Faktoren
    (Markt, Size, Momentum) erklaeren den Krypto-Querschnitt; zehn Charakteristika
    bilden signifikante Long-Short-Strategien; Universum 1.827 Coins mit
    Marktkapitalisierung > 1 Mio USD, 2014-01 bis 2020-07, Formationsperiode
    1-4 Wochen; Momentum-Long-Short ~3 %/Woche [sek, alle Zahlen].
  - Liu/Tsyvinski (2021), *RFS*, "Risks and Returns of Cryptocurrency":
    starker Time-Series-Momentum-Effekt auf 1-4-Wochen-Horizont; 1-Wochen-
    Sortierung, oberstes Quintil 11,22 %/Woche bei SR 0,45, unterstes Quintil
    2,60 %/Woche bei SR 0,19 [sek]. **Diese Groessenordnung ist NICHT
    uebertragbar** -- sie stammt aus dem Microcap-Coin-Universum 2014-2018 mit
    Spreads von Prozentpunkten, nicht aus liquiden Perps.
  - Grobys/Sapkota (2019): auf 143 Coins, Monatsdaten 2014-2018, **kein**
    Querschnitts-Momentum [sek]. Der Widerspruch zu LTW ist ein
    Horizont-Widerspruch (Woche vs. Monat), kein Datenfehler.
  - Zerfall: "Momentum Trading in Cryptocurrencies: A Comparative Study of
    Time-Series and Cross-Sectional Strategies" (BATP): nach Mitte 2021
    stabilisiert und sinkt die kumulierte Momentum-Performance; TS-Momentum
    liefert 2022-2023 negative Jahresrenditen, die Querschnitts-Variante
    begrenzt Verluste besser (strukturell marktneutral); 2024-2025 konvergieren
    beide auf bescheiden positiv [sek].
- **Erwartete Groessenordnung vs. Friktion:** Aus Abschnitt 0.2. Bei einem
  realistisch angesetzten Rank-IC von 0,03 und `sigma_xs` = 1200 bps/Woche:
  Dezil-L/S brutto **~72 bps/Woche**, Kosten bei Turnover 0,6 und 2x Brutto
  **18 bps/Woche** -> netto ~54 bps/Woche = **~28 % p.a.** auf 2x Brutto.
  Bei `sigma_xs` = 400 bps (Majors-artiges Universum) bleiben netto 6 bps/Woche
  = 3 % p.a. -- nicht handelbar. **Die gesamte Handelbarkeit haengt an
  `sigma_xs`, und `sigma_xs` haengt an der Breite und Alt-Lastigkeit des
  Universums.** Deshalb ist V-0 Frage 3 nicht optional.
  Turnover-Daempfung ist erste Designpflicht, nicht Feintuning: Uebergang von
  Turnover 1,0 auf 0,4 spart 18 bps/Woche = 9,4 % p.a. -- mehr, als die meisten
  Signalverbesserungen bringen.
- **Daten:** Bestand reicht NICHT (5 Symbole). Nachzuladen: `/v5/market/kline`,
  `category=linear`, `interval=D` und `interval=60`, K~300 Symbole, 5,5 Jahre =
  900 + 14.700 Calls, ~26 min, ~15 Mio Zeilen, < 1 GB. Zusaetzlich
  `/v5/market/instruments-info` (Universum + Status) und, fuer die
  Delisting-Kontrolle, ggf. Bybit-Announcement-Scraping. Der WP-0-Bar-Cache
  bleibt fuer die 5 Majors die Referenz -- der neue Panel-Store wird analog
  gebaut (eigener Pfad, `SCHEMA_VERSION`, SHA-256-Sidecar, Manifest-Gate,
  Loud-Fail bei "Rohzeilen > 0, geparst = 0"; INFRA Abschnitt 2 und Abschnitt 7).
- **Rechenaufwand:** CPU-only. Panelbau ~1 h, Faktorlauf Sekunden bis Minuten,
  Block-Bootstrap mit 10.000 Ziehungen wenige Minuten. **PC-tauglich, keine GPU,
  kein Overnight-Lauf.** Das ist gegenueber H-14..H-17 (2-3 GPU-Tage bis 180 h)
  ein Kostenvorteil von drei Groessenordnungen.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Metrik:** mittlerer wochentlicher Spearman-Rank-IC zwischen
    Formationsrendite und Folgewochenrendite, ueber das point-in-time-Universum;
    plus als Nicht-Trivialitaets-Anker die Dezil-L/S-Bruttorendite.
  - **Fenster (REZENZ, DEC-38):** W1 = 2024-07-01..2025-06-30,
    W2 = 2025-07-01..2026-06-30. Beide urteilstragend, hartes
    Ein-Fenster-Abbruchkriterium (C.10). Historie vor 2024-07 ausschliesslich
    deskriptives Aera-Profil, nie urteilstragend.
  - **Rauschboden (DEC-31/33-Pflicht):** `SE(IC_Woche) = 1/sqrt(K-1)`;
    ueber W=52 Wochen `SE = 1/sqrt(51*52) = 0,0194` bei K=52,
    `0,0114` bei K=150, `0,0089` bei K=250. **Schwelle wird erst nach V-0
    gesetzt, aus dem gemessenen K**, als `IC_min = 2,802 * SE(K_gemessen)` -- 
    nicht als importierte Literaturzahl. Das ist die direkte Anwendung der
    C-14-Lehre (Kompendium D.2: importierte Schwelle ohne
    Erreichbarkeitspruefung ist wertlos).
  - **Struktureller Nulleffekt:** Der Null ist NICHT exakt 0. Ein
    gleichgewichtetes Dezil-L/S-Portfolio auf einem Universum mit starker
    Volatilitaetsdispersion hat einen strukturellen Erwartungswert aus
    (a) Volatilitaets-Drag-Differenz zwischen Long- und Short-Bein und
    (b) Rebalancing-Effekt. Dieser Null wird **vor** der Schwellenfestlegung
    empirisch bestimmt: identische Portfoliokonstruktion auf einem Panel, in dem
    die Charakteristik **innerhalb jeder Woche permutiert** ist (1.000
    Permutationen). Das Gate ist der Abstand zur Permutationsverteilung, nicht
    zur Null.
  - **Serielle Abhaengigkeit:** Wochen-ICs eines persistenten Signals sind
    autokorreliert. p-Werte ueber stationaeren Block-Bootstrap (Blocklaenge
    4-8 Wochen), nie ueber iid-t.
  - **FDR-Familie:** F-XSEC1 = {K-01 (3 Formationslaengen), K-04, K-05},
    Benjamini-Hochberg alpha=0,10 innerhalb der Familie; zweite, uebergeordnete
    BH ueber die gepoolten Survivor der gesamten Welle (DEC-22, Kompendium C.16).
  - **Fixtures (DEC-39):** positiv = synthetisches Panel mit injiziertem
    Querschnitts-IC von exakt 0,04 bei realistischer Korrelationsstruktur, das
    Gate muss feuern; negativ = Panel mit identischer Vol-/Korrelationsstruktur
    ohne Signal, das Gate darf nicht feuern; plus das Survivorship-Fixture aus V-0.
- **Was ihn a priori toetet:** (1) V-0 liefert K < ~110 durchgehend handelbare
  Perps ueber beide Fenster -> struktureller Power-DROP wie GL-012, kein
  Datenlauf noetig. (2) V-0 zeigt, dass delistete Perps aus Bybit-Bordmitteln
  nicht rekonstruierbar sind UND das Survivorship-Fixture zeigt eine
  Verzerrung in der Groessenordnung der erwarteten Kante -> nicht registrierbar.
  (3) Die gemessene `sigma_xs` liegt unter ~500 bps/Woche -> Bruttokante
  strukturell unter der Wand, Tradability a priori tot (Mess-Gate koennte
  formal noch laufen, aber ohne Handelsperspektive; dann als reine
  kapitalfreie Existenzfrage kennzeichnen, nach Kompendium C.2).
- **Bezug zu Kompendium D/E:** Wiederholt **nicht** D.7 (C-06/H-07/H-08). H-07
  starb an `max|z| = sqrt(N-1) = 2,0 < 2,5` bei N=5 -- hier ist bei K=150
  `max|z| = 12,2`, die strukturelle Sperre ist aufgehoben. H-08 starb empirisch
  auf **demselben** 5-Symbol-Panel; das nachweislich neue Signal ist die um
  Faktor 30 groessere Breite, ohne die der Test in H-08 gar nicht aussagefaehig
  sein konnte (Rauschboden `SE(IC) = 0,50` bei N=5 gegen `0,0114` hier -- Faktor
  44). Die Richtung ist zudem invers zu H-08 (Momentum statt Mean-Reversion) und
  der Horizont ist Wochen statt Stunden. Nutzt den offenen Faden E: das
  PRD-PARK-Register haelt **C-13 Cross-Sectional-Z** mit der Entsperrbedingung
  "nur falls 2-Symbol-Mess-Gate handelbare Kante findet" -- diese Bedingung ist
  durch H-04b/H-05c **nicht** erfuellt, daher ist K-01 formal eine NEUE
  Registrierung, kein C-13-Wiedergaenger; sie ersetzt die tote
  Mikrostruktur-Begruendung von C-13 durch eine Faktorpraemien-Begruendung.
  Vermeidet ausserdem D.16 (S4/S5-Infrastrukturfalle): der Panel-Harness ist
  hier ~1 Personentag CPU-Code, nicht eine Multi-Modell-Maschine.
- **Vertrauen:** **mittel-hoch** fuer die Messbarkeit (die Power-Rechnung geht
  auf, sobald K >= 170), **mittel** fuer ein positives Ergebnis (die Literatur
  ist fuer 2014-2020 stark, fuer post-2021 explizit abschwaechend [sek]; der
  Faktor ist der bekannteste im Krypto-Querschnitt und entsprechend gut
  abgegrast), **niedrig-mittel** fuer Handelbarkeit nach Friktion, weil alles an
  der ungemessenen `sigma_xs` und an der Slippage im Alt-Perp-Segment haengt
  (15 bps ist die Majors-Konstante; auf Rang-200-Perps ist sie **unbelegt** und
  vermutlich deutlich hoeher -- eigene Slippage-Messung ist Pflicht vor jedem
  Tradability-Gate).

---

### K-02 Querschnitts-Funding-Carry auf Perps (richtungsneutral, ohne Spot-Bein)

- **Ertragsquelle:** **Praemie**, nicht Prognose. Der Funding-Satz ist eine
  explizite, dreimal taeglich ausgezahlte Kompensation dafuer, dass jemand die
  unbeliebte Seite eines Perp haelt. Wer zahlt: der gehebelte Long im Bullenmarkt
  (bzw. der gehebelte Short im Ausverkauf), der fuer Sofort-Exposure ohne
  Kapitaleinsatz zahlt. Das ist eine Risikopraemie mit sauber identifizierbarem
  Zahler -- genau die Klasse, in die 3.0 laut Auftragslage suchen soll.
  **Abgrenzung:** Dies ist NICHT der Cash-and-Carry-Basistrade (Perp short +
  Spot long). Es ist ein **dollarneutrales Querschnitts-Portfolio nur auf Perps**:
  long die Perps mit dem niedrigsten (idealerweise negativen) Funding, short die
  mit dem hoechsten. Das Marktrisiko faellt im Querschnitt heraus, das Spot-Bein
  entfaellt, und damit auch dessen doppelte Gebuehr.
- **Horizont & Instrument:** Signal = mittlerer Funding-Satz der letzten 3-7 Tage,
  Halteperiode 1 Woche, Bybit-Linear-Perps, Dezil-Long-Short.
- **Literatur/Evidenz:**
  - Crypto-Carry als Strategie: annualisierter Sharpe 6,45 ueber 2020-2025,
    ab 2024 auf 4,06 gefallen, 2025 negativ; der Ertrag stammt ueberwiegend aus
    dem Funding-Satz selbst (Mittelwert ~8 % bei Volatilitaet 0,8 %) [sek].
    **Achtung:** diese Zahlen beziehen sich auf den delta-neutralen
    Spot-vs-Perp-Carry, nicht auf die hier vorgeschlagene Querschnittsvariante,
    und ein Sharpe von 6,45 ist ein Warnsignal fuer nicht abgezogene
    Finanzierungs-/Ausfall-/Delisting-Risiken, nicht ein Qualitaetsmerkmal.
  - Perps machen ~93 % des Krypto-Futures-Volumens aus; Funding-Dynamik ueber
    fragmentierte Maerkte ist wenig untersucht [sek].
  - Basis-/Spread-Abweichungen fallen im Mittel ~11 % pro Jahr, konsistent mit
    zunehmendem Arbitragekapital; Hedgefonds haben Ende 2021/Anfang 2022 aus
    dieser Aktivitaet rotiert [sek]. Der Zerfallspfad ist damit belegt und die
    REZENZ-Klausel entsprechend zwingend.
  - Eine spezifisch **querschnittliche** Funding-Sortierung auf Perp-only-Basis
    habe ich in der Literatur **nicht** gefunden -- das ist der eigentliche
    Reiz und zugleich das Data-Snooping-Risiko.
- **Erwartete Groessenordnung vs. Friktion:** Der Funding-Satz ist ein
  **Cashflow**, keine Preisprognose. Typische Majors: 0,01 %/8h = 3 bps/Tag =
  ~21 bps/Woche = ~11 % p.a. Im Alt-Segment laufen Spitzen-Perps regelmaessig
  auf 0,05-0,3 %/8h. Ein Dezil-Spread von 30-100 bps/Woche im Funding ist damit
  plausibel (**unbelegt**, in V-0 zu messen) gegen 18 bps/Woche Kosten.
  **Die entscheidende, falsifizierbare Frage ist nicht, ob der Cashflow da ist -- 
  er ist trivial da -- , sondern ob das Preisbein ihn exakt auffrisst.** Genau das
  ist die Nullhypothese und der Grund, warum dieser Kandidat sauber ist: er hat
  einen strukturellen, vorab exakt berechenbaren Nulleffekt.
- **Daten:** `/v5/market/funding/history` (oeffentlich, 200 Records/Call [sek]),
  K~300 Symbole x 6.023 Records = ~9.300 Calls, ~15 min. Plus das
  Kline-Panel aus V-0 fuer das Preisbein. Historische Tiefe der Funding-Historie
  je Symbol: **unbelegt**, V-0-Probe. Der Harvest-Baum hat nur 113 Tage
  `bybit/rest.fundingRate` (Kompendium F.1) -- reicht nicht, Nachladen ist
  zwingend.
- **Rechenaufwand:** CPU-only, Minuten. PC-tauglich.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Metrik:** Gesamtrendite des Dezil-L/S-Portfolios, **zerlegt** in
    (i) Funding-Akkumulation und (ii) Preisbein. Urteilstragend ist die
    **Summe**; die Zerlegung wird verpflichtend mitberichtet, weil ein positives
    Gesamtergebnis bei stark negativem Preisbein eine andere Aussage ist als
    eines mit neutralem Preisbein.
  - **Fenster:** wie K-01, W1/W2 je 12 Monate ab 2024-07-01, hartes
    Ein-Fenster-Kriterium.
  - **Struktureller Nulleffekt (DEC-31/33), hier besonders scharf:** unter der
    No-Arbitrage-Nullhypothese ist der Funding-Cashflow exakt durch die
    Preisdrift kompensiert, Gesamtrendite = 0. Der strukturell **positive**
    Bias, der vorab auszurechnen ist: (a) das Short-Bein sind per Konstruktion
    die Perps mit dem staerksten juengsten Preisanstieg (Funding korreliert
    mechanisch mit Momentum) -- K-02 ist also ohne Orthogonalisierung ein
    **verstecktes Reversal-Portfolio**. Pflicht: Rendite wird gegen K-01
    (Momentum) und K-04 (Reversal) regressiert, urteilstragend ist das
    **Residual-Alpha**, nicht die Rohrendite. (b) Ein
    Funding-basierter Sortierschluessel kippt systematisch in illiquide
    Kleinstperps -- der Kosten-Nullpunkt ist symbolabhaengig und muss mit
    symbolspezifischer, gemessener Slippage gerechnet werden, nicht mit der
    Majors-Konstante 15 bps.
  - **Rauschboden:** wie K-01 aus `1/sqrt((K-1)*W)`; zusaetzlich muss die
    Funding-Persistenz gemessen werden (ist der Sortierschluessel ueber eine
    Woche ueberhaupt stabil? Bei Autokorrelation < 0,3 ist das Signal zum
    Handelszeitpunkt bereits verfallen und der Kandidat tot).
  - **FDR-Familie:** F-CARRY1 = {K-02 (3 Lookback-Laengen)} plus Ueber-Familie.
  - **Fixtures:** positiv = synthetisches Panel, in dem Funding zu 50 % NICHT
    durch Preis kompensiert wird; negativ = Panel mit exakter Kompensation
    (Gesamtrendite muss statistisch 0 sein -- dieser Fixture prueft direkt, ob
    die Buchhaltung der Funding-Akkumulation korrekt ist, was der haeufigste
    Implementierungsfehler dieser Klasse ist).
- **Was ihn a priori toetet:** (1) Funding-Historie reicht nicht ueber beide
  Fenster fuer >= 110 Symbole zurueck. (2) Die Autokorrelation des
  Funding-Sortierschluessels ueber eine Woche liegt unter 0,3 -> das Signal ist
  bei Handelsbeginn tot. (3) Nach Orthogonalisierung gegen Momentum/Reversal
  bleibt kein Residual -- dann ist K-02 nur ein teuer verpacktes K-01/K-04 und
  darf nicht als eigener Kandidat weitergefuehrt werden.
- **Bezug zu Kompendium D/E:** Wiederholt **nicht** D.1/H-01 (S3
  Pre-Settlement-Funding-Pressure). H-01 war ein **Minuten**-Timing-Trade um den
  Settlement-Zeitpunkt herum, mit -15,47 bps Nettokante; hier wird der Funding-
  **Cashflow ueber eine Woche geerntet**, das Settlement-Timing ist irrelevant
  und wird bewusst nicht ausgenutzt. Beruehrt PRD-PARK **C-23
  Basis-Convergence** ("2-Bein ~22 bps gegen < 0,08 % Konvergenz") -- dessen
  Entsperrbedingung ist "Standalone-Verdrahtung + Nachweis Konvergenz >
  Friktion"; K-02 umgeht das 2-Bein-Problem, indem es das Spot-Bein weglaesst
  und damit die halbe Gebuehr spart. Beruehrt ausserdem den gestrichenen
  Kandidaten DSM-03 (Funding-Premium-**Vorhersage**, Kompendium D.17) -- K-02
  sagt Funding NICHT vorher, sondern nimmt den realisierten Satz als
  Sortierschluessel.
- **Vertrauen:** **mittel-hoch** fuer die Messbarkeit und fuer die Sauberkeit
  der Nullhypothese (das ist der methodisch klarste Kandidat des Berichts),
  **niedrig-mittel** fuer ein positives Residual-Alpha (die Kompensationsthese
  ist oekonomisch stark, und ein 2025 negativ gewordener Carry [sek] deutet auf
  Abarbeitung), **niedrig** fuer die Kostenrechnung, weil das Signal in illiquide
  Symbole zieht.

---

### K-03 Time-Series-Momentum / Trend (1-4 Wochen) -- nur als BREITEN-Variante

- **Ertragsquelle:** Prognose. Trendfolge als Kompensation dafuer, dass der
  Trendfolger Liquiditaet in genau den Momenten nachfragt, in denen
  Risikoreduzierer (Vol-Target-Fonds, Margin-Calls, Liquidationskaskaden) sie
  brauchen. Wer zahlt: der zwangsweise Entkaeufer.
- **Horizont & Instrument:** Signal = Vorzeichen (oder vol-normierte Staerke) der
  1/2/4-Wochen-Rendite je Symbol, Halteperiode 1 Woche, Bybit-Perps.
- **Literatur/Evidenz:**
  - Liu/Tsyvinski (2021) *RFS*: starker TS-Momentum-Effekt auf 1-4-Wochen-
    Horizont [sek, Zahlen s. K-01].
  - Zerfall nach 2021 belegt [sek: BATP-Vergleichsstudie -- TS-Momentum liefert
    2022-2023 negative Jahresrenditen; nach Mitte 2021 sinkende kumulierte
    Performance; die Querschnittsvariante haelt sich besser].
  - Praktiker-Groessenordnung mit Kosten: arXiv-Preprint 2602.11708 (2026),
    "Systematic Trend-Following with Adaptive Portfolio Construction" -- 150+
    Krypto-Paare, 2022-2024, annualisierter Sharpe **2,41** bei modellierten
    4 bps Taker, orderbuchkalibrierter Slippage und Funding-Kosten [sek].
    **Dieser Wert ist mit grosser Vorsicht zu lesen:** ein Sharpe von 2,41 ueber
    3 Jahre in einem nicht peer-reviewten Preprint mit "adaptiver
    Portfoliokonstruktion" ist das klassische Ueberanpassungsprofil.
  - Konservativer Praktikerbereich: XBTO-Trendstrategie 2020-2025 gegen
    passives BTC: Sharpe 1,62 vs. 0,95, ~27 % weniger annualisierte Rendite bei
    ~5x kleinerem Maximum-Drawdown [sek, Anbieter-Eigenwerbung, kein
    unabhaengiger Track Record].
- **Erwartete Groessenordnung vs. Friktion:** Friktion ist hier **nicht** das
  Problem. Ein 1-Wochen-Trendsignal mit ~0,3-0,5 Vorzeichenwechseln pro Woche
  kostet 9-15 bps/Woche = 5-8 % p.a. bei 1x Brutto. Gegen eine
  Krypto-Jahresvolatilitaet von 60-80 % ist das ein Sharpe-Abschlag von
  ~0,08-0,13 -- eine **echte Fussnote**. Das Problem ist ausschliesslich die
  Power.
- **Daten:** Bestand (WP-0-Bar-Cache, 5 Symbole, 5-6 Jahre) reicht **technisch**,
  aber nicht statistisch. Fuer die Breiten-Variante das V-0-Panel.
- **Rechenaufwand:** trivial, CPU, Sekunden.
- **Kapitalfreies Mess-Gate (Entwurf) -- und hier liegt der Bruch:**
  - **Power (Pflichtteil, GL-012):** TSMOM ist Markt-Timing. Selbst auf 300
    Symbolen ist das aggregierte Portfolio **eine** Renditeserie, weil alle
    Symbole am selben Markt-Beta haengen -- `N_eff ~ 1-1,5`, nicht 300.
    Unter der REZENZ-Klausel (2 disjunkte Fenster nach Mitte 2024, je 12 Monate)
    muss ein annualisierter Sharpe von **2,80 in JEDEM Fenster** erreicht werden.
    Selbst mit 2 x 18 Monaten sind es noch 2,29 je Fenster. Der beste
    unabhaengig plausible Literaturwert liegt bei 1,6 [sek]. **Das Gate ist auf
    diesem Datenbestand strukturell unerreichbar -- genau das GL-012-Muster von
    H-07, nur an der Zeitachse statt an der Querschnittsachse.**
  - **Konsequenz:** K-03 wird als gerichtete Timing-Hypothese **nicht
    registriert.** Er wird ausschliesslich in einer der beiden folgenden Formen
    registrierbar:
    (a) **als Panel-Regression statt als Portfoliorendite:** urteilstragend ist
    nicht der Portfolio-Sharpe, sondern der **gepoolte Koeffizient** der
    Regression der Folgewochenrendite auf die vol-normierte Formationsrendite,
    mit Standardfehlern nach Driscoll-Kraay (querschnittsabhaengigkeitsrobust).
    Damit zaehlt Breite wieder -- aber nur so weit, wie die
    Querschnittsabhaengigkeit es zulaesst, und der DK-Standardfehler rechnet das
    ehrlich aus. Rauschboden: exakt der DK-Standardfehler, vorab auf einem
    permutierten Panel zu bestimmen. **Nur diese Form ist zulaessig.**
    (b) **als deskriptives Aera-Profil ohne Verdikt** ueber die volle Historie
    2021-2026, ausdruecklich als Marktarchaeologie gekennzeichnet (DEC-38).
  - **Struktureller Nulleffekt:** Eine vol-normierte Trendfolge auf einem Asset
    mit positiver unbedingter Drift hat einen strukturell **positiven**
    Erwartungswert, der nichts mit Trendprognose zu tun hat (die Strategie ist
    im Mittel long ein steigendes Asset). Vorab auszurechnen als: identische
    Strategie auf einer blockweise umsortierten Renditeserie, die die
    unbedingte Drift und die Vol-Clusterung erhaelt, die Reihenfolge aber
    zerstoert. Das ist das direkte Analogon zum Dressing-Artefakt (DEC-31/33,
    Programm-Konstante B.9): ohne diesen Abzug misst man die Drift, nicht den
    Trend.
  - **FDR-Familie:** F-TSMOM1 = {K-03 (3 Formationslaengen)} + Ueber-Familie.
  - **Fixtures:** positiv = AR(1)-Renditeprozess mit phi=0,1 auf Wochenbasis;
    negativ = iid-Renditen mit identischer Vol-Clusterung (GARCH) und identischer
    Drift -- das Gate darf auf letzterem nicht feuern, was genau den
    Drift-Artefakt-Test darstellt.
- **Was ihn a priori toetet:** Bereits geschehen fuer die Portfolio-Sharpe-Form
  (Power, siehe oben). Die Panel-Regressionsform stirbt, wenn der
  Driscoll-Kraay-Standardfehler auf dem permutierten Panel zeigt, dass der
  Rauschboden ueber der plausiblen Effektgroesse liegt -- das ist vor jedem
  Datenlauf berechenbar und muss berechnet werden.
- **Bezug zu Kompendium D/E:** Wiederholt **nicht** D.14 (C-24/H-24,
  Minuten-Netto-Fluss als Fortsetzungssignal) -- das war ein 30-Minuten-Horizont
  auf einem Fluss-Signal, hier ist es ein Wochen-Horizont auf einem
  Preis-Signal. H-24 hat allerdings einen relevanten Querbefund geliefert, der
  gegen K-03 spricht: Minuten-Impact ist **permanent, nicht fortsetzend**, ueber
  zehn Halbjahre stabil (Programm-Konstante B.14). Das ist eine
  Mikrostruktur-Aussage und schliesst Wochen-Trend nicht aus, aber es ist kein
  Rueckenwind. Wiederholt nicht D.3 (CS-02/S2 Entropie-Momentum): das war ein
  Orderflow-Entropie-Sign-Flip auf Sekundenskala, keine Preis-Trendfolge.
  Beruehrt das PRD-PARK "Vol-Targeting (Risk-Layer aus C-42)" -- dessen
  Entsperrbedingung ("aktiviert erst bei netto-positiver Basis") ist der
  eigentliche Grund fuer K-07.
- **Vertrauen:** **hoch** darin, dass die Portfolio-Sharpe-Form nicht
  urteilsfaehig ist (die Rechnung ist eindeutig); **niedrig-mittel** darin, dass
  die Panel-Regressionsform ein verwertbares Verdikt liefert; **niedrig** in ein
  positives Ergebnis (der Zerfall nach 2021 ist mehrfach belegt [sek], und die
  REZENZ-Klausel zwingt genau in die Zerfallsperiode).

---

### K-04 Querschnitts-Kurzfrist-Reversal (1 Woche) auf dem breiten Universum

- **Ertragsquelle:** Praemie (Liquiditaetsbereitstellung) -- der Reversal-Trader
  wird dafuer bezahlt, dass er die Gegenseite eines nicht-informierten
  Nachfrageschocks nimmt. Wer zahlt: der Fonds/Retail-Fluss, der eine grosse
  Positionsaenderung in kurzer Zeit durchdruecken muss, und der liquidierte
  gehebelte Halter. Oekonomisch das saubere Gegenstueck zu K-01: **derselbe
  Datensatz, entgegengesetztes Vorzeichen, anderer Mechanismus** -- was die
  gemeinsame FDR-Familie zwingend macht.
- **Horizont & Instrument:** Formation 1 Woche (bzw. 3 Tage), Halteperiode
  1 Woche, Bybit-Perps, Dezil-Long-Short (long die Verlierer der Vorwoche).
- **Literatur/Evidenz:** Grobys/Sapkota (2019) finden **keine** signifikante
  Kurzfrist-Reversal-Praemie, waehrend andere Arbeiten Reversal-Effekte finden,
  die aus der Illiquiditaet der Mehrheit der Coins resultieren [sek]. Der
  Widerspruch ist selbst die Information: **wenn Reversal existiert, ist es eine
  Illiquiditaetspraemie, und dann frisst die Friktion sie per Konstruktion.**
  Liu/Tsyvinski/Wu (2022) berichten fuer eine Reihe von Charakteristika
  signifikant **negative** Long-Short-Renditen (u. a. Size) [sek], was mit einem
  Reversal/Illiquiditaets-Mechanismus konsistent ist.
- **Erwartete Groessenordnung vs. Friktion:** Hier ist die Wand **keine
  Fussnote**, sondern der Gegner. Reversal-Signale haben per Konstruktion
  Turnover nahe 1,0 (das Signal dreht jede Woche) -> 30 bps/Woche = 15,7 % p.a.
  bei 2x Brutto. Bruttokante muesste bei IC=0,03 und `sigma_xs`=1200 bps also
  72 bps/Woche gegen 30 bps stehen -- noch tragfaehig, aber der Sicherheitsabstand
  halbiert sich gegenueber K-01. Zusaetzlich zieht Reversal per Konstruktion in
  die illiquidesten Symbole (dort ist die Ueberreaktion am groessten und die
  Slippage am hoechsten) -- die Majors-Slippagekonstante von 15 bps ist dort
  **nicht** gueltig und muss symbolweise gemessen werden.
- **Daten:** identisch zu K-01 (dasselbe V-0-Panel). Zusatzkosten: null.
- **Rechenaufwand:** CPU, Minuten. PC-tauglich.
- **Kapitalfreies Mess-Gate (Entwurf):** identische Maschinerie wie K-01
  (Rank-IC, W1/W2 ab 2024-07, Permutations-Null, Block-Bootstrap,
  Driscoll-Kraay wo aggregiert). **Zusatzpflicht (Nicht-Trivialitaets-Anker):**
  Der IC muss auch nach Ausschluss des untersten Liquiditaetsdezils erhalten
  bleiben. Faellt er dort weg, ist der Befund eine reine Illiquiditaets-Artefakt-
  Messung und wird als solche etikettiert (H-16-Muster: Verdikt steht, Lesart
  wird eingeschraenkt -- Kompendium B.12).
  **Struktureller Nulleffekt (besonders wichtig):** Ein 1-Wochen-Reversal auf
  Schlusskursen enthaelt einen mechanischen Bid-Ask-Bounce-Anteil, der **auch
  ohne jede oekonomische Reversion** einen positiven Reversal-IC erzeugt. Dieser
  Anteil ist vorab exakt zu quantifizieren aus dem gemessenen Spread je Symbol
  (WP-4-Methodik) und vom gemessenen IC abzuziehen. Ohne diesen Abzug misst man
  den Spread, nicht die Praemie -- die exakte Fehlerklasse, die WP-4/DEC-42
  bereits fuer Spread-Capture aufgedeckt hat. Alternativ und sauberer:
  Formations- und Halteperiode **um einen Tag getrennt** (Gap-Design), was den
  Bounce strukturell eliminiert und gleichzeitig die Handelbarkeit realistisch
  abbildet.
  **FDR-Familie:** F-XSEC1 gemeinsam mit K-01 und K-05.
  **Fixtures:** positiv = Panel mit injizierter AR(1)-Reversion phi=-0,05;
  negativ = Panel ohne Reversion, aber MIT realistischem Bid-Ask-Bounce -- das
  Gate darf darauf nicht feuern. Dieser Negativ-Fixture ist der wichtigste des
  gesamten Berichts.
- **Was ihn a priori toetet:** (1) V-0 liefert K < 110 (wie K-01).
  (2) Der Bounce-Abzug allein erklaert den gemessenen IC (Fixture-Test).
  (3) Der IC verschwindet nach Ausschluss des untersten Liquiditaetsdezils UND
  die gemessene symbolspezifische Slippage im verbleibenden Universum uebersteigt
  die Bruttokante -> Tradability a priori tot, Mess-Gate nur noch kapitalfrei.
- **Bezug zu Kompendium D/E:** Grenzfall zu D.7 (C-06 auf dem 5-Symbol-Panel
  "erschoepft"). Das nachweislich neue Signal ist dreifach: (i) Breite K=150+
  statt N=5 (Rauschboden Faktor 44 kleiner), (ii) Horizont Woche statt Stunden
  (H-08 lief auf h6-Horizonten), (iii) explizite Bounce-Kontrolle, die in H-08
  nicht existierte. Ohne diese drei ist er eine unzulaessige Wiederholung -- 
  **das muss in der Registrierung woertlich so stehen**, sonst ist es
  Registry-Verstoss. Wiederholt nicht D.12 (H-20 Tail-Aftermath): das war eine
  bedingte Reversion nach 3,5-sigma-**Stunden** auf 5 Symbolen, hier ein
  unbedingter Querschnitts-Rangfaktor auf Wochenbasis.
- **Vertrauen:** **mittel** fuer die Messbarkeit, **niedrig-mittel** fuer ein
  Ergebnis, das den Bounce-Abzug und den Liquiditaetsfilter ueberlebt.
  Ich halte K-04 fuer den wahrscheinlichsten Kandidaten, der ein formales
  WEITER erreicht und danach an der Tradability stirbt -- genau das Muster
  H-04 -> H-04b.

---

### K-05 Querschnitts-Volatilitaets-/Beta-Anomalie auf dem breiten Universum

- **Ertragsquelle:** Praemie (Hebelbeschraenkung + Lotterie-Nachfrage). Wer
  Hebel nicht bekommt oder nicht will, kauft stattdessen das volatilste
  Instrument; wer Lotterie-Payoffs mag, ueberzahlt die rechte Verteilungsseite.
  Wer zahlt: der hebelbeschraenkte bzw. lotteriesuchende Kaeufer. In Krypto ist
  der Mechanismus **umstritten**, weil Hebel gerade NICHT beschraenkt ist
  (25-100x auf Perps verfuegbar) -- was theoretisch die BAB-Begruendung
  aushebelt, aber die Lotterie-/MAX-Begruendung unberuehrt laesst.
- **Horizont & Instrument:** Signal = realisierte 30-Tage-Volatilitaet bzw.
  Markt-Beta bzw. MAX (groesster Tagesertrag der letzten 4 Wochen), Halteperiode
  1 Woche, **vol-gewichtetes** dollarneutrales Dezil-Long-Short (Gleichgewichtung
  waere hier strukturell falsch, s. u.).
- **Literatur/Evidenz:** Liu/Tsyvinski/Wu (2022) fuehren Volatilitaet als eine
  von vier Charakteristika-Gruppen (Size, Momentum, Volume, Volatility) und
  finden signifikante Long-Short-Renditen, die aber **vollstaendig** vom
  3-Faktor-Modell (Markt/Size/Momentum) erklaert werden [sek]. Das ist eine
  starke A-priori-Warnung: die Vol-Sortierung koennte reine Size-Redundanz sein.
  Fuer Aktien ist die BAB-/IVOL-/MAX-Familie gut belegt; die IVOL-Alpha-Relation
  wird auf langen Horizonten durch die Beta-Alpha-Relation erklaert, auf kurzen
  nicht [sek]. Krypto-spezifische, peer-reviewte BAB-Evidenz habe ich **nicht**
  gefunden -- als **unbelegt** zu fuehren.
- **Erwartete Groessenordnung vs. Friktion:** Vol-Rankings sind sehr persistent
  (Vol-Clusterung), also ist der Turnover **niedrig**: 0,15-0,25/Woche
  plausibel -> **4,5-7,5 bps/Woche = 2,3-3,9 % p.a.** Das ist der
  friktionsfreundlichste Kandidat des Berichts. Bruttokante bei IC=0,02 und
  `sigma_xs`=1200: ~48 bps/Woche gegen ~6 bps Kosten -- Faktor 8.
  **Hier wird die Wand tatsaechlich zur Fussnote, und zwar wegen der
  Signalpersistenz, nicht wegen des Horizonts.** Das ist die zweitwichtigste
  Erkenntnis dieses Berichts nach 0.2.
- **Daten:** identisch zu K-01 (dasselbe V-0-Panel, Tagesbars reichen fuer
  Vol/Beta; 1h-Bars fuer eine robustere realisierte Vol). Zusatzkosten: null.
- **Rechenaufwand:** CPU, Minuten.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Metrik:** Rank-IC zwischen Vol-Rang (bzw. Beta-Rang, bzw. MAX-Rang) und
    Folgewochenrendite; urteilstragend ist das **Alpha gegen ein
    3-Faktor-Modell aus Markt, Size (Volumen-Proxy) und K-01-Momentum**, nicht
    die Rohrendite. Ohne diese Orthogonalisierung wiederholt man exakt den
    LTW-Befund "alles vom 3-Faktor-Modell erklaert" [sek] und lernt nichts.
  - **Struktureller Nulleffekt (DEC-31/33), hier der schaerfste des Berichts:**
    Ein **gleichgewichtetes** Long-Low-Vol/Short-High-Vol-Portfolio hat einen
    strukturell positiven arithmetischen Erwartungswert allein aus dem
    Volatilitaets-Drag: bei log-normalen Renditen ist
    `E[r_arith] - E[r_geom] = sigma^2/2`, und das High-Vol-Bein hat ein
    systematisch groesseres sigma^2/2. Bei sigma_taeglich 5 % vs. 2 % ist die
    Differenz `(0,05^2 - 0,02^2)/2 = 0,105 %/Tag = 0,74 %/Woche` -- 
    **groesser als jede erwartete Kante.** Konsequenz, verbindlich: (i) das
    Portfolio wird **vol-gewichtet** konstruiert (gleiche Risikobeitraege beider
    Beine), (ii) der Rest-Drag wird vorab analytisch berechnet und abgezogen,
    (iii) die Permutations-Null wird auf **identisch vol-geschichteten**
    Zufallsportfolios gezogen, nicht auf unbedingt zufaelligen. Wer diesen
    Schritt auslaesst, misst die Jensen-Ungleichung und nennt sie Alpha -- die
    exakte Fehlerklasse von DEC-31 (CRPS-Dressing-Geschenk).
  - **Fenster / FDR:** wie K-01, F-XSEC1 (gemeinsam mit K-01/K-04; drei
    Vol-Varianten Vol/Beta/MAX zaehlen als drei Tests innerhalb der Familie).
  - **Fixtures:** positiv = Panel mit injiziertem negativen Vol-Rendite-
    Zusammenhang; negativ = Panel mit **identischer Vol-Dispersion, aber ohne
    jeden Zusammenhang** -- das Gate darf darauf nicht feuern, was den
    Drag-Artefakt direkt prueft.
- **Was ihn a priori toetet:** (1) V-0 liefert K < 110. (2) Der berechnete
  Vol-Drag ueberschreitet die plausible Kante um mehr als Faktor 2 UND laesst
  sich durch Vol-Gewichtung nicht unter ein Viertel der Kante druecken.
  (3) Die Vol-Sortierung ist mit der Size-/Volumen-Sortierung im gemessenen
  Universum mit Spearman > 0,8 korreliert -> keine eigenstaendige Achse,
  Redundanz-DROP nach dem H-23-Muster (Redundanzschwelle 0,6, Kompendium B.13).
- **Bezug zu Kompendium D/E:** Wiederholt **nichts** aus D. Nutzt das
  Redundanz-Gate-Muster aus H-23/GL-031 (Spearman gegen eine Referenzachse mit
  0,6-Schwelle) als vorregistriertes Nicht-Trivialitaetskriterium. Beruehrt den
  PRD-PARK-Eintrag **C-34 (GMM-Vol-Regime)** nur oberflaechlich: C-34 ist
  Regime-**Klassifikation** als Enabler, K-05 ist Vol als Querschnitts-
  **Charakteristik** -- andere Frage, anderer Mechanismus. Wiederholt nicht
  D.6 (C-07 Permutation Entropy als Vol-Cluster-Vorbote): K-05 will Vol nicht
  vorhersagen, sondern nutzt die realisierte Vol als Sortierschluessel; die
  Vol-Persistenz ist hier eine bekannte, nicht zu beweisende Voraussetzung.
- **Vertrauen:** **mittel-hoch** fuer die Messbarkeit und fuer die
  Friktionsvertraeglichkeit (niedrigster Turnover aller Kandidaten),
  **niedrig-mittel** fuer eigenstaendiges Alpha (LTW: vom 3-Faktor-Modell
  erklaert [sek]; ausserdem ist der Hebelbeschraenkungs-Mechanismus in Krypto
  fragwuerdig). **Der billigste Kandidat mit dem hoechsten Restrisiko, ein
  Artefakt zu messen** -- deshalb ist der Nulleffekt-Abschnitt oben so lang.

---

### K-06 Kalender-Interaktion, dollarneutral (Wochenende / US-Session / Monatsende)

- **Ertragsquelle:** Struktur (Fluss-/Teilnehmerzusammensetzung). In
  Zeitfenstern, in denen institutionelle Liquiditaet abwesend ist (Wochenende,
  Nicht-US-Stunden), verschiebt sich die Zusammensetzung der Marktteilnehmer
  systematisch; wer dann Liquiditaet bereitstellt, verlangt mehr. Am Monatsende
  kommen mechanische Rebalancing-Fluesse von Produkten mit Kalender-Mandat hinzu.
  Wer zahlt: derjenige, der ausserhalb der Kernzeit handeln muss.
- **Horizont & Instrument:** Tageshorizont (bzw. Session-Bloecke), Bybit-Perps,
  **ausschliesslich als dollarneutrale Querschnitts-Interaktion**:
  Long-High-Beta/Short-Low-Beta ueber das Wochenende vs. ueber Werktage; bzw.
  Long-Illiquid/Short-Liquid in der Nicht-US-Session; bzw. dieselben Beine um
  Monatsende. **Niemals als gerichtete Marktposition** -- siehe Power-Rechnung 0.3D.
- **Literatur/Evidenz:**
  - Wochenendeffekt auf **Aggregatebene ist tot**: kein detektierbarer
    Wochenend-Werktag-Renditeunterschied ueber Gesamt- und Teilstichproben
    2016-2019, 2020-2023 und Anfang 2024; niedrigere Volatilitaet und
    Handelsaktivitaet am Wochenende, konsistent mit Liquiditaets-/
    Aufmerksamkeitsmechanismen statt kompensierender Renditepraemien
    [sek: "Bitcoin's Weekend Effect: Returns, Volatility, and Volume (2014-2024)"].
  - Post-COVID zeigt BTC **keine** erkennbaren Kalenderanomalien, ETH schon
    [sek: Market Efficiency and Calendar Anomalies Post-COVID].
  - Intraday-/Session-Struktur auf Perps existiert nachweislich: periodische
    algorithmische Aktivitaet erzeugt Volumen-/Volatilitaetsschuebe; die
    Order-Imbalance zur Eroeffnung prognostiziert Renditen ueber **4 bis 12
    Stunden**, deutlich schwaecher auf feineren Frequenzen [sek: arXiv
    2607.09426, "The Quarter-Hour Effect", 6 Binance-Perps]. Das ist der
    einzige mir bekannte Beleg, dass auf diesem Horizont ueberhaupt etwas
    existiert -- und es ist ein Fluss-, kein Kalendersignal.
  - Options-Verfall/Max-Pain-Pinning: die verfuegbare Evidenz ist
    **journalistisch, nicht akademisch**, und sie ist negativ -- mehrere grosse
    Deribit-Monatsverfaelle ohne erkennbares Pinning trotz weit entfernter
    Max-Pain-Niveaus [sek, Coindesk/Decrypt 2025-2026]. Als **unbelegt bis
    widerlegt** zu fuehren.
- **Erwartete Groessenordnung vs. Friktion:** Aus 0.3D: eine dollarneutrale L/S
  mit sigma=120 bps/Tag hat auf Wochenendtagen (n=574) eine Nachweisgrenze von
  **14,0 bps/Tag**. Die Kosten: ein Wochenend-Trade ist ein Round-Trip pro
  Wochenende = 15 bps auf 2 Tage = 7,5 bps/Tag bei 1x Brutto, 15 bps/Tag bei 2x.
  **Nachweisgrenze und Friktionswand liegen praktisch aufeinander.** Das heisst:
  jeder Effekt, der gross genug ist, um mit 80 % Power detektiert zu werden, ist
  gerade eben handelbar -- und jeder Effekt, der nicht detektierbar ist, ist auch
  nicht handelbar. **Das ist ein ungewoehnlich sauberer Kandidat in dem Sinn,
  dass Mess-Gate und Tradability-Gate hier zusammenfallen.** Aber es heisst auch:
  der Sicherheitsabstand ist eins, nicht acht wie bei K-05.
- **Daten:** V-0-Panel mit **1h-Bars** (fuer Session-Bloecke zwingend; Tagesbars
  reichen nur fuer die Wochenend-Achse). 14.700 Calls, ~25 min. Kein
  Minutendatenbedarf.
- **Rechenaufwand:** CPU, Minuten.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Metrik:** Differenz der mittleren dollarneutralen L/S-Tagesrendite
    zwischen Kalenderregime und Komplement (**Kontrast**, nie Niveau).
  - **Struktureller Nulleffekt (DEC-31/33):** Ein naiver "Wochenendrendite > 0"-
    Test hat unter positiver unbedingter Marktdrift einen strukturell positiven
    Erwartungswert. Der Kontrast eliminiert das erste Moment, aber nicht das
    zweite: Wochenenden haben **niedrigere Volatilitaet** [sek], daher hat der
    Kontrast unter jeder vol-abhaengigen Positionsgroesse einen strukturellen
    Bias. Pflicht: Positionsgroesse ueber alle Regime **konstant**, und die
    Null ueber eine **Kalender-Permutation** (zufaellige Zuweisung von
    "Wochenend"-Etiketten unter Erhalt der Blocklaenge, 10.000 Ziehungen),
    nicht ueber iid-t.
  - **Fenster:** W1/W2 je 12 Monate ab 2024-07-01 (REZENZ). Bei n=574
    Wochenendtagen ueber 5,5 Jahre bleiben je Fenster nur ~104 Wochenendtage ->
    Nachweisgrenze steigt auf `2,802*120/sqrt(104)` = **33 bps/Tag**. Das ist
    **ueber** dem, was ich fuer plausibel halte. **Ehrliche Konsequenz:** die
    Wochenend-Achse ist unter strikter REZENZ-Klausel vermutlich nicht
    urteilsfaehig; nur die **Session-Achse** (US vs. Nicht-US, n = ca. 2 x 260
    Tagesbloecke je Fenster bei 1h-Aufloesung) hat genug Beobachtungen.
    **Empfehlung: nur die Session-Achse registrieren, Wochenende und Monatsende
    als deskriptives Aera-Profil ohne Verdikt.**
  - **FDR-Familie:** F-CAL1 = {Session, Wochenende, Monatsende, letzter Freitag}
 -- **gemeinsam**, weil sie derselben Suchachse entstammen. Vier Tests, BH
    alpha=0,10, plus Ueber-Familie. Das ist der Kandidat mit dem hoechsten
    Data-Snooping-Risiko im ganzen Bericht, und die Familie ist deshalb
    absichtlich breit geschnitten (verschaerfend).
  - **Fixtures:** positiv = Panel mit injiziertem Regime-Kontrast von 20 bps/Tag;
    negativ = Panel mit regime-abhaengiger **Volatilitaet** aber ohne
    Renditekontrast -- das Gate darf darauf nicht feuern.
- **Was ihn a priori toetet:** (1) Die Nachweisgrenzenrechnung oben toetet die
  Wochenend- und Monatsende-Achse bereits vor dem Lauf (GL-012-Muster).
  (2) Bleibt nach dem Kalender-Permutationstest kein Ueberschuss.
  (3) Der Kontrast existiert, ist aber kleiner als der symbolspezifisch
  gemessene Round-Trip -> Tradability a priori tot.
- **Bezug zu Kompendium D/E:** Wiederholt **explizit nicht** D.1/H-01
  (S3 Pre-Settlement auf Minutenskala, -15,47 bps) -- der Auftrag nennt das
  ausdruecklich als "nicht wiederholen". K-06 arbeitet auf Tages-/Session-
  Aggregaten, nutzt den Settlement-Zeitpunkt **nicht** als Einstiegstrigger und
  ist dollarneutral statt gerichtet. Wiederholt nicht D.9 (H-10 Cross-Stream-
  Pointer-Days) -- dort war die Existenzfrage nach synchronisierten Tagen,
  hier eine feste Kalenderpartition ohne Detektionsschritt.
- **Vertrauen:** **hoch** darin, dass die gerichteten Kalenderachsen tot sind
  (die Rechnung 0.3D ist eindeutig, und die Literatur stuetzt sie [sek]);
  **niedrig-mittel** fuer die Session-Achse; **niedrig** insgesamt. Ich fuehre
  K-06 vor allem deshalb, weil der Auftrag ihn verlangt und weil die
  **negative** Antwort mit einer sauberen Rechnung mehr wert ist als eine
  weitere Runde Kalender-Data-Mining.

---

### K-07 Volatilitaets-getimte Positionsgroesse als ENABLER (kein eigener Kandidat auf Kante)

- **Ertragsquelle:** **keine.** Das ist die zentrale Aussage. Vol-Targeting
  erzeugt kein Alpha; es verteilt vorhandenes Alpha ueber die Zeit um. Es ist
  ein Risiko-Layer, kein Ertragsmodul. Das PRD fuehrt "Vol-Targeting (Risk-Layer
  aus C-42)" bereits im PARK-Register mit der Begruendung "0 x Verstaerker = 0;
  keine positive Basis-E[R]" und der Entsperrbedingung "aktiviert erst bei
  netto-positiver Basis". **Diese Bedingung bleibt bindend.**
- **Horizont & Instrument:** Overlay auf K-01 bzw. K-03; Skalierung mit dem
  Kehrwert einer HAR-Prognose der Portfoliovolatilitaet, Kappung bei 2x-3x.
- **Literatur/Evidenz:**
  - Harvey/Hoyle/Korgaonkar/Rattray/Sargaison/Van Hemert (2018), *JPM* Fall 2018,
    "The Impact of Volatility Targeting": 60 Assets, Tagesdaten ab teils 1926 bis
    2017; Vol-Skalierung auf Asset- und Portfolioebene verbessert Sharpe-Ratios
    und reduziert Tail-Ereignisse; fuer Risiko-Assets fuehrt Vol-Targeting
    faktisch Momentum ein, und dieses Momentum-Overlay ist der Sharpe-Treiber
    [sek]. **Das ist die wichtigste Einschraenkung: der Sharpe-Gewinn kommt
    teilweise aus einem versteckten Timing-Signal, nicht aus reiner
    Risikonormierung.**
  - Barroso/Santa-Clara (2015), *JFE*: Skalierung von Momentum mit dem Kehrwert
    der realisierten 6-Monats-Varianz eliminiert die Momentum-Crashes praktisch
    und **verdoppelt** den Sharpe der Momentum-Strategie nahezu [sek].
  - Krypto-spezifisch: "Cryptocurrency momentum has (not) its moments"
    (*Financial Markets and Portfolio Management*, 2025) behandelt genau die
    Uebertragung von Barroso/Santa-Clara auf Krypto -- Volltext ueber den Proxy
    **nicht erreichbar**, Zahlen daher **unbelegt**. Das ist die eine Quelle,
    die vor einer Registrierung von K-07 im Volltext beschafft werden muss.
- **Erwartete Groessenordnung vs. Friktion:** Vol-Targeting **erhoeht** den
  Turnover (die Positionsgroesse aendert sich auch bei unveraendertem Signal).
  Bei einer Ziel-Vol-Anpassung mit wochentlicher Kadenz und typischer
  Vol-of-Vol liegt der Zusatz-Turnover bei ~0,2-0,4/Woche -> zusaetzlich
  **6-12 bps/Woche = 3-6 % p.a.** Der Sharpe-Gewinn aus der Literatur (bis
  Faktor 2 bei Momentum [sek]) muss diesen Aufschlag decken. Netto ist das bei
  einer Basis-Sharpe von 0,5 vermutlich ein Nullsummenspiel, bei einer
  Basis-Sharpe von 1,0+ klar positiv.
- **Daten:** identisch zu K-01/K-03; keine zusaetzlichen Daten.
- **Rechenaufwand:** CPU, Sekunden. HAR ist ein OLS auf drei Regressoren.
  **Explizit KEIN Modellwettbewerb** -- H-02 (LightGBM/HAR, 0/5 Symbole) und
  H-11c (AnEn schlaegt gedresste HAR nicht, 0/4 Zellen) haben gezeigt, dass
  jede Verbesserung ueber HAR hinaus auf diesem Datenbestand nicht nachweisbar
  ist (Programm-Konstante B.10). **HAR als Basis reicht und ist zu setzen, nicht
  zu testen.**
- **Kapitalfreies Mess-Gate (Entwurf) -- und der entscheidende Punkt:**
  - **K-07 wird NICHT als eigenstaendige Hypothese registriert.** Er ist eine
    **vorab fixierte Variante** innerhalb der Registrierung von K-01 bzw. K-03:
    "Basisvariante ungeskaliert / Variante B vol-getimt", beide vorab
    festgeschrieben, beide in derselben FDR-Familie. Damit ist ausgeschlossen,
    dass Vol-Targeting nachtraeglich als Rettungsanker fuer eine gescheiterte
    Basisvariante eingefuehrt wird -- das waere Torpfosten-Verschieben
    (Kompendium C.1/C.3).
  - **Metrik:** Delta-Sharpe und Delta-Maximum-Drawdown zwischen Basis und
    vol-getimter Variante, **nach** Abzug des Zusatz-Turnovers.
  - **Struktureller Nulleffekt (DEC-31/33-Analogon, Pflichtrechnung):** Eine
    vol-getimte Serie hat auch bei **null Prognosefaehigkeit** einen hoeheren
    Sharpe als die ungeskalierte, sobald (i) die unbedingte Drift positiv ist
    und (ii) Vol-Clusterung existiert -- weil die Skalierung den Varianzdrag
    reduziert. **Dieses "Geschenk" ist die exakte Entsprechung des
    CRPS-Dressing-Artefakts (Programm-Konstante B.9: 21-30 % geschenkter CRPSS
    an eine informationsfreie Baseline).** Es wird vorab quantifiziert, indem
    dasselbe Vol-Targeting-Overlay auf **blockweise umsortierte** Renditen
    derselben Strategie angewendet wird (Vol-Clusterung und Drift bleiben
    erhalten, die Kopplung zwischen Vol und Signal wird zerstoert), 1.000
    Ziehungen. Die Gate-Schwelle fuer Delta-Sharpe wird **oberhalb** der
    95.-Perzentile dieser Geschenk-Verteilung gesetzt -- nicht bei einem
    Literaturwert. Wer das auslaesst, wiederholt GL-022 exakt.
  - **FDR:** innerhalb der Familie des Basiskandidaten.
  - **Fixtures:** positiv = Renditeserie mit echter negativer Vol-Rendite-
    Kopplung; negativ = Serie mit identischer Vol-Clusterung und Drift, aber
    unabhaengigem Vorzeichen -- Delta-Sharpe muss dort **exakt dem berechneten
    Geschenk** entsprechen, nicht mehr.
- **Was ihn a priori toetet:** Die PRD-PARK-Bedingung: kein netto-positiver
  Basiskandidat -> kein Vol-Targeting. Wenn K-01/K-03 beide DROP sind, ist K-07
  gegenstandslos ("0 x Verstaerker = 0"). Ausserdem: wenn die Geschenk-
  Verteilung des Nulleffekts den plausiblen Delta-Sharpe der Literatur ueberdeckt,
  ist das Gate strukturell unerreichbar (GL-012-Muster).
- **Bezug zu Kompendium D/E:** Nutzt B.9/B.10 und DEC-31/33 direkt als
  Methodenvorlage. Wiederholt **nicht** D.15 (reaktives Long-Vol) -- hier wird
  keine Option gekauft, keine Volatilitaetsprognose gehandelt, sondern nur die
  Positionsgroesse eines bestehenden Portfolios normiert. Wiederholt nicht die
  C-42/H-02-Modellfrage: HAR wird gesetzt, nicht gegen etwas getestet.
  Loest den PRD-PARK-Eintrag "Vol-Targeting (Risk-Layer aus C-42)" ein, ohne
  seine Entsperrbedingung zu verletzen.
- **Vertrauen:** **hoch** darin, dass Vol-Targeting den Drawdown reduziert
  (das ist nahezu mechanisch); **mittel** darin, dass es den Sharpe nach
  Turnover-Kosten und nach Abzug des strukturellen Geschenks verbessert;
  **hoch** darin, dass es ohne Basiskante wertlos ist.

---

## Rangliste

| Rang | Kandidat | Begruendung in einem Satz |
|---|---|---|
| **0** | **V-0 Universums-/Survivorship-Zensus** | Kein Kandidat, aber die Bedingung fuer alle: liefert K, `sigma_xs`, rho_bar und die Delisting-Antwort -- ohne diese vier Zahlen ist jede Schwellenfestlegung ein C-14-Wiedergaenger. ~1 Personentag, ~40 min Download. |
| **1** | **K-01 Querschnitts-Momentum breit** | Der einzige Kandidat, bei dem Power-Rechnung, Literaturlage und Friktionsrechnung gleichzeitig aufgehen; loest zugleich das strukturelle Problem, an dem H-07/H-08 gestorben sind. |
| **2** | **K-02 Querschnitts-Funding-Carry** | Methodisch der sauberste (exakt berechenbare Nullhypothese, Praemie statt Prognose, Cashflow statt Preisprognose); Risiko liegt fast ganz in der Momentum-Redundanz und der Liquiditaet. |
| **3** | **K-05 Vol-/Beta-Anomalie breit** | Billigster Zusatztest auf demselben Panel und mit Abstand der friktionsvertraeglichste (Turnover 0,15-0,25); dafuer das hoechste Artefakt-Risiko (Vol-Drag). |
| **4** | **K-04 Kurzfrist-Reversal breit** | Gleiche Maschinerie, null Zusatzkosten, aber Turnover ~1,0 und ein Bid-Ask-Bounce-Artefakt, das groesser sein kann als die Kante. |
| **5** | **K-07 Vol-Targeting (Enabler)** | Nur als vorab fixierte Variante in K-01/K-03, nie eigenstaendig; hoher erwarteter Drawdown-Nutzen, unklarer Sharpe-Nutzen nach Kosten und Geschenk-Abzug. |
| **6** | **K-06 Kalender-Interaktion (nur Session-Achse)** | Ueberwiegend eine sauber begruendete Absage; nur die Session-Achse hat unter REZENZ genug Beobachtungen. |
| **7** | **K-03 Time-Series-Momentum** | Als Portfolio-Sharpe-Hypothese strukturell nicht urteilsfaehig (SR 2,80 je 12-Monats-Fenster noetig); nur in der Panel-Regressionsform registrierbar. |

**Empfohlene Welle:** V-0 zuerst, allein und mit binaerem Befund (WP-4-Muster).
Dann -- und nur bei K >= ~110-170 -- K-01 + K-04 + K-05 als **eine** vorregistrierte
Kohorte auf **einem** Panel-Store (F-XSEC1, zweistufige FDR nach DEC-22), K-02 als
zweite, eigene Familie. K-03/K-06/K-07 danach oder gar nicht. Gesamter
Rechenaufwand: CPU-only, keine GPU-Naechte, Groessenordnung 2-3 Personentage
Code plus Stunden Rechenzeit -- gegenueber den 57-180 GPU-Stunden von H-15/H-16
ein qualitativ anderes Kosten-Nutzen-Profil.

---

## Was ich NICHT vorschlage und warum

1. **Gerichtetes Wochenend-/Tages-Kalender-Timing auf Aggregatebene.**
   Nachweisgrenze auf BTC ueber 5,5 Jahre: 41 bps/Tag = 150 % p.a. (0.3D).
   Kein solcher Effekt existiert, und die Literatur findet fuer 2020-2024
   explizit keinen [sek]. Ein Test waere garantiert ein Nullbefund ohne
   Informationsgehalt -- dieselbe Klasse wie H-10 (N=0 Pointer-Tage).

2. **Options-Verfall-/Max-Pain-Pinning als Tageshypothese.** n=66 letzte
   Freitage in 5,5 Jahren, Nachweisgrenze 121 bps/Tag auf BTC. Selbst wenn der
   Effekt existierte, waere er unmessbar. Die verfuegbare Evidenz ist zudem
   journalistisch und negativ [sek]. Feasibility-DROP nach GL-012 vor jedem Lauf.

3. **Jede Wiederaufnahme von S3 Pre-Settlement-Funding-Timing auf Minuten-
   oder Stundenskala.** Kompendium D-Bereich via H-01, -15,47 bps Nettokante,
   der Auftrag verbietet es ausdruecklich. K-02 nutzt Funding als **Cashflow
   ueber eine Woche**, nicht als Ereignis-Timing -- das ist der einzige
   zulaessige Weg zurueck an diesen Datenstrom.

4. **1-Minuten-Klines fuer 300 Symbole nachladen.** 867 Mio Zeilen, ~24 h
   Download, kein Nutzen fuer Wochenhorizonte. Das waere exakt die
   S4/S5-Infrastrukturfalle (Kompendium D.16 / PRD Abschnitt 2.4): teure Infrastruktur
   vor validiertem Basissignal. 1d + 1h kosten 26 Minuten und beantworten
   jede Frage dieses Berichts.

5. **Ein Modellwettbewerb um die Volatilitaetsprognose (LightGBM/AnEn/TFT vs.
   HAR).** H-02 (0/5 Symbole) und H-11c (0/4 Zellen, CRPSS_dressed in 3/4
   Zellen negativ) haben diese Linie geschlossen (Programm-Konstante B.10).
   K-07 setzt HAR und testet sie nicht.

6. **Cross-Sectional-Mean-Reversion auf dem 5-Symbol-Panel in irgendeiner
   Form.** Kompendium D.7, erschoepft. K-04 ist nur dann keine Wiederholung,
   wenn V-0 tatsaechlich K >= 110 liefert; faellt V-0 negativ aus, ist K-04
   ersatzlos gestrichen und darf nicht auf N=5 zurueckskaliert werden.

7. **Ein Cash-and-Carry-Basistrade (Perp short + Spot long).** Zwei Beine,
   doppelte Gebuehr, und im PRD-PARK als C-23 mit unerfuellter
   Entsperrbedingung. K-02 erreicht dieselbe Ertragsquelle mit einem Bein.

8. **Machine-Learning-Faktormodelle / Deep Learning auf dem Wochenpanel.**
   Bei zwei 12-Monats-Urteilsfenstern und ~104 Wochen Gesamtstichprobe ist
   jede Modellklasse mit mehr als einer Handvoll Parameter garantiert
   ueberangepasst. Die Power-Rechnung 0.3C erlaubt genau eine einfache,
   vorab spezifizierte Rangkorrelation je Charakteristik -- nicht mehr.

9. **Eine Erhoehung der Rebalance-Frequenz auf taeglich, um mehr
   Beobachtungen zu bekommen.** Verfuehrerisch (5x mehr Datenpunkte), aber
   die Kosten steigen 5x (auf ~47 % p.a. bei Turnover 0,6) und die
   Beobachtungen sind ueberlappend, also nicht unabhaengig. Der Power-Gewinn
   ist ungefaehr sqrt(5) ~ 2,2, der Kostenverlust Faktor 5 -- ein schlechter
   Tausch. Wochenkadenz ist das Optimum in diesem Datenbestand.

10. **Ein Tradability-Gate mit der 15-bps-Majors-Konstante auf einem
    Alt-Perp-Universum.** Die Konstante B.1 gilt fuer BTC/ETH/SOL/BNB/XRP.
    Auf Rang-100-bis-300-Perps ist die Slippage **unbelegt** und vermutlich
    ein Vielfaches. Jedes Tradability-Gate der Kandidaten K-01/K-02/K-04/K-05
    braucht zwingend eine eigene, symbolspezifische Slippage-Messung
    (Vorlage: WP-4-Spread-Zensus, auf das breite Universum ausgedehnt) -- 
    andernfalls waere die Anti-Gaming-Klausel (Kompendium C.3) verletzt,
    weil man die Wand implizit absenkt.

---

## Quellen

Alle Zahlen aus diesen Quellen sind als **[sek]** markiert: Volltexte waren
ueber den Egress-Proxy nicht erreichbar (nber.org, link.springer.com,
arxiv.org, acfr.aut.ac.nz, osuva.uwasa.fi, bybit-exchange.github.io,
api.bybit.com allesamt geblockt), die Zahlen stammen aus
Suchmaschinen-Zusammenfassungen und sind vor jeder Registrierung im Volltext
zu verifizieren.

- [Liu, Tsyvinski, Wu (2022), Common Risk Factors in Cryptocurrency, Journal of Finance 77(2):1133-1177](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119)
- [Liu, Tsyvinski, Risks and Returns of Cryptocurrency (NBER w24877)](https://www.nber.org/system/files/working_papers/w24877/w24877.pdf)
- [Momentum Trading in Cryptocurrencies: A Comparative Study of Time-Series and Cross-Sectional Strategies (BATP)](https://www.journals.vu.lt/BATP/en/article/download/44540/42590/138419)
- [Grobys, Sandretto, On survivor cryptocurrency momentum](https://osuva.uwasa.fi/server/api/core/bitstreams/2a766d58-9fd3-44b8-b1a3-14a048a0b653/content)
- [Grobys, Sapkota (2019), Cryptocurrencies and momentum, Economics Letters](https://www.sciencedirect.com/science/article/abs/pii/S0165176519303647)
- [Cryptocurrency momentum has (not) its moments, Financial Markets and Portfolio Management (2025)](https://link.springer.com/article/10.1007/s11408-025-00474-9)
- [Harvey, Hoyle, Korgaonkar, Rattray, Sargaison, Van Hemert (2018), The Impact of Volatility Targeting, JPM](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3175538)
- [Barroso, Santa-Clara (2015), Momentum Has Its Moments, JFE](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2041429)
- [The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Cryptocurrency Futures (arXiv 2607.09426)](https://arxiv.org/html/2607.09426v2)
- [Systematic Trend-Following with Adaptive Portfolio Construction (arXiv 2602.11708)](https://arxiv.org/html/2602.11708)
- [Bitcoin's Weekend Effect: Returns, Volatility, and Volume (2014-2024)](https://www.researchgate.net/publication/396418897_Bitcoin's_Weekend_Effect_Returns_Volatility_and_Volume_2014-2024)
- [Market Efficiency and Calendar Anomalies Post-COVID: Insights from Bitcoin and Ethereum](https://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S2683-26902024000100012)
- [Bybit v5 Get Kline (Doku, ueber Proxy geblockt)](https://bybit-exchange.github.io/docs/v5/market/kline)
- [Bybit v5 Get Funding Rate History (Doku, ueber Proxy geblockt)](https://bybit-exchange.github.io/docs/v5/market/history-fund-rate)
- [Bybit v5 Rate Limit Rules (Doku, ueber Proxy geblockt)](https://bybit-exchange.github.io/docs/v5/rate-limit)

*Ende R2_TAGES_WOCHEN_HORIZONT.md*
