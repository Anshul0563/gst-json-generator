#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parsers.py - Production-Grade GST GSTR-1 Parsers
SINGLE SOURCE OF TRUTH: merged_rows list

Output structure from all parsers:
{
    "merged_rows": [
        {
            "invoice_no": str,
            "pos": str (01-38),
            "txval": float,
            "igst_amt": float,
            "cgst_amt": float,
            "sgst_amt": float,
            "txn_type": str ("sale" | "return"),
            "supplier_etin": str (07AARCM9332R1CQ | 07AAICA3918J1CV),
            "supplier_name": str (Meesho | Amazon)
        },
        ...
    ]
}

gst_builder.py generates from merged_rows:
- b2cs: group by POS
- summary: sum all txval, igst_amt, cgst_amt, sgst_amt
- clttx: group by supplier_etin
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any, Set
import logging

# =====================================================
# STATE MAPPING
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
    "andhra pradesh": "28", "arunachal pradesh": "12", "assam": "18",
    "bihar": "10", "chhattisgarh": "22", "goa": "30", "gujarat": "24",
    "haryana": "06", "himachal pradesh": "02", "jharkhand": "20",
    "karnataka": "29", "kerala": "32", "madhya pradesh": "23",
    "maharashtra": "27", "manipur": "14", "meghalaya": "17", "mizoram": "15",
    "nagaland": "13", "odisha": "21", "punjab": "03", "rajasthan": "08",
    "sikkim": "11", "tamil nadu": "33", "telangana": "36", "tripura": "16",
    "uttar pradesh": "09", "uttarakhand": "05", "west bengal": "19",
    "delhi": "07", "jammu kashmir": "01", "ladakh": "37", "puducherry": "34",
    "andaman nicobar": "35", "chandigarh": "04", "dadra nagar": "25", "daman diu": "26", "lakshadweep": "31",
    "noida": "09", "ghaziabad": "09", "greater noida": "09",
    "mumbai": "27", "pune": "27", "thane": "27", "nagpur": "27",
    "bangalore": "29", "bengaluru": "29", "mysore": "29",
    "hyderabad": "36", "secunderabad": "36", "vizag": "28", "visakhapatnam": "28",
    "chennai": "33", "coimbatore": "33", "salem": "33",
    "kolkata": "19", "darjeeling": "19", "asansol": "19",
    "gurgaon": "06", "gurugram": "06", "faridabad": "06", "new delhi": "07",
    "jaipur": "08", "udaipur": "08", "jodhpur": "08",
    "ahmedabad": "24", "surat": "24", "vadodara": "24",
    "lucknow": "09", "kanpur": "09", "varanasi": "09",
    "indore": "23", "bhopal": "23", "jabalpur": "23",
    "kochi": "32", "thiruvananthapuram": "32", "thrissur": "32", "ludhiana": "03",
    "orissa": "21", "odisha": "21",
}


def safe(v) -> float:
    """Safely convert to float."""
    try:
        if pd.isna(v):
            return 0.0
        s = str(v).replace(",", "").replace("₹", "").strip()
        return float(s) if s and s.lower() not in ["na", "n/a", "null", "none"] else 0.0
    except (ValueError, TypeError, AttributeError):
        return 0.0


def gst_state(x: Optional[str]) -> Optional[str]:
    """Convert state name/code to GST state code (01-38)."""
    if x is None:
        return None
    s = str(x).strip().lower()
    return STATE_MAP.get(s, STATE_MAP.get(s.zfill(2)) if s.isdigit() else None)


# =====================================================
# AUTO MERGE PARSER (Main Entry Point)
# =====================================================

