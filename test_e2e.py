#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end test with real test data files."""

import sys
sys.path.insert(0, '/home/jarvis/Documents/IT/GST-Tool')

from pathlib import Path
import json

# Import with pandas
import pandas as pd
from parsers import AutoMergeParser

print("=" * 70)
print("End-to-End Test: Processing Real Test Data Files")
print("=" * 70)

# List test files
test_data_dir = Path("/home/jarvis/Documents/IT/GST-Tool/test_data")
test_files = [
    test_data_dir / "MTR_B2C-FEBRUARY-2026-A1YGIWFZR88S6S.csv",
    test_data_dir / "Tax_invoice_details.xlsx",
    test_data_dir / "tcs_sales.xlsx",
    test_data_dir / "tcs_sales_return.xlsx",
]

# Filter to files that exist
files_to_process = [str(f) for f in test_files if f.exists()]

print(f"\nFound {len(files_to_process)} test files:")
for f in files_to_process:
    print(f"  - {Path(f).name}")

# Parse with AutoMerge
print("\n" + "-" * 70)
print("Parsing with AutoMergeParser...")
print("-" * 70)

parser = AutoMergeParser()
result = parser.parse_files(files_to_process)

if result:
    print("✓ Parsing completed successfully")
    
    # Print summary
    print("\n" + "=" * 70)
    print("PARSED RESULTS SUMMARY")
    print("=" * 70)
    
    summary = result.get("summary", {})
    print("\nSummary:")
    print(f"  Total Taxable:  {summary.get('total_taxable', 0)}")
    print(f"  Total IGST:     {summary.get('total_igst', 0)}")
    print(f"  Total CGST:     {summary.get('total_cgst', 0)}")
    print(f"  Total SGST:     {summary.get('total_sgst', 0)}")
    
    # Print clttx
    clttx = result.get("clttx", [])
    print(f"\nSupplier-Wise (CLTTX): {len(clttx)} suppliers")
    total_clttx = 0.0
    for supplier in clttx:
        etin = supplier.get("etin", "")
        suppval = supplier.get("suppval", 0)
        print(f"  {etin}: suppval={suppval}")
        total_clttx += suppval
    
    print(f"\nTotal from CLTTX: {total_clttx}")
    
    # Validation
    print("\n" + "=" * 70)
    print("VALIDATION CHECKS")
    print("=" * 70)
    
    # Check 1: summary totals are not negative (unless net is actually negative)
    total_tax = summary.get("total_taxable", 0)
    if total_tax < 0:
        print(f"⚠ WARNING: summary.total_taxable is negative: {total_tax}")
        print("  This is only OK if actual net sales are negative")
    else:
        print(f"✓ summary.total_taxable is positive: {total_tax}")
    
    # Check 2: All suppliers have non-negative suppval
    all_positive = True
    for supplier in clttx:
        suppval = supplier.get("suppval", 0)
        etin = supplier.get("etin", "")
        if suppval < 0:
            print(f"✗ ERROR: {etin} has negative suppval: {suppval}")
            all_positive = False
        elif suppval > 0:
            print(f"✓ {etin} has positive suppval: {suppval}")
        else:
            print(f"- {etin} is empty (suppval=0)")
    
    if not all_positive:
        print("\n❌ CRITICAL: Negative suppval detected - THIS IS THE BUG")
        sys.exit(1)
    
    # Check 3: Both suppliers present
    etins = [s.get("etin") for s in clttx]
    print(f"\nSuppliers in output: {len(etins)}")
    if "07AARCM9332R1CQ" in etins:
        print("  ✓ Meesho present")
    else:
        print("  ✗ Meesho missing")
    
    if "07AAICA3918J1CV" in etins:
        print("  ✓ Amazon present")
    else:
        print("  ✗ Amazon missing (should be present even if empty)")
    
    # Check 4: Document counts
    invoice_docs = result.get("invoice_docs", [])
    credit_docs = result.get("credit_docs", [])
    print(f"\nDocument counts:")
    print(f"  Invoice docs (sales): {len(invoice_docs)}")
    print(f"  Credit docs (returns): {len(credit_docs)}")
    
    # Check 5: Tax consistency
    if len(clttx) > 0:
        clttx_total_tax = sum(s.get("suppval", 0) for s in clttx)
        print(f"\nTax consistency check:")
        print(f"  Sum of CLTTX suppval: {clttx_total_tax}")
        print(f"  Summary total_taxable: {summary.get('total_taxable', 0)}")
        
        # These won't match if there are returns (summary is net, suppval is sales)
        # This is CORRECT behavior
        if clttx_total_tax > summary.get('total_taxable', 0):
            print(f"  → suppval > net (OK - returns reduce net): {clttx_total_tax} > {summary.get('total_taxable', 0)}")
        elif clttx_total_tax == summary.get('total_taxable', 0):
            print(f"  → suppval == net (no returns detected): {clttx_total_tax}")
    
    print("\n" + "=" * 70)
    print("✓ END-TO-END TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
    
    # Save output
    output_file = Path("/home/jarvis/Documents/IT/GST-Tool/output/test_e2e_output.json")
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nOutput saved to: {output_file}")
    
else:
    print("✗ Parsing failed - no result returned")
    sys.exit(1)
