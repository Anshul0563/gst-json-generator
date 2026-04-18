#!/usr/bin/env python3
"""
Integration Test Suite for GST JSON Generator Pro v2.0
Tests all advanced modules and their interactions
"""

import sys
import json
from pathlib import Path

def test_config():
    """Test configuration system"""
    print("Testing config.py...")
    try:
        from config import get_config, init_config, Config
        
        # Test global config
        config = get_config()
        assert config is not None, "Config instance is None"
        
        # Test get/set
        tax_rate = config.get('gst.default_tax_rate')
        assert isinstance(tax_rate, (int, float)), f"Expected number, got {type(tax_rate)}"
        
        # Test dot notation
        version = config.get('app.version')
        assert version == '2.0.0', f"Expected 2.0.0, got {version}"
        
        print("  ✅ Config system working correctly")
        return True
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False

def test_logger():
    """Test advanced logging system"""
    print("Testing logger.py...")
    try:
        from logger import get_logger, AdvancedLogger
        
        # Test singleton
        logger = get_logger()
        assert logger is not None, "Logger is None"
        assert isinstance(logger, AdvancedLogger), f"Expected AdvancedLogger, got {type(logger)}"
        
        # Test logging methods
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        
        # Test performance tracking
        import time
        start = time.time()
        time.sleep(0.01)
        duration = time.time() - start
        logger.perf("test_operation", duration, 100)
        
        print("  ✅ Logger system working correctly")
        return True
    except Exception as e:
        print(f"  ❌ Logger test failed: {e}")
        return False

def test_cache():
    """Test caching system"""
    print("Testing cache.py...")
    try:
        from cache import get_cache, cached, Cache
        
        # Test singleton
        cache = get_cache()
        assert cache is not None, "Cache is None"
        assert isinstance(cache, Cache), f"Expected Cache, got {type(cache)}"
        
        # Test set/get
        test_key = "test_key"
        test_value = {"data": "test"}
        cache.set(test_key, test_value)
        retrieved = cache.get(test_key)
        assert retrieved == test_value, f"Cache value mismatch"
        
        # Test delete
        cache.delete(test_key)
        assert cache.get(test_key) is None, "Key should be deleted"
        
        # Test @cached decorator
        call_count = 0
        @cached(ttl=3600)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = expensive_func(5)
        result2 = expensive_func(5)
        assert result1 == result2 == 10, "Cached results don't match"
        assert call_count == 1, "Function called more than once (caching failed)"
        
        print("  ✅ Cache system working correctly")
        return True
    except Exception as e:
        print(f"  ❌ Cache test failed: {e}")
        return False

def test_validators():
    """Test advanced validation system"""
    print("Testing validators.py...")
    try:
        from validators import Validator
        
        # Test GSTIN validation
        valid_gstin = "27AAPCT1234A1Z5"
        is_valid, error = Validator.validate_gstin(valid_gstin)
        assert is_valid, f"Valid GSTIN failed: {error}"
        
        # Test invalid GSTIN
        invalid_gstin = "INVALID"
        is_valid, error = Validator.validate_gstin(invalid_gstin)
        assert not is_valid, "Invalid GSTIN passed validation"
        
        # Test period validation
        valid_period = "122023"
        is_valid, error = Validator.validate_period(valid_period)
        assert is_valid, f"Valid period failed: {error}"
        
        # Test invalid period
        invalid_period = "132023"
        is_valid, error = Validator.validate_period(invalid_period)
        assert not is_valid, "Invalid period passed validation"
        
        print("  ✅ Validation system working correctly")
        return True
    except Exception as e:
        print(f"  ❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exporter():
    """Test multi-format export system"""
    print("Testing exporter.py...")
    try:
        from exporter import Exporter, BaseExporter, JSONExporter
        
        # Create test data
        test_output = {
            "summary": {
                "gstin": "27AAPCT1234A1Z5",
                "period": "122023",
                "rows": [
                    {"pos": "07", "taxable_value": 1000, "igst": 0, "cgst": 15, "sgst": 15}
                ]
            }
        }
        
        # Test JSONExporter
        json_exporter = JSONExporter()
        result = json_exporter.export(test_output, "test.json")
        assert result is not None, "JSONExporter returned None"
        assert "test.json" in result, f"Expected filename in result: {result}"
        
        # Test Exporter orchestrator
        exporter = Exporter("./test_output")
        results = exporter.export(test_output, "test", ["json"])
        assert "json" in results, f"Expected json in results: {results}"
        
        print("  ✅ Export system working correctly")
        return True
    except Exception as e:
        print(f"  ❌ Export test failed: {e}")
        return False

def test_gst_builder():
    """Test GST builder with design patterns"""
    print("Testing gst_builder.py...")
    try:
        from gst_builder import GSTBuilder, SupplyTypeCalculator, B2CSItemBuilder
        
        # Test SupplyTypeCalculator
        calculator = SupplyTypeCalculator()
        supply_type, tax_rates = calculator.calculate("07")
        assert supply_type in ["INTRA", "INTER"], f"Invalid supply type: {supply_type}"
        assert "cgst_rate" in tax_rates, "Missing cgst_rate in tax_rates"
        
        # Test B2CSItemBuilder with a row
        test_row = {
            "pos": "07",
            "taxable_value": 1000,
            "igst": 0,
            "cgst": 15,
            "sgst": 15
        }
        builder = B2CSItemBuilder(test_row)
        item = builder.build()
        assert item["pos"] == "07", "Builder failed to set POS"
        
        # Test GSTBuilder
        gst_builder = GSTBuilder()
        assert gst_builder is not None, "GSTBuilder is None"
        
        print("  ✅ GST Builder working correctly")
        return True
    except Exception as e:
        print(f"  ❌ GST Builder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parsers():
    """Test parser modules"""
    print("Testing parsers.py...")
    try:
        # Check if pandas is available
        try:
            import pandas
        except ImportError:
            print("  ⚠ Skipping parser tests (pandas not installed)")
            return True
        
        from parsers import BaseParser, MeeshoParser, FlipkartParser, AmazonParser, AutoMergeParser
        
        # Test parser initialization
        meesho = MeeshoParser()
        assert meesho is not None, "MeeshoParser is None"
        assert meesho.ETIN is not None, "MeeshoParser ETIN not set"
        
        flipkart = FlipkartParser()
        assert flipkart is not None, "FlipkartParser is None"
        
        amazon = AmazonParser()
        assert amazon is not None, "AmazonParser is None"
        
        auto_merge = AutoMergeParser()
        assert auto_merge is not None, "AutoMergeParser is None"
        
        print("  ✅ Parser system working correctly")
        return True
    except Exception as e:
        print(f"  ❌ Parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("GST JSON Generator Pro v2.0 - Integration Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        test_config,
        test_logger,
        test_cache,
        test_validators,
        test_exporter,
        test_gst_builder,
        test_parsers,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Unexpected error in {test.__name__}: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} passed")
    print("=" * 60)
    
    if passed == total:
        print("✅ All integration tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
