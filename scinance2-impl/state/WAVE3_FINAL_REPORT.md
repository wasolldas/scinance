# Welle-3-Abschlussbericht — Scinance 2.0

**Branch:** `scinance2-wave2` (Welle 3 lief ohne eigenen Branch auf dem Welle-2-Endstand; vgl. `wave3_survey.md` §6 Branch-Hinweis)
**Stand:** 2026-07-02
**Status:** DONE (Welle 3) — alle vier Welle-3-Gates entschieden (H-05b, H-05c, H-07, H-08)

---

## 1. Executive Summary

Welle 3 ist abgeschlossen. Vier Gates wurden gegen die vorregistrierten Tore der Hypothesen-Registry entschieden: **H-05b WEITER (inverse OFI-Mess-Existenz, kapitalfrei, Kapital PARK)** *(GL-010)*, **H-05c PARK (inverse Kante nicht handelbar)** *(GL-011)*, **H-07 DROP (struktureller A-priori-Power-DROP — erstes rein mathematisches Verdikt des Programms)** *(GL-012)*, **H-08 DROP (empirisch)** *(GL-013)*. Welle 3 ist zugleich die erste Welle auf dem **externen Datenharvester** (read-only Junction `data/harvest`, Backfill bis 2026-03-20) statt der Collector-DuckDB — das ermöglichte echte **Pre-Discovery-OOS-Fenster** (April/Mai, DEC-15) statt wochenlangem Warten auf Forward-Daten *(decisions.md DEC-15)*. Inhaltliches Kernergebnis: Das Muster „reales Mikrostruktur-Signal existiert, überlebt aber Friktion+Latenz nicht" ist jetzt **zweimal repliziert** (H-04→H-04b in Welle 2, H-05b→H-05c in Welle 3); der OFI-Vorzeichen-Komplex ist vollständig erschöpft (H-05 DROP / H-05b Mess-WEITER / H-05c PARK, kein H-05d) *(GL-011 §Symmetrie/Erschöpfung)*, und C-06 ist dreifach geschlossen (Trivial-MR E-04-verboten, absolute Über-Dehnung H-07 strukturell, Rang-Über-Dehnung H-08 empirisch) *(GL-013)*. Programm-Bilanz nach 13 Gate-Verdikten: **2 kapitalfreie Mess-WEITER, beide Tradability-PARK, 0 handelbare Kanten, 0 Torpfosten-Verschiebungen** *(GL-013 Programm-Bilanz)*.

## 2. Die vier Gate-Verdikte

### Übersicht

| Gate | Vorregistrierte Schwelle | Messwert (tragend) | Ergebnis | GL-Referenz |
|---|---|---|---|---|
| **H-05b · OFI invers OOS** (KAPITALFREI) | sign=− UND p ≤ 0.05 BH-FDR (F-OFI-INV) UND ≥ 2-Fenster-Konsistenz aus Nicht-Entdeckungszellen UND \|corr\| ≥ 0.05 ODER Hit-Rate ≤ 0.47 | SOLUSDT δ1s/δ5s: sign− + FDR-sig in BEIDEN Fenstern (p_crit 0.0199); HR 0.4095–0.4605 ≤ 0.47; corr −0.0102…−0.0505 | **WEITER** (schmal; Kapital PARK) | *(GL-010 · 2026-06-30)* |
| **H-05c · OFI-Fade-TRADABILITY** (capital_free=FALSE) | Netto-Edge > 0 UND Bootstrap-p ≤ 0.05 (F-OFI-INV-TRADE) in ≥ 2 Fenstern, Latenz ≥ 300 ms, Wand ≥ 11 bps + 4 bps Slippage | alle 4 Zellen Netto −14.97…−14.90 bps, Bootstrap p=1.0000, 0 FDR-Survivor; Brutto-Einfang +0.031…+0.099 bps (~150–500× unter 15-bps-Wand) | **PARK** | *(GL-011 · 2026-07-01)* |
| **H-07 · C-06 absolute Über-Dehnung** (KAPITALFREI) | Achse A \|z\| ≥ 2.5 UND N-Floor ≥ 30 Events/Fenster UND CI-Verstärkungs-Anker | max\|z\| = √(N−1) = 2.0 (Population) / 1.79 (Sample) auf N=5 → 0 Events möglich → N-Floor reißt mit Sicherheit | **DROP** (strukturell, kein Datenlauf) | *(GL-012 · 2026-07-01)* |
| **H-08 · C-06 Rang-Über-Dehnung** (KAPITALFREI) | kond. μ_rev > 0 UND p ≤ 0.05 BH-FDR (F-XMR-RANK) UND ≥ 2 Fenster UND nicht-überlappende 95%-CIs kond>baseline UND N ≥ 30 | N 501–508/Fenster (feasible), aber 0 FDR-Survivor (p 0.0796–0.9453), CI-Anker in allen 6 Zellen verfehlt, B-h6 μ_rev −0.8 bp | **DROP** (empirisch) | *(GL-013 · 2026-07-02)* |

