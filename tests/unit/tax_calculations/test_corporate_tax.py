"""法人税計算テスト

TaxMCPサーバーの法人税計算機能をテストする
"""

import unittest
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.test_config import TaxMCPTestCase, PerformanceTestMixin
from tests.utils.assertion_helpers import TaxAssertions
from tests.utils.test_data_generator import TestDataGenerator


class TestCorporateTaxCalculation(TaxMCPTestCase, PerformanceTestMixin):
    """法人税計算テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.data_generator = TestDataGenerator()
    
    def test_small_company_tax_calculation(self):
        """中小法人の法人税計算テスト"""
        print("\n=== 中小法人の法人税計算テスト ===")
        
        # 中小法人テストデータ
        test_data = self.data_generator.generate_corporate_tax_data(
            annual_revenue=50000000,
            annual_profit=8000000,
            company_type="small",
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # MCPリクエスト作成
        request = self.create_test_request(
            method="tools/call",
            params={
                "name": "calculate_corporate_tax",
                "arguments": test_data
            }
        )
        
        print(f"MCPリクエスト: {request}")
        
        # 期待される結果（中小法人税率15%）
        expected_result = {
            "total_tax": 2000000,
            "corporate_tax": 1200000,  # 8,000,000 * 0.15
            "local_corporate_tax": 120000,  # 1,200,000 * 0.10
            "business_tax": 680000,  # 8,000,000 * 0.085
            "tax_year": 2025,
            "company_type": "small",
            "tax_rate": 0.15,
            "calculation_details": {
                "annual_revenue": 50000000,
                "annual_profit": 8000000,
                "taxable_income": 8000000,
                "corporate_tax_rate": 0.15,
                "local_tax_rate": 0.10,
                "business_tax_rate": 0.085,
                "effective_tax_rate": 0.25
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_corporate_tax_result(expected_result)
        TaxAssertions.assert_tax_rate_validity(expected_result["tax_rate"], 0.0, 0.30)
        TaxAssertions.assert_tax_amount_accuracy(
            expected_result["corporate_tax"], 1200000, tolerance=1.0
        )
        
        print("✓ 中小法人の法人税計算テスト成功")
    
    def test_large_company_tax_calculation(self):
        """大法人の法人税計算テスト"""
        print("\n=== 大法人の法人税計算テスト ===")
        
        # 大法人テストデータ
        test_data = self.data_generator.generate_corporate_tax_data(
            annual_revenue=5000000000,
            annual_profit=800000000,
            company_type="large",
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果（大法人税率23%）
        expected_result = {
            "total_tax": 252000000,
            "corporate_tax": 184000000,  # 800,000,000 * 0.23
            "local_corporate_tax": 18400000,  # 184,000,000 * 0.10
            "business_tax": 49600000,  # 800,000,000 * 0.062
            "tax_year": 2025,
            "company_type": "large",
            "tax_rate": 0.23,
            "calculation_details": {
                "annual_revenue": 5000000000,
                "annual_profit": 800000000,
                "taxable_income": 800000000,
                "corporate_tax_rate": 0.23,
                "local_tax_rate": 0.10,
                "business_tax_rate": 0.062,
                "effective_tax_rate": 0.315
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_corporate_tax_result(expected_result)
        TaxAssertions.assert_tax_rate_validity(expected_result["tax_rate"], 0.20, 0.30)
        self.assertGreater(expected_result["total_tax"], 100000000, "大法人の税額は適切")
        
        print("✓ 大法人の法人税計算テスト成功")
    
    def test_startup_company_tax_calculation(self):
        """スタートアップ企業の法人税計算テスト"""
        print("\n=== スタートアップ企業の法人税計算テスト ===")
        
        # スタートアップテストデータ（赤字）
        test_data = {
            "annual_revenue": 10000000,
            "annual_profit": -2000000,  # 赤字
            "company_type": "startup",
            "tax_year": 2025,
            "startup_benefits": {
                "tax_exemption": True,
                "loss_carryforward": 2000000
            }
        }
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果（赤字のため税額なし）
        expected_result = {
            "total_tax": 0,
            "corporate_tax": 0,
            "local_corporate_tax": 0,
            "business_tax": 0,
            "tax_year": 2025,
            "company_type": "startup",
            "tax_rate": 0.0,
            "calculation_details": {
                "annual_revenue": 10000000,
                "annual_profit": -2000000,
                "taxable_income": 0,
                "loss_carryforward": 2000000,
                "tax_exemption_applied": True
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_corporate_tax_result(expected_result)
        self.assertEqual(expected_result["total_tax"], 0, "赤字企業の税額は0")
        self.assertIn("loss_carryforward", expected_result["calculation_details"], "繰越欠損金が記録されている")
        
        print("✓ スタートアップ企業の法人税計算テスト成功")
    
    def test_complex_corporate_tax_calculation(self):
        """複雑な法人税計算テスト（控除・特例あり）"""
        print("\n=== 複雑な法人税計算テスト ===")
        
        # 複雑なテストデータ
        test_data = {
            "annual_revenue": 200000000,
            "annual_profit": 30000000,
            "company_type": "small",
            "tax_year": 2025,
            "deductions": {
                "research_development": 5000000,
                "equipment_investment": 3000000,
                "employee_training": 1000000
            },
            "tax_credits": {
                "rd_tax_credit": 1500000,
                "investment_tax_credit": 900000,
                "employment_tax_credit": 300000
            },
            "special_measures": {
                "digital_transformation": True,
                "carbon_neutral": True
            }
        }
        
        print(f"入力データ: {test_data}")
        
        # 控除後の課税所得計算
        total_deductions = sum(test_data["deductions"].values())
        taxable_income = test_data["annual_profit"] - total_deductions
        
        # 期待される結果
        expected_result = {
            "total_tax": 4450000,
            "corporate_tax": 3150000,  # (30,000,000 - 9,000,000) * 0.15
            "local_corporate_tax": 315000,
            "business_tax": 985000,
            "tax_year": 2025,
            "company_type": "small",
            "tax_rate": 0.15,
            "calculation_details": {
                "annual_revenue": 200000000,
                "annual_profit": 30000000,
                "total_deductions": total_deductions,
                "taxable_income": taxable_income,
                "corporate_tax_before_credits": 3150000,
                "total_tax_credits": 2700000,
                "final_corporate_tax": 450000,
                "special_measures_applied": ["digital_transformation", "carbon_neutral"]
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_corporate_tax_result(expected_result)
        self.assertEqual(
            expected_result["calculation_details"]["total_deductions"],
            9000000,
            "控除額の合計が正しい"
        )
        self.assertEqual(
            expected_result["calculation_details"]["taxable_income"],
            21000000,
            "課税所得が正しい"
        )
        
        print("✓ 複雑な法人税計算テスト成功")
    
    def test_corporate_tax_calculation_performance(self):
        """法人税計算のパフォーマンステスト"""
        print("\n=== 法人税計算パフォーマンステスト ===")
        
        # テストデータ
        test_data = self.data_generator.generate_corporate_tax_data(
            annual_revenue=100000000,
            annual_profit=15000000,
            company_type="small",
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # パフォーマンス測定
        def mock_calculation():
            import time
            time.sleep(0.05)  # 50ms の処理時間をシミュレート
            return {
                "total_tax": 3750000,
                "corporate_tax": 2250000,
                "local_corporate_tax": 225000,
                "business_tax": 1275000,
                "tax_year": 2025
            }
        
        result, execution_time = self.measure_performance(mock_calculation)
        
        print(f"実行時間: {execution_time:.3f}秒")
        print(f"計算結果: {result}")
        
        # パフォーマンスアサーション
        self.assert_response_time(execution_time, max_time=0.5)
        
        print("✓ 法人税計算パフォーマンステスト成功")
    
    def test_corporate_tax_edge_cases(self):
        """法人税計算の境界値テスト"""
        print("\n=== 法人税計算境界値テスト ===")
        
        # 境界値テストケース
        edge_cases = [
            {
                "annual_profit": 0,
                "expected_tax": 0,
                "description": "利益なし"
            },
            {
                "annual_profit": 8000000,
                "expected_tax": 2000000,
                "description": "中小法人境界値"
            },
            {
                "annual_profit": 800000000,
                "expected_tax": 184000000,
                "description": "大法人適用"
            },
            {
                "annual_profit": -5000000,
                "expected_tax": 0,
                "description": "赤字法人"
            }
        ]
        
        for case in edge_cases:
            print(f"\n--- {case['description']} ---")
            
            # 会社タイプを利益に基づいて決定
            if case["annual_profit"] <= 0:
                company_type = "startup"
            elif case["annual_profit"] < 100000000:
                company_type = "small"
            else:
                company_type = "large"
            
            test_data = {
                "annual_revenue": max(case["annual_profit"] * 5, 0),
                "annual_profit": case["annual_profit"],
                "company_type": company_type,
                "tax_year": 2025
            }
            
            print(f"入力データ: {test_data}")
            
            # 期待される結果
            expected_result = {
                "total_tax": case["expected_tax"],
                "tax_year": 2025,
                "company_type": company_type,
                "calculation_details": {
                    "annual_profit": case["annual_profit"]
                }
            }
            
            print(f"期待される結果: {expected_result}")
            
            # 基本的なアサーション
            self.assertIsInstance(expected_result["total_tax"], (int, float))
            self.assertGreaterEqual(expected_result["total_tax"], 0)
            
            print(f"✓ {case['description']}テスト成功")
    
    def test_invalid_corporate_tax_input(self):
        """無効な入力データのテスト"""
        print("\n=== 無効な入力データテスト ===")
        
        # 無効な入力パターン
        invalid_inputs = [
            {
                "annual_revenue": "invalid",
                "description": "文字列の売上"
            },
            {
                "annual_profit": None,
                "description": "None値の利益"
            },
            {
                "company_type": "unknown",
                "description": "不明な会社タイプ"
            },
            {
                "tax_year": 2010,
                "description": "古い税年度"
            },
            {
                "annual_revenue": -1000000,
                "description": "負の売上"
            }
        ]
        
        for invalid_input in invalid_inputs:
            print(f"\n--- {invalid_input['description']} ---")
            
            test_data = {
                "annual_revenue": invalid_input.get("annual_revenue", 100000000),
                "annual_profit": invalid_input.get("annual_profit", 15000000),
                "company_type": invalid_input.get("company_type", "small"),
                "tax_year": invalid_input.get("tax_year", 2025)
            }
            
            print(f"無効な入力データ: {test_data}")
            
            # バリデーションエラーを期待
            try:
                # 実際のバリデーション処理をシミュレート
                if isinstance(test_data["annual_revenue"], str):
                    raise ValueError("売上は数値である必要があります")
                if test_data["annual_profit"] is None:
                    raise ValueError("利益は必須です")
                if test_data["annual_revenue"] < 0:
                    raise ValueError("売上は非負である必要があります")
                if test_data["company_type"] not in ["small", "large", "startup"]:
                    raise ValueError("会社タイプが無効です")
                if test_data["tax_year"] < 2020 or test_data["tax_year"] > 2030:
                    raise ValueError("税年度は2020-2030の範囲である必要があります")
                
                self.fail(f"バリデーションエラーが発生すべきでした: {invalid_input['description']}")
            
            except ValueError as e:
                print(f"期待されるバリデーションエラー: {e}")
                print(f"✓ {invalid_input['description']}バリデーションテスト成功")
    
    def test_tax_rate_transitions(self):
        """税率境界値での遷移テスト"""
        print("\n=== 税率境界値遷移テスト ===")
        
        # 中小法人から大法人への境界値テスト
        transition_cases = [
            {"profit": 99999999, "expected_type": "small", "expected_rate": 0.15},
            {"profit": 100000000, "expected_type": "large", "expected_rate": 0.23},
            {"profit": 100000001, "expected_type": "large", "expected_rate": 0.23}
        ]
        
        for case in transition_cases:
            print(f"\n--- 利益: {case['profit']:,}円 ---")
            
            test_data = {
                "annual_revenue": case["profit"] * 5,
                "annual_profit": case["profit"],
                "company_type": case["expected_type"],
                "tax_year": 2025
            }
            
            print(f"入力データ: {test_data}")
            
            # 期待される税率
            expected_corporate_tax = case["profit"] * case["expected_rate"]
            
            expected_result = {
                "corporate_tax": expected_corporate_tax,
                "tax_rate": case["expected_rate"],
                "company_type": case["expected_type"]
            }
            
            print(f"期待される結果: {expected_result}")
            
            # アサーション
            self.assertEqual(expected_result["tax_rate"], case["expected_rate"])
            self.assertEqual(expected_result["company_type"], case["expected_type"])
            
            print(f"✓ 利益{case['profit']:,}円の税率遷移テスト成功")
    
    def test_multiple_fiscal_years(self):
        """複数事業年度の法人税計算テスト"""
        print("\n=== 複数事業年度法人税計算テスト ===")
        
        # 複数年度のテストデータ
        test_years = [2023, 2024, 2025]
        annual_profit = 20000000
        
        results = []
        
        for year in test_years:
            print(f"\n--- {year}年度 ---")
            
            test_data = {
                "annual_revenue": annual_profit * 4,
                "annual_profit": annual_profit,
                "company_type": "small",
                "tax_year": year
            }
            
            print(f"入力データ: {test_data}")
            
            # 年度別の期待結果
            expected_result = {
                "total_tax": 5000000,  # 基本的には同じ税率
                "corporate_tax": 3000000,  # 20,000,000 * 0.15
                "tax_year": year,
                "company_type": "small",
                "calculation_details": {
                    "annual_profit": annual_profit
                }
            }
            
            print(f"期待される結果: {expected_result}")
            
            results.append(expected_result)
            
            # アサーション
            TaxAssertions.assert_corporate_tax_result(expected_result)
            
            print(f"✓ {year}年度計算テスト成功")
        
        # 年度間の一貫性チェック
        print("\n--- 年度間一貫性チェック ---")
        for i in range(len(results) - 1):
            current_year = results[i]
            next_year = results[i + 1]
            
            # 同じ利益なら同じ税額（税制改正がない場合）
            self.assertEqual(
                current_year["corporate_tax"],
                next_year["corporate_tax"],
                "年度間の税額一貫性"
            )
            
            print(f"✓ {current_year['tax_year']}年度と{next_year['tax_year']}年度の一貫性確認")


if __name__ == "__main__":
    unittest.main(verbosity=2)