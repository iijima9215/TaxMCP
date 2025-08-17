# RAG統合機能ガイド

## 概要

日本税制計算MCPサーバーにRAG（Retrieval-Augmented Generation）統合機能が追加されました。この機能により、公式データソースから最新の税制情報を取得し、計算精度と信頼性を向上させることができます。

## 主な機能

### 1. 最新税制情報取得 (`get_latest_tax_info`)

外部データソースから最新の税制情報を検索・取得します。

**パラメータ:**
- `query`: 検索クエリ（例："基礎控除", "法人税率"）
- `category`: カテゴリフィルター（`income_tax`, `corporate_tax`, `consumption_tax`等）
- `tax_year`: 対象年度（2020-2025）

**使用例:**
```json
{
  "query": "基礎控除",
  "category": "income_tax",
  "tax_year": 2025
}
```

### 2. 税率更新情報取得 (`get_tax_rate_updates`)

指定年度の税制改正による税率変更情報を取得します。

**パラメータ:**
- `tax_year`: 対象年度（デフォルト：2025）

**使用例:**
```json
{
  "tax_year": 2025
}
```

## データソース

### 1. 財務省税制改正資料
- **URL**: https://www.mof.go.jp/tax_policy/tax_reform/outline/index.html
- **内容**: 毎年の税制改正要点、法人税率・控除・インセンティブ等
- **更新頻度**: 週1回
- **キャッシュ期間**: 168時間（1週間）

### 2. 国税庁タックスアンサー
- **URL**: https://www.nta.go.jp/taxes/shiraberu/taxanswer/index.htm
- **内容**: 所得税・法人税・消費税・相続税のFAQ形式公式解説
- **更新頻度**: 日1回
- **キャッシュ期間**: 24時間

### 3. e-Gov法令検索（将来実装予定）
- **URL**: https://elaws.e-gov.go.jp/
- **内容**: 所得税法・法人税法・租税特別措置法等の法文
- **更新頻度**: 3日に1回

### 4. 自治体サイト（将来実装予定）
- **内容**: 住民税・事業税・固定資産税の条例情報
- **更新頻度**: 自治体により異なる

## 技術仕様

### アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCPクライアント   │ -> │   MCPサーバー    │ -> │  RAG統合モジュール │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        v
                                              ┌─────────────────┐
                                              │  外部データソース │
                                              │ ・財務省        │
                                              │ ・国税庁        │
                                              │ ・e-Gov         │
                                              └─────────────────┘
```

### 主要クラス

#### `RAGIntegration`
- メインの統合クラス
- 外部データソースとの連携を管理

#### `TaxDataFetcher`
- データ取得の実装クラス
- 非同期HTTP通信とスクレイピング

#### `RAGCache`
- キャッシュ管理クラス
- ファイルベースのキャッシュシステム

#### `TaxInformation`
- 取得した税制情報のデータクラス
- メタデータと関連度スコアを含む

### キャッシュシステム

- **保存場所**: `cache/` ディレクトリ
- **形式**: Pickleファイル
- **キー**: MD5ハッシュ
- **有効期限**: データソースごとに設定
- **自動削除**: 期限切れキャッシュは自動削除

### エラーハンドリング

- **ネットワークエラー**: フォールバック機能でキャッシュデータを使用
- **パースエラー**: ログ記録後、空の結果を返却
- **タイムアウト**: 30秒でタイムアウト

## 設定とカスタマイズ

### 依存関係

```txt
aiohttp>=3.9.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

### 環境変数（オプション）

```bash
# キャッシュディレクトリ
RAG_CACHE_DIR=cache

# タイムアウト設定（秒）
RAG_TIMEOUT=30

# ユーザーエージェント
RAG_USER_AGENT="TaxMCP-RAG/1.0 (Tax Calculation Service)"
```

### カスタムデータソース追加

新しいデータソースを追加する場合：

1. `TaxDataSource` インスタンスを作成
2. `TaxDataFetcher` にフェッチメソッドを追加
3. `RAGIntegration.get_latest_tax_info` を更新

```python
# 例：新しいデータソース
new_source = TaxDataSource(
    name="新しいデータソース",
    url="https://example.com/tax-data",
    source_type="api",
    update_frequency=24
)
```

## 使用例

### 基本的な使用方法

```python
# 最新の所得税情報を検索
result = await rag_integration.get_latest_tax_info(
    query="基礎控除",
    category="income_tax"
)

# 2025年度の税率更新情報を取得
rate_updates = await rag_integration.get_tax_rate_updates(2025)
```

### MCPツールとしての使用

```json
// 最新税制情報取得
{
  "method": "get_latest_tax_info",
  "params": {
    "query": "法人税率",
    "category": "corporate_tax",
    "tax_year": 2025
  }
}

// 税率更新情報取得
{
  "method": "get_tax_rate_updates",
  "params": {
    "tax_year": 2025
  }
}
```

## パフォーマンス最適化

### キャッシュ戦略

- **頻繁にアクセスされるデータ**: 長期キャッシュ（1週間）
- **リアルタイム性が重要なデータ**: 短期キャッシュ（24時間）
- **検索結果**: クエリごとにキャッシュ

### 非同期処理

- 複数データソースの並行取得
- aiohttp による非同期HTTP通信
- コネクションプールの活用

### メモリ使用量

- 大きなHTMLページの部分的パース
- 不要なデータの早期削除
- ストリーミング処理の活用

## セキュリティ

### アクセス制御

- User-Agentの設定
- リクエスト頻度の制限
- タイムアウトの設定

### データ検証

- 取得データの整合性チェック
- 悪意のあるコンテンツのフィルタリング
- SSL/TLS通信の強制

## トラブルシューティング

### よくある問題

**1. ネットワーク接続エラー**
```
エラー: aiohttp.ClientConnectorError
解決策: ネットワーク接続を確認、プロキシ設定を確認
```

**2. パースエラー**
```
エラー: BeautifulSoup parsing error
解決策: lxmlパーサーがインストールされているか確認
```

**3. キャッシュエラー**
```
エラー: Permission denied on cache directory
解決策: cache/ディレクトリの権限を確認
```

### ログ確認

```python
import logging
logging.getLogger('rag_integration').setLevel(logging.DEBUG)
```

### テスト実行

```bash
# RAG統合のテスト
python -c "import asyncio; from rag_integration import test_rag_integration; asyncio.run(test_rag_integration())"

# 全体テスト
python test_client.py
```

## 今後の拡張予定

### Phase 2: 高度な検索機能
- セマンティック検索の実装
- 自然言語クエリの対応
- 関連度スコアの改善

### Phase 3: リアルタイム更新
- Webhookによる即座更新
- RSS/Atomフィードの監視
- 変更差分の検出

### Phase 4: AI統合
- LLMによる情報要約
- 自動的な税制変更の影響分析
- 予測的な税制改正情報

## ライセンス

MIT License - 詳細は LICENSE ファイルを参照

## サポート

技術的な質問や問題報告は、プロジェクトのIssueトラッカーまでお願いします。