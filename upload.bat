@echo off
title JARVIS - 1-Click Automated YouTube Uploader
color 0a
cd /d "%~dp0"

echo ================================================================
echo          PROJECT JARVIS - 1-CLICK YOUTUBE SHORT UPLOADER
echo ================================================================
echo.
echo [*] Target Channel : GHOST _OF_FOOTBALL
echo [*] Video Selected : MrBeast Color Splash Masterpiece
echo [*] Clearing lockfiles...
del /f /q "jarvis\browser_profile\lockfile" 2>nul
del /f /q "jarvis\browser_profile\Singleton*" 2>nul
echo.
echo [*] Launching automated upload pipeline...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "jarvis\backend\social\uploader_cli.py" %*
) else (
    python "jarvis\backend\social\uploader_cli.py" %*
)

echo.
echo ================================================================
echo [*] Pipeline complete. Returning to JARVIS HUD...
echo ================================================================
echo.
pause

