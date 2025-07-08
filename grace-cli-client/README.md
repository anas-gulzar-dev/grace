# Grace Biosensor Data Capture - CLI Edition

🚀 **A beautiful, fully-functional command-line interface for biosensor data capture with cross-platform window detection, screenshot capture, Azure OCR integration, and real-time data export capabilities.**

## ✨ Features

- 🎨 **Beautiful CLI Interface** - Rich text formatting, progress bars, and interactive menus
- 🖥️ **Cross-Platform Window Detection** - Works on Windows, macOS, and Linux
- 📸 **Multi-Method Screenshot Capture** - DXcam, MSS, scrot, PyAutoGUI support
- 🔍 **Azure Computer Vision OCR** - Advanced text extraction from screenshots
- 📱 **Smart Device Categorization** - Automatically categorizes mobile devices, tablets, emulators
- ⚡ **Real-Time Auto-Capture** - Automated data collection with configurable intervals
- 💾 **Multiple Export Formats** - CSV and JSON data export
- ⚙️ **Configurable Settings** - Persistent configuration management
- 🎯 **Interactive & Command-Line Modes** - Both GUI-like TUI and direct CLI commands

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Install

1. **Clone or download the Grace CLI client:**
   ```bash
   cd grace-cli-client
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Platform-specific dependencies:**

   **Windows:**
   ```bash
   pip install dxcam win32gui win32con
   ```

   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt install python3-tk xdotool wmctrl scrot
   pip install -r requirements.txt
   ```

   **macOS:**
   ```bash
   pip install -r requirements.txt
   ```

### Azure Computer Vision Setup

1. **Create an Azure Computer Vision resource:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new Computer Vision resource
   - Get your endpoint URL and API key

2. **Configure Grace CLI:**
   ```bash
   python grace_cli.py configure --endpoint "YOUR_ENDPOINT" --key "YOUR_API_KEY"
   ```

   Or create a `.env` file:
   ```env
   AZURE_COMPUTER_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
   AZURE_COMPUTER_VISION_KEY=your-api-key-here
   ```

## 🚀 Usage

### Interactive Mode (Recommended)

Launch the beautiful interactive CLI interface:

```bash
python grace_cli.py interactive
```

This provides a menu-driven interface with:
- 📋 Window listing and selection
- 📸 Manual and automatic capture
- ⚙️ Configuration management
- 📊 System status monitoring
- 💾 Data export options

### Command-Line Mode

#### List Available Windows
```bash
# Show all windows with categories
python grace_cli.py list-windows

# Show simple list without categories
python grace_cli.py list-windows --no-categories
```

#### Capture a Specific Window
```bash
# Interactive window selection
python grace_cli.py capture

# Capture by window title
python grace_cli.py capture --window "Calculator"

# Capture and export to CSV
python grace_cli.py capture --window "Calculator" --csv

# Capture and export to both CSV and JSON
python grace_cli.py capture --window "Calculator" --csv --json
```

#### Auto-Capture Mode
```bash
# Auto-capture every 5 seconds
python grace_cli.py auto-capture --window "Calculator" --interval 5

# Auto-capture for 60 seconds
python grace_cli.py auto-capture --window "Calculator" --interval 5 --duration 60

# Infinite auto-capture (stop with Ctrl+C)
python grace_cli.py auto-capture --window "Calculator" --interval 10
```

#### Configuration Management
```bash
# Configure Azure OCR
python grace_cli.py configure

# Set Azure credentials directly
python grace_cli.py configure --endpoint "YOUR_ENDPOINT" --key "YOUR_KEY"

# Show system status
python grace_cli.py status

# Show version information
python grace_cli.py version
```

## 📁 File Structure

```
grace-cli-client/
├── grace_cli.py          # Main CLI application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── screenshots/         # Screenshot storage (auto-created)
├── .grace/             # Configuration directory (auto-created)
│   └── config.json     # Persistent settings
└── .env                # Environment variables (optional)
```

## 🎨 CLI Interface Preview

### Interactive Menu
```
╭─────────────────── Welcome to Grace CLI ───────────────────╮
│                                                             │
│           Grace Biosensor Data Capture                     │
│                CLI Edition v2.0.0                          │
│                                                             │
│  ✓ Cross-platform window detection                         │
│  ✓ Multi-method screenshot capture                         │
│  ✓ Azure Computer Vision OCR                               │
│  ✓ Real-time data export                                   │
│  ✓ Beautiful CLI interface                                 │
│                                                             │
╰─────────────────────────────────────────────────────────────╯

Grace CLI Menu
1. List Windows
2. Select Window
3. Capture Now
4. Auto Capture
5. Export Results
6. Configure Azure
7. System Status
8. Settings
9. Help
0. Exit
```

