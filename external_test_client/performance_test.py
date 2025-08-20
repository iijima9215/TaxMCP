#!/usr/bin/env python3
"""
外部テスト環境用パフォーマンステストクライアント
同時リクエスト処理とレスポンス時間を測定します。
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import statistics
from typing import Dict, Any, List, Tuple
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import logging

# 現在のディレクトリから.envを読み込み
load_dotenv()

class PerformanceTestClient:
    """パフォーマンステスト用クライアント"""
    
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'https://taxmcp.ami-j2.com')
        self.api_version = os.getenv('API_VERSION', 'v1')
        self.timeout = int(os.getenv('TIMEOUT', '30'))
        self.ssl_verify = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
        
        # パフォーマンステスト設定
        self.concurrent_requests = int(os.getenv('CONCURRENT_REQUESTS', '10'))
        self.max_response_time = float(os.getenv('MAX_RESPONSE_TIME', '5.0'))
        self.test_duration = int(os.getenv('TEST_DURATION', '60'))  # 秒
        
        # 認証情報
        self.api_key = os.getenv('API_KEY')
        
        # ログ設定
        self.setup_logging()
        
        # 結果保存用
        self.results = []
    
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('performance_test.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_headers(self) -> Dict[str, str]:
        """リクエストヘッダーを取得"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TaxMCP-Performance-Test-Client/1.0'
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        return headers
    
    async def single_request_test(self, session: aiohttp.ClientSession, test_id: int) -> Dict[str, Any]:
        """単一リクエストテスト"""
        start_time = time.time()
        
        try:
            # 個人所得税計算のテストリクエスト
            url = f"{self.base_url}/api/{self.api_version}/calculate/individual"
            test_data = {
                "income": 5000000 + (test_id * 1000),  # テストIDで少し変化させる
                "deductions": 480000,
                "tax_year": 2025,
                "prefecture": "東京都",
                "city": "新宿区"
            }
            
            async with session.post(
                url, 
                json=test_data, 
                headers=self.get_headers()
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                result = {
                    "test_id": test_id,
                    "status_code": response.status,
                    "response_time": response_time,
                    "success": response.status == 200,
                    "timestamp": datetime.now().isoformat(),
                    "url": url
                }
                
                if response.status == 200:
                    response_data = await response.json()
                    result["response_size"] = len(json.dumps(response_data))
                else:
                    result["error"] = await response.text()
                
                return result
                
        except Exception as e:
            end_time = time.time()
            return {
                "test_id": test_id,
                "status_code": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "url": url
            }
    
    async def concurrent_load_test(self) -> List[Dict[str, Any]]:
        """同時負荷テスト"""
        self.logger.info(f"同時負荷テスト開始: {self.concurrent_requests}並行リクエスト")
        
        connector = aiohttp.TCPConnector(
            ssl=self.ssl_verify,
            limit=self.concurrent_requests * 2,
            limit_per_host=self.concurrent_requests
        )
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            # 同時リクエスト実行
            tasks = [
                self.single_request_test(session, i)
                for i in range(self.concurrent_requests)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 例外処理
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "test_id": i,
                        "status_code": 0,
                        "response_time": 0,
                        "success": False,
                        "error": str(result),
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
    
    async def sustained_load_test(self) -> List[Dict[str, Any]]:
        """持続負荷テスト"""
        self.logger.info(f"持続負荷テスト開始: {self.test_duration}秒間")
        
        all_results = []
        start_time = time.time()
        test_round = 0
        
        while time.time() - start_time < self.test_duration:
            test_round += 1
            self.logger.info(f"テストラウンド {test_round}")
            
            round_results = await self.concurrent_load_test()
            all_results.extend(round_results)
            
            # 短い休憩
            await asyncio.sleep(1)
        
        self.logger.info(f"持続負荷テスト完了: {len(all_results)}リクエスト実行")
        return all_results
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """結果分析"""
        if not results:
            return {"error": "結果データがありません"}
        
        # 基本統計
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r["success"])
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests) * 100
        
        # レスポンス時間統計
        response_times = [r["response_time"] for r in results if r["success"]]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # パーセンタイル計算
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
            p99_response_time = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        # エラー分析
        error_types = {}
        for result in results:
            if not result["success"]:
                error_key = result.get("error", f"HTTP {result['status_code']}")
                error_types[error_key] = error_types.get(error_key, 0) + 1
        
        # スループット計算
        if results:
            test_duration = max(r["timestamp"] for r in results) - min(r["timestamp"] for r in results)
            # ISO形式の時間文字列を解析
            start_dt = datetime.fromisoformat(min(r["timestamp"] for r in results).replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(max(r["timestamp"] for r in results).replace('Z', '+00:00'))
            duration_seconds = (end_dt - start_dt).total_seconds()
            throughput = successful_requests / duration_seconds if duration_seconds > 0 else 0
        else:
            throughput = 0
        
        analysis = {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate_percent": round(success_rate, 2),
                "throughput_rps": round(throughput, 2)
            },
            "response_times": {
                "average_ms": round(avg_response_time * 1000, 2),
                "median_ms": round(median_response_time * 1000, 2),
                "min_ms": round(min_response_time * 1000, 2),
                "max_ms": round(max_response_time * 1000, 2),
                "p95_ms": round(p95_response_time * 1000, 2),
                "p99_ms": round(p99_response_time * 1000, 2)
            },
            "performance_assessment": {
                "meets_sla": avg_response_time <= self.max_response_time,
                "max_response_time_sla": self.max_response_time,
                "slow_requests": sum(1 for t in response_times if t > self.max_response_time)
            },
            "errors": error_types
        }
        
        return analysis
    
    def generate_report(self, analysis: Dict[str, Any], results: List[Dict[str, Any]]):
        """レポート生成"""
        self.logger.info("\n=== パフォーマンステスト結果レポート ===")
        
        # サマリー
        summary = analysis["summary"]
        self.logger.info(f"総リクエスト数: {summary['total_requests']}")
        self.logger.info(f"成功リクエスト数: {summary['successful_requests']}")
        self.logger.info(f"失敗リクエスト数: {summary['failed_requests']}")
        self.logger.info(f"成功率: {summary['success_rate_percent']}%")
        self.logger.info(f"スループット: {summary['throughput_rps']} RPS")
        
        # レスポンス時間
        rt = analysis["response_times"]
        self.logger.info(f"\n--- レスポンス時間統計 ---")
        self.logger.info(f"平均: {rt['average_ms']}ms")
        self.logger.info(f"中央値: {rt['median_ms']}ms")
        self.logger.info(f"最小: {rt['min_ms']}ms")
        self.logger.info(f"最大: {rt['max_ms']}ms")
        self.logger.info(f"95パーセンタイル: {rt['p95_ms']}ms")
        self.logger.info(f"99パーセンタイル: {rt['p99_ms']}ms")
        
        # パフォーマンス評価
        perf = analysis["performance_assessment"]
        self.logger.info(f"\n--- パフォーマンス評価 ---")
        self.logger.info(f"SLA達成: {'✓' if perf['meets_sla'] else '✗'}")
        self.logger.info(f"SLA基準: {perf['max_response_time_sla']}秒")
        self.logger.info(f"SLA違反リクエスト数: {perf['slow_requests']}")
        
        # エラー詳細
        if analysis["errors"]:
            self.logger.info(f"\n--- エラー詳細 ---")
            for error_type, count in analysis["errors"].items():
                self.logger.info(f"{error_type}: {count}件")
        
        # 結果をファイルに保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 詳細結果
        results_file = f"performance_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "analysis": analysis,
                "raw_results": results,
                "test_config": {
                    "base_url": self.base_url,
                    "concurrent_requests": self.concurrent_requests,
                    "max_response_time": self.max_response_time,
                    "test_duration": self.test_duration
                }
            }, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n詳細結果を保存: {results_file}")
    
    async def run_performance_test(self, test_type: str = "concurrent"):
        """パフォーマンステスト実行"""
        self.logger.info(f"=== パフォーマンステスト開始 ({test_type}) ===")
        self.logger.info(f"テスト対象: {self.base_url}")
        
        try:
            if test_type == "concurrent":
                results = await self.concurrent_load_test()
            elif test_type == "sustained":
                results = await self.sustained_load_test()
            else:
                raise ValueError(f"不明なテストタイプ: {test_type}")
            
            # 結果分析
            analysis = self.analyze_results(results)
            
            # レポート生成
            self.generate_report(analysis, results)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"パフォーマンステストエラー: {e}")
            return None

async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TaxMCP パフォーマンステスト')
    parser.add_argument(
        '--test-type', 
        choices=['concurrent', 'sustained'], 
        default='concurrent',
        help='テストタイプ (default: concurrent)'
    )
    
    args = parser.parse_args()
    
    try:
        client = PerformanceTestClient()
        await client.run_performance_test(args.test_type)
    except KeyboardInterrupt:
        print("\nテストが中断されました")
    except Exception as e:
        print(f"テスト実行エラー: {e}")

if __name__ == "__main__":
    asyncio.run(main())