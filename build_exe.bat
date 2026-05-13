@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "LOG=%~dp0build_exe.log"
echo [%date% %time%] Building GPU Server Control exe > "%LOG%"

set "PYTHON_EXE="
if exist "%USERPROFILE%\miniconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        echo %%P | findstr /I "\\WindowsApps\\python.exe" >nul
        if errorlevel 1 if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
    )
)

if not defined PYTHON_EXE (
    echo Could not find a usable Python executable. >> "%LOG%"
    echo Could not find a usable Python executable.
    pause
    exit /b 1
)

echo Using Python: %PYTHON_EXE% >> "%LOG%"
"%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt" pyinstaller >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install build dependencies. See "%LOG%".
    pause
    exit /b 2
)

"%PYTHON_EXE%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name GPU_Server_Control ^
    --hidden-import bcrypt ^
    --hidden-import nacl ^
    --hidden-import cryptography ^
    "%~dp0gpu_server_tool.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller build failed. See "%LOG%".
    pause
    exit /b 3
)

if not exist "%~dp0dist" mkdir "%~dp0dist"
copy /Y "%~dp0servers.json" "%~dp0dist\servers.json" >> "%LOG%" 2>&1

echo.
echo Build complete:
echo   %~dp0dist\GPU_Server_Control.exe
echo   %~dp0dist\servers.json
echo.
pause
