# Japanese Tax Calculator MCP Server

日本の税制に特化した**Model Context Protocol (MCP)** サーバーです。MCPプロトコルに完全対応し、ChatGPTやClaude DesktopなどのLLMクライアントから税務計算機能を安全に利用できます。

## MCPプロトコルとは

**Model Context Protocol (MCP)** は、OpenAIが提唱したLLM（ChatGPTなど）から外部システムに安全にアクセスするための統一仕様です。

### MCPプロトコルの特徴

- **JSON-RPC 2.0ベース**: 標準化されたリクエスト/レスポンス形式
- **初期化ハンドシェイク**: クライアントとサーバー間の能力交換
- **認証・認可**: トークンやスコープ管理による安全なアクセス
- **機能登録**: tools、resources、eventsの標準化された公開方法
- **ストリーミング対応**: リアルタイムデータ交換
- **エラーハンドリング**: 統一されたエラー処理機構

### REST APIとの違い

| 項目 | REST API | MCPプロトコル |
|------|----------|---------------|
| **目的** | 一般的なHTTPデータ交換 | LLM専用の安全な統合 |
| **プロトコル** | HTTP/HTTPS | JSON-RPC 2.0 over HTTP/WebSocket/stdio |
| **初期化** | なし | ハンドシェイク必須 |
| **機能発見** | 手動実装 | 標準化された機能公開 |
| **認証** | 各実装で異なる | 統一された認証機構 |
| **LLM統合** | 手動実装 | ネイティブサポート |

### 本プロジェクトのMCP対応

✅ **完全なMCPプロトコル実装**:
- JSON-RPC 2.0準拠のリクエスト/レスポンス処理
- MCPハンドシェイクとcapability交換
- 標準化されたtools定義と公開
- エラーハンドリングとログ機能
- 複数の通信方式サポート（HTTP、WebSocket、stdio）

✅ **LLMクライアント対応**:
- ChatGPT（将来対応予定）
- Claude Desktop（ネイティブサポート）
- その他MCPクライアント

## アーキテクチャ

```
LLMクライアント → (MCPプロトコル) → 本MCPサーバー → 税務計算エンジン
     ↓                                        ↓
ChatGPT/Claude                           内部REST API（オプション）
```

**重要**: 本プロジェクトは単なるREST APIサーバーではなく、MCPプロトコルに完全対応したMCPサーバーです。

## 機能

### MCPツール（税務計算）

本MCPサーバーは以下のツールをMCPプロトコル経由で提供します：

#### 1. 所得税計算 (`calculate_income_tax`)
年収、各種控除に基づく所得税の精密計算

#### 2. 法人税計算 (`calculate_corporate_tax`)
法人税率、事業税、地方法人税の総合計算

#### 3. 住民税計算 (`calculate_resident_tax`)
都道府県別の住民税計算（所得割・均等割）

#### 4. 法的参照検索 (`search_legal_reference`)
税法条文、タックスアンサー、判例の検索

### 高度な機能

- **RAG統合**: 国税庁タックスアンサー、財務省税制改正資料との連携
- **SQLiteインデックス**: 財務省資料の自動インデックス化と全文検索
- **セキュリティ**: 入力検証、監査ログ、JWT認証
- **キャッシュ機能**: 外部API呼び出しの効率化

## セットアップ

### 前提条件
- Python 3.8以上
- MCPクライアント（Claude Desktop推奨）

### インストール

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd TaxMCP
```

2. **仮想環境の作成**
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
```env
SERVER_HOST=localhost
SERVER_PORT=8000
DEBUG=true
SECRET_KEY=your-secret-key-here
```

### MCPサーバーの起動

#### 方法1: stdio通信（Claude Desktop推奨）
```bash
python main.py
```

#### 方法2: HTTP通信
```bash
python http_server.py
```

#### 方法3: Docker
```bash
docker compose up -d
```

## MCPクライアント接続

### Claude Desktop接続

詳細な設定方法は [Claude Desktop設定ガイド](./CLAUDE_DESKTOP_SETUP_GUIDE.md) を参照してください。

**設定例** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "tax-calculator": {
      "command": "python",
      "args": ["C:\\path\\to\\TaxMCP\\main.py"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\TaxMCP"
      }
    }
  }
}
```

