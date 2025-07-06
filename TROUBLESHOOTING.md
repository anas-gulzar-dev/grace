# 🔧 Troubleshooting Guide

## Python 3.13 Installation Issues

If you're encountering installation errors with Python 3.13, this guide will help you resolve them.

### Common Error: Pillow Build Failure

**Error Message:**
```
Getting requirements to build wheel did not run successfully.
KeyError: '__version__'
```

**Solutions:**

#### Option 1: Use Pre-compiled Wheels
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install packages individually with pre-compiled wheels
pip install --only-binary=all PyQt5
pip install --only-binary=all Pillow
pip install pygetwindow PyAutoGUI requests
```

#### Option 2: Use Conda (Recommended for Python 3.13)
```bash
# Install Anaconda or Miniconda first
# Then create a new environment
conda create -n biosensor python=3.11
conda activate biosensor

# Install packages via conda
conda install -c conda-forge pyqt pillow requests
pip install pygetwindow PyAutoGUI
```

#### Option 3: Downgrade Python Version
```bash
# Install Python 3.11 (more stable for this project)
# Download from: https://www.python.org/downloads/release/python-3118/
```

#### Option 4: Use Alternative Installation Script
```bash
# Try the fallback requirements
pip install -r requirements_fallback.txt

# Or run our enhanced setup script
python setup.py
```

### PyQt5 Installation Issues

**If PyQt5 fails to install:**

```bash
# Try alternative PyQt5 installation
pip install PyQt5 --config-settings --global-option=--verbose

# Or use PyQt6 (requires code modifications)
pip install PyQt6
```

### Windows-Specific Issues

#### Missing Visual C++ Build Tools
```bash
# Install Microsoft C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

#### Permission Issues
```bash
# Run as administrator or use --user flag
pip install --user -r requirements.txt
```

### Alternative Package Managers

#### Using Chocolatey
```bash
# Install Chocolatey first, then:
choco install python311
choco install vcredist2019
```

#### Using Scoop
```bash
# Install Scoop first, then:
scoop install python
scoop install vcredist2022
```

### Manual Installation Steps

If automated installation fails completely:

1. **Install core packages one by one:**
   ```bash
   pip install requests
   pip install Pillow --upgrade
   pip install PyQt5 --no-deps
   pip install pygetwindow
   pip install PyAutoGUI
   ```

2. **Verify installations:**
   ```bash
   python -c "import PyQt5; print('PyQt5 OK')"
   python -c "import pygetwindow; print('pygetwindow OK')"
   python -c "import pyautogui; print('PyAutoGUI OK')"
   python -c "import requests; print('requests OK')"
   python -c "import PIL; print('Pillow OK')"
   ```

### Environment Variables

Sometimes setting these environment variables helps:

```bash
# Windows Command Prompt
set PYTHONPATH=%PYTHONPATH%;C:\path\to\your\project
set QT_QPA_PLATFORM_PLUGIN_PATH=%CONDA_PREFIX%\Library\plugins\platforms

# PowerShell
$env:PYTHONPATH += ";C:\path\to\your\project"
$env:QT_QPA_PLATFORM_PLUGIN_PATH = "$env:CONDA_PREFIX\Library\plugins\platforms"
```

### Testing Your Installation

After installation, test with this minimal script:

```python
# test_installation.py
try:
    import sys
    print(f"Python version: {sys.version}")
    
    import PyQt5
    print("✅ PyQt5 imported successfully")
    
    import pygetwindow
    print("✅ pygetwindow imported successfully")
    
    import pyautogui
    print("✅ PyAutoGUI imported successfully")
    
    import requests
    print("✅ requests imported successfully")
    
    import PIL
    print("✅ Pillow imported successfully")
    
    print("\n🎉 All dependencies are working!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please check the troubleshooting guide.")
```

### Still Having Issues?

1. **Check your Python installation:**
   ```bash
   python --version
   pip --version
   ```

2. **Clear pip cache:**
   ```bash
   pip cache purge
   ```

3. **Update pip and setuptools:**
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   ```

4. **Try virtual environment:**
   ```bash
   python -m venv biosensor_env
   biosensor_env\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

5. **Check for conflicting packages:**
   ```bash
   pip list | findstr -i qt
   pip list | findstr -i pillow
   ```

### Contact Information

If none of these solutions work:
- Check the main README.md for basic troubleshooting
- Ensure you have the latest version of the project files
- Consider using Python 3.11 instead of 3.13 for better compatibility

---

**Remember:** Python 3.13 is very new, and some packages may not have full compatibility yet. Python 3.11 is recommended for the most stable experience.