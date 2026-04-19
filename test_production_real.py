#!/usr/bin/env python3
"""
REAL PRODUCTION FILES SAFE VALIDATION
"""

import sys
sys.path.insert(0, '.')

from parsers import MeeshoParser, FlipkartParser, AmazonParser, AutoMergeParser
import logging

logging.basicConfig(level=logging.INFO)

FLIPKART_FILE = "test_data/flipkart_variants/1f1924de-add8-4717-8998-64952c2dc16e_1773998487000.xlsx"
AMAZON_FILE = "test_data/MTR_B2C-FEBRUARY-2026-A1YGIWFZR88S6S.csv"

MEESHO_FILES = [
    "test_data/tcs_sales.xlsx",
    "test_data/tcs_sales_return.xlsx",
    "test_data/Tax_invoice_details.xlsx"
]

# FINAL REAL EXPECTED VALUES
EXPECTED_FLIPKART = 194.19
EXPECTED_AMAZON = 193.20
EXPECTED_MEESHO = 2406.79
EXPECTED_MERGED = 2794.18


def safe_validate_result(result):
    print("RAW RESULT TYPE:", type(result))
    print("RAW RESULT:", result)

    if not isinstance(result, dict):
        print("FAIL: parser did not return dict")
        return False

    if "summary" not in result:
        print("FAIL: summary missing")
        return False

    if "total_taxable" not in result["summary"]:
        print("FAIL: total_taxable missing")
        return False

    return True


def validate_total(name, total, expected):
    match = abs(total - expected) <= 1.0
    print(f"{name} total Rs{total:.2f} | Expected Rs{expected:.2f} => {'PASS' if match else 'FAIL'}")
    return match


def test_flipkart():
    print("\n=== FLIPKART FEBRUARY ===")
    parser = FlipkartParser()
    result = parser.parse_files([FLIPKART_FILE])

    if safe_validate_result(result):
        total = result["summary"]["total_taxable"]
        return validate_total("Flipkart", total, EXPECTED_FLIPKART)

    return False


def test_amazon():
    print("\n=== AMAZON MTR ===")
    parser = AmazonParser()
    result = parser.parse_files([AMAZON_FILE])

    if safe_validate_result(result):
        total = result["summary"]["total_taxable"]
        return validate_total("Amazon", total, EXPECTED_AMAZON)

    return False


def test_meesho():
    print("\n=== MEESHO ===")
    parser = MeeshoParser()
    result = parser.parse_files(MEESHO_FILES)

    if safe_validate_result(result):
        total = result["summary"]["total_taxable"]
        return validate_total("Meesho", total, EXPECTED_MEESHO)

    return False


def test_automerge():
    print("\n=== AUTO MERGE ALL ===")
    parser = AutoMergeParser()
    result = parser.parse_files([FLIPKART_FILE, AMAZON_FILE] + MEESHO_FILES)

    if safe_validate_result(result):
        total = result["summary"]["total_taxable"]
        return validate_total("Merged", total, EXPECTED_MERGED)

    return False


print("GST REAL PRODUCTION SAFE TEST SUITE")

passed = (
    test_flipkart() and
    test_amazon() and
    test_meesho() and
    test_automerge()
)

print("\nOVERALL RESULT:", "PASS" if passed else "FAIL")
sys.exit(0 if passed else 1)