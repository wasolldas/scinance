# AUDIT — Daten-Inventar & Ausschlussliste (Phase AUDIT, `data-feasibility-scout`)

**Stand dieses Audits:** 2026-07-07
**Zugriff aufs reale Harvest-Manifest:** **NEIN.** `/home/user/scinance/data/harvest/state/harvest_manifest.sqlite`
existiert in dieser Sandbox nicht (`/home/user/scinance/data` ist überhaupt nicht vorhanden — kein
Junction-Mountpoint, kein Verzeichnisstumpf). Die einzige Windows-lokale Junction-Referenz, die im Repo
auffindbar ist, sind Verweise in `scinance2-impl/state/decisions.md` (DEC-15, DEC-17/18) auf eine ÄLTERE,
kleinere read-only Junction `data/harvest` (Backfill bis 2026-03-20, genutzt für H-05b/H-08) — auch diese
liegt nicht in der Sandbox. **Kein SELECT gegen `partitions` war möglich.** Dieses gesamte Dokument stützt
sich daher zu 100 % auf **Dokumenten-Übernahme** aus `reference/DATASET.md` (Snapshot-Stand 2026-07-02) und
ist **nicht live verifiziert**. Jeder Fachgebiets-Agent MUSS das bei jeder Datenbindung explizit
kennzeichnen ("lt. DATASET.md, nicht live geprüft") und darf keine Coverage-Zahl als härter behandeln, als
sie hier markiert ist.

Konsequenz für Phase PRE-SCREEN: Ohne Manifest-Zugriff kann kein "Reifegrad: sofort testbar" auf Tages-
genauer `done_days`-Basis verifiziert werden. Die Reifegrad-Einstufungen unten sind daher **Wahrscheinlich-
keitsurteile aus dem dokumentierten Deep-Backfill-Zeitplan**, keine harten Ja/Nein-Befunde. Jeder IC-
Vorschlag, der auf einem konkreten Datumsfenster fußt, muss in PRE-SCREEN entweder (a) die Manifest-Abfrage
aus DATASET.md §7 tatsächlich ausführen lassen (auf der Windows-Maschine des Nutzers), oder (b) sich auf
den **Basis-Bestand** (§5 DATASET.md: 2026-03-27…heute, lückenlos, alle 5 Symbole) beschränken, der laut
Dokumentation bereits vor dem Deep-Backfill fertig war und daher am wenigsten Risiko trägt.

---

## Teil 1 — Daten-Inventar

### 1.1 Reifegrad-Kategorien (verwendet unten)
- **SOFORT NUTZBAR** — laut DATASET.md Teil des fertigen Basis-Bestands (2026-03-27…heute, lückenlos) ODER
  Live-Stream seit Collector-Start; keine Abhängigkeit vom laufenden Deep-Backfill.
- **DEEP-BACKFILL-IM-AUFBAU** — Tiefe wächst gerade rückwärts (Start 2026-07-02, Ziel 2014-01-01…2026-03-26);
  `first_done` kann bereits alt sein, OHNE dass die Lücke geschlossen ist — Nutzung NUR nach expliziter
  Manifest-Prüfung (`done_days == last_done − first_done + 1`).
- **STRUKTURELL NIE VERFÜGBAR (frei)** — laut DATASET.md §5 auch nach Abschluss des Deep-Backfills nicht
  zu erwarten (keine freie Quelle).

### 1.2 Streams × Symbole × Tiefe (aus DATASET.md §4/§5/§7, nicht live verifiziert)

