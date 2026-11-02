# Review: sechs Physik-/Naturwissenschafts-Konzepte fuer Krypto-Derivate (Stand 2026-11-02)

> **Rolle:** adversarischer Review (Scinance 3.0, Verfassung 3.1). **Gegenstand:** sechs vom Nutzer hochgeladene, fremde,
> ungepruefte Dokumente (Dok 1 PRD "SCINANCE-PHYSICS-EDGE v2.0"; Dok 2 Seismologie; Dok 3 Thermodynamik/Information;
> Dok 4 Biophysik; Dok 5 Research-PRD "Crypto Cascade Intelligence"; Dok 6 Zwei-Seiten-Konzept "Interdisziplinaerer
> KI-Trading-Edge"). **Massstab:** `scinance3-impl/CLAUDE.md`, Kompendium C/D, 2.0-Gesamtbericht, PRD_ANALYSE_2026-11-01
> (0, 1, 4, 5, Nachtraege 1-3), METHODEN_SWEEP_2026-11-02, DEC-104/105, FENSTERREGISTER, DATENINVENTAR_2026-11-01,
> H21_LUECKENLISTE_2026-11-02. **Nur Lesearbeit und eigene Formeln** (`calc/physics_calc.py`, Ausgabe `calc/physics_calc.out`);
> keine Marktdaten geladen, kein Harvest-Client, kein Code aus den Uploads ausgefuehrt, nichts im Repo geaendert.
> **Markierungen:** [F] Fakt aus der Akte; [R] eigene Rechnung; [U] Urteil; [V] Vermutung; [sek] Sekundaerbeleg (Lehrbuch
> oder Literatur aus dem Gedaechtnis, Primaerquelle zu beschaffen); UNBELEGT = keine Daten, keine Rechnung im Dokument und
> nicht in der Akte. "Dok-Angabe" = Zahl aus dem Upload, nicht von uns geprueft.
> **Klassen:** A = im Programm (IK-Karte, Feld F1..F12, WP, Exkurs-Aufnahme); A(neg) = im Programm bereits geprueft und
> verworfen (Negativliste N-x, Exkurs), ohne Datenlauf; B = in 2.0 getestet und tot (Kompendium D.x); C = unter der Wand
> (Sekunden..Minuten; nach Mission nur als Kosten-/Nullwelt-/Messprogramm); D = neu und unter 3.1 pruefbar; E = Analogie
> ohne pruefbaren Mechanismus oder nicht falsifizierbar; F = Governance-Konflikt mit der Verfassung.

---

## 0. Befund in Kuerze

1. [U] **Fuenf der sechs Dokumente verkaufen Sub-Sekunden-Signale als Handelskante.** Die Kernhorizonte (Lyapunov 240..550 ms,
   Transfer-Entropie 80..260 ms, Pre-Rupture 50..500 ms, Ising 80..400 ms, LIGO 100..450 ms) liegen dort, wo ein *perfektes*
   Orakel 0,20..0,53 bp liefert, gegen 11 bp Taker-Wand (Faktor 21..55) und 4 bp Maker (Faktor 8..20) [R calc A; F CLAUDE.md
   K-0.1, Errata DEC-105 Nr. 1]. Das ist die Horizont-Schere der PRD-Analyse (Abschnitt 4 Nr. 1), nicht eine neue Frontier.
2. [F/R] **Unsere Daten koennen die behaupteten Vorlaeufe gar nicht aufloesen:** `orderbook.1000` kommt mit ~431.000 Frames je
   Tag, also im **200-ms-Takt** [F DEC-Eintrag WP-10(B) zu 2026-08-13; R calc I]; ein 10-ms-Ising-Gitter hat zu 95 % keine neue
   Buchinformation, ein 100..450-ms-Chirp umfasst 0,5..2,3 Frames, der Lyapunov-Horizont 1,2..2,8 Frames. `deribit/dvol` liegt
   **stuendlich** im Archiv (24 Zeilen je Tag) [R calc I], die behauptete DVOL->RV-Fuehrung von 0,3..1,5 s ist damit nicht pruefbar.
3. [F] **Was an den Dokumenten richtig ist, steht schon in der Akte:** Quadratwurzel-Impact und Kostenkurve (IK-01), Queue- und
   First-Passage-Modelle (IK-02), Skalengesetze/Multifraktal (IK-04), Liquidations-Kaskaden/ETAS (F9, 2.0-PARK C-27/C-28/C-29,
   Negativliste N-16/N-17/N-24), Resilienz nach Schocks (X-OEKO-1 -> WP-11 v2, DEC-63: Omori-artiger Zerfall, Exponent
   0,23..0,32, Halbwertszeit 22..31 h). Was tot ist, ist dort tot: Lead-Lag (H-04/H-04b, D.11), Permutationsentropie (D.6),
   Entropie-Momentum (D.3), OFI (D.5), Spread-Capture (D.1), Branching-Schwellen (D.2), Tail-Reversion (D.12), Lotka-Volterra
   (Exkurs S2), Critical Slowing Down als Signal (N-6), TDA/RQA (N-20).
4. [R] **Zahlen sind ueberwiegend UNBELEGT, mehrere widersprechen sich selbst:** p < 1e-4 mit 1.000 Surrogaten ist unerreichbar
   (min p 0,000999); der Pareto-Index 0,723 ist mit den eigenen Tageskennzahlen unvereinbar (max/Summe 0,0077 gegen
   Erwartung ~0,28; in 2.000 Simulationen nie so klein); CPCV mit 16 Pfaden aus 6 Bloecken ist unmoeglich (5 oder 10); das
   SNR-Optimum der stochastischen Resonanz ist falsch (Delta V/2 statt Delta V/sqrt 2); die GPU-Gesamtlatenzen sind exakt die
   Summe der Einzelkerne (konstruiert, nicht gemessen) [R calc C, E, L, N, O].
5. [F] **"Garcia Seuma (2026)" kommt in der Akte nicht vor** (grep, Abschnitt 3.1). Naechster Akteneintrag: arXiv 2607.27070
   ("Early-warning signals are event-heterogeneous across seven crypto-perpetual liquidation cascades", nur Titel/Abstract,
   [sek], R3 K-34). Die Kernzahlen (n 0,10..0,20, 88 % Absorption) sind UNBELEGT und mit unseren Daten nicht pruefbar (off-book
   Fills unbeobachtet).
6. [F/U] **Governance:** Dok 1 ("Approved for Implementation", Live-Canary-Kapital ab 2027-01-06, Kelly, Meta-Fusion, GPU),
   Dok 2 (OMS/Execution-Router), Dok 3 (IOC-Orders, 4,3 ms Latenzbudget), Dok 4 (IOC/Post-Only-Logik), Dok 6 ("Freigegeben",
   Live Deployment ab Woche 10) kollidieren mit "kein Live-Order-Code", DEC-57 (GPU 0), Sequenz-Zwang und Registry-Disziplin.
7. [U] **Dok 5 ist anders:** nuechtern, mit Nicht-Zielen, Baselines, Negativkontrollen, Label-Einfrieren und `ts_available`.
   Es ist als **Methodenquelle uebernehmbar**, aber nicht als PRD: Gates ohne alpha/Power/SESOI/Selektions-K/Positivkontrolle,
   ein Tradingnutzen-Gate gegen C.2, und fast alle seine Datenstroeme (Liquidationen, `orderbook.1000`, Options-Ticker) liegen
   vollstaendig in Zone K. Sofort in Zone X geht nur die liquidationsfreie Variante auf Trades 2020..2024-06 und L2 2023-01..2024-06.
8. [F/V] **Fremdoeffnung:** Dok 2 enthaelt Streuungs-/Verteilungskennzahlen eines Zone-K-Tages (`allLiquidation` BTCUSDT) und
   Payload-Beispiele mit Zeitstempeln und BTC-Preisniveaus aus Zone V und K. Falls echt, ist das eine Oeffnung durch Fremdquelle
   und gehoert in das Konto-Inventar (Praezedenz KONTAMINATION-Vermerk DEC-97 A-3); Abschnitt 3.4.
9. [U] **Rettbar** sind hoechstens sieben Skizzen, davon **netto eine echte neue Karte** (R-1: Liquidations-Kaskaden als
   SK0-Zensus jetzt und als Zone-K-Messprogramm ab Kohorte 1, die 3.1-Nachfolge von H-21/F9) und eine bedingte (R-2: Hawkes auf
   Zone-X-Trades als Positivkontroll-Vorschaltung fuer R-1); der Rest praezisiert IK-01, IK-02, IK-04, IK-10/F7.

---

## 1. Kurzcharakteristik je Dokument

| Dok | Anspruch | Horizont | Datenstroeme (laut Dok) | Governance-Aussagen | Zone der Daten nach FENSTERREGISTER |
|---|---|---|---|---|---|
| 1 PRD Physics Edge v2.0 (540 Z.) | "Epistemologischer Beweis" nicht-zufaelliger Struktur (IAAFT, Takens, Lyapunov, Kolmogorov, RQA) plus acht Saeulen (Seismik, Thermodynamik, Biophysik, LIGO, TDA, Hydrodynamik, Quantensysteme, Neuromorphik) -> GPU-Meta-Alpha mit Kelly-Sizing | 5 ms..3 s; Edge-Fenster 50..550 ms | allLiquidation, insurance, orderbook.1000, publicTrade, tickers/tickers_1h, fundingRateAll, openInterest, deribit tickers/orderbook/dvol | "Status: Approved for Implementation"; Roadmap mit Paper Trading, "Sub-10ms Shadow Gateway", "Live Canary Capital Deployment" ab 2027-01-06; DSR > 0,95; Kelly | ueberwiegend K (Live-Stroeme ab 2026-06); L2/Trades vor 2024-07 X |
| 2 Seismologie (770 Z.) | ETAS/Omori/Gutenberg-Richter auf Liquidationen; "Garcia Seuma (2026)": subkritisch n 0,1..0,2, 88 % Insurance-Absorption, Phasenuebergang 1. Ordnung; Edges Erschoepfungs-Reversal und Pre-Rupture-Breakout | 50 ms..30 min | allLiquidation, insurance, orderbook.1000, publicTrade, fundingRate, openInterest, dvol, markprice.options | "Validierter Forschungs- und Implementierungsbericht"; Einbindung in OMS/Execution-Router; 100-Hz-Refit; Circuit Breaker | Liquidationen/Insurance nur K (ab 2026-06-16, X-Anteil null) |
| 3 Thermodynamik/Info (945 Z.) | Onsager/MEPP, Transfer-Entropie (Shannon, Renyi, KSG), Multiskalen-PE, 2D-Ising; Edges Deribit->Bybit-Lead-Lag und "Kritikalitaets-Divergenz" | 10 ms..5 s | orderbook.1000, publicTrade, deribit tickers/greeks, dvol, fundingRate, allLiquidation | "Production-Ready Research & Engineering Specification"; Latenzbudget 4,3 ms, VIP-Gebuehren, Kelly | L2 1000/Ticker K; Tardis-Kette X (63 Tage) |
| 4 Biophysik (807 Z.) | Latentes Orderbuch (A+B->0) mit Wurzelgesetz-Herleitung, Turing-Streifen, FitzHugh-Nagumo, Lotka-Volterra, 2D-Perkolation; Edges LPB, APRH, LV-PEA | 10 ms..50 s | orderbook.1000, publicTrade, allLiquidation, bybit tickers/tickers_1h, deribit tickers | "Version 2.0, vollstaendige Monographie"; IOC/Post-Only-Ausfuehrungslogik; PINNs | K (L2 1000, Ticker), X nur ueber orderbook.500 2023-01..2024-06 |
| 5 Cascade Intelligence (36 S.) | Probabilistischer Zustands-/Ereignisdetektor (Kaskaden-Hazard, Buchseiten-Erschoepfung, Resilienz); P0-A markiertes ETAS/Hawkes, P0-B First-Passage/Queue; P1 Entropie/TE/Resilienz; P2 SOC/Netz/TDA | 5 s..15 min | wie oben plus Binance, BitMEX, Tardis, kline1m/1d, Instruments/Delistings | "Forschungs-PRD zur Freigabe des MVP-Scope; noch kein Nachweis"; ausdruecklich keine Orders; Go/No-Go-Gates "nach Data-QA finalisiert"; Shadow-Signal-Service | K fuer alles mit Liquidationen/L2 1000/Optionen; V fuer Binance/Deribit-Trades 2025..06/2026; X nur Bybit-Trades/L2 500 |
| 6 KI-Trading-Edge (2 S.) | Agententeam; ETAS + Coulomb-Stress (Edge bei n > 1), Ginzburg-Landau/CSD, effektive TE, RD/Lotka-Volterra; TFT-Konsens | 0,5..5 s | allLiquidation, openInterest, orderbook (bybit, binance), tickers, publicTrade | "Version 1.0 (Freigegeben)"; Stop-Limit-Ausfuehrung; "Woche 10+: Live Deployment an Bybit" | K/V |

---

## 2. Klassifikation je Vorschlag (jede Saeule einzeln)

Spalte "Fundstelle" nennt den Akteneintrag, der die Einordnung traegt. Horizont nach Dokument.

### 2.1 Dok 1 (PRD Physics Edge)

| Nr | Vorschlag | Horizont | Klasse | Begruendung und Fundstelle |
|---|---|---|---|---|
| 1-01 | Epistemologisches Gate: IAAFT-Surrogate, Zeitumkehr-Statistik, NLPE, p < 1e-4 | < 1 s | A, B, E | IAAFT steht als Gegenprobe in IK-04 [F Sweep]. "Nicht-zufaellige Struktur existiert" ist in 2.0 bereits beantwortet: H-15 WEITER (Grammatik jenseits Markov, 200 Block-Surrogate), H-16 WEITER (Zeit-Irreversibilitaet, aber 85..106 % aus dem Vol-Envelope, B.12) - beide ohne Tradability-Folge (C.2, E.10). Die IAAFT-Null (linear-Gauss plus statische Verzerrung) wird von **jedem** Prozess mit Vol-Clustering verworfen [sek]; das Gate besteht also per Konstruktion (struktureller Nulleffekt, C.4) und trennt nicht GARCH von "Chaos" - genau die Frage, die Dok 1 2 selbst stellt. p < 1e-4 ist mit B = 1.000 unerreichbar [R calc C]. |
| 1-02 | Takens-Einbettung, Lyapunov 1,8..4,2 s^-1, Kaplan-Yorke 2,4..3,8 | 240..550 ms | C, E | Finite-Sample-Lyapunov-Schaetzer liefern auch fuer verrauschte stochastische Reihen endliche positive Werte; "0 < lambda < unendlich beweist Chaos" diskriminiert nicht [sek: Rauschen-gegen-Chaos-Literatur]. Horizont = 1,2..2,8 L2-Frames [R calc B]; perfektes Orakel 0,35..0,53 bp gegen 11 bp [R calc A]. |
| 1-03 | Kolmogorov/NCD-Kriterium C(LOB)/C(Surrogat) < 0,68 | - | A(neg), E | Kompressionsindex als Regimevariable verworfen (N-4); Schwelle ohne strukturellen Nulleffekt (C.4). |
| 1-04 | RQA DET > 0,85, LAM > 0,70 als "Ausfuehrungsfenster" | - | A(neg), E | N-20 (TDA, RQA: kein Mechanismus, keine Nullverteilung; Legacy `m12_rqa`). |
| 1-05 | Saeule I: ETAS/Omori/GR/Branching auf `allLiquidation` | ms..min | A, B, C, D (Teil) | = Feld F9 (PRD_ANALYSE 5, Rang 12), N-16/N-17 (DUP, Siegel), 2.0-PARK C-27/C-28 (E.12); jede Branching-**Schwelle** faellt unter D.2 (C-14: rho ~2e-7, sechs Groessenordnungen unter 0,85). Daten nur Zone K (F5 Live-Stroeme) -> rettbar nur als SK0 jetzt und Messprogramm ab Kohorte 1 (R-1). |
| 1-06 | "Garcia-Seuma-Paradox": n 0,10..0,20, 88 % off-book, Phasenuebergang 1. Ordnung | - | E (auf unseren Daten), UNBELEGT | Quelle nicht in der Akte (3.1); off-book-Fills sind im Harvest nicht beobachtet (Dok 5 3.4 sagt das selbst); die Kausalaussage "Absorption senkt n" ist mit unseren Stroemen nicht pruefbar. |
| 1-07 | Akustische Emissionen, Dieterich-Ruina, Pre-Rupture-Index | 50..500 ms | C, E, B-nah | (A - B) ist aus L2 nicht identifiziert (keine Reibungs- und Zustandsgroesse); PRI ist ein multiplikativer Index ohne Nullverteilung; 200-ms-Takt; inhaltlich Nachbar von D.4 (CFAR auf Inter-Arrivals, 250x unter Wand) und D.5 (OFI). |
| 1-08 | Saeule II: TE Deribit-Skew/Gamma -> Bybit, Vorsprung 80..260 ms | 0,08..0,26 s | B, C | H-04 (TE BTC->ETH 1..3 s, WEITER) -> H-04b PARK (Brutto-Einfang +0,19 bp, ~80x unter Wand); H-14 Positivkontrolle gescheitert (D.11); H-18 Fragilitaetsetikett. Perfektes Orakel 0,20..0,36 bp [R calc A]. Deribit-Ticker nur ab 2026-06-16 (K); Zone X nur Tardis-Kette an 63 Stichtagen (IK-06). |
| 1-09 | Multiskalen-Permutationsentropie, Kollaps unter 0,65 | 150 ms..1,2 s | B, C, E | D.6 (H-06: PRE-rho max 0,0145 gegen 0,30), D.3. Der "Kollaps" ist ein Fensterartefakt: mit d = 4 (24 Muster) und W <= 8 Mustervektoren ist H <= 0,654; bei BTC ~20 Trades/s enthaelt ein 150-ms-Fenster ~3 Trades, auf Skala mu = 5 im 1,2-s-Fenster ~5 Punkte [R calc J]. |
| 1-10 | 2D-Ising, Suszeptibilitaet gamma 1,75 | 80..400 ms | E, C | Spins sign(dQ) sind deterministisch aus Daten, kein Boltzmann-Ensemble; Fluktuations-Dissipations-Satz setzt Gleichgewicht voraus; 2D-Ising-Exponenten gelten fuer das isotrope Gleichgewichtsmodell, nicht fuer ein Preis-x-Zeit-Gitter [sek]. 10-ms-Raster bei 200-ms-Takt [R calc I]. Widerspricht Saeule I/Dok 2 3.3 ("Suszeptibilitaet divergierte in keinem der 7 Ereignisse"). |
| 1-11 | Saeule III: latentes Orderbuch, Quadratwurzel-Impact | Kosten | A | IK-01 (M03, Kostenkurve; Y 0,5..1 [sek]); B.14 (Impact permanent). Als Kostenkurve wertvoll, als Signal nichts. "Kyle physikalisch falsch" ist ueberzogen (Kyle ist linear im Gleichgewichtsmodell, das Wurzelgesetz gilt fuer Metaorders [sek]). |
| 1-12 | FitzHugh-Nagumo, Refraktaerphase, APRH-Maker-Sniping | s | B, E, F | Ertrag aus Spread-Rueckgang = Spread-Capture (D.1; Spread exakt ein Tick, B.2, WP-4); Maker-Rabatt widerspricht FEE_MAKER 2,0 bp (B.3). |
| 1-13 | 2D-Perkolation, p_c 0,5927, "Slippage-Singularitaet" | 0,1..50 s | E, C (Rest R-7) | p_c gilt fuer unkorrelierte Besetzung im unendlichen Gitter [sek]; die Besetzung wird ueber die Schwelle mu - 0,5 sd festgelegt und liegt per Konstruktion bei ~0,64..0,71 bzw. bei 1 fuer CV > 2 [R calc K]; Zeitachse durch Queue-Persistenz und 200-ms-Takt stark korreliert. |
| 1-14 | Saeule IV: LIGO-Chirp-Matched-Filter | 100..450 ms | E, C | Keine Inspiral-Physik, kein Template-Mechanismus; divergierende Chirp-Frequenz gegen Nyquist 2,5 Hz bei 200 ms; Falschalarmrate in nicht-gaussschem Buchrauschen unbekannt (LIGO kalibriert per Zeitverschiebung); Schwelle 8,5 (Diagramm) gegen 8,0 (Text) und Fenster 120..400 gegen 100..450 ms widerspruechlich [F Dok]. Matched-Filter-Nachbarschaft N-21. |
| 1-15 | Saeule V: TDA, persistente Homologie | - | A(neg), E | N-20; Dok 5 stuft TDA selbst als P2 mit Hyperparameter-Warnung ein. |
| 1-16 | Saeule VI: Bernoulli, Rayleigh-Plesset, Burgers/Rankine-Hugoniot | ms | E | Druck, Dampfdruck, Oberflaechenspannung, Viskositaet haben keine messbare Entsprechung; Rankine-Hugoniot ist fuer Burgers korrekt [sek], aber ohne Abbildung von u auf eine Beobachtung; "exakte Vorhersage des Kaskaden-Endpunkts" UNBELEGT. |
| 1-17 | Kolmogorov K41, Multifraktal f(alpha) | Skalen | A | IK-04 (M04, MRW als Nullwelt); Strukturfunktionen als Gate verworfen (N-7, Exkurs S3). zeta(q) ist fuer Multifraktale konkav, nicht "konvex" [sek]. |
| 1-18 | Saeule VII: Lindblad, CTQW, Quantum Discord, Zeno | - | E | Discord ist fuer klassische (diagonale) Zustaende null [sek] - "D > 0" ist auf klassischen Daten nur durch willkuerliche Einbettung erreichbar; Zeno setzt Messrueckwirkung voraus, passives Mitschneiden oeffentlicher Feeds wirkt nicht zurueck; CTQW ohne Kohaerenzmechanismus. Nicht falsifizierbar. |
| 1-19 | Saeule VIII: STDP | ms | E | Umbenennung eines Trade->Cancel-Antwortkerns; pruefbarer Rest ist Kreuzanregung im multivariaten Hawkes (Dok 5 P0-A, R-2). |
| 1-20 | Stochastische Resonanz, Iceberg-Erkennung 94 % | - | E, UNBELEGT | Nachtraeglich addiertes Rauschen kann die Information aufgezeichneter Daten nicht erhoehen (Datenverarbeitungs-Ungleichung [sek]); ohne L3 gibt es kein Iceberg-Label, also keine messbare Trefferquote; SNR-Optimum falsch [R calc L]. |
| 1-21 | Crackling-Noise gamma ~1,33, "kritischer Gehirnzustand" | - | A, E | Avalanche-Statistik = 2.0-PARK C-29 (Shape-Collapse, E.12) und Dok 5 H6; als Groessenverteilung der Trades in IK-01 (M11). Die Deutung "jede Order kann eine ungedaempfte Lawine ausloesen" folgt aus keinem Exponenten. |
| 1-22 | Meta-Alpha-Fusion sigma(w'Phi), fraktionales Kelly | ms | F | Keine Vorregistrierung, Selektions-K der Fusion unbegrenzt (DEC-51 (4)); Kelly/Kapital sind Nutzerfragen (P-11) und kein 3.1-Gegenstand. |
| 1-23 | RTX-Workstation, CUDA-Kernel, Benchmarktabelle | - | F | DEC-57 (GPU-Standardbudget 0, nur mit registrierter Begruendung); DEC-83 (gerechnet wird in der Cloud-Sitzung). Benchmarks konstruiert (3.2). |
| 1-24 | CPCV, Deflated Sharpe > 0,95, VIP-Gebuehrenmatrix, Wurzel-Impact | - | A (Teil), F | Purged Walk-Forward in H-02 [F]; DSR ist sharpe-basiert, die Verfassung urteilt nie ueber Sharpe ("Sharpe wird berichtet, nie geurteilt"); Gebuehren nicht die kanonischen Konstanten (B.3: 5,5/2,0 bp je Bein); 16 CPCV-Pfade aus 6 Bloecken unmoeglich [R calc N]; Embargo 2 h gegen gemessene Nachschock-Halbwertszeit 22..31 h (DEC-63) zu kurz um Faktor 11..16 [R calc T]. |
| 1-25 | Roadmap: NVMe-Spiegel, Paper Trading, Shadow Gateway, Live Canary Capital ab 2027-01-06; Status "Approved" | - | F | Kein Live-Order-Code (Verfassung, Autonomie Nr. 4); Registrierung nur durch den Orchestrator (Sequenz-Zwang); Kapital ist Nutzerfrage. Ein Komplettspiegel der Rohdaten ist gegen das Schutzgut "data/harvest nie cachen" und DEC-83 zu pruefen [V]. |

### 2.2 Dok 2 (Seismologie)

| Nr | Vorschlag | Horizont | Klasse | Begruendung und Fundstelle |
|---|---|---|---|---|
| 2-01 | ETAS-Intensitaet, Omori-Utsu-Kern, Likelihood, Gradienten, n-Formel | - | A (Methode) | Formeln korrekt [R: Zeitintegral c^(1-p)/(p-1) fuer p > 1, Markenerwartung beta/(beta - alpha) fuer beta > alpha]; = Methodik von F9 und C-27 (Cori-R_t, 2.0-PARK). Baustein fuer R-1/R-2. |
| 2-02 | b-Wert-Abfall vor grossen Kaskaden als Vorlaeufer | min | C, E-nah | In der Seismologie umstritten [sek]; auf Liquidationen nur Zone K (F5), also vor Kohorte 1 nur SK0; als Vorhersagesignal unter der Wand. |
| 2-03 | Edge A: Erschoepfungs-Reversal (ERS) | s..min | B, C, F | Nachbar von D.12 (Tail-Aftermath-Reversion H-20, Vorzeichen instabil) und D.15 (reaktiver Einstieg in Schockminuten); IAR > 0,6 ist bei V_cum > 5 Mio unerreichbar (verlangt 3 Mio USDT Fondsaenderung = 93x Dok-Beispielsaldo) [R calc G]; Post-Only-Orders, Stop-Loss = Ausfuehrungslogik. |
| 2-04 | Edge A: Fortsetzungs-Short (CBS) | s | C, E | Bedingung "p <= 1" ist im eigenen Code unerreichbar (Parametrisierung p = 1 + exp(.)) [F Dok 2 7.3]. |
| 2-05 | Edge B: Pre-Rupture-Breakout, 50..150 bp in 1..3 s | 50..500 ms Eintritt | C, B-nah | 50 bp in 3 s sind 32 unbedingte SD, 150 bp in 1 s 168 SD [R calc A] - seltene Schwanzereignisse ohne Haeufigkeitsangabe; Latenzabschlag 300 ms (C.3) frisst den Vorlauf. |
| 2-06 | GPU-ETAS mit 100 Hz, Einbindung in OMS/Execution-Router | - | F | Live-Ausfuehrungspfad; bei der eigenen Rate von ~214 Liquidationen/h sind 100 Hz ~1.700 Neuschaetzungen je neuem Ereignis, und das Fenster N = 2.000 entspricht ~9 h statt 1 h [R calc H]. |

### 2.3 Dok 3 (Thermodynamik / Informationstheorie)

| Nr | Vorschlag | Horizont | Klasse | Begruendung und Fundstelle |
|---|---|---|---|---|
| 3-01 | Onsager-Kraefte/Fluesse, MEPP, Glansdorff-Prigogine-Kriterium | - | E | Keine messbaren konjugierten Paare; Reziprozitaet und MEPP sind ohne Gleichgewichtsnaehe nicht definiert bzw. selbst umstritten [sek]. |
| 3-02 | TE Achse 1: IV-Skew -> Perp, 80..240 ms | sub-s | B, C | wie 1-08. |
| 3-03 | TE Achse 2: DVOL -> RV, 0,3..1,5 s | sub-s | C, nicht pruefbar | `deribit/dvol` im Archiv stuendlich [R calc I aus F Dateninventar]. |
| 3-04 | TE Achse 3: Funding-Prognose -> Taker-Fluss vor 00/08/16 UTC | min | C, A-nah | F2/R-7 (Funding-Dynamik); der 08:00-UTC-Slot ist A2-Placebo-Slot und faellt unter die A2-Maske [07:00, 08:30) in V/K (Sweep 4.7) -> Konflikt mit A2-Blindheit. |
| 3-05 | Renyi-TE alpha 0,5 fuer Schwanzereignisse | 0,5..5 s | C, E | Nichtlineare TE ohne Vorteil (N-8); Schwanzgewichtung auf wenigen Ereignissen ohne Nullverteilung. |
| 3-06 | MPE und Komplexitaets-Entropie-Ebene, Kollaps unter 0,65 / 0,50 | 150 ms..1,2 s | B, E | D.6; Fensterartefakt [R calc J]. Laminarbereich 0,88..0,98 (Dok 3) gegen 0,96..0,99 (Dok 1) [F Dok]. |
| 3-07 | 2D-Ising-Gitter 10 ms x 50 Level | 80..400 ms | E | wie 1-10. |
| 3-08 | Edge A Lead-Lag-Arbitrage, Halten 250..1.200 ms, Latenz 4,3 ms, VIP-Gebuehren | sub-s | B, C, F | H-04b; Anti-Gaming C.3 (Wand, 300-ms-Haircut, Taker fix); Gebuehren nicht B.3. |
| 3-09 | Edge B Kritikalitaets-Signal (MPE x Suszeptibilitaet x Imbalance), Kelly | 150 ms..2 s | E, F | "Phasenuebergang 2. Ordnung" widerspricht Dok 2 3.3 ("1. Ordnung, keine Divergenz"); Kelly. |
| 3-10 | GPU-Pipeline, Benchmarks | - | F | DEC-57; Benchmarks konstruiert (3.2). |

### 2.4 Dok 4 (Biophysik)

| Nr | Vorschlag | Horizont | Klasse | Begruendung und Fundstelle |
|---|---|---|---|---|
| 4-01 | Reaktions-Diffusion, latentes Buch, Herleitung I = Y sigma sqrt(Q/V) | Kosten | A | IK-01; Herleitung ist Literaturstand [sek], Y 0,5..0,7 innerhalb des IK-01-Bands 0,5..1. Nutzbar als Theorieetikett der Kostenkurve. |
| 4-02 | Turing-Instabilitaet, Liquiditaetsstreifen | - | E, B-nah | Schnakenberg-Algebra korrekt [R], aber kein identifizierter Mechanismus; Rundzahl-Praeferenz (D.8, H-09) erklaert Liquiditaetswaelle sparsamer. |
| 4-03 | FitzHugh-Nagumo, Refraktaerphase, Zweitwellen-Kollaps | s | E, B-nah | Kritischer Strom falsch: korrekt I_c = 2/3 + a - gamma (eps -> 0), Dok 2/3 + (a - gamma)/gamma [R calc M]; Nachbar D.12/D.15. |
| 4-04 | APRH: Post-Only-Maker nach Crash, Spread 50 -> 0,5 USDT | s | B, F | D.1 (Spread-Capture tot; Spread = ein Tick, B.2); Maker-Rabatt widerspricht B.3. |
| 4-05 | Lotka-Volterra mit Holling II, LV-PEA | s | A(neg), E | Exkurs S2 "Was ich NICHT vorschlage" Nr. 2 und Synthese 3: abgelehnt mit Entsperrbedingung (>= 18 Monate `orderbook.1000` auf >= 3 Symbolen plus Identifikationsargument, dass Nachfuellrate und Aggression nicht dieselbe Volumenreihe sind). Rosenzweig-MacArthur-Algebra korrekt [R]. |
| 4-06 | Perkolation LPB (Bid/Ask getrennt, xi_crit 15 Ticks) | s | E, C (Rest R-7) | wie 1-13; Preisraster 0,5 USDT sind 5 Ticks, nicht "Ticks" [sek: BTCUSDT-Tick 0,1 USDT; Spread exakt ein Tick B.2]. |
| 4-07 | Optionen-Perkolationsgitter (Strike x Verfall) | - | E | Kein Mechanismus; Daten ab 2026-06-16 (K). |
| 4-08 | GPU-RD-Solver, PINNs, Laufzeiten < 35 us | - | F | DEC-57, D.16 (Infrastruktur vor Signal). |

### 2.5 Dok 5 (Crypto Cascade Intelligence)

| Nr | Vorschlag | Horizont | Klasse | Begruendung und Fundstelle |
|---|---|---|---|---|
| 5-01 | P0-A markiertes ETAS / multivariater Hawkes, Ereignis-Ontologie, Modelltreppe Poisson -> univariat -> multivariat -> markiert -> neural | 30 s..5 min | A, C, D | F9, C-27/C-28, N-24 ("zulaessig ohne Schwelle, ohne Abnehmer"). Neu: die Ereignis-Ontologie (Trade-Burst, Depletion, Replenish, Spread-Jump) erlaubt eine liquidationsfreie Zone-X-Fassung (R-2) und eine Zone-K-Fassung mit Liquidationen (R-1). Nach Mission nur Kosten-/Stressmessung. |
| 5-02 | P0-B First-Passage / Queue-Reaction | 5..60 s | A, C | IK-02 (Intensitaeten je Level, p_fill, adverse Selektion, Resilienz, Time-to-Fill als konkurrierendes Risiko; Cont/Stoikov/Talreja, Huang/Lehalle/Rosenbaum [sek]). Ergaenzung als Ausgabe von IK-02 (R-3), keine neue Karte. |
| 5-03 | P1 Buch- und Evententropie | s | B-nah, C | D.3/D.6 (Entropie als Signal tot); als Zustandsvariable nur mit Abnehmer. |
| 5-04 | P1 Zeit-Irreversibilitaet als Fruehwarnung (Kooloth et al. 2026 [sek]) | s | B | H-16: Irreversibilitaet real, aber 85..106 % Envelope-Asymmetrie (B.12, DEC-30). Jede neue Fassung muss gegen die Envelope-Null testen. |
| 5-05 | P1 TE Liquidation -> Trades, Venue -> Venue, BTC -> ETH | s | B, C | H-04/H-04b/H-14/H-18; Cross-Venue hat **keinen** Zone-X-Anteil (Binance-Trades ab 2025-01, Deribit-Trades ab 2025-08, BitMEX 2026 [F Dateninventar]). |
| 5-06 | P1 Resilienz-Fruehwarnsystem (Recovery-Halbwertszeit, CSD) | s..min | A, A(neg) | Resilienz: IK-02 und X-OEKO-1 -> WP-11 v2 (DEC-63, Tagesskala gemessen); CSD als Signal N-6 (Literatur negativ, n_eff = T/w). Rest R-5. |
| 5-07 | H5 Cross-Excitation zwischen Boersen und Symbolen | s | B, C | D.11, D.10 (H-12), H-17/H-23 (Venue-Fingerprint ohne Tradability); Daten nur V/K. |
| 5-08 | H6 Avalanche/SOC mit Clauset-Protokoll (MLE, KS, Alternativen) | - | A, D (Teil) | C-29 (E.12); Groessenverteilung der Trades in IK-01 (M11). Das Clauset-Protokoll ist als Methode fuer R-1/R-2 verbindlich zu uebernehmen. |
| 5-09 | H7 TDA | - | A(neg) | N-20. |
| 5-10 | Label-, Validierungs- und Gate-Design | - | A (kompatibel mit Luecken) | Abschnitt 5. |
| 5-11 | Shadow-Signal-Service, Signalvertrag fuer spaetere Strategien | - | F (leicht) | Keine Orders (Verfassung eingehalten), aber Dauerbetrieb auf dem Nutzer-PC vor validiertem Signal = D.16. |

### 2.6 Dok 6 (Interaktiver KI-Trading-Edge)

| Nr | Vorschlag | Horizont | Klasse | Begruendung und Fundstelle |
|---|---|---|---|---|
| 6-01 | ETAS, Edge "n > 1 = ueberkritisch" | s | B, E | D.2 (C-14 REFUTED: rho-Median ~2e-7); widerspricht Dok 2 (n 0,10..0,20); n > 1 ist nicht-stationaer, eine stationaere Schaetzung ist dort nicht definiert [sek]. |
| 6-02 | Coulomb-Stress-Transfer auf Preislevel | - | E | Keine Spannungs- oder Reibungsgroesse im Buch. |
| 6-03 | Ginzburg-Landau, CSD mit "exponentiell" steigender Erholungszeit | s | E, A(neg) | N-6; CSD laesst die Relaxationszeit potenzgesetzartig, nicht exponentiell divergieren [sek]. |
| 6-04 | Effektive TE Optionen -> Orderbuch, 0,5..5 s | s | B, C | H-04/H-04b. |
| 6-05 | RD-PDE, Lotka-Volterra | - | A / A(neg) | IK-01 / Exkurs S2. |
| 6-06 | TFT-Konsens, Stop-Limit an Coulomb-Punkten, Live Deployment ab Woche 10, "Freigegeben" | - | F | D.16, DEC-57, kein Live-Order-Code, Registry-Disziplin. |

**Zaehlung [R]** (Mehrfachklassen, "-nah" nicht gezaehlt): 66 Zeilen; E 31, C 24, B 15, F 14, A 14, A(neg) 8 (A oder A(neg) zusammen 20 Zeilen), D nur als Teilklasse 3 (1-05, 5-01, 5-08). Rein einklassig: E 11, F 8, A 5, C 5, B 1, A(neg) 1. Keine Zeile ist rein D.

---

## 3. Zahlenpruefung

### 3.1 "Garcia Seuma (2026)" in der Akte

[F] `grep -rniIl "garc[ii]a|seuma"` ueber das Repo ohne `state/runs` und `.git`: **0 Treffer**; `git log --all --grep=seuma`: 0.
Ebenfalls nicht in der Akte: Gresnigt/Kole/Franses, Kooloth, Pindza/Mashele, Cont/de Larrard, Clauset, Mucciante/Sancetta,
Shi/Cartlidge, Li et al. 2024, Assaf et al. (Dok 5); vorhanden: Diks/Hommes/Wang (Exkurs S2), Hardiman et al. (Sweep, 2013er
Fassung), Scheffer 2009, Huang/Lehalle/Rosenbaum (IK-02). Naechster Akteneintrag zum Gegenstand: arXiv 2607.27070 "Where does
the criticality live? Early-warning signals are event-heterogeneous across seven crypto-perpetual liquidation cascades" (R3 K-34,
nur Titel/Abstract, [sek]). [V] Dok 2 3.3 ("7 historische Krypto-Crashs", keine Suszeptibilitaets-Divergenz) passt inhaltlich
dazu; ob derselbe Autor, ist offen. [V] Dok 2 nennt als Datenbasis "transparente Orderbuch- und On-Chain-Fill-Logs" und
"Backstop Liquidity Provider": das spricht fuer einen On-Chain-Handelsplatz mit Backstop-Vault, nicht fuer Bybit; die 88 %
waeren dann auf Bybit nicht uebertragbar. Status: **UNBELEGT**, Primaerquelle zu beschaffen (Netzfreigabe P-11 offen).

### 3.2 Tabelle der quantitativen Behauptungen

| Nr | Behauptung (Dok) | Herkunft | Pruefung | Status |
|---|---|---|---|---|
| Z-01 | IAAFT p < 1e-4 vor jeder Kapitalvergabe, B = 1.000 (D1 2, 2.1) | Dok | min p = 1/(B+1) = 0,000999; fuer p < 1e-4 braucht es B >= 9.999; Flussdiagramm laesst 1e-4 <= p < 1e-3 undefiniert [R calc C] | **widerspruechlich** |
| Z-02 | lambda_max 1,8..4,2 s^-1, Horizont 240..550 ms (D1 2.2) | Dok, keine Daten | 1/lambda = 238..556 ms, also intern konsistent [R calc B]; Messung nicht gezeigt; Schaetzer diskriminiert Rauschen nicht [sek] | UNBELEGT |
| Z-03 | Kaplan-Yorke 2,4..3,8; NCD < 0,68; DET > 0,85, LAM > 0,70 (D1 2.2-2.4) | Dok | keine Herleitung, keine Nullverteilung | UNBELEGT |
| Z-04 | c 5..20 ms (D1) bzw. 5..50 ms (D2 2.2) | Dok | Bereiche inkonsistent | UNBELEGT, inkonsistent |
| Z-05 | Omori p 1,15..1,40 (D1, D2) | Dok | Akte misst fuer eine andere Groesse (Nachschock-Ueberschuss von Vol/Volumen, 5-min) Exponent 0,23..0,32, Halbwertszeit 22..31 h (DEC-63) [F]; fuer Liquidationsraten nichts | UNBELEGT |
| Z-06 | b 0,314, beta = gamma 0,723 < 1 (D1, D2 5.2) | Dok, ein Zone-K-Tag | b x ln 10 = 0,7230 konsistent [R calc D]; aber die eigenen Tageskennzahlen widersprechen gamma 0,723: max/Summe 0,0077 gegen Grenzwert 1 - gamma = 0,277 (Darling [sek]), in 2.000 simulierten Pareto(0,723)-Stichproben mit gleichem N nie <= 0,0077 (0,1-%-Quantil 0,062); max/Q75 ~70 gegen typisch ~20.000, implizit gamma ~1,7 [R calc E]. Ursache [V]: Hill/Aki-Schaetzer ab dem Stichprobenminimum auf einem nicht-paretoschen Koerper. Code setzt M0 = 2,0, Text M0 = 0 (V0 = min) [F Dok 2 2.3/7.3] | **innerer Widerspruch**; Siegelzone (3.4) |
| Z-07 | n = K c^(1-p)/(p-1) x beta/(beta-alpha) (D1, D2 2.4) | Lehrbuch [sek] | formal korrekt fuer p > 1, beta > alpha [R] | korrekt |
| Z-08 | n 0,10..0,20 (D1), 0,10..0,22 (D2-Kasten), <S> = 1/(1-n) = 1,176 bei 0,15 (D2 3.1) | "Garcia Seuma" | 1,176 korrekt [R calc F]; Bereich zwischen D1/D2 abweichend; widerspricht Dok 6 ("Edge bei n > 1") | UNBELEGT |
| Z-09 | 88 % des Zwangsvolumens in 30 min off-book absorbiert; 12 % Rest (D1, D2 3.2) | "Garcia Seuma" | bei linearer Ausduennung n_eff = 0,12 n_roh folgt n_roh = 0,83..1,67 fuer n_eff 0,10..0,20 [R calc F] - das Narrativ setzt also einen nahe-/ueberkritischen Markt ohne Backstop voraus, der nicht beobachtbar ist. Bybit-Versicherungsfonds deckt Fehlbetraege zwischen Konkurs- und Ausfuehrungspreis, Liquidationsorders laufen ueber die Engine in den Markt [sek, Boersendoku zu beschaffen] - "Volumen absorbiert" passt nicht zur Mechanik [V] | UNBELEGT |
| Z-10 | OI-Bereinigung 25..70 % in < 30 min; Ordnungsparameter-Sprung 1,6..4,4 SD; Suszeptibilitaet in 5 von 7 Faellen kollabiert (D2 3.1/3.3) | "Garcia Seuma" | keine Daten | UNBELEGT |
| Z-11 | Voight-Exponent m 0,8..1,2; PRI-Vorlauf 50..500 ms; PRI > 4,5 x Basis (D2 4.2/6.2/8) | Dok | 200-ms-Takt [R calc I] | UNBELEGT, unter Aufloesung |
| Z-12 | Edge B: 50..150 bp in 1..3 s (D2 6.2) | Dok | 32..168 unbedingte SD [R calc A]; Haeufigkeit nicht angegeben | UNBELEGT |
| Z-13 | ERS: V_cum > 5 Mio, n <= 0,25, p > 1,20, IAR > 0,60; CBS: n > 0,60 oder p <= 1,00; Notbremse -500.000 USD/h (D2 6.1/8) | Dok | IAR > 0,6 verlangt > 3 Mio USDT Fondsaenderung = 93x eigener Beispielsaldo; Notbremse 15x Saldo je Stunde; p <= 1 im eigenen Code unerreichbar [R calc G; F Dok 2 7.3] | **unerreichbar** (C.12) |
| Z-14 | ETAS-Fit 1,18 ms GPU, CPU 260 ms (D1) bzw. 80..150 ms (D2), Fenster N = 2.000 in 1 h, 100 Hz (D2 7) | Dok | Speedup 220x (D1) gegen 68..127x (D2); 2.000 Ereignisse/h gegen ~214/h aus der eigenen Tageszahl [R calc H] | UNBELEGT, inkonsistent |
| Z-15 | TE-Vorsprung 80..260 ms (D1, D3 Zusammenfassung) bzw. 80..240 ms (D3 Achse 1); 50..500 ms (D3 Edge A) | Dok | keine Daten; Bereiche abweichend; perfektes Orakel 0,20..0,36 bp [R calc A] | UNBELEGT |
| Z-16 | DVOL fuehrt RV um 0,3..1,5 s (D3 2.2) | Dok | Archiv-DVOL stuendlich [R calc I] | nicht pruefbar |
| Z-17 | Deribit > 75 % Optionsmarktanteil (D3 5.1) | Dok | Groessenordnung plausibel [sek] | [sek] |
| Z-18 | H_PE laminar 0,96..0,99 (D1) bzw. 0,88..0,98 (D3); Kollaps < 0,65, Skala 5 < 0,50; C_JS 0,35..0,45 (D1, D3 3.4) | Dok | mit W <= 8 Mustervektoren ist H <= 0,654 und unter iid-Rauschen P(H < 0,65) 0,73..1,0 bei W 2..8 [R calc J] - der "Kollaps" ist ein Kurzfenster-Artefakt; Laminarbereiche widersprechen sich | **struktureller Nulleffekt** (C.4) |
| Z-19 | Ising gamma = 1,75, Divergenz 80..400 ms vorher; Delta chi > 3,0 (D3 Edge B) bzw. > 3,5 (D3 Tabelle) | Lehrbuch / Dok | Exponent korrekt fuer 2D-Ising im Gleichgewicht [sek], Uebertragung ohne Grundlage; Schwellen inkonsistent; widerspricht D2 3.3 | UNBELEGT, widerspruechlich |
| Z-20 | S_crit-Beispiele 0,01 / +0,82 / -0,95 (D3 5.2) | Dok | 0,0009 / 0,822 / -0,952 [R calc Q] | erstes Beispiel falsch gerundet |
| Z-21 | Gebuehren Taker <= 2,0 bp, Maker -0,5 bp; Mindestimpuls 4,5 bp; Latenz 4,3 ms (D3 5.1); Maker -0,5..+1 bp, Taker 2..5,5 bp (D1 7) | Dok | kanonisch FEE_TAKER 5,5, FEE_MAKER 2,0 bp je Bein, Wand 11/15 bp, Latenzabschlag 300 ms [F B.1, B.3, C.3] | nicht kanonisch |
| Z-22 | p_c 0,592746; beta 5/36, nu 4/3, tau 187/91, sigma 36/91 (D1, D4) | Lehrbuch [sek] | korrekt fuer unkorrelierte 2D-Knotenperkolation; Besetzung per Schwelle ~0,64..0,71 bzw. 1 [R calc K] | korrekt, nicht anwendbar |
| Z-23 | Y = sqrt(2/C) 0,5..0,7 (D4 2.3) | [sek] | im IK-01-Band 0,5..1 [F Sweep] | [sek] |
| Z-24 | FHN: eps 0,05, Upstroke 10..50 ms, Plateau 100..500 ms, I_c-Formel (D4 3) | Dok | I_c falsch [R calc M]; Zeiten UNBELEGT | Formelfehler |
| Z-25 | Rosenzweig-MacArthur N*, K_c (D4 4.3) | Lehrbuch | korrekt [R] | korrekt |
| Z-26 | Spread kollabiert in 500 ms von 50 auf 0,5 USDT; Maker-Rabatt (D4 7.2) | Dok | Spread exakt ein Tick, 0,0157 bp BTC [F B.2] | widerspricht Akte |
| Z-27 | LIGO rho > 8,5 (Diagramm) / > 8,0 (Text); 120..400 / 100..450 ms; SNR < -5 dB (D1 IV) | Dok | inkonsistent; Nyquist [R calc I] | UNBELEGT |
| Z-28 | TDA max l_H1 > 3,5 x Mittel (D1 V) | Dok | ohne Nullverteilung | UNBELEGT |
| Z-29 | CTQW "doppelt so schnelle" Vorhersage; Discord > 0 (D1 VII) | Dok | Discord klassischer Zustaende = 0 [sek] | nicht falsifizierbar |
| Z-30 | Stochastische Resonanz: sigma_opt = Delta V/sqrt 2; 94 % Iceberg-Erkennung (D1 VIII) | Dok | argmax der eigenen SNR-Formel = Delta V/2 [R calc L]; kein Label fuer 94 % | Formelfehler, UNBELEGT |
| Z-31 | Crackling gamma = (beta-1)/(alpha-1) ~1,33 (D1 VIII) | [sek] | Relation korrekt; Deutung UNBELEGT | [sek] |
| Z-32 | GPU-Benchmarks 202..266x; Gesamt 2.627 -> 10,7 ms (D1) und 2.282 -> 9,095 ms (D3); RD-Solver < 0,12 ms, PINN < 35 us (D4) | Dok | Gesamtzeiten sind exakt die Summen der Kerne (2.627 / 10,695; 2.282 / 9,095) ohne I/O, JSON-Parsing, Buchreplay [R calc O] -> konstruiert, nicht gemessen [V] | UNBELEGT |
| Z-33 | CPCV N = 6 Bloecke, K = 16 Pfade; DSR > 0,95 (D1 7) | Dok | phi(6, k) = 1, 5, 10, 10, 5 - 16 nicht erreichbar [R calc N; sek: Pfadformel] | **unmoeglich** |
| Z-34 | Embargo 2 h fuer Omori-Gedaechtnis (D1 7) | Dok | gemessene Nachschock-Halbwertszeit 22..31 h (DEC-63) -> Faktor 11..16 zu kurz [R calc T] | widerspricht Akte |
| Z-35 | n > 1 als Edge; tau_corr steigt exponentiell; ETE-Vorlauf 0,5..5 s (D6) | Dok | widerspricht D2 und CSD-Theorie [sek]; perfektes Orakel 0,5..5 s: 0,50..1,59 bp [R calc A] | UNBELEGT, widerspruechlich |
| Z-36 | Dok-5-Datenfakten (13.08. Duplikate, 14.08. Ausfall, ETH-Optionen 22.-27.08., L2-Fehltage 26.06., 06.07.-16.07., 01.08.; tickers_1h ab 16.06.; Instruments ab 20.10.) | DATA_ACCESS | stimmen mit Akte (Verfassung Marktdaten, E.8, H21-Liste, Dateninventar) [F]; es fehlen die L2-no_raw-Tage 14.08. (als Gesamtausfall genannt) und 13.09.-16.09. (DEC WP-10(B)); "kline1d ab 29.09.2026" widerspricht dem Katalog (kline1d ab 2021-01-01) [F] | weitgehend belegt |
| Z-37 | Dok 5 Gate "mindestens 5 % relative Verbesserung" von Log Loss oder PR-AUC | Dok | ohne strukturellen Nulleffekt; B.9 zeigt, dass Dressing allein 26..30 % CRPS-Geschenk erzeugt [F] -> vor einer festen Relativschwelle ist das Geschenk der Baseline-Form auszurechnen (C.4) | ungeprueft |

### 3.3 Widersprueche zwischen den Dokumenten (dasselbe Paket)

| Gegenstand | Aussage A | Aussage B | Folge [U] |
|---|---|---|---|
| Ordnung des Kaskaden-Uebergangs | D1 Saeule I, D2 3.3: 1. Ordnung, keine Suszeptibilitaets-Divergenz, kein CSD | D1 Saeule II, D3 4.4/5.2: 2. Ordnung, chi divergiert 80..400 ms vorher; D4 5.4: Perkolation 2. Ordnung; D6: CSD vor dem Uebergang | Die Meta-Fusion in D1 5 kombiniert Merkmale, die nach der eigenen Saeule I nicht existieren. Ein Paket, das beide Lesarten als "exakt berechenbar" fuehrt, ist nicht falsifizierbar. |
| Branching | D2: n 0,10..0,22, "Normalzustand n ~0,1" | D6: Edge, "wenn n > 1 konvergiert"; D1 5: Taker-Zweig bei n > 0,45 | D.2: jede Schwelle zuerst auf Erreichbarkeit pruefen. |
| ETAS-Latenz | D1: CPU 260 ms | D2: CPU 80..150 ms | Benchmarks nicht gemessen [V]. |
| PE-Laminarbereich | D1: 0,96..0,99 | D3: 0,88..0,98 | Kalibrierung fehlt. |
| Lead-Fenster | D1/D3: 80..260 ms | D3 Achse 1: 80..240; D3 Edge A: 50..500; D6: 500 ms..5 s | UNBELEGT in allen Fassungen. |

### 3.4 Fremdoeffnung von Zone K/V durch Dok 2 (Governance-Hinweis)

[F Dok 2 5.1/5.2] Dok 2 nennt fuer **einen Tag in Zone K** (BTCUSDT `allLiquidation`, August 2026) Anzahl, Mittelwert, Maximum,
75-%-Quantil und b-Wert, und zeigt Payload-Beispiele mit Boersenzeitstempeln und BTC-Preisniveaus von einem Tag am Ende von W2
(Zone V) und vom selben K-Tag. [F FENSTERREGISTER 6] Live-Stroeme sind ab 2026-07-01 rein K (vor Kohorte 1 nur SK0); BTC-Preise
sind BTC/ETH-Aggregat (nur prospektiv in K konfirmierbar, DEC-104 E4 (i)). [V] Ob die Werte echt oder erfunden sind, ist ohne
Siegelbruch nicht pruefbar. [U] **Empfehlung (Strenge, reversibel):** als Oeffnung durch Fremdquelle in `state/KONTO_INVENTAR`
(Praezedenz KONTAMINATION-Vermerk DEC-97 A-3) buchen; der K-Tag kommt auf die C.17-Liste jeder kuenftigen Liquidations- oder
BTC-Rendite-Statistik (R-1); die Rohwerte nicht in das oeffentliche Repo uebernehmen. Dieser Review nennt deshalb nur
abgeleitete Verhaeltnisse (Z-06), keine Niveaus und kein Datum.

---

## 4. Was ist rettbar: sieben Skizzen fuer Verfassung 3.1

Leitlinie: die Mission erlaubt Sekunden..Minuten nur als Kosten-/Zensus-/Nullwelt-Messung (CLAUDE.md, K-0.1); jede Skizze gibt
nach DEC-104 E1 Schaetzer, 95-%-CI und obere Ausschlussgrenze aus, nie ein Verdikt in Zone X; Konto-Zeile vor jeder Zone-X-Abfrage;
GPU 0; Positivkontrolle zuerst (C.13). **Netto neu ist nur R-1 (und bedingt R-2); R-3..R-7 sind Ausgaben bestehender Karten.**

### R-1 Liquidations-Kaskaden: SK0-Zensus jetzt, ETAS/Omori/Branching-Messprogramm in Zone K ab Kohorte 1 (3.1-Nachfolge von H-21/F9)

- **Frage.** Wie sind Groessen (Clauset-Protokoll: MLE, KS, Likelihood-Quotient gegen Lognormal/gestreckte Exponentialverteilung),
  Nachlauf-Kern (Omori-Potenz gegen Exponential) und Endogenitaet (Branching n mit CI, univariat und Liq -> Trade-Burst) der
  gemeldeten Liquidationen beschaffen - **ohne Schwelle** auf n (D.2 durch Konstruktion erfuellt)?
- **Abnehmer (Entscheidungsrelevanz).** (i) Stress-Kostenfenster in `tradability3` (DEC-63 (1): mindestens ein Kalendertag nach
  Schockstunde) - ab wann sind Kaskaden-Nachlaeufe in Liquidationszeit abgeklungen; (ii) STRESS_ABS-Zelle (DEC-63 (3), 27 < 30
  Ereignistage); (iii) Wiedervorlage H-21 als "Messfrage" nur ueber Kohorte 1 (H21-Liste 1).
- **Daten.** `bybit/allLiquidation` 5 Symbole ab 2026-06-16 (BTC/ETH 125/139 Tage, Alts 117/131), `insurance` ab 2026-06-16,
  `publicTrade` fuer die Kreuzanregung [F Dateninventar].
- **Zone.** Kein X-Anteil; 2026-06-16..06-28 V (blind), ab 2026-07-01 K [F Register 6, F5]. **Jetzt nur SK0:** Zeilen,
  Partitionen, Luecken, Zeitstempel, Frame-Buendelung je Tag, Schema und Meldesemantik (Mindestgroesse, Buendelungsintervall).
  Ob eine Ereigniszahl je Tag aus dem Payload noch SK0 ist, entscheidet der Orchestrator vorab (F9: Zaehlungen sind
  Vol-Stellvertreter, DEC-97 A-3).
- **Fruehester Zeitpunkt.** SK0 sofort; Registrierung zum Kohorten-Stichtag 2027-01-01 (OC liegt vor, DEC-104 Nachtrag 2);
  12-Monats-K-Fenster 2026-07-01..2027-06-30 mit bis zu vier Quartalsblicken, letzter Blick Anfang Juli 2027; Ausfallbudget
  >= 10 % (14 von 138 Tagen [F H21-Liste 2]) -> Mindestzahl gueltiger Tage statt "lueckenlos".
- **Aufwand.** SK0 < 1 h (Katalog/`hd.gaps`); Herleitung plus Review ~1..2 Agententage; Rechnung je Blick Minuten CPU
  (~163.000 Zeilen gesamt [F]).
- **Pflichtzeilen.** Cluster = Kalendertag, BTC+ETH ein Cluster (DEC-63 (2), L-6); Selektions-K (Kerne x Marken x Symbole) im
  Konto; Positivkontrolle auf synthetischem Hawkes mit bekanntem n und auf R-2; Fremdoeffnungs-Tag (3.4) auf der C.17-Liste.
- **Abgrenzung.** = F9 (konkretisiert und an 3.1 angepasst); IK-08 liefert das Ausfallbudget; kein Ueberlapp mit IK-01..IK-11.
- **Was nicht folgt.** Kein Handelssignal (unter der Wand); keine Aussage zu off-book-Fills oder zu "Garcia Seuma".

### R-2 Hawkes/ETAS auf Bybit-Trades 2020-03..2024-06 (Zone X) - nur als Positivkontroll- und Nullwelt-Vorschaltung fuer R-1

- **Frage.** Liefert dieselbe Pipeline (Modelltreppe aus Dok 5 5.1: Poisson -> univariat -> multivariat -> markiert) auf
  Trade-Bursts und Grossauftraegen stabile Kerne und Endogenitaetsschaetzer ueber Jahre und Symbole, und reproduziert sie einen
  bekannten Effekt (gleichzeitiger Minuten-IC +0,53..0,61, B.14) sowie synthetisch eingepflanzte Parameter?
- **Daten.** `bybit/publicTrade` 5 Symbole (BTC ab 2020-03-25 ... SOL/BNB ab 2021-06-29), dieselbe Stichprobe wie IK-01
  (~560 Symbol-Tage, ~20 GB, ~2,7 h Transfer [F Sweep 4.2]) - kein Zusatztransfer.
- **Zone.** X (Konto). Konfirmation keine (Nullwelt/Positivkontrolle).
- **Fruehester Zeitpunkt.** Sofort nach Konto-Zeile; vor der Registrierung von R-1 abzuschliessen.
- **Aufwand.** CPU-Stunden; Potenzkern O(N^2) je Fenster verlangt Ereignisverduennung (Bursts statt Einzeltrades; BTC ~20 Trades/s).
- **Abgrenzung.** N-24 ("Hawkes auf Trades ohne Abnehmer") bleibt gueltig, **wenn R-1 nicht registriert wird**; mit R-1 ist der
  Abnehmer die Pflicht-Positivkontrolle (C.13). IK-04 (e) Ereigniszeit-Uhr nutzt die Kerne als Nullwelt-Baustein; IK-01 nutzt die
  Burst-Zustaende als Typ-B-Stressband der Taker-Kurve. Kein Ueberlapp mit F4 (Tagesaggregate).

### R-3 First-Passage und Mehrstufen-Depletion des Buchs (Ausgabe von IK-02, keine neue Karte)

- **Frage.** P(Bid-Band bzw. Ask-Band der ersten N Stufen erschoepft vor Wiederauffuellung | Zustand) fuer 5/15/60 s und
  Rueckfuellzeit bis 50/80/100 % nach Sweeps (Dok 5 P0-B, 5.4) - als Maker-Adverse-Selection- und Stress-RAISE-Kurve.
- **Daten.** L2 `orderbook.500` BTC/ETH 2023-01-18..2024-06-30 (Snapshot+Delta [F WP-1]; X-Abdeckung UNGEMESSEN, gesamt 74/41 %),
  Trades fuer die Trade-through-Untergrenze; Takt der 500er-Aera [V] per S0 zu messen.
- **Zone.** X; Gesetzesteil (TOST) wie IK-02 in K (Alts ab 2026-07, BTC/ETH ab 2026-10-01).
- **Aufwand.** Auf der IK-02-Stichprobe (40 Tage, ~34 GB, Nutzer-PC oder L2-Vorextraktion, Datenauftrag 4) + Stunden.
- **Abgrenzung.** IK-02 enthaelt Intensitaeten, p_fill, Resilienz und Time-to-Fill; R-3 fuegt nur die Mehrstufen-Ausgabe und die
  "welche Seite zuerst"-Verteilung hinzu. WP-10(B) bleibt Groessenordnungsabgleich (E-31).

### R-4 Transfer-Entropie auf Tagesbasis (F7): keine eigene Karte, nur registrierte Nebenstatistik

- **Befund.** Cross-Venue hat **keinen Zone-X-Anteil** (Binance-Trades BTC ab 2025-01, Rest ab 2026-03; Deribit-Trades ab 2025-08;
  BitMEX 2026 [F Dateninventar]); F7 hat ~540 Vortage, MDE80 0,107 (zu kurz [F PRD_ANALYSE 5]). Cross-Asset auf dem Bybit-Panel
  ist die lineare Fassung IK-10; nichtlineare TE auf ~1.277 Tagespunkten ohne Vorteil (N-8).
- **Rettbar.** TE (KSG, Surrogat-Null mit erhaltener Saisonalitaet) als **vorab registrierte Nebenstatistik** innerhalb IK-10
  (Zone X, Konto, K-Buchung in der Renditefamilie) und spaeter innerhalb F7 (V/K). Kein eigener V-Blick (E4 (d)).
- **Aufwand.** Minuten CPU auf `kline1d`. **Abgrenzung.** IK-10, F7; D.11/H-04 (Sekunden) unberuehrt.

### R-5 Mehrskalen-Relaxation nach Schocks als Nullwelt-Kenngroesse (Resilienz ohne Fruehwarn-Anspruch)

- **Frage.** Wie skaliert die Relaxation nach Schocks von Sekunden (L2-Rueckfuellung, R-3) ueber Minuten (Bar-Cache, 1-min)
  bis zur Tagesskala (WP-11 v2: Exponent 0,23..0,32, Halbwertszeit 22..31 h, DEC-63)? Ein Kern ueber alle Skalen oder Bruch?
- **Abnehmer.** IK-04-Nullwelt (Ereignis-Clustering, Kurtosis der Clusterstatistiken), Stress-Kostenfenster, Embargo-Laengen
  jeder Intraday-Validierung (vgl. Z-34).
- **Daten/Zone.** X: WP-0-Bar-Cache, R-3-Ausgabe; keine neuen Daten. **Aufwand.** Stunden.
- **Abgrenzung.** X-OEKO-1/WP-11 (Tag, erledigt), IK-04 (Skalengesetze), IK-02 (L2-Resilienz); CSD als Signal bleibt N-6.

### R-6 Multifraktale Strukturfunktionen (Teilmodul IK-04)

- **Rettbar.** zeta(q) und f(alpha) nur als Kalibriergroessen des MRW in IK-04 (f) (Kalibrierung 2021-01..2022-09, Validierung
  2022-10..2024-06 gegen einbehaltene Momente); nie als Gate (N-7), Schaetzer mit Clauset-artiger Randkontrolle (q-Momente
  existieren nur bis zum Tail-Index). Zone X, Minuten CPU, keine neue Karte.

### R-7 Luecken- und Inselstatistik des L2 statt Perkolation (Ergaenzung IK-01 (c) / IK-02)

- **Frage.** Verteilung leerer und duenner Preisstufen-Laeufe innerhalb +-X bp nach Zustand (Vol-Terzil, Stress) gegen eine
  Nullwelt mit permutierten Stufen; Abnehmer ist der Schwanz der Buchlauf-Kosten einer hypothetischen Market-Order (IK-01 (c)).
  **Ohne p_c** (Besetzung per Schwelle festgelegt, R calc K).
- **Daten/Zone.** L2 BTC/ETH 2023-01..2024-06 (X), IK-02-Stichprobe. **Aufwand.** Stunden auf der vorhandenen Stichprobe.
- **Abgrenzung.** Keine Ertragsidee (D.1); Teil der Kostenkurven IK-01/IK-02.

---

## 5. Dok 5 (Cascade Intelligence) gegen DEC-51/53/104 und das Siegel

### 5.1 Gates und Validierungsvorschlaege

| Dok-5-Element | Akten-Massstab | Bewertung [U] | Auflage fuer eine 3.1-Fassung |
|---|---|---|---|
| Gates "nach Data-QA-Audit finalisiert" (9.5) | Vorregistrierung vor jeder Outcome-Beruehrung (C.1, DEC-104 E9); SESOI aus dem Kostenmodell (E3) | zulaessig nur, wenn das Audit SK0 bleibt | Schwellen und Design-Menue im YAML mit Hash vor dem ersten Outcome; Audit nur Zeilen/Luecken/Schema |
| Datenintegritaet: keine unerkannte Sequenzluecke | C.14 loud fail; H21-Budget-Regel (keine "lueckenlos"-Bedingung auf Live-Stroemen) | kompatibel ("unerkannt") | Mindestzahl gueltiger Tage je Fenster; Ausfallbudget >= 10 % (IK-08) |
| Ereignislabel vor Holdout eingefroren; "ausreichend unabhaengige positive Events" | DEC-51 (Power 0,80, Cluster-Einheit); E8 (d) Erreichbarkeit; C.12 | Richtung richtig, Zahl fehlt | N-Floor aus der Power-Rechnung, Cluster = Kalendertag (DEC-63 (2)), BTC+ETH ein Cluster |
| Prognoseguete: BSS > 0 und >= 5 % relativ besser als staerkste Baseline in mehreren Walk-forward-Fenstern | DEC-51 alpha/Power; C.4 struktureller Nulleffekt (B.9: Dressing schenkt 26..30 %); E2 gepoolt alpha 0,0025 + REZENZ-Screen 0,05 | **Luecke:** kein alpha, keine Power, kein Nulleffekt, "mehrere Fenster" unbestimmt | Unter 3.1 als **Messprogramm** fuehren: Verlustdifferenz je Kalendertag mit CI und Ausschlussgrenze (E1); falls doch Hypothese: einseitiger Test auf Tages-Clustern, gepoolt + Screen, MDE gegen SESOI |
| Fruehwarnnutzen: "messbarer Vorlauf" | E8 (d); `ts_available` (Dok 5 6.3, gut) | unbestimmt | Vorlauf als Verteilung mit CI, nur aus `ts_available`; 200-ms-Takt als Aufloesungsgrenze ausweisen |
| Robustheit: nicht von einem Symbol, Tag, Ereignis abhaengig | REZENZ (C.18, E6), Leave-one-cluster-out | kompatibel | REZENZ-Screen auf dem juengsten Fenster; Leave-one-event-out als Sensitivitaetszeile |
| Tradingnutzen: Netto-EV > 0 nach konservativen Kosten, 2x Slippage nicht sofort negativ, CI nur berichtet | C.2 (keine oekonomische Groesse in einer PASS-Bedingung), C.3 Anti-Gaming, E2 (Bestaetigung auf neuen Daten vor jeder Tradability-Frage), K-0.1 | **Konflikt:** Mess- und Tradability-Gate vermischt; Punktschaetzer > 0 ohne Signifikanz; Horizont 30 s..5 min ist `unter_wand` | Streichen aus dem Mess-Paket; Tradability nur als getrennte, spaetere Registrierung mit kanonischen Konstanten (11/15 bp, 300 ms) - realistisch: Etikett `unter_wand` |
| Kalibrierung | IK-08 Kalibrierbuch | kompatibel | - |
| Multiple-Testing "ueber alle Horizonte, Features, Schwellen" | DEC-51 (4) Selektions-K, E4 (f) BY q 0,10 je Kohorte | Richtung richtig, Verfahren fehlt | K zaehlen: schon H1 allein 3 Horizonte x 2 Labelvarianten x 4 Modellstufen = 24 (E[max z] ~1,95); Gesamtraster 7 Ziele x 3 Horizonte x 2 Labels ~42 (2,18) bis > 100 (2,51) [R calc P] |
| Surrogat-/Permutationstests mit Saisonalitaet; Negativkontrollen (verschobene Zeiten, falsche Richtung, verspaetete Features); Ablationen | DEC-39-Trio, H-15-Block-Shuffle | **stark**, uebernehmen | um **Positivkontrolle** ergaenzen (C.13: bekannter Effekt B.14 und synthetischer Hawkes), adversariales Fixture |
| Cluster-Bootstrap (Tag/Ereignis) | DEC-53 Ergebnis-Artefakt (Cluster-Serie + Bootstrap-Replikate + Seed) | kompatibel | Artefakt-Schema DEC-53/E1 statt nur MLflow |
| Chronologischer Walk-forward mit Purging/Embargo | Zonen X/V/K (E4); Embargo nach DEC-63 | Idee richtig | Train/Val in X, ein V-Blick je Familie, Konfirmation in K mit GSD; Embargo >= ein Kalendertag |
| GPU nur fuer Training/neural; Replay CPU | DEC-57 | kompatibel | - |
| Keine Orders, Shadow-Service | Verfassung; D.16 | Orders: kompatibel; Dauerbetrieb: zu frueh | Shadow erst nach einem Mess-Befund |
| Fehlt ganz | OC-Zeile (E8 (a)), Strenge-Quotient (E8 (b)), Zone je Datenstrom, Konto (E4 (c)), Vorwissens-Klasse (E4 (i)), Jahresbuch (E4 (g)) | Luecke | die zwoelf Pflichtzeilen plus E9-Zusatzfelder |

### 5.2 Was davon sofort als Zone-X-Messprogramm geht

- Milestone 0 als **SK0 auf allen Stroemen** (auch im Siegel): Katalog, `hd.gaps`, Zeitstempelachsen, Frame-Buendelung, Schema -
  deckt sich mit IK-08 und R-1-SK0.
- Milestone 1/2 **liquidationsfrei** auf Zone X: Ereignis-Ontologie TRADE_BURST, BID/ASK_DEPLETION, REPLENISH, SPREAD_JUMP aus
  `publicTrade` 2020-03..2024-06 und `orderbook.500` BTC/ETH 2023-01-18..2024-06-30; Modelltreppe P0-A (= R-2), First-Passage
  P0-B (= R-3), Resilienz 5.4 (= R-3/R-5), Avalanche H6 mit Clauset-Protokoll (IK-01 M11), Irreversibilitaet nur gegen die
  Envelope-Null (H-16). Alles mit Konto, Ausgabe Schaetzer/CI/Ausschlussgrenze, keine Verdikte.
- Aufwand: die Stichproben von IK-01 (~20 GB) und IK-02 (~34 GB, Nutzer-PC oder Vorextraktion) genuegen; CPU.

### 5.3 Was einen Siegelkonflikt hat

- **Alles mit `allLiquidation`, `insurance`, `orderbook.1000`, Bybit/Deribit-Options-Tickern, `tickers_1h`, `deribit/orderbook`,
  `markprice.options`:** Daten ab 2026-06 = Live-Stroeme, vollstaendig Zone K (vor Kohorte 1 nur SK0) [F Register 2/6]. Dok 5s
  Walk-forward mit Train/Validierung/Test auf diesen Stroemen wuerde K vor jeder Registrierung oeffnen - **nicht zulaessig**. Weg:
  R-1 (Registrierung Kohorte 1, Blicke quartalsweise).
- **Cross-Venue (H5) und Binance-/Deribit-Trades 2025..06/2026:** Zone V (ein Blick je Familie, blind) bzw. K; kein X-Anteil.
- **BTC/ETH-Mikrostruktur 2024-07..2026-06** ("Brachland", Sweep 4.6): weder X noch konfirmierbar, solange P-13 nicht entschieden ist.
- **Intraday-Statistiken auf BTC/ETH in V/K:** A2-Maske [07:00, 08:30) UTC Pflicht (Sweep 4.7) - betrifft auch Dok-3-Achse 3.
- **Formatbruch** `orderbook.500` (X) gegen `orderbook.1000` (K): X-Befunde sind Exploration; jede K-Pruefung muss die Aera-Grenze
  als Design-Parameter fuehren (F.1).

---

## 6. Gesamturteil je Dokument

| Dok | Urteil [U] | Drei staerkste Gruende |
|---|---|---|
| 1 PRD Physics Edge | **ablehnen** (als PRD); keine eigene Ideenquelle ueber Dok 5 und die IK-Karten hinaus | (1) Governance: "Approved", Live-Canary-Kapital, Kelly, ungebundene Meta-Fusion, GPU - Konflikt mit kein Live-Order-Code, DEC-57, Registry-Disziplin (1-22..1-25). (2) Kernhorizont 50..550 ms: perfektes Orakel 0,2..0,5 bp gegen 11 bp, und unterhalb des 200-ms-Buchtakts unserer Daten nicht einmal messbar (Z-02, Z-27, R calc A/I). (3) Fuenf der acht Saeulen sind Analogien ohne pruefbaren Mechanismus (LIGO, Hydrodynamik, Quantensysteme, STDP/Resonanz, Ising), die uebrigen sind in der Akte tot (D.2, D.6, H-04b) oder schon Karten (IK-01, IK-04); mehrere Zahlen sind innerlich widerspruechlich oder unmoeglich (Z-01, Z-30, Z-33). |
| 2 Seismologie | **als Ideenquelle verwerten** (Formalismus), Edges ablehnen | (1) ETAS-Formalismus und n-Formel sind korrekt und decken sich mit F9/C-27 - Grundlage fuer R-1/R-2. (2) Die empirische Basis ist ein einzelner versiegelter K-Tag mit innerem Widerspruch (gamma 0,723 gegen eigene Quantile, Z-06) plus eine nicht in der Akte belegte Quelle (3.1); die Absorptionsthese ist mit unseren Stroemen nicht pruefbar. (3) Beide Edges sind unter der Wand, nutzen unerreichbare Schwellen (IAR, p <= 1, Z-13) und sitzen in einem Ausfuehrungspfad (OMS). Zusaetzlich Fremdoeffnung (3.4). |
| 3 Thermodynamik | **ablehnen** | (1) Edge A ist eine Wiederholung von H-04/H-04b (Lead-Lag, 80x unter der Wand), Edge B baut auf Permutationsentropie (D.6) - beides ohne Nicht-Wiederholungs-Nachweis (C.1). (2) Datenunmoeglichkeit: DVOL stuendlich, L2 200 ms, MPE-"Kollaps" ist Kurzfenster-Artefakt (Z-16, Z-18). (3) Ising/Onsager/MEPP ohne messbare Abbildung, und die "2. Ordnung" widerspricht Dok 2 desselben Pakets (3.3); Gebuehren und Latenz nicht kanonisch (Z-21). |
| 4 Biophysik | **als Ideenquelle verwerten** (nur Theorieetikett), Edges ablehnen | (1) Die Wurzelgesetz-Herleitung ist ein brauchbares Theorieetikett fuer IK-01. (2) APRH ist Spread-Capture (D.1), Lotka-Volterra ist mit Entsperrbedingung bereits abgelehnt (Exkurs S2), LPB-Perkolation misst nur die eigene Schwellendefinition (R calc K). (3) Formel- und Faktenfehler (I_c, Spread 50 -> 0,5 USDT, Tickraster; Z-24, Z-26). Rest als R-7. |
| 5 Cascade Intelligence | **teilweise uebernehmen** (als Methodenquelle fuer R-1..R-3, R-5), nicht als PRD | (1) Methodisch das staerkste Dokument: Nicht-Ziele, Modelltreppe mit Poisson-Null, staerkste Baseline, Negativkontrollen, Ablationen, Label-Einfrieren, `ts_available`, Clauset-Protokoll - weitgehend kompatibel mit C.13/C.14/DEC-39/DEC-53. (2) Gates ohne alpha/Power/SESOI/Selektions-K/Positivkontrolle und ein Tradingnutzen-Gate gegen C.2/E2 (5.1); Horizont 5 s..5 min ist nach Mission nur Kosten-/Stressmessung. (3) Fast alle Zielstroeme liegen in Zone K; sofort geht nur die liquidationsfreie Zone-X-Fassung (5.2/5.3). |
| 6 KI-Trading-Edge | **ablehnen** | (1) Edge "n > 1" ist D.2 und widerspricht Dok 2. (2) "Freigegeben", Stop-Limit-Ausfuehrung, Live Deployment ab Woche 10, TFT-Fusion - F. (3) Inhaltlich vollstaendig von Dok 5 (besser) und den IK-Karten abgedeckt; Coulomb-Stress und Ginzburg-Landau ohne Abbildung. |

### Kurzfassung an den Orchestrator (12 Zeilen)

1. Sechs Uploads geprueft (66 Vorschlaege, Mehrfachklassen): 31x E (Analogie/nicht falsifizierbar), 24x C (unter der Wand), 15x B (in 2.0 tot), 14x F (Governance), 20x A/A(neg) (schon im Programm oder verworfen), D nur als Teilklasse (3x), keine Zeile rein D.
2. Kernhorizonte 50..550 ms: perfektes Orakel 0,2..0,5 bp gegen 11 bp; `orderbook.1000` laeuft im 200-ms-Takt, DVOL stuendlich - die behaupteten Vorlaeufe sind auf unseren Daten nicht einmal messbar.
3. Richtiges steht schon in der Akte (IK-01 Wurzelgesetz, IK-02 Queue/First-Passage, IK-04 Multifraktal, F9/C-27 ETAS, WP-11 Resilienz); Lead-Lag, PE, Spread-Capture, Branching-Schwellen, LV, CSD, TDA sind tot bzw. verworfen.
4. Zahlen: "Garcia Seuma (2026)" nicht in der Akte (naechster Eintrag arXiv 2607.27070 [sek]); n 0,1..0,2 und 88 % UNBELEGT und mit unseren Stroemen nicht pruefbar.
5. Innere Widersprueche: p < 1e-4 mit 1.000 Surrogaten unerreichbar; gamma 0,723 gegen eigene Quantile (max/Summe 0,008 statt ~0,28); 16 CPCV-Pfade aus 6 Bloecken unmoeglich; SNR-Optimum falsch; Benchmarks = exakte Kernsummen; 1. gegen 2. Ordnung im selben Paket.
6. Governance: Dok 1/2/3/4/6 enthalten Ausfuehrungslogik, Kelly, GPU-Pflicht, "Approved/Freigegeben", Live-Kapital - Konflikt mit kein Live-Order-Code, DEC-57, Registry.
7. Fremdoeffnung: Dok 2 nennt Verteilungskennzahlen eines Zone-K-Liquidationstages und BTC-Preisniveaus aus V/K - als Oeffnung durch Fremdquelle buchen (DEC-97 A-3), Tag auf C.17-Liste, Rohwerte nicht ins Repo.
8. Dok 5 als Methodenquelle uebernehmen: Modelltreppe, Baselines, Negativkontrollen, Label-Einfrieren, ts_available; fehlend: alpha/Power/SESOI/Selektions-K (H1 allein K ~24), Positivkontrolle; Tradingnutzen-Gate verletzt C.2/E2.
9. Siegel: Liquidationen, L2 1000, Options-Ticker sind rein K (vor Kohorte 1 nur SK0); Cross-Venue ohne X-Anteil; sofort geht nur die liquidationsfreie Fassung auf Trades 2020..2024-06 und L2 500 2023-01..2024-06.
10. Rettbar netto eine Karte: R-1 Liquidations-Kaskaden (SK0 jetzt; ETAS/Omori/n ohne Schwelle als K-Messprogramm ab Kohorte 1, Abnehmer Stress-Kostenfenster/H-21-Nachfolge); bedingt R-2 (Hawkes auf X-Trades als Positivkontrolle).
11. R-3 (Mehrstufen-Depletion), R-5 (Mehrskalen-Relaxation), R-6 (Multifraktal), R-7 (L2-Lueckenstatistik) sind Ausgaben von IK-02/IK-04/IK-01; R-4 (TE Tagesbasis) nur als Nebenstatistik in IK-10/F7.
12. Urteile: Dok 1, 3, 6 ablehnen; Dok 2, 4 als Ideenquelle (Formalismus/Theorieetikett); Dok 5 teilweise uebernehmen (Methodik), nicht als PRD.

---

## Anhang A: Rechenweg

`calc/physics_calc.py` (nur Formeln und synthetische Monte-Carlo-Ziehungen mit festem Seed 20261102; keine Marktdaten),
Ausgabe `calc/physics_calc.out`. Abschnitte: A perfektes Orakel sqrt(2/pi) sigma_d sqrt(tau/86400) mit sigma_d 262 bp [F];
B 1/lambda; C min p = 1/(B+1); D b ln 10; E Darling-Grenzwert E[max/Summe] -> 1 - gamma [sek], MC Pareto(0,723) mit N der
Dok-Angabe, max/Q75 gegen (N/4)^(1/gamma); F 1/(1-n), n/(1-0,88); G IAR-Erreichbarkeit; H Ereignisrate und Refits; I Takt aus
Katalogzeilen [F]; J Obergrenze ln(min(W,24))/ln 24 und MC unter Gleichverteilung; K P(V > mu - 0,5 sd) fuer Gauss und Lognormal;
L argmax der Dok-SNR-Formel; M FHN-Knie (eps -> 0); N CPCV-Pfade k/N C(N,k) [sek]; O Benchmarksummen; P E[max z] durch
Quadratur; Q S_crit; T Embargo gegen DEC-63.

## Anhang B: Vorgehen, Grenzen, Offenlegung

- Gelesen: die sechs Uploads vollstaendig (Dok 5/6 als Textextrakt) und die Pflichtlektuere; ergaenzend Kompendium A/B/E/F,
  Exkurs S2 und Synthese, R3 K-34, 2.0-PRD (C-27..C-30), DEC-57, DEC-63, WP-10(B)-Eintrag.
- Kein Code aus den Uploads ausgefuehrt; keine Marktdaten, kein Harvest-Client; nichts im Repo geaendert oder committed.
- **Offenlegung:** Ein erster `grep` nach "garcia/seuma" lief versehentlich mit `--include=*.json` auch ueber `state/runs/`
  (einschliesslich der Siegeldateien `*_L_window_sealed.json`; keine `.csv`). Es war eine reine Mustersuche nach dem Namen mit
  null Treffern im gesamten Repo; kein Dateiinhalt wurde angezeigt oder gelesen. Die Suche wurde mit `--exclude-dir=runs`
  wiederholt (Abschnitt 3.1). [U] Kein Informationsfluss aus den Siegeldateien; der Orchestrator entscheidet, ob ein
  Konto-Vermerk noetig ist.
- Diese Datei enthaelt aus Dok 2 abgeleitete Verhaeltnisse eines Zone-K-Tages (Z-06) und den b-Wert; vor einer Uebernahme ins
  oeffentliche Repo bitte gegen 3.4 pruefen. `calc/physics_calc.py` enthaelt die Dok-Rohangaben dieses Tages und gehoert nicht
  ins Repo.
- Alle Literaturaussagen [sek] sind aus dem Gedaechtnis; Primaerquellen (insbesondere zur Bybit-Versicherungsfonds- und
  Liquidationsmechanik und zu "Garcia Seuma") sind zu beschaffen (P-11 Netzfreigabe offen).

## Anhang C: Was nicht folgt

Kein Verdikt, keine Registrierung, keine Regelaenderung; kein Datenauftrag ausgeloest; keine Kostenzahl gemessen. Die
Klassifikation ist ein Review-Urteil und ersetzt keine Herleitung; die sieben Skizzen sind keine Registrierungsempfehlungen
(Kohorte 1 und Zustandsmaschine bleiben massgeblich).
