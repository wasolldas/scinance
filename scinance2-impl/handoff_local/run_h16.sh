#!/usr/bin/env bash
# ========================================================================
# run_h16.sh - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-16)
#
# Ein Befehl, keine Pflicht-Parameter. GPU ZWINGEND (registry H-16): der
# Lauf ist NUR auf einem echten CUDA-Device verdikt-tragend. Bricht NIE mit
# offenem Prompt ab; jeder Teilschritt hat Timeout + Fehler-Kapselung.
#
#   bash scinance2-impl/handoff_local/run_h16.sh
#
# H-16 = Time-Arrow-CNN: Classifier-Two-Sample-Test (Lopez-Paz & Oquab 2017).
# Ein ResNet-18 klassifiziert FORWARD vs. TIME-REVERSED Morlet-CWT-Log-Power-
# Scalogramme der 1s-signed-Trade-Imbalance-Serie (5 Symbole). Reversal auf
# der Roh-Serie VOR der CWT. Bayes-optimale AUC=0.5 ist die exakte Null.
# KAPITALFREI: reine Struktur-/Existenzfrage, KEINE Kosten-/Ertragsrechnung.
#
# DIFFERENZIERUNG (Registry-Pflicht, wortgleich in driver.DIFFERENTIATION_NOTE
# und im JSON/MD-Report): H-16 ist KEIN Duplikat des gesperrten Informations-
# theorie-/Nichtlineare-Dynamik-Clusters (PE/TE/RQA/MFDFA/TDA) - kein Entropie-
# Schaetzer, andere Eigenschaft (Zeit-Irreversibilitaet statt Komplexitaet),
# exakte Bayes-Null statt geschaetztem Schwellenwert.
#
# Ablauf: (1) H16_GPU_CHECK via --check-gpu-only (rc 2 = kein CUDA -> SKIP,
# der volle Lauf startet dann NICHT - ein CPU-Lauf darf niemals verdikt-
# tragend aussehen), (2) nur bei rc 0: H16_ARROW voller Lauf: 5 Symbole,
# 5 Seeds Haupt-C2ST + 20 IAAFT-Surrogat-Retrainings (Pflicht-Leak-Kontrolle)
# + 3 Ablations-Seeds auf |Imbalance| je Symbol = ~140 Trainings,
# F-ARROW BH-FDR alpha=0.10. Gate-neutral - gate-auditor urteilt; eine
# Leak-Kontrolle > 0.52 wird vom Modul selbst als METHOD_INVALID_NO_VERDICT
# markiert (eigener Zustand, KEIN DROP).
#
# Exit-Code: 0 = OK * 1 = FAIL * 2 = SKIP (kein CUDA-Device gefunden).
# Ergebnisse: scinance2-impl/handoff_local/results/h16_<timestamp>/
#             + SUMMARY_<datum>.md (Morgen-Auswertung gate-auditor).
#
# Optionale Env-Overrides (KEINE Pflicht):
#   HARVEST_DIR, HANDOFF_DRY_RUN=1 (+HANDOFF_DRY_RC), H16_END_DATE
#   (Cutoff, default = gestern UTC), H16_N_SEEDS, H16_N_SURROGATES,
#   H16_ABLATION_SEEDS, H16_TIMEOUT_SEC (Default 8h Budget fuer den vollen Lauf).
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"

SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
START_DATE="2026-03-27"
# Cutoff: default gestern UTC (heutiger Tag ist typischerweise noch nicht
# vollstaendig geharvestet). GNU- und BSD-date-kompatibel.
if [ -n "${H16_END_DATE:-}" ]; then
    END_DATE="$H16_END_DATE"
elif date -u -d 'yesterday' +%F >/dev/null 2>&1; then
    END_DATE="$(date -u -d 'yesterday' +%F)"
else
    END_DATE="$(date -u -v-1d +%F)"
fi
SEED=42
N_SEEDS="${H16_N_SEEDS:-5}"
N_SURROGATES="${H16_N_SURROGATES:-20}"
ABLATION_SEEDS="${H16_ABLATION_SEEDS:-3}"
TMO_GPU_CHECK=120
TMO_FULL="${H16_TIMEOUT_SEC:-28800}"   # 8h Default-Budget (registry: ~145 Trainings)

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
renice -n 10 $$ >/dev/null 2>&1 || true
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h16_$TS"
mkdir -p "$RUN/h16"
STEPS="$RUN/steps.tsv"
rec() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$STEPS"; }

