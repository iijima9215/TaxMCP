# ChatGPT連携設定ファイル

このディレクトリには、TaxMCPサーバーとChatGPTを連携するための設定ファイルが含まれています。

## ファイル一覧

### 設定ファイル
- `mcp_local_config.json` - ローカル環境用MCP設定
- `mcp_production_config.json` - 本番環境用MCP設定
- `mcp_combined_config.json` - 両環境対応統合設定（推奨）

### テストツール
- `test_production_connection.py` - 本番環境接続テストスクリプト

## 設定手順

### 1. 本番環境接続テスト

まず、本番環境への接続をテストします：

```bash
cd C:\Void\TaxMCP\chatgpt_config
python test_production_connection.py
```

### 2. ChatGPTクライアント設定

#### Claude Desktop の場合

1. Claude Desktopの設定ディレクトリを開く：
   - **Windows**: `%APPDATA%\Claude\`
   - **macOS**: `~/Library/Application Support/Claude/`
   - **Linux**: `~/.config/claude/`

2. 適切な設定ファイルをコピー：

   **本番環境のみ使用する場合：**
   ```bash
   copy mcp_production_config.json "%APPDATA%\Claude\mcp_servers.json"
   ```

   **ローカル環境のみ使用する場合：**
   ```bash
   copy mcp_local_config.json "%APPDATA%\Claude\mcp_servers.json"
   ```

   **両環境を使用する場合（推奨）：**
   ```bash
   copy mcp_combined_config.json "%APPDATA%\Claude\mcp_servers.json"
   ```

3. Claude Desktopを再起動

#### その他のChatGPTクライアントの場合

各クライアントのドキュメントに従って、適切な設定ディレクトリに設定ファイルをコピーしてください。

### 3. 設定の確認

ChatGPTクライアントで以下のような質問をして、連携が正常に動作することを確認：

```
年収500万円、基礎控除48万円の場合の2024年度所得税を計算してください。
```

## 環境別の使い分け

### ローカル環境 (taxmcp-local)
- 開発・テスト用
- ローカルでTaxMCPサーバーを起動している場合
- レスポンスが高速
- デバッグ情報が豊富

### 本番環境 (taxmcp-production)
- 実際の税務計算用
- https://taxmcp.ami-j2.com サーバーを使用
- 安定した動作
- 最新の税制データ

## トラブルシューティング

### 接続エラーが発生する場合

1. **本番環境接続テストを実行**：
   ```bash
   python test_production_connection.py
   ```

2. **ネットワーク設定を確認**：
   - ファイアウォール設定
   - プロキシ設定
   - SSL証明書の検証

3. **設定ファイルのパスを確認**：
   - `mcp_local_config.json`の`cwd`パスが正しいか
   - 絶対パスで指定されているか

### 計算結果が期待と異なる場合

1. **入力パラメータを確認**：
   - 年収、控除額、税年度
   - 都道府県名の表記

2. **サーバーログを確認**：
   ```bash
   # ローカル環境の場合
   tail -f logs/app.log
   ```

3. **最新の税制データが適用されているか確認**

## セキュリティ注意事項

### 本番環境使用時
- SSL証明書の検証を無効にしない
- タイムアウト値を適切に設定
- 機密情報をログに出力しない

### ローカル環境使用時
- SECRET_KEYを適切に設定
- デバッグモードを本番では無効にする
- 監査ログを有効にする

## 更新手順

### 設定ファイルの更新
1. 新しい設定ファイルをダウンロード
2. 既存の設定をバックアップ
3. 新しい設定ファイルをコピー
4. ChatGPTクライアントを再起動

### 接続テストの実行
```bash
python test_production_connection.py
```

## サポート

問題が発生した場合は、以下の情報を含めてサポートに連絡してください：

1. 使用している環境（ローカル/本番）
2. エラーメッセージの詳細
3. 接続テストの結果
4. ChatGPTクライアントの種類とバージョン
5. 実行しようとした操作の詳細

## 関連ドキュメント

- [CHATGPT_INTEGRATION_GUIDE.md](../CHATGPT_INTEGRATION_GUIDE.md) - 詳細な連携ガイド
- [README.md](../README.md) - TaxMCPサーバーの基本情報
- [architecture.md](../architecture.md) - システムアーキテクチャ