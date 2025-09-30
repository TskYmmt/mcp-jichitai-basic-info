# MCP Server 仕様書: 自治体調査支援サーバー

**プロジェクト名**: `jichitai-research-mcp-server`
**バージョン**: 1.0.0
**作成日**: 2025-09-30
**目的**: 日本の地方自治体（市区町村）に関する公的統計データの検索・取得を支援するMCPサーバー

---

## 1. 概要

### 1.1 目的
このMCPサーバーは、日本の自治体調査プロジェクト（特に手続きナビゲーションシステム導入自治体の分析）において、以下を実現する：

1. **総務省等の公的統計データへの効率的なアクセス**
2. **自治体基本情報（人口、財政等）の一括取得**
3. **自治体コードによる名寄せ・データ統合**
4. **CSVやExcelファイルの構造化データとしての提供**

### 1.2 主要な利用シーン
- 全国1,741自治体の人口・世帯数データの一括取得
- 特定自治体群（例：手続きナビ導入23自治体）の財政データ抽出
- 自治体名から自治体コードへの変換
- 人口規模別、地域別の自治体リスト生成

### 1.3 データソース
- 総務省「住民基本台帳に基づく人口、人口動態及び世帯数」
- 総務省「市町村別決算状況調」
- 総務省「全国地方公共団体コード」
- その他、e-Stat（政府統計ポータル）のデータ

---

## 2. ツール仕様

### Tool 1: `search_soumu_statistics`
**目的**: 総務省の統計ページから利用可能なデータセットを検索する

#### 入力パラメータ
```typescript
{
  category: string;  // "人口", "財政", "地方公共団体コード" 等
  year?: number;     // 年度（省略時は最新）
  format?: string;   // "excel", "csv", "pdf" 等のファイル形式
}
```

#### 出力
```typescript
{
  datasets: Array<{
    title: string;           // データセット名
    url: string;            // ダウンロードURL
    year: number;           // 対象年度
    format: string;         // ファイル形式
    description: string;    // 説明
    fileSize?: string;      // ファイルサイズ
    lastUpdated?: string;   // 最終更新日
  }>;
}
```

#### 実装ヒント
- 総務省の以下のページをスクレイピング：
  - 人口: https://www.soumu.go.jp/main_sosiki/jichi_gyousei/daityo/jinkou.html
  - 財政: https://www.soumu.go.jp/iken/shichouson_kessan.html
  - 地方公共団体コード: https://www.soumu.go.jp/denshijiti/code.html
- HTML解析でダウンロードリンクを抽出
- メタデータ（年度、形式等）をパース

---

### Tool 2: `download_soumu_data`
**目的**: 総務省統計データをダウンロードし、構造化データとして返す

#### 入力パラメータ
```typescript
{
  url: string;              // ダウンロードURL（Tool 1で取得）
  sheet_name?: string;      // Excelの場合、シート名（省略時は最初のシート）
  skip_rows?: number;       // スキップする行数（ヘッダー前の説明文等）
  encoding?: string;        // 文字エンコーディング（デフォルト: "utf-8"）
}
```

#### 出力
```typescript
{
  data: Array<Record<string, any>>;  // JSON形式のデータ配列
  columns: string[];                 // カラム名のリスト
  row_count: number;                 // 行数
  metadata: {
    source_url: string;
    downloaded_at: string;
    file_format: string;
  };
}
```

#### 実装ヒント
- Excel: `openpyxl`（Python）または`xlsx`（Node.js）で読み込み
- CSV: `pandas`（Python）または`csv-parser`（Node.js）
- ファイルをダウンロードして一時ディレクトリに保存
- データをJSON配列に変換して返す
- 総務省のExcelは複雑な構造（結合セル、ヘッダーが複数行等）に注意

---

### Tool 3: `get_jichitai_basic_info`
**目的**: 自治体コードまたは自治体名から基本情報を取得する

#### 入力パラメータ
```typescript
{
  jichitai_code?: string;    // 自治体コード（6桁）例: "141003"（横須賀市）
  jichitai_name?: string;    // 自治体名 例: "横須賀市"
  prefecture?: string;       // 都道府県名（自治体名の曖昧性解消用）
  data_year?: number;        // データ年度（省略時は最新）
}
```

