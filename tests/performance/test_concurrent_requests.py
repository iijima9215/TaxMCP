#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaxMCP パフォーマンステスト - 同時リクエスト処理

このモジュールは、TaxMCPサーバーの同時リクエスト処理能力をテストします。

主なテスト項目:
- 同時税計算リクエスト処理
- 同時データベースアクセス
- 同時RAG検索処理
- スレッドプールの効率性
- リソース競合の検出
- スループットの測定
"""

import unittest
import time
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from statistics import mean, median, stdev
import psutil
import gc

from tests.utils.test_config import TaxMCPTestCase
from tests.utils.performance_helpers import PerformanceTestMixin
from tests.utils.test_data_generator import TestDataGenerator


class TestConcurrentRequests(TaxMCPTestCase, PerformanceTestMixin):
    """同時リクエスト処理テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.data_generator = TestDataGenerator()
        self.max_workers = 10
        self.performance_thresholds = {
            "concurrent_tax_calculation": 2.0,  # 2秒
            "concurrent_database_access": 1.0,  # 1秒
            "concurrent_rag_search": 3.0,       # 3秒
            "throughput_min": 50,               # 最小スループット（req/sec）
            "error_rate_max": 0.05              # 最大エラー率（5%）
        }
        self.results_queue = queue.Queue()
        print(f"\n{'='*50}")
        print(f"テスト開始: {self._testMethodName}")
        print(f"{'='*50}")
    
    def tearDown(self):
        """テストクリーンアップ"""
        super().tearDown()
        gc.collect()
        print(f"\nテスト完了: {self._testMethodName}")
    
    def test_concurrent_tax_calculations(self):
        """同時税計算処理テスト"""
        print("\n=== 同時税計算処理テスト ===")
        
        # 所得税の同時計算
        print("\n--- 所得税同時計算 ---")
        
        concurrent_levels = [5, 10, 20]
        
        for concurrent_count in concurrent_levels:
            print(f"\n同時実行数: {concurrent_count}")
            
            # テストデータ準備
            test_cases = []
            for i in range(concurrent_count):
                test_cases.append({
                    "income": 3000000 + (i * 100000),
                    "deductions": 480000 + (i * 10000),
                    "case_id": i
                })
            
            start_time = time.perf_counter()
            results = []
            errors = []
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 全ての税計算を同時実行
                future_to_case = {
                    executor.submit(self._calculate_income_tax_with_timing, case): case
                    for case in test_cases
                }
                
                for future in as_completed(future_to_case):
                    case = future_to_case[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        errors.append({"case_id": case["case_id"], "error": str(e)})
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            # 結果分析
            success_count = len(results)
            error_count = len(errors)
            error_rate = error_count / concurrent_count
            throughput = success_count / total_time
            
            response_times = [r["response_time"] for r in results]
            avg_response_time = mean(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            
            # アサーション
            self.assertLess(total_time, self.performance_thresholds["concurrent_tax_calculation"], 
                          f"同時税計算の総処理時間が閾値を超過: {concurrent_count}件")
            self.assertLess(error_rate, self.performance_thresholds["error_rate_max"], 
                          f"同時税計算のエラー率が閾値を超過: {concurrent_count}件")
            
            print(f"✓ 総処理時間: {total_time:.2f}s")
            print(f"✓ 成功: {success_count}件, エラー: {error_count}件")
            print(f"✓ エラー率: {error_rate:.2%}")
            print(f"✓ スループット: {throughput:.1f} req/sec")
            print(f"✓ 平均レスポンス時間: {avg_response_time*1000:.2f}ms")
            print(f"✓ 最大レスポンス時間: {max_response_time*1000:.2f}ms")
        
        # 法人税の同時計算
        print("\n--- 法人税同時計算 ---")
        
        concurrent_count = 15
        test_cases = []
        for i in range(concurrent_count):
            test_cases.append({
                "revenue": 100000000 + (i * 10000000),
                "expenses": 80000000 + (i * 8000000),
                "case_id": i
            })
        
        start_time = time.perf_counter()
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_case = {
                executor.submit(self._calculate_corporate_tax_with_timing, case): case
                for case in test_cases
            }
            
            for future in as_completed(future_to_case):
                case = future_to_case[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    errors.append({"case_id": case["case_id"], "error": str(e)})
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        success_count = len(results)
        error_count = len(errors)
        error_rate = error_count / concurrent_count
        throughput = success_count / total_time
        
        self.assertLess(total_time, self.performance_thresholds["concurrent_tax_calculation"], 
                      f"法人税同時計算の総処理時間が閾値を超過")
        self.assertLess(error_rate, self.performance_thresholds["error_rate_max"], 
                      f"法人税同時計算のエラー率が閾値を超過")
        
        print(f"✓ 法人税同時計算 - 総処理時間: {total_time:.2f}s, スループット: {throughput:.1f} req/sec")
        
        print("✓ 同時税計算処理テスト成功")
    
    def test_concurrent_database_access(self):
        """同時データベースアクセステスト"""
        print("\n=== 同時データベースアクセステスト ===")
        
        # 読み取り専用の同時アクセス
        print("\n--- 読み取り専用同時アクセス ---")
        
        concurrent_count = 20
        queries = [
            "SELECT * FROM tax_documents WHERE tax_type = 'income_tax' LIMIT 10",
            "SELECT * FROM tax_documents WHERE tax_type = 'corporate_tax' LIMIT 10",
            "SELECT * FROM tax_documents WHERE tax_type = 'consumption_tax' LIMIT 10",
            "SELECT COUNT(*) FROM tax_documents GROUP BY tax_type",
            "SELECT * FROM document_metadata WHERE created_at > '2024-01-01' LIMIT 5"
        ]
        
        test_cases = []
        for i in range(concurrent_count):
            test_cases.append({
                "query": queries[i % len(queries)],
                "case_id": i
            })
        
        start_time = time.perf_counter()
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_case = {
                executor.submit(self._execute_database_query_with_timing, case["query"]): case
                for case in test_cases
            }
            
            for future in as_completed(future_to_case):
                case = future_to_case[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    errors.append({"case_id": case["case_id"], "error": str(e)})
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        success_count = len(results)
        error_count = len(errors)
        error_rate = error_count / concurrent_count
        throughput = success_count / total_time
        
        self.assertLess(total_time, self.performance_thresholds["concurrent_database_access"], 
                      f"同時データベース読み取りの総処理時間が閾値を超過")
        self.assertLess(error_rate, self.performance_thresholds["error_rate_max"], 
                      f"同時データベース読み取りのエラー率が閾値を超過")
        
        print(f"✓ 読み取り専用同時アクセス - 総処理時間: {total_time:.2f}s, スループット: {throughput:.1f} req/sec")
        
        # 読み書き混合の同時アクセス
        print("\n--- 読み書き混合同時アクセス ---")
        
        concurrent_count = 15
        operations = []
        
        # 読み取り操作（70%）
        for i in range(int(concurrent_count * 0.7)):
            operations.append({
                "type": "read",
                "query": "SELECT * FROM tax_documents LIMIT 5",
                "case_id": f"read_{i}"
            })
        
        # 書き込み操作（30%）
        for i in range(int(concurrent_count * 0.3)):
            operations.append({
                "type": "write",
                "data": {
                    "title": f"テスト文書_{i}",
                    "content": f"同時書き込みテスト用文書 {i}",
                    "tax_type": "income_tax"
                },
                "case_id": f"write_{i}"
            })
        
        start_time = time.perf_counter()
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for operation in operations:
                if operation["type"] == "read":
                    future = executor.submit(self._execute_database_query_with_timing, operation["query"])
                else:
                    future = executor.submit(self._insert_document_with_timing, operation["data"])
                futures.append((future, operation))
            
            for future, operation in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    errors.append({"case_id": operation["case_id"], "error": str(e)})
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        success_count = len(results)
        error_count = len(errors)
        error_rate = error_count / concurrent_count
        throughput = success_count / total_time
        
        self.assertLess(total_time, self.performance_thresholds["concurrent_database_access"] * 1.5, 
                      f"読み書き混合同時アクセスの総処理時間が閾値を超過")
        self.assertLess(error_rate, self.performance_thresholds["error_rate_max"], 
                      f"読み書き混合同時アクセスのエラー率が閾値を超過")
        
        print(f"✓ 読み書き混合同時アクセス - 総処理時間: {total_time:.2f}s, スループット: {throughput:.1f} req/sec")
        
        print("✓ 同時データベースアクセステスト成功")
    
    def test_concurrent_rag_search(self):
        """同時RAG検索テスト"""
        print("\n=== 同時RAG検索テスト ===")
        
        # セマンティック検索の同時実行
        print("\n--- セマンティック検索同時実行 ---")
        
        search_queries = [
            "所得税の計算方法について教えてください",
            "法人税の税率と控除について詳しく",
            "消費税の軽減税率対象品目は何ですか",
            "住民税の計算方法と納付時期",
            "相続税の基礎控除額と計算例",
            "贈与税の非課税枠と特例について",
            "固定資産税の評価方法と軽減措置",
            "事業税の計算方法と申告期限",
            "印紙税の課税対象と税額表",
            "登録免許税の計算方法と軽減措置"
        ]
        
        concurrent_count = len(search_queries)
        test_cases = []
        for i, query in enumerate(search_queries):
            test_cases.append({
                "query": query,
                "case_id": i
            })
        
        start_time = time.perf_counter()
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_case = {
                executor.submit(self._perform_semantic_search_with_timing, case["query"]): case
                for case in test_cases
            }
            
            for future in as_completed(future_to_case):
                case = future_to_case[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    errors.append({"case_id": case["case_id"], "error": str(e)})
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        success_count = len(results)
        error_count = len(errors)
        error_rate = error_count / concurrent_count
        throughput = success_count / total_time
        
        response_times = [r["response_time"] for r in results]
        avg_response_time = mean(response_times) if response_times else 0
        
        self.assertLess(total_time, self.performance_thresholds["concurrent_rag_search"], 
                      f"同時セマンティック検索の総処理時間が閾値を超過")
        self.assertLess(error_rate, self.performance_thresholds["error_rate_max"], 
                      f"同時セマンティック検索のエラー率が閾値を超過")
        
        print(f"✓ セマンティック検索同時実行 - 総処理時間: {total_time:.2f}s")
        print(f"✓ スループット: {throughput:.1f} req/sec")
        print(f"✓ 平均レスポンス時間: {avg_response_time*1000:.2f}ms")
        
        # キーワード検索の同時実行
        print("\n--- キーワード検索同時実行 ---")
        
        keyword_sets = [
            ["所得税", "計算"],
            ["法人税", "税率"],
            ["消費税", "軽減税率"],
            ["住民税", "納付"],
            ["相続税", "控除"],
            ["贈与税", "非課税"],
            ["固定資産税", "評価"],
            ["事業税", "申告"],
            ["印紙税", "課税"],
            ["登録免許税", "軽減"]
        ]
        
        concurrent_count = len(keyword_sets)
        test_cases = []
        for i, keywords in enumerate(keyword_sets):
            test_cases.append({
                "keywords": keywords,
                "case_id": i
            })
        
        start_time = time.perf_counter()
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_case = {
                executor.submit(self._perform_keyword_search_with_timing, case["keywords"]): case
                for case in test_cases
            }
            
            for future in as_completed(future_to_case):
                case = future_to_case[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    errors.append({"case_id": case["case_id"], "error": str(e)})
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        success_count = len(results)
        error_count = len(errors)
        error_rate = error_count / concurrent_count
        throughput = success_count / total_time
        
        self.assertLess(total_time, self.performance_thresholds["concurrent_rag_search"] * 0.5, 
                      f"同時キーワード検索の総処理時間が閾値を超過")
        self.assertLess(error_rate, self.performance_thresholds["error_rate_max"], 
                      f"同時キーワード検索のエラー率が閾値を超過")
        
        print(f"✓ キーワード検索同時実行 - 総処理時間: {total_time:.2f}s, スループット: {throughput:.1f} req/sec")
        
        print("✓ 同時RAG検索テスト成功")
    
    def test_mixed_workload_performance(self):
        """混合ワークロードパフォーマンステスト"""
        print("\n=== 混合ワークロードパフォーマンステスト ===")
        
        # 税計算、データベースアクセス、RAG検索を混合して実行
        print("\n--- 混合ワークロード実行 ---")
        
        concurrent_count = 30
        operations = []
        
        # 税計算操作（40%）
        for i in range(int(concurrent_count * 0.4)):
            operations.append({
                "type": "tax_calculation",
                "data": {
                    "income": 3000000 + (i * 100000),
                    "deductions": 480000 + (i * 10000)
                },
                "case_id": f"tax_{i}"
            })
        
        # データベースアクセス（30%）
        for i in range(int(concurrent_count * 0.3)):
            operations.append({
                "type": "database_query",
                "query": "SELECT * FROM tax_documents WHERE tax_type = 'income_tax' LIMIT 5",
                "case_id": f"db_{i}"
            })
        
        # RAG検索（30%）
        search_queries = [
            "所得税について", "法人税について", "消費税について",
            "住民税について", "相続税について", "贈与税について",
            "固定資産税について", "事業税について", "印紙税について"
        ]
        for i in range(int(concurrent_count * 0.3)):
            operations.append({
                "type": "rag_search",
                "query": search_queries[i % len(search_queries)],
                "case_id": f"rag_{i}"
            })
        
        # 操作をシャッフルして実行順序をランダム化
        import random
        random.shuffle(operations)
        
        start_time = time.perf_counter()
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for operation in operations:
                if operation["type"] == "tax_calculation":
                    future = executor.submit(
                        self._calculate_income_tax_with_timing, 
                        operation["data"]
                    )
                elif operation["type"] == "database_query":
                    future = executor.submit(
                        self._execute_database_query_with_timing, 
                        operation["query"]
                    )
                else:  # rag_search
                    future = executor.submit(
                        self._perform_semantic_search_with_timing, 
                        operation["query"]
                    )
                
                futures.append((future, operation))
            
            for future, operation in futures:
                try:
                    result = future.result()
                    result["operation_type"] = operation["type"]
                    results.append(result)
                except Exception as e:
                    errors.append({
                        "case_id": operation["case_id"], 
                        "operation_type": operation["type"],
                        "error": str(e)
                    })
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # 結果分析
        success_count = len(results)
        error_count = len(errors)
        error_rate = error_count / concurrent_count
        throughput = success_count / total_time
        
        # 操作タイプ別の分析
        tax_results = [r for r in results if r["operation_type"] == "tax_calculation"]
        db_results = [r for r in results if r["operation_type"] == "database_query"]
        rag_results = [r for r in results if r["operation_type"] == "rag_search"]
        
        tax_avg_time = mean([r["response_time"] for r in tax_results]) if tax_results else 0
        db_avg_time = mean([r["response_time"] for r in db_results]) if db_results else 0
        rag_avg_time = mean([r["response_time"] for r in rag_results]) if rag_results else 0
        
        # アサーション
        self.assertLess(error_rate, self.performance_thresholds["error_rate_max"], 
                      f"混合ワークロードのエラー率が閾値を超過")
        self.assertGreater(throughput, self.performance_thresholds["throughput_min"], 
                         f"混合ワークロードのスループットが閾値を下回る")
        
        print(f"✓ 混合ワークロード実行結果:")
        print(f"  - 総処理時間: {total_time:.2f}s")
        print(f"  - 成功: {success_count}件, エラー: {error_count}件")
        print(f"  - エラー率: {error_rate:.2%}")
        print(f"  - 総スループット: {throughput:.1f} req/sec")
        print(f"  - 税計算平均時間: {tax_avg_time*1000:.2f}ms ({len(tax_results)}件)")
        print(f"  - DB平均時間: {db_avg_time*1000:.2f}ms ({len(db_results)}件)")
        print(f"  - RAG平均時間: {rag_avg_time*1000:.2f}ms ({len(rag_results)}件)")
        
        print("✓ 混合ワークロードパフォーマンステスト成功")
    
    def test_resource_contention(self):
        """リソース競合テスト"""
        print("\n=== リソース競合テスト ===")
        
        # CPU集約的タスクとI/O集約的タスクの混合実行
        print("\n--- CPU/IO混合負荷テスト ---")
        
        concurrent_count = 20
        operations = []
        
        # CPU集約的操作（50%）
        for i in range(int(concurrent_count * 0.5)):
            operations.append({
                "type": "cpu_intensive",
                "iterations": 100000,
                "case_id": f"cpu_{i}"
            })
        
        # I/O集約的操作（50%）
        for i in range(int(concurrent_count * 0.5)):
            operations.append({
                "type": "io_intensive",
                "query": "SELECT * FROM tax_documents LIMIT 100",
                "case_id": f"io_{i}"
            })
        
        # メモリ使用量監視
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        start_time = time.perf_counter()
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for operation in operations:
                if operation["type"] == "cpu_intensive":
                    future = executor.submit(
                        self._cpu_intensive_task_with_timing, 
                        operation["iterations"]
                    )
                else:  # io_intensive
                    future = executor.submit(
                        self._execute_database_query_with_timing, 
                        operation["query"]
                    )
                
                futures.append((future, operation))
            
            for future, operation in futures:
                try:
                    result = future.result()
                    result["operation_type"] = operation["type"]
                    results.append(result)
                except Exception as e:
                    errors.append({
                        "case_id": operation["case_id"], 
                        "operation_type": operation["type"],
                        "error": str(e)
                    })
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # 結果分析
        success_count = len(results)
        error_count = len(errors)
        error_rate = error_count / concurrent_count
        
        cpu_results = [r for r in results if r["operation_type"] == "cpu_intensive"]
        io_results = [r for r in results if r["operation_type"] == "io_intensive"]
        
        cpu_avg_time = mean([r["response_time"] for r in cpu_results]) if cpu_results else 0
        io_avg_time = mean([r["response_time"] for r in io_results]) if io_results else 0
        
        # アサーション
        self.assertLess(error_rate, self.performance_thresholds["error_rate_max"], 
                      f"リソース競合テストのエラー率が閾値を超過")
        self.assertLess(memory_increase, 100, 
                      f"リソース競合テストでのメモリ増加量が閾値を超過: {memory_increase:.2f}MB")
        
        print(f"✓ CPU/IO混合負荷テスト結果:")
        print(f"  - 総処理時間: {total_time:.2f}s")
        print(f"  - 成功: {success_count}件, エラー: {error_count}件")
        print(f"  - エラー率: {error_rate:.2%}")
        print(f"  - CPU集約的タスク平均時間: {cpu_avg_time*1000:.2f}ms ({len(cpu_results)}件)")
        print(f"  - I/O集約的タスク平均時間: {io_avg_time*1000:.2f}ms ({len(io_results)}件)")
        print(f"  - メモリ増加量: {memory_increase:.2f}MB")
        
        print("✓ リソース競合テスト成功")
    
    # ヘルパーメソッド
    def _calculate_income_tax_with_timing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """タイミング付き所得税計算ヘルパー"""
        start_time = time.perf_counter()
        
        # 所得税計算のシミュレーション
        income = data["income"]
        deductions = data["deductions"]
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
        else:
            tax_rate = 0.23
            deduction = 636000
        
        tax_amount = (taxable_income * tax_rate) - deduction
        
        # 計算時間をシミュレート
        time.sleep(0.01)  # 10ms
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        return {
            "taxable_income": taxable_income,
            "tax_amount": max(0, tax_amount),
            "response_time": response_time
        }
    
    def _calculate_corporate_tax_with_timing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """タイミング付き法人税計算ヘルパー"""
        start_time = time.perf_counter()
        
        revenue = data["revenue"]
        expenses = data["expenses"]
        profit = revenue - expenses
        
        if profit <= 0:
            tax_amount = 0
        elif profit <= 8000000:
            tax_amount = profit * 0.15
        else:
            tax_amount = profit * 0.234
        
        time.sleep(0.015)  # 15ms
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        return {
            "profit": profit,
            "tax_amount": tax_amount,
            "response_time": response_time
        }
    
    def _execute_database_query_with_timing(self, query: str) -> Dict[str, Any]:
        """タイミング付きデータベースクエリ実行ヘルパー"""
        start_time = time.perf_counter()
        
        # データベースクエリのシミュレーション
        time.sleep(0.02)  # 20ms
        
        # クエリに応じたモックデータを返す
        if "LIMIT 5" in query:
            result_count = 5
        elif "LIMIT 10" in query:
            result_count = 10
        elif "LIMIT 100" in query:
            result_count = 100
        else:
            result_count = 1
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        return {
            "result_count": result_count,
            "response_time": response_time
        }
    
    def _insert_document_with_timing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """タイミング付き文書挿入ヘルパー"""
        start_time = time.perf_counter()
        
        # 文書挿入のシミュレーション
        time.sleep(0.03)  # 30ms
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        return {
            "inserted_id": f"doc_{int(time.time() * 1000000)}",
            "response_time": response_time
        }
    
    def _perform_semantic_search_with_timing(self, query: str) -> Dict[str, Any]:
        """タイミング付きセマンティック検索ヘルパー"""
        start_time = time.perf_counter()
        
        # セマンティック検索のシミュレーション
        time.sleep(0.1)  # 100ms
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        return {
            "query": query,
            "result_count": 5,
            "response_time": response_time
        }
    
    def _perform_keyword_search_with_timing(self, keywords: List[str]) -> Dict[str, Any]:
        """タイミング付きキーワード検索ヘルパー"""
        start_time = time.perf_counter()
        
        # キーワード検索のシミュレーション
        time.sleep(0.02)  # 20ms
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        return {
            "keywords": keywords,
            "result_count": len(keywords) * 3,
            "response_time": response_time
        }
    
    def _cpu_intensive_task_with_timing(self, iterations: int) -> Dict[str, Any]:
        """タイミング付きCPU集約的タスクヘルパー"""
        start_time = time.perf_counter()
        
        # CPU集約的な計算
        result = 0
        for i in range(iterations):
            result += i ** 2
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        return {
            "iterations": iterations,
            "result": result,
            "response_time": response_time
        }


if __name__ == "__main__":
    unittest.main(verbosity=2)