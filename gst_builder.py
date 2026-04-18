# gst_builder.py
# FINAL CLONE BUILDER - Works with Final parsers.py

from typing import Dict, Any, List
from datetime import datetime
import hashlib


class GSTBuilder:
    def __init__(self):
        pass

    # =====================================================
    # MAIN
    # =====================================================
    def build_gstr1(self, parsed_data: Dict[str, Any], gstin: str, period: str) -> Dict[str, Any]:
        """
        Build final GST JSON from single parser output
        """
        summary = parsed_data["summary"]

        total_taxable = round(summary["total_taxable"], 2)
        total_igst = round(summary["total_igst"], 2)
        total_cgst = round(summary["total_cgst"], 2)
        total_sgst = round(summary["total_sgst"], 2)

        json_data = {
            "gstin": gstin,
            "fp": period,
            "version": "GST3.1.6",
            "hash": self.make_hash(gstin, period, total_taxable),

            "gt": total_taxable,
            "cur_gt": total_taxable,

            "b2cs": self.build_b2cs(summary["rows"]),
            "supeco": self.build_supeco(
                parsed_data["etin"],
                total_taxable,
                total_igst,
                total_cgst,
                total_sgst
            ),
            "doc_issue": self.build_doc_issue(parsed_data)
        }

        return json_data

    # =====================================================
    # HASH
    # =====================================================
    def make_hash(self, gstin: str, period: str, amount: float) -> str:
        raw = f"{gstin}{period}{amount}"
        return hashlib.md5(raw.encode()).hexdigest()

    # =====================================================
    # B2CS
    # =====================================================
    def build_b2cs(self, rows: List[Dict]) -> List[Dict]:
        out = []

        for r in rows:
            pos = str(r["pos"]).zfill(2)

            taxable = round(float(r["taxable_value"]), 2)
            igst = round(float(r["igst"]), 2)
            cgst = round(float(r["cgst"]), 2)
            sgst = round(float(r["sgst"]), 2)

            if pos == "07":
                row = {
                    "sply_ty": "INTRA",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": taxable,
                    "camt": cgst,
                    "samt": sgst,
                    "csamt": 0
                }
            else:
                row = {
                    "sply_ty": "INTER",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": taxable,
                    "iamt": igst,
                    "csamt": 0
                }

            out.append(row)

        return out

    # =====================================================
    # SUPECO
    # =====================================================
    def build_supeco(self, etin, suppval, igst, cgst, sgst):
        return {
            "clttx": [
                {
                    "etin": etin,
                    "suppval": round(suppval, 2),
                    "igst": round(igst, 2),
                    "cgst": round(cgst, 2),
                    "sgst": round(sgst, 2),
                    "cess": 0,
                    "flag": "N"
                }
            ]
        }

    # =====================================================
    # DOC ISSUE
    # =====================================================
    def build_doc_issue(self, data):
        sections = []

        # -------------------------
        # Invoices
        # -------------------------
        invoice_docs = data.get("invoice_docs", [])
        if invoice_docs:
            docs = []
            for i, d in enumerate(invoice_docs, start=1):
                docs.append({
                    "num": i,
                    "from": d["from"],
                    "to": d["to"],
                    "totnum": d["totnum"],
                    "cancel": 0,
                    "net_issue": d["totnum"]
                })

            sections.append({
                "doc_num": 1,
                "doc_typ": "Invoices for outward supply",
                "docs": docs
            })

        # -------------------------
        # Credit Notes
        # -------------------------
        credit_docs = data.get("credit_docs", [])
        if credit_docs:
            docs = []
            for i, d in enumerate(credit_docs, start=1):
                docs.append({
                    "num": i,
                    "from": d["from"],
                    "to": d["to"],
                    "totnum": d["totnum"],
                    "cancel": 0,
                    "net_issue": d["totnum"]
                })

            sections.append({
                "doc_num": 5,
                "doc_typ": "Credit Note",
                "docs": docs
            })

        # -------------------------
        # Debit Notes
        # -------------------------
        debit_docs = data.get("debit_docs", [])
        if debit_docs:
            docs = []
            for i, d in enumerate(debit_docs, start=1):
                docs.append({
                    "num": i,
                    "from": d["from"],
                    "to": d["to"],
                    "totnum": d["totnum"],
                    "cancel": 0,
                    "net_issue": d["totnum"]
                })

            sections.append({
                "doc_num": 4,
                "doc_typ": "Debit Note",
                "docs": docs
            })

        return {"doc_det": sections}