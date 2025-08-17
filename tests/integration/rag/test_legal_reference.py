"""法令参照RAG統合テスト

TaxMCPサーバーの法令参照RAG機能をテストする
"""

import unittest
import sys
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.test_config import TaxMCPTestCase, PerformanceTestMixin
from tests.utils.assertion_helpers import APIAssertions, PerformanceAssertions
from tests.utils.mock_external_apis import MockRAGIntegration
from tests.utils.test_data_generator import TestDataGenerator


class TestLegalReference(TaxMCPTestCase, PerformanceTestMixin):
    """法令参照RAG統合テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.rag_integration = MockRAGIntegration()
        self.data_generator = TestDataGenerator()
    
    def test_income_tax_law_search(self):
        """所得税法検索テスト"""
        print("\n=== 所得税法検索テスト ===")
        
        # 所得税法に関する検索クエリ
        income_tax_queries = [
            {
                "query": "所得税の基礎控除額",
                "tax_year": 2025,
                "expected_articles": ["所得税法第84条", "所得税法施行令第217条"]
            },
            {
                "query": "給与所得控除の計算方法",
                "tax_year": 2025,
                "expected_articles": ["所得税法第28条", "所得税法施行令第63条"]
            },
            {
                "query": "配偶者控除の適用要件",
                "tax_year": 2025,
                "expected_articles": ["所得税法第83条", "所得税法施行令第216条"]
            },
            {
                "query": "住宅借入金等特別控除",
                "tax_year": 2025,
                "expected_articles": ["租税特別措置法第41条"]
            }
        ]
        
        for query_data in income_tax_queries:
            print(f"\n--- 検索クエリ: {query_data['query']} ---")
            
            # 法令検索リクエスト
            search_request = {
                "method": "search_legal_reference",
                "params": {
                    "query": query_data["query"],
                    "tax_category": "income_tax",
                    "tax_year": query_data["tax_year"],
                    "search_type": "comprehensive",
                    "max_results": 10
                }
            }
            
            print(f"検索リクエスト: {search_request}")
            
            # RAG検索実行
            search_result = self.rag_integration.search_legal_reference(
                search_request["params"]
            )
            
            print(f"検索結果: {search_result}")
            
            # 検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "法令検索が成功している")
            self.assertGreater(
                len(search_result["results"]),
                0,
                "検索結果が返されている"
            )
            
            # 期待される条文の確認
            found_articles = [result["article"] for result in search_result["results"]]
            for expected_article in query_data["expected_articles"]:
                self.assertIn(
                    expected_article,
                    found_articles,
                    f"期待される条文 {expected_article} が見つかっている"
                )
            
            # 検索結果の品質確認
            for result in search_result["results"]:
                self.assertIn("article", result, "条文番号が含まれている")
                self.assertIn("content", result, "条文内容が含まれている")
                self.assertIn("relevance_score", result, "関連度スコアが含まれている")
                self.assertGreaterEqual(
                    result["relevance_score"],
                    0.5,
                    "関連度スコアが十分に高い"
                )
            
            print(f"✓ {query_data['query']} 検索成功")
    
    def test_corporate_tax_law_search(self):
        """法人税法検索テスト"""
        print("\n=== 法人税法検索テスト ===")
        
        # 法人税法に関する検索クエリ
        corporate_tax_queries = [
            {
                "query": "法人税の税率",
                "tax_year": 2025,
                "expected_articles": ["法人税法第66条"]
            },
            {
                "query": "減価償却の方法",
                "tax_year": 2025,
                "expected_articles": ["法人税法第31条", "法人税法施行令第48条"]
            },
            {
                "query": "欠損金の繰越控除",
                "tax_year": 2025,
                "expected_articles": ["法人税法第57条"]
            },
            {
                "query": "中小企業の軽減税率",
                "tax_year": 2025,
                "expected_articles": ["租税特別措置法第42条の3の2"]
            }
        ]
        
        for query_data in corporate_tax_queries:
            print(f"\n--- 検索クエリ: {query_data['query']} ---")
            
            # 法令検索リクエスト
            search_request = {
                "method": "search_legal_reference",
                "params": {
                    "query": query_data["query"],
                    "tax_category": "corporate_tax",
                    "tax_year": query_data["tax_year"],
                    "search_type": "detailed",
                    "include_related": True
                }
            }
            
            print(f"検索リクエスト: {search_request}")
            
            # RAG検索実行
            search_result = self.rag_integration.search_legal_reference(
                search_request["params"]
            )
            
            print(f"検索結果: {search_result}")
            
            # 検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "法人税法検索が成功している")
            
            # 関連条文の確認
            if search_request["params"]["include_related"]:
                self.assertIn(
                    "related_articles",
                    search_result,
                    "関連条文が含まれている"
                )
            
            print(f"✓ {query_data['query']} 検索成功")
    
    def test_consumption_tax_law_search(self):
        """消費税法検索テスト"""
        print("\n=== 消費税法検索テスト ===")
        
        # 消費税法に関する検索クエリ
        consumption_tax_queries = [
            {
                "query": "消費税の税率",
                "tax_year": 2025,
                "expected_articles": ["消費税法第29条"]
            },
            {
                "query": "軽減税率の対象品目",
                "tax_year": 2025,
                "expected_articles": ["消費税法附則第34条"]
            },
            {
                "query": "免税事業者の判定",
                "tax_year": 2025,
                "expected_articles": ["消費税法第9条"]
            },
            {
                "query": "インボイス制度",
                "tax_year": 2025,
                "expected_articles": ["消費税法第30条"]
            }
        ]
        
        for query_data in consumption_tax_queries:
            print(f"\n--- 検索クエリ: {query_data['query']} ---")
            
            # 法令検索リクエスト
            search_request = {
                "method": "search_legal_reference",
                "params": {
                    "query": query_data["query"],
                    "tax_category": "consumption_tax",
                    "tax_year": query_data["tax_year"],
                    "search_type": "practical",
                    "include_examples": True
                }
            }
            
            print(f"検索リクエスト: {search_request}")
            
            # RAG検索実行
            search_result = self.rag_integration.search_legal_reference(
                search_request["params"]
            )
            
            print(f"検索結果: {search_result}")
            
            # 検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "消費税法検索が成功している")
            
            # 実例の確認
            if search_request["params"]["include_examples"]:
                self.assertIn(
                    "practical_examples",
                    search_result,
                    "実例が含まれている"
                )
            
            print(f"✓ {query_data['query']} 検索成功")
    
    def test_cross_reference_search(self):
        """横断的法令検索テスト"""
        print("\n=== 横断的法令検索テスト ===")
        
        # 複数の税法にまたがる検索クエリ
        cross_reference_queries = [
            {
                "query": "事業所得の計算",
                "expected_laws": ["所得税法", "法人税法", "消費税法"]
            },
            {
                "query": "減価償却資産",
                "expected_laws": ["所得税法", "法人税法"]
            },
            {
                "query": "外国税額控除",
                "expected_laws": ["所得税法", "法人税法"]
            },
            {
                "query": "電子帳簿保存",
                "expected_laws": ["電子帳簿保存法", "所得税法", "法人税法", "消費税法"]
            }
        ]
        
        for query_data in cross_reference_queries:
            print(f"\n--- 横断検索クエリ: {query_data['query']} ---")
            
            # 横断的法令検索リクエスト
            search_request = {
                "method": "search_cross_reference",
                "params": {
                    "query": query_data["query"],
                    "tax_categories": ["all"],
                    "tax_year": 2025,
                    "search_type": "comprehensive",
                    "group_by_law": True
                }
            }
            
            print(f"横断検索リクエスト: {search_request}")
            
            # 横断的RAG検索実行
            search_result = self.rag_integration.search_cross_reference(
                search_request["params"]
            )
            
            print(f"横断検索結果: {search_result}")
            
            # 横断検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "横断的法令検索が成功している")
            
            # 複数の法律からの結果確認
            found_laws = list(search_result["results_by_law"].keys())
            for expected_law in query_data["expected_laws"]:
                self.assertIn(
                    expected_law,
                    found_laws,
                    f"期待される法律 {expected_law} からの結果が含まれている"
                )
            
            # 法律間の関連性確認
            if "cross_references" in search_result:
                self.assertGreater(
                    len(search_result["cross_references"]),
                    0,
                    "法律間の相互参照が見つかっている"
                )
            
            print(f"✓ {query_data['query']} 横断検索成功")
    
    def test_contextual_search(self):
        """文脈的検索テスト"""
        print("\n=== 文脈的検索テスト ===")
        
        # 文脈を含む検索シナリオ
        contextual_scenarios = [
            {
                "context": {
                    "taxpayer_type": "individual",
                    "income_type": "salary",
                    "annual_income": 5000000,
                    "family_status": "married_with_children"
                },
                "query": "適用可能な所得控除",
                "expected_controls": ["基礎控除", "配偶者控除", "扶養控除"]
            },
            {
                "context": {
                    "taxpayer_type": "corporation",
                    "company_size": "small",
                    "annual_revenue": 80000000,
                    "industry": "manufacturing"
                },
                "query": "適用可能な税制優遇措置",
                "expected_measures": ["中小企業軽減税率", "研究開発税制"]
            },
            {
                "context": {
                    "taxpayer_type": "individual",
                    "property_type": "residential",
                    "purchase_year": 2025,
                    "loan_amount": 30000000
                },
                "query": "住宅関連の税制優遇",
                "expected_benefits": ["住宅借入金等特別控除", "住宅取得等資金贈与の特例"]
            }
        ]
        
        for scenario in contextual_scenarios:
            print(f"\n--- 文脈的検索: {scenario['query']} ---")
            print(f"文脈: {scenario['context']}")
            
            # 文脈的検索リクエスト
            search_request = {
                "method": "search_contextual",
                "params": {
                    "query": scenario["query"],
                    "context": scenario["context"],
                    "tax_year": 2025,
                    "personalized": True,
                    "include_calculations": True
                }
            }
            
            print(f"文脈的検索リクエスト: {search_request}")
            
            # 文脈的RAG検索実行
            search_result = self.rag_integration.search_contextual(
                search_request["params"]
            )
            
            print(f"文脈的検索結果: {search_result}")
            
            # 文脈的検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "文脈的検索が成功している")
            
            # パーソナライズされた結果の確認
            self.assertIn(
                "personalized_results",
                search_result,
                "パーソナライズされた結果が含まれている"
            )
            
            # 期待される項目の確認
            if "expected_controls" in scenario:
                found_controls = [
                    result["name"] for result in search_result["personalized_results"]
                ]
                for expected_control in scenario["expected_controls"]:
                    self.assertIn(
                        expected_control,
                        found_controls,
                        f"期待される控除 {expected_control} が見つかっている"
                    )
            
            print(f"✓ {scenario['query']} 文脈的検索成功")
    
    def test_semantic_search_accuracy(self):
        """セマンティック検索精度テスト"""
        print("\n=== セマンティック検索精度テスト ===")
        
        # セマンティック検索のテストケース
        semantic_test_cases = [
            {
                "query": "年収500万円のサラリーマンの税金",
                "semantic_keywords": ["給与所得", "所得税", "住民税"],
                "expected_relevance": 0.8
            },
            {
                "query": "会社を設立した時の税務手続き",
                "semantic_keywords": ["法人設立", "法人税", "消費税", "届出書"],
                "expected_relevance": 0.75
            },
            {
                "query": "家を買った時の税金の優遇",
                "semantic_keywords": ["住宅取得", "住宅借入金等特別控除", "登録免許税"],
                "expected_relevance": 0.8
            },
            {
                "query": "副業の収入はどう申告するか",
                "semantic_keywords": ["雑所得", "確定申告", "20万円以下"],
                "expected_relevance": 0.75
            }
        ]
        
        for test_case in semantic_test_cases:
            print(f"\n--- セマンティック検索: {test_case['query']} ---")
            
            # セマンティック検索リクエスト
            search_request = {
                "method": "search_semantic",
                "params": {
                    "query": test_case["query"],
                    "search_mode": "semantic",
                    "tax_year": 2025,
                    "max_results": 5,
                    "min_relevance": 0.6
                }
            }
            
            print(f"セマンティック検索リクエスト: {search_request}")
            
            # セマンティックRAG検索実行
            search_result = self.rag_integration.search_semantic(
                search_request["params"]
            )
            
            print(f"セマンティック検索結果: {search_result}")
            
            # セマンティック検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "セマンティック検索が成功している")
            
            # 関連度スコアの確認
            for result in search_result["results"]:
                self.assertGreaterEqual(
                    result["semantic_score"],
                    test_case["expected_relevance"],
                    f"セマンティックスコアが期待値 {test_case['expected_relevance']} 以上"
                )
            
            # セマンティックキーワードの確認
            found_content = " ".join([
                result["content"] for result in search_result["results"]
            ])
            
            for keyword in test_case["semantic_keywords"]:
                # 完全一致または類似表現の確認
                keyword_found = (
                    keyword in found_content or
                    any(similar in found_content for similar in self._get_similar_terms(keyword))
                )
                self.assertTrue(
                    keyword_found,
                    f"セマンティックキーワード '{keyword}' または類似表現が見つかっている"
                )
            
            print(f"✓ {test_case['query']} セマンティック検索成功")
    
    def test_search_performance(self):
        """検索パフォーマンステスト"""
        print("\n=== 検索パフォーマンステスト ===")
        
        # パフォーマンステスト用のクエリ
        performance_queries = [
            "所得税の計算方法",
            "法人税の申告期限",
            "消費税の仕入税額控除",
            "住民税の特別徴収",
            "相続税の基礎控除"
        ]
        
        # 単一検索のパフォーマンステスト
        print("\n--- 単一検索パフォーマンス ---")
        for query in performance_queries:
            print(f"検索クエリ: {query}")
            
            # パフォーマンス測定開始
            start_time = self.start_performance_measurement()
            
            # 検索実行
            search_result = self.rag_integration.search_legal_reference({
                "query": query,
                "tax_category": "all",
                "tax_year": 2025
            })
            
            # パフォーマンス測定終了
            performance_result = self.end_performance_measurement(start_time)
            
            print(f"検索時間: {performance_result['duration']:.3f}秒")
            
            # パフォーマンスのアサーション
            PerformanceAssertions.assert_response_time_acceptable(
                performance_result,
                max_duration=2.0  # 2秒以内
            )
            
            self.assertTrue(search_result["success"], "検索が成功している")
            
            print(f"✓ {query} パフォーマンステスト成功")
        
        # 並行検索のパフォーマンステスト
        print("\n--- 並行検索パフォーマンス ---")
        
        async def concurrent_search_test():
            """並行検索テスト"""
            tasks = []
            
            for query in performance_queries:
                task = asyncio.create_task(
                    self.rag_integration.search_legal_reference_async({
                        "query": query,
                        "tax_category": "all",
                        "tax_year": 2025
                    })
                )
                tasks.append(task)
            
            # 並行実行
            start_time = self.start_performance_measurement()
            results = await asyncio.gather(*tasks)
            performance_result = self.end_performance_measurement(start_time)
            
            return results, performance_result
        
        # 並行検索実行
        concurrent_results, concurrent_performance = asyncio.run(concurrent_search_test())
        
        print(f"並行検索時間: {concurrent_performance['duration']:.3f}秒")
        print(f"検索数: {len(performance_queries)}件")
        
        # 並行検索パフォーマンスのアサーション
        PerformanceAssertions.assert_concurrent_performance_acceptable(
            concurrent_performance,
            request_count=len(performance_queries),
            max_duration=5.0  # 5秒以内
        )
        
        # 全ての並行検索が成功していることを確認
        for i, result in enumerate(concurrent_results):
            self.assertTrue(
                result["success"],
                f"並行検索 {i+1} が成功している"
            )
        
        print("✓ 並行検索パフォーマンステスト成功")
    
    def _get_similar_terms(self, keyword):
        """類似用語を取得するヘルパーメソッド"""
        similar_terms_map = {
            "給与所得": ["給料", "サラリー", "賃金"],
            "所得税": ["個人所得税", "所得課税"],
            "住民税": ["地方税", "市県民税"],
            "法人設立": ["会社設立", "法人成立"],
            "法人税": ["会社税", "企業税"],
            "消費税": ["付加価値税", "間接税"],
            "住宅取得": ["家購入", "住宅購入", "マイホーム取得"],
            "住宅借入金等特別控除": ["住宅ローン控除", "住宅ローン減税"],
            "雑所得": ["その他所得", "副業所得"],
            "確定申告": ["所得申告", "税務申告"]
        }
        
        return similar_terms_map.get(keyword, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)