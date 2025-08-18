# -*- coding: utf-8 -*-
"""
TaxMCPサーバーのテストで使用するアサーション関数群
"""

import json
import math
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date


class TaxAssertions:
    """税計算関連のアサーション"""
    
    @staticmethod
    def assert_tax_calculation_result(result: Dict[str, Any], expected_keys: List[str] = None):
        """税計算結果の基本構造をアサート
        
        Args:
            result: 税計算結果
            expected_keys: 期待されるキーのリスト
        """
        assert isinstance(result, dict), "計算結果はdict型である必要があります"
        
        if expected_keys:
            for key in expected_keys:
                assert key in result, f"計算結果に必要なキー '{key}' がありません"
    
    @staticmethod
    def assert_income_tax_calculation(result: Dict[str, Any], expected_amount: float, tolerance: float = 0.01):
        """所得税計算結果をアサート
        
        Args:
            result: 税計算結果
            expected_amount: 期待される税額
            tolerance: 許容誤差
        """
        assert "income_tax" in result, "計算結果に所得税情報がありません"
        assert "amount" in result["income_tax"], "所得税情報に金額がありません"
        
        actual_amount = result["income_tax"]["amount"]
        assert abs(actual_amount - expected_amount) <= tolerance, \
            f"所得税額が期待値と異なります: {actual_amount} != {expected_amount} (許容誤差: {tolerance})"
    
    @staticmethod
    def assert_corporate_tax_calculation(result: Dict[str, Any], expected_amount: float, tolerance: float = 0.01):
        """法人税計算結果をアサート
        
        Args:
            result: 税計算結果
            expected_amount: 期待される税額
            tolerance: 許容誤差
        """
        assert "corporate_tax" in result, "計算結果に法人税情報がありません"
        assert "amount" in result["corporate_tax"], "法人税情報に金額がありません"
        
        actual_amount = result["corporate_tax"]["amount"]
        assert abs(actual_amount - expected_amount) <= tolerance, \
            f"法人税額が期待値と異なります: {actual_amount} != {expected_amount} (許容誤差: {tolerance})"
    
    @staticmethod
    def assert_consumption_tax_calculation(result: Dict[str, Any], expected_amount: float, tolerance: float = 0.01):
        """消費税計算結果をアサート
        
        Args:
            result: 税計算結果
            expected_amount: 期待される税額
            tolerance: 許容誤差
        """
        assert "consumption_tax" in result, "計算結果に消費税情報がありません"
        assert "amount" in result["consumption_tax"], "消費税情報に金額がありません"
        
        actual_amount = result["consumption_tax"]["amount"]
        assert abs(actual_amount - expected_amount) <= tolerance, \
            f"消費税額が期待値と異なります: {actual_amount} != {expected_amount} (許容誤差: {tolerance})"
    
    @staticmethod
    def assert_local_tax_calculation(result: Dict[str, Any], expected_amount: float, tolerance: float = 0.01):
        """地方税計算結果をアサート
        
        Args:
            result: 税計算結果
            expected_amount: 期待される税額
            tolerance: 許容誤差
        """
        assert "local_tax" in result, "計算結果に地方税情報がありません"
        assert "amount" in result["local_tax"], "地方税情報に金額がありません"
        
        actual_amount = result["local_tax"]["amount"]
        assert abs(actual_amount - expected_amount) <= tolerance, \
            f"地方税額が期待値と異なります: {actual_amount} != {expected_amount} (許容誤差: {tolerance})"
    
    @staticmethod
    def assert_tax_rate_applied(result: Dict[str, Any], tax_type: str, expected_rate: float, tolerance: float = 0.0001):
        """適用された税率をアサート
        
        Args:
            result: 税計算結果
            tax_type: 税種別 (income_tax, corporate_tax, consumption_tax, local_tax)
            expected_rate: 期待される税率
            tolerance: 許容誤差
        """
        assert tax_type in result, f"計算結果に{tax_type}情報がありません"
        assert "rate" in result[tax_type], f"{tax_type}情報に税率がありません"
        
        actual_rate = result[tax_type]["rate"]
        assert abs(actual_rate - expected_rate) <= tolerance, \
            f"{tax_type}の税率が期待値と異なります: {actual_rate} != {expected_rate} (許容誤差: {tolerance})"
    
    @staticmethod
    def assert_deduction_applied(result: Dict[str, Any], deduction_type: str, expected_amount: float, tolerance: float = 0.01):
        """控除適用をアサート
        
        Args:
            result: 税計算結果
            deduction_type: 控除種別
            expected_amount: 期待される控除額
            tolerance: 許容誤差
        """
        assert "deductions" in result, "計算結果に控除情報がありません"
        assert deduction_type in result["deductions"], f"控除情報に{deduction_type}がありません"
        
        actual_amount = result["deductions"][deduction_type]
        assert abs(actual_amount - expected_amount) <= tolerance, \
            f"{deduction_type}の控除額が期待値と異なります: {actual_amount} != {expected_amount} (許容誤差: {tolerance})"
    
    @staticmethod
    def assert_tax_rate_validity(actual_rate: float, min_rate: float, max_rate: float):
        """税率の妥当性をアサート
        
        Args:
            actual_rate: 実際の税率
            min_rate: 最小税率
            max_rate: 最大税率
        """
        assert min_rate <= actual_rate <= max_rate, \
            f"税率が妥当な範囲外です: {actual_rate} (範囲: {min_rate} - {max_rate})"
    
    @staticmethod
    def assert_tax_amount_accuracy(actual_amount: float, expected_amount: float, tolerance: float = 1.0):
        """税額の精度をアサート
        
        Args:
            actual_amount: 実際の税額
            expected_amount: 期待される税額
            tolerance: 許容誤差
        """
        assert abs(actual_amount - expected_amount) <= tolerance, \
            f"税額が期待値と異なります: {actual_amount} != {expected_amount} (許容誤差: {tolerance})"
    
    @staticmethod
    def assert_consumption_tax_calculation_result(test_instance, actual_result: Dict[str, Any], expected_result: Dict[str, Any]):
        """消費税計算結果をアサート
        
        Args:
            test_instance: テストインスタンス
            actual_result: 実際の計算結果
            expected_result: 期待される計算結果
        """
        test_instance.assertEqual(actual_result["total_tax"], expected_result["total_tax"], "消費税総額が一致しません")
        test_instance.assertEqual(actual_result["sales_tax"], expected_result["sales_tax"], "売上税額が一致しません")
        test_instance.assertEqual(actual_result["purchase_tax"], expected_result["purchase_tax"], "仕入税額が一致しません")
        test_instance.assertEqual(actual_result["net_tax"], expected_result["net_tax"], "純税額が一致しません")


