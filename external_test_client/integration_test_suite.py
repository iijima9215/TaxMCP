#!/usr/bin/env python3
"""
外部テスト環境用統合テストスイート
全ての機能テスト、パフォーマンステスト、認証テストを統合実行します。
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# 現在のディレクトリから.envを読み込み
load_dotenv()

# 他のテストモジュールをインポート
from external_test_client import ExternalTaxMCPClient
from performance_test import PerformanceTestClient
from auth_test import AuthTestClient

class IntegrationTestSuite:
    """統合テストスイート"""
    
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'https://taxmcp.ami-j2.com')
        self.verbose = os.getenv('VERBOSE_OUTPUT', 'true').lower() == 'true'
        
        # テスト設定
        self.run_functional_tests = True
        self.run_performance_tests = True
        self.run_auth_tests = True
        
        # ログ設定
        self.setup_logging()
        
        # 結果保存用
        self.test_results = {
            "suite_start_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "functional_tests": None,
            "performance_tests": None,
            "auth_tests": None,
            "summary": {}
        }
    
    def setup_logging(self):
        """ログ設定"""
        log_file = f"integration_test_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"統合テストスイートログ: {log_file}")
    
    async def run_functional_tests(self) -> Dict[str, Any]:
        """機能テスト実行"""
        self.logger.info("\n=== 機能テスト開始 ===")
        
        try:
            async with ExternalTaxMCPClient() as client:
                results = await client.run_comprehensive_test()
                
                # 結果サマリー
                if results and "results" in results:
                    total_tests = 0
                    successful_tests = 0
                    
                    for iteration_result in results["results"]:
                        for test_name, test_result in iteration_result["tests"].items():
                            total_tests += 1
                            if test_result["success"]:
                                successful_tests += 1
                    
                    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
                    
                    summary = {
                        "status": "completed",
                        "total_tests": total_tests,
                        "successful_tests": successful_tests,
                        "success_rate": success_rate,
                        "details": results
                    }
                    
                    self.logger.info(f"機能テスト完了: {successful_tests}/{total_tests} 成功 ({success_rate:.1f}%)")
                else:
                    summary = {
                        "status": "failed",
                        "error": "テスト結果が取得できませんでした"
                    }
                    self.logger.error("機能テスト失敗: 結果が取得できませんでした")
                
                return summary
                
        except Exception as e:
            self.logger.error(f"機能テストエラー: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """パフォーマンステスト実行"""
        self.logger.info("\n=== パフォーマンステスト開始 ===")
        
        try:
            client = PerformanceTestClient()
            
            # 同時負荷テスト
            concurrent_results = await client.run_performance_test("concurrent")
            
            if concurrent_results:
                summary = {
                    "status": "completed",
                    "concurrent_test": concurrent_results,
                    "meets_sla": concurrent_results.get("performance_assessment", {}).get("meets_sla", False)
                }
                
                sla_status = "✓" if summary["meets_sla"] else "✗"
                avg_time = concurrent_results.get("response_times", {}).get("average_ms", 0)
                success_rate = concurrent_results.get("summary", {}).get("success_rate_percent", 0)
                
                self.logger.info(
                    f"パフォーマンステスト完了: {sla_status} SLA達成, "
                    f"平均応答時間: {avg_time}ms, 成功率: {success_rate}%"
                )
            else:
                summary = {
                    "status": "failed",
                    "error": "パフォーマンステスト結果が取得できませんでした"
                }
                self.logger.error("パフォーマンステスト失敗")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"パフォーマンステストエラー: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def run_auth_tests(self) -> Dict[str, Any]:
        """認証テスト実行"""
        self.logger.info("\n=== 認証テスト開始 ===")
        
        try:
            async with AuthTestClient() as client:
                results = await client.run_auth_tests()
                
                if results:
                    summary = {
                        "status": "completed",
                        "total_tests": results["total_tests"],
                        "successful_tests": results["successful_tests"],
                        "success_rate": results["success_rate"],
                        "security_issues": results["security_issues"],
                        "details": results
                    }
                    
                    security_status = "⚠️" if results["security_issues"] > 0 else "✓"
                    
                    self.logger.info(
                        f"認証テスト完了: {results['successful_tests']}/{results['total_tests']} 成功 "
                        f"({results['success_rate']:.1f}%), {security_status} セキュリティ問題: {results['security_issues']}件"
                    )
                else:
                    summary = {
                        "status": "failed",
                        "error": "認証テスト結果が取得できませんでした"
                    }
                    self.logger.error("認証テスト失敗")
                
                return summary
                
        except Exception as e:
            self.logger.error(f"認証テストエラー: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """全テスト実行"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("TaxMCP 外部テスト統合スイート開始")
        self.logger.info(f"テスト対象: {self.base_url}")
        self.logger.info("=" * 60)
        
        # 機能テスト
        if self.run_functional_tests:
            self.test_results["functional_tests"] = await self.run_functional_tests()
        
        # パフォーマンステスト
        if self.run_performance_tests:
            self.test_results["performance_tests"] = await self.run_performance_tests()
        
        # 認証テスト
        if self.run_auth_tests:
            self.test_results["auth_tests"] = await self.run_auth_tests()
        
        # 統合結果サマリー
        self.test_results["suite_end_time"] = datetime.now().isoformat()
        self.generate_integration_summary()
        
        return self.test_results
    
    def generate_integration_summary(self):
        """統合テスト結果サマリー生成"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("統合テスト結果サマリー")
        self.logger.info("=" * 60)
        
        summary = {
            "overall_status": "success",
            "test_suites": {},
            "critical_issues": [],
            "recommendations": []
        }
        
        # 機能テスト結果
        if self.test_results["functional_tests"]:
            func_test = self.test_results["functional_tests"]
            if func_test["status"] == "completed":
                success_rate = func_test.get("success_rate", 0)
                summary["test_suites"]["functional"] = {
                    "status": "✓" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "✗",
                    "success_rate": success_rate,
                    "details": f"{func_test.get('successful_tests', 0)}/{func_test.get('total_tests', 0)} 成功"
                }
                
                if success_rate < 90:
                    summary["critical_issues"].append(f"機能テスト成功率が低い: {success_rate:.1f}%")
                    if success_rate < 70:
                        summary["overall_status"] = "critical"
                
                self.logger.info(f"機能テスト: {summary['test_suites']['functional']['status']} {summary['test_suites']['functional']['details']} ({success_rate:.1f}%)")
            else:
                summary["test_suites"]["functional"] = {"status": "✗", "error": func_test.get("error", "不明なエラー")}
                summary["critical_issues"].append("機能テストが実行できませんでした")
                summary["overall_status"] = "critical"
                self.logger.error(f"機能テスト: ✗ {func_test.get('error', '不明なエラー')}")
        
        # パフォーマンステスト結果
        if self.test_results["performance_tests"]:
            perf_test = self.test_results["performance_tests"]
            if perf_test["status"] == "completed":
                meets_sla = perf_test.get("meets_sla", False)
                concurrent_results = perf_test.get("concurrent_test", {})
                avg_time = concurrent_results.get("response_times", {}).get("average_ms", 0)
                
                summary["test_suites"]["performance"] = {
                    "status": "✓" if meets_sla else "⚠️",
                    "meets_sla": meets_sla,
                    "avg_response_time_ms": avg_time
                }
                
                if not meets_sla:
                    summary["critical_issues"].append(f"パフォーマンスSLA未達成: 平均応答時間 {avg_time}ms")
                    summary["recommendations"].append("サーバーリソースの増強またはアプリケーション最適化を検討してください")
                
                sla_status = "✓" if meets_sla else "⚠️"
                self.logger.info(f"パフォーマンステスト: {sla_status} SLA {'達成' if meets_sla else '未達成'} (平均: {avg_time}ms)")
            else:
                summary["test_suites"]["performance"] = {"status": "✗", "error": perf_test.get("error", "不明なエラー")}
                summary["critical_issues"].append("パフォーマンステストが実行できませんでした")
                self.logger.error(f"パフォーマンステスト: ✗ {perf_test.get('error', '不明なエラー')}")
        
        # 認証テスト結果
        if self.test_results["auth_tests"]:
            auth_test = self.test_results["auth_tests"]
            if auth_test["status"] == "completed":
                security_issues = auth_test.get("security_issues", 0)
                success_rate = auth_test.get("success_rate", 0)
                
                summary["test_suites"]["authentication"] = {
                    "status": "✓" if security_issues == 0 and success_rate >= 90 else "⚠️" if security_issues <= 1 else "✗",
                    "success_rate": success_rate,
                    "security_issues": security_issues
                }
                
                if security_issues > 0:
                    summary["critical_issues"].append(f"セキュリティ問題が検出されました: {security_issues}件")
                    summary["recommendations"].append("セキュリティ設定を見直し、認証機能を強化してください")
                    if security_issues > 2:
                        summary["overall_status"] = "critical"
                
                security_status = "✓" if security_issues == 0 else "⚠️"
                self.logger.info(f"認証テスト: {security_status} {auth_test.get('successful_tests', 0)}/{auth_test.get('total_tests', 0)} 成功, セキュリティ問題: {security_issues}件")
            else:
                summary["test_suites"]["authentication"] = {"status": "✗", "error": auth_test.get("error", "不明なエラー")}
                summary["critical_issues"].append("認証テストが実行できませんでした")
                self.logger.error(f"認証テスト: ✗ {auth_test.get('error', '不明なエラー')}")
        
        # 全体評価
        if summary["overall_status"] == "success" and not summary["critical_issues"]:
            overall_emoji = "🎉"
            overall_message = "全てのテストが正常に完了しました"
        elif summary["overall_status"] == "critical":
            overall_emoji = "🚨"
            overall_message = "重大な問題が検出されました"
        else:
            overall_emoji = "⚠️"
            overall_message = "一部のテストで問題が検出されました"
        
        self.logger.info(f"\n{overall_emoji} 全体評価: {overall_message}")
        
        # 重要な問題
        if summary["critical_issues"]:
            self.logger.warning("\n🚨 重要な問題:")
            for issue in summary["critical_issues"]:
                self.logger.warning(f"  - {issue}")
        
        # 推奨事項
        if summary["recommendations"]:
            self.logger.info("\n💡 推奨事項:")
            for rec in summary["recommendations"]:
                self.logger.info(f"  - {rec}")
        
        # 結果をファイルに保存
        self.test_results["summary"] = summary
        self.save_results()
    
    def save_results(self):
        """結果をファイルに保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 詳細結果
        detailed_file = f"integration_test_results_{timestamp}.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        # サマリーレポート
        summary_file = f"integration_test_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results["summary"], f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n📄 詳細結果: {detailed_file}")
        self.logger.info(f"📄 サマリー: {summary_file}")
    
    def configure_tests(self, functional: bool = True, performance: bool = True, auth: bool = True):
        """テスト実行設定"""
        self.run_functional_tests = functional
        self.run_performance_tests = performance
        self.run_auth_tests = auth
        
        enabled_tests = []
        if functional:
            enabled_tests.append("機能テスト")
        if performance:
            enabled_tests.append("パフォーマンステスト")
        if auth:
            enabled_tests.append("認証テスト")
        
        self.logger.info(f"実行予定テスト: {', '.join(enabled_tests)}")

