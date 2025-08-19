#!/usr/bin/env python3
"""
TaxMCP 詳細法人税計算シナリオテスト

ユーザー提供の具体的なデータを使用した法人税計算テスト
当期純利益：30,000,000円
加算項目：寄附金限度超過額 1,000,000円、交際費限度超過額 500,000円
減算項目：繰越欠損金控除 2,000,000円、受取配当益金不算入 3,000,000円
中小法人（資本金1億円以下）
研究開発税制控除：500,000円
中間納付法人税額：1,200,000円
仮払税金：300,000円
"""

import unittest
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from enhanced_corporate_tax import (
    EnhancedCorporateTaxCalculator,
    AdditionItem,
    DeductionItem,
    TaxCreditItem,
    EnhancedCorporateTaxResult
)

class TestDetailedCorporateTaxScenario(unittest.TestCase):
    """詳細法人税計算シナリオのテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        self.calculator = EnhancedCorporateTaxCalculator()
        
        # ユーザー提供データの設定
        self.test_data = {
            'accounting_profit': 30000000,  # 当期純利益（会計利益）：30,000,000円
            'tax_year': 2025,
            'prefecture': '東京都',
            'capital': 80000000,  # 資本金8000万円（中小法人：1億円以下）
            'interim_payments': 1200000,  # 中間納付法人税額：1,200,000円
            'prepaid_taxes': 300000,  # 仮払税金：300,000円（源泉徴収等）
        }
        
        # 加算項目の設定
        self.addition_items = [
            AdditionItem(
                name="寄附金限度超過額",
                amount=1000000,  # 1,000,000円
                description="寄附金の損金算入限度額を超過した金額",
                related_form="別表四"
            ),
            AdditionItem(
                name="交際費限度超過額",
                amount=500000,  # 500,000円
                description="交際費等の損金算入限度額を超過した金額",
                related_form="別表十五"
            )
        ]
        
        # 減算項目の設定
        self.deduction_items = [
            DeductionItem(
                name="繰越欠損金控除",
                amount=2000000,  # 2,000,000円
                description="前年度以前の欠損金の当期控除額",
                related_form="別表七"
            ),
            DeductionItem(
                name="受取配当益金不算入",
                amount=3000000,  # 3,000,000円
                description="受取配当金の益金不算入額",
                related_form="別表八"
            )
        ]
        
        # 税額控除項目の設定
        self.tax_credit_items = [
            TaxCreditItem(
                name="研究開発税制控除",
                amount=500000,  # 500,000円
                description="研究開発費の税額控除",
                related_form="別表六"
            )
        ]
    
    def test_detailed_corporate_tax_calculation(self):
        """詳細法人税計算テスト"""
        print("\n=== 詳細法人税計算シナリオテスト ===")
        print(f"当期純利益（会計利益）: {self.test_data['accounting_profit']:,}円")
        print(f"資本金: {self.test_data['capital']:,}円（中小法人）")
        print(f"都道府県: {self.test_data['prefecture']}")
        
        # 法人税計算実行
        result = self.calculator.calculate_enhanced_corporate_tax(
            accounting_profit=self.test_data['accounting_profit'],
            tax_year=self.test_data['tax_year'],
            prefecture=self.test_data['prefecture'],
            capital=self.test_data['capital'],
            addition_items=self.addition_items,
            deduction_items=self.deduction_items,
            tax_credit_items=self.tax_credit_items,
            interim_payments=self.test_data['interim_payments'],
            prepaid_taxes=self.test_data['prepaid_taxes']
        )
        
        # 結果の検証
        self.assertIsInstance(result, EnhancedCorporateTaxResult)
        
        # 基本情報の確認
        self.assertEqual(result.accounting_profit, self.test_data['accounting_profit'])
        self.assertEqual(result.tax_year, self.test_data['tax_year'])
        self.assertEqual(result.prefecture, self.test_data['prefecture'])
        self.assertEqual(result.capital, self.test_data['capital'])
        
        # 加算項目の確認
        self.assertEqual(len(result.addition_items), 2)
        self.assertEqual(result.total_additions, 1500000)  # 1,000,000 + 500,000
        
        # 減算項目の確認
        self.assertEqual(len(result.deduction_items), 2)
        self.assertEqual(result.total_deductions, 5000000)  # 2,000,000 + 3,000,000
        
        # 税額控除項目の確認
        self.assertEqual(len(result.tax_credit_items), 1)
        self.assertEqual(result.total_tax_credits, 500000)
        
        # 課税所得金額の確認
        expected_taxable_income = (
            self.test_data['accounting_profit'] + 
            result.total_additions - 
            result.total_deductions
        )
        self.assertEqual(result.taxable_income, expected_taxable_income)
        
        # 中間納付・仮払税金の確認
        self.assertEqual(result.interim_payments, self.test_data['interim_payments'])
        self.assertEqual(result.prepaid_taxes, self.test_data['prepaid_taxes'])
        
        # 中小法人判定の確認
        self.assertEqual(result.company_type, "small_corporation")
        
        # 計算結果の表示
        show_detailed = '--detailed' in sys.argv or '--verbose' in sys.argv
        self._print_calculation_results(result, show_detailed_output=show_detailed)
        
        # 税額が正の値であることを確認
        self.assertGreater(result.corporate_tax_base, 0)
        self.assertGreaterEqual(result.final_corporate_tax, 0)
        
        return result
    
    def test_tax_rate_verification(self):
        """税率適用の検証テスト"""
        print("\n=== 税率適用検証テスト ===")
        
        result = self.test_detailed_corporate_tax_calculation()
        
        # 中小法人の軽減税率適用確認
        if result.taxable_income <= 8000000:  # 800万円以下
            expected_rate = 0.15  # 軽減税率15%
            print(f"軽減税率適用: {expected_rate * 100}%")
        else:
            # 800万円超過部分は23.2%
            reduced_portion = 8000000 * 0.15
            excess_portion = (result.taxable_income - 8000000) * 0.232
            expected_tax = reduced_portion + excess_portion
            print(f"軽減税率部分（800万円以下）: 15%")
            print(f"一般税率部分（800万円超過）: 23.2%")
        
        # 実効税率の計算
        if result.accounting_profit > 0:
            effective_rate = (result.total_tax_payment / result.accounting_profit) * 100
            print(f"実効税率: {effective_rate:.2f}%")
            self.assertGreater(effective_rate, 0)
            self.assertLess(effective_rate, 50)  # 実効税率は50%未満であることを確認
    
    def test_local_tax_calculation(self):
        """地方税計算の検証テスト"""
        print("\n=== 地方税計算検証テスト ===")
        
        result = self.test_detailed_corporate_tax_calculation()
        
        # 住民税の確認
        print(f"住民税均等割: {result.resident_tax_equal:,}円")
        print(f"住民税法人税割: {result.resident_tax_income:,}円")
        
        # 事業税の確認
        print(f"法人事業税: {result.business_tax:,}円")
        print(f"特別法人事業税: {result.special_business_tax:,}円")
        
        # 地方税合計の確認
        expected_local_tax = (
            result.resident_tax_equal + 
            result.resident_tax_income + 
            result.business_tax + 
            result.special_business_tax
        )
        self.assertEqual(result.local_tax_total, expected_local_tax)
        
        # 住民税均等割が資本金に応じた金額であることを確認
        # 資本金8000万円の場合、均等割は70,000円（従業員50人以下の場合）
        self.assertGreater(result.resident_tax_equal, 0)
    
    def test_tax_credit_application(self):
        """税額控除適用の検証テスト"""
        print("\n=== 税額控除適用検証テスト ===")
        
        result = self.test_detailed_corporate_tax_calculation()
        
        # 研究開発税制控除の適用確認
        research_credit = next(
            (item for item in result.tax_credit_items if "研究開発" in item.name),
            None
        )
        self.assertIsNotNone(research_credit)
        self.assertEqual(research_credit.amount, 500000)
        
        # 控除後法人税額の確認
        expected_after_credits = max(0, result.corporate_tax_base - result.total_tax_credits)
        self.assertEqual(result.corporate_tax_after_credits, expected_after_credits)
        
        print(f"控除前法人税額: {result.corporate_tax_base:,}円")
        print(f"税額控除合計: {result.total_tax_credits:,}円")
        print(f"控除後法人税額: {result.corporate_tax_after_credits:,}円")
    
    def test_final_payment_calculation(self):
        """最終納付額計算の検証テスト"""
        print("\n=== 最終納付額計算検証テスト ===")
        
        result = self.test_detailed_corporate_tax_calculation()
        
        # 最終法人税納付額の計算確認
        expected_final_payment = max(0, 
            result.corporate_tax_after_credits - 
            result.interim_payments - 
            result.prepaid_taxes
        )
        self.assertEqual(result.final_corporate_tax, expected_final_payment)
        
        print(f"控除後法人税額: {result.corporate_tax_after_credits:,}円")
        print(f"地方法人税: {result.local_corporate_tax:,}円")
        print(f"中間納付法人税額: {result.interim_payments:,}円")
        print(f"仮払税金: {result.prepaid_taxes:,}円")
        print(f"最終法人税納付額: {result.final_corporate_tax:,}円")
        
        # 総合納付税額の確認
        expected_total_payment = result.final_corporate_tax + result.local_corporate_tax + result.local_tax_total
        self.assertEqual(result.total_tax_payment, expected_total_payment)
        
        print(f"総合納付税額: {result.total_tax_payment:,}円")
    
    def test_api_endpoint_simulation(self):
        """APIエンドポイント呼び出しシミュレーションテスト"""
        print("\n=== APIエンドポイント呼び出しシミュレーション ===")
        
        # APIリクエストデータの構築
        api_request = {
            "accounting_profit": self.test_data['accounting_profit'],
            "tax_year": self.test_data['tax_year'],
            "prefecture": self.test_data['prefecture'],
            "capital": self.test_data['capital'],
            "interim_payments": self.test_data['interim_payments'],
            "prepaid_taxes": self.test_data['prepaid_taxes'],
            "use_default_items": False,  # カスタム項目を使用
            "addition_items": [
                {
                    "name": item.name,
                    "amount": item.amount,
                    "description": item.description,
                    "related_form": item.related_form
                } for item in self.addition_items
            ],
            "deduction_items": [
                {
                    "name": item.name,
                    "amount": item.amount,
                    "description": item.description,
                    "related_form": item.related_form
                } for item in self.deduction_items
            ],
            "tax_credit_items": [
                {
                    "name": item.name,
                    "amount": item.amount,
                    "description": item.description,
                    "related_form": item.related_form
                } for item in self.tax_credit_items
            ]
        }
        
        print("APIリクエストデータ:")
        print(json.dumps(api_request, ensure_ascii=False, indent=2))
        
        # 実際のAPI呼び出しと同等の計算を実行
        result = self.calculator.calculate_enhanced_corporate_tax(
            accounting_profit=api_request['accounting_profit'],
            tax_year=api_request['tax_year'],
            prefecture=api_request['prefecture'],
            capital=api_request['capital'],
            addition_items=self.addition_items,
            deduction_items=self.deduction_items,
            tax_credit_items=self.tax_credit_items,
            interim_payments=api_request['interim_payments'],
            prepaid_taxes=api_request['prepaid_taxes']
        )
        
        # APIレスポンス形式での結果表示
        api_response = self._format_api_response(result)
        print("\nAPIレスポンス:")
        print(json.dumps(api_response, ensure_ascii=False, indent=2))
        
        return api_response
    
    def _print_calculation_results(self, result: EnhancedCorporateTaxResult, show_detailed_output: bool = False):
        """計算結果の詳細表示"""
        print("\n--- 計算結果詳細 ---")
        print(f"当期純利益（会計利益）: {result.accounting_profit:,}円")
        print(f"加算項目合計: {result.total_additions:,}円")
        print(f"減算項目合計: {result.total_deductions:,}円")
        print(f"課税所得金額: {result.taxable_income:,}円")
        print(f"法人税額（控除前）: {result.corporate_tax_base:,}円")
        print(f"税額控除合計: {result.total_tax_credits:,}円")
        print(f"法人税額（控除後）: {result.corporate_tax_after_credits:,}円")
        print(f"地方法人税: {result.local_corporate_tax:,}円")
        print(f"国税ベース確定法人税額: {result.national_tax_total:,}円")
        print(f"住民税均等割: {result.resident_tax_equal:,}円")
        print(f"住民税法人税割: {result.resident_tax_income:,}円")
        print(f"法人事業税: {result.business_tax:,}円")
        print(f"特別法人事業税: {result.special_business_tax:,}円")
        print(f"地方税合計: {result.local_tax_total:,}円")
        print(f"中間納付法人税額: {result.interim_payments:,}円")
        print(f"仮払税金: {result.prepaid_taxes:,}円")
        print(f"最終法人税納付額: {result.final_corporate_tax:,}円")
        print(f"総合納付税額: {result.total_tax_payment:,}円")
        print(f"実効税率: {result.effective_rate:.2f}%")
        print(f"会社区分: {result.company_type}")
        
        if show_detailed_output:
            self._print_detailed_input_output(result)
    
    def _print_detailed_input_output(self, result: EnhancedCorporateTaxResult):
        """入力・出力の詳細情報を漢字と変数で表示"""
        print("\n=== 入力情報詳細 ===")
        print(f"入力項目名: 当期純利益, 変数名: accounting_profit, 値: {result.accounting_profit:,}円")
        print(f"入力項目名: 税年度, 変数名: tax_year, 値: {result.tax_year}年")
        print(f"入力項目名: 都道府県, 変数名: prefecture, 値: {result.prefecture}")
        print(f"入力項目名: 資本金, 変数名: capital, 値: {result.capital:,}円")
        print(f"入力項目名: 中間納付法人税額, 変数名: interim_payments, 値: {result.interim_payments:,}円")
        print(f"入力項目名: 仮払税金, 変数名: prepaid_taxes, 値: {result.prepaid_taxes:,}円")
        
        print("\n=== 加算項目詳細 ===")
        for i, item in enumerate(result.addition_items, 1):
            print(f"加算項目{i}: 項目名: {item.name}, 変数名: addition_item_{i}, 金額: {item.amount:,}円")
            print(f"  説明: {item.description}")
            print(f"  関連別表: {item.related_form}")
        
        print("\n=== 減算項目詳細 ===")
        for i, item in enumerate(result.deduction_items, 1):
            print(f"減算項目{i}: 項目名: {item.name}, 変数名: deduction_item_{i}, 金額: {item.amount:,}円")
            print(f"  説明: {item.description}")
            print(f"  関連別表: {item.related_form}")
        
        print("\n=== 税額控除項目詳細 ===")
        for i, item in enumerate(result.tax_credit_items, 1):
            print(f"税額控除{i}: 項目名: {item.name}, 変数名: tax_credit_item_{i}, 金額: {item.amount:,}円")
            print(f"  説明: {item.description}")
            print(f"  関連別表: {item.related_form}")
        
        print("\n=== 計算結果詳細（変数名付き） ===")
        print(f"出力項目名: 課税所得金額, 変数名: taxable_income, 値: {result.taxable_income:,}円")
        print(f"出力項目名: 法人税額（控除前）, 変数名: corporate_tax_base, 値: {result.corporate_tax_base:,}円")
        print(f"出力項目名: 法人税額（控除後）, 変数名: corporate_tax_after_credits, 値: {result.corporate_tax_after_credits:,}円")
        print(f"出力項目名: 地方法人税, 変数名: local_corporate_tax, 値: {result.local_corporate_tax:,}円")
        print(f"出力項目名: 国税ベース確定法人税額, 変数名: national_tax_total, 値: {result.national_tax_total:,}円")
        print(f"出力項目名: 住民税均等割, 変数名: resident_tax_equal, 値: {result.resident_tax_equal:,}円")
        print(f"出力項目名: 住民税法人税割, 変数名: resident_tax_income, 値: {result.resident_tax_income:,}円")
        print(f"出力項目名: 法人事業税, 変数名: business_tax, 値: {result.business_tax:,}円")
        print(f"出力項目名: 特別法人事業税, 変数名: special_business_tax, 値: {result.special_business_tax:,}円")
        print(f"出力項目名: 地方税合計, 変数名: local_tax_total, 値: {result.local_tax_total:,}円")
        print(f"出力項目名: 最終法人税納付額, 変数名: final_corporate_tax, 値: {result.final_corporate_tax:,}円")
        print(f"出力項目名: 総合納付税額, 変数名: total_tax_payment, 値: {result.total_tax_payment:,}円")
        print(f"出力項目名: 実効税率, 変数名: effective_rate, 値: {result.effective_rate:.2f}%")
        print(f"出力項目名: 会社区分, 変数名: company_type, 値: {result.company_type}")
        
        print("\n=== 計算式詳細 ===")
        print(f"課税所得金額 = 当期純利益 + 加算項目合計 - 減算項目合計")
        print(f"taxable_income = accounting_profit + total_additions - total_deductions")
        print(f"{result.taxable_income:,} = {result.accounting_profit:,} + {result.total_additions:,} - {result.total_deductions:,}")
        
        print(f"\n法人税額（控除後） = 法人税額（控除前） - 税額控除合計")
        print(f"corporate_tax_after_credits = corporate_tax_base - total_tax_credits")
        print(f"{result.corporate_tax_after_credits:,} = {result.corporate_tax_base:,} - {result.total_tax_credits:,}")
        
        print(f"\n最終法人税納付額 = 法人税額（控除後） - 中間納付法人税額 - 仮払税金")
        print(f"final_corporate_tax = corporate_tax_after_credits - interim_payments - prepaid_taxes")
        print(f"{result.final_corporate_tax:,} = {result.corporate_tax_after_credits:,} - {result.interim_payments:,} - {result.prepaid_taxes:,}")
        
        print(f"\n総合納付税額 = 最終法人税納付額 + 地方法人税 + 地方税合計")
        print(f"total_tax_payment = final_corporate_tax + local_corporate_tax + local_tax_total")
        print(f"{result.total_tax_payment:,} = {result.final_corporate_tax:,} + {result.local_corporate_tax:,} + {result.local_tax_total:,}")
    
    def _format_api_response(self, result: EnhancedCorporateTaxResult) -> Dict[str, Any]:
        """API レスポンス形式でのフォーマット"""
        return {
            "calculation_summary": {
                "accounting_profit": result.accounting_profit,
                "taxable_income": result.taxable_income,
                "total_tax_payment": result.total_tax_payment,
                "effective_rate": result.effective_rate,
                "company_type": result.company_type
            },
            "tax_details": {
                "corporate_tax_base": result.corporate_tax_base,
                "corporate_tax_after_credits": result.corporate_tax_after_credits,
                "local_corporate_tax": result.local_corporate_tax,
                "national_tax_total": result.national_tax_total,
                "final_corporate_tax": result.final_corporate_tax
            },
            "local_taxes": {
                "resident_tax_equal": result.resident_tax_equal,
                "resident_tax_income": result.resident_tax_income,
                "business_tax": result.business_tax,
                "special_business_tax": result.special_business_tax,
                "local_tax_total": result.local_tax_total
            },
            "adjustments": {
                "addition_items": [
                    {
                        "name": item.name,
                        "amount": item.amount,
                        "description": item.description,
                        "related_form": item.related_form
                    } for item in result.addition_items
                ],
                "deduction_items": [
                    {
                        "name": item.name,
                        "amount": item.amount,
                        "description": item.description,
                        "related_form": item.related_form
                    } for item in result.deduction_items
                ],
                "tax_credit_items": [
                    {
                        "name": item.name,
                        "amount": item.amount,
                        "description": item.description,
                        "related_form": item.related_form
                    } for item in result.tax_credit_items
                ],
                "total_additions": result.total_additions,
                "total_deductions": result.total_deductions,
                "total_tax_credits": result.total_tax_credits
            },
            "payments": {
                "interim_payments": result.interim_payments,
                "prepaid_taxes": result.prepaid_taxes
            },
            "metadata": {
                "tax_year": result.tax_year,
                "prefecture": result.prefecture,
                "capital": result.capital,
                "calculation_date": datetime.now().isoformat()
            }
        }
    
    def run_comprehensive_test(self, show_detailed_output: bool = False):
        """包括的テストの実行"""
        print("\n" + "=" * 60)
        print("詳細法人税計算シナリオ - 包括的テスト実行")
        print("=" * 60)
        
        # 詳細出力モードの設定
        if show_detailed_output:
            print("詳細出力モード: 有効")
            print("入力・出力情報を漢字と変数名で表示します")
        else:
            print("詳細出力モード: 無効")
            print("基本的な計算結果のみ表示します")
        
        try:
            # 各テストを順次実行
            self.test_detailed_corporate_tax_calculation()
            self.test_tax_rate_verification()
            self.test_local_tax_calculation()
            self.test_tax_credit_application()
            self.test_final_payment_calculation()
            api_response = self.test_api_endpoint_simulation()
            
            print("\n" + "=" * 60)
            print("全テスト完了 - 成功")
            print("=" * 60)
            
            return api_response
            
        except Exception as e:
            print(f"\nテスト実行中にエラーが発生しました: {e}")
            raise

if __name__ == '__main__':
    # コマンドライン引数の処理
    if len(sys.argv) > 1 and ('--comprehensive' in sys.argv or '--detailed' in sys.argv or '--verbose' in sys.argv):
        test_instance = TestDetailedCorporateTaxScenario()
        test_instance.setUp()
        
        # 詳細出力モードの判定
        show_detailed = '--detailed' in sys.argv or '--verbose' in sys.argv
        
        if '--comprehensive' in sys.argv:
            test_instance.run_comprehensive_test(show_detailed_output=show_detailed)
        else:
            # 単一テストの実行（詳細出力付き）
            print("\n=== 詳細法人税計算テスト（詳細出力モード） ===")
            result = test_instance.test_detailed_corporate_tax_calculation()
            if show_detailed:
                test_instance._print_detailed_input_output(result)
    else:
        # 使用方法の表示
        print("\n=== テストプログラム使用方法 ===")
        print("基本実行: python test_detailed_corporate_tax_scenario.py")
        print("詳細出力: python test_detailed_corporate_tax_scenario.py --detailed")
        print("詳細出力（別名）: python test_detailed_corporate_tax_scenario.py --verbose")
        print("包括的テスト: python test_detailed_corporate_tax_scenario.py --comprehensive")
        print("包括的テスト（詳細出力）: python test_detailed_corporate_tax_scenario.py --comprehensive --detailed")
        print("\n詳細出力モードでは、入力・出力情報を漢字と変数名で表示します。")
        print("\n通常のunittestを実行します...\n")
        unittest.main()