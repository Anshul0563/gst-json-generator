#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gst_builder.py - Build GSTR-1 JSON from merged_rows

SINGLE SOURCE OF TRUTH: merged_rows from parser

Pipeline:
1. Receive merged_rows from parser
2. Generate b2cs: group by POS, sum taxes
3. Generate summary: sum all b2cs values
4. Generate clttx: group by supplier_etin, sum taxes

Rule: summary.total_taxable = sum(all b2cs txval)
Rule: clttx totals = sum of their rows from merged_rows
"""

import json
from typing import Dict, Any, List, Tuple
from pathlib import Path
import logging
import pandas as pd


class GSTBuilder:
    """Build GSTR-1 JSON from merged_rows."""
    
    def __init__(self):
        self.version = "GST3.1.6"

    def build_gstr1(self, parser_output: Dict[str, Any], gstin: str, fp: str) -> Dict[str, Any]:
        """
        Build complete GSTR-1 JSON.
        
        Args:
            parser_output: {"merged_rows": [...]} from AutoMergeParser
            gstin: Seller GSTIN
            fp: Filing period (MMYYYY)
        
        Returns:
            Complete GSTR-1 JSON structure
        """
        merged_rows = parser_output.get("merged_rows", [])
        
        if not merged_rows:
            logging.warning("No merged rows provided")
            return None
        
        # Build b2cs from merged_rows
        b2cs = self._build_b2cs(merged_rows)
        
        # Build summary from b2cs
        summary = self._build_summary(b2cs)
        
        # Build clttx from merged_rows
        clttx = self._build_clttx(merged_rows)
        
        # Build doc_issue
        doc_issue = {
            "doc_det": [
                {"doc_num": 1, "doc_typ": "Invoices for outward supply", "docs": []},
                {"doc_num": 5, "doc_typ": "Credit Note", "docs": []},
                {"doc_num": 6, "doc_typ": "Debit Note", "docs": []}
            ]
        }
        
        # Validate consistency
        logging.info(f"B2CS count: {len(b2cs)}")
        logging.info(f"Summary total_taxable: {summary['total_taxable']}")
        logging.info(f"CLTTX count: {len(clttx)}")
        for c in clttx:
            logging.info(f"  {c['etin']}: suppval={c['suppval']}")
        
        return {
            "gstin": gstin.upper(),
            "fp": fp,
            "version": self.version,
            "hash": "hash",
            "b2cs": b2cs,
            "supeco": {"clttx": clttx},
            "doc_issue": doc_issue,
            "summary": summary,
            "merged_rows": merged_rows  # Include for debugging
        }

    def _build_b2cs(self, merged_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build b2cs array by grouping merged_rows by POS.
        
        Rule: Each b2cs entry = one POS with aggregated taxes
        Rule: b2cs[].txval = sum of all txval for that POS
        Rule: b2cs[].iamt = sum of all igst_amt for that POS
        Rule: b2cs[].camt = sum of all cgst_amt for that POS
        Rule: b2cs[].samt = sum of all sgst_amt for that POS
        """
        df = pd.DataFrame(merged_rows)
        
        # Group by POS
        grouped = df.groupby("pos", as_index=False).agg({
            "txval": "sum",
            "igst_amt": "sum",
            "cgst_amt": "sum",
            "sgst_amt": "sum"
        }).round(2)
        
        b2cs = []
        for _, row in grouped.iterrows():
            pos = str(row["pos"]).zfill(2)
            txval = round(float(row["txval"]), 2)
            ig = round(float(row["igst_amt"]), 2)
            cg = round(float(row["cgst_amt"]), 2)
            sg = round(float(row["sgst_amt"]), 2)
            
            # Determine supply type
            if abs(cg) > 0.01 or abs(sg) > 0.01:
                sply_ty = "INTRA"
            else:
                sply_ty = "INTER"
            
            item = {
                "sply_ty": sply_ty,
                "rt": 3.0,
                "typ": "OE",
                "pos": pos,
                "txval": txval,
                "csamt": 0
            }
            
            # Add taxes
            if abs(ig) >= 0.01:
                item["iamt"] = ig
            if abs(cg) >= 0.01:
                item["camt"] = cg
            if abs(sg) >= 0.01:
                item["samt"] = sg
            
            b2cs.append(item)
        
        return b2cs

    def _build_summary(self, b2cs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build summary by aggregating all b2cs entries.
        
        Rule: summary.total_taxable = sum(b2cs[].txval)
        Rule: summary.total_igst = sum(b2cs[].iamt)
        Rule: summary.total_cgst = sum(b2cs[].camt)
        Rule: summary.total_sgst = sum(b2cs[].samt)
        Rule: summary.total_tax = igst + cgst + sgst
        """
        total_txval = sum(float(b.get("txval", 0)) for b in b2cs)
        total_igst = sum(float(b.get("iamt", 0)) for b in b2cs)
        total_cgst = sum(float(b.get("camt", 0)) for b in b2cs)
        total_sgst = sum(float(b.get("samt", 0)) for b in b2cs)
        
        return {
            "total_items": len(b2cs),
            "total_taxable": round(total_txval, 2),
            "total_igst": round(total_igst, 2),
            "total_cgst": round(total_cgst, 2),
            "total_sgst": round(total_sgst, 2),
            "total_tax": round(total_igst + total_cgst + total_sgst, 2)
        }

    def _build_clttx(self, merged_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build clttx by grouping merged_rows by supplier_etin.
        
        Rule: clttx[].suppval = sum(txval) for that supplier
        Rule: clttx[].igst = sum(igst_amt) for that supplier
        Rule: clttx[].cgst = sum(cgst_amt) for that supplier
        Rule: clttx[].sgst = sum(sgst_amt) for that supplier
        """
        df = pd.DataFrame(merged_rows)
        
        # Get unique ETINs from data
        etins = df["supplier_etin"].unique()
        
        clttx = []
        
        for etin in sorted(etins):
            supplier_rows = df[df["supplier_etin"] == etin]
            
            suppval = round(float(supplier_rows["txval"].sum()), 2)
            igst = round(float(supplier_rows["igst_amt"].sum()), 2)
            cgst = round(float(supplier_rows["cgst_amt"].sum()), 2)
            sgst = round(float(supplier_rows["sgst_amt"].sum()), 2)
            
            clttx.append({
                "etin": str(etin),
                "suppval": suppval,
                "igst": igst,
                "cgst": cgst,
                "sgst": sgst,
                "cess": 0,
                "flag": "N"
            })
        
        return clttx

    def validate_output(self, output: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate GSTR-1 output."""
        errors = []
        
        # Check b2cs total matches summary
        b2cs_total = sum(float(b.get("txval", 0)) for b in output.get("b2cs", []))
        summary_total = output.get("summary", {}).get("total_taxable", 0)
        
        if abs(b2cs_total - summary_total) > 0.01:
            errors.append(f"B2CS total {b2cs_total} != summary total {summary_total}")
        
        # Check summary taxes
        b2cs_igst = sum(float(b.get("iamt", 0)) for b in output.get("b2cs", []))
        summary_igst = output.get("summary", {}).get("total_igst", 0)
        if abs(b2cs_igst - summary_igst) > 0.01:
            errors.append(f"B2CS IGST {b2cs_igst} != summary IGST {summary_igst}")
        
        # Check CLTTX
        clttx = output.get("supeco", {}).get("clttx", [])
        if not clttx:
            errors.append("CLTTX is empty")
        
        for item in clttx:
            if item.get("suppval", 0) < 0:
                errors.append(f"CLTTX {item['etin']} has negative suppval: {item['suppval']}")
        
        return len(errors) == 0, errors
