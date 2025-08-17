"""外部データソース連携RAG統合テスト

TaxMCPサーバーの外部データソース連携RAG機能をテストする
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
from tests.utils.mock_external_apis import MockRAGIntegration, MockExternalAPIs
from tests.utils.test_data_generator import TestDataGenerator


class TestExternalDataIntegration(TaxMCPTestCase, PerformanceTestMixin):
    """外部データソース連携RAG統合テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.rag_integration = MockRAGIntegration()
        self.external_apis = MockExternalAPIs()
        self.data_generator = TestDataGenerator()
    
    def test_ministry_of_finance_integration(self):
        """財務省データ連携テスト"""
        print("\n=== 財務省データ連携テスト ===")
        
        # 財務省からのデータ取得テストケース
        mof_data_requests = [
            {
                "data_type": "tax_rates",
                "tax_year": 2025,
                "category": "income_tax",
                "expected_fields": ["rate", "threshold", "effective_date"]
            },
            {
                "data_type": "tax_law_updates",
                "tax_year": 2025,
                "category": "corporate_tax",
                "expected_fields": ["law_number", "amendment_date", "content"]
            },
            {
                "data_type": "economic_indicators",
                "period": "2025-Q1",
                "category": "inflation_rate",
                "expected_fields": ["rate", "period", "source"]
            },
            {
                "data_type": "budget_information",
                "fiscal_year": 2025,
                "category": "tax_revenue",
                "expected_fields": ["amount", "category", "projection"]
            }
        ]
        
        for request_data in mof_data_requests:
            print(f"\n--- 財務省データ取得: {request_data['data_type']} ---")
            
            # 財務省API呼び出しリクエスト
            api_request = {
                "method": "get_ministry_data",
                "params": {
                    "source": "ministry_of_finance",
                    "data_type": request_data["data_type"],
                    "filters": {
                        key: value for key, value in request_data.items()
                        if key not in ["data_type", "expected_fields"]
                    }
                }
            }
            
            print(f"財務省APIリクエスト: {api_request}")
            
            # 外部API呼び出し実行
            api_result = self.external_apis.call_ministry_of_finance_api(
                api_request["params"]
            )
            
            print(f"財務省API結果: {api_result}")
            
            # API結果のアサーション
            APIAssertions.assert_success_response(api_result)
            self.assertTrue(api_result["success"], "財務省APIが成功している")
            self.assertIn("data", api_result, "データが返されている")
            
            # 期待されるフィールドの確認
            if api_result["data"]:
                data_item = api_result["data"][0] if isinstance(api_result["data"], list) else api_result["data"]
                for expected_field in request_data["expected_fields"]:
                    self.assertIn(
                        expected_field,
                        data_item,
                        f"期待されるフィールド {expected_field} が含まれている"
                    )
            
            # RAGへのデータ統合
            print(f"RAGへのデータ統合開始...")
            integration_result = self.rag_integration.integrate_external_data(
                source="ministry_of_finance",
                data=api_result["data"],
                data_type=request_data["data_type"]
            )
            
            print(f"RAG統合結果: {integration_result}")
            
            # RAG統合のアサーション
            APIAssertions.assert_success_response(integration_result)
            self.assertTrue(integration_result["success"], "RAGデータ統合が成功している")
            self.assertGreater(
                integration_result["indexed_count"],
                0,
                "インデックスされたデータがある"
            )
            
            print(f"✓ {request_data['data_type']} 財務省データ連携成功")
    
    def test_national_tax_agency_integration(self):
        """国税庁データ連携テスト"""
        print("\n=== 国税庁データ連携テスト ===")
        
        # 国税庁からのデータ取得テストケース
        nta_data_requests = [
            {
                "data_type": "tax_forms",
                "tax_year": 2025,
                "form_type": "income_tax_return",
                "expected_fields": ["form_number", "title", "pdf_url"]
            },
            {
                "data_type": "tax_guidelines",
                "tax_year": 2025,
                "category": "corporate_tax",
                "expected_fields": ["guideline_id", "title", "content"]
            },
            {
                "data_type": "tax_statistics",
                "tax_year": 2024,
                "category": "income_distribution",
                "expected_fields": ["income_range", "taxpayer_count", "total_tax"]
            },
            {
                "data_type": "faq_data",
                "category": "consumption_tax",
                "topic": "invoice_system",
                "expected_fields": ["question", "answer", "category"]
            }
        ]
        
        for request_data in nta_data_requests:
            print(f"\n--- 国税庁データ取得: {request_data['data_type']} ---")
            
            # 国税庁API呼び出しリクエスト
            api_request = {
                "method": "get_nta_data",
                "params": {
                    "source": "national_tax_agency",
                    "data_type": request_data["data_type"],
                    "filters": {
                        key: value for key, value in request_data.items()
                        if key not in ["data_type", "expected_fields"]
                    }
                }
            }
            
            print(f"国税庁APIリクエスト: {api_request}")
            
            # 外部API呼び出し実行
            api_result = self.external_apis.call_national_tax_agency_api(
                api_request["params"]
            )
            
            print(f"国税庁API結果: {api_result}")
            
            # API結果のアサーション
            APIAssertions.assert_success_response(api_result)
            self.assertTrue(api_result["success"], "国税庁APIが成功している")
            
            # データ品質の確認
            if api_result["data"]:
                data_items = api_result["data"] if isinstance(api_result["data"], list) else [api_result["data"]]
                for data_item in data_items:
                    for expected_field in request_data["expected_fields"]:
                        self.assertIn(
                            expected_field,
                            data_item,
                            f"期待されるフィールド {expected_field} が含まれている"
                        )
            
            # RAGへのデータ統合
            integration_result = self.rag_integration.integrate_external_data(
                source="national_tax_agency",
                data=api_result["data"],
                data_type=request_data["data_type"]
            )
            
            # RAG統合のアサーション
            APIAssertions.assert_success_response(integration_result)
            self.assertTrue(integration_result["success"], "RAGデータ統合が成功している")
            
            print(f"✓ {request_data['data_type']} 国税庁データ連携成功")
    
    def test_egov_integration(self):
        """e-Gov連携テスト"""
        print("\n=== e-Gov連携テスト ===")
        
        # e-Govからのデータ取得テストケース
        egov_data_requests = [
            {
                "data_type": "law_text",
                "law_name": "所得税法",
                "article_range": "1-100",
                "expected_fields": ["article_number", "content", "last_updated"]
            },
            {
                "data_type": "regulation_text",
                "regulation_name": "所得税法施行令",
                "article_range": "1-50",
                "expected_fields": ["article_number", "content", "parent_law"]
            },
            {
                "data_type": "administrative_notices",
                "category": "tax_administration",
                "year": 2025,
                "expected_fields": ["notice_number", "title", "content"]
            },
            {
                "data_type": "legal_precedents",
                "category": "tax_law",
                "court_level": "supreme_court",
                "expected_fields": ["case_number", "date", "summary"]
            }
        ]
        
        for request_data in egov_data_requests:
            print(f"\n--- e-Govデータ取得: {request_data['data_type']} ---")
            
            # e-Gov API呼び出しリクエスト
            api_request = {
                "method": "get_egov_data",
                "params": {
                    "source": "egov",
                    "data_type": request_data["data_type"],
                    "filters": {
                        key: value for key, value in request_data.items()
                        if key not in ["data_type", "expected_fields"]
                    }
                }
            }
            
            print(f"e-Gov APIリクエスト: {api_request}")
            
            # 外部API呼び出し実行
            api_result = self.external_apis.call_egov_api(
                api_request["params"]
            )
            
            print(f"e-Gov API結果: {api_result}")
            
            # API結果のアサーション
            APIAssertions.assert_success_response(api_result)
            self.assertTrue(api_result["success"], "e-Gov APIが成功している")
            
            # 法令データの構造確認
            if api_result["data"]:
                data_items = api_result["data"] if isinstance(api_result["data"], list) else [api_result["data"]]
                for data_item in data_items:
                    for expected_field in request_data["expected_fields"]:
                        self.assertIn(
                            expected_field,
                            data_item,
                            f"期待されるフィールド {expected_field} が含まれている"
                        )
            
            # RAGへのデータ統合
            integration_result = self.rag_integration.integrate_external_data(
                source="egov",
                data=api_result["data"],
                data_type=request_data["data_type"]
            )
            
            # RAG統合のアサーション
            APIAssertions.assert_success_response(integration_result)
            self.assertTrue(integration_result["success"], "RAGデータ統合が成功している")
            
            print(f"✓ {request_data['data_type']} e-Govデータ連携成功")
    
    def test_data_synchronization(self):
        """データ同期テスト"""
        print("\n=== データ同期テスト ===")
        
        # データ同期シナリオ
        sync_scenarios = [
            {
                "sync_type": "incremental",
                "sources": ["ministry_of_finance", "national_tax_agency"],
                "data_types": ["tax_rates", "tax_law_updates"],
                "schedule": "daily"
            },
            {
                "sync_type": "full",
                "sources": ["egov"],
                "data_types": ["law_text", "regulation_text"],
                "schedule": "weekly"
            },
            {
                "sync_type": "on_demand",
                "sources": ["national_tax_agency"],
                "data_types": ["tax_forms", "faq_data"],
                "schedule": "manual"
            }
        ]
        
        for scenario in sync_scenarios:
            print(f"\n--- データ同期: {scenario['sync_type']} ---")
            
            # データ同期リクエスト
            sync_request = {
                "method": "synchronize_data",
                "params": {
                    "sync_type": scenario["sync_type"],
                    "sources": scenario["sources"],
                    "data_types": scenario["data_types"],
                    "force_update": True
                }
            }
            
            print(f"同期リクエスト: {sync_request}")
            
            # データ同期実行
            sync_result = self.rag_integration.synchronize_external_data(
                sync_request["params"]
            )
            
            print(f"同期結果: {sync_result}")
            
            # 同期結果のアサーション
            APIAssertions.assert_success_response(sync_result)
            self.assertTrue(sync_result["success"], "データ同期が成功している")
            
            # 各ソースの同期確認
            for source in scenario["sources"]:
                self.assertIn(
                    source,
                    sync_result["sync_results"],
                    f"ソース {source} の同期結果が含まれている"
                )
                
                source_result = sync_result["sync_results"][source]
                self.assertTrue(
                    source_result["success"],
                    f"ソース {source} の同期が成功している"
                )
            
            # 同期統計の確認
            self.assertIn("sync_statistics", sync_result, "同期統計が含まれている")
            stats = sync_result["sync_statistics"]
            self.assertGreaterEqual(stats["total_records"], 0, "同期レコード数が記録されている")
            
            print(f"✓ {scenario['sync_type']} データ同期成功")
    
    def test_data_validation_and_quality(self):
        """データ検証・品質テスト"""
        print("\n=== データ検証・品質テスト ===")
        
        # データ品質チェックのテストケース
        quality_check_scenarios = [
            {
                "data_source": "ministry_of_finance",
                "data_type": "tax_rates",
                "quality_checks": [
                    "completeness",
                    "accuracy",
                    "consistency",
                    "timeliness"
                ]
            },
            {
                "data_source": "national_tax_agency",
                "data_type": "tax_forms",
                "quality_checks": [
                    "format_validation",
                    "link_validation",
                    "content_integrity"
                ]
            },
            {
                "data_source": "egov",
                "data_type": "law_text",
                "quality_checks": [
                    "structure_validation",
                    "cross_reference_validation",
                    "version_consistency"
                ]
            }
        ]
        
        for scenario in quality_check_scenarios:
            print(f"\n--- データ品質チェック: {scenario['data_source']} ---")
            
            # データ品質チェックリクエスト
            quality_request = {
                "method": "validate_data_quality",
                "params": {
                    "data_source": scenario["data_source"],
                    "data_type": scenario["data_type"],
                    "quality_checks": scenario["quality_checks"],
                    "sample_size": 100
                }
            }
            
            print(f"品質チェックリクエスト: {quality_request}")
            
            # データ品質チェック実行
            quality_result = self.rag_integration.validate_data_quality(
                quality_request["params"]
            )
            
            print(f"品質チェック結果: {quality_result}")
            
            # 品質チェック結果のアサーション
            APIAssertions.assert_success_response(quality_result)
            self.assertTrue(quality_result["success"], "データ品質チェックが成功している")
            
            # 各品質チェックの結果確認
            for check_type in scenario["quality_checks"]:
                self.assertIn(
                    check_type,
                    quality_result["quality_scores"],
                    f"品質チェック {check_type} の結果が含まれている"
                )
                
                score = quality_result["quality_scores"][check_type]
                self.assertGreaterEqual(
                    score,
                    0.8,  # 80%以上の品質スコア
                    f"品質チェック {check_type} のスコアが十分に高い"
                )
            
            # 全体的な品質スコア確認
            overall_score = quality_result["overall_quality_score"]
            self.assertGreaterEqual(
                overall_score,
                0.85,  # 85%以上の全体品質スコア
                "全体的な品質スコアが十分に高い"
            )
            
            print(f"✓ {scenario['data_source']} データ品質チェック成功")
    
    def test_real_time_data_updates(self):
        """リアルタイムデータ更新テスト"""
        print("\n=== リアルタイムデータ更新テスト ===")
        
        # リアルタイム更新のテストシナリオ
        realtime_scenarios = [
            {
                "update_type": "tax_rate_change",
                "source": "ministry_of_finance",
                "trigger": "api_webhook",
                "expected_propagation_time": 30  # 30秒以内
            },
            {
                "update_type": "law_amendment",
                "source": "egov",
                "trigger": "scheduled_check",
                "expected_propagation_time": 300  # 5分以内
            },
            {
                "update_type": "form_update",
                "source": "national_tax_agency",
                "trigger": "manual_refresh",
                "expected_propagation_time": 60  # 1分以内
            }
        ]
        
        for scenario in realtime_scenarios:
            print(f"\n--- リアルタイム更新: {scenario['update_type']} ---")
            
            # 更新前の状態を記録
            initial_state = self.rag_integration.get_data_state(
                source=scenario["source"],
                data_type=scenario["update_type"]
            )
            
            print(f"更新前の状態: {initial_state}")
            
            # リアルタイム更新をトリガー
            update_request = {
                "method": "trigger_realtime_update",
                "params": {
                    "update_type": scenario["update_type"],
                    "source": scenario["source"],
                    "trigger": scenario["trigger"]
                }
            }
            
            print(f"更新トリガーリクエスト: {update_request}")
            
            # パフォーマンス測定開始
            start_time = self.start_performance_measurement()
            
            # リアルタイム更新実行
            update_result = self.rag_integration.trigger_realtime_update(
                update_request["params"]
            )
            
            # パフォーマンス測定終了
            performance_result = self.end_performance_measurement(start_time)
            
            print(f"更新結果: {update_result}")
            print(f"更新時間: {performance_result['duration']:.3f}秒")
            
            # 更新結果のアサーション
            APIAssertions.assert_success_response(update_result)
            self.assertTrue(update_result["success"], "リアルタイム更新が成功している")
            
            # 更新時間のアサーション
            PerformanceAssertions.assert_response_time_acceptable(
                performance_result,
                max_duration=scenario["expected_propagation_time"]
            )
            
            # 更新後の状態確認
            updated_state = self.rag_integration.get_data_state(
                source=scenario["source"],
                data_type=scenario["update_type"]
            )
            
            print(f"更新後の状態: {updated_state}")
            
            # 状態変更の確認
            self.assertNotEqual(
                initial_state["last_updated"],
                updated_state["last_updated"],
                "データの最終更新時刻が変更されている"
            )
            
            self.assertGreater(
                updated_state["version"],
                initial_state["version"],
                "データバージョンが更新されている"
            )
            
            print(f"✓ {scenario['update_type']} リアルタイム更新成功")
    
    def test_error_handling_and_fallback(self):
        """エラーハンドリング・フォールバックテスト"""
        print("\n=== エラーハンドリング・フォールバックテスト ===")
        
        # エラーシナリオのテストケース
        error_scenarios = [
            {
                "scenario": "api_timeout",
                "source": "ministry_of_finance",
                "error_type": "timeout",
                "expected_fallback": "cached_data"
            },
            {
                "scenario": "api_unavailable",
                "source": "national_tax_agency",
                "error_type": "connection_error",
                "expected_fallback": "alternative_source"
            },
            {
                "scenario": "invalid_response",
                "source": "egov",
                "error_type": "malformed_data",
                "expected_fallback": "data_validation_error"
            },
            {
                "scenario": "rate_limit_exceeded",
                "source": "ministry_of_finance",
                "error_type": "rate_limit",
                "expected_fallback": "retry_with_backoff"
            }
        ]
        
        for scenario in error_scenarios:
            print(f"\n--- エラーシナリオ: {scenario['scenario']} ---")
            
            # エラー状況をシミュレート
            error_request = {
                "method": "simulate_error",
                "params": {
                    "source": scenario["source"],
                    "error_type": scenario["error_type"],
                    "scenario": scenario["scenario"]
                }
            }
            
            print(f"エラーシミュレーションリクエスト: {error_request}")
            
            # エラーハンドリング実行
            error_result = self.rag_integration.handle_external_api_error(
                error_request["params"]
            )
            
            print(f"エラーハンドリング結果: {error_result}")
            
            # エラーハンドリングのアサーション
            self.assertFalse(
                error_result["success"],
                "エラーが適切に検出されている"
            )
            
            self.assertEqual(
                error_result["error_type"],
                scenario["error_type"],
                "エラータイプが正しく識別されている"
            )
            
            # フォールバック機能の確認
            self.assertIn(
                "fallback_action",
                error_result,
                "フォールバックアクションが実行されている"
            )
            
            self.assertEqual(
                error_result["fallback_action"],
                scenario["expected_fallback"],
                "期待されるフォールバックが実行されている"
            )
            
            # フォールバックデータの確認（該当する場合）
            if scenario["expected_fallback"] in ["cached_data", "alternative_source"]:
                self.assertIn(
                    "fallback_data",
                    error_result,
                    "フォールバックデータが提供されている"
                )
                
                self.assertIsNotNone(
                    error_result["fallback_data"],
                    "フォールバックデータが有効"
                )
            
            print(f"✓ {scenario['scenario']} エラーハンドリング成功")


if __name__ == "__main__":
    unittest.main(verbosity=2)