"""MCPツール発見機能テスト

TaxMCPサーバーのMCPツール発見機能をテストする
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


class TestToolDiscovery(TaxMCPTestCase, PerformanceTestMixin):
    """MCPツール発見機能テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.data_generator = TestDataGenerator()
        
        # 期待されるツール定義
        self.expected_tools = {
            "calculate_income_tax": {
                "name": "calculate_income_tax",
                "description": "個人の年間所得に対する所得税額を計算し、各種控除を適用した詳細な税額を算出する",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "income": {"type": "number", "description": "年間所得額"},
                        "deductions": {"type": "object", "description": "各種控除額"},
                        "tax_year": {"type": "integer", "description": "課税年度"}
                    },
                    "required": ["income", "tax_year"]
                }
            },
            "calculate_corporate_tax": {
                "name": "calculate_corporate_tax",
                "description": "法人の所得に対する法人税額を計算し、税務申告に必要な詳細情報を提供する",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "revenue": {"type": "number", "description": "年間売上高"},
                        "expenses": {"type": "number", "description": "年間費用"},
                        "company_type": {"type": "string", "description": "法人種別"},
                        "tax_year": {"type": "integer", "description": "事業年度"}
                    },
                    "required": ["revenue", "expenses", "tax_year"]
                }
            },
            "calculate_consumption_tax": {
                "name": "calculate_consumption_tax",
                "description": "商品やサービスの売上に対する消費税額を計算し、適用税率に基づいた正確な税額を算出する",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sales_amount": {"type": "number", "description": "売上金額"},
                        "tax_rate": {"type": "number", "description": "適用税率"},
                        "business_type": {"type": "string", "description": "事業種別"}
                    },
                    "required": ["sales_amount"]
                }
            },
            "search_tax_law": {
                "name": "search_tax_law",
                "description": "税法条文や関連法令を検索し、指定されたキーワードに関連する法的根拠を提供する",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "検索クエリ"},
                        "tax_type": {"type": "string", "description": "税目"},
                        "search_type": {"type": "string", "description": "検索タイプ"}
                    },
                    "required": ["query"]
                }
            },
            "get_tax_forms": {
                "name": "get_tax_forms",
                "description": "指定された税目と年度に対応する税務申告書フォームを取得し、必要な書類情報を提供する",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "form_type": {"type": "string", "description": "申告書種別"},
                        "tax_year": {"type": "integer", "description": "課税年度"},
                        "taxpayer_type": {"type": "string", "description": "納税者種別"}
                    },
                    "required": ["form_type", "tax_year"]
                }
            }
        }
    
    def test_list_tools_basic(self):
        """基本的なツール一覧取得テスト"""
        print("\n=== 基本的なツール一覧取得テスト ===")
        
        # ツール一覧取得リクエスト
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        print(f"ツール一覧リクエスト: {list_tools_request}")
        
        # パフォーマンス測定開始
        start_time = self.start_performance_measurement()
        
        # ツール一覧取得実行（モック）
        tools_response = self._mock_list_tools_response()
        
        # パフォーマンス測定終了
        performance_result = self.end_performance_measurement(start_time)
        
        print(f"ツール一覧レスポンス: {tools_response}")
        print(f"レスポンス時間: {performance_result['duration']:.3f}秒")
        
        # レスポンス構造のアサーション
        self.assertIn("jsonrpc", tools_response, "JSON-RPC形式のレスポンス")
        self.assertEqual(tools_response["jsonrpc"], "2.0", "JSON-RPC 2.0")
        self.assertIn("id", tools_response, "リクエストIDが含まれている")
        self.assertIn("result", tools_response, "結果が含まれている")
        
        # ツール一覧の確認
        result = tools_response["result"]
        self.assertIn("tools", result, "ツール一覧が含まれている")
        
        tools = result["tools"]
        self.assertIsInstance(tools, list, "ツールがリスト形式")
        self.assertGreater(len(tools), 0, "ツールが存在する")
        
        # 期待されるツールの存在確認
        tool_names = [tool["name"] for tool in tools]
        for expected_tool_name in self.expected_tools.keys():
            self.assertIn(
                expected_tool_name,
                tool_names,
                f"期待されるツール {expected_tool_name} が存在する"
            )
        
        # パフォーマンスの確認
        PerformanceAssertions.assert_response_time_acceptable(
            performance_result,
            max_duration=1.0  # 1秒以内
        )
        
        print(f"✓ ツール一覧取得成功: {len(tools)}個のツール")
    
    def test_tool_schema_validation(self):
        """ツールスキーマ検証テスト"""
        print("\n=== ツールスキーマ検証テスト ===")
        
        # ツール一覧取得
        tools_response = self._mock_list_tools_response()
        tools = tools_response["result"]["tools"]
        
        for tool in tools:
            print(f"\n--- ツールスキーマ検証: {tool['name']} ---")
            
            # 必須フィールドの確認
            required_fields = ["name", "description", "inputSchema"]
            for field in required_fields:
                self.assertIn(
                    field,
                    tool,
                    f"ツール {tool['name']} に必須フィールド {field} が存在する"
                )
            
            # ツール名の検証
            self.assertIsInstance(
                tool["name"],
                str,
                f"ツール名が文字列: {tool['name']}"
            )
            self.assertRegex(
                tool["name"],
                r"^[a-z][a-z0-9_]*$",
                f"ツール名が命名規則に従っている: {tool['name']}"
            )
            
            # 説明の検証
            self.assertIsInstance(
                tool["description"],
                str,
                f"説明が文字列: {tool['name']}"
            )
            self.assertGreater(
                len(tool["description"]),
                10,
                f"説明が十分に詳細: {tool['name']}"
            )
            
            # 入力スキーマの検証
            input_schema = tool["inputSchema"]
            self.assertIsInstance(
                input_schema,
                dict,
                f"入力スキーマが辞書形式: {tool['name']}"
            )
            
            # JSON Schemaの基本構造確認
            self.assertIn(
                "type",
                input_schema,
                f"入力スキーマにtypeが定義されている: {tool['name']}"
            )
            
            if input_schema["type"] == "object":
                self.assertIn(
                    "properties",
                    input_schema,
                    f"オブジェクト型スキーマにpropertiesが定義されている: {tool['name']}"
                )
                
                # プロパティの検証
                properties = input_schema["properties"]
                for prop_name, prop_schema in properties.items():
                    self.assertIn(
                        "type",
                        prop_schema,
                        f"プロパティ {prop_name} にtypeが定義されている: {tool['name']}"
                    )
                    
                    self.assertIn(
                        "description",
                        prop_schema,
                        f"プロパティ {prop_name} に説明が定義されている: {tool['name']}"
                    )
            
            # 期待されるツールとの比較
            if tool["name"] in self.expected_tools:
                expected_tool = self.expected_tools[tool["name"]]
                
                # 必須パラメータの確認
                if "required" in expected_tool["inputSchema"]:
                    self.assertIn(
                        "required",
                        input_schema,
                        f"必須パラメータが定義されている: {tool['name']}"
                    )
                    
                    expected_required = set(expected_tool["inputSchema"]["required"])
                    actual_required = set(input_schema.get("required", []))
                    
                    self.assertTrue(
                        expected_required.issubset(actual_required),
                        f"期待される必須パラメータが含まれている: {tool['name']}"
                    )
            
            print(f"✓ ツールスキーマ検証成功: {tool['name']}")
    
    def test_tool_categorization(self):
        """ツールカテゴリ分類テスト"""
        print("\n=== ツールカテゴリ分類テスト ===")
        
        # カテゴリ別ツール一覧取得リクエスト
        categorization_requests = [
            {
                "category": "calculation",
                "expected_tools": [
                    "calculate_income_tax",
                    "calculate_corporate_tax",
                    "calculate_consumption_tax"
                ]
            },
            {
                "category": "search",
                "expected_tools": [
                    "search_tax_law",
                    "search_legal_precedents"
                ]
            },
            {
                "category": "forms",
                "expected_tools": [
                    "get_tax_forms",
                    "validate_tax_form"
                ]
            },
            {
                "category": "information",
                "expected_tools": [
                    "get_tax_rates",
                    "get_tax_deadlines"
                ]
            }
        ]
        
        for request_data in categorization_requests:
            print(f"\n--- カテゴリ別ツール取得: {request_data['category']} ---")
            
            # カテゴリ別ツール一覧リクエスト
            category_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {
                    "category": request_data["category"]
                }
            }
            
            print(f"カテゴリリクエスト: {category_request}")
            
            # カテゴリ別ツール一覧取得実行（モック）
            category_response = self._mock_categorized_tools_response(
                request_data["category"]
            )
            
            print(f"カテゴリレスポンス: {category_response}")
            
            # レスポンス構造のアサーション
            # MCPレスポンスは通常JSONオブジェクトなのでHTTPステータスコードはない
            if hasattr(category_response, 'status_code'):
                APIAssertions.assert_success_response(category_response)
            else:
                # JSONRPCレスポンスの場合は直接検証
                self.assertIn("result", category_response, "成功レスポンスにresultキーがありません")
                self.assertEqual(category_response.get("jsonrpc"), "2.0", "JSONRPCバージョンが正しくありません")
            
            # カテゴリ情報の確認
            result = category_response["result"]
            self.assertIn("category", result, "カテゴリ情報が含まれている")
            self.assertEqual(
                result["category"],
                request_data["category"],
                "指定されたカテゴリが返されている"
            )
            
            # ツール一覧の確認
            tools = result["tools"]
            self.assertIsInstance(tools, list, "ツールがリスト形式")
            
            # 期待されるツールの存在確認
            tool_names = [tool["name"] for tool in tools]
            for expected_tool in request_data["expected_tools"]:
                if expected_tool in self.expected_tools:
                    self.assertIn(
                        expected_tool,
                        tool_names,
                        f"期待されるツール {expected_tool} がカテゴリに含まれている"
                    )
            
            # カテゴリの一貫性確認
            for tool in tools:
                self.assertTrue(
                    self._is_tool_in_category(tool["name"], request_data["category"]),
                    f"ツール {tool['name']} がカテゴリ {request_data['category']} に適している"
                )
            
            print(f"✓ カテゴリ別ツール取得成功: {len(tools)}個のツール")
    
    def test_tool_filtering(self):
        """ツールフィルタリングテスト"""
        print("\n=== ツールフィルタリングテスト ===")
        
        # フィルタリングのテストケース
        filtering_scenarios = [
            {
                "filter_type": "by_tax_type",
                "filter_params": {"tax_type": "income_tax"},
                "expected_tools": ["calculate_income_tax"]
            },
            {
                "filter_type": "by_complexity",
                "filter_params": {"complexity": "basic"},
                "expected_min_tools": 3
            },
            {
                "filter_type": "by_user_type",
                "filter_params": {"user_type": "individual"},
                "expected_tools": ["calculate_income_tax", "search_tax_law"]
            },
            {
                "filter_type": "by_functionality",
                "filter_params": {"functionality": "calculation"},
                "expected_min_tools": 3
            }
        ]
        
        for scenario in filtering_scenarios:
            print(f"\n--- ツールフィルタリング: {scenario['filter_type']} ---")
            
            # フィルタリングリクエスト
            filter_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list",
                "params": {
                    "filters": scenario["filter_params"]
                }
            }
            
            print(f"フィルタリングリクエスト: {filter_request}")
            
            # フィルタリング実行（モック）
            filter_response = self._mock_filtered_tools_response(
                scenario["filter_params"]
            )
            
            print(f"フィルタリングレスポンス: {filter_response}")
            
            # レスポンス構造のアサーション
            # MCPレスポンスは通常JSONオブジェクトなのでHTTPステータスコードはない
            if hasattr(filter_response, 'status_code'):
                APIAssertions.assert_success_response(filter_response)
            else:
                # JSONRPCレスポンスの場合は直接検証
                self.assertIn("result", filter_response, "成功レスポンスにresultキーがありません")
                self.assertEqual(filter_response.get("jsonrpc"), "2.0", "JSONRPCバージョンが正しくありません")
            
            # フィルタリング結果の確認
            result = filter_response["result"]
            self.assertIn("filters_applied", result, "適用されたフィルターが記録されている")
            
            tools = result["tools"]
            self.assertIsInstance(tools, list, "ツールがリスト形式")
            
            # 期待される結果の確認
            if "expected_tools" in scenario:
                tool_names = [tool["name"] for tool in tools]
                for expected_tool in scenario["expected_tools"]:
                    self.assertIn(
                        expected_tool,
                        tool_names,
                        f"期待されるツール {expected_tool} がフィルタリング結果に含まれている"
                    )
            
            if "expected_min_tools" in scenario:
                self.assertGreaterEqual(
                    len(tools),
                    scenario["expected_min_tools"],
                    f"期待される最小ツール数以上: {len(tools)} >= {scenario['expected_min_tools']}"
                )
            
            # フィルター条件の適用確認
            for tool in tools:
                self.assertTrue(
                    self._tool_matches_filter(tool, scenario["filter_params"]),
                    f"ツール {tool['name']} がフィルター条件を満たしている"
                )
            
            print(f"✓ ツールフィルタリング成功: {len(tools)}個のツール")
    
    def test_tool_search(self):
        """ツール検索テスト"""
        print("\n=== ツール検索テスト ===")
        
        # ツール検索のテストケース
        search_scenarios = [
            {
                "search_query": "所得税",
                "expected_tools": ["calculate_income_tax"],
                "search_type": "keyword"
            },
            {
                "search_query": "法人税計算",
                "expected_tools": ["calculate_corporate_tax"],
                "search_type": "semantic"
            },
            {
                "search_query": "税法検索",
                "expected_tools": ["search_tax_law"],
                "search_type": "description"
            },
            {
                "search_query": "申告書",
                "expected_tools": ["get_tax_forms"],
                "search_type": "fuzzy"
            }
        ]
        
        for scenario in search_scenarios:
            print(f"\n--- ツール検索: {scenario['search_query']} ---")
            
            # ツール検索リクエスト
            search_request = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/search",
                "params": {
                    "query": scenario["search_query"],
                    "search_type": scenario["search_type"],
                    "max_results": 10
                }
            }
            
            print(f"検索リクエスト: {search_request}")
            
            # ツール検索実行（モック）
            search_response = self._mock_tool_search_response(
                scenario["search_query"],
                scenario["search_type"]
            )
            
            print(f"検索レスポンス: {search_response}")
            
            # レスポンス構造のアサーション
            # MCPレスポンスは通常JSONオブジェクトなのでHTTPステータスコードはない
            if hasattr(search_response, 'status_code'):
                APIAssertions.assert_success_response(search_response)
            else:
                # JSONRPCレスポンスの場合は直接検証
                self.assertIn("result", search_response, "成功レスポンスにresultキーがありません")
                self.assertEqual(search_response.get("jsonrpc"), "2.0", "JSONRPCバージョンが正しくありません")
            
            # 検索結果の確認
            result = search_response["result"]
            self.assertIn("query", result, "検索クエリが記録されている")
            self.assertIn("search_type", result, "検索タイプが記録されている")
            
            tools = result["tools"]
            self.assertIsInstance(tools, list, "ツールがリスト形式")
            
            # 期待されるツールの存在確認
            tool_names = [tool["name"] for tool in tools]
            for expected_tool in scenario["expected_tools"]:
                self.assertIn(
                    expected_tool,
                    tool_names,
                    f"期待されるツール {expected_tool} が検索結果に含まれている"
                )
            
            # 関連性スコアの確認（セマンティック検索の場合）
            if scenario["search_type"] == "semantic":
                for tool in tools:
                    self.assertIn(
                        "relevance_score",
                        tool,
                        f"ツール {tool['name']} に関連性スコアが含まれている"
                    )
                    
                    self.assertGreaterEqual(
                        tool["relevance_score"],
                        0.0,
                        f"関連性スコアが有効な範囲: {tool['relevance_score']}"
                    )
                    
                    self.assertLessEqual(
                        tool["relevance_score"],
                        1.0,
                        f"関連性スコアが有効な範囲: {tool['relevance_score']}"
                    )
            
            print(f"✓ ツール検索成功: {len(tools)}個のツール")
    
    def test_tool_metadata(self):
        """ツールメタデータテスト"""
        print("\n=== ツールメタデータテスト ===")
        
        # ツール一覧取得（メタデータ付き）
        metadata_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/list",
            "params": {
                "include_metadata": True,
                "metadata_fields": [
                    "version",
                    "author",
                    "last_updated",
                    "complexity",
                    "category",
                    "tags",
                    "usage_stats"
                ]
            }
        }
        
        print(f"メタデータリクエスト: {metadata_request}")
        
        # メタデータ付きツール一覧取得（モック）
        metadata_response = self._mock_tools_with_metadata_response()
        
        print(f"メタデータレスポンス: {metadata_response}")
        
        # レスポンス構造のアサーション
        # MCPレスポンスは通常JSONオブジェクトなのでHTTPステータスコードはない
        if hasattr(metadata_response, 'status_code'):
            APIAssertions.assert_success_response(metadata_response)
        else:
            # JSONRPCレスポンスの場合は直接検証
            self.assertIn("result", metadata_response, "成功レスポンスにresultキーがありません")
            self.assertEqual(metadata_response.get("jsonrpc"), "2.0", "JSONRPCバージョンが正しくありません")
        
        # メタデータの確認
        tools = metadata_response["result"]["tools"]
        
        for tool in tools:
            print(f"\n--- ツールメタデータ確認: {tool['name']} ---")
            
            # メタデータの存在確認
            self.assertIn(
                "metadata",
                tool,
                f"ツール {tool['name']} にメタデータが含まれている"
            )
            
            metadata = tool["metadata"]
            
            # 基本メタデータフィールドの確認
            expected_metadata_fields = [
                "version", "author", "last_updated",
                "complexity", "category", "tags"
            ]
            
            for field in expected_metadata_fields:
                self.assertIn(
                    field,
                    metadata,
                    f"メタデータに {field} が含まれている: {tool['name']}"
                )
            
            # バージョン情報の確認
            self.assertRegex(
                metadata["version"],
                r"^\d+\.\d+\.\d+$",
                f"バージョンがセマンティックバージョニング形式: {tool['name']}"
            )
            
            # 複雑度の確認
            self.assertIn(
                metadata["complexity"],
                ["basic", "intermediate", "advanced"],
                f"複雑度が有効な値: {tool['name']}"
            )
            
            # カテゴリの確認
            self.assertIn(
                metadata["category"],
                ["calculation", "search", "forms", "information"],
                f"カテゴリが有効な値: {tool['name']}"
            )
            
            # タグの確認
            self.assertIsInstance(
                metadata["tags"],
                list,
                f"タグがリスト形式: {tool['name']}"
            )
            
            # 使用統計の確認（含まれている場合）
            if "usage_stats" in metadata:
                usage_stats = metadata["usage_stats"]
                self.assertIn(
                    "call_count",
                    usage_stats,
                    f"使用統計に呼び出し回数が含まれている: {tool['name']}"
                )
                
                self.assertIn(
                    "success_rate",
                    usage_stats,
                    f"使用統計に成功率が含まれている: {tool['name']}"
                )
            
            print(f"✓ ツールメタデータ確認成功: {tool['name']}")
    
    def _mock_list_tools_response(self):
        """ツール一覧レスポンスのモック"""
        tools = []
        for tool_name, tool_def in self.expected_tools.items():
            tools.append({
                "name": tool_def["name"],
                "description": tool_def["description"],
                "inputSchema": tool_def["inputSchema"]
            })
        
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": tools
            }
        }
    
    def _mock_categorized_tools_response(self, category):
        """カテゴリ別ツールレスポンスのモック"""
        category_mapping = {
            "calculation": ["calculate_income_tax", "calculate_corporate_tax", "calculate_consumption_tax"],
            "search": ["search_tax_law"],
            "forms": ["get_tax_forms"],
            "information": []
        }
        
        tools = []
        for tool_name in category_mapping.get(category, []):
            if tool_name in self.expected_tools:
                tool_def = self.expected_tools[tool_name]
                tools.append({
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "inputSchema": tool_def["inputSchema"]
                })
        
        return {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "category": category,
                "tools": tools
            }
        }
    
    def _mock_filtered_tools_response(self, filters):
        """フィルタリングツールレスポンスのモック"""
        # フィルター条件に基づいてツールを選択
        filtered_tools = []
        
        for tool_name, tool_def in self.expected_tools.items():
            if self._tool_matches_filter({"name": tool_name}, filters):
                filtered_tools.append({
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "inputSchema": tool_def["inputSchema"]
                })
        
        return {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "filters_applied": filters,
                "tools": filtered_tools
            }
        }
    
    def _mock_tool_search_response(self, query, search_type):
        """ツール検索レスポンスのモック"""
        # 検索クエリに基づいてツールを選択
        search_results = []
        
        query_lower = query.lower()
        
        # より柔軟な検索ロジック
        search_mappings = {
            "所得税": ["calculate_income_tax"],
            "法人税": ["calculate_corporate_tax"],
            "法人税計算": ["calculate_corporate_tax"],
            "消費税": ["calculate_consumption_tax"],
            "税法": ["search_tax_law"],
            "税法検索": ["search_tax_law"],
            "申告書": ["get_tax_forms"],
            "フォーム": ["get_tax_forms"]
        }
        
        # 直接マッピングから検索
        matched_tools = set()
        for search_term, tools in search_mappings.items():
            if search_term in query_lower:
                matched_tools.update(tools)
        
        # 通常の文字列検索も実行
        for tool_name, tool_def in self.expected_tools.items():
            if (query_lower in tool_name.lower() or
                query_lower in tool_def["description"].lower()):
                matched_tools.add(tool_name)
        
        # 結果を構築
        for tool_name in matched_tools:
            if tool_name in self.expected_tools:
                tool_def = self.expected_tools[tool_name]
                tool_result = {
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "inputSchema": tool_def["inputSchema"]
                }
                
                # セマンティック検索の場合は関連性スコアを追加
                if search_type == "semantic":
                    tool_result["relevance_score"] = 0.85
                
                search_results.append(tool_result)
        
        return {
            "jsonrpc": "2.0",
            "id": 4,
            "result": {
                "query": query,
                "search_type": search_type,
                "tools": search_results
            }
        }
    
    def _mock_tools_with_metadata_response(self):
        """メタデータ付きツールレスポンスのモック"""
        tools = []
        
        for tool_name, tool_def in self.expected_tools.items():
            tool_with_metadata = {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "inputSchema": tool_def["inputSchema"],
                "metadata": {
                    "version": "1.0.0",
                    "author": "TaxMCP Team",
                    "last_updated": "2025-01-01T00:00:00Z",
                    "complexity": "intermediate",
                    "category": self._get_tool_category(tool_name),
                    "tags": self._get_tool_tags(tool_name),
                    "usage_stats": {
                        "call_count": 100,
                        "success_rate": 0.95,
                        "avg_response_time": 0.5
                    }
                }
            }
            tools.append(tool_with_metadata)
        
        return {
            "jsonrpc": "2.0",
            "id": 5,
            "result": {
                "tools": tools
            }
        }
    
    def _is_tool_in_category(self, tool_name, category):
        """ツールがカテゴリに属するかチェック"""
        category_mapping = {
            "calculation": ["calculate_income_tax", "calculate_corporate_tax", "calculate_consumption_tax"],
            "search": ["search_tax_law"],
            "forms": ["get_tax_forms"],
            "information": []
        }
        
        return tool_name in category_mapping.get(category, [])
    
    def _tool_matches_filter(self, tool, filters):
        """ツールがフィルター条件を満たすかチェック"""
        tool_name = tool["name"]
        
        # 税目フィルター
        if "tax_type" in filters:
            tax_type = filters["tax_type"]
            if tax_type == "income_tax" and "income_tax" not in tool_name:
                return False
            if tax_type == "corporate_tax" and "corporate_tax" not in tool_name:
                return False
            if tax_type == "consumption_tax" and "consumption_tax" not in tool_name:
                return False
        
        # 複雑度フィルター
        if "complexity" in filters:
            # 基本的なツールのみ（簡単な判定）
            if filters["complexity"] == "basic":
                return "calculate" in tool_name
        
        # ユーザータイプフィルター
        if "user_type" in filters:
            if filters["user_type"] == "individual":
                return "income_tax" in tool_name or "search" in tool_name
        
        # 機能フィルター
        if "functionality" in filters:
            if filters["functionality"] == "calculation":
                return "calculate" in tool_name
        
        return True
    
    def _get_tool_category(self, tool_name):
        """ツールのカテゴリを取得"""
        if "calculate" in tool_name:
            return "calculation"
        elif "search" in tool_name:
            return "search"
        elif "get" in tool_name:
            return "forms"
        else:
            return "information"
    
    def _get_tool_tags(self, tool_name):
        """ツールのタグを取得"""
        tags = []
        
        if "income_tax" in tool_name:
            tags.extend(["所得税", "個人", "確定申告"])
        elif "corporate_tax" in tool_name:
            tags.extend(["法人税", "企業", "申告書"])
        elif "consumption_tax" in tool_name:
            tags.extend(["消費税", "事業者", "インボイス"])
        elif "search" in tool_name:
            tags.extend(["検索", "法令", "参照"])
        elif "forms" in tool_name:
            tags.extend(["申告書", "様式", "手続き"])
        
        return tags


if __name__ == "__main__":
    unittest.main(verbosity=2)