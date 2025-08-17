# ChatGPT連携ガイド - TaxMCP サーバー

このガイドでは、TaxMCPサーバーをChatGPTと連携して使用する方法を詳細に説明します。

## 概要

TaxMCPサーバーは、Model Context Protocol (MCP) を使用してChatGPTと連携し、高度な税務計算機能を提供します。ChatGPTがMCPクライアントとして動作し、TaxMCPサーバーの各種税務ツールにアクセスできます。

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
```json
{
  "mcpServers": {
    "taxmcp": {
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

**注意**: `cwd`は実際のTaxMCPプロジェクトのパスに変更してください。

#### 2.3 ChatGPTクライアントの再起動
設定ファイルを保存後、ChatGPTクライアントを再起動してください。

## 使用方法

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
**症状**: ChatGPTがTaxMCPサーバーに接続できない

**解決方法**:
- TaxMCPサーバーが起動していることを確認
- ポート8000が他のプロセスで使用されていないか確認
- ファイアウォール設定を確認

```bash
# ポート使用状況の確認
netstat -an | grep 8000
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

このガイドに従って設定を行うことで、ChatGPTとTaxMCPサーバーを効果的に連携させ、高度な税務計算機能を利用できるようになります。定期的なメンテナンスとセキュリティ対策を実施し、安全で効率的な運用を心がけてください。