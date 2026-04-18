#!/usr/bin/env python3
"""
Proof-Based Validation Suite for GST Parsers
Tests with real sample data and compares against expected output
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers import MeeshoParser, FlipkartParser, AmazonParser, AutoMergeParser
from gst_builder import GSTBuilder
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# =====================================================
# TEST DATA SETUP
# =====================================================

def create_meesho_sample():
    """Create realistic Meesho sample CSV."""
    data = {
        'order_id': ['MES001', 'MES002', 'MES003', 'MES004', 'MES005'],
        'state': ['Delhi', 'Maharashtra', 'Karnataka', 'Delhi', 'Gujarat'],
        'taxable_value': [1000, 2000, 3000, 1500, 2500],
        'igst': [0, 60, 90, 0, 75],
        'cgst': [15, 0, 0, 22.5, 0],
        'sgst': [15, 0, 0, 22.5, 0],
    }
    df = pd.DataFrame(data)
    path = Path('test_data/meesho_sales.csv')
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Created Meesho sample: {path}")
    return path

def create_meesho_return():
    """Create realistic Meesho returns CSV."""
    data = {
        'order_id': ['MES-RET001', 'MES-RET002'],
        'state': ['Delhi', 'Maharashtra'],
        'taxable_value': [500, 1000],
        'igst': [0, 30],
        'cgst': [7.5, 0],
        'sgst': [7.5, 0],
    }
    df = pd.DataFrame(data)
    path = Path('test_data/meesho_returns_credit_note.csv')
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Created Meesho returns: {path}")
    return path

def create_flipkart_sample():
    """Create realistic Flipkart sample CSV."""
    data = {
        'invoice_no': ['FK001', 'FK002', 'FK003'],
        'delivery_state': ['Haryana', 'Tamil Nadu', 'West Bengal'],
        'sale_value': [5000, 10000, 7500],
        'tax': [150, 300, 225],
    }
    df = pd.DataFrame(data)
    path = Path('test_data/flipkart_sales.csv')
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Created Flipkart sample: {path}")
    return path

def create_amazon_csv_sample():
    """Create realistic Amazon sample CSV."""
    data = {
        'order_id': ['AMZ001', 'AMZ002', 'AMZ003', 'AMZ004'],
        'ship_state': ['Bangalore', 'Chennai', 'Hyderabad', 'Pune'],
        'tax_exclusive': [2000, 3000, 4000, 2500],
        'igst': [60, 90, 120, 75],
    }
    df = pd.DataFrame(data)
    path = Path('test_data/amazon_sales.csv')
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Created Amazon sample: {path}")
    return path

# =====================================================
# VALIDATION FUNCTIONS
# =====================================================

def validate_parser_output(result, parser_name, expected_totals=None):
    """Validate parser output structure and values."""
    print(f"\n{'='*70}")
    print(f"VALIDATING {parser_name}")
    print(f"{'='*70}")
    
    if result is None:
        print("❌ FAILED: Parser returned None")
        return False
    
    # Check structure
    required_keys = ['summary', 'credit_docs']
    for key in required_keys:
        if key not in result:
            print(f"❌ FAILED: Missing key '{key}'")
            return False
    
    summary = result['summary']
    print(f"\n📊 Summary:")
    print(f"  Platform: {result.get('platform', 'N/A')}")
    print(f"  ETIN: {result.get('etin', 'N/A')}")
    print(f"  States: {len(summary.get('rows', []))} unique states")
    print(f"  Total Taxable: ₹{summary.get('total_taxable', 0):.2f}")
    print(f"  Total IGST: ₹{summary.get('total_igst', 0):.2f}")
    print(f"  Total CGST: ₹{summary.get('total_cgst', 0):.2f}")
    print(f"  Total SGST: ₹{summary.get('total_sgst', 0):.2f}")
    
    # Validate totals if provided
    if expected_totals:
        print(f"\n🔍 Validating against expected totals:")
        all_match = True
        
        for key, expected_val in expected_totals.items():
            actual_val = summary.get(key, 0)
            match = abs(actual_val - expected_val) < 0.01
            status = "✅" if match else "❌"
            print(f"  {status} {key}: expected {expected_val:.2f}, got {actual_val:.2f}")
            if not match:
                all_match = False
        
        return all_match
    
    print("\n✅ Structure validation passed")
    return True

def compare_state_totals(result, parser_name):
    """Show detailed state-wise breakdown."""
    print(f"\n📍 State-wise breakdown for {parser_name}:")
    summary = result.get('summary', {})
    rows = summary.get('rows', [])
    
    for row in rows:
        print(f"  State {row['pos']}: Taxable=₹{row['taxable_value']:.2f}, " +
              f"IGST=₹{row['igst']:.2f}, CGST=₹{row['cgst']:.2f}, SGST=₹{row['sgst']:.2f}")
    
    if result.get('credit_docs'):
        print(f"\n💳 Returns/Credits: {len(result['credit_docs'])} items")
        for doc in result['credit_docs']:
            print(f"  Invoice {doc['invoice_no']}: ₹{doc['txval']:.2f}")

# =====================================================
# TEST EXECUTION
# =====================================================

def test_meesho_parser():
    """Test Meesho parser with sample data."""
    print("\n" + "="*70)
    print("TEST 1: MEESHO PARSER")
    print("="*70)
    
    # Create sample files
    meesho_sales = create_meesho_sample()
    meesho_returns = create_meesho_return()
    
    # Parse
    parser = MeeshoParser()
    result = parser.parse_files([str(meesho_sales), str(meesho_returns)])
    
    # Expected: 2 states (Delhi=07, Maharashtra=27, Karnataka=29, Gujarat=24)
    # Returns now reconcile against sales inside summary totals.
    # Delhi: 1000 + 1500 - 500 = 2000
    # Maharashtra: 2000 - 1000 = 1000
    # Karnataka: 3000
    # Gujarat: 2500
    
    expected = {
        'total_taxable': 8500,
        'total_igst': 195,
        'total_cgst': 30,
        'total_sgst': 30,
    }
    
    passed = validate_parser_output(result, "MEESHO", expected)
    compare_state_totals(result, "MEESHO")
    
    return passed, result

def test_flipkart_parser():
    """Test Flipkart parser with sample data."""
    print("\n" + "="*70)
    print("TEST 2: FLIPKART PARSER")
    print("="*70)
    
    flipkart_file = create_flipkart_sample()
    
    parser = FlipkartParser()
    result = parser.parse_files([str(flipkart_file)])
    
    # Expected: Haryana(06)=5000, Tamil Nadu(33)=10000, West Bengal(19)=7500
    expected = {
        'total_taxable': 5000 + 10000 + 7500,  # 22500
        'total_igst': 150 + 300 + 225,  # 675
        'total_cgst': 0,
        'total_sgst': 0,
    }
    
    passed = validate_parser_output(result, "FLIPKART", expected)
    compare_state_totals(result, "FLIPKART")
    
    return passed, result

def test_amazon_parser():
    """Test Amazon CSV parser with sample data."""
    print("\n" + "="*70)
    print("TEST 3: AMAZON CSV PARSER")
    print("="*70)
    
    amazon_file = create_amazon_csv_sample()
    
    parser = AmazonParser()
    result = parser.parse_files([str(amazon_file)])
    
    # Expected: All are other states (IGST)
    expected = {
        'total_taxable': 2000 + 3000 + 4000 + 2500,  # 11500
        'total_igst': 60 + 90 + 120 + 75,  # 345
        'total_cgst': 0,
        'total_sgst': 0,
    }
    
    passed = validate_parser_output(result, "AMAZON", expected)
    compare_state_totals(result, "AMAZON")
    
    return passed, result

def test_automerge_parser():
    """Test AutoMerge parser combining all platforms."""
    print("\n" + "="*70)
    print("TEST 4: AUTOMERGE PARSER (ALL PLATFORMS)")
    print("="*70)
    
    # Create all sample files
    create_meesho_sample()
    create_meesho_return()
    create_flipkart_sample()
    create_amazon_csv_sample()
    
    files = [
        'test_data/meesho_sales.csv',
        'test_data/meesho_returns_credit_note.csv',
        'test_data/flipkart_sales.csv',
        'test_data/amazon_sales.csv',
    ]
    
    parser = AutoMergeParser()
    result = parser.parse_files(files)
    
    # Total across all
    total_taxable = 8500 + (5000 + 10000 + 7500) + (2000 + 3000 + 4000 + 2500)
    total_igst = 195 + (150 + 300 + 225) + (60 + 90 + 120 + 75)
    total_cgst = 30
    total_sgst = 30
    
    expected = {
        'total_taxable': total_taxable,
        'total_igst': total_igst,
        'total_cgst': total_cgst,
        'total_sgst': total_sgst,
    }
    
    print(f"\n📊 CLTTX (Supplier Details):")
    for supplier in result.get('clttx', []):
        print(f"  ETIN: {supplier['etin']}")
        print(f"    Supply Value: ₹{supplier['suppval']:.2f}")
        print(f"    IGST: ₹{supplier['igst']:.2f}, CGST: ₹{supplier['cgst']:.2f}, SGST: ₹{supplier['sgst']:.2f}")
    
    passed = validate_parser_output(result, "AUTOMERGE", expected)
    compare_state_totals(result, "AUTOMERGE")
    
    return passed, result

def test_gst_builder_integration(automerge_result):
    """Test GST Builder with parser output."""
    print("\n" + "="*70)
    print("TEST 5: GST BUILDER INTEGRATION")
    print("="*70)
    
    builder = GSTBuilder()
    gstin = "27AAPCT1234A1Z5"
    period = "122023"
    
    gstr1_output = builder.build_gstr1(automerge_result, gstin, period)
    
    # Validate
    is_valid, errors = builder.validate_output(gstr1_output)
    
    if is_valid:
        print("✅ GSTR1 output validation PASSED")
    else:
        print("❌ GSTR1 output validation FAILED")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print(f"\n📋 GSTR1 Structure:")
    print(f"  GSTIN: {gstr1_output['gstin']}")
    print(f"  Period: {gstr1_output['fp']}")
    print(f"  Version: {gstr1_output['version']}")
    print(f"  B2CS Items: {len(gstr1_output['b2cs'])}")
    print(f"  Summary:")
    summary = gstr1_output['summary']
    print(f"    Total Taxable: ₹{summary['total_taxable']:.2f}")
    print(f"    Total Tax: ₹{summary['total_tax']:.2f}")
    
    # Save output
    output_path = Path(f'test_output/validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(gstr1_output, f, indent=2)
    print(f"\n💾 Output saved to: {output_path}")
    
    return True

# =====================================================
# MAIN EXECUTION
# =====================================================

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("GST PARSER VALIDATION SUITE - PROOF-BASED TESTING")
    print("="*70)
    
    results = {}
    
    # Test 1: Meesho
    try:
        meesho_pass, meesho_result = test_meesho_parser()
        results['meesho'] = meesho_pass
    except Exception as e:
        print(f"❌ MEESHO TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['meesho'] = False
        meesho_result = None
    
    # Test 2: Flipkart
    try:
        flipkart_pass, flipkart_result = test_flipkart_parser()
        results['flipkart'] = flipkart_pass
    except Exception as e:
        print(f"❌ FLIPKART TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['flipkart'] = False
    
    # Test 3: Amazon
    try:
        amazon_pass, amazon_result = test_amazon_parser()
        results['amazon'] = amazon_pass
    except Exception as e:
        print(f"❌ AMAZON TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['amazon'] = False
    
    # Test 4: AutoMerge
    try:
        automerge_pass, automerge_result = test_automerge_parser()
        results['automerge'] = automerge_pass
    except Exception as e:
        print(f"❌ AUTOMERGE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        results['automerge'] = False
        automerge_result = None
    
    # Test 5: GST Builder Integration
    if automerge_result:
        try:
            builder_pass = test_gst_builder_integration(automerge_result)
            results['gst_builder'] = builder_pass
        except Exception as e:
            print(f"❌ GST BUILDER TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results['gst_builder'] = False
    
    # Summary
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  SOME TESTS FAILED - Review above for details")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
