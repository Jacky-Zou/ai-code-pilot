param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [switch]$Install
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"

function Assert-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

function Assert-PortFree {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($connection) {
        throw "Port $Port is already in use by PID $($connection.OwningProcess). Stop that process or choose another port."
    }
}

function Test-HttpOk {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Get-CleanPath {
    $blockedPatterns = @(
        "\\.sbx-denybin$",
        "\\.codex\\tmp\\arg0"
    )
    $entries = $env:PATH -split ";" | Where-Object {
        $entry = $_.Trim()
        if (-not $entry) {
            return $false
        }
        foreach ($pattern in $blockedPatterns) {
            if ($entry -match $pattern) {
                return $false
            }
        }
        return $true
    }
    return ($entries -join ";")
}

function Convert-ToSingleQuotedPowerShell {
    param([string]$Value)
    return "'" + $Value.Replace("'", "''") + "'"
}

Assert-Command "python"
Assert-Command "npm"

$backendAlreadyRunning = $false
if (Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue) {
    if (Test-HttpOk "http://localhost:$BackendPort/api/health") {
        $backendAlreadyRunning = $true
        Write-Host "[AICodePilot] Reusing backend already running on http://localhost:$BackendPort"
    } else {
        Assert-PortFree $BackendPort
    }
}

$frontendAlreadyRunning = $false
if (Get-NetTCPConnection -LocalPort $FrontendPort -State Listen -ErrorAction SilentlyContinue) {
    if (Test-HttpOk "http://localhost:$FrontendPort") {
        $frontendAlreadyRunning = $true
        Write-Host "[AICodePilot] Frontend already responds on http://localhost:$FrontendPort"
    } else {
        Assert-PortFree $FrontendPort
    }
}

if ($Install) {
    Write-Host "[AICodePilot] Installing backend dependencies..."
    Push-Location $backendDir
    try {
        python -m pip install -r requirements.txt
    } finally {
        Pop-Location
    }

    Write-Host "[AICodePilot] Installing frontend dependencies..."
    Push-Location $frontendDir
    try {
        npm install
    } finally {
        Pop-Location
    }
}

$frontendProjectPath = $repoRoot.Replace("\", "/")
$cleanPath = Get-CleanPath
$quotedCleanPath = Convert-ToSingleQuotedPowerShell $cleanPath
$quotedBackendDir = Convert-ToSingleQuotedPowerShell $backendDir
$quotedFrontendDir = Convert-ToSingleQuotedPowerShell $frontendDir
$quotedProjectPath = Convert-ToSingleQuotedPowerShell $frontendProjectPath

$backendCommand = "`$env:PATH=$quotedCleanPath; Set-Location -LiteralPath $quotedBackendDir; python -m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort"
$frontendCommand = "`$env:PATH=$quotedCleanPath; `$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:$BackendPort'; `$env:NEXT_PUBLIC_DEFAULT_PROJECT_PATH=$quotedProjectPath; Set-Location -LiteralPath $quotedFrontendDir; npm run dev -- --hostname 127.0.0.1 --port $FrontendPort"

if (-not $backendAlreadyRunning) {
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand) -WorkingDirectory $backendDir
    Start-Sleep -Seconds 2
}

if (-not $frontendAlreadyRunning) {
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand) -WorkingDirectory $frontendDir
}

Write-Host "[AICodePilot] Started local development windows."
Write-Host "Backend:  http://localhost:$BackendPort"
Write-Host "Frontend: http://localhost:$FrontendPort"
Write-Host "Stop: close the two PowerShell windows or press Ctrl+C in each one."
