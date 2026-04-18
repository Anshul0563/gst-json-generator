# main.py
# ULTIMATE REBUILD MAIN

import sys
from PySide6.QtWidgets import QApplication

from ui import MainWindow
from gst_builder import GSTBuilder
from parsers import (
    AutoMergeParser,
    MeeshoParser,
    FlipkartParser,
    AmazonParser
)


def main():
    app = QApplication(sys.argv)

    parsers = {
        "Auto Merge": AutoMergeParser(),
        "Meesho": MeeshoParser(),
        "Flipkart": FlipkartParser(),
        "Amazon": AmazonParser(),
    }

    builder = GSTBuilder()

    window = MainWindow(parsers, builder)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()