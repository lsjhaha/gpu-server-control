@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "LOG=%~dp0startup.log"
echo [%date% %time%] Starting GPU Server Control > "%LOG%"

set "PYTHON_EXE="

rem 1) Portable Python next to this bat, if you later copy one here.
if exist "%~dp0python\python.exe" set "PYTHON_EXE=%~dp0python\python.exe"

rem 2) Common user-level conda/python locations.
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYTHON_EXE if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

rem 3) Python launcher, if installed.
if not defined PYTHON_EXE (
    py -3 -c "import sys; print(sys.executable)" > "%TEMP%\gpu_tool_python.txt" 2>> "%LOG%"
    if %ERRORLEVEL% EQU 0 (
        set /p PYTHON_EXE=<"%TEMP%\gpu_tool_python.txt"
    )
)

rem 4) PATH python, but reject Microsoft Store aliases.
if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        echo %%P | findstr /I "\\WindowsApps\\python.exe" >nul
        if errorlevel 1 if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
    )
)

if not defined PYTHON_EXE (
    echo Could not find a usable Python executable. >> "%LOG%"
    echo Could not find a usable Python executable.
    echo.
    echo Please install Miniconda/Python, or put portable Python at:
    echo   %~dp0python\python.exe
    echo.
    echo Details written to:
    echo   %LOG%
    pause
    exit /b 1
)

echo Using Python: %PYTHON_EXE% >> "%LOG%"
echo Using Python: %PYTHON_EXE%

"%PYTHON_EXE%" -c "import tkinter; import sys; print('Python OK', sys.version); print('Tk OK')" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python exists but Tkinter is not available.
    echo Details written to:
    echo   %LOG%
    pause
    exit /b 2
)

"%PYTHON_EXE%" -m pip --version >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python exists but pip is not available.
    echo Details written to:
    echo   %LOG%
    pause
    exit /b 3
)

if exist "%~dp0requirements.txt" (
    echo Installing/updating Python dependencies from requirements.txt
    echo Installing/updating dependencies from requirements.txt >> "%LOG%"
    "%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt" >> "%LOG%" 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Python dependencies.
        echo Details written to:
        echo   %LOG%
        pause
        exit /b 4
    )
)

echo Launching app... >> "%LOG%"
"%PYTHON_EXE%" "%~dp0gpu_server_tool.py" >> "%LOG%" 2>&1
set "EXITCODE=%ERRORLEVEL%"
echo App exited with code %EXITCODE% >> "%LOG%"

if not "%EXITCODE%"=="0" (
    echo App failed to start or exited with an error.
    echo Details written to:
    echo   %LOG%
    pause
)

exit /b %EXITCODE%
