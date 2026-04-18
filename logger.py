"""
logger.py - Advanced Logging System
Structured logging with file/console output and performance tracking
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


class AdvancedLogger:
    """Professional logging system with rotation and performance tracking."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._setup_logging()
            self._initialized = True
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        from config import get_config
        
        config = get_config()
        log_level = config.get('logging.level', 'INFO')
        log_file = config.get('logging.file', 'logs/app.log')
        max_size = config.get('logging.max_size', 10485760)
        backup_count = config.get('logging.backup_count', 5)
        log_format = config.get('logging.format')
        
        # Create logger
        self.logger = logging.getLogger('GST-Tool')
        self.logger.setLevel(getattr(logging, log_level))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # File handler with rotation
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(msg, *args, **kwargs)
    
    def perf(self, operation: str, duration: float, records: int = 0) -> None:
        """Log performance metrics."""
        msg = f"PERF: {operation} completed in {duration:.2f}s"
        if records > 0:
            msg += f" ({records} records)"
        self.logger.info(msg)


def get_logger() -> AdvancedLogger:
    """Get or create logger instance."""
    return AdvancedLogger()
