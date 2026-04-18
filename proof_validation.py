#!/usr/bin/env python3
"""
Proof-based parser validation against accepted expected results.
"""

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Dict
from uuid import uuid4

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from gst_builder import GSTBuilder
from parsers import AmazonParser, FlipkartParser, MeeshoParser


MEESHO_FILES = [
    "test_data/meesho_sales.csv",
    "test_data/meesho_returns_credit_note.csv",
]

AMAZON_FILE = "test_data/amazon_sales.csv"

EXPECTED_MEESHO = {
    "summary": {
        "rows": [
            {"pos": "07", "taxable_value": 2000.0, "igst": 0.0, "cgst": 30.0, "sgst": 30.0},
            {"pos": "24", "taxable_value": 2500.0, "igst": 75.0, "cgst": 0.0, "sgst": 0.0},
            {"pos": "27", "taxable_value": 1000.0, "igst": 30.0, "cgst": 0.0, "sgst": 0.0},
            {"pos": "29", "taxable_value": 3000.0, "igst": 90.0, "cgst": 0.0, "sgst": 0.0},
        ],
        "total_taxable": 8500.0,
        "total_igst": 195.0,
        "total_cgst": 30.0,
        "total_sgst": 30.0,
    },
    "invoice_docs": [
        {"invoice_no": "MES001", "pos": "07", "txval": 1000.0, "igst_amt": 0.0, "cgst_amt": 15.0, "sgst_amt": 15.0},
        {"invoice_no": "MES004", "pos": "07", "txval": 1500.0, "igst_amt": 0.0, "cgst_amt": 22.5, "sgst_amt": 22.5},
        {"invoice_no": "MES005", "pos": "24", "txval": 2500.0, "igst_amt": 75.0, "cgst_amt": 0.0, "sgst_amt": 0.0},
        {"invoice_no": "MES002", "pos": "27", "txval": 2000.0, "igst_amt": 60.0, "cgst_amt": 0.0, "sgst_amt": 0.0},
        {"invoice_no": "MES003", "pos": "29", "txval": 3000.0, "igst_amt": 90.0, "cgst_amt": 0.0, "sgst_amt": 0.0},
    ],
    "credit_docs": [
        {"invoice_no": "MES-RET001", "pos": "07", "txval": 500.0, "igst_amt": 0.0, "cgst_amt": 7.5, "sgst_amt": 7.5},
        {"invoice_no": "MES-RET002", "pos": "27", "txval": 1000.0, "igst_amt": 30.0, "cgst_amt": 0.0, "sgst_amt": 0.0},
    ],
    "clttx": [
        {
            "etin": "07AARCM9332R1CQ",
            "suppval": 8500.0,
            "igst": 195.0,
            "cgst": 30.0,
            "sgst": 30.0,
            "cess": 0.0,
            "flag": "N",
        }
    ],
}

EXPECTED_AMAZON = {
    "summary": {
        "rows": [
            {"pos": "27", "taxable_value": 2500.0, "igst": 75.0, "cgst": 0.0, "sgst": 0.0},
            {"pos": "29", "taxable_value": 2000.0, "igst": 60.0, "cgst": 0.0, "sgst": 0.0},
            {"pos": "33", "taxable_value": 3000.0, "igst": 90.0, "cgst": 0.0, "sgst": 0.0},
            {"pos": "36", "taxable_value": 4000.0, "igst": 120.0, "cgst": 0.0, "sgst": 0.0},
        ],
        "total_taxable": 11500.0,
        "total_igst": 345.0,
        "total_cgst": 0.0,
        "total_sgst": 0.0,
    },
    "invoice_docs": [
        {"invoice_no": "AMZ004", "pos": "27", "txval": 2500.0, "igst_amt": 75.0, "cgst_amt": 0.0, "sgst_amt": 0.0},
        {"invoice_no": "AMZ001", "pos": "29", "txval": 2000.0, "igst_amt": 60.0, "cgst_amt": 0.0, "sgst_amt": 0.0},
        {"invoice_no": "AMZ002", "pos": "33", "txval": 3000.0, "igst_amt": 90.0, "cgst_amt": 0.0, "sgst_amt": 0.0},
        {"invoice_no": "AMZ003", "pos": "36", "txval": 4000.0, "igst_amt": 120.0, "cgst_amt": 0.0, "sgst_amt": 0.0},
    ],
    "credit_docs": [],
}

