# MCP Server 追加ツール仕様書（Phase 2）

**プロジェクト名**: `jichitai-research-mcp-server`
**対象**: 既存MCPサーバーへのツール追加
**作成日**: 2025-09-30
**優先度**: Phase 1 - 高優先度（高価値・低難易度）

---

## 1. 概要

既存の`jichitai-research-mcp-server`に以下の2つのツールを追加する：

1. **マイナンバーカード交付率取得ツール**
2. **デジタル庁DXダッシュボードデータ取得ツール**

これらのツールは、自治体のデジタル化推進状況を把握し、手続きナビゲーションシステムの営業ターゲット選定に活用する。

---

## 2. ツール1: マイナンバーカード交付率取得

### 2.1 ツール名
`get_mynumber_card_rate`

### 2.2 目的
- 自治体別のマイナンバーカード交付率を取得
- デジタルサービスへの住民の受容性を評価する指標として活用

### 2.3 データソース

#### J-LIS（地方公共団体情報システム機構）公式データ
**URL**: https://www.kojinbango-card.go.jp/kofuokuritsushinchoku/

**データ形式**:
- CSV/Excelファイル
- 月次更新（毎月初旬に前月末時点のデータを公表）

**公開データの構造（推定）**:
```
列1: 団体コード（6桁）
列2: 都道府県名
列3: 市区町村名
列4: 人口（人）
列5: 交付枚数（枚）
列6: 交付率（%）
列7: 基準日（YYYY年MM月DD日）
```

**注意点**:
- Excelファイルには説明文やグラフが含まれる可能性がある
- データ行の開始位置を特定する必要がある
- 都道府県の小計・合計行が含まれる可能性がある（自治体コードでフィルタリング）

### 2.4 入力パラメータ

```typescript
{
  jichitai_code?: string;     // 自治体コード（6桁）例: "142018"（横須賀市）
  jichitai_name?: string;     // 自治体名 例: "横須賀市"
  prefecture?: string;        // 都道府県名（自治体名の曖昧性解消用）
  as_of_date?: string;        // 基準日（YYYY-MM-DD形式）省略時は最新
}
```

**バリデーション**:
- `jichitai_code`または`jichitai_name`のいずれかは必須
- 両方指定された場合は`jichitai_code`を優先

### 2.5 出力

```typescript
{
  jichitai_code: string;           // 自治体コード
  jichitai_name: string;           // 自治体名
  prefecture: string;              // 都道府県名
  mynumber_card_data: {
    population: number;            // 人口（人）
    issued_cards: number;          // 交付枚数（枚）
    issuance_rate: number;         // 交付率（%）例: 72.5
    as_of_date: string;            // 基準日（YYYY-MM-DD形式）
    rank_in_prefecture?: number;   // 都道府県内順位（オプション）
    rank_nationwide?: number;      // 全国順位（オプション）
  };
  data_source: {
    source_name: string;           // "J-LIS マイナンバーカード交付状況"
    source_url: string;            // ダウンロード元URL
    downloaded_at: string;         // ダウンロード日時（ISO 8601形式）
  };
}
```

**エラーケース**:
```typescript
{
  error: string;                   // エラーメッセージ
  jichitai_code: string | null;
  jichitai_name: string | null;
}
```

### 2.6 実装の詳細

#### ステップ1: データのダウンロード
1. J-LISの公式ページにアクセス
2. 最新のCSV/Excelファイルのダウンロードリンクを取得
3. ファイルをダウンロード（キャッシュディレクトリに保存）

#### ステップ2: データのパース
1. Excelファイルを読み込み
2. データ行の開始位置を特定（ヘッダー行を検索）
3. 自治体コードが6桁の行のみを抽出（都道府県合計行を除外）
4. JSON形式に変換

#### ステップ3: データの検索
1. `jichitai_code`または`jichitai_name`で該当行を検索
2. `jichitai_name`の場合は既存の`get_jichitai_code`ツールで自治体コードに変換
3. 該当データを返却

