#!/usr/bin/env python3
"""
REGRESSION TESTS - Lightweight synthetic regression
"""

import sys
sys.path.insert(0, '.')
from parsers import FlipkartParser
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

def create_regression_sample():
    "Minimal synthetic for regression."
    data = {
        'Buyer Invoice ID': ['FK001'],
        "Customer's Delivery State": ['Delhi'],
        'Taxable Value Final Invoice Amount Taxes': [1000],
        'Event Type': ['SALE'],
        'Event Sub Type': ['SALE']
    }
    path = Path('test_regression.xlsx')
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        pd.DataFrame(data).to_excel(writer, sheet_name='Sales Report', index=False)
    return str(path)

def test_regression():
    print('REGRESSION TEST - Flipkart basic')
    file = create_regression_sample()
    parser = FlipkartParser()
    result = parser.parse_files([file])
    total = result['summary']['total_taxable'] if result else 0
    print(f'Regression total: Rs{total}')
    Path('test_regression.xlsx').unlink(missing_ok=True)
    return total > 0

if __name__ == '__main__':
    success = test_regression()
    print('Regression:', 'PASS' if success else 'FAIL')
    sys.exit(0 if success else 1)

