# システムメンテナンスガイド - TaxMCP サーバー

## 概要

TaxMCPサーバーは日本の税制に対応した計算システムです。税制改正や法令変更に対応するため、定期的なメンテナンスと更新が必要です。このガイドでは、システムの保守・運用方法について詳細に説明します。

## 税制更新メカニズム

### 現在実装されている更新機能

TaxMCPサーバーには以下の税制更新機能が実装されています：

#### 1. 自動税制情報取得機能
- **機能**: `get_latest_tax_info` ツール
- **データソース**: 財務省、国税庁、e-Gov法令検索
- **更新頻度**: 自動（キャッシュ期間に基づく）
- **対象**: 最新の税制改正情報、法令変更

#### 2. 税率更新情報取得機能
- **機能**: `get_tax_rate_updates` ツール
- **対象**: 所得税、法人税、消費税の税率変更
- **更新頻度**: 週1回（キャッシュ期間168時間）

#### 3. RAG統合による情報更新
- **機能**: 外部データソースからの自動情報取得
- **キャッシュ管理**: 自動キャッシュ更新とデータ整合性確保
- **検索機能**: 全文検索とメタデータ管理

## 税制改正対応手順

### 年次税制改正対応（12月〜3月）

#### ステップ1: 税制改正大綱の確認
```bash
# 最新の税制改正情報を取得
python -c "
import asyncio
from rag_integration import RAGIntegration

async def check_updates():
    rag = RAGIntegration()
    updates = await rag.get_tax_rate_updates(2025)
    print('税制改正情報:', updates)

asyncio.run(check_updates())
"
```

#### ステップ2: 税率データの更新

**所得税率の更新** (`tax_calculator.py`)
```python
# 所得税率テーブルの更新例
INCOME_TAX_BRACKETS = {
    TaxYear.Y2025: [
        (1950000, 0.05),    # 195万円以下: 5%
        (3300000, 0.10),    # 330万円以下: 10%
        (6950000, 0.20),    # 695万円以下: 20%
        (9000000, 0.23),    # 900万円以下: 23%
        (18000000, 0.33),   # 1800万円以下: 33%
        (40000000, 0.40),   # 4000万円以下: 40%
        (float('inf'), 0.45) # 4000万円超: 45%
    ]
}
```

**基礎控除額の更新**
```python
# 基礎控除額の更新例
BASIC_DEDUCTION = {
    TaxYear.Y2025: 480000,  # 2025年度: 48万円
    # 新年度の控除額を追加
}
```

#### ステップ3: 法人税率の更新

**法人税率テーブルの更新**
```python
# 法人税率の更新例
CORPORATE_TAX_RATES = {
    TaxYear.Y2025: {
        'small_company': 0.15,      # 中小法人: 15%
        'large_company': 0.23,      # 大法人: 23%
        'local_corporate_tax': 0.104, # 地方法人税: 10.4%
    }
}
```

#### ステップ4: 消費税率の更新

**消費税率履歴の更新**
```python
# 消費税率履歴の更新例
CONSUMPTION_TAX_HISTORY = [
    {
        'start_date': date(2019, 10, 1),
        'end_date': None,  # 現在も有効
        'standard_rate': 0.10,
        'reduced_rate': 0.08
    }
    # 新しい税率が導入される場合は追加
]
```

### 月次・随時更新対応

#### 1. 外部データソースの監視
```bash
# データソースの更新状況確認
curl -s "https://www.mof.go.jp/tax_policy/tax_reform/outline/index.html" | grep -i "更新"
curl -s "https://www.nta.go.jp/taxes/shiraberu/taxanswer/index.htm" | grep -i "更新"
```

#### 2. キャッシュの手動更新
```bash
# キャッシュクリアによる強制更新
rm -rf cache/*
python main.py  # サーバー再起動
```

#### 3. インデックスの再構築
```python
# SQLiteインデックスの再構築
from sqlite_indexer import SQLiteIndexer

indexer = SQLiteIndexer()
indexer.rebuild_index()  # インデックス再構築
```

## 定期メンテナンス作業

### 日次作業

#### 1. ログ監視
```bash
# エラーログの確認
grep "ERROR" logs/app.log | tail -20

# 監査ログの確認
tail -50 logs/audit.log
```

#### 2. システム稼働状況確認
```bash
# サーバー稼働確認
curl -f http://localhost:8000/health || echo "サーバーダウン"

# メモリ使用量確認
ps aux | grep "python main.py"
```

### 週次作業

#### 1. 外部データソース更新確認
```bash
# 税制情報の更新確認
python -c "
import asyncio
from rag_integration import RAGIntegration

async def weekly_check():
    rag = RAGIntegration()
    # 最新情報の取得テスト
    info = await rag.get_latest_tax_info('基礎控除', 'income_tax')
    print(f'取得件数: {len(info)}')
    
    # 税率更新情報の確認
    updates = await rag.get_tax_rate_updates()
    print(f'更新情報: {updates}')

asyncio.run(weekly_check())
"
```