#### ステップ4: キャッシング
- **キャッシュキー**: `mynumber_card_YYYYMM`（例: `mynumber_card_202501`）
- **キャッシュ有効期限**: 1ヶ月（次回更新まで）
- **キャッシュディレクトリ**: `~/.jichitai-research-mcp-cache/mynumber/`

### 2.7 使用例

```typescript
// 例1: 自治体コードで取得
const result = await get_mynumber_card_rate({
  jichitai_code: "142018"
});
// => {
//   jichitai_name: "横須賀市",
//   mynumber_card_data: { issuance_rate: 72.5, ... }
// }

// 例2: 自治体名で取得
const result = await get_mynumber_card_rate({
  jichitai_name: "矢巾町",
  prefecture: "岩手県"
});

// 例3: 過去データの取得（キャッシュがあれば）
const result = await get_mynumber_card_rate({
  jichitai_code: "142018",
  as_of_date: "2024-12-31"
});
```

### 2.8 テストケース

- [ ] 横須賀市（142018）のマイナンバーカード交付率を取得できる
- [ ] 矢巾町（033227）のデータを自治体名から取得できる
- [ ] 存在しない自治体コードに対して適切なエラーを返す
- [ ] データのキャッシングが正常に機能する
- [ ] 2回目のアクセスはキャッシュから高速に取得できる

---

## 3. ツール2: デジタル庁DXダッシュボードデータ取得

### 3.1 ツール名
`get_digital_agency_dx_data`

### 3.2 目的
- 自治体のDX推進状況を定量的に把握
- 電子申請対応手続き数、DX推進計画策定状況等を取得
- 手続きナビの営業ターゲット選定に活用

### 3.3 データソース

#### デジタル庁「自治体DX推進状況ダッシュボード」
**URL**: https://www.digital.go.jp/resources/govdashboard/local-government-dx

**データ形式**:
- ダッシュボードページにデータビジュアライゼーション
- APIまたはダウンロード可能なCSV/JSONがある可能性（要調査）
- ない場合はスクレイピングが必要

**公開データの内容（推定）**:
- 電子申請対応手続き数
- DX推進計画の策定状況（策定済/策定中/未策定）
- AI-OCR導入状況
- RPA導入状況
- 書かない窓口導入状況
- 自治体情報システムの標準化対応状況
- オープンデータの公開状況

### 3.4 入力パラメータ

```typescript
{
  jichitai_code?: string;          // 自治体コード（6桁）
  jichitai_name?: string;          // 自治体名
  prefecture?: string;             // 都道府県名（曖昧性解消用）
  data_category?: string[];        // 取得するデータカテゴリ（省略時は全て）
                                   // ["電子申請", "DX計画", "AI-OCR", "RPA", "書かない窓口", "標準化", "オープンデータ"]
  as_of_date?: string;             // 基準日（省略時は最新）
}
```

### 3.5 出力

```typescript
{
  jichitai_code: string;
  jichitai_name: string;
  prefecture: string;
  dx_data: {
    electronic_application?: {
      total_procedures: number;              // 総手続き数
      online_available_procedures: number;   // オンライン対応手続き数
      online_ratio: number;                  // オンライン化率（%）
      as_of_date: string;                    // 基準日
    };
    dx_promotion_plan?: {
      status: string;                        // "策定済" | "策定中" | "未策定"
      plan_period?: string;                  // 計画期間（例: "2021-2025"）
      plan_url?: string;                     // 計画文書URL
      as_of_date: string;
    };
    ai_ocr?: {
      status: string;                        // "導入済" | "導入予定" | "未導入"
      implementation_date?: string;          // 導入時期
      as_of_date: string;
    };
    rpa?: {
      status: string;                        // "導入済" | "導入予定" | "未導入"
      implementation_date?: string;
      as_of_date: string;
    };
    kakanai_madoguchi?: {                   // 書かない窓口
      status: string;                        // "導入済" | "導入予定" | "未導入"
      implementation_date?: string;
      as_of_date: string;
    };
    system_standardization?: {
      status: string;                        // "対応済" | "対応中" | "未対応"
      target_systems?: string[];             // 対象システム
      as_of_date: string;
    };
    open_data?: {
      datasets_count: number;                // 公開データセット数
      evaluation?: string;                   // 評価（例: "★★★★☆"）
      as_of_date: string;
    };
  };
  data_source: {
    source_name: string;                     // "デジタル庁 自治体DX推進状況ダッシュボード"
    source_url: string;
    accessed_at: string;                     // アクセス日時
  };
}
```