#### 出力
```typescript
{
  jichitai_code: string;           // 自治体コード
  jichitai_name: string;           // 正式名称
  prefecture: string;              // 都道府県
  jichitai_type: string;           // "市", "町", "村", "特別区", "政令市", "中核市" 等
  population: {
    total: number;                 // 総人口
    male: number;                  // 男性人口
    female: number;                // 女性人口
    households: number;            // 世帯数
    as_of_date: string;            // 基準日
  };
  finance?: {                      // 財政データ（利用可能な場合）
    general_account_budget: number;        // 一般会計歳入歳出決算額（千円）
    financial_capability_index: number;    // 財政力指数
    current_balance_ratio: number;         // 経常収支比率
    real_debt_service_ratio: number;       // 実質公債費比率
    fiscal_year: number;                   // 会計年度
  };
  data_sources: {
    population_source: string;     // 人口データのソースURL
    finance_source?: string;       // 財政データのソースURL
  };
}
```

#### 実装ヒント
- 内部で事前にダウンロードした総務省データをキャッシュ
- 自治体名の表記ゆれに対応（"横須賀市" = "よこすか市" = "Yokosuka"）
- 財政データは年度がずれている場合があるので最新を選択

---

### Tool 4: `search_jichitai_by_criteria`
**目的**: 条件に合致する自治体のリストを取得する

#### 入力パラメータ
```typescript
{
  population_min?: number;         // 最小人口
  population_max?: number;         // 最大人口
  prefecture?: string[];           // 都道府県フィルター（複数指定可）
  jichitai_type?: string[];        // 自治体類型フィルター ["市", "町", "村", "特別区"]
  financial_capability_min?: number;  // 最小財政力指数
  sort_by?: string;                // ソート基準 "population", "financial_capability" 等
  sort_order?: "asc" | "desc";     // ソート順
  limit?: number;                  // 取得件数上限
}
```

#### 出力
```typescript
{
  jichitai_list: Array<{
    jichitai_code: string;
    jichitai_name: string;
    prefecture: string;
    jichitai_type: string;
    population: number;
    financial_capability_index?: number;
  }>;
  total_count: number;             // マッチした総数
  filtered_count: number;          // 返却した件数
}
```

#### 実装ヒント
- 全自治体データをキャッシュしてフィルタリング
- 複数条件のAND検索
- ソート機能の実装

---

### Tool 5: `get_jichitai_code`
**目的**: 自治体名から自治体コードを取得する（名寄せ専用ツール）

#### 入力パラメータ
```typescript
{
  jichitai_name: string;     // 自治体名（例: "横須賀市", "おおい町"）
  prefecture?: string;       // 都道府県名（曖昧性解消用）
  fuzzy_match?: boolean;     // あいまい検索（デフォルト: true）
}
```

#### 出力
```typescript
{
  matches: Array<{
    jichitai_code: string;
    jichitai_name: string;          // 正式名称
    prefecture: string;
    match_score: number;             // マッチスコア（0-1）
  }>;
  exact_match: boolean;              // 完全一致したか
}
```

#### 実装ヒント
- 表記ゆれへの対応が重要
  - ひらがな・カタカナ・漢字の統一
  - "市", "町", "村"の有無
  - "おおい町"（福井県）vs "大井町"（神奈川県）のような同名自治体
- レーベンシュタイン距離やファジーマッチング

---

### Tool 6: `merge_jichitai_data`
**目的**: ユーザー提供のデータ（例：手続きナビ導入23自治体リスト）と総務省データをマージする

#### 入力パラメータ
```typescript
{
  user_data: Array<{
    jichitai_name?: string;
    jichitai_code?: string;
    [key: string]: any;              // ユーザー定義の追加カラム
  }>;
  merge_keys: string[];              // マージに使うキー ["jichitai_code"] or ["jichitai_name"]
  include_population?: boolean;      // 人口データを追加（デフォルト: true）
  include_finance?: boolean;         // 財政データを追加（デフォルト: true）
}
```

