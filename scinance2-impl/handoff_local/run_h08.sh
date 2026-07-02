#!/usr/bin/env bash
# ========================================================================
# run_h08.sh - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 3, H-08)
#
# Linux/macOS-Geschwister von run_h08.ps1. H-08 = C-06 Cross-Sectional MR
# mit RANG-Ueber-Dehnung (DEC-18) auf read-only Harvester-Backfill
# (data/harvest). Achse A (NEU, schwellen-frei): je Bar das EINE extremste
# Symbol i* = argmax |z| (Gleichstand: alphabetisch erstes Symbol,
# deterministisch); KEIN Magnitude-Schwellwert. Achse B (Crash-Dezil)
# UNVERAENDERT aus H-07/DEC-17. KAPITALFREI: reiner Mess-/Verstaerkungs-
# Test, KEINE bps/Edge/PnL/Sharpe/Friction.
#
#   bash scinance2-impl/handoff_local/run_h08.sh
#
# Datenbasis (DEC-15/DEC-17/DEC-18, vorregistriert): 5-Symbol-Panel
# BTC/ETH/SOL/BNB/XRP, zwei disjunkte Kalender-Fenster (je 2 Kalendertage):
#   Fenster A: ab 2026-04-15 00:00 UTC
#   Fenster B: ab 2026-05-15 00:00 UTC
# 5-min-Last-Price-Bars, kontemporaer synchronisiert (forward-fill <=1 Bar).
# L=12 Bars, Crash-Dezil 0.9, Horizonte {1,3,6} Bars, N-Floor 30,
# Surrogates 200, F-XMR-RANK BH-FDR a=0.10. Gate-neutral - gate-auditor urteilt.
#
# EIN Block: H08_XMR_RANK. Env: HARVEST_DIR, HANDOFF_DRY_RUN (+HANDOFF_DRY_RC).
# Exit: 0=OK 1=FAIL 2=SKIP.
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
WIN_A="2026-04-15"; WIN_B="2026-05-15"
CAL_DAYS=2; BAR_MIN=5; LOOKBACK=12; CRASH_DECILE=0.9
HORIZONS="1,3,6"; SURROGATES=200; BOOT=1000; NFLOOR=30; SEED=42; TMO=2400

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h08_$TS"
mkdir -p "$RUN/h08"
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

echo "RUN_H08 (T2) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Panel: $SYMBOLS | A@$WIN_A B@$WIN_B | h $HORIZONS | Achse A=RANG (argmax |z|, schwellen-frei)"
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

# WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-Bug meiden).
SCRIPT="$REPO_ROOT/scripts/c06_xmr.py"
TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"

if [ "$DRY" != "1" ] && [ ! -d "$TRADE_PATH" ]; then
    echo "WARNUNG: Harvester-Pfad fehlt ($TRADE_PATH) - Junction data/harvest pruefen oder HARVEST_DIR setzen"
    rec "H08_XMR_RANK" "SKIP" "0" "0" "Harvester fehlt"; SK=$((SK+1))
else
    step H08_XMR_RANK "$SCRIPT" \
        --overextension rank \
        --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
        --window-a-start "$WIN_A" --window-b-start "$WIN_B" \
        --calendar-days "$CAL_DAYS" --bar-min "$BAR_MIN" \
        --lookback-bars "$LOOKBACK" \
        --crash-decile "$CRASH_DECILE" --horizons "$HORIZONS" \
        --n-surrogates "$SURROGATES" --n-bootstrap "$BOOT" \
        --n-floor "$NFLOOR" --seed "$SEED" --out-dir "$RUN/h08"
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-08 C-06 Cross-Sectional MR mit RANG-Ueber-Dehnung Mess-Gate - T2"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\`  | Harvest \`$HARVEST_DIR\` (read-only) | Panel $SYMBOLS"
    echo "- **Fenster (DEC-15):** A@$WIN_A + B@$WIN_B, je $CAL_DAYS Kalendertage | 5-min-Bars"
    echo "- **Achse A: RANG (argmax |z| je Bar, schwellen-frei, DEC-18) | L=$LOOKBACK Crash-Dezil=$CRASH_DECILE Horizonte $HORIZONS N-Floor=$NFLOOR | F-XMR-RANK BH-FDR a=0.10**"
    echo "- **KAPITALFREI** - reiner Mess-/Verstaerkungs-Test, KEINE bps/Edge/PnL/Sharpe/Friction."
    echo ""
    echo "## Schritte"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    echo "*Gate-Urteil: gate-auditor gegen H-08 (h08/c06_xmr_results.json). WEITER verlangt:"
    echo "konditioniert mu_rev>0 UND p<=0.05 (BH-FDR F-XMR-RANK) UND >=2-Fenster-Konsistenz UND"
    echo "nicht-ueberlappende 95%-CIs (konditioniert > Baseline) fuer >=1 Horizont in >=2 Fenstern"
    echo "UND N>=30/Fenster. Nicht-Trivialitaets-Anker traegt die GESAMTE Beweislast (Rang-1 feuert"
    echo "jede Bar = Verduennung; die unkonditionierte Trivial-MR, E-04-/PRD-6-verboten, zaehlt NIE"
    echo "als Erfolg). Hartes Ein-Fenster-DROP, kein GRAUBEREICH. A-priori: DROP."
    echo "Ergebnisse hochladen -> GL-013.*"
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
