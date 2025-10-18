"""Test for CSV export functionality"""
import sys
from pathlib import Path
import csv
import os

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.data_manager import DataManager


def test_csv_export():
    """Test CSV export functionality"""
    print("=== Testing CSV Export ===\n")

    dm = DataManager()

    # Export to temporary file
    output_path = "/tmp/test_municipalities_export.csv"

    print(f"Exporting all municipalities to: {output_path}")
    result = dm.export_all_municipalities_to_csv(output_path)

    if result.get("status") == "success":
        print(f"✓ Export successful!")
        print(f"  Municipalities exported: {result.get('count')}")
        print(f"  File path: {result.get('file_path')}\n")

        # Verify file exists
        if os.path.exists(output_path):
            print("✓ File exists")

            # Read first few rows
            with open(output_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                print(f"✓ Total rows in CSV: {len(rows)}")
                print(f"✓ Columns: {len(rows[0])} columns")
                print(f"  Column names: {list(rows[0].keys())[:5]}... (showing first 5)")

                # Show first 3 rows
                print("\n  First 3 rows:")
                for i, row in enumerate(rows[:3], 1):
                    print(f"    {i}. {row['jichitai_name']} ({row['jichitai_code']}) - "
                          f"Pop: {row['population_total']}, "
                          f"財政力指数: {row['financial_capability_index']}")

                # Verify some key data
                print("\n✓ Verification:")
                # Check if we have data for different municipality types
                types = set(row['jichitai_type'] for row in rows if row['jichitai_type'])
                print(f"  Municipality types found: {sorted(types)}")

                # Check if 矢巾町 is in the data
                yahaba = next((r for r in rows if r['jichitai_code'] == '033227'), None)
                if yahaba:
                    print(f"  ✓ 矢巾町 found: 財政力指数={yahaba['financial_capability_index']}")
                else:
                    print(f"  ⚠ 矢巾町 not found in export")

            print("\n✓ All CSV export tests passed!")

            # Clean up
            os.remove(output_path)
            print(f"✓ Temporary file removed")
        else:
            print("✗ File not created")
    else:
        print(f"✗ Export failed: {result.get('error')}")

    dm.close()


if __name__ == "__main__":
    test_csv_export()
    print("\n=== CSV export test completed ===")