Chronologie der Welle (jeweils Pre-Registration VOR Lauf/Urteil, Registry-Disziplin §1–3): 2026-06-29 DEC-15-Fensterfixierung → 2026-06-30 H-05b-Lauf + GL-010 + H-05c-Registrierung (DEC-16) + H-05c-Build → 2026-07-01 GL-011 + H-07-Registrierung (DEC-17) + c06_xmr-Build + GL-012 + H-08-Registrierung (DEC-18) + Rang-Build → 2026-07-02 H-08-Lauf + GL-013 *(wave2_state.md W3-CHANGELOG)*.

### H-05b — Inverse OFI-Lesart, OOS-konfirmiert (Data-Snooping-Guard per Konstruktion)

Der konfirmatorische Lauf `h05b_oos_20260630_091035` lief auf dem **Harvester-Backfill** (5 Symbole, δ ∈ {1,5,15,60,300} s, 2 per Datum vorab fixierte Fenster A@2026-04-15 + B@2026-05-15 à 300 000 Ticks/Symbol, F-OFI-INV BH-FDR α=0.10) *(GL-010 Quelle + Registry H-05b WP-0-Nachtrag 2026-06-29)*. Die Entdeckungszelle (ETHUSDT, **Juni**-Collector, δ1s) ist **per Konstruktion ausgeschlossen** — der H-05-Entdeckungslauf hat die April/Mai-Daten nie gesehen; Regel 1–3 des Data-Snooping-Guards sind konstruktiv erfüllt *(GL-010 Disziplin-Frage 3, DEC-15)*. Befund: 16 FDR-signifikante Zellen (12 negativ, 4 positiv; p_crit 0.0199), davon genau **2 inverse-konsistent über beide Fenster: SOLUSDT δ1s und δ5s** — die WEITER-Kriterien sind an diesen Zellen literal erfüllt, das harte Ein-Fenster-DROP nicht ausgelöst, die Symmetrie-Falle greift nicht (eine konsistent-negative Zelle existiert) *(GL-010 Je-Kriterium-Tabelle + A/B-Lesart)*. **Ehrlich dokumentierte Schmalheit (Pflicht-Bestandteil des WEITER):** nur 1 Symbol, nur 2 Lags; der primäre |corr|≥0.05-Anker ist nur in 1 von 4 tragenden Messpunkten (w1 δ1s, 0.0505, knapp) erfüllt, die Magnitude ist überwiegend vom sekundären Hit-Rate-Anker getragen; das Entdeckungssymbol ETH trägt die Konfirmation selbst NICHT; das Familienbild ist vorzeichen-gemischt *(GL-010 §SCHWÄCHE/SCHMALHEIT)*. KAPITALFREI: keine handelbare Aussage; H-05c wurde durch das WEITER nicht impliziert, sondern separat vorregistriert.

### H-05c — Die inverse Kante gegen die Friction-Wand (zweites Tradability-Gate)

Vorregistriert per DEC-16 als exaktes Gegenstück zur H-04→H-04b-Trennung: Fade-Regel (Position entgegen OFI-Vorzeichen, horizon=δ), nur die GL-010-Survivor-Zellen SOL-δ1s/δ5s urteilstragend, Friction-Wand 11 bps Taker + 4 bps Slippage, Latenz-Haircut 300 ms, Anti-Gaming-Klausel mit `gate_valid_assumptions`-Flag *(Registry H-05c + decisions.md DEC-16)*. Der urteilstragende PRIMARY-Block (29 813 + 25 523 Round-Trips bei δ1s) liefert in allen 4 Zellen **Netto −14.97…−14.90 bps, Bootstrap p=1.0000, 0 FDR-Survivor (p_crit 0.0000)** *(GL-011 Zellen-Tabelle + h05c_20260701_153543/h05c/h05c_results.json)*. Entscheidend die Doppel-Aussage: der **Surrogate-p ist auf allen 4 Zellen 0.0050** — die Fade-Richtung ist real und nicht-zufällig (konsistent mit dem H-05b-WEITER) —, aber der Brutto-Einfang nach Latenz-Haircut beträgt **+0.031…+0.099 bps** gegen eine 15-bps-Gesamt-Wand: ~150–500× darunter *(GL-011 Mechanistische Schlussfolgerung)*. Robustheits-Spanne MIT-berichtet, nicht urteilstragend: LAT100/LAT500 identisch negativ, selbst der adverse-selection-vorbehaltliche MAKER-Block bleibt −5.97…−5.90 bps *(GL-011 Anti-Gaming-Tabelle)*. Kein WEITER unter irgendeiner zulässigen Annahme; hartes Ein-Fenster-PARK. Operativer Nebenbefund: ein Runner-Bug (`run_h05c.ps1` fehlender Skript-Pfad, rc=2) wurde **vor** dem urteilstragenden Lauf gefunden und gefixt (Commit 163c184) *(wave2_state.md W3-H05c-GATE)*.

