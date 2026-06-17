#!/usr/bin/env bash
# ========================================================================
# run_h04b.sh - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 2, H-04b Handoff)
#
# Ein Befehl, keine Pflicht-Parameter, laeuft ca. 10-30 min. Bricht NIE mit
# offenem Prompt ab; jeder Teilschritt hat Timeout + Fehler-Kapselung und der
# Lauf faehrt fort.
#
# H-04b = C-17/C-41 Lead-Lag-TRADABILITY-Gate (Paar BTC/ETH). Erste NICHT-
# kapitalfreie Hypothese: das Gate konfrontiert Edge-bps gegen die verbindliche
# 11-bps-Friction-Wand nach 300-ms-Latenz-Haircut. Es bleibt ein HISTORISCHER
# BACKTEST MIT KOSTENMODELL auf dem read-only trades-Bestand - KEIN Live-Order-
# Code, KEIN Geldeinsatz (CLAUDE.md Par.4 / Autonomie-Protokoll Par.3).
#
# Bloecke (jeder einzeln gekapselt, try/catch + Timeout + weitermachen):
#   H04B_PRIMARY   URTEILSTRAGEND: latency=300ms, friction=11bps, Taker (Default-
#                  Punkt). NUR an diesem Punkt faellt das Pass-Urteil (Anti-
#                  Gaming-Klausel registry H-04b, gate_valid_assumptions=true).
#   H04B_LAT100    ROBUSTHEIT (NICHT urteilstragend): latency=100ms.
#   H04B_LAT500    ROBUSTHEIT (NICHT urteilstragend): latency=500ms.
#   H04B_MAKER     SEKUNDAER (NICHT urteilstragend): --maker-secondary, adverse-
#                  selection-vorbehaltlich; gate_valid_assumptions=false.
#
# Die drei Robustheits-/Sekundaer-Bloecke setzen gate_valid_assumptions=false im
# Output und sind als Sensitivitaets-Spanne MIT-berichtet - sie duerfen ein
# WEITER NICHT erzwingen. Das Pass-Urteil faellt der gate-auditor AUSSCHLIESSLICH
# am H04B_PRIMARY-Punkt (300ms/11bps/Taker).
#
# Exit-Code: 0 = alle Bloecke OK * 1 = mind. ein FAIL * 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl/handoff_local/results/h04b_<timestamp>/
#             + SUMMARY_<datum>.md (Morgen-Auswertung durch gate-auditor)
#
# Voraussetzung: DuckDB-Bestand mit trades auf der User-Maschine
# (Default-Pfad data/bybit_edge.duckdb; Override via HANDOFF_DUCKDB).
#
# Optionale Env-Overrides (KEINE Pflicht):
#   HANDOFF_DUCKDB=<pfad>
#   HANDOFF_DRY_RUN=1 (Mechanik-Test ohne echte Laeufe; HANDOFF_DRY_RC=1 -> FAILs)
# ========================================================================
set -u

# -- Pfade (bei Bedarf HIER anpassen - siehe README_H04B.md) -------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DUCKDB_PATH="${HANDOFF_DUCKDB:-$REPO_ROOT/data/bybit_edge.duckdb}"

PAIR="BTCUSDT,ETHUSDT"
WINDOWS=2
LAGS="1,2,3"
FRICTION_BPS=11        # verbindliche Friction-Wand (verdict.md sek.2 Taker-Baseline)
LAT_PRIMARY=300        # URTEILSTRAGENDER Latenz-Default (DEC-13, Anti-Gaming)
LAT_LOW=100            # Robustheits-Spanne unten - NICHT urteilstragend
LAT_HIGH=500           # Robustheits-Spanne oben  - NICHT urteilstragend
BOOTSTRAP=200
SEED=42
MAX_TICKS=150000       # DEC-10-Daten-Scoping (Gate-Schwellen UNVERAENDERT)
GRID_MS=1000

# Per-Schritt-Budget (grosszuegig, aber endlich; CLAUDE.md T2/T3-Regel).
TMO_STEP=1800     # 30 min je Lauf

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
SUMMARY_DATE="$(date -u +%F)"
RUN_DIR="$SCRIPT_DIR/results/h04b_$TS"
mkdir -p "$RUN_DIR" "$RUN_DIR/h04b" "$RUN_DIR/h04b_lat100" "$RUN_DIR/h04b_lat500" "$RUN_DIR/h04b_maker"
STEPS_TSV="$RUN_DIR/steps.tsv"
MAIN_LOG="$RUN_DIR/run_h04b.log"

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

