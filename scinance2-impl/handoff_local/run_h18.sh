#!/usr/bin/env bash
# ========================================================================
# run_h18.sh - T3 LOCAL_LONG Runner (Scinance 2.0 Welle 5, H-18)
#
# H-18 = GL-006/H-04 Lead-Lag High-N-Surrogat-Aufloesungs-Audit.
# **AUFLOESUNGS-AUDIT, KEINE NEU-ADJUDIKATION.** Re-Execution der byte-
# identischen, bereits adjudizierten F-LEADLAG-Pipeline aus GL-006 mit GENAU
# EINER Aenderung: n_surrogates 200 -> 100.000, als GPU-Tensor-Batches
# (torch.fft.rfft/irfft Phase-Shuffle-Primitive, batched TE-Histogramme via
# scatter_add, batched CWT via FFT-Convolution). Das GL-006-Verdikt bleibt
# append-only UNVERAENDERT stehen; dieser Runner schreibt NICHT gate_log.md.
# KAPITALFREI: identisch GL-006 — keine bps/Edge/PnL-Metrik.
#
# **Compute-Gating-Pflicht:** ein voller 100k-Surrogat-Lauf ist NUR auf
# einem echten CUDA-Device verdikt-tragend. Ablauf:
#   (1) H18_SELFTEST  - Methodik-Aequivalenz-Test gegen die ORIGINALE
#       c17_c41_lead_lag-Pipeline bei kleinem N (synthetischer Input, kein
#       Datenzugriff) - MUSS rc=0 liefern, sonst FAIL (Regression).
#   (2) H18_GPU_CHECK - `--check-gpu-only`; rc 0 = CUDA vorhanden, rc 3 =
#       kein CUDA (kein Fehler, sauberer SKIP fuer Schritt 3).
#   (3) H18_AUDIT     - nur bei rc 0 aus (2): voller Lauf, 100.000
#       Surrogate, Seed 42, F-LEADLAG BH-FDR alpha=0.10, --backend cuda.
#
#   bash scinance2-impl/handoff_local/run_h18.sh
#
# Exit-Code: 0 = OK (inkl. GPU-los mit sauberem SKIP von Schritt 3)
#            1 = FAIL (Selftest-Regression ODER Audit-Fehler auf GPU)
#            2 = kein FAIL, aber SKIP (kein CUDA-Device gefunden)
# Ergebnisse: scinance2-impl/handoff_local/results/h18_<timestamp>/h18/...
#             + SUMMARY_<datum>.md
#
# Env-Overrides: HANDOFF_DUCKDB=<pfad>, PYTHON=<python-exe>,
#                HANDOFF_DRY_RUN=1 (Mechanik-Test ohne echte Laeufe,
#                HANDOFF_DRY_RC=1 -> FAILs).
# ========================================================================
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DUCKDB_PATH="${HANDOFF_DUCKDB:-$REPO_ROOT/data/bybit_edge.duckdb}"

PAIR="BTCUSDT,ETHUSDT"
N_WINDOWS=2
N_SURROGATES=100000
SEED=42
TMO_SELFTEST=600     # 10 min - kleine synthetische Aequivalenzpruefung
TMO_GPU_CHECK=120     # 2 min - reine CUDA-Statusabfrage
TMO_AUDIT=10800       # 3 h Budget (Registry-Schaetzung ~1h auf RTX 5060 Ti)

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
fi
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$REPO_ROOT"

DRY=0; if [ "${HANDOFF_DRY_RUN:-0}" != "0" ] && [ -n "${HANDOFF_DRY_RUN:-}" ]; then DRY=1; fi
DRY_RC="${HANDOFF_DRY_RC:-0}"

TS="$(date -u +%Y%m%d_%H%M%S)"; SUMD="$(date -u +%Y-%m-%d)"
RUN="$SCRIPT_DIR/results/h18_$TS"
mkdir -p "$RUN/h18"
STEPS="$RUN/steps.tsv"
rec() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$STEPS"; }

OKN=0; FN=0; SK=0
LAST_RC=0
step() {
    # <name> <timeout_s> <cmd...> ; rc 3 aus H18_GPU_CHECK -> SKIP (kein Fehler).
    local name="$1"; local tmo="$2"; shift 2
    local log="$RUN/$name.log"; local err="$RUN/$name.err.log"
    echo "[$(date +%H:%M:%S)] START $name: $PY $*"
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
    elif [ "$name" = "H18_GPU_CHECK" ] && [ "$rc" = "3" ]; then st="SKIP"; SK=$((SK+1)); detail="kein CUDA-Device gefunden"
    else FN=$((FN+1)); fi
    rec "$name" "$st" "$rc" "$dur" "$detail"
    echo "[$(date +%H:%M:%S)] END   $name: $st ($detail, ${dur}s) log=$log"
    LAST_RC="$rc"
}

echo "RUN_H18 (T3) - Repo: $REPO_ROOT - Ergebnisse: $RUN"
echo "H-18 ist AUFLOESUNGS-AUDIT von GL-006/H-04, KEINE NEU-ADJUDIKATION. DuckDB: $DUCKDB_PATH"
[ "$DRY" = "1" ] && echo "ACHTUNG: HANDOFF_DRY_RUN aktiv."

SCRIPT="$REPO_ROOT/scripts/c18_leadlag_audit.py"

