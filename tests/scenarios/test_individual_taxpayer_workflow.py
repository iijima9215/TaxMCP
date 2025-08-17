#!/usr/bin/env python3
"""
TaxMCP Individual Taxpayer Workflow Tests

このモジュールは個人納税者の典型的なワークフローをテストします。
実際の使用シナリオに基づいて、エンドツーエンドのテストを実行します。
"""

import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tax_calculator import TaxCalculator
from rag_integration import RAGIntegration
from sqlite_indexer import SQLiteIndexer
from security import SecurityManager

class TestIndividualTaxpayerWorkflow(unittest.TestCase):
    """個人納税者ワークフローのテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        self.tax_calculator = TaxCalculator()
        self.rag_integration = Mock(spec=RAGIntegration)
        self.sqlite_indexer = Mock(spec=SQLiteIndexer)
        self.security_manager = Mock(spec=SecurityManager)
        
        # モックレスポンスの設定
        self._setup_mock_responses()
        
    def _setup_mock_responses(self):
        """モックレスポンスの設定"""
        # RAG検索のモックレスポンス
        self.rag_integration.search_legal_references.return_value = {
            'results': [
                {
                    'title': '所得税法第28条',
                    'content': '給与所得の計算方法について',
                    'relevance_score': 0.95
                }
            ]
        }
        
        # SQLite検索のモックレスポンス
        self.sqlite_indexer.search_documents.return_value = [
            {
                'id': 'doc_001',
                'title': '給与所得控除額表',
                'content': '給与所得控除額の計算表',
                'metadata': {'year': 2024, 'type': 'deduction_table'}
            }
        ]
        
        # セキュリティ認証のモックレスポンス
        self.security_manager.authenticate.return_value = True
        self.security_manager.authorize.return_value = True
        
    def test_salary_worker_annual_tax_calculation(self):
        """給与所得者の年間税額計算ワークフロー"""
        # 1. ユーザー認証
        auth_result = self.security_manager.authenticate('user123', 'password')
        self.assertTrue(auth_result)
        
        # 2. 給与所得者の基本情報
        taxpayer_data = {
            'name': '田中太郎',
            'age': 35,
            'marital_status': 'married',
            'dependents': 2,
            'annual_salary': 5000000,  # 500万円
            'social_insurance': 750000,  # 社会保険料
            'life_insurance': 120000,   # 生命保険料
            'spouse_deduction': True,
            'dependent_deduction': 2
        }
        
        # 3. 所得税計算
        income_tax_result = self.tax_calculator.calculate_income_tax(
            income=taxpayer_data['annual_salary'],
            deductions={
                'social_insurance': taxpayer_data['social_insurance'],
                'life_insurance': taxpayer_data['life_insurance'],
                'spouse': 380000 if taxpayer_data['spouse_deduction'] else 0,
                'dependents': taxpayer_data['dependent_deduction'] * 380000
            }
        )
        
        # 4. 住民税計算
        resident_tax_result = self.tax_calculator.calculate_resident_tax(
            income=taxpayer_data['annual_salary'],
            deductions={
                'social_insurance': taxpayer_data['social_insurance'],
                'life_insurance': taxpayer_data['life_insurance'],
                'spouse': 330000 if taxpayer_data['spouse_deduction'] else 0,
                'dependents': taxpayer_data['dependent_deduction'] * 330000
            }
        )
        
        # 5. 結果の検証
        self.assertIsInstance(income_tax_result, dict)
        self.assertIn('tax_amount', income_tax_result)
        self.assertIn('taxable_income', income_tax_result)
        self.assertGreater(income_tax_result['tax_amount'], 0)
        
        self.assertIsInstance(resident_tax_result, dict)
        self.assertIn('tax_amount', resident_tax_result)
        self.assertGreater(resident_tax_result['tax_amount'], 0)
        
        # 6. 法令参照の確認
        legal_refs = self.rag_integration.search_legal_references(
            query='給与所得控除 計算方法',
            tax_type='income_tax'
        )
        self.assertIsInstance(legal_refs, dict)
        self.assertIn('results', legal_refs)
        
    def test_freelancer_tax_calculation_workflow(self):
        """フリーランサーの税額計算ワークフロー"""
        # 1. フリーランサーの基本情報
        freelancer_data = {
            'name': '佐藤花子',
            'age': 28,
            'business_type': 'design',
            'annual_revenue': 8000000,  # 800万円
            'business_expenses': 2000000,  # 200万円
            'blue_form_deduction': 650000,  # 青色申告特別控除
            'social_insurance': 1200000,
            'national_pension': 200000
        }
        
        # 2. 事業所得の計算
        business_income = (
            freelancer_data['annual_revenue'] - 
            freelancer_data['business_expenses'] - 
            freelancer_data['blue_form_deduction']
        )
        
        # 3. 所得税計算
        income_tax_result = self.tax_calculator.calculate_income_tax(
            income=business_income,
            deductions={
                'social_insurance': freelancer_data['social_insurance'],
                'national_pension': freelancer_data['national_pension'],
                'basic': 480000  # 基礎控除
            }
        )
        
        # 4. 消費税計算（課税売上高が1000万円超の場合）
        consumption_tax_result = None
        if freelancer_data['annual_revenue'] > 10000000:
            consumption_tax_result = self.tax_calculator.calculate_consumption_tax(
                taxable_sales=freelancer_data['annual_revenue'],
                tax_rate=0.10
            )
        
        # 5. 結果の検証
        self.assertIsInstance(income_tax_result, dict)
        self.assertIn('tax_amount', income_tax_result)
        self.assertGreater(income_tax_result['tax_amount'], 0)
        
        # 6. 青色申告関連の法令参照
        blue_form_refs = self.rag_integration.search_legal_references(
            query='青色申告特別控除 要件',
            tax_type='income_tax'
        )
        self.assertIsInstance(blue_form_refs, dict)
        
    def test_property_income_workflow(self):
        """不動産所得者の税額計算ワークフロー"""
        # 1. 不動産所得者の基本情報
        property_owner_data = {
            'name': '山田次郎',
            'age': 45,
            'salary_income': 6000000,  # 給与所得
            'rental_income': 3600000,  # 家賃収入（年間）
            'property_expenses': {
                'depreciation': 800000,  # 減価償却費
                'repair': 200000,       # 修繕費
                'management': 360000,   # 管理費
                'insurance': 100000,    # 保険料
                'taxes': 150000         # 固定資産税
            },
            'social_insurance': 900000
        }
        
        # 2. 不動産所得の計算
        total_expenses = sum(property_owner_data['property_expenses'].values())
        property_income = property_owner_data['rental_income'] - total_expenses
        
        # 3. 総所得の計算
        total_income = property_owner_data['salary_income'] + property_income
        
        # 4. 所得税計算
        income_tax_result = self.tax_calculator.calculate_income_tax(
            income=total_income,
            deductions={
                'social_insurance': property_owner_data['social_insurance'],
                'basic': 480000
            }
        )
        
        # 5. 結果の検証
        self.assertIsInstance(income_tax_result, dict)
        self.assertIn('tax_amount', income_tax_result)
        self.assertGreater(income_tax_result['tax_amount'], 0)
        
        # 6. 不動産所得関連の法令参照
        property_refs = self.rag_integration.search_legal_references(
            query='不動産所得 必要経費 減価償却',
            tax_type='income_tax'
        )
        self.assertIsInstance(property_refs, dict)
        
    def test_medical_expense_deduction_workflow(self):
        """医療費控除申請ワークフロー"""
        # 1. 医療費控除申請者の情報
        medical_taxpayer_data = {
            'name': '鈴木一郎',
            'age': 55,
            'annual_income': 4500000,
            'medical_expenses': {
                'hospital': 350000,     # 入院費
                'medicine': 80000,      # 薬代
                'dental': 120000,       # 歯科治療
                'transportation': 15000  # 通院交通費
            },
            'insurance_reimbursement': 200000,  # 保険金
            'social_insurance': 675000
        }
        
        # 2. 医療費控除額の計算
        total_medical_expenses = sum(medical_taxpayer_data['medical_expenses'].values())
        net_medical_expenses = total_medical_expenses - medical_taxpayer_data['insurance_reimbursement']
        
        # 医療費控除額 = (実際に支払った医療費 - 保険金等) - 10万円（所得の5%との少ない方）
        income_threshold = min(100000, medical_taxpayer_data['annual_income'] * 0.05)
        medical_deduction = max(0, net_medical_expenses - income_threshold)
        
        # 3. 所得税計算（医療費控除適用）
        income_tax_result = self.tax_calculator.calculate_income_tax(
            income=medical_taxpayer_data['annual_income'],
            deductions={
                'social_insurance': medical_taxpayer_data['social_insurance'],
                'medical': medical_deduction,
                'basic': 480000
            }
        )
        
        # 4. 結果の検証
        self.assertIsInstance(income_tax_result, dict)
        self.assertIn('tax_amount', income_tax_result)
        self.assertGreater(medical_deduction, 0)  # 医療費控除が適用されることを確認
        
        # 5. 医療費控除関連の法令参照
        medical_refs = self.rag_integration.search_legal_references(
            query='医療費控除 対象 計算方法',
            tax_type='income_tax'
        )
        self.assertIsInstance(medical_refs, dict)
        
    def test_year_end_adjustment_workflow(self):
        """年末調整ワークフロー"""
        # 1. 年末調整対象者の情報
        adjustment_data = {
            'employee_id': 'EMP001',
            'name': '高橋美咲',
            'monthly_salary': 350000,
            'bonus': [500000, 500000],  # 夏・冬のボーナス
            'withholding_tax': 180000,  # 源泉徴収税額
            'insurance_premiums': {
                'life': 120000,
                'earthquake': 50000,
                'personal_pension': 68000
            },
            'dependents': [
                {'name': '高橋太郎', 'age': 8, 'type': 'child'},
                {'name': '高橋花子', 'age': 5, 'type': 'child'}
            ],
            'spouse': {'name': '高橋次郎', 'income': 800000}
        }
        
        # 2. 年間給与総額の計算
        annual_salary = (adjustment_data['monthly_salary'] * 12) + sum(adjustment_data['bonus'])
        
        # 3. 各種控除額の計算
        deductions = {
            'basic': 480000,  # 基礎控除
            'spouse': 380000 if adjustment_data['spouse']['income'] <= 1030000 else 0,
            'dependents': len(adjustment_data['dependents']) * 380000,
            'life_insurance': min(120000, adjustment_data['insurance_premiums']['life']),
            'earthquake_insurance': min(50000, adjustment_data['insurance_premiums']['earthquake']),
            'personal_pension': min(120000, adjustment_data['insurance_premiums']['personal_pension'])
        }
        
        # 4. 年末調整後の所得税計算
        final_tax_result = self.tax_calculator.calculate_income_tax(
            income=annual_salary,
            deductions=deductions
        )
        
        # 5. 還付・追徴税額の計算
        tax_difference = adjustment_data['withholding_tax'] - final_tax_result['tax_amount']
        
        # 6. 結果の検証
        self.assertIsInstance(final_tax_result, dict)
        self.assertIn('tax_amount', final_tax_result)
        self.assertIsInstance(tax_difference, (int, float))
        
        # 7. 年末調整関連の法令参照
        adjustment_refs = self.rag_integration.search_legal_references(
            query='年末調整 扶養控除 配偶者控除',
            tax_type='income_tax'
        )
        self.assertIsInstance(adjustment_refs, dict)
        
    def test_tax_return_filing_workflow(self):
        """確定申告ワークフロー"""
        # 1. 確定申告者の情報
        filing_data = {
            'taxpayer_id': 'TAX2024001',
            'name': '伊藤健一',
            'filing_type': 'comprehensive',  # 総合課税
            'income_sources': {
                'salary': 7200000,
                'business': 1800000,
                'dividend': 150000,
                'interest': 50000
            },
            'deductions': {
                'social_insurance': 1080000,
                'life_insurance': 120000,
                'donation': 100000,  # 寄附金控除
                'medical': 80000,
                'basic': 480000
            },
            'prepaid_tax': 850000  # 予定納税額
        }
        
        # 2. 総所得金額の計算
        total_income = sum(filing_data['income_sources'].values())
        
        # 3. 所得税の計算
        final_tax_calculation = self.tax_calculator.calculate_income_tax(
            income=total_income,
            deductions=filing_data['deductions']
        )
        
        # 4. 納付・還付税額の計算
        tax_balance = final_tax_calculation['tax_amount'] - filing_data['prepaid_tax']
        
        # 5. 申告書データの作成
        tax_return_data = {
            'taxpayer_info': {
                'id': filing_data['taxpayer_id'],
                'name': filing_data['name']
            },
            'income_summary': filing_data['income_sources'],
            'deduction_summary': filing_data['deductions'],
            'tax_calculation': final_tax_calculation,
            'payment_status': {
                'prepaid': filing_data['prepaid_tax'],
                'balance': tax_balance,
                'type': 'payment' if tax_balance > 0 else 'refund'
            },
            'filing_date': datetime.now().isoformat()
        }
        
        # 6. 結果の検証
        self.assertIsInstance(tax_return_data, dict)
        self.assertIn('tax_calculation', tax_return_data)
        self.assertIn('payment_status', tax_return_data)
        self.assertIsInstance(tax_balance, (int, float))
        
        # 7. 確定申告関連の法令参照
        filing_refs = self.rag_integration.search_legal_references(
            query='確定申告 総合課税 申告期限',
            tax_type='income_tax'
        )
        self.assertIsInstance(filing_refs, dict)
        
    def test_workflow_performance(self):
        """ワークフローのパフォーマンステスト"""
        start_time = time.time()
        
        # 複数の計算を連続実行
        test_cases = [
            {'income': 3000000, 'deductions': {'basic': 480000}},
            {'income': 5000000, 'deductions': {'basic': 480000, 'spouse': 380000}},
            {'income': 8000000, 'deductions': {'basic': 480000, 'dependents': 760000}}
        ]
        
        results = []
        for case in test_cases:
            result = self.tax_calculator.calculate_income_tax(
                income=case['income'],
                deductions=case['deductions']
            )
            results.append(result)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # パフォーマンス検証
        self.assertEqual(len(results), len(test_cases))
        self.assertLess(execution_time, 5.0)  # 5秒以内で完了
        
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertIn('tax_amount', result)
            
if __name__ == '__main__':
    unittest.main()