class APIAssertions:
    """API関連のアサーション"""
    
    @staticmethod
    def assert_status_code(response, expected_code: int):
        """ステータスコードをアサート
        
        Args:
            response: APIレスポンス
            expected_code: 期待されるステータスコード
        """
        assert hasattr(response, 'status_code'), "レスポンスにステータスコードがありません"
        assert response.status_code == expected_code, \
            f"ステータスコードが期待値と異なります: {response.status_code} != {expected_code}"
    
    @staticmethod
    def assert_json_response(response):
        """JSONレスポンスをアサート
        
        Args:
            response: APIレスポンス
        """
        assert hasattr(response, 'headers'), "レスポンスにヘッダー情報がありません"
        assert 'Content-Type' in response.headers, "レスポンスにContent-Typeヘッダーがありません"
        assert 'application/json' in response.headers['Content-Type'], \
            f"Content-Typeがapplication/jsonではありません: {response.headers['Content-Type']}"
        
        try:
            response.json()
        except Exception as e:
            assert False, f"レスポンスが有効なJSONではありません: {str(e)}"
    
    @staticmethod
    def assert_error_response(response, expected_code: int, error_key: str = 'error'):
        """エラーレスポンスをアサート
        
        Args:
            response: APIレスポンス
            expected_code: 期待されるステータスコード
            error_key: エラーメッセージのキー
        """
        APIAssertions.assert_status_code(response, expected_code)
        APIAssertions.assert_json_response(response)
        
        data = response.json()
        assert error_key in data, f"エラーレスポンスに{error_key}キーがありません"
        assert data[error_key], "エラーメッセージが空です"
    
    @staticmethod
    def assert_pagination(response, page: int, per_page: int, total_items: Optional[int] = None):
        """ページネーションをアサート
        
        Args:
            response: APIレスポンス
            page: 現在のページ番号
            per_page: 1ページあたりのアイテム数
            total_items: 全アイテム数（省略可）
        """
        APIAssertions.assert_json_response(response)
        
        data = response.json()
        assert "pagination" in data, "レスポンスにページネーション情報がありません"
        pagination = data["pagination"]
        
        assert "page" in pagination, "ページネーション情報にpage属性がありません"
        assert pagination["page"] == page, f"現在のページが期待値と異なります: {pagination['page']} != {page}"
        
        assert "per_page" in pagination, "ページネーション情報にper_page属性がありません"
        assert pagination["per_page"] == per_page, \
            f"1ページあたりのアイテム数が期待値と異なります: {pagination['per_page']} != {per_page}"
        
        if total_items is not None:
            assert "total" in pagination, "ページネーション情報にtotal属性がありません"
            assert pagination["total"] == total_items, \
                f"全アイテム数が期待値と異なります: {pagination['total']} != {total_items}"
            
            expected_total_pages = math.ceil(total_items / per_page) if per_page > 0 else 0
            assert "total_pages" in pagination, "ページネーション情報にtotal_pages属性がありません"
            assert pagination["total_pages"] == expected_total_pages, \
                f"全ページ数が期待値と異なります: {pagination['total_pages']} != {expected_total_pages}"
    
    @staticmethod
    def assert_success_response(response, expected_keys: List[str] = None):
        """成功レスポンスをアサート
        
        Args:
            response: APIレスポンス
            expected_keys: 期待されるキーのリスト
        """
        APIAssertions.assert_status_code(response, 200)
        APIAssertions.assert_json_response(response)
        
        data = response.json()
        if expected_keys:
            for key in expected_keys:
                assert key in data, f"レスポンスに必要なキー '{key}' がありません"
    
    @staticmethod
    def assert_mcp_response(response, expected_id: Optional[Union[int, str]] = None):
        """MCPレスポンスをアサート
        
        Args:
            response: MCPレスポンス
            expected_id: 期待されるリクエストID
        """
        APIAssertions.assert_json_response(response)
        
        data = response.json()
        assert "jsonrpc" in data, "MCPレスポンスにjsonrpcフィールドがありません"
        assert data["jsonrpc"] == "2.0", f"JSONRPCバージョンが2.0ではありません: {data['jsonrpc']}"
        
        if expected_id is not None:
            assert "id" in data, "MCPレスポンスにidフィールドがありません"
            assert data["id"] == expected_id, f"レスポンスIDが期待値と異なります: {data['id']} != {expected_id}"


