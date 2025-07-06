@echo off
echo 🔬 Starting Biosensor Data Capture Tool...
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo ❌ main.py not found in current directory
    echo Please make sure you're running this from the project folder
    pause
    exit /b 1
)

REM Run the application
echo 🚀 Launching application...
echo.
python main.py

REM If the application exits, show a message
echo.
echo 📝 Application closed.
echo.
pause