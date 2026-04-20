#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parsers.py - Production GST Parsers for Meesho, Amazon, Flipkart
Exports: MeeshoParser, AmazonParser, AutoMergeParser
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

STATE_MAP = {
    # Official GST State Codes
    "01": "01", "02": "02", "03": "03", "04": "04", "05": "05", "06": "06", "07": "07", "08": "08",
    "09": "09", "10": "10", "11": "11", "12": "12", "13": "13", "14": "14", "16": "16", "17": "17",
    "18": "18", "19": "19", "20": "20", "21": "21", "22": "22", "23": "23", "24": "24", "25": "25",
    "26": "26", "27": "27", "28": "28", "29": "29", "30": "30", "31": "31", "32": "32", "33": "33",
    "34": "34", "35": "35", "36": "36", "37": "37", "38": "38",
    # State aliases
    "delhi": "07", "new delhi": "07",
    "uttar pradesh": "09", "up": "09", "noida": "09", "ghaziabad": "09",
    "odisha": "21", "orissa": "21",
    "gujarat": "24",
    "maharashtra": "27", "mumbai": "27", "pune": "27",
    "andhra pradesh": "28",
    "karnataka": "29", "bangalore": "29", "bengaluru": "29",
    "tamil nadu": "33", "chennai": "33",
    "telangana": "36", "hyderabad": "36",
    "haryana": "06", "gurgaon": "06", "gururgam": "06",
    "west bengal": "19", "kolkata": "19",
    "rajasthan": "08", "bihar": "10", "meghalaya": "17", "himachal pradesh": "02",
    "punjab": "03"
}

def safe_float(v: Any) -> float:
    "Safely convert to float, handle NaN/None/empty as 0."
    if pd.isna(v) or v is None:
        return 0.0
    try:
        return float(str(v).replace(',', '').replace('₹', '').replace('Rs.', '').strip() or 0)
    except (ValueError, TypeError):
        return 0.0

def get_gst_state(state: Any) -> Optional[str]:
    "Get GST state code from state name or code."
    if not state:
        return None
    s = str(state).strip().upper()
    code = STATE_MAP.get(s.lower(), None)
    if code:
        return code.zfill(2)
    if s.isdigit() and 1 <= int(s) <= 38:
        return s.zfill(2)
    return None

