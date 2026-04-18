# gst_builder.py
# FINAL MERGE SUPPORT VERSION

from typing import Dict, Any, List
import hashlib


class GSTBuilder:

    # =====================================================
    # MAIN
    # =====================================================
    def build_gstr1(self, parsed_data: Dict[str, Any], gstin: str, period: str):
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
            "supeco": self.build_supeco(parsed_data),
            "doc_issue": self.build_doc_issue(parsed_data)
        }

        return json_data

    # =====================================================
    # HASH
    # =====================================================
    def make_hash(self, gstin, period, amount):
        raw = f"{gstin}{period}{amount}"
        return hashlib.md5(raw.encode()).hexdigest()

    # =====================================================
    # B2CS
    # =====================================================
    def build_b2cs(self, rows: List[Dict]):
        out = []

        for r in rows:
            pos = str(r["pos"]).zfill(2)

            tx = round(r["taxable_value"], 2)
            ig = round(r["igst"], 2)
            cg = round(r["cgst"], 2)
            sg = round(r["sgst"], 2)

            if pos == "07":
                out.append({
                    "sply_ty": "INTRA",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": tx,
                    "camt": cg,
                    "samt": sg,
                    "csamt": 0
                })
            else:
                out.append({
                    "sply_ty": "INTER",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": tx,
                    "iamt": ig,
                    "csamt": 0
                })

        return out

    # =====================================================
    # SUPECO
    # =====================================================
    def build_supeco(self, data):
        # merged mode
        if "clttx" in data:
            return {"clttx": data["clttx"]}

        # single mode
        return {
            "clttx": [{
                "etin": data["etin"],
                "suppval": round(data["summary"]["total_taxable"], 2),
                "igst": round(data["summary"]["total_igst"], 2),
                "cgst": round(data["summary"]["total_cgst"], 2),
                "sgst": round(data["summary"]["total_sgst"], 2),
                "cess": 0,
                "flag": "N"
            }]
        }

    # =====================================================
    # DOC ISSUE
    # =====================================================
    def build_doc_issue(self, data):
        blocks = []

        # invoices
        inv = self.make_docs(
            data.get("invoice_docs", []),
            1,
            "Invoices for outward supply"
        )
        if inv:
            blocks.append(inv)

        # credit
        cr = self.make_docs(
            data.get("credit_docs", []),
            5,
            "Credit Note"
        )
        if cr:
            blocks.append(cr)

        # debit
        dr = self.make_docs(
            data.get("debit_docs", []),
            4,
            "Debit Note"
        )
        if dr:
            blocks.append(dr)

        return {"doc_det": blocks}

    # =====================================================
    # MAKE DOCS
    # =====================================================
    def make_docs(self, rows, doc_num, title):
        if not rows:
            return None

        docs = []

        for i, d in enumerate(rows, start=1):
            qty = int(d["totnum"])

            docs.append({
                "num": i,
                "from": d["from"],
                "to": d["to"],
                "totnum": qty,
                "cancel": 0,
                "net_issue": qty
            })

        return {
            "doc_num": doc_num,
            "doc_typ": title,
            "docs": docs
        }