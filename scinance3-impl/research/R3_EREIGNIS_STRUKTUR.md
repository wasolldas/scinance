# R3 -- Ereignis- und struktur-getriebene Ansaetze auf dem vorhandenen Harvest

> Quant-Researcher R3, Scinance-3.0-Phase-3. Read-only auf das Repo.
> Pflichtlektuere gelesen: `ERKENNTNIS_KOMPENDIUM.md` (vollstaendig, A-F),
> `INFRA_OPS_MAP.md` (1, 2, 6), `FINAL_PRD.md` (1, 2, 5, 8), zusaetzlich
> `DATA_INVENTORY_2026-08-10.md`, `STRATEGIE_KANDIDATEN_2026-08-20.md`,
> `WP1_L2_ZENSUS_BEFUND_2026-08-14.md`, `hypothesis_registry.md` (H-09..H-13),
> `wp5_optchain/census.py`, `wp6_optstress/extract.py`, `c13_tailshape/*`.
>
> **Nummerierung:** K-31..K-37 ist R3-lokal gewaehlt (kollisionsfrei zu C-xx/H-xx);
> der Orchestrator kann umnummerieren.
>
> **Belegdisziplin:** Fuenf Volltexte waren aus dieser Umgebung nicht abrufbar
> (Egress-Sperre auf sciencedirect.com, arxiv.org, acfr.aut.ac.nz,
> cryptodatadownload.com, bybit-exchange.github.io). Wo eine Zahl nur aus einem
> Suchtreffer-Abstract stammt, ist sie als **sekundaer belegt** markiert; wo sie
> gar nicht belegt ist, als **unbelegt**. Nichts ist erfunden.

---

## 0. Der eine Befund, der diesen Auftrag traegt

Die im Brief benannten "kaum genutzten" Stroeme haben ein **gemeinsames
Problem und eine gemeinsame Loesung**.

**Das Problem:** Alle reichen Ereignis-/Struktur-Stroeme sind JUNG.
Bybit-Options-Ticker ~66 Tage, `deribit/tickers` ~61 Tage,
`markprice.options` ~78 Tage, `allLiquidation` ~66 Tage, `insurance` ~66 Tage,
`rest.openInterest` ~136 Tage (alle Stand 2026-09-02, hochgerechnet aus der
Inventur vom 2026-08-10). Eine Hypothese, deren Ereignis der Freitags-Verfall
ist, hat auf der Optionskette heute **~10 Ereignisse**. Genau diese Falle hat
H-10 (N_pointer=0) und H-13 (2 Snapshot-Tage) bereits einmal produziert. Jeder
Kandidat, der die Kette in seinem HAUPT-Gate braucht, ist heute nicht
registrierbar -- und das jetzt zu ignorieren waere die dritte Wiederholung
desselben Fehlers.

**Die Loesung:** Bei den drei staerksten Kandidaten laesst sich der
**Ereignis-Takt vom Ereignis-Inhalt trennen**. Der Verfallskalender
(jeden Freitag 08:00 UTC, letzter Freitag im Monat, Quartalsende) ist
deterministisch, ex ante bekannt und reicht ueber die **gesamten 6 Jahre**
des WP-0-Bar-Caches zurueck -- er braucht kein einziges Byte Optionsdaten.
Ebenso ist die Deribit-DVOL-Historie oeffentlich ab 2021-04-01 abrufbar
(s. K-36) und die Bybit-Funding-Historie oeffentlich vollstaendig nachladbar
(s. K-34). Damit wandern drei Kandidaten von "N=10" auf "N=100..300".

Zweiter tragender Punkt: **die Wand ist bei drei Kandidaten nicht zu
umgehen, sondern zu MESSEN.** Die "~15 bps inkl. Slippage" sind seit dem
FINAL_PRD eine Annahme; K-35 macht daraus eine Zahl. Das ist kein Alpha,
aber es ist die Groesse, an der jedes bisherige PARK-Urteil haengt.

---

### K-31 EXP-CLOCK - Options-Verfallsfenster als deterministischer Ereignis-Kalender (kettenfrei)

- **Ertragsquelle:** **Ereignis.** Krypto-Options-Market-Maker sind im Aggregat
  netto short Gamma auf kurzlaufenden Kontrakten (Retail und Fonds kaufen
  Konvexitaet, MM verkaufen sie). Ihr Delta-Hedge ist in den letzten Stunden
  vor dem Verfall maximal preis-sensitiv und faellt um 08:00 UTC schlagartig
  auf null. Beide Boersen setzen den Settlement-Preis als **30-Minuten-TWAP
  des Index von 07:30 bis 08:00 UTC** (Deribit: 450 Snapshots im 4-Sekunden-
  Takt; Bybit ebenso 30-Minuten-Index-Mittel) -- das ist ein mechanisch
  erzwungenes Fenster, in dem hedge-getriebener, preis-unelastischer Fluss
  konzentriert auftritt und danach verschwindet. Wer zahlt: die
  Options-Halter/-Schreiber ueber den Vermoegenstransfer am Settlement, und
  die Liquiditaetsnehmer im Fenster ueber den temporaeren Impact.
- **Horizont & Instrument:** Stunden (Ereignisfenster 06:00-12:00 UTC um
  Freitag 08:00 UTC); Bybit-Perp BTCUSDT/ETHUSDT, **einbeinig**, Taker oder
  passiver Maker-Einstieg. Kein Optionsgeschaeft noetig.
- **Literatur/Evidenz:**
  - Ni, Pearson, Poteshman (2005), *Stock price clustering on option expiration
    dates*, J. Financial Economics 78(1), 49-87: an Verfallstagen werden
    Renditen optionierter Aktien im Mittel um **mindestens 16,5 bps**
    verzerrt; Ursache laut Autoren Hedge-Rebalancing der MM. (Abstract-Zahl,
    Volltext egress-gesperrt -- **sekundaer belegt**.)
  - Blasco, Corredor, Satrustegui (2023), *Is there an expiration effect in the
    bitcoin market?*, Int. Review of Economics and Finance 85, 647-663:
    signifikante Aenderungen in Volumen, Volatilitaet und Rendite um die
    Monatsverfaelle; Effekt **nicht homogen ueber Boersen**, staerker je
    naeher am Verfallszeitpunkt. Keine bps-Zahl aus dem Abstract ermittelbar
    (**sekundaer belegt, Groesse unbelegt**).
  - Finance Research Letters (Juni 2026), *Bitcoin option expiration, gamma
    exposure, and intraday price reversals* (Autoren nicht ermittelbar,
    Volltext gesperrt): **V-foermige Umkehr** um Deribit-Verfaelle --
    signifikant negative Vor-Verfalls-Rendite, danach Umkehr; konzentriert an
    Tagen mit hohem ATM-Open-Interest, **am staerksten bei negativem
    Netto-GEX**; Handelsaktivitaet steigt im Deribit-Perp und an den
    Index-Spot-Boersen; bezifferter Transfer im Fenster **07:00-08:00 UTC:
    ~0,5 Mio USD** von Call-Haltern zu Call-Schreibern. (**sekundaer belegt**.)
  - Gegen-Evidenz, die zu zitieren ist: Max-Pain-"Pinning" als Preis-Magnet
    ist in der Praktiker-Presse populaer, aber empirisch mehrfach gescheitert
    (Juni-2026-Verfall: Spot ~11.000 USD unter dem Max-Pain-Level trotz
    10,6 Mrd USD Notional). Der peer-reviewte Befund ist eine **Umkehr um den
    Verfall**, KEIN Strike-Magnet. K-31 misst darum die Umkehr, nicht Pinning.
- **Erwartete Groessenordnung vs. Friktion:** Aktien-Analogon 16,5 bps liegt
  bei **1,1-1,5x** der Wand (11 bps Taker-RT / 15 bps inkl. Slippage;
  4 bps Maker-RT). Krypto-Groesse in bps ist **unbelegt** -- der einzige
  bezifferte Krypto-Wert (0,5 Mio USD) laesst sich ohne das Ereignis-Notional
  nicht in bps uebersetzen. Ehrliche Erwartung: 10-40 bps brutto im
  30-60-Minuten-Fenster. **Das ist der erste Kandidat des Programms, dessen
  A-priori-Groessenordnung ueberhaupt in der Naehe der Wand liegt** -- alle
  gemessenen Rohkanten lagen bisher 80-500x darunter.
- **Daten:** **Nichts nachzuladen.** WP-0-Bar-Cache (5 Symbole, 10.054
  Cache-Tage, 14,4 Mio Minutenbars) plus ein deterministisch erzeugter
  Verfallskalender (jeder Freitag 08:00 UTC; letzter Freitag im Monat;
  Quartalsende). Optionsstroeme werden im Haupt-Gate **nicht** benutzt.
  - *Datenqualitaets-Fussnote:* Der Bar-Cache friert nur Manifest-DONE-Tage
    ein und ist SHA-256-fingerprinted; die 41-74-%-L2-Luecken und die
    ETH-Options-Luecke 22.-27.08. treffen diesen Kandidaten **gar nicht**,
    weil weder L2 noch Optionsdaten eingehen. Einzige echte Fussnote: das
    Bybit-Listing-Datum je Symbol (SOL/BNB ab 2021-06-29) begrenzt das
    Placebo-Panel, nicht das Haupt-Gate.
