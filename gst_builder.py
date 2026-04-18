
import json
import hashlib
from typing import Dict, Any, List
from utils import get_state_code_map


class GSTBuilder:
    def __init__(self):
        self.state_map = get_state_code_map()

    # =====================================================
    # MAIN
    # =====================================================
    def build_gstr1(self, parsed_data: Dict[str, Any], gstin: str, period: str) -> Dict[str, Any]:
        net = parsed_data["net"]

        gt = round(float(net.get("total_taxable", 0)), 2)
        cur_gt = gt

        result = {
            "gstin": gstin,
            "fp": period,
            "version": "GST3.0",
            "hash": "",
            "gt": gt,
            "cur_gt": cur_gt,
            "b2cs": self._build_b2cs(net.get("state_summary", [])),
            "supeco": self._build_supeco(parsed_data),
            "doc_issue": self._build_doc_issue(parsed_data),
        }

        result["hash"] = self._make_hash(result)
        return result

    # =====================================================
    # B2CS
    # =====================================================
    def _build_b2cs(self, rows: List[Dict]) -> List[Dict]:
        output = []

        for row in rows:
            txval = round(float(row.get("taxable_value", 0)), 2)
            igst = round(float(row.get("igst", 0)), 2)
            cgst = round(float(row.get("cgst", 0)), 2)
            sgst = round(float(row.get("sgst", 0)), 2)

            if abs(txval) < 0.01:
                continue

            item = {
                "sply_ty": "INTER" if igst > 0 else "INTRA",
                "rt": self._detect_rate(txval, igst, cgst, sgst),
                "typ": "OE",
                "pos": self._state_code(row.get("state_code")),
                "txval": txval,
                "iamt": igst,
                "camt": cgst,
                "samt": sgst,
                "csamt": 0.0
            }

            output.append(item)

        return output

    # =====================================================
    # SUPECO
    # =====================================================
    def _build_supeco(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        net = parsed_data["net"]

        return {
            "clttx": [
                {
                    "etin": "URP",
                    "suppval": round(float(net.get("total_taxable", 0)), 2),
                    "iamt": round(float(net.get("total_igst", 0)), 2),
                    "camt": round(float(net.get("total_cgst", 0)), 2),
                    "samt": round(float(net.get("total_sgst", 0)), 2),
                    "csamt": 0.0
                }
            ]
        }

    # =====================================================
    # DOC ISSUE
    # =====================================================
    def _build_doc_issue(self, parsed_data: Dict[str, Any]) -> List[Dict]:
        docs = parsed_data.get("invoice_details", [])

        if not docs:
            return []

        return [
            {
                "doc_det": [
                    {
                        "doc_num": 1,
                        "docs": docs
                    }
                ]
            }
        ]

    # =====================================================
    # HELPERS
    # =====================================================
    def _state_code(self, state_name: str) -> str:
        if state_name is None:
            return "00"

        s = str(state_name).strip().upper()

        # already numeric code
        if s.isdigit():
            return s.zfill(2)

        return self.state_map.get(s, "00")

    def _detect_rate(self, txval: float, igst: float, cgst: float, sgst: float) -> float:
        tax = igst + cgst + sgst

        if txval == 0:
            return 0.0

        rate = (tax / txval) * 100
        return round(rate, 2)

    def _make_hash(self, data: Dict[str, Any]) -> str:
        raw = json.dumps(data, sort_keys=True, default=str).encode()
        return hashlib.sha256(raw).hexdigest()