@echo off
REM Change to the directory of this script
cd /d "%~dp0"

echo Starting Kitchen Printer...
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found in 'venv' folder.
    echo Please run the installation steps in README.md first.
    pause
    exit /b
)

REM Activate venv and run
call venv\Scripts\activate.bat
python kitchen_printer.py

REM Pause so the window doesn't close immediately if the script crashes
echo.
echo Printer script stopped.
pause
