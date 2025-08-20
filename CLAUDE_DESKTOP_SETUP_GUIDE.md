# Claude Desktop アプリでTaxMCPサーバーを利用するガイド

## 概要

このガイドでは、Windows環境でClaude Desktopアプリを使用してTaxMCPサーバー（ローカル環境・本番環境）に接続し、税務計算機能を利用する手順を詳しく説明します。

## 前提条件

- Windows環境
- Claude Desktopアプリがインストール済み（`%USERPROFILE%\AppData\Local\Anthropic\Claude\claude.exe`）
- Googleアカウントでログイン済み
- TaxMCPプロジェクトがダウンロード済み

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

## 2. SECRET_KEYの設定

### 2.1 SECRET_KEYの確認

TaxMCPプロジェクトのルートディレクトリにある`.env`ファイルを開き、SECRET_KEYを確認します：

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

### 3.2 設定内容のコピー

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
4. SECRET_KEYの値を実際の値に置き換える

#### オプション3: 両環境を使用する場合（推奨）

TaxMCPプロジェクトの`chatgpt_config\mcp_combined_config.json`の内容を、Claude Desktopの`claude_desktop_config.json`にコピーします。

**手順**:
1. `C:\Void\TaxMCP\chatgpt_config\mcp_combined_config.json`をテキストエディタで開く
2. 全ての内容をコピー
3. `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`に貼り付け
4. SECRET_KEYの値を実際の値に置き換える

### 3.3 SECRET_KEYの設定

設定ファイル内の`"SECRET_KEY": "your_secret_key_here"`の部分を、実際のSECRET_KEYに置き換えます：

```json
{
  "mcpServers": {
    "taxmcp-local": {
      "command": "python",
      "args": ["C:\\Void\\TaxMCP\\main.py"],
      "env": {
        "SECRET_KEY": "abcd1234efgh5678ijkl9012mnop3456",
        "SERVER_HOST": "localhost",
        "SERVER_PORT": "8000",
        "DEBUG_MODE": "false",
        "LOG_LEVEL": "info",
        "ENABLE_AUDIT_LOG": "true"
      }
    }
  }
}
```

## 4. TaxMCPサーバーの起動（ローカル環境使用時）

ローカル環境を使用する場合は、TaxMCPサーバーを事前に起動する必要があります。

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

#### ローカル環境でのテスト
```
ローカル環境で、年収500万円の個人の所得税を計算してください。
```

#### 本番環境でのテスト
```
本番環境（https://taxmcp.ami-j2.com）で、年収500万円の個人の所得税を計算してください。
```

#### 両環境での比較テスト
```
ローカル環境と本番環境の両方で、年収500万円の個人の所得税を計算して比較してください。
```

## 7. トラブルシューティング

### 7.1 接続エラーの場合

**症状**: "Connection refused" や "Server not responding" エラー

**解決策**:
1. ローカル環境の場合：TaxMCPサーバーが起動していることを確認
2. 本番環境の場合：インターネット接続を確認
3. SECRET_KEYが正しく設定されていることを確認
4. 設定ファイルのJSON形式が正しいことを確認

### 7.2 認証エラーの場合

**症状**: "Authentication failed" や "Invalid SECRET_KEY" エラー

**解決策**:
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

1. **SECRET_KEYの管理**:
   - SECRET_KEYは他人と共有しない
   - 定期的に変更する
   - バージョン管理システムにコミットしない

2. **設定ファイルの保護**:
   - 設定ファイルのアクセス権限を適切に設定
   - 不要な場合は本番環境への接続設定を削除

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
A2: `.env`ファイルで確認するか、新しいSECRET_KEYを生成して設定し直してください。

### Q3: 本番環境のサーバーが応答しない場合は？
A3: `test_production_connection.py`スクリプトを実行して接続状況を確認し、必要に応じてサーバー管理者に連絡してください。

### Q4: 設定ファイルが見つからない場合は？
A4: `%USERPROFILE%\AppData\Roaming\Claude`フォルダに`claude_desktop_config.json`ファイルを新規作成してください。

## 11. サポートとリソース

- **TaxMCPプロジェクト**: `C:\Void\TaxMCP\README.md`
- **ChatGPT連携ガイド**: `C:\Void\TaxMCP\CHATGPT_INTEGRATION_GUIDE.md`
- **設定ファイル詳細**: `C:\Void\TaxMCP\chatgpt_config\README.md`
- **セキュリティガイド**: `C:\Void\TaxMCP\SECRET_KEY_SETUP_GUIDE.md`

---

**注意**: このガイドは Windows 環境での Claude Desktop アプリ使用を前提としています。他の環境では手順が異なる場合があります。