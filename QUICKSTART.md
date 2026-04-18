# GST JSON Generator Pro - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Install Dependencies
```bash
cd /path/to/GST-Tool
pip install -r requirements.txt
```

### 2. Configure (Optional)
Edit `config.json` if you need custom settings:
```json
{
  "output": {
    "output_dir": "./output"
  },
  "gst": {
    "default_tax_rate": 3.0
  }
}
```

### 3. Run Application
```bash
python3 main.py
```

### 4. Use the UI
- Add Excel/CSV files
- Select parsing mode (Auto Merge, Meesho, Flipkart, Amazon)
- Enter GSTIN and Period (MMYYYY)
- Select export formats (JSON, CSV, Excel)
- Click "GENERATE GST JSON"

## 📊 Export Formats

### JSON (Default)
- Full structured output
- Complete data preservation
- Ready for integration

### CSV (New!)
- Tabular format
- Easy to view in spreadsheets
- Suitable for reports

### Excel XLSX (New!)
- Formatted spreadsheets
- Professional appearance
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
