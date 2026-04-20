#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parsers.py - Complete Production-Grade GST GSTR-1 Parsers
Supports Meesho, Amazon, and Auto-Merge parsing with comprehensive error handling.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

# =====================================================
# HELPERS
# =====================================================

def safe(v) -> float:
    """Safely convert value to float, handling various formats."""
    try:
        if pd.isna(v):
            return 0.0
        s = str(v).replace(",", "").replace("₹", "").strip()
        if s == "" or s.lower() in ["na", "n/a", "null", "none"]:
            return 0.0
        return float(s)
    except (ValueError, TypeError, AttributeError):
        return 0.0


# Complete State mapping with all 38 Indian states
STATE_MAP = {
    # State codes
    "01": "01", "02": "02", "03": "03", "04": "04", "05": "05",
    "06": "06", "07": "07", "08": "08", "09": "09", "10": "10",
    "11": "11", "12": "12", "13": "13", "14": "14", "15": "15",
    "16": "16", "17": "17", "18": "18", "19": "19", "20": "20",
    "21": "21", "22": "22", "23": "23", "24": "24", "25": "25",
    "26": "26", "27": "27", "28": "28", "29": "29", "30": "30",
    "31": "31", "32": "32", "33": "33", "34": "34", "35": "35",
    "36": "36", "37": "37", "38": "38",
    
    # State names
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
    
    # Common city aliases
    "noida": "09", "ghaziabad": "09", "greater noida": "09",
    "mumbai": "27", "pune": "27", "thane": "27", "nagpur": "27",
    "bangalore": "29", "bengaluru": "29", "mysore": "29",
    "hyderabad": "36", "secunderabad": "36", "vizag": "28", "visakhapatnam": "28",
    "chennai": "33", "coimbatore": "33", "salem": "33",
    "kolkata": "19", "darjeeling": "19", "asansol": "19",
    "gurgaon": "06", "gurugram": "06", "faridabad": "06",
    "new delhi": "07",
    "jaipur": "08", "udaipur": "08", "jodhpur": "08",
    "ahmedabad": "24", "surat": "24", "vadodara": "24",
    "lucknow": "09", "kanpur": "09", "varanasi": "09",
    "indore": "23", "bhopal": "23", "jabalpur": "23",
    "kochi": "32", "thiruvananthapuram": "32", "thrissur": "32",
    "ludhiana": "03",
}


def gst_state(x: Optional[str]) -> Optional[str]:
    """
    Convert state name/code to GST state code.
    Returns state code (01-38) or None if not found.
    """
    if x is None:
        return None
    
    s = str(x).strip().lower()
    
    # Check exact match
    if s in STATE_MAP:
        return STATE_MAP[s]
    
    # Check if numeric
    if s.isdigit():
        s = s.zfill(2)
        if s in STATE_MAP:
            return STATE_MAP[s]
    
    return None


# =====================================================
# BASE PARSER
# =====================================================

