@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
cd ..

echo ========================================================
echo     Starting Kitchen Printer...
echo ========================================================

REM 0. Check Internet Connectivity
echo [INFO] Testing internet connection...
curl -I -s -m 3 "http://www.msftconnecttest.com/connecttest.txt" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No Internet Connection detected!
    echo [ACTION] Please check your Wi-Fi or Ethernet cable before continuing.
    pause
    exit /b
)
echo [SUCCESS] Internet connection is active.


REM 1. Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo [ACTION REQUIRED] Please double-click UPDATE.bat first to install the printer dependencies.
    pause
    exit /b
)

REM 2. Activate Virtual Environment
call venv\Scripts\activate.bat

REM 3. Run the Python Script natively
python kitchen_printer.py

echo.
echo ========================================================
echo Printer script stopped or crashed.
echo See the output above for any errors.
echo ========================================================
pause