**エラーケース**:
```typescript
{
  error: string;
  jichitai_code: string | null;
  jichitai_name: string | null;
  details?: string;                          // エラー詳細（デバッグ用）
}
```

### 3.6 実装の詳細

#### ステップ1: データソースの調査
**【重要】実装前に以下を確認してください**:

1. **APIの有無を確認**:
   - デジタル庁のダッシュボードページのソースコードを確認
   - ブラウザの開発者ツールでネットワークタブを確認
   - JSON/CSVを返すAPIエンドポイントがあるか調査

2. **ダウンロード可能なデータの有無を確認**:
   - ダッシュボードページにCSV/Excelのダウンロードリンクがあるか
   - ある場合はダウンロードして構造を確認

3. **スクレイピングの必要性を判断**:
   - APIもダウンロードもない場合、HTMLスクレイピングが必要
   - その場合、ページ構造の変更に脆弱になることに注意

#### ステップ2: データ取得の実装
**パターンA: APIが利用可能な場合**
```python
# 例: APIエンドポイントにリクエスト
response = requests.get(
    f"https://api.digital.go.jp/v1/local-government-dx/{jichitai_code}",
    headers={"User-Agent": "jichitai-research-mcp-server/1.0"}
)
data = response.json()
```

**パターンB: CSV/Excelダウンロードの場合**
```python
# ファイルをダウンロード
download_url = "https://www.digital.go.jp/.../dx_data.csv"
df = pd.read_csv(download_url, encoding="utf-8")

# 自治体コードで検索
result = df[df["団体コード"] == jichitai_code]
```

**パターンC: HTMLスクレイピングの場合**
```python
# BeautifulSoupでHTMLを解析
soup = BeautifulSoup(html, "html.parser")
# 自治体データを含む要素を抽出
# ※ ページ構造に依存するため、実際のHTML構造を確認して実装
```

#### ステップ3: データの正規化
- 各カテゴリのデータを統一フォーマットに変換
- 日付フォーマットを統一（YYYY-MM-DD）
- 欠損データは`null`または該当カテゴリを省略

#### ステップ4: キャッシング
- **キャッシュキー**: `digital_agency_dx_YYYYMM`
- **キャッシュ有効期限**: 1ヶ月（デジタル庁の更新頻度に応じて調整）
- **キャッシュディレクトリ**: `~/.jichitai-research-mcp-cache/digital_agency/`

### 3.7 実装における注意点

#### データソースの不確実性
**デジタル庁のダッシュボードは比較的新しいサービスのため、以下の可能性があります**:

1. **APIが公開されていない可能性**
   - その場合、スクレイピングまたはダウンロードCSV解析で実装

2. **データの更新頻度が不明**
   - 四半期ごと、半年ごとなど、頻度を確認してキャッシュ期限を設定

3. **全自治体のデータが揃っていない可能性**
   - 一部自治体のデータが欠損している場合の処理を実装
   - エラーではなく「データなし」として返す

4. **データ項目が変更される可能性**
   - ダッシュボードの仕様変更に対応できるよう、柔軟な実装を推奨
   - データ項目のマッピングを設定ファイル化

#### 実装の優先順位
**最も重要なデータ項目**（これだけでも十分価値がある）:
1. ✅ **電子申請対応手続き数** - 手続きナビのニーズ評価に直結
2. ✅ **DX推進計画策定状況** - DX意識の高さを示す指標

**次に重要**:
3. **書かない窓口導入状況** - 手続きナビと親和性が高い
4. **AI-OCR、RPA導入状況** - デジタル化への積極性を示す

