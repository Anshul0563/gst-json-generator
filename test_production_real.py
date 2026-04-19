#!/usr/bin/env python3
"""
GST PRODUCTION VALIDATION - REAL FEBRUARY FILES
Expected: Flipkart Rs194.19, Amazon Rs193.20, Meesho Rs2406.79, Merged Rs2794.18
"""

import sys
sys.path.insert(0, '.')
from parsers import FlipkartParser, AmazonParser, MeeshoParser, AutoMergeParser
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

FLIPKART_FILE = 'test_data/flipkart_variants/1f1924de-add8-4717-8998-64952c2dc16e_1773998487000.xlsx'
AMAZON_FILE = 'test_data/MTR_B2C-FEBRUARY-2026-A1YGIWFZR88S6S.csv'
MEESHO_FILES = ['test_data/tcs_sales.xlsx', 'test_data/tcs_sales_return.xlsx', 'test_data/Tax_invoice_details.xlsx']

EXPECTED = {
    'flipkart': 194.19,
    'amazon': 193.20,
    'meesho': 2406.79,
    'merged': 2794.18
}

def safe_extract_total(result):
    """Safe total extraction with full debug."""
    print("DEBUG: result =", result)
    print("DEBUG: type(result) =", type(result))
    
    if result is None:
        return None, "No result"
    
    if isinstance(result, dict):
        if 'summary' in result and isinstance(result['summary'], dict):
            if 'total_taxable' in result['summary']:
                return result['summary']['total_taxable'], "OK"
            else:
                return None, "total_taxable missing"
        else:
            return None, "summary missing/invalid"
    else:
        return None, f"Wrong type {type(result)}"

def test_platform(name, files, expected):
    print(f"\n=== {name.upper()} ===")
    parser_map = {
        'flipkart': FlipkartParser,
        'amazon': AmazonParser,
        'meesho': MeeshoParser
    }
    
    ParserClass = parser_map.get(name, AutoMergeParser)
    parser = ParserClass()
    result = parser.parse_files(files)
    
    total, status = safe_extract_total(result)
    if total is None:
        print(f"{name} FAIL: {status}")
        return False
    
    match = abs(total - expected) < 1.0
    print(f"{name} Rs{total:.2f} (exp Rs{expected:.2f}): {'PASS' if match else 'FAIL'}")
    return match

def test_merged():
    print("\n=== MERGED ALL ===")
    parser = AutoMergeParser()
    all_files = [FLIPKART_FILE, AMAZON_FILE] + MEESHO_FILES
    result = parser.parse_files(all_files)
    
    total, status = safe_extract_total(result)
    if total is None:
        print(f"Merged FAIL: {status}")
        return False
    
    match = abs(total - EXPECTED['merged']) < 1.0
    print(f"Merged Rs{total:.2f} (exp Rs{EXPECTED['merged']:.2f}): {'PASS' if match else 'FAIL'}")
    return match

print("GST FEBRUARY PRODUCTION VALIDATION")
print("Expected totals: Flipkart 194.19, Amazon 193.20, Meesho 2406.79, Merged 2794.18")

tests = [
    ('flipkart', [FLIPKART_FILE], EXPECTED['flipkart']),
    ('amazon', [AMAZON_FILE], EXPECTED['amazon']),
    ('meesho', MEESHO_FILES, EXPECTED['meesho'])
]

all_pass = test_merged()
for name, files, expected in tests:
    all_pass = all_pass and test_platform(name, files, expected)

print("\n" + "="*50)
print("FINAL RESULT:", "ALL PASS ✅" if all_pass else "SOME FAIL ❌")
sys.exit(0 if all_pass else 1)

