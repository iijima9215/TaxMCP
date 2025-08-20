# Claude Desktop アプリでTaxMCPサーバーを利用するガイド

## 概要

このガイドでは、Windows環境でClaude Desktopアプリを使用してTaxMCPサーバーに接続し、税務計算機能を利用する手順を詳しく説明します。

### 利用可能な環境
- **ローカル環境**: localhost:8000（ローカルでサーバーを起動）
- **本番環境**: https://taxmcp.ami-j2.com（HTTPクライアント経由で接続）

## 前提条件

- Windows環境
- Claude Desktopアプリがインストール済み（`%USERPROFILE%\AppData\Local\Anthropic\Claude\claude.exe`）
- Googleアカウントでログイン済み
- TaxMCPプロジェクトがダウンロード済み（ローカル環境使用時のみ）

## 1. 必要なファイルの準備

### 1.1 設定ファイルの場所確認

Claude Desktopの設定ファイルは以下の場所にあります：
```
%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json
```

### 1.2 TaxMCPプロジェクトの設定ファイル確認

TaxMCPプロジェクトの`chatgpt_config`フォルダに以下のファイルがあることを確認してください：
- `mcp_local_config.json` - ローカル環境用設定
- `mcp_production_config.json` - 本番環境用設定
- `mcp_combined_config.json` - 両環境対応設定（推奨）

## 2. SECRET_KEYの設定（ローカル環境のみ）

**重要**: SECRET_KEYはローカル環境でのみ必要です。本番環境（https://taxmcp.ami-j2.com）への接続では不要です。

### 2.1 SECRET_KEYの確認（ローカル環境使用時）

ローカル環境を使用する場合は、TaxMCPプロジェクトのルートディレクトリにある`.env`ファイルを開き、SECRET_KEYを確認します：

```bash
# .envファイルの内容例
SECRET_KEY=your_secret_key_here_32_characters_long
SERVER_HOST=localhost
SERVER_PORT=8000
```

**重要**: SECRET_KEYは32文字以上の安全な文字列である必要があります。

### 2.2 SECRET_KEYの生成（必要な場合）

新しいSECRET_KEYが必要な場合は、以下のPythonコードで生成できます：

```python
import secrets
import string

# 32文字の安全なキーを生成
characters = string.ascii_letters + string.digits
secret_key = ''.join(secrets.choice(characters) for _ in range(32))
print(f"SECRET_KEY={secret_key}")
```

## 3. Claude Desktop設定ファイルの作成・編集

### 3.1 設定ファイルの場所を開く

1. Windowsキー + R を押して「ファイル名を指定して実行」を開く
2. `%USERPROFILE%\AppData\Roaming\Claude` と入力してEnterを押す
3. `claude_desktop_config.json`ファイルを探す（存在しない場合は新規作成）

### 3.2 既存設定がある場合の対応

**重要**: 既にClaude Desktopで他のMCPサーバー（filesystemなど）を使用している場合は、既存の設定を保持しながらTaxMCPサーバーを追加する必要があります。

#### 既存設定の例
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/iijima/OneDrive",
        "/Users/iijima/Downloads"
      ]
    }
  }
}
```

#### TaxMCPサーバーを追加する手順

1. 既存の`claude_desktop_config.json`をバックアップ
2. 既存の`mcpServers`セクション内にTaxMCPサーバーの設定を追加
3. SECRET_KEYを実際の値に置き換え

#### 統合設定例（filesystem + TaxMCP両環境）
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/iijima/OneDrive",
        "/Users/iijima/Downloads"
      ]
    },
    "taxmcp-local": {
      "command": "python",
      "args": ["-m", "main"],
      "cwd": "C:\\Void\\TaxMCP",
      "env": {
        "SECRET_KEY": "your_secret_key_here",
        "SERVER_HOST": "localhost",
        "SERVER_PORT": "8000",
        "DEBUG": "false",
        "LOG_LEVEL": "info",
        "AUDIT_LOG_ENABLED": "true"
      }
    },
    "taxmcp-production": {
      "command": "python",
      "args": [
        "-c",
        "import requests; import json; import sys; import os; from urllib.parse import urljoin; base_url = os.getenv('TAXMCP_BASE_URL', 'https://taxmcp.ami-j2.com'); timeout = int(os.getenv('TAXMCP_TIMEOUT', '30')); verify_ssl = os.getenv('TAXMCP_VERIFY_SSL', 'true').lower() == 'true'; print(f'TaxMCP Production Server Connected: {base_url}'); sys.stdout.flush()"
      ],
      "env": {
        "TAXMCP_BASE_URL": "https://taxmcp.ami-j2.com",
        "TAXMCP_TIMEOUT": "30",
        "TAXMCP_VERIFY_SSL": "true",
        "TAXMCP_API_VERSION": "v1",
        "TAXMCP_USER_AGENT": "ChatGPT-MCP-Client/1.0"
      }
    }
  }
}
```

