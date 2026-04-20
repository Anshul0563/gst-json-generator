#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test to verify parser fixes for returns handling."""

import sys
sys.path.insert(0, '/home/jarvis/Documents/IT/GST-Tool')

# Test setup
print("=" * 60)
print("Testing Parser Fixes for Returns Handling")
print("=" * 60)

# Import pandas first
try:
    import pandas as pd
    print("✓ Pandas available")
except ImportError:
    print("✗ Pandas not available - installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "-q"])
    import pandas as pd
    print("✓ Pandas installed")

# Now import our modules
from parsers import BaseParser, MeeshoParser, AmazonParser, AutoMergeParser

# Test 1: Verify returns are stored as positive with txn_type="return"
print("\nTest 1: Verify BaseParser.finalize() handling of sales vs returns")
print("-" * 60)

# Create test data
test_rows = [
    {"invoice_no": "INV001", "pos": "07", "taxable_value": 1000.0, "igst": 0.0, "cgst": 90.0, "sgst": 90.0, "txn_type": "sale"},
    {"invoice_no": "INV002", "pos": "07", "taxable_value": 500.0, "igst": 0.0, "cgst": 45.0, "sgst": 45.0, "txn_type": "return"},  # Return stored as POSITIVE
]

parser = BaseParser()
result = parser.finalize(test_rows)

if result:
    summary = result.get("summary", {})
    print(f"Summary total_taxable: {summary.get('total_taxable')}")
    print(f"Summary sales_taxable: {summary.get('sales_taxable')}")
    print(f"Summary total_igst: {summary.get('total_igst')}")
    print(f"Summary total_cgst: {summary.get('total_cgst')}")
    print(f"Summary total_sgst: {summary.get('total_sgst')}")
    
    # Check invoice vs credit docs
    invoices = result.get("invoice_docs", [])
    credits = result.get("credit_docs", [])
    
    print(f"\nInvoice docs: {len(invoices)}")
    for inv in invoices:
        print(f"  - {inv['invoice_no']}: txval={inv['txval']}, cgst={inv['cgst_amt']}")
    
    print(f"Credit docs: {len(credits)}")
    for cred in credits:
        print(f"  - {cred['invoice_no']}: txval={cred['txval']}, cgst={cred['cgst_amt']}")
    
    # Verify calculations
    expected_net = 1000.0 - 500.0  # sales - returns
    actual_net = summary.get('total_taxable', 0)
    
    if abs(actual_net - expected_net) < 0.01:
        print(f"✓ NET calculation correct: {actual_net} == {expected_net}")
    else:
        print(f"✗ NET calculation WRONG: {actual_net} != {expected_net}")
        sys.exit(1)
    
    # Verify suppval would be sales (1000)
    sales_tax = summary.get('sales_taxable', 0)
    if abs(sales_tax - 1000.0) < 0.01:
        print(f"✓ sales_taxable correct for suppval: {sales_tax}")
    else:
        print(f"✗ sales_taxable WRONG: {sales_tax} != 1000.0")
        sys.exit(1)

# Test 2: Verify AutoMerge creates both suppliers in clttx
print("\n\nTest 2: Verify AutoMerge builds clttx with both suppliers")
print("-" * 60)

# Create test invoice and credit doc arrays
test_invoice_docs = [
    {"invoice_no": "A001", "pos": "07", "txval": 2000.0, "igst_amt": 0.0, "cgst_amt": 180.0, "sgst_amt": 180.0, "txn_type": "sale"},
]

test_credit_docs = [
    {"invoice_no": "A002", "pos": "07", "txval": 500.0, "igst_amt": 0.0, "cgst_amt": 45.0, "sgst_amt": 45.0, "txn_type": "return"},
]

# Create supplier data structure
supplier_data = {
    "07AARCM9332R1CQ": {
        "summary": {
            "rows": [],
            "total_taxable": 1500.0,  # 2000 - 500
            "total_igst": 0.0,
            "total_cgst": 135.0,  # 180 - 45
            "total_sgst": 135.0,
            "sales_taxable": 2000.0,  # For suppval
            "sales_igst": 0.0,
            "sales_cgst": 180.0,
            "sales_sgst": 180.0,
        },
        "invoice_docs": test_invoice_docs,
        "credit_docs": test_credit_docs,
    }
}

# Test merge
auto_merge = AutoMergeParser()
all_rows = test_invoice_docs + test_credit_docs

result = auto_merge._merge_results(all_rows, supplier_data)

if result:
    clttx = result.get("clttx", [])
    print(f"Number of suppliers in clttx: {len(clttx)}")
    
    for supplier in clttx:
        etin = supplier.get("etin", "")
        suppval = supplier.get("suppval", 0)
        print(f"  - {etin}: suppval={suppval}")
    
    # Check that both suppliers exist
    etins = [s.get("etin") for s in clttx]
    if "07AARCM9332R1CQ" in etins:
        print("✓ Meesho in clttx")
    else:
        print("✗ Meesho missing from clttx")
    
    if "07AAICA3918J1CV" in etins:
        print("✓ Amazon in clttx (empty)")
    else:
        print("✗ Amazon missing from clttx")
    
    # Check suppval for Meesho (should be 2000, not 1500)
    meesho = next((s for s in clttx if s.get("etin") == "07AARCM9332R1CQ"), None)
    if meesho:
        suppval = meesho.get("suppval", 0)
        if abs(suppval - 2000.0) < 0.01:
            print(f"✓ Meesho suppval correct: {suppval} (is sales total, not net)")
        else:
            print(f"✗ Meesho suppval WRONG: {suppval} != 2000.0")
            sys.exit(1)
    
    # Check summary total_taxable (should be 1500, the net)
    summary = result.get("summary", {})
    total_tax = summary.get("total_taxable", 0)
    if abs(total_tax - 1500.0) < 0.01:
        print(f"✓ Summary total_taxable correct (net): {total_tax}")
    else:
        print(f"✗ Summary total_taxable WRONG: {total_tax} != 1500.0")
        sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
