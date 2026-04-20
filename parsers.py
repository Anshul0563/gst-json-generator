#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parsers.py - FINAL Production Parser
Meesho + Amazon only
Portal-ready single source of truth = merged_rows
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)


# =====================================================
# STATE MAP
# =====================================================

STATE_MAP = {
    "01": "01", "02": "02", "03": "03", "04": "04", "05": "05",
    "06": "06", "07": "07", "08": "08", "09": "09", "10": "10",
    "11": "11", "12": "12", "13": "13", "14": "14", "15": "15",
    "16": "16", "17": "17", "18": "18", "19": "19", "20": "20",
    "21": "21", "22": "22", "23": "23", "24": "24", "25": "25",
    "26": "26", "27": "27", "28": "28", "29": "29", "30": "30",
    "31": "31", "32": "32", "33": "33", "34": "34", "35": "35",
    "36": "36", "37": "37", "38": "38",

    "delhi": "07",
    "new delhi": "07",

    "uttar pradesh": "09",
    "up": "09",
    "noida": "09",
    "ghaziabad": "09",

    "haryana": "06",
    "gurgaon": "06",
    "gurugram": "06",

    "maharashtra": "27",
    "mumbai": "27",
    "pune": "27",

    "karnataka": "29",
    "bangalore": "29",
    "bengaluru": "29",

    "telangana": "36",
    "hyderabad": "36",

    "tamil nadu": "33",
    "chennai": "33",

    "gujarat": "24",
    "rajasthan": "08",
    "kerala": "32",
    "west bengal": "19",
    "kolkata": "19",
    "punjab": "03",
    "assam": "18",
    "bihar": "10",
    "odisha": "21",
    "madhya pradesh": "23",
}


# =====================================================
# HELPERS
# =====================================================

def safe(v) -> float:
    try:
        if pd.isna(v):
            return 0.0

        s = str(v).replace(",", "").replace("₹", "").strip()

        if not s or s.lower() in ["na", "n/a", "null", "none"]:
            return 0.0

        return round(float(s), 2)

    except Exception:
        return 0.0


def gst_state(x: Optional[str]) -> Optional[str]:
    if x is None:
        return None

    s = str(x).strip().lower()

    if not s:
        return None

    if s in STATE_MAP:
        return STATE_MAP[s]

    if s.isdigit():
        s = s.zfill(2)
        return STATE_MAP.get(s)

    return None


# =====================================================
# MAIN PARSER
# =====================================================