# -- Schritt 1: Methodik-Aequivalenz-Test (immer, unabhaengig von GPU) ---
step H18_SELFTEST "$TMO_SELFTEST" "$SCRIPT" --self-test --seed "$SEED" --out "$RUN/h18"
if [ "$LAST_RC" != "0" ] && [ "$DRY" != "1" ]; then
    echo "FAIL: H18_SELFTEST — Methodik-Aequivalenz zur ORIGINALEN c17_c41_lead_lag-Pipeline gebrochen. Kein Audit-Lauf."
fi

# -- Schritt 2: GPU/CUDA-Status (Compute-Gating-Pflicht) ------------------
step H18_GPU_CHECK "$TMO_GPU_CHECK" "$SCRIPT" --check-gpu-only --out "$RUN/h18"
GPU_RC="$LAST_RC"

# -- Schritt 3: voller 100k-Surrogat-Audit-Lauf, nur bei echtem CUDA ------
if [ "$DRY" = "1" ]; then
    step H18_AUDIT "$TMO_AUDIT" "$SCRIPT" \
        --db "$DUCKDB_PATH" --pair "$PAIR" --windows "$N_WINDOWS" \
        --surrogates "$N_SURROGATES" --seed "$SEED" --db-copy --backend cuda \
        --out "$RUN/h18"
elif [ "$GPU_RC" = "0" ]; then
    if [ ! -f "$DUCKDB_PATH" ]; then
        rec H18_AUDIT SKIP 0 0 "DuckDB fehlt ($DUCKDB_PATH)"; SK=$((SK+1))
        echo "SKIP: H18_AUDIT — DuckDB fehlt ($DUCKDB_PATH)"
    else
        step H18_AUDIT "$TMO_AUDIT" "$SCRIPT" \
            --db "$DUCKDB_PATH" --pair "$PAIR" --windows "$N_WINDOWS" \
            --surrogates "$N_SURROGATES" --seed "$SEED" --db-copy --backend cuda \
            --out "$RUN/h18"
    fi
else
    rec H18_AUDIT SKIP 0 0 "kein CUDA-Device (H18_GPU_CHECK rc=$GPU_RC) — 100k-Surrogat-Lauf ohne CUDA ist NICHT verdikt-tragend"
    SK=$((SK+1))
    echo "SKIP: H18_AUDIT — kein CUDA-Device, ein voller Lauf waere nicht verdikt-tragend (Compute-Gating-Pflicht)."
fi

EXIT=0; [ "$FN" -gt 0 ] && EXIT=1; [ "$FN" -eq 0 ] && [ "$SK" -gt 0 ] && EXIT=2
SUMMARY="$RUN/SUMMARY_$SUMD.md"
{
    echo "# H-18 GL-006/H-04 Lead-Lag High-N-Surrogat-Aufloesungs-Audit — T3 (Welle 5)"
    echo ""
    echo "**AUFLOESUNGS-AUDIT, KEINE NEU-ADJUDIKATION.** Das GL-006-Verdikt (WEITER,"
    echo "Mess-Existenz, Kapital PARK) bleibt append-only UNVERAENDERT stehen. Dieser"
    echo "Runner schreibt NICHT \`gate_log.md\` — ein neuer, eigener GL-Eintrag"
    echo "(GL-014ff.) wird SPAETER manuell aus \`h18/c18_leadlag_audit_results.json\`"
    echo "erstellt."
    echo ""
    echo "- **Erzeugt:** $(date -u +'%Y-%m-%d %H:%M:%S') UTC"
    echo "- **Run-Dir:** \`$RUN\` | DuckDB \`$DUCKDB_PATH\` (read-only, --db-copy)"
    echo "- **Methodik (vorregistriert, EINZIGE Aenderung ggue. GL-006):** n_surrogates 200 -> $N_SURROGATES, Paar $PAIR, Fenster=$N_WINDOWS, Seed=$SEED, F-LEADLAG BH-FDR alpha=0.10 je Fenster"
    echo "- **KAPITALFREI** — identisch GL-006, keine bps/Edge/PnL/Friction-Metrik."
    echo ""
    echo "## Schritte"
    echo ""
    echo "| Schritt | Status | rc | Dauer | Detail |"
    echo "|---|---|---:|---:|---|"
    if [ -f "$STEPS" ]; then while IFS=$'\t' read -r n s r d de; do echo "| $n | $s | $r | ${d}s | $de |"; done < "$STEPS"; fi
    echo ""
    echo "**Gesamt:** ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
    echo ""
    echo "*Ergebnis: \`h18/c18_leadlag_audit_results.json\` (+ .md) enthaelt die"
    echo "vorregistrierten Teil-Claims T1 (12 GL-006-Stage-1-FDR-Survivor bei p<=1e-3"
    echo "neu signifikant) und T2 (ETH->BTC F0 Lag1/Lag2 loesen sich mit >5 MC-SE auf)"
    echo "als separate Felder, plus \`verdict_carrying\` (nur bei echtem CUDA + 100k"
    echo "Surrogaten true). Kein automatisches Gate-Urteil — gate-auditor liest den"
    echo "Payload und erstellt manuell GL-014ff.*"
} > "$SUMMARY"
echo ""; echo "SUMMARY: $SUMMARY"; echo "Gesamt: ok=$OKN fail=$FN skip=$SK -> exit $EXIT"
exit "$EXIT"
