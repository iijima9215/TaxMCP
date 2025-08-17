# SECRET_KEY セットアップ・運用ガイド

## 概要

`SECRET_KEY`は、TaxMCPアプリケーションのセキュリティの根幹を担う重要な暗号化キーです。このガイドでは、SECRET_KEYの目的、適切な設定方法、運用上の注意点について詳しく説明します。

## SECRET_KEYとは

### 定義
SECRET_KEYは、アプリケーションで使用される暗号化処理の基盤となる秘密鍵です。主にセッション管理、データの暗号化・復号化、デジタル署名の生成・検証に使用されます。

### 主な用途

1. **セッション管理**
   - ユーザーセッションの暗号化
   - セッションクッキーの署名
   - セッションデータの改ざん防止

2. **データ暗号化**
   - 機密データの暗号化・復号化
   - パスワードハッシュの生成
   - APIトークンの生成

3. **セキュリティ機能**
   - CSRF（Cross-Site Request Forgery）トークンの生成
   - フォームデータの署名
   - 認証トークンの検証

4. **税務データ保護**
   - 個人情報の暗号化
   - 税務計算結果の保護
   - 法令参照データのキャッシュ暗号化

## セットアップ手順

### 1. 開発環境での設定

#### 初期設定の確認
現在の`.env`ファイルを確認してください：

```bash
# .env ファイルの内容例
SECRET_KEY=your-secret-key-here-change-in-production
```

**⚠️ 重要**: デフォルト値は開発用のプレースホルダーです。本番環境では必ず変更してください。

#### 強力なSECRET_KEYの生成

**方法1: Pythonを使用**
```python
import secrets
import string

# 64文字の強力なキーを生成
characters = string.ascii_letters + string.digits + '!@#$%^&*'
secret_key = ''.join(secrets.choice(characters) for _ in range(64))
print(f"SECRET_KEY={secret_key}")
```

**方法2: OpenSSLを使用**
```bash
# Linux/macOS
openssl rand -base64 48

# Windows PowerShell
[System.Web.Security.Membership]::GeneratePassword(64, 10)
```

**方法3: オンラインツール**
- https://randomkeygen.com/ （信頼できるサイトのみ使用）
- ただし、本番環境では自分で生成することを強く推奨

### 2. 本番環境での設定

#### 環境変数による設定

**Linux/macOS:**
```bash
# .env ファイルに設定
echo "SECRET_KEY=your-generated-secret-key-here" >> .env

# または環境変数として直接設定
export SECRET_KEY="your-generated-secret-key-here"
```

**Windows:**
```powershell
# 環境変数として設定
$env:SECRET_KEY="your-generated-secret-key-here"

# または永続的に設定
[Environment]::SetEnvironmentVariable("SECRET_KEY", "your-generated-secret-key-here", "User")
```

#### Docker環境での設定

**方法1: docker-compose.ymlで直接設定**
```yaml
services:
  taxmcp:
    environment:
      - SECRET_KEY=your-generated-secret-key-here
```

**方法2: .envファイルを使用（推奨）**
```yaml
services:
  taxmcp:
    env_file:
      - .env
```

**方法3: Docker Secretsを使用（最も安全）**
```yaml
services:
  taxmcp:
    secrets:
      - secret_key
    environment:
      - SECRET_KEY_FILE=/run/secrets/secret_key

secrets:
  secret_key:
    file: ./secrets/secret_key.txt
```

### 3. クラウド環境での設定

#### AWS
```bash
# AWS Systems Manager Parameter Store
aws ssm put-parameter \
    --name "/taxmcp/secret-key" \
    --value "your-generated-secret-key-here" \
    --type "SecureString"

# AWS Secrets Manager
aws secretsmanager create-secret \
    --name "taxmcp/secret-key" \
    --secret-string "your-generated-secret-key-here"
```

#### Azure
```bash
# Azure Key Vault
az keyvault secret set \
    --vault-name "your-keyvault" \
    --name "taxmcp-secret-key" \
    --value "your-generated-secret-key-here"
```

#### Google Cloud
```bash
# Google Secret Manager
echo -n "your-generated-secret-key-here" | \
    gcloud secrets create taxmcp-secret-key --data-file=-
```

## セキュリティ要件

### 1. キーの強度要件

- **最小長**: 32文字以上
- **推奨長**: 64文字以上
- **文字種**: 英数字 + 特殊文字
- **エントロピー**: 高いランダム性

### 2. 禁止事項

❌ **絶対にやってはいけないこと**
- デフォルト値をそのまま使用
- 辞書に載っている単語を使用
- 個人情報（名前、誕生日等）を含む
- バージョン管理システム（Git）にコミット
- ログファイルに出力
- 平文でのメール送信
- 共有ドキュメントへの記載

