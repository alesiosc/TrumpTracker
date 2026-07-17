# ensure_tv_watcher.ps1  (TrumpTracker)
# Heals the TradingView Connect Watcher: starts it if not running.
$ErrorActionPreference = 'SilentlyContinue'

$watcherScript = "D:\MyPythonProjects_2\AIO_internals_equities_ma_x3_indicator\docs\13-TS-DASH-v4.0\Module-04 - INDICATORS\tradingview_connect_watcher.py"
$pythonw = "$env:LOCALAPPDATA\Programs\Python\Python313\pythonw.exe"

$alive = $false
$running = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" |
    Where-Object { $_.CommandLine -like "*tradingview_connect_watcher*" }
if ($running) { $alive = $true }

if ($alive) { exit 0 }

Start-Process -FilePath $pythonw -ArgumentList $watcherScript -WindowStyle Hidden
exit 0
