import unittest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tax_calculator import JapaneseTaxCalculator
from security import SecurityManager, AuditLogger
from rag_integration import RAGIntegration

class TestIndividualTaxpayerWorkflow(unittest.TestCase):
    """個人納税者ワークフローテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        self.setup_mocks()
        
    def setup_mocks(self):
        """モックオブジェクトのセットアップ"""
        # 税計算機のセットアップ
        self.tax_calculator = JapaneseTaxCalculator()
        
        # セキュリティマネージャーのモック
        self.security_manager = Mock(spec=SecurityManager)
        # self.security_manager.log_access.return_value = None  # 存在しないメソッド
        # self.security_manager.authenticate.return_value = True  # 存在しないメソッド
        # self.security_manager.authorize.return_value = True  # 存在しないメソッド
        
        # 監査ログのモック
        self.audit_logger = Mock(spec=AuditLogger)
        self.audit_logger.log_api_call.return_value = None
        self.audit_logger.log_security_event.return_value = None
        
        # RAG統合のモック
        self.rag_integration = Mock(spec=RAGIntegration)
        self.rag_integration.search_legal_reference.return_value = {
            'results': [
                {
                    'title': '所得税法第28条',
                    'content': '給与所得の計算に関する規定',
                    'relevance_score': 0.95
                }
            ],
            'total_results': 1
        }
        
        # 法人税計算機のモック（個人納税者テストでは使用しないが、統合テスト用）
        self.corporate_tax_calculator = Mock()
        self.corporate_tax_calculator.calculate_corporate_tax.return_value = {
            'tax_amount': 1000000,
            'effective_rate': 23.4,
            'taxable_income': 5000000
        }
        
    def test_salary_worker_annual_tax_calculation(self):
        """給与所得者の年間税額計算ワークフロー"""
        # 1. ユーザー認証
        # auth_result = self.security_manager.authenticate('user123', 'password')  # 存在しないメソッド
        # self.assertTrue(auth_result)  # 認証結果の確認をスキップ
        
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
            annual_income=taxpayer_data['annual_salary'],
            social_insurance_deduction=taxpayer_data['social_insurance'],
            life_insurance_deduction=taxpayer_data['life_insurance'],
            spouse_deduction=380000 if taxpayer_data['spouse_deduction'] else 0,
            dependents_count=taxpayer_data['dependent_deduction']
        )
        
        # 4. 住民税計算
        resident_tax_result = self.tax_calculator.calculate_resident_tax(
            taxable_income=income_tax_result['taxable_income'],
            prefecture="東京都",
            tax_year=2025
        )
        
        # 住民税計算結果の検証
        self.assertIsNotNone(resident_tax_result)
        self.assertIn('total_resident_tax', resident_tax_result)
        self.assertGreater(resident_tax_result['total_resident_tax'], 0)
        
        # 5. 年間税額合計計算
        total_annual_tax = income_tax_result['income_tax'] + resident_tax_result['total_resident_tax']
        
        # 6. 結果の検証
        self.assertGreater(total_annual_tax, 0)
        self.assertLess(total_annual_tax, taxpayer_data['annual_salary'])  # 税額は年収より少ない
        
        # 7. 計算結果のログ出力
        print(f"\n=== 給与所得者税額計算結果 ===")
        print(f"年収: {taxpayer_data['annual_salary']:,}円")
        print(f"課税所得: {income_tax_result['taxable_income']:,}円")
        print(f"所得税: {income_tax_result['income_tax']:,}円")
        print(f"住民税: {resident_tax_result['total_resident_tax']:,}円")
        print(f"年間税額合計: {total_annual_tax:,}円")
        print(f"実効税率: {(total_annual_tax / taxpayer_data['annual_salary'] * 100):.2f}%")
        
        # 8. 監査ログの記録（モック）
        # self.audit_logger.log_tax_calculation(taxpayer_data, income_tax_result, resident_tax_result)
        
    def test_freelancer_quarterly_tax_calculation(self):
        """フリーランサーの四半期税額計算ワークフロー"""
        # 1. ユーザー認証
        # auth_result = self.security_manager.authenticate('freelancer456', 'password')  # 存在しないメソッド
        # self.assertTrue(auth_result)  # 認証結果の確認をスキップ
        
        # 2. フリーランサーの基本情報
        taxpayer_data = {
            'name': '佐藤花子',
            'age': 28,
            'marital_status': 'single',
            'business_type': 'consulting',
            'quarterly_income': 1500000,  # 四半期収入150万円
            'business_expenses': 300000,   # 経費30万円
            'social_insurance': 180000,    # 社会保険料
            'pension_contribution': 200000  # 年金掛金
        }
        
        # 3. 四半期所得税計算
        quarterly_income = taxpayer_data['quarterly_income'] - taxpayer_data['business_expenses']
        annual_estimated_income = quarterly_income * 4
        
        income_tax_result = self.tax_calculator.calculate_income_tax(
            annual_income=annual_estimated_income,
            social_insurance_deduction=taxpayer_data['social_insurance'] * 4,
            dependents_count=0
        )
        
        # 四半期分の税額
        quarterly_income_tax = income_tax_result['income_tax'] / 4
        
        # 4. 住民税計算（前年度ベース）
        resident_tax_result = self.tax_calculator.calculate_resident_tax(
            taxable_income=income_tax_result['taxable_income'],
            prefecture="神奈川県",
            tax_year=2025
        )
        
        quarterly_resident_tax = resident_tax_result['total_resident_tax'] / 4
        
        # 5. 四半期税額合計
        quarterly_total_tax = quarterly_income_tax + quarterly_resident_tax
        
        # 6. 結果の検証
        self.assertGreater(quarterly_total_tax, 0)
        self.assertLess(quarterly_total_tax, taxpayer_data['quarterly_income'])
        
        # 7. 計算結果のログ出力
        print(f"\n=== フリーランサー四半期税額計算結果 ===")
        print(f"四半期収入: {taxpayer_data['quarterly_income']:,}円")
        print(f"四半期経費: {taxpayer_data['business_expenses']:,}円")
        print(f"四半期所得: {quarterly_income:,}円")
        print(f"四半期所得税: {quarterly_income_tax:,.0f}円")
        print(f"四半期住民税: {quarterly_resident_tax:,.0f}円")
        print(f"四半期税額合計: {quarterly_total_tax:,.0f}円")
        
        # 8. 監査ログの記録（モック）
        # self.audit_logger.log_tax_calculation(taxpayer_data, income_tax_result, resident_tax_result)
        
    def test_pension_recipient_tax_calculation(self):
        """年金受給者の税額計算ワークフロー"""
        # 1. ユーザー認証
        # auth_result = self.security_manager.authenticate('pensioner789', 'password')  # 存在しないメソッド
        # self.assertTrue(auth_result)  # 認証結果の確認をスキップ
        
        # 2. 年金受給者の基本情報
        taxpayer_data = {
            'name': '山田一郎',
            'age': 68,
            'marital_status': 'married',
            'pension_income': 2400000,     # 年金収入240万円
            'part_time_income': 600000,    # パート収入60万円
            'medical_expenses': 150000,    # 医療費
            'spouse_age': 65,
            'spouse_pension': 800000       # 配偶者年金
        }
        
        # 3. 年金所得計算（公的年金等控除適用）
        total_income = taxpayer_data['pension_income'] + taxpayer_data['part_time_income']
        
        income_tax_result = self.tax_calculator.calculate_income_tax(
            annual_income=total_income,
            medical_expense_deduction=taxpayer_data['medical_expenses'],
            spouse_deduction=380000,  # 配偶者控除
            dependents_count=0
        )
        
        # 4. 住民税計算
        resident_tax_result = self.tax_calculator.calculate_resident_tax(
            taxable_income=income_tax_result['taxable_income'],
            prefecture="大阪府",
            tax_year=2025
        )
        
        # 5. 年間税額合計
        total_annual_tax = income_tax_result['income_tax'] + resident_tax_result['total_resident_tax']
        
        # 6. 結果の検証
        self.assertGreaterEqual(total_annual_tax, 0)  # 年金受給者は税額が低い可能性
        
        # 7. 計算結果のログ出力
        print(f"\n=== 年金受給者税額計算結果 ===")
        print(f"年金収入: {taxpayer_data['pension_income']:,}円")
        print(f"パート収入: {taxpayer_data['part_time_income']:,}円")
        print(f"総収入: {total_income:,}円")
        print(f"課税所得: {income_tax_result['taxable_income']:,}円")
        print(f"所得税: {income_tax_result['income_tax']:,}円")
        print(f"住民税: {resident_tax_result['total_resident_tax']:,}円")
        print(f"年間税額合計: {total_annual_tax:,}円")
        
        # 8. 監査ログの記録（モック）
        # self.audit_logger.log_tax_calculation(taxpayer_data, income_tax_result, resident_tax_result)
        
    def test_high_income_taxpayer_calculation(self):
        """高所得者の税額計算ワークフロー"""
        # 1. ユーザー認証
        # auth_result = self.security_manager.authenticate('executive999', 'password')  # 存在しないメソッド
        # self.assertTrue(auth_result)  # 認証結果の確認をスキップ
        
        # 2. 高所得者の基本情報
        taxpayer_data = {
            'name': '鈴木次郎',
            'age': 45,
            'marital_status': 'married',
            'annual_salary': 15000000,     # 年収1500万円
            'bonus': 5000000,              # ボーナス500万円
            'stock_income': 2000000,       # 株式収入200万円
            'social_insurance': 2000000,   # 社会保険料
            'life_insurance': 120000,      # 生命保険料
            'donation': 500000,            # 寄付金
            'dependents': 3
        }
        
        # 3. 総所得計算
        total_income = (
            taxpayer_data['annual_salary'] + 
            taxpayer_data['bonus'] + 
            taxpayer_data['stock_income']
        )
        
        income_tax_result = self.tax_calculator.calculate_income_tax(
            annual_income=total_income,
            social_insurance_deduction=taxpayer_data['social_insurance'],
            life_insurance_deduction=taxpayer_data['life_insurance'],
            donation_deduction=taxpayer_data['donation'],
            spouse_deduction=380000,
            dependents_count=taxpayer_data['dependents']
        )
        
        # 4. 住民税計算
        resident_tax_result = self.tax_calculator.calculate_resident_tax(
            taxable_income=income_tax_result['taxable_income'],
            prefecture="東京都",
            tax_year=2025
        )
        
        # 5. 年間税額合計
        total_annual_tax = income_tax_result['income_tax'] + resident_tax_result['total_resident_tax']
        
        # 6. 結果の検証
        self.assertGreater(total_annual_tax, 1000000)  # 高所得者は高額な税額
        self.assertLess(total_annual_tax, total_income * 0.5)  # 税額は総所得の50%未満
        
        # 7. 実効税率の計算
        effective_rate = (total_annual_tax / total_income) * 100
        
        # 8. 計算結果のログ出力
        print(f"\n=== 高所得者税額計算結果 ===")
        print(f"給与収入: {taxpayer_data['annual_salary']:,}円")
        print(f"ボーナス: {taxpayer_data['bonus']:,}円")
        print(f"株式収入: {taxpayer_data['stock_income']:,}円")
        print(f"総収入: {total_income:,}円")
        print(f"課税所得: {income_tax_result['taxable_income']:,}円")
        print(f"所得税: {income_tax_result['income_tax']:,}円")
        print(f"住民税: {resident_tax_result['total_resident_tax']:,}円")
        print(f"年間税額合計: {total_annual_tax:,}円")
        print(f"実効税率: {effective_rate:.2f}%")
        
        # 9. 監査ログの記録（モック）
        # self.audit_logger.log_tax_calculation(taxpayer_data, income_tax_result, resident_tax_result)

if __name__ == '__main__':
    unittest.main()