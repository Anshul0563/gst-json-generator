# utils.py
# FINAL SUPPORT FILE

import re
import json
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Dict, Any


# =====================================================
# LOGGING
# =====================================================
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "gst_generator.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
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
# GSTIN VALIDATION
# =====================================================
def validate_gstin(gstin: str) -> bool:
    """
    GSTIN Format:
    07ABCDE1234F1Z5
    """
    if not gstin:
        return False

    gstin = gstin.strip().upper()

    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
    return bool(re.match(pattern, gstin))


# =====================================================
# PERIOD VALIDATION
# =====================================================
def validate_period(period: str) -> bool:
    """
    MMYYYY
    Example: 032026
    """
    if not period or len(period) != 6 or not period.isdigit():
        return False

    month = int(period[:2])
    year = int(period[2:])

    if month < 1 or month > 12:
        return False

    if year < 2020 or year > 2100:
        return False

    return True


# =====================================================
# SAVE JSON
# =====================================================
def save_json(data: Dict[str, Any], file_path: str) -> bool:
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        logging.error(f"JSON save failed: {e}")
        return False


# =====================================================
# STATE CODE MAP
# =====================================================
def get_state_code_map():
    return {
        "01": "Jammu and Kashmir",
        "02": "Himachal Pradesh",
        "03": "Punjab",
        "04": "Chandigarh",
        "05": "Uttarakhand",
        "06": "Haryana",
        "07": "Delhi",
        "08": "Rajasthan",
        "09": "Uttar Pradesh",
        "10": "Bihar",
        "11": "Sikkim",
        "12": "Arunachal Pradesh",
        "13": "Nagaland",
        "14": "Manipur",
        "15": "Mizoram",
        "16": "Tripura",
        "17": "Meghalaya",
        "18": "Assam",
        "19": "West Bengal",
        "20": "Jharkhand",
        "21": "Odisha",
        "22": "Chhattisgarh",
        "23": "Madhya Pradesh",
        "24": "Gujarat",
        "25": "Daman and Diu",
        "26": "Dadra and Nagar Haveli",
        "27": "Maharashtra",
        "29": "Karnataka",
        "30": "Goa",
        "31": "Lakshadweep",
        "32": "Kerala",
        "33": "Tamil Nadu",
        "34": "Puducherry",
        "35": "Andaman and Nicobar Islands",
        "36": "Telangana",
        "37": "Andhra Pradesh",
        "38": "Ladakh"
    }


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


# =====================================================
# FILE EXISTS
# =====================================================
def file_exists(path: str) -> bool:
    return Path(path).exists()