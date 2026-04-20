#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui.py - Professional PySide6 Desktop GUI for GST GSTR-1 JSON Generator
Modern dark-themed interface with file management, parsing, and export.
"""

import json
import time
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QMessageBox,
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit, QComboBox,
    QProgressBar, QCheckBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QSpinBox, QFormLayout, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, QCoreApplication, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QColor

from validators import Validator
from logger import get_logger


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, parsers: dict, builder):
        super().__init__()
        self.setWindowTitle("GST JSON Generator Pro v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        self.parsers = parsers
        self.builder = builder
        self.files: List[str] = []
        self.logger = get_logger()
        self.output_data = None
        
        self.setup_ui()
        self.apply_stylesheet()

    def setup_ui(self):
        """Setup the complete UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        root = QVBoxLayout(central)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(10)
        
        # Header
        self._setup_header(root)
        
        # Main content split between left and right
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Input controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self._setup_input_panel(left_layout)
        
        # Right side: Output and logs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self._setup_output_panel(right_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        
        root.addWidget(splitter)
        
        # Status bar
        self._setup_status_bar()

    def _setup_header(self, layout):
        """Setup header section."""
        header_layout = QVBoxLayout()
        
        title = QLabel("GST GSTR-1 JSON Generator Pro v2.0")
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Complete GSTR-1 JSON generation from Meesho & Amazon marketplace data")
        subtitle.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setItalic(True)
        subtitle.setFont(font)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)

    def _setup_input_panel(self, layout):
        """Setup input panel."""
        # Parser selection
        parser_group = QGroupBox("Parser Configuration")
        parser_layout = QFormLayout()
        
        self.mode = QComboBox()
        self.mode.addItems(list(self.parsers.keys()))
        parser_layout.addRow("Select Parser:", self.mode)
        
        self.gstin = QLineEdit()
        self.gstin.setPlaceholderText("e.g., 07TCRPS8655B1ZK")
        self.gstin.setMaxLength(15)
        parser_layout.addRow("GSTIN:", self.gstin)
        
        self.period = QLineEdit()
        self.period.setPlaceholderText("e.g., 042024 (MMYYYY)")
        self.period.setMaxLength(6)
        parser_layout.addRow("Filing Period:", self.period)
        
        parser_group.setLayout(parser_layout)
        layout.addWidget(parser_group)
        
        # File management
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout()
        
        file_buttons = QHBoxLayout()
        self.btn_add = self._create_button("+ Add Files", self.add_files)
        self.btn_remove = self._create_button("- Remove Selected", self.remove_selected)
        self.btn_clear = self._create_button("Clear All", self.clear_all)
        
        file_buttons.addWidget(self.btn_add)
        file_buttons.addWidget(self.btn_remove)
        file_buttons.addWidget(self.btn_clear)
        file_layout.addLayout(file_buttons)
        
        self.list_files = QListWidget()
        self.list_files.setMaximumHeight(150)
        file_layout.addWidget(self.list_files)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Export options
        export_group = QGroupBox("Export Options")
        export_layout = QHBoxLayout()
        
        self.export_json = QCheckBox("JSON")
        self.export_json.setChecked(True)
        self.export_csv = QCheckBox("CSV")
        self.export_excel = QCheckBox("Excel")
        
        export_layout.addWidget(self.export_json)
        export_layout.addWidget(self.export_csv)
        export_layout.addWidget(self.export_excel)
        export_layout.addStretch()
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # Generate button
        self.btn_generate = self._create_button("GENERATE GST JSON", self.generate, primary=True)
        self.btn_generate.setMinimumHeight(50)
        layout.addWidget(self.btn_generate)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        layout.addStretch()

    def _setup_output_panel(self, layout):
        """Setup output panel with tabs."""
        tab_widget = QTabWidget()
        
        # JSON Preview tab
        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setPlaceholderText("JSON output will appear here...")
        tab_widget.addTab(self.json_preview, "JSON Preview")
        
        # Logs tab
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setPlaceholderText("Operation logs will appear here...")
        tab_widget.addTab(self.logs, "Logs")
        
        # Summary tab
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setPlaceholderText("Summary and statistics will appear here...")
        tab_widget.addTab(self.summary, "Summary")
        
        layout.addWidget(tab_widget)
        
        # Export button
        self.btn_export = self._create_button("Export to File", self.export_json_file)
        layout.addWidget(self.btn_export)

    def _setup_status_bar(self):
        """Setup status bar."""
        self.statusBar().showMessage("Ready")

    def _create_button(self, text: str, callback, primary: bool = False) -> QPushButton:
        """Create a styled button."""
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        if primary:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #1084d7;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
                QPushButton:disabled {
                    background-color: #90caf9;
                }
            """)
        return btn

    def apply_stylesheet(self):
        """Apply dark theme stylesheet."""
        stylesheet = """
            QMainWindow {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #3f3f3f;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #e0e0e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QLineEdit, QTextEdit, QComboBox, QListWidget, QTableWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3f3f3f;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QPushButton {
                background-color: #3f3f3f;
                color: #e0e0e0;
                border: none;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4f4f4f;
            }
            QProgressBar {
                border: 1px solid #3f3f3f;
                border-radius: 3px;
                background-color: #2d2d2d;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
            }
            QCheckBox {
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #3f3f3f;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 8px 20px;
                border: 1px solid #3f3f3f;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
        """
        self.setStyleSheet(stylesheet)

    def refresh_ui(self):
        """Process events to refresh UI."""
        QCoreApplication.processEvents()

    def log(self, msg: str):
        """Log message to logs tab."""
        self.logs.append(msg)
        self.logger.info(msg)
        self.refresh_ui()

    def set_progress(self, value: int):
        """Set progress bar value."""
        self.progress.setValue(value)
        self.refresh_ui()

    def set_busy(self, busy: bool = True):
        """Enable/disable controls based on busy state."""
        self.btn_generate.setDisabled(busy)
        self.btn_add.setDisabled(busy)
        self.btn_remove.setDisabled(busy)
        self.btn_clear.setDisabled(busy)
        self.btn_export.setDisabled(busy)
        self.refresh_ui()

    # =====================================================
    # File Management
    # =====================================================
    def add_files(self):
        """Add files to the list."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Input Files",
            "",
            "Spreadsheet Files (*.xlsx *.xls *.csv);;All Files (*)"
        )
        
        added = 0
        for f in files:
            if f not in self.files:
                self.files.append(f)
                item = QListWidgetItem(Path(f).name)
                item.setToolTip(f)
                self.list_files.addItem(item)
                added += 1
        
        self.log(f"✓ {added} file(s) added")
        self.statusBar().showMessage(f"Files: {len(self.files)}")

    def remove_selected(self):
        """Remove selected files."""
        for item in self.list_files.selectedItems():
            row = self.list_files.row(item)
            self.list_files.takeItem(row)
            self.files.pop(row)
        
        self.log(f"✓ Selected file(s) removed")
        self.statusBar().showMessage(f"Files: {len(self.files)}")

    def clear_all(self):
        """Clear all files."""
        self.files.clear()
        self.list_files.clear()
        self.set_progress(0)
        self.summary.clear()
        self.json_preview.clear()
        self.log("✓ All files cleared")
        self.statusBar().showMessage("Ready")

    # =====================================================
    # Generation Logic
    # =====================================================
    def generate(self):
        """Generate GSTR-1 JSON."""
        gstin = self.gstin.text().strip().upper()
        period = self.period.text().strip()
        mode = self.mode.currentText()
        
        # Validate inputs
        valid, errors = self._validate_inputs(gstin, period, self.files)
        if not valid:
            error_msg = "\n".join(errors)
            QMessageBox.warning(self, "Validation Error", error_msg)
            self.logger.warning(f"Validation failed: {error_msg}")
            return
        
        try:
            self.set_busy(True)
            self.logs.clear()
            self.json_preview.clear()
            self.summary.clear()
            start_time = time.time()
            
            self.log("✓ Input validation passed")
            self.set_progress(10)
            self.statusBar().showMessage("Parsing files...")
            
            # Parse files
            self.log(f"⏳ Parsing with {mode} parser...")
            parser = self.parsers[mode]
            self.set_progress(30)
            
            parsed = parser.parse_files(self.files, seller_gstin=gstin)
            if not parsed:
                raise ValueError("No data parsed from files. Check file formats and content.")
            
            self.log(f"✓ Files parsed successfully")
            self.set_progress(60)
            self.statusBar().showMessage("Building JSON...")
            
            # Build JSON
            self.log("⏳ Building GSTR-1 JSON...")
            output = self.builder.build_gstr1(parsed, gstin, period)
            self.set_progress(80)
            
            # Validate output
            self.log("⏳ Validating output...")
            is_valid, validation_errors = self.builder.validate_output(output)
            
            if not is_valid:
                error_msg = "\n".join(validation_errors)
                raise ValueError(f"Output validation failed:\n{error_msg}")
            
            self.log("✓ JSON validation passed")
            self.output_data = output
            self.set_progress(90)
            
            # Display results
            self._display_results(output, parsed)
            self.set_progress(100)
            
            duration = time.time() - start_time
            self.logger.info(f"Generation completed in {duration:.2f}s")
            self.log(f"✓ Completed in {duration:.2f}s")
            
            QMessageBox.information(
                self,
                "Success",
                "GSTR-1 JSON Generated Successfully!\n\nYou can now export to file."
            )
            self.statusBar().showMessage("Ready - JSON generated successfully")
            
        except Exception as e:
            self.set_progress(0)
            error_msg = f"Error: {str(e)}"
            self.log(f"✗ {error_msg}")
            self.logger.exception(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            self.statusBar().showMessage("Error during generation")
            
        finally:
            self.set_busy(False)

    def _validate_inputs(self, gstin: str, period: str, files: List[str]) -> tuple:
        """Validate all inputs."""
        errors = []
        
        # Validate GSTIN
        if not gstin:
            errors.append("GSTIN cannot be empty")
        else:
            valid, err = Validator.validate_gstin(gstin)
            if not valid:
                errors.append(err or f"Invalid GSTIN: {gstin}")
        
        # Validate period
        if not period:
            errors.append("Filing period cannot be empty")
        else:
            valid, err = Validator.validate_period(period)
            if not valid:
                errors.append(err or f"Invalid period: {period}")
        
        # Validate files
        if not files:
            errors.append("Please select at least one file")
        else:
            valid, file_errors = Validator.validate_files(files)
            if not valid:
                errors.extend(file_errors)
        
        return len(errors) == 0, errors

    def _display_results(self, output: dict, parsed: dict):
        """Display results in tabs."""
        # JSON Preview
        json_str = json.dumps(output, indent=2, ensure_ascii=False)
        self.json_preview.setPlainText(json_str)
        
        # Summary
        summary_text = self._build_summary_text(output, parsed)
        self.summary.setPlainText(summary_text)

    def _build_summary_text(self, output: dict, parsed: dict) -> str:
        """Build summary text."""
        lines = [
            "=== GSTR-1 GENERATION SUMMARY ===\n",
            "GSTIN Information:",
            f"  GSTIN: {output.get('gstin')}",
            f"  Filing Period: {output.get('fp')}",
            f"  Version: {output.get('version')}\n",
            "Data Summary:",
            f"  Total Items: {output.get('summary', {}).get('total_items')}",
            f"  Total Taxable Value: ₹{output.get('summary', {}).get('total_taxable', 0):.2f}",
            f"  Total Tax: ₹{output.get('summary', {}).get('total_tax', 0):.2f}",
            f"    - IGST: ₹{output.get('summary', {}).get('total_igst', 0):.2f}",
            f"    - CGST: ₹{output.get('summary', {}).get('total_cgst', 0):.2f}",
            f"    - SGST: ₹{output.get('summary', {}).get('total_sgst', 0):.2f}\n",
            "State-wise Distribution:",
        ]
        
        for row in output.get('summary', {}).get('total_taxable', 0):
            if isinstance(row, dict):
                lines.append(f"  POS {row.get('pos')}: ₹{row.get('taxable_value', 0):.2f}")
        
        # Supplier info if available
        clttx = output.get('supeco', {}).get('clttx', [])
        if clttx:
            lines.append("\nSuppliers:")
            for supplier in clttx:
                lines.append(f"  {supplier.get('etin')}: ₹{supplier.get('suppval', 0):.2f}")
        
        return "\n".join(lines)

    def export_json_file(self):
        """Export JSON to file."""
        if not self.output_data:
            QMessageBox.warning(self, "Warning", "No JSON generated yet. Please generate first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save GSTR-1 JSON",
            f"GSTR1_{int(time.time())}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.builder.save_json(self.output_data, file_path)
                self.log(f"✓ JSON exported to {Path(file_path).name}")
                QMessageBox.information(
                    self,
                    "Success",
                    f"JSON exported successfully to:\n{file_path}"
                )
                self.statusBar().showMessage(f"Exported to {Path(file_path).name}")
            except Exception as e:
                self.logger.error(f"Export failed: {e}")
                QMessageBox.critical(self, "Error", f"Export failed: {e}")
