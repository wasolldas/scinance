#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════
# run_short.sh — T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 1, WP-5)
#
# Ein Befehl, keine Pflicht-Parameter, Gesamtlaufzeit ~10-20 min:
#   1) RECORDER_SMOKE   5-min-Live-Smoke der F0-Recording-Engine (C-36)
#   2) RECORDER_CHECK   Parquet-Existenz + Row-Count je Stream + Schema-Version
#   3) E15_EVAL         E-15/H-01-Auswertung der echten iter-5-Ergebnisse
#                       (Baseline: iter-4 aus edge-reconciliation/input/iter4_raw/)
#   4) C42_QUICK_HAR    C-42-Quick-Fit BTCUSDT, HAR-Baseline (laeuft immer)
#   5) C42_QUICK_LGBM   dito mit LightGBM, NUR falls installiert (optional)
#
# Jeder Schritt ist gekapselt (Timeout + Fehler loggen + weitermachen).
# Ende: 1 Zeile je Schritt (OK/FAIL/SKIP) + Exit-Code:
#   0 = alle Schritte OK · 1 = mind. ein FAIL · 2 = kein FAIL, aber SKIP
# Details: scinance2-impl/handoff_local/results/short_<timestamp>/
#
# Dry-Run (Mechanik-Test ohne echte Laeufe): HANDOFF_DRY_RUN=1 ./run_short.sh
#   (HANDOFF_DRY_RC=1 simuliert fehlschlagende Schritte)
# ════════════════════════════════════════════════════════════════════════
set -u

# ── Pfade (bei Bedarf HIER anpassen — siehe README_RUN.md) ──────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# Lokale DuckDB mit kline_1min/trades. Default = Repo-ueblicher Pfad aus
# persistence/db.py (DATA_DIR/bybit_edge.duckdb). Override: HANDOFF_DUCKDB.
DUCKDB_PATH="${HANDOFF_DUCKDB:-$REPO_ROOT/data/bybit_edge.duckdb}"
# iter-5-Replay-Artefakte (DEC-02-Default-Pfade von replay_all.py).
E15_RESULTS="$REPO_ROOT/edge_research_framework/results/replay_all_results.json"
# trades_all.csv: Pfad-Kaskade — der iter-5-Lauf exportierte nach
# results/trades_iter5/ (T2-Defekt 2026-06-12: fester Pfad fand nichts).
# (1) results/trades_all.csv  (2) results/trades_iter5/trades_all.csv
# (3) neuester results/trades_*/trades_all.csv — erster Treffer gewinnt.
E15_TRADES=""
for cand in \
  "$REPO_ROOT/edge_research_framework/results/trades_all.csv" \
  "$REPO_ROOT/edge_research_framework/results/trades_iter5/trades_all.csv"; do
  if [ -f "$cand" ]; then E15_TRADES="$cand"; break; fi
done
if [ -z "$E15_TRADES" ]; then
  E15_TRADES="$(ls -t "$REPO_ROOT"/edge_research_framework/results/trades_*/trades_all.csv 2>/dev/null | head -n 1 || true)"
fi
# iter-4-Baseline fuer den E-17-Divergenz-Check.
E15_BASE_RESULTS="$REPO_ROOT/edge-reconciliation/input/iter4_raw/replay_all_results.json"
E15_BASE_TRADES="$REPO_ROOT/edge-reconciliation/input/iter4_raw/trades_all.csv"

# ── Umgebung ─────────────────────────────────────────────────────────────
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
fi
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export BYBIT_DATA_DIR="${BYBIT_DATA_DIR:-$REPO_ROOT/data}"
cd "$REPO_ROOT"

DRY="${HANDOFF_DRY_RUN:-0}"
DRY_RC="${HANDOFF_DRY_RC:-0}"
TIMEOUT_BIN=""
command -v timeout >/dev/null 2>&1 && TIMEOUT_BIN="timeout"

TS="$(date -u +%Y%m%d_%H%M%S)"
RUN_DIR="$SCRIPT_DIR/results/short_$TS"
mkdir -p "$RUN_DIR"
STEPS_TSV="$RUN_DIR/steps.tsv"
MAIN_LOG="$RUN_DIR/run_short.log"

N_OK=0; N_FAIL=0; N_SKIP=0
SUMMARY_LINES=""

# record <name> <status> <rc> <dur_s> <detail> [optional]
record() {
  local name="$1" status="$2" rc="$3" dur="$4" detail="$5" optional="${6:-0}"
  printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$status" "$rc" "$dur" "$detail" >> "$STEPS_TSV"
  SUMMARY_LINES="${SUMMARY_LINES}${name}: ${status} (${detail})
"
  case "$status" in
    OK)   N_OK=$((N_OK+1)) ;;
    FAIL) N_FAIL=$((N_FAIL+1)) ;;
    SKIP) [ "$optional" = "1" ] || N_SKIP=$((N_SKIP+1)) ;;
  esac
}

