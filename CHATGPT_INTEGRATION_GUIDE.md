# ChatGPT連携ガイド - TaxMCP サーバー

このガイドでは、TaxMCPサーバーをChatGPTと連携して使用する方法を詳細に説明します。本番環境（https://taxmcp.ami-j2.com）との連動設定も含まれています。

## 概要

TaxMCPサーバーは、Model Context Protocol (MCP) を使用してChatGPTと連携し、高度な税務計算機能を提供します。ChatGPTがMCPクライアントとして動作し、TaxMCPサーバーの各種税務ツールにアクセスできます。

### 利用可能な環境
- **ローカル環境**: localhost:8000
- **本番環境**: https://taxmcp.ami-j2.com

## 前提条件

### 必要なソフトウェア
- Python 3.11以上
- ChatGPT Plus または ChatGPT Pro アカウント
- MCP対応のChatGPTクライアント（Claude Desktop等）

### システム要件
- Windows 10/11、macOS 10.15以上、またはLinux
- 最低2GB RAM
- インターネット接続

## セットアップ手順

### ステップ1: TaxMCPサーバーの準備

#### 1.1 プロジェクトのクローンと環境構築
```bash
# リポジトリのクローン
git clone <repository-url>
cd TaxMCP

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

#### 1.2 環境変数の設定
`.env`ファイルを編集：
```env
SERVER_HOST=localhost
SERVER_PORT=8000
DEBUG=false
SECRET_KEY=your-strong-secret-key-for-production
LOG_LEVEL=info
AUDIT_LOG_ENABLED=true
```

⚠️ **重要**: `SECRET_KEY`は必ず強力な値に変更してください。詳細は[SECRET_KEYセットアップガイド](./SECRET_KEY_SETUP_GUIDE.md)を参照。

#### 1.3 サーバーの起動
```bash
python main.py
```

サーバーが正常に起動すると、以下のメッセージが表示されます：
```
TaxMCP Server starting on localhost:8000
MCP Server is ready for connections
```

### ステップ2: ChatGPT側の設定

#### 2.1 MCP設定ファイルの作成

ChatGPTクライアント（Claude Desktop等）の設定ディレクトリに`mcp_servers.json`を作成：

**Windows:**
```
%APPDATA%\Claude\mcp_servers.json
```

**macOS:**
```
~/Library/Application Support/Claude/mcp_servers.json
```

**Linux:**
```
~/.config/claude/mcp_servers.json
```

#### 2.2 設定ファイルの内容

##### ローカル環境用設定
```json
{
  "mcpServers": {
    "taxmcp-local": {
      "command": "python",
      "args": ["-m", "main"],
      "cwd": "/path/to/TaxMCP",
      "env": {
        "SERVER_HOST": "localhost",
        "SERVER_PORT": "8000"
      }
    }
  }
}
```

##### 本番環境用設定
```json
{
  "mcpServers": {
    "taxmcp-production": {
      "command": "python",
      "args": ["-c", "import requests; import json; import sys; from urllib.parse import urljoin; base_url='https://taxmcp.ami-j2.com'; print('TaxMCP Production Server Connected')"],
      "env": {
        "TAXMCP_BASE_URL": "https://taxmcp.ami-j2.com",
        "TAXMCP_TIMEOUT": "30",
        "TAXMCP_VERIFY_SSL": "true"
      }
    }
  }
}
```

##### 両環境対応設定（推奨）
```json
{
  "mcpServers": {
    "taxmcp-local": {
      "command": "python",
      "args": ["-m", "main"],
      "cwd": "/path/to/TaxMCP",
      "env": {
        "SERVER_HOST": "localhost",
        "SERVER_PORT": "8000"
      }
    },
    "taxmcp-production": {
      "command": "python",
      "args": ["-c", "import requests; import json; import sys; from urllib.parse import urljoin; base_url='https://taxmcp.ami-j2.com'; print('TaxMCP Production Server Connected')"],
      "env": {
        "TAXMCP_BASE_URL": "https://taxmcp.ami-j2.com",
        "TAXMCP_TIMEOUT": "30",
        "TAXMCP_VERIFY_SSL": "true"
      }
    }
  }
}
```

**注意**: `cwd`は実際のTaxMCPプロジェクトのパスに変更してください。

#### 2.3 事前設定済みファイルの使用（推奨）

手動設定の代わりに、事前に用意された設定ファイルを使用できます：

```bash
# 本番環境用設定をコピー
copy "C:\Void\TaxMCP\chatgpt_config\mcp_production_config.json" "%APPDATA%\Claude\mcp_servers.json"

