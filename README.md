# 🔬 Biosensor Data Capture - Professional Edition

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

A professional-grade application for capturing, processing, and analyzing data from biosensor devices through automated screen capture and OCR technology.

## 🌟 Features

### 📸 Advanced Screen Capture
- **Multi-Device Support**: Capture from phones, tablets, computers, and biosensor displays
- **Smart Window Detection**: Automatically detects and categorizes device windows
- **High-Quality Capture**: Optimized capture methods for best image quality
- **Auto-Refresh**: Continuously scans for new devices and windows

### 🔍 Intelligent OCR Processing
- **Azure Computer Vision**: Microsoft's advanced OCR technology
- **Multi-Language Support**: Configurable language detection
- **Orientation Detection**: Automatically handles rotated text
- **Threaded Processing**: Non-blocking OCR for smooth UI experience

### 📊 Data Management
- **CSV Export**: Structured data for spreadsheet analysis
- **JSON Export**: Detailed export with metadata
- **Timestamp Tracking**: Precise capture timestamps
- **Auto-Cleanup**: Manages screenshot storage (keeps last 5)

### ⚡ Automation
- **Auto-Capture**: Scheduled automatic data capture
- **Configurable Intervals**: Adjustable capture frequency
- **Progress Tracking**: Real-time monitoring
- **Easy Control**: Start/stop with single click

### 🎨 Modern UI/UX
- **Dark/Light Themes**: Professional theme switching
- **Modern Design**: Clean interface with gradients and icons
- **Real-Time Status**: Live updates and progress indicators
- **Interactive Help**: Comprehensive built-in documentation

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+** installed on your system
2. **Azure Computer Vision API** subscription
3. **Device connection** (USB or wireless)
4. **Screen mirroring software** (scrcpy for Android, QuickTime for iOS)

### Installation

1. **Clone or download** this repository:
   ```bash
   git clone <repository-url>
   cd biosensor-data-capture
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Add your Azure Computer Vision API credentials

4. **Launch the application**:
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Environment Setup (.env file)

Create a `.env` file in the project root:

```env
# Azure Computer Vision API Configuration
AZURE_API_KEY=your_azure_api_key_here
AZURE_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/

# OCR Settings
OCR_LANGUAGE=en
DETECT_ORIENTATION=true

# Application Settings
SCREENSHOTS_FOLDER=screenshots
EXPORTS_FOLDER=exports
AUTO_CAPTURE_INTERVAL=10
MAX_SCREENSHOTS_TO_KEEP=5