#### 出力
```typescript
{
  merged_data: Array<{
    // ユーザーデータの全カラム
    // + 人口データ（population_total, population_male 等）
    // + 財政データ（general_account_budget 等）
    // + 自治体基本情報（prefecture, jichitai_type 等）
    [key: string]: any;
  }>;
  merge_stats: {
    total_input_rows: number;
    successful_merges: number;
    failed_merges: number;
    failed_rows: Array<{
      row_index: number;
      jichitai_name?: string;
      reason: string;
    }>;
  };
}
```

#### 実装ヒント
- Tool 5を内部で使用して名寄せ
- マッチしなかった行は警告を返す
- CSVファイルのパスを受け取る代替版も検討

---

### Tool 7: `export_to_csv`
**目的**: 取得・加工したデータをCSVファイルとして出力する

#### 入力パラメータ
```typescript
{
  data: Array<Record<string, any>>;  // 出力するデータ
  output_path: string;                // 出力先ファイルパス
  columns?: string[];                 // 出力するカラム（省略時は全カラム）
  encoding?: string;                  // 文字エンコーディング（デフォルト: "utf-8-sig"）
}
```

#### 出力
```typescript
{
  success: boolean;
  output_path: string;
  row_count: number;
  message: string;
}
```

#### 実装ヒント
- BOM付きUTF-8（`utf-8-sig`）でExcel対応
- カラム順序の制御
- 日付フォーマットの統一

---

## 3. データキャッシング戦略

### 3.1 キャッシュの必要性
総務省データは大容量（数MB～数十MB）で、毎回ダウンロードすると時間がかかるため、ローカルキャッシュを実装する。

### 3.2 キャッシュディレクトリ構造
```
~/.jichitai-research-mcp-cache/
├── population/
│   ├── 2025_population_data.json
│   ├── 2024_population_data.json
│   └── metadata.json
├── finance/
│   ├── 2023_finance_data.json
│   ├── 2022_finance_data.json
│   └── metadata.json
└── jichitai_codes/
    └── jichitai_code_master.json
```

### 3.3 キャッシュ更新ポリシー
- **人口データ**: 年1回更新（毎年1月頃に総務省が公表）
- **財政データ**: 年1回更新（毎年秋頃に公表）
- **自治体コード**: 市町村合併時に更新（随時、ただし頻度は低い）
- **キャッシュ有効期限**: 30日（古いデータの場合は自動再ダウンロード）

### 3.4 キャッシュ管理ツール（オプション）

#### Tool 8: `cache_status`
キャッシュの状態を確認する

```typescript
// 入力なし
// 出力
{
  cache_dir: string;
  datasets: Array<{
    category: string;
    year: number;
    cached_at: string;
    age_days: number;
    file_size: string;
    status: "valid" | "expired" | "missing";
  }>;
}
```

#### Tool 9: `clear_cache`
キャッシュをクリアする

```typescript
{
  category?: string;  // "population", "finance", "all"
  year?: number;      // 特定年度のみクリア
}
```

---

## 4. エラーハンドリング

### 4.1 想定されるエラー
1. **ネットワークエラー**: 総務省サイトへの接続失敗
2. **ファイル形式エラー**: Excelの構造が想定と異なる
3. **名寄せ失敗**: 自治体名が見つからない
4. **データ欠損**: 一部自治体のデータが含まれていない

### 4.2 エラーレスポンス形式
```typescript
{
  success: false;
  error: {
    code: string;           // "NETWORK_ERROR", "PARSE_ERROR", "NOT_FOUND" 等
    message: string;        // ユーザー向けエラーメッセージ
    details?: any;          // デバッグ用詳細情報
  };
}
```

---

## 5. 技術スタック推奨

### 5.1 言語
- **Python** (推奨)
  - `pandas`: データ処理
  - `openpyxl`: Excel読み込み
  - `requests`: HTTP通信
  - `beautifulsoup4`: HTMLスクレイピング
  - `mcp`: MCPサーバーSDK

- **Node.js** (代替)
  - `xlsx`: Excel読み込み
  - `csv-parser`: CSV読み込み
  - `axios`: HTTP通信
  - `cheerio`: HTMLスクレイピング
  - `@modelcontextprotocol/sdk`: MCPサーバーSDK