echo "RUN_H04B (T2) - Repo: $REPO_ROOT - Ergebnisse: $RUN_DIR" | tee -a "$MAIN_LOG"
echo "DuckDB: $DUCKDB_PATH | Paar: $PAIR | windows=$WINDOWS lags=$LAGS" | tee -a "$MAIN_LOG"
echo "URTEILSTRAGEND: latency=${LAT_PRIMARY}ms friction=${FRICTION_BPS}bps Taker | bootstrap=$BOOTSTRAP seed=$SEED" | tee -a "$MAIN_LOG"
echo "ROBUSTHEIT (NICHT urteilstragend): latency=${LAT_LOW}ms, latency=${LAT_HIGH}ms, --maker-secondary" | tee -a "$MAIN_LOG"
[ "$DRY" != "0" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe." | tee -a "$MAIN_LOG"

# DuckDB-Pruefung: fehlt -> alle Bloecke SKIP.
DB_OK=1
if [ "$DRY" = "0" ] && [ ! -f "$DUCKDB_PATH" ]; then
  DB_OK=0
  echo "WARNUNG: DuckDB fehlt ($DUCKDB_PATH) - HANDOFF_DUCKDB setzen oder Pfad oben anpassen" | tee -a "$MAIN_LOG"
fi

# -- Block 1: H04B_PRIMARY (URTEILSTRAGEND, 300ms/11bps/Taker) -----------
# --db-copy: Temp-Kopie der DuckDB lesen (lock-frei gegen den laufenden 1.0-
# Collector). Registry-konforme Defaults: latency=300, friction=11, Taker -
# die EINZIGEN Pass-gueltigen Werte. NICHT ueberschreiben (Anti-Gaming Par.2).
# --max-ticks-per-window=150000 ist DEC-10-Daten-Scoping; Gate-Schwellen UNVER-
# AENDERT. lags=1,2,3 = H-04-Survivor; horizon=lag im Driver vorab fixiert.
if [ "$DB_OK" -eq 0 ]; then
  record H04B_PRIMARY SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH)"
else
  run_step H04B_PRIMARY "$TMO_STEP" \
    "$PY" "$REPO_ROOT/scripts/c17_c41_tradability.py" \
    --db "$DUCKDB_PATH" --pair "$PAIR" \
    --windows "$WINDOWS" --lags "$LAGS" \
    --latency-ms "$LAT_PRIMARY" --friction-bps "$FRICTION_BPS" \
    --bootstrap "$BOOTSTRAP" --seed "$SEED" \
    --db-copy --max-ticks-per-window "$MAX_TICKS" --grid-ms "$GRID_MS" \
    --out "$RUN_DIR/h04b" || true
fi

# -- Block 2: H04B_LAT100 (ROBUSTHEIT - NICHT urteilstragend) ------------
# Sensitivitaets-Spanne untere Latenz. Setzt gate_valid_assumptions=false; ein
# WEITER hier zaehlt NICHT (kuerzere Latenz darf das WEITER nicht erzwingen,
# registry H-04b Anti-Gaming-Klausel).
if [ "$DB_OK" -eq 0 ]; then
  record H04B_LAT100 SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH)"
else
  run_step H04B_LAT100 "$TMO_STEP" \
    "$PY" "$REPO_ROOT/scripts/c17_c41_tradability.py" \
    --db "$DUCKDB_PATH" --pair "$PAIR" \
    --windows "$WINDOWS" --lags "$LAGS" \
    --latency-ms "$LAT_LOW" --friction-bps "$FRICTION_BPS" \
    --bootstrap "$BOOTSTRAP" --seed "$SEED" \
    --db-copy --max-ticks-per-window "$MAX_TICKS" --grid-ms "$GRID_MS" \
    --out "$RUN_DIR/h04b_lat100" || true
fi

# -- Block 3: H04B_LAT500 (ROBUSTHEIT - NICHT urteilstragend) ------------
# Sensitivitaets-Spanne obere Latenz. Setzt gate_valid_assumptions=false.
if [ "$DB_OK" -eq 0 ]; then
  record H04B_LAT500 SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH)"
else
  run_step H04B_LAT500 "$TMO_STEP" \
    "$PY" "$REPO_ROOT/scripts/c17_c41_tradability.py" \
    --db "$DUCKDB_PATH" --pair "$PAIR" \
    --windows "$WINDOWS" --lags "$LAGS" \
    --latency-ms "$LAT_HIGH" --friction-bps "$FRICTION_BPS" \
    --bootstrap "$BOOTSTRAP" --seed "$SEED" \
    --db-copy --max-ticks-per-window "$MAX_TICKS" --grid-ms "$GRID_MS" \
    --out "$RUN_DIR/h04b_lat500" || true
fi

# -- Block 4: H04B_MAKER (SEKUNDAER - NICHT urteilstragend) --------------
# Maker-Sekundaerfall: adverse-selection-vorbehaltlich (Maker-Fills auf einem
# 1-3s-Lead-Signal werden bevorzugt gefuellt, wenn man falsch liegt). NIE das
# Primaer-Pass-Kriterium; Driver setzt gate_valid_assumptions=false. Bei
# Default-Latenz 300ms gefahren, damit nur der Maker-Aspekt variiert.
if [ "$DB_OK" -eq 0 ]; then
  record H04B_MAKER SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH)"
