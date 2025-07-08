#!/usr/bin/env python3
"""
Grace CLI Demonstration Script
Showcases all the features and capabilities of the Grace CLI application
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and display its output"""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def demo_basic_commands():
    """Demonstrate basic CLI commands"""
    print("\n" + "#"*80)
    print("# GRACE CLI - BASIC COMMANDS DEMONSTRATION")
    print("#"*80)
    
    commands = [
        ("python grace_cli.py --help", "Show help and available commands"),
        ("python grace_cli.py version", "Display version information"),
        ("python grace_cli.py status", "Show system status and capabilities"),
        ("python grace_cli.py list-windows --no-categories", "List all available windows (simple format)"),
        ("python grace_cli.py list-windows", "List all available windows (with categories)"),
    ]
    
    for cmd, desc in commands:
        success = run_command(cmd, desc)
        if not success:
            print(f"Warning: Command failed: {cmd}")
        time.sleep(1)

def demo_configuration():
    """Demonstrate configuration management"""
    print("\n" + "#"*80)
    print("# GRACE CLI - CONFIGURATION DEMONSTRATION")
    print("#"*80)
    
    print("\nConfiguration Features:")
    print("- Azure Computer Vision OCR settings")
    print("- Screenshot capture preferences")
    print("- Export format options")
    print("- UI customization")
    print("- Persistent settings storage")
    
    # Show current config status
    run_command("python grace_cli.py status", "Current configuration status")
    
    print("\nTo configure Azure OCR:")
    print("  python grace_cli.py configure --endpoint 'YOUR_ENDPOINT' --key 'YOUR_KEY'")
    print("\nOr use interactive configuration:")
    print("  python grace_cli.py configure")

def demo_capture_features():
    """Demonstrate capture capabilities"""
    print("\n" + "#"*80)
    print("# GRACE CLI - CAPTURE FEATURES DEMONSTRATION")
    print("#"*80)
    
    print("\nCapture Features:")
    print("- Cross-platform window detection")
    print("- Multiple screenshot methods (DXcam, MSS, PyAutoGUI)")
    print("- Smart device categorization")
    print("- Manual and automatic capture modes")
    print("- Real-time OCR processing")
    print("- Multiple export formats (CSV, JSON)")
    
    print("\nExample capture commands:")
    print("  # Interactive window selection")
    print("  python grace_cli.py capture")
    print("")
    print("  # Capture specific window")
    print("  python grace_cli.py capture --window 'Calculator'")
    print("")
    print("  # Capture with export")
    print("  python grace_cli.py capture --window 'Calculator' --csv --json")
    print("")
    print("  # Auto-capture mode")
    print("  python grace_cli.py auto-capture --window 'Calculator' --interval 5")

def demo_interactive_mode():
    """Demonstrate interactive mode"""
    print("\n" + "#"*80)
    print("# GRACE CLI - INTERACTIVE MODE DEMONSTRATION")
    print("#"*80)
    
    print("\nInteractive Mode Features:")
    print("- Beautiful menu-driven interface")
    print("- Real-time window listing")
    print("- Live system status monitoring")
    print("- Interactive configuration")
    print("- Progress bars and visual feedback")
    print("- Keyboard shortcuts")
    
    print("\nTo start interactive mode:")
    print("  python grace_cli.py interactive")
    
    print("\nInteractive mode provides:")
    print("  1. List Windows - Browse available windows")
    print("  2. Select Window - Choose target for capture")
    print("  3. Capture Now - Take immediate screenshot")
    print("  4. Auto Capture - Start automated capture")
    print("  5. Export Results - Save data in various formats")
    print("  6. Configure Azure - Set up OCR credentials")
    print("  7. System Status - View capabilities and health")
    print("  8. Settings - Customize application behavior")
    print("  9. Help - Get detailed usage information")
    print("  0. Exit - Close the application")

def demo_file_structure():
    """Show the file structure and organization"""
    print("\n" + "#"*80)
    print("# GRACE CLI - FILE STRUCTURE")
    print("#"*80)
    
    print("\nProject Structure:")
    print("""
grace-cli-client/
├── grace_cli.py          # Main CLI application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── README.md            # Documentation
├── test_grace_cli.py    # Test suite
├── demo.py              # This demonstration script
├── screenshots/         # Screenshot storage (auto-created)
├── .grace/             # Configuration directory (auto-created)
│   └── config.json     # Persistent settings
└── .env                # Environment variables (optional)
""")
    
    # Show actual files
    current_dir = Path(".")
    print("\nActual files in current directory:")
    for item in sorted(current_dir.iterdir()):
        if item.is_file():
            size = item.stat().st_size
            print(f"  📄 {item.name:<25} ({size:,} bytes)")
        elif item.is_dir() and not item.name.startswith('.'):
            print(f"  📁 {item.name}/")

def demo_dependencies():
    """Show dependency information"""
    print("\n" + "#"*80)
    print("# GRACE CLI - DEPENDENCIES & REQUIREMENTS")
    print("#"*80)
    
    print("\nCore Dependencies:")
    dependencies = [
        ("rich", "Beautiful terminal formatting and progress bars"),
        ("textual", "Modern terminal user interfaces"),
        ("click", "Command-line interface framework"),
        ("typer", "Type-hint based CLI framework"),
        ("requests", "HTTP library for Azure OCR API"),
        ("pillow", "Image processing and manipulation"),
        ("numpy", "Numerical computing for image data"),
        ("mss", "Cross-platform screenshot capture"),
        ("PyWinCtl", "Cross-platform window management"),
        ("pygetwindow", "Window detection and control"),
        ("pyautogui", "GUI automation and screenshot fallback"),
        ("pandas", "Data manipulation and CSV export"),
        ("python-dotenv", "Environment variable management"),
        ("psutil", "System and process utilities")
    ]
    
    for dep, desc in dependencies:
        print(f"  • {dep:<15} - {desc}")
    
    print("\nPlatform-specific (Windows):")
    print("  • dxcam         - High-performance DirectX screen capture")
    print("  • win32gui      - Windows GUI API access")
    print("  • win32con      - Windows constants")
    
    print("\nPlatform-specific (Linux):")
    print("  • xdotool       - X11 window manipulation")
    print("  • wmctrl        - Window manager control")
    print("  • scrot         - Screenshot utility")

def main():
    """Run the complete demonstration"""
    print("Grace Biosensor Data Capture - CLI Edition")
    print("Complete Feature Demonstration")
    print("Author: Anas Gulzar Dev")
    print("Version: 2.0.0")
    
    # Check if we're in the right directory
    if not Path("grace_cli.py").exists():
        print("\nError: grace_cli.py not found in current directory")
        print("Please run this demo from the grace-cli-client directory")
        return False
    
    try:
        # Run all demonstrations
        demo_basic_commands()
        demo_configuration()
        demo_capture_features()
        demo_interactive_mode()
        demo_file_structure()
        demo_dependencies()
        
        print("\n" + "#"*80)
        print("# DEMONSTRATION COMPLETE")
        print("#"*80)
        
        print("\nGrace CLI is fully functional and ready to use!")
        print("\nNext steps:")
        print("1. Configure Azure Computer Vision:")
        print("   python grace_cli.py configure")
        print("")
        print("2. Start interactive mode:")
        print("   python grace_cli.py interactive")
        print("")
        print("3. Or use direct commands:")
        print("   python grace_cli.py list-windows")
        print("   python grace_cli.py capture")
        print("")
        print("4. Get help anytime:")
        print("   python grace_cli.py --help")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        return False
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)