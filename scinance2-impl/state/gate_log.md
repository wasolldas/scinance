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