### ChatGPT接続

現在のChatGPT UIでは外部MCPサーバーの直接追加はサポートされていません。詳細は [ChatGPT統合ガイド](./CHATGPT_INTEGRATION_GUIDE.md) を参照してください。

## 使用例

### Claude Desktopでの使用

```
ユーザー: 年収500万円の所得税を計算してください

Claude: 年収500万円の所得税を計算いたします。
[calculate_income_tax ツールを使用]

計算結果：
- 年収: 5,000,000円
- 給与所得控除: 1,440,000円
- 基礎控除: 480,000円
- 課税所得: 3,080,000円
- 所得税額: 205,500円
```

### MCPプロトコル直接呼び出し

```bash
# tools/list - 利用可能なツール一覧
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/list",
    "params": {}
  }'

# calculate_income_tax - 所得税計算
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "calculate_income_tax",
      "arguments": {
        "annual_income": 5000000
      }
    }
  }'
```

## 技術仕様

### MCPプロトコル実装

- **プロトコルバージョン**: MCP 2024-11-05
- **通信方式**: HTTP、WebSocket、stdio
- **メッセージ形式**: JSON-RPC 2.0
- **認証**: JWT、APIキー
- **エラーハンドリング**: 標準MCPエラーコード

### 依存関係

- **FastMCP**: MCPプロトコル実装フレームワーク
- **FastAPI**: HTTP API実装
- **SQLite**: データインデックス
- **Whoosh**: 全文検索エンジン
- **aiohttp**: 非同期HTTP通信
- **PyJWT**: JWT認証

### プロジェクト構造

```
TaxMCP/
├── main.py                    # MCPサーバー（stdio）
├── http_server.py             # MCPサーバー（HTTP）
├── mcp_handler.py             # MCPプロトコル処理
├── tax_calculator.py          # 税計算エンジン
├── security.py                # セキュリティ機能
├── config.py                 # 設定管理
├── rag_integration.py        # RAG統合
├── sqlite_indexer.py         # インデックス機能
├── requirements.txt          # 依存関係
├── CLAUDE_DESKTOP_SETUP_GUIDE.md  # Claude Desktop設定
├── CHATGPT_INTEGRATION_GUIDE.md   # ChatGPT統合ガイド
└── README.md                 # このファイル
```

## 開発

### 新しいMCPツールの追加

1. `tax_calculator.py`に計算ロジックを実装
2. `mcp_handler.py`にMCPツール定義を追加
3. セキュリティ検証を実装
4. テストケースを作成

### MCPプロトコルテスト

```bash
# MCPサーバー情報取得
curl http://localhost:8000/mcp/info

# ツール一覧取得
python -c "
import requests
response = requests.post('http://localhost:8000/mcp', json={
    'jsonrpc': '2.0',
    'id': '1',
    'method': 'tools/list',
    'params': {}
})
print(response.json())
"
```

## セキュリティ

- **入力検証**: 全パラメータの型・範囲チェック
- **認証**: JWT、APIキーによる認証
- **監査ログ**: 全操作の記録
- **レート制限**: DoS攻撃対策
- **暗号化**: 機密データの暗号化

## パフォーマンス

- **非同期処理**: asyncioによる高速処理
- **キャッシュ**: 外部API呼び出し最適化
- **インデックス**: SQLite + Whoosh高速検索
- **接続プール**: データベース接続最適化

## 関連ドキュメント

- [Claude Desktop設定ガイド](./CLAUDE_DESKTOP_SETUP_GUIDE.md) - Claude Desktopとの連携
- [ChatGPT統合ガイド](./CHATGPT_INTEGRATION_GUIDE.md) - ChatGPT統合の制限と代替策
- [アーキテクチャドキュメント](./architecture.md) - システム設計詳細
- [セキュリティガイド](./SECRET_KEY_SETUP_GUIDE.md) - セキュリティ設定
- [システムメンテナンス](./SYSTEM_MAINTENANCE_GUIDE.md) - 運用・保守手順

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。MCPプロトコルの仕様に準拠した実装を心がけてください。

## サポート

技術的な質問や問題については、GitHubのIssuesページでお知らせください。MCPプロトコル関連の質問も歓迎します。