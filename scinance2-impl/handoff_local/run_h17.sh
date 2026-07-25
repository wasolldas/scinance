#!/usr/bin/env bash
# ========================================================================
# run_h17.sh - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-17)
#
# Linux/macOS-Runner fuer H-17 = C-17-VENUE Venue-Fingerprint-Mess-Gate
# (Contrastive-Embedding InfoNCE + Frozen-Linear-Probe, F-VENUE). 10 Nodes
# (5 Symbole x {Bybit, Binance}, publicTrade only), 5-Min-Event-Fenster,
# 4 Kanaele (Inter-Trade-Dauer, Log-Trade-Size, Aggressor-Sign, Tick-
# Direction) mit Pro-Tag-Quantil-Normalisierung je Kanal/Node. Leave-One-
# Symbol-Out (5 Folds), je Fold EIN echtes Training + 20 VOLLE Permutations-
# Retrainings (Within-Symbol-Within-Day-Label-Permutation, KEIN Frozen-
# Model-Shuffling). ONE F-VENUE BH-FDR-Familie ueber die 5 Fold-p-Werte.
# VORREGISTRIERTES Non-Redundanz-Gate gegen c12_frag/H-12 (|Spearman rho|
# < 0,6 gegen die c12-Tages-lambda2/IPR-Serie, sonst REDUNDANT = DROP
# unabhaengig von der Accuracy). KAPITALFREI.
#
#   bash scinance2-impl/handoff_local/run_h17.sh
#
# ZWINGENDE GPU-VORBEDINGUNG (registry H-17, verbindlich): Batch >= 2048
# ist Teil der registrierten Methode. Der Runner prueft ZUERST per
# `--check-gpu-only`, ob ein echtes CUDA-Device sichtbar ist. OHNE CUDA
# wird der volle Lauf UEBERSPRUNGEN (SKIP, exit 2) statt stundenlang eine
# NICHT-verdikt-tragende CPU/Numpy-Pipeline-Smoke zu produzieren - selbst
# WENN der volle Lauf trotzdem versucht wuerde, waere das Ergebnis wegen
# des eingebauten Compute-Gates in driver.run() (`compute.verdict_bearing`)
# NIE urteilstragend (siehe c17_venue/driver.py). Override zum erzwungenen
# Smoke-Lauf trotz fehlender GPU: HANDOFF_H17_FORCE_NO_GPU=1 (nur fuer
# Pipeline-Diagnose, NIE fuer ein Gate-Urteil verwenden).
#
# **EXTREME LAUFZEIT (registry-Schaetzung: GPU ~1-2 Tage, ~105 volle
# Trainings: 5 Folds x (1 echtes InfoNCE-Training + 20 Permutations-
# Retrainings) + Probe-Fits) - DIESER RUNNER IST RESUME-FAEHIG / EINFACH
# ERNEUT STARTEN (run_h14/run_h16-Muster).** Jedes abgeschlossene
# Einzeltraining (Fold-Symbol x {main, null} x Index) schreibt SOFORT
# einen eigenen Checkpoint (atomic write) nach einem STABILEN, NICHT
# zeitgestempelten Verzeichnis (results/h17_checkpoints/<Symbol>/). Ein
# Neustart, ein TIMEOUT dieses Runners oder ein Abbruch verliert
# HOECHSTENS das gerade laufende einzelne Training - nicht den restlichen
# Fortschritt. EINFACH ERNEUT STARTEN: bereits abgeschlossene Trainings
# werden uebersprungen (Start-Log: 'X/Y Trainings bereits als Checkpoint
# vorhanden, Z noch offen'). Timeout-Default 172800s = 48h PRO AUFRUF
# (Override HANDOFF_H17_TIMEOUT_S); braucht der Gesamtlauf mehrere
# Aufrufe, ist das der VORGESEHENE Betriebsmodus, kein Fehler. Die
# Checkpoints sind gegen die Lauf-Parameter gefingerprintet: ein
# Parameterwechsel (anderes Datenfenster/Seed/Batch/Steps/Device/...)
# unter demselben Checkpoint-Pfad bricht HART ab (CheckpointMismatchError,
# rc=1) statt stillschweigend stale Ergebnisse zu mischen.
#
# EIN Block: H17_VENUE (plus vorgelagerter GPU_CHECK). Env: HARVEST_DIR,
# C12_RESULTS_JSON (Pfad zu einem vorhandenen c12_frag_results.json fuer
# das Redundanz-Gate; ohne diesen Pfad bleibt das Gate NICHT auswertbar,
# aber der Lauf schlaegt NICHT fehl), HANDOFF_DRY_RUN (+HANDOFF_DRY_RC),
# H17_END_DATE (Cutoff, Default 2026-07-04; wird beim ERSTEN Aufruf neben
# den Checkpoints in results/h17_checkpoints/H17_END_DATE.pin
# festgeschrieben und bei jedem weiteren Aufruf wiederverwendet - ein
# Resume ueber mehrere Naechte behaelt so dasselbe registrierte
# Datenfenster, sonst braeche der Checkpoint-Fingerprint absichtlich hart
# ab), H17_CKPT_DIR (Default results/h17_checkpoints, NICHT aendern
# zwischen Aufrufen desselben Laufs - sonst kein Resume!).
# Exit: 0=OK 1=FAIL (inkl. TIMEOUT bei unvollstaendigem Plan - KEIN
# Datenverlust, einfach erneut starten) 2=SKIP.
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HARVEST_DIR="${HARVEST_DIR:-$REPO_ROOT/data/harvest}"
C12_RESULTS_JSON="${C12_RESULTS_JSON:-}"

SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT"
EXCHANGES="bybit,binance"
START_DATE="2026-03-27"
N_PERM=20; STEPS=10000; BATCH_SIZE=2048; SEED=42
TMO_GPU_CHECK=60
TMO_MAIN="${HANDOFF_H17_TIMEOUT_S:-172800}"   # 48h Budget PRO AUFRUF (Resume, s. Kopf)
FORCE_NO_GPU="${HANDOFF_H17_FORCE_NO_GPU:-0}"
CKPT_DIR="${H17_CKPT_DIR:-$SCRIPT_DIR/results/h17_checkpoints}"
mkdir -p "$CKPT_DIR"
# Cutoff (End-Datum) PINNEN (run_h16-Muster): ein Resume-Lauf ueber mehrere
# Naechte MUSS dasselbe registrierte Datenfenster behalten - sonst bricht
# der Checkpoint-Fingerprint (absichtlich) hart ab. Der beim ERSTEN Aufruf
# benutzte Cutoff wird neben den Checkpoints gepinnt und wiederverwendet;
# auch eine spaetere Aenderung des Skript-Defaults kann so einen laufenden
# Resume nicht mehr brechen. (H17_END_DATE-Env uebersteuert; dann bei
# geaenderten Werten Checkpoints loeschen oder H17_CKPT_DIR wechseln.)
END_DATE_PIN="$CKPT_DIR/H17_END_DATE.pin"
if [ -n "${H17_END_DATE:-}" ]; then
    END_DATE="$H17_END_DATE"
elif [ -f "$END_DATE_PIN" ]; then
    END_DATE="$(head -n 1 "$END_DATE_PIN" | tr -d '[:space:]')"
else
    END_DATE="2026-07-04"
fi
printf '%s\n' "$END_DATE" > "$END_DATE_PIN"

PY="${PYTHON:-python3}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"
DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h17_$TS"
mkdir -p "$RUN/h17"
STEPS_TSV="$RUN/steps.tsv"
rec() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$STEPS_TSV"; }

OKN=0; FN=0; SK=0
step() {
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
    local st="FAIL"; if [ "$rc" = "0" ]; then st="OK"; OKN=$((OKN+1)); else FN=$((FN+1)); fi
    rec "$name" "$st" "$rc" "$dur" "$detail"
    echo "[$(date +%H:%M:%S)] END   $name: $st ($detail, ${dur}s)"
}

# GPU_CHECK is a diagnostic PROBE, not a pass/fail step: rc=3 ("kein CUDA")
# is an EXPECTED, informative outcome (e.g. every sandbox run) and must NOT
# count as a runner FAIL — only a genuine crash (rc not in {0,3}) does.
# Sets GPU_CHECK_RC as a side effect; recorded to steps.tsv as INFO/FAIL.
GPU_CHECK_RC=-1
gpu_check_step() {
    local name="GPU_CHECK"
    local log="$RUN/$name.log"; local err="$RUN/$name.err.log"
    echo "[$(date +%H:%M:%S)] START $name"
    local t0; t0=$(date +%s); local rc=-1; local detail=""
    if [ "$DRY" = "1" ]; then echo "[DRY-RUN] $SCRIPT --check-gpu-only" >> "$log"; rc="$DRY_RC"; detail="dry-run rc=$rc"
    else
        if command -v timeout >/dev/null 2>&1; then timeout "$TMO_GPU_CHECK" "$PY" "$SCRIPT" --check-gpu-only >"$log" 2>"$err"; rc=$?
        else "$PY" "$SCRIPT" --check-gpu-only >"$log" 2>"$err"; rc=$?; fi
        if [ "$rc" = "124" ]; then detail="TIMEOUT ${TMO_GPU_CHECK}s"; else detail="rc=$rc"; fi
    fi
    local t1; t1=$(date +%s); local dur=$((t1-t0))
    GPU_CHECK_RC="$rc"
    local st="INFO"
    if [ "$rc" != "0" ] && [ "$rc" != "3" ]; then st="FAIL"; FN=$((FN+1)); fi
    rec "$name" "$st" "$rc" "$dur" "$detail"
    echo "[$(date +%H:%M:%S)] END   $name: $st ($detail, ${dur}s)"
}

