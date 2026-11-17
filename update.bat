@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo       UPDATING PROJECT JARVIS
echo ========================================================
echo.

where git >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Pulling latest repository updates...
    git pull
)

echo.
echo [*] Updating Python packages...
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\pip.exe install -r requirements.txt --upgrade
)

echo.
echo [*] Updating Frontend dependencies...
if exist "jarvis\frontend\package.json" (
    cd jarvis\frontend
    call npm update
    cd ..\..
)

echo.
echo [OK] Update process completed.
pause

