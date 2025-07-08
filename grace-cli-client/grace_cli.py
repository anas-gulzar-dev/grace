#!/usr/bin/env python3
"""
Grace Biosensor Data Capture - CLI Edition

A beautiful, fully-functional command-line interface for biosensor data capture
with cross-platform window detection, screenshot capture, Azure OCR integration,
and real-time data export capabilities.

Features:
• Beautiful CLI interface using Rich and Textual
• Cross-platform window detection and management
• Multi-method screenshot capture (DXcam, MSS, PyAutoGUI)
• Azure Computer Vision OCR integration
• Real-time device discovery and categorization
• Automated and manual data capture modes
• CSV and JSON data export
• Live status updates and progress indicators
• Interactive device selection and management

Author: Anas Gulzar Dev
Version: 2.0.0 CLI Edition
"""

import os
import sys
import time
import json
import csv
import glob
import random
import asyncio
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# Rich imports for beautiful CLI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.tree import Tree
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
from rich import box
from rich.status import Status

# Textual imports for advanced TUI
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Button, Static, Input, Select, 
    Checkbox, ProgressBar, TextArea, DataTable, Tree as TextualTree
)
from textual.reactive import reactive
from textual.message import Message
from textual.screen import Screen

# Click for command-line interface
import click
import typer

# Core functionality imports
try:
    import requests
except ImportError:
    requests = None
    print("⚠️ Warning: requests not available. OCR functionality will be limited.")

try:
    import pygetwindow as gw
    import pywinctl
    WINDOW_MANAGER_AVAILABLE = True
except ImportError:
    WINDOW_MANAGER_AVAILABLE = False
    gw = None
    pywinctl = None
    print("⚠️ Warning: Window management not available. Install PyWinCtl and pygetwindow.")

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None
    print("⚠️ Warning: pyautogui not available. Screenshot functionality will be limited.")

try:
    import mss
except ImportError:
    mss = None
    print("⚠️ Warning: mss not available. Fast screenshot functionality will be limited.")

try:
    from PIL import Image
except ImportError:
    Image = None
    print("⚠️ Warning: PIL not available. Image processing will be limited.")

try:
    import numpy as np
except ImportError:
    np = None
    print("⚠️ Warning: numpy not available. Advanced image processing will be limited.")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ Warning: python-dotenv not available. Using environment variables directly.")

# Platform detection
import platform
PLATFORM = platform.system().lower()

