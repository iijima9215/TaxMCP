#!/usr/bin/env python3
"""
TaxMCP Corporate Taxpayer Workflow Tests

このモジュールは法人納税者の典型的なワークフローをテストします。
法人税計算、消費税申告、各種届出などのエンドツーエンドテストを実行します。
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

class TestCorporateTaxpayerWorkflow(unittest.TestCase):
    """法人納税者ワークフローのテストクラス"""
    
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
                    'title': '法人税法第22条',
                    'content': '各事業年度の所得の金額の計算',
                    'relevance_score': 0.95
                }
            ]
        }
        
        # SQLite検索のモックレスポンス
        self.sqlite_indexer.search_documents.return_value = [
            {
                'id': 'corp_doc_001',
                'title': '法人税率表',
                'content': '法人税の税率に関する資料',
                'metadata': {'year': 2024, 'type': 'tax_rate_table'}
            }
        ]
        
        # セキュリティ認証のモックレスポンス
        self.security_manager.authenticate.return_value = True
        self.security_manager.authorize.return_value = True
        
    def test_small_corporation_tax_calculation(self):
        """中小企業の法人税計算ワークフロー"""
        # 1. 企業認証
        auth_result = self.security_manager.authenticate('corp123', 'corp_password')
        self.assertTrue(auth_result)
        
        # 2. 中小企業の基本情報
        corporation_data = {
            'company_name': '株式会社サンプル',
            'company_type': 'small_corporation',
            'capital': 50000000,  # 資本金5000万円
            'fiscal_year_end': '2024-03-31',
            'business_year': 12,  # 12ヶ月
            'financial_data': {
                'revenue': 800000000,      # 売上高8億円
                'cost_of_sales': 480000000, # 売上原価
                'operating_expenses': 250000000, # 販管費
                'non_operating_income': 5000000,  # 営業外収益
                'non_operating_expenses': 8000000, # 営業外費用
                'extraordinary_income': 0,
                'extraordinary_expenses': 2000000
            },
            'deductions': {
                'depreciation': 15000000,
                'bad_debt': 3000000,
                'entertainment': 2000000,  # 交際費（上限あり）
                'donations': 1000000
            }
        }
        
        # 3. 所得金額の計算
        financial = corporation_data['financial_data']
        operating_income = financial['revenue'] - financial['cost_of_sales'] - financial['operating_expenses']
        ordinary_income = operating_income + financial['non_operating_income'] - financial['non_operating_expenses']
        net_income_before_tax = ordinary_income + financial['extraordinary_income'] - financial['extraordinary_expenses']
        
        # 4. 法人税計算
        corporate_tax_result = self.tax_calculator.calculate_corporate_tax(
            income=net_income_before_tax,
            company_type='small_corporation',
            capital=corporation_data['capital']
        )
        
        # 5. 結果の検証
        self.assertIsInstance(corporate_tax_result, dict)
        self.assertIn('tax_amount', corporate_tax_result)
        self.assertIn('effective_rate', corporate_tax_result)
        self.assertGreater(corporate_tax_result['tax_amount'], 0)
        
        # 中小企業の軽減税率が適用されることを確認
        if net_income_before_tax <= 8000000:  # 800万円以下
            expected_rate = 0.15  # 軽減税率15%
        else:
            expected_rate = 0.234  # 一般税率23.4%
        
        # 6. 法令参照の確認
        legal_refs = self.rag_integration.search_legal_references(
            query='法人税 中小企業 軽減税率',
            tax_type='corporate_tax'
        )
        self.assertIsInstance(legal_refs, dict)
        
    def test_large_corporation_tax_calculation(self):
        """大企業の法人税計算ワークフロー"""
        # 1. 大企業の基本情報
        large_corp_data = {
            'company_name': '大手商事株式会社',
            'company_type': 'large_corporation',
            'capital': 5000000000,  # 資本金50億円
            'fiscal_year_end': '2024-03-31',
            'financial_data': {
                'revenue': 50000000000,     # 売上高500億円
                'cost_of_sales': 30000000000,
                'operating_expenses': 15000000000,
                'non_operating_income': 500000000,
                'non_operating_expenses': 300000000,
                'extraordinary_income': 100000000,
                'extraordinary_expenses': 200000000
            },
            'special_items': {
                'foreign_tax_credit': 50000000,  # 外国税額控除
                'research_credit': 100000000,    # 研究開発税制
                'investment_credit': 80000000    # 投資促進税制
            }
        }
        
        # 2. 所得金額の計算
        financial = large_corp_data['financial_data']
        net_income = (
            financial['revenue'] - financial['cost_of_sales'] - 
            financial['operating_expenses'] + financial['non_operating_income'] - 
            financial['non_operating_expenses'] + financial['extraordinary_income'] - 
            financial['extraordinary_expenses']
        )
        
        # 3. 法人税計算（大企業）
        corporate_tax_result = self.tax_calculator.calculate_corporate_tax(
            income=net_income,
            company_type='large_corporation',
            capital=large_corp_data['capital']
        )
        
        # 4. 税額控除の適用
        total_credits = sum(large_corp_data['special_items'].values())
        final_tax = max(0, corporate_tax_result['tax_amount'] - total_credits)
        
        # 5. 結果の検証
        self.assertIsInstance(corporate_tax_result, dict)
        self.assertGreater(corporate_tax_result['tax_amount'], 0)
        self.assertGreaterEqual(final_tax, 0)
        
        # 6. 大企業向け法令参照
        large_corp_refs = self.rag_integration.search_legal_references(
            query='法人税 外国税額控除 研究開発税制',
            tax_type='corporate_tax'
        )
        self.assertIsInstance(large_corp_refs, dict)
        
    def test_consumption_tax_filing_workflow(self):
        """消費税申告ワークフロー"""
        # 1. 消費税課税事業者の情報
        vat_taxpayer_data = {
            'company_name': '製造業株式会社',
            'registration_number': 'T1234567890123',  # 適格請求書発行事業者登録番号
            'filing_period': 'quarterly',  # 四半期申告
            'calculation_method': 'general',  # 一般課税
            'sales_data': {
                'domestic_taxable': 2000000000,    # 国内課税売上
                'domestic_tax_free': 100000000,    # 国内非課税売上
                'export_sales': 300000000,         # 輸出売上
                'tax_collected': 200000000         # 預かり消費税
            },
            'purchase_data': {
                'domestic_purchases': 1200000000,   # 国内課税仕入
                'import_purchases': 200000000,      # 輸入仕入
                'tax_paid': 140000000              # 支払消費税
            }
        }
        
        # 2. 消費税計算
        consumption_tax_result = self.tax_calculator.calculate_consumption_tax(
            taxable_sales=vat_taxpayer_data['sales_data']['domestic_taxable'],
            tax_rate=0.10,
            input_tax=vat_taxpayer_data['purchase_data']['tax_paid']
        )
        
        # 3. 納付税額の計算
        tax_to_pay = (
            vat_taxpayer_data['sales_data']['tax_collected'] - 
            vat_taxpayer_data['purchase_data']['tax_paid']
        )
        
        # 4. 結果の検証
        self.assertIsInstance(consumption_tax_result, dict)
        self.assertIn('tax_amount', consumption_tax_result)
        self.assertIsInstance(tax_to_pay, (int, float))
        
        # 5. 適格請求書等保存方式の確認
        invoice_system_refs = self.rag_integration.search_legal_references(
            query='適格請求書等保存方式 仕入税額控除',
            tax_type='consumption_tax'
        )
        self.assertIsInstance(invoice_system_refs, dict)
        
    def test_simplified_taxation_workflow(self):
        """簡易課税制度ワークフロー"""
        # 1. 簡易課税事業者の情報
        simplified_taxpayer_data = {
            'company_name': '小売業有限会社',
            'business_type': 'retail',  # 小売業
            'simplified_rate': 0.80,    # みなし仕入率80%
            'previous_year_sales': 45000000,  # 前々年課税売上高4500万円
            'current_sales': {
                'taxable_sales': 48000000,
                'tax_collected': 4800000
            }
        }
        
        # 2. 簡易課税による消費税計算
        deemed_input_tax = (
            simplified_taxpayer_data['current_sales']['tax_collected'] * 
            simplified_taxpayer_data['simplified_rate']
        )
        
        simplified_tax_result = {
            'tax_collected': simplified_taxpayer_data['current_sales']['tax_collected'],
            'deemed_input_tax': deemed_input_tax,
            'tax_to_pay': simplified_taxpayer_data['current_sales']['tax_collected'] - deemed_input_tax
        }
        
        # 3. 結果の検証
        self.assertIsInstance(simplified_tax_result, dict)
        self.assertIn('tax_to_pay', simplified_tax_result)
        self.assertGreater(simplified_tax_result['tax_to_pay'], 0)
        
        # 4. 簡易課税制度の法令参照
        simplified_refs = self.rag_integration.search_legal_references(
            query='簡易課税制度 みなし仕入率 事業区分',
            tax_type='consumption_tax'
        )
        self.assertIsInstance(simplified_refs, dict)
        
    def test_tax_return_preparation_workflow(self):
        """法人税申告書作成ワークフロー"""
        # 1. 申告書作成に必要な情報
        tax_return_data = {
            'company_info': {
                'name': 'テクノロジー株式会社',
                'address': '東京都千代田区',
                'representative': '代表取締役 技術太郎',
                'business_year': '2023年4月1日～2024年3月31日'
            },
            'financial_statements': {
                'profit_loss': {
                    'revenue': 1200000000,
                    'expenses': 1000000000,
                    'net_income': 200000000
                },
                'balance_sheet': {
                    'assets': 800000000,
                    'liabilities': 300000000,
                    'equity': 500000000
                }
            },
            'tax_adjustments': {
                'entertainment_excess': 1000000,    # 交際費損金不算入
                'depreciation_excess': 2000000,     # 減価償却超過額
                'reserve_reversal': -1500000        # 引当金戻入
            }
        }
        
        # 2. 所得金額の計算
        accounting_income = tax_return_data['financial_statements']['profit_loss']['net_income']
        tax_adjustments = sum(tax_return_data['tax_adjustments'].values())
        taxable_income = accounting_income + tax_adjustments
        
        # 3. 法人税額の計算
        corporate_tax = self.tax_calculator.calculate_corporate_tax(
            income=taxable_income,
            company_type='ordinary_corporation'
        )
        
        # 4. 申告書データの構築
        tax_return_document = {
            'company_info': tax_return_data['company_info'],
            'income_calculation': {
                'accounting_income': accounting_income,
                'tax_adjustments': tax_return_data['tax_adjustments'],
                'taxable_income': taxable_income
            },
            'tax_calculation': corporate_tax,
            'filing_date': datetime.now().isoformat(),
            'due_date': (datetime.now() + timedelta(days=60)).isoformat()
        }
        
        # 5. 結果の検証
        self.assertIsInstance(tax_return_document, dict)
        self.assertIn('income_calculation', tax_return_document)
        self.assertIn('tax_calculation', tax_return_document)
        self.assertEqual(tax_return_document['income_calculation']['taxable_income'], taxable_income)
        
        # 6. 申告書作成関連の法令参照
        filing_refs = self.rag_integration.search_legal_references(
            query='法人税申告書 別表四 所得金額計算',
            tax_type='corporate_tax'
        )
        self.assertIsInstance(filing_refs, dict)
        
    def test_quarterly_provisional_payment_workflow(self):
        """四半期予定納税ワークフロー"""
        # 1. 予定納税対象法人の情報
        provisional_payment_data = {
            'company_name': '建設業株式会社',
            'previous_year_tax': 2400000,  # 前年度法人税額240万円
            'current_quarter': 1,          # 第1四半期
            'estimated_annual_income': 180000000,  # 当期予想所得
            'quarterly_performance': {
                'q1_income': 45000000,
                'q1_expenses': 38000000
            }
        }
        
        # 2. 予定納税額の計算
        # 前年実績による予定納税額
        provisional_tax_by_previous = provisional_payment_data['previous_year_tax'] / 4
        
        # 当期実績による予定納税額
        quarterly_income = (
            provisional_payment_data['quarterly_performance']['q1_income'] - 
            provisional_payment_data['quarterly_performance']['q1_expenses']
        )
        
        estimated_annual_tax = self.tax_calculator.calculate_corporate_tax(
            income=provisional_payment_data['estimated_annual_income'],
            company_type='ordinary_corporation'
        )
        
        provisional_tax_by_current = estimated_annual_tax['tax_amount'] / 4
        
        # 3. 予定納税額の決定（少ない方を選択）
        final_provisional_tax = min(provisional_tax_by_previous, provisional_tax_by_current)
        
        # 4. 結果の検証
        self.assertIsInstance(final_provisional_tax, (int, float))
        self.assertGreater(final_provisional_tax, 0)
        self.assertLessEqual(final_provisional_tax, provisional_payment_data['previous_year_tax'])
        
        # 5. 予定納税関連の法令参照
        provisional_refs = self.rag_integration.search_legal_references(
            query='法人税 予定納税 四半期',
            tax_type='corporate_tax'
        )
        self.assertIsInstance(provisional_refs, dict)
        
    def test_group_taxation_workflow(self):
        """連結納税ワークフロー"""
        # 1. 連結グループの情報
        consolidated_group_data = {
            'parent_company': {
                'name': 'ホールディングス株式会社',
                'income': 500000000,
                'loss_carryforward': 0
            },
            'subsidiaries': [
                {
                    'name': '子会社A株式会社',
                    'income': 200000000,
                    'loss_carryforward': 50000000
                },
                {
                    'name': '子会社B株式会社',
                    'income': -100000000,  # 当期損失
                    'loss_carryforward': 0
                },
                {
                    'name': '子会社C株式会社',
                    'income': 150000000,
                    'loss_carryforward': 20000000
                }
            ]
        }
        
        # 2. 連結所得の計算
        total_income = consolidated_group_data['parent_company']['income']
        total_loss_carryforward = consolidated_group_data['parent_company']['loss_carryforward']
        
        for subsidiary in consolidated_group_data['subsidiaries']:
            total_income += subsidiary['income']
            total_loss_carryforward += subsidiary['loss_carryforward']
        
        # 3. 繰越欠損金の控除
        consolidated_taxable_income = max(0, total_income - total_loss_carryforward)
        
        # 4. 連結法人税の計算
        consolidated_tax = self.tax_calculator.calculate_corporate_tax(
            income=consolidated_taxable_income,
            company_type='consolidated_group'
        )
        
        # 5. 結果の検証
        self.assertIsInstance(consolidated_tax, dict)
        self.assertIn('tax_amount', consolidated_tax)
        self.assertGreaterEqual(consolidated_taxable_income, 0)
        
        # 6. 連結納税関連の法令参照
        consolidated_refs = self.rag_integration.search_legal_references(
            query='連結納税 繰越欠損金 所得通算',
            tax_type='corporate_tax'
        )
        self.assertIsInstance(consolidated_refs, dict)
        
    def test_workflow_integration_performance(self):
        """ワークフロー統合パフォーマンステスト"""
        start_time = time.time()
        
        # 複数の法人税計算を連続実行
        test_corporations = [
            {'income': 50000000, 'type': 'small_corporation'},
            {'income': 200000000, 'type': 'ordinary_corporation'},
            {'income': 1000000000, 'type': 'large_corporation'}
        ]
        
        results = []
        for corp in test_corporations:
            # 法人税計算
            corp_tax = self.tax_calculator.calculate_corporate_tax(
                income=corp['income'],
                company_type=corp['type']
            )
            
            # 消費税計算
            vat_tax = self.tax_calculator.calculate_consumption_tax(
                taxable_sales=corp['income'] * 1.2,  # 仮定の売上高
                tax_rate=0.10
            )
            
            results.append({
                'corporate_tax': corp_tax,
                'consumption_tax': vat_tax
            })
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # パフォーマンス検証
        self.assertEqual(len(results), len(test_corporations))
        self.assertLess(execution_time, 10.0)  # 10秒以内で完了
        
        for result in results:
            self.assertIsInstance(result['corporate_tax'], dict)
            self.assertIsInstance(result['consumption_tax'], dict)
            self.assertIn('tax_amount', result['corporate_tax'])
            self.assertIn('tax_amount', result['consumption_tax'])
            
if __name__ == '__main__':
    unittest.main()