#!/usr/bin/env bash
# ========================================================================
# run_h05c.sh - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 3, H-05c)
#
# Linux/macOS-Geschwister von run_h05c.ps1. H-05c OFI-Fade-Tradability auf
# read-only Harvester-Backfill (data/harvest), SOLUSDT, OOS-Fenster DEC-15,
# delta {1,5}s (GL-010-Survivor). capital_free=FALSE, aber Backtest mit
# Kostenmodell - KEIN Live-Order, KEIN Geld (CLAUDE.md §4). Kapital PARK.
#
#   bash scinance2-impl/handoff_local/run_h05c.sh
#
# Vier Bloecke: PRIMARY (300ms/11bps/Taker, urteilstragend) + LAT100/LAT500/
# MAKER (Robustheit, NICHT urteilstragend). Env: HARVEST_DIR, HANDOFF_DRY_RUN.
# Exit: 0=OK 1=FAIL 2=SKIP.
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOL="SOLUSDT"; WIN_A="2026-04-15"; WIN_B="2026-05-15"; DELTAS="1,5"
MAX_TICKS=300000; FRICTION=11; LAT_PRIMARY=300; LAT_LOW=100; LAT_HIGH=500
BOOT=200; SEED=42; TMO=2400

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h05c_$TS"
mkdir -p "$RUN/h05c" "$RUN/h05c_lat100" "$RUN/h05c_lat500" "$RUN/h05c_maker"
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

echo "RUN_H05C (T2) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Symbol: $SYMBOL | A@$WIN_A B@$WIN_B | delta $DELTAS"
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

SCRIPT="$REPO_ROOT/scripts/c01_ofi_tradability.py"
TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"
COMMON=(--base-dir "$HARVEST_DIR" --symbol "$SYMBOL" --window-a-start "$WIN_A" \
    --window-b-start "$WIN_B" --deltas "$DELTAS" --max-ticks "$MAX_TICKS" \
    --friction-bps "$FRICTION" --n-bootstrap "$BOOT" --seed "$SEED")

if [ "$DRY" != "1" ] && [ ! -d "$TRADE_PATH" ]; then
    echo "WARNUNG: Harvester-Pfad fehlt ($TRADE_PATH)"
    for n in H05C_PRIMARY H05C_LAT100 H05C_LAT500 H05C_MAKER; do rec "$n" "SKIP" "0" "0" "Harvester fehlt"; SK=$((SK+1)); done
else
    step H05C_PRIMARY "$SCRIPT" "${COMMON[@]}" --latency-ms "$LAT_PRIMARY" --out-dir "$RUN/h05c"
    step H05C_LAT100  "$SCRIPT" "${COMMON[@]}" --latency-ms "$LAT_LOW"  --out-dir "$RUN/h05c_lat100"
    step H05C_LAT500  "$SCRIPT" "${COMMON[@]}" --latency-ms "$LAT_HIGH" --out-dir "$RUN/h05c_lat500"
    step H05C_MAKER   "$SCRIPT" "${COMMON[@]}" --latency-ms "$LAT_PRIMARY" --maker-secondary --out-dir "$RUN/h05c_maker"
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-05c OFI-Fade-Tradability (C-01, SOLUSDT) - T2"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\`  | Harvest \`$HARVEST_DIR\` (read-only) | Symbol $SYMBOL"
    echo "- **Fenster (DEC-15):** A@$WIN_A + B@$WIN_B | delta ${DELTAS}s (GL-010-Survivor)"
    echo "- **capital_free=FALSE** - Backtest mit Kostenmodell, KEIN Live-Order/Geld. Kapital PARK."
    echo ""
    echo "Urteilstragend: H05C_PRIMARY (300ms/11bps/Taker). LAT100/LAT500/MAKER NICHT urteilstragend."
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    echo "*Gate-Urteil: gate-auditor gegen H-05c (h05c/h05c_results.json). Hartes Ein-Fenster-PARK, kein GRAUBEREICH.*"
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
