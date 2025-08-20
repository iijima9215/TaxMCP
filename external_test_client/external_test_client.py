#!/usr/bin/env python3
"""
外部テスト環境用TaxMCPクライアント
HTTPSリバースプロキシ経由でTaxMCPサーバーをテストします。
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# 現在のディレクトリから.envを読み込み
load_dotenv()

class ExternalTaxMCPClient:
    """外部テスト用TaxMCPクライアント"""
    
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'https://taxmcp.ami-j2.com')
        self.api_version = os.getenv('API_VERSION', 'v1')
        self.timeout = int(os.getenv('TIMEOUT', '30'))
        self.ssl_verify = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
        self.verbose = os.getenv('VERBOSE_OUTPUT', 'true').lower() == 'true'
        
        # 認証情報
        self.api_key = os.getenv('API_KEY')
        self.jwt_token = None
        
        # テスト設定
        self.test_iterations = int(os.getenv('TEST_ITERATIONS', '5'))
        self.test_delay = float(os.getenv('TEST_DELAY', '1'))
        
        # ログ設定
        self.setup_logging()
        
        # セッション
        self.session = None
    
    def setup_logging(self):
        """ログ設定"""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_file = os.getenv('LOG_FILE', 'test_results.log')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        connector = aiohttp.TCPConnector(ssl=self.ssl_verify)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session:
            await self.session.close()
    
    def get_headers(self) -> Dict[str, str]:
        """リクエストヘッダーを取得"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TaxMCP-External-Test-Client/1.0'
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        if self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        return headers
    
    async def test_health_check(self) -> bool:
        """ヘルスチェックテスト"""
        try:
            url = f"{self.base_url}/health"
            self.logger.info(f"ヘルスチェック: {url}")
            
            async with self.session.get(url, headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"ヘルスチェック成功: {data}")
                    return True
                else:
                    self.logger.error(f"ヘルスチェック失敗: {response.status}")
                    return False
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
    
    async def test_individual_tax_calculation(self) -> bool:
        """個人所得税計算テスト"""
        try:
            url = f"{self.base_url}/api/{self.api_version}/calculate/individual"
            
            test_data = {
                "income": int(os.getenv('SAMPLE_INCOME', '5000000')),
                "deductions": int(os.getenv('SAMPLE_DEDUCTIONS', '480000')),
                "tax_year": int(os.getenv('SAMPLE_TAX_YEAR', '2025')),
                "prefecture": "東京都",
                "city": "新宿区"
            }
            
            self.logger.info(f"個人所得税計算テスト: {url}")
            if self.verbose:
                self.logger.info(f"テストデータ: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info("個人所得税計算成功")
                    if self.verbose:
                        self.logger.info(f"計算結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"個人所得税計算失敗: {response.status} - {error_text}")
                    return False
        except Exception as e:
            self.logger.error(f"個人所得税計算エラー: {e}")
            return False
    
    async def test_corporate_tax_calculation(self) -> bool:
        """法人税計算テスト"""
        try:
            url = f"{self.base_url}/api/{self.api_version}/calculate/corporate"
            
            test_data = {
                "revenue": 100000000,
                "expenses": 80000000,
                "tax_year": int(os.getenv('SAMPLE_TAX_YEAR', '2025')),
                "company_type": "普通法人",
                "capital": 50000000
            }
            
            self.logger.info(f"法人税計算テスト: {url}")
            if self.verbose:
                self.logger.info(f"テストデータ: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info("法人税計算成功")
                    if self.verbose:
                        self.logger.info(f"計算結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"法人税計算失敗: {response.status} - {error_text}")
                    return False
        except Exception as e:
            self.logger.error(f"法人税計算エラー: {e}")
            return False
    
    async def test_tax_answer_search(self) -> bool:
        """タックスアンサー検索テスト"""
        try:
            url = f"{self.base_url}/api/{self.api_version}/search/tax-answer"
            
            test_data = {
                "query": "給与所得控除",
                "limit": 5
            }
            
            self.logger.info(f"タックスアンサー検索テスト: {url}")
            if self.verbose:
                self.logger.info(f"検索クエリ: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info("タックスアンサー検索成功")
                    if self.verbose:
                        self.logger.info(f"検索結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"タックスアンサー検索失敗: {response.status} - {error_text}")
                    return False
        except Exception as e:
            self.logger.error(f"タックスアンサー検索エラー: {e}")
            return False
    
    async def test_law_search(self) -> bool:
        """法令検索テスト"""
        try:
            url = f"{self.base_url}/api/{self.api_version}/search/law"
            
            test_data = {
                "query": "所得税法",
                "limit": 3
            }
            
            self.logger.info(f"法令検索テスト: {url}")
            if self.verbose:
                self.logger.info(f"検索クエリ: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info("法令検索成功")
                    if self.verbose:
                        self.logger.info(f"検索結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"法令検索失敗: {response.status} - {error_text}")
                    return False
        except Exception as e:
            self.logger.error(f"法令検索エラー: {e}")
            return False
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """包括的テスト実行"""
        self.logger.info("=== TaxMCP外部テスト開始 ===")
        self.logger.info(f"テスト対象: {self.base_url}")
        self.logger.info(f"テスト回数: {self.test_iterations}")
        
        test_results = {
            "start_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "test_iterations": self.test_iterations,
            "results": []
        }
        
        test_functions = [
            ("health_check", self.test_health_check),
            ("individual_tax", self.test_individual_tax_calculation),
            ("corporate_tax", self.test_corporate_tax_calculation),
            ("tax_answer_search", self.test_tax_answer_search),
            ("law_search", self.test_law_search)
        ]
        
        for iteration in range(self.test_iterations):
            self.logger.info(f"\n--- テスト反復 {iteration + 1}/{self.test_iterations} ---")
            iteration_results = {"iteration": iteration + 1, "tests": {}}
            
            for test_name, test_func in test_functions:
                self.logger.info(f"実行中: {test_name}")
                start_time = time.time()
                
                try:
                    success = await test_func()
                    end_time = time.time()
                    
                    iteration_results["tests"][test_name] = {
                        "success": success,
                        "duration": round(end_time - start_time, 3),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if success:
                        self.logger.info(f"✓ {test_name} 成功 ({iteration_results['tests'][test_name]['duration']}秒)")
                    else:
                        self.logger.error(f"✗ {test_name} 失敗")
                        
                except Exception as e:
                    end_time = time.time()
                    iteration_results["tests"][test_name] = {
                        "success": False,
                        "duration": round(end_time - start_time, 3),
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.logger.error(f"✗ {test_name} エラー: {e}")
                
                # テスト間の遅延
                if self.test_delay > 0:
                    await asyncio.sleep(self.test_delay)
            
            test_results["results"].append(iteration_results)
        
        test_results["end_time"] = datetime.now().isoformat()
        
        # 結果サマリー
        self.generate_test_summary(test_results)
        
        return test_results
    
    def generate_test_summary(self, test_results: Dict[str, Any]):
        """テスト結果サマリー生成"""
        self.logger.info("\n=== テスト結果サマリー ===")
        
        total_tests = 0
        successful_tests = 0
        
        test_names = set()
        for result in test_results["results"]:
            test_names.update(result["tests"].keys())
        
        for test_name in test_names:
            successes = 0
            total = 0
            total_duration = 0
            
            for result in test_results["results"]:
                if test_name in result["tests"]:
                    total += 1
                    total_tests += 1
                    if result["tests"][test_name]["success"]:
                        successes += 1
                        successful_tests += 1
                    total_duration += result["tests"][test_name]["duration"]
            
            success_rate = (successes / total * 100) if total > 0 else 0
            avg_duration = (total_duration / total) if total > 0 else 0
            
            self.logger.info(
                f"{test_name}: {successes}/{total} 成功 "
                f"({success_rate:.1f}%) 平均時間: {avg_duration:.3f}秒"
            )
        
        overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        self.logger.info(f"\n全体成功率: {successful_tests}/{total_tests} ({overall_success_rate:.1f}%)")
        
        # 結果をJSONファイルに保存
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"詳細結果を保存: {results_file}")

async def main():
    """メイン関数"""
    try:
        async with ExternalTaxMCPClient() as client:
            results = await client.run_comprehensive_test()
            return results
    except KeyboardInterrupt:
        print("\nテストが中断されました")
        return None
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())