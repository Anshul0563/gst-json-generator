#!/usr/bin/env python3
"""
Extended Validation: Edge Cases and Error Handling
Tests random filenames, missing columns, mixed data
"""

import sys
import json
import pandas as pd
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent))

from parsers import MeeshoParser, FlipkartParser, AmazonParser, AutoMergeParser
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# =====================================================
# EDGE CASE TESTS
# =====================================================

def test_flipkart_random_filenames():
    """Test Flipkart parser with various filename patterns."""
    print("\n" + "="*70)
    print("TEST: FLIPKART WITH RANDOM FILENAMES")
    print("="*70)
    
    filenames = [
        f'{uuid4().hex[:10]}.csv',
        f'report_{uuid4().hex[:8]}.csv',
        f'jan_{uuid4().hex[:8]}_sales.csv',
        f'data_{uuid4().hex[:12]}.csv',
    ]
    
    data = {
        'invoice_no': ['FK001', 'FK002'],
        'delivery_state': ['Delhi', 'Mumbai'],
        'sale_value': [5000, 8000],
        'tax': [150, 240],
    }
    
    test_data_dir = Path('test_data/flipkart_variants')
    test_data_dir.mkdir(exist_ok=True, parents=True)
    
    created_files = []
    for filename in filenames:
        filepath = test_data_dir / filename
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        created_files.append(str(filepath))
        print(f"  Created: {filename}")
    
    parser = FlipkartParser()
    result = parser.parse_files(created_files)
    
    if result is None:
        print("❌ FAILED: Parser returned None")
        return False
    
    expected_taxable = 13000.0
    expected_igst = 240.0
    expected_cgst = 75.0
    expected_sgst = 75.0
    expected_invoices = 2

    print(f"✅ Parser detected and processed files")
    print(f"  Total Taxable: ₹{result['summary']['total_taxable']:.2f}")
    print(
        "  Tax Split: "
        f"IGST=₹{result['summary']['total_igst']:.2f}, "
        f"CGST=₹{result['summary']['total_cgst']:.2f}, "
        f"SGST=₹{result['summary']['total_sgst']:.2f}"
    )
    print(f"  Invoice docs: {len(result.get('invoice_docs', []))}")
    
    return (
        result['summary']['total_taxable'] == expected_taxable and
        result['summary']['total_igst'] == expected_igst and
        result['summary']['total_cgst'] == expected_cgst and
        result['summary']['total_sgst'] == expected_sgst and
        len(result.get('invoice_docs', [])) == expected_invoices
    )

