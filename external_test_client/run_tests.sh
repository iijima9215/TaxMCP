#!/bin/bash
# TaxMCP 外部テストクライアント実行スクリプト (Linux/macOS)
# このスクリプトは外部テスト環境でTaxMCPサーバーをテストします

set -e

echo "========================================"
echo "TaxMCP 外部テストクライアント"
echo "========================================"
echo

# 現在のディレクトリを確認
echo "現在のディレクトリ: $(pwd)"
echo

# .envファイルの存在確認
if [ ! -f ".env" ]; then
    echo "エラー: .envファイルが見つかりません"
    echo ".envファイルを作成して、必要な設定を行ってください"
    echo
    echo "必要な設定項目:"
    echo "- BASE_URL=https://taxmcp.ami-j2.com"
    echo "- API_KEY=your_api_key_here"
    echo "- SECRET_KEY=your_secret_key_here"
    echo
    exit 1
fi

# Pythonの確認
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "エラー: Pythonが見つかりません"
        echo "Pythonをインストールしてください"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Pythonバージョン:"
$PYTHON_CMD --version
echo

# pipの確認
if ! command -v pip3 &> /dev/null; then
    if ! command -v pip &> /dev/null; then
        echo "エラー: pipが見つかりません"
        echo "pipをインストールしてください"
        exit 1
    else
        PIP_CMD="pip"
    fi
else
    PIP_CMD="pip3"
fi

# 依存関係のインストール確認
echo "依存関係を確認中..."
if ! $PIP_CMD list | grep -q "aiohttp"; then
    echo "依存関係をインストール中..."
    $PIP_CMD install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "エラー: 依存関係のインストールに失敗しました"
        exit 1
    fi
else
    echo "依存関係は既にインストールされています"
fi
echo

# テストタイプの選択
echo "テストタイプを選択してください:"
echo "1. 統合テスト（全て）"
echo "2. 機能テストのみ"
echo "3. パフォーマンステストのみ"
echo "4. 認証テストのみ"
echo "5. カスタム選択"
echo
read -p "選択 (1-5): " choice

case $choice in
    1)
        echo "統合テスト（全て）を実行します..."
        $PYTHON_CMD integration_test_suite.py
        test_exit_code=$?
        ;;
    2)
        echo "機能テストのみを実行します..."
        $PYTHON_CMD integration_test_suite.py --functional-only
        test_exit_code=$?
        ;;
    3)
        echo "パフォーマンステストのみを実行します..."
        $PYTHON_CMD integration_test_suite.py --performance-only
        test_exit_code=$?
        ;;
    4)
        echo "認証テストのみを実行します..."
        $PYTHON_CMD integration_test_suite.py --auth-only
        test_exit_code=$?
        ;;
    5)
        echo
        echo "カスタム選択:"
        echo "実行したいテストを選択してください（y/n）"
        echo
        
        read -p "機能テスト (y/n): " func_test
        read -p "パフォーマンステスト (y/n): " perf_test
        read -p "認証テスト (y/n): " auth_test
        
        test_args=""
        
        if [[ "$func_test" =~ ^[Nn]$ ]]; then
            test_args="$test_args --skip-functional"
        fi
        
        if [[ "$perf_test" =~ ^[Nn]$ ]]; then
            test_args="$test_args --skip-performance"
        fi
        
        if [[ "$auth_test" =~ ^[Nn]$ ]]; then
            test_args="$test_args --skip-auth"
        fi
        
        echo
        echo "カスタムテストを実行します..."
        $PYTHON_CMD integration_test_suite.py $test_args
        test_exit_code=$?
        ;;
    *)
        echo "無効な選択です"
        exit 1
        ;;
esac

echo
echo "========================================"
echo "テスト実行完了"
echo "========================================"

case $test_exit_code in
    0)
        echo "✓ 全てのテストが正常に完了しました"
        ;;
    1)
        echo "✗ 重大な問題が検出されました"
        ;;
    2)
        echo "⚠️ 警告レベルの問題が検出されました"
        ;;
    130)
        echo "⚠️ テストが中断されました"
        ;;
    *)
        echo "⚠️ 予期しないエラーが発生しました（終了コード: $test_exit_code）"
        ;;
esac

echo
echo "結果ファイルを確認してください:"
ls -1 *test_results_*.json 2>/dev/null || true
ls -1 *test_summary_*.json 2>/dev/null || true
ls -1 *test_suite_*.log 2>/dev/null || true

echo
echo "詳細な結果を確認するには、生成されたJSONファイルとログファイルを参照してください。"
echo

exit $test_exit_code