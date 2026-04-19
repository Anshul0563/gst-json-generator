"""
config.py - Application Configuration Management
Centralized configuration with validation and hot-reload support
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not required, but helpful if installed
    pass


class Config:
    """Advanced configuration manager with validation and caching."""
    
    DEFAULT_CONFIG = {
        "app": {
            "name": "GST JSON Generator Pro",
            "version": "2.0.0",
            "debug": False,
            "auto_save": True,
            "batch_limit": 50
        },
        "parser": {
            "encoding_fallback": True,
            "encodings": ["utf-8", "latin1", "iso-8859-1"],
            "skip_sheets": ["summary", "pivot", "total", "dashboard", "overview"],
            "max_rows": 100000,
            "chunk_size": 5000
        },
"gst": {
            "default_tax_rate": 3.0,
            "flipkart_value_mode": "AUTO",
            "igst_states": ["non-delhi"],
            "cgst_rate": 1.5,
            "sgst_rate": 1.5,
            "cess_rate": 0,
            "version": "GST3.1.6"
        },
        "output": {
            "formats": ["json", "csv", "xlsx"],
            "indent": 2,
            "ensure_ascii": False,
            "timestamp_output": True,
            "output_dir": "./output"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/app.log",
            "max_size": 10485760,  # 10MB
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "validation": {
            "strict_mode": False,
            "allow_duplicates": False,
            "max_file_size_mb": 500,
            "check_file_integrity": True
        },
        "cache": {
            "enabled": True,
            "ttl": 3600,  # 1 hour
            "max_size_mb": 100
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._config_file = config_file or "config.json"
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file if exists."""
        config_path = Path(self._config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_config(user_config)
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")
    
    def _merge_config(self, user_config: Dict) -> None:
        """Recursively merge user config with defaults."""
        for key, value in user_config.items():
            if key in self._config and isinstance(value, dict):
                if isinstance(self._config[key], dict):
                    self._config[key].update(value)
            else:
                self._config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
    
    def save(self, file_path: Optional[str] = None) -> None:
        """Save configuration to file."""
        path = file_path or self._config_file
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def to_dict(self) -> Dict:
        """Get entire configuration as dictionary."""
        return self._config.copy()
    
    def validate(self) -> tuple:
        """Validate configuration. Returns (is_valid, errors)."""
        errors = []
        
        # Validate output directory
        output_dir = self.get('output.output_dir')
        if output_dir and not Path(output_dir).exists():
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Validate logging
        log_file = self.get('logging.file')
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Validate tax rates
        tax_rate = self.get('gst.default_tax_rate', 0)
        if tax_rate < 0 or tax_rate > 100:
            errors.append("Invalid tax rate")
        
        return len(errors) == 0, errors


# Global config instance
_global_config = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def init_config(config_file: Optional[str] = None) -> Config:
    """Initialize global config instance."""
    global _global_config
    _global_config = Config(config_file)
    return _global_config
