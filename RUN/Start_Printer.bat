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
    echo [WARNING] The Kitchen Printer requires an internet connection to receive orders.
    echo.
    choice /c YN /m "Do you want to ignore this warning and start the printer anyway?"
    if errorlevel 2 (
        echo Exiting...
        pause
        exit /b
    )
    echo [INFO] Continuing without verified internet connection...
) else (
    echo [SUCCESS] Internet connection is active.
)


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