### 5.2 外部依存
- 総務省Webサイト（スクレイピング対象）
- ローカルファイルシステム（キャッシュ用）

---

## 6. 実装の優先順位

### Phase 1: MVP（最小機能）
1. ✅ **Tool 2**: `download_soumu_data` - 指定URLからデータダウンロード
2. ✅ **Tool 3**: `get_jichitai_basic_info` - 自治体基本情報取得
3. ✅ **Tool 5**: `get_jichitai_code` - 自治体名→コード変換

**これだけあれば、ユーザーが手動でURLを調べて、データを取得できる**

### Phase 2: 自動化強化
4. ✅ **Tool 1**: `search_soumu_statistics` - 総務省サイトからURL自動検索
5. ✅ **Tool 4**: `search_jichitai_by_criteria` - 条件検索
6. ✅ **キャッシング機能**: 自動キャッシュ

**総務省サイトのURL探索を自動化**

### Phase 3: データ統合支援
7. ✅ **Tool 6**: `merge_jichitai_data` - ユーザーデータとのマージ
8. ✅ **Tool 7**: `export_to_csv` - CSV出力
9. ✅ **Tool 8, 9**: キャッシュ管理

**調査プロジェクトのワークフローを完全サポート**

---

## 7. 使用例

### 例1: 手続きナビ導入23自治体の人口・財政データを取得

```typescript
// ステップ1: 自治体名から自治体コードを取得
const yokosuka = await get_jichitai_code({
  jichitai_name: "横須賀市"
});
// => { jichitai_code: "142018", ... }

// ステップ2: 基本情報取得
const info = await get_jichitai_basic_info({
  jichitai_code: "142018"
});
// => { population: { total: 367293, ... }, finance: { ... } }

// ステップ3: 23自治体分をループ処理して配列作成
// ステップ4: CSV出力
await export_to_csv({
  data: results,
  output_path: "/path/to/output.csv"
});
```

### 例2: 人口10万人以上の市を抽出

```typescript
const cities = await search_jichitai_by_criteria({
  population_min: 100000,
  jichitai_type: ["市"],
  sort_by: "population",
  sort_order: "desc"
});
// => 約250自治体のリスト
```

### 例3: ユーザーCSVとマージ

```typescript
// user_data.csv: 手続きナビ導入23自治体（自治体名のみ）
const merged = await merge_jichitai_data({
  user_data: [
    { jichitai_name: "横須賀市", tetsuzuki_navi: true, implementation_date: "2021-04-01" },
    { jichitai_name: "矢巾町", tetsuzuki_navi: true, implementation_date: "2023-12-04" },
    // ... 21件
  ],
  merge_keys: ["jichitai_name"],
  include_population: true,
  include_finance: true
});
// => 人口・財政データが追加された配列
```

---

## 8. テストケース

### 8.1 基本機能テスト
- [ ] 横須賀市の人口・財政データを正常に取得できる
- [ ] "おおい町"（福井県）と"大井町"（神奈川県）を正しく区別できる
- [ ] 存在しない自治体名に対して適切なエラーを返す
- [ ] 人口10万人以上の市を正しく抽出できる

### 8.2 エッジケーステスト
- [ ] 総務省サイトが503エラーの場合、適切にリトライまたはエラー処理
- [ ] Excelファイルの構造が変わった場合の検出
- [ ] 市町村合併で自治体コードが変わった場合の対応
- [ ] キャッシュが破損した場合の再取得

### 8.3 パフォーマンステスト
- [ ] 1,741自治体全件の基本情報取得が60秒以内に完了
- [ ] キャッシュ使用時は10秒以内に完了

---

## 9. 将来の拡張可能性

### 9.1 追加データソース候補
- **e-Stat API**: 政府統計の総合窓口（API経由でのデータ取得）
- **地方公共団体情報システム機構（J-LIS）**: マイナンバーカード交付率等
- **デジタル庁**: 自治体DX推進状況ダッシュボード
- **各都道府県の統計サイト**: より詳細な市町村データ

