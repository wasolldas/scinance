#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════
# run_overnight.sh — T3 LOCAL_LONG Runner (Scinance 2.0 Welle 1, WP-5)
#
# Ein Befehl, keine Pflicht-Parameter, laeuft UNBEAUFSICHTIGT ueber Nacht
# (~8h+, vom Recorder-Dauertest bestimmt). Bricht NIE mit offenem Prompt ab;
# jeder Teilschritt hat Timeout + Fehler-Kapselung und der Lauf faehrt fort.
#
# Bloecke:
#   RECORDER_LONG    Recorder-Dauertest im Hintergrund (Default 8h, Cap 50 GB)
#   C42_WF_<sym>     C-42 Voll-Walk-Forward je Symbol (BTC/ETH/SOL/BNB/XRP),
#                    Modell lightgbm mit har-Fallback wenn Import scheitert
#   C31_CFAR_<sym>   C-31 CFAR auf echten Ticks (DuckDB-trades, 200 Surrogates,
#                    2 disjunkte Fenster) je Symbol
#   REPLAY_ITER5     NUR Hinweis: replay_all.py (12h-Replays) wird bewusst
#                    NICHT automatisch gestartet — User-Entscheidung
#   RECORDER_CHECK   Parquet/Row-Count/Schema-Version + Storage-Deckel
#   SUMMARY          aggregate_results.py -> results/SUMMARY_<yyyy-mm-dd>.md
#
# Exit-Code: 0 = alle Bloecke OK · 1 = mind. ein FAIL · 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl/handoff_local/results/overnight_<timestamp>/
#             + results/SUMMARY_<datum>.md (Morgen-Auswertung gate-auditor)
#
# Optionale Env-Overrides (KEINE Pflicht):
#   HANDOFF_RECORDER_HOURS=8   HANDOFF_RECORDER_CAP_GB=50   HANDOFF_DUCKDB=<pfad>
#   HANDOFF_DRY_RUN=1 (Mechanik-Test ohne echte Laeufe; HANDOFF_DRY_RC=1 -> FAILs)
# ════════════════════════════════════════════════════════════════════════
set -u

# ── Pfade (bei Bedarf HIER anpassen — siehe README_RUN.md) ──────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# Lokale DuckDB mit kline_1min/trades. Default = Repo-ueblicher Pfad aus
# persistence/db.py (DATA_DIR/bybit_edge.duckdb). Override: HANDOFF_DUCKDB.
DUCKDB_PATH="${HANDOFF_DUCKDB:-$REPO_ROOT/data/bybit_edge.duckdb}"
E15_RESULTS="$REPO_ROOT/edge_research_framework/results/replay_all_results.json"

RECORDER_HOURS="${HANDOFF_RECORDER_HOURS:-8}"
RECORDER_CAP_GB="${HANDOFF_RECORDER_CAP_GB:-50}"
RECORDER_DURATION_S=$(( RECORDER_HOURS * 3600 ))
SYMBOLS="BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT"
C31_WINDOWS=2
C31_SURROGATES=200
C31_MAX_TICKS=150000   # DEC-09: deterministische Tick-Obergrenze je Fenster
C31_TIMEOUT_SEC=1800   # mit Tick-Cap reichlich (vorher 5400s -> 5/5 TIMEOUT)

# ── Umgebung ─────────────────────────────────────────────────────────────
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
fi
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export BYBIT_DATA_DIR="${BYBIT_DATA_DIR:-$REPO_ROOT/data}"
cd "$REPO_ROOT"
renice -n 10 $$ >/dev/null 2>&1 || true   # Ressourcen-Disziplin: niedrige Prio

DRY="${HANDOFF_DRY_RUN:-0}"
DRY_RC="${HANDOFF_DRY_RC:-0}"
TIMEOUT_BIN=""
command -v timeout >/dev/null 2>&1 && TIMEOUT_BIN="timeout"

TS="$(date -u +%Y%m%d_%H%M%S)"
RUN_DIR="$SCRIPT_DIR/results/overnight_$TS"
mkdir -p "$RUN_DIR"
STEPS_TSV="$RUN_DIR/steps.tsv"
MAIN_LOG="$RUN_DIR/run_overnight.log"

N_OK=0; N_FAIL=0; N_SKIP=0
SUMMARY_LINES=""

