# 自治体基本情報 MCP Server

日本の自治体（市区町村）の基本情報（人口、財政データ、自治体コード）にアクセスするためのMCPサーバーです。

## 機能

このMCPサーバーは以下のデータへのアクセスを提供します：

- **人口データ**: 全国の市区町村の住民基本台帳データ
- **財政データ**: 市町村の財政指標（財政力指数、経常収支比率など）
- **自治体コード**: 自治体コードと名称のマッチング機能付き完全リスト

## ツール

### 1. `get_jichitai_basic_info`

自治体の包括的な情報を取得します。

**パラメータ:**
- `jichitai_code` (オプション): 6桁の自治体コード（例: "011002"は札幌市）
- `jichitai_name` (オプション): 自治体名（例: "札幌市"）
- `prefecture` (オプション): 都道府県名（同名の自治体がある場合の絞り込み用）

**返り値の例:**
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

自治体名から自治体コードを取得します（あいまい検索対応）。

**パラメータ:**
- `jichitai_name` (必須): 自治体名
- `prefecture` (オプション): 都道府県名（絞り込み用）
- `fuzzy_match` (オプション): あいまい検索を有効化（デフォルト: true）

**返り値の例:**
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

様々な条件で自治体を検索します。

**パラメータ:**
- `population_min` (オプション): 最小人口
- `population_max` (オプション): 最大人口
- `prefecture` (オプション): 都道府県名のリスト
- `jichitai_type` (オプション): 自治体タイプのリスト ["市", "町", "村"]
- `financial_capability_min` (オプション): 最小財政力指数
- `sort_by` (オプション): ソート項目（"population" または "financial_capability"）
- `sort_order` (オプション): ソート順（"asc" または "desc"）
- `limit` (オプション): 結果の最大件数

**返り値の例:**
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

## インストール

```bash
# 依存パッケージのインストール
pip install -e .
```

## データファイル

サーバーは以下のデータファイルを `data/source/` に必要とします：

```
data/source/
├── population/
│   └── r06_municipal_population.xlsx
├── finance/
│   └── r05_finance_summary.xlsx
└── codes/
    └── municipal_codes_2019.xlsx
```

### データファイルの詳細

#### 1. 人口データ (`r06_municipal_population.xlsx`)

**出典:** 住民基本台帳に基づく人口、人口動態及び世帯数（令和6年1月1日現在）

**ダウンロード元:** 総務省ホームページ
- URL: https://www.soumu.go.jp/main_sosiki/jichi_gyousei/daityo/jinkou_jinkoudoutai-setaisuu.html
- 具体的なダウンロードリンク: [市区町村別住民基本台帳人口](https://www.soumu.go.jp/main_content/000949768.xlsx)

**データ構造:**
- シート名: "R6.1.1住民基本台帳人口"
- データ開始行: 7行目
- カラム構成:
  - 1-2列: 都道府県コード、都道府県名
  - 3-5列: 市区町村コード、市区町村名、支所等
  - 6-8列: 総数、男、女（人口）
  - 9-11列: 世帯数、転入、出生等
- カバレッジ: 2,288自治体（全市区町村）

#### 2. 財政データ (`r05_finance_summary.xlsx`)

**出典:** 令和5年度市町村別決算状況調

**ダウンロード元:** 総務省ホームページ
- URL: https://www.soumu.go.jp/iken/kessan_jokyo_2.html
- 具体的なダウンロードリンク: [令和5年度決算状況調（市町村分）](https://www.soumu.go.jp/main_content/000943713.xlsx)

**データ構造:**
- シート名: "決算状況調"
- データ開始位置: 17行目、**15列目（O列）から開始**
- 主要カラム:
  - 15-16列: 団体コード、団体名
  - 35列（AI列）: 財政力指数
  - 36列（AJ列）: 経常収支比率
  - 37列（AK列）: 実質収支比率
  - 38列（AL列）: 標準財政規模
- カバレッジ: 815市（市のみ、町村は含まれない）
- 注意: 空のセルや「-」が多数存在

#### 3. 自治体コード (`municipal_codes_2019.xlsx`)

**出典:** 全国地方公共団体コード（令和6年1月1日現在）

**ダウンロード元:** 総務省ホームページ
- URL: https://www.soumu.go.jp/denshijiti/code.html
- 具体的なダウンロードリンク: [全国地方公共団体コード一覧](https://www.soumu.go.jp/main_content/000835837.xlsx)

**データ構造:**
- シート名: "R6.1.1現在の団体"
- データ開始行: 2行目
- カラム構成:
  - 1列: 団体コード（6桁）
  - 2列: 都道府県名（漢字）
  - 3列: 市区町村名（漢字）
  - 4列: 都道府県名（カナ）
  - 5列: 市区町村名（カナ）
- カバレッジ: 1,795自治体
- 注意: 漢字・カナ両方の名称を含む

### データ更新履歴

- **2024-01-01**: 初回データダウンロード（令和6年1月1日現在）
- 人口データ: 令和6年1月1日時点の住民基本台帳データ
- 財政データ: 令和5年度決算データ
- 自治体コード: 年次更新、令和6年1月1日現在

## 使用方法

### サーバーの起動

```bash
python -m src.server
```

### Claude Desktop での設定

Claude Desktop の設定ファイルに以下を追加してください：

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

### Claude Code での設定

プロジェクトルートに `.mcp.json` を配置：

```json
{
  "mcpServers": {
    "jichitai-basic-information": {
      "command": "/absolute/path/to/venv/bin/python3",
      "args": ["-m", "src.server"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/jichitai-basic-information-server"
      }
    }
  }
}
```

## 開発

### テストの実行

```bash
python tests/test_basic.py
```

### プロジェクト構造

```
jichitai-basic-information-server/
├── src/
│   ├── server.py              # MCPサーバーエントリーポイント
│   └── data/
│       ├── data_manager.py    # データ統合管理
│       ├── population_parser.py
│       ├── finance_parser.py
│       └── codes_parser.py
├── data/
│   └── source/                # データファイル（上記参照）
├── tests/
│   └── test_basic.py
└── .mcp.json                  # MCPサーバー設定
```

## ライセンス

### ソフトウェア

このプロジェクトのソースコードはMITライセンスの下で提供されています。

### データ

このプロジェクトで使用している総務省のデータは、クリエイティブ・コモンズ・ライセンス 表示 4.0 国際（CC BY 4.0）と互換性のある利用ルールが適用されています。

**出典:**
- 総務省「住民基本台帳に基づく人口、人口動態及び世帯数」
- 総務省「市町村別決算状況調」
- 総務省「全国地方公共団体コード」

詳細は[LICENSE](LICENSE)ファイルをご確認ください。

## 注意事項

- 人口データは令和6年（2024年）1月1日時点のものです
- 財政データは令和5年度（2023年度）決算データです
- 自治体コードは総務省により毎年更新されます
- データの正確性について総務省は保証していません
- データを利用した結果について総務省および本プロジェクトは責任を負いません