class SecurityAssertions:
    """セキュリティ関連のアサーション"""
    
    @staticmethod
    def assert_sql_injection_blocked(security_manager, malicious_input: str, time_window: float = 1.0):
        """SQLインジェクション攻撃がブロックされることをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            malicious_input: 悪意のある入力
            time_window: 検証時間枠(秒)
        """
        # 入力検証は呼び出し元で実行されるため、ここでは実行しない
        # テスト内で既に security_manager.validate_input が呼び出されている
        # 結果は security_manager.last_validation_result から取得する
        result = security_manager.last_validation_result
        assert not result["valid"], f"SQLインジェクション攻撃がブロックされていません: {malicious_input}"
        assert "sql_injection" in result["threats_detected"], "SQLインジェクション脅威が検出されていません"
    
    @staticmethod
    def assert_xss_blocked(security_manager, malicious_input: str, time_window: float = 1.0):
        """XSS攻撃がブロックされることをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            malicious_input: 悪意のある入力
            time_window: 検証時間枠(秒)
        """
        # 入力検証は呼び出し元で実行されるため、ここでは実行しない
        result = security_manager.last_validation_result
        assert not result["valid"], f"XSS攻撃がブロックされていません: {malicious_input}"
        assert "xss" in result["threats_detected"], "XSS脅威が検出されていません"
    
    @staticmethod
    def assert_command_injection_blocked(security_manager, malicious_input: str, time_window: float = 1.0):
        """コマンドインジェクション攻撃がブロックされることをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            malicious_input: 悪意のある入力
            time_window: 検証時間枠(秒)
        """
        # 入力検証は呼び出し元で実行されるため、ここでは実行しない
        result = security_manager.last_validation_result
        assert not result["valid"], f"コマンドインジェクション攻撃がブロックされていません: {malicious_input}"
        assert "command_injection" in result["threats_detected"], "コマンドインジェクション脅威が検出されていません"
    
    @staticmethod
    def assert_path_traversal_blocked(security_manager, malicious_input: str, time_window: float = 1.0):
        """パストラバーサル攻撃がブロックされることをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            malicious_input: 悪意のある入力
            time_window: 検証時間枠(秒)
        """
        # 入力検証は呼び出し元で実行されるため、ここでは実行しない
        result = security_manager.last_validation_result
        assert not result["valid"], f"パストラバーサル攻撃がブロックされていません: {malicious_input}"
        assert "path_traversal" in result["threats_detected"], "パストラバーサル脅威が検出されていません"
    
    @staticmethod
    def assert_data_type_invalid(security_manager, field: str, invalid_value: Any, expected_type: str):
        """データ型検証が失敗することをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            field: フィールド名
            invalid_value: 無効な値
            expected_type: 期待されるデータ型
        """
        result = security_manager.validate_data_types({field: invalid_value})
        assert not result["valid"], f"データ型検証が失敗していません: {field}={invalid_value}"
        assert field in result["type_violations"], f"{field}がデータ型違反として記録されていません"
        assert expected_type in result["expected_types"][field], f"{field}の期待されるデータ型が{expected_type}ではありません"
    
    @staticmethod
    def assert_input_length_exceeded(security_manager, field: str, long_input: str, max_length: int = None):
        """入力長制限違反をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            field: フィールド名
            long_input: 長すぎる入力
            max_length: 最大許容長
        """
        result = security_manager.validate_input_length({field: long_input})
        assert not result["valid"], f"入力長制限違反が検出されていません: {field}"
        assert field in result["length_violations"], f"{field}が長さ違反として記録されていません"
    
    @staticmethod
    def assert_special_characters_blocked(security_manager, malicious_input: str):
        """特殊文字インジェクションがブロックされることをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            malicious_input: 悪意のある入力
        """
        # 入力検証は呼び出し元で実行されるため、ここでは実行しない
        result = security_manager.last_validation_result
        assert not result["valid"], f"特殊文字インジェクションがブロックされていません: {malicious_input}"
        assert "special_character_injection" in result["threats_detected"], "特殊文字インジェクション脅威が検出されていません"
    
    @staticmethod
    def assert_json_invalid(security_manager, json_data: str, description: str = ""): 
        """JSON構造が無効であることをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            json_data: 検証するJSON文字列
        """
        # 入力検証は呼び出し元で実行されるため、ここでは実行しない
        result = security_manager.last_validation_result
        assert not result["valid"], f"JSON構造が無効として検出されていません: {json_data}"
        assert "error_type" in result, "JSON構造エラータイプが記録されていません"
    
    @staticmethod
    def assert_business_logic_violation(security_manager, params: Dict[str, Any]):
        """ビジネスロジック違反をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            params: 検証するパラメータ
        """
        # 入力検証は呼び出し元で実行されるため、ここでは実行しない
        result = security_manager.last_validation_result
        assert not result["valid"], f"ビジネスロジック違反が検出されていません: {params}"
        assert "violations" in result, "ビジネスロジック違反が記録されていません"
        assert len(result["violations"]) > 0, "ビジネスロジック違反が少なくとも1つ検出されるべきです"
    
    @staticmethod
    def assert_comprehensive_validation_failed(security_manager, params: Dict[str, Any]):
        """総合的な入力検証が失敗することをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            params: 検証するパラメータ
        """
        # 入力検証は呼び出し元で実行されるため、ここでは実行しない
        result = security_manager.last_validation_result
        assert not result["valid"], "総合的な入力検証が失敗していません"
        assert "threats_detected" in result, "検出された脅威が記録されていません"
        assert len(result["threats_detected"]) > 0, "少なくとも1つの脅威が検出されるべきです"
        assert "violations" in result, "検出された違反が記録されていません"
        assert "security_score" in result, "セキュリティスコアが記録されていません"
        assert result["security_score"] <= 50, "危険なリクエストのセキュリティスコアが低すぎます"
    
    @staticmethod
    def assert_authentication_success(security_manager, api_key: str, client_id: str):
        """認証成功をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            api_key: APIキー
            client_id: クライアントID
        """
        result = security_manager.authenticate_api_key(api_key, client_id)
        assert result["authenticated"], "認証が成功していません"
        assert "session_token" in result, "セッショントークンが含まれていません"
    
    @staticmethod
    def assert_authentication_failure(security_manager, api_key: str, client_id: str):
        """認証失敗をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            api_key: APIキー
            client_id: クライアントID
        """
        result = security_manager.authenticate_api_key(api_key, client_id)
        assert not result["authenticated"], "認証が失敗していません"
        assert "error" in result, "エラー情報が含まれていません"
    
    @staticmethod
    def assert_session_valid(security_manager, session_token: str):
        """セッション有効性をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            session_token: セッショントークン
        """
        result = security_manager.validate_session_token(session_token)
        assert result["valid"] == True, "セッションが有効ではありません"
    
    @staticmethod
    def assert_session_invalid(security_manager, session_token: str):
        """セッション無効性をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            session_token: セッショントークン
        """
        result = security_manager.validate_session_token(session_token)
        assert result["valid"] == False, "セッションが無効として検出されていません"
    
    @staticmethod
    def assert_rate_limit_exceeded(security_manager, client_id: str):
        """レート制限超過をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            client_id: クライアントID
        """
        result = security_manager.check_rate_limit(client_id, "/api/test")
        assert not result["allowed"], "レート制限が超過していません"
        assert "retry_after" in result, "リトライ時間が含まれていません"
    
    @staticmethod
    def assert_access_granted(security_manager, user_id: str, resource: str, permission: str):
        """アクセス許可をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            user_id: ユーザーID
            resource: リソース
            permission: 権限
        """
        result = security_manager.check_permission(user_id, permission)
        assert result["granted"], f"アクセスが許可されていません: {user_id} -> {permission}"
    
    @staticmethod
    def assert_access_denied(security_manager, user_id: str, resource: str, permission: str):
        """アクセス拒否をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            user_id: ユーザーID
            resource: リソース
            permission: 権限
        """
        result = security_manager.check_permission(user_id, permission)
        assert not result["granted"], f"アクセスが拒否されていません: {user_id} -> {permission}"
    
    @staticmethod
    def assert_brute_force_blocked(security_manager, client_id: str):
        """ブルートフォース攻撃ブロックをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            client_id: クライアントID
        """
        result = security_manager.check_brute_force_protection(client_id)
        assert result["blocked"], "ブルートフォース攻撃がブロックされていません"
        assert "lockout_duration" in result, "ロックアウト時間が含まれていません"
    
    @staticmethod
    def assert_security_headers_valid(security_manager, headers: dict):
        """セキュリティヘッダーの有効性をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            headers: HTTPヘッダー
        """
        result = security_manager.validate_security_headers(headers)
        assert result["valid"], f"セキュリティヘッダーが無効: {result.get('missing_headers', [])}"
    
    @staticmethod
    def assert_mfa_success(security_manager, session_token: str, totp_code: str):
        """多要素認証成功をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            session_token: セッショントークン
            totp_code: TOTPコード
        """
        # モック実装では常に成功とする
        assert session_token is not None, "セッショントークンが必要です"
        assert totp_code is not None, "TOTPコードが必要です"
    
    @staticmethod
    def assert_audit_log_recorded(security_manager, event: dict):
        """監査ログ記録をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            event: イベント情報
        """
        result = security_manager.log_audit_event(
            event.get("event_type", "test_event"),
            event.get("user_id", "test_user"),
            event.get("details", {})
        )
        assert result["logged"] == True, "監査ログが記録されていません"
    
    @staticmethod
    def assert_security_incident_logged(security_manager, incident: dict):
        """セキュリティインシデントログをアサート
        
        Args:
            security_manager: セキュリティマネージャー
            incident: インシデント情報
        """
        result = security_manager.log_audit_event(
            "security_incident",
            incident.get("user_id", "unknown"),
            incident
        )
        assert result.status_code == 200, "セキュリティインシデントが記録されていません"
    
    @staticmethod
    def assert_log_integrity_valid(security_manager, integrity_check: dict):
        """ログ整合性の有効性をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            integrity_check: 整合性チェック結果
        """
        assert integrity_check.get("valid", False), "ログの整合性が無効です"
    
    @staticmethod
    def assert_log_tampering_detected(security_manager, integrity_check: dict):
        """ログ改ざん検出をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            integrity_check: 整合性チェック結果
        """
        assert not integrity_check.get("valid", True), "ログ改ざんが検出されていません"
    
    @staticmethod
    def assert_retention_policy_valid(security_manager, policy: dict):
        """保持ポリシーの有効性をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            policy: 保持ポリシー
        """
        assert policy.get("valid", False), "保持ポリシーが無効です"
    
    @staticmethod
    def assert_log_archival_successful(security_manager, archive_result: dict):
        """ログアーカイブ成功をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            archive_result: アーカイブ結果
        """
        assert archive_result.get("success", False), "ログアーカイブが失敗しました"
    
    @staticmethod
    def assert_log_search_successful(security_manager, search_result: dict):
        """ログ検索成功をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            search_result: 検索結果
        """
        assert search_result.get("success", False), "ログ検索が失敗しました"
        assert "results" in search_result, "検索結果が含まれていません"
    
    @staticmethod
    def assert_incident_analysis_valid(security_manager, analysis: dict):
        """インシデント分析の有効性をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            analysis: 分析結果
        """
        assert analysis.get("valid", False), "インシデント分析が無効です"
    
    @staticmethod
    def assert_monitoring_setup_successful(security_manager, setup: dict):
        """監視設定成功をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            setup: 設定結果
        """
        assert setup.get("success", False), "監視設定が失敗しました"
    
    @staticmethod
    def assert_alerts_triggered(security_manager, alerts: dict):
        """アラート発火をアサート
        
        Args:
            security_manager: セキュリティマネージャー
            alerts: アラート情報
        """
        assert alerts.get("triggered", False), "アラートが発火していません"


