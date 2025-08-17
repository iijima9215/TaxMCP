#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaxMCP パフォーマンステスト - レスポンス時間

このモジュールは、TaxMCPサーバーのレスポンス時間をテストします。

主なテスト項目:
- 税計算のレスポンス時間
- データベースクエリのレスポンス時間
- RAG検索のレスポンス時間
- 大量データ処理のレスポンス時間
- メモリ使用量の監視
"""

import unittest
import time
import threading
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, median, stdev

from tests.utils.test_config import TaxMCPTestCase
from tests.utils.performance_helpers import PerformanceTestMixin
from tests.utils.test_data_generator import TestDataGenerator


class TestResponseTime(TaxMCPTestCase, PerformanceTestMixin):
    """レスポンス時間テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.data_generator = TestDataGenerator()
        self.performance_thresholds = {
            "tax_calculation": 0.5,  # 500ms
            "database_query": 0.1,   # 100ms
            "rag_search": 1.0,       # 1000ms
            "bulk_processing": 5.0,  # 5000ms
            "memory_limit": 512      # 512MB
        }
        print(f"\n{'='*50}")
        print(f"テスト開始: {self._testMethodName}")
        print(f"{'='*50}")
    
    def tearDown(self):
        """テストクリーンアップ"""
        super().tearDown()
        gc.collect()  # ガベージコレクション実行
        print(f"\nテスト完了: {self._testMethodName}")
    
    def test_tax_calculation_response_time(self):
        """税計算レスポンス時間テスト"""
        print("\n=== 税計算レスポンス時間テスト ===")
        
        # 所得税計算のレスポンス時間
        print("\n--- 所得税計算レスポンス時間 ---")
        
        income_tax_cases = [
            {"income": 3000000, "deductions": 480000, "description": "標準ケース"},
            {"income": 10000000, "deductions": 1000000, "description": "高所得ケース"},
            {"income": 50000000, "deductions": 5000000, "description": "超高所得ケース"}
        ]
        
        for case in income_tax_cases:
            response_times = []
            for i in range(10):  # 10回実行
                start_time = time.perf_counter()
                result = self._calculate_income_tax(case["income"], case["deductions"])
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
            
            avg_time = mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            self.assertLess(avg_time, self.performance_thresholds["tax_calculation"], 
                          f"所得税計算の平均レスポンス時間が閾値を超過: {case['description']}")
            
            print(f"✓ {case['description']}: 平均{avg_time*1000:.2f}ms, 最大{max_time*1000:.2f}ms, 最小{min_time*1000:.2f}ms")
        
        # 法人税計算のレスポンス時間
        print("\n--- 法人税計算レスポンス時間 ---")
        
        corporate_tax_cases = [
            {"revenue": 100000000, "expenses": 80000000, "description": "中小企業ケース"},
            {"revenue": 1000000000, "expenses": 800000000, "description": "大企業ケース"},
            {"revenue": 5000000000, "expenses": 4000000000, "description": "超大企業ケース"}
        ]
        
        for case in corporate_tax_cases:
            response_times = []
            for i in range(10):
                start_time = time.perf_counter()
                result = self._calculate_corporate_tax(case["revenue"], case["expenses"])
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
            
            avg_time = mean(response_times)
            self.assertLess(avg_time, self.performance_thresholds["tax_calculation"], 
                          f"法人税計算の平均レスポンス時間が閾値を超過: {case['description']}")
            
            print(f"✓ {case['description']}: 平均{avg_time*1000:.2f}ms")
        
        # 消費税計算のレスポンス時間
        print("\n--- 消費税計算レスポンス時間 ---")
        
        consumption_tax_cases = [
            {"amount": 10000, "rate": 0.10, "description": "標準税率ケース"},
            {"amount": 1000000, "rate": 0.08, "description": "軽減税率ケース"},
            {"amount": 100000000, "rate": 0.10, "description": "大金額ケース"}
        ]
        
        for case in consumption_tax_cases:
            response_times = []
            for i in range(10):
                start_time = time.perf_counter()
                result = self._calculate_consumption_tax(case["amount"], case["rate"])
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
            
            avg_time = mean(response_times)
            self.assertLess(avg_time, self.performance_thresholds["tax_calculation"], 
                          f"消費税計算の平均レスポンス時間が閾値を超過: {case['description']}")
            
            print(f"✓ {case['description']}: 平均{avg_time*1000:.2f}ms")
        
        print("✓ 税計算レスポンス時間テスト成功")
    
    def test_database_query_response_time(self):
        """データベースクエリレスポンス時間テスト"""
        print("\n=== データベースクエリレスポンス時間テスト ===")
        
        # 単純なクエリのレスポンス時間
        print("\n--- 単純クエリレスポンス時間 ---")
        
        simple_queries = [
            {"query": "SELECT * FROM tax_documents LIMIT 10", "description": "小規模取得"},
            {"query": "SELECT * FROM tax_documents LIMIT 100", "description": "中規模取得"},
            {"query": "SELECT * FROM tax_documents LIMIT 1000", "description": "大規模取得"}
        ]
        
        for query_case in simple_queries:
            response_times = []
            for i in range(5):
                start_time = time.perf_counter()
                result = self._execute_database_query(query_case["query"])
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
            
            avg_time = mean(response_times)
            self.assertLess(avg_time, self.performance_thresholds["database_query"], 
                          f"データベースクエリの平均レスポンス時間が閾値を超過: {query_case['description']}")
            
            print(f"✓ {query_case['description']}: 平均{avg_time*1000:.2f}ms")
        
        # 複雑なクエリのレスポンス時間
        print("\n--- 複雑クエリレスポンス時間 ---")
        
        complex_queries = [
            {
                "query": "SELECT d.*, m.* FROM tax_documents d JOIN document_metadata m ON d.id = m.document_id WHERE d.tax_type = 'income_tax'",
                "description": "JOIN クエリ"
            },
            {
                "query": "SELECT tax_type, COUNT(*) as count FROM tax_documents GROUP BY tax_type ORDER BY count DESC",
                "description": "集計クエリ"
            },
            {
                "query": "SELECT * FROM tax_documents WHERE content LIKE '%所得税%' AND created_at > '2024-01-01'",
                "description": "検索クエリ"
            }
        ]
        
        for query_case in complex_queries:
            response_times = []
            for i in range(3):
                start_time = time.perf_counter()
                result = self._execute_database_query(query_case["query"])
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
            
            avg_time = mean(response_times)
            self.assertLess(avg_time, self.performance_thresholds["database_query"] * 5, 
                          f"複雑クエリの平均レスポンス時間が閾値を超過: {query_case['description']}")
            
            print(f"✓ {query_case['description']}: 平均{avg_time*1000:.2f}ms")
        
        print("✓ データベースクエリレスポンス時間テスト成功")
    
    def test_rag_search_response_time(self):
        """RAG検索レスポンス時間テスト"""
        print("\n=== RAG検索レスポンス時間テスト ===")
        
        # セマンティック検索のレスポンス時間
        print("\n--- セマンティック検索レスポンス時間 ---")
        
        semantic_search_cases = [
            {"query": "所得税の計算方法", "description": "基本検索"},
            {"query": "法人税の税率と控除について詳しく教えてください", "description": "詳細検索"},
            {"query": "消費税の軽減税率対象品目と適用条件、計算例を含む包括的な情報", "description": "複雑検索"}
        ]
        
        for case in semantic_search_cases:
            response_times = []
            for i in range(3):
                start_time = time.perf_counter()
                result = self._perform_semantic_search(case["query"])
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
            
            avg_time = mean(response_times)
            self.assertLess(avg_time, self.performance_thresholds["rag_search"], 
                          f"セマンティック検索の平均レスポンス時間が閾値を超過: {case['description']}")
            
            print(f"✓ {case['description']}: 平均{avg_time*1000:.2f}ms")
        
        # キーワード検索のレスポンス時間
        print("\n--- キーワード検索レスポンス時間 ---")
        
        keyword_search_cases = [
            {"keywords": ["所得税"], "description": "単一キーワード"},
            {"keywords": ["法人税", "税率"], "description": "複数キーワード"},
            {"keywords": ["消費税", "軽減税率", "対象品目"], "description": "多数キーワード"}
        ]
        
        for case in keyword_search_cases:
            response_times = []
            for i in range(5):
                start_time = time.perf_counter()
                result = self._perform_keyword_search(case["keywords"])
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
            
            avg_time = mean(response_times)
            self.assertLess(avg_time, self.performance_thresholds["rag_search"] * 0.5, 
                          f"キーワード検索の平均レスポンス時間が閾値を超過: {case['description']}")
            
            print(f"✓ {case['description']}: 平均{avg_time*1000:.2f}ms")
        
        print("✓ RAG検索レスポンス時間テスト成功")
    
    def test_bulk_processing_response_time(self):
        """大量データ処理レスポンス時間テスト"""
        print("\n=== 大量データ処理レスポンス時間テスト ===")
        
        # 大量税計算のレスポンス時間
        print("\n--- 大量税計算レスポンス時間 ---")
        
        bulk_calculation_cases = [
            {"count": 100, "description": "100件の税計算"},
            {"count": 500, "description": "500件の税計算"},
            {"count": 1000, "description": "1000件の税計算"}
        ]
        
        for case in bulk_calculation_cases:
            # テストデータ生成
            test_data = []
            for i in range(case["count"]):
                test_data.append({
                    "income": 3000000 + (i * 10000),
                    "deductions": 480000 + (i * 1000)
                })
            
            start_time = time.perf_counter()
            results = self._bulk_calculate_income_tax(test_data)
            end_time = time.perf_counter()
            response_time = end_time - start_time
            
            self.assertLess(response_time, self.performance_thresholds["bulk_processing"], 
                          f"大量税計算の処理時間が閾値を超過: {case['description']}")
            
            per_item_time = response_time / case["count"]
            print(f"✓ {case['description']}: 総時間{response_time:.2f}s, 1件あたり{per_item_time*1000:.2f}ms")
        
        # 大量データベース挿入のレスポンス時間
        print("\n--- 大量データベース挿入レスポンス時間 ---")
        
        bulk_insert_cases = [
            {"count": 100, "description": "100件のデータ挿入"},
            {"count": 500, "description": "500件のデータ挿入"},
            {"count": 1000, "description": "1000件のデータ挿入"}
        ]
        
        for case in bulk_insert_cases:
            # テストデータ生成
            test_documents = []
            for i in range(case["count"]):
                test_documents.append({
                    "title": f"テスト文書{i}",
                    "content": f"これはテスト用の文書内容です。番号: {i}",
                    "tax_type": "income_tax",
                    "created_at": datetime.now().isoformat()
                })
            
            start_time = time.perf_counter()
            result = self._bulk_insert_documents(test_documents)
            end_time = time.perf_counter()
            response_time = end_time - start_time
            
            self.assertLess(response_time, self.performance_thresholds["bulk_processing"], 
                          f"大量データ挿入の処理時間が閾値を超過: {case['description']}")
            
            per_item_time = response_time / case["count"]
            print(f"✓ {case['description']}: 総時間{response_time:.2f}s, 1件あたり{per_item_time*1000:.2f}ms")
        
        print("✓ 大量データ処理レスポンス時間テスト成功")
    
    def test_memory_usage_monitoring(self):
        """メモリ使用量監視テスト"""
        print("\n=== メモリ使用量監視テスト ===")
        
        # 初期メモリ使用量
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        print(f"\n初期メモリ使用量: {initial_memory:.2f}MB")
        
        # 税計算でのメモリ使用量
        print("\n--- 税計算メモリ使用量 ---")
        
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        # 大量の税計算を実行
        test_data = []
        for i in range(1000):
            test_data.append({
                "income": 3000000 + (i * 10000),
                "deductions": 480000 + (i * 1000)
            })
        
        results = self._bulk_calculate_income_tax(test_data)
        
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = memory_after - memory_before
        
        self.assertLess(memory_increase, self.performance_thresholds["memory_limit"], 
                      f"税計算でのメモリ増加量が閾値を超過: {memory_increase:.2f}MB")
        
        print(f"✓ 税計算メモリ増加量: {memory_increase:.2f}MB")
        
        # RAG検索でのメモリ使用量
        print("\n--- RAG検索メモリ使用量 ---")
        
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        # 複数の検索を実行
        search_queries = [
            "所得税の計算方法について",
            "法人税の税率と控除",
            "消費税の軽減税率対象品目",
            "住民税の計算方法",
            "相続税の基礎控除額"
        ]
        
        for query in search_queries:
            result = self._perform_semantic_search(query)
        
        memory_after = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = memory_after - memory_before
        
        self.assertLess(memory_increase, self.performance_thresholds["memory_limit"], 
                      f"RAG検索でのメモリ増加量が閾値を超過: {memory_increase:.2f}MB")
        
        print(f"✓ RAG検索メモリ増加量: {memory_increase:.2f}MB")
        
        # ガベージコレクション後のメモリ使用量
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"\n最終メモリ使用量: {final_memory:.2f}MB")
        print(f"総メモリ増加量: {total_increase:.2f}MB")
        
        print("✓ メモリ使用量監視テスト成功")
    
    def test_response_time_under_load(self):
        """負荷下でのレスポンス時間テスト"""
        print("\n=== 負荷下レスポンス時間テスト ===")
        
        # CPU負荷下でのレスポンス時間
        print("\n--- CPU負荷下レスポンス時間 ---")
        
        def cpu_intensive_task():
            """CPU集約的なタスク"""
            for i in range(100000):
                _ = i ** 2
        
        # CPU負荷を生成
        cpu_threads = []
        for i in range(2):  # 2つのCPU集約的スレッド
            thread = threading.Thread(target=cpu_intensive_task)
            thread.start()
            cpu_threads.append(thread)
        
        try:
            # 負荷下での税計算レスポンス時間測定
            response_times = []
            for i in range(5):
                start_time = time.perf_counter()
                result = self._calculate_income_tax(3000000, 480000)
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
            
            avg_time = mean(response_times)
            # 負荷下では通常の2倍の時間まで許容
            self.assertLess(avg_time, self.performance_thresholds["tax_calculation"] * 2, 
                          f"CPU負荷下での税計算レスポンス時間が閾値を超過")
            
            print(f"✓ CPU負荷下での税計算: 平均{avg_time*1000:.2f}ms")
        
        finally:
            # CPU負荷スレッドの終了を待つ
            for thread in cpu_threads:
                thread.join()
        
        # メモリ負荷下でのレスポンス時間
        print("\n--- メモリ負荷下レスポンス時間 ---")
        
        # メモリ負荷を生成（大きなリストを作成）
        memory_load = [list(range(100000)) for _ in range(10)]
        
        try:
            response_times = []
            for i in range(5):
                start_time = time.perf_counter()
                result = self._calculate_income_tax(3000000, 480000)
                end_time = time.perf_counter()
                response_time = end_time - start_time
                response_times.append(response_time)
            
            avg_time = mean(response_times)
            self.assertLess(avg_time, self.performance_thresholds["tax_calculation"] * 1.5, 
                          f"メモリ負荷下での税計算レスポンス時間が閾値を超過")
            
            print(f"✓ メモリ負荷下での税計算: 平均{avg_time*1000:.2f}ms")
        
        finally:
            # メモリ負荷を解放
            del memory_load
            gc.collect()
        
        print("✓ 負荷下レスポンス時間テスト成功")
    
    # ヘルパーメソッド
    def _calculate_income_tax(self, income: float, deductions: float) -> Dict[str, Any]:
        """所得税計算ヘルパー"""
        # 簡単な所得税計算のシミュレーション
        taxable_income = max(0, income - deductions)
        
        if taxable_income <= 1950000:
            tax_rate = 0.05
            deduction = 0
        elif taxable_income <= 3300000:
            tax_rate = 0.10
            deduction = 97500
        elif taxable_income <= 6950000:
            tax_rate = 0.20
            deduction = 427500
        elif taxable_income <= 9000000:
            tax_rate = 0.23
            deduction = 636000
        elif taxable_income <= 18000000:
            tax_rate = 0.33
            deduction = 1536000
        elif taxable_income <= 40000000:
            tax_rate = 0.40
            deduction = 2796000
        else:
            tax_rate = 0.45
            deduction = 4796000
        
        tax_amount = (taxable_income * tax_rate) - deduction
        
        return {
            "taxable_income": taxable_income,
            "tax_rate": tax_rate,
            "tax_amount": max(0, tax_amount)
        }
    
    def _calculate_corporate_tax(self, revenue: float, expenses: float) -> Dict[str, Any]:
        """法人税計算ヘルパー"""
        # 簡単な法人税計算のシミュレーション
        profit = revenue - expenses
        
        if profit <= 0:
            return {"profit": profit, "tax_amount": 0}
        
        if profit <= 8000000:  # 800万円以下
            tax_rate = 0.15
        else:
            tax_rate = 0.234  # 23.4%
        
        tax_amount = profit * tax_rate
        
        return {
            "profit": profit,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount
        }
    
    def _calculate_consumption_tax(self, amount: float, rate: float) -> Dict[str, Any]:
        """消費税計算ヘルパー"""
        # 簡単な消費税計算のシミュレーション
        tax_amount = amount * rate
        total_amount = amount + tax_amount
        
        return {
            "base_amount": amount,
            "tax_rate": rate,
            "tax_amount": tax_amount,
            "total_amount": total_amount
        }
    
    def _execute_database_query(self, query: str) -> List[Dict[str, Any]]:
        """データベースクエリ実行ヘルパー"""
        # データベースクエリのシミュレーション
        time.sleep(0.01)  # 10ms のシミュレーション遅延
        
        # クエリに応じたモックデータを返す
        if "LIMIT 10" in query:
            return [{"id": i, "title": f"Document {i}"} for i in range(10)]
        elif "LIMIT 100" in query:
            return [{"id": i, "title": f"Document {i}"} for i in range(100)]
        elif "LIMIT 1000" in query:
            return [{"id": i, "title": f"Document {i}"} for i in range(1000)]
        else:
            return [{"id": 1, "title": "Sample Document"}]
    
    def _perform_semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """セマンティック検索ヘルパー"""
        # セマンティック検索のシミュレーション
        time.sleep(0.1)  # 100ms のシミュレーション遅延
        
        return [
            {
                "id": 1,
                "title": "関連文書1",
                "content": f"'{query}'に関連する内容です。",
                "score": 0.95
            },
            {
                "id": 2,
                "title": "関連文書2",
                "content": f"'{query}'についての詳細情報です。",
                "score": 0.87
            }
        ]
    
    def _perform_keyword_search(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """キーワード検索ヘルパー"""
        # キーワード検索のシミュレーション
        time.sleep(0.02)  # 20ms のシミュレーション遅延
        
        return [
            {
                "id": i,
                "title": f"文書{i}",
                "content": f"キーワード {', '.join(keywords)} を含む文書です。",
                "matched_keywords": keywords
            }
            for i in range(len(keywords) * 2)
        ]
    
    def _bulk_calculate_income_tax(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """大量所得税計算ヘルパー"""
        results = []
        for data in data_list:
            result = self._calculate_income_tax(data["income"], data["deductions"])
            results.append(result)
        return results
    
    def _bulk_insert_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """大量文書挿入ヘルパー"""
        # 大量挿入のシミュレーション
        time.sleep(len(documents) * 0.001)  # 1件あたり1ms のシミュレーション
        
        return {
            "inserted_count": len(documents),
            "success": True
        }


if __name__ == "__main__":
    unittest.main(verbosity=2)