**重要なポイント**:
- **ローカル環境（taxmcp-local）**: SECRET_KEYが必要、ローカルでサーバーを起動
- **本番環境（taxmcp-production）**: SECRET_KEYは不要、HTTPクライアント経由で接続

### 3.3 新規設定の場合

既存の設定がない場合は、以下のオプションから選択してください。

#### オプション1: ローカル環境のみ使用する場合

TaxMCPプロジェクトの`chatgpt_config\mcp_local_config.json`の内容を、Claude Desktopの`claude_desktop_config.json`にコピーします。

**手順**:
1. `C:\Void\TaxMCP\chatgpt_config\mcp_local_config.json`をテキストエディタで開く
2. 全ての内容をコピー
3. `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`に貼り付け
4. SECRET_KEYの値を実際の値に置き換える

#### オプション2: 本番環境のみ使用する場合

TaxMCPプロジェクトの`chatgpt_config\mcp_production_config.json`の内容を、Claude Desktopの`claude_desktop_config.json`にコピーします。

**手順**:
1. `C:\Void\TaxMCP\chatgpt_config\mcp_production_config.json`をテキストエディタで開く
2. 全ての内容をコピー
3. `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`に貼り付け

**注意**: 本番環境ではSECRET_KEYの設定は不要です。HTTPクライアント経由で直接接続します。

#### オプション3: 両環境を使用する場合（推奨）

TaxMCPプロジェクトの`chatgpt_config\mcp_combined_config.json`の内容を、Claude Desktopの`claude_desktop_config.json`にコピーします。

**手順**:
1. `C:\Void\TaxMCP\chatgpt_config\mcp_combined_config.json`をテキストエディタで開く
2. 全ての内容をコピー
3. `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`に貼り付け
4. ローカル環境用のSECRET_KEYの値を実際の値に置き換える（本番環境用は不要）

### 3.4 SECRET_KEYの設定（ローカル環境のみ）

**ローカル環境を使用する場合のみ**、設定ファイル内の`"SECRET_KEY": "your_secret_key_here"`の部分を、実際のSECRET_KEYに置き換えます：

```json
{
  "mcpServers": {
    "taxmcp-local": {
      "command": "python",
      "args": ["-m", "main"],
      "cwd": "C:\\Void\\TaxMCP",
      "env": {
        "SECRET_KEY": "abcd1234efgh5678ijkl9012mnop3456",
        "SERVER_HOST": "localhost",
        "SERVER_PORT": "8000",
        "DEBUG": "false",
        "LOG_LEVEL": "info",
        "AUDIT_LOG_ENABLED": "true"
      }
    }
  }
}
```

**重要**: 
- 本番環境（taxmcp-production）ではSECRET_KEYの設定は不要です
- 既存のfilesystemサーバーなどがある場合は、上記の統合設定例を参考にして、既存の設定を保持しながらTaxMCPサーバーの設定を追加してください

## 4. TaxMCPサーバーの起動（ローカル環境使用時のみ）

**ローカル環境を使用する場合のみ**、TaxMCPサーバーを事前に起動する必要があります。

**注意**: 本番環境（https://taxmcp.ami-j2.com）を使用する場合は、サーバーの起動は不要です。

### 4.1 PowerShellでサーバー起動

1. PowerShellを管理者として実行
2. TaxMCPプロジェクトディレクトリに移動：
   ```powershell
   cd C:\Void\TaxMCP
   ```
3. サーバーを起動：
   ```powershell
   python http_server.py
   ```
4. 「Server running on http://localhost:8000」と表示されることを確認

### 4.2 サーバー動作確認

ブラウザで `http://localhost:8000/health` にアクセスし、以下のレスポンスが返ることを確認：
```json
{"status": "healthy", "timestamp": "2024-01-XX..."}
```

## 5. Claude Desktopアプリの再起動

設定ファイルを変更した後は、Claude Desktopアプリを再起動する必要があります。

1. Claude Desktopアプリを完全に終了
2. タスクマネージャーでclaude.exeプロセスが終了していることを確認
3. Claude Desktopアプリを再起動
4. Googleアカウントで再ログイン（必要な場合）

## 6. 接続テストと動作確認

### 6.1 MCP接続の確認

Claude Desktopアプリで以下のメッセージを送信して、MCP接続を確認します：

```
TaxMCPサーバーに接続できていますか？利用可能な機能を教えてください。
```

### 6.2 税務計算のテスト

#### ローカル環境でのテスト（ローカル環境設定時）
```
taxmcp-localサーバーを使用して、年収500万円の個人の所得税を計算してください。
```

#### 本番環境でのテスト（本番環境設定時）
```
taxmcp-productionサーバー（https://taxmcp.ami-j2.com）を使用して、年収500万円の個人の所得税を計算してください。
```

#### 両環境での比較テスト（両環境設定時）
```
taxmcp-localとtaxmcp-productionの両方で、年収500万円の個人の所得税を計算して比較してください。
```

## 7. トラブルシューティング

