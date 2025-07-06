@echo off
echo 🐍 Python 3.13 Compatible Installation Script
echo =============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

echo 🔄 Upgrading pip and build tools...
python -m pip install --upgrade pip setuptools wheel
echo.

echo 📦 Installing dependencies with Python 3.13 compatibility...
echo.

REM Try fallback requirements first
echo 🔄 Trying fallback requirements...
python -m pip install -r requirements_fallback.txt
if %errorlevel% equ 0 (
    echo ✅ Fallback installation successful!
    goto :success
)

echo ⚠️ Fallback failed, trying individual installation...
echo.

REM Install packages individually with binary wheels
echo 📦 Installing PyQt5...
python -m pip install --only-binary=all PyQt5

echo 📦 Installing Pillow...
python -m pip install --only-binary=all Pillow

echo 📦 Installing other packages...
python -m pip install pygetwindow PyAutoGUI requests

echo.
echo 🧪 Testing installation...
python -c "import PyQt5; import pygetwindow; import pyautogui; import requests; import PIL; print('✅ All packages imported successfully!')"

if %errorlevel% equ 0 (
    goto :success
) else (
    goto :failure
)

:success
echo.
echo 🎉 Installation completed successfully!
echo.
echo 📝 Next steps:
echo 1. Copy .env.example to .env
echo 2. Edit .env with your Azure API credentials
echo 3. Run: python main.py
echo.
goto :end

:failure
echo.
echo ❌ Installation failed. Please try:
echo 1. Install Anaconda/Miniconda
echo 2. Use Python 3.11 instead of 3.13
echo 3. Check TROUBLESHOOTING.md for detailed solutions
echo.

:end
pause