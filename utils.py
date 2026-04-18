# utils.py
# FINAL STABLE UTILITIES

import json
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


# =====================================================
# LOGGING
# =====================================================
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                log_file,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8"
            )
        ]
    )


# =====================================================
# SAVE JSON
# =====================================================
def save_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =====================================================
# SAFE FLOAT
# =====================================================
def safe_float(v):
    try:
        if v is None or v == "":
            return 0.0
        return float(v)
    except:
        return 0.0