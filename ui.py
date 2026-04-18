# ui.py
# ULTIMATE EXACT CLONE V2 - PRODUCTION UI

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QMessageBox,
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QComboBox, QLineEdit, QTextEdit,
    QProgressBar
)

from validators import run_full_validation
from utils import save_json


class MainWindow(QMainWindow):
    def __init__(self, parsers, gst_builder):
        super().__init__()

        self.parsers = parsers
        self.gst_builder = gst_builder
        self.files = []

        self.setWindowTitle("GST JSON Generator Pro - X10THINK")
        self.setMinimumSize(1100, 720)

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main = QVBoxLayout(central)
        main.setContentsMargins(15, 15, 15, 15)
        main.setSpacing(12)

        # Title
        title = QLabel("GST JSON Generator Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            padding: 12px;
        """)
        main.addWidget(title)

        # Top form
        top = QHBoxLayout()

        self.platform = QComboBox()
        self.platform.addItems(["Meesho", "Flipkart", "Amazon"])

        self.gstin = QLineEdit()
        self.gstin.setPlaceholderText("Enter GSTIN")

        self.period = QLineEdit()
        self.period.setPlaceholderText("MMYYYY")

        top.addWidget(QLabel("Platform"))
        top.addWidget(self.platform)

        top.addWidget(QLabel("GSTIN"))
        top.addWidget(self.gstin)

        top.addWidget(QLabel("Period"))
        top.addWidget(self.period)

        main.addLayout(top)

        # Buttons
        row = QHBoxLayout()

        self.btn_add = QPushButton("Add Files")
        self.btn_clear = QPushButton("Clear")
        self.btn_generate = QPushButton("Generate JSON")

        self.btn_add.clicked.connect(self.add_files)
        self.btn_clear.clicked.connect(self.clear_files)
        self.btn_generate.clicked.connect(self.generate_json)

        row.addWidget(self.btn_add)
        row.addWidget(self.btn_clear)
        row.addStretch()
        row.addWidget(self.btn_generate)

        main.addLayout(row)

        # File list
        self.file_list = QListWidget()
        main.addWidget(self.file_list, 2)

        # Progress
        self.progress = QProgressBar()
        self.progress.setValue(0)
        main.addWidget(self.progress)

        # Logs
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        main.addWidget(self.logs, 3)

        self.statusBar().showMessage("Ready")

    # =====================================================
    # ACTIONS
    # =====================================================

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "Excel/CSV Files (*.xlsx *.xls *.csv)"
        )

        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.file_list.addItem(f)

        self.log(f"{len(files)} file(s) added")

    def clear_files(self):
        self.files = []
        self.file_list.clear()
        self.progress.setValue(0)
        self.log("Files cleared")

    def generate_json(self):
        gstin = self.gstin.text().strip().upper()
        period = self.period.text().strip()
        platform = self.platform.currentText()

        ok, errors = run_full_validation(
            gstin=gstin,
            period=period,
            files=self.files
        )

        if not ok:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        try:
            self.progress.setValue(10)
            self.log(f"Processing {len(self.files)} files for {platform}...")

            parser = self.parsers[platform]
            parsed = parser.parse_files(self.files)

            self.progress.setValue(60)
            self.log("Data parsed successfully")

            result = self.gst_builder.build_gstr1(
                parsed,
                gstin,
                period
            )

            self.progress.setValue(85)
            self.log("JSON built successfully")

            ok2, errors2 = run_full_validation(
                gstin,
                period,
                self.files,
                parsed,
                result
            )

            if not ok2:
                QMessageBox.warning(
                    self,
                    "JSON Validation Warning",
                    "\n".join(errors2)
                )

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save JSON",
                f"GSTR1_{platform}_{period}.json",
                "JSON Files (*.json)"
            )

            if path:
                if save_json(result, path):
                    self.progress.setValue(100)
                    self.log(f"Saved: {path}")
                    QMessageBox.information(
                        self,
                        "Success",
                        "GST JSON Generated Successfully!"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Error",
                        "Failed to save file"
                    )

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.log(f"ERROR: {e}")
            self.progress.setValue(0)

    # =====================================================
    # LOG
    # =====================================================

    def log(self, text):
        self.logs.append(text)
        self.statusBar().showMessage(text)