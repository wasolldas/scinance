#!/usr/bin/env bash
# ========================================================================
# run_wave4.sh - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 4, Phase E)
#
# Ein Befehl, keine Pflicht-Parameter, laeuft UNBEAUFSICHTIGT. Bricht NIE
# mit offenem Prompt ab; jeder Teilschritt hat Timeout + Fehler-Kapselung
# und der Lauf faehrt fort.
#
# Bloecke (jeder einzeln gekapselt, try/catch + Timeout + weitermachen):
#   H11_UNLOCK_CHECK  H-11 Entsperr-Check (--check-unlock-only; DATA-GATED,
#                     Manifest-Coverage >=730 Tage; rc 2 = gesperrt -> SKIP)
#   H13_UNLOCK_CHECK  H-13 Entsperr-Check (--check-unlock-only; DATA-GATED,
#                     2 vol-regime-disjunkte IV-Snapshot-Tage; rc 2 = SKIP)
#   H09               Risk-Limit-Tier-Bunching (F-BUNCH, 5 Symbole x 2
#                     Fenster, 500 Bootstrap) - KAPITALFREI
#   H10               Cross-Stream-Pointer-Days (F-POINTER, 30 Serien,
#                     dvol-Hold-out, 1000 Surrogate/Permutationen) - KAPITALFREI
#   H12               Cross-Exchange-Fragmentierung (F-FRAG, 6 Serien,
#                     1000 MC-Reps PRO TAG - laengster Block!) - KAPITALFREI
#   H11               AnEn vs. HAR-RV - NUR wenn Entsperr-Check rc 0
#   H13               Tail-Form xi_P vs. xi_Q - NUR wenn Entsperr-Check rc 0
#   WAVE4_FDR         F-XDOM1 zweistufige BH-FDR-Aggregation ueber die
#                     Kohorte H-09/H-10/H-12 (Registry F-XDOM1, DEC-22)
#
# WICHTIG: H-11/H-13 sind GESPERRT registriert; ein SKIP mit Diagnose ist
# der ERWARTETE, korrekte Ausgang (kein Datenzugriff, kein Verdikt).
# Die Kohorten-Regel der Registry verlangt F-XDOM1 VOR diesem Lauf -
# registriert 2026-07-08 (hypothesis_registry.md, DEC-22).
#
# Exit-Code: 0 = alle Bloecke OK * 1 = mind. ein FAIL * 2 = kein FAIL, aber SKIP
# Ergebnisse: scinance2-impl/handoff_local/results/wave4_<timestamp>/
#             + WAVE4_SUMMARY.md + SUMMARY_<datum>.md (Morgen-Auswertung)
#
# Voraussetzung: read-only Harvester-Junction data/harvest (Override via
# HARVEST_DIR). Optionale Env-Overrides (KEINE Pflicht):
#   HARVEST_DIR=<pfad>
#   HANDOFF_DRY_RUN=1 (Mechanik-Test ohne echte Laeufe; HANDOFF_DRY_RC=1 ->
#   FAILs). WAVE4_FDR laeuft auch im Dry-Run ECHT (reine lokale JSON-
#   Aggregation ohne Datenzugriff) - WAVE4_SUMMARY.md entsteht IMMER.
# ========================================================================
set -u

# -- Pfade (bei Bedarf HIER anpassen - siehe README_WAVE4.md) ------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

# Registrierte Default-Parameter (identisch zu den auditierten T2-Runnern
# run_h09/run_h10/run_h11/run_h12/run_h13 - KEINE Abweichung).
SYMBOLS5="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
SYMBOLS2="BTCUSDT,ETHUSDT"
SYMBOLS_H13="BTC,ETH"
EXCHANGES_H12="bybit,binance,deribit"
SEED=42
# H-09 (Registry-Fenster, identisch H-12):
H09_WA_START="2026-03-27"; H09_WA_END="2026-05-15"
H09_WB_START="2026-05-16"; H09_WB_END="2026-07-04"
H09_BOOT=500
# H-10 (Tagesraster + Burn-in + Registry-Fenster):
H10_DATA_START="2026-03-27"; H10_DATA_END="2026-07-04"; H10_BURN_IN=21
H10_W1_START="2026-04-17"; H10_W1_END="2026-05-25"
H10_W2_START="2026-05-26"; H10_W2_END="2026-07-04"
H10_SURR=1000; H10_PERM=1000
# H-11 (data-gated; Parameter nur fuer den Fall der Entsperrung):
H11_TUNE_START="2024-03-27"; H11_TUNE_END="2025-09-30"
H11_W1_START="2025-10-01";   H11_W1_END="2026-03-26"
H11_W2_START="2026-03-27";   H11_W2_END="2026-06-30"
H11_UNLOCK_START="2024-03-27"; H11_UNLOCK_END="2026-03-26"; H11_MIN_UNLOCK=730
H11_K=20; H11_EMBARGO=30; H11_GRID="0,0.5,1,1.5,2"
H11_BLOCK=5; H11_BOOT=1000
# H-12 (Registry-Fenster identisch H-09):
H12_N_MC=1000
# H-13 (data-gated; Parameter nur fuer den Fall der Entsperrung):
H13_BOOT=500; H13_TRAIL_DAYS=60; H13_SNAP_HOUR=8

