@echo off
echo ==========================================
echo  Meklo 1.3 -- Project Setup
echo ==========================================
echo.
cd /d "%~dp0"
python setup_meklo.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python failed. Trying python3...
    python3 setup_meklo.py
)
echo.
echo Press any key to exit...
pause >nul
