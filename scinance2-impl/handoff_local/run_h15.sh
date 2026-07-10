#!/usr/bin/env bash
# ========================================================================
# run_h15.sh - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-15)
#
# Linux/macOS-Geschwister von run_h15.ps1. H-15 = C-15 Trade-Tape-Event-
# Grammatik jenseits Markov (F-GRAMMAR) auf dem read-only Harvester-Baum.
# Decoder-only Causal-Transformer (~2-4M Parameter, Kontext 1024 Token) vs.
# KT-geglaettetes Variable-Order-Markov (k<=4), gleicher Train-Fold, purged
# Walk-Forward (4 Folds, 1-Tag-Embargo, 3 Seeds), Null via >=200 Within-
# Hour-of-Day-Block-Shuffle-Surrogate (Blocklaenge 256 Events). KAPITALFREI:
# reine Existence-of-Structure-Messung, KEINE Kapital-Metriken.
#
#   bash scinance2-impl/handoff_local/run_h15.sh
#
# WICHTIG - Compute-Gating (verbindlich): ein verdikt-tragender Lauf braucht
# echtes CUDA (Registry: "GPU, zwingend"). Dieser Runner prueft VOR dem
# Hauptlauf per `--check-gpu-only`, ob torch+CUDA verfuegbar sind:
#   * CUDA verfuegbar  -> MODE=full (Standard), volles Gate, gate_valid
#     haengt zusaetzlich an den registrierten Parametern (4 Folds, 1-Tag-
#     Embargo, 3 Seeds, >=200 Surrogate, Vocab 128).
#   * CUDA NICHT verfuegbar -> sauberer SKIP (exit 2), KEIN mechanics-Fallback
#     automatisch (ein CPU-"Erfolg" waere hier irrefuehrend) - Override via
#     MODE=mechanics env, dann NIEMALS verdikt-tragend (gate_valid=false).
#
# Erwartete Laufzeit auf RTX 5060 Ti: Stunden (5 Symbole x 4 Folds x 3
# Seeds seriell). EIN Block: H15_GRAMMAR. Ergebnisse werden laufend im
# JSON persistiert (kein Datenverlust bei Abbruch mitten im Lauf).
#
# Datenbasis (Registry H-15, vorregistriert): Basis-Bestand 2026-03-27..
# Cutoff (~100 Tage), 5 Bybit-Perp-Symbole, publicTrade-Tokenstream je
# Symbol. EIN Fenster (Purged Walk-Forward, kein W1/W2-Split).
# >=200 Surrogate, F-GRAMMAR BH-FDR a=0.10.
#
# Env-Overrides: HARVEST_DIR, MODE (full|mechanics, Default full),
# HANDOFF_DRY_RUN (+HANDOFF_DRY_RC).
# Exit: 0=OK 1=FAIL 2=SKIP.
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
DATA_START="2026-03-27"; DATA_END="2026-07-04"
N_FOLDS=4; EMBARGO_DAYS=1; SEEDS="42,43,44"
N_SURROGATES=200; BLOCK_LEN=256
MODE="${MODE:-full}"
TMO=43200   # 12h Budget fuer den einen Gesamtblock (alle 5 Symbole)

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h15_$TS"
mkdir -p "$RUN/h15"
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

echo "RUN_H15 (T3) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Panel: $SYMBOLS x publicTrade | Raster $DATA_START..$DATA_END"
echo "Walk-Forward: $N_FOLDS Folds, ${EMBARGO_DAYS}-Tag-Embargo, Seeds $SEEDS | Surrogate $N_SURROGATES (Block $BLOCK_LEN)"
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

SCRIPT="$REPO_ROOT/scripts/c15_grammar.py"
TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"

if [ "$DRY" != "1" ] && [ ! -d "$TRADE_PATH" ]; then
    echo "WARNUNG: Harvester-Pfad fehlt ($TRADE_PATH) - Junction data/harvest pruefen oder HARVEST_DIR setzen"
    rec "H15_GRAMMAR" "SKIP" "0" "0" "Harvester fehlt"; SK=$((SK+1))
