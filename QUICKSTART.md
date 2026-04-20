# GST JSON Generator Pro v2.0 - QUICK START REFERENCE

## ⚡ 5-Minute Quick Start

### Prerequisites
- Python 3.10+ installed
- ~1GB disk space
- Your Meesho/Amazon data files

### Installation (3 steps)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create output directories:**
   ```bash
   mkdir -p logs output
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

---

## 🎯 Usage Workflow

```
1. SELECT PARSER
   ↓ Choose: Auto Merge, Meesho, or Amazon
   ↓
2. ENTER GSTIN
   ↓ E.g., 07TCRPS8655B1ZK (first 2 digits = state code)
   ↓
3. ENTER PERIOD
   ↓ E.g., 042024 (April 2024, MMYYYY format)
   ↓
4. ADD FILES
   ↓ Select CSV or Excel files with your data
   ↓
5. GENERATE & EXPORT
   ↓ Click "GENERATE GST JSON"
   ↓ Click "Export to File"
   ↓
OUTPUT: Valid GSTR-1 JSON in ./output/
```

---

## 📋 Supported File Formats

### Meesho Files
- `tcs_sales.xlsx`
- `tcs_sales_return.xlsx`
- `tax_invoice_details.xlsx`
- Any file with: `sub_order_num`, `end_customer_state_new`, `total_taxable_sale_value`

### Amazon Files
- `*_settlement_*.csv`
- `*_mtr*.csv`
- Any CSV with: `invoice_number`, `ship_to_state`, `tax_exclusive_gross`, `igst_tax`, `cgst_tax`, `sgst_tax`

---

## 💡 Input Validation Rules

| Field | Format | Example | Valid |
|-------|--------|---------|-------|
| GSTIN | 15 chars, 2-digit state code | 07TCRPS8655B1ZK | ✓ |
| Period | MMYYYY | 042024 | ✓ |
| Files | .xlsx, .xls, .csv | data.csv | ✓ |
| File Size | Max 500MB | 50MB | ✓ |

---

## 💰 Tax Calculation

### Same State (Intra-State)
```
If POS = Seller's State:
  CGST = 1.5% 
  SGST = 1.5%
  IGST = 0%
```

### Different State (Inter-State)
```
If POS ≠ Seller's State:
  IGST = 3%
  CGST = 0%
  SGST = 0%
```

---

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "File not found" | Wrong file path | Check file exists |
| "Invalid GSTIN" | Wrong format | Use 15-char format: 07XXXXX |
| "Invalid period" | Wrong format | Use MMYYYY: 042024 |
| App won't start | Missing dependency | Run: `pip install -r requirements.txt` |

---

## 📊 Sample Output

```json
{
  "gstin": "07TCRPS8655B1ZK",
  "fp": "042024",
  "version": "GST3.1.6",
  "b2cs": [
    {
      "sply_ty": "INTRA",
      "rt": 3.0,
      "typ": "OE",
      "pos": "07",
      "txval": 1000.00,
      "camt": 15.00,
      "samt": 15.00
    }
  ],
  "summary": {
    "total_items": 1,
    "total_taxable": 1000.00,
    "total_tax": 30.00
  }
}
```

---

## 🔍 Log File Location

```
logs/app.log
```

---

## ✅ Production Checklist

- [ ] Python 3.10+ installed
- [ ] Dependencies installed
- [ ] config.json exists
- [ ] logs/ directory exists
- [ ] output/ directory exists
- [ ] Test file processed
- [ ] Output JSON validated

---

## 📞 Support Resources

| Topic | File |
|-------|------|
| Full Documentation | README_COMPLETE.md |
| Installation | SETUP_COMPLETE.md |
| Source Code | parsers.py, gst_builder.py, ui.py |

---

**Version**: 2.0.0  
**Status**: Production-Ready ✓
3. Download CSV

### Organize Files
```
gst-json-generator-pro/
├── meesho_sales.xlsx
├── flipkart_sales.xlsx
└── amazon_sales.csv
```

---

## 3️⃣ Run Generator

### In Application

1. **Enter Your GSTIN**
   ```
   07AARCM9332R1CQ
   ```
   (15-digit GST number)

2. **Enter Period**
   ```
   042024
   ```
   (MMYYYY format: April 2024)

3. **Select Mode**
   ```
   Auto Merge
   ```
   (For multiple platforms)

4. **Add Files**
   - Click "Add Files"
   - Select your downloaded reports

5. **Choose Export**
   - ☑️ JSON (recommended)
   - ☐ CSV
   - ☐ Excel

6. **Generate**
   - Click "GENERATE GST JSON"
   - Wait for completion
   - Check reconciliation dashboard

---

## 4️⃣ Verify Output

### Reconciliation Dashboard Shows:
- ✅ Total Taxable: ₹50,000.00
- ✅ Total Tax: ₹1,500.00
- ✅ Returns: ₹500.00
- ✅ State-wise breakdown

### Files Generated (in `output/` folder):
```
GSTR1_042024_20260419_153045.json
GSTR1_042024_20260419_153045.csv
GSTR1_042024_20260419_153045.xlsx
```

---

## 5️⃣ Upload to GST Portal

1. Go to https://gstr.gov.in
2. Log in with DSC
3. GSTR-1 → Prepare Offline
4. Upload generated JSON file
5. Validate and submit

---

## ✅ Checklist Before Upload

- [ ] GSTIN matches seller registration
- [ ] Period is correct (MMYYYY)
- [ ] Total taxable matches your records
- [ ] Tax calculations verified
- [ ] No zero amounts
- [ ] Returns properly deducted
- [ ] Invoice numbers are correct

---

## 🆘 Troubleshooting

### "Python not found"
```bash
# Install Python 3 from https://www.python.org
python3 --version  # Check version (should be 3.7+)
```

### "File not recognized"
- Check file format (Excel or CSV)
- Verify columns: Invoice, State, Taxable Value
- Try saving with UTF-8 encoding

### "GSTIN invalid"
- Must be 15 digits
- Format: AABBCCCCCCCCCCN
- Example: 07AARCM9332R1CQ (Delhi seller)

### App won't start
```bash
# Reinstall everything
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

