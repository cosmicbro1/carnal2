@echo off
REM ============================================================================
REM CARNAL 2.0 - ONE-BUTTON LAUNCH
REM ============================================================================
REM This is the EASY LAUNCHER - just double-click to start healing!
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"
color 0A
title CARNAL 2.0 - LAUNCHING YOUR AI HEALER

echo.
echo ============================================================================
echo  CARNAL 2.0 - LAUNCHING
echo ============================================================================
echo.

REM ============================================================================
REM Check if Ollama is running
REM ============================================================================
echo Checking Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if errorlevel 1 (
    echo.
    echo Starting Ollama server in background...
    echo (This may take a few seconds on first run)
    echo.
    start "" "ollama" serve
    timeout /t 5 /nobreak
    echo.
)

REM ============================================================================
REM Verify Ollama is responding
REM ============================================================================
echo Verifying Ollama is ready...
python -c "from openai import OpenAI; c = OpenAI(api_key='ollama', base_url='http://localhost:11434/v1'); c.chat.completions.create(model='gemma2', messages=[{'role': 'user', 'content': 'hi'}], max_tokens=1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Ollama is not responding!
    echo.
    echo SOLUTION:
    echo 1. Open Command Prompt
    echo 2. Type: ollama serve
    echo 3. Keep that window open
    echo 4. Then try this launcher again
    echo.
    pause
    exit /b 1
)

echo OK - Ollama ready!
echo.

REM ============================================================================
REM Start Carnal 2.0
REM ============================================================================
echo Launching Carnal 2.0...
echo.
echo Your healing companion is starting...
echo Please wait a moment...
echo.

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python carnal2.py

REM If we get here, the app closed
echo.
echo Carnal 2.0 closed.
echo Thank you for using your AI healing companion!
echo.
pause
