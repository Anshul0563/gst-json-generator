#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gst_builder.py - FINAL GST Portal Compliant Builder
Exact structure for GST upload portal
Uses parser.py merged_rows output
"""

import json
import logging
from typing import Dict, Any, List, Tuple
from collections import OrderedDict

import pandas as pd


class GSTBuilder:
    def __init__(self):
        self.version = "GST3.1.6"

    # ==================================================
    # MAIN BUILD
    # ==================================================
    def build_gstr1(self, parser_output: Dict[str, Any], gstin: str, fp: str) -> Dict[str, Any]:
        merged_rows = parser_output.get("merged_rows", [])

        if not merged_rows:
            raise ValueError("No parsed rows found")

        b2cs = self._build_b2cs(merged_rows)
        clttx = self._build_clttx(merged_rows)

        output = OrderedDict()
        output["gstin"] = str(gstin).strip().upper()
        output["fp"] = str(fp).strip()
        output["version"] = self.version
        output["hash"] = "hash"
        output["doc_issue"] = {"doc_det": []}
        output["b2cs"] = b2cs
        output["supeco"] = {"clttx": clttx}

        return dict(output)

    # Backward compatibility
    def build(self, parser_output: Dict[str, Any], gstin: str, fp: str) -> Dict[str, Any]:
        return self.build_gstr1(parser_output, gstin, fp)

    # ==================================================
    # B2CS
    # ==================================================
    def _build_b2cs(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        df = pd.DataFrame(rows)

        grouped = (
            df.groupby("pos", as_index=False)
            .agg({
                "txval": "sum",
                "igst_amt": "sum",
                "cgst_amt": "sum",
                "sgst_amt": "sum",
            })
            .sort_values("pos")
            .reset_index(drop=True)
        )

        b2cs = []

        for _, r in grouped.iterrows():
            pos = str(r["pos"]).zfill(2)

            txval = round(float(r["txval"]), 2)
            igst = round(float(r["igst_amt"]), 2)
            cgst = round(float(r["cgst_amt"]), 2)
            sgst = round(float(r["sgst_amt"]), 2)

            # skip full zero rows
            if abs(txval) < 0.01 and abs(igst) < 0.01 and abs(cgst) < 0.01 and abs(sgst) < 0.01:
                continue

            intra = abs(cgst) > 0 or abs(sgst) > 0

            item = OrderedDict()
            item["sply_ty"] = "INTRA" if intra else "INTER"
            item["rt"] = 3.0
            item["typ"] = "OE"
            item["pos"] = pos
            item["txval"] = txval

            if intra:
                item["camt"] = cgst
                item["samt"] = sgst
            else:
                item["iamt"] = igst

            item["csamt"] = 0

            b2cs.append(dict(item))

        return b2cs

    # ==================================================
    # CLTTX
    # ==================================================
    def _build_clttx(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        df = pd.DataFrame(rows)

        grouped = (
            df.groupby("supplier_etin", as_index=False)
            .agg({
                "txval": "sum",
                "igst_amt": "sum",
                "cgst_amt": "sum",
                "sgst_amt": "sum",
            })
            .sort_values("supplier_etin")
            .reset_index(drop=True)
        )

        clttx = []

        for _, r in grouped.iterrows():
            item = OrderedDict()
            item["etin"] = str(r["supplier_etin"]).strip()
            item["suppval"] = round(float(r["txval"]), 2)
            item["igst"] = round(float(r["igst_amt"]), 2)
            item["cgst"] = round(float(r["cgst_amt"]), 2)
            item["sgst"] = round(float(r["sgst_amt"]), 2)
            item["cess"] = 0
            item["flag"] = "N"

            clttx.append(dict(item))

        return clttx

    # ==================================================
    # SAVE
    # ==================================================
    def save_json(self, output: Dict[str, Any], filepath: str) -> bool:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Save failed: {e}")
            return False

    def save(self, output: Dict[str, Any], filepath: str) -> bool:
        return self.save_json(output, filepath)

    # ==================================================
    # VALIDATE
    # ==================================================
    def validate_output(self, output: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        required = [
            "gstin",
            "fp",
            "version",
            "hash",
            "doc_issue",
            "b2cs",
            "supeco",
        ]

        for key in required:
            if key not in output:
                errors.append(f"Missing key: {key}")

        if "b2cs" in output and not isinstance(output["b2cs"], list):
            errors.append("b2cs must be list")

        if "supeco" in output:
            if "clttx" not in output["supeco"]:
                errors.append("supeco.clttx missing")
            elif not isinstance(output["supeco"]["clttx"], list):
                errors.append("supeco.clttx must be list")

        if "doc_issue" in output:
            if "doc_det" not in output["doc_issue"]:
                errors.append("doc_issue.doc_det missing")

        return len(errors) == 0, errors