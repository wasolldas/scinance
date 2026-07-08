#!/usr/bin/env bash
# ========================================================================
# run_h12.sh - T2 LOCAL_SHORT Runner (Scinance 2.0 Welle 4, H-12)
#
# Linux/macOS-Geschwister von run_h12.ps1. H-12 = C-12-FRAG Cross-Exchange-
# Fragmentierungsmatrix (RMT/MP-IPR, F-FRAG) auf dem read-only Harvester-
# Baum (data/harvest). 6-Serien-Minuten-Panel (BTC/ETH x Bybit/Binance/
# Deribit), Tagesfenster (UTC, T=1440), Korrelationsmatrix-Eigenzerlegung
# je gueltigem Tag. Nullhypothese zweistufig: (a) MC-Gaussian-Wishart-
# Referenz (1000 Ziehungen, NICHT urteilstragend), (b) Ein-Faktor-Gauss-
# Null je Tag (1000 Replikationen, urteilstragend). EINE F-FRAG BH-FDR-
# Familie ueber BEIDE Fenster. KAPITALFREI: reine Mess-/Explorationsfrage,
# KEINE bps/PnL/Sharpe/Friction.
#
#   bash scinance2-impl/handoff_local/run_h12.sh
#
# Datenbasis (Registry H-12, vorregistriert): 6 Serien = 2 Symbole
# (BTCUSDT, ETHUSDT) x 3 Boersen (bybit, binance, deribit) publicTrade.
# Deribit-Notation BTC-PERPETUAL/ETH-PERPETUAL (panel.DERIBIT_SYMBOL_MAP).
# Fenster (identisch H-09): W1 = 2026-03-27..2026-05-15,
#                            W2 = 2026-05-16..2026-07-04.
# Tag gueltig >=1380/1440 gueltige Minuten je Serie (Forward-Fill <=1 min).
#
# EIN Block: H12_FRAG. Env: HARVEST_DIR, HANDOFF_DRY_RUN (+HANDOFF_DRY_RC).
# Exit: 0=OK 1=FAIL 2=SKIP. Laufzeit ca. 20-40 min (rechenintensiv: 2
# Fenster x 1000 MC-Reps/Tag).
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOLS="BTCUSDT,ETHUSDT"
EXCHANGES="bybit,binance,deribit"
WIN_A_START="2026-03-27"; WIN_A_END="2026-05-15"
WIN_B_START="2026-05-16"; WIN_B_END="2026-07-04"
N_MC=1000; SEED=42; TMO=2400

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h12_$TS"
mkdir -p "$RUN/h12"
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

echo "RUN_H12 (T2) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Panel: $SYMBOLS x {$EXCHANGES}"
echo "Fenster: W1 $WIN_A_START..$WIN_A_END | W2 $WIN_B_START..$WIN_B_END | n_mc=$N_MC seed=$SEED"
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

# WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-Bug meiden).
SCRIPT="$REPO_ROOT/scripts/c12_frag.py"
BYBIT_PATH="$HARVEST_DIR/raw/bybit/publicTrade"
BINANCE_PATH="$HARVEST_DIR/raw/binance/publicTrade"
DERIBIT_PATH="$HARVEST_DIR/raw/deribit/publicTrade"

if [ "$DRY" != "1" ] && { [ ! -d "$BYBIT_PATH" ] || [ ! -d "$BINANCE_PATH" ] || [ ! -d "$DERIBIT_PATH" ]; }; then
    echo "WARNUNG: Harvester-Pfad fehlt ($BYBIT_PATH bzw. $BINANCE_PATH bzw. $DERIBIT_PATH) - Junction data/harvest pruefen oder HARVEST_DIR setzen"
    rec "H12_FRAG" "SKIP" "0" "0" "Harvester fehlt"; SK=$((SK+1))
else
    step H12_FRAG "$SCRIPT" \
        --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" --exchanges "$EXCHANGES" \
        --window-a-start "$WIN_A_START" --window-a-end "$WIN_A_END" \
        --window-b-start "$WIN_B_START" --window-b-end "$WIN_B_END" \
        --n-mc "$N_MC" --seed "$SEED" --out-dir "$RUN/h12"
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-12 Cross-Exchange-Fragmentierungsmatrix Mess-Gate (RMT/MP-IPR) - T2"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\` | Harvest \`$HARVEST_DIR\` (read-only)"
    echo "- **Panel:** $SYMBOLS x {$EXCHANGES}"
    echo "- **Fenster:** W1 $WIN_A_START..$WIN_A_END | W2 $WIN_B_START..$WIN_B_END (identisch H-09)"
    echo "- **n_mc=$N_MC (Stufe a + Stufe b) | seed=$SEED | F-FRAG BH-FDR a=0.10**"
    echo "- **KAPITALFREI** - reine Mess-/Explorationsfrage, KEINE bps/PnL/Sharpe/Friction."
    echo ""
    echo "## Schritte"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    echo "*Gate-Urteil: gate-auditor gegen H-12 (h12/c12_frag_results.json). WEITER verlangt in"
    echo "BEIDEN Fenstern: (a) Anteil gueltiger Tage mit lambda2 nach BH-FDR alpha=0.10 ueber F-FRAG"
    echo "signifikant ueber der Ein-Faktor-Null >=20% UND (b) Median-IPR(v2) ueber den FDR-"
    echo "signifikanten Tagen >=0.40 UND (c) an >=70% der FDR-signifikanten Tage groesste v2^2-"
    echo "Boersenlast auf derselben Boerse. Validitaets-Vorbedingung (KEIN Gate-Bestandteil):"
    echo "IPR(v1)<=0.25 an >=90% der gueltigen Tage UND >=35 gueltige Tage je Fenster - sonst Lauf"
    echo "UNGUELTIG (kein Verdikt, NICHT DROP). Hartes Ein-Fenster-DROP sonst, kein Graubereich."
    echo "A-priori: DROP erwartet. Ergebnisse hochladen -> GL-Zaehlung.*"
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
