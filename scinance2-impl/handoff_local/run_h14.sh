#!/usr/bin/env bash
# ========================================================================
# run_h14.sh - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-14)
#
# Aufruf (keine Pflicht-Parameter):
#   bash scinance2-impl/handoff_local/run_h14.sh
#
# H-14 = C-14-PANELLAG Conditional Cross-Venue-Lead-Lag-Graph via
# Node-Ablation-Cross-Attention. 12-Node-1s-Panel (BTC/ETH x {Bybit,
# Binance, Deribit-PERP} + SOL/BNB/XRP x {Bybit, Binance}), pro Node ein
# PatchTST-Style-Encoder (m18_patchtst-Wiederverwendung) + Cross-Node-
# Multi-Head-Attention, Target = Vorzeichen der naechsten 10s-Rendite.
# Edge-Statistik T(j->i) = OOS-Delta-Log-Loss (Vollmodell vs. Single-
# Source-j-Retrain-Ablation). Null: ~100 Retrainings mit komplett
# surrogaten Cross-Node-Inputs je Fenster. ZWEI Fenster W1/W2 (identisch
# H-09/H-12). F-PANELLAG BH-FDR a=0.10 ueber 99 Non-BTC-Source-Kanten je
# Fenster (Registry-Schaetzung "~110"). KAPITALFREI: reine Struktur-/
# Existenzfrage, KEINE Kosten-/Ertragsrechnung. GPU ZWINGEND: ein Lauf ohne
# echtes CUDA-Device ist NIEMALS verdikt-tragend.
#
# **EXTREME LAUFZEIT (~226 volle Trainings, ~2-3 GPU-Tage auf RTX 5060 Ti)
# - DIESER RUNNER IST RESUME-FAEHIG.** Jedes abgeschlossene Training
# (1 Vollmodell + 12 Ablationen + ~100 Nullen, je Fenster) schreibt SOFORT
# einen eigenen Checkpoint (atomic write) nach einem STABILEN, NICHT
# zeitgestempelten Verzeichnis (results/h14_checkpoints/). Ein Stromausfall,
# ein Timeout dieses Runners oder ein manueller Abbruch verliert HOECHSTENS
# das gerade laufende einzelne Training (10-20 Min) - nicht den restlichen
# Fortschritt. EINFACH DIESES SKRIPT ERNEUT STARTEN: es laedt automatisch
# alle bereits abgeschlossenen Trainings aus results/h14_checkpoints/ und
# trainiert nur die fehlenden weiter. Der volle Lauf braucht typischerweise
# MEHRERE Aufrufe dieses Skripts ueber mehrere Naechte (Default-Budget pro
# Aufruf s.u.) - das ist der VORGESEHENE Betriebsmodus, kein Fehler.
#
# Ablauf: (1) H14_GPU_CHECK via --check-gpu-only (rc 2 = kein CUDA -> SKIP,
# der volle Lauf startet dann NICHT), (2) nur bei rc 0: H14_PANELLAG voller
# (Teil-)Lauf innerhalb des Zeitbudgets dieses Aufrufs; schreibt
# c14_panellag_results.{json,md} NUR wenn ALLE Trainings beider Fenster
# abgeschlossen sind (sonst TIMEOUT/FAIL bei diesem Aufruf, aber Fortschritt
# bleibt in results/h14_checkpoints/ erhalten -> naechster Aufruf macht weiter).
#
# Exit-Code: 0 = OK (voller Lauf komplett, Ergebnis-JSON geschrieben) *
#            1 = FAIL (inkl. TIMEOUT dieses Aufrufs bei noch unvollstaendigem
#                Plan - KEIN Datenverlust, einfach erneut starten) *
#            2 = SKIP (kein CUDA-Device gefunden).
# Ergebnisse: scinance2-impl/handoff_local/results/h14_<timestamp>/
#             + SUMMARY_<datum>.md. Checkpoints (STABIL, ueberlebt Neustarts):
#             scinance2-impl/handoff_local/results/h14_checkpoints/{W1,W2}/*.json
#
# Optionale Env-Overrides (KEINE Pflicht):
#   HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC), H14_N_NULL (Default 100),
#   H14_TIMEOUT_SEC (Default 36000 = 10h Budget PRO AUFRUF - der Gesamtlauf
#   braucht mehrere Aufrufe, s.o.), H14_CKPT_DIR (Default results/h14_checkpoints,
#   NICHT aendern zwischen Aufruefen desselben Laufs - sonst kein Resume!).
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

