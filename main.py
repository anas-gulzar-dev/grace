#!/usr/bin/env python3
"""
Grace Biosensor Data Capture - Cross-Platform Professional Edition

A comprehensive, cross-platform application for capturing and analyzing biosensor data
through automated screen capture and OCR processing using Azure Computer Vision API.

🌟 KEY FEATURES:
• Cross-platform support (Windows, macOS, Linux)
• Real-time window detection and management
• Automated screenshot capture with multiple methods
• Azure Computer Vision OCR integration
• Auto-capture with configurable intervals
• CSV and JSON data export
• Modern PyQt5 interface with dark theme
• Device discovery and categorization
• Zoom functionality and accessibility features

🔧 SUPPORTED PLATFORMS:
• Windows 10/11 (with dxcam acceleration)
• macOS 10.14+ (with PyObjC frameworks)
• Linux (Ubuntu, Fedora, Arch with X11 tools)

📦 INSTALLATION:

1. Universal Installer (Recommended):
   python install_universal.py

2. All-Platform Dependencies:
   pip install -r all_platform_requirements.txt

3. Platform-Specific:
   Windows: install_windows.ps1
   Linux: install_linux.sh
   macOS: install_macos.sh

🚀 QUICK START:
1. Install dependencies using one of the methods above
2. Copy .env.example to .env and add your Azure API credentials
3. Connect your biosensor device
4. Start screen mirroring (e.g., scrcpy for Android)
5. Run: python main.py

🔍 DEPENDENCIES:
• Core: PyQt5, PyWinCtl, requests, Pillow, pyautogui, mss
• Windows: pywin32, dxcam (optional)
• Linux: python3-xlib, xdotool, wmctrl, scrot
• macOS: pyobjc, pyobjc-frameworks

📋 CONFIGURATION:
Create a .env file with:
- AZURE_API_KEY=your_azure_api_key
- AZURE_ENDPOINT=your_azure_endpoint
- DEFAULT_CAPTURE_INTERVAL=5
- SCREENSHOTS_FOLDER=screenshots
- OCR_LANGUAGE=en

🛠️ TROUBLESHOOTING:
• For installation issues, see TROUBLESHOOTING.md
• For missing dependencies, run the universal installer
• For platform-specific issues, check the README.md

📄 LICENSE: MIT License
👨‍💻 AUTHOR: Anas Gulzar (https://github.com/anas-gulzar-dev/grace/)
📅 VERSION: 2.0.0 - Cross-Platform Edition
"""

import sys
import os
import json
import time
import random
import csv
import glob
from datetime import datetime
from typing import Optional, Dict, Any

import pywinctl

# Cross-platform window management
try:
    import pywinctl as gw  # Cross-platform replacement for pygetwindow
    WINDOW_MANAGER_AVAILABLE = True
except ImportError:
    try:
        import pygetwindow as gw  # Fallback for Windows-only environments
        WINDOW_MANAGER_AVAILABLE = True
        print("Using pygetwindow (Windows-only fallback)")
    except ImportError:
        WINDOW_MANAGER_AVAILABLE = False
        print("❌ No window manager available. Please install PyWinCtl: pip install PyWinCtl")
import pyautogui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QWidget, QCheckBox,
    QSpinBox, QGroupBox, QMessageBox, QProgressBar,
    QComboBox, QDialog, QTreeWidget, QTreeWidgetItem, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QFrame, QSplitter, QTabWidget
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QLinearGradient, QPainter, QTransform
import mss
import numpy as np
from PIL import Image

# Modern JSON and text formatting libraries
try:
    import pygments
    from pygments import highlight
    from pygments.lexers import JsonLexer, TextLexer
    from pygments.formatters import HtmlFormatter
    from pygments.styles import get_style_by_name
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    print("⚠️ Pygments not available. Install with: pip install pygments")

try:
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.text import Text
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️ Rich not available. Install with: pip install rich")

try:
    import markdown
    from markdown.extensions import codehilite
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("⚠️ Markdown not available. Install with: pip install markdown")

# Clipboard functionality
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    print("⚠️ Clipboard functionality not available. Install with: pip install pyperclip")

# Modern UI Libraries
try:
    import qdarkstyle
    import qtawesome as qta
    MODERN_UI_AVAILABLE = True
except ImportError:
    MODERN_UI_AVAILABLE = False
    print("Modern UI libraries not available, using default styling")

try:
    import requests
except ImportError:
    requests = None

# Platform detection and platform-specific imports
import platform
PLATFORM = platform.system().lower()

# Platform-specific screen capture
try:
    if PLATFORM == 'windows':
        import dxcam
        DXCAM_AVAILABLE = True
    else:
        DXCAM_AVAILABLE = False
except ImportError:
    DXCAM_AVAILABLE = False
    if PLATFORM == 'windows':
        print("DXcam not available, using MSS fallback")

# Platform-specific window management tools
if PLATFORM == 'linux':
    try:
        import subprocess
        # Test if xdotool and wmctrl are available
        subprocess.run(['which', 'xdotool'], check=True, capture_output=True)
        subprocess.run(['which', 'wmctrl'], check=True, capture_output=True)
        LINUX_TOOLS_AVAILABLE = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        LINUX_TOOLS_AVAILABLE = False
        print("⚠️  Linux window management tools not found. Please install: sudo apt-get install xdotool wmctrl")
else:
    LINUX_TOOLS_AVAILABLE = False

# Cross-platform process management
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available, some features may be limited")

try:
    from config import (
        AZURE_API_KEY, AZURE_ENDPOINT, DEFAULT_CAPTURE_INTERVAL,
        SCREENSHOTS_FOLDER, SCRCPY_WINDOW_TITLES, OCR_LANGUAGE, DETECT_ORIENTATION,
        ENABLE_AUTO_DELETE_SCREENSHOTS
    )
except ImportError:
    print("ERROR: Configuration not found!")
    print("Please ensure you have:")
    print("1. Created a .env file with your Azure credentials")
    print("2. Copied .env.example to .env and updated the values")
    print("3. Run the application again after setting up .env")
    sys.exit(1)


class InstantDeviceDialog(QDialog):
    """Dialog window to display ALL devices instantly in a simple list"""
    
    def __init__(self, device_list, parent=None):
        super().__init__(parent)
        self.device_list = device_list
        self.setWindowTitle("📱 ALL DEVICES - INSTANT VIEW")
        self.setGeometry(200, 200, 900, 700)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("📱 ALL CONNECTED DEVICES - NO FILTERING")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title_label)
        
        # Device count
        count_label = QLabel(f"🎯 Total Devices Found: {len(self.device_list)}")
        count_label.setFont(QFont("Arial", 12, QFont.Bold))
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet("color: #4CAF50; padding: 5px;")
        layout.addWidget(count_label)
        
        # Device list
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(5)
        self.device_table.setHorizontalHeaderLabels(["#", "Device/Window Name", "Size", "Position", "Visible"])
        self.device_table.setRowCount(len(self.device_list))
        
        # Populate table
        for i, window in enumerate(self.device_list):
            # Row number
            self.device_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            
            # Device name
            name_item = QTableWidgetItem(window.title)
            name_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.device_table.setItem(i, 1, name_item)
            
            # Size
            size_text = f"{window.width} x {window.height}"
            self.device_table.setItem(i, 2, QTableWidgetItem(size_text))
            
            # Position
            pos_text = f"({window.left}, {window.top})"
            self.device_table.setItem(i, 3, QTableWidgetItem(pos_text))
            
            # Visible status
            visible_text = "✅ Yes" if window.visible else "❌ No"
            visible_item = QTableWidgetItem(visible_text)
            if window.visible:
                visible_item.setForeground(QColor("green"))
            else:
                visible_item.setForeground(QColor("red"))
            self.device_table.setItem(i, 4, visible_item)
        
        # Table styling
        self.device_table.resizeColumnsToContents()
        self.device_table.setAlternatingRowColors(True)
        self.device_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.device_table.setSortingEnabled(True)
        layout.addWidget(self.device_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.clicked.connect(self.refresh_devices)
        refresh_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px; border-radius: 4px; }")
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 8px; border-radius: 4px; }")
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def refresh_devices(self):
        """Refresh the device list - Cross-platform implementation"""
        try:
            if not WINDOW_MANAGER_AVAILABLE:
                QMessageBox.warning(self, "Window Manager Error", 
                                  "Window manager not available. Please install PyWinCtl: pip install PyWinCtl")
                return
            
            # Get updated device list
            all_windows = gw.getAllWindows()
            self.device_list = []
            
            # Platform-specific filtering
            excluded_titles = ['Program Manager', 'Desktop Window Manager']  # Windows
            if PLATFORM == 'linux':
                excluded_titles.extend(['Desktop', 'Panel', 'Taskbar', 'Unity Panel', 'gnome-panel'])
            elif PLATFORM == 'darwin':  # macOS
                excluded_titles.extend(['Dock', 'Menu Bar', 'Spotlight'])
            
            for window in all_windows:
                if window.title and window.title.strip():
                    if window.title not in excluded_titles:
                        # Additional filtering for very small windows (likely system windows)
                        try:
                            if hasattr(window, 'width') and hasattr(window, 'height'):
                                if window.width > 50 and window.height > 50:  # Filter out tiny windows
                                    self.device_list.append(window)
                            else:
                                self.device_list.append(window)
                        except:
                            # If we can't get dimensions, include it anyway
                            self.device_list.append(window)
            
            # Update table
            self.device_table.setRowCount(len(self.device_list))
            
            for i, window in enumerate(self.device_list):
                self.device_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                
                name_item = QTableWidgetItem(window.title)
                name_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.device_table.setItem(i, 1, name_item)
                
                # Handle potential attribute differences between PyWinCtl and pygetwindow
                try:
                    width = getattr(window, 'width', getattr(window, 'size', [0, 0])[0] if hasattr(window, 'size') else 0)
                    height = getattr(window, 'height', getattr(window, 'size', [0, 0])[1] if hasattr(window, 'size') else 0)
                    size_text = f"{width} x {height}"
                except:
                    size_text = "Unknown"
                self.device_table.setItem(i, 2, QTableWidgetItem(size_text))
                
                try:
                    left = getattr(window, 'left', getattr(window, 'topleft', [0, 0])[0] if hasattr(window, 'topleft') else 0)
                    top = getattr(window, 'top', getattr(window, 'topleft', [0, 0])[1] if hasattr(window, 'topleft') else 0)
                    pos_text = f"({left}, {top})"
                except:
                    pos_text = "Unknown"
                self.device_table.setItem(i, 3, QTableWidgetItem(pos_text))
                
                try:
                    visible = getattr(window, 'visible', getattr(window, 'isVisible', True))
                    visible_text = "✅ Yes" if visible else "❌ No"
                    visible_item = QTableWidgetItem(visible_text)
                    if visible:
                        visible_item.setForeground(QColor("green"))
                    else:
                        visible_item.setForeground(QColor("red"))
                except:
                    visible_item = QTableWidgetItem("Unknown")
                self.device_table.setItem(i, 4, visible_item)
            
            # Update count label
            count_label = self.findChild(QLabel)
            if count_label:
                for child in self.findChildren(QLabel):
                    if "Total Devices Found" in child.text():
                        child.setText(f"🎯 Total Devices Found: {len(self.device_list)} (Platform: {PLATFORM.title()})")
                        break
            
            self.device_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh devices: {str(e)}\nPlatform: {PLATFORM}")