### 3. 推奨事項

✅ **セキュリティベストプラクティス**
- 環境ごとに異なるキーを使用
- 定期的なキーローテーション（3-6ヶ月）
- アクセス権限の最小化
- 暗号化された保存
- 監査ログの記録

## 運用手順

### 1. キーローテーション

#### 手順
1. 新しいSECRET_KEYを生成
2. 段階的デプロイメント
   - ステージング環境でテスト
   - 本番環境への適用
3. 古いキーの無効化
4. 監査ログの確認

#### 自動化スクリプト例
```bash
#!/bin/bash
# key_rotation.sh

# 新しいキーを生成
NEW_KEY=$(openssl rand -base64 48)

# バックアップ作成
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 新しいキーを設定
sed -i "s/SECRET_KEY=.*/SECRET_KEY=${NEW_KEY}/" .env

# アプリケーション再起動
docker-compose restart

echo "キーローテーション完了: $(date)"
```

### 2. 監視とアラート

#### 監視項目
- キーの有効期限
- 不正アクセス試行
- 暗号化エラー
- セッション異常

#### アラート設定例
```python
# monitoring.py
import logging
from datetime import datetime, timedelta

def check_key_age():
    """キーの年齢をチェック"""
    key_created = datetime(2024, 1, 1)  # キー作成日
    age = datetime.now() - key_created
    
    if age > timedelta(days=180):  # 6ヶ月
        logging.warning("SECRET_KEY rotation required")
        # アラート送信処理
```

### 3. バックアップとリカバリ

#### バックアップ戦略
```bash
# 暗号化バックアップ
echo "$SECRET_KEY" | gpg --symmetric --cipher-algo AES256 > secret_key.backup.gpg

# 複数の安全な場所に保存
# - 暗号化されたクラウドストレージ
# - オフラインの物理メディア
# - 企業の金庫
```

#### リカバリ手順
1. バックアップからキーを復元
2. 環境変数に設定
3. アプリケーション再起動
4. 動作確認
5. ログ監視

## トラブルシューティング

### よくある問題と解決方法

#### 1. 「Invalid SECRET_KEY」エラー
**原因**: キーの形式が不正
**解決**: 正しい形式のキーを再生成

#### 2. セッションが無効になる
**原因**: キーが変更された
**解決**: ユーザーに再ログインを促す

#### 3. 暗号化データが復号できない
**原因**: キーが変更された
**解決**: 古いキーでデータを復号後、新しいキーで再暗号化

#### 4. Docker環境でキーが読み込まれない
**原因**: 環境変数の設定ミス
**解決**: docker-compose.ymlとDockerfileを確認

### デバッグ方法

```python
# debug_secret_key.py
import os
from config import get_secret_key

def debug_secret_key():
    """SECRET_KEYの設定状況をデバッグ"""
    print(f"環境変数 SECRET_KEY: {'設定済み' if os.getenv('SECRET_KEY') else '未設定'}")
    print(f"キーの長さ: {len(get_secret_key()) if get_secret_key() else 0}")
    print(f"デフォルト値使用: {'Yes' if get_secret_key() == 'your-secret-key-here-change-in-production' else 'No'}")

if __name__ == "__main__":
    debug_secret_key()
```

## コンプライアンスと法的要件

### 1. 個人情報保護法対応
- 適切な暗号化強度の確保
- アクセスログの記録
- データ漏洩時の対応手順

### 2. 業界標準への準拠
- NIST Cybersecurity Framework
- ISO 27001
- PCI DSS（決済情報を扱う場合）

### 3. 監査対応
- キー管理ポリシーの文書化
- アクセス権限の記録
- 定期的なセキュリティ評価

## まとめ

SECRET_KEYは、TaxMCPアプリケーションのセキュリティにおいて最も重要な要素の一つです。適切な生成、設定、運用を行うことで、ユーザーの税務データを安全に保護できます。

### チェックリスト

- [ ] 強力なSECRET_KEYを生成済み
- [ ] 本番環境でデフォルト値を変更済み
- [ ] 環境変数として適切に設定済み
- [ ] バージョン管理から除外済み
- [ ] バックアップを安全な場所に保存済み
- [ ] キーローテーション計画を策定済み
- [ ] 監視・アラート体制を構築済み
- [ ] チーム内でセキュリティポリシーを共有済み

### サポート

技術的な質問や問題が発生した場合は、以下のリソースを参照してください：

- [TaxMCP技術ドキュメント](./README.md)
- [セキュリティガイド](./security.py)
- [設定ファイル](./config.py)

---

**重要**: このガイドの内容は定期的に見直し、最新のセキュリティ要件に合わせて更新してください。