#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional


# =====================================================
# HELPERS
# =====================================================

def safe(v):
    try:
        if pd.isna(v):
            return 0.0
        return float(str(v).replace(",", "").replace("₹", "").strip() or 0)
    except:
        return 0.0


STATE_MAP = {
    "02": "02",
    "03": "03",
    "07": "07",
    "08": "08",
    "09": "09",
    "17": "17",
    "24": "24",
    "27": "27",
    "28": "28",
    "29": "29",
    "33": "33",
    "36": "36",

    "delhi": "07",
    "new delhi": "07",
    "uttar pradesh": "09",
    "up": "09",
    "gujarat": "24",
    "maharashtra": "27",
    "andhra pradesh": "28",
    "karnataka": "29",
    "tamil nadu": "33",
    "telangana": "36",
}


def gst_state(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in STATE_MAP:
        return STATE_MAP[s]
    if s.isdigit():
        return s.zfill(2)
    return None


# =====================================================
# BASE PARSER
# =====================================================

class BaseParser:
    PLATFORM = "Base"
    ETIN = ""

    def parse_files(self, files, seller_gstin=None):
        rows = []
        for f in files:
            data = self.read_one(f)
            if data:
                rows.extend(data)

        return {"merged_rows": rows}

    def read_one(self, f):
        return []


# =====================================================
# MEESHO PARSER
# =====================================================

class MeeshoParser(BaseParser):
    PLATFORM = "Meesho"
    ETIN = "07AARCM9332R1CQ"

    def read_one(self, f):
        name = Path(f).name.lower()

        if "meesho" not in name and "tcs_sales" not in name:
            return []

        df = pd.read_excel(f) if f.endswith((".xlsx", ".xls")) else pd.read_csv(f)

        cols = {str(c).lower(): c for c in df.columns}

        inv = cols.get("sub_order_num", list(df.columns)[0])
        st = cols.get("end_customer_state_new", cols.get("state"))
        txv = cols.get("total_taxable_sale_value", cols.get("taxable_value"))
        tax = cols.get("tax_amount")

        out = []

        for i, row in df.iterrows():
            pos = gst_state(row.get(st))
            if not pos:
                continue

            val = round(safe(row.get(txv)), 2)
            tax_amt = round(safe(row.get(tax)), 2) if tax else round(val * 0.03, 2)

            if pos == "07":
                ig = 0
                cg = round(tax_amt / 2, 2)
                sg = round(tax_amt / 2, 2)
            else:
                ig = tax_amt
                cg = 0
                sg = 0

            out.append({
                "invoice_no": str(row.get(inv, i)),
                "pos": pos,
                "txval": val,
                "igst_amt": ig,
                "cgst_amt": cg,
                "sgst_amt": sg,
                "supplier_etin": self.ETIN,
            })

        return out


# =====================================================
# AMAZON PARSER
# =====================================================

class AmazonParser(BaseParser):
    PLATFORM = "Amazon"
    ETIN = "07AAICA3918J1CV"

    def read_one(self, f):
        name = Path(f).name.lower()

        if "amazon" not in name and "mtr" not in name and not name.endswith(".csv"):
            return []

        try:
            df = pd.read_csv(f, encoding="utf-8")
        except:
            df = pd.read_csv(f, encoding="latin1")

        cols = {str(c).lower(): c for c in df.columns}

        out = []

        for i, row in df.iterrows():
            pos = gst_state(row.get(cols.get("ship_to_state")))
            if not pos:
                continue

            val = round(safe(row.get(cols.get("tax_exclusive_gross"))), 2)
            ig = round(safe(row.get(cols.get("igst_tax"))), 2)
            cg = round(safe(row.get(cols.get("cgst_tax"))), 2)
            sg = round(
                safe(row.get(cols.get("sgst_tax"))) +
                safe(row.get(cols.get("utgst_tax"))), 2
            )

            out.append({
                "invoice_no": str(row.get(cols.get("invoice_number"), i)),
                "pos": pos,
                "txval": val,
                "igst_amt": ig,
                "cgst_amt": cg,
                "sgst_amt": sg,
                "supplier_etin": self.ETIN,
            })

        return out


# =====================================================
# AUTO MERGE
# =====================================================

class AutoMergeParser(BaseParser):
    PLATFORM = "Auto Merge"

    def parse_files(self, files, seller_gstin=None):
        rows = []

        for parser in [MeeshoParser(), AmazonParser()]:
            result = parser.parse_files(files)
            rows.extend(result["merged_rows"])

        return {"merged_rows": rows}