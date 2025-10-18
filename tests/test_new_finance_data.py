"""Test for new finance data (all municipalities)"""
import sys
from pathlib import Path
import json

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.data_manager import DataManager


def test_new_finance_schema():
    """Test that new finance data works correctly for all municipality types"""
    print("=== Testing New Finance Data (All Municipalities) ===\n")

    dm = DataManager()

    # Test 1: City (横須賀市)
    print("Test 1: City (横須賀市: 142018)")
    result = dm.get_jichitai_basic_info(jichitai_code="142018")
    if result and result.get("finance"):
        finance = result["finance"]
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  財政力指数: {finance.get('financial_capability_index')}")
        print(f"  経常収支比率: {finance.get('current_balance_ratio')}")
        print(f"  実質公債費比率: {finance.get('real_debt_service_ratio')}")
        print(f"  将来負担比率: {finance.get('future_burden_ratio')}")
        print(f"  ラスパイレス指数: {finance.get('laspeyres_index')}")
        print("  ✓ Test 1 passed: City has finance data with new schema\n")
    else:
        print("  ✗ Test 1 failed\n")

    # Test 2: Town (矢巾町) - THIS IS THE KEY TEST!
    print("Test 2: Town (矢巾町: 033227) - Should now have finance data!")
    result = dm.get_jichitai_basic_info(jichitai_code="033227")
    if result and result.get("finance"):
        finance = result["finance"]
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  財政力指数: {finance.get('financial_capability_index')}")
        print(f"  経常収支比率: {finance.get('current_balance_ratio')}")
        print(f"  実質公債費比率: {finance.get('real_debt_service_ratio')}")
        print(f"  将来負担比率: {finance.get('future_burden_ratio')}")
        print(f"  ラスパイレス指数: {finance.get('laspeyres_index')}")
        if finance.get('financial_capability_index') is not None:
            print("  ✓ Test 2 passed: Town now has finance data!\n")
        else:
            print("  ✗ Test 2 failed: Town has finance field but data is null\n")
    else:
        print("  ✗ Test 2 failed: Town has no finance data\n")

    # Test 3: Village (検索で見つける)
    print("Test 3: Village (新篠津村: 013048)")
    result = dm.get_jichitai_basic_info(jichitai_code="013048")
    if result and result.get("finance"):
        finance = result["finance"]
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  財政力指数: {finance.get('financial_capability_index')}")
        if finance.get('financial_capability_index') is not None:
            print("  ✓ Test 3 passed: Village has finance data!\n")
        else:
            print("  ✗ Test 3 failed\n")
    else:
        print("  ✗ Test 3 failed\n")

    # Test 4: Special ward (世田谷区)
    print("Test 4: Special ward (世田谷区: 131121)")
    result = dm.get_jichitai_basic_info(jichitai_code="131121")
    if result and result.get("finance"):
        finance = result["finance"]
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  財政力指数: {finance.get('financial_capability_index')}")
        print(f"  将来負担比率: {finance.get('future_burden_ratio')}")
        if finance.get('financial_capability_index') is not None:
            print("  ✓ Test 4 passed: Special ward has finance data!\n")
        else:
            print("  ✗ Test 4 failed\n")
    else:
        print("  ✗ Test 4 failed\n")

    # Test 5: Search by financial capability - should now include towns!
    print("Test 5: Search by financial capability (min=0.6)")
    result = dm.search_jichitai_by_criteria(
        financial_capability_min=0.6,
        sort_by="financial_capability",
        sort_order="desc",
        limit=10
    )
    if result and result.get("jichitai_list"):
        jichitai_list = result["jichitai_list"]
        print(f"  Found {len(jichitai_list)} municipalities")
        # Count types
        city_count = sum(1 for j in jichitai_list if j.get("jichitai_type") == "市")
        town_count = sum(1 for j in jichitai_list if j.get("jichitai_type") == "町")
        village_count = sum(1 for j in jichitai_list if j.get("jichitai_type") == "村")
        ward_count = sum(1 for j in jichitai_list if j.get("jichitai_type") == "特別区")
        print(f"  市: {city_count}, 町: {town_count}, 村: {village_count}, 特別区: {ward_count}")

        # Show top 3
        print("  Top 3:")
        for j in jichitai_list[:3]:
            print(f"    - {j['jichitai_name']} ({j.get('jichitai_type', 'N/A')}): {j['financial_capability_index']}")

        if town_count > 0 or village_count > 0:
            print("  ✓ Test 5 passed: Search now includes towns/villages!\n")
        else:
            print("  ⚠ Test 5 warning: No towns/villages in results (may be expected if min=0.6 is high)\n")
    else:
        print("  ✗ Test 5 failed\n")

    dm.close()


if __name__ == "__main__":
    test_new_finance_schema()
    print("=== New finance data test completed ===")