class AutoMergeParser:
    """
    Meesho + Amazon only
    Returns:
    {
        "merged_rows": [...]
    }
    """

    MEESHO_ETIN = "07AARCM9332R1CQ"
    AMAZON_ETIN = "07AAICA3918J1CV"

    # -------------------------------------------------
    # ENTRY
    # -------------------------------------------------
    def parse_files(self, files: List[str], seller_gstin=None) -> Optional[Dict[str, Any]]:
        merged_rows = []

        for f in files:
            name = Path(f).name.lower()

            try:
                if self._is_meesho(name):
                    rows = self._parse_meesho(f)
                    if rows:
                        merged_rows.extend(rows)

                elif self._is_amazon(name):
                    rows = self._parse_amazon(f)
                    if rows:
                        merged_rows.extend(rows)

            except Exception as e:
                logging.error(f"Parse failed {name}: {e}")

        if not merged_rows:
            return None

        df = pd.DataFrame(merged_rows)

        # Deduplicate
        dedup_cols = [
            "invoice_no",
            "pos",
            "txval",
            "igst_amt",
            "cgst_amt",
            "sgst_amt",
            "txn_type",
            "supplier_etin",
        ]

        df = df.drop_duplicates(subset=dedup_cols, keep="first").reset_index(drop=True)

        return {
            "merged_rows": df.to_dict("records")
        }

    # -------------------------------------------------
    # FILE DETECTION
    # -------------------------------------------------
    def _is_meesho(self, name: str) -> bool:
        keys = ["meesho", "tcs_sales", "tax_invoice"]
        return any(k in name for k in keys)

    def _is_amazon(self, name: str) -> bool:
        keys = ["amazon", "mtr", "mtb", "settlement"]
        return any(k in name for k in keys) or name.endswith(".csv")

    # -------------------------------------------------
    # MEESHO
    # -------------------------------------------------
    def _parse_meesho(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        try:
            if file_path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path, sheet_name=0)
            else:
                try:
                    df = pd.read_csv(file_path, encoding="utf-8")
                except Exception:
                    df = pd.read_csv(file_path, encoding="latin1")

            if df.empty:
                return None

            cols = {str(c).strip().lower(): c for c in df.columns}

            inv_col = cols.get("sub_order_num", cols.get("order_id"))
            state_col = cols.get("end_customer_state_new", cols.get("state"))
            value_col = cols.get(
                "total_taxable_sale_value",
                cols.get("taxable_value", cols.get("amount"))
            )
            tax_col = cols.get("tax_amount", cols.get("tax"))

            if not (inv_col and state_col and value_col):
                return None

            fname = Path(file_path).name.lower()
            is_return_file = ("return" in fname or "credit" in fname)

            out = []

            for i, row in df.iterrows():
                pos = gst_state(row.get(state_col))
                if not pos:
                    continue

                val = safe(row.get(value_col))

                tax_amt = safe(row.get(tax_col)) if tax_col else round(val * 0.03, 2)

                if abs(val) < 0.01 and abs(tax_amt) < 0.01:
                    continue

                if pos == "07":
                    igst = 0.0
                    cgst = round(tax_amt / 2, 2)
                    sgst = round(tax_amt / 2, 2)
                else:
                    igst = round(tax_amt, 2)
                    cgst = 0.0
                    sgst = 0.0

                if is_return_file:
                    val = -abs(val)
                    igst = -abs(igst)
                    cgst = -abs(cgst)
                    sgst = -abs(sgst)
                    txn_type = "return"
                else:
                    txn_type = "sale"

                out.append({
                    "invoice_no": str(row.get(inv_col, i)).strip(),
                    "pos": pos,
                    "txval": round(val, 2),
                    "igst_amt": round(igst, 2),
                    "cgst_amt": round(cgst, 2),
                    "sgst_amt": round(sgst, 2),
                    "txn_type": txn_type,
                    "supplier_etin": self.MEESHO_ETIN,
                    "supplier_name": "Meesho"
                })

            return out if out else None

        except Exception as e:
            logging.error(f"Meesho parse error: {e}")
            return None

    # -------------------------------------------------
    # AMAZON
    # -------------------------------------------------
    def _parse_amazon(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        try:
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except Exception:
                df = pd.read_csv(file_path, encoding="latin1")

            if df.empty:
                return None

            cols = {str(c).strip().lower(): c for c in df.columns}

            state_col = cols.get("ship_to_state", cols.get("destination_state"))
            value_col = cols.get(
                "tax_exclusive_gross",
                cols.get("transaction_amount", cols.get("amount"))
            )

            igst_col = cols.get("igst_tax", cols.get("igst"))
            cgst_col = cols.get("cgst_tax", cols.get("cgst"))
            sgst_col = cols.get("sgst_tax", cols.get("sgst"))
            utgst_col = cols.get("utgst_tax", cols.get("utgst"))

            inv_col = cols.get("invoice_number", cols.get("document_no"))
            txn_col = cols.get("transaction_type", cols.get("type"))

            if not (state_col and value_col):
                return None

            out = []

            for i, row in df.iterrows():
                pos = gst_state(row.get(state_col))
                if not pos:
                    continue

                val = safe(row.get(value_col))
                igst = safe(row.get(igst_col)) if igst_col else 0.0
                cgst = safe(row.get(cgst_col)) if cgst_col else 0.0
                sgst = safe(row.get(sgst_col)) if sgst_col else 0.0
                utgst = safe(row.get(utgst_col)) if utgst_col else 0.0

                sgst += utgst

                txn_text = str(row.get(txn_col, "shipment")).strip().lower() if txn_col else "shipment"

                is_return = (
                    txn_text in ["refund", "cancel", "cancelled", "return", "reversal"]
                    or val < 0
                )

                if abs(val) < 0.01 and abs(igst + cgst + sgst) < 0.01:
                    continue

                if is_return:
                    val = -abs(val)
                    igst = -abs(igst)
                    cgst = -abs(cgst)
                    sgst = -abs(sgst)
                    txn_type = "return"
                else:
                    val = abs(val)
                    igst = abs(igst)
                    cgst = abs(cgst)
                    sgst = abs(sgst)
                    txn_type = "sale"

                out.append({
                    "invoice_no": str(row.get(inv_col, i)).strip() if inv_col else str(i),
                    "pos": pos,
                    "txval": round(val, 2),
                    "igst_amt": round(igst, 2),
                    "cgst_amt": round(cgst, 2),
                    "sgst_amt": round(sgst, 2),
                    "txn_type": txn_type,
                    "supplier_etin": self.AMAZON_ETIN,
                    "supplier_name": "Amazon"
                })

            return out if out else None

        except Exception as e:
            logging.error(f"Amazon parse error: {e}")
            return None