**優先度は低い**（余裕があれば実装）:
5. システム標準化対応状況
6. オープンデータ公開状況

### 3.8 使用例

```typescript
// 例1: 電子申請データのみ取得
const result = await get_digital_agency_dx_data({
  jichitai_code: "142018",
  data_category: ["電子申請"]
});
// => {
//   dx_data: {
//     electronic_application: {
//       total_procedures: 1500,
//       online_available_procedures: 350,
//       online_ratio: 23.3
//     }
//   }
// }

// 例2: 全データを取得
const result = await get_digital_agency_dx_data({
  jichitai_name: "横須賀市"
});

// 例3: DX推進計画の策定状況のみ
const result = await get_digital_agency_dx_data({
  jichitai_code: "142018",
  data_category: ["DX計画"]
});
```

### 3.9 テストケース

- [ ] 横須賀市のDXデータを取得できる
- [ ] 電子申請対応手続き数が正しく取得できる
- [ ] DX推進計画の策定状況が取得できる
- [ ] データが存在しない自治体に対して適切なエラーまたは空データを返す
- [ ] キャッシングが正常に機能する

---

## 4. 共通仕様

### 4.1 エラーハンドリング

両ツールで共通のエラーハンドリングを実装：

```typescript
// エラーコード
ERROR_CODES = {
  "NETWORK_ERROR": "データソースへの接続に失敗",
  "PARSE_ERROR": "データの解析に失敗",
  "NOT_FOUND": "該当する自治体データが見つかりません",
  "INVALID_PARAMETER": "パラメータが不正です",
  "DATA_UNAVAILABLE": "データが公開されていません",
  "CACHE_ERROR": "キャッシュの読み書きに失敗"
}
```

### 4.2 ログ出力

デバッグ用のログを出力（オプション、環境変数で制御）:

```python
logger.info(f"Fetching mynumber card rate for {jichitai_code}")
logger.debug(f"Cache hit: {cache_path}")
logger.error(f"Failed to parse data: {error_message}")
```

### 4.3 既存ツールとの連携

- **`get_jichitai_code`**: 自治体名→自治体コード変換
- **`get_jichitai_basic_info`**: マイナンバーカードデータやDXデータを追加で返すことも検討

例：`get_jichitai_basic_info`の拡張案
```typescript
{
  // 既存のデータ
  jichitai_code: "142018",
  population: { ... },
  finance: { ... },

  // 新規追加（オプション）
  mynumber_card?: { issuance_rate: 72.5, ... },
  dx_status?: { electronic_application: { ... }, ... }
}
```

**実装方針**:
- 既存ツールへの影響を最小化するため、新しいツールとして独立実装
- 将来的に`get_jichitai_basic_info`に統合することも検討

---

## 5. 実装のステップ

### Phase 2-1: マイナンバーカードツール（推定工数: 2-3時間）
1. ✅ J-LISのWebサイトからダウンロードURLを取得（10分）
2. ✅ Excelファイルの構造を確認（10分）
3. ✅ ダウンロード・パース処理を実装（60分）
4. ✅ キャッシング処理を実装（30分）
5. ✅ ツール関数の実装（30分）
6. ✅ テストケース作成・実行（20分）

### Phase 2-2: デジタル庁DXツール（推定工数: 3-5時間）
1. ✅ **データソースの調査**（30-60分）← 最重要
   - APIの有無確認
   - ダウンロード可能なデータの確認
   - スクレイピングが必要か判断
2. ✅ データ取得処理の実装（60-90分）
   - API/CSV/スクレイピングのいずれか
3. ✅ データの正規化処理（30分）
4. ✅ キャッシング処理（30分）
5. ✅ ツール関数の実装（30分）
6. ✅ テストケース作成・実行（30分）

**注意**: デジタル庁のデータソースの状況により、実装方法が大きく変わる可能性があります。

---

## 6. 納品物

### 6.1 コード
- `src/tools/get_mynumber_card_rate.py` (または `.ts`)
- `src/tools/get_digital_agency_dx_data.py` (または `.ts`)
- 既存の`server.py`への統合コード

