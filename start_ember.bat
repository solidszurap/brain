@echo off
rem Wake Ember up and open its window.
rem Press Ctrl+C (or close this window) to let it rest. It is saved every 2 minutes and on exit.
cd /d "%~dp0"
start "" cmd /c "timeout /t 4 >nul & start http://localhost:8765"
python ember.py %*
pause