### 7.1 接続エラーの場合

**症状**: "Connection refused" や "Server not responding" エラー

**解決策**:
1. **ローカル環境（taxmcp-local）の場合**：
   - TaxMCPサーバーが起動していることを確認
   - `http://localhost:8000/health` にアクセスして動作確認
2. **本番環境（taxmcp-production）の場合**：
   - インターネット接続を確認
   - `https://taxmcp.ami-j2.com` にアクセス可能か確認
3. 設定ファイルのJSON形式が正しいことを確認

### 7.2 認証エラーの場合（ローカル環境のみ）

**症状**: "Authentication failed" や "Invalid SECRET_KEY" エラー

**注意**: 本番環境（taxmcp-production）では認証エラーは発生しません。

**解決策（ローカル環境のみ）**:
1. `.env`ファイルのSECRET_KEYと設定ファイルのSECRET_KEYが一致することを確認
2. SECRET_KEYが32文字以上であることを確認
3. 特殊文字が正しくエスケープされていることを確認

### 7.3 設定ファイルエラーの場合

**症状**: Claude Desktopが起動しない、またはMCPサーバーが認識されない

**解決策**:
1. JSON形式が正しいことを確認（JSONバリデーターを使用）
2. ファイルパスが正しいことを確認（バックスラッシュのエスケープ）
3. 設定ファイルの文字エンコーディングがUTF-8であることを確認

### 7.4 本番環境接続テスト

本番環境への接続に問題がある場合は、以下のテストスクリプトを実行：

```powershell
cd C:\Void\TaxMCP\chatgpt_config
python test_production_connection.py
```

## 8. セキュリティ注意事項

1. **SECRET_KEYの管理（ローカル環境のみ）**:
   - SECRET_KEYは他人と共有しない
   - 定期的に変更する
   - バージョン管理システムにコミットしない
   - **注意**: 本番環境ではSECRET_KEYは不要です

2. **設定ファイルの保護**:
   - 設定ファイルのアクセス権限を適切に設定
   - 不要な場合は使用しない環境の設定を削除

3. **ネットワークセキュリティ**:
   - 本番環境使用時はHTTPS接続を確認
   - ファイアウォール設定を確認

## 9. 更新とメンテナンス

### 9.1 TaxMCPサーバーの更新

1. TaxMCPプロジェクトを最新版に更新
2. 依存関係を更新：`pip install -r requirements.txt`
3. 設定ファイルに新しいオプションが追加されていないか確認
4. Claude Desktopアプリを再起動

### 9.2 Claude Desktopアプリの更新

1. Claude Desktopアプリを最新版に更新
2. 設定ファイルの互換性を確認
3. 必要に応じて設定ファイルを調整

## 10. よくある質問

### Q1: 複数の環境を同時に使用できますか？
A1: はい、`mcp_combined_config.json`を使用することで、ローカル環境と本番環境の両方を同時に利用できます。

### Q2: SECRET_KEYを忘れた場合はどうすればよいですか？
A2: ローカル環境使用時のみ必要です。`.env`ファイルで確認するか、新しいSECRET_KEYを生成して設定し直してください。本番環境ではSECRET_KEYは不要です。

### Q3: 本番環境のサーバーが応答しない場合は？
A3: `test_production_connection.py`スクリプトを実行して接続状況を確認し、必要に応じてサーバー管理者に連絡してください。

### Q4: 設定ファイルが見つからない場合は？
A4: `%USERPROFILE%\AppData\Roaming\Claude`フォルダに`claude_desktop_config.json`ファイルを新規作成してください。

## 11. まとめ

### 環境別設定の違い

| 項目 | ローカル環境 | 本番環境 |
|------|-------------|----------|
| サーバー起動 | 必要（`python http_server.py`） | 不要 |
| SECRET_KEY | 必要（32文字以上） | 不要 |
| 接続方式 | ローカルプロセス起動 | HTTPクライアント |
| TaxMCPプロジェクト | 必要 | 不要 |
| 設定ファイル | `mcp_local_config.json` | `mcp_production_config.json` |

### 推奨設定

- **初心者**: 本番環境のみ（`mcp_production_config.json`）
- **開発者**: 両環境対応（`mcp_combined_config.json`）
- **オフライン使用**: ローカル環境のみ（`mcp_local_config.json`）

## 12. サポートとリソース

- **TaxMCPプロジェクト**: `C:\Void\TaxMCP\README.md`
- **ChatGPT連携ガイド**: `C:\Void\TaxMCP\CHATGPT_INTEGRATION_GUIDE.md`
- **設定ファイル詳細**: `C:\Void\TaxMCP\chatgpt_config\README.md`
- **本番環境**: https://taxmcp.ami-j2.com
- **セキュリティガイド**: `C:\Void\TaxMCP\SECRET_KEY_SETUP_GUIDE.md`

---

**注意**: このガイドは Windows 環境での Claude Desktop アプリ使用を前提としています。他の環境では手順が異なる場合があります。