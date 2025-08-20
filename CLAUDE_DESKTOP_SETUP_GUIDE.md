# Claude Desktop MCP接続セットアップガイド

## 概要

Claude DesktopはMCP（Model Context Protocol）をネイティブサポートしており、本税務計算MCPサーバと直接連携できます。このガイドでは、Claude Desktopから本MCPサーバに接続する方法を説明します。

## 前提条件

- Claude Desktop（最新版）
- Python 3.8以上
- 本MCPサーバが稼働中

## セットアップ手順

### 1. MCPサーバの起動

```bash
# プロジェクトディレクトリに移動
cd C:\Void\TaxMCP

# 仮想環境の有効化
.\venv\Scripts\activate

# MCPサーバの起動
python http_server.py
```

サーバが `http://localhost:8000` で起動することを確認してください。

### 2. Claude Desktop設定ファイルの作成

Claude Desktopの設定ディレクトリに移動し、MCP設定ファイルを作成します。

#### Windows
```
%APPDATA%\Claude\claude_desktop_config.json
```

#### macOS
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### 3. 設定ファイルの内容

以下の内容で `claude_desktop_config.json` を作成または更新してください：

```json
{
  "mcpServers": {
    "tax-calculator": {
      "command": "python",
      "args": [
        "C:\\Void\\TaxMCP\\http_server.py",
        "--mcp-mode"
      ],
      "env": {
        "PYTHONPATH": "C:\\Void\\TaxMCP"
      }
    }
  }
}
```

### 4. HTTP接続設定（代替方法）

HTTPエンドポイント経由で接続する場合：

```json
{
  "mcpServers": {
    "tax-calculator-http": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-http",
        "http://localhost:8000/mcp"
      ]
    }
  }
}
```

### 5. Claude Desktopの再起動

設定ファイルを保存後、Claude Desktopを完全に終了し、再起動してください。

## 接続確認

### 1. MCPサーバの動作確認

Claude Desktopで以下のメッセージを送信して接続を確認：

```
利用可能なツールを教えてください
```

### 2. 税務計算テスト

```
年収500万円の所得税を計算してください
```

## 利用可能な機能

### 税務計算ツール

1. **所得税計算** (`calculate_income_tax`)
   - 年収から所得税額を計算
   - 各種控除を考慮

2. **住民税計算** (`calculate_resident_tax`)
   - 課税所得から住民税額を計算
   - 都道府県別税率対応

3. **法人税計算** (`calculate_corporate_tax`)
   - 法人所得から法人税額を計算
   - 資本金規模別税率適用

4. **法的参照検索** (`search_legal_reference`)
   - 税法関連の条文検索
   - 判例・通達の参照

## 使用例

### 基本的な税務計算

```
ユーザー: 年収600万円の会社員の所得税を計算してください

Claude: 年収600万円の所得税を計算いたします。
[calculate_income_tax ツールを使用]

計算結果：
- 年収: 6,000,000円
- 給与所得控除: 1,640,000円
- 所得控除: 480,000円（基礎控除等）
- 課税所得: 3,880,000円
- 所得税額: 272,500円
```

### 複合的な税務相談

```
ユーザー: 個人事業主として年収800万円、法人化を検討中です。法人税との比較をお願いします。

Claude: 個人事業主と法人化の税負担を比較いたします。
[複数のツールを使用して詳細分析]
```

## トラブルシューティング

### 接続エラー

**症状**: Claude DesktopでMCPサーバに接続できない

**解決策**:
1. MCPサーバが起動していることを確認
2. ポート8000が使用可能であることを確認
3. 設定ファイルのパスが正しいことを確認
4. Claude Desktopを再起動

### ツールが表示されない

**症状**: 利用可能なツールが表示されない

**解決策**:
1. 設定ファイルの JSON 構文を確認
2. ファイルパスの区切り文字を確認（Windows: `\\`）
3. 環境変数の設定を確認

### 計算結果が不正確

**症状**: 税額計算の結果が期待と異なる

**解決策**:
1. 入力パラメータを確認
2. 適用される控除額を確認
3. 最新の税率が適用されているか確認

## セキュリティ考慮事項

- ローカル環境での使用を推奨
- 機密情報の取り扱いに注意
- 定期的なソフトウェア更新

## パフォーマンス最適化

- 仮想環境の使用
- 不要なプロセスの停止
- メモリ使用量の監視

## 更新とメンテナンス

### MCPサーバの更新

```bash
# 最新版の取得
git pull origin main

# 依存関係の更新
pip install -r requirements.txt

# サーバの再起動
python http_server.py
```

### Claude Desktopの更新

Claude Desktopは自動更新されますが、手動確認も可能です：

- メニュー → ヘルプ → アップデートの確認

## サポート

技術的な問題や質問については：

- プロジェクトのIssueトラッカー
- Claude Desktop公式ドキュメント
- MCP仕様書

## まとめ

Claude DesktopのMCPサポートにより、本税務計算サーバと直接連携できます。適切な設定により、Claude Desktopから税務計算機能をシームレスに利用できるようになります。