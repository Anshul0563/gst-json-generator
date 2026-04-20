# GST JSON Generator Pro v2.0

**A Complete Production-Grade Desktop Application for GSTR-1 JSON Generation**

---

## 📋 Overview

GST JSON Generator Pro is a professional desktop application built with **PySide6** that automates the generation of valid **GSTR-1 JSON files** from marketplace data (Meesho & Amazon). It eliminates manual data entry, ensures GST compliance, and generates audit-ready JSON in seconds.

---

## ✨ Key Features

### 🎯 Core Functionality
- **Multi-Format Support**: Parse Meesho, Amazon, and MTR CSV files
- **Auto-Merge**: Automatically detect and merge data from multiple sources
- **Smart GSTIN Detection**: Automatically determine seller state and calculate correct tax split
- **Valid GSTR-1 Output**: Generates GST3.1.6 compliant JSON
- **Real-time Validation**: Comprehensive error checking and validation

### 🖥️ User Interface
- **Modern Dark Theme**: Professional PySide6 interface
- **Intuitive Workflow**: Simple 5-step process to generate JSON
- **Real-time Logging**: View detailed logs and progress updates
- **Multiple Export Options**: Save as JSON, CSV, or Excel
- **Summary Dashboard**: View reconciliation and state-wise breakdown

### 🛡️ Data Integrity
- **Automatic Deduplication**: Eliminates duplicate entries
- **Encoding Detection**: Handles UTF-8, Latin-1, and mixed encodings
- **Comprehensive Validation**: Validates GSTIN, period, and file content
- **Error Reporting**: Detailed error messages for troubleshooting

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **pip** (Python package manager)
- **~500MB disk space** for dependencies

### Installation

1. **Clone the Repository**
```bash
git clone <repository-url>
cd GST-Tool
```

