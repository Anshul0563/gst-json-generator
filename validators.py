# validators.py
# FINAL UI COMPATIBLE VERSION
# returns exactly: ok, errors

import re
from pathlib import Path


def run_full_validation(gstin, period, files):
    errors = []

    gstin = str(gstin).strip().upper()
    period = str(period).strip()

    # GSTIN
    if not re.fullmatch(r"[0-9]{2}[A-Z0-9]{13}", gstin):
        errors.append("Invalid GSTIN")

    # Period MMYYYY
    if not re.fullmatch(r"(0[1-9]|1[0-2])[0-9]{4}", period):
        errors.append("Invalid Return Period (MMYYYY)")

    # Files
    if not files:
        errors.append("Please select files")
    else:
        valid_ext = {".xlsx", ".xls", ".csv"}

        for f in files:
            if Path(f).suffix.lower() not in valid_ext:
                errors.append(f"Unsupported file: {Path(f).name}")

    return (len(errors) == 0), errors