WIN_A_START="2026-03-27"; WIN_A_END="2026-05-15"
WIN_B_START="2026-05-16"; WIN_B_END="2026-07-04"
N_NULL="${H14_N_NULL:-100}"
SEED=42
TMO_GPU_CHECK=120
TMO_FULL="${H14_TIMEOUT_SEC:-36000}"   # 10h Default-Budget PRO AUFRUF (s. Kopf-Kommentar)
CKPT_DIR="${H14_CKPT_DIR:-$SCRIPT_DIR/results/h14_checkpoints}"

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
renice -n 10 $$ >/dev/null 2>&1 || true
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h14_$TS"
mkdir -p "$RUN/h14" "$CKPT_DIR"
STEPS="$RUN/steps.tsv"
rec() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$STEPS"; }

SKIP_MSG="H-14 SKIP - kein verdikt-taugliches CUDA-Device gefunden (torch/CUDA-Check negativ)"
OKN=0; FN=0; SK=0
LAST_RC=0
step() {
    # rc 2 des CLI = kein Compute-Gate -> Status SKIP (kein FAIL). rc 124
    # (Bash-timeout) oder sonstiger rc!=0 = FAIL, ABER bei H14_PANELLAG ist
    # ein TIMEOUT-FAIL bei unvollstaendigem Plan NORMAL (s. Kopf-Kommentar) -
    # der naechste Aufruf resumed aus results/h14_checkpoints/.
    local name="$1"; local tmo="$2"; shift 2
    local log="$RUN/$name.log"; local err="$RUN/$name.err.log"
    echo "[$(date +%H:%M:%S)] START $name (timeout ${tmo}s)"
    local t0; t0=$(date +%s); local rc=-1; local detail=""
    if [ "$DRY" = "1" ]; then echo "[DRY-RUN] $*" >> "$log"; rc="$DRY_RC"; detail="dry-run rc=$rc"
    else
        if command -v timeout >/dev/null 2>&1; then timeout "$tmo" "$PY" "$@" >"$log" 2>"$err"; rc=$?
        else "$PY" "$@" >"$log" 2>"$err"; rc=$?; fi
        if [ "$rc" = "124" ]; then detail="TIMEOUT ${tmo}s (Plan unvollstaendig - Checkpoints erhalten, naechster Aufruf resumed)"; else detail="rc=$rc"; fi
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

echo "RUN_H14 (T3) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | 12-Node-Panel (BTC/ETH x Bybit/Binance/Deribit + SOL/BNB/XRP x Bybit/Binance)"
echo "Fenster: W1 $WIN_A_START..$WIN_A_END | W2 $WIN_B_START..$WIN_B_END | n_null=$N_NULL seed=$SEED"
echo "Checkpoints (STABIL ueber Neustarts): $CKPT_DIR"
echo "H-14 ist GPU ZWINGEND: erst ehrlicher Compute-Check, dann (nur bei echtem CUDA) voller Lauf."
echo "RESUME-FAEHIG: bereits abgeschlossene Trainings werden uebersprungen (s. Kopf-Kommentar)."
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

# Alle 12 Node-Pfade muessen existieren (Panel braucht alle 12 Serien).
# Reihenfolge/Deribit-Notation identisch panel.DEFAULT_NODES.
NODE_PATHS=(
    "bybit/publicTrade/symbol=BTCUSDT"
    "binance/publicTrade/symbol=BTCUSDT"
    "deribit/publicTrade/symbol=BTC-PERPETUAL"
    "bybit/publicTrade/symbol=ETHUSDT"
    "binance/publicTrade/symbol=ETHUSDT"
    "deribit/publicTrade/symbol=ETH-PERPETUAL"
    "bybit/publicTrade/symbol=SOLUSDT"
    "binance/publicTrade/symbol=SOLUSDT"
    "bybit/publicTrade/symbol=XRPUSDT"
    "binance/publicTrade/symbol=XRPUSDT"
    "bybit/publicTrade/symbol=BNBUSDT"
    "binance/publicTrade/symbol=BNBUSDT"
)
HarvestOk=1
if [ "$DRY" != "1" ]; then
    for rel in "${NODE_PATHS[@]}"; do
        if [ ! -d "$HARVEST_DIR/raw/$rel" ]; then
            HarvestOk=0
            echo "WARNUNG: Harvester-Pfad fehlt ($HARVEST_DIR/raw/$rel)"
        fi
    done
fi

if [ "$HarvestOk" = "0" ]; then
    rec "H14_GPU_CHECK" "SKIP" "0" "0" "Harvester-Pfad(e) fehlen (12-Node-Panel unvollstaendig)"; SK=$((SK+1))
else
    # WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-rc=2-Bug meiden).
    SCRIPT="$REPO_ROOT/scripts/c14_panellag.py"
    step H14_GPU_CHECK "$TMO_GPU_CHECK" "$SCRIPT" \
        --check-gpu-only --out-dir "$RUN/h14"
    if [ "$LAST_RC" = "0" ]; then
        step H14_PANELLAG "$TMO_FULL" "$SCRIPT" \
            --base-dir "$HARVEST_DIR" \
            --window-a-start "$WIN_A_START" --window-a-end "$WIN_A_END" \
            --window-b-start "$WIN_B_START" --window-b-end "$WIN_B_END" \
            --n-null "$N_NULL" --seed "$SEED" --device cuda \
            --ckpt-dir "$CKPT_DIR" --out-dir "$RUN/h14"
    elif [ "$LAST_RC" = "2" ]; then
        echo "SKIP: $SKIP_MSG"
    fi
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-14 Conditional Cross-Venue-Lead-Lag-Graph (Node-Ablation-Cross-Attention) - T3 (GPU zwingend)"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\` | Harvest \`$HARVEST_DIR\` (read-only)"
    echo "- **Checkpoints (STABIL, ueberlebt Neustarts):** \`$CKPT_DIR\`"
    echo "- **Panel:** 12 Nodes = BTC/ETH x {Bybit, Binance, Deribit-PERP} + SOL/BNB/XRP x {Bybit, Binance}, publicTrade 1s-Grid"
    echo "- **Fenster:** W1 $WIN_A_START..$WIN_A_END | W2 $WIN_B_START..$WIN_B_END (identisch H-09/H-12)"
    echo "- **Methodik (vorregistriert):** pro Node PatchTST-Style-Encoder (m18-Wiederverwendung) + Cross-Node-Multi-Head-Attention, Target = Vorzeichen der naechsten 10s-Rendite. T(j->i) = OOS-Delta-Log-Loss (Vollmodell vs. Single-Source-j-Retrain-Ablation). n_null=$N_NULL Retrainings je Fenster (zirkulaeres Surrogat), seed=$SEED | F-PANELLAG BH-FDR a=0.10 ueber 99 Non-BTC-Source-Kanten je Fenster"
    echo "- **KAPITALFREI** - reine Struktur-/Existenzfrage, KEINE Kosten-/Ertragsrechnung."
    echo "- **RESUME-FAEHIG:** ~226 Trainings, ~2-3 GPU-Tage total - dieser Runner braucht typischerweise MEHRERE Aufrufe ueber mehrere Naechte; jeder Aufruf setzt aus den Checkpoints in \`$CKPT_DIR\` fort. Ein TIMEOUT/FAIL bei unvollstaendigem Plan ist NORMAL, kein Datenverlust."
    echo ""
    echo "## Schritte (dieser Aufruf)"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    if [ "$EXIT" = "2" ]; then
        echo "*SKIP: $SKIP_MSG. Ein voller Lauf ohne echtes CUDA-Device ist NIEMALS verdikt-tragend (Registry H-14) und wurde deshalb NICHT gestartet.*"
    elif [ "$EXIT" = "1" ]; then
        echo "*FAIL/TIMEOUT bei diesem Aufruf. Pruefe \`$RUN/H14_PANELLAG.err.log\`. Falls TIMEOUT: das ist bei ~226 Trainings ERWARTET -"
        echo "Fortschritt liegt sicher in \`$CKPT_DIR\` (atomic writes je abgeschlossenem Training). EINFACH DIESES SKRIPT ERNEUT STARTEN -"
        echo "es ueberspringt alle bereits abgeschlossenen Trainings und macht nur mit den fehlenden weiter. c14_panellag_results.json wird"
        echo "erst geschrieben, wenn ALLE Trainings beider Fenster fertig sind (rc=0).*"
    else
        echo "*Gate-Urteil faellt der gate-auditor gegen H-14 (Roh-JSON unter \`h14/c14_panellag_results.json\`)."
        echo "WEITER verlangt in BEIDEN Fenstern mindestens eine gerichtete Non-BTC-Source-Kante ueber dem 95. Perzentil"
        echo "der ~100-Surrogat-Null UND BH-FDR a=0.10 ueber F-PANELLAG ueberlebend. DROP (hartes Ein-Fenster-Kriterium):"
        echo "null ueberlebende Non-BTC-Source-Kanten in einem Fenster. BTC->ETH ist Positivkontrolle (vom Pass ausgeschlossen;"
        echo "Scheitern = methodisch invalide, kein Verdikt, KEIN DROP). Pruefe im JSON zwingend \`compute_gating.gate_valid\`"
        echo "(muss true sein) und \`weiter_indication\` (null = nicht verdikt-tragend, sollte bei echtem GPU-Lauf nicht"
        echo "vorkommen). Kein Graubereich, keine nachtraegliche Kanten-/Schwellen-Anpassung. A-priori: DROP erwartet."
        echo "Ergebnisse (kompletten Ordner \`$RUN\` + \`$CKPT_DIR\`) hochladen -> Morgen-Auswertung.*"
    fi
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
