"""Parser for finance data from Excel files"""
import openpyxl
from typing import Dict, List, Optional
from pathlib import Path


class FinanceParser:
    """Parse municipal finance data from Excel files"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.workbook = None
        self.worksheet = None

    def load(self):
        """Load the Excel file"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Finance data file not found: {self.file_path}")

        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        # Get first sheet
        self.worksheet = self.workbook[self.workbook.sheetnames[0]]

    def parse(self) -> List[Dict]:
        """
        Parse finance summary data from Excel file

        Returns:
            List of dictionaries with finance data for each municipality
        """
        if self.worksheet is None:
            self.load()

        ws = self.worksheet
        data = []

        # Data starts at row 17, column 15 (O column)
        # Key columns:
        # 15(O): 団体コード
        # 16(P): 団体名
        # 17(Q): 住民基本台帳登載人口
        # 27(AA): 標準財政規模
        # 29(AC): 実質収支比率
        # 30(AD): 経常収支比率
        # 35(AI): 財政力指数
        # 40(AN): 歳入総額
        # 41(AO): 歳出総額

        for row_idx in range(17, ws.max_row + 1):
            jichitai_code = ws.cell(row_idx, 15).value

            # Skip if no code
            if not jichitai_code or not str(jichitai_code).strip():
                continue

            # Skip if not a valid 6-digit code
            if not str(jichitai_code).isdigit() or len(str(jichitai_code)) != 6:
                continue

            municipality_name = ws.cell(row_idx, 16).value
            population = ws.cell(row_idx, 17).value
            standard_fiscal_scale = ws.cell(row_idx, 27).value
            real_balance_ratio = ws.cell(row_idx, 29).value
            current_balance_ratio = ws.cell(row_idx, 30).value
            financial_capability_index = ws.cell(row_idx, 35).value
            revenue_total = ws.cell(row_idx, 40).value
            expenditure_total = ws.cell(row_idx, 41).value

            record = {
                "jichitai_code": str(jichitai_code).zfill(6),
                "municipality_name": municipality_name,
                "population": population,
                "finance": {
                    "standard_fiscal_scale": standard_fiscal_scale,  # 標準財政規模 (千円)
                    "real_balance_ratio": real_balance_ratio,  # 実質収支比率 (%)
                    "current_balance_ratio": current_balance_ratio,  # 経常収支比率 (%)
                    "financial_capability_index": financial_capability_index,  # 財政力指数
                    "revenue_total": revenue_total,  # 歳入総額 (千円)
                    "expenditure_total": expenditure_total,  # 歳出総額 (千円)
                }
            }

            data.append(record)

        return data

    def get_by_code(self, jichitai_code: str) -> Optional[Dict]:
        """Get finance data for a specific municipality by code"""
        data = self.parse()
        code = str(jichitai_code).zfill(6)

        for record in data:
            if record["jichitai_code"] == code:
                return record

        return None

    def close(self):
        """Close the workbook"""
        if self.workbook:
            self.workbook.close()