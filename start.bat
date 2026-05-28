@echo off
title Bybit Edge System
cd /d "%~dp0"

echo ============================================
echo   Bybit Edge System
echo ============================================
echo.

:: Venv aktivieren
if not exist .venv\Scripts\activate.bat (
    echo [ERROR] Kein .venv gefunden! Erstelle es zuerst:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate.bat
    echo   pip install -e ".[dev]"
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat

:: Pruefen ob bybit_edge installiert ist
python -c "import bybit_edge" 2>nul
if errorlevel 1 (
    echo [SETUP] Installiere bybit-edge...
    pip install -e ".[dev]" --quiet
)

:: .env pruefen
if not exist .env (
    echo [WARNUNG] Keine .env Datei gefunden!
    echo Erstelle .env mit deinen Bybit Demo API-Keys.
    echo.
    echo Beispiel:
    echo   BYBIT_API_KEY=dein_key
    echo   BYBIT_API_SECRET=dein_secret
    echo   BYBIT_DEMO=true
    echo   BYBIT_TESTNET=false
    echo   LOG_LEVEL=INFO
    echo.
    pause
    exit /b 1
)

:: Status anzeigen
echo [OK] venv aktiv: %VIRTUAL_ENV%
python -c "from bybit_edge.config import rest_base_url, BYBIT_DEMO, BYBIT_TESTNET, PRIMARY_SYMBOL; print(f'[OK] Modus: {\"DEMO\" if BYBIT_DEMO else \"TESTNET\" if BYBIT_TESTNET else \"LIVE\"}'); print(f'[OK] URL: {rest_base_url()}'); print(f'[OK] Symbol: {PRIMARY_SYMBOL}')"
echo.

:: Menu
:menu
echo Was moechtest du tun?
echo.
echo   1 = Tests laufen lassen (pytest)
echo   2 = System starten (Collector + Pipeline)
echo   3 = Monitor (Position + PnL + Equity)
echo   4 = Quick-Check (alle Module importieren)
echo   5 = Python Shell (interaktiv)
echo   6 = Beenden
echo.
set /p choice="Auswahl [1-6]: "

if "%choice%"=="1" (
    echo.
    echo --- Tests ---
    pytest tests/unit/ -v --tb=short
    echo.
    goto menu
)
if "%choice%"=="2" (
    echo.
    echo --- Starte Bybit Edge System ---
    echo Druecke Ctrl+C zum Beenden.
    echo.
    python -m bybit_edge
    goto menu
)
if "%choice%"=="3" (
    echo.
    echo --- Monitor (Ctrl+C zum Zurueck) ---
    python -m bybit_edge.monitor --interval 10
    goto menu
)
if "%choice%"=="4" (
    echo.
    echo --- Quick-Check ---
    python -c "from bybit_edge.pipeline import Pipeline; from bybit_edge.strategies import Strategy3PreSettlement; from bybit_edge.decision_aggregator import DecisionAggregator; print('Alle Module OK!')"
    echo.
    goto menu
)
if "%choice%"=="5" (
    echo.
    echo --- Python Shell (exit() zum Zurueck) ---
    python
    goto menu
)
if "%choice%"=="6" (
    exit /b 0
)

echo Ungueltige Auswahl.
goto menu