# Windows-specific imports
DXCAM_AVAILABLE = False
WIN32_AVAILABLE = False
if PLATFORM == 'windows':
    try:
        import dxcam
        DXCAM_AVAILABLE = True
    except ImportError:
        pass
    
    try:
        import win32gui
        import win32con
        import win32ui
        import ctypes
        from ctypes import windll, wintypes
        WIN32_AVAILABLE = True
        
        # Set DPI awareness to fix black screenshot issues
        try:
            # Try the newer SetProcessDpiAwarenessContext first
            windll.user32.SetProcessDpiAwarenessContext(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        except:
            try:
                # Fallback to SetProcessDpiAwareness
                windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except:
                try:
                    # Last resort - basic DPI awareness
                    windll.user32.SetProcessDPIAware()
                except:
                    pass  # DPI awareness failed, continue anyway
                    
    except ImportError:
        WIN32_AVAILABLE = False

# Linux-specific tools check
LINUX_TOOLS_AVAILABLE = False
if PLATFORM == 'linux':
    import subprocess
    try:
        subprocess.run(['which', 'xdotool'], check=True, capture_output=True)
        subprocess.run(['which', 'wmctrl'], check=True, capture_output=True)
        subprocess.run(['which', 'scrot'], check=True, capture_output=True)
        LINUX_TOOLS_AVAILABLE = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

# Initialize Rich console
console = Console()

# Global configuration
class Config:
    """Configuration management for Grace CLI"""
    
    def __init__(self):
        self.azure_endpoint = os.getenv('AZURE_COMPUTER_VISION_ENDPOINT', '')
        self.azure_key = os.getenv('AZURE_COMPUTER_VISION_KEY', '')
        self.screenshots_dir = Path('screenshots')
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Auto-capture settings
        self.auto_capture_enabled = False
        self.auto_capture_interval = 5  # seconds
        
        # UI settings
        self.show_debug = False
        self.max_screenshots = 5
        
    def is_azure_configured(self) -> bool:
        """Check if Azure OCR is properly configured"""
        return bool(self.azure_endpoint and self.azure_key)
    
    def validate_azure_config(self) -> tuple[bool, str]:
        """Validate Azure configuration"""
        if not self.azure_endpoint:
            return False, "Azure Computer Vision endpoint not configured"
        if not self.azure_key:
            return False, "Azure Computer Vision key not configured"
        if not requests:
            return False, "requests library not available"
        return True, "Azure configuration valid"

config = Config()

class WindowManager:
    """Cross-platform window management"""
    
    @staticmethod
    def get_all_windows() -> List[Any]:
        """Get all available windows"""
        if not WINDOW_MANAGER_AVAILABLE:
            return []
        
        try:
            all_windows = gw.getAllWindows()
            visible_windows = []
            
            # Platform-specific system window exclusions
            excluded_titles = ['Program Manager', 'Desktop Window Manager']  # Windows
            if PLATFORM == 'linux':
                excluded_titles.extend(['Desktop', 'Panel', 'Taskbar', 'Unity Panel', 'gnome-panel'])
            elif PLATFORM == 'darwin':  # macOS
                excluded_titles.extend(['Dock', 'Menu Bar', 'Spotlight'])
            
            for window in all_windows:
                if (window.title and window.title.strip() and 
                    window.title not in excluded_titles and
                    window.width > 0 and window.height > 0):
                    visible_windows.append(window)
            
            return sorted(visible_windows, key=lambda w: w.title.lower())
            
        except Exception as e:
            console.print(f"[red]Error getting windows: {e}[/red]")
            return []
    
    @staticmethod
    def categorize_windows(windows: List[Any]) -> Dict[str, List[Any]]:
        """Categorize windows by device type"""
        categories = {
            'mobile_phones': [],
            'tablets': [],
            'wearables': [],
            'emulators': [],
            'dev_tools': [],
            'browsers': [],
            'unknown_devices': []
        }
        
        for window in windows:
            title_lower = window.title.lower()
            
            if any(kw in title_lower for kw in ['phone', 'sm-', 'iphone', 'pixel', 'oneplus', 'xiaomi', 'huawei', 'oppo', 'vivo']):
                categories['mobile_phones'].append(window)
            elif any(kw in title_lower for kw in ['tablet', 'ipad', 'tab', 'surface']):
                categories['tablets'].append(window)
            elif any(kw in title_lower for kw in ['watch', 'band', 'fitbit', 'garmin', 'amazfit']):
                categories['wearables'].append(window)
            elif any(kw in title_lower for kw in ['emulator', 'bluestacks', 'nox', 'memu', 'ldplayer']):
                categories['emulators'].append(window)
            elif any(kw in title_lower for kw in ['scrcpy', 'adb', 'vysor', 'android studio']):
                categories['dev_tools'].append(window)
            elif any(kw in title_lower for kw in ['chrome', 'firefox', 'safari', 'edge', 'browser']):
                categories['browsers'].append(window)
            else:
                categories['unknown_devices'].append(window)
        
        return categories
    
    @staticmethod
    def activate_window(window: Any) -> bool:
        """Activate and bring window to foreground"""
        try:
            if PLATFORM == 'windows' and WIN32_AVAILABLE:
                hwnd = window._hWnd
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    time.sleep(0.2)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.3)
                return True
            
            elif PLATFORM == 'linux' and LINUX_TOOLS_AVAILABLE:
                result = subprocess.run(['xdotool', 'search', '--name', window.title], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    window_id = result.stdout.strip().split('\n')[0]
                    subprocess.run(['xdotool', 'windowactivate', window_id], check=True)
                    time.sleep(0.3)
                    return True
            
            # Fallback to PyWinCtl
            if hasattr(window, 'activate'):
                window.activate()
                time.sleep(0.3)
                return True
            
            return True
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not activate window: {e}[/yellow]")
            return True  # Still try to capture

class ScreenshotCapture:
    """Multi-method screenshot capture"""
    
    @staticmethod
    def capture_window_background(window: Any, crop_padding: int = 0) -> Optional[str]:
        """Capture screenshot of window in background without bringing it to foreground
        
        Args:
            window: Window object to capture
            crop_padding: Additional padding around window bounds (pixels)
            
        Returns:
            str: Path to saved screenshot file, or None if failed
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_num = random.randint(1000, 9999)
            filename = f"background_capture_{timestamp}_{random_num}.png"
            filepath = config.screenshots_dir / filename
            
            console.print(f"[dim]Capturing window '{window.title}' in background...[/dim]")
            
            # Method 1: Windows - Use PrintWindow API for true background capture
            if PLATFORM == 'windows' and WIN32_AVAILABLE:
                try:
                    # Get window handle - try multiple methods
                    hwnd = None
                    
                    # Method 1a: Direct _hWnd attribute
                    if hasattr(window, '_hWnd'):
                        hwnd = window._hWnd
                    
                    # Method 1b: Find window by title
                    if not hwnd and hasattr(window, 'title'):
                        hwnd = win32gui.FindWindow(None, window.title)
                    
                    # Method 1c: Enumerate windows to find match
                    if not hwnd:
                        def enum_windows_callback(hwnd_enum, results):
                            if win32gui.IsWindowVisible(hwnd_enum):
                                window_text = win32gui.GetWindowText(hwnd_enum)
                                if window_text and window.title in window_text:
                                    results.append(hwnd_enum)
                        
                        windows_list = []
                        win32gui.EnumWindows(enum_windows_callback, windows_list)
                        if windows_list:
                            hwnd = windows_list[0]
                    
                    if hwnd and win32gui.IsWindow(hwnd):
                        # Get actual window dimensions from Windows API
                        rect = win32gui.GetWindowRect(hwnd)
                        left, top, right, bottom = rect
                        width = right - left
                        height = bottom - top
                        
                        # Apply crop padding
                        if crop_padding > 0:
                            left = max(0, left - crop_padding)
                            top = max(0, top - crop_padding)
                            width += 2 * crop_padding
                            height += 2 * crop_padding
                        
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
                                
                                if Image:
                                    img = Image.frombuffer(
                                        'RGB',
                                        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                                        bmpstr, 'raw', 'BGRX', 0, 1
                                    )
                                    
                                    # Check if image is not blank (all black)
                                    extrema = img.getextrema()
                                    is_blank = all(channel == (0, 0) for channel in extrema)
                                    
                                    if not is_blank:
                                        img.save(filepath)
                                        
                                        # Cleanup
                                        win32gui.DeleteObject(saveBitMap.GetHandle())
                                        saveDC.DeleteDC()
                                        mfcDC.DeleteDC()
                                        win32gui.ReleaseDC(hwnd, hwndDC)
                                        
                                        console.print(f"[green]✓[/green] Background capture successful: {filename}")
                                        return str(filepath)
                                    else:
                                        console.print("[yellow]PrintWindow returned blank image, trying alternative method...[/yellow]")
                            
                            # Cleanup on failure
                            win32gui.DeleteObject(saveBitMap.GetHandle())
                            saveDC.DeleteDC()
                            mfcDC.DeleteDC()
                            win32gui.ReleaseDC(hwnd, hwndDC)
                            
                            # Try alternative PrintWindow flags if first attempt failed
                            if not result:
                                console.print("[yellow]Trying PrintWindow without flags...[/yellow]")
                                # Recreate contexts for second attempt
                                hwndDC = win32gui.GetWindowDC(hwnd)
                                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                                saveDC = mfcDC.CreateCompatibleDC()
                                saveBitMap = win32ui.CreateBitmap()
                                saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                                saveDC.SelectObject(saveBitMap)
                                
                                # Try with flag 0 (no special rendering)
                                result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
                                
                                if result:
                                    bmpinfo = saveBitMap.GetInfo()
                                    bmpstr = saveBitMap.GetBitmapBits(True)
                                    
                                    if Image:
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
                                            
                                            console.print(f"[green]✓[/green] Background capture successful: {filename}")
                                            return str(filepath)
                                
                                # Final cleanup
                                win32gui.DeleteObject(saveBitMap.GetHandle())
                                saveDC.DeleteDC()
                                mfcDC.DeleteDC()
                                win32gui.ReleaseDC(hwnd, hwndDC)
                    
                except Exception as e:
                    if config.show_debug:
                        console.print(f"[yellow]Win32 PrintWindow failed: {e}[/yellow]")
            
            # Method 2: Cross-platform MSS with proper window coordinates
            if mss:
                try:
                    # Get window dimensions - use fresh coordinates
                    width = getattr(window, 'width', 0)
                    height = getattr(window, 'height', 0)
                    left = getattr(window, 'left', 0)
                    top = getattr(window, 'top', 0)
                    
                    if width <= 0 or height <= 0:
                        console.print("[yellow]Invalid window dimensions for MSS[/yellow]")
                    else:
                        # Apply crop padding
                        if crop_padding > 0:
                            left = max(0, left - crop_padding)
                            top = max(0, top - crop_padding)
                            width += 2 * crop_padding
                            height += 2 * crop_padding
                        
                        with mss.mss() as sct:
                            monitor = {
                                "top": top,
                                "left": left,
                                "width": width,
                                "height": height
                            }
                            
                            sct_img = sct.grab(monitor)
                            if sct_img:
                                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                                
                                # Check if image is not blank
                                extrema = img.getextrema()
                                is_blank = all(channel == (0, 0) for channel in extrema)
                                
                                if not is_blank:
                                    img.save(filepath)
                                    console.print(f"[green]✓[/green] Background capture successful: {filename}")
                                    return str(filepath)
                                else:
                                    console.print("[yellow]MSS captured blank image[/yellow]")
                            
                except Exception as e:
                    if config.show_debug:
                        console.print(f"[yellow]MSS background capture failed: {e}[/yellow]")
            
            # Method 3: Linux - Use xwd for background capture
            if PLATFORM == 'linux' and LINUX_TOOLS_AVAILABLE:
                try:
                    # Get window ID
                    result = subprocess.run(['xdotool', 'search', '--name', window.title], 
                                          capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        window_id = result.stdout.strip().split('\n')[0]
                        
                        # Use xwd to capture window
                        xwd_cmd = ['xwd', '-id', window_id, '-out', str(filepath.with_suffix('.xwd'))]
                        result = subprocess.run(xwd_cmd, capture_output=True)
                        
                        if result.returncode == 0:
                            # Convert xwd to png using ImageMagick
                            convert_cmd = ['convert', str(filepath.with_suffix('.xwd')), str(filepath)]
                            result = subprocess.run(convert_cmd, capture_output=True)
                            
                            if result.returncode == 0 and filepath.exists():
                                # Clean up xwd file
                                filepath.with_suffix('.xwd').unlink(missing_ok=True)
                                console.print(f"[green]✓[/green] Background capture successful: {filename}")
                                return str(filepath)
                            
                except Exception as e:
                    if config.show_debug:
                        console.print(f"[yellow]Linux background capture failed: {e}[/yellow]")
            
            # Fallback: Try regular capture without activation
            console.print("[yellow]All background methods failed, falling back to regular capture...[/yellow]")
            return ScreenshotCapture.capture_window_silent(window)
            
        except Exception as e:
            console.print(f"[red]Background capture error: {e}[/red]")
            return None
    
    @staticmethod
    def capture_window_silent(window: Any) -> Optional[str]:
        """Capture window without activation (silent mode)"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_num = random.randint(1000, 9999)
            filename = f"silent_capture_{timestamp}_{random_num}.png"
            filepath = config.screenshots_dir / filename
            
            # Refresh window coordinates to get current position
            try:
                if hasattr(window, 'refresh'):
                    window.refresh()
                elif hasattr(window, 'update'):
                    window.update()
            except:
                pass
            
            # Get fresh window dimensions
            width = getattr(window, 'width', 0)
            height = getattr(window, 'height', 0)
            left = getattr(window, 'left', 0)
            top = getattr(window, 'top', 0)
            
            # For Windows, try to get accurate coordinates using Win32 API
            if PLATFORM == 'windows' and WIN32_AVAILABLE:
                try:
                    hwnd = None
                    if hasattr(window, '_hWnd'):
                        hwnd = window._hWnd
                    elif hasattr(window, 'title'):
                        hwnd = win32gui.FindWindow(None, window.title)
                    
                    if hwnd and win32gui.IsWindow(hwnd):
                        rect = win32gui.GetWindowRect(hwnd)
                        left, top, right, bottom = rect
                        width = right - left
                        height = bottom - top
                except:
                    pass
            
            if width <= 0 or height <= 0:
                return None
            
            console.print(f"[dim]Silent capturing window '{window.title}' at ({left}, {top}) {width}x{height}[/dim]")
            
            # Try MSS first (fastest and most reliable for background capture)
            if mss:
                try:
                    with mss.mss() as sct:
                        monitor = {
                            "top": top,
                            "left": left,
                            "width": width,
                            "height": height
                        }
                        sct_img = sct.grab(monitor)
                        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                        
                        if img.getextrema() != ((0, 0), (0, 0), (0, 0)):
                            img.save(filepath)
                            return str(filepath)
                except Exception:
                    pass
            
            # Try PyAutoGUI as fallback
            if pyautogui:
                try:
                    screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    screenshot.save(filepath)
                    return str(filepath)
                except Exception:
                    pass
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def capture_window(window: Any) -> Optional[str]:
        """Capture screenshot of specified window"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_num = random.randint(1000, 9999)
            filename = f"screenshot_{timestamp}_{random_num}.png"
            filepath = config.screenshots_dir / filename
            
            # Activate window first to ensure it's in foreground
            WindowManager.activate_window(window)
            
            # Wait a moment for window activation
            time.sleep(0.2)
            
            # Refresh window coordinates after activation
            try:
                if hasattr(window, 'refresh'):
                    window.refresh()
                elif hasattr(window, 'update'):
                    window.update()
            except:
                pass
            
            # Get fresh window dimensions after activation
            width = getattr(window, 'width', 0)
            height = getattr(window, 'height', 0)
            left = getattr(window, 'left', 0)
            top = getattr(window, 'top', 0)
            
            # For Windows, try to get accurate coordinates using Win32 API
            if PLATFORM == 'windows' and WIN32_AVAILABLE:
                try:
                    hwnd = None
                    if hasattr(window, '_hWnd'):
                        hwnd = window._hWnd
                    elif hasattr(window, 'title'):
                        hwnd = win32gui.FindWindow(None, window.title)
                    
                    if hwnd and win32gui.IsWindow(hwnd):
                        rect = win32gui.GetWindowRect(hwnd)
                        left, top, right, bottom = rect
                        width = right - left
                        height = bottom - top
                except:
                    pass
            
            if width <= 0 or height <= 0:
                console.print("[red]Invalid window dimensions[/red]")
                return None
            
            console.print(f"[dim]Capturing window '{window.title}' at ({left}, {top}) {width}x{height}[/dim]")
            
            # Method 1: Try DXcam (Windows only)
            if DXCAM_AVAILABLE and PLATFORM == 'windows':
                try:
                    camera = dxcam.create()
                    if camera:
                        region = (left, top, left + width, top + height)
                        frame = camera.grab(region=region)
                        if frame is not None and frame.size > 0:
                            img = Image.fromarray(frame)
                            if img.getextrema() != ((0, 0), (0, 0), (0, 0)):
                                img.save(filepath)
                                camera.release()
                                return str(filepath)
                        camera.release()
                except Exception as e:
                    if config.show_debug:
                        console.print(f"[yellow]DXcam failed: {e}[/yellow]")
            
            # Method 2: MSS (cross-platform)
            if mss:
                try:
                    with mss.mss() as sct:
                        monitor = {
                            "top": top,
                            "left": left,
                            "width": width,
                            "height": height
                        }
                        sct_img = sct.grab(monitor)
                        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                        if img.getextrema() != ((0, 0), (0, 0), (0, 0)):
                            img.save(filepath)
                            return str(filepath)
                except Exception as e:
                    if config.show_debug:
                        console.print(f"[yellow]MSS failed: {e}[/yellow]")
            
            # Method 3: Linux scrot
            if PLATFORM == 'linux' and LINUX_TOOLS_AVAILABLE:
                try:
                    scrot_cmd = ["scrot", "-a", f"{left},{top},{width},{height}", str(filepath)]
                    result = subprocess.run(scrot_cmd, capture_output=True, text=True)
                    if result.returncode == 0 and filepath.exists():
                        return str(filepath)
                except Exception as e:
                    if config.show_debug:
                        console.print(f"[yellow]scrot failed: {e}[/yellow]")
            
            # Method 4: PyAutoGUI fallback
            if pyautogui:
                try:
                    screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    screenshot.save(filepath)
                    return str(filepath)
                except Exception as e:
                    if config.show_debug:
                        console.print(f"[yellow]PyAutoGUI failed: {e}[/yellow]")
            
            console.print("[red]All screenshot methods failed[/red]")
            return None
            
        except Exception as e:
            console.print(f"[red]Screenshot capture error: {e}[/red]")
            return None

class AzureOCR:
    """Azure Computer Vision OCR integration"""
    
    @staticmethod
    def process_image(image_path: str) -> Dict[str, Any]:
        """Process image with Azure OCR"""
        if not config.is_azure_configured():
            return {
                'success': False,
                'error': 'Azure OCR not configured',
                'raw_text': ''
            }
        
        if not requests:
            return {
                'success': False,
                'error': 'requests library not available',
                'raw_text': ''
            }
        
        try:
            # Read image file
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Azure OCR API call
            headers = {
                'Ocp-Apim-Subscription-Key': config.azure_key,
                'Content-Type': 'application/octet-stream'
            }
            
            url = f"{config.azure_endpoint}/vision/v3.2/ocr"
            params = {'language': 'unk', 'detectOrientation': 'true'}
            
            response = requests.post(url, headers=headers, params=params, data=image_data, timeout=30)
            
            if response.status_code == 200:
                ocr_result = response.json()
                raw_text = AzureOCR.extract_text_from_result(ocr_result)
                
                return {
                    'success': True,
                    'result': ocr_result,
                    'raw_text': raw_text,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                return {
                    'success': False,
                    'error': f'Azure API error: {response.status_code} - {response.text}',
                    'raw_text': ''
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'OCR processing error: {str(e)}',
                'raw_text': ''
            }
    
    @staticmethod
    def extract_text_from_result(ocr_result: Dict[str, Any]) -> str:
        """Extract text from Azure OCR result"""
        try:
            raw_text_lines = []
            
            if 'regions' in ocr_result:
                for region in ocr_result['regions']:
                    for line in region.get('lines', []):
                        line_text = ' '.join([word.get('text', '') for word in line.get('words', [])])
                        if line_text.strip():
                            raw_text_lines.append(line_text)
            
            return '\n'.join(raw_text_lines) if raw_text_lines else ''
            
        except Exception as e:
            return f"Error extracting text: {str(e)}"

class DataExporter:
    """Data export functionality"""
    
    @staticmethod
    def save_to_csv(data: Dict[str, Any], filename: str = "auto_data.csv") -> bool:
        """Save data to CSV file"""
        try:
            csv_path = config.screenshots_dir / filename
            file_exists = csv_path.exists()
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'window_title', 'raw_text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'timestamp': data.get('timestamp', ''),
                    'window_title': data.get('window_title', ''),
                    'raw_text': data.get('raw_text', '').replace('\n', ' | ')
                })
            
            return True
            
        except Exception as e:
            console.print(f"[red]CSV export error: {e}[/red]")
            return False
    
    @staticmethod
    def save_to_json(data: Dict[str, Any], filename: str = None) -> bool:
        """Save data to JSON file"""
        try:
            if not filename:
                timestamp_safe = data.get('timestamp', '').replace(':', '-').replace(' ', '_')
                filename = f"capture_{timestamp_safe}.json"
            
            json_path = config.screenshots_dir / filename
            
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            console.print(f"[red]JSON export error: {e}[/red]")
            return False
    
    @staticmethod
    def cleanup_old_screenshots():
        """Clean up old screenshots, keeping only the last N files"""
        try:
            screenshot_files = list(config.screenshots_dir.glob("screenshot_*.png"))
            
            if len(screenshot_files) <= config.max_screenshots:
                return
            
            # Sort by modification time (newest first)
            screenshot_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Delete old files
            for old_file in screenshot_files[config.max_screenshots:]:
                try:
                    old_file.unlink()
                except Exception as e:
                    if config.show_debug:
                        console.print(f"[yellow]Could not delete {old_file}: {e}[/yellow]")
                        
        except Exception as e:
            if config.show_debug:
                console.print(f"[yellow]Cleanup error: {e}[/yellow]")

# CLI Application Classes
class GraceCLI:
    """Main CLI application class"""
    
    def __init__(self):
        self.selected_window = None
        self.auto_capture_running = False
        self.auto_capture_thread = None
        self.last_ocr_result = None
    
    def show_banner(self):
        """Display application banner"""
        banner = Panel.fit(
            "[bold blue]Grace Biosensor Data Capture[/bold blue]\n"
            "[dim]CLI Edition v2.0.0[/dim]\n\n"
            "[green]✓[/green] Cross-platform window detection\n"
            "[green]✓[/green] Multi-method screenshot capture\n"
            "[green]✓[/green] Azure Computer Vision OCR\n"
            "[green]✓[/green] Real-time data export\n"
            "[green]✓[/green] Beautiful CLI interface",
            title="[bold]Welcome to Grace CLI[/bold]",
            border_style="blue"
        )
        console.print(banner)
        console.print()
    
    def show_system_status(self):
        """Display system status and capabilities"""
        status_table = Table(title="System Status", box=box.ROUNDED)
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="green")
        status_table.add_column("Details", style="dim")
        
        # Platform info
        status_table.add_row(
            "Platform", 
            f"[green]✓[/green] {PLATFORM.title()}",
            f"Running on {platform.platform()}"
        )
        
        # Window management
        if WINDOW_MANAGER_AVAILABLE:
            status_table.add_row(
                "Window Management", 
                "[green]✓ Available[/green]",
                "PyWinCtl + pygetwindow"
            )
        else:
            status_table.add_row(
                "Window Management", 
                "[red]✗ Missing[/red]",
                "Install PyWinCtl and pygetwindow"
            )
        
        # Screenshot capabilities
        methods = []
        if DXCAM_AVAILABLE:
            methods.append("DXcam")
        if mss:
            methods.append("MSS")
        if LINUX_TOOLS_AVAILABLE:
            methods.append("scrot")
        if pyautogui:
            methods.append("PyAutoGUI")
        
        if methods:
            status_table.add_row(
                "Screenshot Methods", 
                f"[green]✓ {len(methods)} available[/green]",
                ", ".join(methods)
            )
        else:
            status_table.add_row(
                "Screenshot Methods", 
                "[red]✗ None available[/red]",
                "Install required dependencies"
            )
        
        # Azure OCR
        is_configured, message = config.validate_azure_config()
        if is_configured:
            status_table.add_row(
                "Azure OCR", 
                "[green]✓ Configured[/green]",
                "Ready for text extraction"
            )
        else:
            status_table.add_row(
                "Azure OCR", 
                "[yellow]⚠ Not configured[/yellow]",
                message
            )
        
        console.print(status_table)
        console.print()
    
    def list_windows(self, show_categories: bool = True) -> List[Any]:
        """List all available windows"""
        with Status("[bold blue]Scanning for windows...", console=console):
            windows = WindowManager.get_all_windows()
        
        if not windows:
            console.print("[red]No windows found![/red]")
            return []
        
        if show_categories:
            categories = WindowManager.categorize_windows(windows)
            
            tree = Tree("[bold blue]Available Windows[/bold blue]")
            
            for category, window_list in categories.items():
                if window_list:
                    category_name = category.replace('_', ' ').title()
                    category_branch = tree.add(f"[cyan]{category_name}[/cyan] ({len(window_list)})")
                    
                    for i, window in enumerate(window_list):
                        window_info = f"[{i+1}] {window.title} ({window.width}x{window.height})"
                        category_branch.add(window_info)
            
            console.print(tree)
        else:
            table = Table(title="Available Windows", box=box.ROUNDED)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Window Title", style="white")
            table.add_column("Dimensions", style="dim")
            
            for i, window in enumerate(windows, 1):
                table.add_row(
                    str(i),
                    window.title[:60] + "..." if len(window.title) > 60 else window.title,
                    f"{window.width}x{window.height}"
                )
            
            console.print(table)
        
        return windows
    
    def select_window(self, windows: List[Any]) -> Optional[Any]:
        """Interactive window selection"""
        if not windows:
            return None
        
        console.print("\n[bold]Select a window to capture:[/bold]")
        
        while True:
            try:
                choice = IntPrompt.ask(
                    "Enter window number",
                    default=1,
                    show_default=True
                )
                
                if 1 <= choice <= len(windows):
                    selected = windows[choice - 1]
                    console.print(f"[green]✓ Selected: {selected.title}[/green]")
                    return selected
                else:
                    console.print(f"[red]Invalid choice. Please enter 1-{len(windows)}[/red]")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Selection cancelled[/yellow]")
                return None
    
    def capture_window(self, window: Any) -> Optional[Dict[str, Any]]:
        """Capture and process a window"""
        console.print(f"\n[bold blue]Capturing window: {window.title}[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            # Step 1: Take screenshot
            task1 = progress.add_task("Taking screenshot...", total=100)
            progress.update(task1, advance=30)
            
            image_path = ScreenshotCapture.capture_window(window)
            progress.update(task1, advance=70)
            
            if not image_path:
                progress.update(task1, completed=100)
                console.print("[red]✗ Screenshot failed[/red]")
                return None
            
            progress.update(task1, completed=100)
            console.print(f"[green]✓ Screenshot saved: {Path(image_path).name}[/green]")
            
            # Step 2: OCR processing
            task2 = progress.add_task("Processing with OCR...", total=100)
            progress.update(task2, advance=20)
            
            ocr_result = AzureOCR.process_image(image_path)
            progress.update(task2, advance=80)
            
            if not ocr_result['success']:
                progress.update(task2, completed=100)
                console.print(f"[red]✗ OCR failed: {ocr_result['error']}[/red]")
                return None
            
            progress.update(task2, completed=100)
            
            # Prepare result data
            result_data = {
                'timestamp': ocr_result['timestamp'],
                'window_title': window.title,
                'raw_text': ocr_result['raw_text'],
                'image_path': image_path,
                'ocr_result': ocr_result['result']
            }
            
            self.last_ocr_result = result_data
            
            # Display results
            self.display_ocr_results(result_data)
            
            return result_data
    
    def capture_window_background(self, window: Any, crop_padding: int = 0) -> Optional[Dict[str, Any]]:
        """Capture and process a window in background without bringing it to foreground"""
        console.print(f"\n[bold blue]Capturing window in background: {window.title}[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            # Step 1: Take background screenshot
            task1 = progress.add_task("Taking background screenshot...", total=100)
            progress.update(task1, advance=30)
            
            image_path = ScreenshotCapture.capture_window_background(window, crop_padding)
            progress.update(task1, advance=70)
            
            if not image_path:
                progress.update(task1, completed=100)
                console.print("[red]✗ Background screenshot failed[/red]")
                return None
            
            progress.update(task1, completed=100)
            console.print(f"[green]✓ Background screenshot saved: {Path(image_path).name}[/green]")
            
            # Step 2: OCR processing
            task2 = progress.add_task("Processing with OCR...", total=100)
            progress.update(task2, advance=20)
            
            ocr_result = AzureOCR.process_image(image_path)
            progress.update(task2, advance=80)
            
            if not ocr_result['success']:
                progress.update(task2, completed=100)
                console.print(f"[red]✗ OCR failed: {ocr_result['error']}[/red]")
                return None
            
            progress.update(task2, completed=100)
            
            # Prepare result data
            result_data = {
                'timestamp': ocr_result['timestamp'],
                'window_title': window.title,
                'raw_text': ocr_result['raw_text'],
                'image_path': image_path,
                'capture_method': 'background',
                'crop_padding': crop_padding,
                'ocr_result': ocr_result['result']
            }
            
            self.last_ocr_result = result_data
            
            # Display results
            self.display_ocr_results(result_data, background=True)
            
            return result_data
    
    def display_ocr_results(self, data: Dict[str, Any], background: bool = False):
        """Display OCR results in a beautiful format"""
        console.print("\n" + "="*60)
        capture_type = "Background OCR Results" if background else "OCR Results"
        console.print(f"[bold green]{capture_type}[/bold green]")
        console.print("="*60)
        
        # Create results panel
        results_text = data['raw_text'] if data['raw_text'].strip() else "[dim]No text detected[/dim]"
        
        title_text = f"[bold]Extracted Text from: {data['window_title']}[/bold]"
        if background:
            title_text += " [dim](Background Capture)[/dim]"
        
        subtitle_parts = [f"Captured at: {data['timestamp']}"]
        if background and 'crop_padding' in data:
            subtitle_parts.append(f"Padding: {data['crop_padding']}px")
        
        results_panel = Panel(
            results_text,
            title=title_text,
            subtitle=f"[dim]{' | '.join(subtitle_parts)}[/dim]",
            border_style="green"
        )
        
        console.print(results_panel)
        console.print()
    
    def auto_capture_worker(self):
        """Auto-capture worker thread"""
        while self.auto_capture_running:
            if self.selected_window:
                try:
                    result = self.capture_window(self.selected_window)
                    if result:
                        # Auto-save to CSV
                        DataExporter.save_to_csv(result)
                        # Clean up screenshot
                        if result['image_path'] and Path(result['image_path']).exists():
                            Path(result['image_path']).unlink()
                        DataExporter.cleanup_old_screenshots()
                except Exception as e:
                    console.print(f"[red]Auto-capture error: {e}[/red]")
            
            # Wait for next capture
            for _ in range(config.auto_capture_interval):
                if not self.auto_capture_running:
                    break
                time.sleep(1)
    
    def start_auto_capture(self):
        """Start auto-capture mode"""
        if not self.selected_window:
            console.print("[red]Please select a window first[/red]")
            return
        
        if self.auto_capture_running:
            console.print("[yellow]Auto-capture is already running[/yellow]")
            return
        
        interval = IntPrompt.ask(
            "Auto-capture interval (seconds)",
            default=config.auto_capture_interval,
            show_default=True
        )
        
        if interval < 1:
            console.print("[red]Interval must be at least 1 second[/red]")
            return
        
        config.auto_capture_interval = interval
        self.auto_capture_running = True
        
        self.auto_capture_thread = threading.Thread(target=self.auto_capture_worker, daemon=True)
        self.auto_capture_thread.start()
        
        console.print(f"[green]✓ Auto-capture started (every {interval}s)[/green]")
        console.print("[dim]Press Ctrl+C to stop auto-capture[/dim]")
    
    def stop_auto_capture(self):
        """Stop auto-capture mode"""
        if not self.auto_capture_running:
            console.print("[yellow]Auto-capture is not running[/yellow]")
            return
        
        self.auto_capture_running = False
        if self.auto_capture_thread:
            self.auto_capture_thread.join(timeout=2)
        
        console.print("[green]✓ Auto-capture stopped[/green]")
    
    def export_last_result(self):
        """Export the last OCR result"""
        if not self.last_ocr_result:
            console.print("[red]No results to export. Capture a window first.[/red]")
            return
        
        console.print("\n[bold]Export Options:[/bold]")
        console.print("1. CSV format")
        console.print("2. JSON format")
        console.print("3. Both formats")
        
        choice = IntPrompt.ask("Select export format", choices=["1", "2", "3"], default="3")
        
        success = False
        
        if choice in ["1", "3"]:
            if DataExporter.save_to_csv(self.last_ocr_result):
                console.print("[green]✓ Exported to CSV[/green]")
                success = True
        
        if choice in ["2", "3"]:
            if DataExporter.save_to_json(self.last_ocr_result):
                console.print("[green]✓ Exported to JSON[/green]")
                success = True
        
        if success:
            console.print(f"[dim]Files saved to: {config.screenshots_dir}[/dim]")
    
    def configure_azure(self):
        """Configure Azure OCR settings"""
        console.print("\n[bold blue]Azure Computer Vision Configuration[/bold blue]")
        
        current_endpoint = config.azure_endpoint or "[dim]Not set[/dim]"
        current_key = "[dim]Not set[/dim]" if not config.azure_key else "[dim]***configured***[/dim]"
        
        console.print(f"Current endpoint: {current_endpoint}")
        console.print(f"Current key: {current_key}")
        console.print()
        
        if Confirm.ask("Update Azure configuration?"):
            endpoint = Prompt.ask(
                "Azure Computer Vision Endpoint",
                default=config.azure_endpoint or ""
            )
            
            key = Prompt.ask(
                "Azure Computer Vision Key",
                password=True
            )
            
            if endpoint and key:
                config.azure_endpoint = endpoint
                config.azure_key = key
                console.print("[green]✓ Azure configuration updated[/green]")
                
                # Save to .env file
                env_path = Path('.env')
                env_content = f"AZURE_COMPUTER_VISION_ENDPOINT={endpoint}\n"
                env_content += f"AZURE_COMPUTER_VISION_KEY={key}\n"
                
                with open(env_path, 'w') as f:
                    f.write(env_content)
                
                console.print(f"[dim]Configuration saved to {env_path}[/dim]")
            else:
                console.print("[yellow]Configuration cancelled[/yellow]")
    
    def show_help(self):
        """Display help information"""
        help_panel = Panel(
            "[bold]Available Commands:[/bold]\n\n"
            "[cyan]1.[/cyan] List Windows - Show all available windows\n"
            "[cyan]2.[/cyan] Select Window - Choose a window to capture\n"
            "[cyan]3.[/cyan] Capture Now - Take screenshot and process with OCR\n"
            "[cyan]4.[/cyan] Auto Capture - Start/stop automatic capture mode\n"
            "[cyan]5.[/cyan] Export Results - Save last results to CSV/JSON\n"
            "[cyan]6.[/cyan] Configure Azure - Set up Azure OCR credentials\n"
            "[cyan]7.[/cyan] System Status - Show system capabilities\n"
            "[cyan]8.[/cyan] Settings - Adjust application settings\n"
            "[cyan]9.[/cyan] Help - Show this help message\n"
            "[cyan]0.[/cyan] Exit - Quit the application\n\n"
            "[dim]Use Ctrl+C to interrupt any operation[/dim]",
            title="[bold]Grace CLI Help[/bold]",
            border_style="cyan"
        )
        console.print(help_panel)
    
    def show_settings(self):
        """Display and modify settings"""
        console.print("\n[bold blue]Application Settings[/bold blue]")
        
        settings_table = Table(box=box.ROUNDED)
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Current Value", style="white")
        settings_table.add_column("Description", style="dim")
        
        settings_table.add_row(
            "Auto-capture interval",
            f"{config.auto_capture_interval}s",
            "Time between automatic captures"
        )
        
        settings_table.add_row(
            "Max screenshots",
            str(config.max_screenshots),
            "Maximum screenshots to keep"
        )
        
        settings_table.add_row(
            "Debug mode",
            "Enabled" if config.show_debug else "Disabled",
            "Show detailed error messages"
        )
        
        settings_table.add_row(
            "Screenshots directory",
            str(config.screenshots_dir),
            "Where screenshots and data are saved"
        )
        
        console.print(settings_table)
        
        if Confirm.ask("\nModify settings?"):
            # Auto-capture interval
            new_interval = IntPrompt.ask(
                "Auto-capture interval (seconds)",
                default=config.auto_capture_interval
            )
            if new_interval >= 1:
                config.auto_capture_interval = new_interval
            
            # Max screenshots
            new_max = IntPrompt.ask(
                "Maximum screenshots to keep",
                default=config.max_screenshots
            )
            if new_max >= 1:
                config.max_screenshots = new_max
            
            # Debug mode
            config.show_debug = Confirm.ask(
                "Enable debug mode?",
                default=config.show_debug
            )
            
            console.print("[green]✓ Settings updated[/green]")
    
    def run_interactive(self):
        """Run the interactive CLI interface"""
        self.show_banner()
        
        try:
            while True:
                console.print("\n[bold]Grace CLI Menu[/bold]")
                console.print("1. List Windows")
                console.print("2. Select Window")
                console.print("3. Capture Now")
                console.print("4. Background Capture")
                console.print("5. Auto Capture")
                console.print("6. Export Results")
                console.print("7. Configure Azure")
                console.print("8. System Status")
                console.print("9. Settings")
                console.print("10. Help")
                console.print("0. Exit")
                
                try:
                    choice = IntPrompt.ask(
                        "\nSelect option",
                        choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                        show_choices=False
                    )
                    
                    if choice == 0:
                        break
                    elif choice == 1:
                        self.list_windows()
                    elif choice == 2:
                        windows = self.list_windows(show_categories=False)
                        if windows:
                            self.selected_window = self.select_window(windows)
                    elif choice == 3:
                        if self.selected_window:
                            self.capture_window(self.selected_window)
                        else:
                            console.print("[red]Please select a window first (option 2)[/red]")
                    elif choice == 4:
                        if self.selected_window:
                            # Ask for padding
                            padding = IntPrompt.ask(
                                "Enter crop padding (pixels)",
                                default=10,
                                show_default=True
                            )
                            self.capture_window_background(self.selected_window, padding)
                        else:
                            console.print("[red]Please select a window first (option 2)[/red]")
                    elif choice == 5:
                        if self.auto_capture_running:
                            self.stop_auto_capture()
                        else:
                            self.start_auto_capture()
                    elif choice == 6:
                        self.export_last_result()
                    elif choice == 7:
                        self.configure_azure()
                    elif choice == 8:
                        self.show_system_status()
                    elif choice == 9:
                        self.show_settings()
                    elif choice == 10:
                        self.show_help()
                        
                except KeyboardInterrupt:
                    console.print("\n[yellow]Operation cancelled[/yellow]")
                    continue
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting Grace CLI...[/yellow]")
        finally:
            self.stop_auto_capture()
            console.print("[green]Thank you for using Grace CLI![/green]")

# Command-line interface using Click/Typer
app = typer.Typer(
    name="grace-cli",
    help="Grace Biosensor Data Capture - CLI Edition",
    add_completion=False
)

@app.command()
def interactive():
    """Launch interactive CLI interface"""
    cli = GraceCLI()
    cli.run_interactive()

@app.command()
def list_windows(
    categories: bool = typer.Option(True, "--categories/--no-categories", help="Show windows in categories")
):
    """List all available windows"""
    cli = GraceCLI()
    cli.list_windows(show_categories=categories)

@app.command()
def capture(
    window_title: str = typer.Option(None, "--window", "-w", help="Window title to capture"),
    background: bool = typer.Option(False, "--background", "-b", help="Capture window in background without bringing to foreground"),
    crop_padding: int = typer.Option(0, "--padding", "-p", help="Additional padding around window bounds (pixels)"),
    export_csv: bool = typer.Option(False, "--csv", help="Export to CSV"),
    export_json: bool = typer.Option(False, "--json", help="Export to JSON")
):
    """Capture a specific window"""
    cli = GraceCLI()
    
    if not window_title:
        windows = cli.list_windows(show_categories=False)
        if windows:
            selected = cli.select_window(windows)
            if selected:
                if background:
                    result = cli.capture_window_background(selected, crop_padding)
                else:
                    result = cli.capture_window(selected)
                if result and (export_csv or export_json):
                    if export_csv:
                        DataExporter.save_to_csv(result)
                    if export_json:
                        DataExporter.save_to_json(result)
        return
    
    # Find window by title
    windows = WindowManager.get_all_windows()
    matching_windows = [w for w in windows if window_title.lower() in w.title.lower()]
    
    if not matching_windows:
        console.print(f"[red]No windows found matching '{window_title}'[/red]")
        return
    
    if len(matching_windows) > 1:
        console.print(f"[yellow]Multiple windows found matching '{window_title}':[/yellow]")
        for i, w in enumerate(matching_windows, 1):
            console.print(f"  {i}. {w.title}")
        
        choice = IntPrompt.ask("Select window number", default=1)
        if 1 <= choice <= len(matching_windows):
            selected = matching_windows[choice - 1]
        else:
            console.print("[red]Invalid selection[/red]")
            return
    else:
        selected = matching_windows[0]
    
    if background:
        result = cli.capture_window_background(selected, crop_padding)
    else:
        result = cli.capture_window(selected)
        
    if result and (export_csv or export_json):
        if export_csv:
            DataExporter.save_to_csv(result)
        if export_json:
            DataExporter.save_to_json(result)

@app.command()
def background_capture(
    window_title: str = typer.Argument(..., help="Window title to capture"),
    crop_padding: int = typer.Option(10, "--padding", "-p", help="Additional padding around window bounds (pixels)"),
    export_csv: bool = typer.Option(False, "--csv", help="Export to CSV"),
    export_json: bool = typer.Option(False, "--json", help="Export to JSON")
):
    """Capture a window in the background without bringing it to foreground"""
    cli = GraceCLI()
    
    # Find window by title
    windows = WindowManager.get_all_windows()
    matching_windows = [w for w in windows if window_title.lower() in w.title.lower()]
    
    if not matching_windows:
        console.print(f"[red]No windows found matching '{window_title}'[/red]")
        return
    
    if len(matching_windows) > 1:
        console.print(f"[yellow]Multiple windows found matching '{window_title}':[/yellow]")
        for i, w in enumerate(matching_windows, 1):
            console.print(f"  {i}. {w.title}")
        
        choice = IntPrompt.ask("Select window number", default=1)
        if 1 <= choice <= len(matching_windows):
            selected = matching_windows[choice - 1]
        else:
            console.print("[red]Invalid selection[/red]")
            return
    else:
        selected = matching_windows[0]
    
    result = cli.capture_window_background(selected, crop_padding)
    
    if result and (export_csv or export_json):
        if export_csv:
            DataExporter.save_to_csv(result)
        if export_json:
            DataExporter.save_to_json(result)

@app.command()
def auto_capture(
    window_title: str = typer.Option(None, "--window", "-w", help="Window title to capture"),
    interval: int = typer.Option(5, "--interval", "-i", help="Capture interval in seconds"),
    duration: int = typer.Option(None, "--duration", "-d", help="Duration in seconds (0 for infinite)")
):
    """Start auto-capture mode"""
    cli = GraceCLI()
    
    if not window_title:
        console.print("[red]Window title is required for auto-capture mode[/red]")
        return
    
    # Find window by title
    windows = WindowManager.get_all_windows()
    matching_windows = [w for w in windows if window_title.lower() in w.title.lower()]
    
    if not matching_windows:
        console.print(f"[red]No windows found matching '{window_title}'[/red]")
        return
    
    selected = matching_windows[0]
    cli.selected_window = selected
    config.auto_capture_interval = interval
    
    console.print(f"[green]Starting auto-capture for: {selected.title}[/green]")
    console.print(f"[dim]Interval: {interval}s, Duration: {'infinite' if not duration else f'{duration}s'}[/dim]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    
    cli.auto_capture_running = True
    start_time = time.time()
    
    try:
        while cli.auto_capture_running:
            result = cli.capture_window(selected)
            if result:
                DataExporter.save_to_csv(result)
                # Clean up screenshot
                if result['image_path'] and Path(result['image_path']).exists():
                    Path(result['image_path']).unlink()
                DataExporter.cleanup_old_screenshots()
            
            # Check duration
            if duration and (time.time() - start_time) >= duration:
                break
            
            # Wait for next capture
            for _ in range(interval):
                if not cli.auto_capture_running:
                    break
                time.sleep(1)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Auto-capture stopped[/yellow]")
    finally:
        cli.auto_capture_running = False

@app.command()
def configure(
    endpoint: str = typer.Option(None, "--endpoint", help="Azure Computer Vision endpoint"),
    key: str = typer.Option(None, "--key", help="Azure Computer Vision key")
):
    """Configure Azure OCR settings"""
    if endpoint and key:
        config.azure_endpoint = endpoint
        config.azure_key = key
        
        # Save to .env file
        env_path = Path('.env')
        env_content = f"AZURE_COMPUTER_VISION_ENDPOINT={endpoint}\n"
        env_content += f"AZURE_COMPUTER_VISION_KEY={key}\n"
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        console.print("[green]✓ Azure configuration saved[/green]")
    else:
        cli = GraceCLI()
        cli.configure_azure()

@app.command()
def status():
    """Show system status and capabilities"""
    cli = GraceCLI()
    cli.show_system_status()

@app.command()
def version():
    """Show version information"""
    console.print("[bold blue]Grace Biosensor Data Capture - CLI Edition[/bold blue]")
    console.print("Version: 2.0.0")
    console.print("Author: Anas Gulzar Dev")
    console.print("Platform: " + PLATFORM.title())

if __name__ == "__main__":
    app()