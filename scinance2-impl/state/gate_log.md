# Gate-Log (append-only · PRD §8.3 / Registry-Disziplin §3)

> Format je Eintrag: Datum · Gate · registrierte Schwelle · gemessener Wert · Urteil · Konsequenzen.
> Geurteilt wird AUSSCHLIESSLICH gegen `state/hypothesis_registry.md` (H-01/H-02/H-03).
> Torpfosten-Verschiebung verboten (§2). Mess-Lücken aus Nacht-Läufen sind kein Gate-FAIL, sondern PENDING (§4).

---

## GL-001 · 2026-06-12 · H-02 · C-42-Reproduktion (LightGBM/HAR-RV, Pilot 2) — **DROP/PARK**

**Quelle:** `handoff_local/results/upload_20260611/overnight_20260611_154638/c42_{BTC,ETH,SOL,BNB,XRP}USDT/`
(je `c42_results.json` + `c42_report.md`; T3-Voll-WF, model=lightgbm, seed=42, n_folds=3).

**Runner-Statusvorbehalt:** `summary.txt`/`steps.tsv` zeigen für alle C42-Blöcke „FAIL (rc=)". Das ist der
bekannte PS-5.1-ExitCode-Capture-Bug (rc-Feld leer), NICHT der Schritt-Status: die Blöcke liefen 1163–1324 s
voll durch, schrieben vollständige `results.json` + `report.md`, und die `C42_WF_*.log`-Zeilen tragen das
inhaltliche Pipeline-Urteil (`C42-REPRO DROP/PARK ... r2_pass=False qlike<har=False`). Geurteilt wird nach
den INHALTEN. → kein Mess-Lücken-Vorbehalt für H-02; die Daten sind vollständig (5/5 Symbole).

### Registriertes Gate (H-02, wörtlich)
- **WEITER:** „OOS-R² ≥ 0.15 UND QLIKE schlägt naive HAR-RV-Baseline." Operationalisierung (WP-4-DoD,
  Ein-Fenster-Abbruch): **beide Kriterien in ALLEN ≥2 OOS-Fenstern** erfüllt.
- **Abbruch (PARK/DROP):** „OOS-R² < 0.15 in einem Fenster ODER HAR-RV nicht geschlagen → der gesamte
  Vol-Stack verliert seinen Anker, C-42 fällt auf PARK/DROP, alle abhängigen Vol-Module bleiben gesperrt."
- **Kein GRAUBEREICH** registriert (Registry H-02; konservativ kein Nachregistrieren).