#### 2. データベース最適化
```bash
# SQLiteデータベースの最適化
sqlite3 cache/tax_documents.db "VACUUM;"
sqlite3 cache/tax_documents.db "ANALYZE;"
```

#### 3. ログローテーション
```bash
# ログファイルのアーカイブ
tar -czf logs/archive/app_$(date +%Y%m%d).tar.gz logs/app.log
tar -czf logs/archive/audit_$(date +%Y%m%d).tar.gz logs/audit.log

# ログファイルのクリア
> logs/app.log
> logs/audit.log
```

### 月次作業

#### 1. 依存関係の更新確認
```bash
# 依存関係の脆弱性チェック
pip audit

# 更新可能なパッケージの確認
pip list --outdated
```

#### 2. パフォーマンス分析
```bash
# レスポンス時間の分析
grep "response_time" logs/app.log | awk '{print $NF}' | sort -n | tail -10

# エラー率の確認
grep "ERROR" logs/app.log | wc -l
wc -l logs/app.log
```

#### 3. バックアップ作成
```bash
# 設定ファイルのバックアップ
tar -czf backup/config_$(date +%Y%m%d).tar.gz .env config.py

# データベースのバックアップ
cp cache/tax_documents.db backup/tax_documents_$(date +%Y%m%d).db
```

## 緊急時対応手順

### 税制緊急変更対応

#### 1. 緊急税率変更
```bash
# 緊急時の税率変更手順
# 1. サーバー停止
pkill -f "python main.py"

# 2. 税率データの緊急更新
# tax_calculator.py を直接編集

# 3. テスト実行
python test_client.py

# 4. サーバー再起動
python main.py
```

#### 2. 外部データソース障害対応
```python
# キャッシュデータでの運用継続
# rag_integration.py の設定変更
CACHE_FALLBACK_ENABLED = True
CACHE_MAX_AGE_EMERGENCY = 720  # 30日間のキャッシュ利用
```

### システム障害対応

#### 1. サーバー復旧手順
```bash
# 1. プロセス確認
ps aux | grep python

# 2. ポート確認
netstat -tulpn | grep 8000

# 3. ログ確認
tail -100 logs/app.log

# 4. 強制再起動
pkill -f "python main.py"
sleep 5
python main.py
```

#### 2. データベース復旧
```bash
# SQLiteデータベースの整合性チェック
sqlite3 cache/tax_documents.db "PRAGMA integrity_check;"

# 破損時のバックアップからの復旧
cp backup/tax_documents_latest.db cache/tax_documents.db
```

## 税制データ管理

### データソース管理

#### 1. 公式データソース一覧

| データソース | URL | 更新頻度 | 重要度 |
|-------------|-----|---------|--------|
| 財務省税制改正資料 | https://www.mof.go.jp/tax_policy/tax_reform/outline/ | 年1回 | 高 |
| 国税庁タックスアンサー | https://www.nta.go.jp/taxes/shiraberu/taxanswer/ | 随時 | 高 |
| e-Gov法令検索 | https://elaws.e-gov.go.jp/ | 随時 | 中 |
| 各都道府県サイト | 各自治体URL | 年1回 | 中 |

#### 2. データ品質管理

**データ整合性チェック**
```python
# データ整合性確認スクリプト
def validate_tax_data():
    # 税率の論理チェック
    assert 0 <= income_tax_rate <= 1, "所得税率が範囲外"
    assert 0 <= consumption_tax_rate <= 1, "消費税率が範囲外"
    
    # 年度データの連続性チェック
    years = sorted(TAX_YEARS.keys())
    for i in range(1, len(years)):
        assert years[i] == years[i-1] + 1, "年度データに欠損"
```

**データ更新履歴管理**
```python
# 更新履歴の記録
DATA_UPDATE_HISTORY = {
    '2024-12-13': {
        'type': '税制改正大綱',
        'changes': ['基礎控除額変更', '法人税率調整'],
        'source': '財務省',
        'updated_by': 'system'
    }
}
```

### バージョン管理

#### 1. 税制データのバージョニング
```python
# 税制データバージョン管理
TAX_DATA_VERSION = {
    'major': 2025,      # 税年度
    'minor': 1,         # 年度内改正回数
    'patch': 0,         # 修正回数
    'build_date': '2024-12-13'
}
```

#### 2. 後方互換性の確保
```python
# 旧バージョンとの互換性維持
def get_tax_rate(year, rate_type):
    if year < 2020:
        return get_legacy_tax_rate(year, rate_type)
    return get_current_tax_rate(year, rate_type)
```

## 監視とアラート

### システム監視

#### 1. ヘルスチェック
```bash
# ヘルスチェックスクリプト
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -ne 200 ]; then
    echo "$(date): サーバーヘルスチェック失敗 (HTTP $RESPONSE)" >> logs/health.log
    # アラート送信処理
fi
```

