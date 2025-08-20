# ChatGPT統合ガイド

## 重要な注意事項

**現在のChatGPT UIでは、ユーザー自身が外部MCPサーバを直接追加する機能は提供されていません。**

OpenAIが公式に用意したMCPサーバ（例：Google Drive、Gmailなどのコネクタ）が統合されているのと同じ仕組みで動作します。したがって、自分のドメインの`/mcp`をChatGPT Plusアカウントからそのまま使うことはできません。

## 代替策

独自MCPサーバを自作アプリ（Next.js / Node.js / Python など）のバックエンドに組み込み、そのアプリ経由でChatGPT API（Assistants API）から利用する形になります。

### アーキテクチャ概要

```
ChatGPT UI → 独自Webアプリ → MCPサーバ（このプロジェクト）
```

## 実装方法

### 1. 独自Webアプリの作成

独自のWebアプリケーション（未構築）を作成し、以下の機能を実装する必要があります：

- ChatGPT APIとの連携
- 本MCPサーバへのプロキシ機能
- ユーザー認証・認可
- セッション管理

### 2. MCPサーバとの連携

独自Webアプリから本MCPサーバの以下のエンドポイントを利用：

- `POST /mcp` - MCP JSON-RPC 2.0リクエスト
- `GET /mcp/info` - サーバー情報取得

### 3. ChatGPT Assistants APIの利用

独自Webアプリ内でChatGPT Assistants APIを使用し、税務計算機能を提供します。

## 利用可能な機能

本MCPサーバは以下の機能を提供します：

### 税務計算
- **所得税計算** (`calculate_income_tax`)
- **住民税計算** (`calculate_resident_tax`)
- **法人税計算** (`calculate_corporate_tax`)

### 情報検索
- **法的参照検索** (`search_legal_reference`)

## 技術仕様

### MCPプロトコル
- JSON-RPC 2.0準拠
- HTTP/HTTPS対応
- 認証機能付き

### サポート環境
- Python 3.8+
- FastAPI
- Uvicorn

## セキュリティ考慮事項

- API認証の実装
- HTTPS通信の強制
- 入力値検証
- レート制限
- ログ監視

## 開発ロードマップ

1. **Phase 1**: 独自Webアプリの基盤構築
2. **Phase 2**: ChatGPT API統合
3. **Phase 3**: MCPサーバ連携
4. **Phase 4**: UI/UX改善
5. **Phase 5**: 本番環境デプロイ

## サポート

技術的な質問や問題については、プロジェクトのIssueトラッカーをご利用ください。

## まとめ

ChatGPT UIから直接MCPサーバを利用することはできませんが、独自Webアプリを介することで同等の機能を提供できます。本MCPサーバは、そのバックエンドコンポーネントとして機能します。