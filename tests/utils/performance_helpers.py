"""パフォーマンステスト用ヘルパークラス"""
import time
import threading
import asyncio
from typing import List, Dict, Any, Callable
import statistics


class PerformanceTestMixin:
    """パフォーマンステスト用のミックスインクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.performance_results = []
        self.start_time = None
        self.end_time = None
    
    def start_timer(self):
        """タイマー開始"""
        self.start_time = time.time()
    
    def stop_timer(self):
        """タイマー停止"""
        self.end_time = time.time()
        return self.end_time - self.start_time if self.start_time else 0
    
    def measure_execution_time(self, func: Callable, *args, **kwargs) -> tuple:
        """関数の実行時間を測定
        
        Args:
            func: 測定対象の関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            tuple: (実行結果, 実行時間)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.performance_results.append({
            'function': func.__name__,
            'execution_time': execution_time,
            'timestamp': start_time
        })
        
        return result, execution_time
    
    async def measure_async_execution_time(self, coro) -> tuple:
        """非同期関数の実行時間を測定
        
        Args:
            coro: 測定対象のコルーチン
            
        Returns:
            tuple: (実行結果, 実行時間)
        """
        start_time = time.time()
        result = await coro
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.performance_results.append({
            'function': 'async_function',
            'execution_time': execution_time,
            'timestamp': start_time
        })
        
        return result, execution_time
    
    def run_concurrent_requests(self, func: Callable, request_count: int, *args, **kwargs) -> List[Dict[str, Any]]:
        """同時リクエストを実行
        
        Args:
            func: 実行する関数
            request_count: リクエスト数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            List[Dict]: 実行結果のリスト
        """
        results = []
        threads = []
        
        def execute_request(request_id):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                results.append({
                    'request_id': request_id,
                    'result': result,
                    'execution_time': end_time - start_time,
                    'success': True,
                    'error': None
                })
            except Exception as e:
                end_time = time.time()
                results.append({
                    'request_id': request_id,
                    'result': None,
                    'execution_time': end_time - start_time,
                    'success': False,
                    'error': str(e)
                })
        
        # スレッドを作成して実行
        for i in range(request_count):
            thread = threading.Thread(target=execute_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # すべてのスレッドの完了を待機
        for thread in threads:
            thread.join()
        
        return results
    
    async def run_async_concurrent_requests(self, coro_func: Callable, request_count: int, *args, **kwargs) -> List[Dict[str, Any]]:
        """非同期同時リクエストを実行
        
        Args:
            coro_func: 実行する非同期関数
            request_count: リクエスト数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            List[Dict]: 実行結果のリスト
        """
        async def execute_async_request(request_id):
            start_time = time.time()
            try:
                result = await coro_func(*args, **kwargs)
                end_time = time.time()
                return {
                    'request_id': request_id,
                    'result': result,
                    'execution_time': end_time - start_time,
                    'success': True,
                    'error': None
                }
            except Exception as e:
                end_time = time.time()
                return {
                    'request_id': request_id,
                    'result': None,
                    'execution_time': end_time - start_time,
                    'success': False,
                    'error': str(e)
                }
        
        # 非同期タスクを作成して実行
        tasks = [execute_async_request(i) for i in range(request_count)]
        results = await asyncio.gather(*tasks)
        
        return results
    
    def calculate_performance_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """パフォーマンス統計を計算
        
        Args:
            results: 実行結果のリスト
            
        Returns:
            Dict: パフォーマンス統計
        """
        execution_times = [r['execution_time'] for r in results if r['success']]
        success_count = sum(1 for r in results if r['success'])
        error_count = len(results) - success_count
        
        if not execution_times:
            return {
                'total_requests': len(results),
                'successful_requests': success_count,
                'failed_requests': error_count,
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'min_response_time': 0.0,
                'max_response_time': 0.0,
                'median_response_time': 0.0,
                'std_dev_response_time': 0.0
            }
        
        return {
            'total_requests': len(results),
            'successful_requests': success_count,
            'failed_requests': error_count,
            'success_rate': success_count / len(results),
            'avg_response_time': statistics.mean(execution_times),
            'min_response_time': min(execution_times),
            'max_response_time': max(execution_times),
            'median_response_time': statistics.median(execution_times),
            'std_dev_response_time': statistics.stdev(execution_times) if len(execution_times) > 1 else 0.0
        }
    
    def assert_performance_threshold(self, execution_time: float, threshold: float, message: str = None):
        """パフォーマンス閾値をアサート
        
        Args:
            execution_time: 実行時間
            threshold: 閾値
            message: エラーメッセージ
        """
        if message is None:
            message = f"実行時間 {execution_time:.3f}秒 が閾値 {threshold:.3f}秒 を超過しました"
        
        self.assertLessEqual(execution_time, threshold, message)
    
    def assert_success_rate(self, results: List[Dict[str, Any]], min_success_rate: float, message: str = None):
        """成功率をアサート
        
        Args:
            results: 実行結果のリスト
            min_success_rate: 最小成功率
            message: エラーメッセージ
        """
        stats = self.calculate_performance_stats(results)
        success_rate = stats['success_rate']
        
        if message is None:
            message = f"成功率 {success_rate:.2%} が最小成功率 {min_success_rate:.2%} を下回りました"
        
        self.assertGreaterEqual(success_rate, min_success_rate, message)
    
    def log_performance_results(self, results: List[Dict[str, Any]], test_name: str = None):
        """パフォーマンス結果をログ出力
        
        Args:
            results: 実行結果のリスト
            test_name: テスト名
        """
        stats = self.calculate_performance_stats(results)
        
        print(f"\n=== パフォーマンステスト結果 {test_name or ''} ===")
        print(f"総リクエスト数: {stats['total_requests']}")
        print(f"成功リクエスト数: {stats['successful_requests']}")
        print(f"失敗リクエスト数: {stats['failed_requests']}")
        print(f"成功率: {stats['success_rate']:.2%}")
        print(f"平均レスポンス時間: {stats['avg_response_time']:.3f}秒")
        print(f"最小レスポンス時間: {stats['min_response_time']:.3f}秒")
        print(f"最大レスポンス時間: {stats['max_response_time']:.3f}秒")
        print(f"中央値レスポンス時間: {stats['median_response_time']:.3f}秒")
        print(f"標準偏差: {stats['std_dev_response_time']:.3f}秒")
        print("=" * 50)