#### 2. パフォーマンス監視
```python
# レスポンス時間監視
import time
import requests

def monitor_performance():
    start_time = time.time()
    response = requests.get('http://localhost:8000/health')
    response_time = time.time() - start_time
    
    if response_time > 5.0:  # 5秒以上の場合
        print(f"警告: レスポンス時間が遅延 ({response_time:.2f}秒)")
```

### データ更新監視

#### 1. 外部データソース監視
```python
# データソース更新監視
import hashlib
import requests

def monitor_data_source(url):
    response = requests.get(url)
    current_hash = hashlib.md5(response.content).hexdigest()
    
    # 前回のハッシュと比較
    if current_hash != stored_hash:
        print(f"データソース更新検出: {url}")
        # 更新処理をトリガー
```

#### 2. 税制変更アラート
```python
# 税制変更の自動検出
def detect_tax_changes():
    keywords = ['税制改正', '税率変更', '控除額変更']
    
    for keyword in keywords:
        results = search_latest_info(keyword)
        if results and is_recent_update(results):
            send_alert(f"税制変更検出: {keyword}")
```

## セキュリティメンテナンス

### 定期セキュリティ作業

#### 1. SECRET_KEY更新
```bash
# SECRET_KEYの定期更新（四半期ごと）
# 新しいキーの生成
python -c "import secrets; print(secrets.token_urlsafe(32))"

# .envファイルの更新
# サーバーの再起動
```

#### 2. 依存関係の脆弱性チェック
```bash
# セキュリティ脆弱性のチェック
pip audit
safety check

# 脆弱性が発見された場合の対応
pip install --upgrade [パッケージ名]
```

#### 3. ログ監査
```bash
# 不審なアクセスパターンの検出
grep -i "failed\|error\|unauthorized" logs/audit.log

# 異常なリクエスト頻度の確認
awk '{print $1}' logs/audit.log | sort | uniq -c | sort -nr | head -10
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. 税率計算の不整合
**症状**: 計算結果が期待値と異なる

**原因調査**:
```python
# デバッグ用の詳細ログ出力
DEBUG = True
LOG_LEVEL = "debug"

# 計算過程の確認
result = calculate_income_tax(income=5000000, year=2025, debug=True)
print(result['calculation_steps'])
```

**解決方法**:
1. 税率テーブルの確認
2. 控除額の確認
3. 計算ロジックの検証

#### 2. 外部データソース接続エラー
**症状**: RAG機能が動作しない

**原因調査**:
```bash
# ネットワーク接続確認
curl -I https://www.mof.go.jp/
curl -I https://www.nta.go.jp/

# DNS解決確認
nslookup www.mof.go.jp
```

**解決方法**:
1. ネットワーク設定の確認
2. プロキシ設定の確認
3. キャッシュデータでの運用継続

#### 3. データベース性能劣化
**症状**: 検索が遅い

**原因調査**:
```sql
-- SQLiteの実行計画確認
EXPLAIN QUERY PLAN SELECT * FROM documents WHERE content MATCH 'keyword';

-- インデックス使用状況確認
.schema documents
```

**解決方法**:
1. インデックスの再構築
2. データベースの最適化
3. 不要データの削除

## 災害復旧計画

### バックアップ戦略

#### 1. 定期バックアップ
```bash
# 日次バックアップスクリプト
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 設定ファイル
cp .env config.py $BACKUP_DIR/

# データベース
cp cache/*.db $BACKUP_DIR/

# ログファイル
cp logs/*.log $BACKUP_DIR/

# 圧縮
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
```

#### 2. 復旧手順
```bash
# 災害復旧手順
# 1. バックアップからの復元
tar -xzf backup/20241213.tar.gz
cp 20241213/* ./

# 2. 依存関係の再インストール
pip install -r requirements.txt

# 3. サーバー起動
python main.py

# 4. 動作確認
python test_client.py
```

### 事業継続計画

#### 1. 最小限サービス継続
```python
# 緊急時の最小限機能
EMERGENCY_MODE = True

if EMERGENCY_MODE:
    # 外部データソース無効化
    EXTERNAL_DATA_ENABLED = False
    # キャッシュデータのみで運用
    CACHE_ONLY_MODE = True
```

#### 2. 段階的復旧
1. **フェーズ1**: 基本計算機能の復旧
2. **フェーズ2**: 検索機能の復旧
3. **フェーズ3**: 外部データソース連携の復旧

## まとめ

TaxMCPサーバーの適切な運用には、定期的なメンテナンスと税制変更への迅速な対応が重要です。このガイドに従って運用することで、システムの安定性と税制情報の正確性を維持できます。

### 重要なポイント

1. **税制改正への対応**: 年次の税制改正大綱発表時には必ず対応作業を実施
2. **定期メンテナンス**: 日次・週次・月次の定期作業を確実に実行
3. **監視とアラート**: システムの異常を早期に検出する仕組みの維持
4. **セキュリティ**: 定期的なセキュリティ更新とログ監査
5. **災害復旧**: 定期バックアップと復旧手順の確認

税制は頻繁に変更されるため、常に最新の情報を維持し、システムの信頼性を確保することが重要です。