### 9.2 追加機能候補
- **Tool 10**: `get_prefecture_summary` - 都道府県別サマリー統計
- **Tool 11**: `compare_jichitai` - 複数自治体の比較分析
- **Tool 12**: `visualize_data` - グラフ生成（人口ピラミッド、財政推移等）
- **Tool 13**: `get_historical_data` - 過去データの時系列取得

### 9.3 AI統合
- **自然言語クエリ**: "神奈川県内で人口30万人前後の市は？"
- **推論機能**: "この自治体は手続きナビのターゲットか？"（人口・予算から判定）

---

## 10. セキュリティ・倫理的考慮

### 10.1 スクレイピングのマナー
- ✅ robots.txtを尊重
- ✅ リクエスト間隔を適切に設定（最低1秒）
- ✅ User-Agentを適切に設定
- ✅ 過度な負荷をかけない

### 10.2 データの取り扱い
- ✅ 公開されているデータのみを取得
- ✅ 個人情報は含まれない（自治体の統計データのみ）
- ✅ データソースを明記（総務省統計であることを出力に含める）

---

## 11. ドキュメント

### 11.1 README.md
- インストール方法
- 基本的な使い方
- ツール一覧と簡単な説明

### 11.2 API仕様書
- 本ドキュメント（mcp_server_spec.md）

### 11.3 チュートリアル
- 手続きナビ導入自治体の分析ワークフロー
- CSV出力までの完全な手順

---

## 12. プロジェクト構成案（Python版）

```
jichitai-research-mcp-server/
├── README.md
├── pyproject.toml                    # Poetry設定
├── mcp_server_spec.md               # 本ドキュメント
├── src/
│   ├── __init__.py
│   ├── server.py                    # MCPサーバーのエントリポイント
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search_soumu_statistics.py
│   │   ├── download_soumu_data.py
│   │   ├── get_jichitai_basic_info.py
│   │   ├── search_jichitai_by_criteria.py
│   │   ├── get_jichitai_code.py
│   │   ├── merge_jichitai_data.py
│   │   └── export_to_csv.py
│   ├── data/
│   │   ├── cache_manager.py         # キャッシュ管理
│   │   ├── soumu_scraper.py         # 総務省スクレイパー
│   │   └── data_parser.py           # Excel/CSV パーサー
│   └── utils/
│       ├── jichitai_matcher.py      # 自治体名の名寄せロジック
│       └── error_handler.py         # エラーハンドリング
├── tests/
│   ├── test_basic_info.py
│   ├── test_jichitai_matcher.py
│   └── test_data_merge.py
└── cache/                           # キャッシュディレクトリ（.gitignore）
```

---

## 13. 次のアクション

### 開発者（MCPサーバープロジェクト側）
1. ✅ Phase 1のMVP実装（Tool 2, 3, 5）
2. ✅ 総務省サイトの構造調査
3. ✅ Excelファイルのパース処理実装
4. ✅ 基本的なテストケース作成

### ユーザー（本プロジェクト側）
1. ✅ 総務省データの具体的なURLとファイル構造を確認
2. ✅ 手続きナビ導入23自治体リストをCSV形式で準備
3. ✅ MCPサーバー完成後、実際のデータ取得を試行
4. ✅ 取得データを用いて調査分析を実施

---

## 付録A: 総務省データの具体的な構造（実データ分析結果）

### A.1 住民基本台帳人口データ（市区町村別）

#### データソース
**総務省公式ページ**: https://www.soumu.go.jp/main_sosiki/jichi_gyousei/daityo/jinkou_jinkoudoutai-setaisuu.html
**e-Stat（推奨）**: https://www.e-stat.go.jp/stat-search/files?tstat=000001039591

#### 必要なファイル
1. **【総計】市区町村別人口、人口動態及び世帯数** (表番号 24-03または類似)
2. **【総計】市区町村別年齢階級別人口** (表番号 24-04または類似)

**ファイル形式**: Excel (.xlsx)

#### 実データ構造（令和6年1月1日現在・検証済み）