### Aggregationsregel (begründet aus Registry-Text)
H-02 ist über das 5-Symbol-Universum (BTC/ETH/SOL/BNB/XRP) registriert; das harte Ein-Fenster-Abbruchkriterium
(§6) wirkt PRO disjunktem Fenster. Folglich: **Gate wird je Symbol über seine Folds geurteilt; das
Gesamturteil ist die strengste Lesart** — ein einziges Symbol×Fenster, das ein Kriterium verfehlt, kippt
C-42 in den Abbruch (Registry: „in einem Fenster"). Es gibt kein „2-von-5-Symbole-reicht"-Mehrheitsvotum;
der Vol-Stack-Anker muss als Befund robust stehen. Hier ist das Urteil ohnehin eindeutig: **0/5 Symbole bestehen.**

### Befund je Symbol × Fold

OOS-R² (Modell) je Fold; **fett** = R²≥0.15 verfehlt. QLIKE-Spalte: model<HAR? (ja=HAR geschlagen).

| Symbol | Fold | model R² | R²≥0.15 | model QLIKE | HAR QLIKE | QLIKE<HAR | beide erfüllt |
|---|---:|---:|:--:|---:|---:|:--:|:--:|
| **BTCUSDT** | 0 | 0.4699 | ja | 0.5566 | 0.7477 | ja | ja |
| | 1 | **-0.0808** | nein | 0.3876 | 0.4921 | ja | nein |
| | 2 | **-0.3212** | nein | 0.3321 | 0.3275 | **nein** | nein |
| **ETHUSDT** | 0 | 0.2494 | ja | 0.8989 | 0.6203 | **nein** | nein |
| | 1 | **0.1184** | nein | 0.4532 | 0.5862 | ja | nein |
| | 2 | **-0.1470** | nein | 0.3421 | 0.3546 | ja | nein |
| **SOLUSDT** | 0 | 0.3488 | ja | 0.6672 | 0.6272 | **nein** | nein |
| | 1 | **-0.0285** | nein | 0.3547 | 0.4039 | ja | nein |
| | 2 | **-0.0849** | nein | 0.2691 | 0.2709 | ja | nein |
| **BNBUSDT** | 0 | 0.3429 | ja | 0.6455 | 0.6032 | **nein** | nein |
| | 1 | **-0.5294** | nein | 0.4312 | 0.3887 | **nein** | nein |
| | 2 | 0.2172 | ja | 0.2674 | 0.2692 | ja | ja |
| **XRPUSDT** | 0 | 0.2509 | ja | 0.7949 | 0.5213 | **nein** | nein |
| | 1 | **-0.0346** | nein | 0.2938 | 0.3533 | ja | nein |
| | 2 | 0.2281 | ja | 0.2391 | 0.2661 | ja | ja |

### Kriterien einzeln (Schwelle vs. gemessen)

| Kriterium (registriert) | Schwelle | gemessen | erfüllt |
|---|---|---|---|
| OOS-R² ≥ 0.15 in ALLEN Fenstern | min Fold-R² ≥ 0.15 (je Symbol) | min: BTC −0.3212 · ETH −0.1470 · SOL −0.0849 · BNB −0.5294 · XRP −0.0346 → **alle < 0.15** | **nein (0/5)** |
| QLIKE schlägt HAR-RV in ALLEN Fenstern | model_qlike < har_qlike je Fold | jedes Symbol verfehlt in ≥1 Fold (4/5 schon in Fold 0; BTC in Fold 2) | **nein (0/5)** |
| purged Walk-Forward, ≥2 disjunkte OOS-Fenster | deterministisch-chronologischer Splitter | 3 Fenster, Purge=60 Bars + Embargo=1440 Bars, je Fenster n_test=12925 | **ja** |
| FDR BH α=0.10 über 36 Features (F-VOL) | BH step-up über Permutations-p | **0/36 signifikant** in allen 5 Symbolen | n/a (Reporting; bestätigt kein Feature trägt) |

### Testdesign-Konformität (gegen Registry geprüft)
- Purged Walk-Forward, ≥2 disjunkte OOS-Fenster: **erfüllt** (3 Fenster, Purge 60 + Embargo 1440 Bars).
- Deterministisch-chronologische, nicht-diskretionäre Fensterwahl: **erfüllt** (fixer Splitter, Seed 42).
- 36-Feature-FDR mit BH α=0.10 (F-VOL): **erfüllt** (eine Familie, step-up; 0/36 signifikant).
- Symbol-Universum vollständig: **5/5** (BTC/ETH/SOL/BNB/XRP). Read-only auf `kline_1min`, keine neue Aufzeichnung.

### URTEIL: **DROP/PARK** — C-42 reproduziert NICHT.
Beide Pflicht-Kriterien scheitern in allen 5 Symbolen. Das einzige positive Muster ist Fold 0 (frühestes,
kürzestes Trainingsfenster), das in keinem Symbol R² UND QLIKE gemeinsam besteht außer BTC — und auch BTC
bricht in Fold 1+2 ein. Der dokumentierte Test-R²≈0.249-Befund (research_notes, L1-Selbstauskunft) **überlebt
purged Walk-Forward + FDR nicht**; er war ein L1-Artefakt (Peso/L0-Verschärfung §8.4 bestätigt). Die FDR
liefert 0/36 signifikante Features in jedem Symbol — der Vol-Anker trägt auf keiner Ebene.

### Reproduktions-Treue-Vorbehalt (Pflicht-Bestandteil des Urteils)
Das Feature-Set ist **1 DOCUMENTED / 35 ASSUMED** (`feature_provenance` in jedem `results.json`; nur `atr_60`
ist aus research_notes #1 belegt, die übrigen 35 sind plausibel rekonstruiert, nicht aus der Originalquelle
verifiziert). Damit ist dies kein bit-genaues Replikat des Kestrel-v1.4-Notebooks, sondern eine
**Best-Effort-Reproduktion unter rekonstruiertem Feature-Vektor**. Das Urteil DROP/PARK bezieht sich auf
DIESE Reproduktion. Falls eine bit-genaue Original-Feature-Spezifikation nachgeliefert wird, wäre das eine
**neue Hypothese (neuer Registry-Eintrag, neuer Lauf)** — Torpfosten-Verschiebung am bestehenden H-02 ist
verboten (§2). Die Stärke des Negativbefunds (alle 5 Symbole, beide Kriterien, FDR 0/36) macht es jedoch
unwahrscheinlich, dass die Feature-Provenance allein das Ergebnis umkehrt.

### Konsequenzen (kaskadiert, PRD §3-Sequenzierung)
- **C-42 → PARK/DROP.** Der gesamte Vol-Stack verliert seinen Anker und **bleibt gesperrt**:
  **C-10, C-35, C-11, C-12, C-34** und das **VRP-RV-Bein** dürfen NICHT starten (alle ΔR²-Gates messen sonst
  gegen ein Phantom, verdict §7 / PRD §3 Pilot 2 Abbruchkriterium).
- F-VOL-Familie bleibt offen, aber ohne Baseline-Anker: keine Folge-ΔR²-Tests gegen C-42 registrierbar,
  solange C-42 nicht (als neue Hypothese) reproduziert ist.
- Empfehlung an Orchestrator: **PARK statt hartes DROP** — Re-Run mit verifizierter Original-Feature-Spez
  (neuer Registry-Eintrag H-02b) ist der einzige Pfad, den Anker zu retten; sonst Vol-Stack endgültig zu.

---

## GL-002 · 2026-06-12 · H-01 · E-15 / CS-03 (S3 Pre-Settlement, iter-5) — **PENDING (nicht geurteilt)**

**Status:** Gate NICHT geurteilt — der konfirmatorische Lauf hat **keine Ergebnisse produziert** (Mess-Lücke, §4).

**Blocker (konkret):** `E15_EVAL` bricht in beiden T2-Läufen mit echtem rc=1 ab:
`E15-EVAL DATENDEFEKT: trades file not found: ...\edge_research_framework\results\trades_all.csv`.
Der iter-5-Replay-Export liegt NICHT am Default-Pfad `trades_all.csv`; laut Overnight-`REPLAY_ITER5`-INFO-Zeile
existieren iter-5-Ergebnisse, vermutlich unter `trades_iter5/`. Es ist ein **Pfad-/Export-Defekt im Runner**,
kein inhaltliches Gate-Ergebnis. Keine `e15_evaluation.json` im Lauf.

**Registriertes Gate (unverändert, zur Erinnerung):** WEITER bei aggregierter Netto-Edge ≥ −5 bps UND
E-17-Divergenz geklärt; DROP bei ≤ −10 bps; GRAUBEREICH dazwischen → genau ein weiteres vorregistriertes Fenster.

**Konsequenz:** Kein Urteil, keine Vorwegnahme. Reparatur-WP (Pfad-Fix `trades_all.csv` ↔ `trades_iter5/`,
dann E15_EVAL erneut) → siehe morning_report. S3 bleibt unter E-15-Vorbehalt aktiv (PRD §6 unverändert).

---

## GL-003 · 2026-06-12 · H-03 · C-31-CFAR (Cyclostationary CFAR, Pilot 4) — **PENDING (nicht geurteilt)**

**Status:** Gate NICHT geurteilt — der konfirmatorische Surrogate-Lauf **crashte vor jedem Ergebnis**
(Mess-Lücke, §4). Keine `c31_cfar_results.json` für irgendein Symbol.

**Blocker (konkret, aus `C31_CFAR_*.err.log`, identisch für alle 5 Symbole):**
`numpy ArrayMemoryError: Unable to allocate 1.30 TiB for an array with shape (178056061487,)` in
`cyclic_spectrum.py:115 bin_counts` (`edges = lo + bin_dt_ms * np.arange(n_bins+1)`), aufgerufen aus
`surrogate.py:71 _pipeline_top_snr` → `surrogate_test`. Ursache ist ein Bin-/Zeitfenster-Parameterfehler
(`n_bins` explodiert, vermutlich `bin_dt_ms` zu klein gegen die Tick-Zeitspanne t0..t1) — Implementierungs-Bug,
**kein** inhaltliches Gate-Ergebnis. Code lief auf `E:\...\scripts\c31_cfar.py`.

**Registriertes Gate (unverändert, zur Erinnerung):** WEITER bei Surrogate p ≤ 0.05 in ≥2 Fenstern UND
Lead > 50 ms UND Edge > 11 bps; hartes Ein-Fenster-Abbruch → DROP; kein GRAUBEREICH.

**Konsequenz:** Kein Urteil, KEINE inhaltliche Vorwegnahme (Traceback wird parallel diagnostiziert).
Reparatur-WP (bin_counts-Guard/Parameter-Sanity, dann Surrogate-Lauf auf Echt-Ticks) → siehe morning_report.

---

## GL-004 · 2026-06-12 · C-36 Recording-Pilot (PRD §3 Pilot 3) — **PILOT-STATUS (kein Alpha-Gate)**

**Hinweis:** C-36 ist **kein registriertes Alpha-Gate** (kein Eintrag in der Hypothesen-Registry; Infrastruktur).
Das vorregistrierte F0-Recall-≥95%-Gate (PRD §3) ist ein 2–4-Wochen-Ziel und hier NICHT fällig. Dokumentiert
wird nur der **Pilot-Betriebsstatus** aus Smoke (5 min) + Dauertest (8 h).

**Befund (recording_check.json, RECORDER_LONG.err.log — 8h-Lauf, beide T2-Smokes konsistent):**

| Stream | Pflicht | Segmente | Rows | schema_version | Status |
|---|---|---:|---:|---|---|
| premium_index_kline | ja | 483 | 96600 | 1 | **OK** (REST-Pfad funktioniert) |
| adl_alerts | nein | 0 | 0 | - | EMPTY_OK (event-getrieben, plausibel) |
| rpi_orderbook | ja | 0 | 0 | - | **NO_DATA** |
| insurance_pool | ja | 0 | 0 | - | **NO_DATA** |
| option_tickers | ja | 0 | 0 | - | **NO_DATA** |

- Storage-Deckel: 0.004 GB / 50 GB → OK. Recorder lief stabil 28800 s durch, sauberer Stop.
- **Linear-WS** (`wss://.../v5/public/linear`): subscribe auf `['orderbook.rpi.BTCUSDT','insurance.USDT','adlAlert']`
  wird **bestätigt** (kein Subscribe-Reject geloggt), liefert aber über 8 h **null** rpi/insurance-Nachrichten.
- **Option-WS** (`wss://.../v5/public/option`): subscribe `['tickers.BTC','tickers.ETH']` bestätigt, aber die
  Verbindung **bricht alle ~30 s** mit `1011 (internal error) keepalive ping timeout` und reconnectet endlos →
  liefert nie Daten. Eigenständiger Verbindungs-/Keepalive-Defekt, getrennt vom NO_DATA der linearen Topics.

**Offene Frage (INC-06-Lektion: PRD-referenzierte Endpoints können falsch sein):**
Subscribe wird akzeptiert, aber kein Datenfluss → **Subscribe-Fehler vs. nicht-existentes/falsch benanntes Topic**
ist noch nicht entschieden. rpi/insurance/option könnten falsche Topic-Namen sein (`orderbook.rpi.*`,
`insurance.USDT`, `adlAlert`, `tickers.{BTC,ETH}` gegen die echte Bybit-v5-Spec prüfen), ODER event-arme Topics
(insurance/adl feuern selten), ODER — beim Option-Stream — ein reiner Keepalive-Bug, der jede Lieferung verhindert.

**Konsequenz:** Kein Gate-Urteil (kein Alpha-Gate). **Reparatur-/Diagnose-WP** (Topic-Namen gegen Bybit-v5-Doc
verifizieren; Option-WS-Keepalive/ping fixen; 1 kurzer Live-Probe-Subscribe je Topic) → siehe morning_report.
Zeitkritisch: C-36 ist Vorbedingung aller recording-abhängigen Welle-2-Pilots; premium_index_kline läuft bereits.

---

## GL-004 · 2026-06-13 · H-01 · E-15 / CS-03 (S3 Pre-Settlement, iter-5) — **DROP**

**Status:** Geurteilt. Löst GL-002 (PENDING) ab — der konfirmatorische iter-5-Lauf liegt jetzt vor
(`replay_all_results.json` generated 2026-06-13T01:11:24Z; `trades_iter5/trades_all.csv`; E15_EVAL rc=0).
Datenquelle korrekt: trades_path = `…/trades_iter5/trades_all.csv` (Pfad-Kaskade aus DIAG hat gegriffen).

**Gate-Urteil gegen die vorregistrierten H-01-Tore (Registry §H-01):**

| Kriterium (Registry wörtlich) | Schwelle | Messwert iter-5 | iter-4 | Bestanden |
|---|---|---|---|---|
| WEITER · Netto-Edge ≥ −5 bps | ≥ −5.0 | **−15.47** | −16.81 | nein |
| WEITER · E-17 geklärt | true | ja (Ratio 1.50 Trades / 0.83 per-Trade) | — | ja |
| DROP · Netto-Edge ≤ −10 bps | ≤ −10.0 | **−15.47** | −16.81 | **ja → DROP** |

**Urteil: DROP.** Aggregierte S3-Netto-Edge −15.47 bps liegt klar unterhalb der −10-bps-DROP-Schwelle.
Kein GRAUBEREICH (der greift nur zwischen −10 und −5). Endgültig, keine Wiederholung nötig.

**Mechanik des iter-5-Fixes — funktionierte wie entworfen, rettete die Edge aber NICHT:**

| Metrik | iter-4 (Bug) | iter-5 (Fix) | Bewertung |
|---|---|---|---|
| time_stop_exceeded | 1 | **128** | Tick-Zeit-Fix wirkt |
| max Haltedauer (s) | 2124.9 | **178.4** | Monster-Tails eliminiert |
| worst trade (bps) | −56.60 | **−38.10** | gekappt |
| n<−30bps | 33 | **25** | friction-aware Hard-Stop hilft |
| Trades gesamt | 213 | **320** | +50% (frühe Exits → mehr Re-Entries) |
| mean Netto-Edge (bps) | −16.81 | **−15.47** | praktisch unverändert |
| mean RAW-Edge (bps) | −5.81 | **−4.48** | bleibt negativ |

**Mechanistische Schlussfolgerung (forensisch, nicht spekulativ):** Die iter-4-Hypothese „S3 ist
friction-bound + tail-driven; bounded-loss-Exits legen die Edge frei" ist damit **widerlegt**. Die Tails
wurden sauber gekappt (max Hold 178 s statt 2125 s, worst −38 statt −57 bps), aber die Aggregat-Edge bewegte
sich nur um +1.34 bps (netto). Grund: Die Tail-Reduktion (~1.3 bps Gewinn) wird durch die zusätzliche Friktion
aus 107 Mehr-Trades fast exakt aufgehoben. Entscheidend ist die **RAW-Edge von −4.48 bps**: Selbst bei NULL
Gebühren verliert S3 — der Pre-Settlement-Pressure-Release-Entry trifft die Richtung nicht. Das Problem war nie
der Exit, sondern das Entry-Signal. Konsistent über alle 5 Symbole (RAW-Edge −3.07 bis −5.65 bps, kein Symbol
positiv).

**FDR-Familie F-S3:** Einzelner konfirmatorischer Test, keine Korrektur nötig (Registry).

**Konsequenz:** S3 fällt auf DROP. Damit sind ALLE Strategien des ursprünglichen Scinance-1.0-Portfolios
empirisch erledigt: S1 (GL/iter-4: ρ-Estimator gebrochen), S2 (3 Forensiken refuted), **S3 (jetzt: bounded-loss
definitiv getestet, Entry hat keine Edge)**, S4/S5 (nie gelaufen, loader-/harness-bound). Der letzte Eintrag aus
dem Original-PRD ist gefallen. PRD §6: S3 wird in der Live-Config deaktiviert (kein Kapital), Code bleibt als
Archiv. Folge-Arbeit ausschließlich an Scinance-2.0-Piloten (Recording-Fundament + neue Hypothesen), nicht an S3.

---

## GL-005 · 2026-06-15 · H-03 · C-31 CFAR (Cyclostationary Footprint, Pilot 4) — **DROP**

**Status:** Geurteilt. Löst GL-003 (PENDING) ab.
Datenquelle: `handoff_local/results/cfar_20260615_120813/` (Standalone-Runner; --db-copy, --max-ticks-per-window 150000, --windows 2, --surrogates 200, seed 42, F-CFAR-Familie 3 Varianten).

**Lauf-Status je Symbol:**

| Symbol | Status | Dauer | n_ticks gesamt (genutzt) | gemessene Fenster |
|---|---|---|---|---|
| BTCUSDT | OK | 712 s | (300 000 jüngste Ticks) | 2/2 final |
| ETHUSDT | OK | 661 s | (300 000 jüngste Ticks) | 2/2 final |
| SOLUSDT | TIMEOUT | 1800 s | 300 000 genutzt | 1/2 final, Fenster 0 ALLE Varianten gemessen (Teil-Logs) |
| BNBUSDT | TIMEOUT | 1800 s | 300 000 genutzt | partial |
| XRPUSDT | TIMEOUT | 1800 s | — | partial |

**Gate-Urteil gegen die vorregistrierten H-03-Tore (BTCUSDT — repräsentativ; ETHUSDT analog):**

| Kriterium (Registry wörtlich) | Schwelle | BTC F0 | BTC F1 | ETH F0 | ETH F1 | Status |
|---|---|---|---|---|---|---|
| Surrogate p (FDR-korrigiert, F-CFAR) | ≤ 0.05 | **0.871** | **1.000** | **0.965** | **0.801** | ALLE 4 verfehlt |
| Lead > 50 ms | > 50 | 100.0 | 100.0 | 100.0 | 100.0 | ja |
| Edge > 11 bps | > 11 | **0.04** | **0.01** | **0.04** | **0.01** | ALLE 4 verfehlt (3 Größenordnungen darunter) |

**Anwendung des Ein-Fenster-DROP-Kriteriums (PRD §8.5, Registry §6):**
„Schwelle in EINEM disjunkten Fenster verfehlt → DROP, kein Nachverhandeln. **Kein GRAUBEREICH.**"

BTC Fenster 0 verfehlt p-Kriterium (0.871 ≫ 0.05) UND Edge-Kriterium (0.04 ≪ 11). Damit ist H-03 bereits hier definitiv DROP. Die übrigen drei gemessenen Fenster (BTC F1, ETH F0, ETH F1) bestätigen das Muster auf BTC und ETH unabhängig. **Urteil: DROP.**

**Zu den 3 Timeouts (SOL/BNB/XRP):** Methodisch nicht entscheidungsrelevant, weil das Gate auf je-Symbol-Ebene operiert und BTC/ETH bereits DROP-konstitutiv sind. Plus: Die Progress-Logs in `C31_CFAR_SOLUSDT.err.log` zeigen für SOL Fenster 0 ALLE drei Varianten gemessen — alle p=1.0000 (z.B. dt100ms_T6: observed_snr=13.200 p=1.0000). Hätten SOL/BNB/XRP perfekte Treffer geliefert (taten sie nicht), würden sie das je-Symbol-DROP für BTC und ETH nicht aufheben. Die Timeouts sind Performance-Hinweis für Welle 2 (Bin-Grid 10ms ist auf 150k Ticks rechenintensiv), nicht inhaltlich offen.

**FDR-Familie F-CFAR:** BH α=0.10 über drei Varianten (dt10/50/100ms × Schwellenfaktor 6), p_crit = 0.000 — kein Test überlebt die Korrektur, konsistent mit der unkorrigierten p≈1 auf jedem Fenster.

**Mechanistische Schlussfolgerung:** Die Hypothese „zyklostationäres Spektrum der Inter-Arrival-Zeiten enthält CFAR-detektierbare, prädiktive periodische Struktur mit handelbarer Edge oberhalb der Friction-Wand" ist auf den 4 unabhängig gemessenen Fenstern (BTC × 2 + ETH × 2) **deutlich widerlegt**: Die p-Werte sind statistisch nicht von der geshuffelten Inter-Arrival-Null zu unterscheiden (≈ 1.0), und die geschätzte Edge ist ~250× UNTER der 11-bps-Friction-Wand. Selbst wenn die Spektral-Detektion irgendwann ein signifikantes p liefern würde, wäre die handelbare Edge inhaltlich tot. Konsistent mit der Skeptic-Argumentation im iter-3-Verdict: HFT-abgegraste Anomalie, adaptiver Gegner, keine Retail-überlebende Edge.

**Konsequenz:** H-03 fällt auf DROP. **Damit sind alle vier Welle-1-Piloten entschieden:** H-01 DROP (S3), H-02 DROP (Vol-Stack-Anker), H-03 DROP (CFAR), C-36 Recording-Fundament steht (~5 Mio RPI-Zeilen, kein Alpha-Gate).

---

## GL-006 · 2026-06-17 · H-04 · C-17/C-41 Cross-Sectional Lead-Lag (Welle-2-Pilot 1, KAPITALFREI) — **WEITER (Mess-Existenz; Kapital-Status bleibt PARK)**

**Quelle:** `handoff_local/results/wave2_20260617_090618/h04/c17_c41_results.{json,md}` + `WAVE2_SUMMARY.md` (F-WAVE2 zweistufig) + `wave2_summary.json`.
Lauf: BTCUSDT/ETHUSDT-Paar aus `trades`, 2 disjunkte Fenster (F0: 3874 Bars, 1780611314526..1780615189170 ms; F1: 3875 Bars, 1780615190990..1780619066816 ms), Grid 1000 ms, Lags [1,2,3,5,10] Bars, Achsen TE (C-17) + WCOH (C-41), n_surrogates 200, seed 42, BH-FDR α=0.10 über F-LEADLAG. Runner 5/5 OK (rc=0).

### Registriertes Gate (H-04, wörtlich) — vier Kriterien
1. Konditionale gerichtete Info signifikant > Surrogate-Null, p ≤ 0.05 NACH BH-FDR α=0.10 über F-LEADLAG.
2. Existenz in ≥ 2 disjunkten Fenstern.
3. Lead-Symbol-Stabilität: Vorzeichen/Lead-Symbol über beide Fenster konsistent.
4. Hartes Ein-Fenster-DROP: Surrogate-Signifikanz in EINEM Fenster verfehlt ODER Lead-Symbol kippt. Kein GRAUBEREICH.

### Je-Kriterium-Tabelle (Messwert vs. Schwelle vs. bestanden)

| Kriterium (Registry wörtlich) | Schwelle | Messwert | Bestanden |
|---|---|---|---|
| Surrogate-p FDR-sig (F-LEADLAG) Fenster 0 | ≤ 0.05 nach BH-FDR | beste Variante WCOH p=0.0050 (FDR-sig); 8 Varianten FDR-sig, p_crit=0.0697 | **ja** |
| Surrogate-p FDR-sig (F-LEADLAG) Fenster 1 | ≤ 0.05 nach BH-FDR | beste Variante WCOH p=0.0050 (FDR-sig); 4 Varianten FDR-sig, p_crit=0.0199 | **ja** |
| Existenz in ≥ 2 disjunkten Fenstern | ≥ 2 | 2/2 Fenster mit ≥1 FDR-sig Variante | **ja** |
| Lead-Symbol-Stabilität über beide Fenster | konsistent | Lead je Fenster = [BTCUSDT, BTCUSDT] (stabil) | **ja** |
| Ein-Fenster-DROP ausgelöst? | nein-Fall = Pass | kein Fenster ohne Surrogate-Signifikanz; Lead kippt nicht | **nicht ausgelöst** |

### Zentrale Bewertungsfrage: Verletzt bidirektionale Signifikanz in Fenster 0 die Lead-Symbol-Stabilität?

In Fenster 0 sind BEIDE TE-Richtungen FDR-signifikant (BTC→ETH: lag1/2/3/5; ETH→BTC: lag3 mit p=0.0199 FDR-sig, lag1/lag2 nur unkorrigiert grenzwertig p=0.0647/0.0697 = NICHT FDR-sig bei p_crit 0.0697 für lag2 genau auf der Grenze). In Fenster 1 ist die Rückrichtung ETH→BTC NICHT FDR-sig (lag1 ETH→BTC p=0.0050 ist hier zwar sig, aber WCOH+BTC→ETH dominieren). Es gibt also bidirektionale Kopplung mindestens in F0.

**Beide Lesarten dokumentiert:**
- **Lesart A (strenge „bidirektional = Kippen"):** Wenn „Lead-Symbol kippt" so verstanden wird, dass NUR eine gerichtete Achse signifikant sein darf, dann ist bidirektionale Signifikanz in F0 ein Verstoß → DROP.
- **Lesart B (Registry-Wortlaut „Lead-Symbol bleibt über beide Fenster konsistent"):** Das Kriterium fragt nach der KONSISTENZ des dominanten Lead-Symbols über die Fenster, nicht nach Ausschließlichkeit einer Richtung pro Fenster.

**Entscheidung (streng aus dem Registry-Wortlaut, nicht aus Wunschdenken): Lesart B.** Begründung exakt am Text:
- Der Registry-Text definiert das Kriterium als „Lag-Stabilität (das **Vorzeichen/Lead-Symbol bleibt über beide Fenster konsistent**)" und das Abbruchkriterium als „Lead-Symbol **kippt**". „Kippt" = das dominante Lead-Symbol wechselt zwischen den Fenstern (BTC→ETH in F0, ETH→BTC in F1). Das ist hier NICHT der Fall.
- Die Stabilität ist in beiden Fenstern eindeutig durch BTCUSDT getragen: (a) Auf der WCOH-Achse (C-41) ist Lead=BTCUSDT in BEIDEN Fenstern (F0 +0.9028 p=0.0050; F1 +0.9076 p=0.0050). (b) Auf der TE-Achse (C-17) ist BTC→ETH bei JEDEM gematchten Lag STÄRKER als ETH→BTC — F0 lag1 +0.0054>+0.0040, lag2 +0.0074>+0.0046, lag3 +0.0059=+0.0046, lag5 +0.0048>+0.0029; F1 lag1 +0.0087>+0.0055, lag2 +0.0049>+0.0028. Die dominante (höchste obs-Stat) gerichtete Achse ist in beiden Fenstern BTC→ETH.
- Bidirektionale Kopplung bei zwei eng korrelierten Perp-Märkten im Sekunden-Takt ist physikalisch erwartbar (gemeinsamer Order-Flow, ETH reagiert nicht latenzfrei auf BTC); das Registry verlangt NICHT, dass die Rückrichtung null ist, sondern dass das Lead-Symbol nicht kippt. Die registrierte Hypothese lautet „BTC führt, Alt folgt" — genau das ist messbar erfüllt (BTC dominiert in beiden Fenstern auf beiden Achsen).
- Lesart A würde de facto einen Schwellwert nachregistrieren („Rückrichtung muss insignifikant sein"), der im Registry NICHT steht — das wäre Torpfosten-Verschiebung (§2). Daher abgelehnt.

→ Kriterium 3 (Lead-Symbol-Stabilität) ist **erfüllt**. Kriterium 4 ist **nicht ausgelöst** (kein Fenster ohne Surrogate-Signifikanz; kein Kippen). Alle vier Kriterien bestanden.

### Anwendung der zweistufigen F-WAVE2-FDR
Stage 1 (F-LEADLAG-intern, BH α=0.10): 12 von 22 Varianten überleben. Stage 2 (Über-Familie, gemeinsam mit F-OFI/F-ENTROPY-Survivorn, p_crit=0.0697): **12/12 überleben auch Stage 2 — 0 verloren.** Insbesondere die beiden WCOH-Survivors (p=0.0050) und die BTC→ETH-TE-Survivors bleiben in Stage 2 signifikant. Stage 2 ändert das Urteil NICHT.

### Mechanistische Schlussfolgerung
Auf dem BTC/ETH-Perp-Paar existiert über beide disjunkten Fenster ein robust messbarer, surrogat-signifikanter gerichteter Informationsfluss mit BTCUSDT als stabilem Lead-Symbol, sowohl auf der Transfer-Entropy-Achse (C-17) als auch auf der Wavelet-Coherence-Phasen-Achse (C-41). Die signifikanten gerichteten Lags liegen bei 1–3 s (TE lag1–lag3 sind die FDR-Survivor; ab lag5/lag10 zerfällt die Signifikanz in beiden Fenstern). Die Existenz von gerichteter Information ist damit messbar bestätigt — H-04 als reines Mess-Gate ist WEITER.

### KAPITALFREIHEIT (verbindliche Pflichtnotiz — Registry H-04, PRD §4 Z.133)
**WEITER heißt AUSSCHLIESSLICH: gerichtete Information existiert messbar. NICHT handelbar.** Die signifikanten Lags sind 1–3 s — tiefes HFT-Territorium. PRD §4 wörtlich: „keine handelbare Kante (abgegraste 30–60s-HFT-Anomalie) → bleibt PARK." Es wird KEINE Edge-/bps-/Sharpe-/Tradability-Aussage nachregistriert; das Gate trägt keine. Konsequenz: **Kapital-Status bleibt PARK** (kein Kapitaleinsatz, kein Friction-Wand-Vergleich). Tradability wäre eine **NEUE H-04b** (eigener Registry-Eintrag, eigener Lauf, L2-Tiefen-Stream) und ist WP-0-Arbeit — hier NICHT registriert. Das Mess-WEITER entsperrt keinerlei Kapitalmodul.

### URTEIL: **WEITER (Mess-Existenz bestätigt)** — Kapital-Status PARK, Tradability = offene NEUE H-04b.
Erster nicht-trivialer Nicht-DROP des Frameworks: ein Gate, das tatsächlich bestanden wird — aber bewusst als kapitalfreies Mess-Gate konstruiert, sodass „bestanden" keine handelbare Behauptung impliziert.

---

## GL-007 · 2026-06-17 · H-05 · C-01 OFI-Vorzeichen-Test (INC-02-Anker, Welle-2-Pilot 2, KAPITALFREI) — **DROP für C-01 + C-09-OFI-Bein + C-14-OFI-Erbe**

**Quelle:** `handoff_local/results/wave2_20260617_090618/h05/c01_ofi_sign_results.{json,md}` + `WAVE2_SUMMARY.md`.
Lauf: 5 Symbole (BTC/ETH/SOL/BNB/XRP) aus `trades`, 2 disjunkte Fenster, δ ∈ {1,5,15,60,300} s, n_surrogates 200, seed 42, BH-FDR α=0.10 über F-OFI (50 Varianten), Tick-Cap 150000/Fenster, eigener OFI-Schätzer (m2_ofi.py unberührt, DEC-11). Runner OK (rc=0).

### Registriertes Gate (H-05, wörtlich)
- **WEITER:** sign(corr)=+ (Aggression-Folge) UND p ≤ 0.05 nach BH-FDR (F-OFI) UND Konsistenz in ≥ 2 disjunkten Fenstern UND Magnitude (|corr| ≥ 0.05 ODER Hit-Rate ≥ 0.53).
- **DROP (INC-02-bestätigend):** sign ≤ 0 in ≥ 1 Fenster ODER Magnitude verfehlt ODER FDR-p > 0.05 → DROP für C-01 + C-09-OFI-Bein + C-14-OFI-Erbe.
- **Inverse These = NEUE H-05b** (kein H-05-Bestehen, kein Torpfosten-Verschieben). Hartes Ein-Fenster-Kriterium, kein GRAUBEREICH.

### Je-Kriterium-Tabelle — gesucht: irgendein Symbol/δ mit FDR-sig POSITIVEM Vorzeichen in BEIDEN Fenstern?

| Kriterium (Registry wörtlich) | Schwelle | Messwert | Bestanden |
|---|---|---|---|
| FDR-sig POSITIVE Vorzeichen-Varianten (F-OFI, p_crit=0.0050) | p ≤ 0.05 nach BH-FDR UND sign=+ | nur **BNBUSDT w0 d1s** (corr +0.0441, p=0.0050) und **BNBUSDT w0 d5s** (corr +0.0204, p=0.0050) | nur Fenster 0 |
| dieselbe Variante FDR-sig + positiv AUCH in Fenster 1 | ≥ 2 disjunkte Fenster | BNB w1 d1s p=0.0597 (NICHT FDR-sig); BNB w1 d5s sign− p=0.1393; BNB w1 d15s sign− | **nein** |
| ≥ 2-Fenster-Konsistenz (positiv) für IRGENDEIN Symbol/δ | beide Fenster | **kein** Symbol×δ ist in beiden Fenstern FDR-sig + positiv | **nein** |
| Magnitude |corr| ≥ 0.05 ODER Hit-Rate ≥ 0.53 | einer reicht | BNB w0 d1s erfüllt (HR 0.601); aber Fenster-Konsistenz fehlt | n/a |
| Hartes Ein-Fenster: sign ≤ 0 in ≥ 1 Fenster | kein neg./null-Vorzeichen | BTC F0 alle δ negativ; ETH beide Fenster fast durchgängig negativ; SOL/XRP gemischt negativ | **verletzt → DROP** |

**Befund zur Kernfrage:** Es gibt **KEIN einziges** Symbol/δ mit FDR-signifikant positivem Vorzeichen in BEIDEN Fenstern. Der einzige positive FDR-Survivor (BNBUSDT, w0 d1s/d5s) bricht in Fenster 1 zusammen (d1s nicht FDR-sig, d5s/d15s kippen sogar ins Negative). Das harte Ein-Fenster-Kriterium ist mehrfach verletzt (BTC, ETH negativ).

### ETH-Befund: signifikant INVERSES Vorzeichen → H-05b-Trigger
**ETHUSDT w0 d1s: corr = −0.0550, p = 0.0050 (FDR-sig in F-OFI, inverse_significant=true), Hit-Rate 0.490.** Das ist die MM-Replenishment-Lesart: OFI markiert nicht die aggressive Folge-Seite, sondern die nachfüllende Market-Maker-Seite (Vorzeichen invertiert). |corr| 0.055 ≥ Magnitude-Floor und p FDR-sig — also ein echtes, signifikantes inverses Signal, kein Rauschen.

**Bestätigt das die iter-3/S2-2023-Forensik (E-04, OFI-Vorzeichen invertiert)?** Ja, konsistent. Der INC-02-Anker (E-04 hit_sum 0.179 = fälschlich invertiertes Vorzeichen der S2-Implementierung) wird durch dieses unabhängige read-only-Mess-Gate REPRODUZIERT: auf ETH ist das OFI-Vorzeichen signifikant negativ (inverse/MM-Replenishment-Richtung), nicht positiv (Aggression-Folge). Die ETH-Spalte ist über BEIDE Fenster durchgängig negativ (w0 alle δ negativ, w1 alle δ negativ), was die Robustheit der Inversion unterstreicht — auch wenn nur w0 d1s FDR-sig ist.

### Anwendung der zweistufigen F-WAVE2-FDR
Stage 1 (F-OFI, p_crit=0.0050): 3 Survivor (BNB w0 d1s, BNB w0 d5s, ETH w0 d1s-invers). Stage 2 (Über-Familie): **3/3 überleben — 0 verloren.** Stage 2 ändert NICHTS: Die 3 Survivor erfüllen das H-05-Pass-Kriterium ohnehin nicht (BNB scheitert an ≥2-Fenster-Konsistenz; ETH ist invers = H-05b, kein Pass). Die zweistufige FDR ist damit für das H-05-Urteil nicht entscheidungstragend — das Urteil folgt aus Vorzeichen-Konsistenz + Ein-Fenster-Kriterium, die strenger greifen als die reine FDR-Survivorschaft.

### Mechanistische Schlussfolgerung
Die PRD-v1/CS-02-Behauptung „sign(OFI)=+ (Aggression-Folge)" ist auf dem Bestands-`trades`-Stream **widerlegt**: kein Symbol zeigt FDR-sig positive Vorzeichen-Konsistenz über ≥ 2 Fenster; die einzige robuste, FDR-signifikante Struktur ist ein INVERSES Vorzeichen auf ETH (MM-Replenishment) — exakt die E-04/INC-02-Lesart. Das ist KEIN H-05-Bestehen, sondern Falsifikation der ursprünglichen Richtung + Bestätigung des Falsifikators.

### URTEIL: **DROP** für C-01 + C-09-OFI-Bein + C-14-OFI-Erbe (PRD §4 Z.131 wörtlich, kaskaden-wirksam).
Hartes Ein-Fenster-Kriterium verletzt (negatives Vorzeichen in ≥ 1 Fenster auf mehreren Symbolen) UND keine ≥2-Fenster-positive-Konsistenz UND der einzige robuste FDR-Effekt ist invers.

### Empfehlung (KEINE Selbst-Registrierung — WP-0-Arbeit)
Der inverse ETH-Befund (corr −0.0550, p=0.0050, FDR-sig) ist der Auslöser für eine **NEUE H-05b-Pre-Registration** (MM-Replenishment-Lesart von INC-02). Registry-Disziplin §2: kein Verschieben der Torpfosten — H-05b ist ein eigener Eintrag mit eigenem vorregistrierten Gate (inverse Richtung als Haupt-These, ≥2-Fenster-Konsistenz, FDR, kapitalfrei). **Ich registriere H-05b NICHT selbst** (das ist WP-0/Orchestrator-Arbeit); ich empfehle es als Folge-WP. Hinweis: Auch ein H-05b müsste die ≥2-Fenster-Konsistenz erst zeigen (ETH-Inversion ist bislang nur in w0 d1s FDR-sig, wenngleich das Vorzeichen über beide Fenster konsistent negativ ist).

---

## GL-008 · 2026-06-17 · H-06 · C-07 Permutation Entropy (Welle-2-Pilot 3, KAPITALFREI) — **DROP (PRE-Gate in ALLEN Fenstern verfehlt)**

**Quelle:** `handoff_local/results/wave2_20260617_090618/h06/c07_pe_results.{json,md}` + `WAVE2_SUMMARY.md`.
Lauf: 5 Symbole aus `kline_1min` (NICHT trades), 2 disjunkte Fenster, m=4/τ=1 vorab fixiert (DEC-12, read-only Konstanten), Rolling-PE 240 Bars, δ ∈ {1,5,15,60} min, Vol-Cluster=RV über 15-min-Forward, n_surrogates 200, seed 42, BH-FDR α=0.10 über F-ENTROPY (40 Varianten), Bar-Cap 43200/Fenster (= 30 Tage, Stationaritäts-Cap). Runner OK (rc=0).

### Registriertes Gate (H-06, wörtlich)
- **PRE-Gate (Vorbedingung):** ρ ≥ 0.30 zwischen PE-Drop und 15-min-Vol-Cluster in ≥ 2 disjunkten Fenstern. **ρ < 0.30 in EINEM Fenster → DROP, kein Voll-Lauf** (hartes Ein-Fenster-Kriterium, PRD §8.5).
- **Haupt-Gate:** PRE-Gate bestanden UND Surrogate-p ≤ 0.05 nach BH-FDR (F-ENTROPY) in ≥ 2 Fenstern UND bedingter AUC-Lift ≥ +0.03 in G1-Fenstern. Kein GRAUBEREICH.

### Je-Kriterium-Tabelle

| Kriterium (Registry wörtlich) | Schwelle | Messwert | Bestanden |
|---|---|---|---|
| PRE-Gate ρ ≥ 0.30 in ≥ 2 Fenstern | ρ ≥ 0.30 | alle 10 Symbol×Fenster: ρ ∈ [−0.0059, +0.0145], **max +0.0145** (BNB w1); alle ≈ 0 | **nein — in ALLEN Fenstern verfehlt** |
| PRE-Gate ρ < 0.30 in EINEM Fenster → DROP | DROP-Auslöser | in JEDEM der 10 Fenster ρ ≪ 0.30 | **DROP ausgelöst** |
| Haupt-Gate Surrogate-p FDR-sig (F-ENTROPY) in ≥ 2 Fenstern | ≤ 0.05 BH-FDR | nur 2 Survivor, beide XRP w1 (d15min, d60min), p=0.0050 — nur EIN Fenster (w1), nicht ≥ 2 | nein |
| Haupt-Gate AUC-Lift ≥ +0.03 in G1 | ≥ +0.03 | beste Werte XRP w1 d15/d60: **+0.0072 / +0.0072**; alle 40 Varianten < +0.03 (viele negativ) | **nein — doppelt verfehlt** |

### Anwendung des Ein-Fenster-DROP-Kriteriums (PRD §8.5, Registry H-06)
Das PRE-Gate ist ein harter Reproduktions-Filter VOR dem Haupt-Gate. ρ ≥ 0.30 ist in **keinem einzigen** der 10 Symbol×Fenster-Paare erreicht (Maximum +0.0145, ~20× unter der Schwelle; mehrere ρ sind sogar negativ). Damit ist „ρ < 0.30 in EINEM Fenster" massiv erfüllt → **hartes DROP**, unabhängig von Stage 2 (das PRE-Gate ist explizit NICHT Teil von F-WAVE2 — es ist ein Korrelations-Floor, kein p-Wert-Test).

### Zweite, unabhängige Verfehlung (Haupt-Gate)
Selbst wenn man das PRE-Gate ignorierte: Die 2 Haupt-Gate-FDR-Survivor (XRP w1 d15min, w1 d60min) liefern AUC-Lift **+0.0072 / +0.0072 — beide < +0.03-Schwelle** (4× zu klein). Zudem liegen beide Survivor im SELBEN Fenster (w1), die ≥2-Fenster-Existenz für das Haupt-Gate ist also auch nicht erfüllt. H-06 ist damit **doppelt** verfehlt (PRE-Gate UND Haupt-Gate).

### Anwendung der zweistufigen F-WAVE2-FDR
Stage 1 (F-ENTROPY, p_crit=0.0050): 2 Survivor (XRP w1 d15/d60). Stage 2: **2/2 überleben — 0 verloren.** Stage 2 ändert NICHTS: Die FDR-Survivorschaft ist für H-06 irrelevant, weil (a) das PRE-Gate bereits hart auf DROP steht und (b) die Survivor das AUC-Lift-Kriterium und die ≥2-Fenster-Forderung verfehlen.

### Mechanistische Schlussfolgerung
Die PRE-Gate-Vorbedingung (PRD §4 Z.130 wörtlich: „ρ-Vorprüfung ≥ 0.3 … ρ < 0.3 → DROP") ist auf allen 5 Symbolen über beide Fenster eindeutig nicht erfüllt: Es gibt praktisch keine lineare Kopplung zwischen PE-Drop und nachgelagertem 15-min-Vol-Cluster (ρ ≈ 0). Die Hypothese, PE trage bedingte prädiktive Vol-Information oberhalb des ρ-Floors, ist widerlegt. Auch die schwache FDR-Signifikanz auf XRP w1 ist ohne handelbare/diagnostische Relevanz (AUC-Lift ~0.007, weit unter +0.03).

### URTEIL: **DROP.**
PRE-Gate in ALLEN Fenstern verfehlt (max ρ +0.0145 ≪ 0.30) → hartes Ein-Fenster-DROP. Zusätzlich Haupt-Gate-AUC-Lift +0.0072 < +0.03 doppelt verfehlt. Kein GRAUBEREICH. KAPITALFREIHEIT bleibt gewahrt (kein Edge-/bps-/Sharpe-Bezug) — hier ohnehin müßig, da DROP.

### Welle-2-Bilanz (nach GL-006/007/008)
H-04 **WEITER (Mess-Existenz, Kapital PARK)**; H-05 **DROP** (+ C-09-OFI-Bein/C-14-OFI-Erbe, inverser ETH-Befund → H-05b-Empfehlung); H-06 **DROP**. F-WAVE2 Stage 2 hat in keiner der drei Hypothesen einen Stage-1-Survivor gekillt (0 verloren) und damit kein Urteil verändert.

---

## GL-009 · 2026-06-18 · H-04b · C-17/C-41 Lead-Lag-TRADABILITY (Folge nach GL-006, **capital_free=FALSE**) — **PARK**

**Quelle:** `handoff_local/results/h04b_20260618_091937/h04b/c17_c41_tradability_results.{json,md}` (urteilstragender PRIMARY-Block) + `h04b_{lat100,lat500,maker}/c17_c41_tradability_results.{json,md}` (Robustheits-/Sekundär-Spanne, NICHT urteilstragend per Anti-Gaming-Klausel) + `SUMMARY_2026-06-18.md`.
Lauf: BTCUSDT→ETHUSDT auf `trades`, 2 disjunkte Fenster (F0: 9 984 Round-Trips, 1 780 611 314 526..1 780 615 189 170 ms; F1: 9 619 RT, 1 780 615 190 990..1 780 619 066 816 ms), Grid 1 000 ms, Lags [1,2,3] s (H-04-Survivor-Set), `horizon = lag` (DEC-13 Default), `WINDOW_MAX_TICKS=150 000`, `n_bootstrap=200`, `seed=42`, BH-FDR α=0.10 über **F-LEADLAG-TRADE**. Runner 4/4 OK (rc=0).

### Registriertes Gate (H-04b, wörtlich)
- **WEITER:** Netto-Edge/Round-Trip = (Brutto-Einfang über `[t+latenz, t+lag+horizon]` − Friction-Wand 11 bps − Slippage) **> 0 UND statistisch > 0** (Bootstrap `p ≤ 0.05` nach BH-FDR α=0.10 über F-LEADLAG-TRADE) auf **≥ 2 disjunkten Fenstern**.
- **DROP/PARK (hartes Ein-Fenster-Kriterium, kein GRAUBEREICH):** Netto-Edge **≤ 0 in ≥ 1 Fenster** ODER nicht statistisch > 0 (FDR-`p > 0.05`).
- **Anti-Gaming-Klausel:** WEITER nur gültig bei `latenz ≥ 300 ms` UND `Friction-Wand ≥ 11 bps` UND Latenz-Haircut angewandt UND **Taker** (nicht Maker). Abweichung → `gate_valid_assumptions=false` → ein WEITER ist ungültig (Registry H-04b Z.132).

### Urteilstragender Punkt (PRIMARY-Block, gate_valid_assumptions=TRUE)
Latenz 300 ms, Friction-Wand 11 bps, Slippage 4 bps (Gesamt-Wand 15 bps), Taker, Latenz-Haircut angewandt (`[t+latenz, t+lag+horizon]`). Das ist der EINZIGE urteilstragende Punkt der Klausel.

| Kriterium (Registry wörtlich) | Schwelle | Messwert (PRIMARY) | Bestanden |
|---|---|---|---|
| Netto-Edge > 0 in Fenster 0 | > 0 bps | beste Variante `lag3/h3` **-14.95 bps** (Brutto-Einfang +0.05, Brutto-voll +0.08 < 15-bps-Wand); Bootstrap p = 1.0000 | **nein** |
| Netto-Edge > 0 in Fenster 1 | > 0 bps | beste Variante `lag3/h3` **-14.83 bps** (Brutto-Einfang +0.17, Brutto-voll +0.19 < 15-bps-Wand); Bootstrap p = 1.0000 | **nein** |
| Statistisch > 0 (Bootstrap p ≤ 0.05 nach BH-FDR F-LEADLAG-TRADE) | ≤ 0.05 | beide Fenster Bootstrap p = 1.0000; **0 FDR-Survivor** je Fenster und global, p_crit = 0.0000 | **nein** |
| Existenz in ≥ 2 disjunkten Fenstern | ≥ 2 | 0/2 Fenster mit Pass | **nein** |
| Hartes Ein-Fenster-Kriterium ausgelöst | ja-Fall = PARK | beide Fenster verfehlen → schon F0 löst PARK aus (PRD §8.5) | **PARK ausgelöst** |

### Anti-Gaming-Prüfung gegen die Robustheits-/Sekundär-Blöcke
Die Robustheits-/Sekundär-Spanne wird MIT-berichtet (Registry-Erlaubnis Z.128), darf das Urteil aber **NICHT** drehen (Anti-Gaming-Klausel Z.132).

| Block | latency_ms | Maker? | gate_valid_assumptions | F0 Netto (bps) | F1 Netto (bps) | per_window_pass |
|---|---:|---|---|---:|---:|---|
| **PRIMARY (urteilstragend)** | **300** | **nein (Taker)** | **TRUE** | **-14.95** | **-14.83** | **[False, False]** |
| LAT100 (Robustheit) | 100 | nein | FALSE | -14.94 | -14.82 | [False, False] |
| LAT500 (Robustheit) | 500 | nein | TRUE | -14.95 | -14.84 | [False, False] |
| MAKER (Sekundär, adverse-selection-vorbehaltlich Z.127) | 300 | ja | FALSE | -5.95 | -5.83 | [False, False] |

Selbst der adverse-selection-vorbehaltliche MAKER-Block (kleinere effektive Wand) bleibt Netto **negativ** (-5.9 / -5.8 bps) — die Trading-Regel verfehlt das Gate auch unter dieser registry-fremden, ehrlich markierten Annahme. Es existiert **keine** zulässige Annahme-Variante (Anti-Gaming-Klausel), unter der das Gate ein WEITER zulassen würde.

### Mechanistische Schlussfolgerung
H-04 hat in GL-006 die Mess-Existenz des gerichteten Informationsflusses BTC→ETH auf Lags 1–3 s bestätigt (`capital_free:true`). H-04b prüft jetzt die im H-04-Gate ausdrücklich antizipierte härtere Frage: *Ist die gemessene Information nach realistischer Friktion und Latenz handelbar?* Die Antwort der vorregistrierten Trading-Regel über 19 603 Round-Trips ist eindeutig **nein**: Der maximale Brutto-Einfang (nach Latenz-Haircut über `[t+300 ms, t+lag+horizon]`) erreicht **+0.19 bps** (F1, lag3) — das ist ~80× **unter** der 15-bps-Gesamt-Wand. Die Asymmetrie zwischen H-04 (WEITER kapitalfrei, gerichtete Information existiert) und H-04b (PARK nicht handelbar) ist exakt der PRD-§4-Z.133-A-priori: „abgegraste 30–60s-HFT-Anomalie → bleibt PARK". H-04b reproduziert diese Vorhersage empirisch.

### URTEIL: **PARK.**
Hartes Ein-Fenster-PARK-Kriterium (Registry H-04b Z.131) durch F0 ausgelöst (Netto -14.95 bps ≪ 0; Bootstrap p 1.0000), in F1 reproduziert (Netto -14.83 bps). Kein GRAUBEREICH. **Anti-Gaming-Klausel respektiert:** Robustheits-/Sekundär-Blöcke (LAT100/LAT500/MAKER) sind MIT-berichtet, kein WEITER auf einem Nicht-PRIMARY-Punkt erzwungen — alle vier Blöcke führen am PRIMARY-Punkt zum selben PARK. **CLAUDE.md §4 / Autonomie-Protokoll Z.30:** Keine Live-Order, kein Kapitaleinsatz — historischer Backtest mit Kostenmodell auf read-only `trades`. **Kapital-Status:** PARK bestätigt. **Welle-2-Anschluss:** keine Erweiterung der Welle-2-Über-Familie F-WAVE2 (append-only, GL-006/007/008 abgeschlossen); F-LEADLAG-TRADE ist als eigenständige H-04b-Familie geführt. Eine andere Latenz/Wand-Annahme wäre eine NEUE Hypothese H-04c (Registry-Disziplin §2) — hier NICHT nachregistriert.

### Welle-2-Bilanz (nach GL-006/007/008/009)
**H-04 WEITER (Mess-Existenz, capital_free=true, Kapital PARK)** · **H-04b PARK** (Tradability nicht handelbar, capital_free=false, Anti-Gaming respektiert) · **H-05 DROP** (+ C-09-OFI-Bein/C-14-OFI-Erbe; inverser ETH-Befund → H-05b registriert, OOS-pending) · **H-06 DROP**. **Welle 2 inhaltlich abgeschlossen.** Offene Folge-Sache: H-05b wartet auf frische OOS-Daten (C-36 Recording läuft weiter — keine Codearbeit nötig, kein Lauf jetzt). H-04c (alternative Latenz/Wand) NICHT registriert. Tragendes Ergebnis der Welle 2: ein einziges Mess-WEITER (H-04), das in der gleich-vorregistrierten Tradability-Prüfung (H-04b) ehrlich PARK wird — die methodische Trennung „Mess-Gate vs. Tradability-Gate" hat den S2-2023-Trap (Mess-Existenz mit Handelbarkeit verwechseln) erfolgreich abgefangen.

---

## GL-010 · 2026-06-30 · H-05b · C-01 OFI-Vorzeichen INVERSE Lesart (MM-Replenishment, OOS-Konfirmation nach GL-007, KAPITALFREI) — **WEITER (inverse Mess-Existenz; Kapital-Status PARK)**

**Quelle:** `handoff_local/results/h05b_oos_20260630_091035/h05b/h05b_oos_results.{json,md}`.
Lauf: 5 Symbole (BTC/ETH/SOL/BNB/XRP) aus dem **Harvester-Backfill** (read-only `data/harvest/raw/bybit/publicTrade`, Pre-Discovery April/Mai), **2 disjunkte OOS-Fenster A@2026-04-15 + B@2026-05-15** (per Datum fixiert, DEC-15/WP-0-Nachtrag 2026-06-29), δ ∈ {1,5,15,60,300}s, Grid 1000 ms, `WINDOW_MAX_TICKS=300000`, n_surrogates 200, seed 42, BH-FDR α=0.10 über die eigenständige Familie **F-OFI-INV** (F-WAVE2 NICHT erweitert — allein laufend). Gate-Schwellen (sign=−, p≤0.05 FDR, ≥2-Fenster-Konsistenz, |corr|≥0.05 ODER Hit-Rate≤0.47, Ein-Fenster-DROP) EXAKT wie registriert. Datenlage selbst am JSON verifiziert (s.u.).

**Verifikation am JSON (nicht blind übernommen):** `fdr_p_crit=0.0199`, `n_fdr_significant=16` (eigene Re-Zählung: **4 positiv-sig + 12 negativ-sig = 16** ✓), `n_inverse_consistent_cells=2` = **NUR SOLUSDT δ1s und δ5s** (beide Fenster sign−, FDR-sig). Beide SOL-Konsistenz-δ sind in **beiden** Fenstern `sign_direction=-1`. ✓

### Registriertes Gate (H-05b, wörtlich)
- **WEITER (Mess-Existenz inverse Richtung):** `sign(corr(OFI_t, ret_{t+δ})) = −` UND `p ≤ 0.05` nach BH-FDR α=0.10 über **F-OFI-INV** UND **Konsistenz in ≥ 2 disjunkten Fenstern** (Entdeckungszelle ETHUSDT w0 δ1s ausgeschlossen) UND Magnitude **`|corr| ≥ 0.05` ODER Hit-Rate ≤ 0.47**. „Eines der beiden Magnitude-Kriterien reicht; `|corr| ≥ 0.05` ist primär, die inverse Hit-Rate sekundärer Plausibilitäts-Anker."
- **DROP:** Vorzeichen **≥ 0** in ≥ 1 konfirmatorischem Fenster ODER Magnitude verfehlt (`|corr| < 0.05` UND Hit-Rate > 0.47) ODER FDR-`p > 0.05` ODER **Konsistenz nur durch die Entdeckungszelle getragen**. Hartes Ein-Fenster-Kriterium, kein GRAUBEREICH.
- **Symmetrie-Falle (der ehrlichste Ausgang):** Ist OFI „WEDER konsistent positiv … NOCH konsistent negativ", so sind **beide** Vorzeichen-Lesarten verworfen — OFI trägt keine stabile Vorzeichen-Information. Das löst KEIN H-05c aus; der Vorzeichen-Test ist erschöpft.
- **OOS/Data-Snooping Regeln 1–3:** Entdeckungszelle nicht konfirmatorisch (1); ≥2-Fenster-Konsistenz aus ANDEREN Zellen (2); frische/erweiterte Daten über den Entdeckungslauf hinaus (3). Per DEC-15 durch April/Mai-Pre-Discovery-Backfill konstruktiv erfüllt.

### Je-Kriterium-Tabelle (Schwelle vs. Messwert vs. bestanden) — bewertet an der inverse-konsistenten Zelle SOLUSDT

| Kriterium (Registry wörtlich) | Schwelle | Messwert (SOL δ1s / SOL δ5s) | Bestanden |
|---|---|---|---|
| Vorzeichen `sign(corr) = −` in BEIDEN Fenstern | sign=− | δ1s: w0 −0.0102 / w1 −0.0505 · δ5s: w0 −0.0172 / w1 −0.0215 — **alle 4 sign−** | **ja** |
| `p ≤ 0.05` nach BH-FDR (F-OFI-INV, p_crit=0.0199) in BEIDEN Fenstern | ≤ p_crit | δ1s: w0 0.0199 / w1 0.0050 · δ5s: w0 0.0050 / w1 0.0050 — **alle FDR-sig** | **ja** |
| Konsistenz in ≥ 2 disjunkten Fenstern | ≥ 2 | δ1s: Fenster {0,1} · δ5s: Fenster {0,1} — **2/2** | **ja** |
| Entdeckungszelle (ETH w0 δ1s) ausgeschlossen / nicht tragend | Ausschluss | per Konstruktion: Lauf nur auf April/Mai; SOL ≠ ETH-Juni; Konsistenz aus ANDEREM Symbol getragen | **ja (Regel 1–3)** |
| Magnitude `|corr| ≥ 0.05` ODER Hit-Rate ≤ 0.47 (eines reicht) | OR | δ1s: HR 0.4095/0.4210 ≤ 0.47 ✓ (|corr| nur w1 0.0505 ✓) · δ5s: HR 0.4445/0.4605 ≤ 0.47 ✓ (|corr| nein) | **ja (über sek. Anker)** |
| Hartes Ein-Fenster-DROP: sign ≥ 0 in ≥ 1 konfirmat. Fenster | kein neg.-Bruch | beide SOL-Zellen in BEIDEN Fenstern sign− → **nicht ausgelöst** | **nicht ausgelöst** |

→ Die registrierten WEITER-Kriterien sind durch **SOLUSDT δ1s und δ5s** literal erfüllt; das DROP-Kriterium ist an diesen Zellen nicht ausgelöst.

### Disziplin-Fragen (PFLICHT, je einzeln beantwortet)

**1. Liest die Registry das Gate PER (Symbol,δ)-Zelle oder als generelle Vorzeichen-Eigenschaft von OFI?** — **Per (Symbol,δ)-Zelle.** Der Registry-Wortlaut trägt das eindeutig: „jede δ-Variante × Symbol zählt einzeln in F-OFI-INV" (H-05b Fenster/Datenbasis) und „alle δ × Symbol × Fenster-Varianten = eine Familie" (FDR-Familie). Die Konsistenz-Forderung lautet „Konsistenz in ≥ 2 disjunkten Fenstern" — operationalisiert je Zelle als „sign− UND FDR-sig in BEIDEN Fenstern" (genau das Feld `inverse_consistent` je (Symbol,δ)). H-05b ist außerdem das **Spiegelbild von H-05**, und H-05 wurde in GL-007 ebenfalls per-Zelle gelesen („gesucht: irgendein Symbol/δ mit FDR-sig POSITIVEM Vorzeichen in BEIDEN Fenstern"). Ein konsistentes Spiegel-Urteil MUSS dieselbe per-Zelle-Lesart anlegen. Die alternative „generelle Vorzeichen-Eigenschaft von OFI" (die 4 positiv-sig Zellen widersprächen einer „konsistent negativen" These) ist **NICHT der registrierte Test** — sie wäre ein NEU erfundenes Kriterium „keine positive Zelle in der ganzen Familie", das im H-05b-Text nirgends steht. Es ausdrücklich NICHT anzulegen ist hier die Anti-Torpfosten-Disziplin in BEIDE Richtungen (der Auftrag verbietet genau diese Erfindung, um ein DROP zu erzwingen). **Folglich: SOL δ1s/δ5s erfüllen WEITER.**

**2. Erfüllt SOL δ1s/δ5s die DROP-Bedingung „Vorzeichen ≥ 0 in ≥ 1 konfirmatorischem Fenster"?** — **Nein.** Am JSON verifiziert: SOL δ1s w0 −0.0102 / w1 −0.0505; SOL δ5s w0 −0.0172 / w1 −0.0215. Alle vier konfirmatorischen Messpunkte sind sign−. Die positive SOL-Zelle (w1 **δ60s** +0.0099, FDR-sig) ist eine ANDERE δ-Zelle und kein konfirmatorisches Fenster der δ1s/δ5s-Zellen; sie löst das per-Zelle-DROP für δ1s/δ5s nicht aus. Kein Vorzeichen-Bruch innerhalb der tragenden Zellen.

**3. Ist die Konsistenz „nur durch die Entdeckungszelle getragen" (Regel 3 / DROP)?** — **Nein.** Die Entdeckungszelle ist ETHUSDT, **Juni**-Collector, δ1s. Der Lauf nutzt ausschließlich **April/Mai**-Pre-Discovery-Backfill (DEC-15) — ein vom Entdeckungslauf nie berührter Zeitraum; die tragenden Zellen sind zudem ein anderes **Symbol** (SOL). Damit ist die ≥2-Fenster-Konsistenz zwingend aus ANDEREN (Symbol×Fenster×δ)-Zellen als der Entdeckungszelle getragen (Regel 2 erfüllt). Regel 3 ist im strengsten Sinn erfüllt: temporal unabhängiger, sauberer Pre-Discovery-Backfill statt regimenaher, doppel-trade-anfälliger Post-Discovery-Daten.

**4. Magnitude überwiegend vom sekundären Anker (Hit-Rate) statt primär (|corr|≥0.05) — darf daraus ein DROP abgeleitet werden?** — **Nein.** Der Registry-Wortlaut ist explizit ein OR: „Effekt-Magnitude `|corr| ≥ 0.05` ODER bedingte Hit-Rate ≤ 0.47 … **Eines der beiden Magnitude-Kriterien reicht**." Er bezeichnet `|corr| ≥ 0.05` als „primär" und die inverse Hit-Rate als „sekundärer Plausibilitäts-Anker" — das ist eine Rangordnung der Anker, KEINE Forderung, dass der primäre erfüllt sein muss. Der sekundäre Hit-Rate-Anker ist in allen vier SOL-Messpunkten erfüllt (HR 0.4095/0.4210/0.4445/0.4605, alle ≤ 0.47), der primäre |corr|≥0.05 nur in SOL w1 δ1s (0.0505) knapp. Aus „überwiegend sekundär getragen" ein DROP abzuleiten hieße, den OR nachträglich in ein AND zu verschärfen = Torpfosten-Verschiebung §2 (in der erschwerenden Richtung, ebenso verboten). **Daher: kein DROP daraus; aber die SCHWÄCHE wird dokumentiert** (s.u.).

### Die explizite A/B-Lesart-Diskussion

**(A) WEITER-Lesart (inverse Mess-Existenz):** Per-Zelle gelesen (Disziplin-Frage 1) erfüllen SOLUSDT δ1s und δ5s ALLE registrierten WEITER-Kriterien literal: sign− in beiden Fenstern, FDR-sig in beiden Fenstern (F-OFI-INV, p_crit 0.0199), ≥2-Fenster-Konsistenz aus Nicht-Entdeckungszellen, Magnitude über den (registry-zulässigen) sekundären Hit-Rate-Anker. Kein DROP-Trigger an diesen Zellen. Analog GL-006/H-04: reine kapitalfreie Mess-Existenz, Kapital PARK.

**(B) Symmetrie-Fallen-/DROP-Lesart:** Die FDR-Familie ist vorzeichen-GEMISCHT (4 positiv-sig + 12 negativ-sig). Greift die Symmetrie-Falle? Der Registry-Wortlaut definiert sie als „OFI WEDER konsistent positiv … NOCH konsistent negativ". Das tragende Wort ist **konsistent**, und „konsistent" ist im H-05b-Text operationalisiert als die per-(Symbol,δ)-≥2-Fenster-Inverse-Konsistenz. H-05 (positiv) ist bereits per GL-007 DROP, weil **keine** Zelle positive ≥2-Fenster-Konsistenz erreichte (die 4 positiv-sig Zellen hier sind alle **Einzelfenster**: BNB w0 δ5s/δ15s, BTC w0 δ300s, SOL w1 δ60s — keine über beide Fenster). H-05b (negativ) erreicht hingegen mit SOL δ1s/δ5s **konsistente** ≥2-Fenster-Inversion. Damit ist die Bedingung der Symmetrie-Falle „NICHT konsistent negativ" **faktisch falsch** — es GIBT eine konsistent-negative Zelle. Die Symmetrie-Falle greift folglich **nicht**.

Die 4 positiv-sig Einzelfenster-Zellen einer „konsistent negativen" These entgegenzuhalten, würde verlangen, „konsistent negativ" als „in der GANZEN Familie keine positive Zelle" umzudeuten — ein Kriterium, das im Registry nicht existiert (Disziplin-Frage 1). Das wäre die Torpfosten-Verschiebung, die der Auftrag ausdrücklich verbietet. **Lesart B (Symmetrie-Falle/DROP) wird daher abgelehnt — nicht weil das Bild stark wäre, sondern weil der registrierte Wortlaut sie nicht trägt.**

**Entscheidung: Lesart A (WEITER), streng am Wortlaut — mit ehrlich dokumentierter Schwäche.**

### Mechanistische Schlussfolgerung
Auf dem temporal unabhängigen April/Mai-Pre-Discovery-Backfill reproduziert genau EIN Symbol (SOLUSDT) an den zwei kürzesten Lags (δ1s, δ5s) ein über beide disjunkte OOS-Fenster **konsistent negatives, FDR-signifikantes** OFI→forward-return-Vorzeichen (MM-Replenishment/Fade der aggressiven Seite — Liquiditätsanbieter absorbieren aggressiven Flow, der Preis kehrt zurück statt zu folgen). Das ist die zu H-05 konkurrierende Mikrostruktur-These und der INC-02/E-04/GL-007-Anker, jetzt OOS und außerhalb der Entdeckungsdaten erstmals ≥2-Fenster-konsistent gemessen. BTC/ETH zeigen das gleiche Vorzeichen in beiden Fenstern, erreichen aber die ≥2-Fenster-FDR-Konsistenz NICHT (sig nur in Fenster A/April). Die inverse Mess-Existenz ist damit literal bestätigt — **aber schmal**.

### SCHWÄCHE / SCHMALHEIT (verbindlicher, ehrlicher Bestandteil des WEITER)
- **Nur 1 Symbol (SOL), nur 2 δ (1s/5s).** BTC/ETH (inkl. des Entdeckungssymbols ETH) sind in beiden Fenstern sign−, erreichen aber FDR-sig NUR in Fenster A → fallen aus der ≥2-Fenster-Konsistenz. Das Entdeckungssymbol selbst trägt die Konfirmation also NICHT.
- **Magnitude überwiegend sekundär.** Der primäre Anker `|corr| ≥ 0.05` ist nur in 1 von 4 tragenden SOL-Messpunkten (w1 δ1s, 0.0505, knapp) erfüllt; die restlichen drei tragen ausschließlich über die inverse Hit-Rate (≤ 0.47). Registry-konform (OR), aber die Effektstärke ist klein (|corr| ~0.010–0.051).
- **Vorzeichen-gemischtes Familienbild.** 4 positiv-sig (Aggression-Folge) gegen 12 negativ-sig (invers) — die inverse Tasche ist real, aber schmal; XRP lehnt sogar überwiegend positiv (4/5 δ positiv in beiden Fenstern, nie FDR-sig). OFI trägt kein universell-inverses Vorzeichen, sondern eine **symbol-/lag-lokalisierte** inverse Struktur auf SOL-Kurzlags.

### KAPITALFREIHEIT (verbindliche Pflichtnotiz — Registry H-05b Z.109)
**WEITER heißt AUSSCHLIESSLICH: das inverse (MM-Replenishment-)OFI-Vorzeichen existiert messbar und ist OOS ≥2-Fenster-konsistent auf SOL-Kurzlags. NICHT handelbar.** H-05b trägt KEINE bps/Edge/PnL/Sharpe-Aussage, KEINEN Friction-Wand-Vergleich (11 bps). Das Mess-WEITER impliziert KEINE handelbare inverse Kante. Eine handelbare inverse Kante wäre eine **NEUE H-05c** (eigener Registry-Eintrag, eigener Lauf, L2-Tiefen-Stream über Wochen, Survey §2.1) — hier **NICHT** registriert und durch dieses WEITER **NICHT impliziert** und **NICHT ausgelöst**. Kapital-Status: **PARK**. Kein Kapitalmodul wird entsperrt.

### URTEIL: **WEITER (inverse Mess-Existenz bestätigt)** — Kapital-Status PARK; H-05c NICHT ausgelöst (nicht impliziert).
Die registrierten WEITER-Kriterien sind durch SOLUSDT δ1s/δ5s literal erfüllt (sign− beide Fenster, FDR-sig beide Fenster in F-OFI-INV, ≥2-Fenster-Konsistenz aus Nicht-Entdeckungszellen unter Regel 1–3, Magnitude über den registry-zulässigen sekundären Hit-Rate-Anker). Das harte Ein-Fenster-DROP ist an den tragenden Zellen nicht ausgelöst. Die Symmetrie-Falle greift nicht, weil eine konsistent-negative Zelle existiert (≠ „NICHT konsistent negativ"). Streng gegen den Wortlaut, ohne Torpfosten-Verschiebung in EINE Richtung: weder wird die schmale inverse Tasche künstlich zum DROP umgedeutet (verbotene Erschwerung), noch wird die dokumentierte Schwäche verschwiegen (verbotene Erleichterung).

### Welle-2-/Nachlauf-Anschluss
- **F-WAVE2 NICHT erweitert** (append-only, GL-006/007/008/009 abgeschlossen). H-05b lief allein → nur Familien-interne BH-FDR über **F-OFI-INV** (p_crit 0.0199); keine Über-Familien-zweite-Stufe nötig (Registry H-05b FDR-Familie).
- **H-05 bleibt DROP** (GL-007, C-01 + C-09-OFI-Bein + C-14-OFI-Erbe gefallen) — H-05b dreht das NICHT zurück; es bestätigt die zu H-05 konkurrierende inverse These als kapitalfreie Mess-Existenz, nicht die ursprüngliche Aggression-Folge-Richtung.
- **H-05c (handelbare inverse Kante) NICHT registriert, NICHT impliziert.** Falls je gewünscht: eigener Registry-Eintrag, L2-Tiefen-Stream über Wochen, eigenes Tradability-Gate (analog der H-04→H-04b-Trennung). Das ist WP-0/Orchestrator-Arbeit; **ich registriere H-05c NICHT selbst.**

> **Nachtrag 2026-07-09 (append-only, Loader-Bug-Transparenz — Originaltext GL-010 oben UNVERÄNDERT, Verdikt UNVERÄNDERT):** Der adversariale Review (`state/CRITICAL_REVIEW_2026-07-09.md`, Befund `src/bybit_edge/research/c01_ofi_sign/oos.py:138`, CRITICAL, 3/3 bestätigt) fand im urteilsspeisenden Loader `load_harvest_window` einen SQL-AND/OR-Präzedenzfehler: `… AND side IS NOT NULL OR S IS NOT NULL` wurde als `(… AND side IS NOT NULL) OR (S IS NOT NULL)` geparst, sodass jede Zeile im LIVE-Payload-Format (Schlüssel `$.S` statt `$.side`) sowohl den NULL-Timestamp-Filter als auch den vorregistrierten Fenster-Start-Filter `ts_exchange_ms >= start_ms` umging. **Der Bug ist am 2026-07-09 im Code gefixt** (OR-Klausel korrekt geklammert; Regressionstest `tests/unit/test_c01_oos.py::test_load_harvest_window_live_form_respects_ts_filters`, verifiziert rot-vor-Fix/grün-nach-Fix; DEC-23). **Materielle Bewertung für DIESEN Lauf (ehrlich, am Code/an der Datenlage geprüft):** Der Bypass greift AUSSCHLIESSLICH für Live-Form-Zeilen (`$.side` NULL, `$.S` gesetzt); Backfill-Form-Zeilen (`side`/`price`/`size`) wurden immer korrekt gefiltert. Die GL-010-Fenster sind per DEC-15 **Pre-Discovery-April/Mai-BACKFILL** (Hive-Partitionen `date=2026-04-15/16` und `date=2026-05-15/16`, `spill_days=1`) — die Backfill-Single-Trade-Form; die Live-Form entsteht erst mit der C-36-Live-Aufzeichnung (Juni+) in ANDEREN date-Partitionen, die der Loader konstruktionsbedingt nie liest (nur Startdatum + Spill-Tag). Ein unabhängiger Beleg derselben Datenlage: `c12_frag/panel.py` dokumentiert die registrierten Backfill-Fenster ausdrücklich als „backfill-bound (flat price form)". Zusätzlich hätte NULL-ts-Leakage im Loader zu NaN im ts-Array geführt (Span-Log `int(ts[0])..int(ts[-1])` wäre mit ValueError gecrasht bzw. t0_ms/t1_ms im JSON NaN); der Lauf lief rc=0 mit plausiblen, im GL-010 verifizierten Fenster-Spans. **Ergebnis: Für GL-010 blieb der Bug nach dieser Prüfung praktisch folgenlos (keine Live-Form-Daten in den gelesenen Partitionen); das WEITER-Verdikt steht materiell nicht in Frage und wird NICHT rückwirkend geändert** (Registry-Disziplin §8, append-only; kein Post-hoc-Revisionismus). Einschränkung transparent benannt: Die Roh-Partitionen liegen auf der Nutzer-Maschine (read-only Junction) — die Bewertung stützt sich auf die dokumentierte Datenherkunft (DEC-14/DEC-15), die Loader-Konstruktion und die Lauf-Artefakt-Konsistenz, nicht auf einen erneuten Scan der Rohdaten. Jeder KÜNFTIGE Lauf über diesen Loader (inkl. Fenster mit Live-Form-Anteil) nutzt den gefixten Filter.

---

## GL-011 · 2026-07-01 · H-05c · C-01 OFI-Fade-TRADABILITY (Folge nach GL-010, **capital_free=FALSE**) — **PARK**

**Quelle:** `handoff_local/results/h05c_20260701_153543/h05c/h05c_results.{json,md}` (urteilstragender PRIMARY-Block) + `h05c_{lat100,lat500,maker}/h05c_results.{json,md}` (Robustheits-/Sekundär-Spanne, NICHT urteilstragend per Anti-Gaming-Klausel) + `SUMMARY_2026-07-01.md`.
Lauf: SOLUSDT auf Harvester-Backfill (read-only Junction `data/harvest`, DEC-15-Fenster A@2026-04-15 + B@2026-05-15), 2 disjunkte Fenster (F0: 29 813 / F1: 25 523 Round-Trips je δ1s), Grid 1000 ms, δ ∈ {1,5}s (GL-010-Survivor), Fade-Regel (Position entgegen OFI-Vorzeichen, glatt nach horizon=δ), `n_bootstrap=200`, `seed=42`, BH-FDR α=0.10 über **F-OFI-INV-TRADE**. Runner 4/4 OK (rc=0).

### Registriertes Gate (H-05c, wörtlich / DEC-16)
- **WEITER:** Netto-Edge/Round-Trip = (Brutto-Einfang des inversen SOL-Moves über `[t+latenz, t+δ]` − Friction-Wand 11 bps − Slippage) **> 0 UND statistisch > 0** (Bootstrap `p ≤ 0.05` nach BH-FDR über F-OFI-INV-TRADE) auf **≥ 2 disjunkten Fenstern** für ≥ 1 Zelle ∈ {SOL-δ1s, SOL-δ5s}.
- **DROP/PARK:** Netto-Edge **≤ 0 in ≥ 1 Fenster** ODER nicht statistisch > 0 (FDR-`p > 0.05`). **Hartes Ein-Fenster-Kriterium (PRD §8.5), kein GRAUBEREICH.**
- **Anti-Gaming-Klausel:** WEITER nur gültig bei `latenz ≥ 300 ms` UND `Wand ≥ 11 bps` UND Latenz-Haircut angewandt UND Taker UND Pass-Zelle ∈ {SOL-δ1s, SOL-δ5s}.

### Urteilstragender Punkt (PRIMARY-Block, gate_valid_assumptions=TRUE)
Latenz 300 ms, Friction-Wand 11 bps, Slippage 4 bps (Gesamt-Wand 15 bps), Taker, Latenz-Haircut angewandt, Symbol SOLUSDT. EINZIGER urteilstragender Punkt.

| Zelle | Round-Trips | Brutto-Einfang (bps) | Brutto-voll (bps) | Wand (bps) | Netto-Edge (bps) | bootstrap p | surrogate p | FDR-sig | bestanden |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| SOL w0 δ1s | 29 813 | +0.048 | +0.076 | 15.0 | **-14.952** | 1.0000 | 0.0050 | nein | nein |
| SOL w0 δ5s | 29 809 | +0.099 | +0.127 | 15.0 | **-14.901** | 1.0000 | 0.0050 | nein | nein |
| SOL w1 δ1s | 25 523 | +0.031 | +0.057 | 15.0 | **-14.969** | 1.0000 | 0.0050 | nein | nein |
| SOL w1 δ5s | 25 519 | +0.062 | +0.088 | 15.0 | **-14.938** | 1.0000 | 0.0050 | nein | nein |

**Tradability-Konsistenz:** δ1s 0/2 Fenster bestanden, δ5s 0/2 Fenster bestanden. `any_tradable_consistent=False`, `weiter_indication=False`, BH-FDR p_crit=0.0000 (0 Survivor).

### Je-Kriterium-Tabelle
| Kriterium (Registry wörtlich) | Schwelle | Messwert (PRIMARY) | Bestanden |
|---|---|---|---|
| Netto-Edge > 0 in ≥ 2 Fenstern (≥1 Pass-Zelle) | > 0 bps | beste Zelle SOL-δ5s w0 **-14.90 bps**; ALLE 4 Zellen ∈ [-14.97, -14.90] bps | **nein** |
| Statistisch > 0 (Bootstrap p ≤ 0.05, BH-FDR F-OFI-INV-TRADE) | ≤ 0.05 | alle 4 Bootstrap p = 1.0000; **0 FDR-Survivor**, p_crit 0.0000 | **nein** |
| ≥ 2-Fenster-Konsistenz für ≥ 1 Zelle | ≥ 2 | δ1s 0/2, δ5s 0/2 | **nein** |
| Hartes Ein-Fenster-Kriterium ausgelöst | ja-Fall = PARK | jede Zelle Netto ≪ 0 → schon F0 löst PARK aus | **PARK ausgelöst** |

### Anti-Gaming-Prüfung gegen die Robustheits-/Sekundär-Blöcke (MIT-berichtet, NICHT urteilstragend)
| Block | latency_ms | Maker? | gate_valid_assumptions | Netto-Spanne (bps) | any_tradable |
|---|---:|---|---|---|---|
| **PRIMARY (urteilstragend)** | **300** | **nein (Taker)** | **TRUE** | **[-14.97, -14.90]** | **nein** |
| LAT100 (Robustheit) | 100 | nein | FALSE | [-14.95, -14.88] | nein |
| LAT500 (Robustheit) | 500 | nein | TRUE | [-14.98, -14.92] | nein |
| MAKER (Sekundär, adverse-selection-vorbehaltlich) | 300 | ja | FALSE | [-5.97, -5.90] | nein |

Selbst der adverse-selection-vorbehaltliche MAKER-Block (kleinere effektive Wand 6 bps) bleibt Netto **-5.9 bps** — keine zulässige Annahme-Variante lässt das Gate WEITER zu (Anti-Gaming respektiert).

### Mechanistische Schlussfolgerung — die H-05b→H-05c-Lehre in Reinform
Die Fade-Richtung ist **real und nicht-zufällig**: der Surrogate-p (Fade-Vorzeichen-Permutation) ist auf allen 4 Zellen 0.0050, d.h. der inverse OFI-Effekt aus GL-010 reproduziert sich als gerichtetes Signal auch hier (konsistent mit dem H-05b-WEITER). ABER: der handelbare **Brutto-Einfang nach 300-ms-Latenz-Haircut ist +0.03…+0.10 bps** — ~150–500× **unter** der 15-bps-Gesamt-Wand. Selbst der volle Move ohne Haircut liegt bei +0.06…+0.13 bps. Das inverse OFI-Signal existiert messbar (H-05b), trägt aber **keine handelbare Netto-Kante** (H-05c). Exakt die H-04→H-04b-Lehre, hier mit noch größerem Abstand zur Wand (das Mess-Signal war schwächer).

### URTEIL: **PARK.**
Hartes Ein-Fenster-PARK-Kriterium (Registry H-05c / DEC-16) durch F0 ausgelöst (Netto -14.95 bps ≪ 0, Bootstrap p 1.0000), in allen 4 Zellen reproduziert. Kein GRAUBEREICH. **Anti-Gaming respektiert** — kein WEITER auf einem Nicht-PRIMARY-Punkt erzwungen; alle vier Blöcke PARK. **CLAUDE.md §4:** kein Live-Order, kein Kapitaleinsatz — historischer Backtest mit Kostenmodell auf read-only Harvester-Backfill. **Kapital-Status:** PARK bestätigt. **Symmetrie/Erschöpfung:** Der OFI-Vorzeichen-Komplex ist damit vollständig abgearbeitet — H-05 (positiv) DROP, H-05b (invers) kapitalfreies Mess-WEITER, H-05c (inverse Tradability) PARK. Eine andere Latenz/Wand-Annahme wäre eine NEUE H-05d (Registry-Disziplin §2) — hier NICHT nachregistriert und durch dieses PARK NICHT nahegelegt.

### Programm-Bilanz (nach GL-011)
Welle 1: H-01/H-02/H-03 alle DROP. Welle 2: H-04 WEITER (kapitalfrei) · H-04b PARK · H-05 DROP · H-06 DROP. Welle 3: H-05b WEITER (kapitalfrei, GL-010) · **H-05c PARK (GL-011)**. **Zwei kapitalfreie Mess-WEITER (H-04, H-05b), beide in der gleich-vorregistrierten Tradability-Prüfung (H-04b, H-05c) ehrlich PARK — 0 handelbare Kanten.** Die Mess-Gate-vs-Tradability-Gate-Trennung hat den S2-2023-Trap (Signal mit Handelbarkeit verwechseln) in BEIDEN Fällen abgefangen.

> **Nachtrag 2026-07-09 (append-only, Loader-Bug-Transparenz — Originaltext GL-011 oben UNVERÄNDERT, Verdikt UNVERÄNDERT):** Auch der GL-011-Lauf (H-05c, `c01_ofi_tradability`) lädt seine Fenster über denselben Loader `load_harvest_window` (`c01_ofi_sign/oos.py`), dessen SQL-AND/OR-Präzedenzfehler (`state/CRITICAL_REVIEW_2026-07-09.md`, CRITICAL, 3/3 bestätigt) am 2026-07-09 gefixt wurde — Details, Fix und Regressionstest siehe Nachtrag 2026-07-09 unter GL-010 sowie DEC-23. **Materielle Bewertung für DIESEN Lauf:** identische Datenlage wie GL-010 — dieselben DEC-15-Pre-Discovery-Backfill-Fenster A@2026-04-15 + B@2026-05-15 (Backfill-Single-Trade-Form `side`/`price`/`size`), nur Symbol SOLUSDT; der Bypass betrifft ausschließlich Live-Form-Zeilen (`$.S`), die in den gelesenen April/Mai-Partitionen nicht vorliegen. **Der Bug blieb für GL-011 nach dieser Prüfung praktisch folgenlos; das PARK-Verdikt steht materiell nicht in Frage und wird NICHT rückwirkend geändert** (Registry-Disziplin §8, append-only). Zur Einordnung: Selbst hypothetisch verschobene Fenster-Inhalte hätten die PARK-Richtung kaum drehen können — der gemessene Brutto-Einfang (+0.03…+0.10 bps) liegt ~150–500× unter der 15-bps-Gesamt-Wand; das Urteil hängt nicht an Randticks des Fensterstarts. Diese Robustheits-Bemerkung ist ergänzende Transparenz, NICHT die Urteilsgrundlage — das Verdikt bleibt das registrierte GL-011-Gate.

> **Nachtrag 2026-07-13 (append-only, Bootstrap-Methodik-Transparenz — Originaltext GL-011 oben UNVERÄNDERT, Verdikt UNVERÄNDERT):** Der zweite adversariale Review (`state/CRITICAL_REVIEW_2_2026-07-13.md`, Lane research-modules, Befund `src/bybit_edge/research/c01_ofi_tradability/net_edge.py:65`, HIGH, 3/3 Skeptiker bestätigt) fand, dass `bootstrap_mean_le_zero_p` (der primäre, urteilstragende Signifikanztest hinter der `bootstrap p`-Spalte oben) Round-Trip-Netto-Edges **i.i.d. mit Zurücklegen** resampelte, obwohl aufeinanderfolgende Round-Trips bei `grid_ms=1000` stark überlappende Forward-Return-Fenster teilen (bei δ=5s ~80% Überlappung, effektive unabhängige Stichprobengröße eher n/5 als n). Ein i.i.d.-Bootstrap unterschätzt dadurch strukturell die wahre Stichprobenvarianz des Mittelwerts und liefert **zu kleine (anti-konservative) p-Werte** — das Risiko: ein Ergebnis könnte fälschlich als statistisch signifikant (p ≤ 0.05) erscheinen, obwohl die wahre Unsicherheit das nicht trägt. **Fix (append-only, DIESER Nachtrag, Code separat committet):** `bootstrap_mean_le_zero_p` in `net_edge.py` resampelt jetzt in **zirkulären zusammenhängenden Blöcken** von Round-Trips (Blocklänge = `ceil(delta_s * 1000 / grid_ms)` Round-Trips, z.B. 5 bei δ=5s/grid_ms=1000ms; 1 = keine Überlappung bei δ=1s/grid_ms=1000ms → degeneriert korrekt zu i.i.d.), exakt nach dem bestehenden Repo-Muster `c11_anen.stats.block_bootstrap_p` / `c06_xmr.stats.block_bootstrap_ci`. Regressionstest `tests/unit/test_c01_ofi_tradability.py::test_block_bootstrap_more_conservative_than_iid_on_autocorrelated_edges` beweist an synthetischen, absichtlich autokorrelierten Daten, dass der Block-Bootstrap einen strikt größeren (konservativeren) p liefert als der alte i.i.d.-Bootstrap auf identischen Daten, und dass der i.i.d.-Fehler in diesem Regime real genug ist, um die registrierte p≤0.05-Schwelle fälschlich zu unterschreiten, während der Block-Bootstrap korrekt darüber bleibt.
>
> **Materielle Bewertung für DIESEN Lauf (GL-011, ehrlich, OHNE echten Re-Lauf):** Ein Re-Lauf mit den echten Harvester-Rohdaten (Roh-Round-Trip-Serien liegen NICHT im State-Verzeichnis vor, nur die aggregierten Zell-Statistiken oben) ist im Rahmen dieses Fixes **nicht durchgeführt worden** — die folgende Einschätzung stützt sich ausschließlich auf die bereits berichteten Aggregate der Tabelle oben und ist entsprechend mit Vorbehalt zu lesen:
> 1. **Bootstrap-p ist in allen 4 Zellen bereits bei der Obergrenze `1.0000`** (`n_bootstrap=200` → `(200+1)/(200+1)`), d.h. unter dem alten i.i.d.-Verfahren hatten buchstäblich 100 % der Resamples einen Mittelwert ≤ 0. Da p ∈ (0, 1] beschränkt ist, kann ein Verfahren, das (korrekterweise) eine GRÖSSERE Resampling-Varianz ansetzt, diesen bereits maximalen Wert nicht weiter erhöhen — die einzig mathematisch mögliche Bewegung wäre gleich oder (bei extremer Blockstruktur) sogar leicht NACH UNTEN, niemals in Richtung einer neuen, fälschlich hohen Signifikanz. Die anti-konservative Fehlerrichtung des Bugs (p fälschlich zu KLEIN) hat hier also keinen Hebel, der GL-011 von PARK Richtung WEITER hätte kippen können.
> 2. **Das harte Netto-Edge>0-Kriterium (Registry H-05c / DEC-16) scheitert bereits rein arithmetisch, unabhängig von JEDER Bootstrap-Methodik:** Netto-Edge liegt in allen 4 Zellen bei **-14.90 bis -14.97 bps** (Brutto-Einfang nur +0.03…+0.10 bps gegen eine 15-bps-Wand) — ein deterministischer, nicht-stochastischer Tatbestand, den keine Resampling-Korrektur verändert. Das harte Ein-Fenster-PARK-Kriterium (PRD §8.5) greift bereits über dieses Kriterium allein.
> **Fazit:** Beide unabhängigen Linien (p bereits an der Obergrenze; Netto-Edge deterministisch negativ) sprechen dagegen, dass eine korrekte Block-Bootstrap-Neuberechnung das PARK-Verdikt materiell in Frage stellen würde — eine abschließende, beweisende Aussage ist aber NUR mit einem echten Re-Lauf auf den Roh-Round-Trip-Serien möglich, und genau das wird hier explizit NICHT behauptet. **Das PARK-Verdikt (GL-011) wird nach Registry-Disziplin §8 (append-only) NICHT rückwirkend geändert** — dieser Nachtrag ist reine Transparenz, keine neue Adjudikation. Siehe DEC-25 für die Entscheidung, den Bug zu fixen ohne das Verdikt zu berühren (identisches Muster zu DEC-23).

---

## GL-012 · 2026-07-01 · H-07 · C-06 Cross-Sectional Ergodic Mean-Reversion (Welle-3-Pilot, KAPITALFREI) — **DROP (struktureller A-priori-Power-DROP)**

**Quelle:** Registrierter H-07-Eintrag + DEC-17 + `c06_xmr`-Build-Befund (Modul grün, 17 Tests) + mathematische Verifikation (unten). **Kein Datenlauf nötig** — das Urteil ruht auf einer beweisbaren Eigenschaft von (Gate, Panel), nicht auf gemessenen Datenwerten.

### Registriertes Gate (H-07, relevant)
- **Achse A (Kern-Trigger):** Über-Dehnung `|z_{i,t}| ≥ 2.5`, wobei `z` die **Cross-Sectional-Standardisierung über die N=5 Panel-Symbole zum Zeitpunkt t** ist (`σ_cross,t` = Cross-Sectional-Std der 5 Symbol-Zeitmittel; M13-Formel, registriert).
- **N-Floor (harte DROP-Bedingung):** < 30 konditionierte (i,t)-Ereignisse pro Fenster nach Konditionierung → DROP; **kein Symbol-Nachladen, keine Z_THRESH-Absenkung** (registriert).

### Struktureller Befund (mathematische Gewissheit)
Die Cross-Sectional-z-Statistik über N Punkte ist hart beschränkt: für ein Extremsymbol gegen N−1 gleiche gilt `z_extrem = (N−1)/√(N−1) = √(N−1)`. Für **N=5**: **max|z| = √4 = 2.0** (Population-Std) bzw. **1.79** (Sample-Std, ddof=1). Beides **< 2.5**. Verifiziert (numerisch):

| N | Std | max\|z\| | Z_THRESH=2.5 erreichbar? |
|---|---|---:|---|
| 5 | Population (ddof=0) | 2.0000 | **nein** |
| 5 | Sample (ddof=1) | 1.7889 | **nein** |

Die M13-Literatur-Schwelle |z|>2.5 wurde für ein **Top-20-Panel** gesetzt (dort √(N−1)=√19≈4.36 → 2.5 gut erreichbar). Auf dem verfügbaren **5-Symbol-Harvester-Panel** ist sie **mathematisch unerreichbar**.

### Je-Kriterium-Anwendung
| Kriterium (Registry) | Schwelle | Struktureller Wert | Bestanden |
|---|---|---|---|
| Achse A: |z|≥2.5 feuert | ≥1 Event möglich | max|z|=2.0 < 2.5 → **0 Events möglich** | **nein (nie)** |
| N-Floor ≥ 30 Events/Fenster | ≥ 30 | N = 0 (garantiert) | **nein → DROP** |
| Nicht-Trivialitäts-Anker, FDR, ≥2-Fenster | — | nicht erreichbar (N=0) | n/a |

### Abgrenzung zur Torpfosten-Verschiebung (verbindlich)
Z_THRESH bleibt **2.5** (registriert, CLI-Default unverändert). Es wird **NICHT** abgesenkt, um N>0 zu erzwingen — das wäre der explizit verbotene „Retten durch Z_THRESH-Absenkung" (Registry H-07 / §2). Der DROP wird **angenommen, nicht umgangen**. Der `c06_xmr`-Build ist korrekt und behält 2.5 als Default; die Mechanismus-Tests nutzen dokumentiert z_thresh=1.8 (NUR um die Verstärkungs-Logik zu prüfen, NICHT urteilstragend).

### Mechanistische Schlussfolgerung
H-07 ist an der **Datenlage** gescheitert (5-statt-20-Symbol-Panel), nicht an einer Widerlegung der Mean-Reversion-Verstärkung selbst — die konnte auf diesem Panel mit der registrierten Literatur-Schwelle **nie gemessen** werden. Das ist der ehrlichste mögliche Ausgang der vorregistrierten H-07: die Verfassung (Literatur-Schwelle) trifft auf eine Daten-Realität (nur 5 Symbole verfügbar), und wir verschieben die Schwelle NICHT, sondern nehmen den DROP. **research_notes §7.5 hat genau das antizipiert** („5 Symbole zu eng gekoppelt").

### URTEIL: **DROP (struktureller A-priori-Power-DROP).**
Achse A (|z|≥2.5) ist auf dem registrierten 5-Symbol-Panel mathematisch nie erfüllbar (max|z|=2.0) → N=0 → registrierter N-Floor reißt mit Sicherheit → DROP. Kein GRAUBEREICH. Kein Datenlauf nötig (beweisbare Eigenschaft); ein empirischer Lauf würde N=0 deterministisch bestätigen (optional für den Audit-Trail, nicht urteilsverändernd). KAPITALFREIHEIT gewahrt (kein bps-Bezug). **Kein H-07-Retten.** Die panel-robuste Rang-/Perzentil-Über-Dehnung ist eine NEUE, separat vorzuregistrierende Hypothese **H-08** (nicht durch dieses DROP nahegelegt außer als ehrliche wissenschaftliche Folge-Frage; A-priori dort weiterhin DROP wegen Survivorship).

### Programm-Bilanz (nach GL-012)
Welle 1: H-01/H-02/H-03 DROP. Welle 2: H-04 WEITER (kapitalfrei) · H-04b PARK · H-05 DROP · H-06 DROP. Welle 3: H-05b WEITER (kapitalfrei) · H-05c PARK · **H-07 DROP (struktureller Power-DROP)**. 2 kapitalfreie Mess-WEITER, beide Tradability-PARK; 0 handelbare Kanten. H-07 ist der erste **struktureller** DROP (Daten-Panel-Grenze), sauber ohne Torpfosten-Verschiebung angenommen.

---

## GL-013 · 2026-07-02 · H-08 · C-06 Cross-Sectional MR mit RANG-Über-Dehnung (Welle-3-Pilot, KAPITALFREI) — **DROP**

**Quelle:** `handoff_local/results/h08_20260702_085014/h08/c06_xmr_results.{json,md}` + `SUMMARY_2026-07-02.md`. Lauf: 5-Symbol-Panel (BTC/ETH/SOL/BNB/XRP) auf read-only Harvester-Backfill, DEC-15-Kalenderfenster A@2026-04-15 + B@2026-05-15 (je 2 Tage, synchronisierte 5-min-Bars), Rang-Über-Dehnung (argmax|z| je Bar, schwellen-frei), Achse B Crash-Dezil-Veto, h ∈ {1,3,6} Bars, n_surrogates=200, BH-FDR α=0.10 über **F-XMR-RANK**. Runner 1/1 OK (rc=0, 68s). `overextension_mode=rank`, `hypothesis=H-08`, `capital_free=true` im Payload bestätigt.

### Registriertes Gate (H-08, wörtlich) — vier Kriterien + N-Floor
WEITER erfordert ALLE gemeinsam: (1) konditionierte μ_rev > 0, (2) Surrogate-p ≤ 0.05 nach BH-FDR über F-XMR-RANK, (3) ≥2-Fenster-Konsistenz, (4) Nicht-Trivialitäts-Anker: Δμ > 0 UND nicht-überlappende 95%-Bootstrap-CIs (kond vs. baseline) in ≥2 Fenstern für ≥1 h, plus N ≥ 30 je Fenster. Hartes Ein-Fenster-Kriterium, kein GRAUBEREICH.

### Je-Kriterium-Tabelle (Messwerte, urteilstragend)

| Kriterium | Schwelle | Messwert | Bestanden |
|---|---|---|---|
| N-Floor ≥ 30 Events/Fenster | ≥ 30 | 501–508 Events je Fenster (Rang-Modus feasible — bestätigt die GL-012/DEC-18-Konstruktion) | **ja** |
| Konditionierte μ_rev > 0 in allen tragenden Zellen | > 0 | A: +0.9/+2.2/+2.3 bp (h1/h3/h6) · B: +0.4/+0.7/**−0.8** bp — **B-h6 NEGATIV** | **nein** (B h6) |
| Surrogate-p ≤ 0.05 nach BH-FDR (F-XMR-RANK) | ≤ 0.05 | p ∈ [0.0796, 0.9453] über alle 6 Zellen; **0 FDR-Survivor**, p_crit = 0.0000 | **nein — in ALLEN Zellen** |
| ≥2-Fenster-Konsistenz | ≥ 2 | 0 Fenster mit FDR-sig Zelle | **nein** |
| Nicht-Trivialitäts-Anker (CIs nicht-überlappend, Δμ>0, ≥2 Fenster) | erfüllt | `ci_nonoverlap_vs_baseline=False` in **allen 6 Zellen**; Δμ in Fenster B sogar ≤ 0 (h3: −0.3 bp, h6: −2.2 bp) | **nein — in ALLEN Zellen** |
| `any_amplified_consistent` | true für WEITER | **False** | **nein** |

### Mechanistische Schlussfolgerung — der Survivorship-Guard hat gegriffen
Das Regime-Muster ist exakt das vorregistrierte Survivorship-Szenario (research_notes §7.5, XRP-April): In **Fenster A (April)** zeigt die konditionierte Reversion durchweg positive Δμ (+0.8 bis +1.6 bp über Baseline) — schwach, nicht signifikant, aber richtungskonform mit dem April-MR-Regime. In **Fenster B (Mai)** kollabiert der Effekt vollständig: Δμ ≤ 0 bei h3/h6, konditionierte μ_rev bei h6 sogar negativ (Momentum statt Reversion). Der ≥2-Fenster-über-Regimes-Zwang (April UND Mai) war als Survivorship-Guard konstruiert — er hat den April-only-Effekt wie vorhergesagt aussortiert. Zusätzlich ist die Verdünnung der Rang-Definition sichtbar: das je Bar extremste von 5 eng gekoppelten Symbolen trägt keine CI-trennbare Verstärkung gegen den unkonditionierten Baseline. Die E-04-verbotene Trivial-Lesart wurde korrekt NIE als Erfolgspfad angeboten (Anker-Konstruktion), und auch die nicht-triviale Amplifikations-These ist damit empirisch gefallen.

### URTEIL: **DROP.**
Hartes Ein-Fenster-Kriterium mehrfach ausgelöst (0 FDR-Survivor in beiden Fenstern; Anker in allen 6 Zellen verfehlt; B-h6 mit negativem μ_rev). Kein GRAUBEREICH. KAPITALFREIHEIT gewahrt (kein bps-Edge-Bezug im Gate; die bp-Angaben oben sind reine Mess-Deskriptoren der Renditegröße, keine Tradability-Aussage). **C-06 ist damit vollständig und empirisch abgeschlossen:** Trivial-MR (E-04, verboten), absolute Über-Dehnung (H-07, struktureller Power-DROP GL-012), rang-basierte Über-Dehnung (H-08, empirischer DROP GL-013). Kein H-08b/H-09-Nachschieben nahegelegt — der C-06-Hypothesenraum auf dem verfügbaren 5-Symbol-Panel ist erschöpft.

### Programm-Bilanz (nach GL-013)
Welle 1: H-01/H-02/H-03 DROP. Welle 2: H-04 WEITER (kapitalfrei) · H-04b PARK · H-05 DROP · H-06 DROP. Welle 3: H-05b WEITER (kapitalfrei) · H-05c PARK · H-07 DROP (strukturell) · **H-08 DROP (empirisch)**. 2 kapitalfreie Mess-WEITER, beide Tradability-PARK; **0 handelbare Kanten**. 13 Gate-Verdikte, 0 Torpfosten-Verschiebungen.

---

## GL-014 · 2026-07-18 · H-18 · C18 GL-006/H-04 Lead-Lag High-N-Surrogat-Auflösungs-Audit (Welle 5, KAPITALFREI) — **AUDIT-BEFUND dokumentiert (kein Hypothesen-Verdikt; GL-006 bleibt unverändert)**

**Sonderstatus (Registry H-18, wörtlich):** H-18 ist KEINE neue empirische Hypothese über die Welt, sondern ein Auflösungs-Audit des bereits adjudizierten GL-006 (H-04, WEITER kapitalfrei, Kapital PARK) — byte-identische F-LEADLAG-Pipeline mit GENAU EINER vorab deklarierten Änderung: `n_surrogates` 200 → 100.000. **Das GL-006-Verdikt bleibt append-only UNVERÄNDERT.** Ein abdriftender GL-006-Survivor falsifiziert NICHT GL-006, sondern markiert das Messungen-WEITER als „auflösungsbedingt fragil" (Audit-Finding, vorregistriert). Dieser Eintrag vergibt daher KEIN WEITER/DROP/GRAUBEREICH, sondern dokumentiert den Audit-Befund.

**Quelle:** `state/c18_leadlag_audit_results.{json,md}` (archiviert aus `handoff_local/results/h18_20260717_160409/h18/`), erzeugt 2026-07-17 16:07:35 UTC auf der Nutzer-Maschine (RTX 5060 Ti, torch 2.11.0+cu128, backend `torch-cuda`). Läufe: H18_SELFTEST rc=0 (Methodik-Äquivalenz gegen die ORIGINALE c17_c41-Pipeline bei N=500, `equivalence_holds=true`, 12 s) → H18_GPU_CHECK rc=0 → H18_AUDIT rc=0 (192 s — die Registry-Schätzung ~1 h wurde 18-fach unterboten). **`verdict_carrying=true`** (echtes CUDA-Device + volle 100.000 Surrogate + Seed 42 = registriert; Compute-Gating-Pflicht erfüllt).

### Datenbindung vs. GL-006 (`all_windows_match_gl006=False` — ehrlich eingeordnet, nicht überstimmt)
Beide Fenster sind **byte-identisch** zu den archivierten GL-006-Fenstern (F0: 2026-06-04 22:15:14–23:19:49 UTC, 3874 Bars · F1: 23:19:50–00:24:26 UTC, 3875 Bars; `t0_ms`/`t1_ms`/`n_bars` exakt gleich, `span_match=true`). Die **Observed-Statistiken** weichen jedoch bis max. **7,13e-6** von den GL-006-Archivwerten ab und reißen damit die strikte Bindungstoleranz (atol 1e-9 / rtol 1e-6). Einordnung: Das ist die Signatur von **Library-Versions-Drift** — der GL-006-Lauf (2026-06-17) lief im damaligen Umgebungs-Stack, dieser Lauf im frisch aufgesetzten venv (numpy 2.4.6, Python 3.13); Quantil-Binning-Kanten verschieben sich dabei um O(1e-6). KEINE Fenster- oder Datenabweichung. Konsequenz (streng, wie vom Runner geflaggt): Dieser Lauf ist formal eine **Re-Messung derselben Fenster unter leicht anderem Numerik-Stack**, kein byte-identischer Replay — T1/T2 werden unten trotzdem berichtet, tragen aber diesen Vorbehalt. Der Flag wird bewusst NICHT wegdiskutiert.

### T1 — 12 GL-006-Stage-1-FDR-Survivor bei N=100.000 (vorregistriert: alle bei p ≤ 1e-3 UND BH-signifikant)

| F | Zelle | p (GL-006, N=200) | p (neu, N=100k) | MC-SE | p≤1e-3 | BH-sig (neu) | hält |
|---|---|---:|---:|---:|:---:|:---:|:---:|
| 0 | TE BTC→ETH lag1 | 0,02488 | 0,012420 | 3,5e-4 | nein | ja | nein |
| 0 | TE ETH→BTC lag1 | 0,06468 | 0,068989 | 8,0e-4 | nein | ja | nein |
| 0 | TE BTC→ETH lag2 | 0,00995 | **0,000560** | 7,5e-5 | **ja** | ja | **ja** |
| 0 | TE ETH→BTC lag2 | 0,06965 | 0,028150 | 5,2e-4 | nein | ja | nein |
| 0 | TE BTC→ETH lag3 | 0,01493 | 0,004500 | 2,1e-4 | nein | ja | nein |
| 0 | TE ETH→BTC lag3 | 0,01990 | 0,030420 | 5,4e-4 | nein | ja | nein |
| 0 | TE BTC→ETH lag5 | 0,04478 | 0,025570 | 5,0e-4 | nein | ja | nein |
| 0 | WCOH BTC/ETH | 0,00498 (Floor) | **0,000010 (neuer Floor)** | 1,0e-5 | **ja** | ja | **ja** |
| 1 | TE BTC→ETH lag1 | 0,00498 (Floor) | **0,000010 (neuer Floor)** | 1,0e-5 | **ja** | ja | **ja** |
| 1 | TE ETH→BTC lag1 | 0,00498 (Floor) | 0,003650 | 1,9e-4 | nein | ja | nein |
| 1 | TE BTC→ETH lag2 | 0,01990 | 0,012320 | 3,5e-4 | nein | ja | nein |
| 1 | WCOH BTC/ETH | 0,00498 (Floor) | **0,000010 (neuer Floor)** | 1,0e-5 | **ja** | ja | **ja** |

**`t1_holds=false` — 4/12 halten die strenge p≤1e-3-Schranke.** ABER: **12/12 bleiben BH-FDR-signifikant (α=0,10) auch bei 500-facher Auflösung** — der Mess-Existenz-Befund von GL-006 verschwindet nicht, er wird präzisiert:
- **3 Zellen sitzen auch bei N=100.000 noch am Floor** (p < 1e-5): beide WCOH-Zellen + TE BTC→ETH lag1 in F1 — bei N=200 als p=0,00498 gefloort, tatsächlich ≥500× stärker. Plus TE BTC→ETH lag2 F0 mit p=5,6e-4. Diese 4 sind bei extremer Auflösung **hart bestätigt**.
- **8 Zellen driften** auf echte p-Werte im Bereich 3,65e-3 … 6,9e-2 — bei N=200 nicht von „sehr stark" unterscheidbar, jetzt als **moderat (aber BH-haltbar)** aufgelöst. Vorregistrierte Lesart: diese 8 Zellen sind ab jetzt als „**auflösungsbedingt fragil**" etikettiert.
- **Richtungsmuster (deskriptiv):** ALLE 4 harten Zellen sind BTC→ETH bzw. symmetrische Kohärenz; ALLE ETH→BTC-TE-Zellen (4 von 4 unter den Survivorn) driften. Die Auflösung schärft die Asymmetrie: die BTC-führt-Kante ist das robuste Substrat des GL-006-Befunds.

### T2 — die zwei Lesart-Entscheidungszellen (vorregistriert: Auflösung mit > 5 MC-SE Abstand von p_crit)

| Zelle (F0) | p (neu) | p_crit (neu) | Distanz | Seite | aufgelöst |
|---|---:|---:|---:|---|:---:|
| TE ETH→BTC lag2 | 0,028150 | 0,068989 | **78,1 MC-SE** | signifikant | **ja** |
| TE ETH→BTC lag1 | 0,068989 | 0,068989 | **0,0 MC-SE** | signifikant | nein |

**`t2_holds=false`, aber differenziert:** Lag2 löst sich **entschieden** auf die signifikante Seite auf (78 MC-SE — bei N=200 war die Zelle < 1 MC-SE von p_crit, jetzt eindeutig). Lag1 ist ein **struktureller Sonderfall**: p_neu == p_crit EXAKT, weil die Zelle selbst die BH-Step-up-Grenze definiert (die größte akzeptierte p-Zelle hat per Konstruktion Distanz 0 zu p_crit). Das vorregistrierte „>5 MC-SE"-Kriterium ist für die grenzdefinierende Zelle prinzipiell unerfüllbar — kein MC-Auflösungsproblem, sondern eine strukturelle Eigenschaft des BH-Verfahrens, die bei der T2-Formulierung nicht antizipiert wurde. Die Zelle IST signifikant (letzte akzeptierte), bleibt aber definitionsgemäß marginal.

### AUDIT-BEFUND (kein Verdikt)
1. **GL-006 wird NICHT falsifiziert.** 12/12 Survivor bleiben bei 500× Auflösung BH-signifikant; das Messungen-WEITER steht.
2. **Präzisierung:** 4 Zellen (WCOH ×2, BTC→ETH lag1 F1, BTC→ETH lag2 F0) sind hart bestätigt (3 davon < 1e-5); 8 Zellen — darunter ALLE ETH→BTC-Kanten — tragen ab jetzt das vorregistrierte Etikett **„auflösungsbedingt fragil"** (echte p 3,7e-3…6,9e-2). Jede künftige Arbeit, die auf der ETH→BTC-Richtung aufbaut, muss diese Fragilität zitieren.
3. **T2-Lesart:** Die GL-006-Unentscheidbarkeit von ETH→BTC F0 lag2 ist AUFGELÖST (signifikant, 78 MC-SE); lag1 bleibt strukturell marginal (BH-grenzdefinierend — Distanz 0 per Konstruktion).
4. **Vorbehalt:** Datenbindung formal nicht byte-identisch (Observed-Stat-Drift ≤ 7,13e-6 bei identischen Fenstern; Library-Versions-Signatur). Für eine byte-identische Reproduktion müsste der Juni-Umgebungs-Stack eingefroren nachgebaut werden — angesichts der Größenordnung (1e-6 auf Statistiken von O(1e-2)) wird das als nicht verhältnismäßig eingestuft, aber offen dokumentiert.
5. **Kapitalfrei bestätigt:** keine bps/Edge/PnL-Metrik im gesamten Payload; H-18 impliziert keine Tradability-Folge.

### Programm-Bilanz (nach GL-014)
Welle 1: H-01/H-02/H-03 DROP. Welle 2: H-04 WEITER (kapitalfrei) · H-04b PARK · H-05 DROP · H-06 DROP. Welle 3: H-05b WEITER (kapitalfrei) · H-05c PARK · H-07 DROP (strukturell) · H-08 DROP (empirisch). Welle 5 (laufend): **H-18 Auflösungs-Audit abgeschlossen** (GL-006 präzisiert: 4 harte + 8 fragile Zellen; kein neues Verdikt) · H-14…H-17 ausstehend (H-16-Lauf 1 durch PC-Neustart abgebrochen). Weiterhin 2 kapitalfreie Mess-WEITER, beide Tradability-PARK; 0 handelbare Kanten. 14 GL-Einträge, 0 Torpfosten-Verschiebungen.

---

## GL-015 · 2026-07-24 · H-16 · C16 Time-Arrow-CNN: Zeit-Irreversibilität im 1s-Trade-Imbalance-Flow (Welle 5, KAPITALFREI, GPU) — **WEITER (kapitalfrei)**

**Quelle:** `state/c16_arrow_results.{json,md}` (archiviert aus `handoff_local/results/h16_20260722_115606/h16/`), erzeugt 2026-07-23 22:06 UTC. Lauf: RTX 5060 Ti, torch 2.11.0+cu128, `verdict_bearing=true` (echtes CUDA, `cell_errors=[]`, `non_verdict_reasons=[]`, 0 Sentinel-Zellen, torch/numpy-Scalogramm-Paritätscheck max_abs_diff 2,4e-7 < atol 1e-6). Datenfenster 2026-03-27..2026-07-19 (gepinnt; die Envelope-only-Tage ab 2026-07-17 wurden von der Datenhygiene sauber als INVALID ausgeschlossen — effektiv bis 2026-07-16, z.B. BTC 112/115 valide Tage). Methodik registriert: 5 Seeds + 20 IAAFT-Surrogat-Retrainings + 3 Ablationen je Symbol = 140 Trainings, Seed 42, ~57h GPU über 4 Checkpoint-Sessions (das in dieser Welle eingeführte Checkpoint/Resume-System — Commit 341d1d9 — hat den Lauf über 2 Timeouts und 1 Fortsetzung bit-identisch zusammengesetzt).

### Registriertes Gate (H-16, wörtlich) vs. Messung

Gate: WEITER, wenn Held-out-Day-Forward-vs-Reversed-AUC >=0,60 MIT IAAFT-Surrogat-Null-95.-Perzentil unter 0,53, bei >=4/5 Symbolen nach BH-FDR alpha=0,10 über F-ARROW, UND die phasenrandomisierte Leak-Kontrolle bleibt <=0,52.

| Symbol | AUC | >=0,60 | Surr-p95 | <0,53 | Leak | <=0,52 | p (BH-FDR) | FDR-sig | Zelle bestanden |
|---|---:|:---:|---:|:---:|---:|:---:|---:|:---:|:---:|
| BTCUSDT | **0,7331** | ja | 0,5045 | ja | 0,4979 | ja | ~0 | ja | **ja** |
| ETHUSDT | **0,7353** | ja | 0,5077 | ja | 0,5001 | ja | ~0 | ja | **ja** |
| SOLUSDT | **0,6648** | ja | 0,5082 | ja | 0,4993 | ja | ~0 | ja | **ja** |
| BNBUSDT | 0,5929 | **nein** | 0,5044 | ja | 0,4989 | ja | 5,8e-146 | ja | **nein** (AUC-Floor) |
| XRPUSDT | **0,6416** | ja | 0,5067 | ja | 0,5007 | ja | ~0 | ja | **ja** |

- **Quorum: 4/5 Zellen bestanden — die registrierte >=4/5-Schwelle ist EXAKT erfüllt.** BH-FDR α=0,10 über F-ARROW: 5/5 signifikant (p_crit 5,8e-146 — die p-Werte sind so extrem, dass BH degeneriert; urteilstragend ist das Zell-Quorum inkl. AUC-Floor).
- **Leak-Kontrolle bestanden in allen 5 Zellen** (max 0,5007 <= 0,52) — methodisch valide, kein Repräsentations-Leak.
- **BNBUSDT ehrlich eingeordnet:** Der Effekt existiert auch dort unzweifelhaft (p=5,8e-146 gegen die exakte Bayes-Null 0,5, Surrogate sauber bei ~0,50), liegt aber mit AUC 0,593 knapp UNTER dem registrierten Stärke-Floor 0,60 — die Zelle zählt NICHT zum Quorum. Keine Schwellen-Diskussion: der Floor stand vorregistriert, BNB ist zugleich das dünnste Symbol des Panels (~9,0M Events vs. 196,6M bei BTC).
- **Robustheit (deskriptiv, nicht urteilstragend):** Seed-Streuung winzig (z.B. BTC 0,7228–0,7394 über 5 Seeds); Surrogat-Nullen eng um 0,50 (0,4855–0,5087 über alle 100 Surrogat-Trainings); Effektstärken-Ordnung BTC≈ETH > SOL > XRP > BNB folgt grob der Liquiditätsordnung. Ablations-Diagnostik (3 je Symbol, z.B. BTC 0,695–0,701) zeigt, dass der Effekt nicht an einer Einzelkomponente der Repräsentation hängt.
- **Differenzierungsklausel erfüllt:** Der registrierte Abgrenzungsabsatz zum gesperrten Informationstheorie-Cluster (kein Entropie-Schätzer; gemessen wird Zeit-IRREVERSIBILITÄT unter t→−t mit exakter Bayes-Null 0,5) ist im Payload enthalten (`differentiation_note`).
- **KAPITALFREI bestätigt:** `capital_free=true`, keinerlei bps/Edge/PnL-Metrik im Payload. Eine Handelsfolge wäre eine NEUE H-16b und ist NICHT impliziert.

### URTEIL: **WEITER (kapitalfrei).**
Alle registrierten WEITER-Bedingungen sind erfüllt (4/5-Quorum mit AUC>=0,60 + Surr-p95<0,53 + FDR-sig; Leak-Kontrolle global bestanden). Die 1s-Trade-Imbalance-Dynamik der großen Perp-Märkte trägt eine massive, symbol-replizierte, seed-stabile Zeit-Irreversibilitäts-Signatur (AUC bis 0,735 gegen exakte 0,5-Null), die von IAAFT-Surrogaten (lineare Struktur + Marginal erhalten) NICHT reproduziert wird — der Zeitpfeil sitzt in der nichtlinearen/höheren Struktur des Flows. Verdikt-Status: Messungen-WEITER, Kapital-Status entfällt (kapitalfrei per Registrierung). Kein H-16b-Nachschieben impliziert.

### Programm-Bilanz (nach GL-015)
Welle 1–3 unverändert (2 kapitalfreie Mess-WEITER, beide Tradability-PARK, 0 handelbare Kanten). Welle 5: H-18 Audit abgeschlossen (GL-014) · **H-16 WEITER (kapitalfrei) — das erste vollständige GPU-Hypothesen-Verdikt des Programms** · H-15 läuft (Checkpoint-Tranchen) · H-14/H-17 data-gated (Entsperrung in Prüfung nach Harvester-Backfill). 15 GL-Einträge, 0 Torpfosten-Verschiebungen.

---

## GL-016 · 2026-07-26 · H-09 · C-09 Risk-Limit-Tier-Bunching (Welle 4, KAPITALFREI) — **DROP (empirisch)**

**Quelle:** `state/wave4_20260726/c09_bunch_results.{json,md}` (Lauf `wave4_20260726_084312`, erster Welle-4-Datenlauf überhaupt; 568 s CPU). Kohorten-Lauf mit H-10/H-12 unter der vorregistrierten Über-Familie **F-XDOM1** (Beide-Stufen-Regel, DEC-22). Fenster W1 2026-03-27..05-15 / W2 2026-05-16..07-04, 5 Symbole, 500 Bootstrap-Reps, BH-FDR α=0,10 über **F-BUNCH** (10 Zellen).

### Registriertes Gate vs. Messung
WEITER verlangt für ≥1 Symbol in BEIDEN Fenstern: Bootstrap-p≤0,05 nach BH-FDR UND b̂⁻≥1,0 UND b̂⁻−b̂⁺≥0,5 UND b̂⁻ > max(Placebos); N-Floors ≥2.000 Orders im Band + CF-Erwartung ≥50.

- **0 von 10 Zellen bestehen; 0 FDR-signifikant** (bestes p: SOL-W1 0,0559 — überlebt BH nicht; p_crit degeneriert auf 0). 7/10 Zellen valide (BNB reißt in beiden Fenstern den N-Floor — dünnstes Symbol, dokumentiert, kein Fenster komplett invalide).
- Die b̂⁻-Schätzer streuen vorzeichen-wild (−3,49 … +10,20) bei riesiger Bootstrap-Varianz — das Muster von RAUSCHEN, nicht von systematischem Bunching unter der Tier-Kante. Mehrere Zellen mit b̂⁻ ≤ 0.
- F-XDOM1 Stage 2: keine Stage-1-Survivor aus F-BUNCH → nichts zu aggregieren.

### URTEIL: **DROP.**
Hartes Ein-Fenster-Kriterium in beiden Fenstern verfehlt (0 Survivor). Das vorregistrierte A-priori („Positionsgrößen werden auf Account-, nicht Order-Ebene gesteuert; sichtbares Clustering ist Rundzahl-Präferenz") ist bestätigt. KAPITALFREI gewahrt. Kein H-09b nahegelegt.

---

## GL-017 · 2026-07-26 · H-10 · C-10 Cross-Stream-Pointer-Days + Pre-Event-Drift (Welle 4, KAPITALFREI) — **DROP (empirisch; das registrierte Power-Risiko hat sich als N=0 realisiert)**

**Quelle:** `state/wave4_20260726/c10_pointer_results.{json,md}` (Lauf `wave4_20260726_084312`, 648 s CPU). 30 Detektions-Serien (5 Symbole × {rv, funding, dlog_oi} × {bybit, binance}), Hold-out-Ziel deribit dvol (nie in der Detektion), 79 nutzbare Tage nach 21-Tage-Burn-in, 1.000 Surrogate + 1.000 Permutationen, BH-FDR α=0,10 über **F-POINTER** (4 Zellen).

### Registriertes Gate vs. Messung
WEITER verlangt ALLE 4 Zellen: Stufe-1-Surrogat-p≤0,05 in W1 UND W2, **N_pointer ≥3 je Fenster (Floor NICHT absenkbar)**, Stufe-2-Permutations-p≤0,05 in W1 UND W2. Pointer-Tag-Definition: ≥60% der verfügbaren Serien mit |C_t|≥1,5 gleichgerichtet.

| Stufe | Fenster | N_pointer | p | N-Floor ≥3 | Zelle besteht |
|---:|---|---:|---:|:---:|:---:|
| 1 | W1 | **0** | 1,0000 | NEIN | nein |
| 1 | W2 | **0** | 1,0000 | NEIN | nein |
| 2 | W1 | 0 | n/a | NEIN | nein |
| 2 | W2 | 0 | n/a | NEIN | nein |

- **Es existiert im gesamten 79-Tage-Zeitraum KEIN einziger Pointer-Tag** nach der registrierten Cropper-Regel — und die nicht-urteilstragende Neuwirth-13-Tage-Gegenprobe findet ebenfalls 0 (Anti-Method-Shopping-Diagnostikum: die Nullmenge ist nicht artefakt der Fensterwahl).
- Das in der Registry benannte Power-Risiko („nur ~2–6 erwartete Pointer-Tage je Fenster") hat sich als **N=0** realisiert: Die 30 Streams dieses Frühjahr/Sommer-Regimes richten sich an keinem Tag zu ≥60% gleichzeitig aus.

### URTEIL: **DROP.**
Hartes Ein-Fenster-Kriterium (N-Floor, nicht absenkbar) in beiden Fenstern verfehlt. Ehrliche Einordnung: Das ist primär ein Existenz-DROP für die registrierte Pointer-Tag-Definition in DIESEM 100-Tage-Panel — kein Beleg gegen Ausnahme-Tage in Crash-Regimes (der Zeitraum enthielt keinen). Eine Neuauflage bräuchte einen neuen Registry-Eintrag mit längerem/regime-reicherem Fenster und ist NICHT nahegelegt. **Damit entfällt auch die H-10b-Arithmetik (13–55× über der Wand) — ohne Pointer-Tage gibt es nichts zu handeln.** KAPITALFREI gewahrt.

---

## GL-018 · 2026-07-26 · H-12 · C-12 Cross-Exchange-Fragmentierungsmatrix (RMT/MP, Welle 4, KAPITALFREI) — **DROP (empirisch; W1 valide und Kriterium (b) klar verfehlt — W2 formal invalide)**

**Quelle:** `state/wave4_20260726/c12_frag_results.{json,md}` (Lauf `wave4_20260726_084312`, 346 s CPU). 6-Serien-Panel (BTC/ETH × Bybit/Binance/Deribit-PERPETUAL, Minuten-Last-Price), Ein-Faktor-Gauß-Null je Tag, 1.000 MC-Draws, BH-FDR α=0,10 über **F-FRAG** (78 Tages-Zellen). Erst durch den Binance/Deribit-Backfill vom 2026-07-24 lauffähig geworden (DEC-27/28).

### Validitäts-Vorbedingung (KEIN Gate-Bestandteil)
- **W1: VALIDE** — 47/50 gültige Tage (≥35 ✓), IPR(v1)≤0,25 an 100% der Tage (≥90% ✓).
- **W2: INVALIDE** — nur **31/50 gültige Tage < 35-Floor** (Panel-Lücken v.a. um die Deribit-Stream-Umbenennung Mitte Juni; IPR(v1)-Kriterium wäre erfüllt gewesen). Per Registrierung: für W2 KEIN Verdikt-Beitrag.

### Registriertes Gate vs. Messung (tragend: das VALIDE Fenster W1)

| Kriterium | Schwelle | W1 (valide) | W2 (invalide, informativ) | Bestanden |
|---|---|---|---|:---:|
| (a) Anteil FDR-sig. Tage (λ2 > Ein-Faktor-Null) | ≥20% | **89,4%** (42/47) | 64,5% | ja |
| (b) Median-IPR(v2) über FDR-sig. Tage | ≥0,40 | **0,169** | 0,170 | **NEIN** |
| (c) Max-Last derselben Börse an FDR-sig. Tagen | ≥70% | 95,2% (deribit) | 95,0% (deribit) | ja |

F-XDOM1 Stage 2: alle 62 Stage-1-Survivor (Tages-λ2-p-Werte) überleben auch Stage 2 (p_crit 0,0410) — ändert nichts, da das Gate an (b) scheitert, nicht an der Signifikanz.

### URTEIL: **DROP.**
Das harte Ein-Fenster-Kriterium ist im VALIDEN Fenster W1 ausgelöst: Kriterium (b) wird nicht knapp, sondern strukturell verfehlt — der Median-IPR(v2) von 0,169 liegt praktisch exakt am theoretischen Minimum 1/6≈0,167 eines VOLLSTÄNDIG DELOKALISIERTEN Vektors. Die registrierte Fragmentierungs-These (ein auf EINER Börse lokalisierter zweiter Faktor) ist damit klar widerlegt.

**Ehrlicher Messbefund am Rande (KEIN Verdikt, KEINE Nachregistrierung):** Kriterium (a) zeigt mit 89% signifikanten Tagen, dass ein robuster ZWEITER Faktor jenseits des Marktmodus existiert; (c) zeigt, dass seine größte Einzellast an 95% der Tage auf Deribit liegt. Zusammen mit (b) gelesen: Es gibt systematische Struktur jenseits des Ein-Faktor-Modells, aber sie ist PANEL-BREIT (venue-klassen-artig, z.B. Deribit-vs-Rest-Kontrast), nicht börsen-lokalisiert. Eine darauf zugeschnittene Hypothese wäre ein NEUER Registry-Eintrag und wird durch diesen DROP nicht nahegelegt.

KAPITALFREI gewahrt (H-12b explizit nicht impliziert; friction_audit-A-priori 80–500× unter der Wand).

### Welle-4-Bilanz + Programm-Bilanz (nach GL-018)
**Welle 4 ist mit diesem Lauf vollständig adjudiziert, soweit entsperrt:** H-09 DROP · H-10 DROP · H-12 DROP (alle drei A-prioris „DROP erwartet" bestätigt; 0 Torpfosten-Verschiebungen). H-11/H-13 bleiben GESPERRT — die Entsperr-Checks liefen erstmals und ehrlich: H-11 Manifest-Coverage 8/730 Tagen im geforderten Fenster (die Verzeichnis-Inventur vom 07-20 zählte Lebenszeit-Ordner, nicht Fenster-done_days — die Scout-Lehre aus DEC-27 bestätigt sich erneut); H-13 ohne zwei vol-regime-disjunkte Snapshot-Tage im noch jungen markprice.options-Fenster (wächst kalendarisch).
Gesamtbild: Welle 1–3: 2 kapitalfreie Mess-WEITER (H-04, H-05b), beide Tradability-PARK. Welle 4: H-09/H-10/H-12 DROP, H-11/H-13 gesperrt. Welle 5: H-18 Audit (GL-014) · H-16 WEITER kapitalfrei (GL-015) · H-15/H-14/H-17 laufen. **18 GL-Einträge, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

---

## GL-019 · 2026-07-29 · H-17 · C17 Venue-Fingerprint (Welle 5, KAPITALFREI, GPU) — **VERDIKT AUSSTEHEND (Mess-Befund herausragend; Non-Redundanz-Gate strukturell nicht auswertbar)**

**Quelle:** `state/c17_venue_results.{json,md}` (Lauf über 3 Checkpoint-Sessions, abgeschlossen 2026-07-28 20:44 UTC nach ~59h GPU brutto inkl. eines Maschinen-RAM-Kaskaden-Abbruchs bei Training 93/105 — das c17-Checkpoint-System, Commit 09fd8b3, hat alle Sessions bit-konsistent zusammengesetzt). `verdict_bearing=true`: echtes CUDA, VenueEncoder verdikt-fähig, Batch 2048 = registriertes Minimum erreicht, 10.000 Steps erreicht, `blocked_reasons=[]`. Redundanz-Gate-Quelle: `wave4_20260726/c12_frag_results.json` (erst durch den Welle-4-Lauf vom 26.07. verfügbar).

### Mess-Gate (registriert) vs. Messung — ALLE Kriterien bestanden

| Fold (Symbol out) | Balanced Acc | >=0,60 | p (add-one, 20 Null-Retrainings) | FDR-sig (α=0,10) | bestanden |
|---|---:|:---:|---:|:---:|:---:|
| BTCUSDT | **0,9424** | ja | 0,0476 | ja | ja |
| ETHUSDT | **0,9950** | ja | 0,0476 | ja | ja |
| SOLUSDT | **0,9679** | ja | 0,0476 | ja | ja |
| BNBUSDT | 0,7130 | ja | 0,0952 | ja | ja |
| XRPUSDT | **0,8535** | ja | 0,0476 | ja | ja |

**5/5 Folds bestanden** (registriert: >=4/5), Pooled-Balanced-Accuracy **0,8944** (>=0,55 ✓), BH-FDR p_crit 0,0952. Der Venue-Fingerprint ist SYMBOL-INVARIANT massiv lernbar: Auf nie gesehenen Symbolen erkennt der Contrastive-Encoder die Börse am shape-normalisierten Order-Flow mit bis zu 99,5%. Ehrliche Randnotiz: Die Permutations-Null-Verteilungen sind schwer-schwänzig (Einzel-Nulls bis 0,94 bei ETH, 0,86 bei BNB — volle Retrainings auf permutierten Labels können vereinzelt echte Venue-Struktur wiederfinden); die add-one-p-Konvention verarbeitet das korrekt und BNB bleibt mit p=0,0952 knapp unter p_crit.

### Non-Redundanz-Gate (registriert, bindend) — NICHT AUSWERTBAR

Registriert: |Spearman ρ| < 0,6 der täglichen Embedding-Distance-Serie gegen die c12_frag-Tages-λ2/IPR-Serie an überlappenden Tagen; |ρ|>=0,6 = REDUNDANT zu H-12 = DROP. Gemessen: **n_overlap_days = 2** (technisches Minimum 10) → `evaluable=false`, ρ nicht berechenbar. **Strukturelle Ursache, kein Zufall:** Die c17-Distanz-Serie existiert konstruktionsbedingt nur auf den Fold-TEST-Tagen (letzte 3 Wochen, ~2026-06-14..07-04); die c12-W2-Serie hat in genau diesem Zeitraum nur **2 valide Tage** (2026-06-15, 2026-06-26 — die übrigen 19 Tage scheitern an der 6-Serien-Panel-Vollständigkeit rund um die Deribit-Stream-Umstellung Mitte Juni). Ein Spearman-ρ auf n=2 wäre ohnehin bedeutungslos (immer ±1).

### URTEIL: **KEIN VERDIKT — AUSSTEHEND** (Präzedenz: GL-002/GL-003 PENDING).
Die registrierten WEITER-Bedingungen verlangen das BESTEHEN des Non-Redundanz-Gates — es kann nicht bestehen, was nicht auswertbar ist. Die registrierten DROP-Bedingungen (Pooled<0,55 / <4/5 Folds / ρ>=0,6) sind sämtlich NICHT ausgelöst. Ein WEITER allein auf dem Mess-Befund wäre eine Torpfosten-Verschiebung (das Redundanz-Gate wurde exakt gegen die Möglichkeit registriert, dass H-17 heimlich H-12-Fragmentierung nachmisst — pikanterweise ist H-12 inzwischen selbst DROP/GL-018, was die Redundanz-Sorge inhaltlich entschärft, aber die Registry kennt diese Bedingung nicht als erfüllbar durch H-12-Wegfall). **Auflösungspfade (jeweils NEUE Registrierung, keine automatisch nahegelegt):** (a) H-17-Wiederholung mit über ALLE Tage definierter Distanz-Serie; (b) Redundanz-Prüfung gegen ein neues c12-Fenster mit vollem Panel nach Stabilisierung der Deribit-Daten. KAPITALFREI gewahrt; H-17b nicht impliziert.

---

## GL-020 · 2026-07-29 · H-14 · C14 Conditional Cross-Venue-Lead-Lag-Graph (Welle 5, KAPITALFREI, GPU) — **METHODISCH INVALIDE (Positivkontrolle in beiden Fenstern gescheitert — kein Verdikt, NICHT DROP)**

**Quelle:** `state/c14_panellag_results.{json,md}` (Lauf über mehrere Checkpoint-Sessions, abgeschlossen 2026-07-29 11:15 UTC). Compute-Gating erfüllt: echtes CUDA-Training (RTX 5060 Ti), `ran_on_gpu=true`, kein CPU-/Synthetik-Fallback, `gate_valid=true` — der Lauf ist verdikt-TRAGFÄHIG; das Verdikt scheitert an der METHODEN-Validität, nicht am Compute.

### Vorregistrierte Positivkontrolle (Registry H-14, bindend) — GESCHEITERT

Registriert: Mindestens eine BTC→ETH-Kante (der durch H-04/GL-006 etablierte Effekt, vom Pass-Kriterium ausgeschlossen) muss je Fenster das 95. Perzentil ihrer Retrain-Ablations-Null überschreiten. „Scheitert sie, ist der Lauf METHODISCH INVALIDE (kein Verdikt, NICHT DROP)."

| Fenster | BTC→ETH-Kanten | davon über Null-q95 | Kontrolle |
|---|---:|---:|:---:|
| W1 (2026-03-27..05-15) | 9 | **0** | GESCHEITERT |
| W2 (2026-05-16..07-04) | 9 | **0** | GESCHEITERT |

`validity_status="ungueltig"`, `weiter_indication=null` (payload-seitig korrekt erzwungen).

### URTEIL: **KEIN VERDIKT — METHODISCH INVALIDE.**
Die Ablations-Messmaschinerie (PatchTST-Encoder + Cross-Node-Attention, Retrain-Ablations-ΔLogLoss auf 10s-Vorzeichen-Targets) konnte nicht einmal den BEKANNTEN BTC→ETH-Lead detektieren — damit ist ihr Null-Befund auf allen anderen Kanten uninformativ. Genau dafür war die Positivkontrolle vorregistriert; sie hat funktioniert. Ehrliche Interpretations-Notiz: Der H-04-Lead lebt auf 1–3s-Lags; das H-14-Target (10s-Forward-Vorzeichen) liegt möglicherweise jenseits der Kohärenzzeit des Effekts — eine Horizont-/Architektur-Neufassung wäre eine NEUE Hypothese und wird NICHT automatisch nahegelegt. Deskriptiv am Rande (urteils-irrelevant, da invalide): In W1 überlebte genau 1 von 198 Kanten die BH-FDR (bybit:BNB→binance:SOL, ΔLogLoss 6,1e-4, p=1,0e-4); W2: 0.

### Programm-Bilanz (nach GL-020)
Welle 1–3 unverändert (H-04/H-05b Mess-WEITER, Tradability-PARK). Welle 4: H-09/H-10/H-12 DROP; H-11/H-13 gesperrt. Welle 5: H-18 Audit (GL-014) · **H-16 WEITER kapitalfrei (GL-015)** · H-17 VERDIKT AUSSTEHEND (GL-019, Redundanz-Gate strukturell nicht auswertbar) · H-14 METHODISCH INVALIDE (GL-020, Positivkontrolle) · H-15 läuft (Checkpoint-Tranchen). **20 GL-Einträge, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

---

## GL-021 · 2026-08-07 · H-15 · C-15 Trade-Tape-Event-Grammatik (Welle 5, KAPITALFREI, GPU) — **WEITER (kapitalfrei)**

**Quelle:** `state/c15_grammar_results.{json,md}` (Lauf abgeschlossen 2026-08-07, rc=0). Der Lauf lief über **9 Checkpoint-Sessions** (2026-07-24 bis 2026-08-07, ~180 h GPU brutto) auf RTX 5060 Ti / torch 2.11.0+cu128; das dreistufige Checkpoint-System (Symbol → Fold → Surrogat-Zwischenstand mit PCG64-State + Seed-Modell-Gewichten, Commit 00a531d) hat den Lauf über mehrere Timeouts, einen Windows-Shutdown und einen Junction-Ausfall bit-konsistent zusammengesetzt. **`gate_valid=true`, `ran_on_gpu=true`, `gate_valid_reasons=[]`, `events_capped=false`, `family_complete=true`** — verdikt-tragend.

Methodik wie registriert, ohne jede Abweichung: 5 Symbole × 4 purged Walk-Forward-Folds (1-Tag-Embargo) × 3 Seeds (42/43/44), Causal-Transformer (context 1024, d_model 256, 4 Heads, 4 Layer, 3,49 M Parameter) gegen die beste Variable-Order-Markov-Baseline k≤4 (in ALLEN Zellen `interp_k4`), Datenfenster 2026-03-27..2026-07-04 (100 Tage), Vocab 128 (ohne tick_direction), 200 Within-Hour-of-Day-Block-Shuffle-Surrogate (Blocklänge 256 Events), BH-FDR α=0,10 über **F-GRAMMAR** (5 Zellen).

### Registriertes Gate vs. Messung

Gate: WEITER, wenn OOS-Token-CE des Transformers **≥2% relativ** unter der besten Markov-k≤4-Baseline bei **≥4/5 Symbolen** UND die CE-Lücke **über dem 95. Perzentil der Surrogat-Lücken-Verteilung** liegt, nach BH-FDR α=0,10 über F-GRAMMAR.

| Symbol | Transformer-CE | Markov-CE (interp_k4) | abs. Lücke | **rel. Lücke** | ≥2% | Surr-p95 | > p95 | p | FDR-sig | Zelle |
|---|---:|---:|---:|---:|:---:|---:|:---:|---:|:---:|:---:|
| BTCUSDT | 1,1778 | 1,2155 | 0,0377 | **3,10%** | ja | 0,0257 | ja | 0,00498 | ja | **bestanden** |
| ETHUSDT | 1,0648 | 1,1085 | 0,0437 | **3,94%** | ja | 0,0314 | ja | 0,00498 | ja | **bestanden** |
| SOLUSDT | 1,6003 | 1,6446 | 0,0443 | **2,69%** | ja | 0,0270 | ja | 0,00498 | ja | **bestanden** |
| XRPUSDT | 1,9803 | 2,0898 | 0,1095 | **5,24%** | ja | 0,0601 | ja | 0,00498 | ja | **bestanden** |
| BNBUSDT | 1,9216 | 1,9201 | −0,0015 | **−0,08%** | **nein** | −0,0208 | ja | 0,00498 | ja | **nicht bestanden** (Stärke-Floor) |

**4/5 Symbole bestanden — die registrierte ≥4/5-Schwelle ist erfüllt** (`n_symbols_pass=4`, `family_pass_geq_4of5=true`). BH-FDR: 5/5 Zellen signifikant bei p_crit 0,004975 (alle Surrogat-p am 1/201-Floor — die beobachtete Lücke wurde von KEINEM der 200 Surrogate je Symbol erreicht).

### Einordnung (ehrlich)
- **Der Effekt repliziert über Symbole und Marktphasen.** Alle Einzel-Folds der bestandenen Symbole lagen über der Schwelle, mit steigender Tendenz in den späteren Fenstern (z.B. ETH Fold 0→3: 3,48% → 3,98% → 4,98%). Die Surrogat-Verteilungen sind extrem eng (Streuung im Promillebereich über 200 Reps) — die Trennung Signal/Null ist nicht knapp, sondern deutlich.
- **BNBUSDT fällt sauber und erklärbar durch:** Als einziges Symbol ist die Transformer-CE praktisch identisch zur Markov-Baseline (−0,08%, faktisch Gleichstand); die Fold-Lücken alternieren im Vorzeichen (−0,022 / +0,010 / +0,009 / −0,018). BNB ist mit ~9,0 M Events das mit Abstand dünnste Symbol des Panels (BTC 196,6 M, ETH 221,8 M) — dasselbe Symbol, das schon bei H-16/GL-015 als einziges den Stärke-Floor verfehlte. Bemerkenswert und im Payload sichtbar: BNBs Surrogat-p95 ist **negativ** (−0,0208), d.h. selbst die Surrogat-Läufe erreichten dort im Mittel keine positive Lücke — die formal erfüllte „> p95"-Bedingung ist bei BNB daher inhaltlich leer, und die Zelle scheitert korrekt am 2%-Floor. Keine Schwellen-Diskussion: der Floor stand vorregistriert.
- **Konfundierungs-Kontrolle bestanden:** Das registrierte A-priori lautete „DROP erwartet — Konfundierung durch Saisonalität/Regime-Drift ist der wahrscheinlichere Ausgang". Genau dagegen war die Within-Hour-of-Day-Block-Shuffle-Null konstruiert (erhält Tageszeit-Saisonalität und lokale Blockstruktur, zerstört nur die längerreichweitige Sequenz-Grammatik). Die Lücke überlebt diese Null in 4/5 Symbolen deutlich — die Saisonalitäts-Erklärung ist damit vorregistriert ausgeschlossen.
- **Differenzierung zum gesperrten Informationstheorie-Cluster** (Registry-Pflicht) im Payload enthalten (`differentiation_note`): Event-Stream statt Renditen, CE als Scoring-Rule statt Entropie-Schätzer, kein rho-/Trading-Gate.
- **KAPITALFREI bestätigt:** keine bps/Edge/PnL/Friction-Metrik im Payload. Eine Handelsfolge wäre eine NEUE H-15b und ist **NICHT** impliziert.

### URTEIL: **WEITER (kapitalfrei).**
Alle registrierten WEITER-Bedingungen sind erfüllt (4/5-Quorum mit rel. CE-Lücke ≥2% UND Lücke über Surrogat-p95 UND BH-FDR-Signifikanz). Der Trade-Tape-Event-Stream der großen Perp-Märkte trägt **längerreichweitige sequentielle Struktur, die ein Variable-Order-Markov-Modell 4. Ordnung nicht erfasst** und die von saisonalitätserhaltenden Block-Shuffles nicht reproduziert wird. Verdikt-Status: Messungen-WEITER, Kapital-Status entfällt (kapitalfrei per Registrierung).

**Konditionale Folge-Kandidaten (vom GPU-Scan 2026-07-09 vorgemerkt, durch dieses WEITER erst adressierbar, NICHT automatisch registriert):** DSM-02 (Memory-Horizon-Ablation: bis zu welcher Kontextlänge reicht die Grammatik?) und DSM-04 (Cross-Symbol-Zero-Shot-Universalität) — beide wären neue Registry-Einträge nach §2.

### Welle-5-Bilanz + Programm-Bilanz (nach GL-021)
**Welle 5 ist abgeschlossen:** H-18 Auflösungs-Audit (GL-014) · **H-16 WEITER kapitalfrei** (GL-015) · H-17 VERDIKT AUSSTEHEND (GL-019, Non-Redundanz-Gate strukturell nicht auswertbar) · H-14 METHODISCH INVALIDE (GL-020, Positivkontrolle gescheitert) · **H-15 WEITER kapitalfrei** (GL-021). Zwei von fünf GPU-Hypothesen mit vollem WEITER — beide messen unabhängig voneinander dieselbe Grundaussage: der Orderflow trägt nichtlineare, zeitgerichtete, längerreichweitige Struktur, die lineare bzw. Kurzgedächtnis-Modelle nicht sehen.
Gesamt: Welle 1–3: 2 kapitalfreie Mess-WEITER (H-04, H-05b), beide Tradability-PARK. Welle 4: H-09/H-10/H-12 DROP, H-11/H-13 gesperrt. Welle 5: s.o. **21 GL-Einträge, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten** (alle vier Mess-WEITER sind kapitalfrei; keine Tradability-Hypothese wurde durch sie impliziert).

> **Nachtrag 2026-08-10 zu GL-018 (append-only, Loader-Bug-Transparenz — Originaltext GL-018 oben UNVERÄNDERT, Verdikt UNVERÄNDERT und GESTÄRKT):** Der ursprüngliche H-12-Lauf (2026-07-26) las die **Envelope-Payload-Form nicht** (Live-Trades verschachtelt in `data[…]`, siehe DATASET.md §6). Für Deribit beginnt diese Form ~2026-06-16; die Deribit-Serie war ab dann leer, wodurch 19 von 50 W2-Tagen die Minuten-Abdeckung (1380/1440 je Serie) rissen und **W2 formal invalide** wurde (31 < 35 gültige Tage). Der Loader-Fix (Commit `4f28cda`, `payload_sql.trade_rows_sql`; reales Deribit-Live-Payload als Regressionstest gepinnt, Commit `5456ff1`) wurde am 2026-08-10 mit einem vollständigen c12-Re-Lauf gegengeprüft (`state/h12_20260810_envelope_rerun/`).
>
> **Materielle Bewertung — das Verdikt ändert sich nicht, es wird STÄRKER:**
>
> | | GL-018-Basis (2026-07-26) | Nach Envelope-Fix (2026-08-10) |
> |---|---|---|
> | W1 gültige Tage | 47/50 (valide) | 47/50 (valide) — **unverändert** |
> | W2 gültige Tage | 31/50 (**invalide**) | **38/50 (valide)** |
> | Kriterium (b) W1 | 0,1695 < 0,40 ✗ | **0,1695 < 0,40 ✗ (identisch)** |
> | Kriterium (b) W2 | 0,1698 < 0,40 ✗ | 0,1687 < 0,40 ✗ |
> | `all_criteria_met` | False / False | **False / False** |
>
> W1 ist reines Backfill-Fenster und vom Fix **arithmetisch unberührt** (alle drei Kriterienwerte identisch bis zur 4. Nachkommastelle) — das urteilstragende Fenster von GL-018 steht unverändert. Neu ist, dass **W2 jetzt formal valide ist und ebenfalls an Kriterium (b) scheitert**: Der Median-IPR(v2) liegt mit 0,169 in BEIDEN Fenstern praktisch am theoretischen Minimum 1/6 ≈ 0,167 eines vollständig delokalisierten Eigenvektors. Die registrierte Fragmentierungs-These (auf EINER Börse lokalisierter zweiter Faktor) ist damit nicht mehr nur in einem, sondern in **beiden** Fenstern widerlegt. **DROP bleibt, auf breiterer Basis.** Der begleitende Messbefund aus GL-018 (robuster zweiter Faktor, 89 %/66 % signifikante Tage, Deribit-Maxlast 95 %) bestätigt sich ebenfalls. Registry-Disziplin §8 (append-only) gewahrt: kein Verdikt rückwirkend geändert; siehe DEC-29.

> **Nachtrag 2026-08-10 zu GL-015 (append-only, KORREKTUR EINER FEHLLESUNG DES ORCHESTRATORS — Originaltext GL-015 oben UNVERÄNDERT, Verdikt UNVERÄNDERT):** Die Welle-6-Recherche (Lane B) hat eine Fehlinterpretation in der GL-015-Adjudikation aufgedeckt, die der Orchestrator hiermit korrigiert. Der Originaltext schreibt: *„Ablations-Diagnostik (3 je Symbol, z.B. BTC 0,695–0,701) zeigt, dass der Effekt nicht an einer Einzelkomponente der Repräsentation hängt."* **Diese Lesart ist falsch.** Die Registry definiert die Ablation nicht als Robustheitsprobe, sondern als vorregistrierten Diskriminator zwischen zwei konkurrierenden Erklärungen: *„(b) Volatility-Asymmetry-Ablation — Wiederholung auf |Imbalance| (unsigned) zur **Trennung von Leverage-Effekt- vs. Flow-Richtungs-Asymmetrie** (nicht-urteilstragend, aber Pflicht-Report)."*
>
> **Die Messwerte, im Überschuss über die exakte Bayes-Null 0,5 (vom Orchestrator aus `state/c16_arrow_results.json` nachgerechnet):**
>
> | Symbol | signed AUC−0,5 | unsigned AUC−0,5 | unsigned/signed |
> |---|---:|---:|---:|
> | BTCUSDT | 0,2331 | 0,1982 | **85 %** |
> | ETHUSDT | 0,2353 | 0,2095 | **89 %** |
> | SOLUSDT | 0,1648 | 0,1417 | **86 %** |
> | XRPUSDT | 0,1416 | 0,1324 | **93 %** |
> | BNBUSDT | 0,0929 | 0,0987 | **106 %** |
>
> `unsigned=True` wendet `abs()` auf die Roh-Tagesserie an, BEVOR das Skalogramm gebildet wird (`c16_arrow/driver.py`) — der Klassifikator sieht dann ausschließlich den Betrags-/Aktivitäts-Envelope und **keinerlei Flussrichtung**. Er erreicht damit 85–106 % des gemessenen Zeitpfeil-Überschusses.
>
> **Korrigierte Lesart:** Die Zeit-Irreversibilität ist real und bleibt nachgewiesen — aber ihr Träger ist **überwiegend die Asymmetrie des Aktivitäts-/Volatilitäts-Envelopes** (schneller Anstieg, langsamer Abfall — ein etablierter Stilisierter Fakt, verwandt mit dem Leverage-Effekt), **nicht die Richtung des Order-Flows**. Das Vorzeichen trägt höchstens ~15 % des Effekts, bei BNB gar nichts. Die vorregistrierte Kontrolle hat exakt das geleistet, wofür sie gebaut wurde; der Fehler lag allein in ihrer Auslegung durch den Orchestrator.
>
> **Was sich NICHT ändert:** Das Verdikt **WEITER (kapitalfrei)** steht unverändert. Das registrierte Gate lief ausschließlich auf der signed-AUC (4/5 Symbole ≥0,60, Surrogat-p95 <0,53, BH-FDR, Leak-Kontrolle ≤0,52) und war in allen Punkten erfüllt; die Ablation war vorregistriert als **nicht-urteilstragend**. Registry-Disziplin §8 (append-only) gewahrt: kein Verdikt rückwirkend geändert, kein Torpfosten verschoben.
>
> **Was sich ändert — Auflagen für Folgearbeit:** (1) Die Programm-Formulierung „der Orderflow trägt nichtlineare, **zeitgerichtete** Struktur" ist in dieser Schärfe von den eigenen Payloads **nicht gedeckt** und darf so nicht weiterverwendet werden; korrekt ist „zeit-**asymmetrische** Struktur, überwiegend im Aktivitäts-Envelope". Das betrifft auch `WELLE5_FINAL_REPORT.md` §2.1 und §4, die diese Formulierung tragen (dort per Korrektur-Notiz vermerkt). (2) Jede Hypothese, die auf H-16 aufbaut, MUSS diesen Vorbehalt zitieren — analog zur GL-014-Zitierpflicht für die „auflösungsbedingt fragilen" ETH→BTC-Zellen. (3) Eine Richtungs-/Tradability-Brücke, die implizit annimmt, H-16 belege gerichtete Information, ist damit a priori entwertet. Siehe DEC-30.

---

## GL-022 · 2026-08-12 · H-11 · C-11 AnEn-Vol-Regime-Forecast vs. HAR-RV, 3-Tage-Horizont (Welle 4 nachgeholt, KAPITALFREI) — **WEITER (kapitalfrei) — mit bindenden Einschränkungs-Etiketten; Effektgrößen-Lesart ausdrücklich NICHT gedeckt**

**Quelle:** `state/h11_20260811_135839/c11_anen_results.{json,md}` (Lauf 2026-08-11 13:58–15:02 UTC, 3.801 s, rc=0, CPU — für H-11 registriert und ausreichend). Entsperr-Bedingung erfüllt und im Payload belegt: bybit `publicTrade` + `rest.fundingRate`, BTC+ETH, 2024-03-27..2026-03-26, **730/730 done_days, gapless=true, missing_days_count=0** in allen vier Strömen (`unlock_check.unlocked=true`, Quelle `manifest_done_days`). Damit ist die seit 2026-07-07 bestehende Sperre regelkonform aufgehoben — die Schwelle (>=730 zusammenhängende Tage) wurde NICHT gesenkt.

### Registriertes Gate (wörtlich) und Messergebnis

Gate: „WEITER, wenn fuer mindestens ein Symbol in {BTC,ETH} in BEIDEN Fenstern: CRPSS = 1 - Summe(CRPS_AnEn)/Summe(CRPS_HAR) >=0,05 UND Block-Bootstrap-p<=0,05 nach BH-FDR alpha=0,10 ueber F-ANEN." · DROP: hartes Ein-Fenster-Kriterium, „Kein Graubereich."

| Zelle | n | mean CRPS AnEn | mean CRPS HAR | **CRPSS** | Bootstrap-p | FDR-sig | Zelle besteht |
|---|---:|---:|---:|---:|---:|:---:|:---:|
| BTC W1 (2025-10-01..2026-03-26) | 177 | 0,15042 | 0,21238 | **0,2917** | 0,000999 | ja | **ja** |
| BTC W2 (2026-03-27..06-30) | 96 | 0,12961 | 0,17056 | **0,2401** | 0,000999 | ja | **ja** |
| ETH W1 | 177 | 0,16504 | 0,21934 | **0,2475** | 0,000999 | ja | **ja** |
| ETH W2 | 96 | 0,15630 | 0,21164 | **0,2615** | 0,000999 | ja | **ja** |

F-ANEN: 4 Zellen, BH-FDR alpha=0,10, p_crit=0,000999; `n_fdr_significant=4`; `any_symbol_both_windows_pass=true` (BEIDE Symbole, beide Fenster). Gewichte auf L eingefroren (BTC [2;2;0,5;0;0], ETH [2;0,5;0;0;0]), k=20, Embargo 30 Tage, Blocklänge 5, 1.000 Reps, Seed 42 — alles wie registriert. Die registrierte A-priori-Erwartung war **DROP**; sie ist widerlegt.

### URTEIL: **WEITER (kapitalfrei).**
Das vorregistrierte Gate ist in allen vier Zellen erfüllt, mit dem Vierfachen bis Sechsfachen der Schwelle. Eine unabhängige Implementierungs-Prüfung (6 Achsen: Look-ahead in der Analog-Auswahl, Ziel-Leckage zwischen Trailing- und Forward-Fenstern, Gewichts-Einfrierung, Corsi-Spezifikation mit symmetrischem `<= t-30`-Fit, volle n mit gepaarter NaN-Filterung, zirkulärer Block-Bootstrap) hat **keinen** Defekt gefunden; `stats.py` implementiert die Gneiting-Raftery-Form korrekt. Es gibt bei H-11 **keine vorregistrierte Positivkontrolle**, die gescheitert wäre — der GL-020-Weg („methodisch invalide, kein Verdikt") steht deshalb NICHT offen. Ein nachträgliches Kassieren eines PASS, den man ex ante als unwahrscheinlich notiert hatte, wäre eine Torpfosten-Verschiebung nach unten und damit genau der Regelbruch, den §8 verbietet — in beide Richtungen.

### Bindende Einschränkungs-Etiketten (Zitierpflicht für jede Folgearbeit)

**(E1) Das Gate hat gegen die naheliegendste Null keine Trennschärfe.** Die Registry schreibt für die Baseline wörtlich vor: „CRPS der Punktprognose = |Prognose-Beobachtung|". Die HAR wird damit als **Dirac-Verteilung** bewertet, das AnEn als echte 20-Mitglieder-Verteilung. CRPS belohnt jede Verteilung mit sachgerechter Breite gegenüber einem Punkt — strukturell, ohne jede Information. Kontrafaktual „Dressed HAR" (identische HAR-Punktprognose, lediglich mit einer k=20-Wolke passender Breite umhüllt, **null Zusatzinformation**), analytisch und per 400k-Simulation bestätigt:

| Fehlerverteilung | CRPS_dressed/MAE | geschenkter CRPSS |
|---|---:|---:|
| Gauß, k=20 (analytisch (1+1/k)/√π ÷ √(2/π)) | 0,7425 | **0,2575** |
| Gauß, k→∞ (1/√2) | 0,7071 | **0,2929** |
| t₅ (varianz-normiert) | 0,7656 | **0,2344** |
| Laplace (varianz-normiert) | 0,7877 | **0,2123** |

**Der gemessene CRPSS von 0,240–0,292 liegt vollständig in dem Band, das ein informationsfreies Dressing erzeugt.** Die registrierte Schwelle 0,05 liegt um Faktor ~4–5 UNTER diesem strukturellen Boden; das Gate war ex ante ein Fast-Automatik-PASS. Das ist ein **Registrierungs-Defekt (Schwellenwahl), kein Ausführungsfehler** — der Lauf hat exakt geliefert, was bestellt war.

**(E2) Rest-Skill gegenüber einer gedressten HAR ist vorzeichen-instabil.** 1 − ΣCRPS_AnEn/ΣCRPS_dressedHAR:

| Zelle | vs. Gauß | vs. t₅ | vs. Laplace |
|---|---:|---:|---:|
| BTC W1 | +0,046 | +0,075 | +0,101 |
| BTC W2 | **−0,023** | +0,007 | +0,035 |
| ETH W1 | **−0,013** | +0,017 | +0,045 |
| ETH W2 | +0,005 | +0,035 | +0,062 |

Je nach Annahme über die Schwänze der HAR-Fehlerverteilung besteht das AnEn 2 bis 4 von 4 Zellen — und nur bei schweren Schwänzen deutlich. Welche Annahme zutrifft, ist aus dem Payload **nicht** entscheidbar (die HAR-Fehler-Tagesreihe wird nicht persistiert). Deshalb H-11c (s.u.).

**(E3) Zerlegung: der Vorsprung sitzt fast vollständig im Nicht-Lage-Term.** Exakt und annahmefrei, H−A = (H−M) + (M−A) mit M = `mean_abs_err_ensemble_mean`:

| Zelle | CRPS-Lücke gesamt | Lage-Term | Nicht-Lage-Term | Anteil Nicht-Lage |
|---|---:|---:|---:|---:|
| BTC W1 | 0,06196 | +0,00993 | 0,05203 | **84,0 %** |
| BTC W2 | 0,04095 | −0,00765 | 0,04860 | **118,7 %** |
| ETH W1 | 0,05430 | −0,00716 | 0,06145 | **113,2 %** |
| ETH W2 | 0,05533 | −0,00597 | 0,06130 | **110,8 %** |

**(E4) PIT: Breite plausibel, Zentrum verzerrt.** χ² gegen Gleichverteilung (21 Bins, df=20), mitberichtet und laut Registry ausdrücklich **nicht-urteilstragend**:

| Zelle | n | χ² | p | mittlerer Rang (flach = 10,00) |
|---|---:|---:|---:|---:|
| BTC W1 | 177 | 23,86 | 0,248 | 11,08 (Unter-Prognose) |
| BTC W2 | 96 | 35,69 | **0,017** | 8,78 (Über-Prognose) |
| ETH W1 | 177 | 20,78 | 0,410 | 10,20 |
| ETH W2 | 96 | 31,31 | 0,051 | 7,51 (starke Über-Prognose) |

BH-FDR α=0,10 über die vier Tests: BTC W2 signifikant, ETH W2 knapp verfehlt. Die Bias-Richtung **kippt zwischen W1 und W2** — Fingerabdruck einer regime-veralteten Analog-Bibliothek, gegen die die HAR mit monatlichem Refit adaptiert. Die Ensemble-**Breite** ist dagegen sachgerecht (A/M = 0,718–0,743 liegt praktisch auf dem Minimum ~0,725, das bei kalibrierter Dispersion σ_ens/σ_err ≈ 1 erreichbar ist; Fehl-Dispersion in beide Richtungen triebe A/M auf 0,80–0,95). „Hedging-Blähung" liegt also NICHT vor — der Punkt ist, dass auch eine *korrekt* gewählte Breite gegen eine Dirac-Baseline ein struktureller Gratisgewinn ist.

**(E5) Die ökonomische 25–75×-Notiz ist von diesem Befund NICHT gedeckt.** Die Registry-Zeile („~350–870 bps 3-Tage-Kumulation gegen die 11–15-bps-Wand ≈ 25–75× ÜBER der Wand") ist eine Aussage über die **Bewegungsgröße**, nie an den CRPSS konditioniert. Gemessen wurde eine Verteilung über log-annualisierte RV, keine Preis-Return-Übersetzung; für Vol-Targeting/Straddle wäre die **Lage** der RV-Prognose entscheidend, und dort ist die Evidenz nach (E3) ein Unentschieden mit in 3 von 4 Zellen negativem Vorzeichen. Zusätzlich zeigen beide W2-Zellen systematische Über-Prognose — genau der Bias, der eine Straddle-Long-Regel systematisch überzahlen ließe. Die Notiz darf in keinem Bericht neben dem CRPSS stehen, ohne dass diese Entkopplung explizit mitgeschrieben wird. `KAPITALFREIHEIT (verbindlich)` bleibt unberührt: Monetarisierung wäre eine NEUE **H-11b**, nicht impliziert.

**(E6) Was H-11 belegt und was nicht.** Gedeckt: „Das AnEn schlägt die *registrierte* HAR-Punktschätzer-Baseline unter der *registrierten* Regel, in allen vier Zellen, FDR-fest." **Nicht gedeckt:** „Das AnEn hat einen Informationsvorsprung von ~25 % gegenüber HAR." Der zweite Satz darf im Programm nicht verwendet werden. Ebenfalls unverändert gilt die registrierte Abgrenzung: ein WEITER hier **rehabilitiert den an H-02/GL-001 gebundenen Vol-Stack (C-10/C-35/C-11/C-12) NICHT**.

### Nebenbefund (dokumentiert, ohne Folge)
Die registrierte CRPS-Form nutzt den Spread-Term 1/(2k²) statt des erwartungstreuen 1/(2k(k−1)). Das unterzählt den Spread um Faktor (k−1)/k = 0,95 und wirkt damit **zuungunsten** des Ensembles — ein Handicap, kein Bonus. Es wird nicht geändert (Torpfosten fixiert); die Kontrafaktual-Rechnung in (E1) verwendet dieselbe Form auf beiden Seiten und ist davon unberührt.

### Korrektur einer Orchestrator-Zwischenthese (offengelegt)
Der Orchestrator hatte die Deflation zunächst mit einer Tabelle „HAR-MAE vs. MAE des **Ensemble-Mittels**" belegt (AnEn schlage nur in 1 von 4 Zellen). Dieser Beleg ist defekt und wird zurückgezogen: (a) falsches Funktional — MAE wird vom **Median** minimiert, nicht vom Mittel (`driver.py:372` markiert `mean_abs_err_ensemble_mean` selbst als „secondary/display statistic only — NOT what CRPS scores"); ein Median-MAE existiert im Payload nicht und ist ohne Re-Run nicht rekonstruierbar; (b) statistisch leer — die Differenzen von 0,006–0,010 log-RV-Einheiten entsprechen bei ρ≈0,8 korrelierten Fehlerreihen |t| < 1,4 in allen vier Zellen, sind also Vorzeichen-Lesen an Rauschen. **Die Deflations-Schlussfolgerung überlebt dennoch** — sie trägt über (E1)/(E3), also über die annahmefreie Zerlegung und das Dressing-Kontrafaktual, nicht über den ursprünglichen Punktprognose-Vergleich.

### Folge-Auflage (verbindlich vor jeder Weiterverwendung)
**H-11c** wird vorregistriert (s. `hypothesis_registry.md`): identische Fenster, identische eingefrorene Gewichte, kein Re-Tuning — aber Baseline = **dispersions-gematchte HAR** (unveränderte Punktprognose, gedresst mit der *empirischen* Verteilung ihrer eigenen, zum Zeitpunkt t verfügbaren Residuen). Erst dieses Gate trennt Information von Verteilungs-Geometrie. Bis H-11c entschieden ist, darf H-11 in keiner Folgehypothese als Beleg für einen Prognose-Vorsprung zitiert werden — nur mit den Etiketten (E1)–(E6).

### Programm-Bilanz (nach GL-022)
Welle 1–3 unverändert. Welle 4: H-09/H-10/H-12 DROP · **H-11 WEITER kapitalfrei (GL-022, mit Etiketten)** · H-13 gesperrt. Welle 5: H-18 Audit (GL-014) · H-16 WEITER kapitalfrei (GL-015 + Nachtrag) · H-17 Verdikt ausstehend (GL-019) · H-14 methodisch invalide (GL-020) · H-15 WEITER kapitalfrei (GL-021). **22 GL-Einträge, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

---

## GL-023 · 2026-08-12 · H-11c · C-11 AnEn gegen dispersions-gematchte HAR (Dressed-HAR), Lauf 1 (KAPITALFREI) — **KEIN VERDIKT (registrierte Vorbedingung verfehlt; Vorbedingung war selbst fehlerhaft konstruiert)**

**Quelle:** `state/h11c_20260812_161304_invalid/c11c_dressed_results.{json,md}` (Lauf 2026-08-12 16:13–16:49 UTC, 2.176 s, rc=3). `gate_valid=false`, `anen_side_reproduces_gl022=false`.

### Warum kein Verdikt
Die am 2026-08-12 registrierte Vorbedingung verlangte, dass die AnEn-Seite die archivierten GL-022-Summen `sum_crps_anen` je Zelle mit relativer Toleranz **1e-9** reproduziert. Ergebnis:

| Zelle | Summe CRPS AnEn (GL-022) | beobachtet | rel. Abw. | im Rahmen |
|---|---:|---:|---:|:---:|
| BTC W1 | 26,623978231 | 26,623978231 | 2,7e-16 | ja |
| BTC W2 | 12,442607196 | 12,442607196 | 2,9e-16 | ja |
| **ETH W1** | 29,212400403 | 29,212400292 | **3,8e-09** | **NEIN** |
| ETH W2 | 15,005176450 | 15,005176450 | 1,2e-16 | ja |

Drei von vier Zellen sind bit-identisch, eine verfehlt die Schranke um Faktor ~4. Die Registry ist an dieser Stelle eindeutig: `gate_valid=false` → **der Lauf traegt kein Urteil**. Es wird deshalb hier auch keines gefaellt.

### Ursachen-Diagnose (soweit belastbar)
- **Code ist ausgeschlossen.** Der gesamte AnEn-Lesepfad (`features.py`, `analog.py`, `baseline.py`, `payload_sql.py`) ist seit **2026-08-10 11:54 UTC** (Commit 03447cb) unveraendert — also seit VOR dem H-11-Lauf vom 2026-08-11 13:58 UTC. Der heutige Commit e586d35 hat ausschliesslich NEUE Dateien (`dressed.py`, `driver_c.py`) hinzugefuegt. Git-verifiziert.
- **Bleiben zwei Kandidaten:** (i) nicht-deterministische Float-Summation in der parallelen DuckDB-Aggregation (`sqrt(sum(r*r))` je Tag), (ii) der Harvest-Speicher hat sich zwischen den beiden Laeufen bewegt — er ist LIVE, der Collector laeuft durchgehend, und Backfill/Dedup/Kompaktierung duerfen historische Partitionen neu schreiben. Beide erzeugen genau die beobachtete Groessenordnung. Welcher von beiden es war, ist **nachtraeglich nicht mehr entscheidbar** — es existiert kein Fingerabdruck des Panels vom 2026-08-11. Genau diese Luecke wird geschlossen (s.u.).
- **Zweiter, unabhaengiger Kontinuitaets-Beleg:** derselbe Lauf rechnet die H-11-Groesse (CRPSS unter der alten Dirac-Regel) aus heutigen Daten nach: BTC W1 rel. 3,8e-16 · BTC W2 9,3e-16 · ETH W1 8,3e-09 · ETH W2 3,3e-10. Die H-11-Messung als Ganzes landet also weiterhin dort, wo sie am 2026-08-11 landete. **GL-022 steht unberuehrt.**

### Die Vorbedingung war der Fehler, nicht der Lauf
Bit-Identitaet gegen ein Archiv, das an einem ANDEREN Tag aus einem LEBENDEN Datenspeicher gezogen wurde, ist strukturell unerreichbar — nicht bei ungluecklichem Timing, sondern grundsaetzlich. Das ist ein Konstruktionsfehler des Orchestrators bei der H-11c-Registrierung vom selben Tag, aufgedeckt durch den Lauf. Korrektur per Nachtrag VOR dem urteilstragenden Lauf: siehe DEC-32 und `hypothesis_registry.md` H-11c Nachtrag 2. Kernpunkt: die neue Schranke (1e-4 relativ) ist aus der **Gate-Arithmetik** hergeleitet (eine relative Stoerung eps bewegt den CRPSS um hoechstens ~2·eps, also ≤2e-4 — das 250-Fache unter der 0,05-Schwelle), **nicht** aus der beobachteten Abweichung; die Beobachtung liegt vier Groessenordnungen darunter. Zusaetzlich wird ab sofort ein SHA-256-Fingerabdruck des Tagespanels mitgeschrieben, damit die Frage „hat sich der Schnappschuss bewegt?" beim naechsten Mal beantwortbar ist statt offen zu bleiben.

### Offenlegung: was der ungueltige Lauf zeigt (NICHT urteilstragend)
Damit niemand die Vorbedingungs-Korrektur fuer ergebnis-motiviert halten kann, wird das Beobachtete hier vollstaendig protokolliert — es ist unter jeder denkbaren Schranke dasselbe:

| Zelle | n | **CRPSS_dressed** | Schwelle | boot-p | Zelle |
|---|---:|---:|---:|---:|:---:|
| BTC W1 | 177 | **+0,0154** | 0,05 | 0,2917 | nein |
| BTC W2 | 96 | **−0,0305** | 0,05 | 0,7602 | nein |
| ETH W1 | 177 | **−0,0435** | 0,05 | 0,9401 | nein |
| ETH W2 | 96 | **−0,0594** | 0,05 | 0,9161 | nein |

**0 von 4 Zellen bestehen**, die beste liegt 0,0346 unter der Schwelle, die schlechteste 0,109 darunter; kein einziger p-Wert unter 0,29. Die 4-ppb-Unsicherheit der Vorbedingung ist rund sieben Groessenordnungen zu klein, um daran irgendetwas zu bewegen. Die registrierte A-priori „DROP erwartet" zeichnet sich klar ab — das Verdikt bleibt trotzdem bis zum gueltigen Lauf ausgesetzt (Muster GL-019).

Ebenfalls mitberichtet (registriert als nicht-urteilstragend): Der Punktprognose-Vergleich mit dem korrekten Funktional — MAE des Ensemble-**Medians** gegen HAR-MAE — ergibt BTC W1 +0,0027 · BTC W2 +0,0078 · ETH W1 −0,0089 · ETH W2 −0,0027 mit zweiseitigen p von 0,27–0,79: in allen vier Zellen ein statistisches Unentschieden, mit BTC leicht fuer und ETH leicht gegen das AnEn. Das bestaetigt beide Punkte aus GL-022 gleichzeitig: die urspruengliche Orchestrator-Tabelle (Ensemble-Mittel) war das falsche Funktional UND ihre Vorzeichen waren Rauschen. Dispersions-Verhaeltnisse: AnEn 0,97–1,26, Dressed-HAR 0,95–1,17 — beide Seiten ~kalibriert, wie in GL-022 E4 hergeleitet.

### Programm-Bilanz (nach GL-023)
Unveraendert gegenueber GL-022, plus: **H-11c Lauf 1 ohne Verdikt** (Vorbedingung verfehlt, Vorbedingung korrigiert, Wiederholungslauf ausstehend). **23 GL-Eintraege, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

---

## GL-024 · 2026-08-13 · H-11c · C-11 AnEn gegen dispersions-gematchte HAR (Dressed-HAR), Lauf 2 — **DROP (empirisch; 0 von 4 Zellen, kein p-Wert unter 0,29)**

**Quelle:** `state/h11c_20260813_101714/c11c_dressed_results.{json,md}` (Lauf 2026-08-13 10:17–11:04 UTC, 2.852 s, rc=0). `gate_valid=true`, Kontinuitaets-Vorbedingung nach Registry-Nachtrag 2 / DEC-32 **erfuellt**: maximale relative Abweichung 8,3e-09 (ETH W1, H-11-Groesse) gegen die Materialitaets-Schranke 1e-4 — vier Groessenordnungen Reserve. Entsperr-Check gruen (`manifest_done_days`).

### Registriertes Gate (wörtlich) und Messergebnis

Gate: „WEITER, wenn fuer mindestens ein Symbol in {BTC,ETH} in BEIDEN Fenstern: CRPSS_dressed = 1 - Summe(CRPS_AnEn)/Summe(CRPS_DressedHAR) >= 0,05 UND Block-Bootstrap-p <= 0,05 nach BH-FDR alpha=0,10 ueber F-ANEN-C." · DROP: hartes Ein-Fenster-Kriterium, „Kein Graubereich."

| Zelle | n | CRPS AnEn | CRPS Dressed-HAR | **CRPSS_dressed** | >=0,05 | Bootstrap-p | <=0,05 | Zelle |
|---|---:|---:|---:|---:|:---:|---:|:---:|:---:|
| BTC W1 | 177 | 0,15042 | 0,15277 | **+0,0154** | nein | 0,2917 | nein | **nein** |
| BTC W2 | 96 | 0,12961 | 0,12578 | **−0,0305** | nein | 0,7602 | nein | **nein** |
| ETH W1 | 177 | 0,16504 | 0,15816 | **−0,0435** | nein | 0,9401 | nein | **nein** |
| ETH W2 | 96 | 0,15630 | 0,14755 | **−0,0594** | nein | 0,9161 | nein | **nein** |

F-ANEN-C: 4 Zellen, BH-FDR alpha=0,10 → `n_fdr_significant=0`, `p_crit=0`. `any_symbol_both_windows_pass=false`; beide Symbole 0 von 2 Fenstern. Die registrierte A-priori „DROP erwartet" ist bestaetigt.

### URTEIL: **DROP.**
Kein Symbol besteht ein einziges Fenster — weder die CRPSS-Schwelle noch die Bootstrap-Bedingung, in keiner Zelle. Die beste Zelle liegt 0,035 unter der Schwelle, drei von vier sind negativ (das AnEn ist dort SCHLECHTER als eine informationsfrei gedresste HAR), und der kleinste p-Wert ist 0,29. Das harte Ein-Fenster-Kriterium greift zweifach. **Sobald die HAR-Baseline dieselbe Verteilungs-Geometrie erhaelt wie das AnEn, verschwindet der gesamte in H-11 gemessene Vorsprung.**

### Der strukturelle Geschenk-Term, jetzt empirisch gemessen
Derselbe Lauf bewertet die HAR zusaetzlich unter der alten Dirac-Regel. Die Differenz ist der Betrag, den reines Dressing ohne jede Zusatzinformation einbringt:

| Zelle | CRPS HAR als Dirac | CRPS HAR gedresst | **Geschenk allein durch Dressing** | CRPSS unter alter Regel (= H-11) |
|---|---:|---:|---:|---:|
| BTC W1 | 0,21238 | 0,15277 | **28,1 %** | 0,2917 |
| BTC W2 | 0,17056 | 0,12578 | **26,3 %** | 0,2401 |
| ETH W1 | 0,21934 | 0,15816 | **27,9 %** | 0,2475 |
| ETH W2 | 0,21164 | 0,14755 | **30,3 %** | 0,2615 |

GL-022 hatte diesen Term theoretisch auf 0,21–0,29 veranschlagt (Laplace bis Gauss k→∞). Gemessen: **26,3–30,3 %** — die Vorhersage trifft, und in jeder einzelnen Zelle ist das Geschenk **groesser** als der unter der alten Regel gemessene „Vorsprung". Damit ist Etikett E1/E2/E6 aus GL-022 nicht mehr Argument, sondern Befund.

### Pflicht-Diagnostik (vorab als NICHT urteilstragend registriert)
| Zelle | MAE AnEn-Median | MAE HAR-Punkt | Diff (HAR−Median) | 2-seitig p | Disp. AnEn | Disp. Dressed | PIT χ² AnEn (p) |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTC W1 | 0,20970 | 0,21238 | +0,00267 | 0,717 | 0,987 | 0,988 | 23,9 (0,248) |
| BTC W2 | 0,16278 | 0,17056 | +0,00777 | 0,433 | 1,257 | 1,173 | 35,7 (0,017) |
| ETH W1 | 0,22820 | 0,21934 | −0,00887 | 0,269 | 0,973 | 0,951 | 20,8 (0,410) |
| ETH W2 | 0,21430 | 0,21164 | −0,00267 | 0,794 | 1,090 | 1,136 | 31,3 (0,051) |

Der Punktprognose-Vergleich mit dem **korrekten Funktional** (Median, nicht Mittel — die in GL-022 offengelegte Luecke) ist in allen vier Zellen ein statistisches Unentschieden: BTC leicht fuer, ETH leicht gegen das AnEn, kein p unter 0,27. Das bestaetigt beide Haelften der GL-022-Korrektur gleichzeitig: die urspruengliche Orchestrator-Tabelle nutzte das falsche Funktional UND ihre Vorzeichen waren Rauschen. Dispersions-Verhaeltnisse 0,95–1,26 auf beiden Seiten — beide Ensembles sind naeherungsweise kalibriert, „Hedging-Blaehung" liegt nicht vor (GL-022 E4 bestaetigt).

### Nachtrag zu GL-023: die offene Ursachenfrage ist beantwortet
Lauf 2 reproduziert Lauf 1 **bit-identisch** in allen vier Zellen (`sum_crps_anen` Delta 0, CRPSS-Delta <=2,2e-16) — inklusive der Zelle ETH W1, die ihren eigenen Wert 29,212400292 exakt wiederholt statt des GL-022-Werts 29,212400403. Damit ist Kandidat (i) aus GL-023 — nicht-deterministische Float-Summation in der parallelen DuckDB-Aggregation — **ausgeschlossen**: die Pipeline ist ueber Laeufe hinweg deterministisch. Es bleibt Kandidat (ii): der LEBENDE Harvest-Speicher hat sich zwischen dem H-11-Lauf (2026-08-11 13:58 UTC) und dem ersten H-11c-Lauf (2026-08-12 16:13 UTC) in der ETH-Historie bewegt und ist seither stabil. Die ab GL-023 mitgeschriebenen Panel-Fingerabdruecke belegen das kuenftig direkt (Lauf 2, 829 Tage 2024-03-27..2026-07-03: BTC `d0b7f1a00066e97e…`, ETH `98068d794b7e7bd1…`).

### Folgen (verbindlich)
1. **GL-022 bleibt unveraendert** (append-only). H-11 hat sein registriertes Gate bestanden; das wird nicht rueckwirkend kassiert. Aber die dort angehaengten Etiketten sind ab jetzt empirisch belegt statt theoretisch begruendet.
2. **Jede Zitierung von H-11 muss GL-024 mitfuehren.** Die Formulierung „das AnEn prognostiziert Vol-Regime besser als HAR" ist von den eigenen Payloads NICHT gedeckt und darf im Programm nicht verwendet werden. Korrekt ist: „das AnEn liefert eine annaehernd kalibrierte Verteilung; einen Prognose-Vorsprung gegenueber einer gleich breit gedressten HAR hat es nicht."
3. **H-11b (Monetarisierung) ist a fortiori tot** und wird nicht registriert: eine Tradability-Hypothese auf einem Mess-Vorsprung, den es nicht gibt, ist gegenstandslos. Die „~25–75x ueber der Wand"-Notiz bleibt entkoppelt (GL-022 E5) und traegt nichts.
4. **Die C-11-Linie (Analog-Ensemble-Vol-Prognose) ist als Quelle eines Prognose-Vorsprungs geschlossen.** Siehe DEC-33.

### Programm-Bilanz (nach GL-024)
Welle 1–3 unveraendert. Welle 4: H-09/H-10/H-12 DROP · H-11 WEITER kapitalfrei mit Etiketten (GL-022) · **H-11c DROP (GL-024)** · H-13 gesperrt. Welle 5: H-18 Audit (GL-014) · H-16 WEITER kapitalfrei (GL-015 + Nachtrag) · H-17 Verdikt ausstehend (GL-019) · H-14 methodisch invalide (GL-020) · H-15 WEITER kapitalfrei (GL-021). **24 GL-Eintraege, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

> **Nachtrag zu GL-024 · 2026-08-13 (append-only, KORREKTUR einer Orchestrator-Fehlaussage; Verdikt UNVERAENDERT):**
>
> Ein dritter, unmittelbar an Lauf 2 angehaengter Lauf (`state/h11c_20260813_112523/`, 2026-08-13 11:25–12:16 UTC, rc=0, `gate_valid=true`) **widerlegt die Ursachen-Aussage im GL-024-Abschnitt „Nachtrag zu GL-023"**. Dort stand: „DuckDB-Nichtdeterminismus ist ausgeschlossen; der lebende Harvest-Speicher hat sich zwischen 2026-08-11 und 2026-08-12 in der ETH-Historie bewegt." **Das ist falsch.** Richtig ist das Gegenteil: die Daten haben sich nie bewegt, die Aggregation ist nicht-deterministisch.
>
> Beleg — drei Laeufe, identischer Code (git-verifiziert), identischer Datenstand:
>
> | Zelle | Lauf 1 (08-12) | Lauf 2 (08-13 10:17) | Lauf 3 (08-13 11:25) | Spanne | rel. |
> |---|---:|---:|---:|---:|---:|
> | BTC W1 | 26,623978231118 | 26,623978231118 | 26,623978231118 | 3,6e-15 | 1,3e-16 |
> | BTC W2 | 12,442607195621 | 12,442607195621 | 12,442607195621 | 5,3e-15 | 4,3e-16 |
> | **ETH W1** | 29,2124002916 | 29,2124002916 | **29,2124004029** | **1,1e-07** | **3,8e-09** |
> | ETH W2 | 15,005176449560 | 15,005176449560 | 15,005176449560 | 0 | 0 |
>
> Der entscheidende Punkt: **Lauf 3 trifft in ETH W1 exakt den archivierten GL-022-Wert 29,2124004029.** Die Aggregation hat also (mindestens) zwei diskrete Ergebnisse, und der H-11-Lauf vom 2026-08-11 lag schlicht auf dem anderen. Zusaetzlich weichen die neu eingefuehrten Panel-rv-Fingerabdruecke zwischen Lauf 2 und Lauf 3 **fuer beide Symbole** ab (BTC `d0b7f1a0…` vs `ce5cd2bd…`, ETH `98068d79…` vs `47fa76fc…`), waehrend die Funding-Fingerabdruecke identisch bleiben — die Nichtdeterminismus-Quelle sitzt im Trade-/RV-Pfad, nicht im Funding-Pfad. Der Fingerabdruck war zwei Stunden alt und hat den Fehler des Orchestrators sofort gefunden; genau dafuer wurde er eingebaut.
>
> **Mechanismus (zwei Kandidaten, nicht isoliert):** (a) Assoziativitaets-Verlust bei der parallelen Float-Summation von `sum(r*r)` — erklaert die 1e-16-Ebene bei BTC zwanglos, aber nicht die 1,1e-7 bei ETH W1; (b) ein **nicht eindeutiger Tie-Break in `max_by(price, ts_exchange_ms)`** bei der Minutenbar-Bildung: zwei Trades derselben Minute mit identischem `ts_exchange_ms`, aber verschiedenem Preis — dann haengt der Bar-Schlusskurs von der Scan-Reihenfolge ab, zwei 1-Minuten-Renditen aendern sich um echte Tick-Betraege, und die Groessenordnung 1e-7 auf der Zellsumme passt. (b) ist die wahrscheinlichere Erklaerung fuer die ETH-W1-Zelle; belastbar isoliert ist sie nicht. **Betroffen sind vier Loader** (`c11_anen/features.py`, `c12_frag/panel.py`, `c14_panellag/panel.py`, `c10_pointer/loaders.py`) — der Befund ist also programmweit, nicht c11-spezifisch. Konsequenz: DEC-34.
>
> **Was sich NICHT aendert:** Das Verdikt **DROP** steht unveraendert. Ueber alle drei Laeufe schwankt der CRPSS_dressed um hoechstens **1,5e-09** (BTC W1 +0,0154103 · BTC W2 −0,0304856 · ETH W1 −0,0435116 · ETH W2 −0,0593609), die Bootstrap-p-Werte sind auf vier Stellen identisch (0,2917 / 0,7602 / 0,9401 / 0,9161), `n_fdr_significant=0` und `any_symbol_both_windows_pass=false` in allen drei Laeufen. Die Messunsicherheit ist rund **sieben Groessenordnungen** kleiner als der Abstand der besten Zelle zur Schwelle (0,0346). Auch GL-022 ist unberuehrt: die H-11-Groesse schwankt in derselben Groessenordnung.
>
> **Was sich damit BESTAETIGT:** DEC-32 war sachlich richtig, aber aus dem falschen Grund begruendet. Die dortige Materialitaets-Schranke ist jetzt nicht mehr nur aus der Gate-Arithmetik hergeleitet, sondern hat einen **gemessenen Rausch-Boden**: maximale relative Lauf-zu-Lauf-Streuung 3,8e-09 gegen die Schranke 1e-4 — vier Groessenordnungen Reserve. Die urspruengliche 1e-9-Vorbedingung war nicht wegen eines lebenden Speichers unerreichbar, sondern weil sie **unter dem Rauschboden der eigenen Pipeline** lag. Das Verbot von Bit-Identitaets-Vorbedingungen (DEC-32, Prozess-Lehre) gilt damit erst recht.

---

## GL-025 · 2026-08-17 · H-19 · C-19 DRIFT: Stationaritaet der Tape-Struktur (Welle 6, META/AUDIT, KAPITALFREI) — **BEFUND: STATIONAER-GENUG (0 von 15 Zellen; KEINE Regime-Splitting-Auflage)**

**Quelle:** `state/h19_20260817/c19_drift_results.{json,md}` (Lauf 2026-08-17 08:26–08:35 UTC, 527 s, rc=0). **Datenbindung einwandfrei:** alle fuenf registrierten WP-0-Cache-Fingerabdruecke bit-genau bestaetigt (`gate_valid=true`) — der erste Welle-6-Lauf unter dem neuen Determinismus-Regime, und die Vorbedingungs-Maschinerie hat exakt wie entworfen funktioniert.

### Registrierte Befund-Regel und Ergebnis

Regel (Registry H-19, magnitudengetrieben): DRIFT-BEFUND je Deskriptor×Symbol, wenn |rho_p| >= 0,30 in BEIDEN OOS-Fenstern mit GLEICHEM Vorzeichen (partieller Spearman gegen den Tagesindex, konditioniert auf log-RV und log-Volumen).

**Ergebnis: 0 von 15 Zellen erfuellen die Befund-Regel.** Kein Deskriptor zeigt in beiden Fenstern gleichgerichteten materiellen Drift; die Rotations-Null-p (nicht urteilstragend) sind nach BH-FDR alpha=0,10 ueber F-DRIFT in 0 von 30 OOS-Zellen signifikant.

| Symbol | D1 lag1-AC (OOS1/OOS2) | D2 Varianz-Signatur | D3 Herfindahl |
|---|---|---|---|
| BTC | −0,08 / +0,08 | −0,10 / +0,25 | **−0,33** / +0,06 |
| ETH | −0,09 / −0,09 | −0,07 / −0,04 | **−0,47** / +0,02 |
| XRP | −0,13 / +0,08 | −0,18 / +0,14 | −0,05 / −0,16 |
| SOL | −0,06 / −0,05 | −0,21 / −0,04 | **−0,49** / +0,09 |
| BNB | −0,15 / +0,05 | −0,18 / +0,06 | −0,29 / −0,09 |

### BEFUND (bindend fuer Welle 6): **STATIONAER-GENUG — die Regime-Splitting-Auflage wird NICHT ausgeloest.**
H-20/H-21/H-22 duerfen ihre Mehrjahres-Fenster ungesplittet auswerten; die vorregistrierte Konsequenzregel ist leer gelaufen.

### Deskriptive Beobachtung (ausdruecklich KEIN Befund, ehrlich protokolliert)
D3 (Aktivitaets-Konzentration) zeigt ein klares **abgeschlossenes Uebergangsmuster statt eines laufenden Drifts**: in L (2021–2022) POSITIV (+0,36..+0,49 bei XRP/SOL/BNB), in OOS-1 (2023–2024H1) stark NEGATIV (BTC −0,33, ETH −0,47, SOL −0,49), in OOS-2 (2024H2–2025) ueberall nahe null. Lesart: Die Klumpung der Handelsaktivitaet stieg bis ~2022, fiel bis Mitte 2024 (Dekonzentration — konsistent mit Marktreifung/mehr kontinuierlichem Flow) und ist seither stabil. Genau diese Signatur — Vorzeichenwechsel zwischen den Fenstern — ist es, wofuer die Beide-Fenster-gleiches-Vorzeichen-Regel gebaut wurde: ein einmaliger Struktur-Uebergang ist KEIN fortlaufender Kalender-Drift. Bemerkenswert auch: selbst die −0,49-Zelle ist unter der Rotations-Null NICHT signifikant — die hohe Persistenz von D3 erzeugt unter der Null haeufig grosse Schein-|rho| gegen die Zeit, und die registrierte Null (zirkulaerer Shift, erhaelt die Autokorrelation) preist das korrekt ein. Ein naiver iid-Permutationstest haette hier falsch-positiv „Drift" gerufen.

### Programm-Bilanz (nach GL-025)
Welle 1–5 unveraendert (GL-022/023/024 inkl. H-11c DROP). Welle 6: **H-19 STATIONAER-GENUG (GL-025, META/AUDIT)** · H-20 registriert, Lauf ausstehend · H-21 GESPERRT bis Fensterschluss 2026-12-27 · H-22 registriert, wartet auf WP-2. **25 GL-Eintraege, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

---

## GL-026 · 2026-08-17 · H-20 · C-20 TAIL-AFTERMATH: Nachbewegung nach 3,5-σ-Stunden (Welle 6, KAPITALFREI) — **DROP (empirisch; beide OOS-Fenster verfehlen das Gate, Ein-Fenster-Kriterium greift zweifach)**

**Quelle:** `state/h20_20260817/c20_tail_results.{json,md}` (Lauf 2026-08-17 09:08 UTC, 95 s, rc=0). Datenbindung einwandfrei: alle fuenf Cache-Fingerabdruecke bestaetigt (`gate_valid=true`). **Verdikt-Auswertbarkeit gegeben:** N-Floor (>=100 Event-Tage je Fenster) mit 403 (OOS-1) und 362 (OOS-2) Event-Tagen komfortabel erfuellt; 0 Events wegen Datenqualitaet verworfen. Die Feasibility-Schaetzung der Registrierung (300–650 Events/Fenster) wurde mit 1.044/962 sogar uebertroffen — die Ereignis-Maschinerie hat funktioniert.

### Registriertes Gate (wörtlich) und Messergebnis

Gate: „WEITER, wenn in BEIDEN OOS-Fenstern gepoolt: mean(y) >= +10 bp UND Cluster-Bootstrap-p <= 0,05 nach BH-FDR alpha=0,10 ueber F-TAIL (2 Zellen). DROP: hartes Ein-Fenster-Kriterium. Kein Graubereich."

| Fenster | urteilstragend | Events | Event-Tage | mean y | median y | >= +10 bp | Cluster-p | <= 0,05 | Zelle |
|---|:---:|---:|---:|---:|---:|:---:|---:|:---:|:---:|
| L (deskriptiv) | nein | 889 | 362 | **−40,5 bp** | −6,5 bp | — | 0,9311 | — | — |
| OOS-1 | ja | 1.044 | 403 | **+4,8 bp** | +14,2 bp | **nein** | 0,3976 | **nein** | **nein** |
| OOS-2 | ja | 962 | 362 | **+17,3 bp** | +20,2 bp | ja | 0,1728 | **nein** | **nein** |

F-TAIL: `n_fdr_significant=0`, `p_crit=0`.

### URTEIL: **DROP.**
OOS-1 verfehlt BEIDE Bedingungen (Mittel unter dem Boden, p weit ueber der Schwelle); OOS-2 erreicht zwar den +10-bp-Boden, aber p=0,17 ist dreieinhalbfach ueber der Schwelle. Das harte Ein-Fenster-Kriterium greift damit zweifach. Kein Graubereich registriert, keiner anwendbar.

### Ehrliche Einordnung des Musters
1. **Die Punktschaetzer sind in beiden OOS-Fenstern positiv** (Mittel +5/+17 bp, Mediane +14/+20 bp) — die Reversions-Richtung ist als Tendenz sichtbar, traegt aber keine Signifikanz: die tages-geclusterte Streuung der Nachbewegungen ist zu gross (~12–13 bp Standardfehler des gepoolten Mittels).
2. **Das Vorzeichen ist ueber Symbole und Fenster instabil:** BTC −16 → +36, SOL −49 → +46, ETH +32 → −12, XRP +15 → −21 bp. Kein Symbol traegt den Effekt konsistent — das gepoolte Plus ist ein Durchschnitt wechselnder Vorzeichen, kein gemeinsames Phaenomen.
3. **Das deskriptive L-Fenster (2021–2022) zeigt das GEGENTEIL:** −40,5 bp — nach Schocks dominierte dort FORTSETZUNG. Zusammen mit GL-025 (D3-Uebergang endet ~Mitte 2024) ergibt sich ein konsistentes Bild: das Nach-Schock-Verhalten ist selbst regime-abhaengig und hat in keiner Aera die registrierte Staerke.
4. **Die oekonomische 25–50-bp-Erwartung der Synthese ist nicht bestaetigt** — die gemessenen +5/+17 bp laegen selbst bei Signifikanz unter bzw. knapp ueber der 15-bps-Wand. Die Notiz war nicht-bindend und faellt mit dem DROP ersatzlos.

**Abgrenzung (vorab registriert, bleibt bindend):** Keine Sigma-/Horizont-/Luecken-Nachsuche. Eine konditionierte Neufassung (z. B. nur Crash-Events, nur High-Vol-Regime, anderer Horizont) waere eine NEUE Hypothese mit eigener Vorregistrierung und muesste die hier dokumentierte Vorzeichen-Instabilitaet als A-priori-Gegenevidenz zitieren.

### Programm-Bilanz (nach GL-026)
Welle 6: H-19 STATIONAER-GENUG (GL-025) · **H-20 DROP (GL-026)** · H-21 GESPERRT bis 2026-12-27 · H-22 registriert, wartet auf WP-2. **26 GL-Eintraege, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

---

## GL-027 · 2026-08-18 · H-22 · C-22 L2-TILT: Tages-Buchneigung → Folgetags-Rendite (Welle 6, KAPITALFREI) — **DROP (empirisch; beide BTC-Fenster verfehlen das Gate; die registrierte A-priori „DROP erwartet" ist bestaetigt)**

**Quelle:** `state/h22_20260818/c22_l2tilt_results.{json,md}` (Lauf 2026-08-18 07:56 UTC, 27 s, rc=0). **Datenbindung einwandfrei:** alle FUENF registrierten Fingerabdruecke bit-genau bestaetigt (3 WP-2-Tilt-Fenster + 2 WP-0-Bar-Symbole, `gate_valid=true`); der 85-%-Abdeckungs-Floor in beiden urteilstragenden Fenstern erfuellt (99,2 % / 93,2 %).

### Registriertes Gate (wörtlich) und Messergebnis

Gate: „WEITER, wenn BTC in BEIDEN L2-Fenstern: IC >= 0,10 UND Bootstrap-p <= 0,05 nach BH-FDR alpha=0,10 ueber F-L2 (2 Zellen). DROP: hartes Ein-Fenster-Kriterium. Kein Graubereich."

| Symbol | Fenster | urteilstragend | Paare | Abdeckung | **IC** | >= 0,10 | boot-p | <= 0,05 | Zelle |
|---|---|:---:|---:|---:|---:|:---:|---:|:---:|:---:|
| BTC | W-L2-1 (2023-07..2024-06) | ja | 363 | 99,2 % | **+0,0665** | nein | 0,0969 | nein | **nein** |
| BTC | W-L2-2 (2024-07..2025-06) | ja | 340 | 93,2 % | **−0,0112** | nein | 0,5704 | nein | **nein** |
| ETH | W-ETH (2023-04..2024-04, Bericht) | nein | 395 | 99,8 % | +0,0618 | nein | 0,1059 | — | — |

F-L2: `n_fdr_significant=0`, `p_crit=0`.

### URTEIL: **DROP.**
Beide BTC-Fenster verfehlen beide Bedingungen; das harte Ein-Fenster-Kriterium greift zweifach. Die von Lane C woertlich registrierte A-priori — „DROP erwartet: ±5-bp-Buchtiefe gegen einen 1-Tages-Horizont widerspricht der Zerfallsstruktur" — ist bestaetigt. Zum ersten Mal in Welle 6 stimmen A-priori und Verdikt ueberein.

### Ehrliche Einordnung
1. **Der 2023/24-Aera-IC ist nicht null, aber unterhalb jeder registrierten Relevanz:** BTC W-L2-1 (+0,067) und das nicht urteilstragende ETH-Fenster (+0,062) — zwei ueberlappende Zeitraeume, zwei Symbole, dasselbe schwach positive Signal knapp ueber dem reinen Rauschboden (1/sqrt(363) ≈ 0,052) und klar unter der Schwelle 0,10, die die Registrierung aus genau diesem Rauschboden kalibriert hat. In W-L2-2 (2024/25) ist auch das verschwunden (−0,011). Dieselbe Aera-Abhaengigkeit wie bei H-20 — was immer da war, ist duenn und nicht persistent.
2. **Die oekonomische 1,7–2x-Notiz** der Synthese (25–30 bps entspraeche |IC| ~ 0,1) ist nicht erreicht und faellt mit dem DROP ersatzlos; sie war entkoppelt registriert.
3. **Die WP-2-Maschinerie hat sich bewaehrt:** Snapshot-validierte Buchrekonstruktion ueber 1.098 Fenster-Tage, 0 verworfene Tage, 96 Sequenzbrueche gesamt (~1/11 Tage), fuenffache Fingerprint-Bindung — der Lauf selbst dauerte 27 Sekunden. Die Infrastruktur steht fuer jede kuenftige L2-Hypothese (SWEEP-PRE aus der Vertagt-Liste waere jetzt billig).

**Abgrenzung (registriert, bindend):** Keine Band-/Sampling-/Aggregat-Nachsuche. Ein Intraday-Horizont (der zur Zerfallsstruktur passen wuerde) waere eine NEUE Hypothese mit eigener Registrierung.

### Programm-Bilanz (nach GL-027)
Welle 6: H-19 STATIONAER-GENUG (GL-025) · H-20 DROP (GL-026) · **H-22 DROP (GL-027)** · H-21 GESPERRT bis 2026-12-27. Damit ist Welle 6 bis auf H-21 vollstaendig adjudiziert. **27 GL-Eintraege, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

---

## GL-028 · 2026-08-18 · H-24 · C-24 Minuten-Fluss-Lead (Welle 7, KAPITALFREI) — **DROP (empirisch; IC30 in BEIDEN Rezenz-Fenstern NEGATIV, p am Ceiling)**

**Quelle:** `state/h24_20260818/c24_impact_results.{json,md}` (Lauf 2026-08-18 14:36 UTC, 200 s, rc=0; ein zweiter Lauf am 2026-08-19 reproduziert **bit-identisch**). Alle fuenf WP-0-Fingerabdruecke bestaetigt (`gate_valid=true`).

### Vorbedingungen: beide erfuellt
- **Positivkontrolle (bindend, GL-020-Muster):** gleichzeitiger IC **+0,5376 / +0,5265** in den Rezenz-Fenstern — das **5,3-Fache** des registrierten Floors 0,10, und ueber alle zehn Halbjahre stabil zwischen +0,53 und +0,61. Die Messmaschinerie sieht den Impact ueberdeutlich; ihr Null-Befund auf dem Forward-Horizont ist damit informativ (anders als GL-020, wo genau das scheiterte).
- **Tages-Floor:** 184 bzw. 181 Tage je Fenster gegen Floor 100. `verdict_evaluable=true`.

### Registriertes Gate und Messergebnis

Gate: „WEITER, wenn in BEIDEN Rezenz-Fenstern gepoolt: mean(IC_P30) >= 0,02 UND Cluster-Bootstrap-p <= 0,05 nach BH-FDR alpha=0,10 ueber F-IMP. DROP: hartes Ein-Fenster-Kriterium."

| Fenster | Symbol-Tage | mean IC30 | median | >= +0,02 | Lesart | boot-p | Zelle |
|---|---:|---:|---:|:---:|---|---:|:---:|
| W-R1 (2025-08..2026-01) | 920 | **−0,0179** | −0,0186 | nein | permanent | 1,0000 | **nein** |
| W-R2 (2026-02..2026-07) | 905 | **−0,0169** | −0,0165 | nein | permanent | 1,0000 | **nein** |

Beide Fenster verfehlen beide Bedingungen — das Vorzeichen ist sogar entgegengesetzt zur Hypothese. `n_fdr_significant=0`. Der p-Wert 1,0000 ist der Deckelwert des einseitigen Tests (H0: Mittel <= 0) bei negativem beobachtetem Mittel.

### URTEIL: **DROP.**
Das harte Ein-Fenster-Kriterium greift zweifach. Die registrierte A-priori („DROP leicht favorisiert, ~60/40; die Mikrostruktur-Literatur findet Minuten-Impact ueberwiegend transient") ist bestaetigt. **Der Minuten-Nettofluss kuendigt KEINE weitere gleichgerichtete Bewegung an.**

### Der eigentliche Befund: ein ueber FUENF JAHRE stabiler stilisierter Fakt

| Halbjahr | 21H2 | 22H1 | 22H2 | 23H1 | 23H2 | 24H1 | 24H2 | 25H1 | **25H2** | **26H1** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IC gleichzeitig | +0,53 | +0,58 | +0,59 | +0,58 | +0,61 | +0,59 | +0,57 | +0,56 | **+0,54** | **+0,53** |
| IC30 | −0,012 | −0,011 | −0,017 | −0,019 | −0,022 | −0,022 | −0,019 | −0,018 | **−0,018** | **−0,017** |

Zehn Halbjahre, fuenf Symbole gepoolt, 2021–2026: der gleichzeitige Impact liegt konstant bei ~+0,57, der Forward-IC konstant bei ~−0,017. **Das ist die erste Groesse im gesamten Programm, die ueber alle Aeren stabil ist.** Welle 6 fand durchweg Aera-Abhaengigkeit (GL-025 D3-Uebergang, GL-026 Vorzeichenwechsel, GL-027 IC nur 2023/24); H-24 findet das Gegenteil — eine Konstante. Die `impact_reading`-Klassifikation (DEC-39, nicht urteilstragend) lautet in 8 von 10 Halbjahren `permanent`, in 2 (23H2, 24H1) `reversal`, beide direkt an der −0,02-Grenze. Lesart: **Der Minuten-Impact ist ganz ueberwiegend PERMANENT mit einer kleinen transienten Komponente** — er bleibt im Preis, aber er fuehrt nichts nach.

Die mitberichteten Horizonte schliessen die „falscher Horizont"-Ausrede vorab aus: IC5 = −0,021/−0,024 und IC120 = −0,014/−0,016 in den Rezenz-Fenstern — dasselbe Bild auf 5 und 120 Minuten. Kein Horizont rettet die Hypothese.

**Ehrlicher Interpretations-Vorbehalt (wichtig, nicht wegzulassen):** Die kleine negative Zahl ist NICHT zwingend Liquiditaets-Reversion. Bei starkem Kaufdruck liegt der Minuten-Schlusskurs mechanisch eher auf der Angebotsseite des Spreads; die Rueckkehr zur Mitte erzeugt allein daraus einen leicht negativen Forward-IC. Die Groessenordnung (−0,017 Rang-Korrelation) ist mit einem solchen Halb-Spread-Effekt gut vereinbar. Zu behaupten, hier sei echte Reversion gemessen, waere eine Ueberinterpretation — und sie ist fuer das Verdikt auch gleichgueltig: unter beiden Lesarten ist das Gate verfehlt.

### Abgrenzung (registriert, bindend)
Keine Horizont-/Flussdefinitions-Nachsuche. Zitierpflicht GL-007/GL-010: H-05 testete Tick-OFI-Vorzeichen auf Tick-Skala (DROP, inverse Mess-Existenz, Kapital-PARK); H-24 hat die Forward-Lead-Struktur des Minuten-Aggregatflusses gemessen. **Kein H-24-Ergebnis rehabilitiert C-01 oder dessen Tradability** — im Gegenteil, der Befund verengt den Raum: der Aggregatfluss traegt auf Minutenskala keine Vorlauf-Information.

### Programm-Bilanz (nach GL-028)
Welle 6 abgeschlossen bis auf H-21 (gesperrt bis 2026-12-27). Welle 7: **H-24 DROP (GL-028)** · H-23 registriert, Code (Voll-Inferenz) ausstehend. **28 GL-Eintraege, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

---

## GL-029 · 2026-08-19 · H-23 · C-17-Wiederholung mit Voll-Distanzserie, Lauf 1 (Welle 7, KAPITALFREI, GPU) — **KEIN VERDIKT (Redundanz-Referenz nicht uebergeben — Runner-Bedienfehler des Orchestrators, nicht Methode oder Daten)**

**Quelle:** `state/h23_20260819_nogate/c23_venue_full_results.{json,md}` (Lauf 2026-08-19 12:32–16:47 UTC, 15.272 s, rc=0). `verdict_bearing=true`, `blocked_reasons=[]` — echtes CUDA, Batch >= 2048, 10.000 Steps.

### Was funktioniert hat (alles Registrierte)
- **Die Voll-Distanzserie steht:** `distance_scope="full_panel"`, **100 Tage** statt der 2 aus GL-019. Je Fold wurden 55.831–57.600 Fenster eingebettet statt nur ~12.000 Test-Fenster. Genau der Zweck der Hypothese ist erreicht.
- **Die Checkpoint-Abgrenzung (Nachtrag (2)) hat exakt gegriffen:** die 100 Null-Retrainings RESUMTEN aus den H-17-Checkpoints (im Log je Fold nachlesbar), nur die 5 Haupt-Trainings liefen neu. Kosten: 4,2 h statt der ~35 h eines Vollaufs.
- **Der Mess-Befund repliziert GL-019 unabhaengig** — mit frisch trainierten Encodern, also stochastisch neuen Laeufen:

| Fold | GL-019 (2026-07) | H-23 Lauf 1 | p |
|---|---:|---:|---:|
| BTC | 0,9424 | 0,9312 | 0,0476 |
| ETH | 0,9950 | 0,9773 | 0,0476 |
| SOL | 0,9679 | 0,9531 | 0,0476 |
| BNB | 0,7130 | 0,7603 | 0,0952 |
| XRP | 0,8535 | 0,8370 | 0,0476 |
| **Pooled** | **0,8944** | **0,8914** | — |

5/5 Folds bestanden, Pooled 0,8914 gegen die registrierte 0,55-Schwelle. Der symbol-invariante Venue-Fingerprint ist damit ueber zwei unabhaengige Trainings-Kohorten stabil — das war in GL-019 nicht belegbar und ist ein echter Zugewinn.

### Warum trotzdem kein Verdikt
`c12_payload_present: false` → `n_overlap_days: 0` → `evaluable: false` → `redundant: false`, `passed: false` → `weiter_indication=false`. Die **registrierte Redundanz-Referenz** (`state/wave4_20260726/c12_frag_results.json`) wurde dem Lauf nie uebergeben: Der H-23-Runner hatte den Default aus `run_h17.ps1` geerbt, wo der Pfad per `$env:C12_RESULTS_JSON` manuell zu setzen war. **Das ist ein Bedienfehler im Runner des Orchestrators** — nicht Datenlage, nicht Methode, nicht Compute. Der registrierte Eintrag benennt die Referenzdatei woertlich; der Runner haette sie verdrahten muessen.

Die registrierten WEITER-Bedingungen verlangen das BESTEHEN des Non-Redundanz-Gates. Es kann nicht bestehen, was nicht auswertbar ist — **dieselbe formale Lage wie GL-019, aber aus einem trivial behebbaren Grund.** Ein WEITER allein auf dem Mess-Befund waere die Torpfosten-Verschiebung, die GL-019 bereits verweigert hat.

### Behebung (bereits umgesetzt, Kosten: Minuten)
`run_h23.ps1` verdrahtet die registrierte Referenz jetzt als Default und **bricht LAUT ab**, wenn sie fehlt (`rc=2`, SKIP) — statt eine nicht-adjudizierbare GPU-Nacht zu verbrennen. Der Wiederholungslauf ist billig, weil das `c12_payload` NICHT in den Run-Fingerabdruck eingeht (es ist ein Nach-Trainings-Vergleich, kein Trainings-Parameter): alle 105 Trainings resumen aus den Checkpoints — die 5 Haupt-Trainings jetzt aus den in diesem Lauf geschriebenen `main_full`-Checkpoints —, und nur das Redundanz-Gate wird neu gerechnet.

### Prozess-Lehre
Ein Runner, dessen Lauf ohne einen optionalen Parameter **strukturell nicht adjudizierbar** ist, darf diesen Parameter nicht optional lassen. Die Regel gilt ab sofort fuer alle Runner: **Was die Registrierung als Referenz oder Vorbedingung BENENNT, prueft der Runner VOR dem Start und bricht sonst laut ab.** (Verwandt mit der Loud-Fail-Doktrin aus GL-018 und dem Fingerprint-Guard aus DEC-34 — dort geht es um falsche Daten, hier um fehlende.)

### Programm-Bilanz (nach GL-029)
Welle 7: H-24 DROP (GL-028) · **H-23 Lauf 1 ohne Verdikt (GL-029), Wiederholung ausstehend**. H-21 gesperrt bis 2026-12-27. **29 GL-Eintraege, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**