- **Rechenaufwand:** CPU, Minuten. Bar-Cache-Lesen + Ereignis-Aggregation +
  Block-Bootstrap (1.000 Reps). Keine GPU. PC-tauglich, Sandbox-tauglich.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Metrik:** mittlere log-Rendite im Settlement-Fenster [07:30, 08:00) UTC
    (r_pre) und im Fenster [08:00, 09:00) UTC (r_post) an Verfalls-Freitagen,
    je Symbol, aus dem Bar-Cache.
  - **Urteilstragende Groesse ist immer eine DIFFERENZ**, nie ein Rohmittel:
    Delta = Mittel(Verfalls-Freitage) - Mittel(Placebo-Slots).
  - **Drei vorregistrierte Placebos (DEC-31/33-Pflichtzeile):**
    (P1) Nicht-Verfalls-Freitage im selben Uhrzeit-Fenster;
    (P2) **Nicht-Freitags-08:00-UTC-Slots** -- dieser Placebo ist zwingend,
    weil Bybits USDT-Perp-Funding um 00:00/08:00/16:00 UTC abgerechnet wird
    (vom Programm vor Registrierung gegen die Boersen-Doku zu verifizieren).
    Ohne P2 misst K-31 H-01 neu, und H-01 ist DROP;
    (P3) alle uebrigen Tagesstunden als unbedingte Baseline.
  - **Negativ-Panel als Gratis-DEC-39-Fixture:** XRP/BNB (und SOL vor 2025)
    haben ueber den Grossteil der Historie **keine liquide Optionskette** --
    dort MUSS Delta ~ 0 sein. Das ist ein echtes negatives Fixture aus
    Realdaten, kein synthetisches.
  - **REZENZ-Klausel:** urteilstragend sind zwei disjunkte **12-Monats**-Fenster,
    W1 = 2024-09-01..2025-08-31, W2 = 2025-09-01..2026-08-31. Begruendung fuer
    12 statt 6 Monate: (i) Power (s. Rauschboden), (ii) der Welle-6-Querbefund
    datiert den D3-Uebergang auf ~Mitte 2024, beide Fenster liegen also
    vollstaendig in der juengsten Aera. 2020-2024 ist rein deskriptives
    Aera-Profil und **nicht** urteilstragend.
  - **Rauschboden (hergeleitet, nicht gesetzt):** BTC-Tagesvol ~2,5% ->
    Stundenrendite-SD ~51 bps -> 30-Minuten-SD ~36 bps. Je Symbol und
    12-Monats-Fenster N ~ 52 Verfalls-Freitage; gepoolt BTC+ETH N ~ 104 ->
    SE(Delta) ~ 36/sqrt(104) ~ **3,5 bps**.
  - **Schwelle:** |Delta| >= **12 bps** (~3,4 SE) mit **gleichem Vorzeichen**
    in BEIDEN 12-Monats-Fenstern, Block-Bootstrap-p <= 0,05 (Bloecke = ganze
    Handelstage, 1.000 Reps), UND Delta gegen alle drei Placebos gleichzeitig.
    12 bps ist bewusst UNTER der 15-bps-Wand gewaehlt: das Gate ist
    kapitalfrei; die Wand kommt in einer separaten K-31b-Tradability-
    Registrierung (H-04 -> H-04b-Doktrin), die hier **nicht** impliziert ist.
  - **FDR-Familie:** **F-EXPCLOCK** -- 2 urteilstragende Symbole x 2 Fenster
    x 2 Fenstertypen (r_pre, r_post) = 8 Zellen, BH alpha = 0,10. Das
    Negativ-Panel ist NICHT Teil der Familie (Placebo-Konvention aus H-09).
  - **Feasibility (GL-012-Check):** bestanden fuer die 12-Monats-Fassung
    (12 bps = 3,4 SE). **Verfehlt fuer eine 6-Monats-Fassung** (N ~ 52,
    SE ~ 5,0 bps, 12 bps = 2,4 SE, in zwei Fenstern gleichzeitig
    unwahrscheinlich) -- die Fensterlaenge ist damit VOR dem Lauf aus der
    Arithmetik begruendet und nicht nachtraeglich waehlbar.
- **Was ihn a priori toetet:** (1) P2 erklaert den Effekt vollstaendig -- dann
  ist es der Funding-Settlement-Takt und damit H-01, tot. (2) Vorzeichenwechsel
  zwischen W1 und W2 (hartes Ein-Fenster-Kriterium, wie H-20). (3) Delta lebt
  nur im deskriptiven Aera-Profil vor 2024 (REZENZ-Klausel, wie H-22).
  (4) Das Negativ-Panel zeigt denselben Effekt -> es ist ein Wochentags-/
  Uhrzeit-Artefakt, kein Verfallseffekt.
- **Bezug zu Kompendium D/E:** Wiederholt **D-12 nicht** (H-20 Tail-Aftermath:
  dort ist das Ereignis endogen ueber eine 3,5-sigma-Preisbewegung DEFINIERT
  und die Sigma-Nachsuche verboten; hier ist das Ereignis exogen-kalendarisch
  und ex ante bekannt -- es gibt keinen Freiheitsgrad, den man nachsuchen
  koennte). Wiederholt **H-01 nicht** (dort eine Funding-Pressure-Entry-Regel
  auf Minutenskala mit Time-Stop; hier ist derselbe Settlement-Slot der
  PLACEBO). Wiederholt **D-14 nicht** (H-24: dort Minuten-Netto-FLUSS als
  Praediktor; hier keine Flussvariable, nur der Kalender). Nutzt den offenen
  Faden aus Programm-Konstante 16 / DATA_INVENTORY Par. 4.5: die lueckenlose
  5-Symbol-Mehrjahres-Tickhistorie, die **von keiner Hypothese als
  Ereignis-Panel genutzt** wurde.
- **Vertrauen:** **mittel.** Der Mechanismus ist in Aktien seit 20 Jahren
  belegt, in Krypto peer-reviewed nachgewiesen, und die Datenlage ist die
  beste im ganzen Programm (kein Nachladen, N ~ 200, sauberes Negativ-Panel).
  Abzug: die einzige Krypto-Groessenzahl ist nicht in bps uebersetzbar, und
  selbst ein PASS liegt vermutlich knapp an der Wand.

---

### K-32 GEX-KOND - Gamma-Exposure aus der Kette als Konditionierer von K-31 (data-gated)

- **Ertragsquelle:** **Ereignis/Struktur.** Der K-31-Effekt sollte nach der
  Theorie nur dann existieren, wenn die Haendler netto SHORT Gamma sind
  (dann verstaerkt der Hedge die Bewegung, positives Feedback); bei netto
  LONG Gamma daempft der Hedge und der Effekt kehrt sich um. GEX ist aus der
  gehaerteten Kette berechenbar: GEX = Summe_k OI_k * Gamma_k * S^2 * s_k,
  wobei s_k das (in Krypto strittige) Haendler-Vorzeichen ist.
- **Horizont & Instrument:** wie K-31 (Stunden, Bybit-Perp einbeinig); die
  Kette liefert nur die Konditionierungsvariable.
- **Literatur/Evidenz:**
  - Finance Research Letters (2026), s. K-31: Umkehr **am staerksten bei
    negativem Netto-GEX** und an Tagen mit hohem ATM-OI -- die direkte
    Krypto-Evidenz fuer genau diese Konditionierung (**sekundaer belegt**).
  - *Gamma positioning and market quality*, J. of Economic Dynamics and
    Control (2024), Artikel S0165188924000721 -- Aktienmarkt-Mechanismus
    (Volltext gesperrt, **sekundaer belegt**).
  - Glassnode Research, *Introducing: Taker-Flow-Based Gamma Exposure*
    (Praktiker-Quelle): begruendet ausdruecklich, dass die aus dem
    Aktienmarkt importierte Vorzeichen-Konvention (Calls = Haendler long,
    Puts = Haendler short) in Krypto **nicht gilt** und durch die
    Taker-Richtung ersetzt werden muss; Krypto-MM tragen strukturell
    haeufiger negatives GEX als Aktien-MM. **Das ist der entscheidende
    C-14-Warnhinweis dieses Kandidaten:** ein importiertes Vorzeichen ohne
    Erreichbarkeits-/Gueltigkeitspruefung ist der Hawkes-rho-Fehler in neuem
    Gewand (D-2).
- **Erwartete Groessenordnung vs. Friktion:** Die Literaturhoffnung ist eine
  Verdopplung bis Verdreifachung des K-31-Effekts in der GEX<0-Teilmenge
  (also 25-80 bps in ~40-50% der Ereignisse) und ein Vorzeichenwechsel in der
  GEX>0-Teilmenge. Fuer Krypto **unbelegt ausser durch die eine FRL-Arbeit**.
- **Daten:** `bybit/tickers` (die Options-Ticker liegen dort neben den
  Perp-Tickern, DEC-46; Felder `delta`, `gamma`, `vega`, `openInterest`,
  `underlyingPrice` sind in `wp5_optchain/census.py` bereits verdrahtet),
  `deribit/tickers` (5.964 Symbole, Greeks + OI je Strike),
  `deribit/markprice.options`, plus `data/optchain_snaps/` (REST-Sampler,
  15-Min-Takt seit 2026-08-24). **Nachzuladen fuer die Vorzeichenfrage:** ein
  Options-**Trade**-Tape je Instrument (Taker-Richtung) -- `deribit/publicTrade`
  deckt nur die PERPETUALS, nicht die Optionen. Das waere ein neuer
  Harvester-Auftrag (Deribit `trades.option.any.raw` bzw. Bybit
  `publicTrade.{option}`), Volumen klein, Aufwand liegt beim Harvest-Projekt.
  - *Datenqualitaets-Fussnote (die haerteste im ganzen Papier):*
    Bybit-Options-Ticker ~66 Tage, `deribit/tickers` ~61 Tage --
    **~9-10 Verfalls-Freitage**. Die **ETH-Luecke 2026-08-22 08:00 bis
    08-27 08:00 UTC liegt exakt IM Settlement-Fenster** eines Verfalls und
    ist fuer 22.-24.08. **endgueltig quellenlos** (E-8); das kostet mindestens
    einen ETH-Ereignistag ersatzlos. Die Bybit-Bid/Ask-Historie vor
    2026-08-24 ist nicht unabhaengig verifiziert (E-9). Fuer OI/Greeks (nicht
    Quotes) ist der WS-Ticker die einzige Quelle vor dem 24.08.
