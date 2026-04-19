#!/usr/bin/env python3
# parsers.py - Meesho + Amazon Production Parser

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
    "07": "07", "delhi": "07", "new delhi": "07",
    "09": "09", "up": "09", "uttar pradesh": "09",
    "27": "27", "maharashtra": "27",
    "29": "29", "karnataka": "29",
    "33": "33", "tamil nadu": "33",
    "36": "36", "telangana": "36"
}


def gst_state(x):
    s = str(x).strip().lower()
    return STATE.get(s, s if s.isdigit() and len(s) == 2 else None)


def split_tax(pos, tx, seller="07"):
    tx = safe(tx)
    if pos == seller:
        return 0.0, round(tx / 2, 2), round(tx / 2, 2)
    return tx, 0.0, 0.0


class Base:
    PLATFORM = "Base"
    ETIN = ""

    def parse_files(self, files):
        rows = []
        for f in files:
            data = self.read_one(f)
            if data:
                rows.extend(data)
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
            "invoice_docs": [
                {
                    "invoice_no": r["invoice_no"],
                    "pos": r["pos"],
                    "txval": r["taxable_value"],
                    "igst_amt": r["igst"],
                    "cgst_amt": r["cgst"],
                    "sgst_amt": r["sgst"],
                    "txn_type": "sale",
                }
                for _, r in sales.iterrows()
            ],
            "credit_docs": [
                {
                    "invoice_no": r["invoice_no"],
                    "pos": r["pos"],
                    "txval": abs(r["taxable_value"]),
                    "igst_amt": abs(r["igst"]),
                    "cgst_amt": abs(r["cgst"]),
                    "sgst_amt": abs(r["sgst"]),
                    "txn_type": "return",
                }
                for _, r in returns.iterrows()
            ],
        }


class MeeshoParser(Base):
    PLATFORM = "Meesho"
    ETIN = "07AARCM9332R1CQ"

    def read_one(self, f):
        name = Path(f).name.lower()

        if "tcs_sales" not in name and "meesho" not in name:
            return []

        df = pd.read_excel(f) if f.endswith((".xlsx", ".xls")) else pd.read_csv(f)

        cols = {str(c).lower(): c for c in df.columns}

        inv = cols.get("sub_order_num", list(df.columns)[0])
        st = cols.get("end_customer_state_new", cols.get("state", list(df.columns)[0]))
        taxv = cols.get(
            "total_taxable_sale_value",
            cols.get("taxable_value", list(df.columns)[0])
        )
        tax = cols.get("tax_amount")

        ret = "return" in name
        out = []

        for _, row in df.iterrows():
            pos = gst_state(row.get(st))
            val = safe(row.get(taxv))

            if tax:
                ig, cg, sg = split_tax(pos, row.get(tax), "07")
            else:
                ig, cg, sg = round(val * 0.03, 2), 0.0, 0.0

            if ret:
                val, ig, cg, sg = -abs(val), -abs(ig), -abs(cg), -abs(sg)

            if pos and (val or ig or cg or sg):
                out.append({
                    "invoice_no": str(row.get(inv)),
                    "pos": pos,
                    "taxable_value": val,
                    "igst": ig,
                    "cgst": cg,
                    "sgst": sg,
                    "txn_type": "return" if ret else "sale",
                })

        return out


class AmazonParser(Base):
    PLATFORM = "Amazon"
    ETIN = "07AAICA3918J1CV"

    def read_one(self, f):
        name = Path(f).name.lower()

        if not (name.endswith(".csv") or "amazon" in name or "mtr" in name):
            return []

        df = pd.read_csv(f)
        out = []

        for i, row in df.iterrows():
            pos = gst_state(row.get("ship_to_state"))
            val = safe(row.get("tax_exclusive_gross"))

            ig = safe(row.get("igst_tax"))
            cg = safe(row.get("cgst_tax"))
            sg = safe(row.get("sgst_tax")) + safe(row.get("utgst_tax"))

            typ = str(row.get("transaction_type", "shipment")).lower()
            ret = typ in ["refund", "cancel"] or val < 0

            if ret:
                val, ig, cg, sg = -abs(val), -abs(ig), -abs(cg), -abs(sg)

            if pos and (val or ig or cg or sg):
                out.append({
                    "invoice_no": str(row.get("invoice_number", i)),
                    "pos": pos,
                    "taxable_value": val,
                    "igst": ig,
                    "cgst": cg,
                    "sgst": sg,
                    "txn_type": "return" if ret else "sale",
                })

        return out


class AutoMergeParser:
    def parse_files(self, files):
        results = []

        for parser in [MeeshoParser(), AmazonParser()]:
            res = parser.parse_files(files)
            if res:
                results.append(res)

        docs = []
        seen = set()

        for res in results:
            for k in ["invoice_docs", "credit_docs"]:
                for d in res[k]:
                    key = (d["invoice_no"], d["pos"], d["txval"], d["txn_type"])
                    if key not in seen:
                        seen.add(key)
                        docs.append(d)

        state = defaultdict(
            lambda: {"taxable_value": 0.0, "igst": 0.0, "cgst": 0.0, "sgst": 0.0}
        )

        for d in docs:
            sign = -1 if d["txn_type"] == "return" else 1
            p = d["pos"]

            state[p]["taxable_value"] += sign * d["txval"]
            state[p]["igst"] += sign * d["igst_amt"]
            state[p]["cgst"] += sign * d["cgst_amt"]
            state[p]["sgst"] += sign * d["sgst_amt"]

        rows = []
        for pos, vals in state.items():
            if any(vals.values()):
                rows.append({
                    "pos": pos,
                    "taxable_value": round(vals["taxable_value"], 2),
                    "igst": round(vals["igst"], 2),
                    "cgst": round(vals["cgst"], 2),
                    "sgst": round(vals["sgst"], 2),
                })

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
            "invoice_docs": [d for d in docs if d["txn_type"] == "sale"],
            "credit_docs": [d for d in docs if d["txn_type"] == "return"],
        }