# ensure_trump_keepalive.ps1  (TrumpTracker)
# Self-heals the browser failsafe: if keep_trump_tabs.py is not running, start it.
# Intended to run every 1 min via Scheduled Task so the keepalive
# restarts itself even if it ever dies.
$ErrorActionPreference = 'SilentlyContinue'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$py  = "$env:LOCALAPPDATA\Programs\Python\Python313\pythonw.exe"
$script = Join-Path $dir "keep_trump_tabs.py"
$lock = Join-Path $dir ".trump_keepalive.lock"

function Test-Alive($pidStr) {
    if (-not $pidStr) { return $false }
    $p = Get-Process -Id $pidStr -ErrorAction SilentlyContinue
    return ($null -ne $p)
}

# Primary check: the lock file the keepalive itself writes
$alive = $false
if (Test-Path $lock) {
    $pidStr = (Get-Content $lock -ErrorAction SilentlyContinue).Trim()
    if (Test-Alive $pidStr) { $alive = $true }
}
# Fallback: scan for the process by command line.
if (-not $alive) {
    $running = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" |
        Where-Object { $_.CommandLine -like "*keep_trump_tabs.py*" }
    if ($running) { $alive = $true }
}

if ($alive) {
    exit 0
}

Start-Process -FilePath $py -ArgumentList $script -WorkingDirectory $dir -WindowStyle Hidden
exit 0