- **Rechenaufwand:** CPU, Minuten (Kettenaggregation je Verfallstag).
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Interaktions-Gate, nicht Haupteffekt-Gate:** Delta(GEX<0) - Delta(GEX>=0)
    >= **15 bps**, gleiches Vorzeichen in beiden Fenstern, Permutations-p
    <= 0,05, FDR **F-GEX**.
  - **Struktureller Nulleffekt (Pflicht):** GEX waechst mechanisch mit OI und
    mit S^2. Eine Zweiteilung nach GEX ist damit teilweise eine Zweiteilung
    nach Marktgroesse und Vol-Niveau -- und Ereignisse mit hoher Vol haben
    per Konstruktion groessere |Rendite|. Der Nulleffekt ist vorab durch
    **Permutation der GEX-Etiketten ueber Ereignisse bei erhaltenem
    Ereignis-Vol-Rang** auszurechnen; die 15 bps sind gegen diese Nullbreite
    zu kalibrieren, nicht gegen 0.
  - **Vorzeichen-Identifikation als GATE-Vorbedingung, nicht als Annahme:**
    ohne Options-Taker-Tape ist s_k nicht identifiziert. Vorregistrierte
    Regel: entweder das Tape existiert, oder es werden BEIDE Konventionen
    (Aktien-Import vs. Taker-Fluss) als getrennte, in der FDR-Familie
    gezaehlte Zellen gefahren -- nie eine davon still gewaehlt.
  - **N-Floor / Entsperr-Bedingung (nicht senkbar):** >= 40 Verfalls-Freitage
    mit lueckenloser Kette je Symbol in JEDEM von zwei disjunkten Fenstern.
    Bei Start 2026-06-28 und ~52 Freitagen/Jahr ist das **fruehestens ~2027-05**
    erreicht. Bis dahin: **nicht registrieren.**
- **Was ihn a priori toetet:** (1) der N-Floor -- heute ~10 Ereignisse, das ist
  exakt die H-10/H-13-Falle; (2) die Vorzeichen-Mehrdeutigkeit ohne
  Options-Tape (dann ist K-32 kein Kandidat, sondern ein Harvester-Auftrag);
  (3) wenn K-31 selbst DROP ist, ist die Konditionierung gegenstandslos --
  **K-32 ist strikt nachgelagert.**
- **Bezug zu Kompendium D/E:** Nicht in D. Wiederholt **H-13 nicht** (dort
  GPD-xi-FORM der risikoneutralen Dichte an zwei Snapshot-Tagen; hier ein
  OI-gewichtetes Gamma-Aggregat als Ereignis-Konditionierer -- andere
  Groesse, anderer Zweck, andere Fenster). Wiederholt **D-17 nicht**
  (Tardis-Options-Chain-Kandidaten starben am 2-Tage-Sampling; hier
  taegliche Live-Kette). Nutzt E-3 (H-13-Kettenfaden) und E-9
  (Bybit-Options-Historie) als Datenfaden. Traegt aktiv die **D-2-Lehre**
  (importierte Schwelle/Konvention zuerst auf Erreichbarkeit pruefen).
- **Vertrauen:** **mittel** fuer den Mechanismus (direkte Krypto-Evidenz
  vorhanden), **niedrig** fuer Registrierbarkeit vor Mitte 2027.

---

### K-33 X-PULL - Cross-Venue-Dislokation als Stunden-Signal, einbeinig auf Bybit

- **Ertragsquelle:** **Struktur.** Bybits Perp weicht episodisch vom
  venue-uebergreifenden Konsens (Binance-Perp, Deribit-Perp, Bybit-Spot) ab,
  weil lokaler Zwangsfluss (Liquidations-Engine, eine grosse Marktorder) nur
  ein Buch trifft. Die Rueckkehr ist mechanische Konsensbildung, keine
  Richtungsprognose. Wer zahlt: derjenige Fluss, der Bybit lokal aus dem
  Konsens drueckt.
- **Horizont & Instrument:** 1-6 Stunden. **Nur ein Bein, nur auf Bybit** --
  Deribit und Binance bleiben reine Messquellen, damit die
  Programm-Randbedingung (Deribit ist Datenquelle, kein Handelsplatz)
  eingehalten ist. Das ist der wesentliche Unterschied zu jeder klassischen
  Basis-Arbitrage.
- **Literatur/Evidenz:**
  - *Fragmentation, Price Formation and Cross-Impact in Bitcoin Markets*,
    Applied Mathematical Finance (2022): Cross-Impact zwischen Krypto-Boersen
    existiert und ist messbar -- aber **keine Stunden-Horizont-Zahl**
    (**sekundaer belegt**).
  - Praktiker-Quellen (arbitragescanner.io, Sharpe/Glassnode-Blogs):
    Dislokationen von **40-60 bps nur in Liquidations-Kaskaden**, sonst
    "snap together within seconds". **Unbelegt** (Blog-Niveau), aber
    richtungsweisend fuer die A-priori.
  - Programm-intern: H-04b (Lead-Lag, PARK), H-12 (RMT, DROP), H-14 (Graph,
    invalide) -- **alle auf Sekundenskala**, keiner auf Stunden. H-04b hat
    ausdruecklich nur den Sekunden-Fall mit 300-ms-Latenz-Haircut getoetet.
- **Erwartete Groessenordnung vs. Friktion:** Einbeinig -> 11 bps Taker-RT
  (15 inkl. Slippage). Die Dislokation muss also **> ~20 bps** sein UND
  laenger als die Ausfuehrungszeit bestehen. Ehrliche Erwartung: Median
  1-3 bps (**unbelegt** -- genau das misst Stufe 1); alles haengt an der
  TAIL-Haeufigkeit.
- **Daten:** Bar-Cache existiert nur fuer Bybit; ein Binance-/Deribit-Bar-Cache
  ist derselbe Code (`exchange=` ist bereits Partitionsschluessel) -- kleiner
  WP. Abdeckung heute: `binance/publicTrade` BTC 519 Tage ab 2025-01-01,
  uebrige 4 Symbole je 128 Tage; `deribit/publicTrade` PERPETUAL je 126 Tage.
  **Billiger Nachlade-Pfad statt Trade-Backfill:** Binance-Futures-Klines
  (`/fapi/v1/klines`, oeffentlich, ohne Key, Jahre tief) -- ~5 Symbole x 6 Jahre
  x 1-min ~ 15 Mio Zeilen, Download in Stunden. Das ersetzt den teuren
  Trade-Backfill vollstaendig, weil auf Stundenskala nur der Preis gebraucht
  wird, nicht das Tape.
  - *Datenqualitaets-Fussnote:* Der Binance-Trade-Strom hat den
    FLAT/ENVELOPE-Dialekt-Bruch (silent-drop-Bug 2026-07-17) -- bei
    Kline-Nachladung faellt dieses Risiko weg. Der Deribit-Strom traegt die
    Umbenennung "BTC" -> "BTC-PERPETUAL" (2026-06-24) mit ~9 Ueberlappungstagen,
    die in H-14/H-17-Loadern bereits vereinigt werden musste -- wiederverwenden,
    nicht neu bauen. `binance/orderbook` (BTC nur 23 Tage) wird **nicht**
    gebraucht.
- **Rechenaufwand:** CPU. Backfill Stunden, Auswertung Minuten.
- **Kapitalfreies Mess-Gate (Entwurf) -- zweistufig, Stufe 1 ist der Killer:**
  - **Stufe 1 (ZENSUS, kein p-Wert, WP-4-Muster):** Verteilung von
    b_t = log(P_bybit / P_binance) auf Stundenrastern, ausgewiesen p50 / p90 /
    p99 / max und **N(|b| >= 20 bps) je Halbjahr**, je Symbol, getrennt nach
    Ruhe/Stress. **Vorab fixierte binaere Abbruchregel:** liegt
    N(|b| >= 20 bps) < **30 je Halbjahr**, ist der gesamte Kandidat ohne
    weiteren Aufwand tot (N-Floor, keine Schwellensenkung -- die WP-4-Lehre:
    eine Vorfrage, die den ganzen Ansatz binaer entscheidet, kommt zuerst).
  - **Struktureller Nulleffekt (Pflicht, DEC-31/33):** b_t enthaelt mechanisch
    (i) die Funding-Differenz beider Boersen (Barwert ueber 1 h ~
    (f_bybit - f_binance)/8) und (ii) den Unterschied der Index-Konstituenten.
    Beides ist VOR der Schwellenfestlegung auszurechnen und abzuziehen; der
    Rest ist die eigentliche Dislokation.
  - **Stufe 2 (nur bei bestandener Stufe 1):** bedingt auf |b_t| >= 20 bps die
    mittlere Bybit-EIGENE Rendite ueber [t, t+1h] in Richtung
    Dislokationsschliessung. Rauschboden: Stundenrendite-SD ~51 bps,
    SE = 51/sqrt(N_cond); bei N_cond = 60 also **6,6 bps**. Schwelle:
    mittlere bedingte Rendite >= **15 bps** (~2,3 SE) mit gleichem Vorzeichen
    in beiden Halbjahren, Block-Bootstrap-p <= 0,05, FDR **F-XPULL**.
    Ein IC-Gate ist hier explizit VERBOTEN: bei N_cond ~ 60 liegt der
    IC-Rauschboden 1/sqrt(60) = 0,13, eine 0,10-IC-Schwelle waere strukturell
    unerreichbar (GL-012-Analogon zu H-07).
  - **Anti-Gaming (DEC-13/16, unveraendert):** 11 bps Wand und 300-ms-Latenz-
    Haircut sind vor dem Lauf fixiert und werden nicht gesenkt.
