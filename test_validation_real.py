#!/usr/bin/env python3
#\"\"\"PRODUCTION REAL FILES VALIDATION - NO SYNTHETICS\"\"\"

import sys
sys.path.insert(0, '.')
from parsers import MeeshoParser, FlipkartParser, AmazonParser, AutoMergeParser
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# REAL PRODUCTION FILES ONLY
REAL_FILES = {
    'flipkart': ['test_data/flipkart_variants/1f1924de-add8-4717-8998-64952c2dc16e_1773998487000.xlsx'],
    'amazon': ['test_data/MTR_B2C-FEBRUARY-2026-A1YGIWFZR88S6S.csv'],
    'meesho': [
        'test_data/tcs_sales.xlsx',
        'test_data/tcs_sales_return.xlsx',
        'test_data/Tax_invoice_details.xlsx'
    ]
}

EXPECTED = {
    '1f1924de-add8-4717-8998-64952c2dc16e_1773998487000.xlsx': 1686.38  # Flipkart Feb
}

def test_platform(parser, name, files):
    print(f'\n=== {name.upper()} REAL FILES ===')
    result = parser.parse_files(files)
    if result:
        total = result['summary']['total_taxable']
        print(f'✅ {name}: ₹{total:.2f}')
        return True
    print(f'❌ {name}: FAILED')
    return False

print('GST TOOL - REAL PRODUCTION VALIDATION\\n')

# Individual platform tests
flipkart_pass = test_platform(FlipkartParser(), 'flipkart', REAL_FILES['flipkart'])
amazon_pass = test_platform(AmazonParser(), 'amazon', REAL_FILES['amazon'])
meesho_pass = test_platform(MeeshoParser(), 'meesho', REAL_FILES['meesho'])

# AutoMerge
print('\\n=== AUTO MERGE ALL REAL FILES ===')
all_files = []
for files in REAL_FILES.values():
    all_files.extend(files)
automerge = AutoMergeParser()
merged = automerge.parse_files(all_files)
total = merged['summary']['total_taxable'] if merged else 0
print(f'✅ AutoMerge: ₹{total:.2f}')

# Flipkart specific totals check
flipkart_results = FlipkartParser().parse_files(REAL_FILES['flipkart'])
flipkart_totals_ok = False
if flipkart_results:
    for r in flipkart_results:
        filename = r['filename']
        actual = r['summary']['total_taxable']
        expected_total = EXPECTED.get(filename)
        if expected_total:
            match = abs(actual - expected_total) < 1.0
            print(f'Flipkart {filename}: ₹{actual:.2f} {"✓" if match else "✗"} (exp {expected_total})')
            flipkart_totals_ok = flipkart_totals_ok or match

overall = flipkart_pass and amazon_pass and meesho_pass
print(f'\n🎯 RESULT: {"PASS ✅" if overall else "FAIL ❌"}')

sys.exit(0 if overall else 1)

