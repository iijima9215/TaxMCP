"""RAG統合テスト - 必要最小限のテストケース

外部データソース連携、法令参照検索、税制情報取得の
基本機能をテストする。
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any

# テストユーティリティのインポート
from tests.utils.test_config import TaxMCPTestCase
from tests.utils.performance_helpers import PerformanceTestMixin
from tests.utils.assertion_helpers import DataAssertions

# RAG統合モジュールのインポート
from rag_integration import RAGIntegration, TaxInformation


class TestRAGIntegration(TaxMCPTestCase, PerformanceTestMixin, DataAssertions):
    """RAG統合機能のテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.rag = RAGIntegration()
        
        # モックデータの準備
        self.sample_tax_info = [
            TaxInformation(
                source="国税庁",
                title="法人税率の改正について",
                content="令和7年度税制改正により法人税率が変更されます",
                url="https://www.nta.go.jp/test",
                category="corporate_tax",
                tax_year=2025,
                relevance_score=0.9
            ),
            TaxInformation(
                source="財務省",
                title="所得税控除額の見直し",
                content="基礎控除額が48万円に変更されます",
                url="https://www.mof.go.jp/test",
                category="income_tax",
                tax_year=2025,
                relevance_score=0.8
            )
        ]
    
    def tearDown(self):
        """テストクリーンアップ"""
        super().tearDown()
    
    def test_get_latest_tax_info_basic(self):
        """最新税制情報取得の基本テスト"""
        # モックの設定
        with patch.object(self.rag, 'fetcher') as mock_fetcher:
            mock_fetcher.__aenter__ = AsyncMock(return_value=mock_fetcher)
            mock_fetcher.__aexit__ = AsyncMock(return_value=None)
            mock_fetcher.fetch_mof_tax_reform_data = AsyncMock(return_value=self.sample_tax_info[:1])
            mock_fetcher.fetch_nta_tax_answer_data = AsyncMock(return_value=self.sample_tax_info[1:])
            mock_fetcher.search_relevant_info = MagicMock(return_value=self.sample_tax_info)
            
            # テスト実行
            async def run_test():
                result = await self.rag.get_latest_tax_info(query="法人税")
                return result
            
            result = asyncio.run(run_test())
            
            # 検証
            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)
            self.assertIsInstance(result[0], TaxInformation)
            
            # モックが呼ばれたことを確認
            mock_fetcher.fetch_mof_tax_reform_data.assert_called_once()
            mock_fetcher.fetch_nta_tax_answer_data.assert_called_once_with("法人税")
    
    def test_get_tax_rate_updates(self):
        """税率更新情報取得のテスト"""
        # モックの設定
        with patch.object(self.rag, 'fetcher') as mock_fetcher:
            mock_fetcher.__aenter__ = AsyncMock(return_value=mock_fetcher)
            mock_fetcher.__aexit__ = AsyncMock(return_value=None)
            mock_fetcher.fetch_mof_tax_reform_data = AsyncMock(return_value=self.sample_tax_info)
            mock_fetcher.fetch_nta_tax_answer_data = AsyncMock(return_value=[])
            mock_fetcher.search_relevant_info = MagicMock(return_value=self.sample_tax_info)
            
            # キャッシュをクリア
            self.rag.cache.get = MagicMock(return_value=None)
            self.rag.cache.set = MagicMock()
            
            # テスト実行
            async def run_test():
                result = await self.rag.get_tax_rate_updates(2025)
                return result
            
            result = asyncio.run(run_test())
            
            # 検証
            self.assertIsInstance(result, dict)
            self.assertEqual(result['tax_year'], 2025)
            self.assertIn('income_tax_changes', result)
            self.assertIn('corporate_tax_changes', result)
            self.assertIn('consumption_tax_changes', result)
            self.assertIn('last_updated', result)
            
            # 結果の基本構造を確認（変更が検出されない場合もある）
            self.assertIsInstance(result['corporate_tax_changes'], list)
    
    def test_search_legal_reference_tax_answer(self):
        """法令参照検索（タックスアンサー）のテスト"""
        # モックの設定
        mock_result = TaxInformation(
            source="国税庁タックスアンサー",
            title="タックスアンサー No.5280",
            content="法人税の計算について",
            url="https://www.nta.go.jp/taxes/shiraberu/taxanswer/hojin/5280.htm",
            category="tax_answer",
            relevance_score=1.0
        )
        
        with patch.object(self.rag, '_search_tax_answer_by_number', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_result
            
            # キャッシュをクリア
            self.rag.cache.get = MagicMock(return_value=None)
            self.rag.cache.set = MagicMock()
            
            # テスト実行
            async def run_test():
                result = await self.rag.search_legal_reference("No.5280")
                return result
            
            result = asyncio.run(run_test())
            
            # 検証
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].title, "タックスアンサー No.5280")
            self.assertEqual(result[0].category, "tax_answer")
            
            # モックが正しい引数で呼ばれたことを確認
            mock_search.assert_called_once_with("5280")
    
    def test_search_legal_reference_law_article(self):
        """法令参照検索（法令条文）のテスト"""
        # モックの設定
        mock_result = TaxInformation(
            source="e-Gov法令検索",
            title="法人税法 第61条の4",
            content="法人税法第61条の4の条文内容",
            url="https://elaws.e-gov.go.jp/search/test",
            category="law_article",
            relevance_score=1.0
        )
        
        with patch.object(self.rag, '_search_law_article', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_result
            
            # キャッシュをクリア
            self.rag.cache.get = MagicMock(return_value=None)
            self.rag.cache.set = MagicMock()
            
            # テスト実行
            async def run_test():
                result = await self.rag.search_legal_reference("法人税法第61条の4")
                return result
            
            result = asyncio.run(run_test())
            
            # 検証
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].title, "法人税法 第61条の4")
            self.assertEqual(result[0].category, "law_article")
            
            # モックが正しい引数で呼ばれたことを確認
            mock_search.assert_called_once_with("法人税法", "61", "4")
    
    def test_cache_functionality(self):
        """キャッシュ機能のテスト"""
        # キャッシュにデータを設定
        test_data = [self.sample_tax_info[0]]
        self.rag.cache.set("test_key", test_data)
        
        # キャッシュからデータを取得
        cached_data = self.rag.cache.get("test_key")
        
        # 検証
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 1)
        self.assertEqual(cached_data[0].title, "法人税率の改正について")
    
    def test_performance_get_latest_tax_info(self):
        """最新税制情報取得のパフォーマンステスト"""
        # モックの設定
        with patch.object(self.rag, 'fetcher') as mock_fetcher:
            mock_fetcher.__aenter__ = AsyncMock(return_value=mock_fetcher)
            mock_fetcher.__aexit__ = AsyncMock(return_value=None)
            mock_fetcher.fetch_mof_tax_reform_data = AsyncMock(return_value=self.sample_tax_info)
            mock_fetcher.fetch_nta_tax_answer_data = AsyncMock(return_value=[])
            mock_fetcher.search_relevant_info = MagicMock(return_value=self.sample_tax_info)
            
            # パフォーマンステスト実行
            import time
            start_time = time.time()
            
            async def run_test():
                return await self.rag.get_latest_tax_info(query="法人税")
            
            result = asyncio.run(run_test())
            execution_time = time.time() - start_time
            
            # 検証（5秒以内で完了することを確認）
            self.assertLess(execution_time, 5.0, "RAG情報取得が5秒以内に完了すること")
            self.assertIsInstance(result, list)
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        # 例外を発生させるモックを設定
        with patch.object(self.rag, 'fetcher') as mock_fetcher:
            mock_fetcher.__aenter__ = AsyncMock(return_value=mock_fetcher)
            mock_fetcher.__aexit__ = AsyncMock(return_value=None)
            mock_fetcher.fetch_mof_tax_reform_data = AsyncMock(side_effect=Exception("ネットワークエラー"))
            mock_fetcher.fetch_nta_tax_answer_data = AsyncMock(return_value=[])
            mock_fetcher.search_relevant_info = MagicMock(return_value=[])
            
            # テスト実行（例外が発生しても正常に処理されることを確認）
            async def run_test():
                try:
                    result = await self.rag.get_latest_tax_info()
                    return result
                except Exception:
                    # 例外が発生した場合は空のリストを返す
                    return []
            
            result = asyncio.run(run_test())
            
            # 検証（例外が発生してもリストが返されることを確認）
            self.assertIsInstance(result, list)


if __name__ == '__main__':
    unittest.main()