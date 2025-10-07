"""Test for finance schema unification (town/city/special ward)"""
import sys
from pathlib import Path
import json

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.data_manager import DataManager


def test_finance_schema_unification():
    """Test that finance field is always present with correct schema"""
    print("=== Testing Finance Schema Unification ===\n")

    dm = DataManager()

    # Test 1: City (市) - should have finance data
    print("Test 1: City (横須賀市: 142018) - should have finance data")
    result = dm.get_jichitai_basic_info(jichitai_code="142018")
    if result:
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  自治体タイプ: {result['jichitai_type']}")
        print(f"  finance field exists: {'finance' in result}")
        print(f"  finance value: {result.get('finance')}")
        print(f"  finance_source exists: {'finance_source' in result.get('data_sources', {})}")
        print(f"  finance_source: {result.get('data_sources', {}).get('finance_source')}")
        if 'finance' in result and result['finance'] is not None:
            print("  ✓ Test 1 passed: City has finance data\n")
        else:
            print("  ✗ Test 1 failed: City should have finance data\n")
    else:
        print("  ✗ Test 1 failed: No data found\n")

    # Test 2: Town (町) - should have finance as null
    print("Test 2: Town (矢巾町: 033227) - should have finance as null")
    result = dm.get_jichitai_basic_info(jichitai_code="033227")
    if result:
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  自治体タイプ: {result['jichitai_type']}")
        print(f"  finance field exists: {'finance' in result}")
        print(f"  finance value: {result.get('finance')}")
        print(f"  finance_source exists: {'finance_source' in result.get('data_sources', {})}")
        print(f"  finance_source: {result.get('data_sources', {}).get('finance_source')}")
        if 'finance' in result and result['finance'] is None:
            print("  ✓ Test 2 passed: Town has finance field as null\n")
        else:
            print("  ✗ Test 2 failed: Town should have finance field as null\n")
    else:
        print("  ✗ Test 2 failed: No data found\n")

    # Test 3: Tokyo special ward (特別区) - should have finance with some null values
    print("Test 3: Tokyo special ward (世田谷区: 131121) - should have finance with some null indicators")
    result = dm.get_jichitai_basic_info(jichitai_code="131121")
    if result:
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  自治体タイプ: {result.get('jichitai_type')}")
        print(f"  finance field exists: {'finance' in result}")
        finance = result.get('finance')
        if finance:
            print(f"  standard_fiscal_scale: {finance.get('standard_fiscal_scale')}")
            print(f"  financial_capability_index: {finance.get('financial_capability_index')}")
            print(f"  real_balance_ratio: {finance.get('real_balance_ratio')}")
            print(f"  current_balance_ratio: {finance.get('current_balance_ratio')}")
            # Check if special ward indicators are null (not string "-")
            if (finance.get('standard_fiscal_scale') is None and
                finance.get('financial_capability_index') is None and
                finance.get('real_balance_ratio') is None):
                print("  ✓ Test 3 passed: Special ward has null for N/A indicators\n")
            else:
                print("  ✗ Test 3 failed: Special ward should have null (not string) for N/A indicators\n")
        else:
            print("  ✗ Test 3 failed: Special ward should have finance field\n")
    else:
        print("  ✗ Test 3 failed: No data found\n")

    # Test 4: Verify data_sources always includes finance_source
    print("Test 4: Verify data_sources structure")
    city = dm.get_jichitai_basic_info(jichitai_code="142018")
    town = dm.get_jichitai_basic_info(jichitai_code="033227")

    all_passed = True
    if city and 'data_sources' in city and 'finance_source' in city['data_sources']:
        print(f"  City finance_source: {city['data_sources']['finance_source']}")
    else:
        print("  ✗ City missing finance_source in data_sources")
        all_passed = False

    if town and 'data_sources' in town and 'finance_source' in town['data_sources']:
        print(f"  Town finance_source: {town['data_sources']['finance_source']}")
    else:
        print("  ✗ Town missing finance_source in data_sources")
        all_passed = False

    if all_passed:
        print("  ✓ Test 4 passed: data_sources always includes finance_source\n")
    else:
        print("  ✗ Test 4 failed\n")

    dm.close()


if __name__ == "__main__":
    test_finance_schema_unification()
    print("=== Finance schema test completed ===")