# Per-Schritt-Budgets (grosszuegig, aber endlich; CLAUDE.md T3-Regel).
# H-12 ist laut README_H12.md der rechenintensivste Block (1000 MC-Reps PRO
# gueltigem Tag, ~70-100 Tage => genannt 20-40 min, T2-Budget 2400 s) -
# hier mit ECHTER Marge auf 7200 s (2 h) gedeckelt.
TMO_UNLOCK_H11=600    # 10 min - Manifest-Query/Ordner-Scan
TMO_UNLOCK_H13=900    # 15 min - deterministische D1/D2-Suche
TMO_H09=7200          # 120 min - DuckDB-Aggregation + 500 Bootstrap x 10 Zellen
TMO_H10=3600          # 60 min - 30 Serien x ~100 Tage, 1000 Surrogate
TMO_H12=7200          # 120 min - ~70-100 Tage x 1000 MC-Reps (laengster Block)
TMO_H11=3600          # 60 min - nur bei Entsperrung
TMO_H13=3600          # 60 min - nur bei Entsperrung
TMO_AGG=600           # 10 min - reine JSON-Aggregation

# -- Umgebung ------------------------------------------------------------
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
fi
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
renice -n 10 $$ >/dev/null 2>&1 || true   # Ressourcen-Disziplin

DRY="${HANDOFF_DRY_RUN:-0}"
DRY_RC="${HANDOFF_DRY_RC:-0}"
TIMEOUT_BIN=""
command -v timeout >/dev/null 2>&1 && TIMEOUT_BIN="timeout"

TS="$(date -u +%Y%m%d_%H%M%S)"
SUMMARY_DATE="$(date -u +%F)"
RUN_DIR="$SCRIPT_DIR/results/wave4_$TS"
mkdir -p "$RUN_DIR" "$RUN_DIR/h09" "$RUN_DIR/h10" "$RUN_DIR/h11" "$RUN_DIR/h12" "$RUN_DIR/h13"
STEPS_TSV="$RUN_DIR/steps.tsv"
MAIN_LOG="$RUN_DIR/run_wave4.log"

N_OK=0; N_FAIL=0; N_SKIP=0
SUMMARY_LINES=""

record() { # <name> <status> <rc> <dur_s> <detail>
  local name="$1" status="$2" rc="$3" dur="$4" detail="$5"
  printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$status" "$rc" "$dur" "$detail" >> "$STEPS_TSV"
  SUMMARY_LINES="${SUMMARY_LINES}${name}: ${status} (${detail})
"
  case "$status" in
    OK)   N_OK=$((N_OK+1)) ;;
    FAIL) N_FAIL=$((N_FAIL+1)) ;;
    SKIP) N_SKIP=$((N_SKIP+1)) ;;
  esac
}

# run_step <name> <timeout_s> <skip_rc|-> <force_real 0|1> <skip_detail|-> <cmd...>
# Kapselt, loggt, faehrt IMMER fort. skip_rc: dieser Exit-Code zaehlt als
# SKIP statt FAIL (Entsperr-Checks: rc 2 = gesperrt). force_real=1: Schritt
# laeuft auch im Dry-Run echt (nur fuer die lokale Aggregation).
STEP_RC=-1
run_step() {
  local name="$1" tmo="$2" skip_rc="$3" force_real="$4" skip_detail="$5"; shift 5
  local log="$RUN_DIR/${name}.log" rc detail="" t0 t1 status
  echo "[$(date -u '+%H:%M:%S')] START $name: $*" | tee -a "$MAIN_LOG"
  t0=$(date +%s)
  if [ "$DRY" != "0" ] && [ "$force_real" != "1" ]; then
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
  status=FAIL
  if [ "$rc" -eq 0 ]; then status=OK
  elif [ "$skip_rc" != "-" ] && [ "$rc" = "$skip_rc" ]; then
    status=SKIP
    [ "$skip_detail" != "-" ] && detail="$skip_detail"
  fi
  [ -z "$detail" ] && detail="rc=$rc"
  record "$name" "$status" "$rc" "$((t1-t0))" "$detail"
  echo "[$(date -u '+%H:%M:%S')] END   $name: $status ($detail, $((t1-t0))s) log=$log" | tee -a "$MAIN_LOG"
  STEP_RC="$rc"
  return 0
}

