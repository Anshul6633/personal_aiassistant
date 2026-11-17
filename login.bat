@echo off
title JARVIS - YouTube Studio Sign-In Console
color 0b
cd /d "%~dp0"

echo ================================================================
echo          PROJECT JARVIS - YOUTUBE STUDIO AUTHENTICATION
echo ================================================================
echo.
echo [*] Clearing lockfiles...
del /f /q "jarvis\browser_profile\lockfile" 2>nul
del /f /q "jarvis\browser_profile\Singleton*" 2>nul

echo [*] Launching Native Google Chrome (Bypasses all Google bot detection)...
echo [*] Sign into your channel: GHOST _OF_FOOTBALL (khatrianshul977@gmail.com)
echo [*] Once you see YouTube Studio dashboard, close Chrome.
echo.
echo ================================================================

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="%~dp0jarvis\browser_profile" "https://studio.youtube.com"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --user-data-dir="%~dp0jarvis\browser_profile" "https://studio.youtube.com"
) else (
    echo [ERROR] Google Chrome was not found.
    pause
    exit /b 1
)

echo.
echo [*] Google Chrome launched! Complete sign-in in the Chrome window.
echo.
pause
