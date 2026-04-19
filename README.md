# GST JSON Generator Pro v2.0 🚀

**Professional GST-compliant GSTR-1 JSON generator for e-commerce sellers**

Generate GST Portal compatible JSON files directly from Meesho, Flipkart, and Amazon marketplace reports with automatic tax calculations, validation, and reconciliation.

---

## 📋 Quick Links

- 🚀 [Quick Start](#quick-start) - Get running in 2 minutes
- 📖 [Usage Guide](#usage) - Step-by-step instructions
- 📦 [Supported Formats](#file-formats) - What file types work
- ⚙️ [Configuration](#configuration) - Customize settings
- 🔧 [Troubleshooting](#troubleshooting) - Common issues & fixes
- 📁 [Project Structure](#project-structure) - How it's organized

---

## ✨ Features

### Core Functionality
- ✅ **Multi-Platform**: Meesho, Flipkart, Amazon
- ✅ **GST 3.1.6 Compliant**: GST Portal ready JSON
- ✅ **Auto Tax Calculation**: IGST/CGST/SGST based on POS
- ✅ **Smart Detection**: Auto-detects file structure
- ✅ **Multi-Export**: JSON, CSV, Excel formats
- ✅ **Real-time Dashboard**: Totals verification

### Data Processing
- ✅ **Multi-Sheet Excel**: Automatic merging
- ✅ **Encoding Support**: UTF-8, Latin1, ISO-8859-1
- ✅ **Deduplication**: Intelligent duplicate removal
- ✅ **Return Handling**: Credit note processing
- ✅ **State Mapping**: All 38 Indian states
- ✅ **Invoice Series**: Automatic range generation

### Quality
- ✅ **Advanced Validation**: Input verification
- ✅ **Logging System**: Detailed operation logs
- ✅ **Error Recovery**: Graceful handling
- ✅ **Caching**: Performance optimization
- ✅ **Configuration**: Flexible settings

---

## 🚀 Quick Start

### Linux/macOS:
```bash
git clone https://github.com/Anshul0563/gst-json-generator-pro.git
cd gst-json-generator-pro
chmod +x run.sh
./run.sh
```

### Windows:
```bash
git clone https://github.com/Anshul0563/gst-json-generator-pro.git
cd gst-json-generator-pro
run.bat
```

The script automatically creates venv, installs dependencies, and launches the app.

---

## ⚙️ Manual Installation

### Requirements
- Python 3.7+
- pip
- 200MB disk space

### Steps
```bash
# 1. Clone and enter directory
git clone https://github.com/Anshul0563/gst-json-generator-pro.git
cd gst-json-generator-pro

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run application
python3 main.py
```

---

## 📖 Usage

### Workflow
1. **Launch**: Run `./run.sh` or `python3 main.py`
2. **Enter Details**:
   - GSTIN: Your 15-digit registration (e.g., 07AARCM9332R1CQ)
   - Period: MMYYYY format (e.g., 042024 for April 2024)
   - Mode: Select parser (Auto Merge recommended for multi-platform)
3. **Add Files**: Select marketplace reports
4. **Select Export**: Choose output format (JSON recommended)
5. **Generate**: Click button and wait for completion
6. **Verify**: Check reconciliation dashboard
7. **Upload**: Download JSON and upload to GST Portal

---

## 📦 Supported Formats

### Input Files
| Platform | File Type | Format | Status |
|----------|-----------|--------|--------|
| Meesho | Sales Report | XLSX | ✅ Full |
| Meesho | Returns | XLSX/CSV | ✅ Full |
| Flipkart | Sales Report | XLSX | ✅ Full |
| Flipkart | Cash Back (Returns) | XLSX | ✅ Full |
| Amazon | Monthly Report | CSV | ✅ Full |
| Amazon | Refunds | CSV | ✅ Auto |

### Output Formats
- **JSON**: GSTR-1 compliant for GST Portal
- **CSV**: Summary for spreadsheet applications
- **Excel**: Formatted with headers and totals

---

## ⚙️ Configuration

### Via config.json
```json
{
  "gst": {
    "default_tax_rate": 3.0,
    "cgst_rate": 1.5,
    "sgst_rate": 1.5
  },
  "output": {
    "formats": ["json", "csv", "xlsx"],
    "output_dir": "./output"
  }
}
```

### Via Environment Variables
Create `.env`:
```bash
LOG_LEVEL=INFO
OUTPUT_DIR=./output
DEFAULT_TAX_RATE=3.0
```

---

## 🔧 Troubleshooting

### Python not found
```bash
# Install Python 3: https://www.python.org
python3 --version  # Verify installation
```

### Module errors
```bash
# Reactivate venv and reinstall
source venv/bin/activate
pip install -r requirements.txt
```

### File not recognized
- Verify column names (Invoice, State, Taxable Value)
- Check encoding (UTF-8 recommended)
- Ensure platform selection matches file source

### GSTIN format error
- Format: AABBCCCCCCCCCCN (15 digits)
- First 2 digits: State code (01-38)
- Example: 07AARCM9332R1CQ

---

## 📁 Project Structure

```
gst-json-generator-pro/
├── main.py              # Entry point
├── ui.py                # GUI interface
├── parsers.py           # Platform parsers
├── gst_builder.py       # JSON builder
├── validators.py        # Input validation
├── exporter.py          # Export formats
├── config.py            # Configuration
├── logger.py            # Logging
├── cache.py             # Caching
├── utils.py             # Utilities
├── requirements.txt     # Dependencies
├── run.sh / run.bat     # Launchers
├── README.md            # This file
├── DEBUG_REPORT.md      # Technical details
├── logs/                # App logs
├── output/              # Generated files
└── test_data/           # Sample files
```

---

## 🧪 Testing

```bash
source venv/bin/activate
python3 integration_test.py
python3 test_validation.py
```

---

## 🏗️ Architecture

- **Strategy Pattern**: Parsers
- **Builder Pattern**: JSON creation
- **Singleton Pattern**: Config/Logger/Cache
- **Adapter Pattern**: Templates
- **Factory Pattern**: File readers

---

## 🔐 Security

- ✅ Works offline (no cloud upload)
- ✅ Files processed locally only
- ✅ No telemetry or tracking
- ✅ Open source (full transparency)
- ✅ Complete audit logs

---

## 📞 Support

- **Issues**: GitHub Issues
- **Email**: anshul@example.com
- **Docs**: See DEBUG_REPORT.md

---

## 📄 License

MIT License - Free and open source

---

## ✅ Pre-Upload Checklist

- [ ] GSTIN matches seller registration
- [ ] Period is MMYYYY format
- [ ] Total taxable matches your records
- [ ] Tax calculations verified
- [ ] No negative non-return items
- [ ] All states included
- [ ] Invoice series continuous
- [ ] Returns properly deducted

---

**Made with ❤️ for Indian e-commerce sellers**

Version: 2.0.0 | Last Updated: April 19, 2026
