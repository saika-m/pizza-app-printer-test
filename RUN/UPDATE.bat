@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
cd ..

echo ========================================================
echo     Kitchen Printer Updater
echo ========================================================
echo Pulling latest updates from GitHub...
git pull

echo.
echo ========================================================
echo     Checking Environment...
echo ========================================================

REM 1. Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Python is not installed. Downloading Python 3.11 Installer...
    
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe' -OutFile 'python-installer.exe'"
    
    if exist "python-installer.exe" (
        echo [INFO] Installing Python silently for the current user...
        start /wait python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1
        del python-installer.exe
        
        echo [SUCCESS] Python successfully installed.
        echo [IMPORTANT] Please close this window and double-click UPDATE.bat again!
        pause
        exit /b
    ) else (
        echo [ERROR] Failed to download Python. Please install manually from python.org
        pause
        exit /b
    )
)

REM 2. Ensure virtual environment exists
set "VENV_EXISTS=0"
if exist "venv\Scripts\activate.bat" (
    set "VENV_EXISTS=1"
)

if "%VENV_EXISTS%" == "0" (
    echo [INFO] Creating virtual environment...
    if exist "venv" rmdir /s /q "venv"
    python -m venv venv
)

REM 3. Activate Virtual Environment
call venv\Scripts\activate.bat

REM 4. Install requirements
echo [INFO] Installing dependencies...
python -m pip install --upgrade pip
if exist "requirements.txt" (
    pip install -r requirements.txt
)

echo.
echo ========================================================
echo [SUCCESS] Update and Installation Complete!
echo You can now run the printer by clicking Start_Printer.bat
echo ========================================================
pause

