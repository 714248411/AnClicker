@echo off
setlocal
cd /d "%~dp0"
if exist ".venv-build\Scripts\python.exe" (
  ".venv-build\Scripts\python.exe" tools\setup_crawl4ai_runtime.py
) else (
  py -3 tools\setup_crawl4ai_runtime.py
)
set "setup_exit=%errorlevel%"
pause
exit /b %setup_exit%