record() { # <name> <status> <rc> <dur_s> <detail> [optional]
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

run_step() { # <name> <timeout_s> <cmd...> — kapselt, loggt, faehrt fort
  local name="$1" tmo="$2"; shift 2
  local log="$RUN_DIR/${name}.log" rc detail="" t0 t1 status
  echo "[$(date -u '+%H:%M:%S')] START $name: $*" | tee -a "$MAIN_LOG"
  t0=$(date +%s)
  if [ "$DRY" != "0" ]; then
    echo "[DRY-RUN] $*" >> "$log"
    rc="$DRY_RC"; detail="dry-run rc=$rc"
  else
    if [ -n "$TIMEOUT_BIN" ]; then
      "$TIMEOUT_BIN" --kill-after=60 "${tmo}s" "$@" >> "$log" 2>&1
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

echo "RUN_OVERNIGHT (T3) — Repo: $REPO_ROOT — Ergebnisse: $RUN_DIR" | tee -a "$MAIN_LOG"
echo "Recorder: ${RECORDER_HOURS}h, Cap ${RECORDER_CAP_GB} GB | DuckDB: $DUCKDB_PATH" | tee -a "$MAIN_LOG"
[ "$DRY" != "0" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv — keine echten Laeufe." | tee -a "$MAIN_LOG"

# ── Block 1: Recorder-Dauertest im Hintergrund starten ──────────────────
REC_PID=""
REC_T0=$(date +%s)
if [ "$DRY" = "0" ]; then
  nohup nice -n 10 "$PY" -m bybit_edge.recorder \
    --duration "$RECORDER_DURATION_S" --cap-gb "$RECORDER_CAP_GB" \
    >> "$RUN_DIR/RECORDER_LONG.log" 2>&1 &
  REC_PID=$!
  echo "[$(date -u '+%H:%M:%S')] RECORDER_LONG gestartet (PID $REC_PID, ${RECORDER_DURATION_S}s)" | tee -a "$MAIN_LOG"
fi

# ── Block 2: C-42 Voll-Walk-Forward multi-symbol ─────────────────────────
C42_MODEL="lightgbm"
if [ "$DRY" = "0" ] && ! "$PY" -c "import lightgbm" >/dev/null 2>&1; then
  C42_MODEL="har"
  echo "lightgbm-Import scheitert -> har-Fallback (DEC-04; pip install -e .[vol] fuer Reproduktions-Treue)" | tee -a "$MAIN_LOG"
fi
if [ "$DRY" = "0" ] && [ ! -f "$DUCKDB_PATH" ]; then
  record C42_WF SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH) — Pfad oben im Skript / HANDOFF_DUCKDB anpassen"
else
  for sym in $SYMBOLS; do
    # --db-copy: liest eine Temp-Kopie der DuckDB, damit der Voll-WF nie am
    # RW-Lock des laufenden 1.0-Collectors haengt (overnight-Defekt 2026-06-13:
    # 5x C42_WF FAIL nach 31s am _open_db_with_timeout). Kopier-Overhead ist
    # trivial gegen das 7200s-Budget.
    run_step "C42_WF_${sym}" 7200 \
      "$PY" "$REPO_ROOT/scripts/c42_repro.py" --model "$C42_MODEL" --symbol "$sym" \
      --n-folds 3 --db-path "$DUCKDB_PATH" --db-copy --out "$RUN_DIR/c42_${sym}"
    rc=$?
    if [ "$rc" -eq 2 ] && [ "$C42_MODEL" != "har" ]; then
      # Modell-Dependency fehlte zur Laufzeit doch -> einmaliger har-Fallback.
      run_step "C42_WF_${sym}_HARFB" 7200 \
        "$PY" "$REPO_ROOT/scripts/c42_repro.py" --model har --symbol "$sym" \
        --n-folds 3 --db-path "$DUCKDB_PATH" --db-copy --out "$RUN_DIR/c42_${sym}" || true
    fi
  done
fi

# ── Block 3: C-31 CFAR auf echten Ticks (DuckDB-trades) ──────────────────
if [ "$DRY" = "0" ] && [ ! -f "$DUCKDB_PATH" ]; then
  record C31_CFAR SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH)"
else
  for sym in $SYMBOLS; do
    # --db-copy: Temp-Kopie der DuckDB lesen (lock-frei, wie C42). Der CFAR-
    # Driver hat zusaetzlich einen 30s-Open-Timeout (DataError mit Lock-Hinweis),
    # damit ein blockierter Open den Subprozess nicht haengen laesst (overnight-
    # Defekt 2026-06-13: kein C31-Log -> Hauptrunner starb).
    # --max-ticks-per-window (DEC-09): nimmt die JUENGSTEN windows x max-ticks
    # Ticks je Symbol -> rechenbar + stationaer. Behebt den 5400s-TIMEOUT 5/5
    # vom 2026-06-14 (die trades-Tabelle ist tage-/wochentief; ungebremst
    # spannte jedes Fenster Tage). Gate-Schwellen UNVERAENDERT.
    run_step "C31_CFAR_${sym}" "$C31_TIMEOUT_SEC" \
      "$PY" "$REPO_ROOT/scripts/c31_cfar.py" --db "$DUCKDB_PATH" --symbol "$sym" \
      --windows "$C31_WINDOWS" --surrogates "$C31_SURROGATES" \
      --max-ticks-per-window "$C31_MAX_TICKS" --db-copy \
      --out "$RUN_DIR/c31_${sym}" || true
  done
fi

# ── Block 4: Hinweis iter-5-Replay (bewusst NICHT automatisch starten) ───
if [ -f "$E15_RESULTS" ]; then
  record REPLAY_ITER5 INFO 0 0 "iter-5-Ergebnisse vorhanden — E-15-Auswertung laeuft im run_short (Schritt E15_EVAL)"
else
  record REPLAY_ITER5 INFO 0 0 "iter-5-Replay fehlt noch: scripts/replay_all.py separat starten (12h) — Runner startet das bewusst NICHT (User-Entscheidung)"
fi

# ── Block 5: Auf Recorder warten, dann pruefen (inkl. Storage-Deckel) ────
if [ "$DRY" != "0" ]; then
  status=FAIL; [ "$DRY_RC" -eq 0 ] && status=OK
  record RECORDER_LONG "$status" "$DRY_RC" 0 "dry-run rc=$DRY_RC"
elif [ -n "$REC_PID" ]; then
  REC_DEADLINE=$(( REC_T0 + RECORDER_DURATION_S + 600 ))
  while kill -0 "$REC_PID" 2>/dev/null && [ "$(date +%s)" -lt "$REC_DEADLINE" ]; do
    sleep 60
  done
  if kill -0 "$REC_PID" 2>/dev/null; then
    kill "$REC_PID" 2>/dev/null; sleep 15; kill -9 "$REC_PID" 2>/dev/null
    record RECORDER_LONG FAIL 124 "$(( $(date +%s) - REC_T0 ))" "TIMEOUT: lief nach duration+600s noch — gekillt"
  else
    wait "$REC_PID"; rec_rc=$?
    rec_status=FAIL; [ "$rec_rc" -eq 0 ] && rec_status=OK
    record RECORDER_LONG "$rec_status" "$rec_rc" "$(( $(date +%s) - REC_T0 ))" "rc=$rec_rc"
  fi
fi

REC_AGE_MIN=$(( RECORDER_DURATION_S / 60 + 120 ))
run_step RECORDER_CHECK 300 \
  "$PY" "$SCRIPT_DIR/check_recording.py" --max-age-min "$REC_AGE_MIN" \
  --cap-gb "$RECORDER_CAP_GB" --json "$RUN_DIR/recording_check.json" || true

# ── Block 6: SUMMARY_<datum>.md aggregieren (Morgen-Auswertung) ──────────
SUMMARY_DATE="$(date -u +%F)"
"$PY" "$SCRIPT_DIR/aggregate_results.py" --run-dir "$RUN_DIR" \
  --label overnight --date "$SUMMARY_DATE" >> "$MAIN_LOG" 2>&1 \
  && record SUMMARY OK 0 0 "results/SUMMARY_${SUMMARY_DATE}.md geschrieben" \
  || record SUMMARY FAIL 1 0 "aggregate_results.py fehlgeschlagen — Roh-JSONs liegen in $RUN_DIR"

# ── Gesamt-Summary: 1 Zeile je Block + Exit-Code ─────────────────────────
EXIT=0
[ "$N_SKIP" -gt 0 ] && EXIT=2
[ "$N_FAIL" -gt 0 ] && EXIT=1
{
  echo "──────── RUN_OVERNIGHT SUMMARY ────────"
  printf '%s' "$SUMMARY_LINES"
  echo "RUN_OVERNIGHT GESAMT: ok=$N_OK fail=$N_FAIL skip=$N_SKIP -> exit $EXIT | Ergebnisse: $RUN_DIR"
} | tee "$RUN_DIR/summary.txt" | tee -a "$MAIN_LOG"
exit "$EXIT"