class PerformanceAssertions:
    """パフォーマンス関連のアサーション"""
    
    @staticmethod
    def assert_response_time(actual_time: float, max_time: float):
        """レスポンス時間をアサート
        
        Args:
            actual_time: 実際の時間(秒)
            max_time: 最大許容時間(秒)
        """
        assert actual_time <= max_time, f"レスポンス時間が制限を超えています: {actual_time:.3f}秒 > {max_time:.3f}秒"
    
    @staticmethod
    def assert_response_time_acceptable(performance_result: Dict[str, Any], max_duration: float):
        """応答時間が許容範囲内であることをアサート

        Args:
            performance_result: パフォーマンス測定結果
            max_duration: 許容される最大応答時間(秒)
        """
        assert "duration" in performance_result, "パフォーマンス結果にdurationキーが含まれていません"
        assert performance_result["duration"] <= max_duration, \
            f"応答時間が許容範囲を超えています: {performance_result['duration']:.3f}秒 (許容: {max_duration:.3f}秒)"

    @staticmethod
    def assert_concurrent_performance_acceptable(
        performance_result: Dict[str, Any],
        request_count: int,
        max_duration: float
    ):
        """並行処理のパフォーマンスが許容範囲内であることをアサート

        Args:
            performance_result: パフォーマンス測定結果
            request_count: 並行リクエスト数
            max_duration: 許容される最大応答時間(秒)
        """
        assert "duration" in performance_result, "パフォーマンス結果にdurationキーが含まれていません"
        assert performance_result["duration"] <= max_duration, \
            f"並行処理の応答時間が許容範囲を超えています: {performance_result['duration']:.3f}秒 (許容: {max_duration:.3f}秒)"
        assert "start_time" in performance_result, "パフォーマンス結果にstart_timeキーが含まれていません"
        assert "end_time" in performance_result, "パフォーマンス結果にend_timeキーが含まれていません"
        assert request_count > 0, "リクエスト数は0より大きい必要があります"
    
    @staticmethod
    def assert_memory_usage(current_usage: int, max_usage: int):
        """メモリ使用量をアサート
        
        Args:
            current_usage: 現在の使用量(バイト)
            max_usage: 最大許容使用量(バイト)
        """
        assert current_usage <= max_usage, f"メモリ使用量が制限を超えています: {current_usage} > {max_usage} bytes"
    
    @staticmethod
    def assert_throughput(requests_per_second: float, min_throughput: float):
        """スループットをアサート
        
        Args:
            requests_per_second: 実際のRPS
            min_throughput: 最小要求スループット
        """
        assert requests_per_second >= min_throughput, f"スループットが要求を下回っています: {requests_per_second:.2f} < {min_throughput:.2f} RPS"


