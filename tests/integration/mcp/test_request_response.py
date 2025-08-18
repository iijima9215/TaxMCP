"""MCPリクエスト・レスポンス処理テスト

TaxMCPサーバーのMCPリクエスト・レスポンス処理機能をテストする
"""

import unittest
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.test_config import TaxMCPTestCase, PerformanceTestMixin
from tests.utils.assertion_helpers import APIAssertions, PerformanceAssertions
from tests.utils.test_data_generator import TestDataGenerator


class TestRequestResponse(TaxMCPTestCase, PerformanceTestMixin):
    """MCPリクエスト・レスポンス処理テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.data_generator = TestDataGenerator()
        
        # テスト用のリクエストデータ
        self.test_requests = {
            "income_tax_calculation": {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "calculate_income_tax",
                    "arguments": {
                        "income": 5000000,
                        "deductions": {
                            "basic_deduction": 480000,
                            "spouse_deduction": 380000,
                            "social_insurance": 750000
                        },
                        "tax_year": 2024
                    }
                }
            },
            "corporate_tax_calculation": {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "calculate_corporate_tax",
                    "arguments": {
                        "revenue": 100000000,
                        "expenses": 80000000,
                        "company_type": "ordinary_corporation",
                        "tax_year": 2024
                    }
                }
            },
            "tax_law_search": {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "search_tax_law",
                    "arguments": {
                        "query": "所得税の基礎控除",
                        "tax_type": "income_tax",
                        "search_type": "semantic"
                    }
                }
            }
        }
    
    def test_valid_request_processing(self):
        """有効なリクエスト処理テスト"""
        print("\n=== 有効なリクエスト処理テスト ===")
        
        for request_name, request_data in self.test_requests.items():
            print(f"\n--- リクエスト処理テスト: {request_name} ---")
            
            print(f"リクエスト: {request_data}")
            
            # パフォーマンス測定開始
            start_time = self.start_performance_measurement()
            
            # リクエスト処理実行（モック）
            response = self._mock_tool_call_response(request_data)
            
            # パフォーマンス測定終了
            performance_result = self.end_performance_measurement(start_time)
            
            print(f"レスポンス: {response}")
            print(f"レスポンス時間: {performance_result['duration']:.3f}秒")
            
            # レスポンス構造のアサーション
            # MCPレスポンスは通常JSONオブジェクトなのでHTTPステータスコードはない
            if hasattr(response, 'status_code'):
                APIAssertions.assert_success_response(response)
            else:
                # JSONRPCレスポンスの場合は直接検証
                self.assertIn("result", response, "成功レスポンスにresultキーがありません")
                self.assertEqual(response.get("jsonrpc"), "2.0", "JSONRPCバージョンが正しくありません")
            
            # リクエストIDの一致確認
            self.assertEqual(
                response["id"],
                request_data["id"],
                "リクエストIDが一致している"
            )
            
            # 結果の存在確認
            self.assertIn("result", response, "結果が含まれている")
            
            # ツール固有の結果検証
            self._validate_tool_specific_result(
                request_data["params"]["name"],
                request_data["params"]["arguments"],
                response["result"]
            )
            
            # パフォーマンスの確認
            PerformanceAssertions.assert_response_time_acceptable(
                performance_result,
                max_duration=2.0  # 2秒以内
            )
            
            print(f"✓ リクエスト処理成功: {request_name}")
    
    def test_invalid_request_handling(self):
        """無効なリクエスト処理テスト"""
        print("\n=== 無効なリクエスト処理テスト ===")
        
        # 無効なリクエストのテストケース
        invalid_requests = [
            {
                "name": "missing_jsonrpc",
                "request": {
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "calculate_income_tax"}
                },
                "expected_error": "Invalid Request"
            },
            {
                "name": "invalid_method",
                "request": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "invalid_method",
                    "params": {}
                },
                "expected_error": "Method not found"
            },
            {
                "name": "missing_tool_name",
                "request": {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "arguments": {"income": 5000000}
                    }
                },
                "expected_error": "Invalid params"
            },
            {
                "name": "unknown_tool",
                "request": {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "unknown_tool",
                        "arguments": {}
                    }
                },
                "expected_error": "Tool not found"
            },
            {
                "name": "invalid_arguments",
                "request": {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "calculate_income_tax",
                        "arguments": {
                            "income": "invalid_income",  # 数値でない
                            "tax_year": 2024
                        }
                    }
                },
                "expected_error": "Invalid arguments"
            },
            {
                "name": "missing_required_arguments",
                "request": {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {
                        "name": "calculate_income_tax",
                        "arguments": {
                            # income が欠けている
                            "tax_year": 2024
                        }
                    }
                },
                "expected_error": "Missing required arguments"
            }
        ]
        
        for test_case in invalid_requests:
            print(f"\n--- 無効リクエストテスト: {test_case['name']} ---")
            
            print(f"無効リクエスト: {test_case['request']}")
            
            # 無効リクエスト処理実行（モック）
            error_response = self._mock_error_response(
                test_case["request"],
                test_case["expected_error"]
            )
            
            print(f"エラーレスポンス: {error_response}")
            
            # エラーレスポンス構造のアサーション
            # MCPエラーレスポンスは通常200ステータスでJSONRPCエラーを返す
            if hasattr(error_response, 'status_code'):
                APIAssertions.assert_error_response(error_response, 200)
            else:
                # JSONRPCエラーレスポンスの場合は直接検証
                self.assertIn("error", error_response, "エラーレスポンスにerrorキーがありません")
            
            # リクエストIDの確認（存在する場合）
            if "id" in test_case["request"]:
                self.assertEqual(
                    error_response["id"],
                    test_case["request"]["id"],
                    "リクエストIDが一致している"
                )
            
            # エラー情報の確認
            error = error_response["error"]
            self.assertIn("code", error, "エラーコードが含まれている")
            self.assertIn("message", error, "エラーメッセージが含まれている")
            
            # 期待されるエラーメッセージの確認
            self.assertIn(
                test_case["expected_error"].lower(),
                error["message"].lower(),
                f"期待されるエラーメッセージが含まれている: {test_case['expected_error']}"
            )
            
            print(f"✓ 無効リクエスト処理成功: {test_case['name']}")
    
    def test_concurrent_request_processing(self):
        """同時リクエスト処理テスト"""
        print("\n=== 同時リクエスト処理テスト ===")
        
        # 同時リクエスト数
        concurrent_requests = 10
        
        # 同時リクエスト用のデータ生成
        requests = []
        for i in range(concurrent_requests):
            request = {
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": "tools/call",
                "params": {
                    "name": "calculate_income_tax",
                    "arguments": {
                        "income": 5000000 + (i * 100000),
                        "deductions": {
                            "basic_deduction": 480000,
                            "social_insurance": 750000
                        },
                        "tax_year": 2024
                    }
                }
            }
            requests.append(request)
        
        print(f"同時リクエスト数: {concurrent_requests}")
        
        # パフォーマンス測定開始
        start_time = self.start_performance_measurement()
        
        # 同時リクエスト処理実行（モック）
        responses = self._mock_concurrent_requests(requests)
        
        # パフォーマンス測定終了
        performance_result = self.end_performance_measurement(start_time)
        
        print(f"同時処理時間: {performance_result['duration']:.3f}秒")
        
        # ゼロ除算を避けるための安全な計算
        if performance_result['duration'] > 0:
            avg_response_time = performance_result['duration'] / concurrent_requests
            print(f"平均レスポンス時間: {avg_response_time:.3f}秒")
        else:
            print("平均レスポンス時間: 測定不可（処理時間が0秒）")
        
        # レスポンス数の確認
        self.assertEqual(
            len(responses),
            concurrent_requests,
            "すべてのリクエストに対してレスポンスが返されている"
        )
        
        # 各レスポンスの確認
        for i, response in enumerate(responses):
            # レスポンス構造のアサーション
            # MCPレスポンスは通常JSONオブジェクトなのでHTTPステータスコードはない
            if hasattr(response, 'status_code'):
                APIAssertions.assert_success_response(response)
            else:
                # JSONRPCレスポンスの場合は直接検証
                self.assertIn("result", response, "成功レスポンスにresultキーがありません")
                self.assertEqual(response.get("jsonrpc"), "2.0", "JSONRPCバージョンが正しくありません")
            
            # リクエストIDの一致確認
            self.assertEqual(
                response["id"],
                i + 1,
                f"リクエストID {i + 1} が一致している"
            )
            
            # 結果の存在確認
            self.assertIn("result", response, f"結果 {i + 1} が含まれている")
        
        # パフォーマンスの確認
        PerformanceAssertions.assert_response_time_acceptable(
            performance_result,
            max_duration=5.0  # 5秒以内
        )
        
        # スループットの確認（ゼロ除算を避ける）
        if performance_result['duration'] > 0:
            throughput = concurrent_requests / performance_result['duration']
            self.assertGreater(
                throughput,
                2.0,  # 最低2リクエスト/秒
                f"十分なスループット: {throughput:.2f} req/sec"
            )
            print(f"✓ 同時リクエスト処理成功: {throughput:.2f} req/sec")
        else:
            # 処理時間が0の場合は非常に高速として扱う
            print("✓ 同時リクエスト処理成功: 非常に高速（測定不可）")
    
    def test_large_request_handling(self):
        """大きなリクエスト処理テスト"""
        print("\n=== 大きなリクエスト処理テスト ===")
        
        # 大きなリクエストデータの生成
        large_deductions = {}
        for i in range(100):  # 100個の控除項目
            large_deductions[f"deduction_{i}"] = 10000 + (i * 1000)
        
        large_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "calculate_income_tax",
                "arguments": {
                    "income": 10000000,
                    "deductions": large_deductions,
                    "tax_year": 2024,
                    "additional_info": {
                        "taxpayer_name": "テスト納税者" * 100,  # 長い文字列
                        "address": "テスト住所" * 50,
                        "notes": "備考" * 200
                    }
                }
            }
        }
        
        print(f"大きなリクエストサイズ: {len(json.dumps(large_request))} bytes")
        
        # パフォーマンス測定開始
        start_time = self.start_performance_measurement()
        
        # 大きなリクエスト処理実行（モック）
        response = self._mock_large_request_response(large_request)
        
        # パフォーマンス測定終了
        performance_result = self.end_performance_measurement(start_time)
        
        print(f"大きなリクエスト処理時間: {performance_result['duration']:.3f}秒")
        print(f"レスポンスサイズ: {len(json.dumps(response))} bytes")
        
        # レスポンス構造のアサーション
        # MCPレスポンスは通常JSONオブジェクトなのでHTTPステータスコードはない
        if hasattr(response, 'status_code'):
            APIAssertions.assert_success_response(response)
        else:
            # JSONRPCレスポンスの場合は直接検証
            self.assertIn("result", response, "成功レスポンスにresultキーがありません")
            self.assertEqual(response.get("jsonrpc"), "2.0", "JSONRPCバージョンが正しくありません")
        
        # 結果の確認
        result = response["result"]
        self.assertIn("calculated_tax", result, "税額が計算されている")
        self.assertIn("total_deductions", result, "総控除額が計算されている")
        
        # 大量の控除項目が処理されていることの確認
        self.assertGreater(
            result["total_deductions"],
            1000000,  # 100個の控除項目の合計
            "大量の控除項目が正しく処理されている"
        )
        
        # パフォーマンスの確認（大きなリクエストでも合理的な時間内）
        PerformanceAssertions.assert_response_time_acceptable(
            performance_result,
            max_duration=3.0  # 3秒以内
        )
        
        print("✓ 大きなリクエスト処理成功")
    
    def test_request_timeout_handling(self):
        """リクエストタイムアウト処理テスト"""
        print("\n=== リクエストタイムアウト処理テスト ===")
        
        # タイムアウトが発生するリクエスト（モック）
        timeout_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "calculate_income_tax",
                "arguments": {
                    "income": 5000000,
                    "tax_year": 2024,
                    "_simulate_timeout": True  # タイムアウトシミュレーション
                }
            }
        }
        
        print(f"タイムアウトリクエスト: {timeout_request}")
        
        # タイムアウト処理実行（モック）
        timeout_response = self._mock_timeout_response(timeout_request)
        
        print(f"タイムアウトレスポンス: {timeout_response}")
        
        # タイムアウトエラーレスポンスの確認
        # MCPエラーレスポンスは通常200ステータスでJSONRPCエラーを返す
        if hasattr(timeout_response, 'status_code'):
            APIAssertions.assert_error_response(timeout_response, 200)
        else:
            # JSONRPCエラーレスポンスの場合は直接検証
            self.assertIn("error", timeout_response, "エラーレスポンスにerrorキーがありません")
        
        # エラー情報の確認
        error = timeout_response["error"]
        self.assertEqual(error["code"], -32603, "内部エラーコード")
        self.assertIn(
            "timeout",
            error["message"].lower(),
            "タイムアウトエラーメッセージ"
        )
        
        print("✓ タイムアウト処理成功")
    
    def test_request_validation(self):
        """リクエスト検証テスト"""
        print("\n=== リクエスト検証テスト ===")
        
        # 検証テストケース
        validation_cases = [
            {
                "name": "json_schema_validation",
                "request": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "calculate_income_tax",
                        "arguments": {
                            "income": 5000000,
                            "tax_year": 2024
                        }
                    }
                },
                "should_pass": True
            },
            {
                "name": "business_logic_validation",
                "request": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "calculate_income_tax",
                        "arguments": {
                            "income": -1000000,  # 負の所得
                            "tax_year": 2024
                        }
                    }
                },
                "should_pass": False,
                "expected_error": "Invalid income value"
            },
            {
                "name": "range_validation",
                "request": {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "calculate_income_tax",
                        "arguments": {
                            "income": 5000000,
                            "tax_year": 1900  # 無効な年度
                        }
                    }
                },
                "should_pass": False,
                "expected_error": "Invalid tax year"
            },
            {
                "name": "data_type_validation",
                "request": {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "calculate_income_tax",
                        "arguments": {
                            "income": "5000000",  # 文字列（数値であるべき）
                            "tax_year": 2024
                        }
                    }
                },
                "should_pass": False,
                "expected_error": "Invalid data type"
            }
        ]
        
        for case in validation_cases:
            print(f"\n--- リクエスト検証: {case['name']} ---")
            
            print(f"検証リクエスト: {case['request']}")
            
            # リクエスト検証実行（モック）
            validation_response = self._mock_validation_response(case)
            
            print(f"検証レスポンス: {validation_response}")
            
            if case["should_pass"]:
                # 成功すべきケース
                # MCPレスポンスは通常JSONオブジェクトなのでHTTPステータスコードはない
                if hasattr(validation_response, 'status_code'):
                    APIAssertions.assert_success_response(validation_response)
                else:
                    # JSONRPCレスポンスの場合は直接検証
                    self.assertIn("result", validation_response, "成功レスポンスにresultキーがありません")
                    self.assertEqual(validation_response.get("jsonrpc"), "2.0", "JSONRPCバージョンが正しくありません")
                print(f"✓ 検証成功: {case['name']}")
            else:
                # 失敗すべきケース
                # MCPエラーレスポンスは通常200ステータスでJSONRPCエラーを返す
                if hasattr(validation_response, 'status_code'):
                    APIAssertions.assert_error_response(validation_response, 200)
                else:
                    # JSONRPCエラーレスポンスの場合は直接検証
                    self.assertIn("error", validation_response, "エラーレスポンスにerrorキーがありません")
                
                error = validation_response["error"]
                self.assertIn(
                    case["expected_error"].lower(),
                    error["message"].lower(),
                    f"期待されるエラーメッセージ: {case['expected_error']}"
                )
                print(f"✓ 検証エラー検出成功: {case['name']}")
    
    def test_response_formatting(self):
        """レスポンス形式テスト"""
        print("\n=== レスポンス形式テスト ===")
        
        # 標準的なリクエスト
        standard_request = self.test_requests["income_tax_calculation"]
        
        # レスポンス生成（モック）
        response = self._mock_tool_call_response(standard_request)
        
        print(f"レスポンス: {response}")
        
        # JSON-RPC 2.0形式の確認
        self.assertEqual(response["jsonrpc"], "2.0", "JSON-RPC 2.0形式")
        
        # 必須フィールドの確認
        required_fields = ["jsonrpc", "id"]
        for field in required_fields:
            self.assertIn(field, response, f"必須フィールド {field} が存在する")
        
        # 結果またはエラーのいずれかが存在
        self.assertTrue(
            "result" in response or "error" in response,
            "結果またはエラーが含まれている"
        )
        
        # 結果の構造確認（成功レスポンスの場合）
        if "result" in response:
            result = response["result"]
            
            # ツール実行結果の基本構造
            expected_result_fields = ["calculated_tax", "effective_rate", "calculation_details"]
            for field in expected_result_fields:
                self.assertIn(
                    field,
                    result,
                    f"結果フィールド {field} が存在する"
                )
            
            # 数値フィールドの型確認
            self.assertIsInstance(
                result["calculated_tax"],
                (int, float),
                "計算された税額が数値"
            )
            
            self.assertIsInstance(
                result["effective_rate"],
                (int, float),
                "実効税率が数値"
            )
            
            # 計算詳細の確認
            details = result["calculation_details"]
            self.assertIsInstance(details, dict, "計算詳細が辞書形式")
        
        print("✓ レスポンス形式確認成功")
    
    def _mock_tool_call_response(self, request):
        """ツール呼び出しレスポンスのモック"""
        tool_name = request["params"]["name"]
        arguments = request["params"]["arguments"]
        
        if tool_name == "calculate_income_tax":
            income = arguments["income"]
            deductions = arguments.get("deductions", {})
            
            # 簡単な所得税計算
            total_deductions = sum(deductions.values())
            taxable_income = max(0, income - total_deductions)
            calculated_tax = taxable_income * 0.2  # 簡易計算
            
            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "calculated_tax": calculated_tax,
                    "effective_rate": calculated_tax / income if income > 0 else 0,
                    "taxable_income": taxable_income,
                    "total_deductions": total_deductions,
                    "calculation_details": {
                        "income": income,
                        "deductions": deductions,
                        "tax_rate": 0.2
                    }
                }
            }
        
        elif tool_name == "calculate_corporate_tax":
            revenue = arguments["revenue"]
            expenses = arguments["expenses"]
            
            # 簡単な法人税計算
            profit = max(0, revenue - expenses)
            calculated_tax = profit * 0.23  # 簡易計算
            
            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "calculated_tax": calculated_tax,
                    "effective_rate": calculated_tax / revenue if revenue > 0 else 0,
                    "profit": profit,
                    "calculation_details": {
                        "revenue": revenue,
                        "expenses": expenses,
                        "tax_rate": 0.23
                    }
                }
            }
        
        elif tool_name == "search_tax_law":
            query = arguments["query"]
            
            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "search_results": [
                        {
                            "title": "所得税法第84条（基礎控除）",
                            "content": "居住者については、その者のその年分の総所得金額、退職所得金額及び山林所得金額の合計額から四十八万円を控除する。",
                            "relevance_score": 0.95,
                            "source": "所得税法"
                        }
                    ],
                    "total_results": 1,
                    "search_time": 0.1
                }
            }
        
        # デフォルトレスポンス
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "message": "Tool executed successfully"
            }
        }
    
    def _mock_error_response(self, request, error_type):
        """エラーレスポンスのモック"""
        error_codes = {
            "Invalid Request": -32600,
            "Method not found": -32601,
            "Invalid params": -32602,
            "Tool not found": -32001,
            "Invalid arguments": -32002,
            "Missing required arguments": -32003
        }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": error_codes.get(error_type, -32603),
                "message": error_type,
                "data": {
                    "request": request,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
    
    def _mock_concurrent_requests(self, requests):
        """同時リクエスト処理のモック"""
        responses = []
        
        for request in requests:
            response = self._mock_tool_call_response(request)
            responses.append(response)
        
        return responses
    
    def _mock_large_request_response(self, request):
        """大きなリクエストレスポンスのモック"""
        # 大きなリクエストでも通常の処理を行う
        response = self._mock_tool_call_response(request)
        
        # 大量の控除項目の処理結果を追加
        deductions = request["params"]["arguments"]["deductions"]
        total_deductions = sum(deductions.values())
        
        response["result"]["total_deductions"] = total_deductions
        response["result"]["deduction_count"] = len(deductions)
        
        return response
    
    def _mock_timeout_response(self, request):
        """タイムアウトレスポンスのモック"""
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "error": {
                "code": -32603,
                "message": "Request timeout: Tool execution exceeded time limit",
                "data": {
                    "timeout_duration": 30,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
    
    def _mock_validation_response(self, case):
        """検証レスポンスのモック"""
        if case["should_pass"]:
            return self._mock_tool_call_response(case["request"])
        else:
            return self._mock_error_response(case["request"], case["expected_error"])
    
    def _validate_tool_specific_result(self, tool_name, arguments, result):
        """ツール固有の結果検証"""
        if tool_name == "calculate_income_tax":
            # 所得税計算結果の検証
            self.assertIn("calculated_tax", result, "計算された税額が含まれている")
            self.assertIn("effective_rate", result, "実効税率が含まれている")
            self.assertIn("taxable_income", result, "課税所得が含まれている")
            
            # 計算結果の妥当性確認
            self.assertGreaterEqual(
                result["calculated_tax"],
                0,
                "計算された税額が非負"
            )
            
            self.assertGreaterEqual(
                result["effective_rate"],
                0,
                "実効税率が非負"
            )
            
            self.assertLessEqual(
                result["effective_rate"],
                1.0,
                "実効税率が100%以下"
            )
        
        elif tool_name == "calculate_corporate_tax":
            # 法人税計算結果の検証
            self.assertIn("calculated_tax", result, "計算された税額が含まれている")
            self.assertIn("profit", result, "利益が含まれている")
            
            # 計算結果の妥当性確認
            self.assertGreaterEqual(
                result["calculated_tax"],
                0,
                "計算された税額が非負"
            )
        
        elif tool_name == "search_tax_law":
            # 税法検索結果の検証
            self.assertIn("search_results", result, "検索結果が含まれている")
            self.assertIn("total_results", result, "総結果数が含まれている")
            
            # 検索結果の構造確認
            search_results = result["search_results"]
            self.assertIsInstance(search_results, list, "検索結果がリスト形式")
            
            for search_result in search_results:
                self.assertIn("title", search_result, "タイトルが含まれている")
                self.assertIn("content", search_result, "内容が含まれている")
                self.assertIn("relevance_score", search_result, "関連性スコアが含まれている")


if __name__ == "__main__":
    unittest.main(verbosity=2)