| Stream/Quelle | Symbole | Dokumentierte Tiefe (Ziel nach Deep-Backfill) | Reifegrad JETZT (2026-07-07, 5 Tage nach Deep-Backfill-Start) |
|---|---|---|---|
| Bybit `publicTrade` (Backfill) | 5 Perp (BTC/ETH/SOL/BNB/XRP) | ~2020-07 (BTCUSDT-Listing) je Symbol unterschiedlich; SOL/BNB/XRP erst ~2020-2021 | Basis-Bestand (2026-03-27…heute) SOFORT NUTZBAR; Historie vor 2026-03-27 DEEP-BACKFILL-IM-AUFBAU, Coverage-Check zwingend vor Nutzung |
| Bybit `rest.fundingRate`/`rest.openInterest` | 5 Perp | analog publicTrade | Basis-Bestand SOFORT NUTZBAR; ältere Historie DEEP-BACKFILL-IM-AUFBAU; OI zusätzlich strukturell nur ~30 Tage Historie (Binance-OI-Caveat DATASET.md §9.6) |
| Bybit `orderbook` L2 (bycsi-Backfill) | 5 Perp | **faktisch leer für 2026** (HTTP 404 auf allen 360/Symbol geprüften Tagen, DATASET.md §4 Fußnote 1) | STRUKTURELL NIE VERFÜGBAR per Backfill für das aktuelle Fenster — L2 existiert nur über **Live SRC-04 forward-only ab Collector-Start (~2026-06-16)** |
| Bybit Live (`orderbook`, `tickers`, `allLiquidation`, `insurance`) | 5 Perp (+ USDC-Optionen BTC/ETH) | forward-only | SOFORT NUTZBAR, aber nur ab ~2026-06-16 — **~3 Wochen Historie zum Audit-Datum**, kein Backfill davor möglich |
| Binance `publicTrade` (aggTrades) | 5 Perp | ~2019 (Futures-Start) | Basis-Bestand SOFORT NUTZBAR; ältere Historie DEEP-BACKFILL-IM-AUFBAU |
| Binance `orderbook` (bookDepth, %-Buckets) | 5 Perp | ab 2023-01 | Basis-Bestand SOFORT NUTZBAR; 2023-01…2026-03 DEEP-BACKFILL-IM-AUFBAU |
| Binance `rest.fundingRate`/OI/`liquidationSnapshot` | 5 Perp | analog | Basis-Bestand SOFORT NUTZBAR; OI strukturell nur ~30 Tage Historie |
| Deribit `publicTrade`, `book_summary` | BTC, ETH | ab 2019-03-30 | Basis-Bestand SOFORT NUTZBAR; ältere Historie DEEP-BACKFILL-IM-AUFBAU |
| Deribit `dvol` (Vol-Index) | BTC, ETH | ab 2021-04-01 | Basis-Bestand SOFORT NUTZBAR; 2021-04…2026-03 DEEP-BACKFILL-IM-AUFBAU |
| Deribit Live (`orderbook`, `tickers`, `markprice.options` = volle IV-Surface) | BTC/ETH-PERPETUAL + Options-Surface | forward-only | SOFORT NUTZBAR ab Collector-Start (~2026-06-16), **~3 Wochen Historie** — für IV-Surface-Zeitreihen-Hypothesen zu kurz, für Querschnitts-/Snapshot-Hypothesen (ein Tag Options-Chain) nutzbar |
| BitMEX `publicTrade` (XBTUSD) | XBTUSD | ab 2014-11-22 (**tiefste dokumentierte Historie im ganzen System**) | Basis-Bestand SOFORT NUTZBAR; die volle 2014-Tiefe ist DEEP-BACKFILL-IM-AUFBAU — genau das Fenster, das neue Multi-Zyklen-Hypothesen (mehrere Crashes) tragen könnte, aber JETZT nicht ohne Coverage-Check nutzbar |
| Tardis `options_chain` (IV/Greeks, volle Chain) | Options (ganze Chain/Tag) | ab 2019, aber nur **1 Tag/Monat** Stichprobe | DEEP-BACKFILL-IM-AUFBAU; selbst nach Abschluss strukturell **Stichprobencharakter** (kein tägliches Panel) — jede Hypothese muss das Monats-Sampling explizit als Design-Constraint tragen, nicht als Backtest-Frequenz missverstehen |
| Liquidation-Streams (Bybit `allLiquidation` Live; Binance `liquidationSnapshot` Backfill) | 5 Perp | Bybit forward-only ab ~2026-06-16; Binance analog Basis-Bestand | Bybit: SOFORT NUTZBAR, aber nur ~3 Wochen Historie; Binance: Basis-Bestand SOFORT NUTZBAR, ältere Tage DEEP-BACKFILL-IM-AUFBAU |
| Insurance-Fund (Bybit `insurance`, Live) | 5 Perp | forward-only ab ~2026-06-16 | SOFORT NUTZBAR, ~3 Wochen Historie — für ADL-/Mechanism-Design-Hypothesen (Ereignis-Dichte!) reicht das noch nicht für belastbare N; PROGRAM_FINAL_REPORT §8 nennt für die verwandte C-27/28/29-Kaskaden-Schwelle (~7 Insurance-Events/h) einen Vorlauf bis **Aug.-Okt. 2026** für ≥30 Ereignisse — als Analogie-Richtwert auch für `mechanism-design`-ADL-Hypothesen zu behandeln |
| ADL-Alerts | 5 Perp | Live, aber laut PROGRAM_FINAL_REPORT §7 "adl_alerts-Bybit-Topic-Klärung" als offene Reparatur-WP vermerkt | **UNGEKLÄRT/möglicherweise defekt** — vor Nutzung explizit als offenes Risiko flaggen, nicht blind annehmen |
| Options-IV per-Strike (`tickers.<OPTION>`, Bybit) | BTC/ETH-Optionen | Live forward-only | SOFORT NUTZBAR (Snapshot-artig), ~3 Wochen Historie |
| **5-Symbol-Parität** (BTC/ETH/SOL/BNB/XRP gemeinsam, alle Kern-Streams) | 5 Perp | Bestätigt DEC-10/Lauf 9 laut DATASET.md §4 | Für den **Basis-Bestand (2026-03-27…heute) SOFORT gegeben**; für Historie vor März 2026 ist SOL/BNB/XRP strukturell erst ab **~2020-2021** verfügbar (jünger als BTC/ETH/BitMEX/Deribit) — Panel-Hypothesen mit "langer" Historie müssen sich auf BTC/ETH beschränken oder das Fenster auf ≥2021 begrenzen |

