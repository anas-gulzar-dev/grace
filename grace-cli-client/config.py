#!/usr/bin/env python3
"""
Configuration management for Grace CLI

Handles application settings, environment variables, and configuration persistence.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class AzureConfig:
    """Azure Computer Vision configuration"""
    endpoint: str = ""
    key: str = ""
    api_version: str = "v3.2"
    language: str = "unk"
    detect_orientation: bool = True
    timeout: int = 30
    
    def is_configured(self) -> bool:
        """Check if Azure is properly configured"""
        return bool(self.endpoint and self.key)
    
    def validate(self) -> tuple[bool, str]:
        """Validate Azure configuration"""
        if not self.endpoint:
            return False, "Azure Computer Vision endpoint not configured"
        if not self.key:
            return False, "Azure Computer Vision key not configured"
        if not self.endpoint.startswith(('http://', 'https://')):
            return False, "Invalid endpoint URL format"
        return True, "Azure configuration valid"

@dataclass
class CaptureConfig:
    """Screenshot capture configuration"""
    auto_interval: int = 5  # seconds
    max_screenshots: int = 5
    cleanup_enabled: bool = True
    preferred_method: str = "auto"  # auto, dxcam, mss, scrot, pyautogui
    activate_window: bool = True
    activation_delay: float = 0.3  # seconds
    
@dataclass
class ExportConfig:
    """Data export configuration"""
    auto_csv: bool = True
    auto_json: bool = False
    csv_filename: str = "auto_data.csv"
    json_timestamp_format: str = "%Y%m%d_%H%M%S"
    csv_delimiter: str = ","
    include_full_ocr: bool = True
    
@dataclass
class UIConfig:
    """User interface configuration"""
    show_debug: bool = False
    show_categories: bool = True
    console_width: Optional[int] = None
    color_theme: str = "auto"  # auto, dark, light
    progress_style: str = "bar"  # bar, spinner
    table_style: str = "rounded"  # rounded, simple, heavy
    
@dataclass
class AppConfig:
    """Main application configuration"""
    azure: AzureConfig
    capture: CaptureConfig
    export: ExportConfig
    ui: UIConfig
    
    # Directories
    screenshots_dir: str = "screenshots"
    config_dir: str = ".grace"
    
    # Application info
    app_name: str = "Grace CLI"
    app_version: str = "2.0.0"
    author: str = "Anas Gulzar Dev"
    
    def __post_init__(self):
        """Initialize directories after creation"""
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        Path(self.screenshots_dir).mkdir(exist_ok=True)
        Path(self.config_dir).mkdir(exist_ok=True)
    
    @property
    def screenshots_path(self) -> Path:
        """Get screenshots directory path"""
        return Path(self.screenshots_dir)
    
    @property
    def config_path(self) -> Path:
        """Get config directory path"""
        return Path(self.config_dir)
    
    @property
    def config_file_path(self) -> Path:
        """Get config file path"""
        return self.config_path / "config.json"
    
    @property
    def env_file_path(self) -> Path:
        """Get .env file path"""
        return Path(".env")

class ConfigManager:
    """Configuration manager for Grace CLI"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file) if config_file else None
        self._config: Optional[AppConfig] = None
    
    @property
    def config(self) -> AppConfig:
        """Get current configuration (property access)"""
        return self.get_config()
    
    def load_config(self) -> AppConfig:
        """Load configuration from file and environment"""
        if self._config is not None:
            return self._config
        
        # Start with default configuration
        config = AppConfig(
            azure=AzureConfig(),
            capture=CaptureConfig(),
            export=ExportConfig(),
            ui=UIConfig()
        )
        
        # Load from environment variables
        self._load_from_env(config)
        
        # Load from config file if it exists
        config_file = self.config_file or config.config_file_path
        if config_file.exists():
            self._load_from_file(config, config_file)
        
        self._config = config
        return config
    
    def save_config(self, config: AppConfig, save_env: bool = True) -> bool:
        """Save configuration to file and optionally to .env"""
        try:
            # Save to JSON config file
            config.ensure_directories()
            config_data = self._config_to_dict(config)
            
            config_file = self.config_file or config.config_file_path
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Save Azure config to .env file if requested
            if save_env and config.azure.is_configured():
                self._save_to_env(config)
            
            self._config = config
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _load_from_env(self, config: AppConfig):
        """Load configuration from environment variables"""
        # Azure configuration
        config.azure.endpoint = os.getenv('AZURE_COMPUTER_VISION_ENDPOINT', config.azure.endpoint)
        config.azure.key = os.getenv('AZURE_COMPUTER_VISION_KEY', config.azure.key)
        
        # Other environment variables
        if os.getenv('GRACE_SCREENSHOTS_DIR'):
            config.screenshots_dir = os.getenv('GRACE_SCREENSHOTS_DIR')
        
        if os.getenv('GRACE_DEBUG'):
            config.ui.show_debug = os.getenv('GRACE_DEBUG', '').lower() in ('true', '1', 'yes')
        
        if os.getenv('GRACE_AUTO_INTERVAL'):
            try:
                config.capture.auto_interval = int(os.getenv('GRACE_AUTO_INTERVAL'))
            except ValueError:
                pass
    
    def _load_from_file(self, config: AppConfig, config_file: Path):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update configuration with file data
            if 'azure' in data:
                azure_data = data['azure']
                for key, value in azure_data.items():
                    if hasattr(config.azure, key):
                        setattr(config.azure, key, value)
            
            if 'capture' in data:
                capture_data = data['capture']
                for key, value in capture_data.items():
                    if hasattr(config.capture, key):
                        setattr(config.capture, key, value)
            
            if 'export' in data:
                export_data = data['export']
                for key, value in export_data.items():
                    if hasattr(config.export, key):
                        setattr(config.export, key, value)
            
            if 'ui' in data:
                ui_data = data['ui']
                for key, value in ui_data.items():
                    if hasattr(config.ui, key):
                        setattr(config.ui, key, value)
            
            # Update other settings
            if 'screenshots_dir' in data:
                config.screenshots_dir = data['screenshots_dir']
            
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
    
    def _save_to_env(self, config: AppConfig):
        """Save Azure configuration to .env file"""
        try:
            env_content = []
            
            # Read existing .env file if it exists
            env_file = config.env_file_path
            existing_vars = {}
            
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_vars[key.strip()] = value.strip()
            
            # Update Azure variables
            existing_vars['AZURE_COMPUTER_VISION_ENDPOINT'] = config.azure.endpoint
            existing_vars['AZURE_COMPUTER_VISION_KEY'] = config.azure.key
            
            # Write updated .env file
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("# Grace CLI Environment Configuration\n")
                f.write("# Azure Computer Vision Settings\n")
                for key, value in existing_vars.items():
                    f.write(f"{key}={value}\n")
            
        except Exception as e:
            print(f"Warning: Could not save .env file: {e}")
    
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """Convert configuration to dictionary for JSON serialization"""
        return {
            'azure': asdict(config.azure),
            'capture': asdict(config.capture),
            'export': asdict(config.export),
            'ui': asdict(config.ui),
            'screenshots_dir': config.screenshots_dir,
            'config_dir': config.config_dir,
            'app_name': config.app_name,
            'app_version': config.app_version,
            'author': config.author
        }
    
    def reset_config(self) -> AppConfig:
        """Reset configuration to defaults"""
        self._config = None
        return self.load_config()
    
    def get_config(self) -> AppConfig:
        """Get current configuration (load if not already loaded)"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def update_azure_config(self, endpoint: str, key: str, save: bool = True) -> bool:
        """Update Azure configuration"""
        config = self.get_config()
        config.azure.endpoint = endpoint
        config.azure.key = key
        
        if save:
            return self.save_config(config)
        return True
    
    def update_capture_config(self, **kwargs) -> bool:
        """Update capture configuration"""
        config = self.get_config()
        
        for key, value in kwargs.items():
            if hasattr(config.capture, key):
                setattr(config.capture, key, value)
        
        return self.save_config(config)
    
    def update_ui_config(self, **kwargs) -> bool:
        """Update UI configuration"""
        config = self.get_config()
        
        for key, value in kwargs.items():
            if hasattr(config.ui, key):
                setattr(config.ui, key, value)
        
        return self.save_config(config)

# Global configuration manager instance
config_manager = ConfigManager()

# Convenience function to get current config
def get_config() -> AppConfig:
    """Get current application configuration"""
    return config_manager.get_config()

# Convenience function to save config
def save_config(config: AppConfig) -> bool:
    """Save application configuration"""
    return config_manager.save_config(config)

# Convenience function to update Azure config
def update_azure_config(endpoint: str, key: str) -> bool:
    """Update Azure configuration"""
    return config_manager.update_azure_config(endpoint, key)

if __name__ == "__main__":
    # Test configuration management
    config = get_config()
    print(f"App: {config.app_name} v{config.app_version}")
    print(f"Azure configured: {config.azure.is_configured()}")
    print(f"Screenshots dir: {config.screenshots_path}")
    print(f"Config file: {config.config_file_path}")