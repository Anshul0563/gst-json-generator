#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# parsers.py - FINAL PRODUCTION VERSION (Meesho + Amazon Merge)

import pandas as pd
from pathlib import Path
from collections import defaultdict


# =====================================================
# HELPERS
# =====================================================

def safe(v):
    try:
        if pd.isna(v):
            return 0.0
        s = str(v).replace(",", "").replace("₹", "").strip()
        if s == "":
            return 0.0
        return float(s)
    except:
        return 0.0


STATE = {
    "01":"01","02":"02","03":"03","04":"04","05":"05","06":"06","07":"07",
    "08":"08","09":"09","10":"10","11":"11","12":"12","13":"13","14":"14",
    "15":"15","16":"16","17":"17","18":"18","19":"19","20":"20","21":"21",
    "22":"22","23":"23","24":"24","25":"25","26":"26","27":"27","28":"28",
    "29":"29","30":"30","31":"31","32":"32","33":"33","34":"34","35":"35",
    "36":"36","37":"37","38":"38",

    "delhi":"07","new delhi":"07",
    "up":"09","uttar pradesh":"09","noida":"09","ghaziabad":"09",
    "maharashtra":"27","mumbai":"27","pune":"27",
    "karnataka":"29","bangalore":"29","bengaluru":"29",
    "tamil nadu":"33","chennai":"33",
    "telangana":"36","hyderabad":"36",
    "rajasthan":"08",
    "gujarat":"24",
    "kerala":"32",
    "west bengal":"19","kolkata":"19",
    "haryana":"06","gurgaon":"06","gurugram":"06",
    "punjab":"03",
    "bihar":"10",
    "odisha":"21",
    "assam":"18",
    "madhya pradesh":"23",
}


def gst_state(x):
    s = str(x).strip().lower()
    if s in STATE:
        return STATE[s]

    if s.isdigit():
        s = s.zfill(2)
        if s in STATE:
            return s

    return None


def split_tax(pos, amt, seller="07"):
    amt = safe(amt)

    if pos == seller:
        half = round(amt / 2, 2)
        return 0.0, half, half

    return amt, 0.0, 0.0


# =====================================================
# BASE
# =====================================================

class BaseParser:
    PLATFORM = "Base"
    ETIN = ""

    def parse_files(self, files, seller_gstin=None):
        rows = []

        for f in files:
            try:
                data = self.read_one(f)
                if data:
                    rows.extend(data)
            except Exception as e:
                print(f"{self.PLATFORM} error in {f}: {e}")

        return self.finalize(rows)

    def finalize(self, rows):
        if not rows:
            return None

        df = pd.DataFrame(rows)

        df = df.drop_duplicates(
            subset=["invoice_no", "pos", "taxable_value", "txn_type"]
        ).reset_index(drop=True)

        grp = (
            df.groupby("pos", as_index=False)[
                ["taxable_value", "igst", "cgst", "sgst"]
            ]
            .sum()
            .round(2)
        )

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


# =====================================================
# MEESHO
# =====================================================

class MeeshoParser(BaseParser):
    PLATFORM = "Meesho"
    ETIN = "07AARCM9332R1CQ"

    def read_one(self, f):
        name = Path(f).name.lower()

        if not ("meesho" in name or "tcs_sales" in name):
            return []

        df = pd.read_excel(f) if f.endswith((".xlsx", ".xls")) else pd.read_csv(f)

        cols = {str(c).strip().lower(): c for c in df.columns}

        inv = cols.get("sub_order_num", list(df.columns)[0])
        st = cols.get("end_customer_state_new", cols.get("state"))
        taxv = cols.get(
            "total_taxable_sale_value",
            cols.get("taxable_value", list(df.columns)[0])
        )
        tax = cols.get("tax_amount")

        is_return = "return" in name

        out = []

        for i, row in df.iterrows():
            pos = gst_state(row.get(st))
            if not pos:
                continue

            val = safe(row.get(taxv))

            if tax:
                ig, cg, sg = split_tax(pos, row.get(tax), "07")
            else:
                if pos == "07":
                    ig, cg, sg = 0.0, round(val * 0.015, 2), round(val * 0.015, 2)
                else:
                    ig, cg, sg = round(val * 0.03, 2), 0.0, 0.0

            if is_return:
                val, ig, cg, sg = -abs(val), -abs(ig), -abs(cg), -abs(sg)

            if abs(val) < 0.01 and abs(ig)+abs(cg)+abs(sg) < 0.01:
                continue

            out.append({
                "invoice_no": str(row.get(inv, i)),
                "pos": pos,
                "taxable_value": val,
                "igst": ig,
                "cgst": cg,
                "sgst": sg,
                "txn_type": "return" if is_return else "sale",
            })

        return out


