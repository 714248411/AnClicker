@echo off
setlocal
cd /d "%~dp0"
if exist ".venv-build\Scripts\python.exe" (
  ".venv-build\Scripts\python.exe" tools\prepare_agent_models.py --gpu %*
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tools\prepare_agent_models.py --gpu %*
) else if exist ".local/toolchains/python-3.10.11\python.exe" (
  ".local/toolchains/python-3.10.11\python.exe" tools\prepare_agent_models.py --gpu %*
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
