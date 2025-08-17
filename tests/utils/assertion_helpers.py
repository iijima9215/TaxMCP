"""アサーションヘルパーユーティリティ

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
            expected_keys: 期待されるキー一覧
        """
        assert isinstance(result, dict), "結果は辞書型である必要があります"
        
        # 基本的なキーの存在確認
        basic_keys = ["total_tax", "calculation_details", "tax_year"]
        if expected_keys:
            basic_keys.extend(expected_keys)
        
        for key in basic_keys:
            assert key in result, f"結果に'{key}'キーが含まれている必要があります"
        
        # 税額は非負の数値
        assert isinstance(result["total_tax"], (int, float)), "total_taxは数値である必要があります"
        assert result["total_tax"] >= 0, "税額は非負である必要があります"
        
        # 年度は妥当な範囲
        assert isinstance(result["tax_year"], int), "tax_yearは整数である必要があります"
        assert 2020 <= result["tax_year"] <= 2030, "税年度は2020-2030の範囲である必要があります"
    
    @staticmethod
    def assert_income_tax_result(result: Dict[str, Any]):
        """所得税計算結果をアサート
        
        Args:
            result: 所得税計算結果
        """
        TaxAssertions.assert_tax_calculation_result(result)
        
        # 所得税特有のキー
        income_tax_keys = ["income_tax", "resident_tax", "social_insurance"]
        for key in income_tax_keys:
            if key in result:
                assert isinstance(result[key], (int, float)), f"{key}は数値である必要があります"
                assert result[key] >= 0, f"{key}は非負である必要があります"
        
        # 計算詳細の確認
        if "calculation_details" in result:
            details = result["calculation_details"]
            assert isinstance(details, dict), "calculation_detailsは辞書型である必要があります"
            
            # 基礎控除の確認
            if "basic_deduction" in details:
                assert details["basic_deduction"] >= 0, "基礎控除は非負である必要があります"
    
    @staticmethod
    def assert_corporate_tax_result(result: Dict[str, Any]):
        """法人税計算結果をアサート
        
        Args:
            result: 法人税計算結果
        """
        TaxAssertions.assert_tax_calculation_result(result)
        
        # 法人税特有のキー
        corporate_tax_keys = ["corporate_tax", "local_corporate_tax", "business_tax"]
        for key in corporate_tax_keys:
            if key in result:
                assert isinstance(result[key], (int, float)), f"{key}は数値である必要があります"
                assert result[key] >= 0, f"{key}は非負である必要があります"
        
        # 税率の確認
        if "tax_rate" in result:
            assert 0 <= result["tax_rate"] <= 1, "税率は0-1の範囲である必要があります"
    
    @staticmethod
    def assert_tax_amount_accuracy(actual: float, expected: float, tolerance: float = 1.0):
        """税額の精度をアサート
        
        Args:
            actual: 実際の税額
            expected: 期待される税額
            tolerance: 許容誤差（円）
        """
        assert isinstance(actual, (int, float)), "実際の税額は数値である必要があります"
        assert isinstance(expected, (int, float)), "期待される税額は数値である必要があります"
        
        diff = abs(actual - expected)
        assert diff <= tolerance, f"税額の誤差が許容範囲を超えています: 実際={actual}, 期待={expected}, 誤差={diff}, 許容={tolerance}"
    
    @staticmethod
    def assert_tax_rate_validity(rate: float, min_rate: float = 0.0, max_rate: float = 1.0):
        """税率の妥当性をアサート
        
        Args:
            rate: 税率
            min_rate: 最小税率
            max_rate: 最大税率
        """
        assert isinstance(rate, (int, float)), "税率は数値である必要があります"
        assert min_rate <= rate <= max_rate, f"税率が範囲外です: {rate} (範囲: {min_rate}-{max_rate})"