EXPECTED_FLIPKART_RANDOM = {
    "summary": {
        "rows": [
            {"pos": "07", "taxable_value": 5000.0, "igst": 0.0, "cgst": 75.0, "sgst": 75.0},
            {"pos": "27", "taxable_value": 8000.0, "igst": 240.0, "cgst": 0.0, "sgst": 0.0},
        ],
        "total_taxable": 13000.0,
        "total_igst": 240.0,
        "total_cgst": 75.0,
        "total_sgst": 75.0,
    },
    "invoice_count": 2,
}


def ensure_files_exist(paths):
    missing = [path for path in paths if not Path(path).exists()]
    if missing:
        raise FileNotFoundError(f"Missing sample files: {missing}")


def create_sample_file(path: str, data: Dict[str, list]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(data).to_csv(target, index=False)


def ensure_sample_inputs() -> None:
    if not Path(MEESHO_FILES[0]).exists():
        create_sample_file(
            MEESHO_FILES[0],
            {
                "order_id": ["MES001", "MES002", "MES003", "MES004", "MES005"],
                "state": ["Delhi", "Maharashtra", "Karnataka", "Delhi", "Gujarat"],
                "taxable_value": [1000, 2000, 3000, 1500, 2500],
                "igst": [0, 60, 90, 0, 75],
                "cgst": [15, 0, 0, 22.5, 0],
                "sgst": [15, 0, 0, 22.5, 0],
            },
        )

    if not Path(MEESHO_FILES[1]).exists():
        create_sample_file(
            MEESHO_FILES[1],
            {
                "order_id": ["MES-RET001", "MES-RET002"],
                "state": ["Delhi", "Maharashtra"],
                "taxable_value": [500, 1000],
                "igst": [0, 30],
                "cgst": [7.5, 0],
                "sgst": [7.5, 0],
            },
        )

    if not Path(AMAZON_FILE).exists():
        create_sample_file(
            AMAZON_FILE,
            {
                "order_id": ["AMZ001", "AMZ002", "AMZ003", "AMZ004"],
                "ship_state": ["Bangalore", "Chennai", "Hyderabad", "Pune"],
                "tax_exclusive": [2000, 3000, 4000, 2500],
                "igst": [60, 90, 120, 75],
            },
        )


def build_single_platform_gst_json(parsed_result):
    payload = deepcopy(parsed_result)
    payload["clttx"] = [
        {
            "etin": parsed_result["etin"],
            "suppval": parsed_result["summary"]["total_taxable"],
            "igst": parsed_result["summary"]["total_igst"],
            "cgst": parsed_result["summary"]["total_cgst"],
            "sgst": parsed_result["summary"]["total_sgst"],
            "cess": 0.0,
            "flag": "N",
        }
    ]
    builder = GSTBuilder()
    return builder.build_gstr1(payload, "27AAPCT1234A1Z5", "122023")


def accepted_meesho_gst_json():
    return {
        "gstin": "27AAPCT1234A1Z5",
        "fp": "122023",
        "version": "GST3.1.6",
        "hash": "hash",
        "b2cs": [
            {"sply_ty": "INTER", "rt": 3.0, "typ": "OE", "pos": "07", "txval": 2000.0, "csamt": 0, "iamt": 60.0},
            {"sply_ty": "INTER", "rt": 3.0, "typ": "OE", "pos": "24", "txval": 2500.0, "csamt": 0, "iamt": 75.0},
            {"sply_ty": "INTRA", "rt": 3.0, "typ": "OE", "pos": "27", "txval": 1000.0, "csamt": 0, "camt": 15.0, "samt": 15.0},
            {"sply_ty": "INTER", "rt": 3.0, "typ": "OE", "pos": "29", "txval": 3000.0, "csamt": 0, "iamt": 90.0},
        ],
        "supeco": {"clttx": EXPECTED_MEESHO["clttx"]},
        "doc_issue": {
            "doc_det": [
                {
                    "doc_num": 1,
                    "doc_typ": "Invoices for outward supply",
                    "docs": [{"from": "MES001", "to": "MES005", "totnum": 5, "cancel": 0, "net_issue": 5}],
                },
                {
                    "doc_num": 5,
                    "doc_typ": "Credit Note",
                    "docs": [{"from": "MES-RET001", "to": "MES-RET002", "totnum": 2, "cancel": 0, "net_issue": 2}],
                },
            ]
        },
        "summary": {
            "total_items": 4,
            "total_taxable": 8500.0,
            "total_igst": 195.0,
            "total_cgst": 30.0,
            "total_sgst": 30.0,
            "total_tax": 255.0,
        },
    }


def print_section_result(label, mismatches):
    if not mismatches:
        print(f"  PASS {label}")
        return True

    print(f"  FAIL {label}")
    for mismatch in mismatches:
        print(f"    - {mismatch}")
    return False


def compare_rows(actual_rows, expected_rows, label):
    mismatches = []
    if actual_rows != expected_rows:
        actual_map = {row["pos"]: row for row in actual_rows}
        expected_map = {row["pos"]: row for row in expected_rows}
        for pos in sorted(set(actual_map) | set(expected_map)):
            if actual_map.get(pos) != expected_map.get(pos):
                mismatches.append(
                    f"{label} POS {pos}: expected {expected_map.get(pos)}, got {actual_map.get(pos)}"
                )
    return mismatches


def compare_meesho():
    ensure_files_exist(MEESHO_FILES)
    parser = MeeshoParser()
    result = parser.parse_files(MEESHO_FILES)
    gst_json = build_single_platform_gst_json(result)
    accepted_json = accepted_meesho_gst_json()

    print("\nMEESHO PROOF CHECK")
    print(f"  Files: {', '.join(MEESHO_FILES)}")

    checks = []
    checks.append(print_section_result(
        "state totals",
        compare_rows(result["summary"]["rows"], EXPECTED_MEESHO["summary"]["rows"], "state totals"),
    ))

    tax_mismatches = []
    for key in ["total_taxable", "total_igst", "total_cgst", "total_sgst"]:
        actual = result["summary"][key]
        expected = EXPECTED_MEESHO["summary"][key]
        if actual != expected:
            tax_mismatches.append(f"{key}: expected {expected}, got {actual}")
    checks.append(print_section_result("tax totals", tax_mismatches))

    invoice_mismatches = []
    if result["invoice_docs"] != EXPECTED_MEESHO["invoice_docs"]:
        invoice_mismatches.append(
            f"expected {len(EXPECTED_MEESHO['invoice_docs'])} invoices, got {len(result['invoice_docs'])}"
        )
        invoice_mismatches.append(f"expected docs {EXPECTED_MEESHO['invoice_docs']}")
        invoice_mismatches.append(f"actual docs {result['invoice_docs']}")
    checks.append(print_section_result("invoice counts", invoice_mismatches))

    supeco_mismatches = []
    if gst_json["supeco"] != accepted_json["supeco"]:
        supeco_mismatches.append(f"expected {accepted_json['supeco']}, got {gst_json['supeco']}")
    checks.append(print_section_result("supeco", supeco_mismatches))

    returns_mismatches = []
    if result["credit_docs"] != EXPECTED_MEESHO["credit_docs"]:
        returns_mismatches.append(f"expected {EXPECTED_MEESHO['credit_docs']}, got {result['credit_docs']}")
    checks.append(print_section_result("returns", returns_mismatches))

    gst_mismatches = []
    if gst_json != accepted_json:
        for key in accepted_json:
            if gst_json.get(key) != accepted_json.get(key):
                gst_mismatches.append(f"{key}: expected {accepted_json[key]}, got {gst_json.get(key)}")
    checks.append(print_section_result("generated GST JSON exact match", gst_mismatches))

    return all(checks), result, gst_json


def compare_flipkart_random():
    parser = FlipkartParser()
    base_dir = Path("test_data/flipkart_variants")
    base_dir.mkdir(parents=True, exist_ok=True)
    data = pd.DataFrame(
        {
            "invoice_no": ["FK001", "FK002"],
            "delivery_state": ["Delhi", "Mumbai"],
            "sale_value": [5000, 8000],
            "tax": [150, 240],
        }
    )
    files = []
    for _ in range(3):
        path = base_dir / f"{uuid4().hex}.csv"
        data.to_csv(path, index=False)
        files.append(str(path))

    result = parser.parse_files(files)

    print("\nFLIPKART RANDOM-FILENAME CHECK")
    print(f"  Files: {', '.join(Path(path).name for path in files)}")

    checks = []
    checks.append(print_section_result(
        "state totals",
        compare_rows(result["summary"]["rows"], EXPECTED_FLIPKART_RANDOM["summary"]["rows"], "state totals"),
    ))

    tax_mismatches = []
    for key in ["total_taxable", "total_igst", "total_cgst", "total_sgst"]:
        actual = result["summary"][key]
        expected = EXPECTED_FLIPKART_RANDOM["summary"][key]
        if actual != expected:
            tax_mismatches.append(f"{key}: expected {expected}, got {actual}")
    checks.append(print_section_result("tax totals", tax_mismatches))

    invoice_mismatches = []
    actual_count = len(result.get("invoice_docs", []))
    expected_count = EXPECTED_FLIPKART_RANDOM["invoice_count"]
    if actual_count != expected_count:
        invoice_mismatches.append(f"expected {expected_count} invoices, got {actual_count}")
    checks.append(print_section_result("invoice counts", invoice_mismatches))

    return all(checks), result


def compare_amazon():
    ensure_files_exist([AMAZON_FILE])
    parser = AmazonParser()
    result = parser.parse_files([AMAZON_FILE])

    print("\nAMAZON CSV CHECK")
    print(f"  File: {AMAZON_FILE}")

    checks = []
    checks.append(print_section_result(
        "state totals",
        compare_rows(result["summary"]["rows"], EXPECTED_AMAZON["summary"]["rows"], "state totals"),
    ))

    tax_mismatches = []
    for key in ["total_taxable", "total_igst", "total_cgst", "total_sgst"]:
        actual = result["summary"][key]
        expected = EXPECTED_AMAZON["summary"][key]
        if actual != expected:
            tax_mismatches.append(f"{key}: expected {expected}, got {actual}")
    checks.append(print_section_result("tax totals", tax_mismatches))

    invoice_mismatches = []
    if result["invoice_docs"] != EXPECTED_AMAZON["invoice_docs"]:
        invoice_mismatches.append(
            f"expected {len(EXPECTED_AMAZON['invoice_docs'])} invoices, got {len(result['invoice_docs'])}"
        )
    checks.append(print_section_result("invoice counts", invoice_mismatches))

    returns_mismatches = []
    if result["credit_docs"] != EXPECTED_AMAZON["credit_docs"]:
        returns_mismatches.append(f"expected no returns, got {result['credit_docs']}")
    checks.append(print_section_result("returns", returns_mismatches))

    return all(checks), result


def main():
    overall = True
    ensure_sample_inputs()

    meesho_ok, _, meesho_json = compare_meesho()
    flipkart_ok, _ = compare_flipkart_random()
    amazon_ok, _ = compare_amazon()
    overall = meesho_ok and flipkart_ok and amazon_ok

    output_path = Path("test_output/proof_validation_latest.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(meesho_json, indent=2))

    print("\nFINAL RESULT")
    print(f"  Meesho exact match: {'PASS' if meesho_ok else 'FAIL'}")
    print(f"  Flipkart random filenames: {'PASS' if flipkart_ok else 'FAIL'}")
    print(f"  Amazon CSV parser: {'PASS' if amazon_ok else 'FAIL'}")
    print(f"  Evidence JSON: {output_path}")

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