def get_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    "Find first matching column (case-insensitive)."
    cols_lower = {col.lower(): col for col in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None

class BaseParser:
    PLATFORM: str = "Base"
    ETIN: str = ""

    def parse_files(self, files: List[str], seller_gstin: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        all_rows = []
        for f in files:
            rows = self.read_one(f)
            all_rows.extend(rows)
        
        deduped = self.deduplicate_rows(all_rows)
        return {"merged_rows": deduped}

    def read_one(self, filepath: str) -> List[Dict[str, Any]]:
        return []

    def deduplicate_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for row in rows:
            key = (
                str(row.get('invoice_no', '')),
                str(row.get('pos', '')),
                str(row.get('txval', 0)),
                str(row.get('supplier_etin', ''))
            )
            if key not in seen:
                seen.add(key)
                if self._is_zero_row(row):
                    continue
                deduped.append(row)
        return deduped

    def _is_zero_row(self, row: Dict[str, Any]) -> bool:
        txval = abs(row.get('txval', 0)) < 0.01
        igst = abs(row.get('igst_amt', 0)) < 0.01
        cgst = abs(row.get('cgst_amt', 0)) < 0.01
        sgst = abs(row.get('sgst_amt', 0)) < 0.01
        return txval and igst and cgst and sgst

    def _read_df(self, filepath: str) -> Optional[pd.DataFrame]:
        path = Path(filepath)
        encodings = ['utf-8', 'latin1']
        
        if path.suffix.lower() in ['.xlsx', '.xls']:
            try:
                return pd.read_excel(filepath, engine='openpyxl')
            except Exception:
                return None
        
        for enc in encodings:
            try:
                return pd.read_csv(filepath, encoding=enc)
            except Exception:
                continue
        return None

class MeeshoParser(BaseParser):
    PLATFORM = "Meesho"
    ETIN = "07AARCM9332R1CQ"

    def read_one(self, filepath: str) -> List[Dict[str, Any]]:
        name = Path(filepath).name.lower()
        if 'flipkart' in name:
            return []
        
        if not any(x in name for x in ['meesho', 'tcs', 'sales', 'return']):
            return []
        
        df = self._read_df(filepath)
        if df is None or df.empty:
            return []
        
        cols_lower = {c.lower(): c for c in df.columns}
        
        inv_candidates = ['sub_order_num', 'order_id', 'invoice_number', 'document_no']
        state_candidates = ['end_customer_state_new', 'state', 'destination_state']
        txval_candidates = ['total_taxable_sale_value', 'taxable_value', 'amount', 'transaction_amount']
        tax_candidates = ['tax_amount']
        
        inv_col = get_col(df, inv_candidates)
        state_col = get_col(df, state_candidates)
        txval_col = get_col(df, txval_candidates)
        tax_col = get_col(df, tax_candidates)
        
        if not txval_col:
            return []
        
        rows = []
        for _, row in df.iterrows():
            pos = get_gst_state(row.get(state_col))
            if not pos:
                continue
            
            txval = safe_float(row.get(txval_col))
            if tax_col is not None and pd.notna(row.get(tax_col)):
                total_tax = safe_float(row.get(tax_col))
            else:
                total_tax = abs(txval) * 0.03
            
            # Tax split: Delhi intra -> CGST/SGST, else IGST
            if pos == '07':
                igst_amt = 0.0
                cgst_amt = round(total_tax / 2, 2) * (1 if txval >= 0 else -1)
                sgst_amt = round(total_tax / 2, 2) * (1 if txval >= 0 else -1)
            else:
                igst_amt = total_tax * (1 if txval >= 0 else -1)
                cgst_amt = 0.0
                sgst_amt = 0.0
            
            rows.append({
                'invoice_no': str(row.get(inv_col, '')),
                'pos': pos,
                'txval': round(txval, 2),
                'igst_amt': round(igst_amt, 2),
                'cgst_amt': round(cgst_amt, 2),
                'sgst_amt': round(sgst_amt, 2),
                'supplier_etin': self.ETIN,
            })
        return rows

class AmazonParser(BaseParser):
    PLATFORM = "Amazon"
    ETIN = "07AAICA3918J1CV"

    def read_one(self, filepath: str) -> List[Dict[str, Any]]:
        name = Path(filepath).name.lower()
        if 'flipkart' in name:
            return []
        
        if not any(x in name for x in ['amazon', 'mtr']) or not Path(filepath).suffix.lower() == '.csv':
            return []
        
        df = self._read_df(filepath)
        if df is None or df.empty:
            return []
        
        state_candidates = ['ship_to_state', 'state', 'destination_state']
        txval_candidates = ['tax_exclusive_gross', 'amount', 'transaction_amount']
        igst_candidates = ['igst_tax', 'igst']
        cgst_candidates = ['cgst_tax', 'cgst']
        sgst_candidates = ['sgst_tax', 'sgst']
        utgst_candidates = ['utgst_tax', 'utgst']
        inv_candidates = ['invoice_number', 'order_id', 'document_no']
        
        state_col = get_col(df, state_candidates)
        txval_col = get_col(df, txval_candidates)
        igst_col = get_col(df, igst_candidates)
        cgst_col = get_col(df, cgst_candidates)
        sgst_col = get_col(df, sgst_candidates)
        utgst_col = get_col(df, utgst_candidates)
        inv_col = get_col(df, inv_candidates)
        
        if not txval_col or not state_col:
            return []
        
        rows = []
        for _, row in df.iterrows():
            pos = get_gst_state(row.get(state_col))
            if not pos:
                continue
            
            txval = safe_float(row.get(txval_col))
            igst_amt = safe_float(row.get(igst_col, 0))
            cgst_amt = safe_float(row.get(cgst_col, 0))
            sgst_amt = safe_float(row.get(sgst_col, 0))
            if utgst_col and pd.notna(row.get(utgst_col)):
                sgst_amt += safe_float(row.get(utgst_col))
            
            rows.append({
                'invoice_no': str(row.get(inv_col, '')),
                'pos': pos,
                'txval': round(txval, 2),
                'igst_amt': round(igst_amt, 2),
                'cgst_amt': round(cgst_amt, 2),
                'sgst_amt': round(sgst_amt, 2),
                'supplier_etin': self.ETIN,
            })
        return rows

class AutoMergeParser(BaseParser):
    PLATFORM = "AutoMerge"

    def parse_files(self, files: List[str], seller_gstin: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        all_rows = []
        meesho_parser = MeeshoParser()
        amazon_parser = AmazonParser()
        
        for f in files:
            all_rows.extend(meesho_parser.read_one(f))
            all_rows.extend(amazon_parser.read_one(f))
        
        deduped = self.deduplicate_rows(all_rows)
        return {"merged_rows": deduped}

# Exact exports required
__all__ = ['MeeshoParser', 'AmazonParser', 'AutoMergeParser']