else
  run_step H04B_MAKER "$TMO_STEP" \
    "$PY" "$REPO_ROOT/scripts/c17_c41_tradability.py" \
    --db "$DUCKDB_PATH" --pair "$PAIR" \
    --windows "$WINDOWS" --lags "$LAGS" \
    --latency-ms "$LAT_PRIMARY" --friction-bps "$FRICTION_BPS" --maker-secondary \
    --bootstrap "$BOOTSTRAP" --seed "$SEED" \
    --db-copy --max-ticks-per-window "$MAX_TICKS" --grid-ms "$GRID_MS" \
    --out "$RUN_DIR/h04b_maker" || true
fi

# -- Gesamt-Summary: 1 Zeile je Block + Exit-Code ------------------------
EXIT=0
[ "$N_SKIP" -gt 0 ] && EXIT=2
[ "$N_FAIL" -gt 0 ] && EXIT=1
{
  echo "-------- RUN_H04B SUMMARY --------"
  printf '%s' "$SUMMARY_LINES"
  echo "RUN_H04B GESAMT: ok=$N_OK fail=$N_FAIL skip=$N_SKIP -> exit $EXIT | Ergebnisse: $RUN_DIR"
  echo "URTEIL: NUR H04B_PRIMARY (300ms/11bps/Taker). Robustheit/Maker NICHT urteilstragend."
} | tee "$RUN_DIR/summary.txt" | tee -a "$MAIN_LOG"

# SUMMARY_<datum>.md (maschinen- und menschenlesbar fuer den gate-auditor)
{
  echo "# H-04b - C-17/C-41 Lead-Lag-TRADABILITY Runner (T2)"
  echo ""
  echo "- **Erzeugt:** $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
  echo "- **Run-Dir:** \`$RUN_DIR\`"
  echo "- **DuckDB:** \`$DUCKDB_PATH\`"
  echo "- **Paar:** $PAIR | windows=$WINDOWS | lags=$LAGS | bootstrap=$BOOTSTRAP | seed=$SEED"
  echo "- **capital_free = FALSE** (erste nicht-kapitalfreie Hypothese; aber HISTORISCHER"
  echo "  BACKTEST mit Kostenmodell auf read-only trades - KEIN Live-Order-Code, KEIN Geld)."
  echo ""
  echo "## Urteilstragender Punkt (Anti-Gaming-Klausel)"
  echo ""
  echo "Das H-04b-Pass-Urteil faellt **AUSSCHLIESSLICH** am Block **H04B_PRIMARY**"
  echo "(latency=${LAT_PRIMARY}ms, friction=${FRICTION_BPS}bps, Taker) - der EINZIGE Punkt mit"
  echo "\`gate_valid_assumptions=true\`. Die Bloecke H04B_LAT100 / H04B_LAT500 / H04B_MAKER"
  echo "sind **Robustheits-/Sekundaer-Laeufe (NICHT urteilstragend)**, MIT-berichtet als"
  echo "Sensitivitaets-Spanne; sie setzen \`gate_valid_assumptions=false\` und duerfen ein"
  echo "WEITER NICHT erzwingen (registry H-04b Anti-Gaming-Klausel)."
  echo ""
  echo "| Block | Rolle | Status | rc | Dauer | Detail |"
  echo "|---|---|---|---:|---:|---|"
  echo "| H04B_PRIMARY | URTEILSTRAGEND (300ms/11bps/Taker) | | | | |"
  echo "| H04B_LAT100 | Robustheit (NICHT urteilstragend) | | | | |"
  echo "| H04B_LAT500 | Robustheit (NICHT urteilstragend) | | | | |"
  echo "| H04B_MAKER | Sekundaer (NICHT urteilstragend) | | | | |"
  echo ""
  echo "### steps.tsv (Roh-Status je Block)"
  echo ""
  echo "| Block | Status | rc | Dauer | Detail |"
  echo "|---|---|---:|---:|---|"
  printf '%s' "$RESULT_ROWS"
  echo ""
  echo "**Gesamt:** ok=$N_OK fail=$N_FAIL skip=$N_SKIP -> exit $EXIT"
  echo ""
  echo "*H-04b-Gate-Urteil faellt der gate-auditor gegen die Registry (Roh-JSON unter"
  echo "\`h04b/c17_c41_tradability_results.json\`; das harte Ein-Fenster-PARK-Kriterium und"
  echo "die Anti-Gaming-Klausel gelten - WEITER nur am H04B_PRIMARY-Punkt).*"
} > "$RUN_DIR/SUMMARY_${SUMMARY_DATE}.md"

exit "$EXIT"
