@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-build\Scripts\python.exe" (
  echo Python environment missing. Run the development setup first.
  pause
  exit /b 1
)
".venv-build\Scripts\python.exe" -m models.tool_api %*
if errorlevel 1 pause
