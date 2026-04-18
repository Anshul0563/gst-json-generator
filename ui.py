# ui.py
# FINAL AUTO MERGE UI VERSION

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QMessageBox,
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QTextEdit, QComboBox,
    QProgressBar
)

from PySide6.QtCore import Qt
from validators import run_full_validation


class MainWindow(QMainWindow):
    def __init__(self, parsers, gst_builder):
        super().__init__()

        self.parsers = parsers
        self.gst_builder = gst_builder
        self.files = []

        self.init_ui()

    # =====================================================
    # UI
    # =====================================================
    def init_ui(self):
        self.setWindowTitle("GST JSON Generator Pro - Auto Merge")
        self.setGeometry(100, 100, 1250, 780)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(12)

        title = QLabel("GST JSON Generator Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size:28px;
            font-weight:700;
            padding:12px;
        """)
        root.addWidget(title)

        # -----------------------------------
        # Top Controls
        # -----------------------------------
        top = QHBoxLayout()

        self.platform = QComboBox()
        self.platform.addItems([
            "Auto Merge",
            "Meesho",
            "Flipkart",
            "Amazon"
        ])
        self.platform.setMinimumHeight(42)

        self.gstin = QLineEdit()
        self.gstin.setPlaceholderText("Enter GSTIN")
        self.gstin.setMinimumHeight(42)

        self.period = QLineEdit()
        self.period.setPlaceholderText("MMYYYY")
        self.period.setMinimumHeight(42)

        top.addWidget(self.platform)
        top.addWidget(self.gstin)
        top.addWidget(self.period)

        root.addLayout(top)

        # -----------------------------------
        # Buttons
        # -----------------------------------
        btn = QHBoxLayout()

        self.add_btn = QPushButton("Add Files")
        self.remove_btn = QPushButton("Remove Selected")
        self.clear_btn = QPushButton("Clear All")

        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn.clicked.connect(self.clear_files)

        for b in [self.add_btn, self.remove_btn, self.clear_btn]:
            b.setMinimumHeight(38)
            btn.addWidget(b)

        root.addLayout(btn)

        # -----------------------------------
        # File list
        # -----------------------------------
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(220)
        root.addWidget(self.file_list)

        # -----------------------------------
        # Generate button
        # -----------------------------------
        self.generate_btn = QPushButton("GENERATE GST JSON")
        self.generate_btn.setMinimumHeight(58)
        self.generate_btn.clicked.connect(self.generate_json)

        self.generate_btn.setStyleSheet("""
            QPushButton{
                background:#0a84ff;
                color:white;
                font-size:18px;
                font-weight:700;
                border:none;
                border-radius:8px;
            }
            QPushButton:hover{
                background:#006be6;
            }
        """)

        root.addWidget(self.generate_btn)

        # -----------------------------------
        # Progress
        # -----------------------------------
        self.progress = QProgressBar()
        self.progress.setValue(0)
        root.addWidget(self.progress)

        # -----------------------------------
        # Logs
        # -----------------------------------
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        root.addWidget(self.logs)

    # =====================================================
    # HELPERS
    # =====================================================
    def log(self, msg):
        self.logs.append(msg)

    # =====================================================
    # FILES
    # =====================================================
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Source Files",
            "",
            "Excel/CSV Files (*.xlsx *.xls *.csv)"
        )

        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.file_list.addItem(Path(f).name)

        self.log(f"{len(files)} file(s) added")

    def remove_selected(self):
        rows = sorted(
            [x.row() for x in self.file_list.selectedIndexes()],
            reverse=True
        )

        for r in rows:
            self.file_list.takeItem(r)
            self.files.pop(r)

        self.log("Selected file(s) removed")

    def clear_files(self):
        self.files.clear()
        self.file_list.clear()
        self.log("All files cleared")

    # =====================================================
    # MAIN
    # =====================================================
    def generate_json(self):
        gstin = self.gstin.text().strip().upper()
        period = self.period.text().strip()
        mode = self.platform.currentText()

        self.progress.setValue(10)

        ok, errors = run_full_validation(gstin, period, self.files)
        if not ok:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        try:
            self.log(f"Processing {len(self.files)} files using {mode}...")
            self.progress.setValue(25)

            parser = self.parsers[mode]
            parsed = parser.parse_files(self.files)

            self.progress.setValue(70)

            final_json = self.gst_builder.build_gstr1(
                parsed,
                gstin,
                period
            )

            self.progress.setValue(90)

            default_name = f"GSTR1_{mode}_{period}.json"

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save JSON",
                default_name,
                "JSON Files (*.json)"
            )

            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(final_json, f, indent=2, ensure_ascii=False)

                self.progress.setValue(100)
                self.log("JSON generated successfully")

                QMessageBox.information(
                    self,
                    "Success",
                    "GST JSON Generated Successfully!"
                )

        except Exception as e:
            self.progress.setValue(0)
            self.log(f"ERROR: {str(e)}")

            QMessageBox.critical(self, "Error", str(e))