# nullbook installer for Windows — irm https://raw.githubusercontent.com/jfornear/nullbook/main/install.ps1 | iex
#Requires -Version 5.1
$ErrorActionPreference = "Stop"

# ── Colors ────────────────────────────────────────────
function Info    { param($msg) Write-Host "  [info]  $msg" -ForegroundColor Cyan }
function Success { param($msg) Write-Host "  [ok]    $msg" -ForegroundColor Green }
function Warn    { param($msg) Write-Host "  [warn]  $msg" -ForegroundColor Yellow }
function Fail    { param($msg) Write-Host "  [fail]  $msg" -ForegroundColor Red; exit 1 }

$InstallDir = if ($env:NULLBOOK_DIR) { $env:NULLBOOK_DIR } else { "$HOME\nullbook" }
$RepoUrl = "https://github.com/jfornear/nullbook.git"

# ── Header ────────────────────────────────────────────
Write-Host ""
Write-Host "  nullbook Installer" -ForegroundColor White
Write-Host "  The AI agent for your personal finances." -ForegroundColor DarkGray
Write-Host ""

# ── Helpers ───────────────────────────────────────────
function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

$HasWinget = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)

function Install-WithWinget {
    param($Name, $WingetId, $ManualUrl)
    if ($HasWinget) {
        Info "Installing $Name via winget..."
        winget install --id $WingetId --accept-source-agreements --accept-package-agreements --silent 2>$null
        Refresh-Path
    } else {
        Fail "$Name not found. Install it from: $ManualUrl"
    }
}

# ── Check / Install Python ────────────────────────────
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    $pyVer = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    $pyMinor = [int]($pyVer.Split('.')[1])
    if ($pyMinor -ge 12) {
        Success "Python $pyVer"
    } else {
        Warn "Python 3.12+ required (found $pyVer)"
        Install-WithWinget "Python" "Python.Python.3.12" "https://www.python.org/downloads/"
        Success "Python installed"
    }
} else {
    Warn "Python not found"
    Install-WithWinget "Python" "Python.Python.3.12" "https://www.python.org/downloads/"
    Success "Python installed"
}

# ── Check / Install Node.js ───────────────────────────
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    $nodeVer = (& node -v).TrimStart('v')
    $nodeMajor = [int]($nodeVer.Split('.')[0])
    if ($nodeMajor -ge 18) {
        Success "Node.js $nodeVer"
    } else {
        Warn "Node.js 18+ required (found $nodeVer)"
        Install-WithWinget "Node.js" "OpenJS.NodeJS.LTS" "https://nodejs.org/"
        Success "Node.js installed"
    }
} else {
    Warn "Node.js not found"
    Install-WithWinget "Node.js" "OpenJS.NodeJS.LTS" "https://nodejs.org/"
    Success "Node.js installed"
}

# ── Check / Install Git ──────────────────────────────
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    $gitVer = (& git --version) -replace 'git version ', ''
    Success "Git $gitVer"
} else {
    Warn "Git not found"
    Install-WithWinget "Git" "Git.Git" "https://git-scm.com/download/win"
    Success "Git installed"
}

# ── Check Docker (for Redis) ─────────────────────────
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Success "Docker available (will use for Redis)"
} else {
    Warn "Docker not found. Install Docker Desktop for background task support."
    Warn "  https://docs.docker.com/desktop/install/windows-install/"
}

Write-Host ""

# ── Clone Repository ─────────────────────────────────
if (Test-Path "$InstallDir\.git") {
    Info "nullbook already cloned at $InstallDir"
    Set-Location $InstallDir
    Info "Pulling latest..."
    & git pull --quiet
    Success "Updated to latest version"
} else {
    Info "Cloning nullbook to $InstallDir..."
    & git clone --depth 1 $RepoUrl $InstallDir 2>$null
    Success "Cloned to $InstallDir"
    Set-Location $InstallDir
}

Write-Host ""

# ── Environment Setup ────────────────────────────────
$EnvFile = "$InstallDir\.env"
if (-not (Test-Path $EnvFile) -and (Test-Path "$InstallDir\.env.example")) {
    Copy-Item "$InstallDir\.env.example" $EnvFile
    Info "Created .env from template"
}

# ── Anthropic API Key ────────────────────────────────
Write-Host "  AI Setup" -ForegroundColor White
Write-Host "  nullbook uses Claude (Anthropic) for AI features." -ForegroundColor DarkGray
Write-Host ""

$existingKey = ""
if (Test-Path $EnvFile) {
    $envContent = Get-Content $EnvFile -ErrorAction SilentlyContinue
    $keyLine = $envContent | Where-Object { $_ -match "^ANTHROPIC_API_KEY=" }
    if ($keyLine) { $existingKey = ($keyLine -split "=", 2)[1] }
}

if ($existingKey -and $existingKey -ne "your-anthropic-api-key") {
    Success "Anthropic API key already configured"
} else {
    Write-Host "  Get an API key at: https://console.anthropic.com/settings/keys" -ForegroundColor Cyan
    Write-Host ""
    $apiKey = Read-Host "  Anthropic API key (or press Enter to skip)"
    if ($apiKey) {
        (Get-Content $EnvFile) -replace "^ANTHROPIC_API_KEY=.*", "ANTHROPIC_API_KEY=$apiKey" | Set-Content $EnvFile
        Success "Anthropic API key saved"
    } else {
        Warn "Skipped - add ANTHROPIC_API_KEY to .env before using chat"
    }
}

Write-Host ""

# ── Install Dependencies ─────────────────────────────
Write-Host "  Installing dependencies..." -ForegroundColor White
Write-Host ""

# Python venv
$VenvDir = "$InstallDir\backend\.venv"
if (-not (Test-Path $VenvDir)) {
    Info "Creating Python virtual environment..."
    & python -m venv $VenvDir
}

$Pip = "$VenvDir\Scripts\pip.exe"
$Py = "$VenvDir\Scripts\python.exe"

Info "Installing Python packages..."
& $Pip install --upgrade pip --quiet 2>$null
& $Pip install -r "$InstallDir\backend\requirements.txt" --quiet 2>$null
Success "Python packages installed"

Info "Installing Node packages..."
Set-Location "$InstallDir\frontend"
& npm install --silent 2>$null
Success "Node packages installed"

Write-Host ""

# ── Database Setup ───────────────────────────────────
Write-Host "  Setting up database..." -ForegroundColor White
Write-Host ""

Set-Location "$InstallDir\backend"

& $Py manage.py migrate --verbosity=0 2>$null
Success "Migrations complete"

& $Py manage.py seed_categories 2>$null | Out-Null
& $Py manage.py seed_institutions 2>$null | Out-Null
Success "Database seeded"

& $Py manage.py create_local_user 2>$null | Out-Null
Success "Account created"

# ── Done ─────────────────────────────────────────────
Write-Host ""
Write-Host "  ────────────────────────────────────────"
Write-Host ""
Write-Host "  nullbook is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "  Start it:" -ForegroundColor White
Write-Host "    cd $InstallDir"
Write-Host "    python backend\manage.py runserver 8001   # in one terminal"
Write-Host "    cd frontend && npm run dev                # in another terminal"
Write-Host ""
Write-Host "  Then open:" -ForegroundColor White
Write-Host "    http://localhost:5173"
Write-Host ""
Write-Host "  Edit $InstallDir\.env to configure" -ForegroundColor DarkGray
Write-Host "  Plaid, Gmail, and other integrations." -ForegroundColor DarkGray
Write-Host ""
