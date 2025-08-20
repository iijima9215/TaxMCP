# 税務計算システム フロントエンド

日本の税務計算に特化したインテリジェントなチャットシステムのフロントエンドアプリケーションです。MCPサーバーと連携して、所得税、法人税、住民税の計算を自動化し、税務相談をサポートします。

## 🚀 主な機能

### 💬 インテリジェントチャット
- **自動税務判定**: 質問内容を自動分析し、適切な税務計算機能を呼び出し
- **OpenAI Function Calling**: GPT-4を活用した自然言語処理
- **Markdown表示**: 計算結果を読みやすい形式で表示
- **リアルタイム応答**: ストリーミング対応でスムーズな会話体験

### 🧮 税務計算機能
- **所得税計算**: 給与所得、事業所得、各種控除を考慮した詳細計算
- **法人税計算**: 基本税率、軽減税率、各種特別控除の適用
- **住民税計算**: 都道府県民税、市町村民税の自動計算
- **詳細法人税**: 複雑な企業税務に対応した高度な計算機能
- **法的参照検索**: 税法条文や通達の検索・参照機能

### 🎨 ユーザーインターフェース
- **レスポンシブデザイン**: デスクトップ・モバイル対応
- **ダークモード対応**: 目に優しい表示オプション
- **直感的操作**: シンプルで使いやすいチャットインターフェース
- **MCPサンプル機能**: 各税務計算のクイックアクセスボタン

## 🛠️ 技術スタック

### フレームワーク・ライブラリ
- **Next.js 15**: React フレームワーク（App Router使用）
- **React 19**: ユーザーインターフェース構築
- **TypeScript**: 型安全な開発環境
- **Tailwind CSS**: ユーティリティファーストCSS
- **@tailwindcss/typography**: Markdown表示の美しいスタイリング

### Markdown・数式表示
- **react-markdown**: Markdownレンダリング
- **remark-gfm**: GitHub Flavored Markdown対応
- **remark-math & rehype-katex**: LaTeX数式表示
- **katex**: 高品質な数式レンダリング

### API・通信
- **OpenAI API**: GPT-4による自然言語処理
- **MCP Protocol**: Model Context Protocol対応
- **RESTful API**: バックエンドとの通信

## 📦 セットアップ・起動方法

### 前提条件
- Node.js 18.0.0 以上
- npm または yarn
- バックエンドMCPサーバーが起動していること

### インストール

```bash
# 依存関係のインストール
npm install

# または
yarn install
```

### 開発サーバーの起動

```bash
# 開発サーバー起動
npm run dev

# または
yarn dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開いてアプリケーションにアクセスできます。

### 環境変数の設定

`.env.local` ファイルを作成し、以下の環境変数を設定してください：

```env
# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here

# MCPサーバー設定（デフォルト: http://localhost:8000）
MCP_SERVER_URL=http://localhost:8000
```

## 🏗️ プロジェクト構造

```
frontend/
├── src/
│   └── app/
│       ├── api/
│       │   ├── chat/          # チャットAPI（OpenAI連携）
│       │   └── mcp/           # MCP通信API
│       ├── chat/              # メインチャットページ
│       ├── globals.css        # グローバルスタイル
│       ├── layout.tsx         # アプリケーションレイアウト
│       └── page.tsx           # ホームページ
├── public/                    # 静的ファイル
├── tailwind.config.js         # Tailwind CSS設定
├── next.config.ts             # Next.js設定
└── package.json               # 依存関係・スクリプト
```

## 🔧 主要コンポーネント

### チャットページ (`/chat`)
- **メッセージ表示**: ユーザーとアシスタントの会話履歴
- **入力フォーム**: テキスト入力とファイルアップロード対応
- **MCPボタン**: 各税務計算機能への直接アクセス
- **ローディング表示**: 処理中のユーザーフィードバック

### API エンドポイント
- **`/api/chat`**: OpenAI GPT-4との通信、Function Calling実装
- **`/api/mcp`**: MCPサーバーとの通信、税務計算実行

## 🎯 使用方法

### 基本的な使い方
1. チャットページにアクセス
2. 税務に関する質問を自然言語で入力
3. システムが自動的に適切な計算機能を判定・実行
4. 結果がMarkdown形式で美しく表示

### MCPボタンの活用
- **所得税計算**: 給与や事業所得の税額計算
- **法人税計算**: 企業の法人税額計算
- **住民税計算**: 地方税の計算
- **詳細法人税**: 複雑な企業税務の詳細計算
- **法的参照**: 税法条文や通達の検索

### 入力例
```
年収500万円のサラリーマンの所得税を計算してください

資本金3000万円の会社の法人税率を教えてください

住民税の計算方法について説明してください
```

## 🔄 開発・デプロイ

### ビルド

```bash
# プロダクションビルド
npm run build

# ビルド結果の確認
npm run start
```

### リンティング・フォーマット

```bash
# ESLintチェック
npm run lint

# 型チェック
npm run type-check
```

### Vercelデプロイ

最も簡単なデプロイ方法は [Vercel Platform](https://vercel.com/new) を使用することです。

1. GitHubリポジトリをVercelに接続
2. 環境変数を設定
3. 自動デプロイの完了を待機

## 🤝 貢献・開発参加

### 開発ガイドライン
- TypeScriptの型安全性を重視
- Tailwind CSSでのスタイリング統一
- コンポーネントの再利用性を考慮
- アクセシビリティの確保

### バグ報告・機能要望
Issueを作成して報告・要望をお寄せください。

## 📚 関連リソース

### Next.js学習リソース
- [Next.js Documentation](https://nextjs.org/docs) - Next.jsの機能とAPI
- [Learn Next.js](https://nextjs.org/learn) - インタラクティブなチュートリアル
- [Next.js GitHub](https://github.com/vercel/next.js) - フィードバックと貢献

### 税務システム関連
- [MCPサーバー仕様](../README.md) - バックエンドシステムの詳細
- [税務計算ロジック](../tax_calculator.py) - 計算アルゴリズムの実装
- [API仕様書](../architecture.md) - システム全体のアーキテクチャ

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。
