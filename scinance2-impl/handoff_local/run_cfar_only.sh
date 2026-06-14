#!/usr/bin/env bash
# ========================================================================
# run_cfar_only.sh - H-03-Notausgang (Scinance 2.0 Welle 1, WP-3)
#
# Standalone-Runner NUR fuer C-31 CFAR ueber alle 5 Symbole (BTC/ETH/SOL/
# BNB/XRP). Gedacht als 1-2h-Schnelldurchgang falls run_overnight kippt:
# H-03 bleibt der einzige unbeschiedene Welle-1-Pilot, daher dieser Pfad
# (overnight-Defekt 2026-06-13: Block 3 wurde nie erreicht; Hauptrunner
# starb zwischen Block 2 und Block 3).
#
# Aufruf (keine Pflicht-Parameter):
#   bash scinance2-impl/handoff_local/run_cfar_only.sh
#
# Macht NUR:
#   C31_CFAR_<sym>   C-31 CFAR auf DuckDB-trades mit --db-copy
#                    (lock-frei, 30s Open-Timeout im Driver).
#                    Default-Parameter wie run_overnight (Windows 2,
#                    Surrogates 200, Seed 42); Pro-Symbol-Timeout 1800s.
#
# Exit-Code: 0 = alle OK, 1 = mind. ein FAIL, 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl/handoff_local/results/cfar_<timestamp>/
#             + SUMMARY.md (eigenes Mini-Summary nur fuer H-03)
#
# Optionale Env-Overrides:
#   HANDOFF_DUCKDB=<pfad>   HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC)
# ========================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DUCKDB_PATH="${HANDOFF_DUCKDB:-$REPO_ROOT/data/bybit_edge.duckdb}"

SYMBOLS="BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT"
C31_WINDOWS=2
C31_SURROGATES=200
C31_TIMEOUT_SEC=1800   # 30 min/Symbol - mit --db-copy reichlich

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
fi
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export BYBIT_DATA_DIR="${BYBIT_DATA_DIR:-$REPO_ROOT/data}"
cd "$REPO_ROOT"
renice -n 10 $$ >/dev/null 2>&1 || true

DRY="${HANDOFF_DRY_RUN:-0}"
DRY_RC="${HANDOFF_DRY_RC:-0}"
TIMEOUT_BIN=""
command -v timeout >/dev/null 2>&1 && TIMEOUT_BIN="timeout"

TS="$(date -u +%Y%m%d_%H%M%S)"
RUN_DIR="$SCRIPT_DIR/results/cfar_$TS"
mkdir -p "$RUN_DIR"
STEPS_TSV="$RUN_DIR/steps.tsv"
MAIN_LOG="$RUN_DIR/run_cfar_only.log"

N_OK=0; N_FAIL=0; N_SKIP=0
SUMMARY_LINES=""
RESULT_ROWS=""

record() { # <name> <status> <rc> <dur_s> <detail> [optional]
  local name="$1" status="$2" rc="$3" dur="$4" detail="$5" optional="${6:-0}"
  printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$status" "$rc" "$dur" "$detail" >> "$STEPS_TSV"
  SUMMARY_LINES="${SUMMARY_LINES}${name}: ${status} (${detail}, ${dur}s)
"
  RESULT_ROWS="${RESULT_ROWS}| ${name} | ${status} | ${rc} | ${dur}s | ${detail} |
"
  case "$status" in
    OK)   N_OK=$((N_OK+1)) ;;
    FAIL) N_FAIL=$((N_FAIL+1)) ;;
    SKIP) [ "$optional" = "1" ] || N_SKIP=$((N_SKIP+1)) ;;
  esac
}

run_step() { # <name> <timeout_s> <cmd...>
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

echo "RUN_CFAR_ONLY (H-03 Notausgang) - Repo: $REPO_ROOT - Ergebnisse: $RUN_DIR" | tee -a "$MAIN_LOG"
echo "DuckDB: $DUCKDB_PATH | windows=$C31_WINDOWS surrogates=$C31_SURROGATES timeout=${C31_TIMEOUT_SEC}s/symbol" | tee -a "$MAIN_LOG"
[ "$DRY" != "0" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." | tee -a "$MAIN_LOG"

# -- C31 CFAR je Symbol ---------------------------------------------------
if [ "$DRY" = "0" ] && [ ! -f "$DUCKDB_PATH" ]; then
  for sym in $SYMBOLS; do
    record "C31_CFAR_${sym}" SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH) - HANDOFF_DUCKDB setzen"
  done
else
  for sym in $SYMBOLS; do
    run_step "C31_CFAR_${sym}" "$C31_TIMEOUT_SEC" \
      "$PY" "$REPO_ROOT/scripts/c31_cfar.py" --db "$DUCKDB_PATH" --symbol "$sym" \
      --windows "$C31_WINDOWS" --surrogates "$C31_SURROGATES" --db-copy \
      --out "$RUN_DIR/c31_${sym}" || true
  done
fi

# -- Mini-Summary ---------------------------------------------------------
EXIT=0
[ "$N_SKIP" -gt 0 ] && EXIT=2
[ "$N_FAIL" -gt 0 ] && EXIT=1
{
  echo "-------- RUN_CFAR_ONLY SUMMARY --------"
  printf '%s' "$SUMMARY_LINES"
  echo "RUN_CFAR_ONLY GESAMT: ok=$N_OK fail=$N_FAIL skip=$N_SKIP -> exit $EXIT | Ergebnisse: $RUN_DIR"
} | tee "$RUN_DIR/summary.txt" | tee -a "$MAIN_LOG"

# SUMMARY.md (maschinen- und menschenlesbar fuer den gate-auditor)
{
  echo "# H-03 Notausgang - C-31 CFAR Runner"
  echo ""
  echo "- **Erzeugt:** $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
  echo "- **Run-Dir:** \`$RUN_DIR\`"
  echo "- **DuckDB:** \`$DUCKDB_PATH\`"
  echo "- **Parameter:** windows=$C31_WINDOWS, surrogates=$C31_SURROGATES, --db-copy, timeout=${C31_TIMEOUT_SEC}s/symbol"
  echo ""
  echo "| Symbol | Status | rc | Dauer | Detail |"
  echo "|---|---|---:|---:|---|"
  printf '%s' "$RESULT_ROWS"
  echo ""
  echo "**Gesamt:** ok=$N_OK fail=$N_FAIL skip=$N_SKIP -> exit $EXIT"
  echo ""
  echo "*H-03-Gate-Urteil faellt der gate-auditor gegen die Registry (Roh-JSONs je Symbol unter \`c31_<symbol>/c31_cfar_results.json\`).*"
} > "$RUN_DIR/SUMMARY.md"

exit "$EXIT"
