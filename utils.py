
import json
import logging
import re
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
# VALIDATORS
# =====================================================

def validate_gstin(gstin: str) -> bool:
    if not gstin:
        return False

    gstin = gstin.strip().upper()

    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
    return bool(re.match(pattern, gstin))


def validate_period(period: str) -> bool:
    if not period:
        return False

    period = str(period).strip()

    if not period.isdigit() or len(period) != 6:
        return False

    mm = int(period[:2])
    yyyy = int(period[2:])

    return 1 <= mm <= 12 and 2000 <= yyyy <= 2100


# =====================================================
# SAVE JSON
# =====================================================

def save_json(data: Dict[str, Any], filepath: str) -> bool:
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        logging.exception("Failed to save JSON")
        return False


# =====================================================
# STATE CODE MAP
# =====================================================

def get_state_code_map() -> Dict[str, str]:
    return {
        # Union Territories / States
        "JAMMU AND KASHMIR": "01",
        "HIMACHAL PRADESH": "02",
        "PUNJAB": "03",
        "CHANDIGARH": "04",
        "UTTARAKHAND": "05",
        "HARYANA": "06",
        "DELHI": "07",
        "RAJASTHAN": "08",
        "UTTAR PRADESH": "09",
        "BIHAR": "10",
        "SIKKIM": "11",
        "ARUNACHAL PRADESH": "12",
        "NAGALAND": "13",
        "MANIPUR": "14",
        "MIZORAM": "15",
        "TRIPURA": "16",
        "MEGHALAYA": "17",
        "ASSAM": "18",
        "WEST BENGAL": "19",
        "JHARKHAND": "20",
        "ODISHA": "21",
        "ORISSA": "21",
        "CHHATTISGARH": "22",
        "MADHYA PRADESH": "23",
        "GUJARAT": "24",
        "DAMAN AND DIU": "25",
        "DADRA AND NAGAR HAVELI": "26",
        "MAHARASHTRA": "27",
        "ANDHRA PRADESH (OLD)": "28",
        "KARNATAKA": "29",
        "GOA": "30",
        "LAKSHADWEEP": "31",
        "KERALA": "32",
        "TAMIL NADU": "33",
        "PUDUCHERRY": "34",
        "ANDAMAN AND NICOBAR ISLANDS": "35",
        "TELANGANA": "36",
        "ANDHRA PRADESH": "37",
        "LADAKH": "38",

        # Common Short Codes
        "JK": "01",
        "HP": "02",
        "PB": "03",
        "CH": "04",
        "UK": "05",
        "HR": "06",
        "DL": "07",
        "RJ": "08",
        "UP": "09",
        "BR": "10",
        "SK": "11",
        "AR": "12",
        "NL": "13",
        "MN": "14",
        "MZ": "15",
        "TR": "16",
        "ML": "17",
        "AS": "18",
        "WB": "19",
        "JH": "20",
        "OD": "21",
        "OR": "21",
        "CG": "22",
        "MP": "23",
        "GJ": "24",
        "DNHDD": "26",
        "MH": "27",
        "KA": "29",
        "GA": "30",
        "KL": "32",
        "TN": "33",
        "PY": "34",
        "AN": "35",
        "TG": "36",
        "TS": "36",
        "AP": "37",
        "LD": "38",
    }