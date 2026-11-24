@echo off
setlocal
chcp 65001 >nul
pushd "%~dp0"
if errorlevel 1 exit /b 1
set "ANCLICKER_PYTHON=%~dp0.venv-build\Scripts\python.exe"
if not exist "%ANCLICKER_PYTHON%" (
    echo 未找到项目 Python 环境：.venv-build\Scripts\python.exe
    echo 请保留完整项目目录后再启动。
    popd
    pause
    exit /b 1
)
if not exist "%~dp0main.py" (
    echo 未找到 main.py，请将此文件放在 AnClicker 项目根目录。
    popd
    pause
    exit /b 1
)
"%ANCLICKER_PYTHON%" -B -X utf8 "%~dp0main.py" %*
set "ANCLICKER_EXIT_CODE=%ERRORLEVEL%"
popd
if not "%ANCLICKER_EXIT_CODE%"=="0" (
    echo.
    echo AnClicker 启动或运行失败，退出码：%ANCLICKER_EXIT_CODE%
    echo 请保留上方报错信息以便排查。
    pause
)
exit /b %ANCLICKER_EXIT_CODE%
