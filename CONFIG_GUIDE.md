# TaxMCP 設定ガイド

## 概要

TaxMCPでは、税率設定と計算設定を環境変数として外部化し、プログラムコードを変更することなく設定を調整できます。

## 設定方法

### 1. 環境変数による設定

以下の環境変数を設定することで、税率や計算設定をカスタマイズできます：

#### 法人税率設定

```bash
# 大法人税率（デフォルト: 0.232 = 23.2%）
CORPORATE_TAX_RATE_LARGE=0.232

# 中小法人税率（800万円以下、デフォルト: 0.15 = 15%）
CORPORATE_TAX_RATE_SMALL=0.15

# 中小法人税率（800万円超、デフォルト: 0.232 = 23.2%）
CORPORATE_TAX_RATE_SMALL_HIGH=0.232
```

#### 地方法人税率設定

```bash
# 地方法人税率（デフォルト: 0.103 = 10.3%）
LOCAL_CORPORATE_TAX_RATE=0.103
```

#### 事業税率設定

```bash
# 事業税所得割（低）（デフォルト: 0.035 = 3.5%）
BUSINESS_TAX_RATE_INCOME_LOW=0.035

# 事業税所得割（中）（デフォルト: 0.053 = 5.3%）
BUSINESS_TAX_RATE_INCOME_MID=0.053

# 事業税所得割（高）（デフォルト: 0.07 = 7.0%）
BUSINESS_TAX_RATE_INCOME_HIGH=0.07

# 事業税所得割（低）超過税率（デフォルト: 0.0375 = 3.75%）
BUSINESS_TAX_RATE_INCOME_LOW_EXCESS=0.0375

# 事業税所得割（中）超過税率（デフォルト: 0.0565 = 5.65%）
BUSINESS_TAX_RATE_INCOME_MID_EXCESS=0.0565

# 事業税所得割（高）超過税率（デフォルト: 0.0748 = 7.48%）
BUSINESS_TAX_RATE_INCOME_HIGH_EXCESS=0.0748

# 事業税付加価値割（デフォルト: 0.0037 = 0.37%）
BUSINESS_TAX_RATE_VALUE_ADDED=0.0037

# 事業税資本割（デフォルト: 0.00086 = 0.086%）
BUSINESS_TAX_RATE_CAPITAL=0.00086
```

#### 住民税率設定

```bash
# 住民税法人税割（デフォルト: 0.07 = 7%）
RESIDENT_TAX_INCOME_RATE=0.07

# 住民税均等割（資本金5000万円以下、デフォルト: 70000円）
RESIDENT_TAX_EQUAL_50M_BELOW=70000

# 住民税均等割（資本金5000万円超～10億円以下、デフォルト: 180000円）
RESIDENT_TAX_EQUAL_50M_1B=180000

# 住民税均等割（資本金10億円超、デフォルト: 290000円）
RESIDENT_TAX_EQUAL_1B_ABOVE=290000
```

#### 計算設定

```bash
# 丸め処理有効化（デフォルト: true）
CALCULATION_ROUNDING_ENABLED=true

# 丸め精度（小数点以下桁数、デフォルト: 0）
CALCULATION_ROUNDING_PRECISION=0

# 丸め方法（デフォルト: ROUND_HALF_UP）
CALCULATION_ROUNDING_METHOD=ROUND_HALF_UP
```

### 2. .envファイルによる設定

プロジェクトルートに`.env`ファイルを作成して設定することも可能です：

```bash
# .env ファイルの例
CORPORATE_TAX_RATE_LARGE=0.232
CORPORATE_TAX_RATE_SMALL=0.15
LOCAL_CORPORATE_TAX_RATE=0.103
CALCULATION_ROUNDING_ENABLED=true
CALCULATION_ROUNDING_PRECISION=0
```

## MCPツールによる設定確認・変更

### 設定確認

`get_system_config`ツールを使用して、現在の設定値を確認できます：

```python
# 現在の設定値を取得
config = get_system_config()
print(config)
```

### 設定変更

`update_system_config`ツールを使用して、実行時に設定値を変更できます：

```python
# 法人税率を変更
result = update_system_config(
    corporate_tax_rate_large=0.25,  # 25%に変更
    calculation_rounding_enabled=False  # 丸め処理を無効化
)
print(result)
```

**注意**: `update_system_config`による変更は現在のセッションでのみ有効です。永続化するには環境変数または`.env`ファイルを更新してください。

## 丸め処理について

### 丸め処理の種類

- `ROUND_HALF_UP`: 四捨五入（国税庁標準）
- `ROUND_DOWN`: 切り捨て
- `ROUND_UP`: 切り上げ
- `ROUND_HALF_EVEN`: 銀行家の丸め

### 丸め処理の無効化

正規の税率を扱いたい場合は、以下の方法で丸め処理を無効化できます：

1. **環境変数で無効化**:
   ```bash
   CALCULATION_ROUNDING_ENABLED=false
   ```

2. **MCPツールで無効化**:
   ```python
   update_system_config(calculation_rounding_enabled=False)
   ```

3. **計算時に無効化**:
   ```python
   result = calculate_corporate_tax_with_custom_rates(
       accounting_profit=10000000,
       disable_rounding=True
   )
   ```

## 設定値の優先順位

1. MCPツール（`update_system_config`）による変更
2. 環境変数
3. `.env`ファイル
4. デフォルト値（`config.py`内）

## トラブルシューティング

### 設定が反映されない場合

1. 環境変数名が正しいか確認
2. 値の形式が正しいか確認（税率は0.0-1.0の範囲）
3. サーバーを再起動
4. `get_system_config`で現在の設定値を確認

### 計算結果が期待と異なる場合

1. 丸め処理設定を確認
2. `disable_rounding=True`で正確な値を確認
3. 税率設定が正しいか確認

## 例：カスタム税率での計算

```python
# 環境変数で基本税率を設定
# CORPORATE_TAX_RATE_LARGE=0.25
# CALCULATION_ROUNDING_ENABLED=false

# 特定の計算でカスタム税率を使用
result = calculate_corporate_tax_with_custom_rates(
    accounting_profit=50000000,  # 5000万円
    corporate_tax_rate=0.20,     # 20%（カスタム）
    disable_rounding=True        # 丸め処理無効
)

print(f"法人税額: {result['法人税額']}")
print(f"実効税率: {result['実効税率']}%")
```

この設定により、プログラムコードを変更することなく、税率や計算設定を柔軟に調整できます。