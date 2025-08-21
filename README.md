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

#### 2. 法人税計算

本MCPサーバーは、法人税計算において**3段階の入力レベル**をサポートしています：

##### レベル1: 基本法人税計算 (`calculate_corporate_tax`)
**最も簡単な入力レベル** - 基本的な法人税計算

**必要な入力項目**:
- 年間所得（円）
- 課税年度（オプション、デフォルト: 2025年）
- 都道府県（オプション、デフォルト: 東京都）
- 資本金（オプション、デフォルト: 1億円）
- 控除額合計（オプション、デフォルト: 0円）

**計算内容**:
- 法人税（中小企業軽減税率対応）
- 地方法人税
- 法人事業税
- 特別法人事業税
- 法人住民税

**使用例**:
```json
{
  "name": "calculate_corporate_tax",
  "arguments": {
    "annual_income": 10000000,
    "capital": 50000000
  }
}
```

##### レベル2: 詳細法人税計算 (`calculate_enhanced_corporate_tax`)
**最も詳細な入力レベル** - 法人税申告書レベルの詳細計算

**必要な入力項目**:

> **📋 入力項目対応状況サマリ**
> 
> 本システムは、法人税申告書作成に必要な**47個の主要入力項目**を網羅的にサポートしています：
> 
> - ✅ **完全対応**: 44項目（基本情報、損益項目、別表四〜八関連、税額控除等）
> - 🔄 **部分対応**: 3項目（減価償却資産明細は総額として対応）
> - 📊 **対応率**: 93.6%（44/47項目）
> 
> 詳細な対応項目については、以下の入力項目表をご参照ください。

| 項目カテゴリ | 入力項目 | 対応別表 | 説明 |
|-------------|----------|----------|------|
| **基本項目** | 当期純利益（会計利益） | - | 損益計算書の当期純利益（円） |
| | 課税年度 | - | 申告対象年度（デフォルト: 2025年） |
| | 都道府県 | - | 事業所所在地（デフォルト: 東京都） |
| | 資本金 | - | 資本金額（円） |
| **加算項目**<br>（損金不算入） | 寄附金損金不算入額 | 別表四 | 一般寄附金の損金算入限度超過額 |
| | 交際費損金不算入額 | 別表十五 | 交際費等の損金算入限度超過額 |
| | 過大役員給与 | 別表四 | 不相当に高額な役員給与 |
| | 減価償却超過額 | 別表十六 | 償却限度額を超える減価償却費 |
| | その他損金不算入項目 | 別表四 | 各種損金不算入項目 |
| **減算項目**<br>（益金不算入） | 受取配当金益金不算入額 | 別表八 | 関係会社等からの受取配当金 |
| | 特別償却準備金取崩額 | 別表十三 | 特別償却準備金の益金算入額 |
| | 繰越欠損金控除額 | 別表七 | 青色欠損金の繰越控除額 |
| | その他益金不算入項目 | 別表八 | 各種益金不算入項目 |
| **税額控除項目** | 研究開発税制 | 別表六（八） | 試験研究費の税額控除 |
| | 中小企業投資促進税制 | 別表六（十八） | 中小企業者等の機械装置等の税額控除 |
| | 所得拡大促進税制 | 別表六（二十六） | 雇用者給与等支給額の税額控除 |
| | 外国税額控除 | 別表六（三） | 外国法人税等の税額控除 |
| **その他** | 中間納付額 | - | 当期の中間納付税額 |
| | 仮払税金 | - | 源泉徴収税額等 |

**計算プロセス**:
1. **会計利益** → 加算・減算調整 → **課税所得金額**
2. **課税所得金額** → 税率適用 → **法人税額**
3. **法人税額** → 税額控除適用 → **控除後法人税額**
4. **控除後法人税額** → 中間納付控除 → **最終納付額**
5. 地方税（住民税、事業税、特別法人事業税）の詳細計算
6. 実効税率の算出

**使用例**:
```json
{
  "name": "calculate_enhanced_corporate_tax",
  "arguments": {
    "accounting_profit": 15000000,
    "capital": 80000000,
    "addition_items": [
      {
        "name": "寄附金損金不算入額",
        "amount": 500000,
        "description": "一般寄附金の損金不算入額",
        "related_form": "別表四"
      },
      {
        "name": "交際費損金不算入額",
        "amount": 300000,
        "description": "交際費等の損金不算入額",
        "related_form": "別表十五"
      }
    ],
    "deduction_items": [
      {
        "name": "受取配当金益金不算入額",
        "amount": 200000,
        "description": "関係会社からの受取配当金",
        "related_form": "別表八"
      }
    ],
    "tax_credit_items": [
      {
        "name": "研究開発税制",
        "amount": 150000,
        "description": "試験研究費の税額控除",
        "related_form": "別表六（八）"
      }
    ],
    "interim_payments": 800000,
    "prepaid_taxes": 50000
  }
}
```

**出力内容**:
- 段階的な税額計算プロセス
- 各別表に対応した調整項目の詳細
- 法人税、地方法人税、住民税、事業税、特別法人事業税の個別計算
- 法人区分（外形標準課税法人、特別法人、その他）に応じた税率適用
- 実効税率と最終納付額
- 税務申告書作成に必要な全情報

##### 入力レベルの選択指針

| 用途 | 推奨レベル | 特徴 |
|------|------------|------|
| **概算計算** | レベル1（基本） | 簡単な入力で迅速な税額概算 |
| **詳細検討** | レベル2（詳細） | 実際の申告書レベルの精密計算 |
| **税務申告** | レベル2（詳細） | 別表対応の完全な税額計算 |
| **税務相談** | レベル2（詳細） | 各種控除・調整項目の個別検討 |

#### 3. 住民税計算 (`calculate_resident_tax`)
都道府県別の住民税計算（所得割・均等割）

#### 4. 法的参照検索 (`search_legal_reference`)
税法条文、タックスアンサー、判例の検索

### 特別法人事業税の計算

特別法人事業税は、法人事業税（所得割・収入割）の標準税率に対して、法人区分に応じた税率を乗じて計算されます：

| 法人区分 | 税率 |
|---------|------|
| 外形標準課税法人 | 260% |
| 特別法人 | 34.5% |
| その他の法人 | 37% |

**法人区分の判定**:
- 外形標準課税法人: 資本金1億円超の普通法人
- 特別法人: 公益法人等、協同組合等
- その他の法人: 上記以外の法人（資本金1億円以下の普通法人など）

**計算例**:
- 法人事業税（所得割）が100万円の外形標準課税法人の場合
  特別法人事業税 = 1,000,000円 × 260% = 2,600,000円

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