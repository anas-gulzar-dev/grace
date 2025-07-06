@echo off
echo 🔬 Biosensor Data Capture Tool - Windows Setup
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Run setup script
echo 🚀 Running setup script...
python setup.py

echo.
echo 📝 Setup completed. Check the output above for any issues.
echo.
echo To run the application, use: python main.py
echo Or double-click run_app.bat
echo.
pause