# =====================================================
# AMAZON
# =====================================================

class AmazonParser(BaseParser):
    PLATFORM = "Amazon"
    ETIN = "07AAICA3918J1CV"

    def read_one(self, f):
        name = Path(f).name.lower()

        if not (".csv" in name or "amazon" in name or "mtr" in name):
            return []

        try:
            df = pd.read_csv(f, encoding="utf-8")
        except:
            df = pd.read_csv(f, encoding="latin1")

        cols = {str(c).strip().lower(): c for c in df.columns}

        out = []

        for i, row in df.iterrows():
            pos = gst_state(row.get(cols.get("ship_to_state")))
            if not pos:
                continue

            val = safe(row.get(cols.get("tax_exclusive_gross")))

            ig = safe(row.get(cols.get("igst_tax")))
            cg = safe(row.get(cols.get("cgst_tax")))
            sg = safe(row.get(cols.get("sgst_tax"))) + safe(
                row.get(cols.get("utgst_tax"))
            )

            typ = str(
                row.get(cols.get("transaction_type"), "shipment")
            ).strip().lower()

            is_return = typ in ["refund", "cancel", "cancelled"] or val < 0

            if is_return:
                val, ig, cg, sg = -abs(val), -abs(ig), -abs(cg), -abs(sg)

            if abs(val) < 0.01 and abs(ig)+abs(cg)+abs(sg) < 0.01:
                continue

            out.append({
                "invoice_no": str(row.get(cols.get("invoice_number"), i)),
                "pos": pos,
                "taxable_value": val,
                "igst": ig,
                "cgst": cg,
                "sgst": sg,
                "txn_type": "return" if is_return else "sale",
            })

        return out


# =====================================================
# AUTO MERGE
# =====================================================

class AutoMergeParser:
    def parse_files(self, files, seller_gstin=None):
        meesho_files = []
        amazon_files = []

        for f in files:
            name = Path(f).name.lower()

            if "meesho" in name or "tcs_sales" in name:
                meesho_files.append(f)

            elif "amazon" in name or "mtr" in name or name.endswith(".csv"):
                amazon_files.append(f)

        results = []

        if meesho_files:
            r = MeeshoParser().parse_files(meesho_files, seller_gstin)
            if r:
                results.append(r)

        if amazon_files:
            r = AmazonParser().parse_files(amazon_files, seller_gstin)
            if r:
                results.append(r)

        docs = []
        seen = set()

        for res in results:
            for bucket in ["invoice_docs", "credit_docs"]:
                for d in res[bucket]:
                    key = (
                        d["invoice_no"],
                        d["pos"],
                        round(d["txval"], 2),
                        d["txn_type"],
                    )
                    if key not in seen:
                        seen.add(key)
                        docs.append(d)

        state = defaultdict(
            lambda: {
                "taxable_value": 0.0,
                "igst": 0.0,
                "cgst": 0.0,
                "sgst": 0.0,
            }
        )

        for d in docs:
            sign = -1 if d["txn_type"] == "return" else 1
            p = d["pos"]

            state[p]["taxable_value"] += sign * d["txval"]
            state[p]["igst"] += sign * d["igst_amt"]
            state[p]["cgst"] += sign * d["cgst_amt"]
            state[p]["sgst"] += sign * d["sgst_amt"]

        rows = []

        for pos in sorted(state.keys()):
            vals = state[pos]

            if any(abs(v) > 0.001 for v in vals.values()):
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