---

## 📊 Sample Data

Test files are in `test_data/`:

```bash
# Quick test
cd gst-json-generator-pro
source venv/bin/activate
python3 main.py

# In app:
# GSTIN: 07AARCM9332R1CQ
# Period: 042024
# Mode: Auto Merge
# Add: test_data/meesho_sales.csv, test_data/flipkart_sales.csv
# Generate
```

Expected output:
- Total Taxable: ₹31,000.00
- Total IGST: ₹870.00

---

## 💡 Tips

1. **Auto Merge** works best for multiple platforms
2. **Use JSON** format for GST Portal upload
3. **Always verify** totals before uploading
4. **Keep backups** of generated JSON files
5. **Check logs** if something goes wrong (in `logs/` folder)

---

## 📞 Need Help?

- Check [README.md](README.md) for detailed documentation
- See [DEBUG_REPORT.md](DEBUG_REPORT.md) for technical details
- Visit [DEPLOYMENT.md](DEPLOYMENT.md) for server setup

---

**Ready? Let's generate your GST JSON! 🚀**

Last Updated: April 19, 2026
- Easy to share

## 🎯 Common Tasks

### Task 1: Generate Single Format
```
1. Add files
2. Check only "JSON" format
3. Click Generate
```

### Task 2: Export in All Formats
```
1. Add files
2. Check all formats: JSON, CSV, Excel
3. Click Generate
4. Files saved to ./output/ folder
```

### Task 3: Custom Configuration
```
1. Edit config.json
2. Customize settings (output dir, tax rates, etc.)
3. Run: python3 main.py
```

## 📁 File Organization

```
Output Files:
./output/
├── GSTR1_AutoMerge_122023.json      # JSON format
├── GSTR1_AutoMerge_122023.csv       # CSV format
└── GSTR1_AutoMerge_122023.xlsx      # Excel format
```

## 🔍 Checking Logs

```bash
# View application logs
tail -f logs/app.log

# View recent errors
grep ERROR logs/app.log

# View performance metrics
grep PERF logs/app.log
```

## ✅ Verification

### Run Tests
```bash
python3 integration_test.py
```

Expected: `✅ All integration tests passed!`

### Check Configuration
```bash
python3 -c "from config import get_config; print(get_config().to_dict())"
```

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module" error | Run `pip install -r requirements.txt` |
| Logs not found | Create: `mkdir -p logs` |
| Export not working | Check config.json `output_dir` path |
| Cache issues | Clear cache: `config.get_cache().clear()` |

## 🎓 Advanced Usage

### Programmatic Use
```python
from main import create_parsers
from gst_builder import GSTBuilder
from exporter import Exporter

# Initialize
parsers = create_parsers()
builder = GSTBuilder()

# Parse
parsed = parsers["Auto Merge"].parse_files(["file.xlsx"])

# Build
output = builder.build_gstr1(parsed, "27AAPCT1234A1Z5", "122023")

# Export
exporter = Exporter('./output')
results = exporter.export(output, 'report', ['json', 'csv', 'xlsx'])
print(f"Exported: {list(results.keys())}")
```

### Custom Configuration
```python
from config import init_config

# Load custom config
config = init_config('custom_config.json')

# Use custom settings
output_dir = config.get('output.output_dir')
tax_rate = config.get('gst.default_tax_rate')
```

### Performance Tracking
```python
from logger import get_logger
import time

logger = get_logger()

start = time.time()
# Do work...
duration = time.time() - start

logger.perf("operation_name", duration, record_count=1000)
# Output: PERF: operation_name completed in 1.23s (1000 records)
```

## 📊 Performance Tips

1. **Use Caching**: Repeated file processing is 10x faster
2. **Multi-format Export**: Export all formats at once (faster than separately)
3. **Batch Processing**: Process multiple files together
4. **Monitor Logs**: Check `logs/app.log` for performance metrics

## 🔐 Best Practices

1. ✅ Keep config.json in version control
2. ✅ Review logs regularly
3. ✅ Test with sample data first
4. ✅ Validate GSTIN format
5. ✅ Use proper period format (MMYYYY)
6. ✅ Backup output regularly

## 📚 Further Reading

- `ADVANCED_FEATURES.md` - Detailed feature documentation
- `MIGRATION_GUIDE.md` - Migration from v1.0 to v2.0
- `README.md` - Complete documentation
- `integration_test.py` - Working examples

## 🎉 You're All Set!

You now have an enterprise-grade GST JSON Generator with:
- ✅ Multi-format export
- ✅ Advanced caching
- ✅ Professional logging
- ✅ Centralized configuration
- ✅ Design patterns
- ✅ Enhanced validation

Ready to generate GST JSON files efficiently!

---

**Need Help?** Check the logs: `tail -f logs/app.log`
