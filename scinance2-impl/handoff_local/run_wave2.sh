#!/usr/bin/env bash
# ========================================================================
# run_wave2.sh - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 2, WP-4 Handoff)
#
# Ein Befehl, keine Pflicht-Parameter, laeuft UNBEAUFSICHTIGT 2-4h. Bricht
# NIE mit offenem Prompt ab; jeder Teilschritt hat Timeout + Fehler-
# Kapselung und der Lauf faehrt fort.
#
# Bloecke (jeder einzeln gekapselt, try/catch + Timeout + weitermachen):
#   H04            C-17/C-41 Lead-Lag-Mess-Gate (Paar BTC/ETH, 2 Fenster,
#                  200 Surrogates, F-LEADLAG BH-FDR alpha=0.10) - KAPITALFREI
#   H05            C-01 OFI-Vorzeichen-Test (BTC/ETH/SOL/BNB/XRP, 2 Fenster,
#                  200 Surrogates, F-OFI BH-FDR alpha=0.10) - KAPITALFREI
#   H06            C-07 Permutation Entropy (BTC/ETH/SOL/BNB/XRP, 2 Fenster,
#                  200 Surrogates, F-ENTROPY BH-FDR alpha=0.10) - KAPITALFREI
#   WAVE2_FDR      F-WAVE2 zweistufige BH-FDR-Aggregation (Stage 1 je Familie
#                  + Stage 2 ueber alle Stage-1-Survivor gemeinsam)
#
# Exit-Code: 0 = alle Bloecke OK * 1 = mind. ein FAIL * 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl/handoff_local/results/wave2_<timestamp>/
#             + SUMMARY_<datum>.md + WAVE2_SUMMARY.md (Morgen-Auswertung)
#
# Voraussetzung: DuckDB-Bestand mit trades+kline_1min auf der User-Maschine
# (Default-Pfad data/bybit_edge.duckdb; Override via HANDOFF_DUCKDB).
#
# Optionale Env-Overrides (KEINE Pflicht):
#   HANDOFF_DUCKDB=<pfad>
#   HANDOFF_DRY_RUN=1 (Mechanik-Test ohne echte Laeufe; HANDOFF_DRY_RC=1 -> FAILs)
# ========================================================================
set -u

# -- Pfade (bei Bedarf HIER anpassen - siehe README_WAVE2.md) ------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DUCKDB_PATH="${HANDOFF_DUCKDB:-$REPO_ROOT/data/bybit_edge.duckdb}"

PAIR="BTCUSDT,ETHUSDT"
SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
N_WINDOWS=2
N_SURROGATES=200
SEED=42
MAX_TICKS=150000
MAX_BARS=43200

# Per-Schritt-Budgets (grosszuegig, aber endlich; CLAUDE.md T3-Regel).
TMO_H04=5400      # 90 min - TE + WCOH + 200 Surrogates auf 150k Ticks * 2 Fenster
TMO_H05=7200      # 120 min - 5 Symbole * 5 deltas * 2 Fenster * 200 Surrogates
TMO_H06=7200      # 120 min - 5 Symbole * 4 deltas * 2 Fenster * 200 Surrogates
TMO_AGG=600       # 10 min - reine JSON-Aggregation

# -- Umgebung ------------------------------------------------------------
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
fi
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export BYBIT_DATA_DIR="${BYBIT_DATA_DIR:-$REPO_ROOT/data}"
cd "$REPO_ROOT"
renice -n 10 $$ >/dev/null 2>&1 || true   # Ressourcen-Disziplin

DRY="${HANDOFF_DRY_RUN:-0}"
DRY_RC="${HANDOFF_DRY_RC:-0}"
TIMEOUT_BIN=""
command -v timeout >/dev/null 2>&1 && TIMEOUT_BIN="timeout"

TS="$(date -u +%Y%m%d_%H%M%S)"
RUN_DIR="$SCRIPT_DIR/results/wave2_$TS"
mkdir -p "$RUN_DIR" "$RUN_DIR/h04" "$RUN_DIR/h05" "$RUN_DIR/h06"
STEPS_TSV="$RUN_DIR/steps.tsv"
MAIN_LOG="$RUN_DIR/run_wave2.log"

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

