@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo       SHUTTING DOWN PROJECT JARVIS
echo ========================================================
echo.

echo [*] Terminating FastAPI backend on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [*] Terminating Vite frontend on port 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [OK] All JARVIS services have been stopped.
echo.