class DeviceDiscoveryDialog(QDialog):
    """Dialog window to display all discovered devices in a tree structure"""
    
    def __init__(self, devices_data, parent=None):
        super().__init__(parent)
        self.devices_data = devices_data
        self.setWindowTitle("🔍 Device Discovery Results")
        self.setGeometry(200, 200, 800, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("🔍 All Connected Devices")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Summary
        total_devices = sum(len(category) for category in self.devices_data.values())
        summary_label = QLabel(f"📊 Total devices found: {total_devices}")
        summary_label.setFont(QFont("Arial", 12))
        summary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(summary_label)
        
        # Tree widget for devices
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Device Name", "Size", "Position", "Visible", "Keywords"])
        self.tree.setAlternatingRowColors(True)
        
        # Populate tree with devices
        self.populate_tree()
        
        layout.addWidget(self.tree)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        # Expand all categories by default
        self.tree.expandAll()
        
        # Resize columns to content
        for i in range(5):
            self.tree.resizeColumnToContents(i)
    
    def populate_tree(self):
        """Populate the tree widget with device data"""
        category_icons = {
            'mobile_phones': '📱',
            'tablets': '📟',
            'wearables': '⌚',
            'emulators': '🎮',
            'dev_tools': '🛠️',
            'unknown_devices': '❓'
        }
        
        for category, device_list in self.devices_data.items():
            if device_list:  # Only show categories with devices
                category_name = category.replace('_', ' ').title()
                icon = category_icons.get(category, '📱')
                
                # Create category item
                category_item = QTreeWidgetItem([f"{icon} {category_name} ({len(device_list)})"])
                category_item.setFont(0, QFont("Arial", 10, QFont.Bold))
                self.tree.addTopLevelItem(category_item)
                
                # Add devices under category
                for device in device_list:
                    device_item = QTreeWidgetItem([
                        device['title'],
                        device['size'],
                        device['position'],
                        str(device['visible']),
                        ', '.join(device['matched_keywords'][:3]) + ('...' if len(device['matched_keywords']) > 3 else '')
                    ])
                    category_item.addChild(device_item)
        
        # If no devices found, show a message
        if sum(len(category) for category in self.devices_data.values()) == 0:
            no_devices_item = QTreeWidgetItem(["❌ No devices detected"])
            no_devices_item.setFont(0, QFont("Arial", 10, QFont.Bold))
            self.tree.addTopLevelItem(no_devices_item)
            
            tips_item = QTreeWidgetItem(["💡 Tips to detect devices:"])
            tips_item.setFont(0, QFont("Arial", 10, QFont.Bold))
            self.tree.addTopLevelItem(tips_item)
            
            tips = [
                "• Connect your device via USB",
                "• Enable USB debugging (Android)",
                "• Start scrcpy or similar mirroring tool",
                "• Launch device emulators",
                "• Make sure device windows are visible"
            ]
            
            for tip in tips:
                tip_item = QTreeWidgetItem([tip])
                tips_item.addChild(tip_item)


class OCRWorker(QThread):
    """Worker thread for OCR processing to avoid blocking the UI"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, image_path: str, api_key: str, endpoint: str):
        super().__init__()
        self.image_path = image_path
        self.api_key = api_key
        self.endpoint = endpoint
    
    def run(self):
        try:
            if not requests:
                self.error.emit("requests library not installed. Please install: pip install requests")
                return
                
            # Azure Computer Vision OCR API call
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Content-Type': 'application/octet-stream'
            }
            
            with open(self.image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            response = requests.post(
                f"{self.endpoint}/vision/v3.2/ocr",
                headers=headers,
                data=image_data,
                params={'language': OCR_LANGUAGE, 'detectOrientation': str(DETECT_ORIENTATION).lower()}
            )
            
            if response.status_code == 200:
                self.finished.emit(response.json())
            else:
                self.error.emit(f"OCR API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.error.emit(f"OCR processing failed: {str(e)}")


class HelpDocumentationDialog(QDialog):
    """Comprehensive help and documentation dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Biosensor Data Capture - User Guide & Documentation")
        self.setGeometry(200, 200, 900, 700)
        self.setModal(True)
        
        # Zoom management for help dialog
        self.help_zoom_level = 1.0
        
        # Apply modern styling
        if MODERN_UI_AVAILABLE:
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        self.init_help_ui()
    
    def init_help_ui(self):
        """Initialize the help dialog UI"""
        layout = QVBoxLayout()
        
        # Header with title and zoom controls
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("🔬 Biosensor Data Capture - Complete User Guide")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00bcd4; margin: 10px; padding: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Zoom controls for help dialog
        help_zoom_layout = QHBoxLayout()
        help_zoom_layout.setSpacing(5)
        
        help_zoom_out_btn = QPushButton("🔍-")
        help_zoom_out_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ff9a9e, stop:1 #fecfef);
                color: #2d3748;
                border: none;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                min-width: 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ff8a80, stop:1 #fbb6ce);
            }
        """)
        help_zoom_out_btn.clicked.connect(self.help_zoom_out)
        help_zoom_layout.addWidget(help_zoom_out_btn)
        
        self.help_zoom_label = QLabel("100%")
        self.help_zoom_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 10px;
                font-weight: bold;
                padding: 6px 8px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
                min-width: 30px;
                text-align: center;
            }
        """)
        self.help_zoom_label.setAlignment(Qt.AlignCenter)
        help_zoom_layout.addWidget(self.help_zoom_label)
        
        help_zoom_in_btn = QPushButton("🔍+")
        help_zoom_in_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #a8edea, stop:1 #fed6e3);
                color: #2d3748;
                border: none;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                min-width: 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #81e6d9, stop:1 #fbb6ce);
            }
        """)
        help_zoom_in_btn.clicked.connect(self.help_zoom_in)
        help_zoom_layout.addWidget(help_zoom_in_btn)
        
        header_layout.addLayout(help_zoom_layout)
        layout.addLayout(header_layout)
        
        # Create tab widget for organized documentation
        tab_widget = QTabWidget()
        
        # Tab 1: Getting Started
        getting_started_tab = self.create_getting_started_tab()
        tab_widget.addTab(getting_started_tab, "🚀 Getting Started")
        
        # Tab 2: Step-by-Step Guide
        step_guide_tab = self.create_step_guide_tab()
        tab_widget.addTab(step_guide_tab, "📋 Step-by-Step Guide")
        
        # Tab 3: Features & Functions
        features_tab = self.create_features_tab()
        tab_widget.addTab(features_tab, "⚡ Features & Functions")
        
        # Tab 4: Troubleshooting
        troubleshooting_tab = self.create_troubleshooting_tab()
        tab_widget.addTab(troubleshooting_tab, "🔧 Troubleshooting")
        
        # Tab 5: Configuration
        config_tab = self.create_config_tab()
        tab_widget.addTab(config_tab, "⚙️ Configuration")
        
        # Tab 6: FAQ
        faq_tab = self.create_faq_tab()
        tab_widget.addTab(faq_tab, "❓ FAQ")
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_btn = QPushButton("✅ Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4caf50, stop: 1 #388e3c);
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #66bb6a, stop: 1 #4caf50);
            }
        """)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def help_zoom_in(self):
        """Zoom in the help documentation"""
        if self.help_zoom_level < 2.0:  # Max zoom 200%
            self.help_zoom_level += 0.1
            self.apply_help_zoom()
    
    def help_zoom_out(self):
        """Zoom out the help documentation"""
        if self.help_zoom_level > 0.5:  # Min zoom 50%
            self.help_zoom_level -= 0.1
            self.apply_help_zoom()
    
    def apply_help_zoom(self):
        """Apply zoom level to the help documentation"""
        # Update zoom label
        self.help_zoom_label.setText(f"{int(self.help_zoom_level * 100)}%")
        
        # Apply font scaling to all text elements
        for widget in self.findChildren(QWidget):
            if hasattr(widget, 'setFont'):
                widget_font = widget.font()
                if widget_font.pointSize() > 0:
                    base_size = 9 if widget_font.pointSize() <= 12 else 12
                    new_size = int(base_size * self.help_zoom_level)
                    widget_font.setPointSize(max(6, min(new_size, 24)))
                    widget.setFont(widget_font)
            
            # Special handling for QTextEdit content
            if isinstance(widget, QTextEdit):
                # Apply zoom to HTML content by adjusting font size in style
                current_html = widget.toHtml()
                # This is a simplified approach - in a real implementation,
                # you might want to parse and modify the HTML more carefully
                widget.setStyleSheet(f"font-size: {int(12 * self.help_zoom_level)}px;")
    
    def create_getting_started_tab(self):
        """Create the getting started tab content"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>🚀 Welcome to Biosensor Data Capture!</h2>
        
        <h3>📋 What This Application Does:</h3>
        <ul>
            <li><b>🖼️ Screen Capture:</b> Captures screenshots of device windows (phones, tablets, biosensor displays)</li>
            <li><b>🔍 OCR Processing:</b> Extracts text data from captured images using Azure Computer Vision</li>
            <li><b>📊 Data Export:</b> Saves extracted data to CSV and JSON formats</li>
            <li><b>⚡ Auto-Capture:</b> Automatically captures data at specified intervals</li>
            <li><b>🎯 Smart Detection:</b> Automatically detects connected devices and mirroring windows</li>
        </ul>
        
        <h3>🔧 Prerequisites:</h3>
        <ul>
            <li><b>Azure Computer Vision API:</b> You need an active Azure subscription with Computer Vision service</li>
            <li><b>Device Connection:</b> Connect your biosensor device via USB or wireless</li>
            <li><b>Screen Mirroring:</b> Use tools like scrcpy (Android) or QuickTime (iOS) for device mirroring</li>
            <li><b>Python Environment:</b> Python 3.7+ with required packages installed</li>
        </ul>
        
        <h3>📁 File Structure:</h3>
        <ul>
            <li><b>📄 .env:</b> Configuration file with API keys and settings</li>
            <li><b>📂 screenshots/:</b> Directory where captured images are stored</li>
            <li><b>📂 exports/:</b> Directory where CSV and JSON exports are saved</li>
            <li><b>📄 config.py:</b> Application configuration and settings</li>
        </ul>
        
        <h3>🎨 Theme Options:</h3>
        <p>The application supports both <b>Dark Theme</b> (default) and <b>Light Theme</b>. Use the theme toggle button in the header to switch between themes.</p>
        """)
        
        layout.addWidget(content)
        widget.setLayout(layout)
        return widget
    
    def create_step_guide_tab(self):
        """Create the step-by-step guide tab content"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>📋 Step-by-Step Usage Guide</h2>
        
        <h3>🔧 Step 1: Initial Setup</h3>
        <ol>
            <li><b>Configure API Keys:</b> Edit the <code>.env</code> file with your Azure Computer Vision API key and endpoint</li>
            <li><b>Install Dependencies:</b> Run <code>pip install -r requirements.txt</code></li>
            <li><b>Launch Application:</b> Run <code>python main.py</code></li>
        </ol>
        
        <h3>📱 Step 2: Device Connection</h3>
        <ol>
            <li><b>Connect Device:</b> Connect your biosensor device via USB</li>
            <li><b>Enable USB Debugging:</b> For Android devices, enable USB debugging in developer options</li>
            <li><b>Start Screen Mirroring:</b>
                <ul>
                    <li><b>Android:</b> Use scrcpy: <code>scrcpy</code></li>
                    <li><b>iOS:</b> Use QuickTime Player or similar tools</li>
                    <li><b>Windows:</b> Use built-in projection or third-party tools</li>
                </ul>
            </li>
            <li><b>Verify Detection:</b> Click "🔍 Show ALL Devices NOW" to see detected devices</li>
        </ol>
        
        <h3>🖼️ Step 3: Manual Capture</h3>
        <ol>
            <li><b>Select Window:</b> Choose your device window from the dropdown</li>
            <li><b>Position Device:</b> Make sure the biosensor data is visible on screen</li>
            <li><b>Capture:</b> Click "📸 Capture Selected Window"</li>
            <li><b>Review Results:</b> Check the OCR results in the text area</li>
            <li><b>Export Data:</b> Use "📊 Export to CSV" or "📋 Export to JSON" buttons</li>
        </ol>
        
        <h3>⚡ Step 4: Auto-Capture Setup</h3>
        <ol>
            <li><b>Enable Auto-Capture:</b> Check the "🔄 Enable Auto-Capture" checkbox</li>
            <li><b>Set Interval:</b> Adjust the capture interval (seconds) using the spin box</li>
            <li><b>Start Monitoring:</b> The system will automatically capture and process data</li>
            <li><b>Monitor Progress:</b> Watch the progress bar and status messages</li>
            <li><b>Stop When Done:</b> Click "🛑 Stop Auto-Capture" to end the session</li>
        </ol>
        
        <h3>📊 Step 5: Data Management</h3>
        <ol>
            <li><b>Review Captures:</b> All screenshots are saved in the <code>screenshots/</code> folder</li>
            <li><b>Check Exports:</b> CSV and JSON files are saved in the <code>exports/</code> folder</li>
            <li><b>Clean Up:</b> The system automatically keeps only the last 5 screenshots</li>
            <li><b>Backup Data:</b> Regularly backup your export files for long-term storage</li>
        </ol>
        """)
        
        layout.addWidget(content)
        widget.setLayout(layout)
        return widget
    
    def create_features_tab(self):
        """Create the features tab content"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>⚡ Features & Functions</h2>
        
        <h3>🖼️ Screen Capture Features</h3>
        <ul>
            <li><b>📱 Multi-Device Support:</b> Captures from phones, tablets, computers, and biosensor displays</li>
            <li><b>🎯 Smart Window Detection:</b> Automatically detects and categorizes device windows</li>
            <li><b>📸 High-Quality Capture:</b> Uses optimized capture methods for best image quality</li>
            <li><b>🔄 Auto-Refresh:</b> Continuously scans for new devices and windows</li>
        </ul>
        
        <h3>🔍 OCR Processing Features</h3>
        <ul>
            <li><b>☁️ Azure Computer Vision:</b> Uses Microsoft's advanced OCR technology</li>
            <li><b>🌐 Multi-Language Support:</b> Configurable language detection</li>
            <li><b>📐 Orientation Detection:</b> Automatically handles rotated text</li>
            <li><b>⚡ Threaded Processing:</b> Non-blocking OCR processing for smooth UI</li>
        </ul>
        
        <h3>📊 Data Export Features</h3>
        <ul>
            <li><b>📄 CSV Export:</b> Structured data export for spreadsheet analysis</li>
            <li><b>📋 JSON Export:</b> Detailed export with metadata and formatting</li>
            <li><b>🕒 Timestamp Tracking:</b> All captures include precise timestamps</li>
            <li><b>📁 Organized Storage:</b> Automatic file organization and naming</li>
        </ul>
        
        <h3>⚡ Automation Features</h3>
        <ul>
            <li><b>🔄 Auto-Capture:</b> Scheduled automatic data capture</li>
            <li><b>⏱️ Configurable Intervals:</b> Adjustable capture frequency</li>
            <li><b>📈 Progress Tracking:</b> Real-time progress monitoring</li>
            <li><b>🛑 Easy Control:</b> Start/stop automation with single click</li>
        </ul>
        
        <h3>🎨 User Interface Features</h3>
        <ul>
            <li><b>🌙 Dark/Light Themes:</b> Toggle between professional dark and light themes</li>
            <li><b>📱 Modern Design:</b> Clean, professional interface with gradients and icons</li>
            <li><b>📊 Real-Time Status:</b> Live status updates and progress indicators</li>
            <li><b>🔍 Device Discovery:</b> Interactive device detection and categorization</li>
        </ul>
        
        <h3>🔧 Management Features</h3>
        <ul>
            <li><b>🗂️ Auto-Cleanup:</b> Automatically manages screenshot storage (keeps last 5)</li>
            <li><b>⚙️ Configuration:</b> Environment-based configuration management</li>
            <li><b>🔒 Security:</b> Secure API key management through environment variables</li>
            <li><b>📚 Documentation:</b> Comprehensive built-in help and documentation</li>
        </ul>
        """)
        
        layout.addWidget(content)
        widget.setLayout(layout)
        return widget
    
    def create_troubleshooting_tab(self):
        """Create the troubleshooting tab content"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>🔧 Troubleshooting Guide</h2>
        
        <h3>❌ Common Issues & Solutions</h3>
        
        <h4>🔑 API Key Issues</h4>
        <ul>
            <li><b>Problem:</b> "Invalid API key" error</li>
            <li><b>Solution:</b> Check your <code>.env</code> file and ensure AZURE_API_KEY is correct</li>
            <li><b>Verification:</b> Test your API key in Azure portal</li>
        </ul>
        
        <h4>📱 Device Not Detected</h4>
        <ul>
            <li><b>Problem:</b> Device window not appearing in dropdown</li>
            <li><b>Solutions:</b>
                <ul>
                    <li>Ensure device is connected and screen mirroring is active</li>
                    <li>Click "🔍 Show ALL Devices NOW" to refresh device list</li>
                    <li>Make sure the device window is visible and not minimized</li>
                    <li>Try disconnecting and reconnecting the device</li>
                </ul>
            </li>
        </ul>
        
        <h4>🖼️ Capture Issues</h4>
        <ul>
            <li><b>Problem:</b> Black or empty screenshots</li>
            <li><b>Solutions:</b>
                <ul>
                    <li>Ensure the target window is not minimized</li>
                    <li>Check if the window is behind other windows</li>
                    <li>Try capturing a different window first</li>
                    <li>Restart the screen mirroring application</li>
                </ul>
            </li>
        </ul>
        
        <h4>🔍 OCR Processing Issues</h4>
        <ul>
            <li><b>Problem:</b> Poor text recognition accuracy</li>
            <li><b>Solutions:</b>
                <ul>
                    <li>Ensure good image quality and lighting</li>
                    <li>Check that text is clearly visible and not blurry</li>
                    <li>Adjust device screen brightness</li>
                    <li>Try capturing when text is static (not scrolling)</li>
                </ul>
            </li>
        </ul>
        
        <h4>⚡ Auto-Capture Issues</h4>
        <ul>
            <li><b>Problem:</b> Auto-capture not working</li>
            <li><b>Solutions:</b>
                <ul>
                    <li>Ensure a window is selected before enabling auto-capture</li>
                    <li>Check that the interval is set to a reasonable value (≥5 seconds)</li>
                    <li>Verify the selected window remains visible</li>
                    <li>Monitor the status messages for error details</li>
                </ul>
            </li>
        </ul>
        
        <h3>🔍 Diagnostic Steps</h3>
        <ol>
            <li><b>Check Configuration:</b> Verify all settings in <code>.env</code> file</li>
            <li><b>Test API Connection:</b> Try a manual capture to test OCR functionality</li>
            <li><b>Verify Permissions:</b> Ensure the application has screen capture permissions</li>
            <li><b>Check File Paths:</b> Verify that screenshots and exports directories exist</li>
            <li><b>Review Logs:</b> Check console output for detailed error messages</li>
        </ol>
        
        <h3>📞 Getting Help</h3>
        <ul>
            <li><b>Error Messages:</b> Always read the full error message in the status area</li>
            <li><b>Log Files:</b> Check console output for detailed debugging information</li>
            <li><b>Configuration:</b> Verify all environment variables are properly set</li>
            <li><b>Dependencies:</b> Ensure all required packages are installed</li>
        </ul>
        """)
        
        layout.addWidget(content)
        widget.setLayout(layout)
        return widget
    
    def create_config_tab(self):
        """Create the configuration tab content"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>⚙️ Configuration Guide</h2>
        
        <h3>📄 Environment Configuration (.env file)</h3>
        <p>Create a <code>.env</code> file in the project root with the following settings:</p>
        
        <pre style="background: #2d2d2d; padding: 15px; border-radius: 8px; color: #f0f0f0;">
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
        </pre>
        
        <h3>🔑 Azure Computer Vision Setup</h3>
        <ol>
            <li><b>Create Azure Account:</b> Sign up at <a href="https://azure.microsoft.com">azure.microsoft.com</a></li>
            <li><b>Create Resource:</b> Create a new Computer Vision resource</li>
            <li><b>Get API Key:</b> Copy the API key from the resource's "Keys and Endpoint" section</li>
            <li><b>Get Endpoint:</b> Copy the endpoint URL from the same section</li>
            <li><b>Update .env:</b> Add your API key and endpoint to the .env file</li>
        </ol>
        
        <h3>📁 Directory Structure</h3>
        <pre style="background: #2d2d2d; padding: 15px; border-radius: 8px; color: #f0f0f0;">
project/
├── main.py                 # Main application file
├── config.py              # Configuration loader
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── screenshots/           # Captured images (auto-created)
├── exports/              # CSV and JSON exports (auto-created)
└── README.md             # Project documentation
        </pre>
        
        <h3>🔧 Advanced Configuration</h3>
        
        <h4>📸 Capture Settings</h4>
        <ul>
            <li><b>SCREENSHOTS_FOLDER:</b> Directory for storing captured images</li>
            <li><b>MAX_SCREENSHOTS_TO_KEEP:</b> Number of recent screenshots to retain</li>
            <li><b>AUTO_CAPTURE_INTERVAL:</b> Default interval for auto-capture (seconds)</li>
        </ul>
        
        <h4>🔍 OCR Settings</h4>
        <ul>
            <li><b>OCR_LANGUAGE:</b> Language code for text recognition (en, es, fr, etc.)</li>
            <li><b>DETECT_ORIENTATION:</b> Enable automatic text orientation detection</li>
        </ul>
        
        <h4>🎨 UI Settings</h4>
        <ul>
            <li><b>DEFAULT_THEME:</b> Starting theme (dark/light)</li>
            <li><b>ENABLE_ANIMATIONS:</b> Enable UI animations and transitions</li>
        </ul>
        
        <h3>🔒 Security Best Practices</h3>
        <ul>
            <li><b>Environment Variables:</b> Never commit API keys to version control</li>
            <li><b>.env File:</b> Add .env to your .gitignore file</li>
            <li><b>API Key Rotation:</b> Regularly rotate your Azure API keys</li>
            <li><b>Access Control:</b> Limit API key permissions to minimum required</li>
        </ul>
        
        <h3>📦 Dependencies Management</h3>
        <p>Install all required packages using:</p>
        <pre style="background: #2d2d2d; padding: 15px; border-radius: 8px; color: #f0f0f0;">
pip install -r requirements.txt
        </pre>
        
        <p>Key dependencies include:</p>
        <ul>
            <li><b>PyQt5:</b> GUI framework</li>
            <li><b>requests:</b> HTTP client for API calls</li>
            <li><b>Pillow:</b> Image processing</li>
            <li><b>python-dotenv:</b> Environment variable management</li>
            <li><b>qdarkstyle:</b> Modern dark theme</li>
            <li><b>qtawesome:</b> Icon library</li>
        </ul>
        """)
        
        layout.addWidget(content)
        widget.setLayout(layout)
        return widget
    def create_faq_tab(self):
        """Create the FAQ tab content"""
        widget = QWidget()
        layout = QVBoxLayout()

        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>❓ Frequently Asked Questions (FAQ)</h2>

        <h3>Application Crashes at Start</h3>
        <p><strong>Check:</strong> Ensure all environment variables are set. Verify the log for errors.</p>
        <h3>OCR Not Working</h3>
        <p><strong>Solution:</strong> Verify Azure API key and endpoint in the configuration.</p>
        <h3>Output is Garbled</h3>
        <p><strong>Hint:</strong> Check the language settings in the configuration tab.</p>

        <h3>How to Report Bugs?</h3>
        <p><strong>Guidance:</strong> Use the 'Report Issue' button in the menu or submit via <a href='https://github.com/username/repo/issues'>GitHub Issues</a>.</p>

        <h3>Need More Help?</h3>
        <p><strong>Suggestion:</strong> Refer to the 'Getting Help' tab for more troubleshooting steps.</p>
        """)

        layout.addWidget(content)
        widget.setLayout(layout)
        return widget

class USBStabilityManager:
    """
    USB Stability Management System
    
    This class provides comprehensive USB stability management to prevent
    USB disconnections during auto-capture operations. It implements:
    
    1. Intelligent file operation timing
    2. Reduced I/O operation frequency
    3. Graceful error handling
    4. Auto-recovery mechanisms
    5. Resource optimization
    """
    
    def __init__(self, parent_app):
        self.app = parent_app
        self.is_stable_mode = True  # Default to stable mode
        self.operation_delays = {
            'file_write': 0.2,
            'file_delete': 0.5,
            'cleanup': 1.0,
            'ocr_process': 0.3
        }
        self.max_concurrent_operations = 1
        self.current_operations = 0
        self.error_count = 0
        self.last_error_time = 0
        
    def enable_stability_mode(self):
        """Enable maximum USB stability mode"""
        self.is_stable_mode = True
        self.operation_delays = {
            'file_write': 0.3,
            'file_delete': 0.8,
            'cleanup': 2.0,
            'ocr_process': 0.5
        }
        self.max_concurrent_operations = 1
        print("DEBUG: USB Stability - Maximum stability mode enabled")
        
    def disable_stability_mode(self):
        """Disable USB stability mode for faster operations"""
        self.is_stable_mode = False
        self.operation_delays = {
            'file_write': 0.1,
            'file_delete': 0.2,
            'cleanup': 0.5,
            'ocr_process': 0.1
        }
        self.max_concurrent_operations = 3
        print("DEBUG: USB Stability - Fast mode enabled")
        
    def safe_file_operation(self, operation_type, operation_func, *args, **kwargs):
        """Safely execute file operations with USB stability considerations"""
        if self.current_operations >= self.max_concurrent_operations:
            print(f"DEBUG: USB Stability - Operation queued: {operation_type}")
            time.sleep(self.operation_delays.get(operation_type, 0.2))
            
        self.current_operations += 1
        
        try:
            # Add delay before operation
            if self.is_stable_mode:
                time.sleep(self.operation_delays.get(operation_type, 0.2))
            
            # Execute operation
            result = operation_func(*args, **kwargs)
            
            # Add delay after operation
            if self.is_stable_mode:
                time.sleep(self.operation_delays.get(operation_type, 0.2) * 0.5)
            
            self.error_count = 0  # Reset error count on success
            return result
            
        except Exception as e:
            self.error_count += 1
            self.last_error_time = time.time()
            print(f"DEBUG: USB Stability - Operation failed: {operation_type}, Error: {e}")
            
            # Auto-enable stability mode if errors occur
            if self.error_count >= 3:
                self.enable_stability_mode()
                self.app.update_status("🔌 Auto-enabled USB stability mode due to errors", "orange")
            
            raise e
            
        finally:
            self.current_operations = max(0, self.current_operations - 1)
            
    def safe_file_write(self, file_path, content, mode='w', encoding='utf-8'):
        """Safely write to file with USB stability"""
        def write_operation():
            with open(file_path, mode, encoding=encoding) as f:
                if isinstance(content, str):
                    f.write(content)
                else:
                    f.write(str(content))
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
                
        return self.safe_file_operation('file_write', write_operation)
        
    def safe_file_delete(self, file_path):
        """Safely delete file with USB stability"""
        def delete_operation():
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
            
        return self.safe_file_operation('file_delete', delete_operation)
        
    def safe_cleanup(self, cleanup_func, *args, **kwargs):
        """Safely perform cleanup operations"""
        return self.safe_file_operation('cleanup', cleanup_func, *args, **kwargs)
        
    def get_optimal_cleanup_frequency(self):
        """Get optimal cleanup frequency based on current stability mode"""
        if self.is_stable_mode:
            return 20  # Every 20 captures
        else:
            return 10  # Every 10 captures
            
    def should_skip_operation(self, operation_type):
        """Determine if an operation should be skipped for USB stability"""
        if not self.is_stable_mode:
            return False
            
        # Skip operations if there were recent errors
        if self.error_count > 0 and (time.time() - self.last_error_time) < 30:
            return True
            
        # Skip deletion operations in maximum stability mode
        if operation_type == 'file_delete' and self.is_stable_mode:
            return True
            
        return False
        
    def optimize_for_device(self, device_name):
        """Optimize settings for specific device types"""
        device_name = device_name.lower()
        
        if any(keyword in device_name for keyword in ['xiaomi', 'mi band', 'redmi']):
            # Xiaomi devices are more sensitive to USB operations
            self.enable_stability_mode()
            self.operation_delays['file_delete'] = 1.0
            print("DEBUG: USB Stability - Optimized for Xiaomi device")
            
        elif any(keyword in device_name for keyword in ['samsung', 'galaxy']):
            # Samsung devices are generally more stable
            self.operation_delays['file_delete'] = 0.3
            print("DEBUG: USB Stability - Optimized for Samsung device")
            
        elif any(keyword in device_name for keyword in ['scrcpy', 'android']):
            # Generic Android via scrcpy
            self.operation_delays['file_delete'] = 0.4
            print("DEBUG: USB Stability - Optimized for Android via scrcpy")
            
    def get_status_message(self):
        """Get current USB stability status message"""
        if self.is_stable_mode:
            return f"🔌 USB Stability Mode: ACTIVE (Errors: {self.error_count})"
        else:
            return f"⚡ Fast Mode: ACTIVE (Errors: {self.error_count})"


class SettingsDialog(QDialog):
    """Modern settings dialog with tabbed interface"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setWindowTitle("⚙️ Settings - Grace Biosensor Data Capture")
        self.setGeometry(150, 150, 800, 600)
        self.setModal(True)
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #2b2b2b, stop: 1 #1e1e1e);
                color: white;
            }
            QTabWidget::pane {
                border: 2px solid #555;
                background: #2d2d2d;
            }
            QTabBar::tab {
                background: #3a3a3a;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #00bcd4;
                color: white;
            }
            QTabBar::tab:hover {
                background: #4a4a4a;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the settings UI with tabs"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Performance monitoring tab
        self.performance_tab = self.create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "📊 Performance Metrics")
        
        # API testing tab
        self.api_tab = self.create_api_tab()
        self.tab_widget.addTab(self.api_tab, "🌐 API & Network Testing")
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #45a049, stop: 1 #3d8b40);
            }
        """)
        layout.addWidget(button_box)
    
    def create_performance_tab(self):
        """Create performance monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Performance metrics group
        metrics_group = QGroupBox("📊 Real-time Performance Metrics")
        metrics_layout = QVBoxLayout(metrics_group)
        
        # Performance metrics row 1
        perf_row1 = QHBoxLayout()
        
        # Total captures
        self.total_captures_label = QLabel("📸 Total Captures: 0")
        self.total_captures_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_captures_label.setStyleSheet("color: #2196F3; padding: 10px; border: 1px solid #555; border-radius: 4px;")
        perf_row1.addWidget(self.total_captures_label)
        
        # Total processing time
        self.total_time_label = QLabel("⏱️ Total Processing: 0.0s")
        self.total_time_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_time_label.setStyleSheet("color: #FF9800; padding: 10px; border: 1px solid #555; border-radius: 4px;")
        perf_row1.addWidget(self.total_time_label)
        
        metrics_layout.addLayout(perf_row1)
        
        # Performance metrics row 2
        perf_row2 = QHBoxLayout()
        
        # Average processing time
        self.avg_time_label = QLabel("⚡ Avg Processing: 0.0s")
        self.avg_time_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.avg_time_label.setStyleSheet("color: #4CAF50; padding: 10px; border: 1px solid #555; border-radius: 4px;")
        perf_row2.addWidget(self.avg_time_label)
        
        # Session uptime
        self.uptime_label = QLabel("🕐 Session Uptime: 0:00:00")
        self.uptime_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.uptime_label.setStyleSheet("color: #607D8B; padding: 10px; border: 1px solid #555; border-radius: 4px;")
        perf_row2.addWidget(self.uptime_label)
        
        metrics_layout.addLayout(perf_row2)
        
        # Reset stats button
        self.reset_stats_btn = QPushButton("🔄 Reset Performance Statistics")
        self.reset_stats_btn.clicked.connect(self.reset_performance_stats)
        self.reset_stats_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #795548, stop: 1 #5D4037);
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5D4037, stop: 1 #4E342E);
            }
        """)
        metrics_layout.addWidget(self.reset_stats_btn)
        
        layout.addWidget(metrics_group)
        layout.addStretch()
        
        return widget
    
    def create_api_tab(self):
        """Create comprehensive API and network testing tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # API Key Status Group (simplified)
        api_status_group = QGroupBox("🔑 API Configuration")
        api_status_layout = QVBoxLayout(api_status_group)
        
        # Simple API status label
        self.api_config_label = QLabel("✅ API configured and ready for OCR processing")
        self.api_config_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.api_config_label.setStyleSheet("color: #4CAF50; padding: 12px; border: 2px solid #4CAF50; border-radius: 6px;")
        api_status_layout.addWidget(self.api_config_label)
        
        layout.addWidget(api_status_group)
        
        # Network Testing Group
        network_group = QGroupBox("🌐 Network & Connectivity")
        network_layout = QVBoxLayout(network_group)
        
        # Network status row
        network_row = QHBoxLayout()
        
        # Internet connectivity
        self.internet_status_label = QLabel("📶 Internet: Checking...")
        self.internet_status_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.internet_status_label.setStyleSheet("color: #FF9800; padding: 8px; border: 1px solid #555; border-radius: 4px;")
        network_row.addWidget(self.internet_status_label)
        
        # Ping latency
        self.ping_latency_label = QLabel("📡 Ping: Not tested")
        self.ping_latency_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.ping_latency_label.setStyleSheet("color: #9C27B0; padding: 8px; border: 1px solid #555; border-radius: 4px;")
        network_row.addWidget(self.ping_latency_label)
        
        network_layout.addLayout(network_row)
        
        # Test network button
        self.network_test_btn = QPushButton("📡 Test Network Connection")
        self.network_test_btn.clicked.connect(self.test_network_connection)
        self.network_test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #673AB7, stop: 1 #512DA8);
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #512DA8, stop: 1 #4527A0);
            }
        """)
        network_layout.addWidget(self.network_test_btn)
        
        layout.addWidget(network_group)
        
        # OCR Testing Group
        ocr_test_group = QGroupBox("🔍 OCR Processing Testing")
        ocr_test_layout = QVBoxLayout(ocr_test_group)
        
        # OCR processing estimate
        self.ocr_estimate_label = QLabel("🔍 OCR Estimate: Click test to check")
        self.ocr_estimate_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.ocr_estimate_label.setStyleSheet("color: #4CAF50; padding: 10px; border: 2px solid #555; border-radius: 6px;")
        ocr_test_layout.addWidget(self.ocr_estimate_label)
        
        # Test OCR processing button
        self.ocr_test_btn = QPushButton("🔍 Test OCR Processing Speed")
        self.ocr_test_btn.clicked.connect(self.test_ocr_processing)
        self.ocr_test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4CAF50, stop: 1 #388E3C);
                color: white;
                border: none;
                padding: 12px 20px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #388E3C, stop: 1 #2E7D32);
            }
            QPushButton:disabled {
                background: #666;
                color: #999;
            }
        """)
        ocr_test_layout.addWidget(self.ocr_test_btn)
        
        layout.addWidget(ocr_test_group)
        
        # Initialize status checks
        self.check_network_status()
        
        layout.addStretch()
        return widget
    
    
    # Removed the update_api_status and test_api_latency methods
    
    def test_network_connection(self):
        """Test network connection and ping latency"""
        if self.parent_app:
            self.parent_app.test_network_connection_from_settings(self)
    
    def test_ocr_processing(self):
        """Test OCR processing time estimation"""
        if self.parent_app:
            self.parent_app.test_ocr_processing_from_settings(self)
    
    def check_network_status(self):
        """Check initial network connectivity status"""
        if self.parent_app:
            self.parent_app.check_network_status_from_settings(self)
    
    def reset_performance_stats(self):
        """Reset performance statistics"""
        if self.parent_app:
            self.parent_app.reset_performance_stats()
    
    def update_performance_display(self):
        """Update performance metrics display"""
        if self.parent_app:
            # Update total captures
            self.total_captures_label.setText(f"📸 Total Captures: {self.parent_app.total_captures}")
            
            # Update total processing time
            self.total_time_label.setText(f"⏱️ Total Processing: {self.parent_app.total_processing_time:.2f}s")
            
            # Update average processing time
            if self.parent_app.total_captures > 0:
                avg_time = self.parent_app.total_processing_time / self.parent_app.total_captures
                self.avg_time_label.setText(f"⚡ Avg Processing: {avg_time:.2f}s")
            else:
                self.avg_time_label.setText("⚡ Avg Processing: 0.0s")
            
            # Update session uptime
            uptime_seconds = int(time.time() - self.parent_app.session_start_time)
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            seconds = uptime_seconds % 60
            self.uptime_label.setText(f"🕐 Session Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def update_api_latency_display(self, latency_text):
        """Update API latency display"""
        self.api_latency_label.setText(latency_text)
    
    def update_api_history(self, history_text):
        """Update API test history"""
        self.test_history_label.setText(history_text)
    
    def set_api_test_button_state(self, enabled, text="🧪 Test API Latency"):
        """Set API test button state"""
        self.api_test_btn.setEnabled(enabled)
        self.api_test_btn.setText(text)
    
    def update_status(self, message: str, color: str = "black"):
        """Update status for this dialog - placeholder method"""
        # This method is required by some of the parent app methods
        # For now, we'll just pass since we don't have a status label in settings
        pass


from rich.console import Console
from rich.syntax import Syntax
import pyperclip

class OutputDetailsDialog(QDialog):
    """Dialog to show detailed OCR output in a resizable window"""

    def __init__(self, parent=None, raw_text="", ocr_result=None):
        super().__init__(parent)
        self.setWindowTitle("Output Details")
        self.setGeometry(300, 150, 1000, 800)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Tabs for different outputs
        tabs = QTabWidget()

        # Raw Text Tab
        raw_text_tab = QWidget()
        raw_text_layout = QVBoxLayout(raw_text_tab)
        self.raw_text_edit = QTextEdit()
        self.raw_text_edit.setReadOnly(True)
        self.raw_text_edit.setText(raw_text)
        raw_text_layout.addWidget(self.raw_text_edit)
        tabs.addTab(raw_text_tab, "Raw Text")

        # JSON Tab
        json_tab = QWidget()
        json_layout = QVBoxLayout(json_tab)
        self.json_edit = QTextEdit()
        self.json_edit.setReadOnly(True)
        console = Console()

        # Apply rich formatting to raw text
        syntax_raw = Syntax(raw_text, "text", theme="monokai", line_numbers=True)
        console.print(syntax_raw)

        # Apply rich formatting to JSON
        formatted_json = json.dumps(ocr_result, indent=2, ensure_ascii=False)
        syntax_json = Syntax(formatted_json, "json", theme="monokai", line_numbers=True)
        console.print(syntax_json)

        self.json_edit.setText(formatted_json)
        json_layout.addWidget(self.json_edit)

        # Copy buttons
        copy_raw_btn = QPushButton("Copy Raw Text")
        copy_raw_btn.clicked.connect(lambda: pyperclip.copy(raw_text))
        raw_text_layout.addWidget(copy_raw_btn)

        copy_json_btn = QPushButton("Copy JSON")
        copy_json_btn.clicked.connect(lambda: pyperclip.copy(formatted_json))
        json_layout.addWidget(copy_json_btn)
        tabs.addTab(json_tab, "JSON")

        layout.addWidget(tabs)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def update_contents(self, raw_text, ocr_result):
        """Update dialog contents with new results"""
        # Update the text areas
        self.raw_text_edit.setText(raw_text if raw_text.strip() else "No text detected")
        formatted_json = json.dumps(ocr_result, indent=2, ensure_ascii=False)
        self.json_edit.setText(formatted_json)


class BiosensorApp(QMainWindow):
    """
    Grace Biosensor Data Capture - Cross-Platform Main Application Class
    
    A comprehensive PyQt5-based application for capturing and analyzing biosensor data
    through automated screen capture and OCR processing. Supports Windows, macOS, and Linux
    with platform-specific optimizations and fallback mechanisms.
    
    🌟 Core Features:
    • Cross-platform window detection and management (PyWinCtl/pygetwindow)
    • Multi-method screenshot capture (dxcam, mss, pyautogui, scrot)
    • Azure Computer Vision OCR integration
    • Real-time device discovery and categorization
    • Automated capture with configurable intervals
    • CSV and JSON data export capabilities
    • Modern UI with dark/light theme support
    • Zoom functionality and accessibility features
    • Platform-specific error handling and diagnostics
    
    🔧 Platform Support:
    • Windows 10/11: Full feature support with dxcam acceleration
    • macOS 10.14+: PyObjC-based window management
    • Linux (X11): xdotool, wmctrl, and scrot integration
    
    📦 Dependencies:
    • Core: PyQt5, requests, Pillow, pyautogui, mss
    • Cross-platform: PyWinCtl (primary), pygetwindow (fallback)
    • Windows-specific: pywin32, dxcam (optional)
    • Linux-specific: python3-xlib, system tools (xdotool, wmctrl, scrot)
    • macOS-specific: pyobjc, pyobjc-frameworks
    
    🎨 UI Features:
    • Modern dark/light theme switching
    • Responsive layout with zoom support
    • Real-time status updates and progress indicators
    • Tabbed interface for organized functionality
    • Comprehensive help and documentation system
    
    🔄 Auto-Detection:
    • Automatic device discovery every 2 seconds
    • Window refresh every 3 seconds
    • Platform-specific window filtering
    • Smart categorization (phones, tablets, emulators, dev tools)
    
    📊 Data Management:
    • Automatic screenshot organization
    • Configurable data retention
    • Multiple export formats (CSV, JSON)
    • Timestamp-based file naming
    
    🛡️ Error Handling:
    • Graceful degradation for missing dependencies
    • Platform-specific error messages
    • Comprehensive logging and diagnostics
    • User-friendly error reporting
    
    Attributes:
        is_dark_theme (bool): Current theme state (True for dark, False for light)
        zoom_level (float): Current UI zoom level (0.5 to 2.0)
        screenshots_dir (str): Directory for storing captured screenshots
        auto_timer (QTimer): Timer for automated capture intervals
        refresh_timer (QTimer): Timer for window list refresh
        device_detection_timer (QTimer): Timer for device discovery
        last_device_count (int): Cache for device count change detection
        ocr_worker (OCRWorker): Background thread for OCR processing
        azure_api_key (str): Azure Computer Vision API key
        azure_endpoint (str): Azure Computer Vision endpoint URL
        last_ocr_result (dict): Cache of most recent OCR result for export
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔬 Grace Biosensor Data Capture - Professional Edition")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application icon
        self.set_app_icon()
        
        # Theme management
        self.is_dark_theme = True  # Start with dark theme
        
        # Zoom management
        self.zoom_level = 1.0  # Start with 100% zoom
        
        # Apply modern styling
        self.apply_modern_styling()
        
        # Create main storage directories
        self.screenshots_dir = os.path.join(SCREENSHOTS_FOLDER, "images")
        self.json_dir = os.path.join(SCREENSHOTS_FOLDER, "json")
        self.csv_dir = os.path.join(SCREENSHOTS_FOLDER, "csv")
        
        # Create directories if they do not exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.csv_dir, exist_ok=True)
        
        # Timer for auto-capture
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.auto_capture)
        
        # Timer for auto-refresh (detect new devices) - NOT started by default
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_windows)
        # self.refresh_timer.start(3000)  # Auto-refresh disabled by default
        
        # Timer for automatic device detection and UI updates - NOT started by default
        self.device_detection_timer = QTimer()
        self.device_detection_timer.timeout.connect(self.auto_detect_devices)
        # self.device_detection_timer.start(2000)  # Device detection disabled by default
        
        # Store last known device count for change detection
        self.last_device_count = 0
        
        # OCR worker thread
        self.ocr_worker = None
        
        # Navigation Alert System
        self.task_queue = []
        self.current_task = None
        self.task_progress = 0
        
        # Azure OCR settings from config
        self.azure_api_key = AZURE_API_KEY
        self.azure_endpoint = AZURE_ENDPOINT
        
        # Store last OCR result for manual export
        self.last_ocr_result = None
        
        # Performance tracking variables
        self.auto_capture_times = []  # List of processing times for auto captures
        self.manual_capture_times = []  # List of processing times for manual captures
        self.api_latency_times = []  # List of API response times
        self.total_captures = 0
        self.auto_captures = 0
        self.manual_captures = 0
        self.total_processing_time = 0.0
        self.auto_processing_time = 0.0
        self.manual_processing_time = 0.0
        self.session_start_time = time.time()
        self.last_capture_time = None
        self.last_api_time = None
        
        # Real-time performance updates timer
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance_displays)
        self.performance_timer.start(1000)  # Update every second
        
        # USB Stability Configuration
        # Load from config, but default to False for USB stability
        self.enable_auto_delete_screenshots = ENABLE_AUTO_DELETE_SCREENSHOTS
        
        # Initialize cleanup counter for reduced frequency operations
        self._cleanup_counter = 0
        
        # USB Stability Management System
        self.usb_stability_manager = USBStabilityManager(self)
        
        self.init_ui()
    
    def set_app_icon(self):
        """Set the application icon"""
        try:
            # Check if app_icon.png exists in the current directory
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
            
            if os.path.exists(icon_path):
                # Set the window icon
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
                
                # Set the application icon (for taskbar, etc.)
                QApplication.instance().setWindowIcon(icon)
                
                print(f"✅ App icon loaded successfully: {icon_path}")
            else:
                print(f"⚠️ App icon not found at: {icon_path}")
                print("📝 Using default system icon")
                
        except Exception as e:
            print(f"❌ Error loading app icon: {str(e)}")
            print("📝 Using default system icon")
    
    def apply_modern_styling(self):
        """Apply modern professional styling to the application"""
        if MODERN_UI_AVAILABLE:
            # Apply dark theme
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        # Custom modern styling
        modern_style = """
        QMainWindow {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #2b2b2b, stop: 1 #1e1e1e);
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 10px;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #3a3a3a, stop: 1 #2d2d2d);
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #00bcd4;
        }
        
        QPushButton {
            border: none;
            padding: 12px 24px;
            font-size: 13px;
            font-weight: bold;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #4a4a4a, stop: 1 #3a3a3a);
        }
        
        QComboBox {
            border: 2px solid #555;
            border-radius: 6px;
            padding: 8px;
            background: #3a3a3a;
            selection-background-color: #00bcd4;
        }
        
        QTextEdit {
            border: 2px solid #555;
            border-radius: 6px;
            background: #2d2d2d;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        
        QProgressBar {
            border: 2px solid #555;
            border-radius: 6px;
            text-align: center;
            background: #2d2d2d;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 #00bcd4, stop: 1 #4caf50);
            border-radius: 4px;
        }
        
        QLabel {
            color: #ffffff;
        }
        
        QCheckBox {
            spacing: 8px;
            color: #ffffff;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 3px;
            border: 2px solid #555;
        }
        
        QCheckBox::indicator:checked {
            background: #00bcd4;
            border: 2px solid #00bcd4;
        }
        
        QSpinBox {
            border: 2px solid #555;
            border-radius: 6px;
            padding: 6px;
            background: #3a3a3a;
        }
        """
        
        self.setStyleSheet(self.styleSheet() + modern_style)
    
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        self.is_dark_theme = not self.is_dark_theme
        
        if self.is_dark_theme:
            # Switch to dark theme
            self.theme_toggle_btn.setText("☀️ Light Mode")
            if MODERN_UI_AVAILABLE:
                self.theme_toggle_btn.setIcon(qta.icon('fa5s.sun', color='#ffa726'))
            self.apply_modern_styling()
            self.update_status("🌙 Switched to Dark Theme", "blue")
        else:
            # Switch to light theme
            self.theme_toggle_btn.setText("🌙 Dark Mode")
            if MODERN_UI_AVAILABLE:
                self.theme_toggle_btn.setIcon(qta.icon('fa5s.moon', color='#424242'))
            self.apply_light_theme()
            self.update_status("☀️ Switched to Light Theme", "blue")
    
    def apply_light_theme(self):
        """Apply light theme styling"""
        light_style = """
        QMainWindow {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f5f5f5, stop: 1 #e0e0e0);
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #bbb;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 10px;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #ffffff, stop: 1 #f0f0f0);
            color: #333;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #1976d2;
        }
        
        QComboBox {
            border: 2px solid #bbb;
            border-radius: 6px;
            padding: 8px;
            background: #ffffff;
            color: #333;
            selection-background-color: #1976d2;
        }
        
        QTextEdit {
            border: 2px solid #bbb;
            border-radius: 6px;
            background: #ffffff;
            color: #333;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        
        QProgressBar {
            border: 2px solid #bbb;
            border-radius: 6px;
            text-align: center;
            background: #f0f0f0;
            color: #333;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 #1976d2, stop: 1 #4caf50);
            border-radius: 4px;
        }
        
        QLabel {
            color: #333;
        }
        
        QCheckBox {
            spacing: 8px;
            color: #333;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 3px;
            border: 2px solid #bbb;
            background: #ffffff;
        }
        
        QCheckBox::indicator:checked {
            background: #1976d2;
            border: 2px solid #1976d2;
        }
        
        QSpinBox {
            border: 2px solid #bbb;
            border-radius: 6px;
            padding: 6px;
            background: #ffffff;
            color: #333;
        }
        """
        
        self.setStyleSheet(light_style)
    
    def show_help_dialog(self):
        """Show comprehensive help and documentation dialog"""
        help_dialog = HelpDocumentationDialog(self)
        help_dialog.exec_()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header with title, zoom controls, and buttons
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("🔬 Biosensor Data Capture - Professional Edition")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #00bcd4; padding: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(5)
        
        zoom_out_btn = QPushButton("🔍-")
        zoom_out_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ff9a9e, stop:1 #fecfef);
                color: #2d3748;
                border: none;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ff8a80, stop:1 #fbb6ce);
            }
        """)
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 10px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                min-width: 40px;
                text-align: center;
            }
        """)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        zoom_layout.addWidget(self.zoom_label)
        
        zoom_in_btn = QPushButton("🔍+")
        zoom_in_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #a8edea, stop:1 #fed6e3);
                color: #2d3748;
                border: none;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 40px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #81e6d9, stop:1 #fbb6ce);
            }
        """)
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)
        
        header_layout.addLayout(zoom_layout)
        
        # Developer website link
        dev_link_btn = QPushButton("🌐 Developer")
        dev_link_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #667eea, stop: 1 #764ba2);
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5a67d8, stop: 1 #6b46c1);
            }
        """)
        dev_link_btn.clicked.connect(self.open_developer_website)
        header_layout.addWidget(dev_link_btn)
        
        # Theme toggle button
        self.theme_toggle_btn = QPushButton()
        self.is_dark_theme = True  # Start with dark theme
        if MODERN_UI_AVAILABLE:
            self.theme_toggle_btn.setIcon(qta.icon('fa5s.sun', color='#ffa726'))
        self.theme_toggle_btn.setText("☀️ Light Mode")
        self.theme_toggle_btn.setToolTip("Switch between Dark and Light themes")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.theme_toggle_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffa726, stop: 1 #ff9800);
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ff9800, stop: 1 #f57c00);
            }
        """)
        header_layout.addWidget(self.theme_toggle_btn)
        
        # Help button
        self.help_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.help_btn.setIcon(qta.icon('fa5s.question-circle', color='white'))
        self.help_btn.setText("❓ Help")
        self.help_btn.setToolTip("Show application documentation and usage guide")
        self.help_btn.clicked.connect(self.show_help_dialog)
        self.help_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #9c27b0, stop: 1 #7b1fa2);
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #7b1fa2, stop: 1 #6a1b9a);
            }
        """)
        header_layout.addWidget(self.help_btn)
        
        # Settings gear button
        self.settings_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.settings_btn.setIcon(qta.icon('fa5s.cog', color='white'))
        self.settings_btn.setText("⚙️ Settings")
        self.settings_btn.setToolTip("Open settings for performance, API, capture, and USB")
        self.settings_btn.clicked.connect(self.open_settings_dialog)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #607D8B, stop: 1 #455A64);
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #455A64, stop: 1 #37474F);
            }
        """)
        header_layout.addWidget(self.settings_btn)
        
        main_layout.addLayout(header_layout)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #555;")
        main_layout.addWidget(separator)
        
        # Window Selection panel
        window_group = QGroupBox("Window Selection")
        window_layout = QVBoxLayout(window_group)
        
        # Window selection row
        window_select_layout = QHBoxLayout()
        
        window_select_layout.addWidget(QLabel("Select Window:"))
        
        self.window_combo = QComboBox()
        self.window_combo.setMinimumWidth(300)
        window_select_layout.addWidget(self.window_combo)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.manual_refresh_windows)
        self.refresh_btn.setToolTip("Click to manually scan for new devices and windows")
        window_select_layout.addWidget(self.refresh_btn)
        
        # Auto-scan toggle button
        self.auto_scan_btn = QPushButton("🔄 Auto-Scan: OFF")
        self.auto_scan_btn.setCheckable(True)
        self.auto_scan_btn.clicked.connect(self.toggle_auto_scan)
        self.auto_scan_btn.setToolTip("Enable/disable automatic device scanning")
        self.auto_scan_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #9E9E9E, stop: 1 #757575);
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #757575, stop: 1 #616161);
            }
            QPushButton:checked {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4CAF50, stop: 1 #388E3C);
            }
            QPushButton:checked:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #388E3C, stop: 1 #2E7D32);
            }
        """)
        window_select_layout.addWidget(self.auto_scan_btn)
        
        window_layout.addLayout(window_select_layout)
        main_layout.addWidget(window_group)
        
        # Control panel
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout(control_group)
        
        # Main controls row
        main_controls = QHBoxLayout()
        
        # Background capture button with modern styling (main method)
        self.background_capture_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.background_capture_btn.setIcon(qta.icon('fa5s.camera', color='white'))
        self.background_capture_btn.setText("📸 Smart Background Capture")
        self.background_capture_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #2196F3, stop: 1 #1976D2);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1976D2, stop: 1 #1565C0);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1565C0, stop: 1 #0D47A1);
            }
        """)
        self.background_capture_btn.clicked.connect(self.capture_background_window)
        self.background_capture_btn.setToolTip("Captures the selected window without bringing it to foreground - No interruption to your workflow!")
        main_controls.addWidget(self.background_capture_btn)
        
        # Traditional capture button (fallback method)
        self.capture_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.capture_btn.setIcon(qta.icon('fa5s.camera', color='white'))
        self.capture_btn.setText("📸 Traditional Capture")
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #45a049, stop: 1 #3d8b40);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #3d8b40, stop: 1 #2e7d32);
            }
        """)
        self.capture_btn.clicked.connect(self.capture_selected_window)
        self.capture_btn.setToolTip("Activates the window first, then captures - May interrupt your workflow")
        main_controls.addWidget(self.capture_btn)
        
        # Background service button removed to prevent unwanted captures
        
        control_layout.addLayout(main_controls)
        
        # Auto-capture settings
        auto_layout = QHBoxLayout()
        
        self.auto_checkbox = QCheckBox("Auto-capture every")
        self.auto_checkbox.stateChanged.connect(self.toggle_auto_capture)
        auto_layout.addWidget(self.auto_checkbox)
        
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(10, 300)
        self.interval_spinbox.setValue(DEFAULT_CAPTURE_INTERVAL)
        self.interval_spinbox.setSuffix(" seconds")
        self.interval_spinbox.valueChanged.connect(self.update_capture_interval)
        auto_layout.addWidget(self.interval_spinbox)
        
        # Stop auto-capture button with modern styling
        self.stop_auto_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.stop_auto_btn.setIcon(qta.icon('fa5s.stop', color='white'))
        self.stop_auto_btn.setText("⏹️ Stop Auto-Capture")
        self.stop_auto_btn.clicked.connect(self.stop_auto_capture)
        self.stop_auto_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ff5722, stop: 1 #e64a19);
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e64a19, stop: 1 #d84315);
            }
            QPushButton:disabled {
                background: #666;
                color: #999;
            }
        """)
        self.stop_auto_btn.setEnabled(False)  # Initially disabled
        auto_layout.addWidget(self.stop_auto_btn)
        
        auto_layout.addStretch()
        control_layout.addLayout(auto_layout)
        
        # USB Stability configuration with custom time interval
        usb_stability_layout = QHBoxLayout()
        
        self.usb_stability_checkbox = QCheckBox("🔌 Enable screenshot auto-deletion (may cause USB disconnects)")
        self.usb_stability_checkbox.setChecked(self.enable_auto_delete_screenshots)
        self.usb_stability_checkbox.stateChanged.connect(self.toggle_usb_stability)
        self.usb_stability_checkbox.setToolTip("Disable this to prevent USB disconnection issues during auto-capture")
        usb_stability_layout.addWidget(self.usb_stability_checkbox)
        
        # Custom time interval selector for screenshot deletion
        deletion_interval_label = QLabel("Delete screenshots older than:")
        deletion_interval_label.setToolTip("Set custom time interval for automatic screenshot deletion")
        usb_stability_layout.addWidget(deletion_interval_label)
        
        self.deletion_interval_spinbox = QSpinBox()
        self.deletion_interval_spinbox.setRange(1, 1440)  # 1 minute to 24 hours
        self.deletion_interval_spinbox.setValue(60)  # Default to 60 minutes
        self.deletion_interval_spinbox.setSuffix(" minutes")
        self.deletion_interval_spinbox.setToolTip("Screenshots older than this time will be automatically deleted")
        usb_stability_layout.addWidget(self.deletion_interval_spinbox)
        
        # Custom deletion mode selector
        self.deletion_mode_combo = QComboBox()
        self.deletion_mode_combo.addItem("🕐 By Time (minutes)", "time")
        self.deletion_mode_combo.addItem("📁 By Count (keep last N)", "count")
        self.deletion_mode_combo.setCurrentIndex(0)  # Default to time-based
        self.deletion_mode_combo.currentTextChanged.connect(self.update_deletion_mode)
        self.deletion_mode_combo.setToolTip("Choose deletion method: by time or by count")
        usb_stability_layout.addWidget(self.deletion_mode_combo)
        
        # USB Stability Mode Toggle Button
        self.usb_stability_btn = QPushButton("🔌 Max USB Stability")
        self.usb_stability_btn.setCheckable(True)
        self.usb_stability_btn.setChecked(True)  # Start in stability mode
        self.usb_stability_btn.clicked.connect(self.toggle_usb_stability_mode)
        self.usb_stability_btn.setToolTip("Toggle between maximum USB stability and fast mode")
        self.usb_stability_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #45a049, stop: 1 #3d8b40);
            }
            QPushButton:checked {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #FF9800, stop: 1 #F57C00);
            }
        """)
        usb_stability_layout.addWidget(self.usb_stability_btn)
        
        usb_stability_layout.addStretch()
        control_layout.addLayout(usb_stability_layout)
        
        # Note about auto-capture
        auto_note = QLabel("Note: Auto-capture will use the currently selected window")
        auto_note.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
        control_layout.addWidget(auto_note)
        
        # USB stability note
        usb_note = QLabel("💡 Tip: If experiencing USB disconnects, disable screenshot auto-deletion above")
        usb_note.setStyleSheet("color: #FFA726; font-style: italic; font-size: 10px;")
        control_layout.addWidget(usb_note)
        
        # Background service note removed
        main_layout.addWidget(control_group)
        
        # Status and Navigation Alert System
        status_group = QGroupBox("Status & Task Queue")
        status_layout = QVBoxLayout(status_group)
        
        # Current status
        self.status_label = QLabel("🟡 Ready to capture")
        self.status_label.setFont(QFont("Arial", 12))
        status_layout.addWidget(self.status_label)
        
        # Task queue display
        self.task_queue_label = QLabel("📋 Task Queue: Empty")
        self.task_queue_label.setFont(QFont("Arial", 10))
        self.task_queue_label.setStyleSheet("color: #666; font-style: italic;")
        status_layout.addWidget(self.task_queue_label)
        
        # Gradient progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 8px;
                text-align: center;
                background: #2d2d2d;
                font-size: 12px;
                font-weight: bold;
                color: white;
                min-height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #667eea, stop: 0.25 #764ba2, stop: 0.5 #f093fb, 
                    stop: 0.75 #f5576c, stop: 1 #4facfe);
                border-radius: 6px;
                margin: 1px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        # Task completion indicator
        self.completion_label = QLabel("")
        self.completion_label.setFont(QFont("Arial", 10))
        self.completion_label.setAlignment(Qt.AlignCenter)
        self.completion_label.setVisible(False)
        status_layout.addWidget(self.completion_label)
        
        main_layout.addWidget(status_group)
        
        # Settings notification
        settings_notice = QLabel("⚙️ Performance metrics, API testing, and advanced settings moved to Settings button")

        # Fix font: make it italic properly
        font = QFont("Arial", 10)
        font.setItalic(True)
        settings_notice.setFont(font)

        # Fix style: 'text-align' and 'box-shadow' are not valid in Qt stylesheets
        settings_notice.setStyleSheet("color: #888; padding: 8px;")  # Removed 'text-align'
        settings_notice.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(settings_notice)

        
        # Results section - Minimal display
        results_group = QGroupBox("OCR Results Preview")
        results_layout = QVBoxLayout(results_group)
        
        # Status display for last OCR result
        self.ocr_status_label = QLabel("No OCR results yet. Capture a window to see results.")
        self.ocr_status_label.setFont(QFont("Arial", 11))
        self.ocr_status_label.setStyleSheet("""
            QLabel {
                color: #888;
                padding: 20px;
                text-align: center;
                background: rgba(255, 255, 255, 0.05);
                border: 2px dashed #555;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        self.ocr_status_label.setAlignment(Qt.AlignCenter)
        results_layout.addWidget(self.ocr_status_label)
        
        # Quick stats display
        self.quick_stats_label = QLabel("")
        self.quick_stats_label.setFont(QFont("Arial", 10))
        self.quick_stats_label.setStyleSheet("color: #4CAF50; padding: 5px;")
        self.quick_stats_label.setAlignment(Qt.AlignCenter)
        results_layout.addWidget(self.quick_stats_label)
        
        main_layout.addWidget(results_group)
        
        # Control buttons layout
        buttons_layout = QHBoxLayout()
        
        # Clear button with modern styling
        clear_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            clear_btn.setIcon(qta.icon('fa5s.trash', color='white'))
        clear_btn.setText("🗑️ Clear Results")
        clear_btn.clicked.connect(self.clear_results)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f44336, stop: 1 #d32f2f);
                color: white;
                border: none;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #d32f2f, stop: 1 #c62828);
            }
        """)
        buttons_layout.addWidget(clear_btn)
        
        # CSV Export button with modern styling
        self.csv_export_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.csv_export_btn.setIcon(qta.icon('fa5s.file-csv', color='white'))
        self.csv_export_btn.setText("📊 Export to CSV")
        self.csv_export_btn.clicked.connect(self.export_last_result_to_csv)
        self.csv_export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #2196F3, stop: 1 #1976D2);
                color: white;
                border: none;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1976D2, stop: 1 #1565C0);
            }
            QPushButton:disabled {
                background: #666;
                color: #999;
            }
        """)
        self.csv_export_btn.setEnabled(False)  # Initially disabled
        buttons_layout.addWidget(self.csv_export_btn)
        
        # JSON Export button with modern styling
        self.json_export_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.json_export_btn.setIcon(qta.icon('fa5s.file-code', color='white'))
        self.json_export_btn.setText("📄 Export to JSON")
        self.json_export_btn.clicked.connect(self.export_last_result_to_json)
        self.json_export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ff9800, stop: 1 #f57c00);
                color: white;
                border: none;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f57c00, stop: 1 #ef6c00);
            }
            QPushButton:disabled {
                background: #666;
                color: #999;
            }
        """)
        self.json_export_btn.setEnabled(False)  # Initially disabled
        buttons_layout.addWidget(self.json_export_btn)
        
        # View Output Details button with modern styling
        self.view_details_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.view_details_btn.setIcon(qta.icon('fa5s.eye', color='white'))
        self.view_details_btn.setText("👁️ View Output Details")
        self.view_details_btn.clicked.connect(self.show_output_details_dialog)
        self.view_details_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #9c27b0, stop: 1 #7b1fa2);
                color: white;
                border: none;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #8e24aa, stop: 1 #6a1b9a);
            }
            QPushButton:disabled {
                background: #666;
                color: #999;
            }
        """)
        self.view_details_btn.setEnabled(False)  # Initially disabled
        buttons_layout.addWidget(self.view_details_btn)
        
        # Instant Device Display button with modern styling
        self.instant_device_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.instant_device_btn.setIcon(qta.icon('fa5s.mobile-alt', color='white'))
        self.instant_device_btn.setText("📱 Show ALL Devices NOW")
        self.instant_device_btn.clicked.connect(self.show_all_devices_instantly)
        self.instant_device_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #FF5722, stop: 1 #E64A19);
                color: white;
                border: none;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #E64A19, stop: 1 #D84315);
            }
        """)
        buttons_layout.addWidget(self.instant_device_btn)
        
        # Clear completed tasks button
        self.clear_tasks_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.clear_tasks_btn.setIcon(qta.icon('fa5s.broom', color='white'))
        self.clear_tasks_btn.setText("🧹 Clear Completed Tasks")
        self.clear_tasks_btn.clicked.connect(self.clear_completed_tasks)
        self.clear_tasks_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #9C27B0, stop: 1 #7B1FA2);
                color: white;
                border: none;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #7B1FA2, stop: 1 #6A1B9A);
            }
        """)
        buttons_layout.addWidget(self.clear_tasks_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Set the central widget
        self.setCentralWidget(central_widget)
        
        # Initialize window list after all UI elements are created
        # Don't automatically refresh - let user control this
        self.window_combo.addItem("🔍 Click 'Scan Devices' to start...")
        self.window_combo.setCurrentIndex(0)
        
        # Status message to show that auto-scan is disabled
        self.update_status("⏹️ Auto-scan disabled - click 'Refresh' to manually scan for devices", "orange")
        
        # Debug: Print timer status
        print("DEBUG: Timer status at startup:")
        print(f"  - Refresh timer active: {self.refresh_timer.isActive()}")
        print(f"  - Device detection timer active: {self.device_detection_timer.isActive()}")
        print(f"  - Auto capture timer active: {self.auto_timer.isActive()}")
    
    def manual_refresh_windows(self):
        """Manual refresh triggered by user clicking refresh button"""
        try:
            # Disable refresh button temporarily
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("🔄 Scanning...")
            
            # Force immediate refresh
            self.refresh_windows()
            
            # Re-enable button
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("🔄 Refresh")
            
        except Exception as e:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("🔄 Refresh")
            self.update_status(f"❌ Manual refresh failed: {str(e)}", "red")
    
    def toggle_auto_scan(self):
        """Toggle automatic device scanning on/off"""
        try:
            if self.auto_scan_btn.isChecked():
                # Start auto-scanning
                self.auto_scan_btn.setText("🔄 Auto-Scan: ON")
                self.refresh_timer.start(3000)  # Refresh every 3 seconds
                self.device_detection_timer.start(2000)  # Device detection every 2 seconds
                self.update_status("🔄 Auto-scan enabled - watching for new devices", "green")
            else:
                # Stop auto-scanning
                self.auto_scan_btn.setText("🔄 Auto-Scan: OFF")
                self.refresh_timer.stop()
                self.device_detection_timer.stop()
                self.update_status("⏹️ Auto-scan disabled - manual refresh only", "orange")
        except Exception as e:
            self.update_status(f"❌ Auto-scan toggle failed: {str(e)}", "red")
    
    def open_settings_dialog(self):
        """Open the settings dialog"""
        try:
            self.settings_dialog = SettingsDialog(self)
            
            # Start timer to update performance display in settings
            self.settings_update_timer = QTimer()
            self.settings_update_timer.timeout.connect(self.settings_dialog.update_performance_display)
            self.settings_update_timer.start(1000)  # Update every second
            
            result = self.settings_dialog.exec_()
            
            # Stop the timer when dialog is closed
            if hasattr(self, 'settings_update_timer'):
                self.settings_update_timer.stop()
            
            if result == QDialog.Accepted:
                self.update_status("⚙️ Settings updated successfully", "green")
                # Apply any settings changes here if needed
            
        except Exception as e:
            self.update_status(f"❌ Error opening settings: {str(e)}", "red")
    

    def test_network_connection_from_settings(self, settings_dialog):
        """Check network connection and ping to a well-known server"""
        try:
            import subprocess
            import platform
            
            # Use system ping command
            if platform.system().lower() == 'windows':
                result = subprocess.run(['ping', '-n', '4', '8.8.8.8'], capture_output=True, text=True, timeout=10)
            else:
                result = subprocess.run(['ping', '-c', '4', '8.8.8.8'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Extract average latency from ping output
                output_lines = result.stdout.lower()
                if 'average' in output_lines:
                    # Try to find average latency
                    import re
                    avg_match = re.search(r'average[\s=]*([0-9.]+)', output_lines)
                    if avg_match:
                        avg_latency = float(avg_match.group(1))
                        settings_dialog.ping_latency_label.setText(f"📡 Ping: {avg_latency:.1f} ms")
                        settings_dialog.ping_latency_label.setStyleSheet("color: #4CAF50; padding: 8px; border: 1px solid #4CAF50; border-radius: 4px;")
                        return
                
                # Fallback: just show success
                settings_dialog.ping_latency_label.setText("📡 Ping: Success")
                settings_dialog.ping_latency_label.setStyleSheet("color: #4CAF50; padding: 8px; border: 1px solid #4CAF50; border-radius: 4px;")
            else:
                settings_dialog.ping_latency_label.setText("❌ Ping: Failed")
                settings_dialog.ping_latency_label.setStyleSheet("color: #F44336; padding: 8px; border: 1px solid #F44336; border-radius: 4px;")
                
        except Exception as e:
            settings_dialog.ping_latency_label.setText(f"❌ Ping: Error")
            settings_dialog.ping_latency_label.setStyleSheet("color: #F44336; padding: 8px; border: 1px solid #F44336; border-radius: 4px;")

    def test_ocr_processing_from_settings(self, settings_dialog):
        """Estimate OCR processing time based on the current configuration"""
        try:
            if not self.azure_api_key or not self.azure_endpoint:
                settings_dialog.ocr_estimate_label.setText("❌ OCR Test: API credentials not configured")
                return
            
            # Simulate OCR processing by creating a larger test image
            test_image = Image.new('RGB', (100, 100), color='white')
            test_path = os.path.join(self.screenshots_dir, 'settings_ocr_test.png')
            test_image.save(test_path)
            
            start_time = time.time()
            
            # Create OCR worker for estimation
            self.settings_ocr_worker = OCRWorker(test_path, self.azure_api_key, self.azure_endpoint)
            self.settings_ocr_worker.finished.connect(lambda result: self.on_ocr_estimation_finished(result, settings_dialog, start_time))
            self.settings_ocr_worker.error.connect(lambda error: self.on_ocr_estimation_error(error, settings_dialog))
            self.settings_ocr_worker.start()
            
        except Exception as e:
            settings_dialog.ocr_estimate_label.setText(f"❌ OCR estimation failed: {str(e)}")

    def on_ocr_estimation_finished(self, result, settings_dialog, start_time):
        """Handle OCR processing estimation completion"""
        try:
            processing_time = time.time() - start_time
            settings_dialog.ocr_estimate_label.setText(f"🔍 OCR Estimate: {processing_time:.2f}s")
            settings_dialog.update_status(f"✅ OCR estimation: {processing_time:.2f}s", "green")
            
            # Clean up test image
            test_path = os.path.join(self.screenshots_dir, 'settings_ocr_test.png')
            if os.path.exists(test_path):
                os.remove(test_path)
        except Exception as e:
            settings_dialog.ocr_estimate_label.setText(f"❌ OCR estimate error: {str(e)}")

    def on_ocr_estimation_error(self, error_msg, settings_dialog):
        """Handle OCR processing estimation error"""
        settings_dialog.ocr_estimate_label.setText(f"❌ OCR test failed: {error_msg}")
        
        # Clean up test image
        test_path = os.path.join(self.screenshots_dir, 'settings_ocr_test.png')
        if os.path.exists(test_path):
            os.remove(test_path)

    def check_network_status_from_settings(self, settings_dialog):
        """Check initial network connectivity start up status"""
        try:
            import urllib.request
            urllib.request.urlopen('http://google.com', timeout=1)
            settings_dialog.internet_status_label.setText("📶 Internet: Connected")
            settings_dialog.internet_status_label.setStyleSheet("color: #4CAF50; padding: 8px; border: 1px solid #4CAF50; border-radius: 4px;")
        except Exception:
            settings_dialog.internet_status_label.setText("❌ Internet: Disconnected")
            settings_dialog.internet_status_label.setStyleSheet("color: #F44336; padding: 8px; border: 1px solid #F44336; border-radius: 4px;")
    
    def on_settings_latency_test_finished(self, result, settings_dialog, start_time):
        """Handle latency test completion from settings"""
        try:
            latency = time.time() - start_time
            self.api_latency_times.append(latency)
            
            # Keep only last 10 measurements
            if len(self.api_latency_times) > 10:
                self.api_latency_times = self.api_latency_times[-10:]
            
            settings_dialog.set_api_test_button_state(True)
            settings_dialog.update_api_latency_display(f"🌐 API Latency: {latency:.2f}s")
            
            # Update history
            avg_latency = sum(self.api_latency_times) / len(self.api_latency_times)
            settings_dialog.update_api_history(f"📈 Recent Tests: {len(self.api_latency_times)} tests, Avg: {avg_latency:.2f}s")
            
            # Clean up test image
            test_path = os.path.join(self.screenshots_dir, 'settings_api_test.png')
            if os.path.exists(test_path):
                os.remove(test_path)
                
        except Exception as e:
            settings_dialog.set_api_test_button_state(True)
            settings_dialog.update_api_latency_display(f"❌ Test error: {str(e)}")
    
    def on_settings_latency_test_error(self, error_msg, settings_dialog):
        """Handle latency test error from settings"""
        settings_dialog.set_api_test_button_state(True)
        settings_dialog.update_api_latency_display(f"❌ API test failed: {error_msg}")
        
        # Clean up test image
        test_path = os.path.join(self.screenshots_dir, 'settings_api_test.png')
        if os.path.exists(test_path):
            os.remove(test_path)
    
    def reset_performance_stats(self):
        """Reset all performance statistics"""
        try:
            self.auto_capture_times = []
            self.manual_capture_times = []
            self.api_latency_times = []
            self.total_captures = 0
            self.auto_captures = 0
            self.manual_captures = 0
            self.total_processing_time = 0.0
            self.auto_processing_time = 0.0
            self.manual_processing_time = 0.0
            self.session_start_time = time.time()
            self.last_capture_time = None
            self.last_api_time = None
            
            self.update_status("📊 Performance statistics reset", "blue")
            
        except Exception as e:
            self.update_status(f"❌ Error resetting stats: {str(e)}", "red")
    
    def update_performance_displays(self):
        """Update performance displays in real-time"""
        try:
            # Update any open settings dialogs
            for widget in QApplication.allWidgets():
                if isinstance(widget, SettingsDialog) and hasattr(widget, 'update_performance_display'):
                    widget.update_performance_display()
        except Exception as e:
            # Silently handle errors to avoid disrupting the UI
            pass
    
    def auto_refresh_windows(self):
        """Automatically refresh windows to detect new devices"""
        try:
            # Only auto-refresh if no capture is in progress
            if not hasattr(self, 'ocr_worker') or not self.ocr_worker or not self.ocr_worker.isRunning():
                current_count = self.window_combo.count()
                old_selection = self.window_combo.currentText() if self.window_combo.currentIndex() >= 0 else None
                
                # Get current window count for comparison
                new_windows = self.get_all_windows()
                
                # Only refresh if window count changed significantly
                if abs(len(new_windows) - (current_count - 4)) > 1:  # -4 for separators and placeholder
                    self.refresh_windows()
                    
                    # Try to restore selection if it was valid
                    if old_selection and old_selection not in ["🔍 Select a window to capture...", "❌ No windows found - Connect device and click Refresh"]:
                        for i in range(self.window_combo.count()):
                            if old_selection in self.window_combo.itemText(i):
                                self.window_combo.setCurrentIndex(i)
                                break
        except:
            pass  # Silently ignore auto-refresh errors
    
    def auto_detect_devices(self):
        """Automatically detect new devices and update UI when changes occur"""
        try:
            # Only run if no capture is in progress
            if hasattr(self, 'ocr_worker') and self.ocr_worker and self.ocr_worker.isRunning():
                return
            
            # Get current device information
            devices = self.discover_newer_devices()
            current_device_count = sum(len(category) for category in devices.values())
            
            # Check if device count changed
            if current_device_count != self.last_device_count:
                self.last_device_count = current_device_count
                
                # Update status with device information
                if current_device_count > 0:
                    # Get device names for status
                    device_names = []
                    for category in ['mobile_phones', 'dev_tools', 'tablets', 'emulators']:
                        for device in devices[category][:2]:  # Show first 2 from each category
                            device_names.append(device['title'])
                    
                    if device_names:
                        device_list = ", ".join(device_names[:3])  # Show max 3 device names
                        if current_device_count > 3:
                            device_list += f" (+{current_device_count-3} more)"
                        self.update_status(f"🔍 Auto-detected {current_device_count} devices: {device_list}", "green")
                    else:
                        self.update_status(f"🔍 Auto-detected {current_device_count} devices", "green")
                    
                    # Auto-refresh window list to include new devices
                    self.refresh_windows()
                else:
                    self.update_status("⚠️ No devices detected - Connect device and click Refresh", "orange")
                    
        except Exception as e:
            # Silently handle errors to avoid disrupting the UI
            print(f"DEBUG: Auto-detect error: {e}")
        
    def update_status(self, message: str, color: str = "black"):
        """Update status label with colored message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def pause_all_operations(self):
        """Pause all timers and operations to prevent USB disconnection during capture"""
        try:
            # Stop all timers
            if hasattr(self, 'refresh_timer') and self.refresh_timer.isActive():
                self.refresh_timer.stop()
                self._refresh_timer_was_active = True
            else:
                self._refresh_timer_was_active = False
                
            if hasattr(self, 'device_detection_timer') and self.device_detection_timer.isActive():
                self.device_detection_timer.stop()
                self._device_timer_was_active = True
            else:
                self._device_timer_was_active = False
                
            if hasattr(self, 'auto_timer') and self.auto_timer.isActive():
                self.auto_timer.stop()
                self._auto_timer_was_active = True
            else:
                self._auto_timer_was_active = False
                
            print("DEBUG: All operations paused for USB stability")
            
        except Exception as e:
            print(f"DEBUG: Error pausing operations: {e}")
    
    def resume_all_operations(self):
        """Resume all timers and operations after capture is complete"""
        try:
            # Wait a moment before resuming to ensure device stability
            time.sleep(1.0)
            
            # Resume timers that were active
            if hasattr(self, '_refresh_timer_was_active') and self._refresh_timer_was_active:
                if hasattr(self, 'refresh_timer'):
                    self.refresh_timer.start(3000)
                    
            if hasattr(self, '_device_timer_was_active') and self._device_timer_was_active:
                if hasattr(self, 'device_detection_timer'):
                    self.device_detection_timer.start(2000)
                    
            if hasattr(self, '_auto_timer_was_active') and self._auto_timer_was_active:
                if hasattr(self, 'auto_timer') and hasattr(self, 'interval_spinbox'):
                    interval = self.interval_spinbox.value() * 1000
                    self.auto_timer.start(interval)
                    
            print("DEBUG: All operations resumed after capture")
            
        except Exception as e:
            print(f"DEBUG: Error resuming operations: {e}")
    
    def take_screenshot_safe(self, window):
        """Take screenshot with minimal file operations to prevent USB disconnection"""
        try:
            self.update_status("📷 Taking screenshot...", "blue")
            
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"screenshot_{timestamp}.png"
            image_path = os.path.join(self.screenshots_dir, filename)
            
            # Use the most stable screenshot method
            success = False
            
            # Method 1: Try MSS (most stable)
            try:
                with mss.mss() as sct:
                    monitor = {
                        "top": window.top,
                        "left": window.left,
                        "width": window.width,
                        "height": window.height
                    }
                    screenshot = sct.grab(monitor)
                    # Save directly without any additional processing
                    mss.tools.to_png(screenshot.rgb, screenshot.size, output=image_path)
                    success = True
                    print(f"DEBUG: Screenshot saved using MSS: {image_path}")
            except Exception as e:
                print(f"DEBUG: MSS method failed: {e}")
            
            # Method 2: Fallback to pyautogui if MSS fails
            if not success:
                try:
                    screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))
                    screenshot.save(image_path)
                    success = True
                    print(f"DEBUG: Screenshot saved using pyautogui: {image_path}")
                except Exception as e:
                    print(f"DEBUG: pyautogui method failed: {e}")
            
            if success:
                self.update_status(f"✅ Screenshot captured: {filename}", "green")
                return image_path
            else:
                self.update_status("❌ Failed to capture screenshot", "red")
                return None
                
        except Exception as e:
            self.update_status(f"❌ Screenshot error: {str(e)}", "red")
            print(f"DEBUG: Screenshot error: {e}")
            return None
    
    def process_with_ocr_safe(self, image_path, task_name=None):
        """Process image with OCR using minimal operations"""
        try:
            self.update_status("🔍 Processing with OCR...", "blue")
            
            # Create and start OCR worker thread
            self.ocr_worker = OCRWorker(image_path, self.azure_api_key, self.azure_endpoint)
            self.ocr_worker.finished.connect(lambda result: self.on_ocr_finished_safe(result, task_name))
            self.ocr_worker.error.connect(lambda error: self.on_ocr_error_safe(error, task_name))
            self.ocr_worker.start()
            
            if task_name:
                self.update_task_progress(80, "Processing OCR")
            
        except Exception as e:
            self.update_status(f"❌ OCR processing error: {str(e)}", "red")
            if task_name:
                self.complete_task(task_name, False)
            print(f"DEBUG: OCR processing error: {e}")
    
    def on_ocr_finished_safe(self, result, task_name=None):
        """Handle OCR completion with minimal file operations"""
        try:
            # Extract text from OCR result
            raw_text = ""
            if 'regions' in result:
                for region in result['regions']:
                    for line in region['lines']:
                        for word in line['words']:
                            raw_text += word['text'] + " "
                        raw_text += "\n"
            
            # Store result for potential export
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.last_ocr_result = {
                'result': result,
                'raw_text': raw_text,
                'timestamp': timestamp
            }
            
            # Update task progress
            if task_name:
                self.update_task_progress(90, "Displaying results")
            
            # Display results without saving files
            self.display_ocr_results(raw_text, result)
            
            # Enable export buttons
            self.csv_export_btn.setEnabled(True)
            self.json_export_btn.setEnabled(True)
            self.view_details_btn.setEnabled(True)
            
            self.update_status(f"✅ OCR completed successfully - {len(raw_text)} characters extracted", "green")
            
            # Complete the task
            if task_name:
                self.update_task_progress(100, "Task completed")
                self.complete_task(task_name, True)
            
        except Exception as e:
            self.update_status(f"❌ OCR result processing error: {str(e)}", "red")
            if task_name:
                self.complete_task(task_name, False)
            print(f"DEBUG: OCR result processing error: {e}")
    
    def on_ocr_error_safe(self, error_message, task_name=None):
        """Handle OCR error with minimal operations"""
        self.update_status(f"❌ OCR Error: {error_message}", "red")
        if task_name:
            self.complete_task(task_name, False)
        print(f"DEBUG: OCR Error: {error_message}")
    
    def display_ocr_results(self, raw_text, ocr_result):
        """Display minimal OCR results preview"""
        try:
            # Update status label with preview
            if raw_text.strip():
                preview_text = raw_text[:100] + "..." if len(raw_text) > 100 else raw_text
                self.ocr_status_label.setText(f"✅ OCR Complete! Preview: {preview_text}")
                self.ocr_status_label.setStyleSheet("""
                    QLabel {
                        color: #4CAF50;
                        padding: 15px;
                        background: rgba(76, 175, 80, 0.1);
                        border: 2px solid #4CAF50;
                        border-radius: 8px;
                        margin: 10px;
                    }
                """)
            else:
                self.ocr_status_label.setText("⚠️ OCR Complete but no text detected")
                self.ocr_status_label.setStyleSheet("""
                    QLabel {
                        color: #FF9800;
                        padding: 15px;
                        background: rgba(255, 152, 0, 0.1);
                        border: 2px solid #FF9800;
                        border-radius: 8px;
                        margin: 10px;
                    }
                """)
            
            # Update quick stats
            char_count = len(raw_text)
            word_count = len(raw_text.split()) if raw_text.strip() else 0
            regions_count = len(ocr_result.get('regions', []))
            
            self.quick_stats_label.setText(
                f"📊 {char_count} chars | 📝 {word_count} words | 🔍 {regions_count} regions | 👁️ Click 'View Output Details' for full results"
            )
                
        except Exception as e:
            self.ocr_status_label.setText(f"Error displaying results: {str(e)}")
            print(f"DEBUG: Error displaying results: {e}")
    
    def add_task_to_queue(self, task_name, task_type="capture"):
        """Add a task to the navigation alert queue"""
        task = {
            'name': task_name,
            'type': task_type,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'status': 'queued'
        }
        self.task_queue.append(task)
        self.update_task_queue_display()
        print(f"DEBUG: Task added to queue: {task_name}")
    
    def start_task(self, task_name):
        """Start a task and update the navigation system"""
        # Find and start the task
        for task in self.task_queue:
            if task['name'] == task_name and task['status'] == 'queued':
                task['status'] = 'running'
                self.current_task = task
                self.task_progress = 0
                break
        
        self.update_task_queue_display()
        self.show_progress_bar(task_name)
        print(f"DEBUG: Task started: {task_name}")
    
    def update_task_progress(self, progress, message=None):
        """Update the progress of the current task"""
        self.task_progress = progress
        self.progress_bar.setValue(progress)
        
        if message:
            self.progress_bar.setFormat(f"{message} ({progress}%)")
        else:
            self.progress_bar.setFormat(f"{progress}%")
        
        # Update completion indicator
        if progress < 30:
            self.completion_label.setText("🔄 Initializing...")
            self.completion_label.setStyleSheet("color: #FFA726;")
        elif progress < 70:
            self.completion_label.setText("⚡ Processing...")
            self.completion_label.setStyleSheet("color: #2196F3;")
        elif progress < 100:
            self.completion_label.setText("🔍 Finalizing...")
            self.completion_label.setStyleSheet("color: #FF9800;")
        
        self.completion_label.setVisible(True)
    
    def complete_task(self, task_name, success=True):
        """Complete a task and update the navigation system"""
        # Find and complete the task
        for task in self.task_queue:
            if task['name'] == task_name and task['status'] == 'running':
                task['status'] = 'completed' if success else 'failed'
                task['completion_time'] = datetime.now().strftime('%H:%M:%S')
                break
        
        self.current_task = None
        self.task_progress = 100 if success else 0
        
        # Show completion status
        if success:
            self.completion_label.setText("✅ Task Completed Successfully!")
            self.completion_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("✅ Completed")
        else:
            self.completion_label.setText("❌ Task Failed")
            self.completion_label.setStyleSheet("color: #f44336; font-weight: bold;")
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("❌ Failed")
        
        # Auto-hide progress bar after 3 seconds
        QTimer.singleShot(3000, self.hide_progress_bar)
        
        self.update_task_queue_display()
        print(f"DEBUG: Task completed: {task_name} - Success: {success}")
    
    def update_task_queue_display(self):
        """Update the task queue display label"""
        if not self.task_queue:
            self.task_queue_label.setText("📋 Task Queue: Empty")
            self.task_queue_label.setStyleSheet("color: #666; font-style: italic;")
            return
        
        queued_tasks = [t for t in self.task_queue if t['status'] == 'queued']
        running_tasks = [t for t in self.task_queue if t['status'] == 'running']
        completed_tasks = [t for t in self.task_queue if t['status'] == 'completed']
        failed_tasks = [t for t in self.task_queue if t['status'] == 'failed']
        
        status_text = f"📋 Queue: {len(queued_tasks)} waiting"
        if running_tasks:
            status_text += f" | ⚡ {len(running_tasks)} running"
        if completed_tasks:
            status_text += f" | ✅ {len(completed_tasks)} completed"
        if failed_tasks:
            status_text += f" | ❌ {len(failed_tasks)} failed"
        
        self.task_queue_label.setText(status_text)
        
        # Color coding based on queue status
        if running_tasks:
            self.task_queue_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        elif queued_tasks:
            self.task_queue_label.setStyleSheet("color: #FFA726; font-weight: bold;")
        else:
            self.task_queue_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
    
    def show_progress_bar(self, task_name):
        """Show the gradient progress bar for a task"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"Starting: {task_name}")
        self.completion_label.setVisible(True)
        self.completion_label.setText("🔄 Initializing task...")
        self.completion_label.setStyleSheet("color: #FFA726;")
    
    def hide_progress_bar(self):
        """Hide the progress bar and completion indicator"""
        self.progress_bar.setVisible(False)
        self.completion_label.setVisible(False)
    
    def clear_completed_tasks(self):
        """Clear completed and failed tasks from the queue"""
        self.task_queue = [t for t in self.task_queue if t['status'] in ['queued', 'running']]
        self.update_task_queue_display()
        print("DEBUG: Cleared completed tasks from queue")
        
    def get_newer_device_keywords(self) -> list:
        """Get comprehensive list of modern device keywords for 2025"""
        return [
            # Samsung devices (all models)
            'sm-', 'galaxy', 'samsung', 'note', 'tab s', 'galaxy watch', 'galaxy buds',
            
            # Apple devices
            'iphone', 'ipad', 'apple watch', 'airpods', 'macbook', 'imac',
            
            # Google devices
            'pixel', 'nexus', 'chromebook', 'nest', 'google tv',
            
            # Chinese brands (major players)
            'xiaomi', 'redmi', 'poco', 'mi band', 'mi watch', 'mi pad',
            'huawei', 'honor', 'mate', 'p30', 'p40', 'p50', 'p60', 'nova',
            'oneplus', 'nord', 'oppo', 'find', 'reno', 'a series',
            'vivo', 'iqoo', 'x series', 'y series', 'v series',
            'realme', 'gt series', 'narzo',
            
            # Other major brands
            'sony', 'xperia', 'lg', 'wing', 'velvet',
            'motorola', 'moto', 'edge', 'razr',
            'nokia', 'htc', 'asus', 'rog phone', 'zenfone',
            'lenovo', 'legion phone', 'blackberry',
            
            # Wearables and IoT
            'fitbit', 'garmin', 'amazfit', 'zepp', 'huami',
            'apple watch', 'galaxy watch', 'wear os', 'tizen',
            
            # Tablets and 2-in-1s
            'surface', 'ipad', 'tab', 'tablet', 'kindle', 'fire tablet',
            
            # Gaming devices
            'steam deck', 'nintendo switch', 'rog ally', 'legion go',
            
            # Emulators and dev tools
            'scrcpy', 'android', 'adb', 'usb debugging', 'emulator',
            'bluestacks', 'nox', 'memu', 'ldplayer', 'gameloop', 'smartgaga',
            'android studio', 'vysor', 'mirroring',
            
            # Generic terms
            'phone', 'mobile', 'device', 'smart', 'wearable'
        ]
    
    def discover_newer_devices(self) -> dict:
        """Discover and categorize all newer devices connected to the system - Cross-platform implementation"""
        device_info = {
            'mobile_phones': [],
            'tablets': [],
            'wearables': [],
            'emulators': [],
            'dev_tools': [],
            'unknown_devices': []
        }
        
        try:
            if not WINDOW_MANAGER_AVAILABLE:
                print("ERROR: Window manager not available for device discovery")
                return device_info
            
            all_windows = gw.getAllWindows()
            device_keywords = self.get_newer_device_keywords()
            
            for window in all_windows:
                if not window.title or not window.title.strip():
                    continue
                    
                title_lower = window.title.lower()
                
                # Check if it matches any device keyword
                matched_keywords = [kw for kw in device_keywords if kw in title_lower]
                
                if matched_keywords:
                    # Cross-platform attribute handling
                    try:
                        width = getattr(window, 'width', getattr(window, 'size', [0, 0])[0] if hasattr(window, 'size') else 0)
                        height = getattr(window, 'height', getattr(window, 'size', [0, 0])[1] if hasattr(window, 'size') else 0)
                        left = getattr(window, 'left', getattr(window, 'topleft', [0, 0])[0] if hasattr(window, 'topleft') else 0)
                        top = getattr(window, 'top', getattr(window, 'topleft', [0, 0])[1] if hasattr(window, 'topleft') else 0)
                        visible = getattr(window, 'visible', getattr(window, 'isVisible', True))
                        
                        device_entry = {
                            'title': window.title,
                            'size': f"{width}x{height}",
                            'position': f"({left}, {top})",
                            'visible': visible,
                            'matched_keywords': matched_keywords
                        }
                    except Exception as attr_error:
                        print(f"DEBUG: Error getting window attributes: {attr_error}")
                        device_entry = {
                            'title': window.title,
                            'size': "Unknown",
                            'position': "Unknown",
                            'visible': True,
                            'matched_keywords': matched_keywords
                        }
                    
                    # Categorize device
                    if any(kw in title_lower for kw in ['phone', 'sm-', 'iphone', 'pixel', 'oneplus', 'xiaomi', 'huawei', 'oppo', 'vivo']):
                        device_info['mobile_phones'].append(device_entry)
                    elif any(kw in title_lower for kw in ['tablet', 'ipad', 'tab', 'surface']):
                        device_info['tablets'].append(device_entry)
                    elif any(kw in title_lower for kw in ['watch', 'band', 'fitbit', 'garmin', 'amazfit']):
                        device_info['wearables'].append(device_entry)
                    elif any(kw in title_lower for kw in ['emulator', 'bluestacks', 'nox', 'memu', 'ldplayer']):
                        device_info['emulators'].append(device_entry)
                    elif any(kw in title_lower for kw in ['scrcpy', 'adb', 'vysor', 'android studio']):
                        device_info['dev_tools'].append(device_entry)
                    else:
                        device_info['unknown_devices'].append(device_entry)
                        
        except Exception as e:
            print(f"DEBUG: Error in device discovery: {e} (Platform: {PLATFORM})")
            
        return device_info
    
    def show_all_devices_instantly(self):
        """Show ALL devices instantly in a separate dialog window - Cross-platform implementation"""
        try:
            if not WINDOW_MANAGER_AVAILABLE:
                self.update_status("❌ Window manager not available. Install PyWinCtl: pip install PyWinCtl", "red")
                return
            
            # Get ALL windows immediately
            all_windows = gw.getAllWindows()
            device_list = []
            
            # Platform-specific system window exclusions
            excluded_titles = ['Program Manager', 'Desktop Window Manager']  # Windows
            if PLATFORM == 'linux':
                excluded_titles.extend(['Desktop', 'Panel', 'Taskbar', 'Unity Panel', 'gnome-panel'])
            elif PLATFORM == 'darwin':  # macOS
                excluded_titles.extend(['Dock', 'Menu Bar', 'Spotlight'])
            
            for window in all_windows:
                if window.title and window.title.strip():
                    # Skip platform-specific system windows
                    if window.title not in excluded_titles:
                        device_list.append(window)
            
            # Create and show the instant device dialog
            dialog = InstantDeviceDialog(device_list, self)
            dialog.exec_()
            
            # Update status
            self.update_status(f"📱 Displayed {len(device_list)} devices in separate window! (Platform: {PLATFORM.title()})", "green")
            
            # Also refresh the combo box
            self.refresh_windows()
            
        except Exception as e:
            self.update_status(f"❌ Error showing devices: {str(e)} (Platform: {PLATFORM})", "red")
    
    def get_all_windows(self) -> list:
        """Get ALL windows without any filtering - Cross-platform implementation"""
        try:
            if not WINDOW_MANAGER_AVAILABLE:
                print("ERROR: Window manager not available")
                self.update_status("❌ Window manager not available. Install PyWinCtl: pip install PyWinCtl", "red")
                return []
            
            all_windows = gw.getAllWindows()
            visible_windows = []
            
            print(f"DEBUG: Processing {len(all_windows)} total windows on {PLATFORM}...")
            
            # Platform-specific system window exclusions
            excluded_titles = ['Program Manager', 'Desktop Window Manager']  # Windows
            if PLATFORM == 'linux':
                excluded_titles.extend(['Desktop', 'Panel', 'Taskbar', 'Unity Panel', 'gnome-panel', 
                                      'Plasma', 'plasmashell', 'kwin', 'compiz'])
            elif PLATFORM == 'darwin':  # macOS
                excluded_titles.extend(['Dock', 'Menu Bar', 'Spotlight', 'SystemUIServer'])
            
            for window in all_windows:
                try:
                    # Only skip completely empty titles
                    if not window.title or not window.title.strip():
                        continue
                    
                    # Skip platform-specific system windows
                    if window.title in excluded_titles:
                        continue
                    
                    # Cross-platform dimension checking
                    try:
                        width = getattr(window, 'width', getattr(window, 'size', [0, 0])[0] if hasattr(window, 'size') else 0)
                        height = getattr(window, 'height', getattr(window, 'size', [0, 0])[1] if hasattr(window, 'size') else 0)
                        
                        # Add windows with reasonable dimensions
                        if width > 0 and height > 0:
                            visible_windows.append(window)
                            print(f"DEBUG: Added window: {window.title} ({width}x{height})")
                    except:
                        # If we can't get dimensions, include it anyway
                        visible_windows.append(window)
                        print(f"DEBUG: Added window (no dims): {window.title}")
                            
                except Exception as window_error:
                    print(f"DEBUG: Error processing window: {window_error}")
                    continue
            
            # Sort windows by title
            visible_windows.sort(key=lambda w: w.title.lower())
            print(f"DEBUG: Total windows found: {len(visible_windows)} on {PLATFORM}")
            return visible_windows
            
        except Exception as e:
            self.update_status(f"❌ Error getting windows: {str(e)} (Platform: {PLATFORM})", "red")
            return []
    
    def refresh_windows(self):
        """Simple refresh - show ALL windows instantly"""
        try:
            current_selection = None
            if self.window_combo.currentIndex() >= 0:
                current_selection = self.window_combo.currentText()
            
            self.update_status("🔄 Getting all windows...", "blue")
            self.window_combo.clear()
            
            # Get all windows - no filtering!
            windows = self.get_all_windows()
            
            if not windows:
                self.window_combo.addItem("❌ No windows found")
                self.update_status("⚠️ No windows detected.", "orange")
                return
            
            # Add placeholder
            self.window_combo.addItem("🔍 Select a window to capture...", None)
            
            # Add ALL windows in simple list - no categories!
            for window in windows:
                display_text = f"{window.title} ({window.width}x{window.height})"
                if len(display_text) > 80:
                    display_text = display_text[:77] + "..."
                self.window_combo.addItem(display_text, window)
            
            # Try to restore previous selection
            if current_selection:
                for i in range(self.window_combo.count()):
                    if current_selection in self.window_combo.itemText(i):
                        self.window_combo.setCurrentIndex(i)
                        break
            
            self.update_status(f"✅ Found {len(windows)} windows - ALL devices shown!", "green")
            
        except Exception as e:
            self.update_status(f"❌ Error refreshing windows: {str(e)}", "red")
    
    def get_selected_window(self):
        """Get the currently selected window from combo box"""
        try:
            current_index = self.window_combo.currentIndex()
            if current_index >= 0:
                window = self.window_combo.itemData(current_index)
                # Check if it's a valid window object (not None or separator)
                if window and hasattr(window, 'title') and hasattr(window, 'left'):
                    return window
            return None
        except Exception as e:
            self.update_status(f"❌ Error getting selected window: {str(e)}", "red")
            return None
    
    def activate_window(self, window) -> bool:
        """Bring window to foreground and ensure it's visible - Cross-platform implementation"""
        try:
            if PLATFORM == 'windows':
                # Windows-specific activation using win32gui
                try:
                    import win32gui
                    import win32con
                    
                    # Get window handle
                    hwnd = window._hWnd
                    
                    # Check if window is minimized
                    if win32gui.IsIconic(hwnd):
                        # Restore the window
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        time.sleep(0.2)  # Give time for window to restore
                    
                    # Bring window to foreground
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.3)  # Give time for window to come to front
                    
                    # Ensure window is visible
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    time.sleep(0.2)
                    
                    # Verify window is now in foreground
                    foreground_hwnd = win32gui.GetForegroundWindow()
                    if foreground_hwnd == hwnd:
                        self.update_status(f"✅ Window activated: {window.title}", "green")
                        return True
                    else:
                        self.update_status(f"⚠️ Window partially activated: {window.title}", "orange")
                        return True  # Still proceed with capture
                        
                except ImportError:
                    # Fallback if win32gui not available
                    self.update_status(f"⚠️ win32gui not available, using PyWinCtl activation", "orange")
                    
            elif PLATFORM == 'linux':
                # Linux-specific activation using xdotool/wmctrl
                try:
                    if LINUX_TOOLS_AVAILABLE:
                        # Try to activate using xdotool
                        result = subprocess.run(['xdotool', 'search', '--name', window.title], 
                                              capture_output=True, text=True)
                        if result.returncode == 0 and result.stdout.strip():
                            window_id = result.stdout.strip().split('\n')[0]
                            subprocess.run(['xdotool', 'windowactivate', window_id], check=True)
                            time.sleep(0.3)
                            self.update_status(f"✅ Window activated (Linux): {window.title}", "green")
                            return True
                    else:
                        self.update_status(f"⚠️ Linux window tools not available, using PyWinCtl", "orange")
                except Exception as linux_error:
                    print(f"Linux activation failed: {linux_error}")
                    
            elif PLATFORM == 'darwin':  # macOS
                # macOS-specific activation
                try:
                    # Use PyWinCtl's cross-platform activation
                    if hasattr(window, 'activate'):
                        window.activate()
                        time.sleep(0.3)
                        self.update_status(f"✅ Window activated (macOS): {window.title}", "green")
                        return True
                except Exception as macos_error:
                    print(f"macOS activation failed: {macos_error}")
            
            # Cross-platform fallback using PyWinCtl
            try:
                if hasattr(window, 'activate'):
                    window.activate()
                    time.sleep(0.3)
                    self.update_status(f"✅ Window activated (PyWinCtl): {window.title}", "green")
                    return True
                elif hasattr(window, 'setFocus'):
                    window.setFocus()
                    time.sleep(0.3)
                    self.update_status(f"✅ Window focused: {window.title}", "green")
                    return True
                else:
                    self.update_status(f"⚠️ Window activation method not available for: {window.title}", "orange")
                    return True  # Still proceed with capture
            except Exception as fallback_error:
                print(f"PyWinCtl activation failed: {fallback_error}")
                
        except Exception as e:
            self.update_status(f"⚠️ Could not activate window: {str(e)} (Platform: {PLATFORM})", "orange")
            return True  # Still try to capture
    
    def take_screenshot_background(self, window) -> Optional[str]:
        """Take screenshot without activating window (background capture)"""
        try:
            # Generate unique filename with appropriate directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_num = random.randint(1000, 9999)
            
            # Determine if this is auto-capture or manual capture
            if hasattr(self, 'auto_checkbox') and self.auto_checkbox.isChecked():
                # Auto-capture - save to auto directory
                auto_images_dir = os.path.join(self.screenshots_dir, "auto_captures")
                os.makedirs(auto_images_dir, exist_ok=True)
                filename = f"auto_background_{timestamp}_{random_num}.png"
                filepath = os.path.join(auto_images_dir, filename)
            else:
                # Manual capture - save to manual directory
                manual_images_dir = os.path.join(self.screenshots_dir, "manual_captures")
                os.makedirs(manual_images_dir, exist_ok=True)
                filename = f"manual_background_{timestamp}_{random_num}.png"
                filepath = os.path.join(manual_images_dir, filename)
            
            # Refresh window information to get current position
            try:
                # Get fresh window list and find our target window
                all_windows = pywinctl.getAllWindows() if WINDOW_MANAGER_AVAILABLE else gw.getAllWindows()
                target_window = None
                
                for w in all_windows:
                    if hasattr(w, 'title') and hasattr(window, 'title') and w.title == window.title:
                        target_window = w
                        break
                
                if target_window:
                    window = target_window  # Use refreshed window object
                    print(f"DEBUG: Found refreshed window: {window.title}")
                else:
                    print(f"DEBUG: Could not refresh window info for: {window.title}")
            except Exception as refresh_error:
                print(f"DEBUG: Window refresh error: {refresh_error}")
            
            # Get cross-platform window dimensions and position
            try:
                width = getattr(window, 'width', getattr(window, 'size', [0, 0])[0] if hasattr(window, 'size') else 0)
                height = getattr(window, 'height', getattr(window, 'size', [0, 0])[1] if hasattr(window, 'size') else 0)
                left = getattr(window, 'left', getattr(window, 'topleft', [0, 0])[0] if hasattr(window, 'topleft') else 0)
                top = getattr(window, 'top', getattr(window, 'topleft', [0, 0])[1] if hasattr(window, 'topleft') else 0)
                
                print(f"DEBUG: Window dimensions - Width: {width}, Height: {height}, Left: {left}, Top: {top}")
                self.update_status(f"📸 Background capturing: {window.title} ({width}x{height}) at ({left},{top})", "blue")
            except Exception as e:
                self.update_status(f"❌ Could not get window properties: {str(e)}", "red")
                print(f"DEBUG: Window properties error: {e}")
                return None
            
            # Validate window dimensions
            if width <= 50 or height <= 50:
                self.update_status(f"❌ Window too small: {width}x{height} (minimum 50x50)", "red")
                print(f"DEBUG: Window dimensions too small: {width}x{height}")
                return None
            
            # Method 1: Windows - Use PrintWindow API for true background capture
            if PLATFORM == 'windows':
                try:
                    import win32gui
                    import win32ui
                    import win32con
                    from ctypes import windll
                    
                    # Get window handle - try multiple methods
                    hwnd = None
                    
                    # Method 1a: Direct _hWnd attribute (pygetwindow)
                    if hasattr(window, '_hWnd'):
                        hwnd = window._hWnd
                        print(f"DEBUG: Got hwnd from _hWnd: {hwnd}")
                    
                    # Method 1b: Try handle attribute (pywinctl)
                    elif hasattr(window, 'handle'):
                        hwnd = window.handle
                        print(f"DEBUG: Got hwnd from handle: {hwnd}")
                    
                    # Method 1c: Find window by exact title
                    if not hwnd and hasattr(window, 'title'):
                        hwnd = win32gui.FindWindow(None, window.title)
                        print(f"DEBUG: Got hwnd from FindWindow: {hwnd}")
                    
                    if hwnd and win32gui.IsWindow(hwnd):
                        # Get actual window dimensions from Windows API
                        rect = win32gui.GetWindowRect(hwnd)
                        left, top, right, bottom = rect
                        width = right - left
                        height = bottom - top
                        
                        if width > 0 and height > 0:
                            # Create device contexts
                            hwndDC = win32gui.GetWindowDC(hwnd)
                            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                            saveDC = mfcDC.CreateCompatibleDC()
                            
                            # Create bitmap
                            saveBitMap = win32ui.CreateBitmap()
                            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                            saveDC.SelectObject(saveBitMap)
                            
                            # Use PrintWindow with PW_RENDERFULLCONTENT flag for background capture
                            PW_RENDERFULLCONTENT = 0x00000002
                            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), PW_RENDERFULLCONTENT)
                            
                            if result:
                                # Convert to PIL Image
                                bmpinfo = saveBitMap.GetInfo()
                                bmpstr = saveBitMap.GetBitmapBits(True)
                                
                                img = Image.frombuffer(
                                    'RGB',
                                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                                    bmpstr, 'raw', 'BGRX', 0, 1
                                )
                                
                                # Check if image is not blank
                                extrema = img.getextrema()
                                is_blank = all(channel == (0, 0) for channel in extrema)
                                
                                if not is_blank:
                                    img.save(filepath)
                                    
                                    # Cleanup
                                    win32gui.DeleteObject(saveBitMap.GetHandle())
                                    saveDC.DeleteDC()
                                    mfcDC.DeleteDC()
                                    win32gui.ReleaseDC(hwnd, hwndDC)
                                    
                                    self.update_status(f"✅ Background screenshot saved: {filename}", "green")
                                    return filepath
                                else:
                                    print("PrintWindow returned blank image, trying fallback...")
                            
                            # Cleanup on failure
                            win32gui.DeleteObject(saveBitMap.GetHandle())
                            saveDC.DeleteDC()
                            mfcDC.DeleteDC()
                            win32gui.ReleaseDC(hwnd, hwndDC)
                            
                            # Try alternative PrintWindow flags
                            if not result:
                                # Recreate contexts for second attempt
                                hwndDC = win32gui.GetWindowDC(hwnd)
                                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                                saveDC = mfcDC.CreateCompatibleDC()
                                saveBitMap = win32ui.CreateBitmap()
                                saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                                saveDC.SelectObject(saveBitMap)
                                
                                # Try with flag 0 (standard rendering)
                                result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
                                
                                if result:
                                    bmpinfo = saveBitMap.GetInfo()
                                    bmpstr = saveBitMap.GetBitmapBits(True)
                                    
                                    img = Image.frombuffer(
                                        'RGB',
                                        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                                        bmpstr, 'raw', 'BGRX', 0, 1
                                    )
                                    
                                    extrema = img.getextrema()
                                    is_blank = all(channel == (0, 0) for channel in extrema)
                                    
                                    if not is_blank:
                                        img.save(filepath)
                                        
                                        # Cleanup
                                        win32gui.DeleteObject(saveBitMap.GetHandle())
                                        saveDC.DeleteDC()
                                        mfcDC.DeleteDC()
                                        win32gui.ReleaseDC(hwnd, hwndDC)
                                        
                                        self.update_status(f"✅ Background screenshot saved: {filename}", "green")
                                        return filepath
                                
                                # Final cleanup
                                win32gui.DeleteObject(saveBitMap.GetHandle())
                                saveDC.DeleteDC()
                                mfcDC.DeleteDC()
                                win32gui.ReleaseDC(hwnd, hwndDC)
                            
                except Exception as e:
                    print(f"Windows PrintWindow failed: {e}")
            
            # Method 2: Cross-platform MSS with window coordinates
            try:
                with mss.mss() as sct:
                    monitor = {
                        "top": top,
                        "left": left,
                        "width": width,
                        "height": height
                    }
                    
                    # Grab the screenshot
                    sct_img = sct.grab(monitor)
                    
                    # Convert to PIL Image
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    
                    # Check if image is not just black
                    if img.getextrema() != ((0, 0), (0, 0), (0, 0)):
                        img.save(filepath)
                        self.update_status(f"✅ Background screenshot saved (MSS): {filename}", "green")
                        return filepath
                    else:
                        print("MSS captured black image, trying fallback...")
                    
            except Exception as e:
                print(f"MSS failed: {e}")
            
            # Method 3: Linux-specific screenshot methods
            if PLATFORM == 'linux':
                try:
                    import subprocess
                    scrot_cmd = [
                        "scrot", 
                        "-a", f"{left},{top},{width},{height}",
                        filepath
                    ]
                    result = subprocess.run(scrot_cmd, capture_output=True, text=True)
                    if result.returncode == 0 and os.path.exists(filepath):
                        self.update_status(f"✅ Background screenshot saved (scrot): {filename}", "green")
                        return filepath
                except Exception as e:
                    print(f"scrot failed: {e}")
            
            # Method 4: Fallback to pyautogui (may require activation)
            try:
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
                
                # Check if screenshot is not just black
                extrema = screenshot.getextrema()
                if extrema != ((0, 0), (0, 0), (0, 0)):
                    screenshot.save(filepath)
                    self.update_status(f"✅ Background screenshot saved (PyAutoGUI): {filename}", "green")
                    return filepath
                else:
                    self.update_status("⚠️ Captured image appears to be black/empty", "orange")
                    # Save anyway for debugging
                    screenshot.save(filepath)
                    return filepath
                    
            except Exception as e:
                print(f"PyAutoGUI failed: {e}")
            
            self.update_status(f"❌ All background capture methods failed (Platform: {PLATFORM})", "red")
            return None
            
        except Exception as e:
            self.update_status(f"❌ Background screenshot failed: {str(e)} (Platform: {PLATFORM})", "red")
            return None
    
    def take_screenshot(self, window) -> Optional[str]:
        """Take screenshot with automatic window activation"""
        try:
            # Step 1: Activate the window to bring it to foreground
            self.update_status("🔄 Activating target window...", "blue")
            self.activate_window(window)
            
            # Step 2: Refresh window position (in case it moved) - Cross-platform
            if WINDOW_MANAGER_AVAILABLE:
                try:
                    # Use PyWinCtl for cross-platform window refresh
                    all_windows = pywinctl.getAllWindows()
                    for w in all_windows:
                        if hasattr(w, 'title') and w.title == window.title:
                            # Check if window has valid dimensions
                            width = getattr(w, 'width', getattr(w, 'size', [0, 0])[0] if hasattr(w, 'size') else 0)
                            height = getattr(w, 'height', getattr(w, 'size', [0, 0])[1] if hasattr(w, 'size') else 0)
                            visible = getattr(w, 'visible', getattr(w, 'isVisible', True))
                            
                            if visible and width > 0 and height > 0:
                                window = w  # Use updated window object
                                break
                except Exception as e:
                    print(f"Window refresh failed: {e}")
                    pass  # Use original window if refresh fails
            else:
                # Fallback for systems without PyWinCtl
                try:
                    if hasattr(gw, 'getWindowsWithTitle'):
                        window_list = gw.getWindowsWithTitle(window.title)
                        for w in window_list:
                            if w.visible and w.width > 0 and w.height > 0:
                                window = w  # Use updated window object
                                break
                except:
                    pass  # Use original window if refresh fails
            
            # Step 3: Validate window region - Cross-platform attribute handling
            try:
                width = getattr(window, 'width', getattr(window, 'size', [0, 0])[0] if hasattr(window, 'size') else 0)
                height = getattr(window, 'height', getattr(window, 'size', [0, 0])[1] if hasattr(window, 'size') else 0)
                
                if width <= 0 or height <= 0:
                    self.update_status("❌ Invalid window dimensions", "red")
                    return None
            except Exception as e:
                self.update_status(f"❌ Could not get window dimensions: {str(e)}", "red")
                return None
            
            # Generate unique filename with appropriate directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_num = random.randint(1000, 9999)
            
            # Determine if this is auto-capture or manual capture
            if hasattr(self, 'auto_checkbox') and self.auto_checkbox.isChecked():
                # Auto-capture - save to auto directory
                auto_images_dir = os.path.join(self.screenshots_dir, "auto_captures")
                os.makedirs(auto_images_dir, exist_ok=True)
                filename = f"auto_screenshot_{timestamp}_{random_num}.png"
                filepath = os.path.join(auto_images_dir, filename)
            else:
                # Manual capture - save to manual directory
                manual_images_dir = os.path.join(self.screenshots_dir, "manual_captures")
                os.makedirs(manual_images_dir, exist_ok=True)
                filename = f"manual_screenshot_{timestamp}_{random_num}.png"
                filepath = os.path.join(manual_images_dir, filename)
            
            # Get cross-platform window dimensions and position
            try:
                width = getattr(window, 'width', getattr(window, 'size', [0, 0])[0] if hasattr(window, 'size') else 0)
                height = getattr(window, 'height', getattr(window, 'size', [0, 0])[1] if hasattr(window, 'size') else 0)
                left = getattr(window, 'left', getattr(window, 'topleft', [0, 0])[0] if hasattr(window, 'topleft') else 0)
                top = getattr(window, 'top', getattr(window, 'topleft', [0, 0])[1] if hasattr(window, 'topleft') else 0)
                
                self.update_status(f"📸 Capturing window: {window.title} ({width}x{height})", "blue")
            except Exception as e:
                self.update_status(f"❌ Could not get window properties: {str(e)}", "red")
                return None
            
            # Method 1: Try DXcam (fastest, Windows Desktop Duplication API) - Windows only
            if DXCAM_AVAILABLE and PLATFORM == "Windows":
                try:
                    camera = dxcam.create()
                    if camera:
                        region = (left, top, left + width, top + height)
                        frame = camera.grab(region=region)
                        if frame is not None and frame.size > 0:
                            img = Image.fromarray(frame)
                            # Check if image is not just black
                            if img.getextrema() != ((0, 0), (0, 0), (0, 0)):
                                img.save(filepath)
                                camera.release()
                                self.update_status(f"✅ Screenshot saved (DXcam): {filename}", "green")
                                return filepath
                        camera.release()
                except Exception as e:
                    print(f"DXcam failed: {e}")
            
            # Method 2: MSS (ultra-fast cross-platform)
            try:
                with mss.mss() as sct:
                    monitor = {
                        "top": top,
                        "left": left,
                        "width": width,
                        "height": height
                    }
                    
                    # Grab the screenshot
                    sct_img = sct.grab(monitor)
                    
                    # Convert to PIL Image
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    
                    # Check if image is not just black
                    if img.getextrema() != ((0, 0), (0, 0), (0, 0)):
                        img.save(filepath)
                        self.update_status(f"✅ Screenshot saved (MSS): {filename}", "green")
                        return filepath
                    else:
                        print("MSS captured black image, trying fallback...")
                    
            except Exception as e:
                print(f"MSS failed: {e}")
            
            # Method 3: Linux-specific screenshot methods
            if PLATFORM == "Linux":
                try:
                    # Try using scrot for Linux
                    import subprocess
                    scrot_cmd = [
                        "scrot", 
                        "-a", f"{left},{top},{width},{height}",
                        filepath
                    ]
                    result = subprocess.run(scrot_cmd, capture_output=True, text=True)
                    if result.returncode == 0 and os.path.exists(filepath):
                        self.update_status(f"✅ Screenshot saved (scrot): {filename}", "green")
                        return filepath
                except Exception as e:
                    print(f"scrot failed: {e}")
            
            # Method 4: Fallback to pyautogui with window activation (cross-platform)
            try:
                # Additional wait to ensure window is ready
                time.sleep(0.5)
                
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
                
                # Check if screenshot is not just black
                extrema = screenshot.getextrema()
                if extrema != ((0, 0), (0, 0), (0, 0)):
                    screenshot.save(filepath)
                    self.update_status(f"✅ Screenshot saved (PyAutoGUI): {filename}", "green")
                    return filepath
                else:
                    self.update_status("⚠️ Captured image appears to be black/empty", "orange")
                    # Save anyway for debugging
                    screenshot.save(filepath)
                    return filepath
                    
            except Exception as e:
                print(f"PyAutoGUI failed: {e}")
            
            self.update_status(f"❌ All capture methods failed (Platform: {PLATFORM})", "red")
            return None
            
        except Exception as e:
            self.update_status(f"❌ Screenshot failed: {str(e)} (Platform: {PLATFORM})", "red")
            return None
    
    def process_with_ocr(self, image_path: str):
        """Process image with Azure OCR API"""
        if not self.azure_api_key:
            self.update_status("❌ Azure API key not configured", "red")
            self.ocr_status_label.setText("⚠️ Please configure your Azure Computer Vision API key and endpoint in your .env file.")
            self.ocr_status_label.setStyleSheet("""
                QLabel {
                    color: #FF5722;
                    padding: 15px;
                    background: rgba(255, 87, 34, 0.1);
                    border: 2px solid #FF5722;
                    border-radius: 8px;
                    margin: 10px;
                }
            """)
            return
        
        # Store current image path for potential deletion after CSV export
        self.current_image_path = image_path
        
        self.update_status("🔄 Processing with OCR...", "blue")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start OCR worker thread
        self.ocr_worker = OCRWorker(image_path, self.azure_api_key, self.azure_endpoint)
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.start()
    
    def on_ocr_finished(self, result: Dict[Any, Any]):
        """Handle successful OCR result"""
        self.progress_bar.setVisible(False)
        self.update_status("✅ OCR processing completed", "green")
        
        # Extract raw text from OCR result
        raw_text = self.extract_raw_text(result)
        
        # Store last result for manual export
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.last_ocr_result = {
            'result': result,
            'raw_text': raw_text,
            'timestamp': timestamp,
            'image_path': getattr(self, 'current_image_path', None)
        }
        
        # Enable export buttons
        self.csv_export_btn.setEnabled(True)
        self.json_export_btn.setEnabled(True)
        self.view_details_btn.setEnabled(True)
        
        # Display results using new minimal preview approach
        self.display_ocr_results(raw_text, result)
        
        # Save to CSV based on capture mode
        image_path = getattr(self, 'current_image_path', None)
        if self.auto_checkbox.isChecked():
            # Auto-capture mode: save to auto_data.csv and JSON
            self.save_auto_data(raw_text, timestamp, image_path)
        else:
            # Manual capture mode: save to single_screenshot_time.csv
            self.save_manual_capture(raw_text, timestamp, image_path)
    
    def extract_raw_text(self, ocr_result: Dict[Any, Any]) -> str:
        """Extract raw text from OCR result"""
        try:
            raw_text_lines = []
            
            # Handle different Azure Computer Vision API response formats
            if 'analyzeResult' in ocr_result:
                # Document Intelligence / Read API v3.2+ format
                analyze_result = ocr_result['analyzeResult']
                if 'readResults' in analyze_result:
                    for page in analyze_result['readResults']:
                        for line in page.get('lines', []):
                            raw_text_lines.append(line.get('text', ''))
                elif 'pages' in analyze_result:
                    for page in analyze_result['pages']:
                        for line in page.get('lines', []):
                            raw_text_lines.append(line.get('text', ''))
            elif 'readResult' in ocr_result:
                # Read API v3.0/3.1 format
                for page in ocr_result['readResult']['pages']:
                    for line in page.get('lines', []):
                        raw_text_lines.append(line.get('text', ''))
            elif 'regions' in ocr_result:
                # OCR API v3.2 format (this is what we're actually using)
                for region in ocr_result['regions']:
                    for line in region.get('lines', []):
                        # Extract text from words in each line
                        line_text = ' '.join([word.get('text', '') for word in line.get('words', [])])
                        if line_text.strip():
                            raw_text_lines.append(line_text)
            else:
                # Fallback: recursively search for any 'text' fields
                def find_text_recursive(obj, texts):
                    if isinstance(obj, dict):
                        # Look for 'text' field
                        if 'text' in obj and isinstance(obj['text'], str) and obj['text'].strip():
                            texts.append(obj['text'])
                        # Look for 'content' field (alternative text field)
                        elif 'content' in obj and isinstance(obj['content'], str) and obj['content'].strip():
                            texts.append(obj['content'])
                        # Recursively search in nested objects
                        for key, value in obj.items():
                            if key not in ['text', 'content']:  # Avoid duplicate processing
                                find_text_recursive(value, texts)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_text_recursive(item, texts)
                
                find_text_recursive(ocr_result, raw_text_lines)
            
            # Clean and join the text lines
            clean_lines = [line.strip() for line in raw_text_lines if line.strip()]
            return '\n'.join(clean_lines) if clean_lines else ''
            
        except Exception as e:
            return f"Error extracting text: {str(e)}"
    
    def save_to_csv(self, raw_text: str, timestamp: str, image_path: str = None):
        """Save only raw data to CSV file in proper format"""
        try:
            csv_file_path = os.path.join(self.csv_dir, "auto_data.csv")
            
            # Get current window info
            window = self.get_selected_window()
            window_title = window.title if window else "Unknown"
            
            # Prepare simplified CSV row data (only raw data)
            csv_data = {
                'timestamp': timestamp,
                'window_title': window_title,
                'raw_text': raw_text.replace('\n', ' | ') if raw_text.strip() else 'No text detected'
            }
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(csv_file_path)
            
            # Write to CSV file
            with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'window_title', 'raw_text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Write data row
                writer.writerow(csv_data)
            
            self.update_status(f"📊 Raw data saved to auto_data.csv", "green")
            
            # Auto-delete screenshot after saving to CSV (with enhanced logging)
            if image_path and os.path.exists(image_path):
                try:
                    print(f"DEBUG: Attempting to delete screenshot: {image_path}")
                    os.remove(image_path)
                    print(f"DEBUG: Successfully deleted screenshot: {image_path}")
                    self.update_status(f"🗑️ Screenshot deleted: {os.path.basename(image_path)}", "gray")
                except Exception as delete_error:
                    print(f"DEBUG: Failed to delete screenshot: {str(delete_error)}")
                    self.update_status(f"⚠️ Could not delete screenshot: {str(delete_error)}", "orange")
            else:
                print(f"DEBUG: Screenshot not deleted - path: {image_path}, exists: {os.path.exists(image_path) if image_path else 'N/A'}")
            
        except Exception as e:
            self.update_status(f"❌ Failed to save CSV: {str(e)}", "red")
    
    def save_manual_capture(self, raw_text: str, timestamp: str, image_path: str = None):
        """Save manual capture data to separate CSV and JSON files in dedicated directory"""
        try:
            # Create manual captures directory
            manual_images_dir = os.path.join(self.screenshots_dir, "manual_images")
            manual_csv_dir = os.path.join(self.csv_dir, "manual_captures")
            manual_json_dir = os.path.join(self.json_dir, "manual_captures")
            os.makedirs(manual_images_dir, exist_ok=True)
            os.makedirs(manual_csv_dir, exist_ok=True)
            os.makedirs(manual_json_dir, exist_ok=True)
            
            # Get window title
            window = self.get_selected_window()
            window_title = window.title if window else "Unknown"
            
            # Save to separate CSV file for manual captures with dynamic filename
            timestamp_safe = timestamp.replace(':', '-').replace(' ', '_')
            csv_filename = f"manual_capture_{timestamp_safe}.csv"
            csv_path = os.path.join(manual_csv_dir, csv_filename)
            file_exists = os.path.exists(csv_path)
            
            csv_data = {
                'timestamp': timestamp,
                'window_title': window_title,
                'raw_text': raw_text.replace('\n', ' | ') if raw_text.strip() else 'No text detected'
            }
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'window_title', 'raw_text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(csv_data)
            
            # Save to JSON file in manual captures directory
            if hasattr(self, 'last_ocr_result') and self.last_ocr_result:
                export_data = {
                    'timestamp': timestamp,
                    'window_title': window_title,
                    'raw_text': raw_text,
                    'full_ocr_result': self.last_ocr_result['result'],
                    'image_path': image_path
                }
                
                json_timestamp_safe = timestamp.replace(':', '-').replace(' ', '_')
                json_filename = f"manual_capture_{json_timestamp_safe}.json"
                json_path = os.path.join(manual_json_dir, json_filename)
                
                with open(json_path, 'w', encoding='utf-8') as json_file:
                    json.dump(export_data, json_file, indent=2, ensure_ascii=False)
                
                self.update_status(f"📋 Manual capture saved: {csv_filename} and {json_filename}", "green")
            else:
                self.update_status(f"📋 Manual capture saved: {csv_filename}", "green")
            
            # Clean up old screenshots (keep only last 5)
            self.cleanup_old_screenshots()
            
            # Keep screenshot for manual captures (don't auto-delete)
            if image_path and os.path.exists(image_path):
                self.update_status(f"📸 Screenshot preserved: {os.path.basename(image_path)}", "blue")
            
        except Exception as e:
            self.update_status(f"❌ Failed to save manual capture: {str(e)}", "red")
    
    def cleanup_old_screenshots(self):
        """Clean up old screenshots based on custom time interval or count"""
        try:
            # Get all screenshot files in the auto and manual subdirectories
            auto_images_dir = os.path.join(self.screenshots_dir, "auto_captures")
            manual_images_dir = os.path.join(self.screenshots_dir, "manual_captures")
            
            screenshot_patterns = []
            # Add patterns for auto-capture directory
            if os.path.exists(auto_images_dir):
                screenshot_patterns.extend([
                    os.path.join(auto_images_dir, "*.png"),
                    os.path.join(auto_images_dir, "*.jpg"),
                    os.path.join(auto_images_dir, "*.jpeg"),
                    os.path.join(auto_images_dir, "*.bmp")
                ])
            # Add patterns for manual capture directory
            if os.path.exists(manual_images_dir):
                screenshot_patterns.extend([
                    os.path.join(manual_images_dir, "*.png"),
                    os.path.join(manual_images_dir, "*.jpg"),
                    os.path.join(manual_images_dir, "*.jpeg"),
                    os.path.join(manual_images_dir, "*.bmp")
                ])
            
            all_screenshots = []
            for pattern in screenshot_patterns:
                all_screenshots.extend(glob.glob(pattern))
            
            if len(all_screenshots) == 0:
                return  # No screenshots to clean up
            
            # Get deletion mode and settings
            deletion_mode = self.deletion_mode_combo.currentData() if hasattr(self, 'deletion_mode_combo') else "count"
            deletion_value = self.deletion_interval_spinbox.value() if hasattr(self, 'deletion_interval_spinbox') else 5
            
            screenshots_to_delete = []
            deleted_count = 0
            
            if deletion_mode == "time":
                # Delete screenshots older than specified time interval
                import time
                current_time = time.time()
                time_threshold = deletion_value * 60  # Convert minutes to seconds
                
                for screenshot_path in all_screenshots:
                    try:
                        file_modified_time = os.path.getmtime(screenshot_path)
                        if (current_time - file_modified_time) > time_threshold:
                            screenshots_to_delete.append(screenshot_path)
                    except Exception as e:
                        print(f"DEBUG: Error checking file time for {screenshot_path}: {e}")
                
                # Delete old screenshots
                for screenshot_path in screenshots_to_delete:
                    try:
                        os.remove(screenshot_path)
                        deleted_count += 1
                        print(f"DEBUG: Cleaned up old screenshot (time-based): {os.path.basename(screenshot_path)}")
                    except Exception as delete_error:
                        print(f"DEBUG: Failed to delete old screenshot {screenshot_path}: {delete_error}")
                
                if deleted_count > 0:
                    self.update_status(f"🧹 Cleaned up {deleted_count} screenshots older than {deletion_value} minutes", "blue")
                
            else:  # count mode
                # Keep only the most recent N screenshots
                if len(all_screenshots) <= deletion_value:
                    return  # No cleanup needed
                
                # Sort by modification time (newest first)
                all_screenshots.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # Keep only the first N (newest), delete the rest
                screenshots_to_delete = all_screenshots[deletion_value:]
                
                for screenshot_path in screenshots_to_delete:
                    try:
                        os.remove(screenshot_path)
                        deleted_count += 1
                        print(f"DEBUG: Cleaned up old screenshot (count-based): {os.path.basename(screenshot_path)}")
                    except Exception as delete_error:
                        print(f"DEBUG: Failed to delete old screenshot {screenshot_path}: {delete_error}")
                
                if deleted_count > 0:
                    self.update_status(f"🧹 Cleaned up {deleted_count} old screenshots (keeping last {deletion_value} files)", "blue")
                
        except Exception as e:
            print(f"DEBUG: Screenshot cleanup error: {e}")
            self.update_status(f"⚠️ Screenshot cleanup warning: {str(e)}", "orange")
    
    def save_auto_data(self, raw_text: str, timestamp: str, image_path: str = None):
        """Save data to both CSV and JSON files when auto-capture is active
        
        Enhanced with comprehensive USB stability management:
        - Intelligent file operation timing
        - Reduced concurrent I/O operations
        - Error recovery mechanisms
        - Device-specific optimizations
        """
        try:
            # Get window title
            window = self.get_selected_window()
            window_title = window.title if window else "Unknown"
            
            # USB STABILITY: Use managed delay based on device type
            if hasattr(self, 'usb_stability_manager'):
                stability_delay = self.usb_stability_manager.operation_delays.get('file_write', 0.2)
                time.sleep(stability_delay)
            else:
                time.sleep(0.1)
            
            # Save to CSV with proper error handling
            csv_path = os.path.join(self.csv_dir, "auto_data.csv")
            file_exists = os.path.exists(csv_path)
            
            csv_data = {
                'timestamp': timestamp,
                'window_title': window_title,
                'raw_text': raw_text.replace('\n', ' | ') if raw_text.strip() else 'No text detected'
            }
            
            try:
                with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['timestamp', 'window_title', 'raw_text']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow(csv_data)
                    csvfile.flush()  # Ensure data is written immediately
                    
            except Exception as csv_error:
                print(f"DEBUG: CSV write error: {csv_error}")
                self.update_status(f"⚠️ CSV save failed: {str(csv_error)}", "orange")
                return  # Don't continue if CSV fails
            
            # USB STABILITY FIX 2: Delay between major file operations
            time.sleep(0.15)
            
            # Save to JSON (only if CSV succeeded)
            json_saved = False
            if hasattr(self, 'last_ocr_result') and self.last_ocr_result:
                try:
                    export_data = {
                        'timestamp': timestamp,
                        'window_title': window_title,
                        'raw_text': raw_text,
                        'full_ocr_result': self.last_ocr_result['result'],
                        'image_path': image_path
                    }
                    
                    timestamp_safe = timestamp.replace(':', '-').replace(' ', '_')
                    json_filename = f"auto_capture_{timestamp_safe}.json"
                    json_path = os.path.join(self.json_dir, json_filename)
                    
                    with open(json_path, 'w', encoding='utf-8') as json_file:
                        json.dump(export_data, json_file, indent=2, ensure_ascii=False)
                        json_file.flush()  # Ensure data is written immediately
                    
                    json_saved = True
                    self.update_status(f"💾 Auto-saved to CSV and JSON: {os.path.basename(csv_path)}, {json_filename}", "green")
                    
                except Exception as json_error:
                    print(f"DEBUG: JSON write error: {json_error}")
                    self.update_status(f"💾 CSV saved successfully, JSON failed: {str(json_error)}", "orange")
            
            if not json_saved:
                self.update_status(f"💾 Auto-saved to CSV: {os.path.basename(csv_path)}", "green")
            
            # USB STABILITY: Use managed delay before cleanup operations
            if hasattr(self, 'usb_stability_manager'):
                cleanup_delay = self.usb_stability_manager.operation_delays.get('cleanup', 0.5)
                time.sleep(cleanup_delay)
            else:
                time.sleep(0.2)
            
            # Clean up old screenshots with USB stability-aware frequency
            if not hasattr(self, '_cleanup_counter'):
                self._cleanup_counter = 0
            self._cleanup_counter += 1
            
            # Get optimal cleanup frequency from USB stability manager
            cleanup_frequency = 10  # Default
            if hasattr(self, 'usb_stability_manager'):
                cleanup_frequency = self.usb_stability_manager.get_optimal_cleanup_frequency()
            
            if self._cleanup_counter % cleanup_frequency == 0:
                try:
                    if hasattr(self, 'usb_stability_manager'):
                        self.usb_stability_manager.safe_cleanup(self.cleanup_old_screenshots)
                    else:
                        self.cleanup_old_screenshots()
                except Exception as cleanup_error:
                    print(f"DEBUG: Screenshot cleanup error: {cleanup_error}")
                    # Don't fail the operation if cleanup fails
            
            # USB STABILITY: Intelligent screenshot deletion management
            auto_delete_enabled = getattr(self, 'enable_auto_delete_screenshots', False)
            
            if auto_delete_enabled and image_path and os.path.exists(image_path):
                # Check if we should skip deletion for USB stability
                if hasattr(self, 'usb_stability_manager') and self.usb_stability_manager.should_skip_operation('file_delete'):
                    print(f"DEBUG: Screenshot deletion skipped for USB stability: {image_path}")
                    if self._cleanup_counter % 5 == 0:
                        self.update_status(f"🔌 Screenshot deletion skipped for USB stability", "blue")
                else:
                    try:
                        # Use USB stability manager for safe deletion
                        if hasattr(self, 'usb_stability_manager'):
                            success = self.usb_stability_manager.safe_file_delete(image_path)
                            if success:
                                print(f"DEBUG: Screenshot safely deleted: {image_path}")
                                self.update_status(f"🗑️ Screenshot auto-deleted: {os.path.basename(image_path)}", "gray")
                            else:
                                print(f"DEBUG: Screenshot not found for deletion: {image_path}")
                        else:
                            # Fallback to regular deletion with delay
                            time.sleep(0.3)
                            os.remove(image_path)
                            print(f"DEBUG: Screenshot deleted successfully: {image_path}")
                            self.update_status(f"🗑️ Screenshot auto-deleted: {os.path.basename(image_path)}", "gray")
                    except Exception as delete_error:
                        print(f"DEBUG: Failed to delete screenshot: {image_path}, Error: {delete_error}")
                        # Don't fail the entire operation if deletion fails
                        self.update_status(f"⚠️ Screenshot deletion failed, continuing...", "orange")
            elif image_path and os.path.exists(image_path):
                if not auto_delete_enabled:
                    print(f"DEBUG: Auto-deletion disabled for USB stability - preserving: {image_path}")
                    # Only show this message occasionally to avoid spam
                    if self._cleanup_counter % 5 == 0:
                        stability_status = ""
                        if hasattr(self, 'usb_stability_manager'):
                            stability_status = f" ({self.usb_stability_manager.get_status_message()})"
                        self.update_status(f"💾 Screenshots preserved (auto-delete disabled){stability_status}", "blue")
                else:
                    print(f"DEBUG: Screenshot not found for deletion - path: {image_path}")
            
        except Exception as e:
            print(f"DEBUG: Critical error in save_auto_data: {e}")
            self.update_status(f"❌ Failed to save auto data: {str(e)}", "red")
    
    def on_ocr_error(self, error_message: str):
        """Handle OCR error"""
        self.progress_bar.setVisible(False)
        self.update_status(f"❌ OCR Error", "red")
        self.ocr_status_label.setText(f"❌ OCR Error: {error_message}")
        self.ocr_status_label.setStyleSheet("""
            QLabel {
                color: #F44336;
                padding: 15px;
                background: rgba(244, 67, 54, 0.1);
                border: 2px solid #F44336;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        self.quick_stats_label.setText("")
    
    def capture_background_window(self):
        """Capture the selected window in background without activating it"""
        # Start performance tracking
        capture_start_time = time.time()
        
        # Add task to navigation queue
        task_name = "Background Screenshot Capture"
        self.add_task_to_queue(task_name)
        self.start_task(task_name)
        
        self.update_status("🔍 Getting selected window for background capture...", "blue")
        self.update_task_progress(10, "Getting window")
        
        try:
            # Step 1: Get selected window
            window = self.get_selected_window()
            if not window:
                current_text = self.window_combo.currentText()
                if "Select a window" in current_text or "No windows found" in current_text:
                    self.update_status("❌ Please select a valid window first", "red")
                    self.complete_task(task_name, False)
                    QMessageBox.warning(self, "No Window Selected", 
                                      "Please select a valid window from the dropdown list.\n\n" +
                                      "If you don't see your device window:\n" +
                                      "1. Make sure your device/app is running\n" +
                                      "2. Click the 'Refresh' button\n" +
                                      "3. Look for your device in the Mobile/Device section")
                else:
                    self.update_status("❌ Invalid window selection", "red")
                    self.complete_task(task_name, False)
                    QMessageBox.warning(self, "Invalid Selection", 
                                      "The selected item is not a valid window. Please choose a window from the list.")
                return
            
            self.update_task_progress(20, "Validating window")
            
            # Verify window is still valid
            try:
                width = getattr(window, 'width', getattr(window, 'size', [0, 0])[0] if hasattr(window, 'size') else 0)
                height = getattr(window, 'height', getattr(window, 'size', [0, 0])[1] if hasattr(window, 'size') else 0)
                visible = getattr(window, 'visible', getattr(window, 'isVisible', True))
                
                if not visible or width <= 0 or height <= 0:
                    self.update_status("❌ Selected window is no longer valid", "red")
                    self.complete_task(task_name, False)
                    QMessageBox.warning(self, "Window Not Available", 
                                      "The selected window is no longer available. Please refresh the list and select again.")
                    return
            except:
                self.update_status("❌ Selected window is no longer accessible", "red")
                self.complete_task(task_name, False)
                QMessageBox.warning(self, "Window Error", 
                                  "Cannot access the selected window. Please refresh the list and try again.")
                return
            
            self.update_status(f"✅ Selected window: {window.title} - Background capture mode", "green")
            self.update_task_progress(30, "Window validated")
            
            # Step 2: Take background screenshot (no activation)
            self.update_task_progress(40, "Taking background screenshot")
            image_path = self.take_screenshot_background(window)
            if not image_path:
                self.complete_task(task_name, False)
                return
            
            self.update_task_progress(60, "Background screenshot captured")
            
            # Step 3: Process with OCR
            self.update_task_progress(70, "Starting OCR")
            self.process_with_ocr(image_path)
            
            # Update performance metrics for auto capture
            self.total_captures += 1
            self.auto_captures += 1
            processing_time = time.time() - capture_start_time
            self.total_processing_time += processing_time
            self.auto_processing_time += processing_time
            self.auto_capture_times.append(processing_time)
            
            # Keep only last 50 measurements
            if len(self.auto_capture_times) > 50:
                self.auto_capture_times = self.auto_capture_times[-50:]
            
            self.complete_task(task_name, True)
            
        except Exception as e:
            self.update_status(f"❌ Background capture failed: {str(e)}", "red")
            self.complete_task(task_name, False)
    
    def capture_selected_window(self):
        """Capture the selected window with USB stability fix and navigation alerts"""
        # Start performance tracking
        capture_start_time = time.time()
        
        # Add task to navigation queue
        task_name = "Manual Screenshot Capture"
        self.add_task_to_queue(task_name)
        self.start_task(task_name)
        
        self.update_status("🔍 Getting selected window...", "blue")
        self.update_task_progress(10, "Getting window")
        
        # DISABLE ALL TIMERS AND OPERATIONS TO PREVENT USB DISCONNECTION
        self.pause_all_operations()
        
        try:
            # Step 1: Get selected window
            window = self.get_selected_window()
            if not window:
                current_text = self.window_combo.currentText()
                if "Select a window" in current_text or "No windows found" in current_text:
                    self.update_status("❌ Please select a valid window first", "red")
                    self.complete_task(task_name, False)
                    QMessageBox.warning(self, "No Window Selected", 
                                      "Please select a valid window from the dropdown list.\n\n" +
                                      "If you don't see your device window:\n" +
                                      "1. Make sure your device/app is running\n" +
                                      "2. Click the 'Refresh' button\n" +
                                      "3. Look for your device in the Mobile/Device section")
                else:
                    self.update_status("❌ Invalid window selection", "red")
                    self.complete_task(task_name, False)
                    QMessageBox.warning(self, "Invalid Selection", 
                                      "The selected item is not a valid window. Please choose a window from the list.")
                return
            
            self.update_task_progress(20, "Validating window")
            
            # Verify window is still valid
            try:
                if not window.visible or window.width <= 0 or window.height <= 0:
                    self.update_status("❌ Selected window is no longer valid", "red")
                    self.complete_task(task_name, False)
                    QMessageBox.warning(self, "Window Not Available", 
                                      "The selected window is no longer available. Please refresh the list and select again.")
                    return
            except:
                self.update_status("❌ Selected window is no longer accessible", "red")
                self.complete_task(task_name, False)
                QMessageBox.warning(self, "Window Error", 
                                  "Cannot access the selected window. Please refresh the list and try again.")
                return
            
            self.update_status(f"✅ Selected window: {window.title}", "green")
            self.update_task_progress(30, "Window validated")
            
            # Step 2: Take screenshot with minimal file operations
            self.update_task_progress(40, "Taking screenshot")
            image_path = self.take_screenshot_safe(window)
            if not image_path:
                self.complete_task(task_name, False)
                return
            
            self.update_task_progress(60, "Screenshot captured")
            
            # Step 3: Process with OCR (minimal operations)
            self.update_task_progress(70, "Starting OCR")
            self.process_with_ocr_safe(image_path, task_name)
            
            # Update performance metrics for manual capture
            self.total_captures += 1
            self.manual_captures += 1
            processing_time = time.time() - capture_start_time
            self.total_processing_time += processing_time
            self.manual_processing_time += processing_time
            self.manual_capture_times.append(processing_time)
            
            # Keep only last 50 measurements
            if len(self.manual_capture_times) > 50:
                self.manual_capture_times = self.manual_capture_times[-50:]
            
        except Exception as e:
            self.update_status(f"❌ Capture failed: {str(e)}", "red")
            self.complete_task(task_name, False)
            
        finally:
            # ALWAYS RESUME OPERATIONS
            self.resume_all_operations()
    
    def capture_data(self):
        """Legacy method - redirects to capture_selected_window"""
        self.capture_selected_window()
    
    def auto_capture(self):
        """Perform automatic capture with USB stability management - Uses background capture by default"""
        if self.auto_checkbox.isChecked():
            # Check if a window is selected before auto-capturing
            window = self.get_selected_window()
            if window:
                # Optimize USB stability for the selected device
                if hasattr(self, 'usb_stability_manager'):
                    self.usb_stability_manager.optimize_for_device(window.title)
                    
                    # Check if we should skip this operation for USB stability
                    if self.usb_stability_manager.should_skip_operation('auto_capture'):
                        self.update_status("🔌 Auto-capture skipped for USB stability", "blue")
                        return
                
                # Use background capture for auto-capture to avoid interrupting user workflow
                self.capture_background_window()
            else:
                self.update_status("⚠️ Auto-capture skipped: No window selected", "orange")
    
    def toggle_auto_capture(self, state):
        """Toggle auto-capture timer"""
        if state == Qt.Checked:
            interval = self.interval_spinbox.value() * 1000  # Convert to milliseconds
            if interval > 0:  # Ensure valid interval
                self.auto_timer.start(interval)
                self.update_status(f"🔄 Auto-capture enabled (every {self.interval_spinbox.value()}s)", "blue")
                self.stop_auto_btn.setEnabled(True)  # Enable stop button
            else:
                self.auto_checkbox.setChecked(False)  # Uncheck if invalid interval
                self.update_status(f"❌ Invalid interval: {self.interval_spinbox.value()}s", "red")
        else:
            self.auto_timer.stop()
            self.update_status("⏹️ Auto-capture disabled", "orange")
            self.stop_auto_btn.setEnabled(False)  # Disable stop button
    
    def stop_auto_capture(self):
        """Stop auto-capture and uncheck the checkbox"""
        self.auto_timer.stop()
        self.auto_checkbox.setChecked(False)  # This will trigger toggle_auto_capture
        self.update_status("⏹️ Auto-capture stopped by user", "orange")
    
    def update_capture_interval(self, value):
        """Update the capture interval when spinbox value changes"""
        if self.auto_timer.isActive():
            # If auto-capture is running, restart the timer with new interval
            interval = value * 1000  # Convert to milliseconds
            if interval > 0:
                self.auto_timer.stop()
                self.auto_timer.start(interval)
                self.update_status(f"🔄 Auto-capture interval updated to {value}s", "blue")
            else:
                self.auto_timer.stop()
                self.auto_checkbox.setChecked(False)
                self.update_status(f"❌ Invalid interval: {value}s", "red")
    
    def toggle_usb_stability(self, state):
        """Toggle USB stability mode (screenshot auto-deletion)"""
        self.enable_auto_delete_screenshots = (state == Qt.Checked)
        
        if self.enable_auto_delete_screenshots:
            deletion_mode = self.deletion_mode_combo.currentData()
            if deletion_mode == "time":
                interval = self.deletion_interval_spinbox.value()
                self.update_status(f"🔌 Screenshot auto-deletion enabled (every {interval} minutes)", "orange")
                print(f"DEBUG: USB stability mode disabled - screenshots will be auto-deleted every {interval} minutes")
            else:
                count = self.deletion_interval_spinbox.value()
                self.update_status(f"🔌 Screenshot auto-deletion enabled (keep last {count} files)", "orange")
                print(f"DEBUG: USB stability mode disabled - will keep last {count} screenshots")
        else:
            self.update_status(f"💾 Screenshots will be preserved (USB stability mode enabled)", "green")
            print("DEBUG: USB stability mode enabled - screenshots will be preserved")
    
    def update_deletion_mode(self):
        """Update the deletion mode interface when user changes selection"""
        mode = self.deletion_mode_combo.currentData()
        if mode == "time":
            self.deletion_interval_spinbox.setRange(1, 1440)  # 1 minute to 24 hours
            self.deletion_interval_spinbox.setValue(60)  # Default to 60 minutes
            self.deletion_interval_spinbox.setSuffix(" minutes")
            self.deletion_interval_spinbox.setToolTip("Screenshots older than this time will be automatically deleted")
        else:  # count mode
            self.deletion_interval_spinbox.setRange(1, 100)  # Keep 1 to 100 files
            self.deletion_interval_spinbox.setValue(5)  # Default to keep last 5 files
            self.deletion_interval_spinbox.setSuffix(" files")
            self.deletion_interval_spinbox.setToolTip("Number of most recent screenshots to keep")
        
        # Update status if auto-deletion is enabled
        if hasattr(self, 'enable_auto_delete_screenshots') and self.enable_auto_delete_screenshots:
            self.toggle_usb_stability(Qt.Checked)
    
    def toggle_usb_stability_mode(self):
        """Toggle between maximum USB stability mode and fast mode"""
        if hasattr(self, 'usb_stability_manager'):
            if self.usb_stability_btn.isChecked():
                self.usb_stability_manager.enable_stability_mode()
                self.usb_stability_btn.setText("🔌 Max USB Stability")
                self.update_status("🔌 Maximum USB stability mode enabled - prevents disconnections", "green")
            else:
                self.usb_stability_manager.disable_stability_mode()
                self.usb_stability_btn.setText("⚡ Fast Mode")
                self.update_status("⚡ Fast mode enabled - faster operations but may cause USB issues", "orange")
        else:
            self.update_status("⚠️ USB Stability Manager not available", "red")
    
    # launch_background_service method removed to prevent unwanted background captures
    
    def export_last_result_to_csv(self):
        """Export the last OCR result to CSV manually"""
        if not hasattr(self, 'last_ocr_result') or not self.last_ocr_result:
            QMessageBox.warning(self, "No Data", "No OCR result available to export. Please capture a window first.")
            return
        
        try:
            raw_text = self.last_ocr_result['raw_text']
            timestamp = self.last_ocr_result['timestamp']
            image_path = self.last_ocr_result.get('image_path', None)
            
            # Save to CSV (without auto-deleting screenshot for manual export)
            self.save_to_csv(raw_text, timestamp, None)  # Don't delete screenshot for manual export
            
            # Show success message
            csv_path = os.path.join(self.csv_dir, "auto_data.csv")
            QMessageBox.information(self, "Export Successful", 
                                  f"Raw data exported to CSV successfully!\n\nFile location:\n{csv_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export to CSV:\n{str(e)}")
    
    def export_last_result_to_json(self):
        """Export the last OCR result to JSON file"""
        if not hasattr(self, 'last_ocr_result') or not self.last_ocr_result:
            QMessageBox.warning(self, "No Data", "No OCR result available to export. Please capture a window first.")
            return
        
        try:
            # Create JSON export data
            export_data = {
                'timestamp': self.last_ocr_result['timestamp'],
                'window_title': self.get_selected_window().title if self.get_selected_window() else "Unknown",
                'raw_text': self.last_ocr_result['raw_text'],
                'full_ocr_result': self.last_ocr_result['result'],
                'image_path': self.last_ocr_result.get('image_path', None)
            }
            
            # Generate filename
            timestamp_safe = self.last_ocr_result['timestamp'].replace(':', '-').replace(' ', '_')
            json_filename = f"ocr_export_{timestamp_safe}.json"
            json_path = os.path.join(self.json_dir, json_filename)
            
            # Write JSON file
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json.dump(export_data, json_file, indent=2, ensure_ascii=False)
            
            # Show success message
            QMessageBox.information(self, "Export Successful", 
                                  f"OCR data exported to JSON successfully!\n\nFile location:\n{json_path}")
            
            self.update_status(f"📄 JSON exported: {json_filename}", "green")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export to JSON:\n{str(e)}")
    
    def clear_results(self):
        """Clear the results preview and reset UI"""
        self.ocr_status_label.setText("No OCR results yet. Capture a window to see results.")
        self.ocr_status_label.setStyleSheet("""
            QLabel {
                color: #888;
                padding: 20px;
                text-align: center;
                background: rgba(255, 255, 255, 0.05);
                border: 2px dashed #555;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        self.quick_stats_label.setText("")
        self.csv_export_btn.setEnabled(False)
        self.json_export_btn.setEnabled(False)
        self.view_details_btn.setEnabled(False)
        self.last_ocr_result = None
        self.update_status("Results cleared", "blue")
    
    def show_output_details_dialog(self):
        """Show the enhanced output details dialog"""
        if not self.last_ocr_result:
            self.update_status("No output to display", "orange")
            return
        
        raw_text = self.last_ocr_result.get('raw_text', '')
        ocr_result = self.last_ocr_result.get('result', {})
        
        dialog = OutputDetailsDialog(self, raw_text, ocr_result)
        dialog.exec_()
        self.json_export_btn.setEnabled(False)
        
        # Clear last result
        if hasattr(self, 'last_ocr_result'):
            self.last_ocr_result = None
    
    def zoom_in(self):
        """Zoom in the main application"""
        if self.zoom_level < 2.0:  # Max zoom 200%
            self.zoom_level += 0.1
            self.apply_zoom()
            self.update_status(f"🔍 Zoomed in to {int(self.zoom_level * 100)}%", "blue")
    
    def zoom_out(self):
        """Zoom out the main application"""
        if self.zoom_level > 0.5:  # Min zoom 50%
            self.zoom_level -= 0.1
            self.apply_zoom()
            self.update_status(f"🔍 Zoomed out to {int(self.zoom_level * 100)}%", "blue")
    
    def apply_zoom(self):
        """Apply zoom level to the main application"""
        # Update zoom label
        self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
        
        # Apply zoom transformation to the central widget
        transform = QTransform()
        transform.scale(self.zoom_level, self.zoom_level)
        
        # Get the central widget and apply transformation
        central_widget = self.centralWidget()
        if central_widget:
            # Create a graphics effect for zoom
            font = central_widget.font()
            original_size = 9  # Base font size
            new_size = int(original_size * self.zoom_level)
            font.setPointSize(max(6, min(new_size, 24)))  # Clamp between 6 and 24
            
            # Apply font changes to main elements
            for widget in central_widget.findChildren(QWidget):
                if hasattr(widget, 'setFont'):
                    widget_font = widget.font()
                    if widget_font.pointSize() > 0:
                        base_size = 9 if widget_font.pointSize() <= 12 else 12
                        new_widget_size = int(base_size * self.zoom_level)
                        widget_font.setPointSize(max(6, min(new_widget_size, 24)))
                        widget.setFont(widget_font)
    
    def open_developer_website(self):
        """Open developer website in default browser"""
        import webbrowser
        developer_url = "https://github.com/anas-gulzar-dev/grace/"  # Replace with actual URL
        try:
            webbrowser.open(developer_url)
            self.update_status("🌐 Developer website opened in browser", "blue")
        except Exception as e:
            QMessageBox.information(self, "Developer Info", 
                                  f"Developer Website: {developer_url}\n\n" +
                                  "Please copy and paste this URL into your browser.\n\n" +
                                  f"Error opening automatically: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.auto_timer.isActive():
            self.auto_timer.stop()
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
        if self.ocr_worker and self.ocr_worker.isRunning():
            self.ocr_worker.quit()
            self.ocr_worker.wait()
        event.accept()


def main():
    """
    Main application entry point for Grace Biosensor Data Capture.
    
    Initializes the cross-platform PyQt5 application, performs dependency checks,
    and launches the main biosensor data capture interface.
    
    Features:
    • Cross-platform compatibility (Windows, macOS, Linux)
    • Automatic dependency validation
    • Modern UI with dark theme support
    • Platform-specific optimizations
    
    Returns:
        int: Application exit code
    """
    app = QApplication(sys.argv)
    
    # Set application properties for cross-platform compatibility
    app.setApplicationName("Grace Biosensor Data Capture")
    app.setApplicationVersion("2.0.0")  # Cross-Platform Edition
    app.setApplicationDisplayName("Grace Biosensor Data Capture - Cross-Platform Edition")
    app.setOrganizationName("Anas Gulzar Dev")
    app.setOrganizationDomain("github.com/anas-gulzar-dev")
    
    # Platform detection for startup optimizations
    platform_info = f"Running on {PLATFORM.title()}"
    if WINDOW_MANAGER_AVAILABLE:
        platform_info += " with window management support"
    print(f"🚀 {platform_info}")
    
    # Create and show main window
    window = BiosensorApp()
    window.show()
    
    # Cross-platform dependency validation
    missing_deps = []
    missing_features = []
    
    if not requests:
        missing_deps.append("requests")
    
    if not WINDOW_MANAGER_AVAILABLE:
        missing_features.append("Window management (install PyWinCtl)")
    
    if PLATFORM == 'windows' and not DXCAM_AVAILABLE:
        missing_features.append("DXcam acceleration (optional)")
    
    if PLATFORM == 'linux' and not LINUX_TOOLS_AVAILABLE:
        missing_features.append("Linux window tools (install xdotool, wmctrl)")
    
    # Show dependency warnings if any
    if missing_deps or missing_features:
        warning_msg = "⚠️ Some dependencies or features are missing:\n\n"
        
        if missing_deps:
            warning_msg += f"Critical dependencies: {', '.join(missing_deps)}\n"
            warning_msg += "Install with: pip install " + " ".join(missing_deps) + "\n\n"
        
        if missing_features:
            warning_msg += f"Optional features: {', '.join(missing_features)}\n"
            warning_msg += "For full installation, run: python install_universal.py\n\n"
        
        warning_msg += "The application will continue with limited functionality."
        
        QMessageBox.information(
            window, 
            "Dependency Check - Grace Biosensor Data Capture", 
            warning_msg
        )
    
    # Start the application event loop
    return sys.exit(app.exec_())


if __name__ == "__main__":
    main()
