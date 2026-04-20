#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GST JSON Generator Pro v2.0
Production-grade desktop application for GSTR-1 JSON generation.

Main entry point with complete error handling, logging, and initialization.
"""

import sys
import logging
from pathlib import Path

# Version check
if sys.version_info < (3, 10):
    print("Error: Python 3.10+ is required")
    sys.exit(1)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

from config import init_config, get_config
from logger import get_logger
from ui import MainWindow
from gst_builder import GSTBuilder
from parsers import (
    AutoMergeParser,
    MeeshoParser,
    AmazonParser
)


def setup_application() -> bool:
    """
    Initialize application configuration and logging.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize configuration
        config_file = Path("config.json")
        config = init_config(str(config_file))
        
        # Validate configuration
        is_valid, errors = config.validate()
        if not is_valid:
            logger = get_logger()
            for error in errors:
                logger.warning(f"Configuration warning: {error}")
        
        # Initialize logging
        logger = get_logger()
        logger.info("=" * 60)
        logger.info("GST JSON Generator Pro v2.0 Starting")
        logger.info("=" * 60)
        logger.info(f"Configuration loaded from {config_file if config_file.exists() else 'defaults'}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {Path.cwd()}")
        
        return True
        
    except Exception as e:
        print(f"Fatal error during setup: {e}")
        logger = get_logger()
        logger.critical(f"Setup failed: {e}", exc_info=True)
        return False


def create_parsers() -> dict:
    """
    Create and initialize all available parsers.
    
    Returns:
        Dictionary mapping parser names to parser instances
    """
    logger = get_logger()
    
    try:
        parsers = {
            "Auto Merge": AutoMergeParser(),
            "Meesho": MeeshoParser(),
            "Amazon": AmazonParser(),
        }
        
        logger.info(f"Loaded {len(parsers)} parsers: {', '.join(parsers.keys())}")
        return parsers
        
    except Exception as e:
        logger.error(f"Failed to initialize parsers: {e}", exc_info=True)
        raise


def main():
    """Main application entry point."""
    logger = None
    app = None
    
    try:
        # Setup
        if not setup_application():
            sys.exit(1)
        
        logger = get_logger()
        logger.info("Application setup completed successfully")
        
        # Create Qt application
        app = QApplication(sys.argv)
        logger.info("Qt application created")
        
        # Initialize core components
        logger.info("Initializing parsers...")
        parsers = create_parsers()
        
        logger.info("Initializing GST Builder...")
        builder = GSTBuilder()
        
        # Create and show main window
        logger.info("Creating main window...")
        window = MainWindow(parsers, builder)
        window.show()
        logger.info("Main window displayed")
        
        logger.info("Application ready")
        logger.info("=" * 60)
        
        # Run application
        exit_code = app.exec()
        logger.info(f"Application closing with exit code: {exit_code}")
        logger.info("=" * 60)
        sys.exit(exit_code)
        
    except Exception as e:
        error_msg = f"Fatal error: {str(e)}"
        print(error_msg)
        if logger:
            logger.critical(error_msg, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
