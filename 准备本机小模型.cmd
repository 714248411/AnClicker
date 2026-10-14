@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tools\prepare_agent_models.py --gpu %*
) else if exist ".build-python\python.exe" (
  ".build-python\python.exe" tools\prepare_agent_models.py --gpu %*
) else (
  py -3 tools\prepare_agent_models.py --gpu %*
)
if errorlevel 1 (
  echo Preparation failed. Check the error above.
  pause
  exit /b 1
)
echo Ready. Open AnClicker - Conversation Agent to start.
pause
