#!/usr/bin/env python3
"""
REAL PRODUCTION FILES VALIDATION - No synthetics
"""

import sys
sys.path.insert(0, '.')
from parsers import MeeshoParser, FlipkartParser, AmazonParser, AutoMergeParser
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Real production files only
FLIPKART_FILE = 'test_data/flipkart_variants/1f1924de-add8-4717-8998-64952c2dc16e_1773998487000.xlsx'
AMAZON_FILE = 'test_data/MTR_B2C-FEBRUARY-2026-A1YGIWFZR88S6S.csv'
MEESHO_FILES = [
    'test_data/tcs_sales.xlsx',
    'test_data/tcs_sales_return.xlsx',
    'test_data/Tax_invoice_details.xlsx'
]

EXPECTED_FLIPKART = 1686.38

def test_flipkart():
    print('\\n=== FLIPKART FEBRUARY ===')
    parser = FlipkartParser()
    results = parser.parse_files([FLIPKART_FILE])
    if results:
        for r in results:
            total = r['summary']['total_taxable']
            print(f"File: {r['filename']} Month: {r['month']} Total: Rs{total:.2f}")
            match = abs(total - EXPECTED_FLIPKART) < 1.0
            print(f"Expected Rs{EXPECTED_FLIPKART}: {'PASS' if match else 'FAIL'}")
            return match
    print('Flipkart FAILED')
    return False

def test_amazon():
    print('\\n=== AMAZON MTR ===')
    parser = AmazonParser()
    result = parser.parse_files([AMAZON_FILE])
    total = result['summary']['total_taxable'] if result else 0
    print(f"Amazon total: Rs{total:.2f}")
    return bool(result)

def test_meesho():
    print('\\n=== MEESHO ===')
    parser = MeeshoParser()
    result = parser.parse_files(MEESHO_FILES)
    total = result['summary']['total_taxable'] if result else 0
    print(f"Meesho total: Rs{total:.2f}")
    return bool(result)

def test_automerge():
    print('\\n=== AUTO MERGE ALL ===')
    all_files = [FLIPKART_FILE, AMAZON_FILE] + MEESHO_FILES
    parser = AutoMergeParser()
    result = parser.parse_files(all_files)
    total = result['summary']['total_taxable'] if result else 0
    print(f"Merged total: Rs{total:.2f}")
    return bool(result)

print('GST REAL PRODUCTION TEST SUITE')

passed = (
    test_flipkart() and
    test_amazon() and 
    test_meesho() and
    test_automerge()
)

print(f'\\nOVERALL: {"PASS" if passed else "FAIL"}')
sys.exit(0 if passed else 1)

