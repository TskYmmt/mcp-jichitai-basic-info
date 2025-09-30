"""Central data manager that integrates all parsers"""
from typing import Dict, List, Optional
from pathlib import Path
from .population_parser import PopulationParser
from .finance_parser import FinanceParser
from .codes_parser import CodesParser


class DataManager:
    """Central manager for all municipality data"""

    def __init__(self, data_dir: str = None):
        # Default to data directory relative to this file's location
        if data_dir is None:
            # Get the project root (2 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data" / "source"

        self.data_dir = Path(data_dir)
        self.population_parser = None
        self.finance_parser = None
        self.codes_parser = None

        # Initialize parsers
        self._init_parsers()

    def _init_parsers(self):
        """Initialize all data parsers"""
        # Population parser
        pop_file = self.data_dir / "population" / "r06_municipal_population.xlsx"
        if pop_file.exists():
            self.population_parser = PopulationParser(str(pop_file))

        # Finance parser
        finance_file = self.data_dir / "finance" / "r05_finance_summary.xlsx"
        if finance_file.exists():
            self.finance_parser = FinanceParser(str(finance_file))

        # Codes parser
        codes_file = self.data_dir / "codes" / "municipal_codes_2019.xlsx"
        if codes_file.exists():
            self.codes_parser = CodesParser(str(codes_file))

    def get_jichitai_basic_info(
        self,
        jichitai_code: Optional[str] = None,
        jichitai_name: Optional[str] = None,
        prefecture: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get basic information for a municipality

        Args:
            jichitai_code: 6-digit municipality code
            jichitai_name: Municipality name
            prefecture: Prefecture name (optional, for disambiguation)

        Returns:
            Dictionary with all available data for the municipality
        """
        # Find municipality by code or name
        if jichitai_code:
            code_data = self.codes_parser.get_by_code(jichitai_code) if self.codes_parser else None
            if not code_data:
                return None
            code = jichitai_code
        elif jichitai_name:
            if not self.codes_parser:
                return None
            matches = self.codes_parser.get_by_name(jichitai_name, prefecture)
            if not matches:
                return None
            # Use best match
            code_data = matches[0]
            code = code_data["jichitai_code"]
        else:
            return None

        # Gather data from all sources
        result = {
            "jichitai_code": code,
            "jichitai_name": code_data.get("municipality") if code_data else None,
            "prefecture": code_data.get("prefecture") if code_data else None,
            "jichitai_type": code_data.get("jichitai_type") if code_data else None,
        }

        # Add population data
        if self.population_parser:
            pop_data = self.population_parser.get_by_code(code)
            if pop_data:
                result["population"] = pop_data.get("population")
                result["households"] = pop_data.get("households")
                result["population_dynamics"] = pop_data.get("population_dynamics")
                result["data_sources"] = {
                    "population_source": "令和6年1月1日住民基本台帳",
                }

        # Add finance data
        if self.finance_parser:
            finance_data = self.finance_parser.get_by_code(code)
            if finance_data:
                result["finance"] = finance_data.get("finance")
                if "data_sources" not in result:
                    result["data_sources"] = {}
                result["data_sources"]["finance_source"] = "令和5年度市町村別決算状況調"

        return result

    def get_jichitai_code(
        self,
        jichitai_name: str,
        prefecture: Optional[str] = None,
        fuzzy_match: bool = True
    ) -> Dict:
        """
        Get municipality code(s) from name

        Args:
            jichitai_name: Municipality name
            prefecture: Prefecture name (optional)
            fuzzy_match: Enable fuzzy matching

        Returns:
            Dictionary with matches and exact_match flag
        """
        if not self.codes_parser:
            return {"matches": [], "exact_match": False}

        matches = self.codes_parser.get_by_name(jichitai_name, prefecture)

        # Check for exact match
        exact_match = any(m.get("match_score", 0) == 1.0 for m in matches)

        return {
            "matches": matches,
            "exact_match": exact_match
        }

    def search_jichitai_by_criteria(
        self,
        population_min: Optional[int] = None,
        population_max: Optional[int] = None,
        prefecture: Optional[List[str]] = None,
        jichitai_type: Optional[List[str]] = None,
        financial_capability_min: Optional[float] = None,
        sort_by: str = "population",
        sort_order: str = "desc",
        limit: Optional[int] = None
    ) -> Dict:
        """
        Search municipalities by criteria

        Args:
            population_min: Minimum population
            population_max: Maximum population
            prefecture: List of prefecture names
            jichitai_type: List of municipality types
            financial_capability_min: Minimum financial capability index
            sort_by: Sort field ("population" or "financial_capability")
            sort_order: Sort order ("asc" or "desc")
            limit: Maximum number of results

        Returns:
            Dictionary with matching municipalities
        """
        if not self.population_parser:
            return {"jichitai_list": [], "total_count": 0, "filtered_count": 0}

        # Get all population data
        pop_data = self.population_parser.parse()

        # Get all finance data if needed
        finance_data_map = {}
        if self.finance_parser and (financial_capability_min is not None or sort_by == "financial_capability"):
            finance_list = self.finance_parser.parse()
            finance_data_map = {f["jichitai_code"]: f for f in finance_list}

        # Filter results
        results = []
        for record in pop_data:
            # Apply filters
            pop_total = record["population"]["total"]

            # Skip if population is None
            if pop_total is None:
                continue

            if population_min is not None and pop_total < population_min:
                continue
            if population_max is not None and pop_total > population_max:
                continue

            if prefecture and record["prefecture"] not in prefecture:
                continue

            # Get municipality type from codes
            code_data = self.codes_parser.get_by_code(record["jichitai_code"]) if self.codes_parser else None
            muni_type = code_data.get("jichitai_type") if code_data else None

            if jichitai_type and muni_type not in jichitai_type:
                continue

            # Check financial capability
            finance_record = finance_data_map.get(record["jichitai_code"])
            fin_cap_index = None
            if finance_record:
                fin_cap_index = finance_record["finance"].get("financial_capability_index")

            if financial_capability_min is not None and (fin_cap_index is None or fin_cap_index < financial_capability_min):
                continue

            # Build result record
            result = {
                "jichitai_code": record["jichitai_code"],
                "jichitai_name": record["municipality"],
                "prefecture": record["prefecture"],
                "jichitai_type": muni_type,
                "population": pop_total,
                "financial_capability_index": fin_cap_index
            }
            results.append(result)

        total_count = len(results)

        # Sort results
        if sort_by == "population":
            results.sort(key=lambda x: x["population"] or 0, reverse=(sort_order == "desc"))
        elif sort_by == "financial_capability":
            results.sort(key=lambda x: x["financial_capability_index"] or 0, reverse=(sort_order == "desc"))

        # Apply limit
        if limit:
            results = results[:limit]

        return {
            "jichitai_list": results,
            "total_count": total_count,
            "filtered_count": len(results)
        }

    def close(self):
        """Close all parsers"""
        if self.population_parser:
            self.population_parser.close()
        if self.finance_parser:
            self.finance_parser.close()
        if self.codes_parser:
            self.codes_parser.close()