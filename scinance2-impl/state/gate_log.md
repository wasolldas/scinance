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
