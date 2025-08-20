# Japanese Tax Calculator MCP Server

日本の税制に特化したModel Context Protocol (MCP) サーバーです。所得税、消費税、住民税の計算機能を提供します。

## 機能

### 主要機能
- **所得税計算**: 年収、各種控除に基づく所得税の計算
- **法人税計算**: 法人税率、事業税、地方法人税の計算
- **消費税率取得**: 日付と商品カテゴリーに基づく消費税率の取得
- **住民税計算**: 都道府県別の住民税計算
- **複数年シミュレーション**: 複数年にわたる税額シミュレーション
- **都道府県情報**: サポートされている都道府県の一覧取得
- **税年度情報**: サポートされている税年度とその特徴の取得

### 高度な機能
- **法令参照機能**: 法人税法条文検索、タックスアンサー番号検索、e-Gov法令検索API統合
- **RAG統合**: 国税庁タックスアンサー、財務省税制改正資料との連携
- **SQLiteインデックス**: 財務省資料の自動インデックス化と全文検索
- **拡張税務情報検索**: 高度な検索機能とメタデータ管理
- **外部データソース統合**: Web API、スクレイピング、キャッシュ機能

### セキュリティ機能
- 入力データの検証とサニタイズ
- 監査ログ記録
- JWT認証サポート
- セキュリティイベントログ

## セットアップ

### 前提条件
- Python 3.11以上
- Docker（オプション）

### ローカル環境での実行

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd TaxMCP
```

2. **仮想環境の作成と有効化**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

4. **環境変数の設定**
`.env`ファイルを編集して必要な設定を行います：
```env
SERVER_HOST=localhost
SERVER_PORT=8000
DEBUG=true
SECRET_KEY=your-secret-key-here-change-in-production
```

⚠️ **重要**: `SECRET_KEY`は本番環境では必ず変更してください。この値はセッション管理、データ暗号化、セキュリティ機能の基盤となる重要な暗号化キーです。

📖 **詳細情報**: SECRET_KEYの適切な設定方法については、[SECRET_KEYセットアップガイド](./SECRET_KEY_SETUP_GUIDE.md)を参照してください。

5. **サーバーの起動**

#### MCPサーバー（stdio経由）
```bash
python main.py
```

#### HTTPサーバー（Web API）
```bash
python http_server.py
```

または、uvicornを直接使用：
```bash
uvicorn http_server:app --host 0.0.0.0 --port 8000 --reload
```

**注意**: 
- `main.py`: MCPクライアント用のstdio通信サーバー
- `http_server.py`: HTTP API用のWebサーバー（ヘルスチェック、外部テスト用）

### Dockerを使用した実行

1. **Docker Composeでの起動**
```bash
docker compose up -d
```

2. **ログの確認**
```bash
docker compose logs -f taxmcp
```

3. **停止**
```bash
docker compose down
```

## 使用方法

### MCPクライアントからの接続

サーバーが起動したら、MCPクライアントから以下のエンドポイントに接続できます：
- HTTP: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws`

### 利用可能なツール

#### 1. 所得税計算 (`calculate_income_tax`)
```json
{
  "annual_income": 5000000,
  "tax_year": 2024,
  "basic_deduction": 480000,
  "dependents_count": 2
}
```

#### 2. 消費税率取得 (`get_consumption_tax_rate`)
```json
{
  "date": "2024-01-01",
  "category": "standard"
}
```

#### 3. 住民税計算 (`calculate_resident_tax`)
```json
{
  "taxable_income": 3000000,
  "prefecture_code": 13
}
```

#### 4. 法人税計算 (`calculate_corporate_tax`)
```json
{
  "taxable_income": 10000000,
  "tax_year": 2024,
  "company_size": "small",
  "prefecture_code": 13
}
```

#### 5. 複数年シミュレーション (`simulate_multi_year_taxes`)
```json
{
  "annual_incomes": [4000000, 4200000, 4400000],
  "start_year": 2024,
  "prefecture_code": 13
}
```

#### 6. 法令参照検索 (`search_legal_reference`)
```json
{
  "query": "法人税法第22条",
  "search_type": "law_article",
  "limit": 10
}
```

#### 7. 拡張税務情報検索 (`search_enhanced_tax_info`)
```json
{
  "query": "消費税 軽減税率",
  "limit": 5,
  "include_metadata": true
}
```