else
    # Compute-Gate-Vorlauf: --check-gpu-only ist eine reine Statusabfrage
    # (rc=0 immer), NIE der eigentliche Lauf.
    GPU_LOG="$RUN/gpu_status.json"
    if [ "$DRY" = "1" ]; then
        echo "[DRY-RUN] check-gpu-only" > "$GPU_LOG"
        CUDA_OK=1
    else
        "$PY" "$SCRIPT" --check-gpu-only > "$GPU_LOG" 2>>"$RUN/gpu_status.err.log"
        if grep -q '"cuda_available": true' "$GPU_LOG" 2>/dev/null; then CUDA_OK=1; else CUDA_OK=0; fi
    fi
    echo "GPU-Status: $(cat "$GPU_LOG" 2>/dev/null | tr '\n' ' ')"

    if [ "$MODE" = "full" ] && [ "$DRY" != "1" ] && [ "$CUDA_OK" != "1" ]; then
        echo "WARNUNG: kein CUDA-Geraet gefunden - MODE=full waere nicht verdikt-faehig (Registry: GPU, zwingend)."
        echo "Sauberer SKIP statt irrefuehrendem CPU-Ersatzlauf. Override: MODE=mechanics bash run_h15.sh (NIE verdikt-tragend)."
        rec "H15_GRAMMAR" "SKIP" "0" "0" "kein CUDA-Geraet (MODE=full)"; SK=$((SK+1))
    else
        step H15_GRAMMAR "$SCRIPT" \
            --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
            --data-start "$DATA_START" --data-end "$DATA_END" \
            --mode "$MODE" \
            --n-folds "$N_FOLDS" --embargo-days "$EMBARGO_DAYS" \
            --seeds "$SEEDS" --n-surrogates "$N_SURROGATES" --block-len "$BLOCK_LEN" \
            --out-dir "$RUN/h15"
    fi
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-15 C-15 Trade-Tape-Event-Grammatik Mess-Gate - T3"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\` | Harvest \`$HARVEST_DIR\` (read-only)"
    echo "- **Modus:** $MODE (full = verdikt-faehig, braucht CUDA; mechanics = NIE verdikt-tragend)"
    echo "- **Panel:** $SYMBOLS x publicTrade | Raster $DATA_START..$DATA_END"
    echo "- **Walk-Forward:** $N_FOLDS Folds, ${EMBARGO_DAYS}-Tag-Embargo, Seeds $SEEDS"
    echo "- **Surrogate $N_SURROGATES (Within-Hour-of-Day-Block-Shuffle, Blocklaenge $BLOCK_LEN) | F-GRAMMAR BH-FDR a=0.10**"
    echo "- **KAPITALFREI** - reine Existence-of-Structure-Messung, KEINE Kapital-Metriken."
    echo ""
    echo "## Schritte"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    echo "*Gate-Urteil: gate-auditor gegen H-15 (h15/c15_grammar_results.json)."
    echo "WEITER verlangt: OOS-Token-CE des Transformers >=2% relativ niedriger als die beste"
    echo "Markov-k-(k<=4)-Baseline bei >=4/5 Symbolen UND CE-Luecke ueber dem 95. Perzentil der"
    echo "Surrogat-Luecken-Verteilung, nach BH-FDR a=0.10 ueber F-GRAMMAR. Hartes Kriterium, kein"
    echo "GRAUBEREICH. WICHTIG: nur bei ran_on_gpu=true UND gate_valid=true ist ein Urteil zulaessig."
    echo "A-priori: DROP erwartet (Saisonalitaets-/Regime-Konfundierung wahrscheinlicher als echte"
    echo "Grammatik-Struktur). Ergebnisse hochladen -> GL-Zaehlung.*"
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
