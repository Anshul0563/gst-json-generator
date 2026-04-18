# validators.py
# FINAL STABLE VALIDATOR

import re
from pathlib import Path


# =====================================================
def validate_gstin(gstin):
    if not gstin:
        return False, "GSTIN required"

    gstin = gstin.strip().upper()

    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"

    if not re.match(pattern, gstin):
        return False, "Invalid GSTIN"

    return True, ""


# =====================================================
def validate_period(period):
    if not period:
        return False, "Return period required"

    if len(period) != 6 or not period.isdigit():
        return False, "Use MMYYYY"

    month = int(period[:2])

    if month < 1 or month > 12:
        return False, "Invalid month"

    return True, ""


# =====================================================
def validate_files(files):
    if not files:
        return False, ["No files selected"]

    errors = []

    for f in files:
        p = Path(f)

        if not p.exists():
            errors.append(f"Missing file: {p.name}")

        if p.suffix.lower() not in [".xlsx", ".xls", ".csv"]:
            errors.append(f"Unsupported file: {p.name}")

    return len(errors) == 0, errors


# =====================================================
def run_full_validation(gstin, period, files):
    errors = []

    ok, msg = validate_gstin(gstin)
    if not ok:
        errors.append(msg)

    ok, msg = validate_period(period)
    if not ok:
        errors.append(msg)

    ok, file_errors = validate_files(files)
    errors.extend(file_errors)

    return len(errors) == 0, errors