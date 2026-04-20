#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gst_builder.py - Build GSTR-1 JSON (Portal-Compliant)
Exact GST portal template format with only Meesho + Amazon
"""

import json
from typing import Dict, Any, List, Tuple
import logging
import pandas as pd
from collections import OrderedDict


class GSTBuilder:
    """Build portal-compliant GSTR-1 JSON."""
    
    def __init__(self):
        self.version = "GST3.1.6"

    def build_gstr1(self, parser_output: Dict[str, Any], gstin: str, fp: str) -> Dict[str, Any]:
        merged_rows = parser_output.get("merged_rows", [])
        if not merged_rows:
            return None
        
        b2cs = self._build_b2cs(merged_rows)
        clttx = self._build_clttx(merged_rows)
        
        output = OrderedDict()
        output["gstin"] = gstin.upper()
        output["fp"] = fp
        output["version"] = self.version
        output["hash"] = "hash"
        output["b2cs"] = b2cs
        output["supeco"] = {"clttx": clttx}
        output["doc_issue"] = {"doc_det": []}
        
        return dict(output)

    def _build_b2cs(self, merged_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        df = pd.DataFrame(merged_rows)
        grouped = df.groupby("pos", as_index=False).agg({
            "txval": "sum",
            "igst_amt": "sum",
            "cgst_amt": "sum",
            "sgst_amt": "sum"
        })
        
        b2cs = []
        for _, row in grouped.iterrows():
            pos = str(row["pos"]).zfill(2)
            txval = round(float(row["txval"]), 2)
            igst = round(float(row["igst_amt"]), 2)
            cgst = round(float(row["cgst_amt"]), 2)
            sgst = round(float(row["sgst_amt"]), 2)
            
            sply_ty = "INTRA" if (cgst > 0.01 or sgst > 0.01) else "INTER"
            
            item = OrderedDict()
            item["sply_ty"] = sply_ty
            item["rt"] = 3.0
            item["typ"] = "OE"
            item["pos"] = pos
            item["txval"] = txval
            
            if sply_ty == "INTER":
                if igst > 0.01:
                    item["iamt"] = igst
            else:
                if cgst > 0.01:
                    item["camt"] = cgst
                if sgst > 0.01:
                    item["samt"] = sgst
            
            item["csamt"] = 0
            b2cs.append(dict(item))
        
        return b2cs

    def _build_clttx(self, merged_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        df = pd.DataFrame(merged_rows)
        etins = sorted(df["supplier_etin"].unique())
        clttx = []
        
        for etin in etins:
            supplier_rows = df[df["supplier_etin"] == etin]
            
            suppval = round(float(supplier_rows["txval"].sum()), 2)
            igst = round(float(supplier_rows["igst_amt"].sum()), 2)
            cgst = round(float(supplier_rows["cgst_amt"].sum()), 2)
            sgst = round(float(supplier_rows["sgst_amt"].sum()), 2)
            
            item = OrderedDict()
            item["etin"] = str(etin)
            item["suppval"] = suppval
            item["igst"] = igst
            item["cgst"] = cgst
            item["sgst"] = sgst
            item["cess"] = 0
            item["flag"] = "N"
            
            clttx.append(dict(item))
        
        return clttx

    def save_json(self, output: Dict[str, Any], filepath: str) -> bool:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Save failed: {e}")
            return False

    def validate_output(self, output: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        required_keys = ["gstin", "fp", "version", "hash", "b2cs", "supeco", "doc_issue"]
        
        missing_keys = [k for k in required_keys if k not in output]
        if missing_keys:
            errors.append(f"Missing: {missing_keys}")
        
        extra_keys = [k for k in output.keys() if k not in required_keys]
        if extra_keys:
            errors.append(f"Extra keys: {extra_keys}")
        
        b2cs = output.get("b2cs", [])
        if not isinstance(b2cs, list):
            errors.append("b2cs not array")
        
        clttx = output.get("supeco", {}).get("clttx", [])
        if not isinstance(clttx, list):
            errors.append("clttx not array")
        
        return len(errors) == 0, errors