### 1.3 Kurzfassungs-taugliche JETZT-Fenster (für die 6 Disziplin-Agenten)

1. **Basis-Bestand 2026-03-27…heute, alle 5 Symbole, alle Kern-Streams (Trades, Funding, OI, Deribit dvol/book_summary, Bybit L2 nur via Live)** — der einzige Bereich, der OHNE Manifest-Prüfung mit vertretbarem Risiko als "sofort testbar" behandelt werden darf, weil er laut DATASET.md §5 bereits VOR dem Deep-Backfill fertig/lückenlos war.
2. **Live-only-Fenster seit ~2026-06-16 (≈3 Wochen zum Audit-Datum):** L2-Orderbook, volle Options-IV-Surface (Deribit `markprice.options`), Liquidations- und Insurance-Streams. Kurz, aber der EINZIGE Ort im ganzen System mit echter L2-Tiefe und voller IV-Surface — für Querschnitts-/Momentaufnahme-Hypothesen (z.B. Netzwerktopologie über L2-Snapshot, EVT-Tail-Formvergleich über die Options-Chain an einem Tag) nutzbar, für Zeitreihen-Hypothesen mit Wochen-Monats-Horizont (climatology-ensemble!) zu kurz.
3. **BTC/ETH/BitMEX/Deribit-Tiefe potenziell bis 2014/2019** — sobald der Deep-Backfill für diese Serien durchgelaufen ist (Reihenfolge/Fortschritt unbekannt, da kein Manifest-Zugriff). Das ist das Fenster, das "mehrere Marktzyklen/Crashes" (CLAUDE.md §0) tragen könnte — aber JETZT nur mit explizitem Coverage-Check nutzbar, nicht blind.
4. **Tardis Options-Chain-Stichproben (1 Tag/Monat seit 2019)** — für EVT/Tail-Form- oder Cross-Sectional-Snapshot-Hypothesen über lange Zeit, aber strukturell ein Sampling-Design (kein tägliches Panel) — muss in jeder Pre-Registration als Frequenz-Constraint explizit gemacht werden.

### 1.4 Strukturelle Lücken (auch nach Abschluss des Deep-Backfills nicht behebbar)
- L2-Orderbook vor 2023 (frei nicht verfügbar).
- Options-IV-Surface vor Collector-Start, außer den Tardis-Monatsstichproben.
- Binance-OI generell nur ~30 Tage Historie (rollend, keine Tiefe).
- Bybit-L2-Backfill (bycsi) für 2026 strukturell leer (404) — L2 kommt nur über Live vorwärts.

---

## Teil 2 — Ausschlussliste (REFUTED/DROP/PARK)

Basis: CLAUDE.md §1 (bereits kondensiert aus FINAL_PRD/PROGRAM_FINAL_REPORT). Gegenprüfung gegen die
Originalquellen unten — **CLAUDE.md §1 ist vollständig und akkurat**; keine zusätzlichen Einträge in
FINAL_PRD §5/§6 oder PROGRAM_FINAL_REPORT §3/§4 gefunden, die über die CLAUDE.md-Fassung hinausgehen. Zwei
Präzisierungen ergänzt (markiert **[Ergänzung]**), die für die 6 Disziplin-Agenten handlungsrelevant sind,
weil sie den jeweils "abgegrasten" Cluster genauer verorten.

