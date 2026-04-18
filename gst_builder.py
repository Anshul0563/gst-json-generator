
from typing import Dict, List
import hashlib


class GSTBuilder:

    def build_gstr1(self, parsed_data, gstin, period):
        s = parsed_data["summary"]

        gt = round(s["total_taxable"], 2)

        return {
            "gstin": gstin,
            "fp": period,
            "version": "GST3.1.6",
            "hash": self.make_hash(gstin, period, gt),
            "gt": gt,
            "cur_gt": gt,
            "b2cs": self.build_b2cs(s["rows"]),
            "supeco": self.build_supeco(parsed_data),
            "doc_issue": self.build_doc_issue(parsed_data)
        }

    # =====================================================
    def make_hash(self, gstin, period, amount):
        return hashlib.md5(f"{gstin}{period}{amount}".encode()).hexdigest()

    # =====================================================
    def build_b2cs(self, rows: List[Dict]):
        out = []

        for r in rows:
            pos = str(r["pos"]).zfill(2)

            tx = round(float(r["taxable_value"]), 2)
            ig = round(float(r["igst"]), 2)
            cg = round(float(r["cgst"]), 2)
            sg = round(float(r["sgst"]), 2)

            # remove zero rows
            if tx == 0 and ig == 0 and cg == 0 and sg == 0:
                continue

            if pos == "07":
                if cg == 0 and sg == 0 and ig > 0:
                    cg = round(ig / 2, 2)
                    sg = round(ig / 2, 2)

                row = {
                    "sply_ty": "INTRA",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": tx,
                    "camt": cg,
                    "samt": sg,
                    "csamt": 0
                }

            else:
                row = {
                    "sply_ty": "INTER",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": tx,
                    "iamt": ig if ig else round(cg + sg, 2),
                    "csamt": 0
                }

            out.append(row)

        return out

    # =====================================================
    def build_supeco(self, data):
        if "clttx" in data:
            rows = [
                x for x in data["clttx"]
                if x["suppval"] != 0
            ]
            return {"clttx": rows}

        s = data["summary"]

        return {
            "clttx": [{
                "etin": data["etin"],
                "suppval": round(s["total_taxable"], 2),
                "igst": round(s["total_igst"], 2),
                "cgst": round(s["total_cgst"], 2),
                "sgst": round(s["total_sgst"], 2),
                "cess": 0,
                "flag": "N"
            }]
        }

    # =====================================================
    def build_doc_issue(self, data):
        docs = data.get("invoice_docs", [])

        if not docs:
            return {"doc_det": []}

        rows = []

        for i, d in enumerate(docs, start=1):
            qty = int(d["totnum"])

            rows.append({
                "num": i,
                "from": d["from"],
                "to": d["to"],
                "totnum": qty,
                "cancel": 0,
                "net_issue": qty
            })

        return {
            "doc_det": [
                {
                    "doc_num": 1,
                    "doc_typ": "Invoices for outward supply",
                    "docs": rows
                }
            ]
        }