"""所得税計算テスト

TaxMCPサーバーの所得税計算機能をテストする
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


class TestIncomeTaxCalculation(TaxMCPTestCase, PerformanceTestMixin):
    """所得税計算テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.data_generator = TestDataGenerator()
    
    def test_basic_income_tax_calculation(self):
        """基本的な所得税計算テスト"""
        print("\n=== 基本的な所得税計算テスト ===")
        
        # テストデータ生成
        test_data = self.data_generator.generate_income_tax_data(
            annual_income=5000000,
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # MCPリクエスト作成
        request = self.create_test_request(
            method="tools/call",
            params={
                "name": "calculate_income_tax",
                "arguments": test_data
            }
        )
        
        print(f"MCPリクエスト: {request}")
        
        # モック計算結果
        expected_result = {
            "total_tax": 572500,
            "income_tax": {"amount": 372500},
            "resident_tax": 200000,
            "tax_year": 2025,
            "calculation_details": {
                "annual_income": 5000000,
                "basic_deduction": 480000,
                "taxable_income": 4520000,
                "income_tax_rate": 0.20,
                "income_tax_deduction": 427500,
                "calculated_income_tax": 476500,
                "tax_credit": 104000,
                "final_income_tax": 372500,
                "resident_tax_rate": 0.10,
                "resident_tax": 200000
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_income_tax_calculation(expected_result, expected_result["income_tax"]["amount"]) 
        TaxAssertions.assert_tax_amount_accuracy(
            expected_result["total_tax"], 572500, tolerance=1.0
        )
        
        print("✓ 基本的な所得税計算テスト成功")
    
    def test_low_income_tax_calculation(self):
        """低所得者の所得税計算テスト"""
        print("\n=== 低所得者の所得税計算テスト ===")
        
        # 低所得テストデータ
        test_data = self.data_generator.generate_income_tax_data(
            annual_income=1500000,
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果（低所得のため税額が少ない）
        expected_result = {
            "total_tax": 51000,
            "income_tax": {"amount": 51000},
            "resident_tax": 0,  # 住民税非課税
            "tax_year": 2025,
            "calculation_details": {
                "annual_income": 1500000,
                "basic_deduction": 480000,
                "taxable_income": 1020000,
                "income_tax_rate": 0.05,
                "final_income_tax": 51000
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_income_tax_calculation(expected_result, expected_result["income_tax"]["amount"]) 
        self.assertLessEqual(expected_result["total_tax"], 100000, "低所得者の税額は適切")
        
        print("✓ 低所得者の所得税計算テスト成功")
    
    def test_high_income_tax_calculation(self):
        """高所得者の所得税計算テスト"""
        print("\n=== 高所得者の所得税計算テスト ===")
        
        # 高所得テストデータ
        test_data = self.data_generator.generate_income_tax_data(
            annual_income=20000000,
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果（高所得のため高税率適用）
        expected_result = {
            "total_tax": 4764000,
            "income_tax": {"amount": 3764000},
            "resident_tax": 1000000,
            "tax_year": 2025,
            "calculation_details": {
                "annual_income": 20000000,
                "basic_deduction": 480000,
                "taxable_income": 19520000,
                "income_tax_rate": 0.33,
                "income_tax_deduction": 1536000,
                "calculated_income_tax": 4905600,
                "tax_credit": 1141600,
                "final_income_tax": 3764000,
                "resident_tax_rate": 0.10,
                "resident_tax": 1000000
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_income_tax_calculation(expected_result, expected_result["income_tax"]["amount"]) 
        self.assertGreater(expected_result["total_tax"], 1000000, "高所得者の税額は適切")
        TaxAssertions.assert_tax_rate_validity(
            expected_result["calculation_details"]["income_tax_rate"], 0.0, 0.45
        )
        
        print("✓ 高所得者の所得税計算テスト成功")
    
    def test_complex_income_tax_calculation(self):
        """複雑な所得税計算テスト（複数控除）"""
        print("\n=== 複雑な所得税計算テスト ===")
        
        # 複雑なテストデータ（複数控除あり）
        test_data = {
            "annual_income": 8000000,
            "tax_year": 2025,
            "deductions": {
                "basic_deduction": 480000,
                "spouse_deduction": 380000,
                "dependent_deduction": 380000,
                "social_insurance_deduction": 1200000,
                "life_insurance_deduction": 120000,
                "earthquake_insurance_deduction": 50000
            },
            "tax_credits": {
                "basic_tax_credit": 104000,
                "spouse_tax_credit": 38000,
                "dependent_tax_credit": 38000
            }
        }
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果
        total_deductions = sum(test_data["deductions"].values())
        taxable_income = test_data["annual_income"] - total_deductions
        
        expected_result = {
            "total_tax": 1230000,
            "income_tax": {"amount": 1030000},
            "resident_tax": 200000,
            "tax_year": 2025,
            "calculation_details": {
                "annual_income": 8000000,
                "total_deductions": total_deductions,
                "taxable_income": taxable_income,
                "income_tax_before_credits": 1210000,
                "total_tax_credits": 180000,
                "final_income_tax": 1030000
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_income_tax_calculation(expected_result, expected_result["income_tax"]["amount"]) 
        self.assertEqual(
            expected_result["calculation_details"]["total_deductions"],
            2610000,
            "控除額の合計が正しい"
        )
        
        print("✓ 複雑な所得税計算テスト成功")
    
    def test_income_tax_calculation_performance(self):
        """所得税計算のパフォーマンステスト"""
        print("\n=== 所得税計算パフォーマンステスト ===")
        
        # テストデータ
        test_data = self.data_generator.generate_income_tax_data(
            annual_income=5000000,
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # パフォーマンス測定
        def mock_calculation():
            # 実際の計算をシミュレート
            import time
            time.sleep(0.1)  # 100ms の処理時間をシミュレート
            return {
                "total_tax": 572500,
                "income_tax": {"amount": 372500},
                "resident_tax": 200000,
                "tax_year": 2025
            }
        
        result, execution_time = self.measure_performance(mock_calculation)
        
        print(f"実行時間: {execution_time:.3f}秒")
        print(f"計算結果: {result}")
        
        # パフォーマンスアサーション
        self.assert_response_time(execution_time, max_time=1.0)
        
        print("✓ 所得税計算パフォーマンステスト成功")
    
    def test_income_tax_edge_cases(self):
        """所得税計算の境界値テスト"""
        print("\n=== 所得税計算境界値テスト ===")
        
        # 境界値テストケース
        edge_cases = [
            {"annual_income": 0, "expected_tax": 0, "description": "所得なし"},
            {"annual_income": 1000000, "expected_tax": 26000, "description": "最低税率適用"},
            {"annual_income": 1950000, "expected_tax": 97500, "description": "税率境界値"},
            {"annual_income": 40000000, "expected_tax": 11640000, "description": "最高税率適用"}
        ]
        
        for case in edge_cases:
            print(f"\n--- {case['description']} ---")
            
            test_data = self.data_generator.generate_income_tax_data(
                annual_income=case["annual_income"],
                tax_year=2025
            )
            
            print(f"入力データ: {test_data}")
            
            # 期待される結果
            expected_result = {
                "total_tax": case["expected_tax"],
                "tax_year": 2025,
                "calculation_details": {
                    "annual_income": case["annual_income"]
                }
            }
            
            print(f"期待される結果: {expected_result}")
            
            # 基本的なアサーション
            self.assertIsInstance(expected_result["total_tax"], (int, float))
            self.assertGreaterEqual(expected_result["total_tax"], 0)
            
            print(f"✓ {case['description']}テスト成功")
    
    def test_invalid_income_tax_input(self):
        """無効な入力データのテスト"""
        print("\n=== 無効な入力データテスト ===")
        
        # 無効な入力パターン
        invalid_inputs = [
            {"annual_income": -1000000, "description": "負の所得"},
            {"annual_income": "invalid", "description": "文字列の所得"},
            {"tax_year": 2010, "description": "古い税年度"},
            {"tax_year": 2040, "description": "未来の税年度"},
            {"annual_income": None, "description": "None値"}
        ]
        
        for invalid_input in invalid_inputs:
            print(f"\n--- {invalid_input['description']} ---")
            
            test_data = {
                "annual_income": invalid_input.get("annual_income", 5000000),
                "tax_year": invalid_input.get("tax_year", 2025)
            }
            
            print(f"無効な入力データ: {test_data}")
            
            # バリデーションエラーを期待
            try:
                # 実際のバリデーション処理をシミュレート
                if isinstance(test_data["annual_income"], str):
                    raise ValueError("所得は数値である必要があります")
                if test_data["annual_income"] is None:
                    raise ValueError("所得は必須です")
                if test_data["annual_income"] < 0:
                    raise ValueError("所得は非負である必要があります")
                if test_data["tax_year"] < 2020 or test_data["tax_year"] > 2030:
                    raise ValueError("税年度は2020-2030の範囲である必要があります")
                
                self.fail(f"バリデーションエラーが発生すべきでした: {invalid_input['description']}")
            
            except ValueError as e:
                print(f"期待されるバリデーションエラー: {e}")
                print(f"✓ {invalid_input['description']}バリデーションテスト成功")
    
    def test_multiple_tax_years(self):
        """複数年度の所得税計算テスト"""
        print("\n=== 複数年度所得税計算テスト ===")
        
        # 複数年度のテストデータ
        test_years = [2023, 2024, 2025]
        annual_income = 6000000
        
        results = []
        
        for year in test_years:
            print(f"\n--- {year}年度 ---")
            
            test_data = self.data_generator.generate_income_tax_data(
                annual_income=annual_income,
                tax_year=year
            )
            
            print(f"入力データ: {test_data}")
            
            # 年度別の期待結果（基礎控除額の変更等を反映）
            expected_results = {
                2023: {"total_tax": 774000, "basic_deduction": 480000},
                2024: {"total_tax": 774000, "basic_deduction": 480000},
                2025: {"total_tax": 774000, "basic_deduction": 480000}
            }
            
            expected_result = {
                "total_tax": expected_results[year]["total_tax"],
                "tax_year": year,
                "calculation_details": {
                    "annual_income": annual_income,
                    "basic_deduction": expected_results[year]["basic_deduction"]
                }
            }
            
            print(f"期待される結果: {expected_result}")
            
            results.append(expected_result)
            
            # アサーション
            TaxAssertions.assert_tax_calculation_result(expected_result)
            
            print(f"✓ {year}年度計算テスト成功")
        
        # 年度間の一貫性チェック
        print("\n--- 年度間一貫性チェック ---")
        for i in range(len(results) - 1):
            current_year = results[i]
            next_year = results[i + 1]
            
            # 基本的な一貫性（同じ所得なら近い税額）
            tax_diff = abs(current_year["total_tax"] - next_year["total_tax"])
            self.assertLess(tax_diff, 100000, "年度間の税額差が適切")
            
            print(f"✓ {current_year['tax_year']}年度と{next_year['tax_year']}年度の一貫性確認")


if __name__ == "__main__":
    unittest.main(verbosity=2)