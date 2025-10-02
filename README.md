# 自治体基本情報 MCP Server

日本の自治体（市区町村）の基本情報（人口、財政データ、自治体コード）にアクセスするためのMCPサーバーです。

## 機能

このMCPサーバーは以下のデータへのアクセスを提供します：

- **人口データ**: 全国の市区町村の住民基本台帳データ
- **財政データ**: 市町村の財政指標（財政力指数、経常収支比率など）
- **自治体コード**: 自治体コードと名称のマッチング機能付き完全リスト
- **マイナンバーカード交付率**: 市区町村別のマイナンバーカード交付状況
- **DX推進状況**: デジタル庁による自治体DX推進状況（15指標 + 52手続のオンライン申請率）

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

### 4. `get_mynumber_card_rate`

市区町村のマイナンバーカード交付率を取得します。

**データ内容:**
- マイナンバーカード交付枚数と交付率
- 令和7年8月末時点のデータ
- 1,741自治体をカバー

**パラメータ:**
- `jichitai_code` (オプション): 6桁の自治体コード（例: "142018"は横須賀市）
- `jichitai_name` (オプション): 自治体名（例: "横須賀市"）
- `prefecture` (オプション): 都道府県名（絞り込み用）

**返り値の例:**
```json
{
  "jichitai_code": "142018",
  "jichitai_name": "横須賀市",
  "prefecture": "神奈川県",
  "mynumber_card_data": {
    "population": 379041,           // 人口（R7.1.1時点）
    "issued_cards": 296127,         // 交付枚数（累計）
    "issuance_rate": 78.13          // 交付率（%）
  },
  "data_source": {
    "source_name": "総務省 マイナンバーカード交付状況",
    "source_url": "https://www.soumu.go.jp/kojinbango_card/kofujokyo.html"
  }
}
```

**活用例:**
- デジタルサービスへの住民受容性評価
- マイナンバーカード普及率による自治体比較
- 電子申請サービス導入のターゲティング

### 5. `get_digital_agency_dx_data`

デジタル庁のDX推進状況ダッシュボードデータを取得します。

**データ内容:**
- **DX推進体制・取組状況**: 15指標
  - CIOの任命、全体方針策定、外部人材活用、職員育成など
- **オンライン申請の実施状況**: 52手続
  - 子育て・介護26手続（児童手当、保育施設申込、要介護認定など）
  - よく使う32手続（図書館予約、施設予約、粗大ゴミ申込など）
- 2024年7月12日更新データ
- 1,742自治体をカバー

**パラメータ:**
- `jichitai_code` (オプション): 6桁の自治体コード（例: "142018"は横須賀市）
- `jichitai_name` (オプション): 自治体名（例: "横須賀市"）
- `prefecture` (オプション): 都道府県名（絞り込み用）
- `data_category` (オプション): 取得するデータカテゴリ（省略時は全て）

**返り値の詳細:**
```json
{
  "jichitai_code": "142018",
  "jichitai_name": "横須賀市",
  "prefecture": "神奈川県",
  "dx_data": {
    "dx_indicators": {
      // DX推進体制（15指標）
      "CIOの任命": "未実施",
      "CIO補佐官等の任命": "未実施",
      "全体方針策定": "実施",
      "全庁的な体制構築": "実施",
      "外部人材活用": "実施",
      "職員育成の取組": "実施",
      "全職員対象研修の実施": "実施",
      "AIの導入状況": "実施",
      "RPAの導入状況": "実施",
      "テレワークの導入状況": "実施",
      "マイナンバーカードの保有状況": "72%",
      "子育て・介護26手続のオンライン化状況": "46%",
      "よく使う32手続のオンライン化状況": "63%",
      "よく使う32手続のオンライン化状況_実施されている手続総数（分母）": 24,
      "よく使う32手続のオンライン化状況_実施されている手続総数のうち「オンライン化済」と回答した手続数（分子）": 15
    },
    "online_procedures": {
      // よく使う32手続（オンライン申請率%、null=未実施）
      "図書館の図書貸出予約等": null,
      "文化・スポーツ施設等の利用予約等": 15.8,
      "研修・講習・各種イベント等の申込": null,
      "粗大ごみ収集の申込": 4.5,
      "犬の登録申請、死亡届": 10.7,
      "職員採用試験申込": 100.0,
      "転出届": 2.4,

      // 子育て・介護26手続（オンライン申請率%、null=未実施）
      "児童手当等の現況届": 21.1,
      "児童手当等の受給資格及び児童手当の額についての認定請求": null,
      "保育施設等の利用申込": null,
      "妊娠の届出": null,
      "要介護・要支援認定の申請": null,
      "要介護・要支援更新認定の申請": null,
      "高額介護（予防）サービス費の支給申請": null,

      // その他の手続...
      "産業廃棄物の処理、運搬の実績報告": 69.7
    }
  },
  "data_source": {
    "source_name": "デジタル庁 自治体DX推進状況ダッシュボード",
    "source_url": "https://www.digital.go.jp/resources/govdashboard/local-government-dx"
  }
}
```

