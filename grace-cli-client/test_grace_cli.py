#!/usr/bin/env python3
"""
Test script for Grace CLI application
Basic functionality tests to ensure the CLI works correctly
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import rich
        print("  [+] Rich library imported successfully")
    except ImportError:
        print("  [-] Rich library not found - run: pip install rich")
        return False
    
    try:
        import click
        print("  [+] Click library imported successfully")
    except ImportError:
        print("  [-] Click library not found - run: pip install click")
        return False
    
    try:
        import requests
        print("  [+] Requests library imported successfully")
    except ImportError:
        print("  [-] Requests library not found - run: pip install requests")
        return False
    
    try:
        import mss
        print("  [+] MSS library imported successfully")
    except ImportError:
        print("  [-] MSS library not found - run: pip install mss")
        return False
    
    try:
        import PyWinCtl
        print("  [+] PyWinCtl library imported successfully")
    except ImportError:
        print("  [-] PyWinCtl library not found - run: pip install PyWinCtl")
        return False
    
    return True

def test_config_creation():
    """Test if configuration system works"""
    print("\nTesting configuration system...")
    
    try:
        from config import ConfigManager
        
        # Create a temporary config for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            config_manager = ConfigManager(config_path)
            
            # Test saving and loading
            config_manager.config.azure.endpoint = "https://test.cognitiveservices.azure.com/"
            config_manager.config.azure.api_key = "test_key"
            config_manager.save_config(config_manager.config)
            
            # Load and verify
            new_config = ConfigManager(config_path)
            if new_config.config.azure.endpoint == "https://test.cognitiveservices.azure.com/":
                print("  [+] Configuration save/load works correctly")
                return True
            else:
                print("  [-] Configuration save/load failed")
                return False
                
    except Exception as e:
        print(f"  [-] Configuration test failed: {e}")
        return False

def test_cli_help():
    """Test if CLI help command works"""
    print("\nTesting CLI help command...")
    
    try:
        result = subprocess.run(
            [sys.executable, "grace_cli.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "Grace Biosensor Data Capture" in result.stdout:
            print("  [+] CLI help command works correctly")
            return True
        else:
            print(f"  [-] CLI help command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  [-] CLI help test failed: {e}")
        return False

def test_version_command():
    """Test if version command works"""
    print("\nTesting version command...")
    
    try:
        result = subprocess.run(
            [sys.executable, "grace_cli.py", "version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "Grace CLI" in result.stdout:
            print("  [+] Version command works correctly")
            return True
        else:
            print(f"  [-] Version command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  [-] Version test failed: {e}")
        return False

def test_status_command():
    """Test if status command works"""
    print("\nTesting status command...")
    
    try:
        result = subprocess.run(
            [sys.executable, "grace_cli.py", "status"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            print("  [+] Status command works correctly")
            return True
        else:
            print(f"  [-] Status command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  [-] Status test failed: {e}")
        return False

def test_list_windows_command():
    """Test if list-windows command works"""
    print("\nTesting list-windows command...")
    
    try:
        result = subprocess.run(
            [sys.executable, "grace_cli.py", "list-windows", "--no-categories"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            print("  [+] List-windows command works correctly")
            return True
        else:
            print(f"  [-] List-windows command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  [-] List-windows test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Grace CLI Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_creation,
        test_cli_help,
        test_version_command,
        test_status_command,
        test_list_windows_command
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Grace CLI is ready to use.")
        print("\nQuick start:")
        print("   python grace_cli.py interactive")
        print("   python grace_cli.py list-windows")
        print("   python grace_cli.py --help")
        return True
    else:
        print(f"{total - passed} tests failed. Please check the issues above.")
        print("\nCommon fixes:")
        print("   pip install -r requirements.txt")
        print("   Check Python version (3.8+ required)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)