- **Was ihn a priori toetet:** (1) Stufe 1 (Tail-Haeufigkeit unter 30);
  (2) die 20-bps-Ereignisse fallen per Konstruktion in Kaskadenminuten, in
  denen der Bybit-Spread und der Slippage-Aufschlag explodieren -- die
  15-bps-Annahme ist dort nachweislich falsch (das ist genau die Groesse,
  die K-35 misst; WP-6 hat den analogen Effekt auf der Optionsseite bereits
  quantifiziert). Wer K-33 ohne K-35 monetarisieren will, wiederholt den
  WP-6-Fehler.
- **Bezug zu Kompendium D/E:** Wiederholt **D-10 nicht** (H-12 RMT-
  Eigenstruktur: dort Tages-Eigenvektor-Lokalisierung, hier ein Preis-Spread
  auf Stundenraster), **D-11 nicht** (H-14 Graph-Ablation, andere
  Architektur UND anderer Horizont -- die Kompendium-D-Formulierung erlaubt
  eine Wiederholung ausdruecklich nur "mit Horizont-/Architektur-Neufassung
  als neue, eigens vorregistrierte Hypothese", genau das ist dies), und ist
  **kein H-04c** (H-04b war der Sekunden-Trade-Fluss-Lead mit Latenz-Haircut;
  hier ein Stunden-Preisniveau-Spread, kein Fluss).
- **Vertrauen:** **niedrig-mittel** fuer ein PASS; **hoch** fuer den Wert des
  Zensus (billiger, binaerer Killer einer ganzen Kandidatenfamilie -- exakt
  das Muster, mit dem WP-4 den gesamten Market-Making-Zweig in einem
  Nachmittag erledigt hat).

---

### K-34 LEV-STATE - OI-/Funding-Zustand als Verteilungs-Konditionierer (kein Richtungssignal)

- **Ertragsquelle:** **Struktur, als Risikomessung.** Hoher OI-Aufbau bei
  einseitigem Funding = Positionsueberhang mit mechanischer
  Zwangsverkaufsschwelle. Die Behauptung ist ausdruecklich **nicht**, dass
  die Richtung prognostizierbar ist (das waere D-14/H-24-Terrain), sondern
  dass die **FORM der naechsten Tagesverteilung** (Abwaerts-Semivarianz,
  Wahrscheinlichkeit einer 3,5-sigma-Stunde) zustands-abhaengig ist. Wer
  zahlt: die gehebelte Mehrheit ueber Liquidationsgebuehr und Impact.
- **Horizont & Instrument:** 1-5 Tage. Verwendung **nicht als Entry**, sondern
  als Gating-/Sizing-Variable fuer den einzigen lebenden Pfad
  (H-26/C-33 Short-Vol) und als datenbasierte Herleitung der heute frei
  gesetzten "24-h-Kill-Regel nach einer 3,5-sigma-Stunde".
- **Literatur/Evidenz:**
  - *Liquidation, Leverage and Optimal Margin in Bitcoin Futures Markets*
    (arXiv 2102.04591): Hebel/Margin-Mechanik erzeugt fette Raender
    (Volltext egress-gesperrt, **sekundaer belegt**).
  - *Where does the criticality live? Early-warning signals are
    event-heterogeneous across seven crypto-perpetual liquidation cascades*
    (arXiv 2607.27070): **Negativbefund** -- Fruehwarnsignale sind ueber
    Ereignisse hinweg heterogen (Titel/Abstract, Volltext gesperrt,
    **sekundaer belegt**). Dieser Befund ist der Grund, warum K-34 KEIN
    Vorhersage-Gate auf einzelne Kaskaden setzt, sondern ein
    Verteilungs-Gate ueber viele Tage.
  - *Anatomy of the Oct 10-11, 2025 Crypto Liquidation Cascade* (SSRN 5611392):
    ~19 Mrd USD Open Interest in 36 h vernichtet; stundenbasierte
    Ereignisstudie ueber 10 Coins, Binance mit Bybit-Cross-Validierung
    (**sekundaer belegt**).
- **Erwartete Groessenordnung vs. Friktion:** **Es wird keine bps-Kante
  beansprucht** -- die Wand ist hier per Konstruktion irrelevant, weil die
  Zielgroesse ein Verteilungsmass ist und die Variable nur eine bereits
  bestehende Position gating. Der oekonomische Wert: der einzige lebende
  Strategie-Pfad (H-26/C-33) haengt heute an einer **ungemessenen**
  Post-Schock-Kalibrierung -- die Kandidaten-Notiz vom 2026-08-20 sagt das
  woertlich. K-34 misst genau diese fehlende Zahl.
- **Daten:**
  - **Funding: der Blocker ist weg.** `/v5/market/funding/history` ist
    oeffentlich und ohne Key; 3 Settlements/Tag x ~2.330 Tage x 5 Symbole
    ~ **35.000 Records** -- Minuten Download. Die 113-Tage-Grenze des
    Harvest-Baums ist damit kein Hindernis mehr (das ist derselbe Hebel, mit
    dem DATA_INVENTORY Par. 4.1 den H-11-Blocker aufgeloest hat, nur fuer 6 Jahre
    statt 2).
  - **OI: Ruecklaufzeit UNBELEGT.** `/v5/market/open-interest`
    (intervalTime 5min..1d) -- die Bybit-Doku war aus dieser Umgebung
    egress-gesperrt. **Pflicht-Feasibility-Vorabprobe (GL-012):** ein
    Testabruf mit startTime 2021-01-01 VOR jeder Registrierung. Faellt die
    Ruecklaufzeit auf ~6 Monate, faellt der OI-Arm ersatzlos und nur der
    Funding-Arm bleibt (der aber ueber 6 Jahre lebt). Der Harvest-Baum
    (`rest.openInterest`, ~136 Tage) reicht allein nicht fuer zwei
    rezenz-konforme Fenster.
  - Returns/RV: WP-0-Bar-Cache.
  - *Datenqualitaets-Fussnote:* `allLiquidation` (~66 Tage) und `insurance`
    (~66 Tage) werden **bewusst nicht** benutzt -- sie sind fuer H-21
    reserviert und heute zu kurz. K-34 kommt vollstaendig ohne sie aus; das
    ist die Abgrenzung zu H-21, nicht nur eine Formulierung.
- **Rechenaufwand:** CPU, Minuten. PC- und Sandbox-tauglich.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Zustandsvariable (vorab fixiert, keine Fensterlaengen-Suche):**
    Z_t = z-Score(Delta-log-OI ueber 7 Tage) x sign(Mittel-Funding ueber
    7 Tage). Ohne OI-Arm: Z_t = z-Score(Mittel-Funding ueber 7 Tage).
  - **Metrik:** R = Semivarianz_abwaerts(Tag t+1 | Z_t im obersten Dezil) /
    unbedingte Semivarianz_abwaerts.
  - **Struktureller Nulleffekt (die entscheidende Pflichtzeile):**
    Vol-Clustering allein erzeugt bereits R > 1, weil Z_t mit der trailing-RV
    korreliert ist. Der Nulleffekt ist R unter einer **RV-gematchten
    Baseline** (Tage mit gleichem trailing-RV-Dezil, aber beliebigem Z_t).
    **Urteilstragend ist R_bedingt - R_RV-gematcht, nie R selbst.** Ohne diese
    Zeile waere K-34 ein garantiertes Schein-PASS -- exakt die H-11/DEC-31-Lehre
    (Schwelle unter dem strukturellen Boden).
  - **Gate:** (R_bedingt - R_RV-gematcht) >= **0,25** in BEIDEN juengsten
    12-Monats-Fenstern (W1/W2 wie K-31), Block-Bootstrap-p <= 0,05,
    FDR **F-LEVSTATE** (5 Symbole x 2 Fenster = 10 Zellen).
  - **DEC-39-Fixturepaar:** positiv = synthetische Reihe mit injizierter
    zustandsabhaengiger Sprungintensitaet (muss zurueckgewonnen werden);
    negativ = GARCH-Reihe mit demselben Vol-Clustering aber Z_t zufaellig
    permutiert (muss ~0 liefern).
  - **Feasibility (GL-012-Check):** kein struktureller Deckel auf der
    Semivarianz-Ratio (kein H-07-Analogon); limitierend ist die Zahl der
    Dezil-Tage: 12-Monats-Fenster -> ~36 Tage im obersten Dezil je Symbol,
    gepoolt ueber 5 Symbole ~180 -- ausreichend fuer einen Block-Bootstrap,
    knapp fuer einzelne Symbolzellen (deshalb ist die Symbol-Zelle
    berichtend, das gepoolte Panel urteilstragend; das ist VOR dem Lauf
    festzuschreiben).
- **Was ihn a priori toetet:** (1) R_bedingt - R_RV-gematcht < 0,25 -> OI und
  Funding sind blosse Vol-Proxys und tragen nichts Eigenes; (2) die
  OI-Ruecklaufzeit-Probe scheitert und der Funding-Arm allein verfehlt die
  Schwelle; (3) Vorzeichen-/Groessenwechsel zwischen den Fenstern.
- **Bezug zu Kompendium D/E:** Wiederholt **D-12 nicht** (H-20: dort die
  Reversion NACH einem 3,5-sigma-Ereignis als Renditeprognose, DROP; hier ein
  EX-ANTE-Zustand vor dem Tag und **keine Renditegroesse**, sondern ein
  Verteilungsmass -- es gibt keine gemeinsame Zelle). Wiederholt **H-21 nicht**
  (dort der Informationsgehalt des Liquidations-LABELS im Tape auf
  `allLiquidation`; hier aggregierte OI-/Funding-Zustandsvariablen ohne
  einen einzigen Liquidations-Record -- H-21 bleibt vollstaendig unberuehrt und
  gesperrt). Wiederholt **H-01 nicht** (Funding als Minuten-Entry-Trigger).
  Wiederholt **D-14 nicht** (H-24 misst Fluss->Rendite, nicht Zustand->Streuung).
  Bedient E-2/E-7 (H-26-Sizing-Luecke) und E-12 (Kaskaden-Cockpit-PARK) ohne
  deren Hawkes-Erbe anzufassen.
- **Vertrauen:** **mittel-hoch**, dass der Effekt messbar existiert (er ist
  nahezu mechanisch); **niedrig**, dass er nach der RV-gematchten Baseline
  noch etwas Eigenes traegt -- und genau das ist die interessante Frage.

---

### K-35 SLIP-ZENSUS - WP-3 gebaut: gemessene Ausfuehrungskosten-Kurve + Sweep-/Nachfuell-Struktur

- **Ertragsquelle:** **keine** -- dies ist ein Zensus im WP-4/WP-5/WP-6-Muster.
  Er beansprucht keine Kante, sondern haertet oder toetet eine
  **Programm-Konstante**: die "~15 bps inkl. Slippage" sind seit dem
  FINAL_PRD eine ANNAHME, an der jedes PARK-Urteil des Programms haengt
  (H-04b, H-05c, jede kuenftige Tradability-Frage, der H-26b-Delta-Hedge-Pfad).
- **Horizont & Instrument:** n/a (Messung). Ergebnis ist ein Eingang in jedes
  kuenftige Tradability-Gate.
- **Literatur/Evidenz:**
  - Large (2007), *Measuring the resiliency of an electronic limit order book*,
    J. of Financial Markets 10, 1-25: in **ueber 60% der Faelle fuellt das Buch
    nach einem grossen Trade NICHT verlaesslich nach**; wenn doch, mit einer
    Halbwertszeit von **~20 s**. Das ist die einzige belastbare Zahl in der
    Resilienz-Literatur -- sie stammt von LSE-Aktien, die Uebertragung auf
    Krypto-Perps ist **unbelegt** (**sekundaer belegt** ueber Abstract).
  - Degryse et al. (2005), Foucault/Kadan/Kandel (2005): Resilienz-Theorie,
    Nachfuellgeschwindigkeit steigt mit dem Anteil geduldiger Haendler
    (**sekundaer belegt**).
  - Programm-intern: WP-4 hat den Top-of-Book-Spread gemessen (exakt ein Tick),
    aber **nie die Tiefe dahinter** -- die Kostenkurve c(Q) fuer Q > Top-of-Book
    existiert im ganzen Programm nicht.
- **Erwartete Groessenordnung vs. Friktion:** Zielgroesse ist c(Q) in bps fuer
  Clips von 10k / 50k / 250k USD, je Stunde, getrennt nach Ruhe/Stress.
  Erwartung: bei BTC im Ruhe-Regime **deutlich unter 1 bp** (der Spread ist
  ein Tick, die Tiefe an den ersten Levels ist gross), im Stress-Perzentil
  Groessenordnungen darueber. **Beide Ausgaenge sind wertvoll:** ein niedriger
  Ruhewert korrigiert die 15-bps-Konstante fuer kleine Clips nach unten (der
  erste guenstige Strukturbefund des Programms ueberhaupt), ein hoher
  Stresswert toetet K-33 Stufe 2 und schaerft die H-26b-Hedge-Rechnung.
- **Daten:** Die WP-2-Replay-Maschinerie (`c22_l2tilt/extract.py`, 554 Zeilen,
  deterministisch, bit-identisch per Test gepinnt, Snapshot-Validierung +
  MAX_BREAKS_PER_DAY = 10 + lautes `discarded`) ist gebaut. Die Sweep- und
  Tiefen-Extraktion ist ein **zusaetzlicher Pass auf demselben Buchzustand** --
  das ist WP-3 (DEC-38, bisher nur "vertagt", nie verworfen). Nichts
  nachzuladen.
  - *Datenqualitaets-Fussnote (die haerteste Einschraenkung dieses Kandidaten):*
    BTC `orderbook.500` 2023-01-18..2025-08-13, `orderbook.1000` ab
    2026-06-22 -- **Loch 2025-08..2026-06**, Gesamtabdeckung 74%.
    ETH `orderbook.500` endet bereits **2024-05-10**, `orderbook.1000` ab
    2026-06-19 -- **~2-Jahres-Loch**, Gesamtabdeckung 41%. SOL/BNB/XRP nur
    35 Tage. **Rezenz-konform ist damit ausschliesslich das
    `orderbook.1000`-Fenster ab Juni 2026, heute ~2,5 Monate.** Dazu der
    Formatbruch snapshot-500 vs. delta-1000, der beide Aeren getrennt
    auszuweisen zwingt (die 500er-Aera hat ~2 Snapshots/Tag, die 1000er
    7-13 im Fenster).
- **Rechenaufwand:** CPU. Vergleichswerte aus dem Repo: WP-4-Spread-Zensus
  86 min (rc=0); WP-2 war ein Ein-Pass-Lauf je Fenster. Groessenordnung
  **Stunden**, PC-tauglich, kein GPU.
- **Kapitalfreies Mess-Gate (Entwurf) -- binaer, kein p-Wert (WP-4-Muster):**
  - **(A)** c(Q) = volumengewichtete Kosten gegen Mid fuer Q in
    {10k, 50k, 250k} USD, Median und p95 je Stunde, je Aera getrennt.
  - **(B)** Sweep-Ereignisse (>= 5 Levels durchgehandelt in einem
    `ts_exchange_ms`) mit Nachfuell-Halbwertszeit und dem Anteil der Sweeps
    **ohne** Nachfuellung binnen 60 s -- das ist die Large-2007-Zahl auf
    Krypto uebertragen und damit die erste echte Zahl zum vertagten
    SWEEP-PRE-Faden.
  - **Vorab fixierte Entscheidungsregel:** liegt c(50k USD) im Median unter
    **3 bps**, wird die Programm-Konstante "15 bps inkl. Slippage" fuer
    Clips <= 50k USD durch einen gemessenen Wert ersetzt (append-only DEC).
    **Ausdrueckliche Anti-Torpfosten-Klausel: bereits gefaellte PARK-/DROP-
    Urteile (H-04b, H-05c) werden NICHT rueckwirkend geaendert** -- sie sind
    unter der damals registrierten Wand gefallen und bleiben, was sie sind.
    Der neue Wert gilt nur fuer kuenftige Registrierungen.
  - **Struktureller Nulleffekt:** ein naives "Fill bei Beruehrung" erzeugt auf
    einem Random Walk mechanisch positive Spread-Capture (die im
    Kandidaten-Papier vom 2026-08-20 bereits benannte Fill-Nulleffekt-Falle);
    K-35 misst darum ausschliesslich **Taker-Kosten gegen Mid**, nie
    Maker-Ertrag -- die Metrik ist so gewaehlt, dass es keinen Nulleffekt gibt,
    der geschenkt wird.
- **Was ihn a priori toetet:** die REZENZ-Luecke. Ein Zensus auf 2023-2025 ist
  Marktarchaeologie (DEC-38); mit nur ~2,5 Monaten `orderbook.1000` ist eine
  Stress-Episode nicht garantiert. **Konsequenz, ehrlich:** K-35 ist heute
  aera-deskriptiv und wird erst mit wachsendem 1000er-Fenster urteilstragend --
  aber die 500er-Aera-Zahlen sind trotzdem sofort wertvoll, weil sie die
  Groessenordnung der Konstante zum ersten Mal ueberhaupt liefern.
- **Bezug zu Kompendium D/E:** Erledigt **E-5** (SWEEP-PRE/WP-3), OHNE dessen
  tote Kern-These zu reiten: der Wert von SWEEP-PRE war Execution-Timing
  UNTER der Wand, hier wird die Resilienz-Messung zur KOSTEN-Messung
  umgewidmet -- die Wand wird nicht umgangen, sondern quantifiziert.
  Wiederholt **D-13 nicht** (H-22: Buchneigung als Folgetags-RICHTUNGSsignal;
  hier keine Richtungsaussage und keine Rendite-Zielgroesse). Wiederholt
  **D-1 nicht** (Spread-Capture; hier wird ausdruecklich nur die
  Taker-Kostenseite gemessen). Bedient E-6(b) (H-26b braucht einen
  Options-Spread-Zensus; K-35 liefert das Perp-Bein des Delta-Hedges).
- **Vertrauen:** **hoch**, dass es sauber und deterministisch messbar ist
  (die Maschinerie ist gebaut und getestet); **hoch** fuer den Wert;
  **keine Kante beansprucht** -- deshalb kein Kanten-Vertrauensurteil.

---

### K-36 VRP-KOND - Konditionierung des Varianz-Risiko-Premiums auf der oeffentlichen DVOL-Vollhistorie

- **Ertragsquelle:** **Praemie** -- aber die FRAGE ist nicht ihre Existenz
  (das ist H-26 und bleibt es), sondern ihre **Konditionierung**: in welchem
  IV-Zustand ist die Praemie negativ, d.h. wann verliert der Verkaeufer
  systematisch? Der oekonomische Mechanismus: die VRP ist die Kompensation
  fuer das Uebernehmen von Vol-Sprungrisiko; sie ist im Mittel positiv, aber
  ihr bedingter Erwartungswert kippt, wenn das IV-Niveau bereits weit unter
  der jungen Vergangenheit liegt (dann ist der Verkaeufer unterbezahlt).
  Wer zahlt: im Normalzustand der Kaeufer der Konvexitaet, im gekippten
  Zustand der Verkaeufer.
- **Horizont & Instrument:** 1 Woche; reine Messung. Instrument spaeter
  Bybit-USDT/USDC-Optionen, aber **hier nicht impliziert**.
- **Literatur/Evidenz:**
  - Allgemeine VRP-Literatur (Carr/Wu-Linie) fuer Aktien -- in dieser Sitzung
    **nicht unabhaengig geprueft**, daher fuer Krypto als **unbelegt** gefuehrt.
  - Atanasova et al., *Illiquidity Premium and Crypto Option Returns*
    (AUT ACFR Working Paper; Volltext egress-gesperrt): Verkaufsdruck und
    Illiquiditaet erzeugen eine **positive Illiquiditaets-Praemie in
    erwarteten Options-Renditen** (**sekundaer belegt**). Relevant, weil ein
    Teil dessen, was als VRP gemessen wird, in Wahrheit Illiquiditaets-
    Kompensation sein kann -- das ist eine Interpretationsgrenze, die
    vorab zu protokollieren ist.
  - Praktiker-Kalibrierung: DVOL schwankte zwischen 43% (Ende 12/2025) und
    63% (Ende 11/2025), gegen einen VIX von 14-20 im selben Zeitraum
    (**unbelegt**, Praktiker-Quelle, nur als Groessenordnung).
- **Erwartete Groessenordnung vs. Friktion:** In Vol-Punkten. Options-Gebuehr
  2 bp (Maker) / 3 bp (Taker) des Index je Fill, vega/S = 5,28 bp Index je
  Vol-Punkt (BTC) / 5,10 (ETH). Ein passiver Ein-und-Halten-bis-Verfall-Zyklus
  (2 Fills) kostet damit **~0,76 Vol-Punkte** (BTC) -- konsistent mit DEC-45
  (25-26% einer 3-Vol-Punkt-Kante). Eine Konditionierung ist nur dann
  wertvoll, wenn sie den bedingten Praemien-Unterschied um **>= 2-3
  Vol-Punkte** verschiebt.
- **Daten -- hier liegt der eigentliche Fund:**
  - Deribit `public/get_volatility_index_data` liefert DVOL-OHLC
    **oeffentlich, ohne Key, ab 2021-04-01**, in waehlbarer Aufloesung
    (z.B. 3600 s). Das sind **~5,4 Jahre statt der 112 harvesteten Tage** --
    ~47.000 Stundenkerzen je Waehrung, Download in Minuten.
  - RV-Seite: WP-0-Bar-Cache (6 Jahre, deterministisch).
  - **Registry-Warnung, ausdruecklich und bindend:** dieser Backfill darf die
    H-26-Entsperrbedingung **nicht ersetzen**. H-26 ist auf lueckenlose
    harvestete `done_days` geschrieben; ein Ersatz waere Torpfosten-
    Verschiebung. Ebenso darf er die **C-33-12-Monats-Uhr nicht erfuellen** --
    E-7 sagt woertlich, dass eine Deribit-Substitution unzulaessig ist.
    K-36 ist eine EIGENE, neue Vorregistrierung mit einer anderen Frage
    (bedingter statt unbedingter Mittelwert) auf einer anderen Datenquelle.
    Ob der Backfill DARUEBER HINAUS etwas fuer H-26/C-33 aendert, ist eine
    Verfassungsfrage fuer den Orchestrator, nicht fuer mich.
  - *Datenqualitaets-Fussnote:* Der oeffentliche DVOL-Endpunkt ist eine
    ANDERE Quelle als der harvestete `dvol`-Strom (112 Tage, mit
    Manifest-DONE-Luecke, DEC-50 offen). Vor jeder Nutzung ist ein
    **Ueberlappungsabgleich** ueber die ~112 gemeinsamen Tage Pflicht
    (Materialitaets-Schranke statt Bit-Identitaet, DEC-32: relative Schranke
    aus der Gate-Arithmetik + SHA-256-Fingerabdruck). Weicht der oeffentliche
    Feed materiell ab, faellt der Kandidat sofort.
- **Rechenaufwand:** CPU, Minuten.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Zustand (vorab fixiert):** (i) DVOL-Perzentil ueber trailing 1 Jahr;
    (ii) DVOL / RV_20d. Keine Suche ueber Varianten.
  - **Metrik:** VRP_w(t) = DVOL_t (auf 7 Tage skaliert) - RV[t, t+7d];
    Vergleich des bedingten Mittelwerts im untersten vs. obersten
    Zustands-Terzil.
  - **Fenster:** zwei disjunkte 12-Monats-Fenster als urteilstragend
    (W1/W2 wie K-31); 2021-2024 rein deskriptives Aera-Profil.
  - **Struktureller Nulleffekt (zwei Pflichtrechnungen, DEC-31/33 + DEC-39):**
    (i) **Horizont-Mismatch:** DVOL ist ein 30-Tage-Index, RV wird ueber
    7 Tage gemessen. Unter einer flachen Term-Struktur und **ohne jede
    Praemie** erzeugt das bereits eine systematische Differenz (Jensen +
    Term-Struktur). Diese ist per Simulation mit IV == wahrer Forward-Vol
    durch dieselbe Pipeline auszurechnen (das ist exakt der Nullpfad, den
    die H-26-Kandidatennotiz vom 2026-08-20 unter Korrektur 5 fordert).
    (ii) **DVOL-Mean-Reversion** erzeugt eine Terzil-Differenz auch ohne
    Praemien-Konditionierung -- gegen ein AR(1)-Surrogat der DVOL zu
    kalibrieren.
  - **Gate:** Terzil-Differenz >= **3 Vol-Punkte** mit gleichem Vorzeichen in
    beiden Fenstern, Block-Bootstrap-p <= 0,05 (Bloecke = 4 Wochen wegen der
    ueberlappenden 7-Tage-Fenster), FDR **F-VRPCOND** (2 Symbole x 2 Fenster
    = 4 Zellen).
  - **Feasibility (GL-012-Check), ehrlich:** je 12-Monats-Fenster gibt es
    ~52 nicht-ueberlappende Wochen, je Terzil ~17. Bei einer
    Wochen-VRP-SD von 12 Vol-Punkten ist SE(Terzil-Mittel) = 12/sqrt(17)
    = **2,9 Vol-Punkte**, die Terzil-DIFFERENZ hat SE ~4,1 --
    **die 3-Punkte-Schwelle waere dann 0,7 SE und strukturell unerreichbar.**
    Vor der Registrierung ist die tatsaechliche Wochen-VRP-SD auf dem
    Aera-Profil zu messen; liegt sie ueber ~6 Vol-Punkten, muss entweder auf
    Terzil-Vergleich mit ueberlappenden Wochen + Newey-West umgestellt oder
    die Fensterlaenge auf 24 Monate erhoeht werden -- beides **vor** dem Lauf
    und aus der Arithmetik begruendet, nie danach. Das ist der ehrlichste
    Punkt dieses Kandidaten: er kann am eigenen Power-Check sterben.
- **Was ihn a priori toetet:** (1) der Nullpfad (i) liefert selbst >= 3
  Vol-Punkte -> die Schwelle ist sinnlos und muss neu hergeleitet werden
  (die H-11/GL-022-Lehre, hier vorweggenommen); (2) der Power-Check oben;
  (3) der Ueberlappungsabgleich zwischen oeffentlichem und harvestetem
  DVOL-Feed scheitert.
- **Bezug zu Kompendium D/E:** Wiederholt **H-26 nicht** (dort unbedingte
  Existenz der Praemie, harvestete Deribit-`done_days`, >= 210 Tage,
  Schwelle 3% Mittelpraemie; hier bedingte Terzil-DIFFERENZ auf 5,4 Jahren
  oeffentlicher Historie -- andere Frage, andere Datenquelle, andere Statistik).
  Wiederholt **H-13 nicht** (Tail-FORM an zwei Snapshot-Tagen). Wiederholt
  **D-... / H-02 / H-11c nicht**: dort wurde eine RV-PROGNOSE gegen HAR bzw.
  gegen eine gedresste HAR bewertet und die Dressing-Falle war toedlich; hier
  wird **keine Verteilungsprognose bewertet**, sondern ein bedingter
  Praemien-Mittelwert -- das CRPS-Dressing-Geschenk (Programm-Konstante 9)
  ist auf diese Metrik nicht anwendbar. Wiederholt **D-15 nicht**
  (reaktives Long-Vol; hier keine Reaktionsregel, kein Schub-Signal).
  Bedient E-2 (H-26) und E-7 (C-33-Uhr) -- **ohne** deren Sperren zu beruehren.
- **Vertrauen:** **mittel.** Der Datenfund ist hart und veraendert die
  Datenlage des Optionspfades substanziell; die Frage ist sauber von H-26
  abgegrenzt; die Power ist der Schwachpunkt und wird vorab geprueft.

---

### K-37 SKEW-VORLAEUFER - Risk-Reversal-Aenderung als Vorlaeufer der realisierten Schiefe (zweistufig, Stufe 1 sofort)

- **Ertragsquelle:** **Prognose auf einer risikoneutral/physisch-Diskrepanz.**
  Die 25-Delta-Risk-Reversal (RR = IV_25dCall - IV_25dPut) ist der Preis der
  Absicherungsnachfrage. Aendert sie sich, bevor die realisierte Verteilung
  schief wird, dann traegt die Kette Information ueber die physische
  Verteilung; aendert sie sich erst danach, ist sie eine Nachlaufgroesse.
  Beide Ausgaenge sind fuer den Optionspfad wertvoll. Wer zahlt: wer
  Absicherung nachfragt, wenn sie schon teuer ist.
- **Horizont & Instrument:** 1-2 Wochen. Messung; Instrument spaeter
  Bybit-Optionen (Risk-Reversal-Bein), hier **nicht impliziert**.
- **Literatur/Evidenz:**
  - Kim et al. (2025), *Effects of Social Media-Based Peer Opinions on the
    Prices of Cryptocurrency Options*, J. of Futures Markets: auf
    Deribit-BTC/ETH-Optionen wird die risikoneutrale Schiefe **negativer in
    baerischen Sentiment-Phasen**; OTM-Put-IVs steigen staerker als ATM
    (**sekundaer belegt**). Das belegt, dass RR in Krypto **auf** Zustaende
    reagiert -- offen bleibt genau die Vorlauf-Frage.
  - Alexander/Imeraj-Linie (Univ. Sussex), u.a. *Delta hedging bitcoin
    options with a smile* (Quantitative Finance 2023) und die Beobachtung,
    dass **~80% des BTC-Optionsvolumens auf <= 1 Monat Restlaufzeit**
    entfaellt (**sekundaer belegt**) -- begruendet, warum der Front-Tenor die
    einzige sinnvolle Messstelle ist.
  - Vorlauf-Evidenz fuer Krypto: **unbelegt**. Genau deshalb ist das eine
    Hypothese und keine Uebernahme.
- **Erwartete Groessenordnung vs. Friktion:** Zielgroesse ist eine
  Korrelation/IC, keine bps-Kante. Eine spaetere Monetarisierung ueber ein
  RR-Bein kostet 2 Fills passiv ~0,76 Vol-Punkte (BTC) -- dieselbe Rechnung
  wie K-36. Die Vorlaufgroesse muesste also >= 2 Vol-Punkte RR-Bewegung
  vorhersagen, um ueberhaupt diskutabel zu sein. **Das ist eine spaetere,
  nicht implizierte K-37b-Frage.**
- **Daten und der Grund fuer die Zweistufigkeit:**
  - **Stufe 1 (SOFORT, billig, kein Gate im Alpha-Sinn): Ketten-
    Vollstaendigkeitszensus.** Fuer jeden Tag und jedes Symbol im
    Bybit-Options-Ticker-Strom, in `deribit/tickers`, in
    `markprice.options` und im REST-Sampler: welche Felder liegen wirklich
    vor (`delta`/`gamma`/`vega`/`openInterest`/IV, mit dem
    `FIELD_ALIASES`-Muster aus `wp6_optstress/extract.py`), wieviele Strikes
    je Verfall im Band 0,15 <= |Delta| <= 0,35, wieviele Verfaelle je Tag,
    und eine **tagesgenaue Luecken-Karte**. Ausgabe: die Tabelle, die
    entscheidet, ob K-32 und K-37 Stufe 2 je registrierbar sind -- und die
    zugleich die Datenqualitaets-Fussnoten dieses ganzen Papiers von
    Schaetzungen in Messungen verwandelt. Das ist exakt das WP-1-Muster
    ("faellt der Zensus aus, wird die Hypothese nicht registriert").
  - **Stufe 2 (data-gated):** RR_25d je Tag/Symbol aus der Kette;
    Delta-RR ueber 5 Tage gegen die realisierte Schiefe der folgenden
    10 Tage (aus dem Bar-Cache).
  - *Datenqualitaets-Fussnote:* dieselbe wie K-32 -- ~10 Verfaelle,
    ETH-Luecke 22.-27.08. (fuer 22.-24.08. quellenlos), unverifizierte
    Bybit-Tiefe vor 2026-08-24. Zusaetzlich: `markprice.options` fuehrt
    Mark-IV, aber **kein Open Interest**; `deribit/tickers` fuehrt Greeks
    UND OI, ist aber der juengste Strom. Fuer RR reicht IV (also auch
    `markprice.options`, ~78 Tage) -- RR ist damit **frueher registrierbar
    als GEX**, was K-37 vor K-32 stellt.
- **Rechenaufwand:** CPU. Stufe 1 Minuten bis eine Stunde; Stufe 2 Minuten.
- **Kapitalfreies Mess-Gate (Entwurf):**
  - **Stufe 1: kein p-Wert, kein Gate -- ein Zensus mit vorab fixierter
    Abbruchregel.** Existieren in ZWEI disjunkten Fenstern je >= 60 Tage mit
    >= 8 Strikes im |Delta|-Band je Symbol, ist Stufe 2 registrierbar; sonst
    nicht, und die Schwelle wird nicht gesenkt.
  - **Stufe 2:** Spearman-IC zwischen Delta-RR_5d(t) und der realisierten
    Schiefe ueber [t, t+10d]. Rauschboden 1/sqrt(N); bei N = 60 Tagen je
    Fenster ist das **0,129** -> Schwelle **|IC| >= 0,25** (~2 Rauschboeden),
    gleiches Vorzeichen in beiden Fenstern, Permutations-p <= 0,05
    (Block-Permutation, 20-Tage-Bloecke wegen der Ueberlappung),
    FDR **F-SKEW** (2 Symbole x 2 Fenster).
  - **Struktureller Nulleffekt:** RR und realisierte Schiefe teilen den
    **Leverage-Effekt** -- beide sind mechanisch mit der gleichzeitigen
    Rendite korreliert (H-16 hat genau diese Envelope-Asymmetrie als
    85-106%-Erklaerung eines vermeintlichen Struktureffekts entlarvt).
    Vorab zu rechnen: der IC unter einem Surrogat, das die
    Renditen-Korrelation erhaelt und nur den Vorlauf zerstoert. Ohne diese
    Zeile misst K-37 den Leverage-Effekt neu.
  - **Ueberlappungs-Falle:** 5-Tage-Delta gegen 10-Tage-Forward auf
    Tagesraster erzeugt starke Autokorrelation; die Block-Permutation ist
    Gate-Bestandteil, nicht Robustheit.
- **Was ihn a priori toetet:** (1) Stufe 1 (Strike-Abdeckung); (2) der
  Leverage-Nulleffekt erklaert den IC (die H-16-Lehre, hier vorweggenommen);
  (3) N = 60 je Fenster macht |IC| >= 0,25 zwar erreichbar, aber die
  Zwei-Fenster-Bedingung bei dieser Power sehr streng -- ein ehrlicher
  DROP-Favorit.
- **Bezug zu Kompendium D/E:** Wiederholt **H-13 nicht** (dort GPD-xi-FORM
  des Tails an zwei Snapshot-Tagen, hier die zeitliche VORLAUF-Beziehung
  einer Smile-Kennzahl -- H-13 ist ein Querschnittsvergleich, K-37 ein
  Laengsschnitt). Wiederholt **D-17 nicht** (Tardis-Chain tot;
  hier Live-Kette). Wiederholt **D-15 nicht** (kein Reaktionskauf).
  Wiederholt **H-16 nicht**, sondern **benutzt dessen Lehre** als
  Pflicht-Nulleffekt. Bedient E-3 und E-13 (C-11-M-S17 IV-Surface-PH bleibt
  unberuehrt und geparkt).
- **Vertrauen:** **niedrig-mittel** fuer Stufe 2; **hoch** fuer den Wert von
  Stufe 1 (die Ketten-Luecken-Karte fehlt dem Programm heute komplett und
  wird von jedem Options-Kandidaten gebraucht).

---

## Rangliste

| Rang | Kandidat | Warum hier | Sofort startbar? |
|---|---|---|---|
| 1 | **K-31 EXP-CLOCK** | Einziger Kandidat mit (i) einer A-priori-Groessenordnung in Wandnaehe, (ii) N ~ 200 Ereignissen, (iii) **null** Nachladeaufwand, (iv) einem Gratis-Negativ-Panel aus Realdaten. Nutzt genau den Bestand, der laut DATA_INVENTORY Par. 4.5 "von keiner einzigen bisherigen Hypothese genutzt" wurde. | **ja** |
| 2 | **K-36 VRP-KOND** | Harter Datenfund (DVOL oeffentlich ab 2021-04, 5,4 Jahre statt 112 Tagen) auf dem einzigen lebenden Strategie-Pfad; sauber von H-26/C-33 abgegrenzt; Power-Risiko vorab pruefbar. | ja, nach Ueberlappungsabgleich |
| 3 | **K-33 X-PULL (Stufe 1)** | Billiger, binaerer Killer einer ganzen Kandidatenfamilie -- exakt das WP-4-Muster, das den Market-Making-Zweig in einem Nachmittag erledigt hat. Auch ein DROP ist ein Programm-Ergebnis. | ja (Stufe 1) |
| 4 | **K-34 LEV-STATE** | Misst die eine Zahl, die dem einzigen lebenden Pfad (H-26/C-33-Sizing, 3,5-sigma-Kill-Regel) heute nachweislich fehlt; Funding-Blocker per oeffentlichem Backfill weg. | ja (Funding-Arm); OI-Arm erst nach Ruecklaufzeit-Probe |
| 5 | **K-37 Stufe 1 (Ketten-Zensus)** | Liefert die Luecken-Karte, die K-32, K-37 Stufe 2 und jeder kuenftige Options-Kandidat braucht; verwandelt alle Datenqualitaets-Fussnoten dieses Papiers in Messungen. | **ja** |
| 6 | **K-35 SLIP-ZENSUS (WP-3)** | Haertet die Programm-Konstante, an der jedes PARK-Urteil haengt, und erledigt den vertagten SWEEP-PRE-Faden -- aber die REZENZ-Luecke (nur ~2,5 Monate `orderbook.1000`) macht ihn heute aera-deskriptiv. | ja, aber vorerst deskriptiv |
| 7 | **K-32 GEX-KOND** | Bester Mechanismus mit direkter Krypto-Evidenz, schlechteste Registrierbarkeit: N-Floor fruehestens ~2027-05, und ohne Options-Taker-Tape ist das GEX-Vorzeichen nicht identifiziert. **Heute ein Harvester-Auftrag, keine Hypothese.** | **nein** |

**Sequenz-Empfehlung:** K-31 und K-37 Stufe 1 parallel (beide CPU-Minuten,
kein Nachladen, keine gemeinsame FDR-Familie). Dann K-33 Stufe 1 und der
K-34-Funding-Arm. K-36 nach dem DVOL-Ueberlappungsabgleich. K-35 als
WP-Auftrag ohne Alpha-Gate. K-32 **nicht registrieren**, sondern nur den
Harvester-Auftrag (Options-Trade-Tape) stellen und die Uhr laufen lassen.

**Multiple-Testing-Hinweis (PRD Par. 8.1, DEC-22):** laufen >= 2 dieser
Kandidaten als gemeinsame Kohorte, ist VOR dem Lauf eine Ueber-Familie
(analog F-WAVE2/F-XDOM1) zu registrieren. Bei der obigen Sequenz betrifft
das mindestens K-31 + K-37-Stufe-2 und spaeter K-33-Stufe-2 + K-34.

---

## Was ich NICHT vorschlage und warum

1. **Max-Pain-Pinning als Strike-Magnet-Handel.** Der peer-reviewte
   Krypto-Befund ist eine **Umkehr um den Verfall**, kein Strike-Magnet; der
   Magnet ist Praktiker-Folklore und wurde im Juni-2026-Verfall oeffentlich
   widerlegt (Spot ~11.000 USD vom Max-Pain-Level entfernt bei 10,6 Mrd USD
   Notional). Ausserdem braucht Max Pain die volle Kette und stuerzt damit in
   denselben N-Floor wie K-32. K-31 misst den belegten Effekt, nicht den
   erzaehlten.

2. **L2-Tiefe-Asymmetrie und Wal-Order-Persistenz als Richtungssignal auf
   Tages-/Wochen-Horizont.** D-13 (H-22) hat die Buchneigung auf 1-Tages-
   Horizont erledigt, und die Literatur ist eindeutig, dass der
   Praediktivgehalt der Buchimbalance **auf Sekunden bis maximal eine Minute**
   beschraenkt ist. Eine Wiederholung auf Wochen waere ein
   Horizont-Nachsuchen ohne Mechanismus. Zusaetzlich toedlich: die
   REZENZ-Klausel -- ETH hat ein 2-Jahres-L2-Loch, BTC ein 10-Monats-Loch, und
   das rezenz-konforme 1000er-Fenster ist ~2,5 Monate lang. Der einzige
   L2-Vorschlag, den ich mache (K-35), ist deshalb bewusst eine
   **Kosten**-Messung ohne jede Richtungsaussage.

3. **SWEEP-PRE in seiner urspruenglichen Fassung (Ereignis-Vorlauf vor
   Sweeps).** DEC-38 hat den Wert korrekt als "Execution-Timing UNTER der
   Friktionswand" identifiziert. Ich reite das nicht neu, sondern widme die
   dafuer noetige Extraktion in K-35 zu einer Kostenmessung um -- dieselbe
   Maschinerie, eine Frage, die die Wand nicht umgehen muss.

4. **Liquidations-Cluster als Ereignis-Trigger (Heatmap-Magnet).** Drei
   Gruende: (i) H-21 ist registriert und bis 2026-12-27 gesperrt -- ein
   Parallelkandidat auf demselben `allLiquidation`-Strom (~66 Tage) waere
   die H-10/H-13-N-Falle zum dritten Mal; (ii) der einzige gefundene
   Fachaufsatz zum Thema ist ein **Negativbefund** (Fruehwarnsignale sind
   ereignis-heterogen); (iii) H-20 hat die Post-Schock-Reversion bereits
   erledigt. K-34 benutzt darum **keinen einzigen Liquidations-Record**.

5. **Zweibeinige Cross-Venue-Basis-Arbitrage (Bybit-vs-Binance,
   Perp-vs-Deribit).** Verstoesst gegen die Programm-Randbedingung
   (Deribit/Binance sind Datenquellen, keine Handelsplaetze) und kostet
   4 Fills ~ 22 bps Taker-RT plus zwei Funding-Stroeme plus
   Cross-Margin-Risiko. K-33 ist deshalb bewusst einbeinig.

6. **Perp-vs-Spot-Basis-Mean-Reversion als eigener Kandidat.** C-23
   (Basis-Convergence) steht im PRD-PARK-Register mit der bereits gefaellten
   Rechnung "2-Bein ~22 bps gegen <0,08% Konvergenz" -- das ist eine
   quantifizierte Absage, die ich ohne neue Zahl nicht aufhebe. Die
   Funding-Carry-Ernte (Perp-Short + Spot-Long) waere eine legitime,
   prognosefreie Praemie, gehoert aber in die **Praemien-Spur**, nicht in
   meinen Ereignis-/Struktur-Auftrag; ich melde sie dorthin weiter statt sie
   hier zu duplizieren.

7. **Jede GEX-Registrierung auf dem heutigen Bestand.** ~10 Verfalls-Freitage.
   Das ist praezise die Falle, an der H-10 (N_pointer = 0) und H-13
   (2 Snapshot-Tage) haengen. K-32 ist deshalb ausdruecklich mit
   Entsperr-Bedingung und Nicht-Start-Empfehlung formuliert.

8. **Wiederbelebung der Options-Chain-Graph-Kandidaten (CHAIN-GRAPH,
   SET-SHAPE).** D-17: am Tardis-2-Tage-Sampling gestorben. Die Live-Kette ist
   zwar andere Daten, aber die Kandidaten waren strukturell datenhungrige
   Topologie-Modelle -- ohne validiertes Basissignal waeren sie die
   S4/S5-Infrastruktur-Falle (D-16).

9. **Ein neuer RV-Prognose-Kandidat aus L2- oder OI-Features.** H-02 (0/5
   Symbole), H-11 (Schwelle unter dem Dressing-Boden) und H-11c (0/4 Zellen
   gegen die gedresste HAR) haben diese Bewertungsfamilie erledigt. K-34 und
   K-36 sind deshalb bewusst so formuliert, dass **keine Verteilungsprognose
   gegen eine Baseline bewertet wird** -- sonst waere Programm-Konstante 9
   (26-30% Gratis-Geschenk durch Dressing) sofort anwendbar.

---

## Anhang -- Quellen

- Ni, Pearson, Poteshman (2005), *Stock price clustering on option expiration dates*, J. Financial Economics 78(1), 49-87 -- https://www.sciencedirect.com/science/article/abs/pii/S0304405X05000577
- Blasco, Corredor, Satrustegui (2023), *Is there an expiration effect in the bitcoin market?*, Int. Review of Economics and Finance 85, 647-663 -- https://www.sciencedirect.com/science/article/pii/S1059056023000515
- *Bitcoin option expiration, gamma exposure, and intraday price reversals*, Finance Research Letters (Juni 2026) -- https://www.sciencedirect.com/science/article/pii/S1544612326008688
- *Gamma positioning and market quality*, J. of Economic Dynamics and Control (2024) -- https://www.sciencedirect.com/science/article/pii/S0165188924000721
- Large (2007), *Measuring the resiliency of an electronic limit order book*, J. of Financial Markets 10, 1-25 -- https://www.sciencedirect.com/science/article/abs/pii/S1386418106000528
- *Resiliency of the limit order book*, J. of Economic Dynamics and Control -- https://www.sciencedirect.com/science/article/abs/pii/S0165188915001797
- *Fragmentation, Price Formation and Cross-Impact in Bitcoin Markets*, Applied Mathematical Finance (2022) -- https://www.tandfonline.com/doi/full/10.1080/1350486X.2022.2080083
- Kim et al. (2025), *Effects of Social Media-Based Peer Opinions on the Prices of Cryptocurrency Options*, J. of Futures Markets -- https://onlinelibrary.wiley.com/doi/10.1002/fut.70004
- Alexander et al. (2023), *Delta hedging bitcoin options with a smile*, Quantitative Finance -- https://www.tandfonline.com/doi/full/10.1080/14697688.2023.2181205
- Atanasova et al., *Illiquidity Premium and Crypto Option Returns*, AUT ACFR WP -- https://acfr.aut.ac.nz/__data/assets/pdf_file/0006/969378/950002_Atanasova_Illiquidity-Premium-and-Crypto-Option-Returns.pdf
- *Where does the criticality live? Early-warning signals are event-heterogeneous across seven crypto-perpetual liquidation cascades*, arXiv 2607.27070 -- https://arxiv.org/html/2607.27070
- *Liquidation, Leverage and Optimal Margin in Bitcoin Futures Markets*, arXiv 2102.04591 -- https://arxiv.org/pdf/2102.04591
- *Anatomy of the Oct 10-11, 2025 Crypto Liquidation Cascade*, SSRN 5611392 -- https://papers.ssrn.com/sol3/Delivery.cfm/5611392.pdf?abstractid=5611392
- Glassnode Research, *Introducing: Taker-Flow-Based Gamma Exposure* -- https://research.glassnode.com/gamma-exposure/
- Deribit Support, *Settlement* (30-Min-TWAP, 450 Snapshots, 08:00 UTC) -- https://support.deribit.com/hc/en-us/articles/29734325712413-Settlement
- Deribit API, *public/get_volatility_index_data* (DVOL-Historie ab 2021-04-01, oeffentlich) -- https://docs.deribit.com/api-reference/market-data/public-get_volatility_index_data
- Bybit Help Center, *FAQ Options* / *Derivatives Overview* (Settlement 08:00 UTC, 30-Min-Index-Mittel) -- https://www.bybit.com/en/help-center/article/FAQ-Options-Trading
- Bybit API v5, *Get Funding Rate History* -- https://bybit-exchange.github.io/docs/v5/market/history-fund-rate
- Bybit API v5, *Get Open Interest* (Ruecklaufzeit in dieser Sitzung nicht verifizierbar) -- https://bybit-exchange.github.io/docs/v5/market/open-interest

*Ende R3_EREIGNIS_STRUKTUR.md*