# run_step <name> <timeout_s> <cmd...>  — try/except-Aequivalent: Fehler
# werden geloggt, der Lauf geht IMMER weiter. Rueckgabe = rc des Kommandos.
run_step() {
  local name="$1" tmo="$2"; shift 2
  local log="$RUN_DIR/${name}.log" rc detail="" t0 t1 status
  echo "[$(date -u '+%H:%M:%S')] START $name: $*" | tee -a "$MAIN_LOG"
  t0=$(date +%s)
  if [ "$DRY" != "0" ]; then
    echo "[DRY-RUN] $*" >> "$log"
    rc="$DRY_RC"; detail="dry-run rc=$rc"
  else
    if [ -n "$TIMEOUT_BIN" ]; then
      "$TIMEOUT_BIN" --kill-after=30 "${tmo}s" "$@" >> "$log" 2>&1
    else
      "$@" >> "$log" 2>&1
    fi
    rc=$?
    [ "$rc" -eq 124 ] && detail="TIMEOUT nach ${tmo}s"
  fi
  t1=$(date +%s)
  status=FAIL; [ "$rc" -eq 0 ] && status=OK
  [ -z "$detail" ] && detail="rc=$rc"
  record "$name" "$status" "$rc" "$((t1-t0))" "$detail"
  echo "[$(date -u '+%H:%M:%S')] END   $name: $status ($detail, $((t1-t0))s) log=$log" | tee -a "$MAIN_LOG"
  return "$rc"
}

echo "RUN_SHORT (T2) — Repo: $REPO_ROOT — Ergebnisse: $RUN_DIR" | tee -a "$MAIN_LOG"
[ "$DRY" != "0" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv — keine echten Laeufe." | tee -a "$MAIN_LOG"

# ── Schritt 1: Recorder-Smoke (5 min live gegen echte Bybit-WS) ─────────
run_step RECORDER_SMOKE 420 \
  "$PY" -m bybit_edge.recorder --duration 300 --cap-gb 5 || true

# ── Schritt 2: Parquet-/Row-Count-/Schema-Version-Check je Stream ───────
run_step RECORDER_CHECK 120 \
  "$PY" "$SCRIPT_DIR/check_recording.py" --max-age-min 30 \
  --json "$RUN_DIR/recording_check.json" || true

# ── Schritt 3: E-15-Auswertung auf echten iter-5-Ergebnissen ────────────
if [ "$DRY" = "0" ] && [ ! -f "$E15_RESULTS" ]; then
  record E15_EVAL SKIP 0 0 "iter-5-Ergebnisse fehlen ($E15_RESULTS) — scripts/replay_all.py separat laufen lassen"
elif [ "$DRY" = "0" ] && [ -z "$E15_TRADES" ]; then
  record E15_EVAL SKIP 0 0 "trades_all.csv nicht gefunden (gesucht: results/, results/trades_iter5/, results/trades_*/) — Replay mit --export-trades laufen lassen"
else
  # Dry-Run ohne gefundene Datei: Default-Pfad nur fuer die Kommandozeile.
  [ -z "$E15_TRADES" ] && E15_TRADES="$REPO_ROOT/edge_research_framework/results/trades_all.csv"
  run_step E15_EVAL 600 \
    "$PY" "$REPO_ROOT/scripts/evaluate_e15.py" \
    --results-path "$E15_RESULTS" --trades-path "$E15_TRADES" \
    --baseline-results "$E15_BASE_RESULTS" --baseline-trades "$E15_BASE_TRADES" \
    --out "$RUN_DIR/e15" || true
fi

# ── Schritt 4: C-42-Quick-Fit BTCUSDT (HAR, laeuft immer) ───────────────
if [ "$DRY" = "0" ] && [ ! -f "$DUCKDB_PATH" ]; then
  record C42_QUICK_HAR SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH) — Pfad oben im Skript / HANDOFF_DUCKDB anpassen"
  record C42_QUICK_LGBM SKIP 0 0 "DuckDB fehlt" 1
else
  # --db-copy: liest eine Temp-Kopie der DuckDB, damit der T2-Lauf nie am
  # RW-Lock des laufenden 1.0-Collectors haengt (T2-Defekt 2026-06-12).
  run_step C42_QUICK_HAR 900 \
    "$PY" "$REPO_ROOT/scripts/c42_repro.py" --quick --model har --symbol BTCUSDT \
    --db-path "$DUCKDB_PATH" --db-copy --max-bars 60000 --out "$RUN_DIR/c42_quick_har" || true

  # ── Schritt 5 (optional): zusaetzlich LightGBM, falls installiert ─────
  if [ "$DRY" != "0" ] || "$PY" -c "import lightgbm" >/dev/null 2>&1; then
    run_step C42_QUICK_LGBM 900 \
      "$PY" "$REPO_ROOT/scripts/c42_repro.py" --quick --model lightgbm --symbol BTCUSDT \
      --db-path "$DUCKDB_PATH" --db-copy --max-bars 60000 --out "$RUN_DIR/c42_quick_lightgbm" || true
  else
    record C42_QUICK_LGBM SKIP 0 0 "lightgbm nicht installiert (optional; pip install -e .[vol])" 1
  fi
fi

# ── Gesamt-Summary: 1 Zeile je Schritt + Exit-Code ──────────────────────
EXIT=0
[ "$N_SKIP" -gt 0 ] && EXIT=2
[ "$N_FAIL" -gt 0 ] && EXIT=1
{
  echo "──────── RUN_SHORT SUMMARY ────────"
  printf '%s' "$SUMMARY_LINES"
  echo "RUN_SHORT GESAMT: ok=$N_OK fail=$N_FAIL skip=$N_SKIP -> exit $EXIT | Ergebnisse: $RUN_DIR"
} | tee "$RUN_DIR/summary.txt" | tee -a "$MAIN_LOG"
exit "$EXIT"