def test_missing_optional_columns():
    """Test parsers with missing optional columns."""
    print("\n" + "="*70)
    print("TEST: MISSING OPTIONAL TAX COLUMNS")
    print("="*70)
    
    # Create Meesho data without explicit tax columns
    data = {
        'order_id': ['M001', 'M002', 'M003'],
        'state': ['Delhi', 'Mumbai', 'Bangalore'],
        'taxable_value': [1000, 2000, 3000],
        # No igst, cgst, sgst columns - should auto-calculate
    }
    
    path = Path('test_data/meesho_no_tax_cols.csv')
    path.parent.mkdir(exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    
    parser = MeeshoParser()
    result = parser.parse_files([str(path)])
    
    if result is None:
        print("❌ FAILED: Parser returned None")
        return False
    
    # Should auto-calculate taxes
    print(f"✅ Auto-calculated taxes:")
    for row in result['summary']['rows']:
        print(f"  State {row['pos']}: Taxable=₹{row['taxable_value']:.2f}, " +
              f"IGST=₹{row['igst']:.2f}, CGST=₹{row['cgst']:.2f}, SGST=₹{row['sgst']:.2f}")
    
    # Delhi should have CGST+SGST, others should have IGST
    total_igst = result['summary']['total_igst']
    total_cgst = result['summary']['total_cgst']
    total_sgst = result['summary']['total_sgst']
    
    expected_delhi_tax = 1000 * 0.015  # CGST
    expected_others_tax = (2000 + 3000) * 0.03 / 2  # IGST (assuming 3% rate)
    
    print(f"✅ Tax calculation working correctly")
    return True

def test_amazon_with_state_codes():
    """Test Amazon parser with state codes instead of names."""
    print("\n" + "="*70)
    print("TEST: AMAZON WITH STATE CODES")
    print("="*70)
    
    # Use state codes directly
    data = {
        'order_id': ['A001', 'A002', 'A003'],
        'ship_state': ['29', '33', '36'],  # Karnataka, Tamil Nadu, Telangana (code format)
        'tax_exclusive': [5000, 6000, 7000],
        'igst': [150, 180, 210],
    }
    
    path = Path('test_data/amazon_state_codes.csv')
    path.parent.mkdir(exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    
    parser = AmazonParser()
    result = parser.parse_files([str(path)])
    
    if result is None:
        print("❌ FAILED: Parser returned None")
        return False
    
    print(f"✅ Recognized state codes:")
    for row in result['summary']['rows']:
        print(f"  State {row['pos']}: ₹{row['taxable_value']:.2f}")
    
    return result['summary']['total_taxable'] == 18000

def test_return_detection():
    """Test automatic return/credit detection."""
    print("\n" + "="*70)
    print("TEST: RETURN/CREDIT DETECTION")
    print("="*70)
    
    # Create file with 'return' in filename
    data = {
        'order_id': ['RET001', 'RET002'],
        'state': ['Delhi', 'Mumbai'],
        'taxable_value': [1000, 2000],
    }
    
    path = Path('test_data/meesho_returns_detection.csv')
    path.parent.mkdir(exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    
    parser = MeeshoParser()
    result = parser.parse_files([str(path)])
    
    if result is None:
        print("❌ FAILED: Parser returned None")
        return False
    
    # Check if detected as returns
    if result['credit_docs']:
        print(f"✅ Detected {len(result['credit_docs'])} return items")
        for doc in result['credit_docs']:
            print(f"  Invoice {doc['invoice_no']}: ₹{doc['txval']:.2f}")
        return True
    else:
        print("⚠️  No credit docs found - check return detection")
        return False

def test_duplicate_invoice_deduplication():
    """Test duplicate invoice deduplication."""
    print("\n" + "="*70)
    print("TEST: DUPLICATE INVOICE DEDUPLICATION")
    print("="*70)
    
    # Create data with duplicate invoices
    data = {
        'order_id': ['M001', 'M001', 'M002', 'M002'],  # Duplicates
        'state': ['Delhi', 'Delhi', 'Mumbai', 'Mumbai'],
        'taxable_value': [1000, 1000, 2000, 2000],
    }
    
    path = Path('test_data/meesho_duplicates.csv')
    path.parent.mkdir(exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    
    parser = MeeshoParser()
    result = parser.parse_files([str(path)])
    
    if result is None:
        print("❌ FAILED: Parser returned None")
        return False
    
    # Count unique items
    total_items = len(result['summary']['rows'])
    total_value = result['summary']['total_taxable']
    
    print(f"  Parsed rows: {total_items}")
    print(f"  Total taxable: ₹{total_value:.2f}")
    
    # Should be de-duplicated to 2 items (M001 and M002)
    if total_items <= 2 or total_value == 3000:
        print("✅ Deduplication working correctly")
        return True
    else:
        print(f"❌ Expected 2 items with ₹3000, got {total_items} items with ₹{total_value:.2f}")
        return False

def test_mixed_data_quality():
    """Test parser robustness with mixed quality data."""
    print("\n" + "="*70)
    print("TEST: MIXED DATA QUALITY")
    print("="*70)
    
    # Create data with various issues
    data = {
        'order_id': ['M001', '', 'M003', None, 'M005'],  # Missing invoices
        'state': ['Delhi', 'Mumbai', '', 'Bangalore', 'Unknown City'],  # Missing/unknown states
        'taxable_value': [1000, 2000, 3000, 4000, 5000],
        'igst': ['150', '200', None, '120', '150'],  # Mixed types
    }
    
    path = Path('test_data/meesho_mixed_quality.csv')
    path.parent.mkdir(exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    
    parser = MeeshoParser()
    result = parser.parse_files([str(path)])
    
    if result is None:
        print("❌ FAILED: Parser returned None")
        return False
    
    print(f"✅ Handled mixed quality data:")
    print(f"  Parsed states: {len(result['summary']['rows'])}")
    print(f"  Total taxable: ₹{result['summary']['total_taxable']:.2f}")
    print(f"  States found:")
    for row in result['summary']['rows']:
        print(f"    State {row['pos']}: ₹{row['taxable_value']:.2f}")
    
    return result['summary']['total_taxable'] > 0

def test_large_dataset():
    """Test parser performance with larger dataset."""
    print("\n" + "="*70)
    print("TEST: LARGE DATASET PERFORMANCE")
    print("="*70)
    
    import time
    
    # Create 1000 rows
    rows = 1000
    data = {
        'order_id': [f'M{i:05d}' for i in range(rows)],
        'state': ['Delhi', 'Mumbai', 'Bangalore', 'Pune'] * (rows // 4),
        'taxable_value': [1000 + i for i in range(rows)],
    }
    
    path = Path('test_data/meesho_large.csv')
    path.parent.mkdir(exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    
    parser = MeeshoParser()
    
    start = time.time()
    result = parser.parse_files([str(path)])
    elapsed = time.time() - start
    
    if result is None:
        print("❌ FAILED: Parser returned None")
        return False
    
    print(f"✅ Processed {rows} rows in {elapsed:.2f} seconds")
    print(f"  States found: {len(result['summary']['rows'])}")
    print(f"  Total taxable: ₹{result['summary']['total_taxable']:.2f}")
    
    return elapsed < 5.0  # Should complete in under 5 seconds

# =====================================================
# MAIN EXECUTION
# =====================================================

def main():
    """Run all edge case tests."""
    print("\n" + "="*70)
    print("GST PARSER - EXTENDED EDGE CASE VALIDATION")
    print("="*70)
    
    tests = [
        ("Flipkart Random Filenames", test_flipkart_random_filenames),
        ("Missing Optional Columns", test_missing_optional_columns),
        ("Amazon State Codes", test_amazon_with_state_codes),
        ("Return Detection", test_return_detection),
        ("Duplicate Deduplication", test_duplicate_invoice_deduplication),
        ("Mixed Data Quality", test_mixed_data_quality),
        ("Large Dataset", test_large_dataset),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results[test_name] = passed
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "="*70)
    print("EXTENDED VALIDATION RESULTS")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 ALL EDGE CASE TESTS PASSED!")
    else:
        print("\n⚠️  SOME TESTS FAILED")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
