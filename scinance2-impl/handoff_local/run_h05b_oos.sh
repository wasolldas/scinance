#!/usr/bin/env bash
# ========================================================================
# run_h05b_oos.sh - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 3, H-05b OOS)
#
# Linux/macOS-Geschwister von run_h05b_oos.ps1. Gleiche Semantik:
# H-05b inverse OFI-Vorzeichen-Konfirmation auf read-only Harvester-Backfill
# (Junction/Pfad data/harvest), zwei vorregistrierte OOS-Fenster (DEC-15),
# 5 Symbole, delta {1,5,15,60,300}s, F-OFI-INV BH-FDR a=0.10. KAPITALFREI.
#
#   bash scinance2-impl/handoff_local/run_h05b_oos.sh
#
# Env-Overrides: HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC), PYTHON.
# Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP.
# ========================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
WIN_A_START="2026-04-15"
WIN_B_START="2026-05-15"
MAX_TICKS=300000
SURROGATES=200
SEED=42
TMO_STEP=2400

PYTHON_EXE="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"

DRY_RUN=0
if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY_RUN=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"
SUMMARY_DATE="$(date -u +%Y-%m-%d)"
RUN_DIR="$SCRIPT_DIR/results/h05b_oos_$TS"
mkdir -p "$RUN_DIR/h05b"
STEPS_TSV="$RUN_DIR/steps.tsv"

record_step() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$STEPS_TSV"; }

STATUS="FAIL"; RC=-1; DETAIL=""; DUR=0
run_step() {
    local name="$1"; local tmo="$2"; shift 2
    local log="$RUN_DIR/$name.log"; local errlog="$RUN_DIR/$name.err.log"
    echo "[$(date +%H:%M:%S)] START $name: $PYTHON_EXE $*"
    local t0; t0=$(date +%s)
    if [ "$DRY_RUN" = "1" ]; then
        echo "[DRY-RUN] $*" >> "$log"; RC="$DRY_RC"; DETAIL="dry-run rc=$RC"
    else
        if command -v timeout >/dev/null 2>&1; then
            timeout "$tmo" "$PYTHON_EXE" "$@" >"$log" 2>"$errlog"; RC=$?
        else
            "$PYTHON_EXE" "$@" >"$log" 2>"$errlog"; RC=$?
        fi
        if [ "$RC" = "124" ]; then DETAIL="TIMEOUT nach ${tmo}s"; else DETAIL="rc=$RC"; fi
    fi
    local t1; t1=$(date +%s); DUR=$((t1 - t0))
    if [ "$RC" = "0" ]; then STATUS="OK"; else STATUS="FAIL"; fi
    record_step "$name" "$STATUS" "$RC" "$DUR" "$DETAIL"
    echo "[$(date +%H:%M:%S)] END   $name: $STATUS ($DETAIL, ${DUR}s) log=$log"
}

echo "RUN_H05B_OOS (T2) - Repo: $REPO_ROOT - Ergebnisse: $RUN_DIR"
echo "Harvest: $HARVEST_DIR | Symbole: $SYMBOLS"
echo "Fenster A: $WIN_A_START | Fenster B: $WIN_B_START | max_ticks=$MAX_TICKS surrogates=$SURROGATES seed=$SEED"
[ "$DRY_RUN" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv - keine echten Laeufe."

OK=0; FAILN=0; SKIPN=0
TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"
if [ "$DRY_RUN" != "1" ] && [ ! -d "$TRADE_PATH" ]; then
    echo "WARNUNG: Harvester-Pfad fehlt ($TRADE_PATH) - Junction/HARVEST_DIR pruefen"
    record_step "H05B_OOS" "SKIP" "0" "0" "Harvester fehlt ($TRADE_PATH)"; SKIPN=1
else
    run_step "H05B_OOS" "$TMO_STEP" \
        "$REPO_ROOT/scripts/c01_ofi_sign_oos.py" \
        --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
        --window-a-start "$WIN_A_START" --window-b-start "$WIN_B_START" \
        --max-ticks "$MAX_TICKS" --n-surrogates "$SURROGATES" --seed "$SEED" \
        --out-dir "$RUN_DIR/h05b"
    if [ "$STATUS" = "OK" ]; then OK=1; else FAILN=1; fi
fi

EXIT=0
[ "$FAILN" -gt 0 ] && EXIT=1
[ "$FAILN" -eq 0 ] && [ "$SKIPN" -gt 0 ] && EXIT=2

SUMMARY="$RUN_DIR/SUMMARY_$SUMMARY_DATE.md"
{
    echo "# H-05b OOS-Konfirmation (C-01 inverse OFI-Vorzeichen) - T2"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN_DIR\`"
    echo "- **Harvest:** \`$HARVEST_DIR\` (read-only)"
    echo "- **Fenster (DEC-15):** A@$WIN_A_START + B@$WIN_B_START, je $MAX_TICKS Ticks/Symbol"
    echo "- **Symbole:** $SYMBOLS | delta {1,5,15,60,300}s | F-OFI-INV BH-FDR a=0.10"
    echo "- **KAPITALFREI** - Entdeckungszelle per Konstruktion ausgeschlossen."
    echo ""
    echo "**Gesamt:** ok=$OK fail=$FAILN skip=$SKIPN -> exit $EXIT"
    echo ""
    echo "*Gate-Urteil: gate-auditor gegen H-05b (Roh-JSON h05b/h05b_oos_results.json).*"
} > "$SUMMARY"

echo ""
echo "SUMMARY: $SUMMARY"
echo "Gesamt: ok=$OK fail=$FAILN skip=$SKIPN -> exit $EXIT"
exit "$EXIT"
