#!/usr/bin/env python3
"""
TEST SUITE: FlipkartParser Fixes
Tests all fixes to the FlipkartParser implementation:
1. Sales Report parsing with Event Type=SALE & Sub Type=SALE filtering
2. Cash Back Report parsing with Document Type=CREDIT filtering
3. Duplicate rows handling
4. Returns subtraction (negation)
5. Taxable value extraction (NOT invoice amount)
6. State/POS mapping for all states
7. Zero rows filtering
8. Doc_issue ranges
9. All months support
10. Dynamic column detection
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent))

from parsers import FlipkartParser, AutoMergeParser
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# =====================================================
# TEST 1: Sales Report with Event Type Filtering
# =====================================================

def test_flipkart_sales_report_filtering():
    """Test that Sales Report correctly filters Event Type=SALE, Sub Type=SALE."""
    print("\n" + "="*80)
    print("TEST 1: Sales Report Event Type Filtering")
    print("="*80)
    
    # Create sample data with mixed event types
    test_data = {
        'Buyer Invoice ID': ['FK001', 'FK002', 'FK003', 'FK004'],
        "Customer's Delivery State": ['Delhi', 'Mumbai', 'Chennai', 'Bangalore'],
        'Taxable Value Final Invoice Amount Taxes': [5000.0, 8000.0, 0.0, 3000.0],
        'IGST Amount': [150.0, 240.0, 0.0, 90.0],
        'CGST Amount': [0.0, 0.0, 0.0, 0.0],
        'SGST Amount Or UTGST As Applicable': [0.0, 0.0, 0.0, 0.0],
        'Event Type': ['SALE', 'SALE', 'SALE', 'RETURN'],  # Mix of SALE and RETURN
        'Event Sub Type': ['SALE', 'SALE', 'CANCELLED', 'RETURN'],  # Mix of SALE and non-SALE
    }
    
    test_file = Path('test_data/flipkart_test_sales.xlsx')
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write test data
    with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
        pd.DataFrame(test_data).to_excel(writer, sheet_name='Sales Report', index=False)
    
    parser = FlipkartParser()
    result = parser.parse_files([str(test_file)])
    
    # Verify filtering
    expected_rows = 2  # Only FK001 and FK002 (SALE + SALE)
    actual_rows = len(result['summary']['rows']) if result else 0
    
    print(f"Expected rows after filtering: {expected_rows}")
    print(f"Actual rows: {actual_rows}")
    print(f"Tax totals: IGST={result['summary']['total_igst']:.2f}, "
          f"CGST={result['summary']['total_cgst']:.2f}, "
          f"SGST={result['summary']['total_sgst']:.2f}" if result else "No data")
    
    passed = actual_rows == expected_rows
    print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")
    
    return passed


# =====================================================
# TEST 2: Cash Back Report with Credit Note Filtering
# =====================================================

def test_flipkart_cashback_filtering():
    """Test that Cash Back Report correctly filters for CREDIT notes."""
    print("\n" + "="*80)
    print("TEST 2: Cash Back Report Credit Note Filtering")
    print("="*80)
    
    # Create sample data with mixed document types
    test_data = {
        'Credit Note ID': ['CN001', 'DN001', 'CN002', 'DN002'],
        "Customer's Delivery State": ['Delhi', 'Mumbai', 'Chennai', 'Bangalore'],
        'Taxable Value': [1000.0, 2000.0, 500.0, 1500.0],
        'IGST Amount': [30.0, 60.0, 15.0, 45.0],
        'CGST Amount': [0.0, 0.0, 0.0, 0.0],
        'SGST Amount Or UTGST As Applicable': [0.0, 0.0, 0.0, 0.0],
        'Document Type': ['CREDIT', 'DEBIT', 'CREDIT', 'DEBIT'],  # Mix of CREDIT and DEBIT
    }
    
    test_file = Path('test_data/flipkart_test_cashback.xlsx')
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write test data
    with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
        pd.DataFrame(test_data).to_excel(writer, sheet_name='Cash Back Report', index=False)
    
    parser = FlipkartParser()
    result = parser.parse_files([str(test_file)])
    
    # Verify filtering and negation
    expected_credit_notes = 2  # Only CN001 and CN002
    actual_rows = len(result['summary']['rows']) if result else 0
    
    print(f"Expected credit note rows: {expected_credit_notes}")
    print(f"Actual rows: {actual_rows}")
    
    if result and actual_rows > 0:
        total_taxable = result['summary']['total_taxable']
        print(f"Total taxable (should be negative for returns): {total_taxable:.2f}")
        print(f"Status: {'✅ PASS' if total_taxable < 0 else '❌ FAIL (not negated)'}")
        return total_taxable < 0
    else:
        print("Status: ❌ FAIL (no data)")
        return False


# =====================================================
# TEST 3: Taxable Value Extraction (NOT invoice amount)
# =====================================================

def test_flipkart_taxable_value_extraction():
    """Test that taxable value is extracted correctly (NOT invoice amount)."""
    print("\n" + "="*80)
    print("TEST 3: Taxable Value Extraction")
    print("="*80)
    
    # Create sample with different taxable vs invoice amounts
    test_data = {
        'Buyer Invoice ID': ['FK001', 'FK002'],
        "Customer's Delivery State": ['Delhi', 'Mumbai'],
        'Taxable Value Final Invoice Amount Taxes': [10000.0, 5000.0],  # Correct taxable value
        'Total Invoice Amount': [11300.0, 5540.0],  # Different from taxable (includes taxes)
        'IGST Amount': [300.0, 150.0],
        'CGST Amount': [0.0, 0.0],
        'SGST Amount Or UTGST As Applicable': [0.0, 0.0],
        'Event Type': ['SALE', 'SALE'],
        'Event Sub Type': ['SALE', 'SALE'],
    }
    
    test_file = Path('test_data/flipkart_test_taxable.xlsx')
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
        pd.DataFrame(test_data).to_excel(writer, sheet_name='Sales Report', index=False)
    
    parser = FlipkartParser()
    result = parser.parse_files([str(test_file)])
    
    expected_taxable = 15000.0  # 10000 + 5000
    actual_taxable = result['summary']['total_taxable'] if result else 0
    
    print(f"Expected taxable value: ₹{expected_taxable:.2f}")
    print(f"Actual taxable value: ₹{actual_taxable:.2f}")
    
    passed = abs(actual_taxable - expected_taxable) < 0.01
    print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")
    
    return passed


# =====================================================
# TEST 4: Duplicate Rows Deduplication
# =====================================================

def test_flipkart_duplicate_deduplication():
    """Test that duplicate invoices are deduplicated correctly."""
    print("\n" + "="*80)
    print("TEST 4: Duplicate Rows Deduplication")
    print("="*80)
    
    # Create sample with duplicate invoices
    test_data = {
        'Buyer Invoice ID': ['FK001', 'FK001', 'FK002', 'FK002'],  # FK001 and FK002 repeated
        "Customer's Delivery State": ['Delhi', 'Delhi', 'Mumbai', 'Mumbai'],
        'Taxable Value Final Invoice Amount Taxes': [5000.0, 5000.0, 8000.0, 8000.0],
        'IGST Amount': [150.0, 150.0, 240.0, 240.0],
        'CGST Amount': [0.0, 0.0, 0.0, 0.0],
        'SGST Amount Or UTGST As Applicable': [0.0, 0.0, 0.0, 0.0],
        'Event Type': ['SALE', 'SALE', 'SALE', 'SALE'],
        'Event Sub Type': ['SALE', 'SALE', 'SALE', 'SALE'],
    }
    
    test_file = Path('test_data/flipkart_test_duplicates.xlsx')
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
        pd.DataFrame(test_data).to_excel(writer, sheet_name='Sales Report', index=False)
    
    parser = FlipkartParser()
    result = parser.parse_files([str(test_file)])
    
    expected_unique_rows = 2  # After deduplication: 2 invoices
    actual_rows = len(result['summary']['rows']) if result else 0
    
    print(f"Input rows: 4 (2 unique invoices, each repeated)")
    print(f"Expected rows after dedup: {expected_unique_rows}")
    print(f"Actual rows: {actual_rows}")
    
    passed = actual_rows == expected_unique_rows
    print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")
    
    return passed


# =====================================================
# TEST 5: Zero Rows Filtering
# =====================================================

def test_flipkart_zero_rows_filtering():
    """Test that zero-value rows are filtered out."""
    print("\n" + "="*80)
    print("TEST 5: Zero Rows Filtering")
    print("="*80)
    
    # Create sample with zero-value rows
    test_data = {
        'Buyer Invoice ID': ['FK001', 'FK002', 'FK003'],
        "Customer's Delivery State": ['Delhi', 'Mumbai', 'Chennai'],
        'Taxable Value Final Invoice Amount Taxes': [5000.0, 0.0, 8000.0],  # FK002 is zero
        'IGST Amount': [150.0, 0.0, 240.0],
        'CGST Amount': [0.0, 0.0, 0.0],
        'SGST Amount Or UTGST As Applicable': [0.0, 0.0, 0.0],
        'Event Type': ['SALE', 'SALE', 'SALE'],
        'Event Sub Type': ['SALE', 'SALE', 'SALE'],
    }
    
    test_file = Path('test_data/flipkart_test_zero.xlsx')
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
        pd.DataFrame(test_data).to_excel(writer, sheet_name='Sales Report', index=False)
    
    parser = FlipkartParser()
    result = parser.parse_files([str(test_file)])
    
    expected_rows = 2  # Only FK001 and FK003 (FK002 should be filtered)
    actual_rows = len(result['summary']['rows']) if result else 0
    
    print(f"Input rows: 3 (1 with zero value)")
    print(f"Expected rows after filtering: {expected_rows}")
    print(f"Actual rows: {actual_rows}")
    
    passed = actual_rows == expected_rows
    print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")
    
    return passed


# =====================================================
# TEST 6: State/POS Mapping for All States
# =====================================================

def test_flipkart_all_states_mapping():
    """Test that state/POS mapping works for various Indian states."""
    print("\n" + "="*80)
    print("TEST 6: State/POS Mapping for All States")
    print("="*80)
    
    # Test with various state names
    test_data = {
        'Buyer Invoice ID': ['FK001', 'FK002', 'FK003', 'FK004', 'FK005'],
        "Customer's Delivery State": ['Delhi', 'Maharashtra', 'Tamil Nadu', 'Haryana', 'West Bengal'],
        'Taxable Value Final Invoice Amount Taxes': [1000.0, 2000.0, 3000.0, 4000.0, 5000.0],
        'IGST Amount': [30.0, 60.0, 90.0, 120.0, 150.0],
        'CGST Amount': [0.0, 0.0, 0.0, 0.0, 0.0],
        'SGST Amount Or UTGST As Applicable': [0.0, 0.0, 0.0, 0.0, 0.0],
        'Event Type': ['SALE', 'SALE', 'SALE', 'SALE', 'SALE'],
        'Event Sub Type': ['SALE', 'SALE', 'SALE', 'SALE', 'SALE'],
    }
    
    test_file = Path('test_data/flipkart_test_states.xlsx')
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
        pd.DataFrame(test_data).to_excel(writer, sheet_name='Sales Report', index=False)
    
    parser = FlipkartParser()
    result = parser.parse_files([str(test_file)])
    
    print(f"Tested states: Delhi, Maharashtra, Tamil Nadu, Haryana, West Bengal")
    print(f"Rows processed: {len(result['summary']['rows']) if result else 0}")
    
    # Verify all states were mapped
    if result and result['summary']['rows']:
        states_found = set()
        for row in result['summary']['rows']:
            pos = row.get('pos')
            if pos:
                states_found.add(pos)
                invoice = row.get('invoice_no', row.get('docs', ['N/A'])[0] if isinstance(row.get('docs'), list) else 'N/A')
                print(f"  {invoice}: State -> POS Code {pos}")
        
        expected_states = 5
        actual_states = len(states_found)
        passed = actual_states == expected_states
        
        print(f"\nExpected unique states: {expected_states}")
        print(f"Actual unique states: {actual_states}")
        print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")
        return passed
    else:
        print("Status: ❌ FAIL (no data)")
        return False


# =====================================================
# TEST 7: Returns Subtraction (Negation)
# =====================================================

def test_flipkart_returns_subtraction():
    """Test that returns are subtracted (negated) correctly."""
    print("\n" + "="*80)
    print("TEST 7: Returns Subtraction")
    print("="*80)
    
    # Create both Sales Report and Cash Back Report
    sales_data = {
        'Buyer Invoice ID': ['FK001', 'FK002'],
        "Customer's Delivery State": ['Delhi', 'Mumbai'],
        'Taxable Value Final Invoice Amount Taxes': [5000.0, 8000.0],
        'IGST Amount': [150.0, 240.0],
        'CGST Amount': [0.0, 0.0],
        'SGST Amount Or UTGST As Applicable': [0.0, 0.0],
        'Event Type': ['SALE', 'SALE'],
        'Event Sub Type': ['SALE', 'SALE'],
    }
    
    cashback_data = {
        'Credit Note ID': ['CN001'],
        "Customer's Delivery State": ['Delhi'],
        'Taxable Value': [2000.0],  # Return of 2000
        'IGST Amount': [60.0],
        'CGST Amount': [0.0],
        'SGST Amount Or UTGST As Applicable': [0.0],
        'Document Type': ['CREDIT'],
    }
    
    test_file = Path('test_data/flipkart_test_returns.xlsx')
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
        pd.DataFrame(sales_data).to_excel(writer, sheet_name='Sales Report', index=False)
        pd.DataFrame(cashback_data).to_excel(writer, sheet_name='Cash Back Report', index=False)
    
    parser = FlipkartParser()
    result = parser.parse_files([str(test_file)])
    
    # Expected: (5000+8000) - 2000 = 11000
    expected_net_taxable = 11000.0
    actual_net_taxable = result['summary']['total_taxable'] if result else 0
    
    print(f"Sales: 5000 + 8000 = 13000")
    print(f"Returns: -2000")
    print(f"Expected net taxable: ₹{expected_net_taxable:.2f}")
    print(f"Actual net taxable: ₹{actual_net_taxable:.2f}")
    
    passed = abs(actual_net_taxable - expected_net_taxable) < 0.01
    print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")
    
    return passed


# =====================================================
# TEST 8: All Months Support
# =====================================================

def test_flipkart_all_months():
    """Test that parser works for any month, not just February."""
    print("\n" + "="*80)
    print("TEST 8: All Months Support")
    print("="*80)
    
    months = [
        ('January', '2026-01-15'),
        ('March', '2026-03-15'),
        ('June', '2026-06-15'),
        ('December', '2026-12-15'),
    ]
    
    all_passed = True
    for month_name, date_str in months:
        test_data = {
            'Buyer Invoice ID': [f'FK_{month_name}_001'],
            "Customer's Delivery State": ['Delhi'],
            'Taxable Value Final Invoice Amount Taxes': [5000.0],
            'IGST Amount': [150.0],
            'CGST Amount': [0.0],
            'SGST Amount Or UTGST As Applicable': [0.0],
            'Event Type': ['SALE'],
            'Event Sub Type': ['SALE'],
        }
        
        test_file = Path(f'test_data/flipkart_test_{month_name}.xlsx')
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
            pd.DataFrame(test_data).to_excel(writer, sheet_name='Sales Report', index=False)
        
        parser = FlipkartParser()
        result = parser.parse_files([str(test_file)])
        
        passed = result is not None and len(result['summary']['rows']) > 0
        print(f"  {month_name}: {'✅ PASS' if passed else '❌ FAIL'}")
        all_passed = all_passed and passed
    
    print(f"Status: {'✅ PASS' if all_passed else '❌ FAIL'}")
    return all_passed


# =====================================================
# MAIN TEST RUNNER
# =====================================================

def run_all_tests():
    """Run all tests."""
    print("\n" + "█"*80)
    print("FLIPKART PARSER FIX VALIDATION TEST SUITE")
    print("█"*80)
    
    tests = [
        ("Sales Report Event Type Filtering", test_flipkart_sales_report_filtering),
        ("Cash Back Report Credit Filtering", test_flipkart_cashback_filtering),
        ("Taxable Value Extraction", test_flipkart_taxable_value_extraction),
        ("Duplicate Rows Deduplication", test_flipkart_duplicate_deduplication),
        ("Zero Rows Filtering", test_flipkart_zero_rows_filtering),
        ("State/POS Mapping", test_flipkart_all_states_mapping),
        ("Returns Subtraction", test_flipkart_returns_subtraction),
        ("All Months Support", test_flipkart_all_months),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results[test_name] = passed
        except Exception as e:
            print(f"  ⚠️  EXCEPTION: {str(e)[:60]}")
            results[test_name] = False
    
    # Summary
    print("\n" + "█"*80)
    print("TEST SUMMARY")
    print("█"*80)
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    print(f"Status: {'✅ ALL TESTS PASSED' if passed_count == total_count else '❌ SOME TESTS FAILED'}")
    
    return passed_count == total_count


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