async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TaxMCP 統合テストスイート')
    parser.add_argument('--skip-functional', action='store_true', help='機能テストをスキップ')
    parser.add_argument('--skip-performance', action='store_true', help='パフォーマンステストをスキップ')
    parser.add_argument('--skip-auth', action='store_true', help='認証テストをスキップ')
    parser.add_argument('--functional-only', action='store_true', help='機能テストのみ実行')
    parser.add_argument('--performance-only', action='store_true', help='パフォーマンステストのみ実行')
    parser.add_argument('--auth-only', action='store_true', help='認証テストのみ実行')
    
    args = parser.parse_args()
    
    try:
        suite = IntegrationTestSuite()
        
        # テスト設定
        if args.functional_only:
            suite.configure_tests(functional=True, performance=False, auth=False)
        elif args.performance_only:
            suite.configure_tests(functional=False, performance=True, auth=False)
        elif args.auth_only:
            suite.configure_tests(functional=False, performance=False, auth=True)
        else:
            suite.configure_tests(
                functional=not args.skip_functional,
                performance=not args.skip_performance,
                auth=not args.skip_auth
            )
        
        # テスト実行
        results = await suite.run_all_tests()
        
        # 終了コード設定
        if results["summary"]["overall_status"] == "critical":
            sys.exit(1)
        elif results["summary"]["critical_issues"]:
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nテストが中断されました")
        sys.exit(130)
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())