class AutoMergeParser:
    """Parse Meesho, Amazon, and other files into single merged_rows list."""
    
    MEESHO_ETIN = "07AARCM9332R1CQ"
    AMAZON_ETIN = "07AAICA3918J1CV"

    def parse_files(self, files: List[str]) -> Optional[Dict[str, Any]]:
        """Parse multiple files and return merged_rows."""
        merged_rows = []
        
        # Parse each file
        for f in files:
            name = Path(f).name.lower()
            
            # Try Meesho
            if "meesho" in name or "tcs_sales" in name or "tax_invoice" in name:
                rows = self._parse_meesho(f)
                if rows:
                    merged_rows.extend(rows)
                    logging.info(f"Meesho: {len(rows)} rows from {Path(f).name}")
            
            # Try Amazon
            elif "amazon" in name or "mtr" in name or "settlement" in name:
                rows = self._parse_amazon(f)
                if rows:
                    merged_rows.extend(rows)
                    logging.info(f"Amazon: {len(rows)} rows from {Path(f).name}")
        
        if not merged_rows:
            logging.info("No data parsed from any files")
            return None
        
        # Deduplicate
        df = pd.DataFrame(merged_rows)
        dup_cols = ["invoice_no", "pos", "txval", "igst_amt", "cgst_amt", "sgst_amt", "txn_type", "supplier_etin"]
        df = df.drop_duplicates(subset=dup_cols).reset_index(drop=True)
        
        merged_rows = df.to_dict("records")
        
        logging.info(f"Total merged rows: {len(merged_rows)}")
        
        return {"merged_rows": merged_rows}

    def _parse_meesho(self, f: str) -> Optional[List[Dict[str, Any]]]:
        """Parse Meesho file."""
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
                
                # Seller state 07 (Delhi) for Meesho
                if pos == "07":
                    ig, cg, sg = 0.0, round(tax_amt / 2, 2), round(tax_amt / 2, 2)
                else:
                    ig, cg, sg = round(tax_amt, 2), 0.0, 0.0
                
                if abs(val) < 0.01 and abs(ig) + abs(cg) + abs(sg) < 0.01:
                    continue
                
                out.append({
                    "invoice_no": str(row.get(inv_col, i)).strip(),
                    "pos": str(pos).zfill(2),
                    "txval": round(abs(val), 2),
                    "igst_amt": round(abs(ig), 2),
                    "cgst_amt": round(abs(cg), 2),
                    "sgst_amt": round(abs(sg), 2),
                    "txn_type": "return" if is_return else "sale",
                    "supplier_etin": self.MEESHO_ETIN,
                    "supplier_name": "Meesho"
                })
            
            return out if out else None
        except Exception as e:
            logging.error(f"Meesho parse error: {e}")
            return None

    def _parse_amazon(self, f: str) -> Optional[List[Dict[str, Any]]]:
        """Parse Amazon/MTR file."""
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
            
            if not (state_col and value_col):
                return None
            
            out = []
            
            for i, row in df.iterrows():
                pos = gst_state(row.get(state_col))
                if not pos:
                    continue
                
                val = safe(row.get(value_col))
                ig = safe(row.get(igst_col)) if igst_col else 0.0
                cg = safe(row.get(cgst_col)) if cgst_col else 0.0
                sg = safe(row.get(sgst_col)) if sgst_col else 0.0
                
                utgst_col = cols.get("utgst_tax", cols.get("utgst", cols.get("ut_tax")))
                if utgst_col:
                    sg += safe(row.get(utgst_col))
                
                txn_col = cols.get("transaction_type", cols.get("type", cols.get("document_type")))
                txn_type_val = str(row.get(txn_col, "shipment")).strip().lower() if txn_col else "shipment"
                is_return = txn_type_val in ["refund", "cancel", "cancelled", "return", "reversal"] or val < 0
                
                if abs(val) < 0.01 and abs(ig) + abs(cg) + abs(sg) < 0.01:
                    continue
                
                out.append({
                    "invoice_no": str(row.get(inv_col, i)).strip() if inv_col else str(i),
                    "pos": str(pos).zfill(2),
                    "txval": round(abs(val), 2),
                    "igst_amt": round(abs(ig), 2),
                    "cgst_amt": round(abs(cg), 2),
                    "sgst_amt": round(abs(sg), 2),
                    "txn_type": "return" if is_return else "sale",
                    "supplier_etin": self.AMAZON_ETIN,
                    "supplier_name": "Amazon"
                })
            
            return out if out else None
        except Exception as e:
            logging.error(f"Amazon parse error: {e}")
            return None