run_step() { # <name> <timeout_s> <cmd...> - kapselt, loggt, faehrt fort
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

echo "RUN_WAVE2 (T3) - Repo: $REPO_ROOT - Ergebnisse: $RUN_DIR" | tee -a "$MAIN_LOG"
echo "DuckDB: $DUCKDB_PATH | Paar: $PAIR | Symbole: $SYMBOLS" | tee -a "$MAIN_LOG"
echo "Fenster: $N_WINDOWS * Surrogates: $N_SURROGATES * Seed: $SEED" | tee -a "$MAIN_LOG"
[ "$DRY" != "0" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." | tee -a "$MAIN_LOG"

# DuckDB-Pruefung: fehlt -> alle drei Pilots SKIP, Aggregation laeuft trotzdem.
DB_OK=1
if [ "$DRY" = "0" ] && [ ! -f "$DUCKDB_PATH" ]; then
  DB_OK=0
  echo "WARNUNG: DuckDB fehlt ($DUCKDB_PATH) - HANDOFF_DUCKDB setzen oder Pfad oben anpassen" | tee -a "$MAIN_LOG"
fi

# -- Block 1: H-04 C-17/C-41 Lead-Lag ------------------------------------
# --db-copy: Temp-Kopie der DuckDB lesen (lock-frei gegen den laufenden 1.0-
# Collector). --max-ticks-per-window=150000 ist DEC-10-Daten-Scoping; die
# H-04-Gate-Schwellen bleiben unveraendert. Lag-Universum kommt aus dem Driver
# (DEFAULT_LAGS) - KEIN CLI-Override, da im Driver vorregistriert.
if [ "$DB_OK" -eq 0 ]; then
  record H04 SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH)"
else
  run_step H04 "$TMO_H04" \
    "$PY" "$REPO_ROOT/scripts/c17_c41_lead_lag.py" \
    --db "$DUCKDB_PATH" --pair "$PAIR" \
    --windows "$N_WINDOWS" --surrogates "$N_SURROGATES" --seed "$SEED" \
    --db-copy --max-ticks-per-window "$MAX_TICKS" \
    --out "$RUN_DIR/h04" || true
fi

# -- Block 2: H-05 C-01 OFI-Vorzeichen ----------------------------------
# delta-Lag-Universum (1,5,15,60,300s) ist im Driver vorregistriert - kein
# CLI-Override hier. --max-ticks-per-window=150000 = DEC-11-Daten-Scoping.
if [ "$DB_OK" -eq 0 ]; then
  record H05 SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH)"
else
  run_step H05 "$TMO_H05" \
    "$PY" "$REPO_ROOT/scripts/c01_ofi_sign.py" \
    --db "$DUCKDB_PATH" --symbols "$SYMBOLS" \
    --windows "$N_WINDOWS" --surrogates "$N_SURROGATES" --seed "$SEED" \
    --db-copy --max-ticks-per-window "$MAX_TICKS" \
    --out "$RUN_DIR/h05" || true
fi

# -- Block 3: H-06 C-07 Permutation Entropy ------------------------------
# m=4/tau=1 sind read-only Konstanten im Driver (PE_M/PE_TAU), KEIN CLI-Flag.
# --max-bars-per-window=43200 (30 Tage) = DEC-12-Stationaritaets-Scoping.
if [ "$DB_OK" -eq 0 ]; then
  record H06 SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH)"
else
  run_step H06 "$TMO_H06" \
    "$PY" "$REPO_ROOT/scripts/c07_pe.py" \
    --db "$DUCKDB_PATH" --symbols "$SYMBOLS" \
    --windows "$N_WINDOWS" --surrogates "$N_SURROGATES" --seed "$SEED" \
    --db-copy --max-bars-per-window "$MAX_BARS" \
    --out "$RUN_DIR/h06" || true
fi

# -- Block 4: F-WAVE2 zweistufige BH-FDR-Aggregation ---------------------
SUMMARY_DATE="$(date -u +%F)"
run_step WAVE2_FDR "$TMO_AGG" \
  "$PY" "$SCRIPT_DIR/aggregate_wave2_fdr.py" \
  --h04 "$RUN_DIR/h04" --h05 "$RUN_DIR/h05" --h06 "$RUN_DIR/h06" \
  --out "$RUN_DIR/WAVE2_SUMMARY.md" \
  --json "$RUN_DIR/wave2_summary.json" \
  --label "wave2_$TS" || true

# -- SUMMARY_<datum>.md zusaetzlich (T3-Konvention, Block-Status-Tabelle) -
# Nicht-kritisch: greift auf aggregate_results.py zu (Welle-1-Aggregator, der
# nur die steps.tsv-Tabelle braucht - die H-Sektionen bleiben leer/nicht
# relevant). Wenn er fehlschlaegt, ist das ok - WAVE2_SUMMARY.md ist die
# verbindliche Welle-2-Auswertung.
if [ -f "$SCRIPT_DIR/aggregate_results.py" ]; then
  "$PY" "$SCRIPT_DIR/aggregate_results.py" --run-dir "$RUN_DIR" \
    --label wave2 --date "$SUMMARY_DATE" >> "$MAIN_LOG" 2>&1 \
    && record SUMMARY OK 0 0 "results/SUMMARY_${SUMMARY_DATE}.md geschrieben" 1 \
    || record SUMMARY SKIP 0 0 "Welle-1-aggregate_results.py n/a fuer Welle 2 - WAVE2_SUMMARY.md ist verbindlich" 1
fi

# -- Gesamt-Summary -----------------------------------------------------
EXIT=0
[ "$N_SKIP" -gt 0 ] && EXIT=2
[ "$N_FAIL" -gt 0 ] && EXIT=1
{
  echo "-------- RUN_WAVE2 SUMMARY --------"
  printf '%s' "$SUMMARY_LINES"
  echo "RUN_WAVE2 GESAMT: ok=$N_OK fail=$N_FAIL skip=$N_SKIP -> exit $EXIT | Ergebnisse: $RUN_DIR"
  echo "F-WAVE2-Aggregat: $RUN_DIR/WAVE2_SUMMARY.md (Morgen-Auswertung gate-auditor)"
} | tee "$RUN_DIR/summary.txt" | tee -a "$MAIN_LOG"
exit "$EXIT"
