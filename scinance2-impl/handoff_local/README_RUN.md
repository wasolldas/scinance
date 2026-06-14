# handoff_local — Lokale Test-Runner (Scinance 2.0, Welle 1)

Kurzfassung: **`run_short` doppelklicken/starten (~10–20 min), `run_overnight`
vor dem Schlafengehen starten (~8 h+), morgens den Inhalt von
`handoff_local/results/` in die Session hochladen — fertig.**

> **Wichtig (Vorlauf!):** Den `run_overnight` (enthaelt den Recording-Dauertest
> C-36) so frueh wie moeglich erstmals starten — der Daten-Vorlauf fuer
> Welle 2 beginnt erst mit der ersten Aufzeichnung auf deiner Maschine.

---

## Voraussetzungen (einmalig)

1. **Python-Umgebung** des Repos aktiv (die Umgebung, mit der auch
   `scripts/replay_all.py` laeuft), Paket installiert: `pip install -e .`
2. **Optional, empfohlen fuer C-42-Reproduktions-Treue:**
   `pip install -e .[vol]` (installiert LightGBM + scikit-learn).
   Ohne LightGBM laufen die Runner trotzdem — C-42 faellt automatisch auf
   die HAR-Baseline zurueck (DEC-04) bzw. ueberspringt den LightGBM-Zusatzschritt.
3. **Lokale DuckDB** mit `kline_1min`- und `trades`-Tabellen unter dem
   Repo-ueblichen Pfad `data/bybit_edge.duckdb`. Liegt sie woanders:
   - Variable `DUCKDB_PATH` / `$DuckDbPath` **oben in jedem Runner-Skript**
     anpassen (kommentiert), oder
   - Umgebungsvariable `HANDOFF_DUCKDB=<pfad>` setzen.
4. **Fuer die E-15-Auswertung:** die iter-5-Replay-Ergebnisse muessen unter
   `edge_research_framework/results/replay_all_results.json` + `trades_all.csv`
   liegen (Default-Output von `scripts/replay_all.py`, DEC-02). Fehlen sie,
   wird der Schritt sauber uebersprungen (SKIP) — dann `scripts/replay_all.py`
   separat starten (~12 h; die Runner starten das bewusst NICHT automatisch).
5. **Windows, vor dem Nacht-Lauf:** Standby deaktivieren, sonst schlaeft der
   Rechner ein: `powercfg /change standby-timeout-ac 0`

Start (Windows PowerShell, primaer):
```powershell
powershell -ExecutionPolicy Bypass -File scinance2-impl\handoff_local\run_short.ps1
powershell -ExecutionPolicy Bypass -File scinance2-impl\handoff_local\run_overnight.ps1
```
Start (WSL/Linux/macOS, Fallback):
```bash
bash scinance2-impl/handoff_local/run_short.sh
bash scinance2-impl/handoff_local/run_overnight.sh
```
Beide Varianten funktionieren aus **beliebigem Arbeitsverzeichnis** (Repo-Root
wird relativ zum Skript ermittelt). Keine Pflicht-Parameter.

---

## run_short (T2, ~10–20 min, sequentiell)

| # | Schritt | Was passiert | Dauer |
|---|---|---|---|
| 1 | `RECORDER_SMOKE` | F0-Recording-Engine (C-36) 5 min live gegen die oeffentliche Bybit-WS (`python -m bybit_edge.recorder --duration 300 --cap-gb 5`) | ~5 min |
| 2 | `RECORDER_CHECK` | Parquet-Existenz + Row-Count **je Stream** (rpi_orderbook, insurance_pool, premium_index_kline, option_tickers; adl_alerts ist event-getrieben und darf leer sein) + Schema-Version-Check | Sekunden |
| 3 | `E15_EVAL` | `scripts/evaluate_e15.py` auf den **echten iter-5-Ergebnissen** (Default-Pfade DEC-02), Baseline = iter-4 aus `edge-reconciliation/input/iter4_raw/` → H-01-Vorab-Urteil | ~1 min |
| 4 | `C42_QUICK_HAR` | `scripts/c42_repro.py --quick --model har` auf BTCUSDT gegen die lokale DuckDB (Pipeline-Durchstich) | wenige min |
| 5 | `C42_QUICK_LGBM` | dito mit `--model lightgbm`, **nur falls lightgbm installiert** (sonst optionaler SKIP, zaehlt nicht gegen den Exit-Code) | wenige min |

Ende: eine Zeile je Schritt (OK/FAIL/SKIP) + Gesamtzeile.
Details/Logs: `results/short_<timestamp>/` (je Schritt eigene Log-Datei,
`steps.tsv`, `summary.txt`, Roh-JSONs der Piloten).

