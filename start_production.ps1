# JARVIS Autonomous AI Assistant - Production Launcher
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "            J.A.R.V.I.S. AUTONOMOUS PRODUCTION DEPLOYMENT" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Check Python virtual environment
$VenvPython = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found at $VenvPython. Run python -m venv .venv"
    exit 1
}

# 2. Check frontend compilation
$DistIndex = "jarvis\frontend\dist\index.html"
if (-not (Test-Path $DistIndex)) {
    Write-Host "[BUILD] Compiling production React SPA bundle..." -ForegroundColor Yellow
    Push-Location "jarvis\frontend"
    npm run build
    Pop-Location
}

# 3. Detect LAN IP
$LanIp = "127.0.0.1"
try {
    $LanIp = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*", "Ethernet*" | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
} catch {
    $LanIp = "127.0.0.1"
}

Write-Host ""
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkCyan
Write-Host " DEPLOYMENT CHANNELS READY:" -ForegroundColor Green
Write-Host "   [*] Local Desktop Workstation : http://localhost:8000" -ForegroundColor White
Write-Host "   [*] Local Wi-Fi Mobile Phone  : http://${LanIp}:8000" -ForegroundColor White
Write-Host "   [*] Phone Remote Hub          : http://${LanIp}:8000/mobile" -ForegroundColor Yellow
Write-Host "   [*] Worldwide Public Access   : Activate with 1-click in the UI!" -ForegroundColor Magenta
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkCyan
Write-Host "[INFO] Starting Uvicorn on 0.0.0.0:8000..." -ForegroundColor Cyan
Write-Host ""

& $VenvPython -m uvicorn jarvis.backend.main:app --host 0.0.0.0 --port 8000