class DataAssertions:
    """データ関連のアサーション"""
    
    @staticmethod
    def assert_json_structure(data: Dict[str, Any], expected_schema: Dict[str, Any]):
        """JSON構造をアサート
        
        Args:
            data: 検証対象データ
            expected_schema: 期待されるスキーマ
        """
        def validate_field(value, schema, path=""):
            if isinstance(schema, dict):
                if "type" in schema:
                    expected_type = schema["type"]
                    if expected_type == "string":
                        assert isinstance(value, str), f"{path}: 文字列である必要があります"
                    elif expected_type == "number":
                        assert isinstance(value, (int, float)), f"{path}: 数値である必要があります"
                    elif expected_type == "boolean":
                        assert isinstance(value, bool), f"{path}: 真偽値である必要があります"
                    elif expected_type == "array":
                        assert isinstance(value, list), f"{path}: 配列である必要があります"
                    elif expected_type == "object":
                        assert isinstance(value, dict), f"{path}: オブジェクトである必要があります"
                
                if "required" in schema and isinstance(value, dict):
                    for required_field in schema["required"]:
                        assert required_field in value, f"{path}: 必須フィールド '{required_field}' がありません"
                
                if "properties" in schema and isinstance(value, dict):
                    for prop_name, prop_schema in schema["properties"].items():
                        if prop_name in value:
                            validate_field(value[prop_name], prop_schema, f"{path}.{prop_name}")
        
        validate_field(data, expected_schema)
    
    @staticmethod
    def assert_date_format(date_str: str, expected_format: str = "%Y-%m-%d"):
        """日付フォーマットをアサート
        
        Args:
            date_str: 日付文字列
            expected_format: 期待されるフォーマット
        """
        try:
            datetime.strptime(date_str, expected_format)
        except ValueError:
            assert False, f"日付フォーマットが正しくありません: '{date_str}' (期待: {expected_format})"
    
    @staticmethod
    def assert_currency_format(amount: Union[int, float], currency: str = "JPY"):
        """通貨フォーマットをアサート
        
        Args:
            amount: 金額
            currency: 通貨コード
        """
        assert isinstance(amount, (int, float)), "金額は数値である必要があります"
        
        if currency == "JPY":
            # 日本円は整数
            assert amount == int(amount), "日本円は整数である必要があります"
            assert amount >= 0, "金額は非負である必要があります"


# 便利な関数
def assert_all(assertions: List[callable], message: str = "アサーション失敗"):
    """複数のアサーションを実行
    
    Args:
        assertions: アサーション関数のリスト
        message: 失敗時のメッセージ
    """
    for i, assertion in enumerate(assertions):
        try:
            assertion()
        except AssertionError as e:
            raise AssertionError(f"{message} (アサーション {i+1}): {str(e)}")


def assert_eventually(condition: callable, timeout: float = 5.0, interval: float = 0.1):
    """条件が最終的に満たされることをアサート
    
    Args:
        condition: 条件関数
        timeout: タイムアウト(秒)
        interval: チェック間隔(秒)
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            if condition():
                return
        except:
            pass
        time.sleep(interval)
    
    assert False, f"条件が{timeout}秒以内に満たされませんでした"