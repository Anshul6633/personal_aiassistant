@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo       PROJECT JARVIS - SYSTEM DIAGNOSTIC TOOL
echo ========================================================
echo.

echo [1/8] Checking Operating System and Hardware...
powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture"
powershell -Command "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors"

echo.
echo [2/8] Checking NVIDIA GPU and CUDA Acceleration...
where nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader
) else (
    echo [WARN] nvidia-smi not found. CUDA GPU offloading may be disabled.
)

echo.
echo [3/8] Checking Disk Storage Space...
powershell -Command "Get-PSDrive -PSProvider FileSystem | Select-Object Root, @{Name='Free_GB';Expression={[math]::Round($_.Free/1GB,2)}}, @{Name='Used_GB';Expression={[math]::Round($_.Used/1GB,2)}}"

echo.
echo [4/8] Checking Python Runtime...
where python >nul 2>&1
if %errorlevel% equ 0 (
    python --version
) else (
    echo [ERROR] Python is not installed in PATH!
)

echo.
echo [5/8] Checking Node.js and NPM...
where node >nul 2>&1
if %errorlevel% equ 0 (
    node -v
    npm -v
) else (
    echo [ERROR] Node.js is not installed in PATH!
)

echo.
echo [6/8] Checking Ollama Local AI Runtime...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama binary detected. Listing local models:
    ollama list
) else (
    echo [ERROR] Ollama is not installed or not in PATH!
)

echo.
echo [7/8] Checking FFmpeg Media Processor...
if exist "jarvis\assets\bin\ffmpeg.exe" (
    echo [OK] Standalone FFmpeg detected in jarvis\assets\bin.
    jarvis\assets\bin\ffmpeg.exe -version | findstr "version"
) else (
    where ffmpeg >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] FFmpeg found in PATH.
        ffmpeg -version | findstr "version"
    ) else (
        echo [WARN] FFmpeg not found.
    )
)

echo.
echo [8/8] Testing Python Environment and Imports...
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "import fastapi, uvicorn, psutil, mss, pyautogui, edge_tts, faster_whisper, ollama; print('[SUCCESS] All key Python modules loaded successfully!')"
) else (
    echo [WARN] Virtual environment .venv not yet created. Run install.bat.
)

echo.
echo ========================================================
echo       DIAGNOSTIC COMPLETE.
echo ========================================================