**ファイル名**: `000959256.xlsx` (市区町村別人口・世帯数)
**ダウンロードURL**: https://www.soumu.go.jp/main_content/000959256.xlsx
**シート名**: `人口、世帯数、人口動態（市区町村別）【総計】`
**データサイズ**: 2,288行 × 25列

**実際のデータ構造**:
```
行1: タイトル行
  "令和6年1月1日住民基本台帳人口・世帯数、令和5年（1月1日から同年12月31日まで）人口動態（市区町村別）（総計）"

行2-5: 複数行ヘッダー（結合セルあり）
  行2: 年度情報 (例: "令和6年", "令和5年")
  行3: 西暦 (例: "2024年", "2023年")
  行4: データ種別 (例: "人口", "世帯数", "住民票記載数")
  行5: 詳細項目 (例: "男", "女", "計", "世帯数", "転入者数（国内）")

行6: カラム名とデータ型
  - 列1: 団体コード (文字列, 例: "011002")
  - 列2: 都道府県名 (文字列, 例: "北海道")
  - 列3: 市区町村名 (文字列, 例: "札幌市", 都道府県行の場合は "-")
  - 列4: 人口（男）(整数)
  - 列5: 人口（女）(整数)
  - 列6: 人口（計）(整数)
  - 列7: 世帯数 (整数)
  - 列8: 転入者数（国内）(整数)
  - 列9: 転入者数（国外）(整数)
  - 列10: 転入者数（計）(整数)
  - 列11: 出生者数 (整数)
  - 列12以降: その他の人口動態データ（転出、死亡、増減率等）

行7: 全国合計行
  団体コード: "-", 都道府県名: "合計", 市区町村名: "-"

行8: 北海道合計行
  団体コード: "010006", 都道府県名: "北海道", 市区町村名: "-"

行9以降: 市区町村データ
  - 札幌市: "011002"
  - 札幌市中央区: "011011"
  - 札幌市北区: "011029"
  - ... (全国の市区町村)
```

**データの特徴**:
- 行7: 全国合計（団体コード="-"）
- 行8以降: 都道府県合計行と市区町村行が混在
  - 都道府県行: 市区町村名が"-"（例: 010006, 北海道, -）
  - 市区町村行: 市区町村名あり（例: 011002, 北海道, 札幌市）
- 政令指定都市は区別にも行が存在（例: 札幌市中央区、北区等）
- データ行数: 約2,288行（全国合計1 + 都道府県47 + 市区町村約2,240）

**パース実装の注意点**:
1. **ヘッダー行の処理**: 行2-6の複数行ヘッダーを統合してカラム名を生成
2. **データ開始行**: 行7（全国合計）から開始、実際の自治体データは行8から
3. **都道府県行の除外**: 市区町村名が"-"の行はスキップ（または別途処理）
4. **団体コードの処理**: 文字列として扱う（ゼロパディング維持のため）
5. **Noneの処理**: 結合セルやデータ欠損でNoneが含まれる可能性あり

### A.2 市町村別決算状況調（財政データ）

#### データソース
**総務省公式ページ**: https://www.soumu.go.jp/iken/kessan_jokyo_2.html
**最新データ（令和5年度）**: https://www.soumu.go.jp/iken/zaisei/r05_shichouson.html

#### 必要なファイル
1. **[第1] 総括** - r05_finance_summary.xlsx
   - URL: https://www.soumu.go.jp/main_content/000999900.xlsx
   - 内容: 財政力指数、経常収支比率、実質公債費比率等

2. **[第2] 普通会計** - r05_finance_general.xlsx
   - URL: https://www.soumu.go.jp/main_content/000999901.xlsx
   - 内容: 一般会計歳入歳出決算額、各種財政指標

**ファイル形式**: Excel (.xlsx)

#### 実データ構造（令和5年度・検証済み）

**重要**: データは列15(O列)から始まります。列1-14は空白です。

---

##### ファイル1: [第1] 総括 (r05_finance_summary.xlsx)

**シート名**: `AFAHO11H0010`
**データサイズ**: 982行 × 49列
**データ範囲**: O1:AW982

