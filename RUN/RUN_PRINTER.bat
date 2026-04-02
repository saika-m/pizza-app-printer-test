@echo off
setlocal enabledelayedexpansion

REM Change to the root directory of the application
cd /d "%~dp0"
cd ..

echo ========================================================
echo     Kitchen Printer Application Bootstrapper
echo ========================================================

REM 1. Check if Python is installed and accessible
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Python is not installed or not in PATH.
    echo [INFO] Downloading Python 3.11 Installer...
    
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe' -OutFile 'python-installer.exe'"
    
    if exist "python-installer.exe" (
        echo [INFO] Installing Python silently for the current user...
        echo [INFO] This might take a minute, please wait...
        start /wait python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1
        del python-installer.exe
        
        echo [SUCCESS] Python successfully installed.
        echo [IMPORTANT] Please close this window and double-click RUN_PRINTER.bat again!
        pause
        exit /b
    ) else (
        echo [ERROR] Failed to download Python. Please install manually from python.org
        pause
        exit /b
    )
)

echo [INFO] Python is installed.

REM 2. Check for virtual environment and its validity
set "VENV_EXISTS=0"
if exist "venv\Scripts\activate.bat" (
    set "VENV_EXISTS=1"
)

if "%VENV_EXISTS%" == "0" (
    echo [INFO] Virtual environment 'venv' not found or incomplete.
    echo [INFO] Creating a new virtual environment...
    
    REM If venv folder exists but is broken or empty, remove it
    if exist "venv" (
        rmdir /s /q "venv"
    )

    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment. Let's try specifying absolute path...
        REM Fallback if simple command fails
        for /f "delims=" %%i in ('where python') do set "PY_PATH=%%i"
        "!PY_PATH!" -m venv venv
        if !ERRORLEVEL! NEQ 0 (
             echo [ERROR] Failed to create virtual environment again. Please check your Python installation.
             pause
             exit /b
        )
    )
    echo [SUCCESS] Virtual environment created successfully.
)

REM 3. Activate Virtual Environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM 4. Install or Update Requirements
echo [INFO] Checking for required packages...
python -m pip install --upgrade pip >nul 2>&1
if exist "requirements.txt" (
    pip install -r requirements.txt >nul 2>&1
    echo [SUCCESS] Dependencies are ready.
) else (
    echo [WARNING] requirements.txt not found.
)

REM 5. Run the Application
echo.
echo ========================================================
echo Starting Kitchen Printer...
echo Logging to: kitchen_printer.log
echo ========================================================
echo.

python kitchen_printer.py

REM 6. Pause if it closes/crashes
echo.
echo ========================================================
echo Printer script stopped.
echo ========================================================
pause
