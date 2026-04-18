
import sys
from PySide6.QtWidgets import QApplication

from ui import MainWindow
from parsers import MeeshoParser, FlipkartParser, AmazonParser
from gst_builder import GSTBuilder
from utils import setup_logging


def main():
    # logging
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("GST JSON Generator Pro")
    app.setOrganizationName("X10THINK")

    # parsers
    parsers = {
        "Meesho": MeeshoParser(),
        "Flipkart": FlipkartParser(),
        "Amazon": AmazonParser(),
    }

    # builder
    builder = GSTBuilder()

    # ui
    window = MainWindow(parsers, builder)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()