### 2.1 REFUTED (nie wiederholen)
| ID | Ein-Satz-Grund | Abgegrastes Disziplin-Cluster (CLAUDE.md §1) |
|---|---|---|
| C-14 | Hawkes-Branching-Ratio-Schwelle ρ>0.85 strukturell unerreichbar (ρ-Median ≈2e-7, 6 Größenordnungen darunter); Estimator+Schwelle REFUTED, Konzept lebt in C-27 weiter | Seismologie/Statistische Physik (Hawkes/Branching-Ratio) |
| CS-01 | Cascade-Detector feuert 0 Trades, weil das vorgeschaltete C-14-ρ-Gate nie öffnet (nicht Datenmangel) | Seismologie/Statistische Physik |
| CS-02 | Entropie-Momentum: Roh-Edge negativ auf JEDEM Symbol auch ohne Fees, nicht invertierbar (execution-loss-bound) | Informationstheorie/Nichtlineare Dynamik (Entropie-Momentum) |

### 2.2 DROP/PARK (kein Re-Test ohne neues Signal) — H-01…H-08 inkl. b/c
| ID | Urteil | Ein-Satz-Grund | Abgegrastes Disziplin-Cluster |
|---|---|---|---|
| H-01 | DROP (GL-004) | S3-Entry: RAW-Edge −4.48 bps auf allen 5 Symbolen negativ, Entry hat keine eigene Edge | (Futures-Mikrostruktur allgemein, nicht diszplin-spezifisch aus §1) |
| H-02 | DROP (GL-001) | C-42 Vol-RV-Anker: 0/5 Symbole bestehen OOS-R²≥0.15, 0/36 Features FDR-sig; sperrt den gesamten Vol-Stack | Physiologie-nahe Signalverarbeitung (TDA/RQA, C-11/C-12), Radartechnik (CEEMDAN, C-35) — beide PARK, weil sie auf diesem gefallenen Anker aufbauen |
| H-03 | DROP (GL-005) | Cyclostationary CFAR: Surrogate-p≈1.0 auf 4 Fenstern, Edge ~250× unter der 11-bps-Wand | Radartechnik/Signalverarbeitung (CFAR) |
| H-04 | WEITER (Mess, Kapital PARK, GL-006) | BTC→ETH-Lead-Lag FDR-signifikant messbar — aber NUR Mess-Gate, kein Handels-Claim | — (kein §1-Cluster; eigenständiges Mikrostruktur-Paar-Ergebnis) |
| H-04b | PARK (GL-009) | Lead-Lag-Tradability: Netto −14.95 bps, Brutto-Einfang nur +0.19 bps (~80× unter Wand) | — |
| H-05 | DROP (GL-007) | C-01 OFI-Vorzeichen: keine ≥2-Fenster-konsistente positive Signifikanz; ETH invers signifikant | — |
| H-05b | WEITER (Mess, Kapital PARK, GL-010) | Inverses OFI OOS: SOL δ1s/δ5s sign− in beiden Fenstern FDR-sig — nur Mess-Gate | — |
| H-05c | PARK (GL-011) | OFI-Fade-Tradability: Netto −14.9 bps, Einfang +0.03–0.10 bps (~150–500× unter Wand) | — |
| H-06 | DROP (GL-008) | C-07 Permutation Entropy: PRE-Gate ρ≥0.30 in allen 10 Symbol×Fenster-Paaren verfehlt (max +0.0145, ~20× zu klein) | Informationstheorie/Nichtlineare Dynamik (Permutation Entropy, C-07) |
| H-07 | DROP, strukturell (GL-012) | C-06 absolute Cross-Sectional-Z: max\|z\|=√(N−1)=2.0 bei N=5 strukturell unter der registrierten Schwelle 2.5 — **die zentrale GL-012-Lehre, die diesen Agenten begründet** | — |
| H-08 | DROP, empirisch (GL-013) | C-06 Rang-Über-Dehnung: 0 FDR-Survivor, Fenster B (Mai) kollabiert (Momentum statt Reversion) — C-06 dreifach geschlossen (E-04/H-07/H-08) | — |

