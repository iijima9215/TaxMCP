# TaxMCP 外部テストクライアント

TaxMCPサーバーの外部テスト環境用クライアントテストスイートです。

## 概要

このテストスイートは、本番環境またはステージング環境で動作するTaxMCPサーバーに対して、外部からHTTPS経由でテストを実行します。

## ファイル構成

```
external_test_client/
├── .env                        # 環境設定ファイル
├── requirements.txt            # Python依存関係
├── README.md                   # このファイル
├── external_test_client.py     # メイン機能テストクライアント
├── performance_test.py         # パフォーマンステストクライアント
├── auth_test.py               # 認証テストクライアント
└── integration_test_suite.py   # 統合テストスイート
```

## セットアップ

### 1. 依存関係のインストール

```bash
cd external_test_client
pip install -r requirements.txt
```

### 2. 環境設定

`.env`ファイルを編集して、テスト対象のサーバー情報を設定してください：

```env
# TaxMCPサーバー設定
BASE_URL=https://taxmcp.ami-j2.com
API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here

# テストユーザー認証情報
TEST_USERNAME=test_user
TEST_PASSWORD=test_password
```

**重要**: 本番環境のAPIキーやシークレットキーは絶対に公開しないでください。

## テスト実行方法

### 統合テストスイート（推奨）

全てのテストを一括実行：

```bash
python integration_test_suite.py
```

特定のテストのみ実行：

```bash
# 機能テストのみ
python integration_test_suite.py --functional-only

# パフォーマンステストのみ
python integration_test_suite.py --performance-only

# 認証テストのみ
python integration_test_suite.py --auth-only
```

特定のテストをスキップ：

```bash
# パフォーマンステストをスキップ
python integration_test_suite.py --skip-performance

# 認証テストをスキップ
python integration_test_suite.py --skip-auth
```

### 個別テスト実行

#### 機能テスト

```bash
python external_test_client.py
```

主要機能のテスト：
- ヘルスチェック
- 個人所得税計算
- 法人税計算
- タックスアンサー検索
- 法令検索
- エラーハンドリング

#### パフォーマンステスト

```bash
python performance_test.py
```

パフォーマンス指標の測定：
- 同時リクエスト処理能力
- レスポンス時間
- スループット
- エラー率
- SLA達成度

#### 認証テスト

```bash
python auth_test.py
```

セキュリティ関連のテスト：
- API Key認証
- JWT認証（有効/無効/期限切れ）
- 認証なしアクセス
- セキュリティヘッダー

## テスト結果

### 出力ファイル

テスト実行後、以下のファイルが生成されます：

- `integration_test_results_YYYYMMDD_HHMMSS.json` - 詳細テスト結果
- `integration_test_summary_YYYYMMDD_HHMMSS.json` - サマリーレポート
- `integration_test_suite_YYYYMMDD_HHMMSS.log` - 実行ログ
- `external_test_results_YYYYMMDD_HHMMSS.json` - 機能テスト結果
- `performance_test_results_YYYYMMDD_HHMMSS.json` - パフォーマンステスト結果
- `auth_test_results_YYYYMMDD_HHMMSS.json` - 認証テスト結果

### 結果の解釈

#### 統合テスト結果

```json
{
  "summary": {
    "overall_status": "success",  // success, warning, critical
    "test_suites": {
      "functional": {
        "status": "✓",  // ✓(成功), ⚠️(警告), ✗(失敗)
        "success_rate": 95.0
      },
      "performance": {
        "status": "✓",
        "meets_sla": true
      },
      "authentication": {
        "status": "✓",
        "security_issues": 0
      }
    },
    "critical_issues": [],
    "recommendations": []
  }
}
```

#### 終了コード

- `0`: 全テスト成功
- `1`: 重大な問題あり
- `2`: 警告レベルの問題あり
- `130`: ユーザーによる中断

## 設定オプション

### 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `BASE_URL` | TaxMCPサーバーのベースURL | `https://taxmcp.ami-j2.com` |
| `API_KEY` | API認証キー | - |
| `SECRET_KEY` | JWT署名用シークレットキー | - |
| `TEST_USERNAME` | テストユーザー名 | `test_user` |
| `TEST_PASSWORD` | テストパスワード | `test_password` |
| `REQUEST_TIMEOUT` | リクエストタイムアウト（秒） | `30` |
| `MAX_RETRIES` | 最大リトライ回数 | `3` |
| `CONCURRENT_USERS` | 同時ユーザー数 | `10` |
| `TEST_DURATION` | テスト実行時間（秒） | `60` |
| `VERBOSE_OUTPUT` | 詳細出力 | `true` |

### パフォーマンステスト設定

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `PERF_TARGET_RPS` | 目標RPS | `100` |
| `PERF_MAX_RESPONSE_TIME` | 最大応答時間（ms） | `2000` |
| `PERF_MIN_SUCCESS_RATE` | 最小成功率（%） | `95` |

## トラブルシューティング

### よくある問題

#### 1. 接続エラー

```
ConnectionError: HTTPSConnectionPool(host='taxmcp.ami-j2.com', port=443)
```

**解決方法**:
- ネットワーク接続を確認
- ファイアウォール設定を確認
- サーバーが稼働中か確認

#### 2. 認証エラー

```
401 Unauthorized: Invalid API key
```

**解決方法**:
- `.env`ファイルの`API_KEY`を確認
- APIキーの有効期限を確認
- サーバー側の認証設定を確認

#### 3. タイムアウトエラー

```
TimeoutError: Request timed out after 30 seconds
```

**解決方法**:
- `REQUEST_TIMEOUT`を増加
- サーバーの負荷状況を確認
- ネットワーク遅延を確認

#### 4. SSL証明書エラー

```
SSLError: certificate verify failed
```

**解決方法**:
- 証明書が有効か確認
- システムの証明書ストアを更新
- 必要に応じて`SSL_VERIFY=false`を設定（開発環境のみ）

### ログレベル設定

詳細なデバッグ情報が必要な場合：

```bash
export LOG_LEVEL=DEBUG
python integration_test_suite.py
```

### カスタムテスト設定

特定の環境向けにテスト設定をカスタマイズする場合、`.env`ファイルをコピーして環境別設定を作成：

```bash
cp .env .env.staging
cp .env .env.production
```

実行時に環境を指定：

```bash
# ステージング環境
cp .env.staging .env
python integration_test_suite.py

# 本番環境
cp .env.production .env
python integration_test_suite.py
```

## セキュリティ注意事項

1. **認証情報の管理**
   - `.env`ファイルをバージョン管理に含めない
   - 本番環境の認証情報は安全に管理
   - 定期的にAPIキーをローテーション

2. **ネットワークセキュリティ**
   - HTTPS通信のみ使用
   - 信頼できるネットワークからテスト実行
   - VPN経由でのアクセスを推奨

3. **テストデータ**
   - 実際の個人情報は使用しない
   - テスト用のダミーデータを使用
   - テスト後のデータクリーンアップ

## サポート

問題が発生した場合：

1. このREADMEのトラブルシューティングセクションを確認
2. ログファイルを確認
3. 開発チームに連絡（ログファイルを添付）

## ライセンス

このテストスイートは、TaxMCPプロジェクトの一部として提供されています。