# または両環境対応設定をコピー（推奨）
copy "C:\Void\TaxMCP\chatgpt_config\mcp_combined_config.json" "%APPDATA%\Claude\mcp_servers.json"
```

利用可能な設定ファイル：
- `chatgpt_config/mcp_local_config.json` - ローカル環境専用
- `chatgpt_config/mcp_production_config.json` - 本番環境専用
- `chatgpt_config/mcp_combined_config.json` - 両環境対応（推奨）

#### 2.4 本番環境接続テスト

本番環境（https://taxmcp.ami-j2.com）への接続をテスト：

```bash
cd C:\Void\TaxMCP\chatgpt_config
python test_production_connection.py
```

テストが成功すると以下のような出力が表示されます：
```
✓ ヘルスチェック成功
✓ 税務計算テスト成功
✓ MCP互換性確認成功
🎉 全てのテストが成功しました！
```

#### 2.5 ChatGPTクライアントの再起動
設定ファイルを保存後、ChatGPTクライアントを再起動してください。

## 使用方法

### 環境の選択

ChatGPTでTaxMCPを使用する際は、使用する環境を指定できます：

- **ローカル環境**: `taxmcp-local` サーバーを使用
- **本番環境**: `taxmcp-production` サーバー（https://taxmcp.ami-j2.com）を使用

### 基本的な使用例

ChatGPTとの会話で以下のような質問をすることで、TaxMCPサーバーの機能を利用できます：

#### 所得税計算
```
年収500万円、基礎控除48万円、扶養家族2人の場合の2024年度所得税を計算してください。
```

#### 法人税計算
```
課税所得1000万円の中小企業の法人税を東京都で計算してください。
```

#### 消費税率確認
```
2024年1月1日時点での食品の消費税率を教えてください。
```

#### 法令参照
```
法人税法第22条について検索してください。
```

#### 税務情報検索
```
消費税の軽減税率について詳しい情報を検索してください。
```

### 本番環境での使用例

本番環境（https://taxmcp.ami-j2.com）を使用する場合の具体例：

#### 環境指定での計算
```
taxmcp-productionサーバーを使用して、年収600万円、配偶者控除38万円、扶養控除38万円の場合の2024年度所得税を東京都で計算してください。
```

#### 最新税制での計算
```
本番環境で最新の税制データを使用して、法人税率の確認と課税所得800万円の法人税計算を行ってください。
```

#### 複数環境での比較
```
ローカル環境と本番環境の両方で同じ条件（年収500万円、基礎控除48万円）の所得税を計算して比較してください。
```

### 高度な使用例

#### 複数年シミュレーション
```
年収400万円、420万円、440万円の3年間の税額シミュレーションを東京都で実行してください。
```

#### インデックス統計確認
```
現在のデータベースのインデックス統計情報を表示してください。
```

## 利用可能な機能

### 税務計算機能
- **所得税計算** (`calculate_income_tax`)
- **法人税計算** (`calculate_corporate_tax`)
- **消費税率取得** (`get_consumption_tax_rate`)
- **住民税計算** (`calculate_resident_tax`)
- **複数年シミュレーション** (`simulate_multi_year_taxes`)

### 情報検索機能
- **法令参照検索** (`search_legal_reference`)
- **拡張税務情報検索** (`search_enhanced_tax_info`)
- **インデックス統計** (`get_index_statistics`)

### システム情報機能
- **都道府県情報取得** (`get_supported_prefectures`)
- **税年度情報取得** (`get_supported_tax_years`)

## トラブルシューティング

### よくある問題と解決方法

#### 1. サーバーに接続できない

##### ローカル環境の場合
**症状**: ChatGPTがローカルのTaxMCPサーバーに接続できない

**解決方法**:
- TaxMCPサーバーが起動していることを確認
- ポート8000が他のプロセスで使用されていないか確認
- ファイアウォール設定を確認

```bash
# ポート使用状況の確認
netstat -an | grep 8000
```

##### 本番環境の場合
**症状**: ChatGPTが本番環境（https://taxmcp.ami-j2.com）に接続できない

**解決方法**:
1. **接続テストの実行**:
   ```bash
   cd C:\Void\TaxMCP\chatgpt_config
   python test_production_connection.py
   ```

2. **ネットワーク設定の確認**:
   - インターネット接続の確認
   - プロキシ設定の確認
   - SSL証明書の検証設定

3. **サーバー状態の確認**:
   ```bash
   curl -I https://taxmcp.ami-j2.com/health
   ```

#### 2. 認証エラー
**症状**: 認証関連のエラーメッセージが表示される

**解決方法**:
- `.env`ファイルの`SECRET_KEY`が正しく設定されているか確認
- サーバーを再起動

#### 3. 計算結果が不正確
**症状**: 税額計算の結果が期待値と異なる

**解決方法**:
- 入力パラメータ（年収、控除額、税年度等）を確認
- 最新の税制データが適用されているか確認
- ログファイルでエラーメッセージを確認

```bash
# ログファイルの確認
tail -f logs/app.log
```

#### 4. 検索機能が動作しない
**症状**: 法令参照や税務情報検索が結果を返さない

**解決方法**:
- インターネット接続を確認
- キャッシュディレクトリの権限を確認
- インデックスの再構築を実行

#### 5. 本番環境でのタイムアウトエラー
**症状**: 本番環境での計算処理がタイムアウトする

**解決方法**:
1. **タイムアウト設定の調整**:
   - `mcp_production_config.json`の`TAXMCP_TIMEOUT`値を増加
   - 推奨値: 30-60秒

2. **ネットワーク状況の確認**:
   ```bash
   ping taxmcp.ami-j2.com
   ```

3. **処理の分割**:
   - 複雑な計算を小さな単位に分割
   - 複数年シミュレーションの年数を減らす

#### 6. SSL証明書エラー
**症状**: SSL証明書の検証でエラーが発生

**解決方法**:
1. **証明書の確認**:
   ```bash
   openssl s_client -connect taxmcp.ami-j2.com:443 -servername taxmcp.ami-j2.com
   ```

2. **設定の調整**:
   - `TAXMCP_VERIFY_SSL`を`false`に設定（テスト時のみ）
   - 本番環境では`true`を維持することを推奨

### ログの確認方法

#### アプリケーションログ
```bash
# リアルタイムでログを監視
tail -f logs/app.log