SKIP_MSG="H-16 SKIP - kein verdikt-taugliches CUDA-Device gefunden (torch/CUDA-Check negativ)"
OKN=0; FN=0; SK=0
LAST_RC=0
step() {
    # rc 2 des CLI = kein Compute-Gate -> Status SKIP (kein FAIL).
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

echo "RUN_H16 (T3) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Symbole: $SYMBOLS | Fenster: $START_DATE..$END_DATE"
echo "Seeds=$N_SEEDS Surrogate=$N_SURROGATES Ablation=$ABLATION_SEEDS Seed=$SEED"
echo "H-16 ist GPU ZWINGEND: erst ehrlicher Compute-Check, dann (nur bei echtem CUDA) voller Lauf."
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

TRADE_PATH="$HARVEST_DIR/raw/bybit/publicTrade"
if [ "$DRY" != "1" ] && [ ! -d "$TRADE_PATH" ]; then
    echo "WARNUNG: Harvester-Pfad fehlt ($TRADE_PATH) - Junction data/harvest pruefen"
    rec "H16_GPU_CHECK" "SKIP" "0" "0" "Harvester-Pfad fehlt"; SK=$((SK+1))
else
    # WICHTIG: Skript-Pfad ist das ERSTE CmdArg, VOR allen --flags (run_h05c-rc=2-Bug meiden).
    SCRIPT="$REPO_ROOT/scripts/c16_arrow.py"
    step H16_GPU_CHECK "$TMO_GPU_CHECK" "$SCRIPT" \
        --check-gpu-only --out-dir "$RUN/h16"
    if [ "$LAST_RC" = "0" ]; then
        step H16_ARROW "$TMO_FULL" "$SCRIPT" \
            --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" \
            --start-date "$START_DATE" --end-date "$END_DATE" \
            --n-seeds "$N_SEEDS" --n-surrogates "$N_SURROGATES" \
            --ablation-seeds "$ABLATION_SEEDS" --seed "$SEED" \
            --device cuda --out-dir "$RUN/h16"
    elif [ "$LAST_RC" = "2" ]; then
        echo "SKIP: $SKIP_MSG"
    fi
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-16 Time-Arrow-CNN Mess-Gate - T3 (GPU zwingend)"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\` | Harvest \`$HARVEST_DIR\` (read-only) | Symbole $SYMBOLS"
    echo "- **Fenster:** $START_DATE..$END_DATE (Basis-Bestand..Cutoff) | Held-out-Day-Split (letzte 20% valide Tage)"
    echo "- **Methodik (vorregistriert):** Morlet-CWT-Log-Power-Scalogram (64 Skalen 2s-256s x 512 Zeit-Bins, Stride 64s), ResNet-18, Reversal auf Roh-Serie VOR CWT, $N_SEEDS Seeds, $N_SURROGATES IAAFT-Surrogat-Retrainings (Pflicht-Leak-Kontrolle <=0.52), $ABLATION_SEEDS Ablations-Seeds auf \\|Imbalance\\| (Pflicht-Report, nicht urteilstragend), Seed $SEED | F-ARROW BH-FDR a=0.10"
    echo "- **KAPITALFREI** - reine Struktur-/Existenzfrage, KEINE Kosten-/Ertragsrechnung."
    echo "- **DIFFERENZIERUNG (Registry-Pflicht):** KEIN Duplikat des gesperrten Informationstheorie-/Nichtlineare-Dynamik-Clusters (PE/TE/RQA/MFDFA/TDA) - kein Entropie-Schaetzer, gemessene Eigenschaft ist Zeit-Irreversibilitaet statt Komplexitaet/Vorhersagbarkeit, exakte Bayes-Null AUC=0.5 statt geschaetztem Schwellenwert."
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
        echo "*SKIP: $SKIP_MSG. Ein voller Lauf ohne echtes CUDA-Device ist NIEMALS verdikt-tragend (Registry H-16) und wurde deshalb NICHT gestartet.*"
    else
        echo "*Gate-Urteil: gate-auditor gegen H-16 (h16/c16_arrow_results.json). WEITER verlangt:"
        echo "Held-out-Day-Forward-vs-Reversed-AUC >=0.60 MIT IAAFT-Surrogat-Null-95.-Perzentil<0.53,"
        echo "bei >=4/5 Symbolen nach BH-FDR a=0.10 ueber F-ARROW, UND die Leak-Kontrolle bleibt <=0.52"
        echo "(sonst methodisch invalide -> status=METHOD_INVALID_NO_VERDICT, das ist ein EIGENER"
        echo "Zustand und KEIN DROP). DROP nur: AUC<0.60 bei <4/5 Symbolen. Kein Graubereich, keine"
        echo "nachtraegliche Skalen-/Fenster-Anpassung. Ergebnisse hochladen -> Morgen-Auswertung.*"
    fi
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
