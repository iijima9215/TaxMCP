"""外部API モックユーティリティ

TaxMCPサーバーの外部API連携をモックするためのユーティリティ
"""

import json
import asyncio
import re
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, date


class MockRAGIntegration:
    """RAG統合機能のモック"""
    
    def __init__(self):
        self.cache = {}
        self.call_count = 0
    
    async def get_latest_tax_info(self, query: str, category: str = "general") -> List[Dict[str, Any]]:
        """最新税制情報取得のモック
        
        Args:
            query: 検索クエリ
            category: カテゴリ
            
        Returns:
            モック検索結果
        """
        self.call_count += 1
        
        # クエリに基づくモックレスポンス
        mock_responses = {
            "基礎控除": [
                {
                    "title": "基礎控除の概要",
                    "content": "2025年度の基礎控除額は48万円です。",
                    "source": "国税庁",
                    "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1199.htm",
                    "last_updated": "2024-12-01",
                    "relevance_score": 0.95
                }
            ],
            "法人税率": [
                {
                    "title": "法人税率の改正",
                    "content": "中小法人の税率は15%、大法人は23%です。",
                    "source": "財務省",
                    "url": "https://www.mof.go.jp/tax_policy/",
                    "last_updated": "2024-11-15",
                    "relevance_score": 0.92
                }
            ],
            "消費税": [
                {
                    "title": "消費税率について",
                    "content": "標準税率10%、軽減税率8%が適用されます。",
                    "source": "国税庁",
                    "url": "https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/",
                    "last_updated": "2024-10-01",
                    "relevance_score": 0.98
                }
            ]
        }
        
        # 部分マッチで検索
        results = []
        for key, value in mock_responses.items():
            if key in query or query in key:
                results.extend(value)
        
        # デフォルトレスポンス
        if not results:
            results = [{
                "title": f"検索結果: {query}",
                "content": f"'{query}'に関する情報が見つかりました。",
                "source": "モックデータ",
                "url": "https://example.com/mock",
                "last_updated": datetime.now().isoformat(),
                "relevance_score": 0.5
            }]
        
        return results
    
    async def get_tax_rate_updates(self, year: Optional[int] = None) -> Dict[str, Any]:
        """税率更新情報取得のモック
        
        Args:
            year: 対象年度
            
        Returns:
            モック税率更新情報
        """
        self.call_count += 1
        
        return {
            "year": year or 2025,
            "updates": [
                {
                    "type": "income_tax",
                    "description": "基礎控除額の調整",
                    "effective_date": "2025-01-01",
                    "details": {
                        "old_value": 480000,
                        "new_value": 480000,
                        "change_reason": "据え置き"
                    }
                },
                {
                    "type": "corporate_tax",
                    "description": "中小法人税率の維持",
                    "effective_date": "2025-04-01",
                    "details": {
                        "small_company_rate": 0.15,
                        "large_company_rate": 0.23
                    }
                }
            ],
            "last_updated": datetime.now().isoformat()
        }
    
    async def search_legal_reference(self, query: str, law_type: str = "income_tax") -> List[Dict[str, Any]]:
        """法令参照検索のモック
        
        Args:
            query: 検索クエリ
            law_type: 法令種別
            
        Returns:
            モック法令検索結果
        """
        self.call_count += 1
        
        mock_laws = {
            "income_tax": [
                {
                    "law_name": "所得税法",
                    "article": "第1条",
                    "content": "この法律は、所得税について定めるものとする。",
                    "url": "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/detail?lawId=340AC0000000033"
                }
            ],
            "corporate_tax": [
                {
                    "law_name": "法人税法",
                    "article": "第1条",
                    "content": "この法律は、法人税について定めるものとする。",
                    "url": "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/detail?lawId=340AC0000000034"
                }
            ],
            "all": [
                {
                    "law_name": "所得税法",
                    "article": "第1条",
                    "content": "この法律は、所得税について定めるものとする。",
                    "url": "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/detail?lawId=340AC0000000033"
                },
                {
                    "law_name": "法人税法",
                    "article": "第1条",
                    "content": "この法律は、法人税について定めるものとする。",
                    "url": "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/detail?lawId=340AC0000000034"
                }
            ]
        }
        
        return mock_laws.get(law_type, [])

    async def search_cross_reference(self, query: str, tax_year: int) -> List[Dict[str, Any]]:
        """横断的参照検索のモック"""
        self.call_count += 1
        return [
            {
                "article": "所得税法第1条",
                "content": f"所得税法に関する横断的参照結果 for {query} in {tax_year}",
                "relevance_score": 0.85
            }
        ]

    async def search_semantic(self, query: str, tax_category: str) -> List[Dict[str, Any]]:
        """セマンティック検索のモック"""
        self.call_count += 1
        return [
            {
                "document_id": "doc123",
                "summary": f"所得税 給与所得 確定申告 住宅借入金等特別控除 法人税 消費税 住民税 法人設立 届出書 住宅取得 登録免許税 雑所得 20万円以下 セマンティック検索結果の要約 for {query} in {tax_category}",
                "score": 0.9
            }
        ]

    async def search_contextual(self, query: str, context: str) -> List[Dict[str, Any]]:
        """文脈的検索のモック"""
        self.call_count += 1
        return [
            {
                "article": "文脈的検索結果",
                "content": f"'{query}'に関する文脈的検索結果。コンテキスト: {context}",
                "relevance_score": 0.75
            }
        ]


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
            "; ls", "| cat", "&& rm", "; wget", "| nc", "; curl", "&& echo", "; python"
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
            "errors": errors
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
            "errors": errors,
            "sanitized_data": input_data,
            "security_score": security_score
        }
        self.last_validation_result = result
        return result


    def validate_data_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力データのデータ型を検証"""
        validation_result = {"valid": True, "invalid_fields": {}, "expected_types": {}}

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
                    validation_result["invalid_fields"][field] = f"Expected {expected_type.__name__}, got {type(value).__name__}"
                    validation_result["expected_types"][field] = expected_type.__name__

        self.last_validation_result = validation_result
        return validation_result



    def validate_input_length(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力データの長さを検証"""
        validation_result = {"valid": True, "length_violations": {}}

        length_constraints = {
            "user_name": 1000,
            "description": 5000,
            "api_key": 256,
            "query": 2000
        }

        for field, max_length in length_constraints.items():
            if field in data and isinstance(data[field], str):
                if len(data[field]) > max_length:
                    validation_result["valid"] = False
                    validation_result["length_violations"][field] = f"Exceeded max length of {max_length}"

        self.last_validation_result = validation_result
        return validation_result



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
            "errors": errors
        }
        self.last_validation_result = result
        return result

    def validate_json_structure(self, json_string: str) -> Dict[str, Any]:
        """JSON構造の検証"""
        is_valid = True
        error_type = None
        try:
            json.loads(json_string)
        except json.JSONDecodeError as e:
            is_valid = False
            error_type = "syntax_error"
            if "Expecting value" in str(e):
                error_type = "missing_value"
            elif "Expecting ',' delimiter" in str(e):
                error_type = "missing_comma"
            elif "Extra data" in str(e):
                error_type = "extra_data"
            elif "Unterminated string" in str(e):
                error_type = "unterminated_string"
            elif "Invalid control character" in str(e):
                error_type = "invalid_control_character"
            elif "Unterminated object or array" in str(e):
                error_type = "unterminated_structure"

        result = {
            "valid": is_valid,
            "error_type": error_type
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
            "violations": violations
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
    
    def validate_special_characters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """特殊文字検証のモック
        
        Args:
            data: 検証するデータ
            
        Returns:
            検証結果
        """
        self.call_count += 1
        is_valid = True
        threats = []
        errors = []
        
        for key, value in data.items():
            if isinstance(value, str):
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
        
        # セキュリティスコア計算
        security_score = 100
        if threats:
            security_score -= len(set(threats)) * 20
        if errors:
            security_score -= len(errors) * 10
        security_score = max(0, security_score)
        
        result = {
            "valid": is_valid,
            "threats_detected": list(set(threats)),
            "errors": errors,
            "sanitized_data": data,
            "security_score": security_score
        }
        self.last_validation_result = result
        return result
    
    def validate_json_structure(self, json_data: str) -> Dict[str, Any]:
        """JSON構造検証のモック
        
        Args:
            json_data: 検証するJSON文字列
            
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

        try:
            json.loads(json_data)
        except json.JSONDecodeError as e:
            result["valid"] = False
            result["threats_detected"].append("json_structure_violation")
            result["violations"].append(f"JSON decoding error: {e}")
            result["error_type"] = "syntax_error"
            result["security_score"] -= 30 # スコアを減点

        return result
    
    def validate_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ビジネスロジック検証のモック
        
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

        income = data.get("income")
        tax_year = data.get("tax_year")
        deductions = data.get("deductions", 0)
        birth_date = data.get("birth_date")

        if income is not None and income < 0:
            result["valid"] = False
            result["violations"].append("negative_income")
            result["threats_detected"].append("business_logic_violation")
            result["security_score"] -= 15
        if tax_year is not None and (tax_year < 1950 or tax_year > 2050):
            result["valid"] = False
            result["violations"].append("invalid_tax_year")
            result["threats_detected"].append("business_logic_violation")
            result["security_score"] -= 15
        if income is not None and deductions > income:
            result["valid"] = False
            result["violations"].append("deductions_exceed_income")
            result["threats_detected"].append("business_logic_violation")
            result["security_score"] -= 20
        if birth_date and birth_date > "2024-01-01": # 未来の生年月日を検出
            result["valid"] = False
            result["violations"].append("future_birth_date")
            result["threats_detected"].append("business_logic_violation")
            result["security_score"] -= 10
        if income is not None and income > 10**12: # 非現実的な高額所得
            result["valid"] = False
            result["violations"].append("unrealistic_income")
            result["threats_detected"].append("business_logic_violation")
            result["security_score"] -= 25

        if not result["valid"] and result["error_type"] is None:
            result["error_type"] = "business_logic_error"

        return result
    
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

        return final_result
    
    def validate_data_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データ型検証のモック
        
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

        # 期待されるデータ型の定義 (例)
        expected_types = {
            "income": (int, float),
            "tax_year": int,
            "deductions": (int, float),
            "birth_date": str, # YYYY-MM-DD形式を想定
            "user_name": str,
            "file_path": str,
            "command": str,
            "notes": str,
            "special_data": str
        }

        for key, value in data.items():
            if key in expected_types:
                if not isinstance(value, expected_types[key]):
                    result["valid"] = False
                    result["threats_detected"].append("data_type_violation")
                    result["violations"].append(f"Invalid data type for {key}. Expected {expected_types[key]}, got {type(value)}.")
                    result["security_score"] -= 20 # スコアを減点
                    if result["error_type"] is None:
                        result["error_type"] = "data_type_error"

        return result
    
    def validate_input_length(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力長検証のモック
        
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

        # 最大入力長の定義 (例)
        max_lengths = {
            "user_name": 50,
            "file_path": 200,
            "command": 100,
            "notes": 10000,
            "search_query": 255,
            "text_input": 5000,
            "user_comment": 1000
        }

        for key, value in data.items():
            if key in max_lengths and isinstance(value, str):
                if len(value) > max_lengths[key]:
                    result["valid"] = False
                    result["threats_detected"].append("input_length_violation")
                    result["violations"].append(f"Input for {key} exceeds maximum length of {max_lengths[key]}. Actual length: {len(value)}.")
                    result["security_score"] -= 10 # スコアを減点
                    if result["error_type"] is None:
                        result["error_type"] = "input_length_error"

        return result

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
            "; ls", "| cat", "&& rm", "; wget", "| nc", "; curl", "&& echo", "; python"
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


class MockSQLiteIndexer:
    """SQLiteインデックス機能のモック"""
    
    def __init__(self):
        self.documents = []
        self.index_built = False
    
    async def add_document(self, title: str, content: str, metadata: Dict[str, Any]) -> bool:
        """ドキュメント追加のモック
        
        Args:
            title: ドキュメントタイトル
            content: ドキュメント内容
            metadata: メタデータ
            
        Returns:
            追加成功フラグ
        """
        doc = {
            "id": len(self.documents) + 1,
            "title": title,
            "content": content,
            "metadata": metadata,
            "created_at": datetime.now().isoformat()
        }
        self.documents.append(doc)
        return True
    
    async def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """ドキュメント検索のモック
        
        Args:
            query: 検索クエリ
            limit: 結果数制限
            
        Returns:
            モック検索結果
        """
        results = []
        for doc in self.documents:
            if query.lower() in doc["title"].lower() or query.lower() in doc["content"].lower():
                results.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"][:200] + "...",
                    "metadata": doc["metadata"],
                    "score": 0.8
                })
                if len(results) >= limit:
                    break
        return results
    
    async def build_index(self) -> bool:
        """インデックス構築のモック
        
        Returns:
            構築成功フラグ
        """
        self.index_built = True
        return True
    
    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得のモック
        
        Returns:
            モック統計情報
        """
        return {
            "total_documents": len(self.documents),
            "index_size": len(self.documents) * 1024,  # 仮のサイズ
            "last_updated": datetime.now().isoformat(),
            "index_built": self.index_built
        }



class MockExternalAPIs:
    """外部API群のモック"""
    
    @staticmethod
    def mock_mof_api():
        """財務省APIのモック
        
        Returns:
            モックレスポンス
        """
        return {
            "status": 200,
            "data": {
                "tax_reforms": [
                    {
                        "year": 2025,
                        "title": "令和7年度税制改正大綱",
                        "url": "https://www.mof.go.jp/tax_policy/tax_reform/outline/fy2025/20241213taikou.pdf",
                        "summary": "基礎控除額の据え置き等"
                    }
                ]
            }
        }
    
    @staticmethod
    def mock_nta_api():
        """国税庁APIのモック
        
        Returns:
            モックレスポンス
        """
        return {
            "status": 200,
            "data": {
                "tax_answers": [
                    {
                        "id": "1199",
                        "title": "基礎控除",
                        "content": "基礎控除は、すべての納税者に適用される控除です。",
                        "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1199.htm"
                    }
                ]
            }
        }
    
    @staticmethod
    def mock_egov_api():
        """e-Gov法令検索APIのモック
        
        Returns:
            モックレスポンス
        """
        return {
            "status": 200,
            "data": {
                "laws": [
                    {
                        "law_id": "340AC0000000033",
                        "law_name": "所得税法",
                        "articles": [
                            {
                                "article_number": "第1条",
                                "content": "この法律は、所得税について定めるものとする。"
                            }
                        ]
                    }
                ]
            }
        }


class MockContextManager:
    """モックコンテキストマネージャー"""
    
    def __init__(self):
        self.patches = []
    
    def __enter__(self):
        # RAG統合のモック
        rag_patch = patch('rag_integration.RAGIntegration', MockRAGIntegration)
        self.patches.append(rag_patch)
        rag_patch.start()
        
        # SQLiteインデックスのモック
        sqlite_patch = patch('sqlite_indexer.SQLiteIndexer', MockSQLiteIndexer)
        self.patches.append(sqlite_patch)
        sqlite_patch.start()
        
        # セキュリティマネージャーのモック
        security_patch = patch('security.SecurityManager', MockSecurityManager)
        self.patches.append(security_patch)
        security_patch.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for patch_obj in self.patches:
            patch_obj.stop()
        self.patches.clear()


# 便利な関数
def create_mock_response(status_code: int = 200, data: Any = None, error: str = None) -> Dict[str, Any]:
    """モックレスポンス作成
    
    Args:
        status_code: ステータスコード
        data: レスポンスデータ
        error: エラーメッセージ
        
    Returns:
        モックレスポンス
    """
    response = {
        "status_code": status_code,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if error is not None:
        response["error"] = error
    
    return response


def create_mock_http_client():
    """モックHTTPクライアント作成
    
    Returns:
        モックHTTPクライアント
    """
    mock_client = Mock()
    
    # GET リクエストのモック
    async def mock_get(url: str, **kwargs):
        if "mof.go.jp" in url:
            return create_mock_response(data=MockExternalAPIs.mock_mof_api())
        elif "nta.go.jp" in url:
            return create_mock_response(data=MockExternalAPIs.mock_nta_api())
        elif "e-gov.go.jp" in url:
            return create_mock_response(data=MockExternalAPIs.mock_egov_api())
        else:
            return create_mock_response(status_code=404, error="Not found")
    
    mock_client.get = AsyncMock(side_effect=mock_get)
    
    return mock_client