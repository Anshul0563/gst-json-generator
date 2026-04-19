#!/usr/bin/env python3
"""
REAL PRODUCTION FILES SAFE VALIDATION
"""

import sys
sys.path.insert(0, '.')
from parsers import MeeshoParser, FlipkartParser, AmazonParser, AutoMergeParser
import logging
from pathlib import Path
from typing import Dict, Any, List, Union

logging.basicConfig(level=logging.INFO)

FLIPKART_FILE = 'test_data/flipkart_variants/1f1924de-add8-4717-8998-64952c2dc16e_1773998487000.xlsx'
AMAZON_FILE = 'test_data/MTR_B2C-FEBRUARY-2026-A1YGIWFZR88S6S.csv'
MEESHO_FILES = [
    'test_data/tcs_sales.xlsx',
    'test_data/tcs_sales_return.xlsx',
    'test_data/Tax_invoice_details.xlsx'
]

EXPECTED_FLIPKART = 1686.38

def safe_validate_result(result: Any) -> bool:
    "Safe parser result validation."
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

def test_flipkart():
    print("\n=== FLIPKART FEBRUARY ===")
    parser = FlipkartParser()
    results = parser.parse_files([FLIPKART_FILE])
    
    if not results:
        print("FAIL: no results")
        return False
    
    # Handle both dict and list
    if isinstance(results, list) and len(results) > 0:
        r = results[0]
        print("Flipkart list result[0]:", r)
        if safe_validate_result(r):
            total = r["summary"]["total_taxable"]
            match = abs(total - EXPECTED_FLIPKART) < 1.0
            print("Flipkart total Rs%.2f: %s" % (total, 'PASS' if match else 'FAIL'))
            return match
    elif isinstance(results, dict):
        if safe_validate_result(results):
            total = results["summary"]["total_taxable"]
            match = abs(total - EXPECTED_FLIPKART) < 1.0
            print("Flipkart dict total Rs%.2f: %s" % (total, 'PASS' if match else 'FAIL'))
            return match
    
    print("FAIL: invalid result format")
    return False

def test_amazon():
    print("\n=== AMAZON MTR ===")
    parser = AmazonParser()
    result = parser.parse_files([AMAZON_FILE])
    if safe_validate_result(result):
        total = result["summary"]["total_taxable"]
        print("Amazon total: Rs%.2f" % total)
        return True
    return False

def test_meesho():
    print("\n=== MEESHO ===")
    parser = MeeshoParser()
    result = parser.parse_files(MEESHO_FILES)
    if safe_validate_result(result):
        total = result["summary"]["total_taxable"]
        print("Meesho total: Rs%.2f" % total)
        return True
    return False

def test_automerge():
    print("\n=== AUTO MERGE ALL ===")
    all_files = [FLIPKART_FILE, AMAZON_FILE] + MEESHO_FILES
    parser = AutoMergeParser()
    result = parser.parse_files(all_files)
    if safe_validate_result(result):
        total = result["summary"]["total_taxable"]
        print("Merged total: Rs%.2f" % total)
        return True
    return False

print("GST REAL PRODUCTION SAFE TEST SUITE")

passed = (
    test_flipkart() and
    test_amazon() and 
    test_meesho() and
    test_automerge()
)

print("\nOVERALL RESULT: %s" % ("PASS" if passed else "FAIL"))
sys.exit(0 if passed else 1)

