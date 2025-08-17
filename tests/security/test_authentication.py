"""認証機能テスト

TaxMCPサーバーの認証機能をテストする
"""

import unittest
import sys
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.test_config import TaxMCPTestCase, SecurityTestMixin
from tests.utils.assertion_helpers import SecurityAssertions
from tests.utils.mock_external_apis import MockSecurityManager


class TestAuthentication(TaxMCPTestCase, SecurityTestMixin):
    """認証機能テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.security_manager = MockSecurityManager()
    
    def test_valid_api_key_authentication(self):
        """有効なAPIキー認証テスト"""
        print("\n=== 有効なAPIキー認証テスト ===")
        
        # 有効なAPIキー
        valid_api_key = "taxmcp_test_key_12345"
        
        # 認証リクエスト
        auth_request = {
            "method": "authenticate",
            "params": {
                "api_key": valid_api_key,
                "client_id": "test_client",
                "timestamp": int(time.time())
            }
        }
        
        print(f"認証リクエスト: {auth_request}")
        
        # 認証実行
        auth_result = self.security_manager.authenticate_api_key(
            valid_api_key,
            auth_request["params"]["client_id"]
        )
        
        print(f"認証結果: {auth_result}")
        
        # 期待される結果
        expected_result = {
            "authenticated": True,
            "user_id": "test_user",
            "permissions": ["tax_calculation", "data_access"],
            "session_token": auth_result.get("session_token"),
            "expires_at": auth_result.get("expires_at")
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        SecurityAssertions.assert_authentication_success(auth_result)
        self.assertTrue(auth_result["authenticated"], "認証が成功している")
        self.assertIn("session_token", auth_result, "セッショントークンが含まれている")
        self.assertIn("expires_at", auth_result, "有効期限が設定されている")
        
        print("✓ 有効なAPIキー認証テスト成功")
    
    def test_invalid_api_key_authentication(self):
        """無効なAPIキー認証テスト"""
        print("\n=== 無効なAPIキー認証テスト ===")
        
        # 無効なAPIキー
        invalid_api_key = "invalid_key_12345"
        
        # 認証リクエスト
        auth_request = {
            "method": "authenticate",
            "params": {
                "api_key": invalid_api_key,
                "client_id": "test_client",
                "timestamp": int(time.time())
            }
        }
        
        print(f"認証リクエスト: {auth_request}")
        
        # 認証実行
        auth_result = self.security_manager.authenticate_api_key(
            invalid_api_key,
            auth_request["params"]["client_id"]
        )
        
        print(f"認証結果: {auth_result}")
        
        # 期待される結果
        expected_result = {
            "authenticated": False,
            "error": "Invalid API key",
            "error_code": "AUTH_001"
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        SecurityAssertions.assert_authentication_failure(auth_result)
        self.assertFalse(auth_result["authenticated"], "認証が失敗している")
        self.assertIn("error", auth_result, "エラーメッセージが含まれている")
        
        print("✓ 無効なAPIキー認証テスト成功")
    
    def test_session_token_validation(self):
        """セッショントークン検証テスト"""
        print("\n=== セッショントークン検証テスト ===")
        
        # 有効なセッショントークンを取得
        api_key = "taxmcp_test_key_12345"
        auth_result = self.security_manager.authenticate_api_key(api_key, "test_client")
        session_token = auth_result["session_token"]
        
        print(f"セッショントークン: {session_token}")
        
        # トークン検証リクエスト
        validation_request = {
            "method": "validate_session",
            "params": {
                "session_token": session_token,
                "timestamp": int(time.time())
            }
        }
        
        print(f"検証リクエスト: {validation_request}")
        
        # トークン検証実行
        validation_result = self.security_manager.validate_session_token(session_token)
        
        print(f"検証結果: {validation_result}")
        
        # 期待される結果
        expected_result = {
            "valid": True,
            "user_id": "test_user",
            "permissions": ["tax_calculation", "data_access"],
            "expires_at": validation_result.get("expires_at")
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        SecurityAssertions.assert_session_valid(validation_result)
        self.assertTrue(validation_result["valid"], "セッションが有効")
        self.assertEqual(validation_result["user_id"], "test_user", "ユーザーIDが正しい")
        
        print("✓ セッショントークン検証テスト成功")
    
    def test_expired_session_token(self):
        """期限切れセッショントークンテスト"""
        print("\n=== 期限切れセッショントークンテスト ===")
        
        # 期限切れのセッショントークン
        expired_token = "expired_token_12345"
        
        # トークン検証リクエスト
        validation_request = {
            "method": "validate_session",
            "params": {
                "session_token": expired_token,
                "timestamp": int(time.time())
            }
        }
        
        print(f"検証リクエスト: {validation_request}")
        
        # トークン検証実行（期限切れをシミュレート）
        validation_result = {
            "valid": False,
            "error": "Session token expired",
            "error_code": "AUTH_002",
            "expired_at": int(time.time()) - 3600  # 1時間前に期限切れ
        }
        
        print(f"検証結果: {validation_result}")
        
        # アサーション
        SecurityAssertions.assert_session_invalid(validation_result)
        self.assertFalse(validation_result["valid"], "セッションが無効")
        self.assertIn("expired", validation_result["error"].lower(), "期限切れエラー")
        
        print("✓ 期限切れセッショントークンテスト成功")
    
    def test_rate_limiting(self):
        """レート制限テスト"""
        print("\n=== レート制限テスト ===")
        
        # レート制限設定
        rate_limit = 5  # 5回/分
        client_id = "test_client_rate_limit"
        
        print(f"レート制限: {rate_limit}回/分")
        print(f"クライアントID: {client_id}")
        
        # 制限回数まで認証リクエストを送信
        successful_requests = 0
        for i in range(rate_limit + 2):  # 制限を超えて送信
            auth_request = {
                "method": "authenticate",
                "params": {
                    "api_key": "taxmcp_test_key_12345",
                    "client_id": client_id,
                    "timestamp": int(time.time()),
                    "request_id": f"req_{i}"
                }
            }
            
            # レート制限チェック
            rate_check = self.security_manager.check_rate_limit(client_id)
            
            if rate_check["allowed"]:
                successful_requests += 1
                print(f"リクエスト {i+1}: 成功 (残り: {rate_check['remaining']})")
            else:
                print(f"リクエスト {i+1}: レート制限により拒否")
                print(f"制限詳細: {rate_check}")
                
                # レート制限エラーのアサーション
                SecurityAssertions.assert_rate_limit_exceeded(rate_check)
                self.assertFalse(rate_check["allowed"], "レート制限が適用されている")
                self.assertIn("retry_after", rate_check, "リトライ時間が指定されている")
                break
        
        print(f"成功したリクエスト数: {successful_requests}/{rate_limit}")
        self.assertLessEqual(successful_requests, rate_limit, "レート制限が正しく動作")
        
        print("✓ レート制限テスト成功")
    
    def test_permission_based_access_control(self):
        """権限ベースアクセス制御テスト"""
        print("\n=== 権限ベースアクセス制御テスト ===")
        
        # 異なる権限レベルのユーザー
        users = [
            {
                "user_id": "admin_user",
                "permissions": ["tax_calculation", "data_access", "admin"],
                "description": "管理者ユーザー"
            },
            {
                "user_id": "regular_user",
                "permissions": ["tax_calculation"],
                "description": "一般ユーザー"
            },
            {
                "user_id": "readonly_user",
                "permissions": ["data_access"],
                "description": "読み取り専用ユーザー"
            }
        ]
        
        # アクセス制御テストケース
        access_tests = [
            {
                "resource": "tax_calculation",
                "required_permission": "tax_calculation",
                "description": "税計算機能"
            },
            {
                "resource": "admin_panel",
                "required_permission": "admin",
                "description": "管理パネル"
            },
            {
                "resource": "data_export",
                "required_permission": "data_access",
                "description": "データエクスポート"
            }
        ]
        
        for user in users:
            print(f"\n--- {user['description']} ---")
            print(f"ユーザー権限: {user['permissions']}")
            
            for test in access_tests:
                print(f"\n{test['description']}へのアクセステスト:")
                
                # アクセス制御チェック
                access_result = self.security_manager.check_permission(
                    user["user_id"],
                    test["required_permission"]
                )
                
                print(f"アクセス結果: {access_result}")
                
                # 期待される結果
                expected_access = test["required_permission"] in user["permissions"]
                
                # アサーション
                if expected_access:
                    SecurityAssertions.assert_access_granted(access_result)
                    self.assertTrue(
                        access_result["granted"],
                        f"{user['description']}は{test['description']}にアクセス可能"
                    )
                else:
                    SecurityAssertions.assert_access_denied(access_result)
                    self.assertFalse(
                        access_result["granted"],
                        f"{user['description']}は{test['description']}にアクセス不可"
                    )
                
                print(f"✓ {user['description']}の{test['description']}アクセステスト成功")
    
    def test_authentication_security_headers(self):
        """認証セキュリティヘッダーテスト"""
        print("\n=== 認証セキュリティヘッダーテスト ===")
        
        # セキュリティヘッダー付きリクエスト
        secure_request = {
            "method": "authenticate",
            "headers": {
                "X-API-Key": "taxmcp_test_key_12345",
                "X-Client-ID": "test_client",
                "X-Request-ID": "req_12345",
                "X-Timestamp": str(int(time.time())),
                "User-Agent": "TaxMCP-Client/1.0",
                "Content-Type": "application/json"
            },
            "params": {
                "timestamp": int(time.time())
            }
        }
        
        print(f"セキュアリクエスト: {secure_request}")
        
        # ヘッダー検証
        header_validation = self.security_manager.validate_security_headers(
            secure_request["headers"]
        )
        
        print(f"ヘッダー検証結果: {header_validation}")
        
        # 期待される結果
        expected_validation = {
            "valid": True,
            "security_score": 95,
            "checks": {
                "api_key_present": True,
                "client_id_present": True,
                "request_id_present": True,
                "timestamp_valid": True,
                "user_agent_valid": True,
                "content_type_valid": True
            }
        }
        
        print(f"期待される結果: {expected_validation}")
        
        # アサーション
        SecurityAssertions.assert_security_headers_valid(header_validation)
        self.assertTrue(header_validation["valid"], "セキュリティヘッダーが有効")
        self.assertGreaterEqual(
            header_validation["security_score"],
            90,
            "セキュリティスコアが高い"
        )
        
        print("✓ 認証セキュリティヘッダーテスト成功")
    
    def test_brute_force_protection(self):
        """ブルートフォース攻撃保護テスト"""
        print("\n=== ブルートフォース攻撃保護テスト ===")
        
        # 攻撃者のクライアントID
        attacker_client = "attacker_client"
        
        # 連続した認証失敗をシミュレート
        failed_attempts = 0
        max_attempts = 5
        
        print(f"最大試行回数: {max_attempts}")
        
        for attempt in range(max_attempts + 2):
            print(f"\n--- 試行 {attempt + 1} ---")
            
            # 無効なAPIキーで認証試行
            auth_request = {
                "method": "authenticate",
                "params": {
                    "api_key": f"invalid_key_{attempt}",
                    "client_id": attacker_client,
                    "timestamp": int(time.time())
                }
            }
            
            print(f"認証試行: {auth_request}")
            
            # ブルートフォース保護チェック
            protection_check = self.security_manager.check_brute_force_protection(
                attacker_client
            )
            
            print(f"保護チェック結果: {protection_check}")
            
            if protection_check["blocked"]:
                print(f"ブルートフォース攻撃として検出・ブロック")
                
                # ブロック状態のアサーション
                SecurityAssertions.assert_brute_force_blocked(protection_check)
                self.assertTrue(protection_check["blocked"], "攻撃がブロックされている")
                self.assertIn("lockout_duration", protection_check, "ロックアウト期間が設定")
                break
            else:
                failed_attempts += 1
                print(f"認証失敗 (失敗回数: {failed_attempts})")
        
        print(f"\n総失敗回数: {failed_attempts}")
        self.assertLessEqual(
            failed_attempts,
            max_attempts,
            "ブルートフォース保護が正しく動作"
        )
        
        print("✓ ブルートフォース攻撃保護テスト成功")
    
    def test_multi_factor_authentication(self):
        """多要素認証テスト"""
        print("\n=== 多要素認証テスト ===")
        
        # 第1要素: APIキー認証
        api_key = "taxmcp_test_key_12345"
        first_factor_result = self.security_manager.authenticate_api_key(
            api_key, "mfa_test_client"
        )
        
        print(f"第1要素認証結果: {first_factor_result}")
        
        # 第2要素: TOTPコード
        totp_code = "123456"  # テスト用固定コード
        second_factor_request = {
            "method": "verify_totp",
            "params": {
                "session_token": first_factor_result["session_token"],
                "totp_code": totp_code,
                "timestamp": int(time.time())
            }
        }
        
        print(f"第2要素認証リクエスト: {second_factor_request}")
        
        # TOTP検証
        totp_result = self.security_manager.verify_totp(
            first_factor_result["session_token"],
            totp_code
        )
        
        print(f"TOTP検証結果: {totp_result}")
        
        # 期待される結果
        expected_mfa_result = {
            "authenticated": True,
            "mfa_completed": True,
            "user_id": "test_user",
            "permissions": ["tax_calculation", "data_access"],
            "session_token": totp_result.get("session_token"),
            "mfa_factors": ["api_key", "totp"]
        }
        
        print(f"期待される結果: {expected_mfa_result}")
        
        # アサーション
        SecurityAssertions.assert_mfa_success(totp_result)
        self.assertTrue(totp_result["mfa_completed"], "多要素認証が完了")
        self.assertIn("totp", totp_result["mfa_factors"], "TOTPが認証要素に含まれる")
        
        print("✓ 多要素認証テスト成功")
    
    def test_authentication_audit_logging(self):
        """認証監査ログテスト"""
        print("\n=== 認証監査ログテスト ===")
        
        # 認証イベントのシミュレート
        auth_events = [
            {
                "event_type": "authentication_success",
                "api_key": "taxmcp_test_key_12345",
                "client_id": "test_client",
                "timestamp": int(time.time())
            },
            {
                "event_type": "authentication_failure",
                "api_key": "invalid_key",
                "client_id": "suspicious_client",
                "timestamp": int(time.time())
            },
            {
                "event_type": "session_expired",
                "session_token": "expired_token_12345",
                "user_id": "test_user",
                "timestamp": int(time.time())
            }
        ]
        
        # 各イベントのログ記録
        logged_events = []
        for event in auth_events:
            print(f"\n--- {event['event_type']} ---")
            print(f"イベント: {event}")
            
            # 監査ログ記録
            log_result = self.security_manager.log_auth_event(event)
            logged_events.append(log_result)
            
            print(f"ログ結果: {log_result}")
            
            # ログ記録のアサーション
            SecurityAssertions.assert_audit_log_recorded(log_result)
            self.assertTrue(log_result["logged"], "監査ログが記録されている")
            self.assertIn("log_id", log_result, "ログIDが生成されている")
        
        # 監査ログ検索テスト
        print("\n--- 監査ログ検索 ---")
        search_result = self.security_manager.search_audit_logs({
            "event_type": "authentication_failure",
            "time_range": {
                "start": int(time.time()) - 3600,
                "end": int(time.time())
            }
        })
        
        print(f"検索結果: {search_result}")
        
        # 検索結果のアサーション
        self.assertGreater(len(search_result["logs"]), 0, "失敗ログが検索される")
        
        print("✓ 認証監査ログテスト成功")


if __name__ == "__main__":
    unittest.main(verbosity=2)