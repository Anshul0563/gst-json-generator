# validators.py
# FULL FIXED VERSION

import re
from pathlib import Path


def validate_gstin(gstin):
    gstin = gstin.strip().upper()

    if not re.match(r"^[0-9]{2}[A-Z0-9]{13}$", gstin):
        raise ValueError("Invalid GSTIN")

    return gstin


def validate_period(period):
    period = period.strip()

    if not re.match(r"^(0[1-9]|1[0-2])[0-9]{4}$", period):
        raise ValueError("Use MMYYYY format")

    return period


def validate_files(files):
    if not files:
        raise ValueError("Please select files")

    valid_ext = {".xlsx", ".xls", ".csv"}

    for f in files:
        ext = Path(f).suffix.lower()
        if ext not in valid_ext:
            raise ValueError(f"Unsupported file: {Path(f).name}")

    return files


def run_full_validation(gstin, period, files):
    gstin = validate_gstin(gstin)
    period = validate_period(period)
    files = validate_files(files)

    return gstin, period, files