#!/usr/bin/env bash
# ========================================================================
# run_h09.sh - T2 LOCAL Runner (Scinance 2.0 Welle 4, H-09)
#
# Linux/macOS-Geschwister von run_h09.ps1. H-09 = Risk-Limit-Tier-Bunching
# (F-BUNCH, DEC-19, KAPITALFREI) auf read-only Harvester-Backfill
# (data/harvest). Taker-Order-Aggregate -> Notional-Binning um K_s (Band
# [0.4,1.3)*K_s, 90 Bins) -> Polynom-Grad-7-Counterfactual (Ausschluss
# [0.9,1.1)*K_s) -> Excess-Mass b- vs b+ -> Residuen-Bootstrap (500 Reps)
# -> Placebos 0.5/0.75*K_s (NICHT in FDR-Familie). KAPITALFREI: reiner
# Struktur-/Verhaltensfakt, KEINE Kosten-/Handelsspalten.
#
#   bash scinance2-impl/handoff_local/run_h09.sh
#
# !!! K_s-PLATZHALTER-WARNUNG: nur BTCUSDT=2.000.000 USDT ist registry-
# beziffert; ETH/SOL/BNB/XRP sind PLATZHALTER (src/bybit_edge/research/
# c09_bunch/kinks.py) - vor echtem Lauf gegen die aktuelle Bybit-Risk-
# Limit-Tabelle verifizieren (Konstanz ueber W1+W2!), DEC-09-Muster,
# datierter append-only Operationalisierungs-Nachtrag erforderlich. !!!
#
# Datenbasis (Registry H-09, vorregistriert): 5-Symbol-Panel BTC/ETH/SOL/
# BNB/XRP, zwei disjunkte Kalender-Fenster:
#   W1: 2026-03-27 .. 2026-05-15
#   W2: 2026-05-16 .. 2026-07-04
# N-Floor: >=2.000 Order-Beobachtungen im Band UND Counterfactual-
# Erwartung in B- >=50. F-BUNCH = 5x2 Zellen, BH-FDR a=0.10.
# Gate-neutral - gate-auditor urteilt.
#
# EIN Block: H09_BUNCH. Env: HARVEST_DIR, HANDOFF_DRY_RUN (+HANDOFF_DRY_RC).
# Exit: 0=OK 1=FAIL 2=SKIP.
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
WIN_A_START="2026-03-27"; WIN_A_END="2026-05-15"
WIN_B_START="2026-05-16"; WIN_B_END="2026-07-04"
BOOT=500; SEED=42; TMO=7200

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h09_$TS"
mkdir -p "$RUN/h09"
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

echo "RUN_H09 (T2) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Panel: $SYMBOLS | W1 $WIN_A_START..$WIN_A_END W2 $WIN_B_START..$WIN_B_END | Bootstrap=$BOOT Seed=$SEED"
echo "K_s-PLATZHALTER: ETH/SOL/BNB/XRP unverifiziert (kinks.py) - vor echtem Gate-Urteil Nachtrag noetig!"
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

# WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-Bug meiden).
SCRIPT="$REPO_ROOT/scripts/c09_bunch.py"
TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"

if [ "$DRY" != "1" ] && [ ! -d "$TRADE_PATH" ]; then
    echo "WARNUNG: Harvester-Pfad fehlt ($TRADE_PATH) - Junction data/harvest pruefen oder HARVEST_DIR setzen"
    rec "H09_BUNCH" "SKIP" "0" "0" "Harvester fehlt"; SK=$((SK+1))
else
    step H09_BUNCH "$SCRIPT" \
        --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
        --window-a-start "$WIN_A_START" --window-a-end "$WIN_A_END" \
        --window-b-start "$WIN_B_START" --window-b-end "$WIN_B_END" \
        --n-bootstrap "$BOOT" --seed "$SEED" --out-dir "$RUN/h09"
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-09 Risk-Limit-Tier-Bunching Mess-Gate (F-BUNCH) - T2"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\`  | Harvest \`$HARVEST_DIR\` (read-only) | Panel $SYMBOLS"
    echo "- **Fenster (Registry H-09):** W1 $WIN_A_START..$WIN_A_END + W2 $WIN_B_START..$WIN_B_END"
    echo "- **Methodik:** Order-Aggregat | Band [0.4,1.3)*K_s, 90 Bins | Polynom Grad 7 (Ausschluss [0.9,1.1)) | B-/B+ | Residuen-Bootstrap $BOOT | Placebos 0.5/0.75*K_s | F-BUNCH BH-FDR a=0.10 | N-Floor 2000/50"
    echo "- **K_s-PLATZHALTER:** ETH/SOL/BNB/XRP unverifiziert (kinks.py) - vor Gate-Urteil append-only Nachtrag (DEC-09-Muster) + Konstanz-Pruefung ueber W1+W2 noetig; nur BTCUSDT=2.000.000 USDT registry-beziffert."
    echo "- **KAPITALFREI** - reiner Struktur-/Verhaltensfakt; Tradability waere NEUE H-09b."
    echo ""
    echo "## Schritte"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    echo "*Gate-Urteil: gate-auditor gegen H-09 (h09/c09_bunch_results.json). WEITER verlangt fuer"
    echo ">=1 Symbol in BEIDEN Fenstern (gueltige Zelle): Bootstrap-p<=0.05 nach BH-FDR a=0.10 ueber"
    echo "F-BUNCH UND b->=1.0 UND b- - b+>=0.5 UND b- > max(b_P1,b_P2). N-Floor: >=2.000 Order-"
    echo "Beobachtungen im Schaetzband UND Counterfactual-Erwartung in B- >=50, sonst Zelle ungueltig;"
    echo "alle 5 Zellen eines Fensters ungueltig -> DROP wegen Power (keine Floor-Absenkung). Hartes"
    echo "Ein-Fenster-DROP, kein GRAUBEREICH. A-priori: DROP (Rundzahl-Praeferenz)."
    echo "Ergebnisse hochladen -> GL-014ff. (erster Welle-4-Lauf).*"
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
