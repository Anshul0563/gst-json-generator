# GST JSON Generator Pro v2.0 - SETUP GUIDE

## Complete Installation & Setup Instructions

### System Requirements
- **OS**: Windows, macOS, or Linux
- **Python**: 3.10 or higher
- **RAM**: Minimum 2GB (4GB recommended)
- **Disk Space**: ~1GB for dependencies + data

---

## 🔧 Installation Steps

### 1. Install Python 3.10+

**Windows:**
- Download from https://www.python.org/downloads/
- Run installer and **IMPORTANT**: Check "Add Python to PATH"
- Verify: `python --version`

**macOS:**
```bash
brew install python@3.10
# or use https://www.python.org/downloads/
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3.10 python3.10-venv python3-pip
```

**Linux (Fedora/CentOS):**
```bash
sudo dnf install python3.10
```

### 2. Clone or Download the Repository

```bash
# Option 1: Clone repository
git clone <repository-url>
cd GST-Tool

# Option 2: Download ZIP
# Extract the ZIP file and open the directory
```

### 3. Create Virtual Environment

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Upgrade pip

```bash
# Windows
python -m pip install --upgrade pip

# macOS/Linux
python3 -m pip install --upgrade pip
```

### 5. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Or install individually:
pip install PySide6>=6.5.0
pip install pandas>=2.0.0
pip install openpyxl>=3.10.0
pip install xlrd>=2.0.1
pip install numpy>=1.24.0
pip install python-dotenv>=1.0.0
pip install requests>=2.31.0
pip install pytz>=2023.3
```

### 6. Verify Installation

```bash
# Test all imports
python -c "import PySide6, pandas, openpyxl; print('✓ All dependencies installed')"

# Or run syntax check
python -m py_compile main.py parsers.py gst_builder.py ui.py config.py logger.py validators.py
```

---

## 🚀 Running the Application

### Option 1: Using Startup Script

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
- Double-click `run.bat`
- Or in Command Prompt: `run.bat`

### Option 2: Manual Launch

**Windows:**
```cmd
venv\Scripts\activate
python main.py
```

**macOS/Linux:**
```bash
source venv/bin/activate
python3 main.py
```

### Option 3: Using IDE

1. Open project in VS Code / PyCharm
2. Select Python interpreter from `venv`
3. Run `main.py`

---

## ✅ Troubleshooting Installation

### "Python not found" or "python: command not found"
**Solution:**
- Install Python 3.10+ from python.org
- On Linux: `sudo apt-get install python3.10`
- On macOS: `brew install python@3.10`
- Verify: `python3 --version`

### "pip: command not found"
**Solution:**
```bash
# Install pip
python -m ensurepip --upgrade
# or
python3 -m ensurepip --upgrade
```

### "ModuleNotFoundError: No module named 'PySide6'"
**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Reinstall PySide6
pip install --upgrade PySide6
```

### "No module named 'pandas'"
**Solution:**
```bash
pip install pandas
```

### Virtual environment activation fails
**Solution:**
```bash
# Delete old venv and recreate
rm -rf venv  # macOS/Linux: rm -rf venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
```

### Application won't start (black window appears and closes)
**Solution:**
1. Run from terminal to see error messages
2. Check `logs/app.log` for detailed error
3. Verify all dependencies: `pip install -r requirements.txt`

---

## 📦 Dependency Details

| Package | Version | Purpose |
|---------|---------|---------|
| PySide6 | ≥6.5.0 | GUI Framework |
| pandas | ≥2.0.0 | Data processing |
| openpyxl | ≥3.10.0 | Excel file handling |
| xlrd | ≥2.0.1 | Legacy Excel support |
| numpy | ≥1.24.0 | Numerical operations |
| python-dotenv | ≥1.0.0 | Environment configuration |
| requests | ≥2.31.0 | HTTP requests |
| pytz | ≥2023.3 | Timezone handling |

---

## 🔍 Verification Checklist

After installation, verify:

- [ ] Python 3.10+ installed: `python --version`
- [ ] Virtual environment created: `ls venv` or `dir venv`
- [ ] Virtual environment activated: `(venv)` in terminal
- [ ] Dependencies installed: `pip list | grep -i pyside6`
- [ ] Syntax check passed: `python -m py_compile main.py`
- [ ] Application starts: `python main.py`

---

## 🎓 First Time Usage

1. **Create a directory for your data**
   - Create a folder like `~/GST-Tool/data`
   - Place your Meesho/Amazon CSV files there

2. **Launch the application**
   - Run `python main.py` or `./run.sh`
   - Wait for the GUI to load

3. **Test with sample data**
   - Add a small test file first
   - Generate JSON to verify it works
   - Check the output in `./output` folder

4. **Configure for production**
   - Edit `config.json` if needed
   - Update `output.output_dir` to your preferred location

---

## 🛠️ Advanced Configuration

Edit `config.json` to customize:

```json
{
  "app": {
    "name": "GST JSON Generator Pro",
    "version": "2.0.0",
    "debug": false
  },
  "parser": {
    "encoding_fallback": true,
    "max_rows": 100000
  },
  "output": {
    "output_dir": "./output",
    "formats": ["json"]
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log"
  }
}
```

---

## 📝 Creating Log Directories

The application will auto-create directories, but you can pre-create them:

```bash
# Create logs directory
mkdir -p logs

# Create output directory
mkdir -p output

# Or on Windows:
md logs
md output
```

---

## 🔐 Security Considerations

1. **Keep dependencies updated:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Run in isolated environment:**
   - Always use virtual environment
   - Don't run with admin/sudo unless necessary

3. **Backup your data:**
   - Keep original files backed up
   - Store generated JSON files securely

4. **Check logs for errors:**
   - Review `logs/app.log` regularly
   - Report any security concerns

---

## 🆘 Support Resources

1. **Check logs**: `logs/app.log`
2. **Read README**: `README_COMPLETE.md`
3. **Review code comments** in source files
4. **Test with sample files** first

---

## ✨ Ready to Use!

Once installation is complete and verified:

1. Place your data files in a folder
2. Run: `python main.py`
3. Follow the 5-step GUI wizard
4. Generate your GSTR-1 JSON
5. Export and upload

**That's it! You're ready to generate production-grade GSTR-1 JSONs.**

---

## 🔄 Updating the Application

To get the latest version:

```bash
# Pull latest changes
git pull origin main

# Reinstall dependencies (in case of updates)
pip install --upgrade -r requirements.txt

# Run application
python main.py
```

---

**Last Updated**: April 2024  
**Status**: Production-Ready ✓  
**Support**: Check logs/README for detailed help