echo "RUN_WAVE4 (T3) - Repo: $REPO_ROOT - Ergebnisse: $RUN_DIR" | tee -a "$MAIN_LOG"
echo "Harvest: $HARVEST_DIR (read-only Junction) | Seed: $SEED" | tee -a "$MAIN_LOG"
echo "Kohorte: H-09 + H-10 + H-12 (F-XDOM1 vorregistriert, DEC-22)" | tee -a "$MAIN_LOG"
echo "Data-gated: H-11 + H-13 (Entsperr-Check zuerst; SKIP = erwarteter Ausgang)" | tee -a "$MAIN_LOG"
[ "$DRY" != "0" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Modul-Laeufe (Aggregation laeuft echt)." | tee -a "$MAIN_LOG"

# Datenpfade (je Modul die Pfade der auditierten T2-Runner):
TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"
BINANCE_TRADE_PATH="$HARVEST_DIR/raw/binance/publicTrade"
DERIBIT_TRADE_PATH="$HARVEST_DIR/raw/deribit/publicTrade"
DVOL_PATH="$HARVEST_DIR/raw/deribit/dvol"
BINANCE_FUND_PATH="$HARVEST_DIR/raw/binance/rest.fundingRate"
BINANCE_OI_PATH="$HARVEST_DIR/raw/binance/rest.openInterest"
OPT_PATH="$HARVEST_DIR/raw/deribit/markprice.options"

# WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags
# (Vorbild run_h08..run_h13; NICHT den run_h05c-Bug wiederholen).

# -- Block 1: H-11 Entsperr-Check (DATA-GATED, GESPERRT registriert) ------
# rc 0 = entsperrt, rc 2 = gesperrt (SKIP, erwarteter Ausgang), sonst FAIL.
H11_LOCKED=1
if [ "$DRY" = "0" ] && [ ! -d "$TRADE_PATH" ]; then
  record H11_UNLOCK_CHECK SKIP 2 0 "Harvester-Pfad fehlt ($TRADE_PATH) - Junction data/harvest pruefen oder HARVEST_DIR setzen"
else
  run_step H11_UNLOCK_CHECK "$TMO_UNLOCK_H11" 2 0 \
    "H-11 gesperrt - Manifest-Coverage <$H11_MIN_UNLOCK Tage, Entsperr-Bedingung nicht erfuellt" \
    "$PY" "$REPO_ROOT/scripts/c11_anen.py" \
    --check-unlock-only \
    --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS2" \
    --unlock-start "$H11_UNLOCK_START" --unlock-end "$H11_UNLOCK_END" \
    --min-unlock-days "$H11_MIN_UNLOCK"
  [ "$STEP_RC" = "0" ] && H11_LOCKED=0
fi

# -- Block 2: H-13 Entsperr-Check (DATA-GATED, GESPERRT registriert) ------
H13_LOCKED=1
if [ "$DRY" = "0" ] && { [ ! -d "$TRADE_PATH" ] || [ ! -d "$OPT_PATH" ]; }; then
  record H13_UNLOCK_CHECK SKIP 2 0 "Harvester-/Options-Pfad fehlt ($TRADE_PATH / $OPT_PATH)"
else
  run_step H13_UNLOCK_CHECK "$TMO_UNLOCK_H13" 2 0 \
    "H-13 gesperrt - keine 2 vol-regime-disjunkten Snapshot-Tage im Live-Fenster gefunden" \
    "$PY" "$REPO_ROOT/scripts/c13_tailshape.py" \
    --check-unlock-only \
    --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS_H13" \
    --snapshot-hour "$H13_SNAP_HOUR" --seed "$SEED" \
    --out-dir "$RUN_DIR/h13"
  [ "$STEP_RC" = "0" ] && H13_LOCKED=0
fi

# -- Block 3: H-09 Risk-Limit-Tier-Bunching (Kohorte) ---------------------
# K_s-PLATZHALTER-WARNUNG: nur BTCUSDT registry-beziffert; ETH/SOL/BNB/XRP
# Platzhalter (kinks.py) - der Driver setzt gate_valid_assumptions korrekt.
if [ "$DRY" = "0" ] && [ ! -d "$TRADE_PATH" ]; then
  record H09 SKIP 0 0 "Harvester-Pfad fehlt ($TRADE_PATH)"
else
  run_step H09 "$TMO_H09" - 0 - \
    "$PY" "$REPO_ROOT/scripts/c09_bunch.py" \
    --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS5" \
    --window-a-start "$H09_WA_START" --window-a-end "$H09_WA_END" \
    --window-b-start "$H09_WB_START" --window-b-end "$H09_WB_END" \
    --n-bootstrap "$H09_BOOT" --seed "$SEED" --out-dir "$RUN_DIR/h09"
fi

# -- Block 4: H-10 Cross-Stream-Pointer-Days (Kohorte) --------------------
# Alle 4 Datenpfade noetig (audit_h10 BUG-5): bybit-Detektion, dvol-Hold-out,
# binance funding + OI.
if [ "$DRY" = "0" ] && { [ ! -d "$TRADE_PATH" ] || [ ! -d "$DVOL_PATH" ] \
    || [ ! -d "$BINANCE_FUND_PATH" ] || [ ! -d "$BINANCE_OI_PATH" ]; }; then
  record H10 SKIP 0 0 "Harvester-/Hold-out-Pfad fehlt (bybit publicTrade / deribit dvol / binance fundingRate / binance openInterest)"
else
  run_step H10 "$TMO_H10" - 0 - \
    "$PY" "$REPO_ROOT/scripts/c10_pointer.py" \
    --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS5" \
    --data-start "$H10_DATA_START" --data-end "$H10_DATA_END" \
    --burn-in-days "$H10_BURN_IN" \
    --w1-start "$H10_W1_START" --w1-end "$H10_W1_END" \
    --w2-start "$H10_W2_START" --w2-end "$H10_W2_END" \
    --n-surrogates "$H10_SURR" --n-permutations "$H10_PERM" \
    --seed "$SEED" --out-dir "$RUN_DIR/h10"
fi

# -- Block 5: H-12 Cross-Exchange-Fragmentierung (Kohorte, laengster Block)
if [ "$DRY" = "0" ] && { [ ! -d "$TRADE_PATH" ] || [ ! -d "$BINANCE_TRADE_PATH" ] \
    || [ ! -d "$DERIBIT_TRADE_PATH" ]; }; then
  record H12 SKIP 0 0 "Harvester-Pfad fehlt (bybit/binance/deribit publicTrade)"
else
  run_step H12 "$TMO_H12" - 0 - \
    "$PY" "$REPO_ROOT/scripts/c12_frag.py" \
    --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS2" --exchanges "$EXCHANGES_H12" \
    --window-a-start "$H09_WA_START" --window-a-end "$H09_WA_END" \
    --window-b-start "$H09_WB_START" --window-b-end "$H09_WB_END" \
    --n-mc "$H12_N_MC" --seed "$SEED" --out-dir "$RUN_DIR/h12"
fi

# -- Block 6: H-11 voller Lauf - NUR bei bestandenem Entsperr-Check -------
if [ "$H11_LOCKED" = "1" ]; then
  record H11 SKIP 2 0 "H-11 gesperrt - Entsperr-Bedingung nicht erfuellt (kein Datenlauf, kein Gate-Urteil; erwarteter Ausgang)"
else
  run_step H11 "$TMO_H11" 2 0 \
    "H-11 gesperrt - Entsperr-Bedingung nicht erfuellt" \
    "$PY" "$REPO_ROOT/scripts/c11_anen.py" \
    --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS2" \
    --tune-start "$H11_TUNE_START" --tune-end "$H11_TUNE_END" \
    --w1-start "$H11_W1_START" --w1-end "$H11_W1_END" \
    --w2-start "$H11_W2_START" --w2-end "$H11_W2_END" \
    --unlock-start "$H11_UNLOCK_START" --unlock-end "$H11_UNLOCK_END" \
    --min-unlock-days "$H11_MIN_UNLOCK" \
    --k "$H11_K" --embargo-days "$H11_EMBARGO" \
    --weight-grid "$H11_GRID" \
    --block-len "$H11_BLOCK" --n-bootstrap "$H11_BOOT" \
    --seed "$SEED" --out-dir "$RUN_DIR/h11"
fi

# -- Block 7: H-13 voller Lauf - NUR bei bestandenem Entsperr-Check -------
if [ "$H13_LOCKED" = "1" ]; then
  record H13 SKIP 2 0 "H-13 gesperrt - keine 2 vol-regime-disjunkten Snapshot-Tage (kein Fit, kein Gate-Urteil; erwarteter Ausgang)"
else
  run_step H13 "$TMO_H13" 2 0 \
    "H-13 gesperrt - keine 2 vol-regime-disjunkten Snapshot-Tage" \
    "$PY" "$REPO_ROOT/scripts/c13_tailshape.py" \
    --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS_H13" \
    --n-bootstrap "$H13_BOOT" --trailing-days "$H13_TRAIL_DAYS" \
    --snapshot-hour "$H13_SNAP_HOUR" --seed "$SEED" \
    --out-dir "$RUN_DIR/h13"
fi

# -- Block 8: F-XDOM1 zweistufige BH-FDR-Aggregation ----------------------
# Laeuft IMMER echt (auch im Dry-Run und bei fehlenden Driver-Outputs):
# reine lokale JSON-Aggregation ohne Datenzugriff; fehlende Driver werden
# als Luecke im Bericht dokumentiert, nie als Absturz.
run_step WAVE4_FDR "$TMO_AGG" - 1 - \
  "$PY" "$SCRIPT_DIR/aggregate_wave4_fdr.py" \
  --h09 "$RUN_DIR/h09" --h10 "$RUN_DIR/h10" --h12 "$RUN_DIR/h12" \
  --out "$RUN_DIR/WAVE4_SUMMARY.md" \
  --json "$RUN_DIR/wave4_summary.json" \
  --label "wave4_$TS"

# -- SUMMARY_<datum>.md (T3-Konvention, immer geschrieben) ----------------
EXIT=0
[ "$N_SKIP" -gt 0 ] && EXIT=2
[ "$N_FAIL" -gt 0 ] && EXIT=1
SUMMARY="$RUN_DIR/SUMMARY_$SUMMARY_DATE.md"
{
  echo "# Welle-4-Kohorten-Lauf (H-09/H-10/H-12 + Entsperr-Checks H-11/H-13) - T3"
  echo ""
  echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
  echo "- **Run-Dir:** \`$RUN_DIR\` | Harvest \`$HARVEST_DIR\` (read-only Junction)"
  echo "- **Kohorte:** H-09 (F-BUNCH) + H-10 (F-POINTER) + H-12 (F-FRAG); Ueber-Familie F-XDOM1"
  echo "  (zweite BH-FDR alpha=0.10 ueber die Stage-1-Survivor, Registry-Eintrag F-XDOM1/DEC-22,"
  echo "  VOR diesem Lauf registriert). Eine Hypothese besteht nur, wenn sie BEIDE Stufen ueberlebt."
  echo "- **Data-gated:** H-11 + H-13 - Entsperr-Check via --check-unlock-only; gesperrt -> sauberer"
  echo "  SKIP ohne Datenzugriff (erwarteter Ausgang, kein Fehler, kein Verdikt)."
  echo "- **KAPITALFREI** - alle 5 Module sind reine Mess-Gates ohne bps/Edge/PnL/Friction-Rechnung."
  echo ""
  echo "## Schritte"
  echo ""
  echo "| Schritt | Status | rc | Dauer | Detail |"
  echo "|---|---|---:|---:|---|"
  if [ -f "$STEPS_TSV" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS_TSV"; fi
  echo ""
  echo "**Gesamt:** ok=$N_OK fail=$N_FAIL skip=$N_SKIP -> exit $EXIT"
  echo ""
  echo "*F-XDOM1-Aggregat: \`WAVE4_SUMMARY.md\` + \`wave4_summary.json\` (gate-neutral, KEIN"
  echo "Gesamturteil). Gate-Urteile faellt der gate-auditor gegen H-09/H-10/H-12 unter der"
  echo "Beide-Stufen-Regel; Roh-JSONs unter h09/, h10/, h12/ (h11/, h13/ nur bei Entsperrung)."
  echo "Ergebnisse hochladen -> GL-014ff. (erster Welle-4-Lauf).*"
} > "$SUMMARY"

# -- Gesamt-Summary -------------------------------------------------------
{
  echo "-------- RUN_WAVE4 SUMMARY --------"
  printf '%s' "$SUMMARY_LINES"
  echo "RUN_WAVE4 GESAMT: ok=$N_OK fail=$N_FAIL skip=$N_SKIP -> exit $EXIT | Ergebnisse: $RUN_DIR"
  echo "F-XDOM1-Aggregat: $RUN_DIR/WAVE4_SUMMARY.md (Morgen-Auswertung gate-auditor)"
  echo "SUMMARY: $SUMMARY"
} | tee "$RUN_DIR/summary.txt" | tee -a "$MAIN_LOG"
exit "$EXIT"
