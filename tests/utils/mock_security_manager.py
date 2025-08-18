"""セキュリティマネージャーモック

TaxMCPサーバーのセキュリティ機能をモックするためのクラス
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from .mock_response import MockResponse


class MockSecurityManager:
    """セキュリティマネージャーのモック"""

    def __init__(self):
        self.call_count = 0
        self.last_validation_result = None
        self.auth_attempts = []
        self.audit_logs = []

    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """入力検証のモック

        Args:
            input_data: 検証する入力データ

        Returns:
            検証結果（有効性、検出された脅威）
        """
        self.call_count += 1
        is_valid = True
        threats = []
        errors = []

        # SQLインジェクションパターン
        sql_injection_patterns = [
            "'; DROP TABLE", "' OR '1'='1", "'; INSERT INTO", "' UNION SELECT",
            "'; UPDATE", "' OR 1=1 /*", "'; EXEC", "' AND (SELECT COUNT(*)"
        ]
        # XSSパターン
        xss_patterns = [
            "<script>", "<img src=x onerror=", "javascript:", "<iframe>",
            "<svg onload=", "<body onload=", "onfocus=", "<a href='javascript:"
        ]
        # コマンドインジェクションパターン
        command_injection_patterns = [
            "; ls", "| cat", "&& rm", "; wget", "| nc", "; curl", "&& echo", "; python", "; rm"
        ]
        # パストラバーサルパターン
        path_traversal_patterns = [
            "../", "..\\", "%2e%2e%2f", "%2e%2e%5c", "..%252f", "..%255c",
            "%c0%af", "%c0%5c"
        ]

        for key, value in input_data.items():
            if isinstance(value, str):
                lower_value = value.lower()
                # SQLインジェクションチェック
                if any(p.lower() in lower_value for p in sql_injection_patterns):
                    is_valid = False
                    threats.append("sql_injection")
                # XSSチェック
                if any(p.lower() in lower_value for p in xss_patterns):
                    is_valid = False
                    threats.append("xss")
                # コマンドインジェクションチェック
                if any(p.lower() in lower_value for p in command_injection_patterns):
                    is_valid = False
                    threats.append("command_injection")
                # パストラバーサルチェック
                if any(p.lower() in lower_value for p in path_traversal_patterns):
                    is_valid = False
                    threats.append("path_traversal")
                
                # ヌルバイトチェック（制御文字チェックより先に実行）
                if '\x00' in value:
                    threats.append("null_byte_injection")
                    threats.append("special_character_injection")  # SecurityAssertions用
                    errors.append(f"ヌルバイトが検出されました: {key}")
                    is_valid = False
                # HTTPレスポンス分割チェック
                elif '\r\n' in value and ('HTTP/' in value or '<html>' in value.lower()):
                    threats.append("http_response_splitting")
                    threats.append("special_character_injection")  # SecurityAssertions用
                    errors.append(f"HTTPレスポンス分割攻撃が検出されました: {key}")
                    is_valid = False
                # 制御文字チェック（ヌルバイト以外）
                elif any(ord(c) < 32 and c not in '\t\n\r' and c != '\x00' for c in value):
                    threats.append("control_character_injection")
                    threats.append("special_character_injection")  # SecurityAssertions用
                    errors.append(f"制御文字が検出されました: {key}")
                    is_valid = False

                # Unicode制御文字チェック
                elif any(char in value for char in ['\u202e', '\u202d', '\u200e', '\u200f']):
                    threats.append("unicode_control_injection")
                    threats.append("special_character_injection")  # SecurityAssertions用
                    errors.append(f"Unicode制御文字が検出されました: {key}")
                    is_valid = False
                # エスケープシーケンスチェック
                elif '\\x' in value or '\\u' in value:
                    threats.append("escape_sequence_injection")
                    threats.append("special_character_injection")  # SecurityAssertions用
                    errors.append(f"エスケープシーケンスが検出されました: {key}")
                    is_valid = False
                # 一般的な特殊文字チェック
                else:
                    special_chars = ['<', '>', '&', '"', "'", ';', '|', '`', '$', '(', ')', '{', '}', '[', ']']
                    for char in special_chars:
                        if char in value:
                            threats.append("special_character_injection")
                            errors.append(f"特殊文字 '{char}' が検出されました: {key}")
                            is_valid = False
                            break

        validation_result = {
            "valid": is_valid,
            "threats_detected": list(set(threats)),
            "violations": errors
        }

        # セキュリティスコア計算
        security_score = 100
        if threats:
            security_score -= len(set(threats)) * 20
        if errors:
            security_score -= len(errors) * 10
        security_score = max(0, security_score)

        result = {
            "valid": is_valid,
            "threats_detected": list(set(threats)),  # 重複を削除
            "violations": errors,
            "sanitized_data": input_data,
            "security_score": security_score
        }
        self.last_validation_result = result
        return result

    def validate_data_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力データのデータ型を検証"""
        validation_result = {"valid": True, "invalid_fields": {}, "expected_types": {}, "type_violations": {}, "violations": [], "threats_detected": [], "security_score": 100}

        type_mappings = {
            "income": float,
            "tax_year": int,
            "deductions": float,
            "married": bool,
            "birth_date": date  # datetime.date型を期待
        }

        for field, expected_type in type_mappings.items():
            if field in data:
                value = data[field]
                is_valid = True

                if expected_type == float:
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        is_valid = False
                elif expected_type == int:
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        is_valid = False
                elif expected_type == bool:
                    if not isinstance(value, bool):
                        is_valid = False
                elif expected_type == date:
                    if not isinstance(value, str):
                        is_valid = False
                    else:
                        try:
                            datetime.strptime(value, "%Y-%m-%d").date()
                        except ValueError:
                            is_valid = False

                if not is_valid:
                    validation_result["valid"] = False
                    error_msg = f"Expected {expected_type.__name__}, got {type(value).__name__}"
                    validation_result["invalid_fields"][field] = error_msg
                    validation_result["violations"].append(f"Data type violation in {field}: {error_msg}")
                    validation_result["threats_detected"].append("data_type_violation")
                    validation_result["security_score"] -= 15  # データ型違反で15点減点
                    # expected_typesを配列形式にし、numberとfloatの両方を含む
                    if expected_type == float:
                        validation_result["expected_types"][field] = ["number", "float"]
                    elif expected_type == int:
                        validation_result["expected_types"][field] = ["integer", "int"]
                    elif expected_type == bool:
                        validation_result["expected_types"][field] = ["boolean", "bool"]
                    elif expected_type == date:
                        validation_result["expected_types"][field] = ["date"]
                    else:
                        validation_result["expected_types"][field] = [expected_type.__name__]
                    validation_result["type_violations"][field] = error_msg

        self.last_validation_result = validation_result
        return validation_result

    def validate_input_length(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力データの長さを検証"""
        validation_result = {"valid": True, "length_violations": {}, "violations": [], "threats_detected": [], "error_type": None, "security_score": 100}

        length_constraints = {
            "user_name": 1000,
            "description": 5000,
            "api_key": 256,
            "query": 2000,
            "notes": 10000
        }

        for field, max_length in length_constraints.items():
            if field in data and isinstance(data[field], str):
                if len(data[field]) > max_length:
                    validation_result["valid"] = False
                    error_msg = f"Exceeded max length of {max_length}"
                    validation_result["length_violations"][field] = error_msg
                    validation_result["violations"].append(f"Length violation in {field}: {error_msg}")
                    validation_result["threats_detected"].append("input_length_violation")
                    if validation_result["error_type"] is None:
                        validation_result["error_type"] = "length_violation_error"
                    validation_result["security_score"] -= 25

        self.last_validation_result = validation_result
        return validation_result


    def validate_json_structure(self, json_string: str) -> Dict[str, Any]:
        """JSON構造検証のモック"""
        try:
            json.loads(json_string)
            result = {"valid": True, "error_type": None, "violations": [], "threats_detected": [], "security_score": 100}
        except json.JSONDecodeError as e:
            # テストでは全てのJSONエラーでsyntax_errorを期待している
            error_msg = f"JSON syntax error: {str(e)}"
            result = {
                "valid": False, 
                "error_type": "syntax_error", 
                "details": str(e),
                "violations": [error_msg],
                "threats_detected": ["json_syntax_error"],
                "security_score": 75  # JSON構文エラーで25点減点
            }
        self.last_validation_result = result
        return result

    def validate_business_logic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ビジネスロジック検証のモック"""
        is_valid = True
        violations = []

        if "income" in params and params["income"] < 0:
            is_valid = False
            violations.append("negative_income")
        if "tax_year" in params and params["tax_year"] < 2000:
            is_valid = False
            violations.append("invalid_tax_year")
        if "deductions" in params and "income" in params and params["deductions"] > params["income"]:
            is_valid = False
            violations.append("deductions_exceed_income")
        if "birth_date" in params:
            try:
                birth_date = datetime.strptime(params["birth_date"], "%Y-%m-%d").date()
                if birth_date > date.today():
                    is_valid = False
                    violations.append("future_birth_date")
            except ValueError:
                pass # データ型検証で処理されるためここでは無視
        if "income" in params and params["income"] > 1_000_000_000_000:
            is_valid = False
            violations.append("unrealistic_income")

        threats_detected = ["business_logic_violation"] if not is_valid else []
        security_score = 100 - (len(violations) * 20)  # 各違反で20点減点
        error_type = "business_logic_error" if not is_valid else None
        result = {"valid": is_valid, "violations": violations, "threats_detected": threats_detected, "error_type": error_type, "security_score": security_score}
        self.last_validation_result = result
        return result




    def authenticate_user(self, username, password):
        """ユーザー認証のモック"""
        if username == "testuser" and password == "password123":
            self.auth_attempts.append({"username": username, "success": True})
            return MockResponse(200, {"message": "Authentication successful", "token": "mock_token"})
        else:
            self.auth_attempts.append({"username": username, "success": False})
            return MockResponse(401, {"message": "Authentication failed"})

    def verify_totp(self, username, totp_code):
        """TOTP検証のモック"""
        if username == "testuser" and totp_code == "123456":
            return MockResponse(200, {"message": "TOTP verification successful"})
        else:
            return MockResponse(401, {"message": "TOTP verification failed"})

    def check_permission(self, user_id, permission):
        """権限チェックのモック"""
        if user_id == "admin" and permission == "admin_access":
            return MockResponse(200, {"message": "Permission granted"})
        elif user_id == "testuser" and permission == "read_access":
            return MockResponse(200, {"message": "Permission granted"})
        else:
            return MockResponse(403, {"message": "Permission denied"})

    def check_rate_limit(self, ip_address, endpoint):
        """レート制限チェックのモック"""
        # 簡単なモック: 10.0.0.1からのリクエストは常に許可
        if ip_address == "10.0.0.1":
            return MockResponse(200, {"message": "Rate limit not exceeded"})
        else:
            # その他のIPアドレスは5回まで許可
            if not hasattr(self, '_rate_limit_counts'):
                self._rate_limit_counts = {}
            if ip_address not in self._rate_limit_counts:
                self._rate_limit_counts[ip_address] = 0
            self._rate_limit_counts[ip_address] += 1

            if self._rate_limit_counts[ip_address] <= 5:
                return MockResponse(200, {"message": "Rate limit not exceeded"})
            else:
                return MockResponse(429, {"message": "Rate limit exceeded"})

    def validate_session_token(self, token):
        """セッショントークン検証のモック"""
        if token == "valid_token":
            return MockResponse(200, {"message": "Session valid", "user_id": "testuser"})
        else:
            return MockResponse(401, {"message": "Session invalid"})

    def log_audit_event(self, event_type, user_id, details):
        """監査イベントログのモック"""
        self.audit_logs.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        })
        return MockResponse(200, {"message": "Audit event logged successfully"})




    def validate_special_characters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """特殊文字の検証"""
        is_valid = True
        threats = []
        errors = []

        for key, value in data.items():
            if isinstance(value, str):
                # ヌルバイトチェック
                if '\x00' in value:
                    threats.append("null_byte_injection")
                    threats.append("special_character_injection")
                    errors.append(f"ヌルバイトが検出されました: {key}")
                    is_valid = False
                # HTTPレスポンス分割チェック
                elif '\r\n' in value and ('HTTP/' in value or '<html>' in value.lower()):
                    threats.append("http_response_splitting")
                    threats.append("special_character_injection")
                    errors.append(f"HTTPレスポンス分割攻撃が検出されました: {key}")
                    is_valid = False
                # 制御文字チェック
                elif any(ord(c) < 32 and c not in '\t\n\r' and c != '\x00' for c in value):
                    threats.append("control_character_injection")
                    threats.append("special_character_injection")
                    errors.append(f"制御文字が検出されました: {key}")
                    is_valid = False
                # Unicode制御文字チェック
                elif any(char in value for char in ['\u202e', '\u202d', '\u200e', '\u200f']):
                    threats.append("unicode_control_injection")
                    threats.append("special_character_injection")
                    errors.append(f"Unicode制御文字が検出されました: {key}")
                    is_valid = False
                # エスケープシーケンスチェック
                elif '\\x' in value or '\\u' in value:
                    threats.append("escape_sequence_injection")
                    threats.append("special_character_injection")
                    errors.append(f"エスケープシーケンスが検出されました: {key}")
                    is_valid = False
                # 一般的な特殊文字チェック
                else:
                    special_chars = ['<', '>', '&', '"', "'", ';', '|', '`', '$', '(', ')', '{', '}', '[', ']']
                    for char in special_chars:
                        if char in value:
                            threats.append("special_character_injection")
                            errors.append(f"特殊文字 '{char}' が検出されました: {key}")
                            is_valid = False
                            break

        result = {
            "valid": is_valid,
            "threats_detected": list(set(threats)),
            "violations": errors,
            "error_type": "special_character_error" if not is_valid else None,
            "security_score": 75 if not is_valid else 100
        }
        self.last_validation_result = result
        return result



    def validate_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ビジネスロジックの検証"""
        is_valid = True
        violations = []

        # 所得が負でないこと
        if "income" in data and (not isinstance(data["income"], (int, float)) or data["income"] < 0):
            violations.append("negative_income")
            is_valid = False

        # 税年度が妥当な範囲内であること
        if "tax_year" in data and (not isinstance(data["tax_year"], int) or data["tax_year"] < 2000 or data["tax_year"] > 2050):
            violations.append("invalid_tax_year")
            is_valid = False

        # 控除が所得を超過しないこと
        if "income" in data and "deductions" in data and data["deductions"] > data["income"]:
            violations.append("deductions_exceed_income")
            is_valid = False

        # 生年月日が未来でないこと
        if "birth_date" in data and isinstance(data["birth_date"], str):
            try:
                birth_date_obj = datetime.strptime(data["birth_date"], "%Y-%m-%d").date()
                if birth_date_obj > date.today():
                    violations.append("future_birth_date")
                    is_valid = False
            except ValueError:
                # 日付フォーマットが不正な場合はデータ型検証で捕捉されるため、ここでは無視
                pass

        # 所得が非現実的な高額でないこと
        if "income" in data and isinstance(data["income"], (int, float)) and data["income"] > 1_000_000_000:
            violations.append("unrealistic_income")
            is_valid = False

        result = {
            "valid": is_valid,
            "violations": violations,
            "threats_detected": ["business_logic_violation"] if not is_valid else [],
            "error_type": "business_logic_error" if not is_valid else None,
            "security_score": 75 if not is_valid else 100
        }
        self.last_validation_result = result
        return result
    
    def authenticate_request(self, token: str) -> Dict[str, Any]:
        """リクエスト認証のモック
        
        Args:
            token: 認証トークン
            
        Returns:
            認証結果
        """
        self.auth_attempts.append({
            "token": token,
            "timestamp": datetime.now().isoformat(),
            "success": token == "valid_token"
        })
        
        if token == "valid_token":
            return {
                "authenticated": True,
                "user_id": "test_user",
                "permissions": ["read", "write"]
            }
        else:
            return {
                "authenticated": False,
                "error": "Invalid token"
            }
    
    def log_audit_event(self, event_type: str, details: Dict[str, Any]) -> bool:
        """監査ログ記録のモック
        
        Args:
            event_type: イベント種別
            details: イベント詳細
            
        Returns:
            記録成功フラグ
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        self.audit_logs.append(log_entry)
        return True
    
    def authenticate_api_key(self, api_key: str, client_id: str) -> Dict[str, Any]:
        """APIキー認証のモック
        
        Args:
            api_key: APIキー
            client_id: クライアントID
            
        Returns:
            認証結果
        """
        if api_key == "taxmcp_test_key_12345":
            return {
                "authenticated": True,
                "user_id": "test_user",
                "permissions": ["tax_calculation", "data_access"],
                "session_token": "mock_session_token_12345",
                "expires_at": (datetime.now().timestamp() + 3600)
            }
        else:
            return {
                 "authenticated": False,
                 "error": "Invalid API key"
             }
    
    def get_audit_logger(self):
        """監査ログ取得のモック
        
        Returns:
            モック監査ログ
        """
        return self

    def comprehensive_input_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """総合的な入力検証のモック
        
        Args:
            data: 検証するデータ
            
        Returns:
            検証結果
        """
        final_result = {
            "valid": True,
            "threats_detected": [],
            "violations": [],
            "error_type": None,
            "security_score": 100
        }

        # 各検証メソッドを呼び出し、結果を統合
        validation_methods = [
            self.validate_sql_injection,
            self.validate_xss,
            self.validate_command_injection,
            self.validate_path_traversal,
            self.validate_special_characters,
            self.validate_input_length,
            self.validate_data_types,
            self.validate_business_logic
        ]

        for method in validation_methods:
            # 各メソッドはdata全体を受け取るように調整
            # ただし、validate_special_charactersはparamsを期待するので、その場合はparamsを渡す
            if method == self.validate_special_characters:
                current_result = method(data) # dataがparamsとして機能すると仮定
            elif method == self.validate_json_structure: # JSON構造検証は文字列を期待
                # 総合検証ではJSON文字列が直接渡されるとは限らないため、スキップまたは適切な変換が必要
                # ここでは、json_dataキーがあればそれを渡すように仮定
                if "json_data" in data and isinstance(data["json_data"], str):
                    current_result = method(data["json_data"])
                else:
                    continue # json_dataがない、または文字列でない場合はスキップ
            else:
                current_result = method(data)

            if not current_result["valid"]:
                final_result["valid"] = False
                final_result["threats_detected"].extend(current_result["threats_detected"])
                final_result["violations"].extend(current_result["violations"])
                final_result["security_score"] -= (100 - current_result["security_score"]) # 各検証の減点分を加算
                if final_result["error_type"] is None and current_result["error_type"] is not None:
                    final_result["error_type"] = current_result["error_type"]

        # 重複する脅威タイプを削除
        final_result["threats_detected"] = list(set(final_result["threats_detected"]))
        final_result["violations"] = list(set(final_result["violations"]))

        # スコアが0未満にならないように調整
        if final_result["security_score"] < 0:
            final_result["security_score"] = 0

        # 結果を保存
        self.last_validation_result = final_result
        return final_result

    def validate_sql_injection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """SQLインジェクション検証のモック
        
        Args:
            data: 検証するデータ
            
        Returns:
            検証結果
        """
        result = {
            "valid": True,
            "threats_detected": [],
            "violations": [],
            "error_type": None,
            "security_score": 100
        }

        sql_injection_patterns = [
            "'; DROP TABLE", "' OR '1'='1", "'; INSERT INTO", "' UNION SELECT",
            "'; UPDATE", "' OR 1=1 /*", "'; EXEC", "' AND (SELECT COUNT(*)"
        ]

        for key, value in data.items():
            if isinstance(value, str):
                for pattern in sql_injection_patterns:
                    if pattern.lower() in value.lower():
                        result["valid"] = False
                        result["threats_detected"].append("sql_injection")
                        result["violations"].append(f"SQL Injection detected in {key}: {value}")
                        result["security_score"] -= 25
                        if result["error_type"] is None:
                            result["error_type"] = "sql_injection_error"
                        break
        return result

    def validate_xss(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """XSS検証のモック
        
        Args:
            data: 検証するデータ
            
        Returns:
            検証結果
        """
        result = {
            "valid": True,
            "threats_detected": [],
            "violations": [],
            "error_type": None,
            "security_score": 100
        }

        xss_patterns = [
            "<script>", "<img src=x onerror=", "javascript:", "<iframe>",
            "<svg onload=", "<body onload=", "onfocus=", "<a href='javascript:"
        ]

        for key, value in data.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if pattern.lower() in value.lower():
                        result["valid"] = False
                        result["threats_detected"].append("xss")
                        result["violations"].append(f"XSS detected in {key}: {value}")
                        result["security_score"] -= 25
                        if result["error_type"] is None:
                            result["error_type"] = "xss_error"
                        break
        return result

    def validate_command_injection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """コマンドインジェクション検証のモック
        
        Args:
            data: 検証するデータ
            
        Returns:
            検証結果
        """
        result = {
            "valid": True,
            "threats_detected": [],
            "violations": [],
            "error_type": None,
            "security_score": 100
        }

        command_injection_patterns = [
            "; ls", "| cat", "&& rm", "; wget", "| nc", "; curl", "&& echo", "; python", "; rm"
        ]

        for key, value in data.items():
            if isinstance(value, str):
                for pattern in command_injection_patterns:
                    if pattern.lower() in value.lower():
                        result["valid"] = False
                        result["threats_detected"].append("command_injection")
                        result["violations"].append(f"Command Injection detected in {key}: {value}")
                        result["security_score"] -= 25
                        if result["error_type"] is None:
                            result["error_type"] = "command_injection_error"
                        break
        return result

    def validate_path_traversal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """パストラバーサル検証のモック
        
        Args:
            data: 検証するデータ
            
        Returns:
            検証結果
        """
        result = {
            "valid": True,
            "threats_detected": [],
            "violations": [],
            "error_type": None,
            "security_score": 100
        }

        path_traversal_patterns = [
            "../", "..\\", "%2e%2e%2f", "%2e%2e%5c", "..%252f", "..%255c",
            "%c0%af", "%c0%5c"
        ]

        for key, value in data.items():
            if isinstance(value, str):
                for pattern in path_traversal_patterns:
                    if pattern.lower() in value.lower():
                        result["valid"] = False
                        result["threats_detected"].append("path_traversal")
                        result["violations"].append(f"Path Traversal detected in {key}: {value}")
                        result["security_score"] -= 25
                        if result["error_type"] is None:
                            result["error_type"] = "path_traversal_error"
                        break
        return result