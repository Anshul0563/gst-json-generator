#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gst_builder.py - Build GSTR-1 JSON from merged_rows (Portal-Compliant)

SINGLE SOURCE OF TRUTH: merged_rows from parser

Pipeline:
1. Receive merged_rows from parser
2. Generate b2cs: group by POS, sum taxes
3. Generate clttx: group by supplier_etin, sum taxes
4. Return PORTAL-COMPLIANT JSON structure

ROOT KEY ORDER (MANDATORY):
  gstin → fp → version → hash → b2cs → supeco → doc_issue

IMPORTANT: NO SUMMARY SECTION IN OUTPUT
The portal template does NOT include a summary section in the JSON.
"""

import json
from typing import Dict, Any, List, Tuple
from pathlib import Path
import logging
import pandas as pd
from collections import OrderedDict


class GSTBuilder:
    """Build GSTR-1 JSON from merged_rows (Portal-Compliant)."""
    
    def __init__(self):
        self.version = "GST3.1.6"

    def build_gstr1(self, parser_output: Dict[str, Any], gstin: str, fp: str) -> Dict[str, Any]:
        """
        Build complete GSTR-1 JSON (portal-compliant format).
        
        Args:
            parser_output: {"merged_rows": [...]} from AutoMergeParser
            gstin: Seller GSTIN
            fp: Filing period (MMYYYY)
        
        Returns:
            Complete GSTR-1 JSON structure with exact portal format
            
        ROOT KEY ORDER: gstin → fp → version → hash → b2cs → supeco → doc_issue
        NO SUMMARY SECTION
        """
        merged_rows = parser_output.get("merged_rows", [])
        
        if not merged_rows:
            logging.warning("⚠ No merged rows provided")
            return None
        
        # Build b2cs from merged_rows
        b2cs = self._build_b2cs(merged_rows)
        
        # Build clttx from merged_rows
        clttx = self._build_clttx(merged_rows)
        
        # Build doc_issue (empty doc_det)
        doc_issue = {
            "doc_det": []
        }
        
        # Log summary
        logging.info(f"✓ B2CS entries: {len(b2cs)}")
        logging.info(f"✓ CLTTX entries: {len(clttx)}")
        
        for c in clttx:
            logging.info(f"  {c['etin']}: ₹{c['suppval']}")
        
        # Build output with EXACT root key order
        # Using OrderedDict to ensure order is preserved in Python < 3.7
        output = OrderedDict()
        output["gstin"] = gstin.upper()
        output["fp"] = fp
        output["version"] = self.version
        output["hash"] = "hash"
        output["b2cs"] = b2cs
        output["supeco"] = {"clttx": clttx}
        output["doc_issue"] = doc_issue
        
        return dict(output)

    def _build_b2cs(self, merged_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build b2cs array by grouping merged_rows by POS.
        
        Schema:
        {
          "sply_ty": "INTER" or "INTRA",
          "rt": 3.0,
          "typ": "OE",
          "pos": "01" to "38",
          "txval": number,
          "iamt": number (for INTER),
          "camt": number (for INTRA),
          "samt": number (for INTRA),
          "csamt": 0
        }
        """
        df = pd.DataFrame(merged_rows)
        
        # Group by POS and aggregate
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
            
            # Determine supply type
            if cgst > 0.01 or sgst > 0.01:
                sply_ty = "INTRA"
            else:
                sply_ty = "INTER"
            
            # Build item with correct key order
            item = OrderedDict()
            item["sply_ty"] = sply_ty
            item["rt"] = 3.0
            item["typ"] = "OE"
            item["pos"] = pos
            item["txval"] = txval
            item["csamt"] = 0
            
            # Add tax fields based on type
            if sply_ty == "INTER":
                if igst > 0.01:
                    item["iamt"] = igst
            else:  # INTRA
                if cgst > 0.01:
                    item["camt"] = cgst
                if sgst > 0.01:
                    item["samt"] = sgst
            
            b2cs.append(dict(item))
        
        return b2cs

    def _build_clttx(self, merged_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build clttx by grouping merged_rows by supplier_etin.
        
        Schema:
        {
          "etin": "string",
          "suppval": number,
          "igst": number,
          "cgst": number,
          "sgst": number,
          "cess": 0,
          "flag": "N"
        }
        """
        df = pd.DataFrame(merged_rows)
        
        # Get unique ETINs from data (sorted for consistency)
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
        """
        Save GSTR-1 JSON to file with UTF-8 encoding.
        
        Args:
            output: GSTR-1 dictionary
            filepath: Output file path
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            logging.info(f"✓ JSON saved: {filepath}")
            return True
        except Exception as e:
            logging.error(f"✗ Failed to save JSON: {e}")
            return False

    def validate_output(self, output: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate GSTR-1 output against schema."""
        errors = []
        
        # Check root keys
        required_keys = ["gstin", "fp", "version", "hash", "b2cs", "supeco", "doc_issue"]
        missing_keys = [k for k in required_keys if k not in output]
        if missing_keys:
            errors.append(f"Missing keys: {', '.join(missing_keys)}")
        
        # Check no extra keys (only allowed keys)
        allowed_keys = set(required_keys)
        extra_keys = [k for k in output.keys() if k not in allowed_keys]
        if extra_keys:
            errors.append(f"Extra keys (remove them): {', '.join(extra_keys)}")
        
        # Check b2cs is array
        b2cs = output.get("b2cs", [])
        if not isinstance(b2cs, list):
            errors.append("b2cs must be an array")
        
        # Check b2cs items have required fields
        for i, item in enumerate(b2cs):
            required_b2cs_keys = ["sply_ty", "rt", "typ", "pos", "txval", "csamt"]
            missing = [k for k in required_b2cs_keys if k not in item]
            if missing:
                errors.append(f"b2cs[{i}] missing fields: {', '.join(missing)}")
            
            # Check numeric values
            if not isinstance(item.get("txval"), (int, float)):
                errors.append(f"b2cs[{i}].txval must be number, got {type(item.get('txval'))}")
            if not isinstance(item.get("csamt"), (int, float)):
                errors.append(f"b2cs[{i}].csamt must be number, got {type(item.get('csamt'))}")
        
        # Check supeco.clttx
        clttx = output.get("supeco", {}).get("clttx", [])
        if not isinstance(clttx, list):
            errors.append("supeco.clttx must be an array")
        
        # Check clttx items
        for i, item in enumerate(clttx):
            required_clttx_keys = ["etin", "suppval", "igst", "cgst", "sgst", "cess", "flag"]
            missing = [k for k in required_clttx_keys if k not in item]
            if missing:
                errors.append(f"clttx[{i}] missing fields: {', '.join(missing)}")
            
            # Check numeric values
            if not isinstance(item.get("suppval"), (int, float)):
                errors.append(f"clttx[{i}].suppval must be number")
        
        # Check doc_issue.doc_det is array
        doc_det = output.get("doc_issue", {}).get("doc_det", None)
        if not isinstance(doc_det, list):
            errors.append("doc_issue.doc_det must be an array")
        
        return len(errors) == 0, errors
