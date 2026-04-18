# validators.py
# FINAL VALIDATION FILE

import re
from pathlib import Path
from typing import Dict, List, Tuple, Any


class GSTValidator:

    # =====================================================
    # GSTIN
    # =====================================================
    @staticmethod
    def validate_gstin(gstin: str) -> Tuple[bool, str]:
        if not gstin:
            return False, "GSTIN required"

        gstin = gstin.strip().upper()

        pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"

        if not re.match(pattern, gstin):
            return False, "Invalid GSTIN format"

        return True, "Valid GSTIN"

    # =====================================================
    # PERIOD
    # =====================================================
    @staticmethod
    def validate_period(period: str) -> Tuple[bool, str]:
        if not period:
            return False, "Return period required"

        if len(period) != 6 or not period.isdigit():
            return False, "Use MMYYYY format"

        month = int(period[:2])
        year = int(period[2:])

        if month < 1 or month > 12:
            return False, "Invalid month"

        if year < 2020 or year > 2100:
            return False, "Invalid year"

        return True, "Valid period"

    # =====================================================
    # FILES
    # =====================================================
    @staticmethod
    def validate_files(files: List[str]) -> Tuple[bool, List[str]]:
        errors = []
        valid = []

        if not files:
            return False, ["No files selected"]

        for f in files:
            p = Path(f)

            if not p.exists():
                errors.append(f"Missing file: {p.name}")
                continue

            if p.suffix.lower() not in [".xlsx", ".xls", ".csv"]:
                errors.append(f"Unsupported file: {p.name}")
                continue

            valid.append(str(p))

        if not valid:
            return False, errors

        return True, errors

    # =====================================================
    # PARSED DATA
    # =====================================================
    @staticmethod
    def validate_parsed_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        if not isinstance(data, dict):
            return False, ["Parsed data invalid"]

        required = ["platform", "summary"]

        for k in required:
            if k not in data:
                errors.append(f"Missing key: {k}")

        summary = data.get("summary", {})

        if "rows" not in summary:
            errors.append("Missing summary rows")

        if summary.get("total_taxable", 0) < 0:
            errors.append("Negative taxable value")

        return len(errors) == 0, errors

    # =====================================================
    # FINAL JSON
    # =====================================================
    @staticmethod
    def validate_json(json_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        required = [
            "gstin",
            "fp",
            "version",
            "hash",
            "gt",
            "cur_gt",
            "b2cs",
            "supeco",
            "doc_issue"
        ]

        for k in required:
            if k not in json_data:
                errors.append(f"Missing JSON field: {k}")

        # GSTIN check
        ok, msg = GSTValidator.validate_gstin(json_data.get("gstin", ""))
        if not ok:
            errors.append(msg)

        # Period check
        ok, msg = GSTValidator.validate_period(json_data.get("fp", ""))
        if not ok:
            errors.append(msg)

        # Totals
        if json_data.get("gt", 0) < 0:
            errors.append("Grand total invalid")

        if not isinstance(json_data.get("b2cs", []), list):
            errors.append("b2cs must be list")

        return len(errors) == 0, errors


# =====================================================
# COMPLETE PIPELINE
# =====================================================
def run_full_validation(
    gstin: str,
    period: str,
    files: List[str],
    parsed_data: Dict[str, Any] = None,
    json_data: Dict[str, Any] = None
):
    errors = []

    # GSTIN
    ok, msg = GSTValidator.validate_gstin(gstin)
    if not ok:
        errors.append(msg)

    # PERIOD
    ok, msg = GSTValidator.validate_period(period)
    if not ok:
        errors.append(msg)

    # FILES
    ok, file_errors = GSTValidator.validate_files(files)
    errors.extend(file_errors)

    # PARSED
    if parsed_data:
        ok, e = GSTValidator.validate_parsed_data(parsed_data)
        errors.extend(e)

    # JSON
    if json_data:
        ok, e = GSTValidator.validate_json(json_data)
        errors.extend(e)

    return len(errors) == 0, errors