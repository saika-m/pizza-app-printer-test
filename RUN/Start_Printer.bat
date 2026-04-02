@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
cd ..

echo ========================================================
echo     Starting Kitchen Printer...
echo ========================================================

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