## run_overnight (T3, unbeaufsichtigt, ~8 h+)

| Block | Was passiert | Budget |
|---|---|---|
| `RECORDER_LONG` | Recorder-**Dauertest** im Hintergrund: Default **8 h**, Storage-Deckel **50 GB** (Ringpuffer; Override `HANDOFF_RECORDER_HOURS` / `HANDOFF_RECORDER_CAP_GB`) | 8 h (parallel) |
| `C42_WF_<sym>` | C-42 **Voll-Walk-Forward** je Symbol (BTC/ETH/SOL/BNB/XRP), `--model lightgbm` mit automatischem `har`-Fallback, 3 purged OOS-Fenster → H-02 | bis 2 h/Symbol (Timeout) |
| `C31_CFAR_<sym>` | C-31 **CFAR auf echten Ticks** (DuckDB-`trades`), 2 disjunkte Fenster, 200 Surrogates, Seed 42 → H-03 | bis 1,5 h/Symbol (Timeout) |
| `REPLAY_ITER5` | Nur **Hinweis-Zeile**, falls die iter-5-Replays noch fehlen — `replay_all.py` (12 h) startet NIE automatisch | 0 |
| `RECORDER_CHECK` | Nach Recorder-Ende: Parquet/Row-Count/Schema-Version je Stream + **Deckel-Verifikation** (≤ 50 GB) | Sekunden |
| `SUMMARY` | Aggregation aller Bloecke → **`results/SUMMARY_<yyyy-mm-dd>.md`** | Sekunden |

Robustheit: jeder Block hat Timeout + Fehler-Kapselung (try/except bzw.
try/catch + `$LASTEXITCODE`/ExitCode); ein fehlgeschlagener Block wird geloggt
und der Lauf **faehrt fort**. Es gibt keinerlei interaktive Prompts. Die
Prozess-Prioritaet ist niedrig (nice/BelowNormal).

## run_cfar_only (H-03-Notausgang, ~1–2 h)

Wenn der nächtliche Lauf wieder kippt (z. B. OS-Sleep zwischen den Blöcken),
bleibt H-03 unbeschieden. Der **Standalone-CFAR-Runner** holt das auf einem
1–2-h-Pfad nach — er macht NUR C-31 über alle fünf Symbole, mit `--db-copy`
gegen den DuckDB-Lock und 30 min Pro-Symbol-Timeout:

```powershell
powershell -ExecutionPolicy Bypass -File scinance2-impl\handoff_local\run_cfar_only.ps1
```
```bash
bash scinance2-impl/handoff_local/run_cfar_only.sh
```

Ergebnisse: `results/cfar_<timestamp>/` (Roh-JSONs + Logs je Symbol,
`SUMMARY.md` als Mini-Aufstellung für den gate-auditor). Exit-Code-Semantik
wie bei den anderen Runnern. Default-Parameter spiegeln den Overnight-Block
(`--windows 2 --surrogates 200 --seed 42`); Override über `HANDOFF_DUCKDB`.

## Ergebnisse & Morgen-Auswertung

- Alles landet in **`scinance2-impl/handoff_local/results/`**:
  `short_<ts>/` bzw. `overnight_<ts>/` (Roh-JSONs + Logs je Schritt) und
  `SUMMARY_<datum>.md` (aggregiert, maschinen- und menschenlesbar).
- **Ergebnisse aus `handoff_local/results/` in die Session hochladen →
  automatische Morgen-Auswertung durch den gate-auditor gegen die Registry
  (H-01 / H-02 / H-03)** — du musst nichts interpretieren.

## Exit-Codes (beide Runner)

| Code | Bedeutung |
|---|---|
| 0 | alle Schritte OK |
| 1 | mindestens ein Schritt FAIL (Logs im Run-Verzeichnis) |
| 2 | kein FAIL, aber mindestens ein Pflicht-Schritt SKIP (z. B. iter-5-Ergebnisse oder DuckDB fehlen) |

Optionale Schritte (z. B. LightGBM-Zusatzlauf ohne installiertes lightgbm)
zaehlen als SKIP **nicht** gegen den Exit-Code.

## Selbsttest / Dry-Run (fuer Entwickler)

`HANDOFF_DRY_RUN=1` laesst jeden Runner ohne echte Laeufe durchlaufen
(Summary- und Exit-Code-Mechanik testen); `HANDOFF_DRY_RC=1` simuliert
fehlschlagende Schritte. PowerShell: `$env:HANDOFF_DRY_RUN='1'`.

Hilfsskripte (werden von den Runnern aufgerufen, kein Direktaufruf noetig):
`check_recording.py` (Parquet-/Schema-/Deckel-Pruefung, read-only) und
`aggregate_results.py` (SUMMARY-Erzeugung).