### H-07 — Der erste strukturelle A-priori-DROP des Programms

H-07 (C-06 nicht-triviale Cross-Sectional-MR, Achse A |z| ≥ 2.5 aus M13/§7.5 wörtlich, Nicht-Trivialitäts-Anker gegen den unkonditionierten Baseline, DEC-17) fiel **ohne Datenlauf**: die Cross-Sectional-z-Statistik über N Punkte ist hart beschränkt durch **max|z| = √(N−1)**; auf dem verfügbaren 5-Symbol-Panel also 2.0 (Population-Std) bzw. 1.79 (Sample-Std) — beides unter der registrierten Literatur-Schwelle 2.5, die für ein Top-20-Panel gesetzt war (√19 ≈ 4.36) *(GL-012 Struktureller Befund + Registry H-07-Nachtrag 2026-07-01)*. Achse A feuert nie → 0 konditionierte Events → der vorregistrierte N-Floor (≥ 30/Fenster) reißt mit mathematischer Sicherheit → DROP. **Torpfosten-Disziplin:** Z_THRESH wurde NICHT abgesenkt, um N>0 zu erzwingen (in H-07 explizit verboten); der DROP wurde **angenommen, nicht umgangen** *(GL-012 Abgrenzung zur Torpfosten-Verschiebung)*. H-07 scheiterte an der Datenlage (5 statt 20 Symbole — exakt das in research_notes §7.5 antizipierte Power-Risiko), nicht an einer Widerlegung der MR-Verstärkung selbst; die panel-robuste Rang-Definition wurde als NEUE H-08 separat vorregistriert.

### H-08 — Rang-Über-Dehnung: feasible, aber empirisch tot (der Survivorship-Guard griff)

H-08 ersetzt die unerreichbare absolute Schwelle durch die **schwellen-freie Rang-Definition** (argmax|z| je Bar, Gleichstand deterministisch alphabetisch) — der einzige forking-paths-freie Ausweg, denn jede abgesenkte |z|-Schwelle wäre eine verkappte Z_THRESH-Absenkung *(decisions.md DEC-18)*. Der Lauf `h08_20260702_085014` (5er-Panel, 5-min-Bars, DEC-15-Kalenderfenster, h ∈ {1,3,6}, F-XMR-RANK, 68 s, rc=0) bestätigt zuerst die Konstruktion: **N-Floor überall erfüllt (501–508 Events/Fenster)** *(GL-013 Je-Kriterium-Tabelle)*. Dann reißen alle urteilstragenden Kriterien: **0 FDR-Survivor** (Surrogate-p 0.0796–0.9453, p_crit 0.0000), Nicht-Trivialitäts-Anker (CI-Nicht-Überlappung kond vs. baseline) **in allen 6 Zellen verfehlt**, und Fenster B (Mai) kollabiert (Δμ ≤ 0 bei h3/h6; μ_rev(h6) = −0.8 bp, Momentum statt Reversion), während Fenster A (April) schwach positiv war (μ_rev +0.9/+2.2/+2.3 bp; Δμ +0.8…+1.6 bp, n.s.) *(GL-013)*. Das ist exakt das vorregistrierte Survivorship-Szenario (research_notes §7.5, XRP-April): der ≥ 2-Fenster-über-Regimes-Zwang war als Guard konstruiert und hat den April-only-Effekt wie vorhergesagt aussortiert. Die E-04-verbotene Trivial-Lesart wurde per Anker-Konstruktion nie als Erfolgspfad angeboten. **C-06 ist damit vollständig geschlossen** — dreifach: Trivial-MR (E-04, PRD-§6-verboten, nie als Pass getestet), absolute Über-Dehnung (H-07, strukturell), Rang-Über-Dehnung (H-08, empirisch); kein H-08b/H-09 nahegelegt *(GL-013 Urteil)*.

