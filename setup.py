#!/usr/bin/env python3
"""
Setup script for Biosensor Data Capture Tool
This script helps install dependencies and check the environment.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required.")
        print(f"   Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} is compatible")
        return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing Python dependencies...")
    
    # Check Python version for compatibility warnings
    if sys.version_info >= (3, 13):
        print("⚠️ Python 3.13+ detected. Some packages may need alternative installation.")
    
    # Try main requirements first
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install from requirements.txt: {e}")
        print("\n🔄 Trying fallback installation method...")
        
        # Try fallback requirements
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_fallback.txt"])
            print("✅ Fallback dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"❌ Fallback installation also failed: {e2}")
            print("\n🛠️ Trying individual package installation...")
            
            # Try installing packages individually
            packages = ['PyQt5', 'pygetwindow', 'PyAutoGUI', 'requests', 'Pillow']
            success_count = 0
            
            for package in packages:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    print(f"✅ {package} installed")
                    success_count += 1
                except subprocess.CalledProcessError:
                    print(f"❌ Failed to install {package}")
            
            if success_count >= 3:  # At least core packages installed
                print(f"✅ Installed {success_count}/{len(packages)} packages")
                return True
            else:
                print(f"❌ Only {success_count}/{len(packages)} packages installed")
                return False
                
    except FileNotFoundError:
        print("❌ requirements.txt file not found")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n🔍 Checking installed packages...")
    required_packages = [
        'PyQt5',
        'pygetwindow', 
        'pyautogui',
        'requests',
        'Pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = ['screenshots']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created/verified directory: {directory}")

def check_config():
    """Check configuration file"""
    print("\n⚙️ Checking configuration...")
    
    if not os.path.exists('config.py'):
        print("❌ config.py file not found")
        return False
    
    try:
        from config import AZURE_API_KEY, AZURE_ENDPOINT
        
        if AZURE_API_KEY == "AZURE_API_KEY":
            print("⚠️ Azure API key not configured in config.py")
            print("   Please update AZURE_API_KEY with your actual API key")
            return False
        
        if AZURE_ENDPOINT == "AZURE_ENDPOINT":
            print("⚠️ Azure endpoint not configured in config.py")
            print("   Please update AZURE_ENDPOINT with your actual endpoint")
            return False
        
        print("✅ Configuration file looks good")
        return True
        
    except ImportError as e:
        print(f"❌ Error importing config: {e}")
        return False

def check_scrcpy():
    """Check if scrcpy is available"""
    print("\n📱 Checking scrcpy...")
    try:
        result = subprocess.run(['scrcpy', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ scrcpy is installed and accessible")
            return True
        else:
            print("❌ scrcpy command failed")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ scrcpy not found in PATH")
        print("   Please install scrcpy from: https://github.com/Genymobile/scrcpy")
        return False

def main():
    """Main setup function"""
    print("🔬 Biosensor Data Capture Tool - Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️ Dependency installation failed. Checking what's already installed...")
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("   Try running: pip install -r requirements.txt")
    
    # Create directories
    create_directories()
    
    # Check configuration
    config_ok = check_config()
    
    # Check scrcpy
    scrcpy_ok = check_scrcpy()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Setup Summary:")
    print(f"   Python version: {'✅' if True else '❌'}")
    print(f"   Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"   Configuration: {'✅' if config_ok else '⚠️'}")
    print(f"   scrcpy: {'✅' if scrcpy_ok else '❌'}")
    
    if deps_ok and config_ok and scrcpy_ok:
        print("\n🎉 Setup complete! You can now run: python main.py")
    else:
        print("\n⚠️ Please fix the issues above before running the application.")
        
        if not config_ok:
            print("\n📝 Next steps for configuration:")
            print("   1. Get Azure Computer Vision API credentials")
            print("   2. Edit config.py and update AZURE_API_KEY and AZURE_ENDPOINT")
        
        if not scrcpy_ok:
            print("\n📱 Next steps for scrcpy:")
            print("   1. Download scrcpy from: https://github.com/Genymobile/scrcpy")
            print("   2. Add scrcpy to your system PATH")
            print("   3. Connect your Android device and run: scrcpy")

if __name__ == "__main__":
    main()