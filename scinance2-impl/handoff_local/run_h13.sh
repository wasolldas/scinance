#!/usr/bin/env bash
# ========================================================================
# run_h13.sh - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 4, H-13)
#
# Linux/macOS-Geschwister von run_h13.ps1. H-13 = Tail-Form-Konsistenz:
# statistisches GPD-xi (xi_P, POT auf 1-min-Verlusten, Bybit publicTrade)
# vs. risikoneutraler Tail-Shape (xi_Q, Deribit markprice.options ->
# SVI -> Breeden-Litzenberger-RND -> GPD-PWM). KAPITALFREI: reine Mess-/
# Konsistenzfrage, KEINE Kosten-/Ertragsrechnung.
#
# DATA-GATED / GESPERRT: Entsperr-Bedingung sind 2 vol-regime-disjunkte
# Live-IV-Snapshot-Tage D1<D2 (|log(RV_5d-Ratio)|>=log(1.5), >=10 Kalender-
# tage Abstand, je Tag/Symbol >=12 Strikes mit 0.01<=|Delta|<=0.5 im
# 20-45-DTE-Tenor). Die D1/D2-Suche laeuft PROGRAMMATISCH; ohne gueltiges
# Paar -> sauberer SKIP (exit 2), kein Fit, kein Gate-Urteil.
#
#   bash scinance2-impl/handoff_local/run_h13.sh
#
# Ablauf: (1) H13_UNLOCK_CHECK via --check-unlock-only (rc 2 = gesperrt),
# (2) nur bei rc 0: H13_TAILSHAPE voller Lauf (500 Bootstrap-Reps je Seite,
# Seed 42, F-TAILSHAPE BH-FDR a=0.10). Gate-neutral - gate-auditor urteilt.
# Env: HARVEST_DIR, HANDOFF_DRY_RUN (+HANDOFF_DRY_RC).
# Exit: 0=OK 1=FAIL 2=SKIP (H-13 gesperrt).
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOLS="BTC,ETH"
BOOT=500; TRAIL_DAYS=60; SNAP_HOUR=8; SEED=42
TMO_UNLOCK=900; TMO_FULL=3600

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h13_$TS"
mkdir -p "$RUN/h13"
STEPS="$RUN/steps.tsv"
rec() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$STEPS"; }

SKIP_MSG="H-13 gesperrt - keine 2 vol-regime-disjunkten Snapshot-Tage im Live-Fenster gefunden"
OKN=0; FN=0; SK=0
LAST_RC=0
step() {
    # rc 2 des CLI = H-13 gesperrt -> Status SKIP (kein FAIL).
    local name="$1"; local tmo="$2"; shift 2
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
    elif [ "$rc" = "2" ]; then st="SKIP"; SK=$((SK+1)); detail="$SKIP_MSG"
    else FN=$((FN+1)); fi
    rec "$name" "$st" "$rc" "$dur" "$detail"
    echo "[$(date +%H:%M:%S)] END   $name: $st ($detail, ${dur}s)"
    LAST_RC="$rc"
}

echo "RUN_H13 (T2) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Symbole: $SYMBOLS | Bootstrap=$BOOT Seed=$SEED"
echo "H-13 ist DATA-GATED: erst deterministische D1/D2-Suche, dann (nur bei Entsperrung) voller Lauf."
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

# WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-rc=2-Bug meiden).
SCRIPT="$REPO_ROOT/scripts/c13_tailshape.py"
TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"
OPT_PATH="$HARVEST_DIR/raw/deribit/markprice.options"

if [ "$DRY" != "1" ] && { [ ! -d "$TRADE_PATH" ] || [ ! -d "$OPT_PATH" ]; }; then
    echo "WARNUNG: Harvester-/Options-Pfad fehlt ($TRADE_PATH / $OPT_PATH) - Junction data/harvest bzw. Live-Fenster pruefen"
    rec "H13_UNLOCK_CHECK" "SKIP" "0" "0" "Harvester-/Options-Pfad fehlt"; SK=$((SK+1))
else
    step H13_UNLOCK_CHECK "$TMO_UNLOCK" "$SCRIPT" \
        --check-unlock-only \
        --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
        --snapshot-hour "$SNAP_HOUR" --seed "$SEED" \
        --out-dir "$RUN/h13"
    if [ "$LAST_RC" = "0" ]; then
        step H13_TAILSHAPE "$TMO_FULL" "$SCRIPT" \
            --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
            --n-bootstrap "$BOOT" --trailing-days "$TRAIL_DAYS" \
            --snapshot-hour "$SNAP_HOUR" --seed "$SEED" \
            --out-dir "$RUN/h13"
    elif [ "$LAST_RC" = "2" ]; then
        echo "SKIP: $SKIP_MSG"
    fi
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-13 Tail-Form-Konsistenz xi_P vs. xi_Q Mess-Gate - T2 (data-gated)"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\` | Harvest \`$HARVEST_DIR\` (read-only) | Symbole $SYMBOLS"
    echo "- **Methodik (vorregistriert):** POT 99.5%-Quantil / GPD-MLE / 60-min-Block-Bootstrap / Hill; SVI -> BL-RND -> GPD-PWM / Strike-Bootstrap; Tenor 20-45 DTE, Delta 0.01-0.5, $BOOT Reps, Seed $SEED | F-TAILSHAPE BH-FDR a=0.10"
    echo "- **KAPITALFREI** - reine Mess-/Konsistenzfrage, KEINE Kosten-/Ertragsrechnung."
    echo "- **DATA-GATED** - Entsperr-Bedingung (waechst mit Kalenderzeit, wird NICHT gesenkt): 2 Snapshot-Tage D1<D2 mit |log(RV_5d-Ratio)|>=log(1.5), >=10 Tage Abstand, je >=12 Strikes im Delta-Band."
    echo ""
    echo "## Schritte"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    if [ "$EXIT" = "2" ]; then
        echo "*SKIP: $SKIP_MSG. H-13 bleibt GESPERRT - kein Fit, kein Gate-Urteil.*"
    else
        echo "*Gate-Urteil: gate-auditor gegen H-13 (h13/c13_tailshape_results.json). WEITER verlangt:"
        echo "fuer >=1 Symbol in {BTC,ETH} an BEIDEN Snapshot-Tagen sign(Delta_xi) identisch UND"
        echo "|Delta_xi|>=0.15 UND Bootstrap-p<=0.05 nach BH-FDR a=0.10 ueber F-TAILSHAPE UND"
        echo "Hill-Gegenprobe widerspricht dem GPD-Vorzeichen nicht. DROP sonst (hartes"
        echo "Ein-Fenster-/Ein-Tag-Kriterium, kein GRAUBEREICH; u_P, Tenor-Band, RND-Quantil und"
        echo "0.15 nicht verhandelbar). Ergebnisse hochladen -> Morgen-Auswertung.*"
    fi
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
