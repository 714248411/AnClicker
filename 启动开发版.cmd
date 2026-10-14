@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" --version >nul 2>&1
if not errorlevel 1 goto run
if not exist ".build-python\python.exe" goto missing_python
echo Repairing the local Python environment...
".build-python\python.exe" -m venv --without-pip .venv
if errorlevel 1 goto repair_failed
:run
".venv\Scripts\python.exe" main.py %*
set "launch_exit=%errorlevel%"
if not "%launch_exit%"=="0" pause
exit /b %launch_exit%
:missing_python
echo Python is missing or the development environment is no longer valid.
echo Install Python 3.10 and recreate .venv with requirements.txt.
pause
exit /b 1
:repair_failed
echo Unable to repair the local Python environment. See the error above.
pause
exit /b 1
