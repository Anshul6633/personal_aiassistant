@echo off
title JARVIS - YouTube Studio Native Sign-In
color 0b
cd /d "%~dp0"

echo ================================================================
echo          PROJECT JARVIS - ONE-TIME YOUTUBE STUDIO SIGN-IN
echo ================================================================
echo.
echo [*] Clearing lockfiles...
del /f /q "jarvis\browser_profile\lockfile" 2>nul
del /f /q "jarvis\browser_profile\Singleton*" 2>nul

echo [*] Launching Native Google Chrome (No Automation - 100%% Secure)...
echo [*] Sign into your channel: GHOST _OF_FOOTBALL
echo [*] Once you reach studio.youtube.com, close the browser window.
echo.
echo ================================================================

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="%~dp0jarvis\browser_profile" "https://studio.youtube.com"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --user-data-dir="%~dp0jarvis\browser_profile" "https://studio.youtube.com"
) else (
    echo [ERROR] Google Chrome was not found in Program Files.
    pause
    exit /b 1
)

echo.
echo [*] Google Chrome has been launched!
echo [*] Complete your sign-in, then close Chrome and return to JARVIS.
echo.
pause

