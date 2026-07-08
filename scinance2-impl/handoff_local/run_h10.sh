#!/usr/bin/env bash
# ========================================================================
# run_h10.sh - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 4, H-10)
#
# Linux/macOS-Geschwister von run_h10.ps1. H-10 = C-10 Cross-Stream-
# Pointer-Days + Pre-Event-Drift (F-POINTER) auf dem read-only
# Harvester-Baum (data/harvest). Stufe 1: Pointer-Tage (>=60% von 30
# Serien gleichzeitig |Cropper-C|>=1.5 gleicher Richtung, n_avail>=18)
# vs. zirkulaere Surrogat-Null. Stufe 2: Pre-Event-Drift des GEHALTENEN
# Deribit-dvol-Index (BTC+ETH, NIE in der Detektion) vs. Permutations-
# Null (>=6 Tage Abstand zu jedem Pointer-Tag). KAPITALFREI: reine
# Mess-/Existenzfrage, KEINE Kapital-Metriken.
#
#   bash scinance2-impl/handoff_local/run_h10.sh
#
# Datenbasis (Registry H-10, vorregistriert): 30 Detektions-Serien =
# 5 Perp-Symbole x {bybit,binance} x {RV(publicTrade),
# Funding(rest.fundingRate), dlogOI(rest.openInterest)}; Hold-out
# deribit/dvol BTC+ETH. Tagesraster 2026-03-27..2026-07-04, Burn-in 21:
#   W1: 2026-04-17..2026-05-25 (39 Tage)
#   W2: 2026-05-26..2026-07-04 (40 Tage)
# Surrogate/Permutationen 1000/1000, F-POINTER BH-FDR a=0.10.
# Gate-neutral - gate-auditor urteilt.
#
# EIN Block: H10_POINTER. Env: HARVEST_DIR, HANDOFF_DRY_RUN (+HANDOFF_DRY_RC).
# Exit: 0=OK 1=FAIL 2=SKIP.
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
DATA_START="2026-03-27"; DATA_END="2026-07-04"; BURN_IN=21
W1_START="2026-04-17"; W1_END="2026-05-25"
W2_START="2026-05-26"; W2_END="2026-07-04"
SURROGATES=1000; PERMUT=1000; SEED=42; TMO=2400

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h10_$TS"
mkdir -p "$RUN/h10"
STEPS="$RUN/steps.tsv"
rec() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$STEPS"; }

OKN=0; FN=0; SK=0
step() {
    local name="$1"; shift
    local log="$RUN/$name.log"; local err="$RUN/$name.err.log"
    echo "[$(date +%H:%M:%S)] START $name"
    local t0; t0=$(date +%s); local rc=-1; local detail=""
    if [ "$DRY" = "1" ]; then echo "[DRY-RUN] $*" >> "$log"; rc="$DRY_RC"; detail="dry-run rc=$rc"
    else
        if command -v timeout >/dev/null 2>&1; then timeout "$TMO" "$PY" "$@" >"$log" 2>"$err"; rc=$?
        else "$PY" "$@" >"$log" 2>"$err"; rc=$?; fi
        if [ "$rc" = "124" ]; then detail="TIMEOUT ${TMO}s"; else detail="rc=$rc"; fi
    fi
    local t1; t1=$(date +%s); local dur=$((t1-t0))
    local st="FAIL"; if [ "$rc" = "0" ]; then st="OK"; OKN=$((OKN+1)); else FN=$((FN+1)); fi
    rec "$name" "$st" "$rc" "$dur" "$detail"
    echo "[$(date +%H:%M:%S)] END   $name: $st ($detail, ${dur}s)"
}

echo "RUN_H10 (T2) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Panel: $SYMBOLS x {bybit,binance} x {RV,Funding,dlogOI} | Hold-out deribit/dvol BTC+ETH"
echo "Raster: $DATA_START..$DATA_END (Burn-in $BURN_IN) | W1 $W1_START..$W1_END | W2 $W2_START..$W2_END | surr/perm $SURROGATES/$PERMUT seed=$SEED"
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

# WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-Bug meiden).
SCRIPT="$REPO_ROOT/scripts/c10_pointer.py"
TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"
DVOL_PATH="$HARVEST_DIR/raw/deribit/dvol"
# audit_h10 BUG-5: der alte Pre-Check deckte nur 2 der 4 benoetigten Pfade ab
# (Bybit-Detektion + Hold-out). Ohne Binance-Funding/OI waere ein fehlender
# Binance-Zweig erst nach dem vollen Lauf im Payload sichtbar statt als
# sauberes SKIP vorab.
FUND_PATH="$HARVEST_DIR/raw/binance/rest.fundingRate"
OI_PATH="$HARVEST_DIR/raw/binance/rest.openInterest"

if [ "$DRY" != "1" ] && { [ ! -d "$TRADE_PATH" ] || [ ! -d "$DVOL_PATH" ] \
        || [ ! -d "$FUND_PATH" ] || [ ! -d "$OI_PATH" ]; }; then
    echo "WARNUNG: Harvester-/Hold-out-Pfad fehlt (bybit publicTrade=$TRADE_PATH, deribit dvol=$DVOL_PATH, binance fundingRate=$FUND_PATH, binance openInterest=$OI_PATH) - Junction data/harvest pruefen oder HARVEST_DIR setzen"
    rec "H10_POINTER" "SKIP" "0" "0" "Harvester/Hold-out fehlt"; SK=$((SK+1))
else
    step H10_POINTER "$SCRIPT" \
        --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
        --data-start "$DATA_START" --data-end "$DATA_END" \
        --burn-in-days "$BURN_IN" \
        --w1-start "$W1_START" --w1-end "$W1_END" \
        --w2-start "$W2_START" --w2-end "$W2_END" \
        --n-surrogates "$SURROGATES" --n-permutations "$PERMUT" \
        --seed "$SEED" --out-dir "$RUN/h10"
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-10 C-10 Cross-Stream-Pointer-Days + Pre-Event-Drift Mess-Gate - T2"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\` | Harvest \`$HARVEST_DIR\` (read-only)"
    echo "- **Panel:** $SYMBOLS x {bybit,binance} x {RV,Funding,dlogOI} | Hold-out (NIE in Detektion): deribit/dvol BTC+ETH"
    echo "- **Raster:** $DATA_START..$DATA_END (Burn-in $BURN_IN) | W1 $W1_START..$W1_END | W2 $W2_START..$W2_END"
    echo "- **Surrogate/Permutationen $SURROGATES/$PERMUT | F-POINTER BH-FDR a=0.10 | N-Floor 3 (NICHT absenkbar)**"
    echo "- **KAPITALFREI** - reine Mess-/Existenzfrage, KEINE Kapital-Metriken."
    echo ""
    echo "## Schritte"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    echo "*Gate-Urteil: gate-auditor gegen H-10 (h10/c10_pointer_results.json). WEITER verlangt"
    echo "nach BH-FDR a=0.10 ueber F-POINTER ALLE 4 Zellen: Stufe-1-Surrogat-p<=0.05 in W1 UND W2"
    echo "UND N_pointer>=3 je Fenster (Floor NICHT absenkbar) UND Stufe-2-Permutations-p<=0.05"
    echo "(zweiseitig) in W1 UND W2. Hartes Ein-Fenster-DROP, kein GRAUBEREICH."
    echo "A-priori: Stufe 1 WEITER-nah, Stufe 2 DROP erwartet. Ergebnisse hochladen -> GL-Zaehlung.*"
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