# UI Settings
DEFAULT_THEME=dark
ENABLE_ANIMATIONS=true
```

### Azure Computer Vision Setup

1. **Create Azure Account**: Sign up at [azure.microsoft.com](https://azure.microsoft.com)
2. **Create Resource**: Create a new Computer Vision resource
3. **Get Credentials**: Copy API key and endpoint from "Keys and Endpoint" section
4. **Update Configuration**: Add credentials to your `.env` file

## 📋 Step-by-Step Usage Guide

### Step 1: Device Connection

1. **Connect your biosensor device** via USB or wireless
2. **Enable USB debugging** (Android devices)
3. **Start screen mirroring**:
   - **Android**: `scrcpy` command
   - **iOS**: QuickTime Player or similar
   - **Windows**: Built-in projection tools
4. **Verify detection**: Click "🔍 Show ALL Devices NOW"

### Step 2: Manual Capture

1. **Select window** from the dropdown menu
2. **Position device** so biosensor data is visible
3. **Capture**: Click "📸 Capture Selected Window"
4. **Review results** in the OCR text area
5. **Export data** using CSV or JSON buttons

### Step 3: Auto-Capture Setup

1. **Enable auto-capture** checkbox
2. **Set interval** using the spin box (seconds)
3. **Start monitoring** - system captures automatically
4. **Monitor progress** via progress bar and status
5. **Stop when done** using the stop button

### Step 4: Data Management

1. **Review captures**: Check `screenshots/` folder
2. **Access exports**: Find data in `exports/` folder
3. **Automatic cleanup**: System keeps last 5 screenshots
4. **Backup data**: Regular backup of export files

## 🎨 User Interface Guide

### Theme Switching
- **Dark Theme**: Professional dark interface (default)
- **Light Theme**: Clean light interface
- **Toggle**: Use the theme button in the header

### Main Interface Elements

1. **Header Section**:
   - Application title
   - Theme toggle button
   - Help documentation button

2. **Window Selection**:
   - Dropdown menu for available windows
   - Refresh button for device detection
   - Device discovery dialog

3. **Capture Controls**:
   - Manual capture button
   - Auto-capture settings
   - Progress monitoring

4. **Results Section**:
   - OCR text display
   - Export buttons (CSV/JSON)
   - Clear results option

5. **Status Area**:
   - Real-time status messages
   - Progress indicators
   - Error notifications

## 🔧 Troubleshooting

### Common Issues

#### API Key Problems
- **Issue**: "Invalid API key" error
- **Solution**: Verify `.env` file and Azure credentials
- **Check**: Test API key in Azure portal

#### Device Not Detected
- **Issue**: Device window not in dropdown
- **Solutions**:
  - Ensure screen mirroring is active
  - Click device refresh button
  - Check window visibility
  - Reconnect device

#### Capture Issues
- **Issue**: Black or empty screenshots
- **Solutions**:
  - Ensure window is not minimized
  - Check window positioning
  - Restart mirroring software
  - Try different window

#### OCR Accuracy
- **Issue**: Poor text recognition
- **Solutions**:
  - Improve image quality/lighting
  - Ensure text is clearly visible
  - Adjust screen brightness
  - Capture when text is static

### Diagnostic Steps

1. **Check configuration** in `.env` file
2. **Test API connection** with manual capture
3. **Verify permissions** for screen capture
4. **Check file paths** for directories
5. **Review logs** in console output

## 📁 Project Structure

```
project/
├── main.py                 # Main application file
├── config.py              # Configuration loader
├── .env                   # Environment variables (create this)
├── .env.example          # Environment template
├── requirements.txt       # Python dependencies
├── README.md             # This documentation
├── screenshots/          # Captured images (auto-created)
├── exports/             # CSV and JSON exports (auto-created)
└── docs/                # Additional documentation
```

## 🔒 Security

### Best Practices

- **Environment Variables**: Never commit API keys to version control
- **`.env` File**: Add to `.gitignore` to prevent accidental commits
- **API Key Rotation**: Regularly rotate Azure API keys
- **Access Control**: Limit API permissions to minimum required
- **Local Storage**: All data processed locally for privacy

## 📦 Dependencies

### Core Dependencies
- **PyQt5**: GUI framework
- **requests**: HTTP client for API calls
- **Pillow**: Image processing
- **python-dotenv**: Environment management
- **pygetwindow**: Window detection
- **pyautogui**: Screen capture
- **mss**: Fast screen capture

### Optional Dependencies
- **qdarkstyle**: Modern dark theme
- **qtawesome**: Icon library
- **dxcam**: Hardware-accelerated capture
- **opencv-python**: Advanced image processing

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help

1. **Built-in Help**: Use the "❓ Help" button in the application
2. **Documentation**: Check this README and inline documentation
3. **Issues**: Report bugs via GitHub issues
4. **Logs**: Check console output for detailed error information

### Reporting Issues

When reporting issues, please include:
- **Error messages**: Full error text from console
- **Steps to reproduce**: Detailed reproduction steps
- **Environment**: OS, Python version, dependency versions
- **Configuration**: Relevant settings (without API keys)

## 🔄 Version History

### v2.0.0 (Current)
- ✨ Modern UI with dark/light themes
- 📚 Comprehensive documentation system
- 🔄 Automatic screenshot cleanup
- 🎨 Enhanced visual design
- 🔧 Improved error handling

### v1.0.0
- 🚀 Initial release
- 📸 Basic screen capture
- 🔍 OCR processing
- 📊 Data export functionality

---

**Made with ❤️ for the biosensor research community**