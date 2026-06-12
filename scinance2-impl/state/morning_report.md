# Morning Report — 2026-06-12 (ANALYZE, Welle 1)

**Auswertung:** gate-auditor gegen `state/hypothesis_registry.md` (H-01/H-02/H-03) + PRD §3/§8.
**Upload:** `handoff_local/results/upload_20260611/` (3 Läufe + SUMMARY_2026-06-11.md).
**Formale Gate-Urteile:** `state/gate_log.md` (GL-001…GL-004).

---

## 1. Was lief, was nicht (Upload-Übersicht)

| Lauf | Typ | Ergebnis |
|---|---|---|
| `overnight_20260611_154638` | T3 (vor Runner-Fixes) | **C-42 voll durchgelaufen, 5/5 Symbole** (Daten vollständig). C-31 crashte (5/5). Recorder-Dauertest 8 h OK, aber 3 Streams NO_DATA. Der „FAIL (rc=)" in summary.txt = PS-5.1-ExitCode-Bug, nicht der Inhalt. |
| `short_20260611_143537` | T2 (vor Fixes) | rc-Bug, C42-Quick-Timeouts, E15-Pfaddefekt. Überholt. |
| `short_20260612_082957` | T2 (nach Fixes) | RECORDER_SMOKE rc=0 OK. RECORDER_CHECK rc=1 echt (3 Streams NO_DATA). E15_EVAL rc=1 echt (trades_all.csv fehlt). C42-Quick beide TIMEOUT (DuckDB-Open-Hang, Lock-Verdacht). |

**Kernbotschaft:** Der einzige Lauf mit verwertbaren Gate-Daten ist der T3-Overnight — und der reicht für ein
**vollständiges, eindeutiges H-02-Urteil**. H-01 und H-03 sind durch Werkzeug-Defekte blockiert, nicht durch
inhaltliche Befunde.

---

## 2. Gate-Urteile

### H-02 · C-42-Reproduktion → **DROP/PARK** (Gate verfehlt, 0/5 Symbole) — Kernbefund des Uploads
Registriertes Gate: OOS-R² ≥ 0.15 UND QLIKE < HAR-RV in ALLEN ≥2 Fenstern. **Kein Symbol** besteht.

| Symbol | min OOS-R² (3 Folds) | R²≥0.15 alle Folds | QLIKE<HAR alle Folds | Urteil |
|---|---:|:--:|:--:|:--:|
| BTCUSDT | −0.3212 | nein | nein (Fold 2) | FAIL |
| ETHUSDT | −0.1470 | nein | nein (Fold 0) | FAIL |
| SOLUSDT | −0.0849 | nein | nein (Fold 0) | FAIL |
| BNBUSDT | −0.5294 | nein | nein (Fold 0,1) | FAIL |
| XRPUSDT | −0.0346 | nein | nein (Fold 0) | FAIL |

- Aggregation: Gate je Symbol, Gesamturteil = strengste Lesart (Ein-Fenster-Abbruch §6 wirkt pro Fenster).
  Hier müßig — alle 5 fallen durch beide Kriterien.
- FDR (F-VOL, BH α=0.10): **0/36 Features signifikant** in jedem Symbol. Der Vol-Anker trägt nicht.
- Testdesign konform (purged WF, 3 disjunkte Fenster, Purge 60 + Embargo 1440 Bars, deterministisch, 5/5 Symbole).
- **Reproduktions-Vorbehalt:** Feature-Set 1 DOCUMENTED / 35 ASSUMED → Best-Effort-Repro, kein bit-genaues
  Kestrel-Replikat. Urteil gilt für diese Repro; bit-genaue Original-Features wären eine neue Hypothese (H-02b).
- **Der dokumentierte Test-R²≈0.249-Befund überlebt purged WF + FDR nicht — L1-Selbstauskunfts-Artefakt bestätigt.**

**Kaskade (PRD §3):** Vol-Stack verliert den Anker, gesperrt bleiben **C-10 / C-35 / C-11 / C-12 / C-34 / VRP-RV-Bein.**

