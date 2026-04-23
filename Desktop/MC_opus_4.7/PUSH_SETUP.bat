@echo off
cd /d "C:\Users\big e"

echo ==========================================
echo  Pushing setup_meklo.py to GitHub
echo ==========================================
echo.

git add Desktop/MC_opus_4.7/setup_meklo.py

echo Committing...
git commit -m "Add Meklo 1.3 setup script (full project generator)" -m "setup_meklo.py writes all 24+ project files when executed." -m "Run: python setup_meklo.py (or double-click RUN_SETUP.bat)" -m "" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo Done! Press any key to close.
pause >nul
