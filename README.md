# Jichitai Basic Information MCP Server

MCP Server for accessing Japanese municipality (自治体) basic information including population, finance data, and municipal codes.

## Features

This MCP server provides access to:

- **Population Data**: Resident registry data (住民基本台帳) for all Japanese municipalities
- **Finance Data**: Municipal finance indicators (財政力指数, 経常収支比率, etc.)
- **Municipal Codes**: Complete list of municipality codes with name matching

## Tools

### 1. `get_jichitai_basic_info`

Get comprehensive information about a municipality.

**Parameters:**
- `jichitai_code` (optional): 6-digit municipality code (e.g., "011002" for Sapporo)
- `jichitai_name` (optional): Municipality name (e.g., "札幌市")
- `prefecture` (optional): Prefecture name for disambiguation

**Example:**
```json
{
  "jichitai_code": "011002",
  "jichitai_name": "札幌市",
  "prefecture": "北海道",
  "jichitai_type": "市",
  "population": {
    "total": 1956928,
    "male": 915082,
    "female": 1041846
  },
  "households": 1104953,
  "finance": {
    "financial_capability_index": 0.71,
    "current_balance_ratio": 95.4
  }
}
```

### 2. `get_jichitai_code`

Get municipality code(s) from name with fuzzy matching.

**Parameters:**
- `jichitai_name` (required): Municipality name
- `prefecture` (optional): Prefecture name for disambiguation
- `fuzzy_match` (optional): Enable fuzzy matching (default: true)

**Example:**
```json
{
  "matches": [
    {
      "jichitai_code": "011002",
      "municipality": "札幌市",
      "prefecture": "北海道",
      "match_score": 1.0
    }
  ],
  "exact_match": true
}
```

### 3. `search_jichitai_by_criteria`

Search municipalities by various criteria.

**Parameters:**
- `population_min` (optional): Minimum population
- `population_max` (optional): Maximum population
- `prefecture` (optional): List of prefecture names
- `jichitai_type` (optional): List of municipality types ["市", "町", "村"]
- `financial_capability_min` (optional): Minimum financial capability index
- `sort_by` (optional): Sort field ("population" or "financial_capability")
- `sort_order` (optional): "asc" or "desc"
- `limit` (optional): Maximum number of results

**Example:**
```json
{
  "jichitai_list": [
    {
      "jichitai_code": "131016",
      "jichitai_name": "特別区部",
      "prefecture": "東京都",
      "population": 9733276,
      "financial_capability_index": null
    }
  ],
  "total_count": 250,
  "filtered_count": 10
}
```

## Installation

```bash
# Install dependencies
pip install -e .
```

## Data Files

The server requires the following data files in `data/source/`:

```
data/source/
├── population/
│   └── r06_municipal_population.xlsx
├── finance/
│   └── r05_finance_summary.xlsx
└── codes/
    └── municipal_codes_2019.xlsx
```

### Data File Details

#### 1. Population Data (`r06_municipal_population.xlsx`)

**Source:** 住民基本台帳に基づく人口、人口動態及び世帯数（令和6年1月1日現在）

**Download Location:** 総務省ホームページ
- URL: https://www.soumu.go.jp/main_sosiki/jichi_gyousei/daityo/jinkou_jinkoudoutai-setaisuu.html
- 具体的なダウンロードリンク: [市区町村別住民基本台帳人口](https://www.soumu.go.jp/main_content/000949768.xlsx)

**Data Structure:**
- Sheet: "R6.1.1住民基本台帳人口"
- Data starts: Row 7
- Columns:
  - Column 1-2: 都道府県コード、都道府県名
  - Column 3-5: 市区町村コード、市区町村名、支所等
  - Column 6-8: 総数、男、女（人口）
  - Column 9-11: 世帯数、転入、出生等
- Coverage: 2,288 municipalities (全市区町村)

#### 2. Finance Data (`r05_finance_summary.xlsx`)

**Source:** 令和5年度市町村別決算状況調

**Download Location:** 総務省ホームページ
- URL: https://www.soumu.go.jp/iken/kessan_jokyo_2.html
- 具体的なダウンロードリンク: [令和5年度決算状況調（市町村分）](https://www.soumu.go.jp/main_content/000943713.xlsx)

**Data Structure:**
- Sheet: "決算状況調"
- Data starts: Row 17, **Column 15 (O列)**
- Important Columns:
  - Column 15-16: 団体コード、団体名
  - Column 35 (AI列): 財政力指数
  - Column 36 (AJ列): 経常収支比率
  - Column 37 (AK列): 実質収支比率
  - Column 38 (AL列): 標準財政規模
- Coverage: 815 cities (市のみ、町村は含まれない)
- Note: 空のセルや「-」が多数存在

#### 3. Municipal Codes (`municipal_codes_2019.xlsx`)

**Source:** 全国地方公共団体コード（令和6年1月1日現在）

**Download Location:** 総務省ホームページ
- URL: https://www.soumu.go.jp/denshijiti/code.html
- 具体的なダウンロードリンク: [全国地方公共団体コード一覧](https://www.soumu.go.jp/main_content/000835837.xlsx)

**Data Structure:**
- Sheet: "R6.1.1現在の団体"
- Data starts: Row 2
- Columns:
  - Column 1: 団体コード（6桁）
  - Column 2: 都道府県名（漢字）
  - Column 3: 市区町村名（漢字）
  - Column 4: 都道府県名（カナ）
  - Column 5: 市区町村名（カナ）
- Coverage: 1,795 municipalities
- Note: 漢字・カナ両方の名称を含む

### Data Update History

- **2024-01-01**: Initial data download (令和6年1月1日現在)
- Population data: Reflects resident registry as of January 1, 2024
- Finance data: FY2023 (令和5年度) settlement data
- Municipal codes: Updated annually, current as of January 1, 2024

## Usage

### Running the Server

```bash
python -m src.server
```

### Claude Desktop Configuration

Add to your Claude Desktop config file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "jichitai-basic-information": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/jichitai-basic-information-server"
    }
  }
}
```

## Development

### Running Tests

```bash
python tests/test_basic.py
```

### Project Structure

```
jichitai-basic-information-server/
├── src/
│   ├── server.py              # MCP server entry point
│   └── data/
│       ├── data_manager.py    # Central data integration
│       ├── population_parser.py
│       ├── finance_parser.py
│       └── codes_parser.py
├── data/
│   └── source/                # Data files (see Data Files section)
├── tests/
│   └── test_basic.py
└── .mcp.json                  # MCP server configuration
```

## License

MIT License

## Notes

- Population data is from January 1, 2024 (Reiwa 6)
- Finance data is from FY2023 (Reiwa 5) settlements
- Municipal codes are updated annually by the Ministry