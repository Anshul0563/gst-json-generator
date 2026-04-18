
from typing import Dict, Any, List, Tuple
from utils import validate_gstin, validate_period


class GSTValidator:

    # =====================================================
    # INPUT VALIDATION
    # =====================================================

    @staticmethod
    def validate_inputs(
        gstin: str,
        period: str,
        files: List[str]
    ) -> Tuple[bool, List[str]]:

        errors = []

        if not validate_gstin(gstin):
            errors.append("Invalid GSTIN")

        if not validate_period(period):
            errors.append("Invalid Period (MMYYYY)")

        if not files:
            errors.append("No files selected")

        return len(errors) == 0, errors

    # =====================================================
    # PARSED DATA VALIDATION
    # =====================================================

    @staticmethod
    def validate_parsed_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        if not isinstance(data, dict):
            return False, ["Parsed data must be dictionary"]

        if "platform" not in data:
            errors.append("Missing platform")

        if "net" not in data:
            errors.append("Missing net section")
            return False, errors

        net = data["net"]

        required = [
            "state_summary",
            "total_taxable",
            "total_igst",
            "total_cgst",
            "total_sgst"
        ]

        for key in required:
            if key not in net:
                errors.append(f"Missing net.{key}")

        return len(errors) == 0, errors

    # =====================================================
    # JSON VALIDATION
    # =====================================================

    @staticmethod
    def validate_json(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
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

        for key in required:
            if key not in data:
                errors.append(f"Missing {key}")

        # b2cs row check
        for i, row in enumerate(data.get("b2cs", [])):
            row_req = [
                "sply_ty",
                "rt",
                "typ",
                "pos",
                "txval",
                "iamt",
                "camt",
                "samt",
                "csamt"
            ]
            for k in row_req:
                if k not in row:
                    errors.append(f"b2cs[{i}] missing {k}")

        # supeco
        if "clttx" not in data.get("supeco", {}):
            errors.append("supeco.clttx missing")

        return len(errors) == 0, errors


# =====================================================
# QUICK PIPELINE
# =====================================================

def run_full_validation(
    gstin: str,
    period: str,
    files: List[str],
    parsed_data: Dict[str, Any] = None,
    json_data: Dict[str, Any] = None
):
    errors = []

    ok, e = GSTValidator.validate_inputs(gstin, period, files)
    errors.extend(e)

    if parsed_data is not None:
        ok2, e2 = GSTValidator.validate_parsed_data(parsed_data)
        errors.extend(e2)

    if json_data is not None:
        ok3, e3 = GSTValidator.validate_json(json_data)
        errors.extend(e3)

    return len(errors) == 0, errors