# ========================================================================
# start_recorder.ps1 - C-36 Recording Engine launcher (Schutzgut #1)
#
# Aufruf (keine Pflicht-Parameter):
#   powershell -ExecutionPolicy Bypass -File .\start_recorder.ps1
#
# Was er tut:
#   - startet "python -m bybit_edge.recorder" mit 5 Symbolen
#   - leitet stdout+stderr in ein zeitstempel-Log unter logs\recorder\
#   - laeuft mit BelowNormal-Prioritaet (Recorder darf interaktive Arbeit
#     nicht ausbremsen)
#   - laeuft unbegrenzt (default --duration unbounded, Ring-Buffer Cap aus
#     storage.py / DEC-07)
#
# Stoppen:
#   Ctrl+C im Fenster ODER 'taskkill /F /PID <pid>' (PID wird beim Start
#   ausgegeben).
#
# Daten:
#   data\parquet\recording_f0\<stream>\... (rpi_orderbook, insurance_pool,
#   premium_index_kline, adl_alerts (phantom), option_tickers (NO_DATA))
#
# Schutzgut #1 (CLAUDE.md): dieser Recorder darf nicht laenger als noetig
# offline sein. Sunset-Review-Uhr laeuft seit 2026-06-11, erster Review
# ca. 2026-09-11.
# ========================================================================

$ErrorActionPreference = "Stop"

# An Repo-Root wechseln (das Skript steht im Root)
Set-Location -LiteralPath $PSScriptRoot

# ----------------------------------------------------------------------
# Single-Instance-Guard (Schutzgut #1: NIE zwei Writer auf recording_f0).
# Verhindert, dass ein manueller Start + der Autostart-Task (oder zwei
# manuelle Starts) gleichzeitig in denselben Parquet-Pfad schreiben und
# den Audit-Bestand mit Duplikaten verschmutzen.
# Pruefung gegen die Kommandozeile aller python.exe-Prozesse; der eigene
# Kind-Prozess existiert zu diesem Zeitpunkt noch nicht -> kein Selbst-Treffer.
# ----------------------------------------------------------------------
$running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*bybit_edge.recorder*" }
if ($running) {
    $pids = ($running | ForEach-Object { $_.ProcessId }) -join ", "
    Write-Host ""
    Write-Host "Recorder laeuft bereits (PID(s): $pids)." -ForegroundColor Yellow
    Write-Host "Kein zweiter Start - Schutzgut #1 (ein Writer pro recording_f0)." -ForegroundColor Yellow
    Write-Host "Stoppen mit:  Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" |" -ForegroundColor DarkGray
    Write-Host "              ? { \$_.CommandLine -like '*bybit_edge.recorder*' } | %% { Stop-Process \$_.ProcessId -Force }" -ForegroundColor DarkGray
    exit 0
}

# venv aktivieren falls vorhanden (Idiom aus start.bat)
if (Test-Path .\.venv\Scripts\Activate.ps1) {
    & .\.venv\Scripts\Activate.ps1
}

# Log-Verzeichnis
$logDir = Join-Path $PSScriptRoot "logs\recorder"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

# Zeitstempel-Log
$stamp  = Get-Date -Format "yyyyMMdd_HHmmss"
$logOut = Join-Path $logDir "recorder_$stamp.log"
$logErr = Join-Path $logDir "recorder_$stamp.err.log"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  C-36 Recording Engine - Schutzgut #1" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Streams:  rpi_orderbook, insurance_pool, premium_index_kline,"
Write-Host "          option_tickers (NO_DATA known), adl_alerts (phantom)"
Write-Host "Symbols:  BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT"
Write-Host "Options:  BTC, ETH"
Write-Host "Output:   data\parquet\recording_f0\"
Write-Host "Logs:     $logOut"
Write-Host "Stop:     Ctrl+C in diesem Fenster"
Write-Host ""

# Recorder starten - direkt im Fenster (nicht detached), damit Ctrl+C wirkt.
# BelowNormal-Prioritaet, damit der Recorder kein interaktives Arbeiten ausbremst.
$pythonArgs = @(
    "-m", "bybit_edge.recorder",
    "--symbols", "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT",
    "--options", "BTC,ETH"
)

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName  = "python"
$psi.Arguments = ($pythonArgs -join " ")
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError  = $true
$psi.UseShellExecute        = $false
$psi.WorkingDirectory       = $PSScriptRoot

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi

# Output-Streams nach Log und Terminal in einem Schritt
$proc.add_OutputDataReceived({
    param($s, $e)
    if ($null -ne $e.Data) {
        $e.Data | Out-File -FilePath $logOut -Append -Encoding ASCII
        Write-Host $e.Data
    }
})
$proc.add_ErrorDataReceived({
    param($s, $e)
    if ($null -ne $e.Data) {
        $e.Data | Out-File -FilePath $logErr -Append -Encoding ASCII
        Write-Host $e.Data -ForegroundColor Yellow
    }
})

$null = $proc.Start()
$null = $proc.Handle   # Cache Handle (PS 5.1 Bug-Workaround, exit code)
$proc.PriorityClass = "BelowNormal"
$proc.BeginOutputReadLine()
$proc.BeginErrorReadLine()

Write-Host "Recorder gestartet, PID=$($proc.Id), Prioritaet=BelowNormal." -ForegroundColor Green
Write-Host ""

# Auf Prozess warten (Ctrl+C reicht durch zu python -> sauberer Shutdown)
try {
    $proc.WaitForExit()
}
finally {
    if (-not $proc.HasExited) {
        Write-Host "Sende Stop-Signal an Recorder (PID $($proc.Id))..." -ForegroundColor Yellow
        $proc.Kill()
    }
    $exit = $proc.ExitCode
    Write-Host ""
    Write-Host "Recorder beendet, ExitCode=$exit." -ForegroundColor Cyan
    Write-Host "Logs: $logOut"
    exit $exit
}