class BaseParser:
    """Base class for all file parsers with common logic."""
    
    PLATFORM = "Base"
    ETIN = ""

    def parse_files(self, files: List[str], seller_gstin: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Parse multiple files and return combined data."""
        rows = []
        
        for f in files:
            try:
                data = self.read_one(f)
                if data:
                    rows.extend(data)
            except Exception as e:
                logging.warning(f"{self.PLATFORM} error in {Path(f).name}: {e}")
        
        if not rows:
            logging.info(f"{self.PLATFORM}: No data parsed")
            return None
        
        return self.finalize(rows)

    def read_one(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Read and parse a single file. Override in subclasses."""
        return []

    def finalize(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Finalize parsed data with deduplication and aggregation."""
        if not rows:
            return None
        
        df = pd.DataFrame(rows)
        
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Deduplicate by key columns
        dedup_cols = ["invoice_no", "pos", "taxable_value", "igst", "cgst", "sgst", "txn_type"]
        df = df.drop_duplicates(subset=dedup_cols).reset_index(drop=True)
        
        # Group by POS (Place of Supply)
        grp = df.groupby("pos", as_index=False)[
            ["taxable_value", "igst", "cgst", "sgst"]
        ].sum().round(2)
        
        # Separate sales and returns
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
                    "invoice_no": str(r["invoice_no"]).strip(),
                    "pos": str(r["pos"]).zfill(2),
                    "txval": round(float(r["taxable_value"]), 2),
                    "igst_amt": round(float(r["igst"]), 2),
                    "cgst_amt": round(float(r["cgst"]), 2),
                    "sgst_amt": round(float(r["sgst"]), 2),
                    "txn_type": "sale",
                }
                for _, r in sales.iterrows()
            ],
            "credit_docs": [
                {
                    "invoice_no": str(r["invoice_no"]).strip(),
                    "pos": str(r["pos"]).zfill(2),
                    "txval": abs(round(float(r["taxable_value"]), 2)),
                    "igst_amt": abs(round(float(r["igst"]), 2)),
                    "cgst_amt": abs(round(float(r["cgst"]), 2)),
                    "sgst_amt": abs(round(float(r["sgst"]), 2)),
                    "txn_type": "return",
                }
                for _, r in returns.iterrows()
            ],
        }


# =====================================================
# MEESHO PARSER
# =====================================================

class MeeshoParser(BaseParser):
    """Parser for Meesho export files."""
    
    PLATFORM = "Meesho"
    ETIN = "07AARCM9332R1CQ"

    def read_one(self, f: str) -> Optional[List[Dict[str, Any]]]:
        """Parse Meesho file."""
        name = Path(f).name.lower()
        
        # Check if file is Meesho-related
        if not ("meesho" in name or "tcs_sales" in name or "tax_invoice" in name):
            return None
        
        try:
            # Read Excel or CSV
            if f.endswith((".xlsx", ".xls")):
                df = pd.read_excel(f, sheet_name=0)
            else:
                try:
                    df = pd.read_csv(f, encoding="utf-8")
                except:
                    df = pd.read_csv(f, encoding="latin1")
            
            if df.empty:
                return None
            
            # Create case-insensitive column mapping
            cols = {str(c).strip().lower(): c for c in df.columns}
            
            # Find required columns
            inv_col = cols.get("sub_order_num", cols.get("order_id", cols.get("invoice_number")))
            state_col = cols.get("end_customer_state_new", cols.get("state", cols.get("customer_state")))
            value_col = cols.get("total_taxable_sale_value", cols.get("taxable_value", cols.get("amount")))
            tax_col = cols.get("tax_amount", cols.get("tax", cols.get("gst")))
            
            if not all([inv_col, state_col, value_col]):
                logging.warning(f"Meesho: Missing required columns in {Path(f).name}")
                return None
            
            is_return = "return" in name or "credit" in name
            out = []
            
            for i, row in df.iterrows():
                # Get state code
                pos = gst_state(row.get(state_col))
                if not pos:
                    continue
                
                # Get taxable value
                val = safe(row.get(value_col))
                
                # Get tax (calculate if needed)
                if tax_col:
                    tax_amt = safe(row.get(tax_col))
                else:
                    tax_amt = val * 0.03
                
                # Calculate CGST/SGST/IGST based on POS
                if pos == "07":  # Within state (intra)
                    ig, cg, sg = 0.0, round(tax_amt / 2, 2), round(tax_amt / 2, 2)
                else:  # Inter-state
                    ig, cg, sg = round(tax_amt, 2), 0.0, 0.0
                
                # Negate values for returns
                if is_return:
                    val = -abs(val)
                    ig = -abs(ig)
                    cg = -abs(cg)
                    sg = -abs(sg)
                
                # Skip zero/negligible rows
                if abs(val) < 0.01 and abs(ig) + abs(cg) + abs(sg) < 0.01:
                    continue
                
                out.append({
                    "invoice_no": str(row.get(inv_col, i)).strip(),
                    "pos": str(pos).zfill(2),
                    "taxable_value": round(val, 2),
                    "igst": round(ig, 2),
                    "cgst": round(cg, 2),
                    "sgst": round(sg, 2),
                    "txn_type": "return" if is_return else "sale",
                })
            
            return out if out else None
            
        except Exception as e:
            logging.error(f"Meesho parse error: {e}")
            return None


# =====================================================
# AMAZON PARSER
# =====================================================

class AmazonParser(BaseParser):
    """Parser for Amazon/MTR CSV files."""
    
    PLATFORM = "Amazon"
    ETIN = "07AAICA3918J1CV"

    def read_one(self, f: str) -> Optional[List[Dict[str, Any]]]:
        """Parse Amazon/MTR file."""
        name = Path(f).name.lower()
        
        # Check if file looks like Amazon/MTR data
        if not ("amazon" in name or "mtr" in name or "settlement" in name or name.endswith(".csv")):
            return None
        
        try:
            # Try UTF-8 first, fallback to latin1
            try:
                df = pd.read_csv(f, encoding="utf-8")
            except:
                df = pd.read_csv(f, encoding="latin1")
            
            if df.empty:
                return None
            
            # Create case-insensitive column mapping
            cols = {str(c).strip().lower(): c for c in df.columns}
            
            # Find required columns
            state_col = cols.get("ship_to_state", cols.get("state", cols.get("destination_state")))
            value_col = cols.get("tax_exclusive_gross", cols.get("amount", cols.get("transaction_amount")))
            igst_col = cols.get("igst_tax", cols.get("igst"))
            cgst_col = cols.get("cgst_tax", cols.get("cgst"))
            sgst_col = cols.get("sgst_tax", cols.get("sgst"))
            utgst_col = cols.get("utgst_tax", cols.get("utgst", cols.get("ut_tax")))
            txn_col = cols.get("transaction_type", cols.get("type", cols.get("document_type")))
            inv_col = cols.get("invoice_number", cols.get("order_id", cols.get("document_no")))
            
            if not all([state_col, value_col]):
                logging.warning(f"Amazon: Missing required columns in {Path(f).name}")
                return None
            
            out = []
            
            for i, row in df.iterrows():
                # Get state code
                pos = gst_state(row.get(state_col))
                if not pos:
                    continue
                
                # Get values
                val = safe(row.get(value_col))
                ig = safe(row.get(igst_col)) if igst_col else 0.0
                cg = safe(row.get(cgst_col)) if cgst_col else 0.0
                sg = safe(row.get(sgst_col)) if sgst_col else 0.0
                ut = safe(row.get(utgst_col)) if utgst_col else 0.0
                
                sg += ut  # Add UTGST to SGST
                
                # Check transaction type
                txn_type = str(row.get(txn_col, "shipment")).strip().lower()
                is_return = txn_type in ["refund", "cancel", "cancelled", "return"] or val < 0
                
                # Negate for returns
                if is_return:
                    val = -abs(val)
                    ig = -abs(ig)
                    cg = -abs(cg)
                    sg = -abs(sg)
                
                # Skip zero/negligible rows
                if abs(val) < 0.01 and abs(ig) + abs(cg) + abs(sg) < 0.01:
                    continue
                
                out.append({
                    "invoice_no": str(row.get(inv_col, i)).strip(),
                    "pos": str(pos).zfill(2),
                    "taxable_value": round(val, 2),
                    "igst": round(ig, 2),
                    "cgst": round(cg, 2),
                    "sgst": round(sg, 2),
                    "txn_type": "return" if is_return else "sale",
                })
            
            return out if out else None
            
        except Exception as e:
            logging.error(f"Amazon parse error: {e}")
            return None


# =====================================================
# AUTO MERGE PARSER
# =====================================================

class AutoMergeParser:
    """Auto-detect and merge multiple parser formats."""
    
    PLATFORM = "Auto Merge"

    def parse_files(self, files: List[str], seller_gstin: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Parse files from multiple sources and merge results."""
        
        parsers = [
            MeeshoParser(),
            AmazonParser(),
        ]
        
        all_rows = []
        supplier_data = {}
        
        # Parse with each parser
        for parser in parsers:
            result = parser.parse_files(files, seller_gstin)
            if result:
                supplier_data[parser.ETIN] = result
                all_rows.extend(result.get("invoice_docs", []))
                all_rows.extend(result.get("credit_docs", []))
        
        if not all_rows:
            logging.info("AutoMerge: No data parsed from any source")
            return None
        
        # Merge and finalize
        return self._merge_results(all_rows, supplier_data)

    def _merge_results(self, rows: List[Dict[str, Any]], supplier_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results from multiple parsers."""
        
        # Create normalized DataFrame for grouping
        norm_rows = []
        for r in rows:
            norm_rows.append({
                "invoice_no": r["invoice_no"],
                "pos": str(r["pos"]).zfill(2),
                "taxable_value": r["txval"],
                "igst": r["igst_amt"],
                "cgst": r["cgst_amt"],
                "sgst": r["sgst_amt"],
                "txn_type": r["txn_type"],
            })
        
        df = pd.DataFrame(norm_rows)
        
        # Deduplicate
        dedup_cols = ["invoice_no", "pos", "taxable_value", "igst", "cgst", "sgst", "txn_type"]
        df = df.drop_duplicates(subset=dedup_cols).reset_index(drop=True)
        
        # Group by POS
        grp = df.groupby("pos", as_index=False)[
            ["taxable_value", "igst", "cgst", "sgst"]
        ].sum().round(2)
        
        # Build clttx (supplier consolidated tax)
        clttx = []
        for etin, data in supplier_data.items():
            summary = data.get("summary", {})
            clttx.append({
                "etin": etin,
                "suppval": round(summary.get("total_taxable", 0), 2),
                "igst": round(summary.get("total_igst", 0), 2),
                "cgst": round(summary.get("total_cgst", 0), 2),
                "sgst": round(summary.get("total_sgst", 0), 2),
                "cess": 0,
                "flag": "N"
            })
        
        return {
            "summary": {
                "rows": grp.to_dict("records"),
                "total_taxable": round(df["taxable_value"].sum(), 2),
                "total_igst": round(df["igst"].sum(), 2),
                "total_cgst": round(df["cgst"].sum(), 2),
                "total_sgst": round(df["sgst"].sum(), 2),
            },
            "clttx": clttx,
            "doc_issue": {
                "doc_det": [
                    {
                        "doc_num": 1,
                        "doc_typ": "Invoices for outward supply",
                        "docs": []
                    },
                    {
                        "doc_num": 5,
                        "doc_typ": "Credit Note",
                        "docs": []
                    }
                ]
            },
            "all_docs": rows,
            "invoice_docs": [r for r in rows if r["txn_type"] == "sale"],
            "credit_docs": [r for r in rows if r["txn_type"] == "return"],
        }
