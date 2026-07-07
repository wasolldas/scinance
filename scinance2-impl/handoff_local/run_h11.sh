#!/usr/bin/env bash
# ========================================================================
# run_h11.sh - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 4, H-11)
#
# Linux/macOS-Geschwister von run_h11.ps1. H-11 = AnEn-Vol-Regime-Forecast
# vs. HAR-RV (IC-CLIM-1, 3-Tage-Horizont). KAPITALFREI: reines Mess-Gate
# (CRPS-Verteilungsvergleich), KEINE bps/Edge/PnL/Sharpe/Friction-Rechnung.
#
#   bash scinance2-impl/handoff_local/run_h11.sh
#
# WICHTIG - H-11 ist DATA-GATED (Registry: GESPERRT). Der Runner prueft
# ZUERST die Entsperr-Bedingung (lueckenlose date=-Partitionen fuer bybit
# publicTrade UND rest.fundingRate, BTC+ETH, 2024-03-27..2026-03-26,
# >=730 Tage). Nicht erfuellt -> sauberer SKIP ("H-11 gesperrt -
# Manifest-Coverage <730 Tage, Entsperr-Bedingung nicht erfuellt"),
# Exit 2, KEIN Fehler, KEIN Datenlauf.
#
# Nach Entsperrung: L=2024-03-27..2025-09-30 (LOO-CRPS-Gewichte, Grid
# {0;0.5;1;1.5;2}^5, eingefroren), W1=2025-10-01..2026-03-26,
# W2=2026-03-27..2026-06-30, k=20, 30-Tage-Embargo, Block-Bootstrap
# (5 Tage, 1000 Reps), F-ANEN BH-FDR a=0.10. Gate-neutral.
#
# Schritte: H11_UNLOCK_CHECK -> H11_ANEN.
# Env: HARVEST_DIR, H11_RESULTS_DIR, HANDOFF_DRY_RUN (+HANDOFF_DRY_RC).
# Exit: 0=OK 1=FAIL 2=SKIP.
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOLS="BTCUSDT,ETHUSDT"
TUNE_START="2024-03-27"; TUNE_END="2025-09-30"
W1_START="2025-10-01";   W1_END="2026-03-26"
W2_START="2026-03-27";   W2_END="2026-06-30"
UNLOCK_START="2024-03-27"; UNLOCK_END="2026-03-26"; MIN_UNLOCK=730
K_ANALOGS=20; EMBARGO=30; WEIGHT_GRID="0,0.5,1,1.5,2"
BLOCK_LEN=5; BOOT=1000; SEED=42
TMO_CHECK=300; TMO_STEP=3600

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RESULTS_BASE="${H11_RESULTS_DIR:-$SCRIPT_DIR/results}"
RUN="$RESULTS_BASE/h11_$TS"
mkdir -p "$RUN/h11"
STEPS="$RUN/steps.tsv"
rec() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$STEPS"; }

OKN=0; FN=0; SK=0
# step NAME TIMEOUT SKIP_RC CMD... -> globale Variable STEP_RC
STEP_RC=-1
step() {
    local name="$1"; local tmo="$2"; local skip_rc="$3"; shift 3
    local log="$RUN/$name.log"; local err="$RUN/$name.err.log"
    echo "[$(date +%H:%M:%S)] START $name"
    local t0; t0=$(date +%s); local rc=-1; local detail=""
    if [ "$DRY" = "1" ]; then echo "[DRY-RUN] $*" >> "$log"; rc="$DRY_RC"; detail="dry-run rc=$rc"
    else
        if command -v timeout >/dev/null 2>&1; then timeout "$tmo" "$PY" "$@" >"$log" 2>"$err"; rc=$?
        else "$PY" "$@" >"$log" 2>"$err"; rc=$?; fi
        if [ "$rc" = "124" ]; then detail="TIMEOUT ${tmo}s"; else detail="rc=$rc"; fi
    fi
    local t1; t1=$(date +%s); local dur=$((t1-t0))
    local st="FAIL"
    if [ "$rc" = "0" ]; then st="OK"; OKN=$((OKN+1))
    elif [ "$rc" = "$skip_rc" ]; then st="SKIP"; SK=$((SK+1))
    else FN=$((FN+1)); fi
    rec "$name" "$st" "$rc" "$dur" "$detail"
    echo "[$(date +%H:%M:%S)] END   $name: $st ($detail, ${dur}s)"
    STEP_RC="$rc"
}

echo "RUN_H11 (T2) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Symbole: $SYMBOLS | DATA-GATED (Entsperr-Check zuerst)"
echo "L=$TUNE_START..$TUNE_END | W1=$W1_START..$W1_END | W2=$W2_START..$W2_END | k=$K_ANALOGS Embargo=${EMBARGO}d seed=$SEED"
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

# WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags
# (Vorbild run_h08; NICHT den run_h05c-Bug wiederholen).
SCRIPT="$REPO_ROOT/scripts/c11_anen.py"
TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"
LOCKED=0