### 6.2 テストコード
- `tests/test_mynumber_card_rate.py`
- `tests/test_digital_agency_dx_data.py`

### 6.3 ドキュメント
- `README.md`への追記（新ツールの説明）
- データソースのURL、更新頻度、注意事項をドキュメント化

### 6.4 動作確認
- 横須賀市、矢巾町、おおい町の3自治体でテスト実行
- 結果をJSON形式で出力し、正常性を確認

---

## 7. 実装時の質問・確認事項

### 7.1 デジタル庁DXダッシュボードについて
**【実装前に必ず確認してください】**

1. デジタル庁のダッシュボードページの実際の構造を調査
2. APIまたはダウンロード可能なデータの有無を確認
3. データの項目名、フォーマット、更新頻度を確認
4. 全自治体のデータが揃っているか確認

**確認後、以下を報告してください**:
- データソースの種類（API/CSV/スクレイピング）
- 利用可能なデータ項目のリスト
- データの更新頻度
- 実装上の制約事項

### 7.2 J-LISマイナンバーカードデータについて
**【実装前に確認】**

1. 最新のExcelファイルのダウンロードリンク
2. ファイルの正確な構造（ヘッダー行の位置、カラム名）
3. データの更新頻度（毎月何日頃に更新されるか）

---

## 8. 完成後の確認

### 8.1 動作確認コマンド例

```typescript
// マイナンバーカード交付率
const mynumber = await get_mynumber_card_rate({
  jichitai_code: "142018"
});
console.log(mynumber.mynumber_card_data.issuance_rate); // => 72.5%

// デジタル庁DXデータ
const dx = await get_digital_agency_dx_data({
  jichitai_code: "142018",
  data_category: ["電子申請", "DX計画"]
});
console.log(dx.dx_data.electronic_application.online_ratio); // => 23.3%
```

### 8.2 統合テスト

既存の`get_jichitai_basic_info`と組み合わせて使用：

```typescript
// 横須賀市の包括的な情報取得
const basic = await get_jichitai_basic_info({ jichitai_code: "142018" });
const mynumber = await get_mynumber_card_rate({ jichitai_code: "142018" });
const dx = await get_digital_agency_dx_data({ jichitai_code: "142018" });

// 3つのデータを統合して営業資料を作成
const comprehensive_data = {
  ...basic,
  mynumber_card_rate: mynumber.mynumber_card_data.issuance_rate,
  online_procedures: dx.dx_data.electronic_application.online_available_procedures,
  dx_plan_status: dx.dx_data.dx_promotion_plan.status
};
```

---

## 9. 今後の拡張性

Phase 3以降で追加予定のツール（参考）:
- `get_okuyami_madoguchi_status` - おくやみ窓口設置状況
- `search_gikai_gijiroku` - 議会議事録検索
- `get_nais_procurement_info` - NAIS調達情報

これらとの連携を考慮した実装を推奨。

---

## 付録A: データソース調査チェックリスト

### A.1 J-LIS マイナンバーカード交付率
- [ ] 公式ページのURL確認: https://www.kojinbango-card.go.jp/kofuokuritsushinchoku/
- [ ] 最新データのダウンロードリンク取得
- [ ] ファイル形式確認（Excel/CSV）
- [ ] ファイル内のデータ構造確認
- [ ] 更新頻度確認（月次/四半期/不定期）

### A.2 デジタル庁 自治体DXダッシュボード
- [ ] 公式ページのURL確認: https://www.digital.go.jp/resources/govdashboard/local-government-dx
- [ ] ページのHTML構造を確認
- [ ] APIエンドポイントの有無確認（ブラウザ開発者ツール）
- [ ] ダウンロード可能なCSV/Excelの有無確認
- [ ] 利用可能なデータ項目のリスト作成
- [ ] データの更新頻度確認

**調査結果を報告してから実装に着手してください。**

---

**以上がPhase 2の追加ツール仕様書です。実装をお願いします。**