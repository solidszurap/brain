@echo off
rem Open Ember's window. Close this window (or press Ctrl+C) to close Ember; it is saved as it goes.
cd /d "%~dp0"
start "" cmd /c "timeout /t 3 >nul & start http://localhost:8765"
python ember.py %*
pause