class APIAssertions:
    """API関連のアサーション"""
    
    @staticmethod
    def assert_mcp_response(response: Dict[str, Any]):
        """MCPレスポンスの基本構造をアサート
        
        Args:
            response: MCPレスポンス
        """
        assert isinstance(response, dict), "レスポンスは辞書型である必要があります"
        
        # MCPプロトコルの基本構造
        if "jsonrpc" in response:
            assert response["jsonrpc"] == "2.0", "JSON-RPC 2.0である必要があります"
        
        # IDの存在確認（リクエストがある場合）
        if "id" in response:
            assert response["id"] is not None, "IDが設定されている必要があります"
    
    @staticmethod
    def assert_success_response(response: Dict[str, Any]):
        """成功レスポンスをアサート
        
        Args:
            response: レスポンス
        """
        APIAssertions.assert_mcp_response(response)
        assert "result" in response, "成功レスポンスにはresultキーが必要です"
        assert "error" not in response, "成功レスポンスにはerrorキーがあってはいけません"
    
    @staticmethod
    def assert_error_response(response: Dict[str, Any], expected_code: int = None):
        """エラーレスポンスをアサート
        
        Args:
            response: レスポンス
            expected_code: 期待されるエラーコード
        """
        APIAssertions.assert_mcp_response(response)
        assert "error" in response, "エラーレスポンスにはerrorキーが必要です"
        assert "result" not in response, "エラーレスポンスにはresultキーがあってはいけません"
        
        error = response["error"]
        assert isinstance(error, dict), "errorは辞書型である必要があります"
        assert "code" in error, "エラーにはcodeが必要です"
        assert "message" in error, "エラーにはmessageが必要です"
        
        if expected_code is not None:
            assert error["code"] == expected_code, f"期待されるエラーコード: {expected_code}, 実際: {error['code']}"
    
    @staticmethod
    def assert_mcp_error(response: Dict[str, Any], expected_code: int = None):
        """MCPエラーレスポンスをアサート
        
        Args:
            response: MCPレスポンス
            expected_code: 期待されるエラーコード
        """
        APIAssertions.assert_mcp_response(response)
        
        assert "error" in response, "エラーレスポンスにはerrorキーが必要です"
        error = response["error"]
        
        assert isinstance(error, dict), "errorは辞書型である必要があります"
        assert "code" in error, "エラーにはcodeが必要です"
        assert "message" in error, "エラーにはmessageが必要です"
        
        if expected_code is not None:
            assert error["code"] == expected_code, f"期待されるエラーコード: {expected_code}, 実際: {error['code']}"
    
    @staticmethod
    def assert_mcp_success(response: Dict[str, Any]):
        """MCP成功レスポンスをアサート
        
        Args:
            response: MCPレスポンス
        """
        APIAssertions.assert_mcp_response(response)
        
        assert "result" in response, "成功レスポンスにはresultキーが必要です"
        assert "error" not in response, "成功レスポンスにはerrorキーがあってはいけません"
    
    @staticmethod
    def assert_tool_call_result(result: Dict[str, Any], tool_name: str):
        """ツール呼び出し結果をアサート
        
        Args:
            result: ツール呼び出し結果
            tool_name: ツール名
        """
        assert isinstance(result, dict), "結果は辞書型である必要があります"
        
        # ツール固有の検証
        if tool_name == "calculate_income_tax":
            TaxAssertions.assert_income_tax_result(result)
        elif tool_name == "calculate_corporate_tax":
            TaxAssertions.assert_corporate_tax_result(result)
        elif tool_name in ["get_latest_tax_info", "search_legal_reference"]:
            assert isinstance(result, list), "検索結果はリスト型である必要があります"
            for item in result:
                assert isinstance(item, dict), "検索結果の各項目は辞書型である必要があります"
                assert "title" in item, "検索結果にはtitleが必要です"
                assert "content" in item, "検索結果にはcontentが必要です"


class SecurityAssertions:
    """セキュリティ関連のアサーション"""
    
    @staticmethod
    def assert_no_sensitive_data(data: Any, sensitive_patterns: List[str] = None):
        """機密データの漏洩がないことをアサート
        
        Args:
            data: チェック対象データ
            sensitive_patterns: 機密パターンリスト
        """
        if sensitive_patterns is None:
            sensitive_patterns = [
                "password", "secret", "key", "token", "credential",
                "パスワード", "秘密", "キー", "トークン", "認証情報"
            ]
        
        data_str = str(data).lower()
        for pattern in sensitive_patterns:
            assert pattern.lower() not in data_str, f"機密データパターン '{pattern}' が検出されました"
    
    @staticmethod
    def assert_input_sanitized(original_input: str, sanitized_input: str):
        """入力のサニタイズを確認
        
        Args:
            original_input: 元の入力
            sanitized_input: サニタイズ後の入力
        """
        # SQLインジェクション対策
        sql_patterns = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
        for pattern in sql_patterns:
            if pattern in original_input:
                assert pattern not in sanitized_input, f"SQLインジェクションパターン '{pattern}' がサニタイズされていません"
        
        # XSS対策
        xss_patterns = ["<script", "javascript:", "onload=", "onerror="]
        for pattern in xss_patterns:
            if pattern.lower() in original_input.lower():
                assert pattern.lower() not in sanitized_input.lower(), f"XSSパターン '{pattern}' がサニタイズされていません"
    
    @staticmethod
    def assert_rate_limit_respected(call_times: List[datetime], max_calls: int, time_window: int):
        """レート制限の遵守を確認
        
        Args:
            call_times: 呼び出し時刻のリスト
            max_calls: 最大呼び出し数
            time_window: 時間窓（秒）
        """
        if len(call_times) <= max_calls:
            return  # 制限内
        
        # 時間窓内の呼び出し数をチェック
        for i in range(len(call_times) - max_calls):
            window_start = call_times[i]
            window_end = call_times[i + max_calls]
            time_diff = (window_end - window_start).total_seconds()
            
            assert time_diff >= time_window, f"レート制限違反: {max_calls}回の呼び出しが{time_diff}秒で実行されました（制限: {time_window}秒）"


class PerformanceAssertions:
    """パフォーマンス関連のアサーション"""
    
    @staticmethod
    def assert_response_time(actual_time: float, max_time: float):
        """レスポンス時間をアサート
        
        Args:
            actual_time: 実際の時間（秒）
            max_time: 最大許容時間（秒）
        """
        assert actual_time <= max_time, f"レスポンス時間が制限を超えています: {actual_time:.3f}秒 > {max_time:.3f}秒"
    
    @staticmethod
    def assert_response_time_acceptable(performance_result: Dict[str, Any], max_duration: float):
        """パフォーマンス結果の応答時間をアサート
        
        Args:
            performance_result: パフォーマンス測定結果
            max_duration: 最大許容時間（秒）
        """
        duration = performance_result.get('duration', 0)
        assert duration <= max_duration, f"レスポンス時間が制限を超えています: {duration:.3f}秒 > {max_duration:.3f}秒"
    
    @staticmethod
    def assert_memory_usage(current_usage: int, max_usage: int):
        """メモリ使用量をアサート
        
        Args:
            current_usage: 現在の使用量（バイト）
            max_usage: 最大許容使用量（バイト）
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
        timeout: タイムアウト（秒）
        interval: チェック間隔（秒）
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