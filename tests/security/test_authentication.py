import unittest
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from tests.utils.mock_security_manager import MockSecurityManager


class TestSecurityCore(unittest.TestCase):
    """セキュリティ機能の核心テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.security_manager = MockSecurityManager()
    
    def test_token_creation_and_verification(self):
        """トークン作成と検証のテスト"""
        # トークン作成
        data = {"user_id": "test_user", "permissions": ["read", "write"]}
        token = self.security_manager.create_access_token(data)
        
        # トークン検証
        payload = self.security_manager.verify_token(token)
        
        # アサーション
        self.assertIsNotNone(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["user_id"], "test_user")
        self.assertEqual(payload["permissions"], ["read", "write"])
    
    def test_expired_token_rejection(self):
        """期限切れトークンの拒否テスト"""
        # 期限切れトークンを作成
        expired_token = self.security_manager.create_expired_token()
        
        # 検証
        payload = self.security_manager.verify_token(expired_token)
        
        # アサーション
        self.assertIsNone(payload)
    
    def test_invalid_token_rejection(self):
        """無効トークンの拒否テスト"""
        invalid_token = "invalid.token.here"
        
        # 検証
        payload = self.security_manager.verify_token(invalid_token)
        
        # アサーション
        self.assertIsNone(payload)
    
    def test_input_validation_required_fields(self):
        """必須フィールド検証テスト"""
        required_fields = ["user_id", "amount"]
        
        # 有効なデータ
        valid_data = {"user_id": "test", "amount": 1000}
        is_valid, message = self.security_manager.validate_input(valid_data, required_fields)
        self.assertTrue(is_valid)
        
        # 無効なデータ（必須フィールド不足）
        invalid_data = {"user_id": "test"}
        is_valid, message = self.security_manager.validate_input(invalid_data, required_fields)
        self.assertFalse(is_valid)
        self.assertIn("amount", message)
    
    def test_input_validation_numeric_fields(self):
        """数値フィールド検証テスト"""
        required_fields = ["annual_income"]
        
        # 有効な数値
        valid_data = {"annual_income": 5000000}
        is_valid, message = self.security_manager.validate_input(valid_data, required_fields)
        self.assertTrue(is_valid)
        
        # 負の数値
        invalid_data = {"annual_income": -1000}
        is_valid, message = self.security_manager.validate_input(invalid_data, required_fields)
        self.assertFalse(is_valid)
        self.assertIn("non-negative", message)
        
        # 文字列
        invalid_data = {"annual_income": "not_a_number"}
        is_valid, message = self.security_manager.validate_input(invalid_data, required_fields)
        self.assertFalse(is_valid)
        self.assertIn("valid number", message)
    
    def test_input_sanitization(self):
        """入力サニタイズテスト"""
        dirty_data = {
            "name": "  test user  ",
            "amount": 150000000,  # 上限超過
            "description": "x" * 2000  # 長すぎる文字列
        }
        
        sanitized = self.security_manager.sanitize_input(dirty_data)
        
        # アサーション
        self.assertEqual(sanitized["name"], "test user")  # トリム済み
        self.assertEqual(sanitized["amount"], 100000000)  # 上限適用
        self.assertEqual(len(sanitized["description"]), 1000)  # 長さ制限
    
    def test_data_type_validation(self):
        """データ型検証テスト"""
        # 有効なデータ型
        valid_data = {
            "income": 5000000.0,
            "tax_year": 2024,
            "married": True
        }
        result = self.security_manager.validate_data_types(valid_data)
        self.assertTrue(result["valid"])
        
        # 無効なデータ型
        invalid_data = {
            "income": "not_a_number",
            "tax_year": "2024",  # 文字列だが数値に変換可能
            "married": "yes"  # 文字列（booleanではない）
        }
        result = self.security_manager.validate_data_types(invalid_data)
        self.assertFalse(result["valid"])
        self.assertIn("income", result["type_violations"])
        self.assertIn("married", result["type_violations"])
    
    def test_input_length_validation(self):
        """入力長検証テスト"""
        # 有効な長さ
        valid_data = {"user_name": "test_user", "description": "short desc"}
        result = self.security_manager.validate_input_length(valid_data)
        self.assertTrue(result["valid"])
        
        # 無効な長さ
        invalid_data = {
            "user_name": "x" * 1001,  # 上限超過
            "description": "x" * 5001  # 上限超過
        }
        result = self.security_manager.validate_input_length(invalid_data)
        self.assertFalse(result["valid"])
        self.assertIn("user_name", result["length_violations"])
        self.assertIn("description", result["length_violations"])
    
    def test_api_key_generation_and_hashing(self):
        """APIキー生成とハッシュ化テスト"""
        # APIキー生成
        api_key = self.security_manager.generate_api_key()
        
        # ハッシュ化
        hashed = self.security_manager.hash_api_key(api_key)
        
        # アサーション
        self.assertIsNotNone(api_key)
        self.assertGreater(len(api_key), 20)  # 十分な長さ
        self.assertIsNotNone(hashed)
        self.assertNotEqual(api_key, hashed)  # ハッシュ化されている
        
        # 同じAPIキーは同じハッシュを生成
        hashed2 = self.security_manager.hash_api_key(api_key)
        self.assertEqual(hashed, hashed2)


class TestAuditLogging(unittest.TestCase):
    """監査ログ機能のテスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.security_manager = MockSecurityManager()
    
    def test_api_call_logging(self):
        """API呼び出しログテスト"""
        # API呼び出しをログ記録
        result = self.security_manager.log_api_call(
            tool_name="calculate_tax",
            params={"income": 5000000},
            client_id="test_client",
            success=True
        )
        
        # アサーション
        self.assertTrue(result["logged"])
        self.assertEqual(result["event_type"], "api_call")
    
    def test_security_event_logging(self):
        """セキュリティイベントログテスト"""
        # セキュリティイベントをログ記録
        result = self.security_manager.log_security_event(
            event_type="authentication_failure",
            details="Invalid API key",
            client_id="suspicious_client"
        )
        
        # アサーション
        self.assertTrue(result["logged"])
        self.assertEqual(result["event_type"], "authentication_failure")


if __name__ == '__main__':
    unittest.main()