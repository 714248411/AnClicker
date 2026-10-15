@echo off
setlocal
cd /d "%~dp0"
if exist ".venv-build\Scripts\python.exe" (
  set "app_python=.venv-build\Scripts\python.exe"
  goto run
)
if not exist ".venv\Scripts\python.exe" goto missing_python
".venv\Scripts\python.exe" -c "import sys; assert sys.version_info[:2] == (3, 10); import PySide2" >nul 2>&1
if errorlevel 1 goto missing_python
set "app_python=.venv\Scripts\python.exe"
:run
"%app_python%" main.py %*
set "launch_exit=%errorlevel%"
if not "%launch_exit%"=="0" pause
exit /b %launch_exit%
:missing_python
echo A Python 3.10 / PySide2 environment is required.
echo Run tools\prepare_build.py to prepare .venv-build. Existing .venv is preserved.
pause
exit /b 1