### FDR-Führung der Welle 3 — sequenzielle Einzel-Läufe statt Kohorte

Anders als Welle 2 (drei parallele Pilots → zweistufige Über-Familie F-WAVE2) lief Welle 3 als **rollierende Folge von Einzel-Läufen**; nach der Registry-Regel greift dann nur die Familien-interne BH-FDR α=0.10, und **F-WAVE2 wurde in keinem Fall erweitert** (append-only abgeschlossen seit GL-006/007/008) *(Registry H-05b/H-05c/H-07/H-08 §FDR-Familie; wave3_survey.md §4 Über-Familien-Empfehlung)*. Vier neue Familien wurden vorab registriert und je einmal verbraucht:

| Familie | Hypothese | Zellen | p_crit | Survivor |
|---|---|---|---|---|
| **F-OFI-INV** | H-05b | 5 Symbole × 5 δ × 2 Fenster | 0.0199 | 16 FDR-sig (12 neg / 4 pos), 2 inverse-konsistent *(GL-010)* |
| **F-OFI-INV-TRADE** | H-05c | SOL-δ1s/δ5s × 2 Fenster | 0.0000 | 0 *(GL-011)* |
| **F-XMR** | H-07 | — | — | nie gelaufen (struktureller DROP vor jedem Datenlauf) *(GL-012)* |
| **F-XMR-RANK** | H-08 | 3 h × 2 Fenster | 0.0000 | 0 *(GL-013)* |

Eine F-WAVE3-Über-Familie wurde bewusst NICHT prophylaktisch konstruiert — sie wäre nur bei ≥ 2 gleichzeitig laufenden neuen Hypothesen fällig gewesen; die sequenzielle Führung vermeidet α-Budget-Verbrauch durch Familien, die nie zustande kommen *(wave3_survey.md §4)*.

## 3. Infrastruktur- und Betriebsstand — die Harvester-Wende

