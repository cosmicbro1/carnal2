@echo off
REM ============================================================================
REM CARNAL 2.0 - FLAWLESS ONE-CLICK SETUP FOR BROKE STUDENTS
REM ============================================================================
REM This script handles everything needed to get Carnal 2.0 running:
REM - Checks if Ollama is installed (and guides installation if not)
REM - Downloads Gemma 2 model
REM - Installs Python dependencies
REM - Verifies everything works
REM - Creates shortcut for easy launching
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"
color 0A
title CARNAL 2.0 - FLAWLESS SETUP (STUDENT EDITION)

echo.
echo ============================================================================
echo  CARNAL 2.0 - FLAWLESS ONE-CLICK SETUP
echo  For broke students (like you!) - Zero cost, infinite healing
echo ============================================================================
echo.

REM ============================================================================
REM STEP 1: Check if Python is installed
REM ============================================================================
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found!
    echo.
    echo SOLUTION: Download Python from https://www.python.org/downloads/
    echo - Click "Download Python 3.11" (or latest)
    echo - Run the installer
    echo - IMPORTANT: Check "Add Python to PATH" during install
    echo - Then run this setup script again
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo OK: Found %PYTHON_VERSION%
echo.

REM ============================================================================
REM STEP 2: Check if Ollama is installed
REM ============================================================================
echo [2/5] Checking Ollama installation...
where ollama >nul 2>&1
if errorlevel 1 (
    echo.
    echo OLLAMA NOT FOUND - This is needed for FREE local AI!
    echo.
    echo SOLUTION:
    echo 1. Download Ollama: https://ollama.ai
    echo 2. Run the installer and follow the prompts
    echo 3. After installation, run this setup script again
    echo.
    echo Why Ollama? It's FREE, LOCAL, and OPEN SOURCE - perfect for broke students!
    echo.
    pause
    exit /b 1
)
echo OK: Ollama found
echo.

REM ============================================================================
REM STEP 3: Download Gemma 2 model (the AI that powers healing)
REM ============================================================================
echo [3/5] Downloading Gemma 2 model (one-time, ~4GB)...
echo This may take 5-15 minutes depending on your internet
echo.
ollama pull gemma2
if errorlevel 1 (
    echo.
    echo ERROR: Failed to download Gemma 2
    echo SOLUTION: Make sure Ollama is running. Run: ollama serve
    echo.
    pause
    exit /b 1
)
echo.
echo OK: Gemma 2 model ready!
echo.

REM ============================================================================
REM STEP 4: Install Python dependencies
REM ============================================================================
echo [4/5] Installing Python dependencies...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q --upgrade pip
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Try running: pip install -r requirements.txt
    pause
    exit /b 1
)
echo OK: All Python packages installed!
echo.

REM ============================================================================
REM STEP 5: Verify everything works
REM ============================================================================
echo [5/5] Verifying Ollama connection...
REM Start Ollama server in background if not already running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if errorlevel 1 (
    echo Starting Ollama server in background...
    start "" "ollama" serve
    timeout /t 3 /nobreak
)

REM Test Ollama connection
python -c "from openai import OpenAI; c = OpenAI(api_key='ollama', base_url='http://localhost:11434/v1'); c.chat.completions.create(model='gemma2', messages=[{'role': 'user', 'content': 'hi'}], max_tokens=1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Ollama is not responding
    echo SOLUTION: Make sure Ollama is running
    echo - Open Command Prompt
    echo - Type: ollama serve
    echo - Keep that window open
    echo - Then try this setup again
    echo.
    pause
    exit /b 1
)
echo OK: Ollama is working perfectly!
echo.

REM ============================================================================
REM SETUP COMPLETE!
REM ============================================================================
echo.
echo ============================================================================
echo  SETUP COMPLETE! YOU'RE ALL SET!
echo ============================================================================
echo.
echo Your Carnal 2.0 is now ready to heal!
echo.
echo TO START CARNAL 2.0:
echo ==================
echo 1. Open the "FLAWLESS_RUN.bat" file in this folder
echo 2. Double-click it
echo 3. That's it!
echo.
echo Or keep reading for manual startup...
echo.
echo MANUAL STARTUP (if you prefer):
echo ================================
echo Terminal 1: ollama serve
echo   (This starts the AI engine - keep this running)
echo.
echo Terminal 2: python carnal2.py
echo   (This starts Carnal 2.0)
echo.
echo WHY THIS WORKS FOR BROKE STUDENTS:
echo ===================================
echo - Ollama: FREE (runs on your computer)
echo - Gemma 2: FREE (open source AI model)
echo - Python: FREE (programming language)
echo - Carnal 2.0: FREE (this app)
echo - Your data: YOURS (stays on your computer, no servers)
echo.
echo Total cost: $0.00/year FOREVER
echo.
echo More info: See OPENSOURCE_STUDENT_SETUP.md
echo.
pause
