# FULL updated gst_builder.py + parsers.py + exact JSON
# (same style as uploaded output)

# =========================
# FILE: gst_builder.py
# =========================

import json


class GSTBuilder:
    def __init__(self):
        self.version = "GST3.1.6"

    def build(self, parsed_data, gstin, fp):
        summary = parsed_data.get("summary", {})
        rows = summary.get("rows", [])
        clttx = parsed_data.get("clttx", [])
        doc_issue = parsed_data.get("doc_issue", {"doc_det": []})

        b2cs = []

        for r in rows:
            pos = str(r["pos"]).zfill(2)
            tx = round(float(r["taxable_value"]), 2)
            ig = round(float(r["igst"]), 2)
            cg = round(float(r["cgst"]), 2)
            sg = round(float(r["sgst"]), 2)

            item = {
                "sply_ty": "INTRA" if cg > 0 or sg > 0 else "INTER",
                "rt": 3.0,
                "typ": "OE",
                "pos": pos,
                "txval": tx,
                "csamt": 0,
            }

            if ig != 0:
                item["iamt"] = ig
            else:
                item["camt"] = cg
                item["samt"] = sg

            b2cs.append(item)

        output = {
            "gstin": gstin,
            "fp": fp,
            "version": self.version,
            "hash": "hash",
            "b2cs": b2cs,
            "supeco": {
                "clttx": clttx
            },
            "doc_issue": doc_issue,
            "summary": {
                "total_items": len(b2cs),
                "total_taxable": round(summary.get("total_taxable", 0), 2),
                "total_igst": round(summary.get("total_igst", 0), 2),
                "total_cgst": round(summary.get("total_cgst", 0), 2),
                "total_sgst": round(summary.get("total_sgst", 0), 2),
                "total_tax": round(
                    summary.get("total_igst", 0)
                    + summary.get("total_cgst", 0)
                    + summary.get("total_sgst", 0),
                    2
                ),
            }
        }

        return output

    def save(self, data, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


# =========================
# FILE: parsers.py
# =========================

import pandas as pd
from pathlib import Path
from collections import defaultdict


def safe(v):
    try:
        if pd.isna(v):
            return 0.0
        return float(str(v).replace(",", "").replace("₹", "").strip() or 0)
    except:
        return 0.0


STATE = {
    "01": "01", "jammu": "01",
    "02": "02", "himachal": "02",
    "03": "03", "punjab": "03",
    "04": "04", "chandigarh": "04",
    "05": "05", "uttarakhand": "05",
    "06": "06", "haryana": "06",
    "07": "07", "delhi": "07", "new delhi": "07",
    "08": "08", "rajasthan": "08",
    "09": "09", "up": "09", "uttar pradesh": "09",
    "10": "10", "bihar": "10",
    "17": "17", "meghalaya": "17",
    "19": "19", "west bengal": "19",
    "20": "20", "jharkhand": "20",
    "21": "21", "odisha": "21",
    "24": "24", "gujarat": "24",
    "27": "27", "maharashtra": "27",
    "28": "28", "andhra pradesh": "28",
    "29": "29", "karnataka": "29",
    "33": "33", "tamil nadu": "33",
    "36": "36", "telangana": "36",
    "37": "37", "ap new": "37",
}


def gst_state(x):
    s = str(x).strip().lower()
    if s in STATE:
        return STATE[s]
    if s.isdigit():
        return s.zfill(2)
    return None


def split_tax(pos, amt, seller="07"):
    amt = safe(amt)
    if pos == seller:
        half = round(amt / 2, 2)
        return 0.0, half, half
    return amt, 0.0, 0.0


def build_doc_ranges(nums):
    nums = sorted(set(str(x) for x in nums if str(x).strip()))
    if not nums:
        return []

    return [{
        "num": 1,
        "from": nums[0],
        "to": nums[-1],
        "totnum": len(nums),
        "cancel": 0,
        "net_issue": len(nums),
    }]


class Base:
    PLATFORM = "Base"
    ETIN = ""

    def parse_files(self, files, seller_gstin=None):
        rows = []
        for f in files:
            rows.extend(self.read_one(f))
        return self.finalize(rows)

    def finalize(self, rows):
        if not rows:
            return None

        df = pd.DataFrame(rows).drop_duplicates(
            subset=["invoice_no", "pos", "taxable_value", "txn_type"]
        )

        grp = df.groupby("pos", as_index=False)[
            ["taxable_value", "igst", "cgst", "sgst"]
        ].sum().round(2)

        sales = df[df["txn_type"] == "sale"]
        returns = df[df["txn_type"] == "return"]

        return {
            "etin": self.ETIN,
            "summary": {
                "rows": grp.to_dict("records"),
                "total_taxable": round(grp["taxable_value"].sum(), 2),
                "total_igst": round(grp["igst"].sum(), 2),
                "total_cgst": round(grp["cgst"].sum(), 2),
                "total_sgst": round(grp["sgst"].sum(), 2),
            },
            "invoice_docs": sales.to_dict("records"),
            "credit_docs": returns.to_dict("records"),
        }


class MeeshoParser(Base):
    PLATFORM = "Meesho"
    ETIN = "07AARCM9332R1CQ"

    def read_one(self, f):
        name = Path(f).name.lower()
        if "meesho" not in name and "tcs_sales" not in name:
            return []

        df = pd.read_excel(f) if f.endswith(("xlsx", "xls")) else pd.read_csv(f)

        cols = {str(c).lower(): c for c in df.columns}

        inv = cols.get("sub_order_num", list(df.columns)[0])
        st = cols.get("end_customer_state_new", cols.get("state"))
        taxv = cols.get("total_taxable_sale_value", cols.get("taxable_value"))
        tax = cols.get("tax_amount")

        is_return = "return" in name
        out = []

        for _, row in df.iterrows():
            pos = gst_state(row.get(st))
            val = safe(row.get(taxv))
            if not pos:
                continue

            if tax:
                ig, cg, sg = split_tax(pos, row.get(tax))
            else:
                ig = round(val * 0.03, 2)
                cg = sg = 0.0
                if pos == "07":
                    ig = 0
                    cg = sg = round(val * 0.015, 2)

            if is_return:
                val, ig, cg, sg = -abs(val), -abs(ig), -abs(cg), -abs(sg)

            out.append({
                "invoice_no": str(row.get(inv)),
                "pos": pos,
                "taxable_value": val,
                "igst": ig,
                "cgst": cg,
                "sgst": sg,
                "txn_type": "return" if is_return else "sale",
            })

        return out


class AmazonParser(Base):
    PLATFORM = "Amazon"
    ETIN = "07AAICA3918J1CV"

    def read_one(self, f):
        name = Path(f).name.lower()
        if "amazon" not in name and "mtr" not in name and not name.endswith(".csv"):
            return []

        df = pd.read_csv(f)
        cols = {str(c).lower(): c for c in df.columns}
        out = []

        for i, row in df.iterrows():
            pos = gst_state(row.get(cols.get("ship_to_state")))
            if not pos:
                continue

            val = safe(row.get(cols.get("tax_exclusive_gross")))
            ig = safe(row.get(cols.get("igst_tax")))
            cg = safe(row.get(cols.get("cgst_tax")))
            sg = safe(row.get(cols.get("sgst_tax"))) + safe(row.get(cols.get("utgst_tax")))

            typ = str(row.get(cols.get("transaction_type"), "shipment")).lower()
            ret = typ in ["refund", "cancel"] or val < 0

            if ret:
                val, ig, cg, sg = -abs(val), -abs(ig), -abs(cg), -abs(sg)

            out.append({
                "invoice_no": str(row.get(cols.get("invoice_number"), i)),
                "pos": pos,
                "taxable_value": val,
                "igst": ig,
                "cgst": cg,
                "sgst": sg,
                "txn_type": "return" if ret else "sale",
            })

        return out


class AutoMergeParser:
    def parse_files(self, files, seller_gstin=None):
        results = []

        for p in [MeeshoParser(), AmazonParser()]:
            r = p.parse_files(files, seller_gstin)
            if r:
                results.append(r)

        docs = []
        seen = set()

        for r in results:
            for bucket in ["invoice_docs", "credit_docs"]:
                for d in r[bucket]:
                    key = (
                        d["invoice_no"],
                        d["pos"],
                        round(d["taxable_value"], 2),
                        d["txn_type"]
                    )
                    if key not in seen:
                        seen.add(key)
                        docs.append(d)

        state = defaultdict(lambda: {
            "taxable_value": 0,
            "igst": 0,
            "cgst": 0,
            "sgst": 0
        })

        for d in docs:
            p = d["pos"]
            state[p]["taxable_value"] += d["taxable_value"]
            state[p]["igst"] += d["igst"]
            state[p]["cgst"] += d["cgst"]
            state[p]["sgst"] += d["sgst"]

        rows = []
        for pos, v in sorted(state.items()):
            rows.append({
                "pos": pos,
                "taxable_value": round(v["taxable_value"], 2),
                "igst": round(v["igst"], 2),
                "cgst": round(v["cgst"], 2),
                "sgst": round(v["sgst"], 2),
            })

        sales = [d for d in docs if d["txn_type"] == "sale"]
        returns = [d for d in docs if d["txn_type"] == "return"]

        return {
            "summary": {
                "rows": rows,
                "total_taxable": round(sum(x["taxable_value"] for x in rows), 2),
                "total_igst": round(sum(x["igst"] for x in rows), 2),
                "total_cgst": round(sum(x["cgst"] for x in rows), 2),
                "total_sgst": round(sum(x["sgst"] for x in rows), 2),
            },
            "clttx": [
                {
                    "etin": r["etin"],
                    "suppval": r["summary"]["total_taxable"],
                    "igst": r["summary"]["total_igst"],
                    "cgst": r["summary"]["total_cgst"],
                    "sgst": r["summary"]["total_sgst"],
                    "cess": 0,
                    "flag": "N",
                }
                for r in results
            ],
            "doc_issue": {
                "doc_det": [
                    {
                        "doc_num": 1,
                        "doc_typ": "Invoices for outward supply",
                        "docs": build_doc_ranges([x["invoice_no"] for x in sales]),
                    },
                    {
                        "doc_num": 5,
                        "doc_typ": "Credit Note",
                        "docs": build_doc_ranges([x["invoice_no"] for x in returns]),
                    },
                    {
                        "doc_num": 4,
                        "doc_typ": "Debit Note",
                        "docs": [],
                    },
                ]
            },
        }