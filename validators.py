# validators.py
# LONG TERM V1

import re
from pathlib import Path


def run_full_validation(gstin, period, files):
    errors = []

    gstin = str(gstin).strip().upper()
    period = str(period).strip()

    if not re.fullmatch(r"[0-9]{2}[A-Z0-9]{13}", gstin):
        errors.append("Invalid GSTIN")

    if not re.fullmatch(r"(0[1-9]|1[0-2])[0-9]{4}", period):
        errors.append("Invalid Return Period (MMYYYY)")

    if not files:
        errors.append("Please select files")
    else:
        allowed = {".xlsx", ".xls", ".csv"}
        for f in files:
            if Path(f).suffix.lower() not in allowed:
                errors.append(f"Unsupported file: {Path(f).name}")

    return (len(errors) == 0), errors