@echo off
title Bybit Edge System
cd /d "%~dp0"

echo ============================================
echo   Scinance 2.0 - Falsifikations-Pipeline
echo ============================================
echo.

REM ---- Venv pruefen ----
if not exist .venv\Scripts\activate.bat goto no_venv
call .venv\Scripts\activate.bat

REM ---- bybit_edge installiert? ----
python -c "import bybit_edge" 2>nul
if errorlevel 1 call :install

REM ---- Status ----
echo [OK] venv aktiv: %VIRTUAL_ENV%
echo [OK] Branch:
git -C "%~dp0" rev-parse --abbrev-ref HEAD 2>nul
echo.
echo [INFO] Scinance-1.0-Live-Pipeline ist DEPRECATED (CLEANUP_PLAN.md).
echo [INFO] Daten kommen aus Harvester (extern) + C-36-Recorder (lokal).
echo.

:menu
echo Was moechtest du tun?
echo.
echo   1 = Tests laufen lassen (pytest unit/)
echo   2 = Recorder STARTEN (Schutzgut #1, laeuft dauerhaft)
echo   3 = Recorder-Status pruefen (read-only)
echo   4 = Welle-2-Lauf (run_wave2.ps1)
echo   5 = Python Shell (interaktiv)
echo   6 = Autostart einrichten/entfernen (Task Scheduler)
echo   7 = Beenden
echo.
set "choice="
set /p choice="Auswahl [1-7]: "

if "%choice%"=="1" goto opt_tests
if "%choice%"=="2" goto opt_recorder_start
if "%choice%"=="3" goto opt_recorder_status
if "%choice%"=="4" goto opt_wave2
if "%choice%"=="5" goto opt_pyshell
if "%choice%"=="6" goto opt_autostart
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

:opt_recorder_start
echo.
echo --- Recorder STARTEN (in neuem Fenster, Ctrl+C dort zum Stoppen) ---
echo Logs unter logs\recorder\recorder_*.log
echo.
start "Scinance C-36 Recorder" powershell.exe -ExecutionPolicy Bypass -NoExit -File "%~dp0start_recorder.ps1"
echo Recorder-Fenster gestartet. Diese Konsole bleibt frei.
echo.
pause
goto menu

:opt_recorder_status
echo.
echo --- Recorder-Status (read-only Schutzgut-Check) ---
python scinance2-impl/handoff_local/check_recording.py
echo.
pause
goto menu

:opt_wave2
echo.
echo --- Welle-2-Lauf (run_wave2.ps1) ---
echo Voll-Lauf: H-04 (Lead-Lag) + H-05 (OFI) + H-06 (PE) + F-WAVE2-Aggregator.
echo Dauer: ca. 2-4h. Bricht NIE mit offenem Prompt ab.
echo.
powershell.exe -ExecutionPolicy Bypass -File scinance2-impl\handoff_local\run_wave2.ps1
echo.
pause
goto menu

:opt_pyshell
echo.
echo --- Python Shell (exit() zum Zurueck) ---
python
goto menu

:opt_autostart
echo.
echo --- Autostart fuer Recorder (Windows Task Scheduler) ---
echo.
echo   I = Installieren (startet Recorder bei jeder Anmeldung)
echo   D = Deinstallieren
echo   S = Status anzeigen
echo   Z = Zurueck
echo.
set "asc="
set /p asc="Auswahl [I/D/S/Z]: "
if /i "%asc%"=="I" goto as_install
if /i "%asc%"=="D" goto as_uninstall
if /i "%asc%"=="S" goto as_status
if /i "%asc%"=="Z" goto menu
echo Ungueltige Auswahl.
goto opt_autostart

:as_install
powershell -ExecutionPolicy Bypass -File "%~dp0install_recorder_autostart.ps1"
pause
goto menu

:as_uninstall
powershell -ExecutionPolicy Bypass -File "%~dp0uninstall_recorder_autostart.ps1"
pause
goto menu

:as_status
powershell -Command "Get-ScheduledTask -TaskName 'Scinance C-36 Recorder' -ErrorAction SilentlyContinue | Select-Object TaskName, State; Get-ScheduledTaskInfo -TaskName 'Scinance C-36 Recorder' -ErrorAction SilentlyContinue | Select-Object LastRunTime, LastTaskResult, NextRunTime"
pause
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
