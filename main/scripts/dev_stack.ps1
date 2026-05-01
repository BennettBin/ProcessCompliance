param(
  [int]$BackendPort = 5174,
  [int]$FrontendPort = 5173,
  [switch]$ForceFreePorts = $true
)

$ErrorActionPreference = "Stop"

function Test-PortInUse {
  param([int]$Port)
  try {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
    return ($null -ne $conns -and $conns.Count -gt 0)
  } catch {
    # Fallback: only treat LISTEN state as "in use"; ignore TIME_WAIT/CLOSE_WAIT.
    $hit = netstat -ano | Select-String "[:\.]$Port\s" | Select-String "LISTENING|LISTEN"
    return [bool]$hit
  }
}

function Get-PortPids {
  param([int]$Port)
  $pids = New-Object System.Collections.Generic.List[int]
  try {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
    foreach ($c in $conns) {
      if ($null -ne $c.OwningProcess) {
        $pids.Add([int]$c.OwningProcess)
      }
    }
  } catch {
    # Fallback: only parse listeners, ignore transient connection states.
    $lines = netstat -ano | Select-String "[:\.]$Port\s" | Select-String "LISTENING|LISTEN"
    foreach ($line in $lines) {
      $parts = ($line.ToString().Trim() -split "\s+")
      if ($parts.Length -gt 0) {
        $pidRaw = $parts[-1]
        if ($pidRaw -match "^\d+$") {
          $pids.Add([int]$pidRaw)
        }
      }
    }
  }  
  return $pids | Select-Object -Unique
}

function Stop-PortListeners {
  param([int]$Port)
  $pids = Get-PortPids -Port $Port
  foreach ($pid in $pids) {
    try {
      if ($pid -ne $PID) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($null -ne $proc) {
          Write-Host "[dev-stack] Stopping PID=$pid Name=$($proc.ProcessName) on port $Port" -ForegroundColor Yellow
        } else {
          Write-Host "[dev-stack] Stopping PID=$pid on port $Port" -ForegroundColor Yellow
        }
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
      }
    } catch {
      # ignore cleanup errors
    }
  }
  Start-Sleep -Milliseconds 300
}

function Stop-ProcessSafe {
  param([System.Diagnostics.Process]$Proc)
  if ($null -ne $Proc) {
    try {
      if (-not $Proc.HasExited) {
        Stop-Process -Id $Proc.Id -Force -ErrorAction SilentlyContinue
      }
    } catch {
      # ignore cleanup errors
    }
  }
}

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$frontendDir = Join-Path $root "frontend"

# Ensure node/npm are discoverable in this shell
if (Test-Path "C:\Program Files\nodejs\node.exe") {
  $env:Path = "C:\Program Files\nodejs;$env:Path"
}
if (Test-Path "C:\Users\Binb_\AppData\Local\JetBrains\acp-agents\.runtimes\node\24.13.0\bin\node.exe") {
  $env:Path = "C:\Users\Binb_\AppData\Local\JetBrains\acp-agents\.runtimes\node\24.13.0\bin;$env:Path"
}

if (Test-PortInUse -Port $BackendPort) {
  if ($ForceFreePorts) {
    Write-Host "[dev-stack] Port $BackendPort is in use, trying to free it..." -ForegroundColor Yellow
    Stop-PortListeners -Port $BackendPort
  } else {
    throw "Backend port $BackendPort is already in use. Please free it first."
  }
}
if (Test-PortInUse -Port $FrontendPort) {
  if ($ForceFreePorts) {
    Write-Host "[dev-stack] Port $FrontendPort is in use, trying to free it..." -ForegroundColor Yellow
    Stop-PortListeners -Port $FrontendPort
  } else {
    throw "Frontend port $FrontendPort is already in use. Please free it first."
  }
}

if (Test-PortInUse -Port $BackendPort) {
  throw "Backend port $BackendPort is still in use after cleanup."
}
if (Test-PortInUse -Port $FrontendPort) {
  throw "Frontend port $FrontendPort is still in use after cleanup."
}

$backend = $null
$frontend = $null

try {
  Write-Host "[dev-stack] Starting backend on http://127.0.0.1:$BackendPort" -ForegroundColor Cyan
  $backend = Start-Process `
    -FilePath "python" `
    -ArgumentList "-m","uvicorn","backend.main:app","--reload","--host","127.0.0.1","--port",$BackendPort `
    -WorkingDirectory $root `
    -PassThru

  Start-Sleep -Seconds 1

  Write-Host "[dev-stack] Starting frontend on http://127.0.0.1:$FrontendPort" -ForegroundColor Cyan
  $frontend = Start-Process `
    -FilePath "npm.cmd" `
    -ArgumentList "run","dev" `
    -WorkingDirectory $frontendDir `
    -PassThru

  Write-Host "[dev-stack] Running. Press Ctrl+C to stop and release ports." -ForegroundColor Green

  while ($true) {
    if ($backend.HasExited) {
      throw "Backend exited unexpectedly."
    }
    if ($frontend.HasExited) {
      throw "Frontend exited unexpectedly."
    }
    Start-Sleep -Seconds 1
  }
}
finally {
  Write-Host "[dev-stack] Stopping services and releasing ports..." -ForegroundColor Yellow
  Stop-ProcessSafe -Proc $frontend
  Stop-ProcessSafe -Proc $backend
  Start-Sleep -Milliseconds 300
  Write-Host "[dev-stack] Done." -ForegroundColor Yellow
}
