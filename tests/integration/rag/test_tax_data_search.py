"""税務データ検索RAG統合テスト

TaxMCPサーバーの税務データ検索RAG機能をテストする
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


class TestTaxDataSearch(TaxMCPTestCase, PerformanceTestMixin):
    """税務データ検索RAG統合テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.rag_integration = MockRAGIntegration()
        self.data_generator = TestDataGenerator()
    
    def test_semantic_tax_search(self):
        """セマンティック税務検索テスト"""
        print("\n=== セマンティック税務検索テスト ===")
        
        # セマンティック検索のテストクエリ
        semantic_queries = [
            {
                "query": "給与所得控除の計算方法",
                "expected_topics": ["給与所得", "所得控除", "計算方法"],
                "expected_tax_types": ["所得税"],
                "min_relevance_score": 0.8
            },
            {
                "query": "法人税の減価償却資産の処理",
                "expected_topics": ["法人税", "減価償却", "資産"],
                "expected_tax_types": ["法人税"],
                "min_relevance_score": 0.8
            },
            {
                "query": "消費税のインボイス制度における仕入税額控除",
                "expected_topics": ["消費税", "インボイス", "仕入税額控除"],
                "expected_tax_types": ["消費税"],
                "min_relevance_score": 0.8
            },
            {
                "query": "住民税の特別徴収と普通徴収の違い",
                "expected_topics": ["住民税", "特別徴収", "普通徴収"],
                "expected_tax_types": ["住民税"],
                "min_relevance_score": 0.8
            },
            {
                "query": "相続税の基礎控除額の計算",
                "expected_topics": ["相続税", "基礎控除", "計算"],
                "expected_tax_types": ["相続税"],
                "min_relevance_score": 0.8
            }
        ]
        
        for query_data in semantic_queries:
            print(f"\n--- セマンティック検索: {query_data['query']} ---")
            
            # セマンティック検索リクエスト
            search_request = {
                "method": "semantic_search",
                "params": {
                    "query": query_data["query"],
                    "search_type": "semantic",
                    "max_results": 10,
                    "include_metadata": True,
                    "relevance_threshold": 0.7
                }
            }
            
            print(f"検索リクエスト: {search_request}")
            
            # パフォーマンス測定開始
            start_time = self.start_performance_measurement()
            
            # セマンティック検索実行
            search_result = self.rag_integration.semantic_search(
                search_request["params"]
            )
            
            # パフォーマンス測定終了
            performance_result = self.end_performance_measurement(start_time)
            
            print(f"検索結果: {search_result}")
            print(f"検索時間: {performance_result['duration']:.3f}秒")
            
            # 検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "セマンティック検索が成功している")
            
            # 結果の品質確認
            results = search_result["results"]
            self.assertGreater(len(results), 0, "検索結果が返されている")
            
            # 関連性スコアの確認
            for result in results:
                self.assertGreaterEqual(
                    result["relevance_score"],
                    query_data["min_relevance_score"],
                    f"関連性スコアが十分に高い: {result['relevance_score']}"
                )
                
                # 期待されるトピックの確認
                result_content = result["content"].lower()
                topic_found = any(
                    topic in result_content
                    for topic in query_data["expected_topics"]
                )
                self.assertTrue(
                    topic_found,
                    f"期待されるトピックが含まれている: {query_data['expected_topics']}"
                )
            
            # パフォーマンスの確認
            PerformanceAssertions.assert_response_time_acceptable(
                performance_result,
                max_duration=2.0  # 2秒以内
            )
            
            print(f"✓ セマンティック検索成功: {len(results)}件の結果")
    
    def test_keyword_tax_search(self):
        """キーワード税務検索テスト"""
        print("\n=== キーワード税務検索テスト ===")
        
        # キーワード検索のテストクエリ
        keyword_queries = [
            {
                "keywords": ["所得税", "確定申告"],
                "search_filters": {
                    "tax_type": "income_tax",
                    "document_type": "guideline"
                },
                "expected_min_results": 5
            },
            {
                "keywords": ["法人税", "申告書", "別表"],
                "search_filters": {
                    "tax_type": "corporate_tax",
                    "document_type": "form"
                },
                "expected_min_results": 3
            },
            {
                "keywords": ["消費税", "課税事業者", "免税事業者"],
                "search_filters": {
                    "tax_type": "consumption_tax",
                    "document_type": "regulation"
                },
                "expected_min_results": 4
            },
            {
                "keywords": ["住民税", "均等割", "所得割"],
                "search_filters": {
                    "tax_type": "resident_tax",
                    "document_type": "law"
                },
                "expected_min_results": 2
            }
        ]
        
        for query_data in keyword_queries:
            print(f"\n--- キーワード検索: {query_data['keywords']} ---")
            
            # キーワード検索リクエスト
            search_request = {
                "method": "keyword_search",
                "params": {
                    "keywords": query_data["keywords"],
                    "search_type": "keyword",
                    "filters": query_data["search_filters"],
                    "max_results": 20,
                    "sort_by": "relevance",
                    "include_snippets": True
                }
            }
            
            print(f"検索リクエスト: {search_request}")
            
            # キーワード検索実行
            search_result = self.rag_integration.keyword_search(
                search_request["params"]
            )
            
            print(f"検索結果: {search_result}")
            
            # 検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "キーワード検索が成功している")
            
            # 結果数の確認
            results = search_result["results"]
            self.assertGreaterEqual(
                len(results),
                query_data["expected_min_results"],
                f"期待される最小結果数以上: {len(results)} >= {query_data['expected_min_results']}"
            )
            
            # フィルター適用の確認
            for result in results:
                if "tax_type" in query_data["search_filters"]:
                    self.assertEqual(
                        result["metadata"]["tax_type"],
                        query_data["search_filters"]["tax_type"],
                        "税目フィルターが適用されている"
                    )
                
                if "document_type" in query_data["search_filters"]:
                    self.assertEqual(
                        result["metadata"]["document_type"],
                        query_data["search_filters"]["document_type"],
                        "文書タイプフィルターが適用されている"
                    )
                
                # キーワードの存在確認
                content_lower = result["content"].lower()
                keyword_found = any(
                    keyword.lower() in content_lower
                    for keyword in query_data["keywords"]
                )
                self.assertTrue(
                    keyword_found,
                    f"キーワードが含まれている: {query_data['keywords']}"
                )
            
            print(f"✓ キーワード検索成功: {len(results)}件の結果")
    
    def test_hybrid_search(self):
        """ハイブリッド検索テスト"""
        print("\n=== ハイブリッド検索テスト ===")
        
        # ハイブリッド検索のテストクエリ
        hybrid_queries = [
            {
                "semantic_query": "給与所得者の年末調整の手続き",
                "keywords": ["年末調整", "給与所得", "源泉徴収"],
                "filters": {
                    "tax_year": 2025,
                    "tax_type": "income_tax"
                },
                "weight_semantic": 0.7,
                "weight_keyword": 0.3
            },
            {
                "semantic_query": "中小企業の法人税優遇措置",
                "keywords": ["中小企業", "法人税", "優遇措置", "軽減税率"],
                "filters": {
                    "tax_year": 2025,
                    "tax_type": "corporate_tax"
                },
                "weight_semantic": 0.6,
                "weight_keyword": 0.4
            },
            {
                "semantic_query": "消費税の軽減税率対象品目",
                "keywords": ["軽減税率", "消費税", "対象品目", "食料品"],
                "filters": {
                    "tax_type": "consumption_tax",
                    "regulation_type": "rate_classification"
                },
                "weight_semantic": 0.8,
                "weight_keyword": 0.2
            }
        ]
        
        for query_data in hybrid_queries:
            print(f"\n--- ハイブリッド検索: {query_data['semantic_query']} ---")
            
            # ハイブリッド検索リクエスト
            search_request = {
                "method": "hybrid_search",
                "params": {
                    "semantic_query": query_data["semantic_query"],
                    "keywords": query_data["keywords"],
                    "filters": query_data["filters"],
                    "weight_semantic": query_data["weight_semantic"],
                    "weight_keyword": query_data["weight_keyword"],
                    "max_results": 15,
                    "include_explanation": True
                }
            }
            
            print(f"検索リクエスト: {search_request}")
            
            # ハイブリッド検索実行
            search_result = self.rag_integration.hybrid_search(
                search_request["params"]
            )
            
            print(f"検索結果: {search_result}")
            
            # 検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "ハイブリッド検索が成功している")
            
            # 結果の品質確認
            results = search_result["results"]
            self.assertGreater(len(results), 0, "検索結果が返されている")
            
            # ハイブリッドスコアの確認
            for result in results:
                self.assertIn(
                    "hybrid_score",
                    result,
                    "ハイブリッドスコアが計算されている"
                )
                
                self.assertIn(
                    "semantic_score",
                    result,
                    "セマンティックスコアが含まれている"
                )
                
                self.assertIn(
                    "keyword_score",
                    result,
                    "キーワードスコアが含まれている"
                )
                
                # スコアの妥当性確認
                expected_hybrid_score = (
                    result["semantic_score"] * query_data["weight_semantic"] +
                    result["keyword_score"] * query_data["weight_keyword"]
                )
                
                self.assertAlmostEqual(
                    result["hybrid_score"],
                    expected_hybrid_score,
                    places=3,
                    msg="ハイブリッドスコアが正しく計算されている"
                )
            
            # 結果の並び順確認（ハイブリッドスコア降順）
            for i in range(len(results) - 1):
                self.assertGreaterEqual(
                    results[i]["hybrid_score"],
                    results[i + 1]["hybrid_score"],
                    "結果がハイブリッドスコア順に並んでいる"
                )
            
            print(f"✓ ハイブリッド検索成功: {len(results)}件の結果")
    
    def test_faceted_search(self):
        """ファセット検索テスト"""
        print("\n=== ファセット検索テスト ===")
        
        # ファセット検索のテストケース
        faceted_queries = [
            {
                "query": "税務申告",
                "facets": {
                    "tax_type": ["income_tax", "corporate_tax"],
                    "document_type": ["form", "guideline"],
                    "tax_year": [2024, 2025]
                },
                "facet_mode": "AND"
            },
            {
                "query": "控除",
                "facets": {
                    "tax_type": ["income_tax"],
                    "deduction_type": ["basic", "special", "itemized"],
                    "taxpayer_type": ["individual", "business"]
                },
                "facet_mode": "OR"
            },
            {
                "query": "税率",
                "facets": {
                    "tax_type": ["consumption_tax", "corporate_tax"],
                    "rate_type": ["standard", "reduced", "preferential"],
                    "effective_date": ["2024-01-01", "2025-01-01"]
                },
                "facet_mode": "MIXED"
            }
        ]
        
        for query_data in faceted_queries:
            print(f"\n--- ファセット検索: {query_data['query']} ---")
            
            # ファセット検索リクエスト
            search_request = {
                "method": "faceted_search",
                "params": {
                    "query": query_data["query"],
                    "facets": query_data["facets"],
                    "facet_mode": query_data["facet_mode"],
                    "max_results": 25,
                    "include_facet_counts": True,
                    "include_facet_suggestions": True
                }
            }
            
            print(f"検索リクエスト: {search_request}")
            
            # ファセット検索実行
            search_result = self.rag_integration.faceted_search(
                search_request["params"]
            )
            
            print(f"検索結果: {search_result}")
            
            # 検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "ファセット検索が成功している")
            
            # ファセット情報の確認
            self.assertIn(
                "facet_counts",
                search_result,
                "ファセットカウントが含まれている"
            )
            
            facet_counts = search_result["facet_counts"]
            for facet_name in query_data["facets"].keys():
                self.assertIn(
                    facet_name,
                    facet_counts,
                    f"ファセット {facet_name} のカウントが含まれている"
                )
            
            # 結果のファセット適用確認
            results = search_result["results"]
            for result in results:
                metadata = result["metadata"]
                
                # ファセットモードに応じた確認
                if query_data["facet_mode"] == "AND":
                    # すべてのファセット条件を満たしている
                    for facet_name, facet_values in query_data["facets"].items():
                        if facet_name in metadata:
                            self.assertIn(
                                metadata[facet_name],
                                facet_values,
                                f"ANDモード: ファセット {facet_name} の条件を満たしている"
                            )
                
                elif query_data["facet_mode"] == "OR":
                    # いずれかのファセット条件を満たしている
                    condition_met = False
                    for facet_name, facet_values in query_data["facets"].items():
                        if facet_name in metadata and metadata[facet_name] in facet_values:
                            condition_met = True
                            break
                    
                    self.assertTrue(
                        condition_met,
                        "ORモード: いずれかのファセット条件を満たしている"
                    )
            
            # ファセット提案の確認
            if "facet_suggestions" in search_result:
                suggestions = search_result["facet_suggestions"]
                self.assertIsInstance(
                    suggestions,
                    dict,
                    "ファセット提案が辞書形式で返されている"
                )
            
            print(f"✓ ファセット検索成功: {len(results)}件の結果")
    
    def test_temporal_search(self):
        """時系列検索テスト"""
        print("\n=== 時系列検索テスト ===")
        
        # 時系列検索のテストケース
        temporal_queries = [
            {
                "query": "税制改正",
                "time_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2025-12-31"
                },
                "time_granularity": "year",
                "sort_by_time": True
            },
            {
                "query": "申告期限",
                "time_range": {
                    "start_date": "2025-01-01",
                    "end_date": "2025-03-31"
                },
                "time_granularity": "month",
                "sort_by_time": True
            },
            {
                "query": "税率変更",
                "time_range": {
                    "start_date": "2023-01-01",
                    "end_date": "2025-12-31"
                },
                "time_granularity": "quarter",
                "sort_by_time": False
            }
        ]
        
        for query_data in temporal_queries:
            print(f"\n--- 時系列検索: {query_data['query']} ---")
            
            # 時系列検索リクエスト
            search_request = {
                "method": "temporal_search",
                "params": {
                    "query": query_data["query"],
                    "time_range": query_data["time_range"],
                    "time_granularity": query_data["time_granularity"],
                    "sort_by_time": query_data["sort_by_time"],
                    "max_results": 20,
                    "include_timeline": True
                }
            }
            
            print(f"検索リクエスト: {search_request}")
            
            # 時系列検索実行
            search_result = self.rag_integration.temporal_search(
                search_request["params"]
            )
            
            print(f"検索結果: {search_result}")
            
            # 検索結果のアサーション
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "時系列検索が成功している")
            
            # 時系列情報の確認
            self.assertIn(
                "timeline",
                search_result,
                "タイムライン情報が含まれている"
            )
            
            timeline = search_result["timeline"]
            self.assertIsInstance(
                timeline,
                dict,
                "タイムラインが辞書形式で返されている"
            )
            
            # 結果の時間範囲確認
            results = search_result["results"]
            start_date = datetime.strptime(query_data["time_range"]["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(query_data["time_range"]["end_date"], "%Y-%m-%d")
            
            for result in results:
                if "effective_date" in result["metadata"]:
                    result_date = datetime.strptime(
                        result["metadata"]["effective_date"],
                        "%Y-%m-%d"
                    )
                    
                    self.assertGreaterEqual(
                        result_date,
                        start_date,
                        "結果が指定された開始日以降"
                    )
                    
                    self.assertLessEqual(
                        result_date,
                        end_date,
                        "結果が指定された終了日以前"
                    )
            
            # 時系列ソートの確認
            if query_data["sort_by_time"] and len(results) > 1:
                for i in range(len(results) - 1):
                    if ("effective_date" in results[i]["metadata"] and
                        "effective_date" in results[i + 1]["metadata"]):
                        
                        date1 = datetime.strptime(
                            results[i]["metadata"]["effective_date"],
                            "%Y-%m-%d"
                        )
                        date2 = datetime.strptime(
                            results[i + 1]["metadata"]["effective_date"],
                            "%Y-%m-%d"
                        )
                        
                        self.assertGreaterEqual(
                            date1,
                            date2,
                            "結果が時系列順（降順）に並んでいる"
                        )
            
            print(f"✓ 時系列検索成功: {len(results)}件の結果")
    
    def test_search_performance_optimization(self):
        """検索パフォーマンス最適化テスト"""
        print("\n=== 検索パフォーマンス最適化テスト ===")
        
        # パフォーマンステストのシナリオ
        performance_scenarios = [
            {
                "scenario": "large_result_set",
                "query": "税",
                "max_results": 1000,
                "expected_max_time": 3.0
            },
            {
                "scenario": "complex_semantic_query",
                "query": "個人事業主の青色申告における所得控除と税額控除の適用順序と計算方法",
                "max_results": 50,
                "expected_max_time": 2.0
            },
            {
                "scenario": "multiple_filters",
                "query": "申告",
                "filters": {
                    "tax_type": "income_tax",
                    "document_type": "guideline",
                    "tax_year": 2025,
                    "taxpayer_type": "individual",
                    "complexity_level": "advanced"
                },
                "max_results": 100,
                "expected_max_time": 1.5
            }
        ]
        
        for scenario in performance_scenarios:
            print(f"\n--- パフォーマンステスト: {scenario['scenario']} ---")
            
            # 検索リクエスト準備
            search_request = {
                "method": "optimized_search",
                "params": {
                    "query": scenario["query"],
                    "max_results": scenario["max_results"],
                    "enable_caching": True,
                    "enable_parallel_processing": True
                }
            }
            
            if "filters" in scenario:
                search_request["params"]["filters"] = scenario["filters"]
            
            print(f"検索リクエスト: {search_request}")
            
            # パフォーマンス測定開始
            start_time = self.start_performance_measurement()
            
            # 最適化検索実行
            search_result = self.rag_integration.optimized_search(
                search_request["params"]
            )
            
            # パフォーマンス測定終了
            performance_result = self.end_performance_measurement(start_time)
            
            print(f"検索結果: {len(search_result.get('results', []))}件")
            print(f"検索時間: {performance_result['duration']:.3f}秒")
            
            # パフォーマンスのアサーション
            PerformanceAssertions.assert_response_time_acceptable(
                performance_result,
                max_duration=scenario["expected_max_time"]
            )
            
            # 検索結果の品質確認
            APIAssertions.assert_success_response(search_result)
            self.assertTrue(search_result["success"], "最適化検索が成功している")
            
            # キャッシュ効果の確認（2回目の実行）
            if search_request["params"].get("enable_caching"):
                print("キャッシュ効果テスト実行中...")
                
                # 2回目の検索実行
                start_time_cached = self.start_performance_measurement()
                
                cached_result = self.rag_integration.optimized_search(
                    search_request["params"]
                )
                
                performance_cached = self.end_performance_measurement(start_time_cached)
                
                print(f"キャッシュ検索時間: {performance_cached['duration']:.3f}秒")
                
                # キャッシュによる高速化の確認
                self.assertLess(
                    performance_cached["duration"],
                    performance_result["duration"] * 0.5,  # 50%以上の高速化
                    "キャッシュにより検索が高速化されている"
                )
            
            print(f"✓ {scenario['scenario']} パフォーマンステスト成功")


if __name__ == "__main__":
    unittest.main(verbosity=2)