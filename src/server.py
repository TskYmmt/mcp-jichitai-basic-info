"""MCP Server for Japanese Municipality Basic Information"""
import asyncio
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .data.data_manager import DataManager


# Initialize data manager
data_manager = DataManager()

# Create MCP server
app = Server("jichitai-basic-information-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_jichitai_basic_info",
            description=(
                "Get basic information (population, finance, etc.) for a Japanese municipality by code or name. "
                "Data sources: (1) Population: 総務省「住民基本台帳に基づく人口、人口動態及び世帯数」R6.1.1現在, 2,288自治体. "
                "(2) Finance: 総務省「市町村別決算状況調」R5年度, 815市."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "jichitai_code": {
                        "type": "string",
                        "description": "6-digit municipality code (e.g., '011002' for Sapporo)",
                    },
                    "jichitai_name": {
                        "type": "string",
                        "description": "Municipality name (e.g., '札幌市', '横須賀市')",
                    },
                    "prefecture": {
                        "type": "string",
                        "description": "Prefecture name for disambiguation (e.g., '北海道', '神奈川県')",
                    },
                },
            },
        ),
        Tool(
            name="get_jichitai_code",
            description=(
                "Get municipality code(s) from municipality name (supports fuzzy matching). "
                "Data source: 総務省「全国地方公共団体コード」R6.1.1現在, 1,795自治体."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "jichitai_name": {
                        "type": "string",
                        "description": "Municipality name to search (e.g., '札幌市', 'よこすか')",
                    },
                    "prefecture": {
                        "type": "string",
                        "description": "Prefecture name for disambiguation (optional)",
                    },
                    "fuzzy_match": {
                        "type": "boolean",
                        "description": "Enable fuzzy matching (default: true)",
                        "default": True,
                    },
                },
                "required": ["jichitai_name"],
            },
        ),
        Tool(
            name="search_jichitai_by_criteria",
            description=(
                "Search municipalities by various criteria (population, prefecture, type, financial capability). "
                "Data sources: 総務省「住民基本台帳」R6.1.1, 「市町村別決算状況調」R5年度, 「全国地方公共団体コード」R6.1.1."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "population_min": {
                        "type": "number",
                        "description": "Minimum population",
                    },
                    "population_max": {
                        "type": "number",
                        "description": "Maximum population",
                    },
                    "prefecture": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of prefecture names to filter (e.g., ['北海道', '東京都'])",
                    },
                    "jichitai_type": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of municipality types (e.g., ['市', '町', '村'])",
                    },
                    "financial_capability_min": {
                        "type": "number",
                        "description": "Minimum financial capability index",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["population", "financial_capability"],
                        "description": "Sort field (default: 'population')",
                        "default": "population",
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sort order (default: 'desc')",
                        "default": "desc",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results to return",
                    },
                },
            },
        ),
        Tool(
            name="get_mynumber_card_rate",
            description=(
                "Get My Number Card issuance rate for a Japanese municipality. "
                "Data source: 総務省「マイナンバーカード交付状況」R7.8末時点（人口はR7.1.1時点）, 1,741自治体."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "jichitai_code": {
                        "type": "string",
                        "description": "6-digit municipality code (e.g., '142018' for Yokosuka)",
                    },
                    "jichitai_name": {
                        "type": "string",
                        "description": "Municipality name (e.g., '横須賀市', '矢巾町')",
                    },
                    "prefecture": {
                        "type": "string",
                        "description": "Prefecture name for disambiguation (e.g., '神奈川県', '岩手県')",
                    },
                },
            },
        ),
        Tool(
            name="get_digital_agency_dx_data",
            description=(
                "Get Digital Agency DX Dashboard data for a Japanese municipality (DX indicators, online procedures). "
                "Data source: デジタル庁「自治体DX推進状況ダッシュボード」2024.7.12更新, 15指標+52手続, 1,742自治体."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "jichitai_code": {
                        "type": "string",
                        "description": "6-digit municipality code (e.g., '142018' for Yokosuka)",
                    },
                    "jichitai_name": {
                        "type": "string",
                        "description": "Municipality name (e.g., '横須賀市')",
                    },
                    "prefecture": {
                        "type": "string",
                        "description": "Prefecture name for disambiguation (e.g., '神奈川県')",
                    },
                    "data_category": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of data categories to retrieve (optional, returns all if not specified)",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "get_jichitai_basic_info":
        jichitai_code = arguments.get("jichitai_code")
        jichitai_name = arguments.get("jichitai_name")
        prefecture = arguments.get("prefecture")

        result = data_manager.get_jichitai_basic_info(
            jichitai_code=jichitai_code,
            jichitai_name=jichitai_name,
            prefecture=prefecture
        )

        if result:
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps({
                "error": "Municipality not found",
                "jichitai_code": jichitai_code,
                "jichitai_name": jichitai_name
            }, ensure_ascii=False))]

    elif name == "get_jichitai_code":
        jichitai_name = arguments.get("jichitai_name")
        prefecture = arguments.get("prefecture")
        fuzzy_match = arguments.get("fuzzy_match", True)

        result = data_manager.get_jichitai_code(
            jichitai_name=jichitai_name,
            prefecture=prefecture,
            fuzzy_match=fuzzy_match
        )

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "search_jichitai_by_criteria":
        population_min = arguments.get("population_min")
        population_max = arguments.get("population_max")
        prefecture = arguments.get("prefecture")
        jichitai_type = arguments.get("jichitai_type")
        financial_capability_min = arguments.get("financial_capability_min")
        sort_by = arguments.get("sort_by", "population")
        sort_order = arguments.get("sort_order", "desc")
        limit = arguments.get("limit")

        result = data_manager.search_jichitai_by_criteria(
            population_min=population_min,
            population_max=population_max,
            prefecture=prefecture,
            jichitai_type=jichitai_type,
            financial_capability_min=financial_capability_min,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit
        )

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "get_mynumber_card_rate":
        jichitai_code = arguments.get("jichitai_code")
        jichitai_name = arguments.get("jichitai_name")
        prefecture = arguments.get("prefecture")

        result = data_manager.get_mynumber_card_rate(
            jichitai_code=jichitai_code,
            jichitai_name=jichitai_name,
            prefecture=prefecture
        )

        if result:
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps({
                "error": "My Number Card data not found",
                "jichitai_code": jichitai_code,
                "jichitai_name": jichitai_name
            }, ensure_ascii=False))]

    elif name == "get_digital_agency_dx_data":
        jichitai_code = arguments.get("jichitai_code")
        jichitai_name = arguments.get("jichitai_name")
        prefecture = arguments.get("prefecture")
        data_category = arguments.get("data_category")

        result = data_manager.get_digital_agency_dx_data(
            jichitai_code=jichitai_code,
            jichitai_name=jichitai_name,
            prefecture=prefecture,
            data_category=data_category
        )

        if result:
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps({
                "error": "DX data not found",
                "jichitai_code": jichitai_code,
                "jichitai_name": jichitai_name
            }, ensure_ascii=False))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Main entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())