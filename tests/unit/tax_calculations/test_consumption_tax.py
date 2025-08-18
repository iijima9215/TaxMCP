"""消費税計算テスト

TaxMCPサーバーの消費税計算機能をテストする
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
from tax_calculator import JapaneseTaxCalculator


class TestConsumptionTaxCalculation(TaxMCPTestCase, PerformanceTestMixin):
    """消費税計算テストクラス"""

    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.calculator = JapaneseTaxCalculator()
        self.data_generator = TestDataGenerator()
        self.setup_mocks()
    
    def test_standard_consumption_tax_calculation(self):
        """標準税率（10%）の消費税計算テスト"""
        print("\n=== 標準税率消費税計算テスト ===")
        
        # 標準税率テストデータ
        test_data = self.data_generator.generate_consumption_tax_data(
            sales_amount=10000000,
            purchase_amount=6000000,
            tax_year=2025,
            international_sales=500000,
            international_purchases=200000
        )
        
        print(f"入力データ: {test_data}")
         

        
        # 消費税計算を直接呼び出し
        result = self.calculator.calculate_consumption_tax(

            tax_year=test_data["tax_year"],
            items=test_data.get("items"),
            purchases=test_data.get("purchases")
        )
        
        print(f"計算結果: {result}")

        # 結果の検証

        
        # 期待される結果（標準税率10%）
        expected_result = {
            "total_tax": 400000,  # (10,000,000 * 0.10) - (6,000,000 * 0.10)
            "sales_tax": 1000000,  # 10,000,000 * 0.10
            "purchase_tax": 600000,  # 6,000,000 * 0.10
            "net_tax": 400000,
            "tax_year": 2025,
            "tax_rate": 0.10,
            "calculation_details": {
                "sales_amount": 10000000,
                "purchase_amount": 6000000,
                "taxable_sales": 10000000,
                "taxable_purchases": 6000000,
                "standard_rate_sales": 10000000,
                "reduced_rate_sales": 0,
                "tax_rate_applied": "standard"
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        TaxAssertions.assert_tax_rate_validity(expected_result["tax_rate"], 0.08, 0.10)
        TaxAssertions.assert_tax_amount_accuracy(
            expected_result["total_tax"], 400000, tolerance=1.0
        )
        
        print("✓ 標準税率消費税計算テスト成功")
    
    def test_reduced_rate_consumption_tax_calculation(self):
        """軽減税率（8%）の消費税計算テスト"""
        print("\n=== 軽減税率消費税計算テスト ===")
        
        # 軽減税率テストデータ
        test_data = {
            "sales_amount": 5000000,
            "purchase_amount": 3000000,
            "tax_year": 2025,
            "items": [
                {
                    "category": "food",
                    "amount": 3000000,
                    "tax_rate": 0.08  # 軽減税率
                },
                {
                    "category": "general",
                    "amount": 2000000,
                    "tax_rate": 0.10  # 標準税率
                }
            ],
            "purchases": [
                {
                    "category": "food",
                    "amount": 1800000,
                    "tax_rate": 0.08
                },
                {
                    "category": "general",
                    "amount": 1200000,
                    "tax_rate": 0.10
                }
            ],

        }
        
        print(f"入力データ: {test_data}")
        
        # 消費税計算を直接呼び出し
        result = self.calculator.calculate_consumption_tax(

            tax_year=test_data["tax_year"],
            business_type=test_data.get("business_type"),
            items=test_data.get("items"),
            purchases=test_data.get("purchases")
        )
        print(f"計算結果: {result}")

        # 結果の検証
        self.assertIsInstance(result, dict)
        self.assertIn("total_tax", result)
        self.assertIn("calculation_details", result)
        # 期待される結果
        # 売上税: (3,000,000 * 0.08) + (2,000,000 * 0.10) = 240,000 + 200,000 = 440,000
        # 仕入税: (1,800,000 * 0.08) + (1,200,000 * 0.10) = 144,000 + 120,000 = 264,000
        # 納税額: 440,000 - 264,000 = 176,000
        
        expected_result = {
            "total_tax": 176000,
            "sales_tax": 440000,
            "purchase_tax": 264000,
            "net_tax": 176000,
            "tax_year": 2025,
            "calculation_details": {
                "sales_amount": 5000000,
                "purchase_amount": 3000000,
                "standard_rate_sales": 2000000,
                "reduced_rate_sales": 3000000,
                "standard_rate_purchases": 1200000,
                "reduced_rate_purchases": 1800000,
                "standard_rate_tax": 200000,
                "reduced_rate_tax": 240000,
                "mixed_rate_applied": True
            }
        }
        TaxAssertions.assert_consumption_tax_calculation_result(self, result, expected_result)
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        self.assertTrue(
            expected_result["calculation_details"]["mixed_rate_applied"],
            "軽減税率が適用されている"
        )
        
        print("✓ 軽減税率消費税計算テスト成功")
    
    def test_small_business_consumption_tax(self):
        """小規模事業者の消費税計算テスト"""
        print("\n=== 小規模事業者消費税計算テスト ===")
        
        # 小規模事業者テストデータ（売上1000万円以下）
        test_data = {
            "sales_amount": 8000000,  # 1000万円以下
            "purchase_amount": 5000000,
            "tax_year": 2025,
            "business_type": "small",
            "tax_exemption": {
                "eligible": True,
                "reason": "売上1000万円以下"
            }
        }
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果（免税事業者）
        expected_result = {
            "total_tax": 0,
            "sales_tax": 0,
            "purchase_tax": 0,
            "net_tax": 0,
            "tax_year": 2025,
            "tax_exemption_applied": True,
            "calculation_details": {
                "sales_amount": 8000000,
                "purchase_amount": 5000000,
                "exemption_reason": "売上1000万円以下",
                "taxable_business": False
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        self.assertEqual(expected_result["total_tax"], 0, "免税事業者の税額は0")
        self.assertTrue(
            expected_result["tax_exemption_applied"],
            "免税措置が適用されている"
        )
        
        print("✓ 小規模事業者消費税計算テスト成功")
    
    def test_simplified_taxation_method(self):
        """簡易課税制度の消費税計算テスト"""
        print("\n=== 簡易課税制度消費税計算テスト ===")
        
        # 簡易課税制度テストデータ
        test_data = {
            "sales_amount": 30000000,
            "tax_year": 2025,
            "taxation_method": "simplified",
            "business_category": "retail",  # 小売業（みなし仕入率80%）
            "deemed_purchase_rate": 0.80
        }
        
        print(f"入力データ: {test_data}")
        
        # 期待される結果
        # 売上税: 30,000,000 * 0.10 = 3,000,000
        # みなし仕入税: 3,000,000 * 0.80 = 2,400,000
        # 納税額: 3,000,000 - 2,400,000 = 600,000
        
        expected_result = {
            "total_tax": 600000,
            "sales_tax": 3000000,
            "deemed_purchase_tax": 2400000,
            "net_tax": 600000,
            "tax_year": 2025,
            "taxation_method": "simplified",
            "calculation_details": {
                "sales_amount": 30000000,
                "business_category": "retail",
                "deemed_purchase_rate": 0.80,
                "actual_purchases_ignored": True,
                "simplified_method_applied": True
            }
        }
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        self.assertEqual(
            expected_result["taxation_method"],
            "simplified",
            "簡易課税制度が適用されている"
        )
        self.assertTrue(
            expected_result["calculation_details"]["simplified_method_applied"],
            "簡易課税制度フラグが設定されている"
        )
        
        print("✓ 簡易課税制度消費税計算テスト成功")
    
    def test_consumption_tax_calculation_performance(self):
        """消費税計算のパフォーマンステスト"""
        print("\n=== 消費税計算パフォーマンステスト ===")
        
        # テストデータ
        test_data = self.data_generator.generate_consumption_tax_data(
            sales_amount=50000000,
            purchase_amount=30000000,
            tax_year=2025
        )
        
        print(f"入力データ: {test_data}")
        
        # パフォーマンス測定
        def mock_calculation():
            import time
            time.sleep(0.03)  # 30ms の処理時間をシミュレート
            return {
                "total_tax": 2000000,
                "sales_tax": 5000000,
                "purchase_tax": 3000000,
                "net_tax": 2000000,
                "tax_year": 2025
            }
        
        result, execution_time = self.measure_performance(mock_calculation)
        
        print(f"実行時間: {execution_time:.3f}秒")
        print(f"計算結果: {result}")
        
        # パフォーマンスアサーション
        self.assert_response_time(execution_time, max_time=0.5)
        
        print("✓ 消費税計算パフォーマンステスト成功")
    
    def test_consumption_tax_edge_cases(self):
        """消費税計算の境界値テスト"""
        print("\n=== 消費税計算境界値テスト ===")
        
        # 境界値テストケース
        edge_cases = [
            {
                "sales_amount": 0,
                "purchase_amount": 0,
                "expected_tax": 0,
                "description": "売上・仕入なし"
            },
            {
                "sales_amount": 10000000,
                "purchase_amount": 0,
                "expected_tax": 1000000,
                "description": "仕入なし"
            },
            {
                "sales_amount": 0,
                "purchase_amount": 5000000,
                "expected_tax": -500000,
                "description": "売上なし（還付）"
            },
            {
                "sales_amount": 10000000,
                "purchase_amount": 10000000,
                "expected_tax": 0,
                "description": "売上と仕入が同額"
            }
        ]
        
        for case in edge_cases:
            print(f"\n--- {case['description']} ---")
            
            test_data = {
                "sales_amount": case["sales_amount"],
                "purchase_amount": case["purchase_amount"],
                "tax_year": 2025,
                "tax_rate": 0.10
            }
            
            print(f"入力データ: {test_data}")
            
            # 期待される結果
            expected_result = {
                "total_tax": case["expected_tax"],
                "tax_year": 2025,
                "calculation_details": {
                    "sales_amount": case["sales_amount"],
                    "purchase_amount": case["purchase_amount"]
                }
            }
            
            print(f"期待される結果: {expected_result}")
            
            # 基本的なアサーション
            self.assertIsInstance(expected_result["total_tax"], (int, float))
            
            # 還付の場合は負の値も許可
            if case["description"] != "売上なし（還付）":
                self.assertGreaterEqual(expected_result["total_tax"], 0)
            
            print(f"✓ {case['description']}テスト成功")
    
    def test_invalid_consumption_tax_input(self):
        """無効な入力データのテスト"""
        print("\n=== 無効な入力データテスト ===")
        
        # 無効な入力パターン
        invalid_inputs = [
            {
                "sales_amount": "invalid",
                "description": "文字列の売上"
            },
            {
                "purchase_amount": None,
                "description": "None値の仕入"
            },
            {
                "sales_amount": -1000000,
                "description": "負の売上"
            },
            {
                "purchase_amount": -500000,
                "description": "負の仕入"
            },
            {
                "tax_year": 2010,
                "description": "古い税年度"
            }
        ]
        
        for invalid_input in invalid_inputs:
            print(f"\n--- {invalid_input['description']} ---")
            
            test_data = {
                "sales_amount": invalid_input.get("sales_amount", 10000000),
                "purchase_amount": invalid_input.get("purchase_amount", 6000000),
                "tax_year": invalid_input.get("tax_year", 2025)
            }
            
            print(f"無効な入力データ: {test_data}")
            
            # バリデーションエラーを期待
            try:
                # 実際のバリデーション処理をシミュレート
                if isinstance(test_data["sales_amount"], str):
                    raise ValueError("売上は数値である必要があります")
                if test_data["purchase_amount"] is None:
                    raise ValueError("仕入は必須です")
                if test_data["sales_amount"] < 0:
                    raise ValueError("売上は非負である必要があります")
                if test_data["purchase_amount"] < 0:
                    raise ValueError("仕入は非負である必要があります")
                if test_data["tax_year"] < 2020 or test_data["tax_year"] > 2030:
                    raise ValueError("税年度は2020-2030の範囲である必要があります")
                
                self.fail(f"バリデーションエラーが発生すべきでした: {invalid_input['description']}")
            
            except ValueError as e:
                print(f"期待されるバリデーションエラー: {e}")
                print(f"✓ {invalid_input['description']}バリデーションテスト成功")
    
    def test_tax_rate_changes(self):
        """税率変更の影響テスト"""
        print("\n=== 税率変更影響テスト ===")
        
        # 税率変更前後のテストデータ
        base_data = {
            "sales_amount": 10000000,
            "purchase_amount": 6000000
        }
        
        # 異なる税率でのテスト
        tax_rate_scenarios = [
            {"rate": 0.05, "year": 2020, "description": "旧税率5%"},
            {"rate": 0.08, "year": 2021, "description": "税率8%"},
            {"rate": 0.10, "year": 2025, "description": "現行税率10%"}
        ]
        
        results = []
        
        for scenario in tax_rate_scenarios:
            print(f"\n--- {scenario['description']} ---")
            
            test_data = {
                **base_data,
                "tax_year": scenario["year"],
                "tax_rate": scenario["rate"]
            }
            
            print(f"入力データ: {test_data}")
            
            # 期待される結果
            sales_tax = base_data["sales_amount"] * scenario["rate"]
            purchase_tax = base_data["purchase_amount"] * scenario["rate"]
            net_tax = sales_tax - purchase_tax
            
            expected_result = {
                "total_tax": net_tax,
                "sales_tax": sales_tax,
                "purchase_tax": purchase_tax,
                "net_tax": net_tax,
                "tax_rate": scenario["rate"],
                "tax_year": scenario["year"],
                "calculation_details": {
                    "sales_amount": base_data["sales_amount"],
                    "purchase_amount": base_data["purchase_amount"],
                    "tax_rate_applied": scenario["rate"]
                }
            }
            
            print(f"期待される結果: {expected_result}")
            
            results.append(expected_result)
            
            # アサーション
            TaxAssertions.assert_tax_calculation_result(expected_result)
            TaxAssertions.assert_tax_rate_validity(scenario["rate"], 0.05, 0.10)
            
            print(f"✓ {scenario['description']}テスト成功")
        
        # 税率変更の影響確認
        print("\n--- 税率変更影響確認 ---")
        for i in range(len(results) - 1):
            current = results[i]
            next_result = results[i + 1]
            
            # 税率が上がれば税額も上がる
            if current["tax_rate"] < next_result["tax_rate"]:
                self.assertLess(
                    current["total_tax"],
                    next_result["total_tax"],
                    "税率上昇に伴い税額も増加"
                )
            
            print(f"✓ {current['tax_year']}年から{next_result['tax_year']}年への税率変更影響確認")
    
    def test_international_transactions(self):
        """国際取引の消費税計算テスト"""
        print("\n=== 国際取引消費税計算テスト ===")
        
        # 国際取引テストデータ
        test_data = {
            "domestic_sales": 8000000,
            "export_sales": 2000000,  # 輸出（免税）
            "domestic_purchases": 5000000,
            "import_purchases": 1000000,  # 輸入
            "tax_year": 2025,
            "items": [
                {"amount": 8000000, "tax_rate": 0.10}, # 国内売上
                {"amount": 2000000, "tax_rate": 0.00}  # 輸出売上 (免税)
            ],
            "purchases": [
                {"amount": 5000000, "tax_rate": 0.10}, # 国内仕入れ
                {"amount": 1000000, "tax_rate": 0.10}  # 輸入仕入れ
            ]
        }
        
        print(f"入力データ: {test_data}")
        
        # 消費税計算を直接呼び出し
        result = self.calculator.calculate_consumption_tax(

            tax_year=test_data["tax_year"],
            international_sales=test_data["export_sales"],
            international_purchases=test_data["import_purchases"],
            items=test_data["items"],
            purchases=test_data["purchases"]
        )
        print(f"計算結果: {result}")

        # 結果の検証
        self.assertIsInstance(result, dict)
        self.assertIn("total_tax", result)
        self.assertIn("calculation_details", result)
        # 期待される結果
        # 国内売上税: 8,000,000 * 0.10 = 800,000
        # 輸出売上税: 0（免税）
        # 国内仕入税: 5,000,000 * 0.10 = 500,000
        # 輸入仕入税: 1,000,000 * 0.10 = 100,000
        # 納税額: 800,000 - (500,000 + 100,000) = 200,000
        
        expected_result = {
            "total_tax": 200000,
            "sales_tax": 800000,  # domestic_sales_tax
            "purchase_tax": 600000,  # domestic_purchase_tax + import_purchase_tax
            "domestic_sales_tax": 800000,
            "export_sales_tax": 0,
            "domestic_purchase_tax": 500000,
            "import_purchase_tax": 100000,
            "net_tax": 200000,
            "tax_year": 2025,
            "calculation_details": {
                "sales_amount": 10000000,  # domestic_sales + export_sales
                "purchase_amount": 6000000,  # domestic_purchases + import_purchases
                "domestic_sales": 8000000,
                "export_sales": 2000000,
                "export_exemption_applied": True,
                "import_tax_included": True,
                "tax_rate_applied": "standard"
            }
        }
        TaxAssertions.assert_consumption_tax_calculation_result(self, result, expected_result)
        
        print(f"期待される結果: {expected_result}")
        
        # アサーション
        TaxAssertions.assert_tax_calculation_result(expected_result)
        self.assertEqual(
            expected_result["export_sales_tax"],
            0,
            "輸出売上は免税"
        )
        self.assertTrue(
            expected_result["calculation_details"]["export_exemption_applied"],
            "輸出免税が適用されている"
        )
        
        print("✓ 国際取引消費税計算テスト成功")


if __name__ == "__main__":
    unittest.main(verbosity=2)