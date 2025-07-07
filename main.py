import sys
import os
import json
import time
import random
import csv
import glob
from datetime import datetime
from typing import Optional, Dict, Any

import pygetwindow as gw
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

try:
    import dxcam
    DXCAM_AVAILABLE = True
except ImportError:
    DXCAM_AVAILABLE = False
    print("DXcam not available, using MSS fallback")

try:
    from config import (
        AZURE_API_KEY, AZURE_ENDPOINT, DEFAULT_CAPTURE_INTERVAL,
        SCREENSHOTS_FOLDER, SCRCPY_WINDOW_TITLES, OCR_LANGUAGE, DETECT_ORIENTATION
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
        """Refresh the device list"""
        try:
            # Get updated device list
            all_windows = gw.getAllWindows()
            self.device_list = []
            
            for window in all_windows:
                if window.title and window.title.strip():
                    if window.title not in ['Program Manager', 'Desktop Window Manager']:
                        self.device_list.append(window)
            
            # Update table
            self.device_table.setRowCount(len(self.device_list))
            
            for i, window in enumerate(self.device_list):
                self.device_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                
                name_item = QTableWidgetItem(window.title)
                name_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.device_table.setItem(i, 1, name_item)
                
                size_text = f"{window.width} x {window.height}"
                self.device_table.setItem(i, 2, QTableWidgetItem(size_text))
                
                pos_text = f"({window.left}, {window.top})"
                self.device_table.setItem(i, 3, QTableWidgetItem(pos_text))
                
                visible_text = "✅ Yes" if window.visible else "❌ No"
                visible_item = QTableWidgetItem(visible_text)
                if window.visible:
                    visible_item.setForeground(QColor("green"))
                else:
                    visible_item.setForeground(QColor("red"))
                self.device_table.setItem(i, 4, visible_item)
            
            # Update count label
            count_label = self.findChild(QLabel)
            if count_label:
                for child in self.findChildren(QLabel):
                    if "Total Devices Found" in child.text():
                        child.setText(f"🎯 Total Devices Found: {len(self.device_list)}")
                        break
            
            self.device_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh devices: {str(e)}")


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


class BiosensorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔬 Biosensor Data Capture - Professional Edition")
        self.setGeometry(100, 100, 1200, 800)
        
        # Theme management
        self.is_dark_theme = True  # Start with dark theme
        
        # Zoom management
        self.zoom_level = 1.0  # Start with 100% zoom
        
        # Apply modern styling
        self.apply_modern_styling()
        
        # Create screenshots directory
        self.screenshots_dir = SCREENSHOTS_FOLDER
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Timer for auto-capture
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.auto_capture)
        
        # Timer for auto-refresh (detect new devices)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_windows)
        self.refresh_timer.start(3000)  # Auto-refresh every 3 seconds for faster detection
        
        # Timer for automatic device detection and UI updates
        self.device_detection_timer = QTimer()
        self.device_detection_timer.timeout.connect(self.auto_detect_devices)
        self.device_detection_timer.start(2000)  # Check for new devices every 2 seconds
        
        # Store last known device count for change detection
        self.last_device_count = 0
        
        # OCR worker thread
        self.ocr_worker = None
        
        # Azure OCR settings from config
        self.azure_api_key = AZURE_API_KEY
        self.azure_endpoint = AZURE_ENDPOINT
        
        # Store last OCR result for manual export
        self.last_ocr_result = None
        
        self.init_ui()
    
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
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
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
        
        window_layout.addLayout(window_select_layout)
        main_layout.addWidget(window_group)
        
        # Control panel
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout(control_group)
        
        # Main controls row
        main_controls = QHBoxLayout()
        
        # Capture button with modern styling
        self.capture_btn = QPushButton()
        if MODERN_UI_AVAILABLE:
            self.capture_btn.setIcon(qta.icon('fa5s.camera', color='white'))
        self.capture_btn.setText("📸 Capture Selected Window")
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
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #3d8b40, stop: 1 #2e7d32);
            }
        """)
        self.capture_btn.clicked.connect(self.capture_selected_window)
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
                box-shadow: 0 3px 8px rgba(255, 87, 34, 0.4);
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
        
        # Note about auto-capture
        auto_note = QLabel("Note: Auto-capture will use the currently selected window")
        auto_note.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
        control_layout.addWidget(auto_note)
        
        # Background service note removed
        main_layout.addWidget(control_group)
        
        # Status section
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("🟡 Ready to capture")
        self.status_label.setFont(QFont("Arial", 12))
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(status_group)
        
        # Results section
        results_group = QGroupBox("OCR Results")
        results_layout = QVBoxLayout(results_group)
        
        # Result format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Display Format:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItem("📋 Raw Text Only", "raw")
        self.format_combo.addItem("📊 JSON Only", "json")
        self.format_combo.addItem("📋📊 Both (Raw + JSON)", "both")
        self.format_combo.setCurrentIndex(2)  # Default to both
        format_layout.addWidget(self.format_combo)
        
        format_layout.addStretch()
        results_layout.addLayout(format_layout)
        
        self.results_text = QTextEdit()
        self.results_text.setFont(QFont("Consolas", 10))
        self.results_text.setPlaceholderText("OCR results will appear here...")
        results_layout.addWidget(self.results_text)
        
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
                box-shadow: 0 3px 8px rgba(244, 67, 54, 0.4);
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
                box-shadow: 0 3px 8px rgba(33, 150, 243, 0.4);
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
                box-shadow: 0 3px 8px rgba(255, 152, 0, 0.4);
            }
            QPushButton:disabled {
                background: #666;
                color: #999;
            }
        """)
        self.json_export_btn.setEnabled(False)  # Initially disabled
        buttons_layout.addWidget(self.json_export_btn)
        
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
                box-shadow: 0 3px 8px rgba(255, 87, 34, 0.4);
            }
        """)
        buttons_layout.addWidget(self.instant_device_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Set the central widget
        self.setCentralWidget(central_widget)
        
        # Initialize window list after all UI elements are created
        self.refresh_windows()
    
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
        """Discover and categorize all newer devices connected to the system"""
        device_info = {
            'mobile_phones': [],
            'tablets': [],
            'wearables': [],
            'emulators': [],
            'dev_tools': [],
            'unknown_devices': []
        }
        
        try:
            all_windows = gw.getAllWindows()
            device_keywords = self.get_newer_device_keywords()
            
            for window in all_windows:
                if not window.title or not window.title.strip():
                    continue
                    
                title_lower = window.title.lower()
                
                # Check if it matches any device keyword
                matched_keywords = [kw for kw in device_keywords if kw in title_lower]
                
                if matched_keywords:
                    device_entry = {
                        'title': window.title,
                        'size': f"{window.width}x{window.height}",
                        'position': f"({window.left}, {window.top})",
                        'visible': window.visible,
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
            print(f"DEBUG: Error in device discovery: {e}")
            
        return device_info
    
    def show_all_devices_instantly(self):
        """Show ALL devices instantly in a separate dialog window - no filtering!"""
        try:
            # Get ALL windows immediately
            all_windows = gw.getAllWindows()
            device_list = []
            
            for window in all_windows:
                if window.title and window.title.strip():
                    # Skip only the most basic system windows
                    if window.title not in ['Program Manager', 'Desktop Window Manager']:
                        device_list.append(window)
            
            # Create and show the instant device dialog
            dialog = InstantDeviceDialog(device_list, self)
            dialog.exec_()
            
            # Update status
            self.update_status(f"📱 Displayed {len(device_list)} devices in separate window!", "green")
            
            # Also refresh the combo box
            self.refresh_windows()
            
        except Exception as e:
            self.update_status(f"❌ Error showing devices: {str(e)}", "red")
    
    def get_all_windows(self) -> list:
        """Get ALL windows without any filtering - show everything instantly"""
        try:
            all_windows = gw.getAllWindows()
            visible_windows = []
            
            print(f"DEBUG: Processing {len(all_windows)} total windows...")
            
            for window in all_windows:
                try:
                    # Only skip completely empty titles
                    if not window.title or not window.title.strip():
                        continue
                    
                    # Skip only the most basic system windows
                    if window.title in ['Program Manager', 'Desktop Window Manager']:
                        continue
                    
                    # Add ALL other windows - no filtering!
                    if window.width > 0 and window.height > 0:
                        visible_windows.append(window)
                        print(f"DEBUG: Added window: {window.title} ({window.width}x{window.height})")
                            
                except Exception as window_error:
                    print(f"DEBUG: Error processing window: {window_error}")
                    continue
            
            # Sort windows by title
            visible_windows.sort(key=lambda w: w.title.lower())
            print(f"DEBUG: Total windows found: {len(visible_windows)}")
            return visible_windows
            
        except Exception as e:
            self.update_status(f"❌ Error getting windows: {str(e)}", "red")
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
    
    def get_selected_window(self) -> Optional[gw.Win32Window]:
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
        """Bring window to foreground and ensure it's visible"""
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
                
        except Exception as e:
            self.update_status(f"⚠️ Could not activate window: {str(e)}", "orange")
            return True  # Still try to capture
    
    def take_screenshot(self, window) -> Optional[str]:
        """Take screenshot with automatic window activation"""
        try:
            # Step 1: Activate the window to bring it to foreground
            self.update_status("🔄 Activating target window...", "blue")
            self.activate_window(window)
            
            # Step 2: Refresh window position (in case it moved)
            try:
                window_list = gw.getWindowsWithTitle(window.title)
                for w in window_list:
                    if w.visible and w.width > 0 and w.height > 0:
                        window = w  # Use updated window object
                        break
            except:
                pass  # Use original window if refresh fails
            
            # Step 3: Validate window region
            if window.width <= 0 or window.height <= 0:
                self.update_status("❌ Invalid window dimensions", "red")
                return None
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_num = random.randint(1000, 9999)
            filename = f"screenshot_{timestamp}_{random_num}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            self.update_status(f"📸 Capturing window: {window.title} ({window.width}x{window.height})", "blue")
            
            # Method 1: Try DXcam (fastest, Windows Desktop Duplication API)
            if DXCAM_AVAILABLE:
                try:
                    camera = dxcam.create()
                    if camera:
                        region = (window.left, window.top, 
                                window.left + window.width, 
                                window.top + window.height)
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
                        "top": window.top,
                        "left": window.left,
                        "width": window.width,
                        "height": window.height
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
            
            # Method 3: Fallback to pyautogui with window activation
            try:
                # Additional wait to ensure window is ready
                time.sleep(0.5)
                
                left, top, width, height = window.left, window.top, window.width, window.height
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
            
            self.update_status("❌ All capture methods failed", "red")
            return None
            
        except Exception as e:
            self.update_status(f"❌ Screenshot failed: {str(e)}", "red")
            return None
    
    def process_with_ocr(self, image_path: str):
        """Process image with Azure OCR API"""
        if not self.azure_api_key:
            self.update_status("❌ Azure API key not configured", "red")
            self.results_text.append("\n⚠️ Please configure your Azure Computer Vision API key and endpoint in your .env file.")
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
        
        # Get selected display format
        display_format = self.format_combo.currentData()
        
        # Display results based on selected format
        self.results_text.append(f"\n{'='*50}")
        self.results_text.append(f"OCR Result - {timestamp}")
        self.results_text.append(f"{'='*50}")
        
        if display_format in ["raw", "both"]:
            self.results_text.append("\n📋 RAW TEXT:")
            self.results_text.append("-" * 30)
            if raw_text.strip():
                self.results_text.append(raw_text)
            else:
                self.results_text.append("(No text detected)")
        
        if display_format in ["json", "both"]:
            if display_format == "both":
                self.results_text.append("\n📊 FULL JSON DATA:")
                self.results_text.append("-" * 30)
            formatted_json = json.dumps(result, indent=2, ensure_ascii=False)
            self.results_text.append(formatted_json)
        
        self.results_text.append(f"{'='*50}\n")
        
        # Save to CSV based on capture mode
        image_path = getattr(self, 'current_image_path', None)
        if self.auto_checkbox.isChecked():
            # Auto-capture mode: save to auto_data.csv and JSON
            self.save_auto_data(raw_text, timestamp, image_path)
        else:
            # Manual capture mode: save to single_screenshot_time.csv
            self.save_manual_capture(raw_text, timestamp, image_path)
        
        # Auto-scroll to bottom
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.End)
        self.results_text.setTextCursor(cursor)
    
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
            csv_file_path = os.path.join(self.screenshots_dir, "auto_data.csv")
            
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
            manual_dir = os.path.join(self.screenshots_dir, "manual_captures")
            os.makedirs(manual_dir, exist_ok=True)
            
            # Get window title
            window = self.get_selected_window()
            window_title = window.title if window else "Unknown"
            
            # Save to separate CSV file for manual captures with dynamic filename
            timestamp_safe = timestamp.replace(':', '-').replace(' ', '_')
            csv_filename = f"manual_capture_{timestamp_safe}.csv"
            csv_path = os.path.join(manual_dir, csv_filename)
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
                json_path = os.path.join(manual_dir, json_filename)
                
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
        """Clean up old screenshots, keeping only the last 5 files"""
        try:
            # Get all screenshot files in the screenshots directory
            screenshot_patterns = [
                os.path.join(self.screenshots_dir, "*.png"),
                os.path.join(self.screenshots_dir, "*.jpg"),
                os.path.join(self.screenshots_dir, "*.jpeg"),
                os.path.join(self.screenshots_dir, "*.bmp")
            ]
            
            all_screenshots = []
            for pattern in screenshot_patterns:
                all_screenshots.extend(glob.glob(pattern))
            
            if len(all_screenshots) <= 5:
                return  # No cleanup needed
            
            # Sort by modification time (newest first)
            all_screenshots.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Keep only the first 5 (newest), delete the rest
            screenshots_to_delete = all_screenshots[5:]
            
            deleted_count = 0
            for screenshot_path in screenshots_to_delete:
                try:
                    os.remove(screenshot_path)
                    deleted_count += 1
                    print(f"DEBUG: Cleaned up old screenshot: {os.path.basename(screenshot_path)}")
                except Exception as delete_error:
                    print(f"DEBUG: Failed to delete old screenshot {screenshot_path}: {delete_error}")
            
            if deleted_count > 0:
                self.update_status(f"🧹 Cleaned up {deleted_count} old screenshots (keeping last 5)", "blue")
                
        except Exception as e:
            print(f"DEBUG: Screenshot cleanup error: {e}")
            self.update_status(f"⚠️ Screenshot cleanup warning: {str(e)}", "orange")
    
    def save_auto_data(self, raw_text: str, timestamp: str, image_path: str = None):
        """Save data to both CSV and JSON files when auto-capture is active"""
        try:
            # Get window title
            window = self.get_selected_window()
            window_title = window.title if window else "Unknown"
            
            # Save to CSV
            csv_path = os.path.join(self.screenshots_dir, "auto_data.csv")
            file_exists = os.path.exists(csv_path)
            
            csv_data = {
                'timestamp': timestamp,
                'window_title': window_title,
                'raw_text': raw_text.replace('\n', ' | ') if raw_text.strip() else 'No text detected'
            }
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'window_title', 'raw_text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(csv_data)
            
            # Save to JSON
            if hasattr(self, 'last_ocr_result') and self.last_ocr_result:
                export_data = {
                    'timestamp': timestamp,
                    'window_title': window_title,
                    'raw_text': raw_text,
                    'full_ocr_result': self.last_ocr_result['result'],
                    'image_path': image_path
                }
                
                timestamp_safe = timestamp.replace(':', '-').replace(' ', '_')
                json_filename = f"auto_capture_{timestamp_safe}.json"
                json_path = os.path.join(self.screenshots_dir, json_filename)
                
                with open(json_path, 'w', encoding='utf-8') as json_file:
                    json.dump(export_data, json_file, indent=2, ensure_ascii=False)
                
                self.update_status(f"💾 Auto-saved to CSV and JSON: {os.path.basename(csv_path)}, {json_filename}", "green")
            else:
                self.update_status(f"💾 Auto-saved to CSV: {os.path.basename(csv_path)}", "green")
            
            # Clean up old screenshots (keep only last 5)
            self.cleanup_old_screenshots()
            
            # Delete current screenshot if provided and exists
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"DEBUG: Screenshot deleted successfully: {image_path}")
                    self.update_status(f"🗑️ Screenshot auto-deleted: {os.path.basename(image_path)}", "gray")
                except Exception as delete_error:
                    print(f"DEBUG: Failed to delete screenshot: {image_path}, Error: {delete_error}")
            else:
                print(f"DEBUG: Screenshot not deleted - path: {image_path}, exists: {os.path.exists(image_path) if image_path else 'N/A'}")
            
        except Exception as e:
            self.update_status(f"❌ Failed to save auto data: {str(e)}", "red")
    
    def on_ocr_error(self, error_message: str):
        """Handle OCR error"""
        self.progress_bar.setVisible(False)
        self.update_status(f"❌ OCR Error", "red")
        self.results_text.append(f"\n❌ OCR Error: {error_message}\n")
    
    def capture_selected_window(self):
        """Capture the selected window"""
        self.update_status("🔍 Getting selected window...", "blue")
        
        # Step 1: Get selected window
        window = self.get_selected_window()
        if not window:
            current_text = self.window_combo.currentText()
            if "Select a window" in current_text or "No windows found" in current_text:
                self.update_status("❌ Please select a valid window first", "red")
                QMessageBox.warning(self, "No Window Selected", 
                                  "Please select a valid window from the dropdown list.\n\n" +
                                  "If you don't see your device window:\n" +
                                  "1. Make sure your device/app is running\n" +
                                  "2. Click the 'Refresh' button\n" +
                                  "3. Look for your device in the Mobile/Device section")
            else:
                self.update_status("❌ Invalid window selection", "red")
                QMessageBox.warning(self, "Invalid Selection", 
                                  "The selected item is not a valid window. Please choose a window from the list.")
            return
        
        # Verify window is still valid
        try:
            if not window.visible or window.width <= 0 or window.height <= 0:
                self.update_status("❌ Selected window is no longer valid", "red")
                QMessageBox.warning(self, "Window Not Available", 
                                  "The selected window is no longer available. Please refresh the list and select again.")
                return
        except:
            self.update_status("❌ Selected window is no longer accessible", "red")
            QMessageBox.warning(self, "Window Error", 
                              "Cannot access the selected window. Please refresh the list and try again.")
            return
        
        self.update_status(f"✅ Selected window: {window.title}", "green")
        
        # Step 2: Take screenshot
        image_path = self.take_screenshot(window)
        if not image_path:
            return
        
        # Step 3: Process with OCR
        self.process_with_ocr(image_path)
    
    def capture_data(self):
        """Legacy method - redirects to capture_selected_window"""
        self.capture_selected_window()
    
    def auto_capture(self):
        """Perform automatic capture"""
        if self.auto_checkbox.isChecked():
            # Check if a window is selected before auto-capturing
            window = self.get_selected_window()
            if window:
                self.capture_selected_window()
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
            csv_path = os.path.join(self.screenshots_dir, "auto_data.csv")
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
            json_path = os.path.join(self.screenshots_dir, json_filename)
            
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
        """Clear the results text area"""
        self.results_text.clear()
        self.update_status("🗑️ Results cleared", "gray")
        
        # Disable export buttons when results are cleared
        self.csv_export_btn.setEnabled(False)
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
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Biosensor Data Capture")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = BiosensorApp()
    window.show()
    
    # Check for required dependencies
    missing_deps = []
    if not requests:
        missing_deps.append("requests")
    
    if missing_deps:
        QMessageBox.information(
            window, 
            "Missing Dependencies", 
            f"Please install missing dependencies:\npip install {' '.join(missing_deps)}"
        )
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