Welle 3 ist die erste Welle, deren sämtliche urteilstragenden Läufe auf dem **externen Datenharvester** liefen (read-only Junction `data/harvest`, Hive-Tree `raw/bybit/publicTrade/symbol=<SYM>/date=<d>/`, Backfill bis 2026-03-20; Coverage per `harvest_coverage.py` 2026-06-29: alle 5 Symbole April+Mai durchgehend DONE — ETHUSDT 97 DONE-Tage 2026-03-20..06-24, BTC ab 03-18, BNB/SOL/XRP ab 03-26) *(Registry H-05b WP-0-Nachtrag + DEC-15)*. Der methodische Gewinn ist nicht Komfort, sondern Test-Qualität: statt auf Forward-Daten zu warten (Welle-2-Schätzung für die H-05b-Reife: „konservativ ca. 30.06.–02.07.2026" *(wave3_survey.md §2.1)* — getroffen), standen **Pre-Discovery-Fenster** zur Verfügung, die der Entdeckungslauf nie gesehen hat; zugleich sind die urteilstragenden Läufe von Stunden (Collector-DuckDB, T3) auf Sekunden bis ~1 Minute (T2) gefallen (§7). Konsequenzen und flankierende Betriebsarbeit:

- **DEC-14 Cleanup-Schnitt (2026-06-23):** Scinance-1.0-Live-Stack (live_runner, multi_runner, Pipeline, S1–S5, Dashboard, Backtester, Tuning, Executor u.a.) **DEPRECATE** — alle 5 Strategien empirisch erledigt, kein Live-Order-Betrieb mehr; Bybit-Collector + `bybit_edge.duckdb`-Schreibpfad **REPLACE durch Harvester**; `m8_bocpd`-Off-by-One bewusst NICHT gefixt (Phantom-Bug nach Deprecation). Inventar: `CLEANUP_PLAN.md` (378 Zeilen, 19 KEEP / 21 DEPRECATE / 2 REMOVE / 3 REPLACE, 16 TODOs); 22 DEPRECATE-Header-Marker gesetzt, `start.bat` auf 3-Optionen-Menü umgebaut *(decisions.md DEC-14, wave2_state.md CLEANUP)*.
- **Audit-Freeze (2026-06-23):** `bybit_edge.duckdb` (1 048 326 144 Bytes ≈ 1.0 GB) als read-only Audit-Bestand eingefroren, Kopie `data/audit/bybit_edge_frozen_20260623.duckdb`, SHA-256 `22EE0451F3696B4CCAEDDA44A414DE903DB0CE476BE0EAAB3CE797F66F087902` — die Welle-1/2-Verdikte bleiben gegen exakt diesen Bestand reproduzierbar *(wave2_state.md AUDIT-FREEZE)*.
- **Recorder-Härtung (2026-06-27):** C-36-Recorder (Schutzgut #1) mit Autostart via Task Scheduler (Task „Scinance C-36 Recorder", AtLogOn +30 s, 3× Crash-Restart, kein Time-Limit), `start_recorder.ps1` mit **Single-Instance-Guard** gegen Doppel-Writer; verifiziert 1 logischer Recorder, rpi_orderbook live bei 102 167 231 Zeilen. Dokumentierter Daten-Caveat: ~2026-06-23 16:33 bis 06-27 13:53 liefen zeitweise ZWEI Recorder → `recording_f0`-Konsumenten müssen über dieses Fenster per (stream, ts_exchange_ms, payload) deduplizieren. option_tickers weiterhin NO_DATA, adl_alerts EMPTY_OK/phantom *(wave2_state.md RECORDER-OPS)*.

Datenbasis-Stand am Welle-3-Ende, konsolidiert:

| Quelle | Rolle | Stand / Status | Quelle-Zitat |
|---|---|---|---|
| Harvester `data/harvest` | einzige aktive Bybit-Alpha-Datenquelle (+ Binance, Deribit-IV) | Backfill ab 2026-03-20, read-only Junction, Schema-validiert | *(DEC-14 (b), DEC-15, Registry H-05b-Nachtrag)* |
| `bybit_edge.duckdb` | eingefrorener Audit-Bestand der Welle-1/2-Verdikte | ~1.0 GB, SHA-256 dokumentiert, IsReadOnly=True | *(wave2_state.md AUDIT-FREEZE)* |
| C-36 `recording_f0` | Schutzgut #1, Vorlauf für C-27/28/29/39/33 | rpi_orderbook >102 Mio Zeilen, Autostart + Guard; Dedup-Caveat 06-23..06-27 | *(wave2_state.md RECORDER-OPS)* |
| Scinance-1.0-Live-Stack | DEPRECATE (Audit-Trail im Code belassen) | 22 DEPRECATE-Marker, kein Schreiber mehr aktiv | *(DEC-14, wave2_state.md CLEANUP)* |

## 4. Was empirisch erledigt ist

- **OFI-Vorzeichen-Komplex vollständig abgearbeitet:** H-05 (positiv/Aggression-Folge) DROP *(GL-007)*, H-05b (invers/MM-Replenishment) kapitalfreies Mess-WEITER auf SOL-Kurzlags *(GL-010)*, H-05c (inverse Tradability) PARK *(GL-011)*. Eine andere Latenz/Wand-Annahme wäre eine NEUE H-05d — nicht registriert, durch das PARK nicht nahegelegt *(GL-011 Urteil)*.
- **Das Mess-vs-Tradability-Muster ist repliziert:** H-04→H-04b (Brutto-Einfang +0.19 bps, ~80× unter Wand) und H-05b→H-05c (+0.03…+0.10 bps, ~150–500× unter Wand) zeigen unabhängig dasselbe: reale, surrogate-signifikante Mikrostruktur-Signale existieren, keines überlebt Friktion+Latenz. Der S2-2023-Trap (Signal mit Handelbarkeit verwechseln) wurde in beiden Fällen vom vorregistrierten Gate-Paar abgefangen *(GL-011 Programm-Bilanz)*.
- **C-06 dreifach geschlossen** (E-04-verboten / H-07 strukturell / H-08 empirisch); der C-06-Hypothesenraum auf dem verfügbaren 5-Symbol-Panel ist erschöpft *(GL-013)*.
- **Die A-priori-Vorhersagen der Verfassung halten weiter:** wie schon PRD §4 Z.133 bei H-04b („abgegraste HFT-Anomalie → PARK") wurden auch die in H-05c/H-07/H-08 jeweils **vorab** als erwarteter Ausgang benannten PARK/DROP-Pfade exakt getroffen (H-05c: Sub-bps-Signal vs. 15-bps-Wand; H-07: research_notes-§7.5-Power-Warnung „5 Symbole zu eng gekoppelt"; H-08: Survivorship-/Verdünnungs-A-priori) *(Registry H-05c/H-07/H-08 §A-priori; GL-011/012/013)*.
- **Programm-Gesamtbilanz:** Welle 1: 3 DROP. Welle 2: 1 WEITER (kapitalfrei) + 1 PARK + 2 DROP. Welle 3: 1 WEITER (kapitalfrei) + 1 PARK + 2 DROP. 13 Gate-Verdikte, 2 Mess-WEITER (H-04, H-05b), beide Tradability-PARK, **0 handelbare Kanten, 0 Torpfosten-Verschiebungen** *(GL-013 Programm-Bilanz)*.

## 5. Welle-3-Werkzeug- und Methoden-Erbe

- **Struktureller A-priori-DROP als Urteils-Klasse** *(GL-012)*: erstmals wurde ein Gate aus einer beweisbaren Eigenschaft von (Gate, Panel) entschieden statt aus einem Datenlauf — ohne Torpfosten-Schub, mit dokumentiertem Beweis (max|z|=√(N−1)) und explizitem Verzicht auf das „Retten durch Schwellen-Absenkung". Wiederverwendbares Muster: Feasibility der registrierten Schwelle VOR dem Lauf mathematisch prüfen.
- **Data-Snooping-Guard mit Ausschluss per Konstruktion** *(DEC-15, GL-010)*: Pre-Discovery-Backfill macht den Entdeckungszellen-Ausschluss zur Eigenschaft der Datenbasis statt zur Audit-Fußnote — stärker als Post-Discovery-Forward-Daten (regime-unabhängiger, keine Doppel-Trade-Caveats an der Backfill/Live-Grenze).
- **Forking-Paths-Guard mit schwellen-freier Definition** *(DEC-17/DEC-18, Registry H-07/H-08)*: genau 2 vorab fixierte Konditionierungs-Achsen, Offenlegungstabelle im Draft (`c06_h07_draft.md`), Rang-Definition als einziger parameterfreier Ausweg statt gesuchter Ersatz-Schwelle; Verdünnungs-Preis ehrlich benannt, Beweislast vollständig auf dem CI-Anker.
- **Neue Module** (alle standalone, read-only, per Verzeichnis-Löschung rückbaubar): `c01_ofi_sign/oos.py` (366 LoC, Harvester-Loader + F-OFI-INV-Rollup), `c01_ofi_tradability/` (5 Dateien, 720 LoC, Fade-Regel + costs/net_edge nach `c17_c41_tradability`-Vorlage), `c06_xmr/` (5 Dateien, 1 205 LoC, Panel-Sync + Cross-Sectional-z + CI-Anker + `overextension`-Modus z/rank per DEC-18; z-Default bit-identisch zum H-07-Pfad) *(wave2_state.md W3-CHANGELOG; LoC per wc verifiziert)*.
- **Tests:** c01-Ökosystem 33→53 (+9 H-05b-OOS, +11 H-05c), c06_xmr 29 (17 H-07 + 12 H-08, Test-Datei append-only); Suite-Stand ≈ 957 grün (908 Welle-2-Endstand + 20 + 29), 0 Modul-Bugs zur Gate-Laufzeit; 1 Runner-Bug (run_h05c.ps1) VOR dem Lauf gefixt *(wave2_state.md W3-H05c-GATE/H-05c-BUILD/W3-H08-BUILD)*.
- **Audit-Trail:** 5 DEC (DEC-14 Cleanup, DEC-15 OOS-Fenster, DEC-16 H-05c-Gate, DEC-17 H-07-Methoden, DEC-18 Rang-Definition), 4 GL (GL-010..013), 4 Registry-Einträge/Nachträge (H-05b-WP-0-Nachtrag+Status, H-05c, H-07 inkl. Struktur-Nachtrag, H-08) — alle append-only *(decisions.md, gate_log.md, hypothesis_registry.md)*.

## 6. Ausblick — die Pipeline ist daten-gated, nicht arbeits-gated

Der entscheidende Zustandswechsel nach Welle 3: es gibt **keine sofort lauffähige, ehrlich registrierbare Alpha-Hypothese mehr**, deren Blocker Arbeitszeit wäre. Jeder verbliebene Pilot wartet auf Daten:

| Pfad | Blocker | Horizont |
|---|---|---|
| C-20 MOMENT Zero-Shot | braucht frische Bybit-Neulistings (N=10–20) + Heavy-Dep-Entscheidung | Wochen–Monate Listings-Vorlauf *(wave3_survey.md §2.2)* |
| C-27/C-28/C-29 + C-39/CS-06 Kaskaden | ≥ 30 Kaskaden Recording-Vorlauf; insurance_pool ~7 Events/h; Recording-Stand ~3 Wochen | C-29 ca. Anfang Aug. 2026, C-27/28 ca. Sept.–Okt. 2026 *(wave3_survey.md §3)* |
| C-33 VRP / Short-Vola | ≥ 12 Monate IV-Recording + Stress-Periode; option_tickers-NO_DATA-Defekt weiter offen | frühestens Mitte 2027 *(wave3_survey.md §3)* |
| C-40 RPI | per PRD Forschungs-/Sicherungs-Asset, **kein Alpha-Gate** | Tooling-WP, kein Registry-Eintrag *(wave3_survey.md §2.4)* |
| Vol-Stack (C-10/11/12/34/35, VRP-RV) | H-02-Kaskade; H-02b bräuchte bit-genaue Original-Feature-Spec (Außen-Arbeit) | blockiert *(WAVE1_FINAL_REPORT §6, wave3_survey.md §2.5)* |
| C-25 Toxic Flow / CS-07-C-31-Bein / C-08 / C-37 / CS-12 | zirkulär (keine positive Basis-Strategie) bzw. durch Welle-1/2-DROPs versperrt | blockiert / tote Spur *(wave3_survey.md §1)* |

Passiv laufen und werden mit der Zeit wertvoller: der **C-36-Recorder** (jetzt mit Autostart + Single-Instance-Guard) und der **Harvester** (inkl. Deribit-Options-IV, der langfristig den C-33-Vorlauf entsperrt) *(DEC-14 (b), wave2_state.md RECORDER-OPS)*. Der erste **Sunset-Review** (Anti-Data-Lake-Bremse, 3 Monate nach Recording-Start) fällt auf **ca. 2026-09-11** *(wave3_survey.md §5/§6)*. Bis dahin ist die ehrlichste Programm-Haltung: keine Hypothese erfinden, um beschäftigt zu sein — der wave3_survey-Befund „Welle 3 wird Hypothesen-Erarbeitungs-Arbeit" hat sich verschärft zu „Welle 4 wird Daten-Reife-Arbeit".

## 7. Welle-3-Kosten-Ehrlichkeit

Beziffert (aus `wave2_state.md` W3-CHANGELOG, `steps.tsv` der Lauf-Verzeichnisse, wc-verifizierte LoC):

- **Rechenzeit der urteilstragenden Läufe: Minuten statt Stunden** — der Harvester-Effekt. `h05b_oos` 61 s (1 Block), `h05c` 27 s (4 Blöcke: 8+7+6+6 s), `h08` 68 s (1 Block); zusammen ~156 s T2 *(steps.tsv in h05b_oos_20260630_091035 / h05c_20260701_153543 / h08_20260702_085014)*. Zum Vergleich: der Welle-2-Hauptlauf brauchte 2–4 h T3 *(WAVE2_FINAL_REPORT §7)*. H-07 kostete **null** Rechenzeit (struktureller DROP).
- **~2 300 LoC Welle-3-Produktion** (oos.py 366 + c01_ofi_tradability 720 + c06_xmr 1 205) plus Runner `run_h05b_oos/run_h05c/run_h08.{ps1,sh}` + READMEs.
- **+49 Tests** (c01-Ökosystem 33→53, c06_xmr 0→29), Suite ≈ 957 grün; 0 Modul-Bugs in den Gate-Läufen, 1 Runner-Bug vor Urteil gefixt.
- **5 DEC + 4 GL + 4 Registry-Einträge/Nachträge**, alle reversibel dokumentiert.
- **Nutzer-Maschinen-Aufwand:** 3 T2-Runner-Aufrufe (je 1 Doppelklick, alle rc=0, `ok=… fail=0 skip=0`) *(SUMMARY-Dateien der drei Lauf-Verzeichnisse)* plus die manuellen Cleanup-TODOs 1/2/4/6 (Zombie-Kill, Live-Stopp, Recording-Check, Audit-Freeze) *(DEC-14 Akteur-Verteilung)*.
- **Roh-Daten committet:** `handoff_local/results/h05b_oos_20260630_091035/` + `h05c_20260701_153543/` (4 Blöcke) + `h08_20260702_085014/` — jedes Verdikt bleibt gegen sein Roh-JSON reproduzierbar.
- **Ops-Arbeit ohne Alpha-Anspruch:** Cleanup-Plan (378 Zeilen, 22 DEPRECATE-Marker), Audit-Freeze (1.0-GB-DuckDB + SHA-256), Recorder-Autostart+Guard, Harvester-Junction + `harvest_coverage.py` *(wave2_state.md CLEANUP/AUDIT-FREEZE/RECORDER-OPS, Registry H-05b-Nachtrag)*.

Diese Kosten kaufen: die OOS-Konfirmation eines data-snooped Effekts unter strengem Guard (H-05b), die ehrliche Tradability-Falsifikation desselben Signals (H-05c), zwei C-06-Schließungen — davon eine per mathematischem Beweis statt Rechenlauf (H-07) und eine mit greifendem Survivorship-Guard (H-08) — sowie die vollständige Ablösung der Live-Legacy durch eine auditierbare, read-only Datenbasis.

## 8. Empfehlung

- **Keine Welle 4 auf Vorrat starten.** Alle verbliebenen Pfade sind daten-gated (§6). Nächster natürlicher Programm-Termin ist der Sunset-Review ~2026-09-11; bis dahin nur passives Sammeln (Recorder + Harvester) plus die zwei offenen Reparatur-WPs (option_tickers-Keepalive, adl_alerts-Topic) *(wave3_survey.md §3/§5)*.
- **Feasibility-Check als Pflicht-Schritt vor jeder Registrierung:** die GL-012-Lehre — prüfe VOR dem Lauf, ob die registrierte Schwelle auf der verfügbaren Datenbasis mathematisch erreichbar ist. Ein struktureller DROP ist billiger und ehrlicher als ein leerer Datenlauf, aber am billigsten ist eine Schwelle, die zum Panel passt und trotzdem nicht gesucht wurde.
- **Mess-Gate/Tradability-Gate-Trennung bleibt Verfassungsrang:** zweimal repliziert (H-04b, H-05c), beide Male mit Anti-Gaming-Klausel und MIT-berichteter Robustheits-Spanne. Jede künftige Edge-berührende Hypothese läuft als eigenes nicht-kapitalfreies Folge-Gate.
- **Pre-Discovery-OOS als Standard** für jede aus Daten geborene Folge-Hypothese: der DEC-15-Pfad (temporal unabhängiger Backfill, Entdeckungszellen-Ausschluss per Konstruktion) ist dem Forward-Warten methodisch und operativ überlegen.
- **Keine Reaktivierung gefallener Pilots** ohne neue H-0xb-Zeile; kein H-05d, kein H-08b/H-09 — beide sind ausdrücklich nicht nahegelegt *(GL-011/GL-013)*. Torpfosten-Verschiebung bleibt in beide Richtungen verboten (auch die erschwerende, vgl. GL-010 Disziplin-Frage 4).
- **Ehrliche Erwartung an C-20/C-27ff:** die A-priori-Skepsis des Programms (13 Verdikte, 0 handelbare Kanten) gilt unverändert; die Recording-abhängigen Pilots sind Falsifikationstests mit erwartetem DROP, keine Hoffnungsträger. Das Programm misst seinen Wert in sauberen Verdikten, nicht in Überlebenden.

---

*Quellen durchgängig: `state/gate_log.md` (GL-010/011/012/013 + Programm-Bilanzen), `state/hypothesis_registry.md` (H-05b + WP-0-Nachtrag 2026-06-29, H-05c, H-07 + Struktur-Nachtrag 2026-07-01, H-08, Registry-Disziplin §1–8), `state/decisions.md` (DEC-14/15/16/17/18), `state/wave2_state.md` (CHANGELOG CLEANUP, AUDIT-FREEZE, RECORDER-OPS, W3-H05b-GATE..W3-H08-GATE), `state/wave3_survey.md` (§1–6 Pilot-Universum, Recording-Reife, Sequenzierung), `state/CLEANUP_PLAN.md`, `state/WAVE1_FINAL_REPORT.md` §6 / `state/WAVE2_FINAL_REPORT.md` §7 (Vergleichswerte), `handoff_local/results/h05b_oos_20260630_091035/{SUMMARY_2026-06-30.md, steps.tsv, h05b/h05b_oos_results.json}`, `handoff_local/results/h05c_20260701_153543/{SUMMARY_2026-07-01.md, steps.tsv, h05c*/h05c_results.json}`, `handoff_local/results/h08_20260702_085014/{SUMMARY_2026-07-02.md, steps.tsv, h08/c06_xmr_results.json}`.*