echo "RUN_H17 (T3) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "Harvest: $HARVEST_DIR | Panel: $SYMBOLS x {$EXCHANGES}"
echo "Fenster: $START_DATE..$END_DATE | n_perm=$N_PERM steps=$STEPS batch_size=$BATCH_SIZE seed=$SEED"
echo "C12-Ergebnisse fuer Redundanz-Gate: ${C12_RESULTS_JSON:-<keiner - Gate bleibt nicht auswertbar>}"
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

SCRIPT="$REPO_ROOT/scripts/c17_venue.py"
BYBIT_PATH="$HARVEST_DIR/raw/bybit/publicTrade"
BINANCE_PATH="$HARVEST_DIR/raw/binance/publicTrade"

if [ "$DRY" != "1" ] && { [ ! -d "$BYBIT_PATH" ] || [ ! -d "$BINANCE_PATH" ]; }; then
    echo "WARNUNG: Harvester-Pfad fehlt ($BYBIT_PATH bzw. $BINANCE_PATH) - Junction data/harvest pruefen oder HARVEST_DIR setzen"
    rec "H17_VENUE" "SKIP" "0" "0" "Harvester fehlt"; SK=$((SK+1))
else
    # -- GPU-Vorbedingung (verbindlich) -----------------------------------
    gpu_check_step
    GPU_OK=0
    if [ "$DRY" = "1" ]; then GPU_OK=1
    elif [ "$GPU_CHECK_RC" = "0" ]; then GPU_OK=1; fi

    if [ "$GPU_OK" != "1" ] && [ "$FORCE_NO_GPU" != "1" ]; then
        echo "WARNUNG: kein echtes CUDA-Device gefunden (GPU_CHECK rc=$GPU_CHECK_RC) - voller H-17-Lauf waere NIE verdikt-tragend (registrierter Batch>=2048-Bedarf) - uebersprungen. Override: HANDOFF_H17_FORCE_NO_GPU=1 (nur Pipeline-Diagnose, KEIN Gate-Urteil)."
        rec "H17_VENUE" "SKIP" "0" "0" "kein CUDA-Device (GPU_CHECK rc=$GPU_CHECK_RC)"; SK=$((SK+1))
    else
        ARGS=("$SCRIPT" --base-dir "$HARVEST_DIR" --symbols "$SYMBOLS" --exchanges "$EXCHANGES" \
              --start-date "$START_DATE" --end-date "$END_DATE" \
              --n-perm "$N_PERM" --steps "$STEPS" --batch-size "$BATCH_SIZE" \
              --seed "$SEED" --device auto --out-dir "$RUN/h17")
        if [ -n "$C12_RESULTS_JSON" ]; then ARGS+=(--c12-results "$C12_RESULTS_JSON"); fi
        step H17_VENUE "$TMO_MAIN" "${ARGS[@]}"
    fi
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-17 Venue-Fingerprint Mess-Gate (Contrastive-Embedding) - T3"
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\` | Harvest \`$HARVEST_DIR\` (read-only)"
    echo "- **Panel:** $SYMBOLS x {$EXCHANGES}"
    echo "- **Fenster:** $START_DATE..$END_DATE"
    echo "- **n_perm=$N_PERM steps=$STEPS batch_size=$BATCH_SIZE seed=$SEED | F-VENUE BH-FDR a=0.10**"
    echo "- **C12-Redundanz-Gate-Quelle:** ${C12_RESULTS_JSON:-<keine - Gate nicht auswertbar>}"
    echo "- **KAPITALFREI** - reine Struktur-/Existenzfrage, KEINE bps/PnL/Sharpe/Friction."
    echo ""
    echo "## Schritte"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS_TSV" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS_TSV"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    echo "*Gate-Urteil: gate-auditor gegen H-17 (h17/c17_venue_results.json)."
    echo "WEITER verlangt: Held-out-Balanced-Accuracy >=0.60 in >=4/5 Leave-One-Symbol-Out-Folds"
    echo "gegen die 20-Retrainings-Permutations-Null nach BH-FDR alpha=0.10 ueber F-VENUE UND"
    echo "Non-Redundanz-Gate |Spearman rho| < 0.6 gegen die c12_frag-Tages-lambda2/IPR-Serie."
    echo "DROP: Pooled-Accuracy < 0.55 ODER < 4/5 Folds ODER |rho| >= 0.6 (REDUNDANT zu H-12,"
    echo "DROP unabhaengig von der Accuracy). WICHTIG: das JSON-Feld compute.verdict_bearing"
    echo "MUSS true sein, sonst ist der Lauf eine reine Pipeline-Smoke OHNE Gate-Anspruch"
    echo "(kein echtes CUDA-Device gefunden). Kein Graubereich. Ergebnisse hochladen -> GL-Zaehlung.*"
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
