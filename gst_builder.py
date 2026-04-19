#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json


class GSTBuilder:
    def __init__(self):
        self.version = "GST3.1.6"

    # ===============================
    # Main Build Methods
    # ===============================
    def build_gstr1(self, parsed_data, gstin, fp):
        return self.build(parsed_data, gstin, fp)

    def build(self, parsed_data, gstin, fp):
        summary = parsed_data.get("summary", {})
        rows = summary.get("rows", [])
        clttx = parsed_data.get("clttx", [])
        doc_issue = parsed_data.get("doc_issue", {"doc_det": []})

        b2cs = []

        for r in rows:
            pos = str(r.get("pos", "")).zfill(2)
            tx = round(float(r.get("taxable_value", 0)), 2)
            ig = round(float(r.get("igst", 0)), 2)
            cg = round(float(r.get("cgst", 0)), 2)
            sg = round(float(r.get("sgst", 0)), 2)

            row = {
                "sply_ty": "INTRA" if (cg > 0 or sg > 0) else "INTER",
                "rt": 3.0,
                "typ": "OE",
                "pos": pos,
                "txval": tx,
                "csamt": 0
            }

            if ig != 0:
                row["iamt"] = ig
            else:
                row["camt"] = cg
                row["samt"] = sg

            b2cs.append(row)

        total_taxable = round(summary.get("total_taxable", 0), 2)
        total_igst = round(summary.get("total_igst", 0), 2)
        total_cgst = round(summary.get("total_cgst", 0), 2)
        total_sgst = round(summary.get("total_sgst", 0), 2)

        return {
            "gstin": gstin,
            "fp": fp,
            "version": self.version,
            "hash": "hash",
            "b2cs": b2cs,
            "supeco": {
                "clttx": clttx
            },
            "doc_issue": doc_issue,
            "summary": {
                "total_items": len(b2cs),
                "total_taxable": total_taxable,
                "total_igst": total_igst,
                "total_cgst": total_cgst,
                "total_sgst": total_sgst,
                "total_tax": round(
                    total_igst + total_cgst + total_sgst, 2
                )
            }
        }

    # ===============================
    # Validation Method
    # ===============================
    def validate_output(self, output):
        errors = []

        required_keys = [
            "gstin", "fp", "version",
            "b2cs", "summary"
        ]

        for key in required_keys:
            if key not in output:
                errors.append(f"Missing key: {key}")

        if "summary" in output:
            s = output["summary"]
            for k in [
                "total_taxable",
                "total_igst",
                "total_cgst",
                "total_sgst",
                "total_tax"
            ]:
                if k not in s:
                    errors.append(f"Missing summary key: {k}")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    # ===============================
    # Save Methods
    # ===============================
    def save_json(self, data, file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def save(self, data, file_path):
        self.save_json(data, file_path)