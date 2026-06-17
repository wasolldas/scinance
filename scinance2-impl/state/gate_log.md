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
