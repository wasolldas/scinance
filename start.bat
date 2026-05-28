@echo off
title Bybit Edge System
cd /d "%~dp0"

echo ============================================
echo   Bybit Edge System
echo ============================================
echo.

REM ---- Venv pruefen ----
if not exist .venv\Scripts\activate.bat goto no_venv
call .venv\Scripts\activate.bat

REM ---- bybit_edge installiert? ----
python -c "import bybit_edge" 2>nul
if errorlevel 1 call :install

REM ---- .env pruefen ----
if not exist .env goto no_env

REM ---- Status ----
echo [OK] venv aktiv: %VIRTUAL_ENV%
python -c "from bybit_edge.config import rest_base_url, BYBIT_DEMO, BYBIT_TESTNET, PRIMARY_SYMBOL; m='DEMO' if BYBIT_DEMO else ('TESTNET' if BYBIT_TESTNET else 'LIVE'); print('[OK] Modus:', m); print('[OK] URL:', rest_base_url()); print('[OK] Symbol:', PRIMARY_SYMBOL)"
echo.

:menu
echo Was moechtest du tun?
echo.
echo   1 = Tests laufen lassen (pytest)
echo   2 = System starten (Collector + Pipeline)
echo   3 = Monitor (Position + PnL + Equity)
echo   4 = Backtest (Strategie-Vergleich auf Historie)
echo   5 = Quick-Check (alle Module importieren)
echo   6 = Python Shell (interaktiv)
echo   7 = Beenden
echo.
set "choice="
set /p choice="Auswahl [1-7]: "

if "%choice%"=="1" goto opt_tests
if "%choice%"=="2" goto opt_system
if "%choice%"=="3" goto opt_monitor
if "%choice%"=="4" goto opt_backtest
if "%choice%"=="5" goto opt_quickcheck
if "%choice%"=="6" goto opt_pyshell
if "%choice%"=="7" goto opt_end
echo Ungueltige Auswahl.
echo.
goto menu

:opt_tests
echo.
echo --- Tests ---
pytest tests/unit/ -v --tb=short
echo.
pause
goto menu

:opt_system
echo.
echo --- Starte Bybit Edge System (Ctrl+C zum Beenden, dann N) ---
echo.
python -m bybit_edge
echo.
goto menu

:opt_monitor
echo.
echo --- Monitor (Ctrl+C zum Zurueck, dann N) ---
echo.
python -m bybit_edge.monitor --interval 10
echo.
goto menu

:opt_backtest
echo.
set "months="
set /p months="Wie viele Monate Historie? [6]: "
if "%months%"=="" set months=6
echo --- Backtest (%months% Monate) ---
python scripts/backtest.py --symbol BTCUSDT --interval 5 --months %months%
echo.
pause
goto menu

:opt_quickcheck
echo.
echo --- Quick-Check ---
python -c "from bybit_edge.pipeline import Pipeline; from bybit_edge.strategies import Strategy3PreSettlement; from bybit_edge.decision_aggregator import DecisionAggregator; print('Alle Module OK')"
echo.
pause
goto menu

:opt_pyshell
echo.
echo --- Python Shell (exit() zum Zurueck) ---
python
goto menu

:opt_end
exit /b 0

REM ================= Hilfsroutinen =================

:install
echo [SETUP] Installiere bybit-edge...
pip install -e ".[dev]" --quiet
goto :eof

:no_venv
echo [ERROR] Kein .venv gefunden! Erstelle es zuerst:
echo   python -m venv .venv
echo   .venv\Scripts\activate.bat
echo   pip install -e ".[dev]"
pause
exit /b 1

:no_env
echo [WARNUNG] Keine .env Datei gefunden!
echo Erstelle .env mit deinen Bybit Demo API-Keys:
echo.
echo   BYBIT_API_KEY=dein_key
echo   BYBIT_API_SECRET=dein_secret
echo   BYBIT_DEMO=true
echo   BYBIT_TESTNET=false
echo   LOG_LEVEL=INFO
echo.
pause
exit /b 1