2. **Create Virtual Environment** (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the Application**
```bash
python3 main.py
```

---

## 📖 Usage Guide

### Step 1: Select Parser
Choose the appropriate parser for your data source:
- **Auto Merge**: Automatically detects and merges Meesho & Amazon data
- **Meesho**: Parse Meesho-specific export files
- **Amazon**: Parse Amazon/MTR CSV files

### Step 2: Enter GSTIN
Enter your seller's **15-digit GSTIN** (e.g., `07TCRPS8655B1ZK`)
- The first 2 digits are the state code (determines CGST/SGST vs IGST split)
- The system validates the format automatically

### Step 3: Enter Filing Period
Enter the **filing period in MMYYYY format** (e.g., `042024` for April 2024)
- MM: 01-12 (January-December)
- YYYY: 2000-2099 (Year)

### Step 4: Select Files
Add one or more files:
- Supported: `.xlsx`, `.xls`, `.csv`
- Maximum file size: 500MB per file
- You can add multiple files from different sources

### Step 5: Generate & Export
1. Click **GENERATE GST JSON** to process
2. View the JSON preview, logs, and summary
3. Click **Export to File** to save the JSON

---

## 📁 Supported File Formats

### Meesho
- `tcs_sales.xlsx` / `tcs_sales.csv`
- `tcs_sales_return.xlsx` / `tcs_sales_return.csv`
- `tax_invoice_details.xlsx`
- Any file with columns: `sub_order_num`, `end_customer_state_new`, `total_taxable_sale_value`

### Amazon
- Amazon settlement CSVs
- MTR (Marketplace Transaction Report) CSV
- Any CSV with columns: `invoice_number`, `ship_to_state`, `tax_exclusive_gross`, `igst_tax`, `cgst_tax`, `sgst_tax`

---

## 🎨 UI Components

### Parser Configuration
- Parser dropdown selector
- GSTIN input field (with validation)
- Filing period input (MMYYYY format)

### File Selection
- **Add Files**: Select multiple files
- **Remove Selected**: Remove specific files from the list
- **Clear All**: Clear all files and start over

### Export Options
- JSON (default, always recommended)
- CSV (optional, for spreadsheet view)
- Excel (.xlsx) (optional, for formatted output)

### Progress & Logs
- Real-time progress bar (0-100%)
- Detailed operation logs in Logs tab
- JSON preview in JSON Preview tab
- Summary statistics in Summary tab

---

## 📊 JSON Output Structure

### Complete GSTR-1 Format
```json
{
  "gstin": "07TCRPS8655B1ZK",
  "fp": "042024",
  "version": "GST3.1.6",
  "hash": "hash",
  
  "b2cs": [
    {
      "sply_ty": "INTRA",
      "rt": 3.0,
      "typ": "OE",
      "pos": "07",
      "txval": 500.00,
      "csamt": 0,
      "camt": 7.50,
      "samt": 7.50
    }
  ],
  
  "supeco": {
    "clttx": [
      {
        "etin": "07AARCM9332R1CQ",
        "suppval": 1200.00,
        "igst": 21.00,
        "cgst": 7.50,
        "sgst": 7.50,
        "cess": 0,
        "flag": "N"
      }
    ]
  },
  
  "doc_issue": {
    "doc_det": []
  },
  
  "summary": {
    "total_items": 1,
    "total_taxable": 500.00,
    "total_igst": 0,
    "total_cgst": 7.50,
    "total_sgst": 7.50,
    "total_tax": 15.00
  }
}
```

---

## 🗺️ State Mapping

The application supports all 38 GST states:

| Code | State | Cities |
|------|-------|--------|
| 07 | Delhi | New Delhi, Delhi |
| 09 | Uttar Pradesh | Noida, Ghaziabad, Lucknow |
| 27 | Maharashtra | Mumbai, Pune, Thane |
| 29 | Karnataka | Bangalore, Bengaluru, Mysore |
| 33 | Tamil Nadu | Chennai, Coimbatore |
| 36 | Telangana | Hyderabad, Secunderabad |
| ... | ... | ... |

**All 38 states and major city aliases are supported.**

---

## 💰 GST Tax Calculation Rules

### If POS (Place of Supply) = Seller's State:
- **CGST**: 1.5% (on taxable value)
- **SGST**: 1.5% (on taxable value)
- **IGST**: 0%
- **Supply Type**: INTRA

### If POS ≠ Seller's State:
- **IGST**: 3% (on taxable value)
- **CGST**: 0%
- **SGST**: 0%
- **Supply Type**: INTER

### Return/Refund Handling:
- Negative taxable values are handled automatically
- Negative tax amounts are calculated correctly
- Returns are tracked in "Credit Note" section

---

## 🔧 Configuration

Configuration file: `config.json`

### Default Settings
```json
{
  "app": {
    "name": "GST JSON Generator Pro",
    "version": "2.0.0",
    "debug": false
  },
  "parser": {
    "encoding_fallback": true,
    "encodings": ["utf-8", "latin1", "iso-8859-1"]
  },
  "gst": {
    "default_tax_rate": 3.0,
    "version": "GST3.1.6"
  },
  "output": {
    "formats": ["json", "csv", "xlsx"],
    "output_dir": "./output"
  }
}
```

---

## 📝 Logs

Application logs are stored in `logs/app.log`:
- Automatic log rotation (10MB per file, 5 backup files)
- Timestamp, level, and message for each operation
- Full exception traces for debugging

---

## ✅ Validation Rules

The application enforces comprehensive validation:

### GSTIN
- Format: `DDXXXXXXXXXXXXXXXXX` (15 characters)
- First 2 digits: State code (01-38)
- Alphanumeric characters required

### Filing Period
- Format: `MMYYYY` (6 digits)
- MM: 01-12
- YYYY: 2000-2099

### Files
- Extension: `.xlsx`, `.xls`, `.csv`
- Max size: 500MB per file
- Encoding: Auto-detected (UTF-8, Latin-1, ISO-8859-1)
- Required columns: Detected automatically from each parser

---

## 🐛 Troubleshooting

### "File not found"
- Check that the file path is correct
- Ensure the file hasn't been moved or deleted
- Try adding the file again

### "Missing required columns"
- Verify the file format matches expected structure
- Check that headers are in the first row
- Try using the correct parser for your file type

### "Invalid GSTIN"
- GSTIN must be 15 characters
- First 2 digits must be a valid state code (01-38)
- Use uppercase letters only

### "Invalid filing period"
- Period must be in MMYYYY format
- Month must be 01-12
- Year must be 2000-2099

### Application won't start
- Verify Python 3.10+ is installed: `python3 --version`
- Reinstall dependencies: `pip install -r requirements.txt`
- Check the logs: `logs/app.log`

---

## 📚 Technical Details

### Architecture
- **Frontend**: PySide6 (Qt6-based GUI)
- **Data Processing**: pandas + openpyxl
- **Logging**: Python logging with file rotation
- **Configuration**: JSON-based settings

### Parser Classes
- `BaseParser`: Abstract base with common logic
- `MeeshoParser`: Handles Meesho-specific formats
- `AmazonParser`: Handles Amazon/MTR CSV formats
- `AutoMergeParser`: Auto-detects and merges multiple sources

### Core Modules
- `main.py`: Application entry point
- `ui.py`: PySide6 GUI implementation
- `parsers.py`: File parsing logic
- `gst_builder.py`: JSON generation and validation
- `config.py`: Configuration management
- `logger.py`: Logging system
- `validators.py`: Input validation

---

## 🔐 Error Handling

The application includes:
- ✓ File encoding fallback (UTF-8 → Latin-1)
- ✓ Duplicate row detection and removal
- ✓ Zero/negligible value filtering
- ✓ Missing column detection
- ✓ Invalid data type handling
- ✓ Comprehensive exception tracking
- ✓ User-friendly error messages

---

## 📈 Performance

Typical performance metrics:
- **Small files** (< 10 MB): ~2-3 seconds
- **Medium files** (10-100 MB): ~5-10 seconds
- **Large files** (100-500 MB): ~20-60 seconds
- **Memory usage**: ~500MB - 1GB depending on file size

---

## 🤝 Support & Contributing

For issues, questions, or contributions:
1. Check the logs: `logs/app.log`
2. Review the troubleshooting section above
3. Ensure all dependencies are installed correctly
4. Test with a sample file first

---

## 📄 License

GST JSON Generator Pro v2.0
Production-Grade Application

---

## 🎓 Additional Resources

### GST Knowledge
- [GST Council Official](https://gst.gov.in/)
- [GSTR-1 Filing Guide](https://www.gst.gov.in/)
- [Tax Calculation](https://www.cleartax.in/)

### Development
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [pandas Documentation](https://pandas.pydata.org/)
- [Python Logging](https://docs.python.org/3/library/logging.html)

---

## 💡 Tips & Best Practices

1. **Always backup your data** before processing
2. **Test with a small file first** before processing large batches
3. **Verify GSTIN carefully** - wrong state code affects tax calculation
4. **Review JSON output** before uploading to GST portal
5. **Keep logs** for audit trail and troubleshooting
6. **Update regularly** for bug fixes and improvements

---

**Version**: 2.0.0  
**Last Updated**: April 2024  
**Status**: Production-Ready ✓
