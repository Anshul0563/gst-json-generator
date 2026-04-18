# ui.py
# ADVANCED UI WITH EXPORT OPTIONS AND ENHANCED LOGGING

import json
import time
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QMessageBox,
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QTextEdit, QComboBox,
    QProgressBar, QCheckBox
)
from PySide6.QtCore import Qt, QCoreApplication

from validators import run_full_validation
from exporter import Exporter
from logger import get_logger


class MainWindow(QMainWindow):
    def __init__(self, parsers, builder):
        super().__init__()

        self.parsers = parsers
        self.builder = builder
        self.files = []
        self.logger = get_logger()

        self.setup_ui()

    # =====================================================
    def setup_ui(self):
        self.setWindowTitle("GST JSON Generator Pro v2.0")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(12)

        title = QLabel("GST JSON Generator Pro v2.0")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size:28px;font-weight:700;padding:10px;"
        )
        root.addWidget(title)

        # top controls
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

        # Export options
        export_row = QHBoxLayout()
        export_row.addWidget(QLabel("Export Formats:"))
        
        self.export_json = QCheckBox("JSON")
        self.export_json.setChecked(True)
        
        self.export_csv = QCheckBox("CSV")
        self.export_excel = QCheckBox("Excel")
        
        export_row.addWidget(self.export_json)
        export_row.addWidget(self.export_csv)
        export_row.addWidget(self.export_excel)
        export_row.addStretch()
        
        root.addLayout(export_row)

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

        # generate button
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
    def refresh_ui(self):
        QCoreApplication.processEvents()

    def log(self, msg):
        self.logs.append(msg)
        self.logger.info(msg)
        self.refresh_ui()

    def set_progress(self, value):
        self.progress.setValue(value)
        self.refresh_ui()

    def set_busy(self, busy=True):
        self.btn_generate.setDisabled(busy)
        self.btn_add.setDisabled(busy)
        self.btn_remove.setDisabled(busy)
        self.btn_clear.setDisabled(busy)
        self.refresh_ui()

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

        self.log(f"✅ {added} file(s) added")

    def remove_selected(self):
        rows = sorted(
            [x.row() for x in self.list_files.selectedIndexes()],
            reverse=True
        )

        for r in rows:
            self.list_files.takeItem(r)
            self.files.pop(r)

        self.log("✅ Selected file(s) removed")

    def clear_all(self):
        self.files.clear()
        self.list_files.clear()
        self.set_progress(0)
        self.log("✅ All files cleared")

    # =====================================================
    def generate(self):
        gstin = self.gstin.text().strip().upper()
        period = self.period.text().strip()
        mode = self.mode.currentText()

        ok, errors = run_full_validation(gstin, period, self.files)

        if not ok:
            error_msg = "\n".join(errors)
            QMessageBox.warning(
                self,
                "Validation Error",
                error_msg
            )
            self.logger.warning(f"Validation failed: {error_msg}")
            return

        try:
            self.set_busy(True)
            self.logs.clear()
            start_time = time.time()

            self.log("✓ Validation passed")
            self.set_progress(10)

            self.log("⏳ Parsing files...")
            parser = self.parsers[mode]

            self.set_progress(25)
            parsed = parser.parse_files(self.files)

            if not parsed:
                raise ValueError("No data parsed from files")

            self.log("✓ Files parsed successfully")
            self.set_progress(70)

            self.log("⏳ Building JSON...")
            output = self.builder.build_gstr1(
                parsed,
                gstin,
                period
            )

            # Validate output
            is_valid, errors = self.builder.validate_output(output)
            if not is_valid:
                raise ValueError(f"Output validation failed: {', '.join(errors)}")

            self.log("✓ JSON built and validated")
            self.set_progress(85)

            # Determine export formats
            formats = []
            if self.export_json.isChecked():
                formats.append('json')
            if self.export_csv.isChecked():
                formats.append('csv')
            if self.export_excel.isChecked():
                formats.append('xlsx')

            if not formats:
                self.log("⚠ No export formats selected")
                self.set_progress(0)
                self.set_busy(False)
                return

            # Export files
            from config import get_config
            config = get_config()
            output_dir = config.get('output.output_dir', './output')

            exporter = Exporter(output_dir)
            base_name = f"GSTR1_{mode}_{period}"

            results = exporter.export(output, base_name, formats)

            self.log("✓ Files exported:")
            for fmt, result in results.items():
                if "ERROR" in str(result):
                    self.log(f"  ✗ {fmt}: {result}")
                else:
                    self.log(f"  ✓ {fmt}: {Path(result).name}")

            self.set_progress(100)

            duration = time.time() - start_time
            self.logger.perf("GST JSON generation", duration, len(parsed.get('summary', {}).get('rows', [])))

            self.log(f"✓ Completed in {duration:.2f}s")

            QMessageBox.information(
                self,
                "Success",
                f"GST JSON Generated Successfully\nOutput: {output_dir}"
            )

        except Exception as e:
            self.set_progress(0)
            error_msg = f"Error: {str(e)}"
            self.log(error_msg)
            self.logger.exception(f"Generation failed: {error_msg}")

            QMessageBox.critical(
                self,
                "Error",
                error_msg
            )

        finally:
            self.set_busy(False)
