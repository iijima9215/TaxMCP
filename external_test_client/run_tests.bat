@echo off
REM TaxMCP 外部テストクライアント実行スクリプト (Windows)
REM このスクリプトは外部テスト環境でTaxMCPサーバーをテストします

setlocal enabledelayedexpansion

echo ========================================
echo TaxMCP 外部テストクライアント
echo ========================================
echo.

REM 現在のディレクトリを確認
echo 現在のディレクトリ: %CD%
echo.

REM .envファイルの存在確認
if not exist ".env" (
    echo エラー: .envファイルが見つかりません
    echo .envファイルを作成して、必要な設定を行ってください
    echo.
    echo 必要な設定項目:
    echo - BASE_URL=https://taxmcp.ami-j2.com
    echo - API_KEY=your_api_key_here
    echo - SECRET_KEY=your_secret_key_here
    echo.
    pause
    exit /b 1
)

REM Pythonの確認
python --version >nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonが見つかりません
    echo Pythonをインストールしてください
    pause
    exit /b 1
)

echo Pythonバージョン:
python --version
echo.

REM 依存関係のインストール確認
echo 依存関係を確認中...
pip list | findstr "aiohttp" >nul 2>&1
if errorlevel 1 (
    echo 依存関係をインストール中...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo エラー: 依存関係のインストールに失敗しました
        pause
        exit /b 1
    )
) else (
    echo 依存関係は既にインストールされています
)
echo.

REM テストタイプの選択
echo テストタイプを選択してください:
echo 1. 統合テスト（全て）
echo 2. 機能テストのみ
echo 3. パフォーマンステストのみ
echo 4. 認証テストのみ
echo 5. カスタム選択
echo.
set /p choice="選択 (1-5): "

if "%choice%"=="1" (
    echo 統合テスト（全て）を実行します...
    python integration_test_suite.py
) else if "%choice%"=="2" (
    echo 機能テストのみを実行します...
    python integration_test_suite.py --functional-only
) else if "%choice%"=="3" (
    echo パフォーマンステストのみを実行します...
    python integration_test_suite.py --performance-only
) else if "%choice%"=="4" (
    echo 認証テストのみを実行します...
    python integration_test_suite.py --auth-only
) else if "%choice%"=="5" (
    echo.
    echo カスタム選択:
    echo 実行したいテストを選択してください（y/n）
    echo.
    
    set /p func_test="機能テスト (y/n): "
    set /p perf_test="パフォーマンステスト (y/n): "
    set /p auth_test="認証テスト (y/n): "
    
    set "test_args="
    
    if /i "!func_test!"=="n" (
        set "test_args=!test_args! --skip-functional"
    )
    
    if /i "!perf_test!"=="n" (
        set "test_args=!test_args! --skip-performance"
    )
    
    if /i "!auth_test!"=="n" (
        set "test_args=!test_args! --skip-auth"
    )
    
    echo.
    echo カスタムテストを実行します...
    python integration_test_suite.py !test_args!
) else (
    echo 無効な選択です
    pause
    exit /b 1
)

set test_exit_code=%errorlevel%

echo.
echo ========================================
echo テスト実行完了
echo ========================================

if %test_exit_code%==0 (
    echo ✓ 全てのテストが正常に完了しました
) else if %test_exit_code%==1 (
    echo ✗ 重大な問題が検出されました
) else if %test_exit_code%==2 (
    echo ⚠️ 警告レベルの問題が検出されました
) else if %test_exit_code%==130 (
    echo ⚠️ テストが中断されました
) else (
    echo ⚠️ 予期しないエラーが発生しました（終了コード: %test_exit_code%）
)

echo.
echo 結果ファイルを確認してください:
dir /b *test_results_*.json 2>nul
dir /b *test_summary_*.json 2>nul
dir /b *test_suite_*.log 2>nul

echo.
echo 詳細な結果を確認するには、生成されたJSONファイルとログファイルを参照してください。
echo.

pause
exit /b %test_exit_code%