@echo off
TITLE JARVIS Autonomous AI Assistant - Production Server
COLOR 0B

echo ======================================================================
echo             J.A.R.V.I.S. AUTONOMOUS PRODUCTION DEPLOYMENT
echo ======================================================================
echo [INFO] Initializing production workstation deployment...

:: Check if Python virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found in .venv!
    echo [INFO] Please create one using: python -m venv .venv
    pause
    exit /b 1
)

:: Build frontend if dist folder is absent
if not exist "jarvis\frontend\dist\index.html" (
    echo [BUILD] Production frontend build not detected. Compiling React bundle...
    cd jarvis\frontend
    call npm run build
    cd ..\..
    echo [BUILD] Frontend successfully compiled!
)

:: Check host LAN IP address
for /f "tokens=4" %%a in ('route print ^| findstr 0.0.0.0.*0.0.0.0 ^| findstr /v "127.0.0.1"') do (
    set HOST_IP=%%a
    goto :ip_found
)
:ip_found
if "%HOST_IP%"=="" set HOST_IP=127.0.0.1

echo.
echo ----------------------------------------------------------------------
echo  DEPLOYMENT CHANNELS READY:
echo    [*] Local Desktop Workstation : http://localhost:8000
echo    [*] Local Wi-Fi Mobile Phone  : http://%HOST_IP%:8000
echo    [*] Phone Remote UI           : http://%HOST_IP%:8000/mobile
echo    [*] Worldwide Live HTTPS      : Start with 1-click in the UI header!
echo ----------------------------------------------------------------------
echo [INFO] Launching high-performance Uvicorn production server on 0.0.0.0:8000...
echo.

.\.venv\Scripts\python.exe -m uvicorn jarvis.backend.main:app --host 0.0.0.0 --port 8000
pause

