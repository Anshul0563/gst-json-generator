#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parsers.py - GST GSTR-1 Parsers (Portal-Compliant)
Single source of truth: merged_rows list
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)

STATE_MAP = {
    "01": "01", "02": "02", "03": "03", "04": "04", "05": "05",
    "06": "06", "07": "07", "08": "08", "09": "09", "10": "10",
    "11": "11", "12": "12", "13": "13", "14": "14", "15": "15",
    "16": "16", "17": "17", "18": "18", "19": "19", "20": "20",
    "21": "21", "22": "22", "23": "23", "24": "24", "25": "25",
    "26": "26", "27": "27", "28": "28", "29": "29", "30": "30",
    "31": "31", "32": "32", "33": "33", "34": "34", "35": "35",
    "36": "36", "37": "37", "38": "38",
    "andhra pradesh": "28", "arunachal pradesh": "12", "assam": "18",
    "bihar": "10", "chhattisgarh": "22", "goa": "30", "gujarat": "24",
    "haryana": "06", "himachal pradesh": "02", "jharkhand": "20",
    "karnataka": "29", "kerala": "32", "madhya pradesh": "23",
    "maharashtra": "27", "manipur": "14", "meghalaya": "17", "mizoram": "15",
    "nagaland": "13", "odisha": "21", "punjab": "03", "rajasthan": "08",
    "sikkim": "11", "tamil nadu": "33", "telangana": "36", "tripura": "16",
    "uttar pradesh": "09", "uttarakhand": "05", "west bengal": "19",
    "delhi": "07", "chandigarh": "04", "puducherry": "34",
}


def safe(v) -> float:
    try:
        if pd.isna(v):
            return 0.0
        s = str(v).replace(",", "").replace("₹", "").strip()
        if not s or s.lower() in ["na", "n/a", "null", "none"]:
            return 0.0
        return round(float(s), 2)
    except (ValueError, TypeError, AttributeError):
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
        code = STATE_MAP.get(s.zfill(2))
        return code if code else None
    return None


class AutoMergeParser:
    """Parse Meesho and Amazon files only (no Flipkart)."""
    
    MEESHO_ETIN = "07AARCM9332R1CQ"
    AMAZON_ETIN = "07AAICA3918J1CV"

    def parse_files(self, files: List[str]) -> Optional[Dict[str, Any]]:
        merged_rows = []
        
        for f in files:
            fname = Path(f).name.lower()
            
            if "meesho" in fname or "tcs_sales" in fname or "tax_invoice" in fname:
                rows = self._parse_meesho(f)
                if rows:
                    merged_rows.extend(rows)
            elif "amazon" in fname or "mtr" in fname or "mtb" in fname:
                rows = self._parse_amazon(f)
                if rows:
                    merged_rows.extend(rows)
        
        if not merged_rows:
            return None
        
        df = pd.DataFrame(merged_rows)
        dup_cols = ["invoice_no", "pos", "txval", "supplier_etin"]
        df = df.drop_duplicates(subset=dup_cols, keep="first").reset_index(drop=True)
        
        return {"merged_rows": df.to_dict("records")}

    def _parse_meesho(self, f: str) -> Optional[List[Dict[str, Any]]]:
        try:
            if f.endswith((".xlsx", ".xls")):
                df = pd.read_excel(f, sheet_name=0)
            else:
                try:
                    df = pd.read_csv(f, encoding="utf-8")
                except:
                    df = pd.read_csv(f, encoding="latin1")
            
            if df.empty:
                return None
            
            cols = {str(c).strip().lower(): c for c in df.columns}
            inv_col = cols.get("sub_order_num", cols.get("order_id"))
            state_col = cols.get("end_customer_state_new", cols.get("state"))
            value_col = cols.get("total_taxable_sale_value", cols.get("taxable_value"))
            tax_col = cols.get("tax_amount", cols.get("tax"))
            
            if not (inv_col and state_col and value_col):
                return None
            
            is_return = "return" in f.lower() or "credit" in f.lower()
            out = []
            
            for i, row in df.iterrows():
                pos = gst_state(row.get(state_col))
                if not pos:
                    continue
                
                val = safe(row.get(value_col))
                tax_amt = safe(row.get(tax_col)) if tax_col else val * 0.03
                
                if val < 0.01 and tax_amt < 0.01:
                    continue
                
                if pos == "07":
                    igst, cgst, sgst = 0.0, round(tax_amt / 2, 2), round(tax_amt / 2, 2)
                else:
                    igst, cgst, sgst = round(tax_amt, 2), 0.0, 0.0
                
                out.append({
                    "invoice_no": str(row.get(inv_col, i)).strip(),
                    "pos": str(pos).zfill(2),
                    "txval": round(val, 2),
                    "igst_amt": igst,
                    "cgst_amt": cgst,
                    "sgst_amt": sgst,
                    "txn_type": "return" if is_return else "sale",
                    "supplier_etin": self.MEESHO_ETIN,
                    "supplier_name": "Meesho"
                })
            
            return out if out else None
        except Exception as e:
            logging.error(f"Meesho parse error: {e}")
            return None

    def _parse_amazon(self, f: str) -> Optional[List[Dict[str, Any]]]:
        try:
            try:
                df = pd.read_csv(f, encoding="utf-8")
            except:
                df = pd.read_csv(f, encoding="latin1")
            
            if df.empty:
                return None
            
            cols = {str(c).strip().lower(): c for c in df.columns}
            state_col = cols.get("ship_to_state", cols.get("destination_state"))
            value_col = cols.get("tax_exclusive_gross", cols.get("transaction_amount"))
            igst_col = cols.get("igst_tax", cols.get("igst"))
            cgst_col = cols.get("cgst_tax", cols.get("cgst"))
            sgst_col = cols.get("sgst_tax", cols.get("sgst"))
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
                
                txn_type_val = "shipment"
                if txn_col:
                    txn_type_val = str(row.get(txn_col, "shipment")).strip().lower()
                
                is_return = (
                    txn_type_val in ["refund", "cancel", "cancelled", "return", "reversal"]
                    or val < 0
                )
                
                if val < 0.01 and (igst + cgst + sgst) < 0.01:
                    continue
                
                out.append({
                    "invoice_no": str(row.get(inv_col, i)).strip() if inv_col else str(i),
                    "pos": str(pos).zfill(2),
                    "txval": round(abs(val), 2),
                    "igst_amt": round(igst, 2),
                    "cgst_amt": round(cgst, 2),
                    "sgst_amt": round(sgst, 2),
                    "txn_type": "return" if is_return else "sale",
                    "supplier_etin": self.AMAZON_ETIN,
                    "supplier_name": "Amazon"
                })
            
            return out if out else None
        except Exception as e:
            logging.error(f"Amazon parse error: {e}")
            return None
