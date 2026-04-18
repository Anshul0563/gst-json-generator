
import re


def validate_gstin(gstin):
    gstin = gstin.strip().upper()

    pattern = r"^[0-9]{2}[A-Z0-9]{13}$"

    if not re.match(pattern, gstin):
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

    return files