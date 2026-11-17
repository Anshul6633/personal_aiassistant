@echo off
title JARVIS - Direct Upload Using Your Logged-In Chrome
color 0a
cd /d "%~dp0"

echo ================================================================
echo    JARVIS - DIRECT UPLOAD USING YOUR ALREADY-LOGGED-IN CHROME
echo ================================================================
echo.
echo [*] Closing existing Chrome to enable instant automation bridge...
echo [*] (Your tabs will restore automatically!)
echo.
taskkill /F /IM chrome.exe 2>nul
timeout /t 2 /nobreak >nul

echo [*] Starting Google Chrome with JARVIS automation bridge...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --restore-last-session
timeout /t 3 /nobreak >nul

echo [*] Connecting Playwright directly to GHOST _OF_FOOTBALL channel...
echo [*] Uploading Short: clip_8207c7fa-4f9_mrbeast.mp4...
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "jarvis\backend\social\cdp_uploader.py"
) else (
    python "jarvis\backend\social\cdp_uploader.py"
)

echo.
echo ================================================================
echo [*] Done!
echo ================================================================
echo.
pause