### Window Categories
```
Available Windows
├── 📱 Mobile Phones (2)
│   ├── [1] Samsung Galaxy S21 - Emulator (1080x1920)
│   └── [2] iPhone 13 Pro - Simulator (1170x2532)
├── 📟 Tablets (1)
│   └── [3] iPad Pro - Simulator (2048x2732)
├── 🎮 Emulators (3)
│   ├── [4] BlueStacks App Player (1600x900)
│   ├── [5] NoxPlayer (1280x720)
│   └── [6] MEmu Play (1280x720)
└── 🔧 Dev Tools (2)
    ├── [7] Android Studio (1920x1080)
    └── [8] scrcpy - Device Mirror (720x1280)
```

### Capture Progress
```
📸 Capturing window: Calculator
⠋ Taking screenshot...     ████████████████████ 100%
✓ Screenshot saved: screenshot_20231215_143022_1234.png
⠋ Processing with OCR...   ████████████████████ 100%

════════════════════════════════════════════════════════════
                        OCR Results
════════════════════════════════════════════════════════════

╭─────── Extracted Text from: Calculator ───────╮
│                                                │
│  2 + 2 = 4                                    │
│  Memory: 0                                     │
│  History: Clear                                │
│                                                │
╰─────────── Captured at: 2023-12-15 14:30:22 ──╯
```

## ⚙️ Configuration Options

### Azure OCR Settings
- **Endpoint**: Azure Computer Vision endpoint URL
- **API Key**: Azure Computer Vision subscription key
- **API Version**: OCR API version (default: v3.2)
- **Language**: OCR language detection (default: auto)
- **Timeout**: Request timeout in seconds (default: 30)

### Capture Settings
- **Auto Interval**: Time between auto-captures (default: 5 seconds)
- **Max Screenshots**: Maximum screenshots to keep (default: 5)
- **Preferred Method**: Screenshot capture method preference
- **Window Activation**: Whether to activate windows before capture

### Export Settings
- **Auto CSV**: Automatically export to CSV (default: true)
- **Auto JSON**: Automatically export to JSON (default: false)
- **CSV Filename**: Default CSV filename (default: auto_data.csv)
- **Include Full OCR**: Include complete OCR response in exports

### UI Settings
- **Show Debug**: Display detailed error messages
- **Show Categories**: Group windows by device type
- **Color Theme**: CLI color scheme (auto/dark/light)
- **Table Style**: Table border style (rounded/simple/heavy)

## 🔧 Troubleshooting

### Common Issues

**1. No windows detected:**
```bash
# Check system status
python grace_cli.py status

# Install window management dependencies
pip install PyWinCtl pygetwindow
```

**2. Screenshot capture fails:**
```bash
# Linux: Install system dependencies
sudo apt install python3-tk xdotool wmctrl scrot

# Windows: Install DXcam for better performance
pip install dxcam
```

**3. OCR not working:**
```bash
# Check Azure configuration
python grace_cli.py configure

# Verify credentials
python grace_cli.py status
```

**4. Permission errors:**
```bash
# Linux: Add user to required groups
sudo usermod -a -G video $USER

# Restart terminal session
```

### Debug Mode

Enable debug mode for detailed error information:
```bash
# Set environment variable
export GRACE_DEBUG=true

# Or configure in interactive mode
python grace_cli.py interactive
# → Settings → Enable debug mode
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup

1. **Clone the repository**
2. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio
   ```
3. **Run tests:**
   ```bash
   pytest
   ```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Anas Gulzar Dev**
- GitHub: [@anas-gulzar-dev](https://github.com/anas-gulzar-dev)
- Project: [Grace Biosensor Data Capture](https://github.com/anas-gulzar-dev/grace)

## 🙏 Acknowledgments

- **Rich** - Beautiful terminal formatting
- **Textual** - Modern terminal user interfaces
- **Click/Typer** - Command-line interface framework
- **Azure Computer Vision** - OCR text extraction
- **PyWinCtl** - Cross-platform window management

---

**Made with ❤️ for the biosensor research community**