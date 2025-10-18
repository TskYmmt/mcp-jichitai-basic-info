"""Central data manager that integrates all parsers"""
from typing import Dict, List, Optional
from pathlib import Path
from .population_parser import PopulationParser
from .finance_parser import FinanceParser
from .codes_parser import CodesParser
from .mynumber_parser import MyNumberParser
from .dx_parser import DXParser
from .age_group_parser import AgeGroupParser


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
        self.mynumber_parser = None
        self.dx_parser = None
        self.age_group_parser = None

        # Initialize parsers
        self._init_parsers()

    def _init_parsers(self):
        """Initialize all data parsers"""
        # Population parser
        pop_file = self.data_dir / "population" / "r06_municipal_population.xlsx"
        if pop_file.exists():
            self.population_parser = PopulationParser(str(pop_file))

        # Finance parser - all municipalities (cities, towns, villages, special wards)
        finance_file = self.data_dir / "finance" / "000983094 (1).xlsx"
        if finance_file.exists():
            self.finance_parser = FinanceParser(str(finance_file))

        # Codes parser
        codes_file = self.data_dir / "codes" / "municipal_codes_2019.xlsx"
        if codes_file.exists():
            self.codes_parser = CodesParser(str(codes_file))

        # My Number Card parser
        mynumber_file = self.data_dir / "mynumber" / "mynumber_card_rate.xlsx"
        if mynumber_file.exists():
            self.mynumber_parser = MyNumberParser(str(mynumber_file))

        # DX Dashboard parser
        dx_comparison_file = self.data_dir / "dx_dashboard" / "extracted" / "市区町村毎のDX進捗状況_市区町村比較.xlsx"
        dx_online_file = self.data_dir / "dx_dashboard" / "extracted" / "市区町村毎のDX進捗状況_行政手続のオンライン申請率.xlsx"
        if dx_comparison_file.exists() and dx_online_file.exists():
            self.dx_parser = DXParser(str(dx_comparison_file), str(dx_online_file))

        # Age group population parser
        age_group_file = self.data_dir / "population" / "age_group_population.xlsx"
        if age_group_file.exists():
            self.age_group_parser = AgeGroupParser(str(age_group_file))

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

        # Add finance data (always include field, even if null)
        result["finance"] = None
        if "data_sources" not in result:
            result["data_sources"] = {}
        result["data_sources"]["finance_source"] = None

        if self.finance_parser:
            finance_data = self.finance_parser.get_by_code(code)
            if finance_data:
                result["finance"] = finance_data.get("finance")
                result["data_sources"]["finance_source"] = "令和5年度全市町村の主要財政指標"

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

    def get_mynumber_card_rate(
        self,
        jichitai_code: Optional[str] = None,
        jichitai_name: Optional[str] = None,
        prefecture: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get My Number Card issuance rate for a municipality

        Args:
            jichitai_code: 6-digit municipality code
            jichitai_name: Municipality name
            prefecture: Prefecture name (optional, for disambiguation)

        Returns:
            Dictionary with My Number Card data
        """
        if not self.mynumber_parser:
            return None

        # Find municipality by code or name
        target_name = None
        target_prefecture = None

        if jichitai_code:
            # Get municipality name from codes
            code_data = self.codes_parser.get_by_code(jichitai_code) if self.codes_parser else None
            if not code_data:
                return None
            target_name = code_data.get("municipality")
            target_prefecture = code_data.get("prefecture")
        elif jichitai_name:
            target_name = jichitai_name
            target_prefecture = prefecture

        if not target_name:
            return None

        # Get My Number Card data
        mynumber_data = self.mynumber_parser.get_by_name(target_name, target_prefecture)
        if not mynumber_data:
            return None

        # Get jichitai_code if we don't have it
        if not jichitai_code and self.codes_parser:
            matches = self.codes_parser.get_by_name(target_name, target_prefecture)
            if matches:
                jichitai_code = matches[0].get("jichitai_code")

        return {
            "jichitai_code": jichitai_code,
            "jichitai_name": mynumber_data["municipality"],
            "prefecture": mynumber_data["prefecture"],
            "mynumber_card_data": mynumber_data["mynumber_card"],
            "data_source": {
                "source_name": "総務省 マイナンバーカード交付状況",
                "source_url": "https://www.soumu.go.jp/kojinbango_card/kofujokyo.html"
            }
        }

    def get_digital_agency_dx_data(
        self,
        jichitai_code: Optional[str] = None,
        jichitai_name: Optional[str] = None,
        prefecture: Optional[str] = None,
        data_category: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Get Digital Agency DX Dashboard data for a municipality

        Args:
            jichitai_code: 6-digit municipality code
            jichitai_name: Municipality name
            prefecture: Prefecture name (optional, for disambiguation)
            data_category: List of data categories to retrieve

        Returns:
            Dictionary with DX data
        """
        if not self.dx_parser:
            return None

        # Find municipality by code or name
        target_name = None
        target_prefecture = None

        if jichitai_code:
            # Get municipality name from codes
            code_data = self.codes_parser.get_by_code(jichitai_code) if self.codes_parser else None
            if not code_data:
                return None
            target_name = code_data.get("municipality")
            target_prefecture = code_data.get("prefecture")
        elif jichitai_name:
            target_name = jichitai_name
            target_prefecture = prefecture

        if not target_name:
            return None

        # Get DX data
        dx_data = self.dx_parser.get_by_name(target_name)
        if not dx_data:
            return None

        # Get jichitai_code if we don't have it
        if not jichitai_code and self.codes_parser:
            matches = self.codes_parser.get_by_name(target_name, target_prefecture)
            if matches:
                jichitai_code = matches[0].get("jichitai_code")

        return {
            "jichitai_code": jichitai_code,
            "jichitai_name": dx_data["municipality"],
            "prefecture": target_prefecture,
            "dx_data": {
                "dx_indicators": dx_data.get("dx_indicators", {}),
                "online_procedures": dx_data.get("online_procedures", {})
            },
            "data_source": {
                "source_name": "デジタル庁 自治体DX推進状況ダッシュボード",
                "source_url": "https://www.digital.go.jp/resources/govdashboard/local-government-dx"
            }
        }

    def get_age_group_population(
        self,
        jichitai_code: Optional[str] = None,
        jichitai_name: Optional[str] = None,
        prefecture: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get age-stratified population data for a municipality

        Args:
            jichitai_code: 6-digit municipality code
            jichitai_name: Municipality name
            prefecture: Prefecture name (optional, for disambiguation)

        Returns:
            Dictionary with age group population data
        """
        if not self.age_group_parser:
            return None

        # Find municipality by code or name
        target_code = None

        if jichitai_code:
            target_code = jichitai_code
        elif jichitai_name:
            if not self.codes_parser:
                return None
            matches = self.codes_parser.get_by_name(jichitai_name, prefecture)
            if not matches:
                return None
            target_code = matches[0].get("jichitai_code")

        if not target_code:
            return None

        # Get age group data (3 records: 計, 男, 女)
        age_data_list = self.age_group_parser.get_by_code(target_code)
        if not age_data_list:
            return None

        # Organize data by gender
        result = {
            "jichitai_code": target_code,
            "jichitai_name": age_data_list[0]["municipality"],
            "prefecture": age_data_list[0]["prefecture"],
            "age_groups": {},
            "data_source": {
                "source_name": "総務省 住民基本台帳 年齢階級別人口（市区町村別）",
                "source_url": "https://www.soumu.go.jp/menu_news/s-news/01gyosei02_02000389.html",
                "base_date": "令和7年1月1日"
            }
        }

        # Extract data for each gender
        for record in age_data_list:
            gender = record["gender"]
            result["age_groups"][gender] = {
                "total": record["total"],
                "breakdown": record["age_groups"]
            }

        # Calculate additional metrics
        total_data = result["age_groups"].get("計", {})
        if total_data and total_data.get("breakdown"):
            breakdown = total_data["breakdown"]
            total_pop = total_data.get("total", 0)

            # Calculate age group percentages
            if total_pop and total_pop > 0:
                # Youth (0-14): 0-4, 5-9, 10-14
                youth = sum([
                    breakdown.get("0-4歳", 0) or 0,
                    breakdown.get("5-9歳", 0) or 0,
                    breakdown.get("10-14歳", 0) or 0
                ])
                # Working age (15-64)
                working = sum([
                    breakdown.get(f"{i}-{i+4}歳", 0) or 0
                    for i in range(15, 65, 5)
                ])
                # Elderly (65+)
                elderly = sum([
                    breakdown.get(f"{i}-{i+4}歳", 0) or 0
                    for i in range(65, 100, 5)
                ]) + (breakdown.get("100歳以上", 0) or 0)

                result["demographic_summary"] = {
                    "youth_population": youth,
                    "youth_ratio": round(youth / total_pop * 100, 2),
                    "working_age_population": working,
                    "working_age_ratio": round(working / total_pop * 100, 2),
                    "elderly_population": elderly,
                    "elderly_ratio": round(elderly / total_pop * 100, 2)
                }

        return result

    def close(self):
        """Close all parsers"""
        if self.population_parser:
            self.population_parser.close()
        if self.finance_parser:
            self.finance_parser.close()
        if self.codes_parser:
            self.codes_parser.close()
        if self.mynumber_parser:
            self.mynumber_parser.close()
        if self.dx_parser:
            self.dx_parser.close()
        if self.age_group_parser:
            self.age_group_parser.close()