# エラーログのみを表示
grep "ERROR" logs/app.log
```

#### 監査ログ
```bash
# 監査ログの確認
tail -f logs/audit.log
```

## パフォーマンス最適化

### 推奨設定

#### 本番環境での設定
```env
DEBUG=false
LOG_LEVEL=warning
AUDIT_LOG_ENABLED=true
```

#### 開発環境での設定
```env
DEBUG=true
LOG_LEVEL=debug
AUDIT_LOG_ENABLED=true
```

### キャッシュの管理

#### キャッシュクリア
```bash
# キャッシュディレクトリのクリア
rm -rf cache/*
```

#### キャッシュサイズの確認
```bash
# キャッシュディレクトリのサイズ確認
du -sh cache/
```

## セキュリティ考慮事項

### 本番環境での注意点

1. **SECRET_KEYの管理**
   - 強力なランダム文字列を使用
   - 定期的な更新
   - 環境変数での管理

2. **ネットワークセキュリティ**
   - HTTPSの使用（本番環境）
   - ファイアウォール設定
   - アクセス制限

3. **ログ管理**
   - 機密情報のログ出力禁止
   - ログローテーション設定
   - 監査ログの保護

### 推奨セキュリティ設定

```env
# セキュリティ強化設定
SECRET_KEY=your-very-strong-secret-key-here
AUDIT_LOG_ENABLED=true
LOG_LEVEL=info
DEBUG=false
```

## 更新とメンテナンス

### 定期メンテナンス

#### 1. 依存関係の更新
```bash
# 依存関係の確認
pip list --outdated

# 更新の実行
pip install -r requirements.txt --upgrade
```

#### 2. ログファイルのローテーション
```bash
# 古いログファイルのアーカイブ
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# ログファイルのクリア
> logs/app.log
> logs/audit.log
```

#### 3. データベースの最適化
```bash
# SQLiteデータベースの最適化（必要に応じて）
sqlite3 cache/tax_documents.db "VACUUM;"
```

## サポートとリソース

### ドキュメント
- [README.md](./README.md) - 基本的な使用方法
- [アーキテクチャドキュメント](./architecture.md) - システム設計
- [RAG統合ガイド](./rag_integration_guide.md) - RAG機能の詳細
- [SECRET_KEYセットアップガイド](./SECRET_KEY_SETUP_GUIDE.md) - セキュリティ設定

### テストとデバッグ

#### テストクライアントの実行
```bash
python test_client.py
```

#### デバッグモードでの起動
```bash
# デバッグモードでサーバー起動
DEBUG=true python main.py
```

### 問い合わせ

技術的な問題や質問がある場合は、以下の方法でサポートを受けることができます：

1. **GitHubイシュー**: バグレポートや機能要求
2. **ドキュメント**: 関連ドキュメントの確認
3. **ログ分析**: エラーログの詳細な確認

## まとめ

このガイドに従って設定を行うことで、ChatGPTとTaxMCPサーバーを効果的に連携させ、高度な税務計算機能を利用できるようになります。

### 推奨設定

1. **両環境対応設定の使用**:
   ```bash
   copy "C:\Void\TaxMCP\chatgpt_config\mcp_combined_config.json" "%APPDATA%\Claude\mcp_servers.json"
   ```

2. **本番環境接続テストの実行**:
   ```bash
   cd C:\Void\TaxMCP\chatgpt_config
   python test_production_connection.py
   ```

3. **定期的な接続確認**:
   - 本番環境の可用性確認
   - 設定ファイルの更新確認
   - セキュリティ設定の見直し

### 環境別の使い分け

- **開発・テスト**: ローカル環境（`taxmcp-local`）
- **実際の税務計算**: 本番環境（`taxmcp-production`）
- **比較検証**: 両環境での並行実行

### セキュリティとメンテナンス

定期的なメンテナンスとセキュリティ対策を実施し、安全で効率的な運用を心がけてください：

- SSL証明書の有効性確認
- タイムアウト設定の最適化
- ログの定期的な確認
- 設定ファイルのバックアップ

### サポートリソース

- **設定ファイル**: `chatgpt_config/` ディレクトリ
- **接続テスト**: `test_production_connection.py`
- **詳細ガイド**: `chatgpt_config/README.md`
- **本番環境**: https://taxmcp.ami-j2.com