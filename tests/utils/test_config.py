"""テスト設定とベースクラス

TaxMCPサーバーのテスト実行に必要な設定とベースクラス
"""

import os
import sys
import asyncio
import unittest
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestConfig:
    """テスト設定クラス"""
    
    # テスト環境設定
    TEST_ENV = {
        "SECRET_KEY": "test_secret_key_for_testing_only",
        "DATABASE_URL": ":memory:",  # インメモリSQLite
        "LOG_LEVEL": "DEBUG",
        "ENABLE_AUDIT_LOG": "true",
        "RATE_LIMIT_ENABLED": "false",  # テスト時はレート制限無効
        "CACHE_TTL": "60",
        "MAX_CONCURRENT_REQUESTS": "10"
    }
    
    # テストデータディレクトリ
    TEST_DATA_DIR = Path(__file__).parent / "test_data"
    
    # パフォーマンステスト設定
    PERFORMANCE_LIMITS = {
        "max_response_time": 2.0,  # 秒
        "max_memory_usage": 100 * 1024 * 1024,  # 100MB
        "min_throughput": 10.0,  # RPS
        "max_concurrent_requests": 50
    }
    
    # セキュリティテスト設定
    SECURITY_TEST_PATTERNS = {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM information_schema.tables; --",
            "' UNION SELECT password FROM users --"
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`"
        ]
    }
    
    @classmethod
    def setup_test_environment(cls):
        """テスト環境をセットアップ"""
        # 環境変数設定
        for key, value in cls.TEST_ENV.items():
            os.environ[key] = value
        
        # ログ設定
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('test.log')
            ]
        )
        
        # テストデータディレクトリ作成
        cls.TEST_DATA_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def cleanup_test_environment(cls):
        """テスト環境をクリーンアップ"""
        # 環境変数削除
        for key in cls.TEST_ENV.keys():
            if key in os.environ:
                del os.environ[key]
        
        # テストログファイル削除
        if os.path.exists('test.log'):
            os.remove('test.log')


class AsyncTestCase(unittest.TestCase):
    """非同期テスト用ベースクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        TestConfig.setup_test_environment()
    
    def tearDown(self):
        """テストクリーンアップ"""
        self.loop.close()
        TestConfig.cleanup_test_environment()
    
    def run_async(self, coro):
        """非同期関数を実行
        
        Args:
            coro: コルーチン
            
        Returns:
            実行結果
        """
        return self.loop.run_until_complete(coro)


class TaxMCPTestCase(AsyncTestCase):
    """TaxMCPサーバー用テストベースクラス"""
    
    def setUp(self):
        """TaxMCPテストセットアップ"""
        super().setUp()
        
        # モックオブジェクト初期化
        self.mock_rag = None
        self.mock_sqlite = None
        self.mock_security = None
        
        # テストクライアント初期化
        self.test_client = None
        
        # パフォーマンス測定用
        self.start_time = None
        self.end_time = None
    
    def tearDown(self):
        """TaxMCPテストクリーンアップ"""
        # モックのクリーンアップ
        if hasattr(self, 'patches'):
            for patch_obj in self.patches:
                patch_obj.stop()
        
        super().tearDown()
    
    def setup_mocks(self):
        """モックオブジェクトをセットアップ"""
        from .mock_rag_simple import MockRAGIntegration
        from .mock_sqlite_indexer import MockSQLiteIndexer
        from .mock_security_manager import MockSecurityManager
        
        self.patches = []
        
        # RAG統合のモック
        rag_patch = patch('rag_integration.RAGIntegration', MockRAGIntegration)
        self.patches.append(rag_patch)
        self.mock_rag = rag_patch.start()
        
        # SQLiteインデックスのモック
        sqlite_patch = patch('sqlite_indexer.SQLiteIndexer', MockSQLiteIndexer)
        self.patches.append(sqlite_patch)
        self.mock_sqlite = sqlite_patch.start()
        
        # セキュリティマネージャーのモック
        security_patch = patch('security.SecurityManager', MockSecurityManager)
        self.patches.append(security_patch)
        self.mock_security = security_patch.start()
    
    def create_test_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """テスト用MCPリクエストを作成
        
        Args:
            method: メソッド名
            params: パラメータ
            
        Returns:
            MCPリクエスト
        """
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method
        }
        
        if params:
            request["params"] = params
        
        return request
    
    def assert_mcp_success(self, response: Dict[str, Any]):
        """MCP成功レスポンスをアサート
        
        Args:
            response: MCPレスポンス
        """
        from tests.utils.assertion_helpers import APIAssertions
        APIAssertions.assert_mcp_success(response)
    
    def assert_mcp_error(self, response: Dict[str, Any], expected_code: int = None):
        """MCPエラーレスポンスをアサート
        
        Args:
            response: MCPレスポンス
            expected_code: 期待されるエラーコード
        """
        from tests.utils.assertion_helpers import APIAssertions
        APIAssertions.assert_mcp_error(response, expected_code)
    
    def measure_performance(self, func, *args, **kwargs):
        """パフォーマンスを測定
        
        Args:
            func: 測定対象関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            (結果, 実行時間)
        """
        import time
        
        start_time = time.time()
        
        if asyncio.iscoroutinefunction(func):
            result = self.run_async(func(*args, **kwargs))
        else:
            result = func(*args, **kwargs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        return result, execution_time
    
    def generate_test_data(self, data_type: str, **kwargs):
        """テストデータを生成
        
        Args:
            data_type: データタイプ
            **kwargs: 追加パラメータ
            
        Returns:
            テストデータ
        """
        from tests.utils.test_data_generator import TestDataGenerator
        
        generator = TestDataGenerator()
        
        if data_type == "income_tax":
            return generator.generate_income_tax_data(**kwargs)
        elif data_type == "corporate_tax":
            return generator.generate_corporate_tax_data(**kwargs)
        elif data_type == "consumption_tax":
            return generator.generate_consumption_tax_data(**kwargs)
        elif data_type == "invalid":
            return generator.generate_invalid_data(**kwargs)
        else:
            raise ValueError(f"Unknown data type: {data_type}")


class PerformanceTestMixin:
    """パフォーマンステスト用ミックスイン"""
    
    def start_performance_measurement(self):
        """パフォーマンス測定を開始
        
        Returns:
            開始時刻
        """
        import time
        return time.time()
    
    def end_performance_measurement(self, start_time: float):
        """パフォーマンス測定を終了
        
        Args:
            start_time: 開始時刻
            
        Returns:
            パフォーマンス結果辞書
        """
        import time
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration
        }
    
    def assert_response_time(self, execution_time: float, max_time: float = None):
        """レスポンス時間をアサート
        
        Args:
            execution_time: 実行時間
            max_time: 最大許容時間
        """
        if max_time is None:
            max_time = TestConfig.PERFORMANCE_LIMITS["max_response_time"]
        
        from tests.utils.assertion_helpers import PerformanceAssertions
        PerformanceAssertions.assert_response_time(execution_time, max_time)
    
    def measure_memory_usage(self):
        """メモリ使用量を測定
        
        Returns:
            メモリ使用量（バイト）
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    
    def assert_memory_usage(self, max_usage: int = None):
        """メモリ使用量をアサート
        
        Args:
            max_usage: 最大許容使用量
        """
        if max_usage is None:
            max_usage = TestConfig.PERFORMANCE_LIMITS["max_memory_usage"]
        
        current_usage = self.measure_memory_usage()
        
        from tests.utils.assertion_helpers import PerformanceAssertions
        PerformanceAssertions.assert_memory_usage(current_usage, max_usage)


class SecurityTestMixin:
    """セキュリティテスト用ミックスイン"""
    
    def get_malicious_inputs(self, attack_type: str) -> list:
        """悪意のある入力を取得
        
        Args:
            attack_type: 攻撃タイプ
            
        Returns:
            悪意のある入力のリスト
        """
        return TestConfig.SECURITY_TEST_PATTERNS.get(attack_type, [])
    
    def assert_input_sanitized(self, original: str, sanitized: str):
        """入力のサニタイズを確認
        
        Args:
            original: 元の入力
            sanitized: サニタイズ後の入力
        """
        from tests.utils.assertion_helpers import SecurityAssertions
        SecurityAssertions.assert_input_sanitized(original, sanitized)
    
    def assert_no_sensitive_data(self, data: Any):
        """機密データの漏洩がないことを確認
        
        Args:
            data: チェック対象データ
        """
        from tests.utils.assertion_helpers import SecurityAssertions
        SecurityAssertions.assert_no_sensitive_data(data)


# テストスイート実行用のヘルパー関数
def run_test_suite(test_module_name: str = None):
    """テストスイートを実行
    
    Args:
        test_module_name: テストモジュール名（Noneの場合は全テスト）
    """
    import unittest
    
    if test_module_name:
        suite = unittest.TestLoader().loadTestsFromName(test_module_name)
    else:
        # 全テストを検索
        test_dir = Path(__file__).parent.parent
        suite = unittest.TestLoader().discover(str(test_dir), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # テスト設定の確認
    TestConfig.setup_test_environment()
    print("テスト環境設定完了")
    print(f"テストデータディレクトリ: {TestConfig.TEST_DATA_DIR}")
    print(f"パフォーマンス制限: {TestConfig.PERFORMANCE_LIMITS}")
    TestConfig.cleanup_test_environment()