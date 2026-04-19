#!/bin/bash
# run.sh - GST JSON Generator Pro Launcher
# Cross-platform startup script for Linux/macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════"
echo "GST JSON Generator Pro v2.0"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "   Please install Python 3.7+ from https://www.python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✓ Found: $PYTHON_VERSION"
echo ""

# Check/Create venv
if [ ! -d "venv" ]; then
    echo "⏳ Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate venv
echo "⏳ Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install/Upgrade packages
echo "⏳ Installing dependencies..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create directories
mkdir -p logs output test_output

# Run application
echo "⏳ Starting application..."
echo ""
python3 main.py

# Deactivate venv on exit
deactivate 2>/dev/null || true
echo ""
echo "Application closed"
