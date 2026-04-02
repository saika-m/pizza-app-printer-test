@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
cd ..

echo ========================================================
echo     Kitchen Printer Updater ^& Builder
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

REM 4. Install requirements and PyInstaller
echo [INFO] Installing dependencies and PyInstaller...
python -m pip install --upgrade pip >nul 2>&1
if exist "requirements.txt" (
    pip install -r requirements.txt >nul 2>&1
)
pip install pyinstaller >nul 2>&1

echo.
echo ========================================================
echo     Building Standalone Binary...
echo ========================================================

pyinstaller --onefile --name "KitchenPrinter" --hidden-import="zeroconf" --icon=NONE kitchen_printer.py

if %ERRORLEVEL% EQU 0 (
    REM Move binary to RUN folder and clean up PyInstaller folders
    move /y "dist\KitchenPrinter.exe" "RUN\KitchenPrinter.exe" >nul
    rmdir /s /q build
    rmdir /s /q dist
    if exist "KitchenPrinter.spec" del "KitchenPrinter.spec"

    echo.
    echo ========================================================
    echo [SUCCESS] Update and Build Complete!
    echo You can now just double-click 'KitchenPrinter.exe'
    echo located inside this RUN folder!
    echo ========================================================
) else (
    echo.
    echo [ERROR] Build failed during PyInstaller execution.
)

pause