**DX指標の詳細:**

| カテゴリ | 指標 | 値の意味 |
|---------|------|---------|
| DX推進体制等 | CIOの任命 | "実施" / "未実施" |
| | CIO補佐官等の任命 | "実施" / "未実施" |
| | 全体方針策定 | "実施" / "未実施" |
| | 全庁的な体制構築 | "実施" / "未実施" |
| | 外部人材活用 | "実施" / "未実施" |
| | 職員育成の取組 | "実施" / "未実施" |
| | 全職員対象研修の実施 | "実施" / "未実施" |
| 業務DX化 | AIの導入状況 | "実施" / "未実施" |
| | RPAの導入状況 | "実施" / "未実施" |
| | テレワークの導入状況 | "実施" / "未実施" |
| 住民サービスDX化 | マイナンバーカード保有状況 | パーセンテージ文字列 |
| | 子育て・介護26手続オンライン化 | パーセンテージ文字列 |
| | よく使う32手続オンライン化 | パーセンテージ文字列 |

**オンライン申請率データ（52手続）:**

手続のオンライン申請率は、以下の計算式で算出されています：
```
オンライン申請率(%) = (オンライン申請件数 / 全申請件数) × 100
```

- 数値: オンライン申請率（%）
- null または空文字列: 当該手続きを実施していない

**活用例:**
- DX推進度による自治体ランキング作成
- 電子申請サービスの導入状況分析
- 手続きナビゲーションシステムの営業ターゲット選定
- AI/RPA導入済み自治体の抽出
- オンライン申請率の低い手続きの特定

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
├── codes/
│   └── municipal_codes_2019.xlsx
├── mynumber/
│   └── mynumber_card_rate.xlsx
└── dx_dashboard/
    └── extracted/
        ├── 市区町村毎のDX進捗状況_市区町村比較.xlsx
        └── 市区町村毎のDX進捗状況_行政手続のオンライン申請率.xlsx
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

#### 4. マイナンバーカードデータ (`mynumber_card_rate.xlsx`)

**出典:** マイナンバーカード交付状況（令和7年8月末時点）

**ダウンロード元:** 総務省ホームページ
- URL: https://www.soumu.go.jp/kojinbango_card/kofujokyo.html
- 具体的なダウンロードリンク: [令和7年8月末時点データ](https://www.soumu.go.jp/main_content/001028752.xlsx)

**データ構造:**
- シート名: "公表用"
- データ開始行: 119行目（118行目は全国集計）
- カラム構成:
  - A列: 都道府県名
  - B列: 市区町村名
  - C列: 人口（R7.1.1時点）
  - D列: 保有枚数（R7.8末時点）
  - E列: 人口に対する保有枚数率（交付率）
- カバレッジ: 1,741自治体
- 注意: 市区町村コードは含まれていない（名称マッチングが必要）

#### 5. DXダッシュボードデータ

**出典:** デジタル庁 自治体DX推進状況ダッシュボード（2024年7月12日更新）

**ダウンロード元:** デジタル庁ホームページ
- URL: https://www.digital.go.jp/resources/govdashboard/local-government-dx
- ZIPファイル: [DXダッシュボードデータ](https://www.digital.go.jp/assets/contents/node/basic_page/field_ref_resources/51a5a201-e0dd-493f-9c21-0692402d93e6/85162d87/20240712_resources_govdashboard_local_governmentdx_table_01.zip)

**データ構造:**
- ファイル1: 市区町村毎のDX進捗状況_市区町村比較.xlsx
  - 15のDX指標（CIO任命、全体方針策定、AI/RPA導入状況など）
  - 横持ち形式（市区町村が列、指標が行）
- ファイル2: 市区町村毎のDX進捗状況_行政手続のオンライン申請率.xlsx
  - 52手続のオンライン申請率
  - 横持ち形式（市区町村が列、手続が行）
- カバレッジ: 1,742自治体
- 注意: 市区町村コードは含まれていない（名称マッチングが必要）

### データ更新履歴

- **2024-01-01**: Phase 1 データダウンロード
  - 人口データ: 令和6年1月1日時点の住民基本台帳データ
  - 財政データ: 令和5年度決算データ
  - 自治体コード: 年次更新、令和6年1月1日現在
- **2025-09-30**: Phase 2 データ追加
  - マイナンバーカードデータ: 令和7年8月末時点
  - DXダッシュボードデータ: 2024年7月12日更新

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