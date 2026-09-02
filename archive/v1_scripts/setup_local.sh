#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Bybit Edge System — Lokales Setup (Windows/Linux/macOS)
# ============================================================================
# Voraussetzungen:
#   - Git installiert
#   - Miniconda/Anaconda installiert (https://docs.anaconda.com/miniconda/)
#   - NVIDIA CUDA Toolkit 12.x installiert (optional, fuer GPU-Module)
#
# Ausfuehrung:
#   Windows (Git Bash / WSL2):  bash scripts/setup_local.sh
#   Linux/macOS:                bash scripts/setup_local.sh
# ============================================================================

echo "============================================"
echo "  Bybit Edge System — Setup"
echo "============================================"
echo ""

# ---------- 1. Repository klonen / aktualisieren ----------
REPO_URL="https://github.com/wasolldas/scinance.git"
BRANCH="claude/subagent-prd-development-T16fE"

if [ ! -d ".git" ]; then
    echo "[1/8] Klone Repository..."
    git clone -b "$BRANCH" "$REPO_URL" .
else
    echo "[1/8] Repository existiert — aktualisiere..."
    git fetch origin "$BRANCH"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
fi
echo "     Branch: $(git branch --show-current)"
echo "     Commit: $(git log --oneline -1)"
echo ""

# ---------- 2. Conda Environment erstellen ----------
echo "[2/8] Erstelle Conda Environment..."
if conda info --envs 2>/dev/null | grep -q "bybit-edge"; then
    echo "     Environment 'bybit-edge' existiert bereits — aktualisiere..."
    conda env update -f environment.yml --prune
else
    conda env create -f environment.yml
fi
echo ""

# ---------- 3. Environment aktivieren ----------
echo "[3/8] Aktiviere Environment..."
# In einem Script muss conda ueber 'eval' initialisiert werden
eval "$(conda shell.bash hook 2>/dev/null)"
conda activate bybit-edge
echo "     Python: $(python --version)"
echo "     Prefix: $CONDA_PREFIX"
echo ""

# ---------- 4. Projekt installieren (editable) ----------
echo "[4/8] Installiere Projekt im Editable-Modus..."
pip install -e ".[dev]" --quiet
echo "     bybit-edge installiert."
echo ""

# ---------- 5. CUDA pruefen (optional) ----------
echo "[5/8] Pruefe CUDA/GPU..."
python -c "
try:
    import torch
    if torch.cuda.is_available():
        print(f'     GPU: {torch.cuda.get_device_name(0)}')
        print(f'     CUDA: {torch.version.cuda}')
        print(f'     VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB')
    else:
        print('     Keine GPU erkannt — CPU-Modus (OK fuer Quick Wins)')
except ImportError:
    print('     PyTorch nicht installiert — CPU-only Modus')
    print('     Fuer GPU: conda install pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia')
"
echo ""

# ---------- 6. Tests ausfuehren ----------
echo "[6/8] Fuehre Tests aus..."
python -m pytest tests/unit/ -v --tb=short 2>&1 | tail -20
RESULT=$?
echo ""
if [ $RESULT -eq 0 ]; then
    echo "     ALLE TESTS BESTANDEN"
else
    echo "     ACHTUNG: Einige Tests fehlgeschlagen!"
    echo "     Pruefe Fehler oben und installiere ggf. fehlende Abhaengigkeiten."
fi
echo ""

# ---------- 7. .env Datei erstellen ----------
echo "[7/8] Erstelle .env Konfiguration..."
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
# Bybit Edge System — Konfiguration
# Hole Testnet-Keys von: https://testnet.bybit.com/app/user/api-management

BYBIT_API_KEY=dein_testnet_api_key_hier
BYBIT_API_SECRET=dein_testnet_api_secret_hier
BYBIT_TESTNET=true

# Log-Level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Daten-Verzeichnis (absoluter Pfad oder relativ zum Projektordner)
# BYBIT_DATA_DIR=data
ENVEOF
    echo "     .env erstellt — BITTE API-KEYS EINTRAGEN!"
else
    echo "     .env existiert bereits — ueberspringe."
fi
echo ""

# ---------- 8. Daten-Verzeichnisse erstellen ----------
echo "[8/8] Erstelle Verzeichnisse..."
mkdir -p data/parquet logs
echo "     data/ und logs/ erstellt."
echo ""

# ---------- Zusammenfassung ----------
echo "============================================"
echo "  Setup abgeschlossen!"
echo "============================================"
echo ""
echo "  Naechste Schritte:"
echo ""
echo "  1. API-Keys eintragen:"
echo "     Oeffne .env und trage deine Bybit Testnet Keys ein"
echo "     (https://testnet.bybit.com/app/user/api-management)"
echo ""
echo "  2. Environment aktivieren:"
echo "     conda activate bybit-edge"
echo ""
echo "  3. Tests laufen lassen:"
echo "     pytest tests/unit/ -v"
echo ""
echo "  4. Collector starten (Daten sammeln):"
echo "     python -m bybit_edge"
echo ""
echo "  5. Einzelne Module testen:"
echo "     python -c \"from bybit_edge.layers.l5_risk.m22_funding_pressure import M22FundingPressure; print('M22 OK')\""
echo ""
echo "  6. Backtest starten (sobald Daten vorhanden):"
echo "     python scripts/run_backtest.py --symbol BTCUSDT --strategy S3"
echo ""
echo "============================================"
