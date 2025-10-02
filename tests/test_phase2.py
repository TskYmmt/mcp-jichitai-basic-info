"""Test for Phase 2 new tools (My Number Card and DX Dashboard)"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.data_manager import DataManager


def test_mynumber_card_rate():
    """Test My Number Card rate retrieval"""
    print("=== Testing My Number Card Rate ===\n")

    dm = DataManager()

    # Test 1: Get by jichitai_code
    print("Test 1: Get by jichitai_code (横須賀市: 142018)")
    result = dm.get_mynumber_card_rate(jichitai_code="142018")
    if result:
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  都道府県: {result['prefecture']}")
        print(f"  人口: {result['mynumber_card_data']['population']:,}")
        print(f"  交付枚数: {result['mynumber_card_data']['issued_cards']:,}")
        print(f"  交付率: {result['mynumber_card_data']['issuance_rate']}%")
        print("  ✓ Test 1 passed\n")
    else:
        print("  ✗ Test 1 failed: No data found\n")

    # Test 2: Get by jichitai_name (郡名を含む形式)
    print("Test 2: Get by jichitai_name (紫波郡矢巾町)")
    result = dm.get_mynumber_card_rate(jichitai_name="紫波郡矢巾町", prefecture="岩手県")
    if result:
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  都道府県: {result['prefecture']}")
        print(f"  交付率: {result['mynumber_card_data']['issuance_rate']}%")
        print("  ✓ Test 2 passed\n")
    else:
        print("  ✗ Test 2 failed: No data found\n")

    dm.close()


def test_dx_dashboard_data():
    """Test DX Dashboard data retrieval"""
    print("=== Testing DX Dashboard Data ===\n")

    dm = DataManager()

    # Test 1: Get by jichitai_code
    print("Test 1: Get by jichitai_code (横須賀市: 142018)")
    result = dm.get_digital_agency_dx_data(jichitai_code="142018")
    if result:
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  DX指標数: {len(result['dx_data']['dx_indicators'])}")
        print(f"  オンライン手続数: {len(result['dx_data']['online_procedures'])}")

        # Show some DX indicators
        dx_indicators = result['dx_data']['dx_indicators']
        print("\n  主要DX指標:")
        if 'CIOの任命' in dx_indicators:
            print(f"    - CIOの任命: {dx_indicators['CIOの任命']}")
        if '全体方針策定' in dx_indicators:
            print(f"    - 全体方針策定: {dx_indicators['全体方針策定']}")
        if 'AIの導入状況' in dx_indicators:
            print(f"    - AIの導入状況: {dx_indicators['AIの導入状況']}")

        # Show some online procedures
        online_procs = result['dx_data']['online_procedures']
        print("\n  オンライン申請率（一部）:")
        proc_count = 0
        for proc_name, rate in online_procs.items():
            if rate is not None and proc_count < 3:
                print(f"    - {proc_name}: {rate}%")
                proc_count += 1

        print("\n  ✓ Test 1 passed\n")
    else:
        print("  ✗ Test 1 failed: No data found\n")

    # Test 2: Get by jichitai_name
    print("Test 2: Get by jichitai_name (札幌市)")
    result = dm.get_digital_agency_dx_data(jichitai_name="札幌市", prefecture="北海道")
    if result:
        print(f"  自治体名: {result['jichitai_name']}")
        print(f"  DX指標数: {len(result['dx_data']['dx_indicators'])}")
        print("  ✓ Test 2 passed\n")
    else:
        print("  ✗ Test 2 failed: No data found\n")

    dm.close()


def test_integration():
    """Test integration of all data sources"""
    print("=== Testing Data Integration ===\n")

    dm = DataManager()

    print("Test: Get comprehensive data for 横須賀市")

    # Get basic info
    basic = dm.get_jichitai_basic_info(jichitai_code="142018")
    mynumber = dm.get_mynumber_card_rate(jichitai_code="142018")
    dx = dm.get_digital_agency_dx_data(jichitai_code="142018")

    if basic and mynumber and dx:
        print(f"\n  自治体名: {basic['jichitai_name']}")
        print(f"  人口: {basic['population']['total']:,}")
        print(f"  財政力指数: {basic['finance']['financial_capability_index']}")
        print(f"  マイナンバーカード交付率: {mynumber['mynumber_card_data']['issuance_rate']}%")
        print(f"  DX指標数: {len(dx['dx_data']['dx_indicators'])}")
        print("\n  ✓ Integration test passed\n")
    else:
        print("  ✗ Integration test failed\n")

    dm.close()


if __name__ == "__main__":
    test_mynumber_card_rate()
    test_dx_dashboard_data()
    test_integration()
    print("=== All tests completed ===")