### H-01 · E-15 → **PENDING** (nicht geurteilt)
Blocker: `E15_EVAL` rc=1, `trades_all.csv` am Default-Pfad nicht gefunden; iter-5-Export liegt vermutlich unter
`trades_iter5/`. Reiner Pfad-/Export-Defekt, keine `e15_evaluation.json`. Kein Urteil, keine Vorwegnahme.

### H-03 · C-31-CFAR → **PENDING** (nicht geurteilt)
Blocker: Crash in `cyclic_spectrum.py:115 bin_counts` — `numpy ArrayMemoryError` (1.30 TiB, n_bins explodiert),
alle 5 Symbole identisch. Implementierungs-Bug (Bin-/Zeitfenster-Parameter), keine `c31_cfar_results.json`.
Kein Urteil, KEINE inhaltliche Vorwegnahme (Traceback wird parallel diagnostiziert).

### C-36 Recording → **PILOT-STATUS** (kein Alpha-Gate, F0-Gate noch nicht fällig)
premium_index_kline OK (96600 rows, REST-Pfad). adl_alerts EMPTY_OK (event-getrieben). **rpi_orderbook +
insurance_pool + option_tickers = NO_DATA über 5-min-Smoke UND 8-h-Dauertest.** Subscribe wird bestätigt,
liefert aber nichts; Option-WS bricht zusätzlich alle ~30 s mit `1011 keepalive ping timeout`. Offene Frage
(INC-06): Subscribe-Fehler/falscher Keepalive vs. nicht-existentes/falsch benanntes Topic. Storage 0.004/50 GB OK.

---

## 3. Empfohlene Folge-WPs (Prioritätsreihenfolge)

1. **WP-A · H-02-Konsequenz formalisieren + Vol-Stack sperren (sofort, kein Lauf).**
   C-42 → PARK im State; C-10/C-35/C-11/C-12/C-34/VRP-RV-Bein als „gesperrt (kein Anker)" markieren.
   Entscheidung PARK-vs-DROP dokumentieren (DEC-xx): PARK empfohlen, da ein verifizierter-Feature-Re-Run der
   einzige Rettungspfad ist.

2. **WP-B · C-31-Crash-Fix (höchste Reparatur-Prio — einziger echter Alpha-Test der Welle 1).**
   `bin_counts`-Guard gegen n_bins-Explosion + Sanity-Check `bin_dt_ms` vs. (t1−t0); dann Surrogate-Lauf auf
   Echt-Ticks (≥2 disjunkte Fenster) erneut via handoff_local. Gate H-03 unverändert.

3. **WP-C · C-36 Stream-Diagnose (zeitkritisch — Recording-Vorlauf für ganze Welle 2).**
   (a) Topic-Namen `orderbook.rpi.*`, `insurance.USDT`, `adlAlert`, `tickers.{BTC,ETH}` gegen aktuelle
   Bybit-v5-WS-Doc verifizieren (INC-06: PRD-Endpoints können falsch sein); (b) Option-WS-Keepalive/ping-Intervall
   fixen; (c) je Topic ein kurzer Live-Probe-Subscribe in Sandbox. premium_index_kline läuft bereits — nicht anfassen.

4. **WP-D · E-15-Pfad-Fix (entsperrt H-01-Urteil).**
   `trades_all.csv`-Default ↔ `trades_iter5/`-Export angleichen; E15_EVAL erneut. Danach H-01-Gate-Urteil
   gegen die §3-Korridore. Entscheidet über den gesamten Funding-Cluster (C-37/CS-12/C-08).

5. **WP-E · Runner-Härtung (Begleitfix, niedrige Prio).**
   PS-5.1-ExitCode-Capture reparieren (rc= → echter rc), damit summary.txt den Schritt-Status korrekt zeigt;
   C42-Quick-DuckDB-Open-Hang (Lock-Konflikt mit laufendem Collector → read-only/Retry/Copy-on-open prüfen).

**Heute Nacht laufen sollte:** nach WP-B/WP-C/WP-D — neuer Overnight mit (1) C-31-Surrogate (gefixt),
(2) Recorder-Dauertest mit verifizierten Topics, (3) E-15-Eval auf korrektem Pfad. C-42 NICHT erneut (Urteil steht;
Re-Run nur als neue Hypothese H-02b mit verifizierten Features).