**実際の構造**:
```
行1-9: タイトル、説明（スキップ）

行10: ヘッダー行（列15から開始）
  - 列15(O): 団体コード
  - 列16(P): 団体名
  - 列17(Q): 住民基本台帳登載人口
  - 列19(S): 国勢調査人口
  - 列25(Y): 基準財政需要額
  - 列26(Z): 基準財政収入額
  - 列27(AA): 標準財政規模
  - 列29(AC): 実質収支比率
  - 列30(AD): 経常収支比率
  - 列34(AH): 公債費負担比率
  - 列35(AI): 財政力指数
  - 列36-39: 健全化判断比率（実質赤字比率、連結実質赤字比率、実質公債費比率、将来負担比率）
  - 列40(AN): 歳入総額
  - 列41(AO): 歳出総額
  - 列42(AP): 歳入歳出差引額
  - 列44(AR): 実質収支

行11-16: サブヘッダー（単位等）

行17以降: データ行（815自治体）
  例: 011002 札幌市 1956928 0.71 95.4
```

**データ例**:
| 団体コード | 団体名 | 人口 | 財政力指数 | 経常収支比率 |
|---|---|---|---|---|
| 011002 | 札幌市 | 1,956,928 | 0.71 | 95.4 |
| 012025 | 函館市 | 240,218 | 0.48 | 94.5 |

**総データ行数**: 815行（市のみ。町村は別ファイルの可能性）

---

##### ファイル2: [第2] 普通会計 (r05_finance_general.xlsx)

**シート名**: `AFAHO11H0020`
**データサイズ**: 977行 × 129列

**実際の構造**:
```
行1-8: タイトル、説明（スキップ）

行9-11: 複数行ヘッダー（列15から開始）
  行9: 大カテゴリ（一、二、三...）
  行10: 中カテゴリ（地方税、地方譲与税、地方消費税交付金...）
  行11: 詳細項目（市町村民税個人分、法人分、固定資産税...）

  主要列:
  - 列15(O): 団体コード
  - 列16(P): 団体名
  - 列17(Q): 地方税（計）
  - 列18(R): うち市町村民税個人分
  - 列19(S): うち市町村民税法人分
  - 列20(T): うち固定資産税
  - 列21(U): うち市町村たばこ税
  - 列24-: 地方譲与税、各種交付金、国庫支出金、地方債等

行12-16: 単位行

行17以降: データ行
  例: 011002 札幌市 353772974 148160727 24334019 125591269...
```

**データ例**:
| 団体コード | 団体名 | 地方税 | 市町村民税個人分 | 固定資産税 |
|---|---|---|---|---|
| 011002 | 札幌市 | 353,772,974千円 | 148,160,727千円 | 125,591,269千円 |

---

#### パース実装ガイドライン

**共通の注意点**:
1. ✅ **データ開始列**: 列15(O列)から。列1-14は完全に空白
2. ✅ **`data_only=True`で読み込み可能**: 当初の懸念は解決
3. ✅ **ヘッダー処理**: 複数行ヘッダーを統合してカラム名を生成
4. ✅ **データ型**:
   - 団体コード: 文字列（6桁、ゼロパディングあり）
   - 金額: 整数（千円単位）
   - 比率: 浮動小数点数（%）

**読み込みコード例**:
```python
import openpyxl

# 総括ファイル
wb = openpyxl.load_workbook('r05_finance_summary.xlsx', data_only=True)
ws = wb['AFAHO11H0010']

# ヘッダー取得（行10、列15から）
headers = []
for c in range(15, ws.max_column + 1):
    val = ws.cell(10, c).value
    if val:
        headers.append(val)

# データ取得（行17から、列15から）
data = []
for r in range(17, ws.max_row + 1):
    code = ws.cell(r, 15).value  # 団体コード
    if code and str(code).strip():
        row = [ws.cell(r, c).value for c in range(15, ws.max_column + 1)]
        data.append(row)
```

**その他の注意点**:
- 財政データは人口データより1-2年遅れる（令和5年度決算は令和6年秋公表）
- 市のみで815自治体（町村は別ファイルの可能性あり）
- 政令指定都市も市として1行でカウント（区別データは別ファイル）

### A.3 全国地方公共団体コード

