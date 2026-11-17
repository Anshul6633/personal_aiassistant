@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo       PROJECT JARVIS - ONE-CLICK INSTALLER & SETUP
echo ========================================================
echo.

echo [*] Step 1: Checking Python environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10+ is required but not found in PATH!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)
python --version

echo.
echo [*] Step 2: Setting up Python Virtual Environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
)
echo [OK] Virtual environment ready.

echo.
echo [*] Step 3: Installing Python Dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies!
    pause
    exit /b 1
)
echo [OK] Python dependencies installed successfully.

echo.
echo [*] Step 4: Installing Frontend Dependencies...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is required for the React Dashboard!
    pause
    exit /b 1
)
cd jarvis\frontend
call npm install
cd ..\..
echo [OK] Frontend dependencies installed.

echo.
echo [*] Step 5: Initializing Database & Seed Memories...
.venv\Scripts\python.exe -c "from jarvis.backend.database.db import init_database; init_database(); print('[OK] Database and memory tables initialized.')"

echo.
echo [*] Step 6: Verifying Ollama & Local AI Model...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo Checking for qwen2.5:1.5b model...
    ollama list | findstr "qwen2.5:1.5b" >nul 2>&1
    if %errorlevel% neq 0 (
        echo Pulling local AI model qwen2.5:1.5b...
        ollama pull qwen2.5:1.5b
    ) else (
        echo [OK] Model qwen2.5:1.5b is ready.
    )
) else (
    echo [WARN] Ollama is not installed or not in PATH. Please install from https://ollama.com/
)

echo.
echo ========================================================
echo       INSTALLATION COMPLETE!
echo       Launch JARVIS by running: start.bat
echo ========================================================
pause