#### 8. インデックス統計情報 (`get_index_statistics`)
```json
{}
```

### テストクライアントの実行

```bash
python test_client.py
```

## 設定

### 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `SERVER_HOST` | localhost | サーバーのホスト |
| `SERVER_PORT` | 8000 | サーバーのポート |
| `DEBUG` | false | デバッグモード |
| `SECRET_KEY` | - | JWT署名用の秘密鍵 |
| `LOG_LEVEL` | info | ログレベル |
| `AUDIT_LOG_ENABLED` | true | 監査ログの有効化 |

### 税制更新について

TaxMCPサーバーには税制改正に対応するための自動更新機能が実装されています：

- **自動税制情報取得**: 財務省、国税庁等の公式データソースから最新情報を自動取得
- **税率更新機能**: 所得税、法人税、消費税の税率変更を自動検出
- **RAG統合**: 外部データソースとの連携による情報の自動更新

税制改正時の詳細な対応手順については [SYSTEM_MAINTENANCE_GUIDE.md](SYSTEM_MAINTENANCE_GUIDE.md) を参照してください。

### ログ設定

ログは以下の場所に出力されます：
- アプリケーションログ: `logs/app.log`
- 監査ログ: `logs/audit.log`

## 開発

### プロジェクト構造

```
TaxMCP/
├── main.py                    # MCPサーバーのメインファイル
├── tax_calculator.py          # 税計算ロジック
├── security.py                # セキュリティ機能
├── config.py                 # 設定管理
├── rag_integration.py        # RAG統合機能
├── sqlite_indexer.py         # SQLiteインデックス機能
├── test_client.py            # テストクライアント
├── requirements.txt          # Python依存関係
├── Dockerfile               # Dockerイメージ定義
├── docker-compose.yml       # Docker Compose設定
├── .env                     # 環境変数
├── SECRET_KEY_SETUP_GUIDE.md # SECRET_KEY設定ガイド
├── architecture.md          # アーキテクチャドキュメント
├── rag_integration_guide.md # RAG統合ガイド
├── test_client_guide.md     # テストクライアントガイド
├── mcp_tax.md              # MCP税務サーバードキュメント
├── cache/                   # キャッシュディレクトリ
└── README.md               # このファイル
```

### 技術仕様

#### 依存関係
- **FastMCP**: Model Context Protocol サーバーフレームワーク
- **FastAPI**: 高性能なWebフレームワーク
- **SQLite**: 軽量データベース（インデックス機能用）
- **Whoosh**: 全文検索エンジン
- **Jieba**: 日本語テキスト処理
- **BeautifulSoup4**: HTMLパースィング
- **aiohttp**: 非同期HTTP クライアント
- **PyJWT**: JWT認証
- **Passlib**: パスワードハッシュ化

#### アーキテクチャ
- **MCP準拠**: Model Context Protocol v1.0に完全対応
- **非同期処理**: asyncio を使用した高性能な非同期処理
- **モジュラー設計**: 機能別に分離されたモジュール構造
- **キャッシュ機能**: 外部API呼び出しの効率化
- **セキュリティ**: 入力検証、監査ログ、JWT認証

#### パフォーマンス
- **インデックス検索**: SQLite + Whoosh による高速全文検索
- **キャッシュ**: 外部データソースのレスポンス時間短縮
- **非同期処理**: 複数リクエストの並行処理

### 新しい税計算機能の追加

1. `tax_calculator.py`に計算ロジックを追加
2. `main.py`に新しいツールを定義
3. セキュリティ検証を追加
4. テストケースを`test_client.py`に追加

### 関連ドキュメント

- [アーキテクチャドキュメント](./architecture.md) - システム設計の詳細
- [RAG統合ガイド](./rag_integration_guide.md) - RAG機能の実装詳細
- [テストクライアントガイド](./test_client_guide.md) - テスト方法の詳細
- [SECRET_KEYセットアップガイド](./SECRET_KEY_SETUP_GUIDE.md) - セキュリティ設定の詳細
- [システムメンテナンスガイド](./SYSTEM_MAINTENANCE_GUIDE.md) - 税制更新・運用手順
- [MCP税務サーバードキュメント](./mcp_tax.md) - MCP仕様の詳細

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。

## サポート

質問や問題がある場合は、GitHubのIssuesページでお知らせください。