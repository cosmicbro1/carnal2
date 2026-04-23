@echo off
cd /d "C:\Users\big e"

echo Checking git status...
git status --short
echo.

echo Staging all changes...
git add -A

echo.
echo Creating commit...
git commit -m "Add Meklo 1.3 fully local AI agent project" -m "Complete desktop + mobile AI agent with:" -m "- PyQt6 dark-themed GUI with 6 tabs (Chat, Audit, Image, Video, Orders, Books)" -m "- Flask REST backend (localhost:5000) with streaming SSE chat" -m "- Ollama/Gemma3 local LLM with custom Meklo 1.3 persona/system prompt" -m "- File audit engine: MD5 duplicate detection + PIL image corruption scanner" -m "- Stable Diffusion AUTOMATIC1111 text-to-image integration" -m "- CogVideoX-2b local text-to-video pipeline with background job queue" -m "- Printify API v1 order management with SMTP seller email notifications" -m "- Book writing tools: AI outline/chapter gen + PDF/EPUB export (ReportLab/ebooklib)" -m "- React Native mobile companion app (iOS + Android) with Chat/Image/Orders screens" -m "- settings.json config system with in-app Settings dialog" -m "- Setup script (setup_meklo.py) and launchers (RUN_SETUP.bat, LAUNCH_MEKLO.bat)" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

echo.
echo Commit result:
git log --oneline -1

echo.
git status --short

echo.
echo Done! Press any key to close.
pause >nul