#### データソース
**総務省公式ページ**: https://www.soumu.go.jp/denshijiti/code.html

#### 必要なファイル
**都道府県コード及び市区町村コード** (令和6年1月1日現在)
- URL: https://www.soumu.go.jp/main_content/000925835.xlsx
- ローカル保存名: `municipal_codes_2019.xlsx`

**ファイル形式**: Excel (.xlsx)

#### 実データ構造
**シート1: R6.1.1現在の団体** (1,795行 × 7列)

```
行1: ヘッダー行
  - 列1: 団体コード (6桁文字列, 例: "011002")
  - 列2: 都道府県名（漢字） (例: "北海道")
  - 列3: 市区町村名（漢字） (例: "札幌市", 都道府県のみの場合はNone)
  - 列4: 都道府県名（カナ） (例: "ﾎｯｶｲﾄﾞｳ", 半角カナ)
  - 列5: 市区町村名（カナ） (例: "ｻｯﾎﾟﾛｼ", 半角カナ)
  - 列6-7: 空列
行2以降: データ行
  - 都道府県行: 市区町村名がNone（例: 010006, 北海道）
  - 市区町村行: 市区町村名あり（例: 011002, 北海道, 札幌市）
```

**シート2: R6.1.1政令指定都市** (192行 × 6列)
- 政令指定都市の区別データ

**データ特性**:
- 団体コードは6桁の文字列（ゼロパディングあり）
- 都道府県: 47件（コード末尾が000, 001, 006など）
- 市区町村: 約1,741件（2024年1月1日現在）
- 政令指定都市の行政区: 別シートに格納
- 合併・廃置分合により定期的に更新される

**自治体コードの構造**:
```
[都道府県2桁][市区町村3桁][チェックデジット1桁]

例:
- 011002: 01(北海道) + 100(札幌市) + 2(チェックデジット)
- 142018: 14(神奈川県) + 201(横須賀市) + 8
```

---

## 付録B: データ取得の実装ガイドライン

### B.1 推奨データ取得方法

#### 人口データ
1. **e-Stat APIの利用**（推奨）
   - API Key取得: https://www.e-stat.go.jp/api/
   - 統計表ID: `000001039591`
   - メリット: プログラマティックに最新データ取得可能
   - デメリット: API Key申請が必要

2. **e-Statからの手動ダウンロード**（代替案）
   - フィルター条件: 調査年=最新年, 集計地域区分=市区町村, 形式=EXCEL
   - データを`data/source/population/`に保存
   - キャッシュとして利用

3. **総務省PDF報道資料からの抽出**（非推奨）
   - PDFからのデータ抽出は信頼性が低い

#### 財政データ
1. **e-StatのCSVダウンロード**（推奨）
   - 統計表ID: `000001077755` (地方財政状況調査)
   - Excel形式より安定

2. **総務省サイトからの直接ダウンロード**（要注意）
   - ファイル形式が複雑で解析困難な場合あり
   - 可能であれば再フォーマットを推奨

#### 自治体コード
1. **ローカルキャッシュの利用**（推奨）
   - 年1回の更新頻度なので、キャッシュで十分
   - 定期的に総務省サイトから最新版をダウンロード

### B.2 データパース実装の注意点

#### Excelファイルの読み込み
```python
# 推奨ライブラリ
import openpyxl  # または pandas

# 基本的な読み込み
wb = openpyxl.load_workbook(file_path, data_only=True)
ws = wb[sheet_name]

# 注意点
# 1. data_only=True で数式ではなく値を取得
# 2. 結合セルの処理（merged_cells プロパティ）
# 3. ヘッダー行の特定（複数行にわたる場合あり）
# 4. 空白行・説明行のスキップ
```

#### データクリーニング
```python
# 必要な処理
# 1. 都道府県サマリー行の除外（団体コードで判定）
# 2. 空白セルの処理（None, "", "-" など）
# 3. 数値のカンマ区切りの削除
# 4. 全角数字の半角変換
# 5. 文字エンコーディングの正規化（特に自治体名）
```

---

**以上が自治体調査支援MCPサーバーの仕様書です。付録A・Bには実データ分析結果と実装ガイドラインを含みます。**