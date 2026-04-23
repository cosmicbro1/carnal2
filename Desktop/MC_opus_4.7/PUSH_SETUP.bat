@echo off
cd /d "C:\Users\big e"

echo ==========================================
echo  Pushing setup_meklo.py to GitHub
echo ==========================================
echo.

git add Desktop/MC_opus_4.7/setup_meklo.py Desktop/MC_opus_4.7/PUSH_SETUP.bat

echo Committing...
git commit -m "Fix Meklo 1.3 setup bugs (4 issues resolved)" -m "- Fix LAUNCH_MEKLO.bat: wrong cd path %%~dp0meklo -> %%~dp0" -m "- Fix PyQt6 enum: QTableWidget.EditTrigger -> QAbstractItemView.EditTrigger" -m "- Fix update_settings: now updates video_gen + book_tools config" -m "- Fix requirements.txt: add missing imageio dependency" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo Done! Press any key to close.
pause >nul