if [ "$DRY" != "1" ] && [ ! -d "$TRADE_PATH" ]; then
    echo "WARNUNG: Harvester-Pfad fehlt ($TRADE_PATH) - Junction data/harvest pruefen oder HARVEST_DIR setzen"
    rec "H11_UNLOCK_CHECK" "SKIP" "2" "0" "Harvester fehlt"; SK=$((SK+1)); LOCKED=1
else
    # Schritt 1: Entsperr-Bedingung pruefen (rc 0 = entsperrt, rc 2 = gesperrt).
    step H11_UNLOCK_CHECK "$TMO_CHECK" 2 "$SCRIPT" \
        --check-unlock-only \
        --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
        --unlock-start "$UNLOCK_START" --unlock-end "$UNLOCK_END" \
        --min-unlock-days "$MIN_UNLOCK"
    if [ "$STEP_RC" = "2" ]; then LOCKED=1
    elif [ "$STEP_RC" != "0" ]; then echo "FEHLER: Entsperr-Check fehlgeschlagen - kein Lauf."; fi
fi

if [ "$LOCKED" = "1" ]; then
    echo ""
    echo "H-11 gesperrt - Manifest-Coverage <${MIN_UNLOCK} Tage, Entsperr-Bedingung nicht erfuellt"
    echo "(lueckenlose done_days bybit publicTrade + rest.fundingRate, BTC+ETH,"
    echo " $UNLOCK_START..$UNLOCK_END noetig). Kein Datenlauf, kein Gate-Urteil."
    rec "H11_ANEN" "SKIP" "2" "0" "H-11 gesperrt - Entsperr-Bedingung nicht erfuellt"; SK=$((SK+1))
elif [ "$FN" = "0" ]; then
    # Schritt 2: voller Gate-Lauf (nur nach bestandenem Entsperr-Check).
    step H11_ANEN "$TMO_STEP" 2 "$SCRIPT" \
        --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
        --tune-start "$TUNE_START" --tune-end "$TUNE_END" \
        --w1-start "$W1_START" --w1-end "$W1_END" \
        --w2-start "$W2_START" --w2-end "$W2_END" \
        --unlock-start "$UNLOCK_START" --unlock-end "$UNLOCK_END" \
        --min-unlock-days "$MIN_UNLOCK" \
        --k "$K_ANALOGS" --embargo-days "$EMBARGO" \
        --weight-grid "$WEIGHT_GRID" \
        --block-len "$BLOCK_LEN" --n-bootstrap "$BOOT" \
        --seed "$SEED" --out-dir "$RUN/h11"
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-11 AnEn-Vol-Regime-Forecast vs. HAR-RV Mess-Gate - T2 (data-gated)"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\` | Harvest \`$HARVEST_DIR\` (read-only) | Symbole $SYMBOLS"
    echo "- **Entsperr-Bedingung:** lueckenlose date=-Partitionen publicTrade + rest.fundingRate, BTC+ETH, $UNLOCK_START..$UNLOCK_END (>=$MIN_UNLOCK Tage)"
    echo "- **Fenster:** L=$TUNE_START..$TUNE_END (Tuning) | W1=$W1_START..$W1_END | W2=$W2_START..$W2_END"
    echo "- **Methode:** k=$K_ANALOGS, Embargo ${EMBARGO}d, Grid {$WEIGHT_GRID}^5 eingefroren, Block-Bootstrap ${BLOCK_LEN}d x $BOOT | F-ANEN BH-FDR a=0.10"
    echo "- **KAPITALFREI** - reines Mess-Gate, KEINE bps/Edge/PnL/Sharpe/Friction-Rechnung."
    echo ""
    echo "## Schritte"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    if [ "$LOCKED" = "1" ]; then
        echo "**H-11 gesperrt - Manifest-Coverage <$MIN_UNLOCK Tage, Entsperr-Bedingung nicht erfuellt.**"
        echo "Kein Datenlauf, kein Gate-Urteil. Erneut pruefen, sobald der Deep-Backfill"
        echo "die Range $UNLOCK_START..$UNLOCK_END abdeckt (siehe README_H11.md)."
    else
        echo "*Gate-Urteil: gate-auditor gegen H-11 (h11/c11_anen_results.json). WEITER verlangt:"
        echo "fuer >=1 Symbol in {BTC,ETH} in BEIDEN Fenstern CRPSS>=0.05 UND Block-Bootstrap-"
        echo "p<=0.05 nach BH-FDR a=0.10 ueber F-ANEN. Hartes Ein-Fenster-DROP, kein GRAUBEREICH,"
        echo "keine k-/Gewichts-/Feature-Nachsuche. A-priori: DROP (HAR-RV ist ein notorisch"
        echo "harter Benchmark). Ergebnisse hochladen -> Gate-Log.*"
    fi
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
