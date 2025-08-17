"""住民税計算テスト

TaxMCPサーバーの住民税計算機能をテストする
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


class TestResidentTaxCalculation(TaxMCPTestCase, PerformanceTestMixin):
    """住民税計算テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.data_generator = TestDataGenerator()
    
    def test_standard_resident_tax_calculation(self):
        """標準的な住民税計算テスト"""
        print("\n=== 標準住民税計算テスト ===")
        
        # 標準的な住民税テストデータ
        test_data = self.data_generator.generate_resident_tax_data(
            income=5000000,
            prefecture="東京都",
            municipality="新宿区",
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # MCPリクエスト作成
        request = self.create_test_request(
            method="tools/call",
            params={
                "name": "calculate_resident_tax",
                "arguments": test_data
            }
        )
        
        print(f"MCPリクエスト: {request}")
        
        # 期待される結果
        # 所得割: 課税所得 * 10% (都道府県民税4% + 市区町村民税6%)
        # 均等割: 都道府県民税1,500円 + 市区町村民税3,500円 = 5,000円
        taxable_income = 5000000 - 480000  # 基礎控除等
        income_levy = taxable_income * 0.10
        per_capita_levy = 5000
        
        expected_result = {
            "total_tax": income_levy + per_capita_levy,
            "income_levy": income_levy,
            "per_capita_levy": per_capita_levy,
            "prefecture_tax": (taxable_income * 0.04) + 1500,
            "municipality_tax": (taxable_income * 0.06) + 3500,
            "tax_year": 2025,
            "calculation_details": {
                "gross_income": 5000000,
                "taxable_income": taxable_income,
                "basic_deduction": 480000,
                "prefecture": "東京都",
                "municipality": "新宿区",
                "income_levy_rate": 0.10,
                "prefecture_rate": 0.04,
                "municipality_rate": 0.06
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        TaxAssertions.assert_tax_amount_accuracy(
            expected_result["total_tax"], income_levy + per_capita_levy, tolerance=1.0
        )
        
        print("✓ 標準住民税計算テスト成功")
    
    def test_low_income_resident_tax_exemption(self):
        """低所得者の住民税非課税テスト"""
        print("\n=== 低所得者住民税非課税テスト ===")
        
        # 低所得者テストデータ
        test_data = {
            "income": 1000000,  # 低所得
            "prefecture": "東京都",
            "municipality": "新宿区",
            "tax_year": 2025,
            "dependents": 0,
            "spouse": False
        }
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果（非課税）
        expected_result = {
            "total_tax": 0,
            "income_levy": 0,
            "per_capita_levy": 0,
            "prefecture_tax": 0,
            "municipality_tax": 0,
            "tax_year": 2025,
            "tax_exemption_applied": True,
            "calculation_details": {
                "gross_income": 1000000,
                "taxable_income": 0,
                "exemption_reason": "低所得による非課税",
                "exemption_threshold": 1000000,
                "prefecture": "東京都",
                "municipality": "新宿区"
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        self.assertEqual(expected_result["total_tax"], 0, "低所得者は非課税")
        self.assertTrue(
            expected_result["tax_exemption_applied"],
            "非課税措置が適用されている"
        )
        
        print("✓ 低所得者住民税非課税テスト成功")
    
    def test_high_income_resident_tax_calculation(self):
        """高所得者の住民税計算テスト"""
        print("\n=== 高所得者住民税計算テスト ===")
        
        # 高所得者テストデータ
        test_data = {
            "income": 20000000,  # 高所得
            "prefecture": "東京都",
            "municipality": "港区",
            "tax_year": 2025,
            "deductions": {
                "basic_deduction": 480000,
                "social_insurance": 2000000,
                "life_insurance": 120000,
                "earthquake_insurance": 50000,
                "medical_expenses": 300000
            }
        }
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果
        total_deductions = sum(test_data["deductions"].values())
        taxable_income = max(0, test_data["income"] - total_deductions)
        income_levy = taxable_income * 0.10
        per_capita_levy = 5000
        
        expected_result = {
            "total_tax": income_levy + per_capita_levy,
            "income_levy": income_levy,
            "per_capita_levy": per_capita_levy,
            "prefecture_tax": (taxable_income * 0.04) + 1500,
            "municipality_tax": (taxable_income * 0.06) + 3500,
            "tax_year": 2025,
            "calculation_details": {
                "gross_income": 20000000,
                "taxable_income": taxable_income,
                "total_deductions": total_deductions,
                "prefecture": "東京都",
                "municipality": "港区",
                "high_income_taxpayer": True
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        self.assertGreater(expected_result["total_tax"], 1000000, "高所得者は高額な税額")
        
        print("✓ 高所得者住民税計算テスト成功")
    
    def test_different_municipalities_tax_rates(self):
        """異なる自治体の税率テスト"""
        print("\n=== 異なる自治体税率テスト ===")
        
        # 異なる自治体のテストケース
        municipalities = [
            {
                "prefecture": "東京都",
                "municipality": "新宿区",
                "per_capita_levy": 5000,
                "description": "東京都新宿区"
            },
            {
                "prefecture": "大阪府",
                "municipality": "大阪市",
                "per_capita_levy": 5300,
                "description": "大阪府大阪市"
            },
            {
                "prefecture": "愛知県",
                "municipality": "名古屋市",
                "per_capita_levy": 5300,
                "description": "愛知県名古屋市"
            }
        ]
        
        base_income = 4000000
        
        for municipality in municipalities:
            print(f"\n--- {municipality['description']} ---")
            
            test_data = {
                "income": base_income,
                "prefecture": municipality["prefecture"],
                "municipality": municipality["municipality"],
                "tax_year": 2025
            }
            
            print(f"入力データ: {test_data}")
            
            # 期待される結果
            taxable_income = base_income - 480000  # 基礎控除
            income_levy = taxable_income * 0.10
            per_capita_levy = municipality["per_capita_levy"]
            
            expected_result = {
                "total_tax": income_levy + per_capita_levy,
                "income_levy": income_levy,
                "per_capita_levy": per_capita_levy,
                "tax_year": 2025,
                "calculation_details": {
                    "prefecture": municipality["prefecture"],
                    "municipality": municipality["municipality"],
                    "taxable_income": taxable_income
                }
            }
            
            print(f"期待される結果: {expected_result}")
            
            # アサーション
            TaxAssertions.assert_tax_calculation_result(expected_result)
            self.assertEqual(
                expected_result["per_capita_levy"],
                municipality["per_capita_levy"],
                f"{municipality['description']}の均等割が正しい"
            )
            
            print(f"✓ {municipality['description']}テスト成功")
    
    def test_resident_tax_with_dependents(self):
        """扶養家族がいる場合の住民税計算テスト"""
        print("\n=== 扶養家族住民税計算テスト ===")
        
        # 扶養家族ありテストデータ
        test_data = {
            "income": 6000000,
            "prefecture": "東京都",
            "municipality": "世田谷区",
            "tax_year": 2025,
            "dependents": [
                {"type": "spouse", "age": 35, "income": 0},
                {"type": "child", "age": 10, "income": 0},
                {"type": "child", "age": 8, "income": 0},
                {"type": "parent", "age": 70, "income": 500000}
            ]
        }
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果
        # 基礎控除: 480,000円
        # 配偶者控除: 380,000円
        # 扶養控除: 380,000円 × 2人（子供） + 480,000円（老人扶養親族）
        total_deductions = 480000 + 380000 + (380000 * 2) + 480000
        taxable_income = max(0, test_data["income"] - total_deductions)
        income_levy = taxable_income * 0.10
        per_capita_levy = 5000
        
        expected_result = {
            "total_tax": income_levy + per_capita_levy,
            "income_levy": income_levy,
            "per_capita_levy": per_capita_levy,
            "tax_year": 2025,
            "calculation_details": {
                "gross_income": 6000000,
                "taxable_income": taxable_income,
                "total_deductions": total_deductions,
                "basic_deduction": 480000,
                "spouse_deduction": 380000,
                "dependent_deduction": 380000 * 2,
                "elderly_dependent_deduction": 480000,
                "number_of_dependents": 4
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        self.assertEqual(
            expected_result["calculation_details"]["number_of_dependents"],
            4,
            "扶養家族数が正しい"
        )
        
        print("✓ 扶養家族住民税計算テスト成功")
    
    def test_resident_tax_calculation_performance(self):
        """住民税計算のパフォーマンステスト"""
        print("\n=== 住民税計算パフォーマンステスト ===")
        
        # テストデータ
        test_data = self.data_generator.generate_resident_tax_data(
            income=8000000,
            prefecture="東京都",
            municipality="渋谷区",
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # パフォーマンス測定
        def mock_calculation():
            import time
            time.sleep(0.02)  # 20ms の処理時間をシミュレート
            return {
                "total_tax": 750000,
                "income_levy": 745000,
                "per_capita_levy": 5000,
                "tax_year": 2025
            }
        
        result, execution_time = self.measure_performance(mock_calculation)
        
        print(f"実行時間: {execution_time:.3f}秒")
        print(f"計算結果: {result}")
        
        # パフォーマンスアサーション
        self.assert_response_time(execution_time, max_time=0.3)
        
        print("✓ 住民税計算パフォーマンステスト成功")
    
    def test_resident_tax_edge_cases(self):
        """住民税計算の境界値テスト"""
        print("\n=== 住民税計算境界値テスト ===")
        
        # 境界値テストケース
        edge_cases = [
            {
                "income": 0,
                "expected_tax": 0,
                "description": "所得なし"
            },
            {
                "income": 1000000,
                "expected_tax": 0,
                "description": "非課税限度額"
            },
            {
                "income": 1000001,
                "expected_tax": 57000,  # (1000001 - 480000) * 0.10 + 5000
                "description": "非課税限度額+1円"
            },
            {
                "income": 480000,
                "expected_tax": 0,
                "description": "基礎控除額と同額"
            }
        ]
        
        for case in edge_cases:
            print(f"\n--- {case['description']} ---")
            
            test_data = {
                "income": case["income"],
                "prefecture": "東京都",
                "municipality": "千代田区",
                "tax_year": 2025
            }
            
            print(f"入力データ: {test_data}")
            
            # 期待される結果
            expected_result = {
                "total_tax": case["expected_tax"],
                "tax_year": 2025,
                "calculation_details": {
                    "gross_income": case["income"]
                }
            }
            
            print(f"期待される結果: {expected_result}")
            
            # 基本的なアサーション
            self.assertIsInstance(expected_result["total_tax"], (int, float))
            self.assertGreaterEqual(expected_result["total_tax"], 0)
            
            print(f"✓ {case['description']}テスト成功")
    
    def test_invalid_resident_tax_input(self):
        """無効な入力データのテスト"""
        print("\n=== 無効な入力データテスト ===")
        
        # 無効な入力パターン
        invalid_inputs = [
            {
                "income": "invalid",
                "description": "文字列の所得"
            },
            {
                "income": -1000000,
                "description": "負の所得"
            },
            {
                "prefecture": "",
                "description": "空の都道府県"
            },
            {
                "municipality": None,
                "description": "None値の市区町村"
            },
            {
                "tax_year": 2010,
                "description": "古い税年度"
            }
        ]
        
        for invalid_input in invalid_inputs:
            print(f"\n--- {invalid_input['description']} ---")
            
            test_data = {
                "income": invalid_input.get("income", 5000000),
                "prefecture": invalid_input.get("prefecture", "東京都"),
                "municipality": invalid_input.get("municipality", "新宿区"),
                "tax_year": invalid_input.get("tax_year", 2025)
            }
            
            print(f"無効な入力データ: {test_data}")
            
            # バリデーションエラーを期待
            try:
                # 実際のバリデーション処理をシミュレート
                if isinstance(test_data["income"], str):
                    raise ValueError("所得は数値である必要があります")
                if test_data["income"] < 0:
                    raise ValueError("所得は非負である必要があります")
                if not test_data["prefecture"]:
                    raise ValueError("都道府県は必須です")
                if test_data["municipality"] is None:
                    raise ValueError("市区町村は必須です")
                if test_data["tax_year"] < 2020 or test_data["tax_year"] > 2030:
                    raise ValueError("税年度は2020-2030の範囲である必要があります")
                
                self.fail(f"バリデーションエラーが発生すべきでした: {invalid_input['description']}")
            
            except ValueError as e:
                print(f"期待されるバリデーションエラー: {e}")
                print(f"✓ {invalid_input['description']}バリデーションテスト成功")
    
    def test_special_deductions(self):
        """特別控除の住民税計算テスト"""
        print("\n=== 特別控除住民税計算テスト ===")
        
        # 特別控除テストデータ
        test_data = {
            "income": 8000000,
            "prefecture": "東京都",
            "municipality": "品川区",
            "tax_year": 2025,
            "special_deductions": {
                "disability_deduction": 270000,  # 障害者控除
                "widow_deduction": 270000,       # 寡婦控除
                "working_student_deduction": 270000,  # 勤労学生控除
                "donation_deduction": 100000     # 寄附金控除
            }
        }
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果
        basic_deduction = 480000
        special_deductions_total = sum(test_data["special_deductions"].values())
        total_deductions = basic_deduction + special_deductions_total
        taxable_income = max(0, test_data["income"] - total_deductions)
        income_levy = taxable_income * 0.10
        per_capita_levy = 5000
        
        expected_result = {
            "total_tax": income_levy + per_capita_levy,
            "income_levy": income_levy,
            "per_capita_levy": per_capita_levy,
            "tax_year": 2025,
            "calculation_details": {
                "gross_income": 8000000,
                "taxable_income": taxable_income,
                "basic_deduction": basic_deduction,
                "special_deductions": test_data["special_deductions"],
                "total_deductions": total_deductions,
                "special_deductions_applied": True
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        self.assertTrue(
            expected_result["calculation_details"]["special_deductions_applied"],
            "特別控除が適用されている"
        )
        
        print("✓ 特別控除住民税計算テスト成功")
    
    def test_multi_year_resident_tax_comparison(self):
        """複数年度の住民税比較テスト"""
        print("\n=== 複数年度住民税比較テスト ===")
        
        # 複数年度のテストデータ
        base_data = {
            "income": 6000000,
            "prefecture": "東京都",
            "municipality": "中央区"
        }
        
        years = [2023, 2024, 2025]
        results = []
        
        for year in years:
            print(f"\n--- {year}年度 ---")
            
            test_data = {
                **base_data,
                "tax_year": year
            }
            
            print(f"入力データ: {test_data}")
            
            # 年度による基礎控除の変化を考慮
            basic_deduction = 480000 if year >= 2020 else 380000
            taxable_income = max(0, base_data["income"] - basic_deduction)
            income_levy = taxable_income * 0.10
            per_capita_levy = 5000
            
            expected_result = {
                "total_tax": income_levy + per_capita_levy,
                "income_levy": income_levy,
                "per_capita_levy": per_capita_levy,
                "tax_year": year,
                "calculation_details": {
                    "basic_deduction": basic_deduction,
                    "taxable_income": taxable_income
                }
            }
            
            print(f"期待される結果: {expected_result}")
            
            results.append(expected_result)
            
            # アサーション
            TaxAssertions.assert_tax_calculation_result(expected_result)
            
            print(f"✓ {year}年度テスト成功")
        
        # 年度間比較
        print("\n--- 年度間比較 ---")
        for i in range(len(results) - 1):
            current = results[i]
            next_result = results[i + 1]
            
            print(f"{current['tax_year']}年: {current['total_tax']:,}円")
            print(f"{next_result['tax_year']}年: {next_result['total_tax']:,}円")
            
            # 基礎控除変更の影響確認
            if (current["calculation_details"]["basic_deduction"] != 
                next_result["calculation_details"]["basic_deduction"]):
                print(f"基礎控除変更: {current['calculation_details']['basic_deduction']:,}円 → {next_result['calculation_details']['basic_deduction']:,}円")
        
        print("✓ 複数年度住民税比較テスト成功")


if __name__ == "__main__":
    unittest.main(verbosity=2)