### 2.3 Zusätzliche Cluster-Sperren aus CLAUDE.md §1 (Disziplinen bereits abgegrast, nicht in H-xx-Tabelle)
| Cluster | Betroffene C-xx | Sperrgrund | Entsperr-Bedingung (falls dokumentiert) |
|---|---|---|---|
| Seismologie/Statistische Physik kritischer Phänomene | Hawkes/Branching-Ratio (C-14/C-27/C-28), Gutenberg-Richter+Omori (C-15), Avalanche-Shape-Collapse (C-29), Natural-Time κ₁ (C-30) | alle bereits PARK/REFUTED | C-36-Recording-Vorlauf, frühestens Aug.–Okt. 2026 (≥30 Kaskaden-Events, PROGRAM_FINAL_REPORT §8) |
| Informationstheorie/Nichtlineare Dynamik | Permutation Entropy (C-07, DROP), Transfer Entropy im Lead-Lag-Test (H-04) | s.o. | keine offene Entsperr-Bedingung für C-07; H-04 bleibt Mess-PARK |
| Physiologie-nahe Signalverarbeitung | TDA/Persistent Homology (C-11), RQA (C-12) | PARK, blockiert durch gefallenen Vol-Stack-Anker (H-02) | nach C-42-Reproduktion (bislang nicht erneut versucht) |
| Radartechnik/Signalverarbeitung | Cyclostationary CFAR (C-31, DROP/"abgegrast"), CEEMDAN (C-35, blockiert durch H-02), Wavelet-Denoising (C-04, PARK) | s.o. | C-35 nach C-42-Reproduktion; C-04 nach validiertem PARTIAL-Abnehmer-Signal |
| Epidemiologie | SIR/R₀-Kaskadenmodell (C-26) | in C-39 absorbiert, kein eigener Pilot | entfällt (kein eigenständiger Pfad) |

**[Ergänzung 1]** C-06 (Cross-Sectional-Z, absolut+Rang) ist über drei unabhängige Wege geschlossen (E-04
Mirror-Test-Verbot aus Scinance 1.0, H-07 strukturell, H-08 empirisch) — FINAL_PRD §5 nennt zusätzlich, dass
eine NICHT-triviale MR-Hypothese für C-06 grundsätzlich offenbleibt, aber "ohne neue Hypothese kein PILOT".
Für `network-topology`/`econophysics-rmt` relevant: eine RMT-Korrelationsmatrix-Hypothese ist NICHT
automatisch von C-06 gesperrt (andere Messgröße: Eigenwert-Spektrum statt Cross-Sectional-Z), muss das aber
im IC-Vorschlag explizit gegen H-07/H-08 abgrenzen.

**[Ergänzung 2]** FINAL_PRD §5 (PARK-Register) enthält weitere, in CLAUDE.md §1 nicht namentlich genannte
Einträge außerhalb der sechs gesperrten Cluster (z.B. C-25 Kyle-λ/VPIN, C-33 VRP, C-40 RPI, C-38 TFT,
C-19 TimesNet, CS-04/CS-05/CS-07/CS-08/CS-10/CS-11/CS-12/CS-13) — diese sind jedoch **keine** der sechs in
CLAUDE.md §1 explizit als "abgegrast" markierten Fachgebiets-Cluster und daher für die 6 neuen
Disziplin-Agenten (RMT, EVT, Netzwerktheorie, Mechanism-Design, Klimatologie, Dendrochronologie) nicht per
se gesperrt — sie betreffen andere Methoden (Optionen-Preistheorie, Deep Learning, Marktdesign-Sonderfall
RPI) und keine Überschneidung mit den neuen Fachgebieten, solange die Disziplin-Agenten nicht zufällig
dieselbe Kennzahl (z.B. IV−RV-Spread wie C-33) re-implementieren. Sollte ein Agent auf eine
methodische Nähe zu einem dieser PARK-Einträge stoßen (z.B. `evt-actuarial` zu C-33 VRP, `mechanism-design`
zu C-40 RPI/ADL), ist das explizit als Cross-Domain-Hinweis/Abgrenzung im IC-Vorschlag zu dokumentieren,
nicht automatisch als Ausschluss zu werten — reines Namens-/Themen-Nachbarschaft ist kein CLAUDE.md-§1-Treffer.

---

## Bindungshinweis für PRE-SCREEN
Jeder IC-Vorschlag, der einen der Cluster/Ids aus Teil 2 berührt, ist ohne nachweislich andere Messgröße ein
automatischer Selbst-Kill (CLAUDE.md §1). Jeder IC-Vorschlag, der einen Datenstrom aus Teil 1 als
"DEEP-BACKFILL-IM-AUFBAU" gebunden hat, braucht in PRE-SCREEN entweder eine echte Manifest-Coverage-Prüfung
oder eine Beschränkung auf den Basis-Bestand/Live-Fenster, bevor er als "sofort testbar" gilt.
