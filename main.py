# main.py
# ADVANCED APPLICATION WITH CONFIGURATION, LOGGING, AND ERROR HANDLING

import sys
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication

from config import init_config
from logger import get_logger
from ui import MainWindow
from gst_builder import GSTBuilder
from parsers import (
    AutoMergeParser,
    MeeshoParser,
    FlipkartParser,
    AmazonParser
)


def setup_application() -> None:
    """Initialize application configuration and logging."""
    # Initialize configuration
    config_file = Path("config.json")
    config = init_config(str(config_file))
    
    # Validate configuration
    is_valid, errors = config.validate()
    if not is_valid:
        print(f"Configuration validation warnings: {errors}")
    
    # Initialize logging
    logger = get_logger()
    logger.info("Application starting...")
    logger.info(f"Configuration loaded from {config_file if config_file.exists() else 'defaults'}")


def create_parsers() -> dict:
    """Create and initialize all parsers."""
    logger = get_logger()
    logger.info("Initializing parsers...")
    
    parsers = {
        "Auto Merge": AutoMergeParser(),
        "Meesho": MeeshoParser(),
        "Flipkart": FlipkartParser(),
        "Amazon": AmazonParser(),
    }
    
    logger.info(f"Loaded {len(parsers)} parsers: {', '.join(parsers.keys())}")
    return parsers


def main():
    """Main application entry point."""
    try:
        # Setup application
        setup_application()
        logger = get_logger()
        
        # Create Qt application
        app = QApplication(sys.argv)
        logger.info("Qt application created")
        
        # Initialize core components
        parsers = create_parsers()
        builder = GSTBuilder()
        logger.info("GST Builder initialized")
        
        # Create and show main window
        window = MainWindow(parsers, builder)
        window.show()
        logger.info("Main window displayed")
        
        # Run application
        exit_code = app.exec()
        logger.info(f"Application exiting with code {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger = get_logger()
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()