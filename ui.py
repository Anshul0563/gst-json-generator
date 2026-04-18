# ui.py
# UPDATED FINAL STABLE UI
# Better progress + no freeze feeling + reset states

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
    def __init__(self, parsers, builder):
        super().__init__()

        self.parsers = parsers
        self.builder = builder
        self.files = []

        self.setup_ui()

    # =====================================================
    def setup_ui(self):
        self.setWindowTitle("GST JSON Generator Pro")
        self.resize(1200, 760)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(12)

        title = QLabel("GST JSON Generator Pro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size:28px;font-weight:700;padding:10px;"
        )
        root.addWidget(title)

        # controls
        row = QHBoxLayout()

        self.mode = QComboBox()
        self.mode.addItems([
            "Auto Merge",
            "Meesho",
            "Flipkart",
            "Amazon"
        ])

        self.gstin = QLineEdit()
        self.gstin.setPlaceholderText("GSTIN")

        self.period = QLineEdit()
        self.period.setPlaceholderText("MMYYYY")

        row.addWidget(self.mode)
        row.addWidget(self.gstin)
        row.addWidget(self.period)

        root.addLayout(row)

        # buttons
        btns = QHBoxLayout()

        self.btn_add = QPushButton("Add Files")
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_clear = QPushButton("Clear All")

        self.btn_add.clicked.connect(self.add_files)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_all)

        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_remove)
        btns.addWidget(self.btn_clear)

        root.addLayout(btns)

        # file list
        self.list_files = QListWidget()
        root.addWidget(self.list_files)

        # generate
        self.btn_generate = QPushButton("GENERATE GST JSON")
        self.btn_generate.setMinimumHeight(55)
        self.btn_generate.clicked.connect(self.generate)

        self.btn_generate.setStyleSheet("""
            QPushButton {
                background:#0a84ff;
                color:white;
                font-size:18px;
                font-weight:700;
                border:none;
                border-radius:8px;
            }
            QPushButton:disabled {
                background:#8ab8ff;
            }
        """)

        root.addWidget(self.btn_generate)

        # progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        # logs
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        root.addWidget(self.logs)

    # =====================================================
    def log(self, msg):
        self.logs.append(msg)

    def set_busy(self, busy=True):
        self.btn_generate.setDisabled(busy)
        self.btn_add.setDisabled(busy)
        self.btn_remove.setDisabled(busy)
        self.btn_clear.setDisabled(busy)

    # =====================================================
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "Excel/CSV Files (*.xlsx *.xls *.csv)"
        )

        added = 0

        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.list_files.addItem(Path(f).name)
                added += 1

        self.log(f"{added} file(s) added")

    def remove_selected(self):
        rows = sorted(
            [x.row() for x in self.list_files.selectedIndexes()],
            reverse=True
        )

        for r in rows:
            self.list_files.takeItem(r)
            self.files.pop(r)

        self.log("Selected file(s) removed")

    def clear_all(self):
        self.files.clear()
        self.list_files.clear()
        self.progress.setValue(0)
        self.log("All files cleared")

    # =====================================================
    def generate(self):
        gstin = self.gstin.text().strip().upper()
        period = self.period.text().strip()
        mode = self.mode.currentText()

        ok, errors = run_full_validation(gstin, period, self.files)

        if not ok:
            QMessageBox.warning(
                self,
                "Validation Error",
                "\n".join(errors)
            )
            return

        try:
            self.set_busy(True)
            self.progress.setValue(5)
            self.log("Validation passed")

            self.log("Reading files...")
            self.progress.setValue(20)

            parser = self.parsers[mode]
            parsed = parser.parse_files(self.files)

            self.log("Files parsed successfully")
            self.progress.setValue(70)

            self.log("Building JSON...")
            output = self.builder.build_gstr1(
                parsed,
                gstin,
                period
            )

            self.progress.setValue(85)

            save_name = f"GSTR1_{mode}_{period}.json"

            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save JSON",
                save_name,
                "JSON Files (*.json)"
            )

            if not path:
                self.progress.setValue(0)
                self.log("Save cancelled")
                self.set_busy(False)
                return

            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    output,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            self.progress.setValue(100)
            self.log("Done")

            QMessageBox.information(
                self,
                "Success",
                "GST JSON Generated Successfully"
            )

        except Exception as e:
            self.progress.setValue(0)
            self.log(f"Error: {str(e)}")

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

        finally:
            self.set_busy(False)